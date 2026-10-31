"""Composite integrator, part 1: the room. Plates are corner-pinned onto world quads seen by camera.py, graded to one
dusk (exterior) and one lamp (interior), and the door light is a computed pass shared by the floor, the dog and the person.
Exposes: Set.static (pre-composited far layers), Set.frame(t) -> (rgb, mattes{facade, sill, opening}), light maps."""
import os, json
import numpy as np
from PIL import Image
from comp import W, H, load, homography, warp, Comp, grade, poly_matte, apply, soften
import camera as cam

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'cache', 'plates')
PL = json.load(open(os.path.join(P, 'plates.json')))

DOOR_X = (-0.46, 0.46); DOOR_H = 2.05; WALL_T = 0.16
SILL_H = 0.13   # round 2: a raised threshold board, tall enough that its edge visibly hides the dog's forelegs inside
LAMP = np.array([-0.95, 1.95, -1.5])
DUSK = (0.50, 0.58, 0.80)      # exterior ambient tint
WARM = np.array([1.0, 0.72, 0.40], np.float32)   # lamp colour


def plate(name, alpha=False):
    rgb = load(os.path.join(P, name + '.jpg'))
    a = np.asarray(Image.open(os.path.join(P, name + '_a.jpg')).convert('L'), np.float32) / 255 if alpha else np.ones(rgb.shape[:2], np.float32)
    return rgb, a


def pin(rgb, a, world4, src4=None):
    """Corner pin: source corners (default the plate's own corners) -> projected world quad."""
    h, w = a.shape
    src4 = src4 if src4 is not None else [(0, 0), (w, 0), (w, h), (0, h)]
    dst4, z = cam.project(world4)
    assert (z > 0).all()
    return warp(rgb, a, homography(src4, dst4)), dst4


def tile(rgb, nx, ny):
    rows = []
    for j in range(ny):
        row = [rgb[:, ::-1] if (i + j) % 2 else rgb for i in range(nx)]
        rows.append(np.concatenate(row, 1))
    return np.concatenate(rows, 0)


def door_angle(t):
    """degrees the leaf has swung in: ajar until 6.2 s, then opens (score: door 'open' at 6.2)."""
    u = np.clip((t - 6.2) / 0.55, 0, 1); u = u * u * (3 - 2 * u)
    return 24 + (98 - 24) * u


def lamp_level(t):
    return 0.55 + 0.45 * np.clip((t - 6.2) / 0.5, 0, 1)


def aperture(t):
    """X range on the facade plane through which the lamp shines (the leaf shades the hinge side)."""
    ph = np.radians(door_angle(t))
    E = np.array([DOOR_X[0] + 0.9 * np.cos(ph), 0, -0.9 * np.sin(ph)])
    xe = LAMP[0] + (E[0] - LAMP[0]) * (-LAMP[2]) / (E[2] - LAMP[2])
    return max(DOOR_X[0], xe), DOOR_X[1]


def light_at(Pw, t):
    """Door light reaching world points outside the house (N,3) -> intensity (N,). Same model for floor, dog, person."""
    x0, x1 = aperture(t)
    d = Pw - LAMP
    s = (-LAMP[2]) / np.where(np.abs(d[:, 2]) < 1e-6, 1e-6, d[:, 2])
    Q = LAMP + d * s[:, None]
    soft = 0.05
    inx = np.clip((Q[:, 0] - x0) / soft + .5, 0, 1) * np.clip((x1 - Q[:, 0]) / soft + .5, 0, 1)
    iny = np.clip((DOOR_H - Q[:, 1]) / soft + .5, 0, 1) * np.clip((Q[:, 1] - SILL_H) / 0.03 + .5, 0, 1)
    dist = np.linalg.norm(d, axis=1)
    out = (Pw[:, 2] > 0) * inx * iny * (5.0 / (dist ** 2 + 0.6))
    return out * lamp_level(t)


