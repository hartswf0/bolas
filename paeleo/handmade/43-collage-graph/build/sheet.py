"""contact sheet of rendered scene frames at given times (s): sheet.py out.jpg t1 t2 ... [--crop x0,y0,x1,y1]"""
import sys, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[2:]; crop = None
if '--crop' in args:
    k = args.index('--crop'); crop = tuple(map(int, args[k + 1].split(','))); args = args[:k] + args[k + 2:]
ts = [float(a) for a in args]
tw, th = 480, 270
if crop: th = int(tw * (crop[3] - crop[1]) / (crop[2] - crop[0]))
cols = 4
sh = Image.new('RGB', (tw * cols, th * ((len(ts) + cols - 1) // cols)))
for n, t in enumerate(ts):
    i = min(767, int(round(t * 24)))
    im = Image.open(os.path.join(HERE, 'cache/frames/s%04d.jpg' % i))
    if crop: im = im.crop(crop)
    im = im.resize((tw, th), Image.LANCZOS)
    ImageDraw.Draw(im).text((4, 4), '%.2fs' % (i / 24), fill=(255, 255, 0))
    sh.paste(im, ((n % cols) * tw, (n // cols) * th))
sh.save(sys.argv[1], quality=85)
