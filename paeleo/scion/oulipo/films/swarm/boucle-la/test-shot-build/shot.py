"""boucle-la TEST SHOT: the hinge H into B' (film time 26.0-31.0 s, then 45.5-50.5 s).

Page art = cut pieces of Daumier's 1839 lithograph (cutouts.py) posed on a forward-kinematics rig
(SCION 32), timed on 2s with Gilliam paper jerk and the note's back->face substitution at edge-on
(SCION 1), composed on a hand-lettered pen page.  The film camera moves over the same page raster.
Run: python3 -I shot.py [--stills]
"""
import hashlib
import json
import math
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SWARM = os.path.join(ROOT, "films/swarm/boucle-la")
sys.path.insert(0, os.path.join(SWARM, "proposals"))
sys.path.insert(0, os.path.join(ROOT, "films"))
import kf_common as kc  # noqa: E402  (the work's own stroke alphabet)

MEDIA = os.path.join(ROOT, "films/sources/boucle-la/test-shot")
CUT = os.path.join(MEDIA, "cut")
INK, PAGE = 13, 251
PW, PH = 3200, 1800

# ---------------------------------------------------------------- digits for the margin credit (pen strokes)
kc.G.update({
    "1": (2.2, [[(0.2, 1.2), (1.4, 0), (1.4, 6)], [(0.3, 6), (2.2, 6)]]),
    "3": (3.6, [[(0.2, 0.8), (1.1, 0), (2.6, 0), (3.4, 0.9), (3.3, 2.1), (2.2, 2.9), (1.2, 2.9)],
                [(2.2, 2.9), (3.5, 3.8), (3.5, 5.1), (2.6, 6), (1.0, 6), (0.1, 5.2)]]),
    "8": (3.6, [kc._arc(1.8, 1.5, 1.5, 1.5, 0, 360, 18), kc._arc(1.8, 4.4, 1.8, 1.6, 0, 360, 20)]),
    "9": (3.6, [kc._arc(1.8, 2.0, 1.6, 2.0, 0, 360, 20), [(3.4, 2.0), (3.2, 4.6), (2.2, 6), (0.6, 5.6)]]),
})

TEXT = kc.TEXT  # A, B, C, H: speaker and exact balloon string (the proposal's lines, kept)
SEQ = ["A", "B", "C", "H", "C", "B", "A"]

# ---------------------------------------------------------------- the page layout (plan §5)
def rects():
    r = {}
    for i in range(3):
        x0 = 560 + i * 880
        r[i] = (x0, 40, x0 + 850, 620)          # row 1: A B C
        r[4 + i] = (x0, 1180, x0 + 850, 1760)   # row 3: C B A
    r[3] = (560, 650, 3170, 1150)               # row 2: H, full width
    return r


RECTS = rects()

# ---------------------------------------------------------------- cut pieces and rig
CJ = json.load(open(os.path.join(CUT, "cutouts.json")))
K = CJ["K"]
PIECE = {}
for k, v in CJ["pieces"].items():
    im = np.asarray(Image.open(os.path.join(ROOT, v["file"])).convert("RGBA"))
    PIECE[k] = (im[..., 0].astype(np.float32), im[..., 3].astype(np.float32) / 255.0, v["offset"], v["pin"])
FEET = CJ["rig"]["feet"]
HAND = CJ["rig"]["hand"]
MOUTH = {"gustave": (478 * K, 402 * K), "odette": (557 * K, 398 * K)}
FIG_ORDER = [("gustave", ["body", "head", "fore"]), ("odette", ["body", "head", "fore"])]


def A_rot(deg, cx, cy):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, cx - c * cx + s * cy], [s, c, cy - s * cx - c * cy], [0, 0, 1]], np.float64)


def A_ts(s, tx, ty):
    return np.array([[s, 0, tx], [0, s, ty], [0, 0, 1]], np.float64)


