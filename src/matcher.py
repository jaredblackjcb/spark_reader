import cv2
import numpy as np
from typing import Optional, List
from src.image_mapping import ImageMappingDB, ImageMapping
from src.image_utils import hash_image, extract_orb_features, extract_sift_features
from imagehash import ImageHash, hex_to_hash

class ImageMatcher:
    def __init__(self, db: ImageMappingDB) -> None:
        self.db: ImageMappingDB = db
        self.current_book_id: Optional[int] = None
        self.current_book_mappings: List[ImageMapping] = []

    def _match_hash(self, image_hash: ImageHash, threshold: int = 25) -> Optional[List[ImageMapping]]:
        matches: List[ImageMapping] = []
        # Search cached mappings first
        if self.current_book_mappings:
            for mapping in self.current_book_mappings:
                if hex_to_hash(mapping.image_hash) - image_hash <= threshold:
                    matches.append(mapping)
        # If no matches are found, search the database and clear current book mappings
        if not matches:
            matches = self.db.get_mappings_by_hash(image_hash)
            self.current_book_mappings = []
            self.current_book_id = None
        return matches

    def _match_orb(self, image_mappings: List[ImageMapping], orb_features: np.ndarray, threshold: int = 10) -> List[ImageMapping]:
        matches: List[ImageMapping] = []

        for mapping in image_mappings:
            stored_features: np.ndarray = np.frombuffer(mapping.orb_features, dtype=np.uint8).reshape(-1, 32)
            
            bf: cv2.BFMatcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            feature_matches: List[cv2.DMatch] = bf.match(orb_features, stored_features)
            
            good_matches: List[cv2.DMatch] = [m for m in feature_matches if m.distance < 50]
            
            if len(good_matches) > threshold:
                matches.append(mapping)

        return matches

    def _match_sift(self, image_mappings: List[ImageMapping], query_features: np.ndarray) -> Optional[ImageMapping]:
        """
        Compare the SIFT features from each mapping in image_mappings and return the best match.

        Args:
            image_mappings (List[ImageMapping]): List of image mappings to compare against.
            query_features (np.ndarray): SIFT features of the query image.

        Returns:
            Optional[ImageMapping]: The best matching image mapping or None if no good match is found.
        """
        best_match: Optional[ImageMapping] = None
        max_good_matches: int = 0

        for mapping in image_mappings:
            stored_features: np.ndarray = np.frombuffer(mapping.sift_features, dtype=np.float32).reshape(-1, 128)
            
            bf: cv2.BFMatcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            feature_matches: List[cv2.DMatch] = bf.match(query_features, stored_features)
            # TODO: Figure out why good_matches is always empty
            good_matches: List[cv2.DMatch] = [m for m in feature_matches if m.distance < 0.7 * min(m.distance for m in feature_matches)]
            
            if len(good_matches) > max_good_matches:
                max_good_matches = len(good_matches)
                best_match = mapping

        return best_match if max_good_matches > 10 else None
    
    def _set_current_book_context(self, book_id: int) -> None:
        self.current_book_id = book_id
        self.current_book_mappings = self.db.get_book_mappings(self.current_book_id)
        print(f"New book found: {self.current_book_id}")

    def match_image(self, image_path: str) -> Optional[ImageMapping]:
        # Find the book id using hash to determine most likely book.
        image_hash: ImageHash = hash_image(image_path)
        best_match: Optional[ImageMapping] = None

        matches: List[ImageMapping] = self._match_hash(image_hash)
        # If multiple page ImageMappings are found, try matching with sift and orb features.
        if len(matches) > 1:
            # Try matching orb features
            matches = self._match_orb(matches, extract_orb_features(image_path))
        elif len(matches) == 1:
            best_match = matches[0]
        if len(matches) > 1:
            # Find and return best match using sift features
            best_match = self._match_sift(matches, extract_sift_features(image_path))
        elif len(matches) == 1:
            best_match = matches[0]
        # If a match is found and the current book mappings are not set, set the current book mappings
        if best_match and not self.current_book_mappings:
            self._set_current_book_context(best_match.book_id)
        return best_match