"""99 ways, page 84 "Thirty years on" (time and order; medium: charcoal-card).
The office in 1967, disused: the key still on its hook, the door still closed; the 1937 beats appear as pale figures
in the same room.
Every board is the same 1967 room, built in dark charcoal cards (charcoal99 kit) on the teuf-teuf rock wall ground
(Cueva de las manos, CC BY-SA 3.0): ticket window boarded with planks, the desk under a dust sheet, the wall clock
stopped at 11:52, a 1967 calendar card, cobwebs, a dropped CLOSED card; the cupboard door hangs open and the brass key
(the ANRC 1922 cutout cut as a card, dulled with dust) still hangs on its hook; the SERVICE door is shut, its card
faded. Into this room the 1937 afternoon returns as PALE figures: the same b1m2 card puppets and the 1937 objects
(memo, stranger, closed cupboard door, the clock's 4:10 hands) cut in near-white chalk card, laid half-transparent,
outlined in chalk. Captions in 1967 are bone-on-black slips; the 1937 lines in pale balloons.
Run: python3 -I p84_thirty_years_on.py [--page-only]"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, Shape, R_  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p31_sounds_only as P31  # noqa: E402  (key_card)
from p77_the_cupboard import scale_shapes, written  # noqa: E402

N, PID, TITLE = 84, "thirty-years-on", "Thirty years on"
W, H = 2200, 2850
BLACK = np.array([22, 21, 19], np.float32)
BONE = np.array([232, 224, 200], np.float32)
GHOST_PAPER = np.array([246, 244, 236], np.float32)

BOXES = {"P1": (110, 110, 2090, 750)}
for i in range(6):
    r, c = divmod(i, 2)
    x0 = 110 if c == 0 else 1130
    y0 = 780 + r * 660
    BOXES[f"P{i + 2}"] = (x0, y0, x0 + 960, y0 + 630)

CAPS = {
    "P1": "Randolph station, September 1967. The office has been shut for years.",
    "P2": "1937: he read the memo and got up.",
    "P3": "1937: a lady at the window, where the boards are now.",
    "P4": "The clock has stopped. In 1937 it said ten past four.",
    "P5": "1937: she thanked him and went.",
    "P6": "1937: he opened the cupboard. The key hung there.",
    "P7": "1967: the key is still on its hook. The SERVICE door is still closed.",
}


# ------------------------------------------------------------------ the 1967 room (dark cards, dust)
def layout(w, h):
    """positions of the room's things for a board w x h (the P1 board spreads them wider)"""
    f = h - 34
    if w > 1500:
        return dict(f=f, s=1.0, win=(110, 130, 330, 470), desk=(560, f - 190, 400), clock=(960, 150, 60),
                    cal=(1100, 170), cup=(1380, 200, 250, 400), sdoor=(1740, 120, 220, f - 120))
    return dict(f=f, s=0.86, win=(40, 150, 220, 380), desk=(285, f - 150, 220), clock=(600, 175, 44),
                cal=None, cup=(650, 240, 150, 320), sdoor=(812, 175, 128, f - 175))


def cobweb(lum, cx, cy, r, seed, dirs=(0, 90)):
    """corner cobweb: charcoal threads radiating from the corner, sagging arcs between them"""
    rnd = random.Random(seed)
    a0, a1 = math.radians(dirs[0]), math.radians(dirs[1])
    angs = np.linspace(a0, a1, 6)
    for a in angs:
        C.charcoal_line(lum, [(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))], 1.4, seed + int(a * 100),
                        dark=0.25, tremor=0.3, alpha=0.7)
    for k in range(1, 5):
        rr = r * k / 5
        for a, b in zip(angs[:-1], angs[1:]):
            m = (a + b) / 2
            sag = rr * 0.88
            C.charcoal_line(lum, [(cx + rr * math.cos(a), cy + rr * math.sin(a)), (cx + sag * math.cos(m), cy + sag * math.sin(m)),
                                  (cx + rr * math.cos(b), cy + rr * math.sin(b))], 1.1, seed + k * 31 + rnd.randrange(99),
                            dark=0.28, tremor=0.2, alpha=0.6)


