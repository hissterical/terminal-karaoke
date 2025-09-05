import pygame
import time
import os
from .ui import UI
from .lyrics import LyricsParser
from .audio import AudioManager
from .downloader import SongDownloader##
import curses

class KaraokePlayer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.song_path = ""
        self.lrc_path = ""
        self.lyrics = []  # [(timestamp, line)]
        self.total_time = 0.0
        self.paused = False
        self.current_line_idx = 0
        self.status_message = ""
        self.status_timer = 0
        self.controls = {
            'p': "Pause/Play",
            '←': "Back 5s",
            '→': "Forward 5s",
            'q': "Quit"
        }
        
        # Timing
        self.seek_offset = 0.0
        self.playback_start_time = 0
        self.last_update_time = 0
        
        # Components
        self.ui = UI(stdscr)
        self.audio_manager = AudioManager()
        self.lyrics_parser = LyricsParser()
        self.downloader = SongDownloader()
        
        # Initialize pygame mixer
        self.audio_manager.init_mixer()

    def set_status(self, message, duration=1):
        self.status_message = message
        self.status_timer = time.time() + duration

    def search_and_download(self, query):
        """Search for and download a song with lyrics"""
        self.ui.show_download_progress(f"Searching for: {query}")
        
        # Search YouTube
        youtube_url = self.downloader.search_youtube(query)
        if not youtube_url:
            self.set_status("Song not found", 3)
            return False
        
        self.ui.show_download_progress("Downloading audio...")
        
        # Download audio
        mp3_path = self.downloader.download_audio(youtube_url, query)
        if not mp3_path:
            self.set_status("Download failed", 3)
            return False
        
        self.ui.show_download_progress("Creating lyrics...")
        
        # For now, create basic LRC file since real lyrics fetching is complex
        # In a real implementation, you'd fetch actual lyrics
        try:
            # Get song duration
            temp_sound = pygame.mixer.Sound(mp3_path)
            duration = temp_sound.get_length()
            del temp_sound
            
            # Create basic LRC
            lrc_content = self.downloader.create_basic_lrc(duration, "Unknown Artist", query)
            lrc_path = self.downloader.save_lrc_file(lrc_content, mp3_path)
            
            if lrc_path and self.load_song(mp3_path, lrc_path):
                self.seek_to(0.0)
                self.set_status("Downloaded and ready!", 2)
                return True
            else:
                self.set_status("Failed to create lyrics", 3)
                return False
        except Exception as e:
            self.set_status(f"Error: {str(e)}", 3)
            return False

    def load_song(self, song_path, lrc_path):
        self.song_path = song_path
        self.lrc_path = lrc_path
        
        try:
            success, length = self.audio_manager.load_song(song_path)
            if not success:
                self.set_status("Error loading song", 3)
                return False
                
            self.total_time = length
            self.set_status(f"Loaded: {os.path.basename(song_path)}", 2)
            
            # Reset timing
            self.seek_offset = 0.0
            self.playback_start_time = 0
            self.last_update_time = time.time()
            
        except Exception as e:
            self.set_status(f"Error loading song: {str(e)}", 3)
            return False
        
        self.lyrics = self.lyrics_parser.parse(lrc_path)
        if not self.lyrics:
            self.set_status("Warning: No lyrics found in LRC file", 2)
        
        return True

    def current_time(self):
        """Get the accurate current playback time in seconds"""
        if self.paused:
            return self.seek_offset
        
        pos_ms = self.audio_manager.get_position()
        if pos_ms >= 0:
            return self.seek_offset + pos_ms / 1000.0
        
        # Fallback
        elapsed = time.time() - self.playback_start_time
        return min(self.total_time, self.seek_offset + elapsed)

    def update_current_line(self):
        if not self.lyrics:
            return
        current_time = self.current_time()
        for i in range(len(self.lyrics)):
            if i < len(self.lyrics) - 1:
                if current_time >= self.lyrics[i][0] and current_time < self.lyrics[i+1][0]:
                    self.current_line_idx = i
                    return
            else:
                if current_time >= self.lyrics[i][0]:
                    self.current_line_idx = i
                    return
        self.current_line_idx = 0

    def seek_to(self, seconds):
        if seconds < 0:
            seconds = 0
        elif seconds > self.total_time:
            seconds = self.total_time
        
        self.audio_manager.seek(seconds)
        
        self.seek_offset = seconds
        self.playback_start_time = time.time()
        self.last_update_time = time.time()
        self.set_status(f"Seek → {self.ui.format_time(seconds)}", 1)

    def handle_input(self, key):
        if key == ord('q'):
            return False
        
        elif key == ord('p'):
            if self.paused:
                self.audio_manager.unpause()
                self.paused = False
                self.playback_start_time = time.time()
                self.set_status("Playing", 1)
            else:
                self.audio_manager.pause()
                self.paused = True
                self.seek_offset = self.current_time()
                self.set_status("Paused", 1)
        
        elif key == curses.KEY_LEFT:
            if not self.paused:
                new_pos = max(0, self.current_time() - 5)
                self.seek_to(new_pos)
        
        elif key == curses.KEY_RIGHT:
            if not self.paused:
                new_pos = min(self.total_time, self.current_time() + 5)
                self.seek_to(new_pos)
        
        return True

    def cleanup(self):
        self.audio_manager.cleanup()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def run(self):
        self.stdscr.nodelay(True)
        self.stdscr.timeout(50)
        self.ui.show_file_loader(self)
        
        while True:
            current_time = time.time()
            
            # Update animation
            self.ui.update_animation(current_time)
            
            # Update current line
            self.update_current_line()
            
            # Handle input
            key = self.stdscr.getch()
            if key != -1:
                if not self.handle_input(key):
                    break
            
            self.ui.draw(self)
            time.sleep(0.02)  # 50 FPS cap