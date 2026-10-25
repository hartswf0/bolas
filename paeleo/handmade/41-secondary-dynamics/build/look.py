"""Proof sheets for looking: extract frames of film.mp4 at scene times, tile them 2-up with their time stamps.
python3 build/look.py OUTNAME t1 t2 ...   -> build/cache/look/OUTNAME_k.jpg (8 frames per sheet)"""
import sys, os, subprocess
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE); OUT = os.path.join(HERE, 'cache', 'look'); os.makedirs(OUT, exist_ok=True)
name, ts = sys.argv[1], [float(x) for x in sys.argv[2:]]
crop = os.environ.get('CROP')  # x0,y0,x1,y1 to zoom
ims = []
for t in ts:
    p = os.path.join(OUT, f'_f{t:06.2f}.jpg')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{3 + t + 0.02:.3f}', '-i', os.path.join(TOP, 'film.mp4'), '-frames:v', '1', '-q:v', '3', p], check=True)
    im = Image.open(p)
    if crop: im = im.crop(tuple(int(v) for v in crop.split(',')))
    im = im.resize((640, int(640 * im.height / im.width))); ImageDraw.Draw(im).text((8, 8), f'{t:.2f}s', fill=(255, 255, 0)); ims.append(im)
for s in range(0, len(ims), 8):
    part = ims[s:s + 8]; h = part[0].height; sheet = Image.new('RGB', (1280, h * ((len(part) + 1) // 2)))
    for k, im in enumerate(part): sheet.paste(im, ((k % 2) * 640, (k // 2) * h))
    sheet.save(os.path.join(OUT, f'{name}_{s // 8}.jpg'), quality=85)
print('sheets in', OUT)
