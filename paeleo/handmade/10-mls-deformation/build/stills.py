"""SCION-10 · the four stills from the rendered scene frames (1280x720 JPEG): 3.6 s, 9 s, 19 s, 28 s."""
import os
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, '..', 'stills'); os.makedirs(S, exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    i = int(round(t * 24))
    Image.open(os.path.join(H, 'cache', 'frames', f's_{i:04d}.jpg')).save(os.path.join(S, f'still_{t:04.1f}s.jpg'), quality=92)
    print('still', t, 'frame', i)
