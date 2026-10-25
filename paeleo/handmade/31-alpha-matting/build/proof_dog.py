"""Matte diagnostics for the dog: source | trimap | alpha | F | cookie-cut on dusk | solved on dusk | solved on lamp | solved on checker"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from lib_matte import *
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '../../kit/archive-dog')
frames = [int(a) for a in sys.argv[1:]] or [9, 22, 45]
rows = []
for i in frames:
    z = np.load(os.path.join(HERE, 'cache/dog/f%03d.npz' % i))
    P = z['P'].astype(np.float32); x0, y0, x1, y1 = z['box']; tri = z['tri']; cov = z['cov'].astype(np.float32)
    I = load(os.path.join(KIT, 'frames/f%03d.jpg' % i))[y0:y1, x0:x1]
    a = P[..., 3]; F = P[..., :3] / np.maximum(a, 1e-4)[..., None]
    h, w = a.shape
    dusk = np.zeros((h, w, 3), np.float32) + np.array([.10, .11, .2])
    lamp = np.zeros((h, w, 3), np.float32) + np.array([1., .78, .45])
    yy, xx = np.mgrid[:h, :w]; chk = (((yy // 8) + (xx // 8)) % 2)[..., None] * np.array([.9, .2, .6]) + .05
    def comp(bg, Fc, al): return Fc * al[..., None] + bg * (1 - al[..., None])
    t = np.where(tri[..., None] == 1, 1., np.where(tri[..., None] == 0, 0., .5)) * np.ones(3)
    tiles = [I, t, np.dstack([a] * 3), F * (a[..., None] > .01), comp(dusk, I, cov), comp(dusk, F, a), comp(lamp, F, a), comp(chk, F, a)]
    rows.append(np.concatenate(tiles, 1))
W = max(r.shape[1] for r in rows)
rows = [np.pad(r, [(0, 4), (0, W - r.shape[1]), (0, 0)]) for r in rows]
im = Image.fromarray((np.clip(np.concatenate(rows, 0), 0, 1) * 255).astype(np.uint8))
im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
out = os.path.join(HERE, '../proof/dog_matte_diagnostics.jpg'); im.save(out, quality=90); print(out, im.size)
