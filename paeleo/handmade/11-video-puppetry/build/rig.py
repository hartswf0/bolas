"""SCION 11 · the video-puppet rig (repair round): pose controls -> handle targets -> bent footage.

The body sheet of the footage bends (rigid moving-least-squares on 12 body handles). The head
with its neck, the tail and the four legs are rigid cut-outs from the same frame, pinned at a joint:
each is placed by the least-squares rigid fit of its own handles to their targets, so they can turn
as far as a pose needs without tearing (the critic's repair 2). Big moves -- a head going down, a
leg folding under a lying dog -- are joint rotations; the bending is kept to the body's own sheet.

pose(params)   : canon handle targets for one key (joint rotations + body handle moves)
render()       : one dog layer for one frame, blending at most two keys of the turn axis
"""
import numpy as np
from scipy import ndimage
from puppets import NAMES, BODY, LEGS, FAR, NEAR, NECK, TAILP, load

IDX = {n: i for i, n in enumerate(NAMES)}
KEYS = [('L', False), ('F', False), ('F', True), ('L', True)]  # turn axis: L, F', F, R (flip = faces right)
HEAD_GAIN = {'L': 1.0, 'F': 0.3}


def rot(v, c, deg):
    a = np.radians(deg)
    ca, sa = np.cos(a), np.sin(a)
    d = v - c
    return c + np.stack([d[..., 0] * ca - d[..., 1] * sa, d[..., 0] * sa + d[..., 1] * ca], -1)


def lerp(a, b, t):
    return a + (b - a) * t


def pose(canon, p, t=0.0, hg=1.0):
    """canon: (K,2) handles of a key (facing left, anchor at 0,0). p: pose controls.
    Angle convention (rot(), screen y down): +deg swings a hanging leg forward and a tail down;
    the head is turned by -th, so +th lowers it."""
    T = canon.copy()
    c, lie, head = p.get('crouch', 0), p.get('lie', 0), p.get('head', .9)
    rest, look, tail, wag = p.get('rest', 0), p.get('look', 0), p.get('tail', .5), p.get('wag', 0)
    body = [IDX[n] for n in BODY]
    # --- crouch: the top line sinks a little more than the belly
    for n, d in [('withers', 13), ('back', 12), ('rump', 10), ('tailroot', 9), ('chest', 9), ('belly', 8),
                 ('flank', 8), ('neckbase', 11), ('ft1', 9), ('ft2', 9), ('ht1', 8), ('ht2', 8)]:
        T[IDX[n], 1] += c * d
    # --- lie: the whole body sheet goes down level (hindquarters as low as the shoulders)
    ground_gap = canon[IDX['belly'], 1]  # belly height above the floor (negative)
    T[body, 1] += lie * (-ground_gap - 7)
    # --- legs: rigid, pinned at their tops
    feet = p.get('feet', {})
    for leg, (tp, kn, ft) in LEGS.items():
        top0 = canon[IDX[tp]]
        ids = [IDX[kn], IDX[ft]]
        seg = canon[ids] - top0
        ln = np.hypot(*seg[-1])
        a = 0.0
        if leg in feet:  # walking: swing so the foot sits where the gait planner put it
            dx = feet[leg][0]
            a = np.degrees(np.arcsin(np.clip(-dx / ln, -.8, .8)))
        a += c * (-6 if leg[0] == 'f' else 8)
        # lying: forelegs forward along the boards, hind legs folded forward under the haunch
        a = lerp(a, 84 if leg[0] == 'f' else 104, np.clip(lie * 1.2, 0, 1))
        T[ids] = rot(T[IDX[tp]] + seg, T[IDX[tp]], a)
    # stance feet rise a little when the rigid leg swings; let the body down by the same amount
    if feet:
        rises = []
        for leg, (tp, kn, ft) in LEGS.items():
            if leg in feet and feet[leg][1] <= .3:
                rises.append(T[IDX[tp], 1] - canon[IDX[tp], 1] + canon[IDX[ft], 1] - T[IDX[ft], 1])
        if rises:
            sink = float(np.mean(rises)) - c * 8.5
            T[body, 1] += max(0.0, sink)
            for leg, (tp, kn, ft) in LEGS.items():
                T[[IDX[kn], IDX[ft]], 1] += max(0.0, sink)
    # --- head with neck: rigid, about the neck base (head 0.9 = as filmed)
    nb = T[IDX['neckbase']]
    hd = [IDX[n] for n in ['nose', 'skull', 'throat']]
    T[hd] = canon[hd] - canon[IDX['neckbase']] + nb
    th = (0.9 - head) * 105
    th = lerp(th, 72, rest)
    th = lerp(th, 22, look)
    T[hd] = rot(T[hd], nb, -th * hg)
    # --- tail: rigid about its root (0 high, 0.5 as filmed, 1.35 tucked), plus wag
    tr = T[IDX['tailroot']]
    tl = [IDX['tailmid'], IDX['tailtip']]
    T[tl] = canon[tl] - canon[IDX['tailroot']] + tr
    ang = (tail - .5) * 55 + wag * 22 * np.sin(2 * np.pi * 2.6 * t)
    ang = lerp(ang, 16, lie * .8)   # lying, the tail lies out along the floor
    T[tl] = rot(T[tl], tr, ang)
    bob = p.get('bob', 0)
    T[:, 1] += bob
    return T


