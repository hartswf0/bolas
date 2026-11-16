"""Compare sheet + measurements for the test shot (frames decoded from the mp4 with ffmpeg)."""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import melt
SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
REF = Path("/home/user/bolas/paeleo/scion/oulipo/assets/references/styreneA.webp")
FONT = ImageFont.truetype("/home/user/bolas/paeleo/scion/oulipo/assets/fonts/instrument-sans.woff2", 20)
TMP = Path(sys.argv[1])
times = [(0.60, "21.40 s  full melt, steel refracted"), (2.00, "22.80 s  far cavities emptied first"), (6.20, "27.00 s  four hollows; sprue drained (26.2)")]
frames = []
for t, lab in times:
    p = TMP / f"f{t:.2f}.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SW / "test-shot.mp4"), "-frames:v", "1", str(p)], check=True)
    frames.append((Image.open(p).convert("RGB"), lab))
stats = {}
def measure(a, name):
    a = np.asarray(a, np.float32)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    hsv = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2HSV)
    lit = L > 25
    hue = hsv[..., 0][lit].astype(int) * 2
    warm = ((hue < 50) | (hue > 340)).mean() if lit.any() else 0
    blue = ((hue > 200) & (hue < 250)).mean() if lit.any() else 0
    stats[name] = dict(frac_lum_lt20=round(float((L < 20).mean()), 3), p50=round(float(np.percentile(L, 50)), 1),
                       p95=round(float(np.percentile(L, 95)), 1), p99=round(float(np.percentile(L, 99)), 1),
                       lit_median_sat=round(float(np.median(hsv[..., 1][lit]) / 255), 2) if lit.any() else None,
                       lit_warm_frac=round(float(warm), 2), lit_blue_frac=round(float(blue), 2))
ref = Image.open(REF).convert("RGB")
measure(np.asarray(ref)[144:376], "reference band")
for (im, lab), (t, _) in zip(frames, times):
    measure(np.asarray(im)[66:474], f"t={t + 20.8:.2f}")
# sheet: 2x2 at 640 px wide
cw = 640
def fit(im):
    return im.resize((cw, int(im.height * cw / im.width)))
tiles = [(fit(ref), "REFERENCE  styreneA.webp (1958 still)")] + [(fit(im), "TEST SHOT  " + lab) for im, lab in frames]
th = max(t.height for t, _ in tiles)
sheet = Image.new("RGB", (cw * 2 + 30, (th + 40) * 2 + 20), (16, 16, 16))
d = ImageDraw.Draw(sheet)
for i, (t, lab) in enumerate(tiles):
    x = 10 + (i % 2) * (cw + 10); y = 10 + (i // 2) * (th + 40)
    sheet.paste(t, (x, y + (th - t.height) // 2))
    d.text((x, y + th + 8), lab, font=FONT, fill=(232, 226, 210))
sheet.save(SW / "test-shot-compare.jpg", quality=90)
# runner symmetry about the sprue (plane space): left/right flip about the hub column, and up/down
m = melt.mask; hx, hy = int(melt.hub[0]), int(melt.hub[1])
def flip_iou(m, axis):
    if axis == 1:
        w = min(hx, m.shape[1] - hx); a = m[:, hx - w:hx + w]; b = a[:, ::-1]
    else:
        h = min(hy, m.shape[0] - hy); a = m[hy - h:hy + h]; b = a[::-1]
    return round(float((a & b).sum() / (a | b).sum()), 3)
cav_empty = {int(ci["id"]): round(float(np.interp(melt.cav_Tmax[ci["id"]] * 0 + melt.gate_T[ci["id"]], np.sort(melt.tau_tab), melt.tt_[np.argsort(melt.tau_tab)])) + 20.8, 2) for ci in melt.cav_info}
out = dict(iou=melt.iou_report(), flip_iou_lr=flip_iou(m, 1), flip_iou_ud=flip_iou(m, 0), stats=stats,
           cavity_empty_film_time=cav_empty, empty_order=[int(i) for i in melt.order_empty],
           sprue_empty_film_time=26.20)
json.dump(out, open(TMP / "metrics.json", "w"), indent=1)
print(json.dumps(out, indent=1))
