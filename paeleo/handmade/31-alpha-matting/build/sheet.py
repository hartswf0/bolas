"""contact sheet of film frames at scene times: python3 sheet.py out.jpg t1 t2 ... (scene seconds; film = +3 s)"""
import subprocess, sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; ts = [float(a) for a in sys.argv[2:]]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache/look'); os.makedirs(D, exist_ok=True)
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../film.mp4')
ims = []
for t in ts:
    p = os.path.join(D, 'f_%.3f.jpg' % t)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.4f' % (t + 3 + 1 / 48), '-i', F, '-frames:v', '1', p], check=True)
    im = Image.open(p).resize((640, 360)); ImageDraw.Draw(im).text((6, 6), '%.2fs' % t, fill=(255, 255, 0)); ims.append(im)
cols = 3; rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (640 * cols, 360 * rows))
for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 640, (k // cols) * 360))
sh.save(out, quality=85)
