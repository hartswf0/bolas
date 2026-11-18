"""teuf-teuf ANIMATOR: renders every shot of plan s5 frame by frame over the layout plates.

Reiniger cut-card puppets (SCION #2): pinned joints, joint-angle limits, replacement profiles
(hands open / gripping, head forward / turned back / bowed, log frontal / 3/4 cylinder),
exposure sheet. IK (SCION #33): FK spine, analytic two-bone IK with pole signs and limits,
planted-foot locks from a contact timeline, hands pinned to the stone, the rope, the log, the pin.
Secondary (SCION #41): spring-dampers excited only by sim events (motion.SP).

Look: painted charcoal silhouettes - union of tapered pieces, smoothed into one brushed
contour, a static ragged dry-brush edge, grey dry-brush streaks along each limb, a soft
airbrush halo whose texture is fixed in the frame (does not re-randomise), pale card gap
where silhouettes overlap. Everything is composited in luminance on the layout plates and
printed once through the layout's sepia ramp (layout_wall.ramp) with a fixed grain per shot.

FORAGED: wall plates (layout unit; Cueva de las Manos, Suzko, CC BY-SA 3.0);
wheel = cv2.grabCut cutout of the Ljubljana Marshes wheel (Petar Milosevic, CC BY-SA 4.0).
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import motion as M                                   # noqa: E402
import layout_wall as LW                             # noqa: E402

ROOT = "/home/user/bolas/paeleo/scion/oulipo/films"
LAY = ROOT + "/sources/teuf-teuf/layout/"
OUT = ROOT + "/sources/teuf-teuf/animator/"
W, H = 1280, 720
FPS = 24
GROUND = M.GROUND
SL = M.SL
STONE_H = M.STONE_H


# ------------------------------------------------------------- cameras ---
class Cam:
    def __init__(self, name, s, ox, oy, depth):
        self.name, self.s, self.ox, self.oy, self.depth = name, s, ox, oy, depth

    def p(self, x, y):
        return ((x - self.ox) * self.s, (y - self.oy) * self.s)


CAM_A = Cam("A", 1.0, 0.0, 0.0, (10.0, -7.0))
CAM_B = Cam("B", LW.CAM_B.s, LW.CAM_B.ox, LW.CAM_B.oy, (25.0, -16.0))
PLATE = {"A": np.load(LAY + "frameA_lum.npy").astype(np.float32),
         "B": np.load(LAY + "frameB_lum.npy").astype(np.float32)}


def static_fields(seed):
    rng = np.random.default_rng(seed)
    lf = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 9)
    lf = 1.0 + 0.45 * lf / (lf.std() + 1e-6)
    dots = (rng.random((H, W)) < 0.010).astype(np.float32)
    dots = cv2.GaussianBlur(dots, (0, 0), 0.7) * 3.0
    edge = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.1)
    edge = edge / (edge.std() + 1e-6)
    edge2 = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 3.0)
    edge2 = edge2 / (edge2.std() + 1e-6)
    # dry-brush field: long horizontal-ish bristle streaks (a loaded brush dragged sideways)
    br = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), sigmaX=7.0, sigmaY=0.7)
    br = br / (br.std() + 1e-6)
    spr = (rng.random((H, W)) < 0.05).astype(np.float32)
    spr = cv2.GaussianBlur(spr, (0, 0), 0.9) * 2.2
    return {"lf": np.clip(lf, 0.2, 1.8), "dots": np.clip(dots, 0, 1), "edge": edge * 0.6 + edge2 * 0.4,
            "brush": br, "spray": np.clip(spr, 0, 1)}


class _Fields(dict):
    def __missing__(self, k):          # push-in cameras share frame A's screen-fixed fields
        return self["A"]


FIELDS = _Fields({"A": static_fields(71), "B": static_fields(72)})

# --------------------------------------------------------------- raster ---
SHIFT = 3
SC = 1 << SHIFT


def _pts(cam, pts):
    return np.array([[(x - cam.ox) * cam.s * SC, (y - cam.oy) * cam.s * SC] for x, y in pts], np.int32)


def fill(cam, polys=(), discs=(), lines=()):
    im = np.zeros((H, W), np.uint8)
    for poly in polys:
        if len(poly) >= 3:
            cv2.fillPoly(im, [_pts(cam, poly)], 255, cv2.LINE_AA, SHIFT)
    for (cx, cy, r) in discs:
        x, y = cam.p(cx, cy)
        rr = max(1, int(r * cam.s * SC))
        cv2.circle(im, (int(x * SC), int(y * SC)), rr, 255, -1, cv2.LINE_AA, SHIFT)
    for pts, w in lines:
        cv2.polylines(im, [_pts(cam, pts)], False, 255, max(1, int(round(w * cam.s))), cv2.LINE_AA, SHIFT)
    return im.astype(np.float32) / 255


def strokes(cam, segs):
    """segs: (pts, width_world, value) -> alpha*value layer"""
    im = np.zeros((H, W), np.float32)
    for pts, w, val in segs:
        cv2.polylines(im, [_pts(cam, pts)], False, float(val), max(1, int(round(w * cam.s))), cv2.LINE_AA, SHIFT)
    return im


def painted(cam, raw, soft=1.5, rag=0.13):
    """union of cut pieces -> one brushed contour with a static ragged dry-brush edge"""
    b = cv2.GaussianBlur(raw, (0, 0), soft * cam.s)
    th = 0.5 + rag * FIELDS[cam.name]["edge"]
    return np.clip((b - th) / 0.10 + 0.5, 0, 1)


def halo(canvas, cam, m, reach, haze, dots=0.55, dark=0.10):
    """soft airbrush blow round a silhouette; its grain is fixed in the frame (no shimmer)"""
    f = FIELDS[cam.name]
    hz = cv2.GaussianBlur(m, (0, 0), reach * cam.s) * haze * f["lf"]
    m8 = (m > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 3) / cam.s
    band = np.exp(-dist / (reach * 0.7)) * (dist > 0.5)
    a = np.clip(hz + f["dots"] * band * dots, 0, 0.9) * (1 - m)
    return canvas * (1 - a) + dark * a


def gap(canvas, cam, m, width=1.5, light=0.74):
    k = max(1, int(round(width * cam.s)))
    dil = cv2.dilate((m > 0.4).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    ring = cv2.GaussianBlur(np.clip(dil.astype(np.float32) - m, 0, 1), (0, 0), 0.6)
    dark = canvas < 0.38
    return np.where(dark & (ring > 0.05), canvas * (1 - ring) + light * ring, canvas)


def ink(canvas, m, value):
    return canvas * (1 - m) + value * m


# ------------------------------------------------------------ puppets ---
def tube(p0, p1, w0, w1, wm=None, n=14):
    """stamped discs along a bone: a tapered limb with an optional belly (wm at 0.35)"""
    out = []
    for i in range(n + 1):
        u = i / n
        if wm is None:
            w = w0 + (w1 - w0) * u
        else:
            w = (w0 + (wm - w0) * (u / 0.35)) if u < 0.35 else (wm + (w1 - wm) * ((u - 0.35) / 0.65))
        out.append((p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u, w))
    return out


def ik2(p0, target, L1, L2, bend, lim=(0.0, 160.0)):
    """analytic two-bone IK with pole sign `bend` and an interior-angle limit (degrees of flex)"""
    x0, y0 = p0
    tx, ty = target
    dx, dy = tx - x0, ty - y0
    dist = math.hypot(dx, dy)
    # flex limit -> min / max reach
    fmin, fmax = math.radians(lim[0]), math.radians(lim[1])
    dmax = math.sqrt(L1 * L1 + L2 * L2 + 2 * L1 * L2 * math.cos(fmin))
    dmin = math.sqrt(L1 * L1 + L2 * L2 + 2 * L1 * L2 * math.cos(fmax))
    d = min(max(dist, dmin + 1e-3), dmax - 1e-3)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    k = (x0 + L1 * math.cos(a + bend * b), y0 + L1 * math.sin(a + bend * b))
    ang2 = math.atan2(ty - k[1], tx - k[0])
    e = (k[0] + L2 * math.cos(ang2), k[1] + L2 * math.sin(ang2))
    flex = math.degrees(math.pi - math.acos(max(-1, min(1, (L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2)))))
    return k, e, math.hypot(e[0] - tx, e[1] - ty), flex


def head_poly(neck, ang, face, s, kind):
    """animal-like profile heads (replacement profiles): heavy brow, long muzzle, pricked ear"""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        x = u * face
        y = -v
        return (neck[0] + (x * ca - y * sa) * s, neck[1] + (x * sa + y * ca) * s)
    if kind == "bow":
        skull = [P(-9, 6), P(-12, 16), P(-8, 26), P(0, 30), P(9, 29), P(15, 24), P(20, 15), P(25, 6),
                 P(27, 0), P(23, -2), P(16, 1), P(10, 2), P(4, 0)]
    else:
        skull = [P(-9, 8), P(-12, 18), P(-8, 27), P(0, 32), P(8, 32), P(14, 29), P(18, 25), P(25, 20),
                 P(32, 13), P(34, 8), P(30, 5), P(23, 6), P(17, 7), P(13, 3), P(6, 0), P(-2, 1)]
    ear = [P(-4, 27), P(-10, 40), P(-5, 38), P(2, 31)]
    eye = P(14, 21) if kind != "bow" else P(13, 17)
    brow = [P(8, 26), P(13, 27), P(19, 24)]
    return skull, ear, eye, brow


def hand_shape(e, dirv, s, kind, face):
    """replacement hands: 'grip' (closed fist with thumb knuckle), 'open' (flat palm, thumb apart)"""
    dx, dy = dirv
    L = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy * face, ux * face
    if kind == "grip":
        return [], [(e[0] + ux * 3 * s, e[1] + uy * 3 * s, 5.2 * s), (e[0] + ux * 1 * s - nx * 3 * s, e[1] + uy * 1 * s - ny * 3 * s, 3.0 * s)]
    # open: palm + fingers as a tapered blade, thumb spike
    palm = tube(e, (e[0] + ux * 13 * s, e[1] + uy * 13 * s), 4.3 * s, 1.6 * s, n=6)
    thumb = tube((e[0] + ux * 2 * s, e[1] + uy * 2 * s), (e[0] + ux * 6 * s - nx * 8 * s, e[1] + uy * 6 * s - ny * 8 * s), 2.2 * s, 1.0 * s, n=4)
    return [], palm + thumb


class Puppet:
    def __init__(self, name, s, seed):
        self.name, self.s, self.seed = name, s, seed
        self.T1, self.T2 = 46 * s, 50 * s
        self.TH, self.SH = 64 * s, 62 * s
        self.UA, self.LA = 47 * s, 45 * s
        self.res = {}
        self.flex = {}

    def solve(self, hip, a1, a2, f, feet, hands, solve_hands):
        """contact solve (#33): move the root so every foot target and every PINNED hand target is
        inside its limb's reach, so the IK end-effectors land exactly on their targets (no slide,
        no hand gap). Hands pull the root toward the stone; feet then lower the hip if needed."""
        lmax = math.sqrt(self.TH ** 2 + self.SH ** 2 + 2 * self.TH * self.SH * math.cos(math.radians(2.0))) - 0.6
        amax = self.UA + self.LA - 0.6
        hx, hy = hip
        for _ in range(8):
            moved = False
            mid = (hx + f * self.T1 * math.sin(a1), hy - self.T1 * math.cos(a1))
            sh = (mid[0] + f * self.T2 * 0.80 * math.sin(a2), mid[1] - self.T2 * 0.80 * math.cos(a2))
            for i, hd in enumerate(hands):
                if not solve_hands[i]:
                    continue
                dx, dy = hd[0] - sh[0], hd[1] - sh[1]
                d = math.hypot(dx, dy)
                if d > amax:
                    k = (d - amax) / d
                    hx += dx * k; hy += dy * k
                    sh = (sh[0] + dx * k, sh[1] + dy * k)
                    moved = True
            for ft in feet:
                dx, dy = ft[0] - hx, ft[1] - hy
                if math.hypot(dx, dy) > lmax:
                    if abs(dx) < lmax - 0.5:
                        hy = ft[1] - math.sqrt(lmax * lmax - dx * dx)
                    else:
                        hx = ft[0] - math.copysign(lmax - 0.5, dx) * 0.999
                        hy = ft[1] - math.sqrt(max(0.0, lmax * lmax - (lmax - 0.5) ** 2))
                    moved = True
            if not moved:
                break
        return (hx, hy)

    def build(self, hip, lean1, lean2, head_ang, feet, hands, face=1, head_face=None, head_kind="fwd",
              hand_kind=("grip", "grip"), knee_bend=(-1, -1), elbow_bend=(1, 1), sit=False, solve_hands=(False, False)):
        s, f = self.s, face
        a1, a2 = math.radians(lean1), math.radians(lean2)
        hip = (hip[0], hip[1] - HIP_RAISE)
        hip = self.solve(hip, a1, a2, f, feet, hands, solve_hands)
        self.hip_solved = hip
        mid = (hip[0] + f * self.T1 * math.sin(a1), hip[1] - self.T1 * math.cos(a1))
        neck = (mid[0] + f * self.T2 * math.sin(a2), mid[1] - self.T2 * math.cos(a2))
        sh = (mid[0] + f * self.T2 * 0.80 * math.sin(a2), mid[1] - self.T2 * 0.80 * math.cos(a2))
        far, near, body = [], [], []
        streak_bones = []
        for i, ft in enumerate(feet):
            k, e, r, fl = ik2(hip, ft, self.TH, self.SH, knee_bend[i] * f, lim=(2.0, 150.0))
            self.res[f"foot{i}"] = r
            self.flex[f"knee{i}"] = fl
            toe = (e[0] + f * 17 * s, e[1] + 1.5 * s)
            heel = (e[0] - f * 4 * s, e[1] - 1 * s)
            discs = tube(hip, k, 17 * s, 8 * s, wm=16 * s) + tube(k, e, 8 * s, 3.8 * s, wm=10.0 * s) + \
                tube(heel, toe, 4.6 * s, 2.2 * s, n=8)
            (far if i == 1 else near).append(discs)
            streak_bones += [(hip, k, 12 * s), (k, e, 6.5 * s)]
            self.res[f"foot{i}_xy"] = e
        for i, hd in enumerate(hands):
            k, e, r, fl = ik2(sh, hd, self.UA, self.LA, elbow_bend[i] * f, lim=(0.0, 160.0))
            self.res[f"hand{i}"] = r
            self.flex[f"elbow{i}"] = fl
            _, hdiscs = hand_shape(e, (e[0] - k[0], e[1] - k[1]), s, hand_kind[i], f)
            discs = tube(sh, k, 10.5 * s, 6 * s, wm=10 * s) + tube(k, e, 6.0 * s, 3.4 * s, wm=6.8 * s) + hdiscs
            (far if i == 1 else near).append(discs)
            streak_bones += [(sh, k, 7 * s), (k, e, 5 * s)]
        # FK spine: buttock, belly, deep chest, neck - one curved tapered body
        hipb = (hip[0] - f * 5 * s, hip[1] + 2 * s)
        body.append(tube(hipb, mid, 19 * s, 16 * s, wm=20 * s, n=10) + tube(mid, neck, 16 * s, 7.5 * s, wm=21.5 * s, n=12))
        streak_bones += [(hip, mid, 14 * s), (mid, neck, 15 * s)]
        hf = f if head_face is None else head_face
        skull, ear, eye, brow = head_poly(neck, math.radians(head_ang), hf, s, head_kind)
        self.joints = dict(hip=hip, mid=mid, neck=neck, sh=sh, eye=eye)
        return dict(far=far, near=near, body=body, head=[skull, ear], eye=eye, brow=brow, bones=streak_bones)


def dry_streaks(bones, seed, val=0.25):
    rng = np.random.default_rng(seed)
    segs = []
    for bi, (p0, p1, w) in enumerate(bones):
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0) + 1e-6
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux
        for k in range(4 if w < 9 else 6):
            off = rng.uniform(-0.6, 0.6)
            t = rng.uniform(0.0, 0.3)
            while t < 0.92:
                t2 = min(0.95, t + rng.uniform(0.18, 0.5))
                pts = [(x0 + ux * L * tt + nx * w * off * (1 - 0.3 * tt), y0 + uy * L * tt + ny * w * off * (1 - 0.3 * tt))
                       for tt in np.linspace(t, t2, 4)]
                segs.append((pts, rng.uniform(0.6, 1.2), rng.uniform(0.55, 1.0) * val))
                t = t2 + rng.uniform(0.06, 0.25)
    return segs


def brushed(cam, raw):
    """repair 1: the silhouette edge is a dry brush, not a cut line: bristle streaks drag the
    contour sideways and break it into a feathered fringe (fields fixed in the frame: no boil)."""
    f = FIELDS[cam.name]
    b = cv2.GaussianBlur(raw, (0, 0), 2.0 * cam.s)
    th = np.clip(0.5 + 0.13 * f["edge"] + 0.16 * f["brush"], 0.3, 0.75)
    core = np.clip((b - th) / 0.10 + 0.5, 0, 1)
    fringe = np.clip((b - 0.18) / 0.32, 0, 1) * (1 - core)
    fringe = fringe * np.clip(0.55 + 0.6 * f["brush"], 0, 1) ** 1.5
    return np.clip(core + fringe * 0.85, 0, 1)


def blown(canvas, cam, m):
    """repair 1: blown-pigment halo (spray) round the figure, as round the reference's bull:
    a soft haze plus a field of fine pigment specks thinning out with distance."""
    f = FIELDS[cam.name]
    m8 = (m > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 3) / cam.s
    haze = np.exp(-dist / 7.0) * 0.30 * f["lf"] + np.exp(-dist / 16.0) * 0.12
    specks = f["spray"] * np.exp(-dist / 10.0) * 0.9 + f["dots"] * np.exp(-dist / 14.0) * 0.5
    a = np.clip(haze + specks, 0, 0.9) * (dist > 0.3) * (1 - m)
    return canvas * (1 - a) + 0.10 * a


def draw_puppet(canvas, cam, P, seed):
    allp = [d for grp in (P["far"], P["body"], P["near"]) for d in grp]
    discs = [d for g in allp for d in g]
    raw = fill(cam, polys=P["head"], discs=discs)
    m = brushed(cam, raw)
    canvas = gap(canvas, cam, m, width=1.6)
    canvas = blown(canvas, cam, m)
    canvas = ink(canvas, m, 0.035)
    # far limbs a shade lighter so the near/far pair reads (cut card laid under)
    farm = painted(cam, fill(cam, discs=[d for g in P["far"] for d in g]), soft=1.3, rag=0.12)
    nearbody = painted(cam, fill(cam, polys=P["head"], discs=[d for g in P["body"] + P["near"] for d in g]), soft=1.3, rag=0.12)
    sep = np.clip(farm - nearbody, 0, 1)
    canvas = canvas * (1 - 0.6 * sep) + 0.11 * 0.6 * sep
    # (repair 1: the pale hairline joint seams were removed: they read as cut-card/vector construction)
    st = strokes(cam, dry_streaks(P["bones"], seed))
    inner = cv2.erode((m > 0.6).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    st = st * inner
    canvas = canvas * (1 - np.clip(st * 1.6, 0, 1)) + 0.30 * np.clip(st * 1.6, 0, 1) * 1.0
    sc = strokes(cam, [([P["eye"], (P["eye"][0] + 0.8, P["eye"][1] + 0.4)], 1.6, 1.0), (P["brow"], 0.9, 0.7)]) * m
    canvas = canvas * (1 - sc) + 0.85 * sc
    return canvas, m


# ------------------------------------------------------------- the stone ---
def stone_T(xb, bottom, tilt, pivot=(SL / 2, 0.0)):
    c, s_ = math.cos(tilt), math.sin(tilt)
    px, py = pivot

    def T(x, y):
        x -= px
        y -= py
        return (xb + px + x * c - y * s_, bottom + py + x * s_ + y * c)
    return T


def stone_back_x(y_local):
    best = None
    P = M.STONE
    for i in range(len(P)):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
        if (y0 - y_local) * (y1 - y_local) <= 0 and y0 != y1:
            x = x0 + (x1 - x0) * (y_local - y0) / (y1 - y0)
            best = x if best is None else min(best, x)
    return best


STONE_SEGS = None


def stone_streak_local():
    rng = np.random.default_rng(77)
    segs, scr = [], []
    for k in range(22):
        y = rng.uniform(-STONE_H + 10, -8)
        half = math.sqrt(max(0, 1 - ((y + 63) / 68) ** 2)) * (SL / 2 - 4)
        x0 = SL / 2 - half + rng.uniform(4, 26)
        x1 = SL / 2 + half - rng.uniform(4, 26)
        x = x0
        while x < x1 - 10:
            xe = min(x1, x + rng.uniform(16, 50))
            arch = rng.uniform(-3, 3)
            segs.append(([(xx, y + arch * math.sin(math.pi * (xx - x0) / (x1 - x0 + 1)) + 0.03 * (xx - SL / 2)) for xx in np.linspace(x, xe, 5)],
                         rng.uniform(0.8, 1.8), rng.uniform(0.14, 0.30)))
            x = xe + rng.uniform(6, 22)
    top = sorted([p for p in M.STONE if p[1] < -STONE_H + 26])
    for a, b in [(0.12, 0.42), (0.55, 0.82)]:
        i0, i1 = int(a * len(top)), int(b * len(top))
        scr.append(([(x + 2, y + 5) for x, y in top[i0:i1]], 1.1, 0.8))
    scr.append(([(40, -32), (62, -42), (88, -40)], 1.0, 0.6))
    return segs, scr


STONE_SEGS = stone_streak_local()


def draw_stone(canvas, cam, T):
    raw = fill(cam, polys=[[T(x, y) for x, y in M.STONE]])
    m = painted(cam, raw, soft=1.0, rag=0.10)
    canvas = gap(canvas, cam, m, width=1.8)
    canvas = halo(canvas, cam, m, reach=13, haze=0.32, dots=0.55)
    canvas = ink(canvas, m, 0.04)
    segs, scr = STONE_SEGS
    st = strokes(cam, [([T(x, y) for x, y in pts], w, v) for pts, w, v in segs])
    st = st * cv2.erode((m > 0.6).astype(np.uint8), np.ones((3, 3), np.uint8))
    canvas = canvas + st * 0.9
    sc = strokes(cam, [([T(x, y) for x, y in pts], w, v) for pts, w, v in scr]) * m
    canvas = canvas * (1 - sc) + 0.84 * sc
    return canvas, m


# ---------------------------------------------------------------- logs ---
def draw_log(canvas, cam, L, cx, cy, th, seed, cyl=False, end_mark=0.0):
    """frontal profile (wide): irregular bark end with a short visible length;
    3/4 cylinder replacement (close-up 3b): the full bark length receding."""
    dx, dy = cam.depth if not cyl else (cam.depth[0] * 0.95, cam.depth[1] * 0.95)
    phis = np.linspace(0, 2 * math.pi, 80, endpoint=False)
    rr = L.r(phis - th)
    near = [(cx + r * math.cos(p), cy + r * math.sin(p)) for r, p in zip(rr, phis)]
    far = [(x + dx, y + dy) for x, y in near]
    quads = [[near[i], near[(i + 1) % 80], far[(i + 1) % 80], far[i]] for i in range(80)]
    stub = []
    if L.stub is not None:
        ps = L.stub + th
        r0 = float(L.r(L.stub)) * 0.95
        if abs(math.sin(ps)) < 0.8 or math.sin(ps) < 0:          # not pressed into ground / stone
            base = (cx + r0 * math.cos(ps) + dx * 0.55, cy + r0 * math.sin(ps) + dy * 0.55)
            tip = (base[0] + 0.55 * L.R * math.cos(ps + 0.25), base[1] + 0.55 * L.R * math.sin(ps + 0.25))
            n_ = (-math.sin(ps), math.cos(ps))
            w_ = 0.22 * L.R
            stub = [[(base[0] + n_[0] * w_, base[1] + n_[1] * w_), tip, (base[0] - n_[0] * w_, base[1] - n_[1] * w_)]]
    body = fill(cam, polys=quads + [far] + stub)
    face = fill(cam, polys=[near])
    allm = painted(cam, np.maximum(body, face), soft=0.7, rag=0.07)
    canvas = gap(canvas, cam, allm, width=1.3)
    canvas = halo(canvas, cam, allm, reach=7, haze=0.24, dots=0.45)
    canvas = ink(canvas, allm, 0.06)
    # bark ridges along the length, fixed to the body (turn with it)
    ad = math.atan2(dy, dx)
    segs = []
    for psi0, u0, val in L.bark:
        psi = psi0 + th
        vis = math.cos(psi - ad)
        if vis <= 0.0:
            continue
        r = float(L.r(psi0)) * 0.97
        a = (cx + r * math.cos(psi), cy + r * math.sin(psi))
        pts = [(a[0] + dx * u, a[1] + dy * u) for u in np.linspace(u0, 0.98, 5)]
        segs.append((pts, 1.0 + 0.6 * vis, (0.16 + 0.2 * vis) * val))
    knots = []
    for psi0, u in L.knots:
        psi = psi0 + th
        vis = math.cos(psi - ad)
        if vis > 0.2:
            r = float(L.r(psi0)) * 0.93
            kx, ky = cx + r * math.cos(psi) + dx * u, cy + r * math.sin(psi) + dy * u
            w = 2.0 + 2.6 * vis * (2 if cyl else 1)
            knots.append(([(kx + w * math.cos(a) * 1.3, ky + w * math.sin(a) * 0.8) for a in np.linspace(0, 6.3, 12)], 1.0, 0.7))
    bodyonly = np.clip(body - face, 0, 1)
    st = strokes(cam, segs) * bodyonly
    canvas = canvas + st
    if knots:
        sk = strokes(cam, knots) * bodyonly
        canvas = canvas * (1 - sk) + 0.6 * sk
    # sawn end: paler end grain, rings and a radial crack, all turning with the log
    canvas = canvas * (1 - face) + face * (0.17 * face + canvas * (1 - face))
    rings = []
    for fr_, val in [(0.70, 0.55), (0.40, 0.6)]:
        ring = []
        for p in np.linspace(0, 2 * math.pi, 36):
            r = float(L.r(p - th)) * fr_
            ring.append((cx + r * math.cos(p), cy + r * math.sin(p)))
        rings.append((ring, 0.9, val))
    em = th + end_mark
    crack = [(cx + L.R * u * math.cos(em + 0.08 * math.sin(9 * u)), cy + L.R * u * math.sin(em + 0.08 * math.sin(9 * u)))
             for u in np.linspace(0.1, 0.92, 7)]
    rings.append((crack, 1.6, 0.95))
    sr = strokes(cam, rings) * face
    canvas = canvas * (1 - sr) + 0.80 * sr
    rim = strokes(cam, [(near + [near[0]], 2.0, 1.0)])
    canvas = canvas * (1 - rim) + 0.03 * rim
    return canvas, allm


# --------------------------------------------------------------- wheel ---
WH_LUM = np.load(OUT + "wheel_lum.npy")
WH_A = np.load(OUT + "wheel_alpha.npy")
WH_R0 = 300.0
WH_C = 310.0


def draw_wheel(canvas, cam, cx, cy, th, R, pinned=True, dim=0.0):
    sc = R * cam.s / WH_R0
    sx, sy = cam.p(cx, cy)
    A = cv2.getRotationMatrix2D((WH_C, WH_C), -math.degrees(th), sc)
    A[0, 2] += sx - WH_C
    A[1, 2] += sy - WH_C
    a = cv2.warpAffine(WH_A, A, (W, H), flags=cv2.INTER_LINEAR)
    l = cv2.warpAffine(WH_LUM, A, (W, H), flags=cv2.INTER_LINEAR)
    canvas = gap(canvas, cam, a, width=1.4)
    canvas = halo(canvas, cam, a, reach=8, haze=0.25, dots=0.45)
    canvas = canvas * (1 - a) + (l + dim) * a
    rim = fill(cam, discs=[(cx, cy, R + 0.8)]) - fill(cam, discs=[(cx, cy, R - 1.4)])
    canvas = canvas * (1 - 0.6 * np.clip(rim, 0, 1) * a) + 0.03 * 0.6 * np.clip(rim, 0, 1) * a
    return canvas, a


def square(cx, cy, h, ang=0.0):
    return [(cx + h * math.cos(ang + a) * 1.41, cy + h * math.sin(ang + a) * 1.41) for a in (0.785, 2.356, 3.927, 5.498)]


# ------------------------------------------------------------- the gait ---
def gait(t0, t1, hipfn, facefn, rest, trigger, lead, dur, lift, maxstride=75.0, init=None):
    """planted-foot locks (#33): each foot has a rest slot hip + face*rest[j]. A planted foot
    stays exactly where it is until its slot has drifted more than `trigger` away; then it
    swings (one foot at a time) to where the slot will be at landing, plus `lead` in the
    direction of travel, stride capped at `maxstride` (0.75 m)."""
    f0 = facefn(t0)
    feet = [hipfn(t0) + f0 * rest[0], hipfn(t0) + f0 * rest[1]] if init is None else list(init)   # repair 1: feet carried across segments
    swing = [None, None]
    out, plants = {}, []
    dt = 1 / 240
    n = int(round((t1 - t0) / dt))
    for i in range(n + 1):
        t = t0 + i * dt
        hx, fc = hipfn(t), facefn(t)
        if swing[0] is None and swing[1] is None:
            err = [abs(feet[j] - (hx + fc * rest[j])) for j in range(2)]
            j = int(np.argmax(err))
            if err[j] > trigger:
                ta = min(t + dur, t1)
                v = hipfn(ta) - hipfn(max(t0, ta - 0.05))
                sg = 0 if abs(v) < 1e-3 else (1 if v > 0 else -1)
                tgt = hipfn(ta) + facefn(ta) * rest[j] + sg * lead
                tgt = feet[j] + max(-maxstride, min(maxstride, tgt - feet[j]))
                swing[j] = (t, feet[j], tgt)
        pos = []
        for j in range(2):
            if swing[j] is not None:
                ts, x0, tgt = swing[j]
                u = (t - ts) / dur
                if u >= 1:
                    feet[j] = tgt
                    swing[j] = None
                    plants.append((round(t, 3), j))
                    pos.append((feet[j], 0.0, True))
                else:
                    e = u * u * (3 - 2 * u)
                    pos.append((x0 + (tgt - x0) * e, lift * math.sin(math.pi * u), False))
            else:
                pos.append((feet[j], 0.0, True))
        k = round(t * FPS, 6)
        if abs(k - round(k)) < 1e-6:
            out[int(round(k))] = pos
    out["_end"] = list(feet)
    return out, plants


def lerp(a, b, u):
    return a + (b - a) * u


S = M.sstep
SP = M.SP


# ------------------------------------------------------------ scene state ---
def drag_bottom():
    return GROUND - M.RUNNER_H


def roll_frame(t):
    k = int(round((t - 13.0) * FPS))
    return M.ROLL[min(max(k, 0), max(M.ROLL))]


def counter_frame(t):
    k = int(round((t - 34.0) * FPS))
    return M.COUNTER[min(max(k, 0), max(M.COUNTER))]


def stone_state(t):
    """returns dict: front F, xb, bottom, tilt, pivot, mode"""
    if t < 13.0:
        F = M.drag_front(t) if t >= 4.0 else M.X0
        tilt = math.radians(1.0) * SP["stone_rock"](t) if t >= 4.0 else 0.0
        return dict(mode="drag", F=F, xb=F - SL, bottom=drag_bottom(), tilt=tilt, pivot=(SL * 0.85, 0.0))
    if t < 25.0:
        fr = roll_frame(t)
        F = fr["F"]
        xb = F - SL
        if t < M.DROP_T:
            lift = 52.0 * S((t - M.LIFT_T[0]) / (M.LIFT_T[1] - M.LIFT_T[0]))
            bottom = GROUND - lift
            tilt = SP["stone_settle_tilt"](t) * 0.25
            return dict(mode="shot2", F=F, xb=xb, bottom=bottom, tilt=tilt, pivot=(SL / 2, 0.0), fr=fr)
        tops = []
        for n, s in fr["logs"].items():
            if s["state"] == "carried":
                tops.append(M.LOGS[n].top(s["th"]))
        bottom = min(tops) - SP["stone_bounce"](t) * 0.05
        tilt = SP["stone_settle_tilt"](t) * 0.25 + math.radians(1.0) * SP["stone_rock"](t)
        return dict(mode="roll", F=F, xb=xb, bottom=bottom, tilt=tilt, pivot=(SL / 2, 0.0), fr=fr)
    if t < 34.0:
        F = M.wheel_front(t) if t >= M.W_T0 else M.X0
        return dict(mode="wheel", F=F, xb=F - SL, bottom=plat_top(), tilt=0.0, pivot=(SL / 2, 0.0))
    fr = counter_frame(t)
    F = fr["F"]
    return dict(mode="counter", F=F, xb=F - SL, bottom=plat_top(), tilt=0.0, pivot=(SL / 2, 0.0), fr=fr)


def plat_top():
    return GROUND - 2 * M.R_WHEEL - M.PLAT_T


def plat_tilt(t):
    """counter-check: after the rear wheel rolls out the platform's rear drops to the ground,
    pivoting on the front wheel's top; overshoot from the drop spring (#41)"""
    if t < 34.0:
        return 0.0
    fr = counter_frame(t)
    if fr["drop_t"] is None:
        return 0.0
    pl = fr["F"] - SL - M.PLAT_OFF
    lever = fr["wx"][1] - pl
    full = math.asin(min(0.95, (2 * M.R_WHEEL) / max(lever, 1.0)))
    u = (t - fr["drop_t"]) / M.DROP_DUR      # repair 2: uniform acceleration over 0.30 s (7 frames)
    ang = full * min(1.0, u * u) if u < 1 else full
    over = SP["plat_drop"](t) * 0.035
    return -(ang - abs(over))


# --------------------------------------------------------------- figures ---
PS, CS = 1.06, 1.06          # puppet scales (repair 1: larger, ~33 % of frame height)
HIP_RAISE = 9.0              # hips lifted so the longer legs stand, not crouch
PH_OFF = {"drag": 86.0, "roll": 88.0, "wheel": 74.0, "counter": 74.0, "shot2": 86.0}


def pusher_hip_x(t):
    st = stone_state(t)
    if t < 4.0:
        tgt = M.X0 - SL - PH_OFF["drag"]
        return lerp(-90.0, tgt, S((t - 0.4) / 3.5))
    if t >= 38.0:
        st = stone_state(37.9)
    return st["xb"] - PH_OFF[st["mode"]]


def carrier_hip_x(t):
    if t < 4.0:
        return lerp(40.0, M.X0 + 150.0, S((t - 0.0) / 4.0))
    if t < 13.0:
        return M.drag_front(t) + 150.0
    if t < 14.0:
        return M.X0 + 175.0 - 20 * S((t - 13.0) / 0.5)
    if t < 21.0:
        # 14.0-15.2 walk right to log D lying at x 860; pick up 15.2-15.8; carry it back left;
        # set down 18.6-19.7 with the log at D_X; stand, step back
        if t < 15.2:
            return lerp(M.X0 + 155.0, 672.0, S((t - 14.0) / 1.2))
        if t < 15.9:
            return 672.0
        if t < 18.4:
            return lerp(672.0, M.D_X + 92.0, S((t - 15.9) / 2.5))
        if t < 19.8:
            return M.D_X + 92.0
        return M.D_X + 92.0 + 120 * S((t - 19.85) / 1.5)
    if t < 25.0:
        return M.D_X + 212.0
    if t < 34.0:
        F = M.wheel_front(t) if t >= M.W_T0 else M.X0
        # repair 2: the carrier stays ahead of the load the whole trial (no half-occlusion behind the stone)
        return F + 100.0
    if t < 38.0:
        fr = counter_frame(t)
        base = fr["F"] - SL - M.PLAT_OFF + M.WHEEL_REL[1] + 40.0
        return base if t < 34.9 else base + 70 * S((t - 34.9) / 0.6)
    return carrier_hip_x(37.95)


SEGS = [(0.0, 4.0), (4.0, 13.0), (13.0, 14.0), (14.0, 25.0), (25.0, 34.0), (34.0, 38.0), (38.0, 44.0)]


def carrier_face(t):
    if t < 13.0:
        return 1
    if t < 14.0:
        return -1
    if t < 15.9:
        return 1
    if t < 25.0:
        return -1
    if t < 34.0:
        return 1
    return -1


P_GAIT, C_GAIT, PLANTS = {}, {}, {"pusher": [], "carrier": []}
RESET_T = (13.0, 25.0, 34.0)       # trial resets are real cuts (held black): feet start fresh there
p_end = c_end = None
for (a, b) in SEGS:
    trig = 12 if a == 4.0 else 22
    if a in RESET_T:
        p_end = c_end = None
    g, pl = gait(a, b, pusher_hip_x, lambda t: 1, (-4, -58), trig, 8, 0.24 if a == 4.0 else 0.19, 10 * PS, maxstride=75, init=p_end)
    p_end = g.pop("_end")
    P_GAIT.update(g)
    PLANTS["pusher"] += pl
    g, pl = gait(a, b, carrier_hip_x, carrier_face, (18, -28), 22, 8, 0.20, 9 * CS, maxstride=75, init=c_end)
    c_end = g.pop("_end")
    C_GAIT.update(g)
    PLANTS["carrier"] += pl


def feet_of(G, k, s):
    f = G[k]
    return [(f[0][0], GROUND - 3 - f[0][1]), (f[1][0], GROUND - 3 - f[1][1])], [f[0][2], f[1][2]]


def pusher(t, k, stone):
    st = stone
    T = stone_T(st["xb"], st["bottom"], st["tilt"], st["pivot"])
    feet, planted = feet_of(P_GAIT, k, PS)
    nod = SP["nod"](t)
    head_kind, head_face, hand_kind = "fwd", 1, ("open", "open")
    knee = (-1, -1)
    if t < 4.0:
        walk = 1.0 if S((t - 0.4) / 3.5) < 1 else 0.0
        hip = (pusher_hip_x(t), 464 + 2 * math.sin(t * 2 * math.pi / 0.6) * walk)
        u = S((t - 3.4) / 0.6)
        hy = [lerp(-70, -80, u), lerp(-55, -60, u)]
        hands = [lerp2((hip[0] + 40, hip[1] + 10), T(stone_back_x(hy[0]) + 1.5, hy[0]), u),
                 lerp2((hip[0] + 30, hip[1] + 20), T(stone_back_x(hy[1]) + 1.5, hy[1]), u)]
        lean = lerp(12, 40, u)
        return dict(hip=hip, lean1=lean, lean2=lean + 6, head=-14 + nod, feet=feet, hands=hands, head_kind="fwd",
                    head_face=1, hand_kind=("grip", "grip") if u < 0.5 else ("open", "open"), planted=planted, pinned=u >= 1)
    if t >= 38.0:
        return sit_pose(t, pusher_hip_x(37.9), feet, PS, base_t=38.5, face=1)
    mode = st["mode"]
    if mode in ("drag", "shot2"):
        hy = [-80, -60]
        strain = 1.0
        lean = 40 + 2.5 * math.sin(t * 2 * math.pi / 0.75)
        hip = (pusher_hip_x(t), 470 - 2.0 * strain)
        head = -22 + nod
        if mode == "shot2":
            # heave: the lever is the body - hands under the rear lip, lifting
            u = S((t - 13.05) / 0.12) * (1 - S((t - 13.65) / 0.3))
            hy = [lerp(-80, -44, u), lerp(-60, -36, u)]
            lean = lerp(40, 28, u)
            hip = (pusher_hip_x(t), 470 + 10 * u)
            head = -10
            hand_kind = ("grip", "grip")
    elif mode == "roll":
        hy = [-80, -60]          # repair 1: same stone-local hand height as drag and wheel
        lean = 38
        hip = (pusher_hip_x(t), 468)
        head = -24 + nod
        a_stop = M.A_STOP[0]
        if a_stop + 0.35 <= t < a_stop + 1.6:
            head_kind, head_face, head = "fwd", -1, 12          # turns to look at the log left behind
    else:
        hy = [-80, -60]
        lean = 30 if mode == "wheel" else 34
        bob = 0.0
        if mode == "wheel" and M.W_T0 <= t <= M.W_T1:
            bob = 3.0 * abs(math.sin(t * math.pi * 2.0))
        hip = (pusher_hip_x(t), 462 - bob)
        head = -16 + nod
        if mode == "counter":
            # the pin: right hand goes to the rear fork pin, pulls it out (34.2-34.7)
            fr = st["fr"]
            pl = st["xb"] - M.PLAT_OFF
            pinp = (pl + M.WHEEL_REL[0] + 2, GROUND - M.R_WHEEL - 1)
            u = S((t - 34.15) / 0.3) * (1 - S((t - 34.75) / 0.3))
            if fr["drop_t"] is not None and t > fr["drop_t"]:
                head_kind = "bow"
                head = 10
            hands0 = T(stone_back_x(hy[0]) + 1.5, hy[0])
            pull = S((t - 34.45) / 0.25) * 22
            hands = [hands0, lerp2(T(stone_back_x(hy[1]) + 1.5, hy[1]), (pinp[0] - pull, pinp[1] - pull * 0.6), u)]
            ang = math.radians(SP["stone_rock"](t))
            Tt = T
            if plat_tilt(t) != 0.0:
                Tt = stone_T_counter(t, st)
                hands = [Tt(stone_back_x(hy[0]) + 1.5, hy[0]), Tt(stone_back_x(hy[1]) + 1.5, hy[1])]
            return dict(hip=hip, lean1=lean, lean2=lean + 6, head=head, feet=feet, hands=hands, head_kind=head_kind,
                        head_face=1, hand_kind=("open", "grip" if u > 0.5 else "open"), planted=planted,
                        pinned=u < 0.05, pin=pinp if t < 34.45 else (pinp[0] - pull, pinp[1] - pull * 0.6) if t < 34.75 else None)
    hands = [T(stone_back_x(y) + 1.5, y) for y in hy]
    return dict(hip=hip, lean1=lean, lean2=lean + 6, head=head, feet=feet, hands=hands, head_kind=head_kind,
                head_face=head_face, hand_kind=hand_kind, planted=planted, pinned=True)


def lerp2(p, q, u):
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


def sit_pose(t, hx, feet_walk, s, base_t, face):
    """IK settle: hip lowers to the ground against the wall, knees up, hands on knees"""
    u = S((t - base_t) / 1.3)
    hip = (hx, lerp(455, GROUND - 16, u))
    f0 = (hx + face * lerp(10, 62, u), GROUND - 3)
    f1 = (hx + face * lerp(-70, 44, u), GROUND - 3)
    knee_tgt = (hx + face * 50, GROUND - 70)
    hands = [lerp2((hx + face * 30, 470), (knee_tgt[0] + face * 6, knee_tgt[1] + 6), u),
             lerp2((hx + face * 20, 480), (knee_tgt[0] - face * 4, knee_tgt[1] + 12), u)]
    return dict(hip=hip, lean1=lerp(20, -8, u), lean2=lerp(26, 4, u), head=lerp(-10, 22, u), feet=[f0, f1],
                hands=hands, head_kind="bow" if u > 0.6 else "fwd", head_face=face, hand_kind=("open", "open"),
                planted=[u >= 0.999, u >= 0.999], pinned=False, knee=(-1, -1))


def stone_T_counter(t, st):
    """stone + platform rigid, rotating about the front wheel's top during the drop"""
    fr = st["fr"]
    ang = plat_tilt(t)
    px, py = fr["wx"][1], plat_top() + M.PLAT_T
    c, s_ = math.cos(ang), math.sin(ang)

    def T(x, y):
        X, Y = st["xb"] + x - px, st["bottom"] + y - py
        return (px + X * c - Y * s_, py + X * s_ + Y * c)
    return T


def carrier(t, k, stone):
    feet, planted = feet_of(C_GAIT, k, CS)
    rope = None
    held = None
    face, head_face, head_kind, hand_kind = 1, None, "fwd", ("grip", "grip")
    knee = (-1, -1)
    if t < 4.0:
        hx = carrier_hip_x(t)
        hip = (hx, 462 + 2 * math.sin(t * 2 * math.pi / 0.62))
        u = S((t - 3.4) / 0.6)
        lean = lerp(10, 34, u)
        sh_guess = (hip[0] + 0.6 * 96 * CS * math.sin(math.radians(lean)), hip[1] - 80 * CS)
        hands = [(sh_guess[0] + 10, sh_guess[1] + 22), (sh_guess[0] - 4, sh_guess[1] + 28)]
        nose = (stone["xb"] + SL + 16, GROUND - M.RUNNER_H - 12)
        rope = (nose, hands[1], 18 * (1 - u) + 2)
        return dict(hip=hip, lean1=lean, lean2=lean + 8, head=-12, feet=feet, hands=hands, face=1, head_face=1,
                    head_kind="fwd", hand_kind=hand_kind, planted=planted, rope=rope, held=None, knee=knee)
    if t < 13.0:
        hx = carrier_hip_x(t)
        hip = (hx, 462)
        lean = 36 + 3 * math.sin(t * 2 * math.pi / 0.75 + 1.0)
        sh = (hip[0] + 0.85 * 96 * CS * math.sin(math.radians(lean)), hip[1] - 0.85 * 96 * CS * math.cos(math.radians(lean)))
        hands = [(sh[0] + 8, sh[1] + 20), (sh[0] - 6, sh[1] + 28)]
        nose = (stone["xb"] + SL + 16, GROUND - M.RUNNER_H - 12)
        sag = 2.0 + max(0.0, SP["rope"](t)) * 0.25
        rope = (nose, hands[1], sag)
        return dict(hip=hip, lean1=lean, lean2=lean + 8, head=-8 + SP["nod"](t) * 0.4, feet=feet, hands=hands, face=1,
                    head_face=1, head_kind="fwd", hand_kind=("grip", "grip"), planted=planted, rope=rope, held=None, knee=knee)
    if t < 14.0:
        # crouched in front, facing the stone, rolling the logs in under it (hands on log C)
        fr = roll_frame(t)
        hx = carrier_hip_x(t)
        crouch = S((t - 13.0) / 0.2)
        hip = (hx, lerp(455, 505, crouch))
        c = fr["logs"]["C"]
        tgt = (c["x"] + 8, M.LOGS["C"].cy(c["th"]) - M.R_LOG * 0.8)
        hands = [tgt, (tgt[0] + 10, tgt[1] - 4)]
        return dict(hip=hip, lean1=lerp(10, 48, crouch), lean2=lerp(14, 56, crouch), head=-20, feet=feet, hands=hands,
                    face=-1, head_face=-1, head_kind="fwd", hand_kind=("open", "open"), planted=planted, rope=None,
                    held=None, knee=(-1, -1))
    if t < 25.0:
        hx = carrier_hip_x(t)
        LD = M.LOGS["D"]
        if t < 15.2:
            face = 1
            hip = (hx, 462 + 2 * math.sin(t * 2 * math.pi / 0.6))
            dpos = (712.0, LD.cy(0.6))
            hands = [(hip[0] + 40, hip[1] + 18), (hip[0] + 30, hip[1] + 26)]
            return dict(hip=hip, lean1=18, lean2=24, head=-16, feet=feet, hands=hands, face=1, head_face=1,
                        head_kind="fwd", hand_kind=("open", "open"), planted=planted, rope=None,
                        held=("D", dpos[0], dpos[1], 0.6), knee=knee)
        # pick up (15.2-15.9) facing right, then turn and carry left
        if t < 15.9:
            u = S((t - 15.2) / 0.35) * (1 - S((t - 15.55) / 0.35))
            lift = S((t - 15.5) / 0.4)
            hip = (hx, 462 + 46 * u)
            dpos = (712.0 - 0 * lift, LD.cy(0.6) - 60 * lift)
            hands = [(dpos[0] - LD.R * 0.6, dpos[1] - LD.R * 0.8), (dpos[0] + LD.R * 0.1, dpos[1] - LD.R)]
            return dict(hip=hip, lean1=lerp(18, 55, u), lean2=lerp(24, 62, u), head=-26, feet=feet, hands=hands, face=1,
                        head_face=1, head_kind="fwd", hand_kind=("grip", "grip"), planted=planted, rope=None,
                        held=("D", dpos[0], dpos[1], 0.6), knee=knee)
        face = -1
        crouch = S((t - M.D_SET_T[0]) / (M.D_SET_T[1] - M.D_SET_T[0])) * (1 - S((t - 19.55) / 0.5))
        hip = (hx, 462 + 50 * crouch + (2 * math.sin(t * 2 * math.pi / 0.6) if t < 18.4 else 0))
        sway = sum(SP_sway(t, p) for p, _ in PLANTS["carrier"] if 15.9 < p < 18.4)
        carried = (hip[0] - 66, hip[1] + 6 + sway)
        ground = (M.D_X, LD.cy(0.6))
        u = S((t - M.D_SET_T[0]) / (M.D_SET_T[1] - M.D_SET_T[0]))
        if t < 15.9 + 0.3:
            # turning with the log: it swings from the right side to the left
            v = S((t - 15.9) / 0.3)
            carried = lerp2((712.0, LD.cy(0.6) - 60), carried, v)
        if t < M.D_SET_T[1]:
            dpos = lerp2(carried, ground, u)
            held = ("D", dpos[0], dpos[1], 0.6)
        else:
            dpos = ground
            held = None
        hold = t < M.D_SET_T[1] + 0.25
        if hold:
            hands = [(dpos[0] + LD.R * 0.55, dpos[1] - LD.R * 0.86), (dpos[0] - LD.R * 0.1, dpos[1] - LD.R * 1.0)]
            hk = ("grip", "grip")
        else:
            r = S((t - M.D_SET_T[1] - 0.25) / 0.5)
            hands = [lerp2((dpos[0] + LD.R * 0.55, dpos[1] - LD.R * 0.86), (hip[0] - 22, hip[1] - 20), r),
                     lerp2((dpos[0] - LD.R * 0.1, dpos[1] - LD.R), (hip[0] - 30, hip[1] - 4), r)]
            hk = ("open", "open")
        lean = 26 + 30 * crouch
        head, head_kind, hf = -22 - 18 * crouch, "fwd", -1
        if 20.4 <= t < 22.6:
            head_kind, head = "bow", 4          # looks down at his empty hands / the log left behind
        return dict(hip=hip, lean1=lean, lean2=lean + 10, head=head, feet=feet, hands=hands, face=-1, head_face=hf,
                    head_kind=head_kind, hand_kind=hk, planted=planted, rope=None, held=held, knee=knee, hold=hold)
    if t < 34.0:
        hx = carrier_hip_x(t)
        walking = M.W_T0 <= t <= 32.5
        hip = (hx, 462 - (2.5 * abs(math.sin(t * math.pi * 1.6)) if walking else 0))
        look = S((t - 27.6) / 0.4) * (1 - S((t - 29.2) / 0.4))
        sh = (hip[0] + 0.8 * 96 * CS * math.sin(math.radians(12)), hip[1] - 0.8 * 96 * CS)
        hands = [lerp2((hip[0] + 10, hip[1] + 30), (sh[0] + 34, sh[1] + 6), look),
                 lerp2((hip[0] - 6, hip[1] + 34), (sh[0] + 26, sh[1] + 14), look)]
        head = lerp(-10, 26, look)
        return dict(hip=hip, lean1=12, lean2=14, head=head, feet=feet, hands=hands, face=1, head_face=1,
                    head_kind="bow" if look > 0.5 else "fwd", hand_kind=("open", "open"), planted=planted, rope=None,
                    held=None, knee=knee)
    if t < 38.0:
        hx = carrier_hip_x(t)
        fr = counter_frame(t)
        pl = fr["F"] - SL - M.PLAT_OFF
        pinp = (pl + M.WHEEL_REL[1] - 2, GROUND - M.R_WHEEL - 1)
        u = S((t - 34.1) / 0.3) * (1 - S((t - 34.8) / 0.3))
        crouch = u
        hip = (hx, 462 + 36 * crouch)
        pull = S((t - 34.45) / 0.25) * 20
        hands = [lerp2((hip[0] - 10, hip[1] + 30), (pinp[0] + pull, pinp[1] - pull * 0.5), u),
                 lerp2((hip[0] - 18, hip[1] + 34), (pinp[0] + pull + 4, pinp[1] - pull * 0.5 + 6), u)]
        head_kind = "bow" if (fr["drop_t"] is not None and t > fr["drop_t"] + 0.2) else "fwd"
        return dict(hip=hip, lean1=lerp(10, 44, crouch), lean2=lerp(14, 50, crouch), head=-14 if head_kind == "fwd" else 12,
                    feet=feet, hands=hands, face=-1, head_face=-1, head_kind=head_kind,
                    hand_kind=("grip", "grip") if u > 0.4 else ("open", "open"), planted=planted, rope=None,
                    held=None, knee=(-1, -1), pin=(pinp[0] + pull, pinp[1] - pull * 0.5) if 34.1 < t < 34.75 else None)
    p = sit_pose(t, carrier_hip_x(37.95), feet, CS, base_t=38.9, face=-1)
    return p


def SP_sway(t, tp):
    if t < tp:
        return 0.0
    w = 2 * math.pi * 2.6
    tt = t - tp
    return 2.2 * math.exp(-0.5 * w * tt) * math.sin(w * math.sqrt(1 - 0.25) * tt)


# ---------------------------------------------------------- ghosts / title ---
GH = {}


def ghost(cam, front_m, bottom, seed):
    key = (cam.name, front_m)
    if key not in GH or cam.name not in ("A", "B", "P"):
        xb = M.X0 + front_m * M.PXM - SL
        st = LW.ghost_strokes(M.STONE, xb, bottom, seed)
        a = LW.stroke_alpha(st, width=1.6, seed=seed, shape=(H, W), scale=cam.s, ox=cam.ox, oy=cam.oy)
        poly = fill(cam, polys=[[(x + xb, y + bottom) for x, y in M.STONE]])
        wash = cv2.GaussianBlur(poly, (0, 0), 6 * cam.s) * 0.16
        # write-on order: left to right along x
        xs = np.linspace(0, 1, W)[None, :].repeat(H, 0)
        x0 = (xb - cam.ox) * cam.s / W
        x1 = (xb + SL - cam.ox) * cam.s / W
        out = (wash, a, np.clip((xs - x0) / max(1e-3, x1 - x0), 0, 1))
        if cam.name not in ("A", "B", "P"):
            return out
        GH[key] = out
    return GH[key]


GHOSTS = [(1.2, 11.7, GROUND - M.RUNNER_H, 31), (3.0, 23.15, None, 32), (8.0, 33.35, None, 33)]


def apply_ghosts(canvas, cam, t):
    if cam.name == "B":
        return canvas      # repair 1: at x2.2 the ghost's broken edge read as a stray line across the figures
    for fm, t_on, bottom, seed in GHOSTS:
        if t < t_on:
            continue
        if bottom is None:
            bottom = ghost_bottom(fm)
        wash, a, order = ghost(cam, fm, bottom, seed)
        u = (t - t_on) / 0.8
        rev = np.clip((u * 1.15 - order) * 8, 0, 1) if u < 1 else 1.0
        canvas = canvas * (1 - wash * min(1, u)) + 0.35 * wash * min(1, u)
        aa = a * rev
        sh = np.roll(np.roll(aa, 1, 0), 1, 1)
        canvas = canvas * (1 - 0.10 * sh)
        canvas = canvas * (1 - aa) + 0.97 * aa
    return canvas


def ghost_bottom(fm):
    if fm == 3.0:
        return stone_state(24.9)["bottom"]
    return plat_top()


TITLE = None


def title_layers():
    from PIL import Image
    rub = np.asarray(Image.open(LAY + "title_rub_A.png")).astype(np.float32) / 255
    rev = [np.asarray(Image.open(LAY + f"title_reveal/title_{i:02d}.png")).astype(np.float32) / 255 for i in range(29)]
    return rub, rev


# ------------------------------------------------------------- the props ---
def draw_runner(canvas, cam, F, tilt_T):
    xb = F - SL
    y = GROUND - M.RUNNER_H
    pts = [(xb - 8, GROUND), (F + 4, GROUND), (F + 16, GROUND - 6), (F + 22, GROUND - 18), (F + 14, GROUND - 19),
           (F + 8, GROUND - 10), (F + 2, y), (xb - 8, y)]
    m = painted(cam, fill(cam, polys=[pts]), soft=0.6, rag=0.06)
    canvas = gap(canvas, cam, m, width=1.2)
    canvas = halo(canvas, cam, m, reach=6, haze=0.2, dots=0.4)
    canvas = ink(canvas, m, 0.07)
    sc = strokes(cam, [([(xb, y + 4), (F - 10, y + 5)], 0.9, 0.35)]) * m
    return canvas * (1 - sc) + 0.5 * sc, m


def draw_rope(canvas, cam, rope):
    (x0, y0), (x1, y1), sag = rope
    pts = []
    for u in np.linspace(0, 1, 24):
        pts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + 4 * sag * u * (1 - u)))
    a = strokes(cam, [(pts, 2.3, 1.0)])
    a2 = strokes(cam, [([(x + 0.6, y - 0.6) for x, y in pts[::2]], 0.8, 0.5)]) * a
    canvas = canvas * (1 - a) + 0.05 * a
    return canvas * (1 - a2) + 0.32 * a2


