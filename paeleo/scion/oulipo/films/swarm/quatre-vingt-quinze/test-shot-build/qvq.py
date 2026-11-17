"""quatre-vingt-quinze, test shot: page, cells, puppets.

Cells are rendered by cell_image(cell_id, drawing) only: no route argument
(plan invariant 1). Drawing index None means the page pose.

SCION 2  (Reiniger): solid backlit cut pieces, pinned joints, replacement
          profiles, contact line, an exposure sheet per cell.
SCION 32 (FK):       3x3 parent * local transforms, constant bone lengths,
          the key attached to the wrist frame (errors-by-joint measured).
SCION 38 (pose DP):  replacement heads chosen by a Viterbi decoder over a
          drawing library with a transition matrix and min holds.
"""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, str(FILMS))
from kit import Ink  # noqa: E402
from letters import letter  # noqa: E402

SRC = FILMS / "sources" / "quatre-vingt-quinze" / "test-shot"
SS = 2  # supersampling for cell drawing

# ------------------------------------------------------------ palette ---
PAPER = (253, 250, 246)
INKC = (43, 32, 33)        # #2b2021 line ink
SIL = (22, 16, 15)         # #16100f silhouettes
RED = (177, 78, 63)        # #b14e3f, the reference's mark red
SAL_PALE = (255, 215, 212)  # #ffd7d4
SAL_MID = (237, 146, 131)  # #ed9283
SAL_DEEP = (194, 88, 80)   # #c25850
MAUVE = (126, 75, 69)      # #7e4b45
BRASS = (186, 146, 70)
GLASS = (255, 236, 214)

CW, CH = 900, 600
COLX = [240, 1230, 2220]
ROWY = [260, 950, 1640]
PW, PH = 3360, 2400
CELLS = "ABCDEFGHI"
SALMON_CELLS = set("DEGI")


def cell_origin(c):
    k = CELLS.index(c)
    return COLX[k % 3], ROWY[k // 3]


def cell_center(c):
    x, y = cell_origin(c)
    return x + CW / 2, y + CH / 2


# ------------------------------------------------------------ helpers ---
def new_ink(seed, size=(CW * SS, CH * SS)):
    ink = Ink(0, 0, size, boil=0, wobble=1.0 * SS, seed=seed)
    ink.rng = random.Random(seed)
    return ink


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def catmull(pts, n=6, closed=True):
    P = list(pts)
    out = []
    m = len(P)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1 = P[(i - 1) % m] if closed or i > 0 else P[0], P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed or i + 2 < m else P[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


def radial_pool(w, h, cx, cy, r, inner=SAL_PALE, mid=SAL_MID, outer=SAL_DEEP):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((x - cx) / r) ** 2 + ((y - cy) / (r * 0.9)) ** 2)
    d = np.clip(d, 0, 1.3) / 1.3
    a = np.array(inner, np.float32)
    b = np.array(mid, np.float32)
    c = np.array(outer, np.float32)
    t1 = np.clip(d / 0.55, 0, 1)[..., None]
    t2 = np.clip((d - 0.55) / 0.45, 0, 1)[..., None]
    col = np.where(d[..., None] < 0.55, a + (b - a) * (t1 ** 1.2), b + (c - b) * (t2 ** 0.9))
    return Image.fromarray(col.astype(np.uint8), "RGB")


# ------------------------------------------------------- FK transforms ---
def M_T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def M_R(deg):
    # rotates the local "down" axis (0,1) toward local +x (forward) for +deg
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], float)


def M_F(f):
    return np.array([[f, 0, 0], [0, 1, 0], [0, 0, 1]], float)


def apply(M, pts):
    return [(M[0, 0] * x + M[0, 1] * y + M[0, 2], M[1, 0] * x + M[1, 1] * y + M[1, 2]) for x, y in pts]


def origin(M):
    return (M[0, 2], M[1, 2])


VISITOR = dict(spine=122, neck=14, sh_off=(6, 16), upper=80, fore=72, hip_off=(0, 0), thigh=88, shin=82)
MAN = dict(spine=124, neck=14, sh_off=(4, 16), upper=80, fore=74, hip_off=(0, 0), thigh=92, shin=86)


def solve(rig, pose, root, facing=1):
    """Forward kinematics. Returns dict of joint world matrices.

    pose keys (degrees): pelvis, spine, neck, sh, el, wr, sh2, el2, wr2,
    hip, knee, hip2, knee2; root=(x,y) of the pelvis.
    """
    g = lambda k: pose.get(k, 0.0)
    J = {}
    R0 = M_T(*root) @ M_F(facing)
    J["pelvis"] = R0 @ M_R(g("pelvis"))
    J["chest"] = J["pelvis"] @ M_R(g("spine")) @ M_T(0, -rig["spine"])
    J["neck"] = J["chest"] @ M_R(g("neck")) @ M_T(0, -rig["neck"])
    for side, sfx in (("", ""), ("2", "2")):
        sh = J["chest"] @ M_T(*rig["sh_off"])
        J["shoulder" + sfx] = sh @ M_R(g("sh" + sfx))
        J["elbow" + sfx] = J["shoulder" + sfx] @ M_T(0, rig["upper"]) @ M_R(g("el" + sfx))
        J["wrist" + sfx] = J["elbow" + sfx] @ M_T(0, rig["fore"]) @ M_R(g("wr" + sfx))
        J["hip" + sfx] = J["pelvis"] @ M_T(*rig["hip_off"]) @ M_R(g("hip" + sfx))
        J["knee" + sfx] = J["hip" + sfx] @ M_T(0, rig["thigh"]) @ M_R(g("knee" + sfx))
        J["ankle" + sfx] = J["knee" + sfx] @ M_T(0, rig["shin"])
    return J


BONES = [("pelvis", "chest", "spine"), ("chest", "neck", "neck"), ("shoulder", "elbow", "upper"),
         ("elbow", "wrist", "fore"), ("hip", "knee", "thigh"), ("knee", "ankle", "shin"),
         ("shoulder2", "elbow2", "upper"), ("elbow2", "wrist2", "fore"), ("hip2", "knee2", "thigh"), ("knee2", "ankle2", "shin")]


def bone_errors(rig, J):
    out = {}
    for a, b, k in BONES:
        pa, pb = origin(J[a]), origin(J[b])
        out[f"{a}->{b}"] = abs(math.hypot(pb[0] - pa[0], pb[1] - pa[1]) - rig[k])
    return out


