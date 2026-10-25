"""Deliverable contract: individual RGBA pieces, contour masks, failure masks, original-coordinate transforms.
-> ../pieces/<name>.png (RGBA, source pixels + our alpha), <name>_contour.png, <name>_fail.png, manifest.json
Failure mask colours: red = SAM kept it, our cut removed it; green = our cut kept it, SAM did not; yellow = matte band
(0.02 < alpha < 0.98). The transform maps piece pixel (u, v) to source-frame pixel (u + ox, v + oy)."""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from graphcut import contour
C = os.path.join(HERE, 'cache')
OUT = os.path.join(os.path.dirname(HERE), 'pieces')
os.makedirs(OUT, exist_ok=True)
DOG_USED = [0, 9, 13, 30, 34, 42, 43, 44, 45]
SRC = {'dog': 'paeleo/handmade/kit/archive-dog/frames/f%03d.jpg', }
logd = json.load(open(os.path.join(C, 'dog', 'log.json')))
logw = json.load(open(os.path.join(C, 'world', 'log.json')))
man = {'about': __doc__, 'pieces': []}


def write(name, z, src, extra):
    rgb = z['rgb']; a = z['alpha'].astype(np.float32); fg = z['fg']; sam = z['sam']
    rgba = np.dstack([rgb, (a * 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)
    Image.fromarray((contour(a > .5) * 255).astype(np.uint8)).save(os.path.join(OUT, name + '_contour.png'), optimize=True)
    f = np.zeros(rgb.shape, np.uint8)
    f[sam & ~fg] = [255, 40, 40]; f[fg & ~sam] = [40, 255, 40]; f[(a > .02) & (a < .98)] = [255, 230, 40]
    Image.fromarray(f).save(os.path.join(OUT, name + '_fail.png'), optimize=True)
    ox, oy = [int(v) for v in z['origin']]
    man['pieces'].append(dict({'name': name, 'source': src, 'transform_piece_to_source': {'ox': ox, 'oy': oy, 'scale': 1},
                               'size': [int(a.shape[1]), int(a.shape[0])], 'px_cut': int((a > .5).sum()),
                               'px_disagree_with_sam': int((fg != sam).sum())}, **extra))


for i in DOG_USED:
    z = np.load(os.path.join(C, 'dog', 'f%03d.npz' % i))
    write('dog_f%03d' % i, z, SRC['dog'] % i, {'log': logd.get(str(i))})
for n in ('woman_stand', 'door_panel', 'hand', 'pillar', 'shrub', 'bowl'):
    z = np.load(os.path.join(C, 'world', n + '.npz'))
    lg = logw[n]
    write(n, z, '%s/frames/f%03d.jpg' % (lg['src'], lg['frame']), {'log': lg})
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print(len(man['pieces']), 'pieces')
