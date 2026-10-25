"""SCION 45 · Matte artist. The found plates other than the dog, cut and graded once into build/cache/plates/.

interior.png  Straight Talk (NTIS, public domain) f029: a hallway with coats and an inner door, graded warm   (crop, grade)
leaf.png      Straight Talk f016: the white door panel with its knob, SAM matte, rectified to a rectangle   (mask, quad-rectify)
bulb.png      Light Of Your Life B (public domain) f012: a lit bulb, SAM matte                              (mask, grade)
sky.png       Top Of The Cloud (public domain) f030: cumulus, regraded to dusk                              (grade, luminance remap)
hand.png      Door to Heaven (1941, public domain) f010: an outstretched hand, SAM matte + garbage-extended forearm (mask)
Version: plates-v2
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
DOOR = os.path.join(ROOT, 'paeleo/handmade/kit/archive-door')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
OUT = os.path.join(HERE, 'cache/plates')


def poly_mask(size, polys, blur=0.8):
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([tuple(q) for q in p], fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def grade(img, lift, gain, gamma=1.0):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    a = np.clip(a, 0, 1) ** gamma
    a = lift + a * (np.array(gain) - lift)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def main():
    os.makedirs(OUT, exist_ok=True)
    # interior: hallway, warm
    im = Image.open(os.path.join(DOOR, 'frames/f029.jpg')).convert('RGB')
    lum = np.asarray(im.convert('L')).astype(np.float32) / 255
    warm = np.stack([lum ** 0.9 * 1.0, lum ** 1.0 * 0.78, lum ** 1.25 * 0.48], -1)
    Image.fromarray((np.clip(warm, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'interior.png'))
    # door leaf: rectified panel
    im = Image.open(os.path.join(DOOR, 'frames/f016.jpg')).convert('RGB')
    quad = (305, 0, 266, 285, 374, 287, 376, 1)  # TL, BL, BR, TR (PIL QUAD order: NW, SW, SE, NE)
    leaf = im.transform((120, 300), Image.QUAD, quad, resample=Image.BICUBIC)
    leaf.save(os.path.join(OUT, 'leaf.png'))
    # bulb
    bdir = os.path.join(SHOTS, 'light-bulb-sam')
    im = Image.open(os.path.join(bdir, 'frames/f012.jpg')).convert('RGB')
    m = json.load(open(os.path.join(bdir, 'masks.json')))['12']
    mk = poly_mask(im.size, m)
    b = im.convert('RGBA'); b.putalpha(mk)
    b = b.crop(mk.getbbox()); b.save(os.path.join(OUT, 'bulb.png'))
    # sky: cumulus regraded to dusk (luminance -> dusk ramp)
    sdir = os.path.join(SHOTS, 'cloud-sam')
    im = Image.open(os.path.join(sdir, 'frames/f030.jpg')).convert('RGB')
    a = np.asarray(im).astype(np.float32) / 255
    lum = a.mean(-1)
    H, W = lum.shape
    yy = np.linspace(0, 1, H)[:, None]
    top = np.array([0.16, 0.18, 0.34]); hor = np.array([0.62, 0.42, 0.40])
    base = top * (1 - yy[..., None]) + hor * yy[..., None]
    cloud = np.clip((lum - 0.45) / 0.5, 0, 1)[..., None]
    cl_col = np.array([0.36, 0.30, 0.40]) + 0.25 * np.array([1.0, 0.55, 0.35]) * (yy[..., None])
    sky = base * (1 - cloud * 0.85) + cl_col * cloud * 0.85
    Image.fromarray((np.clip(sky, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'sky.png'))
    # hand: SAM fingers + a garbage-extended forearm polygon (the forearm leaves frame right)
    hdir = os.path.join(SHOTS, 'hand-sam')
    im = Image.open(os.path.join(hdir, 'frames/f010.jpg')).convert('RGB')
    m = json.load(open(os.path.join(hdir, 'masks.json')))['10']
    fore = [(280, 66), (330, 60), (384, 50), (384, 90), (330, 97), (280, 101)]
    mk = poly_mask(im.size, m + [fore])
    h = im.convert('RGBA'); h.putalpha(mk)
    h = h.crop((180, 45, 384, 115))
    h.save(os.path.join(OUT, 'hand.png'))
    print('plates ok')


if __name__ == '__main__':
    main()
