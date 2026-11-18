"""Page 51 Pen alone (medium and material; medium: pen-hand).

The whole page drawn in the shared pen hand alone: one line weight, no tone, no fill.
Eight panels after the base page's order (E0 x3, E1, E2, E3, E4, E5). Every mark on the page is one pen of one
width, PEN = 34 * 0.13 = 4.42 px, the very pen of the folio line: the lettering is pen99.letter with
weight = PEN / cap (so a 44 px balloon letter and the 34 px folio share one stroke width), and the drawing is
the same pen run along the outlines of page 05's HANDMADE figure model (b1m2.agent / stranger / desk / window /
clock / cupboard / service_door shapes), with hidden lines lifted (each nearer shape erases the lines behind it
before its own outline is drawn: paper, not fill). No tone, no hatching, no fill, no paper slips, no shadows:
the LoC 1934 sheet is the only ground.
Run: python3 -I p51_pen_alone.py [--page-only]
"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib  # noqa: E402

N, PID, TITLE = 51, "pen-alone", "Pen alone"
W, H = 2200, 2850
PEN = pen99.FOLIO_CAP * 0.13          # 4.42 px: the folio's pen
SS = 3                                 # supersampling of the drawing mask
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.4)
LCAP = 44                              # balloon lettering
PH = 845
COLS3 = [(110, 750), (780, 1420), (1450, 2090)]
COLS2 = [(110, 1085), (1115, 2090)]
ROWS = [(110, 955), (990, 1835), (1870, 2715)]
BOX = {1: (*COLS3[0], *ROWS[0]), 2: (*COLS3[1], *ROWS[0]), 3: (*COLS3[2], *ROWS[0]),
       4: (*COLS3[0], *ROWS[1]), 5: (*COLS3[1], *ROWS[1]), 6: (*COLS3[2], *ROWS[1]),
       7: (*COLS2[0], *ROWS[2]), 8: (*COLS2[1], *ROWS[2])}
BOX = {k: (v[0], v[2], v[1], v[3]) for k, v in BOX.items()}     # (x0, y0, x1, y1)
SKIP = {"pin", "glass_in"}


def letters(lines, cap, seed):
    return pen99.letter(lines, cap, seed, weight=PEN / cap)


class Pen:
    """A panel's drawing: one pen at SS x supersampling, hidden lines lifted by erasing under nearer shapes."""
    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.m = np.zeros((h * SS, w * SS), np.uint8)
        self.rnd = random.Random(seed)
        self.th = int(round(PEN * SS))
        self.text = []          # (mask, cx, cy) lettering laid after the drawing is downsampled

    def _trem(self, pts, closed):
        p = np.asarray(pts, float)
        if len(p) < 2:
            return p
        seg = np.r_[p, p[:1]] if closed else p
        out = [seg[0]]
        for a, b in zip(seg[:-1], seg[1:]):
            n = max(1, int(np.hypot(*(b - a)) / 6))
            for k in range(1, n + 1):
                out.append(a + (b - a) * k / n)
        out = np.array(out)
        ph = self.rnd.uniform(0, 6.28)
        d = np.gradient(out, axis=0)
        nr = np.c_[-d[:, 1], d[:, 0]] / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9)
        k = np.arange(len(out))
        off = 0.45 * np.sin(k * 0.13 + ph) + 0.25 * np.sin(k * 0.37 + 2 * ph)
        return out + nr * off[:, None]

    def line(self, pts, closed=False):
        q = self._trem(pts, closed)
        cv2.polylines(self.m, [np.int32(np.round(q * SS * 16))], False, 255, self.th, cv2.LINE_AA, shift=4)

    def erase(self, pts):
        cv2.fillPoly(self.m, [np.int32(np.round(np.asarray(pts, float) * SS * 16))], 0, cv2.LINE_AA, shift=4)

    def shape(self, pts, closed=True, erase=True):
        if erase and closed:
            self.erase(pts)
        self.line(pts, closed)

    def shapes(self, ss):
        """outline every shape with the one pen; a shape too thin to outline in one weight (a slit, a bar, a
        tick, the pencil) is drawn as its centre line, a tiny ring is opened to a ring the pen can draw"""
        for s in sorted(ss, key=lambda s: s.z):
            if s.role in SKIP:
                continue
            c = np.asarray(s.curve(), float)
            (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.float32(c))
            if min(rw, rh) < 3.2 * PEN and (max(rw, rh) > 2.5 * min(rw, rh) or len(s.pts) <= 4):
                a = math.radians(ang if rw >= rh else ang + 90)
                L = max(rw, rh) / 2
                d = np.array([math.cos(a), math.sin(a)])
                if not s.hole:
                    self.erase(c)
                self.line([(cx - d[0] * L, cy - d[1] * L), (cx + d[0] * L, cy + d[1] * L)])
                continue
            if max(rw, rh) < 4.4 * PEN:            # a small round: button, eyeglass, knob
                r = max(max(rw, rh) / 2, 1.9 * PEN)
                ring = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
                self.shape(ring, True, erase=not s.hole)
                continue
            self.shape(c, True, erase=not s.hole)

    def rect(self, x0, y0, x1, y1, erase=True):
        self.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True, erase)

    def word(self, lines, cap, cx, cy, seed, box=False, pad=(18, 10)):
        m = letters(lines, cap, seed)
        if box:
            hw, hh = m.shape[1] / 2 - cap * 0.45 + pad[0], m.shape[0] / 2 - cap * 0.35 + pad[1]
            self.rect(cx - hw, cy - hh, cx + hw, cy + hh)
        self.text.append((m, cx, cy))
        return m

    def balloon(self, lines, cx, cy, tip, seed, cap=LCAP):
        m = letters(lines, cap, seed)
        rx, ry = m.shape[1] / 2 * 1.10 + 8, m.shape[0] / 2 * 1.12 + 4
        u = np.zeros_like(self.m)
        cv2.ellipse(u, (int(cx * SS), int(cy * SS)), (int(rx * SS), int(ry * SS)), 0, 0, 360, 255, -1)
        ang = math.atan2(tip[1] - cy, tip[0] - cx)
        bw = 0.22
        base = [(cx + rx * 0.8 * math.cos(ang + s * bw), cy + ry * 0.8 * math.sin(ang + s * bw)) for s in (-1, 1)]
        tri = np.array([base[0], tip, base[1]], float)
        cv2.fillPoly(u, [np.int32(tri * SS)], 255)
        cs, _ = cv2.findContours(u, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=len)[:, 0, :].astype(float) / SS
        c = c[::3]
        self.m[u > 0] = 0
        self.line(c, closed=True)
        self.text.append((m, cx, cy - cap * 0.05))

    def render(self):
        out = cv2.resize(self.m, (self.w, self.h), interpolation=cv2.INTER_AREA)
        for m, cx, cy in self.text:
            B.put_mask(out, m, cx, cy)
        return out


