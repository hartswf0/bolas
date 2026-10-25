"""SCION-25 RIVE · write trace.json, the measured choice onsets, the event log and the acceptance tests from the render.
python3 build/finalize.py   (after render.js, sound.py and the mux in make.sh)"""
import json, os, subprocess, math
B = os.path.dirname(os.path.abspath(__file__)); F = os.path.dirname(B); R = os.path.dirname(os.path.dirname(os.path.dirname(F)))
score = json.load(open(os.path.join(R, 'paeleo/handmade/score/threshold-score.json')))
rt = json.load(open(os.path.join(B, 'cache/film/render-trace.json'))); tr = rt['trace']; ev = rt['events']
assert len(tr) == 768, len(tr)
fr = []
for f in tr:
    fr.append({k: f[k] for k in ('i', 't', 'state', 'x_score', 'x_screen', 'y_screen', 'facing', 'posture')} |
              {k: f[k] for k in ('sm', 'yaw', 'head_rel', 'head_world_yaw', 'bbox', 'height_m', 'head_below_back_px', 'nose_screen', 'muzzle_depth_m', 'front_x_world', 'tail_x_world', 'feet')})
T = lambda i: round(i / 24, 3)


def first(pred, start, end=768):
    for i in range(max(1, start), end):
        if pred(i): return i
    return None


xs = [f['x_screen'] for f in fr]; nose = [f['nose_screen'] for f in fr]
on = {}
# 1.00 retreat: the rendered dog layer starts moving away from the door (centroid +0.4 px/frame)
on['retreat'] = first(lambda i: xs[i] - xs[i - 1] > 0.4, int(0.5 * 24))
# 2.33 watch: the backing stops being driven (smoothed screen speed falls below 60 % of its mean through the retreat)
# (velocity of the rendered layer, smoothed over +-4 frames so the swinging legs do not jitter it)
sv = lambda i: (xs[min(767, i + 4)] - xs[max(0, i - 4)]) / 8
vmean = sum(sv(i) for i in range(31, 53)) / 22   # mean layer speed through the middle of the retreat (1.3-2.2 s)
on['watch_1'] = first(lambda i: sv(i) < 0.6 * vmean, 48)
# 3.42 refuse: the muzzle starts to leave its watching place (the turn begins: nose moves > 3 px relative to the body centroid)
# 3.42 refuse: the drawn head starts to swing away from the door (head yaw leaves 180 deg by more than 4 deg)
on['refuse'] = first(lambda i: abs(fr[i]['head_world_yaw'] - 180) > 4, int(3.0 * 24))
on['back_shown'] = first(lambda i: fr[i]['facing'] == -1, int(3.0 * 24))
# 7.46 watch: the head starts to come round (nose moves > 3 px from where it lay)
n0 = nose[int(7.1 * 24)]
on['watch_2'] = first(lambda i: math.hypot(nose[i][0] - n0[0], nose[i][1] - n0[1]) > 3, int(7.1 * 24))
on['head_toward_door'] = first(lambda i: (fr[i]['head_world_yaw'] % 360) > 120, int(7.1 * 24))
# 14.71 approach: the dog layer starts moving toward the door
on['approach'] = first(lambda i: xs[i] - xs[i - 1] < -0.3, int(14.0 * 24))
# 23.79 lie down: the dog layer's top edge starts to sink (> 2 px below its walking height at 23.3 s)
top0 = fr[int(23.3 * 24)]['bbox'][1]
on['lie_down'] = first(lambda i: fr[i]['bbox'][1] - top0 > 2, int(23.3 * 24))
# 26.4 looks in: the muzzle turns into the room's depth (muzzle tip deeper than the skull by more than 3 cm)
on['look_in'] = first(lambda i: fr[i]['muzzle_depth_m'] < -0.03, int(25.5 * 24))
on['settles'] = first(lambda i: fr[i]['muzzle_depth_m'] > -0.03, (on['look_in'] or 640) + 1)
choices = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
onsets = {k: {'score_t': choices.get(k), 'measured_t': T(v) if v is not None else None, 'dt': round(T(v) - choices[k], 3) if v is not None and k in choices else None} for k, v in on.items()}

