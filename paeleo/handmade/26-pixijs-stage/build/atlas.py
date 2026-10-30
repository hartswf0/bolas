"""SCION-26 · build the texture atlas of archive fragments.

Every sprite the stage draws comes from this one atlas (atlas/atlas.png + atlas/atlas.json), so the GPU can batch hundreds
of fragments into a handful of draw calls. Each atlas frame records exactly where it was cut: source shot, frame index,
crop box in source pixels, the SAM mask used, and the operation (crop + mask + torn alpha, or quickdraw stroke raster).

Fragment classes
  fur_dog   small coat patches cut INSIDE the SAM mask of the archive dog (Amateur Film New Jersey C)
  fur_lion  coat patches inside the lion mask (Andy's Animal Alphabet), pale fur, used for chest/belly/legs
  fur_cat   tabby patches inside the cat mask (Gateways to the Mind), for the saddle and head
  dark      dark-stripe patches inside the tiger mask (Andy's Animal Alphabet) -> ears, nose, eyes, tail tip
  coat      cloth patches cut from the coats hanging in the door shot (Straight Talk) -> the person
  sky       patches of cloud (Top Of The Cloud) -> the dusk sky, tinted on stage
  star      the star cut-out (Gift of Green) -> a few stars
  wood      long strips of fence rail (Billie, the Buffalo Baby) and ladder pole (Robinson Crusoe C) -> boards, frame, sill
  big       single larger cut-outs: the offered hand, the lantern, the door leaf, a framed picture (windmill), cushion (sheep)
  qd_*      Quick, Draw! strokes rasterized as chalk lines (moon, tree, fence, house, dog doodles), key_id kept
Usage: python3 build/atlas.py   (writes build/atlas/atlas.png, atlas.json, quickdraw_used.ndjson)
"""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))          # /home/user/bolas
KIT = os.path.join(ROOT, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
QD = '/home/user/hartswf0/quickdraw'
OUT = os.path.join(HERE, 'atlas')
os.makedirs(OUT, exist_ok=True)
rng = random.Random(26)

FOUND = {s['category']: s for s in json.load(open(os.path.join(KIT, 'found-frames.json')))}

def shot(cat):
    if cat == 'dog':
        return os.path.join(KIT, 'archive-dog/frames'), json.load(open(os.path.join(KIT, 'archive-dog/masks.json')))
    d = os.path.join(SHOTS, cat + '-sam')
    return os.path.join(d, 'frames'), json.load(open(os.path.join(d, 'masks.json')))

def frame_files(cat):
    d, _ = shot(cat)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith('.jpg') or f.endswith('.png'))

def mask_img(polys, size):
    m = Image.new('L', size, 0)
    dr = ImageDraw.Draw(m)
    for p in polys:
        if len(p) > 2:
            dr.polygon([tuple(q) for q in p], fill=255)
    return m

ATLAS = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
FRAMES = {}
CLASSES = {}

def torn_alpha(w, h, kind='round'):
    """an irregular cut edge: a jittered polygon, 1 px feather (the scissors of the stage)"""
    a = Image.new('L', (w * 4, h * 4), 0)
    d = ImageDraw.Draw(a)
    n = rng.randint(6, 9)
    pts = []
    for k in range(n):
        ang = 2 * math.pi * (k + rng.uniform(-.25, .25)) / n
        r = rng.uniform(.80, 1.0) if kind == 'round' else 1.0
        ex, ey = math.cos(ang), math.sin(ang)
        if kind == 'square':
            s = max(abs(ex), abs(ey)); ex, ey = ex / s * rng.uniform(.86, 1), ey / s * rng.uniform(.86, 1)
        pts.append((w * 2 + ex * r * (w * 2 - 4), h * 2 + ey * r * (h * 2 - 4)))
    d.polygon(pts, fill=255)
    return a.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(.5))

def put(name, img, x, y, cls, meta):
    ATLAS.paste(img, (x, y), img)
    FRAMES[name] = dict(x=x, y=y, w=img.width, h=img.height, cls=cls, **meta)
    CLASSES.setdefault(cls, []).append(name)

def rel(p):
    return os.path.relpath(p, ROOT) if p.startswith(ROOT) else p.replace('/home/user/', '')

# ---------- small fragments: 48x48 cells ----------
CELL = 48
cursor = [0, 0]
def next_cell():
    x, y = cursor
    cursor[0] += CELL
    if cursor[0] + CELL > 2048:
        cursor[0] = 0; cursor[1] += CELL
    return x, y