def mls_inverse(P, Q, xs, ys, alpha=1.15):
    """rigid MLS (complex form). P: target handles (screen), Q: source handles. Returns source x,y at grid."""
    Pc = P[:, 0] + 1j * P[:, 1]
    Qc = Q[:, 0] + 1j * Q[:, 1]
    X, Y = np.meshgrid(xs, ys)
    V = (X + 1j * Y).ravel()
    d2 = np.abs(V[:, None] - Pc[None, :]) ** 2
    w = 1.0 / (d2 ** alpha + 1e-6)
    sw = w.sum(1)
    ps = (w @ Pc) / sw
    qs = (w @ Qc) / sw
    ph = Pc[None, :] - ps[:, None]
    qh = Qc[None, :] - qs[:, None]
    M = (w * np.conj(ph) * qh).sum(1)
    M = M / (np.abs(M) + 1e-12)
    f = (V - ps) * M + qs
    return f.real.reshape(X.shape), f.imag.reshape(X.shape)


def rigid_fit(Q, P):
    """rotation+translation (with the global puppet scale) taking source handles Q to targets P.
    returns inverse map function screen->source."""
    qc, pc = Q.mean(0), P.mean(0)
    a = (Q - qc)[:, 0] + 1j * (Q - qc)[:, 1]
    b = (P - pc)[:, 0] + 1j * (P - pc)[:, 1]
    M = (np.conj(a) * b).sum() / ((np.abs(a) ** 2).sum() + 1e-9)  # similarity; scale is the puppet scale
    return qc, pc, M


