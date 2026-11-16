"""Comparison sheet + measurements for the test shot. Reads frames decoded from test-shot.mp4.
Run: python3 -I compare.py"""
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
WS = ROOT + "/films/swarm/anemic-cinema"
MED = ROOT + "/films/sources/anemic-cinema/test-shot"
REF = ROOT + "/assets/references"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FPS = 24
K0 = 96


def grab(n):
    p = MED + f"/mp4_{n:03d}.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", WS + "/test-shot.mp4", "-vf",
                    f"select=eq(n\\,{n})", "-vframes", "1", p], check=True)
    return Image.open(p).convert("RGB")


def measure_text(a):
    L = a.mean(2)
    m = {}
    m["field_corner_L"] = float(L[:40, :40].mean())
    m["field_noise_sigma"] = float(L[:40, :40].std())
    ys, xs = np.nonzero(L > 12)
    m["disc_height_frac"] = float((ys.max() - ys.min() + 1) / a.shape[0])
    cx, cy = 480, 270
    plate = {}
    for nm, (dx, dy) in dict(top=(0, -200), upper_left=(-140, -140), centre=(0, 0),
                             lower_right=(140, 140), bottom=(0, 200)).items():
        patch = L[cy + dy - 6:cy + dy + 7, cx + dx - 6:cx + dx + 7]
        plate[nm] = float(np.median(patch))
    m["plate_samples_L"] = plate
    disc = np.hypot(*np.mgrid[0:540, 0:960][::-1].astype(float) - np.array([[[cx]], [[cy]]])) < 225
    rb = a[..., 0].astype(float) - a[..., 2].astype(float)
    m["plate_mean_R_minus_B"] = float(rb[disc].mean())
    let = L[disc] > 215
    m["letter_pixels_L_p50_p90"] = [float(np.percentile(L[disc][let], 50)), float(np.percentile(L[disc][let], 90))]
    return m


def measure_rings(a):
    L = a.mean(2)
    rb = a[..., 0].astype(float) - a[..., 2].astype(float)
    m = {"field_corner_L": float(L[:40, :40].mean())}
    ys, xs = np.nonzero(L > 12)
    m["disc_height_frac"] = float((ys.max() - ys.min() + 1) / a.shape[0])
    ring = (L > 90) & (L < 175)
    m["ring_pixels_L_p10_p50_p90"] = [float(np.percentile(L[ring], q)) for q in (10, 50, 90)]
    m["ring_R_minus_B_mean"] = float(rb[ring].mean())
    gap = (L > 8) & (L < 60)
    m["gap_rgb_mean"] = [float(a[..., c][gap].mean()) for c in range(3)]
    row = L[270, 480:712] > 80
    runs, cur, val = [], 0, row[0]
    for v in row:
        if v == val:
            cur += 1
        else:
            runs.append((bool(val), cur)); cur, val = 1, v
    runs.append((bool(val), cur))
    on = [r for v, r in runs if v]
    off = [r for v, r in runs[1:-1] if not v]
    m["radial_scan_ring_runs_px"] = on
    m["radial_scan_gap_runs_px"] = off
    m["ring_over_gap"] = float(np.mean(on) / max(np.mean(off), 1)) if off else None
    return m


frames = {"T1 body": 20, "W1 held, F134": 38, "O_A body": 100, "O_B body (keys)": 200}
imgs = {k: grab(n) for k, n in frames.items()}
meas = {
    "T1_frame_n20": measure_text(np.asarray(imgs["T1 body"]).astype(float)),
    "T2_frame_n140": measure_text(np.asarray(grab(140)).astype(float)),
    "OA_frame_n100": measure_rings(np.asarray(imgs["O_A body"]).astype(float)),
    "OB_frame_n200": measure_rings(np.asarray(imgs["O_B body (keys)"]).astype(float)),
}
ra = Image.open(REF + "/spiralTextPom.webp").convert("RGB")
rbm = Image.open(REF + "/duchamp2.webp").convert("RGB")
ra = ra.resize((int(ra.width * 540 / ra.height), 540), Image.LANCZOS)
rbm = rbm.resize((int(rbm.width * 540 / rbm.height), 540), Image.LANCZOS)
lab = 34
gap = 12
cw = max(ra.width, rbm.width)
Wt = cw + 2 * 960 + 4 * gap
Ht = 2 * (540 + lab) + 3 * gap
sheet = Image.new("RGB", (Wt, Ht), (28, 28, 28))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype(FONT, 20)
cells = [
    [("REFERENCE spiralTextPom.webp (Centre Pompidou)", ra), ("SHOT n20 / F116: T1 pun disc, 0.30 rev/s", imgs["T1 body"]),
     ("SHOT n38 / F134: W1 held - outer rings, dashes, inner letters", imgs["W1 held, F134"])],
    [("REFERENCE duchamp2.webp (MoMA)", rbm), ("SHOT n100 / F196: O_A engraved rings", imgs["O_A body"]),
     ("SHOT n200 / F296: O_B rings of GrabCut keys", imgs["O_B body (keys)"])],
]
for r, row in enumerate(cells):
    y = gap + r * (540 + lab + gap)
    x = gap
    for i, (t, im) in enumerate(row):
        wcell = cw if i == 0 else 960
        sheet.paste(im, (x + (wcell - im.width) // 2, y + lab))
        d.text((x + 4, y + 6), t, font=f, fill=(235, 230, 220))
        x += wcell + gap
sheet.save(WS + "/test-shot-compare.jpg", quality=90)
json.dump(meas, open(WS + "/test-shot-build/measurements.json", "w"), indent=1)
print(json.dumps(meas, indent=1))
