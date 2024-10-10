import cv2
import uuid

from src.fingerprint import store_fingerprint, generate_fingerprint
from src.matcher import match_fingerprint
from src.audio import play_audio, record_audio
from src.camera import capture_image
def record():
    img = capture_image()
    
    # Record the audio from the microphone and save it to the audio file path
    audio_file_name = record_audio()

    # Generate a fingerprint for the current image and save it with the corresponding audio file
    store_fingerprint(img, audio_file_name)

def playback():
    # Capture the image from the camera and compare it with stored fingerprints
    img = capture_image()

    # Generate a fingerprint for the current image
    current_fingerprint = generate_fingerprint(img)
    
    # Match it with stored fingerprints
    matched_audio = match_fingerprint(current_fingerprint)
    
    # Play the associated audio if a match is found
    if matched_audio:
        play_audio(f'audio/{matched_audio}')
    else:
        print("No match found.")


if __name__ == "__main__":

    option = None
    while option != '3':
        print('''
          ################## Spark Reader ##################
          1. Record a page
          2. Narrate a previously recorded page
          3. Exit program
          ''')
        option = input("\nPlease select an option: ")
        match option:
            case '1':
                record()
            case '2':
                playback()
            case _:
                print("Please select a valid option 1, 2, or 3")