"""SCION 51 · proof sheets cut from the ENCODED film.mp4 (never from the renderer's frames): the turns, the calls' rapid
substitution, the approach, the sill. Crops follow the measured dog centre in trace.json. Writes proof/*.jpg."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from lib import OUT, FPS, W, H

FILM = os.path.join(OUT, 'film.mp4'); PR = os.path.join(OUT, 'proof'); os.makedirs(PR, exist_ok=True)
TR = {f['i']: f for f in json.load(open(os.path.join(OUT, 'trace.json')))['frames']}


def grab(i):
    """scene frame i from the encoded film (offset 72 title frames)"""
    t = (72 + i + 0.5) / FPS
    r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.4f}', '-i', FILM, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True)
    return Image.frombytes('RGB', (W, H), r.stdout)


def crop(im, i, w=420, h=280):
    f = TR[i]; cx, cy = f['x_screen'], f['y_screen']
    x0 = int(min(max(cx - w / 2, 0), W - w)); y0 = int(min(max(cy - h / 2 - 20, 0), H - h))
    return im.crop((x0, y0, x0 + w, y0 + h))


def sheet(name, idxs, cols=4, cropit=True, scale=1.0):
    ims = []
    for i in idxs:
        im = grab(i); im = crop(im, i) if cropit else im.resize((int(W * scale), int(H * scale)))
        d = ImageDraw.Draw(im); f = TR[i]
        d.rectangle((0, 0, 260, 16), fill=(0, 0, 0)); d.text((3, 2), f"{i} t={i / FPS:.2f} {f['state']} {f['facing']} {f['posture']}", fill=(255, 255, 0))
        ims.append(im)
    w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (w * cols, h * rows))
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * w, (k // cols) * h))
    sh.save(os.path.join(PR, name + '.jpg'), quality=85)


if __name__ == '__main__':
    sheet('turn_away_3.4-4.3s', list(range(80, 104, 2)))
    sheet('turn_back_7.3-8.9s', list(range(175, 215, 3)))
    sheet('calls_rapid_cuts_1.0-1.6s', list(range(24, 40)))
    sheet('approach_head_low', [356, 380, 410, 440, 470, 500, 530, 560])
    sheet('sill_lie_lookin', [575, 590, 620, 640, 650, 660, 680, 767], cols=2, cropit=False, scale=0.5)
    print('proof sheets written')
