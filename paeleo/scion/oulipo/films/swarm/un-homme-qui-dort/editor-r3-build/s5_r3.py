"""S5 FLIGHT-1 (132 frames) and S7 FLIGHT-2 + TAIL (S5's 132 frames byte-identical + 60 held), repair round 2.

Stage: Mydans 2017714056 stairwell (dark flight, lit handrail, balusters, stringer). Static camera (no glide:
the near plane is cut from the same negative, so any relative glide would double the rail's edge).
Climber: the S3/S4 sitter (Bubley 2017862340) -- UB head+torso, TH thigh, SH shin, two leg instances.
SCION-47: footfalls (U2 ledger, pass 20.8/21.35/21.9/22.45/23.0 -> S5 frames 43/56/70/83/96) drive the gait:
  at each footfall a foot plants on the next pair of treads, the body is at its lowest (dip 10 px) and
  then rises; legs are solved by two-bone IK (hip -> knee -> foot), knee forward.
SCION-44: z order far stage < rear leg < torso < near leg < near plane (handrail, balusters, stringer,
  newels). The handrail always occludes the climber: figure-over-rail overlap is measured (must be 0).
Entry (first visible frame) 36 = pass 20.5; gone from frame 108 = pass 23.5 (behind the right newel post).
Run: python3 -I s5_r3.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r3-build")
from ed3 import *  # noqa

Z = np.load(E3 / "json" / "s5r3_pieces.npz")
man = json.loads((E3 / "json" / "s5r3_cut.json").read_text())
VX0, VY0, VS = man["view_to_plate"]["x0"], man["view_to_plate"]["y0"], man["view_to_plate"]["scale"]
REG = man["UB_region_plate"]; LEGR = man["leg_region_plate"]
Hs, Ws = H * SS, W * SS

# ---- stage at render scale ----
stage_g = resample(Z["G"], SS * W / Z["G"].shape[1])
near_a = np.clip(resample(Z["near_a"], SS * W / Z["G"].shape[1]), 0, 1)
near_a[near_a >= 0.995] = 1.0                       # opaque where the cut is opaque (no figure bleed-through)
assert stage_g.shape == (Hs, Ws), stage_g.shape

# ---- climber pieces: one scale (torso hip->crown = 185 screen px), flopped, darkened for the well ----
HIP_V, CROWN_V = (930, 590), (870, 25)
def vpl(p):
    return np.array([VX0 + p[0] * VS, VY0 + p[1] * VS])
torso_len_pl = float(np.linalg.norm(vpl(CROWN_V) - vpl(HIP_V)))
TORSO = 185.0
f = TORSO / torso_len_pl
rs = f * SS
CL_LUT = [(0.0, 0.085), (0.2, 0.125), (0.5, 0.30), (0.8, 0.56), (1.0, 0.72)]   # monotone, recorded
_cl = pchip(*zip(*CL_LUT))


def piece(gray, alpha, org_pl, pts_pl):
    """prescale + flop; returns gray, alpha and the given plate points in the piece's render-scale coords."""
    g = resample(gray.astype(np.float32), rs)[:, ::-1].copy()
    a = resample(alpha.astype(np.float32), rs)[:, ::-1].copy()
    g = _cl(np.clip(g, 0, 1)).astype(np.float32)
    w = g.shape[1]
    out = [np.array([w - 1 - (p[0] - org_pl[0]) * rs, (p[1] - org_pl[1]) * rs]) for p in pts_pl]
    return g, a, out


UB_g, UB_a, (ub_hip, ub_crown) = piece(Z["UB_g"], Z["UB_a"], REG[:2], [vpl(HIP_V), vpl(CROWN_V)])
TH0, TH1 = man["TH_axis_view"]; SH0, SH1 = man["SH_axis_view"]
TH_g, TH_a, (th_hip, th_knee) = piece(Z["Lg"], Z["TH_a"], LEGR[:2], [vpl(TH0), vpl(TH1)])
SH_g, SH_a, (sh_knee, sh_ank) = piece(Z["Lg"], Z["SH_a"], LEGR[:2], [vpl(SH0), vpl(SH1)])
L1 = float(np.linalg.norm(th_knee - th_hip)) / SS
L2 = float(np.linalg.norm(sh_ank - sh_knee)) / SS + 8.0      # + the (hidden) foot
ang = lambda v: float(np.arctan2(v[1], v[0]))
UB_native = ang(ub_crown - ub_hip); TH_native = ang(th_knee - th_hip); SH_native = ang(sh_ank - sh_knee)

