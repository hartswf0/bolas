"""99 ways, page 03 "Backwards" (time and order; medium: engraving-puppet).
A storyboard sheet of eight boards read in the normal order, whose beats run in reverse: board 1 is E5 (the
forgetting), board 8 is E0 (the memo). Each board: a graphite header (board number, event, clock time running
backwards), a panel of cut-paper ENGRAVING PUPPETS pinned with brass pins, and pasted slips beneath: the narration
slip ('Before that, ...') and, where a line is spoken, a dialogue slip naming the speaker.
Puppets (FORAGED, printed as ink onto cream card and cut along drawn scissor paths):
  AGENT  = the telegraph operator in waistcoat and shirt sleeves, Harper's Weekly 24 Jan 1863 p.53 (A.R. Waud), LoC cph.3c11072
           cut into legs, torso, head and two arms pinned at the joints; his table + instrument and the window from the same plate.
  STRANGER = the woman in a hat with a hatbox, 'Buying tickets for the Dickens readings at Steinway Hall' (1867), LoC cph.3c32079.
Set (HANDMADE, pen line in the shared hand): clock at 4:10/4:11, cupboard with key on hook and SERVICE tag, SERVICE door, memo.
Writes assets/pages/99-ways/03-backwards.jpg, films/sources/99-ways/masters/03-backwards.png,
films/sources/99-ways/beats/03/b01..b08.png, films/swarm/99-ways/pages/03.json.   Run: python3 -I build_page03.py"""
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import hexc  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = CANON["constraints"][2]
assert C["id"] == "backwards"
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
FOR = SRC / "forage"
OUT_JPG = ROOT / "assets/pages/99-ways/03-backwards.jpg"
OUT_PNG = SRC / "masters/03-backwards.png"
BEATS = SRC / "beats/03"
W, H = pen99.PAGE_W, pen99.PAGE_H
CARD = hexc("#f4eddc")
SLIPC = hexc("#fbf5e6")
GRAPH = hexc("#5f5a55")
INK = penlib.INK
BRASS = hexc("#b48a3c")

# ------------------------------------------------------------------------------------------- puppets
OPS = 1146 / 874     # operator crop: display px -> crop px
OP_PIECES = {   # display coords of the 874x1000 preview of tel_operator_crop.png; pivot = joint to parent
    "legs": [(470, 450), (572, 448), (625, 515), (700, 518), (706, 600), (662, 680), (642, 758), (694, 790), (610, 792),
             (600, 705), (562, 722), (548, 900), (522, 936), (458, 948), (478, 880), (490, 700), (472, 560)],
    "torso": [(452, 236), (612, 240), (630, 272), (616, 482), (572, 522), (478, 504), (458, 444), (446, 300)],
    "head": [(468, 124), (572, 122), (588, 180), (574, 240), (532, 276), (490, 272), (478, 232), (464, 172)],
    "armU": [(474, 238), (436, 246), (370, 326), (378, 348), (412, 356), (424, 332), (472, 304)],
    "armF": [(372, 324), (350, 352), (328, 394), (333, 452), (362, 444), (376, 388), (414, 354), (396, 330)],
    "armL": [(598, 246), (652, 262), (702, 330), (732, 418), (738, 462), (702, 522), (650, 524), (626, 502), (662, 482), (690, 460), (670, 400), (618, 322)],
    "table": [(35, 400), (456, 420), (472, 560), (446, 830), (424, 836), (392, 682), (332, 692), (332, 982), (298, 986),
              (290, 702), (100, 700), (96, 976), (60, 976), (55, 682), (35, 650)],
    "window": [(34, 136), (244, 146), (244, 412), (38, 422)],
}
JOINTS = {"torso": (520, 470), "head": (525, 252), "armU": (462, 262), "armF": (392, 340), "armL": (606, 258)}   # display coords
WOMAN = [(178, 70), (205, 58), (240, 62), (262, 85), (250, 100), (245, 130), (232, 152), (222, 160), (232, 200), (262, 250),
         (300, 320), (320, 380), (335, 400), (378, 470), (375, 500), (345, 520), (300, 545), (325, 620), (345, 700), (360, 780),
         (330, 800), (200, 810), (110, 815), (70, 800), (80, 700), (100, 600), (120, 520), (110, 420), (105, 320), (110, 250),
         (100, 200), (98, 140), (115, 105), (150, 100), (185, 95)]


