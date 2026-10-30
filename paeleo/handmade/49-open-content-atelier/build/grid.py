"""Semantic cropper aid: crop a source with a labelled pixel grid (coordinates are in the stored source file).
Usage: grid.py src.jpg x0 y0 x1 y1 step zoom out.jpg"""
import sys
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[8]; x0, y0, x1, y1, step = map(int, sys.argv[2:7]); z = float(sys.argv[7])
im = Image.open(src).crop((x0, y0, x1, y1)); im = im.resize((int(im.width * z), int(im.height * z)))
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * z; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if x % (step * 5) == 0 else (255, 150, 150), width=1); d.text((X + 2, 2), str(x), fill='red')
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * z; d.line([(0, Y), (im.width, Y)], fill=(0, 0, 255) if y % (step * 5) == 0 else (150, 150, 255), width=1); d.text((2, Y + 2), str(y), fill='blue')
im.save(out, quality=90)
