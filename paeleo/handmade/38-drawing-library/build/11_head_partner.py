"""Round 3, critic repair 1: a stride partner that shares the HEAD SHAPE of a head-low anchor.
Over all 4,164 dogs (head-low: head drop >= 8% of height), compare the head-end crop (front 30% of the
length, normalised to its own box) by blurred-raster distance, plus half the whole-body distance.
Writes work/head_partners.json and sheets/r3-head-partners-<anchor>.png; picks were made by eye."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import qd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dogs = qd.load('dog')
F = json.load(open(f'{HERE}/work/dog_features.json'))


def pts(d, head_right):
    S = qd.strokes_np(d); x0, y0, x1, y1 = qd.bbox(S)
    P = np.concatenate(qd.densify(S, 1.5))
    X = (P[:, 0] - x0) / max(x1 - x0, 1); Y = (P[:, 1] - y0) / max(x1 - x0, 1)
    return (X if head_right else 1 - X), Y


def ras(X, Y, n=32):
    if len(X) == 0:
        return np.zeros(n * n)
    a0, a1, b0, b1 = X.min(), X.max(), Y.min(), Y.max()
    s = max(a1 - a0, b1 - b0, 1e-6)
    img = np.zeros((n, n))
    ix = np.clip(((X - a0) / s * (n - 3) + 1).astype(int), 0, n - 1)
    iy = np.clip(((Y - b0) / s * (n - 3) + 1).astype(int), 0, n - 1)
    img[iy, ix] = 1
    for _ in range(2):
        img = (np.roll(img, 1, 0) + img + np.roll(img, -1, 0)) / 3
        img = (np.roll(img, 1, 1) + img + np.roll(img, -1, 1)) / 3
    v = img.ravel(); return v / (np.linalg.norm(v) + 1e-9)


def head_drop(X, Y):
    front = X > 0.75; mid = (X > 0.25) & (X < 0.7)
    if not front.any() or not mid.any():
        return -1
    return (Y[front].min() - Y[mid].min()) / (Y.max() - Y.min() + 1e-9)


def desc(idx, hr):
    X, Y = pts(dogs[idx], hr)
    h = X > 0.7
    return ras(X[h], Y[h]), ras(X, Y), head_drop(X, Y)


pool = []
for f in F:
    if not f['recognized'] or not (3 <= f['ns'] <= 12) or f['sym'] > 0.6 or not (1.2 < f['aspect'] < 2.4) or f['legrows'] < 0.15:
        continue
    for hr in (True, False):
        hv, bv, hd = desc(f['idx'], hr)
        if hd >= 0.0:
            pool.append((f['idx'], hr, hv, bv, hd))
print('head-low pool', len(pool))
out = {}
for anchor, ahr in ((135, True), (1309, False), (2830, True)):
    ah, ab, _ = desc(anchor, ahr)
    rows = sorted(((1 - h @ ah) + 1.0 * (1 - b @ ab), i, hr, round(float(1 - h @ ah), 3), round(float(1 - b @ ab), 3), round(float(hd), 3))
                  for i, hr, h, b, hd in pool if i != anchor)
    out[anchor] = rows[:40]
    cols, cw, ch = 6, 250, 170
    img = Image.new('RGB', (cols * cw, 4 * ch), 'white'); dr = ImageDraw.Draw(img)
    items = [(0, anchor, ahr, 0, 0, 0)] + rows[:23]
    for k, (sc_, idx, hr, hd_, bd_, drop) in enumerate(items):
        S = qd.strokes_np(dogs[idx]); x0, y0, x1, y1 = qd.bbox(S)
        sc = min((cw - 30) / max(x1 - x0, 1), (ch - 40) / max(y1 - y0, 1))
        cx, cy = (k % cols) * cw, (k // cols) * ch
        for s in S:
            xs = (s[:, 0] - x0) if hr else (x1 - s[:, 0])
            p = list(zip(cx + 10 + xs * sc, cy + 25 + (s[:, 1] - y0) * sc))
            dr.line(p if len(p) > 1 else p * 2, fill='black', width=3)
        dr.text((cx + 4, cy + 3), f'{idx}{"" if hr else " mirrored"} head {hd_} body {bd_}' if k else f'ANCHOR {idx}', fill=(200, 0, 0))
    img.save(f'{HERE}/sheets/r3-head-partners-{anchor}.png')
json.dump({str(k): v for k, v in out.items()}, open(f'{HERE}/work/head_partners.json', 'w'))
