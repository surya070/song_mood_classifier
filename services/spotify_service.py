import os
import time
import subprocess
import requests
import json
import numpy as np
import librosa
import tensorflow as tf
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from services.feature_extractor import extract_features

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-recently-played user-read-private playlist-read-private user-library-read"
)

def get_spotify_token():
    token_info = sp_oauth.get_cached_token()

    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

    if token_info and 'access_token' in token_info:
        return token_info

    return None

def get_user_info():
    token_info = get_spotify_token()
    if not token_info:
        return None

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user_data = sp.current_user()
    return user_data["display_name"]

def get_recently_played_tracks():
    token_info = get_spotify_token()
    if not token_info:
        return []

    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        results = sp.current_user_recently_played(limit=20)
    except Exception as e:
        print(f"Error fetching recently played tracks: {e}")
        return []

    tracks = []
    seen_songs = set()

    for item in results["items"]:
        track_name = item["track"]["name"]
        artist_name = item["track"]["artists"][0]["name"]
        track_id = item["track"]["id"]

        if track_name not in seen_songs:
            tracks.append({"name": track_name, "artist": artist_name, "id": track_id})
            seen_songs.add(track_name)

    return tracks

def download_song_with_spotdl(track_url):
    """Download song using spotdl and return file path from downloads dir."""
    try:
        before_download = set(os.listdir(DOWNLOAD_DIR))

        command = [
            "spotdl", track_url,
            "--output", f"{DOWNLOAD_DIR}/",
            "--format", "mp3",
            "--audio", "youtube-music"
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("spotdl download failed:\n", result.stderr)
            return None

        time.sleep(2)  # wait for filesystem to catch up

        after_download = set(os.listdir(DOWNLOAD_DIR))
        new_files = after_download - before_download
        new_audio_files = [f for f in new_files if f.lower().endswith((".mp3", ".m4a", ".webm", ".opus"))]

        if not new_audio_files:
            print("No audio file found after spotdl download.")
            return None

        downloaded_file = os.path.join(DOWNLOAD_DIR, new_audio_files[0])
        print("Downloaded:", downloaded_file)
        return downloaded_file
    except subprocess.CalledProcessError as e:
        print("spotdl execution failed:", e)
    return None

def predict_mood(track_url,model):
    audio_path = download_song_with_spotdl(track_url)
    if not audio_path:
        print("Could not download track with spotdl.")
        return None

    try:
        data, sr = librosa.load(audio_path, duration=28, offset=0.6, mono=True)
        features = extract_features(data, sr)
        features = features.reshape(1, -1, 1)
        prediction = model.predict(features)
        predicted_class = np.argmax(prediction, axis=1)[0]
        return predicted_class
    except Exception as e:
        print("Error processing audio:", e)
        return None
    finally:
        # Clean up: Delete the audio file after processing
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print("Deleted file:", audio_path)
        except Exception as del_err:
            print("Error deleting file:", del_err)

def get_playlist_for_mood(mood):
    tracks = get_recently_played_tracks()
    if not tracks:
        print("No recently played tracks found.")
        return []

    filtered_tracks = []

    token_info = get_spotify_token()
    sp = spotipy.Spotify(auth=token_info["access_token"])

    model = tf.keras.models.load_model("models/my_model.keras")

    for track in tracks:
        tr = sp.track(track["id"])
        track_url = tr.get("external_urls", {}).get("spotify")
        if not track_url:
            print("URL not found for track:", track)
            continue

        print(f"Analyzing: {track['name']} by {track['artist']}")
        analyzed_mood = predict_mood(track_url,model)
        if analyzed_mood is not None:
            print("Analyzed mood:", analyzed_mood, "| Desired mood:", mood)
            if analyzed_mood == mood:
                filtered_tracks.append(track)

    return filtered_tracks if filtered_tracks else tracks
