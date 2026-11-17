"""99 ways, page 16 "Fewest marks" (reduction and expansion; medium: cut-paper).
Every figure and object is cut from the fewest pieces of flat paper that keep the incident readable, and the page
shows its own count: a parts strip at the head lays every figure out in its separate pieces with the number of pieces,
then six panels (E0-E5) assemble exactly those pieces. AGENT 4 (trousers, shirt-with-sleeves, waistcoat, head),
PENCIL 1, STRANGER 3 (coat, head, hat), CLOCK 3 (face, two hands), KEY 3 (hook, key, tag), CUPBOARD 2 (carcass, door),
SERVICE DOOR 2 (door, card), TICKET WINDOW 3 (glass, frame, sill), MEMO 1, DESK 1. Nothing has more than five.
Lettering (memo, tag, card, window, balloons) is the shared pen hand, not cut shapes. Ground: one wall and one floor
paper per panel. All HANDMADE cut paper (films/swarm/99-ways/kit/cutpaper99.py) on the LoC 1934 sheet.
Run: python3 -I p16_fewest_marks.py"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, ellipse, rect  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "fewest-marks"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/16-fewest-marks.jpg"
OUT_PNG = SRC / "masters/16-fewest-marks.png"
BEATS = SRC / "beats/16"
W, H = pen99.PAGE_W, pen99.PAGE_H

COL = dict(hair="#3b2a1e", head="#e4b896", shirt="#f3efe4", vest="#2a2420", trousers="#77695a", pencil="#e2b23a",
           hat="#6a2e27", herhead="#e0b08a", coat="#4a5d72",
           face="#f4ecd6", hand="#1b1715", frame="#5a3d26", glass="#bfd0cd", inside="#24211e", door="#a07b52",
           hook="#2c2017", key="#c9a040", tag="#f4ecd6", sdoor="#7d5a36", card="#fbf8ee", memo="#fbf8ee",
           desk="#5e3f26", wall="#e2d1aa", floor="#9c7a52")


# ------------------------------------------------------------------ geometry
def xf(poly, s=1.0, at=(0, 0), flip=False, rot=0.0, pivot=(0, 0)):
    """local -> canvas: rotate about pivot, mirror (x -> -x) if flip, scale, translate"""
    p = np.asarray(poly, np.float32) - np.float32(pivot)
    a = math.radians(rot)
    p = np.stack([p[:, 0] * math.cos(a) - p[:, 1] * math.sin(a), p[:, 0] * math.sin(a) + p[:, 1] * math.cos(a)], 1) + np.float32(pivot)
    if flip:
        p[:, 0] = -p[:, 0]
    return p * s + np.float32(at)


def outline(fill_fn, shape):
    """one cut outline from a union drawn by fill_fn(mask)"""
    u = np.zeros(shape, np.uint8)
    fill_fn(u)
    cs, _ = cv2.findContours(u, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)


def limb_poly(a, b, w0, w1):
    a, b = np.float32(a), np.float32(b)
    d = b - a
    ang = math.degrees(math.atan2(d[1], d[0]))
    ea = ellipse(a[0], a[1], w0 / 2, w0 / 2, ang + 90, ang + 270, 10)
    eb = ellipse(b[0], b[1], w1 / 2, w1 / 2, ang - 90, ang + 90, 10)
    return np.vstack([eb, ea])


def head_poly(rx=46, ry=56, cy=-524):
    """oval head with a nose on the +x side: the only facial mark, it says which way the head looks"""
    pts = []
    for t in np.linspace(0, 360, 64, endpoint=False):
        a = math.radians(t)
        if t < 4 or t > 330:          # the nose replaces this arc (angles measured with y down)
            continue
        pts.append((rx * math.cos(a), cy + ry * math.sin(a)))
    nose = [(rx * math.cos(math.radians(-30)), cy + ry * math.sin(math.radians(-30))),
            (rx + 16, cy + 10), (rx - 1, cy + 12)]
    # start after the nose (t=4) ... end before it (t=330) then the nose closes the outline
    return np.array(pts + nose, np.float32)


def hair_poly(rx=46, ry=56, cy=-524):
    """hair: a cap over the crown and the back of the head (the back is -x)"""
    outer = [((rx + 5) * math.cos(math.radians(t)), cy + (ry + 6) * math.sin(math.radians(t))) for t in np.linspace(150, 335, 30)]
    inner = [(rx * 0.62, cy - ry * 0.52), (rx * 0.1, cy - ry * 0.38), (-rx * 0.45, cy - ry * 0.18), (-rx * 0.62, cy + ry * 0.2),
             (-rx * 0.8, cy + ry * 0.5)]
    return np.array(outer + inner, np.float32)


# A piece: dict(name, poly (canvas px), col, holes, text=(lines, cap, centre, colour) | None)
def P(name, poly, col, holes=(), text=None, shadow=True):
    return dict(name=name, poly=np.asarray(poly, np.float32), col=col, holes=list(holes), text=text, shadow=shadow)


def lay(c, pieces, seed=0):
    for i, p in enumerate(pieces):
        c.piece(p["poly"], COL[p["col"]], holes=p["holes"], shadow=p["shadow"])
        if p["text"]:
            lines, cap, ctr, colour = p["text"]
            c.ink_letters(lines, cap, ctr, seed + i, colour=colour)


ARMS = {  # (back arm, front arm) from the shoulders; the front hand holds the pencil
    "stand": ([(-68, -440), (-88, -350), (-92, -268)], [(68, -440), (88, -350), (92, -268)]),
    "walk": ([(-68, -440), (-104, -360), (-126, -285)], [(68, -440), (104, -360), (128, -290)]),
    "rise": ([(-68, -440), (-96, -350), (-70, -278)], [(68, -440), (112, -352), (176, -300)]),
    "reach": ([(-68, -440), (-90, -350), (-96, -270)], [(68, -440), (162, -418), (262, -402)]),
    "chin": ([(-68, -440), (-88, -350), (-92, -268)], [(68, -440), (114, -346), (46, -452)]),
}
LEGS = {"stand": [(-62, -272), (62, -272), (64, 0), (14, 0), (4, -160), (-4, -160), (-14, 0), (-64, 0)],
        "walk": [(-62, -272), (62, -272), (98, 0), (50, 0), (0, -176), (-44, 0), (-96, 0)]}
VEST = [(-78, -462), (-26, -464), (0, -392), (26, -464), (78, -462), (80, -262), (0, -246), (-80, -262)]
TORSO = [(-80, -470), (80, -470), (84, -262), (-84, -262)]


def agent(shape, s, at, flip=False, arms="stand", legs="stand", head_rot=0.0):
    """AGENT: 5 pieces + PENCIL: 1 piece. Returns (pieces, mouth point)."""
    back, front = ARMS[arms]

    def shirt(u):
        cv2.fillPoly(u, [np.int32(xf(TORSO, s, at, flip))], 255)
        for arm in (back, front):
            q = xf(arm, s, at, flip)
            for a, b in zip(q[:-1], q[1:]):
                cv2.line(u, tuple(int(v) for v in a), tuple(int(v) for v in b), 255, max(3, int(36 * s)))
            cv2.circle(u, tuple(int(v) for v in q[-1]), max(2, int(18 * s)), 255, -1)
    hx, hy = front[-1]
    pen_l = [(hx - 2, hy + 10), (hx + 4, hy - 66)] if arms == "chin" else [(hx + 2, hy + 16), (hx + 14, hy - 58)]
    q = xf(pen_l, s, at, flip)
    pieces = [P("trousers", xf(LEGS[legs], s, at, flip), "trousers"),
              P("shirt", outline(shirt, shape), "shirt"),
              P("waistcoat", xf(VEST, s, at, flip), "vest"),
              P("head", xf(head_poly(), s, at, flip, rot=head_rot, pivot=(0, -470)), "head"),
              P("hair", xf(hair_poly(), s, at, flip, rot=head_rot, pivot=(0, -470)), "hair"),
              P("pencil", limb_poly(q[0], q[1], max(5, 12 * s), max(3, 7 * s)), "pencil")]
    mouth = xf([(30, -500)], s, at, flip, rot=head_rot, pivot=(0, -470))[0]
    return pieces, mouth


def clip_convex(poly, box):
    """Scissor a convex piece to the window opening box (x0, y0, x1, y1): the part behind the frame and below
    the sill is simply not cut, so no paper of her shows on the office side."""
    x0, y0, x1, y1 = box
    r = np.float32([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    _, out = cv2.intersectConvexConvex(np.float32(poly), r)
    return out[:, 0, :].astype(np.float32)


def stranger(shape, s, at, away=False, clip=None):
    """STRANGER: 3 pieces (coat, head, hat); she faces -x (toward the office), or +x when she turns away.
    clip: the window opening (x0, y0, x1, y1); her pieces are cut so they end inside it (at or above the sill)."""
    d = 1 if away else -1
    coat = [(-82, -330), (-40, -372), (40, -372), (82, -330), (100, 0), (-100, 0)]
    hd = head_poly(40, 50, -420)
    hd[:, 0] *= d

    def hat(u):
        cv2.fillPoly(u, [np.int32(xf(ellipse(6 * d, -452, 86, 17, 0, 360, 40), s, at))], 255)
        cv2.fillPoly(u, [np.int32(xf(ellipse(-2 * d, -456, 46, 58, 180, 360, 24), s, at))], 255)
        if clip is not None:
            m = np.zeros_like(u)
            m[int(clip[1]):int(clip[3]), int(clip[0]):int(clip[2])] = 255
            u &= m
    cp, hp = xf(coat, s, at), xf(hd, s, at)
    if clip is not None:
        cp, hp = clip_convex(cp, clip), clip_convex(hp, clip)
    pieces = [P("coat", cp, "coat"), P("head", hp, "herhead"), P("hat", outline(hat, shape), "hat")]
    return pieces, xf([(34 * d, -402)], s, at)[0]


def clock(cx, cy, r, hh=4, mm=10):
    """CLOCK: 3 pieces (face, hour hand, minute hand)"""
    ah, am = math.radians((hh % 12) * 30 + mm * .5), math.radians(mm * 6)
    f = lambda a, k: (cx + math.sin(a) * r * k, cy - math.cos(a) * r * k)
    return [P("face", ellipse(cx, cy, r, r, 0, 360, 48), "face"),
            P("hour hand", limb_poly(f(ah, -.12), f(ah, .55), r * .17, r * .08), "hand"),
            P("minute hand", limb_poly(f(am, -.12), f(am, .86), r * .12, r * .05), "hand")]


def window(x0, y0, x1, y1, sill_x1):
    """TICKET WINDOW: 3 pieces (glass behind, the frame with its pane cut out, the sill/counter ledge)"""
    bw = 30
    glass = P("glass", rect(x0 + 14, y0 + 14, x1 - 14, y1 - 14), "glass", shadow=False)
    frame = P("frame", rect(x0, y0, x1, y1), "frame", holes=[rect(x0 + bw, y0 + bw, x1 - bw, y1 - bw * 2.5)],
              text=(["TICKET OFFICE"], int((x1 - x0) * 0.06), ((x0 + x1) / 2, y1 - bw * 1.25), "#f1e0a8"))
    sill = P("sill", rect(x0 - 24, y1 - 8, sill_x1, y1 + 44), "frame")
    return glass, [frame, sill]


def cupboard(x0, y0, x1, y1, open_k):
    """CUPBOARD: 2 pieces (dark carcass/opening, door hinged on the LEFT jamb)"""
    carcass = P("carcass", rect(x0, y0, x1, y1), "inside")
    if open_k <= 0:
        return carcass, P("door", rect(x0 + 9, y0 + 9, x1 - 9, y1 - 9), "door")
    dw = (x1 - x0 - 18) * (1 - 0.80 * open_k)
    return carcass, P("door", [(x0 + 9, y0 + 9), (x0 + 9 - dw, y0 + 9 - 30 * open_k), (x0 + 9 - dw, y1 - 9 + 30 * open_k),
                               (x0 + 9, y1 - 9)], "door")


def key(shape, x, y, s=1.0):
    """KEY: 3 pieces (hook, key: bow, shank and bit as one cut, SERVICE tag)"""
    def k(u):
        cv2.fillPoly(u, [np.int32(ellipse(x, y + 30 * s, 18 * s, 18 * s, 0, 360, 24))], 255)
        cv2.rectangle(u, (int(x - 5 * s), int(y + 40 * s)), (int(x + 5 * s), int(y + 120 * s)), 255, -1)
        cv2.rectangle(u, (int(x + 2 * s), int(y + 96 * s)), (int(x + 24 * s), int(y + 108 * s)), 255, -1)
        cv2.rectangle(u, (int(x + 2 * s), int(y + 112 * s)), (int(x + 20 * s), int(y + 120 * s)), 255, -1)
        cv2.rectangle(u, (int(x - 3 * s), int(y + 2 * s)), (int(x + 3 * s), int(y + 16 * s)), 255, -1)
    tx, ty = x + 22 * s, y + 54 * s
    return [P("hook", limb_poly((x - 18 * s, y), (x + 18 * s, y), 9 * s, 9 * s), "hook"),
            P("key", outline(k, shape), "key", holes=[ellipse(x, y + 30 * s, 8 * s, 8 * s, 0, 360, 14)]),
            P("tag", rect(tx, ty, tx + 104 * s, ty + 36 * s), "tag", text=(["SERVICE"], int(18 * s), (tx + 52 * s, ty + 19 * s), None))]


def service_door(x0, y0, x1, y1):
    """SERVICE DOOR: 2 pieces (door, card)"""
    cx, cw = (x0 + x1) / 2, (x1 - x0) * 0.8
    return [P("door", rect(x0, y0, x1, y1), "sdoor"),
            P("card", rect(cx - cw / 2, y0 + 70, cx + cw / 2, y0 + 70 + cw * 0.32), "card",
              text=(["SERVICE"], int(cw * 0.15), (cx, y0 + 70 + cw * 0.16), None))]


def memo(cx, cy, w, deg=-3):
    """MEMO: 1 piece, pencilled"""
    h = w * 0.56
    return [P("memo", xf(rect(-w / 2, -h / 2, w / 2, h / 2), 1.0, (cx, cy), rot=deg), "memo",
              text=(["4:15 - open", "SERVICE door.", "Key in cupboard."], int(w * 0.082), (cx, cy), None))]


def desk(x0, x1, ytop, yfloor):
    """DESK: 1 piece (top, apron and legs as one silhouette)"""
    t = 28
    return [P("desk", [(x0, ytop), (x1, ytop), (x1, ytop + t), (x1 - 22, ytop + t), (x1 - 22, yfloor), (x1 - 56, yfloor),
                       (x1 - 56, ytop + 110), (x0 + 56, ytop + 110), (x0 + 56, yfloor), (x0 + 22, yfloor), (x0 + 22, ytop + t),
                       (x0, ytop + t)], "desk")]


# ------------------------------------------------------------------ panels
PW, PH = 970, 640
FLOOR = 586
COLX = [110, 1120]
ROWY = [700, 1380, 2060]
S = 0.86
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]
BCAP = 46
COUNTS = {}


def balloon(c, lines, cap, centre, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.22, bend=0.10)
    penlib.lay_balloon(c.img, b, centre)


def panel(n, stage=9):
    """stage: for beats; 9 = finished panel"""
    c = Cut(PH, PW, seed=1600 + n, fibre_off=(n * 311, n * 177))
    sh = (PH, PW)
    c.piece(rect(-20, -20, PW + 20, FLOOR + 4), COL["wall"], shadow=False, grain=1.4)
    c.piece(rect(-20, FLOOR, PW + 20, PH + 20), COL["floor"], shadow=False)
    figs = {}
    if n == 1:   # E0: the memo on the desk; he rises and turns to go
        figs["clock"] = clock(840, 130, 64)
        ag, m = agent(sh, S, (250, FLOOR), arms="rise", head_rot=10)
        figs["agent+pencil"] = ag
        figs["desk"] = desk(60, 700, 400, FLOOR)
        figs["memo"] = memo(520, 330, 300, deg=-5)
        order = ["clock", "agent+pencil", "desk", "memo"]
    elif n in (2, 3, 4):
        wx = {2: 560, 3: 600, 4: 600}[n]
        glass, wfront = window(wx, 60, wx + 370, 460, PW + 30)
        # P4: she has turned away and is stepping off past the right jamb, half behind the frame
        sx = wx + 185 + (128 if n == 4 else 0)
        # the opening she is seen through: inside the frame's outer edge, down to the sill's top edge (y1 - 8)
        st, sm = stranger(sh, 0.8, (sx, 530), away=(n == 4), clip=(wx + 14, 60, wx + 356, 460 - 8))
        figs["window glass"] = [glass]
        figs["stranger"] = st
        figs["window"] = wfront
        if n == 3:
            figs["clock"] = clock(150, 110, 70)
            ag, m = agent(sh, S, (470, FLOOR), flip=True, arms="stand", head_rot=-30)
        else:
            ag, m = agent(sh, S, (170 if n == 2 else 260, FLOOR), arms="walk", legs="walk")
        figs["agent+pencil"] = ag
        order = ["window glass", "stranger", "window", "clock", "agent+pencil"]
    else:        # E4 / E5 at the cupboard
        figs["SERVICE door"] = service_door(790, 70, 950, FLOOR)
        open_k = 1.0 if (n == 6 or stage >= 2) else 0.0
        carcass, door = cupboard(470, 186, 730, FLOOR - 6, open_k)
        figs["cupboard"] = [carcass, door] if open_k == 0 else [carcass]
        if open_k > 0:
            figs["key"] = key(sh, 602, 220, 1.3)
            figs["cupboard door"] = [door]
        if n == 5:
            ag, m = agent(sh, S, (180, FLOOR), arms="reach" if open_k > 0 else "walk", legs="stand")
        else:
            ag, m = agent(sh, S, (150, FLOOR), arms="chin", head_rot=-6)
        figs["agent+pencil"] = ag
        order = ["SERVICE door", "cupboard", "key", "cupboard door", "agent+pencil"]
    for k in order:
        if k in figs:
            lay(c, figs[k], 1650 + n * 20 + order.index(k) * 3)
    cnt = {}
    for k, v in figs.items():
        for p in v:
            fig = {"window glass": "ticket window", "window": "ticket window", "cupboard door": "cupboard"}.get(k, k)
            if k == "agent+pencil":
                fig = "pencil" if p["name"] == "pencil" else "agent"
            cnt.setdefault(fig, []).append(p["name"])
    COUNTS[n] = cnt
    if stage >= 1:
        if n == 2:
            balloon(c, Q, BCAP, (436, 118), (sm[0] - 8, sm[1]), 1622)
        if n == 3:
            balloon(c, A, BCAP, (205, 430), (m[0] - 4, m[1] + 8), 1632)
        if n == 4:
            balloon(c, T, BCAP + 6, (560, 150), (sm[0] + 6, sm[1] - 4), 1642)
        if n == 6:
            balloon(c, F, BCAP, (500, 96), (m[0] + 10, m[1] - 6), 1666)
    return c.img


# ------------------------------------------------------------------ the parts strip
def explode(pieces, x, base, gap=26):
    """move pieces apart, side by side, bottoms on one baseline; returns (moved pieces, right edge)"""
    out = []
    for p in pieces:
        bb0, bb1 = p["poly"].min(0), p["poly"].max(0)
        d = np.float32([x - bb0[0], base - bb1[1]])
        q = dict(p, poly=p["poly"] + d, holes=[h + d for h in p["holes"]])
        if p["text"]:
            lines, cap, ctr, colour = p["text"]
            q["text"] = (lines, cap, (ctr[0] + d[0], ctr[1] + d[1]), colour)
        out.append(q)
        x = bb1[0] + d[0] + gap
    return out, x - gap


def parts_strip(pg):
    c = Cut(H, W, seed=1690, ground=pg)
    sh = (H, W)
    labels = []
    rows = [  # (label, pieces) ; laid left to right, two rows
        [("agent", agent(sh, 0.5, (1000, 1500))[0][:5]), ("pencil", agent(sh, 0.5, (1000, 1500))[0][5:]),
         ("stranger", stranger(sh, 0.5, (1000, 1500))[0]), ("clock", clock(0, 0, 50)), ("key", key(sh, 1000, 1500, 1.0))],
        [("cupboard", list(cupboard(0, 0, 100, 170, 0))), ("SERVICE door", service_door(0, 0, 80, 210)),
         ("ticket window", [window(0, 0, 170, 190, 190)[0]] + window(0, 0, 170, 190, 190)[1]),
         ("memo", memo(0, 0, 150, 0)), ("desk", desk(0, 190, 0, 120))],
    ]
    bases = [372, 640]
    for r, row in enumerate(rows):
        widths = []
        laid = []
        for lab, pcs in row:
            moved, right = explode(pcs, 0, 0)
            laid.append((lab, moved, right))
        total = sum(w for _, _, w in laid)
        gap = (1980 - 60 - total) / (len(laid) - 1)
        x = 140
        for lab, moved, right in laid:
            d = np.float32([x, bases[r]])
            pcs = [dict(p, poly=p["poly"] + d, holes=[h + d for h in p["holes"]],
                        text=(p["text"][0], p["text"][1], (p["text"][2][0] + d[0], p["text"][2][1] + d[1]), p["text"][3]) if p["text"] else None)
                   for p in moved]
            lay(c, pcs, 1700 + len(labels) * 7)
            labels.append((f"{lab}: {len(moved)}", (x + right / 2, bases[r] + 46), len(moved)))
            x += right + gap
    for i, (t, (lx, ly), _) in enumerate(labels):
        m = pen99.letter([t], 36, 1780 + i)
        sub = np.zeros((H, W), np.uint8)
        y0, x0 = int(ly - m.shape[0] / 2), int(lx - m.shape[1] / 2)
        sub[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
        penlib.ink_onto(c.img, sub)
    return c.img, labels


def build(stages=None, strip=True):
    """stages: {panel n: stage} for beats; panels absent from stages are left blank (unlaid)"""
    pg = pen99.sheet99()
    labels = []
    if strip:
        pg, labels = parts_strip(pg)
    boxes = []
    for n in range(1, 7):
        col, row = (n - 1) % 2, (n - 1) // 2
        x0, y0 = COLX[col], ROWY[row]
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        st = 9 if stages is None else stages.get(n)
        if st is None:
            continue
        pg[y0:y0 + PH, x0:x0 + PW] = panel(n, st)
    bm = penlib.border_mask(pg.shape[:2], boxes, 8, 1690)
    penlib.ink_onto(pg, bm)
    pen99.folio(pg, 16, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8), labels


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page, labels = build()
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    # beat: the cupboard panel assembled piece by piece from its cut shapes, then opened, then the forgetting
    seq = [({1: 9, 2: 9, 3: 9, 4: 9}, "b01: panels E0-E3 laid; the cupboard panels still empty sheet"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 0}, "b02: E4 panel: the agent arrives at the closed cupboard (carcass + door, 2 pieces)"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 2}, "b03: the cupboard door swings open on its left jamb; the key's 3 pieces (hook, key, tag) show"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 2, 6: 0}, "b04: E5 panel laid: pencil to his chin, no line yet"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 2, 6: 9}, "b05: + the forgetting balloon; key unmoved, SERVICE door shut (= the page)")]
    bd = []
    for j, (st, d) in enumerate(seq, 1):
        im = build(st)[0] if j < len(seq) else page
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(d)
    counts = {f"panel {n}": {k: len(v) for k, v in d.items()} for n, d in COUNTS.items()}
    mx = max(max(v.values()) for v in counts.values())
    record = {
        "n": 16, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p16_fewest_marks.py",
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "every figure and object HANDMADE cut paper in code (films/swarm/99-ways/kit/cutpaper99.py: scissor-faceted polygons, flat papers with the LoC 1934 sheet's fibre as relative tone, one down-right paper shadow per piece)",
            "AGENT 5 pieces (trousers, shirt cut in one with both sleeves, waistcoat, head with a nose as its only facial mark, hair) + PENCIL 1; STRANGER 3 (coat, head, hat); CLOCK 3 (face, hour hand, minute hand at 4:10); KEY 3 (hook, key with its bow hole, SERVICE tag); CUPBOARD 2 (dark carcass, door on the left jamb); SERVICE DOOR 2 (door, card); TICKET WINDOW 3 (glass, frame with the pane cut out, sill); MEMO 1; DESK 1",
            "a parts strip across the head of the page: every figure laid out in its separate pieces with its count in the pen hand (agent: 5, pencil: 1, stranger: 3, clock: 3, key: 3, cupboard: 2, SERVICE door: 2, ticket window: 3, memo: 1, desk: 1)",
            "six panels E0-E5 assembled from exactly those pieces; one wall paper and one floor paper per panel as ground",
            "lettering (memo, tag, card, TICKET OFFICE) in the shared pen hand; the four canon lines in the shared cut-paper balloons (penlib.balloon_piece); hand-ruled borders (penlib.border_mask); folio '16 / Fewest marks' (pen99.folio)"],
        "events": {"E0": "panel 1: memo on the desk, clock behind; he rises and turns to go",
                   "E1": "panel 2: walking; the stranger behind the ticket window glass; question balloon tailed to her",
                   "E2": "panel 3: head tipped back to the clock at 4:10; answer balloon tailed to him",
                   "E3": "panel 4: she turns away (her nose now points off), thanks balloon; he walks on",
                   "E4": "panel 5: he holds the cupboard door open on its left jamb; key on its hook with the SERVICE tag",
                   "E5": "panel 6: pencil to his chin, forgetting balloon; key on hook; SERVICE door shut"},
        "lines": LN,
        "beat": "the cupboard panel: the agent reaches the closed cupboard (two pieces), the door swings open on its left jamb showing the key's three pieces, then the E5 panel is laid and its balloon added",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "pieces_per_figure_by_panel": counts, "max_pieces_any_figure": mx, "le_five": mx <= 5,
                       "parts_strip": [t for t, _, _ in labels],
                       "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/16.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()
