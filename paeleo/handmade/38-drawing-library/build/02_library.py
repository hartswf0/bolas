"""Pose illustrator / drawing clustering agent, pass 2: the pose-state library.

Every dog here is a real Quick, Draw! doodle, picked by eye from contact sheets
(sheets/auto-*, sheets/pool-lie-*, sheets/short-*) out of /home/user/hartswf0/quickdraw/dog.part.
The labels below are the agent's reading of each drawing (what pose it shows), and
the stroke-measured features are added next to them so the two can be compared.

Family (identity): round or floppy-eared head, oval/box body, stick legs. Picked so the
substituted drawings read as one kind of dog drawn by many hands.

Writes library/dogs.ndjson (the raw drawings, key_id kept), library/set.ndjson,
library/pose_library.json, sheets/library.png
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import qd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# index in dog.part : (native facing, posture, head 0..1.2, leg spread 0..1, face-to-viewer, rest, note)
LABELS = {
    # standing / walking, head side left
    2419: ('L', 'stand', .75, .8, 0, 0, 'round head high, legs splayed: mid-stride'),
    2011: ('L', 'stand', .90, .2, 0, 0, 'big round head up, straight legs: alert'),
    1926: ('L', 'stand', .85, .3, 0, 0, 'head up, legs straight'),
    2116: ('L', 'stand', .90, .2, 0, 0, 'head up, tail up: alert'),
    2917: ('L', 'stand', .85, .5, 0, 0, 'head up, slanted legs'),
    1162: ('L', 'stand', .60, .3, 0, 0, 'head level, two long legs'),
    2960: ('L', 'stand', .55, .2, 0, 0, 'head level with the back'),
    1106: ('L', 'stand', .40, .6, 0, 0, 'head at body height, legs apart: walking low'),
    778:  ('L', 'stand', .50, .3, 0, 0, 'small head, ears, level'),
    2087: ('L', 'crouch', .50, .6, 0, 0, 'long low body, short bent legs'),
    3578: ('L', 'crouch', .55, .4, 0, 0, 'box body, stubby legs'),
    1956: ('L', 'crouch', .60, .5, 0, 0, 'body low, short legs, head on neck'),
    2750: ('L', 'stand', .90, .4, 0, 0, 'head up on a neck'),
    2627: ('L', 'stand', .80, .7, 0, 0, 'round body, head on neck, legs splayed'),
    3150: ('L', 'stand', .85, .1, 0, 0, 'head up, straight post legs'),
    1043: ('L', 'stand', .80, .6, 1, 0, 'face turned to the viewer, body side-on'),
    # standing / walking, head side right
    2830: ('R', 'stand', .45, .3, 0, 0, 'round head at body height'),
    3619: ('R', 'stand', .55, .3, 0, 0, 'round head level'),
    3005: ('R', 'crouch', .40, .6, 0, 0, 'big head low, short slanted legs'),
    2988: ('R', 'stand', .45, .7, 0, 0, 'head level, legs slanted: walking'),
    3269: ('R', 'stand', .35, .5, 0, 0, 'head low at the chest, tail out'),
    2681: ('R', 'stand', .90, .4, 0, 0, 'head up'),
    2920: ('R', 'stand', .90, .3, 0, 0, 'head up on neck'),
    3704: ('R', 'stand', .70, .1, 0, 0, 'small head up, post legs'),
    3291: ('R', 'stand', .85, .1, 0, 0, 'head up, two legs'),
    2375: ('R', 'stand', .80, .1, 0, 0, 'head up, box body'),
    1910: ('R', 'stand', .75, .3, 0, 0, 'head up, bent legs'),
    # front / turning
    846:  ('F', 'front', .70, .0, 1, 0, 'facing the viewer: head, ears, body below'),
    409:  ('F', 'sit', .70, .0, 1, 0, 'sitting, seen from the front'),
    1652: ('F', 'sit', .70, .0, 1, 0, 'sitting, seen from the front, paws'),
    # lying
    1082: ('L', 'lie', .65, 0, 0, 0, 'lying, floppy-eared head raised, paw forward'),
    2839: ('L', 'lie', .55, 0, 0, 0, 'lying, floppy ears, long body'),
    1056: ('L', 'lie', .30, 0, 0, .9, 'lying, chin forward over two paws'),
    2299: ('L', 'lie', .70, 0, 1, 0, 'lying, face turned to the viewer'),
    2459: ('L', 'lie', .70, 0, 0, 0, 'lying, big head up, tail curled'),
    3072: ('L', 'lie', .60, 0, 0, 0, 'lying, floppy head up'),
    1427: ('L', 'lie', .90, 0, 0, 0, 'lying, head lifted high, ears up'),
    1666: ('L', 'lie', .60, 0, 1, 0, 'lying, face to the viewer'),
    959:  ('L', 'lie', .35, 0, 0, .6, 'lying, head low, ears out'),
    3110: ('L', 'lie', .50, 0, 0, 0, 'lying, ear, one leg folded'),
    # round 2: 2250 (face-on), 3283 and 2098 (round head curled on the body: the critic could not
    # tell which end was the head during the refusal) were dropped from the library
    3476: ('R', 'lie', .35, 0, 0, .5, 'lying, head right and down, ear hanging'),
    # round 2 additions (critic repairs 1, 3, 4), found in sheets/r2-headlow-*, r2-short-*
    135:  ('R', 'stand', .30, .7, 0, 0, 'dome body, round-box head low at the chest, legs apart: the stride twin of 1309'),
    1309: ('L', 'stand', .30, .8, 0, 0, 'dome body, small round head low at the chest, legs splayed: the stride twin of 135 (found by 10_twin_search.py)'),
    639:  ('L', 'stand', .45, .6, 0, 0, 'oval body, plain circle head at the front at back height, four stick legs: the head-shape twin of 2830 (11_head_partner.py)'),
    3537: ('L', 'lie', .75, 0, 0, 0, 'lying, box head in profile, snout and eye pointing left'),
    3107: ('R', 'lie', .60, 0, 0, 0, 'lying, floppy head right'),
}

# round 2 labels: head top below the back line (head-low), head in profile (snout pointing)
HEADLOW = {135, 1309, 2717, 3269, 3005}  # 2830 measured level (head top 0.7 px under the back): not head-low
PROFILE = {3537, 1111}

# set doodles: (category, index in <category>.part, role)
SET = [
    ('house', 3, 'house: roof and walls, no door of its own'),
    ('door', 2, 'door ajar: frame with a gap line'),
    ('door', 42, 'door swinging: diagonal panel'),
    ('door', 46, 'door frame, open (no knob)'),
    ('door', 65, 'door panel swung open'),
    ('moon', 16, 'crescent moon'),
    ('face', 37, "the person's face"),
    ('hand', 23, 'arm and hand reaching'),
    ('hand', 13, 'flat hand offered low'),
    ('stairs', 6, 'porch steps going down'),
    ('fence', 7, 'porch rail and posts'),
]

if __name__ == '__main__':
    dogs = qd.load('dog')
    os.makedirs(f'{HERE}/library', exist_ok=True)
    lib = []
    with open(f'{HERE}/library/dogs.ndjson', 'w') as fh:
        for idx, lab in LABELS.items():
            d = dogs[idx]
            fh.write(json.dumps(d) + '\n')
            f = qd.features(d)
            face, post, head, spread, viewer, rest, note = lab
            lib.append(dict(idx=idx, key_id=d['key_id'], countrycode=d['countrycode'], face=face,
                            headlow=int(idx in HEADLOW), profile=int(idx in PROFILE),
                            posture=post, head=head, spread=spread, viewer=viewer, rest=rest, note=note,
                            measured=dict(aspect=round(f['aspect'], 3), sym=round(f['sym'], 3),
                                          head_side_mass=round(f['hs'], 3), top_left=round(f['tl'], 3),
                                          top_right=round(f['tr'], 3), leg_rows=round(f['legrows'], 3),
                                          strokes=f['ns'])))
    # agreement between agent's facing label and the stroke-measured head side (sanity, not truth)
    agree = 0; n = 0
    for e in lib:
        if e['face'] in 'LR':
            m = e['measured']; s = (m['top_right'] - m['top_left']) + 0.5 * (-m['head_side_mass'])
            guess = 'L' if s > 0 else 'R'
            agree += guess == e['face']; n += 1
    print(f'facing label vs stroke head-side guess: {agree}/{n} agree')
    sets = []
    with open(f'{HERE}/library/set.ndjson', 'w') as fh:
        cache = {}
        for cat, i, role in SET:
            if cat not in cache:
                cache[cat] = qd.load(cat, 2000)
            d = cache[cat][i]
            fh.write(json.dumps(d) + '\n')
            sets.append(dict(category=cat, idx=i, key_id=d['key_id'], countrycode=d['countrycode'], role=role))
    json.dump(dict(dogs=lib, set=sets, facing_agreement=[agree, n]), open(f'{HERE}/library/pose_library.json', 'w'), indent=1)
    # library contact sheet, grouped by posture
    order = sorted(lib, key=lambda e: (['stand', 'crouch', 'front', 'sit', 'lie'].index(e['posture']), e['face'], -e['head']))
    cols, cw, ch = 9, 200, 150
    rows = (len(order) + cols - 1) // cols
    img = Image.new('RGB', (cols * cw, rows * ch), (24, 28, 52)); dr = ImageDraw.Draw(img)
    for k, e in enumerate(order):
        S = qd.strokes_np(dogs[e['idx']]); x0, y0, x1, y1 = qd.bbox(S)
        sc = min((cw - 20) / max(x1 - x0, 1), (ch - 40) / max(y1 - y0, 1))
        cx, cy = (k % cols) * cw, (k // cols) * ch
        for s in S:
            pts = [(cx + 10 + (p[0] - x0) * sc, cy + 20 + (p[1] - y0) * sc) for p in s]
            dr.line(pts if len(pts) > 1 else pts * 2, fill=(239, 230, 210), width=2)
        dr.text((cx + 4, cy + 3), f"{e['posture']} {e['face']} h{e['head']:.2f}", fill=(242, 196, 107))
        dr.text((cx + 4, cy + ch - 14), f"key {e['key_id']}", fill=(150, 150, 190))
    img.save(f'{HERE}/sheets/library.png')
    print(len(lib), 'dogs;', len(sets), 'set drawings')