def engraving_ink(g):
    """the engraving's line as ink on cream card (one threshold curve for every plate)"""
    a = np.clip((205.0 - g) / (205.0 - 70.0), 0, 1) ** 0.9
    return a


def cut_piece(gray, poly, scale_poly=1.0):
    """card piece (rgb float, alpha uint8, origin) cut along a drawn scissor path"""
    P = np.array(poly, np.float32) * scale_poly
    x0, y0 = np.floor(P.min(0)).astype(int) - 12
    x1, y1 = np.ceil(P.max(0)).astype(int) + 12
    x0, y0 = max(0, x0), max(0, y0)
    sub = gray[y0:y1, x0:x1].astype(np.float32)
    m = np.zeros(sub.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((P - (x0, y0)) * 4))], 255, cv2.LINE_AA, shift=2)
    a = engraving_ink(sub)[..., None]
    rgb = CARD * (1 - a) + INK * a
    return dict(rgb=rgb, a=m, origin=(x0, y0))


def load_puppets():
    op = np.asarray(Image.open(FOR / "tel_operator_crop.png").convert("L"))
    wo = np.asarray(Image.open(FOR / "dickens_woman_crop.png").convert("L"))
    P = {k: cut_piece(op, v, OPS) for k, v in OP_PIECES.items()}
    P["woman"] = cut_piece(wo, WOMAN, 1.0)
    return P


def lay(canvas, piece, M, shadow=True, margin=5, lift=0):
    """lay a card piece with affine M (piece px -> canvas px), cream scissor margin, one shadow"""
    h, w = canvas.shape[:2]
    ox, oy = piece["origin"]
    T = np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]], np.float64)
    MM = (np.vstack([M, [0, 0, 1]]) @ T)[:2]
    a = cv2.warpAffine(piece["a"], MM, (w, h), flags=cv2.INTER_LINEAR)
    c = cv2.warpAffine(piece["rgb"].astype(np.float32), MM, (w, h), flags=cv2.INTER_AREA)
    ab = (a > 127).astype(np.uint8) * 255
    pm = penlib.scissor(ab, margin) if margin else ab
    if shadow:
        penlib.shadow_onto(canvas, pm, off=5 + lift, blur=4, opacity=0.33)
    pa = pm.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - pa) + CARD * pa
    af = a.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - af) + c * af


def pin(canvas, x, y, r=7):
    m = np.zeros(canvas.shape[:2], np.uint8)
    cv2.circle(m, (int(x * 4), int(y * 4)), int(r * 4), 255, -1, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, m, off=3, blur=2, opacity=0.4)
    a = m.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - a) + BRASS * a
    hl = np.zeros_like(m)
    cv2.circle(hl, (int((x - r * .3) * 4), int((y - r * .3) * 4)), int(r * 1.4), 255, -1, cv2.LINE_AA, shift=2)
    canvas[:] = canvas * (1 - hl[..., None] / 255 * .6) + hexc("#f0d9a0") * (hl[..., None] / 255 * .6)


def Mof(scale, deg, about, to):
    """affine: scale+rotate about point `about` (piece px), placing it at `to` (canvas px)"""
    R = cv2.getRotationMatrix2D((float(about[0]), float(about[1])), deg, scale)
    R[0, 2] += to[0] - about[0]
    R[1, 2] += to[1] - about[1]
    return R


def agent(canvas, P, foot, s, arms=(0, 0, 0), head=0, flip=False, pins=True):
    """the articulated agent: legs root at foot point; arms = (upper arm, forearm relative, left arm) in degrees
    (cv2 sense) about their joints; flip mirrors the whole puppet (it faces the other way)."""
    J = {k: np.array(v, np.float32) * OPS for k, v in JOINTS.items()}
    legs_foot = np.array([510, 940], np.float32) * OPS
    Mb = np.vstack([Mof(s, 0, legs_foot, foot), [0, 0, 1]])
    if flip:
        Mb = np.array([[-1, 0, 2 * foot[0]], [0, 1, 0], [0, 0, 1]], np.float64) @ Mb
    Rj = lambda k, deg: np.vstack([cv2.getRotationMatrix2D((float(J[k][0]), float(J[k][1])), deg, 1.0), [0, 0, 1]])
    Mu = Mb @ Rj("armU", arms[0])
    Mf = Mu @ Rj("armF", arms[1])
    lay(canvas, P["armL"], (Mb @ Rj("armL", arms[2]))[:2])
    lay(canvas, P["legs"], Mb[:2])
    lay(canvas, P["torso"], Mb[:2])
    lay(canvas, P["head"], (Mb @ Rj("head", head))[:2])
    lay(canvas, P["armU"], Mu[:2], lift=2)
    lay(canvas, P["armF"], Mf[:2], lift=3)
    if pins:
        for k, M in (("armU", Mb), ("armF", Mu), ("armL", Mb), ("head", Mb), ("torso", Mb)):
            q = M @ np.array([J[k][0], J[k][1], 1.0])
            pin(canvas, q[0], q[1], 4)
    hand = np.array([336, 446], np.float32) * OPS
    return (Mf @ np.array([hand[0], hand[1], 1.0]))[:2]


