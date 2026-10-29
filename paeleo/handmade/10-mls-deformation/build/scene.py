"""SCION-10 · the place: a porch at dusk seen from the street side, ray-cast plane by plane in numpy, lit by the sky and,
through the doorway, by a lamp inside. The door leaf, the light it lets out and the shadows are computed per frame.
The person is a figure of shaded capsules (drawn in code, point-splatted like the dog, no face)."""
import os
import numpy as np
from scipy import ndimage as ndi
import cam

W, H = cam.W, cam.H
rng = np.random.default_rng(77)
LAMP = np.array([-1.3, 0.05, 1.95])
LAMP_COL = np.array([1.0, 0.70, 0.40])
SKY_COL = np.array([0.34, 0.39, 0.56])
DOOR_Y = (-0.50, 0.50); DOOR_Z = 2.08; WALL_T = 0.14
HINGE = np.array([-WALL_T + 0.03, -0.48])
MOON = np.array([-0.35, 0.55, 0.76]) / np.linalg.norm([-0.35, 0.55, 0.76]); MOON_COL = np.array([0.30, 0.36, 0.52])
LEAF_W = 0.96
STEP_X = 4.41


def fbm(shape, scales=(2, 6, 18), seed=0):
    r = np.random.default_rng(seed); out = np.zeros(shape)
    for i, s in enumerate(scales):
        n = ndi.gaussian_filter(r.normal(0, 1, shape), s); out += n / (n.std() + 1e-9) / (i + 1)
    return out / out.std()


