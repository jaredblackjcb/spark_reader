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
    def __init__(self, refresh_rate=1, history_size=1, stable_threshold=15):
        self.current_key_image_hash = None  # Stores the stable image hash for audio lookup
        self.hamming_history = deque(maxlen=history_size)  # Queue for last `history_size` seconds of hamming distances
        self.hamming_delta = deque(maxlen=history_size)  # Rate of change in hamming distances
        self.hash_history = deque(maxlen=history_size)  # Queue for last few image hashes
        self.refresh_rate = refresh_rate  # Seconds between image checks
        self.stable_threshold = stable_threshold  # Stability threshold for hamming distance
        self.history_size = history_size
        self.is_running = False
        self._thread = None

    def _set_image_context(self, image_hash):
        """Set the current image hash"""
        self.current_key_image_hash = image_hash
        print(f"Updated key image hash: {image_hash}")

    def _capture_image(self):
        """Capture an image from the camera and return the PIL image"""
        cap = cv2.VideoCapture(0)
        time.sleep(.5)  # Short delay to ensure the camera feed stabilizes
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
        """Detect if a context switch has occurred by comparing the new image hash with the current one"""
        try:
            new_image = self._capture_image()
            new_image_hash = imagehash.phash(new_image)

            # Compare the new hash with the current image hash
            if len(self.hash_history) > 0: # If there is at least one other image to compare to
                # Calculate hamming distance from last hash
                hamming_distance = self.hash_history[-1] - new_image_hash
                print(f"Hamming distance: {hamming_distance}")
                # Update history queues
                self.hamming_delta.append(self.hamming_history[-1] - hamming_distance)
                self.hamming_history.append(hamming_distance)
                print(f"Hamming distances between previous and current images: {self.hamming_history}")
                print(f"Hamming deltas: {self.hamming_delta}")
            else:
                # First entry has no delta or hamming distance
                self.hamming_delta.append(0) 
                self.hamming_history.append(0)
            # In all cases add the current hash to the history
            self.hash_history.append(new_image_hash)

            # Once the history has been fully populated, start checking for stable context
            if len(self.hash_history) == self.history_size:
                # Check if the hamming distance has been stable
                if self._is_stable_context():
                    print("Context stable, updating key image hash.")
                    self._set_image_context(new_image_hash)
                else:
                    print("Context unstable, waiting for further confirmation.")

        except Exception as e:
            print(f"Error in context detection: {e}")

    def _is_stable_context(self):
        """Check if the hamming distance has remained stable over time"""
        # Ensure we have enough history to evaluate
        if len(self.hamming_history) < self.hamming_history.maxlen:
            return False

        # Check if rate of change of hamming distances has stabilized
        print(f"All vals of {self.hamming_delta} should be under {self.stable_threshold} to set context")
        stable_deltas = all(abs(delta) < self.stable_threshold for delta in self.hamming_delta)  # Small change in distance

        return stable_deltas

    def run(self):
        """Start detecting context switches in a background thread"""
        self.is_running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        """Internal method to continuously run context detection at intervals"""
        while self.is_running:
            self._detect_context_switch()
            time.sleep(self.refresh_rate)

    def stop(self):
        """Stop detecting context switches"""
        self.is_running = False
        if self._thread is not None:
            self._thread.join()
