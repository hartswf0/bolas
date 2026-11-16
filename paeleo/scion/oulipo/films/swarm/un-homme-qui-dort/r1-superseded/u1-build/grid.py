"""Draw a coordinate grid over a crop of a plate (for picking seeds). Usage: grid.py img x0 y0 x1 y1 step out [scale]"""
import sys
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
f, x0, y0, x1, y1, step, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
sc = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
im = Image.open(f).convert("RGB").crop((x0, y0, x1, y1))
im = im.resize((int(im.width * sc), int(im.height * sc)))
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * sc; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if x % (step * 5) == 0 else (255, 150, 0), width=1)
    d.text((X + 2, 2), str(x), fill=(255, 0, 0))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * sc; d.line([(0, Y), (im.width, Y)], fill=(0, 160, 255) if y % (step * 5) == 0 else (0, 220, 120), width=1)
    d.text((2, Y + 2), str(y), fill=(0, 100, 255))
im.save(out)
