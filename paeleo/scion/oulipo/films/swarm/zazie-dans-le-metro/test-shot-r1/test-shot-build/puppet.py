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
HAIR = dict(shadow=(44, 21, 4), dark=(65, 35, 18), mid=(86, 58, 40), crown=(104, 77, 60), lit=(118, 91, 72))
SKIN = dict(forehead=(182, 120, 94), cheek=(180, 112, 89), neck=(165, 102, 75), tissue=(196, 104, 84),
            socket=(150, 90, 68), crease=(128, 72, 54))
LIP = (183, 103, 86)
LIP_HI = (196, 118, 98)
TEETH = dict(front=(214, 196, 166), side=(184, 150, 120), back=(162, 117, 92))
MOUTH_IN = (34, 13, 4)
TONGUE = (150, 62, 52)
EYE_W = (176, 150, 126)
IRIS = (52, 30, 18)
LASH = (40, 20, 10)
COLLAR = (214, 96, 30)
COLLAR_F = (168, 66, 20)
JUMPER = (78, 58, 46)

_PAPER = None


def load_paper(path):
    global _PAPER
    k = np.asarray(Image.open(path).convert("L")).astype(np.float32)
    k = np.tile(k, (3, 3))                      # tileable scan -> 3072 sq
    k = (k - k.mean()) / 255.0
    _PAPER = k


def paper_tex(w, h, seed, scale=1.0, gain=1.7):
    """Crop of the real kraft scan, rotated per piece so the laid lines differ piece to piece."""
    r = np.random.default_rng(seed)
    src = _PAPER
    ang = float(r.uniform(-90, 90))
    M = cv2.getRotationMatrix2D((1536, 1536), ang, scale)
    big = cv2.warpAffine(src, M, (3072, 3072), borderMode=cv2.BORDER_REFLECT)
    x0 = int(r.integers(200, 3072 - w - 200)) if w < 2600 else 0
    y0 = int(r.integers(200, 3072 - h - 200)) if h < 2600 else 0
    return 1.0 + gain * big[y0:y0 + h, x0:x0 + w]


class Piece:
    """An RGBA sprite of one cut piece (placed at ox, oy in rig coords)."""
    __slots__ = ("img", "ox", "oy", "name")

    def __init__(self, img, ox, oy, name=""):
        self.img, self.ox, self.oy, self.name = img, ox, oy, name


