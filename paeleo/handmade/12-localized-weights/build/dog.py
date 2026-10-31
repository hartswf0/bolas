"""The lace dog: a cut-paper (papercut) profile, drawn here in code as unions of tapered strokes, then pierced with lace holes.
Puppet-local metres, facing -x (toward the door), ground at y = 0. Deliberately concave: near and far legs a finger apart,
two pricked ears side by side, a curled tail, and 40-odd pierced holes through the body.
Handles (mixed): bones (neck, head, 2 x 4 leg segments, 2 tail segments), points (2 ear tips), and a 6-vertex torso cage."""
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely import affinity


def taper(a, b, ra, rb):
    return unary_union([Point(a).buffer(ra, 24), Point(b).buffer(rb, 24)]).convex_hull


def chain(pts, radii):
    return unary_union([taper(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)])


def catmull(points, n=12):
    P = np.array(points, float); out = []
    m = len(P)
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return Polygon(out)


def ellipse(c, rx, ry, ang=0):
    return affinity.rotate(affinity.scale(Point(c).buffer(1, 24), rx, ry), ang, origin=c)


def petal(c, ang, r0, r1, w):
    """A teardrop hole pointing outward from c at angle ang (degrees)."""
    a = np.radians(ang)
    p0 = (c[0] + r0 * np.cos(a), c[1] + r0 * np.sin(a))
    p1 = (c[0] + r1 * np.cos(a), c[1] + r1 * np.sin(a))
    return taper(p0, p1, w * .35, w)


# ---- rest skeleton (puppet-local) ----
J = {
    'C': (0.0, 0.42),            # torso centre (yaw pivot)
    'N': (-0.29, 0.50),          # neck base
    'H': (-0.40, 0.665),         # head joint (atlas)
    'T0': (0.31, 0.475), 'T1': (0.42, 0.555),   # tail base, tail mid
    'EB_n': (-0.415, 0.765), 'EB_f': (-0.365, 0.76),   # ear bases
}
LEGS = {  # joint0 (shoulder/hip), joint1 (elbow/stifle), paw
    'fn': [(-0.25, 0.33), (-0.25, 0.185), (-0.262, 0.035)],
    'ff': [(-0.150, 0.33), (-0.150, 0.185), (-0.162, 0.035)],
    'hn': [(0.215, 0.36), (0.175, 0.20), (0.235, 0.035)],
    'hf': [(0.300, 0.36), (0.262, 0.20), (0.322, 0.035)],
}


def shape():
    torso = catmull([(-0.335, 0.41), (-0.30, 0.50), (-0.24, 0.56), (-0.12, 0.535), (0.0, 0.52), (0.14, 0.525), (0.26, 0.535),
                     (0.335, 0.49), (0.35, 0.40), (0.31, 0.33), (0.20, 0.315), (0.10, 0.31), (-0.05, 0.285), (-0.20, 0.27),
                     (-0.30, 0.31)])
    neck = taper((-0.27, 0.47), (-0.39, 0.655), 0.095, 0.07)
    skull = ellipse((-0.43, 0.705), 0.08, 0.07, -8)
    muzzle = taper((-0.47, 0.682), (-0.555, 0.660), 0.056, 0.037)
    jaw = taper((-0.45, 0.652), (-0.54, 0.636), 0.034, 0.024)
    nose = Point((-0.565, 0.668)).buffer(0.027, 16)
    ear_n = Polygon([(-0.452, 0.735), (-0.392, 0.748), (-0.418, 0.885)]).buffer(0.008, 8)
    ear_f = Polygon([(-0.392, 0.738), (-0.338, 0.742), (-0.352, 0.868)]).buffer(0.008, 8)
    legs = []
    for k, (a, b, c) in LEGS.items():
        front = k[0] == 'f'
        top = (a[0], a[1] + 0.05)
        if front:
            legs.append(chain([top, a, b, c], [0.05, 0.043, 0.03, 0.025]))
            legs.append(ellipse((c[0] - 0.018, 0.022), 0.034, 0.021))
        else:
            legs.append(chain([(a[0] + 0.02, a[1] + 0.06), a, b, c], [0.07, 0.06, 0.03, 0.024]))
            legs.append(ellipse((c[0] - 0.018, 0.022), 0.037, 0.022))
    tail = chain([(0.30, 0.47), J['T0'], J['T1'], (0.47, 0.63), (0.49, 0.72), (0.47, 0.76)],
                 [0.05, 0.042, 0.032, 0.024, 0.016, 0.01])
    body = unary_union([torso, neck, skull, muzzle, jaw, nose, ear_n, ear_f, tail] + legs).buffer(0.002).buffer(-0.002)
    return body, lace_holes()


