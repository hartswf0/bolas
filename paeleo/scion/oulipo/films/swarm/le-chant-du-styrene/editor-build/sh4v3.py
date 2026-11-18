"""Editor repair round 2 of Sh4 (27.60-35.00): PHOTOGRAPHED-ROD TREES that melt into drops that freeze into pellets.

Critic round 2: the drawn, emissive trees (sh4v2 / U4 trees.py) read as a glowing vector illustration beside
styreneA.webp. Repair (the critic's 'better still' route), with the reviewer's disc note applied:

FORAGED pixels: every rod in every tree is a piece of the real photographed runner 'Spritzguss teile.jpg'
  (Gmhofmann, CC BY-SA 4.0), the same GrabCut cutout (SCION #29) used in Sh1-Sh2 (cutout unit's
  pieces/bare_runner.png). Each of the runner's four arms is straightened along its measured arm polyline
  from geometry.json (SCION #8: one constraint graph) into a strip that keeps the photo's own shading,
  gloss catches, mould lines and edge irregularities; tree segments are cut from those strips
  (Gilliam/Reiniger-style cutout: articulated pieces, each joint a pivot).
DECLARED colour substitution: the teal photo is re-lit through the cutout unit's own thickness gel
  (cutout-build/gel.py, unchanged): thin wall factor -> amber, thick -> deep red; core darker than the edge.
NO ring discs: the trees carry no finished-part shapes (reviewer round 2).
HANDMADE motion: Whitney harmonic bank (SCION #6, U4's formula): branch angle at level k of tree i,
  theta = A_k sin(k n_i Omega (t - 27.6)), Omega = 2 pi / 6 s, A_k = 7 deg / sqrt(k): every phase is zero
  together at 33.60 s (the chord). From 32.05 s each rod piece (irregular lengths 0.8-2.3 rod widths, so there
  is no even bead pitch) softens: its ends round, it shortens and swells (a drop pulling itself round), at its
  own random time; each piece is released between 32.45 and 32.85 s, travels its own harmonic orbit, freezes
  to the opaque orange of the real heap's granules (Granuls orange.jpg, measured), is at rest at 33.60 s, and
  falls. Read in the tour's direction (backward): pellets -> melt -> tree.
"""
import sys, math, json
from pathlib import Path
import numpy as np, cv2

HERE = Path(__file__).resolve().parent
SW = HERE.parent
sys.path.insert(0, str(SW / "cutout-build"))
sys.path.insert(0, str(SW / "harmonic-build"))
from gel import gel                     # the cutout unit's declared gel, unchanged
import trees as T                       # U4: practicals(), camx(), halation_rolloff(), constants

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene")
CUT = SRC / "cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-"
OUT = SRC / "editor-repair2"
GEO = json.load(open(SW / "geometry.json"))
BB = json.load(open(CUT / "geom_src.json"))["report"]["pieces"]["bare_runner"]["bbox_src"]
H, W = 408, 960
T_IN, T_ALIGN, OMEGA = 27.60, 33.60, 2 * math.pi / 6.0
G_FALL = 1400.0

# ------------------------------------------------------------- rod strips ---
_piece = cv2.imread(str(CUT / "pieces/bare_runner.png"), cv2.IMREAD_UNCHANGED)     # BGRA, real photo + GrabCut alpha


