"""SCION-36 · BBW auto-rig of an irregular archive silhouette.

One archive frame (its SAM polygon, its own ragged edge, blur and grain) ->
  1. Geometry preprocessor: raster mask -> auto triangulation (grid sampled inside the mask, triangles kept only
     where their centroid is inside the mask, so the mesh never bridges the gaps between legs)
  2. Handle layout agent: medial axis (skimage.morphology.medial_axis) -> pruned skeleton graph -> endpoints
     -> feet (lowest endpoints), head and tail (the two remaining extreme endpoints, ordered by the view's facing
     bit), spine path head->tail, leg paths foot->spine.  Mixed handles: POINT handles (nose, tail tip),
     BONE handles (neck, back, tail, 4 legs x upper/lower), and one CAGE handle (the outer hull of the
     withers/back region kept as a polygon of vertices that move together).
  3. Weight optimizer: bounded biharmonic weights, min 1/2 w^T (L M^-1 L) w, w=1 on its handle, 0 on the others,
     0 <= w <= 1, solved per handle by a primal active set on the sparse system, then normalised (partition of unity).
Nothing is painted by hand: the only per-view input is the facing bit (+1 head to the right, -1 head to the left).
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy import ndimage as ndi
from skimage.morphology import medial_axis

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
KIT = os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog')
MASKS = None


def load_mask(fi, W=384, H=288):
    global MASKS
    if MASKS is None:
        MASKS = json.load(open(os.path.join(KIT, 'masks.json')))
    polys = MASKS[str(fi)]
    P = max(polys, key=lambda p: abs(_area(p)))
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in P], fill=255)
    m = np.array(im) > 127
    # keep the largest component, fill holes: the found edge stays ragged, the interior is solid
    lab, n = ndi.label(m)
    if n > 1:
        sizes = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    m = ndi.binary_fill_holes(m)
    # slivers under 3 px (a mask tooth along a blurred ear or the frame's edge) cannot carry a weight field; drop them
    o = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(o)
    if n > 1:
        sizes = ndi.sum(o, lab, range(1, n + 1)); o = lab == (1 + int(np.argmax(sizes)))
    return o, P


def _area(p):
    p = np.asarray(p, float); x, y = p[:, 0], p[:, 1]
    return .5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


# ---------------------------------------------------------------- 1. auto triangulation
def triangulate(mask, step=2):
    H, W = mask.shape
    ys, xs = np.mgrid[0:H:step, 0:W:step]
    gh, gw = ys.shape
    inside = mask[ys, xs]
    # a vertex is kept if any of its 4 neighbouring triangles' centroid is in the mask
    idx = -np.ones((gh, gw), int)
    tris = []
    cand = []
    for (a, b, c) in (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0))):
        cy = (ys[:-1, :-1] + step * (a[0] + b[0] + c[0]) / 3.0)
        cx = (xs[:-1, :-1] + step * (a[1] + b[1] + c[1]) / 3.0)
        ok = mask[np.clip(np.round(cy).astype(int), 0, H - 1), np.clip(np.round(cx).astype(int), 0, W - 1)]
        cand.append((a, b, c, ok))
    used = np.zeros((gh, gw), bool)
    for a, b, c, ok in cand:
        for d in (a, b, c):
            used[d[0]:gh - 1 + d[0], d[1]:gw - 1 + d[1]] |= ok
    idx[used] = np.arange(used.sum())
    V = np.stack([xs[used], ys[used]], 1).astype(float)
    for a, b, c, ok in cand:
        r, q = np.nonzero(ok)
        T = np.stack([idx[r + a[0], q + a[1]], idx[r + b[0], q + b[1]], idx[r + c[0], q + c[1]]], 1)
        tris.append(T)
    T = np.concatenate(tris, 0)
    # keep the largest connected component of the mesh
    n = len(V)
    A = sp.coo_matrix((np.ones(len(T) * 3), (T.ravel(), np.roll(T, 1, 1).ravel())), shape=(n, n))
    nc, lab = sp.csgraph.connected_components(A, directed=False)
    if nc > 1:
        big = np.argmax(np.bincount(lab))
        keep = lab == big
        remap = -np.ones(n, int); remap[keep] = np.arange(keep.sum())
        T = remap[T]; T = T[(T >= 0).all(1)]; V = V[keep]
    return V, T


def cotan_laplacian(V, T):
    n = len(V)
    L = sp.lil_matrix((n, n))
    I, J, X = [], [], []
    area = np.zeros(n)
    for k in range(3):
        i, j, l = T[:, k], T[:, (k + 1) % 3], T[:, (k + 2) % 3]
        u = V[i] - V[l]; v = V[j] - V[l]
        cross = np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]) + 1e-12
        cot = (u * v).sum(1) / cross
        I += [i, j]; J += [j, i]; X += [.5 * cot, .5 * cot]
    I = np.concatenate(I); J = np.concatenate(J); X = np.concatenate(X)
    Lo = sp.coo_matrix((X, (I, J)), shape=(n, n)).tocsr()
    L = Lo - sp.diags(np.asarray(Lo.sum(1)).ravel())
    e1 = V[T[:, 1]] - V[T[:, 0]]; e2 = V[T[:, 2]] - V[T[:, 0]]
    ta = .5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    for k in range(3):
        np.add.at(area, T[:, k], ta / 3)
    return L.tocsr(), area  # L is negative semi-definite (sum of rows 0)


# ---------------------------------------------------------------- 2. handle layout from the medial axis
def skeleton_graph(mask):
    sk, dist = medial_axis(mask, return_distance=True)
    pts = np.argwhere(sk)
    S = {tuple(p) for p in pts}
    def nb(p):
        # 4-neighbours always; a diagonal only when no 4-neighbour already links the two (no corner triangles,
        # so a staircase on the found ragged edge does not read as a branch point)
        out = [(p[0] + dy, p[1] + dx) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)) if (p[0] + dy, p[1] + dx) in S]
        for dy in (-1, 1):
            for dx in (-1, 1):
                q = (p[0] + dy, p[1] + dx)
                if q in S and (p[0] + dy, p[1]) not in S and (p[0], p[1] + dx) not in S: out.append(q)
        return out
    adj = {p: nb(p) for p in S}
    return adj, dist


def prune(adj, dist, minlen):
    """remove spurs shorter than minlen (medial axis noise from the ragged found edge)"""
    adj = {k: list(v) for k, v in adj.items()}
    for _pass in range(2):
        ends = [p for p, v in adj.items() if len(v) == 1]
        for e in ends:
            if e not in adj: continue
            path = [e]; prev = None; cur = e
            while True:
                nxt = [q for q in adj[cur] if q != prev]
                if len(adj[cur]) > 2 or not nxt: break
                prev, cur = cur, nxt[0]; path.append(cur)
                if len(path) > minlen: break
            if len(path) <= minlen and len(adj.get(cur, [])) > 2:
                for p in path[:-1]:
                    for q in adj.get(p, []):
                        if q in adj and p in adj[q]: adj[q].remove(p)
                    adj.pop(p, None)
    # drop isolated
    return {k: v for k, v in adj.items() if v}


def shortest_path(adj, a, b):
    import heapq
    D = {a: 0.0}; prev = {}; h = [(0.0, a)]
    while h:
        d, p = heapq.heappop(h)
        if p == b: break
        if d > D[p]: continue
        for q in adj[p]:
            nd = d + np.hypot(q[0] - p[0], q[1] - p[1])
            if nd < D.get(q, 1e18): D[q] = nd; prev[q] = p; heapq.heappush(h, (nd, q))
    if b not in D: return None
    path = [b]
    while path[-1] != a: path.append(prev[path[-1]])
    return path[::-1]


def largest_component(adj):
    seen = set(); best = []
    for s in adj:
        if s in seen: continue
        comp = []; st = [s]; seen.add(s)
        while st:
            p = st.pop(); comp.append(p)
            for q in adj[p]:
                if q not in seen: seen.add(q); st.append(q)
        if len(comp) > len(best): best = comp
    keep = set(best)
    return {k: [q for q in v if q in keep] for k, v in adj.items() if k in keep}


def _path_len(p):
    p = np.asarray(p, float); return float(np.hypot(*np.diff(p, axis=0).T).sum()) if len(p) > 1 else 0.0


def layout_handles(mask, facing):
    """automatic handles from the shape. facing: +1 head to the right, -1 head to the left.
    Returns named handles in (x, y) source-pixel coordinates."""
    adj, dist = skeleton_graph(mask)
    ys, xs = np.nonzero(mask)
    h = ys.max() - ys.min(); w = xs.max() - xs.min()
    adj = largest_component(prune(adj, dist, max(4, int(.12 * h))))
    ends = [p for p, v in adj.items() if len(v) == 1]
    y0 = ys.min(); cx = xs.mean()
    low = sorted([e for e in ends if e[0] > y0 + .58 * h], key=lambda e: -e[0])
    feet = []
    for e in low:
        if all(np.hypot(e[0] - f[0], e[1] - f[1]) > .07 * h for f in feet): feet.append(e)
        if len(feet) == 4: break
    rest = [e for e in ends if e not in feet]
    # head: the free end furthest toward the facing side (ties broken by height)
    head = max(rest, key=lambda e: facing * (e[1] - cx) / w - .25 * (e[0] - y0) / h) if rest else None
    if head is None or facing * (head[1] - cx) < .05 * w:
        # no free head end: take the skeleton point furthest toward the facing side in the upper 70 %
        cand = [p for p in adj if p[0] < y0 + .7 * h]
        head = max(cand, key=lambda e: facing * e[1] - .3 * e[0])
    # tail: free end furthest to the other side, above the feet; else the skeleton extreme on that side
    tails = [e for e in rest if e != head and e[0] < y0 + .75 * h and -facing * (e[1] - cx) > .15 * w]
    if tails:
        tail = max(tails, key=lambda e: -facing * (e[1] - cx))
    else:
        cand = [p for p in adj if p[0] < y0 + .6 * h]
        tail = max(cand, key=lambda e: -facing * e[1] + .2 * e[0])
    spine = shortest_path(adj, head, tail)
    S = set(spine)
    legs = []
    for f in feet:
        p = shortest_path(adj, f, head)
        # leave the leg where it first meets the spine
        k = next((i for i, q in enumerate(p) if q in S), len(p) - 1)
        leg = p[:k + 1]
        if _path_len(leg) < .2 * h or f[0] < y0 + .75 * h: continue
        legs.append(leg)
    # where the legs join the spine: index along the spine (0 = head)
    sidx = {q: i for i, q in enumerate(spine)}
    joins = [sidx[l[-1]] for l in legs]
    n = len(spine)
    if legs:
        jmin, jmax = min(joins), max(joins)
    else:
        jmin, jmax = int(.3 * n), int(.7 * n)
    # front legs join nearer the head than the midpoint of the joins, hind legs further
    mid = (jmin + jmax) / 2 if jmax - jmin > .15 * n else n * .5
    shoulder = jmin if jmin < mid else int(.35 * n)
    hip = jmax if jmax > mid else int(.7 * n)
    shoulder = max(shoulder, int(.18 * n)); hip = min(max(hip, shoulder + 3), n - 3)
    xy = lambda q: (float(q[1]), float(q[0]))
    sp_xy = [xy(q) for q in spine]
    H = dict(facing=facing, height=float(h), width=float(w),
             ground=float(ys.max()), feet=[xy(f) for f in feet])
    H['head'] = {'type': 'point', 'at': sp_xy[0]}
    neck_end = max(1, int(.4 * shoulder))
    H['neck'] = {'type': 'bone', 'a': sp_xy[shoulder], 'b': sp_xy[neck_end], 'path': sp_xy[neck_end:shoulder + 1]}
    H['back'] = {'type': 'bone', 'a': sp_xy[hip], 'b': sp_xy[shoulder], 'path': sp_xy[shoulder:hip + 1]}
    H['tail'] = {'type': 'bone', 'a': sp_xy[hip], 'b': sp_xy[-1], 'path': sp_xy[hip:]}
    H['tailtip'] = {'type': 'point', 'at': sp_xy[-1]}
    for li, (leg, j) in enumerate(sorted(zip(legs, joins), key=lambda t: facing * t[0][0][1], reverse=True)):
        kind = 'front' if abs(j - shoulder) <= abs(j - hip) else 'hind'
        lp = [xy(q) for q in leg][::-1]  # top (joint) -> foot
        m = len(lp) // 2
        H['leg%d' % li] = {'type': 'bone', 'kind': kind, 'a': lp[0], 'k': lp[m], 'b': lp[-1], 'path': lp,
                           'p': lp[int(.3 * len(lp))]}   # pivot: the top of the pinned part (elbow / stifle)
    return H, adj, dist


# ---------------------------------------------------------------- 3. bounded biharmonic weights
def _seg_dist(P, a, b):
    a = np.asarray(a); b = np.asarray(b); d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-9), 0, 1)
    return np.hypot(*(P - (a + t[:, None] * d)).T)


def _poly_dist(P, path):
    path = np.asarray(path, float)
    if len(path) == 1: return np.hypot(*(P - path[0]).T)
    return np.min([_seg_dist(P, path[i], path[i + 1]) for i in range(len(path) - 1)], 0)


def handle_vertices(V, H, r=1.6, joint_gap=3.0):
    """which mesh vertices each handle pins (w = 1): vertices on the bone's medial path, minus a gap at the joints
    so that two bones never claim the same vertex; a point handle pins its nearest vertices."""
    names = [k for k, v in H.items() if isinstance(v, dict) and v.get('type') in ('bone', 'point')]
    sets = {}
    for k in names:
        v = H[k]
        if v['type'] == 'point':
            d = np.hypot(*(V - np.asarray(v['at'])).T)
            sets[k] = np.nonzero(d <= max(r, d.min() + .01))[0]
        else:
            path = v['path']
            if v.get('kind'):
                # a leg pins only its lower 70 %: the shoulder and haunch above it belong to the body, so a folded
                # leg cannot drag a sliver of the back up with it
                path = path[int(.3 * len(path)):]
            d = _poly_dist(V, path)
            da = np.hypot(*(V - np.asarray(path[0])).T); db = np.hypot(*(V - np.asarray(path[-1])).T)
            sel = (d <= r) & (da > joint_gap) & (db > joint_gap)
            sets[k] = np.nonzero(sel)[0]
    # a vertex claimed twice goes to neither
    allv = np.concatenate([s for s in sets.values()]) if sets else np.zeros(0, int)
    u, c = np.unique(allv, return_counts=True); dup = set(u[c > 1])
    sets = {k: np.array([i for i in s if i not in dup], int) for k, s in sets.items()}
    sets = {k: s for k, s in sets.items() if len(s)}
    return sets


def bbw(V, T, sets, iters=40):
    """bounded biharmonic weights by a primal active set per handle; returns W (n x m), handle names, stats"""
    L, area = cotan_laplacian(V, T)
    Minv = sp.diags(1.0 / np.maximum(area, 1e-9))
    Q = (L.T @ Minv @ L).tocsc()
    n = len(V); names = list(sets)
    m = len(names)
    Wr = np.zeros((n, m)); stats = []
    pinned = np.zeros(n, bool)
    for s in sets.values(): pinned[s] = True
    for j, k in enumerate(names):
        fixed_val = np.zeros(n); fixed_val[sets[k]] = 1.0
        lo = np.zeros(n, bool); hi = np.zeros(n, bool)
        it = 0
        while True:
            it += 1
            C = pinned | lo | hi
            val = fixed_val.copy(); val[hi] = 1.0; val[lo & ~pinned] = 0.0
            F = np.nonzero(~C)[0]; Cn = np.nonzero(C)[0]
            w = val.copy()
            if len(F):
                rhs = -(Q[F][:, Cn] @ val[Cn])
                w[F] = spl.spsolve(Q[F][:, F].tocsc(), rhs)
            g = Q @ w
            new_lo = (~C) & (w < -1e-9); new_hi = (~C) & (w > 1 + 1e-9)
            rel_lo = lo & ~pinned & (g < -1e-9); rel_hi = hi & ~pinned & (g > 1e-9)
            if not (new_lo.any() or new_hi.any() or rel_lo.any() or rel_hi.any()) or it >= iters: break
            lo = (lo | new_lo) & ~rel_lo; hi = (hi | new_hi) & ~rel_hi
        Wr[:, j] = np.clip(w, 0, 1)
        stats.append({'handle': k, 'active_set_iters': it, 'n_lower_active': int(lo.sum()), 'n_upper_active': int(hi.sum()),
                      'raw_min': float(w.min()), 'raw_max': float(w.max())})
    s = Wr.sum(1)
    W = Wr / np.maximum(s, 1e-12)[:, None]
    return W, names, {'per_handle': stats, 'sum_before_normalising': [float(s.min()), float(s.max())]}


# ---------------------------------------------------------------- whole-frame rig
def rig_frame(fi, facing, step=2):
    mask, poly = load_mask(fi)
    tri_mask = ndi.binary_dilation(mask, iterations=1)
    V, T = triangulate(tri_mask, step)
    H, adj, dist = layout_handles(mask, facing)
    sets = handle_vertices(V, H)
    W, names, st = bbw(V, T, sets)
    return dict(fi=fi, facing=facing, mask=mask, poly=poly, V=V, T=T, H=H, sets=sets, W=W, names=names, stats=st,
                skeleton=np.array([(q[1], q[0]) for q in adj], float))


def shepard_weights(V, sets, p=2):
    """the counterexample: inverse-distance weights to the same handle vertices (ignore the shape)"""
    D = np.stack([np.min(np.hypot(*(V[:, None, :] - V[s][None, :, :]).transpose(2, 0, 1)), 1) for s in sets.values()], 1)
    Wd = 1.0 / np.maximum(D, 1e-6) ** p
    for j, s in enumerate(sets.values()):
        Wd[s] = 0; Wd[s, j] = 1
    return Wd / Wd.sum(1, keepdims=True)
