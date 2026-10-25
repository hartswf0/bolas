"""SCION 03 Ernst · the dog maquette.  A solid dog of round cones and ellipsoids (an anatomical-plate dog), posed from typed
parameters, its paws placed by the step solver (gait.py) and its legs closed by two-bone IK.

Local frame: F forward (nose direction), Y up, S side.  World yaw phi: F = (cos phi, 0, sin phi); phi = 180 deg faces the
door (world -x), 0 deg faces away (world +x), 90 deg faces the viewer (+z): every turn passes through the face.
"""
import numpy as np
from sdf import cone, ellip

Y = np.array([0.0, 1.0, 0.0])
D2R = np.pi / 180


def frame(phi):
    F = np.array([np.cos(phi), 0.0, np.sin(phi)])
    S = np.cross(F, Y)
    return F, S


def lerp(a, b, t):
    return a + (b - a) * t


def ik2(J, T, l1, l2, hint):
    """two-bone IK: joint J, target T, bone lengths, bend hint (world vector).  Returns the middle joint."""
    d = T - J
    L = np.linalg.norm(d)
    L = np.clip(L, 1e-4, l1 + l2 - 1e-4)
    dn = d / max(np.linalg.norm(d), 1e-9)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = np.sqrt(max(l1 * l1 - a * a, 0.0))
    b = hint - dn * (hint @ dn)
    b /= max(np.linalg.norm(b), 1e-9)
    return J + dn * a + b * h


def rot_axes(F, S, ang_up):
    """axes for a part pointing along F rotated up by ang (about S)."""
    f = F * np.cos(ang_up) + Y * np.sin(ang_up)
    u = np.cross(S, f) if False else (Y * np.cos(ang_up) - F * np.sin(ang_up))
    return f, u


def ell_axes(f, u):
    f = f / np.linalg.norm(f)
    u = u - f * (u @ f); u /= np.linalg.norm(u)
    s = np.cross(f, u)
    return np.stack([f, u, s], axis=1)


LEG = dict(fore=(0.175, 0.2, 0.07), hind=(0.19, 0.205, 0.11))


def rest_paws(lie, crouch):
    """paw positions in the local sagittal frame (forward, up, side) for standing / lying."""
    sf = 0.072
    stand = {'LF': (0.19, 0.025, sf), 'RF': (0.19, 0.025, -sf), 'LH': (-0.185, 0.025, sf), 'RH': (-0.185, 0.025, -sf)}
    lying = {'LF': (0.44, 0.022, 0.06), 'RF': (0.41, 0.022, -0.05), 'LH': (0.0, 0.022, 0.14), 'RH': (-0.04, 0.022, -0.12)}
    out = {}
    for k in stand:
        a = np.array(stand[k]); b = np.array(lying[k])
        a = a + np.array([0.02 * crouch * (1 if k[1] == 'F' else -1), 0, 0])
        out[k] = lerp(a, b, lie)
    return out


def body_points(p):
    """the torso skeleton (local sagittal coordinates) from the posture parameters."""
    lie, cr = p['lie'], p['crouch']
    chest = np.array([0.17, 0.475 - 0.08 * cr, 0.0])
    rump = np.array([-0.19, 0.485 - 0.13 * cr, 0.0])
    chest = lerp(chest, np.array([0.18, 0.165, 0.0]), lie)
    rump = lerp(rump, np.array([-0.18, 0.145, 0.0]), lie)
    chest[1] += p.get('breath', 0.0)
    return chest, rump


K = 1.2      # the maquette is built at unit size and scaled about its root: a large dog (shoulder ~0.7 m)


