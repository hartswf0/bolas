#!/usr/bin/env python3
"""Write each card's eight inks, darkest first, for re-printing archive frames live (the same k-means as stencil.py).
python3 shorts/tools/inks.py <card> ...   writes assets/shorts/parts/<card>/inks.json."""
import json, os, sys
import numpy as np
from PIL import Image
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for card in sys.argv[1:]:
    m = json.load(open(os.path.join(root, 'assets/shorts/parts', card, 'parts.json')))
    ci = np.asarray(Image.open(os.path.join(root, m['card'])).convert('RGB'), dtype=np.float32).reshape(-1, 3) / 255
    rng = np.random.default_rng(1910); px = ci[rng.choice(len(ci), 20000, replace=False)]
    cen = px[rng.choice(len(px), 8, replace=False)]
    for _ in range(20):
        lab = np.argmin(((px[:, None] - cen[None]) ** 2).sum(-1), 1)
        cen = np.array([px[lab == k].mean(0) if (lab == k).any() else cen[k] for k in range(8)])
    cen = cen[np.argsort(cen @ [.3, .59, .11])]
    json.dump([[int(round(v * 255)) for v in c] for c in cen], open(os.path.join(root, 'assets/shorts/parts', card, 'inks.json'), 'w'))
    print(card, (cen * 255).astype(int).tolist())
