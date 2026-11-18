"""99 ways, page 68 "Showdown" (genre; medium: engraving-puppet).
Framed as a frontier standoff at the ticket window, hands at the hip, the clock as the duel's timer.
A storyboard sheet for a western: a torn bill pinned at the head ('SHOWDOWN AT THE TICKET WINDOW'), eight
widescreen shot boards (letterboxed, each headed SHOT n, its framing and a running clock time to the second with a
small pen clock face: the duel's timer), torn commentary slips in a frontier drawl, written for this page.
Shot 3 is the western's eyes-only extreme close-up; shot 4 the hands at the hip; shot 5 the clock filling the
frame at 4:10. The four canon lines verbatim in cut-paper balloons; the outcome unchanged.
Reuses page 03/49's ENGRAVING PUPPETS (kit/build_page03.py, build/p49_epic.py): AGENT = the Harper's Weekly 1863
telegraph operator (LoC cph.3c11072), STRANGER = the hatted woman of the 1867 Steinway Hall engraving (LoC
cph.3c32079), his table and the window from the 1863 plate; set, tumbleweed, clock faces and lettering in the
shared pen hand. Run: python3 -I p68_showdown.py [--page-only]"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import build_page03 as b3  # noqa: E402
import b1m2 as B  # noqa: E402
import p49_epic as E  # noqa: E402

N, PID, TITLE = 68, "showdown", "Showdown"
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, letters, Mof, lay = b3.pen, b3.letters, b3.Mof, b3.lay
K = 0.82                          # boards are cut at 372 px high and laid on the sheet at 0.82
BH = 372
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == E.LN["question"] and " ".join(A) == E.LN["answer"]
assert " ".join(T) == E.LN["thanks"] and " ".join(F) == E.LN["forgetting"]

SHOTS = {  # n: (framing, h, m, s, slip)
    1: ("WIDE", 4, 9, 30, "Randolph, Vermont. Four-oh-nine. One man, one job: open the SERVICE door at a quarter past, "
                          "with the key in the cupboard. He gets up out of that chair, slow."),
    2: ("MEDIUM", 4, 9, 50, "Halfway across the floor, he stops. Somebody's at the window."),
    3: ("EXTREME CLOSE-UP", 4, 10, 0, "His eyes. Her eyes. Nobody blinks."),
    4: ("HANDS AT THE HIP", 4, 10, 4, "Hands at the hip. She draws first."),
    5: ("CLOSE: THE CLOCK", 4, 10, 9, "He draws the time off the wall clock, quick and clean."),
    6: ("MEDIUM", 4, 10, 15, "She tips her head and leaves the window. Nothing left in here now but a bit of blown hay, rolling by."),
    7: ("MEDIUM", 4, 10, 45, "He makes it to the cupboard. There's the key, on its hook."),
    8: ("WIDE", 4, 11, 0, "Showdown's over, and nobody won. The key stays on its hook; the SERVICE door stays shut."),
}
FULL = (1, 8)
SCAP = 28
BILL_OV = 34
BILL_T = (pen99.letter(["SHOWDOWN"], 84, 6990, weight=0.15), pen99.letter(["AT THE TICKET WINDOW"], 40, 6991, weight=0.13),
          pen99.letter(["Randolph station, 4:10 sharp. Eight shots, one clock."], 26, 6992))
BILL_H = sum(m.shape[0] - BILL_OV for m in BILL_T) + 14
TOP0 = 104 + BILL_H + 12
COLX = ((110, 1070), (1130, 2090))


def slip_h(n, w):
    let = B.letter_left(B.wrap(SHOTS[n][4], SCAP, w - 90), SCAP, 6800 + n)
    return let.shape[0] + int(SCAP * 0.9)


def layout():
    rows = [(1,), (2, 3), (4, 5), (6, 7), (8,)]
    bh = int(BH * K)
    hdr = 40
    need = 0
    for r in rows:
        w = 1980 if r[0] in FULL else 960
        need += hdr + bh + 10 + max(slip_h(n, w) for n in r)
    gap = (2728 - TOP0 - need) / (len(rows) - 1)
    assert gap >= 8, gap
    bx, y = {}, TOP0
    for r in rows:
        for i, n in enumerate(r):
            x0, x1 = (110, 2090) if n in FULL else COLX[i]
            bx[n] = (x0, int(y + hdr), x1 - x0, bh)
        w = 1980 if r[0] in FULL else 960
        y += hdr + bh + 10 + max(slip_h(n, w) for n in r) + gap
    return bx


BX = layout()


# ------------------------------------------------------------------ HANDMADE pen props
def tumbleweed(c, cx, cy, r, seed, rot=0.0):
    """a ball of blown hay: tangled pen loops"""
    rnd = random.Random(seed)
    m = np.zeros(c.shape[:2], np.uint8)
    for k in range(14):
        a0 = rnd.uniform(0, 6.28) + rot
        rr = r * rnd.uniform(0.25, 0.6)
        ex = rnd.uniform(0.6, 1.0)
        ox, oy = rnd.uniform(-0.4, 0.4) * r, rnd.uniform(-0.35, 0.35) * r
        pts = [(cx + ox + rr * math.cos(a0 + t) * ex, cy + oy + rr * math.sin(a0 + t) * (2 - ex) * 0.8)
               for t in np.linspace(0, rnd.uniform(2.5, 5.5), 18)]
        penlib.brush_line(m, pts, 2.6, seed + k, tremor=0.7)
    penlib.ink_onto(c, m, b3.INK)
    pen(c, [(cx - r * 2.4, cy + r * 0.95), (cx - r * 1.4, cy + r * 0.95)], 2, seed + 40)        # dust trail
    pen(c, [(cx - r * 3.6, cy + r * 0.80), (cx - r * 2.8, cy + r * 0.80)], 2, seed + 41)


def mini_clock(pg, cx, cy, r, hh, mm, ss, seed):
    """the duel's timer in each shot's header: pen face, hour, minute and second hands"""
    pen(pg, b3.circle_pts(cx, cy, r, 30), 3, seed, closed=True)
    for k in range(12):
        a = math.radians(k * 30)
        pen(pg, [(cx + math.sin(a) * r * .78, cy - math.cos(a) * r * .78), (cx + math.sin(a) * r * .92, cy - math.cos(a) * r * .92)],
            2, seed + 3 + k)
    mmf = mm + ss / 60
    ah, am, asx = math.radians((hh % 12) * 30 + mmf * .5), math.radians(mmf * 6), math.radians(ss * 6)
    pen(pg, [(cx, cy), (cx + math.sin(ah) * r * .5, cy - math.cos(ah) * r * .5)], 4, seed + 20)
    pen(pg, [(cx, cy), (cx + math.sin(am) * r * .8, cy - math.cos(am) * r * .8)], 3, seed + 21)
    pen(pg, [(cx, cy), (cx + math.sin(asx) * r * .86, cy - math.cos(asx) * r * .86)], 1.6, seed + 22, colour=b3.GRAPH)


def big_clock(c, cx, cy, r, ss, seed):
    """the wall clock filling the shot at 4:10, its pendulum and second hand"""
    b3.clock(c, cx, cy, r, 4, 10, seed)
    a = math.radians(ss * 6)
    pen(c, [(cx, cy), (cx + math.sin(a) * r * .82, cy - math.cos(a) * r * .82)], 2, seed + 400, colour=b3.GRAPH)


def eyes_piece(P, key, box):
    """a strip cut across a puppet's eyes (piece px box x0, y0, x1, y1)"""
    pc = P[key]
    ox, oy = pc["origin"]
    x0, y0, x1, y1 = box
    a = np.zeros_like(pc["a"])
    a[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = pc["a"][y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return dict(pc, a=a)


# ------------------------------------------------------------------ boards (cut at native 372 px height)
def board(n, P, st):
    full = n in FULL
    w = int(round((1980 if full else 960) / K))
    h = BH
    c = E.card(w, h, 6810 + n)
    gy = h - 30
    rec = {}
    if n != 3:
        b3.ground_line(c, 0, w, gy, 6820 + n)
    s = 0.33
    if n == 1:      # E0: the office, wide: desk and memo, the wall clock, the cupboard and the SERVICE door far off
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (380, gy + 2)))
        b3.memo(c, 335, 186, 0.62, 6830, deg=-4)
        b3.clock(c, 1180, 92, 44, 4, 9, 6831)
        E.window_board(c, P, 1560, 6832)
        b3.cupboard(c, 1960, 70, 2140, gy - 20, 0.0, 6833)
        b3.service_door(c, 2210, 54, 2370, gy, 6834)
        rise = st.get("rise", 1.0)
        b3.agent(c, P, (620 + 120 * rise, gy + 2), s, arms=(-30 * rise, 10, -10), head=8, flip=True)
    elif n == 2:    # E0-E1: crossing the floor, he stops; a shape behind the glass
        E.window_board(c, P, 830, 6840, woman=dict(flip=True, shift=0.10))
        b3.cupboard(c, 980, 70, 1140, gy - 20, 0.0, 6841)
        b3.agent(c, P, (420, gy + 2), s, arms=(0, 0, 0), flip=True, head=4)
    elif n == 3:    # the eyes, split by the window's sash: his (left), hers (right, turned to face him)
        mid = w // 2
        hp = eyes_piece(P, "head", (596, 147, 596 + 187, 147 + 227))
        Mh = Mof(2.3, 0, (596 + 95, 147 + 112), (mid * 0.5, h * 0.48))
        lay(c, hp, Mh, margin=0)
        wp = eyes_piece(P, "woman", (150, 52, 280, 200))
        Mw = np.vstack([Mof(2.3, 0, (222, 122), (mid * 1.5, h * 0.42)), [0, 0, 1]])
        Mw = (np.array([[-1, 0, 2 * mid * 1.5], [0, 1, 0], [0, 0, 1]], np.float64) @ Mw)[:2]
        lay(c, wp, Mw, margin=0)
        m = np.zeros(c.shape[:2], np.uint8)
        cv2.rectangle(m, (mid - 14, 0), (mid + 14, h), 255, -1)
        penlib.ink_onto(c, m, b3.INK)
    elif n == 4:    # E1: the standoff at the glass, hands at the hip; she draws first
        E.window_board(c, P, 860, 6850, woman=dict(flip=True, shift=0.0))
        # close on his middle: both hands at the hip, the near one hovering, fingers ready (head out of shot)
        rec["hand"] = b3.agent(c, P, (330, gy + 560), 0.78, arms=st.get("arms", (-8, -6, 0)), flip=True, head=-2)
        q = rec["hand"]
        for k, (dx, dy, ex, ey) in enumerate(((-40, -30, -64, -62), (0, -46, 0, -86), (40, -30, 64, -62))):
            pen(c, [(q[0] + dx, q[1] + dy), (q[0] + ex, q[1] + ey)], 4, 6855 + k)      # pen twitch marks
    elif n == 5:    # E2: the clock fills the shot, the duel's timer; his head turned up to it, low left
        big_clock(c, w * 0.62, h * 0.38, 118, st.get("ss", 9), 6860)
        b3.agent(c, P, (170, gy + 120), 0.40, arms=(0, 0, 0), flip=True, head=-22)
        letters(c, ["tick"], 26, w * 0.62 + 200, 90, 6861, colour=b3.GRAPH)
        letters(c, ["tock"], 26, w * 0.62 + 230, 150, 6862, colour=b3.GRAPH)
    elif n == 6:    # E3: the thanks; she turns away; a tumbleweed rolls past on the platform
        E.window_board(c, P, 560, 6870, woman=dict(flip=False, shift=0.42))
        b3.agent(c, P, (270, gy + 2), s, arms=(0, 0, 0), flip=True, head=10)
        tx = st.get("tw", 1.0)
        tumbleweed(c, 800 + 280 * tx, gy - 62, 64, 6871, rot=tx * 6)
    elif n == 7:    # E4: the cupboard open, the key on its hook; hands at the hip
        b3.service_door(c, 840, 60, 1000, gy, 6880)
        b3.cupboard(c, 480, 70, 700, gy - 20, st.get("open", 0.8), 6881)
        b3.agent(c, P, (260, gy + 2), s, arms=(0, 0, 0), flip=True)
    else:           # E5: the wide again: pencil to chin before the open cupboard, the window empty, the door shut
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (380, gy + 2)))
        b3.memo(c, 335, 186, 0.62, 6890, deg=-4)
        b3.clock(c, 1000, 92, 44, 4, 11, 6891)
        E.window_board(c, P, 1300, 6892)
        b3.cupboard(c, 1760, 70, 1960, gy - 20, 1.0, 6893)
        b3.service_door(c, 2100, 54, 2270, gy, 6894)
        hnd = b3.agent(c, P, (1600, gy + 2), 0.33, arms=(47, 132, 0), head=-6, flip=True)
        pen(c, [(hnd[0] + 2, hnd[1] + 4), (hnd[0] - 6, hnd[1] - 34)], 5, 6895)
        rec["agent_x"] = 1600
    return c, rec


