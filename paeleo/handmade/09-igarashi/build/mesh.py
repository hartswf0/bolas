"""Mesh builder: triangulate each source drawing (assets/drawings/*.png) into an ARAP mesh.
python3 build/mesh.py   ->  assets/mesh/<drawing>.json

Typed output per drawing:
  verts   [[x,y],...]   rest positions in drawing pixels (y down); uv = verts / [w,h]
  tris    [[a,b,c],...] counter-clockwise in screen orientation (signed area > 0 with y down means clockwise on paper;
                        we store them so that area2(tri) > 0 at rest, and the solver counts a flip as area2 <= 0)
  weight  per triangle rigidity weight (1 everywhere, FEATURE_W inside feature-protect masks: eye, nose, tag, buttons)
  handles {name: [vertex indices]}  the control handles (vertices within a small radius of each named handle point)
  features {name: [triangle indices]}
The mesh is a regular grid of cells clipped to the drawing's alpha (a cell is kept if any of its pixels is inked), each cell
split into two triangles along alternating diagonals; the cell size is chosen per drawing kind.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DR = os.path.join(ROOT, 'assets', 'drawings')
OUT = os.path.join(ROOT, 'assets', 'mesh')
os.makedirs(OUT, exist_ok=True)
FEATURE_W = 40.0
CELL = {'dog': 7, 'head': 6, 'person': 9}

meta = json.loads(subprocess.check_output(['node', '-e', '''
const {D}=require(process.argv[1]); const o={};
for (const [k,d] of Object.entries(D)) o[k]={kind:d.kind,behind:d.behind||null,cuts:d.cuts||null,w:d.w,h:d.h,handles:d.handles,features:d.features||[],layers:d.layers||null,socket:d.socket||null,ground:d.ground||null,facing:d.facing};
console.log(JSON.stringify(o));''', os.path.join(HERE, 'drawings.js')]))


def m_cuts(m):
    return m.get('cuts') or []


def build(name, png, m, layer=None):
    im = np.asarray(Image.open(png).convert('RGBA')).astype(np.float32)
    a = im[:, :, 3]
    H, W = a.shape
    c = CELL[m['kind']]
    nx, ny = (W + c - 1) // c, (H + c - 1) // c
    keep = np.zeros((ny, nx), bool)
    for j in range(ny):
        for i in range(nx):
            if a[j * c:(j + 1) * c, i * c:(i + 1) * c].max() > 12:
                keep[j, i] = True
    vid = -np.ones((ny + 1, nx + 1), int)
    verts, tris = [], []

    def v(i, j):
        if vid[j, i] < 0:
            vid[j, i] = len(verts); verts.append([min(i * c, W), min(j * c, H)])
        return vid[j, i]
    for j in range(ny):
        for i in range(nx):
            if not keep[j, i]:
                continue
            a0, a1, a2, a3 = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            if (i + j) % 2 == 0:
                tris += [[a0, a1, a2], [a0, a2, a3]]
            else:
                tris += [[a0, a1, a3], [a1, a2, a3]]
    V = np.array(verts, float); T = np.array(tris, int)
    # orientation: make area2 > 0 for all (y-down screen coordinates)
    e1 = V[T[:, 1]] - V[T[:, 0]]; e2 = V[T[:, 2]] - V[T[:, 0]]
    ar = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    T[ar < 0] = T[ar < 0][:, [0, 2, 1]]
    # explicit cuts: duplicate the vertices along each cut so the triangles either side no longer share them
    for cut in m_cuts(m):
        (ax, ay), (bx, by) = cut
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        def proj(px, py):
            u = ((px - ax) * dx + (py - ay) * dy) / L2
            qx, qy = ax + u * dx, ay + u * dy
            return u, np.hypot(px - qx, py - qy), np.sign(dx * (py - ay) - dy * (px - ax))
        cen0 = V[T].mean(1)
        side = {}
        for ti, (cx_, cy_) in enumerate(cen0):
            u, d, sg = proj(cx_, cy_)
            if -0.05 <= u <= 1.05 and d < 2.0 * c:
                side[ti] = sg
        dup = {}
        Vl = V.tolist()
        for ti, sg in side.items():
            if sg >= 0:
                continue
            for k in range(3):
                vi = T[ti, k]
                u, d, _ = proj(*V[vi])
                if 0.08 < u <= 1.2 and d <= 0.75 * c:
                    if vi not in dup:
                        dup[vi] = len(Vl); Vl.append(list(V[vi]))
                    T[ti, k] = dup[vi]
        V = np.array(Vl, float)
        print(f'   cut {cut}: {len(dup)} vertices split')
    used = np.unique(T.ravel())
    used = used[np.lexsort((V[used, 0], V[used, 1]))]          # row-major order keeps the solver's band narrow
    remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    V = V[used]; T = remap[T]
    groups = None
    # split textures along the first cut: triangles on the far side of the foreleg cut sample a texture with the near side
    # erased, and all others sample one with the far side erased, so a near leg crossing a far leg carries none of the
    # far leg's ink or paper with it (and vice versa). The far group is drawn first, behind.
    if m.get('behind') and m_cuts(m):
        (ax_, ay_), (bx_, by_) = m_cuts(m)[0]
        cutx = lambda y: ax_ + (bx_ - ax_) * (y - ay_) / (by_ - ay_)
        yy, xx = np.mgrid[0:H, 0:W]
        band = (yy > ay_) & (yy < by_ + 8)
        right = band & (xx > cutx(yy))
        left = band & (xx <= cutx(yy))
        rgba = np.asarray(Image.open(png).convert('RGBA')).copy()
        near = rgba.copy(); near[right] = 0; far = rgba.copy(); far[left] = 0
        base = os.path.splitext(os.path.basename(png))[0]
        Image.fromarray(near).save(os.path.join(DR, base + '.near.png')); Image.fromarray(far).save(os.path.join(DR, base + '.far.png'))
        c0 = V[T].mean(1)
        isfar = (c0[:, 1] > ay_) & (c0[:, 1] < by_ + 8) & (c0[:, 0] > np.array([cutx(y) for y in c0[:, 1]]))
        T = np.concatenate([T[isfar], T[~isfar]])
        nf = int(isfar.sum())
        groups = [{'from': 0, 'to': nf, 'texture': f'assets/drawings/{base}.far.png'}, {'from': nf, 'to': len(T), 'texture': f'assets/drawings/{base}.near.png'}]
        print(f'   textures split at the foreleg cut: {nf} far-side triangles drawn first')
    elif m.get('behind'):
        from PIL import ImageDraw
        msk = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(msk)
        for poly in m['behind']:
            dr.polygon([tuple(p) for p in poly], fill=255)
        mk = np.asarray(msk)
        c0 = V[T].mean(1)
        back = mk[np.clip(c0[:, 1].astype(int), 0, H - 1), np.clip(c0[:, 0].astype(int), 0, W - 1)] > 0
        T = np.concatenate([T[back], T[~back]])
        print(f'   behind: {int(back.sum())} triangles drawn first')
    cen = V[T].mean(1)
    w = np.ones(len(T))
    feats = {}
    for f in m['features']:
        if layer == 'arm':
            continue
        d = np.hypot(cen[:, 0] - f['c'][0], cen[:, 1] - f['c'][1])
        idx = np.where(d < f['r'])[0]
        w[idx] = FEATURE_W; feats[f['name']] = idx.tolist()
    # connected components (for diagnostics: legs must not be bridged)
    parent = list(range(len(V)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for t in T:
        for k in (1, 2):
            ra, rb = find(t[0]), find(t[k])
            if ra != rb:
                parent[ra] = rb
    comps = len(set(find(i) for i in range(len(V))))
    hs = {}; hp_c = {}
    names = m['handles'].items()
    if layer == 'arm':
        names = [(k, p) for k, p in names if k in ('shoulder', 'elbow', 'hand')]
    elif layer == 'body':
        names = [(k, p) for k, p in names if k not in ('elbow', 'hand')]
    for k, p in names:
        d = np.hypot(V[:, 0] - p[0], V[:, 1] - p[1])
        r = c * 4.0 if (m['kind'] == 'person' and k == 'head') else max(c * 1.6, 1.0)  # the person's head moves as one piece
        idx = np.where(d <= r)[0]
        if len(idx) == 0:
            idx = [int(d.argmin())]
        hs[k] = [int(i) for i in idx]
        hp_c[k] = V[hs[k]].mean(0).round(3).tolist()   # the handle point IS the centroid of its vertices (targets stay consistent)
    out = {'name': name, 'kind': m['kind'], 'layer': layer, 'w': W, 'h': H, 'cell': c, 'verts': V.round(2).tolist(), 'tris': T.tolist(),
           'weight': w.tolist(), 'handles': hs, 'features': feats, 'components': comps, 'socket': m['socket'], 'ground': m['ground'],
           'facing': m['facing'], 'handle_points': hp_c, 'texture': 'assets/drawings/' + os.path.basename(png), 'groups': groups}
    json.dump(out, open(os.path.join(OUT, name + '.json'), 'w'), separators=(',', ':'))
    print(f'{name:22s} verts {len(V):5d} tris {len(T):5d} cell {c}px components {comps} feature tris {sum(len(x) for x in feats.values())}')


for k, m in meta.items():
    if m['layers']:
        for L in m['layers']:
            build(k + '.' + L, os.path.join(DR, f'{k}.{L}.png'), m, L)
    else:
        build(k, os.path.join(DR, k + '.png'), m)
