"""World matte diagnostics: woman / hand / door leaf+lace / cloud, each on a dark dusk and a warm lamp background."""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache')
def tile(P, bg, h=280):
    a = P[..., 3:4]; out = P[..., :3] + np.array(bg, np.float32) * (1 - a)
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)); return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
ims = []
for n in ['woman', 'hand']:
    P = np.load(os.path.join(C, n + '.npz'))['P'].astype(np.float32)
    ims += [tile(P, (.08, .09, .17)), tile(P, (1, .78, .45))]
z = np.load(os.path.join(C, 'door_leaf.npz')); P = z['P'].astype(np.float32); lace = z['lace'].astype(np.float32)
L = P.copy(); L[..., 3] = 1 - (1 - lace) * (lace > 0)  # lace window over a lamp
ims += [tile(P, (0, 0, 0)), tile(np.dstack([np.dstack([lace] * 3) * .9, lace]), (1, .7, .35))]
cl = np.load(os.path.join(C, 'cloud/c10.npz'))['P'].astype(np.float32)
ims += [tile(cl, (.08, .09, .17)), tile(cl, (.9, .5, .45))]
W = sum(i.width for i in ims[:6]); sh = Image.new('RGB', (max(W, sum(i.width for i in ims[6:])), 560))
x = 0
for i in ims[:6]: sh.paste(i, (x, 0)); x += i.width
x = 0
for i in ims[6:]: sh.paste(i, (x, 280)); x += i.width
sh.save(os.path.join(HERE, '../proof/world_matte_diagnostics.jpg'), quality=88); print(sh.size)
