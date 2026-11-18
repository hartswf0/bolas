"""Editor repair render of Sh3a/Sh3b with melt3e (steel exposure, single-recess hollows). python3 -I render_melt.py f0 f1 [step]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import melt3e as m
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/editor-repair")
f0, f1 = int(sys.argv[1]), int(sys.argv[2]); step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
for f in range(f0, f1 + 1, step):
    d = OUT / ("sh3a_dissolve_target" if f <= 422 else "sh3a" if f <= 499 else "sh3b")
    d.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(d / f"f{f:04d}.png"), cv2.cvtColor(m.band(f / 24.0, f), cv2.COLOR_RGB2BGR))
print("done", f0, f1)
