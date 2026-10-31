"""The place, cut from paper: a dollhouse section through a doorway at dusk. Room on the left (x < 0), the wall cut through
(0 .. 0.30 m), the sill, and the porch to the right out to the steps at 4.9 m (score x; the dog's torso centre is drawn at
score x - 0.12). Everything here is drawn in code as polygons with pierced (lace) holes; nothing is imported.
Coordinates: world metres, y up, ground 0. Camera maps to pixels."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

W, H = 1280, 720
SS = 2
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'cache', 'fonts')

PAL = {
    'sky_top': (22, 26, 58), 'sky_low': (78, 52, 84), 'moon': (238, 226, 196), 'hill1': (36, 38, 72), 'hill2': (20, 24, 44),
    'wall_cut': (92, 46, 38), 'wall_cut_dark': (58, 28, 26), 'jamb': (120, 84, 58), 'sill': (150, 136, 118),
    'floor': (62, 66, 92), 'floor_line': (44, 46, 70), 'fascia': (30, 30, 52), 'lattice_bg': (14, 14, 26),
    'roof': (34, 30, 52), 'trim': (150, 128, 170), 'post': (40, 36, 60), 'step': (52, 54, 80),
    'room_wall': (150, 98, 62), 'room_glow': (255, 196, 110), 'room_floor': (110, 70, 46), 'rug': (150, 52, 44),
    'door': (40, 78, 70), 'door_panel': (28, 56, 50), 'stool': (98, 64, 40), 'lamp': (240, 210, 150),
    'dog': (214, 62, 40), 'dog_edge': (96, 22, 14), 'person': (30, 36, 70), 'person_edge': (12, 14, 30),
    'cream': (240, 230, 206),
}


class Camera:
    def __init__(self, left, right, y0):
        self.left, self.right = left, right
        self.s = W / (right - left)
        self.y0 = y0

    def px(self, X, Y, ss=SS):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        return np.stack([(X - self.left) * self.s * ss, (self.y0 - Y * self.s) * ss], -1)

    def inv_x(self, sx):
        return sx / self.s + self.left


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def mask_from(polys, holes=(), size=(W, H)):
    """Polys/holes in SS-pixel coords -> antialiased 1x mask (float32 0..1)."""
    m = Image.new('L', (size[0] * SS, size[1] * SS), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        if len(p) >= 3:
            d.polygon([tuple(q) for q in np.asarray(p)], fill=255)
    for p in holes:
        if len(p) >= 3:
            d.polygon([tuple(q) for q in np.asarray(p)], fill=0)
    m = m.resize(size, Image.LANCZOS)
    return np.asarray(m, np.float32) / 255.0


def paper_texture(seed=7):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    img = Image.fromarray(((n * 20 + 128).clip(0, 255)).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    fib = np.asarray(img, np.float32) / 255.0 - 0.5
    # long fibres
    f2 = Image.fromarray(((rng.normal(0, 1, (H // 8, W)) * 30 + 128).clip(0, 255)).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    fib2 = np.asarray(f2, np.float32) / 255.0 - 0.5
    return 1.0 + 0.10 * fib + 0.05 * fib2


TEX = paper_texture()


def comp(canvas, m, color, shadow=None, edge=None, tex=True):
    """Lay a paper layer: drop shadow (dx, dy, blur px, opacity), body colour (rgb or HxWx3), cut edge darkening.
    Works on the bounding box of the layer (plus the shadow's reach) only."""
    ys, xs = np.nonzero(m > 0.002)
    if len(ys) == 0:
        return canvas
    pad = 2
    if shadow is not None:
        pad += int(abs(shadow[0]) + abs(shadow[1]) + 3 * shadow[2] + 2)
    y0, y1 = max(0, ys.min() - pad), min(canvas.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(canvas.shape[1], xs.max() + pad + 1)
    sub = canvas[y0:y1, x0:x1]
    mm = m[y0:y1, x0:x1]
    if shadow is not None:
        dx, dy, bl, op = shadow
        sm = Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(bl))
        sm = np.asarray(sm, np.float32) / 255.0
        sm = np.roll(np.roll(sm, int(dy), 0), int(dx), 1)
        sub *= (1 - op * sm)[..., None]
    col = np.asarray(color, np.float32)
    if col.ndim == 1:
        col = np.broadcast_to(col, sub.shape)
    else:
        col = col[y0:y1, x0:x1]
    if tex:
        col = col * TEX[y0:y1, x0:x1, None]
    if edge is not None:
        er = Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))
        inner = np.asarray(er, np.float32) / 255.0
        rim = np.clip(mm - inner, 0, 1)
        col = col * (1 - rim[..., None]) + np.asarray(edge, np.float32) * rim[..., None]
    sub[:] = sub * (1 - mm[..., None]) + col * mm[..., None]
    return canvas


