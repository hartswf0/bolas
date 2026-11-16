"""Editor repair of Sh4 (27.60-35.00) and the Sh5 pellet layer (35.00-38.00): MELT TREES -> PELLETS.

Critic round 1: the solid runner-trees breaking into grain read as REGRIND (an unverified hypothesis kept off
screen), and the trees read as flat fills. Repair, built on U4's trees.py (same geometry.json vocabulary, same
Whitney bank, same seeds) with these changes:

0. The melt rises into each tree from below the frame edge (a fill front with a rounded meniscus, as in Sh3b).
1. The trees are MELT, not runners: the same lit-through melt as Sh3b (warm source through Beer-Lambert
   thickness), with grazing-path saturation at the edges (optical path x (1 + 1.8 (1 - n)) -> darker, deeper
   at the rim), a bright lensing core, internal bloom confined to the material, rim speculars, and a liquid
   surface: varicose waves travel up every strand and the radius never sits still.
2. The beading is the Plateau-Rayleigh break-up of a liquid thread (varicose growth at a fixed pitch), and each
   drop then FREEZES while it flies: its colour goes from lit-through melt to the opaque orange granule of the
   real heap (Granuls orange.jpg, which closes the film), lit by a key from upper left. Read backward (the tour's
   direction), the pellets are what the melt came from: melt <- pellets.
3. No reunion into chains: after the cut each pellet travels its own harmonic path to a scattered rest
   position. All phases lock at 33.60 s (the chord): every pellet is at rest at once, separated, then falls.
   d(t) = R e(t) [cos psi', sin psi'],  psi' = psi + 0.6 sgn(m) (1 - cos(m n_i Omega tau)),  e = smoothstep(tcut, 33.6).
"""
import sys, math, json
from pathlib import Path
import numpy as np, cv2
HB = Path(__file__).resolve().parent.parent / "harmonic-build"
sys.path.insert(0, str(HB))
import trees as T
import render as RU          # U4's Sh5 drop code, reused with the solid shader

OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/editor-repair")
RU.OUT = OUT                 # heap is read from OUT.parent / "cutout/..."

# solid pellet colour: the mean lit colour of the real heap's granules (measured, linear 0..1)
_heap = cv2.imread(str(OUT.parent / "cutout/sh5/heap_rgba_960x408.png"), cv2.IMREAD_UNCHANGED)
_hm = _heap[..., 3] > 200
_hc = _heap[..., :3][..., ::-1][_hm].astype(np.float32) / 255
_lum = _hc @ np.array([0.299, 0.587, 0.114])
PELLET = _hc[_lum > np.percentile(_lum, 93)].mean(0).astype(np.float32)   # the lit faces of the real granules

LIGHT = np.array([1.05, 0.80, 0.42], np.float32)       # the Sh3b melt source, seen through the melt


def shade_melt(th, nr, cv, w, absv, t, phase=0.0):
    od = (w * (th * (1 + 2.5 * (1 - nr)) + 3.0 * cv) / 10.0 + 0.9 * (1 - nr) ** 2 * cv)[..., None]   # grazing rays travel further: rim deep red
    Tm = np.exp(-absv[None, None] * od)
    lens = (0.04 + 0.80 * nr ** 2.2)[..., None]                           # lensing core, kept below the roll-off knee
    E = LIGHT * Tm * lens
    # the backlight focused by the rod: a bright streak displaced toward the key side (upper left)
    M = np.float32([[1, 0, 1.6], [0, 1, 1.6]])
    nsh = cv2.warpAffine(nr, M, (nr.shape[1], nr.shape[0]))
    streak = (np.clip(nsh, 0, 1) ** 8 * np.clip(nr, 0, 1))[..., None]
    E = E + 0.55 * streak * (LIGHT * 0.6 + 0.4) * Tm ** 0.35
    gy, gx = np.gradient(cv * nr)
    spec = np.clip(-(gx * -0.62 + gy * -0.78), 0, None)
    spec = (spec * cv) ** 2.5 * (nr < 0.92)
    E = E + 0.7 * np.clip(spec, 0, 0.6)[..., None] * np.array([1.0, 0.85, 0.6], np.float32)
    return E, Tm


def shade_solid(th, nr, cv, w, absv):
    """a frozen granule: mostly opaque orange, key from upper left, thin translucent rim"""
    gy, gx = np.gradient(cv2.GaussianBlur(nr, (0, 0), 0.8))
    nz = np.sqrt(np.clip(1 - (gx ** 2 + gy ** 2) * 4, 0.05, 1))
    lam = np.clip((-gx * 2 * -0.55 + -gy * 2 * -0.45 + nz * 0.70), 0, 1)
    E = PELLET[None, None] * (0.22 + 0.85 * lam)[..., None] * cv[..., None]
    spec = np.clip(lam - 0.86, 0, None) / 0.14
    E = E + 0.35 * (spec ** 3)[..., None] * np.array([1.0, 0.9, 0.75], np.float32)
    return E


