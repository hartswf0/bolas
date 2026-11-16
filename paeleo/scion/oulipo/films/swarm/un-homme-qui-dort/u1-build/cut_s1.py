"""SCION-29 cut for S1 WAKE (LoC 2017862333, master TIFF 8d33576u.tif).
Pieces: H head, K hand+forearm (fingers retained), N near (jacket shoulder + book edge), far (invented fill
under H and along N's edge). Head/background and jaw/jacket boundaries come from GrabCut; the hand/face
boundary (skin against skin, where no colour model separates them) is manual contour markup."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from lib import *

PID = "2017862333"
S1 = (1760, 1703, 4600, 3300)          # 2840 x 1597 -> 960 x 540 (scale 0.3380); shelf labels (MORTON, MINERAL OIL) cropped out
REG = (1300, 1400, 4640, 3420)
g, curve, rec = graded_plate(PID, S1)
x0, y0, x1, y1 = REG
G = g[y0:y1, x0:x1].copy(); o = (x0, y0)
def P(pts):
    return [(x - x0, y - y0) for x, y in pts]

HAND_RIGHT = [(2700, 2770), (2745, 2785), (2805, 2835), (2870, 2890), (2903, 2935), (2950, 3023), (2990, 3077),
              (3030, 3130), (3057, 3183), (3060, 3237), (3045, 3300), (3000, 3420)]
hand_zone = poly_mask(G.shape, [P(HAND_RIGHT + [(2300, 3420), (2300, 2770)])])

rect = (2380 - x0, 2280 - y0, 3800 - x0, y1 - y0)
fg = [P([(2950, 2420), (3300, 2400), (3420, 2600), (3420, 2850), (3150, 2780), (2950, 2700)]),       # hair
      P([(3000, 2850), (3450, 2850), (3500, 3100), (3300, 3200), (3100, 3150)]),                     # face
      P([(2770, 2900), (2880, 2960), (2960, 3100), (2990, 3220), (2900, 3250), (2780, 3050)]),       # hand/palm
      P([(2600, 3230), (2750, 3180), (2800, 3300), (2650, 3350)]),                                   # forearm
      P([(2730, 2560), (2950, 2420), (2950, 2700), (2780, 2760), (2720, 2700)])]                     # left hair
bg = [P([(2380, 2280), (3000, 2280), (2850, 2330), (2700, 2420), (2630, 2560), (2610, 2760), (2380, 2760)]),  # board/wall left
      P([(3000, 2280), (3800, 2280), (3800, 2295), (3000, 2295)]),                                    # above hair
      P([(3560, 2280), (3800, 2280), (3800, 2850), (3640, 2900), (3600, 2700), (3540, 2500), (3480, 2380), (3460, 2295)]),  # curtain/board right
      P([(3660, 2950), (3800, 2900), (3800, 3420), (3600, 3420), (3640, 3150)]),                     # jacket right
      P([(3420, 3330), (3720, 3150), (3800, 3150), (3800, 3420), (3420, 3420)]),                     # book corner
      P([(2380, 2960), (2560, 2960), (2560, 3120), (2380, 3120)])]                                   # bed rail left
hard, init = grabcut(G, rect, fg_polys=fg, bg_polys=bg)
fig, fail_fig, st_fig = cleanup(hard, poly_mask(G.shape, fg), max_hole=3000)
K = (fig & hand_zone).astype(np.uint8)
Hh = (fig & (1 - hand_zone)).astype(np.uint8)
# keep only the head component(s) touching the head seeds
n, lab = cv2.connectedComponents(Hh)
seedH = poly_mask(G.shape, fg[:2])
Hh = np.isin(lab, [i for i in range(1, n) if ((lab == i) & (seedH > 0)).any()]).astype(np.uint8)
# near piece N: jacket shoulder + book edge = non-figure pixels right/below the jaw
near_zone = poly_mask(G.shape, [P([(3300, 3420), (3300, 3330), (3700, 3080), (4200, 3020), (4640, 3020), (4640, 3420)])])
# near piece N = the book's edge (held in front of chin and jacket): GrabCut, pages vs tweed/skin
rectN = (3300 - x0, 3020 - y0, x1 - x0, y1 - y0)
fgN = [P([(3700, 3250), (3900, 3170), (4000, 3300), (3700, 3400)]), P([(3500, 3370), (3650, 3290), (3650, 3410), (3500, 3410)])]
bgN = [P([(3300, 3020), (4640, 3020), (4640, 3080), (4100, 3080), (3750, 3100), (3300, 3300)]), P([(4300, 3100), (4640, 3100), (4640, 3300), (4300, 3300)])]
hardN, _ = grabcut(G, rectN, fg_polys=fgN, bg_polys=bgN)
jacket, fail_N, st_N = cleanup(hardN, poly_mask(G.shape, fgN), max_hole=4000)
N = (near_zone & jacket & (1 - fig)).astype(np.uint8)
N = cv2.morphologyEx(N, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

# alphas (matting band on the hair; feathered elsewhere); hand/face seam keeps a 1 px feather
body = np.clip(Hh + K, 0, 1).astype(np.uint8)
body_a, unk = matting_band(G, body, r=6, blend=0.85)
H_a = body_a * (1 - hand_zone) * cv2.dilate(Hh, np.ones((15, 15), np.uint8))
K_a = np.minimum(body_a * hand_zone, feather(K, 1.0) + body_a * hand_zone * (1 - cv2.dilate(K, np.ones((5, 5), np.uint8))))
K_a = body_a * hand_zone * cv2.dilate(K, np.ones((15, 15), np.uint8))
N_a = feather(N, 1.0)

# H image under the hand: the hidden cheek/temple continued from the visible face (invented, flagged)
H_under = (K & cv2.dilate(Hh, np.ones((81, 81), np.uint8))).astype(np.uint8)
cheek_src = poly_mask(G.shape, [P([(3330, 2990), (3500, 2990), (3510, 3110), (3330, 3110)])])
H_img = np.where(H_under > 0, texture_fill(np.where(K > 0, 0, G), (K > 0).astype(np.uint8), cheek_src, radius=12), G)
H_alpha = np.maximum(H_a, feather(H_under, 1.0) * (1 - 0))  # H extends under K (hidden at rest)
H_img = decontaminate(H_img, np.where(H_under > 0, 1.0, H_a))

# far: plate with the head (dilated) and a 40 px band inside N's edge filled (TELEA from the plate)
fillH = cv2.dilate(Hh, np.ones((9, 9), np.uint8))
fillN = (N & (1 - cv2.erode(N, np.ones((41, 41), np.uint8)))).astype(np.uint8)
fill = np.clip(fillH + fillN, 0, 1).astype(np.uint8) & (1 - cv2.erode(K, np.ones((9, 9), np.uint8)))
board_src = poly_mask(G.shape, [P([(2450, 2250), (2700, 2250), (2700, 2750), (2450, 2750)])]) & (1 - cv2.dilate(fig, np.ones((15, 15), np.uint8)))
far = texture_fill(G, fill, board_src, radius=15)
# the band that a rising, righting head uncovers (left of the hair) is rebuilt from real board/wall
# patches (patch-copy, SSD on the known overlap), not a smooth inpaint
band = (fill & cv2.dilate((1 - fig) & (1 - hand_zone), np.ones((121, 121), np.uint8)) & poly_mask(G.shape, [P([(2600, 2250), (3500, 2250), (3000, 2800), (2600, 2800)])])).astype(np.uint8)
src_q = ((1 - cv2.dilate(fig, np.ones((21, 21), np.uint8))) & poly_mask(G.shape, [P([(2450, 2200), (3600, 2200), (3600, 2340), (2760, 2340), (2700, 2900), (2450, 2900)])])).astype(np.uint8)
far = quilt_fill(far, band, src_q, patch=28, overlap=8, cands=600)

M = U1 / "masks"; R = U1 / "rgba"; F = U1 / "failure_masks"; I = U1 / "fills"
man = {"plate": PID, "region_in_plate": list(REG), "crop_S1": list(S1), "curve": curve, "curve_table": curve_table(curve),
       "grabcut": {"rect_plate": [rect[0] + x0, rect[1] + y0, rect[2] + x0, rect[3] + y0], "iters": PRESETS["photograph"]["iters"], "cleanup": st_fig, "jacket_cleanup": st_N},
       "manual_contour_hand_face_plate": HAND_RIGHT}
man["pieces"] = {"S1_H_head": save_rgba(R / "S1_H_head.png", H_img, H_alpha, o),
                 "S1_K_hand": save_rgba(R / "S1_K_hand.png", decontaminate(G, K_a), K_a, o),
                 "S1_N_near_book_edge": save_rgba(R / "S1_N_near.png", G, N_a, o)}
save_gray(R / "S1_far.png", far)
save_mask(M / "S1_figure_mask.png", fig); save_mask(M / "S1_H_mask.png", Hh); save_mask(M / "S1_K_mask.png", K); save_mask(M / "S1_N_mask.png", N)
save_mask(M / "S1_matting_band.png", unk)
save_mask(F / "S1_figure_cleanup_changed.png", fail_fig); save_mask(F / "S1_jacket_cleanup_changed.png", fail_N)
save_mask(F / "S1_grabcut_init_fg_seeds.png", (init == cv2.GC_FGD).astype(np.uint8))
save_mask(I / "S1_far_invented_fill.png", fill); save_mask(I / "S1_far_patchcopy_band.png", band); save_mask(I / "S1_H_under_hand_invented.png", H_under)
man["fills"] = {"S1_far_invented_fill.png": int(fill.sum()), "S1_H_under_hand_invented.png": int(H_under.sum())}
ys, xs = np.nonzero(Hh)
man["head_bbox_plate"] = [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0 + 1, int(ys.max()) + y0 + 1]
ys, xs = np.nonzero(K)
man["hand_bbox_plate"] = [int(xs.min()) + x0, int(ys.min()) + y0, int(xs.max()) + x0 + 1, int(ys.max()) + y0 + 1]
man["neck_pivot_plate"] = [3300, 3450]
np.savez_compressed(U1 / "json" / "s1_layers.npz", far=far, H_img=H_img, H_a=H_alpha, K_img=decontaminate(G, K_a), K_a=K_a, N_img=G, N_a=N_a, origin=np.array(o))
dump(U1 / "json" / "s1_manifest.json", man)
ov = np.dstack([G, G, G]).copy()
ov[Hh > 0] = ov[Hh > 0] * 0.5 + np.array([0.5, 0, 0]); ov[K > 0] = ov[K > 0] * 0.5 + np.array([0, 0, 0.5]); ov[N > 0] = ov[N > 0] * 0.5 + np.array([0, 0.4, 0])
Image.fromarray((cv2.resize(ov, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)).save(U1 / "diag" / "s1_pieces_overlay.png")
print(json.dumps({k: man[k] for k in ("grabcut", "head_bbox_plate", "hand_bbox_plate", "fills")}))
print("curve", curve["p2"], curve["p98"])