def lace_holes():
    """Bold lace: every piercing is at least 2 cm across its narrow side, so it still reads at the wide shot (~180 px/m)."""
    H = []
    # shoulder and hip rosettes: six petals around a round eye
    for c in ((-0.165, 0.405), (0.165, 0.405)):
        H.append(Point(c).buffer(0.017, 20))
        for k in range(6):
            H.append(petal(c, k * 60, 0.024, 0.050, 0.012))
    # a row of round piercings along the back (above the cage line)
    for x in np.linspace(-0.07, 0.09, 4):
        H.append(Point((x, 0.495)).buffer(0.0125, 16))
    # crescents along the belly, below the cage line
    for x, a in ((-0.10, 6), (-0.03, 2), (0.04, -2)):
        H.append(ellipse((x, 0.316), 0.027, 0.0085, a))
    # centre medallion: diamond and four drops
    c = (0.0, 0.405)
    H.append(Polygon([(c[0], c[1] + 0.036), (c[0] + 0.026, c[1]), (c[0], c[1] - 0.036), (c[0] - 0.026, c[1])]))
    for ang in (0, 90, 180, 270):
        H.append(petal(c, ang + 45, 0.040, 0.054, 0.0105))
    H.append(petal((-0.315, 0.455), -70, 0.0, 0.035, 0.013))   # chest drop
    H.append(ellipse((-0.455, 0.715), 0.016, 0.0105, -12))      # eye
    H.append(ellipse((-0.418, 0.80), 0.008, 0.026, 78))         # near ear slit
    H.append(ellipse((-0.358, 0.795), 0.007, 0.021, 82))        # far ear slit
    H.append(petal((0.255, 0.40), -100, 0.0, 0.032, 0.013))    # thigh drop
    return unary_union(H)


CAGE = [(-0.265, 0.475), (0.0, 0.465), (0.27, 0.47), (0.28, 0.345), (0.0, 0.335), (-0.235, 0.34)]


def handles():
    hs = []
    hs.append({'name': 'neck', 'kind': 'bone', 'a': (-0.315, 0.535), 'b': (-0.375, 0.635), 'group': 'head'})
    hs.append({'name': 'head', 'kind': 'bone', 'a': (-0.43, 0.695), 'b': (-0.545, 0.665), 'group': 'head'})
    for k, (a, b, c) in LEGS.items():
        a, b, c = np.array(a), np.array(b), np.array(c)
        hs.append({'name': k + '_upper', 'kind': 'bone', 'a': tuple(a + (b - a) * 0.12), 'b': tuple(a + (b - a) * 0.80),
                   'group': 'front' if k[0] == 'f' else 'rear', 'leg': k, 'seg': 0})
        hs.append({'name': k + '_lower', 'kind': 'bone', 'a': tuple(b + (c - b) * 0.22), 'b': tuple(b + (c - b) * 0.92),
                   'group': 'front' if k[0] == 'f' else 'rear', 'leg': k, 'seg': 1})
    hs.append({'name': 'tail1', 'kind': 'bone', 'a': (0.345, 0.495), 'b': (0.40, 0.537), 'group': 'rear'})
    hs.append({'name': 'tail2', 'kind': 'bone', 'a': (0.445, 0.585), 'b': (0.478, 0.70), 'group': 'rear'})
    hs.append({'name': 'ear_near', 'kind': 'point', 'p': (-0.417, 0.868), 'group': 'head', 'base': J['EB_n']})
    hs.append({'name': 'ear_far', 'kind': 'point', 'p': (-0.353, 0.852), 'group': 'head', 'base': J['EB_f']})
    for i, p in enumerate(CAGE):
        hs.append({'name': 'cage%d' % i, 'kind': 'cage', 'p': p, 'group': 'front' if p[0] < -0.01 else ('rear' if p[0] > 0.01 else 'mid')})
    return hs


def build(h=0.0075):
    import bbw
    body, holes = shape()
    poly = body.difference(holes)
    hs = handles()
    V, F = bbw.triangulate(poly, hs, h=h)
    return poly, hs, V, F
