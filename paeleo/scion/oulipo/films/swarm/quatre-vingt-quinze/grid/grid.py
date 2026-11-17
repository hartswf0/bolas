"""quatre-vingt-quinze -- U1 story-grid-letterer: page scaffold, hand lettering, marks, registry.

Plan revision r0 (films/swarm/quatre-vingt-quinze/plan.md sections 5, 6, 10).

Everything here is a deterministic function of its explicit arguments. No function
takes a route: cells, grounds and lettering are functions of the cell id only; marks
take a drawing state (u), never a route name; the editor maps the route to u.

What is HANDMADE here (drawn in code, stroke by stroke):
  * a broad-nib single-stroke capital alphabet (thick-thin pen: the stroke width is
    the projection of a slanted nib on the direction of travel), with per-glyph hand
    irregularity seeded by text and position, so the same text always draws the same;
  * a bold lowercase title hand; every second glyph turned 180 degrees about the
    x-band centre, with the 4 in-between turn drawings for the film;
  * balloons (hand-drawn ovals, curved pointed tails), corner caption boxes, red SFX;
  * hand-ruled panel borders (bowed, pressure-varied, chamfered at every corner that
    meets a crossing mark, as on Lecroart's page);
  * the salmon pools, PAINTED: concentric layers of broad brush strokes laid with a
    soft hair edge, denser toward the panel edge, pigment settling into the fibres of
    the real paper (lighter at the action, darker at the edges);
  * the red barbed crossing marks (an arrow per axis, fletched tails, two fletched
    diagonals, a darker ink edge), parametric in u: across-long (u=0), neutral (0.5),
    down-long (1), and the per-mark turn drawings;
  * margin rails, id tabs, bottom line, the red cut-paper gutter arrow (scissor facets,
    a small cast shadow because it is a paper piece lying on the page).

What is FORAGED: the paper itself -- a real scan of a blank sheet, Library of Congress
musftpsets.200218222 page 0001 (Federal Theatre Project, 1934, US government work).
Only its fibre relief (scan / its own 40 px blur) is used, as the paper's texture and
as the surface the salmon pigment settles into. No grain is synthesised; no filter.

Typical editor use:
    import grid as G
    page = G.compose_page({c: cell_rgb_900x600 for c in G.CELLS})       # neutral page
    ground = G.ground("E")              # 900x600 RGB painted pool on real paper
    lett = G.lettering("E")             # 900x600 RGBA balloon layer (page pose)
    ov = G.cell_overlay("E")            # 900x600 RGBA border/chamfer/tab for one cell
    marks = G.marks_layer([0.0]*8)      # page-size RGBA marks, across-long
    arrow = G.arrow_layer("B", "E", 1)  # page-size RGBA arrow in the B/E gutter
"""
import json
import math
import random
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OULIPO = HERE.parents[3]
FILMS = OULIPO / "films"
SRC = FILMS / "sources" / "quatre-vingt-quinze" / "grid"
PAPER_SCAN = SRC / "loc_blank_0001.jpg"
PAPER_CROP = (260, 300, 2940, 2214)   # inside the sheet's edges and tapes (scan px)

# ------------------------------------------------------------------ geometry
PW, PH = 3360, 2400
CW, CH = 900, 600
COLX = [240, 1230, 2220]
ROWY = [260, 950, 1640]
GUT = 90
CELLS = "ABCDEFGHI"
ROUTES = {"across": list("ABCDEFGHI"), "down": list("ADGBEHCFI")}  # data only; no drawing uses it
SALMON = set("DEGI")
SS = 2  # supersampling

# mark centres: 4 interior gutter crossings, then the 4 row-gutter ends at the margins
MARKS = [(1185, 905), (2175, 905), (1185, 1595), (2175, 1595),
         (195, 905), (3165, 905), (195, 1595), (3165, 1595)]
# order in which the film's turn draws them: left to right, top to bottom
MARK_TURN_ORDER = [4, 0, 1, 5, 6, 2, 3, 7]

# ------------------------------------------------------------------ palette (plan 10)
PAPER = (254, 252, 248)     # between #fffefe and #fefdf9
INK = (43, 32, 33)          # #2b2021
SIL = (22, 16, 15)          # #16100f
SAL_PALE = (255, 215, 212)  # #ffd7d4
SAL_MID = (237, 146, 131)   # #ed9283
SAL_DEEP = (194, 88, 80)    # #c25850
MAUVE = (126, 75, 69)       # #7e4b45
MAUVE_L = (172, 134, 130)   # #ac8682
RED = (177, 78, 63)         # #b14e3f
RED_EDGE = (126, 52, 44)
WHITE = (255, 255, 255)

# where each salmon panel's light sits (cell px): (cx, cy, rx, ry) -- the action
POOL = {"D": (430, 250, 560, 430), "E": (470, 190, 560, 440),
        "G": (520, 210, 540, 430), "I": (380, 300, 560, 430)}