def apply(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return float(v[0]), float(v[1])


def fk(pose, frame):
    """Forward kinematics: matrices src->panel for every piece, root->leaf in fixed order."""
    s, ox, oy = frame
    base = A_ts(s / K, ox, oy)   # frame scale is page px per thumb px
    Ms = {}
    for fig, parts in FIG_ORDER:
        P = pose[fig]
        root = base @ A_rot(P["lean"], *FEET[fig])
        Ms[fig + "_body"] = root
        for pn in ("head", "fore"):
            pin = PIECE[f"{fig}_{pn}"][3]
            Ms[f"{fig}_{pn}"] = root @ A_rot(P[pn], pin[0], pin[1])
    return Ms


def warp_piece(canvas, cov, key, M, shadow=True):
    g, a, (x0, y0), _ = PIECE[key]
    Mo = M @ np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], np.float64)
    h, w = canvas.shape
    gw = cv2.warpAffine(g, Mo[:2], (w, h), flags=cv2.INTER_CUBIC, borderValue=PAGE)
    aw = cv2.warpAffine(a, Mo[:2], (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    if shadow:  # paper on paper: a faint 3 px contact shadow, offset down-right
        sh = np.roll(np.roll(aw, 3, 0), 3, 1)
        sh = cv2.GaussianBlur(sh, (0, 0), 1.6) * 0.22
        canvas[:] = canvas * (1 - sh) + INK * sh
    canvas[:] = canvas * (1 - aw) + np.clip(gw, INK, PAGE) * aw
    cov[:] = np.maximum(cov, aw)


# ---------------------------------------------------------------- the handmade note (pen and cut paper)
NOTE_W, NOTE_H = 118, 78  # thumb px; the note's physical size never changes


def note_card(face, scale, ss=3):
    """Front ('À MA CHÈRE / ODETTE') or back (a plain folded sheet with its crease), gray + alpha."""
    w, h = int(round(NOTE_W / K * K * scale)), int(round(NOTE_H * scale))
    w = int(round(NOTE_W * scale))
    W_, H_ = w * ss, h * ss
    paper = Image.new("L", (W_, H_), 0)
    ink = Image.new("L", (W_, H_), 0)
    rs = random.Random(11 if face else 12)
    m = 2 * ss
    quad = [(m + rs.uniform(0, 2) * ss, m), (W_ - m, m + rs.uniform(0, 2) * ss), (W_ - m - rs.uniform(0, 2) * ss, H_ - m),
            (m, H_ - m - rs.uniform(0, 2) * ss)]
    dp, di = ImageDraw.Draw(paper), ImageDraw.Draw(ink)
    dp.polygon(quad, fill=255)
    di.line(quad + [quad[0]], fill=255, width=int(2.4 * ss * scale / 1.2), joint="curve")
    if face:
        cap = h * 0.2
        y = h * 0.2
        for i, l in enumerate(kc.NOTE_FACE):
            lw = kc.text_width(l, cap)
            kc.ink_text(ink, (w - lw) / 2 * ss, y * ss, l, cap=cap * ss, seed=21 + i, pen=max(2, int(cap * 0.2 * ss)), slant=0.16)
            y += cap * 1.75
    else:  # the back: the fold crease, drawn as a thin pen line
        di.line([(W_ * 0.52, m * 2), (W_ * 0.5, H_ - m * 2)], fill=150, width=max(1, int(1.2 * ss)))
    paper = np.asarray(paper.resize((w, h), Image.LANCZOS), np.float32) / 255
    inkm = np.asarray(ink.resize((w, h), Image.LANCZOS), np.float32) / 255
    gray = PAGE * (1 - inkm) + INK * inkm
    alpha = np.maximum(paper, inkm)
    return gray, alpha


def draw_note(canvas, cov, Ms, pose, s):
    P = pose["odette"]
    th = P.get("turn", 0.0)  # 0 = back to the reader, 180 = face out; substitution at edge-on (90)
    face = th > 90
    gray, alpha = note_card(face, s)
    h, w = gray.shape
    c = abs(math.cos(math.radians(th)))
    half = max(0.04, c) * w / 2
    persp = 0.10 * math.sin(math.radians(th))  # the near edge grows as it swings: foreshortened card
    hx, hy = apply(Ms["odette_fore"], HAND["odette"])
    # the note is held by its right edge in her hand, tilted, centred left of the hand
    tilt = math.radians(P.get("tilt", 0.0))
    cx, cy = hx - 0.42 * w, hy - 0.42 * h
    corners = [(-half, -h / 2 * (1 - persp)), (half, -h / 2 * (1 + persp)), (half, h / 2 * (1 + persp)), (-half, h / 2 * (1 - persp))]
    dst = []
    for (x, y) in corners:
        dst.append((cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)))
    src = np.float32([(0, 0), (w, 0), (w, h), (0, h)])
    Mp = cv2.getPerspectiveTransform(src, np.float32(dst))
    H_, W_ = canvas.shape
    gw = cv2.warpPerspective(gray, Mp, (W_, H_), flags=cv2.INTER_CUBIC, borderValue=PAGE)
    aw = cv2.warpPerspective(alpha, Mp, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=0)
    if c < 0.1:  # edge-on: the sheet is a single pen stroke of paper edge
        d = np.zeros_like(canvas, np.uint8)
        top, bot = dst[0], dst[3]
        cv2.line(d, (int(cx), int(cy - h / 2)), (int(cx), int(cy + h / 2)), 255, max(2, int(3 * s / 1.2)), cv2.LINE_AA)
        aw = d.astype(np.float32) / 255
        gw = np.full_like(canvas, INK)
    sh = cv2.GaussianBlur(np.roll(np.roll(aw, 3, 0), 3, 1), (0, 0), 1.6) * 0.22
    canvas[:] = canvas * (1 - sh) + INK * sh
    canvas[:] = canvas * (1 - aw) + np.clip(gw, INK, PAGE) * aw
    return (cx, cy)


# ---------------------------------------------------------------- poses (degrees) and exposure sheets
def P(gl=0, gh=0, gf=0, ol=0, oh=0, of=0, turn=0, tilt=0):
    """G: lean + toward her, head + nods in, fore - raises.  O: lean + recoils, head + back, fore + raises."""
    return {"gustave": {"lean": gl, "head": gh, "fore": gf},
            "odette": {"lean": -ol * -1, "head": -oh * -1, "fore": of, "turn": turn, "tilt": tilt}}


NEUTRAL = P()
# H: heads swing in (6 drawings), hold, the note turns over 6 drawings while he points, face-out, recoil + settle
H_SHEET = (
    [P(0, 0, 0, 0, 0, 0)] +
    [P(0.25 * k, 1.1 * k, 0, -0.2 * k, -1.1 * k, 3 * k) for k in range(1, 6)] + [P(1.5, 6.6, 0, -1.2, -6.4, 16)] +  # swing in (overshoot)
    [P(1.4, 5.5, 0, -1.0, -5.5, 15)] * 5 +                                       # hold 26.5-27.0
    [P(1.4, 5.5, -4, -1.0, -5.5, 18, 30, -4), P(1.4, 5.5, -8, -1.0, -5.5, 21, 30, -4),
     P(1.5, 5.5, -12, -1.0, -5.5, 24, 60, -4), P(1.5, 5.5, -15, -1.0, -5.5, 27, 60, -4),
     P(1.6, 5.5, -18, -1.0, -5.5, 30, 90, -4), P(1.6, 5.5, -19, -1.0, -5.5, 31, 90, -4),
     P(1.6, 5.0, -20, -1.0, -5.0, 32, 120, -4), P(1.6, 5.0, -20, -1.0, -5.0, 33, 120, -4),
     P(1.7, 5.0, -21, -1.0, -5.0, 34, 150, -4), P(1.7, 5.0, -21, -1.0, -5.0, 34, 150, -4),
     P(1.7, 4.5, -22, -1.0, -5.0, 35, 165, -4), P(1.7, 4.5, -22, -1.0, -5.0, 35, 165, -4)] +  # 27.0-28.0 (on 2s, note on 4s)
    []
)
FACE_OUT_DRAWING = len(H_SHEET)  # this drawing is the face-out: ground cuts to black, bell
H_SHEET += [P(1.7, 4.5, -22, -1.0, -5.0, 35, 180, -4),           # 28.0 face-out
            P(1.7, 4.5, -22, -0.3, -2.0, 35, 180, -4),           # recoil starts (body leads)
            P(1.7, 4.5, -22, 0.9, 2.0, 34, 180, -4),
            P(1.7, 4.5, -22, 1.9, 6.0, 33, 180, -4),
            P(1.7, 4.5, -22, 2.2, 9.5, 33, 180, -4),             # head lags a drawing: overshoot
            P(1.7, 4.5, -22, 2.0, 8.5, 33, 180, -4),
            P(1.7, 4.5, -22, 1.9, 7.5, 33, 180, -4)]             # settle -> canonical H
H_CANON = H_SHEET[-1]
H_BALLOON_DRAWING = FACE_OUT_DRAWING + 6                      # 28.5 s

B_SHEET = [P(), P(),
           P(0.4, 2, 0, 0, 0, 0),                             # anticipation: he dips
           P(-0.8, -3, -14, 0, 1, -2),                        # jerk back (body leads)
           P(-2.0, -9, -34, 0, 2, -5),
           P(-2.6, -13, -48, 0, 3, -8),                       # head lags: overshoot nose-up, palm out
           P(-2.3, -11, -44, 0, 4, -10),
           P(-1.9, -8, -38, 0, 4, -11),
           P(-2.0, -9.5, -40, 0, 4, -10),
           ] + [P(-2.0, -9, -40, 0, 4, -10)] * 9             # canonical B held (18 drawings = 1.5 s)
B_CANON = B_SHEET[-1]
B_BALLOON_DRAWING = 5
A_CANON = P(0.5, -4, 4, -1.2, -6, 30, 0, -8)
C_CANON = P(-1.0, -6, 8, -2.6, -8, 22, 0, -6)
CANON = {"A": A_CANON, "B": B_CANON, "C": C_CANON, "H": H_CANON}

# panel framing: page px per thumb px and offset; heads in the middle third, figures >= 60 % of height
FRAME = {"small": (1.10, 425 - 495 * 1.10, 200 - 296 * 1.10), "H": (1.30, 1500 - 495 * 1.30, 66 - 296 * 1.30)}

# the print's dark backdrop, cut as a spot-black collage piece behind the heads (A B C only)
BACK_POLY = [(168, 300), (240, 268), (330, 254), (450, 250), (560, 252), (650, 262), (684, 300), (690, 470), (676, 560),
             (560, 556), (420, 552), (300, 556), (200, 548), (160, 520)]
_back_cache = {}


def backdrop(frame, w, h):
    key = (frame, w, h)
    if key in _back_cache:
        return _back_cache[key]
    src = cv2.imread(os.path.join(ROOT, CJ["source"]), cv2.IMREAD_COLOR)
    lum = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32)
    tone = np.clip((lum - CJ["levels"]["black_point"]) / (CJ["levels"]["white_point"] - CJ["levels"]["black_point"]), 0, 1)
    tone = INK + tone * (PAGE - INK)
    m = np.zeros(lum.shape, np.uint8)
    pts = np.round(np.array(BACK_POLY) * K).astype(np.int32)
    cv2.fillPoly(m, [pts], 255)
    figs = np.zeros_like(m)
    for f in ("gustave", "odette"):
        mm = cv2.imread(os.path.join(CUT, f"matte_{f}_tonal.png"), 0)
        figs |= mm
    figs = cv2.dilate(figs, np.ones((int(9 * K) | 1,) * 2, np.uint8))
    tone[figs > 0] = INK  # under the figures the wall is solid ink (it is already ink around them)
    s, ox, oy = frame
    M = A_ts(s / K, ox, oy)[:2]
    g = cv2.warpAffine(tone, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=PAGE)
    a = cv2.warpAffine(m.astype(np.float32) / 255, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    _back_cache[key] = (g, a)
    return g, a


_panel_cache = {}


def render_panel(key, pose, black=False):
    """One drawing of one panel at page scale (gray float)."""
    x0, y0, x1, y1 = RECTS[3] if key == "H" else RECTS[0]
    w, h = x1 - x0, y1 - y0
    fr = FRAME["H" if key == "H" else "small"]
    ck = (key, json.dumps(pose, sort_keys=True), black)
    if ck in _panel_cache:
        return _panel_cache[ck]
    cv_ = np.full((h, w), float(INK if black else PAGE), np.float32)
    cov = np.zeros((h, w), np.float32)
    if key != "H":
        g, a = backdrop(fr, w, h)
        cv_[:] = cv_ * (1 - a) + g * a
        # a hand-inked floor line where the panel is cut at the hip
    Ms = fk(pose, fr)
    order = [("gustave", "body"), ("gustave", "head"), ("odette", "body"), ("odette", "head"), ("odette", "fore")]
    for fig, pn in order:
        warp_piece(cv_, cov, f"{fig}_{pn}", Ms[f"{fig}_{pn}"])
    warp_piece(cv_, cov, "gustave_fore", Ms["gustave_fore"])  # his pointing hand, under the note's edge
    draw_note(cv_, cov, Ms, pose, fr[0])
    out = np.clip(cv_, 0, 255)
    _panel_cache[ck] = (out, Ms)
    return out, Ms


# ---------------------------------------------------------------- lettering: balloons, borders, furniture (pen)
SS = 3


def balloon_masks(key, cx, cy, cap, maxw, tail, seed=None):
    """Hand-lettered oval balloon with a pointed tail. Returns (box, fill, ink) at page scale."""
    speaker, text = TEXT[key]
    seed = seed if seed is not None else sum(map(ord, key + text))
    lines = kc.wrap_words(text, cap, maxw)
    lh = cap * 1.5
    tw = max(kc.text_width(l, cap) for l in lines)
    th = lh * len(lines) - (lh - cap)
    rx, ry = tw / 2 + cap * 1.25, th / 2 + cap * 1.0
    pad = 30
    bx0 = int(min(cx - rx, tail[0]) - pad)
    by0 = int(min(cy - ry, tail[1]) - pad)
    bx1 = int(max(cx + rx, tail[0]) + pad)
    by1 = int(max(cy + ry, tail[1]) + pad)
    bw, bh = bx1 - bx0, by1 - by0
    fill = Image.new("L", (bw * SS, bh * SS), 0)
    line = Image.new("L", (bw * SS, bh * SS), 0)
    df, dl = ImageDraw.Draw(fill), ImageDraw.Draw(line)
    rs = random.Random(seed)
    lcx, lcy = (cx - bx0) * SS, (cy - by0) * SS
    ph = rs.uniform(0, 6.28)
    pts = []
    for a in np.linspace(0, 2 * math.pi, 120, endpoint=False):
        r = 1 + 0.03 * math.sin(3 * a + ph) + 0.015 * math.sin(5 * a + 2 * ph)
        ca, sa = math.cos(a), math.sin(a)
        e = 2.3
        px = abs(ca) ** (2 / e) * (1 if ca >= 0 else -1)
        py = abs(sa) ** (2 / e) * (1 if sa >= 0 else -1)
        pts.append((lcx + px * rx * SS * r, lcy + py * ry * SS * r))
    tx, ty = (tail[0] - bx0) * SS, (tail[1] - by0) * SS
    ang = math.atan2(ty - lcy, tx - lcx)
    k = min(range(len(pts)), key=lambda i: abs((math.atan2(pts[i][1] - lcy, pts[i][0] - lcx) - ang + math.pi) % (2 * math.pi) - math.pi))
    n = len(pts)
    a0, a1 = pts[(k - 3) % n], pts[(k + 3) % n]
    body = [pts[(k + 3 + j) % n] for j in range(n - 6)]
    shape = body + [a0, (tx, ty), a1]
    pen = 4.6 * SS
    df.polygon(shape, fill=255)
    dl.line(shape + [shape[0]], fill=255, width=int(pen), joint="curve")
    y = lcy - th / 2 * SS
    for i, l in enumerate(lines):
        lw = kc.text_width(l, cap) * SS
        kc.ink_text(line, lcx - lw / 2, y, l, cap=cap * SS, seed=seed + i * 13, pen=int(cap * 0.24 * SS))
        y += lh * SS
    f = np.asarray(fill.resize((bw, bh), Image.LANCZOS), np.float32) / 255
    i_ = np.asarray(line.resize((bw, bh), Image.LANCZOS), np.float32) / 255
    return (bx0, by0), f, i_


def wobbly_border(mask, r, width, seed):
    d = ImageDraw.Draw(mask)
    rs = random.Random(seed)
    x0, y0, x1, y1 = [v * SS for v in r]
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        L = math.hypot(bx - ax, by - ay)
        for t in np.linspace(0, 1, max(4, int(L / (90 * SS))), endpoint=False):
            pts.append((ax + (bx - ax) * t + rs.uniform(-1.2, 1.2) * SS, ay + (by - ay) * t + rs.uniform(-1.2, 1.2) * SS))
    d.line(pts + [pts[0]], fill=255, width=int(width * SS), joint="curve")


def furniture_mask():
    m = Image.new("L", (PW * SS, PH * SS), 0)
    for i in range(7):
        wobbly_border(m, RECTS[i], 6.5 if i != 3 else 7.5, seed=100 + i)
    it = kc.ink_text
    it(m, 46 * SS, 70 * SS, "LE MOT", cap=124 * SS, seed=3, pen=int(19 * SS), slant=0.1)
    it(m, 52 * SS, 262 * SS, "OU QUI L'A", cap=50 * SS, seed=4, pen=int(9 * SS))
    it(m, 52 * SS, 340 * SS, "LAISSÉ ?", cap=50 * SS, seed=5, pen=int(9 * SS))
    d = ImageDraw.Draw(m)
    pts = kc._arc(270 * SS, 960 * SS, 150 * SS, 430 * SS, -80, 262, 90)
    rs = random.Random(9)
    pts = [(x + rs.uniform(-1.5, 1.5) * SS, y + rs.uniform(-1.5, 1.5) * SS) for x, y in pts]
    d.line(pts, fill=255, width=int(7 * SS), joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex - 26 * SS, ey + 16 * SS), (ex + 24 * SS, ey + 10 * SS), (ex + 4 * SS, ey - 36 * SS)], fill=255)
    for i, k in enumerate(SEQ):
        it(m, (60 + i * 64) * SS, 1530 * SS, k, cap=44 * SS, seed=40 + i, pen=int(8 * SS))
    it(m, 54 * SS, 1640 * SS, "ÉTUDE · OUBAPO", cap=30 * SS, seed=60, pen=int(5.5 * SS))
    it(m, 54 * SS, 1705 * SS, "D'APRÈS DAUMIER, 1839", cap=22 * SS, seed=61, pen=int(4 * SS))
    ids = Image.new("L", (PW * SS, PH * SS), 0)
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = RECTS[i]
        it(ids, (x1 - 26) * SS, (y1 + 6) * SS, k, cap=17 * SS, seed=90 + i, pen=int(3 * SS))
    a = np.asarray(m.resize((PW, PH), Image.LANCZOS), np.float32) / 255
    b = np.asarray(ids.resize((PW, PH), Image.LANCZOS), np.float32) / 255 * 0.75
    return np.maximum(a, b)


