"""The person: a coat-wearing human cut from ink-blue paper (the swarm prompt's second proof subject), rigged with the same
solver: bones for neck/head, arm and legs, a 4-vertex cage for the coat skirt, and a point for the hair knot.
Profile, facing +x (toward the porch). Feet at y = 0, x = 0 between the feet. Metres."""
import os
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from dog import taper, chain, ellipse, catmull, petal
import bbw
from rig import rot, aff, ang, ik2, lerp_ang

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')

J = {'hip': (-0.02, 0.93), 'neck': (0.0, 1.47), 'head': (0.01, 1.53), 'shoulder': (0.125, 1.40),
     'elbow': (0.148, 1.135), 'wrist': (0.162, 0.885),
     'kn': (0.03, 0.53), 'an': (0.05, 0.10), 'kf': (-0.085, 0.53), 'af': (-0.085, 0.10)}
COAT = [(-0.12, 0.98), (0.07, 0.98), (0.14, 0.60), (-0.165, 0.60)]


def shape():
    head = ellipse((0.01, 1.61), 0.092, 0.108, 0)
    hair = unary_union([ellipse((-0.025, 1.655), 0.085, 0.075), Point((-0.105, 1.64)).buffer(0.048, 20)])
    nose = Polygon([(0.09, 1.625), (0.122, 1.585), (0.09, 1.575)])
    neck = taper((0.0, 1.45), (0.005, 1.53), 0.045, 0.042)
    upper = catmull([(-0.12, 1.46), (0.0, 1.49), (0.075, 1.46), (0.08, 1.30), (0.075, 1.0), (-0.12, 1.0), (-0.135, 1.30)], 8)
    skirt = Polygon([(-0.125, 1.02), (0.077, 1.02), (0.165, 0.50), (-0.19, 0.50)])
    cap = ellipse((0.095, 1.425), 0.06, 0.05)
    arm = chain([J['shoulder'], J['elbow'], J['wrist']], [0.043, 0.036, 0.029])
    hand = ellipse((0.168, 0.84), 0.032, 0.045, 8)
    legs = [taper((0.03, 0.56), J['an'], 0.045, 0.033), taper((-0.085, 0.56), J['af'], 0.045, 0.033),
            ellipse((0.10, 0.04), 0.075, 0.038), ellipse((-0.04, 0.04), 0.06, 0.036)]
    body = unary_union([head, hair, nose, neck, upper, skirt, cap, arm, hand] + legs).buffer(0.002).buffer(-0.002)
    holes = []
    for x in np.linspace(-0.15, 0.13, 7):            # a pierced border along the coat hem
        holes.append(Point((x, 0.545)).buffer(0.011, 12))
    c = (-0.04, 1.22)                                # a rosette between the shoulders
    holes.append(Point(c).buffer(0.014, 14))
    for k in range(6):
        holes.append(petal(c, 90 + 60 * k, 0.026, 0.048, 0.011))
    holes.append(ellipse((0.055, 1.625), 0.012, 0.007, 0))   # eye
    holes.append(ellipse((-0.03, 0.78), 0.006, 0.07, 0))     # the coat's slit (vent)
    return body.difference(unary_union(holes))


def handles():
    hs = [{'name': 'p_neck', 'kind': 'bone', 'a': (0.0, 1.455), 'b': (0.004, 1.50), 'group': 'body'},
          {'name': 'p_head', 'kind': 'bone', 'a': (0.0, 1.56), 'b': (0.07, 1.61), 'group': 'body'},
          {'name': 'p_spine', 'kind': 'bone', 'a': (-0.03, 1.06), 'b': (-0.03, 1.38), 'group': 'body'},
          {'name': 'p_upper', 'kind': 'bone', 'a': (0.129, 1.37), 'b': (0.145, 1.17), 'group': 'body'},
          {'name': 'p_fore', 'kind': 'bone', 'a': (0.150, 1.10), 'b': (0.163, 0.86), 'group': 'body'},
          {'name': 'p_thigh', 'kind': 'bone', 'a': (-0.03, 0.90), 'b': (-0.02, 0.66), 'group': 'body'},
          {'name': 'p_shin_n', 'kind': 'bone', 'a': (0.032, 0.48), 'b': (0.05, 0.12), 'group': 'body'},
          {'name': 'p_shin_f', 'kind': 'bone', 'a': (-0.085, 0.48), 'b': (-0.085, 0.12), 'group': 'body'},
          {'name': 'p_hair', 'kind': 'point', 'p': (-0.12, 1.645), 'group': 'body'}]
    for i, p in enumerate(COAT):
        hs.append({'name': 'p_coat%d' % i, 'kind': 'cage', 'p': p, 'group': 'body'})
    return hs


def load():
    path = os.path.join(CACHE, 'person_weights.npz')
    hs = handles()
    if os.path.exists(path):
        z = np.load(path)
        return z['V'], z['F'], z['W'], hs
    poly = shape()
    V, F = bbw.triangulate(poly, hs, h=0.012)
    W, info = bbw.solve_bbw(V, F, hs)
    np.savez(path, V=V, F=F, W=W)
    return V, F, W, hs


