"""Test page at print resolution (300 dpi, 1 u = 0.1 mm = 1.1811 px): the hinge
panels P1 | P2 open with their fold marks, an arrow, and the folded panel V(x'),
from the same strip-art.png the film uses, printed on the neutralised paper scan.
Lettering and the pleat diagram are pen.py strokes."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold_shot as F  # noqa
from pen import pen    # noqa  (proposals/pen.py, on path via fold_shot)

K = 300 / 254.0           # px per u
sheet = np.asarray(Image.open(os.path.join(F.MEDIA, "strip-art.png")))
V = F.folded_V(sheet)
sw = int(round(F.SW * K)); sh = int(round(F.SH * K))
open_im = Image.fromarray(sheet).resize((sw, sh), Image.LANCZOS)
vw = int(round(V.shape[1] * K))
fold_im = Image.fromarray(V).resize((vw, sh), Image.LANCZOS)

PW = sw + 240
PH = 220 + sh + 140 + sh + 200
ink = Image.new("L", (PW, PH), 255)
ink.paste(open_im, (120, 220))
fx = PW - 120 - vw
ink.paste(fold_im, (fx, 220 + sh + 140))
d = ImageDraw.Draw(ink)
pen(d, "FOLDED DIALOGUE - THE BORROWED KEY", 120, 70, 64, seed=1)
pen(d, "OPEN: READ PANEL ONE, THEN PANEL TWO", 120, 170, 30, seed=2)
pen(d, "FOLD A MOUNTAIN, M VALLEY, LAY B ON A", fx, 220 + sh + 95, 30, seed=3)
# arrow, pen-drawn
ay = 220 + sh + 140 + sh // 2
ax0, ax1 = fx - 520, fx - 80
for k in range(3):
    F_ = (ax0, ay + k * 4 - 4, ax1, ay + k * 4 - 4)
    d.line(F_, fill=18, width=6)
d.polygon([(ax1 + 40, ay), (ax1 - 30, ay - 45), (ax1 - 30, ay + 45)], fill=18)
# pleat cross-section (side view), layers labelled
cx0, cy0 = 120, 220 + sh + 200
s = 0.62
def P(X, z):
    return (cx0 + X * s, cy0 + 300 - z * 4)
pts3 = [P(0, 0), P(1190, 0)]
d.line(pts3, fill=18, width=5)
d.line([P(0, 16), P(590, 16)], fill=18, width=5)
d.arc([P(-16, 16)[0] - 10, P(0, 16)[1] - 8, P(0, 0)[0] + 10, P(0, 0)[1] + 8], 90, 270, fill=18, width=5)
d.line([P(590, 32), P(-30, 32)], fill=18, width=5)
d.arc([P(590, 0)[0] - 10, P(590, 32)[1] - 2, P(590, 16)[0] + 22, P(590, 16)[1] + 2], 270, 90, fill=18, width=5)
pen(d, "M", P(0, 0)[0] - 50, P(0, 0)[1] - 50, 30, seed=11)
pen(d, "A ON B", P(590, 0)[0] + 30, P(590, 32)[1] - 20, 30, seed=12)
pen(d, "TOP: PANEL ONE LEFT OF A, FACE UP", cx0, cy0 + 400, 28, seed=13)
pen(d, "MIDDLE: A TO M, FACE DOWN, HIDDEN", cx0, cy0 + 450, 28); pen(d, "BOTTOM: PANEL TWO, FACE UP", cx0, cy0 + 500, 28, seed=14)

inkf = 1 - np.asarray(ink, np.float32) / 255.0
paper = F.paper_scan(PW, PH, 0) if PH <= int(1630 * PW / 1280) else None
if paper is None:
    p = F.paper_scan(PW, int(1630 * PW / 1280), 0)
    paper = np.concatenate([p, p[::-1]], 0)[:PH]
out = paper * (1 - 0.93 * inkf[..., None])
dst = os.path.join(F.WORK, "test-page.png")
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, dpi=(300, 300))
print(dst, PW, PH)