# balloon placement per panel ID: centre (panel-relative fraction), cap, max width
BAL = {"A": dict(c=(0.62, 0.17), cap=34, maxw=520, who="odette"),
       "B": dict(c=(0.36, 0.17), cap=34, maxw=520, who="gustave"),
       "C": dict(c=(0.66, 0.15), cap=36, maxw=480, who="odette"),
       "H": dict(c=(0.375, 0.25), cap=38, maxw=560, who="gustave")}


def balloon_for(i, key):
    x0, y0, x1, y1 = RECTS[i]
    w, h = x1 - x0, y1 - y0
    b = BAL[key]
    _, Ms = render_panel(key, CANON[key], black=(key == "H"))
    mx, my = apply(Ms[f"{b['who']}_head"], MOUTH[b["who"]])
    cx, cy = x0 + w * b["c"][0], y0 + h * b["c"][1]
    if key != "H":
        cy = y0 + 22 + h * b["c"][1]
    if b["who"] == "gustave":  # tails touch his cheek, never cross the face
        mx, my = apply(Ms["gustave_head"], (446 * K, 300 * K))
    else:
        mx, my = apply(Ms["odette_head"], (606 * K, 318 * K))
    tail = (x0 + mx, y0 + my - 14)
    if key == "H":  # the wide hinge: the tail comes in from the left to the back of his cap
        mx, my = apply(Ms["gustave_head"], (392 * K, 352 * K))
        tail = (x0 + mx - 12, y0 + my)
    return balloon_masks(key, cx, cy, b["cap"], b["maxw"], tail)


