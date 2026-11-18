# Proposal keyframes for bang-bang.  Usage:
#   python3 -I kf.py <sources dir> <out dir> <reference.webp> [123]
# kf-1  handmade pen storyboard page (all drawn here).
# kf-2  cut-paper collage puppets from PD engravings (Commons): PSM 1894-95 Lilienthal "the start",
#       Penaud's flying models plate, Specht's crow for Brehms Tierleben (1911).
# kf-3  archive: frames of the 1933 Century of Progress high dive (Moving Image Archive cache) with
#       handmade paper wings and the bird's pen commentary.
import sys, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pen

SRC, OUT, REF = sys.argv[1:4]
WHICH = sys.argv[4] if len(sys.argv) > 4 else "123"
W, H = 1280, 720
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def rot(pts, cx, cy, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


# ------------------------------------------------------------------ pen figures
def bird(k, x, y, s=1.0, facing=1, look=0, w=1.6):
    """A pigeon in pen, perched. (x,y) = feet."""
    f = lambda px, py: (x + facing * px * s, y + py * s)
    k.ellipse(*f(0, -16), 17 * s, 11 * s, rot=-12 * facing, width=w)            # body
    k.ellipse(*f(14 + look, -33), 7 * s, 7 * s, width=w)                         # head
    k.line([f(20 + look, -35), f(27 + look, -33), f(20 + look, -31)], width=w * 0.9)  # beak
    k.dot(*f(16 + look, -35), 1.4 * s)                                            # eye
    k.curve([f(-6, -22), f(-14, -16), f(-24, -14)], width=w * 0.8)               # wing line
    k.line([f(-16, -12), f(-32, -6), f(-28, -14)], width=w)                      # tail
    k.line([f(-2, -6), f(-3, 0)], width=w * 0.8); k.line([f(4, -6), f(5, 0)], width=w * 0.8)


def flying_bird(k, x, y, s=1.0, flap=0.0, w=1.5):
    k.ellipse(x, y, 13 * s, 6 * s, width=w)
    k.ellipse(x + 15 * s, y - 3 * s, 5 * s, 5 * s, width=w)
    k.line([(x + 19 * s, y - 4 * s), (x + 25 * s, y - 2 * s), (x + 19 * s, y - 1 * s)], width=w * 0.9)
    k.dot(x + 16 * s, y - 4.5 * s, 1.2 * s)
    up = -18 * s * (1 - flap) + 10 * s * flap
    k.curve([(x - 2 * s, y - 3 * s), (x - 10 * s, y + up * 0.6), (x - 22 * s, y + up)], width=w)
    k.curve([(x + 2 * s, y - 3 * s), (x - 4 * s, y + up * 0.5), (x - 12 * s, y + up * 0.9)], width=w * 0.8)
    k.line([(x - 13 * s, y), (x - 24 * s, y + 3 * s), (x - 22 * s, y - 3 * s)], width=w)


def inventor(k, x, y, s=1.0, ang=0.0, pose="run", w=1.7, wing_up=0.0, upto=1.0):
    """Fictional inventor in a bowler hat with two paper wings strapped to his arms. (x,y) = hip.
    ang rotates the whole figure (nose-up is negative).  `upto` drops the last strokes (a drawing in progress)."""
    strokes = []
    P = lambda px, py: (x + px * s, y + py * s)
    # body
    strokes.append(("curve", [P(0, 0), P(2, -22), P(1, -44)]))
    strokes.append(("ell", (*P(3, -56), 11 * s, 12 * s)))
    strokes.append(("line", [P(-9, -66), P(15, -66)]))                               # hat brim
    strokes.append(("curve", [P(-6, -66), P(-5, -78), P(3, -82), P(11, -78), P(12, -66)]))
    strokes.append(("curve", [P(8, -52), P(13, -50), P(16, -52)]))                    # moustache
    strokes.append(("dot", (*P(9, -58), 1.3 * s)))
    strokes.append(("curve", [P(0, -40), P(-8, -20), P(-14, -4)]))                     # coat tail
    if pose == "run":
        legs = [[P(0, 0), P(12, 14), P(8, 32), P(16, 34)], [P(0, 0), P(-10, 12), P(-20, 26), P(-14, 30)]]
    elif pose == "fall":
        legs = [[P(0, 0), P(10, 16), P(22, 20)], [P(0, 0), P(-6, 18), P(4, 30)]]
    else:
        legs = [[P(0, 0), P(6, 16), P(4, 32), P(12, 33)], [P(0, 0), P(-6, 16), P(-12, 30), P(-6, 32)]]
    strokes += [("curve", l) for l in legs]
    # paper wings: a rib frame (the spar is the arm) and a sheet
    lift = -26 * wing_up
    for side, sh in ((1, 1.0), (-1, 0.82)):
        sx, sy = P(1, -40)
        tip = P(side * 0 + 70 * sh, -46 + lift)
        rear = P(62 * sh, -14 + lift * 0.6)
        root = P(-4, -20)
        if side < 0:
            tip = P(-58 * sh, -48 + lift * 0.9); rear = P(-50 * sh, -16 + lift * 0.5); root = P(4, -20)
        strokes.append(("line", [(sx, sy), tip]))
        strokes.append(("curve", [tip, ((tip[0] + rear[0]) / 2 + side * 6 * s, (tip[1] + rear[1]) / 2), rear]))
        strokes.append(("curve", [rear, ((rear[0] + root[0]) / 2, (rear[1] + root[1]) / 2 + 6 * s), root]))
        for t in (0.33, 0.66):
            a = (sx + (tip[0] - sx) * t, sy + (tip[1] - sy) * t)
            b = (root[0] + (rear[0] - root[0]) * t, root[1] + (rear[1] - root[1]) * t)
            strokes.append(("line", [a, b]))
    n = max(1, int(len(strokes) * upto))
    for kind, data in strokes[:n]:
        if kind == "curve":
            k.curve(rot(data, x, y - 30 * s, ang), width=w)
        elif kind == "line":
            k.line(rot(data, x, y - 30 * s, ang), width=w)
        elif kind == "ell":
            cx, cy = rot([data[:2]], x, y - 30 * s, ang)[0]
            k.ellipse(cx, cy, data[2], data[3], rot=ang, width=w)
        elif kind == "dot":
            cx, cy = rot([data[:2]], x, y - 30 * s, ang)[0]
            k.dot(cx, cy, data[2])


def panel_frame(k, x0, y0, x1, y1, w=1.6):
    k.line([(x0, y0), (x1, y0)], width=w); k.line([(x1, y0), (x1, y1)], width=w)
    k.line([(x1, y1), (x0, y1)], width=w); k.line([(x0, y1), (x0, y0)], width=w)
    k.dot(x0 + 16, y0 + 16, 6.5)  # the punched pin, inked like the reference's dots


def arrow(k, x0, y0, x1, y1, w=1.8):
    k.line([(x0, y0), (x1, y1)], width=w)
    a = math.atan2(y1 - y0, x1 - x0)
    for d in (2.6, -2.6):
        k.line([(x1, y1), (x1 - 14 * math.cos(a + d * 0.18), y1 - 14 * math.sin(a + d * 0.18))], width=w)


# ------------------------------------------------------------------ kf-1: the bird's notebook (handmade)
def kf1():
    page = pen.paper(W, H, 11)
    ghost = pen.Ink(W, H, 5)  # show-through of the facing page: mirrored writing at low density
    rg = np.random.default_rng(3)
    for i, ln in enumerate(["1890 un autre essaie", "avec un parapluie", "et un chapeau de paille", "pas mal du tout",
                            "", "le vent est d'est", "il tombe dans l'herbe"]):
        pen.hand(ghost, ln, 640, 120 + i * 62, size=1.2, width=1.3, rng=rg)
    gc = np.ascontiguousarray(ghost.coverage()[:, ::-1])
    page = pen.put_ink(page, gc * 0.045, ink=(120, 110, 100), bleed=2.0, seed=2)

    k = pen.Ink(W, H, 21)
    PX0, PX1 = 150, 520
    rows = [(46, 246), (262, 462), (478, 678)]
    for (y0, y1) in rows:
        panel_frame(k, PX0, y0, PX1, y1)
    # panel 1: run-up on the roof; the pigeon on the chimney watches
    y0, y1 = rows[0]
    roof = [(PX0, y1 - 50), (PX0 + 210, y1 - 50)]
    k.line(roof, width=1.8); k.line([(PX0 + 210, y1 - 50), (PX0 + 210, y1)], width=1.8)
    for xx in range(PX0 + 14, PX0 + 205, 26):
        k.line([(xx, y1 - 50), (xx + 8, y1 - 40)], width=1.0)   # tiles
    k.line([(PX0 + 40, y1 - 50), (PX0 + 40, y1 - 92), (PX0 + 64, y1 - 92), (PX0 + 64, y1 - 50)], width=1.8)  # chimney
    bird(k, PX0 + 52, y1 - 92, s=0.95, facing=1)
    inventor(k, PX0 + 160, y1 - 84, s=0.95, ang=6, pose="run")
    k.line([(PX0 + 220, y1 - 8), (PX1 - 8, y1 - 8)], width=1.2)  # far ground
    # panel 2: the stall -- nose up 35 deg, pigeon level beside him; reference-style A/B labels
    y0, y1 = rows[1]
    inventor(k, PX0 + 170, y0 + 140, s=1.0, ang=-35, pose="air", wing_up=0.4)
    flying_bird(k, PX0 + 300, y0 + 66, s=1.0, flap=0.3)
    for i in range(3):
        k.line([(PX0 + 60 - i * 12, y0 + 120 + i * 18), (PX0 + 92 - i * 12, y0 + 112 + i * 18)], width=1.0)  # air marks
    k.line([(PX0 + 8, y1 - 10), (PX1 - 8, y1 - 10)], width=1.2)
    pen.hand(k, "A", PX0 + 252, y0 + 158, size=0.9, width=1.4, rng=np.random.default_rng(8))
    arrow(k, PX0 + 248, y0 + 150, PX0 + 222, y0 + 128)
    pen.hand(k, "B", PX0 + 96, y0 + 54, size=0.9, width=1.4, rng=np.random.default_rng(9))
    arrow(k, PX0 + 118, y0 + 54, PX0 + 150, y0 + 70)
    # panel 3: the fall, still being drawn (substitution in progress: last strokes not yet down)
    y0, y1 = rows[2]
    k.line([(PX0 + 8, y1 - 30), (PX1 - 8, y1 - 30)], width=1.4)
    for xx in range(PX0 + 30, PX0 + 200, 18):  # flowerbed
        k.curve([(xx, y1 - 30), (xx + 3, y1 - 44), (xx + 8, y1 - 50)], width=1.0)
    inventor(k, PX0 + 120, y1 - 70, s=0.95, ang=-118, pose="fall", wing_up=0.9, upto=0.72)
    bird(k, PX1 - 70, y1 - 30, s=0.95, facing=-1, look=2)
    pen.hand(k, "Krach!", PX0 + 196, y0 + 70, size=1.15, width=1.6, rng=np.random.default_rng(12))

    # right column: the bird's commentary (the voice), set on the same rows as the panels
    TX = 600; rg = np.random.default_rng(31)
    pen.hand(k, "7", 1190, 40, size=0.8, width=1.2, rng=rg)
    pen.hand(k, "1874 Monsieur Pique-Vent court sur le toit avec deux ailes de papier (c'est un bon toit).", TX, 110,
             size=1.05, width=1.45, rng=rg, maxw=560, line_h=50)
    mx, _ = pen.hand(k, "Il lève le nez pour", TX, 320, size=1.05, width=1.45, rng=rg)
    m2, _ = pen.hand(k, "monter.", mx, 320, size=1.05, width=1.45, rng=rg)
    pen.hand(k, "Moi aussi je lève le nez : c'est pour me poser...", TX, 370, size=1.05, width=1.45, rng=rg, maxw=560, line_h=50)
    pen.hand(k, "A  ailes de papier", TX + 40, 470, size=0.95, width=1.35, rng=rg)
    pen.hand(k, "B  le nez à 35°", TX + 40, 512, size=0.95, width=1.35, rng=rg)
    # the line being written now (write-on stops mid-word: cue sync point)
    ex, ey = pen.hand(k, "Donc il se pose. Très bien, un peu vite", TX, 600, size=1.05, width=1.45, rng=rg, upto=0.78)
    page = pen.put_ink(page, k.coverage(), seed=4)
    # a strike-through like the reference's crossed word
    k2 = pen.Ink(W, H, 77)
    k2.line([(mx - 4, 312), (m2 - 10, 306)], width=1.7)
    k2.line([(mx - 2, 304), (m2 - 8, 316)], width=1.5)
    pen.hand(k2, "s'arrêter", mx + 2, 282, size=0.8, width=1.2, rng=np.random.default_rng(5))
    # graphite timing notes in the margin (the board fixture: frame ranges per row)
    g = pen.Ink(W, H, 78); rg2 = np.random.default_rng(40)
    for (y0, y1), t in zip(rows, ["BB-07  18.0-21.0 s", "BB-08  21.0-24.0 s", "BB-09  24.0-27.5 s"]):
        pen.hand(g, t, 22, y0 + 40, size=0.55, width=0.9, rng=rg2, maxw=110, line_h=24)
    page = pen.put_ink(page, g.coverage() * 0.55, ink=(95, 95, 100), seed=13)
    page = pen.put_ink(page, k2.coverage(), seed=9)
    return Image.fromarray(page.astype(np.uint8))


# ------------------------------------------------------------------ kf-2: cut-paper collage puppets (foraged engravings)
def fill_small_holes(m, maxarea):
    inv = (m == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    out = m.copy()
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < maxarea and x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            out[lab == i] = 255
    return out


def scissor(m, seed, amt=1.4):
    """Scissor edge: tiny low-frequency wobble so the cut is not the line."""
    r = np.random.default_rng(seed); H_, W_ = m.shape
    nz = cv2.resize(r.normal(0, 1, (H_ // 10 + 2, W_ // 10 + 2)).astype(np.float32), (W_, H_), interpolation=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) + nz * amt * 40
    return np.where(a > 127, 255, 0).astype(np.uint8)


def engraving_piece(img, mask, card=(238, 230, 210)):
    """RGBA piece: the engraving's ink printed on a cream card, alpha from the scissor mask."""
    g = np.asarray(img.convert("L"), np.float32) / 255
    g = np.clip((g - 0.12) / 0.8, 0, 1) ** 1.2
    rgb = np.stack([c * (0.1 + 0.9 * g) for c in card], -1)
    return Image.fromarray(np.dstack([rgb, mask]).astype(np.uint8), "RGBA")


def line_cut(img, close=7, dil=4, holes=4000, thr=170, seed=0):
    g = np.asarray(img.convert("L"))
    ink = (g < thr).astype(np.uint8) * 255
    m = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    m = fill_small_holes(m, holes)
    return scissor(m, seed)


def place(canvas, piece, cx, cy, ang=0.0, scale=1.0, pivot=None, shadow=(9, 12), sh_blur=5, sh_a=0.38):
    """Paste an RGBA piece rotated about `pivot` (piece px) whose pivot lands at (cx,cy); with a cast shadow."""
    p = piece
    if scale != 1.0:
        p = p.resize((max(1, int(p.width * scale)), max(1, int(p.height * scale))), Image.LANCZOS)
    pv = (pivot[0] * scale, pivot[1] * scale) if pivot else (p.width / 2, p.height / 2)
    # pad so the pivot is the centre, then rotate
    M_ = int(3 * sh_blur + max(abs(shadow[0]), abs(shadow[1]))) + 8  # room for the blurred shadow
    padw = int(2 * max(pv[0], p.width - pv[0])) + 2 * M_; padh = int(2 * max(pv[1], p.height - pv[1])) + 2 * M_
    big = Image.new("RGBA", (padw, padh), (0, 0, 0, 0))
    ox, oy = int(padw / 2 - pv[0]), int(padh / 2 - pv[1]); big.paste(p, (ox, oy))
    big = big.rotate(ang, resample=Image.BICUBIC)
    x0, y0 = int(cx - padw / 2), int(cy - padh / 2)
    a = np.asarray(big)[..., 3].astype(np.float32) / 255
    sh = cv2.GaussianBlur(a, (0, 0), sh_blur) * sh_a
    cv_ = np.asarray(canvas).astype(np.float32)
    def blend(arr, alpha, x, y, rgb=None):
        H_, W_ = alpha.shape
        X0, Y0 = max(0, x), max(0, y); X1, Y1 = min(cv_.shape[1], x + W_), min(cv_.shape[0], y + H_)
        if X1 <= X0 or Y1 <= Y0:
            return
        al = alpha[Y0 - y:Y1 - y, X0 - x:X1 - x][..., None]
        src = (np.zeros_like(cv_[Y0:Y1, X0:X1]) + np.asarray(rgb, np.float32)) if rgb is not None else arr[Y0 - y:Y1 - y, X0 - x:X1 - x, :3]
        cv_[Y0:Y1, X0:X1] = cv_[Y0:Y1, X0:X1] * (1 - al) + src * al
    blend(None, sh, x0 + shadow[0], y0 + shadow[1], rgb=(40, 34, 28))
    blend(np.asarray(big).astype(np.float32), a, x0, y0)
    return Image.fromarray(cv_.astype(np.uint8)), (x0, y0, padw, padh)


def brad(canvas, x, y, r=5):
    d = ImageDraw.Draw(canvas)
    d.ellipse([x - r - 1, y - r + 1, x + r + 1, y + r + 3], fill=(60, 50, 35))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(176, 140, 72))
    d.ellipse([x - r + 2, y - r + 1, x, y - 1], fill=(222, 196, 130))


def torn_card(w, h, seed, tone, top_only=False, amt=7):
    r = np.random.default_rng(seed)
    m = np.zeros((h, w), np.uint8)
    xs = np.arange(w)
    edge = amt + amt * np.interp(xs, np.linspace(0, w, 30), r.normal(0, 0.5, 30)) + r.normal(0, 0.8, w)
    for x in xs:
        m[int(max(0, edge[x])):, x] = 255
    tex = pen.paper(w, h, seed + 1, tone=tone)
    rgb = tex
    # torn fibre edge: lighter rim
    rim = cv2.dilate(255 - m, np.ones((5, 5), np.uint8)) & m
    rgb = np.where(rim[..., None] > 0, np.minimum(255, rgb + 22), rgb)
    return Image.fromarray(np.dstack([rgb, m]).astype(np.uint8), "RGBA")


def kf2():
    canvas = Image.fromarray(pen.paper(W, H, 51, tone=(240, 233, 214)).astype(np.uint8))
    # --- foraged pieces
    lil = Image.open(os.path.join(SRC, "lilienthal_start.jpg")).convert("RGB")
    m = line_cut(lil, seed=1)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    legs_poly = np.int32([(368, 262), (424, 262), (428, 300), (424, 362), (380, 362), (346, 360), (350, 318), (366, 290)])
    lp = np.zeros_like(m); cv2.fillPoly(lp, [legs_poly], 255)
    legs_m = m & lp
    body_m = m.copy(); body_m[lp > 0] = 0; body_m[(yy > 300) & (xx < 700)] = 0
    body_m = cv2.morphologyEx(body_m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    glider = engraving_piece(lil, body_m); legs = engraving_piece(lil, legs_m)
    gl_bb = glider.getbbox(); glider = glider.crop(gl_bb); lg_bb = legs.getbbox(); legs = legs.crop(lg_bb)

    pn = Image.open(os.path.join(SRC, "penaud_models.jpg")).convert("RGB")
    heli_img = pn.crop((115, 82, 335, 240)); heli = engraving_piece(heli_img, line_cut(heli_img, seed=2, thr=150, holes=600)).crop()
    plane_img = pn.crop((130, 280, 485, 462)); plane = engraving_piece(plane_img, line_cut(plane_img, seed=3, thr=150, holes=600))

    crow = Image.open(os.path.join(SRC, "crow_specht_960.png")).convert("RGB")
    a = np.asarray(crow)
    gm = np.full(a.shape[:2], cv2.GC_BGD, np.uint8); gm[95:600, 38:925] = cv2.GC_PR_BGD
    dark = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY) < 60
    gm[95:600, 38:925][dark[95:600, 38:925]] = cv2.GC_PR_FGD
    gm[200:360, 300:600] = cv2.GC_FGD; gm[330:390, 540:700] = cv2.GC_PR_FGD
    cv2.fillPoly(gm, [np.int32([(600, 140), (690, 108), (800, 150), (858, 228), (770, 262), (705, 330), (560, 392), (520, 372)])], cv2.GC_FGD)
    cv2.fillPoly(gm, [np.int32([(760, 250), (880, 260), (915, 330), (890, 430), (850, 515), (820, 470), (760, 400)])], cv2.GC_FGD)
    cv2.fillPoly(gm, [np.int32([(40, 470), (300, 440), (470, 445), (478, 610), (40, 610)])], cv2.GC_BGD)
    cv2.fillPoly(gm, [np.int32([(640, 540), (930, 520), (930, 620), (640, 620)])], cv2.GC_BGD)
    box = gm[395:530, 470:660]; lite = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)[395:530, 470:660] > 110
    box[lite] = cv2.GC_BGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), gm, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    cm = np.where((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cm, 8)
    big = 1 + int(np.argmax(st[1:, 4])); cm = np.where(lab == big, 255, 0).astype(np.uint8)
    cm = fill_small_holes(cv2.morphologyEx(cm, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), 20000)
    cm = scissor(cm, 4, amt=1.0)
    hp = np.zeros_like(cm); cv2.fillPoly(hp, [np.int32([(712, 150), (960, 150), (960, 545), (805, 545), (765, 405), (700, 330)])], 255)
    head = engraving_piece(crow, cm & hp, card=(236, 230, 214)); body = cm.copy(); body[hp > 0] = 0
    cbody = engraving_piece(crow, body, card=(236, 230, 214))
    CS = 0.36

    # --- handmade set: torn ground strip, a roof gable of card, pen sky marks, the storyboard frame
    k = pen.Ink(W, H, 61)
    for (x, y) in [(470, 150), (520, 190), (430, 120)]:
        k.curve([(x, y), (x + 40, y - 6), (x + 80, y + 2)], width=1.2)
    gable = torn_card(300, 420, 71, tone=(196, 184, 160), amt=4)
    g_m = np.zeros((420, 300), np.uint8); cv2.fillPoly(g_m, [np.int32([(0, 120), (150, 20), (300, 120), (300, 420), (0, 420)])], 255)
    ga = np.asarray(gable).copy(); ga[..., 3] = np.minimum(ga[..., 3], scissor(g_m, 72)); gable = Image.fromarray(ga, "RGBA")
    canvas, _ = place(canvas, gable, 1080, 470, shadow=(6, 8))
    ground = torn_card(1300, 170, 81, tone=(205, 196, 172), amt=9)
    canvas, _ = place(canvas, ground, 640, 660, shadow=(0, -6), sh_a=0.25)
    kk = pen.Ink(W, H, 62)
    for i in range(9):  # pen tiles on the gable
        y = 330 + i * 26
        kk.line([(935, y), (1225, y + 2)], width=1.0, jit=0.8)
    for xx_ in range(950, 1220, 34):
        kk.line([(xx_, 300 + (xx_ - 930) % 50), (xx_ + 4, 560)], width=0.8, jit=0.6, dash=13)
    kk.line([(60, 40), (1220, 40)], width=1.6); kk.line([(1220, 40), (1220, 690)], width=1.6)
    kk.line([(1220, 690), (60, 690)], width=1.6); kk.line([(60, 690), (60, 40)], width=1.6)
    kk.dot(80, 60, 7)
    pg = np.asarray(canvas).astype(np.float32)
    pg = pen.put_ink(pg, np.maximum(k.coverage(), kk.coverage()), seed=7)
    canvas = Image.fromarray(pg.astype(np.uint8))

    # earlier attempts, discarded on the ground: the rubber-band rotor and the paper aeroplane
    canvas, _ = place(canvas, heli, 300, 600, ang=96, scale=0.62, shadow=(5, 6), sh_blur=3)
    canvas, _ = place(canvas, plane, 760, 586, ang=-28, scale=0.55, shadow=(5, 6), sh_blur=3)
    # the witness: Specht's crow on the ground at left, head pinned at the neck and tipped up to watch
    canvas, bb = place(canvas, cbody, 210, 512, scale=CS, pivot=(480, 350), shadow=(6, 6), sh_blur=3)
    canvas, _ = place(canvas, head, 210 + (735 - 480) * CS, 512 + (300 - 350) * CS, ang=58, scale=CS, pivot=(735, 300),
                      shadow=(5, 5), sh_blur=3)
    brad(canvas, int(210 + (735 - 480) * CS), int(512 + (300 - 350) * CS), r=4)
    # the attempt: the glider at the stall, nose (left) up 32 deg, legs swinging forward on their pin
    hip = (395 - gl_bb[0], 268 - gl_bb[1])
    GS = 0.62; GX, GY = 700, 350; GA = -32
    canvas, _ = place(canvas, glider, GX, GY, ang=GA, scale=GS, pivot=hip, shadow=(26, 40), sh_blur=9, sh_a=0.30)
    canvas, _ = place(canvas, legs, GX, GY, ang=GA - 22, scale=GS, pivot=(395 - lg_bb[0], 266 - lg_bb[1]), shadow=(26, 40),
                      sh_blur=9, sh_a=0.30)
    brad(canvas, GX, GY, r=5)

    # the voice: a torn slip of notepaper pinned to the board, written in the bird's hand
    slip = torn_card(430, 150, 91, tone=(247, 243, 232), amt=5)
    sk = pen.Ink(430, 150, 92); rg = np.random.default_rng(93)
    pen.hand(sk, "Il lève le nez.", 22, 52, size=0.95, width=1.4, rng=rg)
    pen.hand(sk, "Moi aussi, quand je veux m'arrêter.", 22, 100, size=0.95, width=1.4, rng=rg, maxw=400)
    sa = np.asarray(slip).copy(); sa[..., :3] = pen.put_ink(sa[..., :3].astype(np.float32), sk.coverage(), seed=3).astype(np.uint8)
    canvas, _ = place(canvas, Image.fromarray(sa, "RGBA"), 330, 190, ang=-2.0, shadow=(5, 7), sh_blur=4)
    brad(canvas, 134, 136, r=5)
    # graphite: board id and time
    g = pen.Ink(W, H, 94)
    pen.hand(g, "BB-08   21.0-24.0 s   le décrochage", 110, 72, size=0.6, width=0.9, rng=np.random.default_rng(95))
    pg = pen.put_ink(np.asarray(canvas).astype(np.float32), g.coverage() * 0.6, ink=(90, 90, 96), seed=8)
    return Image.fromarray(pg.astype(np.uint8))


# ------------------------------------------------------------------ kf-3: the archive dive, annotated by the bird
def print_of(path, w, h, border=12, seed=0, crop=None):
    """A silver print on cream paper: grey frame, warm-neutral tone, white border, slight lifted blacks."""
    im = Image.open(path).convert("L")
    if crop:
        im = im.crop(crop)
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    a = 0.06 + 0.9 * a
    tone = np.stack([a * 246, a * 240, a * 226], -1)
    out = np.full((h + 2 * border, w + 2 * border, 3), (248, 245, 236), np.float32)
    out[border:border + h, border:border + w] = tone
    alpha = np.full(out.shape[:2], 255, np.uint8)
    return Image.fromarray(np.dstack([out, alpha]).astype(np.uint8), "RGBA")


def kf3():
    canvas = Image.fromarray(pen.paper(W, H, 101, tone=(241, 235, 219)).astype(np.uint8))
    FR = os.path.join(SRC, "frames")
    CR = (40, 6, 296, 198)  # 256x192 of the 320x240 frame: closer on the diver, tower kept at the edge
    BW, BH = 640, 480; sx = BW / (CR[2] - CR[0]); bx, by, bang = 56, 50, -1.0
    big = print_of(os.path.join(FR, "dive_13.25.png"), BW, BH, crop=CR)
    canvas, _ = place(canvas, big, bx + big.width / 2, by + big.height / 2, ang=bang, shadow=(6, 8), sh_blur=5, sh_a=0.32)
    # photo corners (black paper mounts), handmade
    d = ImageDraw.Draw(canvas)
    for (cx, cy, dx, dy) in [(bx - 4, by - 2, 1, 1), (bx + big.width + 6, by + 10, -1, 1), (bx - 14, by + big.height - 6, 1, -1),
                             (bx + big.width - 4, by + big.height + 6, -1, -1)]:
        d.polygon([(cx, cy), (cx + 46 * dx, cy), (cx, cy + 46 * dy)], fill=(34, 32, 30))
    # the board sequence: three small prints, leap / nose drops / water
    smalls = [("dive_9.75.png", "9.8"), ("dive_14.75.png", "14.8"), ("dive_20.0.png", "20.0")]
    for i, (f, t) in enumerate(smalls):
        sp = print_of(os.path.join(FR, f), 160, 120, border=7)
        canvas, _ = place(canvas, sp, 150 + i * 215, 640, ang=[1.5, -1.0, 2.0][i], shadow=(4, 5), sh_blur=3, sh_a=0.3)
    k = pen.Ink(W, H, 111)
    # the bird's pen on the print: paper wings drawn onto the diver's arms (rotoscope), and two paths
    def P(x, y):  # source px (320x240) -> page, through the print's placement and small rotation
        X = bx + 12 + (x - CR[0]) * sx; Y = by + 12 + (y - CR[1]) * sx
        return rot([(X, Y)], bx + big.width / 2, by + big.height / 2, -bang)[0]
    sh_ = P(186, 80)
    tip, rear, root = P(205, 34), P(236, 62), P(222, 80)
    # leading spar, then a scalloped paper trailing edge (three bays) back to the hip
    k.curve([sh_, P(194, 52), tip], width=2.0)
    k.curve([tip, P(222, 40), P(222, 50), P(228, 50), P(236, 62)], width=1.6)
    k.curve([rear, P(229, 66), P(231, 72), P(226, 74), root], width=1.6)
    for t in (0.35, 0.68):
        a_ = (sh_[0] + (tip[0] - sh_[0]) * t, sh_[1] + (tip[1] - sh_[1]) * t)
        b_ = (root[0] + (rear[0] - root[0]) * t, root[1] + (rear[1] - root[1]) * t)
        k.line([a_, b_], width=1.3)
    # B: the hoped-for glide (dashed, level, far) vs C: the arc the bird expects (solid, down)
    k.curve([P(168, 84), P(130, 85), P(90, 88), P(50, 92)], width=1.5, dash=9)
    k.curve([P(170, 90), P(152, 112), P(138, 150), P(132, 186)], width=1.9)
    arrow(k, *P(134, 170), *P(132, 188), w=1.9)
    pen.hand(k, "A", *P(206, 26), size=0.95, width=1.5, rng=np.random.default_rng(1))
    pen.hand(k, "B", *P(50, 86), size=0.95, width=1.5, rng=np.random.default_rng(2))
    pen.hand(k, "C", *P(146, 170), size=0.95, width=1.5, rng=np.random.default_rng(3))
    # the witness itself, drawn sitting on the top of the tower
    flying_bird(k, *P(258, 26), s=1.0, flap=0.6)
    # arrows between the small prints
    for i in range(2):
        arrow(k, 240 + i * 215, 640, 272 + i * 215, 640, w=1.5)
    # the voice, right column
    TX = 790; rg = np.random.default_rng(121)
    _, y = pen.hand(k, "1933 Celui-ci n'a pas d'ailes du tout. Je lui en dessine deux.", TX, 92, size=1.0, width=1.4,
                    rng=rg, maxw=450, line_h=46)
    y += 56
    for ln in ["A  ailes de papier (de moi)", "B  ce qu'il espère", "C  ce que je sais"]:
        pen.hand(k, ln, TX + 20, y, size=0.92, width=1.3, rng=rg); y += 42
    y += 40
    _, y = pen.hand(k, "Il ouvre les bras pour planer. C'est juste ; mais l'air ne le porte pas, alors il choisit l'eau.",
                    TX, y, size=1.0, width=1.4, rng=rg, maxw=450, line_h=46)
    pen.hand(k, "Raisonnable.  ... Plouf.", TX + 90, y + 64, size=1.05, width=1.5, rng=rg)
    canvas = Image.fromarray(pen.put_ink(np.asarray(canvas).astype(np.float32), k.coverage(), seed=12).astype(np.uint8))
    g = pen.Ink(W, H, 131); rg2 = np.random.default_rng(132)
    pen.hand(g, "BB-08  21.0-24.0 s  (source 13.2 s)", bx + 6, 34, size=0.55, width=0.9, rng=rg2)
    for i, (_, t) in enumerate(smalls):
        pen.hand(g, t + " s", 72 + i * 215, 572, size=0.5, width=0.85, rng=rg2)
    pen.hand(g, "Century of Progress, Wings of a Century (1933)", TX, 690, size=0.5, width=0.85, rng=rg2)
    pg = pen.put_ink(np.asarray(canvas).astype(np.float32), g.coverage() * 0.6, ink=(90, 90, 96), seed=14)
    return Image.fromarray(pg.astype(np.uint8))


def board(names):
    CW, CH, LB, G = 960, 540, 40, 12
    out = Image.new("RGB", (2 * CW + 3 * G, 2 * (CH + LB) + 3 * G), (24, 24, 26))
    d = ImageDraw.Draw(out); f = ImageFont.truetype(MONO, 20)
    ref = Image.open(REF).convert("RGB"); ref.thumbnail((CW, CH), Image.LANCZOS)
    cells = [("REFERENCE  Bang Bang storyboard page (Drouot / Aguttes)", ref)]
    for i, n in enumerate(names):
        cells.append((n, Image.open(os.path.join(OUT, "kf-%d.png" % (i + 1))).convert("RGB").resize((CW, CH), Image.LANCZOS)))
    for i, (lab, im) in enumerate(cells):
        x = G + (i % 2) * (CW + G); y = G + (i // 2) * (CH + LB + G)
        d.text((x + 6, y + 9), lab, font=f, fill=(236, 232, 220))
        out.paste(im, (x + (CW - im.width) // 2, y + LB + (CH - im.height) // 2))
    out.save(os.path.join(OUT, "board.jpg"), quality=90)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "1" in WHICH:
        kf1().save(os.path.join(OUT, "kf-1.png"))
    if "2" in WHICH:
        kf2().save(os.path.join(OUT, "kf-2.png"))
    if "3" in WHICH:
        kf3().save(os.path.join(OUT, "kf-3.png"))
    board(["1  LE CARNET DE L'OISEAU  pen storyboard, drawn frame by frame",
           "2  PLANCHE GRAVEE  cut-paper puppets from PD engravings",
           "3  LE PLONGEON  1933 archive dive + rotoscoped pen wings"])
