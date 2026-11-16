"""TEST SHOT: baseline (street-side, cut-paper), seed 0417, clip t = 0.00 .. 7.00 s.
Defining beat: the shove on the rear platform at clip t = 1.20 s.

FORAGED : 1916 Agence Rol bus photograph (Commons, PD), rectified + GrabCut (plates.py),
          printed through CLAHE + threshold + tint block.  Sound bed: see ledger.
HANDMADE: carved Haussmann facade, gouged pavement, rear platform/stanchion/chain/bell cord,
          carved destination board, articulated silhouette puppets (Reiniger rig, FK, pins,
          angle limits, replacement hands/heads, exposure sheet on twos), cord + coat-tail
          secondary dynamics (#41).

Run: python3 -I build.py [--stills t1 t2 ...]
"""
import json, math, sys, hashlib, wave, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
sys.path.insert(0, str(ROOT / "films"))
import kit  # noqa: E402  (rendering kit; not edited)

WS = ROOT / "films/swarm/mauro-martino-exercises-in-style"
MEDIA = ROOT / "films/sources/mauro-martino-exercises-in-style/test-shot"
PL = MEDIA / "plates"
SEED = 417
W, H, SS, FPS = 960, 540, 2, 24
CLIP = 7.0
NF = int(CLIP * FPS)

# ---------------------------------------------------------------- palette (sampled tokens)
INK = np.array((34, 33, 31), np.float32)
INK2 = np.array((45, 44, 42), np.float32)
DTINT = np.array((71, 68, 63), np.float32)
TINT = np.array((149, 142, 133), np.float32)
SHADE = np.array((211, 203, 188), np.float32)
PAPER = np.array((238, 230, 214), np.float32)


def rng(*key):
    """Per-element RNG stream keyed by (seed, element id). The renderer never draws from a shared RNG."""
    h = hashlib.sha1(repr((SEED,) + key).encode()).digest()
    return np.random.RandomState(int.from_bytes(h[:4], "little"))


def L(size=(W * SS, H * SS)):
    im = Image.new("L", size, 0)
    return im, ImageDraw.Draw(im)


def spindle(d, x, y, length, width, slope=0.0, fill=255):
    """A tapered V-gouge stroke (lens shape), in SS px."""
    n = 14
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        w = width * math.sin(math.pi * u) ** 0.7
        px, py = x + u * length, y + u * length * slope
        top.append((px, py - w / 2)); bot.append((px, py + w / 2))
    d.polygon(top + bot[::-1], fill=fill)


