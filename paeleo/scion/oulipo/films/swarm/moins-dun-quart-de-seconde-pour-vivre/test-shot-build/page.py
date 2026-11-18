"""Test page: the full two-strip page at print resolution (2480x1754, A4 landscape 300 dpi).

Same plate raster and the same final balloon layers as the test shot. All page
lettering (header, labels, footer) is written in the same single-stroke hand.
"""
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plate2 import draw_plate, art_hash, tone
from balloons import Balloon, composite
from hand import layout, brush

PW, PH = 2480, 1754
XS = (106, 682, 1258, 1834)
ROWS = {'A': 290, 'B': 990}
ORDER = {'A': ['A1', 'A2', None, 'A4'], 'B': ['B1', 'B2', 'B3', 'B4']}
SWARM = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MEDIA = os.path.abspath(os.path.join(SWARM, '../../sources/moins-dun-quart-de-seconde-pour-vivre/test-shot'))


def write(d, text, x, y, size, seed, w, k=2):
    rng = np.random.default_rng(seed)
    st, (tw, th) = layout([text], size * k, rng)
    for i, s in enumerate(st):
        brush(d, [(px + x * k, py + y * k) for px, py in s], w * k, np.random.default_rng(seed * 97 + i), taper=(0.15, 0.2), press=0.18)
    return tw / k


def build_page(plate, layers, with_balloons=True):
    k = 2
    big = Image.new('L', (PW * k, PH * k), 255)
    d = ImageDraw.Draw(big)
    write(d, "ONE PLATE, TWO STRIPS", 106, 78, 54, 3, 6.0)
    rng = np.random.default_rng(4)
    st, (tw, th) = layout(["AFTER MENU AND TRONDHEIM, 1991"], 26 * k, rng)
    write(d, "AFTER MENU AND TRONDHEIM, 1991", 2374 - tw / k, 104, 26, 4, 3.6)
    write(d, "A - TO WAIT", 106, 222, 36, 5, 4.4)
    write(d, "B - THE ALIBI", 106, 922, 36, 6, 4.4)
    write(d, "THE ART LAYER IS IDENTICAL IN ALL EIGHT PANELS - SHA256 " + art_hash(plate)[:12].upper(), 106, 1630, 24, 8, 3.4)
    page = tone(big.resize((PW, PH), Image.LANCZOS))
    hashes = []
    for row, y in ROWS.items():
        for c, key in enumerate(ORDER[row]):
            art = plate.copy()
            hashes.append(art_hash(art))
            panel = composite(art, layers.get(key) if (key and with_balloons) else None)
            page.paste(panel, (XS[c], y))
    assert len(set(hashes)) == 1 and len(hashes) == 8, 'plate drift'
    return page


def load():
    plate = draw_plate()
    balloons = {k: Balloon(k) for k in ('A1', 'A2', 'A4', 'B1', 'B2', 'B3', 'B4')}
    layers = {k: b.render(None) for k, b in balloons.items()}
    return plate, balloons, layers


if __name__ == '__main__':
    plate, balloons, layers = load()
    plate.save(os.path.join(MEDIA, 'plate-540.png'))
    page = build_page(plate, layers)
    page.save(os.path.join(SWARM, 'test-page.png'))
    # balloons must never cover eye / flap / B2 lamp
    from plate2 import EYE_BOX, FLAP_BOX, LAMP_BOX
    rep = {}
    for key, (pm, a) in layers.items():
        def cov(b):
            x0, y0, x1, y1 = b
            return float((a[y0:y1, x0:x1] > 0.02).mean())
        rep[key] = dict(eye=cov(EYE_BOX), flap=cov(FLAP_BOX), lamp=cov(LAMP_BOX), box=[round(v) for v in balloons[key].box])
    print(json.dumps(rep, indent=1))
    g = np.asarray(page)
    mid = ((g > 60) & (g < 200)).mean()
    print('plate sha', art_hash(plate)[:16], 'page mid-tone share %.3f' % mid, 'ink min', g.min(), 'paper max', g.max())
