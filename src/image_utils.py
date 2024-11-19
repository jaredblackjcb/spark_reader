from PIL import Image
import cv2
import imagehash
import uuid
import os
from imagehash import phash, ImageHash
import numpy as np
from typing import Union, Optional
from src.camera_manager import CameraManager

class ImageUtils:
    """
    Handles image capture, processing, and feature extraction operations.
    Manages camera lifecycle and provides image manipulation utilities.
    """
    def __init__(self, camera_id: int = 0):
        self.camera_manager: Optional[CameraManager] = None
        self.camera_id = camera_id

    def init_camera(self) -> None:
        """Initialize the camera manager."""
        if self.camera_manager is None:
            self.camera_manager = CameraManager(self.camera_id)
            self.camera_manager.start()

    def stop_camera(self) -> None:
        """Stop the camera manager."""
        if self.camera_manager is not None:
            self.camera_manager.stop()
            self.camera_manager = None

    def capture_image(self) -> Image.Image:
        """
        Capture an image from the camera.
        
        Returns:
            Image.Image: The captured image
            
        Raises:
            RuntimeError: If camera is not initialized or capture fails
        """
        if self.camera_manager is None:
            raise RuntimeError("Camera not initialized. Call init_camera() first")
        return self.camera_manager.get_frame()

    @staticmethod
    def save_image(image: Image.Image, temp: bool = False) -> str:
        if temp:
            temp_dir: str = os.path.join("images", "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            image_path: str = os.path.join(temp_dir, "current_image.jpg")
        else:
            image_path: str = os.path.join("images", f"{uuid.uuid4()}.jpg")
        
        image.save(image_path)
        return image_path

    @staticmethod
    def open_image(image_path: str) -> Image.Image:
        return Image.open(image_path)

    @staticmethod
    def hash_image(image: Union[str, Image.Image]) -> ImageHash:
        if isinstance(image, str):
            with Image.open(image) as img:
                return phash(img)
        elif isinstance(image, Image.Image):
            return phash(image)
        else:
            raise ValueError("Input must be either a file path or a PIL Image object")

    @staticmethod
    def extract_orb_features(image_path: str) -> np.ndarray:
        img: np.ndarray = ImageUtils._read_grayscale_image(image_path)
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(img, None)
        return descriptors

    @staticmethod
    def _read_grayscale_image(image_path: str) -> np.ndarray:
        return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
