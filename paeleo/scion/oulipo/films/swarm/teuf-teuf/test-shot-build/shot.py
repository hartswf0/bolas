"""teuf-teuf TEST SHOT: the rollers beat (film time 15.0-21.0 s).

  15.0-16.2  wide (layout A): the stone rides three bark logs; they turn and drift back at v/2
  16.2-18.8  oblique close-up (x2.2, same sim instants): the rear log is squeezed out, rolls
             0.33 s on its bark, stops with a 'tok', rocks on its facet (spring); caption 17.2 s
  18.8-21.0  wide: the carrier crouches and sets log D down in front, hands pinned to it;
             the stone waits on two logs, the pusher's hands pinned to it.

Wall: foraged photograph (Cueva de las Manos, Suzko, CC BY-SA 3.0), re-toned (wall.py).
Everything else is handmade here: cut-card puppets (FK spine, analytic two-bone IK with
pole signs, planted-foot locks), bark logs, the boulder, charcoal, scratches, the caption.
Compositing is done in luminance and printed through one sepia ramp sampled from the
reference, then kit.Film adds its print grain and encodes; kit.Mix makes the sound.

Run:  python3 shot.py            (writes ../test-shot.mp4)
      python3 shot.py --stills 15.5 16.9 19.6
"""
import math
import json
import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
import kit                                   # noqa: E402
import wall                                  # noqa: E402
import sim                                   # noqa: E402

SW, SH = 960, 540
FPS = 24
T0 = 15.0
GROUND = sim.GROUND
OUTDIR = HERE.parent
MEDIA = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/teuf-teuf/test-shot")
MEDIA.mkdir(parents=True, exist_ok=True)

LOGS, SIMF, EVENTS, A_STOP = sim.run()
CU_START, CU_END = 16.2, 18.8


# ------------------------------------------------------------------ cameras ---
class Cam:
    def __init__(self, s, ox, oy, depth):
        self.s, self.ox, self.oy = s, ox, oy
        self.depth = depth                       # oblique receding vector for log length (world px)

    def p(self, x, y):
        return ((x - self.ox) * self.s, (y - self.oy) * self.s)

    def pts(self, pts):
        return [self.p(x, y) for x, y in pts]


WIDE = Cam(0.75, 0.0, 0.0, (28.0, -19.0))
CLOSE = Cam(1.65, 318 - 480 / 1.65, 566 - 432 / 1.65, (58.0, -38.0))
PLATES = {}


def plate_for(cam):
    k = id(cam)
    if k not in PLATES:
        PLATES[k] = wall.plate(cam.s, cam.ox, cam.oy, SW, SH).astype(np.float32)
    return PLATES[k]


# ----------------------------------------------------------- mask drawing ---
SS = 2


