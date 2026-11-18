"""99 ways, page 62 "Prisoner's text" (formal / Oulipian rule; medium: pen-hand).

Every letter outside the folio line is one of the thirteen lowercase letters with neither ascender nor
descender: a c e m n o r s u v w x z. No capitals (all reach cap height), no digits (likewise), no i or j
(their dots rise above the x-height). The four lines, the captions, the memo, the door card and the key's tag
are rewritten in those letters; what the letters cannot spell (the times, the key) is DRAWN with the same pen
as small inline pictures (a clock face at 4:15 or 4:10, a key). Punctuation (. , : - — ... ? !) is kept: it is
not letters. Substitutions: SERVICE -> 'annex' (door card and tag), open -> 'uncover', cupboard -> 'case',
hook -> 'screw', TICKET OFFICE board left blank.
Drawing: page 51's one-pen kit (p51_pen_alone.Pen: the folio's pen, 4.42 px, hidden lines lifted) on the LoC 1934
sheet, the b1m2 figure model. Run: python3 -I p62_prisoner.py"""
import math
import re
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib  # noqa: E402
import p51_pen_alone as P  # noqa: E402

N, PID, TITLE = 62, "prisoner", "Prisoner's text"
W, H = 2200, 2850
PEN = P.PEN
ALLOWED = set("acemnorsuvwxz")
PUNCT = set(" .,:-—?!")
TOKEN = re.compile(r"\{(key|c415|c410)\}")

TEXT = {
    "head": "a c e m n o r s u v w x z",
    "c1": ["our man sees a memo:"],
    "memo": ["memo", "{c415} — uncover annex.", "{key} : case."],
    "c2": ["so, across a room — on, on..."],
    "c3": ["now a woman, over a screen,", "summons our man:"],
    "q": ["excuse me —", "can one", "measure now?"],
    "c4": ["our man scans a {c410}:"],
    "a": ["now? {c410} —", "as near as", "one can measure."],
    "c5": ["a woman, ever so warm,", "moves on. no more."],
    "t": ["o, ever so,", "ever so!"],
    "c6": ["our man uncovers a case:", "a {key} on a screw — annex."],
    "f": ["so... now, near a case...", "...ummm... a reason...?"],
    "c7": ["a {key} on a screw, as ever.", "annex: secure as ever."],
    "card": ["annex"],
}


def all_text():
    out = []
    for v in TEXT.values():
        out += v if isinstance(v, list) else [v]
    return out


def check():
    bad = []
    for s in all_text():
        s2 = TOKEN.sub("", s)
        for ch in s2:
            if ch.isalpha() and ch not in ALLOWED:
                bad.append((s, ch))
            elif not ch.isalpha() and ch not in PUNCT:
                bad.append((s, ch))
    assert not bad, bad
    return True


