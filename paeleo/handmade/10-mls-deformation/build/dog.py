"""SCION-10 · the dog: one painted hide, a handle set, and the MLS warp that lifts the hide into a body.

handles()            the editable handle set: name -> (u, v) in the hide, mass, protected group
place(pose)          where the handles go for one pose (porch metres x, y and height z); this is the only thing that moves
warp(Q, family)      MLS of the whole hide from the handles: coarse lattice (6 px) evaluated exactly, dense samples bilinear
                     in between (as the paper evaluates on a grid); returns 3D points, normals, colours, labels per sample
Nothing here is a bone: a pose is a set of target points, and the image between them is the MLS solution."""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import mls

H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, '..', 'assets')
META = json.load(open(os.path.join(A, 'dog_hide_meta.json')))
PPM, U0, V0 = META['ppm'], META['u0'], META['v0']
ALPHA = 2.0          # weight exponent (paper: alpha); compared 1.0 / 1.3 / 1.6 / 2.0 in proof/alpha_strip.jpg: below 2 the far flank spikes between handles
GRID = 6             # lattice step in hide pixels


def hw_trunk(u):
    base = 0.255 + 0.035 * np.exp(-((u - 0.17) / 0.12) ** 2) + 0.025 * np.exp(-((u + 0.27) / 0.1) ** 2) - 0.02 * np.exp(-((u + 0.06) / 0.1) ** 2)
    return base * np.clip(1 - np.abs((u + 0.03) / 0.40) ** 5, 0, 1) ** 0.5


# ---- the handle set (source positions in the hide, metres) -------------------------------------------------------------
def handles():
    h = {}
    def add(n, u, v, g='body', m=1.0): h[n] = {'uv': (u, v), 'group': g, 'mass': m}
    for n, u in (('tail_tip', -0.84), ('tail_mid', -0.62), ('tail_base', -0.40), ('croup', -0.26), ('mid', 0.0), ('withers', 0.20), ('neck', 0.40)):
        add(n, u, 0.0, 'tail' if n.startswith('tail') else 'spine')
    for side, s in (('L', 1), ('R', -1)):
        for n, u in (('sh', 0.20), ('mb', 0.0), ('hp', -0.26)):
            add(f'back_{n}_{side}', u, s * 0.12, 'spine')
            add(f'belly_{n}_{side}', u, s * float(hw_trunk(u)) * 0.97, 'flank')
        add(f'neckside_{side}', 0.40, s * 0.17, 'flank')
        add(f'tailside_{side}', -0.52, s * 0.05, 'tail', 0.5)
        add(f'fleg_mid_{side}', 0.215, s * 0.40, 'leg'); add(f'fpaw_{side}', 0.218, s * 0.548, 'leg')
        add(f'hleg_mid_{side}', -0.255, s * 0.40, 'leg'); add(f'hpaw_{side}', -0.265, s * 0.548, 'leg')
        # protected feature: the head is a rigid cluster of handles
        add(f'cheek_{side}', 0.60, s * 0.16, 'head'); add(f'eye_{side}', 0.675, s * 0.082, 'head'); add(f'jaw_{side}', 0.80, s * 0.085, 'head')
        add(f'crown_{side}', 0.60, s * 0.065, 'head')
        add(f'earin_{side}', 0.505, s * 0.10, 'head'); add(f'earout_{side}', 0.595, s * 0.15, 'head'); add(f'eartip_{side}', 0.47, s * 0.27, 'ear')
    add('skull', 0.60, 0.0, 'head'); add('muzzle', 0.76, 0.0, 'head'); add('nose', 0.875, 0.0, 'head')
    return h