def circle(c, r, n=28):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1)


def rect(x0, y0, x1, y1):
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], float)


# ---------------------------------------------------------------- screen-fixed backdrop: sky, moon, hills
def backdrop():
    c = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None, None]
    c[:] = np.asarray(PAL['sky_top']) * (1 - yy ** 1.6) + np.asarray(PAL['sky_low']) * yy ** 1.6
    rng = np.random.default_rng(3)
    stars = [circle((rng.uniform(560, 1270) * SS, rng.uniform(10, 300) * SS), rng.uniform(1.0, 2.2) * SS, 8) for _ in range(46)]
    comp(c, mask_from(stars), (226, 220, 236), tex=False)
    # moon: a cream disc pierced with a crescent of small holes
    mc = np.array([1010, 112]) * SS
    holes = [circle(mc + np.array(o) * SS, r * SS, 14) for o, r in (((-14, -12), 7), ((12, 4), 5), ((-4, 16), 4), ((18, -16), 3.5), ((-22, 8), 3))]
    comp(c, mask_from([circle(mc, 40 * SS, 64)], holes), PAL['moon'], shadow=(3, 3, 3, .35), edge=(190, 176, 150))
    # far hills (two layers), with pierced leaf-holes in the near one
    xs = np.linspace(-20, W + 20, 60)
    h1 = 470 - 40 * np.sin(xs / 150) - 20 * np.sin(xs / 47 + 1)
    p1 = np.concatenate([np.stack([xs, h1], 1), [[W + 20, H], [-20, H]]]) * SS
    comp(c, mask_from([p1]), PAL['hill1'], shadow=(0, -2, 4, .3))
    trees = []
    holes = []
    for k, tx in enumerate([620, 720, 860, 980, 1110, 1215]):
        ty = 440 - 30 * np.sin(tx / 90)
        r = 46 + 14 * np.sin(k * 2.1)
        trees.append(circle((tx * SS, (ty - r * 0.9) * SS), r * SS, 40))
        trees.append(rect((tx - 5) * SS, (ty - r * 0.5) * SS, (tx + 5) * SS, 520 * SS))
        for j in range(5):
            a = j * 1.3 + k
            holes.append(circle(((tx + 0.5 * r * np.cos(a)) * SS, (ty - r * 0.9 + 0.5 * r * np.sin(a)) * SS), 5 * SS, 10))
    xs2 = np.linspace(-20, W + 20, 60)
    h2 = 505 - 18 * np.sin(xs2 / 90 + 2)
    trees.append(np.concatenate([np.stack([xs2, h2], 1), [[W + 20, H], [-20, H]]]) * SS)
    comp(c, mask_from(trees, holes), PAL['hill2'], shadow=(0, -3, 5, .35))
    return c


# ---------------------------------------------------------------- the built world (moves with the camera)
WALL0, WALL1 = 0.0, 0.30      # wall section
DOOR_TOP = 2.05
SILL_TOP = 0.05
ROOF_Y = 2.45
PORCH_END = 4.9 - 0.12


def floor_band(cam):
    far, near = 0.11, 0.34    # metres of floor depth seen above / below the dog's ground line
    return far, near


