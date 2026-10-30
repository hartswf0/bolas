"""SCION 44 Multiplane Parallax: shared definitions.

World coordinates (metres): X along the porch (= the score's x; door centre at 0, steps at 4.9),
Y up (porch floor at 0), Z depth away from the camera (house wall plane at Z = 0, the room behind it at Z > 0,
the porch in front of it, Z in [-2.1, 0]).  The camera only translates (no rotation, the multiplane rule): it looks
along +Z, so every vertical plane stays parallel to the film and its parallax is f / (Z - cz).
"""
import json, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
KIT = os.path.join(ROOT, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
CACHE = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
W, H = 1280, 720
F_PX = 1000.0          # focal length in pixels (horizontal FOV ~65 deg)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ramp(t, t0, t1):
    return smooth((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)


def lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- camera path (the camera operator's track)
# keys: t, X, Y, Z, focus depth.  Interpolated with a monotone smoothstep between keys (holds read as holds).
CAM_KEYS = [
    # t     X     Y     Z     focusZ   dramaturgy
    (0.0,  1.40, 1.10, -6.30, -0.75),  # the whole porch: the doorway at left, the dog at right (the call)
    (3.0,  1.60, 1.08, -6.25, -0.75),  # drift right with the retreat
    (7.4,  1.50, 1.04, -6.20, -0.75),  # the refusal held: the person steps aside, sits, the door opens (circumstances)
    (14.6, 1.45, 0.86, -5.55, -0.75),  # it turns back to look and waits: we crane down behind the railing
    (19.0, 1.05, 0.82, -4.70, -0.72),  # the approach: the camera trucks left, slower than the dog (parallax carries it)
    (23.7, 0.50, 0.76, -3.55, -0.30),  # at the sill
    (26.3, 0.52, 0.73, -3.05, -0.20),
    (28.5, 0.44, 0.50, -2.05, 0.0),   # looking in: we pass through the railing plane, low over its back, into the light
    (32.0, 0.42, 0.48, -1.96, 0.0),
]


_CAM = None


def camera(t):
    """pchip through the keys: continuous moves, no overshoot, no stop at every key."""
    global _CAM
    if _CAM is None:
        from scipy.interpolate import PchipInterpolator
        k = np.array(CAM_KEYS)
        _CAM = PchipInterpolator(k[:, 0], k[:, 1:], axis=0)
    t = min(max(t, CAM_KEYS[0][0]), CAM_KEYS[-1][0])
    v = _CAM(t)
    return np.array(v[:3]), float(v[3])


def project(P, cam):
    """world point(s) (...,3) -> screen (u, v, depth)."""
    P = np.asarray(P, float)
    d = P[..., 2] - cam[2]
    u = W / 2 + F_PX * (P[..., 0] - cam[0]) / d
    v = H / 2 - F_PX * (P[..., 1] - cam[1]) / d
    return u, v, d


def unproject_x(u, z, cam):
    return cam[0] + (u - W / 2) * (z - cam[2]) / F_PX


def homography(src, dst):
    """3x3 H with dst ~ H src for 4 point pairs."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    A = np.array(A, float)
    _, _, vt = np.linalg.svd(A)
    Hm = vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]
