"""Page 30 Jump cuts (time and order; medium: shadow-puppet).

Black cut-paper silhouette puppets (b1m2 figure model, HANDMADE) and cut set pieces against an evenly lamp-lit
paper screen (page 05's screen and puppet tools, without its blind slats). Seven shots; every shot after the first
opens with a caption stating how much time the cut skipped, and no two skips are equal:
6, 11, 3, 2, 40 and 22 seconds (4:09:41 -> 4:09:47 -> 4:09:58 -> 4:10:01 -> 4:10:03 -> 4:10:43 -> 4:11:05).
Run: python3 -I p30_jump_cuts.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p05_noir as p5
from p05_noir import sil, far, window_letters, brass_key, paper_card, hook

N, PID, TITLE = 30, "jump-cuts", "Jump cuts"
SHEET = pen99.sheet99()
CAP = 44      # caption cap
BCAP = 52     # balloon cap
GAP_PAPER = np.array([236, 226, 196], np.float32)

BOXES = {
    "P1": (110, 110, 2090, 742),
    "P2": (110, 772, 1085, 1404), "P3": (1115, 772, 2090, 1404),
    "P4": (110, 1434, 1085, 2066), "P5": (1115, 1434, 2090, 2066),
    "P6": (110, 2096, 1085, 2728), "P7": (1115, 2096, 2090, 2728),     # gutter aligned with rows 2-3
}
# the stated skip opening each shot after the first (seconds); start 4:09:41
GAPS = {"P2": (6, "Six seconds later"), "P3": (11, "Eleven seconds later"), "P4": (3, "Three seconds later"),
        "P5": (2, "Two seconds later"), "P6": (40, "Forty seconds later"), "P7": (22, "Twenty-two seconds later")}
START = "Nineteen seconds to ten past four"


def scr(k, hot=(0.5, 0.45)):
    x0, y0, x1, y1 = BOXES[k]
    w, h = x1 - x0, y1 - y0
    return p5.screen(w, h, x0, y0, hot=hot, spread=1.25, slats=None), w, h


def gap_card(img, text, seed):
    """The stated skip: a pasted caption slip, top left, in the shared pen hand."""
    return slip(img, 24, 22, [text], CAP, seed, paper=GAP_PAPER, pad=(22, 12))


def win(img, x0, y0, ww, wh, seed, stranger_pose=None):
    ws, sill = window(x0, y0, ww, wh, sill=y0 + wh * 0.56, header=64)
    if stranger_pose is not None:
        far(img, stranger(x0 + ww / 2 + stranger_pose.get("dx", 0), sill + 26, face=stranger_pose.get("face", 1),
                          scale=stranger_pose.get("scale", 1.0), glove=stranger_pose.get("glove", False),
                          tilt=stranger_pose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, x0, y0, ww, 64, seed)
    return sill


def P1(st):   # E0 at the desk, the memo: one wide shot of the office
    img, w, h = scr("P1", hot=(0.45, 0.5))
    floor = h - 16
    win(img, 70, 150, 250, 470, 3011)
    sh = desk(520, floor - 180, 470, floor) + lamp(930, floor - 380, 200)
    sh += agent(690, floor + 34, face=1, scale=0.50, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
                pencil_deg=60, far_arm=(30, 60))
    sh += clock(1180, 210, 70, hh=4, mm=9, swing=-5)
    c, _ = cupboard(1420, 150, 200, 440)
    sh += c + service_door(1730, 110, 210, 490)
    sil(img, sh)
    slip(img, 560, floor - 250, ["4:15 - open SERVICE door.", "Key in cupboard."], 28, 3012, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    paper_card(img, 1835, 190, ["SERVICE"], 30, 3013)
    slip(img, 24, 22, [START + "."], CAP, 3014, paper=GAP_PAPER, pad=(22, 12))
    return img


def P2(st):   # E0 +6 s: risen, already halfway across the floor
    img, w, h = scr("P2", hot=(0.5, 0.5))
    floor = h - 16
    sh = desk(-260, floor - 180, 380, floor)
    c, _ = cupboard(620, 170, 200, 440)
    sh += c + agent(400, floor, face=1, scale=0.58, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200,
                    far_arm=(24, 22))
    sil(img, sh)
    gap_card(img, GAPS["P2"][1], 3021)
    return img


def P3(st):   # E1 +11 s: turned back to the window; the question
    img, w, h = scr("P3", hot=(0.42, 0.5))
    floor = h - 16
    win(img, 60, 150, 300, 470, 3031, {"glove": True, "dx": -10, "scale": 1.0})
    sil(img, agent(830, floor, face=-1, scale=0.50, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190))
    balloon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (575, 340), (215, 330), 3032, tail_w=0.22)
    gap_card(img, GAPS["P3"][1], 3033)
    return img


def P4(st):   # E2 +3 s: he looks up at the clock: ten past four
    img, w, h = scr("P4", hot=(0.55, 0.42))
    floor = h - 16
    sh = clock(790, 225, 80, hh=4, mm=10, swing=6)
    a = agent(240, floor, face=1, scale=0.50, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3)
    sh += a
    sil(img, sh)
    balloon(img, ["Ten past four,", "by the clock."], BCAP, (560, 480), (282, 238), 3041, tail_w=0.24)
    gap_card(img, GAPS["P4"][1], 3042)
    return img


def P5(st):   # E3 +2 s: the thanks; she is already turning from the glass
    img, w, h = scr("P5", hot=(0.42, 0.5))
    floor = h - 16
    win(img, 60, 150, 300, 470, 3051, {"face": -1, "dx": -50, "tilt": -6, "scale": 0.95})
    sil(img, agent(800, floor, face=1, scale=0.50, legs=(16, -14), sh=-10, el=18, pencil_deg=200, lean=2))
    balloon(img, ["Much", "obliged!"], BCAP, (560, 300), (170, 320), 3052, tail_w=0.26)
    gap_card(img, GAPS["P5"][1], 3053)
    return img


def P6(st):   # E4 +40 s: the long skip: he is at the open cupboard, the key on its hook
    img, w, h = scr("P6", hot=(0.45, 0.5))
    floor = h - 16
    p5.cupboard_scene(img, w, h, 200, 190, 290, 410, st.get("open", 112), 0.34, sdoor=True, sd_x=740)
    sil(img, agent(620, floor, face=-1, scale=0.50, legs=(4, -4), sh=34, el=-20, wr=0, pencil_deg=200, tilt=4))
    gap_card(img, GAPS["P6"][1], 3061)
    return img


CHECK = {}


def P7(st):   # E5 +22 s: still before it, pencil to his chin; the key stays, the SERVICE door shut
    img, w, h = scr("P7", hot=(0.45, 0.5))
    floor = h - 16
    p5.cupboard_scene(img, w, h, 70, 340, 220, 276, 112, 0.22, sdoor=True, sd_x=736)
    # he faces LEFT, into the open cupboard, forearm raised, the pencil's end at his chin
    ag = agent(610, floor, face=-1, scale=0.50, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2)
    sil(img, ag)
    before = img.copy()
    if st.get("line", True):
        # the balloon over the cupboard's top-left, its tail to his mouth, clear of his head and the pencil
        balloon(img, ["Well, here I am...", "and what for?"], BCAP - 8, (236, 230), (508, 236), 3071, tail_w=0.20)
    bm = (np.abs(img - before).sum(axis=2) > 6)
    hm = raster([s_ for s_ in ag if s_.role in ("skin", "hair", "ear", "pencil") and s_.pts[:, 1].min() < floor - 330],
                w, h, holes=False) > 30
    CHECK["P7"] = {"balloon_px_over_head_or_pencil": int((bm & hm).sum()), "head_pencil_px": int(hm.sum()),
                   "agent_faces": "left, toward the open cupboard"}
    gap_card(img, GAPS["P7"][1], 3072)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7)]


def build(upto=7, state=None):
    state = state or {}
    page = SHEET.copy()
    shown = []
    for i, (k, fn) in enumerate(PANELS):
        if i >= upto:
            continue
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
        shown.append(BOXES[k])
    frame_border(page, shown, w=12, seed=3090)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    gaps = [g for g, _ in GAPS.values()]
    print("jpeg bytes", size, "gaps", gaps, "distinct", len(set(gaps)) == len(gaps), CHECK)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in range(1, 8):
            p = np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
