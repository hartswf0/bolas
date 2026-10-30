"""SCION 22 · the puppet runtime.  A small Character-Animator-like runtime: layered, named puppets (PSD-style groups)
with swap sets for views and visemes, and behaviours attached to them:
  Lip Sync (visemes from the voice audio) · Triggers (held swap/pose beats from Take 2) · Head & Body Turner (Take 3)
  · Dangle (verlet chains: ears, tail, ponytail) · Auto Blink · Breathe · Eye Gaze (snap gaze to named targets, Take 4)
  · Walk (planted feet from distance travelled) · Limb IK.
Evaluates every scene frame in order (Dangle is stateful) and writes cache/rig.pkl (one draw list per frame, world metres)
and cache/events.json (footfalls, door, contacts) for the sound."""
import json, math, os, pickle
import numpy as np
from common import (SCORE, N, FPS, FOLDER, CACHE, WALL_IN, WALL_OUT, DOOR_W, PERSON_BESIDE, ease, ramp, lerp, camera_track)
from shapes import cr, ellipse, strip, xform, xpt, ik2, lerp2, smooth_path

TAKES = json.load(open(os.path.join(FOLDER, 'takes.json')))
TK = {t['name'].split(' · ')[0]: t for t in TAKES['takes']}
CAP = TK['Take 1']['params']
TRIG = TK['Take 2']['events']
TURN = TK['Take 3']
GAZE = TK['Take 4']
PERS = TK['Take 5']['params']
VIS = json.load(open(os.path.join(CACHE, 'visemes.json')))['visemes']

C = {  # felt palette (before light)
    'tan': (198, 140, 78), 'saddle': (96, 62, 40), 'cream': (238, 218, 182), 'nose': (36, 28, 30), 'collar': (178, 50, 46),
    'pink': (214, 146, 138), 'white': (240, 234, 222), 'iris': (128, 82, 38), 'pupil': (22, 16, 16), 'tag': (214, 182, 74),
    'sweater': (88, 120, 86), 'trousers': (54, 60, 92), 'skin': (226, 176, 140), 'hair': (74, 44, 30), 'shoe': (44, 34, 30),
    'lip': (172, 84, 80), 'mouth': (70, 26, 30), 'teeth': (244, 238, 226), 'tongue': (206, 108, 110), 'cheek': (232, 150, 130),
    'thread': (250, 236, 200),
}
DARK = 0.70   # far-side pieces are cut from the same felt, shaded


def dk(c, k=DARK):
    return tuple(int(v * k) for v in c)


def interp_keys(keys, t):
    ks = keys
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0)) if t1 > t0 else v1
    return ks[-1][1]


# ------------------------------------------------------------------------------------------------ dog artwork (swap sets)
BODY_VIEWS = {
    'Side': {
        'torso': [(-0.44, 0.47), (-0.40, 0.565), (-0.20, 0.60), (0.05, 0.605), (0.20, 0.625), (0.33, 0.58), (0.41, 0.49), (0.40, 0.38), (0.32, 0.30), (0.12, 0.29), (-0.06, 0.33), (-0.22, 0.33), (-0.36, 0.36)],
        'saddle': [(-0.41, 0.55), (-0.20, 0.598), (0.05, 0.603), (0.19, 0.62), (0.22, 0.57), (0.05, 0.53), (-0.18, 0.50), (-0.38, 0.47)],
        'bib': [(0.30, 0.55), (0.40, 0.49), (0.395, 0.38), (0.31, 0.31), (0.25, 0.40)],
        'haunch': [(-0.27, 0.45, 0.135, 0.125, 0.2)], 'shoulder': [(0.24, 0.47, 0.095, 0.12, -0.3)],
        'tail_root': (-0.43, 0.53), 'neck': (0.30, 0.54),
        'legs': {'FN': (0.24, 0.42), 'FF': (0.275, 0.43), 'HN': (-0.27, 0.42), 'HF': (-0.235, 0.43)},
    },
    'Quarter': {
        'torso': [(-0.30, 0.45), (-0.27, 0.56), (-0.16, 0.63), (0.0, 0.64), (0.14, 0.635), (0.24, 0.60), (0.27, 0.52), (0.22, 0.42), (0.10, 0.36), (-0.05, 0.31), (-0.20, 0.31), (-0.29, 0.36)],
        'saddle': [(-0.24, 0.58), (-0.12, 0.635), (0.05, 0.64), (0.20, 0.62), (0.19, 0.57), (0.0, 0.555), (-0.16, 0.54)],
        'bib': None,
        'haunch': [(-0.155, 0.44, 0.15, 0.14, 0.1)], 'shoulder': [],
        'tail_root': (-0.21, 0.575), 'neck': (0.21, 0.60),
        'legs': {'FN': (0.15, 0.43), 'FF': (0.22, 0.45), 'HN': (-0.16, 0.40), 'HF': (0.0, 0.41)},
    },
    'Back': {
        'torso': [(-0.17, 0.46), (-0.15, 0.58), (-0.08, 0.635), (0.0, 0.645), (0.08, 0.635), (0.15, 0.58), (0.17, 0.46), (0.13, 0.36), (0.0, 0.31), (-0.13, 0.36)],
        'saddle': [(-0.13, 0.58), (-0.06, 0.635), (0.06, 0.635), (0.13, 0.58), (0.06, 0.55), (-0.06, 0.55)],
        'bib': None,
        'haunch': [(-0.085, 0.42, 0.095, 0.12, 0.0), (0.085, 0.42, 0.095, 0.12, 0.0)], 'shoulder': [],
        'tail_root': (0.0, 0.565), 'neck': (0.0, 0.615),
        'legs': {'FN': (-0.07, 0.42), 'FF': (0.07, 0.42), 'HN': (-0.085, 0.38), 'HF': (0.085, 0.38)},
    },
}

