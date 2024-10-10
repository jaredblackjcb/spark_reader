import cv2
import uuid
import time

def capture_image():
    input("Press enter to capture image")
    # Capture the image from the camera and save it to a file
    cap = cv2.VideoCapture(0)
    time.sleep(1)
    ret, img = cap.read()
    cap.release()

    if not ret:
        raise Exception("Failed to capture image from webcam")

    image_path = f'images/{uuid.uuid4()}.jpg'
    cv2.imwrite(image_path, img)

    # Load the image and convert it to grayscale
    return img
    