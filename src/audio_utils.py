import pygame
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from pydub import AudioSegment
import threading
import numpy as np
import queue
from typing import List, Tuple, Optional

# Global variables to control recording
is_recording: bool = False
audio_queue: queue.Queue = queue.Queue()

# Audio configuration matching your working ALSA settings
SAMPLE_RATE: int = 16000
CHANNELS: int = 2
DTYPE: str = 'int16'  # Matches S16_LE format

def play_audio(audio_file: str) -> None:
    """
    Play an audio file using pygame mixer.
    
    Args:
        audio_file (str): Path to the audio file to play
    """
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

def record_audio_thread() -> None:
    """Background thread function for recording audio"""
    global is_recording, audio_queue
    
    try:
        # Configure sounddevice to use the same settings as your working arecord command
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE
        ) as stream:
            while is_recording:
                audio_chunk, overflowed = stream.read(1024)
                if not overflowed:
                    audio_queue.put(audio_chunk)
                elif overflowed:
                    print("Warning: Audio buffer overflowed")
    except sd.PortAudioError as e:
        print(f"Error accessing audio device: {e}")
        is_recording = False

def record_audio() -> Optional[str]:
    """
    Start recording audio from the ReSpeaker microphone.
    
    Returns:
        Optional[str]: Path to the recorded file, or None if recording setup fails
    """
    global is_recording, audio_queue
    
    # Clear any existing audio in the queue
    while not audio_queue.empty():
        audio_queue.get()
    
    is_recording = True
    file_name: str = f"{uuid.uuid4()}.wav"
    # Ensure audio directory exists
    os.makedirs("audio", exist_ok=True)
    file_path: str = os.path.join("audio", file_name)
    
    
    print("Recording... Use stop_audio_recording() to stop.")
    
    recording_thread: threading.Thread = threading.Thread(target=record_audio_thread)
    recording_thread.start()
    
    return file_path

def stop_audio_recording() -> Optional[str]:
    """
    Stop recording and save the audio file.
    
    Returns:
        Optional[str]: Path to the saved audio file, or None if no audio was recorded
    """
    global is_recording, audio_queue
    is_recording = False
    
    recorded_chunks: List[np.ndarray] = []
    while not audio_queue.empty():
        recorded_chunks.append(audio_queue.get())
    
    if not recorded_chunks:
        print("No audio data was recorded")
        return None
    
    try:
        recording: np.ndarray = np.concatenate(recorded_chunks, axis=0)
        
        file_name: str = f"{uuid.uuid4()}.wav"
        file_path: str = os.path.join("audio", file_name)
        
        # Save with the same sample rate used during recording
        wav.write(file_path, SAMPLE_RATE, recording)
        print(f"Recording saved as {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving recording: {e}")
        return None

def split_audio(audio_file: str, timestamps: List[Tuple[float, float]]) -> List[str]:
    """
    Split an audio file into multiple clips based on timestamps.
    
    Args:
        audio_file (str): Path to the audio file to split
        timestamps (List[Tuple[float, float]]): List of (start, end) timestamps in seconds
    
    Returns:
        List[str]: List of paths to the generated audio clips
    """
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
