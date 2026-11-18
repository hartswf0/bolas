"""Handmade brush and hand-lettering kit for the iconic-iteration proposals.

Everything here is drawn stroke by stroke: a brush is a chain of overlapping
dabs whose width follows a pressure curve, and every letter is a list of pen
strokes (single-stroke capitals designed for this film). Because each stroke
has an order and a length, lettering can be *written on* frame by frame.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

INK = 0
PAPER = 255


# ------------------------------------------------------------------ curves
def catmull(pts, n=12, closed=False):
    pts = [np.array(p, float) for p in pts]
    if len(pts) < 3:
        out = []
        for a, b in zip(pts, pts[1:]):
            for i in range(n):
                out.append(a + (b - a) * i / n)
        out.append(pts[-1])
        return out
    P = (pts[-1:] + pts + pts[:2]) if closed else ([pts[0]] + pts + [pts[-1]])
    out = []
    rng = range(len(pts)) if closed else range(len(pts) - 1)
    for i in rng:
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return out


def arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy - ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


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


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


# ------------------------------------------------------------------ brush
def brush(d, pts, w, rng, col=INK, taper=(0.35, 0.35), press=0.25, upto=1.0, step=None):
    """Draw a brush stroke as dabs. w: nominal width. upto: fraction of the stroke drawn (write-on)."""
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
    for i in range(m):
        t = i / max(1, n - 1)
        k = 1.0
        if taper[0] and t < taper[0]:
            k = 0.35 + 0.65 * (t / taper[0]) ** 0.6
        if taper[1] and t > 1 - taper[1]:
            k = min(k, 0.35 + 0.65 * ((1 - t) / taper[1]) ** 0.6)
        k *= 1 + press * math.sin(ph + fr * t * 6.28)
        r = max(0.5, w * k / 2)
        x, y = P[i]
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def wobble(pts, amp, rng, smooth=5):
    P = np.array(pts, float)
    noise = rng.normal(0, 1, P.shape)
    k = np.ones(smooth) / smooth
    noise[:, 0] = np.convolve(noise[:, 0], k, 'same')
    noise[:, 1] = np.convolve(noise[:, 1], k, 'same')
    return [tuple(p) for p in P + noise * amp]


def blob(d, ctrl, w, rng, fill=PAPER, line=INK, amp=0.0, outline=True, gaps=0):
    """Closed shape from control points: white fill, brush outline (optionally broken into strokes)."""
    pts = catmull(ctrl, 16, closed=True)
    if amp:
        pts = wobble(pts, amp, rng)
    d.polygon([tuple(p) for p in pts], fill=fill)
    if outline:
        pts = list(pts) + [pts[0]]
        if gaps:
            n = len(pts)
            cuts = sorted(rng.choice(range(5, n - 5), gaps, replace=False))
            prev = 0
            for c in list(cuts) + [n]:
                seg = pts[prev:c]
                if len(seg) > 2:
                    brush(d, seg, w, rng)
                prev = c + 2
        else:
            brush(d, pts, w, rng, taper=(0.08, 0.08), press=0.3)
    return pts


# ------------------------------------------------------------------ lettering
A = arc
GLYPHS = {
    'A': (0.62, [[(0, 1), (0.31, 0), (0.62, 1)], [(0.13, 0.62), (0.5, 0.62)]]),
    'B': (0.6, [[(0, 0), (0, 1)], [(0, 0), (0.38, 0), (0.52, 0.1), (0.52, 0.36), (0.38, 0.48), (0, 0.48)], [(0.38, 0.48), (0.58, 0.6), (0.58, 0.88), (0.42, 1), (0, 1)]]),
    'C': (0.6, [A(0.33, 0.5, 0.31, 0.5, 50, 310)]),
    'D': (0.62, [[(0, 0), (0, 1)], [(0, 0), (0.26, 0), (0.54, 0.18), (0.62, 0.5), (0.54, 0.82), (0.26, 1), (0, 1)]]),
    'E': (0.56, [[(0.55, 0), (0, 0), (0, 1), (0.58, 1)], [(0, 0.5), (0.42, 0.5)]]),
    'F': (0.54, [[(0.55, 0), (0, 0), (0, 1)], [(0, 0.5), (0.42, 0.5)]]),
    'G': (0.64, [A(0.33, 0.5, 0.31, 0.5, 50, 315) + [(0.62, 0.88), (0.62, 0.56), (0.36, 0.56)]]),
    'H': (0.6, [[(0, 0), (0, 1)], [(0.6, 0), (0.6, 1)], [(0, 0.5), (0.6, 0.5)]]),
    'I': (0.16, [[(0.08, 0), (0.08, 1)]]),
    'J': (0.52, [[(0.5, 0), (0.5, 0.78), (0.4, 0.97), (0.2, 1), (0.04, 0.86)]]),
    'K': (0.58, [[(0, 0), (0, 1)], [(0.55, 0), (0, 0.6)], [(0.18, 0.42), (0.6, 1)]]),
    'L': (0.52, [[(0, 0), (0, 1), (0.52, 1)]]),
    'M': (0.74, [[(0, 1), (0.04, 0), (0.37, 0.64), (0.7, 0), (0.74, 1)]]),
    'N': (0.62, [[(0, 1), (0, 0), (0.62, 1), (0.62, 0)]]),
    'O': (0.66, [A(0.33, 0.5, 0.33, 0.5, 100, 470, 32)]),
    'P': (0.56, [[(0, 1), (0, 0), (0.38, 0), (0.56, 0.12), (0.56, 0.38), (0.38, 0.5), (0, 0.5)]]),
    'Q': (0.68, [A(0.33, 0.5, 0.33, 0.5, 100, 470, 32), [(0.38, 0.7), (0.68, 1.06)]]),
    'R': (0.6, [[(0, 1), (0, 0), (0.38, 0), (0.56, 0.12), (0.56, 0.38), (0.38, 0.5), (0, 0.5)], [(0.24, 0.5), (0.6, 1)]]),
    'S': (0.58, [[(0.56, 0.12), (0.42, 0), (0.16, 0), (0.02, 0.14), (0.05, 0.36), (0.3, 0.5), (0.56, 0.64), (0.58, 0.86), (0.42, 1), (0.14, 1), (0, 0.88)]]),
    'T': (0.62, [[(0, 0), (0.62, 0)], [(0.31, 0), (0.31, 1)]]),
    'U': (0.6, [[(0, 0), (0, 0.75), (0.12, 0.97), (0.3, 1), (0.48, 0.97), (0.6, 0.75), (0.6, 0)]]),
    'V': (0.62, [[(0, 0), (0.31, 1), (0.62, 0)]]),
    'W': (0.8, [[(0, 0), (0.18, 1), (0.4, 0.3), (0.62, 1), (0.8, 0)]]),
    'X': (0.6, [[(0, 0), (0.6, 1)], [(0.6, 0), (0, 1)]]),
    'Y': (0.6, [[(0, 0), (0.3, 0.5), (0.6, 0)], [(0.3, 0.5), (0.3, 1)]]),
    'Z': (0.6, [[(0, 0), (0.58, 0), (0, 1), (0.6, 1)]]),
    '.': (0.16, [[(0.07, 0.94), (0.08, 0.97)]]),
    ',': (0.16, [[(0.09, 0.9), (0.03, 1.12)]]),
    "'": (0.14, [[(0.07, 0), (0.04, 0.26)]]),
    '?': (0.54, [[(0.02, 0.2), (0.12, 0.03), (0.3, 0), (0.48, 0.08), (0.52, 0.28), (0.3, 0.47), (0.28, 0.7)], [(0.28, 0.94), (0.29, 0.97)]]),
    '!': (0.16, [[(0.08, 0), (0.08, 0.7)], [(0.08, 0.94), (0.09, 0.97)]]),
    '-': (0.38, [[(0.04, 0.55), (0.34, 0.55)]]),
    '0': (0.54, [A(0.27, 0.5, 0.27, 0.5, 100, 470, 32)]),
    '1': (0.3, [[(0.04, 0.2), (0.2, 0), (0.2, 1)]]),
    '2': (0.56, [[(0.03, 0.2), (0.15, 0.03), (0.32, 0), (0.5, 0.1), (0.52, 0.3), (0.3, 0.6), (0, 1), (0.56, 1)]]),
    '3': (0.56, [[(0.03, 0.1), (0.2, 0), (0.42, 0.03), (0.5, 0.2), (0.42, 0.42), (0.22, 0.48)], [(0.22, 0.48), (0.48, 0.58), (0.54, 0.8), (0.4, 0.98), (0.18, 1), (0, 0.9)]]),
    '4': (0.6, [[(0.42, 1), (0.42, 0), (0, 0.7), (0.6, 0.7)]]),
    '5': (0.56, [[(0.52, 0), (0.08, 0), (0.04, 0.45), (0.3, 0.4), (0.5, 0.52), (0.55, 0.75), (0.42, 0.97), (0.2, 1), (0, 0.9)]]),
    '6': (0.56, [[(0.48, 0.05), (0.3, 0), (0.1, 0.15), (0.02, 0.5), (0.06, 0.85), (0.25, 1), (0.46, 0.95), (0.55, 0.75), (0.48, 0.55), (0.28, 0.48), (0.05, 0.6)]]),
    '7': (0.56, [[(0, 0), (0.56, 0), (0.2, 1)]]),
    '8': (0.56, [A(0.28, 0.24, 0.22, 0.24, 270, 630, 24), A(0.28, 0.73, 0.27, 0.27, 90, 450, 24)]),
    '9': (0.56, [[(0.5, 0.45), (0.3, 0.52), (0.08, 0.42), (0.04, 0.2), (0.2, 0.02), (0.42, 0.02), (0.54, 0.2), (0.52, 0.6), (0.4, 0.92), (0.2, 1), (0.04, 0.92)]]),
    ':': (0.16, [[(0.08, 0.34), (0.09, 0.37)], [(0.08, 0.94), (0.09, 0.97)]]),
    '/': (0.4, [[(0.4, -0.05), (0, 1.05)]]),
    '(': (0.26, [A(0.26, 0.5, 0.22, 0.56, 120, 240, 12)]),
    ')': (0.26, [A(0.0, 0.5, 0.22, 0.56, 60, -60, 12)]),
    ' ': (0.34, []),
}


def layout(lines, size, rng, track=0.16, lead=1.42):
    """Return list of strokes (absolute coords around origin 0,0 = top-left) plus bbox (w,h).
    Each letter gets its own slight hand jitter: rotation, scale, baseline."""
    strokes = []
    maxw = 0
    y = 0
    for line in lines:
        x = 0
        for ch in line.upper():
            gw, gs = GLYPHS.get(ch, GLYPHS[' '])
            sc = size * rng.uniform(0.94, 1.06)
            rot = rng.normal(0, 0.035)
            dy = rng.normal(0, 0.03) * size
            ca, sa = math.cos(rot), math.sin(rot)
            for s in gs:
                pts = []
                for (u, v) in s:
                    u2, v2 = u * sc * 0.92, v * sc
                    u2, v2 = u2 * ca - (v2 - sc / 2) * sa, u2 * sa + (v2 - sc / 2) * ca + sc / 2
                    pts.append((x + u2, y + v2 + dy))
                pts = catmull(pts, 4) if len(pts) > 3 else pts
                pts = wobble(pts, size * 0.012, rng, 3) if len(pts) > 4 else pts
                strokes.append(pts)
            x += gw * sc * 0.92 + track * size
        maxw = max(maxw, x - track * size)
        y += size * lead
    return strokes, (maxw, y - size * (lead - 1))


def letter(d, strokes, ox, oy, w, rng_seed, upto=1.0, col=INK):
    """Write strokes; upto in [0,1] is the fraction of total pen travel already written."""
    rng = np.random.default_rng(rng_seed)
    lens = [max(1e-3, length(s)) for s in strokes]
    tot = sum(lens)
    budget = tot * upto
    for s, L in zip(strokes, lens):
        if budget <= 0:
            break
        f = min(1.0, budget / L)
        budget -= L
        brush(d, [(x + ox, y + oy) for x, y in s], w, rng, col=col, taper=(0.15, 0.2), press=0.18, upto=f)


def balloon_shape(cx, cy, rw, rh, rng, tail=None, n=10):
    """Irregular hand balloon as control points; tail is (tx,ty) tip; returns polygon pts."""
    ctrl = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.normal(0, 0.05)
        k = rng.uniform(0.96, 1.05)
        ctrl.append((cx + rw * k * math.cos(a), cy + rh * k * math.sin(a)))
    pts = catmull(ctrl, 14, closed=True)
    if tail:
        tx, ty = tail
        # find base points on outline nearest the tail direction
        ang = math.atan2((ty - cy) / rh, (tx - cx) / rw)
        P = np.array(pts)
        angs = np.arctan2((P[:, 1] - cy) / rh, (P[:, 0] - cx) / rw)
        i0 = int(np.argmin(np.abs(np.angle(np.exp(1j * (angs - ang + 0.16))))))
        i1 = int(np.argmin(np.abs(np.angle(np.exp(1j * (angs - ang - 0.16))))))
        if i1 < i0:
            i0, i1 = i1, i0
        # insert tail between i0 and i1 (short side)
        if i1 - i0 < len(pts) / 2:
            pts = pts[:i0 + 1] + [np.array((tx, ty))] + pts[i1:]
        else:
            pts = pts[i0:i1 + 1] + [np.array((tx, ty))]
    return [tuple(p) for p in pts]


def balloon(d, text_lines, cx, cy, size, rng_seed, tail=None, line_w=None, upto=1.0, letter_w=None, pad=(0.9, 0.85), fill=PAPER, outline=True):
    rng = np.random.default_rng(rng_seed)
    strokes, (tw, th) = layout(text_lines, size, rng)
    rw = tw / 2 + size * pad[0] * 1.3
    rh = th / 2 + size * pad[1] * 1.3
    rw, rh = rw * 1.08, rh * 1.12
    pts = balloon_shape(cx, cy, rw, rh, rng, tail)
    d.polygon(pts, fill=fill)
    if outline:
        brush(d, pts + [pts[0]], line_w or size * 0.16, rng, taper=(0.05, 0.05), press=0.25)
    letter(d, strokes, cx - tw / 2, cy - th / 2, letter_w or size * 0.15, rng_seed + 1, upto=upto)
    return (cx - rw, cy - rh, cx + rw, cy + rh)
