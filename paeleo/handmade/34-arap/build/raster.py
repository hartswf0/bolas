"""Textured-triangle rasteriser (numpy + PIL): an ID buffer drawn in layer order, then per-pixel affine lookup."""
import numpy as np
from PIL import Image, ImageDraw


class Tex:
    def __init__(self, path, scale=0.5):
        im = Image.open(path).convert('RGBA')
        self.scale = scale
        if scale != 1.0:
            im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255
        a[..., :3] *= a[..., 3:4]                    # premultiplied
        self.a = a
        self.h, self.w = a.shape[:2]

    def sample(self, u, v):
        u = np.clip(u * self.scale - 0.5, 0, self.w - 1.001); v = np.clip(v * self.scale - 0.5, 0, self.h - 1.001)
        x0 = u.astype(int); y0 = v.astype(int); fx = (u - x0)[:, None]; fy = (v - y0)[:, None]
        A = self.a
        return (A[y0, x0] * (1 - fx) * (1 - fy) + A[y0, x0 + 1] * fx * (1 - fy) + A[y0 + 1, x0] * (1 - fx) * fy
                + A[y0 + 1, x0 + 1] * fx * fy)


def draw_pieces(size, items, ss=2, wire=None):
    """items: list of (S screen px (n,2), T, uv, tex, tri_layer(or None), mirrored(bool)) drawn in list order.
    Returns premultiplied RGBA float (H, W, 4) at 1x, and the coverage of each item (for measurement)."""
    W, H = size
    # bounding box of everything
    allS = np.vstack([it[0] for it in items])
    x0 = int(max(0, np.floor(allS[:, 0].min()) - 3)); x1 = int(min(W, np.ceil(allS[:, 0].max()) + 3))
    y0 = int(max(0, np.floor(allS[:, 1].min()) - 3)); y1 = int(min(H, np.ceil(allS[:, 1].max()) + 3))
    out = np.zeros((H, W, 4), np.float32)
    if x1 <= x0 or y1 <= y0:
        return out, (x0, y0, x1, y1)
    bw, bh = (x1 - x0) * ss, (y1 - y0) * ss
    idb = Image.new('I', (bw, bh), 0)
    dr = ImageDraw.Draw(idb)
    affs = []
    texs = []
    base = 0
    for k, (S, T, uv, tex, lay, mir) in enumerate(items):
        Ss = (S - [x0, y0]) * ss
        order = np.argsort(lay, kind='stable') if lay is not None else np.arange(len(T))
        for t in order:
            tri = T[t]
            dr.polygon([(Ss[i, 0], Ss[i, 1]) for i in tri], fill=int(base + t + 1))
        # affine screen(ss px) -> uv per triangle
        s0, s1, s2 = Ss[T[:, 0]], Ss[T[:, 1]], Ss[T[:, 2]]
        u0, u1, u2 = uv[T[:, 0]], uv[T[:, 1]], uv[T[:, 2]]
        Ms = np.stack([s1 - s0, s2 - s0], 2)              # columns
        Mu = np.stack([u1 - u0, u2 - u0], 2)
        det = Ms[:, 0, 0] * Ms[:, 1, 1] - Ms[:, 0, 1] * Ms[:, 1, 0]
        det = np.where(np.abs(det) < 1e-9, 1e-9, det)
        inv = np.stack([np.stack([Ms[:, 1, 1], -Ms[:, 0, 1]], 1), np.stack([-Ms[:, 1, 0], Ms[:, 0, 0]], 1)], 1) / det[:, None, None]
        A = np.einsum('kij,kjl->kil', Mu, inv)
        affs.append((A, s0, u0))
        texs.append((base, base + len(T), tex))
        base += len(T)
    ids = np.asarray(idb, dtype=np.int64)
    hit = ids > 0
    ys, xs = np.nonzero(hit)
    tid = ids[ys, xs] - 1
    big = np.zeros((bh, bw, 4), np.float32)
    P = np.stack([xs + 0.5, ys + 0.5], 1)
    for (A, s0, u0), (lo, hi, tex) in zip(affs, texs):
        sel = (tid >= lo) & (tid < hi)
        if not sel.any():
            continue
        t = tid[sel] - lo
        d = P[sel] - s0[t]
        uvp = u0[t] + np.einsum('kij,kj->ki', A[t], d)
        big[ys[sel], xs[sel]] = tex.sample(uvp[:, 0], uvp[:, 1])
    if wire is not None:
        wim = Image.new('L', (bw, bh), 0)
        wd = ImageDraw.Draw(wim)
        for (S, T, uv, tex, lay, mir), wa in zip(items, wire):
            if wa <= 0:
                continue
            Ss = (S - [x0, y0]) * ss
            E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
            E = np.unique(np.sort(E, 1), axis=0)
            for i, j in E:
                wd.line([(Ss[i, 0], Ss[i, 1]), (Ss[j, 0], Ss[j, 1])], fill=int(255 * wa), width=1)
        wa_ = np.asarray(wim).astype(np.float32)[..., None] / 255 * big[..., 3:4]
        col = np.array([0.95, 0.55, 0.30, 1.0], np.float32)
        big = big * (1 - wa_) + col * wa_ * big[..., 3:4]
    small = big.reshape(y1 - y0, ss, x1 - x0, ss, 4).mean((1, 3))
    out[y0:y1, x0:x1] = small
    return out, (x0, y0, x1, y1)


def over(dst_rgb, src_pm):
    """Composite premultiplied RGBA over an RGB float image (in place)."""
    a = src_pm[..., 3:4]
    dst_rgb *= (1 - a)
    dst_rgb += src_pm[..., :3]
    return dst_rgb
