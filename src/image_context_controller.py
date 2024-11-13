import threading
import time
from PIL import Image
from collections import deque
from typing import Optional, Callable, Deque
from src.image_mapping import ImageMapping, ImageMappingDB
from enum import Enum
from src.image_utils import ImageUtils
from imagehash import ImageHash

class ContextState(Enum):
    SEARCHING_STABLE = 1
    STABLE_FOUND = 2
    WAITING_PAGE_TURN = 3

class LEDColor(Enum):
    YELLOW = 1
    GREEN = 2

class ImageContextController:
    def __init__(self, refresh_rate: float = 0.3, history_size: int = 4, stable_threshold: int = 10, 
                 page_turn_threshold: int = 20, stabilization_count: int = 5, 
                 on_stable_context: Optional[Callable[[ImageMapping], None]] = None, 
                 led_indicator: Optional[Callable[[LEDColor], None]] = None):
        self.current_image_mapping: Optional[ImageMapping] = None
        self.last_key_image_hash: Optional[ImageHash] = None
        self.hamming_history: Deque[int] = deque(maxlen=history_size)
        self.hash_history: Deque[ImageHash] = deque(maxlen=history_size)
        self.refresh_rate: float = refresh_rate
        self.stable_threshold: int = stable_threshold
        self.page_turn_threshold: int = page_turn_threshold
        self.stabilization_count: int = stabilization_count
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self.on_stable_context: Optional[Callable[[ImageMapping], None]] = on_stable_context
        self.led_indicator: Optional[Callable[[LEDColor], None]] = led_indicator
        self.state: ContextState = ContextState.SEARCHING_STABLE
        self.stable_count: int = 0
        self.db: Optional[ImageMappingDB] = None
        self.image_utils = ImageUtils()

    def _set_image_context(self, new_image: Image.Image, new_image_hash: ImageHash) -> ImageMapping:
        image_path: str = self.image_utils.save_image(new_image, temp=True)
        image_mapping: ImageMapping = ImageMapping(image_path=image_path, image_hash=new_image_hash)
        self.current_image_mapping = image_mapping
        self.last_key_image_hash = new_image_hash
        print(f"New page detected. Image mapping created: {image_mapping.image_hash}")
        return image_mapping

    def _detect_context_switch(self) -> None:
        try:
            new_image: Image.Image = self.image_utils.capture_image()
            new_image_hash: ImageHash = ImageUtils.hash_image(new_image)

            if len(self.hash_history) > 0:
                hamming_distance: int = new_image_hash - self.hash_history[-1]
                print(f"Hamming distance from last image: {hamming_distance}")
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
            import traceback
            traceback.print_exc()

    def _handle_searching_stable(self) -> None:
        self._set_led(LEDColor.YELLOW)
        if self._is_stable_context():
            self.state = ContextState.STABLE_FOUND
            print("Stable context found. Ready to set key image.")

    def _handle_stable_found(self, new_image: Image.Image, new_image_hash: ImageHash) -> None:
        if (new_image_hash - self.hash_history[-1]) < self.stable_threshold:
            image_mapping: ImageMapping = self._set_image_context(new_image, new_image_hash)
            self.state = ContextState.WAITING_PAGE_TURN
            self._set_led(LEDColor.GREEN)
            if self.on_stable_context:
                self.on_stable_context(image_mapping)
        else:
            self.state = ContextState.SEARCHING_STABLE

    def _handle_waiting_page_turn(self, new_image: Image.Image, new_image_hash: ImageHash) -> None:
        if self.last_key_image_hash is not None:
            hamming_distance: int = new_image_hash - self.last_key_image_hash
            print(f"Hamming distance from last key image: {hamming_distance}")
            if hamming_distance > self.page_turn_threshold:
                print("Page turn detected. Searching for new stable context.")
                self.state = ContextState.SEARCHING_STABLE
                self._set_led(LEDColor.YELLOW)
                self.stable_count = 0

    def _is_stable_context(self) -> bool:
        if len(self.hamming_history) < self.hamming_history.maxlen:
            return False
        
        rates_of_change: list[int] = [abs(self.hamming_history[i] - self.hamming_history[i-1]) 
                                      for i in range(1, len(self.hamming_history))]
        
        return all(rate < self.stable_threshold for rate in rates_of_change)

    def _set_led(self, color: LEDColor) -> None:
        if self.led_indicator:
            self.led_indicator(color)

    def run(self) -> None:
        """Start the context controller and initialize camera."""
        self.is_running = True
        self.image_utils.init_camera()
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self) -> None:
        self.db = ImageMappingDB()
        while self.is_running:
            self._detect_context_switch()
            time.sleep(self.refresh_rate)
        self.db.close()

    def stop(self) -> None:
        """Stop the context controller and release camera resources."""
        self.is_running = False
        if self._thread is not None:
            self._thread.join()
        self.image_utils.stop_camera()