# --------------------------------------------------- drawing library ---
# Replacement heads: hand-placed contour points in the neck frame
# (x forward, y down, origin at the neck pin). Each is its own drawing.
HEADS = {
    "v_level": dict(pitch=0, pts=[(-14, 4), (-22, -18), (-30, -46), (-46, -60), (-52, -78), (-44, -100), (-24, -118),
                                  (2, -124), (26, -116), (42, -98), (50, -88), (58, -84), (52, -80), (40, -78), (40, -70),
                                  (52, -66), (68, -60), (74, -50), (66, -42), (46, -40), (44, -34), (50, -30), (42, -26),
                                  (40, -20), (30, -12), (16, -6), (14, 4)], eye=(30, -66)),
    "v_turning": dict(pitch=22, pts=[(-16, 4), (-26, -16), (-38, -38), (-58, -46), (-70, -60), (-70, -84), (-56, -106),
                                     (-30, -120), (-2, -120), (22, -108), (34, -100), (42, -100), (38, -92), (30, -86),
                                     (36, -80), (54, -84), (72, -84), (80, -76), (74, -66), (54, -60), (54, -52), (60, -46),
                                     (52, -40), (48, -32), (36, -20), (20, -8), (16, 4)], eye=(26, -78)),
    "v_up": dict(pitch=44, pts=[(-16, 4), (-30, -12), (-46, -30), (-70, -32), (-86, -44), (-92, -68), (-82, -94),
                                (-60, -112), (-32, -118), (-8, -112), (6, -110), (12, -116), (14, -108), (10, -98),
                                (22, -96), (40, -108), (58, -114), (68, -108), (66, -96), (50, -84), (58, -76), (62, -66),
                                (56, -62), (60, -50), (50, -40), (40, -26), (24, -10), (18, 4)], eye=(10, -84)),
    "v_surprise": dict(pitch=6, pts=[(-14, 4), (-22, -18), (-30, -46), (-48, -58), (-56, -78), (-48, -102), (-26, -122),
                                     (0, -128), (26, -120), (42, -102), (50, -92), (58, -90), (52, -84), (40, -80), (42, -72),
                                     (56, -70), (72, -64), (78, -54), (70, -46), (48, -44), (50, -36), (54, -26), (46, -18),
                                     (36, -14), (26, -8), (14, 4)], eye=(30, -70)),
    "v_shrug": dict(pitch=-12, pts=[(-14, 4), (-20, -20), (-24, -48), (-38, -66), (-40, -86), (-28, -108), (-4, -120),
                                    (22, -118), (40, -102), (48, -90), (56, -84), (50, -80), (42, -74), (46, -66), (60, -56),
                                    (70, -44), (66, -34), (48, -34), (44, -26), (46, -20), (38, -14), (24, -4), (12, 4)],
                    eye=(32, -64)),
    "m_watch": dict(pitch=0, pts=[(-16, 4), (-22, -24), (-28, -50), (-30, -64), (-40, -66), (-44, -76), (-34, -84),
                                  (-30, -104), (-10, -114), (16, -112), (32, -102), (36, -92), (64, -90), (70, -84),
                                  (40, -80), (42, -70), (56, -62), (70, -52), (72, -42), (60, -36), (44, -36), (46, -26),
                                  (40, -16), (30, -10), (16, 4)], eye=(26, -70)),
    "m_effort": dict(pitch=18, pts=[(-16, 4), (-26, -20), (-38, -44), (-44, -58), (-54, -58), (-60, -70), (-52, -80),
                                    (-52, -100), (-34, -114), (-8, -116), (10, -108), (16, -100), (44, -106), (52, -102),
                                    (22, -90), (28, -80), (46, -78), (64, -72), (70, -62), (60, -54), (44, -50), (50, -42),
                                    (40, -40), (46, -30), (36, -18), (26, -8), (16, 4)], eye=(16, -82)),
}

# Hands, in the wrist frame (+y along the forearm, +x forward of the palm).
HANDS = {
    "relaxed": [(-7, -2), (-9, 10), (-8, 22), (-2, 30), (6, 28), (9, 18), (12, 10), (8, 0)],
    "pinch": [(-8, -2), (-12, 10), (-10, 22), (-2, 28), (8, 26), (14, 20), (20, 18), (18, 10), (10, 8), (9, 0)],
    "fist": [(-9, -2), (-12, 8), (-10, 20), (0, 24), (10, 22), (13, 12), (10, 0)],
    "open": [(-7, -2), (-10, 12), (-10, 26), (-4, 36), (2, 32), (4, 22), (12, 26), (14, 20), (9, 8), (8, 0)],
    "haul": [(-10, -2), (-13, 9), (-9, 20), (2, 23), (12, 20), (14, 9), (11, 0)],
}

# Coat piece for the visitor: defined around chest (top) and pelvis (bottom) frames.
V_COAT_TOP = [(-30, 0), (-42, 18), (-46, 56), (-46, 96), (-44, 122)]       # chest frame, back edge, going down
V_COAT_FRONT = [(40, 124), (40, 96), (42, 64), (40, 36), (26, 6), (12, -2)]          # chest frame, front edge, going up
V_HEM = [(-48, 0), (-60, 76), (-66, 112), (-24, 118), (24, 120), (62, 112), (54, 64), (42, 0)]  # pelvis frame
M_JACKET = [(-34, 0), (-46, 24), (-46, 70), (-44, 110), (-42, 140), (42, 142), (42, 100), (40, 60), (34, 22), (16, 0)]


def draw_poly(ink, pts, fill=SIL, rough=0.7):
    ink.poly(S(pts), fill=fill, color=None, width=0, rough=True)


def limb(ink, a, b, w0, w1, fill=SIL):
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
           (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]
    ink.d.polygon(S(pts), fill=fill)
    for (cx, cy), w in ((a, w0), (b, w1)):
        r = w / 2 * SS
        ink.d.ellipse([cx * SS - r, cy * SS - r, cx * SS + r, cy * SS + r], fill=fill)


HEAD_SCALE = 1.25
HAND_SCALE = 1.35


def head_draw(ink, M, name, ground):
    h = HEADS[name]
    k = HEAD_SCALE
    M = M @ M_R(0.5 * h["pitch"])  # the drawing's own pitch, seated on the neck pin
    pts = apply(M, [(x * k, y * k) for x, y in catmull(h["pts"], 4)])
    ink.d.polygon(S(pts), fill=SIL)
    ex, ey = apply(M, [(h["eye"][0] * k, h["eye"][1] * k)])[0]
    # cut eye: a sliver of the ground showing through the paper
    ink.d.ellipse([(ex - 5.5) * SS, (ey - 3.2) * SS, (ex + 5.5) * SS, (ey + 3.2) * SS], fill=ground)


