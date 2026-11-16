"""Editor repair E2: title type and end-card overlay with the fiction label, the hommage line (Roubaud named as
the novel's author, not the film's), the film's licence (CC BY-SA 4.0, required by the BY-SA sounds) and the
typeface credits.  Typeface: Hortense Slab, handmade for this film (editor/typeface.py), CC BY-SA 4.0 with the film.
Repair round 2: the title is a stacked slab block, author black above the title red, as on a paperback cover.

    python3 -I films/swarm/la-belle-hortense/editor/cards.py
Writes films/sources/la-belle-hortense/editor/print/{title_type_E2,endcard_text_E2}.png and prints cap heights.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/print')
os.makedirs(OUT, exist_ok=True)
BOLD = '/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf'
REG = '/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Regular.ttf'
W, H = 960, 540
BLACK = (1, 2, 1); RED_T = (165, 9, 23); CREAM = (225, 229, 178)


def F(sz, path=BOLD):
    return ImageFont.truetype(path, sz)


def cap_height(sz, path=BOLD):
    m = F(sz, path).getmask('F'); return m.getbbox()[3] - m.getbbox()[1]


def line(d, xy, s, sz, fg, band=None, path=BOLD, pad=(6, 3)):
    f = F(sz, path)
    x0, y0, x1, y1 = d.textbbox(xy, s, font=f)
    if band is not None:
        d.rectangle((x0 - pad[0], y0 - pad[1], x1 + pad[0], y1 + pad[1]), fill=band + (235,))
    d.text(xy, s, font=f, fill=fg + (255,))
    return y1


FICTION = ["Fiction. Photographies (FSA/OWI 1941–43, C. M. Highsmith, D. Jolivet, enveloppe 1861)",
           "mises en scène ; les personnes représentées n'ont aucun lien avec cette histoire."]


def title():
    """stacked slab block: author in black on two lines, the title in red beneath it (cover order), then the
    sextine lines and the fiction label on typed bands."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pad)
    pd.rectangle((40, 40, 520, 318), fill=CREAM + (222,))          # a typed paper block behind the stack
    img.alpha_composite(pad)
    line(d, (58, 48), 'Jacques', 64, BLACK)
    line(d, (58, 116), 'Roubaud', 64, BLACK)
    line(d, (58, 196), 'La belle', 50, RED_T)
    line(d, (58, 250), 'Hortense', 50, RED_T)
    line(d, (560, 60), 'exercice sur une sextine,', 18, BLACK, CREAM)
    line(d, (560, 88), 'en hommage au roman (1985)', 18, BLACK, CREAM)
    line(d, (560, 122), 'six modules · [6,1,5,2,4,3]', 18, BLACK, CREAM)
    for j, s in enumerate(FICTION):
        line(d, (44, 466 + j * 28), s, 17, CREAM, BLACK)
    return img


CREDITS = [
    "Photographies : Jack Delano, FSA/OWI (Library of Congress, domaine public) ; Daniel Jolivet, Bourré",
    "(CC BY 2.0) ; Carol M. Highsmith (LoC, domaine public) ; Reinhard Dietrich (dom. public) ; clé (CC0){env}.",
    "Sons : Olga Ernst (CC BY-SA 4.0) ; Pwaivers (CC BY-SA 3.0) ; stephan, MKFI (domaine public) ;",
    "Gravity Sound (CC BY 4.0) ; SpaceJoe (CC0).  Caractères : Hortense Slab, dessinés à la main pour ce film (CC BY-SA 4.0).",
    "Hommage au roman de Jacques Roubaud ; rien n'est repris du roman ni de sa couverture.",
    "Enveloppe de 1861 (LoC, domaine public).  Ce film est publié sous licence CC BY-SA 4.0 (creativecommons.org/licenses/by-sa/4.0).",
]


def endcard_text(env=''):
    """overlay for the end card from 60.5 s: cream panel over U4's credit lines, fiction label (>= 10 px caps),
    credits."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 404, W, H), fill=CREAM + (255,))
    for j, s in enumerate(FICTION):
        line(d, (40, 408 + j * 21), s, 17, BLACK)
    for j, s in enumerate(CREDITS):
        d.text((40, 454 + j * 13.4), s.format(env=env), font=F(11, REG), fill=BLACK + (255,))
    return img


if __name__ == '__main__':
    import sys
    env = sys.argv[1] if len(sys.argv) > 1 else ''
    title().save(os.path.join(OUT, 'title_type_E2.png'))
    endcard_text(env).save(os.path.join(OUT, 'endcard_text_E2.png'))
    print('cap height: title fiction 18 px ->', cap_height(18), 'px; end card fiction 17 px ->', cap_height(17), 'px;',
          'credits 11 px ->', cap_height(11, REG), 'px')
