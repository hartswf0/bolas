"""Extract frames from an encoded video and tile them (for looking, not for the film).
python3 build/look.py VIDEO OUT.jpg t1 t2 ... [--offset 3] [--crop x0,y0,x1,y1] [--cols 3] [--w 640]
Times are scene seconds; --offset adds the title-card length when VIDEO is film.mp4."""
import subprocess, sys, io
from PIL import Image, ImageDraw

args = sys.argv[1:]
def opt(name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
off = float(opt('--offset', 0)); crop = opt('--crop', None); cols = int(opt('--cols', 3)); w = int(opt('--w', 640))
video, out, ts = args[0], args[1], [float(t) for t in args[2:]]
ims = []
for t in ts:
    # frame-accurate: frame index = round(t*24) of the scene, plus the offset
    n = round((t + off) * 24)
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', video, '-vf', f'select=eq(n\\,{n})', '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-'], capture_output=True).stdout
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    if crop: im = im.crop(tuple(int(v) for v in crop.split(',')))
    h = round(im.height * w / im.width); im = im.resize((w, h))
    ImageDraw.Draw(im).text((6, 4), f'{t:.2f}s', fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * ims[0].height))
for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * w, (k // cols) * im.height))
sheet.save(out, quality=90)
