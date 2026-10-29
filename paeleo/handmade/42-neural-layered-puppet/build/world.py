"""SCION 42 · the world: a cut-away stone house at dusk, a deep door reveal with a sill, a plank porch.
Everything here is synthesized with numpy (no found imagery). World units: metres along the porch, threshold region as
in the score; screen mapping X = X0 + x * S.  The person is an authored layered puppet (the rig-only control made
visible): the dog is the only learned thing in the frame.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

Wd, Ht = 1280, 720
S = 190.0            # px per metre
X0 = 310.0           # screen x of world x = 0
FLOOR = 612.0        # screen y where feet touch the boards
WALL_IN, WALL_OUT = 0.35, 0.80     # the door reveal (stone wall thickness), world x
LINTEL = FLOOR - 2.05 * S           # top of the door opening
RNG = np.random.default_rng(7)


def X(x): return X0 + x * S


def fbm(h, w, octaves=5, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        sh = (max(2, h >> (octaves - o)), max(2, w >> (octaves - o)))
        n = r.random(sh).astype(np.float32)
        out += amp * np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255.
        tot += amp; amp *= 0.55
    return out / tot


def lerp(a, b, t): return a + (b - a) * t


def build_static():
    """returns dict of float32 HxWx3 images in 0..1: base (dusk, door shut), lit (interior + spill), and masks"""
    yy, xx = np.mgrid[0:Ht, 0:Wd].astype(np.float32)
    img = np.zeros((Ht, Wd, 3), np.float32)
    # sky
    t = np.clip(yy / 560., 0, 1)[..., None]
    sky = lerp(np.array([0.07, 0.08, 0.17]), np.array([0.36, 0.27, 0.36]), t ** 1.6)
    img[:] = sky
    # far hedge and trees (noise silhouettes)
    n1 = fbm(1, Wd, 6, 3)[0]
    ridge = 470 - 70 * n1 - 40 * fbm(1, Wd, 3, 9)[0]
    img[yy > ridge[None, :]] = np.array([0.06, 0.06, 0.11])
    n2 = fbm(1, Wd, 6, 5)[0]
    ridge2 = 545 - 40 * n2
    img[yy > ridge2[None, :]] = np.array([0.045, 0.045, 0.08])
    # porch boards: top surface 590..640, front face below
    xw = (xx - X0) / S
    porch = (yy >= 588) & (xw >= WALL_OUT - 0.02)
    grain = fbm(Ht, Wd, 5, 11)
    plank = (np.floor((yy - 588) / 13.0)).astype(int)
    board = 0.20 + 0.06 * grain + 0.03 * (plank % 2)
    pc = np.stack([board * 0.75, board * 0.62, board * 0.62], -1)
    gaps = ((yy - 588) % 13.0) < 1.2
    pc[gaps] *= 0.45
    face = yy >= 642
    pc[face] = (np.array([0.07, 0.06, 0.07]) + 0.03 * grain[face][:, None])
    img[porch] = pc[porch]
    # house interior (cut-away room) x < WALL_IN
    room = xw < WALL_IN
    plaster = 0.55 + 0.12 * fbm(Ht, Wd, 6, 21)
    roomc = np.stack([plaster * 0.95, plaster * 0.78, plaster * 0.55], -1)
    # floorboards inside
    fl = yy >= 588
    fb = 0.30 + 0.08 * grain
    roomc[fl] = np.stack([fb * 1.0, fb * 0.72, fb * 0.45], -1)[fl]
    roomc[fl & ((yy - 588) % 11 < 1.0)] *= 0.6
    roomc[(yy >= 572) & (yy < 588)] *= 0.55          # skirting
    # inner doorway to a hall, the deep light source of the room
    hall = (xx > 238) & (xx < 352) & (yy > 300) & (yy < 588)   # the lit inner doorway, the light the dog looks into
    roomc[hall] = np.array([1.0, 0.86, 0.6])
    img_room = roomc
    # wall (stone section) between WALL_IN and WALL_OUT, above the lintel, and the house front above
    wall = (xw >= WALL_IN) & (xw < WALL_OUT) & (yy < LINTEL)
    stone = fbm(Ht, Wd, 6, 31)
    cells = (np.sin(xx * 0.09 + 3 * stone) * np.sin(yy * 0.13 + 2 * stone))
    sc = 0.16 + 0.10 * stone + 0.03 * cells
    stonec = np.stack([sc * 0.95, sc * 0.92, sc * 1.05], -1)
    # sill stone
    sill = (xw >= WALL_IN - 0.02) & (xw < WALL_OUT + 0.03) & (yy >= 598) & (yy < 622)
    sillc = np.stack([0.17 + 0.08 * stone, 0.16 + 0.08 * stone, 0.17 + 0.08 * stone], -1)
    # roof / eave over the porch top-left
    eave = (yy < 120) & (xw < 1.6) & (yy < 120 - (xw - WALL_OUT).clip(0) * 25)
    out = {}
    out['sky_porch'] = img
    out['room'] = img_room
    out['room_mask'] = room.astype(np.float32)
    out['stone'] = stonec; out['wall_mask'] = wall.astype(np.float32)
    out['sill'] = sillc; out['sill_mask'] = sill.astype(np.float32)
    out['eave_mask'] = eave.astype(np.float32)
    # the light that comes out: a fan from the door opening over the boards and the air of the porch
    dx = (xx - X(WALL_OUT)).clip(0)
    fan_y = np.abs(yy - FLOOR) / (40 + dx * 0.35)
    floor_spill = np.exp(-dx / 520.) * np.exp(-fan_y ** 2) * (xw > WALL_OUT - 0.05)
    air = np.exp(-dx / 300.) * np.exp(-((yy - (LINTEL + FLOOR) / 2) / 260.) ** 2) * 0.35 * (xw > WALL_OUT - 0.05)
    out['spill'] = (floor_spill + air).astype(np.float32)
    # the reveal: far jamb of the opening seen through the cut, and the foundation under the house
    rev = (xw >= WALL_IN) & (xw < WALL_OUT) & (yy >= LINTEL) & (yy < 588)
    jc = 0.10 + 0.07 * stone
    out['reveal'] = np.stack([jc * 1.1, jc * 0.95, jc * 0.9], -1); out['reveal_mask'] = rev.astype(np.float32)
    out['reveal_light'] = (0.3 + 0.7 * np.clip((X(WALL_OUT) - xx) / (X(WALL_OUT) - X(WALL_IN)), 0, 1) * 0 + 0.7).astype(np.float32)
    fnd = (xw < WALL_OUT + 0.03) & (yy >= 650)
    out['found'] = np.stack([0.05 + 0.04 * stone] * 3, -1) * np.array([1, 0.95, 1.05]); out['found_mask'] = fnd.astype(np.float32)
    # lamp-light distribution inside the room
    out['room_light'] = (0.45 + 0.55 * np.exp(-((xx - 115) / 380.) ** 2 - ((yy - 420) / 420.) ** 2)).astype(np.float32)
    return out


WARM = np.array([1.0, 0.72, 0.38], np.float32)
DUSK = np.array([0.55, 0.62, 1.0], np.float32)


def background(st, door_open, ajar=0.12):
    """door_open 0..1 (0 = ajar crack). Returns float image."""
    lit = ajar + (1 - ajar) * door_open
    img = st['sky_porch'].copy()
    rm = st['room_mask'][..., None]
    room = st['room'] * st['room_light'][..., None] * (0.16 + 0.84 * lit)
    img = img * (1 - rm) + room * rm
    wm = st['wall_mask'][..., None]
    img = img * (1 - wm) + st['stone'] * wm
    sm = st['sill_mask'][..., None]
    img = img * (1 - sm) + st['sill'] * sm
    rv = st['reveal_mask'][..., None]
    img = img * (1 - rv) + st['reveal'] * (0.5 + 2.2 * lit * WARM) * rv
    fm = st['found_mask'][..., None]
    img = img * (1 - fm) + st['found'] * fm
    em = st['eave_mask'][..., None]
    img = img * (1 - em) + np.array([0.03, 0.03, 0.05]) * em
    # the doorway reveal itself (between WALL_IN and WALL_OUT below the lintel): room light falls into it
    img += st['spill'][..., None] * WARM * 0.85 * lit
    return img


def door_leaf(draw_img, a):
    """the door leaf, hinged at the inner face of the wall, swinging into the room toward the camera.
    a = opening angle in radians (0 shut).  Seen from the side the leaf's visible face width is wd*sin(a)."""
    d = ImageDraw.Draw(draw_img, 'RGBA')
    hx = X(WALL_IN); top = LINTEL + 4; bot = FLOOR - 2
    wd = 0.86 * S
    w = wd * np.sin(a)
    persp = 1 + 0.08 * np.sin(a)          # the free edge is nearer the camera: a little taller
    if w < 3:
        d.rectangle([hx - 3, top, hx + 3, bot], fill=(40, 28, 22, 255)); return
    fx = hx - w
    ft, fb = top - (persp - 1) * 60, bot + (persp - 1) * 30
    poly = [(hx, top), (fx, ft), (fx, fb), (hx, bot)]
    d.polygon(poly, fill=(58, 40, 30, 255))
    # panels
    for (u0, u1, v0, v1) in ((0.15, 0.85, 0.08, 0.45), (0.15, 0.85, 0.55, 0.92)):
        def P(u, v):
            xx = hx + (fx - hx) * u
            yt = top + (ft - top) * u; yb = bot + (fb - bot) * u
            return (xx, yt + (yb - yt) * v)
        d.polygon([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], outline=(30, 20, 15, 255), fill=(66, 46, 34, 255))
    d.line([(fx, ft), (fx, fb)], fill=(150, 110, 70, 255), width=2)


def to_u8(img): return (np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)
