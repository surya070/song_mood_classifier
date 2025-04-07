import os
from dotenv import load_dotenv
import spotipy
import requests
import json
from spotipy.oauth2 import SpotifyOAuth
import librosa
import numpy as np
import tempfile
import tensorflow as tf
from services.feature_extractor import extract_features

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-recently-played user-read-private playlist-read-private user-library-read"
)

def get_spotify_token():
    """Retrieve Spotify access token."""
    token_info = sp_oauth.get_access_token()
    if token_info and 'access_token' in token_info:
        return token_info
    return None

def get_user_info():
    """Fetch user's Spotify username."""
    token_info = get_spotify_token()
    if not token_info:
        return None

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user_data = sp.current_user()
    return user_data["display_name"]

def get_recently_played_tracks():
    """Fetch recently played songs from Spotify API."""
    token_info = get_spotify_token()
    if not token_info:
        return None

    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        results = sp.current_user_recently_played(limit=20)
    except Exception as e:
        print(f"Error fetching recently played tracks: {e}")
        return []

    tracks = []
    seen_songs = set()  # To avoid duplicates

    for item in results["items"]:
        track_name = item["track"]["name"]
        artist_name = item["track"]["artists"][0]["name"]
        track_id = item["track"]["id"]

        if track_name not in seen_songs:
            tracks.append({"name": track_name, "artist": artist_name, "id": track_id})
            seen_songs.add(track_name)  # Mark song as seen

    return tracks

def predict_mood(track_url):
    # Get track info
    token_info = get_spotify_token()
    sp = spotipy.Spotify(auth=token_info["access_token"])
    track_info = sp.track(track_url)
    preview_url = track_info.get("preview_url")
    model = tf.keras.models.load_model("models/my_model.keras")

    if not preview_url:
        print("No preview audio available for this track.")
        return None

    # Download preview audio temporarily
    response = requests.get(preview_url)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        tmp.write(response.content)
        tmp.flush()

        # Load audio
        data, sr = librosa.load(tmp.name, duration=28, offset=0.6, mono=True)

        # Extract features
        features = extract_features(data, sr)
        features = features.reshape(1, -1, 1)

        # Predict mood
        prediction = model.predict(features)
        predicted_class = np.argmax(prediction, axis=1)[0]

        return predicted_class

def get_playlist_for_mood(mood):
    """Filter recently played tracks based on mood using Cyanite API."""
    tracks = get_recently_played_tracks()
    filtered_tracks = []
    
    token_info = get_spotify_token()
    sp = spotipy.Spotify(auth=token_info["access_token"])
    for track in tracks:
        # Retrieve the full track details from Spotify
        tr = sp.track(track["id"])
        # Get the Spotify URL from the track's external URLs
        track_url = tr.get("external_urls", {}).get("spotify")
        if not track_url:
            print("URL not found for track", track)
            continue

        analyzed_mood = predict_mood(track_url)
        if analyzed_mood:
            print("Analyzed mood:", analyzed_mood, "Desired mood:", mood)
            if analyzed_mood == mood:
                filtered_tracks.append(track)
    
    return filtered_tracks if filtered_tracks else tracks
