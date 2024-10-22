from PIL import Image
import cv2
import imagehash
import uuid
import os
import time
from imagehash import phash


def capture_image():
    cap = cv2.VideoCapture(0)
    time.sleep(0.1)
    ret, frame = cap.read()
    if ret:
        cap.release()
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    else:
        cap.release()
        raise RuntimeError("Failed to capture image from the camera")

def save_image(image, temp=False):
    if temp:
        temp_dir = os.path.join("images", "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        image_path = os.path.join(temp_dir, "current_image.jpg")
    else:
        image_path = os.path.join("images", f"{uuid.uuid4()}.jpg")
    
    image.save(image_path)
    return image_path

def open_image(image_path):
    return Image.open(image_path)

def hash_image(image):
    if isinstance(image, str):
        # If image is a file path
        with Image.open(image) as img:
            return phash(img)
    elif isinstance(image, Image.Image):
        # If image is already a PIL Image object
        return phash(image)
    else:
        raise ValueError("Input must be either a file path or a PIL Image object")

def extract_orb_features(image_path):
    # Read the image in grayscale
    img = _read_grayscale_image(image_path)
    # Initialize ORB detector
    orb = cv2.ORB_create()
    # Detect keypoints and compute descriptors
    keypoints, descriptors = orb.detectAndCompute(img, None)
    return descriptors

def extract_sift_features(image_path):
    # Read the image in grayscale
    img = _read_grayscale_image(image_path)
    # Initialize SIFT detector
    sift = cv2.SIFT_create()
    # Detect keypoints and compute descriptors
    keypoints, descriptors = sift.detectAndCompute(img, None)
    return descriptors

def _read_grayscale_image(image_path):
    return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
