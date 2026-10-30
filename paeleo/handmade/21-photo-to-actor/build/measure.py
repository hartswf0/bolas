"""Measure what the dog did, from its own rendered layer (alpha masks saved by render.py), and write trace.json.

Per frame: x_screen / y_screen = centroid of the rendered dog alpha; bbox; head-end metrics taken from the alpha itself
(the leading 24 % of the body's width on the side it faces); mask change against the previous frame (IoU after
centring). The state written to the trace is the MEASURED state: each choice's onset is the first frame at which the
picture shows it, by the rule named in onsets[*].rule. Facing = the body orientation drawn (mirrored or not), checked
against the head-end side of the mask.
"""
import glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
CACHE = os.path.join(FOLDER, 'build', 'cache')
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
perf = json.load(open(os.path.join(CACHE, 'performance.json')))
M = {}; A = {}
for f in glob.glob(os.path.join(CACHE, 'measure_*.json')): M.update({int(k): v for k, v in json.load(open(f)).items()})
for f in glob.glob(os.path.join(CACHE, 'alpha_*.npz')):
    z = np.load(f); A.update({int(k[1:]): z[k] for k in z.files})
N = len(perf); FPS = 24
assert len(M) == N and len(A) == N, (len(M), len(A))
X0, KM = 330, 180.0

cx = np.array([M[i]['dog']['centroid'][0] for i in range(N)])
cy = np.array([M[i]['dog']['centroid'][1] for i in range(N)])
bb = np.array([M[i]['dog']['bbox'] for i in range(N)])
hgt = bb[:, 3] - bb[:, 1]; wid = bb[:, 2] - bb[:, 0]
facing = np.array([r['facing'] for r in perf])

# head-end metrics from the alpha (2x downsampled canvas)
head_top = np.zeros(N); head_cy = np.zeros(N); back_top = np.zeros(N); iou = np.ones(N)
prev = None
for i in range(N):
    a = A[i]; oy = M[i]['dog']['alpha_origin'][1]
    ys, xs = np.nonzero(a)
    x0, x1 = xs.min(), xs.max(); w = x1 - x0
    if facing[i] > 0: sel = xs <= x0 + 0.24 * w; mid = (xs > x0 + 0.35 * w) & (xs < x0 + 0.75 * w)
    else: sel = xs >= x1 - 0.24 * w; mid = (xs < x1 - 0.35 * w) & (xs > x1 - 0.75 * w)
    head_top[i] = ys[sel].min() * 2 + oy; head_cy[i] = ys[sel].mean() * 2 + oy
    back_top[i] = ys[mid].min() * 2 + oy
    # centred mask change
    c = np.zeros((200, 280), bool); sy, sx_ = int(ys.mean()), int(xs.mean())
    yy = np.clip(ys - sy + 100, 0, 199); xx = np.clip(xs - sx_ + 140, 0, 279); c[yy, xx] = True
    if prev is not None: iou[i] = (c & prev).sum() / max(1, (c | prev).sum())
    prev = c

vx = np.r_[0, np.diff(cx)]
t = np.arange(N) / FPS


def first(cond, t0, t1):
    for i in range(N):
        if t0 <= t[i] <= t1 and cond(i): return i
    return None


ON = {}
# 1 retreat: the centroid starts moving away from the door (screen right) faster than 0.5 px/frame
i1 = first(lambda i: vx[i] > 0.5, 0.5, 2.0); ON['retreat'] = (i1, 'centroid moves away from the door > 0.5 px/frame')
# 2 watch: stops cowering: the head end rises 3 px above its lowest point during the retreat
lowest = max(head_cy[i1:i1 + 30])
i2 = first(lambda i: i > i1 + 6 and head_cy[i] < lowest - 3 and head_cy[i] < head_cy[i - 1], 1.8, 3.0); ON['watch_1'] = (i2, 'head end rises 3 px from its lowest point in the retreat')
# 3 refuse: the picture changes view (mask IoU with the previous frame < 0.8: the turn away begins)
i3 = first(lambda i: iou[i] < 0.8 or abs(head_top[i] - head_top[i - 1]) > 4, 3.0, 4.0); ON['refuse'] = (i3, 'mask change: head-end/turn sprite replaces the profile (IoU < 0.8 or head-end jump > 4 px)')
# 4 watch: the head comes round (mask change at the head end while the body is still down)
i4 = first(lambda i: iou[i] < 0.9 or abs(head_top[i] - head_top[i - 1]) > 4, 7.0, 8.0); ON['watch_2'] = (i4, 'head end changes (IoU < 0.9 or head-end jump > 4 px) while the body lies')
# 5 approach: the centroid moves toward the door faster than 0.3 px/frame
i5 = first(lambda i: vx[i] < -0.3, 14.0, 15.5); ON['approach'] = (i5, 'centroid moves toward the door > 0.3 px/frame')
# 6 lie down: the body's back line drops 3 px below its walking height
ref_back = np.median(back_top[540:565])
i6 = first(lambda i: back_top[i] > ref_back + 3, 23.0, 24.5); ON['lie_down'] = (i6, 'back line drops 3 px below its height on the approach')
# 7 (not a state change) looks in: the head artwork changes (profile -> foreshortened -> back of head), seen as a mask change
# at the head end of the plate-space layer after the cut to the close shot
i7 = first(lambda i: i >= 634 and (iou[i] < 0.97 or abs(head_top[i] - head_top[i - 1]) >= 2), 26.0, 27.5)
ON['looks_in'] = (i7, 'first head-end mask change after the cut to the close shot (IoU < 0.97 or head-end top moves >= 2 px)')

