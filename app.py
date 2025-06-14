import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import json
import hashlib
import asyncio
from pathlib import Path
from shazamio import Shazam

# Set up the page
st.set_page_config(
    page_title="YouTube Shorts Song Finder",
    page_icon="🎵",
    layout="centered"
)

# Settings
CACHE_FILE = "song_cache.json"
AUDIO_LENGTH = 15  # seconds
MAX_CACHE_ITEMS = 100

def load_cache():
    """Load saved results from file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as file:
                return json.load(file)
        return {}
    except:
        return {}

def save_cache(cache_data):
    """Save results to file"""
    try:
        # Keep only recent items if cache gets too big
        if len(cache_data) > MAX_CACHE_ITEMS:
            items = list(cache_data.items())
            cache_data = dict(items[-MAX_CACHE_ITEMS:])
        
        with open(CACHE_FILE, 'w') as file:
            json.dump(cache_data, file, indent=2)
    except:
        pass

def make_url_hash(url):
    """Create a unique ID for each URL"""
    return hashlib.md5(url.encode()).hexdigest()

def is_youtube_url(url):
    """Check if URL is from YouTube"""
    youtube_parts = [
        'youtube.com/shorts/',
        'youtu.be/',
        'youtube.com/watch?v=',
        'm.youtube.com/shorts/'
    ]
    return any(part in url.lower() for part in youtube_parts)

def download_video(url, save_path):
    """Download YouTube video"""
    try:
        # Settings for downloading
        download_options = {
            'format': 'best[height<=720]',  # Don't download huge files
            'outtmpl': save_path,
            'no_warnings': True,
            'quiet': True,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(download_options) as downloader:
            downloader.download([url])
        
        return True, "Video downloaded successfully"
    except Exception as e:
        return False, f"Could not download video: {str(e)}"

def extract_audio(video_file, audio_file):
    """Get audio from video using ffmpeg"""
    try:
        # Command to extract audio
        command = [
            'ffmpeg',
            '-i', video_file,           # Input video file
            '-t', str(AUDIO_LENGTH),    # Take first 15 seconds
            '-vn',                      # No video, just audio
            '-acodec', 'libmp3lame',    # Make it MP3
            '-ab', '128k',              # Audio quality
            '-ar', '44100',             # Sample rate
            '-y',                       # Overwrite if file exists
            audio_file
        ]
        
        # Run the command
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Audio extracted successfully"
        else:
            return False, f"FFmpeg error: {result.stderr}"
    
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg first."
    except Exception as e:
        return False, f"Could not extract audio: {str(e)}"

def recognize_song(audio_file):
    """Use Shazam to identify the song"""
    try:
        # This function needs to be async for Shazam
        async def identify_song():
            shazam = Shazam()
            result = await shazam.recognize_song(audio_file)
            return result
        
        # Run the async function
        shazam_result = asyncio.run(identify_song())
        
        # Check if we found a song
        if shazam_result and 'track' in shazam_result:
            track_info = shazam_result['track']
            
            # Get basic song info
            song_data = {
                'title': track_info.get('title', 'Unknown'),
                'artist': track_info.get('subtitle', 'Unknown'),
                'shazam_url': '',
                'spotify_url': '',
                'apple_music_url': '',
                'cover_image': '',
                'album': '',
                'release_date': '',
                'genre': '',
                'label': ''
            }
            
            # Get cover image
            if 'images' in track_info:
                images = track_info['images']
                if 'coverart' in images:
                    song_data['cover_image'] = images['coverart']
                elif 'background' in images:
                    song_data['cover_image'] = images['background']
            
            # Get Shazam link
            if 'share' in track_info and 'href' in track_info['share']:
                song_data['shazam_url'] = track_info['share']['href']
            
            # Get streaming links
            if 'hub' in track_info and 'actions' in track_info['hub']:
                for action in track_info['hub']['actions']:
                    if action.get('type') == 'uri':
                        link = action.get('uri', '')
                        if 'spotify' in link.lower():
                            # Convert Spotify URI to web URL
                            if link.startswith('spotify:track:'):
                                track_id = link.split(':')[-1]
                                song_data['spotify_url'] = f"https://open.spotify.com/track/{track_id}"
                            else:
                                song_data['spotify_url'] = link
                        elif 'apple' in link.lower():
                            song_data['apple_music_url'] = link
            
            # Get additional info from sections
            if 'sections' in track_info:
                for section in track_info['sections']:
                    if section.get('type') == 'SONG' and 'metadata' in section:
                        for item in section['metadata']:
                            title = item.get('title', '').lower()
                            text = item.get('text', '')
                            
                            if 'album' in title:
                                song_data['album'] = text
                            elif 'released' in title:
                                song_data['release_date'] = text
                            elif 'label' in title:
                                song_data['label'] = text
            
            # Get genre
            if 'genres' in track_info and 'primary' in track_info['genres']:
                song_data['genre'] = track_info['genres']['primary']
            
            return True, song_data
        else:
            return False, "No song found"
    
    except Exception as e:
        return False, f"Shazam error: {str(e)}"

def process_youtube_video(url, cache_data):
    """Main function to process the video"""
    # Check if we already processed this URL
    url_id = make_url_hash(url)
    if url_id in cache_data:
        st.info("🎯 Found in cache!")
        return cache_data[url_id]
    
    result = {
        'success': False,
        'error': None,
        'song_info': None
    }
    
    # Create temporary folder for files
    with tempfile.TemporaryDirectory() as temp_folder:
        video_path = os.path.join(temp_folder, 'video.%(ext)s')
        audio_path = os.path.join(temp_folder, 'audio.mp3')
        
        # Step 1: Download the video
        st.info("📥 Downloading video...")
        success, message = download_video(url, video_path)
        if not success:
            result['error'] = message
            return result
        
        # Find the downloaded video file
        video_files = list(Path(temp_folder).glob('video.*'))
        if not video_files:
            result['error'] = "Could not find downloaded video"
            return result
        
        actual_video_file = str(video_files[0])
        
        # Step 2: Extract audio
        st.info("🎵 Extracting audio...")
        success, message = extract_audio(actual_video_file, audio_path)
        if not success:
            result['error'] = message
            return result
        
        # Step 3: Recognize song
        st.info("🔍 Identifying song with Shazam...")
        success, song_info = recognize_song(audio_path)
        if success:
            result['success'] = True
            result['song_info'] = song_info
            
            # Save to cache
            cache_data[url_id] = result
            save_cache(cache_data)
        else:
            result['error'] = song_info
    
    return result

def show_song_result(song_info):
    """Display the song information nicely"""
    st.success("🎉 Song found!")
    
    # Show cover image and basic info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if song_info['cover_image']:
            st.image(song_info['cover_image'], width=150)
    
    with col2:
        st.markdown(f"### 🎵 **{song_info['title']}**")
        st.markdown(f"**Artist:** {song_info['artist']}")
        
        if song_info['album']:
            st.markdown(f"**Album:** {song_info['album']}")
        
        if song_info['release_date']:
            st.markdown(f"**Released:** {song_info['release_date']}")
        
        if song_info['genre']:
            st.markdown(f"**Genre:** {song_info['genre']}")
        
        if song_info['label']:
            st.markdown(f"**Label:** {song_info['label']}")
    
    # Show streaming links
    st.markdown("### 🎧 Listen on:")
    
    link_col1, link_col2, link_col3 = st.columns(3)
    
    with link_col1:
        if song_info['spotify_url']:
            st.markdown(f"[🟢 Spotify]({song_info['spotify_url']})")
    
    with link_col2:
        if song_info['apple_music_url']:
            st.markdown(f"[🍎 Apple Music]({song_info['apple_music_url']})")
    
    with link_col3:
        if song_info['shazam_url']:
            st.markdown(f"[🎵 Shazam]({song_info['shazam_url']})")

def main():
    """Main app function"""
    st.title("🎵 YouTube Shorts Song Finder")
    st.markdown("Find out what song is playing in any YouTube Shorts video!")
    
    # Load cached results
    cache_data = load_cache()
    
    # Sidebar with info
    with st.sidebar:
        st.markdown("### ℹ️ How to use:")
        st.markdown("""
        1. Copy a YouTube Shorts URL
        2. Paste it below
        3. Click 'Find Song'
        4. Get song info and streaming links!
        """)
        
        st.markdown("### 🎵 About this app")
        st.markdown("""
        - **100% Free** - No API keys needed
        - **Uses Shazam** - High accuracy recognition
        - **Privacy friendly** - Processes audio locally
        - **Caches results** - Saves time on repeat URLs
        """)
        
        st.markdown("### 📊 Stats")
        cache_count = len(cache_data)
        st.metric("Songs in cache", cache_count)
        
        if st.button("🗑️ Clear cache"):
            cache_data = {}
            save_cache(cache_data)
            st.success("Cache cleared!")
            st.rerun()
    
    # Main input area
    st.markdown("### 🔗 Paste YouTube Shorts URL here")
    
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://youtube.com/shorts/...",
        help="Paste any YouTube Shorts URL here"
    )
    
    # Buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        find_button = st.button("🎵 Find Song", type="primary", use_container_width=True)
    
    with col2:
        if st.button("📋 Try example", use_container_width=True):
            st.info("Paste any real YouTube Shorts URL to test!")
    
    # Process when button clicked
    if find_button:
        # Check if URL was entered
        if not youtube_url:
            st.error("⚠️ Please enter a YouTube URL")
            return
        
        # Check if it's a valid YouTube URL
        if not is_youtube_url(youtube_url):
            st.warning("⚠️ This doesn't look like a YouTube URL. Please check it.")
            return
        
        # Process the video
        with st.spinner("Working on it..."):
            result = process_youtube_video(youtube_url, cache_data)
        
        # Show results
        if result['success']:
            show_song_result(result['song_info'])
        else:
            st.error(f"❌ {result['error']}")
            
            # Give helpful tips
            error_msg = result['error'].lower()
            if "not found" in error_msg or "no song" in error_msg:
                st.info("💡 Try a video with clearer music or a more popular song.")
            elif "ffmpeg" in error_msg:
                st.info("💡 Make sure FFmpeg is installed on your system.")
            elif "download" in error_msg:
                st.info("💡 Check if the URL is correct and the video is public.")

if __name__ == "__main__":
    main()