BALLOONS = {   # n: (lines, cap, centre (board px at sheet scale), tail tip)
    4: (Q, 30, (520, 84), (680, 110)),
    5: (A, 30, (330, 70), (190, 92)),
    6: (T, 34, (640, 82), (488, 92)),
    8: (F, 32, (1110, 70), (1300, 132)),
}


def letterbox(pg, x0, y0, w, h, bar=16):
    m = np.zeros(pg.shape[:2], np.uint8)
    m[y0:y0 + bar, x0:x0 + w] = 255
    m[y0 + h - bar:y0 + h, x0:x0 + w] = 255
    penlib.ink_onto(pg, m, b3.INK)


def bill(pg, seed=6990):
    """the head of the sheet: a torn bill pinned up, frontier-poster lettering in the pen hand"""
    t1, t2, t3 = BILL_T
    ww = max(t1.shape[1], t2.shape[1], t3.shape[1]) + 200
    hh = BILL_H
    x, y = (W - ww) // 2, 104
    rnd = random.Random(seed)
    m = np.zeros(pg.shape[:2], np.uint8)
    top = [(x + k, y + rnd.uniform(-5, 4)) for k in range(0, ww, 14)]
    rt = [(x + ww + rnd.uniform(-4, 4), y + k) for k in range(0, hh, 14)]
    bot = [(x + ww - k, y + hh + rnd.uniform(-6, 5)) for k in range(0, ww, 14)]
    lt = [(x + rnd.uniform(-4, 4), y + hh - k) for k in range(0, hh, 14)]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in top + rt + bot + lt])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(pg, m, off=6, blur=5, opacity=0.32)
    pg[:] = pg * (1 - m[..., None] / 255) + b3.SLIPC * (m[..., None] / 255)
    yy = y + 2
    for mm in (t1, t2, t3):
        sub = np.zeros(pg.shape[:2], np.uint8)
        xx = (W - mm.shape[1]) // 2
        sub[yy:yy + mm.shape[0], xx:xx + mm.shape[1]] = mm
        penlib.ink_onto(pg, sub, penlib.INK)
        yy += mm.shape[0] - BILL_OV
    # a pen five-point star each side, the frontier bill's ornament
    for side in (-1, 1):
        cx, cy, r = W / 2 + side * (t1.shape[1] / 2 + 70), y + 70, 40
        pts = [(cx + (r if k % 2 == 0 else r * 0.42) * math.sin(k * math.pi / 5),
                cy - (r if k % 2 == 0 else r * 0.42) * math.cos(k * math.pi / 5)) for k in range(10)]
        pen(pg, pts, 4, seed + 10 + side, closed=True)
    for px in (x + 24, x + ww - 24):
        b3.pin(pg, px, y + 22, 7)


