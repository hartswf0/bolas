"""99 ways, page 22 "Ballad" (voice and language; medium: stencil-dye).
Eight panels, each carrying one rhymed couplet in the shared pen hand: a ballad of eight couplets. The four lines
are kept word for word and set inside the couplets (two of them are whole second lines: 'Pardon me - have you the
right time?' rhymes with 'chime', 'Ten past four, by the clock.' with 'stock'). Each couplet's rhyme words are
lettered in madder so the rhyme can be seen.
Pictures printed as HANDMADE stencils in flat dyes (the page 08 stencil-dye method: each colour its own cut stencil
with paper ties, slight misregistration, dye pooling at the edges), figures and set pieces from the b1m2 cut model,
the key from the ANRC 1922 cutout used as a stencil.
Run: python3 -I p22_ballad.py"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p08_lipogram as S  # noqa: E402  (stencil-dye kit: print_panel, layers_for, dye, key_stencil, colours)
from b1m2 import *  # noqa: E402,F401

N, PID, TITLE = 22, "ballad", "Ballad"
GW, GH = 970, 620
COLS = (110, 1120)
ROWS = (110, 780, 1450, 2120)          # 4 rows of 620, gaps 50; last ends 2740 -> clamp to 2730
GH_LAST = 2730 - 2120
BOXES = [(COLS[c], ROWS[r], COLS[c] + GW, ROWS[r] + (GH if r < 3 else GH_LAST)) for r in range(4) for c in range(2)]

COUPLETS = [
    ("His memo said, as plain could be:", "'Four-fifteen, SERVICE door - with key.'"),
    ("So up he got from desk and chair", "to fetch the key from cupboard there."),
    ("A lady tapped the glass - a chime:", "'Pardon me - have you the right time?'"),
    ("He looked up at the wall, took stock:", "'Ten past four, by the clock.'"),
    ("'Much obliged!' she said with grace,", "and left the window, left the place."),
    ("He reached the cupboard, swung it wide:", "the brass key hung, tagged SERVICE, inside."),
    ("He stood before the cupboard door:", "'Well, here I am... and what for?'"),
    ("The brass key on its hook would stay;", "the SERVICE door stayed shut that day."),
]
CAP = 40
MADDER = S.MADDER


def last_word_split(line):
    i = line.rstrip().rfind(" ")
    return line[:i], line[i + 1:]


def ink_cols(m):
    cols = np.nonzero(m.max(axis=0) > 60)[0]
    return (cols.min(), cols.max()) if len(cols) else (0, m.shape[1])


def couplet(c, lines, seed, x=24, y=16):
    """Letter the two lines left-aligned; the rhyme word of each in madder. Returns bottom y."""
    if not S.STAGE["text"]:
        return y
    lh = int(CAP * 1.42)
    for k, line in enumerate(lines):
        pre, word = last_word_split(pen99.clean(line))
        mp = pen99.letter([pre], CAP, seed + 10 * k)
        mw = pen99.letter([word], CAP, seed + 10 * k + 5)
        p0, p1 = ink_cols(mp)
        w0, _ = ink_cols(mw)
        space = penlib.GLYPHS[" "][0] * CAP + CAP * 0.1
        ink = np.zeros(c.shape[:2], np.uint8)
        blit_mask(ink, mp[:, p0:], x, y + k * lh)
        red = np.zeros(c.shape[:2], np.uint8)
        blit_mask(red, mw[:, w0:], int(x + (p1 - p0) + space), y + k * lh)
        comp(c, ink, INK)
        comp(c, red, MADDER * 0.92)
    return y + 2 * lh + 8


def finish(c):
    c *= S.SHEET[:c.shape[0], :c.shape[1]].mean(axis=2, keepdims=True) / S.SHEET.mean()
    return c


def window_set(seed, stranger_kw, agent_kw, h):
    floor = h - 60
    ws, sill = window(80, 170, 330, h - 90 - 170, sill=floor - 110, header=62)
    for s_ in ws:
        s_.role = "window"
    fig = list(ws)
    fig += stranger(245 + stranger_kw.pop("dx", 0), sill + 4, scale=0.78, **stranger_kw)
    fig += agent(**agent_kw)
    lay = S.layers_for(fig, GW, h, wall_floor=floor)
    c = finish(S.print_panel(GW, h, lay, seed))
    if S.STAGE["text"]:
        lm = np.zeros((h, GW), np.uint8)
        l = letter(["TICKET OFFICE"], 30, seed + 5, weight=0.17)
        s_ = min(1.0, 320 / l.shape[1])
        l = cv2.resize(l, (int(l.shape[1] * s_), int(l.shape[0] * s_)), interpolation=cv2.INTER_AREA)
        put_mask(lm, l, 245, 170 + 33)
        comp(c, lm, np.array([246, 240, 222], np.float32))
    return c


def P1(h):
    floor = h - 60
    fig = agent(560, floor + 6, face=-1, scale=0.44, legs=(4, -4), sh=-6, el=50, pencil_deg=190, tilt=14)
    fig += desk(180, floor - 170, 330, floor)
    c = finish(S.print_panel(GW, h, S.layers_for(fig, GW, h, wall_floor=floor), 2201))
    if S.STAGE["text"]:
        slip(c, 250, floor - 250, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 26, 2202,
             paper=np.array([248, 244, 230], np.float32), tilt=-4, shadow=0.35)
    return c


def P2(h):
    floor = h - 60
    fig = desk(60, floor - 170, 260, floor)
    fig += agent(470, floor + 6, face=1, scale=0.44, legs=(22, -20), sh=-22, el=24, pencil_deg=200, lean=4)
    cup, _ = cupboard(760, floor - 300, 150, 300)
    fig += cup
    return finish(S.print_panel(GW, h, S.layers_for(fig, GW, h, wall_floor=floor), 2211))


def P3(h):
    return window_set(2221, {"glove": True}, dict(x=720, floor=h + 40, face=-1, scale=0.50, sh=8, el=20, tilt=-3,
                                                  pencil_deg=190), h)


def P4(h):
    floor = h - 60
    fig = clock(330, 300, 92, hh=4, mm=10, swing=8)
    fig += agent(660, floor + 6, face=-1, scale=0.46, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
    return finish(S.print_panel(GW, h, S.layers_for(fig, GW, h, wall_floor=floor), 2231))


def P5(h):
    return window_set(2241, {"dx": -50, "face": -1, "tilt": -4}, dict(x=760, floor=h + 40, face=1, scale=0.50, sh=-14,
                                                                     el=20, legs=(18, -16), pencil_deg=200), h)


def cupboard_set(seed, agent_kw, h, sdoor=True, with_agent=True, big_key=False):
    floor = h - 60
    c0, c1, cw, ch = 330, floor - 330, 230, 330
    cup, ins = cupboard(c0, c1, cw, ch, open_deg=112)
    fig = list(cup)
    if sdoor:
        fig += service_door(680, floor - 360, 180, 360)
    if with_agent:
        fig += agent(**agent_kw)
    lay = S.layers_for(fig, GW, h, wall_floor=floor)
    # the key hangs on its hook on the inside of the open door leaf (as on page 01)
    ex = c0 + cw * math.cos(math.radians(112))
    kx, ky = (c0 + ex) / 2 + 2, c1 + 110
    ks = 0.26 if not big_key else 0.30
    lay.append(("ochre", S.key_stencil(GW, h, kx, ky, ks)))
    c = finish(S.print_panel(GW, h, lay, seed))
    if not S.STAGE["text"]:
        return c
    hk = np.zeros((h, GW), np.uint8)
    penlib.brush_line(hk, [(kx - 20, ky - 96), (kx + 3, ky - 96), (kx + 3, ky - 82)], 6, seed + 3)
    comp(c, hk, S.UMBER)
    slip(c, int(kx + 6), int(ky + 30), ["SERVICE"], 18, seed + 4, paper=np.array([248, 244, 230], np.float32),
         pad=(10, 3), tilt=8, shadow=0.3)
    if sdoor:
        slip(c, 712, floor - 320, ["SERVICE"], 28, seed + 5, paper=np.array([248, 244, 230], np.float32), pad=(14, 5), shadow=0.3)
    return c


def P6(h):
    return cupboard_set(2261, dict(x=190, floor=h - 54, face=1, scale=0.44, legs=(14, -12), sh=60, el=20, pencil_deg=200), h,
                        sdoor=True)


def P7(h):
    return cupboard_set(2271, dict(x=170, floor=h - 54, face=1, scale=0.44, legs=(3, -3), sh=50, el=120, wr=8,
                                   pencil_deg=40, tilt=6), h, sdoor=True)


def P8(h):
    return cupboard_set(2281, None, h, sdoor=True, with_agent=False)


PANELS = [P1, P2, P3, P4, P5, P6, P7, P8]


def build(n=8, state=None):
    state = state or {}
    page = S.SHEET.copy()
    for i, (fn, box) in enumerate(zip(PANELS, BOXES)):
        if i >= n:
            break
        x0, y0, x1, y1 = box
        h = y1 - y0
        S.STAGE["dyes"] = state.get("dyes") if i == n - 1 else None
        S.STAGE["text"] = state.get("pics_text", True) if i == n - 1 else True
        c = fn(h)
        S.STAGE["dyes"], S.STAGE["text"] = None, True
        if not (i == n - 1 and state.get("no_couplet")):
            # the couplet on a pale paper strip pasted across the top of the panel
            pm = np.zeros(c.shape[:2], np.uint8)
            lw = max(pen99.letter([pen99.clean(l)], CAP, 1).shape[1] for l in COUPLETS[i]) + 20
            cv2.fillPoly(pm, [np.int32(np.array([(10, 8), (min(GW - 12, lw + 30), 6), (min(GW - 12, lw + 28), 150),
                                                 (12, 152)]) * 4)], 255, cv2.LINE_AA, shift=2)
            penlib.shadow_onto(c, pm, off=4, blur=3, opacity=0.3)
            comp(c, pm, np.array([246, 241, 226], np.float32))
            couplet(c, COUPLETS[i], 2290 + 20 * i, x=26, y=18)
        page[y0:y1, x0:x1] = c
    frame_border(page, BOXES[:n], w=10, seed=2299)
    return page


def check():
    """each caption two lines whose last words rhyme (by ending letters, checked by hand list)."""
    rhymes = [("be", "key"), ("chair", "there"), ("chime", "time"), ("stock", "clock"), ("grace", "place"),
              ("wide", "inside"), ("door", "for"), ("stay", "day")]
    for (a, b), (r1, r2) in zip(COUPLETS, rhymes):
        w1 = last_word_split(a)[1].strip("'.,:;!?-").lower()
        w2 = last_word_split(b)[1].strip("'.,:;!?-").lower()
        assert (w1, w2) == (r1, r2), (w1, w2)
    return rhymes


if __name__ == "__main__":
    check()
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        # the last panel printed dye by dye, then its couplet lettered; earlier panels arrive whole
        for st in ([1, {}], [3, {}], [5, {}], [7, {}],
                   [8, {"dyes": {"wash"}, "pics_text": False, "no_couplet": True}],
                   [8, {"dyes": {"wash", "ochre", "verdi"}, "pics_text": False, "no_couplet": True}],
                   [8, {"no_couplet": True}], [8, {}]):
            p = np.clip(np.round(build(*st)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(p)
        save_beats(N, frames)
