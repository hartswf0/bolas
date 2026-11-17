"""Page 26 A to Z (formal / Oulipian rule; medium: engraving-puppet).

Twenty-six small captions in order, the first word of each beginning with the next letter of the alphabet.
A storyboard sheet of seven boards (E0-E5 in order; the last board full width) with the page-03 engraving
puppets (Harper's 1863 telegraph operator as the AGENT, pinned at the joints; the 1867 Steinway Hall woman
as the STRANGER) and the HANDMADE pen set; under each board, pasted torn slips pinned with brass pins carry
the captions, each opening on a red pen initial. The four canon lines are quoted verbatim inside captions
H, K, M and V. Writes page, master, beats (slips pinned one board at a time), record.
"""
import math
import random
import re
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import build_page03 as K3  # noqa: E402  (engraving puppets, pen set, pins)
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import b1m2  # noqa: E402

N, PID, TITLE = 26, "a-to-z", "A to Z"
W, H = pen99.PAGE_W, pen99.PAGE_H
INK = penlib.INK
RED = hexc("#9c2a1c")
GRAPH = K3.GRAPH
CARD, SLIPC = K3.CARD, K3.SLIPC

LN = {k: v["text"] for k, v in K3.CANON["incident"]["lines"].items()}

CAPS = [  # (board, caption) in alphabetical order
    (1, "At Randolph, the agent at his desk."),
    (1, "Before him, a memo:"),
    (1, "Clear enough: '4:15 - open SERVICE door. Key in cupboard.'"),
    (2, "Dutifully he rises."),
    (2, "Errand in mind, he sets off across the office."),
    (3, "From the window, a voice."),
    (3, "Gloved, hatted, a stranger leans in."),
    (3, "Her words: 'Pardon me — have you the right time?'"),
    (4, "In reply he turns to the clock."),
    (4, "Just ten past four."),
    (4, "Kindly he answers: 'Ten past four, by the clock.'"),
    (5, "Lightly she nods."),
    (5, "'Much obliged!' she says."),
    (5, "Now the window is empty."),
    (6, "On he goes to the cupboard."),
    (6, "Pulling the door, he opens it."),
    (6, "Quite plainly:"),
    (6, "Right on its hook, the key, tagged SERVICE."),
    (7, "Silence."),
    (7, "The pencil drifts to his chin."),
    (7, "Unable to think why he came, he asks himself,"),
    (7, "very quietly: 'Well, here I am... and what for?'"),
    (7, "Words fail him."),
    (7, "X marks the spot: the key still hangs there."),
    (7, "Yet he never takes it."),
    (7, "Zero errands done: the SERVICE door stays closed."),
]
# fix V: the caption must START with a V word
CAPS[21] = (7, "Very quietly: 'Well, here I am... and what for?'")
CAPS[20] = (7, "Unable to think why he came, he asks himself:")


def initial_of(s):
    m = re.search(r"[A-Za-z]", s)
    return m.start(), s[m.start()].upper()


def check():
    assert len(CAPS) == 26
    got = "".join(initial_of(c)[1] for _, c in CAPS)
    assert got == "ABCDEFGHIJKLMNOPQRSTUVWXYZ", got
    joined = " ".join(c for _, c in CAPS)
    for k, v in LN.items():
        assert v in joined, (k, v)
    return got


# ------------------------------------------------------------------ boards
X0, X1 = 110, 2090
COLX = [(110, 1080), (1120, 2090)]
ROWY = [110, 712, 1314, 1916]
PW, PH = 970, 310
BIG_W, BIG_H = 1980, 430


