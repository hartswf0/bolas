"""SCION 22 · stills extracted from film.mp4 (scene time + 3 s title), and a proof sheet of the turns from the film."""
import os, subprocess
from PIL import Image, ImageDraw
from common import FOLDER
film = os.path.join(FOLDER, 'film.mp4')
os.makedirs(os.path.join(FOLDER, 'stills'), exist_ok=True); os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
def grab(t, out):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % (t + 3.0), '-i', film, '-frames:v', '1', '-q:v', '2', out], check=True)
for t in (3.6, 9.0, 19.0, 28.0):
    grab(t, os.path.join(FOLDER, 'stills', 'still_%04.1fs.jpg' % t))
for name, ts in (('turn_away', [3.42, 3.54, 3.62, 3.71, 3.79, 3.88, 3.96, 4.08]), ('turn_back', [7.38, 7.46, 7.54, 7.67, 7.92, 8.17, 8.29, 8.42]),
                 ('look_in', [26.0, 26.5, 26.75, 27.0, 27.5, 28.0, 28.4, 29.0])):
    sheet = Image.new('RGB', (4 * 480, 2 * 270))
    for k, t in enumerate(ts):
        p = '/tmp/_s22_%d.jpg' % k if False else os.path.join(FOLDER, 'build', 'cache', '_s.jpg')
        grab(t, p)
        im = Image.open(p).resize((480, 270)); ImageDraw.Draw(im).text((6, 6), '%.2f s (from film.mp4)' % t, fill=(255, 255, 0))
        sheet.paste(im, ((k % 4) * 480, (k // 4) * 270))
    sheet.save(os.path.join(FOLDER, 'proof', name + '.jpg'), quality=85)
print('stills + proof')
