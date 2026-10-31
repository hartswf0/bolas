"""SCION 35 · shared primitives: inks, the dot screen, Moving Least Squares (affine / similarity / rigid), forward splat.

Coordinates: image pixels, x right, y down. Print (source) space is 2x output scale (K = 430 px/m); output is 215 px/m.
Time base: scene frame i at 24 fps, t = i/24.
"""
import numpy as np, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # the swarm folder
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache')
SCORE_PATH = os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')

W, H, FPS, NSCENE = 1280, 720, 24, 768
S_OUT = 215.0            # output px per metre at the dog's path
K_SRC = 2 * S_OUT        # print px per metre (470)
GROUND_Y = 600.0         # dog path ground line (px)
SILL_X = 330.0           # screen x of the door plane / sill = score x 0.56


def X_of(x_score):
    return SILL_X + S_OUT * (x_score - 0.56)


# ---- inks (two-colour risograph on cream stock) --------------------------------------------------------------
PAPER = np.array([244, 236, 219], np.float32) / 255
DOGPAPER = np.array([247, 240, 224], np.float32) / 255
BLUE = np.array([38, 66, 138], np.float32) / 255       # dusk blue
ORANGE = np.array([255, 112, 52], np.float32) / 255    # warm orange


def inks(paper, cb, co):
    """multiplicative overprint: paper x (1 - c + c*ink) for each plate. cb, co: coverage arrays (H,W)."""
    out = paper[None, None, :] * (1 - cb[..., None] + cb[..., None] * BLUE[None, None, :])
    out = out * (1 - co[..., None] + co[..., None] * ORANGE[None, None, :])
    return out


# ---- the dot screen -----------------------------------------------------------------------------------------
def _spot_lut():
    g = (np.arange(256) + .5) / 256 - .5
    fu, fv = np.meshgrid(g, g)
    s = np.sort((np.cos(2 * np.pi * fu) + np.cos(2 * np.pi * fv)).ravel())
    c = np.linspace(0, 1, 257)
    idx = np.clip(((1 - c) * (s.size - 1)).astype(int), 0, s.size - 1)
    return c, s[idx]


_LUT_C, _LUT_S = _spot_lut()


def screen(tone, cell, angle_deg, ox=0.0, oy=0.0, xs=None, ys=None):
    """AM halftone: tone (coverage 0..1) -> ink coverage with round dots (cosine spot), anti-aliased.
    The screen lives in the coordinates xs, ys (default: pixel grid of tone)."""
    h, w = tone.shape
    if xs is None:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angle_deg)
    u = ((xs + ox) * np.cos(a) + (ys + oy) * np.sin(a)) / cell
    v = (-(xs + ox) * np.sin(a) + (ys + oy) * np.cos(a)) / cell
    spot = np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)
    t = np.clip(tone, 0, 1)
    s0 = np.interp(t, _LUT_C, _LUT_S)
    wdt = 2 * np.pi / cell * 1.6       # ~1 px transition
    ink = np.clip((spot - s0) / wdt + .5, 0, 1)
    ink[t <= 0.004] = 0
    ink[t >= 0.996] = 1
    return ink.astype(np.float32)


# ---- Moving Least Squares (Schaefer, McPhail, Warren 2006) ----------------------------------------------------
def mls(v, p, q, family, alpha=1.0, eps=1e-6):
    """deform points v (N,2) by handles p -> q (K,2). family: 'affine' | 'similarity' | 'rigid'.
    weights w_i = 1 / |p_i - v|^(2 alpha) (the influence falloff)."""
    v = np.asarray(v, np.float64); p = np.asarray(p, np.float64); q = np.asarray(q, np.float64)
    d2 = ((v[:, None, :] - p[None, :, :]) ** 2).sum(-1)
    w = 1.0 / (d2 ** alpha + eps)
    ws = w.sum(1, keepdims=True)
    ps = (w @ p) / ws; qs = (w @ q) / ws
    ph = p[None] - ps[:, None]; qh = q[None] - qs[:, None]
    dv = v - ps
    if family == 'affine':
        A = np.einsum('nk,nki,nkj->nij', w, ph, ph)
        B = np.einsum('nk,nki,nkj->nij', w, ph, qh)
        det = A[:, 0, 0] * A[:, 1, 1] - A[:, 0, 1] * A[:, 1, 0]
        det = np.where(np.abs(det) < 1e-9, 1e-9, det)
        Ai = np.stack([np.stack([A[:, 1, 1], -A[:, 0, 1]], -1), np.stack([-A[:, 1, 0], A[:, 0, 0]], -1)], 1) / det[:, None, None]
        M = Ai @ B
        return np.einsum('ni,nij->nj', dv, M) + qs
    mu = (w * (ph ** 2).sum(-1)).sum(1)
    a = (w * (ph[..., 0] * qh[..., 0] + ph[..., 1] * qh[..., 1])).sum(1)
    b = (w * (ph[..., 0] * qh[..., 1] - ph[..., 1] * qh[..., 0])).sum(1)
    if family == 'similarity':
        a = a / (mu + 1e-12); b = b / (mu + 1e-12)
    else:  # rigid
        n = np.sqrt(a * a + b * b) + 1e-12
        a = a / n; b = b / n
    # row vector d times [[a, b], [-b, a]]
    fx = dv[:, 0] * a - dv[:, 1] * b
    fy = dv[:, 0] * b + dv[:, 1] * a
    return np.stack([fx, fy], 1) + qs


def jac_svals(G):
    """G: (gh, gw, 2) deformed grid positions (output px) on a source grid of spacing 1 (normalised later).
    returns per-cell singular values s1 >= s2 and the determinant sign, for cells (gh-1, gw-1)."""
    dx = (G[:-1, 1:] - G[:-1, :-1] + G[1:, 1:] - G[1:, :-1]) / 2
    dy = (G[1:, :-1] - G[:-1, :-1] + G[1:, 1:] - G[:-1, 1:]) / 2
    a, c = dx[..., 0], dx[..., 1]; b, d = dy[..., 0], dy[..., 1]
    det = a * d - b * c
    fro = a * a + b * b + c * c + d * d
    disc = np.sqrt(np.maximum(fro * fro - 4 * det * det, 0))
    s1 = np.sqrt((fro + disc) / 2); s2 = np.sqrt(np.maximum((fro - disc) / 2, 0))
    return s1, s2, det


def splat(px, py, vals, h, w):
    """bilinear forward splat of samples at float positions (px, py) into an (h, w) canvas.
    vals: (N, C). returns sums (h, w, C) and weights (h, w)."""
    x0 = np.floor(px).astype(np.int64); y0 = np.floor(py).astype(np.int64)
    fx = px - x0; fy = py - y0
    C = vals.shape[1]
    acc = np.zeros((h * w, C), np.float64); wt = np.zeros(h * w, np.float64)
    for dx_, dy_, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xx = x0 + dx_; yy = y0 + dy_
        ok = (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
        idx = (yy[ok] * w + xx[ok])
        wk = ww[ok]
        wt += np.bincount(idx, wk, h * w)
        for c in range(C):
            acc[:, c] += np.bincount(idx, wk * vals[ok, c], h * w)
    return acc.reshape(h, w, C), wt.reshape(h, w)


def load_score():
    return json.load(open(SCORE_PATH))


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
