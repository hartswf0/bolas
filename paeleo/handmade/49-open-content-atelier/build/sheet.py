"""Critic aid: sheet of frames (from build/cache/frames or an extracted folder). Usage: sheet.py out.jpg dir i1 i2 ... [--crop x0 y0 x1 y1]"""
import sys, os
from PIL import Image, ImageDraw
args = sys.argv[1:]; crop = None
if '--crop' in args:
    k = args.index('--crop'); crop = tuple(map(int, args[k + 1:k + 5])); args = args[:k]
out, d, ids = args[0], args[1], [int(a) for a in args[2:]]
ims = []
for i in ids:
    im = Image.open(os.path.join(d, f'f_{i:04d}.jpg'))
    if crop: im = im.crop(crop)
    im.thumbnail((640, 360)); ims.append((i, im))
c = 2 if len(ims) > 1 else 1; w, h = ims[0][1].size
sh = Image.new('RGB', (c * w, ((len(ims) + c - 1) // c) * (h + 16)), 'white'); dr = ImageDraw.Draw(sh)
for k, (i, im) in enumerate(ims):
    x, y = (k % c) * w, (k // c) * (h + 16); sh.paste(im, (x, y + 16)); dr.text((x + 4, y + 2), f'{i}  t={i/24:.2f}s', fill='black')
sh.save(out, quality=88)