def draw_platform(canvas, cam, T, pins=True, pin_state=None, wheels=None):
    """plank platform with two fork posts holding square axle ends (pinned)"""
    pl0 = -M.PLAT_OFF
    top = 0.0
    plank = [T(pl0, top), T(pl0 + M.PLAT_L, top), T(pl0 + M.PLAT_L + 4, top + M.PLAT_T * 0.5),
             T(pl0 + M.PLAT_L, top + M.PLAT_T), T(pl0, top + M.PLAT_T), T(pl0 - 3, top + M.PLAT_T * 0.5)]
    polys = [plank]
    m = painted(cam, fill(cam, polys=polys), soft=0.6, rag=0.06)
    canvas = gap(canvas, cam, m, width=1.3)
    canvas = halo(canvas, cam, m, reach=7, haze=0.22, dots=0.4)
    canvas = ink(canvas, m, 0.06)
    seams = [([T(pl0 + 4, top + 4), T(pl0 + M.PLAT_L - 6, top + 4.5)], 0.9, 0.4),
             ([T(pl0 + 60, top + 1), T(pl0 + 60, top + M.PLAT_T - 1)], 0.8, 0.35),
             ([T(pl0 + 160, top + 1), T(pl0 + 161, top + M.PLAT_T - 1)], 0.8, 0.35)]
    sc = strokes(cam, seams) * m
    canvas = canvas * (1 - sc) + 0.45 * sc
    return canvas, m