def room(canvas, cam, light, t):
    """Room interior: back wall with lace wallpaper (holes show the lamp-lit layer behind), floor, rug, lamp."""
    L = cam.left - 0.5
    glow = np.asarray(PAL['room_glow']) * (0.55 + 0.45 * light)
    wall_col = np.asarray(PAL['room_wall']) * (0.62 + 0.38 * light)
    far, near = floor_band(cam)
    # glow layer behind everything in the room
    comp(canvas, mask_from([cam.px(*rect(L, -near, WALL0, 6.0).T)]), glow, tex=False)
    holes = []
    for i, x in enumerate(np.arange(L + 0.12, WALL0, 0.26)):
        for j, y in enumerate(np.arange(far + 0.35, 3.4, 0.34)):
            yy = y + (0.17 if i % 2 else 0)
            holes.append(cam.px(*circle((x, yy), 0.035, 10).T))
            for a in range(4):
                ang = a * np.pi / 2 + np.pi / 4
                holes.append(cam.px(*circle((x + 0.065 * np.cos(ang), yy + 0.065 * np.sin(ang)), 0.014, 8).T))
    # framed picture on the back wall: a small cut moon over a hill
    holes.append(cam.px(*rect(-1.05, 1.35, -0.62, 1.70).T))
    comp(canvas, mask_from([cam.px(*rect(L, far, WALL0, 6.0).T)], holes), wall_col)
    pic = [cam.px(*circle((-0.76, 1.58), 0.05).T), cam.px(*np.array([(-1.05, 1.35), (-0.9, 1.47), (-0.75, 1.40), (-0.62, 1.50), (-0.62, 1.35)]).T)]
    comp(canvas, mask_from(pic), np.asarray(PAL['room_wall']) * (0.35 + 0.4 * light))
    # floor band and rug
    comp(canvas, mask_from([cam.px(*rect(L, -near, WALL0, far).T)]), np.asarray(PAL['room_floor']) * (0.45 + 0.55 * light),
         shadow=(0, -3, 4, .25))
    rug = cam.px(*np.array([(-1.75, -0.20), (-0.15, -0.20), (-0.05, 0.06), (-1.62, 0.06)]).T)
    rh = [cam.px(*circle((x, -0.07), 0.03, 10).T) for x in np.arange(-1.55, -0.2, 0.16)]
    comp(canvas, mask_from([rug], rh), np.asarray(PAL['rug']) * (0.45 + 0.55 * light))
    # lamp (left), its shade pierced so it glows
    lx = -1.72
    shade = cam.px(*np.array([(lx - 0.17, 1.42), (lx + 0.17, 1.42), (lx + 0.10, 1.70), (lx - 0.10, 1.70)]).T)
    pole = cam.px(*rect(lx - 0.012, 0.0, lx + 0.012, 1.45).T)
    base = cam.px(*rect(lx - 0.13, 0.0, lx + 0.13, 0.04).T)
    comp(canvas, mask_from([pole, base]), (40, 30, 26), shadow=(3, 2, 3, .3))
    sh = [cam.px(*circle((lx + dx, 1.56), 0.022, 10).T) for dx in (-0.08, 0.0, 0.08)]
    comp(canvas, mask_from([shade], sh), np.asarray(PAL['lamp']) * (0.55 + 0.45 * light), shadow=(3, 2, 3, .3), edge=(120, 90, 60))


def jamb(canvas, cam, light):
    """The far jamb face, seen through the cut doorway (lit from inside when open); the person stands in front of it."""
    jcol = np.asarray(PAL['jamb']) * (0.55 + 0.45 * light)
    comp(canvas, mask_from([cam.px(*rect(WALL0, SILL_TOP, WALL1, DOOR_TOP).T)]), jcol)


def door_leaf(canvas, cam, open_amt, light):
    """The door hinges on the far jamb at the inside face; seen in section it opens into a panel flat against the room."""
    psi = np.radians(10 + 75 * open_amt)
    w = 0.88 * np.sin(psi)
    if w < 0.02:
        return
    x0 = WALL0 - w
    leaf = cam.px(*rect(x0, SILL_TOP, WALL0, DOOR_TOP - 0.02).T)
    k = w / 0.88
    holes = []
    for (a, b, c, d) in ((0.12, 0.25, 0.88, 1.0), (1.10, 0.25, 1.85, 1.0)):
        holes.append(cam.px(*rect(x0 + w * (1 - b / 1.0) * 0 + w * 0.14, a, x0 + w * 0.86, c).T))
    col = np.asarray(PAL['door']) * (0.55 + 0.45 * light)
    comp(canvas, mask_from([leaf], holes), col, shadow=(4, 2, 5, .4), edge=(14, 30, 26))
    comp(canvas, mask_from(holes), np.asarray(PAL['door_panel']) * (0.55 + 0.45 * light))
    knob = cam.px(*circle((x0 + 0.08 * k, 1.0), 0.03).T)
    comp(canvas, mask_from([knob]), (200, 170, 90))


