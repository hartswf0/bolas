"""99 ways, page 75 "Dawn to dark" (time and order; medium: stencil-dye).
Twelve views of the same cupboard wall across one day, 5:40 a.m. to 9:15 p.m. In every view the wall clock reads
that view's time and the light changes: a stencilled patch of window sun crosses the wall (rose at dawn, white at
noon, ochre and madder toward evening) and a shade veil, cut with the light patch (and after dark the lamp's glow)
as reserves, deepens from dawn blue to night indigo. The incident happens only in the 4:10 p.m. view (the wide one):
memo on the desk, the question and thanks from the ticket window, the answer under the clock at 4:10, the open
cupboard and the forgetting. After it the cupboard stands open, key on its hook, SERVICE door shut, till dark.
Printed by the page-08 stencil-dye method (each colour a cut stencil with paper ties, misregistration, mottle and
edge pooling, multiplied onto the LoC 1934 sheet); set pieces and figures from the b1m2 cut model; key = ANRC 1922.
Run: python3 -I p75_dawn_to_dark.py [beats]"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p08_lipogram as S  # noqa: E402
from b1m2 import *  # noqa: E402,F401

N, PID, TITLE = 75, "dawn-to-dark", "Dawn to dark"
FLOOR = 640
CLK = (210, 205, 84)
CUP = (400, 300, 200, 340)          # x0, y0, w, h
SDOOR = (760, 250, 160, 390)
LAMP_X = 330

# twelve times (24 h), label, wash tint, veil colour, veil strength, patch tint, patch strength, lamp lit
TIMES = [
    (5 + 40 / 60, "5:40 a.m.", (214, 196, 204), (70, 86, 140), 0.50, (200, 120, 120), 0.20, False),
    (7.0, "7:00 a.m.", (222, 204, 186), (96, 96, 140), 0.34, (214, 150, 110), 0.18, False),
    (8.5, "8:30 a.m.", (226, 208, 168), (110, 100, 100), 0.24, (226, 186, 120), 0.12, False),
    (10.0, "10:00 a.m.", (228, 214, 176), (110, 100, 96), 0.18, None, 0, False),
    (11.5, "11:30 a.m.", (232, 220, 186), (110, 104, 96), 0.13, None, 0, False),
    (13.5, "1:30 p.m.", (232, 216, 178), (112, 100, 90), 0.15, (232, 204, 140), 0.06, False),
    (16 + 10 / 60, "4:10 p.m.", (228, 204, 156), (116, 94, 80), 0.22, (220, 170, 90), 0.16, False),
    (17 + 20 / 60, "5:20 p.m.", (226, 196, 146), (130, 86, 72), 0.30, (216, 150, 70), 0.24, False),
    (18 + 20 / 60, "6:20 p.m.", (222, 180, 140), (140, 72, 64), 0.38, (200, 104, 62), 0.30, False),
    (19 + 10 / 60, "7:10 p.m.", (206, 176, 170), (100, 66, 96), 0.48, (180, 80, 70), 0.30, False),
    (20 + 10 / 60, "8:10 p.m.", (196, 182, 196), (60, 70, 120), 0.62, None, 0, True),
    (21.5, "9:30 p.m.", (190, 180, 196), (30, 40, 88), 0.84, None, 0, True),
]
INCIDENT = 6

# patch keyframes (hour, cx, cy, w, h)
PATCH = [(5.67, 905, 160, 250, 70), (7.0, 830, 225, 220, 110), (8.5, 730, 320, 190, 150), (10.0, 630, 420, 170, 170),
         (11.5, 530, 520, 150, 150), (13.0, 440, 565, 150, 120), (14.5, 350, 485, 170, 160),
         (16.17, 265, 385, 200, 170), (17.5, 185, 285, 240, 150), (18.67, 115, 195, 300, 100)]


def patch_at(t):
    if t > 19.2:
        return None
    for (a, *pa), (b, *pb) in zip(PATCH, PATCH[1:]):
        if a <= t <= b:
            u = (t - a) / (b - a)
            return [p + (q - p) * u for p, q in zip(pa, pb)]
    return PATCH[0][1:] if t < PATCH[0][0] else PATCH[-1][1:]


def patch_mask(t, W, H, ox, oy):
    """The sun through the platform window: two-by-two panes, sheared by the sun's height (world units)."""
    p = patch_at(t)
    m = np.zeros((H, W), np.uint8)
    if p is None:
        return m
    cx, cy, w, h = p
    sk = (cx - 500) * 0.45
    bar = 9
    for i in range(2):
        for j in range(2):
            x0 = cx - w / 2 + i * (w / 2 + bar / 2)
            x1 = x0 + w / 2 - bar / 2
            y0 = cy - h / 2 + j * (h / 2 + bar / 2)
            y1 = y0 + h / 2 - bar / 2
            sh0, sh1 = sk * (y0 - cy) / h, sk * (y1 - cy) / h
            poly = np.array([(x0 + sh0, y0), (x1 + sh0, y0), (x1 + sh1, y1), (x0 + sh1, y1)]) - (ox, oy)
            cv2.fillPoly(m, [np.int32(poly * 4)], 255, cv2.LINE_AA, shift=2)
    m = cv2.GaussianBlur(m, (0, 0), 2.5)
    m[FLOOR - oy:] = np.where(m[FLOOR - oy:] > 0, m[FLOOR - oy:] // 2, 0)  # patch dies on the floor edge
    return m


def pendant(lit):
    s = [R_(LAMP_X - 2, -400, LAMP_X + 2, 92, "lampcord"),
         Shape([(LAMP_X - 44, 132), (LAMP_X - 20, 92), (LAMP_X + 20, 92), (LAMP_X + 44, 132)], "lamp", smooth=False)]
    if lit:
        s.append(Shape([(LAMP_X - 14, 132), (LAMP_X + 14, 132), (LAMP_X + 10, 142), (LAMP_X - 10, 142)], "bulb", smooth=False))
    return s


def timetable():
    s = [R_(1040, 250, 1240, 480, "board")]
    for k in range(5):
        s.append(R_(1062, 286 + k * 38, 1218, 306 + k * 38, "slit", hole=True, z=1))
    return s


def wall_set(t, people):
    """World shapes of the wall at hour t. people: None or 'incident' (the 4:10 view)."""
    lit = TIMES[[r[0] for r in TIMES].index(t)][7] if t in [r[0] for r in TIMES] else t > 19.5
    hh, mm = int(t) % 12 or 12, int(round((t - int(t)) * 60))
    fig = clock(CLK[0], CLK[1], CLK[2], hh=hh, mm=mm, swing=8 if int(t * 6) % 2 else -8)
    opened = t >= 16.1
    cup, _ = cupboard(*CUP, open_deg=112 if opened else 0)
    fig += cup
    fig += service_door(*SDOOR)
    fig += pendant(lit)
    fig += timetable()
    ws, sill = window(-460, 150, 290, FLOOR - 150, sill=FLOOR - 236, header=62)
    for s_ in ws:
        s_.role = "window"
    fig += ws
    fig += desk(-760, FLOOR - 170, 230, FLOOR)
    if people == "incident":
        fig += stranger(-315, sill + 4, face=1, scale=0.70, glove=True)
        fig += agent(70, FLOOR + 4, face=1, scale=0.42, legs=(3, -3), tilt=-24, sh=-6, el=24, pencil_deg=200)
        fig += agent(668, FLOOR + 4, face=-1, scale=0.42, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6)
    elif people == "opening":
        fig += agent(668, FLOOR + 4, face=-1, scale=0.42, legs=(10, -8), sh=70, el=20, pencil_deg=200)
    return fig, opened


def roles_mask(fig, roles, W, H, off):
    HOLES = {"slit", "dial", "pendwin", "inside", "glass", "pin"}
    return raster(fig, W, H, roles=roles | HOLES, facet=0.8, offset=off)


def view(Wpx, Hpx, wx0, wy0, wx1, wy1, k, people=None, text=True, cup_deg=None, seed=7500):
    """Print one view of the wall at TIMES[k]; world window (wx0, wy0)-(wx1, wy1) scaled to Wpx x Hpx."""
    t, label, wash, vcol, vstr, pcol, pstr, lit = TIMES[k]
    wx0, wy0, wx1, wy1 = int(round(wx0)), int(round(wy0)), int(round(wx1)), int(round(wy1))
    fig, opened = wall_set(t, people)
    if cup_deg is not None:                                 # the opening beat: replace the cupboard
        fig = [s for s in fig if s.role not in ("cupboard", "door", "shelf", "inside") and
               not (s.role == "slit" and CUP[0] <= s.pts[:, 0].mean() <= CUP[0] + CUP[2] and s.pts[:, 1].mean() > 280)]
        cup, _ = cupboard(*CUP, open_deg=cup_deg)
        fig += cup
        opened = cup_deg > 60
    Ww, Hw = int(wx1 - wx0), int(wy1 - wy0)
    off = (-wx0, -wy0)
    L = {
        "indigo": roles_mask(fig, {"waistcoat", "hat", "window", "board"}, Ww, Hw, off),
        "madder": roles_mask(fig, {"coat", "bow", "tie", "clock"}, Ww, Hw, off),
        "umber": roles_mask(fig, {"trousers", "hair", "pencil", "hand", "eye", "glass_arm", "garter", "button", "lampcord"}, Ww, Hw, off),
        "skin": roles_mask(fig, {"skin", "skin_s", "ear", "skin_far", "glove"}, Ww, Hw, off),
        "ochre": roles_mask(fig, {"cupboard", "door", "shelf", "desk", "lamp", "bulb"}, Ww, Hw, off),
        "verdi": roles_mask(fig, {"sdoor"}, Ww, Hw, off),
    }
    wm = np.zeros((Hw, Ww), np.uint8)
    wm[:max(0, FLOOR - wy0)] = 255
    fm = 255 - wm
    pm = patch_mask(t, Ww, Hw, wx0, wy0)
    glow = np.zeros((Hw, Ww), np.uint8)
    if lit:
        cv2.ellipse(glow, (int(LAMP_X - wx0), int(300 - wy0)), (300, 240), 0, 0, 360, 255, -1, cv2.LINE_AA)
        cv2.fillPoly(glow, [np.int32(np.array([(LAMP_X - 40, 130), (LAMP_X + 40, 130), (LAMP_X + 300, 560),
                                                (LAMP_X - 300, 560)]) - (wx0, wy0))], 255, cv2.LINE_AA)
        glow = cv2.GaussianBlur(glow, (0, 0), 40)
    rs = lambda m: cv2.resize(m, (Wpx, Hpx), interpolation=cv2.INTER_AREA)
    c = np.ones((Hpx, Wpx, 3), np.float32) * 255
    sd = seed + 13 * k
    S.dye(c, rs(wm), np.array(wash, np.float32), sd, strength=0.55, bridge=False)
    S.dye(c, rs(fm), S.VERDI, sd + 1, shift=S.SHIFT["verdi"])
    col = {"indigo": S.INDIGO, "madder": S.MADDER, "umber": S.UMBER, "skin": S.SKIN, "ochre": S.OCHRE, "verdi": S.VERDI}
    for i, name in enumerate(("ochre", "verdi", "indigo", "madder", "skin", "umber")):
        S.dye(c, rs(L[name]), col[name], sd + 3 + 17 * i, shift=S.SHIFT[name], bridge=name != "skin")
    if opened:
        cx0, cy0, cw, ch = CUP
        deg = 112 if cup_deg is None else cup_deg
        ex = cx0 + cw * math.cos(math.radians(deg))
        kx, ky = (cx0 + ex) / 2 + 2, cy0 + 110
        km = np.zeros((Hw, Ww), np.uint8)
        paste_mask(km, key_alpha(), kx - wx0, ky - wy0, 0.25)
        S.dye(c, rs(km), S.OCHRE, sd + 140, shift=S.SHIFT["ochre"])
    if pcol is not None and pstr > 0:
        S.dye(c, rs(pm), np.array(pcol, np.float32), sd + 150, strength=pstr, bridge=False)
    veil = np.clip(255 - pm.astype(np.int32) - glow.astype(np.int32), 0, 255).astype(np.uint8)
    S.dye(c, rs(veil), np.array(vcol, np.float32), sd + 160, strength=vstr, bridge=False)
    c *= S.SHEET[:Hpx, :Wpx].mean(axis=2, keepdims=True) / S.SHEET.mean()
    sc = Wpx / Ww

    def P(x, y):
        return int((x - wx0) * sc), int((y - wy0) * sc)

    if text:
        paper = np.array([248, 244, 230], np.float32)
        # SERVICE card on its door, and the key tag if the key shows
        x, y = P(SDOOR[0] + 30, SDOOR[1] + 34)
        slip(c, x, y, ["SERVICE"], max(14, int(30 * sc)), sd + 5, paper=paper, pad=(int(14 * sc) + 4, int(5 * sc) + 2), shadow=0.3)
        if opened:
            deg = 112 if cup_deg is None else cup_deg
            ex = CUP[0] + CUP[2] * math.cos(math.radians(deg))
            kx, ky = (CUP[0] + ex) / 2 + 2, CUP[1] + 110
            hk = np.zeros(c.shape[:2], np.uint8)
            penlib.brush_line(hk, [P(kx - 18, ky - 92), P(kx + 3, ky - 92), P(kx + 3, ky - 80)], max(3, int(6 * sc)), sd + 3)
            comp(c, hk, S.UMBER)
            x, y = P(kx + 6, ky + 28)
            slip(c, x, y, ["SERVICE"], max(11, int(18 * sc)), sd + 4, paper=paper, pad=(int(10 * sc) + 2, 3), tilt=8, shadow=0.3)
        if wx0 < -200:                                       # the ticket window header lettering
            lm = np.zeros(c.shape[:2], np.uint8)
            l = letter(["TICKET OFFICE"], max(14, int(30 * sc)), sd + 6, weight=0.17)
            put_mask(lm, l, *P(-315, 150 + 33))
            comp(c, lm, np.array([246, 240, 222], np.float32))
        if wx0 < -700:                                       # the memo on the desk
            x, y = P(-720, FLOOR - 250)
            slip(c, x, y, ["4:15 - open", "SERVICE door.", "Key in cupboard."], int(24 * sc) + 2, sd + 7, paper=paper,
                 tilt=-4, shadow=0.35)
    return c, P


def time_slip(c, label, seed, cap=34):
    slip(c, 14, 12, [label], cap, seed, paper=np.array([246, 241, 226], np.float32), pad=(16, 8), shadow=0.32)


# ------------------------------------------------------------------ the page
SW, SH = 633, 450
COLX = (110, 783, 1456)
ROWY = (110, 590, 1070, 1800, 2280)
WIDE_H = 700
LW = 970
SMALL_WORLD = (0, 0, 1000, 710)


def boxes():
    b = []
    for r in (0, 1):
        for cx in COLX:
            b.append((cx, ROWY[r], cx + SW, ROWY[r] + SH))
    b.append((110, ROWY[2], 2090, ROWY[2] + WIDE_H))
    for cx in COLX:
        b.append((cx, ROWY[3], cx + SW, ROWY[3] + SH))
    for cx in (110, 1120):
        b.append((cx, ROWY[4], cx + LW, ROWY[4] + SH))
    return b


BOXES = boxes()


def world_for(k, w, h):
    if k == INCIDENT:
        ww = 860 * w / h
        return (-880, -150, -880 + ww, 710)
    if w == LW:
        ww = 710 * w / h
        return (500 - ww / 2 + 120, 0, 500 + ww / 2 + 120, 710)
    return SMALL_WORLD


def incident_text(c, P, sd):
    cap = 40
    balloon(c, ["Pardon me -", "have you the", "right time?"], cap, (400, 118), P(-300, 255), sd + 21)
    balloon(c, ["Ten past four,", "by the clock."], cap, (730, 120), P(102, 300), sd + 22)
    balloon(c, ["Much", "obliged!"], cap, (190, 300), P(-345, 300), sd + 23)
    balloon(c, ["Well, here I am...", "and what for?"], cap, (1720, 330), P(690, 300), sd + 24)


def build(n=12, state=None):
    state = state or {}
    page = S.SHEET.copy()
    for k, (x0, y0, x1, y1) in enumerate(BOXES[:n]):
        w, h = x1 - x0, y1 - y0
        wx0, wy0, wx1, wy1 = world_for(k, w, h)
        c, P = view(w, h, wx0, wy0, wx1, wy1, k, people="incident" if k == INCIDENT else None)
        if k == INCIDENT:
            incident_text(c, P, 7600)
        time_slip(c, TIMES[k][1], 7700 + k, cap=40 if k == INCIDENT else 34)
        page[y0:y1, x0:x1] = c
    frame_border(page, BOXES[:n], w=10, seed=7599)
    return page


# ------------------------------------------------------------------ beats: one view held while the day runs
BW, BH = 960, 1242


def beat(k, people=None, cup_deg=None, line=False):
    ww = 760
    wx0 = 120
    hh = ww * BH / BW
    wy0 = FLOOR + 70 - hh
    c, P = view(BW, BH, wx0, wy0, wx0 + ww, wy0 + hh, k, people=people, cup_deg=cup_deg, seed=7800)
    if line:
        balloon(c, ["Well, here I am...", "and what for?"], 50, (560, 240), P(690, 300), 7811)
    time_slip(c, TIMES[k][1] if not line else "4:11 p.m.", 7820 + k, cap=50)
    frame_border(c, [(14, 14, BW - 14, BH - 14)], w=10, seed=7830)
    return c


def beats():
    fr = [beat(0), beat(2), beat(4), beat(5), beat(6, people="opening", cup_deg=48),
          beat(6, people="incident", line=True), beat(8), beat(11)]
    return fr


def check():
    hours = [r[0] for r in TIMES]
    assert len(TIMES) == 12 and hours == sorted(hours)
    assert TIMES[INCIDENT][1] == "4:10 p.m."
    light = [(r[2], r[3], r[4], tuple(patch_at(r[0]) or ())) for r in TIMES]
    assert all(a != b for a, b in zip(light, light[1:]))      # light changes between every pair of views
    return True


if __name__ == "__main__":
    check()
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        print("beats", save_beats(N, beats()))