# ---------------------------------------------------------------- page composition
FURN = None
BALLOONS = {}


def compose(state):
    """state[i] = (pose, black, ghost, balloon_on).  Returns the page as gray float."""
    global FURN
    if FURN is None:
        FURN = furniture_mask()
    page = np.full((PH, PW), float(PAGE), np.float32)
    for i in range(7):
        key = SEQ[i]
        pose, black, ghost, bal = state[i]
        x0, y0, x1, y1 = RECTS[i]
        tile, _ = render_panel(key, pose, black)
        if ghost:
            tile = PAGE - (PAGE - tile) * 0.22
        page[y0:y1, x0:x1] = tile
    page = page * (1 - FURN) + INK * FURN
    for i in range(7):
        key = SEQ[i]
        pose, black, ghost, bal = state[i]
        if not bal:
            continue
        if i not in BALLOONS:
            BALLOONS[i] = balloon_for(i, key)
        (bx, by), f, ink = BALLOONS[i]
        k = 0.22 if ghost else 1.0
        sl = (slice(by, by + f.shape[0]), slice(bx, bx + f.shape[1]))
        page[sl] = page[sl] * (1 - f * k) + 255 * f * k
        page[sl] = page[sl] * (1 - ink * k) + INK * ink * k
    return page


def final_state():
    return {i: (CANON[SEQ[i]], SEQ[i] == "H", False, True) for i in range(7)}


def to_img(page):
    return Image.fromarray(np.clip(page + 0.5, 0, 255).astype(np.uint8), "L")


if __name__ == "__main__" and "--page" in sys.argv:
    to_img(compose(final_state())).save(os.path.join(SWARM, "test-page.png"))
    print("page written")
