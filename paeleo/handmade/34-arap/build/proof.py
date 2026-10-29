"""Counterexample set: ARAP against a naive warp with the same handles.
Naive = Shepard (inverse-distance) interpolation of the handle displacements, a global point warp with no mesh energy.
Measured per pose: inverted triangles, mean and worst stretch of the triangles (|sigma - 1| of each triangle's Jacobian),
and the same at the protected eye/nose. Writes proof/arap_vs_naive.jpg and proof/proof.json."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from rig import DogP, pose_P
from raster import Tex, draw_pieces


def jac_sig(V, X, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    A, B, C = X[T[:, 0]], X[T[:, 1]], X[T[:, 2]]
    M0 = np.stack([b - a, c - a], 2); M1 = np.stack([B - A, C - A], 2)
    J = M1 @ np.linalg.inv(M0)
    s = np.linalg.svd(J, compute_uv=False)
    det = np.linalg.det(J)
    return s, det


def shepard(V, idx_groups, targets):
    src = np.vstack([V[i] for i in idx_groups]); dst = np.vstack(targets)
    d = np.sqrt(((V[:, None, :] - src[None]) ** 2).sum(2)) + 1e-6
    w = 1 / d ** 3
    return V + (w @ (dst - src)) / w.sum(1, keepdims=True)


d = DogP()
tb = Tex(os.path.join(DRAW, 'P_body.png'))
poses = {'head low (approach)': dict(head=0.22, ear=0.55, tail=0.25), 'cowering (retreat)': dict(crouch=0.9, head=0.35, ear=0.0, tail=1.35),
         'lying across the sill': dict(lie=1.0, head=0.6, ear=0.7, tail=0.3)}
rows = []; res = {}
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
for name, a in poses.items():
    p = pose_P(d, a)
    tg = d.targets(p)[0]
    X = d.solver.solve_repair(tg, iters=80, X0=d.body.V.copy()).copy()
    keys = list(d.H.keys())
    Xn = shepard(d.body.V, [d.H[k] for k in keys], [tg[k] for k in keys])
    r = {}
    for lab, Y in (('arap', X), ('naive', Xn)):
        s, det = jac_sig(d.body.V, Y, d.body.T)
        dist = np.abs(s - 1).max(1)
        r[lab] = dict(inverted=int((det <= 0).sum()), mean_stretch=round(float(dist.mean()), 3), p95_stretch=round(float(np.percentile(dist, 95)), 3))
    res[name] = r
    ims = []
    for lab, Y in (('ARAP', X), ('naive warp', Xn)):
        S = np.stack([260 + 0.4 * Y[:, 0], 330 - 0.4 * Y[:, 1]], 1)
        pm, _ = draw_pieces((520, 360), [(S, d.body.T, d.body.uv, tb, d.body.layer, 0)], wire=[0.35])
        rgb = np.ones((360, 520, 3)) * 0.22; rgb = rgb * (1 - pm[..., 3:4]) + pm[..., :3]
        im = Image.fromarray((rgb * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
        rr = r['arap' if lab == 'ARAP' else 'naive']
        dr.text((8, 8), '%s - %s' % (name, lab), font=font, fill=(240, 220, 180))
        dr.text((8, 30), 'inverted %d   mean |s-1| %.3f' % (rr['inverted'], rr['mean_stretch']), font=font, fill=(200, 200, 200))
        ims.append(im)
    rows.append(ims)
sheet = Image.new('RGB', (1040, 360 * len(rows)))
for k, (a_, b_) in enumerate(rows):
    sheet.paste(a_, (0, 360 * k)); sheet.paste(b_, (520, 360 * k))
sheet.save(os.path.join(ROOT, 'proof', 'arap_vs_naive.jpg'), quality=88)
json.dump(dict(about=__doc__, poses=res), open(os.path.join(ROOT, 'proof', 'proof.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
