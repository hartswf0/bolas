"""SCION-44/47 rig for S3 (REFUSE, 72 frames) and S4 (HELD, 180 frames) from cut_s34 pieces."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *

Z = np.load(U1 / "json" / "s34_layers.npz")
man = json.loads((U1 / "json" / "s34_manifest.json").read_text())
ox, oy = [int(v) for v in Z["origin"]]
PIV = man["neck_pivot_plate"]
OFF = man["head_shadow_offset_plate_px"]

# --- E3 action curve (SCION-47): ring 3 at 9.0; attention -> head turn at 9.25 toward frame left
#     (the sound), hold (refusal: no reach), return starting 10.4 to a changed rest (1.0 deg kept).
T_TURN, T_RET = 9.25, 10.4
F_TURN, F_RET = round(T_TURN * FPS) - 204, round(T_RET * FPS) - 204   # S3 starts at pass frame 204
TURN_DEG, REST_DEG, TURN_DX = 3.0, 0.0, -2.0


def head_pose_s3(fi):
    up = smooth(clamp((fi - F_TURN) / 8.0))           # 8 frames (0.33 s) to turn
    dn = smooth(clamp((fi - F_RET) / 10.0))           # 10 frames to return
    ang = TURN_DEG * up - (TURN_DEG - REST_DEG) * dn
    dx = TURN_DX * up - (TURN_DX * (1 - REST_DEG / TURN_DEG)) * dn
    return ang, dx


def smooth(x):
    return x * x * (3 - 2 * x)


def clamp(x):
    return max(0.0, min(1.0, x))


def build(crop, cam_fn, pose_fn):
    cx0, cy0, cx1, cy1 = crop
    s = W / (cx1 - cx0)
    rs = s * SS
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
        Layer("head_shadow", R(Z["ratio"]), R(Z["shadow_a"]), 1.0, 1, mode="multiply", pose=shadow, org=org, role="cast-shadow plane on the wall: the double"),
        Layer("torso", R(Z["torso_img"]), R(Z["torso_a"]), 1.2, 2, org=org, role="figure: torso"),
        Layer("head", R(Z["head_img"]), R(Z["head_a"]), 1.2, 3, pose=head, org=org, role="figure: head (E3)"),
        Layer("hands", R(Z["hands_img"]), R(Z["hands_a"]), 1.5, 4, org=org, role="near: clasped hands (confine/shield)"),
    ]
    return layers, s, piv, spiv


def cam_s3(fi):
    t = fi / FPS
    u = clamp(t / 2.0)                                # settles to rest by 10.5 (local 2.0)
    return (12.0 * (1 - u) ** 3, 0.0, 1.0, (0, 0))


def cam_s4(fi):
    return (0.0, 0.0, 1.0, (0, 0))


def pose_s4(fi):
    return REST_DEG, TURN_DX * (1 - REST_DEG / TURN_DEG)


if __name__ == "__main__":
    out = {}
    for shot, crop, cam, pose, n in (("S3", man["crops"]["S3"], cam_s3, head_pose_s3, 72), ("S4", man["crops"]["S4"], cam_s4, pose_s4, 180)):
        layers, s, piv, spiv = build(crop, cam, pose)
        cache = {}
        def frames():
            for fi in range(n):
                key = (cam(fi), pose(fi))
                if key not in cache:
                    cache.clear(); cache[key] = compose(layers, fi, cam)
                yield cache[key]
        shas, d = write_shot(shot, frames())
        hb = man["head_bbox_plate"]
        out[shot] = {"crop_plate": crop, "scale_plate_to_screen": round(s, 5), "dir": d, "sha1": shas,
                     "head_height_frac": round((hb[3] - hb[1]) / (crop[3] - crop[1]), 3),
                     "head_pivot_screen": [round(v, 1) for v in piv], "shadow_pivot_screen": [round(v, 1) for v in spiv],
                     "layers": [{"name": L.name, "k": L.k, "z": L.z, "mode": L.mode, "role": L.role} for L in layers],
                     "camera": [list(map(lambda v: round(v, 3), cam(fi)[:2])) for fi in range(0, n, 12)],
                     "head_pose_deg_dx": [list(map(lambda v: round(v, 3), pose(fi))) for fi in range(n)]}
    out["E3_frames"] = {"turn_onset_shot_frame": F_TURN, "turn_onset_pass_frame": F_TURN + 204, "turn_onset_t": T_TURN,
                        "return_onset_shot_frame": F_RET, "return_onset_pass_frame": F_RET + 204, "return_onset_t": T_RET,
                        "turn_deg": TURN_DEG, "rest_after_deg": REST_DEG}
    dump(U1 / "json" / "s34_render.json", out)
    print("ok", {k: (v.get("head_height_frac"), len(v.get("sha1", []))) for k, v in out.items() if k.startswith("S")})
