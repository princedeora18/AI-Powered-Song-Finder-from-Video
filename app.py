import streamlit as st
import yt_dlp
import subprocess
import os
import tempfile
import json
import hashlib
from pathlib import Path
import time
import asyncio
from typing import Dict, Optional, Tuple
from shazamio import Shazam

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Shorts Song Finder",
    page_icon="🎵",
    layout="centered"
)

# Constants
CACHE_FILE = "song_cache.json"
AUDIO_DURATION = 15  # seconds to extract
MAX_CACHE_SIZE = 100  # maximum cached entries

class SongRecognizer:
    """Main class for handling YouTube Shorts song recognition"""
    
    def __init__(self):
        self.cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Load cached results from file"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.warning(f"Could not load cache: {e}")
        return {}
    
    def save_cache(self):
        """Save cache to file with size limit"""
        try:
            # Limit cache size by keeping only the most recent entries
            if len(self.cache) > MAX_CACHE_SIZE:
                items = list(self.cache.items())
                self.cache = dict(items[-MAX_CACHE_SIZE:])
            
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            st.warning(f"Could not save cache: {e}")
    
    def get_url_hash(self, url: str) -> str:
        """Generate hash for URL to use as cache key"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def is_valid_youtube_shorts_url(self, url: str) -> bool:
        """Validate if URL is a YouTube Shorts URL"""
        shorts_patterns = [
            'youtube.com/shorts/',
            'youtu.be/',
            'm.youtube.com/shorts/',
            'youtube.com/watch?v='
        ]
        return any(pattern in url.lower() for pattern in shorts_patterns)
    
    def download_video(self, url: str, output_path: str) -> Tuple[bool, str]:
        """Download YouTube video using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'best[height<=720]',  # Limit quality for faster download
                'outtmpl': output_path,
                'no_warnings': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True, "Video downloaded successfully"
            
        except Exception as e:
            return False, f"Download failed: {str(e)}"
    
    def extract_audio_segment(self, video_path: str, audio_path: str, duration: int = AUDIO_DURATION) -> Tuple[bool, str]:
        """Extract audio segment using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-t', str(duration),  # Extract first N seconds
                '-vn',  # No video
                '-acodec', 'libmp3lame',  # MP3 codec
                '-ab', '128k',  # Audio bitrate
                '-ar', '44100',  # Sample rate
                '-y',  # Overwrite output file
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "Audio extracted successfully"
            else:
                return False, f"FFmpeg error: {result.stderr}"
                
        except FileNotFoundError:
            return False, "FFmpeg not found. Please install FFmpeg."
        except Exception as e:
            return False, f"Audio extraction failed: {str(e)}"
    
    def recognize_song_shazam(self, audio_path: str) -> Tuple[bool, Dict]:
        """Recognize song using Shazamio (free and open-source)"""
        try:
            async def recognize_async():
                shazam = Shazam()
                result = await shazam.recognize_song(audio_path)
                return result
            
            # Run the async function
            result = asyncio.run(recognize_async())
            
            if result and 'track' in result:
                track = result['track']
                
                # Extract song information
                song_data = {
                    'title': track.get('title', 'Unknown Title'),
                    'subtitle': track.get('subtitle', 'Unknown Artist'),
                    'artist': track.get('subtitle', 'Unknown Artist'),
                    'sections': track.get('sections', []),
                    'images': track.get('images', {}),
                    'share': track.get('share', {}),
                    'hub': track.get('hub', {}),
                    'key': track.get('key', ''),
                    'genres': track.get('genres', {}),
                    'urlparams': track.get('urlparams', {}),
                }
                
                # Try to extract additional metadata from sections
                for section in track.get('sections', []):
                    if section.get('type') == 'SONG':
                        metadata = section.get('metadata', [])
                        for meta in metadata:
                            if meta.get('title') == 'Album':
                                song_data['album'] = {'name': meta.get('text', '')}
                            elif meta.get('title') == 'Released':
                                song_data['release_date'] = meta.get('text', '')
                            elif meta.get('title') == 'Label':
                                song_data['label'] = meta.get('text', '')
                
                # Extract streaming links from hub
                if 'actions' in track.get('hub', {}):
                    for action in track['hub']['actions']:
                        if action.get('type') == 'uri':
                            uri = action.get('uri', '')
                            if 'spotify' in uri.lower():
                                song_data['spotify_uri'] = uri
                            elif 'apple' in uri.lower():
                                song_data['apple_music_uri'] = uri
                
                # Extract web links from share
                share_data = track.get('share', {})
                if 'href' in share_data:
                    song_data['shazam_url'] = share_data['href']
                
                return True, song_data
            else:
                return False, {'error': 'No song recognized by Shazam'}
                
        except Exception as e:
            return False, {'error': f'Shazam recognition failed: {str(e)}'}
    
    def process_video(self, url: str) -> Dict:
        """Main processing pipeline"""
        # Check cache first
        url_hash = self.get_url_hash(url)
        if url_hash in self.cache:
            st.info("🎯 Found result in cache!")
            return self.cache[url_hash]
        
        result = {'success': False, 'error': None, 'song_data': None}
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'video.%(ext)s')
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            
            # Step 1: Download video
            st.info("📥 Downloading video...")
            success, message = self.download_video(url, video_path)
            if not success:
                result['error'] = message
                return result
            
            # Find the actual downloaded file
            video_files = list(Path(temp_dir).glob('video.*'))
            if not video_files:
                result['error'] = "Downloaded video file not found"
                return result
            
            actual_video_path = str(video_files[0])
            
            # Step 2: Extract audio
            st.info("🎵 Extracting audio segment...")
            success, message = self.extract_audio_segment(actual_video_path, audio_path)
            if not success:
                result['error'] = message
                return result
            
            # Step 3: Recognize song
            st.info("🔍 Recognizing song with Shazam...")
            success, song_data = self.recognize_song_shazam(audio_path)
            if success:
                result['success'] = True
                result['song_data'] = song_data
                
                # Cache the result
                self.cache[url_hash] = result
                self.save_cache()
            else:
                result['error'] = song_data.get('error', 'Unknown error')
        
        return result

def display_song_result(song_data: Dict):
    """Display song recognition results in a nice format"""
    st.success("🎉 Song recognized!")
    
    # Main song info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Try to get cover art from images
        cover_url = None
        if song_data.get('images', {}).get('coverart'):
            cover_url = song_data['images']['coverart']
        elif song_data.get('images', {}).get('background'):
            cover_url = song_data['images']['background']
        
        if cover_url:
            st.image(cover_url, width=150)
    
    with col2:
        st.markdown(f"### 🎵 **{song_data.get('title', 'Unknown Title')}**")
        st.markdown(f"**Artist:** {song_data.get('artist', 'Unknown Artist')}")
        
        if song_data.get('album', {}).get('name'):
            st.markdown(f"**Album:** {song_data['album']['name']}")
        
        if song_data.get('release_date'):
            st.markdown(f"**Release Date:** {song_data['release_date']}")
        
        if song_data.get('label'):
            st.markdown(f"**Label:** {song_data['label']}")
    
    # Streaming links and additional info
    st.markdown("### 🎧 Links:")
    
    link_col1, link_col2, link_col3 = st.columns(3)
    
    with link_col1:
        if song_data.get('spotify_uri'):
            # Convert Spotify URI to web URL if needed
            spotify_uri = song_data['spotify_uri']
            if spotify_uri.startswith('spotify:'):
                spotify_id = spotify_uri.split(':')[-1]
                spotify_url = f"https://open.spotify.com/track/{spotify_id}"
            else:
                spotify_url = spotify_uri
            st.markdown(f"[🟢 Spotify]({spotify_url})")
    
    with link_col2:
        if song_data.get('apple_music_uri'):
            apple_uri = song_data['apple_music_uri']
            st.markdown(f"[🍎 Apple Music]({apple_uri})")
    
    with link_col3:
        if song_data.get('shazam_url'):
            shazam_url = song_data['shazam_url']
            st.markdown(f"[🎵 Shazam]({shazam_url})")
    
    # Show genre information if available
    if song_data.get('genres', {}).get('primary'):
        st.markdown(f"**Genre:** {song_data['genres']['primary']}")
    
    # Show additional metadata in expander
    if song_data.get('sections'):
        with st.expander("📄 Additional Information"):
            for section in song_data['sections']:
                if section.get('type') == 'LYRICS':
                    st.markdown("**Lyrics Preview Available**")
                elif section.get('type') == 'VIDEO':
                    st.markdown("**Music Video Available**")
                elif section.get('metadata'):
                    for meta in section['metadata']:
                        if meta.get('title') and meta.get('text'):
                            st.markdown(f"**{meta['title']}:** {meta['text']}")

def main():
    """Main Streamlit app"""
    st.title("🎵 YouTube Shorts Song Finder")
    st.markdown("Discover what song is playing in any YouTube Shorts video!")
    
    # Initialize recognizer
    recognizer = SongRecognizer()
    
    # Sidebar for information
    with st.sidebar:
        st.markdown("### ℹ️ How to use:")
        st.markdown("""
        1. Paste any YouTube Shorts URL
        2. Click 'Find Song' and wait for results
        3. Results are cached to save processing time
        4. No API key required - uses free Shazam recognition!
        """)
        
        st.markdown("### 🎵 About Shazam Recognition")
        st.markdown("""
        - **Free and open-source** - No API limits
        - **High accuracy** - Powered by Shazam's algorithm
        - **Rich metadata** - Song info, album art, links
        - **Privacy-friendly** - Processes audio locally
        """)
        
        st.markdown("### 📊 Cache Info")
        cache_size = len(recognizer.cache)
        st.metric("Cached Results", cache_size)
        
        if st.button("🗑️ Clear Cache"):
            recognizer.cache = {}
            recognizer.save_cache()
            st.success("Cache cleared!")
            st.rerun()
    
    # Main interface
    st.markdown("### 🔗 Enter YouTube Shorts URL")
    
    url = st.text_input(
        "YouTube Shorts URL",
        placeholder="https://youtube.com/shorts/...",
        help="Paste the URL of a YouTube Shorts video"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        find_song = st.button("🎵 Find Song", type="primary", use_container_width=True)
    
    with col2:
        if st.button("📋 Example URL", use_container_width=True):
            st.session_state.example_url = "https://youtube.com/shorts/dQw4w9WgXcQ"
            st.info("Example URL would go here - paste any real YouTube Shorts URL!")
    
    # Process video when button is clicked
    if find_song:
        if not url:
            st.error("⚠️ Please enter a YouTube URL")
            return
        
        if not recognizer.is_valid_youtube_shorts_url(url):
            st.warning("⚠️ This doesn't look like a valid YouTube URL. Please check and try again.")
            return
        
        # Show progress
        with st.spinner("Processing video..."):
            result = recognizer.process_video(url)
        
        if result['success']:
            display_song_result(result['song_data'])
        else:
            st.error(f"❌ {result['error']}")
            
            # Provide helpful suggestions
            if "not found" in result['error'].lower() or "invalid" in result['error'].lower():
                st.info("💡 Try checking if the URL is correct and the video is publicly available.")
            elif "shazam" in result['error'].lower():
                st.info("💡 The song might not be in Shazam's database, or the audio quality might be too low.")
            elif "ffmpeg" in result['error'].lower():
                st.info("💡 Make sure FFmpeg is installed on your system.")
            elif "no song recognized" in result['error'].lower():
                st.info("💡 Try a video with clearer audio or a more popular song. Background noise can affect recognition.")

if __name__ == "__main__":
    main()