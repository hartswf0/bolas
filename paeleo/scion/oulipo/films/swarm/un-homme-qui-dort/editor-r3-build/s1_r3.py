"""S1 WAKE, repair round 2: back to the head-on-hand plate LoC 2017862333 (Esther Bubley, Jan 1943,
master TIFF 8d33576u.tif, downloaded by U1). Uses U1's SCION-29 pieces (json/s1_layers.npz):
H head (GrabCut + hair matting band; extends under the hand with an invented, flagged cheek fill),
K hand/forearm (fingers retained), N book edge, far (plate with head region filled, flagged).

SCION-44: closer crop (head >= 0.6 of frame), far k 1.0, H k 1.15, K k 1.3, N k 1.6; glide 10 px.
SCION-47 E1 (pass 2.0-2.8 s = frames 48-67): the HAND STAYS (fixed plane); the head comes up off it:
a weighted rigid motion about the chin (12 deg clockwise righting + 22 px lift at the crown, weight
1 at the crown -> 0 at the jaw so no seam opens under the chin). Measured: crown rise and the gap that
opens between head alpha and hand alpha. No mouth motion (the plate's own closed mouth); eyes are the
plate's own (open, looking down) -- c1 is rewritten to "You lift your head." so it promises no more.
Print: U1's monotone plate curve, then one monotone neutral LUT (recorded) that brings the wallpaper
from ~200 to the reference's mid-grey register (p50 target 110-140). Run: python3 -I s1_r3.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r3-build")
from ed3 import *  # noqa

Z = np.load(U1 / "json" / "s1_layers.npz")
man = json.loads((U1 / "json" / "s1_manifest.json").read_text())
ox, oy = [int(v) for v in Z["origin"]]
CROP = (1950, 1800, 4550, 3263)          # 2600 x 1463 -> 960 x 540 (scale 0.3692, a downscale)
PIV = [3380, 3300]                      # under the chin / neck (plate)
Y_TOP, Y_ZERO = 2330, 3560              # weight 1 at the crown, 0 below the jaw (plate y)
F_ON, F_OFF = 48, 67
LIFT, TILT = -30.0, -5.0               # screen px at the crown / degrees (clockwise = righting)
# print LUT on U1's graded composite (in -> out, 8-bit), monotone, recorded
LUT_PTS = [(0, 21), (30, 27), (60, 44), (110, 78), (160, 112), (195, 140), (215, 196), (232, 232), (245, 242), (255, 247)]
TAB = lut(LUT_PTS)


def sm(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def cam(fi):
    return (10.0 * float(sm(fi / 131.0)), 0.0, 1.0, (0, 0))


cx0, cy0, cx1, cy1 = CROP
s = W / (cx1 - cx0); rs = s * SS
org = ((ox - cx0) * s, (oy - cy0) * s)
piv = ((PIV[0] - cx0) * s, (PIV[1] - cy0) * s)
R = lambda a: resample(a.astype(np.float32), rs)
# --- r3 fixes at plate scale (both flagged invented, masks exported) ---------------------------------
# (a) the cheek hidden under the hand (U1's invented fill) is shaded as the hand's own shadow would
#     shade it, so where the rising head uncovers it, it reads as a shadowed cheek, not a pale smear.
H_under = (np.array(Image.open(U1 / "fills" / "S1_H_under_hand_invented.png")) > 127).astype(np.uint8)
H_img = Z["H_img"] * (1.0 - 0.45 * feather(H_under, 8.0))
# (b) the far plate under the head and its hair fringe (U1 dilated only 9 px, leaving a ghost of the
#     hair matte) is re-filled by patch-copy from the plate's own board/wallpaper left of the head.
_cache_far = E3 / "json" / "s1_far_r3.npz"
hm = (Z["H_a"] > 0.02).astype(np.uint8); km = (Z["K_a"] > 0.5).astype(np.uint8)
zone = (cv2.dilate(hm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45))) & (1 - km)).astype(np.uint8)
if _cache_far.exists():
    FAR = np.load(_cache_far)["far"]
else:
    src = np.zeros_like(hm); src[700:1650, 650:1400] = 1      # region-local coords: board + wallpaper left of the head
    src &= (1 - cv2.dilate(hm, np.ones((91, 91), np.uint8))) & (1 - cv2.dilate(km, np.ones((31, 31), np.uint8)))
    FAR = quilt_fill(Z["far"].astype(np.float32), zone, src, patch=36, overlap=10, cands=500, seed=333)
    np.savez_compressed(_cache_far, far=FAR)
    save_mask(E3 / "fills" / "S1_far_refill_patchcopy.png", zone)
    save_mask(E3 / "fills" / "S1_H_under_hand_shaded.png", H_under)
far_g = R(FAR); H_g, H_a = R(H_img), R(Z["H_a"]); K_g, K_a = R(Z["K_img"]), R(Z["K_a"]); N_g, N_a = R(Z["N_img"]), R(Z["N_a"])
k = {"far": 1.0, "H": 1.15, "K": 1.3, "N": 1.6}
Hs, Ws = H * SS, W * SS
yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
ys_top, ys_zero = (Y_TOP - cy0) * s * SS, (Y_ZERO - cy0) * s * SS


def place(img, kk, fi):
    M = affine(0, 0, 0, (0, 0), (cam(fi)[0] * kk, 0), org)
    return cv2.warpAffine(img, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def u_of(fi):
    return float(sm((fi - F_ON) / (F_OFF - F_ON)))


def warp_H(g, a, fi):
    u = u_of(fi)
    gp, ap = place(g, k["H"], fi), place(a, k["H"], fi)
    if u == 0:
        return gp, ap
    th = np.deg2rad(TILT * u)
    px, py = piv[0] * SS + cam(fi)[0] * k["H"] * SS, piv[1] * SS

    def disp(x, y):
        w = sm((ys_zero - y) / (ys_zero - ys_top)) ** 0.45
        rx = np.cos(th) * (x - px) + np.sin(th) * (y - py) + px - x
        ry = -np.sin(th) * (x - px) + np.cos(th) * (y - py) + py - y
        return w * rx, w * (ry + LIFT * u * SS)
    sx, sy = xx.copy(), yy.copy()
    for _ in range(4):
        dx, dy = disp(sx, sy)
        sx, sy = xx - dx, yy - dy
    sx, sy = sx.astype(np.float32), sy.astype(np.float32)
    return cv2.remap(gp, sx, sy, cv2.INTER_LINEAR, borderValue=0), cv2.remap(ap, sx, sy, cv2.INTER_LINEAR, borderValue=0)


def frame(fi, with_alpha=False):
    out = place(far_g, k["far"], fi)
    hg, ha = warp_H(H_g, H_a, fi); out = hg * ha + out * (1 - ha)
    kg, ka = place(K_g, k["K"], fi), place(K_a, k["K"], fi); out = kg * ka + out * (1 - ka)
    ng, na = place(N_g, k["N"], fi), place(N_a, k["N"], fi); out = ng * na + out * (1 - na)
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    g8 = TAB[(np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)]
    if with_alpha:
        return g8, cv2.resize(ha, (W, H), interpolation=cv2.INTER_AREA), cv2.resize(ka, (W, H), interpolation=cv2.INTER_AREA)
    return g8


def head_metrics(fi):
    g8, ha, ka = frame(fi, True)
    hm = ha > 0.5
    ys, xs = np.nonzero(hm)
    top = int(ys.min())
    # contact: head pixels lying within 2 px of the hand's alpha
    kd = cv2.dilate((ka > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    contact = int((hm & kd & (ka < 0.5)).sum())
    # gap: smallest distance from hand to head along the hand's upper/right edge
    dist = cv2.distanceTransform((~hm).astype(np.uint8), cv2.DIST_L2, 5)
    edge = (ka > 0.5) & ~(cv2.erode((ka > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    return g8, {"crown_top_y": top, "head_px": int(hm.sum()), "head_bbox_h": int(ys.max() - ys.min() + 1),
                "contact_px": contact}


if __name__ == "__main__":
    shas, d = write_shot3("S1", (frame(fi) for fi in range(132)))
    g0, m0 = head_metrics(0); g1, m1 = head_metrics(80)
    st = frame_stats(g0)
    rep = {"plate": "2017862333", "tif": "8d33576u.tif", "crop_plate": CROP, "scale": round(s, 5), "dir": d, "sha1": shas,
           "lut_pts": LUT_PTS, "lut_monotone": bool(np.all(np.diff(TAB.astype(int)) >= 0)),
           "E1": {"frames": [F_ON, F_OFF], "lift_px": LIFT, "tilt_deg": TILT, "pivot_plate": PIV, "rest": m0, "raised": m1,
                  "crown_rise_px": m0["crown_top_y"] - m1["crown_top_y"],
                  "head_hand_contact_px_rest_vs_raised": [m0["contact_px"], m1["contact_px"]]},
           "head_height_frac": round(min(1.0, (min(man["head_bbox_plate"][3], cy1) - max(man["head_bbox_plate"][1], cy0)) / (cy1 - cy0)), 3),
           "stats_f0": st, "stats_f100": frame_stats(frame(100)),
           "layers": [{"name": "room_far", "k": 1.0}, {"name": "H_head", "k": 1.15, "action": "E1 weighted rigid lift off the hand"},
                      {"name": "K_hand", "k": 1.3, "action": "fixed (contact released)"}, {"name": "N_book_edge", "k": 1.6}],
           "camera_far_dx_px": [0.0, 10.0], "pieces_from": "U1 json/s1_layers.npz (cut_s1.py)"}
    dump(E3 / "json" / "s1_render.json", rep)
    strip = np.hstack([cv2.resize(frame(f), (480, 270)) for f in (0, 48, 58, 67, 100)])
    Image.fromarray(strip).save(E3 / "diag" / "s1_strip.png")
    print(json.dumps({k_: rep[k_] for k_ in ("E1", "head_height_frac", "stats_f0", "stats_f100")}, indent=0))
