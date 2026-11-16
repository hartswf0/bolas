"""SCION-29 cut for S3/S4 (LoC 2017862340, master TIFF 8d33583u.tif).
Pieces: head, torso, hands (near), head cast-shadow plane (ratio map), far wall (with invented fill).
All coordinates are plate (TIFF) pixels. Writes npz for the rig + RGBA/masks for the manifest."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from lib import *

PID = "2017862340"
REG = (2150, 1450, 4790, 3240)          # work region (contains S3 and S4 crops + glide margin)
S3 = (2200, 1500, 4790, 2957)
S4 = (2620, 1975, 4790, 3196)   # lowered to take in the dark suit: the reference layout (pale wall left, dark mass right and below)
STATS = (2200, 1500, 4790, 3196)        # union of the shots' crops (curve input statistics)

g, curve, rec = graded_plate(PID, STATS)
x0, y0, x1, y1 = REG
G = g[y0:y1, x0:x1].copy()
o = (x0, y0)
def P(pts):  # plate -> region coords
    return [(x - x0, y - y0) for x, y in pts]

# ---- body (head + torso + hands) by GrabCut with box + polygon seeds
rect = (3040 - x0, 1965 - y0, x1 - x0, y1 - y0)
fg = [P([(3820, 2120), (4180, 2080), (4230, 2300), (4180, 2560), (3900, 2620), (3830, 2450)]),      # face/hair
      P([(3950, 2030), (4150, 2010), (4250, 2150), (3900, 2150)]),                                  # hair top
      P([(3700, 2820), (4300, 2720), (4500, 2900), (4600, 3220), (3700, 3220)]),                    # suit
      P([(3460, 2880), (3700, 2880), (3720, 2960), (3460, 2960)]),                                  # hands
      P([(3330, 2900), (3420, 2880), (3420, 3100), (3330, 3100)]),                                  # left sleeve
      P([(3800, 2390), (3860, 2390), (3850, 2500), (3795, 2490)])]                                  # nose highlight
bg = [P([(2150, 1450), (3690, 1450), (3690, 2700), (3560, 2770), (3300, 2860), (2150, 2860)]),     # wall left of face
      P([(2150, 1450), (4790, 1450), (4790, 1975), (2150, 1975)]),                                  # wall above
      P([(4330, 2100), (4420, 2150), (4520, 2330), (4560, 2560), (4520, 2700), (4420, 2760), (4340, 2700), (4330, 2500), (4322, 2300)]),  # cast shadow interior
      P([(4420, 2560), (4560, 2560), (4600, 2800), (4520, 2820), (4430, 2700)]),                    # shoulder shadow
      P([(4600, 1975), (4790, 1975), (4790, 2800), (4640, 2800), (4600, 2500)]),                    # wall right of shadow
      P([(2150, 2860), (3030, 2860), (3030, 3240), (2150, 3240)])]                                  # bed / book at left (excluded)
hard, init = grabcut(G, rect, fg_polys=fg, bg_polys=bg)
seed = poly_mask(G.shape, fg)
body, fail_body, st_body = cleanup(hard, seed, max_hole=2500)
# manual contour markup at the shared-shadow seam (SCION-29 sec.6): the back of the head and the
# cast shadow have the same grey; the colour model cannot separate them, so the seam is drawn by eye
SEAM = [(4338, 2165), (4320, 2260), (4296, 2350), (4277, 2440), (4262, 2530), (4255, 2615)]
seam_bg = poly_mask(G.shape, [P(SEAM + [(4420, 2615), (4420, 2165)])])
manual_changed = body & seam_bg
body = (body & (1 - seam_bg)).astype(np.uint8)

# ---- split into head / torso / hands by the collar line and a hand polygon
collar = P([(3700, 2560), (3880, 2690), (3990, 2715), (4290, 2615), (4340, 2560)])  # head is above this polyline
head_zone = poly_mask(G.shape, [P([(3600, 1900), (4345, 1900), (4345, 2560), (4290, 2615), (3990, 2715), (3880, 2690), (3700, 2560)])])
hands_zone = poly_mask(G.shape, [P([(3410, 2815), (3730, 2830), (3830, 2890), (3830, 3240), (3410, 3240)])])
head = body & head_zone
hands = body & hands_zone & (1 - head_zone)
torso = body & (1 - head) & (1 - hands)
# torso keeps neck pixels under the head (hidden overlap, 24 px) so a rotating head never opens a gap
k24 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))
torso_under = head & cv2.dilate((1 - head_zone).astype(np.uint8), k24)
torso_full = np.clip(torso + torso_under, 0, 1).astype(np.uint8)

# ---- cast shadow plane: ratio of plate to a smooth shadow-free wall estimate
wall_valid = (1 - cv2.dilate(body, np.ones((25, 25), np.uint8))).astype(np.uint8)
# shadow candidates: right of the head, darker than the lit wall
shadow_zone = poly_mask(G.shape, [P([(4180, 2050), (4420, 2090), (4600, 2350), (4640, 2700), (4620, 3240), (4250, 3240), (4250, 2600)])])
wall_lit = wall_valid & (1 - shadow_zone)
wall_s = smooth_wall(G, wall_lit, sigma=90)
ratio0 = G / np.maximum(wall_s, 1e-3)
lit0 = (wall_valid & (ratio0 > 0.93)).astype(np.float32)   # lit wall anywhere, incl. right of the shadow
num0 = cv2.GaussianBlur(G * lit0, (0, 0), 60); den0 = cv2.GaussianBlur(lit0, (0, 0), 60)
wall_s = np.where(den0 > 0.02, num0 / np.maximum(den0, 1e-4), wall_s)  # local lit-wall tone
ratio = np.clip(G / np.maximum(wall_s, 1e-3), 0, 1.0)
in_shadow = (shadow_zone & wall_valid & (ratio < 0.93)).astype(np.uint8)
in_shadow = cv2.morphologyEx(in_shadow, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
# region D of the moving HEAD shadow: shadow zone above the shoulder line, dilated into lit wall
head_shadow_zone = poly_mask(G.shape, [P([(4180, 1990), (4460, 2030), (4680, 2350), (4700, 2700), (4330, 2660), (4290, 2615)])])
D = cv2.dilate(head_shadow_zone & np.clip(in_shadow + body, 0, 1), np.ones((41, 41), np.uint8)) & head_shadow_zone
D = D.astype(np.uint8)
# extend the ratio map under the whole body (where the shadowed wall continues, hidden): invented, flagged
behind = cv2.dilate(body, np.ones((45, 45), np.uint8)).astype(np.uint8)
r8 = (np.where(behind > 0, 1.0, ratio) * 255).astype(np.uint8)
r_all = cv2.inpaint(r8, behind, 15, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
body_d7 = cv2.dilate(body, np.ones((7, 7), np.uint8)).astype(np.uint8)
r_all = np.where(body_d7 > 0, r_all, ratio)   # true ratio everywhere the wall is visible
# behind the head, inside the head-shadow zone, the shadow continues: extend each row's ratio from the
# first visible wall pixel to the RIGHT (the shadow side), not from the lit wall on the left
hz = (body_d7 & head_shadow_zone).astype(bool)
for yy_ in np.nonzero(hz.any(1))[0]:
    row = hz[yy_]; xs_ = np.nonzero(row)[0]
    xr = xs_.max() + 1
    if xr < G.shape[1]:
        r_all[yy_, row] = np.median(ratio[yy_, min(xr + 2, G.shape[1] - 1):min(xr + 12, G.shape[1])])
r_all = np.where(hz, cv2.GaussianBlur(r_all, (0, 0), 3), r_all)  # smooth the copied values (invented region only)
# local lit-wall tone for the fill (normalized convolution, sigma 25, falls back to the broad estimate)
lit_near = (wall_valid & (ratio > 0.93) & (1 - shadow_zone)).astype(np.float32)
num = cv2.GaussianBlur(G * lit_near, (0, 0), 25); den = cv2.GaussianBlur(lit_near, (0, 0), 25)
wall_loc = np.where(den > 0.02, num / np.maximum(den, 1e-4), wall_s)
r_ext = r_all
yy = np.arange(G.shape[0], dtype=np.float32)[:, None] + y0
ramp_v = np.clip((2720 - yy) / 180.0, 0, 1)  # the head shadow hands over to the (static) shoulder shadow over 180 px
shadow_alpha = feather(D, 6.0) * ramp_v  # soft extent of the moving head-shadow plane

# ---- far wall: plate; under the body (dilated 4 px) the shadowed wall wall_s*r_all (upper) or
#      TELEA inpaint (lower: bed and suit); then divide out the head-shadow plane's own darkening
#      so that far * (1 - a + a*r) == plate exactly at rest (seamless), and = lit wall where a = 1.
fill_far = cv2.dilate(body, np.ones((7, 7), np.uint8)).astype(np.uint8)
lower = np.zeros_like(fill_far); lower[2900 - y0:, :] = 1
far0 = G.copy()
far0 = np.where((fill_far & (1 - lower)) > 0, wall_loc * r_all, far0)
far0 = np.where((fill_far & lower) > 0, inpaint(G, fill_far & lower, 9), far0)
dark = 1 - shadow_alpha + shadow_alpha * r_ext
far = np.clip(far0 / np.maximum(dark, 0.05), 0, 1)
fill_far = np.clip(fill_far + (shadow_alpha > 0.02), 0, 1).astype(np.uint8)  # wall under the head shadow is reconstructed too

# ---- torso under hands (suit behind the clasped hands): invented, inpainted from the suit
hands_d = cv2.dilate(hands, np.ones((21, 21), np.uint8))
torso_img = inpaint(G, hands_d & torso_full, 9)
torso_img = np.where((hands_d & torso_full) > 0, torso_img, G)
torso_alpha_hard = np.clip(torso_full + (hands_d & cv2.dilate(torso_full, np.ones((61, 61), np.uint8))), 0, 1).astype(np.uint8)

# ---- alphas: hair edge gets matting band, others feathered <=1 px; halos decontaminated
# matte the whole body contour (hair, face, shoulders, hands) by local fg/bg means (pure estimate in a
# 6 px band; where fg and bg share a grey the graph-cut prior is kept): no threshold halos
body_a, hair_unk = matting_band(G, body, band_poly=None, r=6, blend=0.85)
head_a = body_a * head_zone  # hard collar cut (hidden by the torso underneath)
torso_a = np.maximum(body_a * (1 - head_zone) * (1 - hands_zone), feather(torso_under, 1.0))
torso_a = np.maximum(torso_a, feather(hands_d & cv2.dilate(torso_full, np.ones((61, 61), np.uint8)), 1.0) * (1 - head_zone))
hands_a = body_a * hands_zone * (1 - head_zone)
head_img = decontaminate(G, head_a)
# no decontamination along the manual shadow seam: there fg and bg share a grey, and pulling the
# hair-core colour into the edge would draw a dark outline that is not in the negative
seam_zone = cv2.dilate(poly_mask(G.shape, [P(SEAM + [(4200, 2615), (4200, 2180)])]) & 0 + poly_mask(G.shape, [P([(4230, 2150), (4345, 2150), (4345, 2640), (4230, 2640)])]), np.ones((3, 3), np.uint8))
head_img = np.where(seam_zone > 0, G, head_img)
hands_img = decontaminate(G, hands_a)

# ---- files
M = U1 / "masks"; R = U1 / "rgba"; F = U1 / "failure_masks"; I = U1 / "fills"
man = {"plate": PID, "region_in_plate": list(REG), "curve": curve, "curve_table": curve_table(curve),
       "grabcut": {"rect_plate": [rect[0] + x0, rect[1] + y0, rect[2] + x0, rect[3] + y0], "iters": PRESETS["photograph"]["iters"],
                   "preset": "photograph (bilateral 7/0.08/5 for the colour model only)", "cleanup": st_body}}
man["pieces"] = {
    "S34_head": save_rgba(R / "S34_head.png", head_img, head_a, o),
    "S34_torso": save_rgba(R / "S34_torso.png", torso_img, torso_a, o),
    "S34_hands": save_rgba(R / "S34_hands.png", hands_img, hands_a, o),
    "S34_shadow_ratio": save_rgba(R / "S34_shadow_ratio.png", r_ext, shadow_alpha, o),
}
save_gray(U1 / "rgba" / "S34_far.png", far)
save_mask(M / "S34_body_mask.png", body); save_mask(M / "S34_head_mask.png", head)
save_mask(M / "S34_torso_mask.png", torso_full); save_mask(M / "S34_hands_mask.png", hands)
save_mask(M / "S34_cast_shadow_mask.png", in_shadow); save_mask(M / "S34_head_shadow_plane_D.png", D)
save_mask(M / "S34_hair_matting_band.png", hair_unk)
save_mask(F / "S34_body_cleanup_changed.png", fail_body)
save_mask(F / "S34_manual_seam_removed.png", manual_changed)
save_mask(F / "S34_grabcut_init_seeds.png", (init == cv2.GC_FGD).astype(np.uint8))
save_mask(I / "S34_far_invented_fill.png", fill_far)
save_mask(I / "S34_shadow_behind_head_invented.png", behind)
save_mask(I / "S34_suit_behind_hands_invented.png", hands_d & torso_full)
man["fills"] = {"S34_far_invented_fill.png": int(fill_far.sum()), "S34_shadow_behind_head_invented.png": int(behind.sum()),
                "S34_suit_behind_hands_invented.png": int((hands_d & torso_full).sum())}
# head-shadow offset: shift of head silhouette that best matches the shadow silhouette (flash geometry)
hs = (head & 1).astype(np.float32)
sh = (in_shadow & head_shadow_zone | (head & 0)).astype(np.float32)
best = (0, 0, -1)
for dx in range(0, 420, 10):
    for dy in range(-60, 200, 10):
        Mt = np.float32([[1, 0, dx], [0, 1, dy]])
        hm = cv2.warpAffine(hs, Mt, hs.shape[::-1])
        vis = hm * (1 - hs)  # the part of the shifted head not hidden behind the head itself
        sc = float((vis * sh).sum() - 0.5 * (vis * (1 - sh)).sum())
        if sc > best[2]:
            best = (dx, dy, sc)
man["head_shadow_offset_plate_px"] = [best[0], best[1]]
ys, xs = np.nonzero(head)
man["head_bbox_plate"] = [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0 + 1, int(ys.max()) + y0 + 1]
man["neck_pivot_plate"] = [4080, 2680]
man["manual_contour_seam_plate"] = SEAM
man["manual_seam_pixels_removed"] = int(manual_changed.sum())
man["crops"] = {"S3": list(S3), "S4": list(S4)}
np.savez_compressed(U1 / "json" / "s34_layers.npz", far=far, head_img=head_img, head_a=head_a, torso_img=torso_img, torso_a=torso_a,
                    hands_img=hands_img, hands_a=hands_a, ratio=r_ext, shadow_a=shadow_alpha, origin=np.array(o))
dump(U1 / "json" / "s34_manifest.json", man)
# diagnostic overlay
ov = np.dstack([G, G, G]).copy()
ov[head > 0] = ov[head > 0] * 0.5 + np.array([0.5, 0, 0]) * 1
ov[torso > 0] = ov[torso > 0] * 0.5 + np.array([0, 0.4, 0])
ov[hands > 0] = ov[hands > 0] * 0.5 + np.array([0, 0, 0.5])
ov[(D > 0) & (body == 0)] = ov[(D > 0) & (body == 0)] * 0.6 + np.array([0.3, 0.3, 0])
Image.fromarray((cv2.resize(ov, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)).save(U1 / "diag" / "s34_pieces_overlay.png")
print(json.dumps({k: man[k] for k in ("grabcut", "head_shadow_offset_plate_px", "head_bbox_plate", "fills")}, indent=1))
print("curve", {k: curve[k] for k in ("p2", "p98", "a")})
