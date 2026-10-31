"""SCION 23 · the draw layer of the runtime: region attachments by inverse-affine bilinear sampling, mesh attachments
by triangle rasterisation, composited in slot order into a premultiplied RGBA canvas."""
import json, math, os
import numpy as np
from PIL import Image
from common import ACTOR, K, X0, YF, W, H

_ATLAS = None


def atlas():
    global _ATLAS
    if _ATLAS is None:
        meta = json.load(open(os.path.join(ACTOR, 'actors.atlas.json')))
        img = np.asarray(Image.open(os.path.join(ACTOR, 'actors.png')).convert('RGBA'), np.float32) / 255
        img[..., :3] *= img[..., 3:4]
        regs = {}
        for n, r in meta['regions'].items():
            x, y = r['xy']; w, h = r['size']
            regs[n] = np.ascontiguousarray(img[y:y + h, x:x + w])
        _ATLAS = regs
    return _ATLAS


def sample(img, u, v):
    """bilinear, premultiplied; u,v in pixel coordinates (pixel centres at i+0.5)"""
    h, w = img.shape[:2]
    u = u - 0.5; v = v - 0.5
    x0 = np.floor(u).astype(np.int32); y0 = np.floor(v).astype(np.int32)
    fx = (u - x0)[..., None]; fy = (v - y0)[..., None]
    out = 0
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi = x0 + dx; yi = y0 + dy
        ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        px = img[np.clip(yi, 0, h - 1), np.clip(xi, 0, w - 1)] * ok[..., None]
        out = out + px * wt
    return out


class Cam:
    """skeleton-world centimetres -> output pixels"""
    def __init__(self, zoom, cx, cy, ox=0.0, oy=0.0, out=(W, H)):
        self.z, self.cx, self.cy = zoom, cx, cy
        self.ow, self.oh = out
        s = K / 100.0 * zoom
        self.A = np.array([[s, 0.0], [0.0, -s]])
        self.b = np.array([(X0 - cx) * zoom + self.ow / 2, (YF - cy) * zoom + self.oh / 2])

    def __call__(self, p):
        return np.asarray(p) @ self.A.T + self.b


def over(canvas, layer, y0, x0):
    h, w = layer.shape[:2]
    H_, W_ = canvas.shape[:2]
    ya, xa = max(0, y0), max(0, x0); yb, xb = min(H_, y0 + h), min(W_, x0 + w)
    if ya >= yb or xa >= xb: return
    L = layer[ya - y0:yb - y0, xa - x0:xb - x0]
    C = canvas[ya:yb, xa:xb]
    C *= (1 - L[..., 3:4]); C += L


def draw_region(canvas, g, cam, img, tint=None, masks=None):
    h, w = img.shape[:2]
    # pixel -> bone local cm -> world cm -> screen
    Apix = np.array([[g['w'] / w, 0.0], [0.0, -g['h'] / h]]); bpix = np.array([g['x'] - g['w'] / 2, g['y'] + g['h'] / 2])
    M = cam.A @ g['R'] @ Apix
    bb = cam.A @ (g['R'] @ bpix + g['P']) + cam.b
    corners = np.array([[0, 0], [w, 0], [0, h], [w, h]]) @ M.T + bb
    x0, y0 = np.floor(corners.min(0)).astype(int) - 1
    x1, y1 = np.ceil(corners.max(0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, canvas.shape[1]), min(y1, canvas.shape[0])
    if x0 >= x1 or y0 >= y1: return None
    Mi = np.linalg.inv(M)
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    q = np.stack([xs + 0.5 - bb[0], ys + 0.5 - bb[1]], -1) @ Mi.T
    px = sample(img, q[..., 0], q[..., 1])
    if tint is not None: px[..., :3] *= tint
    over(canvas, px, y0, x0)
    return (y0, x0, px[..., 3])


def draw_mesh(canvas, g, cam, img, tint=None):
    h, w = img.shape[:2]
    S = cam(g['pts'])
    UV = g['uvs'] * np.array([w, h])
    x0, y0 = np.floor(S.min(0)).astype(int) - 1; x1, y1 = np.ceil(S.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, canvas.shape[1]), min(y1, canvas.shape[0])
    if x0 >= x1 or y0 >= y1: return None
    layer = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
    for t in g['tris']:
        a, b, c = S[t]
        tx0, ty0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        tx1, ty1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1
        tx0, ty0 = max(tx0, x0), max(ty0, y0); tx1, ty1 = min(tx1, x1), min(ty1, y1)
        if tx0 >= tx1 or ty0 >= ty1: continue
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-9: continue
        ys, xs = np.mgrid[ty0:ty1, tx0:tx1].astype(np.float32) + 0.5
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
        l3 = 1 - l1 - l2
        ins = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not ins.any(): continue
        ua, ub, uc = UV[t]
        u = l1 * ua[0] + l2 * ub[0] + l3 * uc[0]; v = l1 * ua[1] + l2 * ub[1] + l3 * uc[1]
        px = sample(img, u[ins], v[ins])
        sub = layer[ty0 - y0:ty1 - y0, tx0 - x0:tx1 - x0]
        cur = sub[ins]
        sub[ins] = np.where(px[:, 3:4] > cur[:, 3:4], px, cur)
    if tint is not None: layer[..., :3] *= tint
    over(canvas, layer, y0, x0)
    return (y0, x0, layer[..., 3])


def draw_actor(canvas, geo, cam, tint=None, mask=None, mask_slots=None, head_mask=None):
    regs = atlas()
    for g in geo:
        img = regs[g['path']]
        r = draw_region(canvas, g, cam, img, tint) if g['type'] == 'region' else draw_mesh(canvas, g, cam, img, tint)
        if r is None: continue
        y0, x0, a = r
        for m, want in ((mask, None), (head_mask, mask_slots)):
            if m is None: continue
            if want is not None and g['slot'] not in want: continue
            hh, ww = a.shape
            sub = m[y0:y0 + hh, x0:x0 + ww]
            sub[...] = np.maximum(sub, a[:sub.shape[0], :sub.shape[1]])
