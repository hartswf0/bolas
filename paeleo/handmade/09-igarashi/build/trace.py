"""Build trace.json, diagnostics.json and the measured choice onsets from what the renderer measured (build/cache/measure.json).
python3 build/trace.py

Per scene frame the renderer read back the dog's own layer (alpha centroid, extent) and the rendered positions of the
dog's handles (muzzle, neck socket, skull, withers, feet), plus the ARAP diagnostics of every piece. From those:
  x_screen, y_screen  alpha-weighted centroid of the rendered dog, px
  facing              +1 when the rendered muzzle points toward the door side (left of its neck), -1 when away
  posture             the rig's posture name for the drawing shown (stand / crouch / back_turned / sitting_back_turned / lying ...)
  state               the rig's state label (it follows the score's choices); the measured onsets below are the evidence
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SC = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
F = SC['frames']
X0, S = 320, 190
assert len(M) == len(F) == 768, (len(M), len(F))

t = np.array([f['t'] for f in F]); cx = np.array([m['meas']['cx'] for m in M]); y0 = np.array([m['meas']['y0'] for m in M])
y1 = np.array([m['meas']['y1'] for m in M]); facing = np.array([m['meas']['facing'] for m in M])
heads = [m['dog']['head'] for m in M]; bodies = [m['dog']['body'] for m in M]


def first(cond, after):
    for i in range(len(t)):
        if t[i] >= after and cond(i):
            return i
    return None


base = np.median(cx[(t > 0.1) & (t < 0.9)])
top_retreat = np.mean(y0[(t > 1.5) & (t < 2.2)])
base_app = np.median(cx[(t > 13) & (t < 14.5)])
top_app = np.median(y0[(t > 22.5) & (t < 23.7)])
on = {}
on['retreat'] = first(lambda i: cx[i] > base + 1.5, 0.5)                                   # starts to move away from the door
on['watch_1'] = first(lambda i: y0[i] < top_retreat - 3, 2.0)                              # stops cowering: the back rises
on['refuse'] = first(lambda i: facing[i] == -1, 3.0)                                       # the rendered muzzle turns away
on['watch_2'] = first(lambda i: facing[i] == 1, 5.0)                                       # the muzzle comes round to the door
on['approach'] = first(lambda i: cx[i] < base_app - 1.5, 13.0)                             # starts toward the door
on['lie_down'] = first(lambda i: y0[i] > top_app + 4, 23.0)                                # the back goes down at the sill
on['look_in'] = first(lambda i: heads[i] == 'head_back' and bodies[i] == 'dog_lie', 25.0)  # the back of its head toward us, muzzle into the room
score_t = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
onsets = {k: {'score_t': score_t[k], 'measured_t': None if v is None else round(float(t[v]), 3), 'frame': v,
              'dt': None if v is None else round(float(t[v]) - score_t[k], 3)} for k, v in on.items()}

frames = []
for f, m in zip(F, M):
    me = m['meas']
    frames.append({'i': f['i'], 't': f['t'], 'state': m['dog']['state'], 'x_score': f['dog']['x'], 'x_screen': round(me['cx'], 2),
                   'y_screen': round(me['cy'], 2), 'facing': me['facing'], 'posture': m['dog']['posture'],
                   'drawings': [m['dog']['body'], m['dog']['head']], 'bbox': [me['x0'], me['y0'], me['x1'], me['y1']],
                   'muzzle': [round(v, 1) for v in me['muzzle']], 'skull_below_withers_px': round(me['skull_below_back'], 1),
                   'person': m['person']})

# head low during the approach: skull below the withers on screen
app = [fr for fr in frames if fr['state'] == 'approach' and fr['t'] >= 14.708 + 0.35]
head_low = sum(1 for fr in app if fr['skull_below_withers_px'] > 0) / max(1, len(app))
# never inside: the rendered dog never passes the threshold into the house (its body centre stays on the porch side of the sill)
door_l, door_r = X0 - 0.46 * S, X0 + 0.46 * S
end = frames[-1]
inside_part = max(0, door_r - end['bbox'][0]) / (end['bbox'][2] - end['bbox'][0])
# feet: rendered handle positions of planted feet in consecutive standing frames
slides = []
for a, b, fa, fb in zip(M[:-1], M[1:], F[:-1], F[1:]):
    if a['dog']['body'] != 'dog_stand' or b['dog']['body'] != 'dog_stand':
        continue
    for k in ('f1', 'f2', 'h1', 'h2'):
        pa, pb = a['meas'].get('feet', {}).get(k), b['meas'].get('feet', {}).get(k)
        if pa and pb and abs(pa[1] - pb[1]) < 0.3 and pa[1] > 585:
            slides.append(abs(pb[0] - pa[0]))
diag = {'pieces': {}}
for m in M:
    for pid, d in m['diag'].items():
        s = diag['pieces'].setdefault(pid, {'frames': 0, 'inverted_frames': 0, 'max_inverted': 0, 'max_energy': 0, 'max_feature_distortion': 0, 'min_area_ratio': 9})
        s['frames'] += 1; s['inverted_frames'] += d['inverted'] > 0; s['max_inverted'] = max(s['max_inverted'], d['inverted'])
        s['max_energy'] = max(s['max_energy'], d['energy']); s['max_feature_distortion'] = max(s['max_feature_distortion'], d['feature_distortion'])
        s['min_area_ratio'] = min(s['min_area_ratio'], d['min_area_ratio'])
ms = [m.get('ms', 0) for m in M]
diag['frame_ms'] = {'mean': round(float(np.mean(ms)), 1), 'p95': round(float(np.percentile(ms, 95)), 1), 'note': 'rig + ARAP solve of every piece + full compositing per frame, headless Chromium with SwiftShader (no GPU)'}
diag['head_low_share_of_approach'] = round(head_low, 3)
diag['end_bbox_inside_door_frame_share'] = round(inside_part, 3)
diag['planted_foot_slide_px'] = {'n': len(slides), 'mean': round(float(np.mean(slides)), 3) if slides else None, 'p95': round(float(np.percentile(slides, 95)), 3) if slides else None, 'max': round(float(np.max(slides)), 3) if slides else None}
for d in diag['pieces'].values():
    for k in ('max_energy', 'max_feature_distortion', 'min_area_ratio'):
        d[k] = round(d[k], 4)
out = {'about': 'SCION 09 Igarashi: what the dog did, measured from its own render (alpha read-back of the dog layer and the rendered handle positions). state is the rig label; onsets_measured are found from the rendered signals.',
       'fps': 24, 'x_screen_mapping': f'x_screen ~ {X0} + x_m * {S} (fixed camera)', 'onsets_measured': onsets, 'frames': frames}
json.dump(out, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=None, separators=(',', ':'))
json.dump(diag, open(os.path.join(ROOT, 'diagnostics.json'), 'w'), indent=1)
print(json.dumps(onsets, indent=0))
print(json.dumps(diag, indent=1))
