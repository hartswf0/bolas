"""SCION 16 JibJab, round 2: the body plate, cut from the archive dog's own footage (Amateur Film New Jersey C, PD).

Two kinds of plate, both graded the same way (duotone, the film's own grain left in), both headless (the head is the face slot):
  rig pieces   cut from f008 (profile, walking left) and f012 (its tail): torso, neck, foreleg upper/lower, two hind legs,
               tail. Re-posed on the performance by two-point affine maps (pivot -> pivot). Far-side foreleg = the near one,
               darkened (recorded as a duplicate).
  turn plates  whole cut-outs of the frames in which the real dog turned from facing left, through facing the camera, to
               facing right (f016 .. f044): re-timed, they are the turns. Their heads are matted out at the pose keys.
Writes plates/rig/*.png, plates/turn/*.png, plates/plate.json (pivots in piece px; piece px = source px x UP).
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(HERE, '..', 'kit', 'archive-dog')
M = json.load(open(os.path.join(KIT, 'masks.json')))
K = json.load(open(os.path.join(KIT, 'pose_agent_v8.json')))
UP = 2
os.makedirs(os.path.join(HERE, 'plates/rig'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'plates/turn'), exist_ok=True)


def frame(i): return Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % i)).convert('L')


def mask(i):
    m = Image.new('L', (384, 288), 0); d = ImageDraw.Draw(m)
    for p in M[str(i)]: d.polygon([tuple(q) for q in p], fill=255)
    return m


def grade(g):
    """the plate grade: the home movie's own tones, mapped to a warm duotone that sits in the dusk"""
    g = ImageOps.autocontrast(g, cutoff=1)
    return ImageOps.colorize(g, black=(22, 16, 13), white=(232, 206, 168), mid=(128, 96, 70))


def cut(i, poly=None, extra_mask=None, feather=0.7, src=None):
    g = src if src is not None else frame(i)
    m = mask(i)
    if poly is not None:
        pm = Image.new('L', m.size, 0); ImageDraw.Draw(pm).polygon(poly, fill=255)
        m = ImageChops.multiply(m, pm)
    if extra_mask is not None: m = ImageChops.multiply(m, extra_mask)
    m = m.filter(ImageFilter.GaussianBlur(feather))
    bb = m.getbbox()
    x0, y0, x1, y1 = bb[0] - 2, bb[1] - 2, bb[2] + 2, bb[3] + 2
    rgb = grade(g).convert('RGBA'); rgb.putalpha(m)
    piece = rgb.crop((x0, y0, x1, y1)).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS)
    return piece, (x0, y0)


meta = {'about': __doc__, 'up': UP, 'source': 'paeleo/handmade/kit/archive-dog (Amateur Film New Jersey C, public domain)', 'rig': {}, 'turn': []}


def piece(name, i, poly, pivots, **kw):
    im, (x0, y0) = cut(i, poly, **kw)
    im.save(os.path.join(HERE, f'plates/rig/{name}.png'))
    meta['rig'][name] = {'png': f'plates/rig/{name}.png', 'frame': i,
                         'pivots': {k: [(x - x0) * UP, (y - y0) * UP] for k, (x, y) in pivots.items()}}


# f008: profile, walking left (pose keys nose 80,85 neck 100,105 chest 110,130 tail 220,130; feet f1 95,185 f2 130,200 h2 200,190)
piece('torso', 8, [(106, 96), (136, 96), (166, 103), (200, 109), (222, 127), (227, 141), (221, 162), (205, 166), (186, 160),
                   (150, 159), (134, 162), (112, 152), (102, 130)], {'shoulder': (124, 140), 'hip': (200, 140)})
piece('neck', 8, [(101, 97), (117, 94), (129, 112), (131, 136), (116, 141), (105, 120)], {'base': (122, 134), 'collar': (106, 102)})
piece('fore_upper', 8, [(109, 138), (135, 140), (135, 174), (117, 174)], {'top': (123, 144), 'knee': (126, 170)})
piece('fore_lower', 8, [(115, 164), (137, 164), (139, 204), (122, 205)], {'knee': (126, 168), 'foot': (131, 199)})
piece('hind_near', 8, [(202, 146), (222, 146), (220, 205), (202, 205)], {'top': (211, 150), 'foot': (210, 200)})
piece('hind_far', 8, [(181, 152), (204, 152), (202, 205), (180, 205)], {'top': (195, 156), 'foot': (190, 198)})
piece('tail', 6, [(212, 116), (230, 126), (263, 136), (268, 161), (244, 162), (224, 153), (211, 141)], {'base': (218, 132), 'tip': (262, 152)})

# the turn: the real dog's own turn, re-timed. yaw labels: 180 faces left, 270 faces the camera, 360 faces right
TURN = [(16, 205), (20, 228), (26, 252), (28, 270), (32, 290), (36, 308), (40, 326), (44, 345)]
for i, yaw in TURN:
    k = K[str(i)]
    nose, neck = k['nose'], k['neck']
    c = (nose[0] * 0.55 + neck[0] * 0.45, nose[1] * 0.55 + neck[1] * 0.45)
    r = 0.62 * math.hypot(nose[0] - neck[0], nose[1] - neck[1]) + 11
    disc = Image.new('L', (384, 288), 0); ImageDraw.Draw(disc).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    # the head is matted out by filling its disc from the surrounding coat (blur-fill inpaint); the slot sits on top
    above = Image.new('L', (384, 288), 0); ImageDraw.Draw(above).rectangle([0, 0, 384, neck[1] + 4], fill=255)
    gone = ImageChops.multiply(disc, above).filter(ImageFilter.GaussianBlur(1.2))
    hm = ImageOps.invert(gone)
    g = frame(i); keep = ImageChops.multiply(mask(i), ImageOps.invert(disc))
    import numpy as np
    G = np.asarray(g).astype(float); Kp = np.asarray(keep).astype(float) / 255
    num, den = G * Kp, Kp.copy()
    def box(A, r=5):
        k = np.ones(2 * r + 1) / (2 * r + 1)
        A = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 0, A)
        return np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 1, A)
    for _ in range(10):
        num, den = box(num, 7), box(den, 7)
    fill = num / np.maximum(den, 1e-3)
    D = np.asarray(disc).astype(float) / 255
    Gf = G * (1 - D) + fill * D
    src = Image.fromarray(np.clip(Gf, 0, 255).astype('uint8'))
    im, (x0, y0) = cut(i, src=src)          # the head's place is filled with coat; the face slot covers it
    m = mask(i); bb = m.getbbox()
    feet = [k[f] for f in ('f1', 'f2', 'h1', 'h2')]
    fy = max(p[1] for p in feet); fx = sum(p[0] for p in feet) / 4
    im.save(os.path.join(HERE, f'plates/turn/f{i:03d}.png'))
    meta['turn'].append({'png': f'plates/turn/f{i:03d}.png', 'frame': i, 'yaw': yaw,
                         'feet': [(fx - x0) * UP, (fy - y0) * UP], 'neck': [(neck[0] - x0) * UP, (neck[1] - y0) * UP],
                         'head_removed': {'c': [(c[0] - x0) * UP, (c[1] - y0) * UP], 'r': r * UP}})
json.dump(meta, open(os.path.join(HERE, 'plates/plate.json'), 'w'), indent=1)
print('plate ok', len(meta['rig']), 'rig pieces', len(meta['turn']), 'turn plates')