def draw_forks(canvas, cam, T, hubs, pin_out=(False, False)):
    polys, pegs = [], []
    for j, (hx, hy) in enumerate(hubs):
        # fork post from the platform underside to the hub, square axle end, peg pin
        a = T(hx + 7 - (-M.PLAT_OFF) - M.PLAT_OFF, 0)
        polys.append([(hx - 7, hy - M.R_WHEEL + 2 - 0), (hx + 7, hy - M.R_WHEEL + 2), (hx + 6, hy + 4), (hx - 6, hy + 4)])
        polys.append(square(hx, hy, 6.5))
        if not pin_out[j]:
            pegs.append([(hx - 1.5, hy - 12), (hx + 1.5, hy - 12), (hx + 1.2, hy + 12), (hx - 1.2, hy + 12)])
    m = painted(cam, fill(cam, polys=polys + pegs), soft=0.5, rag=0.05)
    canvas = gap(canvas, cam, m, width=1.2)
    canvas = ink(canvas, m, 0.05)
    if pegs:
        pm = fill(cam, polys=pegs)
        canvas = canvas * (1 - 0.7 * pm) + 0.55 * 0.7 * pm
    return canvas, m


# ------------------------------------------------------------ the frame ---
CU = (16.2, 18.8)


# repair 2: wide roller shots push in 0.5 s to x1.28 so the logs read as logs at wide scale;
# the camera pulls back to frame A as the stone stops at 3 m (23.0-23.6 s)
P_S, P_OX, P_OY = 1.28, 0.0, 100.0
PUSH = ((14.0, 14.5, 0.0, 1.0), (14.5, 16.2, 1.0, 1.0), (18.8, 23.0, 1.0, 1.0), (23.0, 23.6, 1.0, 0.0))
MASTER = None
BANDTOP = None
PPLATE = {}


