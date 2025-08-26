import curses
import pygame
import time
import os
import sys
import math
from collections import deque

# Initialize pygame mixer
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

class KaraokePlayer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.song_path = ""
        self.lrc_path = ""
        self.lyrics = []  # [(timestamp, line)]
        self.current_time = 0.0
        self.total_time = 0.0
        self.paused = False
        self.current_line_idx = 0
        self.visible_lines = 7
        self.progress_bar_width = 50
        self.dancing_cat_frames = self.create_dancing_cat_frames()
        self.cat_frame_idx = 0
        self.last_cat_update = time.time()
        self.cat_update_interval = 0.15  # seconds
        self.playback_speed = 1.0
        self.setup_colors()
        self.input_buffer = ""
        self.status_message = ""
        self.status_timer = 0
        self.controls = {
            'p': "Pause/Play",
            '←': "Back 5s",
            '→': "Forward 5s",
            'q': "Quit"
        }
        
    def setup_colors(self):
        """Initialize color pairs for the UI"""
        curses.start_color()
        curses.use_default_colors()
        
        # Try to set up colors, but fall back if terminal doesn't support
        try:
            curses.init_pair(1, curses.COLOR_CYAN, -1)     # Title
            curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Current line
            curses.init_pair(3, curses.COLOR_GREEN, -1)    # Progress bar
            curses.init_pair(4, curses.COLOR_RED, -1)      # Status messages
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # Controls
            curses.init_pair(6, 8, -1)                     # Dim text (gray)
            curses.init_pair(7, curses.COLOR_WHITE, -1)    # Normal text
        except:
            # Fallback for terminals that don't support 256 colors
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_BLACK, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
    
    def create_dancing_cat_frames(self):
        """Create ASCII art frames for the dancing cat animation"""
        frames = [
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "  > ^ <  "
            ],
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "   ^_^   "
            ],
            [
                "  /\\_/\\  ",
                " ( -.- ) ",
                "  > ^ <  "
            ],
            [
                "  /\\_/\\  ",
                " ( -.- ) ",
                "   ^_^   "
            ],
            [
                "  /\\_/\\  ",
                " ( o.o ) ",
                "  \\_^_/  "
            ],
            [
                "  /\\_/\\  ",
                " ( '.o ) ",
                "  > ^ <  "
            ]
        ]
        
        # Convert to single strings with proper formatting
        formatted_frames = []
        for frame in frames:
            max_len = max(len(line) for line in frame)
            padded_frame = [line.center(max_len) for line in frame]
            formatted_frames.append("\n".join(padded_frame))
            
        return formatted_frames

    def parse_lrc(self, lrc_path):
        """Parse LRC file into timestamped lyrics"""
        lyrics = []
        try:
            with open(lrc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Find timestamp part
                    if line[0] == '[':
                        end_bracket = line.find(']')
                        if end_bracket > 0:
                            timestamp_str = line[1:end_bracket]
                            text = line[end_bracket+1:].strip()
                            
                            # Parse timestamp: [mm:ss.xx]
                            try:
                                parts = timestamp_str.split(':')
                                if len(parts) == 2:
                                    minutes = int(parts[0])
                                    seconds_parts = parts[1].split('.')
                                    seconds = int(seconds_parts[0])
                                    hundredths = 0
                                    if len(seconds_parts) > 1:
                                        hundredths = int(seconds_parts[1].ljust(2, '0')[:2])
                                    total_seconds = minutes * 60 + seconds + hundredths / 100.0
                                    lyrics.append((total_seconds, text))
                            except:
                                continue
        except Exception as e:
            self.set_status(f"Error parsing LRC: {str(e)}", 3)
        
        # Sort by timestamp
        lyrics.sort(key=lambda x: x[0])
        return lyrics

    def load_song(self, song_path, lrc_path):
        """Load song and lyrics"""
        self.song_path = song_path
        self.lrc_path = lrc_path
        
        # Load song
        try:
            pygame.mixer.music.load(song_path)
            # Get song length using a temporary Sound object
            sound = pygame.mixer.Sound(song_path)
            self.total_time = sound.get_length()
            self.set_status(f"Loaded: {os.path.basename(song_path)}", 2)
        except Exception as e:
            self.set_status(f"Error loading song: {str(e)}", 3)
            return False
        
        # Parse lyrics
        self.lyrics = self.parse_lrc(lrc_path)
        if not self.lyrics:
            self.set_status("Warning: No lyrics found in LRC file", 2)
        
        return True

    def set_status(self, message, duration=1):
        """Set a status message with timeout"""
        self.status_message = message
        self.status_timer = time.time() + duration

    def update_current_line(self):
        """Update the current line index based on playback position"""
        if not self.lyrics:
            return
            
        for i in range(len(self.lyrics)):
            if i < len(self.lyrics) - 1:
                if self.current_time >= self.lyrics[i][0] and self.current_time < self.lyrics[i+1][0]:
                    self.current_line_idx = i
                    return
            else:
                if self.current_time >= self.lyrics[i][0]:
                    self.current_line_idx = i
                    return
        self.current_line_idx = 0

    def get_visible_lines(self):
        """Get the lines to display around the current line"""
        if not self.lyrics:
            return [], 0, 0
            
        start_idx = max(0, self.current_line_idx - (self.visible_lines // 2))
        end_idx = min(len(self.lyrics), start_idx + self.visible_lines)
        
        # Adjust if near the end
        if end_idx - start_idx < self.visible_lines and start_idx > 0:
            start_idx = max(0, end_idx - self.visible_lines)
            
        visible = self.lyrics[start_idx:end_idx]
        current_visible_idx = self.current_line_idx - start_idx
        
        return visible, start_idx, current_visible_idx

    def draw_progress_bar(self, y, x, width):
        """Draw a progress bar with percentage indicator"""
        # Calculate progress
        progress = min(1.0, max(0.0, self.current_time / self.total_time))
        filled = int(width * progress)
        
        # Draw bar
        bar = "█" * filled + "░" * (width - filled)
        self.stdscr.addstr(y, x, f"[{bar}]", curses.color_pair(3))
        
        # Draw time indicators
        time_text = f"{self.format_time(self.current_time)}/{self.format_time(self.total_time)}"
        time_x = x + (width // 2) - (len(time_text) // 2)
        self.stdscr.addstr(y, time_x, time_text, curses.color_pair(7))

    def draw_current_line_progress(self, line, y, x):
        """Draw the current line with color progress effect"""
        if not self.lyrics:
            return
            
        current_line_time, line_text = self.lyrics[self.current_line_idx]
        
        # Calculate line progress
        if self.current_line_idx < len(self.lyrics) - 1:
            next_line_time = self.lyrics[self.current_line_idx + 1][0]
        else:
            next_line_time = self.total_time
            
        line_duration = next_line_time - current_line_time
        if line_duration <= 0:
            line_progress = 1.0
        else:
            line_progress = min(1.0, max(0.0, (self.current_time - current_line_time) / line_duration))
        
        # Split the line based on progress
        num_colored = int(len(line_text) * line_progress)
        colored_text = line_text[:num_colored]
        remaining_text = line_text[num_colored:]
        
        # Draw with gradient effect
        self.stdscr.addstr(y, x, colored_text, curses.color_pair(2))
        self.stdscr.addstr(remaining_text, curses.color_pair(6))

    def format_time(self, seconds):
        """Format time as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def draw_ui(self):
        """Draw the entire UI"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Draw title
        title = " TERMINAL KARAOKE "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(0, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Draw song info
        if self.song_path:
            song_name = os.path.basename(self.song_path)
            self.stdscr.addstr(1, 2, f"Song: {song_name}", curses.color_pair(7))
        
        # Draw status message if active
        if time.time() < self.status_timer and self.status_message:
            status_x = (width - len(self.status_message)) // 2
            self.stdscr.addstr(2, status_x, self.status_message, curses.color_pair(4))
        
        # Draw lyrics area
        if self.lyrics:
            visible_lines, start_idx, current_visible_idx = self.get_visible_lines()
            
            # Calculate center position for lyrics
            lyrics_start_y = (height - len(visible_lines)) // 2 - 1
            
            # Draw previous lines (dimmed)
            for i, (timestamp, line) in enumerate(visible_lines[:current_visible_idx]):
                y = lyrics_start_y + i
                if 0 < y < height - 3:
                    x = (width - len(line)) // 2
                    self.stdscr.addstr(y, x, line, curses.color_pair(6))
            
            # Draw current line (with progress effect)
            if current_visible_idx < len(visible_lines):
                _, current_line = visible_lines[current_visible_idx]
                y = lyrics_start_y + current_visible_idx
                if 0 < y < height - 3:
                    x = (width - len(current_line)) // 2
                    self.draw_current_line_progress(current_line, y, x)
            
            # Draw next lines (dimmed)
            for i, (timestamp, line) in enumerate(visible_lines[current_visible_idx+1:]):
                y = lyrics_start_y + current_visible_idx + 1 + i
                if 0 < y < height - 3:
                    x = (width - len(line)) // 2
                    self.stdscr.addstr(y, x, line, curses.color_pair(6))
            
            # Draw dancing cat in the center
            cat_y = lyrics_start_y + len(visible_lines) // 2 - 1
            cat_frame = self.dancing_cat_frames[self.cat_frame_idx]
            cat_lines = cat_frame.split('\n')
            max_cat_width = max(len(line) for line in cat_lines)
            
            for i, line in enumerate(cat_lines):
                if 0 < cat_y + i < height - 3:
                    cat_x = (width - max_cat_width) // 2
                    self.stdscr.addstr(cat_y + i, cat_x, line, curses.color_pair(5))
        else:
            # No lyrics loaded
            msg = "Load .mp3 and .lrc files to start"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(6))
        
        # Draw progress bar
        if self.total_time > 0:
            bar_y = height - 3
            bar_x = (width - self.progress_bar_width) // 2
            self.draw_progress_bar(bar_y, bar_x, self.progress_bar_width)
        
        # Draw controls
        controls = " | ".join([f"<{k}> {v}" for k, v in self.controls.items()])
        controls_x = (width - len(controls)) // 2
        self.stdscr.addstr(height - 1, controls_x, controls, curses.color_pair(5))
        
        self.stdscr.refresh()

    def handle_input(self, key):
        """Handle user input"""
        if key == ord('q'):
            return False  # Quit
        
        elif key == ord('p'):
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.set_status("Playing", 1)
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.set_status("Paused", 1)
        
        elif key == curses.KEY_LEFT:
            if not self.paused and self.current_time > 5:
                new_pos = max(0, self.current_time - 5)
                pygame.mixer.music.stop()
                pygame.mixer.music.play(start=new_pos)
                self.set_status(f"Back 5s → {self.format_time(new_pos)}", 1)
        
        elif key == curses.KEY_RIGHT:
            if not self.paused and self.current_time < self.total_time - 5:
                new_pos = min(self.total_time, self.current_time + 5)
                pygame.mixer.music.stop()
                pygame.mixer.music.play(start=new_pos)
                self.set_status(f"Forward 5s → {self.format_time(new_pos)}", 1)
        
        elif key == ord('l'):
            self.input_buffer += 'l'
            if len(self.input_buffer) > 10:
                self.input_buffer = self.input_buffer[-10:]
            if "load" in self.input_buffer:
                self.show_file_loader()
        
        return True

    def show_file_loader(self):
        """Show file loader interface"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Draw title
        title = " LOAD SONG AND LYRICS "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Instructions
        instructions = [
            "Enter paths to your .mp3 and .lrc files",
            "Press ENTER after each path",
            "",
            "Song file (.mp3): ",
            "Lyrics file (.lrc): "
        ]
        
        for i, text in enumerate(instructions):
            y = 5 + i
            x = (width - len(text)) // 2
            if y < height - 2:
                self.stdscr.addstr(y, x, text, curses.color_pair(7))
        
        # Input fields
        song_path = ""
        lrc_path = ""
        
        self.stdscr.addstr(8, (width//2) - 10, song_path + "_", curses.color_pair(2))
        self.stdscr.addstr(9, (width//2) - 10, lrc_path + "_", curses.color_pair(2))
        self.stdscr.refresh()
        
        # Get song path
        self.stdscr.addstr(8, (width//2) - 10, " " * 30)
        self.stdscr.addstr(8, (width//2) - 10, song_path, curses.color_pair(2))
        self.stdscr.addstr(8, (width//2) - 10 + len(song_path), "_", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == 10:  # Enter
                break
            elif key == 127:  # Backspace
                song_path = song_path[:-1]
            elif 32 <= key <= 126:  # Printable character
                song_path += chr(key)
            
            # Redraw
            self.stdscr.addstr(8, (width//2) - 10, " " * 30)
            self.stdscr.addstr(8, (width//2) - 10, song_path, curses.color_pair(2))
            self.stdscr.addstr(8, (width//2) - 10 + len(song_path), "_", curses.color_pair(2))
            self.stdscr.refresh()
        
        # Get lrc path
        self.stdscr.addstr(9, (width//2) - 10, " " * 30)
        self.stdscr.addstr(9, (width//2) - 10, lrc_path, curses.color_pair(2))
        self.stdscr.addstr(9, (width//2) - 10 + len(lrc_path), "_", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == 10:  # Enter
                break
            elif key == 127:  # Backspace
                lrc_path = lrc_path[:-1]
            elif 32 <= key <= 126:  # Printable character
                lrc_path += chr(key)
            
            # Redraw
            self.stdscr.addstr(9, (width//2) - 10, " " * 30)
            self.stdscr.addstr(9, (width//2) - 10, lrc_path, curses.color_pair(2))
            self.stdscr.addstr(9, (width//2) - 10 + len(lrc_path), "_", curses.color_pair(2))
            self.stdscr.refresh()
        
        # Load the files
        if self.load_song(song_path, lrc_path):
            pygame.mixer.music.play()
            self.paused = False
            self.set_status("Now playing!", 2)
        
        return True

    def run(self):
        """Main application loop"""
        self.stdscr.nodelay(True)
        self.stdscr.timeout(50)  # 50ms timeout for input
        
        # Show file loader on startup
        self.show_file_loader()
        
        last_update = time.time()
        update_interval = 0.05  # 20 FPS
        
        while True:
            current_time = time.time()
            
            # Update animation frames
            if current_time - self.last_cat_update > self.cat_update_interval:
                self.cat_frame_idx = (self.cat_frame_idx + 1) % len(self.dancing_cat_frames)
                self.last_cat_update = current_time
            
            # Update playback position
            if not self.paused and pygame.mixer.music.get_busy():
                # Get position from mixer
                self.current_time = pygame.mixer.music.get_pos() / 1000.0
                if self.current_time < 0:  # When paused, get_pos returns -1
                    self.current_time = 0
                self.update_current_line()
            
            # Handle input
            key = self.stdscr.getch()
            if key != -1:
                if not self.handle_input(key):
                    break
            
            # Draw UI
            if current_time - last_update > update_interval:
                self.draw_ui()
                last_update = current_time
            
            # Small sleep to reduce CPU usage
            time.sleep(0.01)

def main(stdscr):
    # Configure curses
    curses.curs_set(0)  # Hide cursor
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    
    # Create and run player
    player = KaraokePlayer(stdscr)
    try:
        player.run()
    finally:
        # Clean up
        pygame.mixer.music.stop()
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

if __name__ == "__main__":
    print("Terminal Karaoke - Loading...")
    print("Make sure you have pygame installed: pip install pygame")
    print("Controls:")
    print("  p: Pause/Play")
    print("  ←: Back 5 seconds")
    print("  →: Forward 5 seconds")
    print("  q: Quit")
    print("\nStarting in 2 seconds...")
    time.sleep(2)
    curses.wrapper(main)