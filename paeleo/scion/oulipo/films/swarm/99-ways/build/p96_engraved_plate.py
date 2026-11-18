"""Page 96 Engraved plate (medium and material; medium: engraving-puppet).

The page is a catalogue plate, PLATE XCVI, inside a plate-mark: the figures and objects of the incident laid out as
numbered specimens, Fig. 1 to Fig. 10, in the order the afternoon used them, with a lettered key beneath that names
each figure and carries the four canon lines verbatim ('Fig. 3. The stranger at the ticket window: ...'). No balloon.
Figures: page 03's ENGRAVING PUPPETS (kit/build_page03: the AGENT is the Harper's Weekly 1863 telegraph operator,
LoC cph.3c11072, cut at the joints and pinned; the STRANGER the hatted woman of the 1867 Steinway Hall engraving,
LoC cph.3c32079; his table and the window from the 1863 plate), the stranger seen through the window glass as on
page 49 (build/p49_epic.window_board); the set (memo, clock, cupboard, brass key and tag, SERVICE door) drawn in the
shared pen line with HANDMADE engraver's hatching (parallel pen strokes clipped to each surface), on the LoC 1934 sheet.
Run: python3 -I p96_engraved_plate.py [beats]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import build_page03 as b3  # noqa: E402
import p49_epic as p49  # noqa: E402
from b1m2 import save_page, save_beats, letter_left, blit_mask  # noqa: E402

N, PID, TITLE = 96, "engraved-plate", "Engraved plate"
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, letters, Mof, lay = b3.pen, b3.letters, b3.Mof, b3.lay
INK = penlib.INK
PLATE = (150, 140, 2050, 2715)          # the plate-mark
SHEET = pen99.sheet99()
# repair: soften the sheet's finest fibre (keep its tone and mottling) so the plate encodes under 1.2 MB at q90
SHEET = 0.4 * SHEET + 0.6 * cv2.GaussianBlur(SHEET.astype(np.float32), (0, 0), 1.8)
BASE = [None]            # the region's paper before a figure is drawn (for knocked-out highlights)

KEY = [
    ("1", "The memo on his desk: '4:15 - open SERVICE door. Key in cupboard.'"),
    ("2", "The agent, risen from the desk, setting off for the cupboard."),
    ("3", "The stranger at the ticket window: \"Pardon me — have you the right time?\""),
    ("4", "The office wall clock, at ten past four."),
    ("5", "The agent, looking up at it: \"Ten past four, by the clock.\""),
    ("6", "The stranger, leaving the window: \"Much obliged!\""),
    ("7", "The cupboard, its door opened on the left jamb."),
    ("8", "The brass key on its hook, tagged SERVICE (enlarged)."),
    ("9", "The agent before the open cupboard, pencil to chin: \"Well, here I am... and what for?\""),
    ("10", "The SERVICE door, which stays closed; the key stays on its hook."),
]
EVENT = {"1": "E0", "2": "E0", "3": "E1", "4": "E2", "5": "E2", "6": "E3", "7": "E4", "8": "E4", "9": "E5", "10": "E5"}


# ------------------------------------------------------------------ handmade engraver's hatching
def hatch(canvas, poly, spacing=9, deg=45, w=1.6, seed=0, cross=False, exclude=None):
    """parallel pen strokes clipped to a polygon (each stroke the shared pen's brush_line, with tremor)"""
    h, wd = canvas.shape[:2]
    clip = np.zeros((h, wd), np.uint8)
    cv2.fillPoly(clip, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
    m = np.zeros((h, wd), np.uint8)
    P = np.array(poly, float)
    cx, cy = P.mean(0)
    R = np.linalg.norm(P - (cx, cy), axis=1).max() + 4
    for dd in ([deg, deg + 90] if cross else [deg]):
        a = math.radians(dd)
        u, n = np.array([math.cos(a), math.sin(a)]), np.array([-math.sin(a), math.cos(a)])
        for i, t in enumerate(np.arange(-R, R, spacing)):
            p0 = np.array([cx, cy]) + n * t - u * R
            p1 = np.array([cx, cy]) + n * t + u * R
            penlib.brush_line(m, [tuple(p0), tuple(p1)], w, seed + i + int(dd), tremor=0.35)
    if exclude is not None:
        clip = (clip.astype(np.float32) * (1 - exclude / 255.0)).astype(np.uint8)
    m = (m.astype(np.float32) * clip / 255).astype(np.uint8)
    penlib.ink_onto(canvas, m)


# ------------------------------------------------------------------ the figures (each drawn into its own region)
def fig_label(pg, n, cx, y):
    m = pen99.letter([f"Fig. {n}."], 32, 9600 + int(n), weight=0.14)
    b3_ink(pg, m, cx - m.shape[1] / 2, y)


def b3_ink(pg, m, x, y, colour=INK):
    x, y = int(x), int(y)
    sub = np.zeros(pg.shape[:2], np.uint8)
    blit_mask(sub, m, x, y)
    penlib.ink_onto(pg, sub, colour)


def region(pg, x0, y0, x1, y1):
    return pg[y0:y1, x0:x1]


def fig_memo(c):
    """Fig. 1: the memo slip, enlarged, with a little hatched cast shadow"""
    h, w = c.shape[:2]
    hatch(c, [(70, 80), (w - 40, 74), (w - 30, h - 40), (78, h - 34)], 10, 45, 1.4, 9610)
    b3.memo(c, w / 2 - 10, h / 2 - 10, 1.05, 9611, deg=-3)


def fig_agent_rising(c, P):
    h, w = c.shape[:2]
    gy = h - 20
    lay(c, P["table"], Mof(0.46, 0, np.array([250, 980]) * OPS, (150, gy)))
    b3.memo(c, 105, gy - 300, 0.45, 9620, deg=-4)
    b3.agent(c, P, (390, gy), 0.42, arms=(12, 0, -8), flip=True, head=4)
    pen(c, [(20, gy), (w - 20, gy)], 2, 9621)
    hatch(c, [(20, gy + 2), (w - 20, gy + 2), (w - 40, gy + 16), (40, gy + 16)], 9, 0, 1.2, 9622)


def fig_window(c, P, k=1.32):
    """Fig. 3: the window from the 1863 plate, the stranger behind its glass (page 49's treatment), drawn on a
    small board and laid in enlarged"""
    h, w = c.shape[:2]
    sh, sw = int(h / k), int(w / k)
    t = cv2.resize(BASE[0], (sw, sh), interpolation=cv2.INTER_AREA)
    p49.window_board(t, P, sw // 2, 9630, woman=dict(flip=True, shift=0.10))
    big = cv2.resize(t, (w, h), interpolation=cv2.INTER_CUBIC)
    c[:] = big


def fig_clock(c):
    h, w = c.shape[:2]
    cx, cy, r = w / 2, 150, 92
    case = [(cx - r * 1.3, cy - r * 1.3), (cx + r * 1.3, cy - r * 1.3), (cx + r * 1.3, cy + r * 1.2), (cx + r * 0.8, cy + r * 3.0),
            (cx - r * 0.8, cy + r * 3.0), (cx - r * 1.3, cy + r * 1.2)]
    pen(c, case, 4, 9640, closed=True)
    hatch(c, case, 11, 60, 1.5, 9641)
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(m, (int(cx), int(cy)), int(r * 1.12), 255, -1, cv2.LINE_AA)
    cv2.rectangle(m, (int(cx - r * .5), int(cy + r * 1.35)), (int(cx + r * .5), int(cy + r * 2.75)), 255, -1)
    c[:] = c * (1 - m[..., None] / 255) + BASE[0] * (m[..., None] / 255)
    b3.clock(c, cx, cy, r, 4, 10, 9642)
    for k in range(60):
        if k % 5:
            a = math.radians(k * 6)
            pen(c, [(cx + math.sin(a) * r * .92, cy - math.cos(a) * r * .92), (cx + math.sin(a) * r * .97, cy - math.cos(a) * r * .97)], 1.5, 9650 + k)


def fig_agent_answer(c, P):
    h, w = c.shape[:2]
    gy = h - 20
    b3.agent(c, P, (w / 2 - 10, gy), 0.42, arms=(-112, 10, 0), head=-16, flip=False)
    pen(c, [(30, gy), (w - 30, gy)], 2, 9660)
    hatch(c, [(30, gy + 2), (w - 30, gy + 2), (w - 50, gy + 16), (50, gy + 16)], 9, 0, 1.2, 9661)


def fig_woman_leaving(c, P):
    h, w = c.shape[:2]
    gy = h - 20
    b3.woman(c, P, (w / 2, gy), 0.62, flip=True)
    pen(c, [(40, gy), (w - 40, gy)], 2, 9670)
    hatch(c, [(40, gy + 2), (w - 40, gy + 2), (w - 60, gy + 16), (60, gy + 16)], 9, 0, 1.2, 9671)


def fig_cupboard(c):
    """Fig. 7: the cupboard, open on its left jamb, the interior hatched dark, the key on its hook"""
    h, w = c.shape[:2]
    x0, y0, x1, y1 = 150, 40, w - 40, h - 30
    kx, ky = (x0 + x1) / 2, y0 + 40
    ex = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(ex, (int(kx), int(ky + 29)), 24, 255, -1)
    cv2.rectangle(ex, (int(kx - 10), int(ky - 8)), (int(kx + 24), int(ky + 110)), 255, -1)
    cv2.rectangle(ex, (int(kx + 18), int(ky + 46)), (int(kx + 98), int(ky + 86)), 255, -1)
    ex = cv2.GaussianBlur(ex, (0, 0), 2)
    hatch(c, [(x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x1 - 6, y1 - 6), (x0 + 6, y1 - 6)], 8, 45, 1.8, 9680, cross=False, exclude=ex)
    for i, yy in enumerate(np.linspace(y0 + 90, y1 - 50, 3)):          # shelves, left in light
        m = np.zeros(c.shape[:2], np.uint8)
        cv2.rectangle(m, (x0 + 6, int(yy)), (x1 - 6, int(yy + 14)), 255, -1)
        c[:] = c * (1 - m[..., None] / 255) + BASE[0] * (m[..., None] / 255)
        pen(c, [(x0 + 6, yy), (x1 - 6, yy)], 2, 9681 + i)
        pen(c, [(x0 + 6, yy + 14), (x1 - 6, yy + 14)], 2, 9684 + i)
    pen(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 5, 9690, closed=True)
    leaf = [(x0, y0), (x0 - 120, y0 - 26), (x0 - 120, y1 + 26), (x0, y1)]
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(leaf) * 4)], 255, cv2.LINE_AA, shift=2)
    c[:] = c * (1 - m[..., None] / 255) + BASE[0] * (m[..., None] / 255)
    pen(c, leaf, 5, 9691, closed=True)
    hatch(c, leaf, 12, 90, 1.4, 9692)
    # the key on its hook, left light against the dark interior (Fig. 8 shows it enlarged)
    b3.key(c, kx, ky, 1.1, 9693)
    return (kx + 40, ky + 70)


