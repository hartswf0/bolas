"""99 ways, page 49 "Epic" (voice and language; medium: engraving-puppet).
Captions in an inflated heroic register: the errand a quest, the cupboard a vault, the question a summons.
A storyboard sheet headed THE QUEST OF THE BRASS KEY, six boards called cantos (I-VI), each a strip of cream card
with the ENGRAVING PUPPETS of page 03 (AGENT = the Harper's Weekly 1863 telegraph operator, LoC cph.3c11072, cut at
the joints and pinned; STRANGER = the hatted woman of the 1867 Steinway Hall engraving, LoC cph.3c32079; his table
and the window from the 1863 plate), the set in the shared pen hand, the four canon lines verbatim in cut-paper
balloons, and pasted torn commentary slips that tell it as an epic (invocation of the Muse, epithets, 'lo!').
Reuses films/swarm/99-ways/kit/build_page03.py. Run: python3 -I p49_epic.py"""
import json
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import build_page03 as b3  # noqa: E402
import b1m2 as B  # noqa: E402

N, PID, TITLE = 49, "epic", "Epic"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, letters, Mof, lay = b3.pen, b3.letters, b3.Mof, b3.lay

Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]

# board boxes (x0, y0, w, h), laid out below from the measured heights of the commentary slips
BW = {1: (110, 1980, 390), 2: (110, 970, 372), 3: (1120, 970, 372), 4: (110, 970, 372), 5: (1120, 970, 372),
      6: (110, 1980, 380)}
CANTO = {1: ("I", "E0", "4:09"), 2: ("II", "E1", "4:10"), 3: ("III", "E2", "4:10"), 4: ("IV", "E3", "4:10"),
         5: ("V", "E4", "4:11"), 6: ("VI", "E5", "4:11")}
SLIPS = {
    1: "Sing, O Muse, of the Agent of Randolph, keeper of the hours! Upon his desk the sacred scroll laid its command: "
       "at the fourth hour and the quarter the Door of SERVICE must be opened, and the Key lies in the Vault. "
       "Then rose the hero and set forth upon the Quest.",
    2: "But lo! as he strode the great hall, a stranger from far lands cried a summons through the gate of glass.",
    3: "And he lifted his eyes to the mighty Orb of the Hours, that never sleeps, and gave answer.",
    4: "Then the far-travelled one gave thanks, as wayfarers have ever done, and passed from the gate into the west.",
    5: "Onward to the Vault strode the hero and flung wide its door: lo, the Brass Key, bearing the rune SERVICE!",
    6: "But the jealous gods had stolen his purpose from his breast. Pencil to chin he stood before the open Vault, "
       "and spoke unto his own heart. So the Key hung on, unclaimed; the Door of SERVICE stayed sealed. Here ends the Quest.",
}
SCAP = 31
HDR_H, TOP0 = 44, 346


def slip_h(n):
    w = BW[n][1]
    let = B.letter_left(B.wrap(SLIPS[n], SCAP, w - 90), SCAP, 5000 + n)
    return let.shape[0] + int(SCAP * 0.9)


def layout():
    rows = [(1,), (2, 3), (4, 5), (6,)]
    need = sum(HDR_H + max(BW[n][2] for n in r) + 12 + max(slip_h(n) for n in r) for r in rows)
    gap = (2725 - TOP0 - need) / (len(rows) - 1)
    assert gap >= 12, gap
    bx, y = {}, TOP0
    for r in rows:
        for n in r:
            bx[n] = (BW[n][0], int(y + HDR_H), BW[n][1], BW[n][2])
        y += HDR_H + max(BW[n][2] for n in r) + 12 + max(slip_h(n) for n in r) + gap
    return bx


BX = layout()


def balloon(c, lines, cap, centre, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.20, bend=0.08)
    penlib.lay_balloon(c, b, centre)


def card(w, h, seed):
    return np.zeros((h, w, 3), np.float32) + b3.CARD + (np.random.RandomState(seed).rand(h, w, 1) - 0.5) * 0.8


def window_board(c, P, wx, gy, woman_at, woman_flip, seed):
    """the 1863 plate's window cut out as the gate of glass, TICKET OFFICE lettered beneath; her puppet outside it"""
    Mw = Mof(1.05, 0, np.array([140, 280]) * OPS, (wx, 175))
    lay(c, P["window"], Mw)
    letters(c, ["TICKET", "OFFICE"], 22, wx, 300, seed)
    if woman_at is not None:
        b3.woman(c, P, (woman_at, gy + 2), 0.44, flip=woman_flip)


