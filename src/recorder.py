from src.image_context_controller import ImageContextController
from src.image_mapping import ImageMappingDB
from src.audio import record_audio, split_audio, stop_audio_recording
import cv2
import time
import threading

class Recorder:
    def __init__(self):
        # Initialize the recorder with necessary components
        self.book_context = None  # Stores the current book's identifier
        self.image_context = ImageContextController(on_stable_context=self.on_page_turn)  # Handles image context changes
        self.image_mapping_db = ImageMappingDB()  # Manages database operations for image-audio mappings
        self.recording_start_time = None  # Tracks when the recording started
        self.page_timestamps = []  # Stores (timestamp, image mapping) of detected page turns
        self.current_audio_file = None  # Holds the path to the current audio recording
    
    def on_page_turn(self, new_image_mapping):
        # Callback method triggered when a page turn is detected
        if self.recording_start_time is not None:
            # Calculate the timestamp of the page turn
            timestamp = time.time() - self.recording_start_time
            self.page_timestamps.append((timestamp, new_image_mapping))
            print(f"Page turn detected at {timestamp:.2f} seconds")

    def start_recording(self):
        # Begin the recording process
        self.recording_start_time = time.time()
        
        # Start audio recording in the background
        self.current_audio_file = record_audio()
        
        # Start monitoring for page turns
        self.image_context.run()

    def stop_recording(self):
        # End the recording process
        self.image_context.stop()
        
        # Stop the audio recording and get the final audio file path
        self.current_audio_file = stop_audio_recording()

    def process_recording(self):
        # Process the recorded audio and associate it with detected page turns
        audio_clips = split_audio(self.current_audio_file, self.page_timestamps)
        for i, (audio_clip, (_, image_mapping)) in enumerate(zip(audio_clips, self.page_timestamps)):
            sift_features = self.create_sift_features(image_mapping.image_path)
            image_mapping.audio_path = audio_clip
            image_mapping.sift_features = sift_features
            image_mapping.book_id = self.book_context
            
            self.image_mapping_db.add_mapping(
                image_mapping.book_id,
                image_mapping.image_path,
                image_mapping.audio_path,
                image_mapping.image_hash,
                image_mapping.sift_features
            )

    def create_sift_features(self, image_path):
        # Extract SIFT features from the given image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        sift = cv2.SIFT_create()
        _, descriptors = sift.detectAndCompute(img, None)
        return descriptors

    def set_book_context(self, book_id):
        # Set the current book context
        self.book_context = book_id

    def record_book(self):
        # Main method to record a book
        self.start_recording()
        input("Press Enter when you've finished reading the book...")
        self.stop_recording()
        self.process_recording()
