"""The place, engraved in screen space: a cutaway of the house wall at the door, the porch, the dusk beyond.

Static ink is computed once per camera set-up; light is computed per frame as a colour map that multiplies the paper:
dusk (blue, darkening), the room's lamp (warm), and the beam that comes out through the doorway as the door opens.
The dog and the person are lit by the same map, so they warm when they enter the beam.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, DOOR_X, ASSETS, smoothstep

SS = 2
PAPER = np.array([0.95, 0.92, 0.84], np.float32)
INKC = np.array([0.07, 0.06, 0.07], np.float32)
DOOR_H = 2.05      # m
WALL_T = 0.16      # m, the wall's thickness at the cut


class Canvas:
    def __init__(self):
        self.w, self.h = W * SS, H * SS
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.X, self.Y = xx, yy
        self.ink = np.zeros((self.h, self.w), np.float32)

    def mask(self, polys=(), ellipses=(), lines=(), width=1):
        im = Image.new('L', (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        for p in polys:
            d.polygon([(x * SS, y * SS) for x, y in p], fill=255)
        for (cx, cy, rx, ry) in ellipses:
            d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=255)
        for l in lines:
            d.line([(x * SS, y * SS) for x, y in l], fill=255, width=int(width * SS))
        return np.asarray(im).astype(np.float32) / 255

    def hatch(self, m, angle, spacing, tone, cross=None):
        """Ink lines inside mask m; tone (scalar or map, 0..1) sets line width."""
        s = spacing * SS * 1.45
        n = (-np.sin(angle), np.cos(angle))
        phi = self.X * n[0] + self.Y * n[1]
        d = np.abs((phi / s) % 1 - 0.5) * s
        wid = (0.08 + 0.8 * np.clip(tone, 0, 1)) * s
        ink = 1 - np.clip((s / 2 - d) - wid / 2 + 0.5, 0, 1)
        if cross is not None:
            a2 = angle + cross
            phi2 = self.X * -np.sin(a2) + self.Y * np.cos(a2)
            d2 = np.abs((phi2 / s) % 1 - 0.5) * s
            t2 = np.clip((np.asarray(tone) - 0.55) / 0.45, 0, 1)
            ink2 = (1 - np.clip((s / 2 - d2) - t2 * 0.45 * s + 0.5, 0, 1)) * (t2 > 0)
            ink = np.maximum(ink, ink2)
        self.ink = self.ink * (1 - m) + ink * m
        return ink

    def solid(self, m, val=1.0):
        self.ink = self.ink * (1 - m) + val * m

    def outline(self, polys, width=1.2):
        m = self.mask(lines=[list(p) + [p[0]] for p in polys], width=width)
        self.ink = np.maximum(self.ink, m)

    def down(self, a):
        return a.reshape(H, SS, W, SS).mean((1, 3))


def qd_strokes(key):
    for l in open(os.path.join(ASSETS, 'quickdraw_used.ndjson')):
        d = json.loads(l)
        if d['key_id'] == key:
            return d['drawing']
    return []


class World:
    def __init__(self, cam):
        self.cam = cam
        s, dx, fy = cam['s'], cam['door_px'], cam['floor_px']
        self.s, self.dx, self.fy = s, dx, fy
        X = lambda m: dx + s * m           # metres from the door plane -> px
        Y = lambda m: fy - s * m
        self.X, self.Y = X, Y
        c = Canvas()
        wall_in = X(-WALL_T)                # inner face of the wall
        top = Y(DOOR_H)
        # --- sky and yard (outside, behind the porch)
        sky = c.mask(polys=[[(X(0), 0), (W, 0), (W, Y(0.95)), (X(0), Y(0.95))]])
        grad = np.clip((c.Y / SS) / (Y(0.95)), 0, 1)
        c.hatch(sky, 0.0, 4.2, 0.55 - 0.35 * grad)
        # moon and trees from Quick, Draw! (stroked as engraved chalk lines)
        self._qd(c, '5431885159202816', X(3.05), Y(2.15), 0.26 * s / 205, 2.0)
        self._qd(c, '4593716037681152', X(1.55), Y(2.1), 0.75 * s / 205, 2.2)
        self._qd(c, '6718527320883200', X(3.7), Y(1.95), 0.6 * s / 205, 2.2)
        # porch roof (eave) along the top
        roof = c.mask(polys=[[(X(0), 0), (W, 0), (W, Y(2.5)), (X(0), Y(2.62))]])
        c.hatch(roof, -0.05, 3.2, 0.85, cross=1.2)
        # far railing: top rail, bottom rail and balusters; posts
        rail = c.mask(polys=[[(X(0.05), Y(0.95)), (W, Y(0.95)), (W, Y(0.88)), (X(0.05), Y(0.88))],
                             [(X(0.05), Y(0.16)), (W, Y(0.16)), (W, Y(0.11)), (X(0.05), Y(0.11))]])
        c.hatch(rail, 0.0, 3.0, 0.55)
        bal = []
        x = 0.25
        while X(x) < W + 10:
            bal.append([(X(x), Y(0.88)), (X(x) + 0.035 * s, Y(0.88)), (X(x) + 0.035 * s, Y(0.16)), (X(x), Y(0.16))])
            x += 0.16
        c.hatch(c.mask(polys=bal), 1.57, 2.6, 0.45)
        posts = [[(X(px), Y(2.6)), (X(px) + 0.11 * s, Y(2.6)), (X(px) + 0.11 * s, Y(0.0)), (X(px), Y(0.0))] for px in (1.30, 4.40)]
        c.hatch(c.mask(polys=posts), 1.57, 3.0, 0.62, cross=1.4)
        c.outline(posts, 1.0)
        # porch floor (the boards seen a little from above) and the porch's front edge
        floor = c.mask(polys=[[(X(0), Y(0)), (W, Y(0)), (W, Y(-0.2)), (X(0), Y(-0.2))]])
        c.hatch(floor, 0.0, 3.4, 0.35 + 0.4 * np.clip((c.Y / SS - Y(0)) / (0.2 * s), 0, 1))
        boards = []
        for k in range(1, 4):
            yb = Y(0) + k * 0.05 * s
            boards.append([(X(0), yb), (W, yb)])
        c.ink = np.maximum(c.ink, c.mask(lines=boards, width=1.0) * 0.9)
        front = c.mask(polys=[[(0, Y(-0.2)), (W, Y(-0.2)), (W, H), (0, H)]])
        c.hatch(front, 0.0, 3.0, 0.9, cross=1.0)
        # steps at the porch end (x = 4.9 in the score's metres)
        se = X(4.9 - DOOR_X)
        if se < W:
            st = c.mask(polys=[[(se, Y(0)), (W, Y(0)), (W, H), (se, H)]])
            c.hatch(st, 0.0, 2.6, 0.95, cross=1.57)
        # --- inside: back wall, floor, ceiling shadow, skirting, a picture, the lamp, the stool
        inside = c.mask(polys=[[(0, Y(DOOR_H + 0.6)), (wall_in, Y(DOOR_H + 0.6)), (wall_in, Y(0)), (0, Y(0))]])
        vgrad = np.clip((c.Y / SS - Y(DOOR_H + 0.6)) / (Y(0) - Y(DOOR_H + 0.6)), 0, 1)
        c.hatch(inside, 1.57, 4.0, 0.3 + 0.25 * vgrad)
        ifloor = c.mask(polys=[[(0, Y(0)), (X(0), Y(0)), (X(0), Y(-0.2)), (0, Y(-0.2))]])
        c.hatch(ifloor, 0.0, 3.0, 0.45)
        c.ink = np.maximum(c.ink, c.mask(lines=[[(0, Y(0.12)), (wall_in, Y(0.12))]], width=1.4))
        pic = [(X(-1.05), Y(1.75)), (X(-0.62), Y(1.75)), (X(-0.62), Y(1.42)), (X(-1.05), Y(1.42))]
        c.hatch(c.mask(polys=[pic]), 0.8, 2.6, 0.6, cross=1.4)
        c.outline([pic], 1.6)
        lamp = (X(-0.42), Y(1.62))
        self.lamp = lamp
        shade = [(lamp[0] - 0.09 * s, lamp[1] + 0.02 * s), (lamp[0] + 0.09 * s, lamp[1] + 0.02 * s),
                 (lamp[0] + 0.05 * s, lamp[1] - 0.12 * s), (lamp[0] - 0.05 * s, lamp[1] - 0.12 * s)]
        c.solid(c.mask(polys=[shade]), 0.0)
        c.hatch(c.mask(polys=[shade]), 1.57, 2.0, 0.12)
        c.outline([shade], 1.2)
        arm = [(lamp[0] - 0.01 * s, lamp[1] + 0.02 * s), (lamp[0] + 0.01 * s, lamp[1] + 0.02 * s),
               (wall_in - 0.02 * s, lamp[1] + 0.15 * s), (wall_in - 0.04 * s, lamp[1] + 0.15 * s)]
        stool_x = X(-1.30)
        self.stool_x = stool_x
        stool = [[(stool_x - 0.2 * s, Y(0.45)), (stool_x + 0.2 * s, Y(0.45)), (stool_x + 0.2 * s, Y(0.40)), (stool_x - 0.2 * s, Y(0.40))],
                 [(stool_x - 0.18 * s, Y(0.40)), (stool_x - 0.14 * s, Y(0.40)), (stool_x - 0.16 * s, Y(0)), (stool_x - 0.2 * s, Y(0))],
                 [(stool_x + 0.14 * s, Y(0.40)), (stool_x + 0.18 * s, Y(0.40)), (stool_x + 0.2 * s, Y(0)), (stool_x + 0.16 * s, Y(0))]]
        c.hatch(c.mask(polys=stool), 0.0, 2.4, 0.7)
        c.outline(stool, 1.0)
        # --- the wall, cut: section above the door and the far jamb; the sill
        sect = c.mask(polys=[[(wall_in, 0), (X(0), 0), (X(0), top), (wall_in, top)]])
        c.solid(sect, 0.92)
        c.hatch(sect, 0.785, 5.0, 0.0)
        c.outline([[(wall_in, -5), (X(0), -5), (X(0), top), (wall_in, top)]], 1.6)
        jamb = c.mask(polys=[[(wall_in, top), (wall_in + 0.05 * s, top), (wall_in + 0.05 * s, Y(0)), (wall_in, Y(0))],
                             [(X(0) - 0.05 * s, top), (X(0), top), (X(0), Y(0)), (X(0) - 0.05 * s, Y(0))]])
        c.hatch(jamb, 1.57, 2.4, 0.65)
        self.sill = [(wall_in - 0.03 * s, Y(0.035)), (X(0) + 0.05 * s, Y(0.035)), (X(0) + 0.05 * s, Y(0)), (wall_in - 0.03 * s, Y(0))]
        sl = c.mask(polys=[self.sill])
        c.hatch(sl, 0.0, 2.0, 0.55)
        self.sill_ink = c.down(c.ink * sl)
        self.sill_a = c.down(sl)
        self.ink = c.down(c.ink)
        self.c = c
        self.inside = c.down(c.mask(polys=[[(0, 0), (X(0), 0), (X(0), H), (0, H)]]))
        self.wall_in, self.top = wall_in, top
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.xx, self.yy = xx, yy
        # lamp glow
        dl = np.sqrt((xx - lamp[0]) ** 2 + ((yy - lamp[1]) * 0.8) ** 2) / s
        self.lampglow = np.clip(1.0 / (1 + (dl / 0.9) ** 2), 0, 1) * (xx < X(0))
        self.leaf_cache = {}

    def _qd(self, c, key, cx, cy, sc, width):
        strokes = qd_strokes(key)
        lines = []
        for xs, ys in strokes:
            lines.append([(cx + (x - 128) * sc, cy + (y - 128) * sc) for x, y in zip(xs, ys)])
        if lines:
            m = c.mask(lines=lines, width=width)
            c.ink = c.ink * (1 - m) + 0.06 * m        # chalk: pale lines on the dark sky

    def leaf(self, open_amt):
        """The door leaf: hinged on the far jamb, swung into the room; seen as a panel widening to the left."""
        key = round(open_amt, 3)
        if key in self.leaf_cache:
            return self.leaf_cache[key]
        s = self.s
        ang = 0.20 + (1.35 - 0.20) * open_amt
        wpx = 0.86 * s * np.sin(ang)
        x0 = self.wall_in + 0.04 * s
        poly = [(x0 - wpx, self.top + 0.03 * s), (x0, self.top + 0.01 * s), (x0, self.Y(0.01)), (x0 - wpx, self.Y(0.02))]
        c = Canvas()
        m = c.mask(polys=[poly])
        c.hatch(m, 1.57, 2.6, 0.5)
        panel = [(x0 - wpx * 0.85, self.top + 0.15 * s), (x0 - wpx * 0.15, self.top + 0.15 * s),
                 (x0 - wpx * 0.15, self.Y(1.1)), (x0 - wpx * 0.85, self.Y(1.1))]
        c.outline([poly, panel], 1.2)
        out = (c.down(c.ink * m + 0 * m), c.down(m))
        self.leaf_cache[key] = out
        return out

    def light(self, t, door_open, ajar=0.12):
        """RGB light map for time t; door_open 0..1 (0 = ajar)."""
        s = self.s
        dusk = 1.0 - 0.28 * smoothstep(0, 32, t)
        L = np.empty((H, W, 3), np.float32)
        out_col = np.array([0.30, 0.36, 0.56], np.float32) * dusk
        fig_col = np.array([0.74, 0.78, 0.94], np.float32) * (0.75 + 0.25 * dusk)
        in_col = np.array([1.0, 0.80, 0.52], np.float32)
        L[:] = out_col
        ins = self.inside[..., None]
        room = 0.30 + 0.75 * self.lampglow[..., None]
        L = L * (1 - ins) + (in_col * room) * ins
        # beam through the doorway: on the boards (a widening strip), and in the low air (lights the figures)
        amt = ajar + (1 - ajar) * door_open
        xd = self.X(0)
        dx = (self.xx - xd) / s
        top_y = self.top + (self.Y(0) - self.top) * np.clip(dx / 2.4, 0, 1)
        inbeam = (self.xx >= xd - 2) & (self.yy >= top_y)
        fall = np.clip(1 - dx / (0.9 + 2.8 * amt), 0, 1) ** 1.2
        air = inbeam * fall * amt * np.clip((self.yy - top_y) / (0.3 * s), 0, 1)
        onfloor = (self.yy >= self.Y(0) - 1) & (self.yy <= self.Y(-0.2)) & (self.xx >= xd - 2)
        floor_b = onfloor * fall * amt
        warm = (in_col * 0.95 - out_col * 0.6)[None, None, :]
        Lf = fig_col[None, None, :] * (1 - ins) + (in_col * (0.55 + 0.6 * self.lampglow[..., None])) * ins
        Lobj = Lf + (in_col * 1.0 - fig_col * 0.75)[None, None, :] * air[..., None]
        L = L + warm * (1.15 * floor_b + 0.32 * air * (self.yy > self.Y(1.0)))[..., None]
        self.beam = air
        self.Lobj = np.clip(Lobj, 0, 1.25)
        return np.clip(L, 0, 1.25)

    def compose(self, t, door_open, layers_pm):
        """Background RGB with the light; layers_pm: premultiplied RGBA layers drawn on top, each with a flag
        whether it is lit by the map. Returns the frame (float RGB)."""
        L = self.light(t, door_open)
        ink = self.ink.copy()
        lk, lm = self.leaf(door_open)
        ink = ink * (1 - lm) + lk * lm
        rgb = PAPER[None, None, :] * L * (1 - ink[..., None]) + INKC * ink[..., None]
        for pm, lit in layers_pm:
            col = pm[..., :3] * self.Lobj if lit else pm[..., :3]
            rgb = rgb * (1 - pm[..., 3:4]) + col
        return rgb, L
