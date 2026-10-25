"""Fork: three fur-matte hypotheses on the same frames, composited on dusk blue, for side-by-side viewing."""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from lib_matte import *
from prep_dog import pick, KIT
HERE = os.path.dirname(os.path.abspath(__file__))
masks = json.load(open(os.path.join(KIT, 'masks.json')))
V = {
 'A_wide': dict(r_in=4, r_out=5, gf_r=2, gf_eps=2e-3, curve=None),
 'B_narrow': dict(r_in=2, r_out=3, gf_r=1, gf_eps=2e-4, curve=(.06, .94)),
 'C_prior_gf': dict(r_in=2, r_out=3, gf_r=1, gf_eps=2e-4, curve=(.06, .94), noline=True),
}
rows = []
for i in [9, 22, 45]:
    I = load(os.path.join(KIT, 'frames/f%03d.jpg' % i)); H, W = I.shape[:2]
    cov = coverage(pick(masks[str(i)]), W, H)
    tiles = []
    for k, v in V.items():
        tri = trimap(cov, v['r_in'], v['r_out'])
        a, F, B = solve(I, tri, cov, gf_r=v['gf_r'], gf_eps=v['gf_eps'], conf_k=1e9 if v.get('noline') else 0.004)
        if v['curve']:
            lo, hi = v['curve']; a = np.clip((a - lo) / (hi - lo), 0, 1)
        bg = np.zeros_like(I) + np.array([.10, .11, .2])
        c = F * a[..., None] + bg * (1 - a[..., None])
        ys, xs = np.nonzero(cov > 0); y0, y1, x0, x1 = ys.min() - 8, ys.max() + 8, xs.min() - 8, xs.max() + 8
        tiles.append(c[max(y0, 0):y1, max(x0, 0):x1])
    h = min(t.shape[0] for t in tiles)
    rows.append(np.concatenate([t[:h] for t in tiles], 1))
W = max(r.shape[1] for r in rows)
rows = [np.pad(r, [(0, 4), (0, W - r.shape[1]), (0, 0)]) for r in rows]
im = Image.fromarray((np.clip(np.concatenate(rows, 0), 0, 1) * 255).astype(np.uint8))
im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
im.save(os.path.join(HERE, '../proof/fork_fur_ABC.jpg'), quality=90); print(im.size)
