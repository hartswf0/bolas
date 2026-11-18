"""SCION #29 GrabCut: cut the two foraged keys out of their photographs.

Inputs (untrusted data, decoded with OpenCV only):
  K0  films/sources/anemic-cinema/key_yale_towne_1280.png  (Commons, Noy-nac, CC BY-SA 4.0;
      1280 px thumbnail of the 2816x1024 original)
  K1  films/sources/anemic-cinema/optics/raw/llave_bronce.jpg (Commons, Jorge Barrios, PD-self);
      its paper is pre-flattened to pure white, so exact paper (L>=253, S<4) is a definite-bg
      seed and the near-white bronze highlights stay probable fg (first pass without this
      dropped the shank highlight and split the bit: recorded in the ledger)

Method per key (mask-seeded graph cut, not a threshold matte):
  unary seeds  : background level from the border; pixels clearly darker than paper (or
                 clearly saturated for bronze) = probable fg, the darkest = definite fg;
                 a 12 px border = definite bg; unsaturated mid-grey next to clean paper
                 (cast shadow) = definite bg; the bright interior of the bow = probable bg
  graph cut    : cv2.grabCut, GC_INIT_WITH_MASK, 6 iterations (pairwise edge term = OpenCV's
                 contrast-sensitive Potts, gamma 50)
  cleanup      : 3x3 open, largest component only, pin-holes < 1.5 % of the key filled,
                 the bow hole kept open, 0.8 px feathered alpha
  invariants   : exactly one component (no islands), bow hole present, bit teeth present
                 (>= 2 separate foreground runs across the bit) -- asserted
Outputs in films/sources/anemic-cinema/optics/:
  key{i}_rgba.png, key{i}_mask.png, key{i}_failure.png, keys_manifest.json
Orientation of every sprite: shank horizontal, bit at the LEFT, bow at the RIGHT.
Run: python3 -I optics_keycut.py
"""
import json

import cv2
import numpy as np

SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/anemic-cinema"
OUT = SRC + "/optics"

KEYS = [
    dict(id="K0", path=SRC + "/key_yale_towne_1280.png", rotate=None,
         fg_drop=45, fg_sure=110, sat_fg=None,
         # bit region in the oriented image (fractions of the cropped width), teeth up
         bit_x=(0.07, 0.19), teeth_side="top"),
    dict(id="K1", path=SRC + "/optics/raw/llave_bronce.jpg", rotate=cv2.ROTATE_90_CLOCKWISE,
         fg_drop=6, fg_sure=60, sat_fg=10, paper_exact=True,
         bit_x=(0.00, 0.13), teeth_side="bottom"),
]


