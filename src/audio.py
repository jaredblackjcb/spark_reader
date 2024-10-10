import pygame
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav

def play_audio(audio_file):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def record_audio(duration=5, sample_rate=44100):
    input(f"Press enter to begin recording audio for {duration} seconds")
    # Record audio for the given duration (in seconds)
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until the recording is finished
    
    # Save the recording as a WAV file in the audio folder
    file_name = f"{uuid.uuid4()}.wav"
    file_path = os.path.join("audio", file_name)
    wav.write(file_path, sample_rate, recording)
    print(f"Recording saved as {file_path}")
    return file_name