"""Page 80 Fold-in (formal / Oulipian rule; medium: busch-fold).

Folding the page along its marked lines hides the interruption and joins departure to cupboard, making a story in
which he remembers. The sheet is ruled into three upright strips by two dashed fold lines A and B. Unfolded, every
tier reads across all three strips and keeps the canon (E0-E5, the four lines, key on its hook, door shut). Folded
back so that A meets B, the middle strip (the lady, the clock, the three lines, the forgetting) is hidden, and the
outer strips join: the tier captions, written so that both readings are grammatical, close up into 'So off he goes
for the key.' / 'Across the office he goes, and on he goes, to the cupboard.' / 'He opens it, sees the key, and
takes it.'; the headline 'WHAT HE CAME FOR, HE FORGETS' closes up into 'WHAT HE GETS'; and in the last tier his
reaching hand (stopped short by the width of the hidden strip) meets the key's bow on the cupboard door.
Busch-fold kit (build/p59_once_upon.py, p39_meanwhile.py, p11_station_cat.py, p69_picture_sheet.py): the agent = the
les-caids porter cutout (Busch 1865, Max und Moritz plate 31, PD), the stranger = Helene (Busch 1872, PD) behind the
ticket glass; the les-caids vintage paper (CC BY 2.0) on the wood table (CC0); the ink set, the reaching arm and
hand, the key, the fold marks and all lettering HANDMADE (shared pen hand).
Run: python3 -I p80_fold_in.py [beats]
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
import p69_picture_sheet as S69  # noqa: E402
from b1m2 import save_page, save_beats, wrap  # noqa: E402

W, H = pen99.PAGE_W, pen99.PAGE_H
N, PID, TITLE = 80, "fold-in", "Fold-in"
INK = F.INK
XA, XB = 770, 1430                 # the fold lines (page x); the hidden strip is XA..XB
OX = 110                           # tier canvas x origin on the page
TA, TB = XA - OX, XB - OX          # fold lines in tier coords (660, 1320)
TW, TH, FLOOR = 1980, 500, F.FLOOR  # tier canvas; F.FLOOR = 450
TIER_Y = (450, 1160, 1870)
CAP, LH = 30, 43

Q, A, T, FG = (["Pardon me —", "have you the", "right time?"], ["Ten past four,", "by the clock."], ["Much obliged!"],
               ["Well, here I am...", "and what for?"])

# captions: (L text on the first row, M rows, R text on the last row)
CAPS = [
    ("The memo: SERVICE door, 4:15. So", ["up he gets, and"], "off he goes for the key."),
    ("Across the office he goes, and", ["a lady at the window asks the time;", "he looks at the clock and tells her;",
                                        "she thanks him and goes, and"], "on he goes, to the cupboard."),
    ("He opens it, sees the key, and", ["stands there, pencil to his chin...", "The key stays on its hook; the",
                                        "SERVICE door stays shut. Nobody"], "takes it."),
]


def width_of(lines, cap, seed, weight=0.13):
    return pen99.letter(lines, cap, seed, weight=weight).shape[1] - 1.2 * cap


def text_right(m, s, xr, y, cap, seed, weight=0.13):
    text(m, [s], xr - width_of([s], cap, seed, weight), y, cap, seed, weight=weight)


# ------------------------------------------------------------------ pieces
def porter_at(c, x, s=0.78, flip=False, deg=0.0):
    F.pieces()
    Ma = affine(M39.PORTER_FEET, (x, FLOOR + 30), s, deg=deg, flip=flip)
    a = F.lay(c, F.PORTER, Ma)
    return Ma, a


def floor_line(m, seed, x0=0, x1=TW):
    line(m, [(x0, FLOOR), (x1, FLOOR)], 6, seed)
    line(m, [(x0, 330), (x1, 330)], 2.5, seed + 1)
    hatch(m, x0, FLOOR + 6, x1, TH, 44, 2, seed + 2, ang=-20)


def big_key(c, hx, hy, seed):
    """the brass key on its hook (bow, shaft, bit), brass wash under the ink, tag hung to its LEFT on a string"""
    r = 30
    wash = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(wash, (int(hx), int(hy + 46)), r, 255, -1, cv2.LINE_AA)
    cv2.rectangle(wash, (int(hx - 7), int(hy + 72)), (int(hx + 7), int(hy + 230)), 255, -1)
    cv2.rectangle(wash, (int(hx - 34), int(hy + 190)), (int(hx), int(hy + 230)), 255, -1)
    wa = (cv2.GaussianBlur(wash, (0, 0), 1.2).astype(np.float32) / 255 * 0.85)[..., None]
    c[:] = c * (1 - wa) + np.array([214, 168, 62], np.float32) * wa
    m = np.zeros(c.shape[:2], np.uint8)
    line(m, [(hx + 10, hy - 22), (hx, hy - 8), (hx, hy + 12), (hx - 6, hy + 16)], 6, seed)        # hook
    line(m, ellipse_pts(hx, hy + 46, r, r), 6, seed + 1)
    line(m, ellipse_pts(hx, hy + 46, 11, 11), 3.5, seed + 2)
    line(m, [(hx - 7, hy + 74), (hx - 7, hy + 230)], 5, seed + 3)
    line(m, [(hx + 7, hy + 74), (hx + 7, hy + 230)], 5, seed + 4)
    line(m, [(hx - 7, hy + 190), (hx - 34, hy + 190), (hx - 34, hy + 204), (hx - 20, hy + 204), (hx - 20, hy + 216),
             (hx - 34, hy + 216), (hx - 34, hy + 230), (hx + 7, hy + 230)], 5, seed + 5)
    tx, ty = hx - 150, hy + 96
    line(m, [(hx - 16, hy + 64), (tx + 112, ty + 4)], 2.2, seed + 6)
    tag = np.zeros(c.shape[:2], np.uint8)
    poly = [(tx, ty), (tx + 116, ty + 4), (tx + 114, ty + 46), (tx - 2, ty + 42)]
    cv2.fillPoly(tag, [np.int32(poly)], 255, cv2.LINE_AA)
    ta = tag.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - ta) + np.array([246, 243, 234], np.float32) * ta
    line(m, poly + [poly[0]], 3, seed + 7)
    text(m, ["SERVICE"], tx + 58, ty + 34, 20, seed + 8, align="centre", weight=0.17)
    penlib.ink_onto(c, m, INK)


def reaching_arm(c, shoulder, seed):
    """HANDMADE ink: a sleeve from his shoulder, and an open hand whose fingertips end exactly at fold line B"""
    sx, sy = shoulder
    wx, wy = TB + 96, 258
    m = np.zeros(c.shape[:2], np.uint8)
    paper = np.zeros(c.shape[:2], np.uint8)
    up = [(sx, sy - 24), ((sx + wx) / 2, (sy + wy) / 2 - 26), (wx, wy - 20)]
    lo = [(wx, wy + 20), ((sx + wx) / 2, (sy + wy) / 2 + 26), (sx, sy + 28)]
    cv2.fillPoly(paper, [np.int32(up + lo)], 255, cv2.LINE_AA)
    # the hand: palm, thumb above, three fingers curling round toward the fold
    hand = [(wx + 4, wy - 22), (wx - 30, wy - 32), (TB + 30, wy - 52), (TB + 6, wy - 48), (TB + 2, wy - 40),
            (TB + 34, wy - 30), (TB + 22, wy - 22), (TB + 1, wy - 18), (TB + 1, wy - 8), (TB + 26, wy - 6),
            (TB + 1, wy + 4), (TB + 2, wy + 14), (TB + 28, wy + 12), (TB + 8, wy + 22), (TB + 12, wy + 32),
            (wx - 30, wy + 30), (wx + 4, wy + 22)]
    cv2.fillPoly(paper, [np.int32(hand)], 255, cv2.LINE_AA)
    pa = paper.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - pa) + np.array([244, 242, 236], np.float32) * pa
    line(m, up, 4.5, seed)
    line(m, lo, 4.5, seed + 1)
    line(m, [(wx + 4, wy - 24), (wx + 8, wy + 24)], 5, seed + 2)          # the cuff
    line(m, [(wx - 14, wy - 26), (wx - 10, wy + 24)], 2.5, seed + 3)
    line(m, hand, 3.5, seed + 4, tremor=0.3)
    for k in range(4):                                                     # sleeve hatching
        x = sx - 40 - k * 46
        y = sy + (wy - sy) * (sx - x) / (sx - wx)
        line(m, [(x, y - 18), (x - 16, y + 18)], 2, seed + 10 + k)
    penlib.ink_onto(c, m, INK)
    return (TB + 2, wy - 8)


def balloon(c, lines, cap, centre, tip, seed):
    F.balloon(c, lines, cap, centre, tip, seed)


# ------------------------------------------------------------------ the three tiers (HANDMADE ink + Busch cutouts)
def tier(k):
    c = np.zeros((TH, TW, 3), np.float32) + 238
    m = np.zeros((TH, TW), np.uint8)
    seed = 8000 + 101 * k
    floor_line(m, seed)
    info = {}
    if k == 0:      # E0: L the desk and memo; M the clock on the wall; R he walks off for the key
        line(m, [(90, 300), (420, 300)], 7, seed + 10)
        line(m, [(100, 318), (420, 318)], 3, seed + 11)
        line(m, [(110, 318), (110, FLOOR)], 6, seed + 12)
        line(m, [(410, 318), (410, FLOOR)], 6, seed + 13)
        hatch(m, 116, 322, 404, FLOOR - 4, 18, 2, seed + 14, ang=-80)
        M39.clock(m, 990, 120, 44, seed + 15)
        penlib.ink_onto(c, m, INK)
        F.memo_slip(c, [(160, 300), (176, 214), (360, 222), (356, 300)], seed + 20, cap=20)
        porter_at(c, 470, flip=True, deg=4)
        porter_at(c, 1640, flip=False, deg=-4)
    elif k == 1:    # L he crosses; M the window: question, answer under the clock, thanks; R on to the cupboard
        F.ticket_window(m, seed + 10, x0=700, x1=960, y0=236, y1=400)
        M39.cupboard(m, seed + 12, x0=1760, x1=1900, y0=110, y1=FLOOR, open_=False)
        M39.clock(m, 1262, 92, 32, seed + 14)
        penlib.ink_onto(c, m, INK)
        F.window_sign(c, seed + 16, x0=700, x1=960, y=206)
        F.pieces()
        glass = np.zeros((TH, TW), np.float32)
        glass[254:382, 718:942] = 1
        F.lay(c, F.HELENE, affine(M39.HEL_HAND, (935, 322), 0.40), clip=glass)
        Ma, _ = porter_at(c, 1150, s=0.58, flip=True)
        porter_at(c, 330, flip=False, deg=-3)
        porter_at(c, 1560, flip=False, deg=-3)
        mouth = F.pt(Ma, M39.PORTER_MOUTH)
        balloon(c, Q, 24, (800, 76), (850, 270), seed + 30)
        balloon(c, A, 24, (1085, 66), (mouth[0] - 4, mouth[1]), seed + 31)
        balloon(c, T, 24, (1035, 186), (905, 290), seed + 32)
    else:           # L the open cupboard door, the key on its hook; M the cupboard's dark inside, the forgetting;
        #             R the agent, pencil to chin, his hand out toward the key; the SERVICE door, shut
        leaf = [(468, 104), (TA - 6, 58), (TA - 6, FLOOR - 4), (468, FLOOR - 30)]
        pm = np.zeros((TH, TW), np.uint8)
        cv2.fillPoly(pm, [np.int32(leaf)], 255, cv2.LINE_AA)
        pa = pm.astype(np.float32)[..., None] / 255
        c[:] = c * (1 - pa) + np.array([228, 222, 208], np.float32) * pa
        line(m, leaf + [leaf[0]], 6, seed + 10)
        line(m, [(496, 140), (TA - 30, 104), (TA - 30, 250), (496, 262), (496, 140)], 2.5, seed + 11)
        line(m, [(496, 300), (TA - 30, 296), (TA - 30, FLOOR - 40), (496, FLOOR - 56), (496, 300)], 2.5, seed + 12)
        # the cupboard: jambs at the fold (left) and at x 1020, dark inside with shelves, all in the hidden strip
        line(m, [(TA + 4, 58), (1020, 58), (1020, FLOOR)], 7, seed + 13)
        line(m, [(TA + 4, 58), (TA + 4, FLOOR)], 7, seed + 14)
        hatch(m, TA + 10, 64, 1014, FLOOR - 4, 9, 2, seed + 15, ang=-70)
        for yy in (190, 330):
            line(m, [(TA + 10, yy), (1014, yy)], 5, seed + 16 + yy)
        penlib.ink_onto(c, m, INK)
        F.service_door(c, seed + 20, x0=1790, x1=1930, y0=80)
        big_key(c, TA - 34, 204, seed + 30)            # bow's outer edge (r 30 + pen) ends at fold line A
        Ma, _ = porter_at(c, 1610, flip=True, deg=2)
        pn = np.zeros((TH, TW), np.uint8)
        line(pn, [F.pt(Ma, (M39.PORTER_HAND[0] + 2, M39.PORTER_HAND[1] - 4)),
                  F.pt(Ma, (M39.PORTER_CHIN[0] + 4, M39.PORTER_CHIN[1] + 4))], 8, seed + 40, tremor=0.2)
        penlib.ink_onto(c, pn, INK)
        tip = reaching_arm(c, F.pt(Ma, (236, 236)), seed + 50)
        info["fingertips"] = tip
        # the forgetting, inside the hidden strip, its tail pointing out toward him
        balloon(c, FG, 30, (1100, 92), (TB - 14, 150), seed + 60)
    return c, info


# ------------------------------------------------------------------ the sheet
def sheet_build():
    sheet = k11.paper()
    sheet = 236 + cv2.GaussianBlur(sheet - 238, (0, 0), 2.4) * 0.85
    sheet *= np.array([1.0, 0.985, 0.95], np.float32)
    m = np.zeros((H, W), np.uint8)
    # head: L title | M the question | R the instructions
    text(m, ["FOLD-IN"], 150, 270, 104, 8001, weight=0.16)
    text(m, ["a story in three strips"], 156, 330, 28, 8002)
    q = wrap("What would happen if nothing came between him and the key?", 30, XB - XA - 60)
    text(m, q, (XA + XB) / 2, 200, 30, 8003, align="centre")
    ins = wrap("Fold the page back along line A, then bring A across to meet line B.", 28, 2050 - XB - 40)
    for i, ln in enumerate(ins):
        text(m, [ln], XB + 30, 200 + i * 40, 28, 8004 + i)
    # the headline that closes up: WHAT HE | CAME FOR, HE FOR | GETS
    hc, hy = 62, 410
    text_right(m, "WHAT HE", XA - 34, hy, hc, 8010, weight=0.16)
    text_right(m, "CAME FOR, HE FOR", XB - 1, hy, hc, 8011, weight=0.16)
    text(m, ["GETS"], XB + 1, hy, hc, 8012, weight=0.16)
    infos = []
    for k, ty in enumerate(TIER_Y):
        pic, info = tier(k)
        info["fingertips_page"] = (info["fingertips"][0] + OX, info["fingertips"][1] + ty) if "fingertips" in info else None
        infos.append(info)
        sub = sheet[ty:ty + TH, OX:OX + TW]
        pa = 0.92
        sheet[ty:ty + TH, OX:OX + TW] = sub * (pic / 238.0) * pa + sub * (1 - pa)
        bm = penlib.border_mask((H, W), [(OX, ty, OX + TW, ty + TH)], 4, 8020 + k)
        penlib.ink_onto(sheet, bm, INK)
        lt, mids, rt = CAPS[k]
        y0 = ty + TH + 52
        text_right(m, lt, XA - 12, y0, CAP, 8030 + 10 * k)
        for i, ln in enumerate(mids):
            text(m, [ln], XA + 14, y0 + i * LH, CAP, 8031 + 10 * k + i)
        text(m, [rt], XB + 12, y0 + (len(mids) - 1) * LH, CAP, 8039 + 10 * k)
    # foot
    text(m, ["Fold so that A meets B."], 150, 2650, 30, 8060)
    text(m, ["Unfolded, it is what happened."], (XA + XB) / 2, 2650, 28, 8061, align="centre")
    text(m, ["Folded, it is what he came for."], XB + 30, 2650, 30, 8062)
    penlib.ink_onto(sheet, m, INK)
    # the fold lines: dashed, lettered A and B top and bottom, with small fold arrows
    fm = np.zeros((H, W), np.uint8)
    for x in (XA, XB):
        for y in range(120, 2700, 46):
            line(fm, [(x, y), (x, y + 26)], 3, 8070 + y + x, tremor=0.1)
    for x, lab in ((XA, "A"), (XB, "B")):
        for y in (90, 2730):
            text(fm, [lab], x, y + 18, 34, 8080 + y + x, align="centre", weight=0.18)
    line(fm, [(XA + 30, 2706), (XB - 30, 2706)], 2.5, 8090)
    line(fm, [(XB - 52, 2694), (XB - 30, 2706), (XB - 52, 2718)], 2.5, 8091)
    penlib.ink_onto(sheet, fm, np.array([150, 40, 32], np.float32))
    return sheet, infos


def on_table(sheet, fold=0.0):
    """the sheet on the les-caids table; fold 0..1 = the middle strip folding back (A travelling to B)."""
    page = cv2.GaussianBlur(k11.wood(), (0, 0), 1.6)
    x0, y0, x1, y1 = 52, 40, W - 52, H + 100
    mk = np.zeros((H, W), np.float32)
    mk[y0:y1, x0:x1] = 1
    if fold <= 0:
        sh, mk2 = sheet, mk
    else:
        th = fold * math.pi / 2
        hw = (XB - XA) / 2
        w2 = hw * math.cos(th)
        shift = 2 * hw - 2 * w2
        sh = np.zeros_like(sheet)
        mk2 = np.zeros((H, W), np.float32)
        sh[:, :XA] = sheet[:, :XA]
        mk2[:, :XA] = mk[:, :XA]
        iw = max(1, int(round(w2)))
        for half, (a, b, shade) in enumerate(((XA, XA + int(hw), 1 - 0.38 * math.sin(th)),
                                              (XA + int(hw), XB, 1 - 0.12 * math.sin(th)))):
            if w2 >= 1:
                strip = cv2.resize(sheet[:, a:b], (iw, H), interpolation=cv2.INTER_AREA)
                ms = cv2.resize(mk[:, a:b], (iw, H), interpolation=cv2.INTER_AREA)
                g = np.linspace(1, shade, iw)[None, :, None] if half == 0 else np.linspace(shade, 1, iw)[None, :, None]
                xs = XA + half * iw
                sh[:, xs:xs + iw] = strip * g
                mk2[:, xs:xs + iw] = ms
        rx = int(round(XB - shift))
        n = W - XB
        sh[:, rx:rx + n] = sheet[:, XB:]
        mk2[:, rx:rx + n] = mk[:, XB:]
        sh[:, rx - 2:rx + 2] *= 0.8
    penlib.shadow_onto(page, (mk2 * 255).astype(np.uint8), off=10, blur=12, opacity=0.5)
    a = mk2[..., None]
    out = page * (1 - a) + sh * a
    return cv2.GaussianBlur(out, (0, 0), 0.5)


if __name__ == "__main__":
    sheet, infos = sheet_build()
    page = on_table(sheet)
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, [i.get("fingertips_page") for i in infos])
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for f in (0.0, 0.3, 0.55, 0.75, 0.9, 1.0):
            p = np.clip(np.round(on_table(sheet, f)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        save_beats(N, frames)
