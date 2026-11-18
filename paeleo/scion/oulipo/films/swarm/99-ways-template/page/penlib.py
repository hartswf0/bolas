"""Shared tools for the 99-ways-template TEST SHOT (E5, forgetting).

Only decoded pixels are read from the foraged files (PIL / OpenCV); nothing in them is executed.
Everything here is either FORAGED (photographs, the 1934 sheet) or HANDMADE (pen lettering from a
glyph-stroke table authored below, hand-ruled borders, cut-paper balloons, hook, tag).
"""
import math
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

BUILD = Path(__file__).resolve().parent
SWARM = BUILD.parent
ROOT = SWARM.parents[2]                       # .../oulipo
SRC = ROOT / "films" / "sources" / "99-ways-template"
MEDIA = SRC / "page-cartoonist"
PIECES = MEDIA / "pieces"
TEST = SRC / "test-shot"

INK = np.array([18, 17, 16], np.float32)
BALLOON = np.array([248, 246, 240], np.float32)
PAPER_CUT = np.array([247, 246, 242], np.float32)   # white scissor margin of photo pieces

PAGE_W, PAGE_H = 2550, 3300
# page geometry (tiers 2 and 3 are what the test shot needs; tier 1 is the page unit's)
PANELS = {
    "P4": (150, 1180, 710, 2120),
    "P5": (770, 1180, 1740, 2120),
    "P6": (1800, 1180, 2400, 2120),
    "P7": (150, 2190, 1150, 3200),
    "P8": (1210, 2190, 2400, 3200),
}


# ------------------------------------------------------------------ levels (one curve per source)
def levels(a, lo, hi, gamma=1.0):
    a = np.clip((a.astype(np.float32) - lo) / (hi - lo), 0, 1) ** gamma
    return a * 255.0


ROTH_LEVELS = (30, 186, 0.88)   # Rothstein 1937, one curve for every crop of it
KEY_LEVELS = (22, 212, 0.95)    # ANRC 1922 key plate


# ------------------------------------------------------------------ the 1934 sheet as page ground
def sheet(w=PAGE_W, h=PAGE_H):
    im = Image.open(SRC / "loc" / "blank.jpg").convert("RGB").transpose(Image.ROTATE_90)
    W0, H0 = im.size
    box = (int(W0 * 0.10), int(H0 * 0.11), int(W0 * 0.90), int(H0 * 0.89))  # interior, no tape
    im = im.crop(box).resize((w, h), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    g = a.mean(axis=2, keepdims=True)
    # one levels lift: raw (213,197,163) -> warm off-white ~(239,236,229); fibre kept as relative tone
    g = (g - g.mean()) * 1.6
    warm = np.array([239, 236, 229], np.float32)
    return np.clip(warm + g, 0, 255)


# ------------------------------------------------------------------ handmade pen lettering
def _L(*pts):
    return ("L", pts)


def _E(cx, cy, rx, ry, a0, a1):
    return ("E", (cx, cy, rx, ry, a0, a1))


def _D(x, y):
    return ("D", (x, y))


# glyph-stroke table: authored in page/glyphs.json (HANDMADE pen alphabet)
import json as _json
GLYPHS = {k: (v[0], [tuple(st) for st in v[1]]) for k, v in _json.load(open(Path(__file__).resolve().parent / "glyphs.json"))["glyphs"].items()}


def _stroke_points(st):
    kind, d = st
    if kind == "L":
        p = np.array(d, np.float32)
    elif kind == "E":
        cx, cy, rx, ry, a0, a1 = d
        n = max(12, int(abs(a1 - a0) / 6))
        a = np.radians(np.linspace(a0, a1, n))
        p = np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], 1).astype(np.float32)
    else:
        x, y = d
        p = np.array([(x, y + .035), (x, y - .02)], np.float32)
    return p


