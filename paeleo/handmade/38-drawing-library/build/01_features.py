"""Motion analyst + drawing clustering agent, pass 1.
Compute pose features for every real dog doodle from its stroke data, propose a
coarse automatic class, and print contact sheets for a human-eye (agent) review.
Writes work/dog_features.json and sheets/auto-<class>-<k>.png
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import qd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dogs = qd.load('dog')
feats = []
for idx, d in enumerate(dogs):
    f = qd.features(d)
    f['idx'] = idx
    a, s = f['aspect'], f['sym']
    cls = 'other'
    if not d['recognized'] or f['ns'] < 3:
        cls = 'reject'
    elif s > 0.62 and a < 1.35:
        cls = 'front'
    elif a >= 1.15:
        left = (f['tl'] + 0.06 < f['tr']) or f['hs'] < -0.25
        right = (f['tr'] + 0.06 < f['tl']) or f['hs'] > 0.25
        side = 'L' if left and not right else ('R' if right and not left else '?')
        if a > 2.0 and f['legrows'] < 0.2:
            cls = 'lie' + side
        elif f['legrows'] >= 0.18 and f['legruns'] >= 2:
            cls = 'stand' + side
        else:
            cls = 'side' + side
    f['auto'] = cls
    feats.append(f)

json.dump(feats, open(f'{HERE}/work/dog_features.json', 'w'))
from collections import Counter
print(Counter(f['auto'] for f in feats))


def sheet(items, path, cols=10, rows=6, cw=150, ch=120):
    img = Image.new('RGB', (cols * cw, rows * ch), 'white')
    dr = ImageDraw.Draw(img)
    for k, f in enumerate(items[:cols * rows]):
        d = dogs[f['idx']]
        S = qd.strokes_np(d)
        x0, y0, x1, y1 = qd.bbox(S)
        sc = min((cw - 16) / max(x1 - x0, 1), (ch - 26) / max(y1 - y0, 1))
        cx, cy = (k % cols) * cw, (k // cols) * ch
        for s in S:
            pts = [(cx + 8 + (p[0] - x0) * sc, cy + 18 + (p[1] - y0) * sc) for p in s]
            if len(pts) == 1:
                pts = pts * 2
            dr.line(pts, fill='black', width=2)
        dr.text((cx + 3, cy + 2), f"{f['idx']}", fill=(200, 0, 0))
        dr.rectangle([cx, cy, cx + cw - 1, cy + ch - 1], outline=(220, 220, 220))
    img.save(path)


if __name__ == '__main__':
    os.makedirs(f'{HERE}/sheets', exist_ok=True)
    by = {}
    for f in feats:
        by.setdefault(f['auto'], []).append(f)
    for cls, items in by.items():
        if cls in ('reject',):
            continue
        # simpler drawings first: fewer points read better at small size and swap cleanly
        items.sort(key=lambda f: f['npts'])
        for k in range(min(3, (len(items) + 59) // 60)):
            sheet(items[k * 60:(k + 1) * 60], f'{HERE}/sheets/auto-{cls}-{k}.png')
    # lying candidates are rare: a dedicated pool, widest first (sheets/pool-lie-*)
    ok = [f for f in feats if f['auto'] not in ('reject', 'front') and f['recognized'] and 4 <= f['ns'] <= 14]
    lie = sorted([f for f in ok if f['aspect'] > 1.75 and f['legrows'] < 0.3], key=lambda f: -f['aspect'])
    for k in range(0, min(len(lie), 360), 60):
        sheet(lie[k:k + 60], f'{HERE}/sheets/pool-lie-{k // 60}.png')
