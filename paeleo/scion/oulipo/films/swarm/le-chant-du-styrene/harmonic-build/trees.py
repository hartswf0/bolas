"""U4 harmonic trees -> granule (Sh4 27.60-35.00 s, Sh5 pellet layer 35.00-38.00 s).

Handmade: translucent runner trees built from the four-arm vocabulary of geometry.json,
rendered as a thickness field (stamped spheres along each strand -> rod thickness 2*sqrt(r^2-d^2)),
coloured by Beer-Lambert transmission of a warm backlight; Whitney oscillator bank; Foldes-style
per-frame metamorphosis (whole -> beads at a fixed pitch -> cut -> pellets = the cut pieces ->
harmonic orbits returning at the measured alignment -> release and fall).

All times are film seconds. Band 960x408. No grain (the editor applies the shared grain).
"""
import json, math
from pathlib import Path
import numpy as np
import cv2

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
GEOM = json.loads((ROOT / "films/swarm/le-chant-du-styrene/geometry.json").read_text())
W, H = 960, 408
FPS = 24
T_IN, T_OUT = 27.60, 35.00
T_ALIGN = 33.60
P = T_ALIGN - T_IN            # 6.0 s: the bank's common period; all phases are zero at T_IN and T_ALIGN
OMEGA = 2 * math.pi / P       # base angular frequency, rad/s
T_META = 31.00                # metamorphosis starts
BEAD_DUR = 1.35               # whole -> fully beaded (necks at 0.10 r) -> cut
G_FALL = 1400.0               # px/s^2 (front plane)

# ---------------------------------------------------------------- vocabulary from geometry.json
def _vocab():
    rings = GEOM["rings"]
    hub = np.array(GEOM["hub_src"])
    ang = {r["ring"]: r["arm_angle_deg_src"] for r in rings}        # 181, 297, 9, 105
    up = ang[2]                                                       # 297: the arm that becomes the trunk
    def rel(a):
        d = (a - up + 180) % 360 - 180
        return d
    side = sorted([rel(ang[1]), rel(ang[3])])                          # -116, +72
    trunk_kink = 180 - abs(rel(ang[4]))                               # 105 vs 297 -> 12 deg kink per node
    widths = {r["ring"]: float(np.mean(r["arm_width_src"])) for r in rings}
    wmax = max(widths.values())
    lens = {r["ring"]: float(np.linalg.norm(np.array(r["gate_src"]) - hub)) for r in rings}
    Rr = {r["ring"]: r["outer_R_src"] for r in rings}
    bore = {r["ring"]: r["inner_r_src"] / r["outer_R_src"] for r in rings}
    return dict(side=side, kink=trunk_kink, width_classes=sorted([w / wmax for w in widths.values()], reverse=True),
                disc_to_arm=float(np.mean([Rr[k] / lens[k] for k in Rr])), bore_ratio=float(np.mean(list(bore.values()))),
                raw=dict(arm_angles=ang, widths=widths, arm_lengths=lens, ring_R=Rr))
VOCAB = _vocab()
ANG_COMPRESS = 0.5     # declared: measured side-arm angles (-116, +72 deg from the trunk arm) halved -> -58, +36 deg

# ---------------------------------------------------------------- noise helpers
def smooth_noise(rng, n, scale):
    k = max(2, int(n / scale) + 2)
    v = rng.normal(0, 1, k)
    x = np.linspace(0, k - 1.001, n)
    i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f)
    return v[i] * (1 - f) + v[i + 1] * f

