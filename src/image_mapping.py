import sqlite3
import os
from typing import Optional, List, Union
from imagehash import ImageHash, hex_to_hash
from threading import local
import numpy as np

class ThreadLocalDB(local):
    def __init__(self, db_path: str) -> None:
        self.conn: sqlite3.Connection = sqlite3.connect(db_path)

class ImageMapping:
    def __init__(self, 
                 id: Optional[int] = None, 
                 book_id: Optional[int] = None, 
                 image_path: Optional[str] = None, 
                 audio_path: Optional[str] = None, 
                 image_hash: Optional[Union[str, ImageHash]] = None, 
                 orb_features: Optional[np.ndarray] = None) -> None:
        self.id: Optional[int] = id
        self.book_id: Optional[int] = book_id
        self.image_path: Optional[str] = image_path
        self.audio_path: Optional[str] = audio_path
        self.image_hash: Optional[Union[str, ImageHash]] = image_hash
        self.orb_features: Optional[np.ndarray] = orb_features

class ImageMappingDB:
    def __init__(self, db_path: str = 'data/image_mappings.db') -> None:
        if not os.path.exists('data'):
            os.makedirs('data')
        self.db_path: str = db_path
        self.local: ThreadLocalDB = ThreadLocalDB(db_path)
        self.create_table()

    @property
    def conn(self) -> sqlite3.Connection:
        return self.local.conn

    def create_table(self) -> None:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                image_path TEXT,
                audio_path TEXT,
                image_hash TEXT,
                orb_features BLOB
            )
        ''')
        self.conn.commit()

    def add_mapping(self, book_id: int, image_path: str, audio_path: str, 
                    image_hash: ImageHash, orb_features: np.ndarray) -> None:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO image_mappings (book_id, image_path, audio_path, image_hash, orb_features)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (book_id, image_path, audio_path, str(image_hash), sqlite3.Binary(orb_features.tobytes())))
        self.conn.commit()

    def get_book_mappings(self, book_id: int) -> List[ImageMapping]:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings WHERE book_id = ?', (book_id,))
        return [ImageMapping(*row) for row in cursor.fetchall()]
    
    def get_mappings_by_hash(self, image_hash: ImageHash, threshold: int = 25) -> Optional[List[ImageMapping]]:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM image_mappings')
        mappings: List[tuple] = cursor.fetchall()
        
        matches: List[ImageMapping] = []
        
        for mapping in mappings:
            stored_hash: ImageHash = hex_to_hash(mapping[4])
            distance: int = image_hash - stored_hash
            
            if distance <= threshold:
                matches.append(ImageMapping(*mapping))
        
        return matches

    def get_next_book_id(self) -> int:
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(book_id) FROM image_mappings')
        result: Optional[tuple] = cursor.fetchone()
        return result[0] + 1 if result[0] is not None else 1

    def close(self) -> None:
        self.conn.close()
