# compose.py -- U1 world unit: SCION #44 multiplane scene graph + test frames (wide, close) + world-sheet.jpg.
# Usage: python3 -I compose.py <world media dir> <swarm dir>
# Projection (dolly + lateral camera; P2 = focus plane, depth z = 1):
#   camera state (X, Y, D): lateral offset in P2 px and forward travel in units of the P2 depth.
#   a plane at depth z magnifies by m = z / (z - D) and shifts laterally by (X, Y) / z  (parallax ratio = 1/z).
#   screen = O + m * (p - O - (X, Y) / z),  O = picture centre (400, 270).
# Ratios 1/z: P0 0.15, P1 0.35, P2 1.0, P3 1.5, P4 2.0. A plane with z <= D is behind the camera and is not drawn;
# close framings replace it with "near dressing" pieces laid in screen space (declared, not hidden).
import sys, json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

WM, SW = sys.argv[1], sys.argv[2]
CUT = f"{WM}/cut"; TS = f"{WM}/../test-shot"
PW, PH = 800, 540
O = np.float32([400, 270])
Z = dict(P0=1 / 0.15, P1=1 / 0.35, P2=1.0, P3=1 / 1.5, P4=1 / 2.0)
MAXUP = 1.6


def gblur(a, s):
    return a if s <= 0 else cv2.GaussianBlur(a, (0, 0), s)


def piece(name):
    a = np.asarray(Image.open(f"{CUT}/{name}.png").convert("RGBA"), np.float32)
    return a[..., 0], a[..., 3] / 255


PIECES = {}


def get(name):
    if name not in PIECES: PIECES[name] = piece(name)
    return PIECES[name]


UPS = []


def place(C, name, z, cam, xy, s, blur=0.0, gain=1.0, flip=False, rot=0.0, label=None):
    """xy, s: top-left and scale (source px -> P2 px) at the wide framing (cam 0,0,0)."""
    X, Y, D = cam
    if z <= D + 1e-6: return
    m = z / (z - D)
    sc = s * m
    UPS.append((label or name, round(sc, 3)))
    assert sc <= MAXUP + 1e-6, (name, sc)
    L, A = get(name)
    if flip: L, A = L[:, ::-1], A[:, ::-1]
    if rot:
        h, w = L.shape; M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
        c, s_ = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * s_ + w * c), int(h * c + w * s_)
        M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
        L = cv2.warpAffine(L, M, (nw, nh), flags=cv2.INTER_CUBIC); A = cv2.warpAffine(A, M, (nw, nh), flags=cv2.INTER_CUBIC)
    p = O + m * (np.float32(xy) - O - np.float32([X, Y]) / z)
    # resample the source straight into the picture (one resampling; INTER_AREA when shrinking)
    T = np.float32([[sc, 0, p[0]], [0, sc, p[1]]])
    interp = cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC
    if sc < 1:   # area-average first (INTER_AREA is not supported by warpAffine), then place with a sub-pixel shift
        w2, h2 = max(1, int(round(L.shape[1] * sc))), max(1, int(round(L.shape[0] * sc)))
        L = cv2.resize(L, (w2, h2), interpolation=cv2.INTER_AREA); A = cv2.resize(A, (w2, h2), interpolation=cv2.INTER_AREA)
        T = np.float32([[1, 0, p[0]], [0, 1, p[1]]])
    Lw = cv2.warpAffine(L * A, T, (PW, PH), flags=cv2.INTER_LINEAR, borderValue=0)
    Aw = cv2.warpAffine(A, T, (PW, PH), flags=cv2.INTER_LINEAR, borderValue=0)
    if blur > 0: Lw, Aw = gblur(Lw, blur), gblur(Aw, blur)
    Lw = Lw / np.maximum(Aw, 1e-4) * gain
    C[:] = C * (1 - Aw) + np.clip(Lw, 0, 255) * Aw


# ---------------- handmade P2 objects ----------------
_card = np.asarray(Image.open(f"{TS}/paper/Cardboard_546867_jpg.jpg").convert("L"), np.float32)
_hp = _card - gblur(_card, 6); CARD_HP = np.clip(_hp / (_hp.std() + 1e-6), -3, 3)


def card_tex(h, w, seed):
    r = np.random.default_rng(seed); y0 = r.integers(0, CARD_HP.shape[0] - h); x0 = r.integers(0, CARD_HP.shape[1] - w)
    return CARD_HP[y0:y0 + h, x0:x0 + w]


