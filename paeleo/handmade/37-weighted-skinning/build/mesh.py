"""SCION 37 mesh: one continuous skin per character.
A signed-distance sculpture (smooth union of round cones and ellipsoids laid on the rest skeleton) is polygonised by
surface nets into ONE closed, connected triangle mesh; then per-vertex bone weights are computed by heat diffusion
(Baran & Popovic 2007, 'Pinocchio'): solve (L + M H) w_j = M H p_j on the cotangent Laplacian, H = 1/d^2 to the nearest bone.
Writes ../assets/mesh/<name>.npz (V rest, F, UV, idx/w top-4 normalised weights, full weights) and a weight report."""
import json, os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy import ndimage
import rig

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets', 'mesh'); os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- SDF primitives

def rcone(P, a, b, ra, rb):
    """round cone (capsule with varying radius) from a (radius ra) to b (radius rb)"""
    a, b = np.asarray(a, float), np.asarray(b, float); ba = b - a; L2 = ba @ ba
    t = np.clip(((P - a) @ ba) / L2, 0, 1)
    d = np.linalg.norm(P - (a + t[..., None] * ba), axis=-1)
    return d - (ra + (rb - ra) * t)

def ellip(P, c, r):
    q = (P - np.asarray(c)) / np.asarray(r); k = np.linalg.norm(q, axis=-1)
    return (k - 1) * min(r)

def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

# ---------------------------------------------------------------- surface nets

def surface_nets(f, lo, hi, h):
    xs = [np.arange(lo[i], hi[i] + h / 2, h) for i in range(3)]
    G = np.stack(np.meshgrid(*xs, indexing='ij'), -1)
    S = f(G.reshape(-1, 3)).reshape(G.shape[:3])
    S[S == 0] = 1e-9
    n = S.shape; cs = (n[0] - 1, n[1] - 1, n[2] - 1)
    acc = np.zeros(cs + (3,)); cnt = np.zeros(cs)
    quads = []
    for ax in range(3):
        sl0 = [slice(None)] * 3; sl1 = [slice(None)] * 3; sl0[ax] = slice(0, -1); sl1[ax] = slice(1, None)
        s0, s1 = S[tuple(sl0)], S[tuple(sl1)]
        m = (s0 < 0) != (s1 < 0)
        e = np.argwhere(m)
        t = s0[m] / (s0[m] - s1[m])
        p = G[tuple(sl0)][m]; p = p.copy(); p[:, ax] += t * h
        o = [a for a in range(3) if a != ax]
        for d1 in (0, 1):
            for d2 in (0, 1):
                c = e.copy(); c[:, o[0]] -= d1; c[:, o[1]] -= d2
                ok = (c >= 0).all(1) & (c[:, 0] < cs[0]) & (c[:, 1] < cs[1]) & (c[:, 2] < cs[2])
                np.add.at(acc, tuple(c[ok].T), p[ok]); np.add.at(cnt, tuple(c[ok].T), 1)
        inner = (e[:, o[0]] >= 1) & (e[:, o[1]] >= 1) & (e[:, o[0]] < cs[o[0]]) & (e[:, o[1]] < cs[o[1]])
        e2 = e[inner]; flip = (s0[m][inner] < 0)
        cells = []
        for d1, d2 in ((1, 1), (0, 1), (0, 0), (1, 0)):
            c = e2.copy(); c[:, o[0]] -= d1; c[:, o[1]] -= d2; cells.append(c)
        q = np.stack(cells, 1)
        q[flip] = q[flip][:, ::-1]
        quads.append(q)
    has = cnt > 0
    vid = -np.ones(cs, int); vid[has] = np.arange(has.sum())
    V = acc[has] / cnt[has][:, None]
    Q = np.concatenate([vid[tuple(q.reshape(-1, 3).T)].reshape(-1, 4) for q in quads])
    # split quads along the shorter diagonal
    d02 = np.linalg.norm(V[Q[:, 0]] - V[Q[:, 2]], axis=1); d13 = np.linalg.norm(V[Q[:, 1]] - V[Q[:, 3]], axis=1)
    a = d02 <= d13
    F = np.concatenate([Q[a][:, [0, 1, 2]], Q[a][:, [0, 2, 3]], Q[~a][:, [0, 1, 3]], Q[~a][:, [1, 2, 3]]])
    # orient outward against the SDF gradient
    c = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    eps = h * .3; gr = np.stack([f(c + eps * np.eye(3)[i]) - f(c - eps * np.eye(3)[i]) for i in range(3)], 1)
    bad = (nrm * gr).sum(1) < 0; F[bad] = F[bad][:, ::-1]
    return V, F

