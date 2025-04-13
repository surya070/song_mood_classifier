from flask import Flask, redirect, request, session, url_for, render_template
from services.spotify_service import get_playlist_for_mood, get_user_info, sp_oauth
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key_here")
app.config["SESSION_COOKIE_NAME"] = "Spotify-Login"

load_dotenv()

@app.route("/")
def home():
    username = session.get("username", "Guest")
    return render_template("index.html", username=username)

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)

    if token_info:
        session["token_info"] = token_info
        session["username"] = get_user_info()  # Store username in session
        return redirect(url_for("home"))
    else:
        return "Authorization failed. Please <a href='/login'>try again</a>."

@app.route("/generate_playlist", methods=["POST"])
def generate_playlist():
    moods=["Energetic & Bold","Happy & Playful","Melancholic & Reflective","Humorous & Quirky","Intense & Dramatic"]
    mood = request.form.get("mood")
    mood=moods.index(mood)+1
    if not mood:
        return "Mood not provided.", 400

    playlist = get_playlist_for_mood(mood)
    return render_template("playlist.html", mood=moods[mood-1], tracks=playlist)

if __name__ == "__main__":
    app.run(debug=True)