def project_pt(p, cam, z=1.0):
    X, Y, D = cam; m = z / (z - D)
    return O + m * (np.float32(p) - O - np.float32([X, Y]) / z), m


def poly_mask(pts, feather=0.8):
    m = np.zeros((PH, PW), np.uint8); cv2.fillPoly(m, [np.int32(np.round(pts * 4))], 255, cv2.LINE_AA, shift=2)
    return gblur(m.astype(np.float32) / 255, feather)


def plank(C, cam, occupant_u=None, defl=0.0, thick=12, seed=700):
    """pale scored card, a 2-segment polyline bent under the occupant."""
    p0, m = project_pt((170, 392), cam); p1, _ = project_pt((690, 384), cam)
    u = 0.5 if occupant_u is None else occupant_u
    k = p0 + (p1 - p0) * u + np.float32([0, defl * m])
    th = thick * m
    top = np.float32([p0, k, p1]); bot = top + np.float32([0, th])
    pts = np.concatenate([top, bot[::-1]])
    A = poly_mask(pts)
    ys, xs = np.nonzero(A > 0.01)
    if not len(xs): return
    tex = np.zeros((PH, PW), np.float32)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    tex[y0:y1, x0:x1] = card_tex(y1 - y0, x1 - x0, seed)
    # tone: lit top edge (overcast top light) L~214, face L~188 darkening to 150 at the underside; card fibre +/-4 %
    yy = np.arange(PH)[:, None].astype(np.float32)
    ytop = np.interp(np.arange(PW), top[:, 0], top[:, 1]).astype(np.float32)[None, :]
    f = np.clip((yy - ytop) / max(th, 1), 0, 1)
    tone = np.where(f < 0.18, 214, 196 - 46 * f) * (1 + 0.04 * tex)
    # scored grain lines (handmade: knife scoring along the plank)
    for j in range(1, 4):
        yl = ytop + th * (0.25 * j)
        tone = np.where(np.abs(yy - yl) < 0.6 * m, tone * 0.86, tone)
    C[:] = C * (1 - A) + tone * A


