"""Title and end cards: type set on cream card, laid on the dark table and shot like everything else (grain per frame).
Writes cache/frames/t%03d.jpg (72) and e%03d.jpg (72)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
FD = os.path.join(ROOT, 'tools/paeleo/fonts')
OUT = os.path.join(HERE, 'cache', 'frames')
W, H = 1280, 720
def BIG(s):
    f = ImageFont.truetype(os.path.join(FD, 'f8.woff2'), s)
    f.set_variation_by_axes([800])   # a variable font: set its weight
    return f


def _w(f, w):
    try:
        f.set_variation_by_axes([w])
    except Exception:
        pass
    return f
SERIF = lambda s: _w(ImageFont.truetype(os.path.join(FD, 'f34.woff2'), s), 400)
SERIF_I = lambda s: _w(ImageFont.truetype(os.path.join(FD, 'f27.woff2'), s), 500)
MONO = lambda s: _w(ImageFont.truetype(os.path.join(FD, 'f14.woff2'), s), 400)


def table_and_card(box, seed):
    r = np.random.default_rng(seed)
    bg = np.ones((H, W, 3), np.float32) * np.array([.08, .07, .09]) * (1 + r.normal(0, .02, (H, W, 1)))
    img = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    x0, y0, x1, y1 = box
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle((x0 + 6, y0 + 8, x1 + 6, y1 + 8), fill=150)
    img.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 0)] * 3 + [sh.filter(ImageFilter.GaussianBlur(6))]))
    cw, ch = x1 - x0, y1 - y0
    low = np.asarray(Image.fromarray((r.random((ch // 10 + 2, cw // 10 + 2)) * 255).astype(np.uint8)).resize((cw, ch), Image.BICUBIC)).astype(np.float32) / 255
    card = np.array([.91, .87, .78]) * (1 + (low[..., None] - .5) * .06 + r.normal(0, .01, (ch, cw, 1)))
    img.alpha_composite(Image.fromarray((np.clip(card, 0, 1) * 255).astype(np.uint8)).convert('RGBA'), (x0, y0))
    return img


def shoot(img, prefix, n=72):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    for f in range(n):
        g = np.random.default_rng(50000 + f + (0 if prefix == 't' else 999)).normal(0, .02, (H // 2, W // 2)).astype(np.float32)
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)
        fade = min(1, (f + 1) / 8, (n - f) / 8)
        fr = np.clip((a + g[..., None] * (.5 + .5 * a)) * fade, 0, 1)
        Image.fromarray((fr * 255).astype(np.uint8)).save(os.path.join(OUT, '%s%03d.jpg' % (prefix, f)), quality=90)


def title():
    img = table_and_card((190, 170, 1090, 550), 1)
    d = ImageDraw.Draw(img)
    ink = (40, 28, 26)
    d.text((640, 250), 'PAE-02 · SCION 52 · Gilliam Ephemera', font=BIG(58), fill=ink, anchor='mm')
    d.line((330, 300, 950, 300), fill=(150, 40, 36), width=3)
    d.text((640, 352), 'The threshold, handmade', font=SERIF_I(38), fill=ink, anchor='mm')
    d.text((640, 420), 'a reconstruction of a cut-out method, from public-domain prints', font=SERIF(24), fill=(70, 56, 50), anchor='mm')
    d.text((640, 500), 'pin · slide · swivel · flop · substitute · hold · expose', font=MONO(18), fill=(110, 90, 80), anchor='mm')
    return img


END = [
    ('The dog', 'one frame of a home movie dog (Amateur Film New Jersey C, Internet Archive, public domain), printed, cut into seven '
                'pieces and pinned at neck, shoulders, hips and tail. Two more frames of the same dog give the turning card, '
                'the face it looks back with, and its lowered head. There is no print of the back of its head: that card is cut '
                'from its own fur.'),
    ('The people and things', 'a face in a hat (Vision of the Wild), a smock, jeans and a door swinging (Straight Talk), a forearm '
                'that held a card (Door to Heaven), and the same forearm enlarged, a lamp (Light Of Your Life B), trees (Behind the Lens), a cloud (Top Of The '
                'Cloud), the stone of the dog\'s own house. All public domain.'),
    ('Made here', 'airbrushed sky, painted wall and boards, a crate, shoes, the moon, black paper behind the jaw. The voice is '
                  'flite speech synthesis; every other sound is synthesized.'),
    ('How', 'cards laid on a digital rostrum, moved only by pins and slides, turned over or swapped for another card, shot on '
            'twos and held. No paper was cut by hand: the method is reconstructed, not the archive.'),
]


def endcard():
    img = table_and_card((110, 70, 1170, 650), 2)
    d = ImageDraw.Draw(img)
    ink = (40, 28, 26)
    d.text((150, 104), 'What it is made of', font=BIG(42), fill=ink)
    y = 162
    for head, body in END:
        d.text((150, y), head, font=SERIF_I(23), fill=(140, 40, 34))
        y += 32
        words, line = body.split(), ''
        for w in words:
            if d.textlength(line + ' ' + w, font=SERIF(18)) > 980:
                d.text((150, y), line.strip(), font=SERIF(18), fill=ink); y += 24; line = ''
            line += ' ' + w
        d.text((150, y), line.strip(), font=SERIF(18), fill=ink); y += 32
    d.text((150, 610), 'Quick, Draw! was not used. Sources and rights: assets.json', font=MONO(14), fill=(110, 90, 80))
    return img


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    shoot(title(), 't')
    shoot(endcard(), 'e')
