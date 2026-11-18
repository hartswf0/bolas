"""Brush dabs, after the HANDMADE brush kit of moins-dun-quart-de-seconde-pour-vivre (plate/hand.py,
made for that work): a stroke is a chain of overlapping dabs whose width follows a pressure curve.
Copied here (same method, no foraged material) so page 07 does not depend on that work's source folder."""
import math

import numpy as np


def resample(pts, step):
    pts = [np.array(p, float) for p in pts]
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = np.linalg.norm(b - a)
        if L == 0:
            continue
        t = step - acc
        while t <= L:
            out.append(a + (b - a) * t / L)
            t += step
        acc = L - (t - step)
    if np.linalg.norm(out[-1] - pts[-1]) > 1e-6:
        out.append(pts[-1])
    return out


STATS = None   # set to a list to record (min_r, max_r, n_dabs) per stroke (page 07 thick/thin check)


def brush(d, pts, w, rng, col=0, taper=(0.35, 0.35), press=0.25, upto=1.0, step=None):
    if len(pts) < 2:
        x, y = pts[0]
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)
        return
    step = step or max(0.6, w / 5)
    P = resample(pts, step)
    n = len(P)
    m = max(1, int(round(n * upto)))
    ph = rng.uniform(0, 6.28)
    fr = rng.uniform(1.5, 3.5)
    rs = []
    for i in range(m):
        t = i / max(1, n - 1)
        k = 1.0
        if taper[0] and t < taper[0]:
            k = 0.35 + 0.65 * (t / taper[0]) ** 0.6
        if taper[1] and t > 1 - taper[1]:
            k = min(k, 0.35 + 0.65 * ((1 - t) / taper[1]) ** 0.6)
        k *= 1 + press * math.sin(ph + fr * t * 6.28)
        r = max(0.5, w * k / 2)
        rs.append(r)
        x, y = P[i]
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    if STATS is not None and rs:
        STATS.append((min(rs), max(rs), len(rs)))


def wobble(pts, amp, rng, smooth=5):
    P = np.array(pts, float)
    noise = rng.normal(0, 1, P.shape)
    k = np.ones(smooth) / smooth
    noise[:, 0] = np.convolve(noise[:, 0], k, 'same')
    noise[:, 1] = np.convolve(noise[:, 1], k, 'same')
    return [tuple(p) for p in P + noise * amp]


def shape(d, pts, w, rng, fill=255, line=0, amp=0.8, outline=True, press=0.3, taper=(0.06, 0.06)):
    """Closed shape (already dense points): fill, then a brushed contour."""
    if len(pts) < 12:
        P = list(pts) + [pts[0]]
        dense = []
        for a, b in zip(P, P[1:]):
            for t in np.linspace(0, 1, 6, endpoint=False):
                dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        pts = dense
    pts = wobble(pts, amp, rng) if amp else [tuple(p) for p in pts]
    d.polygon(pts, fill=fill)
    if outline and w > 0:
        brush(d, list(pts) + [pts[0]], w, rng, col=line, taper=taper, press=press)
    return pts
