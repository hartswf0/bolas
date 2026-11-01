#!/usr/bin/env python3
"""Lay a finished cut out shot by shot (head / middle / tail of each, with film time) so the cuts themselves can be read. usage: reel.py <film> [suffix] [frames-per-shot]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); film = sys.argv[1]; suf = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else ""; nf = int(sys.argv[3]) if len(sys.argv) > 3 else 3
d = os.path.join(ROOT, "films", film); L = json.load(open(os.path.join(d, f"ledger{suf}.json")))["shots"]; v = os.path.join(d, f"{film}{suf}.mp4")
F = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 11); w, h = 200, 150; COL = 6; cells = []
for s in L:
    for k in range(nf):
        t = s["at"] + (0.04 + (s["dur"] - 0.2) * k / (nf - 1) if nf > 1 else s["dur"] / 2); cells.append((s, t, k))
rows = (len(cells) + COL - 1) // COL; sh = Image.new("RGB", (COL * w, rows * (h + 16)), "#111"); dr = ImageDraw.Draw(sh)
for i, (s, t, k) in enumerate(cells):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", v, "-frames:v", "1", "-vf", f"scale={w-2}:-1", "-q:v", "3", "/tmp/_r.jpg"])
    x, y = (i % COL) * w, (i // COL) * (h + 16); sh.paste(Image.open("/tmp/_r.jpg"), (x + 1, y + 16))
    dr.text((x + 2, y + 2), f"{s['position']}{chr(97+k)} {t:.1f}s {(s['source'] or '')[:16]}", fill="#fc6" if k == 0 else "#999", font=F)
o = os.path.join(d, f"reel{suf}.jpg"); sh.save(o, quality=82); print(o)
