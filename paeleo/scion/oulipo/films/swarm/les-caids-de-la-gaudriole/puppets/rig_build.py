"""U2 panel artist + puppet fabricator: articulated Busch cutouts, pen furniture,
rest-pose strip art, per-exposure poses (shots 2-3) and seam checks.

Coordinates: sheet units u (1 u = 0.1 mm), 2400 x 900, frozen in strip/sheet.json rev 1.
Every part is a paper cutout: an ink layer (darkness 0..1) and a card matte (0..1).
Compositing per part (SCION #45): the card first covers what lies behind it (holdout),
then its ink darkens.  Parts hang in a joint tree (SCION #8 constraints): each part's
world transform = parent world @ L2P @ R(pivot, angle - base).  The rest pose is the
printed pose; art-layers.png IS render(rest).

Sources (foraged, read-only, decoded with PIL only): Wilhelm Busch, Max und Moritz
(1865) plates 082 (miller), 031 (farmer -> porter), 001 (the boys), Wikimedia Commons, PD.
Handmade here: pen sleeves (miller extension, porter striped forearm), bit-key, floor
lines and boards, the closed service door, balloons, lettering (strip/pen.py), frames,
fold marks.
"""
import os, sys, json, math, random, hashlib
import numpy as np
import cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
STRIP = os.path.join(WS, "strip")
sys.path.insert(0, STRIP)
from pen import pen, text_width  # noqa: E402

ROOT = os.path.normpath(os.path.join(WS, "../../.."))            # oulipo/
SRC = os.path.join(ROOT, "films/sources/les-caids-de-la-gaudriole")
BUSCH = os.path.join(SRC, "busch")
MEDIA = os.path.join(SRC, "panel-artist")
EDITOR = os.path.join(SRC, "panel-artist-puppet-fabricator")
PARTS_DIR = os.path.join(HERE, "parts")
for d_ in (MEDIA, EDITOR, PARTS_DIR):
    os.makedirs(d_, exist_ok=True)

SHEET = json.load(open(os.path.join(STRIP, "sheet.json")))
SW, SH = SHEET["W"], SHEET["H"]
A, M, B, D = SHEET["A"], SHEET["M"], SHEET["B"], SHEET["D"]
P1 = tuple(SHEET["panels"]["P1"]["x"]); P2 = tuple(SHEET["panels"]["P2"]["x"])
PY0, PY1 = SHEET["panels"]["P1"]["y"]
LINE_Y = SHEET["LINE_Y"]; CAP = SHEET["cap_u"]; GAP = SHEET["fragment_gap_u"]
INK = 18
INKF = 1 - INK / 255.0            # darkness of full pen ink


# ------------------------------------------------------------------ pen tools
def wobble_line(d, pts, w=5, seed=0, ink=INK, jit_amp=0.12):
    rnd = random.Random(seed)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        n = max(2, int(math.hypot(bx - ax, by - ay) / 1.5))
        jit = 0
        for k in range(n + 1):
            t = k / n
            jit = 0.97 * jit + rnd.uniform(-jit_amp, jit_amp)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = -(by - ay), (bx - ax)
            L = math.hypot(nx, ny) or 1
            x += nx / L * jit; y += ny / L * jit
            r = w / 2 * (0.85 + 0.3 * math.sin(math.pi * t))
            d.ellipse([x - r, y - r, x + r, y + r], fill=ink)


def taper_stroke(d, pts, w0, w1, seed=0, ink=INK):
    """Busch-like hatch stroke: swells then tapers to a point."""
    rnd = random.Random(seed)
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])) or 1
    acc = 0
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        n = max(2, int(seg / 0.8))
        for k in range(n + 1):
            t = (acc + seg * k / n) / L
            x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
            r = (w0 + (w1 - w0) * t) / 2 * (0.6 + 0.6 * math.sin(math.pi * min(1, t * 1.15)))
            r = max(0.5, r + rnd.uniform(-0.1, 0.1))
            d.ellipse([x - r, y - r, x + r, y + r], fill=ink)
        acc += seg


def rr_pts(x0, y0, x1, y1, r, steps=10):
    pts = []
    for cx, cy, a0 in [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]:
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


# ------------------------------------------------------------------ affine helpers
def T(tx, ty):
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], float)


def S(sx, sy=None):
    sy = sx if sy is None else sy
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], float)


def R(deg, cx=0.0, cy=0.0):
    """Visual counter-clockwise rotation by deg about (cx, cy) in y-down coordinates."""
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    r = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], float)
    return T(cx, cy) @ r @ T(-cx, -cy)


def ap(Mx, p):
    v = Mx @ np.array([p[0], p[1], 1.0])
    return (float(v[0]), float(v[1]))


# ------------------------------------------------------------------ source plates
def plate(n):
    return Image.open(os.path.join(BUSCH, f"mm_{n}.png")).convert("L")


def ink_of(img):
    a = 255 - np.asarray(img, dtype=np.float32)
    return np.clip((a - 25) * 1.25, 0, 255) / 255.0


def poly_mask(shape, poly, fill=1):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(m) > 0


