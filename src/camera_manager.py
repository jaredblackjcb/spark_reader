from threading import Lock
import cv2
from PIL import Image
from typing import Optional
import time

class CameraManager:
    """
    Manages camera operations with on-demand frame capture.
    Keeps camera initialized but only captures when requested.
    """
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.capture: Optional[cv2.VideoCapture] = None
        self.lock = Lock()
        self.is_running = False
        
    def start(self) -> None:
        """Initialize and configure the camera."""
        with self.lock:
            self.capture = cv2.VideoCapture(self.camera_id)
            time.sleep(2)
            if not self.capture.isOpened():
                raise RuntimeError("Failed to initialize camera")
            
            # Configure camera for faster captures
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.is_running = True
            
    def get_frame(self) -> Image.Image:
        """
        Capture and return a single frame as a PIL Image.
        """
        with self.lock:
            if not self.is_running or self.capture is None:
                raise RuntimeError("Camera not initialized or stopped")
            
            # Get frame directly without clearing buffer
            ret, frame = self.capture.read()
            if not ret:
                raise RuntimeError("Failed to capture frame")
                
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
    def stop(self) -> None:
        """Stop and release camera resources."""
        with self.lock:
            self.is_running = False
            if self.capture is not None:
                self.capture.release()
                self.capture = None 