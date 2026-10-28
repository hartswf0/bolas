"""SCION 11 · the video-puppet rig: pose controls -> handle targets -> bent footage.

pose(params)   : canon handle targets for one key (the deformation the puppeteer applies)
mls_inverse()  : moving-least-squares rigid deformation, evaluated backwards
                 (for each film pixel: where in the kit frame does it come from)
render_dog()   : one dog layer for one frame: blends at most two keys of the turn axis,
                 warps each key's real pixels to the same handle targets, returns RGBA
                 plus measurements taken from the warp field itself (head position, folds).
"""
import numpy as np
from scipy import ndimage
from puppets import NAMES, BODY, LEGS, FAR, NEAR, load

IDX = {n: i for i, n in enumerate(NAMES)}
KEYS = [('L', False), ('F', False), ('F', True), ('L', True)]
HEAD_GAIN = {'L': 1.0, 'F': 0.3}  # turn axis: L, F', F, R (flip = faces right)


def rot(v, c, deg):
    a = np.radians(deg)
    ca, sa = np.cos(a), np.sin(a)
    d = v - c
    return c + np.stack([d[..., 0] * ca - d[..., 1] * sa, d[..., 0] * sa + d[..., 1] * ca], -1)


def lerp(a, b, t):
    return a + (b - a) * t


def pose(canon, p, t=0.0, hg=1.0):
    """canon: (K,2) handles of a key (facing left, anchor at 0,0). p: pose controls."""
    T = canon.copy()
    g = lambda n: T[IDX[n]]
    c, lie, head = p.get('crouch', 0), p.get('lie', 0), p.get('head', .9)
    rest, look, tail, wag = p.get('rest', 0), p.get('look', 0), p.get('tail', .5), p.get('wag', 0)
    # --- crouch: the whole top line sinks, knees give
    for n, d in [('withers', 13), ('back', 12), ('rump', 10), ('tailroot', 9), ('chest', 9), ('belly', 9),
                 ('flank', 8), ('nose', 14), ('skull', 14), ('throat', 12), ('tailmid', 9), ('tailtip', 9),
                 ('ft1', 9), ('ft2', 9), ('ht1', 8), ('ht2', 8)]:
        T[IDX[n], 1] += c * d
    for n in ['fk1', 'fk2']:
        T[IDX[n]] += (-4 * c, 5 * c)
    for n in ['hk1', 'hk2']:
        T[IDX[n]] += (-6 * c, 5 * c)
    # --- lie: the body goes to the ground, front legs reach forward, hind legs fold under
    top = {'withers': 40, 'back': 42, 'rump': 36, 'tailroot': 36, 'nose': 40, 'skull': 40, 'throat': 40}
    for n, d in top.items():
        T[IDX[n], 1] += lie * d
    for n, y in [('chest', -12), ('belly', -10), ('flank', -12), ('ft1', -15), ('ft2', -13), ('ht1', -17), ('ht2', -15)]:
        T[IDX[n], 1] = lerp(T[IDX[n], 1], y, lie)
    ll = np.clip(lie * 1.3, 0, 1)
    for leg, (tp, kn, ft) in LEGS.items():
        x = canon[IDX[tp], 0]
        if leg[0] == 'f':   # forelegs reach forward along the floor
            kt, fo = np.array([x - 20, -7.]), np.array([x - 44, -3.])
        else:               # hind legs fold forward under the haunch
            kt, fo = np.array([x - 14, -7.]), np.array([x - 34, -3.])
        if leg in FAR:
            kt[1] -= 3; fo[1] -= 4
        T[IDX[kn]] = lerp(T[IDX[kn]], kt, ll)
        T[IDX[ft]] = lerp(T[IDX[ft]], fo, ll)
    # --- head: rotation about the root of the neck (head 0.9 = as filmed)
    piv = lerp(g('withers'), g('throat'), .55)
    th = np.clip((0.9 - head) * 135, -25, 68)
    th = lerp(th, 58, rest)
    th = lerp(th, 30, look)
    hd = [IDX[n] for n in ['nose', 'skull', 'throat']]
    T[hd] = rot(T[hd], piv, -th * hg)
    # below head 0.4 the neck reaches down instead of the head spinning further (a spin folds the pixels)
    drop = max(0.0, 0.4 - head) * 70 * (1 - look)
    T[hd] += np.array([-0.25 * drop, drop]) * (0.5 + 0.5 * hg)
    T[hd] += np.array([-6., 16.]) * rest * lie   # chin down onto the paws: the neck stretches
    if look > 0:  # the muzzle points away, into the door: it shortens toward the skull
        sk = T[IDX['skull']].copy()
        T[IDX['nose']] = lerp(T[IDX['nose']], sk + (T[IDX['nose']] - sk) * .45, look)
        T[IDX['skull']] += (5 * look, 3 * look)
        T[hd] += np.array([-12., -3.]) * look   # the neck reaches in over the sill
    # --- tail: about its root (0 high, 0.5 as filmed, 1.35 tucked), plus wag
    tr = g('tailroot').copy()
    ang = (tail - .5) * 62 + wag * 24 * np.sin(2 * np.pi * 2.6 * t)
    tl = [IDX['tailmid'], IDX['tailtip']]
    T[tl] = rot(T[tl], tr, ang)
    if lie > 0:  # lying, the tail lies out along the ground
        T[IDX['tailmid'], 1] = lerp(T[IDX['tailmid'], 1], -9, lie * .8)
        T[IDX['tailtip'], 1] = lerp(T[IDX['tailtip'], 1], -4, lie * .8)
    # --- walking: foot offsets come from the gait planner (planted feet are fixed on the floor)
    for n, (dx, lift) in p.get('feet', {}).items():
        T[IDX[n]] += (dx, -lift)
        k = {'f1': 'fk1', 'f2': 'fk2', 'h1': 'hk1', 'h2': 'hk2'}[n]
        T[IDX[k]] += (dx * .55, -lift * .7)
    bob = p.get('bob', 0)
    for n in BODY:
        T[IDX[n], 1] += bob
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


