"""SCION 03 Ernst · the title page and the colophon (what the film is made of), set like a book's pages."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import burin

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
W, H = 1280, 720
INK = tuple(int(c * 255) for c in burin.INK)
PAP = tuple(int(c * 255) for c in burin.PAPER)


def font(name, size):
    return ImageFont.truetype(os.path.join(CACHE, name + '.ttf'), size)


def centred(d, y, txt, f, fill=INK):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=fill)


def vignette(img, name, cx, cy, scale):
    f = np.load(os.path.join(CACHE, 'frag_%s.npz' % name))
    cov, m = f['cov'], f['mask']
    h, w = cov.shape
    im = Image.fromarray((np.clip(cov, 0, 1) * 255).astype(np.uint8)).resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    mk = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)
    a = np.asarray(img, float) / 255
    c = np.asarray(im, float) / 255; mm = np.asarray(mk, float) / 255
    x0, y0 = int(cx - im.width / 2), int(cy - im.height / 2)
    sub = a[y0:y0 + im.height, x0:x0 + im.width]
    frag = np.array(burin.PAPER) * (1 - c[..., None]) + np.array(burin.INK) * c[..., None]
    sub[:] = sub * (1 - mm[..., None]) + frag * mm[..., None]
    return Image.fromarray((a * 255).astype(np.uint8))


def rule(d, y, w=360):
    d.line(((W - w) / 2, y, (W + w) / 2, y), fill=INK, width=1)


def title():
    img = Image.new('RGB', (W, H), PAP)
    img = vignette(img, 'lion_mask', W / 2, 250, 1.25)
    d = ImageDraw.Draw(img)
    centred(d, 62, 'PAE-02 · SCION 03 · Max Ernst', font('literata_sb', 40))
    centred(d, 112, 'Surreal Collage Grammar', font('literata_it', 26))
    rule(d, 372)
    centred(d, 392, 'The threshold, handmade', font('literata', 34))
    centred(d, 446, 'a collage-novel in one plate', font('literata_it', 22))
    rule(d, 490, 120)
    centred(d, 600, 'cohort 2  ·  32 seconds, after the PAELEO threshold score', font('literata_it', 18))
    img.save(os.path.join(CACHE, 'card_title.png'))


END = [
    ('The dog', 'a maquette of round cones and ellipsoids, engraved by this swarm’s own burin;'),
    ('', 'no picture of a dog is used. A step solver sets its paws; its choices are the PAELEO score.'),
    ('', 'Round its neck, the lion\u2019s mane: pasted on at the first call, its seam closing as it lies across the sill.'),
    ('The plate', 'porch, facade, door, chair, fence and dusk built as regions, each cut with its own engraved line.'),
    ('Found fragments', 'cut from public-domain films and re-engraved:'),
    ('', 'a lion, Andy’s Animal Alphabet (the magistrate’s head, the keystone, the dog’s mane);'),
    ('', 'a hand, The Door to Heaven (reaching, then offered low);'),
    ('', 'a miner’s lamp, Anthracite: Pre-Shift Examinations of Underground Mines (the light inside).'),
    ('Sound', 'every sound synthesized: formant voices, a lion’s growl under the calls, paper, stone, hinge, boards.'),
]


def colophon():
    img = Image.new('RGB', (W, H), PAP)
    d = ImageDraw.Draw(img)
    centred(d, 70, 'What this plate is made of', font('literata_sb', 32))
    rule(d, 124, 200)
    y = 168
    fa = font('literata_sb', 19); fb = font('literata', 19)
    for a, b in END:
        if a:
            y += 12
            d.text((150, y), a, font=fa, fill=INK)
        d.text((330, y), b, font=fb, fill=INK)
        y += 32
    rule(d, y + 24, 200)
    centred(d, y + 44, 'Rights: public domain (Internet Archive) for the found frames; Literata (SIL OFL) for the type; everything else made here.', font('literata_it', 17))
    centred(d, 640, 'PAE-02 · SCION 03 · Max Ernst · Surreal Collage Grammar', font('literata_it', 16))
    img.save(os.path.join(CACHE, 'card_end.png'))


if __name__ == '__main__':
    title(); colophon(); print('cards ok')