# ---------------------------------------------------------------- tree construction
class Tree:
    def __init__(self, idx, base_x, height, n_harm, w_dye, opal, scale=1.0, plane="front", seed=0,
                 stagger=0.0, base_y=H + 36, discs=(), mirror=False, dye="amber"):
        self.idx, self.n, self.w, self.opal, self.s, self.plane = idx, n_harm, w_dye, opal, scale, plane
        self.stagger = stagger
        self.dye = dye
        self.absv = ABS_RED if dye == "red" else ABS
        self.eps = float(np.random.default_rng(seed + 999).choice([-1, 1]) * (0.03 + 0.05 * np.random.default_rng(seed + 7).random()))
        rng = np.random.default_rng(seed)
        self.rng = rng
        s = scale
        wc = VOCAB["width_classes"]
        r_trunk = 8.8 * s * (0.85 + 0.35 * rng.random())
        K = 5 if height * s > 250 else 4
        self.K = K
        # trunk nodes (rest), with the measured 12 deg kink alternating
        nodes = [np.array([base_x, base_y], float)]
        seg = height * s / (K + 0.6)
        heading = -90.0 + rng.normal(0, 3)
        for k in range(K + 1):
            heading += (VOCAB["kink"] * 0.5) * (1 if (k % 2) else -1) * 0.5 + rng.normal(0, 1.5)
            L = seg * (1.25 if k == 0 else (0.95 - 0.06 * k)) * (0.9 + 0.2 * rng.random())
            nodes.append(nodes[-1] + L * np.array([math.cos(math.radians(heading)), math.sin(math.radians(heading))]))
        self.nodes = np.array(nodes)       # node 0 below the frame, nodes 1..K+1
        self.strands = []                  # dict(level, rot_gain, pts(N,2) rest, r(N,), closed)
        self.webs = []                     # dict(level, rot_gain, c rest(2,), R, t, bore)
        # trunk: one strand per segment, levels 0..K
        for k in range(K + 1):
            a, b = self.nodes[k], self.nodes[k + 1]
            rr = r_trunk * wc[0] * (1 - 0.13 * k)
            self._add_line(k, 0.0, a, b, rr, rr * 0.92)
        # crown: a V fork at the top (reference trees end in a V)
        top = self.nodes[K + 1]; tdir = self.nodes[K + 1] - self.nodes[K]; th0 = math.degrees(math.atan2(tdir[1], tdir[0]))
        for d in (-28, 24):
            L = 26 * s * (0.8 + 0.4 * rng.random())
            e = top + L * np.array([math.cos(math.radians(th0 + d)), math.sin(math.radians(th0 + d))])
            self._add_line(K + 1, 1.0, top, e, r_trunk * wc[2] * 0.75, r_trunk * wc[3] * 0.5)
        # side branches at nodes 1..K
        disc_set = set(discs)
        for k in range(1, K + 1):
            p = self.nodes[k]
            tdir = self.nodes[k + 1] - self.nodes[k]; th0 = math.degrees(math.atan2(tdir[1], tdir[0]))
            sides = [a * ANG_COMPRESS for a in VOCAB["side"]]
            if (k + mirror) % 2: sides = [-sides[1], -sides[0]]
            for j, d in enumerate(sides):
                d = d + rng.normal(0, 5)
                L = (88 - 9 * k) * s * (0.8 + 0.45 * rng.random())
                e = p + L * np.array([math.cos(math.radians(th0 + d)), math.sin(math.radians(th0 + d))])
                rb = r_trunk * wc[1 + j] * (0.82 - 0.05 * k)
                key = (k, j)
                if key in disc_set:
                    R = max(20 * s, L * VOCAB["disc_to_arm"] * 1.1) * (0.9 + 0.2 * rng.random())
                    u = (e - p) / np.linalg.norm(e - p)
                    gate = e - u * 0.0
                    # gate: the runner necks to 0.55 r just before the disc (a real gate)
                    self._add_line(k, 1.0, p, gate, rb, rb * 0.8, gate_neck=True)
                    self._add_disc(k, 1.0, gate + u * R, R, rb)
                else:
                    self._add_line(k, 1.0, p, e, rb, rb * 0.6)
                    # small twig fork at the tip
                    if rng.random() < 0.5:
                        bd = th0 + d
                        for dd in ((-26, 22) if j == 0 else (24, -20))[: 1 + (rng.random() < 0.5)]:
                            Lt = 20 * s * (0.7 + 0.6 * rng.random())
                            mid = p + (e - p) * (0.62 + 0.2 * rng.random())
                            et = mid + Lt * np.array([math.cos(math.radians(bd + dd)), math.sin(math.radians(bd + dd))])
                            self._add_line(k, 1.0, mid, et, rb * 0.62, rb * 0.42)
        self._make_pellets()

    def _add_line(self, level, gain, a, b, r0, r1, gate_neck=False):
        L = float(np.linalg.norm(b - a)); n = max(3, int(L / 1.2))
        u = np.linspace(0, 1, n)
        pts = a[None] + (b - a)[None] * u[:, None]
        r = r0 + (r1 - r0) * u
        r = r * (1 + 0.07 * smooth_noise(self.rng, n, 14 / self.s))       # moulding irregularity
        if gate_neck:
            r = r * (1 - 0.45 * np.clip((u - 0.86) / 0.1, 0, 1))
        self.strands.append(dict(level=level, gain=gain, pts=pts, r=r, closed=False, ds=L / (n - 1)))

    def _add_disc(self, level, gain, c, R, rb):
        n = max(24, int(2 * math.pi * R / 1.2))
        ph = np.linspace(0, 2 * math.pi, n, endpoint=False)
        Rr = R * (1 + 0.035 * smooth_noise(self.rng, n, 9))                # uneven moulded rim
        pts = c[None] + np.stack([np.cos(ph) * Rr, np.sin(ph) * Rr], 1)
        r = np.full(n, max(2.6, 0.55 * rb)) * (1 + 0.12 * smooth_noise(self.rng, n, 7))
        self.strands.append(dict(level=level, gain=gain, pts=pts, r=r, closed=True, ds=2 * math.pi * R / n))
        self.webs.append(dict(level=level, gain=gain, c=c, R=R * 0.97, t=1.25 * rb * 2 * (1.9 if self.dye == "red" else 1.0), bore=R * VOCAB["bore_ratio"] * 1.4,
                              phase=self.rng.random() * 6.28))

    # ---------------------------------------------------------- pellets: the beads, cut at a fixed pitch
    PITCH = 13.0

    def _make_pellets(self):
        rng = self.rng
        pitch = self.PITCH * self.s
        self.pellets = []
        for si, st in enumerate(self.strands):
            n = len(st["pts"]); ds = st["ds"]
            sarr = np.arange(n) * ds
            Ltot = sarr[-1] + (ds if st["closed"] else 0)
            s0 = rng.random() * pitch
            st["s"] = sarr; st["s0"] = s0; st["pitch"] = pitch
            cs = np.arange(s0, Ltot, pitch)
            if not st["closed"] and len(cs) == 0: cs = np.array([Ltot / 2])
            for c in cs:
                if st["closed"]:
                    dist = (sarr - c + Ltot / 2) % Ltot - Ltot / 2
                else:
                    dist = sarr - c
                sel = np.where(np.abs(dist) <= pitch / 2)[0]
                if len(sel) < 2: continue
                m = int(rng.choice([1, 2, 3], p=[0.45, 0.35, 0.2])) * (1 if rng.random() < 0.5 else -1)
                self.pellets.append(dict(
                    strand=si, idx=sel, dist=dist[sel], centre_i=int(sel[np.argmin(np.abs(dist[sel]))]),
                    m=m, psi=rng.random() * 2 * math.pi, R=float(np.clip(rng.lognormal(math.log(22), 0.45), 7, 55)) * self.s,
                    jit_t=rng.normal(0, 0.28) * pitch, jit_n=rng.normal(0, 2.2) * self.s,
                    spin=rng.normal(0, 70), fall_delay=float(rng.random() ** 1.3 * 0.78), vx=rng.normal(0, 25) * self.s))

    # ---------------------------------------------------------- the oscillator bank
    def theta(self, k, t, detune=0.0):
        """branch level k swings at k*omega_i: theta = A_k(t) sin(k * n_i * OMEGA * (t - T_IN))"""
        if k <= 0: return 0.0
        tau = t - T_IN
        A = math.radians(7.0) / (k ** 0.5)
        env = min(1.0, max(0.0, tau / 1.2)) ** 2 * (3 - 2 * min(1.0, max(0.0, tau / 1.2)))
        return A * env * math.sin(k * self.n * (1 + detune * self.eps) * OMEGA * tau)

    def pose(self, t, detune=0.0):
        """forward kinematics: rotation at node k = Phi_k (trunk, 0.3*theta cumulative) + gain*theta_k"""
        K = self.K
        th = [self.theta(k, t, detune) for k in range(K + 2)]
        Phi = np.cumsum([0.3 * x for x in th])
        posed = [self.nodes[0].copy()]
        for k in range(K + 1):
            c, s_ = math.cos(Phi[k]), math.sin(Phi[k])
            d = self.nodes[k + 1] - self.nodes[k]
            posed.append(posed[-1] + np.array([c * d[0] - s_ * d[1], s_ * d[0] + c * d[1]]))
        return th, Phi, np.array(posed)

    def strand_pts(self, st, th, Phi, posed):
        k = st["level"]; a = Phi[k] + st["gain"] * th[k]
        c, s_ = math.cos(a), math.sin(a)
        d = st["pts"] - self.nodes[k]
        return posed[k][None] + np.stack([c * d[:, 0] - s_ * d[:, 1], s_ * d[:, 0] + c * d[:, 1]], 1), a

    def beta(self, t):
        a = T_META + self.stagger; b = a + BEAD_DUR
        x = min(1.0, max(0.0, (t - a) / (b - a)))
        return x * x * (3 - 2 * x)

    def t_cut(self):
        return T_META + self.stagger + BEAD_DUR