def push_u(t):
    for a, b, u0, u1 in PUSH:
        if a <= t < b:
            return u0 + (u1 - u0) * S((t - a) / (b - a))
    return 0.0


def cam_at(t):
    if CU[0] <= t < CU[1]:
        return CAM_B
    u = push_u(t)
    if u <= 1e-6:
        return CAM_A
    name = "P" if u >= 1 - 1e-6 else f"P{u:.4f}"
    return Cam(name, 1 + (P_S - 1) * u, P_OX * u, P_OY * u, (10.0 + 3.0 * u, -7.0 - 2.0 * u))


def plate_for(cam):
    global MASTER, BANDTOP
    if cam.name in PLATE:
        return PLATE[cam.name]
    if cam.name in PPLATE:
        return PPLATE[cam.name]
    if MASTER is None:
        MASTER = np.load(LAY + "master_lum_x2.2.npy").astype(np.float32)
        BANDTOP = np.load(LAY + "bandtop_A.npy").astype(np.float32)
    lum = LW.to_cam(MASTER, LW.Cam(cam.s, cam.ox, cam.oy))
    lum = lum * (1 - BANDTOP) + PLATE["A"] * BANDTOP      # the top charcoal band stays at screen scale (as in B)
    if cam.name == "P":
        PPLATE["P"] = lum
    return lum


