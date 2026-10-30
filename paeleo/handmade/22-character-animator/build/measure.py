"""SCION 22 · trace.json from the render: the dog's silhouette (union of every Dog/* felt piece as actually composited)
gives its centroid, extent and height; the head pieces give the head centroid.  Facing is measured as which side of the
body the head is on (head left of the body = toward the door = +1).  Choice onsets are detected on these measurements."""
import json, os, pickle
import numpy as np
from common import CACHE, FOLDER, SCORE, N, FPS, WALL_IN, WALL_OUT

M = [json.load(open(os.path.join(CACHE, 'measure', '%04d.json' % i))) for i in range(N)]
rig = pickle.load(open(os.path.join(CACHE, 'rig.pkl'), 'rb'))
S = rig['states']
fr = []
for i in range(N):
    m, st, sc = M[i], S[i], SCORE['frames'][i]
    cam = st['cam']
    s = cam['s']
    off = m['hx'] - m['cx']
    facing = 1 if off < -4 else (-1 if off > 4 else (1 if st['head_mirror'] < 0 else -1))
    hm = (m['y1'] - m['y0']) / s
    posture = 'lying' if hm < 0.56 else ('crouched' if hm < 0.80 else 'standing')
    fr.append({'i': i, 't': round(i / FPS, 4), 'state': sc['dog']['state'], 'x_score': sc['dog']['x'],
               'x_screen': round(m['cx'], 2), 'y_screen': round(m['cy'], 2), 'x_world_measured': round(m['x_world'], 4),
               'facing': facing, 'posture': posture, 'height_m': round(hm, 3), 'head_offset_px': round(off, 1),
               'inside_share': round(m['inside_share'], 3), 'outside_share': round(m['outside_share'], 3),
               'body_view': st['view'], 'head_view': st['head_view'], 'head_top_below_back': bool(st['head_top_y'] < st['back_line_y']),
               'muzzle_x_world': round(st['muzzle'][0], 3), 'cam_scale_px_per_m': round(s, 2)})
X = np.array([f['x_world_measured'] for f in fr]); HO = np.array([f['head_offset_px'] for f in fr]) / np.array([f['cam_scale_px_per_m'] for f in fr])
Hm = np.array([f['height_m'] for f in fr]); t = np.arange(N) / FPS
def first(cond, after):
    for i in range(int(after * FPS), N):
        if cond(i): return round(i / FPS, 3)
    return None
base = X[int(0.5 * FPS):int(0.95 * FPS)].mean()
on = {}
on['retreat'] = first(lambda i: X[i] - base > 0.02, 0.5)
v = np.gradient(X) * FPS
peak = v[int(1.2 * FPS):int(2.2 * FPS)].max()
on['retreat->watch'] = first(lambda i: v[i] < 0.5 * peak, 2.0)
hb = HO[int(3.0 * FPS):int(3.35 * FPS)].mean()
on['refuse'] = first(lambda i: abs(HO[i] - hb) > 0.05, 3.2)
HX = np.array([M[i]['hx'] for i in range(N)]); HY = np.array([M[i]['hy'] for i in range(N)]); SC = np.array([f['cam_scale_px_per_m'] for f in fr])
b7x, b7y = HX[int(6.9 * FPS):int(7.2 * FPS)].mean(), HY[int(6.9 * FPS):int(7.2 * FPS)].mean()
on['turns back to look'] = first(lambda i: np.hypot(HX[i] - b7x, HY[i] - b7y) / SC[i] > 0.05, 7.2)
on['head over the shoulder (head left of body centre)'] = first(lambda i: HO[i] < 0.0, 7.2)
b2 = X[int(14.0 * FPS):int(14.5 * FPS)].mean()
on['approach'] = first(lambda i: b2 - X[i] > 0.02, 14.4)
h2 = Hm[int(22.5 * FPS):int(23.5 * FPS)].mean()
on['lie_down'] = first(lambda i: Hm[i] < 0.92 * h2, 23.5)
hy = np.array([M[i]['hy'] for i in range(N)]); hx = np.array([M[i]['hx'] for i in range(N)])
b3x, b3y = hx[int(25.9 * FPS):int(26.3 * FPS)].mean(), hy[int(25.9 * FPS):int(26.3 * FPS)].mean()
on['looks in'] = first(lambda i: np.hypot(hx[i] - b3x, hy[i] - b3y) > 6 or fr[i]['head_view'] == 'QBack', 26.0)
score_t = {'retreat': 1.0, 'retreat->watch': 2.333, 'refuse': 3.417, 'turns back to look': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'looks in': 26.4}
measured = [{'choice': k, 'score_t': score_t[k], 'measured_t': on[k], 'dt': None if on[k] is None else round(on[k] - score_t[k], 3)} for k in score_t]
measured.append({'choice': 'extra, not a score choice: head crosses to the door side of the body centroid (body turning back)', 'score_t': None,
                 'measured_t': on['head over the shoulder (head left of body centre)'], 'dt': None})
appr = [f for f in fr if f['state'] == 'approach']
endf = fr[-1]
summary = {'measured_choices': measured,
           'approach_head_below_back_share': round(sum(f['head_top_below_back'] for f in appr) / len(appr), 3),
           'refusal_facing_turned_share': round(sum(1 for f in fr if f['state'] == 'refuse' and f['facing'] == -1) / sum(1 for f in fr if f['state'] == 'refuse'), 3),
           'end_inside_share': endf['inside_share'], 'end_outside_share': endf['outside_share'],
           'min_x_score': min(f['x_score'] for f in fr), 'muzzle_x_world_during_look': min(f['muzzle_x_world'] for f in fr if 26.8 < f['t'] < 28.0),
           'wall_inner_face_x': WALL_IN, 'sill_outer_x': WALL_OUT,
           'look_in_head_view_frames': sum(1 for f in fr if f['head_view'] == 'QBack' and f['t'] > 26)}
json.dump({'about': 'SCION 22 trace: measured per scene frame from the render (dog silhouette and head pieces as composited). state = score state; measured onsets in summary.',
           'fps': FPS, 'summary': summary, 'frames': fr}, open(os.path.join(FOLDER, 'trace.json'), 'w'))
print(json.dumps(summary, indent=1))
