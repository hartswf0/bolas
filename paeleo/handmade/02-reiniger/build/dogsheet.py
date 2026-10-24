"""Design sheet: the dog puppet alone, large, for several score frames (the silhouette-read test)."""
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
from theatre import *
rig = json.load(open(os.path.join(OUT, 'rig.json')))
frames = [int(a) for a in sys.argv[1:]]
cell = 420; sc = 200
sheet = Image.new('L', (cell * 3, cell * ((len(frames) + 2) // 3)), 235)
for j, i in enumerate(frames):
    R = rig[i]; dog = DogRig(); dp = dog.pose(i, R['dog'], {k: tuple(v) for k, v in R['feet'].items()})
    im = Image.new('L', (cell * 2, cell * 2), 235); d = ImageDraw.Draw(im)
    x0 = R['dog']['x']
    def tp(p): return [((x - x0) * sc * 2 + cell, (1.0 - y) * sc * 2) for x, y in p]
    d.line([(0, 1.0 * sc * 2), (cell * 2, 1.0 * sc * 2)], fill=150, width=2)
    for p in dp['fills']: d.polygon(tp(p), fill=0)
    for p in dp['holes']: d.polygon(tp(p), fill=235)
    im = im.resize((cell, cell), Image.LANCZOS)
    ImageDraw.Draw(im).text((8, 8), f"{i} t={R['t']:.2f} {R['state']}", fill=90)
    sheet.paste(im, ((j % 3) * cell, (j // 3) * cell))
sheet.save(os.path.join(OUT, 'preview', 'dogsheet.png'))