def raster(polys, cam, ellipses=(), lines=()):
    im = Image.new("L", (SW * SS, SH * SS), 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([(x * SS, y * SS) for x, y in cam.pts(poly)], fill=255)
    for (cx, cy, rx, ry) in ellipses:
        x, y = cam.p(cx, cy)
        d.ellipse([(x - rx * cam.s) * SS, (y - ry * cam.s) * SS, (x + rx * cam.s) * SS, (y + ry * cam.s) * SS], fill=255)
    for pts, w in lines:
        d.line([(x * SS, y * SS) for x, y in cam.pts(pts)], fill=255, width=max(1, int(w * cam.s * SS)))
    return np.asarray(im.resize((SW, SH), Image.BILINEAR)).astype(np.float32) / 255


def strokes(segs, cam, shape=(SH, SW)):
    """segs: list of (pts, width_world, value 0..1). returns alpha layer"""
    im = Image.new("L", (SW * SS, SH * SS), 0)
    d = ImageDraw.Draw(im)
    for pts, w, val in segs:
        d.line([(x * SS, y * SS) for x, y in cam.pts(pts)], fill=int(255 * val), width=max(1, int(round(w * cam.s * SS))))
    return np.asarray(im.resize((SW, SH), Image.BILINEAR)).astype(np.float32) / 255


def halo(canvas, mask, cam, reach, density, seed, dark=0.06, haze=0.30):
    """blown pigment: a soft haze and a spray of dots fading out from the edge."""
    rng = np.random.default_rng(seed)
    m8 = (mask > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 3) / cam.s       # world px
    p = np.exp(-dist / (reach * 0.42)) * (dist > 0.5) * (dist < reach * 2.4)
    dots = (rng.random(mask.shape) < p * density * 0.5).astype(np.float32)
    dots = cv2.GaussianBlur(dots, (0, 0), 0.5 + 0.35 * cam.s) * 2.0
    hz = cv2.GaussianBlur(mask, (0, 0), reach * 0.33 * cam.s) * haze
    a = np.clip(dots + hz, 0, 0.92) * (1 - mask)
    return canvas * (1 - a) + dark * a


def gap(canvas, mask, cam, width=1.4, light=0.72):
    """a hair of pale card edge where a new silhouette lies over an existing dark one
    (Reiniger readability: objects never merge into one blob)."""
    k = max(1, int(round(width * cam.s)))
    dil = cv2.dilate((mask > 0.4).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    ring = np.clip(dil.astype(np.float32) - mask, 0, 1)
    ring = cv2.GaussianBlur(ring, (0, 0), 0.6)
    dark = canvas < 0.35
    return np.where(dark & (ring > 0.05), canvas * (1 - ring) + light * ring, canvas)


def ink(canvas, mask, value, streak=None):
    if streak is not None:
        val = value + streak
    else:
        val = value
    return canvas * (1 - mask) + val * mask


# ------------------------------------------------------- cut-card pieces ---
def ragged_limb(p0, p1, w0, w1, seed, n=22, rag=0.06, brush=True):
    """tapered cut-card limb, edges broken like a dry brush, stable per piece."""
    rng = np.random.default_rng(seed)
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) + 1e-6
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    jitL = rng.normal(0, rag, n + 1); jitR = rng.normal(0, rag, n + 1)
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = w0 + (w1 - w0) * t
        if brush:
            w *= (1.0 - 0.35 * max(0, t - 0.8) / 0.2)         # brush lifts off at the far end
        bulge = 1 + 0.10 * math.sin(math.pi * t)
        cx, cy = x0 + ux * L * t, y0 + uy * L * t
        left.append((cx + nx * w * bulge * (1 + jitL[i]), cy + ny * w * bulge * (1 + jitL[i])))
        right.append((cx - nx * w * bulge * (1 + jitR[i]), cy - ny * w * bulge * (1 + jitR[i])))
    cap1 = [(x1 + ux * w1 * 0.7 * math.cos(a) + nx * w1 * 0.8 * math.sin(a), y1 + uy * w1 * 0.7 * math.cos(a) + ny * w1 * 0.8 * math.sin(a))
            for a in np.linspace(math.pi / 2, -math.pi / 2, 5)]
    cap0 = [(x0 - ux * w0 * 0.8 * math.cos(a) - nx * w0 * math.sin(a), y0 - uy * w0 * 0.8 * math.cos(a) - ny * w0 * math.sin(a))
            for a in np.linspace(math.pi / 2, -math.pi / 2, 5)]
    return left + cap1 + right[::-1] + cap0


def dry_streaks(p0, p1, w0, w1, seed, n=5, val=0.24):
    """grey dry-brush streaks running along the limb (inside the black)."""
    rng = np.random.default_rng(seed + 999)
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) + 1e-6
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    segs = []
    for k in range(n):
        off = rng.uniform(-0.65, 0.65)
        t = rng.uniform(0.0, 0.3)
        while t < 0.95:
            ln = rng.uniform(0.15, 0.5)
            t2 = min(0.95, t + ln)
            pts = []
            for tt in np.linspace(t, t2, 4):
                w = w0 + (w1 - w0) * tt
                pts.append((x0 + ux * L * tt + nx * w * off, y0 + uy * L * tt + ny * w * off))
            segs.append((pts, rng.uniform(0.6, 1.3), rng.uniform(0.6, 1.0) * val))
            t = t2 + rng.uniform(0.05, 0.25)
    return segs


