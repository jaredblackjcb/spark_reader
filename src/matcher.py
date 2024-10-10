import pickle
import cv2

def match_fingerprint(current_fingerprint, threshold=10):
    # Load stored fingerprints and associated audio clips
    with open('fingerprints.pkl', 'rb') as f:
        stored_fingerprints = pickle.load(f)
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    for stored_fingerprint, audio_file in stored_fingerprints:
        matches = bf.match(current_fingerprint, stored_fingerprint)
        print(f"{len(matches)} matches found")
        if len(matches) > threshold:
            return audio_file
    
    return None