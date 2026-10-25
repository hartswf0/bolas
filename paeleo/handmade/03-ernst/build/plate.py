"""SCION 03 Ernst · the plate: the porch, the facade, the door and the dusk, built as engraved regions.

Every region of the set is a projected world quad with its own line system (direction, period, tone), as an engraver
would give each material its own cut: ruled sky, clapboard, door grain, porch boards, a stippled stone sill.  The plate is
assembled per frame from a cached still layer plus the moving door, the light it lets out, and the deepening dusk.
"""
import numpy as np
from PIL import Image, ImageDraw
import sdf
import burin

W, H = 1280, 720
SS = 2                       # region masks are drawn at 2x and box-filtered (soft region edges)
PLATE = (34, 20, 1246, 628)  # the engraved plate's border on the page (the caption sits below)
DOOR_X = (-0.46, 0.46)
DOOR_H = 2.12
WALL_T = 0.24                # wall (reveal) thickness: the doorway goes from z=0 back to z=-WALL_T
FACADE_END = 3.05
STEPS_X = 4.9
PORCH_Z = 2.0
SILL = dict(x=(-0.58, 0.58), z=(-WALL_T, 0.34), h=0.05)

gy, gx = np.mgrid[0:H, 0:W].astype(float) + 0.5


def P(x, y, z):
    sx, sy, _ = sdf.project(np.array([x, y, z], float))
    return float(sx), float(sy)


def mask_poly(pts):
    im = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    a = np.asarray(im, float).reshape(H, SS, W, SS).mean(axis=(1, 3)) / 255
    return a


def quad(c):
    return mask_poly([P(*p) for p in c])


def noise2(seed, scale, shape=(H, W)):
    rng = np.random.default_rng(seed)
    h, w = shape
    sh, sw = h // scale + 3, w // scale + 3
    g = rng.standard_normal((sh, sw))
    im = Image.fromarray(((g - g.min()) / (g.max() - g.min()) * 255).astype(np.uint8))
    im = im.resize((sw * scale, sh * scale), Image.BICUBIC)
    a = np.asarray(im, float)[:h, :w] / 255
    return a * 2 - 1


N1 = noise2(1, 40)
N2 = noise2(2, 9)
N3 = noise2(3, 120)


class Layer:
    """a set of regions painted in order: each paints darkness, a line coordinate u (+ optional v) and a tint."""

    def __init__(self):
        self.dark = np.zeros((H, W)); self.u = np.zeros((H, W)); self.v = np.full((H, W), np.nan)
        self.ink = np.zeros((H, W))          # solid contour ink
        self.cov = np.zeros((H, W))          # alpha (how much of the plate is covered)
        self.lit = np.zeros((H, W))          # 0..1 how much this pixel can receive the door's light

    def paint(self, m, dark, u, v=None, lit=None):
        m = np.clip(m, 0, 1)
        hard = m > 0.5
        self.dark = self.dark * (1 - m) + dark * m
        self.u = np.where(hard, u, self.u)
        if v is not None:
            self.v = np.where(hard, v, self.v)
        else:
            self.v = np.where(hard, np.nan, self.v)
        if lit is not None:
            self.lit = self.lit * (1 - m) + lit * m
        self.cov = np.maximum(self.cov, m)

    def contour(self, m, w=1.0):
        self.ink = np.maximum(self.ink, burin.edge(m > 0.5, w))


def hlines(period, wob=0.25, slope=0.0):
    return (gy + slope * gx + wob * period * N2 * 0.3 + 0.8 * N1 * wob * 4) / period


def vlines(period, wob=0.25):
    return (gx + wob * period * N2 * 0.3 + 0.8 * N1 * wob * 4) / period


def slines(period, ang):
    a = np.radians(ang)
    return (gx * np.sin(a) + gy * np.cos(a) + 1.5 * N1) / period