class Set:
    def __init__(self):
        self.ppm = cam.px_per_m_on_path()
        # far, static layers: sky, interior room, interior floor
        sky = np.zeros((H, W, 3), np.float32)
        g = np.linspace(0, 1, H)[:, None]
        sky[:] = (np.array([0.10, 0.12, 0.22]) * (1 - g) + np.array([0.20, 0.17, 0.24]) * g)[:, None, :] if False else 0
        top = np.array([0.08, 0.10, 0.20], np.float32); bot = np.array([0.30, 0.24, 0.30], np.float32)
        sky[:] = top * (1 - g[..., None]) + bot * g[..., None]
        self.sky = sky
        room, ra = plate('room')
        room = grade(room, gain=1.0, tint=WARM * 1.15, sat=.8)
        self.room_piece, _ = pin(room, ra, [[-1.6, 2.6, -2.7], [2.4, 2.6, -2.7], [2.4, 0, -2.7], [-1.6, 0, -2.7]],
                                 [(0, 0), (384, 0), (384, 288), (0, 288)])
        wall, wa = plate('wall')
        self.side_piece, _ = pin(grade(wall, tint=WARM * 0.9, sat=.6), wa,
                                 [[1.5, 2.6, -0.2], [1.5, 2.6, -2.7], [1.5, 0, -2.7], [1.5, 0, -0.2]])
        fw, fa = plate('floorwood')
        fwl = np.asarray(Image.fromarray((fw * 255).astype(np.uint8)).resize((320, 320), Image.BICUBIC), np.float32) / 255
        self.ifloor_piece, _ = pin(grade(fwl, gain=.8, tint=WARM * .7), np.ones((320, 320), np.float32),   # planks run into the room
                                   [[-1.6, 0, -2.7], [1.5, 0, -2.7], [1.5, 0, -0.0], [-1.6, 0, -0.0]])
        # exterior porch floor: tiled path plate, corner-pinned, graded to dusk
        ft, _ = plate('flags')
        self.floor_rgb = grade(ft, gain=.6, tint=DUSK, sat=.3)
        self.floor_piece, self.floor_quad = pin(self.floor_rgb, np.ones(ft.shape[:2], np.float32),
                                                [[-2.0, 0, 0], [10.0, 0, 0], [10.0, 0, 4.0], [-2.0, 0, 4.0]])
        # the facade: stone wall with the doorway cut by a holdout (the opening matte)
        sw, _ = plate('stonewall')
        self.wall_rgb = grade(sw, gain=.55, tint=DUSK, sat=.35)
        self.facade_piece, _ = pin(self.wall_rgb, np.ones(sw.shape[:2], np.float32),
                                   [[-2.3, 3.4, 0], [10.0, 3.4, 0], [10.0, 0, 0], [-2.3, 0, 0]])
        op, _ = cam.project([[DOOR_X[0], 0, 0], [DOOR_X[1], 0, 0], [DOOR_X[1], DOOR_H, 0], [DOOR_X[0], DOOR_H, 0]])
        self.opening = poly_matte([op.tolist()], (W, H))
        # the reveal: the far jamb's inner face (visible from this side), and lintel underside
        rv = [[DOOR_X[1], 0, 0], [DOOR_X[1], 0, -WALL_T], [DOOR_X[1], DOOR_H, -WALL_T], [DOOR_X[1], DOOR_H, 0]]
        self.reveal = cam.project(rv)[0]
        # casing: painted trim around the opening (Z slightly proud), from the white wall plate
        trim = grade(wall, gain=.9, tint=DUSK, sat=.2)
        cw = 0.09
        quads = [[[DOOR_X[0] - cw, DOOR_H + cw, .02], [DOOR_X[0], DOOR_H + cw, .02], [DOOR_X[0], 0, .02], [DOOR_X[0] - cw, 0, .02]],
                 [[DOOR_X[1], DOOR_H + cw, .02], [DOOR_X[1] + cw, DOOR_H + cw, .02], [DOOR_X[1] + cw, 0, .02], [DOOR_X[1], 0, .02]],
                 [[DOOR_X[0] - cw, DOOR_H + cw, .02], [DOOR_X[1] + cw, DOOR_H + cw, .02], [DOOR_X[1] + cw, DOOR_H, .02], [DOOR_X[0] - cw, DOOR_H, .02]]]
        self.casing = [pin(trim, np.ones(trim.shape[:2], np.float32), q)[0] for q in quads]
        # the sill: a wooden board across the threshold, top face + front face
        fwg = grade(soften(fw, 1.5), gain=.62, tint=DUSK, sat=.4)   # softened: the plank joints made a dashed line
        self.sill_top, st = pin(fwg, np.ones(fw.shape[:2], np.float32),
                                [[DOOR_X[0] - .05, SILL_H, -WALL_T], [DOOR_X[1] + .05, SILL_H, -WALL_T], [DOOR_X[1] + .05, SILL_H, .07], [DOOR_X[0] - .05, SILL_H, .07]])
        self.sill_front, sf = pin(grade(soften(fw, 1.5), gain=.32, tint=DUSK, sat=.4), np.ones(fw.shape[:2], np.float32),
                                  [[DOOR_X[0] - .05, SILL_H, .07], [DOOR_X[1] + .05, SILL_H, .07], [DOOR_X[1] + .05, 0, .07], [DOOR_X[0] - .05, 0, .07]])
        self.sill_matte = np.maximum(poly_matte([st.tolist()], (W, H)), poly_matte([sf.tolist()], (W, H)))
        lf, la = plate('door_leaf', alpha=True)
        self.leaf = (grade(lf, gain=.85, sat=.6), la, PL['door_leaf']['quad'])
        # floor light: world point per screen pixel on the porch floor (quarter res)
        ys, xs = np.mgrid[0:H:4, 0:W:4] + 2.0
        Pw, tt = cam.unproject_to_plane(xs.ravel(), ys.ravel(), np.array([0, 1, 0]), 0.0)
        self.floor_P = Pw; self.floor_ok = (tt > 0) & (Pw[:, 2] > 0.0)
        # path plane (the dog's and person's cards): plane through the path, normal = view direction (horizontal)
        n = cam.V
        Pp, _ = cam.unproject_to_plane(xs.ravel(), ys.ravel(), n, 0.0)
        self.card_P = Pp
        self.qshape = ys.shape

    def up(self, a):
        im = Image.fromarray(a.astype(np.float32), 'F').resize((W, H), Image.BILINEAR)
        return np.asarray(im, np.float32)

    def light_maps(self, t):
        fl = light_at(self.floor_P, t) * self.floor_ok
        cd = light_at(self.card_P, t)
        # inside the house (behind the facade plane), the lamp lights the card directly
        inside = self.card_P[:, 2] < 0
        d = np.linalg.norm(self.card_P - LAMP, axis=1)
        cd = np.where(inside, lamp_level(t) * 5.0 / (d ** 2 + 0.6), cd)   # same law both sides: no seam at the sill
        return self.up(fl.reshape(self.qshape)), self.up(cd.reshape(self.qshape))

    def back(self, t, inside_layers=()):
        """Everything behind the facade plane plus the facade itself; returns comp and the mattes for holdouts."""
        c = Comp(self.sky)
        lv = lamp_level(t)
        for pc in (self.room_piece, self.side_piece, self.ifloor_piece):
            x0, y0, rgb, a = pc
            c.over((x0, y0, rgb * lv, a))
        # the leaf, corner-pinned to its swing
        ph = np.radians(door_angle(t))
        hx, fx, fz = DOOR_X[0], DOOR_X[0] + 0.92 * np.cos(ph), -0.92 * np.sin(ph)
        lrgb, la, q = self.leaf
        piece, _ = pin(lrgb * (0.35 + 0.5 * lv), la, [[hx, DOOR_H, 0], [fx, DOOR_H, fz], [fx, 0, fz], [hx, 0, 0]], q)
        c.over(piece)
        for fn in inside_layers:
            fn(c)
        return c

    def front(self, c, t, floor_light):
        """The facade (with the opening held out), casing, sill and the porch floor with the door light."""
        x0, y0, rgb, a = self.facade_piece
        hole = 1 - self.opening[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
        c.over((x0, y0, rgb * hole[..., None], a * hole), name='facade')
        # reveal (far jamb inner face), lit by the lamp
        rv = poly_matte([self.reveal.tolist()], (W, H))
        col = np.array([.55, .42, .30], np.float32) * lamp_level(t)
        c.rgb = c.rgb * (1 - rv[..., None]) + col * rv[..., None]
        for pc in self.casing:
            c.over(pc, name='facade')
        x0, y0, rgb, a = self.floor_piece
        L = floor_light[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
        lit = rgb * (1 + 4.0 * L[..., None] * WARM)
        c.over((x0, y0, lit, a), name='floor')
        for pc in (self.sill_top, self.sill_front):
            x0, y0, rgb, a = pc
            L = floor_light[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] + .15 * lamp_level(t)
            c.over((x0, y0, rgb * (1 + 2.0 * L[..., None] * WARM), a), name='sill')
        return c
