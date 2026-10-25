"""SCION 03 Ernst · the burin.  Signed-distance maquettes (dog, person) ray-marched in the plate's camera, then engraved.

The maquette is not a texture: it is a solid built from round cones and ellipsoids (typed primitives with an id, a material
and an engraving frame).  The renderer returns, per pixel: hit mask, depth, normal, primitive id, and the burin coordinate
(u, along-form lines; v, ring lines for cross-hatch) so the engraving lines are attached to the body, not to the screen.
"""
import numpy as np

# ---- the plate's camera: orthographic, looking slightly down (a stage seen from the stalls) -------------------------
PITCH = np.radians(18.0)
SCALE = 168.0          # px per metre
X0 = 400.0             # screen x of world x = 0 (the threshold)
Y0 = 548.0             # screen y of world (y=0, z=ZD)
ZD = 0.62              # depth of the dog's walking line in front of the facade (z toward the viewer)
VIEW = np.array([0.0, -np.sin(PITCH), -np.cos(PITCH)])     # ray direction (into the picture)
UP = np.array([0.0, np.cos(PITCH), -np.sin(PITCH)])         # screen up
RIGHT = np.array([1.0, 0.0, 0.0])


def project(P):
    """world (...,3) -> screen x, y (px) and depth (m, larger = farther)."""
    P = np.asarray(P, float)
    sx = X0 + SCALE * P[..., 0]
    q = P.copy(); q[..., 2] = q[..., 2] - ZD
    sy = Y0 - SCALE * (q @ UP)
    dep = q @ VIEW
    return sx, sy, dep


def unproject(sx, sy, dep):
    x = (sx - X0) / SCALE
    upc = (Y0 - sy) / SCALE
    P = RIGHT[None] * x[..., None] + UP[None] * upc[..., None] + VIEW[None] * dep[..., None]
    P[..., 2] += ZD
    return P


# ---- primitives ------------------------------------------------------------------------------------------------------
class Prim:
    __slots__ = ('kind', 'a', 'b', 'r1', 'r2', 'c', 'R', 'rad', 'k', 'mat', 'name', 'ref')

    def __init__(self, kind, name, mat, k=0.03, **kw):
        self.kind = kind; self.name = name; self.mat = mat; self.k = k
        for key, v in kw.items():
            setattr(self, key, v)


def cone(name, a, b, r1, r2, mat, ref, k=0.03):
    return Prim('cone', name, mat, k, a=np.asarray(a, float), b=np.asarray(b, float), r1=float(r1), r2=float(r2),
                ref=np.asarray(ref, float))


def ellip(name, c, R, rad, mat, k=0.03):
    """R: 3x3 with columns = the ellipsoid's local axes in world (axis 0 = long axis = the engraving's 'along')."""
    return Prim('ell', name, mat, k, c=np.asarray(c, float), R=np.asarray(R, float), rad=np.asarray(rad, float))


def d_cone(p, a, b, r1, r2):
    ba = b - a
    l2 = ba @ ba
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    w = pa * l2 - ba[None] * y[:, None]
    x2 = np.einsum('ij,ij->i', w, w)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    d1 = np.sqrt(x2 + z2) * il2 - r2
    d2 = np.sqrt(x2 + y2) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))


