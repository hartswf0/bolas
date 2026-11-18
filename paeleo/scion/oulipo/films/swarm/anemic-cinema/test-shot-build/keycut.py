"""SCION #29 GrabCut: cut the foraged skeleton key out of its photograph.

Input : films/sources/anemic-cinema/key_yale_towne_1280.png (Commons, Noy-nac, CC BY-SA 4.0)
Output: films/sources/anemic-cinema/test-shot/key_rgba.png, key_mask.png, key_failure.png,
        key_manifest.json (crop transform, mask statistics).
Method: luminance seeds (dark iron = probable fg, darkest = definite fg), a 14 px border as
definite background, the bow's hole seeded as definite background from its bright interior,
cv2.grabCut with mask init (6 iterations), largest component only, holes that touch the
background kept open, then a 1 px feathered alpha.
Run: python3 -I keycut.py
"""
import json
import numpy as np
import cv2

SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/anemic-cinema"
OUT = SRC + "/test-shot"

im = cv2.imread(SRC + "/key_yale_towne_1280.png", cv2.IMREAD_UNCHANGED)[:, :, :3]
h, w = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
bg_level = np.median(np.concatenate([g[:20].ravel(), g[-20:].ravel()]))

mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
mask[g < bg_level - 45] = cv2.GC_PR_FGD
mask[g < bg_level - 110] = cv2.GC_FGD
B = 14
mask[:B, :] = mask[-B:, :] = cv2.GC_BGD
mask[:, :B] = mask[:, -B:] = cv2.GC_BGD
# the bow's hole: bright pixels inside the bow (source x > 900) are definite background
hole_seed = (g > bg_level - 12)
hole_seed[:, :900] = False
mask[hole_seed] = cv2.GC_BGD
# cast shadow: unsaturated mid-grey within 14 px of clean paper is definite background
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
paper = ((g > bg_level - 10) & (hsv[..., 1] < 10)).astype(np.uint8)
near = cv2.dilate(paper, np.ones((29, 29), np.uint8)) > 0
shadow = near & (hsv[..., 1] < 22) & (g > 85)
mask[shadow] = cv2.GC_BGD
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(im, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
islands_removed = int(n - 2)
fg = (lab == k).astype(np.uint8)
# fill only pin-holes (< 400 px) inside the key; keep the bow's hole open
inv = 1 - fg
n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
holes = [(i, st2[i, cv2.CC_STAT_AREA]) for i in range(1, n2)
         if st2[i, cv2.CC_STAT_LEFT] > 0 and st2[i, cv2.CC_STAT_TOP] > 0
         and st2[i, cv2.CC_STAT_LEFT] + st2[i, cv2.CC_STAT_WIDTH] < w and st2[i, cv2.CC_STAT_TOP] + st2[i, cv2.CC_STAT_HEIGHT] < h]
bow_hole_area = 0
for i, a in holes:
    if a < 3000:
        fg[lab2 == i] = 1
    else:
        bow_hole_area = max(bow_hole_area, int(a))
n3, _, _, _ = cv2.connectedComponentsWithStats(fg)
assert n3 == 2, "background islands remain"
assert bow_hole_area > 20000, "bow hole lost"
ys, xs = np.nonzero(fg)
y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 4, xs.max() + 5
# bit teeth: the notch between the two teeth (cols 200-260 in the source, rows above the shank)
teeth = fg[40:175, 150:320]
notch_open = bool(teeth[10:70, 70:110].mean() < 0.2)
assert notch_open, "bit notch filled"
a = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.8)
rgba = np.dstack([im, (np.clip(a, 0, 1) * 255).astype(np.uint8)])[y0:y1, x0:x1]
cv2.imwrite(OUT + "/key_rgba.png", rgba)
cv2.imwrite(OUT + "/key_mask.png", (fg[y0:y1, x0:x1] * 255).astype(np.uint8))
# failure overlay: red = pixels whose final label disagrees with the luminance seed
seedfg = (g < bg_level - 45).astype(np.uint8)
over = im.copy()
over[(fg == 1) & (seedfg == 0)] = (0, 0, 255)
over[(fg == 0) & (seedfg == 1)] = (255, 0, 0)
cv2.imwrite(OUT + "/key_failure.png", over[y0:y1, x0:x1])
man = {"source": SRC + "/key_yale_towne_1280.png", "source_size": [w, h],
       "crop_xywh_in_source": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
       "background_level": float(bg_level), "grabcut_iterations": 6,
       "islands_removed": islands_removed, "island_count_after": 0,
       "bow_hole_area_px": bow_hole_area, "bit_notch_open": notch_open,
       "failure_overlay": "red = kept although brighter than seed; blue = dropped although darker than seed"}
json.dump(man, open(OUT + "/key_manifest.json", "w"), indent=1)
print(man)
