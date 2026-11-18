"""Page 97 Six words (reduction and expansion; medium: pen-hand).

Six panels, each captioned with a single word; no balloons. The six words are the whole text of the page outside
the folio margin: Errand. / Time? / Clock. / Thanks. / Key. / Why?  Everything else that page 51 lettered (the
memo text, TICKET OFFICE, the SERVICE card and tag) is drawn here as unlettered pen marks (the memo as pen
scribble lines, the cards and tag as blank ruled boxes) so that no seventh word appears.
Drawing: page 51's one-weight pen (p51_pen_alone.Pen, 4.42 px, hidden lines lifted) over page 05's HANDMADE figure
model (b1m2); the six caption words in the shared pen hand (pen99.letter) at cap 116. The LoC 1934 sheet as ground.
Run: python3 -I p97_six_words.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib  # noqa: E402
import p51_pen_alone as P  # noqa: E402

N, PID, TITLE = 97, "six-words", "Six words"
W, H = 2200, 2850
PEN = P.PEN
COLS = [(110, 1085), (1115, 2090)]
ROWS = [(110, 963), (993, 1846), (1876, 2729)]
PIC_H = 683                     # picture area; the word band below it
WORDS = ["Errand.", "Time?", "Clock.", "Thanks.", "Key.", "Why?"]
WCAP = 116
BOX = {}
for i in range(6):
    c, r = COLS[i % 2], ROWS[i // 2]
    BOX[i + 1] = (c[0], r[0], c[1], r[1])
PW = 975


def scribble_memo(p, x, y, w=150, h=112, seed=0):
    """the memo slip: a ruled box with four pen scribble lines (handwriting too small and quick to be words)"""
    rnd = np.random.default_rng(seed)
    p.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    for k, frac in enumerate((0.2, 0.42, 0.62, 0.82)):
        yy = y - h / 2 + h * frac
        L = w * (0.38 if k == 0 else rnd.uniform(0.6, 0.8))
        xs = np.linspace(x - w * 0.4, x - w * 0.4 + L, 26)
        ys = yy + 3.2 * np.sin(xs * 0.55 + rnd.uniform(0, 6)) + rnd.normal(0, 0.8, len(xs))
        p.line(list(zip(xs, ys)))


def blank_card(p, cx, cy, w=96, h=40):
    p.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    p.line([(cx - w * 0.3, cy), (cx + w * 0.3, cy)])        # a rule where the card's lettering would be


def key(p, cx, top, s=1.0):
    """page 51's key drawing (hook, bow, shank, bit) with its tag left blank"""
    p.line([(cx - 10 * s, top - 6 * s), (cx, top - 14 * s), (cx + 6 * s, top - 4 * s), (cx + 2 * s, top + 14 * s)])
    r1, r2 = 24 * s, 10 * s
    by = top + 14 * s + r1
    p.shape([(cx + r1 * math.cos(t), by + r1 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)])
    p.line([(cx + r2 * math.cos(t), by + r2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 30, endpoint=False)], closed=True)
    sy0, sy1 = by + r1, by + r1 + 108 * s
    p.shape([(cx - 6 * s, sy0 - 2 * s), (cx + 6 * s, sy0 - 2 * s), (cx + 6 * s, sy1), (cx - 6 * s, sy1)])
    p.shape([(cx + 6 * s, sy1 - 34 * s), (cx + 30 * s, sy1 - 34 * s), (cx + 30 * s, sy1 - 22 * s), (cx + 20 * s, sy1 - 22 * s),
             (cx + 20 * s, sy1 - 12 * s), (cx + 30 * s, sy1 - 12 * s), (cx + 30 * s, sy1), (cx + 6 * s, sy1)])
    tx, ty = cx + 52 * s, by + 56 * s
    p.line([(cx + r1 * 0.7, by + r1 * 0.7), (tx - 30 * s, ty - 10 * s)])
    p.rect(tx - 30 * s, ty - 16 * s, tx + 34 * s, ty + 16 * s)


def floor(p, fl):
    p.line([(0, fl), (PW, fl)])
    p.line([(0, fl - 180), (PW, fl - 180)])


FL = 630
SC = 0.5


def window(p, x0, y0, w, sill, stranger=None):
    if stranger:
        p.shapes(B.stranger(*stranger[0], **stranger[1]))
    ws, _ = B.window(x0, y0, w, FL - y0, sill=sill, header=56)
    p.shapes(ws)