def cut(poly, colour, seed, name="", rough=1.0, tex_gain=1.7, alpha=1.0, edge_light=True, soft=0.0):
    """Scissor-cut a polygon out of dyed paper. Returns a Piece."""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    pad = 6
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    x1, y1 = int(math.ceil(max(xs))) + pad, int(math.ceil(max(ys))) + pad
    w, h = max(2, x1 - x0), max(2, y1 - y0)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
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
        col = np.clip(col + rim * 34, 0, 255)
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
    P["ear_l"] = cut(ellipse_pts(500, 800, 44, 72, rot=0.15), SKIN["cheek"], seed + 6)
    P["ear_l_in"] = cut(ellipse_pts(490, 806, 22, 46, rot=0.15), SKIN["socket"], seed + 7, rough=0.4, edge_light=False)
    P["ear_r"] = cut(ellipse_pts(1000, 800, 42, 70, rot=-0.15), SKIN["neck"], seed + 8)
    P["ear_r_in"] = cut(ellipse_pts(1010, 806, 20, 44, rot=-0.15), SKIN["crease"], seed + 9, rough=0.4, edge_light=False)
    P["face"] = cut(face_outline(), SKIN["forehead"], seed + 10, rough=0.6)
    # jaw / chin-shadow tissue (darker, right side away from light) and eye-socket tissue
    P["jaw_tissue"] = cut([(960, 760), (1004, 820), (990, 920), (930, 1010), (840, 1060), (760, 1066), (830, 1010), (920, 930), (950, 840)],
                          SKIN["neck"], seed + 11, alpha=0.65, edge_light=False)
    P["socket_l"] = cut(ellipse_pts(640, 650, 92, 46), SKIN["socket"], seed + 12, alpha=0.38, edge_light=False, soft=6)
    P["socket_r"] = cut(ellipse_pts(866, 650, 92, 46), SKIN["socket"], seed + 13, alpha=0.48, edge_light=False, soft=6)
    # tissue cheeks (separate, they rise with the laugh)
    P["cheek_l"] = cut(ellipse_pts(612, 790, 92, 60, rot=-0.2), SKIN["tissue"], seed + 14, alpha=0.55, edge_light=False, rough=0.8)
    P["cheek_r"] = cut(ellipse_pts(902, 790, 92, 60, rot=0.2), SKIN["tissue"], seed + 15, alpha=0.55, edge_light=False, rough=0.8)
    # nose: folded tab, lit face and shadow side, nostril wings
    P["nose"] = cut([(736, 640), (760, 650), (782, 750), (806, 786), (776, 806), (740, 808), (708, 792), (724, 750)],
                    (190, 128, 100), seed + 16)
    P["nose_sh"] = cut([(760, 650), (782, 750), (806, 786), (776, 806), (770, 760)], SKIN["socket"], seed + 17, edge_light=False)
    P["nostril_l"] = cut(ellipse_pts(728, 798, 14, 7, rot=0.3), (88, 40, 28), seed + 18, rough=0.2, edge_light=False)
    P["nostril_r"] = cut(ellipse_pts(784, 798, 14, 7, rot=-0.3), (88, 40, 28), seed + 19, rough=0.2, edge_light=False)
    return P


def back_hair(wind, seed=1960):
    """Bob behind the face: 3 tones. `wind` (0..1) shears the lower bob to frame right."""
    def sh(pts, k):
        return [(x + k * wind * max(0.0, (y - 300) / 700) ** 1.3, y - 0.25 * k * wind * max(0.0, (y - 600) / 500)) for x, y in pts]
    base = [(470, 470), (520, 330), (640, 262), (760, 246), (880, 262), (990, 320), (1060, 430), (1090, 560), (1100, 700),
            (1112, 830), (1120, 930), (1090, 950), (1060, 905), (1040, 960), (1006, 940), (990, 860), (980, 720),
            (520, 720), (512, 860), (496, 950), (462, 925), (430, 975), (396, 940), (380, 840), (384, 700), (400, 580)]
    P = [cut(sh([(x + (8 if x > 748 else -8), y + 14) for x, y in base], 80), HAIR["shadow"], seed + 40, rough=1.4),
         cut(sh(base, 70), HAIR["mid"], seed + 41, rough=1.3)]
    crown = [(520, 360), (640, 270), (760, 254), (880, 270), (980, 330), (1030, 420), (900, 380), (760, 360), (620, 380), (530, 440)]
    P.append(cut(sh(crown, 40), HAIR["crown"], seed + 42, rough=1.0))
    # lit strands on the light (left) side of the bob
    for i, (a, b) in enumerate((((470, 520), (420, 900)), ((520, 420), (452, 860)), ((1060, 470), (1096, 880)))):
        path = catmull([a, ((a[0] + b[0]) / 2 - 18, (a[1] + b[1]) / 2), b], 6)
        P.append(cut(sh(ribbon(path, 46, 8), 70), HAIR["lit"] if i < 2 else HAIR["dark"], seed + 43 + i, rough=0.8))
    return P


