"""stills/ (from film.mp4 itself, scene time + 3 s title) and proof sheets (from the rendered frames)"""
import os, subprocess
from PIL import Image, ImageDraw
from geom import CACHE, HERE
F = os.path.dirname(HERE)
os.makedirs(os.path.join(F, 'stills'), exist_ok=True); os.makedirs(os.path.join(F, 'proof'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    out = os.path.join(F, 'stills', f'still_{t:04.1f}s.jpg')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{3 + t + 0.5 / 24:.4f}', '-i', os.path.join(F, 'film.mp4'), '-frames:v', '1', '-q:v', '2', out], check=True)
# whole-scene contact sheet, every 0.5 s
fr = list(range(0, 768, 12)); cols = 8; cw, ch = 320, 180
sheet = Image.new('RGB', (cols * cw, ((len(fr) + cols - 1) // cols) * ch))
for k, i in enumerate(fr):
    im = Image.open(os.path.join(CACHE, 'frames', f's{i:04d}.jpg')).resize((cw, ch))
    ImageDraw.Draw(im).text((4, 3), f'{i / 24:.1f}s', fill=(255, 230, 120))
    sheet.paste(im, ((k % cols) * cw, (k // cols) * ch))
sheet.save(os.path.join(F, 'proof', 'contact_sheet.jpg'), quality=85)
print('stills + contact sheet')
