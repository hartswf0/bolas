"""The four stills the brief asks for, from the scene frames (1280x720 JPEG)."""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
os.makedirs(os.path.join(FOLDER, 'stills'), exist_ok=True)
for t in ('03.6', '09.0', '19.0', '28.0'):
    f = int(round(float(t) * 24))
    Image.open(os.path.join(HERE, 'cache', 'frames', 's%03d.jpg' % f)).save(os.path.join(FOLDER, 'stills', 'still_%ss.jpg' % t), quality=90)
