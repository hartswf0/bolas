"""Page 34 Thirty-two panels (reduction and expansion; medium: engraving-puppet).

Every micro-action drawn: thirty-two small storyboard panels in a 4 x 8 grid, numbered 1-32 on pinned slips.
The page-03 engraving puppets (Harper's 1863 telegraph operator as the AGENT, pinned at the joints; the 1867
Steinway Hall woman as the STRANGER; the engraved table and ticket window) with the HANDMADE pen set
(clock, memo, cupboard, key, SERVICE door) on the LoC 1934 sheet. The four canon lines verbatim in pen-hand
balloons. Beats: the board fills row by row (4 panels per frame, 8 frames).
Run: python3 -I p34_thirty_two.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import build_page03 as K3  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import b1m2  # noqa: E402

N, PID, TITLE = 34, "thirty-two", "Thirty-two panels"
W, H = pen99.PAGE_W, pen99.PAGE_H
LN = {k: v["text"] for k, v in K3.CANON["incident"]["lines"].items()}
CARD, SLIPC, GRAPH = K3.CARD, K3.SLIPC, K3.GRAPH

COLS, ROWS = 4, 8
GX, GY = 20, 22
PW = (1980 - (COLS - 1) * GX) // COLS          # 480
PH = (2620 - (ROWS - 1) * GY) // ROWS          # 308
OPS = K3.OPS
HEAD_C = np.array([596 + 113, 147 + 93], np.float32)
WIN_ABOUT = np.array([140, 280]) * OPS
TABLE_FOOT = np.array([250, 980]) * OPS

S = 0.205          # agent full-figure scale
SW = 0.27          # woman scale

# what each panel shows (for the record)
BEATS = [
    "E0 the memo, close: '4:15 - open SERVICE door. Key in cupboard.'",
    "E0 he stands at the desk, reading it; the clock at 4:09",
    "E0 he lifts his head from the memo",
    "E0 he turns from the desk",
    "E0 first step across the office",
    "E0 second step; the closed cupboard ahead",
    "E1 a voice from the window: 'Pardon me — have you the right time?'",
    "E1 he stops mid-step and turns his head",
    "E1 the stranger at the TICKET OFFICE glass, waiting",
    "E1 he turns to face her",
    "E2 he looks up at the wall clock",
    "E2 the clock, close: 4:10",
    "E2 he turns back to the window",
    "E2 'Ten past four, by the clock.'",
    "E3 she nods",
    "E3 'Much obliged!'",
    "E3 she turns from the glass",
    "E3 she has stepped out of frame; he still faces the glass",
    "E3 the empty window",
    "E3 he turns back toward the cupboard",
    "E4 a step",
    "E4 another step; the cupboard and the SERVICE door",
    "E4 his hand to the knob",
    "E4 the door half open",
    "E4 the door wide open on its left jamb",
    "E4 the key, close: on its hook, tagged SERVICE",
    "E5 he looks at the key",
    "E5 the pencil rises",
    "E5 the pencil at his chin",
    "E5 'Well, here I am... and what for?'",
    "E5 the key, close, still on its hook",
    "E5 the SERVICE door shut beside him; the clock at 4:11",
]
assert len(BEATS) == 32


def card(n):
    c = np.zeros((PH, PW, 3), np.float32) + CARD 
    return c


def balloon(c, lines, at, tip, seed, cap=24):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.28, bend=0.1)
    penlib.lay_balloon(c, b, at)


def head_close(c, P, to, s, deg=0, flip=False):
    """the agent's head and torso, close (the puppet laid big, cropped by the panel)"""
    return K3.agent(c, P, to, s, arms=(0, 0, 0), head=deg, flip=flip)


def window(c, x, y, sc, seed, letters=True):
    K3.lay(c, P_["window"], K3.Mof(sc, 0, WIN_ABOUT, (x, y)))
    if letters:
        K3.letters(c, ["TICKET", "OFFICE"], 15 * sc / 0.7, x, y + 95 * sc / 0.7, seed)


P_ = None