def woman(canvas, P, foot, s, flip=False, deg=0):
    pc = P["woman"]
    foot0 = np.array([215, 812], np.float32)
    M = np.vstack([Mof(s, deg, foot0, foot), [0, 0, 1]])
    if flip:
        M = np.array([[-1, 0, 2 * foot[0]], [0, 1, 0], [0, 0, 1]], np.float64) @ M
    lay(canvas, pc, M[:2])
    q = M @ np.array([200, 150, 1.0])
    pin(canvas, q[0], q[1], 6)


# ------------------------------------------------------------------------------------------- pen set (HANDMADE)
def pen(canvas, pts, w=4, seed=0, closed=False, colour=INK):
    m = np.zeros(canvas.shape[:2], np.uint8)
    pts = list(pts) + ([pts[0]] if closed else [])
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        penlib.brush_line(m, [a, b], w, seed + i, tremor=0.6)
    penlib.ink_onto(canvas, m, colour)


def circle_pts(cx, cy, r, n=40):
    return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def clock(canvas, cx, cy, r, hh, mm, seed):
    pen(canvas, circle_pts(cx, cy, r), 4, seed, closed=True)
    pen(canvas, circle_pts(cx, cy, r * 1.15), 3, seed + 50, closed=True)
    for k in range(12):
        a = math.radians(k * 30)
        L = 0.2 if k % 3 == 0 else 0.1
        pen(canvas, [(cx + math.sin(a) * r * .85, cy - math.cos(a) * r * .85), (cx + math.sin(a) * r * (.85 - L), cy - math.cos(a) * r * (.85 - L))], 3, seed + 100 + k)
    ah, am = math.radians((hh % 12) * 30 + mm * .5), math.radians(mm * 6)
    pen(canvas, [(cx, cy), (cx + math.sin(ah) * r * .5, cy - math.cos(ah) * r * .5)], 6, seed + 200)
    pen(canvas, [(cx, cy), (cx + math.sin(am) * r * .78, cy - math.cos(am) * r * .78)], 4, seed + 201)
    pen(canvas, [(cx - r * .7, cy + r * 1.15), (cx - r * .7, cy + r * 2.6), (cx + r * .7, cy + r * 2.6), (cx + r * .7, cy + r * 1.15)], 4, seed + 300)
    pen(canvas, [(cx, cy + r * 1.2), (cx, cy + r * 2.1)], 2, seed + 301)
    pen(canvas, circle_pts(cx, cy + r * 2.15, r * .15, 14), 3, seed + 302, closed=True)


def letters(canvas, lines, cap, cx, cy, seed, colour=INK):
    m = pen99.letter(lines, cap, seed)
    h, w = m.shape
    x, y = int(cx - w / 2), int(cy - h / 2)
    sub = np.zeros(canvas.shape[:2], np.uint8)
    ys, xs, ye, xe = max(0, y), max(0, x), min(canvas.shape[0], y + h), min(canvas.shape[1], x + w)
    sub[ys:ye, xs:xe] = m[ys - y:ye - y, xs - x:xe - x]
    penlib.ink_onto(canvas, sub, colour)
    return w, h