def hand_draw(ink, M, name):
    ink.d.polygon(S(apply(M, [(x * HAND_SCALE, y * HAND_SCALE) for x, y in catmull(HANDS[name], 3)])), fill=SIL)


def shoe(ink, M_ankle, facing):
    """Shoe drawn level on the contact plane at the ankle pin."""
    pts = [(-8, -6), (-10, 6), (-6, 10), (10, 10), (24, 9), (26, 5), (14, 2), (8, -6)]
    ax, ay = origin(M_ankle)
    ink.d.polygon(S([(ax + facing * x, ay + y) for x, y in pts]), fill=SIL)


def M_angle(M):
    # angle of the local down axis in the world, as M_R would build it (for keeping feet level)
    dx, dy = M[0, 1], M[1, 1]
    f = 1 if np.linalg.det(M[:2, :2]) > 0 else -1
    return math.degrees(math.atan2(dx * f, dy))


def visitor(ink, pose, root, facing, head, hand, hand2="relaxed", ground=PAPER, legs=True):
    J = solve(VISITOR, pose, root, facing)
    # back arm first (behind the coat)
    limb(ink, origin(J["shoulder2"]), origin(J["elbow2"]), 26, 21)
    limb(ink, origin(J["elbow2"]), origin(J["wrist2"]), 21, 15)
    hand_draw(ink, J["wrist2"], hand2)
    if legs:
        for s in ("2", ""):
            limb(ink, origin(J["hip" + s]), origin(J["knee" + s]), 30, 22)
            limb(ink, origin(J["knee" + s]), origin(J["ankle" + s]), 22, 14)
            shoe(ink, J["ankle" + s], facing)
    coat = apply(J["chest"], V_COAT_TOP) + apply(J["pelvis"], V_HEM) + apply(J["chest"], V_COAT_FRONT)
    ink.d.polygon(S(catmull(coat, 3)), fill=SIL)
    limb(ink, origin(J["chest"]), origin(J["neck"]), 26, 22)
    head_draw(ink, J["neck"], head, ground)
    limb(ink, origin(J["shoulder"]), origin(J["elbow"]), 28, 21)
    limb(ink, origin(J["elbow"]), origin(J["wrist"]), 21, 15)
    hand_draw(ink, J["wrist"], hand)
    return J


def man(ink, pose, root, facing, head, hand="haul", hand2="haul", ground=PAPER, legs=True):
    J = solve(MAN, pose, root, facing)
    limb(ink, origin(J["shoulder2"]), origin(J["elbow2"]), 24, 19)
    limb(ink, origin(J["elbow2"]), origin(J["wrist2"]), 19, 14)
    hand_draw(ink, J["wrist2"], hand2)
    if legs:
        for s in ("2", ""):
            limb(ink, origin(J["hip" + s]), origin(J["knee" + s]), 30, 22)
            limb(ink, origin(J["knee" + s]), origin(J["ankle" + s]), 22, 16)
            shoe(ink, J["ankle" + s], facing)
    jacket = apply(J["chest"], M_JACKET[:5]) + apply(J["chest"], M_JACKET[5:])
    ink.d.polygon(S(catmull(jacket, 3)), fill=SIL)
    limb(ink, origin(J["pelvis"]), origin(J["chest"]), 46, 50)
    limb(ink, origin(J["chest"]), origin(J["neck"]), 24, 20)
    head_draw(ink, J["neck"], head, ground)
    limb(ink, origin(J["shoulder"]), origin(J["elbow"]), 25, 19)
    limb(ink, origin(J["elbow"]), origin(J["wrist"]), 19, 14)
    hand_draw(ink, J["wrist"], hand)
    return J


# ------------------------------------------------------------- the key ---
_KEY = None


def key_cut():
    """Density cut of the CC0 key photograph (left key), bow hole kept open.
    Printed as one flat brass piece with an ink edge."""
    global _KEY
    if _KEY is None:
        src = Image.open(FILMS / "sources" / "quatre-vingt-quinze" / "skeletonkey.png").convert("L")
        crop = src.crop((150, 50, 445, 640))
        a = np.array(crop, np.float32)
        m = (a < 120).astype(np.uint8)
        # fill engraving specks: holes not touching the border and smaller than the bow hole are filled
        import cv2
        n, lab, stats, _ = cv2.connectedComponentsWithStats((1 - m).astype(np.uint8), connectivity=4)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
        for i in range(1, n):
            if i not in border and stats[i, cv2.CC_STAT_AREA] < 2500:
                m[lab == i] = 1
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = Image.fromarray(m * 255).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 127 else 0)
        edge = mask.filter(ImageFilter.MaxFilter(9))
        img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        img.paste(Image.new("RGBA", mask.size, INKC + (255,)), (0, 0), edge)
        img.paste(Image.new("RGBA", mask.size, BRASS + (255,)), (0, 0), mask)
        _KEY = img
        img.save(SRC / "key_cut.png")
    return _KEY


def paste_key(ink, M, length=92, offset=(4, 20), extra_rot=0.0):
    """The key is attached to the wrist frame M at a fixed offset (prop constraint)."""
    k = key_cut()
    sc = length * SS / k.size[1]
    kimg = k.resize((max(1, int(k.size[0] * sc)), int(k.size[1] * sc)), Image.LANCZOS)
    # key image: bow at bottom (y=h*0.82 is the bow hole), blade upward. In the wrist frame the blade points along +y.
    dx, dy = M[0, 1], M[1, 1]
    # PIL rotates counter-clockwise on screen; the blade (image up) must point along the wrist frame's +y
    rot = math.degrees(math.atan2(-dx, -dy)) + extra_rot
    r = kimg.rotate(rot, resample=Image.BICUBIC, expand=True)
    anchor = apply(M, [offset])[0]
    w, h = kimg.size
    a = math.radians(rot)
    rx, ry = 0.30 * h * math.sin(a), 0.30 * h * math.cos(a)  # bow centre, 0.30h below the image centre
    cx, cy = anchor[0] * SS - rx, anchor[1] * SS - ry
    ink.img.paste(r, (int(cx - r.size[0] / 2), int(cy - r.size[1] / 2)), r)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    bow = (anchor[0], anchor[1])
    tip = apply(M, [(offset[0], offset[1] + length * 0.95)])[0]
    return bow, tip


