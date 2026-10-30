"""Critic aid: crops centred on the measured dog, 2x. Usage: dogsheet.py out.jpg framesdir i1 i2 ..."""
import sys, os, json
from PIL import Image, ImageDraw
out, d, ids = sys.argv[1], sys.argv[2], [int(a) for a in sys.argv[3:]]
m = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'measure.json')))
cw, ch = 300, 170; tiles = []
for i in ids:
    r = m[str(i)]; cx, cy = r['body_cx_screen'], r['body_cy_screen']
    im = Image.open(os.path.join(d, f'f_{i:04d}.jpg')).crop((int(cx - cw / 2 - 40), int(cy - ch / 2 - 30), int(cx + cw / 2 - 40), int(cy + ch / 2 - 30)))
    tiles.append((i, im.resize((cw * 2, ch * 2))))
c = 3; sh = Image.new('RGB', (c * cw * 2, ((len(tiles) + c - 1) // c) * (ch * 2 + 16)), 'white'); dr = ImageDraw.Draw(sh)
for k, (i, im) in enumerate(tiles):
    x, y = (k % c) * cw * 2, (k // c) * (ch * 2 + 16); sh.paste(im, (x, y + 16)); dr.text((x + 4, y + 2), f'{i} t={i/24:.2f}', fill='black')
sh.save(out, quality=85)