def panel(n, P):
    c = card(n)
    gy = PH - 24
    sd = 34000 + n * 50
    if n not in (1, 12, 26, 31):
        K3.ground_line(c, 0, PW, gy, sd)
    if n == 1:
        K3.memo(c, PW / 2, PH / 2 + 4, 1.12, sd + 1, deg=-3)
    elif n == 2:
        K3.lay(c, P["table"], K3.Mof(0.30, 0, TABLE_FOOT, (150, gy + 2)))
        K3.memo(c, 120, 140, 0.33, sd + 1, deg=-5)
        K3.agent(c, P, (285, gy + 2), S, arms=(28, 40, 0), head=10)
        K3.clock(c, 420, 52, 24, 4, 9, sd + 2)
    elif n == 3:
        K3.lay(c, P["table"], K3.Mof(0.30, 0, TABLE_FOOT, (150, gy + 2)))
        K3.memo(c, 120, 140, 0.33, sd + 1, deg=-5)
        K3.agent(c, P, (285, gy + 2), S, arms=(10, 20, 0), head=-6)
        K3.clock(c, 420, 52, 24, 4, 9, sd + 2)
    elif n == 4:
        K3.lay(c, P["table"], K3.Mof(0.30, 0, TABLE_FOOT, (130, gy + 2)))
        K3.memo(c, 100, 140, 0.33, sd + 1, deg=-5)
        K3.agent(c, P, (300, gy + 2), S, arms=(4, 0, -6), flip=True)
    elif n == 5:
        K3.lay(c, P["table"], K3.Mof(0.30, 0, TABLE_FOOT, (60, gy + 2)))
        K3.agent(c, P, (250, gy + 2), S, arms=(18, 0, -14), head=4, flip=True)
    elif n == 6:
        K3.cupboard(c, 330, 70, 440, gy - 10, 0.0, sd + 3)
        K3.agent(c, P, (190, gy + 2), S, arms=(-14, 0, 12), head=4, flip=True)
    elif n == 7:
        K3.cupboard(c, 330, 70, 440, gy - 10, 0.0, sd + 3)
        K3.agent(c, P, (250, gy + 2), S, arms=(10, 0, -10), flip=True)
        balloon(c, ["Pardon me —", "have you the", "right time?"], (110, 84), (-20, 40), sd + 5)
    elif n == 8:
        K3.cupboard(c, 330, 70, 440, gy - 10, 0.0, sd + 3)
        K3.agent(c, P, (250, gy + 2), S, arms=(0, 0, 0), head=12)
    elif n == 9:
        window(c, 210, 150, 0.95, sd + 6)
        K3.woman(c, P, (300, gy + 120), 0.42)
    elif n == 10:
        K3.agent(c, P, (140, gy + 2), S, arms=(6, 0, 0), flip=True)
        window(c, 330, 135, 0.62, sd + 6)
        K3.woman(c, P, (415, gy + 2), SW)
    elif n == 11:
        K3.clock(c, 70, 60, 30, 4, 10, sd + 2)
        K3.agent(c, P, (200, gy + 2), S, arms=(6, 0, 0), head=-18, flip=False)
        window(c, 360, 135, 0.62, sd + 6)
        K3.woman(c, P, (445, gy + 2), SW)
    elif n == 12:
        K3.clock(c, PW / 2, 95, 70, 4, 10, sd + 2)
    elif n == 13:
        K3.clock(c, 60, 60, 30, 4, 10, sd + 2)
        K3.agent(c, P, (200, gy + 2), S, arms=(6, 0, 0), head=-4, flip=True)
        window(c, 360, 135, 0.62, sd + 6)
        K3.woman(c, P, (445, gy + 2), SW)
    elif n == 14:
        K3.clock(c, 60, 60, 30, 4, 10, sd + 2)
        K3.agent(c, P, (190, gy + 2), S, arms=(60, 150, 0), head=-6, flip=True)
        window(c, 360, 135, 0.62, sd + 6)
        K3.woman(c, P, (445, gy + 2), SW)
        balloon(c, ["Ten past four,", "by the clock."], (130, 54), (175, 118), sd + 5)
    elif n == 15:
        K3.agent(c, P, (180, gy + 2), S, arms=(6, 0, 0), flip=True)
        window(c, 350, 135, 0.62, sd + 6)
        K3.woman(c, P, (440, gy + 4), SW, deg=-9)
    elif n == 16:
        K3.agent(c, P, (180, gy + 2), S, arms=(6, 0, 0), flip=True)
        window(c, 350, 135, 0.62, sd + 6)
        K3.woman(c, P, (440, gy + 2), SW)
        balloon(c, ["Much", "obliged!"], (300, 48), (420, 118), sd + 5)
    elif n == 17:
        K3.agent(c, P, (180, gy + 2), S, arms=(6, 0, 0), flip=True)
        window(c, 350, 135, 0.62, sd + 6)
        K3.woman(c, P, (470, gy + 2), SW, flip=True)
    elif n == 18:
        K3.agent(c, P, (180, gy + 2), S, arms=(6, 0, 0), flip=True)
        window(c, 350, 135, 0.62, sd + 6)
        K3.woman(c, P, (548, gy + 2), SW, flip=True)
    elif n == 19:
        window(c, 240, 150, 0.95, sd + 6)
    elif n == 20:
        K3.agent(c, P, (250, gy + 2), S, arms=(6, 0, 0))
        window(c, 410, 135, 0.62, sd + 6)
    elif n in (21, 22):
        K3.service_door(c, 380, 46, 470, gy, sd + 7) if n == 22 else None
        K3.cupboard(c, 250 if n == 22 else 330, 70, 360 if n == 22 else 440, gy - 10, 0.0, sd + 3)
        K3.agent(c, P, (120 if n == 21 else 130, gy + 2), S, arms=(18, 0, -14) if n == 21 else (-14, 0, 12), flip=True)
    elif n in (23, 24, 25):
        K3.service_door(c, 370, 46, 462, gy, sd + 7)
        K3.cupboard(c, 200, 70, 330, gy - 10, {23: 0.0, 24: 0.45, 25: 1.0}[n], sd + 3)
        arms = {23: (-70, 20, 0), 24: (-62, 30, 0), 25: (-30, 40, 0)}[n]
        K3.agent(c, P, (110 if n == 23 else 80, gy + 2), S, arms=arms, flip=True)
    elif n == 31:
        K3.key(c, 110, 46, 2.3, sd + 8)
        K3.pen(c, [(40, 20), (40, PH - 20)], 4, sd + 9)
        hd = K3.agent(c, P, (330, gy + 420), 0.50, arms=(47, 132, 0), head=-6, flip=True)
        K3.pen(c, [(hd[0] + 2, hd[1] + 5), (hd[0] - 8, hd[1] - 46)], 6, sd + 12)
    elif n == 26:
        K3.key(c, PW / 2 - 70, 46, 2.3, sd + 8)
        K3.pen(c, [(60, 20), (60, PH - 20)], 4, sd + 9)          # the cupboard's left jamb
        K3.pen(c, [(60, 250), (PW - 30, 250)], 3, sd + 10)        # a shelf
    elif n in (27, 28, 29, 30, 32):
        K3.service_door(c, 370, 46, 462, gy, sd + 7)
        K3.cupboard(c, 200, 70, 330, gy - 10, 1.0, sd + 3)
        arms = {27: (0, 0, 0), 28: (30, 80, 0), 29: (47, 132, 0), 30: (47, 132, 0), 32: (47, 132, 0)}[n]
        hd = K3.agent(c, P, (90, gy + 2), S, arms=arms, head=-6 if n != 27 else 6, flip=True)
        if n >= 28:
            K3.pen(c, [(hd[0] + 1, hd[1] + 3), (hd[0] - 4, hd[1] - 22)], 4, sd + 12)
        if n == 30:
            balloon(c, ["Well, here I am...", "and what for?"], (300, 44), (118, 64), sd + 5, cap=22)
        if n == 32:
            K3.clock(c, 165, 40, 20, 4, 11, sd + 2)
    return cv2.GaussianBlur(c, (0, 0), 0.6)    # print softness of the small boards (keeps the JPEG in budget)


