"""Mesh tessellator: a conforming Delaunay triangulation of each engraved drawing.

Points: Poisson-disk samples on the outline (spacing rb) and inside (spacing ri, denser in protected features),
triangulated by scipy.spatial.Delaunay, then every triangle whose centroid or any edge midpoint falls outside the drawing
is removed (that is what separates the legs and the ear tips). Triangles carry the drawing part they cover (for layer
order and for rigidity weights). Output: assets/mesh/<name>.npz (V rest mm y-up, T, uv px, part, layer, weight).
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DRAW, MESH


def poisson(cands, r, rng, existing=None):
    """Greedy Poisson-disk thinning on a hash grid."""
    cell = r / np.sqrt(2)
    grid = {}
    out = []
    pts = [] if existing is None else list(existing)
    for p in pts:
        grid.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(p)
    order = rng.permutation(len(cands))
    for k in order:
        p = cands[k]
        gx, gy = int(p[0] // cell), int(p[1] // cell)
        ok = True
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for q in grid.get((gx + dx, gy + dy), ()):
                    if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < r * r:
                        ok = False; break
                if not ok: break
            if not ok: break
        if ok:
            grid.setdefault((gx, gy), []).append(p)
            out.append(p)
    return np.array(out)


def build(name, rb=9.0, ri=17.0, feature_ri=8.0, seed=34, part_weight=None):
    meta = json.load(open(os.path.join(DRAW, name + '.json')))
    rgba = np.array(Image.open(os.path.join(DRAW, name + '.png'))).astype(np.float32) / 255
    label = np.array(Image.open(os.path.join(DRAW, name + '_label.png'))).astype(int) - 1
    mask = rgba[..., 3] > 0.5
    mask = ndimage.binary_opening(mask, iterations=1)
    rng = np.random.default_rng(seed)
    er = ndimage.binary_erosion(mask, iterations=1)
    edge = np.argwhere(mask & ~er)[:, ::-1].astype(float)          # (x, y) image px
    B = poisson(edge, rb, rng)
    inner = ndimage.binary_erosion(mask, iterations=int(rb * 0.6))
    cand = np.argwhere(inner)[:, ::-1].astype(float) + rng.uniform(-0.5, 0.5, (inner.sum(), 2))
    # dense first inside protected features
    feats = meta.get('features', [])
    F = []
    for f in feats:
        cx, cy = f['c'][0] + meta['ox'], meta['oy'] - f['c'][1]
        sel = (cand[:, 0] - cx) ** 2 + (cand[:, 1] - cy) ** 2 < (f['r'] * 1.4) ** 2
        if sel.any():
            F.extend(poisson(cand[sel], feature_ri, rng, existing=list(B) + F))
    I = poisson(cand, ri, rng, existing=list(B) + list(F))
    P = np.vstack([B] + ([np.array(F)] if len(F) else []) + [I])
    tri = Delaunay(P).simplices

    def inside(q):
        x = np.clip(np.round(q[:, 0]).astype(int), 0, mask.shape[1] - 1)
        y = np.clip(np.round(q[:, 1]).astype(int), 0, mask.shape[0] - 1)
        return mask[y, x]
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    keep = inside((a + b + c) / 3) & inside((a + b) / 2) & inside((b + c) / 2) & inside((c + a) / 2)
    # also the quarter points of each edge (thin gaps)
    for s in (0.25, 0.75):
        keep &= inside(a + (b - a) * s) & inside(b + (c - b) * s) & inside(c + (a - c) * s)
    tri = tri[keep]
    # drop slivers on the outline (all three vertices on the boundary and nearly degenerate)
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    area = 0.5 * np.abs((b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0])
    tri = tri[area > 4.0]
    # largest connected component only
    n = len(P)
    import scipy.sparse as sp
    e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    ncomp, lab = sp.csgraph.connected_components(A, directed=False)
    used = np.unique(tri)
    big = np.bincount(lab[used]).argmax()
    tri = tri[lab[tri[:, 0]] == big]
    used = np.unique(tri)
    remap = -np.ones(n, int); remap[used] = np.arange(len(used))
    P = P[used]; tri = remap[tri]
    # rest coordinates in the drawing frame (mm, y up); triangles counter-clockwise in that frame
    V = np.stack([P[:, 0] - meta['ox'], meta['oy'] - P[:, 1]], 1)
    a, b, c = V[tri[:, 0]], V[tri[:, 1]], V[tri[:, 2]]
    sgn = (b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0]
    tri[sgn < 0] = tri[sgn < 0][:, [0, 2, 1]]
    cen = P[tri].mean(1)
    lab_t = label[np.clip(cen[:, 1].astype(int), 0, label.shape[0] - 1), np.clip(cen[:, 0].astype(int), 0, label.shape[1] - 1)]
    # triangles whose centroid sits on a soft edge pixel with no label: take the most common vertex label
    for k in np.where(lab_t < 0)[0]:
        vs = [label[int(P[v, 1]), int(P[v, 0])] for v in tri[k]]
        vs = [v for v in vs if v >= 0]
        lab_t[k] = vs[0] if vs else 0
    layers = np.array([p['layer'] for p in meta['parts']])
    names = [p['name'] for p in meta['parts']]
    weight = np.ones(len(tri))
    if part_weight:
        for k, nm in enumerate(names):
            if nm in part_weight:
                weight[lab_t == k] = part_weight[nm]
    for f in feats:     # protected features: rigid weight 30
        d2 = ((V[tri].mean(1) - np.array(f['c'])) ** 2).sum(1)
        weight[d2 < (f['r'] * 1.25) ** 2] = 30.0
    np.savez(os.path.join(MESH, name + '.npz'), V=V, T=tri, uv=P, part=lab_t, layer=layers[lab_t], weight=weight,
             names=np.array(names))
    print(name, 'verts', len(V), 'tris', len(tri), 'boundary', len(B))
    return V, tri


if __name__ == '__main__':
    names = sys.argv[1:] or ['P_body', 'P_head']
    for nm in names:
        build(nm, **({'rb': 7.0, 'ri': 12.0, 'feature_ri': 6.0} if nm.endswith('head') else {}))
