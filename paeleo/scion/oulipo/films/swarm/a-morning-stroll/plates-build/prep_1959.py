"""1959 plate (LoC ppmsca.70651, Rizzuto, July 1959): unify curve, shot crops, holdout mattes (#29),
DAG geometry (#45), hall layer. Run: python3 -I prep_1959.py

Input : sources/.../test-shot/70651u_full.png (the LoC master TIFF 70651u.tif decoded to greyscale by PIL;
        2470 x 3026, same pixels the approved test shot used)
Output: sources/.../plates/1959/*
All geometry is in master pixel coordinates (x right, y down) unless a key says otherwise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2
import numpy as np
from PIL import Image

from common import PLATES, SRC, drop_islands, dump, push_rects, render_crop, rgba_piece, vignette

OUT = f"{PLATES}/1959"
os.makedirs(OUT, exist_ok=True)

# ---- shots (master coords). A/C: the big granite treads, near twisted bars, stoop shadow side as the one black mass.
SHOTS = {
    "A": (300, 1050, 2310, 2181),     # 2010 x 1131
    "C": (300, 1050, 2310, 2181),     # same framing as A
    "B": (1560, 64, 2200, 424),       # 640 x 360: black recess | white jamb | left leaf | handrail + lace
    "B_insert": (1640, 120, 2040, 345),  # 400 x 225: the beak meeting the leaf at (1921, 251)
}
P1, P99 = 78.0, 225.0                 # print black / white points (measured p1 / p99.5 of the B region)


def curve(L):
    """ONE global unify curve for every 1959 frame: levels to the print's own black/white points, then a
    smooth S (no posterise, no edge filter). t -> 8 + 240 * (0.4 t' + 0.6 smoothstep(t')), t' = clip((t-0.10)/0.62)."""
    t = np.clip((L - P1) / (P99 - P1), 0, 1)
    t = np.clip((t - 0.10) / 0.62, 0, 1)
    t = t * t * (3 - 2 * t) * 0.6 + t * 0.4
    return np.clip(8 + t * 240, 0, 255)


# ---- tread-nose polylines (bottom edge of each nose highlight = top of the riser shadow), measured from vertical
# luminance gradient peaks in 60-px column bands (x 700..1950), bars excluded; feet stand ~0.3 riser above the line.
TREADS = {
    "N2": [(700, 1107), (900, 1118), (1100, 1098), (1250, 1084)],
    "N3": [(900, 1226), (1100, 1214), (1250, 1213), (1550, 1217), (1800, 1244)],
    "N4": [(700, 1367), (900, 1365), (1100, 1374), (1250, 1372), (1550, 1388), (1800, 1376), (1950, 1371)],
    "N5": [(700, 1542), (900, 1544), (1100, 1564), (1250, 1566), (1800, 1601), (1950, 1612)],
    "N6": [(700, 1764), (900, 1801), (1100, 1819), (1250, 1836), (1550, 1862), (1800, 1908)],
    "N7": [(900, 2144), (1100, 2170)],
}
SHADOW_SIDE_X = [(2150, 1150), (2080, 1650), (2000, 2181)]   # left edge of the stoop's black shadow side (approx.)

# ---- shot B geometry (from the test shot's measured plate.json, re-checked on the grid view)
HINGE_X, LEAF_R = 1735, 1982
JAMB = (1690, 1735)                   # white stile/frame strip between the black recess and the leaf
RAIL = ((1560, 684), (2000, 233))
BEAK_CONTACT = (1921, 251)            # the test shot's measured beak-on-leaf point


def floor_y(x):
    return 645.0 - 0.2 * (x - 1950.0)


