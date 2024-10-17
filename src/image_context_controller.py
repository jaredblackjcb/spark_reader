import threading
import time
import imagehash
from PIL import Image
import cv2
from collections import deque
import os
import uuid
from src.image_mapping import ImageMapping

'''
 TODO: Use a queue to store the last few seconds of image hashes and hamming distances to make
 this more context aware of history so it doesn't use a sudden change like an image
 captured mid-page turn as the key image and the rest of the image hashes are really close to the
 threshold but not past it. I want to avoid storing a bad image hash as the key image for the audio
 lookup. Otherwise that page will always have problems.
 I should update the current image hash as I go so as it approaches 0 it means the image stays 
 relatively unchanged. The key hash for audio file storage mapping should only be saved after
 the hamming distance for the last few checks has been close to zero. Use a derivativee or rate of change
 of hamming distance instead of just the distance from the previous value to determine when to set the current_key_image_hash.
'''

class ImageContextController:
    def __init__(self, refresh_rate=0.4, history_size=2, stable_threshold=10, max_hamming_distance=15, on_stable_context=None):
        self.current_image_mapping = None  # Stores the current ImageMapping object
        self.hamming_history = deque(maxlen=history_size)
        self.hamming_delta = deque(maxlen=history_size)
        self.hash_history = deque(maxlen=history_size)
        self.refresh_rate = refresh_rate
        self.stable_threshold = stable_threshold
        self.max_hamming_distance = max_hamming_distance
        self.is_running = False
        self._thread = None
        self.on_stable_context = on_stable_context
        self.previous_page_hash = None

    def _set_image_context(self, new_image, new_image_hash):
        """Set the current image as the key context for audio lookup."""
        image_path = self._save_image(new_image)
        self.current_image_mapping = ImageMapping(image_path, str(new_image_hash))
        print(f"New image mapping created: {self.current_image_mapping.image_hash}")
        if self.on_stable_context:
            self.on_stable_context(self.current_image_mapping)

    def _save_image(self, image):
        """Save the captured image with a unique filename."""
        filename = f"{uuid.uuid4()}.jpg"
        image_path = os.path.join("images", filename)
        image.save(image_path)
        return image_path

    def _capture_image(self):
        """Capture an image from the camera and return a PIL image."""
        cap = cv2.VideoCapture(0)
        time.sleep(0.1)  # Short delay to stabilize the camera feed
        ret, frame = cap.read()
        if ret:
            cap.release()
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            cap.release()
            raise RuntimeError("Failed to capture image from the camera")

    def _detect_context_switch(self):
        """Detect if a context switch has occurred by comparing new image hash with the last."""
        try:
            new_image = self._capture_image()
            new_image_hash = imagehash.phash(new_image)

            if len(self.hash_history) > 0:
                hamming_distance = self.hash_history[-1] - new_image_hash
                print(f"Hamming distance: {hamming_distance}")

                previous_hamming_distance = self.hamming_history[-1] if self.hamming_history else 0
                self.hamming_delta.append(hamming_distance - previous_hamming_distance)
                self.hamming_history.append(hamming_distance)
            else:
                self.hamming_delta.append(0)
                self.hamming_history.append(0)
            
            self.hash_history.append(new_image_hash)

            if len(self.hash_history) == self.hash_history.maxlen:
                if self._is_stable_context(hamming_distance):
                    print("Stable context detected. Creating new image mapping.")
                    self._set_image_context(new_image, new_image_hash)
                else:
                    print("Context unstable. Waiting for further confirmation.")

        except Exception as e:
            print(f"Error in context detection: {e}")

    def _is_stable_context(self, current_hamming_distance):
        """Check if the context is stable based on hamming distance and its rate of change."""
        # Ensure enough history is available for evaluation
        if len(self.hamming_history) < self.hamming_history.maxlen:
            return False

        # Hamming distance stability check
        stable_deltas = all(abs(delta) < self.stable_threshold for delta in self.hamming_delta)

        # Ensure the current hamming distance is not too high (dynamic event like page turn or hand movement)
        if current_hamming_distance > self.max_hamming_distance:
            print("Detected a large change. Likely a dynamic event, resetting context evaluation.")
            self.reset_context()
            return False

        return stable_deltas

    def reset_context(self):
        """Reset the context evaluation to avoid transient events being captured as key images."""
        self.hamming_history.clear()
        self.hamming_delta.clear()
        self.hash_history.clear()
        print("Context evaluation reset.")

    def run(self):
        """Start detecting context switches in a background thread."""
        self.is_running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        """Continuously detect context switches at the specified refresh rate."""
        while self.is_running:
            self._detect_context_switch()
            time.sleep(self.refresh_rate)

    def stop(self):
        """Stop the context detection."""
        self.is_running = False
        if self._thread is not None:
            self._thread.join()
