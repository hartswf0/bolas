"""Title and end cards (3 s each). The end card shows the cast: the dog's head plates with their landmark vectors."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from geom import ROOT, CACHE, W, H, apply
from plates import HEADS, TORSO, PAL
import render as R

FONTS = os.path.join(ROOT, 'tools/paeleo/fonts')
BG = (18, 20, 36)


def font(fn, size): return ImageFont.truetype(os.path.join(FONTS, fn), size)


def wrap(d, text, fnt, width):
    words = text.split(); lines = []; cur = ''
    for w_ in words:
        test = (cur + ' ' + w_).strip()
        if d.textlength(test, font=fnt) > width and cur: lines.append(cur); cur = w_
        else: cur = test
    if cur: lines.append(cur)
    return lines


def plate_thumb(img, table, view, cx, cy, scale, keys_color=(240, 196, 120)):
    P = table[view]
    pts = np.array([P['lm'][k] for k in P['keys']]) * np.array([1, -1])
    M = np.array([[scale, 0, cx], [0, scale, cy]], float)
    pt = R.Painter(img)
    L = np.array([0.95, 0.92, 0.9])
    R.draw_shapes(pt, P['shapes'], M, lambda k: R.lit(k, L), L, ink_w=1.4)
    if table is HEADS:
        f = dict(lid=0.95, crouch=0.0, mouth=0.0)
        R.draw_eyes(pt, view, 1, M, f, L)
    for q in apply(M, pts):
        pt.ellipse(q, 2.2, 2.2, keys_color)


def main():
    out = os.path.join(CACHE, 'cards'); os.makedirs(out, exist_ok=True)
    # title
    big = Image.new('RGB', (W * R.SS, H * R.SS), BG); im = big
    d = ImageDraw.Draw(im)
    f1 = font("f8.woff2", 120); f2 = font('f27.woff2', 46); f3 = font('f14.woff2', 26)
    d.text((W * R.SS / 2, 520), 'PAE-02 · SCION 46 · Face Landmark Registration', font=f1, fill=(238, 226, 200), anchor='mm')
    d.text((W * R.SS / 2, 680), 'Recasting anatomy: the threshold, handmade', font=f2, fill=(214, 170, 112), anchor='mm')
    d.text((W * R.SS / 2, 1250), 'a dog at a threshold that may refuse', font=f3, fill=(140, 140, 170), anchor='mm')
    im.reduce(R.SS).save(os.path.join(out, 'title.png'))
    # end card: the cast and what it is made of
    im = Image.new('RGB', (W * R.SS, H * R.SS), BG); d = ImageDraw.Draw(im)
    for k, v in enumerate((45, 90, 135, 180)):
        plate_thumb(im, HEADS, v, 110 + k * 145, 230, 400)
    for k, v in enumerate((90, 135, 180)):
        plate_thumb(im, TORSO, v, [150, 370, 560][k], 640, 215)
    fh = font("f8.woff2", 64); ft = font('f27.woff2', 33); fm = font('f14.woff2', 23)
    x0 = 1330; y = 150
    d.text((x0, y), 'What it is made of', font=fh, fill=(238, 226, 200)); y += 110
    paras = [
        'The dog is drawn for this film as plates, one per view: four heads, three bodies, ears, eyes, legs and a tail. '
        'Each plate carries its own landmark vector. Nothing is bent by hand: every plate is placed by an affine fit to a solved '
        'skeleton of landmarks, swapped for another view when the head or body turns, and its eyes, ears and mouth are controls.',
        "The person's face is a public-domain cartoon profile from 'We Learn About the Telephone I', placed by a similarity fit "
        '(never sheared); its mouth is its own source frames. Body and hat are drawn. The door is a public-domain door from '
        "'Straight Talk', rectified and re-projected on its hinge. The sound is synthesized.",
    ]
    for ptxt in paras:
        for line in wrap(d, ptxt, ft, 1150):
            d.text((x0, y), line, font=ft, fill=(206, 200, 188)); y += 46
        y += 26
    d.text((x0, 1330), 'gold dots: each plate\'s landmarks   ·   score: PAELEO threshold, 32 s, six choices', font=fm, fill=(140, 140, 170))
    im.reduce(R.SS).save(os.path.join(out, 'end.png'))
    print('cards written')


if __name__ == '__main__':
    main()
