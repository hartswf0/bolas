"""Reference beside 3 frames of the test shot, labelled."""
import subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
REF = '/home/user/bolas/paeleo/scion/oulipo/assets/references/oucipo.webp'
MP4 = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-machine-a-tuer-le-temps/test-shot.mp4'
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-machine-a-tuer-le-temps/test-shot-compare.jpg'
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
picks = [(18, 'f18 (0:00.75) notebook: 05 set down in slot 1, red pencil strikes 5'),
         (100, 'f100 (0:04.17) cut B pos 1: 05 glance, held at half speed'),
         (190, 'f190 (0:07.92) cut B pos 2: 04 the door')]
ref = Image.open(REF).convert('RGB'); ref = ref.resize((1280, round(ref.height * 1280 / ref.width)))
frames = []
with tempfile.TemporaryDirectory() as td:
    for f, lab in picks:
        p = f'{td}/{f}.png'
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', MP4, '-vf', f'select=eq(n\\,{f})', '-frames:v', '1', p], check=True)
        frames.append((Image.open(p).convert('RGB').resize((640, 360)), lab))
W = 1280; H = 40 + ref.height + 2 * (360 + 40) + 10
o = Image.new('RGB', (W, H), (250, 248, 244)); d = ImageDraw.Draw(o)
d.text((10, 8), 'REFERENCE  oucipo.webp (Drouot lot 175 photograph)', font=F, fill=(20, 20, 20))
o.paste(ref, (0, 40)); y = 40 + ref.height
cells = [(0, y), (640, y), (0, y + 400)]
for (im, lab), (x, yy) in zip(frames, cells):
    d.text((x + 8, yy + 8), lab[:58], font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16), fill=(20, 20, 20))
    o.paste(im, (x, yy + 36))
d.text((660, y + 420), 'TEST SHOT  la-machine-a-tuer-le-temps\n10.0 s, 1280x720, 24 fps\nframes taken from test-shot.mp4', font=F, fill=(20, 20, 20))
o.save(OUT, quality=88); print(OUT, o.size)
