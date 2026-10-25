"""proof/source_sheet.jpg: each source frame beside what was made from it (the bar: tracking from derived fragment to scan)."""
import os, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, '..', 'kit')
PL = os.path.join(HERE, 'cache', 'plates')
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, 'cache', 'fonts', n + '.ttf'), s)
W = 1600
sheet = Image.new('RGB', (W, 1500), (238, 229, 208)); d = ImageDraw.Draw(sheet)
d.text((40, 24), 'Source sheet — PAE-02 · SCION 50 · Historical Print Stage', font=F('Literata-Italic', 30), fill=(31, 25, 22))
d.text((40, 66), 'Left: the scan as it is in the kit (unaltered). Right: what was engraved from it. Rights: all public domain as recorded in the kit; no Library of Congress item used.', font=F('JetBrainsMono-Regular', 14), fill=(60, 50, 44))

def on_paper(png, scale=1.0):
    im = Image.open(png).convert('RGBA')
    r, g, b, a = im.split()
    ink = r.point(lambda v: 255 - v)
    base = Image.new('RGB', im.size, (238, 229, 208))
    inkc = Image.new('RGB', im.size, (31, 25, 22))
    out = Image.composite(inkc, base, r)
    if scale != 1: out = out.resize((int(out.width * scale), int(out.height * scale)), Image.LANCZOS)
    return out

rows = [
 ('Amateur Film New Jersey C, f006 (Home Movies, archive.org/details/NewJerseyC)', os.path.join(KIT, 'archive-dog', 'frames', 'f006.jpg'), (81, 61, 273, 209),
  [os.path.join(PL, 'dogL_%s.png' % n) for n in ['torso', 'head', 'tail', 'fore_near_up', 'fore_near_lo', 'hind_near_up', 'hind_near_lo', 'head_rear']],
  'traced into 11 cut pieces (8 shown) + the drawn back of the head (designed analog, last)'),
 ('same film, f026-f044 (the dog\'s own turn), masked', os.path.join(KIT, 'archive-dog', 'frames', 'f028.jpg'), None,
  [os.path.join(PL, 'turn_f%03d.png' % f) for f in [26, 33, 40, 44]], 'whole frames, engraved, shape unaltered, re-timed'),
 ('Straight Talk (NTIS 1992), f030 · archive.org/details/gov.ntis.ava19144vnb1', os.path.join(KIT, 'archive-door', 'frames', 'f030.jpg'), (116, 0, 234, 272),
  [os.path.join(PL, 'door_leaf.png')], 'the door leaf'),
 ('The Door to Heaven (1941), f000 · archive.org/details/DoortoHe1941', os.path.join(ROOT, 'sources', 'hand-door-to-heaven', 'f000.jpg'), None,
  [os.path.join(PL, 'person_hand.png')], 'the hand only; the card lettered SORROW it holds is cropped away'),
]
y = 110
for title, src, box, outs, note in rows:
    im = Image.open(src).convert('RGB')
    th = im.resize((384, 288))
    sheet.paste(th, (40, y))
    if box:
        dd = ImageDraw.Draw(sheet); dd.rectangle([40 + box[0], y + box[1], 40 + box[2], y + box[3]], outline=(168, 38, 30), width=2)
    d.text((40, y + 292), title, font=F('JetBrainsMono-Regular', 12), fill=(60, 50, 44))
    x = 460
    for o in outs:
        p = on_paper(o, 1.0 if 'door_leaf' not in o else 0.7)
        if p.height > 300: p = p.resize((int(p.width * 300 / p.height), 300))
        sheet.paste(p, (x, y)); x += p.width + 16
    d.text((640, y + 308), note, font=F('Literata-Italic', 15), fill=(80, 66, 56))
    y += 340
os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)
sheet.save(os.path.join(ROOT, 'proof', 'source_sheet.jpg'), quality=90)
print('source sheet ok')
