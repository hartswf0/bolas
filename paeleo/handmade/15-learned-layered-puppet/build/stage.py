"""The place: a porch at dusk in an oblique (cabinet) projection, synthesized in numpy/PIL.
World metres: X along the porch (threshold plane X=0, outward +X, the score's x), Y up, Z away from the camera.
The house wall is the plane X=0 seen from the porch side; the door is the opening Z in [-0.46, 0.46], Y in [0, 2.1].
Everything here is drawn or computed (no found material): siding boards, porch boards, door, room, sky, light."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
U0, V0 = 250.0, 560.0
KX, KY, KZ, KZV = 210.0, 210.0, 150.0, 95.0
DOOR_Z = (-0.46, 0.46); DOOR_H = 2.1
rng = np.random.default_rng(15)


def P(X, Y, Z):
    return (U0 + KX * X + KZ * Z, V0 - KY * Y - KZV * Z)


def poly(img, pts, fill):
    ImageDraw.Draw(img).polygon([tuple(map(float, p)) for p in pts], fill=fill)


def mask_of(pts, ss=2):
    m = Image.new('L', (W * ss, H * ss), 0)
    ImageDraw.Draw(m).polygon([(p[0] * ss, p[1] * ss) for p in pts], fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS), np.float32) / 255


def lerp(a, b, t):
    return a + (b - a) * t


def grad_v(c0, c1, y0, y1):
    yy = np.clip((np.arange(H)[:, None] - y0) / (y1 - y0), 0, 1)
    return (np.array(c0) * (1 - yy[..., None]) + np.array(c1) * yy[..., None]) * np.ones((1, W, 1))


def noise(scale, seed, octaves=3):
    r = np.random.default_rng(seed); acc = np.zeros((H, W), np.float32)
    for o in range(octaves):
        s = max(2, int(scale / 2 ** o))
        small = r.random((H // s + 2, W // s + 2)).astype(np.float32)
        acc += np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W + s * 2, H + s * 2), Image.BICUBIC), np.float32)[:H, :W] / 255 / 2 ** o
    return acc / sum(1 / 2 ** o for o in range(octaves))


class Stage:
    def __init__(self):
        self.build()

    def build(self):
        img = grad_v((22, 30, 58), (152, 104, 92), 0, 330).astype(np.float32)      # dusk sky
        sky_glow = np.exp(-((np.arange(W)[None, :] - 1050) ** 2) / 2e5 - ((np.arange(H)[:, None] - 330) ** 2) / 9e3)
        img += sky_glow[..., None] * np.array([70, 40, 10])
        # distant tree line (drawn silhouette with noise edge)
        n1 = noise(40, 3, 4)
        ridge = 250 + 40 * n1[0] + 25 * np.sin(np.arange(W) / 70.0)
        yy = np.arange(H)[:, None]
        trees = (yy > ridge[None, :]).astype(np.float32)
        img = img * (1 - trees[..., None]) + trees[..., None] * np.array([18, 20, 30])
        # yard beyond porch
        img[yy[:, 0] > 330] = img[yy[:, 0] > 330] * 0.5 + np.array([14, 16, 22]) * 0.5
        self.sky = img.copy()
        # moon (a drawn disc)
        mx, my = 1040, 92
        d = np.hypot(np.arange(W)[None, :] - mx, yy - my)
        img += (np.clip(1 - (d - 13) / 1.5, 0, 1)[..., None] * np.array([150, 150, 130]))
        img += (np.exp(-(d / 60) ** 2)[..., None] * np.array([20, 20, 26]))
        # porch floor: X in [0, 4.95], Z in [-0.8, 2.2]
        floor = [P(0, 0, -0.8), P(4.95, 0, -0.8), P(4.95, 0, 2.2), P(0, 0, 2.2)]
        fm = mask_of(floor)
        # boards run along X; plank seams at constant Z
        uu, vv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        Zf = (V0 - vv) / KZV
        Xf = (uu - U0 - KZ * Zf) / KX
        seam = np.abs(((Zf + 0.8) / 0.14) % 1 - 0.5) > 0.46
        grain = noise(18, 5, 3)
        wood = np.array([88, 66, 52]) * (0.75 + 0.35 * grain[..., None]) * (1 - 0.45 * seam[..., None])
        wood *= (0.85 + 0.15 * np.clip(1 - Zf / 2.2, 0, 1))[..., None]
        img = img * (1 - fm[..., None]) + wood * fm[..., None]
        self.Xf, self.Zf, self.floor_mask = Xf, Zf, fm
        # porch front edge (fascia) and steps at the right end
        fascia = [P(0, 0, -0.8), P(4.95, 0, -0.8), P(4.95, -0.35, -0.8), P(-0.5, -0.35, -0.8)]
        m = mask_of(fascia); img = img * (1 - m[..., None]) + m[..., None] * np.array([40, 30, 28])
        for s in range(3):
            x0 = 4.95 + 0.3 * s; y = -0.12 * (s + 1)
            st = [P(x0, y, -0.8), P(x0 + 0.3, y, -0.8), P(x0 + 0.3, y, 1.4), P(x0, y, 1.4)]
            m = mask_of(st); img = img * (1 - m[..., None]) + m[..., None] * np.array([70 - 12 * s, 54 - 10 * s, 44 - 8 * s])
            rs = [P(x0 + 0.3, y, -0.8), P(x0 + 0.3, y - 0.12, -0.8), P(x0 + 0.3, y - 0.12, 1.4), P(x0 + 0.3, y, 1.4)]
            m = mask_of(rs); img = img * (1 - m[..., None]) + m[..., None] * np.array([30, 24, 22])
        # railing along the far edge Z = 2.2
        for xi in np.arange(0.4, 4.9, 0.32):
            post = [P(xi, 0, 2.2), P(xi + 0.05, 0, 2.2), P(xi + 0.05, 0.9, 2.2), P(xi, 0.9, 2.2)]
            m = mask_of(post); img = img * (1 - m[..., None]) + m[..., None] * np.array([34, 28, 30])
        rail = [P(0, 0.9, 2.2), P(4.95, 0.9, 2.2), P(4.95, 0.98, 2.2), P(0, 0.98, 2.2)]
        m = mask_of(rail); img = img * (1 - m[..., None]) + m[..., None] * np.array([42, 34, 34])
        for xi in [0.0, 4.9]:
            post = [P(xi, 0, 2.2), P(xi + 0.1, 0, 2.2), P(xi + 0.1, 2.6, 2.2), P(xi, 2.6, 2.2)]
            m = mask_of(post); img = img * (1 - m[..., None]) + m[..., None] * np.array([30, 24, 26])
        # house wall X=0, Z in [-0.8, 3.5], Y in [0, 3.2]; front face Z=-0.8 for X<0
        wall = [P(0, 0, -0.8), P(0, 0, 3.5), P(0, 3.4, 3.5), P(0, 3.4, -0.8)]
        wm = mask_of(wall)
        Zw = (uu - U0) / KZ; Yw = (V0 - vv - KZV * Zw) / KY
        board = np.abs((Yw / 0.17) % 1 - 0.05) < 0.07
        sid = np.array([62, 66, 78]) * (0.8 + 0.25 * noise(30, 7, 3)[..., None]) * (1 - 0.4 * board[..., None])
        sid *= (0.7 + 0.3 * np.clip(Yw / 3, 0, 1))[..., None]
        img = img * (1 - wm[..., None]) + sid * wm[..., None]
        front = [P(0, 0, -0.8), P(-3, 0, -0.8), P(-3, 3.4, -0.8), P(0, 3.4, -0.8)]
        fm2 = mask_of(front)
        img = img * (1 - fm2[..., None]) + (sid * 0.55) * fm2[..., None]
        self.wall_mask = wm
        # door frame (casing) around the opening
        z0, z1 = DOOR_Z
        self.opening = [P(0, 0, z0), P(0, 0, z1), P(0, DOOR_H, z1), P(0, DOOR_H, z0)]
        casing = [P(0, -0.0, z0 - 0.1), P(0, 0, z1 + 0.1), P(0, DOOR_H + 0.12, z1 + 0.1), P(0, DOOR_H + 0.12, z0 - 0.1)]
        m = mask_of(casing); img = img * (1 - m[..., None]) + m[..., None] * np.array([84, 80, 82])
        self.base = img
        self.om = mask_of(self.opening)
        # sill: a raised board across the opening on the porch side
        sill = [P(0, 0, z0 - 0.08), P(0.14, 0, z0 - 0.08), P(0.14, 0, z1 + 0.08), P(0, 0, z1 + 0.08)]
        self.sill_mask = mask_of(sill)
        sill_face = [P(0.14, 0, z0 - 0.08), P(0.14, 0.05, z0 - 0.08), P(0.14, 0.05, z1 + 0.08), P(0.14, 0, z1 + 0.08)]
        self.sill_face = mask_of(sill_face)
        # interior seen through the door: floor, back wall, a lamp. warm.
        inter = grad_v((120, 84, 50), (200, 140, 80), 100, 560)
        lamp_u, lamp_v = P(-1.5, 0.75, 2.1)
        d = np.hypot(uu - lamp_u, vv - lamp_v)
        inter += np.exp(-(d / 110) ** 2)[..., None] * np.array([110, 90, 50]) + np.exp(-(d / 10) ** 2)[..., None] * np.array([90, 80, 50])
        # interior floor (X<0, Y=0) is darker and redder than the back wall
        Zi = (V0 - vv) / KZV
        inter[(vv > 330) & (uu < 330)] *= 0.82
        # a door frame inside the room (far wall) as a dark rectangle: something to look into
        fr = [P(-2.2, 0, 2.0), P(-2.2, 0, 2.7), P(-2.2, 1.9, 2.7), P(-2.2, 1.9, 2.0)]
        m = mask_of(fr); inter = inter * (1 - 0.35 * m[..., None])
        self.lamp = (lamp_u, lamp_v)
        self.interior = inter
        self.uu, self.vv = uu, vv

    def door_leaf(self, openness):
        """door hinged on the near jamb (Z=z0), swinging into the room; openness 0 ajar (16 deg) .. 1 open (88 deg)."""
        z0, z1 = DOOR_Z; w = z1 - z0
        a = np.radians(16 + 72 * openness)
        hz = z0; ez = hz + w * np.cos(a); ex = -w * np.sin(a)
        pts = [P(0, 0, hz), P(ex, 0, ez), P(ex, DOOR_H, ez), P(0, DOOR_H, hz)]
        return pts, ex, ez

    def frame(self, openness, light):
        """background for a door openness and an interior light level (0..1)."""
        img = self.base.copy()
        om = self.om
        inter = self.interior * (0.6 + 0.55 * light)
        img = img * (1 - om[..., None]) + inter * om[..., None]
        pts, ex, ez = self.door_leaf(openness)
        lm = mask_of(pts) * om
        leaf = np.array([70, 60, 56]) * (0.6 + 0.4 * (1 - openness))
        img = img * (1 - lm[..., None]) + leaf * lm[..., None]
        # gap of light between leaf and near jamb: the visible lit part of the opening
        lit = om * (1 - lm)
        # spill onto the porch: a fan from the opening outwards (+X), brightest near the sill
        Xf, Zf = self.Xf, self.Zf
        z0, z1 = DOOR_Z
        spread = 0.35 + 0.18 * Xf
        open_w = (z1 - z0) * (0.12 + 0.88 * openness)
        zc = z0 + open_w / 2
        fan = np.clip(1 - np.abs(Zf - zc) / (open_w / 2 + spread * np.clip(Xf, 0, None) * 0.6), 0, 1) ** 1.5
        fan *= np.exp(-np.clip(Xf, 0, None) / 2.4) * (Xf > 0) * self.floor_mask
        fan = np.asarray(Image.fromarray((np.clip(fan, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
        warm = np.array([255, 170, 90])
        g = light * (0.15 + 0.85 * openness)
        img = img + fan[..., None] * warm * 0.55 * g
        # sill drawn over the floor and spill
        img = img * (1 - self.sill_mask[..., None]) + self.sill_mask[..., None] * (np.array([96, 74, 58]) + 60 * g)
        img = img * (1 - self.sill_face[..., None]) + self.sill_face[..., None] * np.array([46, 34, 28])
        return img, fan * g, lit
