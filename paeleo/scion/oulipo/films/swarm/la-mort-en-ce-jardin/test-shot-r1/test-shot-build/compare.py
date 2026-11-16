# compare.py: reference beside 3 frames of test-shot.mp4 (labelled) + picture-area measurements.
#   python3 -I compare.py
import subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-mort-en-ce-jardin"
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/bunuel.webp"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f"{SW}/test-shot.mp4", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (960, 540), raw)


def stats(im):
    a = np.asarray(im.convert("RGB"), np.float32)
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    gy, gx = np.gradient(L)
    return dict(p=[int(np.percentile(L, q)) for q in (1, 5, 25, 50, 75, 95, 99)],
                below60=round(float((L < 60).mean()) * 100, 1), above200=round(float((L > 200).mean()) * 100, 1),
                grad=round(float(np.hypot(gx, gy).mean()), 2), rb=round(float(np.abs(a[..., 0] - a[..., 2]).mean()), 2))


ref = Image.open(REF).convert("RGB")
shots = [(1.6, "test shot 1.6 s (film 21.6): grasp, hand over satin"), (2.9, "2.9 s (film 22.9): shoe at her chest, bag with C"),
         (4.9, "4.9 s (film 24.9): ledger struck and rewritten")]
cells = [(ref.resize((800, 541)), "REFERENCE bunuel.webp (MoMA/Photofest), measured only", stats(ref))]
for t, lab in shots:
    fr = grab(t); pic = fr.crop((80, 0, 880, 540)); cells.append((pic, lab, stats(pic)))
cross = grab(7.6).crop((80, 0, 880, 540))
W, H = 800, 541
S = Image.new("RGB", (W * 2 + 30, (H + 70) * 2 + 20), (20, 20, 20)); d = ImageDraw.Draw(S)
for i, (im, lab, st) in enumerate(cells):
    x, y = 10 + (i % 2) * (W + 10), 10 + (i // 2) * (H + 70)
    S.paste(im.resize((W, H)), (x, y))
    d.text((x, y + H + 6), lab, font=F, fill=(230, 230, 230))
    d.text((x, y + H + 28), f"L p1..p99 {st['p']}  <60 {st['below60']}%  >200 {st['above200']}%  grad {st['grad']}  |R-B| {st['rb']}",
           font=F, fill=(180, 180, 180))
S.save(f"{SW}/test-shot-compare.jpg", quality=88)
json.dump(dict(cells=[(lab, st) for _, lab, st in cells], cross_7_6=stats(cross)), open(f"{SW}/test-shot-build/compare-stats.json", "w"), indent=1)
for _, lab, st in cells: print(lab, st)
print("cross 7.6", stats(cross))
