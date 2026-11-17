"""KF2 'Shadow door': page 3 (hinge X + H G / F E) at 29.0 s, the hinge just after the page turn.
Reiniger-style articulated silhouettes cut by hand (polygon puppets, hinged at shoulder, elbow,
hip and neck, lace holes punched), laid on a backlit screen with grey tissue layers behind.
Run: python3 -I kf2.py"""
import sys, math
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/proposals")
from kf_common import *

OUT = ROOT + "/films/swarm/cercle-vicieux/proposals/"
BLACK = 8


def rot(pts, ang, c):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


def scissor(pts, seed, amp=1.6):
    """Every straight edge gets the tiny jogs of a scissor cut."""
    r = rng(seed); out = []
    P = pts + [pts[0]]
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 14))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t + r.uniform(-amp, amp), y0 + (y1 - y0) * t + r.uniform(-amp, amp)))
    return out


def capsule(a, b, r0, r1):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); n = ang + math.pi / 2
    pts = [(a[0] + math.cos(n) * r0, a[1] + math.sin(n) * r0), (b[0] + math.cos(n) * r1, b[1] + math.sin(n) * r1)]
    for i in range(9):
        t = n - math.pi * i / 8
        pts.append((b[0] + math.cos(t) * r1, b[1] + math.sin(t) * r1))
    pts.append((a[0] - math.cos(n) * r0, a[1] - math.sin(n) * r0))
    for i in range(9):
        t = n + math.pi - math.pi * i / 8
        pts.append((a[0] + math.cos(t) * r0, a[1] + math.sin(t) * r0))
    return pts


def limb(d, root, a1, l1, a2, l2, w, seed, col=BLACK):
    """Two-bone limb: forward kinematics from the joint pin."""
    e = (root[0] + math.cos(a1) * l1, root[1] + math.sin(a1) * l1)
    h = (e[0] + math.cos(a1 + a2) * l2, e[1] + math.sin(a1 + a2) * l2)
    d.polygon(scissor(capsule(root, e, w, w * .85), seed), fill=col)
    d.polygon(scissor(capsule(e, h, w * .85, w * .7), seed + 1), fill=col)
    return h


def pin(d, p, s):   # the brass paper-fastener at each joint, seen as a pinhole of light
    d.ellipse([p[0] - 2.5 * s, p[1] - 2.5 * s, p[0] + 2.5 * s, p[1] + 2.5 * s], fill=200)


