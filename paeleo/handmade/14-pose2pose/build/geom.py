"""Drawing geometry for the illustrator: smooth curves, tapered limbs, transforms.
Coordinates are film pixels at S = 190 px per metre, y downward, origin on the ground under the figure's reference point."""
import math


def cr(pts, closed=True, n=6):
    """Catmull-Rom through hand-placed points -> dense polyline."""
    P = [tuple(p) for p in pts]
    m = len(P)
    if m < 3:
        return [list(p) for p in P]
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % m] if closed else P[min(i + 1, m - 1)]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = .5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append([round(x, 2), round(y, 2)])
    if not closed:
        out.append([round(P[-1][0], 2), round(P[-1][1], 2)])
    return out


def add(a, b, s=1.0):
    return (a[0] + s * b[0], a[1] + s * b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ellipse(c, rx, ry, ang=0.0, n=18):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(c[0] + rx * math.cos(2 * math.pi * k / n) * ca - ry * math.sin(2 * math.pi * k / n) * sa,
             c[1] + rx * math.cos(2 * math.pi * k / n) * sa + ry * math.sin(2 * math.pi * k / n) * ca) for k in range(n)]


def limb(joints, widths, foot=None):
    """A tapered limb outline around a polyline of joints (hand placed or solved), widths per joint.
    foot: (dx_toe, len) a paw pad drawn forward of the last joint."""
    J = [tuple(j) for j in joints]
    n = len(J)
    L, R = [], []
    for i in range(n):
        if i == 0:
            d = (J[1][0] - J[0][0], J[1][1] - J[0][1])
        elif i == n - 1:
            d = (J[i][0] - J[i - 1][0], J[i][1] - J[i - 1][1])
        else:
            d1 = (J[i][0] - J[i - 1][0], J[i][1] - J[i - 1][1]); d2 = (J[i + 1][0] - J[i][0], J[i + 1][1] - J[i][1])
            l1 = math.hypot(*d1) or 1; l2 = math.hypot(*d2) or 1
            d = (d1[0] / l1 + d2[0] / l2, d1[1] / l1 + d2[1] / l2)
        ln = math.hypot(*d) or 1
        nx, ny = -d[1] / ln, d[0] / ln
        w = widths[i] / 2
        L.append((J[i][0] + nx * w, J[i][1] + ny * w)); R.append((J[i][0] - nx * w, J[i][1] - ny * w))
    pts = L[:]
    if foot:
        e = J[-1]; dx, fl = foot
        pts += [(e[0] + dx * fl * .55, e[1] + 1), (e[0] + dx * fl, e[1] + 2.5), (e[0] + dx * fl * 1.05, e[1] + 4.5)]
        # pad sits on the ground line of the last joint
    pts += R[::-1]
    # rounded top
    a, b = L[0], R[0]
    top = (J[0][0] - (J[1][0] - J[0][0]) * .25, J[0][1] - (J[1][1] - J[0][1]) * .25)
    pts.append(top)
    return pts


def ik2(a, c, l1, l2, bend):
    """Two-bone solve from a to c with bone lengths l1,l2; bend=+1/-1 picks the knee side. Returns knee."""
    dx, dy = c[0] - a[0], c[1] - a[1]
    d = math.hypot(dx, dy)
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = math.atan2(dy, dx) + bend * math.acos(max(-1, min(1, ca)))
    return (a[0] + l1 * math.cos(ang), a[1] + l1 * math.sin(ang))


def xf(pts, at=(0, 0), ang=0.0, s=1.0, flip=False):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        if flip:
            x = -x
        x, y = x * s, y * s
        out.append((at[0] + x * ca - y * sa, at[1] + x * sa + y * ca))
    return out


def mirror(parts):
    """Flop a whole drawing left-right (a separate drawing, never used as a turn)."""
    out = []
    for p in parts:
        q = dict(p)
        q['p'] = [[-x, y] for x, y in p['p']]
        out.append(q)
    return out


def rnd(pts):
    return [[round(x, 2), round(y, 2)] for x, y in pts]
