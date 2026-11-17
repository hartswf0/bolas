"""Third pass: pieces.py's arm polygon swallowed the right ear and temple edge (they went to the pencil arm and were then
painted over in the head). Re-split head / pencil arm / forearm from the saved full clerk mask: inside the head zone the arm
keeps only the pencil strip; the ear returns to the head; only the pencil strip is repaired. python3 -I fix_head.py"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pieces_lib import levels, grain_fill  # noqa
HERE = Path(__file__).resolve().parent; CUT = HERE.parent; ROOT = CUT.parents[3]
SRC = ROOT / "films" / "sources" / "99-ways-template"; PIECES = SRC / "cutout-surgeon" / "pieces"
man = json.load(open(HERE / "pieces_out.json"))
R = cv2.imread(str(SRC / "test-shot" / "rothstein_master_s3.png"), cv2.IMREAD_GRAYSCALE)
Rl = levels(R, *man["sources"]["rothstein"]["levels"]["lo_hi_gamma"])
clerk = cv2.imread(str(CUT / "failures" / "clerk_mask_full.png"), cv2.IMREAD_GRAYSCALE)
soft = lambda m: cv2.GaussianBlur(m, (0, 0), 1.2)
def keep(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    return np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8) if n > 1 else m
def bb(m, pad=6):
    ys, xs = np.nonzero(m); return (xs.min() - pad, ys.min() - pad, xs.max() + pad + 1, ys.max() + pad + 1)
head_poly = np.int32([(2780, 1480), (3290, 1480), (3290, 1850), (3230, 1960), (3150, 2060), (3080, 2110),
                      (2990, 2135), (2900, 2110), (2830, 2050), (2780, 1900)])
hp = np.zeros_like(clerk); cv2.fillPoly(hp, [head_poly], 255)
pen = np.zeros_like(clerk); cv2.line(pen, (3138, 1772), (3214, 1995), 255, 21, cv2.LINE_AA); pen = (pen > 0).astype(np.uint8) * 255
# the arm below the jaw line (fist, forearm, sleeve) + the pencil strip
arm_poly = np.int32([(3175, 1955), (3300, 2030), (3420, 2040), (3470, 2140), (3520, 2250), (3700, 2420), (3790, 2560),
                     (3800, 2665), (3560, 2665), (3470, 2560), (3420, 2330), (3330, 2250), (3250, 2200), (3200, 2120), (3160, 2030)])
ap = np.zeros_like(clerk); cv2.fillPoly(ap, [arm_poly], 255)
arm = keep(cv2.bitwise_or(cv2.bitwise_and(clerk, ap), cv2.bitwise_and(pen, cv2.dilate(clerk, np.ones((9, 9), np.uint8)))))
head = cv2.bitwise_and(cv2.bitwise_and(clerk, hp), cv2.bitwise_not(cv2.bitwise_and(arm, cv2.bitwise_not(pen))))
head = cv2.bitwise_or(head, cv2.bitwise_and(pen, cv2.erode(cv2.morphologyEx(cv2.bitwise_and(clerk, hp), cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8)), np.ones((5, 5), np.uint8))))
head = keep(cv2.morphologyEx(head, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
pen_face = pen.copy(); pen_face[1880:] = 0   # below y 1880 the pencil is over the dark background, not the face
head = cv2.bitwise_and(head, cv2.bitwise_not(cv2.bitwise_and(pen, cv2.bitwise_not(pen_face))))
head = keep(cv2.morphologyEx(head, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)))
Hg = grain_fill(Rl, cv2.bitwise_and(cv2.dilate(pen_face, np.ones((3, 3), np.uint8)), hp), donor_shift=(0, -26), r=5)
cv2.imwrite(str(CUT / "failures" / "head_pencil_repair_mask.png"), cv2.bitwise_and(pen, hp))
fore_poly = np.int32([(3128, 1760), (3150, 1755), (3225, 1960), (3300, 2030), (3420, 2040), (3500, 2180), (3640, 2380), (3790, 2560),
                      (3800, 2665), (3600, 2665), (3520, 2520), (3380, 2330), (3250, 2200), (3200, 2120), (3175, 2050)])
fp = np.zeros_like(clerk); cv2.fillPoly(fp, [fore_poly], 255)
fore = keep(cv2.bitwise_and(arm, fp))
for name, g, a in [("rothstein.clerk.head", Hg, head), ("rothstein.clerk.pencil_arm", Rl, arm), ("rothstein.clerk.forearm_pencil", Rl, fore)]:
    rec = man["pieces"][name]
    ox, oy = rec["bbox_src"][:2]
    absp = {k: (v[0] + ox, v[1] + oy) for k, v in rec["pivots_local"].items()}
    x0, y0, x1, y1 = [int(v) for v in bb(a)]
    gg, aa = g[y0:y1, x0:x1], soft(a)[y0:y1, x0:x1]
    cv2.imwrite(str(ROOT / rec["file"]), np.dstack([gg, gg, gg, aa]))
    rec["bbox_src"] = [x0, y0, x1, y1]; rec["size"] = [x1 - x0, y1 - y0]
    rec["pivots_local"] = {k: [round(v[0] - x0, 1), round(v[1] - y0, 1)] for k, v in absp.items()}
    rec["alpha_components"] = int(cv2.connectedComponents((aa > 127).astype(np.uint8))[0] - 1)
man["pieces"]["rothstein.clerk.head"]["note"] = ("hinged at the collar (pivot). The pencil strip across the temple/ear is repaired with same-photo "
    "skin grain (mask in cutouts/failures); the right ear is kept. Gaze is DOWN (reading) in the only Randolph frame; see bubley82.agent.head.")
json.dump(man, open(HERE / "pieces_out.json", "w"), indent=1)
print({k: man["pieces"][k]["alpha_components"] for k in ("rothstein.clerk.head", "rothstein.clerk.pencil_arm", "rothstein.clerk.forearm_pencil")})