def bead_mult(st, beta):
    c = np.cos(2 * math.pi * (st["s"] - st["s0"]) / st["pitch"])
    g = 0.10 + 1.18 * ((1 + c) / 2) ** 0.8
    return (1 - beta) + beta * g


# ---------------------------------------------------------------- stamping (thickness, lens, coverage)
_kc = {}
def kernel(r, fx, fy):
    key = (round(r * 4) / 4, fx, fy)
    if key not in _kc:
        rq = max(0.35, key[0]); R = int(math.ceil(rq)) + 1
        y, x = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
        d2 = (x - fx) ** 2 + (y - fy) ** 2
        th = 2 * np.sqrt(np.clip(rq * rq - d2, 0, None))
        nr = np.sqrt(np.clip(1 - d2 / (rq * rq), 0, None))
        cv = np.clip(rq - np.sqrt(d2) + 0.5, 0, 1)
        _kc[key] = (R, th, nr, cv)
    return _kc[key]

def stamp(th, nr, cv, xs, ys, rs):
    Hh, Ww = th.shape
    for x, y, r in zip(xs, ys, rs):
        if r < 0.3: continue
        ix, iy = int(math.floor(x)), int(math.floor(y))
        fx, fy = round((x - ix) * 3) / 3, round((y - iy) * 3) / 3
        R, kt, kn, kv = kernel(r, fx, fy)
        x0, y0 = ix - R, iy - R; x1, y1 = ix + R + 1, iy + R + 1
        if x1 <= 0 or y1 <= 0 or x0 >= Ww or y0 >= Hh: continue
        ax0, ay0 = max(0, -x0), max(0, -y0); ax1 = kt.shape[1] - max(0, x1 - Ww); ay1 = kt.shape[0] - max(0, y1 - Hh)
        sl = (slice(max(0, y0), min(Hh, y1)), slice(max(0, x0), min(Ww, x1)))
        ks = (slice(ay0, ay1), slice(ax0, ax1))
        np.maximum(th[sl], kt[ks], out=th[sl]); np.maximum(nr[sl], kn[ks], out=nr[sl]); np.maximum(cv[sl], kv[ks], out=cv[sl])

