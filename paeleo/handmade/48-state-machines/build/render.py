"""SCION-48 · the board.

The scene is shown on a hybrid display board of 320 x 180 cells: every cell is itself a tiny two-state machine (a disc that
is flipped black or straw-yellow, and holds its state with no power), and some cells carry an LED. The rule of the board:
what GIVES light is lit (sky, the room behind the door, the window, the moon); what RECEIVES light is flipped (the dog, the
person, the boards, the house). Tone is the density of flipped discs (4x4 ordered dither). A cell that changes state in a
frame is caught mid-flip (narrow disc) for that frame, and clicks (see sound.py).

The dog is a body of joints computed every frame from the machine's body layer (machine.py), sampled into the cells by
ray casting a field of rounded segments. It is never drawn as a picture: it exists only as the set of discs the controller
flips.

python3 render.py START END   (scene frames, END exclusive) -> cache/frames/s%04d.jpg, cache/measure_START.jsonl
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
GW, GH, PITCH, SS = 320, 180, 4, 1
F32 = np.float32

# ------------------------------------------------------------------ cameras: a wide shot, and after the dog lies down a closer one
CAMS = {'wide': ((5.35, 1.02, 6.0), (1.55, 0.62, -0.25), 43.0), 'close': ((3.612, 1.35, 2.026), (0.05, 0.38, -0.2), 46.0)}
CUT_T, CUT_LEN = 24.625, 8          # the cut is a sweep of flips across the board, 8 frames, left to right
TANH = TANV = 1.0
CAM = fw = rt = up = DIRS = None
NR = GW * SS * GH * SS
_cache = {}


def set_camera(name):
    global CAM, fw, rt, up, TANH, TANV, DIRS
    if name not in _cache:
        cam, tgt, fov = CAMS[name]
        c = np.array(cam, F32); f = np.array(tgt, F32) - c; f /= np.linalg.norm(f)
        r = np.cross(f, np.array([0, 1, 0], F32)); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        th = math.tan(math.radians(fov / 2)); tv = th * GH / GW
        uu = ((np.arange(GW * SS) + 0.5) / (GW * SS) * 2 - 1) * th
        vv = (1 - (np.arange(GH * SS) + 0.5) / (GH * SS) * 2) * tv
        UU, VV = np.meshgrid(uu, vv)
        Dd = (f[None, None] + UU[..., None] * r[None, None] + VV[..., None] * u[None, None]).astype(F32)
        Dd /= np.linalg.norm(Dd, axis=-1, keepdims=True)
        _cache[name] = (c, f.astype(F32), r.astype(F32), u.astype(F32), th, tv, Dd.reshape(-1, 3))
    CAM, fw, rt, up, TANH, TANV, DIRS = _cache[name]


def camera_for(i):
    return 'wide' if i < round(CUT_T * 24) else 'close'


set_camera('wide')


def project(P):
    """world -> subsample pixel coords (col,row) and depth"""
    d = P - CAM
    z = d @ fw
    x = (d @ rt) / z / TANH
    y = (d @ up) / z / TANV
    return (x + 1) / 2 * GW * SS, (1 - y) / 2 * GH * SS, z


# ------------------------------------------------------------------ world constants
LAMP = np.array([-1.9, 1.5, -0.45], F32)       # the room's lamp (inside)
WALL_T = 0.15
DOOR_W, DOOR_H = 0.92, 2.03
HINGE = np.array([-WALL_T, 0.0, 0.46], F32)     # hinge on the near jamb; the door swings into the room
KEY = np.array([0.55, 0.62, 0.45], F32); KEY /= np.linalg.norm(KEY)      # last of the dusk, beyond the yard
FILL = np.array([0.15, 0.75, 0.65], F32); FILL /= np.linalg.norm(FILL)
WARM = np.array([255, 168, 92], F32) / 255
DOGX = -0.62                                     # world X of the dog's body centre = score x - 0.62


def door_angle(t):
    a0, a1 = 0.25, 1.52
    if t < 6.2:
        return a0
    s = min(1.0, (t - 6.2) / 0.85)
    s = s * s * (3 - 2 * s)
    return a0 + (a1 - a0) * s


def door_frame(a):
    u = np.array([-math.sin(a), 0, -math.cos(a)], F32)       # from the hinge along the slab
    n = np.array([math.cos(a), 0, -math.sin(a)], F32)
    return u, n


def hash2(a, b):
    return (np.sin(a * 12.9898 + b * 78.233) * 43758.5453) % 1.0


# ------------------------------------------------------------------ analytic world: returns t, normal, albedo, emissive(rgb), id
def plane_hit(O, D, axis, val, cond, tbest, res, mat):
    den = D[:, axis]
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (val - O[axis]) / den
    t = np.where((t > 1e-4) & np.isfinite(t), t, np.inf)
    P = O[None] + D * t[:, None]
    ok = cond(P) & (t < tbest)
    tbest = np.where(ok, t, tbest)
    res[ok] = mat
    return tbest


def world(t_scene):
    O = CAM
    D = DIRS
    tb = np.full(NR, np.inf, F32)
    mat = np.zeros(NR, np.int16)   # 0 sky
    # 1 porch floor, 2 wall, 3 jamb, 4 sill top, 5 sill front, 6 door, 7 room floor, 8 room back, 9 room side, 10 room ceil,
    # 11 porch ceiling, 12 step tops, 13 risers, 14 yard, 15 post, 16 beam, 17 window(emissive), 18 picture, 19 chair
    tb = plane_hit(O, D, 1, 0.0, lambda P: (P[:, 0] > 0.06) & (P[:, 0] < 4.3) & (P[:, 2] > -4.6) & (P[:, 2] < 4.4), tb, mat, 1)
    tb = plane_hit(O, D, 1, 0.035, lambda P: (P[:, 0] > -WALL_T - 0.02) & (P[:, 0] < 0.06) & (np.abs(P[:, 2]) < 0.5), tb, mat, 4)
    tb = plane_hit(O, D, 1, 0.0, lambda P: (P[:, 0] > -0.02) & (P[:, 0] < 0.061) & (P[:, 2] > -4.6) & (P[:, 2] < 3.2) & (np.abs(P[:, 2]) >= 0.5), tb, mat, 1)
    tb = plane_hit(O, D, 0, 0.06, lambda P: (P[:, 1] < 0.035) & (P[:, 1] > 0) & (np.abs(P[:, 2]) < 0.5), tb, mat, 5)
    indoor = lambda P: (np.abs(P[:, 2]) >= 0.46) | (P[:, 1] >= DOOR_H)
    tb = plane_hit(O, D, 0, 0.0, lambda P: (P[:, 2] > -4.6) & (P[:, 2] < 4.4) & (P[:, 1] > 0) & (P[:, 1] < 3.0) & indoor(P), tb, mat, 2)
    tb = plane_hit(O, D, 2, -0.46, lambda P: (P[:, 0] < 0) & (P[:, 0] > -WALL_T) & (P[:, 1] < DOOR_H) & (P[:, 1] > 0), tb, mat, 3)
    tb = plane_hit(O, D, 2, 0.46, lambda P: (P[:, 0] < 0) & (P[:, 0] > -WALL_T) & (P[:, 1] < DOOR_H) & (P[:, 1] > 0), tb, mat, 3)
    tb = plane_hit(O, D, 1, DOOR_H, lambda P: (P[:, 0] < 0) & (P[:, 0] > -WALL_T) & (np.abs(P[:, 2]) < 0.46), tb, mat, 3)
    # room
    tb = plane_hit(O, D, 1, 0.0, lambda P: (P[:, 0] < -WALL_T) & (P[:, 0] > -3.4) & (np.abs(P[:, 2]) < 2.2), tb, mat, 7)
    tb = plane_hit(O, D, 0, -3.4, lambda P: (np.abs(P[:, 2]) < 2.2) & (P[:, 1] < 2.5) & (P[:, 1] > 0), tb, mat, 8)
    tb = plane_hit(O, D, 2, -2.2, lambda P: (P[:, 0] < -WALL_T) & (P[:, 0] > -3.4) & (P[:, 1] < 2.5) & (P[:, 1] > 0), tb, mat, 9)
    tb = plane_hit(O, D, 2, 2.2, lambda P: (P[:, 0] < -WALL_T) & (P[:, 0] > -3.4) & (P[:, 1] < 2.5) & (P[:, 1] > 0), tb, mat, 9)
    tb = plane_hit(O, D, 1, 2.5, lambda P: (P[:, 0] < -WALL_T) & (P[:, 0] > -3.4) & (np.abs(P[:, 2]) < 2.2), tb, mat, 10)
    tb = plane_hit(O, D, 0, -3.38, lambda P: (P[:, 2] > -1.2) & (P[:, 2] < -0.35) & (P[:, 1] > 1.15) & (P[:, 1] < 1.75), tb, mat, 18)
    # a chair inside, in silhouette: a back and a seat
    tb = plane_hit(O, D, 0, -2.3, lambda P: (P[:, 2] > 0.05) & (P[:, 2] < 0.55) & (P[:, 1] > 0.0) & (P[:, 1] < 1.0) & ((P[:, 1] > 0.45) | (np.abs(P[:, 2] - 0.1) < 0.04) | (np.abs(P[:, 2] - 0.5) < 0.04)), tb, mat, 19)
    # porch roof, beam, a far post
    # steps and yard
    for k, (x0, x1, y) in enumerate([(4.3, 4.6, -0.17), (4.6, 4.9, -0.34)]):
        tb = plane_hit(O, D, 1, y, lambda P, x0=x0, x1=x1: (P[:, 0] > x0) & (P[:, 0] < x1) & (np.abs(P[:, 2]) < 1.3), tb, mat, 12)
    for x, y0, y1, zw in [(4.3, -0.17, 0.0, 1.3), (4.6, -0.34, -0.17, 1.3), (4.9, -0.51, -0.34, 1.3)]:
        tb = plane_hit(O, D, 0, x, lambda P, y0=y0, y1=y1, zw=zw: (P[:, 1] > y0) & (P[:, 1] < y1) & (np.abs(P[:, 2]) < zw), tb, mat, 13)
    tb = plane_hit(O, D, 0, 4.3, lambda P: (P[:, 1] > -0.51) & (P[:, 1] < 0.0) & (np.abs(P[:, 2]) >= 1.3) & (P[:, 2] > -4.6) & (P[:, 2] < 4.4), tb, mat, 13)
    tb = plane_hit(O, D, 1, -0.51, lambda P: (P[:, 0] > 0) & (P[:, 0] < 60) & (P[:, 2] < 60), tb, mat, 14)
    # the door slab
    a = door_angle(t_scene)
    u, n = door_frame(a)
    den = D @ n
    with np.errstate(divide='ignore', invalid='ignore'):
        td = ((HINGE - O) @ n) / den
    td = np.where((td > 1e-4) & np.isfinite(td), td, np.inf)
    P = O[None] + D * td[:, None]
    with np.errstate(invalid='ignore'):
        q = (P - HINGE) @ u
    ok = (q > 0) & (q < DOOR_W) & (P[:, 1] > 0) & (P[:, 1] < DOOR_H) & (td < tb)
    tb = np.where(ok, td, tb); mat[ok] = 6
    return tb, mat


def normals_for(mat, D, t_scene):
    N = np.zeros((len(mat), 3), F32)
    N[:, 1] = 1
    for m, nv in [(2, (1, 0, 0)), (5, (1, 0, 0)), (8, (1, 0, 0)), (13, (1, 0, 0)), (16, (1, 0, 0)), (18, (1, 0, 0)), (19, (1, 0, 0)), (11, (0, -1, 0)), (10, (0, -1, 0))]:
        N[mat == m] = nv
    for m in (3, 9, 15):
        s = mat == m
        N[s] = 0
        N[s, 2] = -np.sign(D[s, 2])
    a = door_angle(t_scene)
    _, n = door_frame(a)
    s = mat == 6
    N[s] = n * np.where((D[s] @ n) > 0, -1, 1)[:, None]
    return N


def lamp_vis(P, t_scene):
    """how much of the room's lamp a point sees: through the opening, past the door slab (soft by 3 cm)"""
    vis = np.ones(len(P), F32)
    out = P[:, 0] > -WALL_T + 1e-3
    if not out.any():
        return vis
    Q = P[out]
    L = LAMP
    dx = Q[:, 0] - L[0]
    v = np.ones(len(Q), F32)
    for X in (0.0, -WALL_T):
        s = (Q[:, 0] - X) / dx
        C = Q + (L - Q) * s[:, None]
        mz = np.clip((0.46 - np.abs(C[:, 2])) / 0.03 + 0.5, 0, 1)
        my = np.clip((DOOR_H - C[:, 1]) / 0.03 + 0.5, 0, 1)
        v *= mz * my * (C[:, 1] > -0.01)
    a = door_angle(t_scene)
    u, n = door_frame(a)
    den = (L - Q) @ n
    with np.errstate(divide='ignore', invalid='ignore'):
        s = ((HINGE - Q) @ n) / den
    C = Q + (L - Q) * s[:, None]
    qq = (C - HINGE) @ u
    blk = (s > 0) & (s < 1) & (qq > 0) & (qq < DOOR_W) & (C[:, 1] < DOOR_H)
    soft = np.clip((DOOR_W - qq) / 0.03, 0, 1)
    v *= np.where(blk, 1 - soft, 1)
    vis[out] = v
    return vis


