"""Zazie en papier: cut-paper head rig for the test shot (S3 laugh -> S4 jump cut).

HANDMADE puppet. Every piece is a scissor-cut polygon whose fill is a crop of a real
paper scan (Commons "Kraft tileable 1024x1024.png", public domain) dyed to the piece
colour by multiply. Pieces carry real layered drop shadows (light: overcast, upper left).
All coordinates are 2x picture pixels (picture 1440x1080 -> 720x540).

SCION #2 (Reiniger): pinned pieces, replacement mouths/eyes, exposure sheet.
SCION #41 (secondary dynamics): fringe strands = chains of damped angular springs.
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageChops

PW, PH = 1440, 1080
LIGHT = (8, 10)            # drop-shadow offset (2x px) = 4-5 px at 720
SH_BLUR, SH_A = 7, 0.40

# --------------------------------------------------------------- palette (sampled from reference)
HAIR = dict(shadow=(44, 21, 4), dark=(65, 35, 18), deep=(54, 28, 12), mid=(86, 58, 40), warm=(96, 62, 40),
            crown=(104, 77, 60), lit=(118, 91, 72), sheen=(132, 104, 82))
SKIN = dict(forehead=(182, 120, 94), cheek=(180, 112, 89), neck=(165, 102, 75), tissue=(196, 104, 84),
            socket=(150, 90, 68), crease=(128, 72, 54))
LIP = (183, 103, 86)
LIP_HI = (196, 118, 98)
LIP_DK = (150, 76, 62)
TEETH = dict(front=(198, 180, 152), side=(170, 136, 110), back=(150, 110, 88))
MOUTH_IN = (34, 13, 4)
TONGUE = (150, 62, 52)
EYE_W = (176, 150, 126)
IRIS = (52, 30, 18)
LASH = (40, 20, 10)
COLLAR = (214, 96, 30)
COLLAR_F = (168, 66, 20)
JUMPER = (78, 58, 46)

_PAPER = None
_ROT = {}


def load_paper(path):
    global _PAPER
    k = np.asarray(Image.open(path).convert("L")).astype(np.float32)
    k = np.tile(k, (3, 3))                      # tileable scan -> 3072 sq
    k = (k - k.mean()) / 255.0
    _PAPER = k


def paper_tex(w, h, seed, scale=1.0, gain=1.7):
    """Crop of the real kraft scan, rotated per piece so the laid lines differ piece to piece."""
    r = np.random.default_rng(seed)
    key = int(seed) % 12
    if key not in _ROT:
        M = cv2.getRotationMatrix2D((1536, 1536), -90 + 15 * key, scale)
        _ROT[key] = cv2.warpAffine(_PAPER, M, (3072, 3072), borderMode=cv2.BORDER_REFLECT)
    big = _ROT[key]
    x0 = int(r.integers(200, 3072 - w - 200)) if w < 2600 else 0
    y0 = int(r.integers(200, 3072 - h - 200)) if h < 2600 else 0
    return 1.0 + gain * big[y0:y0 + h, x0:x0 + w]


class Piece:
    """An RGBA sprite of one cut piece (placed at ox, oy in rig coords)."""
    __slots__ = ("img", "ox", "oy", "name")

    def __init__(self, img, ox, oy, name=""):
        self.img, self.ox, self.oy, self.name = img, ox, oy, name


def cut(poly, colour, seed, name="", rough=1.0, tex_gain=1.7, alpha=1.0, edge_light=True, soft=0.0, polys=None):
    """Scissor-cut a polygon out of dyed paper. Returns a Piece."""
    polys = polys or [poly]
    xs = [p[0] for q in polys for p in q]; ys = [p[1] for q in polys for p in q]
    pad = 6
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    x1, y1 = int(math.ceil(max(xs))) + pad, int(math.ceil(max(ys))) + pad
    w, h = max(2, x1 - x0), max(2, y1 - y0)
    m = Image.new("L", (w, h), 0)
    for q in polys:
        ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in q], fill=255)
    a = np.asarray(m).astype(np.float32)
    if rough > 0:   # scissor wobble on the cut edge
        r = np.random.default_rng(seed + 991)
        nz = cv2.resize(r.normal(0, 1, (h // 5 + 2, w // 5 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        a = cv2.GaussianBlur(a, (0, 0), 1.2) + nz * 18 * rough
        a = np.clip((a - 128) * 3.0 + 128, 0, 255)
    if soft > 0:
        a = cv2.GaussianBlur(a, (0, 0), soft)
    t = paper_tex(w, h, seed, gain=tex_gain)
    col = np.clip(np.array(colour, np.float32)[None, None, :] * t[..., None], 0, 255)
    if edge_light:  # the cut edge catches the light on its upper-left side (paper thickness)
        e = a / 255.0
        sh = np.roll(np.roll(e, 2, 0), 2, 1)
        rim = np.clip(e - sh, 0, 1)[..., None]
        col = np.clip(col + rim * 12, 0, 255)   # r2: tamer paper-edge catchlight
    rgba = np.dstack([col, a * alpha]).astype(np.uint8)
    return Piece(Image.fromarray(rgba, "RGBA"), x0, y0, name)


class Sheet:
    """A transparent stage sheet. Pieces are laid in order; each throws its shadow only on paper beneath."""

    def __init__(self, w=PW, h=PH):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def lay(self, pc, dx=0, dy=0, shadow=True, sh_off=LIGHT, sh_a=SH_A, sh_blur=SH_BLUR, clip=None):
        x, y = int(round(pc.ox + dx)), int(round(pc.oy + dy))
        if shadow:
            al = pc.img.getchannel("A").filter(ImageFilter.GaussianBlur(sh_blur))
            S = Image.new("L", self.img.size, 0)
            S.paste(al, (x + sh_off[0], y + sh_off[1]))
            S = ImageChops.multiply(S, self.img.getchannel("A"))       # only on paper already laid
            S = S.point(lambda v: int(v * sh_a))
            dark = Image.new("RGBA", self.img.size, (24, 10, 2, 0)); dark.putalpha(S)
            self.img.alpha_composite(dark)
        if clip is not None:   # restrict piece to an existing mask (tissue overlays on the face sheet)
            im = pc.img.copy()
            cm = clip.crop((x, y, x + im.width, y + im.height))
            im.putalpha(ImageChops.multiply(im.getchannel("A"), cm))
            self.img.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else self._paste(im, x, y)
            return
        if x >= 0 and y >= 0:
            self.img.alpha_composite(pc.img, (x, y))
        else:
            self._paste(pc.img, x, y)

    def _paste(self, im, x, y):
        L = Image.new("RGBA", self.img.size, (0, 0, 0, 0)); L.paste(im, (x, y)); self.img.alpha_composite(L)


def brad(sheet, x, y, r=8):
    d = ImageDraw.Draw(sheet.img)
    d.ellipse((x - r + 3, y - r + 4, x + r + 3, y + r + 4), fill=(20, 10, 4, 90))
    d.ellipse((x - r, y - r, x + r, y + r), fill=(150, 116, 58, 255), outline=(84, 60, 26, 255), width=2)
    d.ellipse((x - r * .55, y - r * .6, x - r * .05, y - r * .15), fill=(206, 178, 112, 255))


# --------------------------------------------------------------- geometry helpers
def ribbon(path, w0, w1, cap=True):
    """A tapered strip along a polyline (list of points), width w0 at root -> w1 at tip."""
    P = np.asarray(path, np.float32)
    n = len(P)
    L, R = [], []
    for i in range(n):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, n - 1)]
        d = b - a; d /= (np.linalg.norm(d) + 1e-6)
        nx, ny = -d[1], d[0]
        u = i / (n - 1)
        w = w0 + (w1 - w0) * u ** 0.8
        L.append((P[i][0] + nx * w / 2, P[i][1] + ny * w / 2)); R.append((P[i][0] - nx * w / 2, P[i][1] - ny * w / 2))
    return L + R[::-1]


def catmull(pts, k=8):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.asarray, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for j in range(k):
            t = j / k
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.asarray(pts[-1]))
    return [tuple(map(float, p)) for p in out]


def ellipse_pts(cx, cy, rx, ry, n=48, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


# --------------------------------------------------------------- the rig (neutral head pose)
FACE_C = (748, 712)
NECK_PIN = (748, 1250)
CROWN = (742, 262)
EYES = ((642, 662), (866, 662))
MOUTH_C = (756, 888)


def face_outline():
    cx, cy = FACE_C
    pts = []
    for t in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        s, c = math.sin(t), -math.cos(t)          # c=1 top
        ry = 352 if c > 0 else 342
        rx = 256
        taper = 1 - 0.30 * max(0.0, -c) ** 2.2    # narrower chin
        bulge = 1 + 0.04 * math.exp(-((c + 0.15) / 0.3) ** 2)   # cheeks
        pts.append((cx + rx * s * taper * bulge, cy - ry * c))
    return pts


def build_static(seed=1960):
    """Pieces that never change shape (only move): face sheet, ears, neck, collar, nose, cheeks, back hair base."""
    P = {}
    P["jumper"] = cut([(260, 1080), (330, 1040), (560, 1010), (940, 1010), (1170, 1040), (1240, 1080), (1240, 1120), (260, 1120)],
                      JUMPER, seed + 1)
    P["neck"] = cut([(640, 930), (860, 930), (880, 1100), (620, 1100)], SKIN["neck"], seed + 2)
    P["collar_l"] = cut([(470, 1066), (560, 1040), (668, 1052), (716, 1092), (470, 1100)], COLLAR, seed + 3)
    P["collar_r"] = cut([(790, 1090), (842, 1050), (952, 1038), (1046, 1064), (1046, 1100)], COLLAR, seed + 4)
    P["collar_fold"] = cut([(668, 1052), (716, 1092), (700, 1100), (650, 1078)], COLLAR_F, seed + 5, edge_light=False)
    # ears (behind the face sheet's edge), with inner-ear shade
    P["ear_l"] = cut(ellipse_pts(492, 832, 42, 66, rot=0.15), SKIN["cheek"], seed + 6)
    P["ear_l_in"] = cut(ellipse_pts(484, 838, 20, 40, rot=0.15), SKIN["socket"], seed + 7, rough=0.4, edge_light=False)
    P["ear_r"] = cut(ellipse_pts(1000, 800, 42, 70, rot=-0.15), SKIN["neck"], seed + 8)
    P["ear_r_in"] = cut(ellipse_pts(1010, 806, 20, 44, rot=-0.15), SKIN["crease"], seed + 9, rough=0.4, edge_light=False)
    P["face"] = cut(face_outline(), SKIN["forehead"], seed + 10, rough=0.6)
    # jaw / chin-shadow tissue (darker, right side away from light) and eye-socket tissue
    P["jaw_tissue"] = cut([(960, 760), (1004, 820), (990, 920), (930, 1010), (840, 1060), (760, 1066), (830, 1010), (920, 930), (950, 840)],
                          SKIN["neck"], seed + 11, alpha=0.65, edge_light=False)
    P["socket_l"] = cut(ellipse_pts(640, 650, 92, 46), SKIN["socket"], seed + 12, alpha=0.38, edge_light=False, soft=6)
    P["socket_r"] = cut(ellipse_pts(866, 650, 92, 46), SKIN["socket"], seed + 13, alpha=0.48, edge_light=False, soft=6)
    # nose (r2): short folded tab with a rounded tip, lit face and shadow side, nostril wings
    P["nose"] = cut([(740, 676), (758, 684), (776, 752), (798, 782), (788, 800), (756, 808), (722, 800), (712, 782), (730, 752)],
                    (186, 124, 98), seed + 16)
    P["nose_sh"] = cut([(758, 684), (776, 752), (798, 782), (788, 800), (772, 770)], SKIN["socket"], seed + 17, edge_light=False, alpha=0.8)
    P["nostril_l"] = cut(ellipse_pts(734, 798, 11, 5, rot=0.3), (110, 52, 38), seed + 18, rough=0.2, edge_light=False, alpha=0.8)
    P["nostril_r"] = cut(ellipse_pts(780, 798, 11, 5, rot=-0.3), (100, 46, 34), seed + 19, rough=0.2, edge_light=False, alpha=0.8)
    return P


def tips(p0, p1, n, depth, seed, lean=0.0):
    """Scissor-snipped strand tips: a zigzag from p0 to p1 whose points hang down by up to `depth`."""
    r = np.random.default_rng(seed)
    out = []
    for i in range(2 * n + 1):
        u = i / (2 * n)
        x = p0[0] + (p1[0] - p0[0]) * u + r.uniform(-6, 6)
        y = p0[1] + (p1[1] - p0[1]) * u
        if i % 2 == 1:
            k = r.uniform(0.45, 1.0); y += depth * k; x += lean * depth * k
        out.append((x, y))
    return out


def _bob(seed, d, grow=1.0, dx=0, dy=0):
    c = (748, 600)
    L = [(470, 470), (520, 330), (640, 262), (760, 246), (880, 262), (990, 320), (1060, 430), (1090, 560), (1100, 700),
         (1112, 830), (1122, 915)]
    L += tips((1122, 915), (988, 900), 6, d, seed)
    L += [(985, 760), (520, 760)]
    L += tips((514, 905), (382, 895), 6, d, seed + 1)
    L += [(380, 840), (384, 700), (400, 580)]
    return [(c[0] + (x - c[0]) * grow + dx, c[1] + (y - c[1]) * grow + dy) for x, y in L]


def back_hair(wind, seed=1960):
    """r2: the bob is ONE dense mass built from overlapping under-layers in several browns (shadow, deep, dark),
    lit panels (mid, crown, lit) laid on the light side, and fine slivers on top. `wind` shears it to frame right."""
    def sh(pts, k):
        return [(x + k * wind * max(0.0, (y - 300) / 700) ** 1.3, y - 0.25 * k * wind * max(0.0, (y - 600) / 500)) for x, y in pts]
    P = [cut(sh(_bob(seed + 40, 64, 1.035, 8, 18), 84), HAIR["shadow"], seed + 40, rough=1.3),
         cut(sh(_bob(seed + 41, 52, 1.0), 76), HAIR["deep"], seed + 41, rough=1.2),
         cut(sh(_bob(seed + 42, 40, 0.975, -4, -6), 70), HAIR["dark"], seed + 42, rough=1.1)]
    left = [(470, 480), (530, 340), (650, 272), (720, 266), (610, 372), (540, 520), (508, 700), (510, 880)]
    left += tips((510, 880), (392, 884), 5, 34, seed + 43) + [(394, 700), (410, 580)]
    P.append(cut(sh(left, 66), HAIR["mid"], seed + 43, rough=1.0))
    right = [(992, 336), (1052, 440), (1082, 580), (1094, 720), (1106, 860)] + tips((1106, 870), (1030, 880), 3, 30, seed + 44) + \
            [(1036, 760), (1012, 560), (968, 420)]
    P.append(cut(sh(right, 76), HAIR["warm"], seed + 44, rough=1.0))
    crown = [(526, 366), (640, 276), (760, 258), (880, 274), (982, 334), (1024, 404), (900, 372), (760, 352), (620, 374), (540, 432)]
    P.append(cut(sh(crown, 40), HAIR["crown"], seed + 45, rough=0.9))
    lit = [(556, 356), (650, 292), (760, 274), (850, 284), (760, 304), (660, 334), (586, 390)]
    P.append(cut(sh(lit, 36), HAIR["lit"], seed + 46, rough=0.8))
    # fine slivers along the flow of the bob (paper shavings, 3-9 px at 720)
    r = np.random.default_rng(seed + 47)
    tones = [HAIR["lit"], HAIR["crown"], HAIR["warm"], HAIR["deep"], HAIR["sheen"], HAIR["mid"]]
    for i in range(10):
        side = -1 if i < 6 else 1
        u = r.uniform(0, 1)
        if side < 0:
            a = (590 - 80 * u + r.uniform(-8, 8), 330 + 100 * u)
            m = (480 - 40 * u + r.uniform(-10, 10), 600 + 40 * u)
            b = (470 - 30 * u + r.uniform(-10, 10), 840 + 40 * r.uniform(0, 1))
        else:
            a = (930 + 110 * u, 310 + 110 * u)
            m = (1040 + 40 * u + r.uniform(-15, 15), 600)
            b = (1060 + 40 * u + r.uniform(-15, 15), 860 + 40 * r.uniform(0, 1))
        w = r.uniform(5, 11)
        tone = tones[i % len(tones)] if side < 0 else tones[(i + 2) % len(tones)]
        P.append(cut(sh(ribbon(catmull([a, m, b], 6), w, 2.5), 72), tone, seed + 60 + i, rough=0.35, edge_light=False))
    return P


def crown_cap(seed=1960):
    """Piece laid over the fringe roots: the crown with the parting, snipped lower edge; the split pin goes through it."""
    pts = [(500, 440), (530, 352), (610, 290), (720, 254), (800, 252), (900, 272), (990, 326), (1030, 380)]
    pts += tips((1030, 390), (500, 430), 10, 44, seed + 90, lean=0.9)
    out = [cut(pts, HAIR["mid"], seed + 90, rough=0.8)]
    lit = [(560, 380), (620, 304), (720, 266), (800, 264), (700, 300), (630, 350)]
    out.append(cut(lit, HAIR["crown"], seed + 91, rough=0.6))
    r = np.random.default_rng(seed + 92)     # slivers sweeping from the parting to frame right
    for i in range(7):
        a = (600 + 40 * i + r.uniform(-10, 10), 300 - 6 * i + r.uniform(-8, 8))
        b = (760 + 50 * i + r.uniform(-20, 20), 330 + 4 * i + r.uniform(-10, 10))
        c = (880 + 30 * i + r.uniform(-20, 20), 400 + 6 * i + r.uniform(-10, 10))
        out.append(cut(ribbon(catmull([a, b, c], 6), r.uniform(6, 12), 2), [HAIR["lit"], HAIR["sheen"], HAIR["warm"], HAIR["deep"]][i % 4],
                       seed + 93 + i, rough=0.3, edge_light=False))
    return out


def side_locks(wind, sway, seed=1960):
    """r2: locks in front of the ears as curved masses that hug the cheek (inner edge follows the face outline),
    each on a deeper under-layer, snipped tips, two fine slivers. sway = lateral spring offset (px)."""
    out = []
    for side in (-1, 1):
        k = 0.6 if side < 0 else 1.0
        def mv(p):
            x, y = p; t = max(0.0, (y - 560) / 380)
            return (x + t * (sway * k + 60 * wind * k), y - 20 * wind * k * t)
        def mx(x): return 748 + side * (748 - x) * -1 if side > 0 else x
        inner = [(540, 520), (524, 640), (516, 760), (524, 880)]
        outer = [(428, 930), (418, 840), (420, 700), (444, 560)]
        if side > 0:
            inner = [(1496 - x, y) for x, y in inner]; outer = [(1500 - x, y + 8) for x, y in outer]
        else:   # light side: shorter, so the ear lobe shows under it
            inner = [(540, 520), (524, 640), (518, 740), (522, 800)]; outer = [(440, 820), (424, 740), (424, 660), (444, 560)]
        t_ = tips(inner[-1], outer[0], 4, 46, seed + 70 + side, lean=0.15 * side)
        poly = [mv(p) for p in inner + t_ + outer]
        und = [(x - 6 * side, y + 10) for x, y in poly]
        out.append(cut(und, HAIR["shadow"] if side > 0 else HAIR["deep"], seed + 72 + side, rough=1.0))
        out.append(cut(poly, HAIR["mid"] if side < 0 else HAIR["dark"], seed + 74 + side, rough=1.0))
        for j in range(2):
            x0 = (470 + 22 * j) if side < 0 else (1020 + 22 * j)
            pth = [mv((x0, 560 + 10 * j)), mv((x0 - 10 * side, 740)), mv((x0 - 4 * side, 900 - 20 * j))]
            out.append(cut(ribbon(catmull(pth, 6), 9 - 2 * j, 2), [HAIR["lit"], HAIR["warm"]][j] if side < 0 else [HAIR["warm"], HAIR["deep"]][j],
                           seed + 76 + 2 * side + j, rough=0.3, edge_light=False))
    return out


# --------------------------------------------------------------- replacements: eyes
def eye_piece(kind, ex, ey, flip, seed):
    """Replacement eyes. kind: squeeze | half | open_r. Returns list of Pieces."""
    out = []
    if kind == "squeeze":   # lids squeezed into an arch, lower lid pushed up by the cheek
        arc = [(ex - 74 + 148 * u, ey + 6 - 30 * math.sin(math.pi * u) + 8 * flip * (u - 0.5)) for u in np.linspace(0, 1, 22)]
        inner = [(x, y + 15 - 11 * abs(i - 10.5) / 10.5) for i, (x, y) in enumerate(arc)][::-1]
        out.append(cut(arc + inner, LASH, seed, rough=0.25, edge_light=False))
        # lower-lid crease (cheek push) and crow's-foot creases at the outer corner
        low = [(ex - 62 + 124 * u, ey + 34 - 14 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 16)]
        out.append(cut(ribbon(low, 6, 3), SKIN["crease"], seed + 1, rough=0.2, edge_light=False, alpha=0.45))
        ox = ex + flip * 80
        for j, (dx, dy) in enumerate(()):
            out.append(cut(ribbon([(ox, ey + 4 + j * 6), (ox + flip * dx, ey + 4 + j * 6 + dy)], 5, 2), SKIN["crease"], seed + 2 + j,
                           rough=0.1, edge_light=False, alpha=0.85))
    elif kind == "half":
        top = [(ex - 70 + 140 * u, ey - 6 - 14 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 18)]
        bot = [(ex - 70 + 140 * u, ey + 8 + 4 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 18)][::-1]
        out.append(cut(top + bot, EYE_W, seed, rough=0.2, edge_light=False))
        out.append(cut(ellipse_pts(ex + 10, ey + 2, 20, 11), IRIS, seed + 1, rough=0.1, edge_light=False))
        out.append(cut(ribbon(top, 12, 9), LASH, seed + 2, rough=0.2, edge_light=False))
    else:  # open, looking to frame right (at the tram)
        top = [(ex - 72 + 144 * u, ey - 4 - 34 * math.sin(math.pi * u) ** 0.9) for u in np.linspace(0, 1, 20)]
        bot = [(ex - 72 + 144 * u, ey + 12 + 14 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 20)][::-1]
        out.append(cut(top + bot, EYE_W, seed, rough=0.2, edge_light=False))
        out.append(cut(ellipse_pts(ex + 34, ey - 2, 26, 26), IRIS, seed + 1, rough=0.1, edge_light=False))
        out.append(cut(ellipse_pts(ex + 28, ey - 10, 6, 6), (150, 128, 108), seed + 3, rough=0.0, edge_light=False))
        out.append(cut(ribbon(top, 13, 8), LASH, seed + 2, rough=0.2, edge_light=False))
    return out


def brows(lift, seed=1960):
    out = []
    for i, ((ex, ey), flip) in enumerate(zip(EYES, (-1, 1))):
        y = 566 - lift
        pts = [(ex - 76 + 152 * u, y - 18 * math.sin(math.pi * u) + flip * 8 * (u - 0.5)) for u in np.linspace(0, 1, 14)]
        out.append(cut(ribbon(pts, 18, 8) if flip > 0 else ribbon(pts[::-1], 18, 8), (82, 50, 32), seed + 80 + i, rough=0.5))
    return out


# --------------------------------------------------------------- replacements: mouths (1 closed, 2 gulp, 4 grin, 5 open-gap, 6 open-wide)
# r2: smaller, softer mouth. Upper teeth are ONE ivory strip with a notched central gap (two front teeth), scored
# laterals sunk in shadow; lips are thick paper bands and carry the laugh, with dimples at the lifted corners.
MOUTH_SPECS = {1: dict(w=190, h=0), 2: dict(w=110, h=20), 4: dict(w=200, h=30), 5: dict(w=212, h=56), 6: dict(w=206, h=74)}


def mouth_piece(mid, seed=1960):
    cx, cy = MOUTH_C
    sp = MOUTH_SPECS[mid]
    w, h = sp["w"], sp["h"]
    us = np.linspace(0, 1, 40)
    if mid == 1:   # closed smile: seam + lips
        seam = [(cx - w / 2 + w * u, cy - 26 + 26 * math.sin(math.pi * u)) for u in us]
        up = seam + [(x, y - 12 - 6 * math.sin(math.pi * i / 39)) for i, (x, y) in enumerate(seam)][::-1]
        lo = seam + [(x, y + 22 * math.sin(math.pi * i / 39) ** 0.7) for i, (x, y) in enumerate(seam)][::-1]
        return [cut(up, LIP_DK, seed + 101, rough=0.3), cut(lo, LIP, seed + 102, rough=0.3),
                cut(ribbon(seam, 6, 6), (80, 34, 22), seed + 103, rough=0.1, edge_light=False)]
    if mid == 2:   # gulp: small pressed o
        return [cut(ellipse_pts(cx + 6, cy - 4, w / 2, 24), LIP, seed + 110, rough=0.3),
                cut(ellipse_pts(cx + 8, cy - 2, w / 2 - 26, 9), MOUTH_IN, seed + 111, rough=0.1, edge_light=False)]
    out = []
    lift = 30 if mid == 4 else 34

    def yt(u): return cy - lift + (lift - 6) * math.sin(math.pi * u) ** 0.85          # corners lifted
    def yb(u): return yt(u) + h * math.sin(math.pi * u) ** 0.75
    def X(u): return cx - w / 2 + w * u
    top = [(X(u), yt(u)) for u in us]
    bot = [(X(u), yb(u)) for u in us]
    # lips: upper thin and stretched, lower full; a darker lower-lip underside and a soft highlight on top of it
    up_lip = [(x, y - 6 - 9 * math.sin(math.pi * i / 39) ** 0.6) for i, (x, y) in enumerate(top)]
    out.append(cut(top + up_lip[::-1], LIP_DK, seed + 120, rough=0.3))
    lo_lip = [(x, y + 4 + 24 * math.sin(math.pi * i / 39) ** 0.6) for i, (x, y) in enumerate(bot)]
    out.append(cut(bot + lo_lip[::-1], LIP, seed + 121, rough=0.3))
    hi = [(x, y + 6 + 6 * math.sin(math.pi * i / 23)) for i, (x, y) in enumerate(bot[8:32])]
    out.append(cut(bot[8:32] + hi[::-1], LIP_HI, seed + 124, rough=0.2, edge_light=False, alpha=0.6))
    out.append(cut(top + bot[::-1], MOUTH_IN, seed + 122, rough=0.2, edge_light=False))
    if mid == 6:   # tongue, deep in shadow
        tb = bot[12:28]
        tt = [(x, y - (h * 0.35) * math.sin(math.pi * i / 15)) for i, (x, y) in enumerate(tb)]
        out.append(cut(tb + tt[::-1], (118, 48, 40), seed + 123, rough=0.2, edge_light=False))
    # lower teeth: a short dim strip, mostly behind the lower lip (only when open)
    if h >= 40:
        lu = np.linspace(0.34, 0.66, 14)
        lt = [(X(u), yb(u) + 2) for u in lu] + [(X(u), yb(u) - 8 - 3 * math.sin(math.pi * (u - .34) / .32)) for u in lu[::-1]]
        out.append(cut(lt, (150, 112, 90), seed + 150, rough=0.15, tex_gain=1.1, edge_light=False, alpha=0.85))
    # upper teeth: one strip u .22-.78, front teeth longer; central notch = the gap
    tu = np.linspace(0.22, 0.78, 57)
    th = lambda u: (30 if abs(u - .5) < .105 else 24 if abs(u - .5) < .19 else 15) * (0.85 if h < 40 else 1.0)
    strip = [(X(u), yt(u) - 3) for u in tu]
    lower = []
    for u in tu[::-1]:
        d = abs(u - 0.5)
        y = yt(u) + th(u) - 3 * math.cos(math.pi * ((u - .22) / .056 % 1.0) - math.pi / 2) ** 2   # scalloped tips
        if d < 0.02:                                       # the gap: notch to the top
            y = yt(u) + 2
        lower.append((X(u), y))
    out.append(cut(strip + lower, TEETH["front"], seed + 130, rough=0.12, tex_gain=1.1, edge_light=False))
    # laterals in shadow (tissue over the strip ends) and score lines between teeth
    for k, (u0, u1) in enumerate(((0.21, 0.40), (0.60, 0.79))):
        uu = np.linspace(u0, u1, 12)
        poly = [(X(u), yt(u) - 4) for u in uu] + [(X(u), yt(u) + 24) for u in uu[::-1]]
        out.append(cut(poly, (96, 54, 36), seed + 140 + k, rough=0.1, edge_light=False, alpha=0.18 if k == 0 else 0.3))
    for k, u in enumerate((0.31, 0.395, 0.605, 0.69)):
        out.append(cut(ribbon([(X(u), yt(u)), (X(u) + 1, yt(u) + th(u) - 4)], 3, 2), (110, 76, 56), seed + 145 + k,
                       rough=0.05, edge_light=False, alpha=0.7))
    # dimples at the lifted corners
    for k, side in enumerate((0.0, 1.0)):
        x0 = X(side) + (-8 if side == 0 else 8)
        y0 = yt(side) + 4
        f = -1 if side == 0 else 1
        arc = [(x0 + f * 10 * math.sin(math.pi * v * 0.5), y0 - 14 + 30 * v) for v in np.linspace(0, 1, 8)]
        out.append(cut(ribbon(arc, 5, 2), SKIN["crease"], seed + 160 + k, rough=0.1, edge_light=False, alpha=0.35))
    return out


def cheeks(lg, seed=1960):
    """r2: the cheeks do the laugh. Apples swell and rise (to 11 px @720), a lit top on each apple, a crescent
    shadow underneath where the cheek bunches. Built per drawing; lg = laugh strength 0..1."""
    out = []
    for i, (cx, rot) in enumerate(((618, -0.2), (896, 0.2))):
        cy = 792 - 22 * lg
        rx, ry = 92 + 10 * lg, 58 + 8 * lg
        out.append(cut(ellipse_pts(cx, cy, rx, ry, rot=rot), SKIN["tissue"], seed + 14 + i, alpha=0.5 + 0.12 * lg,
                       edge_light=False, rough=0.8))
        if lg > 0:
            out.append(cut(ellipse_pts(cx - 14, cy - 18, rx * 0.55, ry * 0.42, rot=rot), (200, 138, 112), seed + 16 + i,
                           alpha=0.38 * lg, edge_light=False, rough=0.6, soft=3))
            cr = [(cx - rx * 0.8 + 1.6 * rx * v, cy + ry * 0.9 + 10 * math.sin(math.pi * v)) for v in np.linspace(0, 1, 14)]
            out.append(cut(ribbon(cr, 10, 4), SKIN["socket"], seed + 18 + i, alpha=0.45 * lg, edge_light=False, rough=0.3, soft=2))
    return out


def laugh_folds(strength, seed=1960):
    """Nasolabial creases from nose wings to mouth corners (laugh cue)."""
    if strength <= 0:
        return []
    cx, cy = MOUTH_C
    out = []
    for i, flip in enumerate((-1, 1)):
        a = (cx + flip * 54, 800); b = (cx + flip * 120, 846); c = (cx + flip * 140, 900)
        out.append(cut(ribbon(catmull([a, b, c], 6), 9, 4), SKIN["crease"], seed + 170 + i, rough=0.2, edge_light=False,
                       alpha=0.32 * strength))
    return out


# --------------------------------------------------------------- secondary dynamics: fringe strands
class Strand:
    """Chain of NSEG rigid paper segments; each joint a damped angular spring (semi-implicit Euler)."""
    NSEG = 3

    def __init__(self, root, rest_abs, length, width, tone, seed, k=190.0, zeta=0.32, wind_gain=1.0, detach_at=None):
        self.root0 = np.array(root, np.float64)       # in head-local coords
        self.rest = np.array(rest_abs, np.float64)    # rest absolute angles (rad, from +x, y down), head angle 0
        self.L = length / self.NSEG
        self.width, self.tone, self.seed = width, tone, seed
        self.k = k; self.c = 2 * zeta * math.sqrt(k)
        self.wind_gain = wind_gain
        self.phi = self.rest.copy(); self.om = np.zeros(self.NSEG)
        self.detach_at = detach_at; self.free = None    # ballistic state after detachment

    def rel_rest(self):
        r = np.empty(self.NSEG); prev = 0.0
        for j in range(self.NSEG):
            r[j] = self.rest[j] - prev; prev = self.rest[j]
        return r

    def step(self, dt, head_ang, head_om, head_acc_xy, wind_vec, t):
        rr = self.rel_rest()
        if self.free is not None:
            f = self.free
            f["v"] += (np.array([wind_vec[0] * 900, wind_vec[1] * 900 - 120]) - f["v"] * 1.2) * dt
            f["p"] += f["v"] * dt; f["spin"] += f["w"] * dt
            return
        for j in range(self.NSEG):
            parent = head_ang if j == 0 else self.phi[j - 1]
            parent_om = head_om if j == 0 else self.om[j - 1]
            rel = self.phi[j] - parent
            tau = -self.k * (rel - rr[j]) - self.c * (self.om[j] - parent_om)
            d = np.array([math.cos(self.phi[j]), math.sin(self.phi[j])])
            perp = np.array([-d[1], d[0]])
            # wind: drag on the segment, torque proportional to wind component normal to the segment
            tau += self.wind_gain * 75.0 * float(np.dot(wind_vec, perp)) * (1 + 0.35 * j)
            # inertia: head translation acceleration pushes the free end the other way
            tau += -0.0022 * float(np.dot(head_acc_xy, perp)) * (1 + 0.5 * j)
            self.om[j] += tau * dt
        self.phi += self.om * dt

    def detach(self, head_xform):
        pts = self.points(head_xform)
        self.free = dict(p=np.array(pts[0], np.float64), v=np.array([380.0, -160.0]), spin=0.0, w=2.5,
                         shape=[(x - pts[0][0], y - pts[0][1]) for x, y in pts])

    def points(self, head_xform):
        if self.free is not None:
            f = self.free; c, s = math.cos(f["spin"]), math.sin(f["spin"])
            return [(f["p"][0] + x * c - y * s, f["p"][1] + x * s + y * c) for x, y in f["shape"]]
        p = np.array(head_xform(self.root0)); pts = [tuple(p)]
        for j in range(self.NSEG):
            p = p + self.L * np.array([math.cos(self.phi[j]), math.sin(self.phi[j])])
            pts.append(tuple(p))
        return pts

    def energy(self, head_ang):
        rr = self.rel_rest(); e = 0.0; prev = head_ang
        for j in range(self.NSEG):
            e += 0.5 * self.om[j] ** 2 + 0.5 * self.k * (self.phi[j] - prev - rr[j]) ** 2; prev = self.phi[j]
        return e

    def piece(self, head_xform):
        path = catmull(self.points(head_xform), 6)
        return cut(ribbon(path, self.width, 14), self.tone, self.seed, rough=0.7)


def make_fringe(seed=1960):
    """10 spring strands (the skeleton of the fringe mass) + 9 fine flyaway slivers."""
    tones = [HAIR["crown"], HAIR["mid"], HAIR["warm"], HAIR["crown"], HAIR["mid"], HAIR["warm"], HAIR["mid"], HAIR["dark"],
             HAIR["warm"], HAIR["dark"]]
    strands = []
    for i in range(10):
        u = i / 9
        root = (548 + 420 * u, 360 - 70 * math.sin(math.pi * (0.15 + 0.7 * u)))
        a0 = math.radians(80 - 36 * u)           # sweep: upper left -> right, over the right eye
        rest = [a0 - math.radians(16), a0 + math.radians(2), a0 + math.radians(14)]
        length = 290 + 60 * math.sin(math.pi * u) + (110 if i in (5, 6, 7) else 60 if i == 8 else 0)
        width = 104 - 24 * abs(u - 0.45)
        strands.append(Strand(root, rest, length, width, tones[i], seed + 200 + i, k=170 + 30 * (i % 3)))
    slivers = []
    for i in range(9):   # fine flyaways past the silhouette at top right (low stiffness, more wind)
        root = (880 + 26 * i, 300 + 34 * i)
        rest = [math.radians(-14 + 6 * i), math.radians(-2 + 5 * i), math.radians(8 + 4 * i)]
        tone = [HAIR["lit"], HAIR["sheen"], HAIR["crown"], HAIR["warm"], HAIR["mid"], HAIR["lit"], HAIR["crown"], HAIR["sheen"],
                HAIR["warm"]][i]
        slivers.append(Strand(root, rest, 230 + 22 * (i % 4), 6 + 3 * (i % 3), tone, seed + 220 + i, k=110 + 8 * (i % 3),
                              zeta=0.25, wind_gain=1.5, detach_at=(1.05 if i == 3 else 1.35 if i == 7 else None)))
    return strands, slivers


def ribbon_r(path, wr, wm, wt):
    P = np.asarray(path, np.float32); n = len(P); L, R = [], []
    for i in range(n):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, n - 1)]
        d = b - a; d /= (np.linalg.norm(d) + 1e-6); nx, ny = -d[1], d[0]
        u = i / (n - 1)
        w = wr + (wm - wr) * (u / 0.3) if u < 0.3 else wm + (wt - wm) * ((u - 0.3) / 0.7) ** 0.9
        L.append((P[i][0] + nx * w / 2, P[i][1] + ny * w / 2)); R.append((P[i][0] - nx * w / 2, P[i][1] - ny * w / 2))
    return L + R[::-1]


def fringe_pieces(strand_pts, strands, seed=1960):
    """The fringe as one dense layered mass: union under-layers (shadow, deep) wider than the strands so no gaps
    open, then each strand in its tone, then two fine slivers per strand on top. Returns [(piece, shadow kwargs)]."""
    paths = [catmull(p, 6) for p in strand_pts]
    out = []
    under = [ribbon_r(pp_, s.width * 0.5, s.width * 1.75, 30) for pp_, s in zip(paths, strands)]
    out.append((cut(under[0], HAIR["shadow"], seed + 300, rough=0.8, polys=under), dict(sh_off=(12, 15), sh_a=0.42, sh_blur=9)))
    mid = [ribbon_r(pp_, s.width * 0.45, s.width * 1.5, 20) for pp_, s in zip(paths, strands)]
    out.append((cut(mid[0], HAIR["deep"], seed + 301, rough=0.8, polys=mid), dict(sh_off=(4, 5), sh_a=0.25, sh_blur=4)))
    order = [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]
    for i in order:
        s = strands[i]
        out.append((cut(ribbon_r(paths[i], s.width * 0.4, s.width * 1.22, 12), s.tone, s.seed, rough=0.7),
                    dict(sh_off=(3, 4), sh_a=0.22, sh_blur=4)))
    r = np.random.default_rng(seed + 310)
    tones = [HAIR["lit"], HAIR["sheen"], HAIR["crown"], HAIR["deep"], HAIR["warm"]]
    for i, s in enumerate(strands):
        P = np.asarray(paths[i])
        d = np.gradient(P, axis=0); d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        for j, off in enumerate((-0.28,) if i % 2 else (0.22,)):
            q = P + nrm * s.width * (off + r.uniform(-0.06, 0.06))
            q = q[: int(len(q) * r.uniform(0.75, 1.0))]
            out.append((cut(ribbon([tuple(v) for v in q], r.uniform(6, 13), 2), tones[(i + j * 2) % 5], seed + 320 + 2 * i + j,
                            rough=0.3, edge_light=False), dict(sh_off=(2, 3), sh_a=0.2, sh_blur=2)))
    return out

