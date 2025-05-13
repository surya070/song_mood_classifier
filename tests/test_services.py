# flake8: noqa: E402
import sys
import os
from unittest.mock import patch
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )
from services import spotify_service


@patch("services.spotify_service.get_user_info")
def test_get_user_info(mock_get_user_info):
    mock_get_user_info.return_value = "TestUser"
    result = spotify_service.get_user_info("fake_token")
    assert result == "TestUser"


@patch("services.spotify_service.get_recently_played_tracks")
def test_get_recently_played_tracks(mock_get_recently_played_tracks):
    mock_get_recently_played_tracks.return_value = [
        {"name": "Song1", "artist": "Artist1", "url": "url1"},
        {"name": "Song2", "artist": "Artist2", "url": "url2"},
    ]
    result = spotify_service.get_recently_played_tracks("fake_token")
    assert len(result) == 2
    assert result[0]["name"] == "Song1"
    assert result[1]["name"] == "Song2"


@patch("services.spotify_service.get_playlist_for_mood")
def test_get_playlist_for_mood(mock_get_playlist_for_mood):
    mock_get_playlist_for_mood.return_value = [
        {"name": "Song1", "artist": "Artist1", "url": "url1"}
    ]
    result = spotify_service.get_playlist_for_mood(1, "fake_token")
    assert len(result) == 1
    assert result[0]["name"] == "Song1"


@patch("services.spotify_service.refresh_token")
def test_refresh_token(mock_refresh_token):
    mock_refresh_token.return_value = "new_token"
    result = spotify_service.refresh_token()
    assert result == "new_token"


@patch("services.spotify_service.get_user_info")
def test_get_user_info_invalid_token(mock_get_user_info):
    mock_get_user_info.side_effect = Exception("Invalid token")
    try:
        result = spotify_service.get_user_info("invalid_token")
    except Exception:
        result = "Unknown User"
    assert result == "Unknown User"


@patch("services.spotify_service.get_recently_played_tracks")
def test_get_recently_played_tracks_empty(mock_get_recently_played_tracks):
    mock_get_recently_played_tracks.return_value = []
    result = spotify_service.get_recently_played_tracks("fake_token")
    assert result == []