def cell_origin(c):
    k = CELLS.index(c)
    return COLX[k % 3], ROWY[k // 3]


def cell_rc(c):
    k = CELLS.index(c)
    return k // 3, k % 3


def _rng(*key):
    return random.Random(zlib.crc32(repr(key).encode()))


# ================================================================== paper
@lru_cache(maxsize=1)
def paper_relief():
    """Fibre relief of the real scanned sheet at page size: scan / blur(scan), mean 1."""
    im = Image.open(PAPER_SCAN).convert("L").crop(PAPER_CROP).resize((PW, PH), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    low = np.asarray(im.filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    return a / np.maximum(low, 1.0)


@lru_cache(maxsize=1)
def paper_sheet():
    """The page's paper: palette white carrying the real sheet's fibre (RGB, page size)."""
    r = paper_relief() ** 1.4
    col = np.array(PAPER, np.float32)[None, None, :] * r[..., None]
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB")


def _paper_crop(x0, y0, w, h):
    return paper_sheet().crop((x0, y0, x0 + w, y0 + h))


# ================================================================== painted pools
def _brush_density(c):
    """Pigment density in [0,1] for salmon cell c, laid as broad brush strokes.

    The painter's intention is a radial pool T(r): pale at the action, deep at the panel
    edge. It is laid as a first even coat plus many broad, slightly diagonal brush strokes;
    each stroke carries pigment in proportion to T where it passes, with a soft hair edge
    and pressure that swells and lifts along its length. Where strokes overlap the wash is
    deeper, where they miss it is lighter: the pool is visibly painted, not computed.
    """
    cx, cy, rx, ry = POOL[c]
    rng = _rng("pool", c)
    W, H = CW // 2, CH // 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx * 2 - cx) / rx) ** 2 + ((yy * 2 - cy) / ry) ** 2)
    T = np.clip((r - 0.12) / 1.0, 0, 1) ** 1.35
    cover = np.zeros((H, W), np.float32)
    n = 150
    for i in range(n):
        layer = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(layer)
        # strokes favour the outer ring (the painter works the edges harder)
        while True:
            x = rng.uniform(-40, W + 40)
            y = rng.uniform(-30, H + 30)
            rr = math.hypot((x * 2 - cx) / rx, (y * 2 - cy) / ry)
            if rng.random() < 0.25 + 0.75 * min(1, rr):
                break
        ang = math.radians(rng.uniform(-28, 8))
        L = rng.uniform(90, 220)
        width = rng.uniform(22, 42)
        m = 16
        bend = rng.uniform(-0.25, 0.25)
        pts = []
        for j in range(m + 1):
            f = j / m - 0.5
            px = x + math.cos(ang) * L * f - math.sin(ang) * bend * L * (f * f - 0.25)
            py = y + math.sin(ang) * L * f + math.cos(ang) * bend * L * (f * f - 0.25)
            pts.append((px, py))
        for j in range(m):
            f = j / m
            p = math.sin(math.pi * min(1.0, f * 1.1)) ** 0.6
            d.line([pts[j], pts[j + 1]], fill=int(255 * (0.55 + 0.45 * p)),
                   width=max(2, int(width * (0.75 + 0.25 * p))))
        cover += np.asarray(layer.filter(ImageFilter.GaussianBlur(4.0))).astype(np.float32) / 255.0
    rel = cover / max(1e-3, float(cover.mean()))
    dens = 0.10 + 0.92 * T * np.clip(rel, 0.35, 1.9) ** 0.45
    dens = np.clip(dens, 0, 1)
    img = Image.fromarray((dens * 255).astype(np.uint8)).resize((CW, CH), Image.BICUBIC)
    return np.asarray(img).astype(np.float32) / 255.0


def _ramp(d):
    a = np.array(SAL_PALE, np.float32)
    b = np.array(SAL_MID, np.float32)
    c = np.array(SAL_DEEP, np.float32)
    d = d[..., None]
    t1 = np.clip(d / 0.55, 0, 1)
    t2 = np.clip((d - 0.55) / 0.45, 0, 1)
    return np.where(d < 0.55, a + (b - a) * t1, b + (c - b) * t2)


@lru_cache(maxsize=16)
def ground(c):
    """Canonical ground of cell c (900x600 RGB): real paper; salmon cells painted."""
    x0, y0 = cell_origin(c)
    if c not in SALMON:
        return _paper_crop(x0, y0, CW, CH)
    dens = _brush_density(c)
    col = _ramp(dens)
    rel = paper_relief()[y0:y0 + CH, x0:x0 + CW]
    # pigment settles in the fibre valleys: deeper colour takes the relief harder
    k = 2.2 + 2.5 * dens
    col = col * (rel ** k)[..., None]
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB")


def ground_at(c, x, y):
    """Ground colour at cell px (x, y): for keying silhouettes' window glass etc."""
    return ground(c).getpixel((int(min(CW - 1, max(0, x))), int(min(CH - 1, max(0, y)))))


# ================================================================== the pen
NIB_ANGLE = math.radians(-38)   # broad nib held at about 38 degrees


def pen_stroke(d, pts, width, color, nib=0.82, hair=0.30, taper=(0.55, 0.35), blob=True):
    """Broad-nib stroke on ImageDraw d (coordinates already scaled).

    The nib is a flat edge of length width*(nib+hair) held at NIB_ANGLE, with a
    thickness of width*hair; it is stamped densely along the path, so strokes that run
    along the nib are hairlines and strokes across it are full (thick-thin). Pressure
    ramps in and out over the first/last `taper` fractions; `blob` adds the small
    landing swell of a loaded pen.
    """
    c = tuple(color[:3]) + (255,)
    th = max(1.0, width * hair)
    P = _resample(pts, max(0.5, min(th * 0.15, 2.0)))
    n = len(P)
    ca, sa = math.cos(NIB_ANGLE), math.sin(NIB_ANGLE)
    for i, (x, y) in enumerate(P):
        f = i / max(1, n - 1)
        pa = 1.0
        if blob and f < taper[0] * 0.25:
            pa = 1.0 + 0.25 * (1 - f / (taper[0] * 0.25))
        elif blob and f > 1 - taper[1] * 0.25:
            pa = 0.7 + 0.3 * (1 - f) / (taper[1] * 0.25)
        L = width * (nib + hair) * pa / 2
        t = th * (0.9 + 0.1 * pa) / 2
        d.polygon([(x - ca * L - sa * t, y - sa * L + ca * t), (x + ca * L - sa * t, y + sa * L + ca * t),
                   (x + ca * L + sa * t, y + sa * L - ca * t), (x - ca * L + sa * t, y - sa * L - ca * t)], fill=c)
        if n == 1:
            r = width * 0.5
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)


def _resample(pts, step):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        for j in range(1, k + 1):
            out.append((x0 + (x1 - x0) * j / k, y0 + (y1 - y0) * j / k))
    return out


def ruled(d, a, b, width, color, rng, bow=1.6):
    """A hand-ruled line: slight bow, pressure drift, a hair of overshoot."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / max(L, 1), (x1 - x0) / max(L, 1)
    ov0, ov1 = rng.uniform(-2, 5), rng.uniform(-2, 5)
    ux, uy = (x1 - x0) / max(L, 1), (y1 - y0) / max(L, 1)
    x0, y0 = x0 - ux * ov0, y0 - uy * ov0
    x1, y1 = x1 + ux * ov1, y1 + uy * ov1
    bw = rng.uniform(-bow, bow)
    ph = rng.uniform(0, 6.28)
    m = max(4, int(L / 6))
    c = tuple(color) + (255,)
    prev = None
    for j in range(m + 1):
        f = j / m
        off = bw * math.sin(math.pi * f) + 0.5 * math.sin(f * 11 + ph)
        x = x0 + (x1 - x0) * f + nx * off
        y = y0 + (y1 - y0) * f + ny * off
        w = width * (0.9 + 0.14 * math.sin(f * 5.3 + ph) + (0.12 if f < 0.03 else 0))
        if prev:
            px, py, pw = prev
            hx, hy = nx * (pw + w) / 4, ny * (pw + w) / 4
            d.polygon([(px - hx, py - hy), (x - hx, y - hy), (x + hx, y + hy), (px + hx, py + hy)], fill=c)
        r = w / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        prev = (x, y, w)


# ================================================================== alphabet
def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def _dot(x, y):
    return [(x, y)]


# Capitals: unit box, cap height 1, y down, baseline y = 1. (advance, [strokes]).
# Drawn condensed and a little top-heavy, the way a letterer's capitals are.
CAPS = {
    "A": (0.58, [[(0.0, 1.0), (0.27, 0.0), (0.30, 0.0), (0.58, 1.0)], [(0.12, 0.62), (0.47, 0.60)]]),
    "B": (0.52, [[(0.02, 1.0), (0.02, 0.0)], [(0.02, 0.0), (0.30, 0.0), (0.45, 0.07), (0.47, 0.22), (0.38, 0.40), (0.04, 0.46)],
                 [(0.04, 0.46), (0.36, 0.48), (0.52, 0.62), (0.50, 0.86), (0.34, 1.0), (0.02, 1.0)]]),
    "C": (0.56, [_arc(0.32, 0.5, 0.31, 0.5, -45, -312, 18)]),
    "D": (0.56, [[(0.02, 1.0), (0.02, 0.0)], [(0.02, 0.0), (0.22, 0.0)] + _arc(0.20, 0.5, 0.35, 0.5, -90, 90, 14)[1:] + [(0.02, 1.0)]]),
    "E": (0.48, [[(0.48, 0.0), (0.02, 0.0), (0.02, 1.0), (0.50, 1.0)], [(0.02, 0.48), (0.38, 0.47)]]),
    "F": (0.46, [[(0.48, 0.0), (0.02, 0.0), (0.02, 1.0)], [(0.02, 0.47), (0.36, 0.46)]]),
    "G": (0.6, [_arc(0.32, 0.5, 0.31, 0.5, -40, -350, 18), [(0.62, 0.56), (0.38, 0.57)], [(0.62, 0.56), (0.61, 0.95)]]),
    "H": (0.54, [[(0.02, 0.0), (0.02, 1.0)], [(0.54, 0.0), (0.53, 1.0)], [(0.02, 0.50), (0.54, 0.48)]]),
    "I": (0.12, [[(0.06, 0.0), (0.06, 1.0)]]),
    "J": (0.42, [[(0.40, 0.0), (0.40, 0.72)] + _arc(0.21, 0.72, 0.19, 0.28, 0, 160, 8)[1:]]),
    "K": (0.54, [[(0.02, 0.0), (0.02, 1.0)], [(0.52, 0.0), (0.04, 0.56)], [(0.18, 0.42), (0.56, 1.0)]]),
    "L": (0.44, [[(0.02, 0.0), (0.02, 1.0), (0.46, 0.99)]]),
    "M": (0.70, [[(0.0, 1.0), (0.05, 0.0), (0.35, 0.66), (0.65, 0.0), (0.70, 1.0)]]),
    "N": (0.56, [[(0.02, 1.0), (0.02, 0.0), (0.54, 1.0), (0.54, 0.0)]]),
    "O": (0.62, [_arc(0.31, 0.5, 0.31, 0.5, -110, 252, 24)]),
    "P": (0.50, [[(0.02, 1.0), (0.02, 0.0)], [(0.02, 0.0), (0.30, 0.0), (0.46, 0.09), (0.48, 0.26), (0.38, 0.43), (0.04, 0.50)]]),
    "Q": (0.62, [_arc(0.31, 0.5, 0.31, 0.5, -110, 252, 24), [(0.36, 0.72), (0.64, 1.04)]]),
    "R": (0.52, [[(0.02, 1.0), (0.02, 0.0)], [(0.02, 0.0), (0.30, 0.0), (0.46, 0.09), (0.48, 0.26), (0.38, 0.43), (0.04, 0.50)],
                 [(0.20, 0.49), (0.54, 1.0)]]),
    "S": (0.50, [[(0.48, 0.12), (0.36, 0.01), (0.20, 0.0), (0.05, 0.09), (0.03, 0.24), (0.14, 0.38), (0.30, 0.47),
                  (0.45, 0.57), (0.52, 0.74), (0.47, 0.91), (0.31, 1.0), (0.12, 0.98), (0.0, 0.86)]]),
    "T": (0.56, [[(0.0, 0.02), (0.56, 0.0)], [(0.28, 0.0), (0.28, 1.0)]]),
    "U": (0.54, [[(0.02, 0.0)] + _arc(0.27, 0.68, 0.25, 0.32, 180, 0, 12) + [(0.52, 0.0)]]),
    "V": (0.56, [[(0.0, 0.0), (0.28, 1.0), (0.56, 0.0)]]),
    "W": (0.80, [[(0.0, 0.0), (0.18, 1.0), (0.40, 0.30), (0.62, 1.0), (0.80, 0.0)]]),
    "X": (0.54, [[(0.0, 0.0), (0.54, 1.0)], [(0.54, 0.0), (0.0, 1.0)]]),
    "Y": (0.54, [[(0.0, 0.0), (0.27, 0.50), (0.54, 0.0)], [(0.27, 0.50), (0.27, 1.0)]]),
    "Z": (0.50, [[(0.02, 0.01), (0.50, 0.0), (0.0, 1.0), (0.52, 0.99)]]),
    "0": (0.50, [_arc(0.25, 0.5, 0.25, 0.5, -90, 270, 20)]),
    "1": (0.28, [[(0.02, 0.20), (0.20, 0.0), (0.20, 1.0)]]),
    "2": (0.48, [[(0.02, 0.22), (0.12, 0.05), (0.28, 0.0), (0.44, 0.08), (0.46, 0.28), (0.30, 0.52), (0.0, 1.0), (0.50, 0.99)]]),
    "3": (0.46, [[(0.02, 0.10), (0.20, 0.0), (0.40, 0.06), (0.42, 0.24), (0.20, 0.45), (0.42, 0.58), (0.46, 0.80), (0.30, 0.99), (0.0, 0.92)]]),
    "4": (0.50, [[(0.36, 1.0), (0.36, 0.0), (0.0, 0.70), (0.50, 0.70)]]),
    "5": (0.46, [[(0.44, 0.0), (0.06, 0.0), (0.03, 0.44), (0.24, 0.38), (0.42, 0.48), (0.46, 0.74), (0.32, 0.97), (0.0, 0.94)]]),
    "6": (0.48, [[(0.42, 0.04), (0.24, 0.04), (0.08, 0.22), (0.02, 0.50), (0.04, 0.78), (0.16, 0.97), (0.32, 1.0),
                  (0.46, 0.88), (0.48, 0.68), (0.36, 0.52), (0.18, 0.52), (0.04, 0.64)]]),
    "7": (0.46, [[(0.0, 0.01), (0.46, 0.0), (0.16, 1.0)]]),
    "8": (0.48, [_arc(0.24, 0.25, 0.19, 0.24, 90, 450, 16), _arc(0.24, 0.74, 0.23, 0.26, -90, 270, 16)]),
    "9": (0.48, [[(0.44, 0.40), (0.30, 0.50), (0.10, 0.46), (0.02, 0.26), (0.12, 0.04), (0.30, 0.0), (0.46, 0.12), (0.46, 0.50), (0.38, 0.84), (0.16, 1.0), (0.04, 0.94)]]),
    ".": (0.10, [_dot(0.05, 0.93)]),
    ",": (0.12, [[(0.08, 0.88), (0.02, 1.12)]]),
    "!": (0.13, [[(0.07, 0.0), (0.06, 0.70)], _dot(0.06, 0.94)]),
    "?": (0.46, [[(0.02, 0.20), (0.12, 0.04), (0.26, 0.0), (0.42, 0.08), (0.45, 0.25), (0.34, 0.42), (0.23, 0.52), (0.22, 0.70)],
                 _dot(0.22, 0.94)]),
    "'": (0.09, [[(0.07, -0.02), (0.03, 0.26)]]),
    "-": (0.30, [[(0.02, 0.54), (0.30, 0.52)]]),
    "(": (0.20, [_arc(0.30, 0.5, 0.26, 0.58, 122, 238, 10)]),
    ")": (0.20, [_arc(-0.10, 0.5, 0.26, 0.58, -58, 58, 10)]),
    ":": (0.10, [_dot(0.05, 0.36), _dot(0.05, 0.92)]),
    "—": (0.86, [[(0.04, 0.52), (0.84, 0.50)]]),
    "·": (0.12, [_dot(0.06, 0.52)]),
    "~": (0.40, [[(0.02, 0.60), (0.10, 0.50), (0.20, 0.52), (0.30, 0.60), (0.40, 0.48)]]),
}
CAPS["É"] = (0.48, CAPS["E"][1] + [[(0.16, -0.12), (0.34, -0.28)]])
CAPS["È"] = (0.48, CAPS["E"][1] + [[(0.32, -0.12), (0.14, -0.28)]])
CAPS["Ê"] = (0.48, CAPS["E"][1] + [[(0.08, -0.11), (0.24, -0.28), (0.40, -0.11)]])
CAPS["À"] = (0.58, CAPS["A"][1] + [[(0.38, -0.12), (0.20, -0.28)]])
CAPS["Ç"] = (0.56, CAPS["C"][1] + [[(0.32, 1.0), (0.36, 1.12), (0.24, 1.22)]])

# Bold lowercase (x-band 0.42..1, ascender 0.05, descender 1.36).
LOWER = {
    "a": (0.52, [_arc(0.25, 0.72, 0.24, 0.28, -15, 345, 16), [(0.50, 0.44), (0.50, 0.96), (0.56, 1.0)]]),
    "b": (0.52, [[(0.03, 0.05), (0.03, 1.0)], _arc(0.27, 0.72, 0.25, 0.28, 190, 540, 16)]),
    "e": (0.50, [[(0.03, 0.72), (0.48, 0.71), (0.46, 0.58), (0.36, 0.46), (0.24, 0.43), (0.10, 0.48), (0.02, 0.62),
                  (0.02, 0.82), (0.10, 0.96), (0.26, 1.0), (0.40, 0.97), (0.48, 0.90)]]),
    "g": (0.52, [_arc(0.25, 0.70, 0.24, 0.27, -15, 345, 16), [(0.50, 0.44), (0.50, 1.16)] + _arc(0.28, 1.16, 0.22, 0.2, 0, 160, 8)[1:]]),
    "i": (0.13, [[(0.06, 0.45), (0.06, 1.0)], _dot(0.06, 0.20)]),
    "n": (0.50, [[(0.03, 0.43), (0.03, 1.0)], [(0.03, 0.62), (0.12, 0.47), (0.27, 0.43), (0.42, 0.48), (0.48, 0.62), (0.48, 1.0)]]),
    "q": (0.54, [_arc(0.25, 0.72, 0.24, 0.28, -15, 345, 16), [(0.50, 0.44), (0.50, 1.36), (0.60, 1.32)]]),
    "r": (0.38, [[(0.03, 0.43), (0.03, 1.0)], [(0.03, 0.66), (0.12, 0.49), (0.25, 0.43), (0.38, 0.46)]]),
    "s": (0.42, [[(0.40, 0.50), (0.28, 0.43), (0.12, 0.44), (0.03, 0.53), (0.08, 0.65), (0.24, 0.71), (0.37, 0.78),
                  (0.42, 0.89), (0.33, 0.98), (0.16, 1.0), (0.0, 0.93)]]),
    "t": (0.36, [[(0.15, 0.12), (0.15, 0.90), (0.22, 0.99), (0.36, 0.96)], [(0.0, 0.44), (0.34, 0.43)]]),
    "u": (0.50, [[(0.02, 0.43), (0.02, 0.82), (0.10, 0.96), (0.25, 1.0), (0.40, 0.95), (0.48, 0.82)], [(0.48, 0.43), (0.48, 0.96), (0.54, 1.0)]]),
    "v": (0.48, [[(0.0, 0.43), (0.24, 1.0), (0.48, 0.43)]]),
    "z": (0.46, [[(0.01, 0.44), (0.45, 0.43), (0.02, 1.0), (0.48, 0.99)]]),
    "-": (0.40, [[(0.02, 0.76), (0.11, 0.66), (0.21, 0.68), (0.30, 0.76), (0.40, 0.64)]]),   # the title's wavy hyphen
    "·": (0.14, [_dot(0.07, 0.72)]),
}


def glyph(ch, lower=False):
    if lower and ch in LOWER:
        return LOWER[ch]
    if ch in CAPS:
        return CAPS[ch]
    if ch in LOWER:
        return LOWER[ch]
    raise KeyError(ch)


def measure(text, size, track=0.16, space=0.40, lower=False):
    w = 0.0
    for ch in text:
        w += space if ch == " " else glyph(ch, lower)[0] + track
    return max(0.0, (w - track)) * size


def letter(d, text, x, y, size, width, color, seed=0, align="center", track=0.16, space=0.40,
           tilt=0.0, lower=False, flip_every=0, turn=None, jitter=1.0, s=SS, blob=True, dot=0.62, pen=(0.82, 0.30)):
    """Hand-letter `text` onto ImageDraw d at supersample s.

    size: cap height (px, page/cell units); baseline at y. width: nib width (px).
    flip_every=2 turns every second glyph (index 1, 3, ...) over. `turn` maps a glyph
    index to its turn drawing 0..4 (0 upright, 4 = turned 180 deg) -- for the film's
    title; default: flipped glyphs at 4. Returns the advance width.
    """
    rng = _rng("letter", text, seed)
    total = measure(text, size, track, space, lower)
    x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    cx = 0.0
    gi = 0
    for ch in text:
        if ch == " ":
            cx += space * size
            continue
        gw, strokes = glyph(ch, lower)
        rot = math.radians(rng.uniform(-3.0, 3.0) * jitter)
        sc = size * (1 + rng.uniform(-0.06, 0.06) * jitter)
        dy = rng.uniform(-0.045, 0.045) * size * jitter
        wv = width * (1 + rng.uniform(-0.10, 0.10) * jitter)
        ang = 0.0
        if flip_every and gi % flip_every == 1:
            ang = math.pi * ((turn.get(gi, 4) if turn else 4) / 4.0)
        pivot_y = 0.72 if (lower and ch in LOWER) else 0.5
        for stro in strokes:
            pts = []
            for (u, v) in stro:
                u += rng.uniform(-0.012, 0.012) * jitter
                v += rng.uniform(-0.012, 0.012) * jitter
                if ang:
                    du, dv = u - gw / 2, v - pivot_y
                    u = gw / 2 + du * math.cos(ang) - dv * math.sin(ang)
                    v = pivot_y + du * math.sin(ang) + dv * math.cos(ang)
                px, py = (u - gw / 2) * sc, (v - 1.0) * sc
                px, py = px * math.cos(rot) - py * math.sin(rot), px * math.sin(rot) + py * math.cos(rot)
                gx = cx + gw * size / 2 + px
                gy = py + dy
                X = x0 + gx * ct - gy * st
                Y = y + gx * st + gy * ct
                pts.append((X * s, Y * s))
            if len(pts) == 1:
                X, Y = pts[0]
                r = wv * s * dot
                d.ellipse([X - r, Y - r * 1.1, X + r, Y + r * 1.1], fill=tuple(color) + (255,))
                continue
            pen_stroke(d, pts, wv * s, color, nib=pen[0], hair=pen[1], blob=blob)
        cx += (gw + track) * size
        gi += 1
    return total


# ================================================================== balloons
def balloon(d, lines, cx, cy, tail_to, size=36, seed=0, s=SS, pen=4.4, rx=None, ry=None):
    """White oval with a hand ink outline and a curved pointed tail; lettered lines."""
    rng = _rng("balloon", tuple(lines), seed)
    tw = max(measure(t, size) for t in lines)
    rx = rx or tw / 2 + size * 0.95
    ry = ry or (len(lines) * size * 1.38) / 2 + size * 0.62
    # oval, a little irregular (hand-drawn), slightly flattened at the bottom
    ph = rng.uniform(0, 6.28)
    pts = []
    N = 72
    for k in range(N):
        a = 2 * math.pi * k / N
        rr = 1 + 0.025 * math.sin(2 * a + ph) + 0.015 * math.sin(3 * a + 2 * ph)
        yy = math.sin(a) * (0.94 if math.sin(a) > 0 else 1.0)
        pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * yy))
    tx, ty = tail_to
    ang = math.atan2(ty - cy, tx - cx)
    spread = 0.20 + 0.10 * min(1.0, 160 / max(60, math.hypot(tx - cx, ty - cy)))

    def onrim(a, k=1.0):
        return (cx + rx * k * math.cos(a), cy + ry * k * math.sin(a))

    e0, e1 = onrim(ang - spread), onrim(ang + spread)
    # curved tail: both edges bow the same way (a pen tail, not a triangle)
    bend = 0.16 * (1 if (tx - cx) * (ty - cy) >= 0 else -1)

    def qcurve(p, q, b):
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        nx, ny = -(q[1] - p[1]) / max(L, 1), (q[0] - p[0]) / max(L, 1)
        c = (mx + nx * L * b, my + ny * L * b)
        return [((1 - t) ** 2 * p[0] + 2 * (1 - t) * t * c[0] + t * t * q[0],
                 (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * c[1] + t * t * q[1]) for t in np.linspace(0, 1, 14)]

    t0 = qcurve(e0, (tx, ty), bend)
    t1 = qcurve(e1, (tx, ty), bend)
    S = lambda P: [(x * s, y * s) for x, y in P]
    d.polygon(S(pts), fill=WHITE + (255,))
    d.polygon(S(t0 + t1[::-1] + [onrim(ang, 0.7)]), fill=WHITE + (255,))
    # outline: the oval with a gap where the tail joins
    a_list = [2 * math.pi * k / N for k in range(N)]
    run = []
    for a, p in zip(a_list, pts):
        da = (a - ang + math.pi) % (2 * math.pi) - math.pi
        if abs(da) < spread * 0.96:
            if len(run) > 1:
                pen_stroke(d, S(run), pen * s, INK, nib=0.55, hair=0.45)
            run = []
        else:
            run.append(p)
    if len(run) > 1:
        # join the wrap-around piece
        pen_stroke(d, S(run), pen * s, INK, nib=0.55, hair=0.45)
    pen_stroke(d, S(t0), pen * s, INK, nib=0.55, hair=0.45)
    pen_stroke(d, S(t1), pen * s, INK, nib=0.55, hair=0.45)
    n = len(lines)
    for i, t in enumerate(lines):
        yb = cy + (i - (n - 1) / 2) * size * 1.38 + size / 2
        letter(d, t, cx, yb, size, size * 0.15, INK, seed=seed * 10 + i, s=s)
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def caption(d, text, size=32, seed=0, s=SS, pad=14):
    """Corner caption box: the panel border makes its top and left; two ruled sides."""
    rng = _rng("caption", text, seed)
    w = measure(text, size) + 2 * pad + 6
    h = size + 2 * pad + 4
    S = lambda P: [(x * s, y * s) for x, y in P]
    d.rectangle([0, 0, w * s, h * s], fill=WHITE + (255,))
    ruled(d, (w * s, 0), (w * s, h * s), 4.0 * s, INK, rng, bow=0.6 * s)
    ruled(d, (0, h * s), (w * s, h * s), 4.0 * s, INK, rng, bow=0.6 * s)
    letter(d, text, pad + 4, pad + size + 2, size, size * 0.15, INK, seed=seed, align="left", s=s)
    return (0, 0, w, h)


def sfx(d, text, x, y, size, tilt, seed=0, s=SS):
    """Red tilted sound lettering, heavier nib, with a darker ink edge (two passes)."""
    letter(d, text, x, y, size, size * 0.27, RED_EDGE, seed=seed, tilt=tilt, s=s, track=0.22)
    letter(d, text, x, y, size, size * 0.19, RED, seed=seed, tilt=tilt, s=s, track=0.22)


# ================================================================== per-cell lettering
# Positions are cell px (900x600). Tails point at the page-pose mouth of the figure the
# puppet unit draws (from the approved test shot); U2/editor may pass tail_to to meet a
# moved mouth -- the value is then part of that cell's canonical spec, used by page and film.
LETTERING = {
    "A": [dict(kind="caption", text="GARE DE ST-ROCH, 6 H 10.", seed=1),
          dict(kind="balloon", lines=["PERSONNE ?"], at=(470, 150), tail_to=(372, 206), size=34, seed=2)],
    "B": [dict(kind="sfx", text="DING !", at=(715, 165), size=72, tilt=-12, seed=11),
          dict(kind="sfx", text="DING !", at=(748, 318), size=72, tilt=-5, seed=12)],
    "C": [dict(kind="sfx", text="TOC TOC.", at=(252, 128), size=60, tilt=-9, seed=31)],
    "D": [dict(kind="balloon", lines=["UNE CLÉ ?"], at=(176, 96), tail_to=(318, 214), size=36, seed=41)],
    "E": [dict(kind="balloon", lines=["C'EST POUR", "MOI ?"], at=(196, 108), tail_to=(372, 176), size=38, seed=51)],
    "F": [dict(kind="balloon", lines=["TANT PIS."], at=(310, 104), tail_to=(196, 204), size=36, seed=61)],
    "G": [dict(kind="caption", text="IL TIRE LA CORDE.", seed=71)],
    "H": [dict(kind="caption", text="PLUS PERSONNE.", seed=81)],
    "I": [dict(kind="balloon", lines=["MERCI."], at=(782, 140), tail_to=(640, 252), size=36, seed=91)],
}


def lettering(c, tail_to=None, s=SS):
    """The cell's balloon / caption / SFX as a 900x600 RGBA layer (page pose = film)."""
    img = Image.new("RGBA", (CW * s, CH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for item in LETTERING[c]:
        if item["kind"] == "caption":
            caption(d, item["text"], seed=item["seed"], s=s)
        elif item["kind"] == "balloon":
            t = tail_to or item["tail_to"]
            balloon(d, item["lines"], item["at"][0], item["at"][1], t, size=item["size"], seed=item["seed"], s=s)
        elif item["kind"] == "sfx":
            sfx(d, item["text"], item["at"][0], item["at"][1], item["size"], item["tilt"], seed=item["seed"], s=s)
    return img.resize((CW, CH), Image.LANCZOS) if s != 1 else img


# ================================================================== marks
def mark_drawing(d, x, y, u, seed, s=SS):
    """Red barbed crossing mark at (x, y), state u in [0, 1]:
    u=0 across (long horizontal arrow), 0.5 neutral (equal arms), 1 down (long vertical).
    Two fletched arrows on the axes plus two short fletched diagonals, as on the
    reference page; inked twice (dark edge, then red)."""
    rng = _rng("mark", seed)
    Lh = 74 - 50 * u        # half-length of the horizontal arrow: 74 / 49 / 24
    Lv = 24 + 50 * u
    jit = [rng.uniform(-1.6, 1.6) for _ in range(16)]
    diag = 30 + jit[0]

    def arrow_strokes(dx, dy, L, head):
        ex, ey = x + dx * L, y + dy * L           # head end
        bx, by = x - dx * L, y - dy * L           # tail end
        px, py = -dy, dx
        hs = 10 + 6 * (L / 74)
        strokes = [[(bx, by), (ex, ey)]]
        if head:
            strokes.append([(ex - dx * hs * 1.5 + px * hs * 0.9, ey - dy * hs * 1.5 + py * hs * 0.9), (ex, ey),
                            (ex - dx * hs * 1.5 - px * hs * 0.9, ey - dy * hs * 1.5 - py * hs * 0.9)])
        # fletching: two pairs of barbs at the tail
        for k in range(1):
            fx, fy = bx + dx * (4 + 11 * k), by + dy * (4 + 11 * k)
            for sg in (1, -1):
                strokes.append([(fx, fy), (fx - dx * 8 + px * sg * 9, fy - dy * 8 + py * sg * 9)])
        return strokes

    allst = []
    allst += arrow_strokes(1, 0, Lh, True)
    allst += arrow_strokes(0, 1, Lv, True)
    diag_st = []
    for (dx, dy) in ((0.7071, -0.7071), (-0.7071, -0.7071)):
        ex, ey = x + dx * diag, y + dy * diag
        bx, by = x - dx * diag, y - dy * diag
        px, py = -dy, dx
        diag_st.append([(bx, by), (ex, ey)])
        for sg in (1, -1):
            diag_st.append([(bx + dx * 3, by + dy * 3), (bx + dx * 3 - dx * 7 + px * sg * 7, by + dy * 3 - dy * 7 + py * sg * 7)])
    S = lambda P: [((px + jit[(i * 3) % 16] * 0.4) * s, (py + jit[(i * 5 + 1) % 16] * 0.4) * s) for i, (px, py) in enumerate(P)]
    for col, w, wd in ((RED_EDGE, 9.5, 7.0), (RED, 6.4, 4.4)):
        for st_ in diag_st:
            pen_stroke(d, S(st_), wd * s, col, nib=0.45, hair=0.62, taper=(0.2, 0.2))
        for st_ in allst:
            pen_stroke(d, S(st_), w * s, col, nib=0.45, hair=0.62, taper=(0.2, 0.2))


def marks_layer(states, s=SS):
    """Page-size RGBA of the eight marks; states[i] is mark i's u (MARKS order)."""
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for i, ((x, y), u) in enumerate(zip(MARKS, states)):
        mark_drawing(d, x, y, float(u), seed=i, s=s)
    return img.resize((PW, PH), Image.LANCZOS) if s != 1 else img


# turn drawings: 3 per mark (plan: "3 drawings each"), from a state toward another
def turn_states(u_from, u_to, k):
    """Drawing k (0..3) of one mark's turn: 0 = u_from, 3 = u_to."""
    return u_from + (u_to - u_from) * (min(3, max(0, k)) / 3.0)


U_ACROSS, U_NEUTRAL, U_DOWN = 0.0, 0.5, 1.0


# ================================================================== page furniture
def _chamfered(c):
    """Which corners of cell c meet a crossing mark (chamfered on the page)."""
    r, _ = cell_rc(c)
    return {"tl": r > 0, "tr": r > 0, "bl": r < 2, "br": r < 2}


CHAMFER = 34


def cell_outline(c):
    x0, y0 = cell_origin(c)
    x1, y1 = x0 + CW, y0 + CH
    ch = _chamfered(c)
    k = CHAMFER
    P = []
    P += [(x0, y0 + k), (x0 + k, y0)] if ch["tl"] else [(x0, y0)]
    P += [(x1 - k, y0), (x1, y0 + k)] if ch["tr"] else [(x1, y0)]
    P += [(x1, y1 - k), (x1 - k, y1)] if ch["br"] else [(x1, y1)]
    P += [(x0 + k, y1), (x0, y1 - k)] if ch["bl"] else [(x0, y1)]
    return P


def cell_overlay(c, s=SS):
    """900x600 RGBA: what the scaffold lays over cell c (corner paper, border, id tab)."""
    full = _furniture_layer(s)
    x0, y0 = cell_origin(c)
    return full.crop((x0, y0, x0 + CW, y0 + CH))


@lru_cache(maxsize=2)
def _furniture_layer(s=SS):
    """Page-size RGBA: chamfer paper, hand-ruled borders, id tabs (no marks/rails)."""
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    mask = Image.new("L", (PW * s, PH * s), 0)
    md = ImageDraw.Draw(mask)
    for c in CELLS:
        x0, y0 = cell_origin(c)
        md.rectangle([x0 * s, y0 * s, (x0 + CW) * s, (y0 + CH) * s], fill=255)
        md.polygon([(x * s, y * s) for x, y in cell_outline(c)], fill=0)
    paper = paper_sheet().resize((PW * s, PH * s), Image.BICUBIC).convert("RGBA")
    img.paste(paper, (0, 0), mask)
    for c in CELLS:
        rng = _rng("border", c)
        P = cell_outline(c)
        for a, b in zip(P, P[1:] + P[:1]):
            ruled(d, (a[0] * s, a[1] * s), (b[0] * s, b[1] * s), 7.2 * s, INK, rng, bow=1.4 * s)
        # id tab
        x0, y0 = cell_origin(c)
        bx, by, bw = x0 + CW - 54, y0 + CH - 54, 40
        if _chamfered(c)["br"]:
            bx, by = x0 + CW - 54 - 4, y0 + CH - 54 - 4
        d.rectangle([bx * s, by * s, (bx + bw) * s, (by + bw) * s], fill=WHITE + (255,))
        for a, b in (((bx, by), (bx + bw, by)), ((bx + bw, by), (bx + bw, by + bw)),
                     ((bx + bw, by + bw), (bx, by + bw)), ((bx, by + bw), (bx, by))):
            ruled(d, (a[0] * s, a[1] * s), (b[0] * s, b[1] * s), 3.0 * s, INK, rng, bow=0.4 * s)
        letter(d, c, bx + bw / 2, by + bw - 9, 23, 3.6, INK, seed=ord(c), s=s)
    return img


TITLE = "quatre-vingt-quinze"
TITLE_Y, TITLE_SIZE = 182, 150     # baseline, glyph unit size (x-band = 0.58 of it)


def title_glyph_count():
    return len([ch for ch in TITLE if ch != " "])


def title_layer(turn=None, color=INK, s=SS):
    """Page-size RGBA: the title. turn: {glyph index: drawing 0..4} for the flipped
    (odd-index) glyphs; None = the page (all flipped glyphs at 4, turned over)."""
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    letter(d, TITLE, PW / 2, TITLE_Y, TITLE_SIZE, TITLE_SIZE * 0.20, color, seed=95, lower=True,
           flip_every=2, turn=turn, track=0.12, jitter=0.7, s=s, blob=False, dot=0.48, pen=(0.42, 0.58))
    return img.resize((PW, PH), Image.LANCZOS) if s != 1 else img


def rails_layer(rail="both", s=SS):
    """Page-size RGBA: margin rails. rail: both (the page) | across | down (film)."""
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    rng = _rng("rails")
    on2 = rail in ("both", "down")
    on1 = rail in ("both", "across")
    c2 = INK if rail == "both" else (RED if on2 else MAUVE_L)
    c1 = INK if rail == "both" else (RED if on1 else MAUVE_L)
    num2 = RED if on2 else MAUVE_L
    num1 = RED if on1 else MAUVE_L
    # left rail: II en bas, the down route as a vertical list
    X = 74
    letter(d, "II", X, 360, 64, 10, num2, seed=2, s=s)
    letter(d, "en bas", X, 420, 30, 4.6, c2, seed=3, lower=True, s=s, jitter=0.6)
    ys = [520 + i * 214 for i in range(9)]   # 520 .. 2232, clear of the marks at 905 / 1595
    ys = [y + (34 if 835 < y < 975 else 0) - (34 if 1525 < y < 1665 else 0) for y in ys]
    for i, (c, y) in enumerate(zip(ROUTES["down"], ys)):
        letter(d, c, X, y, 40, 6.0, c2, seed=200 + i, s=s)
        if i < 8:
            ruled(d, (X * s, (y + 16) * s), (X * s, (ys[i + 1] - 52) * s), 3.0 * s, c2, rng, bow=0.6 * s)
            # a small arrowhead at the bottom of each link
            yb = ys[i + 1] - 52
            pen_stroke(d, [((X - 7) * s, (yb - 9) * s), (X * s, yb * s), ((X + 7) * s, (yb - 9) * s)], 3.0 * s, c2, nib=0.4, hair=0.6)
    # right rail: I en travers, the across route as a 3x3
    X = 3266
    letter(d, "I", X, 360, 64, 10, num1, seed=4, s=s)
    letter(d, "en travers", X, 420, 26, 4.0, c1, seed=5, lower=True, s=s, jitter=0.6)
    for i, c in enumerate(ROUTES["across"]):
        x = 3212 + (i % 3) * 54
        y = 540 + (i // 3) * 96
        letter(d, c, x, y, 38, 5.6, c1, seed=300 + i, s=s)
        if i % 3 < 2:
            ruled(d, ((x + 15) * s, (y - 19) * s), ((x + 39) * s, (y - 19) * s), 3.0 * s, c1, rng, bow=0.3 * s)
    return img.resize((PW, PH), Image.LANCZOS) if s != 1 else img


BOTTOM_LINE = "LIRE EN TRAVERS (I) PUIS EN BAS (II) — MÊME FIN : I."


def bottom_layer(s=SS):
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    letter(d, BOTTOM_LINE, PW / 2, 2374, 36, 5.4, INK, seed=7, s=s)
    return img.resize((PW, PH), Image.LANCZOS) if s != 1 else img


# ================================================================== the cut-paper arrow
ARROW_PTS = [(-46, -11), (6, -13), (4, -31), (46, 1), (5, 32), (7, 12), (-45, 13), (-38, 0)]


def gutter_point(a, b):
    """Where the arrow sits for the edge a->b, and its angle (deg, 0 = right, 90 = down)."""
    ra, ca = cell_rc(a)
    rb, cb = cell_rc(b)
    ax, ay = cell_origin(a)
    bx, by = cell_origin(b)
    acx, acy = ax + CW / 2, ay + CH / 2
    bcx, bcy = bx + CW / 2, by + CH / 2
    ang = math.degrees(math.atan2(bcy - acy, bcx - acx))
    if ra == rb:                     # horizontal step across a column gutter
        return (max(ax, bx) - GUT / 2, acy + 120), ang
    if ca == cb:                     # vertical step across a row gutter
        return (acx + 250, max(ay, by) - GUT / 2), ang
    if rb == ra + 1:                 # across return (row end -> next row start): row gutter
        return ((acx + bcx) / 2, max(ay, by) - GUT / 2), ang
    # down return (column end -> next column top): column gutter, mid height
    return (max(ax, bx) - GUT / 2, ROWY[1] + CH / 2), ang


def arrow_drawing(d, x, y, angle, k, seed=0, s=SS):
    """The red cut-paper arrow; k=0 entering (smaller, tilted, set back), k=1 laid down."""
    rng = _rng("arrow", seed)
    sc = 0.72 if k == 0 else 1.0
    tilt = (-9 if k == 0 else 0) + rng.uniform(-1.5, 1.5)
    back = -18 if k == 0 else 0
    a = math.radians(angle + tilt)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(px + back + rng.uniform(-0.8, 0.8), py + rng.uniform(-0.8, 0.8)) for px, py in ARROW_PTS]
    P = [((x + (px * ca - py * sa) * sc) * s, (y + (px * sa + py * ca) * sc) * s) for px, py in pts]
    sh = [(px + 3 * s, py + 4 * s) for px, py in P]
    d.polygon(sh, fill=MAUVE + (110,))            # it is a paper piece: it casts a little shadow
    d.polygon(P, fill=RED + (255,))
    # the scissor facets: a hair-thin lighter cut edge on two sides
    d.line(P[1:4], fill=(205, 120, 104, 200), width=max(1, int(1.2 * s)))


def arrow_layer(a, b, k, s=SS):
    """Page-size RGBA with the arrow for edge a->b at drawing k (0 or 1)."""
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    (x, y), ang = gutter_point(a, b)
    arrow_drawing(d, x, y, ang, k, seed=zlib.crc32((a + b).encode()) & 0xff, s=s)
    return img.resize((PW, PH), Image.LANCZOS) if s != 1 else img


# ================================================================== assembly
def scaffold_layer(marks=None, rail="both", title_turn=None, s=SS):
    """Page-size RGBA of everything that is not cell content: chamfer paper, borders,
    tabs, marks, rails, title, bottom line. marks: 8 u-values (default neutral)."""
    marks = [U_NEUTRAL] * 8 if marks is None else marks
    out = _furniture_layer(s).resize((PW, PH), Image.LANCZOS) if s != 1 else _furniture_layer(s).copy()
    for lay in (marks_layer(marks, s), rails_layer(rail, s), title_layer(title_turn, s=s), bottom_layer(s)):
        out.alpha_composite(lay)
    return out


def page_base():
    """The page's paper with every cell's canonical ground in place (RGB)."""
    page = paper_sheet().copy()
    for c in CELLS:
        page.paste(ground(c), cell_origin(c))
    return page


def compose_page(cells=None, marks=None, rail="both", with_lettering=True):
    """The printed page. cells: {c: 900x600 RGB or RGBA content}; RGBA content is laid on
    the canonical ground, RGB replaces it. Lettering and scaffold go on top."""
    page = page_base().convert("RGBA")
    for c in CELLS:
        x0, y0 = cell_origin(c)
        if cells and c in cells:
            im = cells[c]
            if im.mode == "RGBA":
                page.alpha_composite(im, (x0, y0))
            else:
                page.paste(im, (x0, y0))
        if with_lettering:
            page.alpha_composite(lettering(c), (x0, y0))
    page.alpha_composite(scaffold_layer(marks, rail))
    return page.convert("RGB")


# ================================================================== registry & contracts
FACTS = {
    # cell: (requires-before-on-any-route, establishes, salient for successor)
    "A": (set(), {"visitor_arrived", "envelope_sealed", "door_shut", "window_lit_empty"}, "arrival"),
    "B": (set(), {"bell_rang"}, "bell"),
    "C": ({"visitor_arrived"}, {"knocked_unanswered"}, "knock"),
    "D": ({"visitor_arrived"}, {"envelope_opened", "key_revealed", "man_watched"}, "key"),
    "E": ({"key_revealed"}, {"asked_c_est_pour_moi"}, "question"),
    "F": ({"key_revealed"}, {"key_left_on_bench", "visitor_gone"}, "giving_up"),
    "G": (set(), {"cord_pulled"}, "cord"),
    "H": (set(), {"window_dark", "bench_empty"}, "emptiness"),
    "I": ({"key_left_on_bench"}, {"key_home", "merci"}, "merci"),
}


def contract_check():
    """Solve both routes over the facts: every precondition is met before its cell on
    BOTH routes; each step is a legal neighbour edge; both routes cover all nine cells
    once and end on I; E's art and text carry both predecessors' salients."""
    res = {"routes": {}, "ok": True}
    for name, r in ROUTES.items():
        steps = []
        legal = True
        for a, b in zip(r, r[1:]):
            (ra, ca), (rb, cb) = cell_rc(a), cell_rc(b)
            if name == "across":
                ok = (ra == rb and cb == ca + 1) or (ca == 2 and cb == 0 and rb == ra + 1)
            else:
                ok = (ca == cb and rb == ra + 1) or (ra == 2 and rb == 0 and cb == ca + 1)
            steps.append({"edge": f"{a}->{b}", "legal": ok})
            legal &= ok
        have = set()
        pre = []
        for i, c in enumerate(r):
            need = FACTS[c][0]
            missing = sorted(need - have)
            pre.append({"cell": c, "index": i + 1, "requires": sorted(need), "missing": missing})
            have |= FACTS[c][1]
        cover = sorted(r) == sorted(CELLS) and len(r) == 9
        ok = legal and cover and r[-1] == "I" and r[0] == "A" and all(not p["missing"] for p in pre)
        res["routes"][name] = {"order": "".join(r), "steps": steps, "preconditions": pre, "covers_all_once": cover,
                               "ends_on": r[-1], "ok": ok}
        res["ok"] &= ok
    pa = ROUTES["across"][ROUTES["across"].index("E") - 1]
    pd = ROUTES["down"][ROUTES["down"].index("E") - 1]
    e_carries = {"key": "key raised high in her hand (prop on wrist frame)", "bell": "head turned up toward panel top, where B's bell hangs on the page"}
    res["E"] = {"pred_across": pa, "pred_down": pd, "salient_across": FACTS[pa][2], "salient_down": FACTS[pd][2],
                "E_art_carries": e_carries, "both_licensed": FACTS[pa][2] in e_carries and FACTS[pd][2] in e_carries,
                "position_across": ROUTES["across"].index("E") + 1, "position_down": ROUTES["down"].index("E") + 1}
    res["ok"] &= res["E"]["both_licensed"]
    return res


if __name__ == "__main__":
    print(json.dumps(contract_check(), indent=1))
