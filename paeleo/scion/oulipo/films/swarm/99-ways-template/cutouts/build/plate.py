"""Second pass (after pieces.py): rebuild the empty-desk plate with periodic same-photo texture and remove the right
lamp's cord from the SERVICE door leaf. Reads only decoded pixels. python3 -I plate.py"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pieces_lib import levels, grain_fill  # noqa
HERE = Path(__file__).resolve().parent
CUT = HERE.parent; ROOT = CUT.parents[3]
SRC = ROOT / "films" / "sources" / "99-ways-template"; PIECES = SRC / "cutout-surgeon" / "pieces"
man = json.load(open(HERE / "pieces_out.json"))
R = cv2.imread(str(SRC / "test-shot" / "rothstein_master_s3.png"), cv2.IMREAD_GRAYSCALE)
LV = man["sources"]["rothstein"]["levels"]["lo_hi_gamma"]
Rl = levels(R, *LV)
clerk = cv2.imread(str(CUT / "failures" / "clerk_mask_full.png"), cv2.IMREAD_GRAYSCALE)
gone = clerk.copy()
cv2.fillPoly(gone, [np.int32([(2780, 1480), (3260, 1480), (3245, 1850), (3200, 1990), (3150, 2060), (3080, 2110),
                              (2990, 2135), (2900, 2110), (2830, 2050), (2780, 1900)])], 255)           # head + ears, generous
cv2.fillPoly(gone, [np.int32([(2110, 2560), (2470, 2550), (2510, 2660), (2480, 2890), (2110, 2900)])], 255)  # left arm on desk
gone = cv2.dilate(gone, np.ones((21, 21), np.uint8))
plate = Rl.copy()
# beadboard texture: periodic tiling of a clean wainscot strip left of the clerk (x 1560..2120), whole plank periods
bead = Rl[2000:2550, 1560:2120].astype(np.float32).mean(0); bead -= bead.mean()
ac = np.correlate(bead, bead, "full")[len(bead) - 1:]
period = int(np.argmax(ac[60:220]) + 60)
tile_w = period * max(1, (2120 - 1560) // period)
COUNTER_Y, DESK_Y = 1935, 2665
for y in range(1450, R.shape[0]):
    hx = np.nonzero(gone[y])[0]
    if not len(hx):
        continue
    xs = hx
    if y < COUNTER_Y:          # cupboard base / counter edge: same row from the right of the hole
        a, b = hx.min(), hx.max(); sh = b - a + 13
        src = xs + sh
        src = np.where(src > 4300, xs - sh, src)
    elif y < DESK_Y:           # wainscot behind the clerk: periodic tiling of the clean strip
        src = 1560 + ((xs - 1560) % tile_w)
    else:
        continue
    fill = Rl[y, np.clip(src, 0, R.shape[1] - 1)].astype(np.float32)
    # tone ramp: match the transplanted run to the photo's own tone on both sides of the hole on this row
    a, b = hx.min(), hx.max()
    L0 = float(Rl[y, max(a - 40, 0):max(a - 8, 1)].mean()); L1 = float(Rl[y, min(b + 8, R.shape[1] - 2):min(b + 40, R.shape[1] - 1)].mean())
    f0 = float(fill[: min(32, len(fill))].mean()); f1 = float(fill[-min(32, len(fill)):].mean())
    t = (xs - a) / max(1, b - a)
    if y < COUNTER_Y:
        fill = fill + (1 - t) * (L0 - f0) + t * (L1 - f1)
    plate[y, xs] = np.clip(fill, 0, 255).astype(np.uint8)
desk = gone.copy(); desk[:DESK_Y] = 0
plate = grain_fill(plate, desk, donor_shift=(0, -520), r=11)
edge = cv2.subtract(cv2.dilate(gone, np.ones((7, 7), np.uint8)), cv2.erode(gone, np.ones((7, 7), np.uint8)))
plate = np.where(edge > 0, cv2.GaussianBlur(plate, (0, 0), 1.6), plate).astype(np.uint8)
cv2.imwrite(str(PIECES / "rothstein.desk_empty.png"), plate)
cv2.imwrite(str(CUT / "failures" / "desk_empty_mask.png"), gone)
man["plates"]["rothstein.desk_empty"]["how"] = (
    f"clerk mask + generous head polygon + left-arm polygon, dilated 21 px. Rows y<{COUNTER_Y}: same-row transplant from the right "
    f"(cupboard base, counter edge). Rows {COUNTER_Y}..{DESK_Y}: periodic tiling of the clean wainscot strip x1560-2120 in whole plank "
    f"periods ({period} px, autocorrelation, tile {tile_w} px). Each counter-row run is tone-ramped to the photo on both sides of the hole on its row. Desk top: Telea low band + same-photo grain. 6 px seam blend.")
# SERVICE door leaf: the right pendant's cord hangs in front of it (x ~4052); remove it, keep the leaf
sd = man["pieces"]["rothstein.service_door"]
x0, y0, x1, y1 = sd["bbox_src"]
cord = np.zeros_like(R); cv2.line(cord, (4049, 0), (4056, 1720), 255, 23)
fixed = grain_fill(Rl, cord, donor_shift=(0, -40), r=6)
g = fixed[y0:y1, x0:x1]
cv2.imwrite(str(ROOT / sd["file"]), np.dstack([g, g, g, np.full_like(g, 255)]))
sd["note"] += " The right lamp's cord (x~4052) that hangs in front of the leaf is removed (same-photo wood grain)."
mb = cv2.copyMakeBorder(np.dstack([g, g, g, np.full_like(g, 255)]), 0, 0, 0, 0, cv2.BORDER_CONSTANT)
json.dump(man, open(HERE / "pieces_out.json", "w"), indent=1)
print("period", period, "tile", tile_w)
