"""quatre-vingt-quinze · U2 puppet-cutter-animator (plan revision r0).

Black cut-paper FK silhouette puppets, a hand-drawn replacement library decoded
by dynamic programming, handmade props, and one exposure sheet per cell A-I.

PUBLIC API (the editor imports this; nothing here takes a route argument):
    layer(cell, frame)      -> RGBA 900x600 PIL image: puppets + props of `cell`
                               at cell-local frame `frame` (24 fps, 0..71; frames
                               >= 72 and None give the page pose). Transparent
                               where the ground (U1) and stencils (U3) show.
                               Eye holes are cut through, so the ground shows in them.
    page_layer(cell)        -> the page pose layer (== layer(cell, None)).
    SHEETS[cell]            -> exposure sheet: list of 72 drawing ids (one per frame).
    EVENTS[cell]            -> cell-local seconds of sound-worthy contacts.
    ANCHORS[cell]           -> speaking mouth / balloon keep-clear boxes (cell px).
    build()                 -> writes exposure.json, joint-errors.json, E-test.mp4,
                               the model sheet and per-cell contact sheets.

Coordinates: cell pixels (900x600, y down). Drawing is done at SS x and reduced.
Time base: 24 frames/s; drawings change on 2s (12 drawings/s); slot = frame // 2.

SCION 2  (Reiniger): backlit cut pieces with fixed scissor-cut edges (seeded per
          piece, never per frame), pinned joints with angle limits, replacement
          profiles, contact planes, exposure sheets.
SCION 32 (FK):      parent @ T(pivot offset) @ R(local angle) per joint; constant
          bone lengths; props attached in the wrist frame at fixed offsets;
          errors-by-joint measured every frame (joint-errors.json).
SCION 38 (pose DP): heads and hands are a library of <=10 drawings per character,
          chosen per slot by a Viterbi decoder over pose features (gaze pitch
          computed from the scene, expression tags, hand state), a transition
          matrix and minimum holds, with protected key poses.
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SRC = FILMS / "sources" / "quatre-vingt-quinze"
MEDIA = SRC / "puppets"
EDMEDIA = SRC / "puppet-cutter-animator"

SS = 3
CW, CH = 900, 600
FPS = 24
NFRAMES = 72          # 3 s per cell
NSLOTS = NFRAMES // 2  # on 2s

SIL = (22, 16, 15, 255)        # #16100f backlit silhouette
INKC = (43, 32, 33, 255)       # #2b2021
RED = (177, 78, 63, 255)       # #b14e3f spot red (cords, thread)
GLASS = (255, 236, 214, 255)   # lit window glass
GLASS_DIM = (178, 118, 102, 255)
GLASS_DARK = (58, 40, 38, 255)
CREAM = (248, 238, 214, 255)   # envelope paper
BRASS = (186, 146, 70, 255)
CLEAR = (0, 0, 0, 0)


# =================================================================== helpers ==
def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def catmull(pts, n=5, closed=True):
    P = list(pts)
    m = len(P)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if (closed or i > 0) else P[0]
        p1, p2 = P[i], P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


_CUTS = {}


def scissor(name, pts, amp=0.55, step=3.0):
    """A piece is cut ONCE: its contour is resampled and pushed off true by a
    smooth seeded wobble that depends only on the piece name (local coords),
    so the same piece is the same paper shape in every frame."""
    key = (name, len(pts), round(pts[0][0], 3), round(pts[0][1], 3))
    if key in _CUTS:
        return _CUTS[key]
    rnd = random.Random(sum(ord(ch) * (i + 1) for i, ch in enumerate(name)))
    ph = [rnd.uniform(0, 6.283) for _ in range(3)]
    fr = [rnd.uniform(0.05, 0.09), rnd.uniform(0.17, 0.26), rnd.uniform(0.4, 0.6)]
    out, s = [], 0.0
    closed = pts + [pts[0]]
    for (x0, y0), (x1, y1) in zip(closed, closed[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        nx, ny = (-(y1 - y0) / L, (x1 - x0) / L) if L else (0, 0)
        for k in range(n):
            u = k / n
            w = amp * (0.6 * math.sin(fr[0] * s + ph[0]) + 0.3 * math.sin(fr[1] * s + ph[1]) + 0.25 * math.sin(fr[2] * s + ph[2]))
            out.append((x0 + (x1 - x0) * u + nx * w, y0 + (y1 - y0) * u + ny * w))
            s += L / n
    _CUTS[key] = out
    return out


# ============================================================ FK transforms ==
def M_T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def M_R(deg):
    """Rotate the local 'down' axis (0,1) toward local +x (forward) by +deg."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], float)


def M_F(f):
    return np.array([[f, 0, 0], [0, 1, 0], [0, 0, 1]], float)


def M_S(k):
    return np.array([[k, 0, 0], [0, k, 0], [0, 0, 1]], float)


def apply(M, pts):
    return [(M[0, 0] * x + M[0, 1] * y + M[0, 2], M[1, 0] * x + M[1, 1] * y + M[1, 2]) for x, y in pts]


def org(M):
    return (float(M[0, 2]), float(M[1, 2]))


def inv_apply(M, p):
    Mi = np.linalg.inv(M)
    return (Mi[0, 0] * p[0] + Mi[0, 1] * p[1] + Mi[0, 2], Mi[1, 0] * p[0] + Mi[1, 1] * p[1] + Mi[1, 2])


# Rigs: bone lengths and pivot offsets (cell px). Joint graph:
#   pelvis -> chest -> neck -> head ; chest -> shoulder{,2} -> elbow -> wrist -> hand -> prop
#   pelvis -> hip{,2} -> knee -> ankle -> shoe
VISITOR = dict(name="visitor", spine=120, neck=16, sh_off=(4, 18), upper=82, fore=74, hip_off=(0, 0), thigh=90, shin=86,
               head_k=1.62, hand_k=1.45)
MAN = dict(name="man", spine=126, neck=16, sh_off=(2, 18), upper=84, fore=76, hip_off=(0, 0), thigh=94, shin=88,
           head_k=1.66, hand_k=1.5)

# Joint-angle limits (degrees, local). Elbows flex forward only; knees flex backward only.
LIMITS = dict(pelvis=(-35, 35), spine=(-28, 28), neck=(-32, 36), sh=(-75, 178), el=(0, 150), wr=(-75, 75),
              hip=(-50, 115), knee=(-150, 6))
LIMIT_LOG = []

BONES = [("pelvis", "chest", "spine"), ("chest", "neck", "neck"),
         ("shoulder", "elbow", "upper"), ("elbow", "wrist", "fore"), ("hip", "knee", "thigh"), ("knee", "ankle", "shin"),
         ("shoulder2", "elbow2", "upper"), ("elbow2", "wrist2", "fore"), ("hip2", "knee2", "thigh"), ("knee2", "ankle2", "shin")]


def solve(rig, pose, root, facing=1, tag=""):
    """Forward kinematics: world = parent @ T(pivot offset) @ R(local angle).
    Angles outside LIMITS are clamped and logged (the rig cannot break a joint)."""
    def g(k):
        v = float(pose.get(k, 0.0))
        lo, hi = LIMITS[k.rstrip("2")]
        if v < lo - 1e-9 or v > hi + 1e-9:
            LIMIT_LOG.append(dict(tag=tag, joint=k, asked=round(v, 2), clamped_to=round(min(hi, max(lo, v)), 2)))
            v = min(hi, max(lo, v))
        return v
    J = {}
    J["root"] = M_T(*root) @ M_F(facing)
    J["pelvis"] = J["root"] @ M_R(g("pelvis"))
    J["chest"] = J["pelvis"] @ M_R(g("spine")) @ M_T(0, -rig["spine"])
    J["neck"] = J["chest"] @ M_R(g("neck")) @ M_T(0, -rig["neck"])
    for s in ("", "2"):
        J["shoulder" + s] = J["chest"] @ M_T(*rig["sh_off"]) @ M_R(g("sh" + s))
        J["elbow" + s] = J["shoulder" + s] @ M_T(0, rig["upper"]) @ M_R(g("el" + s))
        J["wrist" + s] = J["elbow" + s] @ M_T(0, rig["fore"]) @ M_R(g("wr" + s))
        J["hip" + s] = J["pelvis"] @ M_T(*rig["hip_off"]) @ M_R(g("hip" + s))
        J["knee" + s] = J["hip" + s] @ M_T(0, rig["thigh"]) @ M_R(g("knee" + s))
        J["ankle" + s] = J["knee" + s] @ M_T(0, rig["shin"])
    return J


def joint_report(rig, J):
    """Per joint: |bone length - nominal| and pin separation (child pin computed
    through the parent piece's distal pin vs the child piece's own origin)."""
    out = {}
    for a, b, k in BONES:
        pa, pb = org(J[a]), org(J[b])
        bl = abs(math.hypot(pb[0] - pa[0], pb[1] - pa[1]) - rig[k])
        # parent piece's distal pin, in the parent piece frame, is (0, +L) for limbs and (0, -L) for spine/neck
        Lsign = -1 if k in ("spine", "neck") else 1
        if k == "spine":
            parent = J["pelvis"]
        elif k == "neck":
            parent = J["chest"]
        else:
            parent = J[a]
        dp = apply(parent, [(0, Lsign * rig[k])])[0]
        if k == "spine":   # chest rotation is applied before the translation; distal pin is along the rotated axis
            dp = apply(parent @ M_R(_last_angle(J, "pelvis", "chest")), [(0, -rig[k])])[0]
        if k == "neck":
            dp = apply(parent @ M_R(_last_angle(J, "chest", "neck")), [(0, -rig[k])])[0]
        sep = math.hypot(dp[0] - pb[0], dp[1] - pb[1])
        out[f"{a}->{b}"] = dict(bone_err=round(bl, 4), pin_sep=round(sep, 4))
    # shoulders on the chest piece, hips on the pelvis piece
    for s in ("", "2"):
        p_exp = apply(J["chest"], [rig["sh_off"]])[0]
        p = org(J["shoulder" + s])
        out[f"chest->shoulder{s}"] = dict(bone_err=0.0, pin_sep=round(math.hypot(p[0] - p_exp[0], p[1] - p_exp[1]), 4))
    return out


def _last_angle(J, a, b):
    A, B = J[a], J[b]
    R = np.linalg.inv(A) @ B          # = R(theta) @ T(0,-L)
    return math.degrees(math.atan2(R[0, 1], R[0, 0]))


def ik2(shoulder, target, L1, L2, facing, elbow_down=True, chest=None):
    """Analytic two-bone solve for (sh, el) so the wrist lands on target.
    Used only to CHOOSE FK angles (hauling, knocking contact); drawing stays FK."""
    # work in the chest frame so local angles are returned
    sx, sy = shoulder
    tx, ty = target
    lx, ly = inv_apply(chest, (tx, ty)) if chest is not None else (tx - sx, ty - sy)
    ox, oy = inv_apply(chest, (sx, sy)) if chest is not None else (0, 0)
    vx, vy = lx - ox, ly - oy
    d = min(L1 + L2 - 1e-3, max(abs(L1 - L2) + 1e-3, math.hypot(vx, vy)))
    phi = math.degrees(math.atan2(vx, vy))          # angle of the target from local down toward forward
    alpha = math.degrees(math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
    beta = math.degrees(math.acos((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2)))
    # elbow flexes forward (+): upper arm rotates back by alpha, forearm forward by 180-beta
    return phi - alpha, 180 - beta


# ======================================================== drawing library ==
# Replacement heads are hand-placed contours in the neck frame (x forward,
# y down, origin at the neck pin). Each library entry is its own drawing.
V_BASE = [(-8, 5), (-9, -12),                                    # nape
          (-11, -16), (-17, -20), (-14, -23),                     # bob curl under the hat
          (-19, -25), (-24, -29), (-21, -33),                     # cloche brim, turned down at the back
          (-23, -46), (-21, -62), (-12, -74), (2, -79), (17, -78), (28, -70), (34, -58),   # deep bell crown
          (36, -48), (42, -44), (48, -38), (45, -36), (34, -40),  # front brim, flared down over the brow
          (31, -37), (33, -33),                                   # brow under the brim
          (40, -27), (52, -21), (62, -17), (66, -13), (62, -9), (52, -10), (44, -11),   # long nose
          (42, -7), (38, -5), (41, -3),                           # mouth
          (39, 0), (33, 1), (24, -3), (15, -7), (11, -5), (10, 5)]  # chin, jaw, throat
V_EYE = (25, -34)

M_BASE = [(-9, 5), (-10, -12), (-14, -24), (-15, -32),            # nape, back of head (flat)
          (-18, -34), (-19, -46), (-14, -52),                     # cap band and back of crown
          (2, -56), (22, -56), (33, -52), (35, -44),              # flat railway-cap crown
          (37, -43), (50, -40), (50, -36), (34, -36),             # peak (visor)
          (32, -33), (35, -30),                                   # brow
          (46, -26), (58, -20), (66, -12), (66, -5), (60, -3), (52, -8), (45, -10),   # long hooked nose
          (45, -6), (41, -3), (37, -4),                           # moustache
          (39, 2), (35, 6), (27, 4), (17, -2), (11, -3), (10, 5)]  # chin, jaw, throat
M_EYE = (24, -30)


def _rot(pts, deg, pivot=(1, -9)):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(pivot[0] + (x - pivot[0]) * c + (y - pivot[1]) * s, pivot[1] - (x - pivot[0]) * s + (y - pivot[1]) * c) for x, y in pts]