def build_static():
    """the parts of the plate that never move.  Returns a Layer."""
    L = Layer()
    x0, y0, x1, y1 = PLATE
    # sky: ruled lines, darker toward the top (dusk); a pale band at the horizon
    hz = P(0, 0, -6)[1] - 40
    sky_t = np.clip(0.30 + 0.55 * (hz - gy) / hz, 0.2, 0.9)
    L.paint(np.ones((H, W)), sky_t, hlines(3.6, 0.1))
    # beyond the porch: the garden ground (lower than the porch), a picket fence, a hedge of trees, the dusk sky
    gnd = quad([(FACADE_END, -0.66, 0.0), (8, -0.66, 0.0), (8, -0.66, -9), (FACADE_END, -0.66, -9)])
    L.paint(gnd, np.clip(0.66 + 0.08 * N1, 0, 1), hlines(3.6, 0.3))
    hedge_top = 262 + 26 * np.sin(gx / 47.0) ** 2 + 18 * np.abs(np.sin(gx / 19.0 + 1.3)) + 10 * N2 - 40 * np.clip((gx - 1120) / 120, 0, 1)
    hedge = ((gy > hedge_top) & (gy < P(0, -0.66, -3.0)[1])).astype(float) * (gx > P(FACADE_END, 0, 0)[0])
    L.paint(hedge, np.clip(0.8 + 0.1 * N2 + 0.06 * N1, 0, 1), slines(3.3, 70), slines(3.3, -25))
    # the moon, low over the hedge (paper left uncut, a few ruled lines across it)
    mc = (1150.0, 118.0)
    md = np.hypot(gx - mc[0], gy - mc[1])
    moon = (md < 26).astype(float) * (np.hypot(gx - mc[0] - 9, gy - mc[1] + 4) > 23)
    L.paint(moon, 0.06, hlines(3.6))
    # picket fence in front of the hedge
    for k in range(14):
        fx = FACADE_END + 0.25 + k * 0.33
        pk = quad([(fx, -0.66, -2.2), (fx + 0.09, -0.66, -2.2), (fx + 0.09, 0.32, -2.2), (fx + 0.045, 0.4, -2.2), (fx, 0.32, -2.2)])
        L.paint(pk, 0.4, vlines(3.0)); L.contour(pk, 0.7)
    rail = quad([(FACADE_END, 0.05, -2.18), (9, 0.05, -2.18), (9, 0.11, -2.18), (FACADE_END, 0.11, -2.18)])
    L.paint(rail, 0.5, hlines(2.8)); L.contour(rail, 0.7)
    # the facade: clapboard from left edge to FACADE_END, up to the top of the plate
    fac = quad([(-4, 0, 0), (FACADE_END, 0, 0), (FACADE_END, 6, 0), (-4, 6, 0)])
    board = 0.19
    yw = (P(0, 0, 0)[1] - gy) / (sdf.SCALE * np.cos(sdf.PITCH))       # world height on the facade plane
    fb = (yw / board) % 1.0
    lap = np.exp(-fb / 0.12) * 0.35                                         # shadow under each lap
    door_c = P(0, 1.0, 0)
    vign = np.clip(np.hypot((gx - door_c[0]) / 700.0, (gy - door_c[1]) / 520.0), 0, 1)
    fac_t = np.clip(0.22 + lap * 0.8 + 0.04 * N1 + 0.5 * vign ** 1.3, 0, 1)
    L.paint(fac, fac_t, hlines(3.9, 0.04), lit=np.ones((H, W)) * 0.5)
    # a lap line at every board
    lapline = (np.abs(fb - 0.0) < 0.018) | (fb > 0.985)
    L.ink = np.maximum(L.ink, (fac > 0.5) * lapline * 0.55)
    # corner board
    cb = quad([(FACADE_END - 0.14, 0, 0.0), (FACADE_END, 0, 0.0), (FACADE_END, 6, 0.0), (FACADE_END - 0.14, 6, 0.0)])
    L.paint(cb, 0.35 + 0.05 * N1, vlines(3.6)); L.contour(cb, 0.8)
    # the end wall of the house, seen edge-on beyond the corner (shadow side): a narrow dark strip
    ew = quad([(FACADE_END, 0, 0), (FACADE_END, 0, -2.5), (FACADE_END, 6, -2.5), (FACADE_END, 6, 0)])
    L.paint(ew, 0.8, vlines(3.2))
    L.contour(fac, 0.8)
    # a window to the left of the door (dark panes, a sash)
    for wx in (-2.25,):
        frame = quad([(wx - 0.5, 0.95, 0), (wx + 0.5, 0.95, 0), (wx + 0.5, 2.15, 0), (wx - 0.5, 2.15, 0)])
        L.paint(frame, 0.3, vlines(3.6)); L.contour(frame)
        for (a, b, c, d) in ((wx - 0.42, wx - 0.03, 1.02, 1.55), (wx + 0.03, wx + 0.42, 1.02, 1.55),
                             (wx - 0.42, wx - 0.03, 1.6, 2.08), (wx + 0.03, wx + 0.42, 1.6, 2.08)):
            pane = quad([(a, c, 0), (b, c, 0), (b, d, 0), (a, d, 0)])
            L.paint(pane, 0.86 + 0.06 * N2, slines(3.2, 35), slines(3.2, -35)); L.contour(pane, 0.7)
        sill_w = quad([(wx - 0.6, 0.9, 0.05), (wx + 0.6, 0.9, 0.05), (wx + 0.6, 0.97, 0.05), (wx - 0.6, 0.97, 0.05)])
        L.paint(sill_w, 0.25, hlines(3.4)); L.contour(sill_w)
    # the door case: pilasters, a lintel with a cornice, the keystone block where the lion will settle
    dl, dr = DOOR_X
    pil_w = 0.13
    for a, b in ((dl - pil_w, dl), (dr, dr + pil_w)):
        pil = quad([(a, 0, 0.03), (b, 0, 0.03), (b, DOOR_H, 0.03), (a, DOOR_H, 0.03)])
        L.paint(pil, 0.3 + 0.05 * N1, vlines(3.4)); L.contour(pil)
        flute = quad([(a + 0.04, 0.15, 0.03), (b - 0.04, 0.15, 0.03), (b - 0.04, DOOR_H - 0.1, 0.03), (a + 0.04, DOOR_H - 0.1, 0.03)])
        L.paint(flute, 0.52, vlines(3.0)); L.contour(flute, 0.6)
    lint = quad([(dl - 0.2, DOOR_H, 0.04), (dr + 0.2, DOOR_H, 0.04), (dr + 0.2, DOOR_H + 0.22, 0.04), (dl - 0.2, DOOR_H + 0.22, 0.04)])
    L.paint(lint, 0.34, hlines(3.4)); L.contour(lint)
    corn = quad([(dl - 0.3, DOOR_H + 0.22, 0.08), (dr + 0.3, DOOR_H + 0.22, 0.08), (dr + 0.3, DOOR_H + 0.32, 0.08), (dl - 0.3, DOOR_H + 0.32, 0.08)])
    L.paint(corn, 0.6, hlines(3.0)); L.contour(corn)
    # porch floor boards (z from the facade to the porch edge), running along x
    flo = quad([(-4, 0, 0), (STEPS_X, 0, 0), (STEPS_X, 0, PORCH_Z), (-4, 0, PORCH_Z)])
    zf = None
    # world z of a floor pixel: invert the projection on y=0
    zf = sdf.ZD + (gy - sdf.Y0) / (sdf.SCALE * np.sin(sdf.PITCH))
    bw = 0.105
    fbz = (zf / bw) % 1.0
    joint = np.exp(-np.minimum(fbz, 1 - fbz) / 0.05) * 0.35
    flo_t = np.clip(0.5 + joint + 0.06 * N1 + 0.1 * (zf / PORCH_Z), 0, 1)
    L.paint(flo, flo_t, hlines(3.2, 0.3), lit=np.clip(1.0, 0, 1))
    L.ink = np.maximum(L.ink, (flo > 0.5) * (np.minimum(fbz, 1 - fbz) < 0.04) * 0.5)
    # plank ends (butt joints) staggered
    rng = np.random.default_rng(7)
    for row in range(int(PORCH_Z / bw) + 1):
        for k in range(4):
            xj = rng.uniform(-3.5, 4.6)
            a = P(xj, 0, row * bw); b = P(xj, 0, (row + 1) * bw)
            m = (np.abs(gx - a[0]) < 0.6) & (gy > min(a[1], b[1])) & (gy < max(a[1], b[1]))
            L.ink = np.maximum(L.ink, m * 0.5)
    # porch fascia (front edge)
    fas = quad([(-4, 0, PORCH_Z), (STEPS_X, 0, PORCH_Z), (STEPS_X, -0.3, PORCH_Z), (-4, -0.3, PORCH_Z)])
    L.paint(fas, 0.7, vlines(3.4)); L.contour(fas)
    # lattice below the porch
    lat = quad([(-4, -0.3, PORCH_Z), (STEPS_X, -0.3, PORCH_Z), (STEPS_X, -1.2, PORCH_Z), (-4, -1.2, PORCH_Z)])
    lu = (gx + gy) / 22.0; lv = (gx - gy) / 22.0
    grid = (np.abs(lu - np.round(lu)) < 0.1) | (np.abs(lv - np.round(lv)) < 0.1)
    L.paint(lat, np.where(grid, 0.35, 0.92), slines(3.0, 45), slines(3.0, -45))
    # steps down at the porch end
    for i in range(3):
        sx0 = STEPS_X + i * 0.28
        top = -0.22 * i
        st = quad([(sx0, top, -0.2), (sx0 + 0.28, top, -0.2), (sx0 + 0.28, top, PORCH_Z), (sx0, top, PORCH_Z)])
        L.paint(st, 0.45 + 0.1 * i, hlines(3.2)); L.contour(st)
        rs = quad([(sx0 + 0.28, top, PORCH_Z), (sx0 + 0.28, top - 0.22, PORCH_Z), (sx0 + 0.28, top - 0.22, -0.2), (sx0 + 0.28, top, -0.2)])
        L.paint(rs, 0.75, vlines(3.0))
    # a newel post at the head of the steps
    post = quad([(STEPS_X - 0.12, 0, PORCH_Z - 0.08), (STEPS_X, 0, PORCH_Z - 0.08), (STEPS_X, 1.0, PORCH_Z - 0.08), (STEPS_X - 0.12, 1.0, PORCH_Z - 0.08)])
    L.paint(post, 0.5, vlines(3.2)); L.contour(post)
    cap = quad([(STEPS_X - 0.16, 1.0, PORCH_Z - 0.08), (STEPS_X + 0.04, 1.0, PORCH_Z - 0.08), (STEPS_X + 0.04, 1.08, PORCH_Z - 0.08), (STEPS_X - 0.16, 1.08, PORCH_Z - 0.08)])
    L.paint(cap, 0.7, hlines(3.0)); L.contour(cap)
    # the chair beside the door (furniture: the person will sit here), against the wall
    cx = -1.25
    back = quad([(cx - 0.24, 0.45, 0.12), (cx + 0.24, 0.45, 0.12), (cx + 0.22, 1.05, 0.08), (cx - 0.22, 1.05, 0.08)])
    L.paint(back, 0.38, vlines(3.2)); L.contour(back)
    for k in range(5):
        t = -0.17 + k * 0.085
        sp = quad([(cx + t - 0.015, 0.47, 0.13), (cx + t + 0.015, 0.47, 0.13), (cx + t + 0.015, 0.98, 0.09), (cx + t - 0.015, 0.98, 0.09)])
        L.paint(sp, 0.86, vlines(2.8)); L.contour(sp, 0.6)
    seat = quad([(cx - 0.27, 0.45, 0.12), (cx + 0.27, 0.45, 0.12), (cx + 0.27, 0.45, 0.6), (cx - 0.27, 0.45, 0.6)])
    L.paint(seat, 0.4, hlines(3.0)); L.contour(seat)
    for lx, lz in ((-0.24, 0.57), (0.24, 0.57)):
        leg = quad([(cx + lx - 0.025, 0, lz), (cx + lx + 0.025, 0, lz), (cx + lx + 0.025, 0.45, lz), (cx + lx - 0.025, 0.45, lz)])
        L.paint(leg, 0.7, vlines(3.0)); L.contour(leg, 0.8)
    return L


