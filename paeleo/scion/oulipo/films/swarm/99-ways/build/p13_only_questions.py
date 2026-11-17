"""Page 13 Only questions (voice and language; medium: shadow-puppet).

Black cut-paper shadow puppets on rods (the b1m2 figure model, HANDMADE) against eight warm, lantern-lit
paper screens; every caption and every balloon is a question, the answer and the thanks included
('Ten past four, by the clock?', 'Much obliged?'). The memo is a blank card on the desk (its words are
carried by the P1 question), so no sentence on the page ends without a question mark.
Lettering: the shared pen hand. Folio by pen99.folio.
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

N, PID, TITLE = 13, "only-questions", "Only questions"
SIL = np.array([16, 12, 10], np.float32)
SHEET = pen99.sheet99()
FIBRE = SHEET.mean(axis=2) - SHEET.mean()

COLS = ((110, 1080), (1120, 2090))
ROWS = ((110, 730), (770, 1390), (1430, 2050), (2090, 2730))
BOXES = {f"P{r * 2 + c + 1}": (COLS[c][0], ROWS[r][0], COLS[c][1], ROWS[r][1]) for r in range(4) for c in range(2)}
CAP = 40
BCAP = 48


def screen(w, h, ox, oy, hot=(0.5, 0.5), spread=0.9):
    """A lantern behind a paper screen: warm amber hotspot fading to a red-brown rim, fibre of the 1934 sheet."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d2 = ((xx / w - hot[0]) ** 2 + ((yy / h - hot[1]) * h / w) ** 2)
    v = np.exp(-d2 / (2 * (spread * 0.5) ** 2))
    rim, mid, core = (np.array([92, 46, 22], np.float32), np.array([214, 142, 70], np.float32),
                      np.array([252, 226, 170], np.float32))
    v3 = v[..., None]
    img = np.where(v3 < 0.5, rim + (mid - rim) * (v3 / 0.5), mid + (core - mid) * ((v3 - 0.5) / 0.5))
    img = img + FIBRE[oy:oy + h, ox:ox + w][..., None] * 1.1
    return img.astype(np.float32)


def sil(img, shapes, blur=0.7, alpha=1.0):
    m = raster(shapes, img.shape[1], img.shape[0])
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    comp(img, m, SIL, alpha)
    return m


def soft(img, shapes, blur=3.0, alpha=0.82):
    """A puppet held a hand's breadth off the screen (beyond the glass): soft-edged."""
    m = raster(shapes, img.shape[1], img.shape[0], holes=False)
    comp(img, cv2.GaussianBlur(m, (0, 0), blur), np.array([40, 24, 16], np.float32), alpha)


def rods(img, pts, h, w=4.5, blur=0.6):
    """Control rods of the puppets: thin straight sticks from a joint down past the bottom of the screen."""
    m = np.zeros(img.shape[:2], np.uint8)
    for (x, y, lean) in pts:
        x2 = x + lean
        cv2.line(m, (int(x * 4), int(y * 4)), (int(x2 * 4), int((h + 40) * 4)), 255, max(1, int(w)), cv2.LINE_AA, 2)
        cv2.circle(m, (int(x * 4), int(y * 4)), int(7 * 4), 255, -1, cv2.LINE_AA, 2)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    comp(img, m, SIL, 0.92)


def joints(shapes):
    """Rod anchor points of an agent puppet: chest and the near hand."""
    tor = [s for s in shapes if s.role == "waistcoat"][0].pts
    hand = [s for s in shapes if s.role == "skin" and s.z == 5][-1].pts
    return tor.mean(0), hand.mean(0)


SAID = []


def cap_slip(img, text, w_max, seed, x=24, y=22, cap=CAP):
    SAID.append(text)
    return slip(img, x, y, wrap(text, cap, w_max), cap, seed, paper=np.array([246, 238, 214], np.float32))


def window_letters(img, x0, y0, w, header, seed):
    m = letter(["TICKET OFFICE"], 34, seed, weight=0.17)
    sc = min(1.0, (w + 10) / m.shape[1])
    m = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    lm = np.zeros(img.shape[:2], np.uint8)
    put_mask(lm, m, x0 + w / 2, y0 + header / 2 + 3)
    comp(img, lm, np.array([250, 214, 150], np.float32))


def card_on(img, cx, cy, text, cap, seed, tilt=0.0):
    m = letter([text], cap, seed, weight=0.15)
    h, w = m.shape
    return slip(img, int(cx - w / 2 - 4), int(cy - h / 2), [text], cap, seed, paper=np.array([244, 232, 200], np.float32),
                pad=(12, 5), align="centre", tilt=tilt, shadow=0.0)


