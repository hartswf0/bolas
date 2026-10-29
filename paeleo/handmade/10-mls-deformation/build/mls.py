"""SCION-10 · Moving Least Squares image deformation (Schaefer, McPhail & Warren 2006), written here in numpy.

Typed primitives
  P : (M,2) control points in the SOURCE sheet (metres of the painted hide, u forward, v lateral)
  Q : (M,k) their targets (k=2 for a plane warp, k=3 for the lifted sheet: x, y on the porch floor and z height)
  m : (M,)  handle mass (1 for a point; a line-segment handle is a run of quadrature points whose masses sum to its length/h)
  V : (N,2) points of the sheet to deform

  w_i(v) = m_i / |p_i - v|^(2 alpha)

Three families, as in the paper:
  affine      f(v) = (v - p*) (sum w p^T p)^-1 (sum w p^T q) + q*                (any k)
  similarity  f(v) = sum q_i (1/mu_s) A_i + q*                                   (k = 2)
  rigid       f(v) = |v - p*| fr(v)/|fr(v)| + q*,   fr(v) = sum q_i A_i          (k = 2)
  with A_i = w_i [p_i ; -p_i_perp] [v - p* ; -(v - p*)_perp]^T, hats = centred on the weighted centroids.

Line-segment handles: the paper integrates the weight along each segment in closed form. Here a segment is sampled with
n Gauss-Legendre points whose masses carry the segment length, a quadrature of the same integral (stated in method.md)."""
import numpy as np

EPS = 1e-9


def segment_handles(a, b, qa, qb, n=4, mass=1.0):
    """quadrature points for a line-segment handle a->b (source) mapped to qa->qb (target)."""
    x, wq = np.polynomial.legendre.leggauss(n)
    s = (x + 1) / 2
    a, b, qa, qb = map(np.asarray, (a, b, qa, qb))
    P = a[None] + s[:, None] * (b - a)[None]
    Q = qa[None] + s[:, None] * (qb - qa)[None]
    return P, Q, mass * wq / 2 * n


def _weights(V, P, m, alpha):
    d2 = ((V[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    return m[None] / np.maximum(d2, EPS) ** alpha


def deform(V, P, Q, m=None, alpha=1.0, family='affine', chunk=20000):
    V = np.asarray(V, float); P = np.asarray(P, float); Q = np.asarray(Q, float)
    m = np.ones(len(P)) if m is None else np.asarray(m, float)
    out = np.empty((len(V), Q.shape[1]))
    for s in range(0, len(V), chunk):
        out[s:s + chunk] = _deform(V[s:s + chunk], P, Q, m, alpha, family)
    return out


def _deform(V, P, Q, m, alpha, family):
    W = _weights(V, P, m, alpha)                       # N,M
    sw = W.sum(1, keepdims=True)
    ps = W @ P / sw; qs = W @ Q / sw                   # N,2 / N,k
    ph = P[None] - ps[:, None]                         # N,M,2
    qh = Q[None] - qs[:, None]                         # N,M,k
    vd = V - ps                                        # N,2
    if family == 'affine':
        A = np.einsum('nm,nmi,nmj->nij', W, ph, ph)
        B = np.einsum('nm,nmi,nmj->nij', W, ph, qh)
        A[:, 0, 0] += 1e-12; A[:, 1, 1] += 1e-12
        return np.einsum('ni,nij->nj', vd, np.linalg.solve(A, B)) + qs
    assert Q.shape[1] == 2, 'similarity and rigid MLS are plane warps'
    # A_i = w [ph ; -ph_perp][vd ; -vd_perp]^T ; ph_perp = (-y, x)
    a0 = ph; a1 = np.stack([ph[..., 1], -ph[..., 0]], -1)          # -ph_perp
    b0 = vd; b1 = np.stack([vd[:, 1], -vd[:, 0]], -1)              # -vd_perp
    # A rows: r0 = a0, r1 = a1 ; A = R1 R2^T -> A[j,l] = sum_c R1[j,c] R2[l,c]
    A00 = (a0 * b0[:, None]).sum(-1); A01 = (a0 * b1[:, None]).sum(-1)
    A10 = (a1 * b0[:, None]).sum(-1); A11 = (a1 * b1[:, None]).sum(-1)
    fx = (W * (qh[..., 0] * A00 + qh[..., 1] * A10)).sum(1)
    fy = (W * (qh[..., 0] * A01 + qh[..., 1] * A11)).sum(1)
    fr = np.stack([fx, fy], -1)
    if family == 'similarity':
        mu = (W * (ph ** 2).sum(-1)).sum(1, keepdims=True)
        return fr / mu + qs
    if family == 'rigid':
        n = np.linalg.norm(fr, axis=1, keepdims=True)
        return np.linalg.norm(vd, axis=1, keepdims=True) * fr / np.maximum(n, EPS) + qs
    raise ValueError(family)


def selftest():
    """numerical invariants (measured): handles hit targets; identity is reproduced; a rigid motion is reproduced exactly."""
    rng = np.random.default_rng(10)
    P = rng.uniform(-1, 1, (12, 2)); V = rng.uniform(-1, 1, (500, 2))
    res = {}
    th = 0.7; R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]]); T = np.array([0.3, -0.2])
    Qr = P @ R + T
    Qx = P + rng.normal(0, 0.15, P.shape)
    for fam in ('affine', 'similarity', 'rigid'):
        e_id = np.abs(deform(V, P, P, family=fam) - V).max()
        e_rig = np.abs(deform(V, P, Qr, family=fam) - (V @ R + T)).max()
        e_hit = np.abs(deform(P + 1e-7, P, Qx, family=fam) - Qx).max()
        res[fam] = {'identity_err': float(e_id), 'rigid_motion_err': float(e_rig), 'handle_hit_err': float(e_hit)}
    Q3 = np.c_[Qx, rng.uniform(0, 1, len(P))]
    res['affine_2to3_handle_hit_err'] = float(np.abs(deform(P + 1e-7, P, Q3) - Q3).max())
    res['ok'] = all(v < 1e-4 for f in ('affine', 'similarity', 'rigid') for v in res[f].values()) and res['affine_2to3_handle_hit_err'] < 1e-4
    return res


if __name__ == '__main__':
    import json
    print(json.dumps(selftest(), indent=1))
