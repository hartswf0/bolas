"""One locked-off camera for the whole shot. World metres: X along the facade, Y up, Z out of the house (facade Z=0).
The dog's path leaves the threshold at 60 deg to the facade normal; the camera looks perpendicular to that path,
so the score's x maps to screen x linearly (one depth) and the doorway is seen 30 deg off its normal."""
import numpy as np
from comp import W, H

TH = np.radians(60)
D = np.array([np.sin(TH), 0, np.cos(TH)])          # path direction, out of the house
V = np.array([np.cos(TH), 0, -np.sin(TH)])         # horizontal view direction (perpendicular to the path)
F = 1060.0
OFFSET = 0.45   # the dog's centre stands OFFSET m nearer the house than the score's x (the score's x is its rear)


def path_point(s, y=0.0):
    return D * s + np.array([0, y, 0])


_C = path_point(1.55) - 5.0 * V + np.array([0, 1.10, 0])
_tilt = np.radians(-2.5)
_fwd = V * np.cos(_tilt) + np.array([0, np.sin(_tilt), 0])
_right = np.cross(_fwd, [0, 1, 0]); _right /= np.linalg.norm(_right)
_up = np.cross(_right, _fwd)
CAM = dict(C=_C.tolist(), fwd=_fwd.tolist(), f=F, tilt_deg=-2.5, path_theta_deg=60, offset=OFFSET)


def project(P):
    P = np.atleast_2d(np.asarray(P, float)) - _C
    z = P @ _fwd
    x = P @ _right; y = P @ _up
    return np.c_[W / 2 + F * x / z, H / 2 - F * y / z], z


def depth(P):
    return project(P)[1]


def px_per_m_on_path():
    a, _ = project([path_point(0), path_point(1)])
    return float(a[1, 0] - a[0, 0])


def unproject_to_plane(u, v, n, d):
    """Ray through screen (u,v) meets plane n.P = d. Returns world points (N,3)."""
    x = (np.asarray(u, float) - W / 2) / F; y = -(np.asarray(v, float) - H / 2) / F
    dirs = _fwd[None] + x[:, None] * _right[None] + y[:, None] * _up[None]
    t = (d - _C @ n) / (dirs @ n)
    return _C[None] + t[:, None] * dirs, t


if __name__ == '__main__':
    for s in (-0.5, 0, 0.14, 1, 2, 3.55, 4.45):
        print(s, project(path_point(s))[0].round(1), project(path_point(s, .6))[0].round(1))
    print('door', project([[-.46, 0, 0], [.46, 0, 0], [.46, 2.05, 0], [-.46, 2.05, 0]])[0].round(1))
    print('px/m', px_per_m_on_path())
