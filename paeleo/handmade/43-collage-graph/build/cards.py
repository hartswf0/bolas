"""title and end cards (3 s each): typeset on cut paper slips laid on the dusk"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache/cards'); os.makedirs(OUT, exist_ok=True)
F = os.path.join(HERE, 'cache/fonts')
W, H = 1280, 720


def bg():
    yy = np.linspace(0, 1, H)[:, None, None]
    c = np.array([16, 20, 40]) * (1 - yy) + np.array([60, 40, 52]) * yy
    return Image.fromarray(np.broadcast_to(c, (H, W, 3)).astype(np.uint8))


def slip(im, xy, lines, fonts, pad=18, tilt=0.0, fill=(226, 218, 198), ink=(36, 30, 28)):
    d0 = ImageDraw.Draw(im)
    ws = [d0.textlength(t, font=f) for t, f in zip(lines, fonts)]
    hs = [f.size * 1.25 for f in fonts]
    w, h = int(max(ws) + 2 * pad), int(sum(hs) + 2 * pad)
    s = Image.new('RGBA', (w, h), fill + (255,))
    d = ImageDraw.Draw(s)
    y = pad
    for t, f, hh in zip(lines, fonts, hs):
        d.text((pad, y), t, font=f, fill=ink); y += hh
    s = s.rotate(tilt, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', s.size, (0, 0, 0, 0)); sh.putalpha(s.getchannel('A').point(lambda v: v // 2))
    im.paste((0, 0, 0), (xy[0] + 6, xy[1] + 8), sh.filter(ImageFilter.GaussianBlur(4)).getchannel('A'))
    im.paste(s, xy, s)


def title():
    im = bg()
    disp = ImageFont.truetype(os.path.join(F, 'display.ttf'), 64)
    mono = ImageFont.truetype(os.path.join(F, 'mono.ttf'), 22)
    serif = ImageFont.truetype(os.path.join(F, 'serif.ttf'), 28)
    slip(im, (150, 220), ['PAE-02 · SCION 43 · Collage Graph Rewriting'], [disp], tilt=1.2)
    slip(im, (420, 380), ['The threshold, handmade'], [serif], tilt=-1.5)
    slip(im, (560, 470), ['one dog, cut from one home movie, rewritten'], [mono], tilt=0.6)
    im.save(os.path.join(OUT, 'title.jpg'), quality=94)


def end():
    import json
    tr = json.load(open(os.path.join(HERE, '../trace.json')))
    n = len(tr['invariants']['dog_fragments'])
    im = bg()
    mono = ImageFont.truetype(os.path.join(F, 'mono.ttf'), 17)
    serif = ImageFont.truetype(os.path.join(F, 'serif.ttf'), 26)
    slip(im, (70, 60), ['What it is made of'], [serif], tilt=-1)
    L = ['The dog: %d fragments cut from the 50 frames of one real dog (Amateur Film New Jersey C,' % n,
         'Home Movies, Internet Archive) - pieces from its shaded and its sunlit frames, two found turning frames;',
         'one piece (the back of its head) cut from its own fur to a shape drawn here.',
         'The person: the coat of the dog\'s own person in that film (also its sleeve and hair); a face from Anthracite:',
         'Pre-Shift Examinations (MSHA); a hand from The Door to Heaven (1941).',
         'The door: Straight Talk (NTIS, 1992). The room: a bulb from Light Of Your Life B.',
         'The voice you see: the sound arcs of We Learn About the Telephone I. The dusk: a cloud',
         'time-lapse (Top Of The Cloud). The house wall: the stone pillar in the home movie; the porch: its path.',
         'All public domain. Moved only by rewrite rules: replace, merge, split, enter.',
         'The sound is synthesized (voice, door, paws, scissors, crickets). The dog\'s choices follow',
         'the PAELEO score; its timing is measured from this render.']
    slip(im, (70, 150), L, [mono] * len(L), pad=22, tilt=0.4)
    im.save(os.path.join(OUT, 'end.jpg'), quality=94)


title(); end(); print('cards ok')
