"""Cast bible sheet: Biscuit's direction states and expression atlas (proof/cast_bible_dog.png)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
import dog
from paint import paint, cm_to_px
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'proof', 'cast_bible_dog.png')
S = 3.0
feet = {'frontn': (-23, 0), 'frontf': (-20, 0), 'hindn': (24, 0), 'hindf': (21, 0)}
poses = [
 ('P stand', dict(body='P', feet=feet)),
 ('Q stand', dict(body='Q', head_view='Q', gaze=(-0.4, 0))),
 ('F stand', dict(body='F', head_view='F', gaze=(0, 0))),
 ('Q mirror', dict(body='Q', head_view='Q', mirror=True, gaze=(-0.4, 0))),
 ('P mirror', dict(body='P', feet=feet, mirror=True)),
 ('P head LOW', dict(body='P', feet=feet, head_stop='LOW', ear='HALF', eye='HALF', brow='WORRY', tail=-10)),
 ('crouch H30 alarm', dict(body='P', H=31, feet=feet, head_stop='MID', ear='FLAT', eye='WIDE', brow='WORRY', tail=-118)),
 ('half down H22', dict(body='P', H=22, feet=feet, head_stop='MID', ear='HALF')),
 ('LIE up', dict(draw='LIE', head_stop='L_UP', eye='OPEN')),
 ('LIE chin', dict(draw='LIE', head_stop='L_CHIN', eye='CLOSED', brow='DOWN', ear='HALF')),
 ('LIE look in (B)', dict(draw='LIE', head_view='B', head_stop='L_HIGH', ear='PRICK')),
 ('LIE QB', dict(draw='LIE', head_view='QB', head_stop='L_UP')),
 ('mirror LIE, head back', dict(draw='LIE', mirror=True, head_mirror=True, head_stop='L_UP', ear='PRICK')),
 ('mirror LIE, F head', dict(draw='LIE', mirror=True, head_view='F', head_stop='L_UP', gaze=(-1, 0))),
 ('P stand, F head', dict(body='P', feet=feet, head_view='F', gaze=(-1, 0), mirror=True)),
 ('expr: sulk', dict(body='P', feet=feet, eye='HALF', brow='DOWN', ear='HALF', mirror=True, head_stop='LOW')),
]
cols = 4; W, Hh = 420, 330
im = Image.new('RGB', (cols * W, ((len(poses) + cols - 1) // cols) * Hh), (92, 104, 134))
d = ImageDraw.Draw(im)
for k, (name, pose) in enumerate(poses):
    ox, oy = (k % cols) * W + W // 2, (k // cols) * Hh + Hh - 40
    d.line([(ox - 190, oy), (ox + 190, oy)], fill=(60, 50, 50), width=2)
    paint(im, dog.build(pose), cm_to_px(S, ox, oy), edge=2, draw=d)
    d.text((ox - 195, oy + 8), name, fill='white')
im.save(OUT); print(OUT)
