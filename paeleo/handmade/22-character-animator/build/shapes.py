"""2D geometry helpers for the felt puppet: Catmull-Rom outlines, ellipses, strips along chains, transforms."""
import numpy as np, math


def cr(ctrl, closed=True, n=7):
    P = np.asarray(ctrl, float)
    m = len(P)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if closed or i > 0 else P[0]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed or i + 2 < m else P[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-1])
    return np.array(out)


def ellipse(cx, cy, rx, ry, rot=0.0, n=30, a0=0.0, a1=2 * math.pi):
    a = np.linspace(a0, a1, n, endpoint=(a1 - a0) < 2 * math.pi - 1e-6)
    c, s = math.cos(rot), math.sin(rot)
    x, y = rx * np.cos(a), ry * np.sin(a)
    return np.stack([cx + c * x - s * y, cy + s * x + c * y], 1)


def strip(path, widths, cap=True):
    """polygon around a polyline with per-point half widths (rounded end)."""
    P = np.asarray(path, float)
    if len(P) < 2:
        return P
    w = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(widths)), widths)
    d = np.gradient(P, axis=0)
    d /= (np.linalg.norm(d, axis=1)[:, None] + 1e-9)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    L = P + nrm * w[:, None]
    R = P - nrm * w[:, None]
    tip = []
    if cap:
        a0 = math.atan2(nrm[-1, 1], nrm[-1, 0])
        for k in range(1, 6):
            a = a0 - math.pi * k / 6
            tip.append(P[-1] + w[-1] * np.array([math.cos(a), math.sin(a)]))
    tail = []
    if cap:
        a0 = math.atan2(-nrm[0, 1], -nrm[0, 0])
        for k in range(1, 6):
            a = a0 - math.pi * k / 6
            tail.append(P[0] + w[0] * np.array([math.cos(a), math.sin(a)]))
    return np.vstack([L, np.array(tip).reshape(-1, 2), R[::-1], np.array(tail).reshape(-1, 2)])


def smooth_path(pts, n=6):
    return cr(pts, closed=False, n=n) if len(pts) > 2 else np.asarray(pts, float)


def xform(pts, origin=(0, 0), mirror=1.0, rot_deg=0.0, scale=(1.0, 1.0), pivot=(0, 0)):
    """local -> parent: scale about pivot, rotate (deg, ccw), mirror x, translate."""
    P = np.asarray(pts, float) - pivot
    P = P * np.asarray(scale)
    P = P + pivot
    a = math.radians(rot_deg)
    c, s = math.cos(a), math.sin(a)
    P = np.stack([c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]], 1)
    P[:, 0] *= mirror
    return P + np.asarray(origin)


def xpt(p, **kw):
    return xform(np.array([p], float), **kw)[0]


def ik2(a, b, l1, l2, bend):
    """two-bone IK from joint a to target b; bend=+1/-1 chooses the side (in world, after mirroring) of the middle joint."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    L = min(max(L, 1e-4), l1 + l2 - 1e-4)
    dn = d / (np.linalg.norm(d) + 1e-9)
    b = a + dn * L
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    perp = np.array([-dn[1], dn[0]]) * bend
    m = a + dn * x + perp * h
    return m, b


def lerp2(a, b, u):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * u