class Set:
    def __init__(self):
        ys, xs = np.mgrid[0:H, 0:W].astype(float)
        a = (xs + 0.5 - cam.ORIGIN[0]) / cam.SCALE; b = (cam.ORIGIN[1] - ys - 0.5) / cam.SCALE
        base = a[..., None] * cam.R + b[..., None] * cam.UP
        self.base = base
        F = cam.F
        best = np.full((H, W), np.inf); kind = np.zeros((H, W), np.int16)
        nrm = np.zeros((H, W, 3)); alb = np.zeros((H, W, 3))

        def plane(axis, val, lo, hi, k, n):
            # intersection with plane P[axis] = val, inside box lo..hi on the other axes
            t = (val - base[..., axis]) / F[axis] if abs(F[axis]) > 1e-9 else np.full((H, W), np.inf)
            P = base + t[..., None] * F
            ok = np.ones((H, W), bool)
            for ax in range(3):
                if ax == axis: continue
                ok &= (P[..., ax] >= lo[ax]) & (P[..., ax] <= hi[ax])
            m = ok & (t < best)
            best[m] = t[m]; kind[m] = k; nrm[m] = n
            return m

        BIG = 50
        # 1 porch boards, 2 steps, 3 yard, 4 fascia, 5 house wall, 6 jamb, 7 sill, 8 room floor, 9 room walls, 10 lintel, 11 rail, 12 backdrop
        plane(2, 0.0, (0, -1.7, 0), (STEP_X, 1.75, 0), 1, (0, 0, 1))
        plane(2, -0.18, (STEP_X, -1.7, 0), (STEP_X + 0.3, 1.75, 0), 2, (0, 0, 1))
        plane(2, -0.36, (STEP_X + 0.3, -1.7, 0), (STEP_X + 0.6, 1.75, 0), 2, (0, 0, 1))
        plane(0, STEP_X, (0, -1.7, -0.18), (0, 1.75, 0), 2, (1, 0, 0))
        plane(0, STEP_X + 0.3, (0, -1.7, -0.36), (0, 1.75, -0.18), 2, (1, 0, 0))
        plane(0, STEP_X + 0.6, (0, -1.7, -0.6), (0, 1.75, -0.36), 2, (1, 0, 0))
        plane(2, -0.6, (0, -BIG, 0), (BIG, BIG, 0), 3, (0, 0, 1))
        plane(1, -1.7, (0, 0, -0.6), (STEP_X, 0, 0), 4, (0, -1, 0))
        # house wall with a doorway
        m = plane(0, 0.0, (0, -BIG, -0.6), (0, 6.0, 12.0), 5, (1, 0, 0))
        P = base + best[..., None] * F
        hole = m & (P[..., 1] > DOOR_Y[0]) & (P[..., 1] < DOOR_Y[1]) & (P[..., 2] < DOOR_Z) & (P[..., 2] > 0.0)
        best[hole] = np.inf; kind[hole] = 0
        plane(1, DOOR_Y[1], (-WALL_T, 0, 0), (0, 0, DOOR_Z), 6, (0, -1, 0))
        plane(2, DOOR_Z, (-WALL_T, DOOR_Y[0], 0), (0, DOOR_Y[1], 0), 10, (0, 0, -1))
        plane(2, 0.035, (-WALL_T - 0.02, DOOR_Y[0], 0), (0.07, DOOR_Y[1], 0), 7, (0, 0, 1))
        plane(0, 0.07, (0, DOOR_Y[0], 0), (0, DOOR_Y[1], 0.035), 7, (1, 0, 0))
        plane(2, 0.0, (-3.4, -BIG, 0), (-WALL_T, BIG, 0), 8, (0, 0, 1))
        plane(0, -3.4, (0, -BIG, 0), (0, BIG, 3.0), 9, (1, 0, 0))
        plane(1, 1.9, (-3.4, 0, 0), (-WALL_T, 0, 3.0), 9, (0, -1, 0))
        # railing along the far edge: posts, rails and balusters on one plane
        m = plane(1, 1.70, (0.05, 0, 0), (STEP_X - 0.05, 0, 0.95), 11, (0, -1, 0))
        P = base + best[..., None] * F
        xx, zz = P[..., 0], P[..., 2]
        xx = np.nan_to_num(xx); zz = np.nan_to_num(zz)
        post = (np.abs(((xx - 0.05) % 1.08) - 0.04) < 0.045)
        rail = (np.abs(zz - 0.90) < 0.045) | (np.abs(zz - 0.12) < 0.03)
        bal = (np.abs(((xx - 0.05) % 0.135) - 0.067) < 0.018) & (zz > 0.12) & (zz < 0.9)
        gap = m & ~(post | rail | bal)
        best[gap] = np.inf; kind[gap] = 0
        # second pass for what shows through the railing gaps: recompute the yard/backdrop behind
        self.kind0 = kind.copy()
        plane(1, 9.0, (-BIG, 0, -0.6), (BIG, 0, 12), 12, (0, -1, 0))
        # where the railing gap fell through, take whatever is nearest behind it
        if gap.any():
            t2 = np.full((H, W), np.inf); k2 = np.zeros((H, W), np.int16); n2 = np.zeros((H, W, 3))
            for (axis, val, lo, hi, k, n) in [(2, -0.6, (0, -BIG, 0), (BIG, BIG, 0), 3, (0, 0, 1)), (1, 9.0, (-BIG, 0, -0.6), (BIG, 0, 12), 12, (0, -1, 0)),
                                              (0, 0.0, (0, 1.75, -0.6), (0, 6.0, 12.0), 5, (1, 0, 0))]:
                t = (val - base[..., axis]) / F[axis]
                Pp = base + t[..., None] * F
                ok = np.ones((H, W), bool)
                for ax in range(3):
                    if ax == axis: continue
                    ok &= (Pp[..., ax] >= lo[ax]) & (Pp[..., ax] <= hi[ax])
                mm = ok & (t < t2) & gap
                t2[mm] = t[mm]; k2[mm] = k; n2[mm] = n
            best[gap] = t2[gap]; kind[gap] = k2[gap]; nrm[gap] = n2[gap]
        self.t = best; self.kind = kind; self.nrm = nrm
        self.P = base + np.where(np.isinf(best), 0, best)[..., None] * F
        self.alb = self.albedo()
        self.sky = kind == 0
        # which pixels can receive lamp light through the door (porch, sill, steps, jamb, railing, yard)
        self.outside = np.isin(kind, (1, 2, 3, 4, 6, 7, 10, 11)) | ((kind == 5) & (self.P[..., 0] > -0.01))
        self.inside = np.isin(kind, (8, 9))
        self._light_cache = {}

    def albedo(self):
        P, k = self.P, self.kind
        A = np.zeros((H, W, 3))
        n1 = fbm((H, W), (1, 4), 3)
        X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
        # porch boards run along x; each board its own tone; gaps between them; grain streaks
        bi = np.floor((Y + 1.7) / 0.142).astype(int)
        tone = np.random.default_rng(5).uniform(0.85, 1.12, 64)[np.clip(bi, 0, 63)]
        gapb = np.abs(((Y + 1.7) % 0.142) - 0.071) > 0.064
        grain = np.sin(X * 37 + np.sin(Y * 80) * 2 + n1 * 1.5) * 0.06
        joint = np.abs(((X + bi * 0.73) % 2.4) - 1.2) > 1.193
        wood = np.array([0.45, 0.40, 0.34])
        boards = wood * (tone * (1 + grain))[..., None] * np.where(gapb | joint, 0.35, 1.0)[..., None]
        A = np.where((k == 1)[..., None] | (k == 2)[..., None], boards, A)
        A = np.where((k == 3)[..., None], np.array([0.10, 0.13, 0.10]) * (1 + 0.10 * n1)[..., None], A)
        A = np.where((k == 4)[..., None], np.array([0.36, 0.33, 0.30]), A)
        # clapboard siding on the house wall
        clap = 0.85 + 0.15 * (((Z % 0.18) / 0.18) ** 0.6)
        wallc = np.array([0.66, 0.66, 0.62]) * (clap * (1 + 0.04 * n1))[..., None]
        A = np.where((k == 5)[..., None], wallc, A)
        trim = (k == 5) & (((np.abs(Y - DOOR_Y[0]) < 0.09) | (np.abs(Y - DOOR_Y[1]) < 0.09)) & (Z < DOOR_Z + 0.09) | ((np.abs(Z - DOOR_Z - 0.045) < 0.05) & (Y > DOOR_Y[0] - 0.09) & (Y < DOOR_Y[1] + 0.09)))
        A[trim] = [0.80, 0.79, 0.74]
        A = np.where(np.isin(k, (6, 10))[..., None], np.array([0.78, 0.76, 0.70]), A)
        A = np.where((k == 7)[..., None], np.array([0.55, 0.52, 0.47]) * (1 + 0.08 * n1)[..., None], A)
        # room: warm floorboards, a rug, plaster walls
        rb = np.abs(((Y + 3) % 0.12) - 0.06) > 0.056
        roomf = np.array([0.52, 0.36, 0.22]) * np.where(rb, 0.6, 1.0)[..., None]
        rug = (X < -0.6) & (X > -2.2) & (Y > -0.9) & (Y < 0.7)
        roomf = np.where(rug[..., None], np.array([0.50, 0.18, 0.14]) * (1 + 0.1 * np.sin(X * 30))[..., None], roomf)
        A = np.where((k == 8)[..., None], roomf, A)
        A = np.where((k == 9)[..., None], np.array([0.70, 0.62, 0.50]), A)
        A = np.where((k == 11)[..., None], np.array([0.60, 0.58, 0.54]), A)
        A = np.where((k == 12)[..., None], 0, A)
        return A

    def sky_and_trees(self):
        if getattr(self, '_bg', None) is None:
            self._bg = self._sky_and_trees()
        return self._bg

    def _sky_and_trees(self):
        """the backdrop: dusk gradient with a last band of amber low down, trees and a roofline in silhouette."""
        ys, xs = np.mgrid[0:H, 0:W].astype(float)
        P = self.P
        img = np.zeros((H, W, 3))
        g = np.clip(ys / 300, 0, 1)
        sky = (1 - g)[..., None] * np.array([0.07, 0.09, 0.20]) + g[..., None] * np.array([0.30, 0.30, 0.42])
        amber = np.exp(-((ys - 330) / 60) ** 2)[..., None] * np.array([0.25, 0.13, 0.05])
        sky = sky + amber
        n = fbm((1, W), (3, 12, 40), 9)[0]
        tree_top = 210 + 45 * n + 30 * np.sin(xs[0] / 140)
        trees = ys > tree_top[None, :]
        img = np.where(trees[..., None], np.array([0.035, 0.045, 0.06]), sky)
        bd = self.kind == 12
        out = np.zeros((H, W, 3)); out[bd] = img[bd]
        out[self.sky] = sky[self.sky]
        # stars
        st = rng.random((H, W)) > 0.9993
        out[self.sky & st & (ys < 200)] += 0.35
        return out

    def leaf(self, ang):
        """door leaf: hinge HINGE, swings into the room by ang (0 closed). Returns (origin, dir_along, normal)."""
        d = np.array([-np.sin(ang), np.cos(ang), 0.0])      # hinge on the near jamb; the free edge swings into the room
        n = np.array([np.cos(ang), np.sin(ang), 0.0])       # outward-facing side at ang=0 is +x
        return np.r_[HINGE, 0.0], d, n

    def lamp_vis(self, Pts, ang, nsamp=4):
        """fraction of the lamp (a small area light) visible from points Pts (...,3) through the doorway, past the leaf."""
        shp = Pts.shape[:-1]; Pf = Pts.reshape(-1, 3)
        vis = np.zeros(len(Pf))
        offs = [(0, 0.35, 0.15), (0, -0.35, 0.15), (0, 0, 0), (0, 0.0, -0.3)][:nsamp]
        o, d, n = self.leaf(ang)
        for off in offs:
            L = LAMP + np.array(off)
            D = L - Pf
            ok = np.ones(len(Pf), bool)
            # crossing the wall plane x = -WALL_T/2 inside the opening (only for points outside the room)
            outside = Pf[:, 0] > -WALL_T
            with np.errstate(divide='ignore', invalid='ignore'):
                s = (-WALL_T / 2 - Pf[:, 0]) / D[:, 0]
            cy = Pf[:, 1] + s * D[:, 1]; cz = Pf[:, 2] + s * D[:, 2]
            through = (cy > DOOR_Y[0]) & (cy < DOOR_Y[1]) & (cz < DOOR_Z) & (cz > 0)
            ok &= ~outside | through
            # blocked by the leaf?
            with np.errstate(divide='ignore', invalid='ignore'):
                sl = ((o - Pf) @ n) / (D @ n)
            hit = Pf + sl[:, None] * D
            along = (hit - o) @ d
            blk = (sl > 0) & (sl < 1) & (along > 0) & (along < LEAF_W) & (hit[:, 2] < DOOR_Z) & (hit[:, 2] > 0)
            ok &= ~blk
            vis += ok
        return (vis / len(offs)).reshape(shp)

    def lamp_term(self, Pts, N, ang, power, nsamp=4):
        D = LAMP - Pts; dist = np.linalg.norm(D, axis=-1)
        lam = np.clip((D * N).sum(-1) / np.maximum(dist, 1e-6), 0, 1)
        return power * lam / (0.4 + dist ** 2) * self.lamp_vis(Pts, ang, nsamp)

    def light_map(self, ang, power):
        key = (round(float(ang), 3), round(float(power), 3))
        if key not in self._light_cache:
            if len(self._light_cache) > 40: self._light_cache.clear()
            P, N = self.P, self.nrm
            m = self.outside | self.inside
            L = np.zeros((H, W))
            L[m] = self.lamp_term(P[m], N[m], ang, power)
            # the room is lit directly (no doorway between), brighter
            self._light_cache[key] = L
        return self._light_cache[key]

    def compose(self, ang, power, shadow=None, ao=None):
        """background image (linear-ish 0..1) for door angle ang, lamp power, optional lamp-shadow mask and ambient occlusion."""
        P, N, A = self.P, self.nrm, self.alb
        skyterm = (0.55 + 0.45 * np.clip(N[..., 2], 0, 1))[..., None] * SKY_COL * 0.62 + np.clip(N @ MOON, 0, 1)[..., None] * MOON_COL * 0.35
        L = self.light_map(ang, power).copy()
        if shadow is not None: L *= (1 - 0.85 * shadow)
        amb = skyterm * (1 - (0.55 * ao)[..., None] if ao is not None else 1)
        img = A * (amb + L[..., None] * LAMP_COL)
        img[self.inside] = A[self.inside] * (0.08 + L[self.inside][:, None] * LAMP_COL * 1.6 + 0.10 * power * LAMP_COL)
        bg = self.sky_and_trees()
        img = np.where((self.sky | (self.kind == 12))[..., None], bg, img)
        return img

    def leaf_layer(self, ang, power):
        """the door leaf drawn as its own ray-cast rectangle (outside face painted dark green, inside face lit by the lamp)."""
        o, d, n = self.leaf(ang)
        F = cam.F; base = self.base
        denom = F @ n
        if abs(denom) < 1e-6: return None
        t = ((o - base) @ n) / denom
        Pp = base + t[..., None] * F
        along = (Pp - o) @ d
        m = (along > 0) & (along < LEAF_W) & (Pp[..., 2] > 0.01) & (Pp[..., 2] < DOOR_Z - 0.01) & (t < self.t)
        if not m.any(): return None
        face_out = denom < 0      # we see the face whose normal is n
        Z = Pp[..., 2]
        panel = ((np.abs(along - LEAF_W / 2) < 0.30) & ((np.abs(Z - 0.55) < 0.35) | (np.abs(Z - 1.45) < 0.40)))
        base_col = np.array([0.17, 0.27, 0.22])
        col = base_col * np.where(panel, 0.85, 1.0)[..., None]
        nn = n if face_out else -n
        lit = self.lamp_term(Pp[m], np.broadcast_to(nn, Pp[m].shape), ang, power) if not face_out else np.zeros(m.sum())
        lit_in = (1 - face_out) * power * 0.25
        sky = SKY_COL * 0.35
        c = col[m] * (sky + (lit[:, None] + lit_in) * LAMP_COL)
        out = np.zeros((H, W, 4)); out[m, :3] = c; out[m, 3] = 1
        return m, out


