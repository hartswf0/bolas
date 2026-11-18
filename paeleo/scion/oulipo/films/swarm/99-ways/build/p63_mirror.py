"""99 ways, page 63 "Mirror" (reader and object; medium: stencil-dye).

The page is printed as its own mirror image: six panels of HANDMADE stencils in flat dyes (page 08's stencil
kit, p08_lipogram: one cut stencil per dye with paper ties, misregistration, mottle and edge pooling; the
b1m2 cut model; the ANRC 1922 key cutout used as a stencil) with captions, the four canon lines, MEMO,
TICKET OFFICE and SERVICE in the shared pen hand, composed the right way round and then the whole sheet is
printed reversed, so every word, and the reading order of the panels, comes true only in a mirror. The folio
line alone is printed the right way.
Run: python3 -I p63_mirror.py"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p08_lipogram as S  # noqa: E402
from b1m2 import *  # noqa: E402,F401

N, PID, TITLE = 63, "mirror", "Mirror"
BOX = {"P1": (110, 110, 2090, 720),
       "P2": (110, 760, 1080, 1400), "P3": (1120, 760, 2090, 1400),
       "P4": (110, 1440, 1080, 2080), "P5": (1120, 1440, 2090, 2080),
       "P6": (110, 2120, 2090, 2730)}
TEXT = {
    "c1": "Randolph station, 1937. The memo says: open the SERVICE door at 4:15; the key is in the cupboard. Up he gets to fetch it.",
    "c2": "On his way, a lady at the ticket window:",
    "c3": "He looks up at the wall clock:",
    "c4": "She thanks him and goes.",
    "c5": "He opens the cupboard: the key hangs on its hook, tagged SERVICE.",
    "c6": "The key stays on its hook. The SERVICE door stays closed.",
    "q": ["Pardon me —", "have you the", "right time?"],
    "a": ["Ten past four,", "by the clock."],
    "t": ["Much", "obliged!"],
    "f": ["Well, here I am...", "and what for?"],
}
PAPER = np.array([248, 244, 230], np.float32)


def size(k):
    x0, y0, x1, y1 = BOX[k]
    return x1 - x0, y1 - y0


def printed(fig, w, h, floor, seed, extra=None):
    lay = S.layers_for(fig, w, h, wall_floor=floor)
    for name, m in (extra or []):
        lay.append((name, m))
    c = S.print_panel(w, h, lay, seed)
    c *= S.SHEET[:h, :w].mean(axis=2, keepdims=True) / S.SHEET.mean()
    return c


def board(c, x0, y0, w, header, seed):
    if not S.STAGE["text"]:
        return
    l = letter(["TICKET OFFICE"], 28, seed, weight=0.17)
    s_ = min(1.0, (w + 30) / l.shape[1])
    l = cv2.resize(l, (int(l.shape[1] * s_), int(l.shape[0] * s_)), interpolation=cv2.INTER_AREA)
    lm = np.zeros(c.shape[:2], np.uint8)
    put_mask(lm, l, x0 + w / 2, y0 + header / 2 + 3)
    comp(c, lm, np.array([246, 240, 222], np.float32))


def card(c, x, y, cap, seed, tilt=0.0):
    if S.STAGE["text"]:
        slip(c, int(x), int(y), ["SERVICE"], cap, seed, paper=PAPER, pad=(14, 5), tilt=tilt, shadow=0.3)


def P1(st):
    w, h = size("P1")
    floor = h - 80
    fig = agent(560, floor + 6, face=1, scale=0.52, legs=(16, -10), sh=10, el=40, pencil_deg=200, lean=6)
    fig += desk(640, floor - 200, 360, floor)
    cup, _ = cupboard(1480, floor - 400, 190, 400)
    fig += cup + service_door(1730, floor - 470, 170, 470)
    c = printed(fig, w, h, floor, 6301)
    if not S.STAGE["text"]:
        return c
    S.caption(c, TEXT["c1"], 6302, cap=38, width=1300)
    slip(c, 690, floor - 300, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 26, 6303, paper=PAPER, tilt=-3, shadow=0.35)
    card(c, 1758, floor - 420, 26, 6304)
    return c


def window_panel(key, seed, st_kw, ag_kw, cap_key):
    w, h = size(key)
    floor = h - 70
    ws, sill = window(80, 170, 320, h - 170, sill=430, header=62)
    for s in ws:
        s.role = "window"
    fig = list(ws[:5]) + stranger(240 + st_kw.pop("dx", 0), sill + 4, scale=0.95, **st_kw) + agent(**ag_kw)
    c = printed(fig, w, h, floor, seed)
    board(c, 80, 170, 320, 62, seed + 3)
    if S.STAGE["text"]:
        S.caption(c, TEXT[cap_key], seed + 4, cap=38)
    return c


def P2(st):
    c = window_panel("P2", 6311, {"glove": True}, dict(x=720, floor=640, face=-1, scale=0.50, sh=8, el=20, tilt=-3, pencil_deg=190), "c2")
    S.bal(c, TEXT["q"], (640, 230), (330, 330), 6315, cap=40)
    return c


def P3(st):
    w, h = size("P3")
    floor = h - 70
    fig = clock(280, 300, 95, swing=8) + agent(660, floor + 6, face=-1, scale=0.50, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
    c = printed(fig, w, h, floor, 6321)
    S.caption(c, TEXT["c3"], 6322, cap=38)
    S.bal(c, TEXT["a"], (330, 530), (610, 380), 6323, cap=42)
    return c


def P4(st):
    c = window_panel("P4", 6331, {"dx": -40, "face": -1, "tilt": -4}, dict(x=720, floor=640, face=-1, scale=0.50, sh=4, el=10, tilt=2, pencil_deg=190), "c4")
    S.bal(c, TEXT["t"], (560, 250), (300, 330), 6335, cap=44)
    return c


def cupboard_panel(key, seed, ag_kw, cap_key, sdoor, open_deg=112):
    w, h = size(key)
    floor = h - 70
    c0, c1, cw, ch = (360 if not sdoor else 250), 150, 260, floor - 150
    cup, ins = cupboard(c0, c1, cw, ch, open_deg=open_deg)
    fig = list(cup)
    if sdoor:
        fig += service_door(1500, 110, 230, floor - 110)
    fig += agent(**ag_kw)
    extra = []
    kx = ky = None
    if ins is not None:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + 115
        extra.append(("ochre", S.key_stencil(w, h, kx, ky, 0.24)))
    c = printed(fig, w, h, floor, seed, extra)
    if not S.STAGE["text"]:
        return c
    if kx is not None:
        hk = np.zeros((h, w), np.uint8)
        penlib.brush_line(hk, [(kx - 20, ky - 94), (kx + 3, ky - 94), (kx + 3, ky - 80)], 7, seed + 3)
        comp(c, hk, S.UMBER)
        card(c, kx + 8, ky + 30, 22, seed + 4, tilt=8)
    if sdoor:
        card(c, 1540, 170, 30, seed + 5)
    S.caption(c, TEXT[cap_key], seed + 6, cap=38, width=(w - 70) if not sdoor else 1100)
    return c


def P5(st):
    return cupboard_panel("P5", 6341, dict(x=200, floor=576, face=1, scale=0.50, legs=(14, -12), sh=60, el=20, pencil_deg=200), "c5",
                          sdoor=False, open_deg=st.get("open", 112))


def P6(st):
    c = cupboard_panel("P6", 6351, dict(x=1050, floor=546, face=-1, scale=0.52, legs=(3, -3), sh=48, el=118, wr=8, pencil_deg=40, tilt=-6),
                       "c6", sdoor=True)
    if st.get("line", True):
        S.bal(c, TEXT["f"], (760, 260), (1060, 160), 6352, cap=46)
    return c


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6)]


def build_true(state=None):
    """The page composed the right way round (never published as such)."""
    state = state or {}
    page = S.SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOX[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOX.values()), w=10, seed=6390)
    return page


def reverse(page):
    """Print it reversed: the whole sheet mirrored left to right. The sheet's own fibre is re-laid the right
    way (only the ink is reversed, as a print from a reversed stencil set would be)."""
    sheet = S.SHEET
    ink = page / np.maximum(sheet, 1)
    return np.clip(ink[:, ::-1] * sheet, 0, 255)


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


def mirror_view(rev, true, x_edge):
    """A hand mirror slid in from the left over the reversed page: left of its edge we see the reflection
    (the page reading true), tinted as glass; a bevelled edge line."""
    out = rev.copy()
    xe = int(x_edge)
    if xe > 0:
        glass = true[:, :xe].astype(np.float32) * np.array([0.93, 0.96, 0.98], np.float32) + 6
        out[:, :xe] = np.clip(glass, 0, 255).astype(np.uint8)
        e0, e1 = max(0, xe - 14), min(out.shape[1], xe + 4)
        out[:, e0:e1] = (out[:, e0:e1] * 0.35 + np.array([200, 210, 214]) * 0.65).astype(np.uint8)
        out[:, max(0, xe - 3):min(out.shape[1], xe + 3)] = 40
    return out


if __name__ == "__main__":
    true = build_true()
    rev = reverse(true)
    img, size_ = save_page(rev.copy(), N, PID, TITLE)
    print("jpeg bytes", size_)
    if "--page" not in sys.argv:
        frames = []
        order = S.ORDER
        for k, dyes in enumerate([order[:2], order[:4], order[:6], order[:7]]):
            S.STAGE["dyes"], S.STAGE["text"] = set(dyes), False
            frames.append(finish(reverse(build_true())))
        S.STAGE["dyes"], S.STAGE["text"] = None, True
        rev_f = finish(rev.copy())
        frames.append(rev_f)
        t = np.clip(np.round(true), 0, 255).astype(np.uint8)
        for xe in (W * 0.38, W * 0.72, W + 20):
            f = mirror_view(rev_f, t, min(W, xe))
            pen99.folio(f, N, TITLE)
            frames.append(f)
        print("beats", save_beats(N, frames))
