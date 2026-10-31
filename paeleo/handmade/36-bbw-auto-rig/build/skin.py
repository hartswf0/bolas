"""SCION-36 · runtime skinning: linear blend of handle affines with the precomputed BBW weights, and a small
vectorised triangle rasteriser that maps the archive frame (texture + its own SAM alpha) onto the deformed mesh."""
import numpy as np


def rot(theta, c):
    c = np.asarray(c, float); C, S = np.cos(theta), np.sin(theta)
    A = np.array([[C, -S], [S, C]])
    return np.hstack([A, (c - A @ c)[:, None]])


def scale_along(c, d, s, s_perp=1.0):
    """affine scaling by s along unit direction d (and s_perp across it) about point c"""
    d = np.asarray(d, float); d = d / (np.linalg.norm(d) + 1e-12); n = np.array([-d[1], d[0]])
    A = s * np.outer(d, d) + s_perp * np.outer(n, n)
    c = np.asarray(c, float)
    return np.hstack([A, (c - A @ c)[:, None]])


def trans(t):
    return np.array([[1, 0, t[0]], [0, 1, t[1]]], float)


def compose(*Ms):
    """compose 2x3 affines: compose(A, B)(p) = A(B(p))"""
    R = np.eye(3)
    for M in Ms:
        R = R @ np.vstack([M, [0, 0, 1]])
    return R[:2]


def apply(M, P):
    P = np.asarray(P, float)
    return P @ M[:, :2].T + M[:, 2]


def lbs(V, W, Ms):
    """V (n,2), W (n,m), Ms (m,2,3) -> deformed (n,2)"""
    Ms = np.asarray(Ms)
    A = np.einsum('nm,mij->nij', W, Ms)
    return np.einsum('nij,nj->ni', A[:, :, :2], V) + A[:, :, 2]


def raster(canvas, alpha_acc, Vd, Vs, T, tex, depth=None, gain=1.0, clip=None):
    """draw textured triangles: Vd screen positions, Vs source uv, tex (h,w,4) float (rgb + alpha).
    Front-most (lowest depth) wins per pixel; composite over canvas in place. Returns the coverage mask."""
    Hc, Wc = canvas.shape[:2]
    P = Vd[T]  # (t,3,2)
    x0 = np.floor(P[:, :, 0].min(1)).astype(int); x1 = np.ceil(P[:, :, 0].max(1)).astype(int)
    y0 = np.floor(P[:, :, 1].min(1)).astype(int); y1 = np.ceil(P[:, :, 1].max(1)).astype(int)
    x0 = np.clip(x0, 0, Wc - 1); x1 = np.clip(x1, 0, Wc - 1); y0 = np.clip(y0, 0, Hc - 1); y1 = np.clip(y1, 0, Hc - 1)
    bw = x1 - x0 + 1; bh = y1 - y0 + 1
    ok = (bw > 0) & (bh > 0) & (bw < 80) & (bh < 80)
    idx = np.nonzero(ok)[0]
    cnt = (bw * bh)[idx]
    tid = np.repeat(idx, cnt)
    start = np.repeat(np.cumsum(cnt) - cnt, cnt)
    k = np.arange(cnt.sum()) - start
    px = x0[tid] + k % bw[tid]; py = y0[tid] + k // bw[tid]
    a, b, c = P[tid, 0], P[tid, 1], P[tid, 2]
    qx = px + .5; qy = py + .5
    det = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    det = np.where(np.abs(det) < 1e-9, 1e-9, det)
    l1 = ((qx - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (qy - a[:, 1])) / det
    l2 = ((b[:, 0] - a[:, 0]) * (qy - a[:, 1]) - (qx - a[:, 0]) * (b[:, 1] - a[:, 1])) / det
    l0 = 1 - l1 - l2
    e = -1e-4
    ins = (l0 >= e) & (l1 >= e) & (l2 >= e)
    tid, px, py, l0, l1, l2 = tid[ins], px[ins], py[ins], l0[ins], l1[ins], l2[ins]
    Ti = T[tid]
    if depth is not None:
        z = depth[Ti[:, 0]] * l0 + depth[Ti[:, 1]] * l1 + depth[Ti[:, 2]] * l2
        o = np.argsort(-z, kind='stable')  # far first, near last
        tid, px, py, l0, l1, l2, Ti = tid[o], px[o], py[o], l0[o], l1[o], l2[o], Ti[o]
    pix = py * Wc + px
    # last occurrence wins (nearest)
    _, last = np.unique(pix[::-1], return_index=True)
    sel = len(pix) - 1 - last
    px, py, l0, l1, l2, Ti = px[sel], py[sel], l0[sel], l1[sel], l2[sel], Ti[sel]
    u = Vs[Ti[:, 0], 0] * l0 + Vs[Ti[:, 1], 0] * l1 + Vs[Ti[:, 2], 0] * l2
    v = Vs[Ti[:, 0], 1] * l0 + Vs[Ti[:, 1], 1] * l1 + Vs[Ti[:, 2], 1] * l2
    col = bilinear(tex, u, v)
    al = col[:, 3:4] * gain
    if clip is not None:
        al = al * clip[py, px][:, None]
    canvas[py, px] = canvas[py, px] * (1 - al) + col[:, :3] * al
    if alpha_acc is not None:
        alpha_acc[py, px] = np.maximum(alpha_acc[py, px], al[:, 0])
    return px, py, al[:, 0]


def bilinear(tex, u, v):
    h, w = tex.shape[:2]
    u = np.clip(u, 0, w - 1.001); v = np.clip(v, 0, h - 1.001)
    i = v.astype(int); j = u.astype(int); fy = (v - i)[:, None]; fx = (u - j)[:, None]
    return (tex[i, j] * (1 - fx) * (1 - fy) + tex[i, j + 1] * fx * (1 - fy) + tex[i + 1, j] * (1 - fx) * fy
            + tex[i + 1, j + 1] * fx * fy)
