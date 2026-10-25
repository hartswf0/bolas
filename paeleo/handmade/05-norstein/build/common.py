"""Shared state for SCION 05 Norstein: the score, the multiplane camera, the scene graph constants.

World: metres. X runs along the porch (door centred at X=0, porch steps at X=4.9, the score's x IS this X).
Y up from the porch boards. Z is depth away from the camera's starting point (the house wall is at Z=5.0).
Time: scene frame i at 24 fps, t = i/24 (the 32 s scene); film frames add a 72-frame title card before it.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
CACHE = os.path.join(HERE, 'cache')
KIT = os.path.join(REPO, 'paeleo/handmade/kit')
FOUND = '/home/user/hartswf0/secondhand-motion/shots'
W, H, FPS = 1280, 720, 24
N = 768
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']

# scene graph depths (Z, metres from the camera origin); the glass planes of the multiplane
Z = dict(grass=1.9, fog_near=2.9, porch_edge=3.8, fog_porch=4.25, dog=4.55, person=4.72, wall=5.0, door=5.05,
         interior_near=6.6, interior_wall=8.2, fog_far=10.0, trees_near=15.0, trees_far=32.0, sky=400.0)
CAM_Y = 1.2      # camera height above the porch boards
F = 920.0        # focal length in px
CX, CY = 640.0, 300.0   # principal point (lens shifted up: horizon at y=300)
APERTURE = 16.0  # px of blur per unit |z - zf|/z


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def smooth(a, b, t):
    if b == a:
        return 1.0 if t >= b else 0.0
    u = clamp((t - a) / (b - a))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def keyed(keys, t):
    """keys: [(t, value), ...] eased (smoothstep) between keys."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(v0, v1, smooth(t0, t1, t))
    return keys[-1][1]


def door_angle(t):
    """degrees the door leaf has swung inward (hinged on the right jamb). ajar 52, open 86."""
    return keyed([(0, 52), (6.15, 52), (6.25, 56), (6.9, 86), (32, 86)], t)


def door_gap(t):
    """the lit opening, as a fraction of the full door width (orthographic estimate)."""
    a = math.radians(door_angle(t))
    return 1 - math.cos(a)


# ---- the camera: pan X, truck Z, focus distance (world Z), as curves of scene time
CAM_X = [(0, 1.95), (4.15, 1.97), (5.7, 2.85), (6.05, 2.86), (7.4, 1.47), (14.6, 1.55), (16.0, 1.42), (23.6, 0.20), (32, 0.02)]
CAM_Z = [(0, 0.0), (4.15, 0.0), (5.7, 0.92), (6.05, 0.94), (7.4, 0.02), (14.6, 0.16), (23.6, 1.10), (32, 1.36)]


def dog_z(t):
    return dog_path(t)[1]


def dog_path(t):
    """root X (the score's x) and root Z (depth on the porch) for scene time t."""
    i = min(N - 1, max(0, int(round(t * FPS))))
    x = FR[i]['dog']['x']
    # depth: the dog keeps to the middle of the porch, then angles in towards the doorway over the last 1.6 m
    z = Z['dog'] + 0.26 * smooth(2.2, 0.59, x) if FR[i]['dog']['state'] in ('approach', 'lie_down') else Z['dog']
    return x, z


FOCUS = None  # filled lazily


def focus_z(t):
    """the exposure/focus schedule: which depth is sharp. Rack-focus events are dramatic beats."""
    zd = dog_z(t)
    k = [(0, Z['grass'] + 0.3), (0.15, Z['grass'] + 0.3), (0.95, zd)]
    if t < 0.95:
        return keyed(k, t)
    if 6.3 <= t <= 7.38:  # the door opens: focus is pulled into the light, then back to the near hand and the dog
        return keyed([(6.3, zd), (6.75, Z['interior_near'] + 0.4), (6.95, Z['interior_near'] + 0.4), (7.38, zd)], t)
    if 26.95 <= t <= 28.0:  # come in: the dog looks in, focus follows its look into the room, then returns to it
        return keyed([(26.95, zd), (27.3, Z['interior_wall'] - 0.6), (27.55, Z['interior_wall'] - 0.6), (27.95, zd)], t)
    return zd


CAM_YK = [(0, CAM_Y), (4.15, CAM_Y), (5.7, 0.82), (6.05, 0.82), (7.4, CAM_Y), (32, CAM_Y)]


def cam(t):
    return keyed(CAM_X, t), keyed(CAM_YK, t), keyed(CAM_Z, t)


def blur_px(z, t):
    cx, cy, cz = cam(t)
    zc = z - cz
    zf = focus_z(t) - cz
    return APERTURE * abs(zc - zf) / max(zc, 0.05)


def project(P, c):
    """pinhole projection of a world point P=(X,Y,Z) for camera c=(cx,cy,cz)."""
    zc = P[2] - c[2]
    return CX + F * (P[0] - c[0]) / zc, CY - F * (P[1] - c[1]) / zc, zc


def unproject_x(sx, zworld, c):
    """the inverse: a screen x at a known world depth back to world X (used to measure the dog's position)."""
    return c[0] + (sx - CX) * (zworld - c[2]) / F


def score_frame(i):
    return FR[min(N - 1, max(0, i))]