HEAD_VIEWS = {
    'Profile': {
        'skull': [(-0.05, 0.02), (-0.06, 0.09), (-0.02, 0.15), (0.06, 0.175), (0.13, 0.15), (0.17, 0.10), (0.27, 0.075), (0.315, 0.05), (0.31, 0.01), (0.25, -0.025), (0.12, -0.045), (0.03, -0.05), (-0.03, -0.025)],
        'cap': [(-0.05, 0.09), (-0.02, 0.15), (0.06, 0.175), (0.13, 0.15), (0.15, 0.12), (0.08, 0.125), (0.0, 0.10)],
        'muzzle': [(0.16, 0.07), (0.27, 0.07), (0.315, 0.045), (0.31, 0.01), (0.25, -0.025), (0.15, -0.035), (0.12, 0.0)],
        'nose': (0.305, 0.045, 0.024, 0.02), 'eyes': [(0.135, 0.095, 0.030, 0.025)], 'mouth': [(0.30, 0.0), (0.21, -0.014), (0.15, 0.0)],
        'ears': {'near': (0.0, 0.15), 'far': (0.04, 0.16)}, 'ear_dir': {'near': (168, 96), 'far': (160, 88)}, 'far_ear_behind': True,
        'muzzle_tip': (0.315, 0.04),
    },
    'QFront': {
        'skull': None, 'skull_e': (0.02, 0.08, 0.11, 0.10),
        'cap': [(-0.08, 0.12), (0.0, 0.18), (0.09, 0.165), (0.06, 0.13), (0.02, 0.115)],
        'muzzle': [(0.04, 0.0), (0.10, 0.06), (0.17, 0.075), (0.215, 0.05), (0.21, 0.01), (0.15, -0.03), (0.07, -0.035)],
        'blaze': [(0.08, 0.07), (0.06, 0.15), (0.09, 0.15), (0.12, 0.07)],
        'nose': (0.205, 0.05, 0.025, 0.021), 'eyes': [(0.03, 0.105, 0.027, 0.023), (0.13, 0.115, 0.021, 0.019)], 'mouth': [(0.20, 0.005), (0.15, -0.012), (0.09, -0.005)],
        'ears': {'near': (-0.06, 0.15), 'far': (0.07, 0.165)}, 'ear_dir': {'near': (150, 100), 'far': (70, 80)}, 'far_ear_behind': True,
        'muzzle_tip': (0.215, 0.04),
    },
    'QBack': {
        'skull': None, 'skull_e': (0.0, 0.08, 0.11, 0.10),
        'cap': [(-0.10, 0.10), (-0.05, 0.165), (0.04, 0.18), (0.10, 0.13), (0.06, 0.10), (-0.04, 0.085)],
        'muzzle_behind': [(0.06, 0.03), (0.16, 0.045), (0.20, 0.062), (0.17, 0.088), (0.08, 0.10)], 'nose_behind': (0.195, 0.062, 0.018, 0.016),
        'ruff': [(0.02, -0.02), (0.09, 0.0), (0.105, 0.04), (0.06, 0.02)],
        'eyes': [], 'mouth': None,
        'ears': {'near': (-0.05, 0.15), 'far': (0.06, 0.165)}, 'ear_dir': {'near': (115, 95), 'far': (75, 85)}, 'far_ear_behind': True,
        'muzzle_tip': (0.20, 0.062),
    },
    'Back': {
        'skull': None, 'skull_e': (0.0, 0.08, 0.105, 0.10),
        'cap': [(-0.09, 0.10), (-0.05, 0.165), (0.05, 0.165), (0.09, 0.10), (0.0, 0.08)],
        'eyes': [], 'mouth': None,
        'ears': {'near': (-0.065, 0.15), 'far': (0.065, 0.15)}, 'ear_dir': {'near': (120, 100), 'far': (60, 80)}, 'far_ear_behind': False,
        'muzzle_tip': (0.0, 0.08),
    },
}


def body_view(theta):
    th = theta % 360
    if th < 25 or th >= 335:
        return 'Side', -1
    if th < 65:
        return 'Quarter', -1
    if th < 115:
        return 'Back', 1
    if th < 155:
        return 'Quarter', 1
    if th < 205:
        return 'Side', 1
    raise ValueError('front body views are not drawn (yaw %.1f)' % th)


def head_view(phi):
    p = phi % 360
    if p < 25 or p >= 335:
        return 'Profile', -1
    if p < 65:
        return 'QBack', -1
    if p < 115:
        return 'Back', 1
    if p < 155:
        return 'QBack', 1
    if p < 205:
        return 'Profile', 1
    if p < 270:
        return 'QFront', 1
    return 'QFront', -1


# ------------------------------------------------------------------------------------------------ behaviours
class Dangle:
    """Character Animator's Dangle: a verlet chain hanging from a handle; springs pull each segment toward its rest angle
    relative to its parent, gravity and damping act on the free particles."""

    def __init__(self, n, seg, stiff, gravity=2.6, damp=0.10):
        self.n, self.seg, self.stiff, self.g, self.damp = n, list(seg), list(stiff), gravity, damp
        self.p = None
        self.prev = None
        self.floor = None

    def step(self, root, base_ang, curv, seg_scale=1.0, dt=1 / FPS, sub=4):
        root = np.asarray(root, float)
        if self.p is None:
            self.p = self.rest(root, base_ang, curv, seg_scale)
            self.prev = self.p.copy()
            return self.p
        h = dt / sub
        for _ in range(sub):
            v = (self.p - self.prev) * (1 - self.damp)
            self.prev = self.p.copy()
            self.p = self.p + v
            self.p[1:, 1] -= self.g * h * h
            self.p[0] = root
            for _it in range(3):
                ang = base_ang
                for i in range(1, self.n):
                    L = self.seg[i - 1] * seg_scale
                    if i > 1:
                        d = self.p[i - 1] - self.p[i - 2]
                        ang = math.degrees(math.atan2(d[1], d[0])) + curv[i - 1]
                    tgt = self.p[i - 1] + L * np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                    self.p[i] += (tgt - self.p[i]) * self.stiff[i - 1]
                    d = self.p[i] - self.p[i - 1]
                    self.p[i] = self.p[i - 1] + d / (np.linalg.norm(d) + 1e-9) * L
                    if self.floor is not None and self.p[i, 1] < self.floor:
                        self.p[i, 1] = self.floor          # the porch boards: nothing dangles through them
        return self.p

    def rest(self, root, base_ang, curv, seg_scale=1.0):
        pts = [np.asarray(root, float)]
        ang = base_ang
        for i in range(1, self.n):
            if i > 1:
                ang += curv[i - 1]
            pts.append(pts[-1] + self.seg[i - 1] * seg_scale * np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]))
        return np.array(pts)

    def translate(self, d):
        if self.p is not None:
            self.p += d; self.prev += d


def blink_schedule(seed, t_end=32.0, lo=2.4, hi=4.6):
    rng = np.random.default_rng(seed)
    t, out = 0.8 + rng.uniform(0, 1.5), []
    while t < t_end:
        out.append(t)
        t += rng.uniform(lo, hi)
    return out