def side_locks(wind, sway, seed=1960):
    """Locks in front of the ears (they cover the ears' tops). sway = lateral spring offset (px)."""
    out = []
    specs = [((520, 520), (470, 760), (452, 960), HAIR["dark"], 70), ((548, 560), (520, 760), (512, 900), HAIR["mid"], 44),
             ((970, 520), (1030, 760), (1066, 950), HAIR["dark"], 72), ((946, 560), (990, 760), (1012, 900), HAIR["crown"], 40)]
    for i, (a, m, b, col, w) in enumerate(specs):
        k = 1.0 if i >= 2 else 0.6
        b2 = (b[0] + sway * k + 60 * wind * k, b[1] - 20 * wind * k)
        m2 = (m[0] + 0.5 * (sway * k + 60 * wind * k), m[1])
        out.append(cut(ribbon(catmull([a, m2, b2], 8), w, 14), col, seed + 60 + i, rough=1.0))
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
        out.append(cut(ribbon(low, 7, 4), SKIN["crease"], seed + 1, rough=0.2, edge_light=False, alpha=0.8))
        ox = ex + flip * 80
        for j, (dx, dy) in enumerate(((26, -16), (32, 2), (24, 20))):
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
MOUTH_SPECS = {1: dict(w=206, h=0), 2: dict(w=120, h=22), 4: dict(w=246, h=46), 5: dict(w=252, h=106), 6: dict(w=236, h=150)}


