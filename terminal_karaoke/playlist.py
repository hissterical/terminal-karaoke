import os
import random
import json
from pathlib import Path

class Playlist:
    def __init__(self, name, songs=None):
        self.name = name
        self.songs = songs or []  # List of (mp3_path, lrc_path) tuples
        self.current_index = 0
        self.shuffle_mode = False
        self.shuffle_order = []
        
    def add_song(self, mp3_path, lrc_path):
        """Add a song to the playlist"""
        self.songs.append((mp3_path, lrc_path))
        
    def remove_song(self, index):
        """Remove a song from the playlist"""
        if 0 <= index < len(self.songs):
            del self.songs[index]
            
    def get_current_song(self):
        """Get the current song"""
        if not self.songs:
            return None
        if self.shuffle_mode:
            if not self.shuffle_order:
                self.regenerate_shuffle()
            if self.current_index < len(self.shuffle_order):
                return self.songs[self.shuffle_order[self.current_index]]
            return None
        else:
            if self.current_index < len(self.songs):
                return self.songs[self.current_index]
            return None
            
    def next_song(self):
        """Move to next song"""
        if not self.songs:
            return None
        self.current_index += 1
        if self.current_index >= len(self.songs):
            self.current_index = 0
        return self.get_current_song()
        
    def previous_song(self):
        """Move to previous song"""
        if not self.songs:
            return None
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.songs) - 1
        return self.get_current_song()
        
    def toggle_shuffle(self):
        """Toggle shuffle mode"""
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.regenerate_shuffle()
        return self.shuffle_mode
        
    def regenerate_shuffle(self):
        """Generate new shuffle order"""
        self.shuffle_order = list(range(len(self.songs)))
        random.shuffle(self.shuffle_order)
        
    def reset(self):
        """Reset to first song"""
        self.current_index = 0
        if self.shuffle_mode:
            self.regenerate_shuffle()


class PlaylistManager:
    def __init__(self, library_path):
        self.library_path = library_path
        self.playlists = {}
        self.current_playlist = None
        self.playlists_dir = os.path.join(library_path, "playlists")
        os.makedirs(self.playlists_dir, exist_ok=True)
        self.load_playlists()
        
    def create_playlist(self, name):
        """Create a new playlist"""
        if name in self.playlists:
            return False
        self.playlists[name] = Playlist(name)
        self.save_playlist(name)
        return True
        
    def delete_playlist(self, name):
        """Delete a playlist"""
        if name in self.playlists:
            del self.playlists[name]
            playlist_file = os.path.join(self.playlists_dir, f"{name}.json")
            if os.path.exists(playlist_file):
                os.remove(playlist_file)
            return True
        return False
        
    def get_playlist(self, name):
        """Get a playlist by name"""
        return self.playlists.get(name)
        
    def list_playlists(self):
        """Get all playlist names"""
        return list(self.playlists.keys())
        
    def create_playlist_from_folder(self, folder_path, playlist_name=None):
        """Create a playlist from all songs in a folder"""
        if not os.path.exists(folder_path):
            return None
            
        if playlist_name is None:
            playlist_name = os.path.basename(folder_path)
            
        # Find all mp3 files with corresponding lrc files
        mp3_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(folder_path, file)
                lrc_path = mp3_path[:-4] + '.lrc'
                if os.path.exists(lrc_path):
                    mp3_files.append((mp3_path, lrc_path))
                    
        if not mp3_files:
            return None
            
        playlist = Playlist(playlist_name, mp3_files)
        self.playlists[playlist_name] = playlist
        self.save_playlist(playlist_name)
        return playlist
        
    def create_playlist_from_library(self):
        """Create a playlist from all songs in the main library"""
        return self.create_playlist_from_folder(self.library_path, "All Songs")
        
    def save_playlist(self, name):
        """Save playlist to JSON file"""
        if name not in self.playlists:
            return False
            
        playlist = self.playlists[name]
        playlist_file = os.path.join(self.playlists_dir, f"{name}.json")
        
        data = {
            "name": playlist.name,
            "songs": playlist.songs,
            "shuffle_mode": playlist.shuffle_mode
        }
        
        try:
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
            
    def load_playlists(self):
        """Load all playlists from JSON files"""
        if not os.path.exists(self.playlists_dir):
            return
            
        for file in os.listdir(self.playlists_dir):
            if file.endswith('.json'):
                playlist_file = os.path.join(self.playlists_dir, file)
                try:
                    with open(playlist_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Verify all songs still exist
                    valid_songs = []
                    for mp3_path, lrc_path in data.get("songs", []):
                        if os.path.exists(mp3_path) and os.path.exists(lrc_path):
                            valid_songs.append((mp3_path, lrc_path))
                    
                    if valid_songs:
                        playlist = Playlist(data["name"], valid_songs)
                        playlist.shuffle_mode = data.get("shuffle_mode", False)
                        self.playlists[data["name"]] = playlist
                except Exception:
                    continue
                    
    def scan_library_folders(self):
        """Scan library for subfolders and create playlists"""
        playlists_created = []
        
        if not os.path.exists(self.library_path):
            return playlists_created
            
        # Check for subdirectories
        for item in os.listdir(self.library_path):
            item_path = os.path.join(self.library_path, item)
            if os.path.isdir(item_path) and item != "playlists":
                # Create playlist from this folder
                playlist = self.create_playlist_from_folder(item_path, item)
                if playlist:
                    playlists_created.append(item)
                    
        return playlists_created

