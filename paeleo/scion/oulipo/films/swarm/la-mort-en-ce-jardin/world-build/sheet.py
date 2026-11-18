# sheet.py -- world-sheet.jpg: reference | wide test | close test, measured; then the cut pieces and their failure masks.
import sys, json, glob, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
WM, SW = sys.argv[1:3]
st = json.load(open(f"{WM}/test/stats.json"))
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
try: fnt = ImageFont.truetype(F, 15); fs = ImageFont.truetype(F, 12)
except Exception: fnt = fs = ImageFont.load_default()
ref = Image.open(f"{SW}/../../../assets/references/bunuel.webp").convert("RGB").resize((800, 541), Image.LANCZOS).crop((0, 0, 800, 540))
cells = [("REFERENCE bunuel.webp (MoMA/Photofest) - measured only, never copied", ref, st["reference_bunuel_native_1000x677"]["stats"]),
         ("WIDE L-S1 t=1.5 (glide X=0): P0-P4 + flood water + banks + plank + liana; no puppets", Image.open(f"{WM}/test/wide_L-S1_t1.5.png"), st["wide_L-S1_t1.5"]["stats"]),
         ("CLOSE L-S5 t=19.0 (dolly M=3.0 at the plank foot): near dressing; no puppets", Image.open(f"{WM}/test/close_L-S5_t19.0.png"), st["close_L-S5_t19.0"]["stats"])]
cuts = [f for f in sorted(glob.glob(f"{WM}/cut/*.png")) if not f.endswith("_fail.png")]
TW, TH = 400, 230
rows = (len(cuts) + 5) // 6
S = Image.new("RGB", (2400, 540 + 110 + rows * (TH * 2 + 40) + 20), (20, 20, 20)); d = ImageDraw.Draw(S)
for i, (lab, im, s) in enumerate(cells):
    S.paste(im, (i * 800, 0))
    d.text((i * 800 + 6, 546), lab, font=fnt, fill=(230, 230, 230))
    d.text((i * 800 + 6, 568), f"L p1/5/25/50/75/95/99 {s['p1_5_25_50_75_95_99']}", font=fnt, fill=(200, 200, 200))
    d.text((i * 800 + 6, 590), f"<L60 {s['below60_pct']}%  >L200 {s['above200_pct']}%  |R-B| {s['mean_abs_R_minus_B']}  grad(|dx|+|dy|) {s['mean_gradient']}", font=fnt, fill=(200, 200, 200))
    d.text((i * 800 + 6, 612), f"row means {s['row_means_top_to_bottom']}", font=fnt, fill=(170, 170, 170))
y0 = 650
for k, f in enumerate(cuts):
    x = (k % 6) * TW; y = y0 + (k // 6) * (TH * 2 + 40)
    im = Image.open(f).convert("RGBA"); im.thumbnail((TW - 8, TH - 8))
    bg = Image.new("RGB", im.size, (150, 40, 40)); bg.paste(im, (0, 0), im); S.paste(bg, (x + 4, y + 4))
    fp = f[:-4] + "_fail.png"
    if os.path.exists(fp):
        fm = Image.open(fp).convert("L"); fm.thumbnail((TW - 8, TH - 8)); S.paste(fm.convert("RGB"), (x + 4, y + TH + 4))
    d.text((x + 4, y + TH * 2 + 6), os.path.basename(f)[:-4] + "  (piece on red / GrabCut doubt mask)", font=fs, fill=(220, 220, 220))
S.save(f"{SW}/world-sheet.jpg", quality=86)
print(S.size)
