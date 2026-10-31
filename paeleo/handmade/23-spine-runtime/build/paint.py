"""SCION 23 · gouache painting in code: flat-banded shading, cool shadows and warm lights, dry-brush strokes, paper
grain and a slight warm outline. Used to paint the atlas regions (dog, person) and the set."""
import math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from common import CE, SE

EX = np.array([1.0, 0, 0]); EY = np.array([0, CE, SE]); EV = np.array([0, -SE, CE])
LIGHT = np.array([-0.42, 0.72, 0.55]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
OUTLINE = np.array([46, 28, 22]) / 255.0


def raycast(ells, X, Y):
    """ells: list of dict(c=world centre (x,y,d), ax=3x3 rows = unit axes (world), r=(3,), id=int)
    X, Y: skeleton-plane metre grids. Returns mask, normal(cam: right, up, toward viewer), hit world point, id."""
    n = X.size
    O = X.reshape(-1, 1) * EX + Y.reshape(-1, 1) * EY - 5.0 * EV   # origin far in front of the plane
    Dv = EV
    best = np.full(n, np.inf); nrm = np.zeros((n, 3)); idx = np.full(n, -1); hit = np.zeros((n, 3))
    for e in ells:
        A, r, c = np.asarray(e['ax']), np.asarray(e['r']), np.asarray(e['c'])
        o = ((O - c) @ A.T) / r
        dv = (A @ Dv) / r
        a = dv @ dv; b = 2 * (o @ dv); cc = (o * o).sum(1) - 1
        disc = b * b - 4 * a * cc
        ok = disc > 0
        t = np.where(ok, (-b - np.sqrt(np.maximum(disc, 0))) / (2 * a), np.inf)
        sel = ok & (t < best)
        if not sel.any(): continue
        best[sel] = t[sel]
        q = o[sel] + t[sel, None] * dv
        nl = q / r
        nw = nl @ A
        nw /= np.linalg.norm(nw, axis=1, keepdims=True)
        nrm[sel] = nw; idx[sel] = e['id']; hit[sel] = O[sel] + t[sel, None] * Dv
    mask = np.isfinite(best)
    ncam = np.stack([nrm @ EX, nrm @ EY, -(nrm @ EV)], 1)
    return mask.reshape(X.shape), ncam.reshape(X.shape + (3,)), hit.reshape(X.shape + (3,)), idx.reshape(X.shape)


def bands(I, edges=(0.3, 0.55, 0.78), soft=0.05):
    out = np.zeros_like(I) + 0.52
    vals = (0.52, 0.72, 0.88, 1.0)
    for k, e in enumerate(edges):
        s = np.clip((I - e) / soft + 0.5, 0, 1)
        out = out + (vals[k + 1] - vals[k]) * s
    return out


def light_for(angle_deg):
    """the key light expressed in a region painted along a bone that points at angle_deg on screen"""
    a = -math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([LIGHT[0] * c - LIGHT[1] * s, LIGHT[0] * s + LIGHT[1] * c, LIGHT[2]])


def vec_for(angle_deg, v):
    a = -math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]])


def shade(ncam, albedo, rim=0.0, light=None, up_axis=None):
    """gouache: banded key light (upper left front), cool violet shadows, warm lights"""
    Lv = LIGHT if light is None else light
    lam = ncam @ Lv
    I = np.clip(0.5 * lam + 0.5, 0, 1) ** 1.1
    q = bands(I)
    cool = np.array([0.66, 0.64, 0.84]); warm = np.array([1.06, 1.0, 0.9])
    tint = cool + (warm - cool) * np.clip((q - 0.52) / 0.48, 0, 1)[..., None]
    col = albedo * q[..., None] * tint
    up = np.clip(ncam[..., 1] if up_axis is None else ncam @ up_axis, 0, 1)[..., None]
    col = col + 0.05 * up * np.array([0.55, 0.6, 0.8])  # a little sky on the tops
    if rim:
        edge = np.clip(1 - ncam[..., 2], 0, 1) ** 3
        col = col + rim * edge[..., None] * np.array([1.0, 0.75, 0.45])
    return np.clip(col, 0, 1)


def value_noise(h, w, cell, rng):
    gh, gw = h // cell + 3, w // cell + 3
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(im, np.float32)[:h, :w] / 255.0


