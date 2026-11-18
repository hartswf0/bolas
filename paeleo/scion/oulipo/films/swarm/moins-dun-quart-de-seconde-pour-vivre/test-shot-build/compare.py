"""test-shot-compare.jpg: reference + chosen keyframe beside 3 frames of the shot, labelled in the film's hand."""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from page import write, SWARM

ROOT = os.path.abspath(os.path.join(SWARM, '../../..'))
ref = Image.open(os.path.join(ROOT, 'assets/references/iteration-001.webp')).convert('RGB')
kf = Image.open(os.path.join(SWARM, 'proposals/kf-1.png')).convert('RGB')
mp4 = os.path.join(SWARM, 'test-shot.mp4')
times = [(1.2, 'B2 WRITING (0:01.2)'), (4.0, 'B2 HELD, LAMP CLEAR (0:04.0)'), (9.5, 'B3 HELD, FLAP CLEAR (0:09.5)')]
frames = []
for t, _ in times:
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(t), '-i', mp4, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    frames.append(Image.frombytes('RGB', (960, 540), raw))
Wd = 1920
refW = ref.resize((Wd, int(ref.height * Wd / ref.width)), Image.LANCZOS)
kfc = kf.crop((0, 380, 1280, 720))                    # kf-1 strip B row
kfW = kfc.resize((Wd, int(kfc.height * Wd / kfc.width)), Image.LANCZOS)
fw = (Wd - 2 * 24) // 3
fr = [f.resize((fw, int(540 * fw / 960)), Image.LANCZOS) for f in frames]
pad, lab = 24, 60
H = pad + lab + refW.height + pad + lab + kfW.height + pad + lab + fr[0].height + pad
im = Image.new('L', (Wd + 2 * pad, H), 255)
big = Image.new('L', (im.width * 2, im.height * 2), 255)
d = ImageDraw.Draw(big)
y = pad
write(d, "REFERENCE - MENU AND TRONDHEIM, ITERATION-001", pad, y + 8, 30, 1, 3.6); y += lab + refW.height + pad
write(d, "CHOSEN KEYFRAME KF-1 (STRIP B ROW)", pad, y + 8, 30, 2, 3.6); y += lab + kfW.height + pad
write(d, "TEST SHOT FRAMES", pad, y + 8, 30, 3, 3.6)
im = big.resize(im.size, Image.LANCZOS).convert('RGB')
y = pad + lab
im.paste(refW, (pad, y)); y += refW.height + pad + lab
im.paste(kfW, (pad, y)); y += kfW.height + pad + lab
for i, f in enumerate(fr):
    im.paste(f, (pad + i * (fw + 24), y))
d = ImageDraw.Draw(im)
big2 = Image.new('L', (im.width * 2, 2 * 50), 255)
for i, (t, s) in enumerate(times):
    pass
im2 = Image.new('RGB', (im.width, im.height + 60), 'white')
im2.paste(im, (0, 0))
b = Image.new('L', (im.width * 2, 120), 255)
db = ImageDraw.Draw(b)
for i, (t, s) in enumerate(times):
    write(db, s, pad + i * (fw + 24), 10, 22, 10 + i, 3.0)
im2.paste(b.resize((im.width, 60), Image.LANCZOS).convert('RGB'), (0, im.height - 10))
im2.save(os.path.join(SWARM, 'test-shot-compare.jpg'), quality=90)
print('ok', im2.size)
