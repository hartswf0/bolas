"""Title card (3 s) and end card (3 s). The title shows the operation itself: archive frame 13 of the dog shot, then the
background falls away from our cut and the figure is left with its cut line. -> build/cache/cards/t%03d.jpg, e%03d.jpg"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from graphcut import erode
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
F = os.path.join(ROOT, 'tools/paeleo/fonts')
OUT = os.path.join(HERE, 'cache/cards')
W, H = 1280, 720
os.makedirs(OUT, exist_ok=True)
big = ImageFont.truetype(os.path.join(F, 'f8.woff2'), 64)
mid = ImageFont.truetype(os.path.join(F, 'f2.woff2'), 30)
mono = ImageFont.truetype(os.path.join(F, 'f14.woff2'), 17)
BG = np.array([10, 12, 22], np.float32)


def smooth(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


src = np.array(Image.open(os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog/frames/f013.jpg')).convert('L')).astype(np.float32)
z = np.load(os.path.join(HERE, 'cache/dog/f013.npz'))
a = np.zeros_like(src); x0, y0 = z['origin']; al = z['alpha'].astype(np.float32)
a[y0:y0 + al.shape[0], x0:x0 + al.shape[1]] = al
edge = ((a > .5) & ~erode(a > .5, 1)).astype(np.float32)
S = 2.0
srcI = np.array(Image.fromarray(src.astype(np.uint8)).resize((int(384 * S), int(288 * S)), Image.BICUBIC)).astype(np.float32)
aI = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize(srcI.shape[::-1], Image.BILINEAR)).astype(np.float32) / 255
eI = np.array(Image.fromarray((edge * 255).astype(np.uint8)).resize(srcI.shape[::-1], Image.BILINEAR)).astype(np.float32) / 255
ox, oy = 470, 70
for k in range(72):
    t = k / 24
    img = np.tile(BG, (H, W, 1))
    fade = 1 - smooth((t - 0.7) / 1.0)        # the background falls away
    line = smooth((t - 0.4) / 0.4)
    lum = srcI / 255.0
    col = lum[..., None] * np.array([150, 170, 215]) * (aI[..., None] + (1 - aI[..., None]) * fade * 0.8)
    reg = img[oy:oy + srcI.shape[0], ox:ox + srcI.shape[1]]
    vis = np.clip(aI + fade, 0, 1)[..., None]
    reg[:] = reg * (1 - vis) + col * vis
    reg[:] = reg * (1 - eI[..., None] * line) + np.array([200, 220, 255]) * eI[..., None] * line
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    ta = int(255 * smooth((t - 0.2) / 0.6))
    d.text((60, 250), 'PAE-02 · SCION 29 · GrabCut', font=mid, fill=(170, 180, 205, ta))
    d.text((60, 290), 'GrabCut', font=big, fill=(232, 236, 245, ta))
    d.text((60, 380), 'the threshold, cut out of archive film', font=mono, fill=(150, 160, 185, ta))
    d.text((60, 640), 'archive frame: Amateur Film New Jersey C (Home Movies, Internet Archive, public domain) · our graph cut', font=mono, fill=(110, 118, 140))
    im.save(os.path.join(OUT, 't%03d.jpg' % k), quality=92)

lines = [
    ('made of', mid),
    ('graph cuts of public-domain archive film: our own max-flow (Boykov-Kolmogorov, numpy), seeded by boxes,', mono),
    ('scribbles and the kit\'s SAM masks as one input; colour, texture and clean-plate unaries; alpha cleanup.', mono),
    ('', mono),
    ('the dog: 19 frames of the home-movie dog, Amateur Film New Jersey C, cut out and re-timed, mirrored,', mono),
    ('played backwards; lying down it is the pieces of one of its own frames (this clip never shows it lying).', mono),
    ('the woman and the door: Straight Talk (NTIS, 1992). the low hand: The Door to Heaven, cut from its card.', mono),
    ('the stone, the porch boards and the garden: the dog\'s own porch, a clean plate of its shot.', mono),
    ('the doorway light, the sky, the shadows and all the sound are synthesized here.', mono),
]
for k in range(72):
    t = k / 24
    im = Image.new('RGB', (W, H), tuple(int(v) for v in BG)); d = ImageDraw.Draw(im)
    ta = int(255 * min(smooth(t / 0.5), smooth((3 - t) / 0.4)))
    y = 170
    for txt, f in lines:
        d.text((90, y), txt, font=f, fill=(200, 208, 225) if f is mono else (232, 236, 245)); y += 44 if f is mid else 30
    if ta < 255:
        im = Image.blend(Image.new('RGB', (W, H), tuple(int(v) for v in BG)), im, ta / 255)
    im.save(os.path.join(OUT, 'e%03d.jpg' % k), quality=92)
print('cards ok')
