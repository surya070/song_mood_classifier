from unittest.mock import patch
from services import spotify_service

@patch("services.spotify_service.get_user_info")
def test_get_user_info(mock_get_user_info):
    mock_get_user_info.return_value = "TestUser"
    result = spotify_service.get_user_info("fake_token")
    assert result == "TestUser"
