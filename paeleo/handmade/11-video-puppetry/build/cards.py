"""SCION 11 · title card and end card (72 frames each) -> build/cache/cards/{title,end}_%02d.jpg"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
FD = os.path.join(ROOT, 'tools/paeleo/fonts')
OUT = os.path.join(HERE, 'cache', 'cards')
W, H = 1280, 720
BIG = ImageFont.truetype(os.path.join(FD, 'f5.woff2'), 74)
MID = ImageFont.truetype(os.path.join(FD, 'f2.woff2'), 40)
MONO = ImageFont.truetype(os.path.join(FD, 'f14.woff2'), 19)
BG = (26, 28, 44)
FG = (234, 224, 200)
DIM = (170, 160, 150)


def paper():
    r = np.random.default_rng(5)
    n = r.normal(0, 1, (H // 6 + 1, W // 6 + 1)).astype(np.float32)
    n = np.asarray(Image.fromarray(n).resize((W, H), Image.BICUBIC))
    a = np.array(BG, np.float32)[None, None] * (1 + .04 * n[..., None])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def write(name, draw_fn):
    os.makedirs(OUT, exist_ok=True)
    base = paper()
    d = ImageDraw.Draw(base)
    draw_fn(d)
    for i in range(72):
        f = min(1, i / 10, (71 - i) / 10)
        im = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), base, max(f, 0))
        im.save(os.path.join(OUT, '%s_%02d.jpg' % (name, i)), quality=92)


def title(d):
    d.text((110, 230), 'PAE-02 · SCION 11 · Connelly Barnes', font=BIG, fill=FG)
    d.text((112, 330), 'Video Puppetry Tabletop — the threshold', font=MID, fill=DIM)
    d.text((112, 420), 'a home-movie dog, cut out and bent as a puppet', font=MONO, fill=DIM)


END = [
    'THE DOG is a real dog: frames 6, 38 and 0 of Amateur Film New Jersey C',
    '  (Home Movies, Internet Archive, public domain), cut out with their masks.',
    '  It is not drawn. Its body sheet is bent by moving-least-squares warps;',
    '  head-and-neck, tail and legs are rigid cut-outs of the same frames,',
    '  pinned at the joints; looking in, its head is the back of its own head.',
    'THE HAND is cut from The Door to Heaven (public domain), mirrored.',
    'THE PERSON\'S BODY, THE HOUSE, THE PORCH, THE DUSK: cut paper made in code.',
    'THE PERFORMANCE comes from the PAELEO score, frame for frame, not from',
    '  a live puppeteer. Voice and sounds are synthesized here.',
]


def end(d):
    d.text((110, 120), 'What it is made of', font=MID, fill=FG)
    for k, line in enumerate(END):
        d.text((112, 200 + k * 38), line, font=MONO, fill=FG if not line.startswith('  ') else DIM)


if __name__ == '__main__':
    write('title', title)
    write('end', end)
    print('cards ok')
