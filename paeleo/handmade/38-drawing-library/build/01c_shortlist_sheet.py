"""Large review sheet of an index list (argv) for labelling by eye."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import qd
from PIL import Image, ImageDraw
dogs = qd.load('dog')
ids = [int(a) for a in sys.argv[2].split(',')]
cols, cw, ch = 6, 250, 180
rows = (len(ids) + cols - 1) // cols
img = Image.new('RGB', (cols * cw, rows * ch), 'white'); dr = ImageDraw.Draw(img)
for k, i in enumerate(ids):
    S = qd.strokes_np(dogs[i]); x0, y0, x1, y1 = qd.bbox(S)
    sc = min((cw - 20) / max(x1 - x0, 1), (ch - 30) / max(y1 - y0, 1))
    cx, cy = (k % cols) * cw, (k // cols) * ch
    for s in S:
        pts = [(cx + 10 + (p[0] - x0) * sc, cy + 22 + (p[1] - y0) * sc) for p in s]
        dr.line(pts if len(pts) > 1 else pts * 2, fill='black', width=3)
    dr.text((cx + 4, cy + 3), str(i), fill=(200, 0, 0))
    dr.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], outline=(210, 210, 210))
img.save(sys.argv[1])