def liana(C, cam, hand=None, seed=650):
    """twisted-paper cord (handmade): two strands twisting around the catenary-like line."""
    a, m = project_pt((-40, 40), cam); b, _ = project_pt((860, 20), cam)
    mid = project_pt((410, 118), cam)[0] if hand is None else project_pt(hand, cam)[0]
    t = np.linspace(0, 1, 400)
    # quadratic through a, mid, b
    P = ((1 - t) ** 2)[:, None] * a + (2 * (1 - t) * t)[:, None] * (2 * mid - (a + b) / 2) + (t ** 2)[:, None] * b
    r = 3.2 * m
    d = np.gradient(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    lay = np.zeros((PH, PW), np.float32); tone = np.zeros((PH, PW), np.float32)
    for k, (ph, tn) in enumerate(((0, 70), (math.pi, 104))):
        off = np.sin(t * 90 + ph)[:, None] * r * 0.45
        Q = P + nrm * off
        for i in range(len(Q) - 1):
            cv2.line(lay, tuple(np.int32(Q[i] * 4)), tuple(np.int32(Q[i + 1] * 4)), 1.0, max(1, int(r * 1.2)), cv2.LINE_AA, shift=2)
            cv2.line(tone, tuple(np.int32(Q[i] * 4)), tuple(np.int32(Q[i + 1] * 4)), tn + 30 * max(0, math.cos(t[i] * 90 + ph)), max(1, int(r * 1.2)), cv2.LINE_AA, shift=2)
    lay = np.clip(lay, 0, 1)
    C[:] = C * (1 - lay) + tone * lay


def water(C, cam, water_y, t, wide=True):
    """flood water: foraged plate W_flood_trunk (+ archive ripple motion in the wide), with the jungle mirrored above."""
    top, m = project_pt((0, water_y), cam)
    top = int(round(top[1]))
    if top >= PH: return top
    L, _ = get("W_flood_trunk")
    s = 0.5 * m
    assert s <= MAXUP
    UPS.append(("W_flood_trunk", round(s, 3)))
    flow = (t * 6.0 * m)                                              # the current drifts R->L at 6 px/s (P2)
    X, Y, D = cam
    x0 = (O[0] + m * (0 - O[0] - X)) - flow
    Wp = cv2.resize(L, (int(L.shape[1] * s), int(L.shape[0] * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    Wp = np.concatenate([Wp, Wp[:, ::-1]], 1)                           # mirror-repeat for the drift (declared)
    hh = PH - top
    xs = (np.arange(PW) - x0).astype(int) % Wp.shape[1]
    rows = Wp[np.clip(np.arange(hh) + 0, 0, Wp.shape[0] - 1)][:, xs]
    # reflection of what stands above the water line (the jungle composited so far), darkened and rippled
    src = C[max(top - hh, 0):top][::-1].copy()
    if src.shape[0] < hh: src = np.concatenate([src, np.repeat(src[-1:], hh - src.shape[0], 0)], 0)
    ph = math.floor(t * 12) / 12
    for yy in range(hh):
        src[yy] = np.roll(src[yy], int(round((1 + yy * 0.03) * math.sin(yy * 0.21 + ph * 7))), axis=0)
    out = rows * 0.68 * 1.08 + gblur(src, 1.0) * 0.32
    if wide:
        fr = int(t * 24) % 120; fr = fr if fr < 60 else 119 - fr     # ping-pong of the 2.5 s archive clip (declared)
        a = np.asarray(Image.open(f"{WM}/water_motion/shock_troops_{fr + 1:03d}.png").convert("L"), np.float32)[120:240]
        mean = RIPPLE_MEAN
        mod = (a - mean) / 255.0
        mod = cv2.resize(mod, (int(320 * 1.6), int(120 * 1.6)), interpolation=cv2.INTER_CUBIC)
        UPS.append(("water_motion shock_troops", 1.6))
        mod = np.concatenate([mod, mod[:, ::-1]], 1)[:, :PW]
        mh = min(hh, mod.shape[0])
        out[:mh] = out[:mh] * (1 + 0.9 * mod[:mh])
    out[:3] = out[:3] * 0.7 + 182 * 0.3                                  # wet meniscus line along the banks/plank
    C[top:] = np.clip(out, 0, 255)
    return top


_rm = [np.asarray(Image.open(f"{WM}/water_motion/shock_troops_{k:03d}.png").convert("L"), np.float32)[120:240] for k in range(1, 61)]
RIPPLE_MEAN = np.mean(_rm, 0)


def bank(C, cam, poly_world, name, xy, s, gain=1.0, seed=0, flip=False, edge_dark=0.35):
    """foraged mud-bank photograph clipped to a torn bank polygon (the tear is handmade; the surface is photographic)."""
    pts = np.float32([project_pt(p, cam)[0] for p in poly_world])
    A = poly_mask(pts, 1.0)
    T = np.zeros((PH, PW), np.float32)
    tmp = np.zeros((PH, PW), np.float32) + 58          # wet mud under any gap in the photograph
    place(tmp, name, 1.0, cam, xy, s, flip=flip, gain=gain, label=f"bank surface {name}")
    h = get(name)[0].shape[0] * s                         # second course of the same photograph below (declared repeat)
    place(tmp, name, 1.0, cam, (xy[0] - 140, xy[1] + h - 6), s, flip=not flip, gain=gain * 0.9, label=f"bank surface {name} (2nd course)")
    # torn-edge darkening: wet mud is darker along the waterline and the top lip catches light
    e = gblur((A > 0.5).astype(np.float32), 4)
    tmp = tmp * (1 - edge_dark * np.clip((1 - e) * 2, 0, 1))
    C[:] = C * (1 - A) + tmp * A


def stats(img):
    a = np.asarray(img, np.float32)
    L = a @ np.float32([0.299, 0.587, 0.114]) if a.ndim == 3 else a
    p = [int(round(v)) for v in np.percentile(L, [1, 5, 25, 50, 75, 95, 99])]
    gx = np.abs(np.diff(L, axis=1))[:-1]; gy = np.abs(np.diff(L, axis=0))[:, :-1]
    rb = float(np.abs(a[..., 0] - a[..., 2]).mean()) if a.ndim == 3 else 0.0
    rows = [int(round(v)) for v in L.reshape(6, -1).mean(1)] if L.shape[0] % 6 == 0 else [int(round(L[i * L.shape[0] // 6:(i + 1) * L.shape[0] // 6].mean())) for i in range(6)]
    return dict(p1_5_25_50_75_95_99=p, below60_pct=round(float((L < 60).mean() * 100), 1), above200_pct=round(float((L > 200).mean() * 100), 1),
                mean_abs_R_minus_B=round(rb, 2), mean_gradient=round(float((gx + gy).mean()), 2), row_means_top_to_bottom=rows)


# ======================= SCENE GRAPH =======================
BANK_PIECE = os.environ.get("BANK_PIECE", "B_litter_ficus")
BANK_S = float(os.environ.get("BANK_S", "0.5"))
# depth blur sigma (px) per plane and framing: rises with |1 - 1/z| away from the P2 focus plane; close = shallower focus
BLUR = dict(wide=dict(P0=1.0, P1=0.5, P2=0.0, P3=0.9, P4=1.5), close=dict(P0=1.1, P1=0.6, P2=0.0, near=1.0, near_fg=1.8))
LAYOUT = [   # (plane, piece, wide top-left xy, wide scale, extra)  -- drawn in list order within each depth group
    ("P0", "P0b_forest", (-40, -120), 0.62, dict(gain=0.80, label="P0 far forest wall (Sinharaja, left 78 %)")),
    ("P0", "P0_far", (330, -190), 0.62, dict(gain=0.85, label="P0 giant buttress trunk + wall (right)")),
    ("P1", "P1c_flood_trunk", (585, -60), 0.66, dict(gain=1.0, label="P1 fluted trunk standing in the flood (right)")),
    ("P1", "P1d_liana", (300, -60), 0.42, dict(gain=0.75, label="P1 hanging liana (Sinharaja)")),
    ("P1", "P3b_treefern_mass", (150, 262), 0.70, dict(gain=1.03, label="P1 lit tree-fern mass on the far bank")),
    ("P1", "P1_ficus_roots", (-250, -95), 0.44, dict(gain=1.04, label="P1 Ficus buttress/root wall (left of centre)")),
    ("P3", "P3c_leaves", (560, -330), 0.42, dict(gain=0.80, label="P3 Colocasia heart leaves, top right")),
    ("P3", "P3d_fern_bw", (-200, -330), 0.42, dict(gain=0.90, label="P3 dark tree-fern fronds, top left")),
    ("P4", "P4_root_diag", (-300, 438), 0.66, dict(gain=0.92, flip=True, label="P4 root diagonal, low left")),
]
BANK_XY_F = tuple(json.loads(os.environ.get("BANK_XY_F", "[560, 374]")))
BANK_XY_N = tuple(json.loads(os.environ.get("BANK_XY_N", "[-300, 384]")))
N_BANK = [(-60, 396), (40, 389), (120, 388), (172, 392), (200, 398), (226, 418), (236, 440), (214, 470), (230, 520), (210, 560), (-60, 560)]
F_BANK = [(688, 384), (700, 391), (740, 380), (780, 376), (860, 380), (860, 560), (716, 560), (700, 500), (712, 450), (696, 420)]


def cam_glide(t):        # L-S1: lateral glide R->L, 60 px at P2 over 3 s
    u = min(max(t / 3.0, 0), 1); u = u * u * (3 - 2 * u); return (30 - 60 * u, 0.0, 0.0)


def cam_push(t, dur=5.5, target=(300, 380)):   # L-S4: push-in 8 % at P2 toward the plank foot region
    u = min(max(t / dur, 0), 1); u = u * u * (3 - 2 * u)
    M = 1 + 0.08 * u; D = 1 - 1 / M
    # keep `target` fixed on screen: O + M (target - O - X) = target  ->  X = (target - O)(1 - 1/M)
    X = (np.float32(target) - O) * (1 - 1 / M)
    return (float(X[0]), float(X[1]), D)


def cam_close(centre, M):
    D = 1 - 1 / M
    X = np.float32(centre) - O          # centre of the world window maps to O
    return (float(X[0]), float(X[1]), D)


CLOSE = {
    "L-S5": dict(centre=(205, 330), M=3.0, why="plank foot: B kneels at x 196, the shoe arrives at (214,410); B's head ~0.25 H once the puppet's head is 42 px at the wide scale"),
    "E-S4": dict(centre=(205, 330), M=3.0, why="= L-S5 framing (alternate equivalence)"),
    "L-S6": dict(centre=(140, 250), M=2.85, why="two-shot B (x 120-196) and C (x 150) on the N bank; C head >= 0.22 H"),
}
NEAR_DRESS = {   # close framings: the camera has passed P3/P4; near pieces re-laid in screen space (declared)
    "L-S5": [("P3_treefern", (590, -20), 0.62, dict(gain=0.98, blur="near", label="near: lit tree-fern crown, right edge (as the reference's fern at right)")),
             ("P3c_leaves", (-170, -260), 0.40, dict(gain=0.78, blur="near", label="near: heart leaf, top left (dark canopy)")),
             ("P4_root_diag", (-330, 380), 0.95, dict(gain=0.86, blur="near_fg", flip=True, label="near: root diagonal across the low left"))],
}
NEAR_DRESS["E-S4"] = NEAR_DRESS["L-S5"]
NEAR_DRESS["L-S6"] = [("P3_treefern", (600, 10), 0.60, dict(gain=0.95, blur="near", label="near fern right")),
                      ("P3d_fern_bw", (-330, -260), 0.62, dict(gain=0.85, blur="near", label="near dark fronds top left")),
                      ("P4_root_diag", (-260, 360), 0.95, dict(gain=0.86, blur="near_fg", flip=True, label="near root diagonal low left"))]


def render(cam, t=0.0, framing="wide", shot=None, water_y=416.0, occupant_u=None, defl=0.0, hand=None, p2_cb=None):
    del UPS[:]
    C = np.zeros((PH, PW), np.float32) + 70
    B = BLUR["wide" if framing == "wide" else "close"]
    for plane, name, xy, s, ex in LAYOUT:
        if plane in ("P3", "P4"): continue
        place(C, name, Z[plane], cam, xy, s, blur=B[plane], gain=ex.get("gain", 1), flip=ex.get("flip", False), label=ex.get("label"))
    water(C, cam, water_y, t, wide=(framing == "wide"))
    bank(C, cam, F_BANK, BANK_PIECE, BANK_XY_F, BANK_S, gain=1.0, seed=2)
    bank(C, cam, N_BANK, BANK_PIECE, BANK_XY_N, BANK_S, gain=0.95, seed=1, flip=True)
    plank(C, cam, occupant_u, defl)
    liana(C, cam, hand)
    if p2_cb is not None: p2_cb(C, cam)      # P2 actors (puppets, bag, shoe) drawn here, before the near planes
    if framing == "wide":
        for plane, name, xy, s, ex in LAYOUT:
            if plane not in ("P3", "P4"): continue
            place(C, name, Z[plane], cam, xy, s, blur=B[plane], gain=ex.get("gain", 1), flip=ex.get("flip", False), label=ex.get("label"))
    else:
        for name, xy, s, ex in NEAR_DRESS[shot]:
            place(C, name, 1.0, (0, 0, 0), xy, s, blur=B[ex["blur"]], gain=ex.get("gain", 1), flip=ex.get("flip", False), label=ex.get("label"))
    return np.clip(C, 0, 255), list(UPS)


def to_rgb(C): return np.repeat(np.clip(C, 0, 255).astype(np.uint8)[..., None], 3, 2)


if __name__ == "__main__":
    os.makedirs(f"{WM}/test", exist_ok=True)
    frames = {}
    wide, ups_w = render(cam_glide(1.5), t=1.5, framing="wide", water_y=416 - 0.5 * 1.5)
    frames["wide_L-S1_t1.5"] = (wide, ups_w)
    close, ups_c = render(cam_close(**{k: CLOSE["L-S5"][k] for k in ("centre", "M")}), t=19.0, framing="close", shot="L-S5", water_y=416 - 0.5 * 19.0)
    frames["close_L-S5_t19.0"] = (close, ups_c)
    out = {}
    for k, (C, ups) in frames.items():
        Image.fromarray(to_rgb(C)).save(f"{WM}/test/{k}.png")
        pb = np.zeros((540, 960, 3), np.uint8) + 0x1b; pb[:, 80:880] = to_rgb(C)
        Image.fromarray(pb).save(f"{WM}/test/{k}_960.png")
        out[k] = dict(stats=stats(to_rgb(C)), plate_scales=ups, max_scale=max(s for _, s in ups))
    ref = Image.open(f"{SW}/../../../assets/references/bunuel.webp").convert("RGB")
    out["reference_bunuel_native_1000x677"] = dict(stats=stats(ref))
    out["reference_bunuel_at_800x541"] = dict(stats=stats(ref.resize((800, 541), Image.LANCZOS)))
    json.dump(out, open(f"{WM}/test/stats.json", "w"), indent=1)
    print(json.dumps({k: v["stats"] | dict(max_scale=v.get("max_scale")) for k, v in out.items()}, indent=0))


def scene_graph():
    planes = {k: dict(depth_z=round(z, 4), parallax_ratio=round(1 / z, 3)) for k, z in Z.items()}
    for k in planes: planes[k]["depth_blur_sigma_px"] = dict(wide=BLUR["wide"][k], close=BLUR["close"].get(k))
    planes["P2"]["contents"] = "water (W_flood_trunk + archive ripple in wides), banks (foraged surface in torn polygon), plank, liana cord, puppets, shoe, bag"
    planes["P3"]["depth_blur_sigma_px"]["close"] = None; planes["P4"]["depth_blur_sigma_px"]["close"] = None
    lay = [dict(plane=p, piece=n, wide_top_left=list(xy), wide_scale=s, **{k: v for k, v in ex.items()}) for p, n, xy, s, ex in LAYOUT]
    cams = {
        "L-S1": dict(kind="lateral glide R->L", function="cam_glide(t)", t_range_local=[0, 3.0], X_from=30, X_to=-30, Y=0, D=0, ease="smoothstep",
                     travel_at_P2_px=60, travel_px_by_plane={k: round(60 / z, 1) for k, z in Z.items()}),
        "E-S1": dict(same_as="L-S1", note="byte-identical frames"),
        "L-S4": dict(kind="push-in 8 % at P2 toward (300,380)", function="cam_push(t, 5.5, (300,380))", t_range_local=[12.5, 18.0],
                     magnification_end_by_plane={k: round(z / (z - (1 - 1 / 1.08)), 4) for k, z in Z.items()}),
        **{k: dict(kind="close (dolly-in reframing of the same world)", centre_world=list(v["centre"]), M_at_P2=v["M"],
                   cam=[round(c, 4) for c in cam_close(v["centre"], v["M"])], why=v["why"],
                   world_window=[v["centre"][0] - 400 / v["M"], v["centre"][1] - 270 / v["M"], v["centre"][0] + 400 / v["M"], v["centre"][1] + 270 / v["M"]],
                   magnification_by_plane={p: (round(z / (z - (1 - 1 / v["M"])), 4) if z > 1 - 1 / v["M"] else "behind camera: replaced by near dressing")
                                           for p, z in Z.items()},
                   near_dressing=[dict(piece=n, screen_top_left=list(xy), scale=s, **ex) for n, xy, s, ex in NEAR_DRESS[k]]) for k, v in CLOSE.items()},
    }
    return dict(projection="screen = O + m (p - O - (X,Y)/z), m = z/(z-D), O=(400,270), picture 800x540 pillarboxed at x=80 in 960x540 (#1b1b1b bars)",
                planes=planes, layout_wide=lay, banks=dict(N=N_BANK, F=F_BANK, surface=BANK_PIECE, scale=BANK_S, xy_N=list(BANK_XY_N), xy_F=list(BANK_XY_F),
                note="foraged surface photograph clipped to a handmade torn polygon; two courses of the same plate (second mirrored) for depth; wet-mud fill 58 under gaps; edge darkening 35 % at the waterline"),
                plank=dict(kind="HANDMADE pale scored card; lit top edge L214, face 196 -> 150; Cardboard-546867 (CC0) fibre +/-4 %", p0=[170, 392], p1=[690, 384], thickness=12),
                liana_cord=dict(kind="HANDMADE twisted-paper cord, two strands (L70 / L104 + 30 sheen), quadratic through (-40,40), hand or (410,118), (860,20)"),
                water=dict(plate="W_flood_trunk (y 80-100 % band of 'Flooded building and tree trunk...', CC BY-SA 4.0) at 0.5 x m, mirror-repeated, drifting R->L 6 px/s",
                           reflection="the composite above the line, mirrored, rippled per row (12 poses/s), 38 % mix",
                           motion="wides only: Shock Troops of Disaster (1938) ripple field, rows 120-240 of the 320x240 clip, x1.6, ping-pong of 60 frames, +/-0.9 modulation",
                           level="world-trace.json water_y(t)"),
                cameras=cams, max_plate_scale=MAXUP,
                invariants=["near planes move more than far ones (ratios 0.15 < 0.35 < 1 < 1.5 < 2.0)", "no plate drawn above 1.6x its downloaded resolution (asserted in place())",
                            "blur only per plane (BLUR table), none on P2", "one monotone curve per plate (plates.py), lighting = uniform per-piece gain"])


if __name__ == "__main__":
    json.dump(scene_graph(), open(f"{SW}/world-scene.json", "w"), indent=1, ensure_ascii=False)
    print("scene graph written")