def blink_amount(t, sched):
    for b in sched:
        dtf = (t - b) * FPS
        if 0 <= dtf < 4:
            return [0.6, 1.0, 1.0, 0.45][int(dtf)]
    return 0.0


def wang(local_ang, mirror, rot):
    """a direction angle in a mirrored, rotated local frame -> world angle (deg)"""
    a = local_ang + rot
    return a if mirror > 0 else 180 - a


# ------------------------------------------------------------------------------------------------ dog runtime
xs = np.array(CAP['x'])
D = np.concatenate([[0], np.cumsum(np.abs(np.diff(xs)))])
D_strict = D + np.arange(N) * 1e-7
STRIDE = 0.50
GAIT = {'HN': 0.0, 'FN': 0.25, 'HF': 0.5, 'FF': 0.75}
STANCE = 0.62


def x_at_D(d):
    return float(np.interp(d, D_strict, xs))


def trig_time(name):
    return next(e['t'] for e in TRIG if e['trigger'] == name)


def head_anchor_side(h, rest, lie):
    """Side-view head pivot (body local) and pitch from the head height control, chin-rest and lying."""
    ks = [(0.15, (0.49, 0.30), -30), (0.45, (0.50, 0.335), -20), (0.9, (0.40, 0.67), 6), (1.25, (0.38, 0.72), 12)]
    h = min(max(h, ks[0][0]), ks[-1][0])
    for (h0, a0, p0), (h1, a1, p1) in zip(ks, ks[1:]):
        if h <= h1:
            u = (h - h0) / (h1 - h0)
            a, p = lerp2(a0, a1, u), lerp(p0, p1, u)
            break
    rest_a, rest_p = np.array([0.40, 0.375]), -5.0
    return lerp2(a, rest_a, rest), lerp(p, rest_p, rest)


