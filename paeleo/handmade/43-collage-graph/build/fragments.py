"""SCION 43 · stage 1 · ARCHIVE FORAGER + MATTE: cut every typed fragment from rights-recorded found footage.

Each fragment = (source frame, my scissors polygon, optional SAM mask intersection, optional luminance key, optional flip).
Output: build/cache/frags/<id>.png (RGBA, tone-normalised, with a thin cut-paper edge) and build/cache/frags.json
(fragment pixel size, anchors in fragment pixels, provenance). Nothing here is drawn except the scissors lines
(cut polygons), which are recorded with each fragment.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
KIT = os.path.join(ROOT, 'paeleo/handmade/kit')
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
OUT = os.path.join(HERE, 'cache/frags')
os.makedirs(OUT, exist_ok=True)

DOGSRC = {'shot': 'archive-dog', 'title': 'Amateur Film New Jersey C', 'collection': 'Home Movies (Internet Archive)',
          'url': 'https://archive.org/details/NewJerseyC', 'rights': 'public_domain'}
DOORSRC = {'shot': 'archive-door', 'title': 'Straight Talk (NTIS, 1992)', 'url': 'https://archive.org/details/gov.ntis.ava19144vnb1',
           'rights': 'public_domain'}
HANDSRC = {'shot': 'hand-sam', 'title': 'Door to Heaven, The', 'url': 'https://archive.org/details/DoortoHe1941', 'rights': 'public_domain'}
LANSRC = {'shot': 'lantern-sam', 'title': 'Anthracite: Pre-Shift Examinations of Underground Mines', 'url': 'https://archive.org/details/gov.msha.dvd614', 'rights': 'public_domain'}
BULBSRC = {'shot': 'light-bulb-sam', 'title': 'Light Of Your Life B', 'url': 'https://archive.org/details/LightOfYourL_2', 'rights': 'public_domain'}
FACESRC = {'shot': 'face-sam', 'title': 'We Learn About the Telephone I', 'url': 'https://archive.org/details/WeLearnA1965', 'rights': 'public_domain'}
CLOUDSRC = {'shot': 'cloud-sam', 'title': 'Top Of The Cloud - Time Lapse (Wide Screen 16:9)', 'url': 'https://archive.org/details/CEP391', 'rights': 'public_domain'}


def frame_path(src, i):
    if src['shot'] in ('archive-dog', 'archive-door'):
        return os.path.join(KIT, src['shot'], 'frames', 'f%03d.jpg' % i)
    return os.path.join(SHOTS, src['shot'], 'frames', 'f%03d.jpg' % i)


def masks_of(src):
    p = os.path.join(KIT, src['shot'], 'masks.json') if src['shot'] in ('archive-dog', 'archive-door') else os.path.join(SHOTS, src['shot'], 'masks.json')
    return json.load(open(p))


_MC = {}


def sam(src, i):
    if src['shot'] not in _MC: _MC[src['shot']] = masks_of(src)
    return _MC[src['shot']].get(str(i), [])


# ---------------------------------------------------------------- fragment specs (the scissors)
# anchors are in SOURCE pixels; 'cut' polygon in source pixels; 'sam': intersect with SAM mask polygons of that frame
D = 'dog'
SPECS = [
    # --- DOG: every piece from the one home-movie dog (identity invariant: source == archive-dog)
    dict(id='torso_f006', type='dog.torso', src=DOGSRC, f=6, sam=True,
         cut=[(104, 128), (116, 112), (130, 102), (150, 96), (186, 106), (214, 110), (222, 118), (222, 166), (196, 166), (150, 164), (112, 164), (102, 140)],
         anchors=dict(S=(126, 142), H=(198, 140), N=(112, 116), T=(214, 121))),
    dict(id='head_alert_f006', type='dog.head', tags=['alert', 'up'], src=DOGSRC, f=6, sam=True,
         cut=[(68, 66), (120, 66), (124, 100), (118, 126), (96, 126), (68, 104)],
         anchors=dict(neck=(112, 116), nose=(82, 82))),
    dict(id='head_level_f012', type='dog.head', tags=['level'], src=DOGSRC, f=12, sam=True,
         cut=[(58, 72), (108, 72), (112, 108), (104, 128), (72, 124), (58, 104)],
         anchors=dict(neck=(102, 114), nose=(68, 96))),
    dict(id='head_low_f048', type='dog.head', tags=['low', 'collar'], src=DOGSRC, f=48, sam=True, flip=True,
         cut=[(220, 116), (292, 116), (292, 200), (220, 200)],
         anchors=dict(neck=(229, 132), nose=(281, 182))),
    # legs: narrow scissor strips along each found leg (f012, the dog mid-stride toward its person)
    dict(id='fore_a_f012', type='dog.leg.fore', src=DOGSRC, f=12, sam=True,
         cut=[(104, 146), (123, 148), (117, 172), (107, 193), (93, 193), (101, 170)], anchors=dict(top=(113, 152), foot=(99, 190))),
    dict(id='fore_b_f012', type='dog.leg.fore', src=DOGSRC, f=12, sam=True,
         cut=[(129, 150), (147, 150), (149, 180), (145, 204), (132, 204), (130, 180)], anchors=dict(top=(138, 155), foot=(139, 200))),
    dict(id='hind_a_f012', type='dog.leg.hind', src=DOGSRC, f=12, sam=True,
         cut=[(177, 148), (199, 148), (197, 175), (196, 201), (181, 201), (179, 175)], anchors=dict(top=(188, 153), foot=(189, 198))),
    dict(id='hind_b_f012', type='dog.leg.hind', tags=['bent'], src=DOGSRC, f=12, sam=True,
         cut=[(164, 148), (184, 150), (178, 170), (163, 188), (148, 188), (157, 170)], anchors=dict(top=(174, 155), foot=(155, 184))),
    dict(id='tail_f006', type='dog.tail', src=DOGSRC, f=6, sam=True,
         cut=[(206, 112), (220, 115), (236, 127), (250, 139), (254, 145), (249, 148), (236, 142), (220, 134), (206, 130)],
         anchors=dict(base=(213, 121), tip=(250, 145))),  # tapered along the found tail
    # the torso is SPLIT into two typed nodes (chest, haunch) so that the threshold can cut the dog in half materially
    dict(id='chest_f006', type='dog.chest', tags=['shade'], src=DOGSRC, f=6, sam=True,
         cut=[(102, 130), (116, 112), (130, 102), (180, 96), (180, 168), (100, 168)], feather=(180, 28, -1), anchors=dict(S=(126, 142), H=(198, 140), M=(160, 128), N=(112, 116))),
    dict(id='haunch_f006', type='dog.haunch', tags=['shade'], src=DOGSRC, f=6, sam=True,
         cut=[(128, 100), (150, 94), (214, 108), (224, 118), (224, 168), (128, 168)], anchors=dict(S=(126, 142), H=(198, 140), M=(160, 128), T=(214, 121))),
    # SUN set: the same dog a few seconds later, in sunlight at its bowl (f045), mirrored to face the door
    dict(id='chest_f045', type='dog.chest', tags=['sun', 'collar'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(174, 112), (226, 110), (240, 118), (247, 130), (245, 170), (174, 172)], feather=(174, 28, 1), anchors=dict(S=(221, 152), H=(158, 146), M=(194, 134), N=(234, 118))),
    dict(id='haunch_f045', type='dog.haunch', tags=['sun'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(136, 108), (226, 112), (226, 170), (136, 170)], anchors=dict(S=(221, 152), H=(158, 146), M=(194, 134), T=(147, 128))),
    dict(id='torso_f045', type='dog.torso', tags=['sun', 'collar'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(136, 108), (190, 110), (226, 110), (247, 128), (242, 168), (136, 168)], anchors=dict(S=(221, 152), H=(158, 146), N=(234, 118), T=(147, 128))),
    dict(id='fore_a_f045', type='dog.leg.fore', tags=['sun'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(212, 158), (230, 160), (245, 206), (237, 215), (225, 213), (215, 186)], anchors=dict(top=(220, 163), foot=(235, 209))),
    dict(id='fore_b_f045', type='dog.leg.fore', tags=['sun'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(189, 158), (209, 158), (207, 199), (191, 201), (187, 180)], anchors=dict(top=(199, 163), foot=(198, 197))),
    dict(id='hind_a_f045', type='dog.leg.hind', tags=['sun'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(163, 152), (185, 152), (183, 191), (167, 193), (163, 175)], anchors=dict(top=(174, 157), foot=(175, 188))),
    dict(id='hind_b_f045', type='dog.leg.hind', tags=['sun', 'bent'], src=DOGSRC, f=45, sam=True, flip=True,
         cut=[(141, 132), (161, 132), (161, 183), (143, 183)], anchors=dict(top=(151, 140), foot=(151, 180))),
    # heads from the found turning frames: f030's frontal head (the head comes round to the door first) and f027's head
    # and neck crushed into shadow against the lit room (seen from the door's light, it is the back of the head)
    dict(id='head_front_f030', type='dog.head', tags=['turn', 'front', 'look-back'], src=DOGSRC, f=30, sam=True,
         cut=[(144, 89), (217, 89), (217, 128), (204, 144), (152, 144), (144, 126)], anchors=dict(neck=(178, 142), crown=(178, 95), muzzle=(210, 120))),
    dict(id='head_back_f027', type='dog.head', tags=['turn', 'away', 'look-in'], src=DOGSRC, f=27, sam=True, tone='backlit',
         cut=[(140, 88), (197, 88), (199, 112), (196, 136), (202, 156), (146, 156), (140, 132)], anchors=dict(neck=(176, 154), crown=(176, 94))),
    dict(id='whole_f027', type='dog.whole', tags=['turn', 'three-quarter'], src=DOGSRC, f=27, sam=True, cut=None, anchors={}),
    dict(id='whole_f030', type='dog.whole', tags=['turn', 'front'], src=DOGSRC, f=30, sam=True, cut=None, anchors={}),
    dict(id='whole_f033', type='dog.whole', tags=['turn', 'front'], src=DOGSRC, f=33, sam=True, cut=None, anchors={}),
    # --- PERSON: the dog's own person (the coat in the same home movie) + a found head + a found hand
    dict(id='coat_f000', type='person.body', src=DOGSRC, f=0, sam=False,
         cut=[(14, 4), (22, 0), (44, 0), (52, 4), (58, 16), (60, 60), (62, 120), (64, 150), (54, 152), (52, 192), (40, 192), (36, 156),
              (30, 156), (28, 192), (16, 192), (14, 152), (4, 150), (6, 120), (8, 60), (10, 16)],
         anchors=dict(top=(33, 0), feet=(34, 191))),
    dict(id='coat_up', type='person.torso', src=DOGSRC, f=0, sam=False,
         cut=[(14, 4), (22, 0), (44, 0), (52, 4), (58, 16), (60, 60), (62, 108), (6, 108), (8, 60), (10, 16)], anchors=dict(top=(33, 0), hip=(33, 102))),
    dict(id='coat_lo', type='person.legs', src=DOGSRC, f=0, sam=False,
         cut=[(16, 120), (52, 120), (52, 192), (40, 192), (36, 160), (30, 160), (28, 192), (16, 192)], anchors=dict(hip=(34, 124), feet=(34, 190))),
    dict(id='sleeve_coat', type='person.sleeve', src=DOGSRC, f=0, sam=False,
         cut=[(20, 30), (44, 30), (45, 112), (19, 112)], anchors=dict(top=(32, 32), bottom=(32, 110))),
    dict(id='hair_coat', type='person.hair', src=DOGSRC, f=0, sam=False,
         cut=[(32 + 22 * math.cos(k * math.pi / 9), 60 + 24 * math.sin(k * math.pi / 9)) for k in range(18)], anchors=dict(c=(32, 60), top=(32, 36)), edge=0),
    dict(id='head_miner_f000', type='person.head', src=LANSRC, f=0, sam=False, flip=True,
         cut=[(300, 40), (384, 40), (384, 214), (372, 205), (350, 186), (343, 175), (338, 152), (330, 137), (320, 129), (325, 110),
              (326, 93), (318, 83), (290, 82), (285, 56)],
         anchors=dict(neck=(368, 205), crown=(345, 42), mouth=(338, 158))),
    dict(id='hand_f000', type='person.hand', src=HANDSRC, f=0, sam=False, flip=True,
         cut=[(158, 88), (165, 75), (200, 66), (240, 62), (300, 55), (384, 42), (384, 100), (300, 98), (250, 100), (220, 110), (190, 112), (160, 108)],
         anchors=dict(arm=(384, 72), tip=(159, 96))),
]
# --- the door leaf at found swing angles (Straight Talk frames, SAM leaf mask), opening = closing played backward
for i in (30, 28, 26, 24, 22, 20, 18, 16):
    SPECS.append(dict(id='leaf_f%03d' % i, type='door.leaf', src=DOORSRC, f=i, sam=True, sam_pick='left', cut=None, anchors={}))
# --- the sound arcs of a found telephone voice (luminance-keyed), re-timed: they become the person's calls
for i in range(8, 32, 3):
    SPECS.append(dict(id='arcs_f%03d' % i, type='voice.arcs', src=FACESRC, f=i, sam=False, key='arcs',
                      cut=[(196, 0), (384, 0), (384, 288), (196, 288)], anchors=dict(mouth=(150, 150)), edge=0))


def poly_mask(size, polys):
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        if len(p) >= 3: d.polygon([tuple(q) for q in p], fill=255)
    return m


def cut(spec):
    im = Image.open(frame_path(spec['src'], spec['f'])).convert('RGB')
    W, H = im.size
    m = Image.new('L', (W, H), 255)
    if spec.get('sam'):
        polys = sam(spec['src'], spec['f'])
        if spec.get('sam_pick') == 'left':  # the door leaf: the polygon whose centroid is leftmost of the large ones
            big = [p for p in polys if len(p) > 6]
            big.sort(key=lambda p: np.mean([q[0] for q in p]))
            polys = big[:1]
        m = poly_mask((W, H), polys)
    if spec.get('cut'):
        c = poly_mask((W, H), [spec['cut']])
        m = Image.fromarray(np.minimum(np.array(m), np.array(c)))
    if spec.get('key') == 'arcs':
        a = np.asarray(im.convert('L')).astype(float)
        bg = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(14))).astype(float)
        k = np.clip((a - bg - 6) * 10, 0, 255)
        k = np.asarray(Image.fromarray(k.astype(np.uint8)).filter(ImageFilter.MaxFilter(5))).astype(float)
        m = Image.fromarray(np.minimum(np.array(m), k).astype(np.uint8))
    if spec.get('feather'):  # a graded join instead of a straight scissor seam
        xe, wd, side = spec['feather']
        xx = np.arange(W)[None, :].astype(float)
        ramp = np.clip((xx - xe) / wd if side > 0 else (xe - xx) / wd, 0, 1) ** 1.5
        m = Image.fromarray((np.asarray(m).astype(float) * ramp).astype(np.uint8))
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    bb = m.getbbox()
    if bb is None: raise SystemExit('empty fragment ' + spec['id'])
    pad = 4
    x0, y0, x1, y1 = max(0, bb[0] - pad), max(0, bb[1] - pad), min(W, bb[2] + pad), min(H, bb[3] + pad)
    rgb = im.crop((x0, y0, x1, y1))
    al = m.crop((x0, y0, x1, y1))
    # tone: stretch the fragment's own range inside its matte (the home movie is murky)
    if spec['type'].startswith(('dog', 'person.body', 'person.torso', 'person.legs', 'person.sleeve', 'person.hair')):
        g = np.asarray(rgb.convert('L')).astype(float)
        aa = np.asarray(al) > 128
        if spec['type'].startswith('dog') and spec.get('sam'):
            # one tone for the whole dog of that frame (pieces no longer stretch on their own: no pale bars)
            full = np.asarray(im.convert('L')).astype(float)
            fm = np.asarray(poly_mask((W, H), sam(spec['src'], spec['f']))) > 128
            lo, hi = np.percentile(full[fm], 3), np.percentile(full[fm], 97)
            g = np.clip((g - lo) / max(1, hi - lo), 0, 1)
            g = g * 200 + 28
            if spec.get('tone') == 'backlit': g = g * 0.20 + 6
            g = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(float)
        elif aa.sum() > 20:
            lo, hi = np.percentile(g[aa], 3), np.percentile(g[aa], 97)
            g = np.clip((g - lo) / max(1, hi - lo), 0, 1)
            g = g * 120 + 14 if spec['type'].startswith('person') else g * 200 + 28
            g = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(float)
        rgb = Image.fromarray(g.astype(np.uint8)).convert('RGB')
    anchors = {k: (v[0] - x0, v[1] - y0) for k, v in spec.get('anchors', {}).items()}
    fw, fh = rgb.size
    if spec['type'] == 'dog.whole' or spec['type'] == 'door.leaf':
        a = np.asarray(al) > 128
        ys, xs = np.nonzero(a)
        anchors['ground'] = (float(xs.mean()), float(ys.max()))
        anchors['top'] = (float(xs.mean()), float(ys.min()))
        anchors['left'] = (float(xs.min()), float(ys.mean()))
        anchors['right'] = (float(xs.max()), float(ys.mean()))
        if spec['type'] == 'dog.whole':  # where the head is: the column of the topmost 15% of the matte
            top = ys < ys.min() + 0.25 * (ys.max() - ys.min())
            anchors['head'] = (float(xs[top].mean()), float(ys[top].mean()))
    if spec.get('flip'):
        rgb = ImageOps.mirror(rgb); al = ImageOps.mirror(al)
        anchors = {k: (fw - 1 - v[0], v[1]) for k, v in anchors.items()}
    rgba = rgb.convert('RGBA'); rgba.putalpha(al)
    # cut-paper edge: the scissors leave a pale rim
    e = spec.get('edge', 0 if spec['type'].startswith('dog') else 1)
    if e:
        big = Image.new('RGBA', rgba.size, (0, 0, 0, 0))
        rim = al.filter(ImageFilter.MaxFilter(3))
        paper = Image.new('RGBA', rgba.size, (214, 206, 188, 255)); paper.putalpha(rim)
        big = Image.alpha_composite(big, paper)
        rgba = Image.alpha_composite(big, rgba)
    rgba.save(os.path.join(OUT, spec['id'] + '.png'))
    return dict(id=spec['id'], type=spec['type'], tags=spec.get('tags', []), size=rgba.size,
                anchors={k: [round(v[0], 2), round(v[1], 2)] for k, v in anchors.items()},
                source=dict(spec['src'], frame=spec['f'], frame_file=os.path.relpath(frame_path(spec['src'], spec['f']), ROOT) if frame_path(spec['src'], spec['f']).startswith(ROOT) else frame_path(spec['src'], spec['f'])),
                operation=('SAM mask ∩ ' if spec.get('sam') else '') + ('scissors polygon' if spec.get('cut') else 'SAM mask') +
                          (' · luminance key' if spec.get('key') else '') + (' · mirrored' if spec.get('flip') else '') + (' · tone crushed (back-lit)' if spec.get('tone') == 'backlit' else '') + (' · graded join (feather)' if spec.get('feather') else '') + (' · tone stretch' if spec['type'].startswith(('dog', 'person.body', 'person.torso', 'person.legs')) else '') + (' · paper rim' if spec.get('edge', 0 if spec['type'].startswith('dog') else 1) else ''),
                cut=spec.get('cut'))


def world():
    """World pieces (not typed actors): crops of found frames that become the building and the dusk."""
    W = {}
    # stones of the home movie's house pillar -> the house wall
    for i in (44, 46, 48, 49):
        im = Image.open(frame_path(DOGSRC, i)).convert('L').crop((282, 0, 384, 200))
        im.save(os.path.join(OUT, 'stone_f%03d.png' % i)); W['stone_f%03d' % i] = dict(source=dict(DOGSRC, frame=i), operation='crop x282-384 y0-200 (stone pillar)')
    # the home movie's path -> the porch floor
    im = Image.open(frame_path(DOGSRC, 20)).convert('L').crop((0, 236, 200, 288)); im.save(os.path.join(OUT, 'floor_f020.png'))
    W['floor_f020'] = dict(source=dict(DOGSRC, frame=20), operation='crop x0-200 y236-288 (gravel path)')
    im = Image.open(frame_path(DOGSRC, 0)).convert('L').crop((60, 0, 300, 46)); im.save(os.path.join(OUT, 'hedge_f000.png'))
    W['hedge_f000'] = dict(source=dict(DOGSRC, frame=0), operation='crop x60-300 y0-46 (shrubs)')
    # Straight Talk: jamb strip and floor strip
    im = Image.open(frame_path(DOORSRC, 30)).convert('RGB').crop((268, 0, 292, 288)); im.save(os.path.join(OUT, 'jamb_f030.png'))
    W['jamb_f030'] = dict(source=dict(DOORSRC, frame=30), operation='crop x268-292 (white door frame)')
    im = Image.open(frame_path(DOORSRC, 30)).convert('RGB').crop((96, 262, 300, 288)); im.save(os.path.join(OUT, 'sill_f030.png'))
    W['sill_f030'] = dict(source=dict(DOORSRC, frame=30), operation='crop y262-288 (floor at the door)')
    # Light Of Your Life: the bulb becomes the room
    for i in (12, 16, 20, 24):
        im = Image.open(frame_path(BULBSRC, i)).convert('RGB').crop((72, 0, 312, 288)); im.save(os.path.join(OUT, 'room_bulb_f%03d.png' % i))
        W['room_bulb_f%03d' % i] = dict(source=dict(BULBSRC, frame=i), operation='crop x72-312 (lit bulb on a shelf) -> the lit room')
    # the cloud time-lapse becomes the dusk
    for i in range(0, 62, 2):
        im = Image.open(frame_path(CLOUDSRC, i)).convert('L'); im.save(os.path.join(OUT, 'sky_f%03d.png' % i))
    W['sky_f000-f060'] = dict(source=dict(CLOUDSRC, frame='0..60 step 2'), operation='luminance only; regraded to dusk at render')
    return W


if __name__ == '__main__':
    lib = [cut(s) for s in SPECS]
    wl = world()
    json.dump(dict(fragments=lib, world=wl), open(os.path.join(HERE, 'cache/frags.json'), 'w'), indent=1)
    # proof sheet
    tiles = [Image.open(os.path.join(OUT, f['id'] + '.png')) for f in lib]
    sc = 2
    cols = 8; tw, th = 220, 220
    sheet = Image.new('RGB', (cols * tw, ((len(tiles) + cols - 1) // cols) * th), (40, 60, 90))
    d = ImageDraw.Draw(sheet)
    for n, (t, f) in enumerate(zip(tiles, lib)):
        s = min((tw - 10) / t.width, (th - 24) / t.height, 3)
        tt = t.resize((max(1, int(t.width * s)), max(1, int(t.height * s))), Image.LANCZOS)
        X, Y = (n % cols) * tw + 5, (n // cols) * th + 18
        sheet.paste(tt, (X, Y), tt)
        for k, v in f['anchors'].items():
            ax, ay = X + v[0] * s, Y + v[1] * s
            d.ellipse((ax - 3, ay - 3, ax + 3, ay + 3), outline=(255, 60, 60)); d.text((ax + 4, ay - 4), k, fill=(255, 255, 0))
        d.text((X, Y - 15), f['id'], fill=(255, 255, 255))
    os.makedirs(os.path.join(HERE, '../proof'), exist_ok=True)
    sheet.save(os.path.join(HERE, '../proof/fragments.jpg'), quality=88)
    print(len(lib), 'fragments')
