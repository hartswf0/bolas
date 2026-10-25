"""Contact sheet of scene frames decoded from film.mp4 (what the viewer gets). usage: contact.py out.png t0 t1 step [crop x0,y0,x1,y1]"""
import subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'film.mp4')
out, t0, t1, step = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
crop = tuple(int(v) for v in sys.argv[5].split(',')) if len(sys.argv) > 5 else None
ts = np.arange(t0, t1 + 1e-6, step)
tiles = []
for t in ts:
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', '%.4f' % (t + 3.0 + 0.001), '-i', F, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    im = Image.frombytes('RGB', (1280, 720), raw)
    if crop: im = im.crop(crop)
    im.thumbnail((420, 420)); d = ImageDraw.Draw(im); d.rectangle([0, 0, 64, 14], fill=(0, 0, 0)); d.text((2, 1), '%.3f' % t, fill=(255, 255, 0))
    tiles.append(im)
cols = 4; w, h = tiles[0].size
sheet = Image.new('RGB', (cols * w, ((len(tiles) + cols - 1) // cols) * h))
for k, im in enumerate(tiles): sheet.paste(im, ((k % cols) * w, (k // cols) * h))
sheet.save(out); print(out, len(tiles))
