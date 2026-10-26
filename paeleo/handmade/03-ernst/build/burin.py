"""SCION 03 Ernst · the burin: one line language for every fragment, so the seams can be concealed (or shown on purpose).

A plate is made of regions; each region carries a tone (darkness 0..1) and a line coordinate u (in line periods).  The
burin cuts a line wherever frac(u) is within darkness/2 of the line centre: the line swells in the dark and thins to
nothing in the light, as in a nineteenth-century wood engraving.  Above a darkness knee a second set (v) cross-hatches.
"""
import numpy as np

PAPER = np.array([238, 229, 208], float) / 255
INK = np.array([28, 24, 30], float) / 255


def fwidth(u):
    gy, gx = np.gradient(u)
    # line phases wrap: take the gradient modulo one period
    gx = gx - np.round(gx); gy = gy - np.round(gy)
    return np.clip(np.abs(gx) + np.abs(gy), 0.02, 0.5)


def cut(u, dark, fw=None, gamma=1.0, lo=0.04):
    """coverage (0..1) of one line system."""
    if fw is None:
        fw = fwidth(u)
    d = np.clip((dark - lo) / (1 - lo), 0, 1) ** gamma
    dist = np.abs(u - np.floor(u) - 0.5)            # 0 at the line centre, 0.5 between lines
    half = 0.5 * d
    return np.clip((half - dist) / fw + 0.5, 0, 1) * (d > 0)


def engrave(u, v, dark, knee=0.58, fw_u=None, fw_v=None, gamma=1.0):
    c1 = cut(u, dark, fw_u, gamma)
    if v is None:
        return c1
    d2 = np.clip((dark - knee) / (1 - knee), 0, 1) * 0.8
    c2 = cut(v, d2, fw_v, 1.0, lo=0.0)
    return 1 - (1 - c1) * (1 - c2)


def compose(cov, tint=None):
    """ink coverage -> RGB float image on paper; tint = optional per-pixel paper colour (H,W,3)."""
    paper = PAPER[None, None] if tint is None else tint
    return paper * (1 - cov[..., None]) + INK[None, None] * cov[..., None]


def blur(a, r):
    """box blur (separable, twice) without scipy."""
    if r <= 0:
        return a
    out = a.astype(float)
    for _ in range(2):
        for ax in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if i == ax else (0, 0) for i in range(out.ndim)], mode='edge'), axis=ax)
            if ax == 0:
                out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
            else:
                out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return out


def edge(mask, w=1.0):
    """outline of a mask (soft)."""
    m = mask.astype(float)
    b = blur(m, 1)
    e = np.clip(np.abs(m - b) * 2.6 * w, 0, 1)
    return e
