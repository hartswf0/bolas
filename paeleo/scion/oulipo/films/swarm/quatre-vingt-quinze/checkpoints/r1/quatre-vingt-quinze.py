"""quatre-vingt-quinze -- the crossed page, read across and then down (plan r0, editor build).

One page, nine immutable cells (A..I), two reading routes:
    across = A B C D E F G H I     (a lost-key story)
    down   = A D G B E H C F I     (a set-up)
The film is a rostrum camera over the SAME page art the page PNG prints. Each cell is a
function of (cell id, cell-local frame) only -- there is no route argument anywhere in
the cell art. The route lives only in the camera path, the crossing marks' long arm,
the active margin rail, the gutter arrow and the inherited sound tail.

Imports (none edited here):
    U1 grid.py / registry.json  : paper, painted salmon pools, hand lettering, borders,
                                  marks, rails, title, bottom line, gutter arrow
    U2 puppets.py / exposure.json: FK cut-paper silhouette puppets, replacement heads
                                  and hands, props, exposure sheets (24 fps, on 2s)
    U3 forage/                  : CC0 key cut (via puppets.key_source), FSA stencil
                                  plates A and H, one fixed sound cue per cell, room tone
Rendering is kit.Film (unedited); every frame is pasted from this composite. No grain,
no filter, no typeface.

Run from the project root:
    python3 films/quatre-vingt-quinze.py                 # page, cells, strips, film
    python3 films/quatre-vingt-quinze.py --stills 44.5   # stills only (kit)
    QVQ_CUT=across python3 films/quatre-vingt-quinze.py  # reader cut: title + across + end only
    QVQ_CUT=down   python3 films/quatre-vingt-quinze.py  # reader cut: title + down + end only

r1 (repair round 1): E has a commissioned skyward head (U2 v_sky, 0.50-1.67 s cell time) and a
retimed lift; B's cue carries strike 13's real ring further (overlap-add of its own ring grains);
E's clink is ducked; the end shows only the two final route edges arriving in I; single-route
reader cuts are rendered from the same composite (time-mapped master frames).
"""
import hashlib
import json
import math
import os
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

