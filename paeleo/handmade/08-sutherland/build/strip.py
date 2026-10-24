"""Diagnostic: crops around the dog at given scene times -> one contact strip (not part of the film)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
import render as R
R.init()
ts = [float(a) for a in sys.argv[2:]]
tiles = []
for t in ts:
    n = R.TITLE_N + int(round(t * 24))
    _, b, meas, N = R.render_frame(n)
    im = Image.frombytes('RGB', (1280, 720), b)
    cx, cy = (meas['cx'], meas['cy']) if meas else (640, 400)
    box = (int(cx - 160), int(cy - 130), int(cx + 160), int(cy + 70))
    c = im.crop(box)
    ImageDraw.Draw(c).text((4, 4), 't=%.2f' % t, fill=(255, 255, 255))
    tiles.append(c)
cols = 4
rows = (len(tiles) + cols - 1) // cols
out = Image.new('RGB', (320 * cols, 200 * rows))
for k, c in enumerate(tiles):
    out.paste(c, ((k % cols) * 320, (k // cols) * 200))
out.save(sys.argv[1])