def stamp_web(th, nr, cv, c, R, t, bore, phase):
    Hh, Ww = th.shape
    x0, x1 = int(max(0, c[0] - R - 2)), int(min(Ww, c[0] + R + 3)); y0, y1 = int(max(0, c[1] - R - 2)), int(min(Hh, c[1] + R + 3))
    if x1 <= x0 or y1 <= y0 or t <= 0.05: return
    y, x = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.hypot(x - c[0], y - c[1]); a = np.arctan2(y - c[1], x - c[0])
    Re = R * (1 + 0.02 * np.sin(3 * a + phase) + 0.015 * np.sin(7 * a + 2 * phase))
    cov = np.clip(Re - d + 0.5, 0, 1) * np.clip(d - bore + 0.5, 0, 1)
    tw = t * (1 + 0.25 * (d / R) ** 2) * cov            # slightly thicker toward the rim (moulded dish)
    sl = (slice(y0, y1), slice(x0, x1))
    np.maximum(th[sl], tw, out=th[sl]); np.maximum(nr[sl], 0.75 * cov, out=nr[sl]); np.maximum(cv[sl], cov, out=cv[sl])


# ---------------------------------------------------------------- light
LIGHT = np.array([1.0, 0.86, 0.60], np.float32)        # warm backlight under the plastic
ABS = np.array([0.10, 0.50, 2.00], np.float32)         # amber dye: absorbs blue most, red least (per unit dye x px / 10)
ABS_RED = np.array([0.11, 0.95, 1.00], np.float32)     # crimson dye: absorbs green most, passes some blue (the reference reds are crimson, B ~ G)
def shade(th, nr, cv, w, opal, gain=1.0, absv=None):
    absv = ABS if absv is None else absv
    od = (w * (th + 4.0 * cv) / 10.0)[..., None]
    T = np.exp(-absv[None, None] * od)
    lens = (0.10 + 0.90 * nr ** 1.1)[..., None]
    E = gain * 1.02 * LIGHT * T * lens
    # small surface scatter (milky / opal), dyed
    E += (0.05 + 0.25 * opal) * gain * (nr[..., None] ** 1.5) * np.array([0.42, 0.14, 0.10], np.float32) * (cv[..., None] > 0)
    # rim speculars from the thickness gradient, light from upper left
    gy, gx = np.gradient(cv * nr)
    spec = np.clip(-(gx * -0.62 + gy * -0.78), 0, None)
    spec = (spec * cv) ** 3 * (nr < 0.9)
    E += 0.55 * gain * np.clip(spec, 0, 0.6)[..., None] * np.array([1.0, 0.86, 0.62], np.float32)
    Tbg = T * (1 - opal) * 0.85
    return E, Tbg