def fig_key(c):
    """Fig. 8: the brass key, enlarged, on its hook with its paper tag lettered SERVICE"""
    h, w = c.shape[:2]
    x, y, s = w / 2 - 60, 40, 3.2
    pen(c, [(x - 30, y), (x + 30, y)], 5, 9700)
    pen(c, [(x, y), (x, y + 14 * s)], 5, 9701)
    bow = b3.circle_pts(x, y + 26 * s, 12 * s, 40)
    pen(c, bow, 5, 9702, closed=True)
    pen(c, b3.circle_pts(x, y + 26 * s, 6 * s, 30), 3, 9703, closed=True)
    hatch(c, [(x - 12 * s, y + 14 * s), (x + 12 * s, y + 14 * s), (x + 12 * s, y + 38 * s), (x - 12 * s, y + 38 * s)], 6, 30, 1.2, 9704)
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(m, (int(x), int(y + 26 * s)), int(6 * s), 255, -1, cv2.LINE_AA)
    c[:] = c * (1 - m[..., None] / 255) + BASE[0] * (m[..., None] / 255)
    pen(c, b3.circle_pts(x, y + 26 * s, 6 * s, 30), 3, 9705, closed=True)
    shank = [(x - 3 * s, y + 38 * s), (x + 3 * s, y + 38 * s), (x + 3 * s, y + 92 * s), (x - 3 * s, y + 92 * s)]
    pen(c, shank, 4, 9706, closed=True)
    hatch(c, shank, 5, 0, 1.1, 9707)
    bit = [(x + 3 * s, y + 76 * s), (x + 14 * s, y + 76 * s), (x + 14 * s, y + 82 * s), (x + 9 * s, y + 82 * s), (x + 9 * s, y + 86 * s),
           (x + 14 * s, y + 86 * s), (x + 14 * s, y + 92 * s), (x + 3 * s, y + 92 * s)]
    pen(c, bit, 4, 9708, closed=True)
    hatch(c, bit, 5, 0, 1.1, 9709)
    pen(c, [(x + 4 * s, y + 30 * s), (x + 30 * s, y + 52 * s)], 2.5, 9710)
    tag = [(x + 24 * s, y + 46 * s), (x + 80 * s, y + 49 * s), (x + 79 * s, y + 70 * s), (x + 23 * s, y + 67 * s)]
    pen(c, tag, 3, 9711, closed=True)
    pen(c, b3.circle_pts(x + 28 * s, y + 52 * s, 2.5 * s, 14), 2, 9712, closed=True)
    letters(c, ["SERVICE"], 8.5 * s, x + 51 * s, y + 58 * s, 9713)