def panel(n, P, w=PW, h=PH):
    c = np.zeros((h, w, 3), np.float32) + CARD + (np.random.RandomState(260 + n).rand(h, w, 1) - 0.5) * 3
    gy = h - 30
    K3.ground_line(c, 0, w, gy, 2600 + n)
    s = 0.26 if n < 7 else 0.36
    if n == 1:      # E0 the desk and the memo; he is seated-standing at it, reading
        K3.lay(c, P["table"], K3.Mof(0.37, 0, np.array([250, 980]) * K3.OPS, (420, gy + 2)))
        K3.memo(c, 370, 150, 0.62, 2610, deg=-5)
        K3.agent(c, P, (640, gy + 2), s, arms=(28, 40, 0), head=8)
        K3.clock(c, 860, 70, 34, 4, 8, 2611)
    elif n == 2:    # E0 rising and setting off: desk behind, cupboard ahead
        K3.lay(c, P["table"], K3.Mof(0.37, 0, np.array([250, 980]) * K3.OPS, (180, gy + 2)))
        K3.cupboard(c, 760, 70, 920, gy - 16, 0.0, 2620)
        K3.agent(c, P, (470, gy + 2), s, arms=(14, 0, -10), flip=True)
    elif n in (3, 4, 5):   # the ticket window between them
        Mw = K3.Mof(0.95, 0, np.array([140, 280]) * K3.OPS, (560, 160))
        if n == 4:
            K3.clock(c, 140, 84, 44, 4, 10, 2640)
        K3.agent(c, P, (330 if n != 5 else 300, gy + 2), s, arms=((60, 150, 0) if n == 4 else (6, 0, 0)),
                 head=(-14 if n == 4 else 0), flip=(n != 5))
        K3.lay(c, P["window"], Mw)
        K3.letters(c, ["TICKET", "OFFICE"], 20, 560, 270, 2650 + n)
        if n == 5:
            K3.woman(c, P, (830, gy + 2), 0.40, flip=True)
        else:
            K3.woman(c, P, (720, gy + 2), 0.40)
    elif n == 6:    # E4 opening the cupboard, the key on its hook
        K3.service_door(c, 740, 50, 900, gy, 2660)
        K3.cupboard(c, 440, 60, 640, gy - 16, 0.8, 2661)
        K3.agent(c, P, (260, gy + 2), s, arms=(-62, 30, 0), flip=True)
    elif n == 7:    # E5 the wide last board: before the open cupboard, pencil to his chin
        K3.clock(c, 300, 100, 56, 4, 11, 2670)
        K3.service_door(c, 1270, 60, 1460, gy, 2671)
        K3.cupboard(c, 950, 70, 1190, gy - 16, 1.0, 2672)
        hd = K3.agent(c, P, (820, gy + 2), s, arms=(47, 132, 0), head=-6, flip=True)
        K3.pen(c, [(hd[0] + 2, hd[1] + 4), (hd[0] - 6, hd[1] - 30)], 5, 2673)
        K3.lay(c, P["table"], K3.Mof(0.48, 0, np.array([250, 980]) * K3.OPS, (1740, gy + 2)))
        K3.memo(c, 1710, 200, 0.7, 2674, deg=4)
    return c


# ------------------------------------------------------------------ caption slips with a red initial
def seg_mask(segments, seed, capmax):
    """Compose [(text, cap, colour_key, gap_before)] on one baseline, cropped to ink. Returns (ink, red, width)."""
    ms = []
    for i, (t, cap, col, gap) in enumerate(segments):
        if not t.strip():
            continue
        m = pen99.letter([t.strip()], cap, seed + i, weight=0.17 if col == "red" else 0.13)
        cols = np.where(m.max(0) > 40)[0]
        m = m[:, max(0, cols[0] - 2):cols[-1] + 3]
        ms.append((m, cap, col, gap))
    base = capmax * 1.15 + 4
    H0 = int(base + capmax * 0.6)
    Wt = sum(m.shape[1] + int(g) for m, _, _, g in ms) + 10
    ink = np.zeros((H0, Wt), np.uint8)
    red = np.zeros_like(ink)
    x = 0
    for m, cap, col, gap in ms:
        x += int(gap)
        top = int(round(base - cap * 1.15))
        tgt = red if col == "red" else ink
        h, w = m.shape
        hh = min(h, H0 - top)
        np.maximum(tgt[top:top + hh, x:x + w], m[:hh], out=tgt[top:top + hh, x:x + w])
        x += w
    return ink, red, x


def caption_masks(text, cap, maxw, seed):
    """Wrap the caption; the first letter is a larger red initial. Returns list of (ink, red, width)."""
    i0, _ = initial_of(text)
    pre, ini, rest = text[:i0], text[i0], text[i0 + 1:]
    capI = int(cap * 1.45)
    lines = b1m2.wrap(rest.strip(), cap, maxw - cap * 1.6)
    out = []
    first_rest = lines[0] if lines else ""
    gap = cap * 0.42 if rest.startswith(" ") else cap * 0.04
    out.append(seg_mask([(pre, cap, "ink", 0), (ini, capI, "red", cap * 0.04 if pre else 0), (first_rest, cap, "ink", gap)], seed, capI))
    for j, l in enumerate(lines[1:]):
        out.append(seg_mask([(l, cap, "ink", cap * 0.1)], seed + 20 + j, capI))
    return out


