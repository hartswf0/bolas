"""Side-by-side review sheets: rendered mp4 stills (band) vs styreneA.webp and kf-2.png, with band stats."""
import json, subprocess, colorsys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SW = ROOT / "films/swarm/le-chant-du-styrene"
MP4 = ROOT / "assets/films/le-chant-du-styrene.mp4"
REF = Image.open(ROOT / "assets/references/styreneA.webp").convert("RGB")
KF2 = Image.open(SW / "proposals/kf-2.png").convert("RGB")
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)

def still(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(MP4), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (960, 540), raw[:960 * 540 * 3])

def stats(im):
    a = np.asarray(im, np.float32) / 255
    lum = a @ [0.299, 0.587, 0.114]
    mx, mn = a.max(-1), a.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lit = lum > 25 / 255
    r, g, b = a[..., 0][lit], a[..., 1][lit], a[..., 2][lit]
    blue = (b > r) & (b > g)
    return dict(lum_lt20=round(float((lum < 20 / 255).mean()), 2), p99=int(np.percentile(lum, 99) * 255),
                lit_sat_med=round(float(np.median(sat[lit])) if lit.any() else 0, 2),
                warm=round(float((~blue).mean()) if lit.any() else 0, 2), blue=round(float(blue.mean()) if lit.any() else 0, 2))

def fit(im, w=640):
    return im.resize((w, int(im.height * w / im.width)))

def band_ref():
    w, h = REF.size; return REF  # whole reference (it is the 2.35 image with its own black)

out = {}
rows = []
for t in (5.0, 16.5, 24.0, 26.5, 32.0):
    s = still(t); b = s.crop((0, 66, 960, 474))
    st = stats(b); out[f"{t:.1f}"] = st
    panels = [(fit(b), f"film {t:.1f}s  " + " ".join(f"{k}={v}" for k, v in st.items())),
              (fit(REF), "styreneA.webp  " + " ".join(f"{k}={v}" for k, v in stats(REF).items())),
              (fit(KF2), "kf-2.png  " + " ".join(f"{k}={v}" for k, v in stats(KF2).items()))]
    H = max(p.height for p, _ in panels) + 26
    row = Image.new("RGB", (640 * 3 + 16, H), (20, 20, 22)); d = ImageDraw.Draw(row)
    for i, (p, lab) in enumerate(panels):
        row.paste(p, (i * 648, 24)); d.text((i * 648 + 4, 4), lab[:88], fill=(232, 226, 210), font=F)
    row.save(SW / f"assembly-compare-{t:04.1f}s.jpg", quality=88); rows.append(row)
sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height
sheet.save(SW / "assembly-compare-sheet.jpg", quality=85)
out["styreneA"] = stats(REF); out["kf-2"] = stats(KF2)
(SW / "assembly_band_stats.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