def _pitch(pts, deg, pivot=(1, -9), back_k=1.0):
    """The drawing is re-drawn rigidly turned about the top of the neck; only the
    two neck points at each end stay seated on the neck pin (the neck piece
    overlaps the seam, as a pinned cut-paper head does)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i < 2 or i >= n - 2:
            out.append((x, y))
            continue
        px, py = x - pivot[0], y - pivot[1]
        rx, ry = pivot[0] + px * c + py * s, pivot[1] - px * s + py * c
        if x < -6:
            rx = pivot[0] + (rx - pivot[0]) * back_k
        out.append((rx, ry))
    return out


def _head(base, eye, pitch, edits=None, eye_kind="slit", back_k=1.0):
    pts = list(base)
    for p, q in (edits or {}).items():
        pts[base.index(p)] = q
    return dict(pitch=pitch, pts=_pitch(pts, pitch, back_k=back_k), eye=_pitch([eye], pitch)[0], eye_kind=eye_kind)


HEADS = {
    # visitor: 6 heads
    "v_down": dict(_head(V_BASE, V_EYE, -22), tag="none"),
    "v_level": dict(_head(V_BASE, V_EYE, 0), tag="none"),
    "v_turn": dict(_head(V_BASE, V_EYE, 24, {(38, -5): (36, -5)}), tag="none"),
    "v_up": dict(_head(V_BASE, V_EYE, 50, {(38, -5): (34, -5), (41, -3): (40, -1), (-24, -29): (-21, -28),
                                           (-17, -20): (-14, -19), (48, -38): (49, -40)}, eye_kind="round", back_k=0.92),
                 tag="none"),
    # r1 (editor repair, commissioned per SCION 38 s.7): the skyward head. Her face turned up
    # toward the top edge of the panel (toward B's bell, directly above E on the page).
    # branch-a (r2 repair, explanation A): redrawn further back (70 -> 84) so that, with the startle's
    # straightened spine and the neck thrown back, her nose points straight up / slightly up-left,
    # past the raised key, at the bell's place above the panel. The mouth opens a little (startle).
    "v_sky": dict(_head(V_BASE, V_EYE, 84, {(38, -5): (34, -3), (41, -3): (40, 0), (-24, -29): (-21, -28),
                                           (-17, -20): (-14, -19), (48, -38): (48, -42), (45, -36): (45, -40)},
                        eye_kind="round", back_k=0.86), tag="none"),
    "v_surprise": dict(_head(V_BASE, V_EYE, 8, {(38, -5): (33, -4), (41, -3): (40, 0), (39, 0): (38, 3),
                                               (48, -38): (48, -43), (45, -36): (45, -41), (34, -40): (34, -44),
                                               (31, -37): (31, -40)}, eye_kind="round"), tag="surprise"),
    "v_shrug": dict(_head(V_BASE, V_EYE, -12, {(62, -17): (61, -14), (66, -13): (64, -8), (62, -9): (59, -5),
                                              (38, -5): (39, -5)}, eye_kind="closed"), tag="shrug"),
    # man: 3 heads
    "m_watch": dict(_head(M_BASE, M_EYE, 0), tag="none"),
    "m_effort": dict(_head(M_BASE, M_EYE, 20, {(41, -3): (40, 0), (37, -4): (35, -1), (39, 2): (38, 5)}, eye_kind="closed"),
                     tag="effort"),
    "m_tilt": dict(_head(M_BASE, M_EYE, 10, {(50, -40): (50, -44), (50, -36): (51, -40)}), tag="none"),
}

# Hands, in the wrist frame (+y along the forearm, outward; +x toward the front of the palm).
# Thumbs are cut as separate lobes so grasp poses stay readable in silhouette.
HANDS = {
    "relaxed": [(-6, -2), (-8, 8), (-8, 20), (-4, 28), (2, 30), (6, 26), (7, 18), (9, 14), (14, 16), (13, 10), (8, 4), (7, -2)],
    "pinch": [(-7, -2), (-10, 8), (-9, 18), (-3, 24), (4, 24), (9, 22), (15, 25), (17, 21), (12, 17), (16, 12), (13, 8), (8, 4), (7, -2)],
    "fist": [(-8, -2), (-11, 6), (-11, 16), (-6, 22), (4, 23), (11, 19), (12, 10), (16, 8), (13, 3), (8, -2)],
    "open": [(-6, -2), (-9, 10), (-12, 24), (-9, 25), (-5, 15), (-4, 29), (-1, 29), (0, 16), (3, 28), (6, 27), (5, 14),
             (9, 23), (12, 21), (8, 10), (14, 11), (15, 7), (9, 2), (7, -2)],
    "grip": [(-9, -2), (-12, 6), (-12, 17), (-7, 23), (4, 24), (12, 20), (13, 10), (17, 8), (14, 2), (8, -2)],
}
HAND_PIN = {"pinch": (16, 22), "relaxed": (6, 24), "fist": (6, 14), "grip": (6, 14), "open": (4, 20)}

LIBRARY = {
    "visitor": dict(heads=["v_down", "v_level", "v_turn", "v_up", "v_sky", "v_surprise", "v_shrug"],
                    hands=["relaxed", "pinch", "fist", "open"]),
    "man": dict(heads=["m_watch", "m_effort", "m_tilt"], hands=["grip", "open", "relaxed"]),
}
# r1: the visitor's library grows to 11 by one commissioned drawing (v_sky); the critic's repair
# condition needs a distinct up-turned head and no existing drawing can be dropped (all are used).
assert all(len(v["heads"]) + len(v["hands"]) <= 11 for v in LIBRARY.values())

# coat / jacket pieces
V_COAT = dict(top=[(-28, 0), (-36, 18), (-40, 56), (-40, 96), (-38, 120)],
              hem=[(-44, 0), (-56, 70), (-62, 108), (-22, 114), (22, 116), (58, 108), (50, 62), (40, 0)],
              front=[(36, 122), (36, 96), (38, 64), (36, 36), (22, 6), (10, -2)])
M_JACKET = dict(top=[(-30, 0), (-42, 24), (-44, 70), (-42, 110), (-40, 136)],
                front=[(40, 138), (40, 100), (38, 60), (32, 22), (14, 0)])


# ================================================================ canvas ==
class Layer:
    def __init__(self):
        self.img = Image.new("RGBA", (CW * SS, CH * SS), CLEAR)
        self.d = ImageDraw.Draw(self.img)

    def poly(self, pts, fill=SIL):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)

    def disc(self, c, r, fill=SIL):
        x, y = c
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)

    def line(self, pts, w, fill=RED):
        P = [(x * SS, y * SS) for x, y in pts]
        self.d.line(P, fill=fill, width=max(1, int(w * SS)), joint="curve")
        for x, y in (P[0], P[-1]):
            r = w * SS / 2
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def rect(self, x0, y0, x1, y1, fill=SIL, name=None):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        self.poly(scissor(name, pts, 0.5, 4) if name else pts, fill)

    def done(self):
        return self.img.resize((CW, CH), Image.LANCZOS)


def limb(L, a, b, w0, w1, name, fill=SIL):
    """A tapered cut piece between two pins, with round pin ends (the hinge overlap)."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    Ln = math.hypot(dx, dy) or 1
    # build in the piece's own frame so the scissor wobble travels with it
    loc = [(-w0 / 2, 0), (-w1 / 2, Ln), (w1 / 2, Ln), (w0 / 2, 0)]
    loc = scissor(name + f"{int(Ln)}", loc, 0.4, 4)
    ux, uy = dx / Ln, dy / Ln
    nx, ny = -uy, ux
    pts = [(x0 + nx * px + ux * py, y0 + ny * px + uy * py) for px, py in loc]
    L.poly(pts, fill)
    L.disc(a, w0 / 2, fill)
    L.disc(b, w1 / 2, fill)


def draw_head(L, M, name, rig):
    h = HEADS[name]
    k = rig["head_k"]
    pts = scissor("head_" + name, catmull(h["pts"], 4), 0.25, 1.6)
    L.poly(apply(M @ M_S(k), pts))
    ex, ey = apply(M @ M_S(k), [h["eye"]])[0]
    if name.startswith("v_"):
        # the cloche's hat band: a narrow slit cut through the paper just above the brim
        band = [(-19, -39), (-8, -44), (8, -48), (22, -49), (32, -48)]
        Pb = _rot(band, h["pitch"])
        L.line(apply(M @ M_S(k), Pb), 1.9, CLEAR)
        L.disc(apply(M @ M_S(k), _rot([(-13, -42)], h["pitch"]))[0], 2.8, CLEAR)
    if h["eye_kind"] == "round":
        L.disc((ex, ey), 4.4, CLEAR)
    elif h["eye_kind"] == "closed":
        c = apply(M @ M_S(k), [(h["eye"][0] - 4, h["eye"][1] + 0.5), (h["eye"][0], h["eye"][1] + 2), (h["eye"][0] + 4, h["eye"][1] + 0.5)])
        L.line(c, 1.6, CLEAR)
    else:
        c = apply(M @ M_S(k), [(h["eye"][0] - 4, h["eye"][1]), (h["eye"][0] + 4, h["eye"][1] - 0.8)])
        L.line(c, 3.0, CLEAR)


def draw_hand(L, M, name, rig):
    k = rig["hand_k"]
    L.poly(apply(M @ M_S(k), scissor("hand_" + name, catmull(HANDS[name], 3), 0.3, 2)))


def hand_point(M, name, rig):
    return apply(M @ M_S(rig["hand_k"]), [HAND_PIN[name]])[0]


def shoe(L, ankle, facing, heel=True):
    pts = [(-8, -7), (-10, 6), (-7, 9), (12, 10), (25, 9), (27, 5), (16, 1), (8, -7)]
    ax, ay = ankle
    P = [(ax + facing * x, ay + y) for x, y in scissor("shoe", pts, 0.3, 3)]
    L.poly(P)
    if heel:
        L.poly([(ax + facing * x, ay + y) for x, y in [(-9, 6), (-4, 6), (-4, 13), (-9, 13)]])


def draw_visitor(L, pose, root, facing, head, hand, hand2="relaxed", legs=True, tag="", back_hand_first=True):
    J = solve(VISITOR, pose, root, facing, tag)
    R = VISITOR
    limb(L, org(J["shoulder2"]), org(J["elbow2"]), 25, 20, "v_up2")
    limb(L, org(J["elbow2"]), org(J["wrist2"]), 20, 14, "v_fo2")
    draw_hand(L, J["wrist2"], hand2, R)
    if legs:
        for s in ("2", ""):
            limb(L, org(J["hip" + s]), org(J["knee" + s]), 26, 18, "v_th" + s)
            limb(L, org(J["knee" + s]), org(J["ankle" + s]), 17, 11, "v_sh" + s)
            shoe(L, org(J["ankle" + s]), facing)
    coat = apply(J["chest"], V_COAT["top"]) + apply(J["pelvis"], V_COAT["hem"]) + apply(J["chest"], V_COAT["front"])
    L.poly(scissor("v_coat_" + str(int(pose.get("hip", 0) - pose.get("hip2", 0))), catmull(coat, 3), 0.5, 3))
    limb(L, org(J["chest"]), org(J["neck"]), 24, 19, "v_neck")
    draw_head(L, J["neck"], head, R)
    limb(L, org(J["shoulder"]), org(J["elbow"]), 26, 20, "v_up1")
    limb(L, org(J["elbow"]), org(J["wrist"]), 20, 14, "v_fo1")
    draw_hand(L, J["wrist"], hand, R)
    return J


