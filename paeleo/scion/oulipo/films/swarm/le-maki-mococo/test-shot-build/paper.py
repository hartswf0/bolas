"""Handmade cut-paper rendering: scissor-wobble outlines, paper fibre, lit cut edges, small cast shadows.

Everything is built here from code (no photographs, no tracing). Work canvas is 2x film size.
Deterministic: every piece is generated from a fixed seed, so a library drawing has the same bytes on every use.
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

S = 2                      # supersample factor
CW, CH = 960 * S, 540 * S  # work canvas
LIGHT = np.array([-0.62, -0.78])  # light from front-left / above (image coords, y down); "front" = viewer


def catmull(pts, closed=True, step=2.0):
    """Smooth closed path through control points, resampled every `step` px (film px)."""
    P = [np.array(p, float) for p in pts]
    n = len(P)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        seg = np.linalg.norm(p2 - p1)
        k = max(2, int(seg / step))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def scissor(path, seed, amp=0.75, snip=6.5):
    """Scissor-wobble: low-frequency normal offset, then straight facets every ~`snip` px like real snips."""
    rs = np.random.RandomState(seed)
    d = np.diff(np.vstack([path, path[:1]]), axis=0)
    L = np.r_[0, np.cumsum(np.linalg.norm(d, axis=1))][:-1]
    tang = np.roll(path, -1, 0) - np.roll(path, 1, 0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([tang[:, 1], -tang[:, 0]], 1)
    off = np.zeros(len(path))
    for lam, a in ((38, 1.0), (17, 0.55), (7, 0.25)):
        ph = rs.uniform(0, 2 * np.pi)
        off += a * np.sin(L / lam + ph + rs.uniform(-.3, .3) * np.sin(L / (lam * 3.1)))
    p = path + nrm * (off * amp)[:, None]
    # facet: keep every k-th point (snip length jitters)
    keep, acc, nxt = [], 0.0, snip
    for i in range(len(p)):
        if i == 0 or L[i] >= nxt:
            keep.append(p[i])
            nxt = L[i] + snip * rs.uniform(0.6, 1.4)
    return np.array(keep)


def mask_of(poly, size=(CW, CH)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([(float(x) * S, float(y) * S) for x, y in poly], fill=255)
    return np.asarray(m, np.float32) / 255.0


_fibre = {}


def fibre_field(seed, size=(CW, CH)):
    """Paper fibre: many short, slightly curved strands, light and dark, plus fine tooth. Returns ~N(0,1)-ish field."""
    if seed in _fibre:
        return _fibre[seed]
    rs = np.random.RandomState(seed)
    w, h = size
    img = Image.new("L", size, 128)
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 140)):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        a = rs.uniform(0, np.pi)
        ln = rs.uniform(3, 11)
        c = int(128 + rs.choice([-1, 1]) * rs.uniform(8, 22))
        bend = rs.uniform(-0.25, 0.25)
        pts = []
        for k in range(5):
            t = k / 4 - 0.5
            aa = a + bend * t
            pts.append((x + math.cos(aa) * ln * t, y + math.sin(aa) * ln * t))
        d.line(pts, fill=c, width=1)
    f = np.asarray(img, np.float32) - 128
    f = cv2.GaussianBlur(f, (0, 0), 0.7)
    tooth = cv2.GaussianBlur(rs.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.2)
    f = f / (f.std() + 1e-6) * 0.8 + tooth / (tooth.std() + 1e-6) * 0.45
    _fibre[seed] = f
    return f


def piece(poly, base, seed, shade=None, hi=None, fibre=0.035, rim=0.16, model=0.10, extra=None, size=(CW, CH)):
    """Render one cut-paper piece as float RGBA (H,W,4) on the 2x canvas.

    base/shade/hi: RGB of the paper; model: broad relief shading; rim: lit/unlit cut edge strength.
    extra(rgb, alpha) -> rgb lets a piece add its own modelling (gradients, gloss)."""
    a = mask_of(poly, size)
    base = np.array(base, np.float32)
    shade = np.array(shade if shade is not None else base * 0.82, np.float32)
    hi = np.array(hi if hi is not None else np.minimum(base * 1.12, 255), np.float32)
    # broad relief from a blurred mask (paper is slightly domed by the glue)
    big = cv2.GaussianBlur(a, (0, 0), 22 * S)
    gy, gx = np.gradient(big)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    facing = (-(gx * LIGHT[0] + gy * LIGHT[1]) / nrm) * np.clip(nrm * 60, 0, 1)  # +1 toward light
    s = np.clip(facing * model * 6, -1, 1)
    rgb = base[None, None] + np.where(s[..., None] > 0, (hi - base)[None, None] * s[..., None], (base - shade)[None, None] * s[..., None])
    # lit cut edge: thin band along the outline
    sm = cv2.GaussianBlur(a, (0, 0), 1.6 * S)
    ey, ex = np.gradient(sm)
    en = np.sqrt(ex * ex + ey * ey)
    edge = np.clip(en * 3.2 * S, 0, 1) * (a > 0.02)
    lit = -(ex * LIGHT[0] + ey * LIGHT[1]) / (en + 1e-6)
    rgb = rgb + (edge * lit * rim * 255)[..., None] * np.where(lit[..., None] > 0, 0.55, 0.9)
    # paper fibre
    if fibre:
        rgb = rgb * (1 + fibre * fibre_field(seed % 3)[..., None])
    if extra is not None:
        rgb = extra(rgb, a)
    return np.dstack([np.clip(rgb, 0, 255), a])


def over(dst, src, alpha=1.0):
    """Alpha-composite float RGBA src over float RGB(A) dst in place (dst RGB)."""
    a = src[..., 3:4] * alpha
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    return dst


def shadow(dst, alpha_mask, dx=2.5, dy=3.5, blur=3.0, strength=0.28, clip=None):
    """Small soft cast shadow of a piece onto whatever is below (multiplicative darkening)."""
    M = np.float32([[1, 0, dx * S], [0, 1, dy * S]])
    sh = cv2.warpAffine(alpha_mask, M, (alpha_mask.shape[1], alpha_mask.shape[0]))
    sh = cv2.GaussianBlur(sh, (0, 0), blur * S) * strength
    if clip is not None:
        sh = sh * clip
    dst[..., :3] *= (1 - sh[..., None])
    return dst


def rotate_rgba(img, angle_deg, pivot):
    """Rigid rotation of a float RGBA layer about pivot (film px). Positive = clockwise on screen."""
    M = cv2.getRotationMatrix2D((pivot[0] * S, pivot[1] * S), -angle_deg, 1.0)
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))


def rot_pts(pts, angle_deg, pivot):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in pts]
