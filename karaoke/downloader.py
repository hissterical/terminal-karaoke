import os
import requests
import yt_dlp
import tempfile
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

class SongDownloader:
    def __init__(self, download_dir=None):
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def search_youtube(self, query):
        """Search YouTube for a song and return the first result URL"""
        try:
            # Use yt-dlp to search YouTube
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'extract_flat': 'in_playlist',
            }
            
            search_query = f"ytsearch1:{query} official audio"
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
    
    def search_lyrics(self, artist, title):
        """Search for lyrics using Genius API or web scraping"""
        try:
            # Try Genius-like search
            search_query = f"{artist} {title} lyrics"
            return self._scrape_lyrics(search_query)
        except Exception as e:
            print(f"Error searching lyrics: {e}")
            return None
    
    def _scrape_lyrics(self, query):
        """Scrape lyrics from the web"""
        try:
            # This is a simplified approach - in practice you'd want to use a proper lyrics API
            search_url = f"https://www.google.com/search?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # For now, we'll create a basic LRC template
            # In a real implementation, you'd scrape from lyrics sites
            return None
        except Exception as e:
            return None
    
    def create_basic_lrc(self, duration_seconds, artist="", title=""):
        """Create a basic LRC file with timing"""
        # This creates a very basic LRC file - in practice you'd want real lyrics
        lrc_content = f"[ti:{title}]\n[ar:{artist}]\n[ length: {duration_seconds}]\n\n"
        
        # Add some basic timing - this is just placeholder
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        lrc_content += f"[00:00.00]♪ {title} by {artist} ♪\n"
        lrc_content += f"[00:05.00]♪ Instrumental ♪\n"
        lrc_content += f"[00:30.00]♪ Instrumental ♪\n"
        lrc_content += f"[01:00.00]♪ Instrumental ♪\n"
        lrc_content += f"[0{minutes:02d}:{seconds:02d}.00]♪ End ♪\n"
        
        return lrc_content
    
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
    """A more dedicated lyrics fetcher"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_genius(self, artist, title):
        """Search Genius for lyrics"""
        try:
            # This is a simplified version - a real implementation would use the Genius API
            search_query = f"{artist} {title}".replace(' ', '%20')
            search_url = f"https://genius.com/api/search/song?q={search_query}"
            
            # Note: This is a simplified approach and may not work without proper API keys
            # For a production version, you'd need to register for a Genius API key
            return None
        except Exception as e:
            return None
    
    def fetch_lyrics_from_url(self, url):
        """Fetch lyrics from a given URL"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is highly dependent on the site structure
            # You'd need to customize this for each lyrics site
            lyrics_div = soup.find('div', class_='lyrics')
            if lyrics_div:
                return lyrics_div.get_text()
            
            # Try another common pattern
            lyrics_divs = soup.find_all('div', class_=re.compile(r'Lyrics__Container'))
            if lyrics_divs:
                lyrics = '\n'.join([div.get_text() for div in lyrics_divs])
                return lyrics
                
            return None
        except Exception as e:
            return None
    
    def convert_text_to_lrc(self, text, duration_seconds):
        """Convert plain text lyrics to LRC format with basic timing"""
        if not text:
            return None
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return None
            
        lrc_lines = []
        lrc_lines.append("[by:Terminal Karaoke]")
        lrc_lines.append("")
        
        # Distribute lines evenly across the song duration
        total_lines = len(lines)
        seconds_per_line = duration_seconds / max(total_lines, 1)
        
        for i, line in enumerate(lines):
            timestamp = i * seconds_per_line
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            centiseconds = int((timestamp % 1) * 100)
            lrc_lines.append(f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{line}")
        
        return '\n'.join(lrc_lines)