def draw_man(L, pose, root, facing, head, hand="grip", hand2="grip", legs=True, tag="", front_arm=True):
    J = solve(MAN, pose, root, facing, tag)
    R = MAN
    limb(L, org(J["shoulder2"]), org(J["elbow2"]), 25, 20, "m_up2")
    limb(L, org(J["elbow2"]), org(J["wrist2"]), 20, 15, "m_fo2")
    draw_hand(L, J["wrist2"], hand2, R)
    if legs:
        for s in ("2", ""):
            limb(L, org(J["hip" + s]), org(J["knee" + s]), 30, 23, "m_th" + s)
            limb(L, org(J["knee" + s]), org(J["ankle" + s]), 23, 17, "m_sh" + s)
            shoe(L, org(J["ankle" + s]), facing, heel=False)
    jacket = apply(J["chest"], M_JACKET["top"]) + apply(J["chest"], M_JACKET["front"])
    L.poly(scissor("m_jacket", catmull(jacket, 3), 0.5, 3))
    limb(L, org(J["pelvis"]), org(J["chest"]), 50, 56, "m_trunk")
    limb(L, org(J["chest"]), org(J["neck"]), 24, 20, "m_neck")
    draw_head(L, J["neck"], head, R)
    if front_arm:
        limb(L, org(J["shoulder"]), org(J["elbow"]), 26, 20, "m_up1")
        limb(L, org(J["elbow"]), org(J["wrist"]), 20, 15, "m_fo1")
        draw_hand(L, J["wrist"], hand, R)
    return J


# ================================================================== props ==
FLOOR = 568   # contact plane of every standing cell (cell px)
_KEY = None


def key_source():
    """U3's density cut of the CC0 key photograph if it has been delivered,
    else the test shot's cut of the same photograph (same recipe)."""
    for p in (SRC / "forage" / "key_cut.png", SRC / "test-shot" / "key_cut.png"):
        if p.exists():
            return p
    raise FileNotFoundError("key_cut.png")


def key_img():
    global _KEY
    if _KEY is None:
        _KEY = Image.open(key_source()).convert("RGBA")
    return _KEY


def paste_key(L, M, bow, length=96, rot=0.0):
    """Paste the key with its bow hole centred on world point `bow`, blade
    pointing along the local +y axis of frame M rotated by `rot` degrees.
    Returns (bow, tip) in world px. The key image has its blade up, bow at
    0.82 of its height."""
    k = key_img()
    sc = length * SS / k.size[1]
    kimg = k.resize((max(1, int(k.size[0] * sc)), max(1, int(k.size[1] * sc))), Image.LANCZOS)
    dx, dy = M[0, 1], M[1, 1]             # world direction of local +y
    ang = math.degrees(math.atan2(dx, dy)) + rot   # 0 = pointing down
    # PIL rotates counter-clockwise; image 'up' must become direction ang from down
    pil_rot = ang - 180
    r = kimg.rotate(pil_rot, resample=Image.BICUBIC, expand=True)
    w, h = kimg.size
    # bow centre offset from image centre (image coords: +0.32 h below centre)
    ox, oy = 0, 0.32 * h
    a = math.radians(pil_rot)
    rx, ry = ox * math.cos(a) + oy * math.sin(a), -ox * math.sin(a) + oy * math.cos(a)
    cx, cy = bow[0] * SS - rx, bow[1] * SS - ry
    L.img.alpha_composite(r, (int(round(cx - r.size[0] / 2)), int(round(cy - r.size[1] / 2))))
    ua = math.radians(ang)
    tip = (bow[0] + math.sin(ua) * length * 0.82, bow[1] + math.cos(ua) * length * 0.82)
    return bow, tip


def paste_key_flat(L, bow, direction_deg, length=84):
    """Key lying on a surface: blade pointing toward direction_deg (0=right)."""
    M = M_R(90 - direction_deg + 0.0) if False else None
    ang = direction_deg
    # blade direction vector
    vx, vy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    M = np.array([[0, vx, 0], [0, vy, 0], [0, 0, 1]], float)
    return paste_key(L, M, bow, length)


def thread(L, pts, w=3.0):
    L.line(catmull(pts, 6, closed=False) if len(pts) > 2 else pts, w, RED)


def hang(a, b, sag, n=14):
    (x0, y0), (x1, y1) = a, b
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, n)]


def glint(L, x, y, r):
    for a, k in ((0, 1), (90, 1), (45, 0.45), (135, 0.45)):
        dx, dy = math.cos(math.radians(a)) * r * k, math.sin(math.radians(a)) * r * k
        n = 9
        for i in range(n + 1):
            u = i / n
            px, py = x - dx + 2 * dx * u, y - dy + 2 * dy * u
            rr = 2.6 * math.sin(math.pi * u) ** 0.7 + 0.3
            L.disc((px, py), rr, (255, 251, 236, 255))


def door(L, x0, y0, x1, y1, window=None, glass=GLASS, knob_side="left", name="door"):
    L.rect(x0, y0, x1, y1, SIL, name)
    if window:
        wx0, wy0, wx1, wy1 = window
        L.rect(wx0, wy0, wx1, wy1, glass, name + "_glass")
        mx = (wx0 + wx1) / 2
        L.rect(mx - 3.5, wy0 - 1, mx + 3.5, wy1 + 1, SIL)
    kx = x0 + 20 if knob_side == "left" else x1 - 20
    L.disc((kx, (y0 + y1) / 2 + 24), 6.5, (236, 214, 190, 255))


def bench(L, x, y, w, name="bench"):
    """Handmade cut bench: seat at height y, backrest above, four legs to the floor."""
    L.rect(x, y, x + w, y + 15, SIL, name + "_seat")
    L.rect(x + 8, y - 66, x + w - 8, y - 53, SIL, name + "_back")
    for lx in (x + 20, x + w - 34):
        L.poly(scissor(name + "_leg", [(lx, y + 12), (lx + 13, y + 12), (lx + 15, FLOOR), (lx + 1, FLOOR)], 0.3, 4))
        L.rect(lx + 3, y - 56, lx + 11, y + 2, SIL)


def floor_line(L, y=FLOOR, x0=0, x1=CW):
    L.line([(x0, y + 1), (x1, y)], 3.6, INKC)


def envelope(L, M, state, w=64, h=42):
    """Cream envelope held in the wrist frame M (centre at local (14, 24)).
    state: 'sealed' | 'torn1' | 'torn2' (flap torn off, mouth open)."""
    c = (14, 30)
    # build in a local frame where x is along the envelope's width
    E = M @ M_T(*c) @ M_R(-90)
    body = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    if state == "torn1":
        body = [(-w / 2, -h / 2), (w / 4, -h / 2), (w / 3, -h / 2 + 6), (w / 2 - 4, -h / 2 + 3), (w / 2, -h / 2 + 10),
                (w / 2, h / 2), (-w / 2, h / 2)]
    if state == "torn2":
        body = [(-w / 2, -h / 2 + 8), (-w / 4, -h / 2 + 4), (0, -h / 2 + 9), (w / 4, -h / 2 + 3), (w / 2, -h / 2 + 8),
                (w / 2, h / 2), (-w / 2, h / 2)]
    P = apply(E, scissor("env_" + state, body, 0.35, 3))
    L.poly(P, INKC)
    Pin = apply(E, [(x * 0.93, y * 0.9) for x, y in body])
    L.poly(Pin, CREAM)
    if state == "sealed":
        L.line(apply(E, [(-w / 2 + 3, -h / 2 + 3), (0, 4), (w / 2 - 3, -h / 2 + 3)]), 2.2, INKC)
        L.disc(apply(E, [(0, 4)])[0], 4.0, RED)   # the red wax seal
    else:
        L.line(apply(E, [(-w / 2 + 4, -h / 2 + 10), (w / 2 - 4, -h / 2 + 10)]), 1.8, INKC)


# ========================================================= pose decoding ==
def viterbi(n, lib, emit, trans, min_hold=2, protect=None):
    """SCION 38 decoder. States are (drawing, run) with run capped at min_hold;
    a drawing may change only after it has been shown min_hold slots (the very
    first run counts as already held). protect = {slot: drawing} are hard."""
    protect = protect or {}
    INF = 1e18
    S = [(d, r) for d in lib for r in range(1, min_hold + 1)]
    cost = {}
    for d, r in S:
        ok = (r == min_hold) and (protect.get(0, d) == d)
        cost[(d, r)] = emit(0, d) if ok else INF
    back = []
    for i in range(1, n):
        new, bp = {}, {}
        for (d, r) in S:
            if protect.get(i, d) != d:
                new[(d, r)] = INF
                bp[(d, r)] = None
                continue
            best, arg = INF, None
            for (d0, r0), v in cost.items():
                if v >= INF:
                    continue
                if d0 == d:
                    if min(r0 + 1, min_hold) != r:
                        continue
                    tr = 0.0
                else:
                    if r != 1 or r0 < min_hold:
                        continue
                    tr = trans(d0, d)
                if v + tr < best:
                    best, arg = v + tr, (d0, r0)
            new[(d, r)] = best + emit(i, d) if arg else INF
            bp[(d, r)] = arg
        back.append(bp)
        cost = new
    # the run that ends the sheet must also be a full hold (page pose is held)
    end = min((s for s in S if s[1] == min_hold), key=lambda s: cost[s])
    path = [end]
    for bp in reversed(back):
        path.append(bp[path[-1]])
    path.reverse()
    return [p[0] for p in path], cost[end]


HEAD_TRANS = {("v_down", "v_level"): 1, ("v_level", "v_down"): 1, ("v_level", "v_turn"): 1, ("v_turn", "v_up"): 1,
              ("v_up", "v_turn"): 2, ("v_turn", "v_sky"): 1, ("v_sky", "v_up"): 1, ("v_up", "v_sky"): 2, ("v_sky", "v_turn"): 1, ("v_turn", "v_level"): 1, ("v_down", "v_turn"): 3, ("v_down", "v_up"): 80, ("v_level", "v_up"): 60, ("v_level", "v_surprise"): 2,
              ("v_down", "v_surprise"): 2, ("v_surprise", "v_level"): 3, ("v_level", "v_shrug"): 2, ("v_down", "v_shrug"): 2,
              ("v_shrug", "v_level"): 3, ("m_watch", "m_tilt"): 1, ("m_tilt", "m_effort"): 1, ("m_effort", "m_tilt"): 1,
              ("m_tilt", "m_watch"): 1, ("m_watch", "m_effort"): 2, ("m_effort", "m_watch"): 2}


def decode_heads(targets, lib, protect=None, min_hold=2):
    """targets: per slot (pitch_deg, tag). Emission: pitch mismatch in 8-degree
    units squared + an expression term (6 if the drawing's tag differs from the
    wanted tag; drawings with a tag are not shown where none is wanted)."""
    def emit(i, d):
        p, tag = targets[i]
        p = min(56.0, max(-30.0, p))   # beyond the library's range means "as far as the drawings go"
        h = HEADS[d]
        e = ((h["pitch"] - p) / 8.0) ** 2
        if h["tag"] != (tag or "none"):
            e += 6.0 if tag and tag != "none" else 9.0
        return e
    trans = lambda a, b: HEAD_TRANS.get((a, b), 30.0)
    return viterbi(len(targets), lib, emit, trans, min_hold, protect)


def decode_hands(wanted, lib, protect=None, min_hold=2):
    """wanted: per slot the hand state the action needs (or a set of acceptable ones)."""
    def emit(i, d):
        w = wanted[i]
        ok = d in w if isinstance(w, (set, tuple, list)) else d == w
        return 0.0 if ok else 10.0
    trans = lambda a, b: 1.0
    return viterbi(len(wanted), lib, emit, trans, min_hold, protect)


