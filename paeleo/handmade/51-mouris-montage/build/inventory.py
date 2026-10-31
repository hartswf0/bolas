"""SCION 51 · collection inventory.
Every image the film uses is a typed record: source shot + frame + crop + imagery class + temperature + layer.
Copies the used source frames into sources/ (unchanged JPEG frames, 384x288) and writes inventory.json.
The Mouris collection itself is NOT here: we had no viewing access. These are independently licensed public-domain shots
(kit/found-frames.json) used to test montage mechanisms (whole-image substitution on a measured rhythm)."""
import json, os, shutil
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(OUT, '../../..'))
SHOTS = '/home/user/hartswf0/secondhand-motion/shots/'
FOUND = {s['category']: s for s in json.load(open(os.path.join(REPO, 'paeleo/handmade/kit/found-frames.json')))}

# id: (shot category, frame, crop [x0,y0,x1,y1] normalised, imagery class, temperature, layers)
# temperature: cold = hard images for the calls; warm = soft images for the soft voice and the light; neutral = waiting
RAW = [
    # fur (the coat)
    ('fur.cat.chest', 'cat', 0, [0.02, 0.62, 0.30, 0.98], 'fur', 'warm', ['coat']),
    ('fur.cat.breast', 'cat', 40, [0.02, 0.74, 0.36, 0.99], 'fur', 'warm', ['coat']),
    ('fur.horse.mane', 'horse', 0, [0.22, 0.02, 0.58, 0.45], 'fur', 'warm', ['coat']),
    ('fur.rabbit.back', 'rabbit', 26, [0.50, 0.40, 0.80, 0.68], 'fur', 'warm', ['coat']),
    ('fur.lion.flank', 'lion', 0, [0.28, 0.45, 0.62, 0.62], 'fur', 'neutral', ['coat']),
    ('fur.sheep.flock', 'sheep', 0, [0.05, 0.48, 0.60, 0.72], 'fur', 'neutral', ['coat']),
    ('fur.sheep.flock2', 'sheep', 20, [0.40, 0.48, 0.95, 0.72], 'fur', 'neutral', ['coat']),
    ('fur.tiger.stripes', 'tiger', 0, [0.02, 0.58, 0.42, 0.92], 'fur', 'cold', ['coat']),
    ('fur.tiger.stripes2', 'tiger', 20, [0.02, 0.50, 0.40, 0.90], 'fur', 'cold', ['coat']),
    ('fur.broom.bristle', 'broom', 0, [0.25, 0.45, 0.62, 0.95], 'fur', 'cold', ['coat']),
    # hard things that stand in for the coat on the calls
    ('hard.wheel.spokes', 'wheel', 13, [0.30, 0.15, 0.75, 0.90], 'hard', 'cold', ['coat', 'room']),
    ('hard.ladder.rungs', 'ladder', 0, [0.25, 0.15, 0.70, 0.95], 'doors', 'cold', ['coat', 'room']),
    ('hard.shovel.blade', 'shovel', 0, [0.30, 0.10, 0.95, 0.70], 'hard', 'cold', ['coat']),
    ('hard.train.front', 'train', 0, [0.15, 0.25, 0.85, 0.85], 'hard', 'cold', ['room']),
    ('hard.traffic.signal', 'traffic-light', 0, [0.0, 0.0, 0.62, 0.85], 'hard', 'cold', ['room']),
    ('hard.clock.bell', 'alarm-clock', 13, [0.30, 0.25, 0.85, 0.95], 'voices', 'cold', ['room', 'letters']),
    # eyes
    ('eyes.human.iris', 'eye', 0, [0.38, 0.30, 0.78, 0.80], 'eyes', 'cold', ['eye']),
    ('eyes.human.iris2', 'eye', 16, [0.38, 0.30, 0.78, 0.80], 'eyes', 'neutral', ['eye']),
    ('eyes.cat.eye', 'cat', 40, [0.21, 0.30, 0.34, 0.44], 'eyes', 'warm', ['eye']),
    ('eyes.tiger.eye', 'tiger', 20, [0.40, 0.16, 0.50, 0.28], 'eyes', 'cold', ['eye']),
    # paws
    ('paws.tiger.paw', 'tiger', 0, [0.47, 0.73, 0.80, 0.97], 'paws', 'cold', ['paw']),
    ('paws.tiger.paw2', 'tiger', 20, [0.66, 0.76, 0.88, 0.97], 'paws', 'neutral', ['paw']),
    ('paws.cat.paw', 'cat', 61, [0.05, 0.70, 0.40, 0.99], 'paws', 'warm', ['paw']),
    # doors
    ('doors.door.panel', 'door', 0, [0.30, 0.0, 0.85, 1.0], 'doors', 'neutral', ['room', 'door']),
    ('doors.door.open', 'door', 16, [0.25, 0.0, 0.95, 1.0], 'doors', 'neutral', ['room', 'door']),
    ('doors.door.wall', 'door', 31, [0.0, 0.0, 0.60, 1.0], 'doors', 'neutral', ['room', 'door']),
    ('doors.stove.door', 'stove', 0, [0.05, 0.05, 0.95, 0.95], 'doors', 'cold', ['room', 'door']),
    # lamps
    ('lamps.bulb.glow', 'light-bulb', 13, [0.20, 0.0, 0.80, 0.95], 'lamps', 'warm', ['room', 'interior', 'letters']),
    ('lamps.bulb.halo', 'light-bulb', 25, [0.10, 0.0, 0.90, 0.95], 'lamps', 'warm', ['room', 'interior', 'letters']),
    ('lamps.lantern.brass', 'lantern', 16, [0.10, 0.05, 0.60, 0.80], 'lamps', 'warm', ['room', 'interior', 'letters']),
    ('lamps.star.flare', 'star', 40, [0.25, 0.15, 0.75, 0.85], 'lamps', 'warm', ['interior']),
    ('lamps.lighthouse', 'lighthouse', 16, [0.30, 0.10, 0.70, 0.95], 'lamps', 'neutral', ['room']),
    # hands
    ('hands.card', 'hand', 0, [0.45, 0.0, 1.0, 0.35], 'hands', 'neutral', ['hand']),
    ('hands.lantern.grip', 'lantern', 16, [0.30, 0.70, 0.70, 1.0], 'hands', 'warm', ['hand']),
    ('hands.basket', 'basket', 0, [0.05, 0.0, 0.45, 0.40], 'hands', 'warm', ['hand']),
    # voices
    ('voices.lips', 'face', 0, [0.0, 0.0, 0.55, 0.85], 'voices', 'cold', ['mouth']),
    ('voices.lips2', 'face', 20, [0.0, 0.0, 0.55, 0.85], 'voices', 'warm', ['mouth']),
    ('voices.trumpet', 'trumpet', 0, [0.08, 0.42, 0.58, 0.75], 'voices', 'cold', ['room', 'letters']),
    ('voices.cello', 'cello', 0, [0.30, 0.10, 0.80, 0.95], 'voices', 'warm', ['letters']),
    # soft, warm things (room and coat on the soft voice)
    ('soft.sleepingbag', 'sleeping-bag', 25, [0.35, 0.30, 0.80, 0.80], 'soft', 'warm', ['coat', 'room', 'letters']),
    ('soft.basket.weave', 'basket', 25, [0.30, 0.35, 0.80, 0.85], 'soft', 'warm', ['room', 'letters']),
    ('soft.flower', 'flower', 19, [0.20, 0.15, 0.85, 0.85], 'soft', 'warm', ['room', 'letters']),
    ('soft.cloud', 'cloud', 30, [0.0, 0.25, 1.0, 0.85], 'soft', 'neutral', ['room']),
    ('soft.person.coat', 'hat', 16, [0.0, 0.55, 0.60, 1.0], 'soft', 'neutral', ['person']),
    ('person.head', 'trumpet', 0, [0.62, 0.20, 0.86, 0.50], 'hands', 'neutral', ['person']),
    ('person.suit', 'trumpet', 0, [0.55, 0.60, 0.95, 1.0], 'soft', 'neutral', ['person']),
]


