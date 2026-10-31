"""SCION 35 · stills and proof sheets, extracted from the ENCODED film (film frame = 72 + scene frame)."""
import subprocess, os, sys
import numpy as np
from PIL import Image, ImageDraw
from common import ROOT, CACHE

FILM = os.path.join(ROOT, 'film.mp4')
OUT = os.path.join(CACHE, 'film_frames')


def extract(scene_frames):
    os.makedirs(OUT, exist_ok=True)
    need = [i for i in scene_frames if not os.path.exists(os.path.join(OUT, '%04d.jpg' % i))]
    if need:
        sel = '+'.join('eq(n\\,%d)' % (72 + i) for i in need)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', FILM, '-vf', 'select=' + sel, '-vsync', '0', '-q:v', '2',
                        os.path.join(OUT, 'tmp_%04d.jpg')], check=True)
        for k, i in enumerate(sorted(need)):
            os.rename(os.path.join(OUT, 'tmp_%04d.jpg' % (k + 1)), os.path.join(OUT, '%04d.jpg' % i))
    return {i: Image.open(os.path.join(OUT, '%04d.jpg' % i)).convert('RGB') for i in scene_frames}


def strip(frames, box, path, cols=8, scale=1.0, label=True):
    ims = extract(frames)
    w, h = int((box[2] - box[0]) * scale), int((box[3] - box[1]) * scale)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new('RGB', (w * cols, h * rows), (20, 20, 30))
    for k, i in enumerate(frames):
        c = ims[i].crop(box).resize((w, h))
        if label:
            ImageDraw.Draw(c).text((4, 4), '%.3fs' % (i / 24), fill=(255, 255, 255))
        sheet.paste(c, ((k % cols) * w, (k // cols) * h))
    sheet.save(path, quality=88)


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        i = int(round(t * 24))
        extract([i])[i].save(os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % t), quality=90)
    P = os.path.join(ROOT, 'proof')
    strip(list(range(80, 97)), (850, 330, 1250, 640), os.path.join(P, 'turn_refusal_3.3-4.0s.jpg'), cols=6, scale=0.75)
    strip(list(range(174, 210)), (850, 330, 1250, 640), os.path.join(P, 'turn_back_7.25-8.7s.jpg'), cols=6, scale=0.6)
    strip(list(range(568, 590)), (60, 360, 560, 650), os.path.join(P, 'lie_down_23.7-24.6s.jpg'), cols=6, scale=0.6)
    strip(list(range(630, 690, 3)), (40, 330, 560, 650), os.path.join(P, 'look_in_26.25-28.7s.jpg'), cols=5, scale=0.6)
    print('stills ok')
