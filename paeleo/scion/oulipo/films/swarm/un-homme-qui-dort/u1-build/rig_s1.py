"""SCION-44/47 rig for S1 WAKE (132 frames): glide + E1 head lift off the hand.
E1 is a weighted rigid motion (an ARAP-style handle warp, plan fallback branch 'S1-warp'): the crown
takes the full lift (8 px) and righting (4 deg clockwise about the chin), the chin and jaw stay
(weight 0), so no seam opens under the chin; the hand K stays put, so the contact is released."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *

Z = np.load(U1 / "json" / "s1_layers.npz")
man = json.loads((U1 / "json" / "s1_manifest.json").read_text())
ox, oy = [int(v) for v in Z["origin"]]
CROP = man["crop_S1"]
PIV = [3250, 3260]          # chin
Y_TOP, Y_ZERO = 2330, 3200  # weight 1 at the crown, 0 at the jaw line (plate y)
T_ON, T_OFF = 2.0, 2.8
F_ON, F_OFF = round(T_ON * FPS), round(T_OFF * FPS)
LIFT, TILT = -8.0, -4.0


def sm(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def cam(fi):
    u = float(sm(fi / 131.0))
    return (11.0 * u, 0.0, 1.0, (0, 0))


cx0, cy0, cx1, cy1 = CROP
s = W / (cx1 - cx0); rs = s * SS
org = ((ox - cx0) * s, (oy - cy0) * s)
piv = ((PIV[0] - cx0) * s, (PIV[1] - cy0) * s)
R = lambda a: resample(a.astype(np.float32), rs)
far_g = R(Z["far"]); H_g, H_a = R(Z["H_img"]), R(Z["H_a"]); K_g, K_a = R(Z["K_img"]), R(Z["K_a"]); N_g, N_a = R(Z["N_img"]), R(Z["N_a"])
k = {"far": 1.0, "H": 1.15, "K": 1.3, "N": 1.6}
Hs, Ws = H * SS, W * SS
yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
# weight field in screen coords at rest (plate y -> screen y)
ys_top, ys_zero = (Y_TOP - cy0) * s * SS, (Y_ZERO - cy0) * s * SS
wfield = sm((ys_zero - yy) / (ys_zero - ys_top)).astype(np.float32)


def place(img, kk, fi, fill=0.0):
    cx = cam(fi)[0] * kk
    M = affine(0, 0, 0, (0, 0), (cx, 0), org)
    return cv2.warpAffine(img, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=fill)


def warp_H(g, a, fi):
    u = float(sm((fi - F_ON) / (F_OFF - F_ON)))
    gp, ap = place(g, k["H"], fi), place(a, k["H"], fi)
    if u == 0:
        return gp, ap
    th = np.deg2rad(TILT * u)
    px, py = piv[0] * SS + cam(fi)[0] * k["H"] * SS, piv[1] * SS
    # forward displacement of a rest point p: w(p) * (Rot(p) - p + lift); inverse map by fixed-point (2 iters)
    def disp(x, y):
        w = sm((ys_zero - y) / (ys_zero - ys_top))
        rx = np.cos(th) * (x - px) + np.sin(th) * (y - py) + px - x
        ry = -np.sin(th) * (x - px) + np.cos(th) * (y - py) + py - y
        return w * rx, w * (ry + LIFT * u * SS)
    sx, sy = xx.copy(), yy.copy()
    for _ in range(3):
        dx, dy = disp(sx, sy)
        sx, sy = xx - dx, yy - dy
    sx, sy = sx.astype(np.float32), sy.astype(np.float32)
    return cv2.remap(gp, sx, sy, cv2.INTER_LINEAR, borderValue=0), cv2.remap(ap, sx, sy, cv2.INTER_LINEAR, borderValue=0)


def frame(fi):
    out = place(far_g, k["far"], fi)
    g, a = warp_H(H_g, H_a, fi); out = g * a + out * (1 - a)
    g, a = place(K_g, k["K"], fi), place(K_a, k["K"], fi); out = g * a + out * (1 - a)
    g, a = place(N_g, k["N"], fi), place(N_a, k["N"], fi); out = g * a + out * (1 - a)
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    return (np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    shas, d = write_shot("S1", (frame(fi) for fi in range(132)))
    hb = man["head_bbox_plate"]
    vis = min(hb[3], cy1) - max(hb[1], cy0)
    out = {"crop_plate": CROP, "scale_plate_to_screen": round(s, 5), "dir": d, "sha1": shas,
           "head_height_frac": round(vis / (cy1 - cy0), 3), "head_bbox_plate": hb,
           "head_pivot_screen": [round(v, 1) for v in piv],
           "layers": [{"name": "room_far", "k": 1.0, "z": 0, "role": "far: wall, board, curtain, jacket"},
                      {"name": "H_head", "k": 1.15, "z": 1, "role": "figure: head H (E1, weighted handle warp)"},
                      {"name": "K_hand", "k": 1.3, "z": 2, "role": "figure: hand/forearm K, fingers retained (stays: contact released)"},
                      {"name": "N_book", "k": 1.6, "z": 3, "role": "near: book edge (shield)"}],
           "camera_far_dx": [round(cam(fi)[0], 3) for fi in range(132)],
           "E1": {"onset_t": T_ON, "onset_frame": F_ON, "end_t": T_OFF, "end_frame": F_OFF, "crown_lift_px": LIFT, "tilt_deg": TILT,
                  "pivot_plate": PIV, "weight": "smoothstep 1 at plate y %d -> 0 at plate y %d" % (Y_TOP, Y_ZERO)}}
    dump(U1 / "json" / "s1_render.json", out)
    print("ok", out["head_height_frac"])
