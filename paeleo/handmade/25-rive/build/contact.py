# contact sheet of rendered stills: python3 contact.py DIR OUT [cols] [scale]
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4; sc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.33
fs = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
ims = [Image.open(os.path.join(d, f)) for f in fs]; w, h = int(1280 * sc), int(720 * sc)
rows = (len(ims) + cols - 1) // cols; c = Image.new('RGB', (cols * w, rows * h), 'black'); dr = ImageDraw.Draw(c)
for k, (f, im) in enumerate(zip(fs, ims)):
    x, y = (k % cols) * w, (k // cols) * h; c.paste(im.resize((w, h)), (x, y)); dr.text((x + 4, y + 4), f + ' %.2fs' % (int(f[1:5]) / 24), fill='yellow')
c.save(out, quality=88)
