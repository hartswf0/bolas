"""Keyframes for mauro-martino-exercises-in-style, proposal round (deterministic).

kf-1  Cut-Paper Platform  foraged 1916 Agence Rol bus (Commons, PD), GrabCut-cut and printed
                          as a two-tone cut-paper/linocut plate; handmade articulated
                          silhouette puppets (the long-necked passenger, the jostler) on the
                          rear platform; handmade carved facade and pavement.
kf-2  Stitched Overhead   handmade procedural embroidery: an overhead scene graph rasterised
                          into cross-stitch / satin-stitch thread on twill denim.
kf-3  The Archive Answers foraged archive frames used as "samples" returned for a baseline
                          prompt and a camera delta; typed manifest as kinetic type.

Run: python3 kf.py   (reads films/sources/mauro-martino-exercises-in-style/, writes kf-*.png, board.jpg)
"""
import math
import os
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUL = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(OUL, "films/sources/mauro-martino-exercises-in-style")
REF = os.path.join(OUL, "assets/references")
W, H = 1280, 720
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CREAM = (236, 228, 210)
INK = (18, 16, 14)


def font(p, s):
    return ImageFont.truetype(p, s)


# ======================================================================= puppets
def capsule(d, p, q, w, fill):
    d.line([p, q], fill=fill, width=int(w))
    for c in (p, q):
        d.ellipse([c[0] - w / 2, c[1] - w / 2, c[0] + w / 2, c[1] + w / 2], fill=fill)


def limb(p, a, L):
    return (p[0] + L * math.sin(a), p[1] + L * math.cos(a))


def puppet(d, foot_x, foot_y, s, pose, fill=INK, cut=CREAM, neck=1.0, cord=False, lean=0.0,
           hat="felt", case=False):
    """Articulated silhouette (forward kinematics). Angles in radians, 0 = straight down.
    pose: dict hipL, kneeL, hipR, kneeR, shL, elL, shR, elR. Returns joint dict."""
    leg = 46 * s
    hip = (foot_x + math.sin(lean) * 2 * leg, foot_y - 2 * leg * math.cos(lean * 0.3))
    kL = limb(hip, pose["hipL"], leg)
    aL = limb(kL, pose["hipL"] + pose["kneeL"], leg)
    kR = limb(hip, pose["hipR"], leg)
    aR = limb(kR, pose["hipR"] + pose["kneeR"], leg)
    for k, a in ((kL, aL), (kR, aR)):
        capsule(d, hip, k, 12 * s, fill)
        capsule(d, k, a, 9 * s, fill)
        d.polygon([(a[0] - 6 * s, a[1] - 5 * s), (a[0] + 16 * s, a[1] - 3 * s), (a[0] + 17 * s, a[1] + 5 * s),
                   (a[0] - 6 * s, a[1] + 5 * s)], fill=fill)
    tl = 62 * s
    sh = (hip[0] + math.sin(lean) * tl, hip[1] - math.cos(lean) * tl)
    # overcoat: tapered polygon from shoulders to below hip
    px, py = math.cos(lean), math.sin(lean)
    coat = [(sh[0] - 13 * s * px, sh[1] - 13 * s * py), (sh[0] + 13 * s * px, sh[1] + 13 * s * py),
            (hip[0] + 19 * s * px + 4 * s, hip[1] + 26 * s), (hip[0] - 18 * s * px - 2 * s, hip[1] + 28 * s)]
    d.polygon(coat, fill=fill)
    nk = 16 * s * neck
    nt = (sh[0] + math.sin(lean * 1.4) * nk, sh[1] - nk)
    capsule(d, sh, nt, 6.5 * s, fill)
    hc = (nt[0] + 2 * s, nt[1] - 9 * s)
    d.ellipse([hc[0] - 11 * s, hc[1] - 13 * s, hc[0] + 11 * s, hc[1] + 12 * s], fill=fill)
    d.polygon([(hc[0] + 8 * s, hc[1] - 2 * s), (hc[0] + 14 * s, hc[1] + 3 * s), (hc[0] + 8 * s, hc[1] + 5 * s)], fill=fill)
    # hat
    by = hc[1] - 8 * s
    if hat == "felt":
        d.ellipse([hc[0] - 19 * s, by - 3 * s, hc[0] + 19 * s, by + 4 * s], fill=fill)
        d.rounded_rectangle([hc[0] - 11 * s, by - 17 * s, hc[0] + 11 * s, by + 1 * s], radius=int(6 * s), fill=fill)
        if cord:  # the plaited cord instead of a ribbon: cut through the crown as a braid
            for i in range(9):
                x = hc[0] - 10 * s + i * 2.4 * s
                yy = by - 4.5 * s + (1.4 * s if i % 2 else -1.4 * s)
                d.ellipse([x - 1.3 * s, yy - 1.0 * s, x + 1.3 * s, yy + 1.0 * s], fill=cut)
    else:  # cloche / bowler
        d.chord([hc[0] - 13 * s, by - 16 * s, hc[0] + 13 * s, by + 10 * s], 180, 360, fill=fill)
        d.ellipse([hc[0] - 16 * s, by - 2 * s, hc[0] + 16 * s, by + 3 * s], fill=fill)
    arms = {}
    for side, so in (("L", -1), ("R", 1)):
        sp = (sh[0] + so * 3 * s, sh[1] + 3 * s)
        e = limb(sp, pose["sh" + side], 34 * s)
        w = limb(e, pose["sh" + side] + pose["el" + side], 32 * s)
        capsule(d, sp, e, 9 * s, fill)
        capsule(d, e, w, 7.5 * s, fill)
        d.ellipse([w[0] - 6 * s, w[1] - 6 * s, w[0] + 6 * s, w[1] + 6 * s], fill=fill)
        arms[side] = (e, w)
    if case:
        e, w = arms["R"]
        d.rectangle([w[0] - 14 * s, w[1], w[0] + 16 * s, w[1] + 22 * s], fill=fill)
    return dict(hip=hip, sh=sh, head=hc, arms=arms)


