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
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

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
    # F : from the front (seen only mid-turn and when it looks back over its shoulder)
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper(d, blob(0.0, 0.12, 0.108, 0.11, rnd), TAN)
    paper(d, blob(0.0, 0.06, 0.072, 0.052, rnd), CREAM)
    paper(d, blob(0.0, 0.085, 0.03, 0.022, rnd), NOSE, edge=(60, 45, 35), ew=2)
    for sx in (-1, 1):
        paper(d, blob(sx * 0.045, 0.145, 0.02, 0.022, rnd), (26, 18, 14), edge=(250, 245, 235), ew=5)
    d.line([m2c(-0.03, 0.035), m2c(0, 0.045), m2c(0.03, 0.035)], fill=DARK, width=6)
    views['F'] = {'img': im, 'nose': (0.0, 0.085), 'ears': [{'piv': (-0.085, 0.18), 'front': True, 'side': -1},
                                                            {'piv': (0.085, 0.18), 'front': True, 'side': 1}]}
    # FL : three-quarter from the front, looking left
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper(d, blob(0.01, 0.12, 0.11, 0.108, rnd), TAN)
    paper(d, blob(-0.075, 0.065, 0.085, 0.055, rnd, rot=0.05), CREAM)
    paper(d, blob(-0.15, 0.088, 0.03, 0.023, rnd), NOSE, edge=(60, 45, 35), ew=2)
    paper(d, blob(-0.065, 0.145, 0.019, 0.022, rnd), (26, 18, 14), edge=(250, 245, 235), ew=5)
    paper(d, blob(0.025, 0.15, 0.017, 0.02, rnd), (26, 18, 14), edge=(250, 245, 235), ew=4)
    views['FL'] = {'img': im, 'nose': (-0.17, 0.088), 'ears': [{'piv': (-0.06, 0.19), 'front': False, 'side': -1, 'scale': .85},
                                                               {'piv': (0.075, 0.185), 'front': True, 'side': 1}]}
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


