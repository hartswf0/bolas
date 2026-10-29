"""Frame regression analyst: trace.json from the render's own measurements, plus measured choice onsets."""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

plan = json.load(open(os.path.join(CACHE, 'perform.json')))
meas = {}
for p in sorted(glob.glob(os.path.join(CACHE, 'measure_*.json'))):
    meas.update(json.load(open(p)))
S = score()


def facing(i):
    """Measured on screen: +1 when the muzzle points toward the door (left of the head joint), -1 away.
    The rear view (no muzzle visible) is -1: the dog's back is what the screen shows."""
    m = meas[str(i)]
    if 'nose' in m:
        return 1 if m['nose'][0] < m['joint'][0] else -1
    return -1


def posture(i):
    m = meas[str(i)]
    bb = m['bbox']
    h = (bb[3] - bb[1]) / cam_for(plan[i]['t'])['s']        # metres tall on screen
    if h < 0.42:
        return 'lying'
    if h < 0.62:
        return 'low'
    return 'standing'


frames = []
for i in range(N_SCENE):
    m = meas[str(i)]; f = plan[i]
    frames.append(dict(i=i, t=round(f['t'], 4), state=f['state'], x_score=f['x'], x_screen=round(m['cx'], 2),
                       y_screen=round(m['cy'], 2), x_world_measured=round(m['x_world_measured'], 4),
                       facing=facing(i), posture=posture(i), view=f['view'] + ('_mirrored' if f['mirror'] else ''),
                       camera='A' if f['t'] < CUT_T else 'B', inverted_triangles=m['inverted'], arap_energy=m['energy'],
                       inside_door_share=round(m.get('inside_share', 0), 3)))


def first(pred, lo, hi):
    for k in range(lo, hi):
        if pred(k):
            return k
    return None

# measured onsets from rendered signals
on = []
xw = [fr['x_world_measured'] for fr in frames]
top = [meas[str(i)]['bbox'][1] for i in range(N_SCENE)]
k0 = int(0.9 * FPS)
k = first(lambda k: frames[k]['x_world_measured'] - xw[k0] > 1.5 / CAMS['A']['s'] or top[k] - top[k0] > 3, k0 + 1, 80)
on.append(dict(choice='watch -> retreat', score_t=1.0, t=frames[k]['t'], signal='dog drops > 3 px or moves away > 1.5 px from its 0.9 s place'))
low = min(range(36, 56), key=lambda k: -top[k])
k = first(lambda k: top[k] < top[low] - 3, low, 82)
on.append(dict(choice='retreat -> watch', score_t=2.333, t=frames[k]['t'], signal='the top of the dog rises 3 px above its lowest (cowering) height'))
k = first(lambda k: frames[k]['facing'] == -1, 80, 120)
on.append(dict(choice='watch -> refuse', score_t=3.417, t=frames[k]['t'], signal='rendered muzzle turns away from the door (or the rear view shows)'))
k = first(lambda k: frames[k]['view'].startswith('P_mirrored') and frames[k]['facing'] == -1, 80, 140)
on.append(dict(choice='refuse: the back shown in profile', score_t=None, t=frames[k]['t'], signal='whole body in profile facing away'))
k = first(lambda k: frames[k]['facing'] == 1, 150, 230)
on.append(dict(choice='refuse -> watch', score_t=7.458, t=frames[k]['t'], signal='rendered muzzle points to the door again'))
k0 = int(14.5 * FPS)
k = first(lambda k: xw[k] < xw[k0] - 1.5 / CAMS['A']['s'], k0, 420)
on.append(dict(choice='watch -> approach', score_t=14.708, t=frames[k]['t'], signal='body centre moves toward the door > 1.5 px'))
k0 = int(23.4 * FPS)
wy = [meas[str(i)].get('withers_y', np.nan) for i in range(N_SCENE)]
base = np.nanmax(wy[k0 - 8:k0 + 1])
k = first(lambda k: wy[k] - base > 3, k0, 620)
on.append(dict(choice='approach -> lie_down', score_t=23.792, t=frames[k]['t'], signal='rendered withers (shoulder patch) 3 px below its walking height'))
k0 = int(26.2 * FPS)
ny0 = meas[str(k0)]['nose'][1]
k = first(lambda k: meas[str(k)]['nose'][1] < ny0 - 2, k0, 700)
on.append(dict(choice='hears come in: looks in', score_t=26.4, t=frames[k]['t'], signal='muzzle lifts and reaches into the doorway (> 2 px)'))
for o in on:
    o['dt'] = None if o['score_t'] is None else round(o['t'] - o['score_t'], 3)
    o['within_0.25s'] = None if o['score_t'] is None else abs(o['dt']) <= 0.25

summary = dict(onsets_measured=on,
               inverted_triangles_total=int(sum(fr['inverted_triangles'] for fr in frames)),
               frames_with_inversions=int(sum(1 for fr in frames if fr['inverted_triangles'] > 0)),
               max_energy=max(fr['arap_energy'] for fr in frames),
               end_inside_door_share=frames[-1]['inside_door_share'],
               head_below_back_approach=None)
about = ('SCION 34 trace, measured from the render: x_screen/y_screen = alpha centroid of the rendered dog (px, in that '
         "frame's camera); x_world_measured back-projects it through the camera (two fixed set-ups, a cut at 20.5 s); "
         'facing = +1 when the rendered muzzle points to the door; posture from the rendered height; x_score = the score x '
         'the dog was placed at.')
json.dump(dict(about=about, summary=summary, frames=frames), open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
print(json.dumps(summary, indent=1))
