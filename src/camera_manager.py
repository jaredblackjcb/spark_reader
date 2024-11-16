from threading import Lock
import cv2
from PIL import Image
import time
from typing import Optional, Union, Tuple
import platform
import sys

# Check if running on Raspberry Pi
IS_RASPBERRY_PI = sys.platform == 'linux'

# Only import picamera2 on Raspberry Pi
if IS_RASPBERRY_PI:
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("Warning: picamera2 not found. Falling back to OpenCV.")
        IS_RASPBERRY_PI = False

class CameraManager:
    """
    Manages camera operations with on-demand frame capture.
    Keeps camera initialized but only captures when requested.
    Automatically uses PiCamera2 on Raspberry Pi and falls back to OpenCV on other platforms.
    
    Args:
        camera_id (int): Camera device ID (default: 0)
        resolution (tuple[int, int], optional): Desired camera resolution (width, height)
    """
    def __init__(self, camera_id: int = 0, resolution: Tuple[int, int] = (1920, 1080)):
        self.camera_id = camera_id
        self.resolution = resolution
        self.capture: Union[cv2.VideoCapture, Picamera2, None] = None
        self.lock = Lock()
        self.is_running = False
        self.using_picamera = IS_RASPBERRY_PI
        
    def start(self) -> None:
        """Initialize and configure the camera."""
        with self.lock:
            if self.using_picamera:
                self._start_picamera()
            else:
                self._start_opencv()
            
            self.is_running = True
            
    def _start_picamera(self) -> None:
        """Initialize and configure PiCamera2."""
        self.capture = Picamera2()
        # Configure camera with main preview configuration
        config = self.capture.create_still_configuration(
            main={"size": self.resolution, "format": "RGB888"}
        )
        self.capture.configure(config)
        self.capture.start()
        # Allow camera to warm up
        time.sleep(2)
        
    def _start_opencv(self) -> None:
        """Initialize and configure OpenCV camera."""
        self.capture = cv2.VideoCapture(self.camera_id)
        if not self.capture.isOpened():
            raise RuntimeError("Failed to initialize camera")
            
        # Configure camera
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        # Allow camera to initialize
        time.sleep(0.5)
            
    def get_frame(self) -> Image.Image:
        """
        Capture and return a single frame as a PIL Image.
        
        Returns:
            Image.Image: Captured frame as PIL Image in RGB format
            
        Raises:
            RuntimeError: If camera is not initialized or frame capture fails
        """
        with self.lock:
            if not self.is_running or self.capture is None:
                raise RuntimeError("Camera not initialized or stopped")
            
            if self.using_picamera:
                # PiCamera2 captures directly in RGB format
                frame = self.capture.capture_array()
                return Image.fromarray(frame)
            else:
                # OpenCV capture
                ret, frame = self.capture.read()
                if not ret:
                    raise RuntimeError("Failed to capture frame")
                # Convert from BGR to RGB
                return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
    def stop(self) -> None:
        """Stop and release camera resources."""
        with self.lock:
            self.is_running = False
            if self.capture is not None:
                if self.using_picamera:
                    self.capture.stop()
                else:
                    self.capture.release()
                self.capture = None