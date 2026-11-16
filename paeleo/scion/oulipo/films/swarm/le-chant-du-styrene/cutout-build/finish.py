"""Sh5 plate on black, gelled RGBA pieces, stills stats and the 16.5 s side-by-side."""
import cv2, numpy as np, json
from render import *
from PIL import Image
O = OUT
for n in ["bare_runner", "runner_with_rings", "ring0", "ring1", "ring2", "ring3"]:
    g = piece(n); a = np.clip(g[..., 3:4], 1e-4, 1)
    out = np.dstack([np.clip(g[..., :3] / a, 0, 1), g[..., 3]])
    cv2.imwrite(str(O / f"pieces/{n}_gelled.png"), cv2.cvtColor((out * 255 + .5).astype(np.uint8), cv2.COLOR_RGBA2BGRA))
heap = cv2.cvtColor(cv2.imread(str(O / 'sh5/heap_rgba_960x408.png'), -1), cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255
pr = practicals(camera(16.0)); a = heap[..., 3:4]
img = pr * (1 - a) + heap[..., :3] * a
lum = img @ np.array([.299, .587, .114], np.float32); hot = img * np.clip((lum - .45) / .3, 0, 1)[..., None]
img = rolloff(img + 0.22 * cv2.GaussianBlur(hot, (0, 0), 5) + 0.10 * cv2.GaussianBlur(hot, (0, 0), 16))
cv2.imwrite(str(O / 'sh5/heap_on_black.png'), cv2.cvtColor((img * 255 + .5).astype(np.uint8), cv2.COLOR_RGB2BGR))
def st(p):
    im = cv2.imread(str(p)); rgb = im[..., ::-1].astype(np.float32); L = rgb @ np.array([.299, .587, .114])
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); lit = L > 25; H = hsv[..., 0][lit] * 2; S = hsv[..., 1][lit] / 255
    return dict(lum_lt20=round(float((L < 20).mean()), 3), p50=float(np.percentile(L, 50).round(1)), p95=float(np.percentile(L, 95).round()),
                p99=float(np.percentile(L, 99).round()), max=float(L.max().round()), lit_p99=float(np.percentile(L[lit], 99).round()),
                lit_sat_median=round(float(np.median(S)), 2), lit_warm_frac=round(float(((H < 50) | (H > 340)).mean()), 2),
                lit_amber_frac_H28_50=round(float(((H >= 28) & (H < 50)).mean()), 2), lit_blue_frac=round(float(((H > 190) & (H < 250)).mean()), 2))
S = {k: st(O / p) for k, p in [('sh1_5.0s_f120', 'sh1/f0120.png'), ('sh2a_12.0s_f288', 'sh2a/f0288.png'), ('sh2b_16.5s_f396', 'sh2b/f0396.png'), ('sh5_heap', 'sh5/heap_on_black.png')]}
ref = np.array(Image.open('/home/user/bolas/paeleo/scion/oulipo/assets/references/styreneA.webp').convert('RGB'))[144:376]
cv2.imwrite(str(O / 'stills/_ref_band.png'), cv2.cvtColor(ref, cv2.COLOR_RGB2BGR)); S['reference_band'] = st(O / 'stills/_ref_band.png')
json.dump(S, open(O / 'stills/stats.json', 'w'), indent=1); print(json.dumps(S))
r = cv2.resize(ref, (960, 408))
def lab(im, t):
    im = np.ascontiguousarray(im.copy()); cv2.putText(im, t, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (232, 226, 210), 1, cv2.LINE_AA); return im
rd = lambda p: cv2.imread(str(O / p))[..., ::-1]
sbs = np.vstack([np.hstack([lab(r, 'reference styreneA.webp (band rows 144-375)'), lab(rd('sh2b/f0396.png'), 'U2 Sh2b 16.50 s (f396): runner + 4 rings, hold')]),
                 np.zeros((8, 1920, 3), np.uint8),
                 np.hstack([lab(rd('sh2a/f0312.png'), 'U2 Sh2a 13.00 s (f312): ring 1 at its gate'), lab(rd('sh5/heap_on_black.png'), 'U2 Sh5 heap (Granuls orange.jpg, GrabCut)')])])
for p in [O / 'stills/compare_16.5s.jpg', Path('/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/cutouts-compare-16.5s.jpg')]:
    cv2.imwrite(str(p), cv2.cvtColor(sbs, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
for f in (120, 312, 396): cv2.imwrite(str(O / f'stills/f{f:04d}.png'), cv2.imread(str(O / ('sh1' if f < 207 else 'sh2a' if f < 313 else 'sh2b') / f'f{f:04d}.png')))