def thread(ink, a, b, sag=20, width=3.0):
    (x0, y0), (x1, y1) = a, b
    pts = [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)) for t in np.linspace(0, 1, 16)]
    ink.line(S(pts), color=RED, width=width * SS, amount=0.6 * SS)


def glint(ink, x, y, r=20):
    for a in (0, 90, 45, 135):
        L = r if a in (0, 90) else r * 0.5
        dx, dy = math.cos(math.radians(a)) * L, math.sin(math.radians(a)) * L
        ink.stroke(S([(x - dx, y - dy), (x + dx, y + dy)]), color=(255, 252, 240), width=5 * SS, taper=True, amount=0.2)


# --------------------------------------------------------- balloons ---
def balloon(ink, lines, cx, cy, rx, ry, tail_to, size=40, seed=0):
    pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    tx, ty = tail_to
    ang = math.atan2(ty - cy, tx - cx)
    base = [(cx + rx * 0.82 * math.cos(ang + d), cy + ry * 0.82 * math.sin(ang + d)) for d in (-0.22, 0.22)]
    ink.d.polygon(S(pts), fill=(255, 255, 255))
    ink.d.polygon(S([base[0], (tx, ty), base[1]]), fill=(255, 255, 255))
    ink.line(S(pts + [pts[0]]), color=INKC, width=4.5 * SS, amount=0.8 * SS)
    # tail edges
    e0 = (cx + rx * math.cos(ang - 0.26), cy + ry * math.sin(ang - 0.26))
    e1 = (cx + rx * math.cos(ang + 0.26), cy + ry * math.sin(ang + 0.26))
    ink.d.polygon(S([e0, (tx, ty), e1, (cx + rx * 0.9 * math.cos(ang), cy + ry * 0.9 * math.sin(ang))]), fill=(255, 255, 255))
    ink.stroke(S([e0, (tx, ty)]), color=INKC, width=5 * SS, taper=False, amount=0.5 * SS)
    ink.stroke(S([e1, (tx, ty)]), color=INKC, width=5 * SS, taper=False, amount=0.5 * SS)
    n = len(lines)
    for i, s in enumerate(lines):
        y = cy + (i - (n - 1) / 2) * size * 1.35 + size / 2
        letter(ink, s, cx, y, size, 4.6, INKC, seed=seed + i, scale=SS)


def caption(ink, s, x=14, y=14, size=34, seed=0, pad=12):
    from letters import measure
    w = measure(s, size) + 2 * pad
    h = size + 2 * pad
    ink.d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], fill=(255, 255, 255))
    ink.line(S([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]), color=INKC, width=4 * SS, amount=0.6 * SS)
    letter(ink, s, x + pad, y + pad + size, size, 4.2, INKC, seed=seed, align="left", scale=SS)


def sfx(ink, s, x, y, size, tilt, seed=0):
    letter(ink, s, x, y, size, 10, RED, seed=seed, tilt=tilt, scale=SS, track=0.24)


# ------------------------------------------------------ FSA stencil ---
def stencil(box, out_size, thresh, ink_col, paper_col=None):
    """Two-level stencil print of the FSA plate (LoC 2017843779): one hand-chosen
    threshold; dark -> ink colour, light -> transparent (paper shows)."""
    src = Image.open(FILMS / "sources" / "la-machine-a-tuer-le-temps" / "loc_2017843779.jpg").convert("L")
    c = src.crop(box).resize(out_size, Image.LANCZOS)
    a = np.array(c.filter(ImageFilter.GaussianBlur(1.5)))
    m = (a < thresh).astype(np.uint8) * 255
    mask = Image.fromarray(m).filter(ImageFilter.MedianFilter(5))
    img = Image.new("RGBA", out_size, (0, 0, 0, 0))
    img.paste(Image.new("RGBA", out_size, ink_col + (255,)), (0, 0), mask)
    return img


_STENCILS = {}


def get_stencil(name):
    if name not in _STENCILS:
        if name == "H":
            _STENCILS[name] = stencil((600, 540, 945, 935), (CW * SS, int(CW * SS * 395 / 345 * 0.62)), 70, SAL_MID)
        elif name == "A":
            _STENCILS[name] = stencil((90, 60, 960, 640), (CW * SS, int(CW * SS * 580 / 870)), 62, SAL_PALE)
        _STENCILS[name].save(SRC / f"stencil_{name}.png")
    return _STENCILS[name]


# ------------------------------------------------------------ props ---
def door(ink, x0, y0, x1, y1, window=None, lit=True, fill=SIL):
    ink.d.rectangle(S([(x0, y0), (x1, y1)])[0] + S([(x1, y1)])[0], fill=fill)
    if window:
        wx0, wy0, wx1, wy1 = window
        ink.d.rectangle([wx0 * SS, wy0 * SS, wx1 * SS, wy1 * SS], fill=GLASS if lit else (40, 30, 30))
        ink.line(S([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)]), color=fill, width=6 * SS, rough=True)
    # knob
    kx, ky = (x0 + 18, (y0 + y1) / 2 + 20) if x0 > 450 else (x1 - 18, (y0 + y1) / 2 + 20)
    ink.d.ellipse([(kx - 7) * SS, (ky - 7) * SS, (kx + 7) * SS, (ky + 7) * SS], fill=GLASS)


def bench(ink, x, y, w, fill=SIL):
    ink.poly(S([(x, y), (x + w, y), (x + w, y + 16), (x, y + 16)]), fill=fill, color=None, width=0)
    ink.poly(S([(x + 6, y - 64), (x + w - 6, y - 64), (x + w - 6, y - 52), (x + 6, y - 52)]), fill=fill, color=None, width=0)
    for lx in (x + 18, x + w - 30):
        ink.poly(S([(lx, y + 14), (lx + 12, y + 14), (lx + 14, y + 74), (lx + 2, y + 74)]), fill=fill, color=None, width=0)
        ink.poly(S([(lx + 2, y - 54), (lx + 10, y - 54), (lx + 10, y), (lx + 2, y)]), fill=fill, color=None, width=0)


def floor_line(ink, y, x0=0, x1=CW):
    ink.line(S([(x0, y), (x1, y)]), color=INKC, width=4 * SS, amount=0.8 * SS)


