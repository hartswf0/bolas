"""Page 59 Once upon a time (genre; medium: busch-fold).

A fairy tale: the forbidden door, the enchanted key, the stranger as a fairy who takes his memory with a
question. A printed picture-book spread on the les-caids tabletop (vintage paper CC BY 2.0, wood CC0), folded
down the middle like a booklet and opened again; six pictures in two columns, each over a passage of tale prose,
the first beginning 'Once upon a time' under a large ornamented initial.
The agent = the les-caids porter cutout (Busch 1865, Max und Moritz plate 31, PD) cut round his figure (p39's
cut); the stranger = Helene (Busch 1872, Die fromme Helene, Werke v2 p 246, PD) with p39's HANDMADE cloche,
and here HANDMADE fairy's wings and a star wand drawn onto the sheet behind and beside her. The set (desk,
memo, window, clock at 4:10, cupboard, key with its enchantment rays, the SERVICE door), sparkles, the little
memo carried off by the fairy, all HANDMADE ink in code; lettering in the shared pen hand.
Run: python3 -I p59_once_upon.py [--page-only]
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
from p11_station_cat import line, hatch, text, ellipse_pts, paste, affine  # noqa: E402
import p39_meanwhile as M39  # noqa: E402
from b1m2 import wrap  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
N, PID, TITLE = 59, "once-upon-a-time", "Once upon a time"
INK = np.array([20, 19, 18], np.float32)
OUT_JPG = ROOT / "assets/pages/99-ways" / f"{N}-{PID}.jpg"
OUT_PNG = ROOT / "films/sources/99-ways/masters" / f"{N}-{PID}.png"
BEATS = ROOT / "films/sources/99-ways/beats" / f"{N}"

PW, PH = 930, 500                  # picture size
COLX = (125, 1145)                 # two columns; the fold runs at x = 1100
FOLD_X = W // 2
ROWY = (300, 1110, 1920)           # picture tops
TXT_H = 250                        # prose under each picture
FLOOR = 450
BAL3 = (556, 46)
P3_X, P3_S, P3_DEG = 700, 0.76, 2
ST6_X, ST6_DEG = 455, 9          # picture 6: the agent upright before the cupboard
M39.PW = PW                         # p39's key/hook helpers size their paper to the picture width

PROSE = [
    "in a little station among the green hills, there lived an agent who kept the hours. One day a memo came: "
    "at a quarter past four he must open the forbidden SERVICE door, and the key to it lay in the cupboard.",
    "So he rose and set out across the office. But at the little window there appeared a fairy in a travelling "
    "hat, and she put to him a question, as fairies will:",
    "He looked up at the great clock on the wall, and because he was an honest man, he answered her truly:",
    "\"Much obliged!\" said the fairy, and was gone in a glitter; and with her, though he never knew it, flew "
    "the thing he had set out to do.",
    "He came to the cupboard and opened it, and there on its hook hung the enchanted key, shining in the dark.",
    "But the spell was cast. He stood before it with his pencil to his chin and asked himself what he had come "
    "for. And the key hangs there still, and the SERVICE door is shut to this day.",
]


# ------------------------------------------------------------------ pieces (p39's cuts)
PORTER = HELENE = None


def pieces():
    global PORTER, HELENE
    if PORTER is None:
        PORTER, HELENE = M39.porter_piece(), M39.helene_piece()


def lay(c, piece, M, clip=None):
    g, a = piece
    return paste(c, g, a, M, clip=clip, margin=6)


def pt(M, p):
    return M39.pt(M, p)


def balloon(c, lines, cap, centre, tip, seed):
    lines = [pen99.clean(l) for l in lines]
    b = penlib.balloon_piece(lines, cap, (tip[0] - centre[0], tip[1] - centre[1]), seed, tail_w=0.26, bend=0.08)
    penlib.lay_balloon(c, b, centre)


# ------------------------------------------------------------------ HANDMADE ink set
def room(m, seed):
    line(m, [(0, FLOOR), (PW, FLOOR)], 6, seed)
    line(m, [(0, 330), (PW, 330)], 2.5, seed + 1)
    hatch(m, 0, FLOOR + 6, PW, PH, 44, 2, seed + 2, ang=-20)


def star(m, cx, cy, r, seed, w=2.5):
    """a four-pointed sparkle"""
    line(m, [(cx - r, cy), (cx + r, cy)], w, seed, tremor=0.1)
    line(m, [(cx, cy - r), (cx, cy + r)], w, seed + 1, tremor=0.1)
    line(m, [(cx - r * 0.45, cy - r * 0.45), (cx + r * 0.45, cy + r * 0.45)], w * 0.6, seed + 2, tremor=0.1)
    line(m, [(cx - r * 0.45, cy + r * 0.45), (cx + r * 0.45, cy - r * 0.45)], w * 0.6, seed + 3, tremor=0.1)


def sparkles(m, pts, seed):
    for k, (x, y, r) in enumerate(pts):
        star(m, x, y, r, seed + 5 * k)


def wings(c, at, s, seed):
    """HANDMADE fairy's wings: two pale leaf shapes with ink veins, laid on the sheet behind her"""
    x, y = at
    mk = np.zeros(c.shape[:2], np.uint8)
    ink = np.zeros(c.shape[:2], np.uint8)
    for k, (ang, L, Wd) in enumerate(((-130, 1.0, 0.42), (-165, 0.8, 0.36))):
        a = math.radians(ang)
        tip = (x + L * s * math.cos(a), y + L * s * math.sin(a))
        nrm = (-math.sin(a), math.cos(a))
        pts = []
        for t in np.linspace(0, 1, 24):
            wv = Wd * s * math.sin(math.pi * t) * (1.1 - 0.4 * t)
            pts.append((x + (tip[0] - x) * t + nrm[0] * wv, y + (tip[1] - y) * t + nrm[1] * wv))
        for t in np.linspace(1, 0, 24):
            wv = Wd * s * math.sin(math.pi * t) * (1.1 - 0.4 * t) * 0.7
            pts.append((x + (tip[0] - x) * t - nrm[0] * wv, y + (tip[1] - y) * t - nrm[1] * wv))
        cv2.fillPoly(mk, [np.int32(pts)], 255, cv2.LINE_AA)
        line(ink, pts + [pts[0]], 3, seed + 10 * k)
        line(ink, [(x, y), tip], 1.6, seed + 10 * k + 1)
        for f in (0.35, 0.6):
            q = (x + (tip[0] - x) * f, y + (tip[1] - y) * f)
            line(ink, [q, (q[0] + nrm[0] * Wd * s * 0.7, q[1] + nrm[1] * Wd * s * 0.7)], 1.4, seed + 10 * k + 2 + int(f * 10))
    a = (mk.astype(np.float32) / 255 * 0.85)[..., None]
    c[:] = c * (1 - a) + np.array([238, 240, 246], np.float32) * a
    penlib.ink_onto(c, ink, INK)


