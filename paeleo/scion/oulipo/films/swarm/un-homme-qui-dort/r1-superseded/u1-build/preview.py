"""preview.py <rig_module> t1 t2 ... -> scratch contact of frames (no kit, for checking)."""
import sys, importlib
import os, sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from lib import composite
mod = importlib.import_module(sys.argv[1])
out = sys.argv[2]
ts = [float(x) for x in sys.argv[3:]]
layers, rep = mod.build(write=False)
ims = []
for t in ts:
    g, a = composite(layers, mod.cam, t)
    assert a.min() > 0.99, f"uncovered pixels at t={t}: min alpha {a.min():.3f}"
    ims.append(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)))
cols = 2
w, h = ims[0].size
sheet = Image.new("L", (w * cols, h * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
print(rep)
