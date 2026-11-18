"""Page 89 Crossing routes (formal / Oulipian rule; medium: shadow-puppet).

A 3x3 grid. Every cell but the centre is two shadow screens: an upper, lamp-warm OFFICE screen that belongs to the
agent's route and a lower, daylight-cool PLATFORM screen that belongs to the stranger's route.
Read ACROSS (row by row, upper screens) the cells tell his afternoon in nine beats; read DOWN (column by column,
lower screens) they tell hers in nine beats. Cell (2,2) is the fifth cell both ways, and there the two screens
become one: the cross-section of the ticket window where they meet, at the question.
Black cut-paper puppets (b1m2 model; the stranger's full-length platform puppet authored here), cut set pieces on
paper screens carrying the LoC 1934 sheet fibre (page 05 screen tools), lettering in the shared pen hand.
Run: python3 -I p89_crossing_routes.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p05_noir as p5
from p05_noir import sil, window_letters, paper_card, brass_key, hook

N, PID, TITLE = 89, "crossing-routes", "Crossing routes"
SHEET = pen99.sheet99()
CW, G = 640, 30
TOP = 236
CH = (2730 - TOP - 2 * G) // 3          # 811
UH, DG = 452, 14                        # upper screen height, divider gap
LH = CH - UH - DG                       # lower screen height
XS = [110 + c * (CW + G) for c in range(3)]
YS = [TOP + r * (CH + G) for r in range(3)]
COOL = np.array([0.80, 0.90, 1.04], np.float32)
GREY = np.array([60, 60, 62], np.float32)


# ------------------------------------------------------------------ screens
def warm(w, h, ox, oy, hot=(0.5, 0.5)):
    return p5.screen(w, h, ox, oy, hot=hot, spread=1.25, slats=None)


def cool(w, h, ox, oy, hot=(0.5, 0.35)):
    img = p5.screen(w, h, ox, oy, hot=hot, spread=1.6, slats=None)
    img = img * COOL[None, None] + 6
    return np.clip(img, 0, 255)


def far_clip(img, shapes, box, blur=2.0, alpha=0.8):
    """A puppet held back beyond the glass: soft and grey, seen only inside the glass box."""
    m = raster(shapes, img.shape[1], img.shape[0], holes=False)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    clip = np.zeros_like(m)
    x0, y0, x1, y1 = [int(v) for v in box]
    clip[max(0, y0):y1, max(0, x0):x1] = 255
    m = (m.astype(np.float32) * clip / 255).astype(np.uint8)
    comp(img, m, GREY, alpha)


# ------------------------------------------------------------------ the stranger, full length (HANDMADE, for her own screens)
S_LONGCOAT = [(-62, -128), (-22, -148), (14, -150), (42, -128), (60, -90), (52, -10), (70, 120), (82, 250),
              (-80, 250), (-66, 120), (-58, -10), (-74, -80)]
S_SLEEVE = [(-18, -6), (20, -8), (24, 90), (18, 170), (-16, 170), (-22, 90)]
S_SHOE = [(-14, 0), (40, 2), (44, 18), (-14, 18)]
VALISE = [(-46, 0), (46, 0), (50, 8), (50, 84), (-50, 84), (-50, 8)]


def walker(x, floor, face=1, s=0.42, step=0.0, arm=10, bag=True, wrist=False, tilt=0, glove=False):
    """Her whole figure (coat to the calf, legs, shoes, sleeve, valise). step: stride angle in degrees.
    wrist=True: the far forearm raised to look at her wristwatch."""
    flip = face < 0
    hip = 418                                         # hem 250, legs 230-400, shoe 18
    B = Mx(x, floor - hip * s, 0, s, flip)
    out = []
    for k, a in enumerate((step, -step)):
        L = B @ Mx(-4 + 10 * k, 230) @ Mx(0, 0, -a)
        out.append(Shape(tf(L, bar_pts((0, 0), (0, 170), 26)), "leg", smooth=False, z=-1))
        out.append(Shape(tf(L @ Mx(0, 166), S_SHOE), "shoe", smooth=False, z=-1))
    out.append(Shape(tf(B, S_LONGCOAT), "coat"))
    out.append(Shape(tf(B, S_COLLAR), "collar", z=1))
    Hm = B @ Mx(0, -148) @ Mx(0, 0, tilt) @ Mx(0, 148)
    out += [Shape(tf(Hm, S_HEAD), "skin_s"), Shape(tf(Hm, S_HAT), "hat", z=1), Shape(tf(Hm, S_BOW), "bow", z=2),
            Shape(tf(Hm, circle_pts(32, -196, 4.5, 10)), "eye", hole=True, z=3)]
    U = B @ Mx(8, -118) @ Mx(0, 0, -arm)
    out.append(Shape(tf(U, S_SLEEVE), "sleeve", z=4))
    if bag:
        out.append(Shape(tf(U @ Mx(0, 176), bar_pts((0, 0), (0, 40), 8)), "handle", smooth=False, z=4))
        out.append(Shape(tf(U @ Mx(0, 212) @ Mx(0, 0, arm), VALISE), "valise", smooth=False, z=4))
        out.append(Shape(tf(U @ Mx(0, 212) @ Mx(0, 0, arm), rect(-50, 30, 50, 36)), "strap", hole=True, smooth=False, z=5))
    if wrist:
        W_ = B @ Mx(30, -100) @ Mx(0, 0, -70)
        out.append(Shape(tf(W_, bar_pts((0, 0), (0, 110), 30)), "fore", smooth=False, z=5))
        W2 = W_ @ Mx(0, 104) @ Mx(0, 0, 120)
        out.append(Shape(tf(W2, bar_pts((0, 0), (0, 92), 24)), "fore", smooth=False, z=5))
        out.append(Shape(tf(W2 @ Mx(0, 40), circle_pts(0, 0, 11, 10)), "watch", hole=True, z=6))
    if glove:
        G_ = B @ Mx(30, -100) @ Mx(0, 0, -110)
        out.append(Shape(tf(G_, bar_pts((0, 0), (0, 150), 28)), "fore", smooth=False, z=5))
        out.append(Shape(tf(G_ @ Mx(0, 150), circle_pts(0, 0, 18, 10)), "knuckle", z=5))
    return out


def bench(x0, x1, seat, floor):
    return [R_(x0, seat, x1, seat + 14, "bench"), R_(x0 + 10, seat - 70, x1 - 10, seat - 58, "bench"),
            R_(x0 + 10, seat - 40, x1 - 10, seat - 30, "bench"),
            R_(x0 + 16, seat - 70, x0 + 28, floor, "bench"), R_(x1 - 28, seat - 70, x1 - 16, floor, "bench")]


def platform(img, w, h, edge=True, sign=None, seed=0):
    """Platform floor and rail edge; optional RANDOLPH board on posts."""
    sh = [R_(-10, h - 22, w + 10, h + 10, "deck")]
    for k in range(0, w + 60, 46):
        sh.append(R_(k, h - 22, k + 4, h - 10, "slit", hole=True, z=1))
    if sign is not None:
        sx, sy, sw = sign
        sh += [R_(sx, sy, sx + sw, sy + 48, "sign"), R_(sx + 20, sy + 48, sx + 30, sy + 120, "sign"),
               R_(sx + sw - 30, sy + 48, sx + sw - 20, sy + 120, "sign")]
    sil(img, sh)
    if sign is not None:
        m = letter(["RANDOLPH"], 30, seed, weight=0.17)
        lm = np.zeros(img.shape[:2], np.uint8)
        put_mask(lm, m, sx + sw / 2, sy + 26)
        comp(img, lm, np.array([226, 230, 236], np.float32))


def station_window(img, x0, y0, ww, wh, seed, agent_pose=None):
    """The ticket window seen from the platform: the station wall around it, glass, the agent grey beyond."""
    ws, sill = window(x0, y0, ww, wh, sill=y0 + wh * 0.66, header=46)
    wall = [R_(x0 - 30 - 400, y0 - 400, x0 - 30, y0 + wh + 400, "wall"), R_(x0 + ww + 30, y0 - 400, x0 + ww + 400, y0 + wh + 400, "wall")]
    img *= 1.0
    glass = (x0, y0 + 46, x0 + ww, sill)
    gm = np.zeros(img.shape[:2], np.uint8)
    gm[int(glass[1]):int(glass[3]), int(glass[0]):int(glass[2])] = 255
    comp(img, gm, np.array([188, 196, 206], np.float32), 0.35)
    if agent_pose is not None:
        ap = dict(agent_pose)
        ap["floor"] = sill + ap.pop("below_sill", 150)
        far_clip(img, agent(**ap), glass)
    sil(img, ws + [R_(x0 - 30, y0 - 200, x0 + ww + 30, y0, "wall")], blur=0.6)
    sil(img, wall, alpha=0.55)
    m = letter(["TICKET OFFICE"], 26, seed, weight=0.17)
    sc = min(1.0, (ww + 30) / m.shape[1])
    m = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    lm = np.zeros(img.shape[:2], np.uint8)
    put_mask(lm, m, x0 + ww / 2, y0 + 25)
    comp(img, lm, np.array([226, 214, 186], np.float32))
    return sill


def office_window(img, x0, y0, ww, wh, seed, pose=None):
    ws, sill = window(x0, y0, ww, wh, sill=y0 + wh * 0.6, header=54)
    if pose is not None:
        far_clip(img, stranger(x0 + ww / 2 + pose.get("dx", 0), sill + 20, face=pose.get("face", 1),
                               scale=pose.get("scale", 0.75), tilt=pose.get("tilt", 0), glove=pose.get("glove", False)),
                 (x0, y0 + 54, x0 + ww, sill), blur=2.2, alpha=0.86)
    sil(img, ws)
    window_letters(img, x0, y0, ww, 54, seed)
    return sill


# ------------------------------------------------------------------ his route (upper screens), row by row
AS = 0.46
AF = UH - 12


def A1(img):   # E0 at the desk, the memo before him
    sh = desk(60, AF - 160, 360, AF) + lamp(470, AF - 330, 170)
    sh += agent(220, AF + 34, face=1, scale=AS, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
                pencil_deg=60, far_arm=(30, 60))
    sh += clock(560, 86, 46, hh=4, mm=9, swing=-5)
    sil(img, sh)
    slip(img, 70, AF - 236, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 27, 8911, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)


def A2(img):   # E0 he rises and sets off
    sh = desk(-180, AF - 160, 330, AF)
    sh += agent(330, AF, face=1, scale=AS, legs=(14, -12), sh=-14, el=20, lean=6, pencil_deg=200, far_arm=(16, 18))
    sil(img, sh)


def A3(img):   # E0 across the office toward the cupboard and the SERVICE door
    c, _ = cupboard(330, 150, 150, AF - 150)
    sh = c + service_door(515, 110, 110, AF - 110)
    sh += agent(200, AF, face=1, scale=AS, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200, far_arm=(24, 22))
    sil(img, sh)
    paper_card(img, 570, 176, ["SERVICE"], 22, 8931)


def A4(img):   # a rap at the glass: he turns to the window
    office_window(img, 40, 110, 230, AF - 110, 8941, {"glove": True, "dx": -6})
    sil(img, agent(470, AF, face=-1, scale=AS, legs=(8, -8), sh=8, el=20, tilt=-2, pencil_deg=190))


def A6(img):   # E2 he reads the clock, 4:10, and answers
    sh = clock(520, 96, 56, hh=4, mm=10, swing=6)
    sh += agent(140, AF, face=1, scale=AS, legs=(4, -4), sh=6, el=16, tilt=-24, pencil_deg=190, lean=-3)
    sil(img, sh)
    balloon(img, ["Ten past four,", "by the clock."], 38, (400, 330), (196, 122), 8961, tail_w=0.16)


def A7(img):   # E3 the thanks from the glass; she turns away
    office_window(img, 40, 120, 230, AF - 120, 8971, {"face": -1, "dx": -30, "tilt": -6})
    sil(img, agent(560, AF, face=-1, scale=AS, legs=(10, -10), sh=-8, el=18, pencil_deg=200, lean=2))
    balloon(img, ["Much obliged!"], 38, (420, 250), (200, 230), 8972, tail_w=0.24)


def A8(img):   # E4 the cupboard open, the key on its hook, tagged SERVICE
    p5.cupboard_scene(img, CW, UH, 110, 140, 210, AF - 160, 112, 0.25, sdoor=False)
    sil(img, agent(480, AF, face=-1, scale=AS, legs=(4, -4), sh=34, el=-20, wr=0, pencil_deg=200, tilt=4))


def A9(img):   # E5 pencil to chin; the key stays on its hook; the SERVICE door stays shut
    p5.cupboard_scene(img, CW, UH, 30, 210, 170, AF - 220, 112, 0.18, sdoor=True, sd_x=420)
    sil(img, agent(270, AF, face=-1, scale=AS, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2))
    balloon(img, ["Well, here I am...", "and what for?"], 32, (470, 74), (300, 92), 8991, tail_w=0.20)


# ------------------------------------------------------------------ her route (lower screens), column by column
SF = LH - 22
SS = 0.40


def S1(img):   # she comes along the platform with her valise
    platform(img, CW, LH, sign=(360, 34, 230), seed=8911)
    sil(img, walker(150, SF, face=1, s=SS, step=16, arm=8))


def S2(img):   # valise set down, she looks at her wristwatch
    platform(img, CW, LH)
    sh = walker(300, SF, face=1, s=SS, step=0, arm=4, bag=False, wrist=True, tilt=18)
    sh += [Shape(tf(Mx(200, SF - 84 * SS * 1.0 - 2, 0, SS), VALISE), "valise", smooth=False)]
    sil(img, sh)


def S3(img):   # she walks up to the ticket window
    platform(img, CW, LH)
    station_window(img, 400, 40, 180, SF - 60, 8931)
    sil(img, walker(200, SF, face=1, s=SS, step=18, arm=10))


def S4(img):   # she raps at the glass; beyond it he is crossing the office
    platform(img, CW, LH)
    station_window(img, 330, 40, 200, SF - 60, 8941,
                   dict(x=470, floor=0, face=1, scale=0.30, legs=(14, -12), sh=-10, el=20, pencil_deg=200))
    sil(img, walker(200, SF, face=1, s=SS, arm=4, bag=False, glove=True))


def S6(img):   # she hears the answer through the glass, and sets her watch by it
    platform(img, CW, LH)
    station_window(img, 40, 40, 200, SF - 60, 8961,
                   dict(x=170, floor=0, face=1, scale=0.30, tilt=-24, sh=6, el=16, pencil_deg=190))
    sil(img, walker(390, SF, face=-1, s=SS, arm=4, bag=False, wrist=True, tilt=16))
    balloon(img, ["Ten past four,", "by the clock."], 30, (470, 66), (210, 120), 8962, tail_w=0.20)


def S7(img):   # E3 the thanks
    platform(img, CW, LH)
    station_window(img, 40, 40, 200, SF - 60, 8971,
                   dict(x=150, floor=0, face=-1, scale=0.30, sh=8, el=20, pencil_deg=190))
    sil(img, walker(370, SF, face=-1, s=SS, arm=8))
    balloon(img, ["Much obliged!"], 32, (480, 62), (380, 140), 8972, tail_w=0.24)


def S8(img):   # she goes along the platform, away from the window
    platform(img, CW, LH)
    station_window(img, 40, 40, 180, SF - 60, 8981)
    sil(img, walker(400, SF, face=1, s=SS, step=18, arm=10))


def S9(img):   # she waits on the bench for her train, watch set; the window behind her empty
    platform(img, CW, LH, sign=(30, 30, 230), seed=8991)
    sh = bench(320, 600, SF - 70, SF)
    sh += walker(250, SF, face=1, s=SS, step=0, arm=6)
    sil(img, sh)


# ------------------------------------------------------------------ the centre: one screen, both routes
def C5(w, h, ox, oy):
    a = warm(w, h, ox, oy, hot=(0.3, 0.45))
    b = cool(w, h, ox, oy, hot=(0.7, 0.4))
    wx0, wx1, gy0, gy1 = 296, 356, 330, 560
    t = np.clip((np.arange(w) - wx0) / float(wx1 - wx0), 0, 1)[None, :, None]
    img = a * (1 - t) + b * t
    floor = h - 16
    sil(img, agent(205, floor, face=1, scale=0.50, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190))
    sil(img, walker(452, floor, face=-1, s=0.56, arm=4, bag=False, tilt=0))
    glass = np.zeros(img.shape[:2], np.uint8)
    glass[gy0:gy1, wx0:wx1] = 255
    comp(img, glass, np.array([200, 206, 212], np.float32), 0.45)
    sh = [R_(wx0, -20, wx1, gy0 - 50, "wall"), R_(wx0, gy1 + 22, wx1, h + 20, "wall"),
          R_(wx0 - 8, gy0 - 50, wx1 + 8, gy0, "frame"), R_(wx0 + 24, gy0, wx1 - 24, gy1, "bar"),
          R_(wx0 - 90, gy1, wx1 + 90, gy1 + 22, "counter"), R_(wx0 - 214, gy0 - 120, wx0, gy0 - 60, "header")]
    sil(img, sh)
    m = letter(["TICKET OFFICE"], 24, 8951, weight=0.17)
    lm = np.zeros(img.shape[:2], np.uint8)
    put_mask(lm, m, wx0 - 104, gy0 - 88)
    comp(img, lm, np.array([226, 214, 186], np.float32))
    balloon(img, ["Pardon me —", "have you the", "right time?"], 44, (492, 150), (500, 345), 8952, tail_w=0.22)
    return img


A_FN = {(0, 0): A1, (0, 1): A2, (0, 2): A3, (1, 0): A4, (1, 2): A6, (2, 0): A7, (2, 1): A8, (2, 2): A9}
S_FN = {(0, 0): S1, (1, 0): S2, (2, 0): S3, (0, 1): S4, (2, 1): S6, (0, 2): S7, (1, 2): S8, (2, 2): S9}


def tag(page, x, y, text, paper, seed):
    slip(page, x, y, [text], 30, seed, paper=paper, pad=(18, 8), align="centre", shadow=0.3)


def arrow(page, x, y, d, size=22):
    """A cut black arrowhead pointing right ('r') or down ('d'), laid on the gutter."""
    if d == "r":
        pts = [(x - size * 0.6, y - size), (x + size * 0.8, y), (x - size * 0.6, y + size)]
    else:
        pts = [(x - size, y - size * 0.6), (x, y + size * 0.8), (x + size, y - size * 0.6)]
    m = np.zeros(page.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    comp(page, m, INK)


HIS_TAG = np.array([240, 228, 200], np.float32)
HER_TAG = np.array([214, 226, 238], np.float32)


def build(a_upto=9, s_upto=9, legend=True):
    page = SHEET.copy()
    boxes = []
    for r in range(3):
        for c in range(3):
            x0, y0 = XS[c], YS[r]
            ai, si = 3 * r + c + 1, 3 * c + r + 1
            if (r, c) == (1, 1):
                boxes.append((x0, y0, x0 + CW, y0 + CH))
                if ai <= a_upto or si <= s_upto:
                    page[y0:y0 + CH, x0:x0 + CW] = C5(CW, CH, x0, y0)
                continue
            boxes.append((x0, y0, x0 + CW, y0 + UH))
            boxes.append((x0, y0 + UH + DG, x0 + CW, y0 + CH))
            if ai <= a_upto:
                img = warm(CW, UH, x0, y0)
                A_FN[(r, c)](img)
                page[y0:y0 + UH, x0:x0 + CW] = img
            if si <= s_upto:
                img = cool(CW, LH, x0, y0 + UH + DG)
                S_FN[(r, c)](img)
                page[y0 + UH + DG:y0 + CH, x0:x0 + CW] = img
    frame_border(page, boxes, w=11, seed=8900)
    # route marks: numbered tags (his warm, top-left of the upper screen; hers cool, bottom-left of the lower)
    for r in range(3):
        for c in range(3):
            x0, y0 = XS[c], YS[r]
            ai, si = 3 * r + c + 1, 3 * c + r + 1
            if ai <= a_upto:
                tag(page, x0 + 14, y0 + 14, f"{ai}", HIS_TAG, 8800 + ai)
            if si <= s_upto:
                tag(page, x0 + 14, y0 + CH - 68 if (r, c) != (1, 1) else y0 + CH - 68, f"{si}", HER_TAG, 8820 + si)
            if c < 2 and ai < a_upto:
                arrow(page, x0 + CW + G / 2, y0 + UH / 2 if (r, c + 1) != (1, 1) and (r, c) != (1, 1) else y0 + UH / 2, "r")
            if r < 2 and si < s_upto:
                arrow(page, x0 + CW / 2, y0 + CH + G / 2, "d")
    if legend:
        m1 = letter_left(["Read ACROSS, the lamp-lit screens: his route, 1 to 9."], 40, 8890)
        m2 = letter_left(["Read DOWN, the daylight screens: her route, 1 to 9. They cross at 5."], 40, 8891)
        lm = np.zeros(page.shape[:2], np.uint8)
        blit_mask(lm, m1, 150, 98)
        blit_mask(lm, m2, 150, 154)
        penlib.ink_onto(page, lm)
        arrow(page, 130, 130, "r", 16)
        arrow(page, 130, 184, "d", 16)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "CH", CH, "LH", LH)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for a, s, lg in ((0, 0, True), (4, 0, True), (4, 4, True), (5, 5, True), (9, 5, True), (9, 9, True)):
            p = np.clip(np.round(build(a, s, lg)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