# ---------------------------------------------------------- cell B ---
B_PIVOT = (400, 110)
BK = 1.3
B_STRIKES = (1.4, 2.6)   # cell-local seconds when the clapper strikes (sound is placed here)


def bell_angles(t):
    """Scripted swing (degrees) for bell and clapper at cell-local time t.
    Cord pulls at 0.9 and 2.15 s drive the bell; the clapper lags (two-link pendulum)."""
    def swing(tt):
        th = 0.0
        for p0, amp in ((1.15, 24.0), (2.35, 18.0)):
            if tt > p0:
                u = tt - p0
                th += amp * math.sin(2 * math.pi * u / 1.0) * math.exp(-u / 1.6) * min(1, u / 0.12)
        return th
    th = swing(t)
    ph = 1.9 * swing(t - 0.08)
    return th, ph


def bell_cell(ink, drawing):
    t = drawing / 12.0       # drawing 31 (t = 2.583 s, the second strike) is the page pose
    th, ph = bell_angles(t)
    px, py = B_PIVOT
    # wall bracket (handmade cut piece)
    ink.poly(S([(60, 30), (96, 30), (96, 230), (60, 230)]), fill=SIL, color=None, width=0)
    ink.poly(S([(92, 84), (px + 6, 94), (px + 6, 112), (92, 116)]), fill=SIL, color=None, width=0)
    ink.poly(S([(96, 190), (220, 100), (236, 110), (98, 212)]), fill=SIL, color=None, width=0)
    B = M_T(px, py) @ M_R(th)
    # lever + cord
    lever_end = apply(B, [(-118, -50)])[0]
    ink.poly(S(apply(B, [(-6, -36), (-120, -58), (-118, -42), (-6, -18)])), fill=SIL, color=None, width=0)
    taut = 0.0
    for p0 in (1.15, 2.35):
        if p0 - 0.1 < t < p0 + 0.25:
            taut = 1.0
    sag = 60 * (1 - taut) + 6
    cx0, cy0 = lever_end
    cord = [(cx0 + (-20 - cx0) * u, cy0 + 300 * u ** 1.6 + sag * math.sin(math.pi * u)) for u in np.linspace(0, 1, 18)]
    ink.line(S(cord), color=RED, width=5 * SS, amount=0.8 * SS)
    # bell body
    body = [(-24, -30), (24, -30), (26, -6), (52, 10), (62, 40), (70, 100), (84, 160), (112, 205), (132, 222),
            (130, 236), (-130, 236), (-132, 222), (-112, 205), (-84, 160), (-70, 100), (-62, 40), (-52, 10), (-26, -6)]
    ink.d.polygon(S(apply(B, [(x * BK, y * BK) for x, y in catmull(body, 3)])), fill=SIL)
    # clapper on its own pin inside the bell (second link)
    C = B @ M_T(0, 20 * BK) @ M_R(ph - th)
    rod_end = apply(C, [(0, 226 * BK)])[0]
    limb(ink, origin(C), rod_end, 14, 12)
    r = 30
    ink.d.ellipse([(rod_end[0] - r) * SS, (rod_end[1] - r) * SS, (rod_end[0] + r) * SS, (rod_end[1] + r) * SS], fill=SIL)
    # a paper-white cut along the shoulder (the cut-paper highlight slit)
    ink.stroke(S(apply(B, [(30 * BK, 30 * BK), (44 * BK, 90 * BK), (62 * BK, 150 * BK)])), color=PAPER, width=5 * SS, taper=True, amount=0.3)
    # motion arcs, drawn near the strikes
    near = any(abs(t - s) < 0.25 for s in B_STRIKES)
    if near:
        for k, rr in enumerate((330, 362)):
            a0, a1 = math.radians(20 + th), math.radians(52 + th)
            pts = [(px + rr * math.sin(a), py + rr * math.cos(a)) for a in np.linspace(a0, a1, 10)]
            ink.stroke(S(pts), color=INKC, width=(6 - k) * SS, taper=True, amount=0.6 * SS)
        for k, rr in enumerate((330, 362)):
            a0, a1 = math.radians(-48 + th), math.radians(-24 + th)
            pts = [(px + rr * math.sin(a), py + rr * math.cos(a)) for a in np.linspace(a0, a1, 10)]
            ink.stroke(S(pts), color=INKC, width=(5 - k) * SS, taper=True, amount=0.6 * SS)
    # SFX: each DING is lettered as it is struck (kinetic lettering); the page pose shows both
    if t >= B_STRIKES[0] - 0.05:
        sfx(ink, "DING !", 715, 150, 70, -12, seed=11)
    if t >= B_STRIKES[1] - 0.05:
        sfx(ink, "DING !", 745, 300, 70, -6, seed=12)


# ---------------------------------------------------------- cell E ---
# 12 key poses of the lift (pose-to-pose, spacing eased), FK angles.
E_KEYS = {
    1: dict(sh=12, el=26, wr=-8, spine=-2, pelvis=0, neck=0, hip=6, knee=-4, hip2=-8, knee2=6, drop=0),
    2: dict(sh=4, el=40, wr=-16, spine=3, pelvis=0, neck=3, hip=10, knee=-14, hip2=-4, knee2=-8, drop=6),   # anticipation
    4: dict(sh=40, el=54, wr=-10, spine=0, pelvis=0, neck=0, hip=7, knee=-7, hip2=-8, knee2=3, drop=1),
    7: dict(sh=78, el=28, wr=0, spine=-5, pelvis=0, neck=-4, hip=4, knee=-2, hip2=-10, knee2=6, drop=-2),
    10: dict(sh=112, el=0, wr=8, spine=-10, pelvis=0, neck=-8, hip=4, knee=0, hip2=-11, knee2=6, drop=-3),  # overshoot
    12: dict(sh=106, el=4, wr=6, spine=-8, pelvis=0, neck=-6, hip=4, knee=0, hip2=-11, knee2=6, drop=-2),
}
E_ROOT = (500, 392)
E_FLOOR = 568


def e_pose(k):
    ks = sorted(E_KEYS)
    if k in E_KEYS:
        return dict(E_KEYS[k])
    lo = max(a for a in ks if a < k)
    hi = min(a for a in ks if a > k)
    u = (k - lo) / (hi - lo)
    u = u * u * (3 - 2 * u)
    return {n: E_KEYS[lo][n] + (E_KEYS[hi][n] - E_KEYS[lo][n]) * u for n in E_KEYS[lo]}


