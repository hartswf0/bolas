"""S1 WAKE, repair round 1 (recast): LoC 2017862347, Esther Bubley, Jan 1943, master TIFF 8d33590u.tif,
"Reading the newspaper aloud in a boardinghouse room" -- the same sitter as 2017862340 (S3/S4): curly
hair, the same dark pinstripe suit and tie. He sits head-bowed over the paper, eyes almost shut, against
the pale flash-lit wall with the dark suit filling the right of frame.

SCION-29: figure (head + shirt + suit) by GrabCut with box + polygon seeds; head piece split by a collar
polygon; matting band on the hair; failure masks exported; fills (behind the head, a band inside the
body edge) flagged invented with masks.
SCION-44: far = wall, lamp, table, newspaper (k 1.0, glide 10 px L->R); figure = body (k 1.5).
SCION-47: E1 2.0-2.8 s (frames 48-67): the bowed head lifts -- a weighted rotation about the nape
(7 deg, face rising) plus a 6 px lift; weight 0 at the collar so no seam opens there. No mouth motion.
Grade: one monotone neutral print curve (PCHIP through control points), recorded.
Run: python3 -I s1_wake.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r2-build")
from ed import *  # noqa

PID = "2017862347"
TIF = E2 / "raw" / "8d33590u.tif"
CROP = (2650, 1820, 4830, 3046)          # 2180 x 1226 -> 960 x 540 (scale 0.4404, a downscale)
REG = (2560, 1740, 4840, 3080)
# print curve: raw (8-bit negative scan) -> L. Wall raw 150-175 -> ~212-232, suit 18-53 -> 28-50,
# face 87-124 -> ~110-175, shirt/lamp 190-240 -> 238-246. Monotone; lifted blacks, soft shoulder.
CURVE_PTS = [(0, 22), (12, 26), (24, 30), (40, 37), (60, 54), (100, 128), (150, 212), (175, 232), (215, 242), (255, 248)]

a8 = np.array(Image.open(TIF))
x0, y0, x1, y1 = REG
f = pchip(*zip(*CURVE_PTS))
G = (f(a8[y0:y1, x0:x1].astype(np.float64)) / 255.0).astype(np.float32)
o = (x0, y0)
def P(pts):
    return [(x - x0, y - y0) for x, y in pts]

rect = (3060 - x0, 1900 - y0, x1 - x0, y1 - y0)
fg = [P([(3300, 2020), (3650, 2000), (3720, 2200), (3300, 2250)]),                  # hair
      P([(3300, 2350), (3560, 2330), (3600, 2620), (3380, 2650)]),                  # face
      P([(3620, 2300), (3800, 2330), (3820, 2600), (3640, 2620)]),                  # ear / neck
      P([(4050, 2450), (4600, 2500), (4700, 3040), (4000, 3040)]),                  # suit
      P([(3700, 2880), (3950, 2860), (3980, 3040), (3720, 3040)]),                  # shirt
      P([(3600, 2700), (3750, 2680), (3800, 2850), (3620, 2860)]),                  # collar/tie
      P([(3280, 2420), (3420, 2400), (3440, 2700), (3340, 2715), (3285, 2560)])]    # lit cheek and brow (skin ~ wall grey)
bg = [P([(2560, 1740), (4840, 1740), (4840, 1930), (2560, 1930)]),                  # wall above the crown
      P([(4050, 1930), (4840, 1930), (4840, 2260), (4560, 2300), (4100, 2310), (3960, 2250), (3950, 2050)]),  # wall right
      P([(4720, 2300), (4840, 2300), (4840, 2700), (4740, 2700)]),                  # window frame
      P([(2560, 1930), (3200, 1930), (3120, 2150), (3110, 2350), (3190, 2470), (3250, 2600), (3290, 2720),
         (3320, 2810), (3380, 2930), (3300, 3080), (2560, 3080)])]                 # lamp, table top, newspaper left
hard, init = grabcut(G, rect, fg_polys=fg, bg_polys=bg)
body, fail_body, st_body = cleanup(hard, poly_mask(G.shape, fg), max_hole=4000)

head_zone = poly_mask(G.shape, [P([(3050, 1900), (3960, 1900), (3990, 2300), (3900, 2560), (3820, 2700), (3700, 2740),
                                   (3560, 2800), (3420, 2880), (3250, 2760), (3060, 2450)])])
head = (body & head_zone).astype(np.uint8)
n_, lab_ = cv2.connectedComponents(head)
seedH = poly_mask(G.shape, fg[:3] + fg[6:7])
head = np.isin(lab_, [i for i in range(1, n_) if ((lab_ == i) & (seedH > 0)).any()]).astype(np.uint8)
torso = (body & (1 - head)).astype(np.uint8)
# the torso continues under the neck (hidden at rest) so a rising head never opens a gap at the collar
neck = (head & cv2.dilate(torso, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))).astype(np.uint8)
low_y = np.zeros_like(head); low_y[2640 - y0:, :] = 1
neck = np.clip(neck + (head & cv2.dilate(torso, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (181, 181))) & low_y), 0, 1).astype(np.uint8)
torso_full = np.clip(torso + neck, 0, 1).astype(np.uint8)

body_a, unk = matting_band(G, body, r=6, blend=0.85)
head_a = body_a * cv2.dilate(head, np.ones((9, 9), np.uint8)) * (1 - torso * (1 - cv2.dilate(head, np.ones((3, 3), np.uint8))))
torso_a = np.maximum(body_a * (1 - head), feather(neck, 1.0))
head_img = decontaminate(G, head_a)
torso_img = decontaminate(G, np.where(neck > 0, 1.0, torso_a))
# the chest/neck hidden under the chin and jaw (seen only as the head lifts) is continued from the
# visible tie/shirt/lapel pixels (TELEA inpaint, flagged invented), never from the chin itself
torso_img = np.where(neck > 0, inpaint(G, neck, 9), torso_img)
# under the bowed chin the throat and collar are in the head's own shadow: the continued pixels are
# clamped to the plate's shadow level there (the darkest decile of the visible lapel/tie), flagged invented
lapel = (torso & low_y & poly_mask(G.shape, [P([(3550, 2750), (3800, 2750), (3800, 3080), (3550, 3080)])])).astype(bool)
shade = float(np.percentile(G[lapel], 25)) if lapel.any() else 0.2
torso_img = np.where((neck > 0) & (low_y > 0), np.minimum(torso_img, shade), torso_img)

# far: background with the figure removed where it could ever be uncovered: under the head (dilated)
# and a 40 px band inside the body edge (the figure plane slides 5 px / ~11 plate px over the far plane).
band = (cv2.dilate(body, np.ones((11, 11), np.uint8)) & (1 - cv2.erode(body, np.ones((81, 81), np.uint8)))).astype(np.uint8)  # 5 px outside the edge too: clean wall boundary
fill = np.clip(cv2.dilate(head, np.ones((15, 15), np.uint8)) + band, 0, 1).astype(np.uint8)
fill &= (1 - cv2.erode(torso, np.ones((121, 121), np.uint8)))      # deep torso never seen
src_wall = ((1 - cv2.dilate(body, np.ones((31, 31), np.uint8))) & poly_mask(G.shape, [P([(3250, 1740), (4700, 1740), (4700, 2250), (3250, 2250)])])).astype(np.uint8)
far = texture_fill(G, fill, src_wall, radius=15)
# where the rising face uncovers the room (in front of the face and under the chin) the far plane is
# rebuilt by patch-copy of the plate's own lamp/table/wall texture (SSD on the known overlap), not a smear
front = (cv2.dilate(head, np.ones((15, 15), np.uint8)) & poly_mask(G.shape, [P([(3000, 2150), (3560, 2150), (3560, 3080), (3000, 3080)])])).astype(np.uint8)
src_q = ((1 - cv2.dilate(body, np.ones((25, 25), np.uint8))) & poly_mask(G.shape, [P([(2900, 2100), (3300, 2100), (3300, 2900), (2900, 2900)])])).astype(np.uint8)
far = quilt_fill(far, front, src_q, patch=24, overlap=8, cands=800)
save_mask(E2 / "fills" / "S1r_far_patchcopy_front.png", front)

# ---- files
M = E2 / "masks"; R = E2 / "rgba"; F = E2 / "failure_masks"; I = E2 / "fills"
man = {"plate": PID, "file": str(TIF), "region_in_plate": list(REG), "crop_S1": list(CROP),
       "print_curve_points_raw_to_L": CURVE_PTS, "print_curve_table": [[int(v), int(round(float(f(v))))] for v in range(0, 256, 16)],
       "grabcut": {"rect_plate": [rect[0] + x0, rect[1] + y0, rect[2] + x0, rect[3] + y0], "iters": PRESETS["photograph"]["iters"], "cleanup": st_body}}
man["pieces"] = {"S1r_head": save_rgba(R / "S1r_head.png", head_img, head_a, o),
                 "S1r_torso": save_rgba(R / "S1r_torso.png", torso_img, torso_a, o)}
save_gray(R / "S1r_far.png", far)
save_mask(M / "S1r_body_mask.png", body); save_mask(M / "S1r_head_mask.png", head); save_mask(M / "S1r_torso_mask.png", torso_full)
save_mask(M / "S1r_matting_band.png", unk)
save_mask(F / "S1r_body_cleanup_changed.png", fail_body)
save_mask(F / "S1r_grabcut_init_fg_seeds.png", (init == cv2.GC_FGD).astype(np.uint8))
save_mask(I / "S1r_far_invented_fill.png", fill); save_mask(I / "S1r_neck_under_head_hidden.png", neck)
man["fills"] = {"S1r_far_invented_fill.png": int(fill.sum()), "S1r_neck_under_head_hidden.png": int(neck.sum())}
ys, xs = np.nonzero(head)
hb = [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0 + 1, int(ys.max()) + y0 + 1]
man["head_bbox_plate"] = hb

# ---- rig
PIV = (3683, 2354)                     # atlas joint, just below the ear (plate)
SEGS = [((3920, 2570), (3770, 2870)), ((3770, 2870), (3470, 2885))]  # weight-0 polyline: nape/collar -> throat -> under the chin (plate)
T_ON, T_OFF = 2.0, 2.8
F_ON, F_OFF = round(T_ON * FPS), round(T_OFF * FPS)
ROT, LIFT = 9.0, -6.0                  # degrees (face rises), screen px
cx0, cy0, cx1, cy1 = CROP
s = W / (cx1 - cx0); rs = s * SS
org = ((x0 - cx0) * s, (y0 - cy0) * s)
piv = ((PIV[0] - cx0) * s, (PIV[1] - cy0) * s)
Rz = lambda a: resample(a.astype(np.float32), rs)
far_g = Rz(far); H_g, H_a = Rz(head_img), Rz(head_a); T_g, T_a = Rz(torso_img), Rz(torso_a)
K = {"far": 1.0, "fig": 1.5}
Hs, Ws = H * SS, W * SS
yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)


def sm(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def cam(fi):
    return (10.0 * float(sm(fi / 131.0)), 0.0, 1.0, (0, 0))


def place(img, kk, fi):
    M_ = affine(0, 0, 0, (0, 0), (cam(fi)[0] * kk, 0), org)
    return cv2.warpAffine(img, M_, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE if kk == 1.0 else cv2.BORDER_CONSTANT, borderValue=0)


def pose_u(fi):
    return float(sm((fi - F_ON) / (F_OFF - F_ON)))


def warp_head(fi):
    gp, ap = place(H_g, K["fig"], fi), place(H_a, K["fig"], fi)
    u = pose_u(fi)
    if u == 0:
        return gp, ap
    th = np.deg2rad(ROT * u)
    px, py = (piv[0] + cam(fi)[0] * K["fig"]) * SS, piv[1] * SS
    R0, R1 = 30 * SS, 130 * SS          # weight 0 within 15 px of the neck/jaw polyline, 1 beyond 120 px
    segs = [(np.array([((a_[0] - cx0) * s + cam(fi)[0] * K["fig"]) * SS, (a_[1] - cy0) * s * SS]),
             np.array([((b_[0] - cx0) * s + cam(fi)[0] * K["fig"]) * SS, (b_[1] - cy0) * s * SS])) for a_, b_ in SEGS]

    def disp(x, y):
        rx, ry = x - px, y - py
        dseg = None
        for sa, sb in segs:
            ab = sb - sa
            t_ = np.clip(((x - sa[0]) * ab[0] + (y - sa[1]) * ab[1]) / float(ab @ ab), 0, 1)
            d_ = np.hypot(x - (sa[0] + t_ * ab[0]), y - (sa[1] + t_ * ab[1]))
            dseg = d_ if dseg is None else np.minimum(dseg, d_)
        w = sm((dseg - R0) / (R1 - R0))
        nx = rx * np.cos(th) - ry * np.sin(th)
        ny = rx * np.sin(th) + ry * np.cos(th)
        return w * (nx - rx), w * (ny - ry + LIFT * u * SS)
    sx, sy = xx.copy(), yy.copy()
    for _ in range(4):
        dx, dy = disp(sx, sy)
        sx, sy = xx - dx, yy - dy
    return (cv2.remap(gp, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderValue=0),
            cv2.remap(ap, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderValue=0))


def frame(fi, alpha_only=False):
    out = place(far_g, K["far"], fi)
    g, a = place(T_g, K["fig"], fi), place(T_a, K["fig"], fi); out = g * a + out * (1 - a)
    hg, ha = warp_head(fi); out = hg * ha + out * (1 - ha)
    if alpha_only:
        return cv2.resize(ha, (W, H), interpolation=cv2.INTER_AREA)
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    return (np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    frames = [frame(fi) for fi in range(132)]
    shas, d = write_shot("S1", iter(frames))
    # measured crown / chin travel from the head alpha (top-most and the face's lowest-left point)
    def head_pts(fi):
        a = frame(fi, alpha_only=True) > 0.5
        ys_, xs_ = np.nonzero(a)
        return {"top_y": int(ys_.min()), "top_x": int(xs_[ys_ == ys_.min()].mean()), "bottom_y": int(ys_.max()), "centroid": [round(float(xs_.mean()), 1), round(float(ys_.mean()), 1)]}
    p0, p1 = head_pts(F_ON - 1), head_pts(F_OFF + 1)
    diffs = [int(np.abs(frames[i].astype(int) - frames[i - 1].astype(int)).sum()) for i in range(1, 132)]
    vis = min(hb[3], cy1) - max(hb[1], cy0)
    out = {"plate": PID, "crop_plate": list(CROP), "scale_plate_to_screen": round(s, 5), "dir": d, "sha1": shas,
           "head_height_frac": round(vis / (cy1 - cy0), 3), "head_bbox_plate": hb,
           "layers": [{"name": "room_far", "k": 1.0, "role": "far: pale wall, lamp, table, newspaper (fill behind the figure flagged)"},
                      {"name": "torso", "k": 1.5, "role": "figure: shirt and dark suit"},
                      {"name": "head", "k": 1.5, "role": "figure: head (E1 weighted rotation about the nape)"}],
           "parallax_near_over_far": 1.5, "camera_far_dx_end": 10.0,
           "E1": {"onset_t": T_ON, "onset_frame": F_ON, "end_t": T_OFF, "end_frame": F_OFF, "rot_deg": ROT, "lift_px": LIFT,
                  "pivot_plate": list(PIV), "weight0_polyline_plate": SEGS, "head_alpha_before": p0, "head_alpha_after": p1,
                  "centroid_travel_px": [round(p1["centroid"][0] - p0["centroid"][0], 1), round(p1["centroid"][1] - p0["centroid"][1], 1)]},
           "frame_diff_sum": diffs}
    out["manifest"] = man
    dump(E2 / "json" / "s1_render.json", out)
    Image.fromarray(np.hstack([frames[0], frames[F_ON], frames[F_OFF], frames[131]])).resize((1920, 270)).save(E2 / "diag" / "s1_strip.png")
    print("ok head", out["head_height_frac"], "E1", out["E1"]["centroid_travel_px"], p0, p1, st_body)