def dust_sheet(lum, x0, top, w, floor, seed):
    """the desk under a draped sheet: one pale-grey card cut as cloth, folds rubbed in"""
    rnd = random.Random(seed)
    pts = [(x0 - 30, floor - 4), (x0 - 22, top + 30), (x0 + 10, top - 6), (x0 + w * 0.5, top - 14), (x0 + w - 10, top - 4),
           (x0 + w + 24, top + 34), (x0 + w + 34, floor - 6)]
    for k in range(8, 0, -1):          # ragged hem
        pts.append((x0 - 30 + (w + 64) * k / 9, floor - 8 + rnd.uniform(-12, 4)))
    m = np.zeros(lum.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(B.catmull(pts, 6)) * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, m, (6, 8), 4, 0.3)
    C.card_piece(lum, m, 0.62, seed, edge=0.30, rub=0.08)
    for k in range(5):                 # folds
        x = x0 + w * (0.1 + 0.2 * k) + rnd.uniform(-10, 10)
        C.charcoal_line(lum, [(x, top + 10), (x + rnd.uniform(-20, 20), (top + floor) / 2), (x + rnd.uniform(-30, 30), floor - 14)],
                        4, seed + 10 + k, dark=0.35, alpha=0.55)


def planks(lum, x0, y0, ww, sill, seed):
    """boards nailed across the ticket window"""
    rnd = random.Random(seed)
    for k in range(4):
        y = y0 + 60 + k * (sill - y0 - 70) / 4 + rnd.uniform(-6, 6)
        deg = rnd.uniform(-6, 6)
        cx, cy = x0 + ww / 2, y + 22
        L = ww + 70
        a = math.radians(deg)
        d = np.array([math.cos(a), math.sin(a)]) * L / 2
        n = np.array([-math.sin(a), math.cos(a)]) * 22
        P = np.array([[cx, cy] - d - n, [cx, cy] + d - n, [cx, cy] + d + n, [cx, cy] - d + n])
        m = np.zeros(lum.shape, np.uint8)
        cv2.fillPoly(m, [np.int32(P * 4)], 255, cv2.LINE_AA, shift=2)
        C.drop(lum, m, (5, 7), 3, 0.35)
        C.card_piece(lum, m, 0.40, seed + k, edge=0.28)
        for e in (-1, 1):
            q = np.array([cx, cy]) + e * d * 0.86
            C.brad(lum, q[0], q[1], 5)