def porter(d, x, y, s, f=1, arm=(-0.3, -0.4), arm2=(0.2, 0.3), head=0.0, seed=0, holes=True):
    """x,y = feet centre; f = facing (+1 right). Angles in radians, mirrored by facing."""
    def X(dx): return x + dx * s * f
    def Y(dy): return y - dy * s
    def ang(a): return a if f > 0 else math.pi - a
    col = BLACK
    # legs
    limb(d, (X(-10), Y(95)), ang(math.pi / 2 + .05) if f > 0 else math.pi / 2 - .05, 50 * s, 0, 45 * s, 10 * s, seed + 1)
    limb(d, (X(12), Y(95)), math.pi / 2 - .08 * f, 50 * s, 0, 45 * s, 10 * s, seed + 2)
    d.polygon(scissor([(X(-20), Y(2)), (X(8), Y(2)), (X(4), Y(10)), (X(-18), Y(10))], seed + 3), fill=col)
    d.polygon(scissor([(X(6), Y(2)), (X(36), Y(2)), (X(30), Y(10)), (X(6), Y(10))], seed + 4), fill=col)
    # long coat with a flared hem
    coat = [(X(-26), Y(205)), (X(26), Y(205)), (X(34), Y(150)), (X(44), Y(60)), (X(-40), Y(60)), (X(-32), Y(150))]
    d.polygon(scissor(coat, seed + 5), fill=col)
    # head on a neck pin
    nk = (X(2), Y(212))
    hc = (X(4), Y(236))
    hp = [(hc[0] + math.cos(t) * 20 * s, hc[1] + math.sin(t) * 22 * s) for t in [i / 20 * 2 * math.pi for i in range(20)]]
    hp += [(X(26), Y(232)), (X(30), Y(226)), (X(22), Y(224))]   # nose
    hp = rot(hp, head * f, nk)
    d.polygon(scissor(hp, seed + 6, 1.0), fill=col)
    cap = [(X(-20), Y(244)), (X(-17), Y(262)), (X(22), Y(266)), (X(26), Y(248)), (X(42), Y(242)), (X(24), Y(238)), (X(-20), Y(236))]
    d.polygon(scissor(rot(cap, head * f, nk), seed + 7, 1.0), fill=col)
    d.polygon(scissor([(X(-10), Y(212)), (X(14), Y(212)), (X(12), Y(200)), (X(-8), Y(200))], seed + 8), fill=col)
    # arms on shoulder pins
    sh = (X(16), Y(196)); sb = (X(-14), Y(196))
    hb = limb(d, sb, ang(math.pi / 2 + arm2[0]), 52 * s, arm2[1] * f, 50 * s, 9 * s, seed + 9)
    hf = limb(d, sh, ang(math.pi / 2 + arm[0]), 52 * s, arm[1] * f, 50 * s, 9 * s, seed + 10)
    for p in (hb, hf):
        d.ellipse([p[0] - 9 * s, p[1] - 9 * s, p[0] + 9 * s, p[1] + 9 * s], fill=col)
    if holes:   # punched lace: buttons, hem scallops, cap badge
        for k in range(4):
            bx, by = X(8), Y(185 - k * 28)
            d.ellipse([bx - 3 * s, by - 3 * s, bx + 3 * s, by + 3 * s], fill=235)
        for k in range(9):
            hx = X(-36 + k * 9.5); hy = Y(70)
            d.polygon([(hx, hy - 6 * s), (hx + 4 * s, hy), (hx, hy + 6 * s), (hx - 4 * s, hy)], fill=235)
        bxy = rot([(X(2), Y(258))], head * f, nk)[0]
        d.ellipse([bxy[0] - 4 * s, bxy[1] - 3 * s, bxy[0] + 4 * s, bxy[1] + 3 * s], fill=235)
        pin(d, sh, s)
    return hf, hb


def visitor(d, x, y, s, f=1, arm=(-0.2, -0.6), arm2=(0.1, 0.2), head=0.0, seed=0, envelope=True):
    def X(dx): return x + dx * s * f
    def Y(dy): return y - dy * s
    def ang(a): return a if f > 0 else math.pi - a
    col = BLACK
    limb(d, (X(-8), Y(70)), math.pi / 2 + .04 * f, 36 * s, 0, 34 * s, 7 * s, seed + 1)
    limb(d, (X(10), Y(70)), math.pi / 2 - .1 * f, 36 * s, 0, 34 * s, 7 * s, seed + 2)
    for dx in (-8, 12):
        d.polygon(scissor([(X(dx - 10), Y(1)), (X(dx + 14), Y(1)), (X(dx + 10), Y(8)), (X(dx - 8), Y(8))], seed + dx), fill=col)
    coat = [(X(-20), Y(185)), (X(20), Y(185)), (X(28), Y(130)), (X(38), Y(66)), (X(-36), Y(66)), (X(-28), Y(130))]
    d.polygon(scissor(coat, seed + 5), fill=col)
    nk = (X(2), Y(190)); hc = (X(4), Y(210))
    hp = [(hc[0] + math.cos(t) * 17 * s, hc[1] + math.sin(t) * 19 * s) for t in [i / 20 * 2 * math.pi for i in range(20)]]
    hp += [(X(21), Y(208)), (X(24), Y(202)), (X(18), Y(200))]
    d.polygon(scissor(rot(hp, head * f, nk), seed + 6, 1.0), fill=col)
    hat = [(X(-26), Y(214)), (X(-18), Y(236)), (X(0), Y(242)), (X(18), Y(236)), (X(24), Y(216)), (X(32), Y(212)), (X(-30), Y(210))]
    d.polygon(scissor(rot(hat, head * f, nk), seed + 7, 1.0), fill=col)
    # scalloped hem: punched half-moons
    for k in range(8):
        hx = X(-30 + k * 9); hy = Y(70)
        d.ellipse([hx - 3 * s, hy - 3 * s, hx + 3 * s, hy + 3 * s], fill=235)
    sh = (X(12), Y(176)); sb = (X(-10), Y(176))
    limb(d, sb, ang(math.pi / 2 + arm2[0]), 44 * s, arm2[1] * f, 40 * s, 7 * s, seed + 9)
    hf = limb(d, sh, ang(math.pi / 2 + arm[0]), 44 * s, arm[1] * f, 40 * s, 7 * s, seed + 10)
    d.ellipse([hf[0] - 7 * s, hf[1] - 7 * s, hf[0] + 7 * s, hf[1] + 7 * s], fill=col)
    if envelope:
        e = [(hf[0] - 4 * s, hf[1] - 18 * s), (hf[0] + 34 * s * f, hf[1] - 22 * s), (hf[0] + 36 * s * f, hf[1] + 2 * s), (hf[0] - 2 * s, hf[1] + 6 * s)]
        d.polygon(scissor(e, seed + 11, 0.8), fill=col)
        d.line([e[0], ((e[0][0] + e[1][0]) / 2, hf[1] - 6 * s), e[1]], fill=235, width=int(2 * s))
    pin(d, sh, s)
    return hf


