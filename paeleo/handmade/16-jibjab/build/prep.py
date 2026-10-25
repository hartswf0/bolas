"""SCION 16 JibJab: prepare the cast and the plates from rights-recorded material only.

Writes (all inside 16-jibjab/):
  cast/<cast>/<view>.png + ears, cast/manifest.json   face slots: three casts, each a set of head views with landmarks
  plates/fur.png      the body plate's fur, cut from the archive dog's own torso (Amateur Film New Jersey C, PD)
  plates/door.png     the door plate, rectified from Straight Talk f028 (NTIS, PD), the empty door with nobody in frame
  plates/qd.json      the Quick, Draw! drawings used (CC BY 4.0), kept whole with key_id
Card convention: 400 px per metre, y down, landmarks in card pixels. socket = where the card meets the collar.
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(HERE, '..', 'kit')
QD = '/home/user/hartswf0/quickdraw'
PPM = 400          # card pixels per metre
SS = 4             # supersampling for drawn casts
CW, CH = 280, 240  # card size in px (0.70 m x 0.60 m)
SOCK = (140, 170)  # socket position in card px

os.makedirs(os.path.join(HERE, 'cast'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'plates'), exist_ok=True)


def qd_line(cat, idx):
    lines = open(f'{QD}/{cat}.part').read().split('\n')[:-1]   # last line may be partial: dropped
    return json.loads(lines[idx])


QD_USED = {
    'dog_profile': ('dog', 240), 'dog_front': ('dog', 298), 'person_face': ('face', 13), 'moon': ('moon', 16),
}
qd = {}
for k, (cat, idx) in QD_USED.items():
    r = qd_line(cat, idx)
    qd[k] = {'category': cat, 'line_index_in_part_file': idx, 'key_id': r['key_id'], 'countrycode': r['countrycode'],
             'recognized': r['recognized'], 'drawing': r['drawing'], 'source': f'{QD}/{cat}.part',
             'rights': 'CC BY 4.0, Quick, Draw! dataset, Google Creative Lab and contributors'}
json.dump(qd, open(os.path.join(HERE, 'plates/qd.json'), 'w'))


def m2c(X, Y):
    """metres (x right, y up, socket origin) -> supersampled card px"""
    return ((SOCK[0] + X * PPM) * SS, (SOCK[1] - Y * PPM) * SS)


def blob(cx, cy, rx, ry, rnd, n=72, jit=0.025, rot=0.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        j = 1 + jit * (rnd.random() - .5) * 2
        x, y = rx * math.cos(a) * j, ry * math.sin(a) * j
        xr, yr = x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
        pts.append(m2c(cx + xr, cy + yr))
    return pts


def paper(draw, pts, fill, edge=(244, 233, 214), ew=5, outline=(43, 27, 16), ow=0):
    """a cut-paper piece: the white core shows at the cut edge"""
    draw.polygon(pts, fill=edge)
    # inset fill: shrink towards centroid
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    ins = []
    for x, y in pts:
        dx, dy = x - cx, y - cy; d = math.hypot(dx, dy) or 1
        ins.append((x - dx / d * ew, y - dy / d * ew))
    draw.polygon(ins, fill=fill)
    if ow:
        draw.line(pts + [pts[0]], fill=outline, width=ow)


def finish(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def shadowed(img, off=(3, 4), alpha=90):
    a = img.split()[3]
    sh = Image.new('RGBA', img.size, (20, 12, 8, 0))
    sh.putalpha(a.point(lambda v: v * alpha // 255).filter(ImageFilter.GaussianBlur(2)))
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, off)
    out.alpha_composite(img)
    return out


manifest = {'about': 'Face slots. Each cast fills the same five head views (L, BL, B; R and BR are mirrors) aligned at the socket '
                     'landmark to the collar of the one performance. Ears are a separate slot where the cast provides them.',
            'card_px_per_m': PPM, 'card_size': [CW, CH], 'socket': list(SOCK), 'casts': {}}

TAN, CREAM, BROWN, DARK, NOSE = (196, 138, 80), (236, 211, 168), (92, 58, 36), (43, 27, 16), (28, 20, 16)


# ---------------------------------------------------------------- cast C: paper (cut by this swarm)
def ear_piece(fill, length=0.19, width=0.085, seed=3, edge=(244, 233, 214)):
    rnd = random.Random(seed)
    W, H = int(0.24 * PPM), int(0.28 * PPM)
    im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # pivot at top centre; ear hangs down (teardrop)
    px, py = W / 2, 0.03 * PPM
    pts = []
    n = 60
    for i in range(n):
        a = 2 * math.pi * i / n
        # teardrop: narrow at top
        t = (1 - math.cos(a)) / 2  # 0 top .. 1 bottom
        r = width / 2 * (0.35 + 0.65 * math.sin(math.pi * min(1, t * 1.15)) ** .7)
        x = r * math.sin(a) * (1 + 0.04 * (rnd.random() - .5))
        y = length * t
        pts.append(((px + x * PPM) * SS, (py + y * PPM) * SS))
    paper(d, pts, fill, edge=edge, ew=4)
    return finish(im), [px, py]


def cast_paper():
    out = {}
    os.makedirs(os.path.join(HERE, 'cast/paper'), exist_ok=True)
    rnd = random.Random(16)
    views = {}
    # L : profile facing left
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper(d, blob(-0.15, 0.065, 0.115, 0.062, rnd, rot=0.08), CREAM)              # muzzle
    paper(d, blob(0.0, 0.115, 0.118, 0.108, rnd), TAN)                             # skull
    paper(d, blob(-0.105, 0.075, 0.075, 0.05, rnd, rot=0.1), CREAM, ew=0)        # muzzle front over skull
    paper(d, blob(-0.258, 0.095, 0.034, 0.026, rnd), NOSE, edge=(60, 45, 35), ew=2)
    d.line([m2c(-0.235, 0.035), m2c(-0.19, 0.022), m2c(-0.14, 0.03)], fill=DARK, width=7)   # mouth line
    paper(d, blob(-0.055, 0.14, 0.022, 0.024, rnd), (26, 18, 14), edge=(250, 245, 235), ew=5)  # eye
    d.ellipse([*m2c(-0.062, 0.152), *m2c(-0.05, 0.14)], fill=(250, 248, 240))
    paper(d, blob(-0.045, 0.19, 0.035, 0.012, rnd, rot=-0.2), BROWN, ew=0)        # brow
    views['L'] = {'img': im, 'nose': (-0.29, 0.09), 'ears': [{'piv': (0.035, 0.185), 'front': True, 'side': 1}]}
    # BL : three-quarter from behind, muzzle just showing at left
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper(d, blob(-0.14, 0.075, 0.075, 0.048, rnd, rot=0.12), CREAM)
    paper(d, blob(-0.19, 0.092, 0.024, 0.02, rnd), NOSE, edge=(60, 45, 35), ew=2)
    paper(d, blob(0.0, 0.12, 0.112, 0.11, rnd), TAN)
    paper(d, blob(0.02, 0.10, 0.07, 0.07, rnd), (176, 120, 68), ew=0)            # back of skull, darker
    views['BL'] = {'img': im, 'nose': (-0.215, 0.09), 'ears': [{'piv': (-0.07, 0.19), 'front': False, 'side': -1, 'scale': .85},
                                                              {'piv': (0.06, 0.19), 'front': True, 'side': 1}]}
    # B : the back of the head
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper(d, blob(0.0, 0.12, 0.108, 0.112, rnd), TAN)
    paper(d, blob(0.0, 0.085, 0.065, 0.07, rnd), (176, 120, 68), ew=0)
    views['B'] = {'img': im, 'nose': (0.0, 0.16), 'ears': [{'piv': (-0.08, 0.19), 'front': True, 'side': -1},
                                                           {'piv': (0.08, 0.19), 'front': True, 'side': 1}]}
    ear, epiv = ear_piece(BROWN)
    ear.save(os.path.join(HERE, 'cast/paper/ear.png'))
    for v, o in views.items():
        img = shadowed(finish(o['img']))
        img.save(os.path.join(HERE, f'cast/paper/{v}.png'))
        out[v] = {'png': f'cast/paper/{v}.png', 'socket': list(SOCK),
                  'nose': [SOCK[0] + o['nose'][0] * PPM, SOCK[1] - o['nose'][1] * PPM],
                  'ears': [{'png': 'cast/paper/ear.png', 'pivot_in_ear': epiv,
                            'at': [SOCK[0] + e['piv'][0] * PPM, SOCK[1] - e['piv'][1] * PPM],
                            'front': e['front'], 'side': e['side'], 'scale': e.get('scale', 1)} for e in o['ears']]}
    return {'name': 'Paper', 'style': 'cut paper, tan and cream, a white core at every cut edge',
            'made_by': 'cut by this swarm (synthesized: PIL polygons with a seeded jitter, seed 16)', 'rights': 'made here',
            'consent_and_likeness': 'not a likeness of any real animal or person', 'views': out,
            'ear_angles': {'flat': 62, 'hang': 8, 'prick': -38}}


# ---------------------------------------------------------------- cast B: doodle (two real people's drawings)
def strokes_to_card(drawing, keep, box_m, flip=False):
    """map quickdraw strokes (0..255) into card metres given box (x0, y0top, size_m)"""
    x0, ytop, size = box_m
    out = []
    for i in keep:
        xs, ys = drawing[i]
        pts = []
        for x, y in zip(xs, ys):
            X = x / 255 * size; Y = y / 255 * size
            if flip: X = size - X
            pts.append((x0 + X, ytop - Y))
        out.append(pts)
    return out


def doodle_img(polys_fill, lines, lw=9, fill=(250, 246, 236)):
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for poly in polys_fill:
        d.polygon([m2c(*p) for p in poly], fill=fill)
    # sticker border: dilate alpha, white
    a = im.split()[3].filter(ImageFilter.MaxFilter(17))
    base = Image.new('RGBA', im.size, (255, 255, 255, 0)); base.putalpha(a)
    base.alpha_composite(im)
    d = ImageDraw.Draw(base)
    for ln in lines:
        if len(ln) > 1:
            d.line([m2c(*p) for p in ln], fill=(22, 22, 26), width=lw, joint='curve')
        for p in (ln[0], ln[-1]):
            x, y = m2c(*p); d.ellipse([x - lw / 2, y - lw / 2, x + lw / 2, y + lw / 2], fill=(22, 22, 26))
    return base


def cast_doodle():
    os.makedirs(os.path.join(HERE, 'cast/doodle'), exist_ok=True)
    P = qd['dog_profile']['drawing']; F = qd['dog_front']['drawing']
    out = {}
    # L: dog 240 (NL) is a head in profile looking left. strokes 0 ear, 1 head, 2 eye, 3 mouth, 4 neck line (dropped: the collar is the neck)
    box = (-0.247, 0.245, 0.36)   # face fitting: the drawing's neck point (175,165) on the socket
    head = strokes_to_card(P, [1], box)[0]
    eye, mouth = strokes_to_card(P, [2, 3], box)
    earL = strokes_to_card(P, [0], box)[0]
    L = doodle_img([head], [head, eye, mouth])
    # the ear stroke becomes the ear slot: its own sticker with pivot at its top
    ex = [p[0] for p in earL]; ey = [p[1] for p in earL]
    top = max(earL, key=lambda p: p[1])
    out['L'] = {'img': L, 'nose': (min(p[0] for p in head), 0.12), 'ear_strokes': earL, 'ear_top': top}
    # B: dog 298 (US) is a face from the front. Strokes 0 head, 1 and 2 ears; the face strokes (3..9) are taken out:
    # the back of the head is the same person's drawing without its face.
    boxF = (-0.167, 0.275, 0.34)  # face fitting: the bottom of the head (125,227) just under the socket
    headF = strokes_to_card(F, [0], boxF)[0]
    e1 = strokes_to_card(F, [1], boxF)[0]; e2 = strokes_to_card(F, [2], boxF)[0]
    B = doodle_img([headF, e1, e2], [headF, e1, e2])
    out['B'] = {'img': B, 'nose': (0.0, 0.2)}
    # BL: the back of 298, with the tip of 240's muzzle showing past it at the left (a join of two drawings)
    snout = [p for p in head if p[0] < -0.16]
    snout = [(x - 0.02, y - 0.02) for x, y in snout]
    BLi = doodle_img([snout + [(-0.12, 0.05)], headF, e1, e2], [snout, headF, e1, e2])
    out['BL'] = {'img': BLi, 'nose': (min(p[0] for p in snout), 0.08)}
    views = {}
    for v, o in out.items():
        img = shadowed(finish(o['img']))
        img.save(os.path.join(HERE, f'cast/doodle/{v}.png'))
        views[v] = {'png': f'cast/doodle/{v}.png', 'socket': list(SOCK),
                    'nose': [SOCK[0] + o['nose'][0] * PPM, SOCK[1] - o['nose'][1] * PPM], 'ears': []}
    # ear slot for L (and R by mirror): the profile ear stroke as its own sticker
    ear = earL
    x0 = min(p[0] for p in ear); y1 = max(p[1] for p in ear)
    W, H = int(0.16 * PPM), int(0.32 * PPM)
    im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tx, ty = top
    loc = [((W / 2 + (x - tx) * PPM) * SS, (0.02 * PPM + (ty - y) * PPM) * SS) for x, y in ear]
    d.polygon(loc, fill=(250, 246, 236))
    a = im.split()[3].filter(ImageFilter.MaxFilter(17)); base = Image.new('RGBA', im.size, (255, 255, 255, 0)); base.putalpha(a)
    base.alpha_composite(im); d = ImageDraw.Draw(base); d.line(loc, fill=(22, 22, 26), width=9)
    finish(base).save(os.path.join(HERE, 'cast/doodle/ear.png'))
    views['L']['ears'] = [{'png': 'cast/doodle/ear.png', 'pivot_in_ear': [W / 2, 0.02 * PPM],
                           'at': [SOCK[0] + tx * PPM, SOCK[1] - ty * PPM], 'front': True, 'side': 1, 'scale': 1}]
    return {'name': 'Doodle', 'style': 'two strangers\' Quick, Draw! dogs as white stickers, black marker line',
            'made_by': 'Quick, Draw! dog key_id %s (NL, profile) and key_id %s (US, face; its face strokes removed for the back views)'
                       % (qd['dog_profile']['key_id'], qd['dog_front']['key_id']),
            'rights': 'CC BY 4.0, Google Creative Lab and contributors', 'consent_and_likeness': 'drawings, no likeness',
            'views': views, 'ear_angles': {'flat': 28, 'hang': 0, 'prick': -14}}


# ---------------------------------------------------------------- cast A: home movie (the archive dog's own face)
def cast_home():
    os.makedirs(os.path.join(HERE, 'cast/home'), exist_ok=True)
    fr = lambda i: Image.open(os.path.join(KIT, 'archive-dog/frames/f%03d.jpg' % i)).convert('L')
    # f038: the only frame where the dog's face reads (eye, nose, white blaze, collar): a 3/4 face looking right.
    # Mirrored, it looks left. Cut by hand along the head (this polygon), feathered; seam under the collar.
    src = fr(38)
    poly = [(193, 108), (203, 101), (214, 102), (226, 106), (236, 113), (241, 124), (242, 134), (238, 142), (228, 147),
            (216, 148), (206, 146), (199, 140), (194, 131), (191, 120)]
    m = Image.new('L', src.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.8))
    x0, y0, x1, y1 = 186, 96, 248, 152
    face = src.crop((x0, y0, x1, y1)); mm = m.crop((x0, y0, x1, y1))
    # lift contrast; sepia tint to sit on the body plate
    face = ImageOps.autocontrast(face, cutoff=1)
    sep = ImageOps.colorize(face, (30, 20, 12), (250, 226, 190))
    sep = sep.convert('RGBA'); sep.putalpha(mm)
    sep = ImageOps.mirror(sep)
    scale = 0.30 * PPM / (x1 - x0)              # face card is 0.30 m wide
    sep = sep.resize((int(sep.width * scale), int(sep.height * scale)), Image.LANCZOS)
    views = {}
    L = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    # socket: bottom-right of the mirrored face (where the neck was)
    ox, oy = SOCK[0] - int(sep.width * 0.62), SOCK[1] - int(sep.height * 0.92)
    L.alpha_composite(sep, (ox, oy))
    # landmark: nose in source at (232,132) -> mirrored local
    nx = ox + (x1 - 232) * scale; ny = oy + (132 - y0) * scale
    views['L'] = (L, (nx, ny))
    # back views: the same head's silhouette (mirrored crop), filled with the archive dog's own back fur (f008), darkened
    fur = fr(8).crop((128, 96, 200, 136)); fur = ImageOps.autocontrast(fur, cutoff=1)
    furc = ImageOps.colorize(fur, (24, 16, 10), (170, 130, 92)).resize((CW, CH), Image.LANCZOS).convert('RGBA')
    sil = Image.new('L', (CW, CH), 0)
    cx, cy = SOCK[0], SOCK[1] - int(0.12 * PPM)
    ImageDraw.Draw(sil).ellipse([cx - 0.105 * PPM, cy - 0.11 * PPM, cx + 0.105 * PPM, cy + 0.11 * PPM], fill=255)
    # ears of the home dog hang: cut from the same fur
    for s in (-1, 1):
        ImageDraw.Draw(sil).polygon([(cx + s * 0.06 * PPM, cy - 0.1 * PPM), (cx + s * 0.135 * PPM, cy - 0.02 * PPM),
                                     (cx + s * 0.13 * PPM, cy + 0.08 * PPM), (cx + s * 0.09 * PPM, cy + 0.06 * PPM)], fill=255)
    sil = sil.filter(ImageFilter.GaussianBlur(1.2))
    B = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); fb = furc.copy(); fb.putalpha(sil); B.alpha_composite(fb)
    views['B'] = (B, (cx, cy - 0.06 * PPM))
    # BL: the back, with the real face's muzzle edge just past it (the mirrored photo, cropped to its left third)
    BL = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    mz = sep.crop((0, 0, int(sep.width * 0.42), sep.height))
    BL.alpha_composite(mz, (cx - int(0.2 * PPM), oy + 6))
    BL.alpha_composite(fb, (8, 0))
    views['BL'] = (BL, (cx - 0.2 * PPM, oy + 6 + (132 - y0) * scale))
    out = {}
    for v, (img, nose) in views.items():
        img = shadowed(img, off=(2, 3), alpha=70)
        img.save(os.path.join(HERE, f'cast/home/{v}.png'))
        out[v] = {'png': f'cast/home/{v}.png', 'socket': list(SOCK), 'nose': [float(nose[0]), float(nose[1])], 'ears': []}
    return {'name': 'Home movie', 'style': 'the archive dog\'s own face, sepia, grain left in',
            'made_by': 'L: hand-cut from Amateur Film New Jersey C f038 (the only legible face, a 3/4 view, mirrored). '
                       'B/BL: no frame shows the back of its head; built as a silhouette filled with its own back fur from f008.',
            'rights': 'public domain (Home Movies collection, Internet Archive: https://archive.org/details/NewJerseyC)',
            'consent_and_likeness': 'an animal in a public-domain home movie; no person\'s face is used', 'views': out,
            'ear_angles': None}


manifest['casts']['paper'] = cast_paper()
manifest['casts']['doodle'] = cast_doodle()
manifest['casts']['home'] = cast_home()
json.dump(manifest, open(os.path.join(HERE, 'cast/manifest.json'), 'w'), indent=1)

# ---------------------------------------------------------------- body plate fur (the archive dog's torso)
f8 = Image.open(os.path.join(KIT, 'archive-dog/frames/f008.jpg')).convert('L')
t = ImageOps.autocontrast(f8.crop((130, 100, 194, 132)), cutoff=2)
tile = Image.new('L', (128, 64))
tile.paste(t, (0, 0)); tile.paste(ImageOps.mirror(t), (64, 0))
tile = tile.resize((256, 128), Image.BICUBIC)
arr = np.asarray(tile).astype(float)
arr = 150 + (arr - arr.mean()) * 0.55
Image.fromarray(np.clip(arr, 0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(HERE, 'plates/fur.png'))

# ---------------------------------------------------------------- door plate (Straight Talk f028; the door, closed, nobody in frame)
door = np.asarray(Image.open(os.path.join(KIT, 'archive-door/frames/f028.jpg')).convert('RGB')).astype(float)
TL, TR, BR, BL = np.array([111, 2.]), np.array([235, 0.]), np.array([212, 284.]), np.array([122, 262.])
W, H = 150, 360
uu, vv = np.meshgrid(np.linspace(0.03, 0.97, W), np.linspace(0.0, 0.985, H))
P = (1 - uu)[..., None] * (1 - vv)[..., None] * TL + uu[..., None] * (1 - vv)[..., None] * TR + \
    uu[..., None] * vv[..., None] * BR + (1 - uu)[..., None] * vv[..., None] * BL
xi = np.clip(P[..., 0], 0, 383); yi = np.clip(P[..., 1], 0, 287)
x0 = np.floor(xi).astype(int); y0 = np.floor(yi).astype(int); x1 = np.minimum(x0 + 1, 383); y1 = np.minimum(y0 + 1, 287)
fx = (xi - x0)[..., None]; fy = (yi - y0)[..., None]
img = door[y0, x0] * (1 - fx) * (1 - fy) + door[y0, x1] * fx * (1 - fy) + door[y1, x0] * (1 - fx) * fy + door[y1, x1] * fx * fy
Image.fromarray(np.clip(img, 0, 255).astype('uint8')).save(os.path.join(HERE, 'plates/door.png'))
print('prep ok')
