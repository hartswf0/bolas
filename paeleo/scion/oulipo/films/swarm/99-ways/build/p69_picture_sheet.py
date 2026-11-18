"""Page 69 Picture sheet (medium and material; medium: busch-fold).

A 19th-century picture sheet: a grid of plate pictures, a printed verse under each. No balloons anywhere: the
four canon lines are quoted inside the verses. Twelve pictures in a 3 x 4 grid under a sheet head ('PICTURE SHEET
No. 69 / THE AGENT AND THE KEY'), each picture a ruled plate with a rhymed couplet beneath (our own verses), a
colophon rule at the foot ('Plain one penny, coloured twopence'). The sheet is hand-coloured in five flat washes
laid slightly off register, as such sheets were coloured by stencil and brush, and it lies on the les-caids
tabletop with the creases of being sold folded in four.
Reuses page 59's busch-fold kit (build/p59_once_upon.py, p39_meanwhile.py, p11_station_cat.py): the agent = the
les-caids porter cutout (Busch 1865, Max und Moritz plate 31, PD), the stranger = Helene (Busch 1872, Die fromme
Helene, PD) with p39's HANDMADE cloche, seen through the ticket-window glass; the les-caids vintage paper
(CC BY 2.0) and wood (CC0); the ink set, washes, creases and lettering HANDMADE in code, the shared pen hand.
Run: python3 -I p69_picture_sheet.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p11_station_cat as k11  # noqa: E402
from p11_station_cat import line, hatch, text, ellipse_pts, affine  # noqa: E402
import p39_meanwhile as M39  # noqa: E402
import p59_once_upon as F  # noqa: E402
from b1m2 import wrap, save_beats  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
N, PID, TITLE = 69, "picture-sheet", "Picture sheet"
INK = F.INK
OUT_JPG = ROOT / "assets/pages/99-ways" / f"{N}-{PID}.jpg"
OUT_PNG = ROOT / "films/sources/99-ways/masters" / f"{N}-{PID}.png"

PW, PH, FLOOR = F.PW, F.PH, F.FLOOR           # pictures cut at p59's plate size (930 x 500), laid at 0.684
CW = 636
K = CW / PW
CH = int(round(PH * K))
COLX = (122, 122 + CW + 36, 122 + 2 * (CW + 36))
ROW0, ROWH = 424, 540
VCAP = 27

Q, A, T, FG = "Pardon me — have you the right time?", "Ten past four, by the clock.", "Much obliged!", \
    "Well, here I am... and what for?"
VERSES = [
    "At Randolph, at his desk, the agent reads his memo through: "
    "'At four-fifteen, the SERVICE door; the key is in the cupboard, too.'",
    "So up he gets, and off he goes, as brisk as brisk can be, "
    "across the office, with a will, to fetch the brass door key.",
    "He's nearly at the cupboard, near the SERVICE door, and then "
    "a tapping at the ticket glass! He turns back round again.",
    "A lady in a travelling hat is standing at the pane; "
    "she taps upon the ticket glass, and taps it once again.",
    f"'{Q}' she asks, polite and sweet. "
    "The agent clears his throat, and stops, and plants his feet.",
    "He lifts his eyes. He finds the clock upon the office wall. "
    "Its hands stand plain: the big at two, the small near four. That's all.",
    f"'{A}' he tells her, true and fair, "
    "with all a station agent's pride, and smooths his hair.",
    f"'{T}' the lady says, and nods, and bobs her hat, "
    "and turns away along the boards, and that, it seems, is that.",
    "The window's empty. Off she's gone. He's back upon his way; "
    "but something went along with her, though what, he cannot say.",
    "He comes up to the cupboard and he swings its door out wide: "
    "the brass key hanging on its hook, the SERVICE tag beside.",
    "He looks at it. It looks at him. It hangs in plain full view. "
    "He scratches at his cap and thinks... but what was he to do?",
    f"Pencil to chin: '{FG}' "
    "The key stays on its hook; and shut stays the SERVICE door.",
]
WASH = {"blue": np.array([150, 178, 214], np.float32), "red": np.array([222, 132, 120], np.float32),
        "ochre": np.array([226, 196, 132], np.float32), "green": np.array([150, 190, 146], np.float32),
        "glass": np.array([200, 214, 222], np.float32)}


def pieces():
    F.pieces()
    return F.PORTER, F.HELENE


def wash(c, mask, col, alpha=0.55, off=(5, 4), grow=3):
    """a flat colour wash laid by stencil and brush: the mask grown a little, shifted off register, multiplied"""
    m = (mask > 127).astype(np.uint8) * 255 if mask.dtype == np.uint8 else (mask > 0.5).astype(np.uint8) * 255
    if grow:
        m = cv2.dilate(m, np.ones((grow * 2 + 1, grow * 2 + 1), np.uint8))
    Mt = np.float32([[1, 0, off[0]], [0, 1, off[1]]])
    m = cv2.warpAffine(m, Mt, (m.shape[1], m.shape[0]))
    a = cv2.GaussianBlur(m, (0, 0), 1.4).astype(np.float32)[..., None] / 255 * alpha
    c[:] = c * (1 - a) + c * (col / 255.0) * a


def rect_mask(shape, x0, y0, x1, y1):
    m = np.zeros(shape, np.uint8)
    cv2.rectangle(m, (int(x0), int(y0)), (int(x1), int(y1)), 255, -1)
    return m


# ------------------------------------------------------------------ the twelve plate pictures (native 930 x 500)
def picture(i, ground, coloured):
    porter, helene = pieces()
    c = ground.copy()
    seed = 6900 + i * 53
    m = np.zeros((PH, PW), np.uint8)
    F.room(m, seed)
    win = i in (3, 4, 5, 6, 7, 8)
    if i in (0, 1):
        line(m, [(90, 300), (420, 300)], 7, seed + 10)
        line(m, [(100, 318), (420, 318)], 3, seed + 11)
        line(m, [(110, 318), (110, FLOOR)], 6, seed + 12)
        line(m, [(410, 318), (410, FLOOR)], 6, seed + 13)
        hatch(m, 116, 322, 404, FLOOR - 4, 18, 2, seed + 14, ang=-80)
    if i == 1:
        M39.clock(m, 720, 140, 48, seed + 40)
    if i == 2:
        F.cupboard(m, seed + 20, x0=520, x1=660, open_=False)
    if win:
        F.ticket_window(m, seed + 30)
    if i in (5, 6):
        M39.clock(m, 600 if i == 5 else 800, 130, 48, seed + 40)
    if i in (9, 10, 11):
        F.cupboard(m, seed + 50, x0=560, x1=700, open_=True)
    penlib.ink_onto(c, m, INK)
    if win:
        F.window_sign(c, seed + 35)
    if i in (2, 9, 10, 11):
        F.service_door(c, seed + 60)
    if i in (0, 1):
        F.memo_slip(c, [(170, 300), (186, 232), (330, 238), (330, 300)], seed + 70)
    if i in (9, 10, 11):
        M39.key_on_hook(c, (590, 180), seed + 80)
    # the stranger behind the glass
    hel_a = None
    if win and i != 8:
        glass = np.zeros((PH, PW), np.float32)
        glass[128:342, 58:312] = 1
        deg = {3: 0, 4: 0, 5: 0, 6: 0, 7: 10}[i]
        Mh = affine(M39.HEL_HAND, (300 if i != 7 else 230, 250), 0.62, deg=deg)
        hel_a = F.lay(c, helene, Mh, clip=glass)
    # the agent
    pose = {0: ((330, FLOOR + 30), 0.80, 6, True), 1: ((600, FLOOR + 30), 0.80, -4, False),
            2: ((330, FLOOR + 30), 0.80, 0, True), 3: ((640, FLOOR + 30), 0.78, 0, True),
            4: ((520, FLOOR + 30), 0.78, 0, True), 5: ((780, FLOOR + 30), 0.80, -12, True),
            6: ((560, FLOOR + 30), 0.80, 0, True), 7: ((540, FLOOR + 30), 0.80, 8, True),
            8: ((640, FLOOR + 30), 0.80, -4, False), 9: ((440, FLOOR + 30), 0.80, 0, False),
            10: ((420, FLOOR + 30), 0.80, -4, False), 11: ((460, FLOOR + 30), 0.80, 0, False)}[i]
    Ma = affine(M39.PORTER_FEET, pose[0], pose[1], deg=pose[2], flip=pose[3])
    ag_a = F.lay(c, porter, Ma)
    pm = np.zeros((PH, PW), np.uint8)
    if i == 11:
        line(pm, [F.pt(Ma, (M39.PORTER_HAND[0] + 2, M39.PORTER_HAND[1] - 4)),
                  F.pt(Ma, (M39.PORTER_CHIN[0] + 4, M39.PORTER_CHIN[1] + 4))], 8, seed + 120, tremor=0.2)
    if i == 2:      # the voice from behind: three pen ticks by his ear
        e = F.pt(Ma, (M39.PORTER_CHIN[0] - 40, M39.PORTER_CHIN[1] - 40))
        for k in range(3):
            a = math.radians(160 + k * 22)
            line(pm, [(e[0] - 30 * math.cos(a) * -1, e[1] + 30 * math.sin(a)), (e[0] - 56 * math.cos(a) * -1, e[1] + 56 * math.sin(a))],
                 3, seed + 130 + k)
    if i in (3,):   # her knuckle on the glass
        for k in range(2):
            line(pm, [(318 + 12 * k, 200 + 14 * k), (338 + 12 * k, 192 + 14 * k)], 3, seed + 140 + k)
    penlib.ink_onto(c, pm, INK)
    if coloured:
        sh = (PH, PW)
        wash(c, rect_mask(sh, 0, FLOOR + 6, PW, PH), WASH["ochre"], 0.55, off=(0, 3), grow=0)
        wash(c, ag_a, WASH["blue"], 0.40, off=(6, 4), grow=1)
        if hel_a is not None:
            wash(c, hel_a, WASH["red"], 0.55, off=(-5, 4))
        if win:
            wash(c, rect_mask(sh, 76, 146, 294, 324), WASH["glass"], 0.35, off=(4, 3), grow=0)
        if i in (2, 9, 10, 11):
            wash(c, rect_mask(sh, 788, 270, 892, FLOOR - 4), WASH["green"], 0.55, off=(5, -3), grow=0)
        if i in (0, 1):
            wash(c, rect_mask(sh, 116, 322, 404, FLOOR - 4), WASH["ochre"], 0.6, off=(4, 4), grow=0)
    return c


# ------------------------------------------------------------------ the sheet
def ornament_rule(m, x0, x1, y, seed):
    line(m, [(x0, y), (x1, y)], 5, seed, tremor=0.3)
    line(m, [(x0, y + 12), (x1, y + 12)], 2, seed + 1, tremor=0.3)
    cx = (x0 + x1) / 2
    for k, dx in enumerate((-30, 0, 30)):
        line(m, ellipse_pts(cx + dx, y + 6, 7, 7), 2.4, seed + 3 + k)


def sheet_build(colour_rows=4, upto=12):
    sheet = k11.paper()
    sheet = 236 + cv2.GaussianBlur(sheet - 238, (0, 0), 2.4) * 0.85
    sheet *= np.array([1.0, 0.985, 0.95], np.float32)          # the sheet's old cream
    m = np.zeros((H, W), np.uint8)
    text(m, ["PICTURE SHEET  No. 69"], W / 2, 168, 32, 6990, align="centre", weight=0.14)
    text(m, ["THE AGENT AND THE KEY"], W / 2, 318, 84, 6991, align="centre", weight=0.15)
    text(m, ["a true and improving history of Randolph station, in twelve pictures"], W / 2, 384, 30, 6992, align="centre")
    ornament_rule(m, 140, W - 140, 192, 6993)
    boxes = []
    for i in range(upto):
        col, row = i % 3, i // 3
        x0, y0 = COLX[col], ROW0 + row * ROWH
        pic = picture(i, np.zeros((PH, PW, 3), np.float32) + 238, coloured=row < colour_rows)
        pic = cv2.resize(pic, (CW, CH), interpolation=cv2.INTER_AREA)
        sub = sheet[y0:y0 + CH, x0:x0 + CW]
        pa = 0.92                                                   # the plate printed into the sheet's own grain
        sheet[y0:y0 + CH, x0:x0 + CW] = sub * (pic / 238.0) * pa + sub * (1 - pa)
        boxes.append((x0, y0, x0 + CW, y0 + CH))
        boxes.append((x0 - 9, y0 - 9, x0 + CW + 9, y0 + CH + 9))
        lines = wrap(VERSES[i], VCAP, CW - 10)
        assert len(lines) <= 4, (i, lines)
        for k, ln in enumerate(lines):
            text(m, [ln], x0 + CW / 2, y0 + CH + 50 + k * 38, VCAP, 7010 + 10 * i + k, align="centre")
        text(m, [f"{i + 1}."], x0 + 10, y0 + 34, 26, 7200 + i)
    yb = ROW0 + 4 * ROWH + 4
    ornament_rule(m, 140, W - 140, yb, 6994)
    text(m, ["Plain one penny, coloured twopence.  Printed for the station agents of Vermont."], W / 2, yb + 58, 26,
         6995, align="centre")
    penlib.ink_onto(sheet, m, INK)
    bm = np.zeros((H, W), np.uint8)
    for k, b in enumerate(boxes):
        bm = np.maximum(bm, penlib.border_mask((H, W), [b], 4 if k % 2 == 0 else 2, 6996 + k))
    penlib.ink_onto(sheet, bm, INK)
    return sheet


def creases(sheet, cx, cy):
    """the creases of a sheet sold folded in four: a valley down the middle and a ridge across"""
    x = np.arange(W, dtype=np.float32)[None, :] - cx
    y = np.arange(H, dtype=np.float32)[:, None] - cy
    sv = 1 - 0.12 * np.exp(-(x / 6) ** 2) - 0.035 * np.exp(-((x - 26) / 40) ** 2) + 0.02 * np.exp(-((x + 24) / 30) ** 2)
    sh = 1 + 0.035 * np.exp(-((y + 10) / 8) ** 2) - 0.09 * np.exp(-((y - 6) / 7) ** 2) - 0.03 * np.exp(-((y - 40) / 50) ** 2)
    shade = sv * sh * np.where(x > 0, 0.975, 1.0) * np.where(y > 0, 0.985, 1.0)
    sheet *= shade[..., None]


def build(colour_rows=4, extent="full", upto=12):
    page = cv2.GaussianBlur(k11.wood(), (0, 0), 1.6)
    sheet = sheet_build(colour_rows, upto)
    creases(sheet, W / 2, H / 2)
    x0, y0, x1, y1 = 52, 40, W - 52, H + 100
    if extent == "quarter":          # still folded in four: only the top-left quarter lies uppermost
        x1, y1 = W / 2 + 2, H / 2 + 2
    elif extent == "half":           # opened once: the top half
        y1 = H / 2 + 2
    Ms = cv2.getRotationMatrix2D((W / 2, H / 2), 0.3, 1.0)
    sh = cv2.warpAffine(sheet, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mk = np.zeros((H, W), np.uint8)
    cv2.rectangle(mk, (int(x0), int(y0)), (int(x1), int(y1)), 255, -1)
    mk = cv2.warpAffine(mk, Ms, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, mk, off=10, blur=12, opacity=0.5 if extent == "full" else 0.65)
    a = mk.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    page = cv2.GaussianBlur(page, (0, 0), 0.5)
    page = np.clip(np.round(page), 0, 255).astype(np.uint8)
    pen99.folio(page, N, TITLE)
    return page


def main():
    page = build()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90)
    print("jpeg", OUT_JPG.stat().st_size)
    if "--page-only" in sys.argv:
        return
    # the sheet unfolded on the table, then hand-coloured row by row
    frames = [build(0, "quarter"), build(0, "half"), build(0), build(1), build(2), build(3), page]
    print("beats", save_beats(N, frames))


if __name__ == "__main__":
    main()