class DogRig:
    def __init__(self):
        self.P = load()

    def targets(self, key_i, params, anchor, scale, t):
        name, flip = KEYS[key_i]
        T = pose(self.P[name]['canon'], params, t, HEAD_GAIN[name])
        if flip:
            T[:, 0] = -T[:, 0]
        return anchor + T * scale

    def warp(self, name, flip, T, x0, y0, w, h, params, step=3):
        pz = self.P[name]
        Q = pz['src'].copy()
        img = pz['img']
        pcs = pz['pieces']
        if flip:  # the same cut-out turned over: mirror the source
            img = img[:, ::-1]; pcs = {k: v[:, ::-1] for k, v in pcs.items()}
            Q[:, 0] = pz['W'] - 1 - Q[:, 0]
        xs = np.arange(x0, x0 + w + step, step, dtype=np.float64)
        ys = np.arange(y0, y0 + h + step, step, dtype=np.float64)
        gy = (np.arange(h) / step); gx = (np.arange(w) / step)
        GX, GY = np.meshgrid(gx, gy)
        yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w].astype(np.float64)
        G = np.zeros((h, w)); A = np.zeros((h, w)); HW = np.zeros((h, w))
        dets = []
        lie = params.get('lie', 0)
        far = FAR + (['h2'] if lie > .3 else [])
        near = [n for n in NEAR if n not in far]
        look = params.get('look', 0)
        wB = float(np.clip((look - .12) / .3, 0, 1)) if name == 'L' else 0.0
        wB = wB * wB * (3 - 2 * wB)
        order = far + ['tail', 'body'] + near + ['neck']
        for pc in order:
            if pc == 'body':
                ids = [IDX[n] for n in BODY]
                sx, sy = mls_inverse(T[ids], Q[ids], xs, ys, 1.15)
                jx_x = np.gradient(sx, axis=1); jx_y = np.gradient(sx, axis=0)
                jy_x = np.gradient(sy, axis=1); jy_y = np.gradient(sy, axis=0)
                det = (jx_x * jy_y - jx_y * jy_x) / step ** 2
                inside = ndimage.map_coordinates(pcs[pc], [sy, sx], order=1, mode='constant', cval=0) > .5
                dets.append(det[inside])
                fx = ndimage.map_coordinates(sx, [GY, GX], order=1)
                fy = ndimage.map_coordinates(sy, [GY, GX], order=1)
            else:
                ids = [IDX[n] for n in (NECK if pc == 'neck' else TAILP if pc == 'tail' else LEGS[pc])]
                qc, pc_, M = rigid_fit(Q[ids], T[ids])
                z = ((xx - pc_[0]) + 1j * (yy - pc_[1])) / M
                fx, fy = z.real + qc[0], z.imag + qc[1]
            a = np.clip(ndimage.map_coordinates(pcs[pc], [fy, fx], order=1, mode='constant', cval=0), 0, 1)
            if pc == 'neck' and wB > 0:   # the head part gives way to the back-of-head piece; the neck stays
                hm0 = ndimage.map_coordinates(pcs['headmap'], [fy, fx], order=1, mode='constant', cval=0)
                a = a * (1 - wB * np.clip(hm0 * 1.6, 0, 1))
                hc_t = np.array([(xx * a).sum(), (yy * a).sum()]) / max(a.sum(), 1)
            if a.max() < 1e-3:
                continue
            g = np.clip(ndimage.map_coordinates(img, [fy, fx], order=3, mode='constant', cval=0), 0, 1)
            if pc in far:
                g = g * .72  # the far legs sit in the body's shade
            G = g * a + G * (1 - a)
            A = a + A * (1 - a)
            if pc == 'neck':
                hm = ndimage.map_coordinates(pcs['headmap'], [fy, fx], order=1, mode='constant', cval=0)
                HW = hm * a + HW * (1 - a)
            else:
                HW = HW * (1 - a)
        if wB > 0:
            # looking in: the head piece is replaced by the back of the head (kit frame 0), pinned at the neck
            B = self.P['B']
            sc = np.hypot(*(T[IDX['withers']] - T[IDX['chest']])) / np.hypot(*(Q[IDX['withers']] - Q[IDX['chest']]))
            sgn = -1 if flip else 1
            up = np.radians(-12 * sgn)  # tipped a little toward the door
            Mb = sc * .92 * np.exp(1j * up)
            hc = (T[IDX['skull']] * .6 + T[IDX['throat']] * .4)   # where the head was
            bc = np.array([129., 96.])                             # the back of the head in frame 0
            z = ((xx - hc[0]) + 1j * (yy - hc[1])) / Mb
            bx, by = z.real + bc[0], z.imag + bc[1]
            if flip:
                bx = 2 * bc[0] - bx
            a = np.clip(ndimage.map_coordinates(B['alpha'], [by, bx], order=1, cval=0), 0, 1) * wB
            g = np.clip(ndimage.map_coordinates(B['img'], [by, bx], order=3, cval=0), 0, 1)
            G = g * a + G * (1 - a)
            A = a + A * (1 - a)
            HW = a + HW * (1 - a)
        G = np.where(A > 1e-4, G / np.maximum(A, 1e-4), 0)
        return G, A, HW, np.concatenate(dets) if dets else np.array([1.0])

    def render(self, k, params, anchor, scale, t, margin=80):
        """k: position on the turn axis (0 L, 1 F', 2 F, 3 R). returns layer dict."""
        k = float(np.clip(k, 0, 3))
        a = int(np.floor(k)); s = k - a
        if a == 3:
            a, s = 2, 1.0
        Ta = self.targets(a, params, anchor, scale, t)
        if a == 1 and s > 1e-4:
            # F' -> F: mirror images; swapped like cut-outs, each at its own shape, slightly narrowed
            kk = 1 if s < .5 else 2
            T = self.targets(kk, params, anchor, scale, t)
            sq = 1 - .14 * np.sin(np.pi * s)
            T = T.copy(); T[:, 0] = anchor[0] + (T[:, 0] - anchor[0]) * sq
            a, s = kk, 0.0
            Ta = T
        if s > 1e-4:
            Tb = self.targets(a + 1, params, anchor, scale, t)
            T = lerp(Ta, Tb, s)
        else:
            T = Ta
        x0 = int(np.floor(T[:, 0].min() - margin)); x1 = int(np.ceil(T[:, 0].max() + margin))
        y0 = int(np.floor(T[:, 1].min() - margin)); y1 = int(np.ceil(T[:, 1].max() + margin * .5))
        w, h = x1 - x0, y1 - y0
        wB = np.clip((s - .42) / .16, 0, 1); wB = wB * wB * (3 - 2 * wB)
        out = None
        dets = []
        for (kk, ww) in ([(a, 1 - wB), (a + 1, wB)] if s > 1e-4 else [(a, 1.0)]):
            if ww <= 1e-3:
                continue
            name, flip = KEYS[kk]
            g, al, hw, d = self.warp(name, flip, T, x0, y0, w, h, params)
            dets.append(d)
            if out is None:
                out = [g * al * ww, al * ww, hw * al * ww]
            else:
                out[0] += g * al * ww; out[1] += al * ww; out[2] += hw * al * ww
        A = np.clip(out[1], 0, 1)
        G = np.where(A > 1e-4, out[0] / np.maximum(out[1], 1e-4), 0)
        H = np.where(A > 1e-4, out[2] / np.maximum(out[1], 1e-4), 0)
        dets = np.concatenate(dets) if dets else np.array([1.0])
        return dict(x0=x0, y0=y0, g=G, a=A, head=H, T=T, det_min=float(dets.min()) if dets.size else 1.0,
                    det_max=float(dets.max()) if dets.size else 1.0,
                    withers=T[IDX['withers']].tolist())
