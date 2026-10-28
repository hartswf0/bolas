"""proof: the learned model alone ('raw') next to the film ('corrected') at the poses the archive never showed."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as RD
HERE = os.path.dirname(os.path.abspath(__file__))
F = ImageFont.truetype(os.path.normpath(os.path.join(HERE, '../../../../tools/paeleo/fonts/f14.woff2')), 15)
TIMES = [(3.62, 'turning (front view)'), (6.5, 'lying, back turned'), (7.62, 'looking back over the shoulder'),
         (19.0, 'coming, head low'), (25.0, 'lying across the sill'), (27.3, 'looking in')]

def crop(img, m, w=420, h=300):
    cx, cy = int(m['cx']), int(m['cy'])
    x0 = max(0, min(1280 - w, cx - w // 2)); y0 = max(0, min(720 - h, cy - h // 2 - 20))
    return Image.fromarray(img).crop((x0, y0, x0 + w, y0 + h))

if __name__ == '__main__':
    rows = []; strip = []
    for t, name in TIMES:
        c = RD.CTRL[int(round(t * 24))]
        a, ma = RD.render_frame(c, 'raw'); b, mb = RD.render_frame(c, 'corrected')
        A, B = crop(a, mb), crop(b, mb)
        for im, lab, m in [(A, 'model alone', ma), (B, 'film (corrected)', mb)]:
            d = ImageDraw.Draw(im); d.rectangle([0, 0, 420, 22], fill=(10, 10, 14))
            d.text((6, 3), '%s %.2fs  %s  ood %.2f' % (lab, t, name, m.get('ood', 0)), font=F, fill=(230, 220, 200))
        rows.append((A, B))
        if name in ('lying, back turned', 'looking back over the shoulder', 'lying across the sill', 'looking in'):
            strip += [A.resize((280, 200)), B.resize((280, 200))]
    S = Image.new('RGB', (850, 310 * len(rows)), (10, 10, 14))
    for k, (A, B) in enumerate(rows):
        S.paste(A, (0, k * 310)); S.paste(B, (430, k * 310))
    S.save(os.path.join(HERE, '..', 'proof', 'raw_vs_corrected.jpg'), quality=85)
    T = Image.new('RGB', (4 * 290, 2 * 205), (14, 15, 22))
    for k, im in enumerate(strip[:8]):
        # pairs: column = pose, row 0 = raw, row 1 = corrected
        T.paste(im, ((k // 2) * 290, (k % 2) * 205))
    T.save(os.path.join(HERE, '..', 'proof', 'raw_vs_corrected_strip.jpg'), quality=90)