SHEET = E.SHEET


def build(upto=8, st=None, line_upto=8):
    st = st or {}
    pg = SHEET.copy()
    P = b3.load_puppets()
    bill(pg)
    for n in range(1, 9):
        if n > upto:
            continue
        x0, y0, w, h = BX[n]
        fr, hh, mm, ss, txt = SHOTS[n]
        hdr = pen99.letter([f"SHOT {n}    {fr}"], 30, 6900 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        sub[y0 - 44:y0 - 44 + hdr.shape[0], x0 - 14:x0 - 14 + hdr.shape[1]] = hdr
        penlib.ink_onto(pg, sub, b3.GRAPH)
        tm = pen99.letter([f"{hh}:{mm:02d}:{ss:02d}"], 30, 6910 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        tx = x0 + w - tm.shape[1] - 40
        sub[y0 - 44:y0 - 44 + tm.shape[0], tx:tx + tm.shape[1]] = tm
        penlib.ink_onto(pg, sub, b3.INK)
        mini_clock(pg, x0 + w - 22, y0 - 22, 17, hh, mm, ss, 6920 + n)
        art, _ = board(n, P, st.get(n, {}))
        art = cv2.resize(art, (w, h), interpolation=cv2.INTER_AREA)
        pg[y0:y0 + h, x0:x0 + w] = art
        letterbox(pg, x0, y0, w, h)
        if n in BALLOONS and n <= line_upto:
            lines, cap, (cx, cy), (tx_, ty_) = BALLOONS[n]
            E.balloon(pg, lines, cap, (x0 + cx, y0 + cy), (x0 + tx_, y0 + ty_), 6940 + n)
        bm = penlib.border_mask(pg.shape[:2], [(x0, y0, x0 + w, y0 + h)], 7, 6950 + n)
        penlib.ink_onto(pg, bm)
        E.slip_left(pg, B.wrap(txt, SCAP, w - 90), SCAP, x0 + 8, y0 + h + 10, 6800 + n)
    return pg


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    # the duel on the clock: shot by shot, the timer running; the question laid, the clock's second hand ticking,
    # the answer, the tumbleweed rolling past, the forgetting
    frames = [build(2), build(3), build(4, line_upto=3), build(4), build(5, {5: {"ss": 4}}, line_upto=4),
              build(5, {5: {"ss": 9}}), build(6, {6: {"tw": 0.0}}), build(8)]
    for f in frames:
        pen99.folio(f, N, TITLE)
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
