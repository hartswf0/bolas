"""The dog: segmented from one historical frame (Amateur Film New Jersey C, frame 11 of the kit clip), with a low head and
a tail transplanted from frame 18 of the same clip. All cut lines and pivots are inferred keys of this swarm (drawn
nodes); the mattes they cut are the documented SAM masks."""
from ops import poly_alpha

DOG = 'paeleo/handmade/kit/archive-dog/'
DOG_ID = 'NJC:2fdacde1-8a23-58e1-b905-5407385bd039'
DOG_TITLE = 'Amateur Film New Jersey C (Home Movies, Internet Archive)'
DOG_URL = 'https://archive.org/details/NewJerseyC'

# inferred keys, frame-11 pixel space (x right, y down). The dog faces left in frame 11.
K11 = {
    'neck_cut': [[60, 60], [132, 60], [150, 98], [134, 124], [114, 154], [60, 154]],
    'neck_cut_body': [[60, 60], [126, 60], [142, 100], [126, 124], [106, 150], [60, 150]],
    'head_pivot': [138, 112],
    'F1': [[96, 150], [128, 150], [124, 172], [111, 194], [106, 202], [80, 202], [90, 186], [104, 168]],
    'F2': [[128, 150], [158, 150], [156, 206], [124, 206]],
    'H': [[166, 140], [214, 140], [214, 206], [166, 206]],
    'legs_below': [[60, 162], [230, 162], [230, 215], [60, 215]],
    'F1_pivot': [118, 152], 'F1_foot': [97, 196],
    'F2_pivot': [140, 152], 'F2_foot': [141, 202],
    'H_pivot': [190, 146], 'H_foot': [190, 200],
    'tail_root': [204, 124],
    'back_line_y': 110, 'belly_y': 156, 'ground_y': 201,
}
# frame 18: the head carried low and the tail
K18 = {
    'head_cut': [[100, 118], [152, 118], [160, 134], [150, 160], [128, 182], [118, 200], [100, 200]],
    'head_pivot': [150, 132],
    'tail_cut': [[214, 136], [246, 136], [246, 182], [214, 182]],
    'tail_root': [219, 141],
}


import math
import numpy as np


def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def R(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def S(sx, sy=None):
    return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], float)


def ap(M, p):
    v = M @ np.array([p[0], p[1], 1.0]); return np.array([v[0], v[1]])


ANCHOR = np.array([165.0, 152.0])     # body anchor in frame-11 px: mid back between shoulder and hip, belly height
LEGS = {  # name: (piece, pivot, foot, near?, gait phase offset)
    'nearH': ('H', K11['H_pivot'], K11['H_foot'], True, 0.0),
    'nearF': ('F2', K11['F2_pivot'], K11['F2_foot'], True, 0.25),
    'farH': ('H', K11['H_pivot'], K11['H_foot'], False, 0.5),
    'farF': ('F1', K11['F1_pivot'], K11['F1_foot'], False, 0.75),
}
FAR_OFFSET = {'farH': np.array([-7.0, -2.0]), 'farF': np.array([-4.0, -1.0])}   # the far legs sit a little forward/up


def gait_foot(s, phase0, stride, duty, A):
    """foot position relative to hip (rig px, + = behind) and lift, for body travel s (px, + = forward).
    Stance: foot planted in the world; swing: carried forward along an arc."""
    p = (s / stride + phase0) % 1.0
    if p < duty:                       # stance: rel goes -A -> +A linearly with travel => planted
        rel = -A + (p / duty) * 2 * A
        return rel, 0.0, True
    q = (p - duty) / (1 - duty)        # swing: +A -> -A, lifted
    rel = A - q * 2 * A
    lift = math.sin(q * math.pi) * 9.0
    return rel, lift, False


def leg_len(name):
    _, pv, ft, _, _ = LEGS[name]
    return float(np.hypot(ft[0] - pv[0], ft[1] - pv[1]))