def hook(img, x, y):
    comp(img, raster([Shape(bar_pts((x - 22, y), (x + 4, y), 8), "h", smooth=False),
                      Shape(bar_pts((x, y), (x + 2, y + 30), 7), "h", smooth=False)], img.shape[1], img.shape[0]), SIL)


def key_sil(img, cx, cy, scale):
    """The ANRC 1922 key cutout as a black shadow shape, hung on its hook."""
    m = np.zeros(img.shape[:2], np.uint8)
    paste_mask(m, key_alpha(), cx, cy, scale)
    comp(img, cv2.GaussianBlur(m, (0, 0), 0.6), SIL)


# ------------------------------------------------------------------ panels
def qballoon(img, lines, cap, at, tip, seed, tail_w=0.24):
    SAID.append(" ".join(lines))
    return balloon(img, lines, cap, at, tip, seed, tail_w=tail_w)


def P1(st):
    x0, y0, x1, y1 = BOXES["P1"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.55, 0.6))
    floor = h - 16
    a = agent(400, floor + 20, face=1, scale=0.46, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
              pencil_deg=60, far_arm=(30, 60))
    sil(img, a + desk(170, 450, 560, floor) + lamp(680, 270, 180))
    # the memo: a blank paper card held to the screen on the desk (its words are asked in the caption)
    pm = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(pm, [np.int32(np.array([(250, 424), (420, 418), (424, 448), (252, 454)]) * 4)], 255, cv2.LINE_AA, 2)
    comp(img, pm, np.array([248, 238, 210], np.float32))
    c, hd = joints(a)
    rods(img, [(c[0], c[1], -30), (hd[0], hd[1], 40)], h)
    cap_slip(img, "Doesn't his memo say 4:15, open the SERVICE door, and isn't the key in the cupboard?", 900, 1311)
    return img


def P2(st):
    x0, y0, x1, y1 = BOXES["P2"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.4, 0.6))
    floor = h - 18
    c_, _ = cupboard(700, 270, 170, 320)
    a = agent(380, floor, face=1, scale=0.45, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200, far_arm=(22, 20))
    sil(img, c_ + desk(-180, 430, 260, floor) + a)
    c, hd = joints(a)
    rods(img, [(c[0], c[1], -40), (hd[0], hd[1], 30)], h)
    cap_slip(img, "So up he gets, and off he goes for the key, doesn't he?", 900, 1321)
    return img


def window_panel(w, h, ox, oy, seed, spose, apose, hot):
    img = screen(w, h, ox, oy, hot=hot)
    wx0, wy0, ww, wh = 60, 150, 300, h - 150
    ws, sill = window(wx0, wy0, ww, wh, sill=wy0 + 300, header=62)
    if spose is not None:
        soft(img, stranger(wx0 + ww / 2 + spose.get("dx", 0), sill + 30, face=spose.get("face", 1), scale=1.12,
                           glove=spose.get("glove", False), tilt=spose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, wx0, wy0, ww, 62, seed)
    a = agent(**apose)
    sil(img, a)
    c, hd = joints(a)
    rods(img, [(c[0], c[1], 30), (hd[0], hd[1], -20)], h)
    return img, sill


def P3(st):
    x0, y0, x1, y1 = BOXES["P3"]
    w, h = x1 - x0, y1 - y0
    img, sill = window_panel(w, h, x0, y0, 1331, {"glove": True, "dx": -10},
                             dict(x=780, floor=h + 30, face=-1, scale=0.56, sh=8, el=20, tilt=-4, pencil_deg=190), (0.35, 0.55))
    qballoon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (560, 330), (300, 340), 1332, tail_w=0.22)
    cap_slip(img, "And who's that at the ticket window?", 920, 1333, y=16)
    return img


def P4(st):
    x0, y0, x1, y1 = BOXES["P4"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.55, 0.42))
    a = agent(330, h + 90, face=1, scale=0.60, sh=6, el=16, tilt=-24, pencil_deg=190, lean=-4)
    sil(img, clock(560, 300, 78, swing=6) + a)
    c, hd = joints(a)
    rods(img, [(c[0], c[1], -30), (hd[0], hd[1], 20)], h)
    qballoon(img, ["Ten past four,", "by the clock?"], BCAP, (770, 480), (420, 330), 1341, tail_w=0.26)
    cap_slip(img, "And where would he look, if not up at the clock?", 900, 1342)
    return img


