"""99 ways, page 93 "Pendulum" (time and order; medium: spiral-disc).
Eight panels, two to a tier. Each panel is one swing of the station clock's pendulum: a cut-card brass rod pinned in
the gutter above the tier, its bob a card disc printed with the anemic-cinema engraved eccentric-ring disc (O_A,
procedural, reused) and numbered with the swing. The rod crosses the gutter into the panel and the bob's dotted path
crosses the centre gutter from the other side, so the bob is left, right, left, right panel by panel. The only
measure of time on the page is the count of swings. Figures: the b1m2 HANDMADE cut-paper model printed in ink (as
pages 06 and 46); the key: the ANRC 1922 cutout in brass. The dial itself is never seen (the clock in panel 4 is
drawn without a pendulum: this is its pendulum).
Run: python3 -I p93_pendulum.py [beats]"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema")
from b1m2 import *  # noqa
import optics  # noqa: E402  (anemic-cinema O_A engraved ring disc; procedural)

N, PID, TITLE = 93, "pendulum", "Pendulum"
PW, PH = 970, 550
COLS = (110, 1120)
TOP0, GUT = 290, 78
TOPS = [TOP0 + r * (PH + GUT) for r in range(4)]
CARD = np.array([238, 229, 208], np.float32)
PRINT = np.array([24, 21, 20], np.float32)
RED = np.array([168, 58, 40], np.float32)
BRASS = np.array([206, 154, 60], np.float32)
BRASS_D = np.array([150, 108, 40], np.float32)
PENCIL = np.array([96, 92, 86], np.float32)
FIG = 0.46
FLOOR = 505
ROD_L, ROD_DEG, BOB_R = 540, 23.5, 80

Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
TH = ["Much obliged!"]
F = ["Well, here I am...", "and what for?"]

CAPS = [
    "Swing 1. His memo: open the SERVICE door at 4:15, key in the cupboard.",
    "Swing 2. He gets up and sets off for the key.",
    "Swing 3. A lady at the window.",
    "Swing 4. He looks up at the clock.",
    "Swing 5. She thanks him.",
    "Swing 6. She goes. On to the cupboard.",
    "Swing 7. He opens it: the brass key on its hook.",
    "Swing 8. The key stays; the door stays shut.",
]
EVENTS = ["E0", "E0", "E1", "E2", "E3", "E3-E4", "E4", "E5"]


def head_of(shapes, role):
    pts = np.concatenate([s.curve() for s in shapes if s.role == role])
    return np.array([pts[:, 0].mean(), pts[:, 1].min() + 55])


def ticket_window(x0, w):
    ws, sill = window(x0, 132, w, FLOOR - 132, sill=FLOOR - 150, header=50)
    return ws, sill


def scene(k):
    """Panel k (0-7) as an upright ink print on card, PW x PH. Returns img, heads, extra-brass boxes."""
    t = np.zeros((PH, PW, 3), np.float32) + CARD
    shapes, heads, inside, lettering, sdoors = [], {}, [], [], []
    ag = None
    if k == 0:      # E0 the memo; he sits at the desk
        ag = agent(400, FLOOR + 70, face=1, scale=FIG, seated=True, tilt=14, sh=40, el=70, pencil_deg=60, lean=6)
        chair = [R_(330, FLOOR - 150, 350, FLOOR, "chair"), R_(330, FLOOR - 150, 440, FLOOR - 134, "chair"),
                 R_(420, FLOOR - 150, 440, FLOOR, "chair")]
        shapes += chair + ag + desk(420, FLOOR - 140, 300, FLOOR) + lamp(700, FLOOR - 270, 130)
    elif k == 1:    # E0 he gets up and sets off (toward the cupboard, right)
        ag = agent(470, FLOOR, face=1, scale=FIG, legs=(22, -20), lean=2, sh=-20, el=20, pencil_deg=200)
        shapes += ag + desk(300, FLOOR - 140, 120, FLOOR)
        c, _ = cupboard(700, FLOOR - 380, 160, 360, open_deg=0)
        shapes += c
    elif k in (2, 4):  # E1 / E3 at the ticket window (window left, he faces left)
        ws, sill = ticket_window(70, 240)
        shapes += ws
        st = stranger(170, sill + 12, face=1, scale=0.62, glove=(k == 2), nod=(8 if k == 4 else 0))
        shapes += st
        heads["her"] = head_of(st, "skin_s")
        ag = agent(640, FLOOR, face=-1, scale=FIG, legs=(4, -4), sh=6, el=16, pencil_deg=190)
        shapes += ag
        lettering.append((["TICKET OFFICE"], 24, (190, 157)))
    elif k == 3:    # E2 he looks up at the clock (no pendulum on it: the page's pendulum is its own)
        shapes += clock(790, 150, 70, pend=False)
        ag = agent(560, FLOOR, face=1, scale=FIG, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
        shapes += ag
    elif k == 5:    # E3 she goes / E4 on to the cupboard
        ws, sill = ticket_window(-60, 200)
        shapes += ws
        shapes += stranger(20, sill + 12, face=-1, scale=0.62)
        ag = agent(420, FLOOR, face=1, scale=FIG, legs=(18, -16), sh=-14, el=20, pencil_deg=200)
        shapes += ag
        c, _ = cupboard(650, FLOOR - 320, 160, 300, open_deg=0)
        shapes += c + service_door(850, FLOOR - 330, 120, 330)
        sdoors.append((850, FLOOR - 330, 120))
    elif k == 6:    # E4 the cupboard open, the key on its hook
        c, ins = cupboard(130, FLOOR - 320, 200, 310, open_deg=112)
        shapes += c + service_door(580, FLOOR - 370, 140, 370)
        sdoors.append((580, FLOOR - 370, 140))
        inside.append(ins)
        ag = agent(440, FLOOR, face=-1, scale=FIG, legs=(12, -10), sh=40, el=40, wr=0, pencil_deg=200)
        shapes += ag
    elif k == 7:    # E5 the forgetting
        c, ins = cupboard(290, FLOOR - 300, 200, 290, open_deg=112)
        shapes += c + service_door(810, FLOOR - 340, 130, 340)
        sdoors.append((810, FLOOR - 250, 130))
        inside.append(ins)
        ag = agent(590, FLOOR, face=-1, scale=FIG, legs=(3, -3), sh=48, el=118, wr=8, pencil_deg=40, tilt=-6)
        shapes += ag
    if ag is not None:
        heads["him"] = head_of(ag, "skin")
    # floor line
    fl = np.zeros((PH, PW), np.uint8)
    cv2.rectangle(fl, (0, FLOOR), (PW, FLOOR + 6), 255, -1)
    comp(t, fl, PRINT, 0.6)
    m = raster(shapes, PW, PH)
    comp(t, m, PRINT)
    for lines, cap, (x, y) in lettering:
        lm = np.zeros((PH, PW), np.uint8)
        put_mask(lm, letter(lines, cap, 9300 + k, weight=0.17), x, y)
        comp(t, lm, CARD)
    if k == 0:      # the memo slip on the desk, pencilled 4:15
        mm_ = np.zeros((PH, PW), np.uint8)
        x0, y0 = 500, FLOOR - 162
        cv2.fillPoly(mm_, [np.int32([(x0, y0), (x0 + 150, y0 - 8), (x0 + 154, y0 + 30), (x0 + 4, y0 + 38)])], 255, cv2.LINE_AA)
        comp(t, mm_, np.array([250, 247, 238], np.float32))
        lm = np.zeros((PH, PW), np.uint8)
        put_mask(lm, letter(["4:15"], 30, 9311, weight=0.18), x0 + 76, y0 + 14)
        comp(t, lm, RED)
    for (dx, dy, dw) in sdoors:   # the SERVICE card on the door
        cm = np.zeros((PH, PW), np.uint8)
        cv2.rectangle(cm, (int(dx + 10), int(dy + 34)), (int(dx + dw - 10), int(dy + 74)), 255, -1)
        comp(t, cm, np.array([246, 240, 226], np.float32))
        lm = np.zeros((PH, PW), np.uint8)
        put_mask(lm, letter(["SERVICE"], 20, 9330 + k, weight=0.2), int(dx + dw / 2), int(dy + 54))
        comp(t, lm, RED)
    for ins in inside:  # the brass key on its hook with its SERVICE tag
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2 - 20, iy0 + (iy1 - iy0) * 0.30
        hook = np.zeros((PH, PW), np.uint8)
        cv2.circle(hook, (int(kx), int(ky - 52)), 6, 255, -1, cv2.LINE_AA)
        comp(t, hook, CARD)
        km = np.zeros((PH, PW), np.uint8)
        paste_mask(km, key_alpha(), kx, ky + 10, 0.24)
        comp(t, cv2.dilate(km, np.ones((3, 3), np.uint8)), CARD)
        comp(t, km, BRASS)
        tag = np.zeros((PH, PW), np.uint8)
        tx, ty = kx + 16, ky + 30
        cv2.fillPoly(tag, [np.int32([(tx, ty), (tx + 92, ty + 8), (tx + 88, ty + 40), (tx - 4, ty + 32)])], 255, cv2.LINE_AA)
        comp(t, tag, np.array([246, 240, 226], np.float32))
        lm = np.zeros((PH, PW), np.uint8)
        put_mask(lm, letter(["SERVICE"], 17, 9320 + k, weight=0.2), int(tx + 44), int(ty + 20))
        comp(t, lm, RED)
    return t, heads


# ------------------------------------------------------------------ the pendulum
def pivot(r):
    return np.array([1100.0, (TOP0 - 28) if r == 0 else TOPS[r] - GUT / 2])


def side(k):
    return -1 if k % 2 == 0 else 1        # left panels swing left, right panels swing right


def bob_pos(k):
    p = pivot(k // 2)
    a = math.radians(ROD_DEG) * side(k)
    return p + ROD_L * np.array([math.sin(a), math.cos(a)])


def ring_disc(theta, d):
    r = optics.render_rings(theta, 1.0)
    L, A = r["L"], r["A"]
    c = L[540 - 470:540 + 470, 960 - 470:960 + 470]
    a = A[540 - 470:540 + 470, 960 - 470:960 + 470]
    c = cv2.resize(c, (d, d), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (d, d), interpolation=cv2.INTER_AREA)
    return np.clip((200 - c) / 140, 0, 1) * a


def draw_trail(page, k):
    p, b = pivot(k // 2), bob_pos(k)
    # the dotted path of the swing, from the other extreme across the centre gutter to this one
    if True:
        s = side(k)
        a0, a1 = -s * math.radians(ROD_DEG), s * math.radians(ROD_DEG)
        dots = np.zeros(page.shape[:2], np.uint8)
        n = 15
        for i in range(n):
            a = a0 + (a1 - a0) * i / (n - 1)
            q = p + (ROD_L) * np.array([math.sin(a), math.cos(a)])
            if np.linalg.norm(q - b) < BOB_R + 18:
                continue
            cv2.circle(dots, (int(q[0]), int(q[1])), 7, 255, -1, cv2.LINE_AA)
        # ghost of the bob where this swing began
        q0 = p + ROD_L * np.array([math.sin(a0), math.cos(a0)])
        cv2.circle(dots, (int(q0[0]), int(q0[1])), BOB_R, 255, 4, cv2.LINE_AA)
        comp(page, dots, PENCIL, 0.75)


def draw_pendulum(page, k):
    p, b = pivot(k // 2), bob_pos(k)
    rod = np.zeros(page.shape[:2], np.uint8)
    u = (b - p) / np.linalg.norm(b - p)
    nrm = np.array([-u[1], u[0]])
    poly = [p + nrm * 9, b + nrm * 7, b - nrm * 7, p - nrm * 9]
    cv2.fillPoly(rod, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
    bob = np.zeros(page.shape[:2], np.uint8)
    cv2.circle(bob, (int(b[0]), int(b[1])), BOB_R, 255, -1, cv2.LINE_AA)
    penlib.shadow_onto(page, np.maximum(rod, bob), off=10, blur=7, opacity=0.45)
    comp(page, cv2.dilate(rod, np.ones((5, 5), np.uint8)), PRINT)
    comp(page, rod, BRASS)
    comp(page, cv2.dilate(bob, np.ones((7, 7), np.uint8)), PRINT)
    comp(page, bob, BRASS)
    d = 2 * (BOB_R - 10)
    ink = ring_disc(-k * math.pi / 3.5, d)
    hm = np.zeros(page.shape[:2], np.float32)
    x0, y0 = int(b[0] - d / 2), int(b[1] - d / 2)
    hm[y0:y0 + d, x0:x0 + d] = ink
    page[:] = page * (1 - hm[..., None] * 0.9) + BRASS_D * 0.35 * (hm[..., None] * 0.9)
    hub = np.zeros(page.shape[:2], np.uint8)
    cv2.circle(hub, (int(b[0]), int(b[1])), 30, 255, -1, cv2.LINE_AA)
    comp(page, hub, np.array([246, 238, 220], np.float32))
    nm = np.zeros(page.shape[:2], np.uint8)
    put_mask(nm, letter([str(k + 1)], 34, 9340 + k, weight=0.2), int(b[0]) + 2, int(b[1]))
    comp(page, nm, RED)
    pin = np.zeros(page.shape[:2], np.uint8)
    cv2.circle(pin, (int(p[0]), int(p[1])), 17, 255, -1, cv2.LINE_AA)
    comp(page, cv2.dilate(pin, np.ones((5, 5), np.uint8)), PRINT)
    comp(page, pin, BRASS)
    cv2.circle(pin, (int(p[0]), int(p[1])), 6, 255, -1)
    pin2 = np.zeros(page.shape[:2], np.uint8)
    cv2.circle(pin2, (int(p[0]), int(p[1])), 6, 255, -1, cv2.LINE_AA)
    comp(page, pin2, PRINT)


# ------------------------------------------------------------------ the page
def header(page):
    # the base of the clock's case, cut card: its pendulum hangs out of it into the page
    case = np.zeros(page.shape[:2], np.uint8)
    cv2.fillPoly(case, [np.int32(np.array([(960, 110), (1240, 110), (1210, 250), (990, 250)]) * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(page, case, off=10, blur=8, opacity=0.45)
    comp(page, case, np.array([58, 44, 34], np.float32))
    slot = np.zeros(page.shape[:2], np.uint8)
    cv2.rectangle(slot, (1060, 200), (1140, 250), 255, -1)
    comp(page, slot, np.array([30, 24, 20], np.float32))
    lm = np.zeros(page.shape[:2], np.uint8)
    blit_mask(lm, letter_left(["The station clock's pendulum:"], 44, 9350), 110, 150)
    comp(page, lm, PRINT)
    lm = np.zeros(page.shape[:2], np.uint8)
    m = letter_left(["one panel, one swing."], 44, 9351)
    blit_mask(lm, m, 2090 - m.shape[1] + 20, 150)
    comp(page, lm, PRINT)


def build(upto=7, pend_upto=None, trail=True):
    pend_upto = upto if pend_upto is None else pend_upto
    page = pen99.sheet99()
    header(page)
    boxes = []
    rec = []
    for k in range(8):
        x0, y0 = COLS[k % 2], TOPS[k // 2]
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        if k > upto:
            pm = np.zeros(page.shape[:2], np.uint8)
            cv2.rectangle(pm, (x0, y0), (x0 + PW, y0 + PH), 255, -1)
            comp(page, pm, CARD, 0.55)
            continue
        t, heads = scene(k)
        page[y0:y0 + PH, x0:x0 + PW] = t
        # caption slip, on the outer top corner (the rod comes in at the inner one)
        lines = wrap(CAPS[k], 32, {0: 700, 7: 250}.get(k, 560))
        bw = letter_left(lines, 32, 1).shape[1]
        cx = x0 + 18 if k % 2 == 0 else x0 + PW - bw - 18
        slip(page, cx, y0 + 16, lines, 32, 9360 + k, pad=(20, 12))
        bal = {2: (Q, 36, "her", (x0 + 450, y0 + 235)), 3: (A_, 38, "him", (x0 + 330, y0 + 215)),
               4: (TH, 38, "her", (x0 + 450, y0 + 225)), 7: (F, 34, "him", (x0 + 330, y0 + 110))}.get(k)
        r_ = dict(panel=k + 1, swing=k + 1, side="left" if side(k) < 0 else "right", event=EVENTS[k], caption=CAPS[k])
        if bal:
            lines_, cap_, who, at = bal
            tip = np.array([x0, y0]) + heads[who] + np.array([0, 20])
            balloon(page, lines_, cap_, at, tuple(tip), 9370 + k, tail_w=0.26, bend=0.10)
            r_["line"] = " ".join(lines_)
            r_["speaker"] = "STRANGER" if who == "her" else "AGENT"
        rec.append(r_)
    frame_border(page, boxes, w=9, seed=9390)
    for k in range(min(pend_upto, 7) + 1):
        draw_trail(page, k)
    for k in range(min(pend_upto, 7) + 1):
        draw_pendulum(page, k)
    return page, rec


def frame(k):
    page, _ = build(k, k)
    p = np.clip(np.round(page), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS))


if __name__ == "__main__":
    page, rec = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    json.dump(rec, open("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/p93_rec.json", "w"), indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        print("beats", save_beats(N, [frame(k) for k in range(8)]))