# ---------------------------------------------------------------------------------------------------------------------
def door_layer(L, ang, light):
    """the doorway: reveal, interior, sill, the door panel at angle `ang` (radians, 0 = shut, opening inward), and the
    interior lamp's light (0..1).  Paints onto a copy of the static layer."""
    dl, dr = DOOR_X
    # the interior seen through the opening: a hall floor receding to a papered back wall with a lamp
    opening = quad([(dl, 0, 0.0), (dr, 0, 0.0), (dr, DOOR_H, 0.0), (dl, DOOR_H, 0.0)])
    hall_dark = 0.9 - 0.72 * light
    back = 3.0
    # wallpaper: a lozenge trellis with a dot (an interior from a catalogue), darker in the dark hall
    wu = (gx + gy * 0.0) / 15.0; wv = gy / 15.0
    lz = np.abs(((wu + wv) % 1.0) - 0.5) + np.abs(((wu - wv) % 1.0) - 0.5)
    paper_pat = np.clip(0.14 * (lz < 0.12) + 0.1 * (lz > 0.46), 0, 1)
    L.paint(opening, np.clip(hall_dark + paper_pat + 0.03 * N2, 0, 1), hlines(2.7, 0.05), lit=np.ones((H, W)))
    hall_floor = quad([(dl - 0.6, 0, -WALL_T), (dr + 0.6, 0, -WALL_T), (dr + 0.6, 0, -back), (dl - 0.6, 0, -back)]) * opening
    L.paint(hall_floor, np.clip(hall_dark + 0.16 + 0.04 * N2, 0, 1), vlines(3.0, 0.05))
    skirting = quad([(dl - 0.6, 0, -back), (dr + 0.6, 0, -back), (dr + 0.6, 0.16, -back), (dl - 0.6, 0.16, -back)]) * opening
    L.paint(skirting, np.clip(hall_dark + 0.3, 0, 1), hlines(2.6, 0.05))
    # the lamp on the hall's back wall: its glow is where the light comes from
    lamp_c = P(0.05, 1.3, -back)
    rr = np.hypot(gx - lamp_c[0], (gy - lamp_c[1]) * 1.05)
    glow = np.clip(1 - rr / 120.0, 0, 1) ** 1.5 * opening
    L.dark = np.where(opening > 0.5, np.clip(L.dark - glow * (0.15 + 0.75 * light), 0, 1), L.dark)
    # the reveal (the jamb's thickness) on the right side of the opening, seen at an angle from above: the sill top
    s = SILL
    sill_top = quad([(s['x'][0], s['h'], s['z'][0]), (s['x'][1], s['h'], s['z'][0]), (s['x'][1], s['h'], s['z'][1]), (s['x'][0], s['h'], s['z'][1])])
    sill_front = quad([(s['x'][0], 0, s['z'][1]), (s['x'][1], 0, s['z'][1]), (s['x'][1], s['h'], s['z'][1]), (s['x'][0], s['h'], s['z'][1])])
    st = np.clip(0.3 + 0.18 * (N2 > 0.35) + 0.05 * N1, 0, 1)
    L.paint(sill_top, st, slines(3.0, 80), lit=np.ones((H, W)))
    L.contour(sill_top, 0.8)
    L.paint(sill_front, 0.62, vlines(2.8)); L.contour(sill_front, 0.8)
    # the door panel: hinged at the left jamb (x = dl, z = 0), opening inward (toward -z)
    c, s_ = np.cos(ang), np.sin(ang)
    wdt = dr - dl
    hx, hz = dl, -WALL_T + 0.02            # the door hangs at the inner face: the reveal in front of it is the door frame
    ex, ez = hx + wdt * c, hz - wdt * s_
    pts = [(hx, 0.01, hz), (ex, 0.01, ez), (ex, DOOR_H - 0.01, ez), (hx, DOOR_H - 0.01, hz)]
    panel = quad(pts)
    L.panel_mask = panel
    # door tone: wood, darker in dusk; when open it is seen against the light (its face is in shade)
    L.paint(panel, np.clip(0.5 + 0.12 * N1 + 0.25 * min(1, ang / 1.2), 0, 1), vlines(3.3))
    L.contour(panel, 1.0)
    # four recessed panels on the door's face (foreshortened with it)
    for (a, b, cc, d) in ((0.12, 0.44, 0.15, 0.95), (0.56, 0.88, 0.15, 0.95), (0.12, 0.44, 1.1, 1.95), (0.56, 0.88, 1.1, 1.95)):
        q = [(hx + wdt * a * c, cc, hz - wdt * a * s_), (hx + wdt * b * c, cc, hz - wdt * b * s_),
             (hx + wdt * b * c, d, hz - wdt * b * s_), (hx + wdt * a * c, d, hz - wdt * a * s_)]
        pm = quad(q)
        L.paint(pm, np.clip(0.62 + 0.25 * min(1, ang / 1.2), 0, 1), vlines(2.9)); L.contour(pm, 0.6)
    # the knob
    kb = P(hx + wdt * 0.92 * c, 1.0, hz - wdt * 0.92 * s_)
    km = (np.hypot(gx - kb[0], gy - kb[1]) < 3.2).astype(float)
    L.paint(km, 0.95, hlines(2.0))
    # the inner face of the right jamb (reveal), visible when looking slightly down: a narrow vertical strip
    rv = quad([(dr, 0, 0.0), (dr, 0, -WALL_T), (dr, DOOR_H, -WALL_T), (dr, DOOR_H, 0.0)])
    L.paint(rv, np.clip(0.75 - 0.45 * light, 0, 1), vlines(2.8), lit=np.ones((H, W)))
    L.contour(opening, 1.1)
    L.opening = opening
    return opening


