"""Cutout fabricator: cuts every piece from its source print and writes build/cache/pieces/*.png and pieces.json.
All coordinates in the polygons are pixels of the 384x288 source frame named in each piece."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutlib import cut, CACHE, FOLDER, ROOT, PALETTES

KIT = os.path.join(ROOT, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
FOUND = {f['category']: f for f in json.load(open(os.path.join(KIT, 'found-frames.json')))}


def prov(cat, frame):
    if cat == 'dog':
        s = json.load(open(os.path.join(KIT, 'archive-dog/source.json')))['source']
        return {'source_title': s['source_title'], 'collection': s['original_collection'], 'archive_url': s['original_source_url'],
                'clip_id': s['clip_id'], 'shot_page': s['shot_page_url'], 'frame': frame, 'rights': s['rights_statement']}
    if cat == 'door':
        s = json.load(open(os.path.join(KIT, 'archive-door/source.json')))['source']
        return {'source_title': s['source_title'], 'archive_url': s['original_source_url'], 'clip_id': s['clip_id'],
                'shot_page': s['shot_page_url'], 'frame': frame, 'rights': s['rights_statement']}
    f = FOUND[cat]
    return {'source_title': f['source_title'], 'archive_url': f['source_url'], 'clip_id': f['clip_id'], 'frame': frame,
            'rights': f['rights'], 'kit_listing': 'paeleo/handmade/kit/found-frames.json'}


def dogf(i): return os.path.join(KIT, 'archive-dog/frames/f%03d.jpg' % i)
def doorf(i): return os.path.join(KIT, 'archive-door/frames/f%03d.jpg' % i)
def shot(cat, i): return os.path.join(SHOTS, cat + '-sam/frames/f%03d.jpg' % i)


DOGM = json.load(open(os.path.join(KIT, 'archive-dog/masks.json')))
DOORM = json.load(open(os.path.join(KIT, 'archive-door/masks.json')))
def mpolys(m, i): return [[tuple(p) for p in poly] for poly in m[str(i)]]

pieces = {}
def add(rec, **kw):
    rec.update(kw); pieces[rec['name']] = rec

# ---------------------------------------------------------------- the dog: one print (f006), cut into seven pieces
DS = 1.31   # print enlargement: 1 source px -> 1.31 screen px (dog ~1.0 m = 210 px at 210 px/m)
M6 = mpolys(DOGM, 6)
HEAD = [(82, 74), (120, 78), (136, 90), (145, 104), (138, 117), (120, 123), (104, 119), (92, 102), (82, 92)]
TORSO = [(108, 92), (166, 98), (240, 108), (242, 162), (226, 160), (220, 157), (205, 157), (198, 159), (186, 161),
         (156, 158), (146, 159), (134, 161), (120, 162), (108, 158)]
FORE = [(130, 146), (155, 146), (155, 207), (121, 207), (121, 194), (131, 188)]
FARFORE = [(116, 160), (131, 160), (131, 197), (116, 197)]
HIND = [(204, 146), (226, 146), (226, 207), (204, 207)]
FARHIND = [(183, 156), (205, 156), (205, 200), (183, 200)]
TAIL = [(236, 108), (290, 108), (290, 182), (236, 182)]
P6 = prov('dog', 6)
# regrade (repair 1): smooth scissor line along the matte, blotches blurred, contrast compressed, no sharpening
DG = dict(smooth_mask=2.2, soften=1.7, contrast=.62, wash_amp=.04, sharpen=False, stretch=(4, 96))
add(cut('dog_torso', dogf(6), [TORSO], DS, 'dog', M6, **DG, holes=[HEAD], seed=1, provenance=P6,
        pins={'neck': (128, 112), 'shoulder': (141, 150), 'farshoulder': (126, 154), 'hip': (213, 151), 'farhip': (198, 152),
              'tailroot': (238, 136), 'centre': (176, 135), 'belly': (176, 160)}), op='crop+matte+scissor cut+tint')
add(cut('dog_head', dogf(6), [HEAD, ('disc', 128, 112, 11)], DS, 'dog', M6, **DG, seed=2, provenance=P6,
        pins={'neck': (128, 112), 'nose': (88, 86), 'eye': (102, 92)}), op='crop+matte+scissor cut+tint')
add(cut('dog_fore', dogf(6), [FORE, ('disc', 141, 151, 11)], DS, 'dog', M6, **DG, seed=3, provenance=P6,
        pins={'shoulder': (141, 150), 'foot': (133, 201)}), op='crop+matte+scissor cut+tint')
add(cut('dog_farfore', dogf(6), [FARFORE, ('disc', 126, 156, 9)], DS, 'dogfar', M6, **DG, seed=4, provenance=P6,
        pins={'shoulder': (126, 154), 'foot': (123, 193)}), op='crop+matte+scissor cut+darker print')
add(cut('dog_hind', dogf(6), [HIND, ('disc', 213, 152, 11)], DS, 'dog', M6, **DG, seed=5, provenance=P6,
        pins={'hip': (213, 151), 'foot': (210, 202)}), op='crop+matte+scissor cut+tint')
add(cut('dog_farhind', dogf(6), [FARHIND, ('disc', 198, 154, 9)], DS, 'dogfar', M6, **DG, seed=6, provenance=P6,
        pins={'hip': (198, 152), 'foot': (191, 196)}), op='crop+matte+scissor cut+darker print')
add(cut('dog_tail', dogf(6), [TAIL, ('disc', 239, 136, 8)], DS, 'dog', M6, **DG, seed=7, provenance=P6,
        pins={'tailroot': (238, 136), 'tip': (282, 158)}), op='crop+matte+scissor cut+tint')
# the turning card: a second print, the same dog facing the camera with its head turning (f030), one whole piece
M30 = mpolys(DOGM, 30)
add(cut('dog_front', dogf(30), [[(130, 80), (230, 80), (230, 210), (130, 210)]], DS, 'dog', M30, **DG, seed=8, provenance=prov('dog', 30),
        pins={'feet': (178, 198), 'head': (192, 120)}), op='crop+matte+scissor cut+tint (substitution card for the turn)')

# the head lowered (f046: the same dog, walking, head down; printed facing right, flopped when laid facing left).
# Cut tight round skull, ear and muzzle, without the white collar: one unambiguous face.
M46 = mpolys(DOGM, 46)
add(cut('dog_head_low', dogf(46), [[(242, 134), (262, 136), (276, 156), (282, 176), (278, 192), (258, 194), (244, 186), (240, 160)]],
        DS, 'dog', M46, **DG, seed=9, provenance=prov('dog', 46),
        pins={'neck': (246, 152), 'nose': (278, 182), 'top': (252, 136)}), op='crop+matte+scissor cut+tint (substitute head card: head low)')

# the face (f030: the dog facing the camera, head turned, eyes and muzzle readable). Used when it looks back over its
# shoulder at the door: one unambiguous face. Printed looking right; flopped when the dog is laid facing left.
add(cut('dog_face', dogf(30), [[(146, 92), (170, 87), (200, 94), (214, 112), (219, 134), (206, 143), (180, 146), (156, 141), (146, 120)]],
        DS, 'dog', M30, **DG, seed=10, provenance=prov('dog', 30),
        pins={'neck': (176, 140), 'nose': (216, 128), 'top': (170, 88)}), op='crop+matte+scissor cut+tint (substitute head card: the face)')

# the back of the head (looking in): there is no print of it. Constructed: the outline of the f030 head (skull and ears,
# muzzle hidden) cut from the fur of the f006 back, i.e. a collage of two prints. Labelled as a constructed piece.
def back_of_head():
    """A head turned away into the room, seen from behind: skull and pricked ears cut from the f006 saddle fur, the ear
    tips folded over (a second layer of darker fur), and the tip of the muzzle - cut from f046's muzzle - showing past the
    skull on the side it is turned to."""
    from cutlib import ramp
    im = Image.open(dogf(6)).convert('RGB')
    W, H = 76, 80
    def fur(box, size, dark=1.0):
        f = im.crop(box).resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(1))
        L = np.asarray(f.convert('L')).astype(np.float32) / 255
        lo, hi = np.percentile(L, (4, 96)); L = np.clip((L - lo) / (hi - lo + 1e-6), 0, 1) * .62 + .14
        return ramp(L * dark, PALETTES['dog'])
    def mask(shapes):
        s = 4; m = Image.new('L', (W * s, H * s), 0); d = ImageDraw.Draw(m)
        for kind, pts in shapes:
            if kind == 'e': d.ellipse([v * s for v in pts], fill=255)
            else: d.polygon([(x * s, y * s) for x, y in pts], fill=255)
        return np.asarray(m.resize((W, H), Image.BOX)).astype(np.float32) / 255
    rgb = np.zeros((H, W, 3), np.float32); a = np.zeros((H, W), np.float32)
    def lay(col, al):
        nonlocal rgb, a
        rgb = rgb * (1 - al[..., None]) + col * al[..., None]; a = a + al * (1 - a)
    # muzzle tip from f046 (flopped: pointing left), behind the skull, sticking well out on the left (turned into the room)
    mz = Image.open(dogf(46)).convert('RGB').crop((260, 156, 282, 192)).transpose(Image.FLIP_LEFT_RIGHT).resize((30, 44), Image.BICUBIC)
    Lm = np.asarray(mz.convert('L')).astype(np.float32) / 255; lo, hi = np.percentile(Lm, (4, 96))
    mcol = np.zeros((H, W, 3), np.float32); mcol[28:72, 0:30] = ramp(np.clip((Lm - lo) / (hi - lo + 1e-6), 0, 1) * .7 + .25, PALETTES['dog'])
    lay(mcol, mask([('p', [(0, 50), (6, 40), (26, 36), (28, 62), (10, 64), (1, 58)])]))
    # skull, broad, on a thick neck
    lay(fur((150, 108, 204, 152), (W, H)), mask([('e', (12, 22, 66, 68)), ('p', [(16, 56), (64, 56), (70, 78), (12, 78)])]))
    # ears: broad-based, upright, the top third folded over outward (a dog's, not a cat's)
    lay(fur((160, 112, 200, 148), (W, H), .8), mask([('p', [(14, 38), (12, 12), (20, 6), (34, 26)]), ('p', [(64, 38), (66, 12), (58, 6), (44, 26)])]))
    lay(fur((160, 112, 200, 148), (W, H), .42), mask([('p', [(12, 12), (20, 6), (10, 24), (4, 22)]), ('p', [(66, 12), (58, 6), (68, 24), (74, 22)])]))
    # the parting of the fur down the back of the skull
    yy, xx = np.mgrid[0:H, 0:W]
    rgb *= (1 - .22 * np.exp(-((xx - 39) ** 2) / 14) * (yy > 26))[..., None]
    A = Image.fromarray((a * 255).astype(np.uint8)); er = np.asarray(A.filter(ImageFilter.MinFilter(3))).astype(np.float32) / 255
    e = np.clip(a - er, 0, 1)
    rgb = rgb * (1 - e[..., None] * .75) + np.array([.93, .9, .82]) * e[..., None] * .75
    fn = os.path.join(CACHE, 'pieces', 'dog_backhead.png')
    Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), 'RGBA').save(fn)
    return {'name': 'dog_backhead', 'file': os.path.relpath(fn, FOLDER), 'origin': [0, 0], 'size': [W, H], 'scale': 1,
            'pins': {'neck': [40, 74]}, 'palette': 'dog', 'source_print': os.path.relpath(dogf(6), ROOT),
            'provenance': prov('dog', 6), 'notes': 'constructed: skull and pricked, folded-tip ears cut from the f006 saddle fur; '
            'the muzzle tip is a scrap of f046 (flopped) showing past the skull', 'op': 'constructed collage of two prints'}
add(back_of_head())

# ---------------------------------------------------------------- the person: a collage, as the method does it
# head: Vision of the Wild f010 (a face looking down and to the right, in a white hat); jaw cut free and pinned
HS = 0.44
# the print faces down and to the LEFT: it is flopped (a mirrored print) on the table to face the dog
HEADP = [(206, 38), (250, 20), (262, 4), (383, 4), (383, 112), (383, 172), (350, 176), (300, 178), (252, 172),
         (240, 122), (216, 62)]
JAW = [(252, 172), (300, 178), (350, 176), (383, 172), (383, 234), (300, 236), (262, 214)]
PH = prov('hat', 10)
add(cut('person_head', shot('hat', 10), [HEADP], HS, 'skin', seed=11, provenance=PH, stretch=(1, 99.5),
        pins={'neck': (318, 232), 'jaw': (372, 170), 'mouth': (292, 186)}), op='crop+scissor cut+tint; flopped when laid')
add(cut('person_jaw', shot('hat', 10), [JAW], HS, 'skin', seed=12, provenance=PH, stretch=(1, 99.5),
        pins={'jaw': (372, 170)}), op='crop+scissor cut+tint (the chin, cut free and pinned at the ear)')
# body: Straight Talk f000, the smock and sleeves (seen from behind, used as a front: a collage liberty)
BS = 0.74
SMOCK = [(150, 172), (160, 122), (180, 103), (232, 88), (285, 88), (318, 103), (331, 150), (331, 192), (305, 196),
         (303, 262), (214, 268), (207, 190), (198, 180), (150, 180)]
add(cut('person_body', doorf(0), [SMOCK], BS, 'smock', seed=13, provenance=prov('door', 0),
        pins={'neck': (258, 90), 'shoulder': (305, 104), 'hip': (258, 250)}), op='crop+scissor cut+tint')
# legs: Straight Talk f013, the jeans, cut at the knee into thighs and shins (each a pair, as one card)
LS = 1.3
THIGH = [(196, 196), (250, 196), (247, 246), (229, 248), (223, 238), (217, 248), (199, 246)]
SHIN = [(199, 238), (220, 238), (218, 287), (202, 287)]
SHIN2 = [(226, 238), (247, 238), (244, 287), (229, 287)]
add(cut('person_thigh', doorf(13), [THIGH], LS, 'jeans', seed=14, provenance=prov('door', 13),
        pins={'hip': (223, 200), 'knee': (223, 242)}), op='crop+scissor cut+tint')
add(cut('person_shin', doorf(13), [SHIN, SHIN2], LS, 'jeans', seed=15, provenance=prov('door', 13),
        pins={'knee': (223, 242), 'ankle': (224, 287)}), op='crop+scissor cut+tint')
# arm: Door to Heaven f000, a forearm and hand (it held a card: the card is cut away)
AS = 0.62
ARM = [(186, 72), (205, 58), (260, 62), (330, 55), (383, 40), (383, 90), (300, 99), (270, 103), (220, 108), (186, 113),
       (178, 106), (192, 90)]
add(cut('person_arm', shot('hand', 0), [ARM], AS, 'skin', seed=16, provenance=prov('hand', 0), stretch=(1, 99.5),
        pins={'shoulder': (378, 64), 'hand': (196, 88)}), op='crop+scissor cut+tint')

# the giant hand (an absurd beat): a second, much larger print of the same forearm, as the method enlarges a found hand
add(cut('giant_hand', shot('hand', 0), [ARM], 1.9, 'skin', seed=17, provenance=prov('hand', 0), stretch=(1, 99.5),
        pins={'tip': (188, 100)}), op='crop+scissor cut+tint, enlarged print (the hand from above the table)')

# ---------------------------------------------------------------- the door: re-timed prints of a real door swinging
DOORS = [31, 27, 24, 22, 20]
for i in DOORS:
    add(cut('door_%02d' % i, doorf(i), mpolys(DOORM, i), 1.62, 'door', seed=20 + i, provenance=prov('door', i), stretch=(1, 99),
            pins={'hinge_top': (min(p[0] for poly in DOORM[str(i)] for p in poly), 0)}),
        op='crop+matte+tint (substitution set)')
# the door seen almost edge-on (fully open): a strip cut from the hinge side of f020
add(cut('door_edge', doorf(20), [[(110, 0), (128, 0), (128, 287), (110, 287)]], 1.62, 'door', DOORM and mpolys(DOORM, 20), seed=59,
        provenance=prov('door', 20), stretch=(1, 99), pins={}), op='crop+matte+narrow scissor strip (the open door, edge-on)')

# ---------------------------------------------------------------- the world
# stone pillar from the dog's own house (archive dog f000, the pillar at the right of the frame)
add(cut('pillar', dogf(0), [[(326, 10), (372, 10), (376, 200), (324, 200)]], 2.4, 'stone', seed=30, provenance=prov('dog', 0),
        pins={'base': (340, 200)}), op='crop+scissor cut+tint')
pieces['pillar']['scale_note'] = 'enlarged 2.4x'
# a window for the empty wall: the curtained glass of the same door print (Straight Talk f031)
add(cut('window', doorf(31), [[(142, 2), (206, 2), (206, 94), (142, 94)]], 1.6, 'door', seed=35, provenance=prov('door', 31),
        stretch=(1, 99), pins={}), op='crop+scissor cut+tint (the curtained glass of the door, reused as a window)')
# the lamp inside: Light Of Your Life B f012, the bulb (cut along its glass)
LB = mpolys(json.load(open(os.path.join(SHOTS, 'light-bulb-sam/masks.json'))), 12)
add(cut('bulb', shot('light-bulb', 12), [[(0, 0), (384, 0), (384, 288), (0, 288)]], 0.36, 'bulb', LB, seed=31,
        provenance=prov('light-bulb', 12), pins={'cap': (190, 288)}), op='crop+matte+tint')

def thresh_alpha(lo, hi, invert=False, blur=0.8):
    def f(crop, W, H):
        L = np.asarray(crop.convert('L').filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
        a = np.clip((L - lo) / (hi - lo), 0, 1)
        return 1 - a if invert else a
    return f
# trees on the horizon: Behind the Lens f000, cut along the print's own dark edge against its sky
add(cut('trees', shot('yoga', 0), [[(250, 60), (378, 60), (378, 215), (250, 215)]], 2.2, 'stone', seed=32,
        provenance=prov('yoga', 0), extra_alpha=thresh_alpha(.42, .52, invert=True), rim=0.0, pins={}),
    op='crop+cut along the print\'s tonal edge (silhouette)')
add(cut('trees2', shot('yoga', 24), [[(0, 80), (130, 80), (130, 215), (0, 215)]], 2.0, 'stone', seed=33,
        provenance=prov('yoga', 24), extra_alpha=thresh_alpha(.42, .52, invert=True), rim=0.0, pins={}),
    op='crop+cut along the print\'s tonal edge (silhouette)')
# a cloud: Top Of The Cloud f000, the cloud body cut from its blue sky
def cloud_alpha(crop, W, H):
    a = np.asarray(crop).astype(np.float32) / 255
    w = np.clip((a.min(axis=2) - .55) / .15, 0, 1)   # white = cloud, blue = sky
    return np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255
add(cut('cloud', shot('cloud', 0), [[(0, 90), (384, 90), (384, 230), (0, 230)]], 1.1, 'cloud', seed=34,
        provenance=prov('cloud', 0), extra_alpha=cloud_alpha, rim=0.0, sharpen=False, pins={}), op='crop+cut along tonal edge+tint')

# ---------------------------------------------------------------- drawn and cut from coloured card (my own)
def card(name, W, H, shapes, color, pins, notes, seed=0, grain=.08):
    s = 4
    m = Image.new('L', (W * s, H * s), 0); d = ImageDraw.Draw(m)
    for sh in shapes:
        if sh[0] == 'poly': d.polygon([(x * s, y * s) for x, y in sh[1]], fill=255)
        elif sh[0] == 'ellipse': d.ellipse([v * s for v in sh[1]], fill=255)
        elif sh[0] == 'rect': d.rectangle([v * s for v in sh[1]], fill=255)
    a = np.asarray(m.resize((W, H), Image.BOX)).astype(np.float32) / 255
    rng = np.random.default_rng(seed)
    n = np.asarray(Image.fromarray((rng.random((max(2, H // 6), max(2, W // 6))) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    fib = rng.normal(0, 1, (H, W)).astype(np.float32)
    rgb = np.array(color, np.float32)[None, None] / 255 * (1 + (n[..., None] - .5) * grain + fib[..., None] * .015)
    A = Image.fromarray((a * 255).astype(np.uint8)); er = np.asarray(A.filter(ImageFilter.MinFilter(3))).astype(np.float32) / 255
    e = np.clip(a - er, 0, 1)
    rgb = rgb * (1 - e[..., None] * .6) + np.array([.93, .9, .82]) * e[..., None] * .6
    fn = os.path.join(CACHE, 'pieces', name + '.png')
    Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), 'RGBA').save(fn)
    pieces[name] = {'name': name, 'file': os.path.relpath(fn, FOLDER), 'origin': [0, 0], 'size': [W, H], 'scale': 1,
                    'pins': pins, 'palette': 'card', 'source_print': None,
                    'provenance': {'source_title': 'drawn and cut for this film', 'rights': 'made here (CC0)'},
                    'notes': notes, 'op': 'drawn (coloured card, scissor cut)'}
card('shoes', 70, 22, [('poly', [(6, 4), (30, 4), (34, 16), (4, 18)]), ('poly', [(38, 4), (60, 4), (66, 16), (36, 18)])],
     (34, 26, 24), {'ankle': [35, 4]}, 'a pair of shoes, black card', seed=40)
card('crate', 96, 70, [('rect', (0, 0, 95, 69))], (118, 86, 56), {'top': [48, 0]}, 'a wooden crate to sit on, brown card', seed=41)
card('mouth', 30, 16, [('ellipse', (0, 0, 29, 15))], (26, 10, 12), {'c': [15, 6]}, 'black paper behind the hinged jaw', seed=43)
card('moon', 70, 70, [('ellipse', (1, 1, 68, 68))], (236, 226, 190), {}, 'the moon, a disc of cream card', seed=42, grain=.14)

json.dump(pieces, open(os.path.join(CACHE, 'pieces.json'), 'w'), indent=1)

# ---------------------------------------------------------------- the cutting sheet (a reconstruction drawing)
def sheet():
    from PIL import ImageFont
    F = os.path.join(ROOT, 'tools/paeleo/fonts/f14.woff2')
    font = ImageFont.truetype(F, 13)
    W, H = 1600, 1000
    S = Image.new('RGB', (W, H), (232, 226, 212)); d = ImageDraw.Draw(S)
    x, y, rowh = 20, 20, 0
    for k, r in pieces.items():
        p = Image.open(os.path.join(FOLDER, r['file']))
        sc = min(1.0, 260 / max(p.size))
        if k in ('trees', 'trees2', 'cloud'): sc = min(sc, .45)
        p2 = p.resize((max(1, int(p.width * sc)), max(1, int(p.height * sc))))
        if x + p2.width + 20 > W: x = 20; y += rowh + 40; rowh = 0
        S.paste(p2, (x, y), p2)
        for nm, (px, py) in r['pins'].items():
            qx = x + (px - r['origin'][0]) * sc; qy = y + (py - r['origin'][1]) * sc
            d.ellipse((qx - 3, qy - 3, qx + 3, qy + 3), outline=(170, 20, 20), width=2)
        pr = r['provenance']
        d.text((x, y + p2.height + 3), f"{k}  <- {pr.get('source_title','')[:22]} f{pr.get('frame','')}", fill=(40, 30, 30), font=font)
        x += max(p2.width, 200) + 24; rowh = max(rowh, p2.height)
    S.save(os.path.join(FOLDER, 'proof', 'cutting_sheet.jpg'), quality=88)
os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
sheet()
print(len(pieces), 'pieces')