def render(k):
    t = k / FPS
    cam = cam_at(t)
    canvas = plate_for(cam).copy()
    rec = {"k": k, "t": round(t, 4), "cam": cam.name}
    masks = {}
    # shot 0: the wall wakes, title scratched in
    if t < 4.0:
        rub, rev = TITLE_L
        ru = S((t - 0.6) / 0.25)
        canvas = canvas * (1 - rub * ru) + 0.26 * rub * ru
        i = int(np.clip((t - 0.85) / 1.2 * 28, 0, 28)) if t >= 0.85 else -1
        fade_t = 1 - S((t - 3.3) / 0.7)
        if i >= 0:
            a = rev[i] * fade_t
            canvas = canvas * (1 - a) + 0.99 * a
        canvas = canvas * (1 - rub * ru * (1 - fade_t) * 0.0)
    canvas = apply_ghosts(canvas, cam, t)
    st = stone_state(t)
    mode = st["mode"]
    T = stone_T(st["xb"], st["bottom"], st["tilt"], st["pivot"])
    fade = S(t / 1.6) if t < 1.6 else 1.0

    # ------------- props behind the figures
    pp = pusher(t, k, st)
    cc = carrier(t, k, st)
    carrier_behind = (t < 3.7) or mode == "wheel"
    if carrier_behind:
        canvas, m = draw_puppet(canvas, cam, Puppet("carrier", CS, 300).build(
            cc["hip"], cc["lean1"], cc["lean2"], cc["head"], cc["feet"], cc["hands"], face=cc.get("face", 1),
            head_face=cc.get("head_face"), head_kind=cc["head_kind"], hand_kind=cc["hand_kind"]), 3)
        m_car = m
    if mode == "drag":
        if cc.get("rope"):
            canvas = draw_rope(canvas, cam, cc["rope"])
        canvas, m = draw_runner(canvas, cam, st["F"], T)
        canvas, m = draw_stone(canvas, cam, T)
        masks["stone"] = m
    elif mode in ("shot2", "roll"):
        fr = st["fr"]
        cyl = cam is CAM_B
        free_logs = []
        for n in "ABCD":
            s = fr["logs"][n]
            L = M.LOGS[n]
            if n == "D":
                if s["state"] == "held":
                    continue
                th = s["th"]
                x = s["x"]
                cy = L.cy(th)
                end = SP["logD_set"](t) * 0.25
            else:
                th = s["th"]
                x = s["x"]
                end = 0.0
                if n in ("A", "B") and s["state"] == "free":
                    ch = SP["logA_end"] if n == "A" else SP["logB_end"]
                    rock = ch(t) * 0.12
                    th = th + rock
                    x = x + rock * L.R
                    end = ch(t) * 0.5
                cy = L.cy(th)
            canvas, m = draw_log(canvas, cam, L, x, cy, th, seed=ord(n), cyl=cyl, end_mark=end)
            masks["log" + n] = m
        canvas, m = draw_stone(canvas, cam, T)
        masks["stone"] = m
        rec["logs"] = {n: [round(v["x"] or 0, 2), round(v["th"], 4), v["state"]] for n, v in fr["logs"].items()}
    elif mode == "wheel":
        F = st["F"]
        th = (F - M.X0) / M.R_WHEEL
        pl = st["xb"] - M.PLAT_OFF
        hubs = [(pl + M.WHEEL_REL[0], GROUND - M.R_WHEEL), (pl + M.WHEEL_REL[1], GROUND - M.R_WHEEL)]
        for (hx, hy) in hubs:
            canvas, _ = draw_wheel(canvas, cam, hx + 6, hy - 4, th + 0.3, M.R_WHEEL, dim=0.04)        # far wheel
        PT = stone_T(st["xb"], plat_top(), 0.0)
        canvas, mpl = draw_platform(canvas, cam, PT)
        canvas, m = draw_stone(canvas, cam, T)
        masks["stone"] = m
        for j, (hx, hy) in enumerate(hubs):
            canvas, mw = draw_wheel(canvas, cam, hx, hy, th + j * 1.1, M.R_WHEEL)
            masks[f"wheel{j}"] = mw
        canvas, _ = draw_forks(canvas, cam, PT, hubs)
        rec["wheel_theta"] = round(th, 4)
    else:      # counter
        fr = st["fr"]
        Tt = stone_T_counter(t, st)
        hubs = [(fr["wx"][j], GROUND - M.R_WHEEL) for j in range(2)]
        for j, (hx, hy) in enumerate(hubs):
            cb = SP["callback"](t) * 0.12 if j == 0 else 0.0
            canvas, _ = draw_wheel(canvas, cam, hx + 6 + cb * M.R_WHEEL, hy - 4, fr["wth"][j] + 0.3 + cb, M.R_WHEEL, dim=0.04)
        pinned = t < M.PIN_T[1]
        canvas, mpl = draw_platform(canvas, cam, Tt)
        canvas, m = draw_stone(canvas, cam, Tt)
        masks["stone"] = m
        late_wheel = None
        for j, (hx, hy) in enumerate(hubs):
            cb = SP["callback"](t) * 0.12 if j == 0 else 0.0
            if j == 0:
                # repair 2: the near rear wheel is drawn in front of the pusher's legs, so its exit
                # (kicked out behind by the falling platform) reads against the figure, not dark-on-dark
                late_wheel = (hx + cb * M.R_WHEEL, hy, fr["wth"][j] + j * 1.1 + cb)
                continue
            canvas, mw = draw_wheel(canvas, cam, hx + cb * M.R_WHEEL, hy, fr["wth"][j] + j * 1.1 + cb, M.R_WHEEL)
            masks[f"wheel{j}"] = mw
        if pinned:
            pout = (t > 34.45, t > 34.55)
            canvas, _ = draw_forks(canvas, cam, Tt, hubs, pin_out=pout)
        else:
            # the forks have dropped: they lie on the ground under the platform
            fx = [M.X0 - SL - M.PLAT_OFF + M.WHEEL_REL[0] - 18, M.X0 - SL - M.PLAT_OFF + M.WHEEL_REL[1] + 26]
            dropu = S((t - M.PIN_T[1]) / 0.12)
            polys = []
            for j, x in enumerate(fx):
                y = lerp(GROUND - 40, GROUND - 6, dropu)
                polys.append([(x - 16, y - 5 * (1 - dropu)), (x + 16, y - 6 + 6 * dropu), (x + 16, y + 6), (x - 16, y + 6)])
            mf = painted(cam, fill(cam, polys=polys), soft=0.5, rag=0.05)
            canvas = gap(canvas, cam, mf, 1.0)
            canvas = ink(canvas, mf, 0.07)
        rec["plat_tilt_deg"] = round(math.degrees(plat_tilt(t)), 3)
        rec["wheels"] = [[round(x, 2), round(a, 4), s] for x, a, s in zip(fr["wx"], fr["wth"], fr["wst"])]

    # ------------- figures (carrier behind pusher in depth when they overlap)
    seq = [("carrier", cc, Puppet("carrier", CS, 300), 3), ("pusher", pp, Puppet("pusher", PS, 100), 1)]
    for name, P, pup, sd in seq:
        if name == "carrier" and carrier_behind:
            pup.build(P["hip"], P["lean1"], P["lean2"], P["head"], P["feet"], P["hands"], face=P.get("face", 1),
                      head_face=P.get("head_face"), head_kind=P["head_kind"], hand_kind=P["hand_kind"])
            masks[name] = m_car
            rec[name] = {"hand_res": [round(pup.res["hand0"], 3), round(pup.res["hand1"], 3)],
                         "foot_res": [round(pup.res["foot0"], 3), round(pup.res["foot1"], 3)],
                         "feet_xy": [[round(c, 3) for c in pup.res["foot0_xy"]], [round(c, 3) for c in pup.res["foot1_xy"]]],
                         "planted": P["planted"], "pinned": False, "knee_flex": [round(pup.flex["knee0"], 1), round(pup.flex["knee1"], 1)],
                         "head": P["head_kind"], "hands": list(P["hand_kind"]), "drawn_behind_props": True}
            continue
        if name == "carrier" and P.get("held"):
            n, x, y, th = P["held"]
            canvas, m = draw_log(canvas, cam, M.LOGS[n], x, y, th, seed=ord(n), cyl=cam is CAM_B)
            masks["logD"] = m
        pin_h = bool(P.get("pinned")) or bool(P.get("hold")) or bool(P.get("held"))
        parts = pup.build(P["hip"], P["lean1"], P["lean2"], P["head"], P["feet"], P["hands"], face=P.get("face", 1),
                          head_face=P.get("head_face"), head_kind=P["head_kind"], hand_kind=P["hand_kind"],
                          knee_bend=P.get("knee", (-1, -1)), solve_hands=(pin_h, pin_h))
        canvas, m = draw_puppet(canvas, cam, parts, sd)
        masks[name] = m
        rec[name] = {"hand_res": [round(pup.res["hand0"], 3), round(pup.res["hand1"], 3)],
                     "foot_res": [round(pup.res["foot0"], 3), round(pup.res["foot1"], 3)],
                     "feet_xy": [[round(c, 3) for c in pup.res["foot0_xy"]], [round(c, 3) for c in pup.res["foot1_xy"]]],
                     "planted": P["planted"], "pinned": bool(P.get("pinned", False)) or bool(P.get("hold", False)),
                     "knee_flex": [round(pup.flex["knee0"], 1), round(pup.flex["knee1"], 1)],
                     "head": P["head_kind"] + ("-back" if P.get("head_face", P.get("face", 1)) != P.get("face", 1) else ""),
                     "hands": list(P["hand_kind"])}
    if mode == "counter" and late_wheel is not None:
        canvas, mw = draw_wheel(canvas, cam, late_wheel[0], late_wheel[1], late_wheel[2], M.R_WHEEL)
        masks["wheel0"] = mw
    rec["stone"] = {"F": round(st["F"], 3), "bottom": round(st["bottom"], 3), "tilt_deg": round(math.degrees(st["tilt"]), 3)}
    if fade < 1:
        canvas = canvas * fade
    lum = np.clip(canvas, 0, 1)
    rgb = LW.print_rgb(lum, seed=SHOT_SEED(t), amt=3.0)
    return k, rgb, rec, (silhouette_test(lum, masks) if k in SIL_FRAMES else None)