def d_ell(p, c, R, rad):
    q = (p - c) @ R
    k0 = np.linalg.norm(q / rad, axis=1)
    k1 = np.linalg.norm(q / (rad * rad), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def dist_one(pr, p):
    if pr.kind == 'cone':
        return d_cone(p, pr.a, pr.b, pr.r1, pr.r2)
    return d_ell(p, pr.c, pr.R, pr.rad)


def scene_sdf(prims, p, want_id=False):
    d = None; best = None; ids = None
    for i, pr in enumerate(prims):
        di = dist_one(pr, p)
        if d is None:
            d = di; best = di.copy(); ids = np.zeros(len(p), np.int16)
            continue
        k = pr.k
        if k > 0:
            h = np.clip(0.5 + 0.5 * (di - d) / k, 0, 1)
            d = di * (1 - h) + d * h - k * h * (1 - h)
        else:
            d = np.minimum(d, di)
        if want_id:
            m = di < best
            best = np.where(m, di, best)
            ids = np.where(m, i, ids)
    return (d, ids) if want_id else d


def bounds(prims):
    pts = []
    for pr in prims:
        if pr.kind == 'cone':
            r = max(pr.r1, pr.r2)
            for e in (pr.a, pr.b):
                pts.append(e - r); pts.append(e + r)
        else:
            r = pr.rad.max()
            pts.append(pr.c - r); pts.append(pr.c + r)
    pts = np.array(pts)
    return pts.min(0), pts.max(0)


def render(prims, W=1280, H=720, pad=6):
    """Ray-march the maquette in the plate camera.  Returns dict of buffers cropped to a box (x0, y0, x1, y1)."""
    lo, hi = bounds(prims)
    corners = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [lo[0], hi[1], lo[2]], [hi[0], hi[1], lo[2]],
                        [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]], [lo[0], hi[1], hi[2]], [hi[0], hi[1], hi[2]]])
    sx, sy, dep = project(corners)
    x0 = int(max(0, np.floor(sx.min()) - pad)); x1 = int(min(W, np.ceil(sx.max()) + pad))
    y0 = int(max(0, np.floor(sy.min()) - pad)); y1 = int(min(H, np.ceil(sy.max()) + pad))
    if x1 <= x0 or y1 <= y0:
        return None
    gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    n = gx.size
    t = np.full(n, dep.min() - 0.05)
    tmax = dep.max() + 0.05
    sxf = gx.ravel(); syf = gy.ravel()
    # conservative 2D cull: in an orthographic view each primitive lies inside the 2D capsule of its projection
    near = np.zeros(n, bool)
    for pr in prims:
        if pr.kind == 'cone':
            ax_, ay_, _ = project(pr.a); bx_, by_, _ = project(pr.b); r = max(pr.r1, pr.r2)
        else:
            ax_, ay_, _ = project(pr.c); bx_, by_ = ax_, ay_; r = pr.rad.max()
        rr = (r + pr.k * 0.5 + 0.01) * SCALE + 2
        lo_x, hi_x = min(ax_, bx_) - rr, max(ax_, bx_) + rr
        lo_y, hi_y = min(ay_, by_) - rr, max(ay_, by_) + rr
        cand = (sxf > lo_x) & (sxf < hi_x) & (syf > lo_y) & (syf < hi_y)
        idx = np.nonzero(cand & ~near)[0]
        if idx.size == 0:
            continue
        px = sxf[idx] - ax_; py = syf[idx] - ay_
        dx, dy = bx_ - ax_, by_ - ay_
        L2 = dx * dx + dy * dy
        h = np.clip((px * dx + py * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros(idx.size)
        dd = np.hypot(px - dx * h, py - dy * h)
        near[idx[dd < rr]] = True
    act = np.nonzero(near)[0]
    hit = np.zeros(n, bool)
    for it in range(64):
        if act.size == 0:
            break
        P = unproject(sxf[act], syf[act], t[act])
        d = scene_sdf(prims, P)
        t[act] += d * 0.92
        done = d < 0.0012
        hit[act[done]] = True
        gone = t[act] > tmax
        act = act[~done & ~gone]
    hidx = np.nonzero(hit)[0]
    out = {'box': (x0, y0, x1, y1), 'hit': hit.reshape(gx.shape)}
    depth = np.full(n, np.inf); depth[hidx] = t[hidx]
    out['depth'] = depth.reshape(gx.shape)
    if hidx.size == 0:
        return out
    P = unproject(sxf[hidx], syf[hidx], t[hidx])
    e = 0.002
    N = np.zeros_like(P)
    for j in range(3):
        dv = np.zeros(3); dv[j] = e
        N[:, j] = scene_sdf(prims, P + dv) - scene_sdf(prims, P - dv)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    _, ids = scene_sdf(prims, P, want_id=True)
    # burin coordinates per primitive: u = angle around the axis (lines run along the form), v = along the axis (rings)
    U = np.zeros(len(P)); V = np.zeros(len(P)); RADI = np.zeros(len(P))
    for i, pr in enumerate(prims):
        m = ids == i
        if not m.any():
            continue
        p = P[m]
        if pr.kind == 'cone':
            ax = pr.b - pr.a; L = np.linalg.norm(ax); ax = ax / L
            ref = pr.ref - ax * (pr.ref @ ax); ref /= max(np.linalg.norm(ref), 1e-9)
            w = np.cross(ax, ref)
            q = p - pr.a
            along = q @ ax
            rad = 0.5 * (pr.r1 + pr.r2)
            th = np.arctan2(q @ w, q @ ref)
            U[m] = th; V[m] = along; RADI[m] = rad
        else:
            q = (p - pr.c) @ pr.R
            rad = 0.5 * (pr.rad[1] + pr.rad[2])
            th = np.arctan2(q[:, 2] / pr.rad[2], q[:, 1] / pr.rad[1])
            U[m] = th; V[m] = q[:, 0]; RADI[m] = rad
    def full(a, fill=0.0, dt=float):
        o = np.full(n, fill, dt); o[hidx] = a; return o.reshape(gx.shape)
    out['P'] = np.zeros(gx.shape + (3,)); out['P'].reshape(-1, 3)[hidx] = P
    out['N'] = np.zeros(gx.shape + (3,)); out['N'].reshape(-1, 3)[hidx] = N
    out['id'] = full(ids, -1, np.int16)
    out['u'] = full(U); out['v'] = full(V); out['rad'] = full(RADI)
    return out