def P1(st):          # E0 the errand: memo on the desk, he rises toward the cupboard far right
    p = P.Pen(PW, PIC_H, 9701)
    floor(p, FL)
    p.shapes(B.desk(70, 430, 390, FL))
    scribble_memo(p, 190, 384, seed=9702)
    p.shapes(B.agent(st.get("x", 560), FL, face=1, scale=SC, legs=(18, -16), sh=-30, el=30, lean=6, pencil_deg=200))
    cs, _ = B.cupboard(760, 240, 120, 330)
    p.shapes(cs)
    return p


def P2(st):          # E1 the question: she at the window, he stopped
    p = P.Pen(PW, PIC_H, 9711)
    floor(p, FL)
    window(p, 90, 170, 380, 500, ((280, 610), dict(face=1, scale=0.95)))
    p.shapes(B.agent(700, FL, face=-1, scale=SC, sh=6, el=16, tilt=4, pencil_deg=190))
    return p


def P3(st):          # E2 the answer: he looks up at the clock at 4:10
    p = P.Pen(PW, PIC_H, 9721)
    floor(p, FL)
    window(p, 60, 170, 300, 500, ((230, 610), dict(face=1, scale=0.95)))
    p.shapes(B.clock(560, 150, 70, 4, 10))
    p.shapes(B.agent(720, FL, face=-1, scale=SC, sh=6, el=16, tilt=-26, pencil_deg=190, lean=-4))
    return p


def P4(st):          # E3 the thanks: she turns away from the window and goes
    p = P.Pen(PW, PIC_H, 9731)
    floor(p, FL)
    window(p, 90, 170, 380, 500, ((st.get("sx", 60), 610), dict(face=-1, scale=0.95)))
    p.shapes(B.agent(700, FL, face=-1, scale=SC, sh=4, el=12, pencil_deg=190))
    return p


def P5(st):          # E4 the open cupboard: the key on its hook
    p = P.Pen(PW, PIC_H, 9741)
    floor(p, FL)
    cs, ins = B.cupboard(170, 160, 250, 420, open_deg=st.get("open", 72))
    p.shapes(cs)
    if ins:
        key(p, (ins[0] + ins[2]) / 2 + 6, ins[1] + 60, 1.1)
    p.shapes(B.service_door(770, 150, 130, FL - 150))
    blank_card(p, 835, 220)
    p.shapes(B.agent(600, FL, face=-1, scale=SC, sh=26, el=30, tilt=6, pencil_deg=190))
    return p


def P6(st):          # E5 the forgetting: pencil to chin; key unmoved; door shut
    p = P.Pen(PW, PIC_H, 9751)
    floor(p, FL)
    cs, ins = B.cupboard(110, 160, 250, 420, open_deg=72)
    p.shapes(cs)
    key(p, (ins[0] + ins[2]) / 2 + 6, ins[1] + 60, 1.1)
    p.shapes(B.service_door(770, 150, 130, FL - 150))
    blank_card(p, 835, 220)
    p.shapes(B.agent(560, FL - 8, face=-1, scale=0.52, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    return p


PANELS = {1: P1, 2: P2, 3: P3, 4: P4, 5: P5, 6: P6}


def frames_mask():
    p = P.Pen(W, H, 9790)
    for k, (x0, y0, x1, y1) in BOX.items():
        p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)
        p.line([(x0, y0 + PIC_H), (x1, y0 + PIC_H)])            # the caption band's rule
    return cv2.resize(p.m, (W, H), interpolation=cv2.INTER_AREA)


FR = [None]


def build(state=None, upto=6, words=6):
    state = state or {}
    pg = P.SHEET.copy()
    if FR[0] is None:
        FR[0] = frames_mask()
    ink = FR[0].copy()
    for k in range(1, upto + 1):
        x0, y0, x1, y1 = BOX[k]
        m = PANELS[k](state.get(k, {})).render()[:PIC_H, :x1 - x0]
        sub = ink[y0:y0 + PIC_H, x0:x1]
        np.maximum(sub, m, out=sub)
    for k in range(1, words + 1):
        x0, y0, x1, y1 = BOX[k]
        m = pen99.letter([WORDS[k - 1]], WCAP, 9760 + k, weight=0.105)
        B.put_mask(ink, m, (x0 + x1) / 2, y0 + PIC_H + (y1 - y0 - PIC_H) / 2 + 16)
    penlib.ink_onto(pg, ink, penlib.INK)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        from PIL import Image
        states = [({}, 0, 0), ({1: {"x": 470}}, 1, 0), ({}, 1, 1), ({}, 2, 2), ({}, 4, 4),
                  ({5: {"open": 0}}, 5, 4), ({}, 5, 5), ({}, 6, 5), ({}, 6, 6)]
        fr = [np.asarray(Image.fromarray(finish(build(s, u, w))).resize((960, 1242), Image.LANCZOS)) for s, u, w in states[1:]]
        print("beats", B.save_beats(N, fr))