def ik2(p0, target, L1, L2, bend):
    """analytic two-bone IK. bend = +1/-1 pole sign. returns (joint, end, residual)."""
    x0, y0 = p0; tx, ty = target
    dx, dy = tx - x0, ty - y0
    dist = math.hypot(dx, dy)
    d = min(max(dist, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    k = (x0 + L1 * math.cos(a + bend * b), y0 + L1 * math.sin(a + bend * b))
    ang2 = math.atan2(ty - k[1], tx - k[0])
    e = (k[0] + L2 * math.cos(ang2), k[1] + L2 * math.sin(ang2))
    return k, e, math.hypot(e[0] - tx, e[1] - ty)


def head_parts(neck, ang, facing, s, seed):
    """animal-like profile head: skull, heavy brow, snout, jaw, a tuft at the back."""
    fx = facing
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):                       # u forward (facing), v up, in head frame
        x = u * fx; y = -v
        return (neck[0] + (x * ca - y * sa) * s, neck[1] + (x * sa + y * ca) * s)
    # rounded cranium, heavy brow, a long muzzle angled down (like the reference's bulls),
    # an open jaw line and a pricked ear: reads as a head facing one way in silhouette
    skull = [P(-9, 8), P(-12, 17), P(-9, 26), P(-2, 31), P(7, 32), P(13, 29), P(17, 25), P(24, 19),
             P(31, 12), P(33, 8), P(30, 5), P(23, 5), P(16, 6), P(13, 3), P(6, 0), P(-2, 1)]
    tuft = [P(-3, 28), P(-11, 39), P(-6, 37), P(1, 31)]
    eye = (P(12, 21), P(16, 20))
    return skull + [], tuft, eye


class Puppet:
    """Reiniger cut-card figure: pinned joints, joint-angle limits, replacement head profiles."""

    def __init__(self, name, s, seed):
        self.name, self.s, self.seed = name, s, seed
        self.T1, self.T2 = 50 * s, 46 * s          # lower torso, chest (FK spine)
        self.TH, self.SH = 63 * s, 61 * s          # thigh, shin
        self.UA, self.LA = 48 * s, 46 * s          # upper arm, forearm
        self.res = {}

    def build(self, hip, lean1, lean2, head_ang, feet, hands, facing=1, knee_bend=(-1, -1), elbow_bend=(1, 1),
              head_face=None):
        """lean in degrees from vertical toward `facing`. feet/hands: IK world targets.
        Returns list of pieces (poly, axis p0, p1, w0, w1, seed) back-to-front, plus extras."""
        s = self.s; f = facing
        a1 = math.radians(lean1); a2 = math.radians(lean2)
        mid = (hip[0] + f * self.T1 * math.sin(a1), hip[1] - self.T1 * math.cos(a1))
        neck = (mid[0] + f * self.T2 * math.sin(a2), mid[1] - self.T2 * math.cos(a2))
        sh = (mid[0] + f * self.T2 * 0.82 * math.sin(a2), mid[1] - self.T2 * 0.82 * math.cos(a2))
        pieces = []
        sd = self.seed
        # far limbs first (index 1), then body, then near limbs (index 0)
        legs, arms = [], []
        for i, ft in enumerate(feet):
            k, e, r = ik2(hip, ft, self.TH, self.SH, knee_bend[i] * f)
            self.res[f"foot{i}"] = r
            # joint-angle limit check (knee 0..150 deg)
            th = math.degrees(math.atan2(k[1] - hip[1], k[0] - hip[0]) - math.atan2(e[1] - k[1], e[0] - k[0]))
            legs.append([(ragged_limb(hip, k, 13 * s, 9.5 * s, sd + 10 + i), hip, k, 13 * s, 9.5 * s, sd + 10 + i),
                         (ragged_limb(k, e, 9 * s, 5.5 * s, sd + 20 + i), k, e, 9 * s, 5.5 * s, sd + 20 + i),
                         (ragged_limb((e[0] - f * 3 * s, e[1] - 2 * s), (e[0] + f * 17 * s, e[1] + 2.5 * s), 5.5 * s, 2.6 * s, sd + 30 + i),
                          e, (e[0] + f * 17 * s, e[1]), 5 * s, 3 * s, sd + 30 + i)])
        for i, h in enumerate(hands):
            k, e, r = ik2(sh, h, self.UA, self.LA, elbow_bend[i] * f)
            self.res[f"hand{i}"] = r
            dirx, diry = e[0] - k[0], e[1] - k[1]
            dl = math.hypot(dirx, diry) + 1e-6
            tip = (e[0] + dirx / dl * 9 * s, e[1] + diry / dl * 9 * s)
            arms.append([(ragged_limb(sh, k, 8.5 * s, 6.5 * s, sd + 40 + i), sh, k, 8.5 * s, 6.5 * s, sd + 40 + i),
                         (ragged_limb(k, e, 6.5 * s, 4.5 * s, sd + 50 + i), k, e, 6.5 * s, 4.5 * s, sd + 50 + i),
                         (ragged_limb(e, tip, 5.8 * s, 3.4 * s, sd + 60 + i, n=6), e, tip, 5 * s, 3.4 * s, sd + 60 + i)])
            self.res[f"elbow{i}"] = k
        torso = [(ragged_limb(hip, mid, 17 * s, 15 * s, sd + 1, brush=False), hip, mid, 17 * s, 15 * s, sd + 1),
                 (ragged_limb(mid, neck, 15.5 * s, 10 * s, sd + 2, brush=False), mid, neck, 15.5 * s, 10 * s, sd + 2),
                 (ragged_limb((hip[0] - f * 4 * s, hip[1] + 4 * s), (hip[0] + f * 3 * s, hip[1] - 14 * s), 16 * s, 14 * s, sd + 3, brush=False),
                  hip, mid, 15 * s, 14 * s, sd + 3)]
        hf = f if head_face is None else head_face
        skull, tuft, eye = head_parts(neck, math.radians(head_ang), hf, s, sd)
        head = [(skull, neck, (neck[0] + hf * 20 * s, neck[1] - 18 * s), 14 * s, 10 * s, sd + 5),
                (tuft, neck, neck, 4 * s, 3 * s, sd + 6)]
        order = legs[1] + arms[1] + torso + head + legs[0] + arms[0]
        self.joints = {"hip": hip, "mid": mid, "neck": neck, "sh": sh, "eye": eye}
        return order


def draw_puppet(canvas, cam, pieces, seed, frame_k, extra_scratch=()):
    polys = [p[0] for p in pieces]
    m = raster(polys, cam)
    canvas = gap(canvas, m, cam, width=1.6)
    canvas = halo(canvas, m, cam, reach=10, density=0.55, seed=seed * 1000 + frame_k // 2, dark=0.07, haze=0.22)
    segs = []
    for poly, p0, p1, w0, w1, sd in pieces:
        if w0 > 4:
            segs += dry_streaks(p0, p1, w0, w1, sd, n=4 if w0 < 10 else 6)
    st = strokes(segs, cam)
    inner = cv2.erode((m > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    st = st * cv2.GaussianBlur(inner, (0, 0), 0.7)
    canvas = ink(canvas, m, 0.035, streak=st)
    if extra_scratch:
        sc = strokes(list(extra_scratch), cam) * m
        canvas = canvas * (1 - sc) + 0.80 * sc
    return canvas


# ------------------------------------------------------------- the stone ---
def make_stone():
    rng = np.random.default_rng(1956)
    pts = []
    cx, cy, rx, ry = 125.0, -76.0, 127.0, 80.0
    for t in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        c, s_ = math.cos(t), math.sin(t)
        e = 2.4
        r = (abs(c) ** e + abs(s_) ** e) ** (-1 / e)
        r *= 1 + 0.035 * math.sin(3 * t + 1) + 0.025 * math.sin(7 * t + 0.4) + rng.normal(0, 0.008)
        x = cx + rx * r * c
        y = cy + ry * r * s_ * (1.0 if s_ < 0 else 1.0)
        y = min(y, 0.0)
        pts.append((x, y))
    return pts


STONE = make_stone()


def stone_back_x(y_local):
    """leftmost x of the stone outline at a given local height"""
    best = None
    P = STONE
    for i in range(len(P)):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
        if (y0 - y_local) * (y1 - y_local) <= 0 and y0 != y1:
            x = x0 + (x1 - x0) * (y_local - y0) / (y1 - y0)
            best = x if best is None else min(best, x)
    return best


def stone_xform(xb, bottom, tilt):
    c, s_ = math.cos(tilt), math.sin(tilt)
    px, py = 125.0, 0.0                       # tilt about the middle of the underside

    def T(x, y):
        x -= px; y -= py
        return (xb + px + x * c - y * s_, bottom + py + x * s_ + y * c)
    return T


def stone_streaks(T, seed=77):
    rng = np.random.default_rng(seed)
    segs = []
    for k in range(26):
        y = rng.uniform(-148, -8)
        half = math.sqrt(max(0, 1 - ((y + 76) / 82) ** 2)) * 120
        x0 = 125 - half + rng.uniform(5, 40); x1 = 125 + half - rng.uniform(5, 40)
        if x1 - x0 < 20:
            continue
        x = x0
        while x < x1:
            ln = rng.uniform(20, 70); xe = min(x1, x + ln)
            arch = rng.uniform(-4, 4)
            pts = [T(xx, y + arch * math.sin(math.pi * (xx - x0) / (x1 - x0 + 1)) + 0.03 * (xx - 125)) for xx in np.linspace(x, xe, 5)]
            segs.append((pts, rng.uniform(0.8, 2.0), rng.uniform(0.12, 0.30)))
            x = xe + rng.uniform(8, 30)
    scr = []
    # white scratched contour accents along the top (the reference's engraved light lines)
    top = [p for p in STONE if p[1] < -110]
    top.sort()
    for a, b in [(0.15, 0.42), (0.55, 0.8)]:
        i0, i1 = int(a * len(top)), int(b * len(top))
        scr.append(([T(x + 2, y + 6) for x, y in top[i0:i1]], 1.2, 0.8))
    scr.append(([T(60, -40), T(85, -52), T(118, -50)], 1.0, 0.6))
    return segs, scr


# ---------------------------------------------------------------- the logs ---
def log_geometry(L, cx, cy, theta, cam, n=72):
    phis = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rr = L.r(phis - theta)
    near = [(cx + r * math.cos(p), cy + r * math.sin(p)) for r, p in zip(rr, phis)]
    dx, dy = cam.depth
    far = [(x + dx, y + dy) for x, y in near]
    return phis, rr, near, far


def draw_log(canvas, cam, L, cx, cy, theta, seed, frame_k, length_scale=1.0):
    dx, dy = cam.depth[0] * length_scale, cam.depth[1] * length_scale
    phis = np.linspace(0, 2 * math.pi, 72, endpoint=False)
    rr = L.r(phis - theta)
    near = [(cx + r * math.cos(p), cy + r * math.sin(p)) for r, p in zip(rr, phis)]
    far = [(x + dx, y + dy) for x, y in near]
    quads = [[near[i], near[(i + 1) % 72], far[(i + 1) % 72], far[i]] for i in range(72)]
    body = raster(quads + [far], cam)
    face = raster([near], cam)
    allm = np.maximum(body, face)
    canvas = gap(canvas, allm, cam, width=1.3)
    canvas = halo(canvas, allm, cam, reach=7, density=0.45, seed=seed * 1000 + frame_k // 2, dark=0.08, haze=0.18)
    # bark: ridges running along the length, fixed to the log body so they turn with it
    rng = np.random.default_rng(seed)
    ad = math.atan2(dy, dx)
    segs = []
    for k in range(16):
        psi0 = k * 2 * math.pi / 16 + rng.normal(0, 0.12)
        psi = psi0 + theta
        vis = math.cos(psi - ad)
        if vis <= 0.05:
            continue
        r = L.r(psi0) * 0.98
        a = (cx + r * math.cos(psi), cy + r * math.sin(psi))
        u0, u1 = rng.uniform(0.05, 0.3), rng.uniform(0.6, 1.0)
        pts = [(a[0] + dx * u, a[1] + dy * u + rng.normal(0, 0.3)) for u in np.linspace(u0, u1, 5)]
        segs.append((pts, rng.uniform(0.8, 1.6), 0.18 + 0.18 * vis))
    st = strokes(segs, cam) * body * (1 - face)
    canvas = ink(canvas, body, 0.06, streak=st)
    # knots on the bark (dark eye with a pale scratched rim): they come round as it rolls
    knots = []
    for kk in range(2):
        psi0 = rng.uniform(0, 2 * math.pi); u = rng.uniform(0.35, 0.7)
        psi = psi0 + theta
        vis = math.cos(psi - ad)
        if vis > 0.15:
            r = L.r(psi0)
            kx = cx + r * math.cos(psi) * 0.93 + dx * u; ky = cy + r * math.sin(psi) * 0.93 + dy * u
            w = 4.5 * vis + 1
            ring = [(kx + w * math.cos(a) * 1.4, ky + w * math.sin(a) * 0.8) for a in np.linspace(0, 6.3, 14)]
            knots.append((ring, 1.1, 0.75))
    if knots:
        sk = strokes(knots, cam) * body * (1 - face)
        canvas = canvas * (1 - sk) + 0.62 * sk
    # end face: sawn-off end, end grain rings + a radial crack that turn with the log
    canvas = ink(canvas, face, 0.16)
    rings = []
    for fr_, val in [(0.72, 0.55), (0.42, 0.6)]:
        ring = []
        for p in np.linspace(0, 2 * math.pi, 40):
            r = L.r(p - theta) * fr_ * (1 + 0.04 * math.sin(5 * (p - theta)))
            ring.append((cx + r * math.cos(p) + 0.6 * fr_, cy + r * math.sin(p)))
        rings.append((ring, 0.9, val))
    crack = [(cx + 2 * math.cos(theta + 1.2), cy + 2 * math.sin(theta + 1.2))] + \
            [(cx + L.R * u * math.cos(theta + 0.08 * math.sin(9 * u)), cy + L.R * u * math.sin(theta + 0.08 * math.sin(9 * u))) for u in np.linspace(0.15, 0.92, 6)]
    rings.append((crack, 1.6, 0.9))
    rings.append(([(cx - 1.2, cy), (cx + 1.2, cy)], 2.2, 0.7))
    sr = strokes(rings, cam) * face
    canvas = canvas * (1 - sr) + 0.78 * sr
    # ragged bark lip round the end face
    rim = strokes([(near + [near[0]], 2.2, 1.0)], cam)
    canvas = canvas * (1 - rim) + 0.03 * rim
    return canvas


# -------------------------------------------------------------- the gait ---
def gait(hip_x_fn, t_list, rest_off, swing_trigger, swing_to, swing_dur, lift, t_freeze=None):
    """planted-foot locks: each foot stays exactly where it planted until the hip has
    carried past it by `swing_trigger`; then it swings (never both at once)."""
    feet = [hip_x_fn(t_list[0]) + rest_off[0], hip_x_fn(t_list[0]) + rest_off[1]]
    swing = [None, None]
    out = []
    plants = []
    dt = 1 / 240
    t = t_list[0]
    tl = iter(t_list)
    nxt = next(tl)
    while True:
        hx = hip_x_fn(t)
        for i in range(2):
            if swing[i] is None and (swing[1 - i] is None) and hx - feet[i] > swing_trigger and (t_freeze is None or t < t_freeze):
                swing[i] = (t, feet[i])
        pos = []
        for i in range(2):
            if swing[i] is not None:
                ts, x0 = swing[i]
                u = (t - ts) / swing_dur
                target = hip_x_fn(ts + swing_dur) + swing_to
                if u >= 1:
                    feet[i] = target; swing[i] = None
                    plants.append(round(t, 3))
                    pos.append((feet[i], 0.0, True))
                else:
                    e = u * u * (3 - 2 * u)
                    pos.append((x0 + (target - x0) * e, lift * math.sin(math.pi * u), False))
            else:
                pos.append((feet[i], 0.0, True))
        if t >= nxt - 1e-9:
            out.append(pos)
            try:
                nxt = next(tl)
            except StopIteration:
                break
        t += dt
    return out, plants


FT = [T0 + k / FPS for k in range(int(6.0 * FPS) + 1)]


def pusher_hip_x(t):
    return sim.stone_xb(t) - 132


def carrier_hip_x(t):
    if t <= 18.6:
        return 520 + 33.0 * (t - 15.0)
    return 520 + 33.0 * 3.6


P_FEET, P_PLANTS = gait(pusher_hip_x, FT, (-14, -96), 112, -12, 0.30, 12)
C_FEET, C_PLANTS = gait(carrier_hip_x, FT, (26, -34), 42, 28, 0.34, 9, t_freeze=18.6)


# ---------------------------------------------------------- springs (#41) ---
def spring(t, t_imp, amp, f, zeta):
    if t < t_imp:
        return 0.0
    w = 2 * math.pi * f
    wd = w * math.sqrt(1 - zeta * zeta)
    tt = t - t_imp
    return amp * math.exp(-zeta * w * tt) * math.sin(wd * tt)


T_REL = [e["t"] for e in EVENTS if e["kind"] == "release"][0]
T_SETDOWN = 19.7


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# -------------------------------------------------------------- the frame ---
METRICS = []


def sim_at(t):
    k = int(round((t - T0) * FPS))
    return SIMF[min(k, len(SIMF) - 1)]


def render(t, k):
    cam = CLOSE if CU_START <= t < CU_END else WIDE
    canvas = plate_for(cam).copy()
    fr = sim_at(t)
    xb = fr["xb"]
    # log state (A rests on its facet and rocks: one-sided spring after the stop)
    lstate = {}
    for name, s in fr["logs"].items():
        L = LOGS[name]
        th = s["th"]; x = s["x"]
        if name == "A" and A_STOP is not None:
            rock = sim.spring_bounce(t - A_STOP, 0.16, f=3.0, zeta=0.40)
            th += rock; x += rock * L.R
        lstate[name] = (x, L.cy(th), th, s["carried"])
    # stone rests on the highest carried log; tilt spring at the release and the stop
    tops = [LOGS[n].top(x, th) for n, (x, cy, th, c) in lstate.items() if c]
    bottom = min(tops)
    tilt = spring(t, T_REL, math.radians(-0.9), 2.2, 0.45) + spring(t, sim.T_STOP, math.radians(0.7), 2.0, 0.5)
    T = stone_xform(xb, bottom, tilt)

    # ---- log bodies behind the stone (A first when it is out)
    for name in ["A", "B", "C"]:
        x, cy, th, c = lstate[name]
        canvas = draw_log(canvas, cam, LOGS[name], x, cy, th, seed={"A": 5, "B": 6, "C": 7}[name], frame_k=k)
    # ---- the stone (cut card)
    sm = raster([[T(x, y) for x, y in STONE]], cam)
    canvas = gap(canvas, sm, cam, width=1.8)
    canvas = halo(canvas, sm, cam, reach=16, density=0.5, seed=900 + k // 2, dark=0.07, haze=0.25)
    segs, scr = stone_streaks(T)
    st = strokes(segs, cam) * cv2.erode((sm > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8))
    canvas = ink(canvas, sm, 0.04, streak=st)
    sc = strokes(scr, cam) * sm
    canvas = canvas * (1 - sc) + 0.82 * sc

    # ---- the carrier and log D
    hx = carrier_hip_x(t)
    crouch = smooth((t - 18.62) / (T_SETDOWN - 18.62)) * (1 - smooth((t - 20.05) / 0.6))
    hip_c = (hx, 432 + 62 * crouch + 1.5 * math.sin((t - 15) * 2 * math.pi / 0.68))
    lean = 30 + 26 * crouch - 10 * smooth((t - 20.1) / 0.5)
    sway = 0.0
    for pt in C_PLANTS:                       # each foot plant swings the carried log (secondary)
        sway += spring(t, pt, 2.4, 2.6, 0.5)
    carried_c = (hx + 74, hip_c[1] + 2 + sway * 0.4)
    LD = LOGS["D"]
    setx = 520 + 33.0 * 3.6 + 74
    ground_c = (setx, LD.cy(0.6))
    u = smooth((t - 18.62) / (T_SETDOWN - 18.62))
    if t < T_SETDOWN:
        dcx = carried_c[0] + (ground_c[0] - carried_c[0]) * u
        dcy = carried_c[1] + (ground_c[1] - carried_c[1]) * u
        dth = 0.6 + 0.05 * sway
    else:
        dcx, dcy = ground_c
        dth = 0.6
        dcy += -spring(t, T_SETDOWN, 1.5, 4.0, 0.45) ** 2 * 0  # contact: no bounce through the ground
    rD = LD.R
    hold = t < 20.05
    if hold:
        handsC = [(dcx - rD * 0.55, dcy - rD * 0.86), (dcx + rD * 0.15, dcy - rD * 1.0)]
    else:
        rel = smooth((t - 20.05) / 0.5)
        handsC = [(dcx - rD * 0.55 - 30 * rel, dcy - rD * 0.86 - 40 * rel), (dcx + rD * 0.15 - 36 * rel, dcy - rD - 34 * rel)]
    head_face_c = -1 if t > 20.55 else 1
    feetC = [(C_FEET[k][0][0], GROUND - 3 - C_FEET[k][0][1]), (C_FEET[k][1][0], GROUND - 3 - C_FEET[k][1][1])]
    carrier = Puppet("carrier", 1.15, 300)
    pcs_c = carrier.build(hip_c, lean, lean + 14, -18 - 20 * crouch + 35 * (head_face_c < 0), feetC, handsC, facing=1,
                          knee_bend=(-1, -1), elbow_bend=(1, 1), head_face=head_face_c)
    canvas = draw_log(canvas, cam, LD, dcx, dcy, dth, seed=8, frame_k=k)
    canvas = draw_puppet(canvas, cam, pcs_c, 3, k, extra_scratch=[((carrier.joints["eye"]), 1.0, 1.0)])

    # ---- the pusher: hands pinned to the stone's back face, feet locked on plants
    hy = [-88, -66]
    handsP = [T(stone_back_x(y) + 1.5, y) for y in hy]
    nod = spring(t, sim.T_STOP, 7.0, 2.4, 0.42) + spring(t, T_REL, -4.0, 2.6, 0.45)
    look_back = 17.45 <= t < 18.55
    hp = (pusher_hip_x(t), 462 + 1.2 * math.sin((t - 15) * 2 * math.pi / 0.6) * (1 if t < sim.T_STOP else 0))
    feetP = [(P_FEET[k][0][0], GROUND - 3 - P_FEET[k][0][1]), (P_FEET[k][1][0], GROUND - 3 - P_FEET[k][1][1])]
    pusher = Puppet("pusher", 1.2, 100)
    head_ang = (-30 + nod) if not look_back else 10
    pcs_p = pusher.build(hp, 40, 48, head_ang, feetP, handsP, facing=1, knee_bend=(-1, -1), elbow_bend=(1, 1),
                         head_face=(-1 if look_back else 1))
    canvas = draw_puppet(canvas, cam, pcs_p, 1, k, extra_scratch=[((pusher.joints["eye"]), 1.0, 1.0)])

    METRICS.append({"t": round(t, 3), "cam": "close" if cam is CLOSE else "wide",
                    "pusher_hand_residual": max(pusher.res["hand0"], pusher.res["hand1"]),
                    "pusher_foot_residual": max(pusher.res["foot0"], pusher.res["foot1"]),
                    "carrier_hand_residual": max(carrier.res["hand0"], carrier.res["hand1"]) if hold else None,
                    "carrier_foot_residual": max(carrier.res["foot0"], carrier.res["foot1"]),
                    "pusher_feet_x": [round(feetP[0][0], 2), round(feetP[1][0], 2)],
                    "pusher_planted": [P_FEET[k][0][2], P_FEET[k][1][2]],
                    "stone_xb": round(xb, 2), "logs": {n: [round(v[0], 2), round(v[2], 3)] for n, v in lstate.items()}})

    rgb = Image.fromarray(np.clip(wall.ramp(np.clip(canvas, 0, 1)), 0, 255).astype(np.uint8))
    return caption(rgb, t)


FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 23)
CAP = "« Et moi ? » dit le rouleau qu'on laisse derrière."


def caption(im, t):
    a = smooth((t - 17.2) / 0.12) * (1 - smooth((t - 20.3) / 0.25))
    if a <= 0:
        return im
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    w = d.textlength(CAP, font=FONT)
    x, y = (SW - w) / 2, 500
    d.text((x + 1.2, y + 1.2), CAP, font=FONT, fill=(14, 15, 8, int(220 * a)))
    d.text((x, y), CAP, font=FONT, fill=(242, 236, 212, int(255 * a)))
    return Image.alpha_composite(im.convert("RGBA"), over).convert("RGB")


# ------------------------------------------------------------------ sound ---
def sound(mix):
    import numpy as _np
    R = kit.RATE
    rng = _np.random.default_rng(56)
    mix.room(0, 6.0, gain=0.035, hum=0)

    # FORAGED: real knocks on wood ("Knocking on wood or door.ogg", stephan / PDSounds,
    # public domain, Wikimedia Commons), decoded with ffmpeg; single knocks cut out and
    # slowed (pitch lowered) so a door knock becomes a heavier log on stone.
    import wave as _wave
    w = _wave.open(str(MEDIA / "knock.wav"))
    kn = _np.frombuffer(w.readframes(w.getnframes()), _np.int16).astype(float) / 32768.0
    grains = {k: kn[int((on - 0.012) * R): int((on + 0.30) * R)] for k, on in
              {"a": 0.495, "b": 2.470, "c": 4.441}.items()}

    def tok(at, gain=0.5, pitch=1.0, dry=1.0, grain="a"):
        g = grains[grain]
        idx = _np.arange(0, len(g) - 1, pitch * 0.78)
        sig = _np.interp(idx, _np.arange(len(g)), g)
        sig = sig * _np.exp(-_np.arange(len(sig)) / (0.09 * R))
        mix.add(sig / (_np.max(_np.abs(sig)) + 1e-9), at, gain=gain, pan=-0.25)

    # bark rolling: a dry crackle whose density/level follows each log's angular speed
    dur = 6.0
    n = int(dur * R)
    tt = _np.arange(n) / R + T0
    env = _np.zeros(n)
    for name in ["A", "B", "C"]:
        xs = _np.array([f["logs"][name]["th"] for f in SIMF])
        ts = _np.array([f["t"] for f in SIMF])
        om = _np.abs(_np.gradient(xs, ts))
        env += _np.interp(tt, ts, om)
    env = env / (env.max() + 1e-9)
    crack = (rng.random(n) < 0.0016 + 0.010 * env).astype(float) * rng.uniform(0.3, 1.0, n)
    crack = _np.convolve(crack, _np.exp(-_np.arange(int(0.004 * R)) / (0.0008 * R)), mode="same")
    rumble = mix.lowpass(rng.normal(0, 1, n), 140) * 3.0
    sig = (crack * 0.5 + rumble * 0.35) * env
    mix.add(sig, 0.0, gain=0.45)
    # log A's own short roll out behind (0.33 s) then the tok on its facet, two small rocks
    a0 = T_REL - T0
    m = int(0.34 * R); e = _np.linspace(1, 0, m) ** 0.7
    cr = (rng.random(m) < 0.02).astype(float) * rng.uniform(0.4, 1, m)
    cr = _np.convolve(cr, _np.exp(-_np.arange(160) / 30.0), mode="same")
    mix.add(cr * e, a0, gain=0.35, pan=-0.3)
    tok(A_STOP - T0, gain=0.62)
    tok(A_STOP - T0 + 0.17, gain=0.10, pitch=1.04, grain="b")
    tok(A_STOP - T0 + 0.33, gain=0.035, pitch=1.06, grain="b")
    # the stone settles when it stops (low)
    mix.thud(sim.T_STOP - T0, freq=55, gain=0.35, seconds=0.5)
    # footsteps on every plant (pusher louder, carrier heavier)
    for p in P_PLANTS:
        mix.step(p - T0, gain=0.12, pan=-0.35)
    for p in C_PLANTS:
        mix.step(p - T0, gain=0.15, pan=0.3)
    # log D set down in front: wood on stone, lower and duller than A's tok
    tok(T_SETDOWN - T0, gain=0.42, pitch=0.85, grain="c")
    mix.thud(T_SETDOWN - T0, freq=80, gain=0.25, seconds=0.25)
    # carrier stands up: two steps as he straightens
    mix.step(20.3 - T0, gain=0.10, pan=0.3)
    mix.step(20.62 - T0, gain=0.08, pan=0.3)


# ------------------------------------------------------------------- main ---
film = kit.Film("test-shot", seconds=6.0, size=(SW, SH), fps=FPS, boil=0, seed=3)
film.poster_at = 2.0


@film.picture
def _pic(t, inkc):
    k = int(round(t * FPS))
    inkc.img.paste(render(T0 + t, k))


film.sound(sound)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        for ts in sys.argv[2:]:
            t = float(ts) - T0
            img = film.frame(int(round(t * FPS)))
            img.save(MEDIA / f"still_{float(ts):05.2f}.png")
        print("stills ->", MEDIA)
    else:
        film.render(out_dir=OUTDIR)
        # contact and continuity metrics (#33 residuals, foot-lock slide, roller slip)
        slide = 0.0
        for a, b in zip(METRICS, METRICS[1:]):
            for i in range(2):
                if a["pusher_planted"][i] and b["pusher_planted"][i]:
                    slide = max(slide, abs(a["pusher_feet_x"][i] - b["pusher_feet_x"][i]))
        rep = {"frames": len(METRICS),
               "max_pusher_hand_residual_px": max(m["pusher_hand_residual"] for m in METRICS),
               "max_pusher_foot_residual_px": max(m["pusher_foot_residual"] for m in METRICS),
               "max_carrier_hand_residual_px_while_holding": max(m["carrier_hand_residual"] or 0 for m in METRICS),
               "max_carrier_foot_residual_px": max(m["carrier_foot_residual"] for m in METRICS),
               "max_planted_foot_slide_px": slide,
               "events": EVENTS, "a_stop": A_STOP, "pusher_plants": P_PLANTS, "carrier_plants": C_PLANTS,
               "per_frame": METRICS}
        (HERE / "metrics.json").write_text(json.dumps(rep, indent=1))
        print({k: v for k, v in rep.items() if k not in ("per_frame",)})