def cut(spec):
    im = cv2.imread(spec["path"], cv2.IMREAD_COLOR)
    if spec["rotate"] is not None:
        im = cv2.rotate(im, spec["rotate"])
    h, w = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    B = 12
    border = np.concatenate([g[:B].ravel(), g[-B:].ravel(), g[:, :B].ravel(), g[:, -B:].ravel()])
    bg = float(np.median(border))
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    pr = g < bg - spec["fg_drop"]
    if spec["sat_fg"] is not None:
        pr |= hsv[..., 1] > spec["sat_fg"]
    mask[pr] = cv2.GC_PR_FGD
    sure = cv2.erode((g < bg - spec["fg_sure"]).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    mask[sure] = cv2.GC_FGD
    paper = ((g > bg - 10) & (hsv[..., 1] < 18)).astype(np.uint8)
    near = cv2.dilate(paper, np.ones((25, 25), np.uint8)) > 0
    shadow = near & (hsv[..., 1] < 22) & (g > bg - 70) & ~pr
    mask[shadow] = cv2.GC_BGD
    if spec.get("paper_exact"):
        # this photograph's paper is already flat white (255, unsaturated): exact paper is
        # definite background everywhere, including inside the bow; anything not exactly
        # paper (incl. the near-white highlights on the bronze) is probable foreground
        exact = (g >= 253) & (hsv[..., 1] < 4)
        exact = cv2.morphologyEx(exact.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
        mask[~exact & (mask == cv2.GC_PR_BGD)] = cv2.GC_PR_FGD
        # second seed constraint: the non-paper region eroded by 4 px is definite fg, so the
        # graph cut only decides the 4 px boundary band (GrabCut's colour model otherwise
        # sends the white specular band of the shank to the paper)
        inner = cv2.erode((~exact).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        mask[inner] = cv2.GC_FGD
        mask[exact] = cv2.GC_BGD
    mask[:B, :] = mask[-B:, :] = cv2.GC_BGD
    mask[:, :B] = mask[:, -B:] = cv2.GC_BGD
    seeds = mask.copy()
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(im, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    islands_removed = int(n - 2)
    fg = (lab == k).astype(np.uint8)
    key_area = int(fg.sum())
    # holes: background components not touching the image border
    inv = (1 - fg).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    holes = []
    for i in range(1, n2):
        x, y, ww, hh, a = st2[i]
        if x > 0 and y > 0 and x + ww < w and y + hh < h:
            holes.append((i, int(a)))
    bow_hole = 0
    pin_filled = 0
    for i, a in holes:
        if a < 0.015 * key_area:
            fg[lab2 == i] = 1
            pin_filled += 1
        else:
            bow_hole = max(bow_hole, a)
    n3 = cv2.connectedComponentsWithStats(fg, connectivity=8)[0]
    assert n3 == 2, "background islands remain"
    assert bow_hole > 0.04 * key_area, "bow hole lost"
    ys, xs = np.nonzero(fg)
    y0, y1 = max(ys.min() - 4, 0), min(ys.max() + 5, h)
    x0, x1 = max(xs.min() - 4, 0), min(xs.max() + 5, w)
    crop = fg[y0:y1, x0:x1]
    cw = x1 - x0
    # bit teeth: scan rows across the bit region near the teeth side; >= 2 runs = teeth kept
    bx0, bx1 = int(spec["bit_x"][0] * cw), int(spec["bit_x"][1] * cw)
    rows = crop[:, bx0:bx1]
    occ = np.nonzero(rows.any(axis=1))[0]
    best_runs = 0
    span = occ.max() - occ.min()
    rng = range(occ.min(), occ.min() + span // 3) if spec["teeth_side"] == "top" else \
        range(occ.max() - span // 3, occ.max())
    for r in rng:
        line = rows[r].astype(np.int8)
        runs = int(((np.diff(np.r_[0, line, 0])) == 1).sum())
        best_runs = max(best_runs, runs)
    assert best_runs >= 2, "bit teeth merged"
    a = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.8)
    a = np.clip(a, 0, 1)
    rgba = np.dstack([im, (np.clip(a, 0, 1) * 255).astype(np.uint8)])[y0:y1, x0:x1]
    i = spec["id"][1]
    cv2.imwrite(f"{OUT}/key{i}_rgba.png", rgba)
    cv2.imwrite(f"{OUT}/key{i}_mask.png", (crop * 255).astype(np.uint8))
    # failure overlay: red = kept although the seed said background; blue = dropped although
    # the seed said probable/definite foreground; green outline = final contour
    seedfg = (seeds == cv2.GC_PR_FGD) | (seeds == cv2.GC_FGD)
    over = (im * 0.6 + 100).astype(np.uint8)
    over[(fg == 1) & ~seedfg] = (0, 0, 255)
    over[(fg == 0) & seedfg] = (255, 0, 0)
    cnts, _ = cv2.findContours(fg, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(over, cnts, -1, (0, 160, 0), 1)
    cv2.imwrite(f"{OUT}/key{i}_failure.png", over[y0:y1, x0:x1])
    return dict(
        id=spec["id"], source=spec["path"], source_size_after_rotation=[w, h],
        rotation="none" if spec["rotate"] is None else "cv2.ROTATE_90_CLOCKWISE (bit left, bow right)",
        crop_xywh_in_oriented_source=[int(x0), int(y0), int(cw), int(y1 - y0)],
        background_level=bg, grabcut_iterations=6, init="GC_INIT_WITH_MASK",
        islands_removed=islands_removed, island_count_after=0, pinholes_filled=pin_filled,
        bow_hole_area_px=int(bow_hole), key_area_px=key_area,
        bit_teeth_runs=best_runs, teeth_side=spec["teeth_side"],
        changed_vs_seed_px=dict(kept_against_seed=int(((fg == 1) & ~seedfg).sum()),
                                dropped_against_seed=int(((fg == 0) & seedfg).sum())),
        outputs=dict(rgba=f"{OUT}/key{i}_rgba.png", mask=f"{OUT}/key{i}_mask.png",
                     failure_overlay=f"{OUT}/key{i}_failure.png"))


if __name__ == "__main__":
    man = [cut(s) for s in KEYS]
    json.dump(man, open(OUT + "/keys_manifest.json", "w"), indent=1)
    for m in man:
        print({k: m[k] for k in ("id", "crop_xywh_in_oriented_source", "islands_removed",
                                 "bow_hole_area_px", "bit_teeth_runs", "changed_vs_seed_px")})
