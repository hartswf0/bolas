"""Plate prep for the test shot (r2): crop the two LoC photochroms, unifying grade, V (tram) cutout mask.
Usage: python3 -I plates.py <r2_dir> <hires_dir> <out_dir>
P1 from the 1024 px service JPEG (it is defocused hard); P2 from the LoC master TIFF (3650 px) so the
tram plane can be held at a lighter defocus. Writes P1_sharp/P2_sharp (graded, 2x picture + 8 % overscan),
P2_Vmask.png (feathered GrabCut mask of the native tram, same plate coords) and stats."""
import sys, json
import numpy as np
import cv2
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
SRC, HI, OUT = sys.argv[1:4]
PW, PH = 1440, 1080
OV = 1.08
K = 3650 / 1024
CROPS = {  # box in 1024-px coords, chosen by eye
    "P1": (f"{SRC}/loc_05184.jpg", (318, 330, 650, 579), 1.0),
    # Clichy r2: tighter, so the native horse tram sits mid-height at frame right, beside her ear (ahead of her)
    "P2": (f"{HI}/09974u_full.png", (122, 418, 482, 688), K),
}
TRAM_BOX = (318, 506, 492, 598)          # 1024-px coords: tram body, impériale rail, lamp posts in front


def grade(a, ds, tint):
    a = a.astype(np.float32) / 255
    a = a ** 1.40                                   # lower gamma
    g = (a * [0.3, 0.59, 0.11]).sum(2, keepdims=True)
    a = g + (a - g) * ds                            # desaturate toward grey
    return a * np.array(tint)                       # and toward grey-olive


DS = {"P1": 0.52, "P2": 0.42}
TINT = {"P1": [0.97, 0.975, 0.93], "P2": [0.985, 0.975, 0.86]}
TGT = {"P1": 101, "P2": 92}
stats = {}
for k, (fn, box, s) in CROPS.items():
    full = Image.open(fn).convert("RGB")
    b = tuple(int(round(v * s)) for v in box)
    im = full.crop(b).resize((int(PW * OV), int(PH * OV)), Image.LANCZOS)
    a = grade(np.asarray(im), DS[k], TINT[k])
    l = a.mean(2) * 255
    gain = TGT[k] / np.percentile(l, 50)
    a = np.clip(a * gain, 0, 186 / 255)
    out = Image.fromarray((a * 255).astype(np.uint8))
    out.save(f"{OUT}/{k}_sharp.png")
    if k == "P2":   # GrabCut the native tram (rect-seeded), feather, store as a plate-coords mask
        sx = out.width / (box[2] - box[0]); sy = out.height / (box[3] - box[1])
        r = (int((TRAM_BOX[0] - box[0]) * sx), int((TRAM_BOX[1] - box[1]) * sy),
             int((TRAM_BOX[2] - TRAM_BOX[0]) * sx), int((TRAM_BOX[3] - TRAM_BOX[1]) * sy))
        img = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
        m = np.zeros(img.shape[:2], np.uint8)
        bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(img, m, r, bg, fg, 5, cv2.GC_INIT_WITH_RECT)
        mm = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
        # keep the largest blob, close holes (windows), feather
        n, lab, st, _ = cv2.connectedComponentsWithStats(mm)
        if n > 1:
            big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); mm = np.where(lab == big, 255, 0).astype(np.uint8)
        mm = cv2.morphologyEx(mm, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
        mm = cv2.GaussianBlur(cv2.erode(mm, np.ones((5, 5), np.uint8)), (0, 0), 5)
        Image.fromarray(mm).save(f"{OUT}/P2_Vmask.png")
        stats["V"] = dict(rect=r, area_frac=float((mm > 128).mean()))
    bl = out.filter(ImageFilter.GaussianBlur(24))
    L = np.asarray(bl).astype(np.float32).mean(2); hsv = np.asarray(bl.convert("HSV"))
    stats[k] = dict(file=fn.split("/")[-1], box=box, gain=round(float(gain), 3), p5=float(np.percentile(L, 5)),
                    p50=float(np.percentile(L, 50)), p95=float(np.percentile(L, 95)), sat=float(hsv[..., 1].mean()))
json.dump(stats, open(f"{OUT}/plate_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
