"""99 ways, page 33 "Ticket stock" (cut-paper). The incident told on a strip of six railway card tickets
joined at perforations, one beat per ticket (E0-E5), each numbered 1-6 with a serial, dated by a dater stamp
(SEP 1937 and the minute), and punched by a conductor's clipper (a hole cut through the card).
All HANDMADE cut paper in code (films/swarm/99-ways/kit/cutpaper99.py) on the LoC 1934 sheet; the small pictures
re-cut from page 16's cut-paper figure kit (p16_fewest_marks: agent, stranger, clock, window, cupboard, key,
SERVICE door, memo, desk); lettering in the shared pen hand (pen99). Run: python3 -I p33_ticket_stock.py"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import Cut, ellipse, rect, hexc  # noqa: E402
import p16_fewest_marks as K  # noqa: E402  (page 16 cut-paper figure kit)
import b1m2 as B  # noqa: E402

N, PID, TITLE = 33, "ticket-stock", "Ticket stock"
W, H = 2200, 2850
TX0, TX1 = 190, 2010
TH = 418
TY0 = 150
STUB = 330
INKC = "#1d1a17"
STAMP = "#5b3a78"          # dater-stamp violet

TICKETS = [
    dict(ev="E0", card="#d9c18e", serial="3701", time="4:09", route="DESK  to  CUPBOARD",
         lines=["Memo: \"4:15 - open SERVICE door.", "Key in cupboard.\" He sets off."]),
    dict(ev="E1", card="#a9c19a", serial="3702", time="4:10", route="STOP:  TICKET WINDOW",
         lines=["The stranger, platform side:", "\"Pardon me — have you the right time?\""]),
    dict(ev="E2", card="#e1b1a8", serial="3703", time="4:10", route="CLOCK:  4:10",
         lines=["He looks up at the clock:", "\"Ten past four, by the clock.\""]),
    dict(ev="E3", card="#bacbd3", serial="3704", time="4:10", route="RETURN:  PLATFORM",
         lines=["She leaves the window:", "\"Much obliged!\""]),
    dict(ev="E4", card="#e2d27c", serial="3705", time="4:11", route="ARRIVAL:  CUPBOARD",
         lines=["He opens it. The brass key hangs", "on its hook, tag SERVICE."]),
    dict(ev="E5", card="#ece4d0", serial="3706", time="4:11", route="NOT GOOD FOR:  SERVICE DOOR",
         lines=["Pencil to chin: \"Well, here I am...", "and what for?\"  Key stays. Door shut."]),
]


def ink_left(c, s, x, base, cap, seed, colour=INKC, weight=0.13):
    m = pen99.letter([s], cap, seed, weight=weight)
    full = np.zeros((H, W), np.uint8)
    B.blit_mask(full, m, int(round(x - cap * 0.6)), int(round(base - cap * 1.15)))
    penlib.ink_onto(c.img, full, hexc(colour))
    return m.shape[1] - cap * 1.2


def ink_centre(c, s, cx, base, cap, seed, colour=INKC, weight=0.13):
    m = pen99.letter([s], cap, seed, weight=weight)
    full = np.zeros((H, W), np.uint8)
    B.blit_mask(full, m, int(round(cx - m.shape[1] / 2)), int(round(base - cap * 1.15)))
    penlib.ink_onto(c.img, full, hexc(colour))


def dashes(c, x0, y0, x1, y1, seed, colour=INKC, w=3, dash=14, gap=10):
    m = np.zeros((H, W), np.uint8)
    L = math.hypot(x1 - x0, y1 - y0)
    s, k = 0.0, 0
    while s < L:
        e = min(L, s + dash)
        a, b = s / L, e / L
        penlib.brush_line(m, [(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], w, seed + k, 0.2)
        s, k = e + gap, k + 1
    penlib.ink_onto(c.img, m, hexc(colour))


def dater(c, cx, cy, time, seed, deg=-7):
    """A dater-stamp impression in violet: an oval frame, SEP 1937 and the minute; uneven ink."""
    m = np.zeros((H, W), np.uint8)
    rx, ry = 122, 50
    pts = [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 60)]
    penlib.brush_line(m, pts, 5, seed, 0.3)
    l1 = pen99.letter(["SEP 1937"], 25, seed + 1, weight=0.15)
    l2 = pen99.letter([time + " PM"], 25, seed + 2, weight=0.15)
    B.put_mask(m, l1, cx, cy - 4)
    B.put_mask(m, l2, cx, cy + 28)
    M = cv2.getRotationMatrix2D((cx, cy), -deg, 1.0)
    m = cv2.warpAffine(m, M, (W, H))
    rng = np.random.default_rng(seed)
    blot = cv2.GaussianBlur(rng.random((H // 8, W // 8)).astype(np.float32), (0, 0), 1.2)
    blot = cv2.resize(blot, (W, H))
    a = np.clip(0.55 + (blot - 0.5) * 2.2, 0.25, 0.95)
    penlib.ink_onto(c.img, (m.astype(np.float32) * a).astype(np.uint8), hexc(STAMP))


VIG = {}


# ------------------------------------------------------------------ pictures (page 16 kit, re-cut small)
def picture(c, k, box, seed):
    vx0, vy0, vx1, vy1 = box
    sh = (H, W)
    floor = vy1 - 34
    c.piece(rect(vx0, vy0, vx1, floor + 2), K.COL["wall"], shadow=False, grain=1.3)
    c.piece(rect(vx0, floor, vx1, vy1), K.COL["floor"], shadow=False)
    s = 0.42
    lay = lambda pcs, sd: K.lay(c, pcs, sd)
    if k == 0:
        lay(K.clock(vx1 - 50, vy0 + 54, 34, hh=4, mm=9), seed)
        ag, _ = K.agent(sh, s, (vx0 + 90, floor), arms="rise", head_rot=10)
        lay(ag, seed + 3)
        lay(K.desk(vx0 + 40, vx1 - 70, floor - 92, floor), seed + 6)
        lay(K.memo(vx0 + 250, floor - 132, 150, deg=-5), seed + 9)
    elif k == 1:      # E1: she is at the glass, facing him; he is stopped on his way
        wx0, wx1 = vx0 + 170, vx1 - 14
        glass, front = K.window(wx0, vy0 + 22, wx1, floor - 88, vx1 + 20)
        lay([glass], seed)
        st, _ = K.stranger(sh, 0.44, ((wx0 + wx1) / 2, floor - 50), away=False)
        lay(st, seed + 2)
        VIG[k] = dict(stranger_x=round((wx0 + wx1) / 2 - vx0), stranger_scale=0.44, faces="the office", agent="faces the window")
        lay(front, seed + 4)
        ag, _ = K.agent(sh, s, (vx0 + 80, floor), arms="walk", legs="walk")
        lay(ag, seed + 6)
    elif k == 3:      # E3: she has left the glass: the window's middle is empty; she walks off along the platform
        wx0, wx1 = vx0 + 170, vx1 - 14
        glass, front = K.window(wx0, vy0 + 22, wx1, floor - 88, vx1 + 20)
        lay([glass], seed)
        sx = wx1 - 46                     # small and far, back turned, half gone behind the right post
        st, _ = K.stranger(sh, 0.27, (sx, floor - 88 - 30), away=True)
        lay(st, seed + 2)
        VIG[k] = dict(stranger_x=round(sx - vx0), stranger_scale=0.27, faces="away, to the platform (right)",
                      agent="turned back, walking left toward the cupboard")
        lay(front, seed + 4)
        ag, _ = K.agent(sh, s, (vx0 + 100, floor), flip=True, arms="walk", legs="walk")
        lay(ag, seed + 6)
    elif k == 2:
        lay(K.clock(vx0 + 100, vy0 + 92, 66, hh=4, mm=10), seed)
        ag, _ = K.agent(sh, s, (vx1 - 110, floor), flip=True, arms="stand", head_rot=-30)
        lay(ag, seed + 3)
    else:
        lay(K.service_door(vx1 - 92, vy0 + 40, vx1 - 14, floor), seed)
        carcass, door = K.cupboard(vx0 + 160, vy0 + 112, vx0 + 290, floor - 3, 1.0)
        lay([carcass], seed + 2)
        lay(K.key(sh, vx0 + 226, vy0 + 128, 0.72), seed + 3)
        lay([door], seed + 6)
        if k == 4:
            ag, _ = K.agent(sh, s, (vx0 + 70, floor), arms="reach", legs="stand")
        else:
            ag, _ = K.agent(sh, s, (vx0 + 60, floor), arms="chin", head_rot=-6)
        lay(ag, seed + 8)
    # printed frame line round the picture
    m = penlib.border_mask((H, W), [(vx0, vy0, vx1, vy1)], w=4, seed=seed + 20)
    penlib.ink_onto(c.img, m, hexc(INKC))


# ------------------------------------------------------------------ the strip
def ticket_box(i):
    y0 = TY0 + i * TH
    return TX0, y0, TX1, y0 + TH


def punch_hole(i):
    x0, y0, x1, y1 = ticket_box(i)
    # clipper bite: a round hole with a small V notch (the conductor's die), in the stub
    cx, cy = x0 + 262, y0 + 96 + (i % 3) * 14
    circ = ellipse(cx, cy, 24, 24, 0, 360, 28)
    return circ


def lay_ticket(c, i, punched, sheet):
    t = TICKETS[i]
    x0, y0, x1, y1 = ticket_box(i)
    sd = 3300 + i * 50
    holes = [punch_hole(i)] if punched else []
    # the card: perforation notches cut along the joins (half-circles on each joined edge)
    c.piece(rect(x0, y0 + 2, x1, y1 - 2), t["card"], holes=holes, jitter=0.5, opacity=0.34, grain=0.55)
    # printed border, stub divider (perforated: dashes)
    m = penlib.border_mask((H, W), [(x0 + 18, y0 + 18, x1 - 18, y1 - 18)], w=3, seed=sd)
    penlib.ink_onto(c.img, m, hexc(INKC))
    dashes(c, x0 + STUB, y0 + 24, x0 + STUB, y1 - 24, sd + 1)
    # stub: No., the big number, serial
    ink_left(c, "No.", x0 + 44, y0 + 86, 38, sd + 2)
    ink_centre(c, str(i + 1), x0 + STUB / 2, y0 + 300, 170, sd + 3, weight=0.15)
    ink_centre(c, "Ser. " + t["serial"], x0 + STUB / 2, y1 - 40, 28, sd + 4)
    # main: head, route, the beat, small print
    mx = x0 + STUB + 40
    ink_left(c, "CENTRAL VERMONT RY.    RANDOLPH, VT.", mx, y0 + 74, 32, sd + 5)
    lm = np.zeros((H, W), np.uint8)
    penlib.brush_line(lm, [(mx - 10, y0 + 92), (x1 - 470, y0 + 93)], 3, sd + 6, 0.3)
    penlib.ink_onto(c.img, lm, hexc(INKC))
    ink_left(c, t["route"], mx, y0 + 168, 54, sd + 7, weight=0.15)
    for j, l in enumerate(t["lines"]):
        ink_left(c, l, mx, y0 + 244 + j * 58, 40, sd + 8 + j)
    ink_left(c, "Good for this afternoon only. Not transferable.", mx, y1 - 36, 24, sd + 12)
    # the picture
    picture(c, i, (x1 - 440, y0 + 36, x1 - 36, y1 - 36), sd + 20)
    # the dater stamp, over the small print corner
    dater(c, x1 - 560, y1 - 62, t["time"], sd + 40, deg=-6 + (i % 3) * 3)
    if punched:   # the clipped-out disc's edge catches the light; hole shows the sheet beneath with a shadow
        p = punch_hole(i)
        cx, cy = p.mean(0)
        hm = np.zeros((H, W), np.uint8)
        cv2.circle(hm, (int(cx), int(cy)), 24, 255, -1, cv2.LINE_AA)
        sh = np.zeros_like(hm)
        cv2.circle(sh, (int(cx) - 5, int(cy) - 6), 24, 255, -1, cv2.LINE_AA)
        a = (cv2.GaussianBlur(cv2.bitwise_and(hm, cv2.bitwise_not(sh)), (0, 0), 1.5).astype(np.float32) / 255 * 0.45)[..., None]
        c.img *= (1 - a)


def perforations(c, n, sheet):
    """Round perforation holes along each join between tickets: the sheet shows through."""
    for i in range(1, n):
        y = TY0 + i * TH
        for x in np.arange(TX0 + 14, TX1 - 8, 26):
            cv2.circle(c.img, (int(x), int(y)), 5, tuple(float(v) for v in sheet[int(y), int(x)] * 0.82), -1, cv2.LINE_AA)


def build(n_laid=6, n_punched=6):
    c = Cut(H, W, seed=3300)
    sheet = c.img.copy()
    for i in range(n_laid):
        lay_ticket(c, i, i < n_punched, sheet)
    perforations(c, n_laid, sheet)
    return c.img


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    frames = []
    for k in range(1, 7):
        f = build(k, k - 1)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    frames.append(img.astype(np.float32))
    nb = B.save_beats(N, frames)
    print("bytes", size, "beats", nb)


if __name__ == "__main__":
    main()
