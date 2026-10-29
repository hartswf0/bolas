"""The four stills (scene frames at 3.6, 9, 19, 28 s), 1280x720 JPEG."""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = os.path.join(ROOT, 'stills'); os.makedirs(out, exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    i = int(round(t * FPS))
    Image.open(os.path.join(CACHE, 'frames', 'f%04d.jpg' % i)).save(os.path.join(out, 'still_%04.1fs.jpg' % t), quality=90)
print(sorted(os.listdir(out)))
