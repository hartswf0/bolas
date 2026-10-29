"""Local-global as-rigid-as-possible solver (Sorkine & Alexa 2007), in 2D, on a triangle mesh.

Energy  E(x) = sum_i sum_{j in N(i)} w_ij || (x_i - x_j) - R_i (p_i - p_j) ||^2
  w_ij  cotangent edge weights (clamped positive), each triangle's contribution scaled by its rigidity weight
        (protected features: eye, nose, tag get 30)
  R_i   one rotation per vertex cell (its one-ring), closed form in 2D: theta_i = atan2(S01 - S10, S00 + S11),
        S_i = sum_j w_ij (p_i - p_j)(x_i - x_j)^T
Handles are HARD constraints: constrained vertices are eliminated, the free block L_FF is factored once (sparse LU,
scipy SuperLU) per mesh and handle set, and every global step is two back-substitutions (x and y).
Each frame warm-starts from the previous frame's solution.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl


def cot_weights(V, T, tri_w):
    n = len(V)
    I, J, Wt = [], [], []
    for k in range(3):
        i, j, o = T[:, k], T[:, (k + 1) % 3], T[:, (k + 2) % 3]
        u, v = V[i] - V[o], V[j] - V[o]
        cross = np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0])
        cot = (u * v).sum(1) / np.maximum(cross, 1e-9)
        I.append(i); J.append(j); Wt.append(0.5 * cot * tri_w)
    I, J, Wt = np.concatenate(I), np.concatenate(J), np.concatenate(Wt)
    Wm = sp.coo_matrix((Wt, (I, J)), shape=(n, n)).tocsr()
    Wm = Wm + Wm.T
    Wm.data = np.maximum(Wm.data, 1e-3 * np.median(np.abs(Wm.data)))
    return Wm.tocoo()


class ARAP:
    def __init__(self, V, T, tri_w, handles):
        """handles: dict name -> array of vertex indices (disjoint)."""
        self.P = np.asarray(V, float)
        self.T = np.asarray(T)
        self.n = len(V)
        self.tri_w0 = np.asarray(tri_w, float).copy()
        self.stiff = np.ones(len(self.tri_w0))
        self.tri_w = self.tri_w0.copy()
        self.handles_in = handles
        self.repairs = 0
        self._build()
        self.X = self.P.copy()

    def _build(self):
        handles = self.handles_in
        W = cot_weights(self.P, self.T, self.tri_w)
        self.ei, self.ej, self.w = W.row, W.col, W.data
        self.E = self.P[self.ei] - self.P[self.ej]                  # rest edge vectors (directed, both ways)
        L = sp.coo_matrix((self.w, (self.ei, self.ej)), shape=(self.n, self.n)).tocsr()
        L = sp.diags(np.asarray(L.sum(1)).ravel()) - L
        self.handles = {k: np.asarray(v, int) for k, v in handles.items()}
        con = np.concatenate(list(self.handles.values())) if self.handles else np.zeros(0, int)
        self.con = con
        free = np.ones(self.n, bool); free[con] = False
        self.free = np.where(free)[0]
        L = L.tocsc()
        self.L_FF = L[self.free][:, self.free].tocsc()
        self.L_FC = L[self.free][:, con].tocsc()
        self.lu = spl.splu(self.L_FF)

    def flipped(self, X):
        a, b, c = X[self.T[:, 0]], X[self.T[:, 1]], X[self.T[:, 2]]
        sgn = (b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0]
        return np.where(sgn <= 0)[0]

    def solve_repair(self, targets, iters=8, X0=None, rounds=10, factor=3.0, cap=400.0, decay=0.93):
        """Solve; if triangles turn over, stiffen them and their one-ring (rigidity x factor, capped) and solve
        again. Stiffening relaxes back toward 1 frame by frame (x decay), so the repair map follows the pose."""
        if (self.stiff > 1).any():
            self.stiff = np.maximum(1.0, self.stiff * decay)
            self.stiff[self.stiff < 1.05] = 1.0
            self.tri_w = self.tri_w0 * self.stiff
            self._build()
        X = self.solve(targets, iters=iters, X0=X0)
        for _ in range(rounds):
            bad = self.flipped(X)
            if len(bad) == 0:
                break
            vs = np.unique(self.T[bad])
            ring = np.where(np.isin(self.T, vs).any(1))[0]
            self.stiff[ring] = np.minimum(cap, self.stiff[ring] * factor)
            self.tri_w = self.tri_w0 * self.stiff
            self.repairs += 1
            self._build()
            X = self.solve(targets, iters=max(iters, 25), X0=X)
        # last resort, a flip guard: free vertices of any triangle still turned over move toward their one-ring mean
        if not hasattr(self, 'nbr'):
            import scipy.sparse as sp
            A = sp.coo_matrix((np.ones(len(self.ei)), (self.ei, self.ej)), shape=(self.n, self.n)).tocsr()
            A.data[:] = 1.0
            self.nbr = sp.diags(1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A
            self.isfree = np.ones(self.n, bool); self.isfree[self.con] = False
        for _ in range(30):
            bad = self.flipped(X)
            if len(bad) == 0:
                break
            vs = np.unique(self.T[bad]); vs = vs[self.isfree[vs]]
            if len(vs) == 0:
                break
            X[vs] = 0.5 * X[vs] + 0.5 * (self.nbr @ X)[vs]
            self.guarded = getattr(self, 'guarded', 0) + 1
        self.X = X
        return X

    def rotations(self, X):
        Ed = X[self.ei] - X[self.ej]
        S = np.zeros((self.n, 2, 2))
        wE = self.E * self.w[:, None]
        np.add.at(S, self.ei, wE[:, :, None] * Ed[:, None, :])
        th = np.arctan2(S[:, 0, 1] - S[:, 1, 0], S[:, 0, 0] + S[:, 1, 1])
        return th

    def solve(self, targets, iters=8, X0=None):
        """targets: dict handle name -> (k,2) positions for its vertices (same order). Returns X (n,2)."""
        X = self.X if X0 is None else np.asarray(X0, float).copy()
        XC = np.concatenate([np.asarray(targets[k], float) for k in self.handles]) if self.handles else np.zeros((0, 2))
        X[self.con] = XC
        rhs_c = self.L_FC @ XC
        for _ in range(iters):
            th = self.rotations(X)
            c, s = np.cos(th), np.sin(th)
            # b_i = sum_j w_ij/2 (R_i + R_j)(p_i - p_j)
            ci = c[self.ei] + c[self.ej]; si = s[self.ei] + s[self.ej]
            e = self.E
            r = np.stack([ci * e[:, 0] - si * e[:, 1], si * e[:, 0] + ci * e[:, 1]], 1) * (0.5 * self.w)[:, None]
            b = np.zeros((self.n, 2))
            np.add.at(b, self.ei, r)
            bf = b[self.free] - rhs_c
            X[self.free, 0] = self.lu.solve(bf[:, 0])
            X[self.free, 1] = self.lu.solve(bf[:, 1])
        self.X = X
        self.theta = th
        return X

    def energy(self, X=None):
        X = self.X if X is None else X
        th = self.rotations(X)
        c, s = np.cos(th), np.sin(th)
        e = self.E
        Re = np.stack([c[self.ei] * e[:, 0] - s[self.ei] * e[:, 1], s[self.ei] * e[:, 0] + c[self.ei] * e[:, 1]], 1)
        d = (X[self.ei] - X[self.ej]) - Re
        return float((self.w * (d * d).sum(1)).sum() / (self.w * (e * e).sum(1)).sum())

    def inverted(self, X=None):
        X = self.X if X is None else X
        a, b, c = X[self.T[:, 0]], X[self.T[:, 1]], X[self.T[:, 2]]
        sgn = (b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0]
        return int((sgn <= 0).sum())


def rigid_targets(P, idx, center_rest, center_new, angle, scale=1.0):
    """Place a handle's vertices by a rotation about its rest centre and a move to its new centre."""
    c, s = np.cos(angle), np.sin(angle)
    d = (P[idx] - center_rest) * scale
    return np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]], 1) + center_new
