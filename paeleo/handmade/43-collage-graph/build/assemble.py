"""title (72) + scene (768) + end card (72) = 912 frames = 38.0 s; mux with the synthesized sound; stills"""
import os, subprocess, shutil
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE)
SEQ = os.path.join(HERE, 'cache/seq')
shutil.rmtree(SEQ, ignore_errors=True); os.makedirs(SEQ)
title = os.path.join(HERE, 'cache/cards/title.jpg'); end = os.path.join(HERE, 'cache/cards/end.jpg')
k = 0
for _ in range(72): os.symlink(title, os.path.join(SEQ, '%04d.jpg' % k)); k += 1
for i in range(768):
    p = os.path.join(HERE, 'cache/frames/s%04d.jpg' % i)
    assert os.path.exists(p), p
    os.symlink(p, os.path.join(SEQ, '%04d.jpg' % k)); k += 1
for _ in range(72): os.symlink(end, os.path.join(SEQ, '%04d.jpg' % k)); k += 1
assert k == 912
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(SEQ, '%04d.jpg'), '-i', os.path.join(HERE, 'cache/sound.wav'),
       '-c:v', 'libx264', '-preset', 'slow', '-crf', os.environ.get('CRF', '22'), '-pix_fmt', 'yuv420p', '-tune', 'film',
       '-c:a', 'aac', '-b:a', '160k', '-t', '38.0', '-movflags', '+faststart', os.path.join(TOP, 'film.mp4')]
subprocess.run(cmd, check=True)
os.makedirs(os.path.join(TOP, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    i = int(round(t * 24))
    Image.open(os.path.join(HERE, 'cache/frames/s%04d.jpg' % i)).save(os.path.join(TOP, 'stills/still_%04.1fs.jpg' % t), quality=90)
print('film', os.path.getsize(os.path.join(TOP, 'film.mp4')) / 1e6, 'MB')
