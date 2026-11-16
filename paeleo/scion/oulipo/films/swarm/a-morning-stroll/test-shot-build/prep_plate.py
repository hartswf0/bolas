"""#29/#45 plate pieces for THE KNOCK (shot B, 1959). Run with python3 -I.

Input : sources/.../test-shot/70651u_full.png  (LoC ppmsca.70651 master TIFF, decoded to greyscale by PIL)
Output: sources/.../test-shot/plate/ region.png (graded plate region), iron.png (railing holdout matte),
        leaf.png (left door-leaf matte), check_*.png (overlays for looking).
All coordinates are full-resolution plate pixels; REGION is the area the shot can see (with push margin).
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

OUL = "/home/user/bolas/paeleo/scion/oulipo"
SRC = f"{OUL}/films/sources/a-morning-stroll/test-shot"
OUT = f"{SRC}/plate"
os.makedirs(OUT, exist_ok=True)

REGION = (1530, 300, 2305, 750)          # x0, y0, x1, y1 (crop + margin)
CROP = (1545, 320, 2295, 742)            # the 16:9 shot frame at push 0 (750 x 422)
HINGE_X, LEAF_R = 1735, 1982             # left door leaf: hinge stile .. meeting stile
RAIL = ((1548, 690), (2010, 236))        # handrail centre line (two points on it)
RAIL_HALF = 13                           # half thickness, measured perpendicular


def floor_y(x):
    """Landing / threshold line (top of the dark band under the door), sloping with perspective."""
    return 645.0 - 0.2 * (x - 1950.0)


def rail_y(x):
    (xa, ya), (xb, yb) = RAIL
    return ya + (yb - ya) * (x - xa) / (xb - xa)


def main():
    full = np.asarray(Image.open(f"{SRC}/70651u_full.png").convert("L"), np.float32)
    x0, y0, x1, y1 = REGION
    L = full[y0:y1, x0:x1]
    h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w]
    X, Y = xx + x0, yy + y0

    # ---- one global tone curve: the print's black point (p1 = 80) to ink, its white (p99) to paper.
    p1, p99 = np.percentile(L, [1, 99.5])
    t = np.clip((L - p1) / (p99 - p1), 0, 1)
    t = t ** 1.15                       # mild toe: keeps the granite mid-greys, deepens the recess
    graded = np.clip(8 + t * 240, 0, 255)
    Image.fromarray(graded.astype(np.uint8)).save(f"{OUT}/region.png")

    # ---- handrail: band about the measured centre line
    (xa, ya), (xb, yb) = RAIL
    nx, ny = (yb - ya), -(xb - xa)
    nn = np.hypot(nx, ny)
    dist = ((X - xa) * nx + (Y - ya) * ny) / nn
    rail = (np.abs(dist) <= RAIL_HALF).astype(np.uint8)

    # ---- bars and lace panels: narrow bright vertical structure = white top-hat across x
    Lb = cv2.GaussianBlur(L, (0, 0), 1.2)
    open_h = cv2.morphologyEx(Lb, cv2.MORPH_OPEN, np.ones((1, 37), np.uint8))
    th = Lb - open_h
    iron = (th > 8).astype(np.uint8)
    below = Y > rail_y(X) - 2            # the iron hangs below the handrail
    iron &= below.astype(np.uint8)
    iron = cv2.morphologyEx(iron, cv2.MORPH_OPEN, np.ones((5, 1), np.uint8))   # drop speckle
    iron = cv2.morphologyEx(iron, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    # remove islands (#29 acceptance: no background islands)
    n, lab, st, _ = cv2.connectedComponentsWithStats(iron)
    keep = np.zeros_like(iron)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= 60 and st[k, cv2.CC_STAT_HEIGHT] >= 14:
            keep[lab == k] = 1
    iron = np.maximum(keep, rail)
    soft = cv2.GaussianBlur(iron.astype(np.float32) * 255, (0, 0), 0.7)
    Image.fromarray(soft.clip(0, 255).astype(np.uint8)).save(f"{OUT}/iron.png")

    # ---- left door leaf (hinged at HINGE_X), up to the threshold line
    leaf = ((X >= HINGE_X) & (X <= LEAF_R) & (Y <= floor_y(X))).astype(np.uint8) * 255
    Image.fromarray(leaf).save(f"{OUT}/leaf.png")

    # failure-mask export / look-check overlays
    rgb = np.dstack([graded] * 3).astype(np.uint8)
    ov = rgb.copy()
    ov[iron > 0] = (0.5 * ov[iron > 0] + [120, 0, 0]).astype(np.uint8)
    ov[(leaf > 0) & (iron == 0)] = (0.7 * ov[(leaf > 0) & (iron == 0)] + [0, 0, 60]).astype(np.uint8)
    Image.fromarray(ov).save(f"{OUT}/check_iron_leaf.png")
    json.dump({"REGION": REGION, "CROP": CROP, "HINGE_X": HINGE_X, "LEAF_R": LEAF_R, "RAIL": RAIL,
               "tone": {"p1": float(p1), "p99.5": float(p99), "gamma": 1.15, "out": [8, 248]}},
              open(f"{OUT}/plate.json", "w"), indent=1)
    print("plate p1/p99.5", p1, p99, "iron px", int(iron.sum()))


if __name__ == "__main__":
    main()
