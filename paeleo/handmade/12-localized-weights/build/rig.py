"""Dog rig: handle transforms from the dog's acting state, then linear blend skinning with the bounded biharmonic weights.

Pose (typed): dict with
  x      world metres of the torso centre (porch axis; threshold at 0, room negative)
  yaw    {'head','front','rear'} degrees (0 = profile facing the door / -x; 180 = back turned)
  lie, crouch, head, rest, look, ear, tail, wag, breath  (score act units, see threshold-score.json)
  paws   {leg: (dx, lift)} gait offsets in profile metres (planted feet; computed by perform.py)
  lookback 0..1  (head raised over the shoulder while the body still faces away)
Output: per-handle 2x3 affines in world metres (y up, ground 0, z toward camera folded into y by OBLIQUE)."""
import os
import numpy as np
import dog as D
import bbw

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
OBLIQUE = 0.22      # camera looks slightly down: depth toward the camera lowers a point on screen
SWING = 0.0         # radius (m) of the arc the shoulders and head swing toward the camera during a turn
DEPTH = {'fn_upper': .065, 'fn_lower': .075, 'ff_upper': -.065, 'ff_lower': -.075, 'hn_upper': .065, 'hn_lower': .075,
         'hf_upper': -.065, 'hf_lower': -.075, 'ear_near': .045, 'ear_far': -.045}
PERSP = 0.0         # nearer groups grow by up to this fraction


def load(h=0.009):
    path = os.path.join(CACHE, 'dog_weights.npz')
    hs = D.handles()
    if os.path.exists(path):
        z = np.load(path, allow_pickle=True)
        return z['V'], z['F'], z['W'], hs
    poly, hs, V, F = D.build(h=h)
    W, info = bbw.solve_bbw(V, F, hs)
    np.savez(path, V=V, F=F, W=W)
    return V, F, W, hs


def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def aff(Lin, p_rest, p_new):
    """Affine with linear part Lin that maps p_rest to p_new."""
    A = np.zeros((2, 3)); A[:, :2] = Lin; A[:, 2] = np.asarray(p_new) - Lin @ np.asarray(p_rest)
    return A


def ang(v):
    return np.arctan2(v[1], v[0])


