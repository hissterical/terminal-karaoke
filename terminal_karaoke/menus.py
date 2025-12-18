import curses
import os
import time

class MenuManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
    def get_input(self, y, x, prompt=""):
        """Get text input from user"""
        if prompt:
            self.stdscr.addstr(y, x, prompt, curses.color_pair(7))
            y += 1
            
        user_input = ""
        while True:
            self.stdscr.addstr(y, x, " " * 50)
            self.stdscr.addstr(y, x, user_input + "_", curses.color_pair(2))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 10:  # Enter
                break
            elif key in [127, 8, 263]:  # Backspace
                user_input = user_input[:-1]
            elif 32 <= key <= 126:
                user_input += chr(key)
        return user_input
    
    def show_file_loader(self, player):
        """Show main menu"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " TERMINAL KARAOKE "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        options = [
            "1. Search and download song",
            "2. Play from library",
            "3. Playlists",
            "4. Load local files",
            "5. Quit"
        ]
        
        for i, option in enumerate(options):
            y = 4 + i
            x = (width - len(option)) // 2
            self.stdscr.addstr(y, x, option, curses.color_pair(7))
        
        self.stdscr.addstr(10, (width - 20) // 2, "Select option: ", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == ord('1'):
                self.show_search_menu(player)
                break
            elif key == ord('2'):
                self.show_library_menu(player)
                break
            elif key == ord('3'):
                from .playlist_ui import PlaylistUI
                playlist_ui = PlaylistUI(self.stdscr)
                playlist_ui.show_enhanced_playlist_selector(player)
                break
            elif key == ord('4'):
                self.show_local_file_loader(player)
                break
            elif key == ord('5') or key == ord('q'):
                return False
        
        return True
    
    def show_search_menu(self, player):
        """Show search and download menu"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        title = " SEARCH & DOWNLOAD SONG "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        instructions = [
            "Enter 'artist - title' format: (e.g., 'Tame Impala - Let it Happen')",
            "or song name if its popular and unique",
        ]
        for i, text in enumerate(instructions):
            y = 4 + i
            x = (width - len(text)) // 2
            if y < height - 2:
                self.stdscr.addstr(y, x, text, curses.color_pair(7))
        
        query = self.get_input(7, (width//2) - 20)
        if query:
            player.search_and_download(query)
        return True
    
    def show_library_menu(self, player):
        """Show songs available in the library folder"""
        library_path = player.downloader.download_dir
        if not os.path.exists(library_path):
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            msg = "Library folder not found"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
            self.stdscr.refresh()
            time.sleep(2)
            return False
            
        mp3_files = [f for f in os.listdir(library_path) if f.lower().endswith('.mp3')]
        
        if not mp3_files:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            msg = "No songs found in library"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
            self.stdscr.refresh()
            time.sleep(2)
            return False
            
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        title = " SELECT SONG FROM LIBRARY "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        self.stdscr.addstr(3, 2, "Available songs:", curses.color_pair(7))
        
        for i, mp3_file in enumerate(mp3_files[:height-8]):
            song_name = mp3_file[:-4]
            self.stdscr.addstr(5 + i, 4, f"{i+1}. {song_name}", curses.color_pair(7))
        
        self.stdscr.addstr(height-2, 2, "Enter song number or 'q' to quit: ", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == ord('q'):
                return False
            elif ord('1') <= key <= ord('9'):
                song_index = key - ord('1')
                if song_index < len(mp3_files):
                    mp3_file = mp3_files[song_index]
                    mp3_path = os.path.join(library_path, mp3_file)
                    lrc_path = mp3_path[:-4] + '.lrc'
                    
                    if not os.path.exists(lrc_path):
                        player.set_status("No lyrics file found", 3)
                        return False
                    
                    if player.load_song(mp3_path, lrc_path):
                        player.seek_to(0.0)
                        player.set_status("Now playing!", 2)
                        return True
            elif key == ord('0') and len(mp3_files) >= 10:
                mp3_file = mp3_files[9]
                mp3_path = os.path.join(library_path, mp3_file)
                lrc_path = mp3_path[:-4] + '.lrc'
                
                if not os.path.exists(lrc_path):
                    player.set_status("No lyrics file found", 3)
                    return False
                
                if player.load_song(mp3_path, lrc_path):
                    player.seek_to(0.0)
                    player.set_status("Now playing!", 2)
                    return True
    
    def show_local_file_loader(self, player):
        """Load local MP3 and LRC files"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        title = " LOAD LOCAL SONG AND LYRICS "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
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
        
        song_path = self.get_input(9, (width//2) - 10)
        lrc_path = self.get_input(10, (width//2) - 10)
        
        if song_path and lrc_path:
            if player.load_song(song_path, lrc_path):
                player.seek_to(0.0)
                player.set_status("Now playing!", 2)
        return True
    
    def show_download_progress(self, message):
        """Show download progress message"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        msg = f"Downloading: {message}"
        x = (width - len(msg)) // 2
        self.stdscr.addstr(height//2, x, msg, curses.color_pair(3))
        self.stdscr.refresh()

