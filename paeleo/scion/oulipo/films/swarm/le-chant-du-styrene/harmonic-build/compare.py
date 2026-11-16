import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats import band_stats
ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SW = ROOT / "films/swarm/le-chant-du-styrene"
OUT = ROOT / "films/sources/le-chant-du-styrene/harmonic"
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
ref = Image.open(ROOT / "assets/references/styreneA.webp").convert("RGB")
refb = ref.crop((0, 144, 650, 376))
kf = Image.open(SW / "proposals/kf-3.png").convert("RGB")
kfb = kf.crop((0, 88, 1280, 633))
ours = {t: Image.open(OUT / f"sh4/f{int(round(t*24)):04d}.png").convert("RGB") for t in (32.0, 33.583, 34.25)}
rows = [("reference styreneA.webp (band rows 144-375; NOT copied, comparison only)", refb),
        ("baseline proposals/kf-3.png (round-2 keyframe, picture band)", kfb),
        ("U4 Sh4 build, t = 32.00 s (frame 768): beading, before the cut", ours[32.0])]
stats = {}
tiles = []
for lab, im in rows:
    st = band_stats(np.asarray(im)); stats[lab] = st
    w = 960; h = int(im.height * w / im.width)
    imr = im.resize((w, h), Image.LANCZOS)
    pad = Image.new("RGB", (w + 470, max(h, 220)), (14, 14, 16)); pad.paste(imr, (0, 0))
    d = ImageDraw.Draw(pad)
    d.text((970, 8), lab, fill=(232, 226, 210), font=f) if len(lab) < 60 else None
    y = 8
    for line in [lab[i:i+55] for i in range(0, len(lab), 55)] + [
        f"lum<20: {st['frac_lum_lt_20']:.2f}   median {st['lum_median']}",
        f"p95 {st['lum_p95']}   p99 {st['lum_p99']}   max {st['lum_max']}",
        f"lit (lum>25) {st['lit_frac']:.2f}   median sat {st['lit_median_sat']}",
        "hue clusters of lit px:",
        "  red {red:.2f}  orange {orange:.2f}  amber {amber:.2f}  blue {blue:.2f}".format(**st['hue_clusters_of_lit']),
        f"warm share {st['warm_share_of_lit']:.2f}"]:
        d.text((972, y), line, fill=(200, 196, 185), font=f); y += 19
    tiles.append(pad)
H = sum(t.height for t in tiles) + 8 * len(tiles)
sheet = Image.new("RGB", (tiles[0].width, H), (40, 40, 40)); y = 0
for t in tiles: sheet.paste(t, (0, y)); y += t.height + 8
sheet.save(SW / "harmonic-compare-32.0s.jpg", quality=92)
# extra stats for other times
for t, im in ours.items(): stats[f"U4 Sh4 t={t}"] = band_stats(np.asarray(im))
(SW / "harmonic-build/compare_stats.json").write_text(json.dumps(stats, indent=1))
print(json.dumps(stats, indent=1))