def keep_largest(V, F):
    n = len(V); A = sp.coo_matrix((np.ones(len(F) * 3), (np.repeat(F[:, 0], 3), F.reshape(-1))), shape=(n, n))
    A = (A + A.T).tocsr(); k, lab = sp.csgraph.connected_components(A, directed=False)
    big = np.bincount(lab).argmax(); keepv = lab == big
    remap = -np.ones(n, int); remap[keepv] = np.arange(keepv.sum())
    Fk = F[keepv[F[:, 0]]]
    return V[keepv], remap[Fk], k

def adjacency(V, F):
    n = len(V); I = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    Jx = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    A = sp.coo_matrix((np.ones(len(I)), (I, Jx)), shape=(n, n)).tocsr(); A.data[:] = 1
    return A

def taubin(V, F, it=6, lam=.5, mu=-.53, fixed=None):
    A = adjacency(V, F); deg = np.asarray(A.sum(1)).ravel()
    for _ in range(it):
        for f in (lam, mu):
            d = A @ V / deg[:, None] - V
            V = V + f * d
    return V

def cotan_laplacian(V, F):
    n = len(V); L = sp.lil_matrix((n, n)); I, Jx, W = [], [], []
    for k in range(3):
        i, j, o = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        u, v = V[i] - V[o], V[j] - V[o]
        cot = (u * v).sum(1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-12)
        cot = np.clip(cot, -5, 50)          # surface-nets triangles can be thin; keep the operator well conditioned
        I += [i, j]; Jx += [j, i]; W += [.5 * cot, .5 * cot]
    I, Jx, W = np.concatenate(I), np.concatenate(Jx), np.concatenate(W)
    Wm = sp.coo_matrix((W, (I, Jx)), shape=(n, n)).tocsr()
    L = sp.diags(np.asarray(Wm.sum(1)).ravel()) - Wm
    area = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
    M = np.bincount(F.reshape(-1), np.repeat(area / 3, 3), n)
    return L.tocsr(), M

def seg_dist(P, a, b):
    ba = b - a; t = np.clip(((P - a) @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ba), axis=1)

HEAT_C = 12.


def heat_weights(V, F, sk, allowed=None):
    """Pinocchio bone heat. allowed(name, V) -> bool mask of vertices that may take that bone as nearest
    (stands in for Pinocchio's visibility test: a left-leg bone is never 'nearest' to the right flank)."""
    L, M = cotan_laplacian(V, F)
    names = sk.deform; Jn = len(names)
    D = np.stack([seg_dist(V, *sk.segs[n]) for n in names], 1)
    if allowed is not None:
        for j, n in enumerate(names):
            D[~allowed(n, V), j] = np.inf
    dmin = D.min(1)
    near = D <= dmin[:, None] * 1.0001 + 1e-9
    H = HEAT_C / np.maximum(dmin, 1e-3) ** 2          # HEAT_C > 1 keeps the heat local enough for a 2 cm mesh
    A = (L + sp.diags(M * H)).tocsc()
    lu = spl.splu(A)
    W = np.zeros((len(V), Jn))
    for j in range(Jn):
        rhs = M * H * near[:, j] / near.sum(1)
        W[:, j] = lu.solve(rhs)
    W = np.clip(W, 0, None); W /= W.sum(1, keepdims=True)
    return W, D

def top_k(W, K=4, floor=.02):
    idx = np.argsort(-W, 1)[:, :K]; w = np.take_along_axis(W, idx, 1)
    w[w < floor] = 0; w /= w.sum(1, keepdims=True)
    return idx, w

# ---------------------------------------------------------------- the dog sculpture