def composite(img, th, nr, cv, w, opal, gain=1.0, blur=0.0, absv=None):
    if blur > 0:
        th = cv2.GaussianBlur(th, (0, 0), blur); nr = cv2.GaussianBlur(nr, (0, 0), blur); cv = cv2.GaussianBlur(cv, (0, 0), blur)
    E, Tbg = shade(th, nr, cv, w, opal, gain, absv)
    c = cv[..., None]
    img *= (1 - c + c * Tbg)
    img += c * E


# ---------------------------------------------------------------- the forest
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def practicals(t):
    """two defocused blue practicals on their own plane (0.3x parallax): a soft disc (upper right) and a bar (left)"""
    dx = -0.3 * camx(t)
    disc = np.exp(-(((xx - (792 + dx)) ** 2 + (yy - (96)) ** 2) / (2 * 58 ** 2)) ** 2.2)
    bar = np.exp(-((np.clip(np.abs(xx - (250 + dx)) - 150, 0, None) / 30) ** 2 + ((yy - 128) / 15) ** 2) ** 1.6)
    c1 = np.array([0.025, 0.14, 0.36], np.float32); c2 = np.array([0.05, 0.15, 0.36], np.float32)
    return (0.98 * disc[..., None] * c1 + 0.90 * bar[..., None] * c2).astype(np.float32)

