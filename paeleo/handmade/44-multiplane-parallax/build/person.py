"""The person: collage pieces cut from Straight Talk (the striped smock, the hair seen from behind, the maroon sleeve,
the trousers) and the offered hand from The Door to Heaven, set at depths like the dog.  Backlit by the room, so the
person reads mostly as a silhouette; no face is shown."""
import math
import numpy as np
from common import *
from dog import hvec, lat, UP


def P(i, k):
    return FR[min(max(i, 0), N - 1)]['person'][k]


def person_z(x):
    # in the doorway (x = -0.28) she stands on the sill; beside the door she sits against the wall
    u = smooth((-0.28 - x) / (1.25 - 0.28))
    return -0.10 + (-0.30 + 0.10) * u


def pose(i):
    t = i / FPS
    x = P(i, 'x'); sit = P(i, 'sit'); reach = P(i, 'reach'); low = P(i, 'low')
    Z = person_z(x)
    R = np.array([x, 0.0, Z])
    hd = 330.0 if sit < 0.5 else 350.0        # turned toward the dog, a little toward us
    F, L = hvec(hd), lat(hd)
    s = smooth(sit)
    pel = R + UP * (0.95 * (1 - s) + 0.14 * s) + F * (0.0 * (1 - s) - 0.05 * s)
    chest = pel + UP * 0.48 + F * (0.02 + 0.08 * s + 0.05 * reach)
    head = chest + UP * 0.21 + F * (0.03 + 0.05 * s + 0.04 * reach)
    if P(i, 'voice') == 'call':
        head = head + F * 0.03
    # walking aside: legs step with distance
    ph = (x + 0.28) / 0.35 * math.pi
    legs = []
    for side in (+1, -1):
        hip = pel + L * side * 0.09
        stand_foot = R + L * side * 0.11 + F * (0.12 * math.sin(ph + (0 if side > 0 else math.pi)) if 5.4 < t < 6.6 else 0) + UP * 0.04
        sit_foot = pel + F * 0.72 + L * side * 0.12 - UP * 0.10
        foot = stand_foot * (1 - s) + sit_foot * s
        bend = F * 1.0 + UP * (0.6 * s)
        from dog import ik2
        knee, foot = ik2(hip, foot, 0.46, 0.46, bend)
        legs.append((side, hip, knee, foot))
    arms = []
    for side in (+1, -1):
        sh = chest + L * side * 0.18 - UP * 0.03
        near = side > 0
        rest_w = pel + L * side * 0.24 + F * 0.12 + UP * 0.05
        if near:
            reach_w = sh + F * 0.62 - UP * 0.08
            low_w = R + F * 0.70 + L * 0.05 + UP * 0.10
            w = rest_w
            w = w * (1 - smooth(reach)) + reach_w * smooth(reach)
            w = w * (1 - smooth(low)) + low_w * smooth(low)
        else:
            w = rest_w + UP * 0.0
        elbow, w = ik2(sh, w, 0.31, 0.29, -UP * 0.6 - F * 0.3 + L * side * 0.4)
        arms.append((side, sh, elbow, w))
    meta = dict(x=x, R=R, head=head, sit=sit, reach=reach, low=low)
    return dict(F=F, L=L, pel=pel, chest=chest, head=head, legs=legs, arms=arms, meta=meta)


def pieces(Q):
    out = []
    add = lambda *a: out.append(a)
    F = Q['F']
    for side, hip, knee, foot in Q['legs']:
        add(f'p_thigh{side}', 'person', ('cap', hip, knee, 0.085, 0.065), 'trousers', 1.0, 0)
        add(f'p_shin{side}', 'person', ('cap', knee, foot, 0.06, 0.05), 'trousers', 0.9, 0)
        add(f'p_shoe{side}', 'person', ('cap', foot, foot + F * 0.16, 0.05, 0.045), 'shoe', 1.0, -0.002)
    add('p_torso', 'person', ('cap', Q['pel'] - UP * 0.04, Q['chest'], 0.21, 0.17), 'smock', 1.0, 0)
    add('p_neck', 'person', ('cap', Q['chest'], Q['head'] - UP * 0.04, 0.05, 0.045), 'hair', 0.8, 0.001)
    add('p_head', 'person', ('prof', Q['head'], F, 0.125), 'hair', 1.0, -0.001)
    for side, sh, el, w in Q['arms']:
        add(f'p_upper{side}', 'person', ('cap', sh, el, 0.06, 0.05), 'sleeve', 1.0, 0)
        add(f'p_fore{side}', 'person', ('cap', el, w, 0.05, 0.04), 'sleeve', 1.0, 0)
        add(f'p_hand{side}', 'person', ('cap', w, w + (w - el) / max(np.linalg.norm(w - el), 1e-6) * 0.10, 0.05, 0.04), 'hand', 1.0, -0.002)
    return out


def frame(i):
    Q = pose(i)
    return pieces(Q), Q['meta']
