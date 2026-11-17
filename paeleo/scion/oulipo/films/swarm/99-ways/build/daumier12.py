"""Daumier collage kit for page 12 (Loop). FORAGED: three CC0 lithographs by Honore Daumier (Rijksmuseum via
Wikimedia Commons, 1280 px renders, licence read from the Commons API extmetadata and recorded in
films/sources/99-ways/forage/p12-daumier/meta.json). Only decoded pixels are read (PIL); nothing is executed.

Pieces are cut by hand-placed scissor polygons (coordinates in the source file's pixels), levelled once per
source (red-filter luminance to drop the newsprint foxing, black/white points, no threshold), and glued
with a narrow paper rim and a cast shadow.
"""
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import penlib

FORAGE = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways/forage/p12-daumier")
FILES = {"stair": "d1.jpg", "voyage": "c4.jpg", "tunnel": "c3.jpg"}
LEVELS = {"stair": (62, 214, 1.15), "voyage": (58, 212, 1.15), "tunnel": (60, 212, 1.15)}
TINT = np.array([1.0, 0.975, 0.93], np.float32)     # the cream of the old newsprint, kept faint
RIM = np.array([243, 238, 226], np.float32)          # paper rim left by the scissors

_SRC = {}


def src(name):
    if name not in _SRC:
        a = np.asarray(Image.open(FORAGE / FILES[name]).convert("RGB")).astype(np.float32)
        L = 0.70 * a[..., 0] + 0.30 * a[..., 1]
        lo, hi, g = LEVELS[name]
        _SRC[name] = cv2.GaussianBlur(penlib.levels(L, lo, hi, g), (0, 0), 0.8)   # newsprint speckle softened
    return _SRC[name]


# ------------------------------------------------------------------ scissor polygons (source px)
POLY = {
    # the bourgeois of 'Il est devenu pro-pri-e-taire !' (Les bons bourgeois no. 18, 1846): our station agent
    "agent_head": ("stair", [(790, 497), (902, 492), (906, 582), (934, 590), (928, 614), (914, 642), (902, 664), (872, 678),
                             (840, 684), (806, 680), (782, 664), (772, 642), (762, 616), (768, 600), (780, 590), (784, 584)]),
    "agent_body": ("stair", [(752, 664), (726, 690), (702, 714), (690, 748), (678, 802), (668, 862), (664, 906), (656, 936),
                             (652, 962), (662, 996), (688, 1004), (702, 984), (712, 1060), (712, 1110), (724, 1150), (736, 1152),
                             (730, 1202), (722, 1282), (712, 1350), (700, 1374), (672, 1390), (676, 1410), (736, 1412), (766, 1402),
                             (772, 1370), (778, 1300), (792, 1200), (820, 1132), (850, 1200), (880, 1300), (898, 1380), (914, 1406),
                             (962, 1414), (1006, 1412), (1002, 1394), (956, 1380), (936, 1330), (930, 1250), (936, 1162), (978, 1142),
                             (988, 1060), (978, 990), (988, 922), (992, 860), (986, 790), (962, 740), (932, 714), (902, 690),
                             (880, 670), (858, 670), (832, 686), (800, 684)]),
    # the frightened old woman in her bonnet, 'Un premier voyage en chemin de fer' (1846): the stranger
    "woman": ("voyage", [(300, 640), (330, 620), (380, 610), (430, 620), (458, 650), (466, 700), (460, 760), (444, 800),
                         (420, 830), (430, 880), (450, 930), (470, 962), (262, 962), (262, 900), (268, 800), (275, 720), (285, 670)]),
    # the clasped hands at the chin of the young man in the same carriage: the pondering hands of E5
    "hands": ("voyage", [(598, 862), (620, 846), (650, 850), (676, 858), (700, 870), (706, 892), (694, 912), (664, 918),
                         (636, 912), (612, 902), (598, 886)]),
    # the carriage window: our ticket window
    "window": ("voyage", [(655, 432), (986, 432), (986, 800), (772, 800), (748, 736), (702, 702), (655, 692)]),
    # the CONCIERGE door's upper half: our SERVICE door
    "door": ("stair", [(492, 312), (738, 312), (738, 636), (588, 636), (575, 622), (528, 622), (515, 636), (492, 636)]),
}
TONE = {   # rectangles of crayon tone that the set pieces are cut out of
    "wall": ("stair", (285, 420, 472, 760)),
    "floor": ("stair", (380, 1418, 660, 1482)),
    "dark": ("tunnel", (232, 285, 400, 500)),
    "mid": ("voyage", (112, 430, 258, 700)),
    "pale": ("voyage", (700, 470, 930, 640)),
}
ANCHOR = {"agent_head": (822, 676), "agent_body": (812, 676)}