# acceptance tests (structural, measured from the render or from the drawn pose)
ap = [f for f in fr if f['state'] == 'approach' and f['t'] > 15.2]
head_low_share = sum(1 for f in ap if f['head_below_back_px'] > 0) / len(ap)
ref = [f for f in fr if f['state'] == 'refuse']; back_share = sum(1 for f in ref if f['facing'] == -1) / len(ref)
back_by_39 = all(f['facing'] == -1 for f in fr if 3.9 <= f['t'] < 7.458)
slide = 0.0; last = {}
for f in fr:
    for ft in f['feet']:
        if ft['planted'] and ft['n'] in last and last[ft['n']] is not None:
            slide = max(slide, math.hypot(ft['x'] - last[ft['n']][0], ft['z'] - last[ft['n']][1]))
        last[ft['n']] = (ft['x'], ft['z']) if ft['planted'] else None
end = fr[-1]; inside_door = end['front_x_world'] < 0.25; tail_out = end['tail_x_world'] > 0.25
min_front = min(f['front_x_world'] for f in fr)
# approach covers the score's distance at its pace: screen metres per score metre (should be constant = 210 px/m)
a0, a1 = fr[int(15 * 24)], fr[int(23.5 * 24)]
pace = (a1['x_screen'] - a0['x_screen']) / (a1['x_score'] - a0['x_score'])
lv = json.load(open(os.path.join(B, 'cache/film/levels.json')))
tests = {
    'frames_scene': len(fr), 'film_frames_expected': 912,
    'choice_onsets_within_0.25s': all(abs(v['dt']) <= 0.25 for k, v in onsets.items() if v['dt'] is not None),
    'refusal_back_share': round(back_share, 3), 'back_turned_from_3.9_to_7.458': back_by_39,
    'approach_head_below_back_share': round(head_low_share, 3),
    'planted_foot_max_slide_m': round(slide, 5),
    'end_front_x_world_m': end['front_x_world'], 'end_tail_x_world_m': end['tail_x_world'], 'door_outer_face_x_world_m': 0.25, 'door_inner_face_x_world_m': -0.25,
    'end_front_inside_frame': inside_door, 'end_tail_outside': tail_out, 'min_front_x_world_m': min_front, 'never_past_inner_face': min_front > -0.25,
    'approach_screen_px_per_score_m': round(pace, 2),
    'audio': lv, 'soft_6db_below_call': lv['soft_below_call_db'] >= 6, 'soft_above_room': lv['soft_above_room_db'] > 0,
    'no_dead_end_states': None}
# no dead ends: every state of every layer has an outgoing transition (from the graph)
pup = json.load(open(os.path.join(B, 'puppet.json')))
dead = []
for L in pup['stateMachine']['layers']:
    for s in L['states']:
        if not any(t['from'] in (s, '*') and t['to'] != s for t in L['transitions']): dead.append(L['name'] + '.' + s)
tests['no_dead_end_states'] = not dead; tests['dead_end_states'] = dead
json.dump({'about': 'SCION-25 RIVE trace: what the dog did, per scene frame, measured from the rendered dog layer (x_screen, y_screen, bbox: alpha centroid and box of the dog-only layer) and from the drawn pose (facing: muzzle left or right of the body centroid on screen; head_below_back_px: top of the skull minus top of the back, screen px, positive = head lower). The camera does not move: x_screen = 355 + 210 * (x_score - 0.24) for the body centre. state is the score state the puppet was given (its mood input).',
           'choice_onsets_measured': onsets, 'frames': fr}, open(os.path.join(F, 'trace.json'), 'w'))
with open(os.path.join(F, 'events.jsonl'), 'w') as o:
    for e in ev: o.write(json.dumps(e) + '\n')
json.dump(tests, open(os.path.join(F, 'proof/acceptance.json'), 'w'), indent=1)
print(json.dumps(onsets, indent=0)); print(json.dumps({k: v for k, v in tests.items() if k != 'audio'}))
