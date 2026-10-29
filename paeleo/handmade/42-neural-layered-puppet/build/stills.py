"""SCION 42 · the four stills, straight from the rendered scene frames (1280x720 JPEG)."""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    i = int(round(t * 24))
    Image.open(os.path.join(HERE, 'cache', 'frames', 's_%04d.jpg' % i)).convert('RGB').save(
        os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % t), quality=90)
print('stills ok')