def SHOT_SEED(t):
    for i, (a, b) in enumerate(SHOTS):
        if a <= t < b[0] if isinstance(b, tuple) else False:
            return 500 + i
    for i, sh in enumerate(SHOT_LIST):
        if sh[1] <= t < sh[2]:
            return 500 + i
    return 599


SHOTS = []
SHOT_LIST = [("0_wall_wakes", 0.0, 4.0), ("1_drag", 4.0, 13.0), ("2_substitute_logs", 13.0, 14.0),
             ("3a_rollers_wide", 14.0, 16.2), ("3b_rollers_closeup", 16.2, 18.8), ("3c_carrier_sets_log", 18.8, 21.0),
             ("3d_rollers_on", 21.0, 23.0), ("3e_hold_3m", 23.0, 25.0), ("4_wheel_axle", 25.0, 34.0),
             ("5_counter_no_axle", 34.0, 38.0), ("6_comparison", 38.0, 44.0)]
SIL_FRAMES = {int(round(x * FPS)) for x in (7.0, 8.2, 15.0, 17.5, 19.5, 20.6, 30.0, 36.4)}


def silhouette_test(lum, masks):
    """Reiniger read: greyscale -> threshold (< 0.30 lum). Each figure must be ONE component
    (limbs never detach) and must not share a component with the stone / logs / wheels."""
    dark = (lum < 0.30).astype(np.uint8)
    n, lab = cv2.connectedComponents(dark, connectivity=4)
    out = {}
    for name, m in masks.items():
        own = (m > 0.6)
        if own.sum() == 0:
            continue
        ids, cnt = np.unique(lab[own & (dark > 0)], return_counts=True)
        main = int(ids[np.argmax(cnt)]) if len(ids) else -1
        share = float(cnt.max() / own.sum()) if len(ids) else 0.0
        mm = (m > 0.5).astype(np.uint8)
        ncomp = cv2.connectedComponents(mm, connectivity=8)[0] - 1
        out[name] = {"label": main, "own_mask_components": int(ncomp), "share_in_main_component": round(share, 3)}
    merged = []
    names = list(out)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if out[a]["label"] == out[b]["label"] and out[a]["label"] > 0 and ("pusher" in (a, b) or "carrier" in (a, b)):
                merged.append([a, b])
    return {"objects": out, "figure_merged_with": merged, "frac_below_60": round(float((lum < 0.20).mean()), 4)}