def key(canvas, x, y, s, seed):
    """the brass key on its hook, pen line, with its SERVICE tag"""
    pen(canvas, [(x - 12 * s, y), (x + 12 * s, y)], 4, seed)                       # hook rail
    pen(canvas, [(x, y), (x, y + 14 * s)], 4, seed + 1)
    pen(canvas, circle_pts(x, y + 26 * s, 12 * s, 18), 4, seed + 2, closed=True)    # bow
    pen(canvas, [(x, y + 38 * s), (x, y + 92 * s)], 5, seed + 3)                   # shank
    pen(canvas, [(x, y + 80 * s), (x + 12 * s, y + 80 * s), (x + 12 * s, y + 92 * s), (x, y + 92 * s)], 4, seed + 4)
    pen(canvas, [(x + 6 * s, y + 30 * s), (x + 30 * s, y + 52 * s)], 2, seed + 5)  # tag string
    pen(canvas, [(x + 24 * s, y + 48 * s), (x + 80 * s, y + 48 * s), (x + 80 * s, y + 70 * s), (x + 24 * s, y + 70 * s)], 3, seed + 6, closed=True)
    letters(canvas, ["SERVICE"], 13 * s, x + 52 * s, y + 59 * s, seed + 7)


def cupboard(canvas, x0, y0, x1, y1, open_k, seed, with_key=True):
    """cupboard against the wall; door hinged on the left jamb, open by open_k (0..1)"""
    pen(canvas, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 5, seed, closed=True)
    if open_k > 0:
        for i, yy in enumerate(np.linspace(y0 + 40, y1 - 30, 4)):
            pen(canvas, [(x0 + 8, yy), (x1 - 8, yy)], 3, seed + 10 + i)                    # shelves
        if with_key:
            key(canvas, x0 + (x1 - x0) * 0.55, y0 + 18, 1.0, seed + 30)
        dx = (x1 - x0) * (1 - 0.85 * open_k)
        pen(canvas, [(x0, y0), (x0 - dx * 0.55, y0 - 22 * open_k), (x0 - dx * 0.55, y1 + 22 * open_k), (x0, y1)], 5, seed + 40)
    else:
        pen(canvas, [(x1 - 18, (y0 + y1) / 2 - 10), (x1 - 18, (y0 + y1) / 2 + 10)], 5, seed + 41)       # knob
        pen(canvas, [(x0 + 15, y0 + 15), (x1 - 15, y0 + 15), (x1 - 15, y1 - 15), (x0 + 15, y1 - 15)], 2, seed + 42, closed=True)


def service_door(canvas, x0, y0, x1, y1, seed):
    pen(canvas, [(x0, y1), (x0, y0), (x1, y0), (x1, y1)], 5, seed)
    pen(canvas, [(x1 - 22, (y0 + y1) / 2), (x1 - 12, (y0 + y1) / 2)], 6, seed + 1)
    cx = (x0 + x1) / 2
    pen(canvas, [(cx - 62, y0 + 40), (cx + 62, y0 + 40), (cx + 62, y0 + 80), (cx - 62, y0 + 80)], 3, seed + 2, closed=True)
    letters(canvas, ["SERVICE"], 22, cx, y0 + 60, seed + 3)


def memo(canvas, cx, cy, s, seed, deg=0):
    w, h = 300 * s, 170 * s
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    a = math.radians(deg)
    R = lambda p: (cx + p[0] * math.cos(a) - p[1] * math.sin(a), cy + p[0] * math.sin(a) + p[1] * math.cos(a))
    m = np.zeros(canvas.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32([[R(p)[0] * 4, R(p)[1] * 4] for p in pts])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, m, off=4, blur=3, opacity=0.3)
    canvas[:] = canvas * (1 - m[..., None] / 255) + SLIPC * (m[..., None] / 255)
    pen(canvas, [R(p) for p in pts], 3, seed, closed=True)
    letters(canvas, ["MEMO", "4:15 - open", "SERVICE door.", "Key in cupboard."], 26 * s, cx, cy, seed + 5)


def ground_line(canvas, x0, x1, y, seed):
    pen(canvas, [(x0 + 14, y), (x1 - 14, y)], 3, seed)


# ------------------------------------------------------------------------------------------- boards
BOARDS = [  # n, event, time, narration slip lines, dialogue (speaker, line lines) or None
    (1, "E5", "4:11", ["4:11. He stands at the open", "cupboard. The key hangs there.", "He can't think why he came."], ("AGENT, to himself", ["Well, here I am...", "and what for?"])),
    (2, "E4", "4:11", ["Before that: he opened", "the cupboard, and there", "was the key, tagged SERVICE."], None),
    (3, "E3", "4:10", ["Before that: she thanked", "him and left the window."], ("STRANGER", ["Much obliged!"])),
    (4, "E2", "4:10", ["Before that: he looked up", "at the clock and told her."], ("AGENT", ["Ten past four,", "by the clock."])),
    (5, "E1", "4:10", ["Before that: on his way", "across, she stopped him", "at the window."], ("STRANGER", ["Pardon me —", "have you the", "right time?"])),
    (6, "E0", "4:09", ["Before that: he set off", "across the office for", "the cupboard."], None),
    (7, "E0", "4:09", ["Before that: he rose", "from his desk."], None),
    (8, "E0", "4:08", ["It began here:", "the memo on his desk."], None),
]
for _b in BOARDS:
    if _b[4]:
        assert " ".join(_b[4][1]) in LN.values(), _b
