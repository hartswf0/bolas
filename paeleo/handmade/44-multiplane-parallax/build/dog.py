"""The dog: a stack of collage pieces at their own depths.

Each piece is a flat paper fragment cut from the real dog of *Amateur Film New Jersey C* (its fur, its dark saddle, its
pale chest, its face), shaped by hand (seeded scissor jitter) and set at a 3D point of a small skeleton.  Pieces are
billboards (always parallel to the film, like every multiplane cel) but each sits at its own depth, so the camera's
movement gives the dog its own parallax: the near legs slide against the far legs, the head against the chest.
Turns are real: the skeleton rotates in depth and the pieces re-stack (chest in front when it faces us, the back of the
head in front when it looks into the room), so no piece is ever mirrored or squashed edge-on.

Acting curves come from the score (lie, crouch, ear, tail, wag, rest, head, look, x) with three re-timings that the
brief's lessons demand: the refusal turn is complete by ~3.9 s; at 7.46 the head swings round to the door first while
the body is still down; looking in at 26.4 turns the head *into the room* (deeper Z), not up.
"""
import math
import numpy as np
from common import *

UP = np.array([0.0, 1.0, 0.0])
SILL = SCORE['places']['sill']


def hvec(deg):
    a = math.radians(deg)
    return np.array([math.cos(a), 0.0, math.sin(a)])


def lat(deg):
    a = math.radians(deg)
    return np.array([-math.sin(a), 0.0, math.cos(a)])


def act(i, k):
    return FR[min(max(i, 0), N - 1)]['dog']['act'][k]


def xs(i):
    return FR[min(max(i, 0), N - 1)]['dog']['x']


# ---------------------------------------------------------------- path in depth
Z_PORCH = -0.75
X_CURVE = 1.75       # where the approach starts to bend toward the door
Z_END = -0.18


def path_z(x):
    if x >= X_CURVE:
        return Z_PORCH
    u = min(1.0, (X_CURVE - x) / (X_CURVE - SILL))
    return Z_PORCH + (Z_END - Z_PORCH) * u * u


def path_heading(x):
    """heading of the path when walking toward -X (180 = straight at the door side)."""
    if x >= X_CURVE:
        return 180.0
    u = min(1.0, (X_CURVE - x) / (X_CURVE - SILL))
    k = 2 * u * (Z_END - Z_PORCH) / (X_CURVE - SILL)
    return 180.0 - math.degrees(math.atan(k))


FINAL_HEADING = 128.0
AWAY = 378.0      # the refusal: rear to the door and three-quarters to us (its back is what we see)


def ease_angle(a, b, u):
    return a + (b - a) * smooth(u)


def body_heading(t, x):
    if t < 3.417:
        return 180.0
    if t < 3.80:
        return ease_angle(180, AWAY, (t - 3.417) / (3.80 - 3.417))
    if t < 7.85:
        return AWAY
    if t < 8.75:
        return ease_angle(AWAY, 180, (t - 7.85) / 0.9)
    if t < 23.79:
        return path_heading(x)
    return ease_angle(path_heading(x), FINAL_HEADING, (t - 23.79) / 0.8)


def head_heading(t, x, hb):
    if 3.417 <= t < 3.80:
        return ease_angle(180, AWAY, (t - 3.417) / 0.22) if t < 3.637 else AWAY
    if 7.458 <= t < 8.75:
        h = ease_angle(AWAY, 186, (t - 7.458) / 0.20)      # the head comes round to the door first
        if t > 7.85:
            h = min(h, max(hb, 180.0) + 6 * (1 - smooth((t - 7.85) / 0.9)))
        return h
    if t >= 26.40:
        a = ease_angle(0, 1, (t - 26.40) / 0.32) - ease_angle(0, 1, (t - 28.45) / 0.6)
        return hb + (88.0 - hb) * a        # 88 = straight into the room (+Z), the back of the head to us
    return hb


def look_amount(t):
    return smooth((t - 26.40) / 0.32) - smooth((t - 28.45) / 0.6) if t >= 26.4 else 0.0