# ------------------------------------------------------------------ the field of rounded segments
class Body:
    """prims: list of (a, b, ra, rb, group, albedo); groups combine with smooth unions."""
    GROUPS = {'torso': 0.07, 'head': 0.03, 'leg': 0.018, 'tail': 0.02, 'p': 0.05}

    def __init__(self, prims, joins, who):
        self.A = np.array([p[0] for p in prims], F32)
        self.B = np.array([p[1] for p in prims], F32)
        self.RA = np.array([p[2] for p in prims], F32)
        self.RB = np.array([p[3] for p in prims], F32)
        self.G = [p[4] for p in prims]
        self.AL = np.array([p[5] for p in prims], F32)
        self.joins = joins      # list of (groupnames, k) in order
        self.who = who
        pts = np.concatenate([self.A, self.B])
        self.c = pts.mean(0)
        self.R = float(np.max(np.linalg.norm(pts - self.c, axis=1)) + self.RA.max() + 0.03)

    def prim_d(self, P):
        pa = P[:, None, :] - self.A[None]
        ba = (self.B - self.A)[None]
        bb = np.maximum((ba * ba).sum(-1), 1e-8)
        h = np.clip((pa * ba).sum(-1) / bb, 0, 1)
        r = self.RA[None] + (self.RB - self.RA)[None] * h
        return np.linalg.norm(pa - ba * h[..., None], axis=-1) - r, h

    def sdf(self, P, parts=False):
        d, h = self.prim_d(P)
        gd = {}
        for k, g in enumerate(self.G):
            base = g.split(':')[0]
            kk = Body.GROUPS[base]
            if g in gd:
                gd[g] = smin(gd[g], d[:, k], kk)
            else:
                gd[g] = d[:, k]
        out = None
        for names, k in self.joins:
            for nme in names:
                if nme not in gd:
                    continue
                out = gd[nme] if out is None else (smin(out, gd[nme], k) if k > 0 else np.minimum(out, gd[nme]))
        if not parts:
            return out
        keys = list(gd.keys())
        stack = np.stack([gd[k2] for k2 in keys], 1)
        gi = np.argmin(stack, 1)
        pi = np.argmin(d, 1)
        return out, [keys[i] for i in range(len(keys))], gi, pi, h


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def march(body, O, D, tmax, steps=56):
    """sphere-trace rays (O fixed point, D[N]) against a body; returns t (inf where missed)"""
    oc = O - body.c
    bq = D @ oc
    cq = oc @ oc - body.R ** 2
    disc = bq * bq - cq
    t = np.where(disc > 0, np.maximum(-bq - np.sqrt(np.maximum(disc, 0)), 0), np.inf).astype(F32)
    alive = np.isfinite(t) & (t < tmax)
    tout = np.full(len(D), np.inf, F32)
    idx = np.nonzero(alive)[0]
    tt = t[idx]
    tfar = np.minimum(tmax[idx], (-bq + np.sqrt(np.maximum(disc, 0)))[idx])
    for _ in range(steps):
        if len(idx) == 0:
            break
        P = O[None] + D[idx] * tt[:, None]
        d = body.sdf(P)
        hit = d < 0.0025
        tout[idx[hit]] = tt[hit]
        tt = tt + d * 0.92
        keep = (~hit) & (tt < tfar)
        idx, tt, tfar = idx[keep], tt[keep], tfar[keep]
    return tout