TITLE_L = title_layers()


def main(only=None, stills=()):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT + "stills", exist_ok=True)
    if stills:
        from PIL import Image
        for s in stills:
            k, rgb, rec, sil = render(int(round(float(s) * FPS)))
            Image.fromarray(rgb).save(OUT + f"stills/still_{float(s):05.2f}.png")
        return
    recs, sils = [], {}
    shots = [s for s in SHOT_LIST if only is None or s[0] in only]
    with Pool(4) as pool:
        for name, a, b in shots:
            ks = list(range(int(round(a * FPS)), int(round(b * FPS))))
            path = OUT + f"shot_{name}.mp4"
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12",
                                   "-preset", "medium", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
            for k, rgb, rec, sil in pool.imap(render, ks, chunksize=2):
                ff.stdin.write(rgb.tobytes())
                rec["shot"] = name
                recs.append(rec)
                if sil is not None:
                    sils[f"{k / FPS:.2f}"] = sil
            ff.stdin.close()
            ff.wait()
            print("wrote", path, flush=True)
    with open(OUT + "frames_metrics.json" if only is None else OUT + "frames_metrics_partial.json", "w") as f:
        json.dump({"frames": recs, "silhouette": sils}, f)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        main(stills=sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "--only":
        main(only=sys.argv[2:])
    else:
        main()
