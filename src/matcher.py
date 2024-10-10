import pickle
import cv2

def match_fingerprint(current_fingerprint, threshold=120):
    # Load stored fingerprints and associated audio clips
    with open('fingerprints.pkl', 'rb') as f:
        stored_fingerprints = pickle.load(f)
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    max_matches = 0
    playback_file = None
    for stored_fingerprint, audio_file in stored_fingerprints:
        matches = bf.match(current_fingerprint, stored_fingerprint)
        if len(matches) > max_matches:
            max_matches = len(matches)
            playback_file = audio_file
        print(f"{len(matches)} matches found")
    if max_matches > threshold:
        return playback_file
    
    return None