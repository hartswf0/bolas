#!/usr/bin/env python3
"""Cutout surgeon for the shorts: cut moving parts out of a postcard and fill the holes they leave.
python3 shorts/tools/cut.py <card> [--check]

Reads shorts/parts/<card>.json:
  {"card": "assets/series/<card>.jpg",
   "parts": [{"name": "boy", "poly": [[x, y], ...], "pivot": [x, y], "fill": true, "matte": "auto"}],
   "holes": [[[x, y], ...]]}          extra regions to fill in the clean plate (painted-out props)
Writes assets/shorts/parts/<card>/:
  clean.jpg      the card with every "fill" part and every hole filled from its surroundings
  empty.jpg      clean.jpg with the "slot" parts (recastable actors) removed too, when there are any
  <name>.png     each part, cropped to its box, with a soft one-pixel edge (or, with "matte", only the drawing
                 inside the outline: see matte())
  parts.json     each part's box and pivot in card pixels, for shorts/stage.js
--check also writes <card>-check.jpg (into $CHECK_DIR, else the parts folder): every outline drawn on the card.
Nothing is generated: parts are the card's own pixels, and fills are the card's own colours pulled inward."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def mask_of(size, polys, grow=0):
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([tuple(q) for q in p], fill=255)
    if grow:
        m = m.filter(ImageFilter.MaxFilter(2 * grow + 1))
    return m


def fill(img, hole):
    """Pyramid fill: average the known pixels into the hole from coarse to fine, then add back grain
    sampled from the card so the fill does not read as a smear."""
    a = np.asarray(img, dtype=np.float32) / 255
    k = (np.asarray(hole) < 128).astype(np.float32)[..., None]
    levels = []
    cur, w = a * k, k
    while min(cur.shape[:2]) > 4:
        levels.append((cur, w))
        h2, w2 = cur.shape[0] // 2 * 2, cur.shape[1] // 2 * 2
        c, ww = cur[:h2, :w2], w[:h2, :w2]
        cur = (c[0::2, 0::2] + c[1::2, 0::2] + c[0::2, 1::2] + c[1::2, 1::2])
        w = (ww[0::2, 0::2] + ww[1::2, 0::2] + ww[0::2, 1::2] + ww[1::2, 1::2])
        cur = np.where(w > 0, cur / np.maximum(w, 1e-6), 0) * (w > 0)
        w = (w > 0).astype(np.float32)
    est = np.where(w > 0, cur, cur.sum((0, 1)) / max(w.sum(), 1))
    for cur, w in reversed(levels):
        up = np.repeat(np.repeat(est, 2, 0), 2, 1)
        up = np.pad(up, ((0, cur.shape[0] - up.shape[0]), (0, cur.shape[1] - up.shape[1]), (0, 0)), mode='edge')
        est = np.where(w > 0, cur, up)
        est = np.asarray(Image.fromarray((np.clip(est, 0, 1) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255 * (1 - w) + cur * w
    rng = np.random.default_rng(7)
    known = np.argwhere(k[..., 0] > 0)
    blur = np.asarray(img.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255
    grain = a - blur
    pick = known[rng.integers(0, len(known), size=a.shape[:2])]
    noise = grain[pick[..., 0], pick[..., 1]]
    out = np.where(k > 0, a, np.clip(est + noise * 0.7, 0, 1))
    return Image.fromarray((out * 255).astype(np.uint8))


def drop_specks(fig, size):
    """Open a binary mask: pieces thinner than size pixels go, the rest keep their shape."""
    m = Image.fromarray((fig * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MinFilter(size)).filter(ImageFilter.MaxFilter(size))
    return np.asarray(m) > 127


def matte(img, poly, how, ground=None):
    """Alpha for the drawing inside an outline, not the outline itself.
    'auto': a pixel is ground when its colour is near a ground colour (sampled from the spec's "ground" boxes, else
    from a ring just outside the outline) and it is connected to the outside through ground; everything else is the
    figure, so the figure comes out solid. 'dark:<l>': a pixel belongs when it is darker than l (0..1)."""
    a = np.asarray(img, dtype=np.float32) / 255
    inside = np.asarray(mask_of(img.size, [poly]), dtype=np.float32) / 255
    if how.startswith('dark'):
        thr = float(how.split(':')[1])
        lum = a @ np.array([.3, .59, .11], dtype=np.float32)
        al = np.clip((thr - lum) / .08 + .5, 0, 1) * inside
    else:
        if ground:
            bg = np.concatenate([a[y0:y1, x0:x1].reshape(-1, 3) for x0, y0, x1, y1 in ground])
        else:
            bg = a[(np.asarray(mask_of(img.size, [poly], grow=7)) > 0) & (inside < .5)]
        rng = np.random.default_rng(3)
        cen = bg[rng.choice(len(bg), 10, replace=False)]
        for _ in range(12):  # k-means on the ground colours
            lab = np.argmin(((bg[:, None] - cen[None]) ** 2).sum(-1), 1)
            cen = np.array([bg[lab == k].mean(0) if (lab == k).any() else cen[k] for k in range(len(cen))])
        d = np.sqrt(((a[..., None, :] - cen[None, None]) ** 2).sum(-1)).min(-1)
        groundlike = Image.fromarray(((d < .11) * 255).astype(np.uint8))
        # flood the ground in from outside the outline; ground-coloured pockets inside the figure stay figure
        cand = Image.new('L', img.size, 255)
        cand.paste(groundlike, mask=mask_of(img.size, [poly]))
        cand = cand.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
        pad = Image.new('L', (img.width + 2, img.height + 2), 255); pad.paste(cand, (1, 1))
        ImageDraw.floodfill(pad, (0, 0), 128)
        reached = np.asarray(pad.crop((1, 1, img.width + 1, img.height + 1))) == 128
        al = (drop_specks((~reached) & (inside > .5), 5) & (inside > .5)).astype(np.float32)
    m = Image.fromarray((al * 255).astype(np.uint8))
    if how == 'auto':  # a scissor-cut contour: smooth the edge, then make it crisp again
        m = m.filter(ImageFilter.GaussianBlur(1.1)).point(lambda v: 255 if v > 120 else 0)
    else:
        m = m.filter(ImageFilter.MedianFilter(3))
    return m.filter(ImageFilter.GaussianBlur(.5))


def main():
    card = sys.argv[1]
    spec = json.load(open(os.path.join(root, 'shorts/parts', card + '.json')))
    img = Image.open(os.path.join(root, spec['card'])).convert('RGB')
    out = os.path.join(root, 'assets/shorts/parts', card)
    os.makedirs(out, exist_ok=True)
    holes = [p['poly'] for p in spec['parts'] if p.get('fill', True) and not p.get('slot')] + spec.get('holes', [])
    clean = fill(img, mask_of(img.size, holes, grow=2)) if holes else img
    # a "slot" part is an actor that another actor can be recast into: it stays in clean.jpg, and empty.jpg has it removed
    slots = [p['poly'] for p in spec['parts'] if p.get('slot')]
    if slots:
        fill(clean, mask_of(img.size, slots, grow=3)).save(os.path.join(out, 'empty.jpg'), quality=92)
    # "copy": [dx, dy] fills that part's hole with the card's own texture from that far away instead (floors, walls)
    for p in spec['parts']:
        if p.get('copy'):
            dx, dy = p['copy']
            src = img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
            m = mask_of(img.size, [p['poly']], grow=3).filter(ImageFilter.GaussianBlur(2))
            clean = Image.composite(src, clean, m)
    clean.save(os.path.join(out, 'clean.jpg'), quality=92)
    manifest = {'card': spec['card'], 'size': list(img.size), 'empty': bool(slots), 'parts': {}}
    for p in spec['parts']:
        m = matte(img, p['poly'], p['matte'], spec.get('ground')) if p.get('matte') else mask_of(img.size, [p['poly']]).filter(ImageFilter.GaussianBlur(0.7))
        x0, y0, x1, y1 = mask_of(img.size, [p['poly']], grow=2).getbbox()
        rgba = img.copy()
        rgba.putalpha(m)
        rgba.crop((x0, y0, x1, y1)).save(os.path.join(out, p['name'] + '.png'), optimize=True)
        manifest['parts'][p['name']] = {'x': x0, 'y': y0, 'w': x1 - x0, 'h': y1 - y0,
                                        'pivot': p.get('pivot', [(x0 + x1) / 2, (y0 + y1) / 2])}
    json.dump(manifest, open(os.path.join(out, 'parts.json'), 'w'), indent=1)
    if '--check' in sys.argv:
        chk = clean.copy()
        d = ImageDraw.Draw(chk)
        for p in spec['parts']:
            d.line([tuple(q) for q in p['poly'] + [p['poly'][0]]], fill=(255, 0, 255), width=1)
            if 'pivot' in p:
                x, y = p['pivot']
                d.ellipse((x - 3, y - 3, x + 3, y + 3), outline=(0, 255, 255))
        for h in spec.get('holes', []):
            d.line([tuple(q) for q in h + [h[0]]], fill=(0, 255, 0), width=1)
        chk = chk.resize((chk.width * 2, chk.height * 2))
        chk.save(os.path.join(os.environ.get('CHECK_DIR', out), card + '-check.jpg'), quality=85)
    print(card, len(spec['parts']), 'parts')


main()
