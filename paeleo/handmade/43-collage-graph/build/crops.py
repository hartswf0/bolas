"""proof crops of rendered scene frames: crops.py out.jpg x0,y0,x1,y1 i1 i2 ...  (or --film t1 t2 ... to crop the encoded film)"""
import sys, os, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
out, box = sys.argv[1], tuple(map(int, sys.argv[2].split(',')))
args = sys.argv[3:]; film = args and args[0] == '--film'
if film: args = args[1:]
tiles = []
for a in args:
    if film:
        p = os.path.join(HERE, 'cache/_c.jpg')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % (float(a) + 3.0 + 0.01), '-i', os.path.join(HERE, '../film.mp4'), '-frames:v', '1', p], check=True)
        im = Image.open(p); lab = 'film scene %.2fs' % float(a)
    else:
        im = Image.open(os.path.join(HERE, 'cache/frames/s%04d.jpg' % int(a))); lab = '%.3fs' % (int(a) / 24)
    im = im.crop(box); ImageDraw.Draw(im).text((3, 3), lab, fill=(255, 255, 0)); tiles.append(im)
w, h = tiles[0].size; cols = max(1, min(4, 1600 // w))
c = Image.new('RGB', (w * cols, h * ((len(tiles) + cols - 1) // cols)))
for k, t in enumerate(tiles): c.paste(t, ((k % cols) * w, (k // cols) * h))
c.save(out, quality=88)