def wand(m, hand, seed, L=120, ang=-55):
    a = math.radians(ang)
    tip = (hand[0] + L * math.cos(a), hand[1] + L * math.sin(a))
    line(m, [hand, tip], 3.5, seed, tremor=0.2)
    star(m, tip[0], tip[1], 20, seed + 1, w=3.5)
    return tip


def ticket_window(m, seed, x0=40, x1=330, y0=110, y1=360):
    line(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 7, seed)
    line(m, [(x0 + 18, y0 + 18), (x1 - 18, y0 + 18), (x1 - 18, y1 - 18), (x0 + 18, y1 - 18), (x0 + 18, y0 + 18)], 3, seed + 1)
    line(m, [(x0 - 20, y1 + 16), (x1 + 20, y1 + 16)], 6, seed + 2)
    hatch(m, x0 - 20, y1 + 22, x1 + 20, FLOOR - 4, 16, 2, seed + 3, ang=-80)


def window_sign(c, seed, x0=40, x1=330, y=62):
    M39.caption  # noqa (kept for parity with p39's lettered boards)
    m = np.zeros(c.shape[:2], np.uint8)
    line(m, [(x0 + 30, y - 34), (x1 - 30, y - 34), (x1 - 30, y + 16), (x0 + 30, y + 16), (x0 + 30, y - 34)], 4, seed)
    text(m, ["TICKET OFFICE"], (x0 + x1) / 2, y + 6, 26, seed + 1, align="centre", weight=0.16)
    penlib.ink_onto(c, m, INK)