def board(n, P, with_line=True):
    x0, y0, w, h = BX[n]
    c = card(w, h, 4900 + n)
    gy = h - 30
    b3.ground_line(c, 0, w, gy, 4910 + n)
    s = 0.33
    if n == 1:      # E0: the scroll on the desk; the hero rises, arm flung toward the far Vault
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (330, gy + 2)))
        b3.memo(c, 285, 186, 0.62, 4920, deg=-4)
        b3.clock(c, 1040, 92, 44, 4, 9, 4921)
        b3.cupboard(c, 1480, 70, 1680, gy - 20, 0.0, 4922)
        b3.service_door(c, 1740, 54, 1900, gy, 4923)
        b3.agent(c, P, (720, gy + 2), 0.35, arms=(-112, 10, -10), head=8, flip=True)
    elif n == 2:    # E1: the summons through the glass
        window_board(c, P, 560, gy, 740, False, 4930)
        b3.agent(c, P, (300, gy + 2), s, arms=(12, 0, -8), flip=True, head=6)
        if with_line:
            balloon(c, Q, 36, (790, 98), (735, 156), 4931)
    elif n == 3:    # E2: the Orb of the Hours at 4:10, and his answer
        b3.clock(c, 140, 96, 54, 4, 10, 4940)
        window_board(c, P, 600, gy, 790, False, 4941)
        b3.agent(c, P, (360, gy + 2), s, arms=(60, 150, 0), head=-14, flip=True)
        if with_line:
            balloon(c, A, 34, (590, 66), (390, 110), 4942)
    elif n == 4:    # E3: her thanks, lingering as she turns away into the west
        window_board(c, P, 520, gy, 820, True, 4950)
        b3.agent(c, P, (270, gy + 2), s, arms=(0, 0, 0), flip=True, head=10)
        if with_line:
            balloon(c, T, 38, (700, 92), (800, 150), 4951)
    elif n == 5:    # E4: the Vault flung wide
        b3.service_door(c, 740, 60, 900, gy, 4960)
        b3.cupboard(c, 430, 70, 650, gy - 20, 0.8, 4961)
        b3.agent(c, P, (240, gy + 2), s, arms=(-62, 30, 0), flip=True)
    else:           # E5: pencil to chin before the open Vault; the Key unclaimed; the Door sealed
        lay(c, P["table"], Mof(0.36, 0, np.array([250, 980]) * OPS, (250, gy + 2)))
        b3.memo(c, 210, 176, 0.56, 4970, deg=-4)
        b3.cupboard(c, 1060, 60, 1280, gy - 20, 1.0, 4971)
        b3.service_door(c, 1400, 44, 1570, gy, 4972)
        hnd = b3.agent(c, P, (900, gy + 2), 0.30, arms=(47, 132, 0), head=-6, flip=True)
        pen(c, [(hnd[0] + 2, hnd[1] + 4), (hnd[0] - 6, hnd[1] - 34)], 5, 4973)
        if with_line:
            balloon(c, F, 36, (620, 80), (900, 120), 4974)
    return c


def title_slip(pg, seed=4990):
    """the sheet's head: a wide torn slip lettered as the epic's title page"""
    t1 = pen99.letter(["THE QUEST OF THE BRASS KEY"], 72, seed, weight=0.12)
    t2 = pen99.letter(["an epic of Randolph station, in six cantos"], 34, seed + 1)
    ww = max(t1.shape[1], t2.shape[1]) + 120
    hh = t1.shape[0] + t2.shape[0] - 10
    x, y = (W - ww) // 2, 118
    rnd = random.Random(seed)
    m = np.zeros(pg.shape[:2], np.uint8)
    tear_b = [(x + ww - k, y + hh + rnd.uniform(-5, 4)) for k in range(0, ww, 14)]
    tear_t = [(x + k, y + rnd.uniform(-4, 3)) for k in range(0, ww, 14)]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in tear_t + [(x + ww, y)] + tear_b + [(x, y + hh)]])], 255,
                 cv2.LINE_AA, shift=2)
    penlib.shadow_onto(pg, m, off=5, blur=4, opacity=0.3)
    pg[:] = pg * (1 - m[..., None] / 255) + b3.SLIPC * (m[..., None] / 255)
    for mm, yy in ((t1, y + 4), (t2, y + t1.shape[0] - 18)):
        sub = np.zeros(pg.shape[:2], np.uint8)
        xx = (W - mm.shape[1]) // 2
        sub[yy:yy + mm.shape[0], xx:xx + mm.shape[1]] = mm
        penlib.ink_onto(pg, sub, penlib.INK)
    # a hand-drawn laurel sprig either side of the title, pen line
    for side in (-1, 1):
        cx = W / 2 + side * (t1.shape[1] / 2 + 10)
        cy = y + 60
        lm = np.zeros(pg.shape[:2], np.uint8)
        stem = [(cx, cy + 46), (cx + side * 18, cy + 10), (cx + side * 22, cy - 36)]
        penlib.brush_line(lm, stem, 3.5, seed + 10 + side)
        for k in range(5):
            t_ = k / 4
            px = cx + side * (4 + 18 * t_)
            py = cy + 40 - 72 * t_
            for d in (-1, 1):
                q = (px + d * 16 - side * 2, py - 10)
                penlib.brush_line(lm, [(px, py), ((px + q[0]) / 2 + d * 3, (py + q[1]) / 2 - 5), q], 3, seed + 20 + k * 3 + d)
        penlib.ink_onto(pg, lm, penlib.INK)
    pin_ = b3.pin
    pin_(pg, x + 22, y + 20, 7)
    pin_(pg, x + ww - 22, y + 20, 7)


