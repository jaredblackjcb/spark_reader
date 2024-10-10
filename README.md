# Spark Reader

This project uses image recognition to detect which page of the book a person is looking at. It then plays the corresponding audio clip.

## Tech notes

Image recognition algorithm should run about once per second to detect page turns in read and record mode.
After audio clip finishes, a bell noise will tell the child to turn the page.
If it is still on the same page as the audio clip it just played, wait until a page turn is detected to avoid loops.

### Playback
Each book will have its own pickle file for speed of lookup.
There will be a pickle file that maps book covers the pickle file name that holds the page image audio mappings.
If no match is found within the pickle file for the currently open book, check for a match in the book cover master file
to see if the book has changed.

### Recording
Make sure to wait at least 1 second after detecting an image change before saving the image fingerprint to avoid capturing the image
when the page is half turned.
Person recording the book will have to make sure the page has been fully turned before they start talking.