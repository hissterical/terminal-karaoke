import curses
import os
import time

class PlaylistUI:
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
    
    def show_enhanced_playlist_selector(self, player):
        """Show playlists with All Songs as default option"""
        all_songs = player.playlist_manager.get_playlist("All Songs")
        if not all_songs:
            all_songs = player.playlist_manager.create_playlist_from_library()
        
        playlists = player.playlist_manager.list_playlists()
        
        if "All Songs" in playlists:
            playlists.remove("All Songs")
            playlists.insert(0, "All Songs")
        
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " SELECT PLAYLIST "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
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
        
        for i, playlist_name in enumerate(playlists[:height-10]):
            playlist = player.playlist_manager.get_playlist(playlist_name)
            song_count = len(playlist.songs)
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
                return self.show_enhanced_playlist_selector(player)
            elif key == ord('e'):
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
    
    def show_create_playlist(self, player):
        """Create a new playlist by selecting songs"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = " CREATE NEW PLAYLIST "
        title_x = (width - len(title)) // 2
        self.stdscr.addstr(2, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        
        self.stdscr.addstr(5, (width - 40) // 2, "Enter playlist name:", curses.color_pair(7))
        playlist_name = self.get_input(6, (width - 30) // 2)
        
        if not playlist_name:
            return False
        
        if player.playlist_manager.get_playlist(playlist_name):
            self.stdscr.clear()
            msg = "Playlist already exists!"
            x = (width - len(msg)) // 2
            self.stdscr.addstr(height//2, x, msg, curses.color_pair(4))
            self.stdscr.refresh()
            time.sleep(2)
            return False
        
        if player.playlist_manager.create_playlist(playlist_name):
            playlist = player.playlist_manager.get_playlist(playlist_name)
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
        
        mp3_files = []
        for file in os.listdir(library_path):
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(library_path, file)
                lrc_path = mp3_path[:-4] + '.lrc'
                if os.path.exists(lrc_path):
                    mp3_files.append((file[:-4], mp3_path, lrc_path))
        
        if not mp3_files:
            return
        
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            title = f" ADD SONGS TO: {playlist.name} "
            title_x = (width - len(title)) // 2
            self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(3, 2, f"Songs in playlist: {len(playlist.songs)}", curses.color_pair(3))
            self.stdscr.addstr(4, 2, "Available songs:", curses.color_pair(7))
            
            for i, (name, mp3_path, lrc_path) in enumerate(mp3_files[:height-10]):
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
        
        mp3_files = []
        for file in os.listdir(library_path):
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(library_path, file)
                lrc_path = mp3_path[:-4] + '.lrc'
                if os.path.exists(lrc_path):
                    mp3_files.append((file[:-4], mp3_path, lrc_path))
        
        if not mp3_files:
            return
        
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            title = f" EDIT: {playlist.name} "
            title_x = (width - len(title)) // 2
            self.stdscr.addstr(1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
            
            delete_instr = "Press 'd' to delete this playlist"
            self.stdscr.addstr(1, width - len(delete_instr) - 2, delete_instr, curses.color_pair(4))
            
            self.stdscr.addstr(3, 2, f"Songs in playlist: {len(playlist.songs)}", curses.color_pair(3))
            self.stdscr.addstr(4, 2, "Available songs (toggle with numbers):", curses.color_pair(7))
            
            for i, (name, mp3_path, lrc_path) in enumerate(mp3_files[:height-10]):
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