def pose_affines(P, hs):
    """P: x (world, feet centre), sit 0..1, lean (deg forward), reach 0..1, low 0..1, call 0..1 (head jab), step (phase),
    stepping 0..1, breath."""
    sit, reach, low = P['sit'], P['reach'], P['low']
    hip0 = np.array(J['hip'])
    # pelvis: sitting lowers the hip onto a stool 0.46 m high, slightly back
    hip = hip0 + np.array([-0.06 * sit, (0.49 - hip0[1]) * sit])
    lean = np.radians(-(P.get('lean', 0.0) + 14 * reach + 22 * low * sit + 6 * P.get('call', 0)))
    Rl = rot(lean)
    out = {}
    out['p_spine'] = aff(Rl, hip0, hip)
    chest = lambda p: Rl @ (np.asarray(p) - hip0) + hip
    nk = chest(J['neck'])
    hj = np.radians(-10 * P.get('call', 0) - 8 * low + 4 * np.sin(P.get('t', 0) * 0.9))
    out['p_neck'] = aff(Rl, J['neck'], nk)
    Rh = rot(lean + hj)
    hp = chest(J['head'])
    out['p_head'] = aff(Rh, J['head'], hp)
    out['p_hair'] = aff(Rh, (-0.12, 1.645), Rh @ (np.array([-0.12, 1.645]) - J['head']) + hp)
    # arm: hanging -> reaching toward the dog (forward, shoulder height) -> offered low (hand near the floor, forward)
    sh = chest(J['shoulder'])
    l1 = np.linalg.norm(np.subtract(J['elbow'], J['shoulder'])); l2 = np.linalg.norm(np.subtract(J['wrist'], J['elbow']))
    hang = (ang(np.subtract(J['elbow'], J['shoulder'])), ang(np.subtract(J['wrist'], J['elbow'])))
    reach_a = (np.radians(-12), np.radians(-4))
    low_a = (np.radians(-58), np.radians(-38))
    rest_a = (hang[0] + lean, hang[1] + lean)
    a1 = lerp_ang(rest_a[0], reach_a[0], reach); a2 = lerp_ang(rest_a[1], reach_a[1], reach)
    a1 = lerp_ang(a1, low_a[0], low); a2 = lerp_ang(a2, low_a[1], low)
    el = sh + l1 * np.array([np.cos(a1), np.sin(a1)])
    out['p_upper'] = aff(rot(a1 - hang[0]), J['shoulder'], sh)
    out['p_fore'] = aff(rot(a2 - hang[1]), J['elbow'], el)
    # legs: standing straight; sitting: thighs forward, shins down; stepping: small alternating steps
    st = P.get('stepping', 0.0); ph = P.get('step', 0.0)
    feet = {'n': np.array([J['an'][0] + 0.05 * sit + 0.06 * st * np.sin(ph), 0.10 + 0.035 * st * max(0, np.sin(ph))]),
            'f': np.array([J['af'][0] + 0.03 * sit - 0.06 * st * np.sin(ph), 0.10 + 0.035 * st * max(0, -np.sin(ph))])}
    thigh_len = np.linalg.norm(np.subtract(J['kn'], J['hip']))
    for k, sk in (('n', 'p_shin_n'), ('f', 'p_shin_f')):
        knee_r, ank_r = np.array(J['k' + k]), np.array(J['a' + k])
        hip_k = hip + np.array([0.05 if k == 'n' else -0.065, 0.0])
        l2 = np.linalg.norm(ank_r - knee_r)
        target = feet[k] + np.array([0.33 * sit, 0.0])
        t1, t2 = ik2(hip_k, target, thigh_len, l2, knee_sign=+1)
        kn = hip_k + thigh_len * np.array([np.cos(t1), np.sin(t1)])
        out[sk] = aff(rot(t2 - ang(ank_r - knee_r)), knee_r, kn)
        if k == 'n':
            out['p_thigh'] = aff(rot(t1 - ang(knee_r - np.array(J['hip']) - [0.05, 0])), J['hip'],
                                 hip + Rl @ np.zeros(2))
            knee_n = kn
    # coat cage: waist follows the chest; hem follows the knees (front) and the seat (back)
    q = [chest(COAT[0]), chest(COAT[1]), None, None]
    q[2] = (1 - sit) * np.array(COAT[2]) + sit * (knee_n + np.array([0.03, 0.04]))
    q[3] = (1 - sit) * np.array(COAT[3]) + sit * (hip + np.array([-0.12, -0.08]))
    q[2] = q[2] + np.array([0.04 * reach, 0.0])
    for i in range(4):
        out['p_coat%d' % i] = aff(np.eye(2), COAT[i], q[i])
    A = np.zeros((len(hs), 2, 3))
    for j, hd in enumerate(hs):
        A[j] = out[hd['name']]
        A[j, 0, 2] += P['x']
    return A