def dog_sdf(P):
    x = P
    core = ellip(x, (.15, .475, 0), (.21, .172, .128))
    core = smin(core, ellip(x, (-.04, .50, 0), (.19, .125, .108)), .06)
    core = smin(core, ellip(x, (-.235, .50, 0), (.14, .125, .112)), .05)
    core = smin(core, ellip(x, (.24, .57, 0), (.09, .07, .08)), .05)                 # withers
    core = smin(core, rcone(x, (.26, .55, 0), (.425, .745, 0), .115, .075), .06)     # neck
    head = ellip(x, (.465, .795, 0), (.094, .082, .074))
    head = smin(head, rcone(x, (.52, .775, 0), (.69, .735, 0), .058, .032), .035)    # muzzle
    head = smin(head, ellip(x, (.51, .745, 0), (.07, .045, .056)), .03)                 # jaw
    for z in (.042, -.042):
        ear = rcone(x, (.452, .85, z), (.43, .965, z * 1.5), .040, .009)
        ear = np.maximum(ear, np.abs(x[..., 0] - (.445 - (x[..., 1] - .85) * .15)) - .015)   # flattened blade
        head = smin(head, ear, .012)
    core = smin(core, head, .035)
    tail = rcone(x, (-.33, .56, 0), (-.50, .52, 0), .052, .048)
    tail = smin(tail, rcone(x, (-.50, .52, 0), (-.63, .46, 0), .048, .040), .02)
    tail = smin(tail, rcone(x, (-.63, .46, 0), (-.775, .39, 0), .040, .020), .02)
    core = smin(core, tail, .03)
    sides = []
    for s in (1, -1):
        z = .09 * s; zh = .0855 * s
        fl = rcone(x, (.235, .48, z), (.20, .30, z), .080, .053)
        fl = smin(fl, rcone(x, (.20, .30, z), (.23, .10, z), .050, .037), .02)
        fl = smin(fl, rcone(x, (.23, .10, z), (.255, .045, z), .037, .034), .015)
        fl = smin(fl, ellip(x, (.275, .034, z), (.058, .034, .042)), .015)
        hl = rcone(x, (-.25, .47, zh), (-.17, .30, zh), .105, .064)
        hl = smin(hl, rcone(x, (-.17, .30, zh), (-.32, .125, zh), .062, .040), .03)
        hl = smin(hl, rcone(x, (-.32, .125, zh), (-.30, .045, zh), .039, .035), .015)
        hl = smin(hl, ellip(x, (-.285, .034, zh), (.056, .034, .041)), .015)
        sides.append(smin(smin(core, fl, .035), hl, .045))
    return np.minimum(*sides)


def dog_allowed(name, V):
    z = V[:, 2]; x = V[:, 0]; y = V[:, 1]
    # stand-in for Pinocchio's visibility test: the flank and the back belong to the trunk, not to the limb bones
    if name[:-1] == 'shoulder' and not (y < .45).all():
        return (y < .45 + .25 * np.clip(x - .22, 0, 1)) & (np.abs(z) > .03) & ((z > 0) if name[-1] == 'L' else (z < 0))
    if name[:-1] == 'hip':
        return (y < .45 - .3 * np.clip(x + .12, 0, 1)) & (np.abs(z) > .03) & ((z > 0) if name[-1] == 'L' else (z < 0))
    if name.endswith('L') and name[:-1] in ('shoulder', 'elbow', 'wrist', 'fpaw', 'hip', 'stifle', 'hock', 'hpaw', 'ear'):
        return z > 0.0
    if name.endswith('R') and name[:-1] in ('shoulder', 'elbow', 'wrist', 'fpaw', 'hip', 'stifle', 'hock', 'hpaw', 'ear'):
        return z < 0.0
    if name in ('tail1', 'tail2', 'tail3'):
        return x < -.30
    return np.ones(len(V), bool)

# ---------------------------------------------------------------- the person sculpture (no face: a faceted head)

