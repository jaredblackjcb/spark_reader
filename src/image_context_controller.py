import threading
import time
import imagehash
from PIL import Image
import cv2
from collections import deque
import os
import uuid
from src.image_mapping import ImageMapping
from enum import Enum

class ContextState(Enum):
    SEARCHING_STABLE = 1
    STABLE_FOUND = 2
    WAITING_PAGE_TURN = 3

class LEDColor(Enum):
    YELLOW = 1
    GREEN = 2

class ImageContextController:
    def __init__(self, refresh_rate=0.3, history_size=3, stable_threshold=10, page_turn_threshold=20, 
                 stabilization_count=5, on_stable_context=None, led_indicator=None):
        self.current_image_mapping = None
        self.last_key_image_hash = None
        self.hamming_history = deque(maxlen=history_size)
        self.hash_history = deque(maxlen=history_size)
        self.refresh_rate = refresh_rate
        self.stable_threshold = stable_threshold
        self.page_turn_threshold = page_turn_threshold
        self.stabilization_count = stabilization_count
        self.is_running = False
        self._thread = None
        self.on_stable_context = on_stable_context
        self.led_indicator = led_indicator
        self.state = ContextState.SEARCHING_STABLE
        self.stable_count = 0

    def _set_image_context(self, new_image, new_image_hash):
        image_path = self._save_image(new_image)
        self.current_image_mapping = ImageMapping(image_path, str(new_image_hash))
        self.last_key_image_hash = new_image_hash
        print(f"New page detected. Image mapping created: {self.current_image_mapping.image_hash}")
        if self.on_stable_context:
            self.on_stable_context(self.current_image_mapping)

    def _save_image(self, image):
        filename = f"{uuid.uuid4()}.jpg"
        image_path = os.path.join("images", filename)
        image.save(image_path)
        return image_path

    def _capture_image(self):
        cap = cv2.VideoCapture(0)
        time.sleep(0.1)
        ret, frame = cap.read()
        if ret:
            cap.release()
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            cap.release()
            raise RuntimeError("Failed to capture image from the camera")

    def _detect_context_switch(self):
        try:
            new_image = self._capture_image()
            new_image_hash = imagehash.phash(new_image)

            if len(self.hash_history) > 0:
                hamming_distance = self.hash_history[-1] - new_image_hash
                print(f"Hamming distance from last image: {hamming_distance}")
                # print(f"Hamming history: {self.hamming_history}")
                self.hamming_history.append(hamming_distance)
            else:
                self.hamming_history.append(0)

            self.hash_history.append(new_image_hash)

            if self.state == ContextState.SEARCHING_STABLE:
                self._handle_searching_stable()
            elif self.state == ContextState.STABLE_FOUND:
                self._handle_stable_found(new_image, new_image_hash)
            elif self.state == ContextState.WAITING_PAGE_TURN:
                self._handle_waiting_page_turn(new_image, new_image_hash)

        except Exception as e:
            print(f"Error in context detection: {e}")

    def _handle_searching_stable(self):
        self._set_led(LEDColor.YELLOW)
        if self._is_stable_context():
            self.state = ContextState.STABLE_FOUND
            print("Stable context found. Ready to set key image.")

    def _handle_stable_found(self, new_image, new_image_hash):
        if abs(new_image_hash - self.hash_history[-1]) < self.stable_threshold:
            self._set_image_context(new_image, new_image_hash)
            self.state = ContextState.WAITING_PAGE_TURN
            self._set_led(LEDColor.GREEN)
        else:
            self.state = ContextState.SEARCHING_STABLE

    def _handle_waiting_page_turn(self, new_image, new_image_hash):
        if self.last_key_image_hash is not None:
            hamming_distance = self.last_key_image_hash - new_image_hash
            print(f"Hamming distance from last key image: {hamming_distance}")
            if hamming_distance > self.page_turn_threshold:
                print("Page turn detected. Searching for new stable context.")
                self.state = ContextState.SEARCHING_STABLE
                self._set_led(LEDColor.YELLOW)
                self.stable_count = 0

    def _is_stable_context(self):
        if len(self.hamming_history) < self.hamming_history.maxlen:
            return False
        
        # Calculate rate of change
        rates_of_change = [abs(self.hamming_history[i] - self.hamming_history[i-1]) 
                           for i in range(1, len(self.hamming_history))]
        
        # Check if all rates of change are below the stable threshold
        return all(rate < self.stable_threshold for rate in rates_of_change)

    def _set_led(self, color):
        if self.led_indicator:
            self.led_indicator(color)

    def run(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        while self.is_running:
            self._detect_context_switch()
            time.sleep(self.refresh_rate)

    def stop(self):
        self.is_running = False
        if self._thread is not None:
            self._thread.join()