def starve(mask, key, amount=0.22, scale=(3, 40)):
    """Ink-starved key block: horizontal streak noise knocks holes into large ink areas only.
    Seeded per seed (static), never per frame."""
    r = rng("starve", key)
    h, w = mask.shape
    sy, sx = scale
    n = r.rand(h // sy + 2, w // sx + 2).astype(np.float32)
    n = cv2.resize(n, (w + 2 * sx, h + 2 * sy), interpolation=cv2.INTER_CUBIC)[sy:sy + h, sx:sx + w]
    fine = r.rand(h, w).astype(np.float32)
    inner = cv2.erode((mask > 0.5).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)
    hole = ((n > 1 - amount) & (fine > 0.35)).astype(np.float32) * inner
    return hole


# ---------------------------------------------------------------- stage (handmade carving)
GROUND_BUS = 380      # wheel contact line (film px)
BUILDING_BASE = 330
KERB = 414
GROUND_FG = 478       # foreground runners' feet


def build_stage():
    """Return colour image (SS) of the carved facade + gouged street, and its key mask."""
    Wd, Hd = W * SS, H * SS
    r = rng("facade")
    ink, di = L(); tint, dt = L(); shade, ds = L(); cuts, dc = L(); dark, dd = L()
    s = SS
    # sky: paper with shade gouges
    for _ in range(70):
        spindle(ds, r.uniform(-100, W) * s, r.uniform(0, 16) * s, r.uniform(40, 240) * s, r.uniform(1, 3) * s, r.uniform(-.01, .01))
    # mansard roof
    dd.polygon([(0, 18 * s), (Wd, 18 * s), (Wd, 54 * s), (0, 54 * s)], fill=255)
    di.rectangle([0, 16 * s, Wd, 19 * s], fill=255)
    off = r.uniform(0, 64)
    cols = [off + 64 * k for k in range(-1, 17)]
    for cx in cols:
        x0 = (cx + 20) * s
        di.rectangle([x0, 26 * s, x0 + 18 * s, 52 * s], fill=255)          # dormer
        di.polygon([(x0 - 3 * s, 27 * s), (x0 + 9 * s, 20 * s), (x0 + 21 * s, 27 * s)], fill=255)
        di.rectangle([x0 + 8 * s, 30 * s, x0 + 10 * s, 50 * s], fill=0)     # cream mullion cut
        di.rectangle([x0 + 3 * s, 38 * s, x0 + 15 * s, 39.5 * s], fill=0)
    for cx in cols[::3]:
        di.rectangle([(cx + 50) * s, 4 * s, (cx + 60) * s, 19 * s], fill=255)  # chimney stacks
    # tint gouges on the mansard (horizontal slate courses)
    for y in range(22, 54, 4):
        for _ in range(8):
            spindle(dc, r.uniform(-50, W) * s, (y + r.uniform(-.6, .6)) * s, r.uniform(30, 160) * s, r.uniform(.8, 1.8) * s)
    # cornice with dentil cuts
    di.rectangle([0, 54 * s, Wd, 64 * s], fill=255)
    for x in np.arange(off % 7, W, 7):
        di.rectangle([x * s, 60 * s, (x + 3) * s, 62.5 * s], fill=0)
    # wall: shade paper with tint ashlar gouges
    dt.rectangle([0, 64 * s, Wd, BUILDING_BASE * s], fill=255)
    for y in range(68, BUILDING_BASE, 9):
        for _ in range(10):
            spindle(dc, r.uniform(-50, W) * s, (y + r.uniform(-1, 1)) * s, r.uniform(40, 220) * s, r.uniform(1, 2.6) * s, r.uniform(-.004, .004))
    for _ in range(260):                          # dark-tint hatching gouges across the wall (second pass of the tint block)
        spindle(dd, r.uniform(-80, W) * s, r.uniform(66, BUILDING_BASE - 40) * s, r.uniform(40, 260) * s, r.uniform(1.2, 3.4) * s, r.uniform(-.003, .003))
    floors = [(74, 116, True), (132, 174, False), (190, 232, True), (248, 288, False)]
    for (y0, y1, balcony) in floors:
        for cx in cols:
            x0 = (cx + 16) * s; x1 = (cx + 42) * s
            jit = r.uniform(-.8, .8) * s
            di.rectangle([x0 + jit, y0 * s, x1, y1 * s], fill=255)
            di.rectangle([(cx + 28.4) * s, (y0 + 3) * s, (cx + 30) * s, (y1 - 2) * s], fill=0)
            di.rectangle([x0 + 3 * s, (y0 + 15) * s, x1 - 3 * s, (y0 + 16.4) * s], fill=0)
            di.rectangle([x0 - 3 * s, (y1 + 1) * s, x1 + 3 * s, (y1 + 4) * s], fill=255)  # sill
            # pediment over the window
            di.polygon([(x0 - 4 * s, (y0 - 2) * s), ((cx + 29) * s, (y0 - 8) * s), (x1 + 4 * s, (y0 - 2) * s)], fill=255)
        if balcony:
            yb = y1 + 6
            di.rectangle([0, yb * s, Wd, (yb + 9) * s], fill=255)
            for x in np.arange(off % 5, W, 5):
                di.rectangle([x * s, (yb + 2.5) * s, (x + 2) * s, (yb + 7.5) * s], fill=0)
    # ground floor: ink shopfront band with lit arched openings
    di.rectangle([0, 292 * s, Wd, BUILDING_BASE * s], fill=255)
    for cx in cols:
        x0 = (cx + 10) * s; x1 = (cx + 48) * s
        di.rectangle([x0, 306 * s, x1, (BUILDING_BASE - 2) * s], fill=0)
        di.pieslice([x0, 296 * s, x1, 318 * s], 180, 360, fill=0)
        di.rectangle([(cx + 28) * s, 300 * s, (cx + 30) * s, (BUILDING_BASE - 2) * s], fill=255)
    # street: paper + long horizontal ink gouges (dense near the kerb and under the bus)
    di.rectangle([0, BUILDING_BASE * s, Wd, (BUILDING_BASE + 3) * s], fill=255)
    for _ in range(300):
        y = r.uniform(BUILDING_BASE + 4, H)
        dens = 1.0 if y > KERB else 0.6
        if r.rand() > dens:
            continue
        spindle(di, r.uniform(-150, W) * s, y * s, r.uniform(30, 260) * s, r.uniform(1.0, 3.2) * s, r.uniform(-.006, .006))
    for _ in range(120):
        y = r.uniform(BUILDING_BASE + 4, H)
        spindle(dt, r.uniform(-150, W) * s, y * s, r.uniform(40, 300) * s, r.uniform(1.5, 5) * s, r.uniform(-.004, .004))
    dt.rectangle([0, (BUILDING_BASE + 3) * s, Wd, (GROUND_BUS - 6) * s], fill=255)   # far roadway: tint block
    for _ in range(90):
        spindle(dc, r.uniform(-150, W) * s, r.uniform(BUILDING_BASE + 5, GROUND_BUS - 8) * s, r.uniform(30, 200) * s, r.uniform(1.0, 2.6) * s, r.uniform(-.004, .004))
    di.rectangle([0, KERB * s, Wd, (KERB + 5) * s], fill=255)  # kerb edge
    for x in np.arange(r.uniform(0, 40), W, 46):
        di.rectangle([x * s, (KERB + 5) * s, (x + 1.5) * s, (KERB + 9) * s], fill=255)

    a = lambda im: np.asarray(im, np.float32) / 255.0
    ink_m = a(ink)
    hole = starve(ink_m, "stage")
    img = np.empty(ink_m.shape + (3,), np.float32); img[:] = PAPER
    for m, col in ((a(shade), SHADE), (a(tint), TINT), (a(cuts) * 0.9, SHADE), (a(dark), DTINT), (ink_m * (1 - hole * 0.85), INK)):
        img = img * (1 - m[..., None]) + col * m[..., None]
    return img


def compose(ink_m, tint_m, shade_m, hole=None, base=None):
    if base is None:
        img = np.empty(ink_m.shape + (3,), np.float32); img[:] = PAPER
    else:
        img = base
    img = img * (1 - shade_m[..., None]) + SHADE * shade_m[..., None]
    img = img * (1 - tint_m[..., None]) + TINT * tint_m[..., None]
    k = ink_m if hole is None else ink_m * (1 - hole * 0.85)
    img = img * (1 - k[..., None]) + INK * k[..., None]
    return img


# ---------------------------------------------------------------- bus print (foraged plate)
K_BUS = 0.74                 # plate film-px -> screen px
BUS_Y0 = 167
PLATE_CUT = 688              # plate x where the real body ends and the handmade platform begins
PLAT_END = 860


def print_levels(gray, key):
    """Two-tone + tint-block print of a photographic grey plate (uint8)."""
    cl = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    cl = cv2.medianBlur(cl, 3)
    g = cv2.GaussianBlur(cl.astype(np.float32), (0, 0), 1.1)
    ink = np.clip((96 - g) / 8, 0, 1)           # key block
    dtint = np.clip((118 - g) / 10, 0, 1) * (1 - ink) * 0.0
    tint = np.clip((165 - g) / 8, 0, 1) * (1 - ink)
    shade = np.clip((205 - g) / 10, 0, 1) * (1 - ink) * (1 - tint)
    return ink, tint, shade


def build_bus():
    meta = json.loads((PL / "plates.json").read_text())
    S = meta["scale"]
    rgba = np.asarray(Image.open(PL / "bus_rect_rgba.png"))
    gray, alpha = rgba[..., 0], rgba[..., 3].astype(np.float32) / 255
    # canvas for the bus layer in plate film-px, extended for the platform and the roof board
    PW, PH, PY = PLAT_END + 10, 330, 40      # PY: extra rows above the plate for the destination board
    sc = K_BUS * SS
    def T(x, y):   # plate film px -> bus-layer px (SS)
        return x * sc, (y + PY) * sc
    lw, lh = int(PW * sc), int(PH * sc + PY * sc)
    g = cv2.resize(gray, (int(gray.shape[1] / S * sc), int(gray.shape[0] / S * sc)), interpolation=cv2.INTER_AREA)
    a = cv2.resize(alpha, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_AREA)
    canvas_g = np.full((lh, lw), 230, np.uint8); canvas_a = np.zeros((lh, lw), np.float32)
    oy = int(PY * sc)
    hh, ww = min(g.shape[0], lh - oy), min(g.shape[1], lw)
    canvas_g[oy:oy + hh, :ww] = g[:hh, :ww]; canvas_a[oy:oy + hh, :ww] = a[:hh, :ww]
    cut = int(PLATE_CUT * sc)
    canvas_a[:, cut:] = 0
    ink, tint, shade = print_levels(canvas_g, "bus")
    ink *= canvas_a; tint *= canvas_a; shade *= canvas_a
    # open cab: what the photograph shows through the cab openings is background, so it is cut away
    # (light shows only as cream gaps); the driver and pillars keep their ink
    cy0, cy1, cx1 = int((25 + PY) * sc), int((125 + PY) * sc), int(268 * sc)
    tint[cy0:cy1, :cx1] = 0; shade[cy0:cy1, :cx1] = 0
    # rear bay pane (plate x 584..680, y 54..119): its dark interior re-cut as a plain tint block,
    # so the seat the man takes at A6 can be read (the real heads in that one bay are given up)
    by0, by1, bx0_, bx1_ = int((54 + PY) * sc), int((119 + PY) * sc), int(584 * sc), int(680 * sc)
    ink[by0:by1, bx0_:bx1_] = 0; tint[by0:by1, bx0_:bx1_] = canvas_a[by0:by1, bx0_:bx1_]; shade[by0:by1, bx0_:bx1_] = 0
    paper_a = canvas_a.copy()
    # handmade platform hardware, drawn into the same layer (slides with the bus)
    im_i = Image.fromarray((ink * 255).astype(np.uint8)); di = ImageDraw.Draw(im_i)
    im_t = Image.fromarray((tint * 255).astype(np.uint8)); dt = ImageDraw.Draw(im_t)
    im_s = Image.fromarray((shade * 255).astype(np.uint8)); dsd = ImageDraw.Draw(im_s)
    im_p = Image.fromarray((paper_a * 255).astype(np.uint8)); dp = ImageDraw.Draw(im_p)
    def R(x0, y0, x1, y1, d, fill=255):
        p0, p1 = T(x0, y0), T(x1, y1); d.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=fill)
    X0, X1 = PLATE_CUT - 2, PLAT_END
    # lit platform opening (cream) with an arched head, framed in ink
    R(X0, 18, X1, 226, dp)
    R(X0, 14, X1, 34, di)                                    # canopy (roof continued)
    R(X0, 14, X1 - 6, 22, dsd)                               # roof shade highlight strip
    p0, p1 = T(X0 + 8, 30), T(X1 - 4, 70)
    di.rectangle([p0[0], p0[1], p1[0], (p0[1] + p1[1]) / 2], fill=255)
    di.pieslice([p0[0], p0[1], p1[0], p1[1]], 180, 360, fill=0)   # arched lit head
    R(X0, 14, X0 + 6, 226, di)                               # rear bulkhead post
    R(X0, 222, X1, 234, di)                                  # platform floor
    R(X0 + 14, 248, X1 - 6, 254, di)                         # step
    for hx in (X0 + 20, X1 - 14):
        R(hx, 232, hx + 3, 250, di)
    # chain: sagging loop of rings between dash panel and stanchion
    for k in range(16):
        u = k / 15; x = X0 + 6 + u * (X1 - X0 - 20); y = 186 + 14 * math.sin(math.pi * u)
        c = T(x, y); rr = 2.2 * sc
        di.ellipse([c[0] - rr * 1.4, c[1] - rr, c[0] + rr * 1.4, c[1] + rr], outline=255, width=max(2, int(sc)))
    # the black stanchion (rear corner)
    R(X1 - 15, 30, X1 - 9, 226, di)
    # bell cord under the canopy (tassel drawn per frame)
    R(X0 + 9, 36, X1 - 9, 37.2, di)
    # carved destination board on the roof
    bx0, bx1, by0, by1 = 250, 560, -24, 6
    R(bx0, by0, bx1, by1, di)
    R(bx0 + 30, by1, bx0 + 34, 12, di); R(bx1 - 34, by1, bx1 - 30, 12, di)
    f = ImageFont.truetype(str(ROOT / "assets/fonts/instrument-serif.woff2"), int(23 * sc))
    txt = "MADELEINE – BASTILLE"
    tb = di.textbbox((0, 0), txt, font=f)
    cx, cy = T((bx0 + bx1) / 2, (by0 + by1) / 2)
    letters = Image.new("L", im_i.size, 0); dl = ImageDraw.Draw(letters)
    dl.text((cx - (tb[2] - tb[0]) / 2 - tb[0], cy - (tb[3] - tb[1]) / 2 - tb[1]), txt, font=f, fill=255)
    # carve: roughen the letter edges with seeded noise (gouge bite), then cut them out of the board
    lr = rng("board")
    nz = (lr.rand(*letters.size[::-1]) * 255).astype(np.uint8)
    la = np.asarray(letters.filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    la = ((la + (nz.astype(np.float32) - 128) * 0.9) > 120).astype(np.uint8) * 255
    ink = np.asarray(im_i, np.float32) / 255 * (1 - la / 255.0)
    tint = np.asarray(im_t, np.float32) / 255 * (1 - ink)
    shade = np.asarray(im_s, np.float32) / 255 * (1 - ink)
    pa = np.maximum(np.asarray(im_p, np.float32) / 255, np.maximum(ink, la / 255.0))
    # remove the photographic shade/tint from the board area, keep paper letters
    hole = starve(ink, "bus", amount=0.18)
    ink = ink * (1 - hole * 0.8)
    # board area also needs to be opaque: alpha = union
    alpha = np.clip(pa, 0, 1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    layer = dict(ink=ink, tint=tint, shade=shade, alpha=alpha, offx=0, offy=(BUS_Y0 - PY * K_BUS) * SS,
                 sc=sc, PY=PY, wheels=meta["wheels"], S=S)
    # wheels: grey tiles (printed after rotation each drawing)
    layer["wheel_tiles"] = {}
    for name in ("front", "rear"):
        t = np.asarray(Image.open(PL / f"wheel_{name}.png"))
        r = meta["wheels"][name]["r"] * sc
        g2 = cv2.resize(t[..., 0], (int(2 * r), int(2 * r)), interpolation=cv2.INTER_AREA)
        layer["wheel_tiles"][name] = g2
    return layer


def bus_x(t):
    """Layer slide: ease-out stop at A1 = 0.90 s; pull-away from 6.20 s. Returns bus-layer x (film px)."""
    rest = 720 - PLAT_END * K_BUS        # rear of platform at x = 720
    d_in = 80.0
    if t < 0.90:
        u = 1 - t / 0.90
        return rest + d_in * u * u       # enters from the right, moving left (forwards: cab is on the left)
    if t < 6.20:
        return rest
    return rest - 0.5 * 160 * (t - 6.20) ** 2


def wheel_angle(t):
    """Wheels are drawings (on twos) and stop one drawing before the layer does."""
    td = math.floor(t * 12 + 1e-9) / 12
    r = 41 * K_BUS
    t_lock = 0.90 - 1 / 12                       # last turning drawing (one drawing before A1)
    a_lock = (bus_x(t_lock) - bus_x(0)) / r
    if td <= t_lock:
        a = (bus_x(td) - bus_x(0)) / r
    elif td < 6.20:
        a = a_lock
    else:
        a = a_lock + (bus_x(td) - bus_x(6.20)) / r
    return math.degrees(a)


def paint_bus(img, ink_k, layer, t, tassel_pull=0.0):
    x = bus_x(t) * SS
    ix = int(round(x)); oy = int(round(layer["offy"]))
    Hd, Wd = img.shape[:2]
    lh, lw = layer["alpha"].shape
    x0, x1 = max(0, ix), min(Wd, ix + lw); y0, y1 = max(0, oy), min(Hd, oy + lh)
    sl = (slice(y0, y1), slice(x0, x1)); ls = (slice(y0 - oy, y1 - oy), slice(x0 - ix, x1 - ix))
    a = layer["alpha"][ls][..., None]
    sub = img[sl]
    sub[:] = sub * (1 - a) + PAPER * a
    for m, col in ((layer["shade"], SHADE), (layer["tint"], TINT), (layer["ink"], INK)):
        mm = m[ls][..., None]
        sub[:] = sub * (1 - mm) + col * mm
    # wheels (rotating cut pieces, printed after rotation)
    ang = wheel_angle(t)
    sc = layer["sc"]
    for name, wd in layer["wheels"].items():
        tile = layer["wheel_tiles"][name]
        n = tile.shape[0]
        Mr = cv2.getRotationMatrix2D((n / 2, n / 2), ang, 1.0)
        rt = cv2.warpAffine(tile, Mr, (n, n), flags=cv2.INTER_LINEAR, borderValue=40)
        wi, wt, ws = print_levels(rt, "wheel")
        yy, xx = np.mgrid[0:n, 0:n]
        circ = np.clip((n / 2 - 1 - np.hypot(xx - n / 2, yy - n / 2)) / 1.2, 0, 1).astype(np.float32)
        cx = ix + wd["center"][0] * sc; cy = oy + (wd["center"][1] + layer["PY"]) * sc
        px, py = int(round(cx - n / 2)), int(round(cy - n / 2))
        if px < 0 or px + n > Wd:
            continue
        s2 = img[py:py + n, px:px + n]
        for m, col in ((np.ones_like(circ), PAPER), (ws, SHADE), (wt, TINT), (wi, INK)):
            mm = (m * circ)[..., None]
            s2[:] = s2 * (1 - mm) + col * mm
        # rim: the tyre is a solid black ring
        ring = np.clip((n / 2 - 1 - np.hypot(xx - n / 2, yy - n / 2)) / 1.2, 0, 1) * np.clip((np.hypot(xx - n / 2, yy - n / 2) - (n / 2 - 7 * sc / SS * SS / 2 - 4)) / 1.2, 0, 1)
        s2[:] = s2 * (1 - ring[..., None]) + INK * ring[..., None]
    return ix / SS


# ---------------------------------------------------------------- puppets (Reiniger rig)
def smooth_closed(pts, n=6):
    """Catmull-Rom through hand-placed points: fluid closed part outlines (never capsules)."""
    P = np.array(pts, np.float64); out = []
    m = len(P)
    for i in range(m):
        p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            u = k / n; u2, u3 = u * u, u * u * u
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    return np.array(out)


SHAPES = {
    # long-necked man
    "m_torso": [(-9, -46), (-4, -49), (5, -48), (10, -44), (11, -30), (9, -12), (10, 4), (12, 24), (4, 26), (-8, 26), (-11, 22), (-10, 4), (-11, -20), (-11, -38)],
    "m_tail": [(0, -2), (-3, 10), (-6, 24), (-1, 25.5), (3, 12), (4, -1)],
    "m_neck": [(-3.2, 2), (-2.8, -12), (-2.4, -28), (2.6, -28), (3.2, -12), (4.4, 2)],
    "m_head": [(-6, 0), (-8, -6), (-7.5, -13), (-3, -17), (3, -17), (6, -14), (7, -10), (10.5, -7), (7.4, -5.6), (7.2, -3.4), (8.4, -2.2), (6, 0.4), (3.5, 2.2), (-0.5, 2)],
    "m_hat": [(-12.5, 1.2), (-7.4, 0.2), (-7.2, -7), (-4, -10.5), (0, -8.4), (4, -10.5), (7.2, -7), (7.4, 0.2), (13.5, 1.0), (12.5, 3), (-11.5, 3)],
    "uarm": [(-4, -1), (-3.6, 12), (-3, 24), (3, 24), (3.8, 12), (4, -1.5)],
    "farm_fist": [(-3, 0), (-2.6, 17), (-3.2, 22), (-2.4, 28), (0, 30), (2.6, 28), (3, 24), (5.6, 22.5), (6.2, 20.5), (3.2, 19.5), (2.8, 17), (3, 0)],
    "farm_open": [(-3, 0), (-2.6, 17), (-4, 19), (-5.2, 27), (-3.6, 27.6), (-2.8, 21.5), (-2.2, 30.4), (-0.8, 30.6), (-0.4, 22), (0.8, 31), (2.2, 30.8), (1.4, 22), (3, 29.2), (4.2, 28.4), (3, 20), (6.6, 22.2), (7, 20.8), (3.2, 16.8), (3, 0)],
    "farm_flat": [(-3, 0), (-2.6, 17), (-3.0, 20), (-2.4, 31), (-0.6, 32.5), (1.4, 31.5), (2.2, 22), (5.4, 20.6), (5.6, 19.0), (3.0, 17.2), (3, 0)],
    "thigh": [(-5.5, -1), (-5.2, 16), (-3.8, 32), (3.8, 32), (5.2, 16), (5.6, -1.5)],
    "shin": [(-3.6, -1), (-3, 26), (-3.8, 31), (-2.2, 33.4), (12, 33.4), (13.2, 31.4), (9, 29), (3.2, 27), (3.6, -1)],
    # jostler: broad back, bowler
    "j_torso": [(-15, -40), (-9, -47), (4, -47), (11, -41), (12.5, -26), (10.5, -8), (11, 4), (13, 22), (-14, 22), (-14, 4), (-16.5, -14), (-17.5, -30)],
    "j_neck": [(-4.5, 2), (-4, -6), (4, -6), (5, 2)],
    "j_head": [(-7, 0), (-8.6, -7), (-7, -14), (-2, -17), (4, -16), (7, -12), (8, -8), (10.4, -6), (8, -4.2), (8.2, -1.6), (5, 1.6), (0, 2.4)],
    "bowler": [(-10.5, 1.5), (-7.5, 0.5), (-7.8, -6), (-5, -10.6), (0, -11.6), (5, -10.6), (7.8, -6), (7.5, 0.5), (10.5, 1.5), (9.5, 3), (-9.5, 3)],
    # runner A: coat flaring, cap
    "a_torso": [(-10, -45), (-4, -48), (6, -47), (11, -42), (12, -28), (10, -10), (11, 4), (-11, 4), (-12, -22)],
    "a_tail": [(-1, -2), (-6, 12), (-10, 26), (-2, 27), (6, 14), (9, -2)],
    "a_head": [(-6.5, 0), (-8, -6), (-7, -13), (-2.5, -16.5), (3.5, -16), (6.5, -12), (7.5, -8.5), (10, -6), (7.4, -4.6), (7.6, -2), (5, 1.4), (0, 2.2)],
    "cap": [(-8, 1), (-8, -6), (-3, -10), (4, -9.5), (8, -5), (8.5, -0.5), (15, 0.6), (14, 2.4), (-7.5, 2.8)],
    "neck_s": [(-3.5, 2), (-3, -7), (3, -7), (4, 2)],
    # runner B: woman, long skirt, cloche
    "b_torso": [(-8, -44), (-3, -47), (5, -46), (9, -41), (9.5, -28), (7, -12), (8, 0), (-8, 0), (-9.5, -20), (-9.5, -36)],
    "b_skirt": [(-8, -2), (8, -2), (13, 18), (16, 36), (-14, 36), (-11, 18)],
    "cloche": [(-9.5, 2), (-8.6, -6), (-5, -10.5), (2, -11), (7, -8), (9, -2), (10.5, 3), (-9, 4)],
}
SCALE = {"m_head": (1.25, 1.25), "m_hat": (1.3, 1.3), "m_torso": (1.25, 1.0), "m_tail": (1.2, 1.0), "j_head": (1.15, 1.15), "bowler": (1.15, 1.15),
         "a_head": (1.15, 1.15), "cap": (1.15, 1.15), "cloche": (1.15, 1.15)}
SM = {k: smooth_closed(v) * np.array(SCALE.get(k, (1, 1))) for k, v in SHAPES.items()}
HATS = 1.3

# part table: name -> (parent, pivot in parent, shape key, draw order)
RIGS = {
    "man": dict(parts=[
        ("leg_f", "root", (0, 2), "thigh", 0), ("shin_f", "leg_f", (0, 31), "shin", 0),
        ("arm_f", "torso", (0, -43), "uarm", 1), ("fore_f", "arm_f", (0, 23), "farm_fist", 1),
        ("tail", "torso", (-11, 6), "m_tail", 2), ("torso", "root", (0, 0), "m_torso", 3),
        ("neck", "torso", (3, -45), "m_neck", 3), ("head", "neck", (0, -26), "m_head", 4),
        ("hat", "head", (0, -17), "m_hat", 5),
        ("leg_n", "root", (0, 2), "thigh", 6), ("shin_n", "leg_n", (0, 31), "shin", 6),
        ("arm_n", "torso", (0, -43), "uarm", 7), ("fore_n", "arm_n", (0, 23), "farm_fist", 7)],
        limits=dict(neck=(-25, 30), head=(-30, 30), fore_n=(0, 150), fore_f=(0, 150), shin_n=(-130, 0), shin_f=(-130, 0))),
    "jostler": dict(parts=[
        ("leg_f", "root", (0, 2), "thigh", 0), ("shin_f", "leg_f", (0, 31), "shin", 0),
        ("arm_f", "torso", (-2, -41), "uarm", 1), ("fore_f", "arm_f", (0, 23), "farm_fist", 1),
        ("torso", "root", (0, 0), "j_torso", 3),
        ("neck", "torso", (0, -45), "j_neck", 3), ("head", "neck", (0, -5), "j_head", 4),
        ("hat", "head", (0, -14), "bowler", 5),
        ("leg_n", "root", (0, 2), "thigh", 6), ("shin_n", "leg_n", (0, 31), "shin", 6),
        ("arm_n", "torso", (-2, -41), "uarm", 7), ("fore_n", "arm_n", (0, 23), "farm_fist", 7)],
        limits=dict(fore_n=(0, 150), fore_f=(0, 150), shin_n=(-130, 0), shin_f=(-130, 0))),
    "runA": dict(parts=[
        ("leg_f", "root", (0, 2), "thigh", 0), ("shin_f", "leg_f", (0, 31), "shin", 0),
        ("arm_f", "torso", (0, -43), "uarm", 1), ("fore_f", "arm_f", (0, 23), "farm_fist", 1),
        ("tail", "torso", (0, 2), "a_tail", 2), ("torso", "root", (0, 0), "a_torso", 3),
        ("neck", "torso", (1, -46), "neck_s", 3), ("head", "neck", (0, -6), "a_head", 4),
        ("hat", "head", (0, -14.4), "cap", 5),
        ("leg_n", "root", (0, 2), "thigh", 6), ("shin_n", "leg_n", (0, 31), "shin", 6),
        ("arm_n", "torso", (0, -43), "uarm", 7), ("fore_n", "arm_n", (0, 23), "farm_fist", 7)],
        limits=dict(fore_n=(0, 150), fore_f=(0, 150), shin_n=(-130, 0), shin_f=(-130, 0))),
    "runB": dict(parts=[
        ("leg_f", "root", (0, 2), "thigh", 0), ("shin_f", "leg_f", (0, 31), "shin", 0),
        ("arm_f", "torso", (0, -42), "uarm", 1), ("fore_f", "arm_f", (0, 23), "farm_fist", 1),
        ("leg_n", "root", (0, 2), "thigh", 2), ("shin_n", "leg_n", (0, 31), "shin", 2),
        ("skirt", "torso", (0, 0), "b_skirt", 3), ("torso", "root", (0, 0), "b_torso", 3),
        ("neck", "torso", (1, -45), "neck_s", 3), ("head", "neck", (0, -6), "a_head", 4),
        ("hat", "head", (0, -13.8), "cloche", 5),
        ("arm_n", "torso", (0, -42), "uarm", 7), ("fore_n", "arm_n", (0, 23), "farm_fist", 7)],
        limits=dict(fore_n=(0, 150), fore_f=(0, 150), shin_n=(-130, 0), shin_f=(-130, 0))),
}


def rot(th):
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    return np.array([[c, s_], [-s_, c]])   # (x,y) -> (x c + y s, -x s + y c); +θ swings a hanging limb forward


def fk(rig, pose):
    """Forward kinematics in puppet space (+x = facing). Returns {part: (origin, angle)} and pins."""
    R = RIGS[rig]; out = {"root": (np.zeros(2), pose.get("root", 0.0))}
    names = {"root"}; ordered = []
    pending = list(R["parts"])
    while pending:
        for p in list(pending):
            if p[1] in names:
                ordered.append(p); names.add(p[0]); pending.remove(p)
    for name, parent, pivot, shape, z in ordered:
        po, pa = out[parent]
        a = pose.get(name, 0.0)
        lo, hi = R["limits"].get(name, (-180, 180))
        a = max(lo, min(hi, a))                      # joint-angle limits held
        o = po + rot(pa) @ np.array(pivot, float)
        out[name] = (o, pa + a)
    return out


def puppet_polys(rig, pose, x, y, s, facing, hands=None, pivot_rot=None):
    """World-space polygons (film px) for every part, in draw order. y is the pelvis height."""
    T = fk(rig, pose); polys = []; anchors = {}
    hands = hands or {}
    for name, parent, pivot, shape, z in sorted(RIGS[rig]["parts"], key=lambda p: p[4]):
        o, a = T[name]
        key = hands.get(name, shape)
        pts = (rot(a) @ SM[key].T).T + o
        polys.append((z, name, pts))
    def world(pts):
        p = pts * s
        if pivot_rot is not None:
            (px, py), th = pivot_rot
            p = (rot(th) @ (p - np.array([px, py])).T).T + np.array([px, py])
        p[:, 0] *= facing
        return p + np.array([x, y])
    wpolys = [(z, n, world(p)) for z, n, p in polys]
    for k, (o, a) in T.items():
        anchors[k] = (world(o[None])[0], a)
    # extra anchors in part space
    def pt(part, local):
        o, a = T[part]; return world((rot(a) @ np.array(local, float) + o)[None])[0]
    anchors["_pt"] = pt
    return wpolys, anchors


def foot_low(wpolys):
    return max(p[:, 1].max() for z, n, p in wpolys if n.startswith("shin") or n == "skirt")


# 6-drawing run cycle (thigh, shin) for one leg; far leg = +3 drawings
RUN = [(42, -8), (22, -24), (-6, -14), (-30, -48), (-16, -106), (22, -86)]
LIFT = [0, 2, 0, 5, 8, 4]


def run_pose(k, lean=-10):
    a = RUN[k % 6]; b = RUN[(k + 3) % 6]
    return {"torso": lean, "leg_n": a[0] - lean * 0.3, "shin_n": a[1], "leg_f": b[0] - lean * 0.3, "shin_f": b[1],
            "arm_n": -a[0] * 0.95, "fore_n": 85, "arm_f": -b[0] * 0.95, "fore_f": 85, "neck": -lean * 0.4,
            "head": 4, "tail": -10 - (8 if k % 3 == 1 else 0), "skirt": 6 + 6 * math.sin(k * math.pi / 3)}


def stand_pose(lean=0):
    return {"torso": lean, "leg_n": 4, "shin_n": -4, "leg_f": -5, "shin_f": -2, "arm_n": -4, "fore_n": 12,
            "arm_f": 6, "fore_f": 14, "neck": 0, "head": 0}


# ---------------------------------------------------------------- exposure sheet (on twos)
def drawing(t):
    return int(math.floor(t * 12 + 1e-9))


SEED_R = rng("runners")
N_RUN = 2 + int(SEED_R.rand() < 0.5)          # 2 or 3 foreground runners (unprotected, seeded)
RUNNERS = []
for i in range(N_RUN):
    rr = rng("runner", i)
    RUNNERS.append(dict(kind="runA" if i % 2 == 0 else "runB", x0=rr.uniform(40, 110) - 165 * i,
                        phase=int(rr.randint(0, 6)), speed=rr.uniform(300, 340), stop=rr.uniform(500, 540) - 150 * i,
                        s=rr.uniform(1.12, 1.24), gy=GROUND_FG + rr.uniform(-4, 12)))


def man_state(t):
    """Long-necked man on the platform. Returns pose, platform-local x, tip angle, hands, visible."""
    d = drawing(t); td = d / 12
    pose = stand_pose(); hands = {}
    tip = 0.0; lx = 795.0; vis = True; seated = 0.0
    pose.update(arm_n=8, fore_n=40, arm_f=10, fore_f=30, neck=-4, head=-2)
    if d == 14:                                  # A3 contact drawing (t 1.167-1.25 s, covers 1.20)
        pose.update(torso=3, neck=-2, head=0, arm_n=16, fore_n=40)
        tip = 3
    elif d == 15:                                # pushed back: head lags forward, arms fly forward
        pose.update(torso=5, neck=-12, head=-6, arm_n=38, fore_n=30, arm_f=26, fore_f=26, leg_n=12, shin_n=-18)
        tip = 9
    elif 16 <= d < 24:                           # A4 1.33: shoulder meets the stanchion (snap), head whips back, held
        whip = {16: 12, 17: 16, 18: 11}.get(d, 8)
        pose.update(torso=6, neck=whip, head=whip * 0.6, arm_n=30 - min(d - 16, 4) * 5, fore_n=34, arm_f=18, fore_f=30, leg_n=14, shin_n=-20)
        tip = 14 if d < 19 else 13
    elif 24 <= d < 39:                           # A5 protest 2.0-3.2: rights himself, head to the jostler, open hand
        u = min(1, (d - 24) / 4)
        tip = 13 - 7 * u
        pose.update(torso=4 - 6 * u, neck=8 - 22 * u, head=6 - 16 * u, arm_n=-40 + 100 * u, fore_n=40 + 70 * u,
                    arm_f=-20 + 10 * u, fore_f=30, leg_n=10, shin_n=-14)
        hands["fore_n"] = "farm_open" if d >= 26 else "farm_fist"
        if d in (30, 31, 34, 35):                # emphatic beats of the open hand
            pose["fore_n"] += 14; pose["neck"] -= 4
    elif 39 <= d < 55:                           # composes himself, then turns into the saloon (4.6..)
        tip = 4 if d < 43 else 0
        pose.update(neck=-6, head=-4)
        if d >= 55 - 0:
            pass
    if 52 <= d < 60:                             # 4.33-5.0: steps left through the bulkhead door
        k = d - 52
        pose.update(run_pose(k, lean=-6)); pose.update(neck=0, head=0, fore_n=40, fore_f=40)
        lx = 795 - k * 14
        tip = 0
        vis = lx > PLATE_CUT - 4
    elif d >= 60:
        vis = False
        seated = (d - 60)                         # drawings since entering the saloon; A6 seated at drawing 66 (5.50)
    return pose, lx, tip, hands, vis, seated


def jostler_state(t):
    d = drawing(t)
    hands = {}
    plat_x = None
    if d < 12:                                   # runs along the bus side toward the platform
        pose = run_pose(d + 2, lean=-14)
        x = 450 + d * 12.5
        y = GROUND_BUS - 0
        mode = "ground"
    elif d == 12:                                # 1.00: foot on the step
        pose = run_pose(0, lean=-16); pose.update(leg_n=58, shin_n=-58, leg_f=-24, shin_f=-30)
        x, y, mode = 600, None, "step"
    elif d == 13:                                # 1.083: lunge up, arm cocked
        pose = dict(torso=-20, leg_n=40, shin_n=-40, leg_f=-28, shin_f=-24, arm_n=60, fore_n=60, arm_f=-30, fore_f=50, neck=6, head=6)
        x, y, mode = 606, None, "platform"
    elif d in (14, 15, 16):                      # 1.167..: the arm drives into the man (contact constraint)
        ext = {14: 0, 15: 6, 16: 8}[d]
        pose = dict(torso=-24 - ext * 0.5, leg_n=34, shin_n=-30, leg_f=-30, shin_f=-14, arm_n=92, fore_n=4, arm_f=-36, fore_f=60, neck=8, head=8)
        hands["fore_n"] = "farm_flat"
        x, y, mode = None, None, "contact"
    elif d < 29:                                 # 1.42-2.4 recovers balance, arm withdrawn
        u = min(1, (d - 17) / 3)
        pose = dict(torso=-16 + 10 * u, leg_n=24 - 12 * u, shin_n=-20 + 10 * u, leg_f=-24 + 14 * u, shin_f=-10, arm_n=70 - 66 * u, fore_n=20 + 10 * u, arm_f=-20 + 20 * u, fore_f=30, neck=4, head=0)
        x, y, mode = 602 + 2 * u, None, "platform"
    elif d < 39:                                 # 2.4-3.2 shrug
        k = d - 29
        up = 1 if 2 <= k < 8 else 0.4
        pose = dict(torso=-4, leg_n=10, shin_n=-8, leg_f=-8, shin_f=-6, arm_n=-14 * up + 6, fore_n=110 * up + 10, arm_f=10, fore_f=100 * up, neck=-10 * up, head=14 * up)
        hands["fore_n"] = "farm_open" if up == 1 else "farm_fist"
        x, y, mode = 606, None, "platform"
    else:                                        # rides the step, holding the stanchion
        pose = dict(torso=-2, leg_n=8, shin_n=-6, leg_f=-6, shin_f=-4, arm_n=-20, fore_n=70, arm_f=12, fore_f=20, neck=0, head=-4)
        if d >= 74:                              # 6.2: the bus pulls away; he braces
            pose.update(torso=4, neck=6, head=2)
        x, y, mode = 608, None, "platform"
    return pose, x, y, mode, hands


# ---------------------------------------------------------------- secondary dynamics (#41)
class Chain:
    """3-link damped pendulum (cord end). Semi-implicit Euler + distance projection, 4 substeps / frame."""
    def __init__(self, anchor, n=3, seg=8.0):
        self.seg = seg; self.p = np.array([anchor + np.array([0.0, seg * (i + 1)]) for i in range(n)])
        self.v = np.zeros_like(self.p); self.prev_anchor = anchor.copy()
    def step(self, anchor, dt, g=900.0, c=5.5, sub=4):
        h = dt / sub
        for k in range(sub):
            a_k = self.prev_anchor + (anchor - self.prev_anchor) * (k + 1) / sub
            self.v += (np.array([0, g]) - c * self.v) * h
            old = self.p.copy(); self.p += self.v * h
            for _ in range(4):
                prev = a_k
                for i in range(len(self.p)):
                    dvec = self.p[i] - prev; L_ = np.linalg.norm(dvec) + 1e-9
                    self.p[i] = prev + dvec / L_ * self.seg
                    prev = self.p[i]
            # collision boundary: the cord is tied under the brim, so no link may rise above
            # 70 deg from hanging (it cannot whip over the hat)
            prev = a_k
            for i in range(len(self.p)):
                dvec = self.p[i] - prev
                ang = math.atan2(dvec[0], dvec[1]); lim = math.radians(70)
                if abs(ang) > lim:
                    ang = math.copysign(lim, ang)
                    self.p[i] = prev + self.seg * np.array([math.sin(ang), math.cos(ang)])
                prev = self.p[i]
            self.v = (self.p - old) / h
        self.prev_anchor = anchor.copy()
    def energy(self, anchor):
        # kinetic + potential above rest (rest = hanging straight under the anchor)
        ke = 0.5 * (self.v ** 2).sum()
        rest_y = anchor[1] + self.seg * np.arange(1, len(self.p) + 1)
        pe = 900.0 * (rest_y - self.p[:, 1]).clip(0).sum()
        return ke + pe


class Spring1:
    """1-link angular spring (coat tail) driven by pelvis acceleration."""
    def __init__(self):
        self.a = 0.0; self.w = 0.0; self.px = None; self.vx = 0.0
    def step(self, x, dt, k=260.0, c=9.0, gain=0.10):
        vx = 0.0 if self.px is None else (x - self.px) / dt
        acc = (vx - self.vx) / dt; self.px = x; self.vx = vx
        self.w += (-k * self.a - c * self.w + gain * acc) * dt
        self.a += self.w * dt
        return math.degrees(self.a)


# ---------------------------------------------------------------- frame assembly
def draw_polys(d, polys, fill=255):
    for z, n, p in polys:
        d.polygon([tuple(q * SS) for q in p], fill=fill)


def cut_braid(d, anchors, s, facing):
    """Plaited-cord band: a row of tiny diamonds cut through the hat crown."""
    pt = anchors["_pt"]
    for k in range(5):
        cx = (-5.4 + k * 2.7) * HATS; yb = -2.8 * HATS; e = 1.25 * HATS
        c2 = pt("hat", (cx + e, yb)); c3 = pt("hat", (cx, yb + e)); c4 = pt("hat", (cx - e, yb)); c5 = pt("hat", (cx, yb - e))
        d.polygon([tuple(q * SS) for q in (c5, c2, c3, c4)], fill=0)


def cast_shadow(d, x, y, w, length, facing=1):
    xs = x - length * 0.85; spindle(d, xs * SS, (y + 1.5) * SS, length * SS, 4.2 * SS)
    spindle(d, (xs + length * 0.3) * SS, (y + 6) * SS, length * 0.6 * SS, 2.2 * SS)


STAGE = None
BUS = None


def setup():
    global STAGE, BUS
    STAGE = build_stage()
    BUS = build_bus()


def simulate():
    """Run dynamics through the clip once (24 fps frames, 4 substeps); sample on twos."""
    chain = None; tail = Spring1(); out = []
    filt = None; fv = np.zeros(2)       # felt-hat compliance: the band follows the head through a critically damped spring
    for f in range(NF):
        t = f / FPS
        pose, lx, tip, hands, vis, seated = man_state(t)
        mx = bus_x(t) + lx * K_BUS
        head_pt, tail_x = man_anchor(t)
        if filt is None:
            filt = head_pt.copy()
        w0 = 30.0; dt = 1 / FPS
        for _ in range(4):
            acc = w0 * w0 * (head_pt - filt) - 2 * w0 * fv
            fv = fv + acc * dt / 4; filt = filt + fv * dt / 4
        anchor = filt.copy()
        if chain is None:
            chain = Chain(anchor)
            for _ in range(40):
                chain.step(anchor, 1 / FPS)
        chain.step(anchor, 1 / FPS)
        ta = tail.step(tail_x, 1 / FPS)
        out.append(dict(cord=chain.p.copy() + (head_pt - anchor), anchor=head_pt.copy(), energy=chain.energy(anchor), tail=ta))
    return out


MAN_S = 0.78
JS = 0.84
FLOOR_Y = BUS_Y0 + 222 * K_BUS          # platform floor (screen y)


def man_place(t):
    pose, lx, tip, hands, vis, seated = man_state(t)
    x = bus_x(t) + lx * K_BUS
    polys, an = puppet_polys("man", pose, 0, 0, MAN_S, -1)
    low = foot_low(polys)
    y = FLOOR_Y - low
    heel = (0.0, low / MAN_S)                   # pivot for the tip-back (puppet space, at the feet)
    polys, an = puppet_polys("man", pose, x, y, MAN_S, -1, hands=hands, pivot_rot=(heel, tip))
    return polys, an, vis, seated, x


def man_anchor(t):
    polys, an, vis, seated, x = man_place(t)
    return an["_pt"]("hat", (-11.8 * HATS, 1.6 * HATS)), an["torso"][0][0]


def render_frame(f, sim):
    t = f / FPS
    td = drawing(t) / 12                         # puppets are drawings: on twos
    fd = 2 * drawing(t)                          # frame index of this drawing (for dynamics sampling)
    img = STAGE.copy()
    Wd, Hd = W * SS, H * SS
    # shadows of bus (long horizontal strokes)
    sh, dsh = L()
    bx = bus_x(t)
    spindle(dsh, (bx + 10) * SS, (GROUND_BUS + 3) * SS, 640 * SS, 9 * SS)
    spindle(dsh, (bx - 40) * SS, (GROUND_BUS + 11) * SS, 560 * SS, 3 * SS)
    # man behind the bus layer? No: he stands on the platform (inside the lit opening), in front of it.
    m = np.asarray(sh, np.float32) / 255
    img = img * (1 - m[..., None]) + INK * m[..., None]
    # bus layer
    paint_bus(img, None, BUS, t)
    # puppets key block
    key, dk = L(); cut = []
    polys, an, vis, seated, mx = man_place(td)
    s = sim[min(fd, NF - 1)]
    if vis:
        # coat tail driven by the spring (rebuild with tail angle)
        pose, lx, tip, hands, _, _ = man_state(td)
        pose = dict(pose); pose["tail"] = pose.get("tail", 0) + s["tail"]
        heel_polys, _ = puppet_polys("man", pose, 0, 0, MAN_S, -1)
        low = foot_low(heel_polys)
        polys, an = puppet_polys("man", pose, mx, FLOOR_Y - low, MAN_S, -1, hands=hands, pivot_rot=((0.0, low / MAN_S), tip))
        # occlusion: the bulkhead post/dash hide him as he passes into the saloon
        clipx = (bus_x(t) + (PLATE_CUT + 6) * K_BUS)
        draw_polys(dk, polys)
        cut_braid(dk, an, MAN_S, -1)
        cord = [s["anchor"]] + list(s["cord"])
        cw = [2.8, 2.4, 2.0, 1.6]
        for i in range(len(cord) - 1):
            dk.line([tuple(cord[i] * SS), tuple(cord[i + 1] * SS)], fill=255, width=int(cw[i] * SS))
        e = cord[-1]; dk.ellipse([(e[0] - 1.6) * SS, (e[1] - 1.6) * SS, (e[0] + 1.6) * SS, (e[1] + 1.6) * SS], fill=255)
        km = np.asarray(key, np.float32) / 255
        km[:, :int(clipx * SS)] = 0
        key = Image.fromarray((km * 255).astype(np.uint8)); dk = ImageDraw.Draw(key)
    if not vis and drawing(td) >= 60:
        # A6: seen in the rear window, sinking into the seat (head, long neck, cord hat)
        bxx = bus_x(t)
        k = drawing(td) - 60
        px_ = 690 - min(k, 3) * 16                # walks along the gangway to the vacant rear seat
        py_ = 150 + max(0, min(k - 3, 3)) * 7    # then sinks into it: seated at drawing 66 (A6, 5.50 s)
        wx = bxx + px_ * K_BUS; wy = BUS_Y0 + py_ * K_BUS
        sp, san = puppet_polys("man", dict(torso=0 if k >= 6 else -6, neck=-4, head=0, arm_n=0, arm_f=0, leg_n=80, leg_f=80, shin_n=-80, shin_f=-80), wx, wy, MAN_S, -1)
        win = Image.new("L", key.size, 0); dw = ImageDraw.Draw(win)
        draw_polys(dw, [p for p in sp if p[1] in ("torso", "neck", "head", "hat")])
        cut_braid(dw, san, MAN_S, -1)
        wm = np.asarray(win, np.float32) / 255
        # window aperture of the rear-most bay of the real bus (plate x 622..684, y 52..120)
        ax0 = int((bxx + 584 * K_BUS) * SS); ax1 = int((bxx + 680 * K_BUS) * SS)
        ay0 = int((BUS_Y0 + 54 * K_BUS) * SS); ay1 = int((BUS_Y0 + 119 * K_BUS) * SS)
        clipm = np.zeros_like(wm); clipm[ay0:ay1, ax0:ax1] = 1
        km = np.maximum(np.asarray(key, np.float32) / 255, wm * clipm)
        key = Image.fromarray((km * 255).astype(np.uint8)); dk = ImageDraw.Draw(key)
    # jostler
    jpose, jx, jy, mode, jh = jostler_state(td)
    if mode == "ground":
        p0, a0 = puppet_polys("jostler", jpose, 0, 0, JS, 1)
        low = foot_low(p0); jx_ = jx; jy_ = GROUND_BUS + 4 - low - LIFT[(drawing(td) + 2) % 6]
    else:
        p0, a0 = puppet_polys("jostler", jpose, 0, 0, JS, 1, hands=jh)
        low = foot_low(p0)
        step_y = BUS_Y0 + 248 * K_BUS
        jy_ = (step_y if mode == "step" else FLOOR_Y + 4) - low
        if mode == "contact":
            # contact constraint: the flat hand's palm touches the man's chest (A3)
            hand = a0["_pt"]("fore_n", (5.0, 26))
            chest = an["_pt"]("torso", (10.5, -30)) if vis else np.array([mx, 0])
            jx_ = chest[0] - hand[0] - 0.5
        else:
            jx_ = bus_x(t) + (jx - bus_x(6.0) / K_BUS * 0) * 1.0 if False else bus_x(t) - bus_x(1.0) + jx
    jp, ja = puppet_polys("jostler", jpose, jx_, jy_, JS, 1, hands=jh)
    draw_polys(dk, jp)
    # bell cord tassel (A7 at 6.00): a conductor's hand from the bulkhead door pulls it
    pull = 1.0 if 5.92 <= td < 6.1 else 0.0
    tx = bus_x(t) + (PLAT_END - 30) * K_BUS; ty0 = BUS_Y0 + 37 * K_BUS
    dk.line([(tx * SS, ty0 * SS), (tx * SS, (ty0 + 18 + 6 * pull) * SS)], fill=255, width=int(1.4 * SS))
    dk.ellipse([(tx - 2) * SS, (ty0 + 17 + 6 * pull) * SS, (tx + 2) * SS, (ty0 + 23 + 6 * pull) * SS], fill=255)
    # foreground runners
    shadows, dsh2 = L()
    for i, R_ in enumerate(RUNNERS):
        dd = drawing(td)
        x = R_["x0"] + R_["speed"] * td
        running = x < R_["stop"]
        if running:
            pose = run_pose(dd + R_["phase"], lean=-12)
        else:
            x = R_["stop"]; pose = stand_pose(-2)
            pose.update(arm_n=-10, fore_n=30, arm_f=8, fore_f=20, neck=-6, head=-8)  # look up at the platform
        pp, pa = puppet_polys(R_["kind"], pose, 0, 0, R_["s"], 1)
        low = foot_low(pp)
        lift = LIFT[(dd + R_["phase"]) % 6] if running else 0
        pp, pa = puppet_polys(R_["kind"], pose, x, R_["gy"] - low - lift, R_["s"], 1)
        draw_polys(dk, pp)
        cast_shadow(dsh2, x, R_["gy"], 30, 150 * R_["s"])
    if mode == "ground":
        cast_shadow(dsh2, jx_, GROUND_BUS + 4, 28, 120)
    # composite key block with a 0.8 px feather (charcoal-soft edge on the print only)
    km = np.asarray(key.filter(ImageFilter.GaussianBlur(0.5 * SS)), np.float32) / 255
    sm = np.asarray(shadows.filter(ImageFilter.GaussianBlur(0.6 * SS)), np.float32) / 255
    img = img * (1 - sm[..., None]) + INK2 * sm[..., None]
    img = img * (1 - km[..., None]) + INK * km[..., None]
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    # tag: small monospace, cream on an ink tab, bottom-left
    dtag = ImageDraw.Draw(out)
    f = kit.font("mono", 13)
    tag = f"baseline · street-side · cut-paper · seed 0417 · t {t:4.2f}"
    tb = dtag.textbbox((0, 0), tag, font=f)
    dtag.rectangle([14, H - 32, 14 + tb[2] + 16, H - 12], fill=tuple(int(c) for c in INK))
    dtag.text((22, H - 29), tag, font=f, fill=tuple(int(c) for c in PAPER))
    return out


def sound(mix, bed):
    if bed is not None:
        mix.add(bed, 0.0, gain=1.0)
    mix.thud(1.20, freq=80, gain=0.55)                         # A3 shove (synthetic, declared)
    mix.click(1.33, gain=0.35, bright=2500, seconds=0.05)      # A4 shoulder on the brass stanchion
    for k in range(13):                                        # runners' steps (synthetic, declared)
        mix.step(0.08 + k * 0.125, gain=0.16, surface="stone", pan=-0.2)
    mix.bell(6.00, freq=1320, seconds=2.0, gain=0.30, pan=0.3)  # A7 bell


def main():
    setup()
    sim = simulate()
    WS.joinpath("test-shot-build").mkdir(exist_ok=True)
    energy = [float(s["energy"]) for s in sim]
    (MEDIA / "cord-energy.json").write_text(json.dumps(dict(fps=FPS, energy=energy)))
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        ts = [float(x) for x in sys.argv[2:]]
        for t in ts:
            render_frame(int(round(t * FPS)), sim).save(MEDIA / f"still_{t:05.2f}.png")
        print("stills", ts); return
    bed = None
    bedp = MEDIA / "bed.wav"
    if bedp.exists():
        with wave.open(str(bedp)) as wf:
            n = wf.getnframes(); ch = wf.getnchannels()
            x = np.frombuffer(wf.readframes(n), np.int16).astype(np.float64) / 32768
            if ch == 2:
                x = x.reshape(-1, 2).mean(1)
            bed = x[: int(CLIP * kit.RATE)]
    mix = kit.Mix(CLIP, seed=SEED)
    sound(mix, bed)
    pcm = mix.master()
    wav = MEDIA / "test-shot-mix.wav"
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(kit.RATE); wf.writeframes(pcm.tobytes())
    mp4 = WS / "test-shot.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-tune", "animation",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(NF):
        im = render_frame(f, sim)
        im = kit._add_grain(im, f)          # kit's paper grain (same bank as the other films)
        if f in (14, 29, 32, 60):
            im.save(MEDIA / f"frame_{f:03d}.png")
        proc.stdin.write(im.tobytes())
    proc.stdin.close(); proc.wait()
    print("wrote", mp4, mp4.stat().st_size)


if __name__ == "__main__":
    main()
