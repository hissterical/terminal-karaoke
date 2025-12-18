import pyaudio
import wave
import threading
import os
from datetime import datetime
from pydub import AudioSegment

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.recording_thread = None
        self.frames = []
        self.audio = None
        self.stream = None
        self.recording_start_time = 0
        self.recording_end_time = 0
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        
        # Create recordings directory
        self.recordings_dir = "recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
    
    def start_recording(self, current_time):
        """Start recording audio from the microphone"""
        if self.is_recording:
            return False
        
        try:
            self.frames = []
            self.recording_start_time = current_time
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
    
    def _record_audio(self):
        """Internal method to record audio in a separate thread"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Error during recording: {e}")
                break
    
    def stop_recording(self, song_path, current_time):
        """Stop recording and merge with the song audio"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.recording_end_time = current_time
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Close the stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        
        # Save the recorded audio to a temporary file
        temp_mic_file = os.path.join(self.recordings_dir, "temp_mic.wav")
        try:
            wf = wave.open(temp_mic_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format) if self.audio else 2)
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
        except Exception as e:
            print(f"Error saving recorded audio: {e}")
            return None
        
        # Merge the recorded audio with the song
        output_path = self._merge_audio(song_path, temp_mic_file)
        
        # Clean up temporary file
        try:
            os.remove(temp_mic_file)
        except:
            pass
        
        return output_path
    
    def _merge_audio(self, song_path, mic_path):
        """Merge the song audio and microphone audio"""
        try:
            # Load audio files
            song = AudioSegment.from_file(song_path)
            mic = AudioSegment.from_wav(mic_path)
            
            # Extract only the segment of the song that was playing during recording
            start_ms = int(self.recording_start_time * 1000)
            end_ms = int(self.recording_end_time * 1000)
            song_segment = song[start_ms:end_ms]
            
            # Match the length - if mic is shorter, pad it; if longer, trim it
            if len(mic) < len(song_segment):
                silence = AudioSegment.silent(duration=len(song_segment) - len(mic))
                mic = mic + silence
            elif len(mic) > len(song_segment):
                mic = mic[:len(song_segment)]
            
            # Boost mic volume by 6dB to make it louder
            mic = mic + 6
            
            # Overlay the microphone audio on the song segment
            merged = song_segment.overlay(mic)
            
            # Generate output filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            song_name = os.path.splitext(os.path.basename(song_path))[0]
            output_filename = f"{song_name}_karaoke_{timestamp}.mp3"
            output_path = os.path.join(self.recordings_dir, output_filename)
            
            # Export the merged audio
            merged.export(output_path, format="mp3")
            
            return output_path
        except Exception as e:
            print(f"Error merging audio: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()

