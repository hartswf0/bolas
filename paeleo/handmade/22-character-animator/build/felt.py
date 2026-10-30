"""SCION 22 · the material: cut felt.  Every piece (puppet layer or set piece) is a felt cut-out: a fibre texture made
here (noise + thousands of short random fibres), a fuzzy cut edge, a soft drop shadow onto whatever is beneath it (the
layers are physically stacked), and a running stitch inset from the edge on the larger pieces."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import CACHE

TILE = 1024
_fib = {}


def fibre_tile(seed=22):
    path = os.path.join(CACHE, 'fibre_%d.npy' % seed)
    if os.path.exists(path):
        return np.load(path)
    rng = np.random.default_rng(seed)
    img = Image.new('L', (TILE, TILE), 128)
    d = ImageDraw.Draw(img)
    for _ in range(90000):
        x, y = rng.uniform(0, TILE, 2)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(3, 11)
        v = int(np.clip(128 + rng.normal(0, 34), 40, 220))
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=v, width=1)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    f = np.asarray(img, np.float32) / 128.0
    low = np.asarray(Image.fromarray((rng.normal(128, 40, (TILE // 32, TILE // 32))).clip(0, 255).astype(np.uint8)).resize((TILE, TILE), Image.BICUBIC), np.float32) / 128.0
    f = 1.0 + (f - 1.0) * 0.45 + (low - 1.0) * 0.10
    np.save(path, f.astype(np.float32))
    return f


def fibre(scale):
    k = round(max(0.5, min(1.2, scale)) * 10) / 10
    if k not in _fib:
        base = fibre_tile()
        n = int(TILE * k)
        im = Image.fromarray(((base - 0.5) * 255 / 1.0).clip(0, 255).astype(np.uint8)).resize((n, n), Image.BILINEAR)
        _fib[k] = np.asarray(im, np.float32) / 255.0 + 0.5
    return _fib[k]


def crop_tile(tile, x0, y0, w, h, ox, oy):
    n = tile.shape[0]
    ys = (np.arange(y0, y0 + h) + int(oy)) % n
    xs = (np.arange(x0, x0 + w) + int(ox)) % n
    return tile[np.ix_(ys, xs)]


def signed_area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def inset(P, d):
    a = signed_area(P)
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    t /= (np.linalg.norm(t, axis=1)[:, None] + 1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1) * (1 if a > 0 else -1)
    return P + nrm * d


class Layer:
    """an RGBA (premultiplied) felt layer plus a shadow accumulator for whatever lies below it."""

    def __init__(self, w, h, base=None):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.float32) if base is None else base.astype(np.float32).copy()
        self.a = np.zeros((h, w), np.float32) if base is None else np.ones((h, w), np.float32)
        self.under_shadow = np.zeros((h, w), np.float32)
        self.masks = {}

    def piece(self, pts, col, zoom=1.0, stitch=False, shadow=True, tint=None, tile_off=(0, 0), alpha=1.0, record=None, fuzz=1.0,
              shadow_k=0.42, stitch_col=None, tex=True, solid=False):
        P = np.asarray(pts, float)
        if len(P) < 3:
            return
        pad = int(8 * zoom) + 4
        x0 = int(math.floor(P[:, 0].min())) - pad; x1 = int(math.ceil(P[:, 0].max())) + pad
        y0 = int(math.floor(P[:, 1].min())) - pad; y1 = int(math.ceil(P[:, 1].max())) + pad
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(self.w, x1), min(self.h, y1)
        if X1 <= X0 or Y1 <= Y0:
            return
        bw, bh = x1 - x0, y1 - y0
        im = Image.new('L', (bw * 2, bh * 2), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * 2, (y - y0) * 2) for x, y in P], fill=255)
        mimg = im.resize((bw, bh), Image.BOX)
        m = np.asarray(mimg, np.float32) / 255.0
        sl = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
        tile = fibre(zoom)
        fib = crop_tile(tile, X0, Y0, X1 - X0, Y1 - Y0, tile_off[0], tile_off[1])
        mm = m[sl]
        if fuzz > 0:
            edge = 4 * mm * (1 - mm)
            mm = np.clip(mm + (fib - 1.0) * 2.2 * edge * fuzz, 0, 1)
        mm = mm * alpha
        R = (slice(Y0, Y1), slice(X0, X1))
        if shadow:
            off = (max(1, int(round(2.2 * zoom))), max(1, int(round(3.0 * zoom))))
            sim = Image.new('L', (bw, bh), 0)
            sim.paste(mimg, off)
            sim = sim.filter(ImageFilter.GaussianBlur(2.2 * zoom + 0.5))
            sm = np.asarray(sim, np.float32)[sl] / 255.0 * shadow_k * alpha
            self.rgb[R] *= (1 - sm)[..., None]
            self.under_shadow[R] = np.maximum(self.under_shadow[R], sm * (1 - self.a[R]))
        c = np.asarray(col, np.float32) / 255.0
        if tex and not solid:
            t = c[None, None, :] * fib[..., None]
        else:
            t = np.broadcast_to(c, (Y1 - Y0, X1 - X0, 3))
        if tint is not None:
            t = t * (tint[R] if tint.ndim == 3 else tint)
        self.rgb[R] = self.rgb[R] * (1 - mm[..., None]) + t * mm[..., None]
        self.a[R] = self.a[R] + mm * (1 - self.a[R])
        if record is not None:
            g = self.masks.setdefault(record, np.zeros((self.h, self.w), np.float32))
            g[R] = np.maximum(g[R], mm)
        if stitch and min(bw, bh) > 18:
            Q = inset(P, 3.2 * zoom)
            Q = np.vstack([Q, Q[:1]])
            seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
            s = np.concatenate([[0], np.cumsum(seg)])
            dash, gap = 4.5 * zoom, 3.5 * zoom
            sim = Image.new('L', (bw * 2, bh * 2), 0)
            dr = ImageDraw.Draw(sim)
            pos = 0.0
            while pos < s[-1]:
                a0, a1 = pos, min(pos + dash, s[-1])
                xa, ya = np.interp(a0, s, Q[:, 0]), np.interp(a0, s, Q[:, 1])
                xb, yb = np.interp(a1, s, Q[:, 0]), np.interp(a1, s, Q[:, 1])
                dr.line([((xa - x0) * 2, (ya - y0) * 2), ((xb - x0) * 2, (yb - y0) * 2)], fill=255, width=max(2, int(2.6 * zoom)))
                pos += dash + gap
            st = np.asarray(sim.resize((bw, bh), Image.BOX), np.float32)[sl] / 255.0 * 0.85 * mm
            sc = np.asarray(stitch_col if stitch_col is not None else tuple(min(255, int(v * 0.55 + 250 * 0.45)) for v in col), np.float32) / 255.0
            stc = sc[None, None, :] * (tint[R] if (tint is not None and tint.ndim == 3) else (tint if tint is not None else 1.0))
            self.rgb[R] = self.rgb[R] * (1 - st[..., None]) + stc * st[..., None]

    def over(self, bg):
        out = bg * (1 - self.under_shadow)[..., None]
        return out * (1 - self.a)[..., None] + self.rgb
