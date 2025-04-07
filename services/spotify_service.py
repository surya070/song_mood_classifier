import os
from dotenv import load_dotenv
import spotipy
import requests
import json
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

CYANITE_API_KEY = os.getenv("CYANITE_API_KEY")
# Note: The GraphQL endpoint is defined below but not used in this code.
# CYANITE_API_URL = "https://api.cyanite.ai/graphql"
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

def analyze_song_mood(track_url):
    """Analyze the mood of the track using the Cyanite Public API REST endpoint."""
    # Use the REST endpoint for track analysis.
    endpoint = "https://api.cyanite.ai/v1/track"
    params = {
        "apikey": CYANITE_API_KEY,
        "url": track_url
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

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

        mood_analysis = analyze_song_mood(track_url)
        if mood_analysis:
            # Debug: print the full response structure to verify keys
            print("Cyanite response:", json.dumps(mood_analysis, indent=2))
            analyzed_mood = mood_analysis.get('mood')  # Adjust key extraction as needed
            print("Analyzed mood:", analyzed_mood, "Desired mood:", mood)
            if analyzed_mood == mood:
                filtered_tracks.append(track)
    
    return filtered_tracks if filtered_tracks else tracks