def light_spill(light, ang):
    """the light that comes out: a trapezoid on the sill and the porch boards, widening toward the viewer, and a faint
    cone in the air.  Returns (floor_light, air_light) per pixel, 0..1."""
    if light <= 0:
        return np.zeros((H, W)), np.zeros((H, W))
    dl, dr = DOOR_X
    open_frac = np.clip(np.sin(ang), 0, 1)
    # the lit gap's left edge moves with the door edge
    lx = dl + (dr - dl) * np.cos(ang) * 0.0 + (dr - dl) * (1 - open_frac) * 0.85
    lamp = np.array([-0.12, 1.45, -3.2])
    def floor_hit(px):
        # ray from the lamp through a point on the door's bottom edge (x=px, y=0.05, z=0) to the floor y=0, extended
        return px
    zfar = 2.4
    k = (zfar + 3.2) / 3.2
    a = (lx, 0.05, 0.0); b = (dr, 0.05, 0.0)
    c = (lamp[0] + (dr - lamp[0]) * k, 0.0, zfar); d = (lamp[0] + (lx - lamp[0]) * k, 0.0, zfar)
    m = quad([a, b, c, d])
    zf = sdf.ZD + (gy - sdf.Y0) / (sdf.SCALE * np.sin(sdf.PITCH))
    fall = np.clip(1.0 - zf / zfar, 0, 1) ** 0.7
    floor = m * fall * light
    air = burin.blur(m, 12) * 0.25 * light
    return floor, air
