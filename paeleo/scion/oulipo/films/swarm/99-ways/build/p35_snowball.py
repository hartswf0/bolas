"""Page 35 Snowball (formal / Oulipian rule; medium: shadow-puppet).

Caption n has exactly n words, one to eight. Eight shots of black cut-paper silhouette puppets (b1m2 figure
model, HANDMADE) and cut set pieces on page 05's lamp-lit paper screen (no blind slats). The snowball shows in
the layout too: each shot is larger than the one before (rows grow taller, the right shot of each row wider).
The four canon lines in pen-hand balloons (balloons are not captions and are not counted).
Run: python3 -I p35_snowball.py [beats]
"""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p05_noir as p5
from p05_noir import sil, far, window_letters, paper_card

N, PID, TITLE = 35, "snowball", "Snowball"
SHEET = pen99.sheet99()
CAP = 42
BCAP = 42
CAP_PAPER = np.array([236, 226, 196], np.float32)

CAPTIONS = [
    "Randolph.",
    "He rises.",
    "A voice calls.",
    "He checks the clock.",
    "She thanks him and goes.",
    "He opens the cupboard door wide.",
    "There hangs the brass key, tagged SERVICE.",
    "He has quite forgotten what he came for.",
]


def words(s):
    return [w for w in s.replace("—", " ").split() if any(ch.isalnum() for ch in w)]


assert [len(words(c)) for c in CAPTIONS] == list(range(1, 9)), [len(words(c)) for c in CAPTIONS]

# rows grow taller; in each row the right shot is wider (ratio n+4 : n+5)
ROWH = [520, 600, 680, 760]
GUT = 20
BOXES = {}
y = 110
for r, rh in enumerate(ROWH):
    a, b = 2 * r + 1, 2 * r + 2
    wa = int(round((1980 - GUT) * (a + 4) / (2 * a + 9)))
    BOXES[f"P{a}"] = (110, y, 110 + wa, y + rh)
    BOXES[f"P{b}"] = (110 + wa + GUT, y, 2090, y + rh)
    y += rh + GUT
assert y - GUT == 2730, y


def scr(k, hot=(0.5, 0.45)):
    x0, y0, x1, y1 = BOXES[k]
    w, h = x1 - x0, y1 - y0
    return p5.screen(w, h, x0, y0, hot=hot, spread=1.25, slats=None), w, h


def caption(img, n, w):
    lines = wrap(CAPTIONS[n - 1], CAP, w - 50)
    return slip(img, 24, 22, lines, CAP, 3500 + n, paper=CAP_PAPER, pad=(22, 12))


def win(img, x0, y0, ww, wh, seed, sp=None):
    ws, sill = window(x0, y0, ww, wh, sill=y0 + wh * 0.56, header=64)
    if sp is not None:
        far(img, stranger(x0 + ww / 2 + sp.get("dx", 0), sill + 26, face=sp.get("face", 1), scale=sp.get("scale", 1.0),
                          glove=sp.get("glove", False), tilt=sp.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, x0, y0, ww, 64, seed)
    return sill


def P1(st):   # E0 at the desk with the memo
    img, w, h = scr("P1", hot=(0.5, 0.55))
    floor = h - 16
    sh = desk(170, floor - 150, 420, floor) + lamp(540, floor - 330, 180)
    sh += agent(330, floor + 30, face=1, scale=0.40, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
                pencil_deg=60, far_arm=(30, 60))
    sh += clock(760, 150, 56, hh=4, mm=9, swing=-5)
    sil(img, sh)
    slip(img, 150, floor - 120, ["4:15 - open SERVICE door.", "Key in cupboard."], 24, 3511, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    caption(img, 1, w)
    return img


def P2(st):   # E0 risen and setting off toward the cupboard
    img, w, h = scr("P2", hot=(0.5, 0.5))
    floor = h - 16
    sh = desk(-240, floor - 150, 360, floor)
    c, _ = cupboard(700, 130, 170, 360)
    sh += c + service_door(920, 90, 110, 410)
    sh += agent(400, floor, face=1, scale=0.42, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200, far_arm=(24, 22))
    sil(img, sh)
    caption(img, 2, w)
    return img


def P3(st):   # E1 the question through the window
    img, w, h = scr("P3", hot=(0.42, 0.5))
    floor = h - 16
    win(img, 60, 140, 280, 440, 3531, {"glove": True, "dx": -10, "scale": 0.92})
    sil(img, agent(780, floor, face=-1, scale=0.46, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190))
    balloon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (540, 330), (200, 310), 3532, tail_w=0.22)
    caption(img, 3, w)
    return img


def P4(st):   # E2 he looks up at the clock: 4:10
    img, w, h = scr("P4", hot=(0.55, 0.42))
    floor = h - 16
    sh = clock(820, 190, 78, hh=4, mm=10, swing=6)
    sh += agent(250, floor, face=1, scale=0.46, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3)
    sil(img, sh)
    balloon(img, ["Ten past four,", "by the clock."], BCAP, (590, 470), (300, 260), 3541, tail_w=0.24)
    caption(img, 4, w)
    return img


def P5(st):   # E3 the thanks; she turns from the glass
    img, w, h = scr("P5", hot=(0.42, 0.5))
    floor = h - 16
    win(img, 60, 170, 300, 480, 3551, {"face": -1, "dx": -50, "tilt": -6, "scale": 0.95})
    sil(img, agent(770, floor, face=1, scale=0.50, legs=(16, -14), sh=-10, el=18, pencil_deg=200, lean=2))
    balloon(img, ["Much", "obliged!"], BCAP, (560, 330), (180, 350), 3552, tail_w=0.26)
    caption(img, 5, w)
    return img


def P6(st):   # E4 he opens the cupboard; the key on its hook
    img, w, h = scr("P6", hot=(0.45, 0.5))
    floor = h - 16
    p5.cupboard_scene(img, w, h, 150, 200, 280, 440, st.get("open", 112), 0.30, sdoor=True, sd_x=760)
    sil(img, agent(600, floor, face=-1, scale=0.52, legs=(4, -4), sh=60, el=-10, wr=0, pencil_deg=200, tilt=4))
    caption(img, 6, w)
    return img


def P7(st):   # E4 the key, close: brass on its hook, tagged SERVICE
    img, w, h = scr("P7", hot=(0.45, 0.55))
    p5.cupboard_scene(img, w, h, 150, 210, 520, 600, 112, 0.62, sdoor=False)
    sil(img, agent(880, h + 330, face=-1, scale=0.95, sh=6, el=10, pencil_deg=200, tilt=2))   # his shoulder at the edge
    caption(img, 7, w)
    return img


def P8(st):   # E5 pencil to his chin; the key stays, the SERVICE door shut
    img, w, h = scr("P8", hot=(0.45, 0.5))
    floor = h - 16
    p5.cupboard_scene(img, w, h, 130, 410, 220, 300, 112, 0.22, sdoor=True, sd_x=770)
    sil(img, agent(620, floor, face=-1, scale=0.56, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2))
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP - 4, (300, 270), (520, 318), 3581, tail_w=0.20)
    caption(img, 8, w)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7), ("P8", P8)]


def build(upto=8):
    page = SHEET.copy()
    shown = []
    for i, (k, fn) in enumerate(PANELS):
        if i >= upto:
            continue
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn({})
        shown.append(BOXES[k])
    frame_border(page, shown, w=12, seed=3590)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, [len(words(c)) for c in CAPTIONS], BOXES)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in range(1, 9):
            p = np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