def room1967(w, h, seed):
    L = layout(w, h)
    lum = C.wall(w, h, seed, level=0.74, hp_gain=0.55, broad_gain=0.40, scale=2.4)
    f = L["f"]
    # damp stains and a darker, older wash
    g = cv2.resize(np.random.default_rng(seed).random((6, 9)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    lum *= 0.92 + 0.08 * g
    P31.floor_band(lum, f, seed + 1)
    wx, wy, ww, wh = L["win"]
    ws, sill = window(wx, wy, ww, wh, sill=wy + wh * 0.56, header=58)
    C.pin_up(lum, ws, seed + 2, halo=False)
    gl = np.zeros(lum.shape, np.float32)                     # grimy glass: dark grey panes
    gl[int(wy + 58):int(sill), int(wx):int(wx + ww)] = 1
    lum[:] = np.where(gl > 0, lum * 0.72, lum)
    C.pin_up(lum, ws, seed + 2, halo=False)
    written(lum, ["TICKET OFFICE"], wx + ww / 2, wy + 30, 26 if w < 1500 else 32, seed + 3, dark=0.78)
    planks(lum, wx, wy, ww, sill, seed + 4)
    dx, dtop, dw = L["desk"]
    dust_sheet(lum, dx, dtop, dw, f, seed + 5)
    cx, cy, cr = L["clock"]
    C.pin_up(lum, clock(cx, cy, cr, hh=11, mm=52, pend=True, swing=0), seed + 6, halo=False)
    if L["cal"]:
        kx, ky = L["cal"]
        m = np.zeros(lum.shape, np.uint8)
        cv2.rectangle(m, (kx, ky), (kx + 170, ky + 190), 255, -1)
        C.drop(lum, m, (5, 6), 3, 0.3)
        C.card_piece(lum, m, 0.78, seed + 7, edge=0.15)
        written(lum, ["SEPTEMBER", "1967"], kx + 85, ky + 50, 24, seed + 8, dark=0.12)
        for r_ in range(4):
            for c_ in range(7):
                C.charcoal_line(lum, [(kx + 16 + c_ * 21, ky + 110 + r_ * 20), (kx + 26 + c_ * 21, ky + 110 + r_ * 20)],
                                3, seed + 9 + r_ * 7 + c_, dark=0.3, alpha=0.8)
        C.brad(lum, kx + 85, ky + 8, 5)
    ux, uy, uw, uh = L["cup"]
    cs, ins = cupboard(ux, uy, uw, uh, open_deg=110)
    C.pin_up(lum, [s for s in cs if s.role != "door"], seed + 10, halo=False)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.42
    P31.key_card(lum, kx, ky, 0.20 if w < 1500 else 0.25, seed + 11)
    lum[int(iy0):int(iy1), int(ix0):int(ix1)] *= 0.93       # dust dulls it
    C.pin_up(lum, [s for s in cs if s.role == "door"], seed + 12, halo=False)
    sx, sy, sw, sh = L["sdoor"]
    C.pin_up(lum, service_door(sx, sy, sw, sh), seed + 13, halo=False)
    m = np.zeros(lum.shape, np.uint8)
    cv2.rectangle(m, (int(sx + sw * 0.18), int(sy + 30)), (int(sx + sw * 0.82), int(sy + 80)), 255, -1)
    C.card_piece(lum, m, 0.70, seed + 14, edge=0.2)
    written(lum, ["SERVICE"], sx + sw / 2, sy + 56, 24 if w > 1500 else 17, seed + 15, dark=0.30)
    cobweb(lum, 0, 0, 150 if w < 1500 else 210, seed + 16, (0, 90))
    cobweb(lum, w - 1, 0, 120 if w < 1500 else 180, seed + 17, (90, 180))
    cobweb(lum, ux - 16, uy - 30, 70, seed + 18, (180, 270))
    # light from the boarded window: slats of pale light falling across the floor
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lum *= (0.80 + 0.20 * np.exp(-(((xx - wx - ww / 2) / (w * 0.55)) ** 2 + ((yy - h * 0.4) / h) ** 2)))
    return lum, L


# ------------------------------------------------------------------ 1937, pale
GHOST_TONES = {k: 0.86 + 0.10 * min(1.0, v * 2) for k, v in C.ROLE_TONE.items()}
GHOST_TONES.update(hair=0.80, waistcoat=0.82, trousers=0.84, tie=0.78, hat=0.80, coat=0.85)


def ghost(lum, shapes, seed, alpha=0.74, outline=True):
    """the 1937 figure: cut in near-white chalk card, laid half-transparent over the 1967 room, chalk outline"""
    h, w = lum.shape
    tmp = lum.copy()
    C.pin_up(tmp, shapes, seed, tones=GHOST_TONES, halo=False, piece_shadow=False)
    solid = [s for s in shapes if not s.hole]
    m = B.raster(solid, w, h, ss=1).astype(np.float32) / 255
    m = cv2.GaussianBlur(m, (0, 0), 1.5)
    lum[:] = lum * (1 - alpha * m) + tmp * alpha * m
    if outline:
        e = cv2.morphologyEx((m > 0.5).astype(np.uint8) * 255, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        a = C.rub_mask(e, seed + 5, smear=(0, 0), keep=0.7) * 0.75
        lum[:] = lum * (1 - a) + 0.98 * a
    return m


def ghost_rect(lum, x0, y0, x1, y1, seed, alpha=0.6):
    return ghost(lum, [R_(x0, y0, x1, y1, "door")], seed, alpha)


def ghost_memo(lum, x, y, seed):
    m = np.zeros(lum.shape, np.uint8)
    pts = np.array([(x, y), (x + 230, y - 8), (x + 236, y + 96), (x + 4, y + 104)], np.float32)
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    a = m.astype(np.float32) / 255 * 0.85
    lum[:] = lum * (1 - a) + 0.97 * a
    written(lum, ["4:15 - open", "SERVICE door.", "Key in cupboard."], x + 118, y + 48, 22, seed, dark=0.30)


def ghost_hands(lum, cx, cy, r, seed):
    """the 1937 hands at 4:10, pale over the stopped ones"""
    for hh_deg, L_, wd in (((4 % 12) * 30 + 10 * 0.5, 0.45, 9), (10 * 6, 0.68, 6)):
        a = math.radians(hh_deg)
        m = np.zeros(lum.shape, np.uint8)
        penlib.brush_line(m, [(cx, cy), (cx + math.sin(a) * r * L_, cy - math.cos(a) * r * L_)], wd, seed + wd, 0.2)
        k = cv2.dilate(m, np.ones((5, 5), np.uint8))
        lum[:] = lum * (1 - 0.6 * k / 255) + 0.15 * (0.6 * k / 255)
        lum[:] = lum * (1 - m / 255) + 0.97 * (m / 255)


def pale_balloon(rgb, lines, cap, at, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.24, bend=0.10)
    penlib.lay_balloon(rgb, b, at)
    return b


def cap_slip(rgb, text, x, y, seed, cap=32, width=None):
    width = width or rgb.shape[1] - 2 * x - 40
    B.slip(rgb, x, y, B.wrap(text, cap, width), cap, seed, paper=BLACK, pad=(20, 12), ink=BONE, shadow=0.5)


# ------------------------------------------------------------------ boards
def board(k, ghosts=True, words=True):
    x0, y0, x1, y1 = BOXES[k]
    w, h = x1 - x0, y1 - y0
    lum, L = room1967(w, h, 8400 + int(k[1:]) * 0 + 1)
    f, s = L["f"], L["s"]
    ux, uy, uw, uh = L["cup"]
    sx, sy, sw, sh = L["sdoor"]
    wx, wy, ww, wh = L["win"]
    cx, cy, cr = L["clock"]
    sill = wy + wh * 0.56
    say = None
    if ghosts and k != "P1":
        if k in ("P2", "P3", "P4", "P5"):           # 1937: the cupboard still closed
            ghost(lum, cupboard(ux, uy, uw, uh, open_deg=0)[0], 8460, alpha=0.55)
        if k == "P2":    # E0: the memo on the desk, he rises
            ghost_memo(lum, L["desk"][0] + 30, L["desk"][1] - 10, 8461)
            ghost(lum, agent(L["desk"][0] + L["desk"][2] + 50, f, face=1, scale=0.46 * s / 0.86, legs=(14, -10), sh=-10,
                             el=30, lean=6, pencil_deg=200, far_arm=(20, 20)), 8462)
        elif k == "P3":  # E1: she is at the glass (through the boards), he turns
            ghost(lum, stranger(wx + ww / 2, sill + 24, face=1, scale=0.70, glove=True), 8463, alpha=0.78)
            ghost(lum, agent(420, f, face=-1, scale=0.46, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190), 8464)
            say = (["Pardon me —", "have you the", "right time?"], 40, (610, 265), (wx + ww / 2 + 30, sill - 120))
        elif k == "P4":  # E2: he looks up at the clock; its 1937 hands at 4:10
            ghost_hands(lum, cx, cy, cr, 8465)
            ag = agent(500, f, face=1, scale=0.46, legs=(4, -4), sh=6, el=16, tilt=-28, pencil_deg=190, lean=-3)
            ghost(lum, ag, 8466)
            ghost(lum, stranger(wx + ww / 2, sill + 24, face=1, scale=0.70), 8467, alpha=0.7)
            say = (["Ten past four,", "by the clock."], 40, (250, 270), (515, 262))
        elif k == "P5":  # E3: her thanks; she turns from the glass
            ghost(lum, stranger(wx + ww / 2 - 30, sill + 24, face=-1, scale=0.68, tilt=-6), 8468, alpha=0.74)
            ghost(lum, agent(430, f, face=-1, scale=0.46, legs=(14, -12), sh=-10, el=18, pencil_deg=200, lean=2), 8469)
            say = (["Much", "obliged!"], 42, (330, 200), (wx + ww / 2 - 10, sill - 110))
        elif k == "P6":  # E4: he opens the cupboard; the pale door swings on its left jamb
            cs, _ = cupboard(ux, uy, uw, uh, open_deg=70)
            ghost(lum, [x for x in cs if x.role == "door"], 8470, alpha=0.55)
            ghost(lum, agent(ux - 85, f, face=1, scale=0.46, legs=(4, -4), sh=78, el=-12, wr=0, pencil_deg=200, tilt=4), 8471)
        elif k == "P7":  # E5: pencil to chin; the key on its hook then and now; the SERVICE door shut
            ag = agent(ux - 85, f, face=1, scale=0.46, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2)
            ghost(lum, ag, 8472)
            say = (["Well, here I am...", "and what for?"], 38, (320, 280), (ux - 70, f - 0.46 * 740))
    rgb = C.tone(lum)
    if words:
        cap_slip(rgb, CAPS[k], 22, 18 if k == "P1" else h - 90 if k in () else 18, 8480 + int(k[1:]),
                 width=(1200 if k == "P1" else 880))
        if say and ghosts:
            lines, cap, at, tip = say
            pale_balloon(rgb, lines, cap, at, tip, 8490 + int(k[1:]))
    return rgb


def place_caps_check():
    return None


SHEET = pen99.sheet99()


def build(ghost_upto=7, words=True):
    pg = SHEET.copy()
    for k in BOXES:
        x0, y0, x1, y1 = BOXES[k]
        pg[y0:y1, x0:x1] = board(k, ghosts=int(k[1:]) <= ghost_upto, words=words)
    B.frame_border(pg, list(BOXES.values()), w=12, seed=8499)
    return pg


def main():
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    frames = [build(1)]
    for u in range(2, 8):
        frames.append(build(u))
    for f in frames:
        pen99.folio(f, N, TITLE)
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
