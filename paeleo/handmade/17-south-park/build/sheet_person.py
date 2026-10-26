"""Cast bible sheet: Maren's postures and mouth atlas (proof/cast_bible_person.png)."""
import os
from PIL import Image, ImageDraw
import person
from paint import paint, cm_to_px
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'proof', 'cast_bible_person.png')
S = 1.6
poses = [
 ('STAND', dict()),
 ('CALL lean', dict(lean=8, brow='UP', mouth='AA')),
 ('REACH', dict(lean=14, brow='UP', mouth='EE', hands={'n': (78, 120), 'f': (-16, 34)})),
 ('CROUCH', dict(posture='CROUCH', pelvis=(0, 42), lean=18, feet={'n': (22, 0), 'f': (-6, 0)})),
 ('SIT, hand low', dict(posture='SIT', pelvis=(0, 13), feet={'n': (56, 0), 'f': (48, 0)}, hands={'n': (82, 8), 'f': (34, 40)}, palm_up=True, eye='HALF', brow='SOFT', mouth='SMILE', tilt=6, lean=20)),
 ('SIT soft speak', dict(posture='SIT', pelvis=(0, 13), feet={'n': (56, 0), 'f': (48, 0)}, hands={'n': (82, 8), 'f': (34, 40)}, palm_up=True, eye='HALF', brow='SOFT', mouth='OH', tilt=6, lean=20)),
]
cols = 3; W, Hh = 420, 380
im = Image.new('RGB', (cols * W, ((len(poses) + cols - 1) // cols) * Hh + 160), (92, 104, 134))
d = ImageDraw.Draw(im)
for k, (name, pose) in enumerate(poses):
    ox, oy = (k % cols) * W + W // 2 - 40, (k // cols) * Hh + Hh - 40
    d.line([(ox - 150, oy), (ox + 190, oy)], fill=(60, 50, 50), width=2)
    pcs, info = person.build(pose)
    paint(im, pcs, cm_to_px(S, ox, oy), edge=2, draw=d)
    d.text((ox - 150, oy + 8), name, fill='white')
# mouth atlas strip
y0 = im.height - 80
for k, m in enumerate(['REST', 'MBP', 'AA', 'EE', 'OH', 'OO', 'CONS', 'S', 'L', 'SMILE']):
    ox = 60 + k * 120
    pcs = person.head('OPEN', 'NEUTRAL', m, (1, 0))
    paint(im, pcs, cm_to_px(2.4, ox, y0), edge=2, draw=d)
    d.text((ox - 20, y0 + 50), m, fill='white')
im.save(OUT); print(OUT)
