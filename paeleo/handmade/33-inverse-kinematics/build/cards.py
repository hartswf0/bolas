"""Title and end cards (3 s each, 72 frames) -> build/cache/title.png, build/cache/end.png."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
FD = os.path.join(REPO, 'tools/paeleo/fonts')
W, H = 1280, 720
BG = (18, 20, 34); INK = (226, 214, 196); DIM = (150, 146, 160); WARM = (236, 178, 112)
big = ImageFont.truetype(os.path.join(FD, 'f8.woff2'), 64)
mid = ImageFont.truetype(os.path.join(FD, 'f2.woff2'), 34)
lit = ImageFont.truetype(os.path.join(FD, 'f27.woff2'), 25)
mono = ImageFont.truetype(os.path.join(FD, 'f14.woff2'), 17)

im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
d.text((110, 250), 'PAE-02 · SCION 33 · Inverse Kinematics', font=big, fill=INK)
d.text((112, 335), 'Contact and Reach — the threshold, handmade', font=mid, fill=WARM)
d.text((112, 400), 'A dog at a doorway at dusk. It may refuse.', font=lit, fill=DIM)
im.save(os.path.join(HERE, 'cache/title.png'))

im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
d.text((110, 110), 'What this is made of', font=mid, fill=WARM)
lines = [
    'The dog and the person are bone chains: tapered capsules on joints, solved every frame',
    'by two-bone inverse kinematics with pole vectors (elbows back, stifles forward) and joint limits.',
    'Each paw is placed by a footfall planner that locks it to the boards until the body has carried',
    'its home away; a locked paw never moves. Heads aim at world-space targets: the person, the boards,',
    'the low hand, the lit room. The door is simulated: held, released, pushed against static friction.',
    'The light is cast through the opening each frame; the bodies cut their shadows out of it.',
    'Proportions studied from the rig keys of a home-movie dog (Amateur Film New Jersey C, Internet',
    'Archive, public domain). No footage, no found drawing, no found image appears. All sound is synthesized.',
]
# re-set: wrap the paragraph to stay inside a 40 px right margin (and the 112 px left one)
words = ' '.join(lines).split()
maxw = W - 112 - 40
rows, cur = [], ''
for w_ in words:
    t = (cur + ' ' + w_).strip()
    if d.textlength(t, font=lit) <= maxw: cur = t
    else: rows.append(cur); cur = w_
rows.append(cur)
for k, ln in enumerate(rows):
    d.text((112, 150 + k * 38), ln, font=lit, fill=INK)
y_end = 150 + len(rows) * 38 + 20
for ln in [d.textlength(r, font=lit) for r in rows]:
    assert 112 + ln <= W - 40
d.text((112, y_end + 10), 'the score: PAELEO threshold machine, 32 s, six choices — kept within ±0.25 s, measured from the render', font=mono, fill=DIM)
d.text((112, y_end + 40), 'SCION 33 · Inverse Kinematics — Contact and Reach Swarm · cohort 4', font=mono, fill=DIM)
im.save(os.path.join(HERE, 'cache/end.png'))
print('cards ok', len(rows), 'rows; widest', max(d.textlength(r, font=lit) for r in rows), 'mono', d.textlength('the score: PAELEO threshold machine, 32 s, six choices — kept within ±0.25 s, measured from the render', font=mono))