# ---- stair geometry (screen px), from the cut ----
RL = man["rail_lines_screen"]
def lin(p, q):
    return lambda x: p[1] + (x - p[0]) * (q[1] - p[1]) / (q[0] - p[0])
rail_top = lin(*RL["top"]); rail_bot = lin(*RL["bottom"]); lstr = lin(*RL["lower_string_top"])
hip_line = lambda x: 0.5 * (rail_top(x) + rail_bot(x)) + 4.0
tread = lambda x: lstr(x) + 14.0                    # treads lie just behind the lower string (feet hidden)

# ---- timing ----
FF = [43, 56, 70, 83, 96]                           # S5 frames of the U2 footfalls (pass 20.8 ... 23.0)
STEP = (FF[-1] - FF[0]) / 4.0
FFX = [FF[0] - 3 * STEP, FF[0] - 2 * STEP, FF[0] - STEP] + FF + [FF[-1] + STEP, FF[-1] + 2 * STEP, FF[-1] + 3 * STEP]
DIP = 10.0
X_A, V = -13.1375, 13.418681640625     # hip x at frame 36, px/frame (bisected: first visible 36, gone at 108)


def sm(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def hip(fi):
    x = X_A + V * (fi - 36)
    bob = DIP * sum(np.exp(-((fi - k) / 2.2) ** 2) for k in FFX)
    return np.array([x, hip_line(x) + bob])


def plant_x(k):
    return X_A + V * (FFX[k] - 36) + 30.0


def foot(fi, leg):
    """leg 0 plants on even FFX indices, leg 1 on odd."""
    ks = [k for k in range(len(FFX)) if k % 2 == leg]
    for a, b in zip(ks, ks[1:]):
        if FFX[a] <= fi < FFX[b]:
            sw0 = FFX[a + 1] + 2 if a + 1 < len(FFX) else FFX[b]      # stance until the other foot lands
            if fi < sw0:
                x = plant_x(a); return np.array([x, tread(x)])
            u = float(sm((fi - sw0) / max(FFX[b] - sw0, 1)))
            x = plant_x(a) + u * (plant_x(b) - plant_x(a))
            return np.array([x, tread(x) - 34.0 * np.sin(np.pi * u)])
    x = plant_x(ks[0] if fi < FFX[0] else ks[-1]); return np.array([x, tread(x)])


def ik(Hp, Fp):
    d = Fp - Hp; dist = float(np.clip(np.linalg.norm(d), 1e-3, L1 + L2 - 0.5))
    a = np.arccos(np.clip((L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist), -1, 1))
    base = ang(d)
    th = base - a                                    # knee forward (+x, direction of travel)
    knee = Hp + L1 * np.array([np.cos(th), np.sin(th)])
    return th, knee, ang(Fp - knee)


def place(g, a, pivot_local, angle, target, shade=1.0):
    c, s_ = np.cos(angle), np.sin(angle)
    Rm = np.array([[c, -s_], [s_, c]])
    t = np.array(target) * SS - Rm @ pivot_local
    M = np.hstack([Rm, t[:, None]])
    gw = cv2.warpAffine(g * shade, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderValue=0)
    aw = cv2.warpAffine(a, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderValue=0)
    return gw, aw


LEAN = np.deg2rad(-8.0)                              # extra forward lean (screen: crown toward +x)
VERT = -np.pi / 2


def frame(fi, diag=False):
    out = stage_g.copy()
    Hp = hip(fi)
    fig_a = np.zeros((Hs, Ws), np.float32)
    layers = []
    for leg, shade in ((1, 0.78), (0, 1.0)):
        th, knee, sh = ik(Hp, foot(fi, leg))
        layers.append(("leg%d" % leg, [place(SH_g, SH_a, sh_knee, sh - SH_native, knee, shade),
                                        place(TH_g, TH_a, th_hip, th - TH_native, Hp, shade)]))
    osc = np.deg2rad(2.0) * sum(np.exp(-((fi - k - 4) / 3.0) ** 2) for k in FFX)
    ub = place(UB_g, UB_a, ub_hip, (VERT + LEAN - osc) - UB_native, Hp)
    # the torso piece stops inside the handrail band (its waist cut is never seen)
    yy = np.arange(Hs, dtype=np.float32)[:, None] / SS
    xx = np.arange(Ws, dtype=np.float32)[None, :] / SS
    keep = (yy <= rail_top(xx) + 14.0) | (xx < 96)
    ub = (ub[0], ub[1] * keep)
    order = [layers[0], ("UB", [ub]), layers[1]]
    for name, pcs in order:
        for g, a in pcs:
            out = g * a + out * (1 - a)
            fig_a = np.maximum(fig_a, a)
    out = stage_g * near_a + out * (1 - near_a)      # near plane over everything
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    g8 = (np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)
    if not diag:
        return g8
    fa = cv2.resize(fig_a, (W, H), interpolation=cv2.INTER_AREA)
    na = cv2.resize(near_a, (W, H), interpolation=cv2.INTER_AREA)
    st8 = (np.clip(cv2.resize(stage_g, (W, H), interpolation=cv2.INTER_AREA), 0, 1) * 255 + 0.5).astype(np.uint8)
    vis = fa * (1 - na)
    full = near_a.reshape(H, SS, W, SS).min(axis=(1, 3)) >= 1.0      # screen px whose render px are all opaque near
    over_rail = int((full & (np.abs(g8.astype(int) - st8.astype(int)) > 0)).sum())
    return g8, {"fig_total": float((fa > 0.02).mean()), "fig_visible": float((vis > 0.02).mean()),
                "fig_over_full_near_px": over_rail, "hip": [round(float(v), 2) for v in Hp]}


if __name__ == "__main__":
    import hashlib
    diag = [frame(fi, True) for fi in range(132)]
    cov = [d[1]["fig_visible"] for d in diag]
    vis = [i for i, c in enumerate(cov) if c > 0]
    print("first visible", vis[0], "last visible", vis[-1])
    frames = [d[0] for d in diag]
    shas5, d5 = write_shot3("S5", iter(frames))
    shas7, d7 = write_shot3("S7", iter(frames + [frames[-1]] * 60), n=192)
    px5 = [hashlib.sha1(f_.tobytes()).hexdigest() for f_ in frames]
    hip_y = [diag[i][1]["hip"][1] - hip_line(diag[i][1]["hip"][0]) for i in range(132)]
    dips = {str(k): round(hip_y[k] - 0.5 * (hip_y[k - 6] + hip_y[k + 6]), 2) for k in FF}
    stats = [frame_stats(frames[i]) for i in (10, 60, 80, 120)]
    rep = {"dir_S5": d5, "dir_S7": d7, "sha1_S5": shas5, "sha1_S7": shas7,
           "S7_first132_equal_S5": shas7[:132] == shas5, "S7_tail_is_S5_last": set(shas7[132:]) == {shas5[-1]},
           "pixel_sha1_S5": px5,
           "figure_visible_coverage": [round(c, 5) for c in cov],
           "figure_total_coverage": [round(d[1]["fig_total"], 5) for d in diag],
           "shadow_coverage": [0.0] * 132,
           "first_visible_frame": vis[0], "last_visible_frame": vis[-1], "gone_from_frame": vis[-1] + 1,
           "figure_over_rail_px_max": max(d[1]["fig_over_full_near_px"] for d in diag),
           "footfall_frames": FF, "dip_px_at_footfalls": dips, "hip_px": [d[1]["hip"] for d in diag],
           "ik": {"L1": round(L1, 1), "L2": round(L2, 1), "knee": "forward", "torso_px": TORSO, "scale_plate_to_screen": round(f, 5)},
           "climber_lut": CL_LUT, "stage_crop": man["crop"], "camera": "static (no glide)", "stats": stats}
    dump(E3 / "json" / "s5_render.json", rep)
    strip = np.hstack([cv2.resize(frames[i], (320, 180)) for i in (20, 40, 50, 60, 70, 80, 95, 110)])
    Image.fromarray(strip).save(E3 / "diag" / "s5_strip.png")
    print(json.dumps({k: rep[k] for k in ("S7_first132_equal_S5", "S7_tail_is_S5_last", "first_visible_frame", "gone_from_frame",
                                         "figure_over_rail_px_max", "dip_px_at_footfalls", "ik")}), stats[1])