# ------------------------------------------------------------------ pen-drawn props
def floor(p, w, fl):
    p.line([(0, fl), (w, fl)])
    p.line([(0, fl - 230), (w, fl - 230)])          # the wainscot rail


def memo(p, x, y, seed):
    p.word(["MEMO", "4:15 - open", "SERVICE door.", "Key in cupboard."], 25, x, y, seed, box=True, pad=(14, 10))


def key(p, cx, top, s=1.0):
    """the brass key on its hook, in outline: hook, bow (ring and eye), shank, bit; its SERVICE tag on a string"""
    p.line([(cx - 10 * s, top - 6 * s), (cx, top - 14 * s), (cx + 6 * s, top - 4 * s), (cx + 2 * s, top + 14 * s)])
    r1, r2 = 24 * s, 10 * s
    by = top + 14 * s + r1
    ring = [(cx + r1 * math.cos(t), by + r1 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    p.shape(ring)
    p.line([(cx + r2 * math.cos(t), by + r2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 30, endpoint=False)], closed=True)
    sy0, sy1 = by + r1, by + r1 + 108 * s
    p.shape([(cx - 6 * s, sy0 - 2 * s), (cx + 6 * s, sy0 - 2 * s), (cx + 6 * s, sy1), (cx - 6 * s, sy1)])
    p.shape([(cx + 6 * s, sy1 - 34 * s), (cx + 30 * s, sy1 - 34 * s), (cx + 30 * s, sy1 - 22 * s), (cx + 20 * s, sy1 - 22 * s),
             (cx + 20 * s, sy1 - 12 * s), (cx + 30 * s, sy1 - 12 * s), (cx + 30 * s, sy1), (cx + 6 * s, sy1)])
    # tag on a string from the bow
    tx, ty = cx + 52 * s, by + 56 * s
    p.line([(cx + r1 * 0.7, by + r1 * 0.7), (tx - 34 * s, ty - 12 * s)])
    p.word(["SERVICE"], int(20 * s), tx + 10 * s, ty, 5199, box=True, pad=(9, 6))


def service_card(p, cx, cy, seed):
    p.word(["SERVICE"], 30, cx, cy, seed, box=True, pad=(14, 8))


def window_with(p, wx0, wy0, ww, wh, sill, stranger_args=None, seed=0):
    if stranger_args:
        p.shapes(B.stranger(*stranger_args[0], **stranger_args[1]))
    ws, _ = B.window(wx0, wy0, ww, wh, sill=sill, header=72)
    p.shapes(ws)
    p.word(["TICKET OFFICE"], 30, wx0 + ww / 2, wy0 + 38, seed)


# ------------------------------------------------------------------ panels (local px; w x PH)
def P1(st):
    w = 640
    p = Pen(w, PH, 5101)
    fl = 770
    floor(p, w, fl)
    p.shapes(B.agent(360, fl + 40, face=1, scale=0.62, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10))
    p.shapes(B.desk(110, 540, 470, fl))
    memo(p, 240, 486, 5102)
    return p


def P2(st):
    w = 640
    p = Pen(w, PH, 5111)
    fl = 770
    floor(p, w, fl)
    p.shapes(B.desk(-260, 540, 420, fl))
    memo(p, 60, 486, 5112)
    dx = st.get("dx", 0)
    p.shapes(B.agent(330 + dx, fl, face=1, scale=0.62, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200))
    return p


def P3(st):
    w = 640
    p = Pen(w, PH, 5121)
    fl = 770
    floor(p, w, fl)
    cs, _ = B.cupboard(300, 300, 150, 430)
    p.shapes(cs)
    p.shapes(B.service_door(500, 210, 120, fl - 210))
    service_card(p, 560, 300, 5122)
    p.shapes(B.agent(170, fl, face=1, scale=0.62, legs=(-20, 22), sh=20, el=10, lean=4, pencil_deg=200))
    return p


def P4(st):
    w = 640
    p = Pen(w, PH, 5131)
    fl = 770
    floor(p, w, fl)
    window_with(p, 50, 240, 330, fl - 240, 620, (((215, 740), dict(face=1, scale=1.15))), 5132)
    p.shapes(B.agent(510, fl, face=-1, scale=0.62, sh=6, el=16, tilt=4, pencil_deg=190))
    p.balloon(["Pardon me —", "have you the", "right time?"], 250, 118, (368, 236), 5133)
    return p


def P5(st):
    w = 640
    p = Pen(w, PH, 5141)
    fl = 770
    floor(p, w, fl)
    p.shapes(B.clock(150, 250, 86, 4, 10))
    p.shapes(B.agent(420, fl, face=-1, scale=0.62, sh=6, el=16, tilt=-24, pencil_deg=190, lean=-4))
    p.balloon(["Ten past four,", "by the clock."], 400, 100, (392, 220), 5142)
    return p


def P6(st):
    w = 640
    p = Pen(w, PH, 5151)
    fl = 770
    floor(p, w, fl)
    window_with(p, 50, 240, 330, fl - 240, 620, (((90, 740), dict(face=-1, scale=1.15))), 5152)
    p.shapes(B.agent(510, fl, face=-1, scale=0.62, sh=4, el=12, pencil_deg=190))
    p.balloon(["Much", "obliged!"], 250, 110, (66, 236), 5153, cap=50)
    return p


def P7(st):
    w = 975
    p = Pen(w, PH, 5161)
    fl = 770
    floor(p, w, fl)
    deg = st.get("open", 72)
    cs, ins = B.cupboard(250, 220, 260, 500, open_deg=deg)
    p.shapes(cs)
    if ins:
        key(p, (ins[0] + ins[2]) / 2 + 10, ins[1] + 70, 1.2)
    p.shapes(B.service_door(800, 210, 130, fl - 210))
    service_card(p, 865, 300, 5162)
    p.shapes(B.agent(650, fl, face=-1, scale=0.62, sh=26, el=30, tilt=6, pencil_deg=190))
    return p


def P8(st):
    w = 975
    p = Pen(w, PH, 5171)
    fl = 770
    floor(p, w, fl)
    cs, ins = B.cupboard(130, 220, 260, 500, open_deg=72)
    p.shapes(cs)
    key(p, (ins[0] + ins[2]) / 2 + 10, ins[1] + 70, 1.2)
    p.shapes(B.service_door(800, 210, 130, fl - 210))
    service_card(p, 865, 300, 5172)
    p.shapes(B.agent(600, 760, face=-1, scale=0.64, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    if st.get("line", True):
        p.balloon(["Well, here I am...", "and what for?"], 560, 110, (575, 300), 5173)
    return p


PANELS = {1: P1, 2: P2, 3: P3, 4: P4, 5: P5, 6: P6, 7: P7, 8: P8}


def frames_mask(ks):
    p = Pen(W, H, 5190)
    for k in ks:
        x0, y0, x1, y1 = BOX[k]
        p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)
    return cv2.resize(p.m, (W, H), interpolation=cv2.INTER_AREA)


FRAMES = None


def build(state=None, upto=8):
    global FRAMES
    state = state or {}
    pg = SHEET.copy()
    ink = np.zeros((H, W), np.uint8)
    if FRAMES is None:
        FRAMES = frames_mask(range(1, 9))
    ink = np.maximum(ink, FRAMES)
    for k in range(1, upto + 1):
        x0, y0, x1, y1 = BOX[k]
        m = PANELS[k](state.get(k, {})).render()
        m = m[:y1 - y0, :x1 - x0]
        sub = ink[y0:y1, x0:x1]
        np.maximum(sub, m, out=sub)
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
        # the page is drawn as it would be by one pen: frames, then the panels in reading order, the last line last
        states = [({}, 0), ({}, 2), ({}, 4), ({}, 6), ({7: {"open": 0}}, 7), ({}, 7), ({8: {"line": False}}, 8), ({}, 8)]
        B.save_beats(N, [np.asarray(Image.fromarray(finish(build(s, u))).resize((960, 1242), Image.LANCZOS)) for s, u in states])
        print("beats", len(states))
