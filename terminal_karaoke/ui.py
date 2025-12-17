import curses
import os
import time

class UI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.visible_lines = 7
        self.progress_bar_width = 50
        self.dancing_cat_frames = self.create_dancing_cat_frames()
        self.cat_frame_idx = 0
        self.last_cat_update = time.time()
        self.cat_update_interval = 0.15
        self.setup_colors()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        try:
            curses.init_pair(1, curses.COLOR_CYAN, -1)      # Title
            curses.init_pair(2, curses.COLOR_YELLOW, -1)    # Current line (highlighted)
            curses.init_pair(3, curses.COLOR_GREEN, -1)     # Progress bar
            curses.init_pair(4, curses.COLOR_RED, -1)       # Error/status
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)   # Cat/controls
            curses.init_pair(6, 8, -1)                      # Past lyrics (darker)
            curses.init_pair(7, curses.COLOR_WHITE, -1)     # Normal text
            curses.init_pair(8, curses.COLOR_BLUE, -1)      # Future lyrics (brighter)
        except:
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_BLACK, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
            curses.init_pair(8, curses.COLOR_BLUE, -1)

    def create_dancing_cat_frames(self):
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
        formatted_frames = []
        for frame in frames:
            max_len = max(len(line) for line in frame)
            padded_frame = [line.center(max_len) for line in frame]
            formatted_frames.append("\n".join(padded_frame))
        return formatted_frames

    def update_animation(self, current_time):
        if current_time - self.last_cat_update > self.cat_update_interval:
            self.cat_frame_idx = (self.cat_frame_idx + 1) % len(self.dancing_cat_frames)
            self.last_cat_update = current_time

    def get_visible_lines(self, player):
        if not player.lyrics:
            return [], 0, 0
        start_idx = max(0, player.current_line_idx - (self.visible_lines // 2))
        end_idx = min(len(player.lyrics), start_idx + self.visible_lines)
        if end_idx - start_idx < self.visible_lines and start_idx > 0:
            start_idx = max(0, end_idx - self.visible_lines)
        visible = player.lyrics[start_idx:end_idx]
        current_visible_idx = player.current_line_idx - start_idx
        return visible, start_idx, current_visible_idx

    def draw_progress_bar(self, y, x, width, current_time, total_time):
        progress = min(1.0, max(0.0, current_time / total_time)) if total_time > 0 else 0
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        self.stdscr.addstr(y, x, f"[{bar}]", curses.color_pair(3))
        
        time_text = f"{self.format_time(current_time)}/{self.format_time(total_time)}"
        time_y = y - 1
        time_x = x + (width // 2) - (len(time_text) // 2)
        if time_y > 0:
            self.stdscr.addstr(time_y, time_x, time_text, curses.color_pair(7))

    def format_time(self, seconds):
        if seconds is None or seconds < 0:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def draw_lyrics(self, player):
        """Draw lyrics with different colors for past, current, and future lines"""
        if not player.lyrics:
            return
            
        current_time = player.current_time()
        visible_lines, start_idx, current_visible_idx = self.get_visible_lines(player)
        height, width = self.stdscr.getmaxyx()
        lyrics_start_y = (height - len(visible_lines)) // 2
        
        for i, (timestamp, line) in enumerate(visible_lines):
            y = lyrics_start_y + i
            if 0 < y < height - 5:
                x = (width - len(line)) // 2
                
                # Determine color based on timing
                if i < current_visible_idx:
                    # Past line
                    self.stdscr.addstr(y, x, line, curses.color_pair(6))
                elif i == current_visible_idx:
                    # Current line with progress highlighting
                    current_line_time = player.lyrics[player.current_line_idx][0]
                    next_line_time = (
                        player.lyrics[player.current_line_idx + 1][0] 
                        if player.current_line_idx < len(player.lyrics) - 1 
                        else player.total_time
                    )
                    self.draw_current_line_progress(
                        line, y, x, 
                        current_time, current_line_time, next_line_time
                    )
                else:
                    # Future line
                    self.stdscr.addstr(y, x, line, curses.color_pair(8))

    def draw_current_line_progress(self, line_text, y, x, current_time, current_line_time, next_line_time):
        """Draw current line with progress highlighting"""
        if not line_text:
            return
        line_duration = next_line_time - current_line_time
        if line_duration <= 0:
            line_progress = 1.0
        else:
            line_progress = min(1.0, max(0.0, (current_time - current_line_time) / line_duration))
        num_colored = int(len(line_text) * line_progress)
        completed_text = line_text[:num_colored]
        remaining_text = line_text[num_colored:]
        self.stdscr.addstr(y, x, completed_text, curses.color_pair(2))  # Past color (darker)
        self.stdscr.addstr(remaining_text, curses.color_pair(8))  # Current color (brighter/yellow)

    def draw(self, player):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Get current time once for consistency
        current_time = player.current_time()
        
        title = " TERMINAL KARAOKE "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(0, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Show playlist info if in playlist mode
        if player.playlist_mode and player.current_playlist:
            shuffle_icon = "🔀 " if player.current_playlist.shuffle_mode else ""
            playlist_info = f"{shuffle_icon}Playlist: {player.current_playlist.name} [{player.current_playlist.current_index + 1}/{len(player.current_playlist.songs)}]"
            info_x = (width - len(playlist_info)) // 2
            self.stdscr.addstr(1, info_x, playlist_info, curses.color_pair(5))
            song_line = 2
        else:
            song_line = 1
        
        if player.song_path:
            song_name = os.path.basename(player.song_path)
            self.stdscr.addstr(song_line, 2, f"Song: {song_name}", curses.color_pair(7))
        
        if time.time() < player.status_timer and player.status_message:
            status_x = (width - len(player.status_message)) // 2
            status_y = song_line + 1
            self.stdscr.addstr(status_y, status_x, player.status_message, curses.color_pair(4))
        
        if player.lyrics:
            # Draw lyrics with color coding
            self.draw_lyrics(player)
            
            # Draw dancing cat
            height, width = self.stdscr.getmaxyx()
            visible_lines, start_idx, current_visible_idx = self.get_visible_lines(player)
            lyrics_start_y = (height - len(visible_lines)) // 2
            cat_y = lyrics_start_y - 4
            cat_frame = self.dancing_cat_frames[self.cat_frame_idx]
            cat_lines = cat_frame.split('\n')
            for i, line in enumerate(cat_lines):
                if 0 < cat_y + i < height - 5:
                    cat_x = (width - max(len(l) for l in cat_lines)) // 2
                    self.stdscr.addstr(cat_y + i, cat_x, line, curses.color_pair(5))
        else:
            msg = "Load .mp3 and .lrc files to start"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(6))
        
        if player.total_time > 0:
            bar_y = height - 3
            bar_x = (width - self.progress_bar_width) // 2
            self.draw_progress_bar(bar_y, bar_x, self.progress_bar_width, current_time, player.total_time)
        
        controls = " | ".join([f"<{k}> {v}" for k, v in player.controls.items()])
        controls_x = (width - len(controls)) // 2
        self.stdscr.addstr(height - 1, controls_x, controls, curses.color_pair(5))
        
        self.stdscr.refresh()

    def get_input(self, y, x, prompt=""):
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

    def show_search_menu(self, player):
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
            
        # Find MP3 files in library
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
            
        # Display menu
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        title = " SELECT SONG FROM LIBRARY "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        self.stdscr.addstr(3, 2, "Available songs:", curses.color_pair(7))
        
        # Display songs with numbers
        for i, mp3_file in enumerate(mp3_files[:height-8]):
            song_name = mp3_file[:-4]  # Remove .mp3 extension
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
                    
                    # Check if LRC file exists
                    if not os.path.exists(lrc_path):
                        player.set_status("No lyrics file found", 3)
                        return False
                    
                    if player.load_song(mp3_path, lrc_path):
                        player.seek_to(0.0)
                        player.set_status("Now playing!", 2)
                        return True
            elif key == ord('0') and len(mp3_files) >= 10:
                # Handle 10th song
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

    def show_file_loader(self, player):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Show menu options
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
                # Go directly to playlist selector with All Songs as default
                self.show_enhanced_playlist_selector(player)
                break
            elif key == ord('4'):
                self.show_local_file_loader(player)
                break
            elif key == ord('5') or key == ord('q'):
                return False
        
        return True

    def show_local_file_loader(self, player):
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
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        msg = f"Downloading: {message}"
        x = (width - len(msg)) // 2
        self.stdscr.addstr(height//2, x, msg, curses.color_pair(3))
        self.stdscr.refresh()
    
    def show_playlist_menu(self, player):
        """Show playlist management menu"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " PLAYLIST MENU "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        options = [
            "1. Play existing playlist",
            "2. Create new playlist",
            "3. Create playlist from folder",
            "4. Create 'All Songs' playlist",
            "5. Back to main menu"
        ]
        
        for i, option in enumerate(options):
            y = 4 + i
            x = (width - len(option)) // 2
            self.stdscr.addstr(y, x, option, curses.color_pair(7))
        
        self.stdscr.addstr(11, (width - 20) // 2, "Select option: ", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == ord('1'):
                self.show_playlist_selector(player)
                break
            elif key == ord('2'):
                self.show_create_playlist(player)
                break
            elif key == ord('3'):
                self.show_create_playlist_from_folder(player)
                break
            elif key == ord('4'):
                playlist = player.playlist_manager.create_playlist_from_library()
                if playlist:
                    player.load_playlist(playlist)
                    player.set_status("Playing All Songs", 2)
                else:
                    player.set_status("No songs in library", 2)
                break
            elif key == ord('5') or key == ord('q'):
                break
        return True
    
    def show_enhanced_playlist_selector(self, player):
        """Show playlists with All Songs as default option"""
        # Ensure All Songs playlist exists
        all_songs = player.playlist_manager.get_playlist("All Songs")
        if not all_songs:
            all_songs = player.playlist_manager.create_playlist_from_library()
        
        playlists = player.playlist_manager.list_playlists()
        
        # Put All Songs first if it exists
        if "All Songs" in playlists:
            playlists.remove("All Songs")
            playlists.insert(0, "All Songs")
        
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " SELECT PLAYLIST "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Add create/edit instructions in top-right
        instruction = "Press 'c' to create | 'e' to edit"
        self.stdscr.addstr(1, width - len(instruction) - 2, instruction, curses.color_pair(5))
        
        if not playlists:
            msg = "No songs in library. Download or add songs first!"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
            self.stdscr.addstr(height-2, 2, "Press 'c' to create playlist or 'q' to go back", curses.color_pair(2))
            self.stdscr.refresh()
            while True:
                key = self.stdscr.getch()
                if key == ord('q'):
                    return False
                elif key == ord('c'):
                    self.show_create_playlist(player)
                    return False
            return False
        
        self.stdscr.addstr(3, 2, "Available playlists:", curses.color_pair(7))
        
        # Display playlists
        for i, playlist_name in enumerate(playlists[:height-10]):
            playlist = player.playlist_manager.get_playlist(playlist_name)
            song_count = len(playlist.songs)
            # Highlight All Songs
            if playlist_name == "All Songs":
                display = f"{i+1}. {playlist_name} ({song_count} songs) [Default]"
                self.stdscr.addstr(5 + i, 4, display, curses.color_pair(3) | curses.A_BOLD)
            else:
                display = f"{i+1}. {playlist_name} ({song_count} songs)"
                self.stdscr.addstr(5 + i, 4, display, curses.color_pair(7))
        
        self.stdscr.addstr(height-2, 2, "Enter number, 'c' to create, 'e' to edit, or 'q' to go back: ", curses.color_pair(2))
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == ord('q'):
                return False
            elif key == ord('c'):
                self.show_create_playlist(player)
                # Refresh the playlist view after creating
                return self.show_enhanced_playlist_selector(player)
            elif key == ord('e'):
                # Edit existing playlist
                self.stdscr.addstr(height-1, 2, "Enter playlist number to edit: ", curses.color_pair(3))
                self.stdscr.refresh()
                edit_key = self.stdscr.getch()
                if ord('1') <= edit_key <= ord('9'):
                    idx = edit_key - ord('1')
                    if idx < len(playlists):
                        playlist = player.playlist_manager.get_playlist(playlists[idx])
                        if playlist and playlist.name != "All Songs":
                            self.edit_playlist(player, playlist)
                            return self.show_enhanced_playlist_selector(player)
                        elif playlist and playlist.name == "All Songs":
                            self.stdscr.clear()
                            msg = "Cannot edit 'All Songs' playlist"
                            x = (width - len(msg)) // 2
                            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
                            self.stdscr.refresh()
                            time.sleep(1.5)
                            return self.show_enhanced_playlist_selector(player)
            elif ord('1') <= key <= ord('9'):
                idx = key - ord('1')
                if idx < len(playlists):
                    playlist = player.playlist_manager.get_playlist(playlists[idx])
                    if playlist:
                        player.load_playlist(playlist)
                        return True
        return False
    
    def show_playlist_selector(self, player):
        """Legacy method - redirects to enhanced version"""
        return self.show_enhanced_playlist_selector(player)
    
    def show_create_playlist(self, player):
        """Create a new playlist by selecting songs"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " CREATE NEW PLAYLIST "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Get playlist name
        self.stdscr.addstr(5, (width - 40) // 2, "Enter playlist name:", curses.color_pair(7))
        playlist_name = self.get_input(6, (width - 30) // 2)
        
        if not playlist_name:
            return False
        
        # Check if playlist exists
        if player.playlist_manager.get_playlist(playlist_name):
            self.stdscr.clear()
            msg = "Playlist already exists!"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
            self.stdscr.refresh()
            time.sleep(2)
            return False
        
        # Create empty playlist
        if player.playlist_manager.create_playlist(playlist_name):
            playlist = player.playlist_manager.get_playlist(playlist_name)
            
            # Add songs from library
            self.add_songs_to_playlist(player, playlist)
            
            player.playlist_manager.save_playlist(playlist_name)
            player.set_status(f"Created: {playlist_name}", 2)
            return True
        return False
    
    def add_songs_to_playlist(self, player, playlist):
        """Add songs from library to a playlist"""
        library_path = player.downloader.download_dir
        if not os.path.exists(library_path):
            return
        
        # Get all mp3 files
        mp3_files = []
        for file in os.listdir(library_path):
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(library_path, file)
                lrc_path = mp3_path[:-4] + '.lrc'
                if os.path.exists(lrc_path):
                    mp3_files.append((file[:-4], mp3_path, lrc_path))
        
        if not mp3_files:
            return
        
        # Show song selection
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            title = f" ADD SONGS TO: {playlist.name} "
            title_x = (width - len(title)) // 2
            self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(3, 2, f"Songs in playlist: {len(playlist.songs)}", curses.color_pair(3))
            self.stdscr.addstr(4, 2, "Available songs:", curses.color_pair(7))
            
            for i, (name, mp3_path, lrc_path) in enumerate(mp3_files[:height-10]):
                # Check if already in playlist
                in_playlist = (mp3_path, lrc_path) in playlist.songs
                marker = "[+] " if in_playlist else "[ ] "
                display = f"{i+1}. {marker}{name}"
                color = curses.color_pair(3) if in_playlist else curses.color_pair(7)
                self.stdscr.addstr(6 + i, 4, display, color)
            
            self.stdscr.addstr(height-3, 2, "Enter number to toggle, 'd' when done: ", curses.color_pair(2))
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == ord('d'):
                break
            elif key == ord('q'):
                break
            elif ord('1') <= key <= ord('9'):
                idx = key - ord('1')
                if idx < len(mp3_files):
                    name, mp3_path, lrc_path = mp3_files[idx]
                    if (mp3_path, lrc_path) in playlist.songs:
                        playlist.songs.remove((mp3_path, lrc_path))
                    else:
                        playlist.add_song(mp3_path, lrc_path)
    
    def edit_playlist(self, player, playlist):
        """Edit an existing playlist - add/remove songs"""
        library_path = player.downloader.download_dir
        if not os.path.exists(library_path):
            return
        
        # Get all mp3 files
        mp3_files = []
        for file in os.listdir(library_path):
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(library_path, file)
                lrc_path = mp3_path[:-4] + '.lrc'
                if os.path.exists(lrc_path):
                    mp3_files.append((file[:-4], mp3_path, lrc_path))
        
        if not mp3_files:
            return
        
        # Show song selection
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            title = f" EDIT: {playlist.name} "
            title_x = (width - len(title)) // 2
            self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
            
            # Add delete instruction
            delete_instr = "Press 'd' to delete this playlist"
            self.stdscr.addstr(1, width - len(delete_instr) - 2, delete_instr, curses.color_pair(4))
            
            self.stdscr.addstr(3, 2, f"Songs in playlist: {len(playlist.songs)}", curses.color_pair(3))
            self.stdscr.addstr(4, 2, "Available songs (toggle with numbers):", curses.color_pair(7))
            
            for i, (name, mp3_path, lrc_path) in enumerate(mp3_files[:height-10]):
                # Check if already in playlist
                in_playlist = (mp3_path, lrc_path) in playlist.songs
                marker = "[+] " if in_playlist else "[ ] "
                display = f"{i+1}. {marker}{name}"
                color = curses.color_pair(3) if in_playlist else curses.color_pair(7)
                self.stdscr.addstr(6 + i, 4, display, color)
            
            self.stdscr.addstr(height-3, 2, "Toggle songs, 'd' to delete playlist, 's' to save & exit: ", curses.color_pair(2))
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == ord('s'):
                player.playlist_manager.save_playlist(playlist.name)
                self.stdscr.clear()
                msg = f"Saved {playlist.name}!"
                x = (width - len(msg)) // 2
                self.stdscr.addstr(height//2, x, msg, curses.color_pair(3))
                self.stdscr.refresh()
                time.sleep(1)
                break
            elif key == ord('q'):
                break
            elif key == ord('d'):
                # Confirm deletion
                self.stdscr.addstr(height-2, 2, f"Delete '{playlist.name}'? (y/n): ", curses.color_pair(4) | curses.A_BOLD)
                self.stdscr.refresh()
                confirm = self.stdscr.getch()
                if confirm == ord('y'):
                    player.playlist_manager.delete_playlist(playlist.name)
                    self.stdscr.clear()
                    msg = f"Deleted {playlist.name}"
                    x = (width - len(msg)) // 2
                    self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
                    self.stdscr.refresh()
                    time.sleep(1)
                    break
            elif ord('1') <= key <= ord('9'):
                idx = key - ord('1')
                if idx < len(mp3_files):
                    name, mp3_path, lrc_path = mp3_files[idx]
                    if (mp3_path, lrc_path) in playlist.songs:
                        playlist.songs.remove((mp3_path, lrc_path))
                    else:
                        playlist.add_song(mp3_path, lrc_path)
    
    def show_create_playlist_from_folder(self, player):
        """Create playlist from a folder"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " CREATE PLAYLIST FROM FOLDER "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Scan for folders
        created = player.playlist_manager.scan_library_folders()
        
        if created:
            self.stdscr.addstr(5, 4, f"Created {len(created)} playlist(s):", curses.color_pair(3))
            for i, name in enumerate(created[:height-10]):
                self.stdscr.addstr(7 + i, 6, f"- {name}", curses.color_pair(7))
        else:
            msg = "No folders with songs found in library"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
        
        self.stdscr.addstr(height-2, 2, "Press any key to continue...", curses.color_pair(2))
        self.stdscr.refresh()
        self.stdscr.getch()
        return True