def pin_slip(canvas, x, y, text, cap, maxw, seed, alpha=1.0):
    rows = caption_masks(text, cap, maxw, seed)
    lh = int(cap * 1.32)
    ww = max(r[2] for r in rows) + int(cap * 1.4)
    hh = lh * (len(rows) - 1) + rows[0][0].shape[0] + 4
    rnd = random.Random(seed)
    m = np.zeros(canvas.shape[:2], np.uint8)
    tear = [(x + ww - k, y + hh + rnd.uniform(-4, 3)) for k in range(0, ww, 14)]
    poly = [(x, y + rnd.uniform(0, 4)), (x + ww, y + rnd.uniform(0, 4))] + tear + [(x, y + hh - rnd.uniform(0, 4))]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in poly])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, m, off=4, blur=3, opacity=0.3)
    canvas[:] = canvas * (1 - m[..., None] / 255) + SLIPC * (m[..., None] / 255)
    yy = y + int(cap * 0.05)
    for ink, red, _ in rows:
        for mm, col in ((ink, INK), (red, RED)):
            sub = np.zeros(canvas.shape[:2], np.uint8)
            h, w = mm.shape
            xx = x + int(cap * 0.35)
            ys, ye = max(0, yy), min(canvas.shape[0], yy + h)
            xs, xe = max(0, xx), min(canvas.shape[1], xx + w)
            sub[ys:ye, xs:xe] = mm[ys - yy:ye - yy, xs - xx:xe - xx]
            penlib.ink_onto(canvas, sub, col)
        yy += lh
    K3.pin(canvas, x + ww - 16, y + 14, 6)
    return ww, hh


def board_slips(pg, x0, x1, y, caps, seed, cap=28, maxw=900):
    """Flow the board's slips left to right, wrapping to new rows."""
    x, rowh = x0 + 6, 0
    for i, t in enumerate(caps):
        rows = caption_masks(t, cap, maxw, seed + 10 * i)
        ww = max(r[2] for r in rows) + int(cap * 1.4)
        if x + ww > x1 and x > x0 + 6:
            x, y = x0 + 6, y + rowh + 12
            rowh = 0
        w_, h_ = pin_slip(pg, x, y + (i % 2) * 4, t, cap, maxw, seed + 10 * i)
        x += w_ + 16
        rowh = max(rowh, h_)
    return y + rowh


def build(upto=7):
    pg = pen99.sheet99()
    P = K3.load_puppets()
    bottoms = []
    for n in range(1, 8):
        if n == 7:
            x0, x1, y0, pw, ph = X0, X1, ROWY[3], BIG_W, BIG_H
        else:
            col, row = (n - 1) % 2, (n - 1) // 2
            (x0, x1), y0, pw, ph = COLX[col], ROWY[row], PW, PH
        letters_here = "".join(initial_of(c)[1] for b, c in CAPS if b == n)
        hdr = pen99.letter([f"board {n}    {letters_here[0]} - {letters_here[-1]}" if len(letters_here) > 1 else f"board {n}    {letters_here}"], 30, 2690 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        h, w = hdr.shape
        sub[y0:y0 + h, x0:x0 + w] = hdr
        penlib.ink_onto(pg, sub, GRAPH)
        py = y0 + 46
        pg[py:py + ph, x0:x0 + pw] = panel(n, P, pw, ph)
        bm = penlib.border_mask(pg.shape[:2], [(x0, py, x0 + pw, py + ph)], 7, 2700 + n)
        penlib.ink_onto(pg, bm)
        hole = np.zeros(pg.shape[:2], np.uint8)
        cv2.circle(hole, (x0 + 26, py + 26), 9, 255, -1, cv2.LINE_AA)
        penlib.ink_onto(pg, hole, hexc("#2a2622"))
        if n <= upto:
            caps = [c for b, c in CAPS if b == n]
            bt = board_slips(pg, x0, x0 + pw, py + ph + 14, caps, 2800 + 100 * n, maxw=(900 if n < 7 else 940))
            bottoms.append((n, bt))
    for n, bt in bottoms:
        lim = ROWY[min(3, n // 2 + (0 if n < 7 else 1))] - 12 if n < 7 else 2730
        if n < 7:
            lim = ROWY[(n - 1) // 2 + 1] - 8
        print("board", n, bt, lim)
    pg = np.clip(np.round(pg), 0, 255).astype(np.uint8)
    pen99.folio(pg, N, TITLE)
    return pg


if __name__ == "__main__":
    print(check())
    page = build(7)
    im = Image.fromarray(page)
    im.save(b1m2.MASTERS / f"{N:02d}-{PID}.png", optimize=True)
    jp = b1m2.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    im.save(jp, quality=90)
    print("jpeg bytes", jp.stat().st_size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [build(k) for k in range(0, 8)]
        b1m2.save_beats(N, frames)
