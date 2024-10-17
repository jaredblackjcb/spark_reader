from src.image_context_controller import ImageContextController

class Recorder:
    def __init__(self):
        self.book_context = None # holds id of the current book
        self.image_context = ImageContextController(on_stable_context=self.on_stable_context_detected)
    
    def on_stable_context_detected(self):
        # pause thread execution on image context controller and start a recording using the current image context
        self.image_context.stop()
        audio_path = self.record_audio()
        # need a current image file to create SIFT feature mapping

        # save new mapping to DB 
        self.save_mapping(self.book_context, audio_path, self.image_context.current_key_image_hash)

        # resume page detection
        self.image_context.previous_page_hash = self.image_context.current_key_image_hash 
        self.image_context.reset_context()
        self.image_context.run()

    def record(self):
        self.image_context.run()
        # listen to image_context for a stable context