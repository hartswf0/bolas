"""Page 91 Polyptych (layout and page grammar; medium: charcoal-card).

One continuous charcoal-card drawing of the office wall runs behind all six panels: desk, ticket window, clock,
notice board, cupboard and SERVICE door are pinned up once, side by side, on one length of the teuf-teuf rock-wall
ground; its picture rail, wainscot and floor run unbroken from the first panel to the last. Six tall panels are then
cut out of it by paper gutters, and the agent (the same b1m2 card puppet) is pinned into each panel at that panel's
moment: E0 at the desk, E1 at the window, E2 under the clock, E3 walking on, E4 at the open cupboard, E5 before the
SERVICE door. The stranger appears only in the window panel, behind the glass.
Kit: build/charcoal99.py (card pieces, brads, spray halos, rock wall: Cueva de las manos, Suzko, CC BY-SA 3.0, via
teuf-teuf); the key card: build/p31_sounds_only.key_card (ANRC 1922 key silhouette); lettering in the shared pen hand.
Run: python3 -I p91_polyptych.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, lamp, Shape, R_  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p31_sounds_only as P31  # noqa: E402
from p77_the_cupboard import written  # noqa: E402

N, PID, TITLE = 91, "polyptych", "Polyptych"
W, H = 2200, 2850
X0, Y0, X1, Y1 = 110, 110, 2090, 2730
G = 30
WIDTHS = [380, 300, 280, 280, 300, 290]
PANELS = []
_x = X0
for _w in WIDTHS:
    PANELS.append((_x, Y0, _x + _w, Y1))
    _x += _w + G
assert PANELS[-1][2] == X1, PANELS[-1]
FLOOR = 2630
S = 1.02                           # agent scale
RAIL, WAIN = 760, 2180


def room(seed=9100):
    """The whole office wall, once, at page size (luminance)."""
    lum = C.wall(W, H, seed, level=0.86, hp_gain=0.55, broad_gain=0.38, scale=2.4)
    P31.floor_band(lum, FLOOR, seed + 1)
    # picture rail and wainscot: card strips the full length of the wall
    C.pin_up(lum, [R_(0, RAIL, W, RAIL + 22, "shelf"), R_(0, WAIN, W, WAIN + 30, "desk")], seed + 2, halo=False)
    for k, x in enumerate(range(20, W, 64)):
        C.charcoal_line(lum, [(x, WAIN + 40), (x + 2, FLOOR - 8)], 3, seed + 10 + k, dark=0.35, alpha=0.55, tremor=0.4)
    # P1: desk and lamp, memo card
    C.pin_up(lum, desk(130, 2260, 200, FLOOR) + lamp(290, 2010, 250), seed + 30)
    # P2: the ticket window
    ws, sill = window(545, 1480, 180, 760, sill=1480 + 760 * 0.62, header=80)
    gl = np.zeros(lum.shape, np.float32)
    gl[1560:int(sill), 545:725] = 1
    lum[:] = np.where(gl > 0, lum * 0.80 + 0.12, lum)
    C.pin_up(lum, ws, seed + 40, halo=False)
    written(lum, ["TICKET", "OFFICE"], 635, 1520, 22, seed + 41, dark=0.86)
    # P3: the clock, high
    C.pin_up(lum, clock(990, 1180, 88, hh=4, mm=10, pend=True, swing=8), seed + 50)
    # P4: a notice board with pinned cards
    nb = [R_(1185, 1180, 1415, 1480, "desk")]
    C.pin_up(lum, nb, seed + 60)
    for k, (x, y, w, h) in enumerate(((1205, 1200, 90, 110), (1310, 1210, 86, 70), (1215, 1330, 120, 120), (1345, 1300, 52, 150))):
        m = np.zeros(lum.shape, np.uint8)
        cv2.rectangle(m, (x, y), (x + w, y + h), 255, -1)
        C.drop(lum, m, (4, 5), 2.5, 0.3)
        C.card_piece(lum, m, 0.84, seed + 61 + k, edge=0.12)
        C.brad(lum, x + w / 2, y + 8, 5)
        for j in range(int(h / 22) - 1):
            C.charcoal_line(lum, [(x + 10, y + 26 + j * 20), (x + w - 12, y + 26 + j * 20)], 2.5, seed + 70 + k * 9 + j,
                            dark=0.35, alpha=0.7)
    written(lum, ["NOTICES"], 1300, 1150, 26, seed + 80, dark=0.16)
    # P5: the cupboard, open on its left jamb, the key on its hook
    cs, ins = cupboard(1500, 1780, 170, 850, open_deg=100)
    C.pin_up(lum, [s for s in cs if s.role != "door"], seed + 90, halo=True)
    ix0, iy0, ix1, iy1 = ins
    P31.key_card(lum, (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.30, 0.22, seed + 91)
    C.pin_up(lum, [s for s in cs if s.role == "door"], seed + 92, halo=False)
    # P6: the SERVICE door, shut, its card
    sx, sy, sw, sh = 1900, 1500, 170, FLOOR - 1500
    C.pin_up(lum, service_door(sx, sy, sw, sh), seed + 100)
    m = np.zeros(lum.shape, np.uint8)
    cv2.rectangle(m, (sx + 12, sy + 40), (sx + sw - 12, sy + 96), 255, -1)
    C.drop(lum, m, (4, 5), 2.5, 0.3)
    C.card_piece(lum, m, 0.80, seed + 101, edge=0.18)
    written(lum, ["SERVICE"], sx + sw / 2, sy + 70, 30, seed + 102, dark=0.12)
    # a long parcel shelf and a long departures board: both run on across the gutters
    C.pin_up(lum, [R_(0, 1000, W, 1018, "shelf")], seed + 120, halo=False)
    r = np.random.RandomState(seed)
    x = 30
    k = 0
    while x < W - 40:
        w_, h_ = r.randint(40, 110), r.randint(60, 150)
        tone_ = float(r.choice([0.30, 0.55, 0.72, 0.42]))
        m = np.zeros(lum.shape, np.uint8)
        cv2.rectangle(m, (x, 1000 - h_), (x + w_, 1000), 255, -1)
        C.drop(lum, m, (4, 5), 2.5, 0.28)
        C.card_piece(lum, m, tone_, seed + 130 + k, edge=0.18)
        if r.rand() < 0.5:
            C.charcoal_line(lum, [(x + 4, 1000 - h_ / 2), (x + w_ - 4, 1000 - h_ / 2)], 3, seed + 400 + k, dark=0.15, alpha=0.8)
        x += w_ + r.randint(6, 30)
        k += 1
    m = np.zeros(lum.shape, np.uint8)
    cv2.rectangle(m, (560, 250), (1650, 470), 255, -1)
    C.drop(lum, m, (6, 8), 3.5, 0.32)
    C.card_piece(lum, m, 0.16, seed + 140, edge=0.10)
    for xx in (580, 1630):
        C.brad(lum, xx, 270, 7)
        C.brad(lum, xx, 450, 7)
    written(lum, ["DEPARTURES"], 1105, 300, 40, seed + 141, dark=0.92)
    written(lum, ["NORTH 4:22   SOUTH 4:48   LOCAL 5:30"], 1105, 410, 44, seed + 142, dark=0.92)
    # ceiling: two hanging lamps on long flexes, crossing panels as the rail does
    for k, x in enumerate((440, 1900)):
        C.charcoal_line(lum, [(x, 0), (x + 2, 520)], 4, seed + 110 + k, dark=0.2, tremor=0.3)
        C.pin_up(lum, [Shape([(x - 90, 600), (x - 50, 520), (x + 50, 520), (x + 90, 600)], "lamp", smooth=False)],
                 seed + 112 + k, halo=False)
    # soft lamp light pooling on the wall below each lamp
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = sum(np.exp(-(((xx - x) / 520.0) ** 2 + ((yy - 900) / 900.0) ** 2)) for x in (440, 1900))
    lum *= (0.82 + 0.18 * np.clip(glow, 0, 1))
    return lum


def memo(lum, seed):
    m = np.zeros(lum.shape, np.uint8)
    pts = np.array([(118, 2196), (288, 2186), (292, 2254), (122, 2262)], np.float32)
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, m, (4, 5), 2.5, 0.3)
    C.card_piece(lum, m, 0.95, seed, edge=0.06, rub=0.02)
    written(lum, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 205, 2224, 15, seed + 1, dark=0.12)


FIG = {
    0: dict(x=370, face=1, legs=(14, -12), sh=-12, el=30, lean=6, pencil_deg=200, far_arm=(20, 20)),
    1: dict(x=745, face=-1, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190),
    2: dict(x=1030, face=-1, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3),
    3: dict(x=1300, face=1, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200, far_arm=(24, 22)),
    4: dict(x=1720, face=-1, legs=(4, -4), sh=40, el=-24, wr=0, pencil_deg=200, tilt=4),
    5: dict(x=1880, face=-1, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2),
}
LINES = {
    1: (["Pardon me —", "have you the", "right time?"], 36, (670, 1250), (610, 1640)),
    2: (["Ten past", "four, by", "the clock."], 38, (990, 1560), (990, 1700)),
    3: (["Much", "obliged!"], 40, (1290, 1610), (1162, 1700)),
    5: (["Well, here", "I am... and", "what for?"], 36, (1945, 1250), (1900, 1690)),
}


def build(stage=6, gutters=True):
    lum = room()
    memo(lum, 9150)
    base = lum.copy()
    out = base.copy()
    for i in range(min(stage, 6)):
        x0, y0, x1, y1 = PANELS[i]
        pl = base.copy()
        if i == 1:   # the stranger behind the glass, a paler card
            tmp = pl.copy()
            C.pin_up(tmp, stranger(610, 1960, face=1, scale=1.05, glove=True), 9160, halo=False,
                     tones=dict(coat=0.42, collar=0.55, skin_s=0.66, hat=0.30, bow=0.80, glove=0.38))
            gl = np.zeros(pl.shape, np.float32)
            gl[1562:1958, 547:723] = 1
            pl[:] = pl * (1 - gl) + tmp * gl
            ws, _ = window(545, 1480, 180, 760, sill=1480 + 760 * 0.62, header=80)
            C.pin_up(pl, ws, 9040, halo=False)
            written(pl, ["TICKET", "OFFICE"], 635, 1520, 22, 9141, dark=0.86)
        kw = dict(FIG[i])
        x = kw.pop("x")
        C.pin_up(pl, agent(x, FLOOR, scale=S, **kw), 9170 + i * 7)
        out[y0:y1, x0:x1] = pl[y0:y1, x0:x1]
    rgb = C.tone(out)
    for i in range(min(stage, 6)):
        if i in LINES:
            lines, cap, at, tip = LINES[i]
            x0, y0, x1, y1 = PANELS[i]
            b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), 9180 + i,
                                     tail_w=0.22, bend=0.08)
            tmp = rgb.copy()
            penlib.lay_balloon(tmp, b, at)
            rgb[y0:y1, x0:x1] = tmp[y0:y1, x0:x1]
    page = pen99.sheet99()
    if gutters:
        page[Y0:Y1, X0:X1] = page[Y0:Y1, X0:X1]
        for (x0, y0, x1, y1) in PANELS:
            page[y0:y1, x0:x1] = rgb[y0:y1, x0:x1]
        B.frame_border(page, PANELS, w=11, seed=9190)
    else:
        page[Y0:Y1, X0:X1] = rgb[Y0:Y1, X0:X1]
        B.frame_border(page, [(X0, Y0, X1, Y1)], w=11, seed=9190)
    return page


def main():
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg", size)
    if "beats" in sys.argv:
        frames = []
        for st, gt in ((0, False), (0, True), (1, True), (2, True), (3, True), (4, True), (5, True), (6, True)):
            p = np.clip(np.round(build(st, gt)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
