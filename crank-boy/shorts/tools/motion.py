#!/usr/bin/env python3
"""Measure how much a plate moves, frame by frame, so a short can drive action from it.
python3 shorts/tools/motion.py <plate name> ...   Writes assets/shorts/plates/<name>.motion.json: {"fps": 24, "energy": [0..1 per frame]}, the mean absolute
change between consecutive frames at 64x48, scaled so the busiest frame is 1. A short can drive action from it."""
import json, os, subprocess, sys
import numpy as np
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for name in sys.argv[1:]:
    src = os.path.join(root, 'assets/shorts/plates', name + '.mp4')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', 'scale=64:48,format=gray', '-f', 'rawvideo', '-'],
                         capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 48, 64).astype(np.float32)
    e = np.concatenate([[0], np.abs(np.diff(f, axis=0)).mean((1, 2))])
    e = np.convolve(e, np.ones(3) / 3, mode='same')
    e = e / (e.max() + 1e-9)
    json.dump({'fps': 24, 'energy': [round(float(x), 3) for x in e]}, open(src.replace('.mp4', '.motion.json'), 'w'))
    print(name, len(e), 'frames, mean', round(float(e.mean()), 3))
