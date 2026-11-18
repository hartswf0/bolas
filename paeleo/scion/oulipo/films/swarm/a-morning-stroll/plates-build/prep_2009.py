"""2009 plate (LoC highsm.56276, Carol M. Highsmith, photographed 2019-03-12): unify grade, crops, mattes, geometry.
Run: python3 -I prep_2009.py

Inputs : plates/raw/56276u_region_3x.png  - master TIFF 56276u.tif (13925 x 7817, uncompressed RGB) read by HTTP
                                            multi-range: master cols 7300-10100, rows 1500-7650 every 3rd row, cols
                                            Lanczos-decimated 3x -> 933 x 2050. region px = (master - (7300,1500)) / 3
         r2/56276v.jpg                    - LoC 1024 x 575 service JPEG (wide shot A/C; master = preview * 13925/1024)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2
import numpy as np
from PIL import Image

from common import PLATES, SRC, drop_islands, dump, push_rects, render_crop, rgba_piece

OUT = f"{PLATES}/2009"
os.makedirs(OUT, exist_ok=True)

SHOTS = {"A": ("preview", (300, 215, 940, 575)), "C": ("preview", (300, 215, 940, 575)),
         "B": ("region", (0, 880, 893, 1382))}
LEAF = (145, 485)          # region x: hinge (left) .. latch edge (right); knob at (460, 860)
LEAF_Y = (330, 1245)       # leaf top (glass lites) .. kick-plate bottom
JAMB_L, JAMB_R = (75, 145), (485, 530)
SILL_Y = 1250
NOSES = [1380, 1514, 1656, 1816, 1929]   # region y, bright nose -> riser shadow (column bands x 150-600)
RAIL_X = (570, 930)        # handrail/balusters, region x span, from y 950 down


def unify(rgb, lo=None, hi=None):
    """One luminance-only levels stretch (same gain on R,G,B -> hue and saturation kept)."""
    a = rgb.astype(np.float32)
    L = a @ np.array([0.299, 0.587, 0.114], np.float32)
    if lo is None:
        lo, hi = np.percentile(L, [0.5, 99.5])
    g = 245.0 / (hi - lo)
    return np.clip((a - lo) * g + 4, 0, 255).astype(np.uint8), float(lo), float(hi)


def main():
    R = np.asarray(Image.open(f"{PLATES}/raw/56276u_region_3x.png").convert("RGB"))
    P = np.asarray(Image.open(f"{SRC}/r2/56276v.jpg").convert("RGB"))
    Rg, lo, hi = unify(R)
    Pg, _, _ = unify(P, lo, hi)              # SAME levels for both sources
    Image.fromarray(Rg).save(f"{OUT}/region_graded.png")
    Image.fromarray(Pg).save(f"{OUT}/preview_graded.png")
    imgs = {"region": Image.fromarray(Rg), "preview": Image.fromarray(Pg)}
    crops = {}
    for k, (src, r) in SHOTS.items():
        pr = push_rects(r)
        render_crop(imgs[src], pr[0], f"{OUT}/crop_{k}_start.png")
        render_crop(imgs[src], pr[1], f"{OUT}/crop_{k}_end.png")
        crops[k] = {"source": src, "rect": list(r), "push_start": pr[0], "push_end": pr[1],
                    "scale_px_per_src": 960 / (r[2] - r[0]), "start_png": f"{OUT}/crop_{k}_start.png"}

    h, w = R.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    # leaf piece and jambs (region coords)
    leaf = ((xx >= LEAF[0]) & (xx <= LEAF[1]) & (yy >= LEAF_Y[0]) & (yy <= LEAF_Y[1])).astype(np.float32) * 255
    jl = ((xx >= JAMB_L[0]) & (xx < JAMB_L[1]) & (yy >= 250) & (yy <= SILL_Y)).astype(np.float32) * 255
    jr = ((xx >= JAMB_R[0]) & (xx < JAMB_R[1]) & (yy >= 250) & (yy <= SILL_Y)).astype(np.float32) * 255
    # handrail iron (#29): dark thin structure on light ground -> black top-hat seeds -> GrabCut in a narrow band
    L = cv2.cvtColor(R, cv2.COLOR_RGB2GRAY).astype(np.float32)
    bh = cv2.morphologyEx(L, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8)) - L
    zone = (xx >= RAIL_X[0]) & (xx <= RAIL_X[1]) & (yy >= 940) & (yy <= 1935) & ~((xx > 740) & (yy < 1010))   # excludes window sill and sidewalk
    cand = ((bh > 28) & (L < 60) & zone).astype(np.uint8)   # black-painted iron is darker than brick/shadowed stone
    cand = drop_islands(cand, 150, 25)
    gc = np.full(L.shape, cv2.GC_BGD, np.uint8)
    band = cv2.dilate(cand, np.ones((3, 3), np.uint8)) > 0
    gc[band] = cv2.GC_PR_BGD
    gc[cand > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(cand, np.ones((3, 3), np.uint8)) > 0] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(np.ascontiguousarray(R), gc, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    m = drop_islands((((gc == 1) | (gc == 3)) & zone & (L < 85)).astype(np.uint8), 150, 25)
    fail = ((cand > 0) & (m == 0)).astype(np.uint8)
    iron = cv2.GaussianBlur(m.astype(np.float32) * 255, (0, 0), 0.6)
    st = {
        "leaf": rgba_piece(Rg, leaf, f"{OUT}/piece_leaf.png", f"{OUT}/piece_leaf_contour.png"),
        "jamb_left": rgba_piece(Rg, jl, f"{OUT}/holdout_jamb_left.png", f"{OUT}/holdout_jamb_left_contour.png"),
        "jamb_right": rgba_piece(Rg, jr, f"{OUT}/holdout_jamb_right.png", f"{OUT}/holdout_jamb_right_contour.png"),
        "iron": rgba_piece(Rg, iron, f"{OUT}/holdout_iron.png", f"{OUT}/holdout_iron_contour.png"),
    }
    Image.fromarray(fail * 255).save(f"{OUT}/failure_iron.png")
    # dark hall (HANDMADE): near-black warm interior, a dim lit floor strip, a far doorway glow
    hall = np.zeros((h, w, 3), np.float32) + [16, 12, 10]
    glow = np.exp(-((xx - 330.0) / 60.0) ** 2) * np.clip((yy - 500.0) / 500.0, 0, 1)
    hall += glow[..., None] * [70, 52, 34]
    hall += (np.exp(-((yy - 1215.0) / 25.0) ** 2))[..., None] * [22, 18, 14]
    hall += np.random.default_rng(2009).normal(0, 2.5, hall.shape)
    hall = hall * ((xx >= LEAF[0]) & (xx <= LEAF[1]) & (yy <= SILL_Y))[..., None]
    Image.fromarray(np.dstack([np.clip(hall, 0, 255).astype(np.uint8), (leaf > 0).astype(np.uint8) * 255]), "RGBA").save(f"{OUT}/hall.png")
    ov = Rg.copy()
    ov[leaf > 0] = (0.7 * ov[leaf > 0] + [0, 0, 70]).astype(np.uint8)
    ov[(jl > 0) | (jr > 0)] = (0.6 * ov[(jl > 0) | (jr > 0)] + [0, 90, 0]).astype(np.uint8)
    ov[m > 0] = [230, 60, 60]
    ov[fail > 0] = [0, 200, 255]
    for y in NOSES:
        cv2.line(ov, (0, y), (w, y), (0, 255, 0), 2)
    cv2.line(ov, (0, SILL_Y), (w, SILL_Y), (255, 0, 255), 2)
    Image.fromarray(ov).resize((466, 1025)).save(f"{OUT}/check.png")

    geom = {
        "plate": "loc-highsm.56276", "coords": "region px unless noted; master = region*3 + (7300,1500); preview = master*1024/13925",
        "unify_grade": {"type": "luminance levels, equal gain on R,G,B (no hue/saturation change)", "lum_lo": lo, "lum_hi": hi, "out": [4, 249]},
        "crops": crops,
        "hinge_axis": {"x": LEAF[0], "y_top": LEAF_Y[0], "y_bottom": LEAF_Y[1], "opens": "inward; stops at ~25 deg on the chain"},
        "leaf_x": list(LEAF), "leaf_y": list(LEAF_Y), "knob": [460, 860], "chain_anchor_leaf": [478, 780], "chain_anchor_frame": [500, 772],
        "jamb_left_x": list(JAMB_L), "jamb_right_x": list(JAMB_R), "sill_y": SILL_Y, "landing_y": [1255, 1380],
        "tread_noses_y": NOSES, "tread_x": [40, 560],
        "light": {"from": "upper right, low winter sun (tree-branch shadows fall down-left across the door, the step riser shadows fall left)",
                  "cast_shadow_dir_img": [-0.75, 0.66], "status": "estimated from the branch and baluster shadows in the plate"},
        "pieces": {k: {"rgba": f"{OUT}/{n}.png", "contour": f"{OUT}/{n}_contour.png", **st[k]} for k, n in
                   (("leaf", "piece_leaf"), ("jamb_left", "holdout_jamb_left"), ("jamb_right", "holdout_jamb_right"), ("iron", "holdout_iron"))},
        "failure_iron": f"{OUT}/failure_iron.png", "hall": f"{OUT}/hall.png", "check": f"{OUT}/check.png",
        "bird_height_region_px": [150, 180], "bird_note": "150-180 region px = 160-195 frame px in B (30-36 %); beak meets the kick plate / lower stile at y ~1150-1200",
        "dag": {"B": ["plate_B", "hall (where the leaf has swung)", "leaf (homography about hinge_axis, 0->25 deg)", "chain (HANDMADE, slack->taut)",
                      "bird_cast_shadow", "bird", "holdout_jamb_right (after E5)", "leaf edge as holdout while squeezing", "grain"],
                "A": ["plate_A", "watcher_cast_shadow", "bird_contact_shadow", "bird", "holdout_iron (preview-scaled)", "grain"]},
    }
    dump(geom, f"{OUT}/geometry.json")
    print(st, lo, hi)


if __name__ == "__main__":
    main()