def card_matte(ink, scissor, close=11):
    """Cut a card: close the drawn outline, fill holes, keep inside the scissor polygon."""
    b = ((ink > 0.35) & scissor).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, k)
    h, w = b.shape
    ff = np.pad(b, 1) * 255
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 128)
    filled = (ff[1:-1, 1:-1] != 128) & scissor
    filled = cv2.dilate(filled.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    filled = filled.astype(bool) & scissor
    return cv2.GaussianBlur(filled.astype(np.float32), (3, 3), 0)


# ------------------------------------------------------------------ parts
class Part:
    def __init__(self, name, ink, matte, origin, parent, L2P, pivot, base, rest, src, crop, made):
        self.name, self.ink, self.matte, self.origin = name, ink.astype(np.float32), matte.astype(np.float32), origin
        self.parent, self.L2P, self.pivot, self.base, self.rest = parent, L2P, pivot, base, rest
        self.src, self.crop, self.made = src, crop, made


PARTS = {}
ORDER = []


def add(p):
    PARTS[p.name] = p; ORDER.append(p.name)


def world(name, pose):
    p = PARTS[name]
    ang = pose.get(name, p.rest)
    Wp = world(p.parent, pose) if p.parent else np.eye(3)
    return Wp @ p.L2P @ R(ang - p.base, *p.pivot)


def rest_pose():
    return {n: PARTS[n].rest for n in ORDER}


def scaled(im, s):
    return im.resize((int(round(im.width * s)), int(round(im.height * s))), Image.LANCZOS)


# --- miller (plate 082) -------------------------------------------------------
MS = 1.0
M_CROP = (660, 100, 1140, 680)
M_BODY = [(672, 262), (690, 190), (760, 125), (860, 112), (960, 128), (1000, 145), (1040, 138), (1085, 150), (1112, 190),
          (1124, 250), (1122, 335), (1080, 350), (1078, 400), (1020, 420), (985, 440), (965, 520), (1010, 560),
          (1040, 590), (1035, 632), (960, 640), (920, 660), (780, 662), (760, 610), (728, 592), (730, 560), (800, 540),
          (780, 440), (770, 345), (700, 340), (668, 300)]
M_ARM = [(1004, 322), (1064, 316), (1071, 396), (1097, 414), (1110, 452), (1106, 482), (1058, 488),
         (1016, 472), (1012, 436), (1019, 410), (1010, 370)]
SHOULDER = (1036, 326)
WRIST_P = (1045, 400)                    # cuff point on the Busch arm (plate)
HAND_AXIS = (40, 84)                     # cuff -> fingertips in the plate
SHOULDER_REST = 52.0                     # printed rest (frozen by the director)
HAND_REST = 40.0                         # hand turned forward so it leads out of the sleeve

# --- porter (plate 031) -------------------------------------------------------
F_CROP = (140, 30, 570, 610)
F_BODY2 = [(150, 380), (200, 300), (205, 100), (245, 56), (320, 56), (345, 36), (420, 36), (455, 88), (492, 118),
           (498, 176), (470, 206), (450, 216), (444, 250), (438, 276), (440, 334), (420, 350), (408, 372),
           (440, 430), (470, 470), (552, 500), (552, 600), (150, 600)]
F_BODY1 = [(150, 380), (200, 300), (205, 100), (245, 56), (320, 56), (345, 36), (420, 36), (455, 88), (492, 118),
           (498, 176), (470, 206), (450, 216), (448, 250), (505, 255), (508, 340), (440, 345), (420, 350), (408, 372),
           (440, 430), (470, 470), (552, 500), (552, 600), (150, 600)]
F_STICK = [(560, 112), (585, 128), (452, 372), (418, 372), (430, 330)]
F_HEAD = [(330, 44), (420, 30), (462, 84), (498, 116), (504, 182), (472, 214), (446, 236), (400, 240), (356, 222),
          (334, 176)]
NECK = (405, 232)
ELBOW_TOP, ELBOW_BOT = (440, 279), (441, 331)   # end of the Busch striped sleeve (plate)


def build_parts():
    # ---------------- miller body + arm
    m_im = plate("082").crop(M_CROP)
    m_ink = ink_of(scaled(m_im, MS))
    sc = lambda pts: [((x - M_CROP[0]) * MS, (y - M_CROP[1]) * MS) for x, y in pts]
    arm_m = poly_mask(m_ink.shape, sc(M_ARM))
    arm_m = cv2.dilate(arm_m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    body_sc = poly_mask(m_ink.shape, sc(M_BODY)) & ~arm_m
    # split the arm at the cuff, on the line perpendicular to the hand's axis
    hx, hy = HAND_AXIS; hl = math.hypot(hx, hy); ux, uy = hx / hl, hy / hl
    wx, wy = sc([WRIST_P])[0]
    yy, xx = np.mgrid[0:m_ink.shape[0], 0:m_ink.shape[1]]
    beyond = ((xx - wx) * ux + (yy - wy) * uy) > 0
    sleeve_sc = arm_m & ~beyond
    hand_sc = arm_m & beyond
    body_mat = card_matte(m_ink, body_sc, 13)
    sleeve_mat = card_matte(m_ink, sleeve_sc, 7)
    hand_mat = card_matte(m_ink, hand_sc, 7)
    # cuff width: ink extent along the cut line
    nx, ny = -uy, ux
    ts = []
    for t in np.arange(-45, 45, 0.5):
        px, py = int(round(wx + nx * t)), int(round(wy + ny * t))
        if 0 <= py < m_ink.shape[0] and 0 <= px < m_ink.shape[1] and arm_m[py, px] and m_ink[py, px] > 0.35:
            ts.append(t)
    t0, t1 = min(ts), max(ts)
    cut_a = (wx + nx * t0, wy + ny * t0); cut_b = (wx + nx * t1, wy + ny * t1)

    # place the miller: hat brim 14 u left of A, feet on the panel bottom
    bx = [x for x, y in sc(M_BODY)]; by_ = [y for x, y in sc(M_BODY)]
    TX = (A - 14) - max(bx)
    TY = 842 - max(by_)
    add(Part("miller.body", m_ink * body_mat, body_mat, (0, 0), None, T(TX, TY), sc([(900, 650)])[0], 0, 0,
             "mm_082", M_CROP, "Busch plate cut with scissors (card silhouette), arm lifted away"))
    sh = sc([SHOULDER])[0]
    add(Part("miller.arm", m_ink * sleeve_mat, sleeve_mat, (0, 0), "miller.body", np.eye(3), sh, 0.0, SHOULDER_REST,
             "mm_082", M_CROP, "Busch upper sleeve, re-hinged at the shoulder (printed rest 52 deg)"))
    W_arm = world("miller.arm", {"miller.arm": SHOULDER_REST})
    E_a, E_b = ap(W_arm, cut_a), ap(W_arm, cut_b)
    E_c = ((E_a[0] + E_b[0]) / 2, (E_a[1] + E_b[1]) / 2)

    # hand rest in world: wrist at A + 22, at the cuff band y; turned HAND_REST deg forward
    Hw = (A + 22.0, E_c[1] + 18.0)
    W_hand_m = T(Hw[0] - wx, Hw[1] - wy) @ R(HAND_REST, wx, wy)
    H_a, H_b = ap(W_hand_m, cut_a), ap(W_hand_m, cut_b)
    return dict(m_ink=m_ink, hand_mat=hand_mat, wx=wx, wy=wy, E=(E_a, E_b), H=(H_a, H_b), Hw=Hw,
                W_hand_m=W_hand_m, cut=(cut_a, cut_b))


def pen_part(name, parent, size_box, draw_fn, pivot_world, rest=0.0, made="", fill_mask_fn=None):
    """A pen-drawn part drawn in world-rest coordinates inside size_box (x0,y0,x1,y1)."""
    x0, y0, x1, y1 = [int(v) for v in size_box]
    w, h = x1 - x0, y1 - y0
    ink = Image.new("L", (w, h), 255); card = Image.new("L", (w, h), 0)
    di, dc = ImageDraw.Draw(ink), ImageDraw.Draw(card)
    draw_fn(di, dc, x0, y0)
    inkf = (255 - np.asarray(ink, np.float32)) / 255.0
    cardf = cv2.GaussianBlur((np.asarray(card) > 0).astype(np.float32), (3, 3), 0)
    cardf = np.maximum(cardf, (inkf > 0.3).astype(np.float32))
    Wp = world(parent, rest_pose()) if parent else np.eye(3)
    add(Part(name, inkf * cardf, cardf, (x0, y0), parent, np.linalg.inv(Wp), pivot_world, rest, rest,
             "handmade", list(size_box), made))


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def build_all():
    g = build_parts()
    (E_a, E_b), (H_a, H_b) = g["E"], g["H"]
    # make (E_up, E_dn) / (H_up, H_dn) ordered top/bottom
    E_up, E_dn = sorted([E_a, E_b], key=lambda p: p[1])
    H_up, H_dn = sorted([H_a, H_b], key=lambda p: p[1])
    # shared end segment: Q at x = A - 20 on the straight line E -> H (each edge)
    def at_x(p, q, x):
        t = (x - p[0]) / (q[0] - p[0]); return (x, p[1] + (q[1] - p[1]) * t)
    Q_up, Q_dn = at_x(E_up, H_up, A - 20), at_x(E_dn, H_dn, A - 20)
    C_up, C_dn = at_x(E_up, H_up, A - 8), at_x(E_dn, H_dn, A - 8)     # cuff line
    g.update(Q=(Q_up, Q_dn), C=(C_up, C_dn), Eo=(E_up, E_dn), Ho=(H_up, H_dn))

    def end_segment(di, dc, ox, oy, dx):
        """The identical cuff band [Q..H] for both sleeves (shift dx = 0 or D)."""
        sh = lambda p: (p[0] + dx - ox, p[1] - oy)
        quad = [sh(C_up), sh(H_up), sh(H_dn), sh(C_dn)]
        dc.polygon(quad, fill=255); di.polygon(quad, fill=255)
        wobble_line(di, [sh(Q_up), sh(H_up)], w=5, seed=71)
        wobble_line(di, [sh(Q_dn), sh(H_dn)], w=5, seed=72)
        wobble_line(di, [sh(C_up), sh(C_dn)], w=4, seed=73)          # cuff seam line
        for kk in range(4):   # shadow ticks on the cuff's lower side (same on both sleeves)
            tt = 0.2 + kk * 0.2
            pa = lerp(lerp(C_up, H_up, tt), lerp(C_dn, H_dn, tt), 0.62)
            pb = lerp(lerp(C_up, H_up, tt + 0.08), lerp(C_dn, H_dn, tt + 0.08), 0.9)
            taper_stroke(di, [sh(pa), sh(pb)], 1.0, 2.2, seed=740 + kk)

    # -------- miller sleeve extension (pen): dark Busch sleeve to the cuff, then the shared band
    def draw_msleeve(di, dc, ox, oy):
        o = lambda p: (p[0] - ox, p[1] - oy)
        quad = [o(E_up), o(C_up), o(C_dn), o(E_dn)]
        dc.polygon(quad + [o(E_up)], fill=255)
        di.polygon(quad, fill=255)
        # Busch's coat-sleeve hatching: dense diagonal strokes, heavier toward the shadow (lower) side
        rnd = random.Random(80)
        Lm = math.hypot(C_up[0] - E_up[0], C_up[1] - E_up[1])
        n = max(3, int(Lm / 4.2))
        for k in range(n + 1):
            t = k / n
            pu = lerp(E_up, C_up, min(1, t)); pd = lerp(E_dn, C_dn, min(1, t))
            a = lerp(pu, pd, 0.18 + rnd.uniform(0, 0.12)); b = lerp(pu, pd, 0.98)
            b = (b[0] - 5, b[1])
            taper_stroke(di, [o(a), o(b)], 0.8, 3.0 + rnd.uniform(-0.3, 0.4), seed=800 + k)
        wobble_line(di, [o(E_up), o(Q_up)], w=5, seed=75)
        wobble_line(di, [o(E_dn), o(Q_dn)], w=5, seed=76)
        end_segment(di, dc, ox, oy, 0)
    xs = [E_up[0], E_dn[0], H_up[0], H_dn[0]]; ys = [E_up[1], E_dn[1], H_up[1], H_dn[1]]
    box = (min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12)
    E_c = lerp(E_up, E_dn, 0.5)
    pen_part("miller.forearm", "miller.arm", box, draw_msleeve, E_c, 0.0,
             "pen-drawn sleeve extension (black coat with Busch-style white streaks) ending in the shared cuff band at A")

    # -------- hands (Busch hand cut from plate 082, two prints of the same cut)
    hm = g["hand_mat"]
    hand_ink = g["m_ink"] * hm
    wx, wy = g["wx"], g["wy"]
    for nm, parent, dx in [("miller.hand", "miller.forearm", 0), ("porter.hand", "porter.forearm", D)]:
        if parent not in PARTS:
            continue
        Wp = world(parent, rest_pose())
        L2P = np.linalg.inv(Wp) @ T(g["Hw"][0] + dx - wx, g["Hw"][1] - wy)
        add(Part(nm, hand_ink, hm, (0, 0), parent, L2P, (wx, wy), 0.0, HAND_REST, "mm_082", M_CROP,
                 "Busch cuff + hand cut from the miller's arm (wrist joint)"))
        if nm == "miller.hand":
            # porter needs its own body/forearm first
            build_porter(g)
    return g


def build_porter(g):
    (Q_up, Q_dn), (C_up, C_dn), (E_up, E_dn), (H_up, H_dn) = g["Q"], g["C"], g["Eo"], g["Ho"]
    f_im = plate("031").crop(F_CROP)
    f_ink = ink_of(f_im)
    sc = lambda pts: [(x - F_CROP[0], y - F_CROP[1]) for x, y in pts]
    stick = poly_mask(f_ink.shape, sc(F_STICK))
    f_ink2 = f_ink * (~stick)
    # ---- porter P2: elbow placed so that the forearm runs straight into the shared cuff band at B
    body2 = poly_mask(f_ink.shape, sc(F_BODY2))
    mat2 = card_matte(f_ink2, body2, 13)
    el_top, el_bot = sc([ELBOW_TOP])[0], sc([ELBOW_BOT])[0]
    el_c = lerp(el_top, el_bot, 0.5)
    q_c = lerp(Q_up, Q_dn, 0.5); q_c = (q_c[0] + D, q_c[1])
    slope = (H_up[1] - E_up[1] + H_dn[1] - E_dn[1]) / (H_up[0] - E_up[0] + H_dn[0] - E_dn[0])
    xs_b = [x for x, y in sc(F_BODY2)]
    TXp = (B - 14) - max(xs_b)
    elw_x = el_c[0] + TXp
    TYp = (q_c[1] - slope * (q_c[0] - elw_x)) - el_c[1]
    add(Part("porter.body", f_ink2 * mat2, mat2, (0, 0), None, T(TXp, TYp), (el_c[0], 560 - F_CROP[1]), 0, 0,
             "mm_031", F_CROP, "Busch farmer as the porter; stick and stick-hand cut away"))
    Wb = world("porter.body", rest_pose())
    ET, EB = ap(Wb, el_top), ap(Wb, el_bot)
    ELB = lerp(ET, EB, 0.5)
    Qu, Qd = (Q_up[0] + D, Q_up[1]), (Q_dn[0] + D, Q_dn[1])
    ET, EB = lerp(Qu, ET, 1.07), lerp(Qd, EB, 1.07)

    def draw_pforearm(di, dc, ox, oy):
        o = lambda p: (p[0] - ox, p[1] - oy)
        top = [ET, lerp(ET, Qu, 0.5), Qu]; bot = [EB, lerp(EB, Qd, 0.5), Qd]
        # slight muscle swell on the underside
        mid = lerp(EB, Qd, 0.45); bot[1] = (mid[0], mid[1] + 5)
        poly = [o(p) for p in top] + [o(p) for p in reversed(bot)]
        dc.polygon(poly, fill=255); di.polygon(poly, fill=255)
        wobble_line(di, [o(p) for p in top], w=5.5, seed=41)
        wobble_line(di, [o(p) for p in bot], w=6.5, seed=42)
        # Busch knit ribbing as on the farmer's own sleeve: close parallel stripes (~5 u), edge to
        # edge, swelling toward the shadow side so the arm reads round, not as a ladder
        L = math.hypot(Qu[0] - ET[0], Qu[1] - ET[1])
        n = int(L / 5.2)
        rnd = random.Random(7)
        for k in range(1, n):
            t = k / n
            if t > 0.95:
                break
            pu, pd = lerp(ET, Qu, t), lerp(EB, Qd, t)
            if 0.3 < t < 0.6:
                pd = (pd[0], pd[1] + 5 * math.sin(math.pi * (t - 0.3) / 0.3))
            a = lerp(pu, pd, 0.06 + rnd.uniform(0, 0.05)); b = lerp(pu, pd, 0.97)
            midp = lerp(a, b, 0.5); midp = (midp[0] + 1.2, midp[1])
            taper_stroke(di, [o(a), o(midp), o(b)], 1.2, 3.0 + rnd.uniform(-0.3, 0.4), seed=100 + k)
        # cuff band identical to the miller's (shared end segment, shifted by D)
        sh = lambda p: (p[0] + D - ox, p[1] - oy)
        quad = [sh(C_up), sh(H_up), sh(H_dn), sh(C_dn)]
        dc.polygon(quad, fill=255); di.polygon(quad, fill=255)
        wobble_line(di, [sh(Q_up), sh(H_up)], w=5, seed=71)
        wobble_line(di, [sh(Q_dn), sh(H_dn)], w=5, seed=72)
        wobble_line(di, [sh(C_up), sh(C_dn)], w=4, seed=73)
        for kk in range(4):   # shadow ticks on the cuff's lower side (same on both sleeves)
            tt = 0.2 + kk * 0.2
            pa = lerp(lerp(C_up, H_up, tt), lerp(C_dn, H_dn, tt), 0.62)
            pb = lerp(lerp(C_up, H_up, tt + 0.08), lerp(C_dn, H_dn, tt + 0.08), 0.9)
            taper_stroke(di, [sh(pa), sh(pb)], 1.0, 2.2, seed=740 + kk)
    xs = [ET[0], EB[0], H_up[0] + D, H_dn[0] + D]; ys = [ET[1], EB[1], H_up[1], H_dn[1]]
    box = (min(xs) - 14, min(ys) - 14, max(xs) + 14, max(ys) + 16)
    pen_part("porter.forearm", "porter.body", box, draw_pforearm, ELB, 0.0,
             "pen-drawn striped forearm (Busch knit ribbing + underside hatching), elbow joint at the Busch sleeve end")
    g["porter_elbow"] = ELB
    # ---- porter P1 (flipped, smaller) with a separate head on a neck joint
    s1 = 0.75
    body1 = poly_mask(f_ink.shape, sc(F_BODY1))
    head = poly_mask(f_ink.shape, sc(F_HEAD))
    mat1 = card_matte(f_ink2, body1 & ~head, 13)
    math_ = card_matte(f_ink2, head, 9)
    W1 = 1164.0
    flipT = T(W1, 846 - (600 - F_CROP[1]) * s1) @ S(-s1, s1) @ T(-(150 - F_CROP[0]), 0)
    add(Part("porter1.body", f_ink2 * mat1, mat1, (0, 0), None, flipT, (400 - F_CROP[0], 560 - F_CROP[1]), 0, 0,
             "mm_031", F_CROP, "Busch farmer, mirrored, as the porter listening in P1"))
    add(Part("porter1.head", f_ink2 * math_, math_, (0, 0), "porter1.body", np.eye(3), sc([NECK])[0], 0, 0,
             "mm_031", F_CROP, "Busch farmer's head and cap, cut at the neck (neck joint)"))


def build_key(g):
    """Pen-drawn bit-key hanging from the porter's fingers (pendulum)."""
    Wh = world("porter.hand", rest_pose())
    # hang point: between the first two fingers of the Busch hand (plate coords)
    hang = ap(Wh, ((1080 - M_CROP[0]) * MS, (470 - M_CROP[1]) * MS))
    kx, ky = hang

    def draw_key(di, dc, ox, oy):
        x, y = kx - ox, ky - oy + 16
        r = 16
        dc.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=255)
        dc.rectangle([x - 9, y + r - 2, x + 28, y + r + 96], fill=255)
        di.ellipse([x - r, y - r, x + r, y + r], fill=255)
        wobble_line(di, [(x + r * math.cos(2 * math.pi * k / 40), y + r * math.sin(2 * math.pi * k / 40)) for k in range(41)], w=5.5, seed=5)
        wobble_line(di, [(x + 6.5 * math.cos(2 * math.pi * k / 24), y + 6.5 * math.sin(2 * math.pi * k / 24)) for k in range(25)], w=3.5, seed=6)
        # Busch shading on the bow: crescent hatch on the lower right
        for k in range(5):
            a0 = math.radians(10 + k * 16); a1 = a0 + math.radians(10)
            p = (x + 10 * math.cos(a0), y + 10 * math.sin(a0)); q = (x + 14 * math.cos(a1), y + 14 * math.sin(a1))
            taper_stroke(di, [p, q], 1.0, 2.0, seed=9 + k)
        L = 88
        top = y + r
        wobble_line(di, [(x - 4, top), (x - 4, top + L)], w=4, seed=12)
        wobble_line(di, [(x + 4, top), (x + 4, top + L - 30)], w=4, seed=13)
        wobble_line(di, [(x + 4, top + L - 30), (x + 24, top + L - 30), (x + 24, top + L - 17), (x + 15, top + L - 17),
                         (x + 15, top + L - 8), (x + 24, top + L - 8), (x + 24, top + L), (x - 4, top + L)], w=4, seed=14)
        # shaft shading: a hairline down the shadow side, short ticks on the bit
        taper_stroke(di, [(x + 1.5, top + 6), (x + 1.5, top + L - 34)], 1.6, 0.8, seed=15)
        for k in range(3):
            taper_stroke(di, [(x + 8 + k * 5, top + L - 26), (x + 6 + k * 5, top + L - 21)], 1.6, 1.0, seed=16 + k)
        di.ellipse([x - 2.5, y - r - 3, x + 2.5, y - r + 2], fill=INK)   # the ring through the fingers
    box = (kx - 30, ky - 12, kx + 40, ky + 16 + 16 + 100)
    pen_part("porter.key", "porter.hand", box, draw_key, hang, 0.0,
             "pen-drawn brass bit-key, hung from the porter's fingers as a pendulum")
    g["key_hang"] = hang


def build_boys():
    im = plate("001"); w, h = im.size
    crop = (int(w * 0.05), int(h * 0.12), int(w * 0.97), int(h * 0.88))
    s = 0.4
    k = ink_of(scaled(im.crop(crop), s))
    hh, ww = k.shape
    scissor = np.ones_like(k, bool)
    b = (k > 0.35).astype(np.uint8)
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    ff = np.pad(b, 1) * 255
    mask = np.zeros((hh + 4, ww + 4), np.uint8)
    for sx, sy in [(0, 0), (ww + 1, 0)]:
        if ff[sy, sx] == 0:
            cv2.floodFill(ff, mask, (sx, sy), 128)
    filled = (ff[1:-1, 1:-1] != 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(filled)
    keep = np.zeros_like(filled)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > 4000:
            keep[lab == i] = 1
    mat = cv2.GaussianBlur(keep.astype(np.float32), (3, 3), 0)
    X0 = P2[1] - ww - 10; Y0 = PY1 - hh - 2
    add(Part("boys", k * mat, mat, (0, 0), None, T(X0, Y0), (ww / 2, hh), 0, 0, "mm_001", list(crop),
             "Busch's Max and Moritz, cut as one card"))


# ------------------------------------------------------------------ static pen layers
def draw_back(d):
    """Behind the figures: floor lines + boards (both panels share y at A and B) and the service door."""
    for (x0, x1), sd in [(P1, 3), (P2, 4)]:
        fl = SHEET["floor_lines"]["P1" if x0 == P1[0] else "P2"]
        wobble_line(d, [tuple(fl[0]), tuple(fl[1])], w=3.4, seed=sd, jit_amp=0.06)
        # second board line, same in both panels
        wobble_line(d, [(x0 + 10, 824), (x1 - 10, 827)], w=2.2, seed=sd + 10, jit_amp=0.06)
        rnd = random.Random(sd)
        # board joints: short perspective strokes, never within 16 u of a crease
        for k in range(14):
            xx = x0 + 40 + k * (x1 - x0 - 80) / 13 + rnd.uniform(-12, 12)
            if min(abs(xx - A), abs(xx - B), abs(xx - M)) < 22:
                continue
            taper_stroke(d, [(xx, 797), (xx - 10 - 0.012 * (xx - x0), 821)], 2.4, 1.0, seed=500 + k + sd * 50)
            if k % 3 == 1:
                taper_stroke(d, [(xx + 30, 830), (xx + 22, 846)], 2.0, 0.8, seed=700 + k + sd * 50)
    # the closed service door behind the porter (P2, left), Busch-style
    x0, x1, y0, y1 = 1246, 1392, 318, 791
    wobble_line(d, [(x0 - 12, y1), (x0 - 12, y0 - 12), (x1 + 12, y0 - 12), (x1 + 12, y1)], w=5, seed=601, jit_amp=0.05)
    wobble_line(d, [(x0, y1), (x0, y0), (x1, y0), (x1, y1)], w=4, seed=602, jit_amp=0.05)
    # frame shading: dense vertical hatch in the jamb gap on the shadow (right) side
    for k in range(5):
        xx = x1 + 3 + k * 2.0
        taper_stroke(d, [(xx, y0 - 6), (xx, y1 - 4)], 1.2, 1.2, seed=610 + k)
    # lintel hatching
    for k in range(int((x1 - x0 + 20) / 6)):
        xx = x0 - 8 + k * 6
        taper_stroke(d, [(xx, y0 - 9), (xx + 4, y0 - 3)], 1.4, 0.8, seed=630 + k)
    # two recessed panels, shaded on their upper-left inner edges
    for (py0, py1) in [(y0 + 30, y0 + 200), (y0 + 236, y1 - 40)]:
        px0, px1 = x0 + 22, x1 - 22
        wobble_line(d, [(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], w=3, seed=640 + py0, jit_amp=0.05)
        for k in range(int((py1 - py0) / 9)):
            yy = py0 + 6 + k * 9
            taper_stroke(d, [(px0 + 3, yy), (px0 + 11, yy + 5)], 1.6, 0.8, seed=650 + k + py0)
        for k in range(int((px1 - px0) / 10)):
            xx = px0 + 8 + k * 10
            taper_stroke(d, [(xx, py0 + 3), (xx + 4, py0 + 9)], 1.4, 0.8, seed=680 + k + py0)
    # hinges (left), knob and keyhole (right): the door is shut and locked
    for hy in (y0 + 40, y1 - 60):
        d.rectangle([x0 + 2, hy, x0 + 16, hy + 26], fill=INK)
    kx, ky = x1 - 26, (y0 + y1) / 2 + 6
    wobble_line(d, [(kx + 9 * math.cos(2 * math.pi * k / 24), ky + 9 * math.sin(2 * math.pi * k / 24)) for k in range(25)], w=3.5, seed=690)
    d.ellipse([kx - 3, ky + 22, kx + 3, ky + 28], fill=INK)
    d.polygon([(kx - 2, ky + 26), (kx + 2, ky + 26), (kx + 3, ky + 36), (kx - 3, ky + 36)], fill=INK)
    # threshold shadow
    for k in range(int((x1 - x0) / 7)):
        xx = x0 + 4 + k * 7
        taper_stroke(d, [(xx, y1 - 10), (xx + 5, y1 - 2)], 1.4, 0.8, seed=700 + k)


def balloon(d, x0, x1, y0, y1, tail, seed):
    d.rounded_rectangle([x0, y0, x1, y1], radius=60, fill=255)
    wobble_line(d, rr_pts(x0, y0, x1, y1, 60), w=5, seed=seed, jit_amp=0.05)
    (bx, tx, ty) = tail
    d.polygon([(bx - 22, y1 - 3), (bx + 22, y1 - 3), (tx, ty)], fill=255)
    wobble_line(d, [(bx - 22, y1), (tx, ty), (bx + 22, y1)], w=5, seed=seed + 1)


def small_balloon(d, cx, cy, lines, tail, seed, size=26):
    w = max(text_width(s, size) for s in lines) + 50
    h = len(lines) * size * 1.6 + 30
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d.ellipse([x0, y0, x1, y1], fill=255)
    pts = [(cx + w / 2 * math.cos(2 * math.pi * k / 60), cy + h / 2 * math.sin(2 * math.pi * k / 60)) for k in range(61)]
    tx, ty = tail
    d.polygon([(cx - 14, y1 - 8), (cx + 14, y1 - 8), (tx, ty)], fill=255)
    wobble_line(d, pts, w=4, seed=seed)
    wobble_line(d, [(cx - 14, y1 - 4), (tx, ty), (cx + 14, y1 - 4)], w=4, seed=seed + 2)
    for i, s in enumerate(lines):
        pen(d, s, cx, y0 + 18 + i * size * 1.6, size, ink=INK, seed=seed + 10 + i, anchor="m")
    return (x0, y0, x1, y1)


def draw_front(img, g):
    d = ImageDraw.Draw(img)
    T1 = SHEET["text"]
    bal = SHEET["balloons"]
    hb = world("porter.body", rest_pose())
    phead = ap(hb, (440 - F_CROP[0], 120 - F_CROP[1]))
    x0, x1, y0, y1 = bal["P1"]; balloon(d, x0, x1, y0, y1, tail=(470, 520, 326), seed=11)
    x0, x1, y0, y1 = bal["P2"]; balloon(d, x0, x1, y0, y1, tail=(1640, phead[0] - 10, phead[1] - 30), seed=12)
    P1L = [("THE KEY?", "I SWEAR, NOT"), ("IN MY", "ENVELOPE!"), ("ALL", "I CARRY IS PAPER.")]
    P2L = [("HERE! SILLY ME -", "I HAD IT"), ("IN THE COAT", "POCKET"), ("ALL", "ALONG.")]
    assert [" ".join(p) for p in P1L] == T1["P1_miller"] and [" ".join(p) for p in P2L] == T1["P2_porter"]
    frag = {}
    for i, (l, r) in enumerate(P1L):
        frag[f"P1.{i}.L"] = pen(d, l, A - GAP, LINE_Y[i], CAP, seed=100 + i, anchor="r")
        frag[f"P1.{i}.R"] = pen(d, r, A + GAP, LINE_Y[i], CAP, seed=110 + i, anchor="l")
    for i, (l, r) in enumerate(P2L):
        frag[f"P2.{i}.L"] = pen(d, l, B - GAP, LINE_Y[i], CAP, seed=200 + i, anchor="r")
        frag[f"P2.{i}.R"] = pen(d, r, B + GAP, LINE_Y[i], CAP, seed=210 + i, anchor="l")
    hp1 = world("porter1.head", rest_pose())
    hat1 = ap(hp1, (400 - F_CROP[0], 40 - F_CROP[1]))
    sb1 = small_balloon(d, 1010, 372, ["WHO BORROWED", "IT, THEN?"], (hat1[0] + 4, hat1[1] + 6), seed=300)
    sb2 = small_balloon(d, 2215, 430, ["OH?", "REALLY?"], (2250, 575), seed=310)
    for (px0, px1), s in [(P1, 21), (P2, 22)]:
        wobble_line(d, rr_pts(px0, PY0, px1, PY1, 4, 2), w=6, seed=s, jit_amp=0.04)
    arr = np.array(img)
    arr[:, :P1[0] - 3] = 255; arr[:, P2[1] + 4:] = 255
    arr[:PY0 - 3] = 255; arr[PY1 + 4:] = 255
    arr[:, P1[1] + 4:P2[0] - 3] = 255
    img2 = Image.fromarray(arr); d = ImageDraw.Draw(img2)
    mk = SHEET["marks"]
    for x, lab in [(A, "A"), (M, "M"), (B, "B")]:
        for yy, sgn in [(mk["top_y"], 1), (mk["bottom_y"], -1)]:
            d.polygon([(x - 10, yy - 10 * sgn), (x + 10, yy - 10 * sgn), (x, yy + 4 * sgn)], fill=INK)
        pen(d, lab, x + 16, 8, 18, seed=400 + x)
        pen(d, lab, x + 16, mk["bottom_y"] - 14, 18, seed=420 + x)
    return img2, frag, sb1, sb2


# ------------------------------------------------------------------ render
DRAW_ORDER = ["boys", "porter.body", "porter.forearm", "porter.hand", "porter.key",
              "miller.body", "miller.arm", "miller.forearm", "miller.hand",
              "porter1.body", "porter1.head"]


def render(pose, back, front_fn):
    cv = (np.asarray(back, np.float32) / 255.0).copy()
    for n in DRAW_ORDER:
        p = PARTS[n]
        Wm = world(n, pose) @ T(*p.origin)
        A2 = Wm[:2].astype(np.float32)
        ink = cv2.warpAffine(p.ink, A2, (SW, SH), flags=cv2.INTER_LINEAR, borderValue=0)
        mat = cv2.warpAffine(p.matte, A2, (SW, SH), flags=cv2.INTER_LINEAR, borderValue=0)
        cv = cv * (1 - mat) + mat          # card holds out what is behind
        cv = cv * (1 - ink)                # its printed ink
    img = Image.fromarray(np.clip(cv * 255 + 0.5, 0, 255).astype(np.uint8))
    return front_fn(img)


if __name__ == "__main__":
    g = build_all()
    build_key(g)
    build_boys()
    back = Image.new("L", (SW, SH), 255)
    draw_back(ImageDraw.Draw(back))
    out = {}
    def front(img):
        im2, frag, sb1, sb2 = draw_front(img, g); out.update(frag=frag, sb1=sb1, sb2=sb2); return im2
    art = render(rest_pose(), back, front)
    art.save(os.path.join(HERE, "art-layers.png"))
    back.save(os.path.join(HERE, "parts", "layer-back.png"))
    import pickle
    pickle.dump(dict(g=g, out=out), open(os.path.join(HERE, "_build.pkl"), "wb"))
    print("ok", {k: (round(v[0], 1), round(v[1], 1)) for k, v in out["frag"].items()})