def composite_v2(img, th, nr, cv, solid, tr, gain, blur, t):
    if blur > 0:
        th = cv2.GaussianBlur(th, (0, 0), blur); nr = cv2.GaussianBlur(nr, (0, 0), blur)
        cv = cv2.GaussianBlur(cv, (0, 0), blur); solid = cv2.GaussianBlur(solid, (0, 0), blur)
    Em, Tm = shade_melt(th, nr, cv, tr.w, tr.absv, t)
    # bloom inside the material only (light scattered in the melt), not a halo around it
    Em = Em + 0.45 * cv2.GaussianBlur(Em, (0, 0), 3.0) * cv[..., None]
    Es = shade_solid(th, nr, cv, tr.w, tr.absv)
    s = np.clip(solid, 0, 1)[..., None]
    c = cv[..., None]
    E = gain * (Em * (1 - s) + Es * s)
    trans = Tm * (1 - tr.opal) * 0.8 * (1 - s)
    img *= (1 - c + c * trans)
    img += c * E


def liquid(st, t, s):
    """varicose surface waves travelling up the strand (the melt is never still)"""
    ss = st["s"]
    ph = st.setdefault("lph", (hash(id(st)) % 997) / 997 * 6.283)
    return 1 + 0.17 * np.sin(2 * math.pi * (ss / (34 * s)) + 2 * math.pi * 1.1 * t + ph) \
             + 0.06 * np.sin(2 * math.pi * (ss / (13 * s)) - 2 * math.pi * 0.7 * t + 2 * ph)


def solid_of(tr, p, t):
    """freezing: 0 = melt, 1 = solid granule. A drop starts to freeze at the cut and is solid by 33.45 s."""
    a = tr.t_cut() + 0.05 + 0.25 * (p["fall_delay"] if p is not None else 0)
    b = 33.45
    x = min(1.0, max(0.0, (t - a) / max(b - a, 0.1)))
    return x * x * (3 - 2 * x)


def disp(p, tr, t):
    tc = tr.t_cut(); tau = t - T.T_IN
    x = min(1.0, max(0.0, (t - tc) / (T.T_ALIGN - tc)))
    e = x * x * (3 - 2 * x)
    m = p["m"]
    psi = p["psi"] + 0.6 * math.copysign(1, m) * (1 - math.cos(abs(m) * tr.n * T.OMEGA * tau))
    R = p["R"] * 1.35 + 6 * tr.s
    return R * e * np.array([math.cos(psi), math.sin(psi)]), e


def render_tree(tree, t, xoff=0.0):
    H, W = T.H, T.W
    th = np.zeros((H, W), np.float32); nr = np.zeros_like(th); cv = np.zeros_like(th); so = np.zeros_like(th)
    ths, Phi, posed = tree.pose(t)
    beta = tree.beta(t)
    tc = tree.t_cut()
    pts_all = [tree.strand_pts(st, ths, Phi, posed)[0] for st in tree.strands]
    if t < tc:
        # the melt rises into the tree from below (fill front at height hF, rounded meniscus), 27.60-28.95 s
        x = min(1.0, max(0.0, (t - T.T_IN) / 1.35)); hF = 40 + 560 * (1 - (1 - x) ** 2)
        base = tree.nodes[0][1]
        for st, pts in zip(tree.strands, pts_all):
            if st["closed"]:                       # a disc rim fills as one piece once the front reaches its centre
                fill = float(np.clip((hF - (base - st["pts"][:, 1].mean())) / (20 * tree.s), 0, 1)) ** 0.5
            else:
                fill = np.clip((hF - (base - st["pts"][:, 1])) / (14 * tree.s), 0, 1) ** 0.5
            r = st["r"] * T.bead_mult(st, beta) * liquid(st, t, tree.s) ** (1 - beta) * fill
            T.stamp(th, nr, cv, pts[:, 0] + xoff, pts[:, 1], r)
        for wb in tree.webs:
            if hF < base - wb["c"][1]:
                continue
            k = wb["level"]; a = Phi[k] + wb["gain"] * ths[k]
            d = wb["c"] - tree.nodes[k]; c, s_ = math.cos(a), math.sin(a)
            cc = posed[k] + np.array([c * d[0] - s_ * d[1], s_ * d[0] + c * d[1]])
            T.stamp_web(th, nr, cv, cc + np.array([xoff, 0]), wb["R"], wb["t"] * (1 - beta) ** 1.5, wb["bore"], wb["phase"] + 2.0 * t)
        return th, nr, cv, so
    g = T.G_FALL * tree.s
    for p in tree.pellets:
        st = tree.strands[p["strand"]]; pts = pts_all[p["strand"]]
        r = st["r"][p["idx"]] * T.bead_mult(st, 1.0)[p["idx"]]
        r = r * np.clip((st["pitch"] / 2 - np.abs(p["dist"])) / (0.18 * st["pitch"]), 0, 1) ** 0.5
        sol = solid_of(tree, p, t)
        # a liquid drop pulls itself round; as it freezes it keeps the short-cylinder shape it froze in
        loc = pts[p["idx"]]; ctr = pts[p["centre_i"]]
        i0 = max(0, p["centre_i"] - 1); i1 = min(len(pts) - 1, p["centre_i"] + 1)
        tg = pts[i1] - pts[i0]; tg = tg / (np.linalg.norm(tg) + 1e-6); nm = np.array([-tg[1], tg[0]])
        d, e = disp(p, tree, t)
        home = ctr + e * (p["jit_t"] * tg + p["jit_n"] * nm)
        tau = t - T.T_IN
        spin = math.radians(p["spin"]) * 2.0 * e * (1 - math.cos(abs(p["m"]) * tree.n * T.OMEGA * tau))
        pos = home + d
        tf = t - (T.T_ALIGN + p["fall_delay"])
        if tf > 0:
            pos = pos + np.array([p["vx"] * tf, 0.5 * g * tf * tf])
            spin += math.radians(p["spin"] * 3) * tf
        rel = (loc - ctr) * (1 - 0.25 * (1 - sol))      # melt drop slightly rounder
        c, s_ = math.cos(spin), math.sin(spin)
        q = pos[None] + np.stack([c * rel[:, 0] - s_ * rel[:, 1], s_ * rel[:, 0] + c * rel[:, 1]], 1)
        if q[:, 1].min() > H + 10:
            continue
        cv0 = cv.copy()
        T.stamp(th, nr, cv, q[:, 0] + xoff, q[:, 1], r * (1 + 0.12 * (1 - sol)))
        np.maximum(so, (cv > cv0) * sol, out=so)
    return th, nr, cv, so


