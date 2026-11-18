"""strip/fold.py - pure fold geometry for 'Les caids de la gaudriole' (sheet rev 1).

No rendering, no I/O except reading strip/sheet.json. Units are sheet units u
(1 u = 0.1 mm). Conventions:

  sheet coords   u in [0, W] along the strip, y in [0, H] down the strip.
  table coords   X along the table, Y = y, z up. The part u >= M (F2, F3) never
                 moves: X = u, z = 0. The pleat lifts F0 and F1 over it.
  folded coords  x' = X - D. The settled packet's top view is V(x').

Crease angles: alpha = rotation at the valley M (0 flat .. pi folded),
               beta  = rotation at the mountain A (0 flat .. pi folded).
Each crease is a circular curl band of length L (default 40 u while moving,
1.6 u when pressed flat, so the pressed pleat is ~ 1 u thick per layer, the
thickness of paper). Bands are exact circular arcs, so at alpha = beta = pi the
facets map exactly to x -> 2A - x (F1) and x -> x - D (F0 -> its folded place),
i.e. the reflections about A and then about the image of M (plan.md 4).

Public API
  S                         frozen constants from sheet.json
  facet_of(u)               'F0' | 'F1' | 'F2' | 'F3'
  map_settled(u)            (x', face, depth) of sheet column u after the pleat
  cross_section(alpha, beta, La=40, Lm=40, lag=(0, 0), du=0.5)
                            arrays u, X, z, phi, nz (front-normal z), facet id
  facet_poses(alpha, beta, La, Lm, lag)
                            3D pose of each planar facet + the crease axes
  layer_order(cs)           occlusion DAG: list of (front facet, behind facet)
  top_view_index(cs, X)     for each table column X: visible u, face (+1 front / -1 back), z
  folded_view(sheet)        V(x') as an array (H x (W - D))
  lightbox_stack(sheet)     dict of layer arrays in x' and their masks, depth order
  ghost_position(x0, x1)    where a sheet x-range appears in the light box (and mirrored?)
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_sheet = json.load(open(os.path.join(HERE, "sheet.json")))


class S:
    W, H = _sheet["W"], _sheet["H"]
    A, M, B, D = _sheet["A"], _sheet["M"], _sheet["B"], _sheet["D"]
    TAU = _sheet["tau_u"]
    P1 = tuple(_sheet["panels"]["P1"]["x"]); P2 = tuple(_sheet["panels"]["P2"]["x"])
    PY = tuple(_sheet["panels"]["P1"]["y"])
    LINE_Y = _sheet["LINE_Y"]; CAP = _sheet["cap_u"]
    WF = W - D                                   # folded strip width in x'


A, M, B, D, W, H = S.A, S.M, S.B, S.D, S.W, S.H
assert B == 2 * M - A and D == B - A and 2 * A - M > 0


def facet_of(u):
    if u < A: return "F0"
    if u < M: return "F1"
    if u < B: return "F2"
    return "F3"


def map_settled(u):
    """Sheet column u -> (x', face, depth layer) in the settled pleat."""
    f = facet_of(u)
    if f == "F0": return u, +1, 1
    if f == "F1": return 2 * A - u, -1, 2
    return u - D, +1, 3


# ------------------------------------------------------------------ cross-section
def cross_section(alpha, beta, La=40.0, Lm=40.0, lag=(0.0, 0.0), du=0.5):
    """Integrate the paper's centre line from u = W down to u = 0.

    Curvature is piecewise constant: -alpha/Lm in the M band, +beta/La in the A
    band, an optional slight bend 'lag' = (k0, k1) total radians spread over F0
    (free edge trailing the unseen hand) and F1, else 0. Arcs are integrated
    exactly, so the result is independent of du on the flats."""
    k0, k1 = lag
    bands = [  # (u_hi, u_lo, total turn)
        (W, M + Lm / 2, 0.0),
        (M + Lm / 2, M - Lm / 2, -alpha),
        (M - Lm / 2, A + La / 2, k1),
        (A + La / 2, A - La / 2, beta),
        (A - La / 2, 0.0, k0),
    ]
    us, Xs, zs, ps = [float(W)], [float(W)], [0.0], [math.pi]
    X, z, ph = float(W), 0.0, math.pi
    for hi, lo, turn in bands:
        L = hi - lo
        if L <= 0: continue
        n = max(1, int(math.ceil(L / du)))
        kap = turn / L
        for i in range(1, n + 1):
            s = L / n
            if abs(kap) < 1e-12:
                X += math.cos(ph) * s; z += math.sin(ph) * s
            else:
                ph2 = ph + kap * s
                X += (math.sin(ph2) - math.sin(ph)) / kap
                z += (math.cos(ph) - math.cos(ph2)) / kap
                ph = ph2
            us.append(hi - i * s); Xs.append(X); zs.append(z); ps.append(ph)
    u = np.array(us); ph = np.array(ps)
    nz = -np.cos(ph)                     # front normal = (sin phi, -cos phi): +1 face up
    fid = np.array([facet_of(v) for v in u])
    return dict(u=u, X=np.array(Xs), z=np.array(zs), phi=ph, nz=nz, facet=fid,
                alpha=alpha, beta=beta, La=La, Lm=Lm)


def facet_poses(alpha, beta, La=40.0, Lm=40.0, lag=(0.0, 0.0)):
    """Rigid pose of each planar facet (rotation about the Y axis).
    Returns {facet: {u_range, origin (X,z) at its high-u end, phi (travel heading),
    face (+1 up/-1 down), rot_y_deg}}, plus the two crease axes (lines parallel to Y)."""
    cs = cross_section(alpha, beta, La, Lm, lag)
    u, X, z, ph = cs["u"], cs["X"], cs["z"], cs["phi"]
    def at(uq):
        i = int(np.argmin(np.abs(u - uq)))
        return float(X[i]), float(z[i]), float(ph[i])
    out = {}
    for f, (hi, lo) in {"F3": (W, B), "F2": (B, M + Lm / 2), "F1": (M - Lm / 2, A + La / 2), "F0": (A - La / 2, 0)}.items():
        x0, z0, p0 = at(hi)
        out[f] = dict(u_range=[lo, hi], origin=[x0, z0], phi=p0, face=1 if -math.cos(p0) >= 0 else -1,
                      rot_y_deg=math.degrees(math.pi - p0))
    xm, zm, _ = at(M); xa, za, _ = at(A)
    out["crease_M"] = dict(X=xm, z=zm, kind="valley", angle=alpha)
    out["crease_A"] = dict(X=xa, z=za, kind="mountain", angle=beta)
    return out


def top_view_index(cs, Xq=None, exclude_bands=False, tol=0.03):
    """Orthographic top view. Pixel column X covers [X, X+1); it shows the highest
    paper sample within tol of its centre X + 0.5. Returns X, u (sheet coordinate
    of that sample, nan where no paper), face (+1 front, -1 back), z, and
    in_band (True where a crease curl is the top surface).
    exclude_bands drops the curl-band samples (the rolled fold edge) first."""
    u, X, z, nz = cs["u"], cs["X"], cs["z"], cs["nz"]
    band = (np.abs(u - A) < cs["La"] / 2) | (np.abs(u - M) < cs["Lm"] / 2)
    keep = ~band if exclude_bands else np.ones_like(band)
    if Xq is None: Xq = np.arange(0, W)
    Xq = np.asarray(Xq)
    uv = np.full(len(Xq), np.nan); fv = np.zeros(len(Xq)); zv = np.full(len(Xq), -1e9); bv = np.zeros(len(Xq), bool)
    idx = np.nonzero(keep)[0]
    Xs, zs = X[idx], z[idx]
    order = np.argsort(Xs)
    Xs, zs, idx = Xs[order], zs[order], idx[order]
    for j, xc in enumerate(Xq + 0.5):
        lo, hi = np.searchsorted(Xs, xc - tol), np.searchsorted(Xs, xc + tol)
        if hi <= lo: continue
        k = idx[lo + int(np.argmax(zs[lo:hi]))]
        uv[j] = u[k]; fv[j] = 1 if nz[k] >= 0 else -1; zv[j] = z[k]; bv[j] = band[k]
    return dict(X=Xq, u=uv, face=fv, z=zv, in_band=bv)


def layer_order(cs):
    """Occlusion DAG between facets from their heights over shared table columns.
    Returns sorted list of (front, behind) facet pairs."""
    u, X, z, fid = cs["u"], cs["X"], cs["z"], cs["facet"]
    cols = {}
    for x, zz, f in zip(np.round(X).astype(int), z, fid):
        cols.setdefault(x, {}).setdefault(f, []).append(zz)
    edges = set()
    for d in cols.values():
        fs = [(np.mean(v), f) for f, v in d.items()]
        fs.sort(reverse=True)
        for a in range(len(fs)):
            for b in range(a + 1, len(fs)):
                if fs[a][0] - fs[b][0] > 1e-6:
                    edges.add((str(fs[a][1]), str(fs[b][1])))
    return sorted(edges)


# ------------------------------------------------------------------ settled views
def folded_view(sheet):
    """V(x') = Sheet(x') for x' < A, Sheet(x' + D) for x' >= A; width W - D."""
    sheet = np.asarray(sheet)
    out = np.empty((sheet.shape[0], S.WF) + sheet.shape[2:], sheet.dtype)
    out[:, :A] = sheet[:, :A]
    out[:, A:] = sheet[:, A + D:A + D + (S.WF - A)]
    return out


def lightbox_stack(sheet):
    """Layers over the folded strip, top (1) to bottom (3), in x' coordinates.
    Each layer: ink-bearing sheet columns resampled to x' (face-down layers come out
    mirrored automatically), and a mask of where that layer has paper.
      layer1 = F0       : u = x'        (x' in [0, A))     face up
      layer2 = F1       : u = 2A - x'   (x' in [2A-M, A])  face down -> mirrored
      layer3 = F2 + F3  : u = x' + D    (x' in [2A-M, WF)) face up
    """
    sheet = np.asarray(sheet)
    xp = np.arange(S.WF)
    m1 = xp < A
    m2 = (xp >= 2 * A - M) & (xp < A)
    m3 = xp >= 2 * A - M
    def take(uidx, mask):
        out = np.full((sheet.shape[0], S.WF) + sheet.shape[2:], 255, sheet.dtype)
        out[:, mask] = sheet[:, np.clip(uidx[mask], 0, W - 1)]
        return out
    L1 = take(xp, m1)
    L2 = take(2 * A - xp, m2)
    L3 = take(xp + D, m3)
    nlayers = m1.astype(int) + m2 + m3
    return dict(layers=[L1, L2, L3], masks=[m1, m2, m3], n=nlayers,
                maps=["u = x'", "u = 2A - x' (face down, mirrored)", "u = x' + D"])


def ghost_position(x0, x1):
    """Where sheet range [x0, x1] shows in folded/light-box coords."""
    f = facet_of((x0 + x1) / 2)
    if f == "F0": return dict(layer=1, x=[x0, x1], mirrored=False, visible=True)
    if f == "F1": return dict(layer=2, x=[2 * A - x1, 2 * A - x0], mirrored=True, visible=False)
    if f == "F2": return dict(layer=3, x=[x0 - D, x1 - D], mirrored=False, visible=False)
    return dict(layer=3, x=[x0 - D, x1 - D], mirrored=False, visible=True)


if __name__ == "__main__":
    for a, b in [(0, 0), (math.pi / 2, math.pi / 3), (math.pi, math.pi)]:
        cs = cross_section(a, b, 40 if a < math.pi else 1.6, 40 if a < math.pi else 1.6)
        print(round(a, 2), round(b, 2), layer_order(cs))
    fp = facet_poses(math.pi, math.pi, 1.6, 1.6)
    print({k: (v.get("origin"), v.get("face")) for k, v in fp.items()})
