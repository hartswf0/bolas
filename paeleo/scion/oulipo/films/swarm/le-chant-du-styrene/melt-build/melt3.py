"""Sh3a + Sh3b 'La coulee rendue' (round-3 build of the test shot; the defining beat).

ONE CONSTRAINT GRAPH (SCION #8 Sutherland): every shape here is generated from the cutout unit's
films/swarm/le-chant-du-styrene/geometry.json (canonical layout sh2b_hold: the bare left runner of
'Spritzguss teile.jpg' with its four loose rings homed at the arm tips by the gate-contact constraint):
  cavity_k  := ellipse fit of ring k (outer + bore)  attached-to  home_centre_k   (shape + position)
  channel_k := arm polyline k (hub -> gate_k), width measured on the GrabCut mask (SCION #29)
  sprue     := well at the hub, radius from the measured post width
Moving a measured point in geometry.json moves the Sh2 puppet rest pose, the gate contact and this mould.

HANDMADE: depth field, fill-time field T(x) (weighted geodesic from the sprue: Poiseuille speed ~ w^2 in each
arm, wall lag ~ depth^0.6, slower in cavities), backward drain (melt shown where T' + eta < tau, T' a
monotone re-timing of T), Beer-Lambert thickness colour, refraction of the steel through the melt surface,
light spill, meniscus specular, warm wet film in the hollows, multiplane blue practicals, perspective camera,
thin-lens focus pull. Boil eta reseeded on twos + a Whitney oscillator bank (SCION #6) on the meniscus.
FORAGED: steel = 'Injection mold - (11).jpg', Bricetofly, CC0 (Commons) -- quilted from its plain plate areas
plus two of its real socket screws (declared).
"""
import heapq, json, math
from pathlib import Path
import cv2, numpy as np

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SRC = ROOT / "sources/le-chant-du-styrene"
CUT = SRC / "cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-"
GEO = json.load(open(ROOT / "swarm/le-chant-du-styrene/geometry.json"))
BBOX = {k: v["bbox_src"] for k, v in json.load(open(CUT / "geom_src.json"))["report"]["pieces"].items()}
BW, BH, FPS = 960, 408, 24
SEED = 1958
PARAMS = {}

HUB = np.array(GEO["hub_src"], float)
CAM_HOLD = GEO["cameras"]["sh2b_hold"]          # centre (world), zoom
# ------------------------------------------------------------------ plane ---
S = 1.25                                          # plane px per world (= source) px
PW, PH = 1700, 1000
OFF = np.array([850.0, 560.0]) - S * np.array(CAM_HOLD["centre"])
def P(world):
    return S * np.asarray(world, float) + OFF
PARAMS.update(plane_scale=S, plane_size=[PW, PH], plane_offset=OFF.tolist())

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

# ------------------------------------------- measure channel widths on the mask ---
rmask = cv2.imread(str(CUT / "masks/bare_runner_mask.png"), 0)
rdt = cv2.distanceTransform((rmask > 127).astype(np.uint8), cv2.DIST_L2, 5)
bb = BBOX["bare_runner"]
def mask_width(poly_src, t0=0.2, t1=0.85):
    poly = np.array(poly_src, float)
    w = []
    for t in np.linspace(t0, t1, 40):
        i = t * (len(poly) - 1); j = int(i); f = i - j
        p = poly[j] * (1 - f) + poly[min(j + 1, len(poly) - 1)] * f
        x, y = int(round(p[0] - bb[0])), int(round(p[1] - bb[1]))
        if 0 <= y < rdt.shape[0] and 0 <= x < rdt.shape[1]:
            # local max of dt across the arm (the polyline may sit off the medial axis by a px or two)
            w.append(2 * float(rdt[max(0, y - 3):y + 4, max(0, x - 3):x + 4].max()))
    return float(np.median(w))
sprue_w = mask_width(GEO["sprue"]["polyline_src"], 0.3, 0.8)

D_CH, D_CAV, D_RIM, D_RIB = 0.40, 1.0, 1.25, 0.50     # depths in optical-depth units (runner thin, rings thick)
depth = np.zeros((PH, PW), np.float32)
part = np.zeros((PH, PW), np.int8) - 1           # -1 steel, 0..3 cavity, 4 runner, 5 sprue
arm_of = np.zeros((PH, PW), np.int8) - 1
hub = P([0, 0])
wobble = smooth_noise(3, 30)
cav_masks, cav_info = [], []

