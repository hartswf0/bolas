"""Canonical panels for the cercle-vicieux test shot: X (hinge, animated), H (animated point), G, F, E (stills).
Shadow theatre (SCION 2 Reiniger): black cut-card puppets, pinned joints, punched lace, on a backlit tissue screen.
Secondary dynamics (SCION 41): bell + clapper + cord simulated with a semi-implicit Euler integrator at 1/240 s,
sampled on twos. Everything is drawn at 2x page resolution (SS=2) and is deterministic: a panel's frame k is the
same bytes wherever the panel occurs (SCION 43 identity)."""
import math, random, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import ink as K

SS = 2
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/cercle-vicieux/test-shot/"
FPS = 24
BLACK = 8
CELL = (800 * SS, 590 * SS)
XSIZE = (600 * SS, 1210 * SS)
CAP = 30 * SS            # cap height ~2.2 % of 1350


def R(seed):
    return random.Random(seed)


# ------------------------------------------------------------------ cut paper
def scissor(pts, seed, amp=2.2, step=22, jog=0.12):
    """Every cut edge carries the small jogs of a pair of scissors: tiny wander plus, now and then,
    a re-entry step where the blades were closed and opened again."""
    r = R(seed); out = []
    P = list(pts) + [pts[0]]
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        nx, ny = (-(y1 - y0) / (L + 1e-9), (x1 - x0) / (L + 1e-9))
        off = 0.0
        for i in range(n):
            t = i / n
            if r.random() < jog:
                off = r.uniform(-amp * 1.6, amp * 1.6)        # the jog
            w = r.uniform(-amp * .45, amp * .45) + off
            out.append((x0 + (x1 - x0) * t + nx * w, y0 + (y1 - y0) * t + ny * w))
    return out


def rot(pts, a, c):
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


def capsule(a, b, r0, r1, n=8):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); q = ang + math.pi / 2
    pts = []
    for i in range(n + 1):
        t = q - math.pi * i / n
        pts.append((b[0] + math.cos(t) * r1, b[1] + math.sin(t) * r1))
    for i in range(n + 1):
        t = q + math.pi - math.pi * i / n
        pts.append((a[0] + math.cos(t) * r0, a[1] + math.sin(t) * r0))
    return pts


def ellipse_pts(cx, cy, rx, ry, n=28):
    return [(cx + math.cos(i / n * 2 * math.pi) * rx, cy + math.sin(i / n * 2 * math.pi) * ry) for i in range(n)]


class Cut:
    """A sheet of black card on the light table: a mask (255 = card)."""

    def __init__(self, size):
        self.m = Image.new("L", size, 0)
        self.d = ImageDraw.Draw(self.m)

    def piece(self, pts, seed, amp=2.2):
        self.d.polygon(scissor(pts, seed, amp), fill=255)

    def punch(self, pts):          # a hole punched through the card
        self.d.polygon(pts, fill=0)

    def hole(self, cx, cy, r):
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)

    def diamond(self, cx, cy, w, h):
        self.punch([(cx, cy - h), (cx + w, cy), (cx, cy + h), (cx - w, cy)])

    def line(self, pts, w):
        self.d.line(pts, fill=255, width=int(w), joint="curve")


def limb(c, root, a1, l1, a2, l2, w, seed):
    """Two pinned pieces (upper and lower), forward kinematics from the root pin; returns (elbow, end).
    The child's pin is computed from the parent's end, so it is coincident by construction (pin error 0 px)."""
    e = (root[0] + math.cos(a1) * l1, root[1] + math.sin(a1) * l1)
    h = (e[0] + math.cos(a1 + a2) * l2, e[1] + math.sin(a1 + a2) * l2)
    c.piece(capsule(root, e, w, w * .86), seed, 1.6)
    c.piece(capsule(e, h, w * .86, w * .7), seed + 1, 1.6)
    return e, h


