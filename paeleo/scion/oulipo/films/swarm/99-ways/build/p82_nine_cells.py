"""Page 82 Nine cells (layout and page grammar; medium: shadow-puppet).

A strict 3x3 grid of nine identical cells (640 x 853 px, 30 px gutters), one beat or held pause per cell:
1 E0 at the desk, the memo | 2 E0 on his way | 3 E1 the question
4 E2 held pause: he looks up at the clock | 5 E2 the answer | 6 E3 the thanks
7 E3 held pause: the window empty, he goes on | 8 E4 the cupboard open | 9 E5 the forgetting.
Black cut-paper silhouette puppets (b1m2 figure model, HANDMADE) and cut set pieces on lamp-lit paper screens
(page 05/30 screen and puppet tools). Run: python3 -I p82_nine_cells.py [beats]
"""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p05_noir as p5
from p05_noir import sil, far, window_letters, paper_card

N, PID, TITLE = 82, "nine-cells", "Nine cells"
SHEET = pen99.sheet99()
BCAP = 48
CW, CH, G = 640, 853, 30
XS = [110, 110 + CW + G, 110 + 2 * (CW + G)]
YS = [110, 110 + CH + G, 110 + 2 * (CH + G)]
BOXES = {f"C{r * 3 + c + 1}": (XS[c], YS[r], XS[c] + CW, YS[r] + CH) for r in range(3) for c in range(3)}
FLOOR = CH - 16


def scr(k, hot=(0.5, 0.45)):
    x0, y0, x1, y1 = BOXES[k]
    return p5.screen(x1 - x0, y1 - y0, x0, y0, hot=hot, spread=1.25, slats=None)


def win(img, x0, y0, ww, wh, seed, pose=None):
    ws, sill = window(x0, y0, ww, wh, sill=y0 + wh * 0.56, header=64)
    if pose is not None:
        far(img, stranger(x0 + ww / 2 + pose.get("dx", 0), sill + 26, face=pose.get("face", 1),
                          scale=pose.get("scale", 1.0), glove=pose.get("glove", False), tilt=pose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, x0, y0, ww, 64, seed)
    return sill


def C1(st):   # E0: seated at the desk, the memo before him
    img = scr("C1", hot=(0.45, 0.55))
    sh = desk(70, FLOOR - 190, 420, FLOOR) + lamp(520, FLOOR - 400, 210)
    sh += agent(250, FLOOR + 40, face=1, scale=0.55, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
                pencil_deg=60, far_arm=(30, 60))
    sh += clock(470, 150, 62, hh=4, mm=9, swing=-5)
    sil(img, sh)
    slip(img, 92, FLOOR - 262, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 30, 8211, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    return img


def C2(st):   # E0: risen, on his way across the office toward the cupboard
    img = scr("C2", hot=(0.5, 0.5))
    sh = desk(-300, FLOOR - 190, 400, FLOOR)
    c, _ = cupboard(450, 250, 210, 450)
    sh += c + agent(290, FLOOR, face=1, scale=0.55, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200,
                    far_arm=(24, 22))
    sil(img, sh)
    return img


def C3(st):   # E1: the question from the window; he turns to it
    img = scr("C3", hot=(0.4, 0.5))
    win(img, 50, 300, 250, 520, 8231, {"glove": True, "dx": -8, "scale": 0.9})
    sil(img, agent(510, FLOOR, face=-1, scale=0.55, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190))
    balloon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (360, 165), (200, 296), 8232, tail_w=0.22)
    return img


def C4(st):   # E2, a held pause: he looks up at the wall clock, which says ten past four
    img = scr("C4", hot=(0.55, 0.4))
    sh = clock(430, 210, 96, hh=4, mm=10, swing=st.get("swing", 6))
    sh += agent(210, FLOOR, face=1, scale=0.55, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3)
    sil(img, sh)
    return img


def C5(st):   # E2: the answer, turned back to the window
    img = scr("C5", hot=(0.45, 0.5))
    win(img, -110, 300, 250, 520, 8251, {"dx": 30, "scale": 0.9})
    sil(img, agent(450, FLOOR, face=-1, scale=0.55, legs=(4, -4), sh=8, el=24, tilt=-2, pencil_deg=190)
        + clock(560, 120, 48, hh=4, mm=10, swing=-6))
    balloon(img, ["Ten past four,", "by the clock."], BCAP, (270, 230), (400, 410), 8252, tail_w=0.24)
    return img


def C6(st):   # E3: the thanks; she turns from the glass
    img = scr("C6", hot=(0.42, 0.5))
    win(img, 50, 300, 250, 520, 8261, {"face": -1, "dx": -40, "tilt": -6, "scale": 0.86})
    sil(img, agent(520, FLOOR, face=-1, scale=0.55, legs=(14, -12), sh=-10, el=18, pencil_deg=200, lean=2))
    balloon(img, ["Much", "obliged!"], BCAP, (340, 170), (190, 296), 8262, tail_w=0.26)
    return img


def C7(st):   # E3, a held pause: the window empty; he goes on toward the cupboard
    img = scr("C7", hot=(0.5, 0.5))
    win(img, 50, 300, 250, 520, 8271)
    c, _ = cupboard(560, 250, 210, 450)
    sil(img, c + agent(420, FLOOR, face=1, scale=0.55, legs=(26, -24), sh=-26, el=28, lean=4, pencil_deg=200,
                       far_arm=(24, 22)))
    return img


def C8(st):   # E4: he opens the cupboard: the brass key on its hook, tagged SERVICE
    img = scr("C8", hot=(0.4, 0.5))
    p5.cupboard_scene(img, CW, CH, 130, 260, 260, 440, st.get("open", 112), 0.34, sdoor=False)
    sil(img, agent(520, FLOOR, face=-1, scale=0.55, legs=(4, -4), sh=34, el=-20, wr=0, pencil_deg=200, tilt=4))
    return img


def C9(st):   # E5: before the open cupboard, pencil to chin; the key stays, the SERVICE door stays shut
    img = scr("C9", hot=(0.4, 0.5))
    p5.cupboard_scene(img, CW, CH, 40, 380, 210, 330, 112, 0.24, sdoor=True, sd_x=445)
    sil(img, agent(350, FLOOR, face=-1, scale=0.55, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2))
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP - 6, (300, 170), (316, 410), 8291, tail_w=0.20)
    return img


CELLS = [("C1", C1), ("C2", C2), ("C3", C3), ("C4", C4), ("C5", C5), ("C6", C6), ("C7", C7), ("C8", C8), ("C9", C9)]


def build(upto=9, state=None):
    state = state or {}
    page = SHEET.copy()
    for i, (k, fn) in enumerate(CELLS):
        x0, y0, x1, y1 = BOXES[k]
        if i < upto:
            page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=12, seed=8290)   # the grid is ruled first, all nine equal
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    sizes = {k: (b[2] - b[0], b[3] - b[1]) for k, b in BOXES.items()}
    print("jpeg bytes", size, "cell sizes", set(sizes.values()), BOXES)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in (0, 1, 2, 3, 5, 6, 8, 9):
            p = np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
