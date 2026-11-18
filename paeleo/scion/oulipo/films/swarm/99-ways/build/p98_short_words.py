"""Page 98 Short words (formal / Oulipian rule; medium: daumier-collage).

Every word on the page has one syllable. Six collage panels under a masthead slip, laid out as page 67 (Inner voice)
but with its thought clouds gone and every text rewritten in words of one beat:
  the four lines:  "Say -- have you the right time?" / "Ten past four, by the clock." (already all one-syllable) /
                   "Thanks so much!" / "Well, here I am... and what for?" (already all one-syllable)
  the signs:       TICKET OFFICE -> FARES, SERVICE -> STAFF (door card and key tag), MEMO -> NOTE; the memo's time
                   (4:15 would be read 'four fif-teen') is given as a small drawn clock face at a quarter past four.
Reuses page 12/50/67's Daumier collage kit (build/daumier12.py, p12_loop.py, p50_brief_meeting.py): FORAGED CC0
lithographs by Honore Daumier (Rijksmuseum via Commons) cut by hand-placed scissor polygons, set pieces cut from the
prints' own crayon tone, the ANRC 1922 key cutout; LoC 1934 sheet ground; pen-hand lettering (pen99).
The Daumier door piece carries the printed word CONCIERGE: it is pasted over with a lintel board cut from the prints'
tone before the STAFF card goes on, so no printed word shows.
Run: python3 -I p98_short_words.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import b1m2
import daumier12 as D
import p12_loop as L
import p50_brief_meeting as B

N, PID, TITLE = 98, "short-words", "Short words"
SHEET = B.SHEET
PAPER = B.PAPER
BCAP, CAP = 42, 30
B.CAP = CAP

BOX = {"P1": (110, 330, 1035, 1030), "P2": (1075, 330, 2090, 1030),
       "P3": (110, 1070, 900, 1770), "P4": (940, 1070, 2090, 1770),
       "P5": (110, 1810, 960, 2730), "P6": (1000, 1810, 2090, 2730)}
ORDER = ["P1", "P2", "P3", "P4", "P5", "P6"]

OLD = {"signs": False}        # beat frames only: the long-word signs before they are pasted over
SIGNS = {"TICKET OFFICE": "FARES", "SERVICE": "STAFF"}
_slip = b1m2.slip


def slip98(c, x0, y0, lines, cap, seed, **kw):
    if not OLD["signs"]:
        lines = [SIGNS.get(l, l) for l in lines]
    return _slip(c, x0, y0, lines, cap, seed, **kw)


L.slip = slip98
B.slip = slip98


def full_door(c, x0, top, x1, floor):
    """page 50's full-height door; its printed CONCIERGE lettering pasted over with a lintel board (tone of the
    prints) and the STAFF card laid on that"""
    k = (x1 - x0) / L.DOOR["gray"].shape[1]
    uh = L.DOOR["gray"].shape[0] * k
    box = B.full_door(c, x0, top, x1, floor)
    if not OLD["signs"]:
        L.set_piece(c, "mid", [(x0 - 8, top - 6), (x1 + 8, top - 6), (x1 + 8, top + uh * 0.37), (x0 - 8, top + uh * 0.37)],
                    rim=3, shade=0.92)
        _slip(c, int(x0 + (x1 - x0) / 2 - 52), int(top + uh * 0.06), ["STAFF"], 32, 9861,
              paper=np.array([246, 242, 230], np.float32), pad=(14, 5), shadow=0.4)
    return box


def small_clock(c, cx, cy, r, hh=4, mm=15, seed=0):
    """a pen clock face drawn on the note: ring, four ticks, the hands at a quarter past four"""
    m = np.zeros(c.shape[:2], np.uint8)
    ring = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)]
    penlib.brush_line(m, ring, 3.2, seed)
    for k in range(4):
        a = math.radians(k * 90)
        penlib.brush_line(m, [(cx + r * 0.70 * math.sin(a), cy - r * 0.70 * math.cos(a)),
                              (cx + r * 0.92 * math.sin(a), cy - r * 0.92 * math.cos(a))], 2.6, seed + 1 + k)
    am, ah = math.radians(mm * 6), math.radians((hh % 12) * 30 + mm * 0.5)
    penlib.brush_line(m, [(cx, cy), (cx + r * 0.48 * math.sin(ah), cy - r * 0.48 * math.cos(ah))], 4.0, seed + 7)
    penlib.brush_line(m, [(cx, cy), (cx + r * 0.78 * math.sin(am), cy - r * 0.78 * math.cos(am))], 3.0, seed + 8)
    comp(c, m, INK)


def note_slip(c, x, y, cap=28, tilt=0, seed=9811):
    """the memo, in short words: NOTE / STAFF door at (a drawn clock at 4:15) / Key in the case."""
    if OLD["signs"]:
        return L.memo_slip(c, x, y, cap=cap - 6, tilt=-4, seed=seed)
    lines = ["NOTE", "STAFF door at", "Key in the case."]
    bx = _slip(c, x, y, lines, cap, seed, paper=np.array([246, 242, 230], np.float32), shadow=0.45, min_w=int(cap * 10.2))
    lh = int(cap * 1.42)
    wl = letter(["STAFF door at"], cap, seed + 1).shape[1] - cap * 1.2
    cy = y + 16 - cap * 0.15 + lh + cap * 0.62
    cx = x + 22 - cap * 0.5 + cap * 0.6 + wl + cap * 1.0
    small_clock(c, cx + cap * 0.25, cy - 2, cap * 0.86, seed=seed + 20)
    return bx


def strike_balloon(c, lines, cap, at, seed):
    """the long-word line struck through in pen (beat frames only)"""
    m0 = letter(lines, cap, seed)
    h, w = m0.shape
    sm = np.zeros(c.shape[:2], np.uint8)
    n = len(lines)
    for i in range(n):
        yy = at[1] - h / 2 + (i + 0.55) * h / n
        penlib.brush_line(sm, [(at[0] - w * 0.36, yy + 4), (at[0] + w * 0.36, yy - 3)], 5, seed + 30 + i)
    comp(c, sm, INK)


def say(c, st, new, old, cap, at, tip, seed, tail_w=0.22):
    """a balloon in short words; in the beat frames it may first carry the canon line, then the line struck"""
    stage = st.get("line", "new")
    if stage == "new":
        balloon(c, new, cap, at, tip, seed, tail_w=tail_w)
    else:
        balloon(c, old, cap, at, tip, seed, tail_w=tail_w)
        if stage == "struck":
            strike_balloon(c, old, cap, at, seed)


# ------------------------------------------------------------------ panels
def P1(st):
    """E0: at the desk, the note; he gets up"""
    w, h = 925, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    ch = penlib.about((150, fl + 4), penlib.R(-6))
    for poly in [[(120, 360), (146, 360), (146, fl + 4), (120, fl + 4)], [(120, 470), (262, 470), (262, 490), (120, 490)],
                 [(240, 490), (258, 490), (258, fl + 4), (240, fl + 4)]]:
        L.set_piece(c, "mid", [tuple(penlib.apply(ch, q)) for q in poly], rim=3, shade=0.78)
    top = 450
    foot = (330, fl + 66)
    d, sh, el = B.solve_to(foot, 1, 0.40, 10, (478, top + 4))
    B.agent2(c, foot=foot, face=1, scale=0.40, head_deg=14, body_deg=10, sh=sh, el=el)
    L.desk(c, 470, top, 400, fl + 8)
    note_slip(c, 560, 300)
    B.cap_at(c, "He reads the note on his desk: at the time drawn there, the STAFF door must be thrown wide, and "
                "the key hangs in the case. Up he gets.", 520, 9813, corner="tl", inset=14)
    return c


def P2(st):
    """E1: on his way, the question at the glass"""
    w, h = 1015, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    B.window(c, 200, 420, 0.60, fl, woman=(-10, -1, 0.50))
    L.agent(c, (860, fl + 66), face=-1, scale=0.40, head_deg=-6)
    say(c, st, ["Say — have you", "the right time?"], ["Pardon me —", "have you the", "right time?"], BCAP, (560, 400),
        (300, 450), 9822)
    B.cap_at(c, "On his way to the case, a voice at the glass:", 360, 9821, corner="tr", inset=14)
    return c


def P3(st):
    """E2: the clock at 4:10; the answer"""
    w, h = 790, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    L.clock(c, 140, 300, 84)
    _, Mh = L.agent(c, (600, fl + 66), face=-1, scale=0.40, head_deg=28)
    mp = L.at_src(Mh, L.HEAD, (786, 642))
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (400, 430), (mp[0] - 6, mp[1] + 2), 9832, tail_w=0.22)
    B.cap_at(c, "He looks up at the clock.", 330, 9831, corner="tl", inset=14)
    return c


def P4(st):
    """E3: the thanks; she goes"""
    w, h = 1150, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    B.window(c, 230, 470, 0.60, fl, woman=(-150, 1, 0.50))
    L.agent(c, (960, fl + 66), face=-1, scale=0.40, head_deg=-4)
    say(c, st, ["Thanks", "so much!"], ["Much", "obliged!"], 46, (470, 470), (150, 400), 9841, tail_w=0.24)
    B.cap_at(c, "She nods and goes. That is that.", 330, 9842, corner="br", inset=14)
    return c


def P5(st):
    """E4: the case swung wide, the key in plain view"""
    w, h = 850, 920
    c, fl = B.ground(w, h, fl_frac=0.86)
    L.PH = fl / 0.80
    L.cupboard(c, 200, 330, 190, 300, open_=st.get("open", True))
    full_door(c, 430, 318, 574, fl + 4)
    L.agent(c, (720, fl + 70), face=-1, scale=0.46, head_deg=4)
    B.cap_at(c, "Now to the case. He swings it wide: there hangs the key, in plain view.", 420, 9852, corner="tl", inset=14)
    return c


def P6(st):
    """E5: the forgetting; key on its hook, STAFF door shut"""
    w, h = 1090, 920
    c, fl = B.ground(w, h, fl_frac=0.86)
    L.cupboard(c, 150, 330, 190, 300, open_=True)
    full_door(c, 380, 318, 524, fl + 4)
    d, sh, el = B.solve_chin(0.48, -4, target_off=(-44, 78))
    r = B.agent2(c, foot=(700, fl + 70), face=-1, scale=0.48, head_deg=-4, sh=sh, el=el, pencil=True)
    if st.get("line", True):
        balloon(c, ["Well, here I am...", "and what for?"], BCAP, (520, 220), (r["mouth"][0] - 8, r["mouth"][1] - 4), 9862,
                tail_w=0.22)
    B.cap_at(c, "The key stays on its hook. The STAFF door stays shut.", 420, 9863, corner="br", inset=14)
    return c


PANELS = {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5, "P6": P6}


def masthead(pg):
    slip(pg, 420, 116, ["SHORT WORDS"], 88, 9890, paper=PAPER, align="centre", min_w=1360, pad=(40, 16), shadow=0.4,
         weight=0.12)
    sub = np.zeros(pg.shape[:2], np.uint8)
    put_mask(sub, letter(["a tale told in words of one beat"], 34, 9891), 1100, 288)
    comp(pg, sub, INK)


def build(state=None, upto=6):
    state = state or {}
    pg = SHEET.copy()
    masthead(pg)
    rects = []
    for i, k in enumerate(ORDER):
        if i >= upto:
            break
        x0, y0, x1, y1 = BOX[k]
        pg[y0:y1, x0:x1] = PANELS[k](state.get(k, {}))
        rects.append(BOX[k])
    frame_border(pg, rects, w=11, seed=9896)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        from PIL import Image
        old = {"P2": {"line": "old"}, "P4": {"line": "old"}}
        seq = [(True, old), (False, old),
               (False, {"P2": {"line": "struck"}, "P4": {"line": "old"}}),
               (False, {"P4": {"line": "old"}}),
               (False, {"P4": {"line": "struck"}}),
               (False, {})]
        seq = [(True, old)] + [(True, {"P2": {"line": "struck"}, "P4": {"line": "old"}}),
                               (True, {"P4": {"line": "old"}}), (True, {"P4": {"line": "struck"}}), (True, {}),
                               (False, {})]
        frames = []
        for signs_old, s in seq:
            OLD["signs"] = signs_old
            frames.append(np.asarray(Image.fromarray(finish(build(s))).resize((960, 1242), Image.LANCZOS)))
        OLD["signs"] = False
        save_beats(N, frames)
        print("beats", len(frames))
