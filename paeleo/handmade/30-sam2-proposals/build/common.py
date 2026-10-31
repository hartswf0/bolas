"""SCION 30 / SAM 2 proposal swarm: shared paths, loaders and mask rasterisation.

Every piece of the film is a mask proposal over a real source frame. A proposal is typed:
  {obj, src, frame, prompt:{box, points}, polygon(s), mirror, corrections[], conf{...}}
and is always rasterised from its polygon (never from unexplained pixels)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)                       # paeleo/handmade/30-sam2-proposals
REPO = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
KIT = os.path.join(REPO, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
CACHE = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
os.makedirs(CACHE, exist_ok=True)

SOURCES = {
    'dog': dict(dir=os.path.join(KIT, 'archive-dog'), title='Amateur Film New Jersey C',
                archive='https://archive.org/details/NewJerseyC', collection='Home Movies (Internet Archive)',
                shot='https://www.movingimagearchive.com/sources/amateur-film-new-jersey-c-c65a8960?clip=2fdacde1-8a23-58e1-b905-5407385bd039',
                rights='public_domain', sam='Grounding DINO tiny box "dog" -> SAM 2.1 hiera-small mask, every frame (secondhand-motion mask_meta.json)'),
    'door': dict(dir=os.path.join(SHOTS, 'door-sam'), title='Straight Talk', archive='(NTIS; see kit/archive-door/source.json)',
                 collection='NTIS', shot='clip 271d80c7-4f56-51b8-90fe-012dfb984b4f', rights='public_domain',
                 sam='Grounding DINO tiny box "a door." -> SAM 2.1 hiera-small mask, every frame'),
    'hand': dict(dir=os.path.join(SHOTS, 'hand-sam'), title='Door to Heaven, The (1941)',
                 archive='https://archive.org/details/DoortoHe1941', collection='Internet Archive',
                 shot='https://www.movingimagearchive.com/sources/door-to-heaven-the?clip=0870ef3a-b328-5284-890b-3e1ac18057c1',
                 rights='public_domain', sam='Grounding DINO tiny box "a hand." -> SAM 2.1 hiera-small mask, every frame'),
    'sitter': dict(dir=os.path.join(SHOTS, 'sleeping-bag-sam'), title='Survival Stresses', archive='(found-frames.json)',
                   collection='found-frames.json', shot='sleeping-bag-sam', rights='public_domain',
                   sam='Grounding DINO tiny box "a sleeping bag." -> SAM 2.1 hiera-small mask, every frame'),
}


def src_frame(src, i):
    return Image.open(os.path.join(SOURCES[src]['dir'], 'frames', 'f%03d.jpg' % i)).convert('RGB')


_masks = {}


def src_masks(src):
    if src not in _masks:
        _masks[src] = json.load(open(os.path.join(SOURCES[src]['dir'], 'masks.json')))
    return _masks[src]


def src_meta(src):
    p = os.path.join(SOURCES[src]['dir'], 'mask_meta.json')
    if src == 'dog':
        p = os.path.join(SHOTS, 'dog-sam', 'mask_meta.json')
    if not os.path.exists(p):
        return {}
    return {f['f']: f for f in json.load(open(p))['frames']}


def raster(polys, size, ss=4, add=(), sub=()):
    """Rasterise polygons (+ correction strokes: add/sub polygons) to a soft alpha in [0,1] at 1x via ss supersampling."""
    W, H = size
    im = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        if len(poly) >= 3:
            d.polygon([(x * ss, y * ss) for x, y in poly], fill=255)
    for poly in add:
        d.polygon([(x * ss, y * ss) for x, y in poly], fill=255)
    for poly in sub:
        d.polygon([(x * ss, y * ss) for x, y in poly], fill=0)
    return np.asarray(im.resize((W, H), Image.BOX), dtype=np.float32) / 255.0


def largest_component(binary):
    """4-connected largest component of a boolean array (pure numpy/python flood fill)."""
    H, W = binary.shape
    lab = np.zeros((H, W), np.int32)
    best, best_n, cur = 0, 0, 0
    ys, xs = np.nonzero(binary)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        cur += 1
        st = [(y0, x0)]; lab[y0, x0] = cur; n = 0
        while st:
            y, x = st.pop(); n += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and binary[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = cur; st.append((yy, xx))
        if n > best_n:
            best, best_n = cur, n
    return lab == best


def fill_holes(binary):
    outside = largest_component_bg(~binary)
    return ~outside


def largest_component_bg(bg):
    """background region connected to the border"""
    H, W = bg.shape
    seen = np.zeros_like(bg)
    st = [(y, x) for y in (0, H - 1) for x in range(W) if bg[y, x]] + [(y, x) for x in (0, W - 1) for y in range(H) if bg[y, x]]
    for y, x in st:
        seen[y, x] = True
    while st:
        y, x = st.pop()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < H and 0 <= xx < W and bg[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True; st.append((yy, xx))
    return seen


def grad_mag(gray):
    g = gray.astype(np.float32)
    gx = np.zeros_like(g); gy = np.zeros_like(g)
    gx[:, 1:-1] = (g[:, 2:] - g[:, :-2]) * .5
    gy[1:-1, :] = (g[2:, :] - g[:-2, :]) * .5
    return np.hypot(gx, gy)


def jdump(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=1)
