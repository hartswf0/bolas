"""SCION 31 matte library: trimaps, fractional alpha, foreground-colour estimation, decontamination, premultiplied alpha.
numpy + Pillow only (cv2 and scipy are not installed here). All images are float32 in [0,1], shape (H,W,3); alpha (H,W).

Typed primitives
  Trimap   int8 (H,W): 1 = known foreground, 0 = known background, -1 = unknown band to solve
  Matte    {alpha (H,W) fractional, F (H,W,3) estimated foreground colour, B (H,W,3) estimated background colour}
  Premult  (H,W,4): rgb already multiplied by alpha; the only form layers are resampled and composited in
"""
import numpy as np
from PIL import Image, ImageDraw


def load(path):
    return np.asarray(Image.open(path).convert('RGB'), np.float32) / 255.


def box(a, r):
    """mean over a (2r+1)^2 window, edge-clamped, via summed-area table"""
    if r <= 0:
        return a.copy()
    p = np.pad(a, [(r + 1, r), (r + 1, r)] + [(0, 0)] * (a.ndim - 2), mode='edge')
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s / (k * k)


def blur(a, r, n=3):
    for _ in range(n):
        a = box(a, r)
    return a


def dilate(m, r):
    m = m.copy()
    for _ in range(r):
        p = np.pad(m, 1, mode='edge')
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def erode(m, r):
    return ~dilate(~m, r)


def coverage(polys, W, H, ss=4):
    """anti-aliased polygon coverage (the SAM outline as a prior, not as the matte)"""
    im = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for P in polys:
        if len(P) >= 3:
            d.polygon([(x * ss, y * ss) for x, y in P], fill=255)
    return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255.


def trimap(cov, r_in, r_out):
    """Trimap designer: erode the outline for sure-foreground, dilate for sure-background; the band between is unknown.
    r_in / r_out are the edge-class widths (fur wide, painted wood narrow)."""
    b = cov > .5
    fg = erode(b, r_in)
    bg = ~dilate(b, r_out)
    t = -np.ones(cov.shape, np.int8)
    t[fg] = 1
    t[bg] = 0
    return t


def fill(I, known, radii=(1, 2, 4, 8, 16, 32, 64)):
    """normalized convolution: extend the colours of a known region into the unknown band, nearest scale first"""
    out = np.full(I.shape, np.nan, np.float32)
    k = known.astype(np.float32)
    for r in radii:
        den = blur(k, r, 2)
        num = blur(I * k[..., None], r, 2)
        v = num / np.maximum(den, 1e-6)[..., None]
        sel = np.isnan(out[..., 0]) & (den > 1e-3)
        out[sel] = v[sel]
    out[np.isnan(out)] = I[np.isnan(out)]
    return out


def guided(I, p, r, eps):
    """He et al. guided filter on a grey guide: edge-aware smoothing of the alpha against the image"""
    g = I.mean(2) if I.ndim == 3 else I
    mI, mp = box(g, r), box(p, r)
    cov = box(g * p, r) - mI * mp
    var = box(g * g, r) - mI * mI
    a = cov / (var + eps)
    b = mp - a * mI
    return box(a, r) * g + box(b, r)


def solve(I, tri, prior, gf_r=1, gf_eps=2e-4, conf_k=0.004, f_lo=.12, f_hi=.6, curve=(.06, .94), f_clamp=.15):
    """Matte solver. Colour-line projection of each unknown pixel onto the line between its local foreground and
    background colours (Knockout-style local sampling), confidence-weighted against the outline prior where F and B are
    too alike to separate, then guided-filter refinement. Returns alpha, F (decontaminated foreground), B."""
    fg, bg, un = tri == 1, tri == 0, tri == -1
    F = fill(I, fg)
    B = fill(I, bg)
    d = F - B
    d2 = (d * d).sum(2)
    a0 = ((I - B) * d).sum(2) / (d2 + 1e-5)
    conf = d2 / (d2 + conf_k)
    pr = blur(prior, 1, 2)
    a = np.clip(conf * a0 + (1 - conf) * pr, 0, 1)
    a[fg], a[bg] = 1, 0
    a = np.clip(guided(I, a, gf_r, gf_eps), 0, 1)
    if curve:
        a = np.clip((a - curve[0]) / (curve[1] - curve[0]), 0, 1)   # no unintended veil: faint haze to 0, near-solid to 1
    a[fg], a[bg] = 1, 0
    # foreground colour estimation: invert the compositing equation where alpha is large enough to trust,
    # and use the extended interior colour where it is not (decontamination: the old background never comes along)
    Fs = np.clip(B + (I - B) / np.maximum(a, .05)[..., None], 0, 1)
    if f_clamp is not None:   # a bright background speck read as fur may not carry its brightness into the edge
        Fs = np.clip(Fs, F - f_clamp, F + f_clamp)
    w = np.clip((a - f_lo) / (f_hi - f_lo), 0, 1)[..., None]
    Fe = w * Fs + (1 - w) * F
    Fe[fg] = I[fg]
    return a.astype(np.float32), Fe.astype(np.float32), B.astype(np.float32)


def premult(F, a):
    return np.dstack([F * a[..., None], a]).astype(np.float32)


def over(dst, src):
    """premultiplied over: dst, src (H,W,4) -> dst"""
    return src + dst * (1 - src[..., 3:4])


def resize_premult(P, W, H):
    """resample in premultiplied form (straight colour resampled next to alpha=0 drags the old background in)"""
    ch = [np.asarray(Image.fromarray(P[..., c]).resize((W, H), Image.BICUBIC)) for c in range(4)]
    P2 = np.stack(ch, 2).astype(np.float32)
    P2[..., 3] = np.clip(P2[..., 3], 0, 1)
    P2[..., :3] = np.clip(P2[..., :3], 0, P2[..., 3:4])
    return P2


def premult_ok(P, tol=1 / 255.):
    """the numerical invariant: premultiplied colour never exceeds its alpha"""
    return float((P[..., :3] - P[..., 3:4]).max()) <= tol