def main():
    full = np.asarray(Image.open(f"{SRC}/test-shot/70651u_full.png").convert("L"), np.float32)
    G = curve(full).astype(np.uint8)
    Image.fromarray(G).save(f"{OUT}/plate_graded.png")
    lut = [int(v) for v in curve(np.arange(256, dtype=np.float32))]
    gimg = Image.fromarray(G).convert("RGB")

    crops = {}
    for k, r in SHOTS.items():
        pr = push_rects(r)
        render_crop(gimg, pr[0], f"{OUT}/crop_{k}_start.png")
        render_crop(gimg, pr[1], f"{OUT}/crop_{k}_end.png")
        crops[k] = {"rect": list(r), "push_start": pr[0], "push_end": pr[1],
                    "scale_px_per_master": 960 / (r[2] - r[0]),
                    "start_png": f"{OUT}/crop_{k}_start.png", "end_png": f"{OUT}/crop_{k}_end.png"}

    # ---- A holdouts (#29): the near twisted bars + lace railings in front of the treads.
    x0, y0, x1, y1 = SHOTS["A"]
    L = full[y0:y1, x0:x1]
    Lb = cv2.GaussianBlur(L, (0, 0), 1.5)
    th = Lb - cv2.morphologyEx(Lb, cv2.MORPH_OPEN, np.ones((1, 45), np.uint8))   # bright, narrow, vertical-ish
    cand = (th > 10).astype(np.uint8)
    cand = cv2.morphologyEx(cand, cv2.MORPH_OPEN, np.ones((9, 1), np.uint8))
    cand = drop_islands(cand, 1500, 160)
    # GrabCut refine: box = region; sure-bg = far from candidates; probable-fg = candidates
    rgb = np.dstack([G[y0:y1, x0:x1]] * 3)
    gc = np.full(L.shape, cv2.GC_PR_BGD, np.uint8)
    far = cv2.dilate(cand, np.ones((5, 9), np.uint8)) == 0   # narrow 4-px band refine (#29 edge band)
    gc[far] = cv2.GC_BGD
    gc[cand > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(cand, np.ones((3, 7), np.uint8)) > 0] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, gc, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    m = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
    m = drop_islands(m, 1500, 160)                                      # no background islands
    fail = ((cand > 0) & (m == 0)) | ((m > 0) & (cand == 0) & far)     # disagreement = failure mask
    alpha = cv2.GaussianBlur(m.astype(np.float32) * 255, (0, 0), 0.7)
    sA = rgba_piece(rgb, alpha, f"{OUT}/holdout_A_iron.png", f"{OUT}/holdout_A_iron_contour.png")
    Image.fromarray((fail * 255).astype(np.uint8)).save(f"{OUT}/failure_A_iron.png")
    ov = rgb.copy()
    ov[m > 0] = (0.45 * ov[m > 0] + [140, 0, 0]).astype(np.uint8)
    ov[fail > 0] = [0, 200, 255]
    for pts in TREADS.values():
        cv2.polylines(ov, [np.array([(px - x0, py - y0) for px, py in pts], np.int32)], False, (0, 255, 0), 3)
    Image.fromarray(ov).resize((960, 540)).save(f"{OUT}/check_A.png")

    # ---- B holdouts (#45): iron (railing+lace) from the test-shot plate cut, leaf, jamb; hall layer.
    bx0, by0, bx1, by1 = SHOTS["B"]
    rx0, ry0 = 1390, 62                                # test-shot REGION origin
    iron = np.asarray(Image.open(f"{SRC}/test-shot/plate/iron.png"), np.float32)
    iron = iron[by0 - ry0:by1 - ry0, bx0 - rx0:bx1 - rx0]
    Bgray = G[by0:by1, bx0:bx1]
    Brgb = np.dstack([Bgray] * 3)
    yy, xx = np.mgrid[by0:by1, bx0:bx1]
    leaf = ((xx >= HINGE_X) & (xx <= LEAF_R) & (yy <= floor_y(xx))).astype(np.float32) * 255
    jamb = ((xx >= JAMB[0]) & (xx < JAMB[1])).astype(np.float32) * 255
    sB = {
        "iron": rgba_piece(Brgb, iron, f"{OUT}/holdout_B_iron.png", f"{OUT}/holdout_B_iron_contour.png"),
        "leaf": rgba_piece(Brgb, leaf, f"{OUT}/piece_B_leaf.png", f"{OUT}/piece_B_leaf_contour.png"),
        "jamb": rgba_piece(Brgb, jamb, f"{OUT}/holdout_B_jamb.png", f"{OUT}/holdout_B_jamb_contour.png"),
    }
    # interior dark hall (HANDMADE): black field, one soft slit of daylight at the far end, neutral grey
    h, w = Bgray.shape
    hall = np.full((h, w), 10, np.float32)
    gx = np.exp(-((xx - 1880.0) / 22.0) ** 2) * np.clip((yy - 120.0) / 200.0, 0, 1)
    hall += 70 * gx                                    # far-door slit
    hall += 14 * np.exp(-((yy - floor_y(xx) + 40) / 30.0) ** 2) * ((xx > HINGE_X) & (xx < LEAF_R))  # floor sheen
    rng = np.random.default_rng(1959)
    hall += rng.normal(0, 3.8, hall.shape)             # reference-matched fine grain
    Image.fromarray(np.clip(hall, 0, 255).astype(np.uint8)).save(f"{OUT}/hall_B.png")
    ovb = Brgb.copy()
    ovb[iron > 127] = (0.45 * ovb[iron > 127] + [140, 0, 0]).astype(np.uint8)
    ovb[(leaf > 0) & (iron <= 127)] = (0.7 * ovb[(leaf > 0) & (iron <= 127)] + [0, 0, 70]).astype(np.uint8)
    ovb[jamb > 0] = (0.6 * ovb[jamb > 0] + [0, 90, 0]).astype(np.uint8)
    cv2.circle(ovb, (BEAK_CONTACT[0] - bx0, BEAK_CONTACT[1] - by0), 5, (255, 255, 0), -1)
    cv2.line(ovb, (HINGE_X - bx0, 0), (HINGE_X - bx0, h), (255, 0, 255), 1)
    Image.fromarray(ovb).resize((960, 540)).save(f"{OUT}/check_B.png")

    # vignette layer for the editor
    v = vignette(corner=0.40)
    Image.fromarray((v * 255).astype(np.uint8)).save(f"{OUT}/vignette_960x540.png")

    geom = {
        "plate": "loc-ppmsca.70651", "master_size": [2470, 3026],
        "graded_plate": f"{OUT}/plate_graded.png",
        "unify_curve": {"black_point": P1, "white_point": P99,
                        "formula": "t=clip((L-78)/(225-78)); t=clip((t-0.10)/0.62); t=0.4t+0.6*smoothstep(t); out=8+240t",
                        "lut_0_255": lut,
                        "note": "replaces the test shot's harsher clip((t-0.15)/0.5)^0.75 so the granite keeps mid-greys; one curve for plate AND puppet"},
        "grain": {"type": "gaussian luma", "std_levels": 3.8, "apply": "after composite, before vignette"},
        "vignette": {"png": f"{OUT}/vignette_960x540.png", "corner_multiplier": 0.40, "apply": "multiply after grain"},
        "crops": crops,
        "A": {"tread_nose_polylines": TREADS, "shadow_side_left_edge": SHADOW_SIDE_X,
              "light": {"from": "camera-left and slightly in front, high morning sun (the stoop's right face is in full shadow)",
                        "cast_shadow_dir_on_treads_img": [0.88, 0.47],
                        "watcher_shadow_dir_img": [0.85, -0.53],
                        "status": "estimated from the plate's shadow side; not photogrammetrically measured"},
              "holdout_iron": {"rgba": f"{OUT}/holdout_A_iron.png", "contour": f"{OUT}/holdout_A_iron_contour.png",
                               "failure_mask": f"{OUT}/failure_A_iron.png", "check": f"{OUT}/check_A.png", **sA,
                               "method": "#29: white top-hat seeds (1x45 opening) -> cv2.grabCut(mask init, 4 iters) -> islands < 1500 px / < 160 px tall dropped; GrabCut confined to a 4-px band around the seeds"},
              "bird_height_master_px": [220, 300],
              "bird_note": "220-300 master px = 105-145 frame px = 19-27 % of frame height in A/C"},
        "B": {"hinge_axis": {"x": HINGE_X, "y_top": 55, "y_bottom": floor_y(HINGE_X), "opens": "inward, away from camera (leaf foreshortens to the hinge)"},
              "leaf_right_x": LEAF_R, "jamb_x": list(JAMB), "black_recess_x": [1560, 1690],
              "sill_line": {"formula": "y = 645 - 0.2 (x - 1950)", "note": "below the B frame; the bird enters from the handrail perch, so the iron holdout plays the sill"},
              "handrail_centre": RAIL, "handrail_half_width": 9, "beak_contact": BEAK_CONTACT,
              "pieces": {k: {"rgba": f"{OUT}/{n}.png", "contour": f"{OUT}/{n}_contour.png", **sB[k]}
                         for k, n in (("iron", "holdout_B_iron"), ("leaf", "piece_B_leaf"), ("jamb", "holdout_B_jamb"))},
              "hall": f"{OUT}/hall_B.png", "check": f"{OUT}/check_B.png",
              "bird_height_master_px": [120, 145],
              "bird_note": "test shot bird was ~95 master px (~19 % of frame); at the tighter B crop 120-145 master px = 180-218 frame px = 33-40 %"},
        "B_insert": {"beak_contact_frame_px": [(BEAK_CONTACT[0] - 1640) * 2.4, (BEAK_CONTACT[1] - 120) * 2.4],
                     "use": "a 2-4 frame cut-in around each strike or one held insert 5.9-6.5 s; 2.4x enlargement of the print, grain shows"},
        "dag": {"A": ["plate_A", "watcher_cast_shadow", "bird_contact_shadow", "bird", "holdout_A_iron", "grain", "vignette"],
                "B": ["plate_B", "hall_B (visible only where leaf has swung)", "leaf (homography about hinge_axis)", "bird_cast_shadow_on_leaf", "bird", "holdout_B_jamb (after E5 start)", "holdout_B_iron", "grain", "vignette"],
                "assertions": ["bird alpha * holdout_A_iron alpha == 0 in output wherever iron is in front", "beak tip inside piece_B_leaf alpha>127 on E3/E4 frames",
                               "bird visible px == 0 at E6 end (it walks left behind holdout_B_jamb into the hall)"]},
    }
    dump(geom, f"{OUT}/geometry.json")
    print("A iron", sA, "B", sB)


if __name__ == "__main__":
    main()
