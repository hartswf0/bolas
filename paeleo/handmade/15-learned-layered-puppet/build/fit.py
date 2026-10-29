"""Deformation-model researcher + differentiable-rendering engineer: fit the layered template to all 50 archive frames.
Loss = soft-silhouette render loss against the SAM mask at two blur scales (+ the agent keypoints where they exist,
linearly interpolated keys with a weaker weight elsewhere) + pose priors + a temporal prior to the previous frame.
Gradients are finite differences of the soft renderer (scipy least_squares, trust-region reflective): the render loss is
differentiable, the derivatives are numerical, not autodiff. Output cache/fits.json: pose, IoU and flags per frame."""
import json, os, sys, time
import numpy as np
from scipy import ndimage, optimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puppet import (Template, PARTS, POINTS, neutral_pose, transforms, render, load_kit, CACHE)
from template import poly_mask

tpl = Template()
masks, keys = load_kit()
SC = 0.25; HH, WW = 72, 96
FREE = [('g', 'tx'), ('g', 'ty'), ('g', 's'), ('g', 'rot'), ('torso', 'fx'),
        ('head', 'rot'), ('head', 'fx'), ('head', 'fy'), ('tail', 'rot'), ('tail', 'fx')]
for l in ['ff', 'fn', 'hf', 'hn']:
    FREE += [(l + '_up', 'rot'), (l + '_up', 'fy'), (l + '_lo', 'rot'), (l + '_lo', 'fy')]
LO = {'tx': -50, 'ty': -50, 's': 0.6, 'fx': 0.15, 'fy': 0.5}
HI = {'tx': 450, 'ty': 350, 's': 1.6, 'fx': 1.3, 'fy': 1.4}
ROTB = {'g': 0.6, 'head': 1.3, 'tail': 1.7}


def bounds():
    lo, hi = [], []
    for p, k in FREE:
        if k == 'rot':
            b = ROTB.get(p, 1.0 if p.endswith('_up') else 1.3)
            lo.append(-b); hi.append(b)
        else:
            lo.append(LO[k]); hi.append(HI[k])
    return np.array(lo), np.array(hi)


def pack(pose):
    return np.array([pose[p][k] for p, k in FREE], float)


def unpack(x, mirror):
    pose = neutral_pose(); pose['g']['mirror'] = mirror
    for (p, k), v in zip(FREE, x):
        pose[p][k] = float(v)
    return pose


def frame_mask(i):
    m = poly_mask(masks[str(i)])
    lab, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    return m


def interp_keys():
    ann = sorted(int(k) for k in keys)
    out = {}
    names = ['nose', 'neck', 'chest', 'tail', 'f1', 'f2', 'h1', 'h2']
    for i in range(50):
        if i in ann:
            out[i] = ({n: keys[str(i)][n] for n in names}, 1.0)
            continue
        a = max([j for j in ann if j < i], default=None); b = min([j for j in ann if j > i], default=None)
        if a is None or b is None or b - a > 6:
            out[i] = (None, 0); continue
        w = (i - a) / (b - a)
        out[i] = ({n: list((1 - w) * np.array(keys[str(a)][n]) + w * np.array(keys[str(b)][n])) for n in names}, 0.4)
    return out


KEYS = interp_keys()


def residuals(x, ctx):
    pose = unpack(x, ctx['mirror'])
    _, A = render(tpl, pose, HH, WW, scale_out=SC, alpha_only=True)
    r = [(ndimage.gaussian_filter(A, 4) - ctx['mb4']).ravel() * 1.0, (ndimage.gaussian_filter(A, 1.5) - ctx['mb3']).ravel() * 1.4, (A - ctx['mb']).ravel() * 2.0]
    kp, kw = ctx['keys']
    if kp is not None and kw > 0:
        M = transforms(pose)
        for n, xy in kp.items():
            part, txy = POINTS[n]
            p = (M[part] @ np.r_[txy, 1])[:2]
            r.append((p - np.array(xy)) / 7.0 * kw * ctx['kscale'])
    pr = []
    for (p, k), v in zip(FREE, x):
        if k == 'fy':
            pr.append((v - 1) / 0.25)
        if k == 'rot' and p.endswith('_lo'):
            pr.append(v / 0.7)
        if k == 'rot' and p.endswith('_up'):
            pr.append(v / 0.9)
    pr.append((pose['head']['fx'] - pose['torso']['fx']) / 0.6)
    r.append(np.array(pr) * 0.5)
    if ctx['prev'] is not None:
        d = (x - ctx['prev']) / ctx['tscale']
        r.append(d * 0.15)
    return np.concatenate(r)