def ell_support(a, b, ang_major, phi):
    psi = phi - ang_major
    return a * b / np.hypot(b * np.cos(psi), a * np.sin(psi))

for k, rg in enumerate(GEO["rings"]):
    e = rg["ring_ellipse_src"]
    home = np.array(rg["home_centre_src"]) - HUB
    gate = np.array(rg["gate_src"]) - HUB
    c, gp = P(home), P(gate)
    w_src = float(np.clip(mask_width(rg["arm_polyline_src"]), 8, 24))
    w = S * w_src / 2
    # channel: hub -> gate along the measured arm polyline, tapering into the gate (a real gate is a restriction)
    poly = [P(np.array(p) - HUB) for p in rg["arm_polyline_src"]]
    dd = np.full((PH, PW), 1e9, np.float32); tt = np.zeros((PH, PW), np.float32)
    L = np.cumsum([0] + [np.linalg.norm(poly[i + 1] - poly[i]) for i in range(len(poly) - 1)])
    for i in range(len(poly) - 1):
        d_, t_ = seg_dist(xx, yy, poly[i], poly[i + 1])
        sel = d_ < dd; dd[sel] = d_[sel]; tt[sel] = ((L[i] + t_ * (L[i + 1] - L[i])) / L[-1])[sel]
    ww = w * (1 + 0.07 * wobble) * (1 - 0.40 * smoothstep(0.86, 1.0, tt))
    ch = np.where(dd < ww, D_CH * np.sqrt(np.clip(1 - (dd / ww) ** 2, 0, 1)), 0)
    sel = ch > depth; depth[sel] = ch[sel]; part[sel & (part < 4)] = 4; arm_of[sel] = k
    # cavity = the ring: ellipse fit (U2: major axis at fit angle + 90 deg), eccentric bore from the bore fit
    a, b_ = e["major"] / 2, e["minor"] / 2
    amaj = math.radians(e["angle"] + 90)
    th = np.arctan2(yy - c[1], xx - c[0])
    r = np.hypot(xx - c[0], yy - c[1]) / S
    rho = r / ell_support(a, b_, amaj, th)         # 1 at the outer rim
    ho = e["hole"]
    bc = c + S * np.array([ho["cx"] - e["cx"], ho["cy"] - e["cy"]])
    ha, hb = ho["major"] / 2, ho["minor"] / 2
    hth = np.arctan2(yy - bc[1], xx - bc[0])
    hr = np.hypot(xx - bc[0], yy - bc[1]) / S
    hrho = hr / ell_support(ha, hb, math.radians(ho.get("angle", e["angle"]) + 90), hth)
    ann = smoothstep(1.0, 1.0 + 1.2 / max(hb, 1), hrho) * (1 - smoothstep(1 - 1.2 / a, 1.0, rho))   # steep machined walls
    prof = D_CAV + (D_RIM - D_CAV) * smoothstep(0.72, 0.84, rho)
    slot_rot = [0.4, 1.9, 2.8, 1.1][k]
    slots = np.zeros_like(rho)
    for s in range(3):
        dth = np.abs(np.angle(np.exp(1j * (th - slot_rot - s * 2 * math.pi / 3))))
        slots = np.maximum(slots, 1 - smoothstep(0.06, 0.11, dth))
    rib = (1 - smoothstep(0.035, 0.075, np.abs(rho - 0.58))) * (1 - slots)
    prof = prof - (D_CAV - D_RIB) * rib
    cav = ann * prof * (1 + 0.03 * wobble)
    m = cav > 0.02
    cav_masks.append(m)
    sel = cav > depth; depth[sel] = cav[sel]; part[sel & m] = k
    cav_info.append(dict(id=k, ring=rg["ring"], piece=rg["loose_piece"], c=c, gate=gp, R=S * a, w_src=w_src,
                         home_world=home.tolist()))
