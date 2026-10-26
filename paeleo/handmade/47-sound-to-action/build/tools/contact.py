"""python3 build/tools/contact.py OUT.jpg COLS SCALE f1 f2 ...  tile rendered stills from build/cache/frames with time labels"""
import sys, os
from PIL import Image, ImageDraw
out, cols, sc = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]); fr = [int(a) for a in sys.argv[4:]]
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache', 'frames')
CROP = tuple(int(v) for v in os.environ['CROP'].split(',')) if os.environ.get('CROP') else (0, 0, 1280, 720)
w, h = int((CROP[2] - CROP[0]) * sc), int((CROP[3] - CROP[1]) * sc); rows = (len(fr) + cols - 1) // cols
S = Image.new('RGB', (w * cols, h * rows)); d = ImageDraw.Draw(S)
for k, i in enumerate(fr):
    im = Image.open(os.path.join(D, f'f{i:03d}.jpg')).crop(CROP).resize((w, h)); x, y = (k % cols) * w, (k // cols) * h
    S.paste(im, (x, y)); d.rectangle([x, y, x + 70, y + 14], fill=(0, 0, 0)); d.text((x + 3, y + 2), f'{i} {i/24:.2f}s', fill=(255, 255, 0))
S.save(out, quality=88)
