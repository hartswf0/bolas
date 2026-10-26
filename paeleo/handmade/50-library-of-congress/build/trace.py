"""trace.json from the render's own measurements of the dog layer (cache/measure.json): silhouette centroid, bbox,
head-piece centroid. The states are assigned from onsets detected in these measured signals, not copied from the score."""
import os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
FPS = 24; N = len(M)
cx = [r['msr']['cx'] for r in M]; cy = [r['msr']['cy'] for r in M]
h = [r['msr']['y1'] - r['msr']['y0'] for r in M]; w = [r['msr']['x1'] - r['msr']['x0'] for r in M]
hx = [r['msr'].get('hx') for r in M]; hy = [r['msr'].get('hy') for r in M]
def facing_of(r):
    # puppet frames: which side of the neck joint the rendered head piece lies on (the head plate points its nose away from
    # the joint), +1 = toward the door (screen left); documented turn frames: the view of that frame (+1, 0 camera, -1)
    if r['kind'] != 'puppet': return r['facing_m']
    neck = [j[0] for j in r['joints'] if j[1] == 'head'][0]
    return 1 if r['msr']['hx'] < neck[0] else -1
fac = [facing_of(r) for r in M]

def first(cond, start, sustain=3):
    for i in range(start, N - sustain):
        if all(cond(j) for j in range(i, i + sustain)): return i
    return None

on = {}
on['retreat'] = first(lambda j: cx[j] - cx[j - 1] > 0.25, int(0.5 * FPS))
# back to watching: the backing has slowed below half its peak speed and the head is coming up
vmax = max(cx[j] - cx[j - 1] for j in range(on['retreat'], on['retreat'] + 36))
on['watch_1'] = first(lambda j: (cx[j] - cx[j - 1]) < 0.5 * vmax and hy[j] is not None and hy[j] < hy[j - 1] - 0.15, on['retreat'] + 6, 2)
# the refusal: the drawing on the stage changes (the silhouette's width jumps as the documented turn begins)
on['refuse'] = first(lambda j: abs(w[j] - w[j - 1]) > 12 or abs(h[j] - h[j - 1]) > 12, int(3.0 * FPS), 1)
# turning back to look: the head piece comes round to the door's side of the body
on['watch_2'] = first(lambda j: fac[j] == 1, int(6.0 * FPS), 3)
on['approach'] = first(lambda j: cx[j - 1] - cx[j] > 0.25, int(14.0 * FPS))
# lying down: the body's centroid sinks toward the boards (more than 1 px a frame, sustained)
on['lie_down'] = first(lambda j: cy[j] > cy[j - 1] + 1.0, int(23.0 * FPS))
on['look_in'] = first(lambda j: hx[j] is not None and hx[j] < hx[j - 1] - 0.4, int(26.0 * FPS), 2)
seq = [('watch', 0), ('retreat', on['retreat']), ('watch', on['watch_1']), ('refuse', on['refuse']), ('watch', on['watch_2']),
       ('approach', on['approach']), ('lie_down', on['lie_down'])]
h_stand = sorted(h[:20])[10]
frames = []
for i in range(N):
    st = 'watch'
    for s, k in seq:
        if k is not None and i >= k: st = s
    t = round(i / FPS, 4)
    lying = h[i] < 0.72 * h_stand
    head_low = hy[i] is not None and hy[i] > cy[i] - 4
    posture = 'lying' if lying else ('turning (documented frame f%03d)' % M[i]['src'] if M[i]['kind'] == 'turn' else 'standing')
    if not lying and M[i]['kind'] == 'puppet' and head_low: posture += ', head low'
    if lying and i >= (on['look_in'] or N) and hx[i] is not None and hx[i] < 330: posture += ', head into the doorway'
    frames.append({'i': i, 't': t, 'state': st, 'x_score': SCORE['frames'][i]['dog']['x'], 'x_screen': round(cx[i], 2), 'y_screen': round(cy[i], 2),
                   'facing': fac[i], 'posture': posture, 'bbox_h': h[i], 'head_screen': None if hx[i] is None else [round(hx[i], 1), round(hy[i], 1)],
                   'drawing': ('f%03d cut pieces%s' % (6, ' reversed' if M[i]['a'] == -1 else '')) if M[i]['kind'] == 'puppet' else 'f%03d whole frame' % M[i]['src']})
score_t = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
onsets = {k: {'measured_t': None if v is None else round(v / FPS, 3), 'score_t': score_t[k], 'dt': None if v is None else round(v / FPS - score_t[k], 3)} for k, v in on.items()}
out = {'about': 'Measured from the dog layer of this film\'s own render (centroid, bbox, head piece). facing: +1 head on the door side, -1 turned away, 0 a documented frame facing the camera. x_screen in px (static camera, 190 px/m).',
       'onsets': onsets, 'frames': frames}
json.dump(out, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
print(json.dumps(onsets, indent=1))
