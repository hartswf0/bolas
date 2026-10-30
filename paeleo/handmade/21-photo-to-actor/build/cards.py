"""Title card and end card (1280x720), set in the house fonts (woff2 -> ttf via fontTools), same grain as the scene."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
CACHE = os.path.join(FOLDER, 'build', 'cache')
FONTS = os.path.join(ROOT, 'tools', 'paeleo', 'fonts')


def ttf(name):
    out = os.path.join(CACHE, name + '.ttf')
    if not os.path.exists(out):
        from fontTools.ttLib import TTFont
        f = TTFont(os.path.join(FONTS, name + '.woff2')); f.flavor = None; f.save(out)
    return out


BIG = ttf('f5'); MONO = ttf('f14')
W, H = 1280, 720
rng = np.random.default_rng(7)


def grain(img):
    a = np.array(img).astype(float)
    n = rng.normal(0, 1, (H // 2, W // 2))
    n = np.array(Image.fromarray(np.clip(128 + 40 * n, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(float) - 128
    a += n[:, :, None] * 0.085
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def card(lines, path):
    im = Image.new('RGB', (W, H), (14, 15, 22)); d = ImageDraw.Draw(im)
    y = lines[0][0]
    for (yy, txt, font, size, col) in lines:
        f = ImageFont.truetype(font, size)
        if font == BIG:
            try: f.set_variation_by_axes([780])
            except Exception: pass
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, yy), txt, font=f, fill=col)
    grain(im).save(path, quality=95)


card([(250, 'PAE-02 · SCION 21', BIG, 46, (226, 190, 130)),
      (318, 'CARTOON ANIMATOR — PHOTO-TO-ACTOR FACTORY', BIG, 58, (236, 232, 222)),
      (420, 'the threshold · a photographed dog, rigged from stills, performs a score it never performed', MONO, 18, (160, 168, 190))],
     os.path.join(CACHE, 'title.jpg'))
card([(150, 'WHAT IT IS MADE OF', BIG, 40, (226, 190, 130)),
      (225, 'The dog: six frames of one real dog, Amateur Film New Jersey C (Home Movies, Internet Archive, public domain),', MONO, 16, (225, 222, 214)),
      (250, 'cut with SAM masks into photo-textured parts on a body template. Angle artwork: front, 3/4, profile, lowered heads,', MONO, 16, (225, 222, 214)),
      (275, 'back-of-head view (f000 fur, hand-cut ears), body back view; auto landmark fit failed on 3 of 5, corrected.', MONO, 16, (225, 222, 214)),
      (300, 'The source footage shows it walking to a bowl. Backing away, refusing, lying across a sill and looking in', MONO, 16, (225, 222, 214)),
      (325, 'are retargeted from the PAELEO score: the photographs never did them.', MONO, 16, (225, 222, 214)),
      (370, 'Person, door leaf, lit hall: Straight Talk (NTIS, public domain). Sky: Top of the Cloud (public domain).', MONO, 16, (190, 196, 214)),
      (395, 'House, porch, railing, light: computed, grain-matched. Voices: flite synthesis. No likeness beyond public-domain film.', MONO, 16, (190, 196, 214)),
      (470, 'PAE-02 · SCION 21 · threshold score 32 s at 24 fps', MONO, 15, (140, 146, 170))],
     os.path.join(CACHE, 'endcard.jpg'))
print('cards ok')
