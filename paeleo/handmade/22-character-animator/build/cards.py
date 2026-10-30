"""SCION 22 · title and end cards (3 s each) on the same digital felt."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import CACHE, REPO
from felt import Layer, fibre
F = os.path.join(REPO, 'tools/paeleo/fonts')
big = ImageFont.truetype(os.path.join(F, 'f5.woff2'), 64)
mid = ImageFont.truetype(os.path.join(F, 'f2.woff2'), 34)
mono = ImageFont.truetype(os.path.join(F, 'f14.woff2'), 19)


def board():
    fib = np.tile(fibre(1.0), (1, 2))[:720, :1280]
    base = np.array([34, 30, 52], np.float32) / 255
    return (base[None, None] * fib[..., None]).clip(0, 1)


def card(lines, path):
    img = Image.fromarray((board() * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    y = 0
    for font, text, col in lines:
        y += font.size * 0.45
    y = (720 - sum(f.size * 1.45 for f, _, _ in lines)) / 2
    for font, text, col in lines:
        w = d.textlength(text, font=font)
        d.text(((1280 - w) / 2, y), text, font=font, fill=col)
        y += font.size * 1.45
    img.save(path, quality=94)


card([(big, 'PAE-02 · SCION 22 · Character Animator', (240, 224, 186)),
      (mid, 'live performance capture, without a camera', (214, 170, 120)),
      (mono, 'a layered felt puppet driven by takes · the threshold, 32 s', (190, 186, 200))], os.path.join(CACHE, 'title.jpg'))
card([(mid, 'What it is made of', (240, 224, 186)),
      (mono, 'Two layered puppets cut from digital felt drawn here (named groups, swap sets for views and visemes).', (220, 214, 226)),
      (mono, 'A small runtime written here plays them: triggers, head & body turner, eye gaze, auto blink,', (220, 214, 226)),
      (mono, 'breathe, dangle (ears, tail, ponytail), walk with planted feet, limb IK, lip sync.', (220, 214, 226)),
      (mono, 'The dog is driven by recorded takes (timed control tracks) built from the PAELEO score.', (220, 214, 226)),
      (mono, 'No camera, no webcam landmarks, no live performer exist here. The voice is synthesized;', (240, 200, 150)),
      (mono, 'the mouth is driven by visemes computed from that audio. All sound synthesized.', (240, 200, 150)),
      (mono, 'SCION 22 · PAELEO · 2026', (160, 156, 176))], os.path.join(CACHE, 'endcard.jpg'))
print('cards')