def body_normal(body, P):
    e = 0.004
    k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], F32)
    n = np.zeros_like(P)
    for kv in k:
        n += kv[None] * body.sdf(P + kv[None] * e)[:, None]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)


# ------------------------------------------------------------------ the dog: joints from the body layer
def ik2(a, target, l1, l2, bend):
    """two-bone solve in 3D: a root, target, bend = preferred direction of the middle joint"""
    d = target - a
    L = np.linalg.norm(d)
    L = min(max(L, 1e-4), l1 + l2 - 1e-4)
    dn = d / max(np.linalg.norm(d), 1e-6)
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    y = math.sqrt(max(l1 * l1 - x * x, 0))
    b = bend - dn * (bend @ dn)
    b = b / max(np.linalg.norm(b), 1e-6)
    mid = a + dn * x + b * y
    end = a + dn * L
    return mid, end


def lerp(a, b, s):
    return a + (b - a) * s


def gait_offset(p, A):
    p = p % 1.0
    if p < 0.66:
        return A * (1 - 2 * p / 0.66), 0.0
    s = (p - 0.66) / 0.34
    s2 = s * s * (3 - 2 * s)
    return -A + 2 * A * s2, math.sin(math.pi * s)


def dog_body(b, x_score, gphase, gait):
    """b: the machine's body layer for this frame. Returns a Body in world coordinates plus named joints."""
    psi, hy = b['psi'], b['head_yaw']
    c, l, rest, look = b['crouch'], b['lie'], b['rest'], b['look']
    head, tail, wag, ear = b['head'], b['tail'], b['wag'], b['ear']
    sm = lambda v: v * v * (3 - 2 * v)
    l = sm(min(max(l, 0), 1))
    X0 = np.array([x_score + DOGX, 0, 0], F32)
    hf = np.array([-math.cos(psi), 0, math.sin(psi)], F32)
    hs = np.array([-math.cos(psi + math.pi / 2), 0, math.sin(psi + math.pi / 2)], F32)
    Y = np.array([0, 1, 0], F32)

    def W(f, y, s):
        return X0 + hf * f + Y * y + hs * s

    # spine bend carries part of the head's turn (front half yaws about the body centre)
    bend = max(-0.4, min(0.4, hy * 0.2))     # the spine carries a little of the turn; the legs never follow it
    rem = hy - bend
    nyaw = max(-1.5, min(1.5, rem * 0.75))
    hyaw = rem - nyaw

    def WB(f, y, s, k=1.0):
        a = bend * k * max(0.0, min(1.0, (f + 0.05) / 0.3))
        ff, ss = f * math.cos(a) - s * math.sin(a), f * math.sin(a) + s * math.cos(a)
        return W(ff, y, ss)

    H = lerp(0.43 - 0.09 * c, 0.155, l)
    Hc = H + lerp(0.01 - 0.03 * c, -0.005, l)
    Hr = H + lerp(0.025 - 0.05 * c, -0.035, l)   # lying, the hips settle lower than the shoulders
    prims = []
    al_b = 0.86
    chest = WB(0.18, Hc - 0.015, 0); ribs = WB(0.05, H + 0.01, 0); loin = W(-0.10, H + 0.035 - 0.02 * l, 0); rump = W(-0.21, Hr + 0.005, 0)
    prims += [(chest, chest, 0.135, 0.135, 'torso', 0.95), (ribs, ribs, 0.118, 0.118, 'torso', al_b),
              (loin, loin, 0.088, 0.088, 'torso', al_b), (rump, rump, 0.102 - 0.01 * l, 0.102 - 0.01 * l, 'torso', al_b * 0.92)]
    # neck and head
    nb_f, nb_y = 0.25, Hc + 0.06
    nb = WB(nb_f, nb_y, 0)
    el = math.radians(lerp(-38, 58, head))
    hp_stand = np.array([nb_f + 0.24 * math.cos(el), nb_y + 0.24 * math.sin(el)])
    pitch_stand = math.radians(lerp(-62, -8, head))
    w0 = max(0.0, 1 - rest - look)
    hp_lie = np.array([0.44, 0.30]) * w0 + np.array([0.43, 0.115]) * rest + np.array([0.70, 0.235]) * look
    hp_lie = hp_lie / max(w0 + rest + look, 1e-6)
    pitch_lie = (math.radians(-16) * w0 + math.radians(-14) * rest + math.radians(1) * look) / max(w0 + rest + look, 1e-6)
    hp = lerp(hp_stand, hp_lie, l)
    pitch = lerp(pitch_stand, pitch_lie, l)
    # yaw the head about the neck base (local f-s plane), then the bend
    rel = np.array([hp[0] - nb_f, 0.0])
    a = nyaw
    hf_loc = nb_f + rel[0] * math.cos(a)
    hs_loc = rel[0] * math.sin(a)
    hc = WB(hf_loc, hp[1], hs_loc)
    prims.append((nb, hc + Y * (-0.02), 0.072, 0.058, 'torso', al_b))
    hyaw += 0.38 * look * l          # looking in: the muzzle turns a little across the lit doorway
    yaw_total = bend + nyaw + hyaw
    hd = np.array([math.cos(yaw_total), 0, math.sin(yaw_total)])  # local f,s direction of the muzzle
    dir_w = hf * hd[0] + hs * hd[2]
    mdir = dir_w * math.cos(pitch) + Y * math.sin(pitch)
    side_w = np.cross(Y, dir_w); side_w /= max(np.linalg.norm(side_w), 1e-6)
    skull = hc
    muz_a = skull + mdir * 0.03 - Y * 0.012
    muz_b = skull + mdir * 0.15 - Y * 0.02
    muz_b = skull + mdir * 0.17 - Y * 0.022
    prims += [(skull + mdir * -0.02, skull + mdir * 0.02, 0.09, 0.086, 'head', 1.0), (muz_a, muz_b, 0.055, 0.036, 'head', 0.8),
              (muz_b + mdir * 0.012, muz_b + mdir * 0.012, 0.022, 0.022, 'head', 0.05)]
    up_h = np.cross(mdir, side_w); up_h /= max(np.linalg.norm(up_h), 1e-6)
    if up_h[1] < 0:
        up_h = -up_h
    for sgn in (1, -1):
        eb = skull - mdir * 0.035 + up_h * 0.065 + side_w * sgn * 0.05
        tipd = up_h * lerp(0.0, 0.095, ear) + mdir * lerp(-0.085, 0.015, ear) + side_w * sgn * lerp(0.03, 0.012, ear) - Y * lerp(0.03, 0, ear)
        prims.append((eb, eb + tipd * 1.15, 0.036, 0.013, 'head', 0.55))
    # legs
    joints = {'head': hc, 'nose': muz_b, 'chest': chest, 'rump': rump,
              'eyes': [skull + mdir * 0.06 + up_h * 0.035 + side_w * sg * 0.048 for sg in (1, -1)]}
    A = 0.21 * gait
    for name, f0, fa, sgn, off in [('lf', 0.19, 0.21, 1, 0.25), ('rf', 0.19, 0.21, -1, 0.75), ('lh', -0.21, -0.23, 1, 0.0), ('rh', -0.21, -0.23, -1, 0.5)]:
        front = name[1] == 'f'
        s0 = 0.072 * sgn
        root = W(f0, (Hc - 0.03) if front else (Hr - 0.01), s0)
        df, lift = gait_offset(gphase + off, A)
        foot_s = W(fa + df, 0.03 + 0.055 * lift * gait, 0.08 * sgn + 0.02 * c * sgn)
        # one solve for every posture: the feet go where the posture puts them, the joints follow (no joint blending)
        if front:
            paw_t = lerp(foot_s, W(0.43, 0.028, 0.068 * sgn), l)
            bendv = -hf - Y * 0.6 * l
            m1, p1 = ik2(root, paw_t, 0.2, 0.215, bendv / np.linalg.norm(bendv))
            prims += [(root, m1, 0.05, 0.036, 'leg:' + name, 0.84), (m1, p1, 0.034, 0.03, 'leg:' + name, 0.88),
                      (p1, p1 + hf * 0.03, 0.031, 0.031, 'leg:' + name, 0.9)]
            joints[name] = p1
        else:
            # lying: the hind leg folds flat along the body, paw forward under the belly, hock tucked under the hip
            paw_t = lerp(foot_s, W(0.0, 0.024, 0.11 * sgn), l)
            hock_t = paw_t + lerp(-hf * 0.05 + Y * 0.10, -hf * 0.17 + Y * 0.02, l)
            bendv = hf + hs * sgn * 0.35 * l * l + Y * 0.3 * l
            sc = 1 - 0.2 * l
            k1, h1 = ik2(root, hock_t, 0.21 * sc, 0.2 * sc, bendv / np.linalg.norm(bendv))
            p1 = paw_t
            prims += [(root, k1, 0.075, 0.045, 'leg:' + name, 0.82), (k1, h1, 0.04, 0.03, 'leg:' + name, 0.84), (h1, p1, 0.028, 0.03, 'leg:' + name, 0.88),
                      (p1, p1 + hf * 0.025, 0.031, 0.031, 'leg:' + name, 0.9)]
            joints[name] = p1
    # tail
    tb = W(-0.30, Hr + 0.05, 0)
    ang = math.radians(45 - 125 * min(tail, 1.35) / 1.35)
    pts = [tb]
    a_ = ang
    wa = wag * 0.7
    for k in range(3):
        a_ -= math.radians(12 + 18 * max(0, tail - 0.8))
        dloc = np.array([-math.cos(a_) * math.cos(wa), math.sin(a_), math.cos(a_) * math.sin(wa)])
        pts.append(pts[-1] + hf * dloc[0] * 0.115 + Y * dloc[1] * 0.115 + hs * dloc[2] * 0.115)
    lie_tail = [tb, W(-0.43, 0.05, -0.07 + wa * 0.05), W(-0.50, 0.03, -0.19 + wa * 0.08), W(-0.45, 0.03, -0.31 + wa * 0.1)]   # laid round the hip, on the porch
    pts = [lerp(p, q, l) for p, q in zip(pts, lie_tail)]
    for k in range(3):
        prims.append((pts[k], pts[k + 1], 0.04 - 0.008 * k, 0.032 - 0.008 * k, 'tail', 0.7 if k < 2 else 0.95))
    joints['tail'] = pts[-1]
    joins = [(['torso', 'head'], 0.03), (['leg:lf', 'leg:rf', 'leg:lh', 'leg:rh'], 0.035), (['tail'], 0.03)]
    return Body([(np.asarray(p[0], F32), np.asarray(p[1], F32), p[2], p[3], p[4], p[5]) for p in prims], joins, 'dog'), joints


