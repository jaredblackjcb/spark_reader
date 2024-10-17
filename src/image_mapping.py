import sqlite3
import cv2
import numpy as np

class ImageMapping:
    def __init__(self, image_path, image_hash):
        self.book_id = None
        self.image_path = image_path
        self.audio_path = None
        self.image_hash = image_hash
        self.sift_features = None

class ImageMappingDB:
    def __init__(self, db_path='image_mappings.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                image_path TEXT,
                audio_path TEXT,
                image_hash TEXT,
                sift_features BLOB
            )
        ''')
        self.conn.commit()

    def add_mapping(self, book_id, image_path, audio_path, image_hash, sift_features):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO image_mappings (book_id, image_path, audio_path, image_hash, sift_features)
            VALUES (?, ?, ?, ?, ?)
        ''', (book_id, image_path, audio_path, image_hash, sqlite3.Binary(sift_features.tobytes())))
        self.conn.commit()

    def get_book_mappings(self, book_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE book_id = ?', (book_id,))
        return cursor.fetchall()
    
    def get_book_mappings_by_hash(self, book_id, image_hash, threshold=20):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE book_id = ?', (book_id,))
        mappings = cursor.fetchall()
        
        matches = []
        for mapping in mappings:
            stored_hash = mapping[4]  # Assuming image_hash is at index 4
            if self.hamming_distance(image_hash, stored_hash) <= threshold:
                matches.append(mapping)
        
        return matches

    def hamming_distance(self, hash1, hash2):
        return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
    
    def get_book_mappings_by_features(self, book_id, query_features, threshold=0.7):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE book_id = ? AND sift_features = ?', (book_id, sqlite3.Binary(query_features.tobytes())))
        return cursor.fetchall()

    def get_mapping_by_hash(self, image_hash):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE image_hash = ?', (image_hash,))
        return cursor.fetchone()

    def get_mapping_by_features(self, query_features, threshold=0.7):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings')
        mappings = cursor.fetchall()

        best_match = None
        best_match_count = 0

        for mapping in mappings:
            db_features = np.frombuffer(mapping[5], dtype=np.float32).reshape(-1, 128)
            
            # FLANN matcher
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(query_features, db_features, k=2)

            # Apply ratio test
            good_matches = [m for m, n in matches if m.distance < threshold * n.distance]

            if len(good_matches) > best_match_count:
                best_match_count = len(good_matches)
                best_match = mapping

        return best_match

    def close(self):
        self.conn.close()
