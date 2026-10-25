"""ACTION EDITOR / FINISH: the trace (what the dog did, measured from the render), the measured choice onsets, the
decoded path trace and failure-frame heat map images, and the four stills.
python3 build/finish.py   (after render.js film, sound.py and the mux)"""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
FOLD = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(FOLD, '..', '..', '..'))
BANK = json.load(open(os.path.join(FOLD, 'bank', 'bank.json')))['drawings']
PATH = json.load(open(os.path.join(C, 'path.json')))
FR = PATH['frames']
MEAS = {m['i']: m for m in json.load(open(os.path.join(C, 'meas.json')))}
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
assert len(MEAS) == 768, len(MEAS)

REFUSE = {'q45_low', 'f90_low', 'q135_low', 'cower_R', 'sink_R', 'lie_R', 'rest_R', 'cower', 'flinch'}
TURN_BACK = {'lookback_R', 'situp_R', 'rise_R', 'f90_qleft', 'q45_up'}
LIE = {'sit', 'lie_up', 'lie_low', 'rest', 'look_in', 'look_in_a', 'look_in_b'}


def head_dir(k):
    d = BANK[k]; p = d['pose']
    if k in ('f90_low',): return -1
    if k in ('f90_qleft',): return 1
    if p.get('over'): return 1
    return 1 if p['yaw'] < 90 else -1


def posture(k):
    p = BANK[k]['pose']
    if p.get('look', 0) > .5: return 'lying, head turned in through the door'
    if p['lie'] >= .9: return 'lying, chin on paws' if p.get('rest', 0) > .5 else 'lying'
    if p['lie'] >= .4: return 'sitting / half down'
    if p.get('moving'): return 'backing away, low' if p.get('back') else 'walking, head low'
    if 45 <= p['yaw'] <= 135: return 'turning (%s view)' % ('front' if p['yaw'] == 90 else 'three-quarter')
    if p.get('crouch', 0) >= .4: return 'crouched'
    if p['head'] < .5: return 'standing, head low'
    return 'standing'


def x_paws(f):
    m = BANK[f['dog']]['meta']
    if 'feet' not in m or m['group'] not in ('stand', 'walk', 'back'): return None
    ft = m['feet']
    return round(300 + f['x_place'] * 190 + sum(v[0] for v in ft.values()) / len(ft), 2)


def classify():
    st = []
    n = len(FR)
    for i, f in enumerate(FR):
        k = f['dog']; g = BANK[k]['meta']['group']
        if g == 'back': s = 'retreat'
        elif g == 'walk' or k == 'stand_low': s = 'approach'
        elif k in REFUSE: s = 'refuse'
        elif k in TURN_BACK: s = 'watch'
        elif k in LIE: s = 'lie_down'
        elif k == 'wary':
            nxt = next((FR[j]['dog'] for j in range(i, n) if FR[j]['dog'] != k), None)
            s = 'refuse' if nxt in REFUSE else 'watch'
        else: s = 'watch'
        st.append(s)
    # a backing run that has stopped on screen (its last drawing held still for 3+ frames) is the dog standing, watching
    i = 0
    while i < n:
        if st[i] == 'retreat':
            j = i
            while j + 1 < n and st[j + 1] == 'retreat': j += 1
            h = j
            while h - 1 >= i and FR[h - 1]['dog'] == FR[j]['dog']: h -= 1
            if j - h + 1 >= 3 and (j + 1 >= n or st[j + 1] != 'retreat'):
                xs = [MEAS[q]['cx'] for q in range(h, j + 1)]
                if max(xs) - min(xs) < 1.0:
                    for q in range(h, j + 1): st[q] = 'watch'
            i = j + 1
        else: i += 1
    return st


