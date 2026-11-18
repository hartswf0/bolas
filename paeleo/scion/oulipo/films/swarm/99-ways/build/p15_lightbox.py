"""Page 15 Lightbox (medium and material; medium: paper-hands).

Six translucent animation sheets laid one over another on a lit lightbox, one beat (E0-E5) per sheet, seen
through the agent's eyes: his cut-paper hands (black paper, opaque) enter from the bottom of each field;
the set is pen-drawn on the sheet; the balloons are glued slips of heavier bond (they block more light);
the brass key is the ANRC 1922 key cutout (99-ways-template piece) glued down, so it is opaque like the hands.
Each later sheet overlaps the earlier ones, and the lightbox shows the earlier beats through it, softer and
fainter for every sheet above them (transmitted light model: T, scatter blur and room-light reflection per
sheet). Peg holes and tape let the bare light through.
Everything is HANDMADE in code (the sheets' fibre and cloud, the hands, the pen set, the optics) except the key
cutout and the 1934 sheet used for the margin. Lettering: the shared pen hand. Folio by pen99.folio.
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

N, PID, TITLE = 15, "lightbox", "Lightbox"
SW, SH = 1180, 960
# where each sheet lies on the page (x, y, rotation deg): a reading order zig-zag, each overlapping its elders
LAY = [(110, 110, -0.8), (910, 250, 1.0), (150, 860, 0.6), (900, 1150, -1.1), (120, 1610, 0.9), (905, 1760, -0.5)]
GLASS = np.array([255, 251, 240], np.float32) / 255
ROOM = np.array([236, 232, 222], np.float32) / 255
T_SHEET, R_SHEET = 0.52, 0.41       # tracing sheet: transmittance and diffuse room reflection
T_BOND, R_BOND = 0.34, 0.50         # bond paper slips (balloons, tags, memo slip)
T_TISSUE, R_TISSUE = 0.30, 0.10     # grey tissue (the stranger behind the glass)
T_BLACK, R_BLACK = 0.02, 0.05       # black cut paper (hands, key)
INK_T = 0.06                        # pen ink on the sheet
SCATTER = 2.2                       # blur (px) of what lies under each sheet
rng0 = np.random.default_rng(1500)


def cloud(h, w, rng, scale):
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return cv2.GaussianBlur(cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), scale * 0.35)


def fibres(h, w, rng, n):
    f = np.zeros((h, w), np.float32)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a, L, c = rng.uniform(0, math.pi), rng.uniform(10, 60), rng.normal(0, 0.03)
        pts = [(x + math.cos(a + c * s) * s, y + math.sin(a + c * s) * s) for s in np.linspace(0, L, 6)]
        cv2.polylines(f, [np.int32(pts)], False, float(rng.choice([-1.0, 1.0]) * rng.uniform(0.4, 1.0)), 1, cv2.LINE_AA)
    return cv2.GaussianBlur(f, (0, 0), 0.7)


# ------------------------------------------------------------------ a sheet: layers in its own frame
class Sheet:
    def __init__(self, k):
        self.k = k
        rng = np.random.default_rng(1510 + k)
        self.paper = np.ones((SH, SW), np.float32)
        self.ink = np.zeros((SH, SW), np.float32)
        self.bond = np.zeros((SH, SW), np.float32)
        self.bond_ink = np.zeros((SH, SW), np.float32)
        self.tissue = np.zeros((SH, SW), np.float32)
        self.black = np.zeros((SH, SW), np.float32)
        self.holes = np.zeros((SH, SW), np.float32)
        self.tex = 1 + cloud(SH, SW, rng, 40) * 0.016 + cloud(SH, SW, rng, 10) * 0.010 + fibres(SH, SW, rng, SW * SH // 260) * 0.04
        for hx in (SW / 2 - 150, SW / 2, SW / 2 + 150):          # three punched peg holes
            if hx == SW / 2:
                cv2.circle(self.holes, (int(hx), 34), 15, 1.0, -1, cv2.LINE_AA)
            else:
                cv2.ellipse(self.holes, (int(hx), 34), (34, 10), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        self.pen_rect(50, 70, SW - 50, SH - 40, 4, 1520 + k)
        put = letter([str(k + 1)], 40, 1530 + k, weight=0.14)      # sheet number, top right corner
        blit_mask_f(self.ink, put, SW - 110, 8)

    # pen on the sheet
    def pen(self, pts, w, seed):
        m = np.zeros((SH, SW), np.uint8)
        penlib.brush_line(m, pts, w, seed)
        self.ink = np.maximum(self.ink, m / 255.0)

    def pen_rect(self, x0, y0, x1, y1, w, seed):
        for i, (a, b) in enumerate((((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))):
            self.pen([a, b], w, seed + i)

    def pen_circle(self, cx, cy, r, w, seed, n=80):
        a = np.linspace(0, 2 * np.pi, n)
        self.pen([(cx + r * math.cos(t), cy + r * math.sin(t)) for t in a], w, seed)

    def letters(self, lines, cap, cx, cy, seed, layer="ink", weight=0.13):
        m = letter(lines, cap, seed, weight)
        tgt = getattr(self, layer)
        blit_mask_f(tgt, m, int(cx - m.shape[1] / 2), int(cy - m.shape[0] / 2))

    def cut(self, layer, polys):
        m = np.zeros((SH, SW), np.uint8)
        for p in polys:
            c = cv2.approxPolyDP(np.int32(np.asarray(p) * 4).reshape(-1, 1, 2), 4, True)     # scissor facets
            cv2.fillPoly(m, [c], 255, cv2.LINE_AA, shift=2)
        tgt = getattr(self, layer)
        np.maximum(tgt, m / 255.0, out=tgt)

    def slip(self, lines, cap, cx, cy, seed, pad=18):
        m = letter(lines, cap, seed)
        h, w = m.shape
        x0, y0 = cx - w / 2 - pad + cap * 0.4, cy - h / 2 - pad * 0.6
        rnd = np.random.default_rng(seed)
        poly = [(x0 + rnd.uniform(-3, 3), y0 + rnd.uniform(-3, 3)), (x0 + w + 2 * pad - cap * 0.8 + rnd.uniform(-3, 3), y0),
                (x0 + w + 2 * pad - cap * 0.8, y0 + h + pad * 1.2), (x0, y0 + h + pad * 1.2 + rnd.uniform(-3, 3))]
        self.cut("bond", [poly])
        blit_mask_f(self.bond_ink, m, int(cx - w / 2), int(cy - h / 2))

    def balloon(self, lines, cap, at, tip, seed, tail_w=0.26):
        b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=tail_w)
        cx, cy = b["center"]
        ox, oy = int(round(at[0] - cx)), int(round(at[1] - cy))
        blit_mask_f(self.bond, b["paper"], ox, oy)
        blit_mask_f(self.bond_ink, b["ink"], ox, oy)


def blit_mask_f(dst, m, x0, y0):
    m = m.astype(np.float32) / (255.0 if m.dtype == np.uint8 else 1.0)
    h, w = m.shape
    H0, W0 = dst.shape
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
    if xe > xs and ye > ys:
        np.maximum(dst[ys:ye, xs:xe], m[ys - y0:ye - y0, xs - x0:xe - x0], out=dst[ys:ye, xs:xe])


# ------------------------------------------------------------------ cut-paper hands (first person, from below)
def capsule(p, q, r0, r1, n=14):
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    a = math.atan2(d[1], d[0])
    out = [q + r1 * np.array([math.cos(a + t), math.sin(a + t)]) for t in np.linspace(-np.pi / 2, np.pi / 2, n)]
    out += [p + r0 * np.array([math.cos(a + t), math.sin(a + t)]) for t in np.linspace(np.pi / 2, 3 * np.pi / 2, n)]
    return np.array(out)


def rot(v, deg):
    a = math.radians(deg)
    return np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)])


def hand(wrist, deg, s, side="R", curl=(0, 0, 0, 0), thumb=30, arm=900, cuff=False):
    """Back of a hand seen from above, fingers pointing along `deg` (0 = up the page), wrist at `wrist`.
    curl: per finger 0..1 (index..little) shortens the finger as it bends under. Returns (black polys, tissue polys)."""
    sg = 1 if side == "R" else -1
    W = np.asarray(wrist, float)
    up = rot((0, -1), deg)
    rt = rot((1, 0), deg)
    L = lambda x, y: W + rt * x * s * sg + up * y * s
    palm = [L(-46, 0), L(46, 0), L(54, 50), L(50, 98), L(-44, 104), L(-54, 52)]
    polys = [np.array(palm)]
    knuck = [(-34, 100), (-11, 108), (12, 106), (34, 96)]
    lens = [70, 78, 72, 56]
    for i, ((kx, ky), ln) in enumerate(zip(knuck, lens)):
        c = curl[i]
        spread = (-6 + 4 * i) * sg
        tipv = rot((0, -1), deg + spread)
        k = L(kx, ky)
        tip = k + tipv * ln * s * (1 - 0.7 * c)
        polys.append(capsule(k, tip, 12.5 * s, 10.5 * s))
    # thumb from the inner side of the palm
    tb = L(48 if sg < 0 else -48, 30) if False else L(-50, 34)
    tv = rot((0, -1), deg - thumb * sg)
    polys.append(capsule(tb, tb + tv * 62 * s, 14 * s, 11 * s))
    # forearm down out of the field
    fa = capsule(W - up * 10 * s, W - up * arm * s, 44 * s, 56 * s)
    polys.append(fa)
    tissue = []
    if cuff:
        c0, c1 = W - up * 26 * s, W - up * 92 * s
        tissue.append(capsule(c0, c1, 54 * s, 58 * s, 10))
    return polys, tissue


def lay_hand(sh, *a, **k):
    polys, tissue = hand(*a, **k)
    sh.cut("black", polys)
    sh.cut("tissue", tissue)


def pencil(sh, p, q, w=9):
    sh.cut("black", [capsule(p, q, w, w * 0.4)])


# ------------------------------------------------------------------ the six sheets
def S0():
    """E0 at the desk: the memo slip under his left hand, the pencil in his right."""
    s = Sheet(0)
    s.pen([(60, 640), (1120, 560)], 6, 1601)           # desk edge, the far side
    s.pen([(60, 900), (1120, 900)], 3, 1602)
    s.pen_circle(980, 300, 46, 5, 1603)                  # inkwell
    s.pen_circle(980, 300, 20, 4, 1604)
    s.slip(["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 44, 560, 380, 1605, pad=26)
    lay_hand(s, (330, 820), 32, 1.55, "L", curl=(0, 0.1, 0.2, 0.3), thumb=50)
    lay_hand(s, (860, 870), -22, 1.55, "R", curl=(0.2, 0.55, 0.7, 0.75), thumb=10)
    pencil(s, (790, 700), (700, 520))
    return s


def window_set(s, seed, header=True):
    x0, y0, x1, y1 = 240, 150, 940, 760
    s.pen_rect(x0, y0, x1, y1, 6, seed)
    s.pen_rect(x0 + 20, y0 + 110, x1 - 20, y1 - 140, 4, seed + 5)
    s.pen([((x0 + x1) / 2, y0 + 110), ((x0 + x1) / 2, y1 - 140)], 4, seed + 10)
    s.pen([(x0 + 20, 420), (x1 - 20, 420)], 4, seed + 11)
    s.pen([(x0 - 120, y1 - 140), (x1 + 120, y1 - 140)], 7, seed + 12)       # the counter sill
    s.pen([(x0 - 120, y1 - 110), (x1 + 120, y1 - 110)], 4, seed + 13)
    if header:
        s.letters(["TICKET OFFICE"], 50, (x0 + x1) / 2, y0 + 58, seed + 20, weight=0.16)
    return (x0, y0, x1, y1)


def stranger_polys(cx, sill, s=1.0, face=1):
    """Her bust in grey tissue: cloche hat, head, coat shoulders (b1m2 outlines)."""
    polys = []
    for P in (S_COAT, S_COLLAR, S_HEAD, S_HAT, S_BOW):
        q = np.array(P, float) * s
        q[:, 0] *= face
        polys.append(catmull(q + np.array([cx, sill]), 8))
    return polys


def S1():
    """E1 the question: the stranger behind the window glass."""
    s = Sheet(1)
    x0, y0, x1, y1 = window_set(s, 1610)
    s.cut("tissue", stranger_polys(560, 620, 1.55))
    s.balloon(["Pardon me —", "have you the", "right time?"], 50, (900, 410), (700, 360), 1611)
    lay_hand(s, (1040, 960), -8, 1.4, "R", curl=(0.4, 0.6, 0.7, 0.7), thumb=20)
    pencil(s, (1000, 860), (930, 700))
    return s


def S2():
    """E2 the answer: he looks up at the clock (4:10); his own voice comes from below the field."""
    s = Sheet(2)
    cx, cy, r = 600, 360, 220
    s.pen_circle(cx, cy, r, 8, 1620)
    s.pen_circle(cx, cy, r - 26, 4, 1621)
    for k in range(12):
        a = math.radians(k * 30)
        s.pen([(cx + (r - 40) * math.sin(a), cy - (r - 40) * math.cos(a)),
               (cx + (r - 70 + (12 if k % 3 else 0)) * math.sin(a), cy - (r - 70 + (12 if k % 3 else 0)) * math.cos(a))],
              8 if k % 3 == 0 else 5, 1622 + k)
    am, ah = math.radians(60), math.radians(125)
    s.pen([(cx, cy), (cx + 0.5 * r * math.sin(ah), cy - 0.5 * r * math.cos(ah))], 14, 1640)
    s.pen([(cx, cy), (cx + 0.78 * r * math.sin(am), cy - 0.78 * r * math.cos(am))], 9, 1641)
    s.pen_rect(cx - 90, cy + r + 10, cx + 90, cy + r + 230, 6, 1642)          # pendulum case
    s.pen([(cx, cy + r + 20), (cx + 22, cy + r + 180)], 4, 1646)
    s.pen_circle(cx + 22, cy + r + 190, 20, 5, 1647)
    s.balloon(["Ten past four,", "by the clock."], 50, (290, 610), (360, 1000), 1648)
    return s


def S3():
    """E3 the thanks: she leaves the window; her hat goes out at its right edge."""
    s = Sheet(3)
    x0, y0, x1, y1 = window_set(s, 1650)
    s.cut("tissue", stranger_polys(880, 620, 1.55, face=-1))
    # the window frame masks the part of her already past the jamb: re-cut it out of the tissue
    s.tissue[:, int(x1) - 22:] = 0
    s.balloon(["Much", "obliged!"], 52, (360, 330), (600, 360), 1651)
    lay_hand(s, (230, 980), 6, 1.4, "L", curl=(0.3, 0.4, 0.5, 0.6), thumb=40)
    return s


def cupboard_set(s, seed, open_=True):
    x0, y0, x1, y1 = 360, 110, 900, 900
    s.pen_rect(x0, y0, x1, y1, 7, seed)
    s.pen([(x0 - 30, y0 - 20), (x1 + 30, y0 - 20)], 7, seed + 4)
    for fy in (420, 700):
        s.pen([(x0, fy), (x1, fy)], 6, seed + fy)
    s.pen([(x0, y0), (x0 - 200, y0 - 60), (x0 - 200, y1 + 60), (x0, y1)], 7, seed + 7)       # the leaf, swung out
    s.pen_rect(x0 - 175, y0 + 40, x0 - 40, y0 + 330, 4, seed + 8)
    s.pen_rect(x0 - 175, y0 + 420, x0 - 40, y1 - 40, 4, seed + 9)
    return (x0, y0, x1, y1)


def key_on_hook(s, kx, ky, scale, seed):
    s.pen([(kx - 40, ky - 36), (kx + 6, ky - 36), (kx + 6, ky - 6)], 9, seed)
    m = np.zeros((SH, SW), np.uint8)
    paste_mask(m, key_alpha(), kx + 4, ky + 723 * scale / 2 - 12, scale)
    s.black = np.maximum(s.black, m / 255.0)
    s.slip(["SERVICE"], 34, kx + 120, ky + 270 * scale / 0.45, seed + 1, pad=14)


def S4():
    """E4 the open cupboard: his left hand on the leaf, the brass key on its hook in plain view."""
    s = Sheet(4)
    x0, y0, x1, y1 = cupboard_set(s, 1660)
    key_on_hook(s, 690, 160, 0.45, 1670)
    lay_hand(s, (120, 760), 44, 1.35, "L", curl=(0.5, 0.5, 0.5, 0.5), thumb=60)
    return s


def S5():
    """E5 the forgetting: the key still on its hook, the SERVICE door shut, the pencil going up to his chin."""
    s = Sheet(5)
    x0, y0, x1, y1 = cupboard_set(s, 1680)
    key_on_hook(s, 690, 160, 0.45, 1690)
    s.pen_rect(960, 160, 1130, 900, 6, 1691)                  # the SERVICE door at the right edge
    s.pen_circle(990, 560, 12, 5, 1692)
    s.slip(["SERVICE"], 34, 1045, 240, 1693, pad=12)
    lay_hand(s, (640, 1060), -38, 1.9, "R", curl=(0.3, 0.6, 0.75, 0.8), thumb=10)
    pencil(s, (560, 900), (420, 700), w=12)
    s.balloon(["Well, here I am...", "and what for?"], 50, (250, 560), (330, 1000), 1694)
    return s


SHEETS = [S0, S1, S2, S3, S4, S5]


# ------------------------------------------------------------------ the lightbox optics
def place(a, k, border=0.0):
    x, y, deg = LAY[k]
    M = cv2.getRotationMatrix2D((SW / 2, SH / 2), -deg, 1.0)
    M[0, 2] += x
    M[1, 2] += y
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=border)


def render(n_sheets=6):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lamp = 1.0 - 0.10 * (((xx - W * 0.5) / (W * 0.7)) ** 2 + ((yy - H * 0.47) / (H * 0.7)) ** 2)
    I = GLASS[None, None] * lamp[..., None]
    for k in range(n_sheets):
        s = SHEETS[k]() if not isinstance(SHEETS[k], Sheet) else SHEETS[k]
        cover = place(s.paper, k)
        tex = place(s.tex, k, 1.0)
        holes = place(s.holes, k)
        ink = place(s.ink, k)
        bond = place(s.bond, k)
        bink = place(s.bond_ink, k)
        tis = place(s.tissue, k)
        blk = place(s.black, k)
        under = cv2.GaussianBlur(I, (0, 0), SCATTER)
        T = T_SHEET * tex
        R = R_SHEET
        T = T * (1 - tis) + T_TISSUE * tis
        R = R * (1 - tis) + R_TISSUE * tis
        T = T * (1 - bond) + T_BOND * tex * bond
        R = R * (1 - bond) + R_BOND * bond
        T = T * (1 - blk) + T_BLACK * blk
        R = R * (1 - blk) + R_BLACK * blk
        inkall = np.maximum(ink * (1 - bond), bink)
        T = T * (1 - inkall * (1 - INK_T))
        R = R * (1 - inkall * 0.85)
        T = T * (1 - holes) + holes
        R = R * (1 - holes)
        lit = under * T[..., None] + ROOM[None, None] * R[..., None]
        # paper edge: a thin darker line where the sheet ends (its cut thickness)
        edge = np.clip(cv2.GaussianBlur(cover, (0, 0), 1.2) - cover, 0, 1) + np.clip(cover - cv2.erode(cover, np.ones((3, 3), np.uint8)), 0, 1)
        lit *= (1 - 0.25 * np.clip(edge, 0, 1))[..., None]
        c = cover[..., None]
        I = I * (1 - c) + lit * c
        # tape: two translucent strips at the sheet's top corners
        for (tx, ty) in ((60, 60), (SW - 60, 60)):
            tm = np.zeros((SH, SW), np.float32)
            cv2.fillPoly(tm, [np.int32(cv2.boxPoints(((tx, ty), (150, 46), 45 if tx < SW / 2 else -45)))], 1.0, cv2.LINE_AA)
            tm = place(tm, k)
            I = I * (1 - tm[..., None]) + (I * 0.93 + np.array([0.04, 0.03, 0.0])) * tm[..., None]
    return np.clip(I * 255, 0, 255)


def build(n=6):
    return render(n)


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        save_beats(N, [np.asarray(Image.fromarray(finish(build(k))).resize((960, 1242), Image.LANCZOS)) for k in range(1, 7)])