def gaze_pitch(J, rig, target):
    """Pose feature: where the eye must look. Pitch of the eye->target ray,
    relative to the neck frame (degrees, + = up), for a profile facing +x."""
    k = rig["head_k"]
    eye = apply(J["neck"] @ M_S(k), [(25, -33)])[0]
    vx, vy = target[0] - eye[0], target[1] - eye[1]
    fwd = apply(J["neck"], [(1, 0)])[0]
    o = org(J["neck"])
    fx, fy = fwd[0] - o[0], fwd[1] - o[1]
    up = apply(J["neck"], [(0, -1)])[0]
    ux, uy = up[0] - o[0], up[1] - o[1]
    return math.degrees(math.atan2(vx * ux + vy * uy, vx * fx + vy * fy))


# ================================================================= walk ==
WALK6 = [  # hand-keyed 6-drawing walk: (hip, knee, hip2, knee2, arm swing)
    (22, -3, -18, -12, -1),
    (12, -12, -8, -44, -0.5),
    (0, -5, 10, -52, 0.3),
    (-18, -12, 22, -3, 1),
    (-8, -44, 12, -12, 0.5),
    (10, -52, 0, -5, -0.3),
]


def walk_root(rig, poses, facing, x0, stance_seq):
    """Contact solve: the stance ankle stays pinned on the floor while the other
    leg swings; the root is moved to honour the pin (no foot slide)."""
    roots = []
    pin = None
    prev_stance = None
    for p, st in zip(poses, stance_seq):
        J0 = solve(rig, p, (0, 0), facing)
        a = org(J0["ankle" + st])
        if pin is None or st != prev_stance:
            if pin is None:
                pin = (x0 + a[0], FLOOR - 10)
            else:
                # the new stance foot lands where it is right now (both feet down at contact)
                Jp = solve(rig, p, roots[-1], facing)
                pin = (org(Jp["ankle" + st])[0], FLOOR - 10)
        root = (pin[0] - a[0], pin[1] - a[1])
        roots.append(root)
        prev_stance = st
    return roots


def stand_root(rig, p, facing, ankle_x, ankle_y=FLOOR - 10, back_x=None):
    """Planted stance: move the root so the front ankle sits on (ankle_x, ankle_y),
    then solve the back leg's hip/knee so its ankle is planted at back_x
    (two-bone, knee bending backward). Mutates p; returns the root."""
    J0 = solve(rig, p, (0, 0), facing)
    a = org(J0["ankle"])
    root = (ankle_x - a[0], ankle_y - a[1])
    if back_x is not None:
        J = solve(rig, p, root, facing)
        H = org(J["hip2"])
        th, sh = rig["thigh"], rig["shin"]
        # local (pelvis-frame) vector to the target, with the facing flip
        vx, vy = (back_x - H[0]) * facing, ankle_y - H[1]
        pel = p.get("pelvis", 0.0)
        d = min(th + sh - 1e-6, math.hypot(vx, vy))
        phi = math.degrees(math.atan2(vx, vy)) - pel
        alpha = math.degrees(math.acos((th * th + d * d - sh * sh) / (2 * th * d)))
        beta = math.degrees(math.acos((th * th + sh * sh - d * d) / (2 * th * sh)))
        p["hip2"] = phi + alpha
        p["knee2"] = -(180 - beta)
    return root


# ============================================================ cell sheets ==
# Each planner returns 36 slot states (12 drawings/s on 2s). Equal consecutive
# states are one held drawing. The last state is the page pose; every sheet
# reaches it by slot 31 at the latest and holds it (2.6-3.0 s).
GAZE_UP_E = (450, -300)    # branch-a: cell B's bell mouth (B x 340-600, pivot 430), above E on the page (cell px)


def _seq(n, keys):
    """Piecewise eased interpolation of numeric dicts keyed at slots."""
    ks = sorted(keys)
    out = []
    for i in range(n):
        if i <= ks[0]:
            out.append(dict(keys[ks[0]]))
            continue
        if i >= ks[-1]:
            out.append(dict(keys[ks[-1]]))
            continue
        lo = max(k for k in ks if k <= i)
        hi = min(k for k in ks if k > i)
        u = smooth((i - lo) / (hi - lo))
        a, b = keys[lo], keys[hi]
        out.append({k: lerp(a[k], b.get(k, a[k]), u) for k in a})
    return out


def _r(d, nd=2):
    return {k: (round(v, nd) if isinstance(v, float) else v) for k, v in d.items()}


# ---------------------------------------------------------------- A ----
A_DOOR = (640, 120, 820, FLOOR)
A_WIN = (676, 160, 784, 262)


def plan_A():
    rig = VISITOR
    arm = dict(sh=26, el=40, wr=-14)
    poses, stance = [], []
    for k in range(12):                       # 2 x the 6-drawing walk
        h, kn, h2, kn2, sw = WALK6[k % 6]
        poses.append(dict(hip=h, knee=kn, hip2=h2, knee2=kn2, spine=5, sh2=-14 * sw, el2=12, neck=2, **arm))
        stance.append("" if (k % 6) < 3 else "2")
    roots = walk_root(rig, poses, 1, 0, stance)
    # where the second cycle ends; shift so the stop lands at pelvis x = 250
    stop = dict(hip=8, knee=-2, hip2=-6, knee2=-2, spine=2, sh2=-6, el2=10, neck=0, **arm)
    J_last = solve(rig, poses[-1], roots[-1], 1)
    a_front = org(J_last["ankle"])[0]
    r_stop = stand_root(rig, dict(stop), 1, a_front + 8, back_x=org(J_last["ankle2"])[0] + 26)
    dx = 250 - r_stop[0]
    states = []
    for k in range(12):
        states.append(dict(pose=_r(poses[k]), root=(round(roots[k][0] + dx, 2), round(roots[k][1], 2)), walk=k % 6))
    for k in range(12, 36):
        p = dict(stop)
        if k >= 18:
            p["spine"] = 4         # a slight lean toward the door window
            p["neck"] = 3
        r = stand_root(rig, p, 1, a_front + 8 + dx, back_x=org(J_last["ankle2"])[0] + 26 + dx)
        states.append(dict(pose=_r(p), root=(round(r[0], 2), round(r[1], 2)), walk=None))
    # heads: look down at the envelope while walking, up at the window once stopped
    targets, hands = [], []
    for k, s in enumerate(states):
        J = solve(rig, s["pose"], s["root"], 1)
        env = org(J["wrist"])
        tgt = (env[0] + 20, env[1] + 30) if k < 14 else ((A_WIN[0] + A_WIN[2]) / 2, (A_WIN[1] + A_WIN[3]) / 2)
        targets.append((gaze_pitch(J, rig, tgt), "none"))
        hands.append("pinch")
    heads, hc = decode_heads(targets, ["v_down", "v_level", "v_turn"], protect={35: "v_level"})
    for s, h in zip(states, heads):
        s["head"], s["hand"], s["hand2"] = h, "pinch", "relaxed"
    return states, dict(head_cost=hc, head_targets=[round(t[0], 1) for t in targets])


def draw_A(L, s):
    door(L, *A_DOOR, window=A_WIN, glass=GLASS, knob_side="left", name="A_door")
    floor_line(L)
    J = draw_visitor(L, s["pose"], s["root"], 1, s["head"], s["hand"], s["hand2"], tag="A")
    envelope(L, J["wrist"], "sealed")
    return [("visitor", VISITOR, J)], {}


# ---------------------------------------------------------------- B ----
B_PIVOT = (430, 150)
BK = 1.3
B_STRIKES = (1.4, 2.6)
B_PULLS = (1.15, 2.35)


def bell_angles(t):
    """Two-link pendulum, scripted from two cord pulls: bell angle th, clapper
    angle ph lagging the bell by 0.08 s and swinging 1.9x as far."""
    def swing(tt):
        th = 0.0
        for p0, amp in ((B_PULLS[0], 24.0), (B_PULLS[1], 18.0)):
            if tt > p0:
                u = tt - p0
                th += amp * math.sin(2 * math.pi * u / 1.0) * math.exp(-u / 1.6) * min(1, u / 0.12)
        return th
    return swing(t), 1.9 * swing(t - 0.08)


def plan_B():
    states = []
    for k in range(36):
        kk = min(k, 31)                # 31 = t 2.583 s, the second strike, is the page pose
        t = kk / 12.0
        th, ph = bell_angles(t)
        taut = any(p0 - 0.1 < t < p0 + 0.25 for p0 in B_PULLS)
        near = any(abs(t - s) < 0.25 for s in B_STRIKES)
        states.append(dict(t=round(t, 4), th=round(th, 3), ph=round(ph, 3), taut=taut, arcs=near))
    return states, {}


def draw_B(L, s):
    th, ph = s["th"], s["ph"]
    px, py = B_PIVOT
    L.poly(scissor("B_wall", [(60, 60), (98, 60), (98, 270), (60, 270)], 0.4, 4))
    L.poly(scissor("B_arm", [(94, 124), (px + 6, 134), (px + 6, 152), (94, 156)], 0.4, 4))
    L.poly(scissor("B_strut", [(98, 230), (240, 140), (256, 150), (100, 252)], 0.4, 4))
    B = M_T(px, py) @ M_R(th)
    lever_end = apply(B, [(-118, -50)])[0]
    L.poly(apply(B, scissor("B_lever", [(-6, -36), (-120, -58), (-118, -42), (-6, -18)], 0.3, 4)))
    sag = 6 if s["taut"] else 66
    cx0, cy0 = lever_end
    cord = [(cx0 + (-20 - cx0) * u, cy0 + 330 * u ** 1.6 + sag * math.sin(math.pi * u)) for u in np.linspace(0, 1, 22)]
    L.line(cord, 5.0, RED)
    body = [(-24, -30), (24, -30), (26, -6), (52, 10), (62, 40), (70, 100), (84, 160), (112, 205), (132, 222),
            (130, 236), (-130, 236), (-132, 222), (-112, 205), (-84, 160), (-70, 100), (-62, 40), (-52, 10), (-26, -6)]
    L.poly(apply(B @ M_S(BK), scissor("B_bell", catmull(body, 3), 0.5, 3)))
    C = B @ M_T(0, 20 * BK) @ M_R(ph - th)
    rod_end = apply(C, [(0, 226 * BK)])[0]
    limb(L, org(C), rod_end, 14, 12, "B_rod")
    L.disc(rod_end, 30)
    # the paper-white slit cut along the bell's shoulder (a cut highlight, not shading)
    sl = apply(B @ M_S(BK), [(30, 30), (40, 70), (50, 110), (64, 150)])
    for (a, b) in zip(sl, sl[1:]):
        pass
    L.line(sl, 4.0, CLEAR)
    if s["arcs"]:
        for k, rr in enumerate((345, 378)):
            for a0, a1 in ((20, 52), (-48, -24)):
                pts = [(px + rr * math.sin(math.radians(a + th)), py + rr * math.cos(math.radians(a + th)))
                       for a in np.linspace(a0, a1, 12)]
                for i, (q0, q1) in enumerate(zip(pts, pts[1:])):
                    w = (5.5 - k) * math.sin(math.pi * (i + 0.5) / (len(pts) - 1)) + 0.6
                    L.line([q0, q1], w, INKC)
    # pin geometry check of the two-link pendulum (bell pin -> clapper pin)
    exp_clapper_pin = apply(B, [(0, 20 * BK)])[0]
    sep = math.hypot(exp_clapper_pin[0] - org(C)[0], exp_clapper_pin[1] - org(C)[1])
    rod = math.hypot(rod_end[0] - org(C)[0], rod_end[1] - org(C)[1]) - 226 * BK
    return [], {"bell->clapper": dict(bone_err=round(abs(rod), 4), pin_sep=round(sep, 4))}


# ---------------------------------------------------------------- C ----
C_DOOR = (560, 40, 840, FLOOR)
C_WIN = (610, 90, 790, 220)
C_KNOCKS = (8, 12, 16)      # contact slots


def _fist_front(rig, p, root, hand="fist"):
    J = solve(rig, p, root, 1)
    pts = apply(J["wrist"] @ M_S(rig["hand_k"]), HANDS[hand])
    return max(x for x, _ in pts)


