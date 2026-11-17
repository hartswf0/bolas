"""Repair r1 fixture (#45 occlusion, #40 physical): checks EVERY exposure of shots 5
and 7, not only the settled view.
 (1) geometry: the paper never goes below the table (z >= 0) and never passes through
     itself (no two non-adjacent segments of the cross-section cross);
 (2) pixels: in every exposure where F0 is the top layer at every X it covers (landing,
     settle, flat), every pixel inside F0's projected footprint (eroded 1 px) shows F0
     in the facet-ID buffer; fail on any connected region > 4 output px that does not.
Imported by render_shots.run(); also runnable alone over the saved fold-events."""
import numpy as np, cv2


def _segs_cross(P, Q, R, S):
    def orient(a, b, c):
        return np.sign((b[..., 0] - a[..., 0]) * (c[..., 1] - a[..., 1]) - (b[..., 1] - a[..., 1]) * (c[..., 0] - a[..., 0]))
    return (orient(P, Q, R) * orient(P, Q, S) < 0) & (orient(R, S, P) * orient(R, S, Q) < 0)


def geometry_ok(cs, step=2):
    X, z = cs["X"][::step], cs["z"][::step]
    pts = np.stack([X, z], 1)
    a, b = pts[:-1], pts[1:]
    n = len(a)
    hits = 0
    for i in range(0, n, 64):
        A_, B_ = a[i:i + 64, None], b[i:i + 64, None]
        c = _segs_cross(A_, B_, a[None], b[None])
        ii = np.arange(i, min(n, i + 64))[:, None]; jj = np.arange(n)[None]
        c &= np.abs(ii - jj) > 2
        hits += int(c.sum())
    return dict(z_min=float(cs["z"].min()), self_crossings=hits // 2, ok=bool(cs["z"].min() >= -1e-9 and hits == 0))


def f0_on_top(cs, A):
    u, X, z = cs["u"], cs["X"], cs["z"]
    f0 = u < A - cs["La"] / 2
    bins = np.round(X / 4).astype(int)
    top_other = {}
    for bb, zz in zip(bins[~f0], z[~f0]):
        top_other[bb] = max(top_other.get(bb, -1e9), zz)
    return all(zz >= top_other.get(bb, -1e9) - 1e-6 for bb, zz in zip(bins[f0], z[f0]))


def pixel_check(rend, ss):
    ids, foot = rend.last_ids, rend.last_foot.get(0)
    if foot is None:
        return dict(checked=False)
    k = np.ones((2 * ss + 1, 2 * ss + 1), np.uint8)
    core = cv2.erode(foot.astype(np.uint8), k) > 0
    bad = (core & (ids != 0)).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bad, 8)
    big = [int(s[cv2.CC_STAT_AREA]) for s in stats[1:] if s[cv2.CC_STAT_AREA] > 4 * ss * ss]
    return dict(checked=True, footprint_px=int(core.sum()), wrong_px=int(bad.sum()), regions_over_4px=len(big), ok=len(big) == 0)
