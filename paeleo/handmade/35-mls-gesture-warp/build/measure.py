"""SCION 35 · trace.json from the render: every value is measured from the rendered layers of each frame
(build/cache/meas/*.json, written by render.py from the composited dog coverage), except x_score (where the score put
the dog). Choice onsets are detected from rendered signals; the trace's state labels follow those measured onsets."""
import json, os, glob
import numpy as np
from common import CACHE, ROOT, load_score

SCORE = load_score()
SF = SCORE['frames']
M = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(CACHE, 'meas', '*.json')))]
assert len(M) == 768, len(M)
T = np.array([m['t'] for m in M])
cx = np.array([m['cx'] for m in M]); top = np.array([m['top'] for m in M]); bot = np.array([m['bottom'] for m in M])
hx = np.array([m['head_cx'] if m['head_cx'] is not None else np.nan for m in M])
hy = np.array([m['head_cy'] if m['head_cy'] is not None else np.nan for m in M])
tx = np.array([m['torso_cx'] for m in M])
rel = hx - tx           # head relative to the body: negative = head toward the door (screen-left)


def first(cond, t_from):
    for i in range(len(M)):
        if T[i] >= t_from and cond(i):
            return i
    return None


def at(t):
    return int(round(t * 24))


onsets = []
# 1 watch -> retreat: the rendered dog moves away from the door (> 1 px right of where it stood at 0.75 s)
i0 = at(0.75)
i = first(lambda i: cx[i] - cx[i0] > 1.0, 0.75)
onsets.append(dict(choice='watch -> retreat', to='retreat', score_t=1.0, i=i, signal='dog centroid moves > 1 px away from the door (from its 0.75 s place)'))
# 2 retreat -> watch: the head comes back up out of the cower (rendered head centre rises > 3 px from its lowest)
lo = np.nanmax(hy[at(1.4):at(2.2)])
i = first(lambda i: hy[i] < lo - 3.0, 2.0)
onsets.append(dict(choice='retreat -> watch', to='watch', score_t=2.333, i=i, signal='rendered head centre rises > 3 px above its lowest (cowering) height'))
# 3 watch -> refuse: the head swings away from the door relative to the body (> 4 px from its 3.2 s offset)
r0 = rel[at(3.2)]
i = first(lambda i: rel[i] - r0 > 4.0, 3.2)
onsets.append(dict(choice='watch -> refuse', to='refuse', score_t=3.417, i=i, signal='rendered head centre swings > 4 px away from the door, relative to the torso'))
# 4 refuse -> watch: the head comes round toward the door relative to the body (> 4 px from its 7.0 s offset)
r0 = rel[at(7.0)]
i = first(lambda i: r0 - rel[i] > 4.0, 7.0)
onsets.append(dict(choice='refuse -> watch', to='watch', score_t=7.458, i=i, signal='rendered head centre swings > 4 px toward the door, relative to the torso (hips still down)'))
# 5 watch -> approach: the dog moves toward the door (> 1 px left of where it stood at 14.4 s)
i0 = at(14.4)
i = first(lambda i: cx[i0] - cx[i] > 1.0, 14.4)
onsets.append(dict(choice='watch -> approach', to='approach', score_t=14.708, i=i, signal='dog centroid moves > 1 px toward the door'))
# 6 approach -> lie_down: the top of the rendered dog drops > 5 px below its height at 23.5 s
i0 = at(23.5)
i = first(lambda i: top[i] - top[i0] > 5.0, 23.5)
onsets.append(dict(choice='approach -> lie_down', to='lie_down', score_t=23.792, i=i, signal='top of the rendered dog drops > 5 px'))
# 7 (hears come in) looks in: the rendered head moves into the doorway / turns (centre shifts > 3 px) after 26.2 s
i0 = at(26.2)
i = first(lambda i: np.hypot(hx[i] - hx[i0], hy[i] - hy[i0]) > 3.0, 26.2)
look = dict(choice='lying: looks in', to=None, score_t=26.4, i=i, signal='rendered head centre moves > 3 px (turning in through the door)')
for o in onsets + [look]:
    o['t'] = round(o['i'] / 24, 3) if o['i'] is not None else None
    o['dt'] = round(o['t'] - o['score_t'], 3) if o['t'] is not None else None
    o['within_0.25s'] = o['dt'] is not None and abs(o['dt']) <= 0.25

