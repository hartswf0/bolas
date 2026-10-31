"""Bounded biharmonic weights on a 2D triangle mesh (after Jacobson, Baran, Popovic, Sorkine 2011), written here from the paper's
definition: for every handle j, minimise  1/2 w_j^T (L M^-1 L) w_j  subject to the handle constraints (w_j = 1 on handle j,
0 on the others; linear along cage edges) and the bounds 0 <= w_j <= 1; then normalise to a partition of unity.

Typed inputs:  a shapely Polygon (with holes) in puppet-local metres; handles = list of dicts
   {'name', 'kind': 'point'|'bone'|'cage', 'p': (x,y)} | {'a': (x,y), 'b': (x,y)} | cage verts share a 'cage' loop.
Typed outputs: V (n,2) float64, F (m,3) int, W (n,k) float64 weights, plus diagnostics.
The box-constrained QP is solved with a primal-dual active-set method (exact zeros where the lower bound is active).
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import triangle as tr
from shapely.geometry import Polygon, MultiPolygon, LineString, Point


def _ring_pts(coords, h):
    """Resample a closed ring uniformly by arc length (drops the near-duplicate vertices a polygon union leaves behind)."""
    c = np.asarray(coords, float)
    if np.allclose(c[0], c[-1]):
        c = c[:-1]
    c = np.concatenate([c, c[:1]])
    seg = np.linalg.norm(np.diff(c, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(8, int(np.ceil(s[-1] / h)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, c[:, 0]), np.interp(t, s, c[:, 1])], 1)


def _seg_pts(a, b, h):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = max(1, int(np.ceil(np.linalg.norm(b - a) / h)))
    return np.array([a + (b - a) * k / n for k in range(n + 1)])


def triangulate(poly, handles, h=0.008, quality=30):
    """Constrained Delaunay triangulation of the cut-paper shape with bone segments, cage edges and point handles as PSLG
    constraints, so every handle lies exactly on mesh vertices."""
    if isinstance(poly, MultiPolygon):
        poly = max(poly.geoms, key=lambda g: g.area)
    verts, segs, holes = [], [], []

    def add_chain(pts, closed):
        base = len(verts)
        verts.extend(list(pts))
        n = len(pts)
        for i in range(n - 1):
            segs.append([base + i, base + i + 1])
        if closed:
            segs.append([base + n - 1, base])

    add_chain(_ring_pts(poly.exterior.coords, h), True)
    for ring in poly.interiors:
        add_chain(_ring_pts(ring.coords, h * 0.7), True)
        holes.append(Polygon(ring).representative_point().coords[0])
    cage = [hd for hd in handles if hd['kind'] == 'cage']
    for hd in handles:
        if hd['kind'] == 'bone':
            add_chain(_seg_pts(hd['a'], hd['b'], h * 0.8), False)
        elif hd['kind'] == 'point':
            verts.append(np.asarray(hd['p'], float))
    if cage:
        loop = [np.asarray(c['p'], float) for c in cage]
        pts = []
        for i in range(len(loop)):
            p = _seg_pts(loop[i], loop[(i + 1) % len(loop)], h * 0.8)[:-1]
            pts.extend(p)
        add_chain(np.array(pts), True)
    A = {'vertices': np.array(verts), 'segments': np.array(segs)}
    if holes:
        A['holes'] = np.array(holes)
    area = h * h * 0.6
    B = tr.triangulate(A, 'pq%da%.8f' % (quality, area))
    return B['vertices'], B['triangles']


def cotan_laplacian(V, F):
    n = len(V)
    I, J, X = [], [], []
    area = np.zeros(n)
    for k in range(3):
        i, j, o = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        u, v = V[i] - V[o], V[j] - V[o]
        cross = np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0])
        cot = (u * v).sum(1) / np.maximum(cross, 1e-14)
        I += [i, j, i, j]; J += [j, i, i, j]; X += [-.5 * cot, -.5 * cot, .5 * cot, .5 * cot]
    I, J, X = np.concatenate(I), np.concatenate(J), np.concatenate(X)
    L = sp.csr_matrix((X, (I, J)), shape=(n, n))
    a = V[F[:, 1]] - V[F[:, 0]]; b = V[F[:, 2]] - V[F[:, 0]]
    tri_area = .5 * np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
    for k in range(3):
        np.add.at(area, F[:, k], tri_area / 3)
    return L, area


def _dist_seg(P, a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-18), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * d), axis=1), t


def constraints(V, handles, tol=1e-7):
    """Boundary conditions: rows of fixed weights for the vertices that lie on a handle."""
    k = len(handles)
    fixed = {}
    cage_idx = [j for j, hd in enumerate(handles) if hd['kind'] == 'cage']
    for j, hd in enumerate(handles):
        if hd['kind'] == 'bone':
            d, _ = _dist_seg(V, hd['a'], hd['b'])
            for i in np.where(d < tol)[0]:
                row = np.zeros(k); row[j] = 1; fixed[i] = row
        elif hd['kind'] == 'point':
            i = int(np.argmin(np.linalg.norm(V - np.asarray(hd['p']), axis=1)))
            row = np.zeros(k); row[j] = 1; fixed[i] = row
    for e in range(len(cage_idx)):
        ja, jb = cage_idx[e], cage_idx[(e + 1) % len(cage_idx)]
        d, t = _dist_seg(V, handles[ja]['p'], handles[jb]['p'])
        for i in np.where(d < tol)[0]:
            row = np.zeros(k); row[ja] = 1 - t[i]; row[jb] = t[i]; fixed[i] = row
    idx = np.array(sorted(fixed))
    return idx, np.array([fixed[i] for i in idx])


def box_qp(Q, r, n, lo=0.0, hi=1.0, iters=80):
    """min 1/2 x^T Q x + r^T x, lo <= x <= hi, by the primal-dual active-set method (Hintermueller, Ito, Kunisch 2002).
    The multiplier on an active bound is the gradient g = Qx + r. Returns x, iterations, converged."""
    c = float(Q.diagonal().mean())
    x = np.zeros(n); g = np.zeros(n)
    Lo = np.zeros(n, bool); Up = np.zeros(n, bool)
    first = True
    seen = set()
    for it in range(iters):
        if not first:
            nLo = g + c * (lo - x) > 0
            nUp = g + c * (hi - x) < 0
            nLo &= ~nUp
            primal = max(float((x - hi).max()), float((lo - x).max()))
            dual_ok = (g[Lo] >= -1e-9 * c).all() and (g[Up] <= 1e-9 * c).all()
            if ((nLo == Lo).all() and (nUp == Up).all()) or (primal < 1e-7 and dual_ok):
                return np.clip(x, lo, hi), it, True
            key = hash(nLo.tobytes()) ^ hash(nUp.tobytes()) * 3
            if key in seen:      # a cycle: make the switching less eager
                c *= 8.0
            seen.add(key)
            Lo, Up = nLo, nUp
        first = False
        I = ~(Lo | Up)
        x = np.zeros(n); x[Lo] = lo; x[Up] = hi
        if I.any():
            QII = Q[I][:, I].tocsc()
            rhs = -(r[I] + Q[I][:, ~I] @ x[~I])
            x[I] = spla.spsolve(QII, rhs)
        g = Q @ x + r
        g[I] = 0
    return np.clip(x, lo, hi), iters, False


def solve_bbw(V, F, handles):
    L, area = cotan_laplacian(V, F)
    Minv = sp.diags(1.0 / area)
    Q = (L @ Minv @ L).tocsr()
    idx, vals = constraints(V, handles)
    n, k = len(V), len(handles)
    free = np.setdiff1d(np.arange(n), idx)
    Qff = Q[free][:, free].tocsr(); Qfc = Q[free][:, idx]
    W = np.zeros((n, k)); W[idx] = vals
    info = []
    for j in range(k):
        r = Qfc @ vals[:, j]
        x, its, ok = box_qp(Qff, r, len(free))
        W[free, j] = x
        info.append({'handle': handles[j]['name'], 'active_set_iterations': its, 'converged': bool(ok)})
    raw_sum = W.sum(1)
    W = W / raw_sum[:, None]
    return W, {'n_vertices': n, 'n_triangles': int(len(F)), 'n_constrained': int(len(idx)), 'solve': info,
               'raw_sum_min': float(raw_sum.min()), 'raw_sum_max': float(raw_sum.max())}


def naive_weights(V, handles, power=2):
    """Inverse-distance (Shepard) weights by straight-line distance: the 'naive' weights that ignore the shape."""
    D = []
    for hd in handles:
        if hd['kind'] == 'bone':
            d, _ = _dist_seg(V, hd['a'], hd['b'])
        else:
            d = np.linalg.norm(V - np.asarray(hd['p']), axis=1)
        D.append(d)
    D = np.maximum(np.array(D).T, 1e-6)
    W = 1.0 / D ** power
    return W / W.sum(1, keepdims=True)


def skin(V, W, A):
    """Linear blend skinning: A (k,2,3) affine per handle. Returns (n,2)."""
    Vh = np.concatenate([V, np.ones((len(V), 1))], 1)
    per = np.einsum('kij,nj->nki', A, Vh)  # n,k,2
    return np.einsum('nk,nki->ni', W, per)


def signed_areas(V, F):
    a = V[F[:, 1]] - V[F[:, 0]]; b = V[F[:, 2]] - V[F[:, 0]]
    return .5 * (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
