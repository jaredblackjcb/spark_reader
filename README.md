# Spark Reader

This project uses image recognition to detect which page of the book a person is looking at. It then plays the corresponding audio clip.

## Tech notes



### Narrator
Image mappings are stored in a sqlite DB. 
```
image_mappings (image_id, book_id, fingerprint, extracted_text, perceptual_hash, audio_file)
```
When in narration mode, the ImageContextController will run a background thread to detect the current page and store current context image.
The Narrator class will hold the book_id context. To find an audio file, it will retrieve the hash, pause the ImageContextController change detection thread, then perform an image search. Image mappings should be indexed by book_id to facilitate fast lookup of pages in the current book context. Narrator will then use the methods in matcher.py to filter down the results. Start with a hash match on images with the same book_id as the current context. If one image is found, play the file for that image. If multiple images are found, use the matcher method that compares features using SIFT to identify the most likely match and play the associated audio clip.

After audio clip finishes, a bell noise will tell the child to turn the page. The narrator class should hold a reference to the most recently narrated page to avoid playing the same page in a loop.

After all audio playback is complete or if no pages were found, resume the ImageContextController thread.


### Recording
Light will turn green when it has acquired page context, at which point the recording can start as soon as the person begins talking. The audio clip should be lightly trimmed and processed to remove noise and any whitespace at the beginning or end of the clip where no one is talking. The audio clip will be saved to the audio directory and an image mapping will be created and saved to the database that includes the image hash, a SIFT fingerprint, book_id of the current book being recorded, and the path to the associated audio file. Image recognition algorithm should run about once per second to detect page turns in record mode.

### Testing
Set to record mode, save images while turning pages and make sure all saved images are good state images.