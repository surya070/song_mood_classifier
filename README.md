# Mood-Based Spotify Playlist Generator
This is a Flask web app that builds playlists based on your mood. It pulls your recently played songs from Spotify, runs them through a custom CNN model trained to classify moods, and then puts together a playlist that fits the vibe you choose—like chill, hype, sad, or focused.

The main idea is to help you rediscover songs in your own library based on how you're feeling. You might find energetic tracks for a workout or something mellow for a late-night study session.

Here’s how it works:

-The app grabs 30-second previews of your recently played tracks using Spotipy and Spotify OAuth.

-Each audio snippet is processed with librosa, where we extract features like MFCCs and apply some augmentations like noise and pitch shifts to make the model more robust.

-The CNN is built with TensorFlow Keras. It has convolutional layers, pooling, dropout—basically a standard image-style CNN but trained on audio spectrograms.

-Once moods are predicted, the tracks that match your selected mood are shown in a custom playlist.

It’s all tied together with Flask on the backend and a simple UI using Jinja templates. You’ll need your Spotify API credentials in a .env file for it to run, along with your Flask secret key.
To try it out, just clone the repo, install the dependencies, and run the app.
