"""Page 90 Find the key (reader and object; medium: busch-fold).

One crowded picture of Randolph station on a September afternoon, printed as a puzzle sheet and laid on the
les-caids tabletop with the creases of being sold folded in four. The front of the station is cut away: the office
(desk, clock, cupboard, SERVICE door, shelves of parcels), the waiting room beyond the ticket window and the
platform in front, all crowded with passengers and luggage. The agent is there six times, the stranger twice: the
six beats E0-E5 are hidden in the crowd, and a legend under the picture asks the reader to find them in order.
Cutouts (all PD, foraged by les-caids-de-la-gaudriole and 99-ways): the agent = the les-caids porter cut
(Busch 1865, Max und Moritz plate 31) as page 39 cut him; the stranger = Helene (Busch 1872) with page 39's
HANDMADE cloche; the crowd = the miller with his sack (plate 82, les-caids part), the two boys (plate 1, les-caids
part), the widow (plate 16, page 11's cut), Munzel the cat (Busch 1872, page 11's cut). Set, luggage, train and
lettering are HANDMADE ink in code, the shared pen hand. Run: python3 -I p90_find_the_key.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p11_station_cat as k11  # noqa: E402
from p11_station_cat import line, hatch, text, ellipse_pts, paste, affine, rgba_part  # noqa: E402
import p39_meanwhile as M39  # noqa: E402
from p69_picture_sheet import creases, ornament_rule  # noqa: E402
from b1m2 import save_beats  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
N, PID, TITLE = 90, "find-the-key", "Find the key"
INK = np.array([20, 19, 18], np.float32)
PARTS = ROOT / "films/sources/les-caids-de-la-gaudriole/panel-artist/parts"
OUT_JPG = ROOT / "assets/pages/99-ways" / f"{N}-{PID}.jpg"
OUT_PNG = ROOT / "films/sources/99-ways/masters" / f"{N}-{PID}.png"

PX0, PY0, PX1, PY1 = 120, 330, 2080, 2250      # the picture
F1 = 1470                                       # office / waiting-room floor
FB = 1380                                       # the back of the office floor (figures further off)
F2 = 2215                                       # the platform in front
WALL_X0, WALL_X1 = 690, 742                     # the wall with the ticket window
WIN_Y0, WIN_Y1 = 990, 1250

P = {}


def pieces():
    if P:
        return P
    P["porter"] = M39.porter_piece()
    P["helene"] = M39.helene_piece()
    mb = rgba_part(PARTS / "miller.body.png")
    ma = rgba_part(PARTS / "miller.arm.png")
    mh = rgba_part(PARTS / "miller.hand.png")
    g = np.full(mb[0].shape, 255.0, np.float32)
    a = np.zeros(mb[1].shape, np.uint8)
    for gg, aa in (mb, ma, mh):                   # the three cut parts, re-assembled at their rest pose
        af = aa.astype(np.float32) / 255
        g = g * (1 - af) + gg * af
        a = np.maximum(a, aa)
    P["miller"] = (g, a)
    P["boys"] = rgba_part(PARTS / "boys.png")
    P["widow"] = k11.bolte_piece()
    P["cat"] = k11.cat_piece()
    return P


def lay(c, piece, M, margin=6):
    g, a = piece
    return paste(c, g, a, M, margin=margin)


def pt(M, p):
    return (M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2], M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2])


def balloon(c, lines, cap, centre, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.24, bend=0.08)
    penlib.lay_balloon(c, b, centre)


def paper_box(c, x0, y0, x1, y1, col=(246, 244, 238)):
    bg = np.zeros(c.shape[:2], np.uint8)
    cv2.rectangle(bg, (int(x0), int(y0)), (int(x1), int(y1)), 255, -1)
    pa = bg.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - pa) + np.array(col, np.float32) * pa


def board(c, m, x0, y0, x1, y1, lines, cap, seed, w=4):
    paper_box(c, x0, y0, x1, y1)
    line(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], w, seed)
    n = len(lines)
    for k, ln in enumerate(lines):
        text(m, [ln], (x0 + x1) / 2, y0 + (y1 - y0) * (k + 0.5) / n + cap * 0.45, cap, seed + 1 + k, align="centre",
             weight=0.16)


# ------------------------------------------------------------------ the set (HANDMADE ink)
def station(c, seed):
    m = np.zeros((H, W), np.uint8)
    # the cut-away building: roof eave with the station name, the back walls, the floors
    line(m, [(PX0, 470), (PX1, 470)], 7, seed)
    line(m, [(PX0, 452), (PX1, 452)], 3, seed + 1)
    for k, x in enumerate(range(PX0 + 30, PX1, 120)):
        line(m, [(x, 470), (x + 40, 430)], 2.5, seed + 2 + k)
    line(m, [(PX0, F1), (PX1, F1)], 7, seed + 40)
    line(m, [(PX0, F1 + 16), (PX1, F1 + 16)], 3, seed + 41)
    line(m, [(PX0, FB), (WALL_X0, FB)], 2, seed + 42)
    line(m, [(WALL_X1, FB), (PX1, FB)], 2, seed + 43)
    for k, x in enumerate(range(PX0 + 40, PX1, 90)):   # floorboards running toward us
        line(m, [(x, FB + 4), (x - 30, F1 - 4)], 1.6, seed + 50 + k, tremor=0.4)
    # wainscot on the back walls
    line(m, [(PX0, 1150), (WALL_X0, 1150)], 2.5, seed + 90)
    line(m, [(WALL_X1, 1150), (PX1, 1150)], 2.5, seed + 91)
    for k, x in enumerate(range(PX0 + 10, PX1, 46)):
        if not (WALL_X0 - 4 < x < WALL_X1 + 4):
            line(m, [(x, 1156), (x, FB - 6)], 1.4, seed + 100 + k, tremor=0.3)
    # the dividing wall and the ticket window in it (seen edge on)
    line(m, [(WALL_X0, 474), (WALL_X0, WIN_Y0)], 6, seed + 200)
    line(m, [(WALL_X1, 474), (WALL_X1, WIN_Y0)], 6, seed + 201)
    hatch(m, WALL_X0, 476, WALL_X1, WIN_Y0 - 2, 12, 2, seed + 202, ang=-50)
    line(m, [(WALL_X0, WIN_Y1 + 22), (WALL_X0, F1)], 6, seed + 203)
    line(m, [(WALL_X1, WIN_Y1 + 22), (WALL_X1, F1)], 6, seed + 204)
    hatch(m, WALL_X0, WIN_Y1 + 24, WALL_X1, F1 - 2, 12, 2, seed + 205, ang=-50)
    line(m, [(WALL_X0 - 70, WIN_Y1), (WALL_X1 + 70, WIN_Y1)], 7, seed + 206)          # the counter
    line(m, [(WALL_X0 - 70, WIN_Y1 + 22), (WALL_X1 + 70, WIN_Y1 + 22)], 4, seed + 207)
    line(m, [(WALL_X0, WIN_Y0), (WALL_X1, WIN_Y0)], 6, seed + 208)
    line(m, [((WALL_X0 + WALL_X1) / 2, WIN_Y0), ((WALL_X0 + WALL_X1) / 2, WIN_Y1)], 2, seed + 209)  # the glass
    # OFFICE: shelves of parcels and ledgers high on the back wall
    for k, y in enumerate((640, 800)):
        line(m, [(800, y), (1240, y)], 5, seed + 300 + k)
        x = 810
        r = np.random.RandomState(seed + k)
        while x < 1220:
            w = r.randint(24, 70)
            h = r.randint(50, 120)
            line(m, [(x, y), (x, y - h), (x + w, y - h), (x + w, y)], 3, seed + 310 + x)
            if r.rand() < 0.5:
                line(m, [(x + 4, y - h / 2), (x + w - 4, y - h / 2)], 1.6, seed + 320 + x)
            x += w + r.randint(4, 14)
    # the desk (back), its telegraph sounder and inkstand
    dx0, dx1, dt = 930, 1240, 1170
    line(m, [(dx0 - 14, dt), (dx1 + 14, dt)], 7, seed + 400)
    line(m, [(dx0, dt + 20), (dx1, dt + 20)], 3, seed + 401)
    line(m, [(dx0 + 10, dt + 20), (dx0 + 10, FB)], 6, seed + 402)
    line(m, [(dx1 - 10, dt + 20), (dx1 - 10, FB)], 6, seed + 403)
    hatch(m, dx0 + 14, dt + 26, dx0 + 120, FB - 4, 14, 2, seed + 404, ang=-80)
        # the clock on the back wall (4:10)
    M39.clock(m, 1340, 640, 58, seed + 500)
    # a calendar, a framed map and a pigeonhole rack on the office wall
    line(m, [(1420, 520), (1540, 520), (1540, 680), (1420, 680), (1420, 520)], 4, seed + 540)
    line(m, [(1420, 560), (1540, 560)], 2.5, seed + 541)
    text(m, ["SEPT. 1937"], 1480, 550, 15, seed + 542, align="centre", weight=0.16)
    for r_ in range(3):
        for q in range(5):
            line(m, ellipse_pts(1436 + q * 22, 590 + r_ * 28, 4, 4), 1.6, seed + 545 + r_ * 5 + q)
    line(m, [(1660, 500), (1880, 500), (1880, 680), (1660, 680), (1660, 500)], 5, seed + 560)
    line(m, [(1680, 600), (1720, 560), (1770, 620), (1830, 540), (1860, 600)], 2.5, seed + 561)
    line(m, [(1700, 520), (1712, 660)], 1.6, seed + 562)
    line(m, [(1790, 520), (1800, 660)], 1.6, seed + 563)
    for r_ in range(3):
        for q in range(4):
            x_, y_ = 800 + q * 52, 860 + r_ * 50
            line(m, [(x_, y_), (x_ + 48, y_), (x_ + 48, y_ + 46), (x_, y_ + 46), (x_, y_)], 2.5, seed + 570 + r_ * 4 + q)
            if (r_ + q) % 2 == 0:
                line(m, [(x_ + 8, y_ + 30), (x_ + 40, y_ + 26)], 1.6, seed + 590 + r_ * 4 + q)
    # a hanging lamp
    for k, x in enumerate((1080, 1560)):
        line(m, [(x, 474), (x, 560)], 2, seed + 520 + k)
        line(m, [(x - 50, 600), (x - 24, 560), (x + 24, 560), (x + 50, 600), (x - 50, 600)], 4, seed + 530 + k)
    # the cupboard, open (leaf on the left jamb), and the SERVICE door, shut
    cx0, cx1, cy0 = 1700, 1880, 900
    line(m, [(cx0, cy0), (cx1, cy0), (cx1, FB)], 6, seed + 600)
    line(m, [(cx0, cy0), (cx0, FB)], 6, seed + 601)
    line(m, [(cx0 - 14, cy0 - 20), (cx1 + 14, cy0 - 20)], 6, seed + 602)
    hatch(m, cx0 + 4, cy0 + 4, cx1 - 4, FB - 4, 9, 2, seed + 603, ang=-70)
    for yy in (1080, 1240):
        line(m, [(cx0 + 4, yy), (cx1 - 4, yy)], 4, seed + 604 + yy)
    line(m, [(cx0, cy0), (cx0 - 70, cy0 + 40), (cx0 - 70, FB - 26), (cx0, FB)], 6, seed + 610)
    sx0, sx1, sy0 = 1920, 2070, 800
    line(m, [(sx0, FB), (sx0, sy0), (sx1, sy0), (sx1, FB)], 6, seed + 620)
    line(m, [(sx0 + 22, sy0 + 130), (sx1 - 22, sy0 + 130), (sx1 - 22, sy0 + 330), (sx0 + 22, sy0 + 330), (sx0 + 22, sy0 + 130)], 3, seed + 621)
    line(m, [(sx0 + 22, sy0 + 370), (sx1 - 22, sy0 + 370), (sx1 - 22, FB - 30), (sx0 + 22, FB - 30), (sx0 + 22, sy0 + 370)], 3, seed + 622)
    line(m, ellipse_pts(sx1 - 30, sy0 + 350, 8, 8), 3, seed + 623)
    # coat stand and mail sacks in the office
    line(m, [(1440, FB), (1440, 900)], 5, seed + 700)
    line(m, [(1400, FB), (1480, FB)], 5, seed + 701)
    for k, (a, b) in enumerate(((1400, 930), (1480, 930), (1410, 960), (1472, 960))):
        line(m, [(1440, 905), (a, b)], 3, seed + 702 + k)
    line(m, [(1418, 935), (1402, 1010), (1430, 1120), (1460, 1010), (1440, 935)], 3, seed + 710)   # a coat on its peg
    # WAITING ROOM: bench, timetable, a poster, the door to the trains
    line(m, [(180, 1290), (520, 1290)], 6, seed + 800)
    line(m, [(180, 1210), (520, 1210)], 4, seed + 801)
    for x in (196, 504):
        line(m, [(x, 1210), (x, FB)], 5, seed + 802 + x)
    line(m, [(140, FB), (140, 760), (300, 760), (300, FB)], 6, seed + 820)
    line(m, [(160, 780), (280, 780), (280, 1000), (160, 1000), (160, 780)], 3, seed + 821)
    # PLATFORM in front: the edge, boards, a coach at the left with steam, trunks and a barrow
    line(m, [(PX0, F2), (PX1, F2)], 7, seed + 900)
    line(m, [(PX0, F2 + 18), (PX1, F2 + 18)], 3, seed + 901)
    for k, x in enumerate(range(PX0 + 20, PX1, 60)):
        line(m, [(x, F2 - 60), (x - 10, F2 - 4)], 1.4, seed + 910 + k, tremor=0.4)
    penlib.ink_onto(c, m, INK)
    return m


def coach(c, seed):
    m = np.zeros((H, W), np.uint8)
    x0, x1, y0, y1 = PX0 - 4, PX1 + 4, 1570, 2060
    paper_box(c, x0, y0 - 60, x1, y1 + 60, (240, 238, 232))
    line(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 6, seed)
    line(m, ellipse_pts((x0 + x1) / 2, y0, (x1 - x0) / 2, 50, 180, 360), 5, seed + 1)
    for k, wx in enumerate(range(x0 + 40, x1 - 90, 130)):
        line(m, [(wx, 1630), (wx + 90, 1630), (wx + 90, 1770), (wx, 1770), (wx, 1630)], 4, seed + 10 + k)
    line(m, [(x0, 1810), (x1, 1810)], 2.5, seed + 3)
    hatch(m, x0 + 2, 1816, x1 - 2, y1 - 4, 30, 1.8, seed + 4, ang=-85)
    for k, wx in enumerate((x0 + 120, x0 + 560, x1 - 560, x1 - 120)):
        line(m, ellipse_pts(wx, y1 + 50, 44, 44), 5, seed + 30 + k)
    M39.steam(m, seed + 60, 520, 1480, 4)
    penlib.ink_onto(c, m, INK)


def trunk(m, x0, y0, w, h, seed, straps=True):
    line(m, [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)], 5, seed)
    line(m, [(x0, y0 + h * 0.28), (x0 + w, y0 + h * 0.28)], 2.5, seed + 1)
    if straps:
        for k, f in enumerate((0.25, 0.75)):
            line(m, [(x0 + w * f, y0), (x0 + w * f, y0 + h)], 3, seed + 2 + k)
    hatch(m, x0 + 3, y0 + h * 0.3, x0 + w - 3, y0 + h - 3, 22, 1.4, seed + 5, ang=-70)


def hatbox(m, cx, y1, r, h, seed):
    line(m, ellipse_pts(cx, y1 - h, r, r * 0.3), 3, seed)
    line(m, [(cx - r, y1 - h), (cx - r, y1)], 3, seed + 1)
    line(m, [(cx + r, y1 - h), (cx + r, y1)], 3, seed + 2)
    line(m, ellipse_pts(cx, y1, r, r * 0.3, 0, 180), 3, seed + 3)


def luggage(c, seed):
    m = np.zeros((H, W), np.uint8)
    trunk(m, 900, 1990, 300, 220, seed)
    trunk(m, 940, 1860, 220, 130, seed + 10, straps=False)
    hatbox(m, 1050, 1858, 60, 70, seed + 20)
    trunk(m, 1720, 2050, 200, 160, seed + 30)
    hatbox(m, 1960, 2210, 70, 90, seed + 40)
    trunk(m, 300, 1360, 120, 100, seed + 50, straps=False)              # a case under the bench
    # the barrow
    line(m, [(1300, 2120), (1600, 2120)], 6, seed + 60)
    line(m, [(1300, 2120), (1250, 1980)], 5, seed + 61)
    line(m, ellipse_pts(1560, 2168, 40, 40), 5, seed + 62)
    trunk(m, 1340, 2010, 220, 108, seed + 70)
    # parcels and sacks in the office corner
    for k, (x, y, w, h) in enumerate(((770, 1380, 90, 70), (800, 1320, 60, 60), (860, 1390, 70, 60))):
        line(m, [(x, y), (x + w, y), (x + w, y + h - 10), (x, y + h - 10), (x, y)], 3, seed + 80 + k)
    penlib.ink_onto(c, m, INK)


def memo(c, seed):
    poly = [(940, 1166), (958, 1100), (1092, 1104), (1090, 1170)]
    sl = np.zeros((H, W), np.uint8)
    cv2.fillPoly(sl, [np.int32(poly)], 255, cv2.LINE_AA)
    penlib.shadow_onto(c, sl, off=4, blur=3, opacity=0.3)
    sa = sl.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - sa) + np.array([248, 247, 242], np.float32) * sa
    mm = np.zeros((H, W), np.uint8)
    line(mm, poly + [poly[0]], 2.5, seed)
    text(mm, ["4:15 open", "SERVICE door.", "Key in cupb'd."], 1024, 1126, 15, seed + 1, align="centre", weight=0.17)
    penlib.ink_onto(c, mm, INK)


def key_on_hook(c, hx, hy, seed):
    paper_box(c, hx - 22, hy - 26, hx + 98, hy + 170, (240, 238, 232))
    wash = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(wash, (int(hx), int(hy + 30)), 19, 255, -1, cv2.LINE_AA)
    cv2.rectangle(wash, (int(hx - 5), int(hy + 46)), (int(hx + 5), int(hy + 150)), 255, -1)
    cv2.rectangle(wash, (int(hx + 2), int(hy + 122)), (int(hx + 24), int(hy + 150)), 255, -1)
    wa = (cv2.GaussianBlur(wash, (0, 0), 1.2).astype(np.float32) / 255 * 0.8)[..., None]
    c[:] = c * (1 - wa) + np.array([214, 168, 62], np.float32) * wa
    m = np.zeros(c.shape[:2], np.uint8)
    line(m, [(hx - 8, hy - 18), (hx, hy - 6), (hx, hy + 8), (hx + 6, hy + 12)], 5, seed)
    line(m, ellipse_pts(hx, hy + 30, 19, 19), 5, seed + 1)
    line(m, ellipse_pts(hx, hy + 30, 7, 7), 3, seed + 7)
    line(m, [(hx - 5, hy + 48), (hx - 5, hy + 150)], 4, seed + 2)
    line(m, [(hx + 5, hy + 48), (hx + 5, hy + 150)], 4, seed + 8)
    line(m, [(hx + 5, hy + 122), (hx + 24, hy + 122), (hx + 24, hy + 132), (hx + 14, hy + 132),
             (hx + 14, hy + 140), (hx + 24, hy + 140), (hx + 24, hy + 150), (hx - 5, hy + 150)], 4, seed + 3)
    tx, ty = hx + 30, hy + 52
    line(m, [(hx + 14, hy + 38), (tx + 4, ty + 2)], 2, seed + 4)
    line(m, [(tx, ty), (tx + 62, ty + 3), (tx + 60, ty + 30), (tx - 2, ty + 27), (tx, ty)], 3, seed + 5)
    text(m, ["SERVICE"], tx + 30, ty + 23, 13, seed + 6, align="centre", weight=0.16)
    penlib.ink_onto(c, m, INK)


# ------------------------------------------------------------------ the people
PF, PM, PC, PHAND = M39.PORTER_FEET, M39.PORTER_MOUTH, M39.PORTER_CHIN, M39.PORTER_HAND
HF, HH, HHAND = M39.HEL_FEET, M39.HEL_HEAD, M39.HEL_HAND

# where each beat sits (page px), for the reader's pencil rings in the film
BEAT_SPOTS = {1: (1080, 1220, 190), 2: (700, 1170, 230), 3: (1340, 1000, 260), 4: (480, 1180, 260),
              5: (1700, 1150, 230), 6: (1950, 1130, 210)}
CAT_B = (170, 271)            # cat piece: bottom centre (local px of the cut)
WID_B = (137, 231)            # widow bust: bottom centre
BOY_B = (235, 300)
MIL_F = (330, 560)


def people(c, seed, stage=9):
    p = pieces()
    sb, sf, sh_ = 0.56, 0.62, 0.50
    # waiting room crowd: the widow on the bench, the two boys peering over its back
    lay(c, p["boys"], affine(BOY_B, (330, 1225), 0.50))
    lay(c, p["widow"], affine(WID_B, (230, 1300), 0.62))
    # E0: behind his desk, the memo before him, getting up
    M0 = affine(PF, (1160, FB + 24), sb, deg=4)
    lay(c, p["porter"], M0)
    # E1: at the window, turned to it; the lady on the other side leaning in, gloved hand on the sill
    M1 = affine(PF, (830, F1 + 26), sf, flip=True)
    lay(c, p["porter"], M1)
    MS1 = affine(HHAND, (WALL_X0 - 4, 1222), sh_)
    lay(c, p["helene"], MS1)
    # E2: under the clock, head up
    M2 = affine(PF, (1340, F1 + 26), sf, deg=-12)
    lay(c, p["porter"], M2)
    # E3: she goes, out toward the trains; he walks on (back of the office)
    MS3 = affine(HF, (470, F1 + 30), sh_, flip=True)
    lay(c, p["helene"], MS3)
    M3 = affine(PF, (1490, FB + 24), sb)
    lay(c, p["porter"], M3)
    # E4: at the cupboard, opening it
    M4 = affine(PF, (1660, F1 + 26), sf, deg=4)
    lay(c, p["porter"], M4)
    # E5: before the open cupboard, pencil to chin, in front of the shut SERVICE door
    M5 = affine(PF, (1945, F1 + 26), sf, flip=True)
    lay(c, p["porter"], M5)
    pm = np.zeros((H, W), np.uint8)
    line(pm, [pt(M5, (PHAND[0] + 2, PHAND[1] - 4)), pt(M5, (PC[0] + 4, PC[1] + 4))], 7, seed + 90, tremor=0.2)
    penlib.ink_onto(c, pm, INK)
    # the cat asleep on the parcels by the window, office side
    lay(c, p["cat"], affine(CAT_B, (850, 1392), 0.30, flip=True))
    # faces at the coach windows (clipped to the glass), and a back row on the platform
    wins = list(range(PX0 - 4 + 40, PX1 + 4 - 90, 130))
    for k, (wi, piece, anchor, sc, fl) in enumerate(((1, "boys", BOY_B, 0.36, False), (4, "widow", WID_B, 0.44, False),
                                                    (8, "widow", WID_B, 0.42, True), (11, "boys", BOY_B, 0.34, True),
                                                    (13, "widow", WID_B, 0.42, False))):
        wx = wins[wi]
        clip = np.zeros((H, W), np.float32)
        clip[1632:1768, wx + 2:wx + 88] = 1
        g, a = p[piece]
        paste(c, g, a, affine(anchor, (wx + 45, 1790), sc, flip=fl), clip=clip)
    lay(c, p["miller"], affine(MIL_F, (1700, 2050), 0.52, flip=True))
    lay(c, p["widow"], affine(WID_B, (560, 2060), 0.6))
    # the platform crowd in front
    lay(c, p["miller"], affine(MIL_F, (780, F2 + 6), 0.80))
    lay(c, p["boys"], affine(BOY_B, (1060, 1870), 0.62))
    lay(c, p["widow"], affine(WID_B, (1500, 2010), 0.80, flip=True))
    lay(c, p["cat"], affine(CAT_B, (1450, 2012), 0.42))
    lay(c, p["miller"], affine(MIL_F, (1880, F2 + 6), 0.74, flip=True))
    lay(c, p["boys"], affine(BOY_B, (1240, 2215), 0.70))
    return dict(M0=M0, M1=M1, M2=M2, M3=M3, M4=M4, M5=M5, MS1=MS1, MS3=MS3)


def build(rings=0, legend=True):
    page = cv2.GaussianBlur(k11.wood(), (0, 0), 1.6)
    c = k11.paper()
    c = 236 + cv2.GaussianBlur(c - 238, (0, 0), 2.4) * 0.85
    c *= np.array([1.0, 0.985, 0.95], np.float32)
    m = np.zeros((H, W), np.uint8)
    text(m, ["PUZZLE PICTURE  No. 90"], W / 2, 150, 30, 9001, align="centre", weight=0.14)
    text(m, ["FIND THE KEY"], W / 2, 262, 80, 9002, align="centre", weight=0.15)
    ornament_rule(m, 140, W - 140, 172, 9003)
    penlib.ink_onto(c, m, INK)
    station(c, 9100)
    m = np.zeros((H, W), np.uint8)
    board(c, m, 860, 340, 1340, 430, ["RANDOLPH"], 54, 9200, w=5)
    board(c, m, 450, 800, 680, 880, ["TICKET", "OFFICE"], 24, 9210)
    board(c, m, 330, 520, 620, 740, ["TIMETABLE", "Northbound 4:22", "Southbound 4:48", "White River Jct."], 22, 9220)
    board(c, m, 1940, 850, 2050, 896, ["SERVICE"], 18, 9230, w=3)
    board(c, m, 150, 640, 290, 740, ["TO", "TRAINS"], 24, 9240)
    board(c, m, 1580, 640, 1640, 860, ["NO", "LOI-", "TER-", "ING"], 14, 9250, w=3)
    penlib.ink_onto(c, m, INK)
    memo(c, 9300)
    key_on_hook(c, 1770, 980, 9310)
    coach(c, 9400)
    luggage(c, 9500)
    Ms = people(c, 9600)
    # the four lines
    balloon(c, ["Pardon me — have", "you the right time?"], 26, (520, 970), (pt(Ms["MS1"], HH)[0] + 10, pt(Ms["MS1"], HH)[1] - 24), 9700)
    balloon(c, ["Ten past four,", "by the clock."], 26, (1200, 880), pt(Ms["M2"], PM), 9710)
    hx, hy = pt(Ms["MS3"], HH)
    balloon(c, ["Much obliged!"], 26, (300, 1060), (hx - 6, hy - 24), 9720)
    balloon(c, ["Well, here I am...", "and what for?"], 26, (1830, 640), pt(Ms["M5"], PM), 9730)
    # frame of the picture
    penlib.ink_onto(c, penlib.border_mask((H, W), [(PX0, PY0, PX1, PY1)], 6, 9740), INK)
    penlib.ink_onto(c, penlib.border_mask((H, W), [(PX0 - 12, PY0 - 12, PX1 + 12, PY1 + 12)], 2, 9741), INK)
    if legend:
        m = np.zeros((H, W), np.uint8)
        text(m, ["Somewhere in the crowd the agent's afternoon happens. Find it, in order:"], 130, 2330, 30, 9800)
        L = ["1  He reads the memo at his desk and gets up.",
             "2  A lady at the window asks him the time.",
             "3  He reads the clock: ten past four.",
             "4  She thanks him and goes; he walks on.",
             "5  He opens the cupboard. There hangs the key.",
             "6  Pencil to chin, he forgets why. The key stays; the door stays shut."]
        for k, ln in enumerate(L[:3]):
            text(m, [ln], 150, 2400 + k * 56, 28, 9810 + k)
        for k, ln in enumerate(L[3:5]):
            text(m, [ln], 1130, 2400 + k * 56, 28, 9820 + k)
        for k, ln in enumerate(["6  Pencil to chin, he forgets why.", "    The key stays; the door stays shut."]):
            text(m, [ln], 1130, 2512 + k * 48, 28, 9830 + k)
        penlib.ink_onto(c, m, INK)
        # the answers, printed upside down at the foot
        a = np.zeros((H, W), np.uint8)
        text(a, ["Answers: 1 behind the desk  2 at the ticket window  3 under the clock  4 the waiting room door and the office  "
                 "5 at the open cupboard  6 by the SERVICE door"], W / 2, 2650, 21, 9840, align="centre")
        a = cv2.rotate(a[2610:2670], cv2.ROTATE_180)
        full = np.zeros((H, W), np.uint8)
        full[2610:2670] = a
        penlib.ink_onto(c, full, INK)
    creases(c, W / 2, H / 2)
    # the reader's pencil rings, one per beat found (the film's beat frames)
    if rings:
        rm = np.zeros((H, W), np.uint8)
        ctr = lambda M, q: pt(M, q)
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        spots = {1: [(ctr(Ms["M0"], (240, 300)), 120, 210)],
                 2: [(mid(ctr(Ms["M1"], (240, 300)), ctr(Ms["MS1"], (300, 380))), 230, 230)],
                 3: [(mid(ctr(Ms["M2"], (240, 300)), (1340, 700)), 150, 380)],
                 4: [(ctr(Ms["MS3"], (300, 380)), 120, 200), (ctr(Ms["M3"], (240, 300)), 110, 190)],
                 5: [(mid(ctr(Ms["M4"], (240, 300)), (1790, 1100)), 200, 260)],
                 6: [(ctr(Ms["M5"], (240, 300)), 125, 210)]}
        for k in range(1, rings + 1):
            for (x, y), rx, ry in spots[k]:
                line(rm, ellipse_pts(x, y, rx, ry, 10, 380, 80), 5, 9900 + k, tremor=1.2)
                text(rm, [str(k)], x + rx * 0.8, y - ry * 0.85, 44, 9910 + k, align="centre", weight=0.16)
        penlib.ink_onto(c, rm, np.array([150, 60, 50], np.float32), alpha=0.85)
    Ms_ = cv2.getRotationMatrix2D((W / 2, H / 2), 0.3, 1.0)
    sh = cv2.warpAffine(c, Ms_, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mk = np.zeros((H, W), np.uint8)
    cv2.rectangle(mk, (52, 40), (W - 52, H + 100), 255, -1)
    mk = cv2.warpAffine(mk, Ms_, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, mk, off=10, blur=12, opacity=0.5)
    a = mk.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    page = cv2.GaussianBlur(page, (0, 0), 0.5)
    page = np.clip(np.round(page), 0, 255).astype(np.uint8)
    pen99.folio(page, N, TITLE)
    return page


def main():
    page = build()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90)
    print("jpeg", OUT_JPG.stat().st_size)
    if "beats" in sys.argv:
        frames = [page] + [build(rings=k) for k in range(1, 7)]
        print("beats", save_beats(N, frames))


if __name__ == "__main__":
    main()