def plan_C():
    rig = VISITOR
    base = dict(spine=6, neck=0, hip=6, knee=-2, sh2=-6, el2=12)
    ank = 470
    # wrist targets (world) for the knock: hanging, raising, cocked, contact, rebound
    pb = dict(base, sh=8, el=10)
    root = stand_root(rig, pb, 1, ank, back_x=ank - 30)
    base.update(hip2=pb["hip2"], knee2=pb["knee2"])
    J0 = solve(rig, dict(base), root, 1)
    shp = org(J0["shoulder"])
    cocked, contact = (shp[0] + 118, shp[1] - 34), (shp[0] + 140, shp[1] - 16)
    rebound = (shp[0] + 126, shp[1] - 26)
    traj = []
    for k in range(36):
        if k < 2:
            traj.append(None)
        elif k < 6:
            u = (k - 2) / 4
            traj.append((lerp(shp[0] + 50, cocked[0], smooth(u)), lerp(shp[1] + 100, cocked[1], smooth(u))))
        elif k < 19:
            ph = (k - 6) % 4     # 0 cocked .. 2 contact .. 3 rebound (contacts at 8, 12, 16)
            traj.append([cocked, (lerp(cocked[0], contact[0], 0.5), lerp(cocked[1], contact[1], 0.5) - 6), contact, rebound][ph])
        else:
            traj.append(cocked)      # listening, fist still raised at the shut door
    states = []
    for k in range(36):
        p = dict(base)
        if traj[k] is None:
            p.update(sh=8, el=10, wr=0)
            hand = "relaxed"
        else:
            J = solve(rig, dict(p, sh=0, el=0), root, 1)
            sh, el = ik2(org(J["shoulder"]), traj[k], rig["upper"], rig["fore"], 1, chest=J["chest"])
            p.update(sh=sh, el=el, wr=-20)
            hand = "fist"
        if k >= 20:
            p["spine"] = 9   # leans in to listen
            p["neck"] = 4
        states.append(dict(pose=_r(p), root=(round(root[0], 2), round(root[1], 2)), hand_want=hand))
    # put the contact drawings' knuckles exactly on the door face (x = 559)
    shift = 559 - _fist_front(rig, states[C_KNOCKS[0]]["pose"], states[C_KNOCKS[0]]["root"])
    for s in states:
        s["root"] = (round(s["root"][0] + shift, 2), s["root"][1])
    targets = []
    for k, s in enumerate(states):
        J = solve(rig, s["pose"], s["root"], 1)
        tgt = ((C_WIN[0] + C_WIN[2]) / 2, (C_WIN[1] + C_WIN[3]) / 2) if k < 20 else (560, 300)
        targets.append((gaze_pitch(J, rig, tgt), "none"))
    heads, hc = decode_heads(targets, ["v_down", "v_level", "v_turn"])
    hands, _ = decode_hands([s["hand_want"] for s in states], ["relaxed", "fist", "open"], protect={8: "fist", 35: "fist"})
    for s, h, hd in zip(states, heads, hands):
        s["head"], s["hand"], s["hand2"] = h, hd, "relaxed"
        del s["hand_want"]
    return states, dict(head_cost=hc, knock_contact_slots=list(C_KNOCKS),
                        knuckle_x_at_contact=[round(_fist_front(rig, states[k]["pose"], states[k]["root"]), 2) for k in C_KNOCKS])


def draw_C(L, s):
    door(L, *C_DOOR, window=C_WIN, glass=GLASS_DARK, knob_side="left", name="C_door")
    floor_line(L)
    J = draw_visitor(L, s["pose"], s["root"], 1, s["head"], s["hand"], s["hand2"], tag="C")
    return [("visitor", VISITOR, J)], {}


# ---------------------------------------------------------------- D ----
D_DOOR = (600, 30, 830, FLOOR)
D_WIN = (636, 84, 794, 252)
D_BENCH = (110, 480, 430)


def plan_D():
    rig = VISITOR
    seat = (330, 475)
    legs = dict(hip=92, knee=-92, hip2=84, knee2=-80, pelvis=0)
    keys = {0: dict(spine=10, neck=0, sh=40, el=70, wr=-30, sh2=34, el2=78, wr2=-20),
            3: dict(spine=10, neck=0, sh=42, el=72, wr=-30, sh2=34, el2=78, wr2=-20),
            5: dict(spine=11, neck=0, sh=50, el=64, wr=-46, sh2=32, el2=80, wr2=-20),    # tear 1
            7: dict(spine=11, neck=0, sh=60, el=54, wr=-56, sh2=30, el2=82, wr2=-20),    # tear 2
            9: dict(spine=10, neck=0, sh=44, el=74, wr=-34, sh2=30, el2=80, wr2=-20),    # fingers into the mouth
            12: dict(spine=6, neck=0, sh=52, el=96, wr=-20, sh2=22, el2=70, wr2=-10),    # key out
            15: dict(spine=-2, neck=-4, sh=76, el=72, wr=-6, sh2=18, el2=64, wr2=-6),  # key held up before her eyes
            16: dict(spine=-4, neck=-5, sh=78, el=72, wr=-6, sh2=18, el2=64, wr2=-6)}
    body = _seq(36, keys)
    # seat the feet on the floor: solve each knee so its ankle meets the contact line
    for s_ in ("", "2"):
        lo, hi = -92.0, 6.0      # shin from vertical (-92) forward: the ankle rises monotonically
        for _ in range(40):
            mid = (lo + hi) / 2
            J = solve(rig, dict(legs, **{"knee" + s_: mid}), seat, -1)
            if org(J["ankle" + s_])[1] > FLOOR - 10:
                lo = mid   # foot below the floor: swing the shin forward
            else:
                hi = mid
        legs["knee" + s_] = round((lo + hi) / 2, 3)
    states = []
    for k in range(36):
        p = dict(legs, **{n: v for n, v in body[k].items()})
        env = "sealed" if k < 4 else ("torn1" if k < 6 else "torn2")
        key = "none" if k < 9 else ("emerging" if k < 11 else "held")
        u = smooth((k - 10) / 10.0)
        man_x = lerp(905, 742, u)
        states.append(dict(pose=_r(p), root=seat, env=env, key=key, man_x=round(man_x, 2)))
    targets = []
    for k, s in enumerate(states):
        J = solve(rig, s["pose"], s["root"], -1)
        tgt = org(J["wrist2"]) if k < 11 else hand_point(J["wrist"], "pinch", rig)
        p = gaze_pitch(J, rig, (tgt[0], tgt[1] + 10))
        targets.append((p, "surprise" if k >= 14 else "none"))
    heads, hc = decode_heads(targets, ["v_down", "v_level", "v_turn", "v_surprise"], protect={14: "v_surprise", 35: "v_surprise"})
    hands, _ = decode_hands([("pinch" if k >= 4 else {"relaxed", "pinch"}) for k in range(36)], ["relaxed", "pinch", "open"])
    for s, h, hd in zip(states, heads, hands):
        s["head"], s["hand"], s["hand2"] = h, hd, "pinch"
    # the window figure's head: watching (no expression change; he is a shadow on glass)
    return states, dict(head_cost=hc, head_targets=[round(t[0], 1) for t in targets])


def draw_D(L, s):
    door(L, *D_DOOR, window=D_WIN, glass=GLASS, knob_side="left", name="D_door")
    # the capped man's profile on the lit glass, slid in from the right, masked to the glass
    W = Layer()
    Jm = draw_man(W, dict(spine=-3, sh=6, el=20, sh2=4, el2=24), (s["man_x"], 370), -1, "m_watch", "relaxed", "relaxed",
                  legs=False, tag="D_window")
    m = Image.new("L", W.img.size, 0)
    x0, y0, x1, y1 = D_WIN
    ImageDraw.Draw(m).rectangle([(x0 + 4) * SS, (y0 + 4) * SS, (x1 - 4) * SS, (y1 - 4) * SS], fill=255)
    a = np.minimum(np.array(W.img.getchannel("A")), np.array(m))
    # where the man covers the glass he is a shadow; elsewhere nothing
    W.img.putalpha(Image.fromarray(a))
    L.img.alpha_composite(W.img)
    mx = (x0 + x1) / 2
    L.rect(mx - 3.5, y0, mx + 3.5, y1, SIL)
    bench(L, *D_BENCH, name="D_bench")
    floor_line(L)
    J = draw_visitor(L, s["pose"], s["root"], -1, s["head"], s["hand"], s["hand2"], tag="D")
    props = {}
    bow_exp = None
    if s["key"] != "none":
        hp = hand_point(J["wrist"], "pinch", VISITOR)
        if s["key"] == "emerging":
            bow, tip = paste_key(L, J["wrist"], hp, length=88, rot=170)
        else:
            bow, tip = paste_key(L, J["wrist"], hp, length=88, rot=-10)
        thread(L, hang(bow, (bow[0] + 10, bow[1] + 92), 6), 3.0)
        props["key@wrist"] = _prop_err(J["wrist"], bow, HAND_PIN["pinch"], VISITOR)
    envelope(L, J["wrist2"], s["env"])
    if s["key"] == "emerging":       # the bow still in the envelope's mouth: redraw the hand over it
        draw_hand(L, J["wrist"], s["hand"], VISITOR)
    return [("visitor", VISITOR, J), ("man(window)", MAN, Jm)], props


def _prop_err(Mw, bow, pin, rig):
    loc = inv_apply(Mw @ M_S(rig["hand_k"]), bow)
    return dict(bone_err=round(math.hypot(loc[0] - pin[0], loc[1] - pin[1]), 4), pin_sep=0.0)


# ---------------------------------------------------------------- E ----
E_ANKLE = 488
E_KEYS = {
    1: dict(sh=14, el=34, wr=-10, spine=-1, neck=0, knee_dip=0),
    2: dict(sh=6, el=46, wr=-16, spine=4, neck=2, knee_dip=8),        # anticipation
    3: dict(sh=30, el=50, wr=-12, spine=2, neck=0, knee_dip=4),
    4: dict(sh=52, el=46, wr=-8, spine=0, neck=-2, knee_dip=1),
    5: dict(sh=74, el=36, wr=-4, spine=-3, neck=-4, knee_dip=0),
    6: dict(sh=96, el=26, wr=0, spine=-5, neck=-6, knee_dip=0),
    7: dict(sh=112, el=16, wr=4, spine=-7, neck=-7, knee_dip=0),
    8: dict(sh=126, el=10, wr=6, spine=-8, neck=-8, knee_dip=0),
    9: dict(sh=134, el=6, wr=8, spine=-9, neck=-9, knee_dip=0),
    10: dict(sh=142, el=2, wr=10, spine=-11, neck=-10, knee_dip=0),   # overshoot, the glint
    11: dict(sh=135, el=6, wr=7, spine=-9, neck=-9, knee_dip=0),
    12: dict(sh=137, el=4, wr=8, spine=-10, neck=-9, knee_dip=0),     # settle: the page pose
}
E_GLINT = {10: 24, 11: 16, 12: 15}


E_THREAD_BY_POSE = [0, 0, 4, -8, -14, -20, -24, -26, -26, -22, -10, 10, 18]
# r1 retime: (lift pose, head, neck offset) per slot. The camera settles at slot 6 (0.5 s).
#   slots 0-2  rest, key at the chest, looking down at it (held while the camera travels)
#   slot  3    anticipation dip (0.25 s, the camera nearly settled)
#   slots 4-9  the lift: 4 drawings up to the overshoot (glint) at slot 7, settle by slot 9
#   slots 6-19 v_sky: her face turned up to the top edge of the panel (0.50-1.67 s)
#   slots 20-  back to v_up, on the raised key: the page pose; a breath runs through the dwell
E_LIFT = [1, 1, 1, 2, 4, 6, 8, 10, 11, 12] + [12] * 26
E_HEAD = ["v_down"] * 4 + ["v_turn"] * 2 + ["v_sky"] * 14 + ["v_up"] * 16
E_NECK = [0] * 6 + [14] + [22] * 13 + [8] + [0] * 15
# branch-a (r2): the startle under the sky look. The spine straightens back (she draws back from the
# key), the neck throws further back, and the free shoulder hitches with a small flinch of the free
# hand at slot 7 (0.58 s, the glint), easing down by slot 12; all zero again from slot 21, so the
# page pose (slot 35) is exactly r1's. The key arm keeps r1's lift and position on the body.
E_SPINE_ADD = [0] * 6 + [5, 9, 9, 8] + [7] * 10 + [3] + [0] * 15
E_NECK_ADD = [0] * 6 + [6, 12, 12, 11] + [10] * 10 + [4] + [0] * 15
E_SH2_ADD = [0] * 6 + [18, 30, 26, 20, 14, 10, 7] + [5] * 7 + [2] + [0] * 15
E_EL2_ADD = [0] * 6 + [20, 34, 30, 24, 18, 14, 10] + [8] * 7 + [3] + [0] * 15


