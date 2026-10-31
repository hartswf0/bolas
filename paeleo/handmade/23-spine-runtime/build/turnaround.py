"""SCION 23 · the turnaround sheet (authoring side only).

A Spine artist lays out a character's views on a turnaround sheet before rigging. This module is that sheet in code:
a dog's joints in its own 3D frame (metres; X forward, Y up, Z to the dog's left), posed by a few acting parameters
(lie, crouch, neck, head, ears, tail), projected through the film camera at a body view angle phi
(0 = facing screen-left / the door, 90 = facing away from the camera, 135 = facing right and away).

It is used ONLY to author: to place the setup pose of every view, to bake the keys of the action clips into 2D bone
values, and to lay out the painted atlas regions. The runtime (runtime.py) never sees 3D: it reads 2D bone values,
attachments and draw order from the skeleton and clip JSON, like any Spine runtime.
"""
import math
import numpy as np
from common import CE, SE

D2R = math.pi / 180

# bone table: name, parent, start joint, end joint, orientation rule
BONES = [
    ('root', None, None, None, 'fixed'),
    ('hips', 'root', 'hipJ', 'chestJ', 'vec'),
    ('chest', 'hips', 'chestJ', 'neckB', 'vec'),
    ('neck', 'chest', 'neckB', 'headJ', 'vec'),
    ('head', 'neck', 'headJ', 'muzzle', 'up'),
    ('earL', 'head', 'earLb', 'earLt', 'vec'),
    ('earR', 'head', 'earRb', 'earRt', 'vec'),
    ('tail1', 'hips', 'tail0', 'tail1', 'vec'),
    ('tail2', 'tail1', 'tail1', 'tail2', 'vec'),
    ('tail3', 'tail2', 'tail2', 'tail3', 'vec'),
]
for s in 'LR':
    BONES += [('f%s_up' % s, 'chest', 'sh%s' % s, 'el%s' % s, 'vec'),
              ('f%s_lo' % s, 'f%s_up' % s, 'el%s' % s, 'wr%s' % s, 'vec'),
              ('f%s_paw' % s, 'f%s_lo' % s, 'wr%s' % s, 'ft%s' % s, 'vec')]
for s in 'LR':
    BONES += [('h%s_th' % s, 'hips', 'hp%s' % s, 'st%s' % s, 'vec'),
              ('h%s_sh' % s, 'h%s_th' % s, 'st%s' % s, 'hk%s' % s, 'vec'),
              ('h%s_mt' % s, 'h%s_sh' % s, 'hk%s' % s, 'pj%s' % s, 'vec'),
              ('h%s_paw' % s, 'h%s_mt' % s, 'pj%s' % s, 'ht%s' % s, 'vec')]
for s in 'LR':
    BONES += [('ik_f%s' % s, 'root', 'wr%s' % s, None, 'target'), ('ik_h%s' % s, 'root', 'pj%s' % s, None, 'target')]

LEN = dict(hips=0.46, chest=0.13, neck=0.19, head=0.30, ear=0.115, tail1=0.13, tail2=0.13, tail3=0.12,
           f_up=0.18, f_lo=0.19, f_paw=0.075, h_th=0.20, h_sh=0.21, h_mt=0.12, h_paw=0.07)


def blen(name):
    if name in LEN: return LEN[name]
    if name.startswith('ear'): return LEN['ear']
    if name[0] in 'fh' and '_' in name and not name.startswith('ik'):
        return LEN[name[0] + '_' + name.split('_')[1]]
    return None


DEFAULT = dict(phi=0.0, lie=0.0, crouch=0.0, rear_drop=0.0, neck_elev=48.0, neck_yaw=0.0, head_pitch=-12.0,
               head_yaw=0.0, ear=0.85, tail=0.5, tail_yaw=0.0, splay=0.0, fore_reach=0.0, body_y=0.0)


def lerp(a, b, t): return a + (b - a) * t


