# 🔍 AI-Powered Song Finder from Video

A Streamlit web app that **automatically identifies music** from any YouTube video or uploaded video file using **Shazam’s audio recognition**.

---

## 🎯 What It Does

This tool helps you find music from:
- **YouTube Shorts**
- **Regular YouTube videos**
- **Locally uploaded video files (MP4, AVI, MOV, etc.)**

It uses **AI audio fingerprinting** to:
- Extract the **first 15 seconds** of the video’s audio
- Identify the background music using the **Shazam API**
- Display **song title, artist, album, cover art, and streaming links**
- **Cache results** to avoid reprocessing the same input

---

## 🚀 Key Features

✅ **Two Input Methods**  
&nbsp;&nbsp;&nbsp;&nbsp;🔗 Paste any YouTube link (Shorts or full-length)  
&nbsp;&nbsp;&nbsp;&nbsp;📁 Upload any video file (MP4, MOV, AVI, etc.)

✅ **No API Key Needed**  
&nbsp;&nbsp;&nbsp;&nbsp;Uses Shazamio (public Python client) for music recognition

✅ **Fast & Local Processing**  
&nbsp;&nbsp;&nbsp;&nbsp;Everything runs locally—your data stays private

✅ **Smart Caching**  
&nbsp;&nbsp;&nbsp;&nbsp;Previous results are stored for quicker repeated searches

✅ **Full Metadata**  
&nbsp;&nbsp;&nbsp;&nbsp;Get song title, artist, album, release date, cover art, and streaming links (Spotify, Apple Music, Shazam)

✅ **Minimal Setup**  
&nbsp;&nbsp;&nbsp;&nbsp;Only Python + FFmpeg required to get started

---

## 🛠 How It Works

1. **📥 Download / Upload Video**  
   - Downloads from YouTube using `yt-dlp`  
   - Or saves the uploaded file to a temp folder

2. **🎙 Extract Audio**  
   - Uses `FFmpeg` to extract a 15-second audio clip

3. **🔎 Identify Music**  
   - Uses `Shazamio` (Python wrapper for Shazam) for music recognition

4. **🎧 Show Results**  
   - Displays full song info, album cover, and platform links

5. **💾 Cache Response**  
   - Results saved in `song_cache.json` for reuse

---

## 🧰 Tech Stack

| Tool         | Use Case                         |
|--------------|----------------------------------|
| Python 3.10+ | Core language                    |
| Streamlit    | Frontend interface               |
| yt-dlp       | YouTube video downloader         |
| FFmpeg       | Extracts audio from video        |
| Shazamio     | Song recognition (Shazam API)    |
| asyncio      | Handles async calls for Shazamio |

---

## 🔧 Installation

### 1. Install Dependencies

```bash
git clone https://github.com/yourusername/youtube-song-finder-ai.git
cd youtube-song-finder-ai
pip install -r requirements.txt
```

### 2. Install FFmpeg  
Make sure FFmpeg is installed and added to your system PATH:  
➡️ [FFmpeg Official Site](https://ffmpeg.org/download.html)

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Then open your browser at:  
🔗 [http://localhost:8501](http://localhost:8501)

---

## 🎥 Demo

🔗 [Click to watch the demo video](./demo/demo-video.mkv)

---

## 🗂 File Structure

```
├── app.py               # Main Streamlit app
├── requirements.txt     # All dependencies
├── song_cache.json      # Stores previous results
└── README.md            # This file
```

---

## 📌 Perfect For

- Finding **uncredited background music** in YouTube Shorts
- Discovering **TikTok-style tracks** in uploaded videos
- Quickly grabbing song info for **personal use or content creation**

---

## 📄 License

This project is licensed under the **Apache License 2.0**.