def e_thread_angle(slot):
    """Red thread hanging from the bow: lags the lift, then a damped swing that
    dies out before the page-pose hold."""
    if slot <= 9:
        return E_THREAD_BY_POSE[E_LIFT[slot]]
    t = (slot - 9) / 12.0
    v = 18 * math.exp(-t / 0.5) * math.cos(2 * math.pi * t / 0.8)
    return 0.0 if slot >= 31 else v


def e_breath(slot):
    """A small breath through the dwell (slots 10-30): weight settles, shoulders rise
    and fall; zero from slot 31 so the page pose is exact."""
    if slot < 10 or slot >= 31:
        return 0.0
    u = (slot - 10) / 21.0
    return math.sin(2 * math.pi * (slot - 10) / 10.0) * (1 - u) ** 1.5


def plan_E():
    rig = VISITOR
    states = []
    for k in range(36):
        d = E_LIFT[k]
        q = dict(E_KEYS[d])
        dip = q.pop("knee_dip")
        br = e_breath(k)
        q["sh"] = q["sh"] + 3.0 * br
        q["spine"] = q["spine"] + 1.4 * br
        q["neck"] = q["neck"] + E_NECK[k] + E_NECK_ADD[k]
        q["spine"] = q["spine"] + E_SPINE_ADD[k]
        dip = dip + 2.0 * max(0.0, -br)
        p = dict(q, hip=6 + dip * 0.6, knee=-dip * 1.3, sh2=-6 + dip * 0.2 + 1.5 * br + E_SH2_ADD[k],
                 el2=14 + E_EL2_ADD[k], pelvis=0)
        root = stand_root(rig, p, 1, E_ANKLE, back_x=E_ANKLE - 34)
        states.append(dict(pose=_r(p), root=(round(root[0], 2), round(root[1], 2)), lift=d,
                           thread=round(e_thread_angle(k), 2), glint=E_GLINT.get(d, 0)))
    targets = []
    for k, s in enumerate(states):
        J = solve(rig, s["pose"], s["root"], 1)
        if k < 4:
            tgt = hand_point(J["wrist"], "pinch", rig)
        elif k < 20:
            tgt = GAZE_UP_E   # the top edge of the panel (B's bell above): she looks up
        else:
            tgt = hand_point(J["wrist"], "pinch", rig)   # back to the raised key
        targets.append((gaze_pitch(J, rig, tgt), "none"))
    protect = {k: h for k, h in enumerate(E_HEAD)}   # the r1 key poses, all protected
    heads, hc = decode_heads(targets, ["v_down", "v_level", "v_turn", "v_up", "v_sky"], protect=protect)
    hands, _ = decode_hands(["pinch"] * 36, ["relaxed", "pinch", "open"], protect={7: "pinch", 35: "pinch"})
    for s, h, hd in zip(states, heads, hands):
        s["head"], s["hand"], s["hand2"] = h, hd, "relaxed"
    return states, dict(head_cost=hc, head_targets=[round(t[0], 1) for t in targets])


def draw_E(L, s):
    floor_line(L)
    J = draw_visitor(L, s["pose"], s["root"], 1, s["head"], s["hand"], s["hand2"], tag="E")
    hp = hand_point(J["wrist"], "pinch", VISITOR)
    bow, tip = paste_key(L, J["wrist"], hp, length=100, rot=18)
    a = math.radians(s["thread"])
    end = (bow[0] + 84 * math.sin(a), bow[1] + 84 * math.cos(a))
    thread(L, hang(bow, end, 5 * math.cos(a)), 3.2)
    draw_hand(L, J["wrist"], s["hand"], VISITOR)     # fingers close over the bow
    if s["glint"]:
        glint(L, tip[0], tip[1], s["glint"])
    return [("visitor", VISITOR, J)], {"key@wrist": _prop_err(J["wrist"], bow, HAND_PIN["pinch"], VISITOR)}


# ---------------------------------------------------------------- F ----
F_BENCH = (300, 480, 400)
F_KEY_BOW = None


def plan_F():
    rig = VISITOR
    states = []
    ank = 404
    keys = {0: dict(spine=4, sh=44, el=24, wr=-10, neck=0),
            2: dict(spine=12, sh=52, el=20, wr=-14, neck=-4),
            4: dict(spine=24, sh=58, el=12, wr=-20, neck=-6),   # the key touches the seat
            5: dict(spine=24, sh=56, el=14, wr=-20, neck=-6),   # released
            7: dict(spine=6, sh=14, el=20, wr=0, neck=0)}
    body = _seq(9, keys)
    for k in range(9):
        p = dict(body[k], hip=6, knee=-2, sh2=-4, el2=12, pelvis=0)
        r = stand_root(rig, p, 1, ank, back_x=ank - 30)
        states.append(dict(pose=_r(p), root=(round(r[0], 2), round(r[1], 2)), facing=1,
                           key="held" if k < 5 else "bench"))
    # the turn: a replacement profile (the mirrored puppet), then one dejected walk cycle out to the left
    walk = []
    stance = []
    for k in range(7):
        h, kn, h2, kn2, sw = WALK6[k % 6] if k < 6 else WALK6[0]
        walk.append(dict(hip=h * 0.72, knee=kn * 0.8, hip2=h2 * 0.72, knee2=kn2 * 0.8, spine=8, neck=2,
                         sh=-12 * sw + 4, el=14, sh2=12 * sw, el2=12, pelvis=0))
        stance.append("" if (k % 6) < 3 else "2")
    J8 = solve(rig, states[-1]["pose"], states[-1]["root"], 1)
    x_start = org(J8["ankle"])[0]
    roots = walk_root(rig, walk, -1, x_start - org(solve(rig, walk[0], (0, 0), -1)["ankle"])[0], stance)
    for k in range(9, 36):
        i = min(k - 9, 6)
        states.append(dict(pose=_r(walk[i]), root=(round(roots[i][0], 2), round(roots[i][1], 2)), facing=-1, key="bench"))
    # the key's resting place: where the hand put it on the seat at the release drawing
    Jr = solve(rig, states[4]["pose"], states[4]["root"], 1)
    bow = hand_point(Jr["wrist"], "pinch", rig)
    global F_KEY_BOW
    F_KEY_BOW = (round(bow[0], 2), F_BENCH[1] - 9)
    targets = []
    for k, s in enumerate(states):
        J = solve(rig, s["pose"], s["root"], s["facing"])
        tgt = F_KEY_BOW if k < 7 else (-200, 300)
        if s["facing"] == -1:
            # the profile faces -x: mirror the target into the puppet's own forward space
            pass
        p = gaze_pitch(J, rig, tgt) if s["facing"] == 1 else 0.0
        targets.append((p if k < 7 else -10.0, "shrug" if k >= 6 else "none"))
    heads, hc = decode_heads(targets, ["v_down", "v_level", "v_shrug"], protect={35: "v_shrug"})
    hands = ["pinch" if k < 5 else ("open" if k < 7 else "relaxed") for k in range(36)]
    hands, _ = decode_hands(hands, ["pinch", "open", "relaxed"], min_hold=2)
    for s, h, hd in zip(states, heads, hands):
        s["head"], s["hand"], s["hand2"] = h, hd, "relaxed"
    return states, dict(head_cost=hc, key_rest_bow=F_KEY_BOW)


def draw_F(L, s):
    bench(L, *F_BENCH, name="F_bench")
    floor_line(L)
    props = {}
    trail = [(700, F_BENCH[1] - 2), (790, 506), (905, 524)]
    if s["key"] == "bench":
        bow, tip = paste_key_flat(L, F_KEY_BOW, 0.0, length=84)
        thread(L, [bow, ((bow[0] + 700) / 2, F_BENCH[1] - 1)] + trail, 3.0)
    J = draw_visitor(L, s["pose"], s["root"], s["facing"], s["head"], s["hand"], s["hand2"], tag="F")
    if s["key"] == "held":
        hp = hand_point(J["wrist"], "pinch", VISITOR)
        bow, tip = paste_key(L, J["wrist"], hp, length=84, rot=-20)
        thread(L, [bow, (bow[0] + 40, F_BENCH[1] - 4), ((bow[0] + 700) / 2 + 30, F_BENCH[1] - 1)] + trail, 3.0)
        draw_hand(L, J["wrist"], s["hand"], VISITOR)
        props["key@wrist"] = _prop_err(J["wrist"], bow, HAND_PIN["pinch"], VISITOR)
    return [("visitor", VISITOR, J)], props


# ---------------------------------------------------------------- G ----
G_ANKLE = 404
G_HI, G_LO = 262, 356   # grip heights on the cord (chest height, clear of the nose)
G_CORD = {}


def g_cord_x(y):
    (tx, ty), (px, py) = G_CORD["top"], G_CORD["floor"]
    return tx + (px - tx) * (y - ty) / (py - ty)


def plan_G():
    rig = MAN
    ank = G_ANKLE
    base = dict(hip=8, knee=-6, pelvis=0, spine=-4, neck=-2)
    pb = dict(base)
    root = stand_root(rig, pb, 1, ank, back_x=ank - 40)
    base.update(hip2=pb["hip2"], knee2=pb["knee2"])
    # the cord is staged in front of his nose: it leaves the panel top right and
    # runs down past his fists to a coil on the floor, never across head or hands
    J0 = solve(rig, dict(base), root, 1)
    sx = org(J0["shoulder"])[0]
    G_CORD["top"] = (sx + 214, -30)
    G_CORD["floor"] = (sx + 120, FLOOR - 2)
    # hand heights per slot: hand-over-hand, 4 drawings per haul, fast down-stroke
    yF, yB, gF, gB, pulled = [], [], [], [], []
    hi, lo = G_HI, G_LO
    f, b = hi, lo           # front hand high, back hand low to start
    gf, gb = "grip", "grip"
    total = 0.0
    for k in range(36):
        h = (k - 2) // 4 if 2 <= k < 18 else None
        j = (k - 2) % 4 if h is not None else None
        if h is not None:
            puller = "F" if h % 2 == 0 else "B"
            yp = [hi + 0.72 * (lo - hi), lo, lo, lo][j]
            yr = [lo, lo - 0.45 * (lo - hi), hi, hi][j]
            gp = "grip"
            gr = ["open", "open", "grip", "grip"][j]
            prev_p = f if puller == "F" else b
            if puller == "F":
                f, b, gf, gb = yp, yr, gp, gr
            else:
                b, f, gb, gf = yp, yr, gp, gr
            total += max(0.0, yp - prev_p)
        yF.append(f)
        yB.append(b)
        gF.append(gf)
        gB.append(gb)
        pulled.append(total)
    states = []
    for k in range(36):
        p = dict(base)
        pull_phase = (2 <= k < 18) and ((k - 2) % 4 in (0, 1))
        p["spine"] = -7 if pull_phase else -3      # leans back into each down-stroke
        J = solve(rig, dict(p, sh=0, el=0, sh2=0, el2=0), root, 1)
        for side, y in (("", yF[k]), ("2", yB[k])):
            tgt = (g_cord_x(y) - 12, y - 10)       # wrist sits just behind the grip on the cord
            sh, el = ik2(org(J["shoulder" + side]), tgt, rig["upper"], rig["fore"], 1, chest=J["chest"])
            p["sh" + side], p["el" + side] = sh, el
            p["wr" + side] = -30
        states.append(dict(pose=_r(p), root=(round(root[0], 2), round(root[1], 2)), yF=round(yF[k], 2), yB=round(yB[k], 2),
                           pulled=round(pulled[k], 2), effort=pull_phase))
    targets = [(24.0 if s["effort"] else 12.0, "effort" if s["effort"] else "none") for s in states]
    targets[-1] = (20.0, "effort")
    prot = {k: "m_effort" for k in range(18, 36)}
    heads, hc = decode_heads(targets, ["m_watch", "m_effort", "m_tilt"], protect=prot)
    hF, _ = decode_hands(gF, ["grip", "open", "relaxed"], min_hold=1)
    hB, _ = decode_hands(gB, ["grip", "open", "relaxed"], min_hold=1)
    for s, h, a, b in zip(states, heads, hF, hB):
        s["head"], s["hand"], s["hand2"] = h, a, b
    return states, dict(head_cost=hc, haul_pull_px_total=round(pulled[-1], 1))