def service_door(c, seed, x0=780, x1=900, y0=120):
    m = np.zeros(c.shape[:2], np.uint8)
    line(m, [(x0, FLOOR), (x0, y0), (x1, y0), (x1, FLOOR)], 7, seed)
    line(m, [(x0 + 16, y0 + 150), (x1 - 16, y0 + 150), (x1 - 16, FLOOR - 20), (x0 + 16, FLOOR - 20), (x0 + 16, y0 + 150)], 3, seed + 1)
    cv2.circle(m, (int(x0 + 22), int(y0 + 200)), 7, 255, -1, cv2.LINE_AA)
    penlib.ink_onto(c, m, INK)
    bg = np.zeros(c.shape[:2], np.uint8)
    cv2.rectangle(bg, (x0 + 8, y0 + 40), (x1 - 8, y0 + 96), 255, -1)
    pa = bg.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - pa) + np.array([248, 246, 240], np.float32) * pa
    m3 = np.zeros(c.shape[:2], np.uint8)
    line(m3, [(x0 + 8, y0 + 40), (x1 - 8, y0 + 40), (x1 - 8, y0 + 96), (x0 + 8, y0 + 96), (x0 + 8, y0 + 40)], 3, seed + 2)
    text(m3, ["SERVICE"], (x0 + x1) / 2, y0 + 84, 28, seed + 3, align="centre", weight=0.17)
    penlib.ink_onto(c, m3, INK)


def cupboard(m, seed, x0=560, x1=700, y0=130, open_=False):
    M39.cupboard(m, seed, x0=x0, x1=x1, y0=y0, y1=FLOOR, open_=open_)


def memo_slip(c, poly, seed, cap=16, lines=("4:15 open", "SERVICE door.", "Key in cupb'd.")):
    slip = np.zeros(c.shape[:2], np.uint8)
    cv2.fillPoly(slip, [np.int32(poly)], 255, cv2.LINE_AA)
    penlib.shadow_onto(c, slip, off=4, blur=3, opacity=0.3)
    sa = slip.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - sa) + np.array([247, 246, 241], np.float32) * sa
    mm = np.zeros(c.shape[:2], np.uint8)
    line(mm, list(poly) + [poly[0]], 2.5, seed)
    if lines:
        cx = np.mean([p[0] for p in poly])
        cy = np.min([p[1] for p in poly])
        text(mm, list(lines), cx, cy + cap * 1.6, cap, seed + 1, align="centre", weight=0.17)
    penlib.ink_onto(c, mm, INK)


def enchant(m, centre, seed, r0=40, r1=80, n=12):
    cx, cy = centre
    for k in range(n):
        a = 2 * math.pi * k / n + 0.13
        line(m, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], 2.2, seed + k,
             tremor=0.2)