# ---------------- the person -------------------------------------------------------------------------------------------
def _capsule_pts(a, b, r, dens):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ax = b - a; L = np.linalg.norm(ax) + 1e-9; u = ax / L
    tmp = np.array([0, 0, 1.0]) if abs(u[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(u, tmp); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    area = 2 * np.pi * r * L + 4 * np.pi * r * r
    n = int(area * dens) + 50
    k = np.random.default_rng(int(L * 1e4 + r * 1e5) % 2 ** 31)
    # cylinder part
    nc = int(n * (2 * np.pi * r * L) / area)
    s = k.random(nc); ph = k.random(nc) * 2 * np.pi
    N1 = np.cos(ph)[:, None] * e1 + np.sin(ph)[:, None] * e2
    P1 = a + s[:, None] * ax + r * N1
    ns = n - nc
    v = k.normal(0, 1, (ns, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    end = np.where(((v @ u) > 0)[:, None], b, a)
    v = np.where((((v @ u) > 0) == ((v @ u) > 0))[:, None], v, v)
    P2 = end + r * v
    return np.r_[P1, P2], np.r_[N1, v]


def person_points(pp, dens=30000):
    """pp: dict of joint positions and colours -> points, normals, colours (no face, no features)."""
    Ps, Ns, Cs = [], [], []
    for a, b, r, col in pp:
        P, N = _capsule_pts(a, b, r, dens)
        Ps.append(P); Ns.append(N); Cs.append(np.broadcast_to(np.asarray(col, float), P.shape))
    return np.concatenate(Ps), np.concatenate(Ns), np.concatenate(Cs)
