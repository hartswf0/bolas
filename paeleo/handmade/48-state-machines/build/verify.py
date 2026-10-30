"""Look at the FINAL film: extract frames from film.mp4 around each choice and lay them out as crops around the dog
(positions from trace.json). python3 verify.py name t0 t1 step  ->  ../proof/film_<name>.jpg"""
import sys, os, json, subprocess
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(HERE)
tr = json.load(open(os.path.join(F, 'trace.json')))['frames']
name, t0, t1, st = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
tmp = os.path.join(HERE, 'cache', 'verify'); os.makedirs(tmp, exist_ok=True)
ims = []
t = t0
while t <= t1 + 1e-6:
    i = int(round(t * 24)); n = i + 72
    out = os.path.join(tmp, f'v{n:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(F, 'film.mp4'), '-vf', f'select=eq(n\\,{n})', '-vframes', '1', out], check=True)
    im = Image.open(out)
    r = tr[i]
    cx, cy = int(r['x_screen'] or 640), int(r['y_screen'] or 360)
    w, h = 440, 300
    c = im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
    ImageDraw.Draw(c).text((6, 6), f'{t:.2f}s', fill=(255, 255, 255))
    ims.append(c)
    t += st
cols = 3
W = Image.new('RGB', (cols * 440, ((len(ims) + cols - 1) // cols) * 300))
for k, c in enumerate(ims):
    W.paste(c, ((k % cols) * 440, (k // cols) * 300))
W.save(os.path.join(F, 'proof', f'film_{name}.jpg'), quality=88)
for fn in os.listdir(tmp):
    os.remove(os.path.join(tmp, fn))