def fig_agent_chin(c, P):
    h, w = c.shape[:2]
    gy = h - 20
    hnd = b3.agent(c, P, (w / 2 + 10, gy), 0.42, arms=(47, 132, 0), head=-6, flip=True)
    pen(c, [(hnd[0] + 2, hnd[1] + 4), (hnd[0] - 8, hnd[1] - 46)], 6, 9720)
    pen(c, [(20, gy), (w - 20, gy)], 2, 9721)
    hatch(c, [(20, gy + 2), (w - 20, gy + 2), (w - 40, gy + 16), (40, gy + 16)], 6, 0, 1.2, 9722)


def fig_door(c):
    h, w = c.shape[:2]
    x0, y0, x1, y1 = 40, 30, w - 40, h - 20
    pen(c, [(x0, y1), (x0, y0), (x1, y0), (x1, y1)], 5, 9730)
    for i, (a, b) in enumerate(((0.30, 0.55), (0.62, 0.92))):
        pnl = [(x0 + 30, y0 + (y1 - y0) * a), (x1 - 30, y0 + (y1 - y0) * a), (x1 - 30, y0 + (y1 - y0) * b), (x0 + 30, y0 + (y1 - y0) * b)]
        pen(c, pnl, 3, 9731 + i, closed=True)
        hatch(c, [(px + (6 if k in (0, 3) else -6), py + (6 if k < 2 else -6)) for k, (px, py) in enumerate(pnl)], 10, 70, 1.3, 9733 + i)
    hatch(c, [(x0 + 4, y0 + 4), (x0 + 24, y0 + 4), (x0 + 24, y1), (x0 + 4, y1)], 5, 90, 1.2, 9736)
    pen(c, [(x1 - 26, (y0 + y1) / 2 + 20), (x1 - 14, (y0 + y1) / 2 + 20)], 6, 9737)
    cx = (x0 + x1) / 2
    pen(c, [(cx - 70, y0 + 40), (cx + 70, y0 + 40), (cx + 70, y0 + 86), (cx - 70, y0 + 86)], 3, 9738, closed=True)
    letters(c, ["SERVICE"], 26, cx, y0 + 63, 9739)


