import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2, melt3f as m
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/editor-repair2/sh3b")
wk, nw = int(sys.argv[1]), int(sys.argv[2])
for f in range(500 + wk, 663, nw):
    cv2.imwrite(str(OUT / f"f{f:04d}.png"), cv2.cvtColor(m.band(f / 24.0, f), cv2.COLOR_RGB2BGR))
