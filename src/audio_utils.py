import pygame
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from pydub import AudioSegment
import threading
import numpy as np
import queue

# Global variables to control recording
is_recording = False
audio_queue = queue.Queue()

def play_audio(audio_file):
    # Play the given audio file using pygame
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def record_audio_thread():
    global is_recording, audio_queue
    
    with sd.InputStream(samplerate=44100, channels=1, dtype='int16') as stream:
        while is_recording:
            audio_chunk, overflowed = stream.read(1024)
            if not overflowed:
                audio_queue.put(audio_chunk)

def record_audio():
    global is_recording, audio_queue
    is_recording = True
    
    # Record audio indefinitely
    file_name = f"{uuid.uuid4()}.wav"
    file_path = os.path.join("audio", file_name)
    
    print("Recording... Use stop_audio_recording() to stop.")
    
    # Start recording in a separate thread
    recording_thread = threading.Thread(target=record_audio_thread)
    recording_thread.start()
    
    return file_path

def stop_audio_recording():
    global is_recording, audio_queue
    is_recording = False
    
    # Combine all recorded chunks
    recorded_chunks = []
    while not audio_queue.empty():
        recorded_chunks.append(audio_queue.get())
    
    recording = np.concatenate(recorded_chunks, axis=0)
    
    # Save the recorded audio to a file
    file_name = f"{uuid.uuid4()}.wav"
    file_path = os.path.join("audio", file_name)
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
