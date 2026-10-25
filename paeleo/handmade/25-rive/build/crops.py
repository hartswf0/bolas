# crops around the dog (from the render trace bbox), 2x, labelled: python3 crops.py DIR OUT [cols]
import sys, os, json
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
tr = {f['i']: f for f in json.load(open(os.path.join(d, 'render-trace.json')))['trace']}
fs = sorted(f for f in os.listdir(d) if f.endswith('.jpg')); cw, chh = 300, 220; tiles = []
for f in fs:
    i = int(f[1:5]); im = Image.open(os.path.join(d, f)); b = tr[i]['bbox']; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    x0, y0 = int(cx - cw / 2), int(cy - chh / 2 - 10); t = im.crop((x0, y0, x0 + cw, y0 + chh)).resize((cw * 2 // 1, chh * 2 // 1))
    dr = ImageDraw.Draw(t); dr.text((6, 6), '%s %.2fs %s' % (f, i / 24, tr[i]['sm']['facing'] + '/' + tr[i]['sm']['attention']), fill='yellow'); tiles.append(t)
rows = (len(tiles) + cols - 1) // cols; W, H = tiles[0].size; c = Image.new('RGB', (cols * W, rows * H))
for k, t in enumerate(tiles): c.paste(t, ((k % cols) * W, (k // cols) * H))
c.save(out, quality=85)
