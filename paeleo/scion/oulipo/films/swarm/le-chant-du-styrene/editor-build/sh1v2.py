"""Editor repair of Sh1 (0-8.60 s): the four kept rings are no longer a near-still.

Critic round 1: 8.6 s of near-hold (mean frame diff 0.047). Same cutout pieces, gel, camera and practicals as
U2's render.py (imported, not edited); added, frame by frame:
  - staggered set-downs: ring1 at 0.60 s (U2's, unchanged), ring3 at 1.25 s, ring2 at 1.85 s, each lowered
    from above (scale 1.22 -> 1.0, 9 px drop, fade-in 0.22 s) with U2's spring-damper settle on landing; ring0 already lies;
  - one ring (ring0) slowly turned in the hand's plane: rot = 16 deg * sin(pi (t - 2.9)/5.5) for 2.9-8.4 s,
    back to 0 before the cut so Sh2a's rest pose is continuous;
  - a light pass: a warm key (handmade) glides left to right across the rings from 3.0 to 8.0 s, raising
    their transmitted light (gain 0.78 -> 1.30 under the beam), so the gel's thickness ramp reads.
python3 sh1v2.py   -> sources/.../editor-repair/sh1/f%04d.png (frames 0-206)
"""
import sys, math
from pathlib import Path
import numpy as np, cv2
CB = Path(__file__).resolve().parent.parent / "cutout-build"
sys.path.insert(0, str(CB))
import os
os.chdir(CB)
import render as R
from layout import RINGS
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/editor-repair/sh1")
DOWN = {"ring3": 1.25, "ring2": 1.85}
yy, xx = np.mgrid[0:R.BH, 0:R.BW].astype(np.float32)


def pose(r, t):
    ctr, rot, sc = R.ring_pose(r, t)
    if r["piece"] in DOWN:
        t0 = DOWN[r["piece"]]
        a = R.smoother(min(max((t - (t0 - 0.55)) / 0.55, 0), 1))
        ctr = ctr + np.array([0, -9.0]) * (1 - a); sc = sc * (1 + 0.22 * (1 - a))
        rot = rot + R.settle(t - t0, 2.4 if r["piece"] == "ring3" else -2.0)
        vis = min(1.0, max(0.0, (t - (t0 - 0.55)) / 0.22))
    else:
        vis = 1.0
    if r["piece"] == "ring0" and 2.9 < t < 8.4:
        rot = rot + 16.0 * math.sin(math.pi * (t - 2.9) / 5.5)
    return ctr, rot, sc, vis


def frame(f):
    t = f / R.FPS
    cam = R.camera(t)
    img = R.practicals(cam).astype(np.float32)
    rings = np.zeros_like(img); A = np.zeros(img.shape[:2], np.float32)
    for r in sorted(RINGS, key=lambda r: -r["flight"]):
        e = r["ellipse_src"]; bb = R.BBOX[r["piece"]]
        pv = (e["cx"] - bb[0], e["cy"] - bb[1])
        ctr, rot, sc, vis = pose(r, t)
        if vis <= 0:
            continue
        g = R.piece(r["piece"]) * vis
        la = R.place(rings, g, ctr - np.array(pv), cam, rot, sc, pivot_local=pv)
        A = 1 - (1 - A) * (1 - la)
    # the light pass: one warm key gliding left -> right
    x0 = -200 + (1300) * R.smoother((t - 3.0) / 5.0)
    beam = np.exp(-((xx - x0 - 0.35 * (yy - 204)) / 170.0) ** 2)
    gain = 0.78 + 0.52 * beam * R.smoother((t - 2.6) / 0.8) * (1 - R.smoother((t - 7.6) / 0.8))
    rings = rings * gain[..., None]
    img = img * (1 - A[..., None]) + rings
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    hot = img * np.clip((lum - 0.45) / 0.3, 0, 1)[..., None]
    img = img + 0.22 * cv2.GaussianBlur(hot, (0, 0), 5) + 0.10 * cv2.GaussianBlur(hot, (0, 0), 16)
    return R.rolloff(img)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fr = [int(x) for x in sys.argv[1:]] or range(0, 207)
    for f in fr:
        im = (frame(f) * 255 + 0.5).astype(np.uint8)
        cv2.imwrite(str(OUT / f"f{f:04d}.png"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