def e_head_target(k):
    """Pose feature for the head decoder: desired head pitch (deg) per drawing."""
    return [0, 0, 0, 2, 8, 16, 24, 32, 40, 46, 46, 44][k - 1]


def decode_heads(targets, lib=("v_level", "v_turning", "v_up", "v_surprise", "v_shrug"), min_hold=2, final="v_up"):
    """SCION 38: Viterbi over the head library. Cost = pitch mismatch + transition cost;
    states carry a hold counter so no drawing is shown for fewer than `min_hold` drawings
    (except where the sequence starts). The protected key pose `final` is forced at the end."""
    T = {("v_level", "v_turning"): 1, ("v_turning", "v_up"): 1, ("v_up", "v_turning"): 2, ("v_turning", "v_level"): 2,
         ("v_level", "v_surprise"): 3, ("v_surprise", "v_level"): 3, ("v_level", "v_up"): 40, ("v_level", "v_shrug"): 3,
         ("v_shrug", "v_level"): 3}
    INF = 1e9
    states = [(h, c) for h in lib for c in (1, 2)]
    em = lambda h, tgt: ((HEADS[h]["pitch"] - tgt) / 6.0) ** 2 + (4 if h in ("v_surprise", "v_shrug") else 0)
    cost = {s: (em(s[0], targets[0]) if s[1] == 2 else INF) for s in states}  # a sequence may start "held"
    back = []
    for i in range(1, len(targets)):
        new, bp = {}, {}
        for (h, c) in states:
            best, arg = INF, None
            for (h0, c0), v in cost.items():
                if v >= INF:
                    continue
                if h0 == h:
                    if min(c0 + 1, 2) != c:
                        continue
                    tr = 0
                else:
                    if c != 1 or c0 < min_hold:
                        continue
                    tr = T.get((h0, h), 25)
                if v + tr < best:
                    best, arg = v + tr, (h0, c0)
            new[(h, c)] = best + em(h, targets[i]) if arg else INF
            bp[(h, c)] = arg
        back.append(bp)
        cost = new
    end = min((s for s in states if s[0] == final and s[1] >= min_hold), key=lambda s: cost[s])
    path = [end]
    for bp in reversed(back):
        path.append(bp[path[-1]])
    path.reverse()
    return [p[0] for p in path], cost[end]


E_HEADS, E_HEAD_COST = decode_heads([e_head_target(k) for k in range(1, 13)])
E_PAGE_DRAWING = 12


def _e_mouth():
    p = e_pose(E_PAGE_DRAWING)
    J = solve(VISITOR, p, (E_ROOT[0], E_ROOT[1] + p["drop"]), 1)
    m = apply(J["neck"], [(-70 * HEAD_SCALE, -50 * HEAD_SCALE)])[0]
    return (m[0] - 26, m[1] - 6)


E_TAIL = _e_mouth()


def e_drawing_of(local_t):
    """Exposure sheet for E: drawing k (1..12) at 12 drawings/s from local 0.0; then hold drawing 12."""
    return min(12, int(local_t * 12) + 1)


JOINT_LOG = []


def lift_cell(ink, drawing, ground):
    k = E_PAGE_DRAWING if drawing is None else drawing
    p = e_pose(k)
    root = (E_ROOT[0], E_ROOT[1] + p.pop("drop"))
    J = visitor(ink, p, root, 1, E_HEADS[k - 1], "pinch", "relaxed", ground=ground)
    JOINT_LOG.append(dict(cell="E", drawing=k, head=E_HEADS[k - 1], errors=bone_errors(VISITOR, J),
                          ankle=origin(J["ankle"]), ankle2=origin(J["ankle2"]), wrist=origin(J["wrist"])))
    bow, tip = paste_key(ink, J["wrist"], length=96, offset=(6, 22))
    thread(ink, bow, (bow[0] - 16, bow[1] + 74), sag=10, width=4)
    if k >= 10:
        glint(ink, tip[0], tip[1], 22 if k == 10 else 15)
    return J, bow


# -------------------------------------------------------- cell grounds ---
POOL = {"D": (420, 260, 640), "E": (470, 210, 640), "G": (520, 200, 640), "I": (360, 300, 620)}


def ground_image(c):
    if c in SALMON_CELLS:
        cx, cy, r = POOL[c]
        return radial_pool(CW * SS, CH * SS, cx * SS, cy * SS, r * SS)
    return Image.new("RGB", (CW * SS, CH * SS), PAPER)


def ground_at(c, x, y):
    if c in SALMON_CELLS:
        cx, cy, r = POOL[c]
        im = radial_pool(1, 1, 0, 0, 1)
        d = min(1.3, math.hypot((x - cx) / r, (y - cy) / (r * 0.9))) / 1.3
        if d < 0.55:
            u = (d / 0.55) ** 1.2
            return tuple(int(a + (b - a) * u) for a, b in zip(SAL_PALE, SAL_MID))
        u = ((d - 0.55) / 0.45) ** 0.9
        return tuple(int(a + (b - a) * u) for a, b in zip(SAL_MID, SAL_DEEP))
    return PAPER


# ------------------------------------------------------- static cells ---
def cell_A(ink):
    st = get_stencil("A")
    ink.img.paste(st, (0, 0), st)
    door(ink, 640, 120, 820, 568, window=(676, 160, 784, 260), lit=True)
    floor_line(ink, 568)
    pose = dict(sh=24, el=34, sh2=-10, el2=10, spine=4, hip=22, knee=-6, hip2=-20, knee2=24)
    J = visitor(ink, pose, (250, 392), 1, "v_level", "pinch", "relaxed")
    # sealed cream envelope in the front hand
    ex, ey = origin(J["wrist"])
    ink.poly(S([(ex - 6, ey + 8), (ex + 62, ey - 2), (ex + 66, ey + 38), (ex - 2, ey + 48)]), fill=(250, 240, 214), color=INKC, width=3 * SS)
    ink.line(S([(ex - 6, ey + 8), (ex + 30, ey + 26), (ex + 62, ey - 2)]), color=INKC, width=2.5 * SS)
    caption(ink, "GARE DE ST-ROCH, 6 H 10.", seed=1)
    balloon(ink, ["PERSONNE ?"], 470, 130, 130, 50, (372, 196), size=34, seed=2)


