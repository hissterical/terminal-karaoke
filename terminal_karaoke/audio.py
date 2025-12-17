import pygame

class AudioManager:
    def __init__(self):
        self.sound = None
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        
    def init_mixer(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.music.set_volume(self.volume)
        
    def load_song(self, song_path):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(song_path)
            self.sound = pygame.mixer.Sound(song_path)
            length = self.sound.get_length()
            return True, length
        except Exception as e:
            return False, 0.0
            
    def seek(self, seconds):
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=seconds)
        
    def pause(self):
        pygame.mixer.music.pause()
        
    def unpause(self):
        pygame.mixer.music.unpause()
        
    def get_position(self):
        return pygame.mixer.music.get_pos()
    
    def set_volume(self, volume):
        """Set volume between 0.0 and 1.0"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        return self.volume
    
    def increase_volume(self, increment=0.1):
        """Increase volume by increment"""
        return self.set_volume(self.volume + increment)
    
    def decrease_volume(self, decrement=0.1):
        """Decrease volume by decrement"""
        return self.set_volume(self.volume - decrement)
    
    def get_volume(self):
        """Get current volume"""
        return self.volume
        
    def cleanup(self):
        pygame.mixer.music.stop()