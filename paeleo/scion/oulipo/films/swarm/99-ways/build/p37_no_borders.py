"""Page 37 No borders (layout and page grammar; medium: daumier-collage).

No panel frames: the Daumier cut-outs, the cut set pieces and the balloons float straight on the LoC 1934
sheet, ordered only by placement (three bands read left to right, top to bottom) and by the balloons' tails.
No ruled line anywhere: no frames, no floor lines, no caption boxes; each figure stands on its own cast shadow.
Reuses page 12's Daumier collage kit (build/daumier12.py, build/p12_loop.py): FORAGED CC0 lithographs by
Honore Daumier (Rijksmuseum via Commons) and the ANRC 1922 key cutout; HANDMADE cuts, pencil, clock hands,
balloons and lettering in the shared pen hand.
Run: python3 -I p37_no_borders.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import daumier12 as D
import p12_loop as L

N, PID, TITLE = 37, "no-borders", "No borders"
SHEET = pen99.sheet99()
BCAP = 46
PAPER = np.array([246, 242, 230], np.float32)


def floor_shadow(c, x0, x1, y, seed):
    """a soft contact shadow under a floating figure (no line: a blurred patch)"""
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.ellipse(m, (int((x0 + x1) / 2), int(y)), (int((x1 - x0) / 2), 16), 0, 0, 360, 255, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 9)
    comp(c, m, np.array([90, 84, 76], np.float32), 0.35)


def window_at(c, x, y, scale, woman, counter_bottom):
    L.PH = counter_bottom / 0.80          # page 12's window unit drops its counter to PH*0.80
    return L.window_unit(c, x, y, scale, woman=woman)


def E0(c):
    # at the desk with the memo (cut at the waist behind the desk)
    floor_shadow(c, 120, 600, 905, 3701)
    L.agent(c, (360, 1110), face=1, head_deg=22, waist=True, scale=0.74)
    L.desk(c, 150, 640, 440, 900)
    L.memo_slip(c, 175, 700, cap=26, tilt=-4, seed=3702)
    L.pencil(c, (470, 632), (585, 622))
    # risen and setting off to the right
    floor_shadow(c, 760, 1060, 905, 3703)
    L.agent(c, (910, 900), face=1, body_deg=4, scale=0.66)
    L.pencil(c, (835, 655), (822, 570))


def E1(c):
    floor_shadow(c, 1440, 2060, 905, 3711)
    window_at(c, 1750, 470, 0.86, (10, -1, 0.74), 900)
    balloon(c, ["Pardon me —", "have you the", "right time?"], BCAP, (1330, 250), (1690, 380), 3712, tail_w=0.22)


def E2(c):
    L.clock(c, 300, 1150, 120)
    floor_shadow(c, 520, 860, 1785, 3721)
    Mb, Mh = L.agent(c, (690, 1780), face=-1, head_deg=16, scale=0.66)
    mouth = L.at_src(Mh, L.HEAD, (786, 642))
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (330, 1580), (mouth[0] - 6, mouth[1] + 8), 3722, tail_w=0.24)


def E3(c):
    floor_shadow(c, 1360, 2060, 1785, 3731)
    window_at(c, 1560, 1330, 0.86, (260, 1, 0.74), 1780)
    balloon(c, ["Much", "obliged!"], BCAP + 4, (1080, 1110), (1700, 1250), 3732, tail_w=0.22)


def E4(c):
    floor_shadow(c, 160, 900, 2660, 3741)
    L.cupboard(c, 320, 2080, 250, 520, open_=True)
    L.agent(c, (760, 2650), face=-1, head_deg=6, scale=0.64)


def E5(c):
    floor_shadow(c, 1080, 2080, 2660, 3751)
    L.cupboard(c, 1210, 2130, 210, 470, open_=True)
    sc = 0.78
    hw, hh = L.DOOR["gray"].shape[1] * sc, L.DOOR["gray"].shape[0] * sc
    cx, top = 1950, 2160
    L.set_piece(c, "mid", [(cx - hw / 2 - 14, top - 14), (cx + hw / 2 + 14, top - 14), (cx + hw / 2 + 14, 2654), (cx - hw / 2 - 14, 2654)])
    L.set_piece(c, "pale", [(cx - hw / 2, top + hh - 4), (cx + hw / 2, top + hh - 4), (cx + hw / 2, 2652), (cx - hw / 2, 2652)], shade=0.86)
    L.service_door(c, cx, top + hh / 2, sc)
    Mb, Mh = L.agent(c, (1580, 2650), face=-1, head_deg=-4, scale=0.64)
    chin = L.at_src(Mh, L.HEAD, (800, 674))
    L.pencil(c, (chin[0] - 100, chin[1] + 104), (chin[0] - 1, chin[1] + 1), w=13, pale=True)
    mouth = L.at_src(Mh, L.HEAD, (786, 642))
    balloon(c, ["Well, here I am...", "and what for?"], BCAP - 2, (1540, 1960), (mouth[0] - 6, mouth[1] - 8), 3752, tail_w=0.22)


STEPS = [E0, E1, E2, E3, E4, E5]


def build(upto=6):
    page = SHEET.copy()
    for f in STEPS[:upto]:
        f(page)
    return page


def ruled_line_check(img):
    """look for any long straight dark line (a frame rule) with a Hough transform on the dark-ink mask"""
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    ink = (g < 60).astype(np.uint8) * 255
    lines = cv2.HoughLinesP(ink, 1, np.pi / 180, threshold=400, minLineLength=500, maxLineGap=4)
    return 0 if lines is None else len(lines)


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "long ruled dark lines:", ruled_line_check(img))
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in range(1, 7):
            p = np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
