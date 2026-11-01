#!/usr/bin/env python3
"""Print motion energy peaks in a stretch of a clip, to find where a hand lands. A helper for the eye, it decides nothing. usage: beats.py <film> <n> <in> <out>"""
import json, os, subprocess, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); film, n, i, o = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
db = json.load(open(os.path.join(ROOT, "films", film, "forage.json"))); c = [x for x in db["clips"].values() if str(x["n"]) == n][0]
r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(i), "-t", str(o - i), "-i", os.path.join(ROOT, "clips", c["id"] + ".mp4"), "-vf", "scale=80:60,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
F = np.frombuffer(r, dtype=np.uint8).reshape(-1, 60, 80).astype(float); e = np.abs(np.diff(F, axis=0)).mean((1, 2)); fps = len(F) / (o - i)
# a strike is where motion collapses: a local minimum after a peak
pk = [k for k in range(2, len(e) - 2) if e[k] > e[k - 1] and e[k] >= e[k + 1] and e[k] > e.mean()]
print(f"#{n} {fps:.1f}fps mean {e.mean():.2f} peaks:", " ".join(f"{i + k / fps:.2f}" for k in pk))