def P5(st):
    x0, y0, x1, y1 = BOXES["P5"]
    w, h = x1 - x0, y1 - y0
    img, sill = window_panel(w, h, x0, y0, 1351, {"face": -1, "dx": -50, "tilt": -6},
                             dict(x=780, floor=h + 30, face=-1, scale=0.56, sh=4, el=10, tilt=2, pencil_deg=190), (0.32, 0.55))
    qballoon(img, ["Much", "obliged?"], BCAP, (560, 330), (290, 340), 1352, tail_w=0.26)
    cap_slip(img, "And now, isn't she gone?", 920, 1353, y=16)
    return img


def cupboard_set(img, cx0, cy0, cw, chh, od, key_scale, sd_x=None, card_seed=1360):
    c, ins = cupboard(cx0, cy0, cw, chh, open_deg=od)
    sh = list(c)
    if sd_x is not None:
        sh += service_door(sd_x, cy0 - 50, 200, chh + 100)
    sil(img, [s for s in sh if s.role != "door"])
    if ins is not None:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2 + 10, iy0 + (iy1 - iy0) * 0.47
        hook(img, kx, ky - 723 * key_scale / 2 - 8)
        key_sil(img, kx, ky, key_scale)
        card_on(img, kx + 60 * key_scale / 0.5, ky + 140 * key_scale / 0.5, "SERVICE", 24, card_seed, tilt=8)
    sil(img, [s for s in sh if s.role == "door"])
    if sd_x is not None:
        card_on(img, sd_x + 100, cy0 + 30, "SERVICE", 28, card_seed + 1)
    return ins


def P6(st):
    """His hand on the knob of the still-closed cupboard: what's behind the door is the question."""
    x0, y0, x1, y1 = BOXES["P6"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.45, 0.55))
    cx0, cy0, cw, chh = 330, 170, 330, 420
    cupboard_set(img, cx0, cy0, cw, chh, 0, 0.40, card_seed=1361)
    knob = (cx0 + cw * 0.9, cy0 + chh * 0.5)
    best = None
    for sh in range(30, 95, 2):                       # pose the arm so the hand lands on the knob
        a = agent(800, h - 14, face=-1, scale=0.50, sh=sh, el=6, wr=0, pencil=False, tilt=-4)
        hd = joints(a)[1]
        err = abs(hd[1] - knob[1])
        if best is None or err < best[0]:
            best = (err, sh, hd)
    _, sh, hd = best
    a = agent(800 + (knob[0] + 6 - hd[0]), h - 14, face=-1, scale=0.50, sh=sh, el=6, wr=0, pencil=False, tilt=-4)
    sil(img, a)
    c, hd = joints(a)
    rods(img, [(c[0], c[1], 20), (hd[0], hd[1], 70)], h)
    cap_slip(img, "And what's behind the cupboard door?", 920, 1362, y=16)
    return img


def P7(st):
    x0, y0, x1, y1 = BOXES["P7"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.5, 0.5), spread=0.7)
    # close on the open cupboard: the key large on its hook
    cupboard_set(img, 250, 130, 470, 640, st.get("open", 112), 0.62, card_seed=1371)
    cap_slip(img, "Isn't that the brass key, on its hook, tagged SERVICE, in plain view?", 860, 1372)
    return img


def P8(st):
    x0, y0, x1, y1 = BOXES["P8"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.42, 0.55))
    cupboard_set(img, 70, 250, 250, 330, 112, 0.30, sd_x=760, card_seed=1381)
    a = agent(500, h - 14, face=-1, scale=0.50, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2)
    sil(img, a)
    c, hd = joints(a)
    rods(img, [(c[0], c[1], 40), (hd[0], hd[1], -30)], h)
    if st.get("line", True):
        qballoon(img, ["Well, here I am...", "and what for?"], BCAP, (690, 112), (470, 230), 1382, tail_w=0.22)
    cap_slip(img, "And the key, still on its hook?", 400, 1383, x=24, y=h - 120, cap=34)
    cap_slip(img, "And the SERVICE door, still closed?", 250, 1384, x=600, y=h - 160, cap=32)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7), ("P8", P8)]
def build(state=None):
    state = state or {}
    page = SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=12, seed=1390)
    return page


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    import re
    page = build()
    sents = [x for t in SAID for x in re.split(r"(?<=[?])\s+", t.strip())]
    assert all(x.endswith("?") for x in sents), sents
    print(len(SAID), "texts,", len(sents), "sentences, all end with '?'")
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        # the beat: the thanks recast as a question is laid, then the cupboard opens and the forgetting is asked
        states = [{"P7": {"open": a}, "P8": {"line": False}} for a in (0, 35, 70, 112)] + [{}]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s))).resize((960, 1242), Image.LANCZOS)) for s in states])