def slip_left(pg, lines, cap, x, y, seed):
    """a torn commentary slip, left-aligned lettering (as build_page03.slip but ragged-left-aligned)"""
    let = B.letter_left(lines, cap, seed)
    lh, lw = let.shape
    ww, hh = lw + int(cap * 1.4), lh + int(cap * 0.9)
    rnd = random.Random(seed)
    m = np.zeros(pg.shape[:2], np.uint8)
    pts = [(x, y + rnd.uniform(0, 4)), (x + ww, y + rnd.uniform(0, 4))]
    tear = [(x + ww - k, y + hh + rnd.uniform(-4, 3)) for k in range(0, ww, 14)]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in pts + tear + [(x, y + hh)]])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(pg, m, off=4, blur=3, opacity=0.3)
    pg[:] = pg * (1 - m[..., None] / 255) + b3.SLIPC * (m[..., None] / 255)
    sub = np.zeros(pg.shape[:2], np.uint8)
    B.blit_mask(sub, let, int(x + cap * 0.95 - cap * 0.6 + 10), int(y + cap * 0.35))
    penlib.ink_onto(pg, sub, penlib.INK)
    b3.pin(pg, x + 14, y + 14, 6)
    return ww, hh


SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.8)   # the LoC sheet, its scan grain softened (file size)


def build(upto=6, line_on=True):
    pg = SHEET.copy()
    P = b3.load_puppets()
    title_slip(pg)
    for n in range(1, 7):
        if n > upto:
            continue
        x0, y0, w, h = BX[n]
        roman, ev, t = CANTO[n]
        hdr = pen99.letter([f"CANTO {roman}    {ev}    {t}"], 32, 4980 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        sub[y0 - 46:y0 - 46 + hdr.shape[0], x0 - 14:x0 - 14 + hdr.shape[1]] = hdr
        penlib.ink_onto(pg, sub, b3.GRAPH)
        pg[y0:y0 + h, x0:x0 + w] = board(n, P, with_line=(line_on or n < upto))
        bm = penlib.border_mask(pg.shape[:2], [(x0, y0, x0 + w, y0 + h)], 7, 4985 + n)
        penlib.ink_onto(pg, bm)
        hole = np.zeros(pg.shape[:2], np.uint8)
        cv2.circle(hole, (x0 + 24, y0 + 24), 9, 255, -1, cv2.LINE_AA)
        penlib.ink_onto(pg, hole, hexc("#2a2622"))
        lines = B.wrap(SLIPS[n], SCAP, w - 90)
        slip_left(pg, lines, SCAP, x0 + 8, y0 + h + 12, 5000 + n)
    return pg


def main():
    page = build(6)
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    frames = []
    # b01 the head only; then canto by canto; cantos with a spoken line arrive first silent, then the balloon is laid
    # canto by canto (the head arrives with canto I); cantos II and VI arrive silent, then their balloon is laid
    for n in range(1, 7):
        frames.append(build(n, line_on=(n not in (2, 6))))
        if n in (2, 6):
            frames.append(build(n))
    for f in frames:
        pen99.folio(f, N, TITLE)
    nb = B.save_beats(N, frames)
    print("beats", nb)


if __name__ == "__main__":
    main()