# ------------------------------------------------------------------ the person
def person_body(w, t):
    sit = w['sit']; reach = w['reach']; low = w['low']; mouth = w['mouth']
    prog = min(1.0, max(0.0, (w['px'] - (-0.28)) / (-1.25 + 0.28)))   # 0 doorway -> 1 beside
    s = prog * prog * (3 - 2 * prog)
    base = np.array([lerp(0.14, 0.27, s), 0, lerp(0.0, -0.80, s)], F32)
    # facing: toward the porch (+X), turned a little toward the dog's path when seated
    yaw = lerp(0.0, 0.42, s) if prog < 1 else 0.42
    walking = 0.0 < prog < 1.0
    if walking:
        yaw = -1.25
    fx = np.array([math.cos(yaw), 0, math.sin(yaw)], F32)
    fz = np.array([-math.sin(yaw), 0, math.cos(yaw)], F32)
    Y = np.array([0, 1, 0], F32)

    def W(f, y, sd):
        return base + fx * f + Y * y + fz * sd

    ss = sit * sit * (3 - 2 * sit)
    lean = 0.28 * reach + 0.05 * (1.0 if w['voice'] == 'call' else 0.0)
    hip_y = lerp(0.92, 0.14, ss)
    hip_f = lerp(0.0, -0.02, ss)
    sh_y = hip_y + 0.5 * math.cos(lean * (1 - ss))
    sh_f = hip_f + 0.5 * math.sin(lean * (1 - ss)) + 0.02 * ss
    hip = W(hip_f, hip_y, 0); chest = W(sh_f, sh_y, 0)
    head = W(sh_f + 0.05 + 0.08 * lean + 0.03 * (mouth > 0.2), sh_y + 0.22 - 0.03 * (w['voice'] == 'soft'), 0)
    al = 0.4
    prims = [(hip, chest, 0.15, 0.17, 'p', al), (chest, head - Y * 0.1, 0.06, 0.05, 'p', 0.6), (head, head + fx * 0.03, 0.115, 0.105, 'p', 0.95)]
    # legs
    for sgn in (1, -1):
        hj = W(hip_f, hip_y - 0.03, 0.1 * sgn)
        ph = 0.0
        if walking:
            ph = math.sin(prog * math.pi * 4 + (0 if sgn > 0 else math.pi)) * 0.18
        foot_st = W(0.02 + ph, 0.04, 0.11 * sgn)
        foot_si = W(0.66, 0.04, 0.15 * sgn)
        foot = lerp(foot_st, foot_si, ss)
        bend = fx * 1.0 + Y * (0.6 * ss)
        knee, ank = ik2(hj, foot, 0.45, 0.45, bend / np.linalg.norm(bend))
        prims += [(hj, knee, 0.075, 0.06, 'p', 0.42), (knee, ank, 0.06, 0.05, 'p', 0.42), (ank, ank + fx * 0.15, 0.045, 0.04, 'p', 0.3)]
    # arms: right (toward the dog, -z side of the body... uses sgn=-1 as the reaching arm), left pushes the door
    for sgn in (1, -1):
        shj = chest + fz * 0.19 * sgn - Y * 0.03
        hand_rest = shj + fx * 0.05 - Y * 0.58 * (1 - ss) + (fx * 0.25 - Y * 0.32) * ss
        tgt = hand_rest
        if sgn == -1:
            hand_reach = shj + fx * 0.6 - Y * 0.28
            hand_low = W(0.60, 0.10, -0.42)
            tgt = lerp(tgt, hand_reach, reach)
            tgt = lerp(tgt, hand_low, low)
            if w['voice'] == 'call' and reach < 0.2:
                tgt = lerp(tgt, shj + fx * 0.35 + Y * 0.05, 0.6)
        else:
            push = 0.0
            if 5.95 < t < 6.75:
                push = math.sin(math.pi * (t - 5.95) / 0.8)
            a = door_angle(t)
            u, _ = door_frame(a)
            edge = HINGE + u * DOOR_W + Y * 0.95
            tgt = lerp(tgt, edge, push * 0.9)
        el, hd = ik2(shj, tgt, 0.31, 0.31, -Y * 0.6 - fx * 0.4 + fz * 0.3 * sgn)
        prims += [(shj, el, 0.055, 0.05, 'p', 0.55), (el, hd, 0.05, 0.042, 'p', 0.7), (hd, hd + fx * 0.05, 0.055, 0.045, 'p', 1.0)]
    return Body([(np.asarray(p[0], F32), np.asarray(p[1], F32), p[2], p[3], p[4], p[5]) for p in prims], [(['p'], 0.0)], 'person')