def strip(poly_src, half, t0=0.16, t1=0.90, n=None):
    """straighten one arm of the photographed runner along its measured polyline -> BGRA strip (along x)"""
    poly = np.array(poly_src, float) - np.array(BB[:2], float)
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    n = n or int((t1 - t0) * L[-1])
    s = np.linspace(t0 * L[-1], t1 * L[-1], n)
    px = np.interp(s, L, poly[:, 0]); py = np.interp(s, L, poly[:, 1])
    tx = np.gradient(px); ty = np.gradient(py); nrm = np.hypot(tx, ty); tx /= nrm; ty /= nrm
    nx, ny = -ty, tx
    v = np.arange(-half, half + 1, dtype=np.float32)
    mx = (px[None, :] + v[:, None] * nx[None, :]).astype(np.float32)
    my = (py[None, :] + v[:, None] * ny[None, :]).astype(np.float32)
    return cv2.remap(_piece, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


# arms 0 (left), 1 (up), 3 (down) are the clean wide arms; arm 2 (right) is thin
RAW = [strip(GEO["rings"][k]["arm_polyline_src"], 15) for k in (0, 1, 3)]
DYES = {"amber": 0.22, "orange": 0.50, "red": 1.35}
TINT = {"amber": [1.08, 0.80, 0.26], "orange": [1.0, 0.82, 0.55], "red": [1.0, 1.0, 1.0]}   # declared amber/orange dye on the gel          # gel wall factors (cutout unit: runner 0.42, rings 1.3)
STRIPS = {d: [gel(s, wall=w, edge_dark=0.45) for s in RAW] for d, w in DYES.items()}   # premultiplied RGBA, RGB order
for d in STRIPS:                                             # rod core is the thickest path: deepen it a little
    for i, s in enumerate(STRIPS[d]):
        h = s.shape[0]; u = np.abs(np.arange(h) - (h - 1) / 2) / ((h - 1) / 2)
        core = (0.72 + 0.28 * u ** 1.5)[:, None, None]
        STRIPS[d][i] = np.dstack([s[..., :3] * core, s[..., 3:]]).astype(np.float32)
for d in STRIPS:
    for i, s in enumerate(STRIPS[d]):
        rgb = s[..., :3] * np.array(TINT[d], np.float32)
        rgb[..., 1] = np.minimum(rgb[..., 1], rgb[..., 0]); rgb[..., 2] = np.minimum(rgb[..., 2], rgb[..., 1])   # no cool fringe from the teal original
        STRIPS[d][i] = np.dstack([rgb, s[..., 3:]]).astype(np.float32)
ROD_W = [float((s[..., 3].max(1) > 0.5).sum()) for s in STRIPS["amber"]]   # measured rod width of each strip (px)

_heap = cv2.imread(str(CUT / "sh5/heap_rgba_960x408.png"), cv2.IMREAD_UNCHANGED)
_hm = _heap[..., 3] > 200
_hc = _heap[..., :3][..., ::-1][_hm].astype(np.float32) / 255
_hl = _hc @ np.array([0.299, 0.587, 0.114])
PELLET = _hc[_hl > np.percentile(_hl, 93)].mean(0).astype(np.float32)      # lit faces of the real granules


def smooth(a, b, x):
    x = min(1.0, max(0.0, (x - a) / (b - a))); return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ trees ---
FRONT = [  # base_x, height, n (harmonic number), dye, seed, mirror
    (70, 360, 2, "red", 11, False), (232, 392, 3, "amber", 12, True), (392, 336, 2, "orange", 13, False),
    (556, 376, 1, "amber", 14, False), (712, 362, 3, "red", 15, True), (876, 388, 2, "amber", 16, False)]
BACK = [(150, 300, 1, "red", 21, False), (470, 280, 2, "amber", 22, True), (630, 310, 1, "red", 23, False),
        (800, 290, 2, "orange", 24, True), (312, 260, 1, "amber", 25, False)]


class Tree:
    def __init__(self, base_x, height, n, dye, seed, mirror, scale=1.0):
        r = np.random.RandomState(seed)
        self.n, self.dye, self.scale, self.r = n, dye, scale, r
        sg = -1 if mirror else 1
        self.base = np.array([base_x, H + 26.0 * scale])
        tw = 17.0 * scale
        height = height * 0.84
        # segments: (parent index, attach fraction on parent, rest angle from vertical (deg), length, width, level)
        segs = [(-1, 0.0, sg * r.uniform(-3, 3), height * 0.56, tw, 0)]
        segs.append((0, 1.0, segs[0][2] + sg * 12.0, height * 0.46, tw * 0.92, 0))        # the 12 deg trunk kink
        lv = 1
        for frac, par in ((0.30, 0), (0.70, 0), (0.18, 1), (0.55, 1)):
            L = height * (0.34 - 0.05 * lv) * r.uniform(0.85, 1.1)
            for side, base_ang in ((-1, 58.0), (1, 36.0)):                              # measured -116/+72 halved
                a = segs[par][2] + sg * side * (base_ang + r.uniform(-6, 6))
                if not (lv == 1 and side == 1 and r.rand() < 0.3):
                    segs.append((par, frac + r.uniform(-0.03, 0.03), a, L, tw * 0.74, lv))
                    k = len(segs) - 1
                    if r.rand() < 0.65:                                                    # a twig fork near the tip
                        segs.append((k, r.uniform(0.55, 0.75), a + side * sg * r.uniform(24, 34), L * 0.42, tw * 0.58, lv))
            lv += 1
        segs.append((1, 1.0, segs[1][2] - sg * 24, height * 0.13, tw * 0.62, 4))          # top Y fork
        segs.append((1, 1.0, segs[1][2] + sg * 22, height * 0.15, tw * 0.62, 4))
        self.segs = segs
        # cut every segment into pieces of irregular length; each piece maps a contiguous run of one strip
        self.pieces = []
        for si, (_, _, _, L, w, lv) in enumerate(segs):
            st = r.randint(3)
            sl = STRIPS[dye][st].shape[1]
            k_src = ROD_W[st] / w / 1.8                  # strip px per dest px along (declared 1.8x stretch along the rod)
            pos, u = 0.0, r.uniform(0, sl * 0.3)
            while pos < L - 1:
                pl = min(w * r.uniform(0.8, 2.3), L - pos)
                ul = pl * k_src
                if u + ul > sl - 1:
                    u = r.uniform(0, max(1, sl - ul - 1))
                self.pieces.append(dict(
                    seg=si, s0=pos, s1=pos + pl, strip=st, u0=u, u1=u + ul, w=w,
                    melt_d=r.uniform(0.0, 0.30), rel=32.45 + r.uniform(0, 0.40),
                    R=r.uniform(8, 34) * scale, psi=r.uniform(0, 2 * math.pi), m=int(r.choice([-3, -2, -1, 1, 2, 3])),
                    spin=r.uniform(-90, 90), fall=r.uniform(0.0, 0.55), vx=r.uniform(-40, 40) * scale))
                u += ul; pos += pl

    def pose(self, t):
        """forward kinematics with the Whitney bank: every angle is at rest together at 27.6 and 33.6 s"""
        tau = t - T_IN
        env = smooth(27.6, 28.6, t)
        out = []
        for si, (par, frac, a0, L, w, lv) in enumerate(self.segs):
            k = lv + 1
            th = (7.0 / math.sqrt(k)) * env * math.sin(k * self.n * OMEGA * tau)
            if par < 0:
                p0 = self.base.copy(); ang = a0 + 0.35 * th
            else:
                pp0, pd, pL, pang = out[par]
                p0 = pp0 + pd * pL * frac; ang = pang + (a0 - self.segs[par][2]) + th
            ar = math.radians(ang)
            d = np.array([math.sin(ar), -math.cos(ar)])
            out.append((p0, d, L, ang))
        return out


def draw_piece(img, src, cen, d, L, w, alpha_cap, mult=1.0, solid=0.0):
    """affine-paste one strip piece (premultiplied RGBA) onto img, centred at cen, along unit vector d"""
    sh, sl = src.shape[:2]
    if sl < 2:
        return
    sx, sy = L / sl, w / ROD_W_CUR[0]
    # capsule mask in dest units (rounded ends as the drop pulls round)
    xs = (np.arange(sl) + 0.5) * sx; ys = (np.arange(sh) - (sh - 1) / 2) * sy
    re = alpha_cap * w / 2
    if re > 0.3:
        ex = np.clip(np.minimum(xs - re, L - re - xs), None, 0)
        dist = np.hypot(ex[None, :], ys[:, None])
        cap = np.clip((w / 2 - dist) / 1.0 + 0.5, 0, 1).astype(np.float32)
        src = src * cap[..., None]
    if solid > 0:                      # freezing: from lit-through to the opaque orange granule, key from upper left
        a = src[..., 3:]
        lum = (src[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
        shade = np.clip(lum / np.maximum(a, 1e-3) / 0.45, 0.2, 1.4)
        top = np.linspace(1.15, 0.6, sh, dtype=np.float32)[:, None, None]
        sol = PELLET[None, None] * shade * top * a
        src = np.dstack([src[..., :3] * (1 - solid) + sol * solid, a])
    src = src * np.float32(mult)
    ux, uy = d
    nx, ny = -uy, ux
    # src (x along, y across, centred) -> dest
    M = np.array([[ux * sx, nx * sy, 0.0], [uy * sx, ny * sy, 0.0]])
    M[:, 2] = cen - M[:, :2] @ np.array([sl / 2, (sh - 1) / 2])
    r_ = 0.5 * math.hypot(L, w) + 3
    x0, y0 = int(math.floor(cen[0] - r_)), int(math.floor(cen[1] - r_))
    x1, y1 = int(math.ceil(cen[0] + r_)), int(math.ceil(cen[1] + r_))
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if X1 <= X0 or Y1 <= Y0:
        return
    M2 = M.copy(); M2[:, 2] -= [X0, Y0]
    patch = cv2.warpAffine(src, M2, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = patch[..., 3:]
    reg = img[Y0:Y1, X0:X1]
    reg *= (1 - 0.92 * a)
    reg += patch[..., :3]


ROD_W_CUR = [11.0]


def render_tree(img, tr, t, xoff=0.0, gain=1.0):
    pose = tr.pose(t)
    g = G_FALL * tr.scale
    tau = t - T_IN
    for p in tr.pieces:
        p0, d, L, ang = pose[p["seg"]]
        src = STRIPS[tr.dye][p["strip"]]
        u0, u1 = int(p["u0"]), max(int(p["u1"]), int(p["u0"]) + 2)
        piece = src[:, u0:u1]
        ROD_W_CUR[0] = ROD_W[p["strip"]]
        mlt = smooth(32.05 + p["melt_d"], 32.50 + p["melt_d"], t)              # softening, at the piece's own time
        Lp = (p["s1"] - p["s0"])
        ov = 2.5 * (1 - mlt)                                                     # intact rods: pieces overlap, no seams
        Ld = Lp * (1 - 0.22 * mlt) + 2 * ov
        wd = p["w"] * (1 + 0.16 * mlt * (1 + 0.15 * math.sin(7 * tau + p["psi"])))
        cen = p0 + d * (p["s0"] + p["s1"]) / 2
        cen = cen + np.array([xoff, 0.0])
        dd = d
        solid = 0.0
        if t > p["rel"]:
            x_ = min(1.0, (t - p["rel"]) / (T_ALIGN - p["rel"])); e = 1 - (1 - x_) ** 2.2   # leaves fast, at rest by 33.6
            m = p["m"]
            psi = p["psi"] + 0.6 * math.copysign(1, m) * (1 - math.cos(abs(m) * tr.n * OMEGA * tau))
            cen = cen + p["R"] * e * np.array([math.cos(psi), math.sin(psi)])
            spin = math.radians(p["spin"]) * e * (1 - math.cos(abs(m) * tr.n * OMEGA * tau)) * 0.5
            solid = smooth(p["rel"] + 0.1, 33.45, t)
            tf = t - (T_ALIGN + p["fall"])
            if tf > 0:
                cen = cen + np.array([p["vx"] * tf, 0.5 * g * tf * tf])
                spin += math.radians(p["spin"] * 2.5) * tf
            c, s_ = math.cos(spin), math.sin(spin)
            dd = np.array([c * d[0] - s_ * d[1], s_ * d[0] + c * d[1]])
            if cen[1] > H + 30:
                continue
        draw_piece(img, piece, cen, dd, Ld, wd, alpha_cap=mlt, mult=gain, solid=solid)


FRONT_T = [Tree(*a) for a in FRONT]
BACK_T = [Tree(bx, h, n, dye, sd, mr, scale=0.55) for (bx, h, n, dye, sd, mr) in BACK]
FRONT_ORDER = [2, 0, 4, 1, 3, 5]


def frame(t):
    img = T.practicals(t).copy()
    cx = T.camx(t)
    back = np.zeros((H, W, 3), np.float32)
    for tr in BACK_T:
        render_tree(back, tr, t, xoff=-0.5 * cx, gain=0.75)
    back = cv2.GaussianBlur(back, (0, 0), 2.4)
    img = img + back                                                  # the back plane: defocused, dim witnesses
    for i in FRONT_ORDER:
        render_tree(img, FRONT_T[i], t, xoff=-cx, gain=1.35)
    return T.halation_rolloff(img)


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
        ims = []
        for t in sys.argv[2:]:
            im = u8(frame(float(t))); ims.append(im)
            cv2.imwrite(f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/s4_{t}.png", cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
        cv2.imwrite("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/s4_sheet.png", cv2.cvtColor(np.vstack(ims), cv2.COLOR_RGB2BGR))