# ------------------------------------------------------------------ the six pictures
def picture(i, ground, st):
    pieces()
    c = ground.copy()
    seed = 5900 + i * 61
    m = np.zeros((PH, PW), np.uint8)
    room(m, seed)
    if i == 0:
        line(m, [(90, 300), (420, 300)], 7, seed + 10)                     # desk
        line(m, [(100, 318), (420, 318)], 3, seed + 11)
        line(m, [(110, 318), (110, FLOOR)], 6, seed + 12)
        line(m, [(410, 318), (410, FLOOR)], 6, seed + 13)
        hatch(m, 116, 322, 404, FLOOR - 4, 18, 2, seed + 14, ang=-80)
        cupboard(m, seed + 20)
    if i in (1, 2, 3):
        ticket_window(m, seed + 30)
    if i == 2:
        M39.clock(m, 560, 140, 52, seed + 40)
    if i in (4, 5):
        cupboard(m, seed + 50, x0=560, x1=700, open_=True)
    penlib.ink_onto(c, m, INK)
    if i in (1, 2, 3):
        window_sign(c, seed + 35)
    if i in (0, 5):
        service_door(c, seed + 60)
    if i == 0:
        memo_slip(c, [(170, 300), (186, 232), (330, 238), (330, 300)], seed + 70)
    if i in (4, 5):
        M39.key_on_hook(c, (590, 180), seed + 80)
        if i == 4:
            em = np.zeros((PH, PW), np.uint8)
            enchant(em, (590, 260), seed + 85, r0=70, r1=110)
            sparkles(em, [(520, 160, 14), (680, 210, 18), (660, 340, 12), (510, 320, 10)], seed + 88)
            penlib.ink_onto(c, em, INK)
    # the fairy (Helene, hatted, winged, with a star wand), seen through the ticket window glass
    if i in (1, 2):
        glass = np.zeros((PH, PW), np.float32)
        glass[128:342, 58:312] = 1
        g, a = HELENE
        Mh = affine(M39.HEL_HAND, (300, 250), 0.62)
        hd = pt(Mh, M39.HEL_HEAD)
        wings(c, (hd[0] - 50, hd[1] + 80), 210, seed + 90)
        c[:] = c * (1 - glass[..., None]) + c * glass[..., None]
        lay(c, HELENE, Mh, clip=glass)
        wm = np.zeros((PH, PW), np.uint8)
        wtip = wand(wm, pt(Mh, M39.HEL_HAND), seed + 95, L=90, ang=-70)
        if i == 1:
            sparkles(wm, [(wtip[0] + 40, wtip[1] + 10, 10), (wtip[0] - 10, wtip[1] - 40, 8), (wtip[0] + 70, wtip[1] + 60, 7)], seed + 97)
        penlib.ink_onto(c, wm, INK)
        head = (hd[0] + 10, hd[1] - 20)
    # the agent
    if i == 0:
        Ma = affine(M39.PORTER_FEET, (480, FLOOR + 30), 0.80, deg=4)
    elif i == 1:
        Ma = affine(M39.PORTER_FEET, (500, FLOOR + 30), 0.72, flip=True)          # turned to the window
    elif i == 2:
        Ma = affine(M39.PORTER_FEET, (P3_X, FLOOR + 30), P3_S, deg=P3_DEG, flip=True)  # head up to the clock
    elif i == 3:
        Ma = affine(M39.PORTER_FEET, (st.get("walk", 620), FLOOR + 30), 0.80)    # walks on, to the right
    elif i == 4:
        Ma = affine(M39.PORTER_FEET, (460, FLOOR + 30), 0.80)                    # arrives at the cupboard
    else:   # he stands before it: drawn upright, planted close, his face to the open cupboard and the key
        Ma = affine(M39.PORTER_FEET, (ST6_X, FLOOR + 30), 0.80, deg=ST6_DEG)
    lay(c, PORTER, Ma)
    if i == 5:
        pm = np.zeros((PH, PW), np.uint8)
        line(pm, [pt(Ma, (M39.PORTER_HAND[0] + 2, M39.PORTER_HAND[1] - 4)), pt(Ma, (M39.PORTER_CHIN[0] + 4, M39.PORTER_CHIN[1] + 4))],
             8, seed + 120, tremor=0.2)
        if st.get("cloud", True):   # a little cloud of nothing over his head
            mh = pt(Ma, (250, 30))
            sparkles(pm, [(mh[0] - 30, mh[1] - 10, 9), (mh[0] + 10, mh[1] - 34, 7)], seed + 125)
        penlib.ink_onto(c, pm, INK)
    if i == 3:   # vanished in a glitter; the little memo flies off with her through the window
        k = st.get("fly", 1.0)
        wm = np.zeros((PH, PW), np.uint8)
        sparkles(wm, [(130, 200, 22), (210, 160, 16), (250, 250, 12), (170, 290, 10), (90, 150, 9)], seed + 100)
        # a dotted trail from his head out to the window
        a0, a1 = np.array((620.0, 150.0)), np.array((170.0, 210.0))
        for t in np.linspace(0.05, 0.95 * k, max(2, int(14 * k))):
            p = a0 + (a1 - a0) * t
            p[1] -= 70 * math.sin(math.pi * t)
            cv2.circle(wm, (int(p[0]), int(p[1])), 4, 255, -1, cv2.LINE_AA)
        penlib.ink_onto(c, wm, INK)
        q = a0 + (a1 - a0) * (0.98 * k)
        q[1] -= 70 * math.sin(math.pi * 0.98 * k)
        memo_slip(c, [(q[0] - 38, q[1] - 22), (q[0] + 36, q[1] - 30), (q[0] + 40, q[1] + 18), (q[0] - 34, q[1] + 24)], seed + 105,
                  lines=())
    mouth = pt(Ma, M39.PORTER_MOUTH)
    if i == 1 and st.get("ask", True):
        balloon(c, ["Pardon me —", "have you the", "right time?"], 32, (560, 82), (head[0] + 20, head[1] + 10), seed + 130)
    if i == 2:
        balloon(c, ["Ten past four, by the clock."], 24, BAL3, mouth, seed + 130)   # above, clear of his head
    if i == 3:
        balloon(c, ["Much", "obliged!"], 36, (440, 400), (250, 300), seed + 130)
    if i == 5 and st.get("line", True):
        balloon(c, ["Well, here I am...", "and what for?"], 34, (212, 128), mouth, seed + 130)   # left, clear of his head
    return c


