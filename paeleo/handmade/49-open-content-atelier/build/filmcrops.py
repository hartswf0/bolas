"""Critic aid: full-res crops from the FINAL film.mp4 around the measured dog. Usage: filmcrops.py out.jpg t1 t2 ... (scene seconds)"""
import sys, os, json, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
tr = json.load(open(os.path.join(HERE, '..', 'trace.json')))['frames']
out, ts = sys.argv[1], [float(a) for a in sys.argv[2:]]
tiles = []
for t in ts:
    i = round(t * 24); n = 72 + i; f = os.path.join(HERE, 'cache', f'fc_{n}.jpg')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', os.path.join(HERE, '..', 'film.mp4'), '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', '-q:v', '2', f], check=True)
    cx, cy = tr[i]['x_screen'], tr[i]['y_screen']
    im = Image.open(f).crop((int(cx - 190), int(cy - 120), int(cx + 190), int(cy + 70))); os.remove(f)
    tiles.append((t, im.resize((570, 285))))
c = 3; sh = Image.new('RGB', (c * 570, ((len(tiles) + c - 1) // c) * 301), 'white'); d = ImageDraw.Draw(sh)
for k, (t, im) in enumerate(tiles):
    x, y = (k % c) * 570, (k // c) * 301; sh.paste(im, (x, y + 16)); d.text((x + 4, y + 2), f'film frame, scene t={t:.3f}', fill='black')
sh.save(out, quality=88)