def doodle_img(polys_fill, lines, lw=9, fill=(214, 200, 178)):
    im = Image.new('RGBA', (CW * SS, CH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for poly in polys_fill:
        d.polygon([m2c(*p) for p in poly], fill=fill)
    # sticker border: dilate alpha, white
    a = im.split()[3].filter(ImageFilter.MaxFilter(17))
    base = Image.new('RGBA', im.size, (226, 214, 194, 0)); base.putalpha(a)
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
    # F and FL: the same stranger's face drawing whole (its features back in)
    feats = strokes_to_card(F, list(range(3, len(F))), boxF)
    Fi = doodle_img([headF, e1, e2], [headF, e1, e2] + feats)
    out['F'] = {'img': Fi, 'nose': (0.0, 0.1)}
    out['FL'] = {'img': Fi.copy(), 'nose': (0.0, 0.1)}
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
    d.polygon(loc, fill=(214, 200, 178))
    a = im.split()[3].filter(ImageFilter.MaxFilter(17)); base = Image.new('RGBA', im.size, (226, 214, 194, 0)); base.putalpha(a)
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
    """every view from the archive dog's own frames, graded like the body plate, at its scale (2 card px per source px)"""
    import numpy as np
    os.makedirs(os.path.join(HERE, 'cast/home'), exist_ok=True)
    KD = os.path.join(KIT, 'archive-dog')
    MK = json.load(open(os.path.join(KD, 'masks.json')))
    fr = lambda i: Image.open(os.path.join(KD, 'frames/f%03d.jpg' % i)).convert('L')
    def fmask(i):
        m = Image.new('L', (384, 288), 0); d = ImageDraw.Draw(m)
        for p in MK[str(i)]: d.polygon([tuple(q) for q in p], fill=255)
        return m
    def grade(g):
        g = ImageOps.autocontrast(g, cutoff=1)
        return ImageOps.colorize(g, black=(22, 16, 13), white=(232, 206, 168), mid=(128, 96, 70))
    def cutp(i, poly, use_mask=True, src=None):
        g = src if src is not None else fr(i)
        m = Image.new('L', (384, 288), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        if use_mask: m = ImageChops.multiply(m, fmask(i))
        m = m.filter(ImageFilter.GaussianBlur(0.7))
        rgb = grade(g).convert('RGBA'); rgb.putalpha(m)
        return rgb
    def place(rgba, sock_src, rot=0, mirror=False):
        """source-px image -> card: 2x, socket on SOCK, rotated about the socket"""
        big = rgba.resize((384 * 2, 288 * 2), Image.LANCZOS)
        sx, sy = sock_src[0] * 2, sock_src[1] * 2
        if mirror:
            big = ImageOps.mirror(big); sx = 768 - sx
        big = big.rotate(rot, resample=Image.BICUBIC, center=(sx, sy))
        card = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        card.alpha_composite(big.crop((int(sx - SOCK[0]), int(sy - SOCK[1]), int(sx - SOCK[0]) + CW, int(sy - SOCK[1]) + CH)))
        return card
    views = {}
    # L: f008, the head in profile (it looks up at the person); turned 24 degrees down to sit level in the slot
    L = cutp(8, [(76, 72), (101, 70), (119, 83), (124, 104), (113, 114), (99, 111), (84, 96)])
    views['L'] = (place(L, (110, 106), rot=24), (-0.12, 0.13))
    # FR: f038, the one legible face (eye, nose, white blaze), three-quarter looking right; FL is its mirror
    FR = cutp(38, [(193, 108), (203, 101), (214, 102), (226, 106), (236, 113), (241, 124), (242, 134), (238, 142), (228, 147),
                   (216, 148), (206, 146), (199, 140), (194, 131), (191, 120)], use_mask=False)
    views['FL'] = (place(FR, (205, 146), mirror=True), (-0.1, 0.06))
    # F: f028, the face toward the camera (head lowered)
    Fi = cutp(28, [(158, 98), (176, 92), (194, 98), (199, 114), (195, 132), (184, 141), (170, 141), (160, 130), (155, 114)])
    views['F'] = (place(Fi, (177, 142)), (0.0, 0.06))
    # B: no frame shows the back of its head. The f028 head (crown and both ears) with its face filled from its own coat
    g = np.asarray(fr(28)).astype(float)
    face = Image.new('L', (384, 288), 0); ImageDraw.Draw(face).ellipse([166, 108, 190, 140], fill=255)
    D = np.asarray(face.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    crown = g[96:106, 166:190].mean()
    rng = np.random.default_rng(28)
    tex = crown + rng.normal(0, 10, g.shape)
    gb = g * (1 - D) + tex * D * 0.85 + g * D * 0.15
    B = cutp(28, [(158, 98), (176, 92), (194, 98), (199, 114), (195, 132), (184, 141), (170, 141), (160, 130), (155, 114)],
             src=Image.fromarray(np.clip(gb, 0, 255).astype('uint8')))
    views['B'] = (place(B, (177, 142)), (0.0, 0.12))
    # BL: the back, with the profile's muzzle tip showing past it at the left
    BLc = place(B, (177, 142)).copy()
    tip = place(L, (110, 106), rot=24)
    tipm = Image.new('L', (CW, CH), 0); ImageDraw.Draw(tipm).rectangle([0, 0, SOCK[0] - 40, CH], fill=255)
    ta = ImageChops.multiply(tip.split()[3], tipm); tip.putalpha(ta)
    BLi = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); BLi.alpha_composite(tip, (-12, 6)); BLi.alpha_composite(BLc, (8, 0))
    views['BL'] = (BLi, (-0.2, 0.1))
    out = {}
    for v, (img, nose) in views.items():
        img = shadowed(img, off=(2, 3), alpha=60)
        img.save(os.path.join(HERE, f'cast/home/{v}.png'))
        out[v] = {'png': f'cast/home/{v}.png', 'socket': list(SOCK), 'nose': [SOCK[0] + nose[0] * PPM, SOCK[1] - nose[1] * PPM], 'ears': []}
    return {'name': 'Home movie', 'style': 'the archive dog\'s own head, graded and grained like its body plate, at the plate\'s scale',
            'made_by': 'L: f008 head (profile, rotated 24 deg). FL/FR: f038 face (mirrored for FL). F: f028 head. '
                       'B: f028 head with the face filled from its own crown coat (no frame shows the back of its head). BL: B + the L muzzle tip.',
            'rights': 'public domain (Home Movies collection, Internet Archive: https://archive.org/details/NewJerseyC)',
            'consent_and_likeness': 'an animal in a public-domain home movie; no person\'s face is used', 'views': out,
            'ear_angles': None, 'card_px_per_source_px': 2}


manifest['casts']['paper'] = cast_paper()
manifest['casts']['doodle'] = cast_doodle()
manifest['casts']['home'] = cast_home()
json.dump(manifest, open(os.path.join(HERE, 'cast/manifest.json'), 'w'), indent=1)

# (round 1's fur tile is gone: the body plate is now cut from the footage itself, build/plate.py)

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