order = [('retreat', 1.0), ('watch_1', 2.333), ('refuse', 3.417), ('watch_2', 7.458), ('approach', 14.708), ('lie_down', 23.792)]
state = []
cur = 'watch'
bounds = [(ON[k][0], {'watch_1': 'watch', 'watch_2': 'watch'}.get(k, k)) for k, _ in order]
for i in range(N):
    for b, s in bounds:
        if b is not None and i == b: cur = s
    state.append(cur)

frames = []
for i in range(N):
    lie = perf[i]['pose']['lie']
    post = 'lying' if hgt[i] < 0.68 * np.median(hgt[200:340]) else ('walking' if abs(vx[i]) > 0.3 else 'standing')
    if perf[i]['view'] != 'rig': post = 'turning (%s view)' % perf[i]['view']
    frames.append({'i': i, 't': round(i / FPS, 4), 'state': state[i], 'state_score': perf[i]['state_score'],
                   'x_score': perf[i]['x'], 'x_screen': round(float(cx[i]), 2), 'y_screen': round(float(cy[i]), 2),
                   'x_world_measured': round(float((cx[i] - X0 + 54) / KM), 4),
                   'camera': M[i]['dog'].get('camera', 'wide'),
                   'x_screen_close': M[i]['dog'].get('centroid_screen_close', [None])[0],
                   'facing': int(facing[i]), 'posture': post, 'view': perf[i]['view'], 'head_view': perf[i]['pose']['head_view'],
                   'head_flip': perf[i]['pose']['head_flip'], 'bbox': [int(v) for v in bb[i]],
                   'head_end_top': round(float(head_top[i]), 1), 'head_end_cy': round(float(head_cy[i]), 1),
                   'back_top': round(float(back_top[i]), 1), 'head_below_back_px': round(float(head_cy[i] - back_top[i]), 1),
                   'mask_iou_prev': round(float(iou[i]), 3)})
onsets = []
for k, ts in order + [('looks_in', 26.4)]:
    i, rule = ON[k]
    onsets.append({'choice': k, 't_score': ts, 'frame': i, 't_measured': None if i is None else round(i / FPS, 3),
                   'dt': None if i is None else round(i / FPS - ts, 3), 'rule': rule})
appr = [f for f in frames if f['state'] == 'approach']
summary = {'approach_head_below_back_px_min': min(f['head_below_back_px'] for f in appr),
           'approach_head_below_back_px_median': float(np.median([f['head_below_back_px'] for f in appr])),
           'mapping': 'plate x = 330 + 180 * x_score - 54 (the score x is the dog\'s loins, 0.3 m behind its body centre). Wide static camera except a 2x close shot on the sill at frames 634-677 (26.42-28.21 s, window x 40-680, y 360-720); x_world_measured is the measured plate centroid in metres for every frame; x_screen is the plate centroid, x_screen_close the on-screen centroid in the close shot',
           'refuse_frames_turned': sum(1 for f in frames if f['state'] == 'refuse' and f['facing'] < 0),
           'refuse_frames': sum(1 for f in frames if f['state'] == 'refuse')}
json.dump({'about': 'SCION 21 photo-to-actor: the dog measured from its own rendered alpha layer, per scene frame. '
                    'state = measured state (onsets below); state_score = the score\'s label for comparison.',
           'fps': FPS, 'onsets_measured': onsets, 'summary': summary, 'frames': frames},
          open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
for o in onsets: print(o)
print(summary)