# ------------------------------------------------------------------ inline lettering with drawn pictures
def pic(kind, cap):
    """A small pen picture the height of the line band: clock (4:15 / 4:10) or key."""
    Hh = int(round(cap * 2.2))
    yb = cap * 1.15
    ss = 3
    th = max(1, int(round(PEN * ss)))
    if kind == "key":
        w = int(cap * 1.75)
        m = np.zeros((Hh * ss, w * ss), np.uint8)
        cy = (yb - cap * 0.31) * ss
        r = cap * 0.27 * ss
        cv2.circle(m, (int(cap * 0.40 * ss), int(cy)), int(r), 255, th, cv2.LINE_AA)
        x0, x1 = cap * 0.40 * ss + r, cap * 1.55 * ss
        cv2.line(m, (int(x0), int(cy)), (int(x1), int(cy)), 255, th, cv2.LINE_AA)
        for bx in (1.25, 1.50):
            cv2.line(m, (int(cap * bx * ss), int(cy)), (int(cap * bx * ss), int(cy + cap * 0.30 * ss)), 255, th, cv2.LINE_AA)
    else:
        mm = 15 if kind == "c415" else 10
        w = int(cap * 1.60)
        m = np.zeros((Hh * ss, w * ss), np.uint8)
        cx, cy, r = w * ss / 2, (yb - cap * 0.40) * ss, cap * 0.70 * ss
        cv2.circle(m, (int(cx), int(cy)), int(r), 255, th, cv2.LINE_AA)
        for k in range(0, 12, 3):
            a = math.radians(k * 30)
            cv2.line(m, (int(cx + r * 0.78 * math.sin(a)), int(cy - r * 0.78 * math.cos(a))),
                     (int(cx + r * 0.95 * math.sin(a)), int(cy - r * 0.95 * math.cos(a))), 255, th, cv2.LINE_AA)
        am, ah = math.radians(mm * 6), math.radians(4 * 30 + mm * 0.5)
        cv2.line(m, (int(cx), int(cy)), (int(cx + r * 0.86 * math.sin(am)), int(cy - r * 0.86 * math.cos(am))), 255, th, cv2.LINE_AA)
        cv2.line(m, (int(cx), int(cy)), (int(cx + r * 0.52 * math.sin(ah)), int(cy - r * 0.52 * math.cos(ah))), 255, th, cv2.LINE_AA)
    return cv2.resize(m, (w, Hh), interpolation=cv2.INTER_AREA)


def trim(m):
    cols = np.nonzero(m.max(0))[0]
    return m[:, cols.min():cols.max() + 1] if len(cols) else m[:, :1]


def line_mask(s, cap, seed):
    parts, pos = [], 0
    for mt in TOKEN.finditer(s):
        if mt.start() > pos:
            parts.append(("t", s[pos:mt.start()]))
        parts.append(("p", mt.group(1)))
        pos = mt.end()
    if pos < len(s):
        parts.append(("t", s[pos:]))
    Hh = int(round(cap * 2.2))
    gap = int(cap * 0.42)
    pieces = []
    for k, (kind, v) in enumerate(parts):
        if kind == "t":
            if not v.strip():
                continue
            m = trim(P.letters([v.strip()], cap, seed + k))
            if m.shape[0] != Hh:
                mm = np.zeros((Hh, m.shape[1]), np.uint8)
                mm[:min(Hh, m.shape[0])] = m[:Hh]
                m = mm
            pieces.append(m)
        else:
            pieces.append(trim(pic(v, cap)))
    out = np.zeros((Hh, sum(p.shape[1] for p in pieces) + gap * (len(pieces) + 1)), np.uint8)
    x = gap
    for p in pieces:
        out[:, x:x + p.shape[1]] = np.maximum(out[:, x:x + p.shape[1]], p)
        x += p.shape[1] + gap
    return out


def block(lines, cap, seed, align="left"):
    ms = [line_mask(l, cap, seed + 31 * i) for i, l in enumerate(lines)]
    lh = int(cap * 1.42)
    Wm = max(m.shape[1] for m in ms)
    out = np.zeros((lh * (len(ms) - 1) + ms[-1].shape[0], Wm), np.uint8)
    for i, m in enumerate(ms):
        x = 0 if align == "left" else (Wm - m.shape[1]) // 2
        out[i * lh:i * lh + m.shape[0], x:x + m.shape[1]] = np.maximum(out[i * lh:i * lh + m.shape[0], x:x + m.shape[1]], m)
    return out


def caption(p, lines, x, y, seed, cap=36, box=True):
    m = block(lines, cap, seed)
    h, w = m.shape
    if box:
        p.rect(x, y, x + w + 10, y + h - cap * 0.55)
    p.text.append((m, x + 5 + w / 2, y + h / 2 - cap * 0.30))


