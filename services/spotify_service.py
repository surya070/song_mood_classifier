import os
import time
import subprocess
import numpy as np
import librosa
import tensorflow as tf
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from services.feature_extractor import extract_features
from flask import session

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=(
            "user-read-recently-played user-read-private "
            "playlist-read-private user-library-read"
        ),
        cache_path=None,
    )


def refresh_token():
    sp_oauth = create_spotify_oauth()
    token_info = session.get("token_info")

    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info
        session["access_token"] = token_info["access_token"]

    return session.get("access_token")


def get_user_info(access_token):
    sp = spotipy.Spotify(auth=access_token)
    return sp.current_user().get("display_name", "Unknown User")


def get_recently_played_tracks(access_token):
    sp = spotipy.Spotify(auth=access_token)
    results = sp.current_user_recently_played(limit=20)
    seen = set()
    tracks = []

    for item in results.get("items", []):
        track = item["track"]
        name = track["name"]
        artist = track["artists"][0]["name"]
        track_id = track["id"]

        if name not in seen:
            seen.add(name)
            tracks.append(
                {
                    "name": name,
                    "artist": artist,
                    "id": track_id,
                    "url": f"https://open.spotify.com/track/{track_id}",
                }
            )

    return tracks


def download_song_with_spotdl(track_url):
    try:
        before = set(os.listdir(DOWNLOAD_DIR))

        command = [
            "spotdl",
            track_url,
            "--output",
            DOWNLOAD_DIR,
            "--format",
            "mp3",
            "--audio",
            "youtube-music",
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("spotdl failed:\n", result.stderr)
            return None

        time.sleep(2)
        after = set(os.listdir(DOWNLOAD_DIR))
        new_files = list(after - before)

        for f in new_files:
            if f.endswith((".mp3", ".m4a", ".webm", ".opus")):
                return os.path.join(DOWNLOAD_DIR, f)

        return None
    except Exception as e:
        print("Error downloading track:", e)
        return None


def predict_mood(track_url, model):
    audio_path = download_song_with_spotdl(track_url)
    if not audio_path:
        return None

    try:
        data, sr = librosa.load(audio_path, duration=28, offset=0.6, mono=True)
        features = extract_features(data, sr).reshape(1, -1, 1)
        prediction = model.predict(features)
        return int(np.argmax(prediction, axis=1)[0])
    except Exception as e:
        print("Error processing audio:", e)
        return None
    finally:
        try:
            os.remove(audio_path)
        except Exception:
            pass


def get_playlist_for_mood(mood, _):
    access_token = refresh_token()
    model = tf.keras.models.load_model("models/my_model.keras")

    tracks = get_recently_played_tracks(access_token)
    if not tracks:
        return []

    filtered = []
    print(f"Filtering tracks for mood: {mood}")

    for track in tracks:
        print(f"Analyzing: {track['name']} by {track['artist']}")
        analyzed_mood = predict_mood(track["url"], model)
        print(f"Predicted mood: {analyzed_mood}")

        if analyzed_mood == mood:
            filtered.append(track)

    return filtered if filtered else tracks
