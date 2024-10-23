import pygame
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from pydub import AudioSegment
import threading
import numpy as np
import queue
from typing import List, Tuple

# Global variables to control recording
is_recording: bool = False
audio_queue: queue.Queue = queue.Queue()

def play_audio(audio_file: str) -> None:
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def record_audio_thread() -> None:
    global is_recording, audio_queue
    
    with sd.InputStream(samplerate=44100, channels=1, dtype='int16') as stream:
        while is_recording:
            audio_chunk, overflowed = stream.read(1024)
            if not overflowed:
                audio_queue.put(audio_chunk)

def record_audio() -> str:
    global is_recording, audio_queue
    is_recording = True
    
    file_name: str = f"{uuid.uuid4()}.wav"
    file_path: str = os.path.join("audio", file_name)
    
    print("Recording... Use stop_audio_recording() to stop.")
    
    recording_thread: threading.Thread = threading.Thread(target=record_audio_thread)
    recording_thread.start()
    
    return file_path

def stop_audio_recording() -> str:
    global is_recording, audio_queue
    is_recording = False
    
    recorded_chunks: List[np.ndarray] = []
    while not audio_queue.empty():
        recorded_chunks.append(audio_queue.get())
    
    recording: np.ndarray = np.concatenate(recorded_chunks, axis=0)
    
    file_name: str = f"{uuid.uuid4()}.wav"
    file_path: str = os.path.join("audio", file_name)
    wav.write(file_path, 44100, recording)
    print(f"Recording saved as {file_path}")
    return file_path

def split_audio(audio_file: str, timestamps: List[Tuple[float, float]]) -> List[str]:
    audio: AudioSegment = AudioSegment.from_wav(audio_file)
    audio_clips: List[str] = []

    for i in range(len(timestamps)):
        start_time: float = timestamps[i][0] * 1000
        end_time: float = timestamps[i+1][0] * 1000 if i+1 < len(timestamps) else len(audio)
        
        clip: AudioSegment = audio[start_time:end_time]
        clip_file: str = f"audio/clip_{i}.wav"
        clip.export(clip_file, format="wav")
        audio_clips.append(clip_file)

    return audio_clips
