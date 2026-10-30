"""Title and end cards (3 s each, 72 frames). The end card shows the layer stack and the mask keys honestly."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
W, H = 1280, 720


def font(f, size):
    return ImageFont.truetype(os.path.join(FONTS, f), size)


BIG = 'f8.woff2'; MONO = 'f14.woff2'; SERIF = 'f20.woff2'


def _fade(base, n=72):
    out = []
    for k in range(n):
        a = min(1, k / 10, (n - 1 - k) / 10)
        out.append((np.asarray(base, np.float32) * a).astype(np.uint8))
    return out


def title_frames():
    im = Image.new('RGB', (W, H), (10, 11, 16)); d = ImageDraw.Draw(im)
    d.text((96, 250), 'PAE-02 · SCION 28', font=font(BIG, 64), fill=(226, 200, 150))
    d.text((96, 330), 'After Effects — Mask and Performance Plate Foundry', font=font(BIG, 46), fill=(235, 235, 240))
    d.text((96, 410), 'the threshold, composited from public-domain archive plates', font=font(MONO, 22), fill=(150, 160, 180))
    return _fade(im)


END = [
    ('LAYER STACK (back to front)', None),
    ('dusk sky', 'computed gradient'),
    ('room: far wall, side wall, floor', 'Straight Talk (NTIS 1992) f031, corner-pinned, lamp grade'),
    ('door leaf', 'Straight Talk f031, SAM mask, corner pin 24 -> 98 deg at 6.2 s'),
    ('person (one body, all stages)', 'Straight Talk f000, roto 24 v; torso + legs on a hip pivot'),
    ('facade (doorway = holdout)', 'Amateur Film New Jersey C: tracked median -> stone blocks'),
    ('casing, sill, porch flags', 'Straight Talk floor + New Jersey C path, corner pins'),
    ('door light pass', 'computed from lamp through aperture; floor, dog, person'),
    ('arm and low hand', 'Door to Heaven (1941) f010, luma key x bezier, on the shoulder'),
    ('DOG: 8 layers parented to a root track', 'New Jersey C f010 body, 3 legs (+1 dup), head; f019 tail;'),
    ('', 'f038 head (looks back); f000 back of head (looks in)'),
    ('dog holdout', 'facade + sill mattes where the dog is past the threshold'),
    ('MASK KEYS', None),
    ('12 SAM-derived bezier mattes + 8 part masks', 'feather 1.2–2.5 px, expand -3..0; static per plate'),
    ('belly mask: 2 keys (standing -> lying)', 'keyed to the score lie value, every frame'),
    ('dog light match', 'ambient set from the measured dusk band behind it; contact shadow'),
    ('transforms: root track = score x', 'legs foot-locked; turns: f013 f030 f032 f036 / f038 f037 f013'),
    ('NO DRAWN PICTURES, NO 3-D MODEL: plates, masks, keys, pins', None),
]


def end_frames():
    im = Image.new('RGB', (W, H), (10, 11, 16)); d = ImageDraw.Draw(im)
    d.text((64, 36), 'What it is made of', font=font(BIG, 44), fill=(226, 200, 150))
    y = 104; fm = font(MONO, 16); fh = font(MONO, 18)
    for a, b in END:
        if b is None:
            d.text((64, y + 6), a, font=fh, fill=(226, 200, 150)); y += 34; continue
        d.text((64, y), a, font=fm, fill=(230, 230, 236))
        d.text((520, y), b, font=fm, fill=(150, 160, 180)); y += 27
    d.text((64, H - 44), 'all sources public domain (Internet Archive / NTIS via movingimagearchive.com); see assets.json',
           font=font(MONO, 15), fill=(120, 128, 145))
    return _fade(im)
