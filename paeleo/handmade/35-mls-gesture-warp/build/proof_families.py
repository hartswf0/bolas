"""SCION 35 · the hard proof of the lineage: the same handle move (head lowered 35 deg on the neck, tail tucked, a
fore paw lifted) applied to the same profile print under each MLS family for every layer, then under the per-region
choice used in the film (rigid skull, similarity legs/tail, affine coat/neck). Writes proof/families.jpg and
proof/families.json (distortion per layer)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import render, anim
from common import ROOT, PAPER

i = 300  # a quiet watching frame (12.5 s), standing in profile
sh, Q, root, info = anim.dog_pose(i, with_stretch=False)
# the move: neck down round the withers, head further down, tail tucked, near fore paw lifted
Q = {k: v.copy() for k, v in Q.items()}
anim.rot(Q, ['poll'] + anim.HEADK, Q['withers'], -35)
anim.rot(Q, anim.HEADK, Q['poll'], -10)
anim.rot(Q, anim.TAILK, Q['tail0'], 55)
Q['fr_paw'] = Q['fr_paw'] + np.array([-18, -30]); Q['fr_wr'] = Q['fr_wr'] + np.array([-14, -26]); Q['fr_el'] = Q['fr_el'] + np.array([-4, -6])
meta, layers = render.load_print(sh)
orig = dict(meta['family'])
panels, stats = [], {}
for label, fam in (('all affine', 'affine'), ('all similarity', 'similarity'), ('all rigid', 'rigid'), ('per region (film)', None)):
    for k in meta['family']:
        meta['family'][k] = fam if fam else orig[k]
    rgb, cov, lay, st = render.warp_print(sh, Q)
    img = np.ones_like(rgb) * PAPER
    img = img * (1 - cov[..., None]) + rgb * cov[..., None]
    x0, y0 = int(root[0] - 200), int(root[1] - 240)
    im = Image.fromarray((np.clip(img[y0:y0 + 280, x0:x0 + 380], 0, 1) * 255).astype(np.uint8)).resize((570, 420))
    d = ImageDraw.Draw(im)
    d.text((8, 6), label, fill=(30, 40, 100))
    for k2 in ('neck', 'head', 'torso', 'leg_fr', 'tail'):
        if k2 in st:
            pass
    y = 384
    d.text((8, y), 'max dot anisotropy  neck %.2f  skull %.2f  coat %.2f  leg %.2f' % (st['neck']['aniso_max'], st['head']['aniso_max'], st['torso']['aniso_max'], st['leg_fr']['aniso_max']), fill=(30, 40, 100))
    d.text((8, y + 16), 'skull area %.2f-%.2f   folded cells %d' % (st['head']['area_min'], st['head']['area_max'], sum(v['folds'] for v in st.values())), fill=(30, 40, 100))
    panels.append(im)
    stats[label] = {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in st.items()}
for k in orig:
    meta['family'][k] = orig[k]
sheet = Image.new('RGB', (570 * 2, 420 * 2), (230, 224, 210))
for n, p in enumerate(panels):
    sheet.paste(p, ((n % 2) * 570, (n // 2) * 420))
sheet.save(os.path.join(ROOT, 'proof', 'families.jpg'), quality=90)
json.dump(dict(about='same handles, same print, four family assignments; per layer: max/mean anisotropy of the dot grid, area range, folds, handle error (px)', stats=stats),
          open(os.path.join(ROOT, 'proof', 'families.json'), 'w'), indent=1)
print('families ok')