def tscale():
    t = []
    for p, k in FREE:
        t.append({'tx': 15, 'ty': 15, 's': 0.1}.get(k, 0.35 if k == 'rot' else 0.2))
    return np.array(t)


def mirrored_init(x):
    """the same pose seen mirrored about the torso centre (the dog has turned through the camera)"""
    y = x.copy()
    for j, (p, k) in enumerate(FREE):
        if k == 'rot':
            y[j] = x[j]  # rotations are expressed in the dog frame; the global mirror flips them on screen
    return y


def fit_frame(i, x0, mirror, prev, kscale=1.0, nfev=60):
    m = frame_mask(i)
    mb = ndimage.zoom(m.astype(np.float32), SC, order=1)
    ctx = {'mirror': mirror, 'mb': mb, 'mb3': ndimage.gaussian_filter(mb, 1.5), 'mb4': ndimage.gaussian_filter(mb, 4), 'keys': KEYS[i], 'prev': prev,
           'tscale': tscale(), 'kscale': kscale}
    lo, hi = bounds()
    x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)
    res = optimize.least_squares(residuals, x0, bounds=(lo, hi), args=(ctx,), method='trf', diff_step=1e-3,
                                 x_scale=tscale(), max_nfev=nfev)
    pose = unpack(res.x, mirror)
    _, A = render(tpl, pose, HH, WW, scale_out=SC, alpha_only=True)
    inter = ((A > .5) & (mb > .5)).sum(); uni = ((A > .5) | (mb > .5)).sum()
    return res.x, float(inter / max(uni, 1)), float(res.cost), m.sum()


def merge():
    areas = [frame_mask(i).sum() for i in range(50)]
    med = np.array([np.median(areas[max(0, i - 4):i + 5]) for i in range(50)])
    bad = [i for i in range(50) if areas[i] > 1.45 * med[i] or areas[i] < 0.6 * med[i]]
    out = {'free': FREE, 'frames': {}, 'mask_area': [int(a) for a in areas], 'mask_suspect': bad}
    for i in range(50):
        f = json.load(open(os.path.join(CACHE, 'fit_parts', '%02d.json' % i)))
        f['mask_suspect'] = i in bad
        out['frames'][i] = f
    json.dump(out, open(os.path.join(CACHE, 'fits.json'), 'w'), indent=0)


if __name__ == '__main__':
    # usage: fit.py start end   (end exclusive; a descending range runs backward), or fit.py merge
    if sys.argv[1] == 'merge':
        merge(); sys.exit()
    a, b = int(sys.argv[1]), int(sys.argv[2])
    order = list(range(a, b)) if b > a else list(range(a, b, -1))
    os.makedirs(os.path.join(CACHE, 'fit_parts'), exist_ok=True)
    t0 = time.time()
    areas = [frame_mask(i).sum() for i in range(50)]
    med = np.array([np.median(areas[max(0, i - 4):i + 5]) for i in range(50)])
    bad = [i for i in range(50) if areas[i] > 1.45 * med[i] or areas[i] < 0.6 * med[i]]
    x = None; prev = None; mirror = 1
    for n, i in enumerate(order):
        m = frame_mask(i)
        if x is None:
            x = pack(neutral_pose()); ys, xs = np.nonzero(m); x[0] = xs.mean(); x[1] = ys.mean() - 10
            cands = [(x, 1), (x, -1)]
        else:
            cands = [(x, mirror)] + ([(x, -mirror)] if 24 <= i <= 42 else [])
            if i >= 17:
                # multi-start: tail hanging down / short, head lowered, in both mirror states
                j_tr, j_tf, j_hr = FREE.index(('tail', 'rot')), FREE.index(('tail', 'fx')), FREE.index(('head', 'rot'))
                for mi in (1, -1):
                    for hr in (0.0, -0.9):
                        y = x.copy(); y[j_tr] = 1.3; y[j_tf] = 0.45; y[j_hr] = hr
                        cands.append((y, mi))
        best = None
        for xi, mi in cands:
            xr, iou, cost, _ = fit_frame(i, xi, mi, prev if (prev is not None and mi == mirror) else None, nfev=120 if n == 0 else 50)
            if best is None or cost < best[2]:
                best = (xr, iou, cost, mi)
        x, iou, cost, mirror = best
        prev = x.copy()
        json.dump({'x': list(map(float, x)), 'mirror': mirror, 'iou': round(iou, 4), 'cost': round(cost, 2),
                   'key_weight': KEYS[i][1], 'mask_suspect': i in bad}, open(os.path.join(CACHE, 'fit_parts', '%02d.json' % i), 'w'))
        print(i, 'mirror', mirror, 'iou %.3f cost %.1f' % (iou, cost), 'suspect' if i in bad else '', '%.0fs' % (time.time() - t0), flush=True)