# The dog's own pieces (round 2): whole subjects, cut by the SAM mask's bounding box (+6%), shown in their own colour.
# (shot, frame, imagery class, temperature, has_face, identifiable on the calls)
DOG = [
    ('tiger', 0, 'fur', 'cold', True, True), ('tiger', 20, 'fur', 'cold', True, True), ('wheel', 13, 'hard', 'cold', False, True),
    ('ladder', 0, 'hard', 'cold', False, False), ('broom', 0, 'fur', 'cold', False, False), ('train', 0, 'hard', 'cold', False, True),
    ('alarm-clock', 13, 'voices', 'cold', False, True), ('traffic-light', 0, 'hard', 'cold', False, True), ('frying-pan', 13, 'hard', 'cold', False, False),
    ('sheep', 0, 'fur', 'neutral', False, True), ('lion', 0, 'fur', 'neutral', True, True), ('dog', 10, 'fur', 'neutral', True, True), ('horse', 0, 'fur', 'neutral', True, True),
    ('cat', 0, 'fur', 'warm', True, True), ('cat', 40, 'fur', 'warm', True, True), ('horse', 30, 'fur', 'warm', True, True), ('rabbit', 26, 'fur', 'warm', True, True),
    ('flower', 19, 'soft', 'warm', False, True), ('sleeping-bag', 25, 'soft', 'warm', False, False), ('basket', 25, 'soft', 'warm', False, True),
    ('lantern', 16, 'lamps', 'warm', False, True), ('cow', 22, 'fur', 'warm', True, True), ('monkey', 0, 'fur', 'warm', True, True), ('light-bulb', 13, 'lamps', 'warm', False, True),
]