class DogRig:
    def __init__(self):
        self.tail = Dangle(7, [0.075] * 6, [0.55, 0.42, 0.32, 0.24, 0.17, 0.12], gravity=2.2, damp=0.12)
        self.ears = {'near': Dangle(3, [0.07, 0.06], [0.6, 0.22], gravity=3.0, damp=0.08),
                     'far': Dangle(3, [0.065, 0.055], [0.6, 0.22], gravity=3.0, damp=0.08)}
        self.blinks = blink_schedule(7)
        self.prev_view = None
        self.prev_hview = None
        self.gaze_off = np.zeros(2)
        self.turn_phase = 0.0
        self.prev_theta = 0.0

    def controls(self, i):
        t = i / FPS
        c = {k: CAP[k][i] for k in ['lie', 'crouch', 'head', 'ear', 'tail', 'wag', 'rest', 'look', 'moving']}
        c['x'] = xs[i]
        theta = interp_keys(TURN['body_yaw'], t)
        phi = interp_keys(TURN['head_yaw'], t)
        c['theta'], c['phi'] = theta, phi
        c['tilt'] = interp_keys(TURN['head_tilt'], t)
        # editor gates (see takes.json editor_corrections)
        if 3.42 <= t < 4.30:
            c['lie'] = 0.0                                    # no lying mid-turn
        elif 4.30 <= t < 5.2:
            c['lie'] = ramp(t, 4.30, 5.0)
        if 7.42 <= t < 7.60:
            c['lie'] = 1.0 - 0.15 * ramp(t, 7.42, 7.60)       # still down while the head comes round
        elif 7.60 <= t < 8.10:
            c['lie'] = (1 - ramp(t, 7.60, 8.05)) * 0.85
        if t >= 26.4:
            hold = ramp(t, 26.42, 26.80) * (1 - ramp(t, 28.02, 28.40))
            c['look'] = hold
            c['rest'] = (1 - hold) * max(CAP['rest'][i], ramp(t, 28.1, 28.7)) if t > 28.0 else (1 - hold) * c['rest']
            c['head'] = lerp(CAP['head'][i], 0.8, hold)
        if 14.7 <= t < 23.79:
            c['head'] = min(c['head'], 0.47)
        return c

    def frame(self, i, person_pts):
        t = i / FPS
        c = self.controls(i)
        X = c['x']
        view, bm = body_view(c['theta'])
        hview, hm = head_view(c['phi'])
        V = BODY_VIEWS[view]
        lie = c['lie']
        lie_e = ease(lie)
        drop = 0.27 * lie_e + 0.07 * c['crouch'] * (1 - lie_e)
        pitch = -3.0 * c['crouch'] * (1 - lie_e)
        f = bm           # body forward direction in world x for Side; mirror for others
        items = []

        def B(pts, sc=(1, 1), piv=(0, 0)):    # body local -> world
            return xform(pts, origin=(X, -drop), mirror=bm, rot_deg=pitch, scale=sc, pivot=piv)

        def Bp(p):
            return B(np.array([p]))[0]

        # breathe (on the torso group only): slow and deep lying, quicker when afraid
        if lie_e > 0.5:
            per, amp = (0.9 if 4.3 < t < 7.6 else 2.3), 0.028
        else:
            per, amp = 1.05, 0.014
        br = 1 + amp * math.sin(2 * math.pi * t / per)
        tsc = (1, br)
        tpiv = (0, 0.30)

        def add(name, pts, col, z, stitch=False, shadow=True, tex='felt'):
            items.append({'n': name, 'g': 'dog', 'pts': np.asarray(pts, float), 'col': col, 'z': z, 'st': stitch, 'sh': shadow, 'tex': tex})

        zt = 30
        add('Dog/Body/%s/Torso' % view, B(cr(V['torso']), tsc, tpiv), C['tan'], zt, stitch=True)
        add('Dog/Body/%s/Saddle' % view, B(cr(V['saddle']), tsc, tpiv), C['saddle'], zt + 1)
        if V['bib']:
            add('Dog/Body/%s/Bib' % view, B(cr(V['bib']), tsc, tpiv), C['cream'], zt + 2)
        for k, (cx, cy, rx, ry, rot) in enumerate(V['haunch']):
            add('Dog/Body/%s/Haunch%d' % (view, k), B(ellipse(cx, cy, rx, ry, rot)), C['tan'], zt + 3, stitch=True)
        for k, (cx, cy, rx, ry, rot) in enumerate(V['shoulder']):
            add('Dog/Body/%s/Shoulder' % view, B(ellipse(cx, cy, rx, ry, rot)), C['tan'], zt + 3)

        # ---- legs (Walk behaviour + IK); feet planted from distance travelled
        dth = abs(c['theta'] - self.prev_theta)
        self.turn_phase += dth / 45.0
        self.prev_theta = c['theta']
        feet_world = {}
        for leg, joint in V['legs'].items():
            front = leg[0] == 'F'
            near = leg[1] == 'N'
            jw = Bp(joint)
            if view == 'Side':
                cyc = D[i] / STRIDE + GAIT[leg]
                n = math.floor(cyc); u = cyc - n
                lx = joint[0]

                def plant(k):
                    dpl = (k - GAIT[leg] + STANCE / 2) * STRIDE
                    return x_at_D(dpl) + f * lx
                if u < STANCE:
                    fx, fy = plant(n), 0.0
                else:
                    s = (u - STANCE) / (1 - STANCE)
                    fx = lerp(plant(n), plant(n + 1), ease(s))
                    fy = 0.055 * math.sin(math.pi * s) * min(1.0, c['moving'] * 1.5)
                gait_foot = np.array([fx, fy])
                fold_local = (0.60 if front else -0.12, 0.015) if near else (0.64 if front else -0.08, 0.02)
                fold = xform(np.array([fold_local]), origin=(X, 0), mirror=bm)[0]
                foot = lerp2(gait_foot, fold, lie_e)
            else:
                lift = 0.045 * max(0.0, math.sin(self.turn_phase * math.pi + GAIT[leg] * 2 * math.pi)) if dth > 0.5 else 0.0
                foot = np.array([jw[0] + (0.01 if front else -0.01) * bm, lift])
            feet_world[leg] = foot
            col = C['tan'] if near else dk(C['tan'])
            pawcol = C['cream'] if near else dk(C['cream'])
            zl = (zt + 6) if near else (zt - 8)
            if view in ('Back', 'Quarter') and front:
                zl = zt - 9 if not near else zt - 7
            if front:
                wrist_off = lerp2((0.0, 0.055), (-0.07 * 1, 0.012), lie_e)
                wrist = foot + np.array([wrist_off[0] * f if view == 'Side' else 0.0, wrist_off[1]])
                m, wpt = ik2(jw, wrist, 0.22, 0.19, bend=-f if view == 'Side' else 1)
                if view != 'Side':
                    m = (jw + wpt) / 2 + np.array([0.0, 0.0])
                path = smooth_path([jw, m, wpt, foot + np.array([0.02 * f if view == 'Side' else 0, 0.012])], n=4)
                add('Dog/Legs/%s' % leg, strip(path, [0.055, 0.045, 0.034, 0.03]), col, zl)
            else:
                hock_off = lerp2((-0.045, 0.13), (-0.17, 0.03), lie_e)
                hock = foot + np.array([hock_off[0] * f if view == 'Side' else 0.0, hock_off[1]])
                m, hk = ik2(jw, hock, 0.23, 0.20, bend=f if view == 'Side' else 1)
                if view != 'Side':
                    m = (jw + hk) / 2
                path = smooth_path([jw, m, hk, foot + np.array([0.02 * f if view == 'Side' else 0, 0.012])], n=4)
                add('Dog/Legs/%s' % leg, strip(path, [0.075, 0.05, 0.03, 0.03]), col, zl)
            pw = 0.048 if view == 'Side' else 0.034
            add('Dog/Legs/%s/Paw' % leg, ellipse(foot[0] + (0.025 * f if view == 'Side' else 0), foot[1] + 0.02, pw, 0.022), pawcol, zl + 0.5)

        # ---- head (Head & Body Turner swap set) + neck
        HV = HEAD_VIEWS[hview]
        dyaw = (c['phi'] - c['theta'] + 180) % 360 - 180
        over = ease((abs(dyaw) - 60) / 80.0) if view == 'Side' else 0.0
        if view == 'Side':
            anc_l, hp = head_anchor_side(c['head'], c['rest'], lie)
            anc_l = lerp2(anc_l, (0.22, 0.66), over)
            hp = lerp(hp, 4.0, over)
            if c['look'] > 0:   # Look In: the neck reaches forward, low, into the room
                anc_l = lerp2(anc_l, (0.56, 0.52), c['look'])
                hp = lerp(hp, 10.0, c['look'])
        else:
            anc_l = np.array(V['neck']) + np.array([0.0, 0.06 + 0.10 * (c['head'] - 0.6)])
            hp = 0.0
        hp += c['tilt'] * 0.0
        anc = Bp(anc_l)
        # Eye Gaze behaviour also nudges the head a little toward the target (Character Animator's head turner/face)
        tgt = self.gaze_target(t, person_pts, X, f)
        hrot = hp + pitch * bm
        rel = tgt - (anc + np.array([0.15 * hm, 0.08]))
        tg_ang = math.degrees(math.atan2(rel[1], abs(rel[0]) + 1e-6))
        hrot += max(-8.0, min(8.0, 0.22 * tg_ang)) if hview in ('Profile', 'QFront') else 0.0
        hrot += c['tilt']
        hz = 40 if view == 'Side' else 12

        def Hd(pts):
            return xform(pts, origin=anc, mirror=hm, rot_deg=hrot)

        def Hp(p):
            return Hd(np.array([p]))[0]

        if view == 'Side':
            nb = Bp(V['neck'])
            neck_end = Hp((-0.01, 0.05))
            npath = np.array([nb, lerp2(nb, neck_end, 0.5) + np.array([0, 0.015]), neck_end])
            add('Dog/Neck', strip(npath, [0.105, 0.085, 0.07], cap=True), C['tan'], 38)
            cpt = lerp2(nb, neck_end, 0.62)
            dvec = neck_end - nb
            dn = dvec / (np.linalg.norm(dvec) + 1e-9)
            pn = np.array([-dn[1], dn[0]])
            add('Dog/Neck/Collar', strip(np.array([cpt - pn * 0.085, cpt + pn * 0.085]), [0.018, 0.018], cap=False), C['collar'], 39, shadow=True)
            add('Dog/Neck/Collar/Tag', ellipse(*(cpt - pn * 0.09 * (1 if (cpt - pn * 0.09)[1] < (cpt + pn * 0.09)[1] else -1)), 0.016, 0.016), C['tag'], 39.5)
        if HV.get('skull') is not None:
            add('Dog/Head/%s/Skull' % hview, Hd(cr(HV['skull'])), C['tan'], hz, stitch=True)
        else:
            add('Dog/Head/%s/Skull' % hview, Hd(ellipse(*HV['skull_e'])), C['tan'], hz, stitch=True)
        if 'muzzle_behind' in HV:
            add('Dog/Head/%s/Muzzle' % hview, Hd(cr(HV['muzzle_behind'])), C['cream'], hz - 0.6)
            add('Dog/Head/%s/Nose' % hview, Hd(ellipse(*HV['nose_behind'])), C['nose'], hz - 0.5)
        add('Dog/Head/%s/Cap' % hview, Hd(cr(HV['cap'])), C['saddle'], hz + 0.5)
        if 'ruff' in HV:
            add('Dog/Head/%s/Ruff' % hview, Hd(cr(HV['ruff'])), C['cream'], hz + 0.6)
        if 'muzzle' in HV:
            add('Dog/Head/%s/Muzzle' % hview, Hd(cr(HV['muzzle'])), C['cream'], hz + 0.7)
        if 'blaze' in HV:
            add('Dog/Head/%s/Blaze' % hview, Hd(cr(HV['blaze'])), C['cream'], hz + 0.75)
        if 'nose' in HV:
            add('Dog/Head/%s/Nose' % hview, Hd(ellipse(*HV['nose'])), C['nose'], hz + 0.9)
        if HV.get('mouth'):
            add('Dog/Head/%s/Mouth' % hview, strip(Hd(np.array(HV['mouth'])), [0.005, 0.006, 0.004], cap=True), C['nose'], hz + 0.95, shadow=False)

        # Eye Gaze (snap) + Auto Blink
        blink = blink_amount(t, self.blinks)
        relaxed = 0.35 * c['rest'] * (1 - c['look'])
        fear = c['crouch'] * (1 - lie_e)
        lid = max(blink, relaxed)
        ev = tgt - Hp((0.13, 0.095))
        # into head-local unmirrored frame
        a = math.radians(hrot)
        lx_, ly_ = ev[0] * hm, ev[1]
        lxr = math.cos(-a) * lx_ - math.sin(-a) * ly_
        lyr = math.sin(-a) * lx_ + math.cos(-a) * ly_
        dirn = np.array([lxr, lyr]) / (math.hypot(lxr, lyr) + 1e-9)
        goal = np.array([max(-0.35, dirn[0]), dirn[1] * 0.9])
        self.gaze_off += (goal - self.gaze_off) * 0.6          # 2-frame saccade
        for k, (ex, ey, rx, ry) in enumerate(HV['eyes']):
            zc = hz + 1.0 + k * 0.01
            add('Dog/Head/%s/Eye%d/White' % (hview, k), Hd(ellipse(ex, ey, rx, ry * (1 + 0.25 * fear))), C['white'], zc, shadow=False)
            ox, oy = self.gaze_off[0] * rx * 0.42, self.gaze_off[1] * ry * 0.38
            ir = ry * 0.78
            add('Dog/Head/%s/Eye%d/Iris' % (hview, k), Hd(ellipse(ex + ox, ey + oy, ir * 0.9, ir)), C['iris'], zc + 0.1, shadow=False)
            add('Dog/Head/%s/Eye%d/Pupil' % (hview, k), Hd(ellipse(ex + ox * 1.15, ey + oy * 1.1, ir * 0.48, ir * 0.55)), C['pupil'], zc + 0.2, shadow=False)
            add('Dog/Head/%s/Eye%d/Glint' % (hview, k), Hd(ellipse(ex + ox * 1.15 + rx * 0.18, ey + oy + ry * 0.25, rx * 0.12, rx * 0.12)), C['white'], zc + 0.3, shadow=False)
            if lid > 0.02:
                top = ey + ry * 1.25
                bot = ey + ry * 1.25 - 2.5 * ry * lid
                lidp = [(ex - rx * 1.25, top), (ex + rx * 1.25, top), (ex + rx * 1.25, bot + ry * 0.2), (ex, bot - ry * 0.15), (ex - rx * 1.25, bot + ry * 0.2)]
                add('Dog/Head/%s/Eye%d/Blink' % (hview, k), Hd(cr(lidp, n=5)), C['tan'], zc + 0.4, shadow=False)
            # brow: worried when afraid, soft when settled
            br_in = 0.012 + 0.018 * fear
            add('Dog/Head/%s/Eye%d/Brow' % (hview, k), strip(Hd(np.array([(ex - rx * 1.0, ey + ry * 1.45), (ex, ey + ry * 1.6 + br_in * 0.5), (ex + rx * 1.0, ey + ry * 1.45 + br_in)])), [0.006, 0.008, 0.006]), C['saddle'], zc + 0.5, shadow=False)

        # Dangle: ears
        if hview != self.prev_hview and self.prev_hview is not None:
            for k in ('near', 'far'):
                self.ears[k].translate(Hp(HV['ears'][k]) - self.ears[k].p[0])
        for k in ('near', 'far'):
            root = Hp(HV['ears'][k])
            a_flat, a_up = HV['ear_dir'][k]
            ea = lerp(a_flat, a_up, min(1.0, max(0.0, c['ear'])))
            base = wang(ea, hm, hrot)
            tipc = -32.0 * c['ear'] * hm
            pts = self.ears[k].step(root, base, [0, 0, tipc])
            path = smooth_path(pts, n=5)
            behind = HV['far_ear_behind'] and k == 'far'
            zc = (hz - 0.8) if behind else (hz + 1.6)
            col = dk(C['saddle'], 0.8) if behind else C['saddle']
            add('Dog/Head/%s/Ear %s' % (hview, k), strip(path, [0.042, 0.036, 0.012], cap=True), col, zc)
            if not behind and hview in ('Back', 'QBack'):
                add('Dog/Head/%s/Ear %s/Inner' % (hview, k), strip(path[: max(2, len(path) * 2 // 3)], [0.012, 0.010, 0.004], cap=True), dk(C['saddle'], 0.75), zc + 0.1, shadow=False)
            elif behind and hview in ('Profile', 'QFront'):
                pass
            else:
                add('Dog/Head/%s/Ear %s/Inner' % (hview, k), strip(path[: max(2, len(path) * 2 // 3)], [0.018, 0.016, 0.005], cap=True), C['pink'], zc + 0.1, shadow=False)
        self.prev_hview = hview

        # Dangle: tail
        if view != self.prev_view and self.prev_view is not None:
            self.tail.translate(Bp(V['tail_root']) - self.tail.p[0])
        root = Bp(V['tail_root'])
        self.tail.floor = 0.012 if X > WALL_OUT - 0.2 else None
        tl = c['tail'] / 1.35
        wag = c['wag'] * 26 * math.sin(2 * math.pi * 2.3 * t)
        if view == 'Side':
            base_l = 35 - 115 * tl + wag
            base = wang(180 - base_l, bm, pitch)
            curv_l = lerp(6.0, -12.0, tl)
            curv = [0] + [(-curv_l if bm > 0 else curv_l)] * 6
            segsc = 1.0
        elif view == 'Quarter':
            base = wang(180 - (10 - 100 * tl) - 25, bm, 0) + wag * 0.6
            curv = [0] + [(-4 if bm > 0 else 4)] * 6
            segsc = 0.85
        else:   # Back: tail seen end-on hangs over the rump, wag sweeps sideways
            base = -90 + 70 * (1 - tl) * 0.0 + 90 * (1 - min(1, tl * 1.6)) + wag * 1.8
            curv = [0] + [0] * 6
            segsc = 0.75 - 0.2 * (1 - tl)
        tp = self.tail.step(root, base, curv, seg_scale=segsc)
        tpath = smooth_path(tp, n=4)
        tz = (zt - 2) if view == 'Side' else (zt + 8)
        add('Dog/Tail', strip(tpath, [0.035, 0.045, 0.045, 0.04, 0.034, 0.024, 0.012]), C['tan'], tz, stitch=False)
        tipn = max(3, len(tpath) // 3)
        add('Dog/Tail/Tip', strip(tpath[-tipn:], [0.03, 0.022, 0.011]), C['cream'], tz + 0.2, shadow=False)
        self.prev_view = view

        # contact shadow on the porch
        ext = 0.48 if view == 'Side' else (0.30 if view == 'Quarter' else 0.2)
        items.append({'n': 'Dog/ContactShadow', 'g': 'shadow', 'pts': ellipse(X, 0.0, ext + 0.1 * lie_e, 0.035), 'col': (0, 0, 0), 'z': 1, 'st': False, 'sh': False, 'tex': 'shadow'})

        muzzle = Hp(HV['muzzle_tip'])
        state = {'view': view, 'head_view': hview, 'body_mirror': bm, 'head_mirror': hm, 'X': X, 'lie': lie, 'look': c['look'],
                 'head_anchor': anc.tolist(), 'muzzle': muzzle.tolist(), 'back_line_y': float(Bp((0.0, 0.60))[1]),
                 'head_top_y': float(max(p[1] for it in items if it['n'].startswith('Dog/Head') and 'Ear' not in it['n'] for p in it['pts'])),
                 'feet': {k: v.tolist() for k, v in feet_world.items()}, 'tail_tip': tp[-1].tolist(), 'ear_tip': self.ears['near'].p[-1].tolist(),
                 'gaze_target': tgt.tolist(), 'blink': blink, 'theta': c['theta'], 'phi': c['phi']}
        return items, state

    def gaze_target(self, t, P, X, f):
        name = GAZE['events'][0][1]
        for tt, nm in GAZE['events']:
            if t >= tt:
                name = nm
        return np.array({'person_face': P['face'], 'person_hand': P['hand'], 'porch_end': (5.6, 0.5), 'floor_ahead': (X + f * 0.9, 0.0),
                         'door_light': (0.2, 1.3), 'sill': (0.45, 0.05), 'room': (-0.78, 1.1)}[name], float)


# ------------------------------------------------------------------------------------------------ person runtime
PHEAD = {
    'face': [(-0.08, 0.02), (-0.10, 0.16), (-0.06, 0.27), (0.04, 0.31), (0.13, 0.27), (0.165, 0.18), (0.175, 0.12), (0.16, 0.05), (0.12, 0.0), (0.06, -0.025), (0.0, -0.02)],
    'hair': [(-0.13, 0.06), (-0.14, 0.20), (-0.09, 0.30), (0.02, 0.345), (0.12, 0.32), (0.18, 0.24), (0.14, 0.235), (0.08, 0.26), (0.02, 0.24), (-0.04, 0.17), (-0.06, 0.07)],
    'ear': (-0.045, 0.14, 0.03, 0.04), 'eyes': [(0.07, 0.165, 0.024, 0.02), (0.14, 0.162, 0.018, 0.017)], 'nose': [(0.155, 0.15), (0.185, 0.10), (0.155, 0.095)],
    'mouth': (0.105, 0.05), 'pony': (-0.11, 0.25),
}
VISEME_SHAPES = {   # (width, open height, teeth, tongue) in metres on the 3/4 face; jaw drop is open*0.6
    'Neutral': (0.050, 0.000, 0, 0), 'M': (0.044, 0.000, 0, 0), 'Ah': (0.054, 0.046, 1, 1), 'Ee': (0.064, 0.016, 1, 0),
    'Oh': (0.036, 0.040, 0, 1), 'W-Oo': (0.024, 0.022, 0, 0), 'Uh': (0.046, 0.028, 1, 1), 'S': (0.056, 0.010, 1, 0),
    'D': (0.048, 0.022, 1, 1), 'L': (0.048, 0.026, 1, 1), 'R': (0.034, 0.024, 0, 1), 'F': (0.046, 0.010, 1, 0),
}


class PersonRig:
    def __init__(self):
        self.pony = Dangle(5, [0.06, 0.06, 0.055, 0.05], [0.35, 0.12, 0.08, 0.05], gravity=9.0, damp=0.10)
        self.blinks = blink_schedule(11, lo=2.0, hi=4.0)
        self.feet = None

    def frame(self, i, dog_head):
        t = i / FPS
        px = PERS['x'][i]
        sit = ease(PERS['sit'][i])
        reach = PERS['reach'][i]
        low = PERS['low'][i]
        items = []

        def add(name, pts, col, z, stitch=False, shadow=True):
            items.append({'n': 'Person/' + name, 'g': 'person', 'pts': np.asarray(pts, float), 'col': col, 'z': z, 'st': stitch, 'sh': shadow, 'tex': 'felt'})

        # feet: two steps aside (4.8-5.4), then planted in front of the bench
        stand_feet = {'near': px + 0.05, 'far': px - 0.05}
        seat_x = PERSON_BESIDE - 0.05
        sit_feet = {'near': PERSON_BESIDE + 0.36, 'far': PERSON_BESIDE + 0.26}
        fn = lerp(-0.20 + 0.05, PERSON_BESIDE + 0.05, ramp(t, 4.80, 5.05))
        ff = lerp(-0.20 - 0.05, PERSON_BESIDE - 0.05, ramp(t, 5.05, 5.32))
        fn_l = 0.06 * math.sin(math.pi * min(1, max(0, (t - 4.80) / 0.25))) if 4.80 < t < 5.05 else 0
        ff_l = 0.06 * math.sin(math.pi * min(1, max(0, (t - 5.05) / 0.27))) if 5.05 < t < 5.32 else 0
        feet = {'near': np.array([lerp(fn, sit_feet['near'], sit), fn_l]), 'far': np.array([lerp(ff, sit_feet['far'], sit), ff_l])}
        hip_stand = np.array([(feet['near'][0] + feet['far'][0]) / 2, 0.80 - 0.02 * (fn_l + ff_l > 0)])
        hip_sit = np.array([seat_x, 0.47])
        hip = lerp2(hip_stand, hip_sit, sit)
        # torso lean: calls lean in, the reach leans more, pulling the door and offering the low hand lean right down
        door_pull = ramp(t, 6.10, 6.35) * (1 - ramp(t, 6.62, 6.85))
        call1 = ramp(t, 1.0, 1.15) * (1 - ramp(t, 2.1, 2.4))
        lean = 5 * call1 + 16 * reach + 24 * door_pull + 27 * low * (1 - door_pull) * (1 - 0.7 * ramp(t, 26.1, 26.7))
        T = lambda p: xform(np.array([p]), origin=hip, rot_deg=-lean)[0]
        Tp = lambda pts: xform(pts, origin=hip, rot_deg=-lean)
        torso = [(-0.13, -0.03), (-0.155, 0.2), (-0.13, 0.34), (-0.06, 0.39), (0.07, 0.39), (0.13, 0.33), (0.155, 0.18), (0.13, -0.03)]
        # legs
        for k, side in ((0, 'far'), (1, 'near')):
            hj = hip + np.array([0.05 if side == 'near' else -0.05, 0.0])
            m, e = ik2(hj, feet[side] + np.array([0, 0.07]), 0.42, 0.37, bend=1)
            col = C['trousers'] if side == 'near' else dk(C['trousers'])
            add('Legs/%s' % side, strip(smooth_path([hj, m, e], n=4), [0.075, 0.06, 0.05]), col, 180 + k * 10)
            add('Legs/%s/Shoe' % side, ellipse(feet[side][0] + 0.05, feet[side][1] + 0.035, 0.085, 0.04), C['shoe'] if side == 'near' else dk(C['shoe']), 180.5 + k * 10)
        add('Torso', Tp(cr(torso)), C['sweater'], 195, stitch=True)
        add('Torso/Hem', strip(Tp(np.array([(-0.135, -0.01), (0.0, -0.02), (0.135, -0.01)])), [0.02, 0.02, 0.02], cap=False), dk(C['sweater'], 0.8), 195.5, shadow=False)
        # head
        nk = T((0.0, 0.40))
        hrot = -lean * 0.4 + (6 if PERS['low'][i] > 0.5 else 0) * -1
        # head looks at the dog (Face behaviour), a little
        dh = np.asarray(dog_head) - nk
        hrot += max(-10, min(6, math.degrees(math.atan2(dh[1], abs(dh[0]))) * 0.25))
        vis = VIS[i]
        wv, ov, teeth, tongue = VISEME_SHAPES.get(vis, VISEME_SHAPES['Neutral'])
        jaw = ov * 0.6
        H = lambda pts: xform(pts, origin=nk + np.array([0, 0.02]), rot_deg=hrot)
        Hp = lambda p: H(np.array([p]))[0]
        add('Neck', strip(np.array([T((0.0, 0.36)), nk + np.array([0, 0.05])]), [0.045, 0.04], cap=True), C['skin'], 196)
        face = [(x, y - jaw * (1 - min(1, y / 0.12)) if y < 0.12 else y) for x, y in PHEAD['face']]
        # ponytail (Dangle)
        root = Hp(PHEAD['pony'])
        pp = self.pony.step(root, wang(250, 1, hrot), [0, 8, 6, 4, 3])
        add('Head/Ponytail', strip(smooth_path(pp, n=4), [0.04, 0.045, 0.04, 0.03, 0.012]), dk(C['hair'], 0.9), 196.5)
        add('Head/Face', H(cr(face)), C['skin'], 197, stitch=True)
        add('Head/Ear', H(ellipse(*PHEAD['ear'])), dk(C['skin'], 0.92), 197.2)
        add('Head/Hair', H(cr(PHEAD['hair'])), C['hair'], 197.5, stitch=True)
        add('Head/Cheek', H(ellipse(0.12, 0.09, 0.025, 0.016)), C['cheek'], 197.3, shadow=False)
        add('Head/Nose', H(cr(PHEAD['nose'], n=4)), dk(C['skin'], 0.85), 197.6, shadow=False)
        # eyes: blink + gaze to the dog
        blink = blink_amount(t, self.blinks)
        soft = PERS['sit'][i]
        lid = max(blink, 0.25 * soft)
        for k, (ex, ey, rx, ry) in enumerate(PHEAD['eyes']):
            add('Head/Eye%d/White' % k, H(ellipse(ex, ey, rx, ry)), C['white'], 197.8, shadow=False)
            gx = 0.35 * rx * (1 if dh[0] > 0 else -1)
            gy = max(-0.5, min(0.3, dh[1] / 1.5)) * ry
            add('Head/Eye%d/Pupil' % k, H(ellipse(ex + gx, ey + gy, rx * 0.5, ry * 0.62)), C['pupil'], 197.9, shadow=False)
            if lid > 0.02:
                top, bot = ey + ry * 1.2, ey + ry * 1.2 - 2.4 * ry * lid
                add('Head/Eye%d/Blink' % k, H(cr([(ex - rx * 1.2, top), (ex + rx * 1.2, top), (ex + rx * 1.2, bot + ry * 0.2), (ex, bot - ry * 0.1), (ex - rx * 1.2, bot + ry * 0.2)], n=4)), C['skin'], 198, shadow=False)
            calling = PERS['reach'][i] > 0.3 or call1 > 0.5
            by = ey + ry * (1.9 + (0.5 if calling else 0.0))
            add('Head/Eye%d/Brow' % k, strip(H(np.array([(ex - rx, by - 0.004), (ex, by + 0.004), (ex + rx, by - 0.002 + (0.006 if not calling else -0.004))])), [0.006, 0.007, 0.005]), C['hair'], 198.1, shadow=False)
        # mouth swap set: viseme from the audio (Lip Sync behaviour)
        mx, my = PHEAD['mouth']
        my -= jaw * 0.5
        if ov < 0.004:
            add('Head/Mouth/%s' % vis, strip(H(np.array([(mx - wv / 2, my + 0.003), (mx, my - 0.002), (mx + wv / 2, my + 0.004)])), [0.006 if vis == 'M' else 0.004] * 3), C['lip'], 198.2, shadow=False)
        else:
            mo = H(ellipse(mx, my, wv / 2, ov / 2 + 0.004))
            add('Head/Mouth/%s' % vis, mo, C['mouth'], 198.2, shadow=False)
            if teeth:
                add('Head/Mouth/%s/Teeth' % vis, H(ellipse(mx, my + ov / 2 - 0.002, wv * 0.36, 0.006)), C['teeth'], 198.3, shadow=False)
            if tongue:
                add('Head/Mouth/%s/Tongue' % vis, H(ellipse(mx, my - ov / 2 + 0.006, wv * 0.3, 0.007)), C['tongue'], 198.3, shadow=False)
            add('Head/Mouth/%s/Lips' % vis, strip(H(ellipse(mx, my, wv / 2 + 0.003, ov / 2 + 0.007, n=24)), [0.004] * 3, cap=False), C['lip'], 198.4, shadow=False)
        # arms: far arm idle / on the knee; near arm: pat (call 1), reach (call 2), pull the door, offer the hand low
        for k, side in ((0, 'far'), (1, 'near')):
            sh = T((0.075, 0.34) if side == 'near' else (-0.06, 0.35))
            idle = hip + np.array([0.10 if side == 'near' else -0.02, 0.0]) if sit < 0.5 else hip + np.array([0.30 if side == 'near' else 0.22, 0.07])
            idle = lerp2(hip + np.array([0.11 if side == 'near' else -0.03, -0.02]), hip + np.array([0.32 if side == 'near' else 0.24, 0.08]), sit)
            hand = idle
            if side == 'near':
                pat = hip + np.array([0.14, -0.08 + 0.03 * abs(math.sin(2 * math.pi * 2.6 * t))])
                hand = lerp2(hand, pat, call1)
                reach_t = sh + np.array([0.58, -0.16])
                hand = lerp2(hand, reach_t, reach)
                ang = door_angle(t)
                edge = np.array([WALL_IN - DOOR_W * math.sin(math.radians(ang)) + 0.02, 0.95])
                hand = lerp2(hand, edge, door_pull)
                lowt = np.array([-0.50, 0.27])
                hand = lerp2(hand, lowt, low * (1 - door_pull) * (1 - ramp(t, 26.1, 26.7)))
            m, e = ik2(sh, hand, 0.31, 0.29, bend=-1)
            col = C['sweater'] if side == 'near' else dk(C['sweater'])
            z = 199 if side == 'near' else 185
            add('Arm/%s' % side, strip(smooth_path([sh, m, e], n=4), [0.05, 0.042, 0.036]), col, z)
            palm_up = side == 'near' and low > 0.5 and door_pull < 0.5
            add('Arm/%s/Hand' % side, ellipse(e[0] + 0.03, e[1] - (0.0 if palm_up else 0.01), 0.055 if palm_up else 0.04, 0.025 if palm_up else 0.04, rot=0.15 if palm_up else 0), C['skin'] if side == 'near' else dk(C['skin']), z + 0.3)
        P = {'face': Hp((0.06, 0.15)).tolist(), 'hand': e.tolist() if False else None}
        hand_near = [it for it in items if it['n'] == 'Person/Arm/near/Hand'][0]['pts'].mean(0)
        P['hand'] = hand_near.tolist()
        return items, P


def door_angle(t):
    return lerp(36.0, 92.0, ramp(t, 6.15, 6.75))


def main():
    dog, person = DogRig(), PersonRig()
    cams = camera_track()
    frames, states, events = [], [], {'feet': [], 'door': [6.15, 6.75], 'person_steps': [4.8, 5.05], 'sit': 5.5}
    prevfeet = None
    P = {'face': (-0.1, 1.4), 'hand': (0.0, 0.9)}
    dog_head = (3.2, 0.7)
    for i in range(N):
        pit, P = person.frame(i, dog_head)
        dit, st = dog.frame(i, P)
        dog_head = st['head_anchor']
        st['person'] = P
        st['door_angle'] = door_angle(i / FPS)
        st['cam'] = cams[i]
        if prevfeet:
            for k, v in st['feet'].items():
                if prevfeet[k][1] > 0.004 and v[1] <= 0.004:
                    events['feet'].append([round(i / FPS, 3), k, round(v[0], 3)])
        prevfeet = st['feet']
        frames.append(pit + dit)
        states.append(st)
    pickle.dump({'frames': frames, 'states': states}, open(os.path.join(CACHE, 'rig.pkl'), 'wb'))
    json.dump(events, open(os.path.join(CACHE, 'events.json'), 'w'))
    print('rig: %d frames, %d footfalls' % (len(frames), len(events['feet'])))
    # puppet export (PSD-style tree; the geometry is in this file)
    names = sorted({it['n'].split('/Eye')[0] for fr in frames for it in fr})
    tree = {'about': 'SCION 22 puppets as Character Animator would see them: named groups, swap sets, behaviours. Geometry: build/rig.py (drawn here, in metres).',
            'Dog': {'swap_sets': {'Body views (Head & Body Turner)': list(BODY_VIEWS), 'Head views': list(HEAD_VIEWS)},
                    'behaviours': ['Triggers (Take 2)', 'Head & Body Turner (Take 3)', 'Eye Gaze, snap (Take 4)', 'Auto Blink', 'Breathe',
                                   'Dangle: Ear near, Ear far, Tail', 'Walk (planted feet from distance travelled)', 'Limb IK (front: shoulder-elbow-wrist; hind: hip-stifle-hock)'],
                    'layers_seen': [n for n in names if n.startswith('Dog')]},
            'Person': {'swap_sets': {'Mouth (Lip Sync visemes)': list(VISEME_SHAPES)},
                       'behaviours': ['Lip Sync (visemes from voice audio)', 'Auto Blink', 'Dangle: Ponytail', 'Face (head toward the dog)', 'Limb IK', 'Take 5 (position, sit, reach, low hand)'],
                       'layers_seen': [n for n in names if n.startswith('Person')]}}
    json.dump(tree, open(os.path.join(FOLDER, 'puppet', 'puppets.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