def main():
    st = classify()
    frames = []
    for i, f in enumerate(FR):
        m = MEAS[i]; k = f['dog']
        frames.append({'i': i, 't': round(i / 24, 4), 'state': st[i], 'score_state': f['state'], 'x_score': f['x_score'],
                       'x_screen': round(m['cx'], 2), 'y_screen': round(m['cy'], 2), 'facing': head_dir(k),
                       'body_facing': 1 if BANK[k]['pose']['yaw'] < 90 else (-1 if BANK[k]['pose']['yaw'] > 90 else 0),
                       'posture': posture(k), 'drawing': k, 'bbox': [round(m['x0']), round(m['y0']), round(m['x1']), round(m['y1'])],
                       'person': f['person'], 'x_paws': x_paws(f)})
    # measured onsets, from pixels where the representation allows it, else from the drawing on screen
    xs = [fr['x_screen'] for fr in frames]
    T = lambda i: round(i / 24, 3)
    on = {}
    i0 = 12
    on['retreat_centroid'] = next(T(i) for i in range(i0, 200) if xs[i] - xs[i0] >= 2.0)
    on['retreat_first_drawing'] = next(T(i) for i in range(i0, 200) if st[i] == 'retreat')
    r0 = int(on['retreat_first_drawing'] * 24)
    on['watch_after_retreat'] = next(T(i) for i in range(r0 + 3, 300) if abs(xs[i + 1] - xs[i]) < .5 and abs(xs[i + 2] - xs[i]) < .5 and abs(xs[i + 3] - xs[i]) < .5)
    on['refuse_first_reaction'] = next(T(i) for i in range(72, 200) if st[i] == 'refuse')
    on['refuse_back_shown'] = next(T(i) for i in range(72, 200) if frames[i]['facing'] == -1)
    on['back_held_until'] = T(next(i for i in range(int(on['refuse_back_shown'] * 24), 400) if frames[i]['facing'] == 1))
    on['turns_back_to_look'] = on['back_held_until']
    on['body_faces_door_again'] = next(T(i) for i in range(170, 300) if frames[i]['body_facing'] == 1)
    a0 = 340
    on['approach_centroid'] = next(T(i) for i in range(a0, 600) if xs[a0] - xs[i] >= 2.0)
    on['approach_first_drawing'] = next(T(i) for i in range(a0, 600) if st[i] == 'approach')
    h_stand = frames[400]['bbox'][3] - frames[400]['bbox'][1]
    on['lie_down_first_drawing'] = next(T(i) for i in range(540, 700) if st[i] == 'lie_down')
    cy_stand = frames[400]['y_screen']; cy_lie = frames[600]['y_screen']
    on['lying_low_measured'] = next(T(i) for i in range(540, 700) if frames[i]['y_screen'] > cy_stand + .6 * (cy_lie - cy_stand))
    on['first_body_step_back_paws'] = next(T(i) for i in range(12, 200) if frames[i]['x_paws'] is not None and frames[12]['x_paws'] is not None and frames[i]['x_paws'] - frames[12]['x_paws'] >= 2.0)
    on['first_body_step_forward_paws'] = next(T(i) for i in range(340, 600) if frames[i]['x_paws'] is not None and frames[340]['x_paws'] - frames[i]['x_paws'] >= 2.0)
    on['looks_in'] = next(T(i) for i in range(600, 768) if BANK[frames[i]['drawing']]['pose'].get('look', 0) > .5)
    on['settles'] = next(T(i) for i in range(int(on['looks_in'] * 24), 768) if frames[i]['drawing'] == 'rest')
    score_t = {'first_body_step_back_paws': 1.0, 'first_body_step_forward_paws': 14.708, 'retreat_centroid': 1.0, 'retreat_first_drawing': 1.0,
               'approach_centroid': 14.708, 'approach_first_drawing': 14.708, 'watch_after_retreat': 2.333, 'refuse_first_reaction': 3.417, 'refuse_back_shown': 3.417,
               'turns_back_to_look': 7.458, 'approach': 14.708, 'lie_down_first_drawing': 23.792, 'lying_low_measured': 23.792, 'looks_in': 26.4}
    onsets = {k: {'measured_s': v, 'score_s': score_t.get(k), 'dt': (round(v - score_t[k], 3) if k in score_t else None)} for k, v in on.items()}
    lying = [fr for fr in frames if fr['state'] == 'lie_down']
    S = 190.0; X0 = 300.0
    end = frames[-1]
    sill = {'door_jambs_screen_x': [X0 - .46 * S, X0 + .46 * S], 'end_bbox': end['bbox'],
            'inside_frame_px': max(0, min(end['bbox'][2], X0 + .46 * S) - max(end['bbox'][0], X0 - .46 * S)),
            'outside_frame_px': max(0, end['bbox'][2] - (X0 + .46 * S)),
            'note': 'front elevation: the dog lies on the threshold stone with its fore half between the jambs and its hind half and tail outside the frame'}
    out = {'about': 'SCION 14 trace. state = what the drawing on screen shows (classified from the drawing, with a pixel check for when backing stops); '
                    'x_screen,y_screen = centroid of the dog pixels measured from the render each frame; facing = where the head points (+1 to the door, -1 away); camera fixed.',
           'onsets': onsets, 'sill': sill, 'frames': frames}
    json.dump(out, open(os.path.join(FOLD, 'trace.json'), 'w'))
    print(json.dumps(onsets, indent=0)); print(sill)
    proofs(frames)


