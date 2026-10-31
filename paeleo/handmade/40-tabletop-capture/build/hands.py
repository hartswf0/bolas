"""SCION 40 · the performers' hands, cut from public-domain archive footage.
Source: hand-sam shot (The Door to Heaven, 1941, archive.org/details/DoortoHe1941, public domain): a hand and forearm
reaching in from the right and holding a card by its edge, 62 frames at 12 fps, with SAM 2.1 masks per frame.
Operation: the SAM polygon gives the hand; the forearm (which SAM left out) is traced column by column as the bright run
continuous with the wrist; the arm is then extended past the frame edge by repeating its last columns along its slope,
so it can reach the edge of the table. Grip = the fingertips (the hand's leftmost points). Arm direction = grip -> the
forearm's exit. Writes cache/hands/f%03d.png (RGBA, grey tinted warm) and data/hands.json."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

EXT = 700


def main():
    masks = json.load(open(os.path.join(HAND_SRC, 'masks.json')))
    od = os.path.join(CACHE, 'hands')
    os_makedirs(od)
    meta = []
    for f in range(62):
        im = Image.open(os.path.join(HAND_SRC, 'frames', 'f%03d.jpg' % f)).convert('L')
        L = np.asarray(im, np.float32)
        h, w = L.shape
        m = Image.new('L', (w, h), 0)
        for poly in masks[str(f)]:
            ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
        M = np.asarray(m) > 0
        ys, xs = np.where(M)
        wx = xs.max() - 4
        # forearm: per column, the bright run that overlaps the previous column's run
        cols = np.where(M[:, wx])[0]
        lo, hi = cols.min(), cols.max()
        arm = np.zeros_like(M)
        runs = []
        for x in range(wx, w):
            col = L[:, x] > 58
            c = (lo + hi) // 2
            if not col[c]:
                cand = np.where(col[lo:hi + 1])[0]
                if len(cand) == 0:
                    break
                c = lo + cand[len(cand) // 2]
            a = c
            while a > 0 and col[a - 1]:
                a -= 1
            b = c
            while b < h - 1 and col[b + 1]:
                b += 1
            if b - a > (hi - lo) * 1.6 + 6:     # ran into the card or the background: keep the previous width
                a, b = lo, hi
            arm[a:b + 1, x] = True
            runs.append((x, a, b))
            lo, hi = a, b
        M = M | arm
        # extend the arm beyond the frame along its slope (fit the last 30 columns' centres)
        r = np.array(runs[-30:], float)
        cy = (r[:, 1] + r[:, 2]) / 2
        k = np.polyfit(r[:, 0], cy, 1)[0] if len(r) > 3 else 0.0
        width = (r[:, 2] - r[:, 1]).mean() if len(r) else 20
        W2 = w + EXT
        big = np.zeros((h + 400, W2), np.float32)
        BM = np.zeros((h + 400, W2), bool)
        oy = 200
        big[oy:oy + h, :w] = L
        BM[oy:oy + h, :w] = M
        x_last, a_last, b_last = runs[-1]
        colv = L[a_last:b_last + 1, x_last]
        for x in range(x_last + 1, W2):
            dy = (x - x_last) * k
            a = int(round(a_last + dy)) + oy
            n = len(colv)
            yy = np.arange(a, a + n)
            ok = (yy >= 0) & (yy < big.shape[0])
            big[yy[ok], x] = colv[ok] * (1 - 0.0003 * (x - x_last))
            BM[yy[ok], x] = True
        # soft matte edge
        alpha = Image.fromarray((BM * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
        g = np.clip(big * 1.25 + 10, 0, 255)
        rgb = np.stack([g * 1.0, g * 0.86, g * 0.74], -1)
        spr = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
        spr.putalpha(alpha)
        spr.save(os.path.join(od, 'f%03d.png' % f))
        tip = xs.min()
        sel = xs < tip + 6
        gx, gy = float(xs[sel].mean()) + 4, float(ys[sel].mean()) + oy
        ex, ey = W2 - 1, (a_last + b_last) / 2 + (W2 - 1 - x_last) * k + oy
        meta.append(dict(f=f, grip=[gx, gy], arm_angle=math.atan2(ey - gy, ex - gx), size=[W2, h + 400], arm_width=float(width)))
    json.dump(dict(source=HAND_SRC, frames=meta), open(os.path.join(DATA, 'hands.json'), 'w'), indent=1)
    print('hands', len(meta))


if __name__ == '__main__':
    main()
