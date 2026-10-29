"""SCION 42 · the learned puppet at render time.

The dog on screen is the template frame's own pixels (archive photograph), carried by the learned layers:
  every template pixel is split into SUBxSUB sub-points; each sub-point has the learned soft layer weights w (from the
  four nearest fitted template points), and moves by  q = sum_k w_k T_k [p;1]  (the same blend the fit used).
  T_k (per layer) = screen placement  o  pose of layer k in dog space.
  Pose in dog space = learned example motion (library, relative to the root layer) followed by optional rotations about
  the learned joints (the manual override, used only where the examples have nothing: lying, the look in).
Visibility states: 'profile' (this learned puppet, facing either way) and 'view' (an archive frame shown whole, for the
3/4 and front views the learned model was never asked to produce).
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.abspath(os.path.join(ROOT, '..', 'kit', 'archive-dog'))
SUB = 3


def to3(A):
    M = np.eye(3); M[:2] = A; return M


def inv3(M): return np.linalg.inv(M)


def load_frame(i, mirror=False):
    import fit as F
    im, mk = F.load(i, mirror)
    return im, mk


class Puppet:
    def __init__(self):
        M = np.load(os.path.join(ROOT, 'model', 'puppet.npz'))
        self.M = M
        self.K = M['w'].shape[1]
        self.parent = M['parent']; self.root = int(M['root'])
        tfi = int(M['template_frame'])
        im, mk = load_frame(tfi)
        self.tim = im; self.tmask = mk
        ys, xs = np.nonzero(mk)
        P = np.stack([xs, ys], 1).astype(np.float64)
        offs = (np.arange(SUB) + 0.5) / SUB - 0.5
        ox, oy = np.meshgrid(offs, offs)
        self.P = (P[:, None, :] + np.stack([ox.ravel(), oy.ravel()], 1)[None]).reshape(-1, 2)
        d, nn = cKDTree(M['p']).query(self.P, k=4)
        wk = 1 / (d + 0.5); wk /= wk.sum(1, keepdims=True)
        self.w = np.einsum('nj,njk->nk', wk, M['w'][nn])
        self.lab = np.argmax(self.w, 1)
        import fit as F
        self.col = F.bil(ndimage.gaussian_filter(im, 0.4), self.P[:, 0], self.P[:, 1])
        soft = ndimage.gaussian_filter(mk.astype(np.float32), 0.8)
        self.alpha = np.clip(F.bil(soft, self.P[:, 0], self.P[:, 1]) * 1.6 - 0.3, 0, 1)
        self.Ph = np.concatenate([self.P, np.ones((len(self.P), 1))], 1)
        # joints: pivot between each part and its parent (template coords)
        self.pivot = {}
        for (a, b), pv in zip(M['joint_keys'], M['joint_pivots']):
            self.pivot[(int(a), int(b))] = pv; self.pivot[(int(b), int(a))] = pv
        self.anchor = np.array([P[:, 0].mean(), P[:, 1].max()])     # body centre x, feet line y
        self.bbox = (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())
        # library of learned motions (relative to the root layer)
        L = np.load(os.path.join(ROOT, 'model', 'library.npz'))
        self.lib = {}
        for name in L.files:
            A = L[name]                        # F x K x 2 x 3
            rel = np.zeros((A.shape[0], self.K, 3, 3))
            for f in range(A.shape[0]):
                R0 = inv3(to3(A[f, self.root]))
                for k in range(self.K): rel[f, k] = R0 @ to3(A[f, k])
            self.lib[name] = rel
        self.order = np.argsort(self.depth_of_labels(), kind='stable')
        self.add_tail()

    def add_tail(self):
        """the template frame shows only the root of the tail; the tail itself is cut from archive frame 6 of the same
        dog (mask pixels right of x=224), pinned to the learned rump layer at its base, with its own wag hinge"""
        import json as _j
        n_ = None
        kp = _j.load(open(os.path.join(KIT, 'pose_agent_v8.json')))[str(int(self.M['template_frame']))]
        from scipy.spatial import cKDTree as _T
        self.rump = int(self.M['lab'][_T(self.M['p']).query(kp['tail'])[1]])
        im6, mk6 = load_frame(6)
        ys, xs = np.nonzero(mk6); sel = xs >= 224; xs, ys = xs[sel], ys[sel]
        off = np.array([-3.0, -6.0])
        P = np.stack([xs, ys], 1).astype(np.float64)
        offs = (np.arange(SUB) + 0.5) / SUB - 0.5
        ox, oy = np.meshgrid(offs, offs)
        P = (P[:, None, :] + np.stack([ox.ravel(), oy.ravel()], 1)[None]).reshape(-1, 2)
        import fit as F
        col = F.bil(ndimage.gaussian_filter(im6, 0.4), P[:, 0], P[:, 1])
        soft = ndimage.gaussian_filter(mk6.astype(np.float32), 0.8)
        al = np.clip(F.bil(soft, P[:, 0], P[:, 1]) * 1.6 - 0.3, 0, 1)
        P = P + off
        self.tail_base = np.array([221.0, 135.0])
        nt = len(P); K = self.K
        self.w = np.concatenate([np.concatenate([self.w, np.zeros((len(self.w), 1))], 1), np.tile(np.eye(K + 1)[K], (nt, 1))])
        self.P = np.concatenate([self.P, P]); self.Ph = np.concatenate([self.P, np.ones((len(self.P), 1))], 1)
        self.col = np.concatenate([self.col, col]); self.alpha = np.concatenate([self.alpha, al])
        self.lab = np.concatenate([self.lab, np.full(nt, K)])
        self.order = np.concatenate([np.arange(len(self.P) - nt, len(self.P)), self.order])   # tail drawn first (behind)
        self.tail_angle = 0.0

    def with_tail(self, T):
        if T.shape[0] == self.K + 1: return T
        c = self.tail_base; a = self.tail_angle
        R = np.eye(3); cs, sn = np.cos(a), np.sin(a); R[:2, :2] = [[cs, -sn], [sn, cs]]; R[:2, 2] = c - R[:2, :2] @ c
        return np.concatenate([T, (T[self.rump] @ R)[None]])

    def depth_of_labels(self):
        # authored layer order (manual override): the learned layers don't tell near from far; layers whose points sit
        # low (legs) are drawn over the trunk, which reads correctly for the near legs in profile
        cy = np.array([self.P[self.lab == k, 1].mean() if np.any(self.lab == k) else 0 for k in range(self.K)])
        d = cy[self.lab]
        return d

    def chain(self, k):
        c = []
        while k >= 0 and k != self.root: c.append(k); k = int(self.parent[k])
        return c[::-1]

    def articulate(self, rel, angles):
        """rel: K x 3x3 learned relative pose; angles: dict part -> radians about its joint with its parent"""
        T = [None] * self.K
        T[self.root] = rel[self.root]
        done = {self.root}
        def get(k):
            if T[k] is not None: return T[k]
            p = int(self.parent[k]); Tp = get(p)
            extra = Tp @ inv3(rel[p])                      # the parent's override motion, carried to the child
            Tk = extra @ rel[k]
            a = angles.get(k, 0.0)
            if a:
                piv = self.pivot.get((k, p))
                c = (Tk @ np.array([piv[0], piv[1], 1.0]))[:2]
                R = np.eye(3); cs, sn = np.cos(a), np.sin(a)
                R[:2, :2] = [[cs, -sn], [sn, cs]]; R[:2, 2] = c - R[:2, :2] @ c
                Tk = R @ Tk
            T[k] = Tk; return Tk
        for k in range(self.K): get(k)
        return np.stack(T)

    def render(self, T, place, canvas_rgb, canvas_a=None, tint=None, seam=True, pins=None, sel=None, hard=False):
        """T: K x 3x3 dog-space; place: 3x3 dog space -> screen.  Splats onto canvas (float HxWx3) in place.
        returns the screen points and alpha mask used for measurement"""
        T = self.with_tail(T)
        G = np.einsum('ij,kjl->kil', place, T)[:, :2]      # K+1 x 2 x 3 (the last is the tail piece)
        Pk = np.einsum('kij,nj->kni', G, self.Ph)
        wts = np.eye(self.K + 1)[self.lab] if hard else self.w
        hs = getattr(self, 'hard_set', None)
        if hs and not hard:
            # layers folded far from their neighbours are cut free (no blend across the fold)
            wts = wts.copy()
            for k in hs:
                wts[:, k] = 0
                wts[self.lab == k] = np.eye(self.K + 1)[k]
            wts /= wts.sum(1, keepdims=True)
        q = np.einsum('nk,kni->ni', wts, Pk)
        H, W = canvas_rgb.shape[:2]
        xi = np.round(q[:, 0]).astype(int); yi = np.round(q[:, 1]).astype(int)
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        if sel is not None: ok &= sel
        order = self.order
        if getattr(self, 'behind', None):
            b = np.isin(self.lab[order], list(self.behind))
            order = np.concatenate([order[b], order[~b]])
        if getattr(self, 'front', None):
            f = np.isin(self.lab[order], list(self.front))
            order = np.concatenate([order[~f], order[f]])
        o = order[ok[order]]
        acc = np.zeros((H, W), np.float32); col = np.zeros((H, W), np.float32); lab = -np.ones((H, W), np.int16)
        acc[yi[o], xi[o]] = self.alpha[o]; col[yi[o], xi[o]] = self.col[o]; lab[yi[o], xi[o]] = self.lab[o]
        x0, x1 = max(0, xi[ok].min() - 3), min(W, xi[ok].max() + 4)
        y0, y1 = max(0, yi[ok].min() - 3), min(H, yi[ok].max() + 4)
        a = acc[y0:y1, x0:x1]; c = col[y0:y1, x0:x1]; lb = lab[y0:y1, x0:x1]
        # fill splat holes (a hole is a pixel with >=5 filled neighbours)
        filled = a > 0
        cnt = ndimage.uniform_filter(filled.astype(np.float32), 3) * 9
        hole = (~filled) & (cnt >= 5)
        if hole.any():
            sa = ndimage.uniform_filter(a, 3) * 9 / np.maximum(cnt, 1); sc = ndimage.uniform_filter(c * filled, 3) * 9 / np.maximum(cnt, 1)
            a = np.where(hole, sa, a); c = np.where(hole, sc, c)
        # close the gaps a folded layer leaves inside the silhouette (no background speckle through the body)
        inside = ndimage.binary_closing(a > 0.3, iterations=3) & ~(a > 0.3)
        if inside.any():
            wsum = ndimage.gaussian_filter((a > 0.3).astype(np.float32), 2.0)
            cfill = ndimage.gaussian_filter(c * (a > 0.3), 2.0) / np.maximum(wsum, 1e-3)
            c = np.where(inside, cfill, c); a = np.where(inside, 1.0, a)
            lb = np.where(inside & (lb < 0), lb, lb)
        a = ndimage.gaussian_filter(a, 0.6)
        lg = getattr(self, 'label_gain', None)
        if lg:
            gimg = np.ones_like(c)
            for k, gk in lg.items(): gimg[lb == k] = gk
            c = c * ndimage.gaussian_filter(gimg, 1.0)
        rgb = c[..., None] * (tint if tint is not None else np.ones(3))[None, None] if tint is None or np.ndim(tint) == 1 else c[..., None] * tint[y0:y1, x0:x1]
        if seam:
            # the cuts between learned layers, drawn as a faint dark seam: the discovered structure, visible
            # majority label in a 5x5 window: interleaved splats of two layers do not draw a speckled seam
            labs = [k for k in np.unique(lb) if k >= 0]
            sm = np.stack([ndimage.uniform_filter((lb == k).astype(np.float32), 5) for k in labs], 0)
            lb = np.where(sm.max(0) > 0.05, np.array(labs)[np.argmax(sm, 0)], -1)
            e = np.zeros_like(filled)
            e[:, 1:] |= (lb[:, 1:] != lb[:, :-1]) & (lb[:, 1:] >= 0) & (lb[:, :-1] >= 0)
            e[1:, :] |= (lb[1:, :] != lb[:-1, :]) & (lb[1:, :] >= 0) & (lb[:-1, :] >= 0)
            e = ndimage.gaussian_filter(e.astype(np.float32), 0.5)
            rgb = rgb * (1 - 0.30 * np.clip(e * 2, 0, 1))[..., None]
        hl = getattr(self, 'head_label', None)
        if hl is not None:
            # a legible head: the head layer's contrast lifted and its outline drawn as a thin pale rim
            hm = ndimage.gaussian_filter((lb == hl).astype(np.float32), 0.8)
            body = (a > 0.5)
            edge = body & ~ndimage.binary_erosion(body, iterations=1)
            edge = ndimage.binary_dilation(edge, iterations=0) if False else edge
            mean = float(rgb[lb == hl].mean()) if np.any(lb == hl) else 0.0
            rgb = rgb * (1 - hm[..., None]) + (mean + (rgb - mean) * 1.9 + 0.04) * hm[..., None]
            rim = edge & (ndimage.binary_dilation(lb == hl, iterations=2))
            if getattr(self, 'rim', True):
                rgb = np.where(rim[..., None], np.array([0.86, 0.80, 0.68]) * 0.9, rgb)
        reg = canvas_rgb[y0:y1, x0:x1]
        canvas_rgb[y0:y1, x0:x1] = reg * (1 - a[..., None]) + rgb * a[..., None]
        if canvas_a is not None: canvas_a[y0:y1, x0:x1] = np.maximum(canvas_a[y0:y1, x0:x1], a)
        full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = a
        return dict(q=q, G=G, alpha=full, box=(x0, y0, x1, y1))

    def joint_screen(self, T, place):
        out = {}
        for k in range(self.K):
            p = int(self.parent[k])
            if p < 0: continue
            piv = self.pivot.get((k, p))
            if piv is None: continue
            out[k] = (place @ T[k] @ np.array([piv[0], piv[1], 1.0]))[:2]
        return out


class ViewFrame:
    """a whole archive frame used as a visibility state (3/4 and front views)"""
    cache = {}

    @classmethod
    def get(cls, i, mirror=False):
        key = (i, mirror)
        if key not in cls.cache:
            im, mk = load_frame(i, mirror)
            ys, xs = np.nonzero(mk)
            soft = ndimage.gaussian_filter(mk.astype(np.float32), 0.8)
            cls.cache[key] = dict(im=im, a=np.clip(soft * 1.6 - 0.3, 0, 1), bbox=(xs.min(), ys.min(), xs.max(), ys.max()),
                                  cx=xs.mean(), foot=ys.max(), h=ys.max() - ys.min())
        return cls.cache[key]
