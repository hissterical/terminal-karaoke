import pygame

class AudioManager:
    def __init__(self):
        self.sound = None
        
    def init_mixer(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
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
    
    def stop(self):
        pygame.mixer.music.stop()
        
    def cleanup(self):
        pygame.mixer.music.stop()