HANDLES = handles()
# line-segment handles (the paper's second kind of handle): a segment between two point handles, moved as a straight
# segment between their targets; its influence integrated by 3-point Gauss quadrature along the segment
SEGMENTS = [('tail_base', 'croup'), ('croup', 'mid'), ('mid', 'withers')] + \
    [(f'back_{a}_{s}', f'back_{b}_{s}') for s in 'LR' for a, b in (('hp', 'mb'), ('mb', 'sh'))] + \
    [(f'belly_{a}_{s}', f'belly_{b}_{s}') for s in 'LR' for a, b in (('hp', 'mb'), ('mb', 'sh'))] + \
    [(f'belly_sh_{s}', f'fleg_mid_{s}') for s in 'LR'] + [(f'fleg_mid_{s}', f'fpaw_{s}') for s in 'LR'] + \
    [(f'belly_hp_{s}', f'hleg_mid_{s}') for s in 'LR'] + [(f'hleg_mid_{s}', f'hpaw_{s}') for s in 'LR']
NQ = 3
_GX, _GW = np.polynomial.legendre.leggauss(NQ)
SEG_S = (_GX + 1) / 2
POINT_NAMES = list(HANDLES)
NAMES = POINT_NAMES + [f'{a}~{b}#{k}' for a, b in SEGMENTS for k in range(NQ)]
_PP = {n: np.array(HANDLES[n]['uv']) for n in POINT_NAMES}
P_SRC = np.array([_PP[n] for n in POINT_NAMES] + [_PP[a] + s * (_PP[b] - _PP[a]) for a, b in SEGMENTS for s in SEG_S])
MASS = np.array([HANDLES[n]['mass'] for n in POINT_NAMES] +
                [0.5 * w * NQ * 0.6 for a, b in SEGMENTS for w in _GW])
# head handles in the head's own frame (forward a, left b, up c), metres, relative to the skull centre
HEAD_LOCAL = {'skull': (0, 0, 0), 'muzzle': (0.17, 0, -0.035), 'nose': (0.28, 0, -0.06),
              'crown_L': (0.0, 0.055, -0.012), 'crown_R': (0.0, -0.055, -0.012),
              'cheek_L': (0.01, 0.068, -0.125), 'cheek_R': (0.01, -0.068, -0.125), 'eye_L': (0.07, 0.058, -0.03), 'eye_R': (0.07, -0.058, -0.03),
              'jaw_L': (0.19, 0.04, -0.105), 'jaw_R': (0.19, -0.04, -0.105),
              'earin_L': (-0.035, 0.035, 0.012), 'earin_R': (-0.035, -0.035, 0.012),
              'earout_L': (-0.015, 0.08, -0.035), 'earout_R': (-0.015, -0.08, -0.035)}


def rot_z(v, a):
    c, s = np.cos(a), np.sin(a)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]])