# ------------------------------------------------------------------ the light table
@functools.lru_cache(None)
def fibre(w, h, seed):
    """Tissue fibre: long thin translucent fibres laid at random, very low contrast (screens only)."""
    r = np.random.RandomState(seed)
    f = np.zeros((h, w), np.float32)
    img = Image.new("L", (w, h), 0); d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 2600)):
        x, y = r.uniform(0, w), r.uniform(0, h)
        a = r.uniform(0, math.pi); L = r.uniform(30, 160); bend = r.uniform(-.4, .4)
        pts = []
        for i in range(8):
            t = i / 7
            aa = a + bend * t
            pts.append((x + math.cos(aa) * L * t, y + math.sin(aa) * L * t))
        d.line(pts, fill=int(r.uniform(40, 255)), width=1)
    f = np.asarray(img, np.float32) / 255.0
    f = cv2.GaussianBlur(f, (0, 0), 0.8)
    clouds = cv2.GaussianBlur(r.normal(0, 1, (h // 16 + 1, w // 16 + 1)).astype(np.float32), (0, 0), 1.5)
    clouds = cv2.resize(clouds, (w, h), interpolation=cv2.INTER_CUBIC)
    return (f * 5.0 + clouds * 1.6).astype(np.float32)   # +/- a few luma levels


def screen(w, h, hot, seed, lo=201.0, hi=242.0, spread=1.0):
    """Backlit tissue screen: hot centre (#F2F2F0) falling off to no darker than #C8C8C6 at the edges."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dmax = max(math.hypot(hot[0] - cx, hot[1] - cy) for cx in (0, w) for cy in (0, h))
    rr = np.hypot(xx - hot[0], yy - hot[1]) / (dmax * spread)
    v = hi - (hi - lo) * np.clip(rr, 0, 1) ** 1.6
    return v + fibre(w, h, seed)


def arches(w, h, top, spacing, aw, seed, x0=0):
    """Second tissue layer: an arcade cut from one sheet of tissue (darkens the screen to ~#B4B4B2)."""
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    x = x0
    while x < w + aw:
        pts = [(x - aw / 2, h)]
        for i in range(25):
            t = math.pi + math.pi * i / 24
            pts.append((x + math.cos(t) * aw / 2, top + aw / 2 + math.sin(t) * aw / 2))
        pts.append((x + aw / 2, h))
        d.polygon(scissor(pts, seed + int(x), 1.4), fill=255)
        x += spacing
    a = np.asarray(m, np.float32) / 255
    return cv2.GaussianBlur(a, (0, 0), 1.2)


def compose(bg, card, tissue=None, tissue_k=0.745):
    """Light through tissue, then the black card on top."""
    v = bg.copy()
    if tissue is not None:
        v = v * (1 - tissue * (1 - tissue_k))
    m = np.asarray(card, np.float32) / 255
    v = v * (1 - m) + BLACK * m
    return v


def letter(img_np, fn):
    """Run a PIL lettering function on a uint8 grey array."""
    im = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8), "L")
    return np.asarray(fn(im), np.float32)


# ------------------------------------------------------------------ puppets
@functools.lru_cache(None)
def redcap_head():
    """Foraged: LoC FSA 'Red cap at the Union Station' (1943) outline, cut and printed solid black."""
    return cv2.imread(SRC + "work/redcap_head_closed.png", 0)


def paste_mask(c, mask, cx, by, scale, ang=0.0, flip=False):
    """Paste a foraged outline as one more card piece, pinned at its bottom centre (neck pin)."""
    m = mask[:, ::-1] if flip else mask
    h, w = m.shape
    M = cv2.getRotationMatrix2D((w / 2, h), math.degrees(-ang), scale)
    M[0, 2] += cx - w / 2; M[1, 2] += by - h
    W, H = c.m.size
    out = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR)
    base = np.asarray(c.m)
    c.m = Image.fromarray(np.maximum(base, out)); c.d = ImageDraw.Draw(c.m)


def porter_back(c, x, y, s, head_ang=0.0, lift=0.0, seed=100):
    """Porter seen from behind (X): coat with half-belt, diamond hem, head = real red-cap outline."""
    X = lambda dx: x + dx * s
    Y = lambda dy: y - dy * s
    # legs and boots
    limb(c, (X(-15), Y(100)), math.pi / 2 + .03, 52 * s, -.02, 46 * s, 11 * s, seed + 1)
    limb(c, (X(15), Y(100)), math.pi / 2 - .03, 52 * s, .02, 46 * s, 11 * s, seed + 3)
    c.piece([(X(-30), Y(0)), (X(-2), Y(0)), (X(-4), Y(9)), (X(-27), Y(9))], seed + 5)
    c.piece([(X(2), Y(0)), (X(30), Y(0)), (X(27), Y(9)), (X(4), Y(9))], seed + 6)
    # coat: shoulders, back, flared hem
    coat = [(X(-44), Y(196)), (X(-30), Y(206)), (X(30), Y(206)), (X(44), Y(196)), (X(46), Y(150)), (X(52), Y(66)),
            (X(-52), Y(66)), (X(-46), Y(150))]
    c.piece(coat, seed + 7)
    # punched lace: diamond hem, half-belt with two buttons, centre-back vent
    for i in range(9):
        c.diamond(X(-44 + i * 11), Y(74), 3.6 * s, 5.2 * s)
    c.punch([(X(-30), Y(127)), (X(30), Y(127)), (X(30), Y(125.6)), (X(-30), Y(125.6))])
    c.punch([(X(-30), Y(119)), (X(30), Y(119)), (X(30), Y(117.6)), (X(-30), Y(117.6))])
    c.hole(X(-22), Y(122.3), 2.2 * s); c.hole(X(22), Y(122.3), 2.2 * s)
    c.punch([(X(-.8), Y(112)), (X(.8), Y(112)), (X(.8), Y(70)), (X(-.8), Y(70))])
    # arms hang on shoulder and elbow pins
    limb(c, (X(-40), Y(192)), math.pi / 2 + .12, 52 * s, -.10, 48 * s, 9.5 * s, seed + 9)
    limb(c, (X(40), Y(192)), math.pi / 2 - .10, 52 * s, .12, 48 * s, 9.5 * s, seed + 11)
    # collar/neck piece, then the foraged head on the neck pin
    c.piece([(X(-16), Y(204)), (X(16), Y(204)), (X(13), Y(222)), (X(-13), Y(222))], seed + 13)
    hm = redcap_head()
    sc = 50 * s / hm.shape[0]
    paste_mask(c, hm, X(0), Y(214) - lift * s, sc, head_ang, flip=True)


def profile_head(c, nx, ny, s, f, ang, seed, hat="cap"):
    """Handmade profile head: skull, brow, nose, lips, chin; pinned at the neck (nx, ny)."""
    X = lambda dx: nx + dx * s * f
    Y = lambda dy: ny - dy * s
    hp = [(X(-14), Y(4)), (X(-18), Y(18)), (X(-19), Y(32)), (X(-14), Y(44)), (X(-4), Y(50)), (X(8), Y(49)),
          (X(15), Y(42)), (X(16), Y(36)), (X(22), Y(28)), (X(16), Y(26)), (X(16), Y(21)), (X(18), Y(18)),
          (X(15), Y(15)), (X(15), Y(11)), (X(10), Y(6)), (X(4), Y(6)), (X(2), Y(0)), (X(-10), Y(0))]
    c.piece(rot(hp, ang * f, (nx, ny)), seed, 1.2)
    if hat == "cap":            # peaked porter's cap with punched badge
        cap = [(X(-20), Y(40)), (X(-18), Y(56)), (X(12), Y(58)), (X(16), Y(46)), (X(30), Y(40)), (X(16), Y(38)),
               (X(-20), Y(36))]
        c.piece(rot(cap, ang * f, (nx, ny)), seed + 1, 1.0)
        bx, by = rot([(X(4), Y(49))], ang * f, (nx, ny))[0]
        c.hole(bx, by, 2.6 * s)
    else:                       # traveller's brimmed hat with a punched band
        hat_ = [(X(-30), Y(42)), (X(-15), Y(46)), (X(-13), Y(62)), (X(10), Y(64)), (X(13), Y(47)), (X(28), Y(43)),
                (X(26), Y(40)), (X(-28), Y(39))]
        c.piece(rot(hat_, ang * f, (nx, ny)), seed + 1, 1.0)
        for i in range(4):
            hx, hy = rot([(X(-9 + i * 5.5), Y(50))], ang * f, (nx, ny))[0]
            c.hole(hx, hy, 1.5 * s)


def porter_side(c, x, y, s, f=1, sh=(1.5, 0.15), sh2=(1.6, 0.1), head=0.0, seed=200, key_in=None):
    """Porter in profile: cap, buttoned coat, diamond hem. sh = (shoulder, elbow) angles for the front arm
    (radians, 0 = pointing forward, pi/2 = hanging), sh2 for the back arm. Returns the front hand."""
    X = lambda dx: x + dx * s * f
    Y = lambda dy: y - dy * s
    A = lambda a: a if f > 0 else math.pi - a
    limb(c, (X(-8), Y(100)), A(math.pi / 2 + .06), 52 * s, -.04 * f, 46 * s, 11 * s, seed + 1)
    limb(c, (X(12), Y(100)), A(math.pi / 2 - .1), 52 * s, .08 * f, 46 * s, 11 * s, seed + 3)
    c.piece([(X(-18), Y(0)), (X(14), Y(0)), (X(10), Y(9)), (X(-16), Y(9))], seed + 5)
    c.piece([(X(4), Y(0)), (X(40), Y(0)), (X(34), Y(9)), (X(6), Y(9))], seed + 6)
    # back arm first (behind the coat)
    a1 = sh2[0]; ang1 = A(a1) if f > 0 else math.pi - a1
    limb(c, (X(-6), Y(194)), A(sh2[0]), 50 * s, sh2[1] * f, 46 * s, 9 * s, seed + 7)
    coat = [(X(-28), Y(204)), (X(24), Y(204)), (X(32), Y(150)), (X(44), Y(64)), (X(-42), Y(64)), (X(-32), Y(150))]
    c.piece(coat, seed + 9)
    for i in range(8):
        c.diamond(X(-36 + i * 11), Y(72), 3.6 * s, 5.2 * s)
    for i in range(5):
        c.hole(X(20 - i * .8), Y(190 - i * 24), 2.6 * s)
    c.piece([(X(-10), Y(204)), (X(12), Y(204)), (X(11), Y(214)), (X(-8), Y(214))], seed + 11)
    profile_head(c, X(1), Y(212), s * 1.05, f, head, seed + 13, "cap")
    e, h = limb(c, (X(4), Y(192)), A(sh[0]), 52 * s, sh[1] * f, 48 * s, 9 * s, seed + 15)
    c.piece(ellipse_pts(h[0], h[1], 8 * s, 7 * s, 12), seed + 17, 1.0)   # mitten hand
    return h


def visitor(c, x, y, s, f=1, sh=(1.55, 0.1), sh2=(1.62, 0.1), head=0.0, step=0.0, seed=300):
    """Visitor in profile: brimmed hat, long travelling coat with a punched round-hole hem."""
    X = lambda dx: x + dx * s * f
    Y = lambda dy: y - dy * s
    A = lambda a: a if f > 0 else math.pi - a
    limb(c, (X(-8), Y(96)), A(math.pi / 2 + .05 + step), 50 * s, -.03 * f, 44 * s, 10 * s, seed + 1)
    limb(c, (X(10), Y(96)), A(math.pi / 2 - .08), 50 * s, .05 * f, 44 * s, 10 * s, seed + 3)
    fx = X(-8) + math.cos(A(math.pi / 2 + .05 + step)) * 94 * s * 0 - (math.sin(step) * 94 * s * f)
    c.piece([(fx - 14 * s * f, Y(0)), (fx + 18 * s * f, Y(0)), (fx + 14 * s * f, Y(8)), (fx - 12 * s * f, Y(8))], seed + 5)
    c.piece([(X(0), Y(0)), (X(32), Y(0)), (X(28), Y(8)), (X(2), Y(8))], seed + 6)
    limb(c, (X(-4), Y(186)), A(sh2[0]), 48 * s, sh2[1] * f, 44 * s, 8.5 * s, seed + 7)
    coat = [(X(-22), Y(196)), (X(22), Y(196)), (X(28), Y(150)), (X(40), Y(56)), (X(-38), Y(56)), (X(-28), Y(150))]
    c.piece(coat, seed + 9)
    for i in range(9):
        c.hole(X(-32 + i * 8), Y(64), 2.4 * s)
    c.punch([(X(-20), Y(150)), (X(20), Y(150)), (X(20), Y(148.6)), (X(-20), Y(148.6))])
    c.piece([(X(-8), Y(196)), (X(10), Y(196)), (X(9), Y(206)), (X(-7), Y(206))], seed + 11)
    profile_head(c, X(1), Y(204), s, f, head, seed + 13, "hat")
    e, h = limb(c, (X(2), Y(184)), A(sh[0]), 48 * s, sh[1] * f, 44 * s, 8.5 * s, seed + 15)
    # pointing hand: a mitten with an index finger along the forearm direction
    ang = math.atan2(h[1] - e[1], h[0] - e[0])
    tip = (h[0] + math.cos(ang) * 22 * s, h[1] + math.sin(ang) * 22 * s)
    c.piece(ellipse_pts(h[0], h[1], 7.5 * s, 6.5 * s, 12), seed + 17, 1.0)
    c.piece(capsule(h, tip, 3.0 * s, 2.4 * s, 4), seed + 18, .8)
    return h


def bell_piece(c, px, py, s, th, ph, seed=400, lever=True):
    """Bell on its pivot (px,py) at angle th; clapper at absolute angle ph. Punched band of lace.
    Returns the lever tip (where the cord is tied)."""
    X = lambda dx: px + dx * s
    Y = lambda dy: py + dy * s
    shell = [(X(-4), Y(0)), (X(4), Y(0)), (X(6), Y(8)), (X(16), Y(14)), (X(22), Y(30)), (X(26), Y(50)), (X(36), Y(62)),
             (X(-36), Y(62)), (X(-26), Y(50)), (X(-22), Y(30)), (X(-16), Y(14)), (X(-6), Y(8))]
    # clapper first so the shell covers its rod; ball hangs below the lip
    cl = (px + math.sin(-ph) * 64 * s, py + math.cos(ph) * 64 * s)
    c.line([(px, py + 8 * s), cl], 3 * s)
    c.piece(ellipse_pts(cl[0], cl[1], 7 * s, 7 * s, 14), seed + 1, .8)
    c.piece(rot(shell, th, (px, py)), seed, 1.4)
    for i in range(7):
        hx, hy = rot([(X(-21 + i * 7), Y(51))], th, (px, py))[0]
        c.hole(hx, hy, 2.0 * s)
    tip = None
    if lever:
        lv = [(X(0), Y(-3)), (X(32), Y(-3)), (X(32), Y(3)), (X(0), Y(3))]
        c.piece(rot(lv, th, (px, py)), seed + 3, .8)
        tip = rot([(X(32), Y(0))], th, (px, py))[0]
    c.piece(ellipse_pts(px, py, 5 * s, 5 * s, 10), seed + 4, .5)
    return tip


def bracket(c, wx, wy, px, py, s, seed=420):
    """Wall bracket from the wall plate at (wx,wy) out to the pivot (px,py)."""
    c.piece([(wx - 4 * s, wy - 16 * s), (wx + 4 * s, wy - 16 * s), (wx + 4 * s, wy + 16 * s), (wx - 4 * s, wy + 16 * s)], seed, 1)
    c.piece([(min(wx, px), py - 4 * s), (max(wx, px), py - 4 * s), (max(wx, px), py + 2 * s), (min(wx, px), py + 2 * s)], seed + 1, 1)
    c.line([(wx, wy + 12 * s), (px + (wx - px) * .45, py)], 3 * s)


def key_piece(c, x, y, s, ang, seed=500):
    """Brass key in silhouette: bow with a punched hole, shank, bit."""
    bow = ellipse_pts(x, y, 9 * s, 9 * s, 16)
    c.piece(bow, seed, .7)
    sh = [(x + 7 * s, y - 2.2 * s), (x + 40 * s, y - 2.2 * s), (x + 40 * s, y + 2.2 * s), (x + 7 * s, y + 2.2 * s)]
    bit = [(x + 30 * s, y + 2 * s), (x + 38 * s, y + 2 * s), (x + 38 * s, y + 10 * s), (x + 34 * s, y + 10 * s),
           (x + 34 * s, y + 6 * s), (x + 30 * s, y + 6 * s)]
    c.piece(rot(sh, ang, (x, y)), seed + 1, .5)
    c.piece(rot(bit, ang, (x, y)), seed + 2, .5)
    c.hole(x, y, 4 * s)


def service_door(c, x0, y0, x1, y1, s, seed=600, pane=True):
    """The service door, closed: black slab in a black frame, punched panel slots, a punched keyhole, and the
    frosted pane (a window cut out of the card). Returns the pane box."""
    c.piece([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], seed, 1.6)
    w = x1 - x0
    pb = None
    if pane:
        pb = (x0 + w * .16, y0 + w * .18, x1 - w * .16, y0 + w * .18 + (x1 - x0) * .95)
        c.punch(scissor([(pb[0], pb[1]), (pb[2], pb[1]), (pb[2], pb[3]), (pb[0], pb[3])], seed + 1, 1.2))
    # punched slots outlining two lower panels
    top = (pb[3] if pb else y0 + w * .2) + w * .14
    mid = top + (y1 - top) * .46
    for (a, b) in ((top, mid - w * .05), (mid + w * .05, y1 - w * .12)):
        r0 = (x0 + w * .2, a, x1 - w * .2, b)
        lw = 2.2 * s
        for seg in ([(r0[0], r0[1]), (r0[2], r0[1] + lw)], [(r0[0], r0[3] - lw), (r0[2], r0[3])],
                    [(r0[0], r0[1]), (r0[0] + lw, r0[3])], [(r0[2] - lw, r0[1]), (r0[2], r0[3])]):
            (ax, ay), (bx, by) = seg
            c.punch([(ax, ay), (bx, ay), (bx, by), (ax, by)])
    # keyhole: light from behind the door shows through it
    kx, ky = x0 + w * .84, top - w * .02
    c.hole(kx, ky, 3.2 * s)
    c.punch([(kx - 1.6 * s, ky), (kx + 1.6 * s, ky), (kx + 2.4 * s, ky + 9 * s), (kx - 2.4 * s, ky + 9 * s)])
    return pb


def floor(c, w, h, top, seed=700):
    c.piece([(-10, top), (w + 10, top), (w + 10, h + 10), (-10, h + 10)], seed, 1.8)


# ------------------------------------------------------------------ dynamics (SCION 41)
def pull_profile(t, pulls=(1.25, 2.55), D=34.0):
    """Hand displacement (px at 1x panel scale) behind the glass: two pulls, each down 0.22 s, hold, release."""
    d = 0.0
    for t0 in pulls:
        if t0 <= t < t0 + 0.22:
            u = (t - t0) / 0.22; d = max(d, D * (u * u * (3 - 2 * u)))
        elif t0 + 0.22 <= t < t0 + 0.34:
            d = max(d, D)
        elif t0 + 0.34 <= t < t0 + 0.72:
            u = (t - t0 - 0.34) / 0.38; d = max(d, D * (1 - u * u * (3 - 2 * u)))
    return d


@functools.lru_cache(None)
def simulate_x(seconds=5.2, dt=1 / 240):
    """Bell (damped pendulum) driven only through a one-sided cord spring from the hand; clapper is a free
    pendulum (period 1.6x the bell's) hung at the same pivot, so it lags and strikes the rim.
    Semi-implicit Euler at 1/240 s. Returns per-substep arrays and the strike list."""
    wb = 2 * math.pi * 1.05; zb = 0.14
    wc = wb / 1.6; zc = 0.06
    Lv = 32.0                     # lever length (px, 1x bell scale)
    kc = 5.0                      # cord stiffness (rad/s^2 per px of stretch)
    lim = 0.30                    # clapper/rim clearance (rad)
    th = om = 0.0; ph = oc = 0.0
    T, TH, PH, D, E = [], [], [], [], []
    strikes = []
    n = int(round(seconds / dt))
    for i in range(n):
        t = i * dt
        d = pull_profile(t)
        stretch = d - Lv * math.sin(th)
        torque = kc * max(0.0, stretch) * math.cos(th)
        om += (-wb * wb * math.sin(th) - 2 * zb * wb * om + torque) * dt
        th += om * dt
        oc += (-wc * wc * math.sin(ph) - 2 * zc * wc * oc) * dt
        ph += oc * dt
        rel = ph - th
        if abs(rel) > lim:
            vrel = oc - om
            if vrel * rel > 0:
                strikes.append((t, abs(vrel)))
                oc = om - 0.35 * vrel
            ph = th + math.copysign(lim, rel)
        T.append(t); TH.append(th); PH.append(ph); D.append(d)
        E.append(0.5 * om * om + wb * wb * (1 - math.cos(th)))
    return np.array(T), np.array(TH), np.array(PH), np.array(D), np.array(E), strikes


def x_state(k):
    """Pose for frame k of X's cycle, sampled on twos (frames 2j and 2j+1 identical)."""
    T, TH, PH, D, E, _ = simulate_x()
    kk = (k // 2) * 2
    i = min(len(T) - 1, int(round(kk / FPS * 240)))
    vel = 0.0
    if i > 0:
        j = max(0, i - 24)
        vel = (D[i] - D[j]) / ((i - j) / 240 + 1e-9)
    return TH[i], PH[i], D[i], vel, kk / FPS


# ------------------------------------------------------------------ panel X
X_CYCLE = int(round(5.2 * FPS))     # 125 frames


@functools.lru_cache(None)
def x_static():
    W, H = XSIZE
    s = SS * 2.0                       # puppet unit scale
    bg = screen(W, H, (W * .62, H * .42), 11, spread=1.05)
    tis = arches(W, H, int(H * .34), int(W * .62), int(W * .48), 12, x0=int(W * .14))
    return bg, tis


X_DOOR = (0.42, 0.30, 0.90, 0.88)       # door box (fractions of X)
X_FLOOR = 0.88


def panel_x(k):
    W, H = XSIZE
    th, ph, d, vel, t = x_state(k)
    bg, tis = x_static()
    s = SS * 2.0
    c = Cut((W, H))
    fl = int(H * X_FLOOR)
    floor(c, W, H, fl)
    dx0, dy0, dx1, dy1 = int(W * X_DOOR[0]), int(H * X_DOOR[1]), int(W * X_DOOR[2]), fl + 2
    # door frame (architrave) and the door
    c.piece([(dx0 - 22 * SS, dy0 - 26 * SS), (dx1 + 22 * SS, dy0 - 26 * SS), (dx1 + 22 * SS, fl + 4), (dx0 - 22 * SS, fl + 4)], 601)
    c.punch([(dx0 - 4 * SS, dy0 - 6 * SS), (dx1 + 4 * SS, dy0 - 6 * SS), (dx1 + 4 * SS, dy0 - 3 * SS), (dx0 - 4 * SS, dy0 - 3 * SS)])
    pb = service_door(c, dx0, dy0, dx1, fl - 5 * SS, SS * 1.3, 610)
    # bell over the door, cord from the lever tip down through the frame head
    cord_x = pb[0] + (pb[2] - pb[0]) * .62
    px, py = cord_x - 32 * SS * 1.55, dy0 - 150 * SS
    bracket(c, dx1 + 10 * SS, py - 10 * SS, px, py, SS * 1.3)
    tip = bell_piece(c, px, py, SS * 1.55, th, ph)
    hole_x = tip[0] if tip else px
    cord_x = pb[0] + (pb[2] - pb[0]) * .62
    c.line([tip, (cord_x, dy0 - 24 * SS)], 2.6 * SS)
    # porter, back to us, at left; head tilts up after the first pull (4 poses)
    tilt = 0.0
    if t >= 1.45:
        tilt = min(4, int((t - 1.45) * 12 / 2) + 1) / 4     # 4 poses on twos
    porter_back(c, W * .21, fl + 2, SS * 2.2, head_ang=0.16 * tilt, lift=3.0 * tilt)
    v = compose(bg, c.m, tis)
    # --- behind the frosted pane: warm light, cord shadow and (only here, only once) the hand-shadow
    x0, y0, x1, y1 = [int(round(q)) for q in pb]
    pw, ph_ = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:ph_, 0:pw].astype(np.float32)
    glow = 247 - 14 * np.clip(np.hypot((xx - pw * .55) / pw, (yy - ph_ * .45) / ph_) * 1.6, 0, 1) ** 2
    sh = hand_shadow(pw, ph_, cord_x - x0, d * SS, t)
    pane = glow * (1 - sh) + 110 * sh
    hole = 255 - np.asarray(c.m, np.float32)[y0:y1, x0:x1] / 255 * 255   # only where the pane is cut
    a = hole / 255
    v[y0:y1, x0:x1] = v[y0:y1, x0:x1] * (1 - a) + pane * a
    # --- the one light from behind the door: the line under it, flickering as the hand moves
    flick = 1.0 - min(0.55, abs(vel) / 260.0)
    ly0 = fl - 5 * SS
    v[ly0:fl + 1, dx0 + 4:dx1 - 4] = BLACK + (250 - BLACK) * flick
    spill = np.zeros((int(H * .07), W), np.float32)
    for r in range(spill.shape[0]):
        u = r / spill.shape[0]
        a0 = int(dx0 - (dx1 - dx0) * .25 * u); a1 = int(dx1 + (dx1 - dx0) * .25 * u)
        spill[r, max(0, a0):min(W, a1)] = (1 - u) ** 2.2
    spill = cv2.GaussianBlur(spill, (0, 0), 3)
    v[fl + 2:fl + 2 + spill.shape[0]] = np.maximum(v[fl + 2:fl + 2 + spill.shape[0]], BLACK + 96 * flick * spill)
    v = letter(v, lambda im: K.caption_box(im, "THE BELL CAN ONLY BE RUNG FROM BEHIND THAT DOOR.", 26 * SS, 24 * SS,
                                            CAP, maxc=17, seed=31, lw=7))
    warm = np.zeros((H, W), np.float32); warm[y0:y1, x0:x1] = a
    return v, warm


def hand_shadow(pw, ph, cx, d, t):
    """Handmade hand puppet behind the glass, gripping the cord: palm, four curled fingers on knuckle pins,
    a separate thumb wrapped over the top; its shadow on frosted glass is soft (blurred)."""
    m = Image.new("L", (pw, ph), 0); dr = ImageDraw.Draw(m)
    c = Cut((pw, ph)); c.m = m; c.d = dr
    s = SS * 1.45
    # cord shadow, full height of the pane
    gy = ph * .40 + d                       # the grip moves with the pull
    c.line([(cx, -10), (cx, ph + 10)], 3.2 * SS)
    curl = 0.25 + 0.25 * min(1.0, d / (30 * SS))   # fingers tighten while pulling
    # forearm comes in from below-left, out of the pane
    wrist = (cx - 26 * s, gy + 30 * s)
    c.piece(capsule((cx - 120 * s, ph + 60 * s), wrist, 26 * s, 17 * s), 801, 1.0)
    # palm block (back of the hand), left of the cord
    palm = [(cx - 44 * s, gy - 18 * s), (cx - 6 * s, gy - 24 * s), (cx + 2 * s, gy + 18 * s), (cx - 18 * s, gy + 38 * s),
            (cx - 40 * s, gy + 32 * s)]
    c.piece(palm, 803, 1.0)
    # four fingers wrap the cord: proximal piece across the cord, distal piece curled back (pinned at the knuckle)
    for i in range(4):
        ky = gy - 14 * s + i * 12.5 * s
        k0 = (cx - 6 * s, ky)
        k1 = (cx + 16 * s, ky + 2 * s)
        c.piece(capsule(k0, k1, 6.0 * s, 5.4 * s, 5), 810 + i, .7)
        a2 = math.pi / 2 + curl + i * .05
        tip = (k1[0] + math.cos(a2) * 11 * s, k1[1] + math.sin(a2) * 11 * s)
        c.piece(capsule(k1, tip, 5.4 * s, 4.4 * s, 5), 820 + i, .7)
    # thumb: its own piece, over the top of the fist, with a gap above the index finger so it reads as a thumb
    t0 = (cx - 30 * s, gy - 22 * s)
    t1 = (cx - 10 * s, gy - 42 * s)
    t2 = (cx + 10 * s, gy - 40 * s - curl * 4 * s)
    c.piece(capsule(t0, t1, 8.5 * s, 7 * s, 5), 830, .7)
    c.piece(capsule(t1, t2, 7 * s, 5.5 * s, 5), 831, .7)
    a = np.asarray(c.m, np.float32) / 255
    # frosted glass: the shadow softens with distance from the glass; thumb stays legible
    return cv2.GaussianBlur(a, (0, 0), 3.0 * SS) * .92


# ------------------------------------------------------------------ cell panels
@functools.lru_cache(None)
def cell_bg(seed, hot):
    W, H = CELL
    bg = screen(W, H, (W * hot[0], H * hot[1]), seed)
    tis = arches(W, H, int(H * .14), int(W * .30), int(W * .22), seed + 1, x0=int(W * .1))
    tis[int(H * .5):] *= np.linspace(1, 0, H - int(H * .5))[:, None] ** .5   # tissue fades toward the floor light
    return bg, tis


CFL = 0.88   # floor top in cells (12 % band)


def panel_h(k):
    """H: the visitor points at the bell, which hangs still. Arm lifts in 4 poses (on twos), then holds."""
    W, H = CELL
    bg, tis = cell_bg(21, (.55, .45))
    c = Cut((W, H)); fl = int(H * CFL); floor(c, W, H, fl)
    s = SS * 1.45
    t = (k // 2) * 2 / FPS
    rest = (1.52, 0.10); point = (-0.24, -0.04)
    p = 0 if t < 0.5 else min(4, int((t - 0.5) * 12 / 2) + 1)    # pose index 0..4
    over = [0, .35, .7, 1.06, 1.0][p]                             # small overshoot then settle
    sh = (rest[0] + (point[0] - rest[0]) * over, rest[1] + (point[1] - rest[1]) * over)
    visitor(c, W * .26, fl + 1, s, 1, sh=sh, head=-0.06 * min(1, p / 3), seed=330)
    px, py = W * .78, H * .30
    bracket(c, W * .90, py - 8 * SS, px, py, SS * 1.3, 431)
    bell_piece(c, px, py, SS * 1.5, 0.0, 0.0, 440, lever=True)
    c.line([(px + 32 * SS * 1.5, py), (px + 32 * SS * 1.5, py + 6 * SS)], 2.4 * SS)
    v = compose(bg, c.m, tis)
    v = letter(v, lambda im: K.balloon(im, "THEN WHO RANG THE BELL?", W * .40, H * .13, CAP, (W * .29, H * .27),
                                       seed=41, maxc=13, kind="whisper", lw=7))
    return v


def panel_g():
    """G: the porter beside the closed door (plain lit pane, line of light under it), head turned, pointing."""
    W, H = CELL
    bg, tis = cell_bg(23, (.40, .45))
    c = Cut((W, H)); fl = int(H * CFL); floor(c, W, H, fl)
    s = SS * 1.45
    pb = service_door(c, W * .72, H * .20, W * .97, fl + 2, SS, 650)
    porter_side(c, W * .40, fl + 1, s, 1, sh=(-0.05, 0.05), head=0.05, seed=260)
    v = compose(bg, c.m, tis)
    x0, y0, x1, y1 = [int(q) for q in pb]
    v[y0:y1, x0:x1] = np.where(np.asarray(c.m)[y0:y1, x0:x1] < 128, 238.0, v[y0:y1, x0:x1])
    v[fl - 3 * SS:fl + 1, int(W * .72) + 4:int(W * .97) - 4] = 250
    v = letter(v, lambda im: K.balloon(im, "NOBODY GOES THROUGH THAT DOOR.", W * .22, H * .16, CAP, (W * .33, H * .34),
                                       seed=51, maxc=15, lw=7))
    return v, (x0, y0, x1, y1)


def panel_f():
    """F: the key lies on the bench; the visitor has stepped back from it, hand withdrawn."""
    W, H = CELL
    bg, tis = cell_bg(25, (.45, .5))
    c = Cut((W, H)); fl = int(H * CFL); floor(c, W, H, fl)
    s = SS * 1.45
    # bench: lace-punched backrest, seat, legs
    bx0, bx1, seat = W * .10, W * .55, fl - 90 * SS
    c.piece([(bx0, seat - 70 * SS), (bx1, seat - 70 * SS), (bx1, seat - 48 * SS), (bx0, seat - 48 * SS)], 751)
    for i in range(10):
        c.hole(bx0 + (i + .5) * (bx1 - bx0) / 10, seat - 59 * SS, 4.5 * SS)
    c.piece([(bx0 - 6 * SS, seat), (bx1 + 6 * SS, seat), (bx1 + 6 * SS, seat + 14 * SS), (bx0 - 6 * SS, seat + 14 * SS)], 752)
    for lx in (bx0 + 10 * SS, bx1 - 22 * SS):
        c.piece([(lx, seat + 10 * SS), (lx + 12 * SS, seat + 10 * SS), (lx + 12 * SS, fl + 2), (lx, fl + 2)], 753 + int(lx))
    c.piece([(bx0 + 30 * SS, seat - 48 * SS), (bx0 + 40 * SS, seat - 48 * SS), (bx0 + 40 * SS, seat), (bx0 + 30 * SS, seat)], 755)
    c.piece([(bx1 - 40 * SS, seat - 48 * SS), (bx1 - 30 * SS, seat - 48 * SS), (bx1 - 30 * SS, seat), (bx1 - 40 * SS, seat)], 756)
    key_piece(c, W * .30, seat - 9 * SS, SS * 1.5, 0.0, 560)
    visitor(c, W * .80, fl + 1, s, -1, sh=(1.2, 0.5), step=0.12, head=0.08, seed=360)
    v = compose(bg, c.m, tis)
    v = letter(v, lambda im: K.balloon(im, "THEN I DON'T WANT IT.", W * .50, H * .15, CAP, (W * .76, H * .34),
                                       seed=61, maxc=12, lw=7))
    return v


def panel_e():
    """E: the porter holds the key up toward the closed door at the right edge."""
    W, H = CELL
    bg, tis = cell_bg(27, (.40, .40))
    c = Cut((W, H)); fl = int(H * CFL); floor(c, W, H, fl)
    s = SS * 1.45
    pb = service_door(c, W * .84, H * .22, W * 1.08, fl + 2, SS, 660)
    hand = porter_side(c, W * .36, fl + 1, s, 1, sh=(-0.95, 0.35), head=-0.12, seed=270)
    key_piece(c, hand[0] + 2 * SS, hand[1] - 14 * SS, SS * 1.5, -math.pi / 2 + .1, 570)
    v = compose(bg, c.m, tis)
    x0, y0, x1, y1 = [int(q) for q in pb]
    x1 = min(x1, W)
    v[y0:y1, x0:x1] = np.where(np.asarray(c.m)[y0:y1, x0:x1] < 128, 236.0, v[y0:y1, x0:x1])
    v = letter(v, lambda im: K.balloon(im, "THIS OPENS THE SERVICE DOOR.", W * .245, H * .14, CAP, (W * .33, H * .33),
                                       seed=71, maxc=14, lw=7))
    return v
