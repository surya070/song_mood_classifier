from flask import Flask, redirect, request, session, url_for, render_template
from services.spotify_service import get_playlist_for_mood, get_user_info, create_spotify_oauth
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key_here")
app.config["SESSION_COOKIE_NAME"] = "Spotify-Login"

@app.route("/")
def home():
    username = session.get("username", "Guest")
    return render_template("index.html", username=username)

@app.route("/login")
def login():
    session.clear()
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)

    if not token_info:
        return "Authorization failed. <a href='/login'>Try again</a>"

    session["token_info"] = token_info
    session["access_token"] = token_info["access_token"]
    session["username"] = get_user_info(token_info["access_token"])
    return redirect(url_for("home"))

@app.route("/generate_playlist", methods=["POST"])
def generate_playlist():
    if "token_info" not in session:
        return redirect(url_for("login"))

    moods = ["Energetic & Bold", "Happy & Playful", "Melancholic & Reflective", "Humorous & Quirky", "Intense & Dramatic"]
    mood_index = moods.index(request.form.get("mood")) + 1
    tracks = get_playlist_for_mood(mood_index, session["access_token"])
    return render_template("playlist.html", mood=moods[mood_index - 1], tracks=tracks)

if __name__ == "__main__":
    app.run(debug=True)
