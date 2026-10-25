"""Build trace.json from what was rendered (cache/meas.json, written by render.mjs from the dog's own layer).
The dog's STATE in the trace is not copied from the score: each choice onset is detected in the render measurements,
and the state changes at the measured onset. Measurements: pixel centroid / bbox / paw band / body-column top of the
dog layer (alpha), and the drawn head geometry (muzzle tip vs skull centre) for facing."""
import json, os, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(H)
M = json.load(open(os.path.join(H, 'cache', 'meas.json')))
SC = json.load(open(os.path.join(D, '..', 'score', 'threshold-score.json')))
K = 1.8; FLOOR = 600

def win(a, b, key):
    return [key(m) for m in M if a <= m['t'] <= b and key(m) is not None]

def first(t0, cond):
    return next((m for m in M if m['t'] >= t0 and cond(m)), None)

on = {}
# 1. retreat: the paws start to travel away from the door (paw-band centroid moves right by > 2 px)
rest = st.mean(win(0.0, 0.9, lambda m: m['meas']['feetX'])); top0 = st.mean(win(0.0, 0.9, lambda m: m['meas']['y0']))
ma = first(0.5, lambda m: m['meas']['y0'] - top0 > 3.0)
mb = first(0.5, lambda m: m['meas']['feetX'] is not None and m['meas']['feetX'] - rest > 2.0)
m = min([x for x in (ma, mb) if x], key=lambda x: x['t'])
on['retreat'] = (m['t'], f'cowering onset (silhouette top drops > 3 px) {ma["t"] if ma else None}s / paws travel away {mb["t"] if mb else None}s (first taken)')
# 2. retreat -> watch: the head comes back up (silhouette top rises past the midpoint between cowering and alert)
low = st.mean(win(1.6, 2.1, lambda m: m['meas']['y0'])); high = st.mean(win(2.9, 3.3, lambda m: m['meas']['y0']))
m = first(on['retreat'][0] + 0.5, lambda m: m['meas']['y0'] < (low + high) / 2)
on['watch1'] = (m['t'], f'silhouette top rises past midpoint {(low + high) / 2:.1f}px (cowering {low:.1f} -> alert {high:.1f})')
# 3. refuse: the drawing turns away (silhouette width departs >6% from the watching width)
w0 = st.mean(win(3.0, 3.35, lambda m: m['meas']['x1'] - m['meas']['x0']))
m = first(3.0, lambda m: abs((m['meas']['x1'] - m['meas']['x0']) - w0) / w0 > 0.06)
on['refuse'] = (m['t'], f'silhouette width departs >6% from watching width {w0:.1f}px (the turn begins)')
# 4. refuse -> watch: the muzzle comes round to point at the door (drawn head geometry)
m = first(6.0, lambda m: m['facing'] == 1)
on['watch2'] = (m['t'], 'muzzle tip left of skull centre: the head points back at the door')
# 5. approach: the head drops below the line of the back, or the paws start toward the door, whichever first
hb = st.mean(win(13.5, 14.5, lambda m: m['meas']['y0'])); fb = st.mean(win(13.5, 14.5, lambda m: m['meas']['feetX']))
ma = first(14.0, lambda m: m['meas']['y0'] - hb > 3.0); mb = first(14.0, lambda m: m['meas']['feetX'] is not None and fb - m['meas']['feetX'] > 2.0)
m = min([x for x in (ma, mb) if x], key=lambda x: x['t'])
on['approach'] = (m['t'], f'head-drop onset {ma["t"] if ma else None}s / paw travel onset {mb["t"] if mb else None}s (first taken)')
# 6. lie down: the top of the body over its centre drops > 3 px below its walking height
wb = st.mean(win(22.5, 23.5, lambda m: m['meas']['backTopCol']))
m = first(23.0, lambda m: m['meas']['backTopCol'] is not None and m['meas']['backTopCol'] - wb > 3.0)
on['lie_down'] = (m['t'], f'body-column top drops > 3 px below walking height {wb:.1f}px')
# 7. (not a state) hears "come in": the head lifts into the doorway (silhouette top rises > 4 px)
lb = st.mean(win(26.0, 26.35, lambda m: m['meas']['y0']))
m = first(26.0, lambda m: lb - m['meas']['y0'] > 4.0)
look = (m['t'], 'silhouette top rises > 4 px as the head turns into the room')
m2 = first(26.0, lambda m: m['head']['mode'] == 'in34')
settle = first(28.0, lambda m: m['head']['mode'] == 'prof')

