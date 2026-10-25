"""SCION 45 · Title and end cards (3 s each), set in the house fonts. -> build/cache/card_title.png, card_end.png"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.abspath(os.path.join(HERE, '../../../../tools/paeleo/fonts'))
W, H = 1280, 720
BG = (16, 17, 27)
INK = (226, 218, 204)
WARM = (240, 178, 104)
DIM = (150, 150, 165)


WEIGHT = {'f2.woff2': 600, 'f5.woff2': 800, 'f8.woff2': 900, 'f14.woff2': 400, 'f20.woff2': 600, 'f27.woff2': 400, 'f34.woff2': 400, 'f41.woff2': 600}


def font(f, size):
    fn = ImageFont.truetype(os.path.join(FONTS, f), size)
    try:
        fn.set_variation_by_axes([WEIGHT[f]])     # the woff2 files are variable fonts; pick the weight local.css names
    except Exception:
        pass
    return fn


def wrap(d, text, fnt, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fnt) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def title():
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.text((110, 220), 'PAE-02 · SCION 45 · Occlusion Compositing', font=font('f5.woff2', 64), fill=INK)
    d.text((110, 310), 'The threshold: who is in front of the door frame?', font=font('f27.woff2', 34), fill=WARM)
    d.text((110, 560), 'a real dog from an amateur home movie, cut into layers and composited at a door', font=font('f14.woff2', 20), fill=DIM)
    # a small occlusion diagram: the jamb in front of half a bar
    d.rectangle([1030, 500, 1170, 530], fill=(120, 110, 100)); d.rectangle([1090, 420, 1108, 570], fill=(200, 200, 205))
    d.rectangle([1108, 500, 1170, 530], fill=(150, 140, 128))
    im.save(os.path.join(HERE, 'cache/card_title.png'))


def end():
    global N_CELS
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.text((90, 70), 'What it is made of', font=font('f5.woff2', 48), fill=INK)
    body = [
        ('The dog', 'every pixel of it is from Amateur Film New Jersey C (Home Movies, Internet Archive, public domain): %d real '
                    'frames cut by their SAM mattes,' % N_CELS + ' some split into head, torso and legs and re-assembled to lie down. Re-lit, never drawn.'),
        ('Found', 'the hallway and the door panel: Straight Talk (NTIS). The bulb: Light Of Your Life B. The hand: Door to Heaven '
                  '(1941). The sky: Top Of The Cloud. All public domain.'),
        ('Drawn here', 'the house, the porch, the bench and the person, who is only a matte: a shape of dark against the light.'),
        ('Heard', 'a synthesized voice (flite), synthesized foley and dusk; the room is heard through the door, held out until it opens.'),
        ('How', 'RGBA layers ordered by an occlusion graph in every frame; where the dog lies across the threshold it is split by its '
                'own depth pass, behind the jamb and in front of it.'),
    ]
    y = 160
    fb = font('f41.woff2', 23); fr = font('f34.woff2', 23)
    for k, v in body:
        d.text((90, y), k, font=fb, fill=WARM)
        for line in wrap(d, v, fr, 900):
            d.text((280, y), line, font=fr, fill=INK); y += 32
        y += 16
    d.text((90, 660), 'Bolas · PAELEO · PAE-02 handmade cohort 3 · SCION 45', font=font('f14.woff2', 18), fill=DIM)
    im.save(os.path.join(HERE, 'cache/card_end.png'))


N_CELS = 0

if __name__ == '__main__':
    import json
    p = os.path.join(HERE, 'cache/cels_used.json')
    N_CELS = len(json.load(open(p))) if os.path.exists(p) else 0
    title(); end(); print('cards ok')
