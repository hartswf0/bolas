"""The stage: static cut-paper planes of the shadow theatre, built once and cached as masks.

Planes (back to front) and their paper density (fraction of the lamp light they stop):
  far hills tissue 0.22 | garden trees tissue 0.42 | house facade card 0.66 | lace curtain 0.6
  black card 0.975 (porch, steps, roof, valance, bench, lantern, casing, sill, lace border).
Light-field shapes (added to the lamp light behind the screen): doorway interior, window,
radial door glow, porch light wedge, lantern glow.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from theatre import *

RNG = np.random.default_rng(1924)   # Reiniger's Prince Achmed was begun in 1923-24: a fixed seed

def canvas(): return Image.new('L', (W * SS, H * SS), 0)
def to1x(img): return np.asarray(img.reduce(SS), np.float32) / 255.0
def sp(pts): return [(float(x) * SS, float(y) * SS) for x, y in pts]          # 1x screen px -> 2x
def wp(pts): return [(X(x) * SS, Y(y) * SS) for x, y in np.asarray(pts)]       # world m -> 2x

def poly(d, pts, fill=255): d.polygon(sp(pts), fill=fill)
def circle(d, cx, cy, r, fill=255):
    d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=fill)

def leaf(cx, cy, length, width, ang):
    t = np.linspace(0, 1, 12)
    up = np.stack([t * length, np.sin(t * math.pi) * width * (1 - 0.3 * t)], 1)
    dn = np.stack([t[::-1] * length, -np.sin(t[::-1] * math.pi) * width * (1 - 0.3 * t[::-1])], 1)
    p = np.concatenate([up, dn])
    c, s = math.cos(ang), math.sin(ang)
    return p @ np.array([[c, s], [-s, c]]) + [cx, cy]

def stroke(d, pts, w0, w1=None):
    """A tapered stroke along a polyline (1x px)."""
    w1 = w0 if w1 is None else w1
    P = np.asarray(pts, float); n = len(P)
    for k in range(n - 1):
        w = w0 + (w1 - w0) * k / max(1, n - 2)
        d.line(sp([P[k], P[k + 1]]), fill=255, width=max(1, int(w * SS)))
        circle(d, P[k + 1][0], P[k + 1][1], w / 2)

def spiral(cx, cy, r0, turns, ang0, sgn=1, n=60):
    t = np.linspace(0, 1, n)
    a = ang0 + sgn * t * turns * 2 * math.pi
    r = r0 * (1 - 0.85 * t)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1)

def vine(d, start, ang, length, depth, wid, curl=0.35, leaves=True):
    """Recursive filigree vine: a curling stem with leaves and tendril spirals."""
    pts = [np.array(start, float)]; a = ang
    n = max(6, int(length / 6))
    for k in range(n):
        a += curl * (0.5 + 0.5 * math.sin(k * 0.6)) / n * 3 + RNG.normal(0, 0.04)
        pts.append(pts[-1] + 6 * np.array([math.cos(a), math.sin(a)]) * length / (n * 6))
    stroke(d, pts, wid, max(1.0, wid * 0.35))
    end = pts[-1]
    if leaves:
        for k in range(2, len(pts) - 1, 3):
            side = 1 if k % 2 else -1
            aa = math.atan2(*(pts[k + 1] - pts[k])[::-1]) + side * 0.9
            ln = 9 + 7 * RNG.random()
            poly(d, leaf(pts[k][0], pts[k][1], ln, ln * 0.36, aa))
    if depth > 0:
        for k in range(len(pts) // 3, len(pts) - 1, max(2, len(pts) // 3)):
            side = RNG.choice([-1, 1])
            vine(d, pts[k], a + side * 0.9, length * 0.5, depth - 1, wid * 0.6, -side * curl, leaves)
    else:
        stroke(d, spiral(end[0], end[1], 7, 1.2, a + math.pi / 2, 1 if curl > 0 else -1, 30), 1.4)

def tree(d, x, y, ang, length, depth, wid):
    """A procedural cut-paper tree with leaf clusters at the tips."""
    ex = x + length * math.cos(ang); ey = y + length * math.sin(ang)
    stroke(d, [(x, y), ((x + ex) / 2 + RNG.normal(0, 3), (y + ey) / 2), (ex, ey)], wid, wid * 0.7)
    if depth == 0:
        for k in range(5):
            aa = RNG.uniform(0, 2 * math.pi); ll = RNG.uniform(7, 13)
            poly(d, leaf(ex, ey, ll, ll * 0.4, aa))
        return
    for k in range(2 if depth > 3 else 3):
        da = RNG.uniform(0.25, 0.65) * (1 if k % 2 else -1) + RNG.normal(0, 0.1)
        tree(d, ex, ey, ang + da, length * RNG.uniform(0.62, 0.8), depth - 1, wid * 0.66)

ARCH_L, ARCH_R, ARCH_SPRING = -0.46, 0.46, 1.9
def arch_outline(n=40):
    """The door opening (world m): straight jambs to 1.9 m, semicircular head."""
    r = (ARCH_R - ARCH_L) / 2; cx = (ARCH_R + ARCH_L) / 2
    pts = [(ARCH_L, 0.0)]
    for a in np.linspace(math.pi, 0, n):
        pts.append((cx + r * math.cos(a), ARCH_SPRING + r * math.sin(a)))
    pts.append((ARCH_R, 0.0))
    return np.array(pts)

FACADE_R = 0.62
WINDOW = (-1.72, -0.86, 1.18, 1.86)  # x0, x1, y0, y1 (m)
LANTERN = (820.0, 92.0)
POST_X = X(4.97)
STEP_X = X(4.9) + 4

def build():
    os.makedirs(OUT, exist_ok=True)
    L = {}
    # ---- far hills (tissue)
    im = canvas(); d = ImageDraw.Draw(im)
    xs = np.linspace(440, 1280, 120)
    ys = 498 + 14 * np.sin(xs / 95.0) + 9 * np.sin(xs / 41.0 + 1.0)
    poly(d, [(440, 720)] + list(zip(xs, ys)) + [(1280, 720)])
    L['far'] = to1x(im)
    # ---- garden trees (tissue)
    im = canvas(); d = ImageDraw.Draw(im)
    tree(d, 700, 600, -math.pi / 2 - 0.05, 120, 6, 15)
    tree(d, 1262, 640, -math.pi / 2 + 0.12, 140, 6, 17)
    for bx in np.linspace(1210, 1280, 4):
        circle(d, bx, 640 + 10 * math.sin(bx), 30)
    L['mid'] = to1x(im)
    # ---- facade card with stone courses scored into it
    im = canvas(); d = ImageDraw.Draw(im)
    poly(d, [(0, 34), (X(FACADE_R), 34), (X(FACADE_R), 600), (0, 600)])
    for k, y in enumerate(np.arange(60, 566, 26)):
        d.line(sp([(0, y), (X(FACADE_R), y)]), fill=150, width=2 * SS // 2)
        off = 0 if k % 2 else 34
        for x in np.arange(off, X(FACADE_R), 68):
            d.line(sp([(x, y), (x, y + 26)]), fill=150, width=SS)
    d.polygon(wp(arch_outline()), fill=0)
    x0, x1, y0, y1 = WINDOW
    poly(d, [(X(x0), Y(y1)), (X(x1), Y(y1)), (X(x1), Y(y0)), (X(x0), Y(y0))], 0)
    L['facade'] = to1x(im)
    # ---- lace curtain in the window (tissue with cut holes)
    im = canvas(); d = ImageDraw.Draw(im)
    for side in (0, 1):
        xa = X(x0) + 6 if side == 0 else (X(x0) + X(x1)) / 2 + 4
        xb = (X(x0) + X(x1)) / 2 - 4 if side == 0 else X(x1) - 6
        pts = [(xa, Y(y1) + 4), (xb, Y(y1) + 4)]
        if side == 0: pts += [(xa + 18, Y(y0) - 4), (xa, Y(y0) - 4)]
        else: pts += [(xb, Y(y0) - 4), (xb - 18, Y(y0) - 4)]
        poly(d, pts)
        for yy in np.arange(Y(y1) + 14, Y(y0) - 8, 11):
            for xx in np.arange(xa + 6, xb - 4, 11):
                circle(d, xx + (5 if int(yy) % 2 else 0), yy, 2.6, 0)
    L['curtain'] = to1x(im)
    # ---- black card: porch, steps, roof, valance, post, bench, casing, sill, window frame, lantern, border
    im = canvas(); d = ImageDraw.Draw(im)
    # house roof with shingle scallops
    poly(d, [(0, 0), (520, 0), (520, 30), (0, 30)])
    for x in np.arange(0, 520, 22): circle(d, x + 11, 32, 11)
    # porch roof beam and lace valance
    poly(d, [(470, 64), (1280, 64), (1280, 92), (470, 92)])
    for x in np.arange(482, 1280, 30):
        d.pieslice([(x - 15) * SS, (92 - 15) * SS, (x + 15) * SS, (92 + 15) * SS], 0, 180, fill=255)
    for x in np.arange(482, 1280, 30): circle(d, x, 96, 4.5, 0)
    for x in np.arange(497, 1280, 30): circle(d, x, 78, 3.5, 0)
    # post with turned profile and filigree brackets
    prof = [(0, 7), (40, 6), (60, 9), (70, 6), (400, 6), (420, 10), (440, 6), (474, 7)]
    left = [(POST_X - w, 92 + y) for y, w in prof]; right = [(POST_X + w, 92 + y) for y, w in prof[::-1]]
    poly(d, left + right)
    for s in (-1, 1):
        stroke(d, spiral(POST_X + s * 34, 110, 26, 0.9, math.pi if s > 0 else 0, -s), 3)
        stroke(d, [(POST_X, 140), (POST_X + s * 40, 93)], 3)
    # floor band, fascia, lattice skirting, steps
    poly(d, [(0, FY), (STEP_X, FY), (STEP_X, 720), (0, 720)])
    for (xa, xb) in ((26, 236), (650, 1160)):
        for yy in np.arange(618, 704, 17):
            for xx in np.arange(xa, xb, 17):
                xo = xx + (8.5 if int((yy - 618) / 17) % 2 else 0)
                if xo < xb - 6:
                    poly(d, [(xo, yy - 6), (xo + 6, yy), (xo, yy + 6), (xo - 6, yy)], 0)
    d.line(sp([(0, 604), (STEP_X, 604)]), fill=0, width=2 * SS)
    for k in range(3):
        poly(d, [(STEP_X + k * 32, FY + k * 30), (1280, FY + k * 30), (1280, 720), (STEP_X + k * 32, 720)])
    # sill stone across the opening (contact plane, 4.5 cm)
    d.polygon(wp([(-0.55, 0.0), (-0.52, 0.045), (0.52, 0.045), (0.55, 0.0)]), fill=255)
    # door casing: architrave around the arch, keystone
    ao = arch_outline()
    for k in range(len(ao) - 1):
        if k == 0 or k == len(ao) - 2:
            continue
        d.line(wp([ao[k], ao[k + 1]]), fill=255, width=7 * SS)
    d.line(wp([(ARCH_L - 0.02, 0.0), (ARCH_L - 0.02, ARCH_SPRING)]), fill=255, width=7 * SS)
    d.line(wp([(ARCH_R + 0.02, 0.0), (ARCH_R + 0.02, ARCH_SPRING)]), fill=255, width=7 * SS)
    d.polygon(wp([(-0.07, 2.42), (0.07, 2.42), (0.05, 2.30), (-0.05, 2.30)]), fill=255)
    # window frame and mullions
    x0, x1, y0, y1 = WINDOW
    for a, b in [((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1)),
                 (((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)), ((x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2))]:
        d.line(wp([a, b]), fill=255, width=5 * SS)
    d.polygon(wp([(x0 - 0.08, y0 - 0.02), (x1 + 0.08, y0 - 0.02), (x1 + 0.05, y0 - 0.07), (x0 - 0.05, y0 - 0.07)]), fill=255)
    for k in range(5):
        xx = x0 + (x1 - x0) * (k + 0.5) / 5
        d.ellipse([(X(xx) - 5) * SS, (Y(y0 - 0.07) - 3) * SS, (X(xx) + 5) * SS, (Y(y0 - 0.07) + 7) * SS], fill=255)
    # interior lamp hanging inside the doorway
    stroke(d, [(X(0.0), Y(2.36)), (X(0.0), Y(2.08))], 2)
    poly(d, [(X(0.0) - 15, Y(2.08)), (X(0.0) + 15, Y(2.08)), (X(0.0) + 7, Y(1.98)), (X(0.0) - 7, Y(1.98))])
    # lantern on the porch beam (frame only; its glass is in the light field)
    lx, ly = LANTERN
    stroke(d, [(lx, ly), (lx, ly + 52)], 2)
    poly(d, [(lx - 13, ly + 52), (lx + 13, ly + 52), (lx + 8, ly + 44), (lx - 8, ly + 44)])
    for s in (-1, 0, 1):
        stroke(d, [(lx + s * 12, ly + 54), (lx + s * 10, ly + 90)], 2.4)
    poly(d, [(lx - 14, ly + 90), (lx + 14, ly + 90), (lx + 6, ly + 98), (lx - 6, ly + 98)])
    # foreground lace: proscenium edge and corner filigree
    band = 16
    outer = [(0, 0), (1280, 0), (1280, 720), (0, 720)]
    inner = []
    def edge(a, b, n):
        for k in range(n):
            t = (k + 0.5) / n
            p = np.array(a) + (np.array(b) - np.array(a)) * t
            inner.append(tuple(p))
    base = im
    im = canvas(); d = ImageDraw.Draw(im)
    poly(d, outer)
    ins = Image.new('L', im.size, 0); di = ImageDraw.Draw(ins)
    pts = []
    for (a, b, nrm) in [((band, band), (1280 - band, band), (0, 1)), ((1280 - band, band), (1280 - band, 720 - band), (-1, 0)),
                        ((1280 - band, 720 - band), (band, 720 - band), (0, -1)), ((band, 720 - band), (band, band), (1, 0))]:
        L_ = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L_ / 24)
        for k in range(n * 6):
            t = k / (n * 6)
            p = np.array(a) + (np.array(b) - np.array(a)) * t
            bump = 5 * abs(math.sin(math.pi * t * n))
            pts.append(tuple(p + np.array(nrm) * bump))
    di.polygon(sp(pts), fill=255)
    arr = np.asarray(im).copy(); arr[np.asarray(ins) > 0] = 0
    im = Image.fromarray(arr); d = ImageDraw.Draw(im)
    for (a, b) in [((band / 2, band / 2), (1280 - band / 2, band / 2)), ((band / 2, 720 - band / 2), (1280 - band / 2, 720 - band / 2)),
                   ((band / 2, band / 2), (band / 2, 720 - band / 2)), ((1280 - band / 2, band / 2), (1280 - band / 2, 720 - band / 2))]:
        L_ = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(1, int(L_ / 24)):
            p = np.array(a) + (np.array(b) - np.array(a)) * (k / int(L_ / 24))
            if 0 < p[1] < 560 or p[0] in (band / 2,):
                circle(d, p[0], p[1], 2.6, 0)
    # ivy over the house (top left), branch from the beam end (top right), corner spirals
    vine(d, (10, 26), 0.55, 230, 2, 4.5, 0.5)
    vine(d, (150, 30), 1.25, 150, 2, 3.5, -0.4)
    vine(d, (1272, 92), 1.9, 210, 2, 4.0, 0.45)
    vine(d, (1150, 92), 1.55, 120, 1, 3.0, -0.4)
    for (cx, cy, a0, sg) in [(40, 690, 0, 1), (1240, 690, math.pi, -1)]:
        stroke(d, spiral(cx, cy, 22, 1.4, a0, sg), 3)
    im = Image.fromarray(np.maximum(np.asarray(im), np.asarray(base)))
    L['black'] = to1x(im)
    # ---- light-field shapes
    im = canvas(); d = ImageDraw.Draw(im); d.polygon(wp(arch_outline()), fill=255); L['door'] = to1x(im)
    im = canvas(); d = ImageDraw.Draw(im)
    poly(d, [(X(x0), Y(y1)), (X(x1), Y(y1)), (X(x1), Y(y0)), (X(x0), Y(y0))]); L['window'] = to1x(im)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.polygon([(X(0.40), FY + 4), (X(0.40), Y(1.95)), (X(4.2), Y(1.05)), (X(4.4), FY + 4)], fill=255)
    L['wedge'] = np.asarray(im.filter(ImageFilter.GaussianBlur(38)), np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    L['radial'] = np.exp(-(((xx - X(0.0)) / 380.0) ** 2 + ((yy - Y(1.1)) / 300.0) ** 2))
    L['lantern'] = np.exp(-(((xx - LANTERN[0]) / 60.0) ** 2 + ((yy - LANTERN[1] - 70) / 60.0) ** 2))
    L['hot'] = 0.80 + 0.30 * np.exp(-(((xx - 660) / 720.0) ** 2 + ((yy - 330) / 430.0) ** 2))
    L['interior'] = np.exp(-(((xx - X(0.0)) / 90.0) ** 2 + ((yy - Y(2.0)) / 160.0) ** 2))
    # paper of the screen: low-frequency mottling plus fibres
    n = RNG.normal(0, 1, (H // 8 + 1, W // 8 + 1)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255 - 0.5
    f = RNG.normal(0, 1, (H, W)).astype(np.float32)
    f = np.asarray(Image.fromarray(((f * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255 - 0.5
    L['paper'] = 1.0 - 0.06 * n - 0.035 * f
    # stars
    st = np.zeros((H, W), np.float32)
    for k in range(70):
        sx_, sy_ = RNG.uniform(500, 1260), RNG.uniform(100, 330)
        st[int(sy_), int(sx_)] = RNG.uniform(0.4, 1.0)
    L['stars'] = np.asarray(Image.fromarray((st * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255.0 * 4
    np.savez_compressed(os.path.join(OUT, 'stage.npz'), **L)
    return L

def load():
    p = os.path.join(OUT, 'stage.npz')
    if not os.path.exists(p): return build()
    z = np.load(p); return {k: z[k] for k in z.files}

if __name__ == '__main__':
    L = build()
    print({k: v.shape for k, v in L.items()})