COLX = [(110, 1080), (1120, 2090)]
ROWY = [110, 770, 1430, 2090]
PW, PH = 970, 380


def panel(n, P):
    """draw board n's picture at panel size; returns float RGB"""
    c = np.zeros((PH, PW, 3), np.float32) + CARD + (np.random.RandomState(n).rand(PH, PW, 1) - 0.5) * 3
    gy = PH - 36
    ground_line(c, 0, PW, gy, 700 + n)
    s = 0.33
    if n == 1:      # E5: before the open cupboard, hand to his chin with the pencil
        service_door(c, 700, 60, 860, gy, 810)
        cupboard(c, 430, 70, 640, gy - 20, 1.0, 820)
        h = agent(c, P, (330, gy + 2), s, arms=(47, 132, 0), head=-6, flip=True)
        pen(c, [(h[0] + 2, h[1] + 4), (h[0] - 6, h[1] - 34)], 5, 830)                  # the pencil to his chin
    elif n == 2:    # E4: he opens it; the door swings on the left jamb, key on its hook
        service_door(c, 700, 60, 860, gy, 811)
        cupboard(c, 430, 70, 640, gy - 20, 0.75, 821)
        h = agent(c, P, (250, gy + 2), s, arms=(-62, 30, 0), flip=True)
    elif n in (3, 4, 5):   # the ticket window: him inside (left), her outside (right)
        Mw = Mof(1.05, 0, np.array([140, 280]) * OPS, (560, 175))
        if n == 4:
            clock(c, 150, 92, 46, 4, 10, 840)
        agent(c, P, (330 if n != 3 else 260, gy + 2), s, arms=((0, 0, 0) if n != 4 else (60, 150, 0)), head=(-14 if n == 4 else 0), flip=(n != 3))
        lay(c, P["window"], Mw)                                                               # the glazed window between them
        letters(c, ["TICKET", "OFFICE"], 22, 560, 300, 850)
        if n == 3:
            woman(c, P, (820, gy + 2), 0.44, flip=True)                                       # leaving: she turns away
        else:
            woman(c, P, (730, gy + 2), 0.44)                                                  # at the glass, facing in
    elif n == 6:    # E0: walking across the office, cupboard ahead
        cupboard(c, 760, 70, 930, gy - 20, 0.0, 822)
        agent(c, P, (430, gy + 2), s, arms=(12, 0, -8), flip=True)
    elif n == 7:    # E0: rising from the desk, the memo on it
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (300, gy + 2)))
        memo(c, 250, 172, 0.55, 860, deg=-4)
        agent(c, P, (520, gy + 2), s, arms=(0, 0, 0))
    elif n == 8:    # E0: the memo, close; his finger on it
        memo(c, 470, 190, 1.2, 870, deg=-3)
        hand = np.array([336, 446], np.float32) * OPS
        M = Mof(0.95, 35, hand, (690, 250))          # whole arm, the finger on the memo's last line
        lay(c, P["armU"], M, lift=3)
        lay(c, P["armF"], M, lift=4)
    return c


def slip(canvas, lines, cap, x, y, seed, speaker=None, maxw=900):
    let = pen99.letter(lines, cap, seed)
    sp = pen99.letter([speaker + ":"], cap * 0.8, seed + 9) if speaker else None
    lh, lw = let.shape
    sh_ = sp.shape if sp is not None else (0, 0)
    ww = max(lw, sh_[1]) + int(cap * 0.8)
    hh = lh + sh_[0] + int(cap * 0.3)
    rnd = random.Random(seed)
    m = np.zeros(canvas.shape[:2], np.uint8)
    pts = [(x, y + rnd.uniform(0, 4)), (x + ww, y + rnd.uniform(0, 4)), (x + ww + rnd.uniform(-3, 3), y + hh), (x, y + hh - rnd.uniform(0, 4))]
    # torn bottom edge
    tear = [(x + ww - k, y + hh + rnd.uniform(-4, 3)) for k in range(0, ww, 14)]
    poly = [pts[0], pts[1]] + tear + [pts[3]]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in poly])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, m, off=4, blur=3, opacity=0.3)
    canvas[:] = canvas * (1 - m[..., None] / 255) + SLIPC * (m[..., None] / 255)
    yy = y + int(cap * 0.15)
    for mm in ([sp] if sp is not None else []) + [let]:
        h, w = mm.shape
        sub = np.zeros(canvas.shape[:2], np.uint8)
        sub[yy:yy + h, x + int(cap * 0.3):x + int(cap * 0.3) + w] = mm
        penlib.ink_onto(canvas, sub, GRAPH if (sp is not None and mm is sp) else INK)
        yy += h
    pin(canvas, x + 16, y + 14, 6)
    return ww, hh


