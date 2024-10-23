import cv2
import numpy as np
from src.image_mapping import ImageMappingDB, ImageMapping
from src.image_utils import hash_image, extract_orb_features, extract_sift_features
from imagehash import ImageHash

class ImageMatcher:
    def __init__(self, db: ImageMappingDB):
        self.db = db
        self.current_book_id = None
        self.current_book_mappings: list[ImageMapping] = []

    def set_current_book(self, book_id):
        if self.current_book_id != book_id:
            self.current_book_id = book_id
            self.current_book_mappings = self.db.get_book_mappings(book_id)

    def match_image(self, image_path, book_id=None):
        if book_id is not None and book_id != self.current_book_id:
            self.set_current_book(book_id)

        image_hash = hash_image(image_path)
        orb_features = extract_orb_features(image_path)
        
        # Step 1: Try hash matching
        hash_match = self._match_hash(image_hash)
        if hash_match:
            if self.current_book_id is None:
                self.set_current_book(hash_match.book_id)
            return hash_match

        # Step 2: Try ORB feature matching
        orb_match = self._match_orb(orb_features)
        if orb_match:
            if self.current_book_id is None:
                self.set_current_book(orb_match.book_id)
            return orb_match

        # Step 3: Fall back to SIFT feature matching
        sift_features = extract_sift_features(image_path)
        sift_match = self._match_sift(sift_features)
        if sift_match:
            if self.current_book_id is None:
                self.set_current_book(sift_match.book_id)
            return sift_match

        # If no match found in current book, search entire database
        if self.current_book_id is not None:
            self.current_book_id = None
            self.current_book_mappings = []
            return self.match_image(image_path)

        return None

    def _match_hash(self, image_hash: ImageHash, threshold=25):
        if self.current_book_mappings:
            return next((mapping for mapping in self.current_book_mappings 
                         if ImageHash(mapping.image_hash) - image_hash <= threshold), None)
        return self.db.get_mapping_by_hash(image_hash, threshold)

    def _match_orb(self, query_features):
        best_match = None
        max_good_matches = 0

        for mapping in self.current_book_mappings:
            stored_features = np.frombuffer(mapping.orb_features, dtype=np.uint8).reshape(-1, 32)
            
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(query_features, stored_features)
            
            good_matches = [m for m in matches if m.distance < 50]
            
            if len(good_matches) > max_good_matches:
                max_good_matches = len(good_matches)
                best_match = mapping

        return best_match if max_good_matches > 10 else None

    def _match_sift(self, query_features):
        best_match = None
        max_good_matches = 0

        for mapping in self.current_book_mappings:
            stored_features = np.frombuffer(mapping.sift_features, dtype=np.float32).reshape(-1, 128)
            
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            matches = bf.match(query_features, stored_features)
            
            good_matches = [m for m in matches if m.distance < 0.7 * min(m.distance for m in matches)]
            
            if len(good_matches) > max_good_matches:
                max_good_matches = len(good_matches)
                best_match = mapping

        return best_match if max_good_matches > 10 else None
