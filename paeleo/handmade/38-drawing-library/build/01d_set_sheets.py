"""Review sheets for the set: house, door, moon, hand, face, stairs, tree, fence."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import qd
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
want = {'house': (2, 5), 'door': (2, 6), 'moon': (1, 3), 'hand': (1, 4), 'face': (4, 8), 'stairs': (1, 3), 'tree': (2, 5), 'fence': (3, 12)}
for cat, (a, b) in want.items():
    L = qd.load(cat, 1500)
    items = [(i, d) for i, d in enumerate(L) if d['recognized'] and a <= len(d['drawing']) <= b][:60]
    cols, cw, ch = 10, 150, 130
    img = Image.new('RGB', (cols * cw, 6 * ch), 'white'); dr = ImageDraw.Draw(img)
    for k, (i, d) in enumerate(items):
        S = qd.strokes_np(d); x0, y0, x1, y1 = qd.bbox(S)
        sc = min((cw - 16) / max(x1 - x0, 1), (ch - 26) / max(y1 - y0, 1))
        cx, cy = (k % cols) * cw, (k // cols) * ch
        for s in S:
            pts = [(cx + 8 + (p[0] - x0) * sc, cy + 18 + (p[1] - y0) * sc) for p in s]
            dr.line(pts if len(pts) > 1 else pts * 2, fill='black', width=2)
        dr.text((cx + 3, cy + 2), str(i), fill=(200, 0, 0))
        dr.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], outline=(220, 220, 220))
    img.save(f'{HERE}/sheets/set-{cat}.png')
