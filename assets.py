import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
VIDEOS_DIR = os.path.join(ASSETS_DIR, 'videos')
AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

def ensure_dirs():
    for d in (ASSETS_DIR, IMAGES_DIR, VIDEOS_DIR, AUDIO_DIR, FONTS_DIR):
        os.makedirs(d, exist_ok=True)
