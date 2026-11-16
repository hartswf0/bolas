"""#43 Collage graph rewriting: HangingThing(gong, hypothesis layer) -> HangingThing(binturong, cue layer).

Handmade: bronze-card gong cut into 12 wedges, twisted cord and knot. Foraged: Brehm/Specht binturong (PD), cut with GrabCut.
Rule replace(gong -> binturong): preconditions t >= release(Q_image); anchor (knot) unchanged; 'hangs' glyph box unchanged.
Graphic bridge: same cord, same knot, the pendulum's phase carries over.
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw
import paper as P

KNOT = (840.0, 70.0)
GONG_R = 68.0
GONG_C = (KNOT[0], KNOT[1] + 18 + GONG_R)
BRONZE = (158, 116, 60)
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/"
S = P.S


def _gong_texture(size):
    """Bronze card: hammered rings and dimples, painted by hand in code (local 2x canvas)."""
    rs = np.random.RandomState(42)
    h = w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    c = size / 2
    r = np.hypot(xx - c, yy - c) / S
    base = np.array(BRONZE, np.float32)
    ring = 0.035 * np.sin(r / 9.0 * 2 * np.pi) * (r > 18) - 0.10 * np.clip((r - 58) / 10, 0, 1) + 0.10 * np.exp(-((r - 18) / 3.0) ** 2)
    sheen = 0.16 * np.clip(1 - np.hypot(xx / S - c / S + 22, yy / S - c / S + 26) / 60, 0, 1)
    ring = ring + sheen
    img = base[None, None] * (1 + ring[..., None])
    # boss
    boss = np.clip(1 - r / 15, 0, 1)
    img = img * (1 + 0.25 * boss[..., None] * (((xx - c) * -0.6 + (yy - c) * -0.8) / (r * S + 1e-3)).clip(-1, 1)[..., None])
    dm = Image.new("L", (w, h), 128)
    d = ImageDraw.Draw(dm)
    for _ in range(260):
        a, rr = rs.uniform(0, 2 * np.pi), rs.uniform(18, GONG_R - 4) * S
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        e = rs.uniform(2.5, 6) * S
        d.ellipse([x - e, y - e * 0.7, x + e, y + e * 0.7], fill=int(128 + rs.uniform(-28, 30)))
    dmf = cv2.GaussianBlur(np.asarray(dm, np.float32) - 128, (0, 0), 2.0)
    img = img * (1 + dmf[..., None] / 400)
    img = img * (1 + 0.03 * P.fibre_field(2, (w, h))[..., None])
    return img


def _dense(pts, step=1.5):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * j / n for j in range(n)]
    return np.array(out)


class Hanging:
    def __init__(self):
        sz = int((GONG_R * 2 + 24) * S)
        self.sz = sz
        tex = _gong_texture(sz)
        c = sz / 2 / S
        self.wedges = []
        for k in range(12):
            a0, a1 = (k / 12) * 2 * np.pi - np.pi / 2, ((k + 1) / 12) * 2 * np.pi - np.pi / 2
            pts = [(c, c)] + [(c + GONG_R * math.cos(a), c + GONG_R * math.sin(a)) for a in np.linspace(a0, a1, 10)]
            pts = P.scissor(_dense(pts), 500 + k, amp=0.45, snip=4.5)
            a = P.mask_of(pts, (sz, sz))
            pc = P.piece(pts, BRONZE, 500 + k, rim=0.22, model=0.05, fibre=0.0, size=(sz, sz))
            rgb = tex * 0.85 + pc[..., :3] * 0.15
            # lit cut edges from the piece render
            edge = pc[..., :3] - P.piece(pts, BRONZE, 500 + k, rim=0.0, model=0.05, fibre=0.0, size=(sz, sz))[..., :3]
            rgb = rgb + edge
            mid = (a0 + a1) / 2
            self.wedges.append(dict(img=np.dstack([np.clip(rgb, 0, 255), a]), mid=mid))
        # hole at the top rim where the cord loop goes through
        for wd in self.wedges[:1] + self.wedges[-1:]:
            hx, hy = int(c * S), int((c - GONG_R + 7) * S)
            cv2.circle(wd["img"], (hx, hy), int(3.2 * S), (0, 0, 0, 0), -1)
        an = np.array(Image.open(SRC + "binturong_hang.png").convert("RGBA"), np.float32)
        info = __import__("json").load(open(SRC + "binturong_hang.json"))
        target_h = 240.0
        sc = target_h * S / an.shape[0]
        an = cv2.resize(an, (int(an.shape[1] * sc), int(an.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        an[..., 3] /= 255.0
        self.animal = an
        self.tail = (info["tail_tip"][0] * sc, info["tail_tip"][1] * sc)   # 2x px inside the sprite
        rs = np.random.RandomState(7)
        self.fall = [dict(vx=rs.uniform(30, 70) * math.cos(w["mid"]) + rs.uniform(-25, 25),
                          vy=rs.uniform(-60, -10) + 40 * math.sin(w["mid"]), w=rs.choice([-1, 1]) * rs.uniform(140, 420))
                     for w in self.wedges]
        # release order: bottom wedges first (the animal's weight tears the paper from below)
        self.order = sorted(range(12), key=lambda k: -math.sin(self.wedges[k]["mid"]))

    # -------------------------------------------------------------------------------------------
    def _paste(self, canvas, sprite, cx, cy, ang=0.0, alpha=1.0, shadow=0.22, pivot=None):
        """Paste float RGBA sprite with its centre (or pivot, sprite px) at (cx,cy) film px, rotated (deg, clockwise)."""
        h, w = sprite.shape[:2]
        pv = pivot if pivot is not None else (w / 2, h / 2)
        M = cv2.getRotationMatrix2D(pv, -ang, 1.0)
        M[0, 2] += cx * S - pv[0]
        M[1, 2] += cy * S - pv[1]
        lay = cv2.warpAffine(sprite, M, (P.CW, P.CH), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        if shadow:
            P.shadow(canvas, lay[..., 3], dx=2.0, dy=3.0, blur=2.5, strength=shadow)
        P.over(canvas, lay, alpha)

    def cord(self, canvas, theta, tail=False):
        im = Image.new("RGBA", (P.CW, P.CH), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        kx, ky = KNOT[0] * S, KNOT[1] * S
        # twisted two-ply cord from above the frame to the knot
        for ply, col in ((0, (104, 76, 52, 255)), (1, (146, 110, 74, 255))):
            pts = [(kx + 1.6 * S * math.sin(y / (5.0 * S) + ply * math.pi), y) for y in np.arange(-10, ky, 2)]
            d.line(pts, fill=col, width=int(1.6 * S))
        if not tail:
            # short loop through the gong's hole, following the swing
            a = math.radians(theta)
            hx, hy = kx - math.sin(a) * 11 * S, ky + math.cos(a) * 11 * S
            d.line([(kx - 2 * S, ky), (hx - 2 * S, hy), (hx + 2 * S, hy), (kx + 2 * S, ky)], fill=(120, 88, 60, 255), width=int(1.4 * S))
        # knot: lumpy wrapped cord
        rs = np.random.RandomState(3)
        for k in range(9):
            ox, oy = rs.uniform(-4, 4) * S, rs.uniform(-3, 4) * S
            r = rs.uniform(2.4, 3.6) * S
            col = (118 + int(rs.uniform(-12, 22)), 86 + int(rs.uniform(-8, 18)), 58, 255)
            d.ellipse([kx + ox - r, ky + oy - r * 0.8, kx + ox + r, ky + oy + r * 0.8], fill=col)
        lay = np.asarray(im, np.float32).copy()
        lay[..., 3] /= 255.0
        # lit edge on the cord (light from left)
        P.shadow(canvas, lay[..., 3], dx=1.5, dy=2.0, blur=1.5, strength=0.2)
        P.over(canvas, lay)

    def render(self, canvas, film_t, t_image=38.0, theta=0.0):
        """Draw the hanging layer at film time film_t. theta: pendulum angle (deg) about the knot."""
        a = math.radians(theta)
        if film_t >= t_image:
            # cue plane: the binturong, tail tip pinned at the knot (rotation about the knot only)
            self._paste(canvas, self.animal, KNOT[0], KNOT[1] - 2, ang=theta, pivot=self.tail, shadow=0.18)
        # hypothesis plane: wedges (in front of the animal)
        rel = film_t - (t_image + 2 / 24)
        for rank, k in enumerate(self.order):
            wd = self.wedges[k]
            t_rel = rel - rank * 3 / 24
            gx = KNOT[0] + math.sin(a) * (18 + GONG_R) * -1
            gy = KNOT[1] + math.cos(a) * (18 + GONG_R)
            if film_t < t_image or t_rel < 0:
                self._paste(canvas, wd["img"], gx, gy, ang=theta, shadow=0.16)
            else:
                f = self.fall[k]
                x = gx + f["vx"] * t_rel
                y = gy + f["vy"] * t_rel + 0.5 * 1900 * t_rel ** 2
                if y > 640:
                    continue
                self._paste(canvas, wd["img"], x, y, ang=theta + f["w"] * t_rel, shadow=0.16)
        self.cord(canvas, theta, tail=film_t >= t_image + 2 / 24 + 11 * 3 / 24)
        return canvas

    def gone(self, film_t, t_image=38.0):
        """Event times for the mix: wedge release ticks (film time)."""
        return [t_image + 2 / 24 + r * 3 / 24 for r in range(12)]
