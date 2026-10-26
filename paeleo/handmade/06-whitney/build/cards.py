"""SCION 06 · Whitney — title and end cards (3 s each), drawn as text plus a 3:2 Lissajous of light points.
Writes build/cache/title.mp4 and build/cache/end.mp4."""
import math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render as R

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
W, Hh = 1280, 720
BIG = ImageFont.truetype(os.path.join(C, 'BigShoulders800.ttf'), 58)
MONO = ImageFont.truetype(os.path.join(C, 'JetBrainsMono400.ttf'), 19)
SER = ImageFont.truetype(os.path.join(C, 'Literata400.ttf'), 25)
SERI = ImageFont.truetype(os.path.join(C, 'Literata400i.ttf'), 25)


def liss(buf, t, cx, cy, r, n=360):
    s = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = cx + r * np.sin(3 * s + 0.6 * t); y = cy + r * np.sin(2 * s)
    R.splat(buf, x, y, np.tile([0.95, 0.88, 0.7], (n, 1)), np.full(n, 0.5))


def card(lines, path, liss_pos):
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{Hh}', '-r', '24',
                           '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(72):
        t = i / 24
        buf = np.zeros((Hh, W, 3), np.float32)
        liss(buf, t, *liss_pos)
        lum = R.blur(buf, 1) * 1.8 + R.glow(buf) * 0.5
        bg = np.array([0.025, 0.03, 0.07], np.float32)
        out = 1 - (1 - bg) * np.exp(-lum)
        a = min(1, t / 0.5, (3 - t) / 0.5)
        im = Image.fromarray(np.clip(out * 255 * (0.25 + 0.75 * a), 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for (x, y, txt, font, col) in lines:
            d.text((x, y), txt, font=font, fill=tuple(int(c * a) for c in col))
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    card([(110, 250, 'PAE-02 · SCION 06 · John Whitney', BIG, (240, 236, 255)),
          (112, 330, 'Harmonic Motion Orchestra', SERI, (255, 214, 160)),
          (112, 372, 'The threshold, handmade', SER, (200, 196, 225)),
          (112, 610, 'a new prompt inspired by Whitney\'s harmonic motion; not his work, not endorsed by him', MONO, (130, 126, 160))],
         os.path.join(C, 'title.mp4'), (1010, 330, 120))
    L = [(90, 120, 'What it is made of', SERI, (255, 214, 160)),
         (90, 175, 'Points of light on computed curves. The dog is tubes of helical dot-lines on a', SER, (225, 222, 245)),
         (90, 210, 'skeleton proportioned from the archive dog\'s rig keys (Amateur Film New Jersey C,', SER, (225, 222, 245)),
         (90, 245, 'Home Movies, Internet Archive, public domain). No footage or drawing appears.', SER, (225, 222, 245)),
         (90, 300, 'It moves by an oscillator bank: the PAELEO score\'s six choices, gait as phase', SER, (225, 222, 245)),
         (90, 335, 'relations, and a 3:2 lock between the dog (3) and the house (2) that the calls', SER, (225, 222, 245)),
         (90, 370, 'detune and the changed circumstances restore. The moon is the phase visualizer.', SER, (225, 222, 245)),
         (90, 425, 'All sound is synthesized from the same oscillators; the voice is additive formants.', SER, (225, 222, 245)),
         (90, 600, 'Fonts: Literata, JetBrains Mono, Big Shoulders Display (SIL OFL). Built in numpy + Pillow + ffmpeg.', MONO, (130, 126, 160))]
    card(L, os.path.join(C, 'end.mp4'), (1120, 560, 60))
