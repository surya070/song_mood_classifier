import sys
import os
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Guest" in response.data


def test_login_redirect(client):
    response = client.get("/login")
    assert response.status_code == 302
    assert "accounts.spotify.com" in response.headers["Location"]


def test_callback_invalid_code(client, mocker):
    mock_spotify_oauth = mocker.MagicMock()
    mock_spotify_oauth.get_access_token.return_value = None
    mocker.patch(
        "app.create_spotify_oauth",
        return_value=mock_spotify_oauth)


    response = client.get("/callback?code=invalid_code")
    assert response.status_code in (200, 302, 500)
    assert (
        b"Authorization failed" in response.data or response.status_code == 302
    )