def proofs(frames):
    n = len(frames)
    groups = ['stand', 'back', 'turn', 'lieR', 'walk', 'lie', 'look']
    ids = sorted({f['drawing'] for f in frames} | {k for k, v in BANK.items() if v['meta']['group'] in groups},
                 key=lambda k: (groups.index(BANK[k]['meta']['group']) if BANK[k]['meta']['group'] in groups else 9, k))
    rowh, lw, W = 13, 110, 110 + n * 2
    H = len(ids) * rowh + 150
    im = Image.new('RGB', (W, H), (22, 19, 15)); d = ImageDraw.Draw(im)
    col = {'stand': (176, 141, 98), 'walk': (209, 176, 126), 'back': (139, 93, 69), 'turn': (201, 119, 79), 'lie': (124, 138, 160), 'lieR': (92, 102, 128), 'look': (224, 192, 96)}
    for r, k in enumerate(ids):
        d.text((4, r * rowh), k, fill=(170, 160, 140))
        d.line([(lw, r * rowh + rowh - 1), (W, r * rowh + rowh - 1)], fill=(36, 32, 28))
    for i, f in enumerate(frames):
        r = ids.index(f['drawing'])
        d.rectangle([lw + i * 2, r * rowh + 2, lw + i * 2 + 1, r * rowh + rowh - 3], fill=col.get(BANK[f['drawing']]['meta']['group'], (200, 200, 200)))
    for c in SCORE['choices']:
        x = lw + c['t'] * 24 * 2; d.line([(x, 0), (x, len(ids) * rowh)], fill=(240, 90, 70)); d.text((x + 2, len(ids) * rowh + 2), '%.2f' % c['t'], fill=(240, 90, 70))
    # position: score x (grey) and measured x_screen (gold)
    y0 = len(ids) * rowh + 30
    for i, f in enumerate(frames):
        ys = y0 + 100 - (f['x_score'] / 4.9) * 100; ym = y0 + 100 - ((f['x_screen'] - 300) / 190 / 4.9) * 100
        d.point((lw + i * 2, ys), fill=(150, 150, 150)); d.point((lw + i * 2, ym), fill=(230, 190, 90))
    d.text((4, y0 + 40), 'x: score (grey)\nmeasured (gold)', fill=(170, 160, 140))
    im.save(os.path.join(FOLD, 'proof', 'path_trace.png'))
    # failure-frame heat map: per frame, each pose-distance term of the chosen drawing
    terms = ['yaw', 'lie', 'crouch', 'head', 'look', 'rest', 'ear', 'tail', 'moving', 'back', 'phase', 'wag', 'over', 'listen']
    hm = Image.new('RGB', (lw + n * 2, len(terms) * 16 + 40), (22, 19, 15)); d = ImageDraw.Draw(hm)
    for r, tname in enumerate(terms):
        d.text((4, r * 16 + 2), tname, fill=(170, 160, 140))
        for i, f in enumerate(PATH['frames']):
            v = min(1.0, f['terms'].get(tname, 0) / 1.5)
            if v > 0:
                d.rectangle([lw + i * 2, r * 16, lw + i * 2 + 1, r * 16 + 14], fill=(int(40 + 215 * v), int(30 + 120 * v * (1 - v)), int(30 * (1 - v))))
    for c in SCORE['choices']:
        x = lw + c['t'] * 24 * 2; d.line([(x, 0), (x, len(terms) * 16)], fill=(90, 160, 240))
    d.text((lw, len(terms) * 16 + 8), 'unexplained pose error of the chosen drawing per frame (bright = far from the performance); blue = choices', fill=(170, 160, 140))
    hm.save(os.path.join(FOLD, 'proof', 'heatmap.png'))


if __name__ == '__main__':
    main()