def cut_patches(cat, cls, n, psize, frames=None, kind='round', inside=True, region=None, enhance=None):
    files = frame_files(cat)
    _, masks = shot(cat)
    idxs = frames or list(range(len(files)))
    got, tries = 0, 0
    while got < n and tries < n * 400:
        tries += 1
        fi = rng.choice(idxs)
        src = Image.open(files[fi]).convert('RGB')
        if region:
            x0, y0, x1, y1 = region
        else:
            x0, y0, x1, y1 = 0, 0, src.width, src.height
        ps = rng.randint(*psize)
        cx, cy = rng.randint(x0 + ps // 2, x1 - ps // 2 - 1), rng.randint(y0 + ps // 2, y1 - ps // 2 - 1)
        box = (cx - ps // 2, cy - ps // 2, cx - ps // 2 + ps, cy - ps // 2 + ps)
        if inside:
            m = mask_img(masks.get(str(fi), []), src.size).crop(box)
            hist = m.histogram()
            if hist[255] < ps * ps * .97:
                continue
        patch = src.crop(box)
        if enhance:
            patch = enhance(patch)
        patch = patch.resize((CELL, CELL), Image.LANCZOS).convert('RGBA')
        patch.putalpha(torn_alpha(CELL, CELL, kind))
        x, y = next_cell()
        put(f'{cls}_{got:03d}', patch, x, y, cls, dict(src=rel(files[fi]), shot=cat, frame=fi, crop=list(box),
            mask='SAM polygon, patch >= 97% inside' if inside else 'none (region crop)', op='crop + torn alpha'))
        got += 1
    print(cls, got, 'from', tries, 'tries')

from PIL import ImageOps, ImageEnhance
def grey_contrast(p):
    g = ImageOps.autocontrast(p.convert('L'), cutoff=2)
    return Image.merge('RGB', (g, g, g))
def fur_soft(p):
    # coat patches: normalized, then pulled halfway to their mean so fragment seams read as fur tone, not confetti
    g = ImageOps.autocontrast(p.convert('L'), cutoff=2)
    mean = sum(i * c for i, c in enumerate(g.histogram())) / (g.width * g.height)
    g = Image.blend(g, Image.new('L', g.size, int(mean * .4 + 160 * .6)), .62)
    return Image.merge('RGB', (g, g, g))
def tiger_dark(p):
    g = p.convert('L')
    return Image.merge('RGB', (g, g, g))

cut_patches('dog', 'fur_dog', 300, (9, 15), frames=list(range(2, 20)) + list(range(26, 46)), enhance=fur_soft)
cut_patches('lion', 'fur_lion', 160, (14, 26), enhance=fur_soft)
cut_patches('cat', 'fur_cat', 120, (18, 34), enhance=fur_soft)
# dark: tiger patches, keep only dark ones
def cut_dark(n):
    files = frame_files('tiger'); _, masks = shot('tiger')
    got = 0; tries = 0
    while got < n and tries < 20000:
        tries += 1
        fi = rng.randrange(len(files)); src = Image.open(files[fi]).convert('RGB')
        ps = rng.randint(10, 18)
        cx, cy = rng.randint(ps, src.width - ps), rng.randint(ps, src.height - ps)
        box = (cx - ps // 2, cy - ps // 2, cx - ps // 2 + ps, cy - ps // 2 + ps)
        m = mask_img(masks.get(str(fi), []), src.size).crop(box)
        if m.histogram()[255] < ps * ps * .97: continue
        p = src.crop(box).convert('L')
        if sum(i * c for i, c in enumerate(p.histogram())) / (ps * ps) > 70: continue
        p = Image.merge('RGB', (p, p, p)).resize((CELL, CELL), Image.LANCZOS).convert('RGBA')
        p.putalpha(torn_alpha(CELL, CELL))
        x, y = next_cell()
        put(f'dark_{got:03d}', p, x, y, 'dark', dict(src=rel(files[fi]), shot='tiger', frame=fi, crop=list(box), mask='SAM polygon, >=97% inside; mean luma <= 70', op='crop + torn alpha'))
        got += 1
    print('dark', got)
cut_dark(60)
# coat: the coats hanging at the left of the door shot (frames 0-12, x 0..90)
cut_patches('door', 'coat', 140, (14, 24), frames=list(range(0, 12)), inside=False, region=(0, 20, 95, 280), kind='square', enhance=grey_contrast)
cut_patches('cloud', 'sky', 60, (40, 70), inside=True, kind='round')
# stars: the star cut-out itself, whole, masked
def cut_star(n):
    files = frame_files('star'); _, masks = shot('star')
    for k in range(n):
        fi = 16 + k * 6
        src = Image.open(files[fi]).convert('RGB'); m = mask_img(masks.get(str(fi), []), src.size)
        bb = m.getbbox()
        p = src.crop(bb).convert('RGBA'); p.putalpha(m.crop(bb))
        p.thumbnail((CELL - 4, CELL - 4), Image.LANCZOS)
        cell = Image.new('RGBA', (CELL, CELL)); cell.paste(p, ((CELL - p.width) // 2, (CELL - p.height) // 2))
        x, y = next_cell()
        put(f'star_{k:02d}', cell, x, y, 'star', dict(src=rel(files[fi]), shot='star', frame=fi, crop=list(bb), mask='SAM polygon (whole object)', op='mask cut-out'))
cut_star(5)
# a soft round "core" disc and a hard dot, synthesized (fill under fragment clouds; contact shadows; light blobs)
def synth(name, img, cls, what):
    x, y = next_cell(); put(name, img, x, y, cls, dict(src='synthesized', op=what))
d = Image.new('L', (CELL, CELL), 0); ImageDraw.Draw(d).ellipse((3, 3, CELL - 4, CELL - 4), fill=255); d = d.filter(ImageFilter.GaussianBlur(5))
synth('soft', Image.merge('RGBA', (Image.new('L', d.size, 255),) * 3 + (d,)), 'synth', 'gaussian disc (shadows, light, fog)')
d2 = Image.new('L', (CELL, CELL), 0); ImageDraw.Draw(d2).ellipse((2, 2, CELL - 3, CELL - 3), fill=255)
synth('dot', Image.merge('RGBA', (Image.new('L', d.size, 255),) * 3 + (d2,)), 'synth', 'hard disc (eye glint, fill)')
sq = Image.new('RGBA', (CELL, CELL), (255, 255, 255, 255))
synth('white', sq, 'synth', 'solid white (tinted flats)')
sm = Image.new('L', (CELL, CELL), 0); ImageDraw.Draw(sm).rectangle((0, 0, CELL - 1, CELL - 1), fill=255)
cursor[0] = 0; cursor[1] += CELL

# ---------- wood strips 128x32 ----------
def cut_strips(cat, n, frames, region, horiz=True):
    files = frame_files(cat)
    for k in range(n):
        fi = rng.choice(frames); src = Image.open(files[fi]).convert('RGB')
        x0, y0, x1, y1 = region
        w, h = (rng.randint(70, 110), rng.randint(10, 16)) if horiz else (rng.randint(10, 16), rng.randint(70, 110))
        bx, by = rng.randint(x0, x1 - w), rng.randint(y0, y1 - h)
        p = fur_soft(src.crop((bx, by, bx + w, by + h)))
        if not horiz: p = p.rotate(90, expand=True)
        p = p.resize((128, 32), Image.LANCZOS).convert('RGBA')
        a = Image.new('L', (128, 32), 0); ImageDraw.Draw(a).polygon([(1, rng.randint(1, 4)), (127, rng.randint(1, 4)), (127, 31 - rng.randint(1, 4)), (1, 31 - rng.randint(1, 4))], fill=255)
        p.putalpha(a.filter(ImageFilter.GaussianBlur(.6)))
        x, y = cursor; cursor[0] += 128
        if cursor[0] + 128 > 2048: cursor[0] = 0; cursor[1] += 32
        put(f'wood_{len(CLASSES.get("wood", [])):03d}', p, x, y, 'wood', dict(src=rel(files[fi]), shot=cat, frame=fi, crop=[bx, by, bx + w, by + h], mask='none (region crop of rails/poles)', op='crop + straight cut'))
# horse shot: fence rails left part (x 0-120, y 0-140) frames 0-20; ladder poles: the ladder in ladder frames (vertical)
cut_strips('horse', 60, list(range(0, 20)), (0, 0, 130, 150))
cut_strips('ladder', 40, list(range(0, 6)), (40, 120, 200, 280))
cursor[0] = 0; cursor[1] += 40

# ---------- big pieces: simple shelf packer ----------
shelf = dict(x=0, y=cursor[1], h=0)
def place(img):
    if shelf['x'] + img.width > 2048:
        shelf['x'] = 0; shelf['y'] += shelf['h'] + 2; shelf['h'] = 0
    x, y = shelf['x'], shelf['y']; shelf['x'] += img.width + 2; shelf['h'] = max(shelf['h'], img.height)
    assert y + img.height <= 2048, 'atlas full'
    return x, y

def cut_object(cat, fi, name, maxsize, flip=False, which=None):
    files = frame_files(cat); _, masks = shot(cat)
    src = Image.open(files[fi]).convert('RGB')
    polys = masks.get(str(fi), [])
    if which is not None: polys = [polys[which]]
    m = mask_img(polys, src.size).filter(ImageFilter.GaussianBlur(.6))
    bb = m.getbbox()
    p = src.crop(bb).convert('RGBA'); p.putalpha(m.crop(bb))
    if flip: p = p.transpose(Image.FLIP_LEFT_RIGHT)
    p.thumbnail(maxsize, Image.LANCZOS)
    x, y = place(p)
    put(name, p, x, y, 'big', dict(src=rel(files[fi]), shot=cat, frame=fi, crop=list(bb), mask='SAM polygon', op='mask cut-out' + (' + mirrored' if flip else '')))

cut_object('hand', 20, 'hand', (300, 200), flip=True)        # the offered hand, mirrored to reach right
cut_object('lantern', 10, 'lantern', (110, 220))
cut_object('door', 31, 'doorleaf', (240, 470))
# the framed picture on the inside wall: a rectangular crop of the windmill shot
files = frame_files('windmill'); wf = Image.open(files[20]).convert('RGB')
pic = grey_contrast(wf.crop((40, 20, 344, 268))).resize((180, 146), Image.LANCZOS).convert('RGBA')
x, y = place(pic); put('picture', pic, x, y, 'big', dict(src=rel(files[20]), shot='windmill', frame=20, crop=[40, 20, 344, 268], mask='none (rectangle)', op='crop'))
# cloud bank strips for the horizon
cf = frame_files('cloud'); _, cm = shot('cloud')
for k in range(3):
    fi = 10 + k * 20; src = Image.open(cf[fi]).convert('RGB'); m = mask_img(cm.get(str(fi), []), src.size)
    p = src.convert('RGBA'); p.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
    p = p.crop(m.getbbox()); p.thumbnail((380, 200), Image.LANCZOS)
    fa = Image.new('L', p.size, 0); ImageDraw.Draw(fa).rectangle((14, 14, p.width - 15, p.height - 15), fill=255)
    fa = fa.filter(ImageFilter.GaussianBlur(10)); from PIL import ImageChops
    p.putalpha(ImageChops.multiply(p.getchannel('A'), fa))
    x, y = place(p); put(f'cloudbank_{k}', p, x, y, 'big', dict(src=rel(cf[fi]), shot='cloud', frame=fi, crop=list(m.getbbox()), mask='SAM polygon', op='mask cut-out'))

# ---------- Quick, Draw! chalk strokes ----------
def lines(path, n_max):
    out = []
    with open(path) as f:
        for ln in f:
            try: out.append(json.loads(ln))
            except Exception: break        # the last line of a .part file may be partial
            if len(out) >= n_max: break
    return out
used_qd = []
def chalk(d, name, size, cls='qd'):
    xs = [x for s in d['drawing'] for x in s[0]]; ys = [y for s in d['drawing'] for y in s[1]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    w, h = size; sc = min((w - 8) / max(1, x1 - x0), (h - 8) / max(1, y1 - y0))
    big = Image.new('L', (w * 3, h * 3), 0); dr = ImageDraw.Draw(big)
    for s in d['drawing']:
        pts = [((x - x0) * sc * 3 + 12, (y - y0) * sc * 3 + 12) for x, y in zip(s[0], s[1])]
        if len(pts) > 1: dr.line(pts, fill=255, width=7, joint='curve')
        for p in pts: dr.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=255)
    a = big.resize((w, h), Image.LANCZOS)
    img = Image.merge('RGBA', (Image.new('L', (w, h), 240), Image.new('L', (w, h), 236), Image.new('L', (w, h), 226), a))
    x, y = place(img)
    put(name, img, x, y, cls, dict(src='Quick, Draw! (' + d['word'] + ')', key_id=d['key_id'], countrycode=d.get('countrycode'), op='stroke raster (chalk)'))
    used_qd.append(dict(name=name, **d))

pick = {'moon': [3], 'tree': [5, 11], 'fence': [2], 'house': [7]}
for cat, ks in pick.items():
    L = lines(os.path.join(QD, cat + '.part'), 40)
    rec = [d for d in L if d.get('recognized')]
    for j, k in enumerate(ks):
        chalk(rec[k], f'qd_{cat}_{j}', (160, 160) if cat != 'fence' else (300, 120))
kitqd = [json.loads(l) for l in open(os.path.join(KIT, 'quickdraw/quickdraw.ndjson'))]
for j, k in enumerate([0, 4, 9, 13, 21, 30]):
    chalk(kitqd[k], f'qd_dog_{j}', (120, 96))

ATLAS.save(os.path.join(OUT, 'atlas.png'), optimize=True)
json.dump(dict(size=[2048, 2048], cell=CELL, classes=CLASSES, frames=FRAMES,
               about='SCION-26 texture atlas: every sprite in the film is one of these frames. src/frame/crop say where each was cut.'),
          open(os.path.join(OUT, 'atlas.json'), 'w'), indent=0)
with open(os.path.join(OUT, 'quickdraw_used.ndjson'), 'w') as f:
    for d in used_qd: f.write(json.dumps(d) + '\n')
print('frames', len(FRAMES), 'atlas used to y =', shelf['y'] + shelf['h'])
