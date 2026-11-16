"""Editor repair-2 render of Sh3a/Sh3b with melt3f. python3 -I render_melt2.py worker nworkers"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import melt3f as m
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/editor-repair2")
wk, nw = int(sys.argv[1]), int(sys.argv[2])
for f in range(415 + wk, 663, nw):
    d = OUT / ("sh3a_dissolve_target" if f <= 422 else "sh3a" if f <= 499 else "sh3b")
    d.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(d / f"f{f:04d}.png"), cv2.cvtColor(m.band(f / 24.0, f), cv2.COLOR_RGB2BGR))
print("done", wk)