def person_sdf(P):
    x = P
    torso = rcone(x, (0, 1.00, 0), (0, 1.36, 0), .145, .160)
    torso = np.maximum(torso, np.abs(x[..., 0]) - .115)                                 # flattened front/back
    torso = smin(torso, rcone(x, (0, .95, -.10), (0, .95, .10), .10, .10), .05)        # hips
    torso = smin(torso, rcone(x, (0, .90, 0), (0, 1.02, 0), .15, .155), .04)           # coat hem
    body = smin(torso, rcone(x, (0, 1.40, -.15), (0, 1.40, .15), .075, .075), .05)     # shoulder yoke
    body = smin(body, rcone(x, (0, 1.46, 0), (.005, 1.60, 0), .055, .05), .03)         # neck
    body = smin(body, ellip(x, (.015, 1.70, 0), (.095, .115, .085)), .03)              # head
    sides = []
    for z in (1, -1):
        # the sleeve meets the body only at the shoulder (a hard union below it), so a raised arm does not drag a web
        arm = rcone(x, (0, 1.40, .21 * z), (0, 1.13, .275 * z), .060, .052)
        arm = smin(arm, rcone(x, (0, 1.13, .275 * z), (0, .88, .305 * z), .052, .045), .02)
        arm = smin(arm, rcone(x, (0, .87, .305 * z), (.01, .74, .315 * z), .036, .03), .015)  # hand
        cap = rcone(x, (0, 1.40, .12 * z), (0, 1.40, .21 * z), .075, .062)
        arm = smin(arm, cap, .03)
        leg = rcone(x, (0, .92, .10 * z), (.01, .50, .10 * z), .085, .060)
        leg = smin(leg, rcone(x, (.01, .50, .10 * z), (0, .09, .10 * z), .060, .045), .02)
        leg = smin(leg, rcone(x, (0, .05, .10 * z), (.17, .04, .10 * z), .045, .038), .02)  # shoe
        upper = np.where(x[..., 1] > 1.30, smin(body, arm, .04), np.minimum(body, arm))
        sides.append(smin(upper, leg, .04))
    return np.minimum(*sides)


def person_allowed(name, V):
    z = V[:, 2]
    if name[:-1] in ('sh', 'el', 'wr', 'hand'): return (z > .215) if name[-1] == 'L' else (z < -.215)
    if name.endswith('L') and name != 'hips': return z > 0
    if name.endswith('R'): return z < 0
    if name in ('hips', 'spine', 'chestp'): return np.abs(z) < .215
    return np.ones(len(V), bool)


def build(name, sdf, lo, hi, h, sk, allowed):
    V, F = surface_nets(sdf, lo, hi, h)
    V, F, ncomp = keep_largest(V, F)
    V = taubin(V, F, it=4)
    W, D = heat_weights(V, F, sk, allowed)
    idx, w = top_k(W)
    # side-projection UV in the rest pose (u along the body, v up)
    UV = np.stack([(V[:, 0] - lo[0]) / (hi[0] - lo[0]), (V[:, 1] - lo[1]) / (hi[1] - lo[1])], 1)
    # euler characteristic: closed single surface of genus 0 has V - E + F = 2
    E = np.unique(np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    edge_use = np.unique(np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0, return_counts=True)[1]
    rep = {'name': name, 'vertices': int(len(V)), 'triangles': int(len(F)), 'components_before_keep': int(ncomp),
           'euler_characteristic': int(len(V) - len(E) + len(F)), 'boundary_edges': int((edge_use == 1).sum()),
           'nonmanifold_edges': int((edge_use > 2).sum()), 'voxel_m': h, 'bones': sk.deform,
           'weights_sum_max_dev': float(np.abs(w.sum(1) - 1).max()), 'max_influences': 4,
           'mean_influences': float((w > 0).sum(1).mean())}
    np.savez_compressed(os.path.join(OUT, name + '.npz'), V=V, F=F, UV=UV, idx=idx, w=w, W=W.astype(np.float32),
                        bones=np.array(sk.deform), lo=np.array(lo), hi=np.array(hi))
    json.dump(rep, open(os.path.join(OUT, name + '.json'), 'w'), indent=1)
    print(json.dumps(rep))
    return rep


if __name__ == '__main__':
    which = sys.argv[1:] or ['dog', 'person']
    if 'dog' in which:
        build('dog', dog_sdf, (-.86, -.02, -.22), (.76, 1.02, .22), .0175, rig.dog_skeleton(), dog_allowed)
    if 'person' in which:
        build('person', person_sdf, (-.25, -.02, -.36), (.30, 1.86, .36), .025, rig.person_skeleton(), person_allowed)