def draw_G(L, s):
    floor_line(L)
    # the cord first, so both fists close over it (it never crosses the head or a hand)
    yl = max(s["yF"], s["yB"])
    lowhand = (g_cord_x(yl), yl)
    G_TOP = G_CORD["top"]
    L.line([G_TOP, lowhand], 6.0, RED)
    # slack: from the lower fist down into a coil on the floor; the coil grows as he hauls
    coil_r = 10 + 0.04 * s["pulled"]
    cx = G_CORD["floor"][0] + 34
    slack = hang(lowhand, (cx - coil_r, FLOOR - 6), 18, 16)
    L.line(slack, 6.0, RED)
    for i in range(3):
        rr = coil_r * (1 - 0.22 * i)
        pts = [(cx + rr * math.cos(t), FLOOR - 6 - 0.32 * rr - 0.3 * rr * math.sin(t) - 4 * i) for t in np.linspace(0, 2 * math.pi, 28)]
        L.line(pts, 5.0, RED)
    # knots on the taut cord travel down with the haul (the cord visibly moves)
    (tx, ty) = G_TOP
    seg = math.hypot(lowhand[0] - tx, lowhand[1] - ty)
    for i in range(6):
        d = (i * 72 + s["pulled"] * 1.0) % (seg + 72) - 36
        if 0 < d < seg - 10:
            u = d / seg
            L.disc((tx + (lowhand[0] - tx) * u, ty + (lowhand[1] - ty) * u), 5.5, RED)
    J = draw_man(L, s["pose"], s["root"], 1, s["head"], s["hand"], s["hand2"], tag="G")
    return [("man", MAN, J)], {}


# ---------------------------------------------------------------- H ----
H_WIN = (700, 40, 830, 160)


def plan_H():
    states = []
    for k in range(36):
        g = "lit" if k < 10 else ("dim" if k < 12 else "dark")
        states.append(dict(glass=g))
    return states, {}


def draw_H(L, s):
    x0, y0, x1, y1 = H_WIN
    L.rect(x0 - 10, y0 - 10, x1 + 10, y1 + 10, SIL, "H_frame")
    L.rect(x0, y0, x1, y1, {"lit": GLASS, "dim": GLASS_DIM, "dark": GLASS_DARK}[s["glass"]], "H_glass")
    mx = (x0 + x1) / 2
    L.rect(mx - 3.5, y0, mx + 3.5, y1, SIL)
    return [], {}


# ---------------------------------------------------------------- I ----
I_DOOR = (330, 30, 640, FLOOR - 14)