def camx(t):
    x = min(1.0, max(0.0, (t - T_IN) / (T_OUT - T_IN)))
    return 30.0 * (x * x * (3 - 2 * x))            # a slow lateral glide to the right (content moves left)

# front plane: 6 trees; back plane: 5 trees at 0.5x
FRONT = [
    dict(base_x=78,  height=352, n_harm=2, w_dye=2.3, opal=0.15, seed=11, dye="red", stagger=0.00, discs=((2, 1),)),
    dict(base_x=238, height=390, n_harm=3, w_dye=0.40, opal=0.05, seed=12, stagger=0.30, discs=((3, 0), (1, 1)), mirror=True),
    dict(base_x=400, height=330, n_harm=2, w_dye=1.30, opal=0.40, seed=13, stagger=0.12, discs=()),
    dict(base_x=560, height=372, n_harm=1, w_dye=0.85, opal=0.10, seed=14, stagger=0.42, discs=((2, 0),)),
    dict(base_x=716, height=360, n_harm=3, w_dye=2.6, opal=0.10, seed=15, dye="red", stagger=0.20, discs=((1, 0), (3, 1)), mirror=True),
    dict(base_x=878, height=384, n_harm=2, w_dye=0.42, opal=0.05, seed=16, stagger=0.34, discs=((2, 1),)),
]
BACK = [
    dict(base_x=150, height=520, n_harm=1, w_dye=2.0, opal=0.2, seed=21, dye="red", stagger=0.50, discs=((2, 0),)),
    dict(base_x=330, height=560, n_harm=2, w_dye=0.4, opal=0.1, seed=22, stagger=0.62, discs=()),
    dict(base_x=500, height=500, n_harm=1, w_dye=2.4, opal=0.1, seed=23, dye="red", stagger=0.55, discs=((1, 1),)),
    dict(base_x=650, height=540, n_harm=2, w_dye=0.5, opal=0.1, seed=24, stagger=0.70, discs=((3, 0),)),
    dict(base_x=820, height=520, n_harm=1, w_dye=2.2, opal=0.2, seed=25, dye="red", stagger=0.58, discs=()),
]
def build():
    fr = [Tree(i, plane="front", **d) for i, d in enumerate(FRONT)]
    bk = [Tree(10 + i, plane="back", scale=0.5, base_y=H + 18, **d) for i, d in enumerate(BACK)]
    return fr, bk
FRONT_T, BACK_T = build()
# draw order within the front plane (2 sub-depths so trees overlap): back sub-depth first
FRONT_ORDER = [2, 0, 4, 1, 3, 5]


def pellet_disp(p, tree, t, detune=0.0):
    """orbit displacement d(t) = R*env*[cos(m*w*tau + psi) - cos psi, sin(m*w*tau + psi) - sin psi];
    zero at tau = 0 and tau = P (the alignment) when locked."""
    tc = tree.t_cut(); tau = t - T_IN
    e = min(1.0, max(0.0, (t - tc) / 0.35)); e = e * e * (3 - 2 * e)
    w = tree.n * (1 + detune * tree.eps) * OMEGA
    ph = p["m"] * w * tau + p["psi"]
    return p["R"] * e * np.array([math.cos(ph) - math.cos(p["psi"]), math.sin(ph) - math.sin(p["psi"])]), e


