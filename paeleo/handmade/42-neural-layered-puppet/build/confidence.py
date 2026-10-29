"""SCION 42 · confidence map: per template point, the mean photometric residual of the learned fit over the training
frames (bright = the layers explain that point badly), with the hinges sized by their rms disagreement."""
import os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
M = np.load(os.path.join(ROOT, 'model', 'puppet.npz'))
p = M['p']; r = M['photo_resid']; r = np.clip(r / np.percentile(r, 95), 0, 1)
S = 4; x0, y0 = p.min(0) - 10; w, h = (p.max(0) - p.min(0) + 20) * S
im = Image.new('RGB', (int(w), int(h)), (14, 14, 24)); d = ImageDraw.Draw(im)
for (x, y), v in zip(p, r):
    c = (int(40 + 215 * v), int(60 + 120 * (1 - v)), int(160 * (1 - v)))
    d.rectangle([(x - x0) * S, (y - y0) * S, (x - x0 + 2) * S - 1, (y - y0 + 2) * S - 1], fill=c)
for (a, b), pv, e in zip(M['joint_keys'], M['joint_pivots'], M['joint_rms']):
    q = ((pv[0] - x0) * S, (pv[1] - y0) * S); rr = 2 * e
    d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=(255, 230, 150), width=2)
d.text((8, 8), 'photometric residual per point (red = poorly explained); rings = hinge rms (radius 2x px)', fill=(220, 220, 220))
im.save(os.path.join(ROOT, 'proof', 'confidence.png'))