# states from the measured onsets
seq = [('watch', 0)] + [(o['to'], o['i']) for o in onsets]
state = []
for i in range(768):
    s = 'watch'
    for st, oi in seq:
        if oi is not None and i >= oi:
            s = st
    state.append(s)

# standing height for posture
stand_h = np.median((bot - top)[at(9):at(14)])
frames = []
for i, m in enumerate(M):
    h = bot[i] - top[i]
    posture = 'standing' if h > 0.86 * stand_h else ('crouched' if h > 0.66 * stand_h else 'lying')
    r = rel[i]
    facing = 1 if r < -6 else (-1 if r > 6 else 0)    # 0: head over the body (rear view mid-turn)
    frames.append(dict(i=i, t=m['t'], state=state[i], x_score=SF[i]['dog']['x'], x_screen=round(m['cx'], 2), y_screen=round(m['cy'], 2),
                       facing=facing, posture=posture, view_print=m['shown'], head_rel_x=round(float(r), 1),
                       top=m['top'], bottom=m['bottom'], inside_px=m['inside_px'], outside_px=m['outside_px'],
                       strain={k: [round(v['aniso_max'], 3), round(v['area_min'], 3), round(v['area_max'], 3), v['folds']] for k, v in m['strain'].items()}))

# distortion summary per family
fam = {}
for m in M:
    for k, v in m['strain'].items():
        f = fam.setdefault(v['family'], dict(aniso=[], area_min=[], area_max=[], folds=0, handle_err=0.0))
        f['aniso'].append(v['aniso_max']); f['area_min'].append(v['area_min']); f['area_max'].append(v['area_max'])
        f['folds'] += v['folds']; f['handle_err'] = max(f['handle_err'], v['handle_err'])
dist = {k: dict(aniso_max_median=round(float(np.median(v['aniso'])), 3), aniso_max_p95=round(float(np.percentile(v['aniso'], 95)), 3),
                aniso_max_max=round(float(np.max(v['aniso'])), 3), area_min=round(float(np.min(v['area_min'])), 3),
                area_max=round(float(np.max(v['area_max'])), 3), folded_cells_total=v['folds'], handle_error_px_max=v['handle_err'])
        for k, v in fam.items()}
end = M[-1]
summary = dict(onsets_measured=onsets, look_in=look, distortion_by_family=dist,
               end_lying=dict(inside_px=end['inside_px'], outside_px=end['outside_px'], tail_inside=end['tail_inside'],
                              posture=frames[-1]['posture']),
               audio=json.load(open(os.path.join(CACHE, 'audio.json'))) if os.path.exists(os.path.join(CACHE, 'audio.json')) else None)
about = ('SCION 35 trace, measured from the render: x_screen/y_screen = centroid of the rendered dog coverage (film px, static '
         'camera); facing = +1 when the rendered head layer sits > 6 px on the door side of the rendered torso, -1 on the far side, '
         '0 when it is over the body (rear view mid-turn); posture from the rendered height vs the standing height; state = the '
         'score state switched at the onsets MEASURED here (signals listed in summary); strain per layer = [max anisotropy of the '
         'dot grid (s1/s2), min and max area ratio, folded cells]; x_score = the score x the dog was placed at.')
json.dump(dict(about=about, summary=summary, frames=frames), open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
for o in onsets + [look]:
    print(o['choice'], o['score_t'], o['t'], o['dt'], o['within_0.25s'])
print(json.dumps(dist, indent=0))
print('end', summary['end_lying'])
