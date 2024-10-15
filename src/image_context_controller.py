import threading
import time
import imagehash
from PIL import Image
import cv2

class ImageContextController:
    def __init__(self, refresh_rate=1):
        self.current_image_hash = None
        self.refresh_rate = refresh_rate  # seconds
        self.is_running = False
        self._thread = None

    def _set_context(self, image_hash):
        """Set the current image hash"""
        self.current_image_hash = image_hash

    def _capture_image(self):
        """Capture an image from the camera and return the PIL image"""
        cap = cv2.VideoCapture(0)
        time.sleep(.5)
        ret, frame = cap.read()
        if ret:
            img_path = 'current_image.jpg'
            cv2.imwrite(img_path, frame)
            cap.release()
            return Image.open(img_path)
        else:
            cap.release()
            raise RuntimeError("Failed to capture image from the camera")

    # Threshold is intentionally low in case image is captured while page is turning or a hand is covering part of the image.
    # I want it to send frequent context updates because the noise filtering will take place at the narrator class
    def _detect_context_switch(self, threshold=15):
        """Detect if a context switch has occurred by comparing the new image hash with the current one"""
        try:
            new_image = self._capture_image()
            new_image_hash = imagehash.phash(new_image)

            # Compare the new hash with the current image hash
            if self.current_image_hash:
                hamming_distance = self.current_image_hash - new_image_hash
                print(f"Hamming distance: {hamming_distance}")

                # If the Hamming distance exceeds the threshold, we consider it a context switch
                if hamming_distance > threshold:
                    print("Context switch detected!")
                    # Update the current image hash
                    self._set_context(new_image_hash)
                    print("Image context has been set")
            else:
                # If no current hash exists, just set the new hash
                self._set_context(new_image_hash)

        except Exception as e:
            print(f"Error in context detection: {e}")

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