def mouth_piece(mid, seed=1960):
    cx, cy = MOUTH_C
    sp = MOUTH_SPECS[mid]
    w, h = sp["w"], sp["h"]
    us = np.linspace(0, 1, 40)
    out = []
    if mid == 1:   # closed smile: seam + lips
        seam = [(cx - w / 2 + w * u, cy - 26 + 30 * math.sin(math.pi * u)) for u in us]
        out.append(cut(ribbon(seam[:20], 6, 10) + [], LIP, seed + 100, rough=0.3))
        up = seam + [(x, y - 12 - 6 * math.sin(math.pi * i / 39)) for i, (x, y) in enumerate(seam)][::-1]
        lo = seam + [(x, y + 24 * math.sin(math.pi * i / 39) ** 0.7) for i, (x, y) in enumerate(seam)][::-1]
        out = [cut(up, LIP, seed + 101, rough=0.3), cut(lo, LIP_HI, seed + 102, rough=0.3),
               cut(ribbon(seam, 7, 7), (70, 28, 18), seed + 103, rough=0.1, edge_light=False)]
        return out
    if mid == 2:   # gulp: small pressed o
        ring = ellipse_pts(cx + 6, cy - 4, w / 2, 24)
        out.append(cut(ring, LIP, seed + 110, rough=0.3))
        out.append(cut(ellipse_pts(cx + 8, cy - 2, w / 2 - 26, 9), MOUTH_IN, seed + 111, rough=0.1, edge_light=False))
        return out
    top = [(cx - w / 2 + w * u, cy - 30 + 22 * math.sin(math.pi * u)) for u in us]
    bot = [(cx - w / 2 + w * u, cy - 30 + (22 + h) * math.sin(math.pi * u) ** 0.8) for u in us]
    # lips (behind interior edge so they frame it)
    up_lip = [(x, y - 16 - 8 * math.exp(-((i / 39 - 0.5) / 0.08) ** 2) * 0 - 6 * math.sin(math.pi * i / 39)) for i, (x, y) in enumerate(top)]
    out.append(cut(top + up_lip[::-1], LIP, seed + 120, rough=0.3))
    lo_lip = [(x, y + 6 + 26 * math.sin(math.pi * i / 39) ** 0.7) for i, (x, y) in enumerate(bot)]
    out.append(cut(bot + lo_lip[::-1], LIP_HI, seed + 121, rough=0.3))
    out.append(cut(top + bot[::-1], MOUTH_IN, seed + 122, rough=0.2, edge_light=False))
    if mid in (5, 6):   # tongue in the shadow of the mouth
        tb = [(x, y) for x, y in bot[8:32]]
        tt = [(x, y - (h * 0.32) * math.sin(math.pi * i / 23)) for i, (x, y) in enumerate(tb)]
        out.append(cut(tb + tt[::-1], TONGUE, seed + 123, rough=0.2, edge_light=False))
    # upper teeth, hanging from the top edge, with Zazie's gap between the two front teeth
    n = 8
    edges = np.linspace(0.12, 0.88, n + 1)
    for i in range(n):
        u0, u1 = edges[i] + 0.006, edges[i + 1] - 0.006
        if i == 3: u1 -= 0.014          # the gap
        if i == 4: u0 += 0.014
        dist = abs((u0 + u1) / 2 - 0.5)
        th = (44 if dist < 0.1 else 36 if dist < 0.25 else 26) * (1.0 if h > 40 else 0.85)
        col = TEETH["front"] if dist < 0.1 else TEETH["side"] if dist < 0.25 else TEETH["back"]
        def yt(u): return cy - 30 + 22 * math.sin(math.pi * u)
        poly = [(cx - w / 2 + w * u0, yt(u0) - 2), (cx - w / 2 + w * u1, yt(u1) - 2),
                (cx - w / 2 + w * u1 - 2, yt(u1) + th * 0.92), (cx - w / 2 + w * (u0 + u1) / 2, yt((u0 + u1) / 2) + th),
                (cx - w / 2 + w * u0 + 2, yt(u0) + th * 0.92)]
        out.append(cut(poly, col, seed + 130 + i, rough=0.15, tex_gain=1.2))
    # lower teeth rising from the bottom edge (only partly seen)
    m = 6
    edges = np.linspace(0.24, 0.76, m + 1)
    for i in range(m):
        u0, u1 = edges[i] + 0.008, edges[i + 1] - 0.008
        def yb(u): return cy - 30 + (22 + h) * math.sin(math.pi * u) ** 0.8
        th = 24 if h < 60 else 20
        dist = abs((u0 + u1) / 2 - 0.5)
        col = TEETH["side"] if dist < 0.15 else TEETH["back"]
        poly = [(cx - w / 2 + w * u0, yb(u0) + 2), (cx - w / 2 + w * u1, yb(u1) + 2), (cx - w / 2 + w * u1 - 2, yb(u1) - th),
                (cx - w / 2 + w * u0 + 2, yb(u0) - th)]
        out.append(cut(poly, col, seed + 150 + i, rough=0.15, tex_gain=1.2))
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
                       alpha=0.75 * strength))
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
    tones = [HAIR["mid"], HAIR["dark"], HAIR["crown"], HAIR["dark"], HAIR["lit"], HAIR["dark"], HAIR["mid"], HAIR["shadow"],
             HAIR["dark"], HAIR["crown"]]
    strands = []
    for i in range(10):
        u = i / 9
        root = (548 + 420 * u, 360 - 70 * math.sin(math.pi * (0.15 + 0.7 * u)))
        a0 = math.radians(80 - 36 * u)           # sweep: upper left -> right, over the right eye
        rest = [a0 - math.radians(16), a0 + math.radians(2), a0 + math.radians(14)]
        length = 290 + 60 * math.sin(math.pi * u) + (110 if i in (5, 6, 7) else 60 if i == 8 else 0)
        width = 112 - 26 * abs(u - 0.45)
        strands.append(Strand(root, rest, length, width, tones[i], seed + 200 + i, k=170 + 30 * (i % 3)))
    slivers = []
    for i in range(4):   # thin slivers flying past the silhouette at top right
        root = (960 + 30 * i, 340 + 60 * i)
        rest = [math.radians(-6 + 8 * i), math.radians(4 + 6 * i), math.radians(14 + 4 * i)]
        slivers.append(Strand(root, rest, 260 + 30 * i, 20 - 2 * i, [HAIR["lit"], HAIR["crown"], HAIR["mid"], HAIR["dark"]][i],
                              seed + 220 + i, k=120, zeta=0.25, wind_gain=1.5, detach_at=(1.05 if i == 1 else 1.35 if i == 3 else None)))
    return strands, slivers
