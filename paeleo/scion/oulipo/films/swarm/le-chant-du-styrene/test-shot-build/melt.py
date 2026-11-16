"""Sh3b 'La coulee rendue' -- the defining beat, test shot.

HANDMADE: cavity/channel depth field built from geometry.json (SCION #8 constraint graph:
  cavity_i := ring piece i (shape)  attached-to  arm i tip (position); one source of truth),
  fill-time field T (weighted geodesic from the sprue), backward drain, Beer-Lambert melt colour,
  refraction of the steel through the melt surface, light spill, raking key, focus pull.
  Meniscus boil = smooth noise reseeded on twos + a Whitney oscillator bank (SCION #6),
  partials k*w0 with locked 2:3 ratio between neighbouring cavities.
FORAGED: steel = 'Injection mold - (11).jpg', Bricetofly, CC0 (Commons).
  Ring/arm geometry measured by GrabCut (SCION #29) from 'Spritzguss teile.jpg', Gmhofmann, CC BY-SA 4.0.

Writes plane-space precompute + per-frame band render function `band(t)` (960x408 RGB uint8).
"""
import heapq, json, math
from pathlib import Path
import cv2, numpy as np

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene")
TS = SRC / "test-shot"
G = json.load(open(TS / "geometry.json"))
BW, BH = 960, 408
DUR = 6.8
rs = np.random.RandomState(1958)

lr_bore = {}
def measure_bores():
    for lr in G["loose_rings"]:
        cut = cv2.imread(str(TS / lr["cutout"]), cv2.IMREAD_UNCHANGED)
        v = cut[..., :3].max(-1).astype(int)
        e = lr["ellipse_src"]
        # bore = dark (V<75) or see-through pixels connected to the hole centre (top face centre ~ 0.12 R above fit centre)
        cx = int(e["cx"] - lr["bbox"][0]); cy = int(e["cy"] - lr["bbox"][1] - 0.12 * e["major"] / 2)
        dark = ((v < 75) | (cut[..., 3] < 128)).astype(np.uint8)
        n, lab = cv2.connectedComponents(dark)
        yy0, xx0 = np.mgrid[0:dark.shape[0], 0:dark.shape[1]]
        near = (np.hypot(xx0 - cx, yy0 - cy) < 0.32 * e["major"] / 2) & (dark > 0)
        ids = np.unique(lab[near]); ids = ids[ids > 0]
        b = np.isin(lab, ids) & (np.hypot(xx0 - cx, yy0 - cy) < 0.45 * e["major"] / 2)
        lr_bore[lr["id"]] = b.astype(np.uint8)
        lr["bore_r_rect"] = float(math.sqrt(b.sum() / G["aspect"] / math.pi))
        # constraint-graph measurements in the rectified frame (y scaled by 1/aspect):
        # equal-area outer radius and silhouette centroid; bore centre offset from that centroid
        a = cut[..., 3] > 127
        ys, xs = np.nonzero(a); bys, bxs = np.nonzero(b)
        lr["R_eq_rect"] = float(math.sqrt(a.sum() / G["aspect"] / math.pi))
        lr["centroid_rect_in_bbox"] = [float(xs.mean()), float(ys.mean() / G["aspect"])]
        lr["bore_offset_rect"] = [float(bxs.mean() - xs.mean()), float((bys.mean() - ys.mean()) / G["aspect"])]
measure_bores()

# ------------------------------------------------------------------ plane ---
S = 1.45                       # plane px per rectified source px (declared transform: similarity)
PW, PH = 1500, 1000
hub_r = np.array(G["hub_rect"])
OFF = np.array([PW * 0.47, PH * 0.50]) - S * (hub_r - np.array([0, 18]))
def P(xy):
    return S * np.asarray(xy, float) + OFF

yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def seg_dist(px, py, a, b):
    ab = b - a; L2 = (ab ** 2).sum()
    t = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / L2, 0, 1)
    return np.hypot(px - (a[0] + t * ab[0]), py - (a[1] + t * ab[1])), t