def frame(t):
    img = T.practicals(t)
    cx = T.camx(t)
    for tr in T.BACK_T:
        th, nr, cv, so = render_tree(tr, t, xoff=-0.5 * cx)
        composite_v2(img, th, nr, cv, so, tr, gain=0.75, blur=2.6, t=t)
    for i in T.FRONT_ORDER:
        tr = T.FRONT_T[i]
        th, nr, cv, so = render_tree(tr, t, xoff=-cx)
        composite_v2(img, th, nr, cv, so, tr, gain=1.0, blur=0.45, t=t)
    return T.halation_rolloff(img)


def positions(tr, t):
    ths, Phi, posed = tr.pose(t)
    out = []
    for p in tr.pellets:
        st = tr.strands[p["strand"]]; pts, _ = tr.strand_pts(st, ths, Phi, posed)
        ctr = pts[p["centre_i"]]
        d, e = disp(p, tr, t)
        out.append((p["strand"], ctr + d, d))
    return out


def worms():
    res = {}
    for t in (32.9, 33.2, 33.45, 33.6, 34.0):
        together = pairs = 0; gaps = []
        for tr in T.FRONT_T:
            if t < tr.t_cut() + 0.3: continue
            ps = positions(tr, t)
            for a, b in zip(ps[:-1], ps[1:]):
                if a[0] != b[0]: continue
                pairs += 1
                if np.linalg.norm(a[2] - b[2]) < 4.0: together += 1
                gaps.append(np.linalg.norm(a[1] - b[1]))
        g = np.array(gaps)
        res[f"{t:.2f}"] = dict(adjacent_pairs=pairs, fraction_travelling_together=round(together / max(pairs, 1), 3),
                               gap_mean_px=round(float(g.mean()), 1), gap_cv=round(float(g.std() / g.mean()), 3))
    return res


def sh5():
    """U4's Sh5 drop code, with the pellets drawn frozen (solid shader) and a soft contact shadow on the heap"""
    def shade(th, nr, cv, w, opal, gain=1.0, absv=None):
        E = shade_solid(th, nr, cv, w, absv)
        return E / np.maximum(cv[..., None], 1e-3) * (cv[..., None] > 1e-3), np.zeros_like(E)
    T.shade = shade
    RU.sh5()


def u8(im):
    return (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    w = sys.argv[1]
    if w == "sh4":
        wk, nw = int(sys.argv[2]), int(sys.argv[3])
        d = OUT / "sh4"; d.mkdir(parents=True, exist_ok=True)
        for f in range(663 + wk, 840, nw):
            cv2.imwrite(str(d / f"f{f:04d}.png"), cv2.cvtColor(u8(frame(f / 24.0)), cv2.COLOR_RGB2BGR))
    elif w == "still":
        for t in sys.argv[2:]:
            cv2.imwrite(f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/sh4_{t}.png",
                        cv2.cvtColor(u8(frame(float(t))), cv2.COLOR_RGB2BGR))
    elif w == "worms":
        r = worms(); print(json.dumps(r, indent=1))
        (Path(__file__).resolve().parent / "sh4v2_worms.json").write_text(json.dumps(r, indent=1))
    elif w == "sh5":
        sh5()
