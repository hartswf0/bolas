"""Matte every archive dog frame: SAM outline -> fur trimap -> solved alpha + decontaminated F -> premultiplied RGBA.
Writes build/cache/dog/fNNN.npz (premult at source res, crop box) and proof diagnostics."""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from lib_matte import *

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '../../kit/archive-dog')
OUT = os.path.join(HERE, 'cache/dog'); os.makedirs(OUT, exist_ok=True)
FUR = dict(r_in=2, r_out=3)          # edge class: fur (wide unknown band)


def area(P):
    P = np.array(P, float); x, y = P[:, 0], P[:, 1]
    return .5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def pick(polys):
    """the dog's own outline: the largest polygon not touching the frame border, plus small parts inside its box"""
    cand = [P for P in polys if len(P) > 2]
    def border(P):
        P = np.array(P); return P[:, 0].min() <= 1 or P[:, 1].max() >= 286
    main = max([P for P in cand if not border(P)] or cand, key=area)
    M = np.array(main); x0, y0 = M.min(0) - 20; x1, y1 = M.max(0) + 20
    keep = [main]
    for P in cand:
        if P is main: continue
        Q = np.array(P)
        if Q[:, 0].min() >= x0 and Q[:, 0].max() <= x1 and Q[:, 1].min() >= y0 and Q[:, 1].max() <= y1 and not border(P):
            keep.append(P)
    return keep


def main():
    masks = json.load(open(os.path.join(KIT, 'masks.json')))
    log = []
    for i in range(50):
        I = load(os.path.join(KIT, 'frames/f%03d.jpg' % i))
        H, W = I.shape[:2]
        polys = pick(masks[str(i)])
        cov = coverage(polys, W, H)
        tri = trimap(cov, **FUR)
        a, F, B = solve(I, tri, cov)
        P = premult(F, a)
        ys, xs = np.nonzero(a > 0.004)
        box_ = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        x0, y0, x1, y1 = box_
        np.savez_compressed(os.path.join(OUT, 'f%03d.npz' % i), P=P[y0:y1, x0:x1].astype(np.float16), box=np.array(box_),
                            tri=tri[y0:y1, x0:x1], cov=cov[y0:y1, x0:x1].astype(np.float16))
        band = (a > .02) & (a < .98)
        # contamination proxy: how far the raw pixel in the band sits from the recovered foreground colour
        cont = float(np.abs(I - F)[band].mean()) if band.any() else 0.
        log.append({'frame': i, 'box': box_, 'unknown_px': int((tri == -1).sum()), 'fractional_px': int(band.sum()),
                    'mean_abs_raw_minus_F_in_band': round(cont, 4), 'premult_ok': premult_ok(P)})
    json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'), indent=0)
    print('dog mattes', len(log), 'premult_ok all', all(l['premult_ok'] for l in log))


if __name__ == '__main__':
    main()
