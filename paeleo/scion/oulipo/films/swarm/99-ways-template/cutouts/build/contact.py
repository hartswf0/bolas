"""Rebuild margins, tone stats and cutouts/contact.jpg from pieces_out.json (after plate.py). python3 -I contact.py"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pieces_lib import *  # noqa
def soften(m, r=1.2):
    return cv2.GaussianBlur(m, (0, 0), r)
HERE = Path(__file__).resolve().parent
CUT = HERE.parent; ROOT = CUT.parents[3]
PIECES = ROOT / "films" / "sources" / "99-ways-template" / "cutout-surgeon" / "pieces"
man = json.load(open(HERE / "pieces_out.json"))
plate = cv2.imread(str(PIECES / "rothstein.desk_empty.png"), cv2.IMREAD_GRAYSCALE)
def bake_margin(rgba, px):
    """white scissor margin of `px` pixels (in the piece's own pixels) around the alpha, paper (247,246,242), slightly irregular"""
    a = rgba[..., 3]
    pad = px + 4
    rgba = cv2.copyMakeBorder(rgba, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
    a = rgba[..., 3]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    m = cv2.dilate((a > 127).astype(np.uint8) * 255, k)
    m = cv2.approxPolyDP if False else m
    m = soften(m, 0.9)
    out = np.zeros_like(rgba)
    out[..., 0], out[..., 1], out[..., 2] = 242, 246, 247   # BGR
    out[..., 3] = m
    al = a[..., None].astype(np.float32) / 255
    out[..., :3] = (rgba[..., :3] * al + out[..., :3] * (1 - al)).astype(np.uint8)
    return out


tiles = []
for name, rec in man["pieces"].items():
    im = cv2.imread(str(ROOT / rec["file"]), cv2.IMREAD_UNCHANGED)
    sc = (rec["scale_to_page_nominal"] or {"x": 0.25})
    s0 = list(sc.values())[-1]
    mpx = max(2, int(round(8 / s0)))
    mb = bake_margin(im, mpx)
    cv2.imwrite(str(PIECES / f"{name}.margin.png"), mb)
    rec["file_with_margin"] = str((PIECES / f"{name}.margin.png").relative_to(ROOT))
    rec["margin_px_local"] = mpx
    a = mb[..., 3:4].astype(np.float32) / 255
    chk = np.where(((np.indices(mb.shape[:2]).sum(0) // 24) % 2)[..., None] == 0, 120, 70).astype(np.float32)
    comp = mb[..., :3] * a + chk * (1 - a)
    for k, (px, py) in rec["pivots_local"].items():
        cv2.circle(comp, (int(px + mpx + 4), int(py + mpx + 4)), max(4, int(6 / s0 / 3)), (0, 0, 255), -1)
    h = 360
    t = cv2.resize(comp.astype(np.uint8), (max(40, int(comp.shape[1] * h / comp.shape[0])), h), interpolation=cv2.INTER_AREA)
    t = cv2.copyMakeBorder(t, 0, 24, 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(t, name.replace("rothstein.", "r.")[:30], (4, h + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    tiles.append(t)
rows, row, wsum = [], [], 0
for t in tiles:
    if wsum + t.shape[1] > 2400 and row:
        rows.append(row); row, wsum = [], 0
    row.append(t); wsum += t.shape[1]
rows.append(row)
W = max(sum(t.shape[1] for t in r) for r in rows)
sheet = np.vstack([np.hstack(r + [np.full((r[0].shape[0], W - sum(t.shape[1] for t in r), 3), 255, np.uint8)]) for r in rows])
pl = cv2.resize(cv2.cvtColor(plate, cv2.COLOR_GRAY2BGR), (W, int(3100 * W / 4360)), interpolation=cv2.INTER_AREA)
sheet = np.vstack([sheet, pl])
cv2.imwrite(str(CUT / "contact.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])

# tone stats per piece (levelled, inside alpha): share of pixels L>220 and L<40, to steer plate choice toward high-key
for name, rec in man["pieces"].items():
    im = cv2.imread(str(ROOT / rec["file"]), cv2.IMREAD_UNCHANGED)
    g = im[..., 0][im[..., 3] > 127]
    rec["tone"] = {"pct_L_gt_220": round(float((g > 220).mean() * 100), 1), "pct_L_lt_40": round(float((g < 40).mean() * 100), 1),
                   "median": int(np.median(g))}
json.dump(man, open(HERE / "pieces_out.json", "w"), indent=1)
print("ok")
