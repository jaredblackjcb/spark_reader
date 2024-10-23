from PIL import Image
import cv2
import imagehash
import uuid
import os
import time
from imagehash import phash, ImageHash
import numpy as np
from typing import Union

def capture_image() -> Image.Image:
    cap = cv2.VideoCapture(0)
    time.sleep(0.1)
    ret, frame = cap.read()
    if ret:
        cap.release()
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    else:
        cap.release()
        raise RuntimeError("Failed to capture image from the camera")

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

def open_image(image_path: str) -> Image.Image:
    return Image.open(image_path)

def hash_image(image: Union[str, Image.Image]) -> ImageHash:
    if isinstance(image, str):
        with Image.open(image) as img:
            return phash(img)
    elif isinstance(image, Image.Image):
        return phash(image)
    else:
        raise ValueError("Input must be either a file path or a PIL Image object")

def extract_orb_features(image_path: str) -> np.ndarray:
    img: np.ndarray = _read_grayscale_image(image_path)
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(img, None)
    return descriptors

def extract_sift_features(image_path: str) -> np.ndarray:
    img: np.ndarray = _read_grayscale_image(image_path)
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(img, None)
    return descriptors

def _read_grayscale_image(image_path: str) -> np.ndarray:
    return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
