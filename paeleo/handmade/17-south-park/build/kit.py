"""SCION 17 // shape kit v1: the restricted cut-out grammar every figure and set piece is cut from.

Units: character pieces are in centimetres in the figure's own frame (y up, origin on the ground under the body centre).
A piece is a closed polygon with one paper colour, a z order and a tag. Nothing is bent or squashed: a piece can be
translated, rotated about its pivot, mirrored as a whole figure (a complete profile drawing seen from the other side),
or replaced by another drawing (substitution). Every cut has a fixed seed, so the same piece is the same piece in every
frame: the recurring-asset invariant is structural.
"""
import hashlib, math
import numpy as np

VERSION = 'kit-v1'

# ---------------------------------------------------------------- paper palette (construction paper under dusk)
PAPER = {
    'ink': (27, 22, 34),
    'dog': (205, 146, 79), 'dog_far': (163, 112, 58), 'dog_saddle': (128, 80, 44), 'dog_cream': (240, 226, 196),
    'dog_ear': (104, 62, 36), 'dog_ear_far': (80, 47, 28), 'nose': (30, 24, 30), 'collar': (196, 55, 58), 'tag': (230, 196, 78),
    'eye': (250, 248, 240), 'pupil': (22, 18, 26), 'tongue': (226, 120, 130),
    'skin': (190, 132, 92), 'skin_far': (160, 108, 74), 'hair': (44, 30, 28), 'sweater': (60, 150, 140), 'sweater_far': (42, 116, 110),
    'trousers': (58, 62, 96), 'trousers_far': (44, 46, 74), 'shoe': (40, 32, 32), 'mouth': (96, 30, 40), 'teeth': (248, 244, 236),
    'lid_person': (176, 120, 84),
}


def seed_of(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def R(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


# ---------------------------------------------------------------- primitive cuts
def ellipse(cx, cy, rx, ry, rot=0.0, n=None):
    """A scissor-cut oval: few facets (paper is cut in short straight snips), not a perfect curve."""
    n = n or int(max(10, min(30, (rx + ry) * 0.9)))
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    p = np.stack([rx * np.cos(a), ry * np.sin(a)], 1)
    if rot: p = p @ R(rot).T
    return p + [cx, cy]


def rrect(x0, y0, x1, y1, r, n=4):
    r = min(r, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
    pts = []
    for (cx, cy, a0) in [(x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)]:
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def capsule(p0, p1, w0, w1=None, n=5):
    """A tapered strip with rounded ends from p0 to p1 (a limb segment)."""
    w1 = w0 if w1 is None else w1
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0; L = np.hypot(*d) or 1e-6; u = d / L; v = np.array([-u[1], u[0]])
    pts = []
    for k in range(n + 1):                        # end cap at p1
        a = -math.pi / 2 + math.pi * k / n
        pts.append(p1 + (u * math.cos(a) + v * math.sin(a)) * w1 / 2)
    for k in range(n + 1):                        # end cap at p0
        a = math.pi / 2 + math.pi * k / n
        pts.append(p0 + (u * math.cos(a) + v * math.sin(a)) * w0 / 2)
    return np.array(pts)


def poly(pts):
    return np.asarray(pts, float)


def handcut(pts, name, amp=0.45):
    """Fixed scissor wobble: each vertex is nudged along its normal by a seeded amount. Same name, same cut, every frame."""
    pts = np.asarray(pts, float); n = len(pts)
    if n < 3: return pts
    g = np.random.default_rng(seed_of(name))
    k = g.uniform(-1, 1, n) * amp
    nxt = np.roll(pts, -1, 0); prv = np.roll(pts, 1, 0); t = nxt - prv
    nrm = np.stack([t[:, 1], -t[:, 0]], 1); nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    return pts + nrm * k[:, None]


class Piece:
    __slots__ = ('pts', 'fill', 'z', 'tag', 'outline', 'grp')

    def __init__(self, pts, fill, z, tag='', outline=True, grp=None):
        self.pts = np.asarray(pts, float); self.fill = fill; self.z = z; self.tag = tag; self.outline = outline; self.grp = grp

    def moved(self, M):
        q = self.pts @ M[:2, :2].T + M[:2, 2]
        return Piece(q, self.fill, self.z, self.tag, self.outline, self.grp)


def affine(tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=1.0, px=0.0, py=0.0):
    """Rotate/scale about pivot (px,py), then translate."""
    M = np.eye(3)
    A = R(rot) @ np.diag([sx, sy])
    M[:2, :2] = A
    M[:2, 2] = np.array([px, py]) - A @ np.array([px, py]) + [tx, ty]
    return M


def apply(pieces, M):
    return [p.moved(M) for p in pieces]


def ik2(hip, foot, a, b, bend):
    """Two-segment limb: knee placed so the foot stays exactly where it is put (planted feet do not slide).
    bend=+1 puts the knee toward +x (the tail side), -1 toward the head side."""
    hip = np.asarray(hip, float); foot = np.asarray(foot, float)
    d = foot - hip; L = np.hypot(*d)
    L = min(L, a + b - 1e-3); L = max(L, abs(a - b) + 1e-3)
    u = d / (np.hypot(*d) or 1e-6)
    x = (a * a - b * b + L * L) / (2 * L); h = math.sqrt(max(a * a - x * x, 0))
    v = np.array([-u[1], u[0]])
    bv = np.array([bend, 0.0]) if np.isscalar(bend) else np.asarray(bend, float)
    if v @ bv < 0: v = -v
    knee = hip + u * x + v * h
    foot = hip + u * L
    return knee, foot
