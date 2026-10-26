"""Matte the rest of the world from rights-recorded archive frames:
woman (Straight Talk f000, hair against the white door), hand+forearm (Door to Heaven f000, on black),
door leaf with its lace curtain (Straight Talk f031), clouds as smoke (Top of the Cloud, 62 frames, on blue sky)."""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from lib_matte import *
from polys import WOMAN_F000, FOREARM
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '../../kit')
SRC = os.path.join(HERE, '../sources')
C = os.path.join(HERE, 'cache'); os.makedirs(C + '/cloud', exist_ok=True)
log = {}


def crop_save(name, P, extra=None):
    a = P[..., 3]; ys, xs = np.nonzero(a > .004)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    np.savez_compressed(os.path.join(C, name), P=P[y0:y1, x0:x1].astype(np.float16), box=np.array([x0, y0, x1, y1]), **(extra or {}))
    log[name] = {'box': [int(x0), int(y0), int(x1), int(y1)], 'premult_ok': premult_ok(P), 'fractional_px': int(((a > .02) & (a < .98)).sum())}


# woman: hair / fabric edge class, drawn trimap prior, wider band because the outline is hand-drawn
I = load(os.path.join(KIT, 'archive-door/frames/f000.jpg')); H, W = I.shape[:2]
cov = coverage([WOMAN_F000], W, H)
a, F, B = solve(I, trimap(cov, 4, 3), cov)
crop_save('woman.npz', premult(F, a))

# hand + forearm: skin on black; SAM hand outline unioned with the drawn forearm
I = load(os.path.join(SRC, 'hand/f000.jpg')); H, W = I.shape[:2]
hm = json.load(open(os.path.join(SRC, 'hand/masks.json')))['0']
cov = np.maximum(coverage(hm, W, H), coverage([FOREARM], W, H))
a, F, B = solve(I, trimap(cov, 7, 4), cov)
crop_save('hand.npz', premult(F, a))

# door leaf: hard painted-wood edge class (narrow band), then rectified to a flat leaf
I = load(os.path.join(KIT, 'archive-door/frames/f031.jpg')); H, W = I.shape[:2]
dm = json.load(open(os.path.join(KIT, 'archive-door/masks.json')))['31']
cov = coverage(dm, W, H)
a, F, B = solve(I, trimap(cov, 1, 2), cov)
P = premult(F, a)
LW, LH = 130, 300
quad = (112, 0, 122, 250, 218, 271, 239, 0)   # UL, LL, LR, UR of the leaf in the frame
rect = np.stack([np.asarray(Image.fromarray(P[..., c]).transform((LW, LH), Image.QUAD, quad, Image.BICUBIC)) for c in range(4)], 2)
rect = np.clip(rect, 0, 1); rect[..., 3] = 1.0          # the rectified leaf is opaque wood; its own edge is drawn by the jamb
rect[..., :3] = np.clip(rect[..., :3], 0, 1)
# sheer curtain: a luminance key inside the window; fabric density from the curtain's own folds
g = rect[..., :3].mean(2)
lace = np.zeros((LH, LW), np.float32)
wx0, wx1, wy0, wy1 = 31, 98, 3, 104                    # the curtained window in the rectified leaf (measured on the proof)
win = g[wy0:wy1, wx0:wx1]
wn = (win - win.min()) / (win.max() - win.min() + 1e-6)
dens = np.clip(.30 + .55 * blur(wn, 1, 1), .15, .9)     # brighter (front-lit) cloth = more fabric in the way
lace[wy0:wy1, wx0:wx1] = dens
np.savez_compressed(os.path.join(C, 'door_leaf.npz'), P=rect.astype(np.float16), lace=lace.astype(np.float16), win=np.array([wx0, wy0, wx1, wy1]))
log['door_leaf.npz'] = {'size': [LW, LH], 'window': [wx0, wy0, wx1, wy1], 'lace_alpha_mean': round(float(dens.mean()), 3)}

# clouds: smoke edge class. Known sky where saturated blue, known cloud where bright and grey; solve the rest.
fs = sorted(os.listdir(os.path.join(SRC, 'cloud')))
fs = [f for f in fs if f.endswith('.jpg')]
for k, f in enumerate(fs):
    I = load(os.path.join(SRC, 'cloud', f))
    sat = I[..., 2] - I[..., :2].mean(2)
    tri = -np.ones(I.shape[:2], np.int8)
    tri[sat > .30] = 0
    tri[(sat < .06) & (I.mean(2) > .62)] = 1
    prior = np.clip((.30 - sat) / .24, 0, 1)
    a, F, B = solve(I, tri, prior, gf_r=2, gf_eps=1e-3, curve=None, f_clamp=None)
    # decontaminate: the cloud's colour may not keep the blue of the sky it was filmed against
    Fg = F.mean(2, keepdims=True); F = np.clip(Fg + .25 * (F - Fg), 0, 1)
    F[..., 2] = np.minimum(F[..., 2], F[..., :2].mean(2))
    P = premult(F, a)
    np.savez_compressed(os.path.join(C, 'cloud/c%02d.npz' % k), P=P.astype(np.float16))
log['clouds'] = {'n': len(fs)}
json.dump(log, open(os.path.join(C, 'world_log.json'), 'w'), indent=1)
print(json.dumps(log))
