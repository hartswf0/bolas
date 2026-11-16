"""Plate prep for the test shot: crop the two LoC photochroms, defocus, unifying grade.
Usage: python3 -I plates.py <r2_dir> <out_dir>
Writes P1_sharp/P2_sharp (graded, unblurred, 2x picture + 8% overscan) and stats."""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
SRC, OUT = sys.argv[1:3]
PW, PH = 1440, 1080           # 2x of the 720x540 picture
OV = 1.08                     # overscan for drift / rack
CROPS = {  # (file, box in 1024px source)  -- chosen by eye
    "P1": ("loc_05184.jpg", (318, 330, 650, 579)),   # Madeleine colonnade fills the frame
    "P2": ("loc_09974.jpg", (6, 330, 458, 669)),     # Clichy: monument pedestal behind head, tram at right
}
def grade(a, ds):
    a = a.astype(np.float32) / 255
    a = a ** 1.45                                   # lower gamma
    g = (a * [0.3, 0.59, 0.11]).sum(2, keepdims=True)
    a = g + (a - g) * ds                          # ~32 % desaturation
    a = a * np.array([0.97, 0.975, 0.93]) + np.array([0, 0.004, 0.012])  # toward grey-olive, blue up a hair vs sepia
    return a
stats = {}
DS = {"P1": 0.52, "P2": 0.70}
TGT = {"P1": 94, "P2": 92}
for k, (fn, box) in CROPS.items():
    im = Image.open(f"{SRC}/{fn}").convert("RGB").crop(box)
    im = im.resize((int(PW * OV), int(PH * OV)), Image.LANCZOS)
    a = grade(np.asarray(im), DS[k])
    # normalise plate median luma to ~92
    l = a.mean(2) * 255
    s = TGT[k] / np.percentile(l, 50)
    a = np.clip(a * s, 0, 188 / 255)
    out = Image.fromarray((a * 255).astype(np.uint8))
    out.save(f"{OUT}/{k}_sharp.png")
    b = np.asarray(out.filter(ImageFilter.GaussianBlur(24))).astype(np.float32)
    L = b.mean(2); hsv = np.asarray(out.filter(ImageFilter.GaussianBlur(24)).convert("HSV"))
    stats[k] = dict(file=fn, box=box, gain=round(float(s), 3), p5=float(np.percentile(L, 5)), p50=float(np.percentile(L, 50)),
                    p95=float(np.percentile(L, 95)), sat=float(hsv[..., 1].mean()))
json.dump(stats, open(f"{OUT}/plate_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
