"""SCION 45 · Matte artist. Cut RGBA cels of the real archive dog from its own frames.

Input : kit/archive-dog/frames/fNNN.jpg (Amateur Film New Jersey C, public domain) + masks.json (SAM polygons)
Output: build/cache/cels/dog_NNN.png (RGBA, source pixel space 384x288, straight alpha) + cels.json (per-cel measurements)
Op    : alpha = SAM polygon  AND  garbage matte (hand-authored, below)  -> 1 px feather.  No pixel of the dog is drawn.
Version: cels-v3
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
KIT = os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog')
OUT = os.path.join(HERE, 'cache/cels')

# Garbage mattes (source px): SAM took grass and shadow with the dog in these frames. Keep only inside the box/polygon.
GARBAGE = {
    20: [(118, 90), (300, 90), (300, 210), (118, 210)],
    21: [(140, 90), (300, 90), (300, 210), (140, 210)],
    22: [(150, 90), (300, 90), (300, 210), (150, 210)],
    24: [(140, 95), (300, 95), (300, 210), (140, 210)],
    25: [(150, 95), (300, 95), (300, 210), (150, 210)],
    12: [(60, 60), (225, 60), (225, 210), (60, 210)],   # stray tail-flare fragment
    6: [(60, 60), (235, 60), (235, 210), (60, 210)],
    8: [(70, 60), (240, 60), (240, 215), (70, 215)],
}
SKIP = {23}  # SAM mask covers half the lawn; unusable


def cut(i):
    im = Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % i)).convert('RGB')
    masks = json.load(open(os.path.join(KIT, 'masks.json')))[str(i)]
    mk = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(mk)
    for poly in masks:
        d.polygon([tuple(p) for p in poly], fill=255)
    if i in GARBAGE:
        g = Image.new('L', im.size, 0)
        ImageDraw.Draw(g).polygon(GARBAGE[i], fill=255)
        mk = Image.fromarray(np.minimum(np.array(mk), np.array(g)))
    a = np.array(mk).astype(np.float32) / 255
    # keep the largest connected blob only (drop SAM islands) via flood from the densest column
    a = keep_main(a)
    mk = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    rgba = im.convert('RGBA')
    rgba.putalpha(mk)
    return rgba


def keep_main(a):
    m = a > 0.5
    H, W = m.shape
    lab = np.zeros((H, W), np.int32)
    cur = 0
    sizes = {}
    for y in range(H):
        for x in range(W):
            if m[y, x] and not lab[y, x]:
                cur += 1
                st = [(y, x)]
                lab[y, x] = cur
                n = 0
                while st:
                    yy, xx = st.pop()
                    n += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        y2, x2 = yy + dy, xx + dx
                        if 0 <= y2 < H and 0 <= x2 < W and m[y2, x2] and not lab[y2, x2]:
                            lab[y2, x2] = cur
                            st.append((y2, x2))
                sizes[cur] = n
    if not sizes:
        return a
    big = max(sizes, key=sizes.get)
    return (lab == big).astype(np.float32)


def measure(rgba):
    a = np.array(rgba)[:, :, 3].astype(np.float32) / 255
    ys, xs = np.nonzero(a > 0.5)
    bb = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    foot = int(ys.max())
    # feet: alpha in the lowest 6 rows, grouped into runs of columns
    low = a[foot - 5:foot + 1].max(0) > 0.5
    runs, x = [], 0
    while x < len(low):
        if low[x]:
            x0 = x
            while x < len(low) and low[x]:
                x += 1
            runs.append([x0, x - 1])
        x += 1
    return {'bbox': bb, 'foot_y': foot, 'cx': float(xs.mean()), 'cy': float(ys.mean()), 'area': int(len(xs)), 'feet_runs': runs}


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for i in range(50):
        if i in SKIP:
            continue
        c = cut(i)
        c.save(os.path.join(OUT, 'dog_%03d.png' % i))
        meta[i] = measure(c)
    json.dump(meta, open(os.path.join(OUT, 'cels.json'), 'w'), indent=0)
    print('cels', len(meta))
