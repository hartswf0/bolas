"""Proof helper: enlarge a source frame region with a labelled pixel grid so fragment polygons can be cut by eye.
usage: gridlook.py <frame.jpg> x0 y0 x1 y1 scale out.jpg [masks.json frame_id] [polys.json]"""
import sys, json
from PIL import Image, ImageDraw, ImageOps
a = sys.argv
im = Image.open(a[1]).convert('RGB')
x0, y0, x1, y1, s = map(int, a[2:7])
im = ImageOps.autocontrast(im.crop((x0, y0, x1, y1)), cutoff=1).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS)
d = ImageDraw.Draw(im)
for x in range((x0 // 10) * 10, x1, 10):
    X = (x - x0) * s
    d.line([(X, 0), (X, im.height)], fill=(0, 255, 255) if x % 50 == 0 else (0, 90, 90), width=1)
    if x % 50 == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // 10) * 10, y1, 10):
    Y = (y - y0) * s
    d.line([(0, Y), (im.width, Y)], fill=(0, 255, 255) if y % 50 == 0 else (0, 90, 90), width=1)
    if y % 50 == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
if len(a) > 8:
    m = json.load(open(a[8]))
    for p in m.get(a[9], []):
        d.line([((q[0] - x0) * s, (q[1] - y0) * s) for q in p] + [((p[0][0] - x0) * s, (p[0][1] - y0) * s)], fill=(255, 0, 0), width=1)
if len(a) > 10:
    for name, p in json.load(open(a[10])).items():
        pts = [((q[0] - x0) * s, (q[1] - y0) * s) for q in p]
        d.line(pts + [pts[0]], fill=(0, 255, 0), width=2)
        d.text(pts[0], name, fill=(0, 255, 0))
im.save(a[7], quality=90)
