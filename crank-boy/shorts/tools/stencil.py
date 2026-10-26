#!/usr/bin/env python3
"""Stencil Town proof: re-print an archive frame in a card's own inks, the way the card was printed.
python3 shorts/tools/stencil.py <card id> <plate.mp4> <seconds> <out.jpg> [--crop x,y,w,h]
1. The card's inks: k-means (8) on the card's pixels.
2. The frame's tones are mapped onto those inks by luminance order, through a 4x4 ordered dither (the print's screen).
3. A key plate: the frame's darks in the card's ink colour, laid one pixel off register over the colour plate.
Writes a strip: the frame as found | re-printed in the card's inks."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
card, plate, sec, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
crop = [int(v) for v in sys.argv[sys.argv.index('--crop') + 1].split(',')] if '--crop' in sys.argv else None
m = json.load(open(os.path.join(root, 'assets/shorts/parts', card, 'parts.json')))
ci = np.asarray(Image.open(os.path.join(root, m['card'])).convert('RGB'), dtype=np.float32).reshape(-1, 3) / 255
rng = np.random.default_rng(1910); px = ci[rng.choice(len(ci), 20000, replace=False)]
cen = px[rng.choice(len(px), 8, replace=False)]
for _ in range(20):
    lab = np.argmin(((px[:, None] - cen[None]) ** 2).sum(-1), 1)
    cen = np.array([px[lab == k].mean(0) if (lab == k).any() else cen[k] for k in range(8)])
lum = cen @ [.3, .59, .11]; inks = cen[np.argsort(lum)]; ink = inks[0]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(sec), '-i', plate, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
import io
fr = Image.open(io.BytesIO(raw)).convert('RGB')
if crop: fr = fr.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
fr = fr.resize((480, int(480 * fr.height / fr.width)), Image.LANCZOS)
a = np.asarray(fr, dtype=np.float32) / 255
L = a @ [.3, .59, .11]
L = (L - np.percentile(L, 2)) / max(1e-3, np.percentile(L, 98) - np.percentile(L, 2))
bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - .5
h, w = L.shape
B = np.tile(bayer, (h // 4 + 1, w // 4 + 1))[:h, :w]
idx = np.clip(np.round(np.clip(L, 0, 1) * 6 + B * .9) + 1, 1, 7).astype(int)   # colour plate: the 7 lighter inks
col = inks[idx]
key = (Image.fromarray((np.clip(1 - L * 2.2, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6)))
k = np.asarray(key, dtype=np.float32)[..., None] / 255
k = np.roll(np.roll(k, 1, 0), 1, 1)                                               # one pixel off register
outp = col * (1 - k * .85) + ink * (k * .85)
grain = rng.normal(0, .025, (h, w, 1)); outp = np.clip(outp + grain, 0, 1)
strip = Image.new('RGB', (w * 2 + 8, h), (214, 198, 158))
strip.paste(fr, (0, 0)); strip.paste(Image.fromarray((outp * 255).astype(np.uint8)), (w + 8, 0))
strip.save(out, quality=86)
print(out, [tuple((c * 255).astype(int)) for c in inks])
