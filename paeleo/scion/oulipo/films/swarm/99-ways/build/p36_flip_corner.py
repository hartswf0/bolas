"""Page 36 Flip corner (reader and object; medium: paper-hands).

A small flip sequence runs down the page's outer corner (page 36 is a verso: the outer edge is the left);
flipped, it animates the forgetting: his own paper hand rises toward the brass key on its hook, stops short,
hangs there, sinks away, and the pencil comes up instead; the key stays on its hook. Twelve numbered frames.
Beside it, the incident in seven lit sheets of the 99-ways-subjective lightbox (first-person views: the
agent's cut paper hands, set pieces cut sharp against the lit paper), and a vellum note pointing to the corner.
Reused HANDMADE code (imported): build/p28_dealt_cards.py (Card, lit paper, hand rig posing, window/cupboard/
SERVICE door sets, ANRC key on hook), which itself imports 99-ways-subjective lightbox.py and e4.py.
Run: python3 -I p36_flip_corner.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p28_dealt_cards as D
from p28_dealt_cards import Card, CW, CH, window_set, cupboard_set, service_door_set, key_on_hook

N, PID, TITLE = 36, "flip-corner", "Flip corner"
SHEET = pen99.sheet99()

# ---------------------------------------------------------------- layout
STRIP_X0, STRIP_X1 = 110, 400           # the flip strip on the outer (left) edge
NF = 12
FG = 14
FH = (2620 - (NF - 1) * FG) // NF       # 205
FW = int(round(FH * CW / CH))           # 282
MX0, MX1 = 450, 2090                    # main area
MCW = (MX1 - MX0 - 30) // 2             # 805
MCH = int(round(MCW * CH / CW))         # 585
MGY = (2620 - 4 * MCH) // 3


def mbox(i):
    r, c = i // 2, i % 2
    x0 = MX0 + c * (MCW + 30)
    y0 = 110 + r * (MCH + MGY)
    return x0, y0


# ---------------------------------------------------------------- the seven main sheets (first person)
def m1():   # E0 the memo in his hand at the desk
    c = Card(3611)
    c.rect(-10, 660, CW + 10, CH + 10, s=4)
    c.rect(820, 540, 900, 660, s=2)
    c.poly([(820, 540), (838, 514), (882, 514), (900, 540)], s=3)
    c.slip(300, 200, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 50, 3612, tilt=3)
    c.hand((330, 470), -48)
    return c


def m2():   # E0 he sets off: the cupboard and the SERVICE door ahead, his hand swinging low
    c = Card(3621)
    c.rect(-10, 720, CW + 10, CH + 10, s=1)
    cupboard_set(c, 300, 190, 250, 530, open_=False, seed=10)
    service_door_set(c, 680, 130, 240, 590, 30)
    c.hand((160, 760), -150)
    return c


def m3():   # E1 the question
    c = Card(3631)
    sill = window_set(c, 420, 90, 540, 680, 50)
    c.shapes(stranger(690, sill + 40, face=-1, scale=1.6, glove=True), layer="far", holes=False)
    c.balloon(["Pardon me —", "have you the", "right time?"], 52, (230, 250), (600, 300), 3632)
    return c


def m4():   # E2 the clock at 4:10; his answer
    c = Card(3641)
    c.shapes(clock(330, 260, 160, hh=4, mm=10, swing=-4))
    c.hand((470, 640), -70, pencil=120)
    c.balloon(["Ten past four,", "by the clock."], 52, (800, 220), (640, 790), 3642)
    return c


def m5():   # E3 the thanks; she turns away
    c = Card(3651)
    sill = window_set(c, 420, 90, 540, 680, 60)
    c.shapes(stranger(820, sill + 40, face=1, scale=1.35, tilt=6), layer="far", holes=False)
    c.balloon(["Much", "obliged!"], 54, (220, 230), (640, 330), 3652)
    return c


def m6():   # E4 the leaf swings open: the key on its hook
    c = Card(3661)
    c.rect(-10, 740, CW + 10, CH + 10, s=1)
    box, leaf = cupboard_set(c, 520, 120, 360, 620, open_=True, seed=70)
    key_on_hook(c, 700, 310, 0.31, 3662)
    c.hand((leaf[1][0] - 6, 250), -58)
    return c


def m7():   # E5 the forgetting: key on its hook, SERVICE door shut, pencil up toward his chin
    c = Card(3671)
    c.rect(-10, 740, CW + 10, CH + 10, s=1)
    cupboard_set(c, 160, 190, 320, 550, open_=True, seed=80)
    key_on_hook(c, 320, 350, 0.30, 3672)
    service_door_set(c, 820, 120, 220, 620, 90)
    c.hand((540, 680), -100, pencil=130)
    c.balloon(["Well, here I am...", "and what for?"], 50, (620, 150), (600, 800), 3673)
    return c


MAIN = [m1, m2, m3, m4, m5, m6, m7]

# ---------------------------------------------------------------- the flip frames: the hand that does not take the key
# (pinch target, hand angle, pencil length or None)
FLIP = [
    ((780, 1000), -120, None),
    ((740, 840), -118, None),
    ((700, 700), -116, None),
    ((650, 580), -114, None),
    ((604, 500), -112, None),     # stops just short of the key
    ((608, 508), -102, None),     # hangs there
    ((620, 540), -96, None),
    ((650, 610), -100, 70),       # the pencil comes up instead
    ((665, 680), -102, 110),
    ((665, 750), -104, 130),
    ((655, 850), -106, 130),
    (None, None, None),           # the key alone, on its hook
]
assert len(FLIP) == NF


def flip_card(k):
    c = Card(3700 + k * 3)
    c.rect(-10, 760, CW + 10, CH + 10, s=1)
    cupboard_set(c, 300, 60, 500, 700, open_=True, seed=3780)
    key_on_hook(c, 540, 300, 0.42, 3790)
    t, hd, pen = FLIP[k]
    if t is not None:
        c.hand(t, hd, pencil=pen)
    return c


CACHE = {}


def rendered(kind, k, size):
    key = (kind, k, size)
    if key not in CACHE:
        c = (MAIN[k] if kind == "m" else (lambda: flip_card(k)))()
        rgb = c.render()
        CACHE[key] = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
    return CACHE[key]


def lay_sheet(page, rgb, x0, y0, seed, lift=6):
    h, w = rgb.shape[:2]
    a = np.zeros(page.shape[:2], np.uint8)
    q = D.facet(D.dense_poly([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], 3.0), seed, 6, 12, 0.5)
    cv2.fillPoly(a, [np.int32(q * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(page, a, off=lift, blur=5, opacity=0.4)
    af = a.astype(np.float32)[..., None] / 255
    sub = np.zeros_like(page)
    sub[y0:y0 + h, x0:x0 + w] = rgb
    page[:] = page * (1 - af) + sub * af


def frame_no(page, k, x, y):
    m = letter_left([f"{k}"], 30, 3600 + k, weight=0.15)
    lm = np.zeros(page.shape[:2], np.uint8)
    blit_mask(lm, m, x, y)
    comp(page, lm, INK)


def build(n_main=7, strip=True):
    page = SHEET.copy()
    # the strip: frame k at the outer edge, numbered on the inner side
    if strip:
        for k in range(NF):
            y0 = 110 + k * (FH + FG)
            lay_sheet(page, rendered("f", k, (FW, FH)), STRIP_X0, y0, 3800 + k, lift=4)
            frame_no(page, k + 1, STRIP_X0 + FW + 4, y0 + FH // 2 - 30)
    for i in range(min(n_main, 7)):
        x0, y0 = mbox(i)
        lay_sheet(page, rendered("m", i, (MCW, MCH)), x0, y0, 3850 + i)
    if n_main >= 7:
        x0, y0 = mbox(7)
        slip(page, x0 + 20, y0 + 60, ["Flip the outer corner:", "the frames down the left edge,", "1 to 12. The hand goes up", "to the key... and comes", "away without it."], 44, 3890, paper=D.VELLUM, pad=(26, 20), tilt=-1.5)
    return page


def flip_view(k):
    """beat frame: flip frame k seen big, as the flipped corner shows it, numbered"""
    img = cv2.resize(SHEET, (960, 1242), interpolation=cv2.INTER_AREA).copy()
    c = flip_card(k).render()
    rgb = cv2.resize(c, (880, 640), interpolation=cv2.INTER_AREA)
    x0, y0 = 40, 240
    a = np.zeros(img.shape[:2], np.uint8)
    a[y0:y0 + 640, x0:x0 + 880] = 255
    penlib.shadow_onto(img, a, off=8, blur=6, opacity=0.45)
    img[y0:y0 + 640, x0:x0 + 880] = rgb
    m = letter_left([f"{k + 1}"], 54, 3600 + k, weight=0.15)
    lm = np.zeros(img.shape[:2], np.uint8)
    blit_mask(lm, m, 860, 900)
    comp(img, lm, INK)
    m = letter_left(["Flip corner", "36"], 30, 3990)
    lm = np.zeros(img.shape[:2], np.uint8)
    blit_mask(lm, m, 40, 1100)
    comp(img, lm, INK)
    return img


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "frame", FW, FH, "main", MCW, MCH, MGY)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [flip_view(k) for k in (0, 2, 4, 5, 7, 9, 10, 11)]
        save_beats(N, frames)
