"""S6 STAIRWELL (LoC 2017714056, Mydans 1935, archival TIFF 8a00242a.tif, 16-bit, on disk from r1). 60 frames.
Three planes cut from the negative: far = the pale lit plane at the bottom of the well (straight architectural
edges, manual contour), near = newel cap and the lower rail with its balusters (GrabCut), mid = the flights.
SCION-44: slow vertical tilt, near 12 px > mid 8 px > far 5 px. Sprocket rebates cropped out."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *

PID = "2017714056"
CROP = (110, 360, 4190, 2655)     # 4080 x 2295 -> 960 x 540 (scale 0.2353)
REG = (64, 230, 4230, 2950)
TH = 4.294
g, curve, rec = graded_plate(PID, CROP)
x0, y0, x1, y1 = REG
G = g[y0:y1, x0:x1].copy(); o = (x0, y0)
def T(pts):
    return [(x * TH - x0, y * TH - y0) for x, y in pts]

FAR_Q = [(318, 50), (818, 50), (793, 192), (440, 305), (318, 305)]   # pale plane (thumb coords), straight edges
far_m = poly_mask(G.shape, [T(FAR_Q)])

rect = (int(80 * TH - x0), int(375 * TH - y0), int(760 * TH - x0), y1 - y0)
fgN = [T([(95, 390), (180, 390), (180, 455), (95, 455)]),                       # newel cap
       T([(205, 505), (420, 565), (415, 585), (205, 525)]),                     # lower rail
       T([(150, 465), (180, 465), (200, 500), (170, 505)])]
fg_lines = [[(t[0] * TH - x0, t[1] * TH - y0) for t in ln] for ln in ([(440, 575), (700, 640)], [(300, 545), (300, 600)], [(355, 560), (355, 610)])]
bgN = [T([(80, 375), (90, 375), (90, 700), (80, 700)]), T([(200, 380), (420, 380), (420, 490), (200, 470)]),
       T([(220, 600), (300, 610), (300, 690), (220, 690)]), T([(430, 300), (760, 300), (760, 520), (430, 540)])]
CACHE = U1 / "json" / "s6_grabcut_cache.npz"
if not CACHE.exists() and (U1 / "masks" / "S6_near_mask.png").exists():
    # result of the first (10 min) GrabCut run of this same script, saved before the band restriction
    hard0 = (np.array(Image.open(U1 / "masks" / "S6_near_mask.png")) > 127).astype(np.uint8)
    np.savez_compressed(CACHE, hard=hard0, initfg=np.clip(poly_mask(G.shape, fgN) + lines_mask(G.shape, fg_lines, 7), 0, 1).astype(np.uint8))
if CACHE.exists():
    z = np.load(CACHE); hard, initfg = z["hard"], z["initfg"]
else:
    hard, init = grabcut(G, rect, fg_polys=fgN, bg_polys=bgN, fg_lines=fg_lines, line_w=7)
    initfg = (init == cv2.GC_FGD).astype(np.uint8)
    np.savez_compressed(CACHE, hard=hard, initfg=initfg)
near, fail, st = cleanup(hard, np.clip(poly_mask(G.shape, fgN) + lines_mask(G.shape, fg_lines, 7), 0, 1), max_hole=3000)
# the graph cut also took the lower flight (same dark wood); the near plane is only the newel, its post,
# the lower rail and its balusters: intersect with a band drawn along them (manual markup)
BAND = [(85, 378), (192, 378), (192, 470), (420, 545), (730, 612), (730, 700), (560, 700), (200, 600), (150, 540), (85, 470)]
near = (near & poly_mask(G.shape, [T(BAND)])).astype(np.uint8)
near = cv2.morphologyEx(near, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
near = (near & (1 - far_m)).astype(np.uint8)
mid = (1 - far_m).astype(np.uint8)

# invented extensions: far plane continued under the flights' edge (TELEA, pale flat surface), and the
# flights continued under the near rail/newel (TELEA band)
far_ext = cv2.dilate(far_m, np.ones((61, 61), np.uint8)) & (1 - far_m)
far_img = np.where(far_ext > 0, smooth_wall(G, far_m, sigma=25), G)   # pale flat plane continued (normalized convolution)
mid_ext = (cv2.dilate(near, np.ones((61, 61), np.uint8)) & near).astype(np.uint8)
mid_img = np.where(mid_ext > 0, inpaint(G, near, 9), G)
near_a = feather(near, 1.0); mid_a = feather(mid, 0.7); far_a = np.ones_like(G)
near_img = decontaminate(G, near_a)

save_rgba(U1 / "rgba" / "S6_near_newel_rail.png", near_img, near_a, o); save_rgba(U1 / "rgba" / "S6_mid_flights.png", mid_img, mid_a, o)
save_gray(U1 / "rgba" / "S6_far_pale_plane.png", far_img)
save_mask(U1 / "masks" / "S6_near_mask.png", near); save_mask(U1 / "masks" / "S6_far_plane_mask.png", far_m)
save_mask(U1 / "failure_masks" / "S6_near_cleanup_changed.png", fail)
save_mask(U1 / "fills" / "S6_far_extension_invented.png", far_ext); save_mask(U1 / "fills" / "S6_mid_under_near_invented.png", near)

s = W / (CROP[2] - CROP[0]); rs = s * SS
org = ((x0 - CROP[0]) * s, (y0 - CROP[1]) * s)
R = lambda a: resample(a.astype(np.float32), rs)
TILT = 5.0
layers = [Layer("well_far", R(far_img), R(far_a), 1.0, 0, org=org, role="far: pale plane at the bottom of the well (distant witness)"),
          Layer("flights_mid", R(mid_img), R(mid_a), 1.6, 1, org=org, role="mid: the flights"),
          Layer("newel_rail_near", R(near_img), R(near_a), 2.4, 2, org=org, role="near: newel cap, lower rail and balusters")]


def cam(fi):
    u = fi / 59.0
    u = u * u * (3 - 2 * u)
    return (0.0, TILT * u, 1.0, (0, 0))   # content moves down: far 5, mid 8, near 12 px


if __name__ == "__main__":
    shas, d = write_shot("S6", (compose(layers, fi, cam) for fi in range(60)))
    out = {"plate": PID, "crop_plate": list(CROP), "scale_plate_to_screen": round(s, 5), "dir": d, "sha1": shas, "curve": curve,
           "curve_table": curve_table(curve), "grabcut": {"rect_plate": [rect[0] + x0, rect[1] + y0, rect[2] + x0, rect[3] + y0], "cleanup": st},
           "near_band_manual_markup_plate": [[round(x * TH, 1), round(y * TH, 1)] for x, y in BAND],
           "far_plane_manual_contour_plate": [[round(x * TH, 1), round(y * TH, 1)] for x, y in FAR_Q],
           "layers": [{"name": L.name, "k": L.k, "z": L.z, "role": L.role} for L in layers],
           "tilt_far_px": TILT, "tilt_near_px": TILT * 2.4,
           "note": "perceptually this negative looks DOWN the well (floorboards bottom left; the newel cap is seen from above); the plan's 'looking up' reading is not supported, the move is a vertical tilt either way"}
    dump(U1 / "json" / "s6_render.json", out)
    print("ok", st)