def bell(d, cx, cy, s, swing=0.0, seed=0):
    br = [(cx - 50 * s, cy - 40 * s), (cx + 6 * s, cy - 40 * s), (cx + 6 * s, cy - 34 * s), (cx - 50 * s, cy - 34 * s)]
    d.polygon(scissor(br, seed), fill=BLACK)
    pv = (cx, cy - 34 * s)
    b = [(cx - 4 * s, cy - 34 * s), (cx + 4 * s, cy - 34 * s), (cx + 8 * s, cy - 26 * s), (cx + 14 * s, cy - 6 * s), (cx + 22 * s, cy + 6 * s),
         (cx + 24 * s, cy + 12 * s), (cx - 24 * s, cy + 12 * s), (cx - 22 * s, cy + 6 * s), (cx - 14 * s, cy - 6 * s), (cx - 8 * s, cy - 26 * s)]
    d.polygon(scissor(rot(b, swing, pv), seed + 1, 0.8), fill=BLACK)
    cl = rot([(cx, cy + 20 * s)], swing * 1.6, pv)[0]
    d.ellipse([cl[0] - 6 * s, cl[1] - 6 * s, cl[0] + 6 * s, cl[1] + 6 * s], fill=BLACK)
    for k in range(5):  # filigree band punched through the bell
        q = rot([(cx - 12 * s + k * 6 * s, cy - 4 * s)], swing, pv)[0]
        d.ellipse([q[0] - 1.8 * s, q[1] - 1.8 * s, q[0] + 1.8 * s, q[1] + 1.8 * s], fill=235)
    return rot([(cx + 18 * s, cy + 6 * s)], swing, pv)[0]