def balloon(p, lines, cx, cy, tip, seed, cap=P.LCAP):
    m = block(lines, cap, seed, align="centre")
    ink_h = (len(lines) - 1) * cap * 1.42 + cap * 0.62
    rx, ry = (m.shape[1] - cap * 0.8) / 2 * 1.22 + cap * 0.55, ink_h / 2 * 1.30 + cap * 0.62
    u = np.zeros_like(p.m)
    SS = P.SS
    cv2.ellipse(u, (int(cx * SS), int(cy * SS)), (int(rx * SS), int(ry * SS)), 0, 0, 360, 255, -1)
    ang = math.atan2(tip[1] - cy, tip[0] - cx)
    bw = 0.22
    base = [(cx + rx * 0.8 * math.cos(ang + s * bw), cy + ry * 0.8 * math.sin(ang + s * bw)) for s in (-1, 1)]
    cv2.fillPoly(u, [np.int32(np.array([base[0], tip, base[1]], float) * SS)], 255)
    cs, _ = cv2.findContours(u, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len)[:, 0, :].astype(float) / SS
    p.m[u > 0] = 0
    p.line(c[::3], closed=True)
    p.text.append((m, cx, cy + cap * 0.26))


# ------------------------------------------------------------------ props
def memo(p, x, y, seed):
    m = block(TEXT["memo"], 32, seed)
    h, w = m.shape
    p.rect(x, y, x + w + 16, y + h - 4)
    p.text.append((m, x + 8 + w / 2, y + h / 2 - 2))


def key(p, cx, top, s=1.0):
    """page 51's outline key on its screw, with its tag lettered 'annex'"""
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
    p.line([(cx + r1 * 0.7, by + r1 * 0.7), (tx - 34 * s, ty - 12 * s)])
    p.word(TEXT["card"], int(22 * s), tx + 6 * s, ty, 6299, box=True, pad=(9, 4))


def card(p, cx, cy, seed):
    p.word(TEXT["card"], 32, cx, cy, seed, box=True, pad=(14, 2))


def window_blank(p, wx0, wy0, ww, wh, sill, st_args=None):
    if st_args:
        p.shapes(B.stranger(*st_args[0], **st_args[1]))
    ws, _ = B.window(wx0, wy0, ww, wh, sill=sill, header=72)
    p.shapes(ws[:5])          # frame, posts, sill, counter: no glazing bars across her face


# ------------------------------------------------------------------ panels
BOX = {1: (110, 230, 1180, 1050), 2: (1215, 230, 2090, 1050),
       3: (110, 1085, 760, 1905), 4: (790, 1085, 1440, 1905), 5: (1470, 1085, 2090, 1905),
       6: (110, 1940, 1085, 2730), 7: (1115, 1940, 2090, 2730)}


def size(k):
    x0, y0, x1, y1 = BOX[k]
    return x1 - x0, y1 - y0


def Q1(st):
    w, h = size(1)
    p = P.Pen(w, h, 6201)
    fl = h - 70
    P.floor(p, w, fl)
    p.shapes(B.agent(330, fl, face=1, scale=0.64, legs=(12, -6), lean=10, tilt=8, sh=30, el=-10, pencil_deg=200))
    p.shapes(B.desk(420, fl - 250, 470, fl))
    memo(p, 450, fl - 460, 6202)
    caption(p, TEXT["c1"], 30, 28, 6203)
    return p


def Q2(st):
    w, h = size(2)
    p = P.Pen(w, h, 6211)
    fl = h - 70
    P.floor(p, w, fl)
    cs, _ = B.cupboard(560, 260, 200, fl - 260)
    p.shapes(cs)
    p.shapes(B.agent(300, fl, face=1, scale=0.64, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200))
    for yy in (330, 420, 510):
        p.line([(90, yy), (160, yy)])
    caption(p, TEXT["c2"], 30, 28, 6213)
    return p


def Q3(st):
    w, h = size(3)
    p = P.Pen(w, h, 6221)
    fl = h - 70
    P.floor(p, w, fl)
    window_blank(p, 50, 330, 330, fl - 330, 650, ((205, 760), dict(face=1, scale=1.10)))
    p.shapes(B.agent(530, fl, face=-1, scale=0.58, sh=6, el=16, tilt=4, pencil_deg=190))
    caption(p, TEXT["c3"], 24, 24, 6223, cap=34)
    balloon(p, TEXT["q"], 300, 236, (220, 440), 6224, cap=40)
    return p


