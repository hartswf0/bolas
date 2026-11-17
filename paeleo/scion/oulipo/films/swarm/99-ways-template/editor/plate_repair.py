"""Editor r1: repair the clerk-removed Rothstein plates (office + set) with pixels of the SAME photograph.
 - head ghost (pale dome where his head was): the cupboard stile by same-column copy from above; the wall by Telea
   plus grain high-passed from the same wall
 - desk-left smear (where his hand lay): wainscot by same-column copy from the planks directly above (they are
   vertical), desk top by Telea + grain from the same desk top
 - chair-back silhouette in the wainscot: horizontal copy by two whole plank periods (2 x 143 px)
No filters; every filled pixel is Rothstein 2017776093. Run: python3 -I plate_repair.py"""
import cv2, numpy as np, json
from pathlib import Path
SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways-template")
PC = SRC / "page-cartoonist" / "pieces"
OUT = SRC / "editor"
off = cv2.imread(str(PC / "office.plate.png"), cv2.IMREAD_GRAYSCALE)
setp = cv2.imread(str(PC / "set.plate.png"), cv2.IMREAD_GRAYSCALE)
g = off.copy()
mask = np.zeros_like(g)
log = []

def colcopy(x0, x1, y0, y1, dy):
    g[y0:y1, x0:x1] = g[y0 - dy:y1 - dy, x0:x1].copy(); mask[y0:y1, x0:x1] = 255
    log.append(f"same-column copy x{x0}-{x1} y{y0}-{y1} from {dy}px above")

def rowcopy(x0, x1, y0, y1, dx):
    g[y0:y1, x0:x1] = g[y0:y1, x0 - dx:x1 - dx].copy(); mask[y0:y1, x0:x1] = 255
    log.append(f"horizontal copy x{x0}-{x1} y{y0}-{y1} from {dx}px left")

def grain(box, h, w):
    gx0, gy0, gx1, gy1 = box
    patch = g[gy0:gy1, gx0:gx1].astype(np.float32)
    hp = patch - cv2.GaussianBlur(patch, (0, 0), 5)
    return np.tile(hp, (h // hp.shape[0] + 1, w // hp.shape[1] + 1))[:h, :w]

def rowinterp(x0, x1, y0, y1, gbox, axis="x"):
    """fill a box by linear interpolation between its two (blurred) boundary lines, plus grain high-passed from a
    clean patch of the same photograph (gbox)"""
    b = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 3)
    if axis == "x":
        L, R = b[y0:y1, x0 - 4][:, None], b[y0:y1, x1 + 3][:, None]
        u = np.linspace(0, 1, x1 - x0)[None, :]
    else:
        L, R = b[y0 - 4, x0:x1][None, :], b[y1 + 3, x0:x1][None, :]
        u = np.linspace(0, 1, y1 - y0)[:, None]
    f = L * (1 - u) + R * u + grain(gbox, y1 - y0, x1 - x0)
    g[y0:y1, x0:x1] = np.clip(f, 0, 255).astype(np.uint8); mask[y0:y1, x0:x1] = 255
    log.append(f"interpolated between boundary {'columns' if axis=='x' else 'rows'} x{x0}-{x1} y{y0}-{y1}, grain from {gbox}")

def match_top(x0, x1, y0, y1, ref_rows=12, fade=120):
    """after a copy: remove the tonal step at its top edge (per-column offset, faded downward)"""
    a = g[y0 - ref_rows:y0, x0:x1].astype(np.float32).mean(0)
    b = g[y0:y0 + ref_rows, x0:x1].astype(np.float32).mean(0)
    d = cv2.GaussianBlur((a - b)[None, :], (0, 0), 6)[0]
    w = np.clip(1 - np.arange(y1 - y0) / fade, 0, 1)[:, None]
    g[y0:y1, x0:x1] = np.clip(g[y0:y1, x0:x1] + d[None, :] * w, 0, 255).astype(np.uint8)

def telea(poly, grain_box):
    m = np.zeros_like(g); cv2.fillPoly(m, [np.int32(poly)], 255)
    f = cv2.inpaint(g, m, 12, cv2.INPAINT_TELEA).astype(np.float32)
    gx0, gy0, gx1, gy1 = grain_box
    patch = g[gy0:gy1, gx0:gx1].astype(np.float32)
    hp = patch - cv2.GaussianBlur(patch, (0, 0), 6)
    ys, xs = np.nonzero(m)
    th, tw = hp.shape
    f[ys, xs] += hp[(ys - ys.min()) % th, (xs - xs.min()) % tw]
    mm = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 2)
    g[:] = np.clip(g * (1 - mm) + f * mm, 0, 255).astype(np.uint8); mask[m > 0] = 255
    log.append(f"Telea + same-photo grain from {grain_box} over poly {np.int32(poly).tolist()}")

# 1 head ghost: the stile (a vertical board) from directly above, tone-matched; the wall between paper pile and stile
colcopy(3058, 3230, 1520, 1890, 360)
match_top(3058, 3230, 1520, 1890)
rowinterp(2838, 3058, 1528, 1886, (2560, 1040, 2660, 1160))
# 2 chair-back silhouette in the wainscot (below its cap rail): two plank periods to the left
rowcopy(3290, 3575, 2012, 2600, 286)
# 2b the arm's residue over the wainscot left of the desk: three plank periods to the left
rowcopy(2290, 2640, 2040, 2600, 429)
# 3 desk-left smear: wainscot above the desk's back edge from the planks above; desk top between folder and desk
colcopy(2080, 2480, 2600, 2775, 175)
colcopy(2460, 2870, 2596, 2650, 50)
rowinterp(2080, 2482, 2775, 2905, (2620, 2860, 2860, 2960))
# feather every seam: 6 px soft edge between the repaired and the untouched photograph
F = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 5)
F = np.maximum(F, (cv2.erode(mask, np.ones((15, 15), np.uint8)) > 0).astype(np.float32))
g = np.clip(off.astype(np.float32) * (1 - F) + g.astype(np.float32) * F, 0, 255).astype(np.uint8)
mask = (F > 0.02).astype(np.uint8) * 255
cv2.imwrite(str(OUT / "office.plate.r1.png"), g)
s2 = setp.copy()
ob = (3124, 796, 3716, 1904)
mm = mask.copy(); mm[ob[1]:ob[3], ob[0]:ob[2]] = 0
s2[mm > 0] = g[mm > 0]
cv2.imwrite(str(OUT / "set.plate.r1.png"), s2)
cv2.imwrite(str(OUT / "plate_repair_mask.png"), mask)
json.dump({"source": "LoC 2017776093 (Rothstein 1937), page-cartoonist office/set plates", "ops": log},
          open(OUT / "plate_repair.json", "w"), indent=1)
print("\n".join(log))
