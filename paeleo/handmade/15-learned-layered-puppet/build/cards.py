"""Title card and end card (1280x720 JPEGs, 72 frames each) -> cache/cards/."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, '../../../../tools/paeleo/fonts'))
OUT = os.path.join(HERE, 'cache', 'cards'); os.makedirs(OUT, exist_ok=True)
BIG = lambda s: ImageFont.truetype(os.path.join(FONTS, 'f5.woff2'), s)
MONO = lambda s: ImageFont.truetype(os.path.join(FONTS, 'f14.woff2'), s)
BG = (14, 15, 22); FG = (232, 222, 206); DIM = (150, 146, 150); WARM = (236, 170, 100)


def title():
    im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
    d.text((110, 250), 'PAE-02 · SCION 15 · Learned Layered Puppet', font=BIG(58), fill=FG)
    d.text((112, 335), 'the threshold, handmade: a dog learned from 50 frames of a 1940s home movie', font=MONO(20), fill=DIM)
    d.text((112, 368), 'and asked to do what the film never showed it doing', font=MONO(20), fill=DIM)
    return im


def end(strip):
    im = Image.new('RGB', (1280, 720), BG); d = ImageDraw.Draw(im)
    d.text((80, 50), 'What it is made of', font=BIG(44), fill=FG)
    lines = [
        'THE DOG  a layered puppet (11 layers) cut from one frame of Amateur Film New Jersey C (Internet Archive, public domain),',
        '         fitted by render-loss optimisation to all 50 frames; what it looks like from each view (texture, head, leg and tail',
        '         shape) is learned from those fits. The score drives its joints; the learned model renders every pose.',
        'CORRECTED BY HAND (listed in assets.json)  turns cut past the front view, far legs hidden; lying: legs tucked under,',
        '         paw pad; looking back over the shoulder; the back of the head for looking in; the neck dropped for the',
        '         head-low walk. Below: the model alone (top) and the film (bottom) at four of those poses.',
        'THE PLACE AND THE PERSON  drawn and computed (numpy/PIL); voices: flite speech synthesis; all sound synthesized.',
    ]
    y = 118
    for l in lines:
        d.text((80, y), l, font=MONO(15), fill=DIM if not l.startswith(('THE', 'CORR')) else FG); y += 26
    if strip is not None:
        im.paste(strip, ((1280 - strip.width) // 2, 300))
    d.text((80, 688), 'SCION 15 after Poursaeed et al., Neural Puppet (2019) - an interpretation, not an endorsement', font=MONO(13), fill=DIM)
    return im


if __name__ == '__main__':
    t = title()
    sp = os.path.join(HERE, '..', 'proof', 'raw_vs_corrected_strip.jpg')
    strip = Image.open(sp).convert('RGB') if os.path.exists(sp) else None
    if strip is not None and strip.width > 1000:
        strip = strip.resize((1000, int(strip.height * 1000 / strip.width)))
    e = end(strip)
    for k in range(72):
        f = min(1, k / 10, (71 - k) / 10)
        Image.fromarray((np.asarray(t, np.float32) * f + np.array(BG) * (1 - f)).astype(np.uint8)).save(os.path.join(OUT, 't%03d.jpg' % k), quality=92)
        f = min(1, k / 10, (71 - k) / 14)
        Image.fromarray((np.asarray(e, np.float32) * f + np.array(BG) * (1 - f)).astype(np.uint8)).save(os.path.join(OUT, 'e%03d.jpg' % k), quality=92)
    t.save(os.path.join(HERE, '..', 'proof', 'card_title.jpg'), quality=85); e.save(os.path.join(HERE, '..', 'proof', 'card_end.jpg'), quality=85)