def smooth_noise(seed, sigma, shape=(PH, PW)):
    r = np.random.RandomState(seed).normal(0, 1, (shape[0] // 4, shape[1] // 4)).astype(np.float32)
    r = cv2.GaussianBlur(r, (0, 0), sigma / 4)
    r = cv2.resize(r, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return r / (r.std() + 1e-6)

D_CH, D_CAV, D_RIM = 0.85, 1.0, 1.25   # depths (units of the melt's optical depth scale)
depth = np.zeros((PH, PW), np.float32)
part = np.zeros((PH, PW), np.int8) - 1   # -1 steel, 0..3 cavity id, 4 runner, 5 sprue
hub = P(hub_r)
cav_masks = []
cav_info = []
wobble = smooth_noise(3, 30)
for a, lr in zip(G["arms"], G["loose_rings"]):
    k = a["id"]
    c = P(a["ring_center_rect"])
    R = S * lr["R_eq_rect"]
    # hole radius measured from the loose ring cutout (dark bore), see iou() below
    rh = S * lr["bore_r_rect"]
    d = c - hub; u = d / np.linalg.norm(d)
    gate = c - u * (R - 2)
    w = S * float(np.clip(a["width_px"], 12.0, 18.0)) / 2           # measured arm half-width
    dd, tt = seg_dist(xx, yy, hub, gate)
    ww = w * (1 + 0.07 * wobble) * (1 - 0.42 * smoothstep(0.82, 1.0, tt))   # taper into the gate
    ch = np.where(dd < ww, D_CH * np.sqrt(np.clip(1 - (dd / ww) ** 2, 0, 1)), 0)
    sel = ch > depth; depth[sel] = ch[sel]; part[sel & (part < 4)] = 4
    # ring cavity: annulus, deeper outer rim, rib (= the part's groove) with three slots
    bo = S * np.array(lr["bore_offset_rect"])         # eccentric bore, as the Sh2 piece shows it
    r = np.hypot(xx - c[0], yy - c[1]); th = np.arctan2(yy - c[1], xx - c[0])
    rb = np.hypot(xx - c[0] - bo[0], yy - c[1] - bo[1])
    mid = c + 0.5 * bo; rm_ = np.hypot(xx - mid[0], yy - mid[1])
    ann = smoothstep(rh, rh + 3, rb) * (1 - smoothstep(R - 3, R, r))
    prof = D_CAV + (D_RIM - D_CAV) * smoothstep(0.70 * R, 0.80 * R, r)
    slot_rot = [0.4, 1.9, 2.8, 1.1][k]
    slots = np.zeros_like(r)
    for s in range(3):
        ang = slot_rot + s * 2 * math.pi / 3
        dth = np.abs(np.angle(np.exp(1j * (th - ang))))
        slots = np.maximum(slots, 1 - smoothstep(0.06, 0.11, dth))
    rib = (1 - smoothstep(2.5, 5.0, np.abs(rm_ - 0.60 * R))) * (1 - slots)
    prof = prof - 0.55 * rib
    cav = ann * prof * (1 + 0.03 * wobble)
    m = cav > 0.02
    cav_masks.append(m)
    sel = cav > depth; depth[sel] = cav[sel]; part[sel & m] = k
    cav_info.append(dict(id=k, c=c, R=R, rh=rh, gate=gate))
# sprue mouth (the post of the real runner, seen end-on)
rs_ = np.hypot(xx - hub[0], yy - hub[1])
w_s = S * 9.5
spr = np.where(rs_ < w_s, 2.4 * np.sqrt(np.clip(1 - (rs_ / w_s) ** 2, 0, 1)) + 0.6, 0)
sel = spr > depth; depth[sel] = spr[sel]; part[sel] = 5
mask = depth > 0.015

# ------------------------------------------------------- fill-time field ---
def geodesic(mask, speed, src, step=2):
    m = mask[::step, ::step]; sp = speed[::step, ::step]
    h, w = m.shape
    T = np.full((h, w), np.inf, np.float32)
    sy, sx = int(src[1] / step), int(src[0] / step)
    T[sy, sx] = 0; q = [(0.0, sy, sx)]
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while q:
        t, y, x = heapq.heappop(q)
        if t > T[y, x]:
            continue
        for dy, dx, l in nb:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and m[ny, nx]:
                nt = t + l * step / (0.5 * (sp[y, x] + sp[ny, nx]))
                if nt < T[ny, nx]:
                    T[ny, nx] = nt; heapq.heappush(q, (nt, ny, nx))
    T[~np.isfinite(T)] = 0
    return cv2.resize(T, (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_LINEAR)

# speed: slower near walls (shear lag, ~ depth^0.6), slower in cavities (spreading front)
speed = 0.15 + np.clip(depth / D_CH, 0, 1) ** 0.6
speed[part >= 0] *= 0.55
speed[part == 5] *= 1.6
T = geodesic(mask, speed, hub)
T = cv2.GaussianBlur(T, (0, 0), 1.2) * mask
Tn = T / T[mask].max()
gate_T = [float(Tn[int(ci["gate"][1]), int(ci["gate"][0])]) for ci in cav_info]
cav_Tmax = [float(Tn[m].max()) for m in cav_masks]
order_empty = list(np.argsort(cav_Tmax)[::-1])   # far cavity first

# tau(t): the fill run backward. Key times (shot-relative, s): all cavities empty by 2.45
# (the hollow is named on 'un creux' at 2.25-2.55), sprue empty at 5.40 (= 26.20 film time).
g_min = min(gate_T)
KEYS = [(0.00, 1.08), (0.25, 1.05), (1.40, 0.45 * g_min + 0.55 * max(cav_Tmax)), (2.45, g_min - 0.015),
        (3.6, 0.42 * g_min), (4.7, 0.10), (5.40, -0.04), (DUR, -0.04)]
def tau(t):
    for (t0, v0), (t1, v1) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * (x * x * (3 - 2 * x) * 0.6 + 0.4 * x)
    return KEYS[-1][1]
tt_ = np.linspace(0, DUR, 2000); tau_tab = np.array([tau(t) for t in tt_])
# per-pixel local drain time (for the residual wet film)
order = np.argsort(tau_tab)
t_drain = np.interp(Tn, tau_tab[order], tt_[order]).astype(np.float32)

# ------------------------------------------------------------------ steel ---
steel = cv2.imread(str(SRC / "kf/mold11.jpg"))[..., ::-1].astype(np.float32) / 255
crop = steel[118:455, 640:1280]                     # right plate + edges of the real pockets, screw
crop = cv2.resize(crop, (PW, int(PW * crop.shape[0] / crop.shape[1])), interpolation=cv2.INTER_CUBIC)
if crop.shape[0] < PH:
    pad = PH - crop.shape[0]
    crop = np.vstack([crop[:pad][::-1], crop])     # declared: mirrored extension of the far edge strip
steel = crop[:PH, :PW]
steel_l = steel.mean(-1, keepdims=True)
# cool the photograph to a neutral steel and keep its real texture
steel = 0.55 * steel + 0.45 * steel_l
steel = steel * np.array([0.92, 0.97, 1.05], np.float32)
# cavity floor: same steel, seen through the cavity (parallax drop) + light falloff with depth
grad_y, grad_x = np.gradient(cv2.GaussianBlur(depth, (0, 0), 1.0))
# raking key from far-left (lights walls that face it), and one from the camera side very dim
Lk = np.array([0.55, 0.35, 0.76]); Lk /= np.linalg.norm(Lk)
nz = 1.0; nx_, ny_ = grad_x * 9, grad_y * 9           # cavity surface z = -depth -> n = (dx, dy, 1)
nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz)
lam = np.clip((nx_ * Lk[0] + ny_ * Lk[1] + Lk[2]) / nn, 0, 1)
wall = np.clip(np.hypot(grad_x, grad_y) * 9, 0, 1)

# real machining texture of the photograph (high-pass), used where light rakes or spills
_sl = steel.mean(-1)
detail = np.clip((_sl - cv2.GaussianBlur(_sl, (0, 0), 6)) * 7 + 1.0, 0.25, 2.2)[..., None]
steel_t = steel * detail
noise_bank = [smooth_noise(100 + i, 9) for i in range(8)]
noise_fine = [smooth_noise(200 + i, 3) for i in range(8)]
theta_cav = np.zeros((PH, PW), np.float32)
for ci in cav_info:
    m = part == ci["id"]
    theta_cav[m] = np.arctan2(yy[m] - ci["c"][1], xx[m] - ci["c"][0])

ALPHA = np.array([0.25, 1.50, 4.5], np.float32)        # Beer-Lambert per unit optical depth (red passes)
SCAT = np.array([0.11, 0.018, 0.016], np.float32)       # back-scatter of the red pigment
E = np.array([1.12, 1.04, 0.86], np.float32)             # warm source seen through the melt

def plane(t, k):
    """Plane-space RGB (float, linear-ish 0..1) at shot time t, frame k."""
    tw = k // 2                                          # boil on twos
    eta = 0.020 * noise_bank[tw % 8] + 0.006 * noise_fine[(tw * 3) % 8]
    # SCION #6: oscillator bank on the meniscus; cavity i gets w_i in 2:3 chain, partials 1..3
    osc = np.zeros_like(Tn)
    for ci in cav_info:
        m = part == ci["id"]
        wi = 2 * math.pi * 0.42 * (1.5 ** (ci["id"] % 2)) * (1 + ci["id"] // 2 * 0.5)
        th = theta_cav[m]
        osc[m] = sum((0.010 / p) * np.sin(p * (3 * th) + p * wi * (tw * 2 / 24) + ci["id"]) for p in (1, 2, 3))
    run = part == 4
    osc[run] = 0.006 * np.sin(Tn[run] * 60 - 2 * math.pi * 0.9 * (tw * 2 / 24))
    f = tau(t) - (Tn + eta + osc)
    present = (f > 0) & mask
    # thickness: full depth behind the front, thinning to a film at the meniscus (rounded contact)
    h = depth * (1 - np.exp(-np.clip(f, 0, None) / 0.022))
    h = np.where(present, h, 0)
    # residual wet film for ~1 s after the front passes
    age = np.clip(t - t_drain, 0, None)
    wet = np.where(mask & ~present, 0.05 * depth * np.exp(-age / 0.9), 0)
    ripple = 0.035 * noise_fine[(tw * 5 + 3) % 8] * (h > 0.05)
    hs = cv2.GaussianBlur(h + wet + ripple, (0, 0), 2.2)
    gy, gx = np.gradient(hs)
    # refraction: the floor seen through the melt is displaced by the surface slope (n ~ 1.59, PS)
    ref = 40.0
    drop = depth * 5.0                                   # parallax of the cavity floor (view tilt)
    mapx = (xx - ref * gx).astype(np.float32)
    mapy = (yy - ref * gy - drop).astype(np.float32)
    floor = cv2.remap(steel_t, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    floor_l = floor.mean(-1, keepdims=True)
    # melt radiance: source reflected by the polished floor, through the melt twice
    # colour from thickness; a vanishing film cannot pass more light than a thin front (no whites):
    # optical path floors at 0.16, brightness falls with the film itself
    hh = (h + wet)
    th2 = 2 * np.maximum(hh, 0.16)[..., None]
    trans = np.exp(-ALPHA * th2)
    fl = np.clip((floor_l - 0.55) * 1.6 + 0.55, 0.08, 1.3)   # steel texture seen through
    rad = E * (0.25 + 1.15 * fl) * trans * 0.95 + SCAT * (1 - np.exp(-3 * th2))
    rad *= smoothstep(0.0, 0.10, hh)[..., None] * (present | (wet > 0.002))[..., None]
    # meniscus specular (key from above-left), small catches only
    nl = np.sqrt(gx ** 2 + gy ** 2 + 1e-4)
    spec = np.clip(-(gx * 0.6 + gy * 0.8) / nl, 0, 1) ** 5 * smoothstep(0.003, 0.015, nl) * 0.75
    spec = spec * ((h + wet) > 0.003)
    # light spill from the melt onto steel (two scales), computed at quarter res
    em = (rad * (present[..., None])).astype(np.float32)
    sm = cv2.resize(em, (PW // 4, PH // 4), interpolation=cv2.INTER_AREA)
    spill = 0.30 * cv2.GaussianBlur(sm, (0, 0), 6) + 1.0 * cv2.GaussianBlur(sm, (0, 0), 22)
    spill = cv2.resize(spill, (PW, PH), interpolation=cv2.INTER_LINEAR)
    # steel shading: very low ambient + raking key on walls + spill * albedo
    base = steel * (0.042 + 0.09 * lam[..., None] * wall[..., None])
    empty = mask & ~present
    hollow = steel_t * (0.06 + 1.0 * (lam * wall)[..., None] + 0.09 * (part >= 0)[..., None]) * empty[..., None]
    lit = base * (~mask)[..., None] + hollow + floor * 0.03 * mask[..., None]
    lit = lit + spill * steel_t * 2.6 * (1 - 0.6 * present[..., None])
    col = np.where(present[..., None], rad, lit) + np.where((wet > 0.002)[..., None], rad * 0.35, 0)
    col = col + spec[..., None] * np.array([1.0, 0.86, 0.66], np.float32)
    return col, present

# ------------------------------------------------------------------ camera ---
def camera(t):
    """Pinhole looking down at the mould face at a tilt; slow glide + push (multiplane-like camera)."""
    x = t / DUR
    e = x * x * (3 - 2 * x)
    pitch = math.radians(50 - 4 * e)        # from the plate normal
    yaw = math.radians(-9 + 5 * e)
    roll = math.radians(-6 + 1.5 * e)
    dist = 1650 - 150 * e
    tgt = np.array([PW * (0.50 + 0.02 * e), PH * (0.47 - 0.02 * e), 0.0])
    cp, sp_, cy, sy, cr, sr = math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw), math.cos(roll), math.sin(roll)
    # camera position: above the plate, pulled back toward +y (near edge)
    cpos = tgt + dist * np.array([sy * sp_, cy * sp_, cp])
    f = tgt - cpos; f /= np.linalg.norm(f)
    up0 = np.array([0, -1.0, 0])
    r_ = np.cross(f, up0); r_ /= np.linalg.norm(r_)
    u_ = np.cross(r_, f)
    r2 = cr * r_ + sr * u_; u2 = -sr * r_ + cr * u_
    R = np.stack([r2, -u2, f])               # rows: x right, y down, z forward
    tvec = -R @ cpos
    fpx = 1020
    K = np.array([[fpx, 0, BW / 2], [0, fpx, BH / 2], [0, 0, 1]])
    Hm = K @ np.column_stack([R[:, 0], R[:, 1], tvec])
    return Hm, R, tvec

def zdepth(Hm, R, tvec):
    Hi = np.linalg.inv(Hm)
    by, bx = np.mgrid[0:BH, 0:BW].astype(np.float64)
    pts = Hi @ np.stack([bx.ravel(), by.ravel(), np.ones(bx.size)])
    X = pts[0] / pts[2]; Y = pts[1] / pts[2]
    z = R[2, 0] * X + R[2, 1] * Y + tvec[2]
    return z.reshape(BH, BW).astype(np.float32), X.reshape(BH, BW), Y.reshape(BH, BW)

# blue practicals: their own plane, behind the mould edge, drifting at 0.3x of the camera glide
def practicals(t):
    by, bx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    dx = -14 * (t / DUR)
    disc = np.exp(-(((bx - (90 + dx)) ** 2 + (by - 70) ** 2) / (2 * 70 ** 2)) ** 2.2)
    bar = np.exp(-((np.clip(np.abs(bx - (560 + dx)) - 230, 0, None) / 30) ** 2 + ((by - 20) / 15) ** 2) ** 1.6)
    c1 = np.array([0.04, 0.16, 0.42], np.float32); c2 = np.array([0.055, 0.15, 0.36], np.float32)
    return 0.8 * disc[..., None] * c1 + bar[..., None] * c2 * 0.85

def band(t, k):
    col, present = plane(t, k)
    Hm, R, tvec = camera(t)
    img = cv2.warpPerspective(col, Hm, (BW, BH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    inside = cv2.warpPerspective(np.ones((PH, PW), np.float32), Hm, (BW, BH), flags=cv2.INTER_LINEAR)
    # the plate's far edge: a chamfer catching the blue practicals
    z, X, Y = zdepth(Hm, R, tvec)
    chamfer = np.exp(-((Y - 6) / 5) ** 2) * (X > 0) * (X < PW)
    img = img + chamfer[..., None].astype(np.float32) * np.array([0.02, 0.06, 0.15], np.float32)
    # blue sheen of the practicals on the brushed steel (far part of the plate)
    sheen = np.clip(1 - Y / (PH * 0.55), 0, 1) ** 2 * inside
    img = img + (sheen[..., None] * np.array([0.004, 0.016, 0.05], np.float32))
    img = img * inside[..., None] + practicals(t) * (1 - inside[..., None])
    # focus pull: from the cavity that empties first to the sprue, thin-lens circle of confusion
    far = cav_info[order_empty[0]]["c"]
    x = np.clip((t - 0.3) / 4.6, 0, 1); x = x * x * (3 - 2 * x)
    fp = (1 - x) * far + x * hub
    zf = R[2, 0] * fp[0] + R[2, 1] * fp[1] + tvec[2]
    coc = np.abs(1 / z - 1 / zf) * zf * 26.0           # px of blur
    coc = np.where(inside > 0.5, coc, 7.0)
    levels = [img, cv2.GaussianBlur(img, (0, 0), 1.6), cv2.GaussianBlur(img, (0, 0), 3.4), cv2.GaussianBlur(img, (0, 0), 6.5)]
    sig = np.array([0, 1.6, 3.4, 6.5], np.float32)
    c = np.clip(coc, 0, 6.5)
    idx = np.clip(np.searchsorted(sig, c) - 1, 0, 2)
    wgt = (c - sig[idx]) / (sig[idx + 1] - sig[idx])
    lo = np.choose(idx[..., None].repeat(3, -1), levels[:3])
    hi = np.choose(idx[..., None].repeat(3, -1), levels[1:])
    out = lo * (1 - wgt[..., None]) + hi * wgt[..., None]
    # unify black point / gentle shoulder (the only grade): x/(1+0.25x)
    out = np.clip(out, 0, None)
    out = out * 1.0 / (1 + 0.22 * out)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

def iou_report():
    """Constraint residual: cavity silhouette (from geometry) vs the rectified ring cutout (Sh2 piece)."""
    res = []
    for lr, ci in zip(G["loose_rings"], cav_info):
        cut = cv2.imread(str(TS / lr["cutout"]), cv2.IMREAD_UNCHANGED)
        a = (cut[..., 3] > 127).astype(np.uint8)
        m = cv2.resize(a, (int(a.shape[1] * S), int(a.shape[0] * S / G["aspect"])), interpolation=cv2.INTER_NEAREST)
        bm = cv2.resize(lr_bore[lr["id"]], (m.shape[1], m.shape[0]), interpolation=cv2.INTER_NEAREST)
        sil = (m > 0) & ~(bm > 0)
        cx, cy = S * np.array(lr["centroid_rect_in_bbox"])
        c0 = ci["c"]; hh, ww = sil.shape
        y0, x0 = int(round(c0[1] - cy)), int(round(c0[0] - cx))
        cavm = cav_masks[ci["id"]][y0:y0 + hh, x0:x0 + ww]
        s2 = sil[:cavm.shape[0], :cavm.shape[1]]
        i = (cavm & s2).sum(); u = (cavm | s2).sum()
        res.append(dict(ring=lr["id"], arm=ci["id"], iou=round(float(i / u), 4)))
    return res

