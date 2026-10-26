"""Contact sheet of rendered scene frames (for looking). python3 build/sheet.py out.jpg x0,y0,x1,y1 cols f1 f2 ... (scene frame numbers)"""
import sys, os, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
out, box, cols = sys.argv[1], [int(v) for v in sys.argv[2].split(',')], int(sys.argv[3])
fr = [int(v) for v in sys.argv[4:]]
subprocess.run(['node', os.path.join(HERE, 'render.js'), 'stills', ','.join('f%d' % (72 + f) for f in fr)], check=True, capture_output=True)
w, h = box[2] - box[0], box[3] - box[1]
sc = min(1.0, 1600 / (cols * w))
tw, th = int(w * sc), int(h * sc)
rows = (len(fr) + cols - 1) // cols
S = Image.new('RGB', (cols * tw, rows * th))
for k, f in enumerate(fr):
    im = Image.open(os.path.join(HERE, 'cache', 'stills', 's_f%d.jpg' % (72 + f))).crop(box).resize((tw, th))
    ImageDraw.Draw(im).text((4, 4), '%d  %.2fs' % (f, f / 24), fill=(255, 255, 0))
    S.paste(im, ((k % cols) * tw, (k // cols) * th))
S.save(out)