seq = [(0, 'watch'), (on['retreat'][0], 'retreat'), (on['watch1'][0], 'watch'), (on['refuse'][0], 'refuse'), (on['watch2'][0], 'watch'), (on['approach'][0], 'approach'), (on['lie_down'][0], 'lie_down')]
def state_at(t):
    s = 'watch'
    for t0, nm in seq:
        if t >= t0: s = nm
    return s

frames = []
for m in M:
    mm = m['meas']
    back_h = (FLOOR - mm['backTopCol']) / K if mm['backTopCol'] is not None else None
    posture = 'lying' if back_h is not None and back_h < 33 else ('low' if back_h is not None and back_h < 47 else 'standing')
    frames.append({'i': m['i'], 't': round(m['t'], 4), 'state': state_at(m['t']), 'x_score': m['x_score'],
                   'x_screen': round(mm['screen']['cx'], 2), 'y_screen': round(mm['screen']['cy'], 2),
                   'x_world_measured': round((mm['cx'] - 320) / 180, 4), 'camera': {k: round(v, 4) for k, v in m['cam'].items()}, 'facing': m['facing'], 'posture': posture,
                   'view': m['fam'], 'head': m['head']['mode'], 'back_height_cm': None if back_h is None else round(back_h, 1),
                   'bbox': [mm['x0'], mm['y0'], mm['x1'], mm['y1']], 'paw_band_x': None if mm['feetX'] is None else round(mm['feetX'], 2),
                   'muzzle_px': [round(v, 1) for v in m['head']['tip']], 'head_top_px': round(m['head']['top'], 1), 'back_top_px': round(m['backTop'], 1),
                   'dog_line_mean_px': round(m['dogLineMean'], 4)})

score_t = {c['to'] + str(k): c['t'] for k, c in enumerate(SC['choices'])}
names = ['retreat', 'watch1', 'refuse', 'watch2', 'approach', 'lie_down']
onsets = [{'choice': f"{c['from']} -> {c['to']}", 'score_t': c['t'], 'measured_t': round(on[n][0], 4), 'dt': round(on[n][0] - c['t'], 3), 'how': on[n][1]} for n, c in zip(names, SC['choices'])]
onsets.append({'choice': 'hears "come in": looks in', 'score_t': 26.4, 'measured_t': round(look[0], 4), 'dt': round(look[0] - 26.4, 3), 'how': look[1],
               'head_drawing_back_of_head_from': m2['t'] if m2 else None, 'settles_head_down_from': settle['t'] if settle else None})
lines = [f['dog_line_mean_px'] for f in frames]
inv = {'line_width_px_mean': round(st.mean(lines), 4), 'line_width_px_sd': round(st.pstdev(lines), 4), 'line_width_cv': round(st.pstdev(lines) / st.mean(lines), 4)}
out = {'about': 'SCION 18 Cartoon Saloon: what the dog did, measured from its own render layer. state changes at the measured onsets.',
       'measured_onsets': onsets, 'line_quality': inv, 'frames': frames}
json.dump(out, open(os.path.join(D, 'trace.json'), 'w'), indent=0)
for o in onsets: print(f"{o['choice']:28s} score {o['score_t']:6.3f}  measured {o['measured_t']:7.3f}  dt {o['dt']:+.3f}")
print('line width px', inv)
