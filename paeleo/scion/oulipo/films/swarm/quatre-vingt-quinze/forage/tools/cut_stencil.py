"""Cut two-level stencil plates from Delano's 1943 Union Station photograph (LoC 2017843779, PD) and print
them as one flat ink at cell resolution 900x600. Each plate: hand-placed crop, a small median to merge grain into
cuttable islands, ONE hand-chosen threshold, islands under MIN_ISLAND px dropped and bridges-free holes under
MIN_HOLE filled (what a knife could actually cut), hand-placed erase/fill masks (figures removed), edge
smoothed at sub-pixel only so the plate edge is a clean cut. Output RGBA: ink where the photograph is dark,
transparent paper elsewhere. No halftone, no grey levels, no grain."""
import sys, json, numpy as np, cv2
from PIL import Image
src, out_dir = sys.argv[1], sys.argv[2]
g0 = np.array(Image.open(src).convert("L"))
PLATES = {
 "A": dict(crop=(90, 70, 941, 637), th=60, ink=(252, 208, 202), min_island=120, min_hole=90, median=3,
           erase=[(180, 425, 250, 515), (625, 495, 725, 570)],   # two travellers removed by hand
           fill=[], note="colonnade, far benches and clock kiosk; pale salmon on the white wall cell (behind the visitor)"),
 "H": dict(crop=(600, 560, 945, 790), th=70, ink=(232, 146, 132), min_island=300, min_hole=200, median=3,
           erase=[(240, 0, 445, 140)], fill=[],   # seated traveller on the far bench removed by hand
           note="right-hand rows of empty high-backed benches (crop starts right of the standing guard); mid salmon on the white cell"),
}
rec = {}
for name, p in PLATES.items():
    x0, y0, x1, y1 = p["crop"]
    c = cv2.resize(g0[y0:y1, x0:x1], (900, 600), interpolation=cv2.INTER_CUBIC)
    c = cv2.medianBlur(c, p["median"])
    m = (c < p["th"]).astype(np.uint8)
    for (a, b, cc, d) in p["erase"]:
        m[b:d, a:cc] = 0
    for (a, b, cc, d) in p["fill"]:
        m[b:d, a:cc] = 1
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= p["min_island"]
    m = keep[lab].astype(np.uint8)
    inv = 1 - m
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    small = np.zeros(n, bool); small[1:] = st[1:, cv2.CC_STAT_AREA] < p["min_hole"]
    m[small[lab]] = 1
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0) > 0.5
    rgba = np.zeros((600, 900, 4), np.uint8); rgba[m] = (*p["ink"], 255)
    Image.fromarray(rgba).save(f"{out_dir}/stencil_{name}.png")
    rec[name] = {k: v for k, v in p.items()} | {"coverage": round(float(m.mean()), 3), "file": f"stencil_{name}.png",
                 "ink_hex": "#%02x%02x%02x" % p["ink"]}
json.dump({"source": src, "method": __doc__, "plates": rec}, open(f"{out_dir}/stencils.json", "w"), indent=1)
print({k: v["coverage"] for k, v in rec.items()})