def build(p):
    """p: x, z, phi, lie, crouch, head, rest, look, ear, tail, wag, paws (world dict).  returns (prims, joints).
    The paws arrive in world coordinates (from the step solver, already at scale K); the body is built at unit scale
    about the root and then scaled by K, so the IK sees the paws in unit space."""
    root = np.array([p['x'], p.get('y', 0.0), p['z']])
    p = dict(p)
    p['paws'] = {k: root + (np.asarray(v, float) - root) / K for k, v in p['paws'].items()}
    prims, J = _build(p, root)
    for pr in prims:
        if pr.kind == 'cone':
            pr.a = root + (pr.a - root) * K; pr.b = root + (pr.b - root) * K; pr.r1 *= K; pr.r2 *= K
        else:
            pr.c = root + (pr.c - root) * K; pr.rad = pr.rad * K
        pr.k *= K
    for k, v in list(J.items()):
        if k == 'hf':
            continue
        J[k] = root + (v - root) * K
    return prims, J


def _build(p, root):
    F, S = frame(p['phi'])

    def W(v):
        return root + F * v[0] + Y * v[1] + S * v[2]

    prims = []
    J = {}
    chest, rump = body_points(p)
    c_w, r_w = W(chest), W(rump)
    spine = c_w - r_w
    # torso: chest barrel, loin, haunch
    ax_t = ell_axes(spine, Y)
    prims.append(ellip('chest', c_w, ax_t, (0.18, 0.185, 0.135), 'coat', k=0.0))
    prims.append(cone('loin', c_w - spine * 0.2 + Y * 0.035, r_w + spine * 0.2 + Y * 0.03, 0.125, 0.108, 'coat', Y, k=0.07))
    prims.append(ellip('haunch', r_w, ax_t, (0.135, 0.14, 0.12), 'coat', k=0.06))
    J['chest'] = c_w; J['rump'] = r_w
    # neck and head
    h = p['head']
    rest = p['rest']
    alpha = (-60 + 115 * min(h, 1.0)) * D2R
    n0 = chest + np.array([0.13, 0.095 - 0.02 * p['lie'], 0])
    # gaze: yaw of the head relative to the body
    yaw = 0.0
    pitch_extra = 0.0
    if p.get('look') is not None:
        g = np.asarray(p['look'], float)
        g = g / np.linalg.norm(g)
        yaw = np.arctan2(g @ S, g @ F)
        lim = p.get('yaw_lim', 125 * D2R)
        yaw = float(np.clip(yaw, -lim, lim))
        pitch_extra = np.arcsin(np.clip(g[1], -1, 1)) * 0.4
    yaw *= p.get('look_w', 1.0)
    if p.get('yaw_rel') is not None:
        yaw = float(p['yaw_rel'])
        pitch_extra = float(p.get('gaze_pitch', 0.0))
    nyaw = yaw * 0.55
    ndir_l = np.array([np.cos(alpha) * np.cos(nyaw), np.sin(alpha), np.cos(alpha) * np.sin(nyaw)])
    nlen = 0.17 - 0.03 * rest
    hc = n0 + ndir_l * nlen
    # chin on the paws: the head goes down and forward to rest between the forepaws
    hrest = np.array([0.47, 0.085, 0.0])
    hc = lerp(hc, hrest, rest)
    hc_w = W(hc); n0_w = W(n0)
    prims.append(cone('neck', n0_w, hc_w, 0.1, 0.08, 'coat', Y, k=0.05))
    # head axes: forward rotated by yaw (about Y) and pitch
    hpitch = ((-28 + 45 * h) * (1 - rest) + (-4) * rest) * D2R + pitch_extra * (1 - rest)
    fy = F * np.cos(yaw) + S * np.sin(yaw)
    sy = np.cross(fy, Y)
    hf = fy * np.cos(hpitch) + Y * np.sin(hpitch)
    hu = Y * np.cos(hpitch) - fy * np.sin(hpitch)
    hs = sy
    ax_h = ell_axes(hf, hu)
    prims.append(ellip('skull', hc_w, ax_h, (0.108, 0.09, 0.084), 'coat', k=0.03))
    m0 = hc_w + hf * 0.05 - hu * 0.022
    m1 = hc_w + hf * 0.152 - hu * 0.036
    prims.append(cone('muzzle', m0, m1, 0.066, 0.046, 'muzzle', hu, k=0.04))
    prims.append(ellip('nose', m1 + hf * 0.012 + hu * 0.008, ax_h, (0.026, 0.021, 0.03), 'nose', k=0.008))
    for sgn, nm in ((1, 'eyeL'), (-1, 'eyeR')):
        prims.append(ellip(nm, hc_w + hf * 0.074 + hu * 0.03 + hs * 0.05 * sgn, ax_h, (0.011, 0.009, 0.01), 'eye', k=0.003))
    ear = float(np.clip(p['ear'], 0, 1))
    for sgn, nm in ((1, 'earL'), (-1, 'earR')):
        base = hc_w - hf * 0.035 + hu * 0.06 + hs * 0.05 * sgn
        d_pr = hu * 1.0 + hs * 0.22 * sgn + hf * 0.04
        d_fl = -hf * 1.0 + hu * 0.15 + hs * 0.45 * sgn
        d = lerp(d_fl, d_pr, ear); d /= np.linalg.norm(d)
        cen = base + d * 0.042
        ax_e = ell_axes(d, hf * ear + (hu + hs * sgn) * (1 - ear))
        prims.append(ellip(nm, cen, ax_e, (0.05, 0.032, 0.012), 'ear', k=0.012))
    J['head'] = hc_w; J['nose'] = m1; J['neck'] = n0_w; J['hf'] = hf
    # legs: shoulders and hips, paws from the step solver, IK
    paws = p['paws']
    for k in ('LF', 'RF', 'LH', 'RH'):
        side = 1 if k[0] == 'L' else -1
        fore = k[1] == 'F'
        if fore:
            Jt = W(chest + np.array([0.1, -0.045, 0.07 * side]))
            l1, l2, l3 = LEG['fore']
            pv_l = lerp(np.array([-0.012, 0.068, 0]), np.array([-0.07, 0.012, 0]), p['lie'])
            hint = -F + Y * 0.2
        else:
            Jt = W(rump + np.array([0.0, -0.04, 0.07 * side]))
            l1, l2, l3 = LEG['hind']
            pv_l = lerp(np.array([-0.012, 0.11, 0]), np.array([-0.11, 0.018, 0]), p['lie'])
            hint = F + Y * 0.1
        paw = np.asarray(paws[k], float)
        pv = F * pv_l[0] + Y * pv_l[1]
        wrist = paw + pv
        mid = ik2(Jt, wrist, l1, l2, hint)
        r_up = 0.058 if fore else 0.072
        prims.append(cone('up' + k, Jt, mid, r_up, 0.036, 'pale' if fore else 'coat', F, k=0.04))
        prims.append(cone('lo' + k, mid, wrist, 0.037, 0.029, 'pale', F, k=0.02))
        prims.append(cone('pa' + k, wrist, paw + F * 0.03, 0.026, 0.024, 'pale', F, k=0.015))
        J['paw' + k] = paw; J['mid' + k] = mid; J['hip' + k] = Jt
    # tail
    tau = p['tail']
    ang = (8 - 72 * tau) * D2R
    curl = (-28 * max(0.0, tau - 0.75) + 14 * max(0.0, 0.6 - tau)) * D2R
    wag = p.get('wag_ang', 0.0)
    base = W(rump + np.array([-0.13, 0.075, 0]))
    pts = [base]
    a = ang
    for i in range(4):
        dl = np.array([-np.cos(a) * np.cos(wag * (i + 1) / 3), np.sin(a), np.sin(wag * (i + 1) / 3) * 0.9])
        dl /= np.linalg.norm(dl)
        dw = F * dl[0] + Y * dl[1] + S * dl[2]
        nxt = pts[-1] + dw * 0.078
        if nxt[1] < 0.03:
            nxt[1] = 0.03
        pts.append(nxt)
        a += curl
    rads = [0.04, 0.034, 0.028, 0.022, 0.014]
    for i in range(4):
        prims.append(cone('tail%d' % i, pts[i], pts[i + 1], rads[i], rads[i + 1], 'coat', Y, k=0.02 if i else 0.04))
    J['tail'] = pts[-1]
    return prims, J
