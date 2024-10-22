import sqlite3
import os
from imagehash import ImageHash, hex_to_hash
from threading import local

class ThreadLocalDB(local):
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

class ImageMapping:
    def __init__(self, image_path, image_hash):
        self.book_id = None
        self.image_path = image_path
        self.audio_path = None
        self.image_hash = image_hash
        self.sift_features = None
        self.orb_features = None

class ImageMappingDB:
    def __init__(self, db_path='data/image_mappings.db'):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.db_path = db_path
        self.local = ThreadLocalDB(db_path)
        self.create_table()

    @property
    def conn(self):
        return self.local.conn

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                image_path TEXT,
                audio_path TEXT,
                image_hash TEXT,
                sift_features BLOB,
                orb_features BLOB
            )
        ''')
        self.conn.commit()

    def add_mapping(self, book_id, image_path, audio_path, image_hash, sift_features, orb_features):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO image_mappings (book_id, image_path, audio_path, image_hash, sift_features, orb_features)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (book_id, image_path, audio_path, str(image_hash), sqlite3.Binary(sift_features.tobytes()), sqlite3.Binary(orb_features.tobytes())))
        self.conn.commit()

    def get_book_mappings(self, book_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE book_id = ?', (book_id,))
        # return data as a list of ImageMapping objects
        return [ImageMapping(*row) for row in cursor.fetchall()]
    
    # def get_book_mappings_by_hash(self, book_id, image_hash, threshold=5):
    #     cursor = self.conn.cursor()
    #     cursor.execute('SELECT * FROM image_mappings WHERE book_id = ?', (book_id,))
    #     mappings = cursor.fetchall()
        
    #     matches = []
    #     for mapping in mappings:
    #         stored_hash = hex_to_hash(mapping[4])  # Convert stored hash string back to ImageHash
    #         if image_hash - stored_hash <= threshold:
    #             matches.append(mapping)
        
    #     return matches

    # def hamming_distance(self, hash1, hash2):
    #     return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
    
    # def get_book_mappings_by_sift_features(self, book_id, query_features, threshold=0.7):
    #     cursor = self.conn.cursor()
    #     cursor.execute('SELECT * FROM image_mappings WHERE book_id = ? AND sift_features = ?', (book_id, sqlite3.Binary(query_features.tobytes())))
    #     return cursor.fetchall()
    
    # def get_book_mappings_by_orb_features(self, book_id, query_features, threshold=0.7):
    #     cursor = self.conn.cursor()
    #     cursor.execute('SELECT * FROM image_mappings WHERE book_id = ? AND orb_features = ?', (book_id, sqlite3.Binary(query_features.tobytes())))
    #     return cursor.fetchall()

    def get_mapping_by_hash(self, image_hash, threshold=5):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings')
        mappings = cursor.fetchall()
        
        best_match = None
        min_distance = float('inf')
        
        for mapping in mappings:
            # Convert stored hash string back to ImageHash
            stored_hash = hex_to_hash(mapping[4])  # Ensure proper conversion to ImageHash
            distance = image_hash - stored_hash
            
            if distance < min_distance and distance <= threshold:
                min_distance = distance
                best_match = mapping
        
        return best_match

    def get_next_book_id(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(book_id) FROM image_mappings')
        result = cursor.fetchone()
        return result[0] + 1 if result[0] is not None else 1

    def close(self):
        self.conn.close()