def mask_crop(cat, fr):
    m = json.load(open(os.path.join(SHOTS, cat + '-sam', 'masks.json')))
    im = Image.open(os.path.join(SHOTS, cat + '-sam', 'frames', sorted(os.listdir(os.path.join(SHOTS, cat + '-sam', 'frames')))[fr])); w, h = im.size
    best = None
    for p in m.get(str(fr), []):
        xs = [q[0] for q in p]; ys = [q[1] for q in p]; a = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if best is None or a > best[0]:
            best = (a, min(xs), min(ys), max(xs), max(ys))
    if not best:
        return [0, 0, 1, 1]
    _, x0, y0, x1, y1 = best; mx, my = (x1 - x0) * 0.06, (y1 - y0) * 0.06
    return [round(max(0, x0 - mx) / w, 3), round(max(0, y0 - my) / h, 3), round(min(w, x1 + mx) / w, 3), round(min(h, y1 + my) / h, 3)]


def build():
    os.makedirs(os.path.join(OUT, 'sources'), exist_ok=True)
    inv = []
    rows = list(RAW)
    for cat, fr, cls, temp, face, ident in DOG:
        rows.append((f'dog.{cat}.{fr}', cat, fr, mask_crop(cat, fr), cls, temp, ['dog'] + ([] if face else ['dog_head']) + (['dog_ident'] if ident else [])))
    for rid, cat, fr, crop, cls, temp, layers in rows:
        d = os.path.join(SHOTS, cat + '-sam', 'frames')
        fs = sorted(os.listdir(d)); fr = min(fr, len(fs) - 1); fn = fs[fr]
        dst = os.path.join('sources', f'{cat}_{fn}')
        if not os.path.exists(os.path.join(OUT, dst)):
            shutil.copy(os.path.join(d, fn), os.path.join(OUT, dst))
        s = FOUND[cat]
        inv.append({'id': rid, 'class': cls, 'temperature': temp, 'layers': layers, 'file': dst, 'crop_norm': crop,
                    'shot': cat + '-sam', 'frame': fn, 'source_title': s['source_title'], 'source_url': s['source_url'],
                    'clip_id': s.get('clip_id'), 'rights': s['rights'], 'crop_from': 'SAM mask bounding box of the largest subject, +6%' if rid.startswith('dog.') else 'chosen by eye',
                    'original_path': os.path.join(d, fn)})
    json.dump({'about': 'Collection inventory: every image used by SCION 51, by imagery class. A record is source frame + crop; '
               'the film substitutes whole crops (never tiles) on the cutting score.', 'records': inv},
              open(os.path.join(OUT, 'inventory.json'), 'w'), indent=1)
    # crop sheet for inspection
    W = 150; n = len(inv); cols = 8; rows = (n + cols - 1) // cols
    sh = Image.new('RGB', (cols * W, rows * (W + 14)), 'white'); dr = ImageDraw.Draw(sh)
    for k, r in enumerate(inv):
        im = Image.open(os.path.join(OUT, r['file'])).convert('RGB'); w, h = im.size
        c = r['crop_norm']; im = im.crop((int(c[0] * w), int(c[1] * h), int(c[2] * w), int(c[3] * h)))
        im.thumbnail((W - 4, W - 4)); x, y = (k % cols) * W, (k // cols) * (W + 14)
        sh.paste(im, (x + 2, y + 2)); dr.text((x + 2, y + W), r['id'][:24], fill='black')
    os.makedirs(os.path.join(OUT, 'proof'), exist_ok=True)
    sh.save(os.path.join(OUT, 'proof/inventory_sheet.jpg'), quality=82)
    return inv


if __name__ == '__main__':
    print(len(build()), 'records')
