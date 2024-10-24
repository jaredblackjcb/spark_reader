from src.image_context_controller import ImageContextController
from src.matcher import ImageMatcher
from src.audio_utils import play_audio
from src.image_mapping import ImageMappingDB, ImageMapping
import time
from typing import Optional

class Narrator:
    def __init__(self, db_path: str = 'data/image_mappings.db'):
        self.db_path: str = db_path
        self.image_matcher: Optional[ImageMatcher] = None
        self.image_context: ImageContextController = ImageContextController(on_stable_context=self._handle_stable_context)
        self.current_audio: Optional[str] = None
        self.db: Optional[ImageMappingDB] = None

    def narrate(self) -> None:
        self.db = ImageMappingDB(self.db_path)
        self.image_matcher = ImageMatcher(self.db)
        self.image_context.run()

    def stop(self) -> None:
        self.image_context.stop()
        if hasattr(self, 'db'):
            self.db.close()

    def _handle_stable_context(self, image_mapping: ImageMapping) -> None:
        match: Optional[ImageMapping] = self.image_matcher.match_image(image_mapping.image_path)
        if match:
            audio_path: str = match.audio_path
            if audio_path != self.current_audio:
                self.current_audio = audio_path
                self._play_audio(audio_path)
        else:
            print("No matching audio found for the current image.")

    def _play_audio(self, audio_path: str) -> None:
        try:
            play_audio(audio_path)
        except Exception as e:
            print(f"Error playing audio: {e}")
