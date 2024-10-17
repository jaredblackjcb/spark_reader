import pickle
import cv2

def match_hash(image_hash, threshold=20, book_id=None):
    """ Uses perceptual hash to quickly find potential matching images within
        a given hamming distance threshold"""
    pass

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

def match_image(hash, fingerprint):
    matches = match_hash(hash) # modify to return type ImageMapping
    if len(matches) > 0:
        # Return highest probability match if there are multiple hash matches that meet the threshold
        matches = [match_fingerprint(fingerprint, match.fingerprint) for match in matches]
    return matches if len(matches) == 1 else None