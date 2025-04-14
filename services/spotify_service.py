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
        scope="user-read-recently-played user-read-private playlist-read-private user-library-read",
        cache_path=None  # We're handling tokens manually
    )

def refresh_token():
    sp_oauth = create_spotify_oauth()
    token_info = session.get("token_info", None)

    if token_info:
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session["token_info"] = token_info
            session["access_token"] = token_info["access_token"]
    return session.get("access_token")

def get_user_info(access_token):
    sp = spotipy.Spotify(auth=access_token)
    return sp.current_user()["display_name"]

def get_recently_played_tracks(access_token):
    sp = spotipy.Spotify(auth=access_token)
    results = sp.current_user_recently_played(limit=20)
    tracks = []
    seen = set()

    for item in results["items"]:
        track = item["track"]
        name, artist, track_id = track["name"], track["artists"][0]["name"], track["id"]

        if name not in seen:
            seen.add(name)
            tracks.append({"name": name, "artist": artist, "id": track_id})
    return tracks

def download_song_with_spotdl(track_url):
    try:
        before = set(os.listdir(DOWNLOAD_DIR))
        command = ["spotdl", track_url, "--output", DOWNLOAD_DIR, "--format", "mp3", "--audio", "youtube-music"]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("spotdl failed:\n", result.stderr)
            return None

        time.sleep(2)
        after = set(os.listdir(DOWNLOAD_DIR))
        new_file = list(after - before)
        audio_file = next((f for f in new_file if f.endswith((".mp3", ".m4a", ".webm", ".opus"))), None)

        return os.path.join(DOWNLOAD_DIR, audio_file) if audio_file else None
    except Exception as e:
        print("Error downloading:", e)
        return None

def predict_mood(track_url, model):
    audio_path = download_song_with_spotdl(track_url)
    if not audio_path:
        return None
    try:
        data, sr = librosa.load(audio_path, duration=28, offset=0.6, mono=True)
        features = extract_features(data, sr).reshape(1, -1, 1)
        prediction = model.predict(features)
        return np.argmax(prediction, axis=1)[0]
    except Exception as e:
        print("Audio error:", e)
        return None
    finally:
        try:
            os.remove(audio_path)
        except:
            pass

def get_playlist_for_mood(mood, _):
    access_token = refresh_token()
    model = tf.keras.models.load_model("models/my_model.keras")

    tracks = get_recently_played_tracks(access_token)
    if not tracks:
        return []

    filtered = []
    sp = spotipy.Spotify(auth=access_token)

    for track in tracks:
        track_url = sp.track(track["id"]).get("external_urls", {}).get("spotify")
        if not track_url:
            continue

        print(f"Analyzing: {track['name']} by {track['artist']}")
        analyzed = predict_mood(track_url, model)
        print(f"Analyzed mood: {analyzed}, Desired mood: {mood}")
        if analyzed == mood:
            track["url"] = track_url
            filtered.append(track)

    return filtered if filtered else tracks