def cell_C(ink):
    door(ink, 560, 40, 840, 568, window=(610, 90, 790, 220), lit=False)
    floor_line(ink, 568)
    pose = dict(sh=96, el=-58, wr=-20, sh2=-6, el2=14, spine=6, hip=8, knee=-4, hip2=-10, knee2=8)
    visitor(ink, pose, (380, 372), 1, "v_level", "fist", "relaxed")
    # knock marks against the door
    for k, (dx, dy) in enumerate(((0, -30), (14, 0), (0, 30))):
        ink.stroke(S([(552 - k * 2, 250 + dy), (520 - k * 4, 238 + dy * 1.3)]), color=INKC, width=4 * SS)
    sfx(ink, "TOC TOC.", 250, 120, 58, -9, seed=31)


def cell_D(ink, ground):
    door(ink, 560, 30, 800, 568, window=(600, 80, 760, 250), lit=True)
    # the capped man's profile on the lit glass (pure shadow, masked to the window)
    lay = Image.new("RGBA", ink.img.size, (0, 0, 0, 0))
    li = new_ink(404, ink.img.size)
    li.img = lay
    li.d = ImageDraw.Draw(lay, "RGBA")
    man(li, dict(spine=-4), (712, 360), -1, "m_watch", legs=False)
    m = Image.new("L", ink.img.size, 0)
    ImageDraw.Draw(m).rectangle([603 * SS, 83 * SS, 757 * SS, 247 * SS], fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.array(lay.getchannel("A")), np.array(m))))
    ink.img.paste(lay, (0, 0), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.line(S([(680, 80), (680, 250)]), color=SIL, width=6 * SS)
    bench(ink, 140, 420, 420)
    floor_line(ink, 568)
    pose = dict(pelvis=0, spine=-4, hip=88, knee=-88, hip2=80, knee2=-70, sh=70, el=40, wr=-30, sh2=40, el2=50)
    J = visitor(ink, pose, (300, 404), 1, "v_surprise", "pinch", "pinch", ground=ground)
    bow, tip = paste_key(ink, J["wrist"], length=92, offset=(6, 22), extra_rot=0)
    thread(ink, bow, (bow[0] - 20, bow[1] + 80), sag=12)
    ex, ey = origin(J["wrist2"])
    ink.poly(S([(ex - 40, ey + 4), (ex + 20, ey - 6), (ex + 26, ey + 30), (ex - 34, ey + 40)]), fill=(250, 240, 214), color=INKC, width=3 * SS)
    ink.line(S([(ex - 40, ey + 4), (ex - 14, ey - 14), (ex + 2, ey + 2), (ex + 20, ey - 6)]), color=INKC, width=2.5 * SS)
    balloon(ink, ["UNE CLÉ ?"], 170, 92, 132, 54, (330, 220), size=36, seed=41)


def cell_F(ink):
    bench(ink, 300, 420, 400)
    floor_line(ink, 568)
    # key lying on the bench, thread trailing off the right edge
    M = M_T(560, 412) @ M_R(-90)
    bow, tip = paste_key(ink, M, length=84, offset=(0, 0))
    ink.line(S([bow, (640, 430), (760, 470), (905, 480)]), color=RED, width=3 * SS, amount=0.6 * SS)
    pose = dict(sh=-22, el=10, sh2=24, el2=20, spine=6, hip=26, knee=-8, hip2=-22, knee2=30)
    visitor(ink, pose, (120, 372), -1, "v_shrug", "open", "relaxed")
    balloon(ink, ["TANT PIS."], 300, 100, 128, 52, (180, 196), size=36, seed=61)


def cell_G(ink, ground):
    floor_line(ink, 568)
    pose = dict(spine=-8, sh=146, el=12, wr=0, sh2=124, el2=26, hip=10, knee=-6, hip2=-12, knee2=10)
    J = man(ink, pose, (430, 380), 1, "m_effort", ground=ground)
    w1, w2 = origin(J["wrist"]), origin(J["wrist2"])
    top = (760, -10)
    ink.line(S([(w2[0] + 2, w2[1] + 40), w2, w1, top]), color=RED, width=6 * SS, amount=0.6 * SS, rough=True)
    ink.line(S([(w2[0] + 2, w2[1] + 40), (w2[0] - 16, w2[1] + 120), (w2[0] + 10, w2[1] + 190)]), color=RED, width=6 * SS)
    caption(ink, "IL TIRE LA CORDE.", seed=71)


def cell_H(ink):
    st = get_stencil("H")
    ink.img.paste(st, (0, CH * SS - st.size[1]), st)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.d.rectangle([700 * SS, 40 * SS, 830 * SS, 160 * SS], fill=SIL)  # the door window, dark
    ink.line(S([(765, 40), (765, 160)]), color=MAUVE, width=4 * SS)
    caption(ink, "PLUS PERSONNE.", seed=81)


def cell_I(ink, ground):
    door(ink, 330, 30, 640, 560, window=(380, 80, 590, 200), lit=False)
    ink.d.rectangle([300 * SS, 560 * SS, 680 * SS, 600 * SS], fill=SIL)  # the sill
    M = M_T(360, 556) @ M_R(-90)
    k = key_cut()
    bow, tip = paste_key(ink, M, length=84, offset=(0, 0))
    # half under the door: redraw the door's lower edge over the key's blade
    ink.d.rectangle([330 * SS, 520 * SS, 640 * SS, 560 * SS], fill=SIL)
    ink.line(S([bow, (300, 575), (250, 590)]), color=RED, width=3 * SS)
    ink.line(S([(372, 548), (336, 556)]), color=RED, width=3 * SS)
    balloon(ink, ["MERCI."], 790, 140, 100, 52, (640, 250), size=36, seed=91)


# ------------------------------------------------------------ cells ---
_CACHE = {}
PAGE_POSE = {"B": 31, "E": 12}  # the last drawing of each animated sheet is what the page prints


def cell_image(c, drawing=None):
    """Canonical cell art at 900x600 (rendered at 2x and reduced). drawing=None is the page pose."""
    if drawing is None:
        drawing = PAGE_POSE.get(c)
    key = (c, drawing)
    if key in _CACHE:
        return _CACHE[key]
    ink = new_ink(1000 + CELLS.index(c) * 100 + (drawing or 0))
    g = ground_image(c)
    ink.img = g.copy()
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    gc = ground_at(c, 300, 200)
    if c == "A":
        cell_A(ink)
    elif c == "B":
        bell_cell(ink, drawing)
    elif c == "C":
        cell_C(ink)
    elif c == "D":
        cell_D(ink, gc)
    elif c == "E":
        floor_line(ink, E_FLOOR + 2)
        lift_cell(ink, drawing, ground_at("E", 420, 160))
        balloon(ink, ["C'EST POUR", "MOI ?"], 196, 104, 160, 80, E_TAIL, size=38, seed=51)
    elif c == "F":
        cell_F(ink)
    elif c == "G":
        cell_G(ink, gc)
    elif c == "H":
        cell_H(ink)
    elif c == "I":
        cell_I(ink, gc)
    img = ink.img.convert("RGB").resize((CW, CH), Image.LANCZOS)
    _CACHE[key] = img
    return img


# ------------------------------------------------------- page scaffold ---
MARKS = [(1185, 905), (2175, 905), (1185, 1595), (2175, 1595), (195, 905), (3165, 905), (195, 1595), (3165, 1595)]


def cross_mark(ink, x, y, state, seed=0, scale=1):
    """Red barbed cross. state: neutral | across | down. The long arms carry the axis cue."""
    long_, short = 66, 22
    arms = {"neutral": (40, 40), "across": (long_, short), "down": (short, long_)}[state]
    ax, ay = arms
    s = scale
    w = 7
    for dx, dy, L in ((1, 0, ax), (-1, 0, ax), (0, 1, ay), (0, -1, ay)):
        ex, ey = x + dx * L, y + dy * L
        ink.stroke([(x * s, y * s), (ex * s, ey * s)], color=RED, width=w * s, taper=False, amount=0.5 * s)
        # barbs: two short strokes back from the tip
        b = 13 if L > 30 else 9
        for sgn in (1, -1):
            bx = ex - dx * b + (dy * sgn) * b * 0.8
            by = ey - dy * b + (dx * sgn) * b * 0.8
            ink.stroke([(ex * s, ey * s), (bx * s, by * s)], color=RED, width=5 * s, taper=False, amount=0.4 * s)


def ruled_border(ink, x0, y0, scale=1):
    s = scale
    pts = [(x0, y0), (x0 + CW, y0), (x0 + CW, y0 + CH), (x0, y0 + CH), (x0, y0)]
    for a, b in zip(pts, pts[1:]):
        ink.stroke([(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)], color=INKC, width=8 * s, taper=False, amount=1.1 * s)


def id_tab(ink, c, x0, y0, scale=1):
    s = scale
    bx, by = x0 + CW - 58, y0 + CH - 58
    ink.d.rectangle([bx * s, by * s, (bx + 44) * s, (by + 44) * s], fill=(255, 255, 255))
    ink.line([(bx * s, by * s), ((bx + 44) * s, by * s), ((bx + 44) * s, (by + 44) * s), (bx * s, (by + 44) * s), (bx * s, by * s)],
             color=INKC, width=3 * s, amount=0.5 * s)
    letter(ink, c, bx + 22, by + 35, 26, 3.6, INKC, seed=ord(c), scale=s)


def scaffold(state="neutral", rail="both", s=1):
    """Everything except cell contents: paper, title, borders, tabs, marks, rails, bottom line.
    Returns an RGBA overlay at page size (x s) and the paper ground."""
    ink = Ink(0, 0, (PW * s, PH * s), boil=0, wobble=1.0 * s)
    ink.rng = random.Random(95)
    ink.img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    letter(ink, "quatre-vingt-quinze", PW / 2, 168, 128, 23, INKC, seed=95, flip_every=2, scale=s, track=0.16)
    for c in CELLS:
        x0, y0 = cell_origin(c)
        ruled_border(ink, x0, y0, s)
        id_tab(ink, c, x0, y0, s)
    for i, (x, y) in enumerate(MARKS):
        cross_mark(ink, x, y, state, seed=i, scale=s)
    # rails
    dim = (190, 172, 168)
    c2 = RED if rail in ("both", "down") else dim
    c1 = RED if rail in ("both", "across") else dim
    letter(ink, "II", 100, 380, 70, 9, c2, seed=2, scale=s)
    letter(ink, "en bas", 100, 450, 36, 5, c2 if rail != "both" else INKC, seed=3, scale=s)
    for i, c in enumerate("ADGBEHCFI"):
        y = 560 + i * 178
        letter(ink, c, 100, y, 40, 5, c2 if rail != "both" else INKC, seed=200 + i, scale=s)
        if i < 8:
            ink.line([(100 * s, (y + 22) * s), (100 * s, (y + 128) * s)], color=c2 if rail != "both" else INKC, width=3 * s, amount=0.5 * s)
    letter(ink, "I", 3260, 380, 70, 9, c1, seed=4, scale=s)
    letter(ink, "en travers", 3260, 450, 30, 4.4, c1 if rail != "both" else INKC, seed=5, scale=s)
    for i, c in enumerate(CELLS):
        x = 3200 + (i % 3) * 60
        y = 600 + (i // 3) * 110
        letter(ink, c, x, y, 40, 5, c1 if rail != "both" else INKC, seed=300 + i, scale=s)
    for r in range(3):
        y = 600 + r * 110 - 20
        ink.line([(3218 * s, y * s), (3242 * s, y * s)], color=INKC, width=3 * s, amount=0.3 * s)
        ink.line([(3278 * s, y * s), (3302 * s, y * s)], color=INKC, width=3 * s, amount=0.3 * s)
    letter(ink, "LIRE EN TRAVERS (I) PUIS EN BAS (II) — MÊME FIN : I.", PW / 2, 2372, 38, 5, INKC, seed=7, scale=s)
    return ink.img


def arrow(ink, x, y, angle, size=1.0, s=1):
    """Red cut-paper arrow, pointing along `angle` degrees (0 = right, 90 = down)."""
    pts = [(-40, -12), (8, -12), (8, -30), (44, 0), (8, 30), (8, 12), (-40, 12)]
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    P = [((x + (px * ca - py * sa) * size) * s, (y + (px * sa + py * ca) * size) * s) for px, py in pts]
    ink.poly(P, fill=RED, color=None, width=0, rough=True)


def build_page(s_cells=None):
    """The printed page: neutral marks, both rails, every cell at its page pose."""
    page = Image.new("RGB", (PW, PH), PAPER)
    for c in CELLS:
        page.paste(cell_image(c, None), cell_origin(c))
    sc = scaffold("neutral", "both", 2).resize((PW, PH), Image.LANCZOS)
    page.paste(sc, (0, 0), sc)
    return page
