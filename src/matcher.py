import cv2
import numpy as np
from typing import Optional, List, Tuple
from src.image_mapping import ImageMappingDB, ImageMapping
from src.image_utils import ImageUtils
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

    def _match_orb(self, image_mappings: List[ImageMapping], orb_features: np.ndarray, min_matches: int = 80, max_distance: int = 50) -> ImageMapping:
        # List to store tuples of (mapping, number of good matches)
        match_counts: List[Tuple[ImageMapping, int]] = []

        for mapping in image_mappings:
            stored_features: np.ndarray = np.frombuffer(mapping.orb_features, dtype=np.uint8).reshape(-1, 32)
            
            bf: cv2.BFMatcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            feature_matches: List[cv2.DMatch] = bf.match(orb_features, stored_features)
            
            good_matches: List[cv2.DMatch] = [m for m in feature_matches if m.distance < max_distance]
            print(f"Good matches: {len(good_matches)}. Min matches: {min_matches}")
            if len(good_matches) > min_matches:
                match_counts.append((mapping, len(good_matches)))

        # Sort the matches by the number of good matches in descending order
        match_counts.sort(key=lambda x: x[1], reverse=True)

        # Return the mapping with the most good matches over the minimum threshold
        if match_counts:
            return match_counts[0][0]
        return None


    def _set_current_book_context(self, book_id: int) -> None:
        self.current_book_id = book_id
        self.current_book_mappings = self.db.get_book_mappings(self.current_book_id)
        print(f"New book found: {self.current_book_id}")

    def match_image(self, image_path: str) -> Optional[ImageMapping]:
        # Find the book id using hash to determine most likely book.
        image_hash: ImageHash = ImageUtils.hash_image(image_path)
        best_match: Optional[ImageMapping] = None

        matches: List[ImageMapping] = self._match_hash(image_hash)
        if len(matches) > 0:
            # Try matching orb features to make sure it is a match
            best_match = self._match_orb(matches, ImageUtils.extract_orb_features(image_path))
            if not best_match:
                print("None of the hash matches met the minimum orb match threshold.")
        # If a match is found and the current book mappings are not set, set the current book mappings
        if best_match and not self.current_book_mappings:
            self._set_current_book_context(best_match.book_id)
        return best_match