def ik2(j0, target, l1, l2, knee_sign=-1):
    """Two-bone IK in the plane; the middle joint goes to the side with x*knee_sign largest (-1: toward -x)."""
    d = np.asarray(target) - j0
    dist = np.clip(np.linalg.norm(d), abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4)
    a = ang(d)
    b = np.arccos(np.clip((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1))
    cands = [a + b, a - b]
    knees = [j0 + l1 * np.array([np.cos(c), np.sin(c)]) for c in cands]
    k = int(np.argmax([kn[0] * knee_sign for kn in knees]))
    t1 = cands[k]
    tgt = j0 + dist * np.array([np.cos(a), np.sin(a)])
    t2 = ang(tgt - knees[k])
    return t1, t2


def lerp_ang(a, b, t):
    d = (b - a + np.pi) % (2 * np.pi) - np.pi
    return a + d * t


LIE_ANG = {  # absolute bone directions (degrees) when lying, sphinx: forearms forward, hocks back
    'f': (-40.0, 175.0), 'h': (-150.0, -5.0)}


def tri_groups(F, W, hs):
    """Each triangle's handle group (head / front / rear) by summed weight: the paper layers drawn in depth order mid-turn."""
    names = ['head', 'front', 'rear']
    G = np.zeros((len(W), 3))
    for j, hd in enumerate(hs):
        g = hd['group']
        if g == 'mid':
            G[:, 1] += .5 * W[:, j]; G[:, 2] += .5 * W[:, j]
        else:
            G[:, names.index(g)] += W[:, j]
    return np.argmax(G[F].sum(1), 1)


def pose_affines(P, hs):
    C = np.array(D.J['C'])
    lie, crouch = P['lie'], P['crouch']
    alpha = np.radians(-6.0 * crouch * (1 - lie))
    dy = -0.235 * lie - 0.075 * crouch * (1 - lie)
    R = rot(alpha)

    def root(p):
        return R @ (np.asarray(p) - C) + C + np.array([0, dy])

    out = {}
    # cage: torso, with breathing on the belly vertices
    for hd in hs:
        if hd['kind'] == 'cage':
            p = np.array(hd['p']); q = root(p)
            if p[1] < 0.4:
                q = q + np.array([0, -P.get('breath', 0.0)])
            out[hd['name']] = aff(R, p, q)
    # legs
    for k, (a, b, c) in D.LEGS.items():
        a, b, c = map(np.array, (a, b, c))
        l1, l2 = np.linalg.norm(b - a), np.linalg.norm(c - b)
        j0 = root(a)
        dx, lift = P['paws'].get(k, (0.0, 0.0))
        target = np.array([c[0] + dx, c[1] + lift])
        s1, s2 = ik2(j0, target, l1, l2, knee_sign=-1)
        L1, L2 = np.radians(LIE_ANG[k[0]][0]), np.radians(LIE_ANG[k[0]][1])
        if k[1] == 'f':          # the far legs fold a little differently, so the pair does not read as one leg
            L1 += np.radians(8); L2 += np.radians(-6 if k[0] == 'f' else 6)
        t1 = lerp_ang(s1, L1, lie); t2 = lerp_ang(s2, L2, lie)
        kn = j0 + l1 * np.array([np.cos(t1), np.sin(t1)])
        out[k + '_upper'] = aff(rot(t1 - ang(b - a)), a, j0)
        out[k + '_lower'] = aff(rot(t2 - ang(c - b)), b, kn)
    # neck and head
    N, H = np.array(D.J['N']), np.array(D.J['H'])
    Np = root(N) + np.array([-0.05 * P['look'], 0.0])
    hval = P['head']
    dbeta = np.clip(74.0 * (0.9 - hval) / 0.45, -30, 95)
    rest_b = 91.0
    dbeta = dbeta * (1 - P['rest']) + rest_b * P['rest']
    look_b = 52.0
    dbeta = dbeta * (1 - P['look']) + look_b * P['look']
    lb = P.get('lookback', 0.0)
    dbeta = dbeta * (1 - lb) + 8.0 * lb
    dbeta += P.get('nod', 0.0)
    beta0 = ang(H - N)
    beta = beta0 + np.radians(dbeta) + alpha
    Hp = Np + np.linalg.norm(H - N) * np.array([np.cos(beta), np.sin(beta)])
    out['neck'] = aff(rot(beta - beta0), N, Np)
    head_rest = ang(np.array(hs[1]['b']) - np.array(hs[1]['a']))
    # head direction: follows the neck partly, levels when resting / looking / looking back
    hd_abs = head_rest + np.radians(0.40 * dbeta) + alpha
    level = max(P['rest'], P['look'], lb)
    hd_abs = lerp_ang(hd_abs, head_rest + np.radians(-6.0), level)
    hd_abs += np.radians(P.get('head_tilt', 0.0))
    Rh = rot(hd_abs - head_rest)
    out['head'] = aff(Rh, H, Hp)
    for nm, base in (('ear_near', D.J['EB_n']), ('ear_far', D.J['EB_f'])):
        hd = next(h for h in hs if h['name'] == nm)
        base = np.array(base); tip = np.array(hd['p'])
        e = np.clip(P['ear'], 0, 1)
        er = rot(np.radians(-78.0 * (1 - e) + (4 if nm == 'ear_far' else 0) * (1 - e)))
        tip_local = er @ (tip - base) + base
        bp = Rh @ (base - H) + Hp
        tp = Rh @ (tip_local - base) + bp
        out[nm] = aff(Rh, tip, tp)
    # tail
    T0, T1 = np.array(D.J['T0']), np.array(D.J['T1'])
    ta = P['tail']
    wag = np.radians(P['wag'] * 32.0 * np.sin(P.get('wag_phase', 0.0)))
    a1 = np.radians(-(ta - 0.35) * 78.0) + wag + alpha
    a2 = a1 + np.radians(-(ta - 0.35) * 45.0) + 0.6 * wag
    T0p = root(T0)
    T1p = rot(a1) @ (T1 - T0) + T0p
    out['tail1'] = aff(rot(a1), T0, T0p)
    out['tail2'] = aff(rot(a2), T1, T1p)
    # yaw: head group pivots at the neck base, front and rear at the torso centre
    Cp = root(C)
    A = np.zeros((len(hs), 2, 3))
    yaw = P['yaw']

    def Y(phi, k=1.0):
        f = np.radians(phi)
        return k * np.array([[np.cos(f), 0.0], [OBLIQUE * np.sin(f), 1.0]])

    sf, sh, sr = (np.sin(np.radians(yaw[g])) for g in ('front', 'head', 'rear'))
    # the shoulders swing out toward the camera on an arc, so mid-turn the front half comes forward, lower and larger
    Cf = Cp + np.array([0.0, -OBLIQUE * SWING * sf])
    kf, kh, kr = 1 + PERSP * sf, 1 + PERSP * max(sf, sh), 1 - 0.4 * PERSP * sr
    Np_y = Cf + Y(yaw['front'], kf) @ (Np - Cp)
    for j, hd in enumerate(hs):
        Aj = out[hd['name']]
        g = hd['group']
        if g == 'head':
            M = Y(yaw['head'], kh); piv_r, piv_n = Np, Np_y
        elif g == 'front':
            M = Y(yaw['front'], kf); piv_r, piv_n = Cp, Cf
        elif g == 'rear' and hd['name'].startswith('tail'):
            # the tail never goes edge-on (a paper tail edge-on is a stick): it flicks across, like a wag
            c = np.cos(np.radians(yaw['rear']))
            cc = np.sign(c) * max(abs(c), 0.5) if abs(c) > 1e-6 else 0.5
            M = kr * np.array([[cc, 0.0], [OBLIQUE * sr, 1.0]]); piv_r, piv_n = Cp, Cp
        elif g == 'rear':
            M = Y(yaw['rear'], kr); piv_r, piv_n = Cp, Cp
        else:
            phi = .5 * (yaw['front'] + yaw['rear'])
            M = Y(phi, .5 * (kf + kr)); piv_r, piv_n = Cp, .5 * (Cp + Cf)
        Lin = M @ Aj[:, :2]
        t = M @ (Aj[:, 2] - piv_r) + piv_n
        # limbs have depth: near legs/ear at +z, far ones at -z; yawing the body swings them apart on screen, so a dog
        # seen head-on (or from behind) mid-turn shows two forelegs (two hind legs, two ears) side by side, as in 3D
        z = DEPTH.get(hd['name'], 0.0)
        if z:
            gy = 'head' if g == 'head' else ('front' if g == 'front' else 'rear')
            t = t + np.array([-z * np.sin(np.radians(yaw[gy])), 0.0])
        A[j, :, :2] = Lin; A[j, :, 2] = t
        A[j, 0, 2] += P['x']
    return A