def rot2(v, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def ik2(a, b, T, bend):
    """2-bone IK in a plane: returns (angle of bone a, angle of bone b) to reach T from origin. bend=+1 knee to +side."""
    d = max(abs(a - b) + 1e-4, min(a + b - 1e-4, math.hypot(*T)))
    ca = (a * a + d * d - b * b) / (2 * a * d)
    A = math.acos(max(-1, min(1, ca)))
    base = math.atan2(T[1], T[0])
    t1 = base + bend * A
    E = np.array([a * math.cos(t1), a * math.sin(t1)])
    t2 = math.atan2(T[1] - E[1], T[0] - E[0])
    return t1, t2


def pose3d(P):
    p = dict(DEFAULT); p.update(P)
    lie, cr = p['lie'], p['crouch']
    le = lie * lie * (3 - 2 * lie)
    hh = 0.50 - 0.10 * cr - 0.07 * p['rear_drop']
    ch = 0.50 - 0.065 * cr
    hh = lerp(hh, 0.205, le) + p['body_y']
    ch = lerp(ch, 0.245, le) + p['body_y']
    dy = ch - hh
    dx = math.sqrt(LEN['hips'] ** 2 - dy * dy)
    beta = math.atan2(dy, dx)
    J = {}
    J['hipJ'] = np.array([-dx / 2, hh, 0.0])
    J['chestJ'] = np.array([dx / 2, ch, 0.0])
    cb = rot2([LEN['chest'], 0], beta + 35 * D2R)
    J['neckB'] = J['chestJ'] + np.array([cb[0], cb[1], 0])
    e, ny = p['neck_elev'] * D2R, p['neck_yaw'] * D2R
    nd = np.array([math.cos(e) * math.cos(ny), math.sin(e), math.cos(e) * math.sin(ny)])
    J['headJ'] = J['neckB'] + LEN['neck'] * nd
    hp, hy = p['head_pitch'] * D2R, (p['neck_yaw'] + p['head_yaw']) * D2R
    f = np.array([math.cos(hp) * math.cos(hy), math.sin(hp), math.cos(hp) * math.sin(hy)])
    up = np.array([-math.sin(hp) * math.cos(hy), math.cos(hp), -math.sin(hp) * math.sin(hy)])
    left = np.array([-math.sin(hy), 0, math.cos(hy)])
    J['muzzle'] = J['headJ'] + LEN['head'] * f
    a = lerp(82, 6, max(0, min(1, p['ear']))) * D2R
    for s, sg in (('L', 1), ('R', -1)):
        b = J['headJ'] + 0.088 * up + 0.04 * f + sg * 0.058 * left
        dr = up * math.cos(a) - f * math.sin(a) + sg * 0.28 * left
        dr /= np.linalg.norm(dr)
        J['ear%sb' % s] = b
        J['ear%st' % s] = b + LEN['ear'] * dr
    # tail
    tt = max(0, min(1, p['tail'] / 1.35))
    t0 = rot2([-0.10, 0.035], beta)
    J['tail0'] = J['hipJ'] + np.array([t0[0], t0[1], 0])
    a0 = lerp(30, -72, tt); a1 = a0 - lerp(12, 22, tt); a2 = a1 - lerp(10, 16, tt)
    a0, a1, a2 = lerp(a0, -26, le), lerp(a1, -4, le), lerp(a2, 6, le)
    w = p['tail_yaw'] * D2R
    pt = J['tail0']
    for i, (aa, ln) in enumerate(zip((a0, a1, a2), (LEN['tail1'], LEN['tail2'], LEN['tail3']))):
        ww = w * (1 + 0.6 * i) + le * (0.45 + 0.35 * i)  # lying: the tail curls round to the dog's near (left) side
        aa = aa * D2R
        d3 = np.array([-math.cos(aa) * math.cos(ww), math.sin(aa), math.cos(aa) * math.sin(ww)])
        pt = pt + ln * d3
        J['tail%d' % (i + 1)] = pt
    # legs: standing = feet planted under the girdles (IK in the sagittal plane); lying = folded (sphinx) offsets
    # from the girdle joint. In between, the paw and hock targets travel from one to the other, kept above the floor,
    # and the leg is re-solved, so no leg passes through the floor and no bone changes length.
    sp = p['splay']
    def fold(start, angs, lens):
        pts, q = [], np.array(start, float)
        for an, ln in zip(angs, lens):
            q = q + ln * np.array([math.cos(an * D2R), math.sin(an * D2R)]); pts.append(q)
        return pts
    for s, sg in (('L', 1), ('R', -1)):
        z = sg * (0.075 + 0.02 * le)
        sh2 = rot2([-0.03, -0.075], beta)
        S = J['chestJ'] + np.array([sh2[0], sh2[1], 0]); S[2] = z
        J['sh' + s] = S
        stand_w = np.array([J['chestJ'][0] + 0.02 + p['fore_reach'], 0.06])
        fe, fw, ff = fold([0, 0], (-118, -4, 2), (LEN['f_up'], LEN['f_lo'], LEN['f_paw']))
        lie_w = S[:2] + fw
        wf = max(0.0, min(1.0, (le - 0.4) / 0.6)); wf = wf * wf * (3 - 2 * wf)
        Wt = stand_w + (lie_w - stand_w) * wf
        Wt[1] = max(Wt[1], 0.012 + 0.04 * (1 - wf))
        t1, t2 = ik2(LEN['f_up'], LEN['f_lo'], Wt - S[:2], -1)
        E = S[:2] + LEN['f_up'] * np.array([math.cos(t1), math.sin(t1)])
        Wr = E + LEN['f_lo'] * np.array([math.cos(t2), math.sin(t2)])
        tp = lerp(-32, 2, wf) * D2R
        Ft = Wr + LEN['f_paw'] * np.array([math.cos(tp), math.sin(tp)])
        J['el' + s] = np.array([E[0], E[1], z]); J['wr' + s] = np.array([Wr[0], Wr[1], z])
        J['ft' + s] = np.array([Ft[0], Ft[1], z])
    for s, sg in (('L', 1), ('R', -1)):
        z = sg * (0.085 + 0.05 * le + 0.04 * sp)
        hp2 = rot2([0.0, -0.07], beta)
        Hp = J['hipJ'] + np.array([hp2[0], hp2[1], 0]); Hp[2] = z
        J['hp' + s] = Hp
        am = (-78 + 46 * max(0.0, min(1.0, (0.47 - hh) / 0.15))) * D2R   # a crouch lowers the hock
        stand_pj = np.array([J['hipJ'][0] - 0.03, 0.045])
        stand_hk = stand_pj - LEN['h_mt'] * np.array([math.cos(am), math.sin(am)])
        fs, fh, fp, ft = fold([0, 0], (-32, -182, -4, 0), (LEN['h_th'], LEN['h_sh'], LEN['h_mt'], LEN['h_paw']))
        lie_hk = Hp[:2] + fh
        wf = max(0.0, min(1.0, (le - 0.3) / 0.7)); wf = wf * wf * (3 - 2 * wf)
        Hkt = stand_hk + (lie_hk - stand_hk) * wf
        Hkt[1] = max(Hkt[1], 0.03)
        t1, t2 = ik2(LEN['h_th'], LEN['h_sh'], Hkt - Hp[:2], +1)
        St = Hp[:2] + LEN['h_th'] * np.array([math.cos(t1), math.sin(t1)])
        Hk = St + LEN['h_sh'] * np.array([math.cos(t2), math.sin(t2)])
        u3 = lerp(am, -4 * D2R, wf)
        Pj = Hk + LEN['h_mt'] * np.array([math.cos(u3), math.sin(u3)])
        if Pj[1] < 0.02:  # keep the paw joint on the floor: swing the metatarsus forward instead
            u3 = -math.asin(max(-1, min(1, (Hk[1] - 0.02) / LEN['h_mt'])))
            Pj = Hk + LEN['h_mt'] * np.array([math.cos(u3), math.sin(u3)])
        u4 = lerp(-30, 0, wf) * D2R
        Ht = Pj + LEN['h_paw'] * np.array([math.cos(u4), math.sin(u4)])
        if Ht[1] < 0.0:
            u4 = -math.asin(max(-1, min(1, (Pj[1] - 0.005) / LEN['h_paw'])))
            Ht = Pj + LEN['h_paw'] * np.array([math.cos(u4), math.sin(u4)])
        for k, v in (('st', St), ('hk', Hk), ('pj', Pj), ('ht', Ht)):
            J[k + s] = np.array([v[0], v[1], z])
    return J, dict(f=f, up=up, left=left), p


def view_axes(phi):
    ph = phi * D2R
    fw = np.array([-math.cos(ph), 0, math.sin(ph)])     # world (x, y, d)
    lf = np.array([-math.sin(ph), 0, -math.cos(ph)])
    return fw, lf


def to_world(v, phi):
    fw, lf = view_axes(phi)
    return v[0] * fw + np.array([0, v[1], 0]) + v[2] * lf


def project(w):
    """world (x, y, d) metres -> skeleton plane (x, y) metres and depth"""
    return np.array([w[0], w[1] * CE + w[2] * SE]), -w[1] * SE + w[2] * CE


def nearest(v, opts):
    return min(opts, key=lambda o: abs(o - v))


def bake(P):
    """pose parameters -> 2D Spine bone values (cm, deg), attachments, draw order"""
    J, hf, p = pose3d(P)
    phi = p['phi']
    S2, DEP = {}, {}
    for k, v in J.items():
        S2[k], DEP[k] = project(to_world(v, phi))
    world = {}
    for name, parent, a, b, rule in BONES:
        if rule == 'fixed':
            world[name] = (np.zeros(2), 0.0, 1.0)
            continue
        P0 = S2[a] * 100
        if rule == 'target':
            world[name] = (P0, 0.0, 1.0)
            continue
        if rule == 'up':
            u2, _ = project(to_world(hf['up'], phi))
            th = math.atan2(u2[1], u2[0]) - math.pi / 2
            sc = 1.0
        else:
            v = (S2[b] - S2[a]) * 100
            ln = math.hypot(*v)
            th = math.atan2(v[1], v[0]) if ln > 1e-3 else world[parent][1]
            L3 = blen(name) * 100
            sc = max(0.05, ln / L3)
        world[name] = (P0, th, sc)
    local = {}
    for name, parent, a, b, rule in BONES:
        P0, th, sc = world[name]
        if parent is None:
            local[name] = dict(x=0.0, y=0.0, rotation=0.0, scaleX=1.0)
            continue
        Pp, tp, _ = world[parent]
        d = rot2(P0 - Pp, -tp)
        r = (th - tp) / D2R
        r = (r + 180) % 360 - 180
        local[name] = dict(x=round(float(d[0]), 3), y=round(float(d[1]), 3), rotation=round(r, 3),
                           scaleX=round(float(sc), 4))
    psi = phi - p['neck_yaw'] - p['head_yaw']
    att, order = attachments_and_order(phi, psi)
    return dict(local=local, world=world, attachments=att, drawOrder=order, phi=phi, psi=psi, joints=S2,
                depth=DEP, params=p)


SLOTS_LEG = {}
for s in 'LR':
    SLOTS_LEG['f' + s] = ['f%s_paw' % s, 'f%s_lo' % s, 'f%s_up' % s]
    SLOTS_LEG['h' + s] = ['h%s_paw' % s, 'h%s_mt' % s, 'h%s_sh' % s, 'h%s_th' % s]
SLOTS = (SLOTS_LEG['fL'] + SLOTS_LEG['fR'] + SLOTS_LEG['hL'] + SLOTS_LEG['hR'] +
         ['tail', 'torso', 'neck', 'head', 'earL', 'earR'])


def attachments_and_order(phi, psi):
    near = 'L' if phi < 90 else 'R'
    far = 'R' if near == 'L' else 'L'
    tv = nearest(phi, [0, 45, 90, 135])
    hv = nearest(max(-10, min(190, psi)), [0, 45, 68, 90, 112, 135, 180])
    att = {'torso': 'torso_%d' % tv, 'tail': 'tail', 'neck': 'neck_dL' if psi < 90 else 'neck_dR',
           'head': 'head_%d' % hv}
    for s in 'LR':
        nf = 'near' if s == near else 'far'
        if 67.5 <= phi <= 112.5: nf = 'near'
        for sl in SLOTS_LEG['f' + s] + SLOTS_LEG['h' + s]:
            att[sl] = sl.split('_')[1] + ('_f' if sl[0] == 'f' else '_h') + '_' + nf
    ear_near = 'L' if psi < 90 else 'R'
    for s in 'LR':
        if 30 < psi < 150:
            att['ear' + s] = 'ear_back'
        else:
            att['ear' + s] = 'ear_side_near' if s == ear_near else 'ear_side_far'
    ears_front = ['earL', 'earR'] if 30 < psi < 150 else ['ear' + ear_near]
    ears_back = [e for e in ('earL', 'earR') if e not in ears_front]
    headgrp = ears_back + ['head'] + ears_front
    up_near = [SLOTS_LEG['f' + near][2], SLOTS_LEG['h' + near][3]]
    lo_near = SLOTS_LEG['h' + near][:3] + SLOTS_LEG['f' + near][:2]
    if 67.5 <= phi <= 112.5:
        order = (SLOTS_LEG['f' + far] + SLOTS_LEG['f' + near] + ['neck'] + headgrp + ['torso'] +
                 SLOTS_LEG['h' + far] + SLOTS_LEG['h' + near] + ['tail'])
    else:
        head_front = phi < 32 or phi > 148
        tail_front = 50 <= phi <= 130
        order = SLOTS_LEG['f' + far] + SLOTS_LEG['h' + far]
        if not tail_front: order += ['tail']
        if not head_front: order += headgrp
        order += ['neck'] + up_near + ['torso']
        if tail_front: order += ['tail']
        order += lo_near
        if head_front: order += headgrp
    return att, order