def poly_piece(name):
    s, P = POLY[name]
    g = src(s)
    P = np.array(P, np.float32)
    x0, y0 = np.floor(P.min(0)).astype(int) - 2
    x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    a = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(a, [np.int32(np.round((P - [x0, y0]) * 4))], 255, cv2.LINE_AA, shift=2)
    return dict(gray=g[y0:y1, x0:x1].copy(), alpha=a, origin=(x0, y0))


def tone(name, w, h):
    """A crayon-tone patch (gray), stretched to w x h."""
    s, (x0, y0, x1, y1) = TONE[name]
    t = cv2.resize(src(s)[y0:y1, x0:x1], (int(w), int(h)), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(t, (0, 0), 1.2)     # the crayon grain kept, its pixel noise softened


def shape_piece(tone_name, poly, w=None, h=None):
    """A set piece: a scissor polygon (panel coords, relative to its own box) cut out of a crayon-tone patch."""
    P = np.array(poly, np.float32)
    x0, y0 = P.min(0)
    x1, y1 = P.max(0)
    W, H = int(math.ceil(x1 - x0)) + 2, int(math.ceil(y1 - y0)) + 2
    g = tone(tone_name, W, H)
    a = np.zeros((H, W), np.uint8)
    cv2.fillPoly(a, [np.int32(np.round((P - [x0, y0]) * 4))], 255, cv2.LINE_AA, shift=2)
    return dict(gray=g, alpha=a, origin=(0, 0)), (float(x0), float(y0))


def M_for(piece, at, scale=1.0, deg=0.0, flip=False, anchor=None):
    """3x3 piece-crop -> canvas. `anchor` in source px (default: the crop centre) lands on `at`."""
    ox, oy = piece["origin"]
    if anchor is None:
        ax, ay = piece["gray"].shape[1] / 2, piece["gray"].shape[0] / 2
    else:
        ax, ay = anchor[0] - ox, anchor[1] - oy
    F = penlib.S(-1, 1) if flip else np.eye(3)
    return penlib.T(at[0], at[1]) @ penlib.R(deg) @ penlib.S(scale) @ F @ penlib.T(-ax, -ay)


def glue(canvas, piece, M, rim=4, shadow=True, lift=0.0, tint=TINT, shade=1.0):
    """Lay a cut piece on the canvas: paper rim (scissor facets), cast shadow, then the printed tone."""
    h, w = canvas.shape[:2]
    g = cv2.warpPerspective(piece["gray"].astype(np.float32), M, (w, h), flags=cv2.INTER_CUBIC, borderValue=0)
    a = cv2.warpPerspective(piece["alpha"], M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    ab = (a > 127).astype(np.uint8) * 255
    if rim:
        pm = penlib.scissor(ab, rim)
        if shadow:
            penlib.shadow_onto(canvas, pm, off=5, blur=4, opacity=0.33, lift=lift)
        pa = pm.astype(np.float32)[..., None] / 255
        canvas[:] = canvas * (1 - pa) + RIM * pa
    elif shadow:
        penlib.shadow_onto(canvas, ab, off=5, blur=4, opacity=0.33, lift=lift)
    af = a.astype(np.float32)[..., None] / 255
    col = np.clip(g * shade, 0, 255)[..., None] * tint
    canvas[:] = canvas * (1 - af) + col * af
    return ab


def overlay_check(out):
    """Debug: draw every scissor polygon on its source (for checking the cuts by eye)."""
    from PIL import ImageDraw
    ims = {}
    for k, (s, P) in POLY.items():
        if s not in ims:
            ims[s] = Image.open(FORAGE / FILES[s]).convert("RGB")
        ImageDraw.Draw(ims[s]).line(P + [P[0]], fill=(255, 0, 0), width=3)
    for k, (s, b) in TONE.items():
        if s not in ims:
            ims[s] = Image.open(FORAGE / FILES[s]).convert("RGB")
        ImageDraw.Draw(ims[s]).rectangle(b, outline=(0, 120, 255), width=3)
    for s, im in ims.items():
        im.thumbnail((1100, 1100))
        im.save(f"{out}_{s}.jpg")
