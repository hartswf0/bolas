"""assemble trace.json (what the dog did, per scene frame, measured from the render), the measured choice onsets,
and graph_trace.json (every rewrite of the typed graph, frame by frame, with the fragments that made the dog)."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(TOP, '../../..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
M = [json.load(open(os.path.join(HERE, 'cache/meas/%04d.json' % i))) for i in range(768)]

frames = []
for m in M:
    me = m['meas'] or {}
    if m['mode'] == 'whole': posture = 'turning (whole found frame)'
    elif m['head'] == 'head_back_cut': posture = 'lying, head turned in'
    elif m['lie'] >= 0.99: posture = 'lying' + (', head on paws' if m['nose'] and m['withers'] and m['nose'][1] > m['withers'][1] else '')
    elif m['lie'] > 0.1: posture = 'going down / getting up'
    elif m['crouch'] >= 0.5: posture = 'crouched, backing'
    elif m['head_mirror']: posture = 'turned away, head looking back'
    elif m['head'] == 'head_low_f048': posture = 'standing, head low'
    else: posture = 'standing'
    frames.append(dict(i=m['i'], t=round(m['t'], 4), state=m['state'], x_score=m['x_score'],
                       x_screen=round(me.get('cx', float('nan')), 2), y_screen=round(me.get('cy', float('nan')), 2),
                       facing=m['facing_measured'], posture=posture,
                       bbox=[me.get('x0'), me.get('y0'), me.get('x1'), me.get('y1')],
                       nose=[round(v, 1) for v in m['nose']] if m['nose'] else None,
                       withers=[round(v, 1) for v in m['withers']] if m['withers'] else None,
                       made_of=sorted(set(f for n, f in m['nodes'] if n.startswith('dog'))),
                       rules=m['rules']))
# NB: state is the rule engine's state as rendered (the rule that fired on that frame); onsets below are measured from pixels.
T = np.array([f['t'] for f in frames])
cx = np.array([f['x_screen'] for f in frames]); y0 = np.array([f['bbox'][1] for f in frames], float); y1 = np.array([f['bbox'][3] for f in frames], float)
face = [f['facing'] for f in frames]
nose_up = np.array([(f['withers'][1] - f['nose'][1]) if f['nose'] and f['withers'] else np.nan for f in frames])  # px nose above withers


def first(cond, t0):
    for k, f in enumerate(frames):
        if f['t'] >= t0 and cond(k): return f['t']
    return None


k05 = int(0.5 * 24)
on = {}
on['retreat'] = first(lambda k: cx[k] - cx[k05] > 3 or y0[k] - y0[k05] > 4, 0.5)
up_crouch = np.nanmean(nose_up[(T > 1.6) & (T < 2.2)]); up_watch = np.nanmean(nose_up[(T > 2.7) & (T < 3.2)])
on['watch_after_retreat'] = first(lambda k: nose_up[k] > (up_crouch + up_watch) / 2, 1.6)
on['refuse'] = first(lambda k: face[k] != 1, 3.0)
on['watch_turns_back'] = first(lambda k: face[k] == 1, 7.0)
low_ref = np.nanmean(nose_up[(T > 12) & (T < 14)])
on['approach'] = first(lambda k: nose_up[k] < low_ref - 15 or cx[k] < cx[int(14 * 24)] - 3, 14.0)
hstand = np.mean((y1 - y0)[(T > 22.5) & (T < 23.5)])
on['lie_down'] = first(lambda k: (y1[k] - y0[k]) < 0.92 * hstand, 23.0)
top_ref = np.mean(y0[(T > 25.8) & (T < 26.3)])
on['looks_in'] = first(lambda k: y0[k] < top_ref - 10, 26.0)
on['settles'] = first(lambda k: y0[k] > top_ref - 4, 27.8)
score_t = dict(retreat=1.0, watch_after_retreat=2.333, refuse=3.417, watch_turns_back=7.458, approach=14.708, lie_down=23.792, looks_in=26.4)
onsets = {k: dict(measured=v, score=score_t.get(k), dt=None if v is None or k not in score_t else round(v - score_t[k], 3)) for k, v in on.items()}
how = dict(retreat='dog-layer centroid moves away >3 px or its top drops >4 px (cowers), from 0.5 s',
           watch_after_retreat='nose rises above the withers past the midpoint between crouched and watching heights',
           refuse='rendered head no longer points to the door (front-view whole frame or head pointing away)',
           watch_turns_back='rendered nose points to the door again (nose left of neck)',
           approach='nose drops >15 px below its watching height above the withers, or centroid moves toward the door >3 px',
           lie_down='dog-layer bbox height falls below 92 % of its standing height (the first going-down drawing is 88 %)',
           looks_in='dog-layer top rises >10 px above its lying height (the head comes up into the doorway)',
           settles='top returns to lying height and the nose is below the withers again')
for k in onsets: onsets[k]['how'] = how[k]
# feet: planted positions must not move while planted (world metres, per leg slot); report the worst creep
creep = 0.0
for a, b in zip(M[:-1], M[1:]):
    if a['planted'] and b['planted'] and a['mode'] == b['mode'] == 'graph' :
        for q in b['planted']:
            d = min(abs(p - q) for p in a['planted'])
            if d < 0.05: creep = max(creep, d)
# identity invariant: every fragment drawn as the dog comes from the one home-movie dog
lib = {f['id']: f for f in json.load(open(os.path.join(HERE, 'cache/frags.json')))['fragments']}
dogfr = sorted(set(f for fr in frames for f in fr['made_of']))
srcs = sorted(set(lib[f]['source']['shot'] for f in dogfr))
inv = dict(dog_fragments=dogfr, dog_sources=srcs, identity_single_source=srcs == ['archive-dog'],
           max_x_screen_per_metre_check=None)
# end state: the threshold
last = frames[-1]
xl = 305 + 205 * -0.55; xr = 305 + 205 * 0.55
inv['end_bbox'] = last['bbox']; inv['door_opening_px'] = [round(xl, 1), round(xr, 1)]
inv['end_part_inside_frame_px'] = max(0, min(xr, last['bbox'][2]) - max(xl, last['bbox'][0]))
inv['end_part_outside_frame_px'] = max(0, last['bbox'][2] - max(xr, last['bbox'][0]))
json.dump(dict(about='SCION 43 collage graph · trace measured from the render (dog layer alpha; head anchors as placed). '
                     'state = the rule engine state rendered on that frame; see measured_onsets for pixel-measured choice onsets.',
               fps=24, frames=frames, measured_onsets=onsets, feet_max_creep_m_between_frames=round(creep, 4), invariants=inv),
          open(os.path.join(TOP, 'trace.json'), 'w'), indent=0)
# graph trace: only the frames where the graph changes
gt = []; prev = None
for m in M:
    key = json.dumps([m['mode'], m['head'], m['head_mirror'], m['split'], m['materials'], m['lie'], m['crouch']])
    if key != prev:
        gt.append(dict(i=m['i'], t=round(m['t'], 3), state=m['state'], rules=m['rules'], mode=m['mode'], head=m['head'],
                       head_mirror=m['head_mirror'], split_at_threshold=m['split'], materials=m['materials'], lie=m['lie'], crouch=m['crouch'],
                       nodes=m['nodes']))
        prev = key
json.dump(dict(about='every change of the typed entity graph (dog + person + door + voice nodes, with the fragment each node is made of)',
               changes=gt), open(os.path.join(TOP, 'graph_trace.json'), 'w'), indent=0)
print(json.dumps(onsets, indent=1)); print('feet creep m', round(creep, 4)); print(json.dumps(inv, indent=1))