def render_tree(tree, t, detune=0.0, xoff=0.0, plane_size=(H, W)):
    th = np.zeros(plane_size, np.float32); nr = np.zeros_like(th); cv = np.zeros_like(th)
    ths, Phi, posed = tree.pose(t, detune)
    beta = tree.beta(t)
    tc = tree.t_cut()
    pts_all = []
    for st in tree.strands:
        pts, ang = tree.strand_pts(st, ths, Phi, posed)
        pts_all.append(pts)
    if t < tc:
        for st, pts in zip(tree.strands, pts_all):
            r = st["r"] * bead_mult(st, beta)
            stamp(th, nr, cv, pts[:, 0] + xoff, pts[:, 1], r)
        for wb in tree.webs:
            k = wb["level"]; a = Phi[k] + wb["gain"] * ths[k]
            d = wb["c"] - tree.nodes[k]; c, s_ = math.cos(a), math.sin(a)
            cc = posed[k] + np.array([c * d[0] - s_ * d[1], s_ * d[0] + c * d[1]])
            stamp_web(th, nr, cv, cc + np.array([xoff, 0]), wb["R"], wb["t"] * (1 - beta) ** 1.5, wb["bore"], wb["phase"])
        return th, nr, cv, 0
    # after the cut: every pellet is its own piece of strand, moved rigidly
    n_vis = 0
    g = G_FALL * tree.s
    for p in tree.pellets:
        st = tree.strands[p["strand"]]; pts = pts_all[p["strand"]]
        r = st["r"][p["idx"]] * bead_mult(st, 1.0)[p["idx"]]
        r = r * np.clip((st["pitch"] / 2 - np.abs(p["dist"])) / (0.18 * st["pitch"]), 0, 1) ** 0.5   # the broken necks close up
        loc = pts[p["idx"]]; ctr = pts[p["centre_i"]]
        i0 = max(0, p["centre_i"] - 1); i1 = min(len(pts) - 1, p["centre_i"] + 1)
        tg = pts[i1] - pts[i0]; tg = tg / (np.linalg.norm(tg) + 1e-6); nm = np.array([-tg[1], tg[0]])
        d, e = pellet_disp(p, tree, t, detune)
        home = ctr + e * (p["jit_t"] * tg + p["jit_n"] * nm)               # spacing jitter: no two pellets keep the strand's spacing
        tau = t - T_IN
        spin = math.radians(p["spin"]) * e * math.sin(p["m"] * tree.n * (1 + detune * tree.eps) * OMEGA * tau)
        pos = home + d
        tf = t - (T_ALIGN + p["fall_delay"])
        if tf > 0:                                                           # release: fall
            pos = pos + np.array([p["vx"] * tf, 0.5 * g * tf * tf])
            spin += math.radians(p["spin"] * 3) * tf
        rel = loc - ctr
        c, s_ = math.cos(spin), math.sin(spin)
        q = pos[None] + np.stack([c * rel[:, 0] - s_ * rel[:, 1], s_ * rel[:, 0] + c * rel[:, 1]], 1)
        if q[:, 1].min() > plane_size[0] + 10: continue
        n_vis += 1
        stamp(th, nr, cv, q[:, 0] + xoff, q[:, 1], r)
    return th, nr, cv, n_vis


def halation_rolloff(img):
    """identical to the cutout unit's unify step (render.py): one mild halation, one highlight roll-off"""
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = img * np.clip((lum - 0.45) / 0.3, 0, 1)[..., None]
    img = img + 0.22 * cv2.GaussianBlur(hot, (0, 0), 5) + 0.10 * cv2.GaussianBlur(hot, (0, 0), 16)
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    k = 0.66; tgt = np.where(lum > k, k + 0.15 * np.tanh((lum - k) / 0.15), lum)
    return np.clip(img * (tgt / np.maximum(lum, 1e-4))[..., None], 0, 1)


def frame(t, detune=0.0):
    img = practicals(t)
    cx = camx(t)
    for tr in BACK_T:                                   # back plane, 0.5x parallax, defocused, dimmer
        th, nr, cv, _ = render_tree(tr, t, detune, xoff=-0.5 * cx)
        composite(img, th, nr, cv, tr.w, tr.opal, gain=0.62, blur=3.2, absv=tr.absv)
    vis = 0
    for i in FRONT_ORDER:
        tr = FRONT_T[i]
        th, nr, cv, nv = render_tree(tr, t, detune, xoff=-cx)
        vis += nv
        composite(img, th, nr, cv, tr.w, tr.opal, gain=1.0, blur=0.45, absv=tr.absv)
    return halation_rolloff(img), vis
