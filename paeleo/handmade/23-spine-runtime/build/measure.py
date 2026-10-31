"""SCION 23 · trace.json from the render: every number here is read off the rendered dog (its alpha, and the alpha of
its head slots), in wide-frame pixels with the camera's zoom undone. States switch at the onsets measured below."""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

sc = load_score(); SF = sc['frames']
M = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(CACHE, 'meas', '*.json')))]
assert len(M) == N, len(M)
T = np.array([m['t'] for m in M])


def wide_pt(m, x, y):
    return from_screen(m['zoom'], m['cx'], m['cy'], x, y)


bx = np.array([wide_pt(m, m['dog']['cx'], m['dog']['cy'])[0] for m in M])
by = np.array([wide_pt(m, m['dog']['cx'], m['dog']['cy'])[1] for m in M])
hx = np.array([wide_pt(m, m['head']['cx'], m['head']['cy'])[0] for m in M])
hy = np.array([wide_pt(m, m['head']['cx'], m['head']['cy'])[1] for m in M])
top = np.array([wide_pt(m, 0, m['dog']['y0'])[1] for m in M])
bot = np.array([wide_pt(m, 0, m['dog']['y1'])[1] for m in M])
hgt = bot - top


def at(t): return int(round(t * FPS))


def first(cond, t0, t1):
    for i in range(at(t0), at(t1)):
        if cond(i): return i
    return None


on = {}
r0 = bx[at(0.9)]
on['retreat'] = first(lambda i: bx[i] > r0 + 1.5, 0.9, 2.0)
i_low = at(1.4) + int(np.argmax(hy[at(1.4):at(2.6)]))
on['watch1'] = first(lambda i: hy[i] < hy[i_low] - 2.0, i_low / FPS, 3.2)
h0 = hx[at(3.3)]
on['refuse'] = first(lambda i: hx[i] > h0 + 2.0, 3.3, 4.2)
h1x, h1y = hx[at(7.3)], hy[at(7.3)]
on['watch2'] = first(lambda i: np.hypot(hx[i] - h1x, hy[i] - h1y) > 2.0, 7.3, 8.2)
b1 = bx[at(7.3)]
body_turn = first(lambda i: abs(bx[i] - b1) > 2.0 or abs(by[i] - by[at(7.3)]) > 2.0, 7.3, 9.0)
a0 = bx[at(14.6)]
on['approach'] = first(lambda i: bx[i] < a0 - 1.5, 14.6, 15.5)
bref = by[at(22.6):at(23.55)].max()
on['lie_down'] = first(lambda i: by[i] > bref + 2.5, 23.55, 24.6)
h3x, h3y = hx[at(26.3)], hy[at(26.3)]
look_in = first(lambda i: np.hypot(hx[i] - h3x, hy[i] - h3y) > 2.0, 26.3, 27.2)
seq = [('watch', 0), ('retreat', on['retreat']), ('watch', on['watch1']), ('refuse', on['refuse']),
       ('watch', on['watch2']), ('approach', on['approach']), ('lie_down', on['lie_down'])]
state = []
for i in range(N):
    s = 'watch'
    for name, k in seq:
        if k is not None and i >= k: s = name
    state.append(s)
hstand = np.median(hgt[at(9.5):at(14.0)])
frames = []
for i, m in enumerate(M):
    facing = 1 if hx[i] < bx[i] else -1
    post = 'lying' if hgt[i] < 0.66 * hstand else ('crouched' if hgt[i] < 0.88 * hstand else 'standing')
    frames.append(dict(i=i, t=round(T[i], 4), state=state[i], x_score=SF[i]['dog']['x'],
                       x_screen=round(m['dog']['cx'], 2), y_screen=round(m['dog']['cy'], 2),
                       x_world_measured=round((bx[i] - X0) / K, 4), facing=facing, posture=post,
                       head_x_wide=round(hx[i], 2), head_y_wide=round(hy[i], 2), height_wide=round(hgt[i], 2),
                       overlap_person_px=m['overlap_person_px']))
choices = [(1.0, 'watch -> retreat', 'retreat', 'dog centroid moves right (away from the door) > 1.5 px from 0.9 s'),
           (2.333, 'retreat -> watch', 'watch1', 'head lifts > 2 px from its lowest point in the retreat'),
           (3.417, 'watch -> refuse', 'refuse', 'head moves right (turning away) > 2 px from 3.3 s'),
           (7.458, 'refuse -> watch', 'watch2', 'head moves > 2 px from its 7.3 s rest (the head leads)'),
           (14.708, 'watch -> approach', 'approach', 'dog centroid moves left > 1.5 px from 14.6 s'),
           (23.792, 'approach -> lie_down', 'lie_down', 'dog centroid drops > 2.5 px below its lowest point in the last second of the approach')]
ons = []
for t, nm, k, how in choices:
    tt = None if on[k] is None else round(on[k] / FPS, 3)
    ons.append(dict(choice=nm, score_t=t, measured_t=tt, dt=None if tt is None else round(tt - t, 3),
                    within_025=tt is not None and abs(tt - t) <= 0.25, measure=how))
ons.append(dict(choice='refuse -> watch: body follows', score_t=7.458,
                measured_t=None if body_turn is None else round(body_turn / FPS, 3),
                measure='dog centroid moves > 2 px from 7.3 s (after the head)'))
ons.append(dict(choice='hears come in: looks in', score_t=26.4, measured_t=None if look_in is None else round(look_in / FPS, 3),
                measure='head moves > 2 px from 26.3 s'))
ref = [f for f in frames if f['state'] == 'refuse']
head_below = [f for f in frames if f['state'] == 'approach']
summary = dict(onsets_measured=ons,
               refusal_back_turned_share=round(sum(1 for f in ref if f['facing'] == -1) / max(1, len(ref)), 3),
               back_turned_from=next((f['t'] for f in ref if f['facing'] == -1), None),
               max_person_overlap_px=max(f['overlap_person_px'] for f in frames),
               end_x_world_measured=frames[-1]['x_world_measured'])
json.dump(dict(about='SCION 23 trace, measured from the render. x_screen/y_screen: dog alpha centroid in the output '
                     'frame (px). x_world_measured: that centroid with the camera undone, in metres on the score axis. '
                     'facing: +1 when the head-slot centroid is left of the body centroid (toward the door). '
                     'posture: from silhouette height. state: switches at the measured onsets in summary.',
               camera='wide until 17.5 s, slow push-in on the doorway complete by 23.6 s (zoom 1 -> 1.62)',
               summary=summary, frames=frames), open(os.path.join(FOLDER, 'trace.json'), 'w'))
print(json.dumps(summary, indent=1))
