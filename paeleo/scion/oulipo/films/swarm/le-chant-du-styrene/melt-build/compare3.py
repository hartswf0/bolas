"""Measurements + comparison sheet for Sh3a/Sh3b (reads rendered PNGs; frames are decoded with PIL only)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import melt3 as m
SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
OUT = m.OUT if hasattr(m, "OUT") else None
MD = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/melt-simulation-camera-unit-b-test-shot-sh3a-sh3b-defining-beat-")
REF = Path("/home/user/bolas/paeleo/scion/oulipo/assets/references/styreneA.webp")
KF2 = SW / "proposals/kf-2.png"
FONT = ImageFont.truetype("/home/user/bolas/paeleo/scion/oulipo/assets/fonts/instrument-sans.woff2", 17)

def frame(f):
    d = "sh3a_dissolve_target" if f <= 422 else "sh3a" if f <= 499 else "sh3b"
    return np.asarray(Image.open(MD / d / f"f{f:04d}.png").convert("RGB"))

def stats(a):
    a = np.asarray(a, np.float32)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    hsv = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2HSV)
    lit = L > 25
    hue = hsv[..., 0][lit].astype(int) * 2
    return dict(frac_lum_lt20=round(float((L < 20).mean()), 3), p50=round(float(np.percentile(L, 50)), 1),
                p95=round(float(np.percentile(L, 95)), 1), p99=round(float(np.percentile(L, 99)), 1), max=round(float(L.max()), 1),
                lit_frac=round(float(lit.mean()), 3),
                lit_median_sat=round(float(np.median(hsv[..., 1][lit]) / 255), 2) if lit.any() else None,
                lit_warm_frac=round(float(((hue < 55) | (hue > 340)).mean()), 2) if lit.any() else None,
                lit_blue_frac=round(float(((hue > 200) & (hue < 250)).mean()), 2) if lit.any() else None)

res = {}
ref = np.asarray(Image.open(REF).convert("RGB"))
kf2 = np.asarray(Image.open(KF2).convert("RGB"))
res["reference_band_rows144_375"] = stats(ref[144:376])
# kf-2 is a full 960x540 letterboxed frame: measure its band rows 66-474 if that size
res["kf2_band"] = stats(kf2[66:474] if kf2.shape[0] == 540 else kf2)
for t in (17.625, 19.5, 21.0, 22.5, 24.0, 25.5, 26.5, 27.5):
    res[f"t={t:.3f}"] = stats(frame(int(round(t * 24))))
# drain timing measured from the simulation (film seconds): last melt leaves each cavity / the sprue
emp = {}
for ci in m.cav_info:
    mm = m.cav_masks[ci["id"]]
    emp[f"cavity{ci['id']}_ring{ci['ring']}"] = round(float(np.percentile(m.t_drain[mm], 99.5)) + m.T0_3B, 2)
emp["sprue"] = round(float(m.t_drain[m.part == 5].max()) + m.T0_3B, 2)
fill = {}
for t in np.arange(0.0, 6.81, 0.4):
    fill[f"{t + m.T0_3B:.1f}"] = [round(float((m.depth * mm * (m.t_drain > t)).sum() / (m.depth * mm).sum()), 2) for mm in m.cav_masks]
# shape match at the Sh2b->Sh3a dissolve: cavity silhouettes vs the U2 ring silhouettes, both in film coords (hold camera)
Hm, R, tv = m.camera(17.60)
ious_film = []
for ci in m.cav_info:
    a = cv2.warpPerspective(m.cav_masks[ci["id"]].astype(np.uint8), Hm, (960, 408), flags=cv2.INTER_NEAREST) > 0
    b = cv2.warpPerspective(m.ring_world_mask(ci).astype(np.uint8), Hm, (960, 408), flags=cv2.INTER_NEAREST) > 0
    ious_film.append(round(float((a & b).sum() / (a | b).sum()), 4))
# and against U2's actual rendered hold frame f0422 (lit-object mask)
u2 = np.asarray(Image.open(m.CUT / "sh2b/f0422.png").convert("RGB")).astype(np.float32)
u2L = u2 @ np.array([0.2126, 0.7152, 0.0722]); u2hsv = cv2.cvtColor(u2.astype(np.uint8), cv2.COLOR_RGB2HSV)
u2obj = (u2L > 18) & ((u2hsv[..., 0] < 30) | (u2hsv[..., 0] > 160)) & (u2hsv[..., 1] > 80)
mouldobj = cv2.warpPerspective(m.mask.astype(np.uint8), Hm, (960, 408), flags=cv2.INTER_NEAREST) > 0
u2_vs_mould = round(float((u2obj & mouldobj).sum() / (u2obj | mouldobj).sum()), 4)
f422 = frame(422).astype(np.float32)
ov = np.clip(0.5 * u2 + 0.5 * f422, 0, 255).astype(np.uint8)
Image.fromarray(ov).save(MD / "dissolve_check_f0422_50pct.png")
res.update(cavity_vs_ring_iou_plane=m.iou_report(), cavity_vs_ring_iou_film_hold=ious_film,
           u2_hold_frame_vs_mould_outline_iou=u2_vs_mould, flip_iou_lr_ud=m.flip_iou(),
           drain_empty_film_time=emp, cavity_fill_fraction_vs_time=fill, drain_order_far_to_near=[int(i) for i in m.order_empty])
# --------------------------------------------------------------- sheet ---
cw = 640
def tile(a, lab, st):
    im = Image.fromarray(a).resize((cw, int(a.shape[0] * cw / a.shape[1])), Image.LANCZOS)
    return im, lab, st
s24 = frame(576)
tiles = [tile(s24, "BUILD  Sh3b @ 24.00 s (f576): three cavities drained far->near, melt leaving the last", res["t=24.000"]),
         tile(kf2[66:474] if kf2.shape[0] == 540 else kf2, "BASELINE  proposals/kf-2.png (round-2 keyframe)", res["kf2_band"]),
         tile(ref[144:376], "REFERENCE  assets/references/styreneA.webp (band rows 144-375)", res["reference_band_rows144_375"]),
         tile(frame(660), "BUILD  Sh3b @ 27.50 s: the four hollows, wet-lit", res["t=27.500"])]
th = max(t[0].height for t in tiles)
sheet = Image.new("RGB", (cw * 2 + 30, (th + 70) * 2 + 20), (14, 14, 14))
d = ImageDraw.Draw(sheet)
for i, (im, lab, st) in enumerate(tiles):
    x = 10 + (i % 2) * (cw + 10); y = 10 + (i // 2) * (th + 70)
    sheet.paste(im, (x, y + (th - im.height) // 2))
    d.text((x, y + th + 6), lab, font=FONT, fill=(232, 226, 210))
    d.text((x, y + th + 28), f"lum<20 {st['frac_lum_lt20']:.2f}  p50 {st['p50']}  p95 {st['p95']}  p99 {st['p99']}  lit sat med {st['lit_median_sat']}  warm {st['lit_warm_frac']}  blue {st['lit_blue_frac']}",
           font=FONT, fill=(180, 172, 160))
sheet.save(SW / "melt-shot-compare-24.0s.jpg", quality=90)
json.dump(res, open(MD / "metrics.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "cavity_fill_fraction_vs_time"}, indent=0))