# ------------------------------------------------------------------ the spread
def initial_O(sheet, x, y, seed):
    """a HANDMADE ornamented initial: a boxed O with vine curls, drawn in ink"""
    m = np.zeros(sheet.shape[:2], np.uint8)
    s = 150
    line(m, [(x, y), (x + s, y), (x + s, y + s), (x, y + s), (x, y)], 5, seed)
    line(m, [(x + 10, y + 10), (x + s - 10, y + 10), (x + s - 10, y + s - 10), (x + 10, y + s - 10), (x + 10, y + 10)], 2, seed + 1)
    line(m, ellipse_pts(x + s / 2, y + s / 2, 46, 54), 13, seed + 2, tremor=0.2)
    for k, (cx, cy) in enumerate(((x + 26, y + 26), (x + s - 26, y + 26), (x + 26, y + s - 26), (x + s - 26, y + s - 26))):
        line(m, ellipse_pts(cx, cy, 10, 10, 0, 300), 2, seed + 5 + k)
        star(m, cx, cy, 6, seed + 20 + k, w=1.5)
    penlib.ink_onto(sheet, m, INK)
    return s


def build(upto=6, state=None):
    state = state or {}
    page = cv2.GaussianBlur(k11.wood(), (0, 0), 1.6)
    sheet = k11.paper()
    sheet = 238 + cv2.GaussianBlur(sheet - 238, (0, 0), 2.6) * 0.85
    boxes = []
    m = np.zeros((H, W), np.uint8)
    s0 = initial_O(sheet, 300, 92, 5992)
    text(m, ["nce upon a time..."], 300 + s0 + 30, 215, 92, 5990, weight=0.13)
    for i in range(upto):
        col, row = i % 2, i // 2
        x0, y0 = COLX[col], ROWY[row]
        sheet[y0:y0 + PH, x0:x0 + PW] = picture(i, sheet[y0:y0 + PH, x0:x0 + PW], state.get(i, {}))
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        ty = y0 + PH + 52
        tx = x0 + 6
        for k, ln in enumerate(wrap(PROSE[i], 31, PW - 30)):
            text(m, [ln], tx, ty + k * 48, 31, 6010 + 10 * i + k)
        if i == 5:
            text(m, ["THE END"], x0 + PW / 2, ty + 4 * 48 + 20, 44, 6099, align="centre", weight=0.15)
    penlib.ink_onto(sheet, m, INK)
    penlib.ink_onto(sheet, penlib.border_mask((H, W), boxes, 6, 5995), INK)
    pen99.folio(sheet, N, TITLE)
    # the fold: down the middle, like a booklet opened flat
    x = np.arange(W, dtype=np.float32)[None, :]
    d = x - FOLD_X
    shade = 1 - 0.15 * np.exp(-(d / 7) ** 2) - 0.04 * np.exp(-((d - 30) / 45) ** 2) + 0.02 * np.exp(-((d + 28) / 34) ** 2)
    shade = shade * np.where(d > 0, 0.965, 1.0)
    sheet *= shade[..., None]
    Ms = cv2.getRotationMatrix2D((W / 2, H / 2), 0.35, 1.0)
    sh = cv2.warpAffine(sheet, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mk = np.zeros((H, W), np.uint8)
    cv2.rectangle(mk, (58, 46), (W - 58, H + 100), 255, -1)
    mk = cv2.warpAffine(mk, Ms, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, mk, off=10, blur=12, opacity=0.5)
    a = mk.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    page = cv2.GaussianBlur(page, (0, 0), 0.55)
    return np.clip(np.round(page), 0, 255).astype(np.uint8)


def main():
    page = build()
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90)
    print("jpeg", OUT_JPG.stat().st_size)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    # the spell: the fairy asks; she vanishes and the memo flies off with her along the trail; then the blank
    seq = [dict(upto=2, state={1: {"ask": False}}), dict(upto=2), dict(upto=4, state={3: {"fly": 0.25, "walk": 560}}),
           dict(upto=4, state={3: {"fly": 0.6, "walk": 600}}), dict(upto=4), dict(upto=6, state={5: {"line": False, "cloud": False}}),
           dict(upto=6)]
    for j, s in enumerate(seq, 1):
        im = page if s == dict(upto=6) else build(**s)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
    print("beats", len(seq))


if __name__ == "__main__":
    main()
