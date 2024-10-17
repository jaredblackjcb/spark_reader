import pygame
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from pydub import AudioSegment

def play_audio(audio_file):
    # Play the given audio file using pygame
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def record_audio(duration=None):
    # Record audio for a specified duration or indefinitely
    file_name = f"{uuid.uuid4()}.wav"
    file_path = os.path.join("audio", file_name)
    
    print("Recording... Press Ctrl+C to stop.")
    try:
        # Start recording
        recording = sd.rec(int(duration * 44100) if duration else None, samplerate=44100, channels=1, dtype='int16')
        sd.wait()  # Wait for the recording to complete
    except KeyboardInterrupt:
        sd.stop()  # Stop recording if interrupted
    
    # Save the recorded audio to a file
    wav.write(file_path, 44100, recording)
    print(f"Recording saved as {file_path}")
    return file_path

def split_audio(audio_file, timestamps):
    # Split the audio file into clips based on the provided timestamps
    audio = AudioSegment.from_wav(audio_file)
    audio_clips = []

    for i in range(len(timestamps)):
        # Calculate start and end times for each clip
        start_time = timestamps[i][0] * 1000  # Convert to milliseconds
        end_time = timestamps[i+1][0] * 1000 if i+1 < len(timestamps) else len(audio)
        
        # Extract the clip from the main audio
        clip = audio[start_time:end_time]
        clip_file = f"audio/clip_{i}.wav"
        clip.export(clip_file, format="wav")
        audio_clips.append(clip_file)

    return audio_clips