def house_and_porch(canvas, cam, light, t):
    far, near = floor_band(cam)
    # porch floor band
    fl = cam.px(*rect(WALL1, -near, PORCH_END, far).T)
    lines = []
    for k, y in enumerate(np.linspace(-near, far, 7)[1:-1]):
        lines.append(cam.px(*rect(WALL1, y - 0.004, PORCH_END, y + 0.004).T))
    comp(canvas, mask_from([fl]), PAL['floor'], shadow=(0, -3, 4, .3))
    comp(canvas, mask_from(lines), PAL['floor_line'], tex=False)
    # steps down at the end of the porch
    st = []
    for k in range(3):
        x0 = PORCH_END + 0.28 * k
        st.append(cam.px(*rect(x0, -near - 0.20 * (k + 1), x0 + 0.4, far - 0.20 * (k + 1)).T))
    comp(canvas, mask_from(st), PAL['step'], shadow=(-3, 3, 4, .4), edge=(30, 30, 50))
    # lattice skirt under the porch (diamond lattice, pierced)
    sk = cam.px(*rect(WALL1, -3.0, PORCH_END, -near).T)
    holes = []
    step = 0.22
    for i, x in enumerate(np.arange(WALL1 + 0.1, PORCH_END, step)):
        for j, y in enumerate(np.arange(-near - 0.12, -2.6, -step / 1.4)):
            xx = x + (step / 2 if j % 2 else 0)
            if xx < PORCH_END - 0.05:
                holes.append(cam.px(*np.array([(xx, y + 0.06), (xx + 0.075, y), (xx, y - 0.06), (xx - 0.075, y)]).T))
    comp(canvas, mask_from([sk], holes), PAL['fascia'], shadow=(0, 3, 4, .3))
    # fascia board along the porch edge with a scalloped lace border
    fas = [cam.px(*rect(WALL1, -near - 0.10, PORCH_END, -near).T)]
    sc = [cam.px(*circle((x, -near - 0.10), 0.045, 14).T) for x in np.arange(WALL1 + 0.06, PORCH_END, 0.12)]
    comp(canvas, mask_from(fas + sc, [cam.px(*circle((x, -near - 0.05), 0.016, 10).T) for x in np.arange(WALL1 + 0.12, PORCH_END, 0.12)]),
         (46, 44, 74), shadow=(0, 3, 3, .3), edge=(20, 20, 36))
    # porch post and roof with gingerbread trim
    post = cam.px(*rect(PORCH_END - 0.16, -0.05, PORCH_END - 0.06, ROOF_Y).T)
    comp(canvas, mask_from([post]), PAL['post'], shadow=(4, 2, 4, .35), edge=(20, 18, 34))
    roof = cam.px(*np.array([(WALL0 - 0.05, ROOF_Y + 0.55), (PORCH_END + 0.35, ROOF_Y + 0.05), (PORCH_END + 0.35, ROOF_Y - 0.05),
                             (WALL0 - 0.05, ROOF_Y + 0.40)]).T)
    trim = []
    trim_holes = []
    for x in np.arange(WALL1, PORCH_END + 0.3, 0.16):
        yb = ROOF_Y + 0.40 - (x - WALL0) * (0.45 / (PORCH_END + 0.4)) - 0.04
        trim.append(cam.px(*np.array([(x - 0.08, yb + 0.05), (x + 0.08, yb + 0.05), (x + 0.08, yb - 0.02), (x, yb - 0.11),
                                      (x - 0.08, yb - 0.02)]).T))
        trim_holes.append(cam.px(*circle((x, yb - 0.02), 0.022, 10).T))
    comp(canvas, mask_from(trim, trim_holes), PAL['trim'], shadow=(2, 4, 4, .4), edge=(90, 70, 110))
    comp(canvas, mask_from([roof]), PAL['roof'], shadow=(0, 4, 5, .4))
    # the wall cut: above the lintel and below the sill; hatched with pierced slots (an architect's section, in lace)
    up = cam.px(*rect(WALL0, DOOR_TOP, WALL1, 4.5).T)
    dn = cam.px(*rect(WALL0, -3.0, WALL1, -near).T)
    hs = []
    for y in np.arange(DOOR_TOP + 0.1, 4.4, 0.12):
        hs.append(cam.px(*np.array([(WALL0 + 0.05, y), (WALL0 + 0.09, y), (WALL1 - 0.05, y + 0.08), (WALL1 - 0.09, y + 0.08)]).T))
    for y in np.arange(-near - 0.1, -2.9, -0.12):
        hs.append(cam.px(*np.array([(WALL0 + 0.05, y), (WALL0 + 0.09, y), (WALL1 - 0.05, y + 0.08), (WALL1 - 0.09, y + 0.08)]).T))
    comp(canvas, mask_from([up, dn], hs), PAL['wall_cut'], shadow=(5, 3, 6, .45), edge=PAL['wall_cut_dark'])
    # sill: a pale stone across the doorway, the whole depth of the floor band
    sill = cam.px(*np.array([(WALL0 - 0.03, -near), (WALL1 + 0.05, -near), (WALL1 + 0.05, SILL_TOP), (WALL0 - 0.03, SILL_TOP + 0.0)]).T)
    sill_top = cam.px(*rect(WALL0 - 0.03, SILL_TOP - 0.004, WALL1 + 0.05, SILL_TOP + far * 0.9).T)
    comp(canvas, mask_from([sill, sill_top]), np.asarray(PAL['sill']) * (0.62 + 0.38 * light), shadow=(3, 3, 4, .4), edge=(120, 106, 88))