# sprue well (the post of the real runner stands out of the plane; in the mould half it is a hole at the hub)
rs_ = np.hypot(xx - hub[0], yy - hub[1])
w_s = S * sprue_w / 2 * 1.15
spr = np.where(rs_ < w_s, 2.4 * np.sqrt(np.clip(1 - (rs_ / w_s) ** 2, 0, 1)) + 0.6, 0)
sel = spr > depth; depth[sel] = spr[sel]; part[sel] = 5
mask = depth > 0.015
PARAMS.update(depths=dict(channel=D_CH, cavity=D_CAV, rim=D_RIM, rib=D_RIB, sprue="0.6 + 2.4*hemisphere"),
              arm_widths_src_measured=[round(ci["w_src"], 2) for ci in cav_info], sprue_post_width_src=round(sprue_w, 2))

# ------------------------------------------------------- fill-time field ---
def geodesic(mask, speed, src, step=2):
    m = mask[::step, ::step]; sp = speed[::step, ::step]
    h, w = m.shape
    T = np.full((h, w), np.inf, np.float64)
    sy, sx = int(round(src[1] / step)), int(round(src[0] / step))
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
    w = np.isfinite(T).astype(np.float32)
    T[~np.isfinite(T)] = 0
    # normalized convolution back to full res: edge pixels missed by the coarse grid take their neighbours' T
    # (a plain resize/blur would pull rim values toward 0 and leave a late-draining rim)
    Tf = cv2.resize(T.astype(np.float32), (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_NEAREST)
    wf = cv2.resize(w, (mask.shape[1], mask.shape[0]), interpolation=cv2.INTER_NEAREST)
    num = cv2.GaussianBlur(Tf * wf, (0, 0), 1.6); den = cv2.GaussianBlur(wf, (0, 0), 1.6)
    for _ in range(4):
        hole = den < 1e-3
        if not (hole & mask).any():
            break
        num = np.where(hole, cv2.GaussianBlur(num, (0, 0), 3), num); den = np.where(hole, cv2.GaussianBlur(den, (0, 0), 3), den)
    return num / np.maximum(den, 1e-6)

W_REF = float(np.median([ci["w_src"] for ci in cav_info]))
speed = 0.15 + np.clip(depth / np.where(part == 4, D_CH, D_CAV), 0, 1) ** 0.6       # wall lag (shear layer)
for ci in cav_info:                                                                # Hagen-Poiseuille: v ~ w^2
    speed[(part == 4) & (arm_of == ci["id"])] *= (ci["w_src"] / W_REF) ** 2
speed[(part >= 0) & (part <= 3)] *= 0.6                                             # spreading front in cavities
speed[part == 5] *= 1.6
T = geodesic(mask, speed, hub)
T = T * mask
Tn = T / T[mask].max()
gate_T = [float(Tn[max(0, int(ci["gate"][1]) - 2):int(ci["gate"][1]) + 3, max(0, int(ci["gate"][0]) - 2):int(ci["gate"][0]) + 3].max()) for ci in cav_info]
cav_Tmax = [float(Tn[m].max()) for m in cav_masks]
# Hesitation (declared model): in an unbalanced multi-cavity runner the front stalls at a gate while an
# easier branch is still filling; branch k's cavity starts once the previously reached cavity is HES_OVERLAP full.
HES_OVERLAP = 0.7
hes = [0.0] * 4
prev_end = None
for i in np.argsort(gate_T):
    i = int(i); span = cav_Tmax[i] - gate_T[i]
    if prev_end is not None:
        hes[i] = max(0.0, prev_end - gate_T[i])
    prev_end = gate_T[i] + hes[i] + HES_OVERLAP * span
for i in range(4):
    Tn[cav_masks[i] & (part == i)] += hes[i]
Tn = Tn / Tn[mask].max()
gate_T = [float(g + h) / float(max(cav_Tmax[j] + hes[j] for j in range(4))) for g, h in zip(gate_T, hes)]
cav_Tmax = [float(Tn[m].max()) for m in cav_masks]
PARAMS.update(hesitation_overlap=HES_OVERLAP, hesitation_delay_T=[round(h, 4) for h in hes])
order_empty = [int(i) for i in np.argsort(gate_T)[::-1]]            # far (filled last) empties first
PARAMS.update(speed="0.15 + (depth/D)^0.6, x (w_arm/w_median)^2 in arm channels, x0.6 in cavities, x1.6 in sprue",
              gate_T=[round(g, 4) for g in gate_T], cav_Tmax=[round(g, 4) for g in cav_Tmax])

# Backward run: monotone re-timing of T to shot time (the drain cue sheet agreed with the process-verse unit:
# cavities released far->near at 21.9/22.9/23.9/24.9 film s, last melt down the sprue at 26.20).
T0_3B = 20.80
REL = [21.9, 22.9, 23.9, 24.9]
SPRUE_T = 26.20
# a cavity is empty when the lowest-T melt in it (beside its gate) has gone: knot on its 0.5th-percentile T
empty_T = [float(np.percentile(Tn[cav_masks[i]], 0.5)) for i in range(4)]
knots_T = [1.02] + [empty_T[i] for i in order_empty] + [0.0]
knots_t = [0.30] + [r - T0_3B for r in REL] + [SPRUE_T - T0_3B]
# a cavity starts to drain only once the previous one is nearly out: extra knot at each cavity's far edge
kT, kt = [knots_T[0]], [knots_t[0]]
for j, i in enumerate(order_empty):
    if j > 0 and cav_Tmax[i] < kT[-1] - 1e-3:
        kT.append(cav_Tmax[i]); kt.append(kt[-1] + 0.55 * (knots_t[j + 1] - kt[-1]))
    kT.append(empty_T[i]); kt.append(knots_t[j + 1])
kT.append(0.0); kt.append(SPRUE_T - T0_3B)
kT, kt = np.array(kT), np.array(kt)
assert np.all(np.diff(kT) < 0) and np.all(np.diff(kt) > 0), (kT, kt)
t_drain = np.interp(-Tn, -kT, kt).astype(np.float32)           # shot-relative time at which each pixel drains
PARAMS.update(retime_knots=dict(T=kT.round(4).tolist(), t_shot=kt.round(3).tolist()))
def tau_of_t(t):
    """the threshold, in re-timed units: melt present where t_drain + eta > t  <=>  T' + eta' < tau"""
    return t

# ------------------------------------------------------------------ steel ---
photo = cv2.imread(str(SRC / "kf/mold11.jpg"))[..., ::-1].astype(np.float32) / 255
# declared: plate texture quilted (feathered random patches) from the photo's plain plate areas only,
# so no cavity is cut through the photo's own slider pocket; two of its real socket screws are kept.
PLAIN = [(235, 790, 5, 285), (255, 435, 800, 1170), (615, 785, 800, 1170)]
rq = np.random.RandomState(SEED)
SC = 1.33
tex = np.zeros((PH, PW, 3), np.float32); wsum = np.zeros((PH, PW, 1), np.float32)
patch = 150
win = np.outer(np.hanning(patch), np.hanning(patch))[..., None].astype(np.float32) + 1e-3
for py in range(-patch // 2, PH, patch // 2):
    for px in range(-patch // 2, PW, patch // 2):
        y0, y1, x0, x1 = PLAIN[rq.randint(len(PLAIN))]
        sh = int(patch / SC) + 1
        sy = rq.randint(y0, y1 - sh); sx = rq.randint(x0, x1 - sh)
        pc = cv2.resize(photo[sy:sy + sh, sx:sx + sh], (patch, patch), interpolation=cv2.INTER_CUBIC)
        pc = pc / (pc.mean((0, 1), keepdims=True) + 1e-4) * 0.62          # level-match patches
        ya, xa = max(py, 0), max(px, 0); yb, xb = min(py + patch, PH), min(px + patch, PW)
        tex[ya:yb, xa:xb] += (pc * win)[ya - py:yb - py, xa - px:xb - px]
        wsum[ya:yb, xa:xb] += win[ya - py:yb - py, xa - px:xb - px]
steel = tex / wsum
# real screws from the photo (round crop, feathered) at the plate corners, away from the layout
for (cy_, cx_, rr), (ty, tx) in [((182, 1243, 36), (300, 1540))]:
    crop = photo[cy_ - rr:cy_ + rr, max(cx_ - rr, 0):cx_ + rr]
    crop = cv2.resize(crop, None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC)
    hh, ww = crop.shape[:2]
    my, mx = np.mgrid[0:hh, 0:ww]
    al = (1 - smoothstep(0.80, 0.98, np.hypot(mx - ww / 2, my - hh / 2) / (min(hh, ww) / 2)))[..., None]
    ys, xs = ty - hh // 2, tx - ww // 2
    steel[ys:ys + hh, xs:xs + ww] = steel[ys:ys + hh, xs:xs + ww] * (1 - al) + crop * al
steel_l = steel.mean(-1, keepdims=True)
steel = (0.55 * steel + 0.45 * steel_l).astype(np.float32)                 # neutral steel, real texture kept
_sl = steel.mean(-1)
detail = np.clip((_sl - cv2.GaussianBlur(_sl, (0, 0), 6)) * 7 + 1.0, 0.25, 2.2)[..., None]
steel_t = steel * detail

grad_y, grad_x = np.gradient(cv2.GaussianBlur(depth, (0, 0), 1.0))
Lk = np.array([0.55, 0.35, 0.76]); Lk /= np.linalg.norm(Lk)              # raking key from far-left
nx_, ny_ = grad_x * 9, grad_y * 9
nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + 1.0)
lam = np.clip((nx_ * Lk[0] + ny_ * Lk[1] + Lk[2]) / nn, 0, 1)
wall = np.clip(np.hypot(grad_x, grad_y) * 9, 0, 1)
# far-side walls of each hollow face the warm source and catch it (the 'wet-lit' rim)
facing = np.clip(-(grad_x * 0.45 + grad_y * 0.9) * 14, 0, 1)
cling = np.clip(cv2.GaussianBlur(wall, (0, 0), 2.0) * 1.6, 0, 1)

noise_bank = [smooth_noise(100 + i, 9) for i in range(8)]
noise_fine = [smooth_noise(200 + i, 3) for i in range(8)]
theta_cav = np.zeros((PH, PW), np.float32)
for ci in cav_info:
    m = part == ci["id"]
    theta_cav[m] = np.arctan2(yy[m] - ci["c"][1], xx[m] - ci["c"][0])

ALPHA = np.array([0.45, 1.30, 3.2], np.float32)      # Beer-Lambert per unit optical depth (red passes most)
SCAT = np.array([0.12, 0.02, 0.012], np.float32)      # back-scatter of the red pigment
E = np.array([1.50, 1.50, 1.05], np.float32)          # warm source seen through the melt (reflected by the floor)
WARM = np.array([1.0, 0.50, 0.20], np.float32)        # colour of the warm key on bare steel
PARAMS.update(beer_lambert_alpha=ALPHA.tolist(), scatter=SCAT.tolist(), source=E.tolist(), warm_key=WARM.tolist(),
              refraction_gain_px=40.0, ior_note="PS n~1.59; displacement = 40 px x surface gradient")

def plane(t, k, boil=1.0):
    """plane-space linear RGB at shot time t (Sh3b clock; t<0 = full), frame index k (boil on twos)."""
    tw = k // 2
    eta = boil * (0.10 * noise_bank[tw % 8] + 0.03 * noise_fine[(tw * 3) % 8])          # in shot seconds
    osc = np.zeros_like(Tn)
    for ci in cav_info:                                   # SCION #6: partials p*w_i, 2:3 chain between cavities
        m = part == ci["id"]
        wi = 2 * math.pi * 0.42 * (1.5 ** (ci["id"] % 2)) * (1 + ci["id"] // 2 * 0.5)
        th = theta_cav[m]
        osc[m] = sum((0.05 / p) * np.sin(p * 3 * th + p * wi * (tw * 2 / 24) + ci["id"]) for p in (1, 2, 3))
    run = part == 4
    osc[run] = 0.03 * np.sin(Tn[run] * 60 - 2 * math.pi * 0.9 * (tw * 2 / 24))
    f = (t_drain + boil * (eta + osc)) - t             # > 0: melt still there
    present = (f > 0) & mask
    # thickness: full depth behind the front, thinning to a film at the meniscus (rounded contact)
    h = depth * (1 - np.exp(-np.clip(f, 0, None) / 0.12))
    h = np.where(present, h, 0)
    # residual wet film: decays over ~1 s to a lasting thin coat (a real cavity stays wet with melt)
    age = np.clip(t - t_drain, 0, None)
    # (the lasting coat clings where the walls meet the floor and in the rib grooves)
    wet = np.where(mask & ~present, depth * (0.035 * (0.25 + 2.2 * cling) + 0.06 * np.exp(-age / 0.9)), 0)
    ripple = 0.035 * noise_fine[(tw * 5 + 3) % 8] * (h > 0.05) * boil
    hs = cv2.GaussianBlur(h + wet + ripple, (0, 0), 2.2)
    gy, gx = np.gradient(hs)
    ref = 40.0
    drop = depth * 5.0
    mapx = (xx - ref * gx).astype(np.float32)
    mapy = (yy - ref * gy - drop).astype(np.float32)
    floor = cv2.remap(steel_t, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    floor_l = floor.mean(-1, keepdims=True)
    hh = h + wet
    th2 = 2 * np.maximum(hh, 0.14)[..., None]
    trans = np.exp(-ALPHA * th2)
    fl = np.clip((floor_l - 0.55) * 1.6 + 0.55, 0.08, 1.3)
    rad = E * (0.25 + 1.15 * fl) * trans * 0.95 + SCAT * (1 - np.exp(-3 * th2))
    film = smoothstep(0.0, 0.10, hh)[..., None]
    graze = 1 - 0.65 * wall[..., None]                 # grazing walls reflect steel, not light: no glow outline
    rad_melt = rad * film * graze * present[..., None]
    # the lasting coat in an emptied hollow: seen at a longer optical path (grazing film on the walls), dim warm red-amber
    rad_w = E * (0.25 + 1.15 * fl) * np.exp(-ALPHA * 2 * np.maximum(hh, 0.45)[..., None]) * 0.95
    rad_wet = rad_w * film * graze * 0.45 * ((wet > 0.002) & ~present)[..., None]
    nl = np.sqrt(gx ** 2 + gy ** 2 + 1e-4)
    spec = np.clip(-(gx * 0.6 + gy * 0.8) / nl, 0, 1) ** 5 * smoothstep(0.003, 0.015, nl) * 0.75
    spec = spec * (hh > 0.003)
    em = rad_melt.astype(np.float32)
    sm = cv2.resize(em, (PW // 4, PH // 4), interpolation=cv2.INTER_AREA)
    spill = 0.08 * cv2.GaussianBlur(sm, (0, 0), 6) + 1.1 * cv2.GaussianBlur(sm, (0, 0), 22)
    spill = cv2.resize(spill, (PW, PH), interpolation=cv2.INTER_LINEAR)
    # steel: very low warm ambient + raking warm key on walls + spill * albedo
    base = steel * WARM * (0.075 + 0.09 * lam[..., None] * wall[..., None])
    empty = mask & ~present
    hollow = steel_t.mean(-1, keepdims=True) * WARM * (0.03 + 0.55 * (lam * wall)[..., None] + 0.40 * facing[..., None]
                               + 0.03 * ((part >= 0) & (part <= 3))[..., None]) * empty[..., None]
    lit = base * (~mask)[..., None] + hollow + floor * 0.03 * mask[..., None]
    lit = lit + spill * steel_t * 2.6 * (1 - 0.6 * present[..., None])
    col = np.where(present[..., None], rad_melt, lit) + rad_wet
    col = col + spec[..., None] * np.array([1.0, 0.80, 0.55], np.float32)
    return col, present

# ------------------------------------------------------------------ camera ---
def cam_matrix(pitch_deg, yaw_deg, roll_deg, dist, tgt_xy, fpx=1020.0):
    pitch, yaw, roll = map(math.radians, (pitch_deg, yaw_deg, roll_deg))
    tgt = np.array([tgt_xy[0], tgt_xy[1], 0.0])
    cp, sp_, cy, sy, cr, sr = math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw), math.cos(roll), math.sin(roll)
    cpos = tgt + dist * np.array([sy * sp_, cy * sp_, -cp])   # viewer on the -z side of the plate face
    f = tgt - cpos; f /= np.linalg.norm(f)
    up0 = np.array([0, -1.0, 0]) if pitch_deg > 1e-3 else np.array([0, -1.0, 0])
    r_ = np.cross(f, up0)
    if np.linalg.norm(r_) < 1e-6:
        r_ = np.array([1.0, 0, 0])
    r_ /= np.linalg.norm(r_)
    u_ = np.cross(r_, f)
    r2 = cr * r_ + sr * u_; u2 = -sr * r_ + cr * u_
    R = np.stack([r2, -u2, f])
    tvec = -R @ cpos
    K = np.array([[fpx, 0, BW / 2], [0, fpx, BH / 2], [0, 0, 1]])
    Hm = K @ np.column_stack([R[:, 0], R[:, 1], tvec])
    return Hm, R, tvec

FPX = 1020.0
HOLD_DIST = FPX * S / CAM_HOLD["zoom"]           # frontal view at sh2b_hold scale
HOLD_TGT = P(CAM_HOLD["centre"])

def lerp(a, b, x):
    return a + (b - a) * x

def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def camera(film_t):
    """Sh3a: frontal = sh2b_hold until 18.00 s (the dissolve), then a slow tilt toward 3/4.
       Sh3b (after cut C2 at 20.80): closer tilted 3/4 view gliding, as in the approved test shot."""
    if film_t < T0_3B:
        x = ease((film_t - 18.0) / (T0_3B - 18.0))
        pitch = lerp(0.0, 16.0, x); yaw = lerp(0.0, -3.0, x); roll = lerp(0.0, -2.0, x)
        dist = lerp(HOLD_DIST, HOLD_DIST * 0.93, x)
        tgt = HOLD_TGT + np.array([0, -10.0]) * x
        return cam_matrix(pitch, yaw, roll, dist, tgt)
    x = ease((film_t - T0_3B) / 6.8)
    hubp = P([0, 0])
    tgt = hubp + np.array([lerp(40.0, 55.0, x), lerp(70.0, 50.0, x)])
    return cam_matrix(lerp(50.0, 46.0, x), lerp(-9.0, -4.0, x), lerp(-6.0, -4.5, x), lerp(1230.0, 1110.0, x), tgt)

def zdepth(Hm, R, tvec):
    Hi = np.linalg.inv(Hm)
    by, bx = np.mgrid[0:BH, 0:BW].astype(np.float64)
    pts = Hi @ np.stack([bx.ravel(), by.ravel(), np.ones(bx.size)])
    X = pts[0] / pts[2]; Y = pts[1] / pts[2]
    z = R[2, 0] * X + R[2, 1] * Y + tvec[2]
    return z.reshape(BH, BW).astype(np.float32), X.reshape(BH, BW), Y.reshape(BH, BW)

byy, bxx = np.mgrid[0:BH, 0:BW].astype(np.float32)
def practicals(film_t):
    """two defocused blue practicals on their own plane (multiplane layer 0), 0.3x drift; same lamps as U2's"""
    dx = -14 * ease((film_t - 17.6) / 10.0)
    disc = np.exp(-(((bxx - (128 + dx)) ** 2 + (byy - 78) ** 2) / (2 * 54 ** 2)) ** 2.2)
    bar = np.exp(-((np.clip(np.abs(bxx - (700 + dx)) - 160, 0, None) / 34) ** 2 + ((byy - 34) / 16) ** 2) ** 1.6)
    c1 = np.array([0.025, 0.14, 0.36], np.float32); c2 = np.array([0.05, 0.15, 0.36], np.float32)
    return 0.78 * disc[..., None] * c1 + 0.72 * bar[..., None] * c2

def rolloff(img):
    """the shared warm-highlight roll-off used by the cutout unit (knee 0.66): no whites"""
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    k = 0.66; tgt = np.where(lum > k, k + 0.15 * np.tanh((lum - k) / 0.15), lum)
    return np.clip(img * (tgt / np.maximum(lum, 1e-4))[..., None], 0, 1)

def band(film_t, k):
    t = film_t - T0_3B
    boil = 1.0 if t >= 0 else 0.35                      # Sh3a: full mould, surface only trembles
    col, present = plane(max(t, -1.0) if t >= 0 else -1.0, k, boil)
    Hm, R, tvec = camera(film_t)
    img = cv2.warpPerspective(col, Hm, (BW, BH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    inside = cv2.warpPerspective(np.ones((PH, PW), np.float32), Hm, (BW, BH), flags=cv2.INTER_LINEAR)
    z, X, Y = zdepth(Hm, R, tvec)
    # plate edge chamfer catching the blue practicals; faint blue sheen on the far plate
    chamfer = np.exp(-((Y - 6) / 5) ** 2) * (X > 0) * (X < PW)
    img = img + chamfer[..., None].astype(np.float32) * np.array([0.02, 0.06, 0.15], np.float32)
    sheen = np.clip(1 - Y / (PH * 0.55), 0, 1) ** 2 * inside
    img = img + sheen[..., None] * np.array([0.004, 0.016, 0.05], np.float32)
    pr = practicals(film_t)
    # the same blue lamps reflected by the polished plate (their light on the steel, real texture modulates it)
    stex = cv2.warpPerspective(steel_t.mean(-1), Hm, (BW, BH), flags=cv2.INTER_LINEAR)
    img = img * inside[..., None] + pr * (1 - inside[..., None]) + 1.15 * cv2.GaussianBlur(pr, (0, 0), 4) * (stex[..., None] / 0.62) * inside[..., None]
    # thin-lens focus: Sh3b pulls from the far cavity (first to empty) to the sprue; Sh3a is nearly flat
    if t >= 0:
        far = cav_info[order_empty[0]]["c"]
        x = ease((t - 0.3) / 4.6)
        fp = (1 - x) * far + x * hub
        aper = 26.0
    else:
        fp = HOLD_TGT; aper = 26.0
    zf = R[2, 0] * fp[0] + R[2, 1] * fp[1] + tvec[2]
    coc = np.abs(1 / z - 1 / zf) * zf * aper
    coc = np.where(inside > 0.5, coc, 7.0)
    sig = np.array([0, 1.6, 3.4, 6.5], np.float32)
    levels = [img] + [cv2.GaussianBlur(img, (0, 0), s) for s in sig[1:]]
    c = np.clip(coc, 0, 6.5)
    idx = np.clip(np.searchsorted(sig, c) - 1, 0, 2)
    wgt = (c - sig[idx]) / (sig[idx + 1] - sig[idx])
    lo = np.choose(idx[..., None].repeat(3, -1), levels[:3])
    hi = np.choose(idx[..., None].repeat(3, -1), levels[1:])
    out = lo * (1 - wgt[..., None]) + hi * wgt[..., None]
    out = np.clip(out, 0, None)
    # the one physical bloom shared with the cutout unit (halation of the amber cores)
    lum = out @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = out * np.clip((lum - 0.45) / 0.3, 0, 1)[..., None]
    out = out + 0.22 * cv2.GaussianBlur(hot, (0, 0), 5) + 0.10 * cv2.GaussianBlur(hot, (0, 0), 16)
    return (rolloff(out) * 255 + 0.5).astype(np.uint8)

# ------------------------------------------------------------------ checks ---
def ring_world_mask(ci):
    """U2's Sh2b hold silhouette of ring ci: piece alpha, unrotated, ellipse centre at home (plane coords)"""
    rg = GEO["rings"][ci["id"]]
    name = Path(rg["loose_piece"]).stem
    a = cv2.imread(str(CUT / "pieces" / f"{name}.png"), cv2.IMREAD_UNCHANGED)[..., 3]
    b0 = BBOX[name]; e = rg["ring_ellipse_src"]
    pv = np.array([e["cx"] - b0[0], e["cy"] - b0[1]])
    M = np.array([[S, 0, ci["c"][0] - S * pv[0]], [0, S, ci["c"][1] - S * pv[1]]], np.float32)
    return cv2.warpAffine(a, M, (PW, PH), flags=cv2.INTER_LINEAR) > 127

def iou_report():
    res = []
    for ci in cav_info:
        rm = ring_world_mask(ci)
        cm = cav_masks[ci["id"]]
        res.append(dict(ring=ci["ring"], cavity=ci["id"], piece=ci["piece"],
                        iou=round(float((rm & cm).sum() / (rm | cm).sum()), 4)))
    return res

def flip_iou():
    hx, hy = int(round(hub[0])), int(round(hub[1]))
    def f(axis):
        m = mask
        if axis == 1:
            w = min(hx, m.shape[1] - hx); a = m[:, hx - w:hx + w]; b = a[:, ::-1]
        else:
            h = min(hy, m.shape[0] - hy); a = m[hy - h:hy + h]; b = a[::-1]
        return round(float((a & b).sum() / (a | b).sum()), 4)
    return f(1), f(0)
