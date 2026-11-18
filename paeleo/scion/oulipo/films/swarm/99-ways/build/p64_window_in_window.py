"""Page 64 Window in a window (layout and page grammar; medium: cut-paper).

Six cut-paper panels, each pasted INSIDE the one before, flush to its lower right, so every panel shows only an
inverted L of itself (a top strip and a left column) round the next: the station front (E0, the agent at his desk
through the office window, the stranger on the platform) > the ticket window from the platform (E1) > the office
under the clock (E2) > the emptied window from inside (E3) > the open cupboard (E4, E5) > the brass key on its hook,
the innermost panel. Each card throws its one paper shadow on the card it sits in; each carries a hand-ruled border.
HANDMADE cut paper: films/swarm/99-ways/kit/cutpaper99.py (scissor facets, LoC 1934 sheet fibre as relative tone,
one down-right paper shadow); the agent figure is page 02's cut-paper agent (kit/build_page02.agent), imported.
Run: python3 -I p64_window_in_window.py
"""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, rect, ellipse, hexc  # noqa: E402
import build_page02 as p02  # noqa: E402
from b1m2 import save_page, save_beats, write_record, credit_pages  # noqa: E402

N, PID, TITLE = 64, "window-in-window", "Window in a window"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
W, H = pen99.PAGE_W, pen99.PAGE_H
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
BCAP = 44

# nesting: each panel sits flush in the lower right of the last, leaving its top strip and left column
TOPS = [560, 330, 320, 310, 300]
COLS = [300, 250, 240, 240, 250]
GAP = 50                       # the strip of the outer panel left showing on the right and below
BOXES = [(110, 110, 2090, 2730)]
for t, cw in zip(TOPS, COLS):
    x0, y0, x1, y1 = BOXES[-1]
    BOXES.append((x0 + cw, y0 + t, x1 - GAP, y1 - GAP))

SKY, SLATE, FASCIA, CLAP, CLAP2, TRIM = "#c9d5d3", "#3e4447", "#e9dfc4", "#c9a66b", "#b8945c", "#5b3d25"
PLATF, PLANK = "#8d7a62", "#75644f"
WALL, WAINS, RAIL, FLOOR = p02.WALL, p02.WAINS, p02.RAIL, p02.FLOOR
GLASS, WFRAME = p02.GLASS, p02.WFRAME
COAT, HAT, HATBAND, FACE2, SKIN2 = p02.COAT, p02.HAT, p02.HATBAND, p02.FACE2, p02.SKIN2
INTERIOR = "#efe3b8"
BRASS, BRASS2 = "#c9a13b", "#9c7a2c"
TAG = "#e9dcb6"


def size(k):
    x0, y0, x1, y1 = BOXES[k]
    return x1 - x0, y1 - y0


def inner_local(k):
    """the next panel's box in panel k's own coordinates"""
    X0, Y0 = BOXES[k][:2]
    x0, y0, x1, y1 = BOXES[k + 1]
    return x0 - X0, y0 - Y0, x1 - X0, y1 - Y0


def ink(c, lines, cap, at, seed, colour=None):
    return c.ink_letters(lines, cap, at, seed, colour)