def dog_layers(P, pose):
    """pose -> ordered layers [(piece, variant, M_piece_to_screen, role)]. Every placement is an affine of a node."""
    f = pose.get('facing', 1)            # 1 = faces left (as in f011), -1 = mirrored
    k = pose['k']
    X, Y = pose['root']
    gy = K11['ground_y']
    Mroot = T(X, Y) @ S(k * f, k) @ T(-ANCHOR[0], -gy)
    lie = pose.get('lie', 0.0); crouch = pose.get('crouch', 0.0)
    dy = crouch * 9.0 + lie * (gy - K11['belly_y'] - 3)
    br = pose.get('breath', 0.0)
    Mb = T(0, dy) @ T(ANCHOR[0], K11['belly_y']) @ S(1.0, 1.0 + 0.012 * br) @ T(-ANCHOR[0], -K11['belly_y']) @ T(*ANCHOR) @ R(pose.get('body_rot', 0.0)) @ T(*(-ANCHOR))
    out = []
    walk = pose.get('walk', 0.0); s = pose.get('s', 0.0)
    stride = pose.get('stride', 70.0); duty = 0.62; A = stride * duty / 2
    legs = {}
    for name, (pc, pv, ft, near, ph) in LEGS.items():
        pvw = ap(Mb, pv) + FAR_OFFSET.get(name, 0)
        v0 = np.array(ft, float) - np.array(pv, float)
        rest = np.array([pvw[0] + v0[0] * (1 - 0.25 * crouch), gy])
        if walk > 0:
            rel, lift, _ = gait_foot(s, ph, stride, duty, A)
            wt = np.array([pvw[0] + rel + (v0[0] * 0.3), gy - lift])
            tgt = rest * (1 - walk) + wt * walk
        else:
            tgt = rest
        vs = tgt - pvw
        L = np.hypot(*v0)
        if lie > 0:
            if name.endswith('F'):
                vl = np.array([-L * 0.98, max(2.0, gy - pvw[1] - 3)])
            else:
                vl = np.array([-L * 0.80, max(2.0, gy - pvw[1] - 6)])
            a_s, a_l = math.atan2(vs[1], vs[0]), math.atan2(vl[1], vl[0])
            n_s, n_l = np.hypot(*vs), np.hypot(*vl)
            a = a_s + (a_l - a_s) * lie; n = n_s + (n_l - n_s) * lie
            vs = np.array([math.cos(a) * n, math.sin(a) * n])
        ang = math.degrees(math.atan2(vs[1], vs[0]) - math.atan2(v0[1], v0[0]))
        sc = float(np.clip(np.hypot(*vs) / L, 0.55, 1.2))
        org = P[pc]['origin']
        M = Mroot @ T(*pvw) @ R(ang) @ S(sc) @ T(-pv[0], -pv[1]) @ T(*org)
        legs[name] = (pc, M, near, pvw + vs)
    hd = pose.get('head', 'up'); hr = pose.get('head_rot', 0.0)
    hp = K11['head_pivot']
    if hd == 'up' and pose.get('head_flip'):
        # looking back over the shoulder: the head piece mirrored about its neck pivot, set a little higher
        Mh = Mroot @ Mb @ T(hp[0] + 6, hp[1] - 4) @ S(-1, 1) @ R(hr) @ T(-hp[0], -hp[1]) @ T(*P['head_up']['origin'])
    elif hd == 'up':
        Mh = Mroot @ Mb @ T(*hp) @ R(hr) @ T(-hp[0], -hp[1]) @ T(*P['head_up']['origin'])
    else:
        h18 = K18['head_pivot']
        Mh = Mroot @ Mb @ T(*hp) @ R(hr) @ S(pose.get('head_scale', 1.0)) @ T(-h18[0], -h18[1]) @ T(*P['head_low']['origin'])
    tr, t18 = K11['tail_root'], K18['tail_root']
    Mt = Mroot @ Mb @ T(*tr) @ R(pose.get('tail_rot', 0.0)) @ T(-t18[0], -t18[1]) @ T(*P['tail']['origin'])
    v = pose.get('variant', 'dusk')
    for name in ('farH', 'farF'):
        pc, M, _, _ = legs[name]; out.append((pc, v, M, 'leg_far'))
    out.append(('tail', v, Mt, 'tail'))
    out.append(('body', v, Mroot @ Mb @ T(*P['body']['origin']), 'body'))
    for name in ('nearH', 'nearF'):
        pc, M, _, _ = legs[name]; out.append((pc, v, M, 'leg_near'))
    out.append(('head_up' if hd == 'up' else 'head_low', v, Mh, 'head'))
    feet = {n: ap(Mroot, l[3]) for n, l in legs.items()}
    # keypoints through the same matrices (frame-11 px: nose, withers and rump top are inferred keys)
    keys = {'nose': ap(Mh, (80 - P['head_up']['origin'][0], 85 - P['head_up']['origin'][1])) if hd == 'up' else None,
            'withers': ap(Mroot @ Mb, (150, 106)), 'rump': ap(Mroot @ Mb, (200, 113))}
    feet['_keys'] = keys
    return out, feet