def screen(box, seed, hot=(0.5, 0.42), lo=150):
    """Backlit screen: hot centre falling off to the frame, plus faint tissue fibres."""
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx / w - hot[0]) * 1.2) ** 2 + ((yy / h - hot[1]) * 1.0) ** 2)
    g = 252 - (252 - lo) * np.clip(r / 0.75, 0, 1) ** 1.6
    rs = np.random.RandomState(seed)
    fib = cv2.GaussianBlur(rs.randn(h // 4 + 1, w // 4 + 1).astype(np.float32), (0, 0), 1.2)
    fib = cv2.resize(fib, (w, h))
    return np.clip(g + fib * 4, 0, 255).astype(np.uint8)


def tissue_layer(img, poly, val, blur=3):
    """A grey tissue cut-out on a pane behind the puppets (multiplane depth)."""
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(img).astype(np.float32); mm = np.array(m).astype(np.float32) / 255
    a = a * (1 - mm * (1 - val / 255.0))
    return Image.fromarray(a.astype(np.uint8))


def arches(x0, y0, x1, y1, n, seed):
    pts = [(x0, y1)]
    w = (x1 - x0) / n
    for i in range(n):
        ax = x0 + i * w
        pts += [(ax, y0 + 40)] + [(ax + w / 2 + math.cos(math.pi - t / 12 * math.pi) * w * .42, y0 + 40 - math.sin(t / 12 * math.pi) * w * .5 + 0) for t in range(13)] + [(ax + w, y0 + 40)]
    pts += [(x1, y1)]
    return pts


def build():
    c = Image.new("L", (W, H), PAPER)
    G = 40
    X0, X1, Y0, Y1 = 70, 2490, 56, 1330
    xw = 640
    bx = {"X": (X0, Y0, X0 + xw, Y1)}
    gx0 = X0 + xw + G
    cw = (X1 - gx0 - G) // 2; ch = (Y1 - Y0 - G) // 2
    bx["H"] = (gx0, Y0, gx0 + cw, Y0 + ch); bx["G"] = (gx0 + cw + G, Y0, X1, Y0 + ch)
    bx["F"] = (gx0, Y0 + ch + G, gx0 + cw, Y1); bx["E"] = (gx0 + cw + G, Y0 + ch + G, X1, Y1)
    a = np.array(c)
    hots = {"X": (0.5, 0.32), "H": (0.6, 0.35), "G": (0.4, 0.4), "F": (0.5, 0.4), "E": (0.45, 0.4)}
    for k, b in bx.items():
        a[b[1]:b[3], b[0]:b[2]] = screen(b, ord(k), hots[k], lo=120 if k == "X" else 150)
    c = Image.fromarray(a)

    def floor(img, b, yy, val=BLACK):
        d = ImageDraw.Draw(img)
        d.polygon(scissor([(b[0], yy), (b[2], yy), (b[2], b[3]), (b[0], b[3])], ord("f") + yy), fill=val)

    # ---------------- X: the hinge. The bell is pulled from behind the door.
    b = bx["X"]
    c = tissue_layer(c, arches(b[0], b[1] + 260, b[2], b[3], 2, 1), 200, 4)
    d = ImageDraw.Draw(c)
    fy = b[3] - 150
    # service door: black frame, frosted upper pane lit from the far side
    dx0, dx1, dy0 = b[0] + 300, b[0] + 560, fy - 560
    d.polygon(scissor([(dx0 - 26, dy0 - 26), (dx1 + 26, dy0 - 26), (dx1 + 26, fy), (dx0 - 26, fy)], 11), fill=BLACK)
    pane = (dx0 + 24, dy0 + 24, dx1 - 24, dy0 + 270)
    pa = screen(pane, 12, (0.5, 0.5), lo=170)
    # the shadow of a hand gripping the cord, cast on the frosted pane from behind (soft: it is on the far side)
    sh = Image.new("L", (pane[2] - pane[0], pane[3] - pane[1]), 0); sd = ImageDraw.Draw(sh)
    cxp = (pane[2] - pane[0]) * .55
    sd.line([(cxp, 0), (cxp, pane[3] - pane[1])], fill=255, width=7)
    hand = [(cxp - 40, 120), (cxp + 18, 104), (cxp + 34, 120), (cxp + 30, 150), (cxp + 14, 168), (cxp - 22, 172), (cxp - 70, 230), (cxp - 120, 270), (cxp - 150, 240), (cxp - 90, 180)]
    sd.polygon(hand, fill=255)
    for k in range(4):
        sd.ellipse([cxp + 8, 112 + k * 14, cxp + 30, 128 + k * 14], fill=255)
    sh = np.array(sh.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255
    pa = (pa * (1 - sh * 0.55)).astype(np.uint8)
    arr = np.array(c); arr[pane[1]:pane[3], pane[0]:pane[2]] = pa; c = Image.fromarray(arr); d = ImageDraw.Draw(c)
    # lower door panels (lace-cut), handle
    for k in range(2):
        q = (dx0 + 40, dy0 + 320 + k * 110, dx1 - 40, dy0 + 400 + k * 110)
        d.rectangle(q, outline=225, width=3)
    d.ellipse([dx1 - 60, dy0 + 300, dx1 - 40, dy0 + 320], fill=225)
    # light under the door
    d.rectangle([dx0, fy - 10, dx1, fy], fill=250)
    floor(c, b, fy)
    d = ImageDraw.Draw(c)
    d.polygon(scissor([(b[0], fy), (b[2], fy), (b[2], fy + 8), (b[0], fy + 8)], 3), fill=BLACK)
    d.rectangle([dx0, fy - 10, dx1, fy + 4], fill=250)
    for k in range(7):   # the spill of light from under the door on the floor
        d.polygon([(dx0 + k * 4, fy + 4), (dx1 - k * 4, fy + 4), (dx1 + 40 + k * 30, fy + 14 + k * 16), (dx0 - 40 - k * 30, fy + 14 + k * 16)], fill=int(250 - k * 34))
    # bell high on the wall; cord runs down the wall and into the door frame
    bcx, bcy = b[0] + 430, b[1] + 340
    tip = bell(d, bcx, bcy, 2.4, swing=0.28, seed=21)
    d.line([(dx1 + 4, dy0 - 26), (dx1 + 4, bcy - 70), (bcx + 10, bcy - 80)], fill=BLACK, width=5)
    for k in range(3):   # ring strokes, cut as paper sparks
        r0 = 70 + k * 34
        for t in (-0.9, -0.5, -0.1):
            p0 = (bcx + math.cos(t) * r0, bcy + 10 + math.sin(t) * r0)
            p1 = (bcx + math.cos(t) * (r0 + 18), bcy + 10 + math.sin(t) * (r0 + 18))
            d.line([p0, p1], fill=BLACK, width=6)
    # porter, back to us at three-quarter, head tipped up toward the bell
    porter(d, b[0] + 150, fy + 4, 2.05, f=1, arm=(-0.15, -0.9), arm2=(0.05, 0.15), head=-0.35, seed=30)
    c = caption_box(c, "The bell can only be rung from behind that door.", b[0] + 24, b[1] + 22, 30, maxc=16, seed=40)

    # ---------------- H: visitor looks up: who rang?
    b = bx["H"]
    c = tissue_layer(c, arches(b[0], b[1] + 150, b[2], b[3], 3, 2), 205, 4)
    d = ImageDraw.Draw(c); fy = b[3] - 80; floor(c, b, fy); d = ImageDraw.Draw(c)
    visitor(d, b[0] + 360, fy + 2, 2.0, f=1, arm=(-1.9, 0.5), arm2=(0.1, 0.2), head=-0.45, seed=50, envelope=False)
    bell(d, b[0] + 730, b[1] + 290, 1.6, swing=0.0, seed=52)
    c = balloon(c, "Then who rang the bell?", b[0] + 640, b[1] + 100, 34, (b[0] + 420, b[1] + 160), seed=55, maxc=13, kind="whisper")

    # ---------------- G: porter by the door
    b = bx["G"]
    c = tissue_layer(c, arches(b[0], b[1] + 150, b[2], b[3], 3, 3), 205, 4)
    d = ImageDraw.Draw(c); fy = b[3] - 80; floor(c, b, fy); d = ImageDraw.Draw(c)
    d.polygon(scissor([(b[0] + 640, fy - 400), (b[0] + 820, fy - 400), (b[0] + 820, fy), (b[0] + 640, fy)], 61), fill=BLACK)
    d.rectangle([b[0] + 640, fy - 8, b[0] + 820, fy], fill=245)
    porter(d, b[0] + 250, fy + 2, 1.6, f=1, arm=(-0.1, -0.2), arm2=(0.05, 0.1), head=0.0, seed=60)
    c = balloon(c, "Nobody goes through that door.", b[0] + 540, b[1] + 92, 32, (b[0] + 330, b[1] + 140), seed=65, maxc=15)

    # ---------------- F: the key left on the bench
    b = bx["F"]
    c = tissue_layer(c, arches(b[0], b[1] + 150, b[2], b[3], 3, 4), 205, 4)
    d = ImageDraw.Draw(c); fy = b[3] - 80; floor(c, b, fy); d = ImageDraw.Draw(c)
    bench = [(b[0] + 180, fy - 150), (b[0] + 620, fy - 150), (b[0] + 620, fy - 126), (b[0] + 600, fy - 126), (b[0] + 600, fy), (b[0] + 580, fy),
             (b[0] + 580, fy - 126), (b[0] + 220, fy - 126), (b[0] + 220, fy), (b[0] + 200, fy), (b[0] + 200, fy - 126), (b[0] + 180, fy - 126)]
    d.polygon(scissor(bench, 71), fill=BLACK)
    d.polygon(scissor([(b[0] + 180, fy - 250), (b[0] + 620, fy - 250), (b[0] + 620, fy - 220), (b[0] + 180, fy - 220)], 72), fill=BLACK)
    for k in range(10):
        d.ellipse([b[0] + 206 + k * 40, fy - 242, b[0] + 222 + k * 40, fy - 228], fill=230)
    # key on the bench (bow with a punched hole)
    kx, ky = b[0] + 380, fy - 162
    d.ellipse([kx - 18, ky - 16, kx + 14, ky + 14], fill=BLACK); d.ellipse([kx - 8, ky - 6, kx + 4, ky + 4], fill=235)
    d.rectangle([kx + 12, ky - 4, kx + 80, ky + 4], fill=BLACK); d.rectangle([kx + 62, ky + 4, kx + 70, ky + 16], fill=BLACK)
    visitor(d, b[0] + 760, fy + 2, 1.7, f=-1, arm=(-0.6, -0.3), arm2=(0.1, 0.2), head=0.1, seed=75, envelope=False)
    c = balloon(c, "Then I don't want it.", b[0] + 500, b[1] + 92, 32, (b[0] + 730, b[1] + 175), seed=78, maxc=12)

    # ---------------- E: porter raises the key
    b = bx["E"]
    c = tissue_layer(c, arches(b[0], b[1] + 150, b[2], b[3], 3, 5), 205, 4)
    d = ImageDraw.Draw(c); fy = b[3] - 80; floor(c, b, fy); d = ImageDraw.Draw(c)
    d.polygon(scissor([(b[0] + 680, fy - 400), (b[0] + 860, fy - 400), (b[0] + 860, fy), (b[0] + 680, fy)], 81), fill=BLACK)
    hf, _ = porter(d, b[0] + 330, fy + 2, 1.6, f=1, arm=(-2.15, 0.25), arm2=(0.05, 0.1), head=-0.15, seed=82)
    kx, ky = hf
    d.ellipse([kx - 14, ky - 40, kx + 14, ky - 12], fill=BLACK); d.ellipse([kx - 5, ky - 31, kx + 5, ky - 21], fill=235)
    d.rectangle([kx - 4, ky - 90, kx + 4, ky - 38], fill=BLACK); d.rectangle([kx + 4, ky - 88, kx + 16, ky - 80], fill=BLACK)
    c = balloon(c, "This opens the service door.", b[0] + 610, b[1] + 290, 32, (b[0] + 400, b[1] + 200), seed=85, maxc=14)

    a = np.array(c); keep = np.zeros(a.shape, bool)
    for q in bx.values():
        keep[q[1]:q[3], q[0]:q[2]] = True
    a[~keep] = PAPER; c = Image.fromarray(a)
    d = ImageDraw.Draw(c)
    for k, q in bx.items():
        panel_frame(d, q, seed=ord(k) + 7, width=9)
    c, _ = letter_line(c, "- 3 -", W // 2, 1395, 26, 90)
    return finish(c, OUT + "kf-2.png")


if __name__ == "__main__":
    build()