def place(p):
    """pose -> 3D target of every handle. p keys: cx, cy (body centre on the floor), th (heading), curl (rad/m),
    zw, zc (back height at withers and croup), depth (back to belly), spread (half width of the body), neck_yaw, head_yaw
    (absolute), head_z, head_pitch, ear (0 flat .. 1 pricked), tail_el (rad, + up), tail_yaw, paws {name: (x,y,z)}."""
    th, k = p['th'], p['curl']
    C = np.array([p['cx'], p['cy']])
    ss = np.linspace(-0.45, 0.45, 91)
    phi = th + k * ss
    d = np.stack([np.cos(phi), np.sin(phi)], 1)
    xy = np.cumsum(d, 0) * (ss[1] - ss[0]); xy -= xy[45]; xy += C
    def cl(s):
        i = int(round((np.clip(s, -0.45, 0.45) + 0.45) * 100)); return xy[i], phi[i]
    def zb(s):
        return p['zc'] + (p['zw'] - p['zc']) * np.clip((s + 0.26) / 0.46, 0, 1.15)
    Q = {}
    for n, s in (('croup', -0.26), ('mid', 0.0), ('withers', 0.20)):
        Q[n] = np.r_[cl(s)[0], zb(s)]
    for side, sg in (('L', 1), ('R', -1)):
        for n, s in (('sh', 0.20), ('mb', 0.0), ('hp', -0.26)):
            c, ph = cl(s); nrm = np.array([-np.sin(ph), np.cos(ph)])
            # a dog's section: deep at the chest, the belly tucked up toward the hips, the back rounded at its edges
            dk = {'sh': 1.0, 'mb': 0.80, 'hp': 0.66}[n]; wk = {'sh': 1.0, 'mb': 0.88, 'hp': 0.92}[n]
            Q[f'back_{n}_{side}'] = np.r_[c + sg * 0.095 * wk * nrm, zb(s) - 0.04]
            Q[f'belly_{n}_{side}'] = np.r_[c + sg * p['spread'] * wk * nrm, max(zb(s) - p['depth'] * dk, 0.015)]
    # neck and head
    cw, phw = cl(0.20)
    hy, hp = p['head_yaw'], p['head_pitch']
    hdir = np.array([np.cos(hy), np.sin(hy)])
    ndir = np.array([np.cos(p['neck_yaw']), np.sin(p['neck_yaw'])])
    reach = p.get('neck_reach', 0.30)
    skull = np.r_[cw + ndir * reach, p['head_z']]
    Q['neck'] = np.r_[(cw + skull[:2]) / 2 + ndir * 0.02, (zb(0.2) + p['head_z']) / 2 + 0.03]
    nn = np.array([-ndir[1], ndir[0]])
    for side, sg in (('L', 1), ('R', -1)):
        Q[f'neckside_{side}'] = np.r_[Q['neck'][:2] + sg * 0.075 * nn, Q['neck'][2] - 0.15]
    cp, sp = np.cos(hp), np.sin(hp)
    for n, (a, b, c) in HEAD_LOCAL.items():
        v = np.array([a * cp + c * sp, b, -a * sp + c * cp])     # pitch: nose down for hp > 0
        Q[n] = skull + rot_z(v, hy)
    e = p['ear']
    for side, sg in (('L', 1), ('R', -1)):
        loc = np.array([-0.075 - 0.085 * (1 - e), sg * (0.085 + 0.01 * (1 - e)), 0.0 + 0.105 * e])
        v = np.array([loc[0] * cp + loc[2] * sp, loc[1], -loc[0] * sp + loc[2] * cp])
        Q[f'eartip_{side}'] = skull + rot_z(v, hy)
    # tail: a curve that leaves the croup backwards, raised or tucked, swinging side to side
    cb, phb = cl(-0.40)
    back = -np.array([np.cos(phb), np.sin(phb)])
    zt = zb(-0.40) - 0.02
    el, ty = p['tail_el'], p['tail_yaw']
    base = np.r_[cb, zt]
    def tail_pt(L, bend):
        a = el + bend
        dirh = rot_z(np.r_[back, 0], ty * (L / 0.44)); dirh = dirh[:2]
        return base + np.r_[dirh * L * np.cos(a), L * np.sin(a)]
    Q['tail_base'] = base
    Q['tail_mid'] = tail_pt(0.22, 0.0)
    Q['tail_tip'] = tail_pt(0.44, p.get('tail_curl', -0.25))
    if Q['tail_mid'][2] < 0.02: Q['tail_mid'][2] = 0.02
    if Q['tail_tip'][2] < 0.02: Q['tail_tip'][2] = 0.02
    tn = np.array([-back[1], back[0]])
    for side, sg in (('L', 1), ('R', -1)):
        m = 0.5 * (Q['tail_base'] + Q['tail_mid'])
        Q[f'tailside_{side}'] = m + np.r_[sg * 0.045 * tn, 0]
    # legs: from the belly line down to the paws the gait put on the floor
    for side in ('L', 'R'):
        for leg, top in (('f', f'belly_sh_{side}'), ('h', f'belly_hp_{side}')):
            paw = np.asarray(p['paws'][f'{leg}paw_{side}'], float)
            Q[f'{leg}paw_{side}'] = paw
            t = Q[top]
            mid = 0.5 * (t + paw)
            # a knee: the middle of the leg sits a little forward (front) or back (hind) of the line
            c, ph = cl(0.2 if leg == 'f' else -0.26)
            fw = np.array([np.cos(ph), np.sin(ph)])
            knee = p.get('knee', 0.03)
            mid[:2] += fw * (knee if leg == 'f' else -knee)
            Q[f'{leg}leg_mid_{side}'] = mid
    pts = [Q[n] for n in POINT_NAMES] + [Q[a] + s * (Q[b] - Q[a]) for a, b in SEGMENTS for s in SEG_S]
    return np.array(pts)