def light_pool(canvas, cam, light):
    """Light out of the open door: a warm wedge on the porch floor, strongest at the sill."""
    if light <= 0.01:
        return
    far, near = floor_band(cam)
    xs = (np.arange(W) / cam.s + cam.left)
    fall = np.clip(1 - (xs - WALL1) / 2.6, 0, 1) ** 1.7 * (xs > WALL0 - 0.03)
    ys = np.arange(H)
    Y = (cam.y0 - ys) / cam.s
    band = ((Y > -near) & (Y < far + 0.02)).astype(np.float32)
    # the light also falls on the sill and a soft spill in the air of the doorway
    door_air = ((xs >= WALL0) & (xs <= WALL1)).astype(np.float32)[None, :] * ((Y > SILL_TOP) & (Y < DOOR_TOP))[:, None]
    m = band[:, None] * fall[None, :] * 0.50 + door_air * 0.10
    m[:, (xs >= WALL0 - 0.03) & (xs <= WALL1 + 0.05)] *= 0.55
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255.0
    warm = np.array([255, 190, 110], np.float32)
    canvas[:] = canvas + (warm[None, None, :] * 0.85 - canvas * 0.25) * (m * light)[..., None]


def stool(canvas, cam):
    x = -1.25 - 0.08
    seat = cam.px(*rect(x - 0.2, 0.42, x + 0.2, 0.47).T)
    legs = [cam.px(*np.array([(x - 0.17, 0.42), (x - 0.13, 0.42), (x - 0.19, 0.0), (x - 0.23, 0.0)]).T),
            cam.px(*np.array([(x + 0.13, 0.42), (x + 0.17, 0.42), (x + 0.23, 0.0), (x + 0.19, 0.0)]).T)]
    comp(canvas, mask_from([seat] + legs, [cam.px(*circle((x, 0.445), 0.012, 8).T)]), PAL['stool'], shadow=(4, 3, 4, .35), edge=(50, 30, 20))


def tri_mask(Xpx, F, size=(W, H)):
    """Fast vectorised rasteriser for a deformed triangle mesh (coords in SS pixels) -> antialiased 1x mask.
    Each triangle tests the SS-pixel centres inside its own bounding box; very large triangles fall back to PIL."""
    Wd2, Hd2 = size[0] * SS, size[1] * SS
    P = Xpx[F]                                   # m,3,2
    lo = np.floor(P.min(1)).astype(int); hi = np.ceil(P.max(1)).astype(int)
    ext = (hi - lo).max(1)
    m = np.zeros((Hd2, Wd2), bool)
    big = ext > 24
    for lo_e, hi_e in ((-1, 6), (6, 12), (12, 24)):
        sel = (ext > lo_e) & (ext <= hi_e)
        if not sel.any():
            continue
        Ps, los = P[sel], lo[sel]
        K = hi_e + 1
        o = np.arange(K)
        gx = los[:, 0, None, None] + o[None, None, :] + 0.5
        gy = los[:, 1, None, None] + o[None, :, None] + 0.5
        gx = np.broadcast_to(gx, (len(Ps), K, K)); gy = np.broadcast_to(gy, (len(Ps), K, K))

        def edge(a, b):
            return ((b[:, 0] - a[:, 0])[:, None, None] * (gy - a[:, 1][:, None, None]) -
                    (b[:, 1] - a[:, 1])[:, None, None] * (gx - a[:, 0][:, None, None]))
        e0 = edge(Ps[:, 0], Ps[:, 1]); e1 = edge(Ps[:, 1], Ps[:, 2]); e2 = edge(Ps[:, 2], Ps[:, 0])
        inside = ((e0 >= 0) & (e1 >= 0) & (e2 >= 0)) | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0))
        xi = gx[inside].astype(int); yi = gy[inside].astype(int)
        ok = (xi >= 0) & (xi < Wd2) & (yi >= 0) & (yi < Hd2)
        m[yi[ok], xi[ok]] = True
    if big.any():
        img = Image.fromarray(m.astype(np.uint8) * 255)
        d = ImageDraw.Draw(img)
        for p in P[big]:
            d.polygon([tuple(q) for q in p], fill=255)
        m = np.asarray(img) > 0
    mm = m.reshape(size[1], SS, size[0], SS).mean((1, 3)).astype(np.float32)
    return mm