def strokes(rgb, mask, rng, angle=0.0, n_per_kpx=2.2, length=(10, 30), width=(2, 5), jitter=0.5, amount=0.22,
            flow=None):
    """dry-brush strokes: short lines along `angle` (radians, or a flow(x,y) function), lighter and darker than the
    paint underneath, clipped to the mask."""
    h, w = mask.shape
    area = mask.sum()
    n = int(area / 1000 * n_per_kpx)
    if n == 0: return rgb
    ys, xs = np.nonzero(mask)
    pick = rng.integers(0, len(xs), n)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in pick:
        x, y = xs[k], ys[k]
        a = (flow(x, y) if flow else angle) + rng.normal(0, jitter)
        L = rng.uniform(*length)
        c = rgb[y, x] * rng.choice([0.84, 0.9, 1.1, 1.18])
        c = tuple(int(v) for v in np.clip(c * 255, 0, 255)) + (int(255 * amount * rng.uniform(0.6, 1.2)),)
        d.line([x - L / 2 * math.cos(a), y - L / 2 * math.sin(a), x + L / 2 * math.cos(a), y + L / 2 * math.sin(a)],
               fill=c, width=int(rng.uniform(*width)))
    la = np.asarray(lay, np.float32) / 255
    al = la[..., 3:4] * mask[..., None]
    return rgb * (1 - al) + la[..., :3] * al


def finish(rgb, alpha, rng, angle=0.0, flow=None, outline=4, stroke_len=(10, 30), stroke_w=(2, 5), amount=0.22,
           grain=0.05, out_alpha=0.85, density=2.2, outline_w=None):
    """brush strokes + wash + grain + outline. rgb float HxWx3, alpha float HxW (supersampled)."""
    h, w = alpha.shape
    m = alpha > 0.5
    rgb = strokes(rgb, m, rng, angle=angle, flow=flow, length=stroke_len, width=stroke_w, amount=amount,
                  n_per_kpx=density)
    wash = value_noise(h, w, 24, rng) * 0.6 + value_noise(h, w, 7, rng) * 0.4
    rgb = rgb * (0.93 + 0.12 * wash[..., None])
    rgb = rgb * (1 + grain * (rng.random((h, w, 1)) - 0.5))
    if outline:
        a8 = Image.fromarray((alpha * 255).astype(np.uint8))
        dil = np.asarray(a8.filter(ImageFilter.MaxFilter(2 * outline + 1)), np.float32) / 255
        ero = np.asarray(a8.filter(ImageFilter.MinFilter(2 * (outline // 2) + 1)), np.float32) / 255
        ring = np.clip(alpha - ero, 0, 1)   # an inner contour band
        brk = value_noise(h, w, 18, rng)
        ring = ring * np.clip(0.55 + 0.9 * brk, 0, 1) * out_alpha
        if outline_w is not None: ring = ring * outline_w
        rgb = rgb * (1 - ring[..., None]) + OUTLINE * ring[..., None]
        alpha = np.maximum(alpha, 0)
    return np.clip(rgb, 0, 1), alpha


def downsample(rgb, alpha, f=2):
    """premultiplied box downsample for antialiasing"""
    h, w = alpha.shape
    h2, w2 = h // f * f, w // f * f
    pm = rgb[:h2, :w2] * alpha[:h2, :w2, None]
    pm = pm.reshape(h2 // f, f, w2 // f, f, 3).mean((1, 3))
    a = alpha[:h2, :w2].reshape(h2 // f, f, w2 // f, f).mean((1, 3))
    c = np.where(a[..., None] > 1e-4, pm / np.maximum(a[..., None], 1e-4), 0)
    return c, a


def to_image(rgb, alpha):
    arr = np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(alpha, 0, 1)[..., None] * 255]).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def capsule_field(L, r0, r1, ppm, pad=6, bulge=0.0):
    """a tapered capsule along +x from 0 to L (metres). Returns grid (X, Y metres), alpha, cam normal.
    Region pixel (0,0) is at (-r0 - pad/ppm, +rmax + pad/ppm)."""
    rmax = max(r0, r1) * (1 + bulge)
    x0, x1 = -r0 - pad / ppm, L + r1 + pad / ppm
    y0, y1 = -rmax - pad / ppm, rmax + pad / ppm
    w = int(math.ceil((x1 - x0) * ppm)); h = int(math.ceil((y1 - y0) * ppm))
    X = x0 + (np.arange(w) + 0.5) / ppm
    Y = y1 - (np.arange(h) + 0.5) / ppm
    X, Y = np.meshgrid(X, Y)
    t = np.clip(X / max(L, 1e-6), 0, 1)
    r = r0 + (r1 - r0) * t
    r = r * (1 + bulge * np.sin(np.pi * t))
    # distance to the tapered segment (approx.) -> round caps
    dx = np.where(X < 0, X, np.where(X > L, X - L, 0))
    rr = np.where(X < 0, r0, np.where(X > L, r1, r))
    d = np.sqrt(dx * dx + Y * Y)
    alpha = np.clip((rr - d) * ppm + 0.5, 0, 1)
    v = np.clip(Y / np.maximum(rr, 1e-6), -1, 1)
    u = np.clip(dx / np.maximum(rr, 1e-6), -1, 1)
    nz = np.sqrt(np.clip(1 - v * v - u * u, 0, 1))
    ncam = np.stack([u, v, nz], -1)
    return (X, Y), alpha, ncam, (x0, y1, w, h)
