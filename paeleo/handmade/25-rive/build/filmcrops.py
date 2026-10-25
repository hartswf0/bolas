# crops of the dog from the finished film at given scene times: python3 filmcrops.py OUT t1 t2 ...
import sys, json, subprocess, os
from PIL import Image, ImageDraw
F = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = sys.argv[1]; ts = [float(x) for x in sys.argv[2:]]
tr = json.load(open(os.path.join(F, 'trace.json')))['frames']; tiles = []
for t in ts:
    i = int(round(t * 24)); p = os.path.join(F, 'build/cache/fc.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(F, 'film.mp4'), '-vf', 'select=eq(n\\,%d)' % (72 + i), '-frames:v', '1', p], check=True)
    im = Image.open(p); b = tr[i]['bbox']; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    t_ = im.crop((int(cx - 170), int(cy - 120), int(cx + 170), int(cy + 100))).resize((510, 330)); ImageDraw.Draw(t_).text((5, 5), '%.2fs' % (i / 24), fill='yellow'); tiles.append(t_)
cols = 6; rows = (len(tiles) + cols - 1) // cols; c = Image.new('RGB', (cols * 510, rows * 330))
for k, t_ in enumerate(tiles): c.paste(t_, ((k % cols) * 510, (k // cols) * 330))
c.save(out, quality=85)
