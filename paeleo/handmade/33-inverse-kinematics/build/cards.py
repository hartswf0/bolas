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
for k, ln in enumerate(lines):
    d.text((112, 175 + k * 40), ln, font=lit, fill=INK)
d.text((112, 530), 'the score: PAELEO threshold machine, 32 s, six choices — kept within ±0.25 s, measured from the render', font=mono, fill=DIM)
d.text((112, 560), 'SCION 33 · Inverse Kinematics — Contact and Reach Swarm · cohort 4', font=mono, fill=DIM)
im.save(os.path.join(HERE, 'cache/end.png'))
print('cards ok')