FILMS = Path(__file__).resolve().parent
PROJECT = FILMS.parent
SW = FILMS / "swarm" / "quatre-vingt-quinze"
SRC = FILMS / "sources" / "quatre-vingt-quinze"
FORAGE = SRC / "forage"
for p in (FILMS, SW / "grid", SW / "puppets"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from kit import Film  # noqa: E402
import grid as G      # noqa: E402  U1
import puppets as P   # noqa: E402  U2

SLUG = "quatre-vingt-quinze"
REVISION = "r1"
REGISTRY = json.load(open(SW / "grid" / "registry.json"))
EXPOSURE = json.load(open(SW / "puppets" / "exposure.json"))

FPS = 24
SECONDS = 64
FW, FH = 1280, 720
PW, PH, CW, CH = G.PW, G.PH, G.CW, G.CH
CELLS = G.CELLS
ACROSS = list("ABCDEFGHI")
DOWN = list("ADGBEHCFI")
ROUTES = {"across": ACROSS, "down": DOWN}
T_ACROSS, T_DOWN = 3, 32          # route starts (s); 3 s per cell
PER = 3
WASH = 0.55                       # the paper wash over an unread cell
OUTSIDE = G.PAPER                 # beyond the sheet (only seen in whole-page views)

# the beat clock (plan section 7)
assert T_DOWN + PER * DOWN.index("E") == 44 <= 44.5 < 47, "beat clock"
assert ACROSS[-1] == DOWN[-1] == "I" and ACROSS[0] == DOWN[0] == "A"

# ----------------------------------------------------------------- schedule ---
OCC = []   # (route, index, cell, start frame)
for i, c in enumerate(ACROSS):
    OCC.append(("across", i, c, (T_ACROSS + PER * i) * FPS))
for i, c in enumerate(DOWN):
    OCC.append(("down", i, c, (T_DOWN + PER * i) * FPS))
NF = P.NFRAMES  # 72 frames per occurrence


def occurrence(K):
    for o in OCC:
        if o[3] <= K < o[3] + NF:
            return o
    return None


def occ_start(route, c):
    return [o[3] for o in OCC if o[0] == route and o[2] == c][0]


def phase(K):
    t = K / FPS
    if t < T_ACROSS:
        return "title"
    if t < 30:
        return "across"
    if t < T_DOWN:
        return "turn"
    if t < 59:
        return "down"
    return "end"


# ------------------------------------------------------------ reader cuts ---
# A reader cut is a time map onto master frames: (cut start s, cut end s, master start s).
CUT = os.environ.get("QVQ_CUT")          # None | "across" | "down"
CUT_SEGMENTS = {"across": [(0, 30, 0), (30, 35, 59)], "down": [(0, 3, 0), (3, 35, 32)]}
END_FROM = G.U_ACROSS if CUT == "across" else G.U_DOWN   # the route the end hold returns from


def master_K(k):
    if not CUT:
        return k
    t = k / FPS
    for a, b, m in CUT_SEGMENTS[CUT]:
        if a <= t < b or (b == CUT_SEGMENTS[CUT][-1][1] and t >= b):
            return int(round((t - a + m) * FPS))
    return k


# ------------------------------------------------------------------ cell art ---
def tail(c):
    """Balloon tail: U2's page-pose mouth anchor, the SAME value for page and film."""
    if c == "F":    # U2's anchor lands in her hat (balloon is above it); U1's tail meets the face
        return None
    m = P.mouth_anchor(c)
    return (float(m[0]), float(m[1])) if m else None


@lru_cache(maxsize=None)
def _lettering(c):
    t = tail(c)
    return G.lettering(c, tail_to=t) if t else G.lettering(c)


@lru_cache(maxsize=None)
def _stencil(c):
    p = FORAGE / f"stencil_{c}.png"
    if not p.exists():
        return None
    im = Image.open(p).convert("RGBA")
    return im if im.size == (CW, CH) else im.resize((CW, CH), Image.LANCZOS)


@lru_cache(maxsize=None)
def _ground(c):
    return G.ground(c).convert("RGBA")


@lru_cache(maxsize=400)
def _cell_by_drawing(c, did):
    """U1 ground -> U3 stencil -> U2 puppets/props -> U1 lettering (RGB 900x600)."""
    im = _ground(c).copy()
    st = _stencil(c)
    if st is not None:
        im.alpha_composite(st)
    im.alpha_composite(P._render(c, did))
    im.alpha_composite(_lettering(c))
    return im.convert("RGB")


def cell_image(c, f=None):
    """Cell c at cell-local frame f (0..71); None = the page pose. No route argument."""
    sh = P.sheet(c)
    did = sh[-1] if f is None or f < 0 or f >= NF else sh[int(f)]
    return _cell_by_drawing(c, did)


@lru_cache(maxsize=None)
def _paper_cell(c):
    x0, y0 = G.cell_origin(c)
    return G.paper_sheet().crop((x0, y0, x0 + CW, y0 + CH))


@lru_cache(maxsize=64)
def _washed(c, did, a):
    return Image.blend(_cell_by_drawing(c, did), _paper_cell(c), a)


# ------------------------------------------------------------- route state ---
def wash_alpha(c, K):
    """Paper wash: over every cell in the title; lifts off each cell as it is read;
    returns over all cells at the turn (30.0-30.5 s). Identical in both occurrences."""
    t = K / FPS
    ph = phase(K)
    if ph == "title":
        return WASH
    if ph == "end":
        return 0.0
    if ph == "turn":
        return round(WASH * min(1.0, (t - 30.0) / 0.5), 3)
    route = ph
    k0 = occ_start(route, c)
    if K < k0:
        return WASH
    lk = K - k0
    if lk < 12:     # 0.5 s, on 2s
        return round(WASH * (1 - (lk // 2 * 2) / 12), 3)
    return 0.0


def active(K):
    """(cell, local frame) of the cell being read, or None. Only that cell animates."""
    o = occurrence(K)
    if o is None:
        return None
    return o[2], K - o[3]


def marks_state(K):
    """Eight u values (0 across-long, 0.5 neutral, 1 down-long), drawn on 2s."""
    t = K / FPS
    if t < 3.0:
        return (G.U_NEUTRAL,) * 8
    if t < 3.5:                          # horizontal arms grow long: 3 drawings
        k = min(3, 1 + int((K - 72) // 4))
        return (G.turn_states(G.U_NEUTRAL, G.U_ACROSS, k),) * 8
    if t < 30.0:
        return (G.U_ACROSS,) * 8
    if t < 32.0:                         # the turn, mark by mark, 3 drawings each
        st = [G.U_ACROSS] * 8
        n = (K - 720) // 2               # drawing slot 0..23
        for j, m in enumerate(G.MARK_TURN_ORDER):
            if n >= 3 * j:
                st[m] = G.turn_states(G.U_ACROSS, G.U_DOWN, min(3, n - 3 * j + 1))
        return tuple(st)
    if t < 59.0:
        return (G.U_DOWN,) * 8
    if t < 59.5:
        k = min(3, 1 + int((K - 59 * FPS) // 4))
        return (G.turn_states(END_FROM, G.U_NEUTRAL, k),) * 8
    return (G.U_NEUTRAL,) * 8


def rail_state(K):
    t = K / FPS
    if t < 1.5:
        return "both"
    if CUT == "down" and t < 3.0:
        return "down"
    if t < 31.0:
        return "across"
    if t < 59.5:
        return "across" if CUT == "across" else "down"
    return "both"


FLIPPED = [i for i in range(G.title_glyph_count()) if i % 2 == 1]


def title_state(K):
    """0-3 s: the alternate glyphs turn over one by one, 4 drawings each (36 drawings)."""
    if K >= 3 * FPS:
        return None
    n = K // 2                      # 12 drawings/s -> 0..35
    j, d = n // 4, n % 4 + 1
    return tuple((g, 4 if q < j else (d if q == j else 0)) for q, g in enumerate(FLIPPED))


def arrow_state(K):
    o = occurrence(K)
    if o is None or o[1] == 0:
        return None
    route, i, c, k0 = o
    prev = ROUTES[route][i - 1]
    return (prev, c, 0 if K - k0 < 2 else 1)


# ------------------------------------------------------------ page sprites ---
def _sprite(img):
    bb = img.getchannel("A").getbbox()
    if bb is None:
        return None
    return img.crop(bb), bb[0], bb[1]


@lru_cache(maxsize=1)
def BASE():
    """The sheet with every cell at its page pose (cell art + lettering), no scaffold."""
    page = G.paper_sheet().copy()
    for c in CELLS:
        page.paste(cell_image(c, None), G.cell_origin(c))
    return page


@lru_cache(maxsize=1)
def TOP():
    """Static scaffold: chamfer paper, hand-ruled borders, id tabs, bottom line."""
    fur = G._furniture_layer(G.SS).resize((PW, PH), Image.LANCZOS)
    fur.alpha_composite(G.bottom_layer())
    return fur


@lru_cache(maxsize=48)
def MARKS(state):
    return _sprite(G.marks_layer(list(state)))


@lru_cache(maxsize=4)
def RAILS(state):
    return _sprite(G.rails_layer(state))


@lru_cache(maxsize=40)
def TITLE(state):
    return _sprite(G.title_layer(dict(state) if state is not None else None))


@lru_cache(maxsize=40)
def ARROW(a, b, k):
    return _sprite(G.arrow_layer(a, b, k))


def _route_points(route, off):
    pts = []
    for c in ROUTES[route]:
        x0, y0 = G.cell_origin(c)
        pts.append((x0 + CW / 2 + off[0], y0 + CH / 2 + off[1]))
    return pts


def _partial(pts, frac):
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    tot, want, out = sum(seg), sum(seg) * frac, [pts[0]]
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if want >= L:
            out.append(b)
            want -= L
        else:
            u = want / L
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            break
    return out


@lru_cache(maxsize=40)
def END_LINES(n):
    """59.5-61.5 s (r1, simplified): only the two route edges that arrive in I draw themselves
    (n = drawing 1..24): across H->I from the left, down F->I from above, each in U1's red pen,
    meeting at one dot in I. No full-route tangle over the page."""
    s = G.SS
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    frac = min(1.0, n / 24)
    ix, iy = _centre("I")
    meet = (ix - 150, iy - 120)
    for prev in (("H"), ("F")):
        px, py = _centre(prev)
        start = (px + (120 if prev == "H" else -150), py + (-120 if prev == "H" else 120))
        pts = _partial([start, meet], frac)
        if len(pts) >= 2:
            G.pen_stroke(d, [(x * s, y * s) for x, y in pts], 6.0 * s, G.RED + (235,), nib=0.6, hair=0.5,
                         taper=(0.15, 0.05), blob=False)
    if frac >= 1.0:
        r = 14
        d.ellipse([(meet[0] - r) * s, (meet[1] - r) * s, (meet[0] + r) * s, (meet[1] + r) * s], fill=G.RED + (255,))
    return _sprite(img.resize((PW, PH), Image.LANCZOS))


@lru_cache(maxsize=4)
def E_BORDER(k):
    """61-62 s: E's border thickens (k = 1, 2), re-ruled over its own outline."""
    s = G.SS
    img = Image.new("RGBA", (PW * s, PH * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    rng = G._rng("E-thick", k)
    P_ = G.cell_outline("E")
    for a, b in zip(P_, P_[1:] + P_[:1]):
        G.ruled(d, (a[0] * s, a[1] * s), (b[0] * s, b[1] * s), (7.2 + 7 * k) * s, G.INK, rng, bow=1.4 * s)
    return _sprite(img.resize((PW, PH), Image.LANCZOS))


def end_state(K):
    t = K / FPS
    lines = None
    if 59.5 <= t < 62.5:
        n = min(24, (K - int(59.5 * FPS)) // 2 + 1)
        lines = n
        if t >= 62.0:                    # the lines lift in 2 drawings before the hold
            lines = -1 if K - 62 * FPS < 6 else None
    eb = None
    if 61.0 <= t < 62.0:
        eb = 1 if (K - 61 * FPS) < 4 or (K - 61 * FPS) >= 20 else 2
    return lines, eb


# --------------------------------------------------------------- compositing ---
def _put(canvas, spr, box):
    if spr is None:
        return
    img, ox, oy = spr
    x0, y0 = max(ox, box[0]), max(oy, box[1])
    x1, y1 = min(ox + img.size[0], box[2]), min(oy + img.size[1], box[3])
    if x1 <= x0 or y1 <= y0:
        return
    canvas.alpha_composite(img.crop((x0 - ox, y0 - oy, x1 - ox, y1 - oy)), (x0 - box[0], y0 - box[1]))


def compose(K, box=(0, 0, PW, PH)):
    """The page at film frame K, in page pixels, for the integer box (x0, y0, x1, y1).
    Pre-camera; this is where cell-space identity is measured."""
    X0, Y0, X1, Y1 = box
    canvas = Image.new("RGB", (X1 - X0, Y1 - Y0), OUTSIDE)
    ix0, iy0, ix1, iy1 = max(0, X0), max(0, Y0), min(PW, X1), min(PH, Y1)
    if ix1 > ix0 and iy1 > iy0:
        canvas.paste(BASE().crop((ix0, iy0, ix1, iy1)), (ix0 - X0, iy0 - Y0))
    act = active(K)
    for c in CELLS:
        x0, y0 = G.cell_origin(c)
        if x0 + CW <= X0 or x0 >= X1 or y0 + CH <= Y0 or y0 >= Y1:
            continue
        a = wash_alpha(c, K)
        f = act[1] if act and act[0] == c else None
        if f is None and a == 0:
            continue                     # BASE already holds the page pose
        sh = P.sheet(c)
        did = sh[-1] if f is None else sh[f]
        im = _washed(c, did, a) if a > 0 else _cell_by_drawing(c, did)
        canvas.paste(im, (x0 - X0, y0 - Y0))
    canvas = canvas.convert("RGBA")
    _put(canvas, (TOP(), 0, 0), box)
    _put(canvas, MARKS(marks_state(K)), box)
    _put(canvas, RAILS(rail_state(K)), box)
    _put(canvas, TITLE(title_state(K)), box)
    ar = arrow_state(K)
    if ar:
        _put(canvas, ARROW(*ar), box)
    lines, eb = end_state(K)
    if eb:
        _put(canvas, E_BORDER(eb), box)
    if lines:
        if lines > 0:
            _put(canvas, END_LINES(lines), box)
        else:                            # lifting: half-strength drawing
            img, ox, oy = END_LINES(24)
            im2 = img.copy()
            im2.putalpha(im2.getchannel("A").point(lambda v: v // 2))
            _put(canvas, (im2, ox, oy), box)
    return canvas.convert("RGB")


# -------------------------------------------------------------------- camera ---
VIEW_CELL = CH / 0.62                       # cell at ~62% of the frame height
VIEW_PAGE = PH * 1.04                       # whole sheet


def _centre(c):
    x0, y0 = G.cell_origin(c)
    return (x0 + CW / 2, y0 + CH / 2)


PAGE_VIEW = (PW / 2, PH / 2, VIEW_PAGE)


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


def _lerp_view(a, b, u):
    u = _ease(u)
    vh = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * u)
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, vh)


def camera(K):
    """(cx, cy, view height) in page px. Each read cell is entered from its predecessor's
    side in 0.5 s (eased); A is reached by a pull-in; turn and end pull out to the page."""
    t = K / FPS
    ph = phase(K)
    if ph == "title":
        return PAGE_VIEW
    if ph == "turn":
        return _lerp_view((*_centre("I"), VIEW_CELL), PAGE_VIEW, (t - 30.0) / 0.5)
    if ph == "end":
        return _lerp_view((*_centre("I"), VIEW_CELL), PAGE_VIEW, (t - 59.0) / 0.6)
    o = occurrence(K)
    route, i, c, k0 = o
    u = (K - k0) / 12.0
    here = (*_centre(c), VIEW_CELL)
    if i == 0:
        return _lerp_view(PAGE_VIEW, here, u)
    prev = ROUTES[route][i - 1]
    return _lerp_view((*_centre(prev), VIEW_CELL), here, u)


def frame_rgb(K):
    cx, cy, vh = camera(K)
    vw = vh * FW / FH
    fx0, fy0 = cx - vw / 2, cy - vh / 2
    box = (int(math.floor(fx0)) - 3, int(math.floor(fy0)) - 3,
           int(math.ceil(fx0 + vw)) + 3, int(math.ceil(fy0 + vh)) + 3)
    reg = compose(K, box)
    return reg.resize((FW, FH), Image.LANCZOS,
                      box=(fx0 - box[0], fy0 - box[1], fx0 - box[0] + vw, fy0 - box[1] + vh))


# --------------------------------------------------------------------- sound ---
def _wav(p):
    w = wave.open(str(p))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()) / 32768.0
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    return x


SOUND_SCHEDULE = [(o[3] / FPS, o[2], f"cue_{o[2]}.wav") for o in OCC]   # cue t0 = exposure frame 0
TURN_CLICKS = [30.0 + 0.25 * j for j in range(8)]


def _map_master_t(T):
    """Cut time of master time T (None when T is outside the cut)."""
    if not CUT:
        return T
    for a, b, m in CUT_SEGMENTS[CUT]:
        if m <= T < m + (b - a):
            return T - m + a
    return None


def sound(mix):
    R = mix.rate
    end_t = SECONDS if not CUT else CUT_SEGMENTS[CUT][-1][1]
    room = _wav(FORAGE / "room.wav")[: mix.n]
    env = np.ones(len(room))
    tt = np.arange(len(room)) / R
    env *= np.clip(tt / 2.5, 0, 1)                       # fades in under the title
    env *= np.clip(((end_t - 2.5) - tt) / 1.0, 0, 1)     # declared silence for the last 2.5 s
    mix.add(room[:, 0] * env / 1.414, 0.0, pan=-1.0)
    mix.add(room[:, 1] * env / 1.414, 0.0, pan=1.0)
    cues = {c: _wav(FORAGE / f"cue_{c}.wav") for c in CELLS}
    for at, c, _ in SOUND_SCHEDULE:                      # each cell's own cue, same on both routes
        at = _map_master_t(at)
        if at is None:
            continue
        x = cues[c]
        mix.add(x[:, 0] / 1.414, at, pan=-1.0)
        mix.add(x[:, 1] / 1.414, at, pan=1.0)
    for j, at in enumerate(TURN_CLICKS if not CUT else []):   # handmade: a paper click per mark
        m = G.MARK_TURN_ORDER[j]
        pan = (G.MARKS[m][0] / PW) * 2 - 1
        mix.click(at, gain=0.16, pan=pan * 0.6, bright=3200, seconds=0.025)


# ------------------------------------------------------------- page products ---
PAGE_K = SECONDS * FPS - 1      # the end hold: the page exactly as printed


def page_image():
    return compose(PAGE_K)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strip(route, page):
    """Walkthrough: the nine canonical cells in route order (3 x 3), red arrow between,
    the incoming edge lettered over each cell (e.g. 'D - E')."""
    s = G.SS
    gx, top, lab, gy = 170, 300, 110, 60
    Wd = 3 * CW + 4 * gx
    Ht = top + 3 * (lab + CH + gy) + 40
    out = G.paper_sheet().resize((Wd, Ht), Image.BICUBIC) if Wd > PW or Ht > PH else G.paper_sheet().crop((0, 0, Wd, Ht))
    out = out.convert("RGBA")
    over = Image.new("RGBA", (Wd * s, Ht * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(over, "RGBA")
    name = "I · EN TRAVERS" if route == "across" else "II · EN BAS"
    G.letter(d, name, Wd / 2, 150, 70, 9.0, G.INK, seed=11 if route == "across" else 12, s=s)
    G.letter(d, " ".join(ROUTES[route]), Wd / 2, 240, 44, 5.6, G.RED, seed=13, s=s)
    for i, c in enumerate(ROUTES[route]):
        r, k = divmod(i, 3)
        x = gx + k * (CW + gx)
        y = top + r * (lab + CH + gy) + lab
        x0, y0 = G.cell_origin(c)
        out.paste(page.crop((x0, y0, x0 + CW, y0 + CH)), (x, y))
        label = f"{ROUTES[route][i - 1]} - {c}" if i else f"{c}"
        G.letter(d, label, x + 70, y - 26, 40, 5.4, G.INK, seed=40 + i, s=s, align="left")
        if i:
            if k:
                G.arrow_drawing(d, x - gx / 2, y + CH / 2, 0, 1, seed=i, s=s)
            else:   # row return: arrow in the left margin, pointing in
                G.arrow_drawing(d, gx / 2, y + CH / 2, 0, 1, seed=i, s=s)
    out.alpha_composite(over.resize((Wd, Ht), Image.LANCZOS))
    return out.convert("RGB")


STAGE = os.environ.get("QVQ_STAGE")   # optional staging root (e.g. when the disk is full)


def _out(path):
    """Where a product is written: its project path, or the same relative path under STAGE."""
    path = Path(path)
    if not STAGE:
        return path
    return Path(STAGE) / path.relative_to(PROJECT)


def write_products():
    pages = _out(PROJECT / "assets" / "pages")
    pages.mkdir(parents=True, exist_ok=True)
    cells_dir = _out(SW / "cells")
    cells_dir.mkdir(parents=True, exist_ok=True)
    page = page_image()
    page_path = pages / f"{SLUG}.png"
    page.save(page_path, optimize=True)
    print("page ->", page_path, page.size)
    reg_cells = {e["id"]: e for e in REGISTRY["cells"]} if isinstance(REGISTRY["cells"], list) else REGISTRY["cells"]
    cj = {"revision": REVISION, "page": f"assets/pages/{SLUG}.png", "page_sha256": sha(page_path),
          "registry_sha256": sha(SW / "grid" / "registry.json"), "exposure_sha256": sha(SW / "puppets" / "exposure.json"),
          "film_script_sha256": sha(__file__), "routes": {k: "".join(v) for k, v in ROUTES.items()},
          "composite_order": "U1 ground -> U3 stencil -> U2 puppets/props (page pose) -> U1 lettering (tail = puppets.mouth_anchor) -> U1 borders/tab",
          "cells": {}}
    for c in CELLS:
        x0, y0 = G.cell_origin(c)
        im = page.crop((x0, y0, x0 + CW, y0 + CH))
        p = cells_dir / f"{c}.png"
        im.save(p, optimize=True)
        rc = reg_cells.get(c, {})
        cj["cells"][c] = {
            "row": G.cell_rc(c)[0], "col": G.cell_rc(c)[1], "page_origin": [x0, y0],
            "lettering": rc.get("lettering", rc.get("text")), "props": rc.get("props"), "cue": f"cue_{c}.wav",
            "cue_sha256": sha(FORAGE / f"cue_{c}.wav"), "outgoing_cues": rc.get("outgoing_cues"),
            "balloon_tail_to": tail(c), "exposure_sheet": P.sheet(c), "page_drawing": P.sheet(c)[-1],
            "stencil": f"stencil_{c}.png" if _stencil(c) is not None else None,
            "film_windows_s": {o[0]: [o[3] / FPS, o[3] / FPS + PER] for o in OCC if o[2] == c},
            "png": f"films/swarm/{SLUG}/cells/{c}.png", "sha256": sha(p), "revision": REVISION}
    json.dump(cj, open(cells_dir / "cells.json", "w"), indent=1)
    for route in ROUTES:
        sp = pages / f"{SLUG}-{route}.png"
        strip(route, page).save(sp, optimize=True)
        print("strip ->", sp)


# ---------------------------------------------------------------------- film ---
if CUT:
    film = Film(f"{SLUG}-{CUT}-only", seconds=CUT_SEGMENTS[CUT][-1][1], size=(FW, FH), fps=FPS, boil=0, seed=95)
    film.poster_at = 16.5 if CUT == "across" else 15.5      # E in each cut
else:
    film = Film(SLUG, seconds=SECONDS, size=(FW, FH), fps=FPS, boil=0, seed=95)
    film.poster_at = 44.5


@film.picture
def picture(t, ink):
    ink.paper(grain=False)                # no added grain: the paper is the real scan
    ink.img.paste(frame_rgb(master_K(int(round(t * FPS)))))


film.sound(sound)

if __name__ == "__main__":
    if not CUT and not (len(sys.argv) > 1 and sys.argv[1] == "--stills"):
        write_products()
    try:
        film.render(out_dir=_out(SW / "readers" if CUT else PROJECT / "assets" / "films"))
    except ValueError:        # kit prints the path relative to the project; staged output is outside it
        print("wrote (staged)", _out(PROJECT / "assets" / "films" / f"{SLUG}.mp4"))
