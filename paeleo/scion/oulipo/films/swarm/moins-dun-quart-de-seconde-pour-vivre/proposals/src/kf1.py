"""KF1 · BRUSH PLATE, WRITTEN BALLOONS.
One brush-drawn plate pasted eight times (identical bytes); balloons on their own
plane, hand-lettered stroke by stroke. Frame shown: 0:47, strip B panel 4 mid-writing."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from plate import draw_plate, art_hash
from hand import balloon, layout, letter, brush

OUT = os.path.join(os.path.dirname(__file__), '..')
K = 2                      # supersample of the page
PW = 300                   # panel size in final px
G = 14
X0 = (1280 - (4 * PW + 3 * G)) // 2
ROWS = (62, 62 + PW + 44)

A = [["IF I OPEN IT,", "I'LL KNOW."], ["IF I DON'T,", "I CAN STILL", "HOPE."], None, ["HOPE IT IS,", "THEN."]]
B = [["ME? I'VE BEEN", "ON THIS BENCH", "SINCE NINE."], ["ASK THE LAMP."], ["AND LOOK -", "STILL SEALED."], ["WHY WOULD I", "OPEN SOMEONE", "ELSE'S?"]]


def strip_label(d, text, x, y, size, seed):
    rng = np.random.default_rng(seed)
    st, _ = layout([text], size, rng)
    letter(d, st, x, y, size * 0.14, seed)


def build(write_upto=0.62, out='kf-1.png'):
    plate = draw_plate(PW * K)
    h0 = art_hash(plate)
    page = Image.new('L', (1280 * K, 720 * K), 255)
    d = ImageDraw.Draw(page)
    hashes = []
    for r, (row, lines) in enumerate(zip(ROWS, (A, B))):
        for c in range(4):
            x, y = (X0 + c * (PW + G)) * K, row * K
            art = plate.copy()
            hashes.append(art_hash(art))
            # balloon plane (separate layer, composited over the art)
            if lines[c]:
                upto = write_upto if (r == 1 and c == 3) else 1.0
                seed = 100 + r * 10 + c
                cy = 92 if len(lines[c]) > 2 else 80
                # balloon plane: drawn over a copy of the art, never into the plate itself
                balloon(ImageDraw.Draw(art), lines[c], 168, cy, 26, seed, tail=(292, 150 if len(lines[c]) > 2 else 132), upto=upto, letter_w=3.6, line_w=3.4)
            page.paste(art, (x, y))
            # hand border
            rng = np.random.default_rng(500 + r * 4 + c)
            bx = [(x, y), (x + PW * K, y), (x + PW * K, y + PW * K), (x, y + PW * K), (x, y)]
            brush(d, bx, 5, rng, taper=(0, 0), press=0.2)
    assert all(h == h0 for h in hashes), 'plate drift'
    strip_label(d, "A  -  TO WAIT", X0 * K, (ROWS[0] - 30) * K, 30, 7)
    strip_label(d, "B  -  THE ALIBI", X0 * K, (ROWS[1] - 30) * K, 30, 8)
    # time stamp / panel 3 silence mark
    strip_label(d, "0:47", (1280 - X0 - 52) * K, (ROWS[0] - 30) * K, 30, 9)
    page = page.resize((1280, 720), Image.LANCZOS).convert('RGB')
    page.save(os.path.join(OUT, out))
    print('plate hash', h0, 'x8 identical')


if __name__ == '__main__':
    build()