def soften(Qh, Th, f):
    """the rigid motion Qh->Th, keeping its translation but only a fraction f of its rotation"""
    qc, tc = Qh.mean(0), Th.mean(0)
    a = (Qh - qc)[:, 0] + 1j * (Qh - qc)[:, 1]
    b = (Th - tc)[:, 0] + 1j * (Th - tc)[:, 1]
    ang = np.angle((np.conj(a) * b).sum()) * f
    r = a * np.exp(1j * ang)
    return np.stack([r.real, r.imag], 1) + tc


class DogRig:
    def __init__(self):
        self.P = load()

    def targets(self, key_i, params, anchor, scale, t):
        name, flip = KEYS[key_i]
        T = pose(self.P[name]['canon'], params, t, HEAD_GAIN[name])
        if flip:
            T[:, 0] = -T[:, 0]
        return anchor + T * scale

    def warp(self, name, flip, T, x0, y0, w, h, step=3):
        """bend one key's pieces to the targets T; composite far legs, body, near legs."""
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
        G = np.zeros((h, w)); A = np.zeros((h, w)); HW = np.zeros((h, w))
        dets = []
        order = FAR + ['body'] + NEAR + ['head']
        for pc in order:
            ids = [IDX[n] for n in (BODY if pc == 'body' else ['nose', 'skull', 'throat'] if pc == 'head' else LEGS[pc])]
            alpha = 1.15 if pc == 'body' else 1.6
            Tp = T[ids].copy()
            if pc == 'body':  # under the rigid head the neck only follows part of the head's turn
                hi = [IDX[n] for n in ('nose', 'skull', 'throat')]
                Tp[:3] = soften(Q[hi], T[hi], .35)
            sx, sy = mls_inverse(Tp, Q[ids], xs, ys, alpha)
            jx_x = np.gradient(sx, axis=1); jx_y = np.gradient(sx, axis=0)
            jy_x = np.gradient(sy, axis=1); jy_y = np.gradient(sy, axis=0)
            det = (jx_x * jy_y - jx_y * jy_x) / step ** 2
            inside = ndimage.map_coordinates(pcs[pc], [sy, sx], order=1, mode='constant', cval=0) > .5
            dets.append(det[inside])
            fx = ndimage.map_coordinates(sx, [GY, GX], order=1)
            fy = ndimage.map_coordinates(sy, [GY, GX], order=1)
            a = np.clip(ndimage.map_coordinates(pcs[pc], [fy, fx], order=1, mode='constant', cval=0), 0, 1)
            if a.max() < 1e-3:
                continue
            g = np.clip(ndimage.map_coordinates(img, [fy, fx], order=3, mode='constant', cval=0), 0, 1)
            if pc in FAR:
                g = g * .72  # the far legs sit in the body's shade
            G = g * a + G * (1 - a)
            A = a + A * (1 - a)
            if pc == 'head':
                HW = a + HW * (1 - a)
            else:
                HW = HW * (1 - a)
        G = np.where(A > 1e-4, G / np.maximum(A, 1e-4), 0)
        return G, A, HW, np.concatenate(dets)

    def render(self, k, params, anchor, scale, t, margin=70):
        """k: position on the turn axis (0 L, 1 F', 2 F, 3 R). returns layer dict."""
        k = float(np.clip(k, 0, 3))
        a = int(np.floor(k)); s = k - a
        if a == 3:
            a, s = 2, 1.0
        Ta = self.targets(a, params, anchor, scale, t)
        if a == 1 and s > 1e-4:
            # F' -> F: the two three-quarter views are mirror images; morphing between them folds the face
            # (ledger attempt 2). They are swapped like cut-outs instead, each at its own shape, with a slight
            # narrowing at the swap as the head passes the camera.
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
            g, al, hw, d = self.warp(name, flip, T, x0, y0, w, h)
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
                    det_max=float(dets.max()) if dets.size else 1.0)