def _densify(p, step):
    out = [p[0]]
    for a, b in zip(p[:-1], p[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(1, n + 1):
            out.append(a + (b - a) * k / n)
    return np.array(out)


def letter_lines(lines, cap, seed, sup=3, weight=0.13):
    """Render lines of hand lettering. Returns (mask uint8, line boxes). Single tapered pen strokes."""
    rnd = random.Random(seed)
    lh = cap * 1.42
    widths = []
    for ln in lines:
        w = sum(GLYPHS[c][0] * cap + cap * .1 for c in ln) - cap * .1
        widths.append(w)
    W = int(max(widths) + cap * 1.2)
    H = int(lh * len(lines) + cap * 0.8)
    m = np.zeros((H * sup, W * sup), np.uint8)
    pen = cap * weight
    for li, ln in enumerate(lines):
        x = (W - widths[li]) / 2
        base = cap * 1.15 + li * lh + rnd.uniform(-.02, .02) * cap
        for c in ln:
            adv, strokes = GLYPHS[c]
            dy = rnd.uniform(-.035, .035) * cap
            rot = math.radians(rnd.uniform(-2.5, 2.5))
            sc = rnd.uniform(.97, 1.03)
            for st in strokes:
                p = _stroke_points(st) * sc
                # rotate about the glyph's base centre
                c0 = np.array([adv / 2, 0.4])
                q = p - c0
                q = np.stack([q[:, 0] * math.cos(rot) - q[:, 1] * math.sin(rot),
                              q[:, 0] * math.sin(rot) + q[:, 1] * math.cos(rot)], 1) + c0
                pts = np.stack([x + q[:, 0] * cap, base + dy - q[:, 1] * cap], 1)
                pts = _densify(pts, 1.0)
                n = len(pts)
                ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
                pr = rnd.uniform(.9, 1.1)
                for k, pt in enumerate(pts):
                    t = k / max(1, n - 1)
                    taper = (min(1.0, 5 * t, 5 * (1 - t)) ** .5) * .45 + .55 if st[0] != "D" else 1.25
                    trem = .5 * math.sin(k * .21 + ph1) + .3 * math.sin(k * .53 + ph2)
                    r = pen * .5 * taper * pr * (1 + .06 * math.sin(k * .09 + ph2))
                    cx, cy = (pt[0] + trem * .5) * sup, (pt[1] + trem * .5) * sup
                    cv2.circle(m, (int(cx), int(cy)), max(1, int(r * sup)), 255, -1, cv2.LINE_AA)
            x += adv * cap + cap * .1
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA)
    return m


# ------------------------------------------------------------------ hand-ruled brush lines
def brush_line(mask, pts, w, seed, tremor=0.9):
    rnd = random.Random(seed)
    pts = _densify(np.array(pts, np.float32), 3.0)
    n = len(pts)
    ph = rnd.uniform(0, 6.28)
    d = pts[-1] - pts[0]
    nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    for k in range(n - 1):
        t = k / max(1, n - 2)
        off = tremor * (math.sin(k * .035 + ph) + .5 * math.sin(k * .11 + ph * 2))
        ww = w * (0.85 + 0.15 * math.sin(k * .05 + ph)) * (min(1, 12 * t, 12 * (1 - t)) ** .3 * .3 + .7)
        a = pts[k] + nrm * off
        b = pts[k + 1] + nrm * off
        cv2.line(mask, (int(a[0] * 4), int(a[1] * 4)), (int(b[0] * 4), int(b[1] * 4)), 255,
                 max(1, int(round(ww))), cv2.LINE_AA, shift=2)


def border_mask(shape, boxes, w=9, seed=900):
    m = np.zeros(shape, np.uint8)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        j = lambda: random.Random(seed + i).uniform(-2, 2)
        sides = [((x0 - 4, y0), (x1 + 4, y0 + 1)), ((x1, y0 - 4), (x1 - 1, y1 + 4)),
                 ((x1 + 4, y1), (x0 - 4, y1 - 1)), ((x0, y1 + 4), (x0 + 1, y0 - 4))]
        for k, (a, b) in enumerate(sides):
            brush_line(m, [a, b], w, seed + 10 * i + k)
    return m


def ink_onto(base, mask, color=INK, alpha=1.0):
    a = (mask.astype(np.float32) / 255.0 * alpha)[..., None]
    base *= (1 - a)
    base += color * a
    return base


# ------------------------------------------------------------------ cut-paper pieces
def scissor(alpha_bin, r):
    """White scissor margin: dilate, then straight scissor facets (approxPolyDP)."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    d = cv2.dilate(alpha_bin, k)
    cs, _ = cv2.findContours(d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(d)
    for c in cs:
        if cv2.contourArea(c) > 30:
            cv2.fillPoly(out, [cv2.approxPolyDP(c, 2.2, True)], 255, cv2.LINE_AA)
    return out


def shadow_onto(base, paper_mask, off=6, blur=4, opacity=0.35, lift=0.0):
    off = int(round(off + lift))
    sh = np.zeros_like(paper_mask)
    h, w = sh.shape
    sh[off:, off:] = paper_mask[:h - off, :w - off]
    sh = cv2.GaussianBlur(sh, (0, 0), blur + lift * 0.5).astype(np.float32) / 255.0 * opacity
    base *= (1 - sh[..., None])
    return base


def place(canvas, gray, alpha, M, margin=8, shadow=True, paper=PAPER_CUT, lift=0.0, shade=1.0):
    """Lay one cut photographic piece onto canvas (float RGB). M: 3x3 piece->canvas."""
    h, w = canvas.shape[:2]
    g = cv2.warpPerspective(gray.astype(np.float32), M, (w, h), flags=cv2.INTER_CUBIC, borderValue=0)
    a = cv2.warpPerspective(alpha, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    ab = (a > 127).astype(np.uint8) * 255
    if margin:
        pm = scissor(ab, margin)
        if shadow:
            shadow_onto(canvas, pm, lift=lift)
        pa = pm.astype(np.float32)[..., None] / 255
        canvas[:] = canvas * (1 - pa) + paper * pa
    elif shadow:
        shadow_onto(canvas, ab, lift=lift)
    af = a.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - af) + (np.clip(g * shade, 0, 255))[..., None] * af
    return canvas


def T(tx=0, ty=0):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], np.float64)


def S(sx, sy=None):
    sy = sx if sy is None else sy
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], np.float64)


def R(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]], np.float64)


def about(p, Mx):
    return T(p[0], p[1]) @ Mx @ T(-p[0], -p[1])


def apply(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return v[:2] / v[2]


# ------------------------------------------------------------------ cut-paper balloon
def balloon_piece(lines, cap, tail_tip, seed, center=(0, 0), tail_w=0.32, bend=0.10):
    """Return (rgb float, alpha paper mask, ink mask, origin) in its own canvas; tail tip relative to centre."""
    rnd = random.Random(seed)
    let = letter_lines(lines, cap, seed + 1)
    th, tw = let.shape
    rx = tw * 0.5 * 1.18 + cap * 0.35
    ry = th * 0.5 * 1.10 + cap * 0.30
    tx, ty = tail_tip
    pad = int(max(abs(tx), abs(ty), rx, ry) + 40)
    Wc, Hc = int(2 * pad), int(2 * pad)
    cx, cy = pad, pad
    ang = np.linspace(0, 2 * np.pi, 400)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    rr = 1 + .018 * np.sin(ang * 3 + ph[0]) + .01 * np.sin(ang * 5 + ph[1]) + .006 * np.sin(ang * 9 + ph[2])
    ell = np.stack([cx + rx * rr * np.cos(ang), cy + ry * rr * np.sin(ang)], 1)
    a0 = math.atan2(ty / ry, tx / rx)
    b1 = np.array([cx + rx * .86 * math.cos(a0 - tail_w), cy + ry * .86 * math.sin(a0 - tail_w)])
    b2 = np.array([cx + rx * .86 * math.cos(a0 + tail_w), cy + ry * .86 * math.sin(a0 + tail_w)])
    tip = np.array([cx + tx, cy + ty])
    mid = (b1 + b2) / 2
    perp = np.array([-(tip - mid)[1], (tip - mid)[0]]) * bend
    tail = []
    for t in np.linspace(0, 1, 30):
        tail.append((1 - t) ** 2 * b1 + 2 * (1 - t) * t * (mid + perp) + t ** 2 * tip)
    for t in np.linspace(0, 1, 30):
        tail.append((1 - t) ** 2 * tip + 2 * (1 - t) * t * (mid + perp * .6) + t ** 2 * b2)
    shape = np.zeros((Hc, Wc), np.uint8)
    cv2.fillPoly(shape, [np.int32(ell * 4)], 255, cv2.LINE_AA, shift=2)
    cv2.fillPoly(shape, [np.int32(np.array(tail + [mid]) * 4)], 255, cv2.LINE_AA, shift=2)
    inkm = np.zeros_like(shape)
    cs, _ = cv2.findContours((shape > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len)[:, 0, :].astype(np.float32)
    c = np.vstack([c, c[:1]])
    # inked contour as one pen line with gentle pressure
    for k in range(len(c) - 1):
        w = 5.2 + 1.2 * math.sin(k * .02 + ph[0])
        cv2.line(inkm, (int(c[k][0] * 4), int(c[k][1] * 4)), (int(c[k + 1][0] * 4), int(c[k + 1][1] * 4)),
                 255, int(round(w)), cv2.LINE_AA, shift=2)
    ly, lx = int(cy - th / 2 + cap * .02), int(cx - tw / 2)
    inkm[ly:ly + th, lx:lx + tw] = np.maximum(inkm[ly:ly + th, lx:lx + tw], let)
    paper = scissor((shape > 127).astype(np.uint8) * 255, 7)
    return dict(paper=paper, ink=inkm, center=(cx, cy))


def lay_balloon(canvas, b, at, dy=0.0, lift=0.0, clip=None):
    """Lay balloon b with its centre at canvas point `at` (+dy drop offset); lift raises its shadow."""
    h, w = canvas.shape[:2]
    cx, cy = b["center"]
    ox, oy = int(round(at[0] - cx)), int(round(at[1] - cy + dy))
    def put(m):
        out = np.zeros((h, w), np.uint8)
        Hc, Wc = m.shape
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(h, oy + Hc), min(w, ox + Wc)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = m[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    pm, im = put(b["paper"]), put(b["ink"])
    shadow_onto(canvas, pm, lift=lift)
    pa = pm.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - pa) + BALLOON * pa
    ink_onto(canvas, im)
    return canvas