# ---- the sheet -------------------------------------------------------------------------------------------------------
class Hide:
    def __init__(self, sample=0.5):
        im = Image.open(os.path.join(A, 'dog_hide.png')).convert('RGBA')
        lab = Image.open(os.path.join(A, 'dog_labels.png'))
        self.W, self.H = im.size
        f = int(round(1 / sample))
        big = np.asarray(im.resize((self.W * f, self.H * f), Image.BILINEAR), float) / 255
        labb = np.asarray(lab.resize((self.W * f, self.H * f), Image.NEAREST))
        keep = big[..., 3] > 0.03
        yy, xx = np.nonzero(keep)
        self.sx = (xx + 0.5) / f; self.sy = (yy + 0.5) / f            # hide pixel coords of each sample
        self.rgb = big[yy, xx, :3]; self.a = big[yy, xx, 3]; self.lab = labb[yy, xx]
        # lattice
        gx = np.arange(0, self.W + GRID, GRID); gy = np.arange(0, self.H + GRID, GRID)
        self.gx, self.gy = gx, gy
        GX, GY = np.meshgrid(gx, gy)
        self.lat_uv = np.c_[U0 + GX.ravel() / PPM, V0 + GY.ravel() / PPM]
        self.lat_shape = GX.shape
        a = np.asarray(im, float)[..., 3] / 255
        occ = ndi.maximum_filter(a > 0.02, GRID * 2 + 1)
        self.lat_used = occ[np.clip(GY, 0, self.H - 1), np.clip(GX, 0, self.W - 1)].ravel()
        self.cg = np.c_[self.sy / GRID, self.sx / GRID].T              # map_coordinates coords

    def warp(self, Q3, family='affine', alpha=ALPHA, src=None):
        """Q3: (M,3) handle targets. Returns per-sample world points (n,3) and normals (n,3)."""
        P = P_SRC if src is None else src
        L = np.full((len(self.lat_uv), 3), np.nan)
        U = self.lat_uv[self.lat_used]
        if family == 'affine':
            L[self.lat_used] = mls.deform(U, P, Q3, MASS, alpha, 'affine')
        else:   # plane families move x, y; the height is always the affine MLS of the handle heights
            L[self.lat_used, :2] = mls.deform(U, P, Q3[:, :2], MASS, alpha, family)
            L[self.lat_used, 2:] = mls.deform(U, P, Q3[:, 2:], MASS, alpha, 'affine')
        L = L.reshape(self.lat_shape + (3,))
        L = np.where(np.isnan(L), 0, L)
        pts = np.stack([ndi.map_coordinates(L[..., c], self.cg, order=1, mode='nearest') for c in range(3)], 1)
        du = np.gradient(L, axis=1); dv = np.gradient(L, axis=0)   # d/du (forward) and d/dv (left) on the lattice
        nrm = np.cross(du, dv)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
        N = np.stack([ndi.map_coordinates(nrm[..., c], self.cg, order=1, mode='nearest') for c in range(3)], 1)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        return pts, N, L


def source_points_px():
    """handle positions in hide pixels (for drawing the handle set)."""
    return np.c_[(P_SRC[:, 0] - U0) * PPM, (P_SRC[:, 1] - V0) * PPM]


def segment_index():
    return {(a, b): (POINT_NAMES.index(a), POINT_NAMES.index(b)) for a, b in SEGMENTS}
