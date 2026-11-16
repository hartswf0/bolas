"""Save a crop of a plate with a coordinate grid (plate pixel coords) for markup. usage: gridcrop.py plate x0 y0 x1 y1 scale step out"""
import sys
import numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
f, x0, y0, x1, y1, sc, step, out = sys.argv[1:]
x0, y0, x1, y1, step = map(int, (x0, y0, x1, y1, step)); sc = float(sc)
a = np.array(Image.open(f))
if a.dtype != np.uint8:
    a = (a.astype(np.float32) / 257).astype(np.uint8)
im = Image.fromarray(a[y0:y1, x0:x1]).convert("RGB")
im = im.resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * sc; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0), width=1); d.text((X + 2, 2), str(x), fill=(255, 60, 60))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * sc; d.line([(0, Y), (im.width, Y)], fill=(0, 160, 255), width=1); d.text((2, Y + 2), str(y), fill=(60, 180, 255))
im.save(out)
