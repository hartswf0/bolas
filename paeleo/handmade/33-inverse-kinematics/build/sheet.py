"""Contact sheet for looking: python3 sheet.py out.png crop|full i,j,k ...  (crops centre on the measured dog)."""
import sys, os, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
out, mode, idx = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(',')]
tiles = []
for i in idx:
    im = Image.open(os.path.join(HERE, 'cache/frames/%04d.png' % i)).convert('RGB')
    if mode == 'crop':
        m = json.load(open(os.path.join(HERE, 'cache/measure/%04d.json' % i)))
        cx, cy = m.get('cx', 640), m.get('cy', 400)
        w, h = 400, 260
        x0 = int(min(max(0, cx - w / 2), 1280 - w)); y0 = int(min(max(0, cy - h / 2 - 20), 720 - h))
        im = im.crop((x0, y0, x0 + w, y0 + h)).resize((w * 3 // 2, h * 3 // 2), Image.LANCZOS)
    else:
        im = im.resize((640, 360), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.text((6, 4), '%d  %.2fs' % (i, i / 24), fill=(255, 255, 255))
    tiles.append(im)
cols = 3 if mode == 'crop' else 2
tw, th = tiles[0].size
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th), (0, 0, 0))
for k, t in enumerate(tiles):
    sheet.paste(t, ((k % cols) * tw, (k // cols) * th))
sheet.save(out)
