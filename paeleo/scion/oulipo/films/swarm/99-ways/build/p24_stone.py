"""Page 24 Stone (medium and material; medium: daumier-collage).

A one-tone satirical lithograph with a caption beneath, the agent as a type of officialdom.
A plate from an invented series, THE COMPANY'S MEN, in the manner of a 19th-century satirical lithograph sheet:
series title and number at the head, four pictures (E0; E1-E2; E3; E4-E5 large), each with its caption beneath
in the lithographic convention (dialogue set off by dashes). Collage of Daumier cut-outs (FORAGED):
  AGENT    = the waistcoated man of Les Gens de Justice no. 1 (Daumier, 1845-48; Commons, PD), cut along a drawn
             scissor path; in the last picture a hand cut from the barrister of the same plate is glued at his
             chin holding a crayon-drawn pencil;
  STRANGER = the woman of Moeurs conjugales no. 3 (Daumier 1839, Rijksmuseum CC0; boucle-la's cut mask).
The set (desk, memo, ticket window, clock at 4:10, cupboard, key with SERVICE tag, SERVICE door) is HANDMADE in
lithographic crayon strokes and hatching in code. Everything printed in ONE tone (a single ink on the sheet).
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import b1m2  # noqa: E402

N, PID, TITLE = 24, "stone", "Stone"
W, H = pen99.PAGE_W, pen99.PAGE_H
ROOT = pen99.ROOT
FOR = ROOT / "films/sources/99-ways/forage/p23-26"
BL = ROOT / "films/sources/boucle-la/daumier"
INK1 = np.array([30, 26, 24], np.float32)        # the one tone
STATE = {"pictures": 4, "big": "full"}

# ------------------------------------------------------------------ foraged pieces
MAN_POLY = [(520, 335), (560, 330), (590, 360), (600, 405), (588, 430), (582, 465), (580, 490), (592, 560), (592, 700),
            (588, 790), (548, 800), (535, 900), (525, 1000), (518, 1100), (515, 1200), (525, 1238), (585, 1258),
            (580, 1280), (510, 1280), (495, 1305), (430, 1312), (425, 1290), (450, 1265), (455, 1200), (448, 1100),
            (435, 1050), (395, 1075), (330, 1060), (262, 1040), (250, 1000), (258, 955), (300, 945), (330, 900),
            (330, 860), (345, 840), (345, 780), (352, 680), (365, 580), (380, 520), (405, 480), (460, 450), (475, 420),
            (470, 380), (490, 350)]
MAN_FOOT = (500, 1300)
HEAD_POLY = [(468, 378), (488, 350), (520, 333), (560, 328), (592, 358), (602, 405), (590, 430), (586, 466), (568, 484),
             (540, 490), (512, 482), (490, 462), (473, 425)]
NECK = (540, 482)
BODY_POLY = [(582, 470), (580, 490)] + MAN_POLY[7:-3] + [(460, 450), (478, 446), (500, 468), (540, 482), (566, 478)]
WAIST_Y = 826          # the seated crop: cut across below the waistcoat, above the hat in his hand
D1 = ROOT / "films/sources/99-ways/forage/p12-daumier/d1.jpg"   # Les bons bourgeois no. 18 (99-ways:daumier-proprietaire-1846)
WOMAN_POLY = [(478, 705), (490, 668), (512, 640), (540, 627), (570, 630), (590, 650), (600, 680), (608, 712), (604, 735),
              (588, 750), (568, 758), (562, 782), (590, 802), (602, 842), (606, 900), (600, 962), (560, 976), (470, 976),
              (440, 962), (428, 900), (444, 846), (470, 816), (498, 792), (504, 762), (488, 742)]
WOMAN_BASE = (520, 976)
HAND_WRIST = (650, 792)
HAND_TIP = (546, 842)
HAND_POLY = [(652, 772), (640, 780), (628, 795), (605, 808), (590, 818), (560, 826), (538, 836), (546, 850), (572, 847), (590, 843),
             (603, 842), (608, 862), (617, 864), (624, 846), (636, 830), (662, 806)]


def levels(g, lo, hi):
    return np.clip((g.astype(np.float32) - lo) / (hi - lo), 0, 1)


def load_pieces():
    g = np.asarray(Image.open(FOR / "gdj_01_big.jpg").convert("L"))
    g = cv2.fastNlMeansDenoising(g, None, 7, 7, 21).astype(np.float32)   # the book photograph's camera noise, not the stone's grain
    tone = levels(g, 28, 222)
    man = cut(tone, MAN_POLY)
    head = cut(tone, HEAD_POLY)
    body = cut(tone, BODY_POLY)
    upper = cut(tone, BODY_POLY, ymax=WAIST_Y)
    hand = cut(tone, HAND_POLY)
    # his own coat sleeve (the hanging near arm, between its outline and the dark fold), cut as two strips to be
    # re-glued as a bent far arm: upper arm and forearm
    sl_u = cut(tone, [(334, 560), (398, 560), (398, 846), (333, 846)])
    sl_f = cut(tone, [(334, 560), (398, 560), (396, 846), (333, 846)])
    # the stranger: the bonneted woman in her dark shawl from Les bons bourgeois no. 18 (Rijksmuseum CC0), cut at
    # the hands; the yellowed sheet levelled and her ink pushed denser (gamma) so she reads behind the glass
    d1 = np.asarray(Image.open(D1).convert("L"))
    d1 = cv2.fastNlMeansDenoising(d1, None, 5, 7, 21).astype(np.float32)
    wt = levels(d1, 66, 214)
    wt = np.where(wt < 0.75, wt ** 1.3, wt)       # her shawl and dress pushed denser; the white bonnet kept white
    woman = cut(wt, WOMAN_POLY)
    # the ANRC 1922 key cutout (99-ways-template), its photograph tones mapped to the one ink
    kp = Image.open(b1m2.TPL_PIECES / "key.png")
    ka = np.asarray(kp)[..., 3]
    kg = np.asarray(kp.convert("L")).astype(np.float32)
    key = dict(t=0.06 + 0.80 * levels(kg, 20, 235) ** 0.8, a=ka, origin=(0, 0))
    return dict(man=man, head=head, body=body, upper=upper, hand=hand, sl_u=sl_u, sl_f=sl_f, woman=woman, key=key)


def cut(tone, poly, ymax=None):
    P = np.array(poly, np.float32)
    x0, y0 = np.floor(P.min(0)).astype(int) - 4
    x1, y1 = np.ceil(P.max(0)).astype(int) + 4
    m = np.zeros(tone.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(P * 4)], 255, cv2.LINE_AA, shift=2)
    if ymax is not None:
        m[int(ymax):] = 0
        y1 = min(y1, int(ymax) + 2)
    return dict(t=tone[y0:y1, x0:x1].copy(), a=m[y0:y1, x0:x1], origin=(x0, y0))


def lay(T, piece, src_pt, dst_pt, s, deg=0.0, flip=False, margin=4):
    """Glue a cut piece onto tone canvas T (1 = paper): its paper margin, a faint shadow, its own tones."""
    h, w = T.shape
    ox, oy = piece["origin"]
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]) * s
    if flip:
        R = R @ np.array([[-1, 0], [0, 1]])
    sp = np.array(src_pt, float) - np.array([ox, oy])
    t = np.array(dst_pt, float) - R @ sp
    M = np.hstack([R, t[:, None]]).astype(np.float32)
    tw = cv2.warpAffine(piece["t"], M, (w, h), flags=cv2.INTER_CUBIC, borderValue=1.0)
    aw = cv2.warpAffine(piece["a"], M, (w, h), flags=cv2.INTER_LINEAR)
    pm = penlib.scissor((aw > 127).astype(np.uint8) * 255, margin) if margin else aw
    sh = cv2.GaussianBlur(np.roll(np.roll(pm, 5, 0), 4, 1).astype(np.float32) / 255, (0, 0), 4)
    T *= 1 - 0.22 * sh * (1 - pm / 255.0)
    pa = pm.astype(np.float32) / 255
    T[:] = T * (1 - pa) + 0.985 * pa
    af = aw.astype(np.float32) / 255
    T[:] = T * (1 - af) + np.clip(tw, 0, 1) * af
    return np.vstack([M, [0, 0, 1]]) @ np.array([[1, 0, -ox], [0, 1, -oy], [0, 0, 1]], float)   # source -> picture


POSES = {}


def lay_man(T, P, n, foot_dst, s, deg=0.0, head=0.0, flip=False, upper=False):
    """The Daumier man as a two-piece cut-out: body (or the seated upper body) and the head on its own, pivoted
    at the neck. Returns the body transform (source -> picture)."""
    M = lay(T, P["upper" if upper else "body"], MAN_FOOT, foot_dst, s, deg=deg, flip=flip)
    nd = (M @ np.array([NECK[0], NECK[1], 1.0]))[:2]
    lay(T, P["head"], NECK, tuple(nd), s, deg=deg + (-head if flip else head), flip=flip, margin=0)
    POSES[n] = dict(crop="upper body (cut at the waist)" if upper else "full figure", flip=flip,
                    body_deg=round(deg, 1), head_deg=round(head, 1), scale=round(s, 3))
    return M


def src_to(M, p):
    return (M @ np.array([p[0], p[1], 1.0]))[:2]


# ------------------------------------------------------------------ lithographic crayon (HANDMADE)
def grain(h, w, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((h, w)).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.1)
    return (g - g.min()) / (g.max() - g.min() + 1e-6)


class Crayon:
    def __init__(self, w, h, seed):
        self.m = np.zeros((h, w), np.uint8)
        self.seed = seed
        self.k = 0

    def line(self, pts, w=4):
        self.k += 1
        penlib.brush_line(self.m, pts, w, self.seed + self.k, tremor=1.1)

    def poly(self, pts, w=4, closed=True):
        self.line(list(pts) + ([pts[0]] if closed else []), w)

    def hatch(self, x0, y0, x1, y1, step=9, w=2, ang=-60, clip=None):
        a = math.radians(ang)
        d = np.array([math.cos(a), math.sin(a)])
        L = (x1 - x0) + (y1 - y0)
        tmp = np.zeros_like(self.m)
        rnd = random.Random(self.seed + 7 * self.k)
        for s in np.arange(-L, L, step):
            p0 = np.array([x0 + s, y1])
            p1 = p0 + d * L * 2
            penlib.brush_line(tmp, [tuple(p0), tuple(p1)], w * rnd.uniform(0.8, 1.2), self.seed + int(s * 3) + self.k, tremor=0.6)
        box = np.zeros_like(self.m)
        if clip is None:
            box[int(y0):int(y1), int(x0):int(x1)] = 255
        else:
            cv2.fillPoly(box, [np.int32(np.array(clip) * 4)], 255, cv2.LINE_AA, shift=2)
        np.maximum(self.m, np.minimum(tmp, box), out=self.m)
        self.k += 1

    def apply(self, T, strength=0.92):
        g = grain(*T.shape, self.seed)
        d = self.m.astype(np.float32) / 255 * (0.82 + 0.18 * g)
        T *= 1 - strength * d
        return T


def letters(T, lines, cap, cx, y_base, seed, weight=0.13, align="centre"):
    m = pen99.letter(lines, cap, seed, weight=weight)
    h, w = m.shape
    x = int(cx - w / 2) if align == "centre" else int(cx - cap * 0.6)
    top = int(y_base - cap * 1.15)
    sub = np.zeros(T.shape, np.uint8)
    ys, xs, ye, xe = max(0, top), max(0, x), min(T.shape[0], top + h), min(T.shape[1], x + w)
    sub[ys:ye, xs:xe] = m[ys - top:ye - top, xs - x:xe - x]
    T *= 1 - sub.astype(np.float32) / 255
    return w


# ------------------------------------------------------------------ set pieces in crayon
def wall_tone(c, w, h, floor, seed):
    """Daumier-like loose vertical wall strokes and a floor line."""
    rnd = random.Random(seed)
    for k in range(int(min(w, 640) / 46)):
        x = rnd.uniform(0, w)
        c.line([(x, rnd.uniform(0, h * 0.2)), (x + rnd.uniform(-6, 6), floor - rnd.uniform(0, 60))], w=rnd.uniform(0.8, 1.6))
    c.line([(0, floor), (w, floor + 4)], 3)
    c.hatch(0, floor + 6, w, h, step=46, w=1.6, ang=-6)


def desk(c, x0, top, w, floor):
    c.poly([(x0 - 14, top), (x0 + w + 14, top), (x0 + w + 14, top + 22), (x0 - 14, top + 22)], 4)
    c.poly([(x0, top + 22), (x0 + w * 0.4, top + 22), (x0 + w * 0.4, floor), (x0, floor)], 3)
    c.line([(x0 + w, top + 22), (x0 + w, floor)], 6)
    c.hatch(x0 + 4, top + 26, x0 + w * 0.4 - 4, floor - 2, step=8, w=1.8, ang=-65)
    for k in range(2):
        y = top + 70 + k * (floor - top - 100) / 2
        c.line([(x0 + 18, y), (x0 + w * 0.4 - 18, y)], 2)


def memo_slip(T, x, y, s, seed, deg=-4):
    m = pen99.letter(["4:15 - open SERVICE door.", "Key in cupboard."], int(22 * s), seed)
    h, w = m.shape
    pad = int(10 * s)
    box = np.ones((h + 2 * pad, w + 2 * pad), np.float32)
    box[pad:pad + h, pad:pad + w] = 1 - m.astype(np.float32) / 255
    M = cv2.getRotationMatrix2D((box.shape[1] / 2, box.shape[0] / 2), -deg, 1.0)
    M[:, 2] += np.array([x, y]) - np.array([box.shape[1] / 2, box.shape[0] / 2])
    bw = cv2.warpAffine(box, M, (T.shape[1], T.shape[0]), borderValue=0)
    am = cv2.warpAffine(np.ones_like(box), M, (T.shape[1], T.shape[0]), borderValue=0)
    sh = cv2.GaussianBlur(np.roll(np.roll(am, 4, 0), 3, 1), (0, 0), 3)
    T *= 1 - 0.25 * sh * (1 - am)
    T[:] = T * (1 - am) + bw * am
    edge = cv2.morphologyEx((am > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    T *= 1 - 0.7 * edge


def window(c, T, x0, y0, w, h, sill, seed, cap=26, bars=True):
    c.poly([(x0 - 24, y0), (x0 + w + 24, y0), (x0 + w + 24, y0 + 64), (x0 - 24, y0 + 64)], 4)
    c.line([(x0, y0 + 64), (x0, sill)], 7)
    c.line([(x0 + w, y0 + 64), (x0 + w, sill)], 7)
    if bars:
        c.line([(x0 + w / 2, y0 + 64), (x0 + w / 2, sill)], 4)
        c.line([(x0, y0 + 64 + (sill - y0 - 64) * 0.45), (x0 + w, y0 + 64 + (sill - y0 - 64) * 0.45)], 4)
    else:       # one pane of glass, shown by two glint strokes in its top corner
        for k, a in enumerate((52, 34)):
            c.line([(x0 + w - a - 10, y0 + 76 + a), (x0 + w - 10, y0 + 76)], 1.5)
    c.poly([(x0 - 40, sill), (x0 + w + 40, sill), (x0 + w + 40, sill + 26), (x0 - 40, sill + 26)], 4)
    c.hatch(x0 - 24, sill + 30, x0 + w + 24, y0 + h, step=11, w=2.2, ang=-70)
    letters(T, ["TICKET OFFICE"], cap, x0 + w / 2, y0 + 46, seed, weight=0.17)


def clock(c, cx, cy, r, swing=8):
    c.poly([(cx + (r + 10) * math.cos(t), cy + (r + 10) * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 50, endpoint=False)], 6)
    c.poly([(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 50, endpoint=False)], 2)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        L = 0.22 if k % 3 == 0 else 0.12
        c.line([(cx + r * .9 * math.cos(a), cy + r * .9 * math.sin(a)), (cx + r * (.9 - L) * math.cos(a), cy + r * (.9 - L) * math.sin(a))], 3)
    ah, am = math.radians(4 * 30 + 5 - 90), math.radians(60 - 90)
    c.line([(cx, cy), (cx + r * .5 * math.cos(ah), cy + r * .5 * math.sin(ah))], 7)
    c.line([(cx, cy), (cx + r * .78 * math.cos(am), cy + r * .78 * math.sin(am))], 4)
    y0, y1 = cy + r + 10, cy + r * 2.6
    c.poly([(cx - r * .6, y0), (cx + r * .6, y0), (cx + r * .6, y1), (cx, y1 + r * .3), (cx - r * .6, y1)], 4)
    b = math.radians(swing)
    bx, by = cx + r * 1.1 * math.sin(b), y0 + r * 1.2 * math.cos(b)
    c.line([(cx, y0 + 6), (bx, by)], 2)
    c.poly([(bx + r * .14 * math.cos(t), by + r * .14 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)], 3)
    c.hatch(cx + r * .3, y0 + 4, cx + r * .58, y1 - 4, step=7, w=1.6, ang=-75)


def cupboard_open(c, x0, y0, w, h, seed):
    c.line([(x0 - 14, y0 - 22), (x0 + w + 14, y0 - 22)], 7)
    c.poly([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], 5)
    for f in (0.33, 0.66):
        c.line([(x0 + 6, y0 + h * f), (x0 + w - 6, y0 + h * f)], 4)
    c.hatch(x0 + 6, y0 + 6, x0 + w - 6, y0 + h - 6, step=14, w=2.6, ang=-55)       # the dark inside
    dx = w * 0.62
    leaf = [(x0, y0), (x0 - dx, y0 - h * 0.06), (x0 - dx, y0 + h * 1.06), (x0, y0 + h)]
    c.poly(leaf, 5)
    c.poly([(x0 - dx * .2, y0 + h * .08), (x0 - dx * .82, y0 + h * .03), (x0 - dx * .82, y0 + h * .48), (x0 - dx * .2, y0 + h * .48)], 2)
    c.poly([(x0 - dx * .2, y0 + h * .56), (x0 - dx * .82, y0 + h * .56), (x0 - dx * .82, y0 + h * 1.0), (x0 - dx * .2, y0 + h * .94)], 2)
    return leaf


def key_on_hook(c, T, x, y, s, seed, P=None):
    """The ANRC 1922 key cutout hung by its bow on a crayon hook, on a pale ground scraped out of the dark
    cupboard (the litho scraper), with a crayon string to the SERVICE tag."""
    m = np.zeros(T.shape, np.uint8)
    cv2.ellipse(m, (int(x + 22 * s), int(y + 78 * s)), (int(66 * s), int(98 * s)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    T[:] = np.maximum(T, cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 10) * 0.88)
    c.line([(x - 18 * s, y), (x + 18 * s, y)], 5)
    c.line([(x, y), (x, y + 16 * s), (x + 8 * s, y + 22 * s)], 4)
    k = P["key"]
    ks = 150 * s / k["a"].shape[0]
    lay(T, k, (96, 30), (x + 2 * s, y + 18 * s), ks, deg=4, margin=0)
    c.line([(x + 10 * s, y + 34 * s), (x + 44 * s, y + 74 * s)], 2)
    tag = [(x + 40 * s, y + 66 * s), (x + 120 * s, y + 74 * s), (x + 116 * s, y + 104 * s), (x + 36 * s, y + 96 * s)]
    c.poly(tag, 3)
    letters(T, ["SERVICE"], int(16 * s), x + 78 * s, y + 94 * s, seed, weight=0.17)


def service_door(c, T, x0, y0, w, h, seed):
    c.line([(x0 - 16, y0 + h), (x0 - 16, y0 - 16), (x0 + w + 16, y0 - 16), (x0 + w + 16, y0 + h)], 6)
    c.poly([(x0, y0 + h), (x0, y0), (x0 + w, y0), (x0 + w, y0 + h)], 3)
    for (a, b, cc, d) in ((0.15, 0.30, 0.85, 0.56), (0.15, 0.63, 0.85, 0.93)):
        c.poly([(x0 + w * a, y0 + h * b), (x0 + w * cc, y0 + h * b), (x0 + w * cc, y0 + h * d), (x0 + w * a, y0 + h * d)], 2)
    c.hatch(x0 + 4, y0 + h * 0.62, x0 + w * 0.3, y0 + h - 4, step=16, w=1.8, ang=-80)
    c.poly([(x0 + w * .2, y0 + 30), (x0 + w * .8, y0 + 30), (x0 + w * .8, y0 + 30 + w * .26), (x0 + w * .2, y0 + 30 + w * .26)], 3)
    m = np.zeros(T.shape, np.uint8)
    cv2.rectangle(m, (int(x0 + w * .2) + 3, int(y0 + 33)), (int(x0 + w * .8) - 3, int(y0 + 27 + w * .26)), 255, -1)
    c.m[m > 0] = 0
    letters(T, ["SERVICE"], int(w * 0.13), x0 + w / 2, y0 + 30 + w * 0.19, seed, weight=0.17)
    c.line([(x0 + w - 24, y0 + h * .58), (x0 + w - 12, y0 + h * .58)], 6)


ARM = {}


def glue_strip(T, piece, src_end, src_dir, a, b, s, widths=(60, 60), round_start=False):
    """Glue a cut sleeve strip so that its end src_end sits at a and its axis src_dir points toward b."""
    d = np.array(b, float) - np.array(a, float)
    deg = math.degrees(math.atan2(d[1], d[0]) - math.atan2(src_dir[1], src_dir[0]))
    L = np.linalg.norm(d)
    # re-cut the strip as a sleeve: tapered from w0 (at src_end) to w1, its far end rounded (the elbow)
    p = dict(piece)
    ox, oy = p["origin"]
    hh, ww = p["a"].shape
    sd = np.array(src_dir, float)
    e0 = np.array(src_end, float) - [ox, oy]
    e1 = e0 + sd * (L / s)
    nrm = np.array([-sd[1], sd[0]])
    w0, w1 = widths
    m = np.zeros((hh, ww), np.uint8)
    poly = [e0 + nrm * w0 / 2, e1 + nrm * w1 / 2, e1 - nrm * w1 / 2, e0 - nrm * w0 / 2]
    cv2.fillPoly(m, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
    cv2.circle(m, (int(e1[0] * 4), int(e1[1] * 4)), int(w1 / 2 * 4), 255, -1, cv2.LINE_AA, shift=2)
    if round_start:
        cv2.circle(m, (int(e0[0] * 4), int(e0[1] * 4)), int(w0 / 2 * 4), 255, -1, cv2.LINE_AA, shift=2)
    p["a"] = np.minimum(m, piece["a"])
    return lay(T, p, src_end, tuple(a), s, deg=deg, margin=2)


def sleeve_arm(T, shoulder, elbow, wrist, wd, seed):
    """A coat sleeve in two segments (upper arm, forearm) cut as paper and worked in lithographic crayon:
    filled in a mid tone, cross-hatched like his coat, outlined; the forearm laid over the upper arm."""
    h, w = T.shape
    for a, b, ww, k in ((shoulder, elbow, wd * 1.05, 0), (elbow, wrist, wd, 1)):
        a, b = np.array(a, float), np.array(b, float)
        d = (b - a) / (np.linalg.norm(b - a) + 1e-6)
        nrm = np.array([-d[1], d[0]])
        a2 = a - d * ww * 0.35
        poly = [a2 + nrm * ww / 2, b + nrm * ww * 0.42, b - nrm * ww * 0.42, a2 - nrm * ww / 2]
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
        cv2.circle(m, tuple(int(v) for v in a), int(ww * 0.48), 255, -1, cv2.LINE_AA)
        mf = m.astype(np.float32) / 255
        T[:] = T * (1 - mf) + 0.80 * mf                    # the sleeve's paper, a mid ground tone
        c = Crayon(w, h, seed + 10 * k)
        ang = math.degrees(math.atan2(d[1], d[0]))
        x0, y0 = np.min(poly, 0) - 20
        x1, y1 = np.max(poly, 0) + 20
        c.hatch(x0, y0, x1, y1, step=7, w=1.7, ang=ang + 70, clip=[tuple(p) for p in poly])
        c.hatch(x0, y0, x1, y1, step=11, w=1.4, ang=ang - 40, clip=[tuple(p) for p in poly])
        c.line([tuple(poly[0]), tuple(poly[1])], 3.5)
        c.line([tuple(poly[3]), tuple(poly[2])], 3.5)
        c.apply(T, 0.85)


# ------------------------------------------------------------------ pictures
def man_scale(height):
    return height / (1312 - 330)


def picture(n, w, h, P):
    T = np.ones((h, w), np.float32)
    c = Crayon(w, h, 2400 + 31 * n)
    if n == 1:      # E0: seated at the desk over the Company's memo, rising to obey (upper-body cut, leaning in)
        floor = h - 70
        wall_tone(c, w, h, floor, 2410)
        top = floor - 230
        # his office chair, pushed back as he rises: back rail and posts behind him, seat and legs beside the desk
        c.line([(232, top - 150), (330, top - 160)], 6)
        c.line([(236, top - 150), (242, top + 60)], 5)
        c.line([(326, top - 158), (322, top + 40)], 5)
        c.line([(238, top - 110), (326, top - 116)], 3)
        c.line([(220, top + 60), (330, top + 46)], 7)
        c.line([(226, top + 64), (220, floor)], 5)
        c.line([(300, top + 56), (306, floor - 8)], 4)
        c.hatch(240, top - 150, 322, top + 50, step=9, w=1.6, ang=-62)
        c.apply(T)
        s = man_scale(h * 0.86)
        # his waist cut sits just under the desk board; he leans forward over the memo, head bowed to read it
        lay_man(T, P, 1, (390, top + 24 + (MAN_FOOT[1] - WAIST_Y) * s), s, deg=7, head=14, upper=True)
        dm = np.zeros(T.shape, np.uint8)
        cv2.rectangle(dm, (316, int(top)), (604, int(floor)), 255, -1)
        T[dm > 0] = 0.985                       # the desk is a cut paper shape glued over his lap
        cd = Crayon(w, h, 2412)
        desk(cd, 330, top, 260, floor)
        cd.apply(T)
        memo_slip(T, 525, top + 2, 0.62, 2411, deg=-3)
    elif n == 2:    # E1-E2: at the window she asks; he turns from her to the clock and looks up at it
        floor = h - 70
        wall_tone(c, w, h, floor, 2420)
        clock(c, 78, 96, 50)
        c2 = Crayon(w, h, 2425)
        T2 = np.ones_like(T)
        c.apply(T)
        s = man_scale(h * 0.86)
        lay_man(T, P, 2, (245, floor + 4), s, deg=-2, head=-16, flip=True)
        # the woman behind the glass (her bust, facing him), then the window frame over her
        lay(T, P["woman"], WOMAN_BASE, (w - 200, floor - 128), 0.74, flip=True, margin=3)
        window(c2, T2, w - 300, 70, 230, floor - 70, floor - 140, 2426, cap=22, bars=False)
        c2.apply(T)
        T *= T2
    elif n == 3:    # E3: thanks, and she goes; he bows the public out
        floor = h - 70
        wall_tone(c, w, h, floor, 2430)
        c2 = Crayon(w, h, 2435)
        T2 = np.ones_like(T)
        c.apply(T)
        s = man_scale(h * 0.84)
        lay_man(T, P, 3, (200, floor + 4), s, deg=6, head=12)
        lay(T, P["woman"], WOMAN_BASE, (w - 165, floor - 128), 0.74, deg=-4, margin=3)
        window(c2, T2, w - 300, 70, 230, floor - 70, floor - 140, 2436, cap=22, bars=False)
        c2.apply(T)
        T *= T2
    else:           # E4-E5: the cupboard open, the key on its hook; his own forearm raised, pencil at his chin
        floor = h - 120
        wall_tone(c, w, h, floor, 2440)
        clock(c, 250, 200, 80, swing=-6)
        leaf = cupboard_open(c, 980, 260, 380, floor - 300, 2441)
        service_door(c, T, 1560, 230, 300, floor - 230, 2442)
        c.apply(T)
        ck = Crayon(w, h, 2444)
        key_on_hook(ck, T, 1150, 300, 2.2, 2443, P)
        ck.apply(T)
        s = man_scale(h * 0.84)
        M = lay_man(T, P, 4, (600, floor + 6), s, deg=0, head=4 if STATE["big"] == "full" else 0)
        if STATE["big"] == "full":
            # the arm: a coat sleeve cut and drawn in crayon, hinged at his far shoulder; the elbow at his side, the
            # forearm raised across the waistcoat; the barrister's hand (same plate) joined at its cuff, fingers
            # at the chin, holding a crayon pencil
            chin = src_to(M, (580, 468))
            hand_tip = chin + np.array([-8, -26]) * s
            v = np.array(HAND_WRIST, float) - np.array(HAND_TIP, float)
            want = np.array([0.32, 1.0])                       # wrist below and a little forward of the tip
            deg = math.degrees(math.atan2(want[1], want[0]) - math.atan2(v[1], v[0]))
            Mh = lay(np.ones_like(T), P["hand"], HAND_TIP, tuple(hand_tip), s * 0.95, deg=deg, margin=0)
            wrist = src_to(Mh, HAND_WRIST)
            shoulder = src_to(M, (548, 556))
            elbow = src_to(M, (642, 742))
            glue_strip(T, P["sl_u"], (367, 640), (0, 1), shoulder, elbow, s, widths=(64, 60), round_start=True)
            glue_strip(T, P["sl_f"], (365, 846), (0, -1), wrist, elbow, s, widths=(50, 60))
            lay(T, P["hand"], HAND_TIP, tuple(hand_tip), s * 0.95, deg=deg, margin=2)
            ARM.update(shoulder=shoulder.round(1).tolist(), elbow=elbow.round(1).tolist(), wrist=wrist.round(1).tolist(),
                       chin=chin.round(1).tolist(), hand_tip=hand_tip.round(1).tolist())
            cp = Crayon(w, h, 2449)
            p0, p1 = hand_tip + np.array([40, 34]) * s, chin + np.array([6, 4]) * s
            d = (p1 - p0) / np.linalg.norm(p1 - p0)
            nn = np.array([-d[1], d[0]]) * 6
            cp.poly([tuple(p0 + nn), tuple(p1 + nn), tuple(p1 - nn), tuple(p0 - nn)], 3)
            cp.line([tuple(p0), tuple(p1)], 5)
            cp.apply(T, 1.0)
    # the print's ruled border
    b = Crayon(w, h, 2490 + n)
    b.poly([(3, 3), (w - 3, 3), (w - 3, h - 3), (3, h - 3)], 3)
    b.apply(T)
    return T


CAPTIONS = {
    1: ["The Company's memo: '4:15 - open SERVICE door.", "Key in cupboard.' He rises at once to obey."],
    2: ["- Pardon me — have you the right time?", "- Ten past four, by the clock."],
    3: ["- Much obliged!", "The public, served, withdraws."],
    4: ["THE AGENT AT HIS POST.  - Well, here I am... and what for?",
        "The Company's key hangs safe on the Company's hook; the Company's door stays shut.",
        "Nothing whatever has been lost, except the errand."],
}


def build():
    T = np.ones((H, W), np.float32)
    P = load_pieces()
    letters(T, ["THE COMPANY'S MEN."], 54, W / 2, 200, 2401, weight=0.15)
    letters(T, ["7."], 40, 2050, 196, 2402, weight=0.15)
    VW, VH, VY = 640, 600, 260
    xs = [110, 780, 1450]
    for i in range(3):
        if i + 1 > STATE["pictures"]:
            continue
        pic = picture(i + 1, VW, VH, P)
        T[VY:VY + VH, xs[i]:xs[i] + VW] = pic
        for j, l in enumerate(CAPTIONS[i + 1]):
            letters(T, [l], 27, xs[i] + VW / 2, VY + VH + 50 + j * 40, 2460 + 10 * i + j)
    BX, BY, BW, BH = 110, 1020, 1980, 1460
    if STATE["pictures"] >= 4:
        pic = picture(4, BW, BH, P)
        T[BY:BY + BH, BX:BX + BW] = pic
        for j, l in enumerate(CAPTIONS[4]):
            letters(T, [l], 40 if j == 0 else 34, W / 2, BY + BH + 66 + j * 54, 2470 + j, weight=0.15 if j == 0 else 0.13)
    # print in one tone on the sheet (the stone holds no finer grain than ~1 px)
    T = cv2.GaussianBlur(T, (0, 0), 0.7)
    sheet = pen99.sheet99().astype(np.float32)
    img = sheet * T[..., None] + INK1 * (1 - T[..., None])
    img = np.clip(np.round(img), 0, 255).astype(np.uint8)
    pen99.folio(img, N, TITLE)
    return img


if __name__ == "__main__":
    page = build()
    im = Image.fromarray(page)
    im.save(b1m2.MASTERS / f"{N:02d}-{PID}.png", optimize=True)
    jp = b1m2.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    im.save(jp, quality=90)
    print("jpeg bytes", jp.stat().st_size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for k, big in ((0, "full"), (1, "full"), (2, "full"), (3, "full"), (4, "none"), (4, "full")):
            STATE["pictures"], STATE["big"] = k, big
            frames.append(build())
        b1m2.save_beats(N, frames)