# ------------------------------------------------------------------ shading
def shade_surface(P, N, alb, t_scene, shadow_bodies):
    amb = 0.13 + 0.07 * N[:, 1]
    key = 0.42 * np.clip(N @ KEY, 0, 1)
    fill = 0.16 * np.clip(N @ FILL, 0, 1)
    Ld = LAMP[None] - P
    dist = np.linalg.norm(Ld, axis=1)
    Ld = Ld / dist[:, None]
    vis = lamp_vis(P, t_scene)
    # shadows of the dog and the person in the door light
    if shadow_bodies:
        cand = np.nonzero(vis > 0.01)[0]
        for body in shadow_bodies:
            if len(cand) == 0:
                break
            Q = P[cand]; Dd = Ld[cand]
            oc = Q - body.c
            bq = (Dd * oc).sum(1)
            cq = (oc * oc).sum(1) - body.R ** 2
            near = (bq * bq - cq > 0) & (-bq > -body.R)
            sel = cand[near]
            if len(sel) == 0:
                continue
            Q = P[sel] + N[sel] * 0.01; Dd = Ld[sel]
            tt = np.full(len(sel), 0.02, F32)
            mind = np.full(len(sel), 1.0, F32)
            for _ in range(18):
                d = body.sdf(Q + Dd * tt[:, None])
                mind = np.minimum(mind, d / np.maximum(tt, 0.02) * 6)
                tt = tt + np.maximum(d, 0.01)
            vis[sel] *= np.clip(mind, 0.0, 1.0)
    door = 5.5 * vis * np.clip((N * Ld).sum(1), 0, 1) / (1 + 0.07 * dist ** 2)
    return alb * (amb + key + fill + door), vis


BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], F32) + 0.5) / 16
THR = np.tile(BAYER, (GH // 4 + 1, GW // 4 + 1))[:GH, :GW]


def sky(D, t_scene):
    el = np.arcsin(np.clip(D[:, 1], -1, 1))
    az = np.arctan2(D[:, 0], -D[:, 2])
    h = np.clip(el / 0.5, 0, 1)
    col = (np.array([1.0, 0.52, 0.26], F32)[None] * (1 - h)[:, None] ** 1.6 * 0.55 + np.array([0.28, 0.24, 0.55], F32)[None] * h[:, None] * 0.22)
    inten = np.ones(len(D), F32)
    tree = 0.028 + sum(amp * np.sin(az * fq + ph) for amp, fq, ph in
                       ((0.010, 3.1, 0.4), (0.008, 7.7, 2.1), (0.006, 13.3, 0.9), (0.005, 23.9, 4.0), (0.004, 41.0, 1.7), (0.003, 77.0, 3.3), (0.002, 131.0, 0.2)))
    tree = tree + 0.012 * np.maximum(0, np.sin(az * 5.3 + 1.0)) ** 3
    dark = el < tree
    moon_c = np.array([0.55, 0.42, -0.72], F32); moon_c /= np.linalg.norm(moon_c)
    md = D @ moon_c
    moon = md > math.cos(0.022)
    crescent = moon & ~((D @ (moon_c + np.array([0.012, 0.006, 0.0], F32)) / np.linalg.norm(moon_c + np.array([0.012, 0.006, 0.0], F32))) > math.cos(0.02))
    return col, dark, crescent


def render_frame(fr, t_scene, prev_on, gphase, gait):
    tb, mat = world(t_scene)
    b = fr['body']
    dog, joints = dog_body(b, fr['x'], gphase, gait)
    per = person_body(fr['world'], t_scene)
    # characters: march in their screen boxes only
    hitid = np.zeros(NR, np.int8)       # 0 world, 1 dog, 2 person
    tch = np.full(NR, np.inf, F32)
    for k, body in ((1, dog), (2, per)):
        pts = np.concatenate([body.A, body.B])
        cx, cy, z = project(pts)
        pad = 0.25 * GW * SS / (2 * TANH * max(z.min(), 0.5))
        x0, x1 = int(max(0, cx.min() - pad)), int(min(GW * SS, cx.max() + pad))
        y0, y1 = int(max(0, cy.min() - pad)), int(min(GH * SS, cy.max() + pad))
        if x1 <= x0 or y1 <= y0:
            continue
        rr, cc = np.mgrid[y0:y1, x0:x1]
        idx = (rr * GW * SS + cc).ravel()
        tmax = np.minimum(tb[idx], tch[idx])
        th = march(body, CAM, DIRS[idx], tmax)
        hit = th < tmax
        tch[idx[hit]] = th[hit]
        hitid[idx[hit]] = k
    # surfaces
    t_any = np.minimum(tb, tch)
    P = CAM[None] + DIRS * np.where(np.isfinite(t_any), t_any, 0)[:, None]
    tone = np.zeros(NR, F32)
    emis = np.zeros((NR, 3), F32)
    emis_on = np.zeros(NR, bool)
    part = np.zeros(NR, np.int8)
    # world surfaces
    wsel = (hitid == 0) & np.isfinite(tb) & (mat > 0)
    Nw = normals_for(mat, DIRS, t_scene)
    alb = np.zeros(NR, F32)
    Pw = P
    seam_z = np.abs(((Pw[:, 2] + 10) % 0.135) - 0.0675) < 0.009
    alb[mat == 1] = np.where(seam_z, 0.0, 0.24)[mat == 1]
    siding = np.abs(((Pw[:, 1]) % 0.19) - 0.095) < 0.012
    trim = (np.abs(Pw[:, 2]) < 0.6) & (Pw[:, 1] < DOOR_H + 0.13)
    alb[mat == 2] = np.where(trim, 0.5, np.where(siding, 0.0, 0.13))[mat == 2]
    alb[mat == 3] = 0.4; alb[mat == 4] = 0.6; alb[mat == 5] = 0.5
    panel = (np.abs(Pw[:, 1] - 1.0) < 0.03) | (np.abs(Pw[:, 1] - 1.75) < 0.03)
    alb[mat == 6] = np.where(panel, 0.1, 0.35)[mat == 6]
    alb[mat == 11] = 0.08; alb[mat == 12] = 0.3; alb[mat == 13] = 0.15; alb[mat == 15] = 0.35; alb[mat == 16] = 0.4
    grass = hash2(np.floor(Pw[:, 0] * 18), np.floor(Pw[:, 2] * 18)) * 0.35
    alb[mat == 14] = (0.05 + 0.6 * grass)[mat == 14]
    v, _ = shade_surface(P[wsel], Nw[wsel], alb[wsel], t_scene, [dog, per])
    tone[wsel] = v
    # the lit room and the window are light
    room = (mat >= 7) & (mat <= 10) & (hitid == 0)
    if room.any():
        Q = P[room]
        dl = np.linalg.norm(Q - LAMP[None], axis=1)
        base = {7: 0.62, 8: 0.95, 9: 0.75, 10: 0.45}
        bi = np.array([base[m] for m in mat[room]], F32) if False else np.select([mat[room] == 7, mat[room] == 8, mat[room] == 9], [0.62, 0.95, 0.75], 0.45)
        rug = (mat[room] == 7) & (np.abs(Q[:, 2] - 0.1) < 0.7) & (Q[:, 0] < -0.9) & (Q[:, 0] > -2.4)
        inten = bi * (0.55 + 0.9 / (1 + 0.5 * dl ** 2)) * np.where(rug, 0.7, 1.0)
        emis[room] = WARM[None] * inten[:, None]
        emis_on[room] = True
    for m in (18, 19):
        s = (mat == m) & (hitid == 0)
        tone[s] = 0.03
    # sky
    ssel = (hitid == 0) & ~np.isfinite(tb)
    col, dark, cres = sky(DIRS[ssel], t_scene)
    e = col.copy()
    e[cres] = np.array([0.95, 0.92, 0.8], F32)
    on = ~dark
    stars = (hash2(np.floor(DIRS[ssel][:, 0] * 260), np.floor(DIRS[ssel][:, 1] * 260)) > 0.996) & (DIRS[ssel][:, 1] > 0.12)
    e[stars] = 0.5
    sidx = np.nonzero(ssel)[0]
    emis[sidx[on]] = e[on]; emis_on[sidx[on]] = True
    tone[sidx[dark]] = 0.02
    # characters
    for k, body in ((1, dog), (2, per)):
        s = hitid == k
        if not s.any():
            continue
        Pc = P[s]
        n = body_normal(body, Pc)
        d, keys, gi, pi, hh = body.sdf(Pc, parts=True)
        albc = body.AL[pi]
        if k == 1:
            gname = np.array(keys)[gi]
            prt = np.where(gname == 'head', 2, np.where(gname == 'tail', 5, np.where(np.char.startswith(gname.astype(str), 'leg'), 4, 1)))
            # coat: a darker saddle on the back
            topness = n[:, 1]
            albc = np.where((prt == 1) & (topness > 0.5), albc * 0.45, albc)
            part[s] = prt
        else:
            part[s] = 9
        v, _ = shade_surface(Pc, n, albc, t_scene, [] if k == 1 else [dog])
        tone[s] = (0.1 + 2.3 * v) if k == 1 else (0.02 + 1.1 * v * np.where(albc > 0.9, 1.6, 0.7))
    # ---- to cells
    def cells(a):
        return a.reshape(GH, SS, GW, SS).mean((1, 3))
    tone_c = cells(tone)
    em_c = np.stack([cells(emis[:, i]) for i in range(3)], -1)
    em_cov = cells(emis_on.astype(F32))
    depth = np.where(np.isfinite(t_any), t_any, 99).reshape(GH, SS, GW, SS).min((1, 3))
    hid = hitid.reshape(GH, SS, GW, SS)
    dogcov = (hid == 1).mean((1, 3))
    percov = (hid == 2).mean((1, 3))
    prt = part.reshape(GH, SS, GW, SS).max((1, 3))
    dogm = dogcov >= 0.5
    perm = percov >= 0.5
    led = (em_cov >= 0.5) & ~dogm & ~perm
    on_disc = (np.clip(tone_c, 0, 1.2) ** 0.85 > THR) & ~led
    # outline: a ring of black discs (and dimmed LEDs) around the dog and the person; depth breaks inside the dog
    for m in (dogm, perm):
        ring = ndimage.binary_dilation(m) & ~m & (~dogm if m is perm else True)   # the dog's ring also cuts into the person behind it
        on_disc &= ~ring
        em_c[ring & led] *= 0.18
    dz = np.zeros_like(dogm)
    dd = depth
    for axis in (0, 1):
        a = np.diff(dd, axis=axis)
        both = np.logical_and(np.take(dogm, range(dogm.shape[axis] - 1), axis), np.take(dogm, range(1, dogm.shape[axis]), axis))
        far_next = (a > 0.09) & both
        far_prev = (a < -0.09) & both
        if axis == 0:
            dz[1:][far_next] = True; dz[:-1][far_prev] = True
        else:
            dz[:, 1:][far_next] = True; dz[:, :-1][far_prev] = True
    on_disc &= ~dz
    # the line where the head meets the rest of the dog (kept on the body's side), so the head reads as a head
    headm = dogm & (prt == 2)
    hb = ndimage.binary_dilation(headm) & dogm & ~headm
    on_disc &= ~hb
    # eyes: one black disc each, where the eye is not hidden
    for e in joints['eyes']:
        ex, ey, ez = project(np.asarray(e, F32)[None])
        cxk, cyk = int(ex[0] // SS), int(ey[0] // SS)
        if 0 <= cxk < GW and 0 <= cyk < GH and dogm[cyk, cxk]:
            if np.linalg.norm(np.asarray(e) - CAM) < depth[cyk, cxk] + 0.03:
                on_disc[cyk, cxk] = False
    # nose and eye: the nose prim is dark by albedo already
    state = np.where(led, 2, np.where(on_disc, 1, 0)).astype(np.int8)
    flips = 0 if prev_on is None else int(((state == 1) != (prev_on == 1)).sum())
    flipm = np.zeros_like(dogm) if prev_on is None else ((state == 1) != (prev_on == 1)) & (state != 2)
    meas = measure(dogm, prt, depth, joints)
    return state, em_c, flipm, flips, meas


ON_C = np.array([236, 205, 112], F32) / 255
OFF_C = np.array([30, 30, 33], F32) / 255
BG_C = np.array([7, 7, 9], F32) / 255


def disc_tile(rx, ry):
    n = 16
    yy, xx = np.mgrid[0:PITCH * n, 0:PITCH * n]
    c = PITCH * n / 2 - 0.5
    m = (((xx - c) / (rx * n)) ** 2 + ((yy - c) / (ry * n)) ** 2) <= 1
    return m.reshape(PITCH, n, PITCH, n).mean((1, 3)).astype(F32)


T_FULL = disc_tile(1.78, 1.78)
T_FLIP = disc_tile(1.45, 1.78)       # caught mid-flip: a little narrower for one frame
T_LED = disc_tile(1.9, 1.9)


def compose(state, em_c, flipm):
    col = np.where((state == 1)[..., None], ON_C, OFF_C)
    col = np.where((state == 2)[..., None], np.clip(em_c * 1.25, 0, 1.4), col)
    big = np.repeat(np.repeat(col, PITCH, 0), PITCH, 1)
    mask = np.where(flipm, 1, 0)
    tf = np.tile(T_FULL, (GH, GW)); tl = np.tile(T_FLIP, (GH, GW)); tled = np.tile(T_LED, (GH, GW))
    mbig = np.repeat(np.repeat(mask, PITCH, 0), PITCH, 1)
    sbig = np.repeat(np.repeat(state, PITCH, 0), PITCH, 1)
    m = np.where(mbig == 1, tl, np.where(sbig == 2, tled, tf))
    img = BG_C[None, None] * (1 - m[..., None]) + big * m[..., None]
    # LED bloom
    ledc = np.where((state == 2)[..., None], em_c, 0)
    bl = np.stack([ndimage.gaussian_filter(ledc[..., i], 2.2) for i in range(3)], -1)
    bl = np.repeat(np.repeat(bl, PITCH, 0), PITCH, 1)
    img = img + bl * 0.35
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def measure(dogm, prt, depth, joints):
    ys, xs = np.nonzero(dogm)
    if len(xs) == 0:
        return {'n': 0}
    out = {'n': int(len(xs)), 'cx': float(xs.mean() * PITCH + PITCH / 2), 'cy': float(ys.mean() * PITCH + PITCH / 2),
           'top': float(ys.min() * PITCH), 'bottom': float((ys.max() + 1) * PITCH), 'left': float(xs.min() * PITCH), 'right': float((xs.max() + 1) * PITCH)}
    for nm, code in (('head', 2), ('body', 1), ('tail', 5), ('legs', 4)):
        s = dogm & (prt == code)
        yy, xx = np.nonzero(s)
        out[nm] = None if len(xx) == 0 else [float(xx.mean() * PITCH + 2), float(yy.mean() * PITCH + 2), int(len(xx))]
    # where the joints fall on screen (for verifying, not for drawing)
    for nm in ('nose', 'head', 'tail', 'rump', 'chest'):
        cx, cy, _ = project(np.asarray(joints[nm], F32)[None])
        out['j_' + nm] = [round(float(cx[0]) / SS * PITCH, 1), round(float(cy[0]) / SS * PITCH, 1)]
    return out


def gait_tracks(frames):
    """signed walking phase from the body's own travel (forward is the way the head points), and gait weight"""
    ph, g, out = 0.0, 0.0, []
    prev = None
    for f in frames:
        b = f['body']
        if prev is not None:
            dx = f['x'] - prev['x']
            fwd = -dx * math.cos(b['psi'])      # heading (-cos psi, ., sin psi) dotted with travel (+x)
            dpsi = abs(b['psi'] - prev['body']['psi'])
            ph += (fwd + dpsi * 0.2) / 0.62
            mv = min(1.0, abs(dx) * 24 / 0.1 + dpsi * 24 / 0.6)
            g += (mv - g) * (0.25 if mv > g else 0.06)
        out.append((ph, g))
        prev = f
    return out


def backproject_x(px, py):
    """a screen point (film pixels) -> the world X where its ray meets the dog's path plane z = 0 -> score metres"""
    u = (px / (GW * PITCH)) * 2 - 1
    v = 1 - (py / (GH * PITCH)) * 2
    d = fw + u * TANH * rt + v * TANV * up
    s = -CAM[2] / d[2]
    return float(CAM[0] + d[0] * s) - DOGX


def main():
    a, b = int(sys.argv[1]), int(sys.argv[2])
    M = json.load(open(os.path.join(CACHE, 'machine.json')))
    frames = M['frames']
    G = gait_tracks(frames)
    os.makedirs(os.path.join(CACHE, 'frames'), exist_ok=True)
    cut_i = round(CUT_T * 24)
    prev = None
    if a > 0:
        f = frames[a - 1]
        set_camera(camera_for(a - 1))
        prev = render_frame(f, f['t'], None, *G[a - 1])[0]
    with open(os.path.join(CACHE, f'measure_{a:04d}.jsonl'), 'w') as fo:
        for i in range(a, b):
            f = frames[i]
            cam = camera_for(i)
            set_camera(cam)
            state, em, flipm, flips, meas = render_frame(f, f['t'], prev, *G[i])
            if meas.get('n'):
                meas['x_world_measured'] = round(backproject_x(meas['cx'], meas['bottom'] - 0.25 * (meas['bottom'] - meas['top'])), 4)
            meas['camera'] = cam
            if cut_i <= i < cut_i + CUT_LEN:
                # the cut: the controller rewrites the board column by column; left of the sweep is the new shot
                set_camera('wide')
                s_old, em_old, _, _, _ = render_frame(f, f['t'], None, *G[i])
                set_camera(cam)
                col = (i - cut_i + 1) / CUT_LEN * GW
                newside = (np.arange(GW)[None, :] < col)
                state = np.where(newside, state, s_old)
                em = np.where(newside[..., None], em, em_old)
                flipm = ((state == 1) != (prev == 1)) & (state != 2)
                flips = int(flipm.sum())
                meas['sweep_col'] = int(col)
            prev = state
            img = compose(state, em, flipm)
            Image.fromarray(img).save(os.path.join(CACHE, 'frames', f's{i:04d}.jpg'), quality=92)
            meas.update({'i': i, 'flips': flips})
            fo.write(json.dumps(meas) + '\n')
            fo.flush()


if __name__ == '__main__':
    main()
