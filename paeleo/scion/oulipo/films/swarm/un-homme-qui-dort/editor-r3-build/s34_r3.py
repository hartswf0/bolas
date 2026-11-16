"""S3 REFUSE + S4 HELD, repair round 1. Same plate (LoC 2017862340, Bubley Jan 1943, master TIFF
8d33583u.tif) and the same SCION-29 pieces U1 cut (u1 json/s34_layers.npz: head, torso, hands, far wall
with flagged fills, his cast-shadow ratio plane), restaged:
  * S3 is now framed on S4's reference layout (pale wall left, head on the boundary, his cast shadow and
    dark suit right/below) instead of the wide wall framing; the glide settles into S4's rest frame, so
    S3 -> S4 is one continuous observation (the cut at 11.5 joins identical framing).
  * E3 head turn toward the sound (frame left) is 9 deg (was 3). It is made as a weighted handle warp
    of the rest composite (the plan's named fallback branch for a seam: SCION-34-style deformation under
    the same handles): head AND its cast shadow on the wall rotate together about the neck pivot
    (weight 1 over the head and shadow, 0 at the collar, shoulders, hands and frame edges), so the
    shadow follows with no reconstructed wall exposed and no seam; it holds and returns at 10.4.
  * Print: one extra monotone neutral curve on the composite (the composite at rest IS the U1-graded
    plate, so plate -> U1 curve -> this curve is still a single monotone curve per plate). It prints the
    dark side deeper and the wall a little lower: frame L 94->57, 226->221, p1/p99 kept.
REPAIR ROUND 2 (r3): the white crown notch / hair halo seen during the turn hold came from the matte edge of
the head piece over U1's filled wall. The glide now settles before the turn (8 px, ease-out over 0.70 s,
frames 0-16, parallax near 1.5x far as before); from frame 17 on, and for all of S4, the base image is the
graded negative itself (no cut edge anywhere), and the E3 turn is the same weighted warp applied to it.
Run: python3 -I s34_r3.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r3-build")
from ed3 import *  # noqa

Z = np.load(U1 / "json" / "s34_layers.npz")
man = json.loads((U1 / "json" / "s34_manifest.json").read_text())
ox, oy = [int(v) for v in Z["origin"]]
PIV = man["neck_pivot_plate"]
OFF = man["head_shadow_offset_plate_px"]
CROP = tuple(man["crops"]["S4"])          # (2620, 1975, 4790, 3196): both shots
LUT_PTS = [(0, 0), (20, 20), (27, 27), (41, 35), (59, 44), (100, 59), (142, 116), (189, 179), (217, 207),
           (226, 221), (235, 236), (241, 243), (255, 250)]
LUT = lut(LUT_PTS)

T_TURN, T_RET = 9.25, 10.4
F_TURN, F_RET = round(T_TURN * FPS) - 204, round(T_RET * FPS) - 204
TURN_DEG, TURN_DX = 9.0, -4.0


def smooth(x):
    return x * x * (3 - 2 * x)


def clamp(x):
    return max(0.0, min(1.0, x))


def head_pose_s3(fi):
    up = smooth(clamp((fi - F_TURN) / 8.0))
    dn = smooth(clamp((fi - F_RET) / 12.0))
    k = up - dn
    return TURN_DEG * k, TURN_DX * k


def pose_rest(fi):
    return 0.0, 0.0


def build(pose_fn):
    cx0, cy0, cx1, cy1 = CROP
    s = W / (cx1 - cx0); rs = s * SS
    org = ((ox - cx0) * s, (oy - cy0) * s)
    piv = ((PIV[0] - cx0) * s, (PIV[1] - cy0) * s)
    spiv = (piv[0] + OFF[0] * s, piv[1] + OFF[1] * s)
    R = lambda a: resample(a.astype(np.float32), rs)
    def head(fi):
        ang, dx = pose_fn(fi); return (dx, 0.0, ang, piv)
    def shadow(fi):
        ang, dx = pose_fn(fi); return (dx, 0.0, ang, spiv)
    layers = [
        Layer("wall_far", R(Z["far"]), np.ones_like(R(Z["far"])), 1.0, 0, org=org, role="far: pale wall (distant witness)"),
        Layer("head_shadow", R(Z["ratio"]), R(Z["shadow_a"]), 1.0, 1, mode="multiply", org=org, role="cast-shadow plane on the wall: the double (turns with the head in turn_warp)"),
        Layer("torso", R(Z["torso_img"]), R(Z["torso_a"]), 1.2, 2, org=org, role="figure: torso"),
        Layer("head", R(Z["head_img"]), R(Z["head_a"]), 1.2, 3, org=org, role="figure: head (E3 by weighted warp, see turn_warp)"),
        Layer("hands", R(Z["hands_img"]), R(Z["hands_a"]), 1.5, 4, org=org, role="near: clasped hands (confine/shield)"),
    ]
    return layers, s, piv, spiv


def compose2x(layers, fi, cam_fn):
    """lib.compose without the final downsample (float, 2x screen)."""
    Hs, Ws = H * SS, W * SS
    out = np.zeros((Hs, Ws), np.float32)
    cx, cy, zoom, zc = cam_fn(fi)
    for L in sorted(layers, key=lambda l: l.z):
        dx, dy, ang, pv = L.pose(fi)
        M = affine(dx, dy, ang, pv, (L.k * cx, L.k * cy), L.org)
        bm = cv2.BORDER_REPLICATE if L.name.endswith("far") else cv2.BORDER_CONSTANT
        g = cv2.warpAffine(L.gray, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=bm, borderValue=0 if L.mode == "over" else 1)
        a = cv2.warpAffine(L.alpha, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=bm, borderValue=0 if L.mode == "over" else 1)
        out = g * a + out * (1 - a) if L.mode == "over" else out * (1 - a + a * g)
    return out


_YY, _XX = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
HEAD_C, R_FULL, R_ZERO = (650.0, 165.0), 235.0, 330.0     # screen px: weight 1 inside R_FULL of the head/shadow centre
Y_FULL, Y_ZERO = 262.0, 322.0                              # weight 1 above the jaw, 0 at the collar line


def turn_warp(big, ang, dx, piv, camx):
    """Weighted rotation (CCW = toward frame left) of head + cast shadow about the neck pivot."""
    th = np.deg2rad(ang)
    px, py = (piv[0] + camx) * SS, piv[1] * SS
    cx_, cy_ = (HEAD_C[0] + camx) * SS, HEAD_C[1] * SS

    def disp(x, y):
        r = np.hypot(x - cx_, y - cy_)
        w = (1 - smooth_a((r - R_FULL * SS) / ((R_ZERO - R_FULL) * SS))) * (1 - smooth_a((y - Y_FULL * SS) / ((Y_ZERO - Y_FULL) * SS)))
        rx, ry = x - px, y - py
        nx = rx * np.cos(th) + ry * np.sin(th)
        ny = -rx * np.sin(th) + ry * np.cos(th)
        return w * (nx - rx + dx * SS), w * (ny - ry)
    sx, sy = _XX.copy(), _YY.copy()
    for _ in range(5):
        ddx, ddy = disp(sx, sy)
        sx, sy = _XX - ddx, _YY - ddy
    return cv2.remap(big, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def smooth_a(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


GLIDE_END = 17


def cam_s3(fi):
    u = clamp(fi / float(GLIDE_END))
    return (8.0 * (1 - u) ** 3, 0.0, 1.0, (0, 0))


_PLATE = {}


def plate_big():
    """the graded negative itself on the shot's crop, at render scale (U1 curve; identical to the rest composite
    except that it has no matte edges)."""
    if "g" not in _PLATE:
        g, c, rec = graded_plate("2017862340", tuple(man["curve"]["stats_box"]))
        x0, y0, x1, y1 = CROP
        _PLATE["g"] = cv2.resize(g[y0:y1, x0:x1].astype(np.float32), (W * SS, H * SS), interpolation=cv2.INTER_AREA)
    return _PLATE["g"]


def cam_s4(fi):
    return (0.0, 0.0, 1.0, (0, 0))


if __name__ == "__main__":
    out = {"plate": "2017862340", "crop_plate": list(CROP), "print_lut_points": LUT_PTS, "print_lut": LUT.tolist()}
    for shot, cam, pose, n in (("S3", cam_s3, head_pose_s3, 72), ("S4", cam_s4, pose_rest, 180)):
        layers, s, piv, spiv = build(pose)
        cache = {}
        frames = []
        for fi in range(n):
            key = (cam(fi), pose(fi))
            if key not in cache:
                cache.clear()
                big = compose2x(layers, fi, cam) if cam(fi)[0] != 0.0 else plate_big().copy()
                ang = pose(fi)[0]
                if ang != 0.0:
                    big = turn_warp(big, ang, pose(fi)[1], piv, cam(fi)[0] * 1.2)
                small = cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA)
                cache[key] = LUT[(np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)]
            frames.append(cache[key])
        shas, d = write_shot3(shot, iter(frames))
        hb = man["head_bbox_plate"]
        hl = layers[3]
        alpha_mid = layer_alpha_on_screen(hl, F_TURN + 20, cam) if shot == "S3" else None
        out[shot] = {"dir": d, "sha1": shas, "scale_plate_to_screen": round(s, 5),
                     "head_height_frac": round((hb[3] - hb[1]) / (CROP[3] - CROP[1]), 3),
                     "layers": [{"name": L.name, "k": L.k, "z": L.z, "mode": L.mode, "role": L.role} for L in layers],
                     "camera_dx": [round(cam(fi)[0], 3) for fi in range(0, n, 6)],
                     "head_pose_deg_dx": [list(map(lambda v: round(v, 3), pose(fi))) for fi in range(n)],
                     "frame_diff_sum": [int(np.abs(frames[i].astype(int) - frames[i - 1].astype(int)).sum()) for i in range(1, n)]}
        if shot == "S3":
            out["S3"]["parallax_near_over_far"] = 1.5
            out["S3"]["glide_px_far"] = 8.0
            out["S3"]["glide_frames"] = [0, GLIDE_END]
            out["S3"]["base_from_frame_%d" % GLIDE_END] = "graded negative (no cut edges)"
            Image.fromarray(np.hstack([frames[0], frames[F_TURN + 12], frames[50], frames[71]])).resize((1920, 270)).save(E3 / "diag" / "s3_strip.png")
            Image.fromarray(np.hstack([frames[F_TURN - 1], frames[F_TURN + 12]])).save(E3 / "diag" / "s3_turn_pair.png")
    out["E3"] = {"turn_onset_shot_frame": F_TURN, "turn_onset_pass_frame": F_TURN + 204, "turn_onset_t": T_TURN,
                 "return_onset_shot_frame": F_RET, "return_onset_pass_frame": F_RET + 204, "return_onset_t": T_RET,
                 "turn_deg": TURN_DEG, "turn_dx_px": TURN_DX, "rest_after_deg": 0.0,
                 "method": "weighted handle warp of head + cast shadow (fallback branch S3-warp)", "weight": {"head_centre_screen": HEAD_C, "r_full": R_FULL, "r_zero": R_ZERO, "y_full": Y_FULL, "y_zero": Y_ZERO}}
    dump(E3 / "json" / "s34_render.json", out)
    a = np.asarray(Image.open(E3 / "shots" / "S4" / "S4_0084.png"))
    print("S4 stats", frame_stats(a))
    print("S3 stats", frame_stats(np.asarray(Image.open(E3 / "shots" / "S3" / "S3_0071.png"))))
