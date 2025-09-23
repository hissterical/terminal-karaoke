import os
import requests
import yt_dlp
import re
import time

class SongDownloader:
    def __init__(self, download_dir=None):
        self.download_dir = download_dir or os.path.join(os.getcwd(), "library")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.lyrics_fetcher = LyricsFetcher()
    
    def search_youtube(self, query):
        """Search YouTube for a song and return the first result URL"""
        try:
            # Use yt-dlp to search YouTube
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'extract_flat': 'in_playlist',
            }
            
            search_query = f"ytsearch1:{query} official karaoke audio"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search_query, download=False)
                if result and 'entries' in result and result['entries']:
                    return result['entries'][0]['url']
        except Exception as e:
            print(f"Error searching YouTube: {e}")
        return None
    
    def download_audio(self, url, title=None):
        """Download audio from YouTube URL"""
        try:
            # Sanitize title for filename
            if title:
                safe_title = re.sub(r'[^\w\-_\. ]', '_', title)[:50]
            else:
                safe_title = "karaoke_song"
            
            output_path = os.path.join(self.download_dir, f"{safe_title}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Get the actual downloaded file path
                downloaded_file = ydl.prepare_filename(info)
                mp3_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'
                return mp3_file
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
    
    def save_lrc_file(self, lrc_content, mp3_path):
        """Save LRC content to file"""
        lrc_path = mp3_path.rsplit('.', 1)[0] + '.lrc'
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
            return lrc_path
        except Exception as e:
            print(f"Error saving LRC file: {e}")
            return None

class LyricsFetcher:
    """Fetch synchronized lyrics using LRCLIB API"""
    
    def __init__(self):
        self.base_url = "https://lrclib.net/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Terminal Karaoke Player (https://github.com/hissterical/terminal-karaoke)'
        })
    
    def search_lyrics(self, artist, title):
        """Search for lyrics using LRCLIB API"""
        try:
            # Search for tracks
            search_params = {
                'q': f"{artist} {title}"
            }
            
            search_response = self.session.get(f"{self.base_url}/search", params=search_params)
            if search_response.status_code == 200:
                search_results = search_response.json()
                if search_results and len(search_results) > 0:
                    # Use the first result
                    track = search_results[0]
                    track_id = track['id']
                    
                    # Get synced lyrics
                    lyrics_response = self.session.get(f"{self.base_url}/get/{track_id}")
                    if lyrics_response.status_code == 200:
                        lyrics_data = lyrics_response.json()
                        synced_lyrics = lyrics_data.get('syncedLyrics')
                        if synced_lyrics:
                            return synced_lyrics
            return None
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return None
    
    def get_lyrics_by_metadata(self, artist, title, album="", duration=0):
        """Get lyrics by metadata using LRCLIB API"""
        try:
            params = {
                'artist_name': artist,
                'track_name': title,
                'album_name': album,
                'duration': duration
            }
            
            response = self.session.get(f"{self.base_url}/get", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('syncedLyrics', None)
            elif response.status_code == 404:
                # Try fuzzy search
                return self.search_lyrics(artist, title)
            return None
        except Exception as e:
            print(f"Error getting lyrics by meta {e}")
            return None
    
    def create_basic_lrc(self, duration_seconds, artist="", title=""):
        """Create a basic LRC file with timing when real lyrics aren't available"""
        lrc_content = f"[ti:{title}]\n[ar:{artist}]\n[length: {self._format_time(duration_seconds)}]\n\n"
        
        # Add some basic timing
        lrc_content += f"[00:00.00]♪ {title} by {artist} ♪\n"
        if duration_seconds > 30:
            lrc_content += f"[00:05.00]♪ Instrumental ♪\n"
            lrc_content += f"[00:30.00]♪ Instrumental ♪\n"
        if duration_seconds > 60:
            lrc_content += f"[01:00.00]♪ Instrumental ♪\n"
        
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        lrc_content += f"[{minutes:02d}:{seconds:02d}.00]♪ End ♪\n"
        
        return lrc_content
    
    def _format_time(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"