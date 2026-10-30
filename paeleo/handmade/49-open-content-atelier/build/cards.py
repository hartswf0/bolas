"""Title and end cards (3 s each, 72 frames) set like museum object labels. Writes build/cache/cards/{title,end}_%04d.jpg."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'cache', 'cards'); os.makedirs(OUT, exist_ok=True)
BIG = 'f8.woff2'; MONO = 'f14.woff2'; SERIF = 'f34.woff2'; SERIF_I = 'f27.woff2'
FONTS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
def F(name, size):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    try:
        ax = f.get_variation_axes()
        if ax and name == BIG: f.set_variation_by_axes([800])
    except Exception: pass
    return f
PAPER = (236, 229, 214); INK = (34, 30, 28); RULE = (150, 120, 90)


def card(lines):
    im = Image.new('RGB', (1280, 720), PAPER); d = ImageDraw.Draw(im)
    d.rectangle((60, 60, 1220, 660), outline=RULE, width=2)
    for x, y, txt, font, col in lines: d.text((x, y), txt, font=font, fill=col)
    return im


title = card([
    (110, 150, 'PAE-02 · SCION 49', F(BIG, 54), INK),
    (110, 220, 'Getty & Smithsonian — Open-Content Atelier', F(BIG, 64), INK),
    (110, 330, 'The threshold, cut from open-access museum objects.', F(SERIF_I, 34), INK),
    (110, 400, 'A dog at a door that may refuse. Every picture in it is a cut from a Smithsonian', F(SERIF, 26), INK),
    (110, 436, 'American Art Museum image released CC0 through Smithsonian Open Access.', F(SERIF, 26), INK),
    (110, 560, 'Object numbers, licence and crop of every piece: assets.json', F(MONO, 20), RULE),
])
end = card([
    (100, 90, 'Made of', F(BIG, 44), INK),
    (100, 150, 'The dog: one pointer, from Currier & Ives, Woodcock Shooting (SAAM 1973.122.4),', F(SERIF, 23), INK),
    (120, 182, 'cut into head, torso, tail, foreleg, thigh and shank, and hinged to walk, turn, lie,', F(SERIF, 21), INK),
    (120, 210, 'look back and rest; the back of its head is its own ear, twice, on a crown of its own fur.', F(SERIF, 21), INK),
    (100, 280, 'The person: Auguste Edouart, cut-paper silhouettes, Father, Mother, and Boy (1981.172.33);', F(SERIF, 23), INK),
    (120, 310, 'the reaching arm from Boy with Dog (1981.172.31).', F(SERIF, 23), INK),
    (100, 350, 'The door: José Dolores López, Screen Door (1989.30.3). The room and floor: E. F. Andrews,', F(SERIF, 23), INK),
    (120, 380, 'Interior of a House (1916.6.39). The dusk: N. MacGilvary, Twilight after the Rain (1913.3.3).', F(SERIF, 23), INK),
    (100, 430, 'All Smithsonian American Art Museum, CC0 (Smithsonian Open Access). No line is drawn;', F(SERIF, 23), INK),
    (100, 460, 'only the light is computed. Getty Open Content could not be reached from this studio: none used.', F(SERIF, 23), INK),
    (100, 500, 'Voices: flite speech synthesis. Every other sound synthesized.', F(SERIF, 23), INK),
    (100, 590, 'PAE-02 · SCION 49 · built bottom-up from the PAELEO threshold score', F(MONO, 18), RULE),
])
for k in range(72):
    title.save(os.path.join(OUT, f'title_{k:04d}.jpg'), quality=92); end.save(os.path.join(OUT, f'end_{k:04d}.jpg'), quality=92)
print('cards ok')
