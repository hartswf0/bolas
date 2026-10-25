"""SCION 33 · world, camera and the analytic/numerical two-bone solvers.

Coordinates (world, metres): X along the porch = the score's x (threshold plane of the house front at X = 0.40,
sill edge at 0.56, porch steps at 4.9); Y up (porch boards at Y = 0); Z toward the camera.
Time base: scene frame i = 0..767 at 24 fps, t = i / 24 (the score's clock).
"""
import math
import numpy as np

W, H = 1280, 720
FPS = 24
N = 768

# ---- the set (fixed; the camera never moves, so x_screen is a valid measure for the checker) ----
WALL_OUT = 0.40      # outer face of the house front
WALL_IN = 0.24       # inner face (jamb depth 0.16 m)
SILL = 0.56          # outer edge of the sill board (score places.sill)
DOOR_Z = (-0.46, 0.46)
DOOR_H = 2.05
HINGE = np.array([WALL_IN, 0.0, 0.46])   # door hinged on the near jamb, opens inward
DOOR_W = 0.92
LAMP = np.array([-1.5, 1.12, -2.35])     # the visible lamp on a table, far side of the room
LAMP2 = np.array([-3.25, 1.02, 0.12])     # a second lamp on the back wall, seen straight through the door
CEIL = np.array([-1.15, 2.45, -0.05])    # the ceiling light that casts the spill through the door
PATH_Z = -0.06                           # the line the dog walks on, just behind the door's centre
STEPS_X = 4.9
PORCH_Z = (-3.2, 1.55)

CAMS = {
    'A': dict(pos=[3.9, 1.35, 4.6], look=[2.2, 0.62, -0.3], fov=35.5),      # the wide: porch, door, yard
    'B': dict(pos=[2.6, 1.6, 2.8], look=[0.35, 0.5, -0.2], fov=38.0),      # closer: the sill, the room, the low hand
}
CUT_T = 20.5          # one cut, mid-approach, while the dog walks (not on a choice)


def cam_name(i):
    return 'A' if i / FPS < CUT_T else 'B'


CAM = np.array([3.9, 1.35, 4.6])
LOOK = np.array([2.2, 0.62, -0.3])
FOV_V = 35.5


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


class Camera:
    def __init__(self, pos=CAM, look=LOOK, fov=FOV_V, w=W, h=H, name=None):
        if name is not None:
            c = CAMS[name]; pos, look, fov = c['pos'], c['look'], c['fov']
        self.pos = np.asarray(pos, float)
        self.fwd = norm(np.asarray(look, float) - self.pos)
        self.right = norm(np.cross(self.fwd, [0, 1, 0]))
        self.up = np.cross(self.right, self.fwd)
        self.w, self.h = w, h
        self.f = (h / 2) / math.tan(math.radians(fov) / 2)

    def project(self, p):
        """world point(s) (..., 3) -> screen x, y and depth (metres along the view axis)."""
        p = np.asarray(p, float)
        d = p - self.pos
        z = d @ self.fwd
        x = self.w / 2 + self.f * (d @ self.right) / z
        y = self.h / 2 - self.f * (d @ self.up) / z
        return np.stack([x, y, z], -1)

    def scale(self, depth):
        return self.f / depth

    def ray(self, sx, sy):
        """screen pixel(s) -> unit world ray directions."""
        a = (np.asarray(sx, float) - self.w / 2) / self.f
        b = -(np.asarray(sy, float) - self.h / 2) / self.f
        d = self.fwd[None] + a[..., None] * self.right[None] + b[..., None] * self.up[None]
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


# ---- two-bone IK: analytic (law of cosines, pole vector) ----

def two_bone(root, target, l1, l2, pole, min_inner_deg=18.0):
    """Solve root -> mid -> end with |root-mid| = l1, |mid-end| = l2 so that end reaches target.
    pole: world direction the middle joint bends toward (knees forward, elbows back).
    Joint limits: the chain cannot straighten past 0.999 (l1 + l2) nor fold the middle joint below min_inner_deg.
    Returns mid, end, residual (|end - target|), and the clamped flag."""
    root = np.asarray(root, float); target = np.asarray(target, float)
    v = target - root
    d = np.linalg.norm(v)
    dmax = (l1 + l2) * 0.999
    inner_min = math.radians(min_inner_deg)
    dmin = math.sqrt(l1 * l1 + l2 * l2 - 2 * l1 * l2 * math.cos(inner_min))
    clamped = False
    if d > dmax:
        d = dmax; clamped = True
    if d < dmin:
        d = dmin; clamped = True
    u = norm(v) if np.linalg.norm(v) > 1e-9 else np.array([0, -1.0, 0])
    end = root + u * d
    # angle at root between chain axis and upper bone
    cos_a = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    p = np.asarray(pole, float)
    p = p - u * (p @ u)
    if np.linalg.norm(p) < 1e-9:
        p = np.cross(u, [0, 0, 1.0])
    p = norm(p)
    mid = root + l1 * (math.cos(a) * u + math.sin(a) * p)
    return mid, end, float(np.linalg.norm(end - target)), clamped


def fabrik(root, target, lengths, pole, iters=40, init=None):
    """Numerical comparison solver (FABRIK) for the same chain, started bent toward the pole."""
    root = np.asarray(root, float); target = np.asarray(target, float)
    n = len(lengths)
    if init is None:
        u = norm(target - root)
        pts = [root.copy()]
        for i, L in enumerate(lengths):
            pts.append(pts[-1] + L * norm(u + (0.6 * norm(pole) if i == 0 else -0.6 * norm(pole))))
        pts = np.array(pts)
    else:
        pts = np.array(init, float)
    for _ in range(iters):
        pts[-1] = target
        for i in range(n - 1, -1, -1):
            pts[i] = pts[i + 1] + lengths[i] * norm(pts[i] - pts[i + 1])
        pts[0] = root
        for i in range(n):
            pts[i + 1] = pts[i] + lengths[i] * norm(pts[i + 1] - pts[i])
    return pts, float(np.linalg.norm(pts[-1] - target))


def bend_side(root, mid, end, pole):
    """+1 when the middle joint bends toward the pole (the intended direction), -1 when it is inverted."""
    axis = norm(end - root)
    off = (mid - root) - axis * ((mid - root) @ axis)
    return 1 if off @ np.asarray(pole, float) > 0 else -1


def smooth(a, b, t):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u
