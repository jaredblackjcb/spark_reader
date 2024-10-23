from src.image_context_controller import ImageContextController
from src.matcher import ImageMatcher
from src.audio_utils import play_audio
from src.image_mapping import ImageMappingDB
import time

class Narrator:
    def __init__(self, db_path='data/image_mappings.db'):
        self.book_id = None  # holds id of the current book
        self.db_path = db_path
        self.image_matcher = None  # We'll initialize this in the thread
        self.image_context = ImageContextController(on_stable_context=self._handle_stable_context)
        self.current_audio = None

    def narrate(self):
        self.db = ImageMappingDB(self.db_path)  # Create a new database connection for this thread
        self.image_matcher = ImageMatcher(self.db)
        self.image_context.run()

    def stop(self):
        self.image_context.stop()
        if hasattr(self, 'db'):
            self.db.close()

    def _handle_stable_context(self, image_mapping):
        match = self.image_matcher.match_image(image_mapping.image_path, self.book_id)
        self.book_id = match.book_id if match else None
        if match:
            audio_path = match.audio_path
            if audio_path != self.current_audio:
                self.current_audio = audio_path
                self._play_audio(audio_path)
        else:
            print("No matching audio found for the current image.")

    def _play_audio(self, audio_path):
        try:
            play_audio(audio_path)
        except Exception as e:
            print(f"Error playing audio: {e}")