def plan_I():
    states = []
    xs = [206, 224, 252, 288, 322, 350]          # bow x for the 6 sliding drawings (jerky pulls)
    for k in range(36):
        if k < 6:
            st = dict(bow_x=206, taut=False)
        elif k < 8:
            st = dict(bow_x=206, taut=True)
        elif k < 20:
            st = dict(bow_x=xs[(k - 8) // 2], taut=True)
        else:
            st = dict(bow_x=xs[-1], taut=True)
        states.append(st)
    return states, {}


def draw_I(L, s):
    floor_line(L)
    bx = s["bow_x"]
    by = FLOOR - 11
    # the loose tail trailing back out of the panel to the left; the taut lead runs into the gap under the door
    thread(L, [(bx - 60, by + 4), (bx - 140, by + 9), (-10, by + 6)], 3.0)
    if s["taut"]:
        L.line([(bx, by), (I_DOOR[2] + 30, by + 1)], 3.0, RED)
    else:
        thread(L, [(bx, by), (bx + 50, by + 8), (I_DOOR[0] - 4, by + 9), (I_DOOR[0] + 30, by + 4)], 3.0)
    # the key lies bow-first toward the door, blade trailing (pointing left)
    paste_key_flat(L, (bx, by - 2), 180.0, length=104)
    # the door is drawn over the key: the part that has slid under it disappears
    door(L, *I_DOOR, window=(380, 80, 590, 200), glass=GLASS_DARK, knob_side="right", name="I_door")
    return [], {}


# ============================================================ the sheets ==
PLANS = dict(A=plan_A, B=plan_B, C=plan_C, D=plan_D, E=plan_E, F=plan_F, G=plan_G, H=plan_H, I=plan_I)
DRAWS = dict(A=draw_A, B=draw_B, C=draw_C, D=draw_D, E=draw_E, F=draw_F, G=draw_G, H=draw_H, I=draw_I)
ACTION = {
    "A": "2 x 6-drawing walk in from the left (stance foot pinned), stop, head replaced from looking down at the envelope to the window",
    "B": "cord pulls at 1.15 and 2.35 s swing the bell; clapper on its own pin lags 0.08 s at 1.9x; strikes 1.4 and 2.6 s; motion arcs near strikes",
    "C": "arm raised by FK, three 4-drawing knocks with knuckles on the door face, then she leans in to listen, fist still raised",
    "D": "2-drawing tear, key drawn out of the envelope's mouth and raised to the face, surprise head (protected), the man's shadow slides into the window",
    "E": "r1: held rest while the camera travels; anticipation dip at 0.25 s; 4-drawing lift to the overshoot+glint at 0.58 s, settle by 0.75 s; skyward head v_sky 0.50-1.67 s, redrawn in branch-a: nose straight up / slightly up-left past the key toward the bell's place, with a startle (spine draws back, neck thrown back, free shoulder hitches and hand flinches at 0.58 s), then v_up on the key (page pose); a breath through the dwell; the thread swings out",
    "F": "4-drawing set-down of the key on the bench, release, shrug head, replacement profile turns her, one dejected walk cycle out left",
    "G": "4 hand-over-hand hauls (fast down-stroke, slower recovery), leaning into each pull; knots travel down the cord; the slack coils at his feet",
    "H": "the door window's light goes out (lit, dim, dark)",
    "I": "thread tightens, the key slides bow-first under the shut door in 6 drawings and stops half under; the door never opens",
}
_PLAN = {}
PLAN_INFO = {}


def plan(c):
    if c not in _PLAN:
        st, info = PLANS[c]()
        assert len(st) == NSLOTS, (c, len(st))
        _PLAN[c] = st
        PLAN_INFO[c] = info
    return _PLAN[c]


def drawing_ids(c):
    """One id per slot; consecutive equal states are the same held drawing."""
    st = plan(c)
    ids, cur = [], None
    for k, s in enumerate(st):
        if k == 0 or json.dumps(s, sort_keys=True) != json.dumps(st[k - 1], sort_keys=True):
            cur = f"{c}{k:02d}"
        ids.append(cur)
    return ids


def sheet(c):
    ids = drawing_ids(c)
    return [ids[f // 2] for f in range(NFRAMES)]


PAGE_DRAWING = {}
_DRAWN = {}
JOINTS = {}


def _render(c, did):
    if did in _DRAWN:
        return _DRAWN[did]
    k = int(did[1:])
    L = Layer()
    figs, props = DRAWS[c](L, plan(c)[k])
    rep = {}
    for name, rig, J in figs:
        for j, e in joint_report(rig, J).items():
            rep[f"{name}:{j}"] = e
        if name in ("visitor", "man") and "ankle" in J:
            for s in ("", "2"):
                rep[f"{name}:ankle{s}_y_minus_contact"] = dict(contact_px=round(org(J["ankle" + s])[1] - (FLOOR - 10), 3))
    for j, e in props.items():
        rep[f"prop:{j}"] = e
    JOINTS[did] = rep
    img = L.done()
    _DRAWN[did] = img
    return img


def layer(c, frame=None):
    """RGBA 900x600 puppet/prop layer of cell c at cell-local frame (24 fps). None = page pose."""
    sh = sheet(c)
    did = sh[-1] if frame is None or frame >= NFRAMES or frame < 0 else sh[int(frame)]
    return _render(c, did)


def page_layer(c):
    return layer(c, None)


EVENTS = {
    "A": dict(steps_s=[round(k / 12, 3) for k in range(12) if k % 3 == 0], stop_s=1.0),
    "B": dict(pulls_s=list(B_PULLS), strikes_s=list(B_STRIKES)),
    "C": dict(knocks_s=[round(k / 12, 3) for k in C_KNOCKS]),
    "D": dict(tear_s=[4 / 12, 6 / 12], key_out_s=9 / 12, surprise_s=14 / 12),
    "E": dict(lift_start_s=3 / 12, head_up_s=6 / 12, head_sky_until_s=20 / 12, key_top_click_s=7 / 12, glint_s=7 / 12),
    "F": dict(key_on_wood_s=4 / 12, steps_s=[round((9 + k) / 12, 3) for k in (0, 3)]),
    "G": dict(downstrokes_s=[round((2 + 4 * h) / 12, 3) for h in range(4)]),
    "H": dict(light_out_s=10 / 12),
    "I": dict(thread_taut_s=6 / 12, scrape_s=[8 / 12, 20 / 12]),
}


def mouth_anchor(c, stop_short=26):
    """Where a balloon tail should end (page pose), cell px: a point just off the
    speaker's mouth, pulled back toward the balloon so the tail never covers the
    face. For I the speaker is behind the door: the tail ends at the door edge."""
    st = plan(c)[-1]
    if c in ("A", "C", "D", "E", "F"):
        facing = st.get("facing", -1 if c == "D" else 1)
        J = solve(VISITOR, st["pose"], st["root"], facing)
        hd = HEADS[st["head"]]
        m = apply(J["neck"] @ M_S(VISITOR["head_k"]), _rot([(6, -56)], hd["pitch"]))[0]   # start inside the crown
        G = _grid()
        at = None
        if G:
            for it in G.LETTERING.get(c, []):
                if it["kind"] == "balloon":
                    at = it["at"]
        if at is None:
            return (round(m[0], 1), round(m[1], 1))
        # walk from the mouth toward the balloon until clear of the silhouette
        a = np.array(_render(c, sheet(c)[-1]).getchannel("A"))
        vx, vy = at[0] - m[0], at[1] - m[1]
        n = math.hypot(vx, vy)
        vx, vy = vx / n, vy / n
        x, y = m
        for _ in range(400):
            xi, yi = int(x), int(y)
            if 0 <= xi < CW and 0 <= yi < CH and a[yi, xi] < 10:
                break
            x, y = x + vx, y + vy
        return (round(x + vx * 12, 1), round(y + vy * 12, 1))
    if c == "I":
        return (I_DOOR[2] - 4, 250)
    return None


def keep_clear(c):
    """Bounding box (cell px) of everything this layer draws across its whole sheet."""
    box = None
    for did in sorted(set(sheet(c))):
        a = np.array(_render(c, did).getchannel("A"))
        ys, xs = np.nonzero(a > 16)
        if len(xs) == 0:
            continue
        b = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    return box


def figure_height(c):
    """Height of the dominant silhouette at the page pose, as a fraction of the panel."""
    st = plan(c)[-1]
    if c in ("A", "C", "E", "F"):
        J = solve(VISITOR, st["pose"], st["root"], st.get("facing", 1))
        top = min(y for x, y in apply(J["neck"] @ M_S(VISITOR["head_k"]), HEADS[st["head"]]["pts"]))
        return round((FLOOR - top) / CH, 3)
    if c == "G":
        J = solve(MAN, st["pose"], st["root"], 1)
        top = min(y for x, y in apply(J["neck"] @ M_S(MAN["head_k"]), HEADS[st["head"]]["pts"]))
        top = min(top, org(J["wrist"])[1] - 20, org(J["wrist2"])[1] - 20)
        return round((FLOOR - top) / CH, 3)
    return None


# ============================================================== preview ==
_G = None


def _grid():
    global _G
    if _G is None:
        sys.path.insert(0, str(HERE.parent / "grid"))
        try:
            import grid as G   # U1's deterministic page functions
            _G = G
        except Exception:      # pragma: no cover
            _G = False
    return _G


def _stencil(c):
    for p in (SRC / "forage" / f"stencil_{c}.png",):
        if p.exists():
            im = Image.open(p).convert("RGBA")
            return im.resize((CW, CH), Image.LANCZOS) if im.size != (CW, CH) else im
    return None


def preview(c, frame=None, lettering=True):
    """Cell composite for checking only (the editor owns the real composite):
    U1 ground -> U3 stencil (if delivered) -> this layer -> U1 lettering -> U1 border."""
    G = _grid()
    if G:
        base = G.ground(c).convert("RGBA")
    else:
        base = Image.new("RGBA", (CW, CH), (254, 252, 248, 255))
    st = _stencil(c)
    if st is not None:
        base.alpha_composite(st)
    base.alpha_composite(layer(c, frame))
    if G and lettering:
        m = mouth_anchor(c)
        base.alpha_composite(G.lettering(c, tail_to=m) if m else G.lettering(c))
        try:
            base.alpha_composite(G.cell_overlay(c, s=1))
        except Exception:
            pass
    return base.convert("RGB")


# ================================================================ build ==
def build(out=HERE):
    import hashlib
    EDMEDIA.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    expo = dict(unit="puppet-cutter-animator (U2)", plan_revision="r0", fps=FPS, drawings_per_second=12, on="2s",
                frames_per_cell=NFRAMES, page_pose="the last frame of every sheet (frames >= 72 also give it)",
                api="puppets.layer(cell, frame) -> RGBA 900x600; no route argument anywhere",
                composite_order="U1 ground -> U3 stencil -> this layer -> U1 lettering -> U1 border/tab",
                floor_contact_y=FLOOR, library={k: dict(v, count=len(v["heads"]) + len(v["hands"])) for k, v in LIBRARY.items()},
                head_transition_costs={f"{a}->{b}": v for (a, b), v in HEAD_TRANS.items()}, default_transition_cost=30.0,
                min_hold_slots=dict(heads=2, hands="2 (G hands 1 = 2 frames, the hand-over-hand alternation)"),
                cells={})
    joints = dict(unit="U2", invariant="bone length |L - L0| <= 0.5 px and pin separation <= 0.5 px, every joint, every frame",
                  cells={}, summary={}, angle_limits=LIMITS, angle_limit_clamps=None)
    for c in "ABCDEFGHI":
        sh = sheet(c)
        st = plan(c)
        ids = drawing_ids(c)
        uniq = []
        for d in ids:
            if d not in uniq:
                uniq.append(d)
        cdir = EDMEDIA / "drawings" / c
        cdir.mkdir(parents=True, exist_ok=True)
        for d in uniq:
            _render(c, d).save(cdir / f"{d}.png", optimize=True)
        page_layer(c).save(EDMEDIA / f"layer_{c}_page.png")
        # schedules
        sched = []
        for k in range(NSLOTS):
            s0 = st[k]
            sched.append(dict(slot=k, frames=[2 * k, 2 * k + 1], drawing=ids[k],
                              head=s0.get("head"), hand=s0.get("hand"), hand2=s0.get("hand2")))
        holds = []
        cur, n = None, 0
        for d in sh:
            if d == cur:
                n += 1
            else:
                if cur:
                    holds.append(n)
                cur, n = d, 1
        holds.append(n)
        info = {k: v for k, v in PLAN_INFO.get(c, {}).items()}
        expo["cells"][c] = dict(
            action=ACTION[c], frames=sh, page_pose_drawing=sh[-1], distinct_drawings=len(uniq),
            min_drawing_hold_frames=min(holds), holds_frames=holds, events_s=EVENTS[c],
            schedule=sched, decoder=info, balloon_tail_to=mouth_anchor(c), keep_clear_box=keep_clear(c),
            dominant_figure_height_frac=figure_height(c),
            drawings_png=f"films/sources/quatre-vingt-quinze/puppet-cutter-animator/drawings/{c}/<id>.png",
            states={d: st[int(d[1:])] for d in uniq})
        # joints per frame
        per = {}
        for f, d in enumerate(sh):
            for j, e in JOINTS[d].items():
                for kk, v in e.items():
                    per.setdefault(f"{j}.{kk}", [None] * NFRAMES)[f] = v
        joints["cells"][c] = per
        joints["summary"][c] = {k: max(abs(x) for x in v if x is not None) for k, v in per.items() if not k.endswith("contact_px")}
        joints["summary"][c].update({k: [min(x for x in v if x is not None), max(x for x in v if x is not None)]
                                     for k, v in per.items() if k.endswith("contact_px")})
    joints["angle_limit_clamps"] = LIMIT_LOG
    allmax = max(v for c in joints["summary"].values() for k, v in c.items() if not isinstance(v, list))
    joints["max_error_px_over_all_joints_frames"] = allmax
    joints["passes_0.5px"] = allmax <= 0.5
    expo["key_cut_used"] = str(key_source().relative_to(FILMS.parent))
    expo["evidence"] = [
        dict(id="KEY", title="File:Skeletonkey.png", author="Blenheimears", license="CC0",
             license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
             source_url="https://commons.wikimedia.org/wiki/File:Skeletonkey.png",
             file_url="https://upload.wikimedia.org/wikipedia/commons/2/21/Skeletonkey.png",
             local_path=expo["key_cut_used"] + " (U3's density cut of forage/src/skeletonkey.png, sha256 cf2401f2..., "
                        "the same file as films/sources/quatre-vingt-quinze/skeletonkey.png; this is what the film renders)",
             what_it_shows="photograph of old skeleton keys; the left key, cut out by density with the bow hole open",
             verified_date_or_place="Commons extmetadata LicenseShortName=CC0, re-read 2026-11-17 by the test shot "
                                    "(films/sources/quatre-vingt-quinze/test-shot/commons_meta.json); not re-fetched by U2",
             used_as="the brass key paper piece: held in the wrist frame in D, E, F; lying on the bench in F; sliding under the door in I"),
        dict(id="KEYS-CLINK", title="File:Keys hitting tree 2 (Gravity Sound).wav", author="Gravity Sound", license="CC BY 4.0",
             license_url="https://creativecommons.org/licenses/by/4.0", 
             source_url="https://commons.wikimedia.org/wiki/File:Keys_hitting_tree_2_(Gravity_Sound).wav", file_url="https://upload.wikimedia.org/wikipedia/commons/c/c8/Keys_hitting_tree_2_%28Gravity_Sound%29.wav",
             local_path="films/sources/quatre-vingt-quinze/test-shot/keys.wav (E-test only; the film's cues read forage/wav/)",
             what_it_shows="recording of keys striking wood", 
             verified_date_or_place="Commons extmetadata LicenseShortName=CC BY 4.0, Artist=Gravity Sound, re-read 2026-11-17 "
                                    "by the test shot (test-shot/commons_meta.json)",
             used_as="E-test.mp4 only: one 0.31 s clink grain at the top of the lift (0.75 s); the film's E cue is U3's"),
    ]
    expo["handmade"] = [
        "visitor rig (cloche hat, coat, bob curl, big nose) and capped-man rig (railway cap with peak, hooked nose, moustache): "
        "FK pieces cut in code with fixed per-piece scissor wobble (puppets.py: VISITOR, MAN, V_BASE, M_BASE, V_COAT, M_JACKET)",
        "replacement library: visitor 7 heads (r1 adds v_sky) + 4 hands = 11; man 3 heads + 3 hands = 6 (HEADS, HANDS, LIBRARY); "
        "hat band and eyes are slits cut through the paper",
        "bell, bracket, lever and clapper (two-link pendulum), red bell cord, sealed and torn envelope with red seal, "
        "service doors with windows (A lit, C dark, D lit with the man's shadow, H lit->dim->dark, I dark), benches (D, F), "
        "red key thread, G's red cord with travelling knots and floor coil, key glint, floor contact lines",
        "exposure sheets A-I (plan_A..plan_I) and the DP decoder (viterbi, decode_heads, decode_hands)",
    ]
    expo["absences"] = [
        "none for the key or stencils: the render uses U3's forage/key_cut.png (see key_cut_used) and forage/stencil_A.png, "
        "stencil_H.png; the test shot's earlier key cut is not used",
        "no foraged motion reference was used for rotoscoping; all motion is keyed FK",
    ]
    expo["outputs"] = dict(
        puppets_py="films/swarm/quatre-vingt-quinze/puppets/puppets.py",
        exposure_json="films/swarm/quatre-vingt-quinze/puppets/exposure.json",
        joint_errors_json="films/swarm/quatre-vingt-quinze/puppets/joint-errors.json",
        e_test_mp4="films/swarm/quatre-vingt-quinze/puppets/E-test.mp4",
        editor_media="films/sources/quatre-vingt-quinze/puppet-cutter-animator/ (layer_<cell>_page.png, drawings/<cell>/<id>.png)",
        stills="films/sources/quatre-vingt-quinze/puppets/ (E-test_fNN.png, model_sheet.png, contact_<cell>.png)")
    (out / "exposure.json").write_text(json.dumps(expo, indent=1, ensure_ascii=False, default=float))
    (out / "joint-errors.json").write_text(json.dumps(joints, default=float))
    return expo, joints


def e_test(out=HERE):
    """Cell E's 3 s sheet alone at final cell size (900x600), composited over U1's
    painted ground and lettering for viewing; the key clink at the top of the lift."""
    import tempfile
    tmp = Path(tempfile.mkdtemp(dir=str(MEDIA)))
    for f in range(NFRAMES):
        preview("E", f).save(tmp / f"f{f:03d}.png")
    snd = SRC / "test-shot" / "keys.wav"
    vid = out / "E-test.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%03d.png")]
    if snd.exists():
        t = EVENTS["E"]["key_top_click_s"]
        cmd += ["-i", str(snd), "-filter_complex",
                f"[1:a]atrim=0.31:0.62,asetpts=PTS-STARTPTS,adelay={int(t * 1000)}|{int(t * 1000)},apad=whole_dur=3[a]",
                "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "96k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-t", "3", str(vid)]
    subprocess.run(cmd, check=True)
    # stills for the record
    for f in (0, 6, 12, 20, 71):
        Image.open(tmp / f"f{f:03d}.png").save(MEDIA / f"E-test_f{f:02d}.png")
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    return vid


if __name__ == "__main__":
    expo, joints = build()
    print("max joint error px:", joints["max_error_px_over_all_joints_frames"], "limit clamps:", len(LIMIT_LOG))
    print("E-test:", e_test())
    tiles = []
    for h in HEADS:
        L = Layer()
        rig = VISITOR if h[0] == "v" else MAN
        limb(L, (300, 440), (300, 300), 24, 19, "sheet_neck")
        draw_head(L, M_T(300, 300), h, rig)
        tiles.append(L.done().crop((150, 120, 500, 440)))
    for hn in HANDS:
        L = Layer()
        draw_hand(L, M_T(300, 240) @ M_S(2.5), hn, VISITOR)
        tiles.append(L.done().crop((150, 120, 500, 440)))
    ms = Image.new("RGB", (350 * 7, 320 * 2), (237, 146, 131))
    for i, t in enumerate(tiles):
        ms.paste(t, ((i % 7) * 350, (i // 7) * 320), t)
    ms.save(MEDIA / "model_sheet.png")
    for c in "ABCDEFGHI":
        u = []
        for d in drawing_ids(c):
            if d not in u:
                u.append(d)
        cols = 6
        cs = Image.new("RGB", (cols * 300, ((len(u) + cols - 1) // cols) * 200), (255, 255, 255))
        for i, d in enumerate(u):
            cs.paste(preview(c, sheet(c).index(d), lettering=False).resize((298, 198)), ((i % cols) * 300, (i // cols) * 200))
        cs.save(MEDIA / f"contact_{c}.jpg", quality=88)