def woman(c, x, yb, s, away=False):
    """The stranger in cut paper, full length (she is on the platform): cloche hat with band, coat, gloves, bag.
    x = centre, yb = feet, s = px per unit (figure ~ 8.2 units tall). away: walking off to the left, back turned."""
    P = lambda dx, dy: (x + dx * s, yb + dy * s)
    Ar = lambda pts: np.array([P(*p) for p in pts], np.float32)
    c.piece(Ar([(-0.42, -2.3), (-0.08, -2.3), (-0.12, -0.25), (-0.40, -0.25)]), "#c9b49a")          # stockings
    c.piece(Ar([(0.08, -2.3), (0.42, -2.3), (0.40, -0.25), (0.12, -0.25)]), "#c9b49a")
    c.piece(Ar([(-0.55, -0.32), (-0.08, -0.32), (-0.05, 0), (-0.62, 0)]), "#2a1f1a")                # shoes
    c.piece(Ar([(0.08, -0.32), (0.55, -0.32), (0.62, 0), (0.05, 0)]), "#2a1f1a")
    c.piece(Ar([(-0.95, -6.35), (-0.55, -6.75), (0.55, -6.75), (0.95, -6.35), (1.15, -2.2), (-1.15, -2.2)]), COAT)
    c.piece(Ar([(-0.55, -6.75), (0.0, -6.0), (0.55, -6.75), (0.35, -6.95), (-0.35, -6.95)]), "#3a474e")   # collar
    for k in range(3):
        c.piece(ellipse(*P(0.18 if not away else -0.18, -5.6 + k * 0.85), s * 0.08, s * 0.08), "#1f2427", shadow=False)
    # arms: the near one crooked, a bag on it
    sgn = -1 if away else 1
    c.limb(P(0.85 * sgn, -6.3), P(1.05 * sgn, -4.6), s * 0.5, s * 0.42, COAT)
    c.limb(P(1.05 * sgn, -4.6), P(0.55 * sgn, -3.9), s * 0.42, s * 0.36, COAT)
    c.piece(ellipse(*P(0.45 * sgn, -3.85), s * 0.2, s * 0.17), "#e6dccb")                             # glove
    c.piece(Ar([(0.7 * sgn, -4.2), (1.45 * sgn, -4.2), (1.5 * sgn, -3.4), (0.65 * sgn, -3.4)]), "#4a2c22")   # bag
    c.limb(P(-0.85 * sgn, -6.3), P(-0.95 * sgn, -3.5), s * 0.5, s * 0.4, COAT)
    c.piece(ellipse(*P(-0.95 * sgn, -3.35), s * 0.2, s * 0.17), "#e6dccb")
    hx, hy = P(0, -7.55)
    c.piece(Ar([(-0.22, -7.0), (0.22, -7.0), (0.2, -6.7), (-0.2, -6.7)]), SKIN2, shadow=False)        # neck
    if away:
        c.piece(ellipse(hx, hy, s * 0.48, s * 0.56), "#5a3a26")                                         # hair, from behind
    else:
        c.piece(ellipse(hx, hy, s * 0.46, s * 0.56), FACE2)
        c.piece(ellipse(hx - s * 0.36, hy - s * 0.12, s * 0.14, s * 0.26), "#5a3a26", shadow=False)    # hair under the brim
        for sx in (-1, 1):
            c.piece(ellipse(hx + sx * s * 0.17 - s * 0.06, hy - s * 0.02, s * 0.055, s * 0.045), "#2a1f1a", shadow=False)
        c.strip((hx - s * 0.16, hy + s * 0.3), (hx + s * 0.06, hy + s * 0.3), s * 0.06, "#9a3b34", shadow=False)
    c.piece(ellipse(hx, hy - s * 0.32, s * 0.78, s * 0.2), HAT)                                         # brim
    c.piece(np.vstack([ellipse(hx, hy - s * 0.38, s * 0.52, s * 0.55, 180, 360)]), HAT)                  # crown
    c.strip((hx - s * 0.5, hy - s * 0.47), (hx + s * 0.5, hy - s * 0.47), s * 0.11, HATBAND, shadow=False)
    c.piece(ellipse(hx + s * 0.42 * (-1 if away else 1), hy - s * 0.55, s * 0.17, s * 0.12), HATBAND)  # bow


def agent_bust(c, x, y, s, look=(0, 0)):
    """the agent seen through glass: page 02's cut-paper agent cropped by the window (feet far below)"""
    p02.agent(c, x, y + 7.65 * s, s, pose="stand", look=look, legs=False)


def frame_border(c, w, h, seed, wt=8):
    m = penlib.border_mask((h, w), [(4, 4, w - 5, h - 5)], wt, seed)
    penlib.ink_onto(c.img, m)


