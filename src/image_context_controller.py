import threading
import time
import imagehash
from PIL import Image
import cv2
from collections import deque

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
    def __init__(self, refresh_rate=0.4, history_size=2, stable_threshold=10, max_hamming_distance=15):
        self.current_key_image_hash = None  # Stores the stable image hash for audio lookup
        self.hamming_history = deque(maxlen=history_size)  # Queue for last few seconds of hamming distances
        self.hamming_delta = deque(maxlen=history_size)  # Queue for rate of change of hamming distances
        self.hash_history = deque(maxlen=history_size)  # Queue for last few image hashes
        self.refresh_rate = refresh_rate  # Time between checks in seconds
        self.stable_threshold = stable_threshold  # Stability threshold for hamming delta
        self.max_hamming_distance = max_hamming_distance  # Max allowable hamming distance before resetting
        self.is_running = False
        self._thread = None

    def _set_image_context(self, image_hash):
        """Set the current image hash as the key context for audio lookup."""
        self.current_key_image_hash = image_hash
        print(f"Key image hash updated: {image_hash}")

    def _capture_image(self):
        """Capture an image from the camera and return a PIL image."""
        cap = cv2.VideoCapture(0)
        time.sleep(0.1)  # Short delay to stabilize the camera feed
        ret, frame = cap.read()
        if ret:
            img_path = 'current_image.jpg'
            cv2.imwrite(img_path, frame)
            cap.release()
            return Image.open(img_path)
        else:
            cap.release()
            raise RuntimeError("Failed to capture image from the camera")

    def _detect_context_switch(self):
        """Detect if a context switch has occurred by comparing new image hash with the last."""
        try:
            new_image = self._capture_image()
            new_image_hash = imagehash.phash(new_image)

            # Compare the new hash with the last one in history
            if len(self.hash_history) > 0:
                hamming_distance = self.hash_history[-1] - new_image_hash
                print(f"Hamming distance: {hamming_distance}")

                # Update history queues
                previous_hamming_distance = self.hamming_history[-1] if self.hamming_history else 0
                self.hamming_delta.append(hamming_distance - previous_hamming_distance)
                self.hamming_history.append(hamming_distance)
            else:
                # First entry has no previous comparison
                self.hamming_delta.append(0)
                self.hamming_history.append(0)
            
            self.hash_history.append(new_image_hash)

            # If history is full, evaluate context stability
            if len(self.hash_history) == self.hash_history.maxlen:
                if self._is_stable_context(hamming_distance):
                    print("Stable context detected. Updating key image hash.")
                    self._set_image_context(new_image_hash)
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
            self._reset_context()
            return False

        return stable_deltas

    def _reset_context(self):
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