# ======================================================================= kf-1
def gouges(d, box, n, rng, lmin, lmax, wmin, wmax, color, ang=0.0, jit=0.08):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        L, w = rng.uniform(lmin, lmax), rng.uniform(wmin, wmax)
        a = ang + rng.uniform(-jit, jit)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        # tapered gouge: lens polygon
        nx, ny = -math.sin(a) * w / 2, math.cos(a) * w / 2
        d.polygon([(x - dx, y - dy), (x + nx * 0.6, y + ny * 0.6), (x + dx, y + dy), (x - nx, y - ny)], fill=color)


def bus_cutout():
    a = cv2.imread(os.path.join(SRC, "commons/rol1916.jpg"))
    m = np.zeros(a.shape[:2], np.uint8)
    m[:] = cv2.GC_BGD
    m[372:680, 525:1085] = cv2.GC_PR_FGD
    m[420:600, 560:1040] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(a, m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    k = ((m == 1) | (m == 3)).astype(np.uint8) * 255
    k = cv2.morphologyEx(k, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    P = np.array([(55, 38), (590, 68), (602, 245), (522, 252), (512, 300), (470, 308), (445, 290), (440, 268),
                  (262, 268), (245, 310), (215, 335), (170, 338), (135, 322), (92, 318), (48, 262), (42, 175),
                  (52, 60)]) + [480, 340]
    pm = np.zeros_like(k)
    cv2.fillPoly(pm, [P.astype(np.int32)], 255)
    k = cv2.bitwise_and(k, pm)
    box = (522, 376, 1084, 680)
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    return g[box[1]:box[3], box[0]:box[2]], k[box[1]:box[3], box[0]:box[2]]


def kf1():
    S = 2
    rng = random.Random(417)
    im = Image.new("RGB", (W * S, H * S), CREAM)
    d = ImageDraw.Draw(im)
    # sky: sparse carved strokes; mansard roof band in black with cut dormers
    gouges(d, (0, 0, W * S, 70 * S), 120, rng, 30 * S, 140 * S, 1.0 * S, 2.6 * S, INK, 0.0, 0.03)
    d.polygon([(0, 70 * S), (W * S, 58 * S), (W * S, 118 * S), (0, 128 * S)], fill=INK)
    for i in range(9):
        x = 40 + i * 150
        d.rectangle([x * S, 80 * S, (x + 30) * S, 112 * S], fill=CREAM)
        d.rectangle([(x + 13) * S, 80 * S, (x + 17) * S, 112 * S], fill=INK)
    # facade: cream stone, black-cut window bays, balconies, cornice lines (carved)
    for y0, y1 in ((142, 232), (262, 352)):
        d.rectangle([0, (y0 - 8) * S, W * S, (y0 - 4) * S], fill=INK)
        for i in range(-1, 15):
            x = 26 + i * 96 + (y0 % 7)
            d.rectangle([x * S, y0 * S, (x + 50) * S, y1 * S], fill=INK)
            d.rectangle([(x + 23) * S, (y0 + 4) * S, (x + 27) * S, (y1 - 4) * S], fill=CREAM)
            d.rectangle([(x + 4) * S, (y0 + 34) * S, (x + 46) * S, (y0 + 37) * S], fill=CREAM)
            d.rectangle([(x - 8) * S, (y1 - 2) * S, (x + 58) * S, (y1 + 2) * S], fill=INK)
            for j in range(9):
                d.rectangle([(x - 6 + j * 8) * S, (y1 - 18) * S, (x - 4 + j * 8) * S, (y1 - 2) * S], fill=INK)
        gouges(d, (0, (y1 + 6) * S, W * S, (y1 + 26) * S), 60, rng, 20 * S, 90 * S, 0.8 * S, 1.8 * S, INK, 0.0, 0.02)
    # shop band: black with cut letters
    d.rectangle([0, 382 * S, W * S, 440 * S], fill=INK)
    gouges(d, (0, 384 * S, W * S, 438 * S), 120, rng, 20 * S, 70 * S, 1.0 * S, 2.4 * S, CREAM, 0.0, 0.05)
    # pavement and roadway, carved
    gouges(d, (0, 446 * S, W * S, 560 * S), 160, rng, 20 * S, 110 * S, 0.8 * S, 2.0 * S, INK, 0.0, 0.02)
    gouges(d, (0, 570 * S, W * S, 720 * S), 560, rng, 30 * S, 170 * S, 1.2 * S, 4.0 * S, INK, 0.0, 0.02)
    # bus: the foraged Rol 1916 bus, GrabCut-cut and printed two-tone (CLAHE + threshold)
    g, k = bus_cutout()
    sc = 1.30 * S
    gw, gh = int(g.shape[1] * sc), int(g.shape[0] * sc)
    g = cv2.resize(g, (gw, gh), interpolation=cv2.INTER_CUBIC)
    k = cv2.resize(k, (gw, gh), interpolation=cv2.INTER_LINEAR)
    g = cv2.createCLAHE(3.0, (6, 6)).apply(g)
    g = cv2.GaussianBlur(g, (0, 0), 1.8)
    ox, oy = 70 * S, 196 * S
    by = oy // S + gh // S
    d.polygon([(130 * S, (by - 14) * S), (820 * S, (by - 26) * S), (860 * S, (by - 6) * S), (110 * S, (by + 10) * S)], fill=INK)
    arr = np.asarray(im).copy()
    reg = arr[oy:oy + gh, ox:ox + gw]
    reg[(g < 115) & (k > 127)] = INK
    reg[(g >= 115) & (k > 127)] = CREAM
    arr[oy:oy + gh, ox:ox + gw] = reg
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    # a lit gap in the facade (a cut-out arcade) so the platform puppets read as silhouettes
    d.rectangle([782 * S, 132 * S, 1040 * S, 472 * S], fill=INK)
    d.rounded_rectangle([792 * S, 142 * S, 1030 * S, 480 * S], radius=110 * S, fill=CREAM)
    gouges(d, (800 * S, 150 * S, 1024 * S, 200 * S), 30, rng, 14 * S, 50 * S, 0.8 * S, 1.6 * S, INK, 0.0, 0.05)
    # handmade rear platform behind the body: floor, step, stanchion, chain
    px0, px1, fy = 786, 1010, 474
    d.rectangle([px0 * S, fy * S, px1 * S, (fy + 12) * S], fill=INK)
    d.rectangle([(px0 + 30) * S, (fy + 12) * S, (px1 - 30) * S, (fy + 24) * S], fill=INK)
    d.rectangle([(px0 + 60) * S, (fy + 34) * S, (px1 - 60) * S, (fy + 40) * S], fill=INK)
    for xx in (px0 + 66, px1 - 66):
        d.rectangle([xx * S, (fy + 24) * S, (xx + 4) * S, (fy + 36) * S], fill=INK)
    d.rectangle([(px1 - 7) * S, 236 * S, px1 * S, fy * S], fill=INK)
    d.rectangle([(px0) * S, 226 * S, (px1 + 6) * S, 234 * S], fill=INK)  # canopy
    for i in range(16):
        t = i / 15
        x = px0 + 20 + t * (px1 - px0 - 20)
        y = 380 + 16 * math.sin(t * math.pi)
        d.ellipse([(x - 5) * S, (y - 3) * S, (x + 5) * S, (y + 3) * S], outline=INK, width=2 * S)
    # the two articulated puppets: the long-necked passenger thrown back; the jostler stepping in
    P = dict(hipL=0.10, kneeL=-0.02, hipR=-0.34, kneeR=0.30, shL=0.65, elL=-1.0, shR=-0.55, elR=-1.45)
    puppet(d, 880 * S, (fy + 1) * S, 1.32 * S, P, neck=2.9, cord=True, lean=-0.20)
    J = dict(hipL=0.42, kneeL=-0.5, hipR=-0.10, kneeR=0.06, shL=-1.35, elL=-0.85, shR=0.25, elR=0.2)
    puppet(d, 968 * S, (fy + 1) * S, 1.26 * S, J, neck=0.8, hat="bowler", lean=-0.26)
    # a waiting figure at the stop, right (next passenger), and walkers in the foreground
    Q = dict(hipL=0.04, kneeL=0.0, hipR=-0.04, kneeR=0.0, shL=0.08, elL=-0.1, shR=-0.1, elR=0.05)
    puppet(d, 1150 * S, 560 * S, 1.2 * S, Q, hat="bowler", case=True)
    for i, (x, ph) in enumerate(((150, 0.4), (300, 2.0), (560, 1.0))):
        a = math.sin(ph) * 0.5
        Wk = dict(hipL=a, kneeL=-0.15 - max(0, a) * 0.7, hipR=-a, kneeR=-0.15 - max(0, -a) * 0.7,
                  shL=-a * 0.9, elL=-0.35, shR=a * 0.9, elR=-0.35)
        puppet(d, x * S, 712 * S, 0.98 * S, Wk, hat="felt" if i % 2 == 0 else "bowler", lean=0.08,
               case=(i == 1))
    im = im.resize((W, H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    n = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 6, (H, W)).astype(np.float32), (0, 0), 0.7)
    im = Image.fromarray(np.clip(a + n[..., None], 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    tag(d, 22, 676, "Δ treatment = cut paper    seed 0417    t 00:19.2    anchor: jostle",
        bg=INK, fg=CREAM)
    return im


def tag(d, x, y, text, bg, fg, size=15):
    f = font(MONO, size)
    tw = d.textlength(text, font=f)
    d.rectangle([x, y, x + tw + 20, y + size + 12], fill=bg)
    d.text((x + 10, y + 5), text, font=f, fill=fg)


# ======================================================================= kf-2
THREAD = dict(denim=(62, 92, 150), road=(120, 150, 196), road2=(104, 134, 182), kerb=(236, 196, 60),
              walk=(214, 206, 186), grass=(46, 128, 64), leaf=(34, 104, 52), leaf2=(92, 160, 70),
              red=(204, 46, 38), yellow=(240, 190, 40), white=(240, 236, 226), black=(28, 26, 30),
              roof=(222, 112, 40), glass=(70, 120, 190), hat1=(60, 46, 38), hat2=(110, 110, 116),
              skin=(226, 180, 140), coat=(40, 52, 90), coat2=(150, 40, 46), cord=(240, 220, 120),
              shadow=(44, 66, 112), lane=(240, 236, 226))


def kf2():
    """Overhead scene graph -> label raster -> cross-stitch."""
    cell = 8
    gw, gh = W // cell, H // cell  # 160 x 90
    lab = Image.new("RGB", (gw * 4, gh * 4), THREAD["denim"])
    d = ImageDraw.Draw(lab)
    s = 4 / cell  # px(1280 space) -> label(640 space)

    def R(box, c):
        d.rectangle([v * s for v in box], fill=THREAD[c])

    def E(box, c):
        d.ellipse([v * s for v in box], fill=THREAD[c])

    def Pg(pts, c):
        d.polygon([(x * s, y * s) for x, y in pts], fill=THREAD[c])

    # street runs left-right; slight diagonal for energy
    Pg([(0, 170), (1280, 120), (1280, 600), (0, 650)], "walk")
    Pg([(0, 230), (1280, 180), (1280, 540), (0, 590)], "road")
    for i in range(0, 1280, 64):  # cobbles banding
        Pg([(i, 230 - i * 0.039), (i + 32, 230 - (i + 32) * 0.039), (i + 32, 590 - (i + 32) * 0.039), (i, 590 - i * 0.039)], "road2")
    Pg([(0, 222), (1280, 172), (1280, 184), (0, 234)], "kerb")
    Pg([(0, 586), (1280, 536), (1280, 548), (0, 598)], "kerb")
    for i in range(0, 1280, 120):  # lane dashes
        Pg([(i, 410 - i * 0.039), (i + 60, 410 - (i + 60) * 0.039), (i + 60, 420 - (i + 60) * 0.039), (i, 420 - i * 0.039)], "lane")
    # tree crowns on the pavements (french knots)
    rng = random.Random(5)
    for x in (80, 330, 590, 850, 1110):
        for yb in (70, 690):
            E((x - 70, yb - 70 - x * 0.02, x + 70, yb + 70 - x * 0.02), "leaf")
            for _ in range(10):
                dx, dy = rng.uniform(-50, 50), rng.uniform(-50, 50)
                E((x + dx - 20, yb + dy - 20, x + dx + 20, yb + dy + 20), rng.choice(["leaf2", "grass"]))
    # pedestrians on pavements from above: hat discs + shadow
    for (x, y, c, h) in ((210, 140, "coat", "hat2"), (470, 612, "coat2", "hat1"), (1000, 128, "coat", "hat1"),
                         (1150, 600, "coat2", "hat2"), (1100, 150, "coat", "black")):
        E((x + 10, y + 10, x + 76, y + 70), "shadow")
        E((x, y + 6, x + 66, y + 54), c)  # shoulders
        E((x + 9, y, x + 57, y + 48), h)  # brim
        E((x + 19, y + 10, x + 47, y + 38), "black" if h != "black" else "hat2")  # crown
    # the bus from above, travelling right; roof with ribs, route plate 'S'; open rear platform at left
    bx0, by0, bx1, by1 = 300, 268, 1010, 470
    R((bx0 + 24, by0 + 26, bx1 + 84, by1 + 26), "shadow")
    R((bx0 + 120, by0, bx1, by1), "roof")
    R((bx1 - 10, by0 + 14, bx1 + 60, by1 - 14), "red")  # bonnet
    R((bx1 + 40, by0 + 40, bx1 + 60, by1 - 40), "black")
    for i in range(6):
        x = bx0 + 150 + i * 120
        R((x, by0 + 6, x + 10, by1 - 6), "yellow")
    R((bx0 + 470, by0 + 70, bx0 + 560, by1 - 70), "white")  # route plate
    d.text(((bx0 + 488) * s, (by0 + 58) * s), "S", font=font(SANS_B, int(78 * s)), fill=THREAD["red"])
    # rear platform (open, floor boards) with rail
    R((bx0, by0 + 10, bx0 + 120, by1 - 10), "hat2")
    for i in range(5):
        R((bx0, by0 + 22 + i * 36, bx0 + 120, by0 + 26 + i * 36), "black")
    R((bx0 - 6, by0 + 10, bx0 + 4, by1 - 10), "yellow")
    # two passengers on the platform seen from above: the jostle = overlapping shoulders
    E((bx0 + 8, by0 + 46, bx0 + 100, by0 + 120), "coat2")  # jostler shoulders
    E((bx0 + 24, by0 + 50, bx0 + 88, by0 + 114), "hat2")  # bowler brim
    E((bx0 + 38, by0 + 64, bx0 + 74, by0 + 100), "hat1")
    E((bx0 + 40, by0 + 104, bx0 + 116, by0 + 174), "coat")  # long-necked passenger
    E((bx0 + 58, by0 + 118, bx0 + 104, by0 + 164), "black")  # his hat crown (cord stitched later)
    lab = lab.resize((gw, gh), Image.NEAREST)
    L = np.asarray(lab)

    rng = np.random.default_rng(417)
    S = 3
    out = Image.new("RGB", (W * S, H * S), THREAD["denim"])
    od = ImageDraw.Draw(out)
    # twill ground
    for k in range(-H * S, W * S, 7 * S):
        od.line([(k, 0), (k + H * S, H * S)], fill=(52, 80, 136), width=2 * S)
    for j in range(gh):
        for i in range(gw):
            c = tuple(int(v) for v in L[j, i])
            if c == THREAD["denim"]:
                continue
            x0, y0 = i * cell * S, j * cell * S
            jx, jy = rng.normal(0, 0.6 * S, 4), rng.normal(0, 0.6 * S, 4)
            sh = tuple(max(0, int(v * 0.62)) for v in c)
            hi = tuple(min(255, int(v * 1.18 + 18)) for v in c)
            m = 1.2 * S
            e = cell * S - m
            # under-stitch (/), then over-stitch (\): the cross
            for (a, b, w) in (((x0 + m + jx[0], y0 + e + jy[0]), (x0 + e + jx[1], y0 + m + jy[1]), 3.8 * S),
                              ((x0 + m + jx[2], y0 + m + jy[2]), (x0 + e + jx[3], y0 + e + jy[3]), 3.8 * S)):
                od.line([a, b], fill=sh, width=int(w + 1.4 * S))
                od.line([a, b], fill=c, width=int(w))
                od.line([(a[0] + 0.8 * S, a[1] - 0.6 * S), (b[0] + 0.8 * S, b[1] - 0.6 * S)], fill=hi, width=max(1, int(0.9 * S)))
    # satin-stitch outline of the bus body (back-stitch run) and the plaited cord on his hat
    def backstitch(pts, col, w=2.2):
        for (a, b) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 14))
            for t in range(n):
                p = (a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n)
                q = (a[0] + (b[0] - a[0]) * (t + 0.8) / n, a[1] + (b[1] - a[1]) * (t + 0.8) / n)
                od.line([(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)], fill=col, width=int(w * S))
    backstitch([(bx0, by0), (bx1, by0), (bx1, by0 + 14), (bx1 + 60, by0 + 14), (bx1 + 60, by1 - 14), (bx1, by1 - 14), (bx1, by1), (bx0, by1), (bx0, by0)], THREAD["black"], 3.0)
    cx, cy, r = bx0 + 81, by0 + 141, 28
    for k in range(36):
        a0, a1 = k / 36 * 2 * math.pi, (k + 0.9) / 36 * 2 * math.pi
        rr = r + (3 if k % 2 else -3)
        od.line([((cx + rr * math.cos(a0)) * S, (cy + rr * math.sin(a0)) * S),
                 ((cx + (r - (3 if k % 2 else -3)) * math.cos(a1)) * S, (cy + (r - (3 if k % 2 else -3)) * math.sin(a1)) * S)],
                fill=THREAD["cord"], width=int(3 * S))
    # loose thread: the jostle vector (running stitch arrow)
    backstitch([(bx0 + 40, by0 + 80), (bx0 + 92, by0 + 132)], THREAD["white"], 2.0)
    out = out.resize((W, H), Image.LANCZOS)
    a = np.asarray(out).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * np.clip(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) - 0.55, 0, 1)
    out = Image.fromarray(np.clip(a * v[..., None], 0, 255).astype(np.uint8))
    d2 = ImageDraw.Draw(out)
    tag(d2, 22, 676, "Δ camera = overhead    seed 0417 (sample 1/2)    t 00:35.2    anchor: jostle",
        bg=(236, 196, 60), fg=(28, 26, 30))
    return out


# ======================================================================= kf-3
def kf3():
    paper = (226, 220, 206)
    im = Image.new("RGB", (W, H), paper)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(9)
    f_t = font(MONO, 17)
    f_s = font(MONO, 13)
    f_h = font(MONO_B, 18)
    # typed manifest line (kinetic type: the field is struck and retyped on screen)
    y = 22
    d.text((36, y), "prompt  ", font=f_h, fill=INK)
    x = 36 + d.textlength("prompt  ", font=f_h)
    base = "\"a crowded platform bus at a stop; a long-necked passenger is jostled\""
    d.text((x, y), base, font=f_t, fill=INK)
    y2 = 52
    d.text((36, y2), "camera  ", font=f_h, fill=INK)
    x = 36 + d.textlength("camera  ", font=f_h)
    old = "street level"
    d.text((x, y2), old, font=f_t, fill=(110, 104, 96))
    ow = d.textlength(old, font=f_t)
    d.line([(x - 2, y2 + 11), (x + ow + 2, y2 + 10)], fill=(196, 40, 30), width=3)
    x2 = x + ow + 18
    d.text((x2, y2), "overhead", font=font(MONO_B, 17), fill=(196, 40, 30))
    cw = d.textlength("overhead", font=font(MONO_B, 17))
    d.rectangle([x2 + cw + 3, y2 + 1, x2 + cw + 12, y2 + 19], fill=(196, 40, 30))  # typing cursor
    d.text((x2 + cw + 30, y2 + 2), "(one field changed; treatment, action, duration frozen)", font=f_s, fill=(90, 84, 76))
    # sample grid
    cols = [("BASELINE  camera: street level", [
        ("commons/bourse1933.jpg", (0, 60, 1280, 958 - 60), "Peyriras 1933 · Gallica/Commons · PD", True, True),
        ("commons/rol1916.jpg", (300, 230, 1180, 820), "Agence Rol 1916 · Gallica/Commons · PD", True, False)]),
        ("DELTA  camera: overhead", [
        ("mia/ggc_2.25.png", None, "Golden Gate City · MIA 86343393 · rights unverified", "~", True),
        ("mia/form_7.png", None, "Formations 1936 · MIA 6eb03e7f · rights unverified", False, False)])]
    gx0, gy0, cw_, ch_ = 36, 100, 590, 252
    for ci, (title, samples) in enumerate(cols):
        cx = gx0 + ci * (cw_ + 28)
        d.text((cx, gy0 - 2), title, font=f_h, fill=(196, 40, 30) if ci else INK)
        for si, (path, crop, cred, bus, enc) in enumerate(samples):
            y0 = gy0 + 26 + si * (ch_ + 26)
            src = Image.open(os.path.join(SRC, path)).convert("L")
            if crop:
                src = src.crop(crop)
            # fit-cover into the cell, at the cell aspect
            tw, th = 400, int(400 * ch_ / cw_ * 1.0)
            sw, sh = src.size
            sc = max(cw_ / sw, (ch_ - 2) / sh)
            src = src.resize((int(sw * sc) + 1, int(sh * sc) + 1), Image.LANCZOS)
            l = (src.width - cw_) // 2
            t = (src.height - ch_) // 2
            src = src.crop((l, t, l + cw_, t + ch_))
            a = np.asarray(src).astype(np.float32)
            a = 18 + a * (226 / 255.0)  # warm print tone on the sheet
            rgb = np.stack([a * 1.0, a * 0.97, a * 0.90], -1)
            im.paste(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), (cx, y0))
            d.rectangle([cx - 1, y0 - 1, cx + cw_, y0 + ch_], outline=INK, width=1)
            d.rectangle([cx, y0 + ch_ - 24, cx + 210, y0 + ch_], fill=INK)
            d.text((cx + 8, y0 + ch_ - 20), f"sample {'AB'[si]} · draw {417 + si:04d}", font=f_s, fill=(240, 236, 226))
            # coverage chips
            chips = [("bus", bus), ("encounter", enc)]
            xx = cx + cw_ - 8
            for name, ok in reversed(chips):
                txt = ({True: "+ ", False: "x ", "~": "~ "}[ok]) + name + (" (cable car)" if ok == "~" else "")
                tw2 = d.textlength(txt, font=f_s)
                xx -= tw2 + 16
                col = {True: (40, 120, 60), False: (196, 40, 30), "~": (176, 128, 20)}[ok]
                d.rectangle([xx, y0 + 8, xx + tw2 + 10, y0 + 28], fill=col)
                d.text((xx + 5, y0 + 11), txt, font=f_s, fill=(250, 248, 240))
                xx -= 6
            d.text((cx, y0 + ch_ + 4), cred, font=font(MONO, 11), fill=(90, 84, 76))
    # red anchor ring on the encounter in the overhead sample A, and the bus in baseline A
    rx, ry = gx0 + cw_ + 28, gy0 + 26
    d.ellipse([rx + 296, ry + 112, rx + 470, ry + 240], outline=(196, 40, 30), width=3)
    d.text((36, 694), "coverage  baseline: bus 2/2, encounter 1/2   delta: bus 0/2 (1 cable car), encounter 1/2   ->  delta B fails event coverage: drift",
           font=f_s, fill=INK)
    a = np.asarray(im).astype(np.float32)
    a += rng.normal(0, 3, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ======================================================================= board
def board(kfs, names):
    ref = Image.open(os.path.join(REF, "martinoCharcoal.webp")).convert("RGB")
    cw = 640
    ch = 360
    lab = 34
    out = Image.new("RGB", (cw * 2 + 30, (ch + lab) * 2 + 30), (20, 20, 20))
    d = ImageDraw.Draw(out)
    f = font(SANS_B, 18)
    tiles = [("REFERENCE  Mauro Martino, Exercises in Style (2023)", ref)] + list(zip(names, kfs))
    for k, (name, img) in enumerate(tiles):
        x, y = 10 + (k % 2) * (cw + 10), 10 + (k // 2) * (ch + lab + 10)
        t = img.copy()
        sc = min(cw / t.width, ch / t.height)
        t = t.resize((int(t.width * sc), int(t.height * sc)), Image.LANCZOS)
        out.paste(t, (x + (cw - t.width) // 2, y + lab))
        d.text((x + 4, y + 6), name, font=f, fill=(240, 236, 226))
    return out


if __name__ == "__main__":
    names = ["1 · CUT-PAPER PLATFORM (silhouette puppets)", "2 · STITCHED OVERHEAD (procedural embroidery)",
             "3 · THE ARCHIVE ANSWERS (archive samples)"]
    kfs = [kf1(), kf2(), kf3()]
    for i, k in enumerate(kfs, 1):
        assert k.size == (W, H)
        k.save(os.path.join(HERE, f"kf-{i}.png"))
    b = board(kfs, names)
    assert b.width <= 2000
    b.save(os.path.join(HERE, "board.jpg"), quality=88)
    print("ok", b.size)