# ---------------------------------------------------------------- feet: a planner that never slides a planted foot
LEGS = [('fore', +1), ('fore', -1), ('hind', +1), ('hind', -1)]
DIAG = {0: 3, 1: 2, 2: 1, 3: 0}


def mounts(R, hb, crouch, lie):
    F, L = hvec(hb), lat(hb)
    S = R + F * 0.22 + UP * (0.50 - 0.06 * crouch)
    Hh = R - F * 0.24 + UP * (0.48 - 0.11 * crouch)
    Sl = R + F * 0.19 + UP * 0.15
    Hl = R - F * 0.25 + UP * 0.12
    w = smooth(lie)
    S = S * (1 - w) + Sl * w
    Hh = Hh * (1 - w) + Hl * w
    return S, Hh, F, L


def stand_target(R, hb, k):
    F, L = hvec(hb), lat(hb)
    kind, side = LEGS[k]
    base = R + F * (0.21 if kind == 'fore' else -0.25) + L * side * 0.095
    return np.array([base[0], 0.0, base[2]])


def plan_feet():
    feet = [None] * 4
    swing = [None] * 4        # (t0, from, to)
    out = []
    SW = 0.13
    for i in range(N):
        t = i / FPS
        R = root(i)
        hb = body_heading(t, xs(i))
        Rn = root(min(i + 3, N - 1)); hbn = body_heading(t + 0.125, xs(min(i + 3, N - 1)))
        tg = [stand_target(Rn, hbn, k) for k in range(4)]
        if feet[0] is None:
            feet = [stand_target(R, hb, k) for k in range(4)]
        # finish swings
        for k in range(4):
            if swing[k] and t - swing[k][0] >= SW:
                feet[k] = swing[k][2]; swing[k] = None
        # start swings: the most-displaced foot, if its diagonal partner is planted and <= 2 swinging
        err = [np.linalg.norm(tg[k] - feet[k]) for k in range(4)]
        for k in sorted(range(4), key=lambda k: -err[k]):
            if swing[k] or err[k] < 0.07:
                continue
            if sum(1 for s in swing if s) >= 2:
                break
            if swing[(k + 1) % 2 + (k // 2) * 2] is not None:   # same-girdle partner swinging: wait
                continue
            swing[k] = (t, feet[k].copy(), tg[k].copy())
        pos = []
        for k in range(4):
            if swing[k]:
                u = (t - swing[k][0]) / SW
                p = swing[k][1] * (1 - smooth(u)) + swing[k][2] * smooth(u)
                p = p + UP * 0.07 * math.sin(math.pi * min(1, u))
                pos.append(p)
            else:
                pos.append(feet[k].copy())
        out.append((pos, [s is not None for s in swing]))
    return out


def root(i):
    x = xs(i)
    return np.array([x, 0.0, path_z(x)])


def ik2(a, c, l1, l2, bend):
    """two-bone IK: joint between a and c, bending toward vector `bend`."""
    d = c - a
    L = np.linalg.norm(d)
    L = min(max(L, 1e-4), l1 + l2 - 1e-4)
    dn = d / max(np.linalg.norm(d), 1e-6)
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    b = bend - dn * np.dot(bend, dn)
    nb = np.linalg.norm(b)
    b = b / nb if nb > 1e-6 else np.array([0.0, 1.0, 0.0])
    return a + dn * x + b * h, a + dn * L


# ---------------------------------------------------------------- the pose -> pieces
def pose(i, feet_plan):
    t = i / FPS
    x = xs(i)
    R = root(i)
    hb = body_heading(t, x)
    hh = head_heading(t, x, hb)
    lie = act(i, 'lie')
    if t >= 23.79:
        lie = max(lie, 0.0)
    crouch = act(i, 'crouch'); ear = act(i, 'ear'); tail = act(i, 'tail'); wag = act(i, 'wag')
    rest = act(i, 'rest'); headup = act(i, 'head')
    look = look_amount(t)
    if t >= 26.4:
        headup = min(headup, 0.75)   # looking in is a turn into the room, not a lift toward the light
    S, Hh, F, L = mounts(R, hb, crouch, lie)
    # neck yaw follows the head partway (a dog looks back over its shoulder)
    rel = ((hh - hb + 180) % 360) - 180
    neck_yaw = hb + max(-80, min(80, rel * 0.6))
    Fn, Fh, Lh = hvec(neck_yaw), hvec(hh), lat(hh)
    # pitch: 0 -> -45 deg (low), 0.45 -> -26 (approach: clearly below the back), 0.9 -> +35, 1.2 -> +45
    pitch = np.interp(headup, [0, 0.45, 0.9, 1.25], [-45, -26, 35, 45])
    turning = max(0.0, 1 - abs(((hb - 270 + 180) % 360) - 180) / 70.0)   # 1 when the body faces us
    pitch = pitch * (1 - 0.6 * turning) + (-5) * 0.6 * turning
    if t >= 26.4:
        pitch = pitch * (1 - look) + 12 * look
    pr = math.radians(pitch)
    NB = S + F * 0.07 + UP * 0.07
    HC = NB + (Fn * math.cos(pr) + UP * math.sin(pr)) * 0.24
    # resting: chin on the paws, ahead of the chest
    HCrest = R + F * 0.44 + UP * 0.10
    rw = smooth(rest) * smooth(lie)
    HC = HC * (1 - rw) + HCrest * rw
    mp = math.radians(min(pitch, 10) * 0.5 - 12 + 10 * rw)
    MZ0 = HC + Fh * 0.035
    MZ1 = HC + (Fh * math.cos(mp) + UP * math.sin(mp)) * 0.15
    if rw > 0.5:
        MZ1[1] = max(MZ1[1], 0.045)
    # legs
    pos, swinging = feet_plan[i]
    w = smooth(lie)
    legs = []
    for k, (kind, side) in enumerate(LEGS):
        if kind == 'fore':
            J = S + L * side * 0.09 - UP * 0.04
            foot_l = R + F * 0.60 + L * side * 0.075 + UP * 0.03
            foot = pos[k] * (1 - w) + foot_l * w
            elbow, foot = ik2(J, foot, 0.22, 0.25, (-F * 1.0 + UP * 0.05) * (1 - w) + (-UP * 1.0 - F * 0.2) * w)
            legs.append((kind, side, [J, elbow, foot]))
        else:
            J = Hh + L * side * 0.09 - UP * 0.02 - F * 0.02
            paw = pos[k] * (1 - w) + (R - F * 0.05 + L * side * 0.13 + UP * 0.03) * w
            hock = paw + UP * (0.14 * (1 - w) + 0.0 * w) - F * (0.05 * (1 - w) - 0.10 * w)
            if w > 0:
                hock = hock * 1.0
            knee, hock = ik2(J, hock, 0.23, 0.22, F * 1.0 - UP * 0.1 + L * side * 0.3 * w)
            legs.append((kind, side, [J, knee, hock, paw]))
    # tail
    ta = np.interp(tail, [0, 0.5, 1.0, 1.35], [55, -25, -70, -105])
    ta = ta * (1 - w) + (-8) * w
    psi = math.radians(wag * 38 * math.sin(2 * math.pi * 2.3 * t))
    TB = Hh - F * 0.12 + UP * 0.05
    pts = [TB]
    seg = 0.12
    for s in range(3):
        a = math.radians(ta + (s * (-12 if tail < 1 else 18)))
        d = (-F * math.cos(a) + UP * math.sin(a)) * math.cos(psi) + L * math.sin(psi)
        p = pts[-1] + d * seg
        p[1] = max(p[1], 0.025)
        pts.append(p)
    # ears
    ears = []
    for side in (+1, -1):
        base = HC + UP * 0.055 + Lh * side * 0.042 - Fh * 0.015
        up = ear
        tip = base + UP * (0.03 + 0.065 * up) - Fh * (0.075 * (1 - up) + 0.005) + Lh * side * 0.018
        ears.append((side, base, tip))
    eyes = [HC + Fh * 0.06 + Lh * s * 0.036 + UP * 0.022 for s in (+1, -1)]
    meta = dict(R=R, S=S, H=Hh, HC=HC, nose=MZ1, hb=hb, hh=hh, lie=lie, look=look, pitch=pitch,
                swinging=swinging, feet=[l[2][-1] for l in legs], withers=S + UP * 0.12)
    return dict(S=S, H=Hh, F=F, L=L, NB=NB, HC=HC, MZ0=MZ0, MZ1=MZ1, legs=legs, tail=pts, ears=ears, eyes=eyes,
                hb=hb, hh=hh, lie=lie, meta=meta)


def pieces(P):
    """the cut list: (name, group, shape, texture, shade, bias)."""
    S, Hh, F, NB, HC = P['S'], P['H'], P['F'], P['NB'], P['HC']
    out = []
    add = lambda *a: out.append(a)
    for kind, side, ch in P['legs']:
        tex = 'leg'
        nm = f'{kind}_{"a" if side > 0 else "b"}'
        if kind == 'fore':
            add(nm + '_upper', 'body', ('cap', ch[0], ch[1], 0.055, 0.035), tex, 1.0, 0)
            add(nm + '_lower', 'body', ('cap', ch[1], ch[2], 0.032, 0.026), tex, 1.05, 0)
            add(nm + '_paw', 'body', ('cap', ch[2] - F * 0.01, ch[2] + F * 0.045, 0.03, 0.028), 'leg', 1.1, -0.01)
        else:
            add(nm + '_thigh', 'body', ('cap', ch[0], ch[1], 0.085, 0.045), 'flank', 0.95, 0)
            add(nm + '_shank', 'body', ('cap', ch[1], ch[2], 0.04, 0.028), tex, 1.0, 0)
            add(nm + '_meta', 'body', ('cap', ch[2], ch[3], 0.027, 0.025), tex, 1.05, 0)
            add(nm + '_paw', 'body', ('cap', ch[3] - F * 0.01, ch[3] + F * 0.045, 0.03, 0.028), 'leg', 1.1, -0.01)
    add('flank', 'body', ('cap', S - F * 0.02, Hh + F * 0.02, 0.145, 0.12), 'flank', 1.0, 0)
    add('saddle', 'body', ('cap', S + UP * 0.05 - F * 0.04, Hh + UP * 0.045, 0.095, 0.08), 'saddle', 1.0, -0.002)
    add('chest', 'body', ('cap', S + F * 0.08 - UP * 0.01, S + F * 0.05 - UP * 0.09, 0.12, 0.09), 'chest', 1.0, -0.003)
    add('rump', 'body', ('cap', Hh - F * 0.06, Hh - F * 0.07 - UP * 0.05, 0.11, 0.09), 'flank', 1.05, -0.001)
    tp = P['tail']
    for s in range(3):
        add(f'tail{s}', 'body', ('cap', tp[s], tp[s + 1], 0.032 - 0.008 * s, 0.026 - 0.009 * s), 'flank', 1.15 + 0.05 * s, 0)   # a pale tail: never mistaken for the dark head
    add('neck', 'head', ('cap', NB - F * 0.03, HC, 0.085, 0.07), 'saddle', 1.0, 0)
    add('ruff', 'head', ('cap', NB + F * 0.03 - UP * 0.05, (NB + HC) / 2 - UP * 0.03, 0.07, 0.06), 'chest', 0.95, -0.001)
    add('skull', 'head', ('cap', HC - P['F'] * 0.0 + UP * 0.005, HC, 0.078, 0.078), 'face', 1.0, 0)
    add('muzzle', 'head', ('cap', P['MZ0'], P['MZ1'], 0.05, 0.03), 'muzzle', 1.0, 0)
    add('nose', 'head', ('cap', P['MZ1'], P['MZ1'], 0.02, 0.02), 'black', 1.0, -0.004)
    for k, e in enumerate(P['eyes']):
        add(f'eye{k}', 'head', ('cap', e, e, 0.012, 0.012), 'eye', 1.0, -0.004)
    for side, base, tip in P['ears']:
        add(f'ear{"a" if side > 0 else "b"}', 'head', ('tri', base, tip, 0.05), 'face', 0.9, 0)
    return out


PLAN = None


def frame(i):
    global PLAN
    if PLAN is None:
        PLAN = plan_feet()
    P = pose(i, PLAN)
    return pieces(P), P['meta']
