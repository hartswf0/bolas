"""Render Sh3a (incl. the 8-frame dissolve-target pre-roll) and Sh3b as PNG sequences (960x408 band, no grain).
Global frame index f, film time t = f/24.  python3 -I render.py <f0> <f1> [step]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import melt3 as m
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/melt-simulation-camera-unit-b-test-shot-sh3a-sh3b-defining-beat-")
f0, f1 = int(sys.argv[1]), int(sys.argv[2]); step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
for f in range(f0, f1 + 1, step):
    d = OUT / ("sh3a_dissolve_target" if f <= 422 else "sh3a" if f <= 499 else "sh3b")
    d.mkdir(parents=True, exist_ok=True)
    a = m.band(f / 24.0, f)
    cv2.imwrite(str(d / f"f{f:04d}.png"), cv2.cvtColor(a, cv2.COLOR_RGB2BGR))
print("done", f0, f1)