def build(upto=8):
    pg = pen99.sheet99()
    P = load_puppets()
    for (n, ev, t, narr, dia) in BOARDS:
        if n > upto:
            continue
        col = (n - 1) % 2
        row = (n - 1) // 2
        x0, x1 = COLX[col]
        y0 = ROWY[row]
        hdr = pen99.letter([f"board {n}   {ev}   {t}"], 32, 9300 + n)
        h, w = hdr.shape
        sub = np.zeros(pg.shape[:2], np.uint8)
        sub[y0:y0 + h, x0:x0 + w] = hdr
        penlib.ink_onto(pg, sub, GRAPH)
        py = y0 + 48
        pg[py:py + PH, x0:x0 + PW] = panel(n, P)
        bm = penlib.border_mask(pg.shape[:2], [(x0, py, x0 + PW, py + PH)], 7, 9400 + n)
        penlib.ink_onto(pg, bm)
        hole = np.zeros(pg.shape[:2], np.uint8)
        cv2.circle(hole, (x0 + 26, py + 26), 9, 255, -1, cv2.LINE_AA)
        penlib.ink_onto(pg, hole, hexc("#2a2622"))
        sy = py + PH + 14
        ww, hh = slip(pg, narr, 30, x0 + 10, sy, 9500 + n)
        if dia:
            sp, dl = dia
            dw = pen99.letter(dl, 36, 1).shape[1] + 30
            slip(pg, dl, 36, x0 + PW - dw - 10, sy - 4, 9600 + n, speaker=sp)
    # the reading arrow note
    pen99.folio(pg, 3, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8)


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS, ROOT / "films/swarm/99-ways/pages"):
        p.mkdir(parents=True, exist_ok=True)
    page = build(8)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    if "--page-only" in sys.argv:
        print(size)
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    bd = []
    for j in range(1, 9):
        im = page if j == 8 else build(j)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: boards 1-{j} pinned (board {j} = {BOARDS[j - 1][1]}, {BOARDS[j - 1][2]})")
    record = {
        "n": 3, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "sources": ["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-1867-dickens-tickets-steinway",
                    "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": ["AGENT puppet: the 1863 telegraph operator (waistcoat, shirt sleeves) cut along drawn scissor paths into legs, torso, head and two arms, pinned with brass pins at the joints; his table and the window cut from the same plate",
                 "STRANGER puppet: the hatted woman with a hatbox from the 1867 Steinway Hall wood engraving, cut along a drawn path",
                 "engraving line printed as ink onto cream card with one threshold curve; cream scissor margin and one shadow per piece",
                 "set in the shared pen hand (HANDMADE): clock (4:10 at the answer), cupboard hinged on the left jamb with the key on its hook and SERVICE tag, SERVICE door, memo, ground lines",
                 "graphite board headers (board n, event, clock time running backwards 4:11 -> 4:08), pasted torn slips with brass pins: narration 'Before that: ...' and dialogue slips naming the speaker",
                 "storyboard sheet on the LoC 1934 sheet ground; folio '03 / Backwards' (pen99.folio)"],
        "events": {f"board {n}": f"{ev} {t}: " + " ".join(narr) + (f" | {d[0]}: {d[1]}" if d else "") for (n, ev, t, narr, d) in BOARDS},
        "lines": LN,
        "beat": "the boards pinned one by one in reading order, so the story is laid down backwards: the forgetting first, the memo last",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "order": "board 1 = E5 (forgetting), board 8 = E0 (memo); headers read E5 E4 E3 E2 E1 E0 E0 E0 and times 4:11 down to 4:08",
                       "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/03.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()
