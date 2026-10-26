"""Round 2, critic repair 1/3: search all 4,164 dogs for a stride twin of #135 (dome body, head
low at the chest): head top clearly below the back line, small visual distance to #135.
Prints the ranking and writes sheets/r2-twins.png (top 18)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import qd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dogs = qd.load('dog')
F = json.load(open(f'{HERE}/work/dog_features.json'))


def norm(d, head_right):
    S = qd.strokes_np(d); x0, y0, x1, y1 = qd.bbox(S)
    sc = 1.0 / max(x1 - x0, 1)
    P = np.concatenate(qd.densify(S, 2.0))
    X = (P[:, 0] - x0) * sc; Y = (P[:, 1] - y1) * sc
    if not head_right:
        X = 1 - X
    return X, Y


def head_drop(X, Y):
    front = X > 0.75; mid = (X > 0.25) & (X < 0.7)
    if not front.any() or not mid.any():
        return -1
    return (Y[front].min() - Y[mid].min()) / (Y.max() - Y.min() + 1e-9)


def vec(X, Y):
    img = Image.new('L', (64, 40), 0); dr = ImageDraw.Draw(img)
    pts = list(zip(X * 60 + 2, Y * 60 + 38))
    for p in pts:
        dr.point(p, fill=255)
    a = np.asarray(img, float)
    for _ in range(3):
        a = (np.roll(a, 1, 0) + a + np.roll(a, -1, 0)) / 3
        a = (np.roll(a, 1, 1) + a + np.roll(a, -1, 1)) / 3
    v = a.ravel(); return v / (np.linalg.norm(v) + 1e-9)


ref = vec(*norm(dogs[135], True))
rows = []
for f in F:
    if not f['recognized'] or f['ns'] < 3 or f['ns'] > 12 or f['sym'] > 0.6 or not (1.2 < f['aspect'] < 2.4) or f['legrows'] < 0.15:
        continue
    for hr in (True, False):
        X, Y = norm(dogs[f['idx']], hr)
        hd = head_drop(X, Y)
        if hd < 0.08:
            continue
        rows.append((float(1 - vec(X, Y) @ ref), f['idx'], hr, round(hd, 3)))
rows.sort()
print('candidates', len(rows))
for r in rows[:25]:
    print(r)
json.dump(rows[:60], open(f'{HERE}/work/twins.json', 'w'))
cols, cw, ch = 6, 250, 170
img = Image.new('RGB', (cols * cw, 3 * ch), 'white'); dr = ImageDraw.Draw(img)
for k, (dist, idx, hr, hd) in enumerate(rows[:18]):
    X, Y = norm(dogs[idx], hr)
    S = qd.strokes_np(dogs[idx]); x0, y0, x1, y1 = qd.bbox(S); sc = (cw - 30) / max(x1 - x0, 1); sc = min(sc, (ch - 40) / max(y1 - y0, 1))
    cx, cy = (k % cols) * cw, (k // cols) * ch
    for s in S:
        xs = (s[:, 0] - x0) if hr else (x1 - s[:, 0])
        pts = list(zip(cx + 10 + xs * sc, cy + 25 + (s[:, 1] - y0) * sc))
        dr.line(pts if len(pts) > 1 else pts * 2, fill='black', width=3)
    dr.text((cx + 4, cy + 3), f'{idx} {"" if hr else "mirror "}d={dist:.2f} drop={hd:.2f}', fill=(200, 0, 0))
img.save(f'{HERE}/sheets/r2-twins.png')