def number_slip(pg, x, y, n):
    m = pen99.letter([str(n)], 24, 34900 + n, weight=0.15)
    cols = np.where(m.max(0) > 40)[0]
    rows = np.where(m.max(1) > 40)[0]
    m = m[max(0, rows[0] - 6):rows[-1] + 7, max(0, cols[0] - 8):cols[-1] + 9]
    h, w = m.shape
    pm = np.zeros(pg.shape[:2], np.uint8)
    cv2.rectangle(pm, (x, y), (x + w + 10, y + h + 4), 255, -1)
    penlib.shadow_onto(pg, pm, off=3, blur=2, opacity=0.3)
    pg[:] = pg * (1 - pm[..., None] / 255) + SLIPC * (pm[..., None] / 255)
    sub = np.zeros(pg.shape[:2], np.uint8)
    sub[y + 2:y + 2 + h, x + 5:x + 5 + w] = m
    penlib.ink_onto(pg, sub, K3.INK)


def box(n):
    r, k = (n - 1) // COLS, (n - 1) % COLS
    x0 = 110 + k * (PW + GX)
    y0 = 110 + r * (PH + GY)
    return x0, y0


CACHE = {}


def build(rows=ROWS):
    global P_
    if P_ is None:
        P_ = K3.load_puppets()
    pg = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.6)    # sheet grain softened (file size); fibre tone kept
    boxes = []
    for n in range(1, 33):
        x0, y0 = box(n)
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        if (n - 1) // COLS >= rows:
            continue
        if n not in CACHE:
            CACHE[n] = panel(n, P_)
        pg[y0:y0 + PH, x0:x0 + PW] = CACHE[n]
    bm = penlib.border_mask(pg.shape[:2], boxes, 6, 3401)
    penlib.ink_onto(pg, bm)
    for n in range(1, 33):
        if (n - 1) // COLS < rows:
            x0, y0 = box(n)
            number_slip(pg, x0 + PW - 50, y0 + PH - 40, n)
    pg = np.clip(np.round(pg), 0, 255).astype(np.uint8)
    pen99.folio(pg, N, TITLE)
    return pg


if __name__ == "__main__":
    page = build()
    im = Image.fromarray(page)
    im.save(b1m2.MASTERS / f"{N:02d}-{PID}.png", optimize=True)
    jp = b1m2.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    im.save(jp, quality=90, optimize=True, progressive=True)
    print("jpeg bytes", jp.stat().st_size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [build(k) for k in range(1, 9)]
        b1m2.save_beats(N, frames)
        print("beats", len(frames))
