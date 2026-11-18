"""Page 81 Quarter turns (reader and object; medium: spiral-disc).

Each tier is lettered in a different orientation; the reader turns the page a quarter turn (clockwise) per tier.
Four card bands, each holding three round disc prints (the b1m2 HANDMADE cut-paper figures printed in ink, as on
pages 06 and 46, via p46.scene) with their captions and balloons, and at its head a turning key: the anemic-cinema
O_A engraved ring disc (procedural, reused) with a red tier numeral and a cut-card arrow. Three tiers of four discs:
tier 1 is laid a quarter turn anticlockwise, tier 2 upside down, tier 3 a quarter turn clockwise, so no tier reads
upright as the page lies; turning the page clockwise a quarter at a time brings each tier upright in story order,
and a fourth turn brings the page (and its folio) home.
The folio line is the book's and stays upright. Beats: the page turned on the table, a quarter at a time; the tier
being read stays full, the others are paled.  Run: python3 -I p81_quarter_turns.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/anemic-cinema")
from b1m2 import *  # noqa
import p46_clock_face as P46  # noqa: E402  (scene(): the b1m2 cut-paper office scenes, upright prints)
import optics  # noqa: E402
import p11_station_cat as k11  # noqa: E402  (the les-caids wood table, for the beats only)

N, PID, TITLE = 81, "quarter-turns", "Quarter turns"
SHEET = pen99.sheet99()
CARD = np.array([238, 229, 208], np.float32)
PRINT = P46.PRINT
RED = P46.RED
TIERS_Y = [(110, 950), (980, 1820), (1850, 2690)]
TX0, TX1 = 110, 2090
ROT = [1, 2, 3]             # np.rot90 k per tier: 1 = laid a quarter turn anticlockwise (upright after one cw turn)

Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
TH = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]

# tier -> three discs: (event, scene, caption, balloon (lines, cap, who) or None)
TIERS = [
    [("E0", "desk", ["At his desk,", "the memo: 4:15,", "open the SERVICE", "door."], None),
     ("E0", "rise", ["He gets up", "to fetch", "the key."], None),
     ("E0", "walk", ["On his way", "across the", "office..."], None),
     ("E1", "ask", ["...a lady at", "the window."], (Q, 34, "her"))],
    [("E2", "look", ["He looks at the clock."], None),
     ("E2", "answer", ["He tells her:"], (A_, 34, "him")),
     ("E3", "thanks", ["She thanks him:"], (TH, 40, "her")),
     ("E3", "gone", ["And she goes."], None)],
    [("E4", "walk2", ["On to the", "cupboard."], None),
     ("E4", "open", ["He opens it."], None),
     ("E4", "key", ["There hangs", "the key, tagged", "SERVICE."], None),
     ("E5", "forget", ["The key stays", "on its hook;", "the SERVICE", "door stays shut."], (F, 30, "him"))],
]
TURN = ["one quarter turn", "two quarter turns", "three quarter turns"]


def ring_disc(d, theta=0.0):
    r = optics.render_rings(theta, 1.0)
    L, A = r["L"], r["A"]
    c = L[540 - 470:540 + 470, 960 - 470:960 + 470]
    a = A[540 - 470:540 + 470, 960 - 470:960 + 470]
    c = cv2.resize(c, (d, d), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (d, d), interpolation=cv2.INTER_AREA)
    return np.clip((200 - c) / 140, 0, 1) * a


def disc(c, cx, cy, R, ev, sc, cap, bal, seed, side=False):
    """one round print of the b1m2 cut-paper scene on canvas c (float RGB), its caption below."""
    hh, ww = c.shape[:2]
    t, view, heads = P46.scene(seed, sc)
    s = R / 345.0
    M = np.array([[s, 0, cx - view[0] * s], [0, s, cy - view[1] * s]], np.float32)
    pic = cv2.warpAffine(t, M, (ww, hh), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    pm = (((xx - cx) ** 2 + (yy - cy) ** 2) <= R ** 2).astype(np.uint8) * 255
    pm = cv2.GaussianBlur(pm, (3, 3), 0)
    penlib.shadow_onto(c, pm, off=6, blur=5, opacity=0.40)
    fa = (pm / 255.0)[..., None]
    c[:] = c * (1 - fa) + pic * fa
    bm = np.zeros((hh, ww), np.uint8)
    pts = [(cx + (R - 2) * math.cos(2 * math.pi * i / 400), cy + (R - 2) * math.sin(2 * math.pi * i / 400)) for i in range(401)]
    penlib.brush_line(bm, pts, 7, seed + 1, tremor=0.4)
    comp(c, bm, PRINT)
    rec = dict(event=ev, scene=sc, caption=" ".join(cap))
    if bal:
        lines, cap_, who = bal
        k = R / 188.0
        toP = lambda q: (cx + (q[0] - view[0]) * s, cy + (q[1] - view[1]) * s)
        tip = toP(heads[who] + np.array([0, 30]))
        balloon(c, lines, int(cap_ * k * 0.82), (cx + 22 * k, cy - R * 0.62), tip, seed + 2, tail_w=0.26, bend=0.10)
        rec["line"] = " ".join(lines)
        rec["speaker"] = "STRANGER" if who == "her" else "AGENT"
    m2 = np.zeros((hh, ww), np.uint8)
    if side:
        lm = letter_left(cap, 34, seed + 3, weight=0.14)
        blit_mask(m2, lm, int(cx + R + 30 - 34 * 0.6), int(cy - lm.shape[0] / 2))
    else:
        lm = letter(cap, 34, seed + 3, weight=0.14)
        blit_mask(m2, lm, int(cx - lm.shape[1] / 2), int(cy + R + 6))
    comp(c, m2, PRINT)
    return rec


def turn_key(c, cx, cy, d, n, label, theta, seed):
    """the turning key: the O_A ring disc printed in ink, the tier numeral in red, a cut-card arrow round it"""
    hh, ww = c.shape[:2]
    ring = ring_disc(d, theta)
    m = np.zeros((hh, ww), np.float32)
    x0, y0 = int(cx - d / 2), int(cy - d / 2)
    m[y0:y0 + d, x0:x0 + d] = ring
    c[:] = c * (1 - m[..., None] * 0.8) + PRINT * (m[..., None] * 0.8)
    pin = np.zeros((hh, ww), np.uint8)
    cv2.circle(pin, (int(cx), int(cy)), int(d * 0.20), 255, -1, cv2.LINE_AA)
    penlib.shadow_onto(c, pin, off=4, blur=3, opacity=0.4)
    comp(c, pin, CARD)
    nm = np.zeros((hh, ww), np.uint8)
    put_mask(nm, letter([str(n)], int(d * 0.24), seed, weight=0.2), int(cx), int(cy))
    comp(c, nm, RED)
    am = np.zeros((hh, ww), np.uint8)
    rr = d / 2 + 22
    arc = [(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))) for a in np.linspace(-150, 60, 60)]
    penlib.brush_line(am, arc, 12, seed + 1, tremor=0.2)
    e = arc[-1]
    tang = np.array([-math.sin(math.radians(60)), math.cos(math.radians(60))])
    nrm = np.array([math.cos(math.radians(60)), math.sin(math.radians(60))])
    head = [tuple(np.array(e) + tang * 34), tuple(np.array(e) + nrm * 22), tuple(np.array(e) - nrm * 22)]
    cv2.fillPoly(am, [np.int32(np.array(head) * 4)], 255, cv2.LINE_AA, shift=2)
    comp(c, am, RED)
    lm = letter([label], 28, seed + 2, weight=0.14)
    m2 = np.zeros((hh, ww), np.uint8)
    blit_mask(m2, lm, int(cx - lm.shape[1] / 2), int(cy + d / 2 + 34))
    comp(c, m2, RED)


def tier_canvas(i, theta=0.0):
    """the tier composed upright (as it reads after its turn); returns canvas (float RGB) and records"""
    y0, y1 = TIERS_Y[i]
    th, tw = y1 - y0, TX1 - TX0
    portrait = ROT[i] in (1, 3)
    cw, ch = (th, tw) if portrait else (tw, th)
    fib = (SHEET.mean(axis=2) - SHEET.mean())[:ch, :cw]
    c = CARD + fib[..., None] * 0.8
    recs = []
    if portrait:            # a tall column: key on top, four discs below, captions beside
        turn_key(c, cw / 2, 130, 150, i + 1, TURN[i], theta, 8100 + 10 * i)
        R = 196
        for k, (ev, sc, cap, bal) in enumerate(TIERS[i]):
            cy = 470 + k * 425
            recs.append(disc(c, 250, cy, R, ev, sc, cap, bal, 8130 + 40 * i + 7 * k, side=True))
    else:                   # a wide band: key at the left, four discs in a row, captions below
        turn_key(c, 160, ch / 2 - 40, 160, i + 1, TURN[i], theta, 8100 + 10 * i)
        R = 206
        for k, (ev, sc, cap, bal) in enumerate(TIERS[i]):
            cx = 460 + k * 432
            recs.append(disc(c, cx, 350, R, ev, sc, cap, bal, 8130 + 40 * i + 7 * k))
        lm = letter(["Now turn the page one more quarter, for the cupboard."], 34, 8199, weight=0.14)
        m2 = np.zeros(c.shape[:2], np.uint8)
        blit_mask(m2, lm, int(cw / 2 - lm.shape[1] / 2 + 80), 690)
        comp(c, m2, RED)
    return c, recs


def build(theta=0.0):
    page = SHEET.copy()
    recs = []
    boxes = []
    for i, (y0, y1) in enumerate(TIERS_Y):
        c, r = tier_canvas(i, theta)
        c = np.rot90(c, ROT[i]).copy()
        bm = np.zeros((H, W), np.uint8)
        bm[y0:y1, TX0:TX1] = 255
        penlib.shadow_onto(page, bm, off=8, blur=6, opacity=0.35)
        page[y0:y1, TX0:TX1] = c
        boxes.append((TX0, y0, TX1, y1))
        recs.append(dict(tier=i + 1, laid=["a quarter turn anticlockwise", "upside down", "a quarter turn clockwise"][i],
                    discs=r))
    frame_border(page, boxes, w=8, seed=8190)
    return page, recs


def turned(page, deg, focus):
    """a beat: the finished page lying on the table, turned deg clockwise; tiers other than `focus` paled."""
    p = page.astype(np.float32).copy()
    if focus is not None:
        for i, (y0, y1) in enumerate(TIERS_Y):
            if i != focus:
                p[y0:y1, TX0:TX1] = p[y0:y1, TX0:TX1] * 0.45 + 238 * 0.55
    tw, th = 960, 1242
    tab = cv2.resize(cv2.GaussianBlur(k11.wood(), (0, 0), 1.6), (tw, th), interpolation=cv2.INTER_AREA)
    s = min(tw, th) / math.hypot(W, H) * 1.0
    s = 0.40 if deg % 180 else 0.43
    if deg % 90:
        s = 0.36
    M = cv2.getRotationMatrix2D((W / 2, H / 2), -deg, s)
    M[0, 2] += tw / 2 - W / 2
    M[1, 2] += th / 2 - H / 2
    im = cv2.warpAffine(p, M, (tw, th), flags=cv2.INTER_AREA, borderValue=(0, 0, 0))
    mk = cv2.warpAffine(np.full((H, W), 255, np.uint8), M, (tw, th), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(tab, mk, off=6, blur=6, opacity=0.5)
    a = mk.astype(np.float32)[..., None] / 255
    return tab * (1 - a) + im * a


if __name__ == "__main__":
    page, recs = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    import json
    json.dump(recs, open("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/p81_rec.json", "w"), indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [turned(img, 0, None), turned(img, 45, 0), turned(img, 90, 0), turned(img, 135, 1),
                  turned(img, 180, 1), turned(img, 270, 2), turned(img, 360, None)]
        save_beats(N, frames)
