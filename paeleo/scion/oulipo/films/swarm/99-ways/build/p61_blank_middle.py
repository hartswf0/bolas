"""99 ways, page 61 "Blank middle" (reduction and expansion; medium: shadow-puppet).

Only the first and the last beats are pictured: two lit shadow screens (page 05's screen, sil and brass-key
gel; black cut-paper b1m2 puppets and set pieces, HANDMADE), E0 at the top and E4-E5 at the foot. The three
middle panels are bare paper (the LoC 1934 sheet, nothing laid on it) carrying only the cut-paper balloons of
the question, the answer and the thanks, their tails pointing out toward speakers we are not shown.
Run: python3 -I p61_blank_middle.py"""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p05_noir as S  # noqa: E402  (screen, sil, far, brass_key, hook, paper_card, cupboard_scene)
from b1m2 import *  # noqa: E402,F401

N, PID, TITLE = 61, "blank-middle", "Blank middle"
BOXES = {"P1": (110, 110, 2090, 1010),
         "P2": (110, 1050, 743, 1650), "P3": (783, 1050, 1416, 1650), "P4": (1457, 1050, 2090, 1650),
         "P5": (110, 1690, 2090, 2730)}
CAP, BCAP = 40, 52


def P1(st):
    x0, y0, x1, y1 = BOXES["P1"]
    w, h = x1 - x0, y1 - y0
    img = S.screen(w, h, x0, y0, hot=(0.42, 0.56), spread=0.95)
    floor = h - 22
    c, _ = cupboard(1440, 330, 230, floor - 330)
    sh = desk(150, 560, 560, floor) + lamp(640, 330, 230) + c
    sh += service_door(1730, 250, 200, floor - 250)
    sh += clock(1250, 250, 78, hh=4, mm=9, pend=True, swing=-8)
    sh += agent(920, floor, face=1, scale=0.68, legs=(22, -20), sh=-22, el=24, lean=5, pencil_deg=200, far_arm=(22, 20))
    S.sil(img, sh)
    slip(img, 250, 455, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 31, 6101, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    S.paper_card(img, 1830, 330, ["SERVICE"], 30, 6102)
    S.cap_slip(img, "Randolph, 1937. The memo says: at 4:15 open the SERVICE door; the key is in the cupboard. "
                    "The agent gets up and sets off to fetch it.", 1080, 6103)
    return img


def P5(st):
    x0, y0, x1, y1 = BOXES["P5"]
    w, h = x1 - x0, y1 - y0
    img = S.screen(w, h, x0, y0, hot=(0.42, 0.55), spread=0.95)
    od = st.get("open", 112)
    floor = h - 24
    S.cupboard_scene(img, w, h, 470, 330, 420, floor - 330, od, 0.62, sdoor=True, sd_x=1560)
    if st.get("agent", "chin") == "chin":
        S.sil(img, agent(1210, floor, face=-1, scale=0.86, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    else:
        S.sil(img, agent(1210, floor, face=-1, scale=0.86, legs=(3, -3), sh=60, el=10, pencil_deg=190, lean=-3))
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP, (1640, 150), (1260, 250), 6151, tail_w=0.22)
    S.cap_slip(img, "The key stays on its hook. The SERVICE door stays closed.", 760, 6152, cap=CAP)
    return img


def blank(img, key, lines, tip_rel, seed, show):
    """A middle panel: bare paper; only its balloon is laid (if shown)."""
    if not show:
        return
    x0, y0, x1, y1 = BOXES[key]
    cx, cy = (x0 + x1) / 2, y0 + 250
    balloon(img, lines, BCAP, (cx, cy), (x0 + tip_rel[0], y0 + tip_rel[1]), seed, tail_w=0.22, bend=0.12)


def build(nb=3, last=None):
    """nb: how many middle balloons are laid; last: state of the last panel, or None for a dark/empty frame."""
    page = S.SHEET.copy()
    x0, y0, x1, y1 = BOXES["P1"]
    page[y0:y1, x0:x1] = P1({})
    blank(page, "P2", ["Pardon me —", "have you the", "right time?"], (560, 560), 6121, nb >= 1)
    blank(page, "P3", ["Ten past four,", "by the clock."], (80, 560), 6131, nb >= 2)
    blank(page, "P4", ["Much", "obliged!"], (560, 520), 6141, nb >= 3)
    if last is not None:
        x0, y0, x1, y1 = BOXES["P5"]
        page[y0:y1, x0:x1] = P5(last)
    frame_border(page, list(BOXES.values()), w=12, seed=6190)
    return page


def fin(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build(3, {})
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page" not in sys.argv:
        states = [(0, None), (1, None), (2, None), (3, None),
                  (3, {"open": 0, "agent": "reach", "line": False}), (3, {"open": 112, "agent": "reach", "line": False}),
                  (3, {"line": False}), (3, {})]
        print("beats", save_beats(N, [fin(build(*s)) for s in states]))
