"""VARIANT-BUILDERS: GrabCut (SCION #29) of the VISITOR from the Bubley 1943 master (LoC 2017861739, 8d33109u.tif).
Seeds: a hand-authored outline polygon (scribble) -> definite FG core (eroded), probable FG inside, probable BG band,
definite BG outside. Graph cut at 1/2 res, mask upsampled, one connected component kept, holes between the
arms/legs kept as background where GrabCut finds them. Writes RGBA piece + mask + failure overlay.
Run: python3 -I cut_visitor.py   (reads only decoded pixels of the foraged master)"""
import json
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MEDIA = ROOT / "films" / "sources" / "99-ways-template" / "variant-builders"
SRCP = MEDIA / "loc" / "8d33109u.png"
OUT = MEDIA / "pieces"
OUT.mkdir(parents=True, exist_ok=True)

OX, OY = 2350, 1350            # crop origin in master px; polygon authored at 1/3 of master scale
POLY3 = [(205, 34), (248, 54), (268, 92), (258, 132), (300, 158), (345, 188), (364, 240), (374, 292), (360, 325),
         (350, 352), (352, 400), (360, 500), (366, 600), (370, 652), (336, 662), (330, 720), (322, 790), (332, 850),
         (322, 870), (282, 872), (275, 840), (270, 790), (266, 720), (262, 672), (252, 672), (250, 730), (252, 800),
         (268, 840), (262, 875), (232, 875), (226, 830), (224, 790), (206, 730), (188, 668), (100, 662), (74, 640),
         (80, 560), (84, 450), (76, 334), (66, 300), (62, 250), (80, 180), (114, 158), (166, 146), (170, 128),
         (165, 92), (174, 56)]


def main():
    a = cv2.imread(str(SRCP), cv2.IMREAD_GRAYSCALE)
    crop = a[OY:OY + 2700, OX:OX + 1350]
    sc = 2
    small = cv2.resize(crop, (crop.shape[1] // sc, crop.shape[0] // sc), interpolation=cv2.INTER_AREA)
    poly = (np.array(POLY3, np.float32) * 3 / sc).astype(np.int32)
    h, w = small.shape
    inside = np.zeros((h, w), np.uint8)
    cv2.fillPoly(inside, [poly], 255)
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    core = cv2.erode(inside, k(12))
    band = cv2.dilate(inside, k(8))
    m = np.full((h, w), cv2.GC_BGD, np.uint8)
    m[band > 0] = cv2.GC_PR_BGD
    m[inside > 0] = cv2.GC_PR_FGD
    m[core > 0] = cv2.GC_FGD
    img = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, m, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    fgm = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fgm = cv2.morphologyEx(fgm, cv2.MORPH_OPEN, k(1))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fgm)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    fgm = np.where(lab == big, 255, 0).astype(np.uint8)
    # small background specks inside the figure (apron folds GrabCut mis-labels) are filled; real holes (>400 px) kept
    inv = 255 - fgm
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n2):
        x, y, ww, hh, ar = st2[i]
        if ar < 400 and x > 0 and y > 0 and x + ww < w and y + hh < h:
            fgm[lab2 == i] = 255
    full = cv2.resize(fgm, (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_LINEAR)
    full = cv2.GaussianBlur(full, (0, 0), 1.2)
    alpha = np.where(full > 127, 255, 0).astype(np.uint8)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    ys, xs = np.nonzero(alpha > 10)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([crop[y0:y1, x0:x1]] * 3 + [alpha[y0:y1, x0:x1]])
    cv2.imwrite(str(OUT / "bubley.visitor.hi.png"), rgba)
    over = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
    cnt, _ = cv2.findContours((alpha > 127).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(over, cnt, -1, (0, 0, 255), 4)
    cv2.imwrite(str(OUT / "bubley.visitor.hi.check.jpg"), cv2.resize(over, (over.shape[1] // 3, over.shape[0] // 3)))
    ncomp = cv2.connectedComponents((alpha > 127).astype(np.uint8))[0] - 1
    # pivots in piece-local px: head (crown), hip (walk pivot), feet (ground contact)
    rec = {"file": str((OUT / "bubley.visitor.hi.png").relative_to(ROOT)), "source": "LoC 2017861739 Bubley 1943 (8d33109u.tif master)",
           "bbox_src": [int(OX + x0), int(OY + y0), int(OX + x1), int(OY + y1)],
           "pivots_local": {"crown": [int(205 * 3 - x0), int(30 * 3 - y0)], "hip": [int(220 * 3 - x0), int(420 * 3 - y0)],
                            "feet": [int(270 * 3 - x0), int(870 * 3 - y0)]},
           "alpha_components": int(ncomp), "method": "cv2.grabCut, mask init from hand-authored outline polygon (scribble), 6 iters at 1/2 res"}
    json.dump(rec, open(OUT / "bubley.visitor.hi.json", "w"), indent=1)
    print(rec)


if __name__ == "__main__":
    main()
