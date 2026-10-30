"""SCION 37 rasterizer: a z-buffered triangle rasterizer in numpy (no GL).
Triangles are bucketed by screen bounding-box size; each bucket tests every pixel centre of its box with edge functions
at once; the nearest candidate per pixel wins (np.minimum.at on depth). Returns per-pixel triangle id and barycentrics,
so every attribute (UV, rest position, world position, weights) can be interpolated and shaded afterwards."""
import numpy as np


class Camera:
    def __init__(self, eye, target, f, W, H, up=(0, 1, 0)):
        self.eye = np.asarray(eye, float); self.target = np.asarray(target, float); self.f = f; self.W = W; self.H = H
        fw = self.target - self.eye; fw /= np.linalg.norm(fw)
        r = np.cross(fw, up); r /= np.linalg.norm(r); u = np.cross(r, fw)
        self.R = np.stack([r, u, fw])            # rows: right, up, forward

    def project(self, X):
        c = (X - self.eye) @ self.R.T
        z = c[:, 2]
        zz = np.where(z > 1e-4, z, 1e-4)
        return np.stack([self.W / 2 + self.f * c[:, 0] / zz, self.H / 2 - self.f * c[:, 1] / zz], 1), z

    def ray(self, px, py):
        d = np.stack([(px - self.W / 2) / self.f, -(py - self.H / 2) / self.f, np.ones_like(px)], -1) @ self.R
        return d / np.linalg.norm(d, axis=-1, keepdims=True)

    def scaled(self, s):
        return Camera(self.eye, self.target, self.f * s, int(self.W * s), int(self.H * s))


def rasterize(xy, z, F, W, H, near=.05, chunk=3_000_000):
    """xy (n,2) pixel coords, z (n,) view depth, F (m,3). Returns tri (H*W,) [-1 empty], bary (H*W,3), depth (H*W,)"""
    A = xy[F]; Z = z[F]
    ok = (Z > near).all(1)
    area = (A[:, 1, 0] - A[:, 0, 0]) * (A[:, 2, 1] - A[:, 0, 1]) - (A[:, 2, 0] - A[:, 0, 0]) * (A[:, 1, 1] - A[:, 0, 1])
    ok &= area < -1e-9                                         # front faces (counter-clockwise in y-up = cw in y-down)
    x0 = np.floor(A[..., 0].min(1)); x1 = np.ceil(A[..., 0].max(1)); y0 = np.floor(A[..., 1].min(1)); y1 = np.ceil(A[..., 1].max(1))
    ok &= (x1 >= 0) & (x0 < W) & (y1 >= 0) & (y0 < H)
    tid = np.nonzero(ok)[0]
    x0 = np.clip(x0[tid], 0, W - 1).astype(np.int64); y0 = np.clip(y0[tid], 0, H - 1).astype(np.int64)
    bw = np.clip(x1[tid], 0, W - 1).astype(np.int64) - x0 + 1; bh = np.clip(y1[tid], 0, H - 1).astype(np.int64) - y0 + 1
    s = np.maximum(bw, bh)
    zbuf = np.full(H * W, np.inf); cands = []
    sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    lo = 0
    for S in sizes:
        sel = np.nonzero((s > lo) & (s <= S))[0]; lo = S
        if not len(sel): continue
        per = max(1, chunk // (S * S))
        oy, ox = np.mgrid[0:S, 0:S]; ox = ox.ravel(); oy = oy.ravel()
        for c0 in range(0, len(sel), per):
            ss = sel[c0:c0 + per]; t = tid[ss]
            px = x0[ss, None] + ox[None]; py = y0[ss, None] + oy[None]
            inb = (px < W) & (py < H)
            cx = px + .5; cy = py + .5
            a = A[t]
            def ed(i, j):
                return (a[:, j, 0, None] - a[:, i, 0, None]) * (cy - a[:, i, 1, None]) - (a[:, j, 1, None] - a[:, i, 1, None]) * (cx - a[:, i, 0, None])
            ar = area[t][:, None]
            b0 = ed(1, 2) / ar; b1 = ed(2, 0) / ar; b2 = 1 - b0 - b1
            m = inb & (b0 >= -1e-7) & (b1 >= -1e-7) & (b2 >= -1e-7)
            if not m.any(): continue
            ti = np.broadcast_to(t[:, None], m.shape)[m]
            B0, B1, B2 = b0[m], b1[m], b2[m]
            zt = Z[ti]
            # perspective-correct barycentrics
            q0, q1, q2 = B0 / zt[:, 0], B1 / zt[:, 1], B2 / zt[:, 2]; qs = q0 + q1 + q2
            depth = 1 / qs
            pix = (py[m] * W + px[m])
            np.minimum.at(zbuf, pix, depth)
            cands.append((pix, depth, ti, np.stack([q0 / qs, q1 / qs, q2 / qs], 1)))
    tri = np.full(H * W, -1, np.int64); bary = np.zeros((H * W, 3))
    for pix, depth, ti, b in cands:
        win = depth <= zbuf[pix]
        tri[pix[win]] = ti[win]; bary[pix[win]] = b[win]
    return tri, bary, zbuf


def interp(attr, F, tri, bary):
    """interpolate per-vertex attr (n,k) at covered pixels; returns (P,k) for pixels where tri>=0"""
    m = tri >= 0; t = tri[m]
    return np.einsum('pi,pik->pk', bary[m], attr[F[t]]), m


def downsample(img, s):
    if s == 1: return img
    H, W = img.shape[0] // s, img.shape[1] // s
    return img[:H * s, :W * s].reshape(H, s, W, s, -1).mean((1, 3))
