from src.image_context_controller import ImageContextController

class Narrator:
    def __init__(self):
        self.book_context = None # holds id of the current book
        self.image_context = ImageContextController()

    def narrate(self):
        self.image_context.run()
        # TODO: handle book narration