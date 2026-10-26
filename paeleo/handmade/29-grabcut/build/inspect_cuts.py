"""QA inspector: proof sheets of cuts. python3 inspect_cuts.py <shot> <frames,comma> <out.jpg>
Per frame: source crop with SAM edge (red) and our cut edge (cyan) | RGBA piece over flat dusk blue |
failure mask (red: we cut away what SAM kept; green: we kept what SAM left out; yellow: matte band)."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphcut import contour

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')


def tile(shot, i, s=2):
    z = np.load(os.path.join(C, shot, (i + '.npz') if isinstance(i, str) else 'f%03d.npz' % i))
    rgb = z['rgb'].astype(np.float32); a = z['alpha'].astype(np.float32); fg = z['fg']; sam = z['sam']
    A = rgb.copy()
    A[contour(sam)] = [255, 40, 40]; A[contour(a > .5)] = [40, 255, 255]
    B = rgb * a[..., None] + np.array([40, 52, 80], np.float32) * (1 - a[..., None])
    Cc = rgb * .35
    Cc[sam & ~fg] = [255, 40, 40]; Cc[fg & ~sam] = [40, 255, 40]
    Cc[(a > .02) & (a < .98)] = [255, 230, 40]
    row = np.concatenate([A, B, Cc], 1).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(row)
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


if __name__ == '__main__':
    shot = sys.argv[1]; fr = [int(x) if x.isdigit() else x for x in sys.argv[2].split(',')]; out = sys.argv[3]
    s = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    ims = [tile(shot, i, s) for i in fr]
    W = max(im.width for im in ims); H = sum(im.height for im in ims)
    sheet = Image.new('RGB', (W, H), (0, 0, 0)); y = 0
    for im in ims:
        sheet.paste(im, (0, y)); y += im.height
    sheet.save(out, quality=90)
