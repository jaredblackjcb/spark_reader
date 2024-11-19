# Spark Reader: Computer Vision Children's Book Narrator for Raspberry Pi

Spark reader uses image recognition to detect the page context in any children's book. Parents and grandparents can make a recording, and the audio clips will be mapped to the associated image and saved to the device. When a child wants to listen, they simply clip the reader onto any previously recorded book and the audio begins to play. It is always aware of the page context, so the narration can go at a child-led pace.

## Installation and Setup
### Equipment
- Raspberry Pi 4B - 4GB edition
- Raspberry Pi camera module
- Respeaker 2-mic array pi hat V1.0
- small speaker

### Raspberry Pi Setup
Install Bullseye headless OS using Raspberry Pi imager and insert the micro SD into the pi.
SSH into the pi and run:
```
sudo apt-get update
sudo apt-get install git
sudo apt-get install python3-venv
```
Install respeaker audio hat drivers using the hintak fork: https://github.com/HinTak/seeed-voicecard/tree/v6.1

Make sure to install the appropriate branch for your kernel version.

Clone the spark_reader project and create a virtual environment:
```
git clone https://github.com/jaredblackjcb/spark_reader.git
python3 -m venv --system-site-packages <env name> # system-site-packages brings in picamera2 module
source <env name>/bin/activate
```

## Install OS dependencies for Python Libraries
Install the following libraries. If you get an error message saying ‘E: Unable to locate package <package_name>’, it is likely that a different version exists for the OS version you are using.
Go to  Debian Webmaster, webmaster@debian.org Debian -- Debian Packages Search and search for the package name without the version.
![image.png](https://prod-files-secure.s3.us-west-2.amazonaws.com/4e43b154-c3d0-49f9-9f21-8f8727c1ba7b/d6c588e6-76f2-44d6-ae8a-c5f07765825e/image.png)

Install numpy dependencies:

```
sudo apt-get install libopenblas0-pthread libgfortran5
```

Install opencv-python-headless dependencies:

```
sudo apt-get install libjbig0 libxcb-render0 libtiff5 libwebp6 libsnappy1v5 libopus0 libpango-1.0-0 libdrm2 libspeex1 libva2 libfontconfig1 libharfbuzz0b libgraphite2-3 libva-drm2 libopenjp2-7 libvorbisenc2 libavformat58 libx264-160 libx265-192 libxrender1 libpangocairo-1.0-0 libthai0 libgfortran5 libpixman-1-0 libtheora0 libxfixes3 libswscale5 libxcb-shm0 libshine3 libgsm1 libswresample3 libssh-gcrypt-4 libwebpmux3 libavutil56 libdatrie1 libwavpack1 libvorbis0a libtwolame0 libva-x11-2 libgdk-pixbuf2.0-0 libsoxr0 libvpx6 libpangoft2-1.0-0 libgme0 libatlas3-base libvorbisfile3 libcroco3 libxvidcore4 libmpg123-0 libavcodec58 libaom0 libzvbi0 libmp3lame0 libcairo2 libbluray2 librsvg2-2 libchromaprint1 libogg0 libopenmpt0 libcodec2-0.9 libvdpau1
```

Install pillow dependencies:

```
sudo apt-get install libwebpmux3 libwebpdemux2 liblcms2-2 libopenjp2-7
```

Install pygame dependencies:

```
sudo apt-get install libvorbisfile3 libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libvorbisenc2 libfluidsynth2 libsdl2-ttf-2.0-0 libmp3lame0 libxss1 libwayland-egl1 libxcb-randr0 libsdl2-2.0-0 libpulse0 libxfixes3 libwayland-server0 libdecoration0 libmodplug1 libwayland-cursor0 libharfbuzz0b libxcursor1 libwayland-client0 libxi6 libxrandr2 libx11-xcb1 libxrender1 libsndfile1 libjack0 libxkbcommon0 libportmidi0 libmpg123-0 libopus0 libinstpatch-1.0-2 libasyncns0 libgbm1 libgraphite2-3 libopusfile0
```

Install scipy dependencies:

```
sudo apt-get install libopenblas0-pthread libgfortran5
```

Install sounddevice dependencies:
```
sudo apt-get install libportaudio
```

Install requirements.txt:
```
python3 -m pip install -U pip wheel # use wheel where available
pip3 install -r requirements.txt
```
You should now be able to run the project.
```
python3 main.py
```


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
