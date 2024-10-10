import cv2
import pickle

def generate_fingerprint(image):
    # Convert the image to grayscale
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Initialize ORB detector
    orb = cv2.ORB_create()
    
    # Detect keypoints and compute descriptors
    keypoints, descriptors = orb.detectAndCompute(grayscale_image, None)
    return descriptors

# Create an image fingerprint
def store_fingerprint(image, audio_file_name):
    # Extract features from the image
    descriptors = generate_fingerprint(image)

    # Load existing fingerprints
    try:
        with open('fingerprints.pkl', 'rb') as f:
            fingerprints = pickle.load(f)
    except FileNotFoundError:
        fingerprints = []

    # Add the new fingerprint
    fingerprints.append((descriptors, audio_file_name))

    # Store the features and audio file path
    with open('fingerprints.pkl', 'wb') as f:
        pickle.dump(fingerprints, f)

