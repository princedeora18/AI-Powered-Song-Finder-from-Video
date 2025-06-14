# YouTube Shorts Audio Identifier

This application identifies songs used in YouTube Shorts, especially when the song name is not mentioned in the title or description. It is designed to detect audio that has been pre-attached by YouTube’s Shorts creation tool.

## Overview

Many YouTube Shorts feature background music added through YouTube’s built-in audio library or during the editing process. However, these videos often do not display the song name in the title, description, or anywhere visible to viewers. This tool bridges that gap by automatically downloading the video, extracting a short audio segment, and using Shazam’s audio fingerprinting system to identify the song.

It’s designed specifically for use cases where the song is pre-attached by the creator but not disclosed—helping users quickly discover the track playing in any YouTube Shorts video.

## Features

- Designed specifically for YouTube Shorts with unlisted background music
- Automatically extracts audio from Shorts using `yt-dlp` and `ffmpeg`
- Utilizes the Shazamio library for music recognition
- Displays song title, artist, album, release date, and streaming links
- Lightweight and easy-to-use web interface built with Streamlit

## How It Works

1. User inputs a YouTube Shorts URL.
2. The app downloads the video and extracts its audio.
3. The audio is passed to the Shazamio client for fingerprint matching.
4. The song details are returned and displayed in a user-friendly format.

## Tech Stack

- Python 3.10+
- Streamlit (UI)
- yt-dlp (video download)
- FFmpeg (audio extraction)
- Shazamio (song recognition)

## Installation

### Requirements

- Python 3.10 or higher
- FFmpeg installed and accessible in system PATH

### Setup

```bash
git clone https://github.com/yourusername/youtube-shorts-song-finder.git
cd youtube-shorts-song-finder
pip install -r requirements.txt
````

## Running the App

```bash
streamlit run app.py
```

This will launch the application in your browser at `http://localhost:8501`.

## Example Use Case

Input:

Video Credit: MisoDope (UCmPizj-upw6BjWs2gEJt9ng)

```
https://youtube.com/shorts/rt8n4kE51_s?si=BPsN64mPUoLdAHUW
```

Output:

* Song Title: Lollipop (feat. Static Major) [feat. Static Major]
* Artist: Lil Wayne
* Album: Tha Carter III
* Release Date: 2008
* Links: Spotify, Apple Music, Shazam

## File Structure

```
├── app.py               # Main application script
├── requirements.txt     # Python dependencies
├── song_cache.json      # Local cache to speed up repeated queries
└── README.md
```

## License

This project is licensed under the Apache License 2.0.