def Q4(st):
    w, h = size(4)
    p = P.Pen(w, h, 6231)
    fl = h - 70
    P.floor(p, w, fl)
    p.shapes(B.clock(150, 270, 86, 4, 10))
    p.shapes(B.agent(545, fl, face=-1, scale=0.58, sh=6, el=16, tilt=-24, pencil_deg=190, lean=-4))
    caption(p, TEXT["c4"], 24, 24, 6233, cap=34)
    balloon(p, TEXT["a"], 236, 630, (515, 330), 6234, cap=40)
    return p


def Q5(st):
    w, h = size(5)
    p = P.Pen(w, h, 6241)
    fl = h - 70
    P.floor(p, w, fl)
    window_blank(p, 40, 330, 320, fl - 330, 650, ((80, 760), dict(face=-1, scale=1.10)))
    p.shapes(B.agent(500, fl, face=-1, scale=0.58, sh=4, el=12, pencil_deg=190))
    caption(p, TEXT["c5"], 24, 24, 6243, cap=34)
    balloon(p, TEXT["t"], 260, 240, (150, 420), 6244, cap=44)
    return p


def Q6(st):
    w, h = size(6)
    p = P.Pen(w, h, 6251)
    fl = h - 60
    P.floor(p, w, fl)
    deg = st.get("open", 72)
    cs, ins = B.cupboard(300, 210, 270, fl - 230, open_deg=deg)
    p.shapes(cs)
    if ins:
        key(p, (ins[0] + ins[2]) / 2 + 10, ins[1] + 80, 1.25)
    p.shapes(B.agent(720, fl, face=-1, scale=0.62, sh=26, el=30, tilt=6, pencil_deg=190))
    caption(p, TEXT["c6"], 24, 24, 6253, cap=34)
    return p


def Q7(st):
    w, h = size(7)
    p = P.Pen(w, h, 6261)
    fl = h - 60
    P.floor(p, w, fl)
    cs, ins = B.cupboard(110, 250, 260, fl - 270, open_deg=72)
    p.shapes(cs)
    key(p, (ins[0] + ins[2]) / 2 + 10, ins[1] + 80, 1.2)
    p.shapes(B.service_door(800, 300, 130, fl - 300))
    card(p, 865, 356, 6262)
    p.shapes(B.agent(600, fl - 6, face=-1, scale=0.62, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    if st.get("line", True):
        balloon(p, TEXT["f"], 726, 150, (640, 250), 6263, cap=34)
    caption(p, TEXT["c7"], 24, 24, 6264, cap=32)
    return p


PANELS = {1: Q1, 2: Q2, 3: Q3, 4: Q4, 5: Q5, 6: Q6, 7: Q7}


def frames_mask(ks):
    p = P.Pen(W, H, 6290)
    for k in ks:
        x0, y0, x1, y1 = BOX[k]
        p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)
    return cv2.resize(p.m, (W, H), interpolation=cv2.INTER_AREA)


def header_mask():
    m = P.letters([TEXT["head"]], 50, 6280)
    out = np.zeros((H, W), np.uint8)
    B.put_mask(out, m, W / 2, 168)
    return out


def build(state=None, upto=7):
    check()
    state = state or {}
    pg = P.SHEET.copy()
    ink = np.maximum(frames_mask(range(1, 8)), header_mask())
    for k in range(1, upto + 1):
        x0, y0, x1, y1 = BOX[k]
        m = PANELS[k](state.get(k, {})).render()[:y1 - y0, :x1 - x0]
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
    img, size_ = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_)
    if "--page" not in sys.argv:
        states = [({}, 0), ({}, 1), ({}, 2), ({}, 3), ({}, 5), ({6: {"open": 0}}, 6), ({7: {"line": False}}, 7), ({}, 7)]
        print("beats", B.save_beats(N, [np.asarray(Image.fromarray(finish(build(s, u))).resize((960, 1242), Image.LANCZOS))
                                        for s, u in states]))
