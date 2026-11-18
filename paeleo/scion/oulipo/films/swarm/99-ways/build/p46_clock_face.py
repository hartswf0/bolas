"""99 ways, page 46 "Clock face" (layout and page grammar; medium: spiral-disc).
The page is the station clock's dial made as a card disc: twelve round panels sit where the hours are, read
clockwise from twelve. Twelve is the memo; eleven, just before twelve again, is the forgetting. At the hub the
anemic-cinema engraved eccentric-ring disc (O_A, procedural, reused) is pinned, with one cut-card reading hand
that points at twelve. Figures: the b1m2 HANDMADE cut-paper model printed in ink (as page 06); the key: the ANRC 1922
cutout in brass. Beats: the reading hand sweeps from twelve round to eleven while the ring disc turns under it.
Run: python3 -I p46_clock_face.py [beats]"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema")
from b1m2 import *  # noqa
import optics  # noqa: E402  (anemic-cinema O_A engraved ring disc; procedural)

N, PID, TITLE = 46, "clock-face", "Clock face"
CX, CY = 1100, 1105
RD = 985                    # dial radius
RR, RP = 775, 188           # ring of panel centres, panel radius
RHUB = 330
TS = 960                    # scene tile
CARD = np.array([238, 229, 208], np.float32)
DIAL = np.array([244, 238, 222], np.float32)
PRINT = np.array([24, 21, 20], np.float32)
RED = np.array([168, 58, 40], np.float32)
BRASS = np.array([206, 154, 60], np.float32)
SHEET = pen99.sheet99()
FIG = 0.43
FEET = 800
ROMAN = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]

Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
TH = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]

# hour -> (event, scene, caption (None for a balloon panel), balloon (lines, cap, speaker))
PANELS = [
    ("E0", "desk", ["The memo:", "4:15, SERVICE door"], None),
    ("E0", "rise", ["He gets up", "for the key."], None),
    ("E0", "walk", ["Across", "the office."], None),
    ("E1", "ask", None, (Q, 34, "her")),
    ("E2", "look", ["He looks", "at the clock."], None),
    ("E2", "answer", None, (A_, 34, "him")),
    ("E3", "thanks", None, (TH, 40, "her")),
    ("E3", "gone", ["She goes."], None),
    ("E4", "walk2", ["On to", "the cupboard."], None),
    ("E4", "open", ["He opens it."], None),
    ("E4", "key", ["The key, on", "its hook."], None),
    ("E5", "forget", None, (F, 32, "him")),
]


def head_of(shapes, role):
    pts = np.concatenate([s.curve() for s in shapes if s.role == role])
    return np.array([pts[:, 0].mean(), pts[:, 1].min() + 60])


def scene(k, sc):
    """One upright print (TS x TS, card + ink) of the b1m2 cut-paper model; returns img, crop centre, heads."""
    t = np.zeros((TS, TS, 3), np.float32) + CARD
    cx, feet = TS / 2, FEET
    shapes, brass, heads = [], [], {}
    ag = None
    view = (cx, 560)
    if sc == "desk":
        ag = agent(cx + 40, feet - 10, face=1, scale=FIG, seated=True, tilt=14, sh=40, el=70, pencil_deg=60, lean=6)
        shapes += ag + desk(cx - 90, feet - 130, 260, feet) + lamp(cx + 250, feet - 250, 120)
    elif sc in ("rise", "walk", "walk2"):
        legs = {"rise": (6, -4), "walk": (22, -20), "walk2": (-8, 10)}[sc]
        lean = {"rise": 8, "walk": 0, "walk2": 2}[sc]
        ag = agent(cx + (60 if sc == "rise" else 0), feet, face=1, scale=FIG, legs=legs, lean=lean, sh=-20, el=20,
                   pencil_deg=200)
        shapes += ag
        if sc == "rise":
            shapes += desk(cx - 330, feet - 130, 220, feet) + lamp(cx - 230, feet - 250, 110)
        elif sc == "walk":
            ws, sill = window(cx - 380, feet - 420, 150, 420, sill=feet - 200, header=40)
            shapes += ws
        else:
            c, _ = cupboard(cx + 170, feet - 360, 150, 340, open_deg=0)
            shapes += c + service_door(cx + 350, feet - 420, 140, 420)
    elif sc in ("ask", "answer", "thanks", "gone"):
        ws, sill = window(cx - 300, feet - 430, 180, 430, sill=feet - 200, header=40)
        shapes += ws
        if sc != "gone":
            st = stranger(cx - 210, sill + 12, face=1, scale=0.66, glove=(sc == "ask"), nod=(8 if sc == "thanks" else 0))
            shapes += st
            heads["her"] = head_of(st, "skin_s")
        else:
            st = stranger(cx - 330, sill + 12, face=-1, scale=0.66)
            shapes += st
        face = -1 if sc != "gone" else 1
        ag = agent(cx + 120, feet, face=face, scale=FIG, legs=(4, -4) if sc != "gone" else (18, -16),
                   tilt=(-16 if sc == "answer" else 0), sh=6, el=16, pencil_deg=190)
        shapes += ag
        if sc == "answer":
            shapes += clock(cx + 300, feet - 560, 46, swing=6)
        view = (cx - 40, 545)
    elif sc == "look":
        shapes += clock(cx - 150, feet - 470, 62, swing=8)
        ag = agent(cx + 80, feet, face=-1, scale=FIG, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
        shapes += ag
    elif sc in ("open", "forget"):
        c, ins = cupboard(cx - 250, feet - 360, 150, 340, open_deg=112)
        shapes += c + service_door(cx + 270, feet - 430, 140, 430)
        brass.append(ins)
        if sc == "forget":
            ag = agent(cx + 40, feet, face=-1, scale=FIG, legs=(3, -3), sh=48, el=118, wr=8, pencil_deg=40, tilt=-6)
        else:
            ag = agent(cx + 30, feet, face=-1, scale=FIG, legs=(12, -10), sh=40, el=40, wr=0, pencil_deg=200)
        shapes += ag
    elif sc == "key":
        c, ins = cupboard(cx - 210, 140, 420, 760, open_deg=0.1)
        s_in = [R_(cx - 190, 160, cx + 190, 880, "inside", hole=True, z=1)]
        shapes += c + s_in
    if ag is not None:
        heads["him"] = head_of(ag, "skin")
    m = raster(shapes, TS, TS)
    comp(t, m, PRINT)
    if sc == "desk":                              # the memo slip on the desk, pencilled 4:15
        mm_ = np.zeros((TS, TS), np.uint8)
        cv2.fillPoly(mm_, [np.int32([(cx - 120, feet - 150), (cx + 10, feet - 158), (cx + 14, feet - 118), (cx - 116, feet - 110)])], 255, cv2.LINE_AA)
        comp(t, mm_, np.array([250, 247, 238], np.float32))
        lm = np.zeros((TS, TS), np.uint8)
        put_mask(lm, letter(["4:15"], 30, 4605, weight=0.18), int(cx - 52), int(feet - 136))
        comp(t, lm, RED)
    if sc == "key":                               # close-up: the key on its hook, its SERVICE tag
        hook = np.zeros((TS, TS), np.uint8)
        cv2.rectangle(hook, (int(cx - 10), 230), (int(cx + 10), 270), 255, -1)
        cv2.ellipse(hook, (int(cx), 280), (22, 22), 0, 0, 200, 255, 10, cv2.LINE_AA)
        comp(t, hook, PRINT)
        ka = key_alpha()
        km = np.zeros((TS, TS), np.uint8)
        paste_mask(km, ka, cx + 6, 300 + ka.shape[0] * 0.62 / 2, 0.62, 2)
        comp(t, cv2.dilate(km, np.ones((5, 5), np.uint8)), PRINT)
        comp(t, km, BRASS)
        tag = np.zeros((TS, TS), np.uint8)
        poly = np.array([(cx + 60, 560), (cx + 230, 585), (cx + 220, 655), (cx + 50, 630)], np.int32)
        cv2.fillPoly(tag, [poly], 255, cv2.LINE_AA)
        thread = np.zeros((TS, TS), np.uint8)
        penlib.brush_line(thread, [(cx + 14, 330), (cx + 64, 568)], 4, 46, tremor=0.4)
        comp(t, thread, PRINT)
        comp(t, cv2.dilate(tag, np.ones((5, 5), np.uint8)), PRINT)
        comp(t, tag, np.array([246, 240, 226], np.float32))
        lt = letter(["SERVICE"], 40, 4601, weight=0.17)
        lm = np.zeros((TS, TS), np.uint8)
        put_mask(lm, lt, int(cx + 140), 608)

        Mr = cv2.getRotationMatrix2D((cx + 140, 608), -8, 1.0)
        comp(t, cv2.warpAffine(lm, Mr, (TS, TS)), RED)
        view = (cx, 470)
    for ins in brass:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.45
        km = np.zeros((TS, TS), np.uint8)
        paste_mask(km, key_alpha(), kx, ky, 0.25)
        comp(t, cv2.dilate(km, np.ones((3, 3), np.uint8)), PRINT)
        comp(t, km, BRASS)
    return t, view, heads


def panel_centre(h):
    a = math.radians(h * 30)
    return CX + RR * math.sin(a), CY - RR * math.cos(a)


def hub_rings(theta):
    """anemic-cinema O_A ring disc (2x canvas), cropped to its plate and printed in ink on the dial card."""
    r = optics.render_rings(theta, 1.0)
    L, A = r["L"], r["A"]
    c = L[540 - 470:540 + 470, 960 - 470:960 + 470]
    a = A[540 - 470:540 + 470, 960 - 470:960 + 470]
    d = 2 * RHUB
    c = cv2.resize(c, (d, d), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (d, d), interpolation=cv2.INTER_AREA)
    ink = np.clip((200 - c) / 140, 0, 1) * a          # the engraved grooves as ink
    return ink


def build(hand_hour=0.0, read_upto=11, theta=0.0, swing=0.0):
    page = SHEET.copy()
    # the clock's pendulum case under the dial (cut card), its window cut through to the sheet
    case = np.zeros((H, W), np.uint8)
    cv2.fillPoly(case, [np.int32(np.array([(760, 1990), (1440, 1990), (1400, 2690), (1100, 2730), (800, 2690)]) * 4)],
                 255, cv2.LINE_AA, shift=2)
    win = np.zeros((H, W), np.uint8)
    cv2.rectangle(win, (930, 2160), (1270, 2600), 255, -1, cv2.LINE_AA)
    penlib.shadow_onto(page, case, off=14, blur=10, opacity=0.45)
    comp(page, case, np.array([58, 44, 34], np.float32))
    comp(page, win, np.array([236, 230, 214], np.float32))
    sw = math.radians(swing)
    top = np.array([1100.0, 2170.0])
    bob = top + 330 * np.array([math.sin(sw), math.cos(sw)])
    pm_ = np.zeros((H, W), np.uint8)
    penlib.brush_line(pm_, [tuple(top), tuple(bob)], 9, 4695, tremor=0.2)
    comp(page, pm_, PRINT)
    bm_ = np.zeros((H, W), np.uint8)
    cv2.circle(bm_, (int(bob[0]), int(bob[1])), 62, 255, -1, cv2.LINE_AA)
    comp(page, cv2.dilate(bm_, np.ones((7, 7), np.uint8)), PRINT)
    comp(page, bm_, BRASS)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2)
    disc = (rr <= RD).astype(np.uint8) * 255
    penlib.shadow_onto(page, disc, off=14, blur=10, opacity=0.45)
    fib = (SHEET.mean(axis=2) - SHEET.mean())
    dial = DIAL + fib[..., None] * 0.8
    a = (disc / 255.0)[..., None]
    page[:] = page * (1 - a) + dial * a
    ink = np.zeros((H, W), np.uint8)
    for rad, wd in ((RD - 8, 8), (RD - 26, 3), (RHUB + 50, 4)):
        pts = [(CX + rad * math.sin(2 * math.pi * i / 900), CY - rad * math.cos(2 * math.pi * i / 900)) for i in range(901)]
        penlib.brush_line(ink, pts, wd, int(rad), tremor=0.3)
    # minute ticks on the rim
    for i in range(60):
        if i % 5 == 0:
            continue
        a_ = math.radians(i * 6)
        p0 = (CX + (RD - 26) * math.sin(a_), CY - (RD - 26) * math.cos(a_))
        p1 = (CX + (RD - 8) * math.sin(a_), CY - (RD - 8) * math.cos(a_))
        penlib.brush_line(ink, [p0, p1], 4, 4700 + i, tremor=0.2)
    comp(page, ink, PRINT)
    rec = []
    for h, (ev, sc, cap, bal) in enumerate(PANELS):
        t, view, heads = scene(h, sc)
        s = RP / 345.0
        px, py = panel_centre(h)
        M = np.array([[s, 0, px - view[0] * s], [0, s, py - view[1] * s]], np.float32)
        pic = cv2.warpAffine(t, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        pm = ((xx - px) ** 2 + (yy - py) ** 2 <= RP ** 2).astype(np.uint8) * 255
        pm = cv2.GaussianBlur(pm, (3, 3), 0)
        penlib.shadow_onto(page, pm, off=6, blur=5, opacity=0.40)
        fa = (pm / 255.0)[..., None]
        page[:] = page * (1 - fa) + pic * fa
        bm = np.zeros((H, W), np.uint8)
        pts = [(px + (RP - 2) * math.cos(2 * math.pi * i / 400), py + (RP - 2) * math.sin(2 * math.pi * i / 400)) for i in range(401)]
        penlib.brush_line(bm, pts, 7, 4620 + h, tremor=0.4)
        comp(page, bm, PRINT)
        toP = lambda q: (px + (q[0] - view[0]) * s, py + (q[1] - view[1]) * s)
        r_ = dict(hour=ROMAN[h], event=ev, scene=sc)
        if cap:
            lm = letter(cap, 28, 4640 + h, weight=0.15)
            bh, bw = lm.shape
            y0 = int(py + RP * 0.84 - bh)
            slipm = np.zeros((H, W), np.uint8)
            cv2.rectangle(slipm, (int(px - bw / 2 + 12), y0 + 6), (int(px + bw / 2 - 12), y0 + bh - 2), 255, -1)
            slipm = (slipm.astype(np.float32) * (pm / 255.0)).astype(np.uint8)
            penlib.shadow_onto(page, slipm, off=3, blur=2, opacity=0.3)
            comp(page, slipm, np.array([250, 246, 236], np.float32))
            m2 = np.zeros((H, W), np.uint8)
            blit_mask(m2, lm, int(px - bw / 2), y0)
            comp(page, m2, PRINT)
            r_["caption"] = " ".join(cap)
        if bal and h <= read_upto:
            lines, cap_, who = bal
            tip = toP(heads[who] + np.array([0, 30]))
            bw = letter(lines, cap_, 1).shape[1]
            at = (px + 25, py - RP * 0.66)
            balloon(page, lines, cap_, at, tip, 4660 + h, tail_w=0.26, bend=0.10)
            r_["line"] = " ".join(lines)
            r_["speaker"] = "STRANGER" if who == "her" else "AGENT"
        rec.append(r_)
        # hour numeral on the dial, just inside the panel
        a_ = math.radians(h * 30)
        nx, ny = CX + (RR - RP - 50) * math.sin(a_), CY - (RR - RP - 50) * math.cos(a_)
        nm = np.zeros((H, W), np.uint8)
        put_mask(nm, letter([ROMAN[h]], 44, 4680 + h, weight=0.18), int(nx), int(ny))
        comp(page, nm, RED)
        if h > read_upto:
            dim = (pm / 255.0 * 0.72)[..., None]
            page[:] = page * (1 - dim) + DIAL * dim
    # hub: the engraved ring disc, pinned, turning with the reading
    ring = hub_rings(theta)
    hm = np.zeros((H, W), np.float32)
    hm[CY - RHUB:CY + RHUB, CX - RHUB:CX + RHUB] = ring
    page[:] = page * (1 - hm[..., None] * 0.85) + PRINT * (hm[..., None] * 0.85)
    # the reading hand: a cut-card hand pinned at the hub, pointing at the hour being read
    ah = math.radians(hand_hour * 30)
    u = np.array([math.sin(ah), -math.cos(ah)])
    nrm = np.array([-u[1], u[0]])
    c0 = np.array([CX, CY], float)
    L1 = RR - RP - 100
    poly = [c0 - u * 90 + nrm * 16, c0 + u * (L1 - 70) + nrm * 12, c0 + u * (L1 - 70) + nrm * 40, c0 + u * L1,
            c0 + u * (L1 - 70) - nrm * 40, c0 + u * (L1 - 70) - nrm * 12, c0 - u * 90 - nrm * 16]
    hmask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(hmask, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
    cv2.circle(hmask, (CX, CY), 40, 255, -1, cv2.LINE_AA)
    penlib.shadow_onto(page, hmask, off=8, blur=6, opacity=0.45)
    comp(page, hmask, RED)
    pin = np.zeros((H, W), np.uint8)
    cv2.circle(pin, (CX, CY), 16, 255, -1, cv2.LINE_AA)
    comp(page, pin, np.array([92, 84, 70], np.float32))
    # legend beside the case
    lg = np.zeros((H, W), np.uint8)
    blit_mask(lg, letter_left(["Read it like the", "station clock:", "start at twelve", "and go round.", "Just before twelve",
                               "again, he has", "forgotten why", "he came."], 44, 4690), 130, 2190)
    comp(page, lg, PRINT)
    lg = np.zeros((H, W), np.uint8)
    blit_mask(lg, letter_left(["XII  the memo", "III  her question", "V  his answer", "VI  her thanks", "IX  the cupboard",
                               "XI  the forgetting"], 40, 4691), 1560, 2190)
    comp(page, lg, RED)
    return page, rec


def frame(hh, upto, theta, swing):
    page, _ = build(hh, upto, theta, swing)
    p = np.clip(np.round(page), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS))


BEAT_STOPS = [(0, 0), (2, 2), (4, 4), (6, 6), (8, 8), (10, 10), (11, 11), (11.9, 11)]

if __name__ == "__main__":
    page, rec = build(0.0, 11, 0.0)
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        save_beats(N, [frame(hh, up, -hh * math.pi / 6, 9.0 * (-1) ** i) for i, (hh, up) in enumerate(BEAT_STOPS)])
        import json
        json.dump(rec, open("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/p46_rec.json", "w"), indent=1)