# ------------------------------------------------------------------ the plate
# (n, x0, y0, x1, y1, label_y)
FIGS = [
    ("1", 200, 470, 690, 860, 940),
    ("2", 740, 400, 1320, 920, 940),
    ("3", 1380, 400, 2010, 920, 940),
    ("4", 250, 1000, 650, 1500, 1540),
    ("5", 720, 1000, 1290, 1520, 1540),
    ("6", 1420, 1000, 1960, 1520, 1540),
    ("7", 200, 1610, 740, 2080, 2095),
    ("8", 780, 1630, 1170, 2010, 2095),
    ("9", 1190, 1560, 1660, 2080, 2095),
    ("10", 1710, 1610, 1990, 2080, 2095),
]

def plate_mark(pg):
    x0, y0, x1, y1 = PLATE
    m = np.zeros((H, W), np.float32)
    m[y0:y1, x0:x1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    pg[:] = pg * (1 - 0.06 * m[..., None]) + hexc("#d9cdb0") * (0.06 * m[..., None])      # the plate's faint tone
    edge = np.zeros((H, W), np.uint8)
    cv2.rectangle(edge, (x0, y0), (x1, y1), 255, 3, cv2.LINE_AA)
    dark = cv2.GaussianBlur(edge, (0, 0), 1.5).astype(np.float32) / 255
    lite = np.roll(np.roll(dark, 3, 0), 3, 1)
    pg[:] = pg * (1 - 0.30 * dark[..., None]) + 255 * (0.18 * lite[..., None]) + pg * (-0.18 * lite[..., None])   # embossed edge
    for ins, wd in ((40, 5), (52, 2)):
        pts = [(x0 + ins, y0 + ins), (x1 - ins, y0 + ins), (x1 - ins, y1 - ins), (x0 + ins, y1 - ins), (x0 + ins, y0 + ins)]
        mm = np.zeros((H, W), np.uint8)
        penlib.brush_line(mm, pts, wd, 9740 + ins, tremor=0.25)
        penlib.ink_onto(pg, mm)


def header(pg):
    m = pen99.letter(["PLATE XCVI."], 40, 9750, weight=0.15)
    b3_ink(pg, m, PLATE[2] - 80 - m.shape[1], PLATE[1] + 64)
    m = pen99.letter(["RANDOLPH STATION, VT. - THE TICKET OFFICE, SEPT. 1937"], 46, 9751, weight=0.15)
    b3_ink(pg, m, W / 2 - m.shape[1] / 2, PLATE[1] + 112)
    m = pen99.letter(["The figures of the afternoon, numbered in the order of their use."], 32, 9752)
    b3_ink(pg, m, W / 2 - m.shape[1] / 2, PLATE[1] + 182)


def key_block(pg, upto=10):
    x0, y0 = PLATE[0] + 90, 2200
    m = pen99.letter(["KEY TO THE FIGURES"], 34, 9760, weight=0.15)
    b3_ink(pg, m, W / 2 - m.shape[1] / 2, y0 - 20)
    colw = 860
    for i, (n, text) in enumerate(KEY[:upto]):
        col, row = i // 5, i % 5
        lines = p49.B.wrap(f"Fig. {n}. {text}", KCAP, colw - 40)
        mk = letter_left(lines, KCAP, 9770 + i)
        yy = y0 + 40 + sum(KEYH[:row]) if col == 0 else y0 + 40 + sum(KEYH2[:row])
        b3_ink(pg, mk, x0 + col * (colw + 20), yy)


def _key_heights():
    hs = []
    for n, text in KEY:
        lines = p49.B.wrap(f"Fig. {n}. {text}", KCAP, 860 - 40)
        hs.append(int(KCAP * 1.42) * len(lines) + 14)
    return hs[:5], hs[5:]


KCAP = 28
KEYH, KEYH2 = _key_heights()


def build(upto=10, key_upto=None):
    key_upto = upto if key_upto is None else key_upto
    P = b3.load_puppets()
    pg = SHEET.copy()
    plate_mark(pg)
    header(pg)
    for (n, x0, y0, x1, y1, ly) in FIGS[:upto]:
        c = region(pg, x0, y0, x1, y1)
        BASE[0] = c.copy()
        {"1": lambda: fig_memo(c), "2": lambda: fig_agent_rising(c, P), "3": lambda: fig_window(c, P),
         "4": lambda: fig_clock(c), "5": lambda: fig_agent_answer(c, P), "6": lambda: fig_woman_leaving(c, P),
         "7": lambda: fig_cupboard(c), "8": lambda: fig_key(c), "9": lambda: fig_agent_chin(c, P),
         "10": lambda: fig_door(c)}[n]()
        fig_label(pg, n, (x0 + x1) / 2, ly)
    key_block(pg, key_upto)
    return pg


def _fol(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


def beats():
    return [cv2.resize(_fol(build(n, k)), (960, 1242), interpolation=cv2.INTER_AREA) for n, k in
            ((0, 0), (2, 2), (4, 4), (6, 6), (8, 8), (10, 10))]


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        print("beats", save_beats(N, beats()))
