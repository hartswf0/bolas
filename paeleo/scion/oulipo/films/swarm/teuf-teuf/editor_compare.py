"""Montage editor: side-by-side acceptance frames (6-7) and measured tone, from the FINAL mp4.

python3 films/swarm/teuf-teuf/editor_compare.py
writes films/swarm/teuf-teuf/compare-final.jpg, compare-pusher-bull.jpg, tone-final.json
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from layout_wall import measure  # noqa: E402  (same function the layout unit used on the reference)

PROJ = HERE.parents[2]
MP4 = PROJ / "assets" / "films" / "teuf-teuf.mp4"
REF = PROJ / "assets" / "references" / "teuf.webp"
TIMES = [7.0, 17.5, 30.0]


def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(MP4), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3)


ref = np.asarray(Image.open(REF).convert("RGB"))
out = {"method": "layout_wall.measure: lum = .299R+.587G+.114B; pale = Gaussian(4)-blurred lum > 150",
       "source": str(MP4.relative_to(PROJ)), "reference": measure(ref), "frames": {}}
rows = []
for t in TIMES:
    a = grab(t)
    m = measure(a)
    pr = m["pale_median_rgb"]
    m["checks"] = dict(
        pale_lum_195_220=195 <= m["pale_median_lum"] <= 220,
        rgb_within_12=all(abs(p - q) <= 12 for p, q in zip(pr, (223, 217, 188))),
        R_ge_G_gt_B=pr[0] >= pr[1] > pr[2],
        below60_ge_12pct=m["frac_below_60"] >= 0.12)
    out["frames"][str(t)] = m
    im = Image.fromarray(a).resize((1000, 562))
    r = Image.fromarray(ref).resize((1000, 617))
    row = Image.new("RGB", (2010, 640), (20, 20, 16))
    row.paste(im, (0, 39))
    row.paste(r, (1010, 11))
    d = ImageDraw.Draw(row)
    d.text((8, 4), f"film {t:.1f} s  pale lum {m['pale_median_lum']} rgb {tuple(pr)}  <60: {m['frac_below_60']:.1%}",
           fill=(240, 235, 210))
    d.text((1018, 0), "reference teuf.webp (Cite Films still)", fill=(240, 235, 210))
    rows.append(row)
sheet = Image.new("RGB", (2010, 640 * len(rows)))
for i, r in enumerate(rows):
    sheet.paste(r, (0, 640 * i))
sheet.save(HERE / "compare-final.jpg", quality=88)

# acceptance 7: pusher crop at 7.0 s beside the reference's black bull, same height
a = Image.fromarray(grab(7.0)).crop((0, 300, 320, 590))
b = Image.fromarray(ref).crop((560, 370, 870, 525))
h = 400
a = a.resize((int(a.width * h / a.height), h))
b = b.resize((int(b.width * h / b.height), h))
pb = Image.new("RGB", (a.width + b.width + 10, h), (20, 20, 16))
pb.paste(a, (0, 0))
pb.paste(b, (a.width + 10, 0))
pb.save(HERE / "compare-pusher-bull.jpg", quality=90)
json.dump(out, open(HERE / "tone-final.json", "w"), indent=1)
print(json.dumps({k: (v["pale_median_lum"], v["pale_median_rgb"], v["frac_below_60"], v["checks"]) for k, v in out["frames"].items()}, indent=1))
