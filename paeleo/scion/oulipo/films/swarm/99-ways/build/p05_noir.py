"""Page 05 Noir (genre; medium: shadow-puppet).

Black cut-paper silhouette puppets (b1m2 figure model, HANDMADE) and cut set pieces against a lit paper
screen crossed by blind-slat light. The only colour is the brass key: the ANRC 1922 key photograph
(99-ways-template cutout, public domain) laid as an amber gel, so the key is the one lit thing in the dark.
Hardboiled first-person captions in the shared pen hand on pasted slips; the four canon lines unchanged.
"""
import json
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

N, PID, TITLE = 5, "noir", "Noir"
SIL = np.array([15, 14, 13], np.float32)
SHEET = pen99.sheet99()
FIBRE = SHEET.mean(axis=2) - SHEET.mean()


def screen(w, h, ox, oy, hot=(0.5, 0.45), spread=0.75, slats=None, seed=0):
    """Lit paper screen: lamp hotspot, fibre of the 1934 sheet, blind-slat shadow bands."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d2 = ((xx / w - hot[0]) ** 2 + ((yy / h - hot[1]) * h / w) ** 2)
    v = np.exp(-d2 / (2 * (spread * 0.5) ** 2))
    dark, bright = np.array([70, 66, 62], np.float32), np.array([228, 222, 208], np.float32)
    img = dark + (bright - dark) * v[..., None]
    if slats:
        ang, per, duty, x0, x1, op = slats
        a = math.radians(ang)
        u = (xx * math.sin(a) + yy * math.cos(a))
        band = ((u % per) < per * duty).astype(np.float32)
        # the slat light falls in a slanted window-shaped patch
        edge = (xx - x0 - (yy * 0.32)) / 30.0
        edge2 = (x1 + yy * 0.32 - xx) / 30.0
        patch = np.clip(edge, 0, 1) * np.clip(edge2, 0, 1)
        band = cv2.GaussianBlur(band, (0, 0), 2.2)
        img *= (1 - op * band * patch)[..., None]
        img *= (1 - 0.28 * (1 - patch))[..., None]
    f = FIBRE[oy:oy + h, ox:ox + w]
    img += f[..., None] * 0.9
    return img


def sil(img, shapes, blur=0.6, color=SIL, alpha=1.0, roles=None):
    m = raster(shapes, img.shape[1], img.shape[0], roles=roles)
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    comp(img, m, color, alpha)
    return m


def far(img, shapes, blur=2.2, alpha=0.86):
    """A puppet held back from the screen, beyond the glass: soft and grey."""
    m = raster(shapes, img.shape[1], img.shape[0], holes=False)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    comp(img, m, np.array([46, 43, 40], np.float32), alpha)


def window_letters(img, x0, y0, w, header, seed):
    """'TICKET OFFICE' cut out of the header board: light through the letters."""
    m = letter(["TICKET OFFICE"], 40, seed, weight=0.17)
    sc = min(1.0, (w + 20) / m.shape[1])
    m = cv2.resize(m, (int(m.shape[1] * sc), int(m.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    lm = np.zeros(img.shape[:2], np.uint8)
    put_mask(lm, m, x0 + w / 2, y0 + header / 2 + 4)
    comp(img, lm, np.array([226, 214, 186], np.float32))


def brass_key(img, cx, cy, scale, deg=0, glow=True):
    a = key_alpha()
    g = key_gray()
    h, w = a.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, scale)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    A = cv2.warpAffine(a, M, (img.shape[1], img.shape[0]))
    G = cv2.warpAffine(g, M, (img.shape[1], img.shape[0]))
    if glow:
        halo = cv2.GaussianBlur(A, (0, 0), 26).astype(np.float32) / 255
        img += (np.array([120, 84, 20], np.float32) * np.clip(halo * 1.6, 0, 1)[..., None]) * 0.55
    brass = np.array([214, 160, 62], np.float32)[None, None] * (0.42 + 0.75 * (G / 255.0))[..., None]
    comp(img, A, 0, 1.0) if False else None
    af = A.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - af) + np.clip(brass, 0, 255) * af
    return A


def paper_card(img, cx, cy, lines, cap, seed, tilt=0.0, glow=False):
    m = letter(lines, cap, seed, weight=0.15)
    h, w = m.shape
    box = slip(img, int(cx - w / 2 - 6), int(cy - h / 2 - 2), lines, cap, seed, paper=np.array([236, 226, 196], np.float32),
               pad=(14, 6), align="centre", tilt=tilt, shadow=0.0)
    return box


def hook(img, x, y):
    m = raster([Shape(bar_pts((x - 26, y), (x + 4, y), 9), "h", smooth=False),
                Shape(bar_pts((x, y), (x + 2, y + 34), 8), "h", smooth=False)], img.shape[1], img.shape[0])
    comp(img, m, SIL)


# ------------------------------------------------------------------ the panels
BOXES = {
    "P1": (110, 110, 1180, 930), "P2": (1220, 110, 2090, 930),
    "P3": (110, 970, 770, 1790), "P4": (810, 970, 1450, 1790), "P5": (1490, 970, 2090, 1790),
    "P6": (110, 1830, 1010, 2730), "P7": (1050, 1830, 2090, 2730),
}
CAP = 40      # caption cap height (px on the 2200 page)
BCAP = 50     # balloon cap height


def cap_slip(img, text, w_max, seed, x=26, y=24, cap=CAP):
    lines = wrap(text, cap, w_max)
    return slip(img, x, y, lines, cap, seed)


def P1(st):
    x0, y0, x1, y1 = BOXES["P1"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.55, 0.62), spread=0.9, slats=(-24, 46, 0.46, 300, 860, 0.55))
    floor = h - 20
    sh = agent(430, floor + 40, face=1, scale=0.70, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
               pencil_deg=60, far_arm=(30, 60))
    sh += desk(180, 560, 640, floor) + lamp(760, 330, 230)
    sil(img, sh)
    # the memo slip lies on the desk, lit
    slip(img, 300, 456, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 31, 501, tilt=-3,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    cap_slip(img, "Four-fifteen, the memo said. Open the SERVICE door. The key's in the cupboard. Simple job. They all start simple.",
             860, 511)
    return img


def P2(st):
    x0, y0, x1, y1 = BOXES["P2"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.35, 0.6), spread=0.85, slats=(-24, 46, 0.46, 60, 520, 0.55))
    floor = h - 24
    c, _ = cupboard(600, 300, 200, 470)
    sh = c + desk(-200, 560, 300, floor)
    sh += agent(330, floor, face=1, scale=0.64, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200,
                far_arm=(22, 20))
    sil(img, sh)
    cap_slip(img, "So I got up and went for the key. Nine steps. I'd walked them a thousand times.", 640, 521)
    return img


def window_panel(w, h, ox, oy, seed, stranger_pose, agent_pose):
    img = screen(w, h, ox, oy, hot=(0.32, 0.55), spread=0.8, slats=(-24, 40, 0.46, -100, 330, 0.5))
    wx0, wy0, ww, wh = 50, 250, 300, 600
    ws, sill = window(wx0, wy0, ww, wh, sill=wy0 + 340, header=70)
    if stranger_pose is not None:
        far(img, stranger(wx0 + ww / 2 + stranger_pose.get("dx", 0), sill + 30, face=stranger_pose.get("face", 1),
                          scale=1.25, glove=stranger_pose.get("glove", False), tilt=stranger_pose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, wx0, wy0, ww, 70, seed)
    if agent_pose is not None:
        sil(img, agent(**agent_pose))
    return img, sill


def P3(st):
    x0, y0, x1, y1 = BOXES["P3"]
    w, h = x1 - x0, y1 - y0
    img, sill = window_panel(w, h, x0, y0, 531, {"glove": True, "dx": -20},
                             dict(x=520, floor=h + 120, face=-1, scale=0.80, sh=8, el=20, tilt=-4, pencil_deg=190))
    balloon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (300, 640), (226, 500), 532, tail_w=0.22)
    cap_slip(img, "Then a dame at the window. Hat, gloves, a voice like rain on the platform.", 560, 533)
    return img


def P4(st):
    x0, y0, x1, y1 = BOXES["P4"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.5, 0.38), spread=0.8, slats=(-24, 40, 0.46, 160, 560, 0.5))
    sh = clock(400, 330, 105, swing=6)
    sh += agent(250, h + 160, face=1, scale=0.86, sh=6, el=16, tilt=-24, pencil_deg=190, lean=-4)
    sil(img, sh)
    balloon(img, ["Ten past four,", "by the clock."], BCAP, (330, 690), (225, 350), 541)
    cap_slip(img, "I gave her the clock. Only honest face in the building.", 540, 542)
    return img


def P5(st):
    x0, y0, x1, y1 = BOXES["P5"]
    w, h = x1 - x0, y1 - y0
    img, sill = window_panel(w, h, x0, y0, 551, {"face": -1, "dx": -40, "tilt": -6},
                             dict(x=470, floor=h + 120, face=-1, scale=0.80, sh=4, el=10, tilt=2, pencil_deg=190))
    balloon(img, ["Much", "obliged!"], BCAP, (240, 660), (170, 520), 552, tail_w=0.26)
    cap_slip(img, "And she was gone. Took nothing. That's what I told myself.", 500, 553)
    return img


def cupboard_scene(img, w, h, cx0, cy0, cw, chh, open_deg, key_scale, sdoor=True, sd_x=None):
    c, ins = cupboard(cx0, cy0, cw, chh, open_deg=open_deg)
    sh = c
    if sdoor:
        sdx = cx0 + cw + 60 if sd_x is None else sd_x
        sh += service_door(sdx, cy0 - 60, 230, chh + 120)
    sil(img, sh, roles=None)
    if ins is not None:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.47
        hook(img, kx, iy0 + (iy1 - iy0) * 0.47 - 723 * key_scale / 2 - 10)
        brass_key(img, kx, ky, key_scale, deg=0)
        paper_card(img, kx + 66 * key_scale / 0.5, ky + 150 * key_scale / 0.5, ["SERVICE"], 26, 561, tilt=8)
        sil(img, [x for x in c if x.role == "door"])   # the leaf passes in front of the key while it swings
    if sdoor:
        sdx = cx0 + cw + 60 if sd_x is None else sd_x
        paper_card(img, sdx + 115, cy0 + 40, ["SERVICE"], 30, 562, tilt=0)


def P6(st):
    x0, y0, x1, y1 = BOXES["P6"]
    w, h = x1 - x0, y1 - y0
    od = st.get("open", 112)
    img = screen(w, h, x0, y0, hot=(0.45, 0.55), spread=0.85, slats=(-24, 44, 0.46, 220, 700, 0.55))
    cupboard_scene(img, w, h, 260, 240, 420, 620, od, 0.62, sdoor=False)
    # his hand on the door edge (the near arm reaching in from the left edge)
    if od > 0:
        th = math.radians(od)
        ex = 260 + 420 * math.cos(th)
        arm = [Shape(bar_pts((-40, 640), (ex + 10, 560), 54), "arm", smooth=False),
               Shape(circle_pts(ex + 14, 556, 30, 12), "hand")]
        sil(img, arm)
    cap_slip(img, "The cupboard. The key. Brass, on its hook, tagged SERVICE, looking at me like it knew something I didn't.",
             820, 563)
    return img


def P7(st):
    x0, y0, x1, y1 = BOXES["P7"]
    w, h = x1 - x0, y1 - y0
    img = screen(w, h, x0, y0, hot=(0.42, 0.55), spread=0.85, slats=(-24, 44, 0.46, 120, 640, 0.55))
    cupboard_scene(img, w, h, 110, 330, 300, 470, 112, 0.40, sdoor=True, sd_x=800)
    sil(img, agent(620, 760, face=-1, scale=0.64, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP, (330, 150), (560, 300), 571, tail_w=0.22)
    cap_slip(img, "The key stayed on its hook. The door stayed shut. Somebody took something off me that afternoon. "
                  "I still couldn't tell you what.", 940, 572, y=h - 200)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7)]


def build(state=None):
    state = state or {}
    page = SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=12)
    return page


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "page"
    if which == "page":
        page = build()
        img, size = save_page(page, N, PID, TITLE)
        print("jpeg bytes", size)
    if which in ("page", "beats"):
        states = [{"P6": {"open": a}, "P7": {"line": False}} for a in (0, 38, 76, 112)] + [{"P7": {"line": False}}, {}]
        frames = []
        for st in states:
            p = build(st)
            p = np.clip(np.round(p), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        frames[4] = frames[3]
        save_beats(N, frames[:4] + frames[5:])
