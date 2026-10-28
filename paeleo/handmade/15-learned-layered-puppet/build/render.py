"""Render the 32 s scene (768 frames) into build/cache/frames/*.jpg and measure the dog from the render -> trace.json.
usage: python3 render.py [start end] [--mode corrected|raw] [--out dir] [--every n]"""
import json, os, sys, time
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage as ST
from stage import P, W, H
import person as PE
import controls as CT
import dogmodel as DM

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = ST.Stage()
CTRL = CT.controls()
VIG = None


def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W * 0.45) / (W * 0.75), (yy - H * 0.55) / (H * 0.8))
    return np.clip(1.08 - 0.45 * r ** 2, 0.45, 1)[..., None]


def blend_dog(c, mode):
    """render the dog; near the front view (psi ~ 90) cross-fade the two mirror solutions (visibility layer)."""
    p, info = DM.build_pose(c, mode)
    g, A, C, L, M = DM.render_dog(p, info, H, W, c, mode)
    phi = c['phi']
    if 86 < phi < 94:
        c2 = dict(c); c2['phi'] = 180 - phi if phi != 90 else 90.001
        c2['phi_h'] = 180 - c['phi_h']
        p2, info2 = DM.build_pose(c2, mode)
        g2, A2, C2, _, _ = DM.render_dog(p2, info2, H, W, c2, mode)
        w = DM.smooth((phi - 86) / 8)
        w = w if info['mirror'] > 0 else 1 - w   # weight of the other solution
        g = g * (1 - w) + g2 * w; A = A * (1 - w) + A2 * w; C = C * (1 - w) + C2 * w
    return p, info, g, A, C, L, M


def render_frame(c, mode='corrected', want=False):
    t = c['t']
    wd = CT.world(t)
    img, fan, lit = STAGE.frame(wd['door'], wd['light'])
    # person
    pp = PE.pose_at(t, wd['person'])
    pa, parm, hand = PE.draw(pp)
    if pp['X'] < 0.02:
        clipm = ndimage.grey_dilation(STAGE.om, size=(3, 3))
        pa = pa * clipm
    pcol = np.array([24, 22, 30], float)
    tex = 0.85 + 0.15 * ndimage.uniform_filter(np.random.default_rng(int(t * 24)).random((H, W)).astype(np.float32), 3)
    for a in (pa, parm):
        edge = np.clip(a - np.roll(a, 2, axis=1), 0, 1) * (0.5 + 0.5 * wd['light'])
        img = img * (1 - a[..., None]) + (pcol * tex[..., None]) * a[..., None] + edge[..., None] * np.array([160, 110, 60])
    # dog
    p, info, g, A, C, L, M = blend_dog(c, mode)
    ys, xs = np.nonzero(A > 0.5)
    X = c['X']
    near = np.exp(-max(X, 0) / 1.6) * wd['light'] * (0.25 + 0.75 * wd['door'])
    if len(xs):
        x0, x1 = xs.min(), xs.max()
        side = np.clip(1 - (np.arange(W) - x0) / max(1, x1 - x0), 0, 1)[None, :] * 0.7 + 0.3
    else:
        side = np.ones((1, W))
    gg = np.clip(g, 0, 1) ** 1.05
    amb = np.array([150, 140, 170]) * 1.0
    col = gg[..., None] * amb + (gg[..., None] * 0.6 + 0.15) * np.array([255, 165, 95]) * (near * side)[..., None] * 0.75
    # contact shadow on the floor under the body
    if len(xs):
        fy = P(X, 0, 0)[1]
        sh = np.zeros((H, W), np.float32)
        cx = 0.5 * (xs.min() + xs.max()); hw = 0.5 * (xs.max() - xs.min()) * 0.9
        yy, xx = np.ogrid[0:H, 0:W]
        sh = np.exp(-(((xx - cx) / max(hw, 10)) ** 2 + ((yy - fy - 2) / 7.0) ** 2) ** 1.5).astype(np.float32)
        img = img * (1 - 0.55 * sh[..., None])
    # unsharp the upscaled archive texture a little, then composite
    colb = ndimage.gaussian_filter(col, (1.2, 1.2, 0))
    col = np.clip(col + 0.6 * (col - colb), 0, 255)
    img = img * (1 - A[..., None]) + col * A[..., None]
    # grade: vignette + fine grain
    global VIG
    if VIG is None:
        VIG = vignette()
    img = img * VIG
    rng = np.random.default_rng(c['i'] + 1000)
    img = img + rng.normal(0, 3.2, (H, W, 1))
    img = np.clip(img, 0, 255).astype(np.uint8)
    meas = measure(c, info, A, M, L)
    if want:
        return img, meas, (g, A, C)
    return img, meas


def measure(c, info, A, M, L):
    """what the dog did, read back from the render: centroid, bbox, nose direction, layer visibility."""
    ys, xs = np.nonzero(A > 0.5)
    m = {'i': c['i'], 't': round(c['t'], 4)}
    if not len(xs):
        return m
    from puppet import POINTS
    def pt(n):
        part, xy = POINTS[n]; return (M[part] @ np.r_[xy, 1])[:2]
    nose, neck, rump, chest = pt('nose'), pt('neck'), pt('rump'), pt('chest')
    hv = nose - neck
    m.update({'cx': float(xs.mean()), 'cy': float(ys.mean()), 'top': int(ys.min()), 'bottom': int(ys.max()),
              'left': int(xs.min()), 'right': int(xs.max()), 'area': int(len(xs)),
              'nose': [round(float(nose[0]), 1), round(float(nose[1]), 1)], 'head_dir': round(float(np.degrees(np.arctan2(hv[1], hv[0]))), 1),
              'body_dir': 1 if (chest[0] < rump[0]) else -1, 'psi': round(info['psi'], 1), 'psi_h': round(info['psi_h'], 1),
              'mirror': info['mirror'], 'head_rel': info['head_rel'], 'ood': round(info['ood'], 3), 'mahal': round(info['mahal'], 2),
              'view_support': round(info['view_support'], 2), 'reach_err': round(info['reach_err'], 2),
              'head_visible': round(float(L['head'].sum()) if 'head' in L else 0.0, 0)})
    return m


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    mode = 'raw' if '--raw' in sys.argv else 'corrected'
    s0, s1 = (int(args[0]), int(args[1])) if len(args) >= 2 else (0, len(CTRL))
    step = 1
    for a in sys.argv:
        if a.startswith('--every='):
            step = int(a.split('=')[1])
    outdir = os.path.join(HERE, 'cache', 'frames' if mode == 'corrected' else 'frames_raw')
    os.makedirs(outdir, exist_ok=True)
    meas = []
    t0 = time.time()
    for i in range(s0, s1, step):
        img, m = render_frame(CTRL[i], mode)
        Image.fromarray(img).save(os.path.join(outdir, '%04d.jpg' % i), quality=92)
        meas.append(m)
        if i % 48 == 0:
            print(i, '%.1fs' % (time.time() - t0), flush=True)
    json.dump(meas, open(os.path.join(HERE, 'cache', 'meas_%s_%04d_%04d.json' % (mode, s0, s1)), 'w'))