# ------------------------------------------------------------------ the six panels (each on its own card)
def panel1():                      # E0 station front: the agent at his desk through the window; the stranger arrives
    w, h = size(0)
    c = Cut(h, w, 6401, ground=SKY, fibre_off=(13, 7))
    # clapboard wall under the eaves
    c.piece(rect(-20, 200, w + 20, h + 20), CLAP, shadow=False)
    for y in range(230, h, 46):
        c.strip((-20, y), (w + 20, y + 2), 5, CLAP2, shadow=False, jitter=0.4)
    # the platform (left column foot) and its planks
    c.piece(rect(-20, h - 330, w + 20, h + 20), PLATF)
    for y in range(h - 300, h, 38):
        c.strip((-20, y), (w + 20, y + 1), 4, PLANK, shadow=False, jitter=0.4)
    c.piece(rect(-20, h - 344, w + 20, h - 318), "#5d4f3f")                                   # platform edge board
    # the roof: slate, broad eaves, fascia board with the station name cut in dark paper
    c.piece(np.float32([(-30, 30), (w + 30, 0), (w + 30, 150), (-30, 170)]), SLATE)
    for y in (60, 95, 130):
        c.strip((-30, y + 18), (w + 30, y - 10), 4, "#2f3437", shadow=False)
    c.piece(rect(-30, 160, w + 30, 236), FASCIA)
    c.cut_letters(["RANDOLPH"], 54, (w * 0.47, 200), "#2b2622", 6402)
    for bx in range(70, w, 330):                                                               # eave brackets
        c.piece(np.float32([(bx, 236), (bx + 34, 236), (bx + 34, 330), (bx + 6, 262)]), TRIM)
    # the office window (top strip): through the glass, the agent at his desk with the memo
    wx0, wy0, wx1 = 380, 300, 980
    c.piece(rect(wx0 - 26, wy0 - 26, wx1 + 26, 640), TRIM)
    c.piece(rect(wx0, wy0, wx1, 640), INTERIOR, shadow=False)
    agent_bust(c, 640, 330, 34, look=(0, 1))
    c.piece(rect(wx0, 500, wx1, 640), "#5a3b24")                                               # desk top edge
    memo = np.float32([(470, 444), (700, 432), (706, 520), (476, 532)])
    c.piece(memo, "#f6f0dc", opacity=0.3)
    ink(c, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 22, (588, 482), 6403)
    c.strip((wx0, 420), (wx1, 420), 8, TRIM, shadow=False)                                    # sash bar
    c.strip(((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, 420), 8, TRIM, shadow=False)
    # second window (to the right: the ticket office, where the next panel is pasted)
    c.piece(rect(1180, 300, 1760, 640), TRIM)
    c.piece(rect(1206, 326, 1734, 640), GLASS, shadow=False)
    # left column: a lamp post and the stranger coming along the platform toward the ticket window
    c.piece(rect(36, 560, 52, h - 330), "#2b2622")
    c.piece(np.float32([(14, 520), (74, 520), (62, 572), (26, 572)]), "#2b2622")
    c.piece(ellipse(44, 540, 16, 14), "#f3e2a0", shadow=False)
    woman(c, 165, h - 360, 74)
    frame_border(c, w, h, 6409, 10)
    return c


def panel2():                      # E1 the ticket window from the platform: her question
    w, h = size(1)
    c = Cut(h, w, 6411, ground=CLAP, fibre_off=(211, 97))
    for y in range(40, h, 46):
        c.strip((-20, y), (w + 20, y + 2), 5, CLAP2, shadow=False, jitter=0.4)
    c.piece(rect(-20, h - 300, w + 20, h + 20), PLATF)
    for y in range(h - 270, h, 38):
        c.strip((-20, y), (w + 20, y + 1), 4, PLANK, shadow=False, jitter=0.4)
    # the window: header board lettered, glass, agent behind it
    c.piece(rect(170, 20, w + 30, 140), "#4a3220")
    c.cut_letters(["TICKET OFFICE"], 52, (680, 82), "#efe0b0", 6412)
    c.piece(rect(170, 140, w + 30, h - 380), WFRAME)
    c.piece(rect(200, 166, w + 30, h - 410), GLASS, shadow=False)
    agent_bust(c, 780, 198, 64, look=(-1, 0))
    c.strip((200, 330), (w + 30, 330), 10, WFRAME)
    woman(c, 150, h - 330, 128)
    c.balloon(Q, BCAP, (360, 236), (205, 640), 6413)
    frame_border(c, w, h, 6419, 9)
    return c


def panel3():                      # E2 inside: he looks up to the clock, 4:10, and answers
    w, h = size(2)
    c = Cut(h, w, 6421, ground=WALL, fibre_off=(401, 151))
    c.piece(rect(-20, 820, w + 20, 1180), WAINS, shadow=False)
    c.strip((-20, 820), (w + 20, 820), 22, RAIL)
    c.piece(rect(-20, 1160, w + 20, h + 20), FLOOR)
    p02.clock(c, w, h, 880, 140, 86, 4, 10)
    p02.agent(c, 125, 1260, 70, pose="stand", look=(0.6, -1))
    c.balloon(A, BCAP, (330, 190), (165, 720), 6423)
    frame_border(c, w, h, 6429, 9)
    return c


def panel4():                      # E3 the window from inside: she thanks him and goes, back turned
    w, h = size(3)
    c = Cut(h, w, 6431, ground=WALL, fibre_off=(611, 301))
    c.piece(rect(-20, 760, w + 20, 1060), WAINS, shadow=False)
    c.strip((-20, 760), (w + 20, 760), 20, RAIL)
    c.piece(rect(-20, 1040, w + 20, h + 20), FLOOR)
    # ticket window (left column), from inside: her back through the glass, going
    c.piece(rect(-20, 240, 230, 760), WFRAME)
    c.piece(rect(-20, 266, 204, 730), GLASS, shadow=False)
    woman(c, 70, 1160, 62, away=True)
    c.piece(rect(-20, 730, 240, 780), "#4a3220")                                              # counter
    c.strip((-20, 470), (204, 470), 9, WFRAME)
    # the cupboard's cornice, ahead (where the next panel sits)
    c.piece(rect(400, 230, 880, 300), "#4a2f1d")
    c.piece(rect(420, 300, 860, h + 20), "#5a3a24")
    c.balloon(T, BCAP, (260, 140), (95, 560), 6433)
    frame_border(c, w, h, 6439, 8)
    return c


def panel5():                      # E4/E5 the open cupboard: he stands at it, pencil to chin
    w, h = size(4)
    c = Cut(h, w, 6441, ground=WALL, fibre_off=(801, 411))
    c.piece(rect(-20, 600, w + 20, 840), WAINS, shadow=False)
    c.strip((-20, 600), (w + 20, 600), 18, RAIL)
    c.piece(rect(-20, 820, w + 20, h + 20), FLOOR)
    # the SERVICE door beside the cupboard, shut (its head and card in the top strip, far right)
    c.piece(rect(560, 150, w + 30, h - 60), p02.DOOR)
    c.piece(rect(586, 190, w - 10, 250), "#f3ecd8")
    ink(c, ["SERVICE"], 30, (650, 220), 6442)
    # cupboard case and its leaf swung open on the left jamb, toward us
    c.piece(rect(236, 230, 560, h - 80), "#4a2f1d")
    p02.agent(c, 100, 900, 56, pose="chin", look=(0.5, 0))
    leaf = np.float32([(250, 300), (196, 262), (196, h - 70), (250, h - 110)])
    c.piece(leaf, "#3a2618")
    c.piece(ellipse(206, 560, 6, 6), BRASS, shadow=False)
    c.balloon(F, BCAP - 4, (380, 150), (140, 470), 6443)
    frame_border(c, w, h, 6449, 8)
    return c


def panel6():                      # the innermost: the brass key on its hook, tagged SERVICE; it stays
    w, h = size(5)
    c = Cut(h, w, 6451, ground="#2f2218", fibre_off=(1001, 601))
    c.piece(rect(-20, 120, w + 20, 140), "#5a3d28")                                           # shelf above
    c.piece(rect(-20, h - 90, w + 20, h - 70), "#5a3d28")                                     # shelf below
    kx, ky = w * 0.50, 190
    c.piece(np.float32([(kx - 6, ky - 22), (kx + 6, ky - 22), (kx + 6, ky + 26), (kx - 6, ky + 26)]), "#8a8478")   # hook plate
    c.strip((kx, ky + 16), (kx + 18, ky + 40), 7, "#8a8478")                                  # hook
    # the key: bow ring, shank, bit (cut brass paper)
    bow = ellipse(kx + 18, ky + 80, 38, 38)
    c.piece(bow, BRASS, holes=[ellipse(kx + 18, ky + 80, 18, 18)])
    c.strip((kx + 18, ky + 116), (kx + 18, ky + 300), 18, BRASS)
    c.piece(rect(kx + 18, ky + 250, kx + 62, ky + 270), BRASS2)
    c.piece(rect(kx + 18, ky + 282, kx + 54, ky + 300), BRASS2)
    # string and paper tag lettered SERVICE
    c.strip((kx + 30, ky + 110), (kx + 80, ky + 170), 3, "#d8cfb8", shadow=False)
    tag = np.float32([(kx + 60, ky + 160), (kx + 190, ky + 175), (kx + 184, ky + 230), (kx + 54, ky + 214)])
    c.piece(tag, TAG)
    ink(c, ["SERVICE"], 26, (kx + 122, ky + 196), 6452)
    frame_border(c, w, h, 6459, 7)
    return c


PANELS = [panel1, panel2, panel3, panel4, panel5, panel6]
CACHE = {}


def build(n=6):
    pg = pen99.sheet99()
    for k in range(n):
        if k not in CACHE:
            CACHE[k] = PANELS[k]().u8().astype(np.float32)
        img = CACHE[k]
        x0, y0, x1, y1 = BOXES[k]
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(pg, m, off=9 if k else 7, blur=7, opacity=0.5)
        pg[y0:y1, x0:x1] = img
    return pg


if __name__ == "__main__":
    page = build()
    img, size_b = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_b, BOXES)
    frames = []
    for n in range(1, 7):
        p = img if n == 6 else np.clip(np.round(build(n)), 0, 255).astype(np.uint8)
        if n < 6:
            pen99.folio(p, N, TITLE)
        frames.append(p)
    save_beats(N, frames)
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, N)
    nest = all(BOXES[k][0] > BOXES[k - 1][0] and BOXES[k][1] > BOXES[k - 1][1] and BOXES[k][2] < BOXES[k - 1][2]
               and BOXES[k][3] < BOXES[k - 1][3] for k in range(1, 6))
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p64_window_in_window.py (cut paper: kit/cutpaper99.py; agent, clock, office papers: kit/build_page02.py)",
        "sources": src,
        "made": [
            "six HANDMADE cut-paper panel cards (cutpaper99.Cut: scissor-faceted flat papers, the LoC 1934 sheet's fibre as relative tone, one down-right paper shadow), each pasted inside the one before, flush to its lower right, so each shows an inverted L (top strip + left column) round the next and a 50 px strip on its right and foot",
            "P1 station front: slate roof, fascia with RANDOLPH cut in dark paper, eave brackets, clapboard, platform planks, lamp post; through the office window the agent at his desk with the memo slip (pen-lettered '4:15 - open SERVICE door. Key in cupboard.'); the stranger arriving along the platform",
            "P2 the ticket window from the platform: TICKET OFFICE cut through the header board, the agent behind the glass, the stranger at the window, her question",
            "P3 the office: page 02's cut-paper clock at 4:10 and the agent looking up to it, his answer",
            "P4 the window from inside: her back through the glass as she goes, her thanks; the cupboard's cornice ahead",
            "P5 the cupboard case with its leaf swung open on the left jamb; the agent, pencil to his chin, his line; the SERVICE door shut beside it, its card lettered",
            "P6 innermost: the brass key cut in brass paper on its hook, the paper tag lettered SERVICE",
            "the stranger as a new full-length cut-paper figure (cloche hat with band and bow, coat, gloves, bag); the agent is page 02's cut-paper agent, imported",
            "hand-ruled borders on every card (penlib.border_mask); the four canon lines in the shared cut-paper balloons (penlib.balloon_piece); folio '64 / Window in a window' (pen99.folio)"],
        "boxes": {f"P{k + 1}": list(b) for k, b in enumerate(BOXES)},
        "events": {"E0": "P1: through the station's office window, the agent at his desk over the memo; the stranger coming along the platform",
                   "E1": "P2: at the TICKET OFFICE window, 'Pardon me — have you the right time?'",
                   "E2": "P3: he looks up to the clock at 4:10: 'Ten past four, by the clock.'",
                   "E3": "P4: her back through the glass as she leaves: 'Much obliged!'",
                   "E4": "P5: the cupboard open on its left jamb; P6: the key on its hook in plain view, tagged SERVICE",
                   "E5": "P5: pencil to his chin, 'Well, here I am... and what for?'; the SERVICE door shut beside the cupboard; P6, the innermost frame, is the key that stays on its hook"},
        "lines": LN,
        "beat": "the closing in performed: the station front lies alone, then each smaller card is pasted into the lower right of the last, down to the key on its hook",
        "beat_frames": ["b01: P1 the station front alone"] + [f"b{n:02d}: P1-P{n} nested" for n in range(2, 7)],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size_b, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size_b <= 1200000,
                       "every_panel_strictly_inside_the_last": nest,
                       "innermost_panel": "P6, the key on its hook",
                       "check": C["check"],
                       "pending": "independent blind reading not run by the maker"},
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
