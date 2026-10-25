"""SCION 33 · trace.json from the render: the dog's silhouette mask (centroid, bbox), its head and muzzle on screen,
the back line; plus measured choice onsets. The camera is fixed, so x_screen is a valid position measure.
facing is measured on screen: +1 when the head is left of the body's centroid (toward the door), -1 when right."""
import os, json, pickle, math
import numpy as np
from geom import Camera, CAMS, PATH_Z
CAMOBJ = {k: Camera(name=k) for k in CAMS}


def x_world_from_screen(cam, sx, sy):
    """back-project the measured silhouette centroid onto the vertical plane of the dog's path (Z = PATH_Z)."""
    d = cam.ray(np.array([sx]), np.array([sy]))[0]
    s = (PATH_Z - cam.pos[2]) / d[2]
    return float(cam.pos[0] + d[0] * s)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
POSE = pickle.load(open(os.path.join(CACHE, 'pose.pkl'), 'rb'))['frames']
M = [json.load(open(os.path.join(CACHE, 'measure/%04d.json' % i))) for i in range(768)]


def posture(fr):
    c = fr['ctrl']
    if c['lie'] > 0.6: return 'lying, chin on paws' if c['rest'] > 0.6 else 'lying, head up'
    if c['lie'] > 0.1: return 'lying down' if True else ''
    mv = np.linalg.norm(POSE[min(767, fr['i'] + 1)]['dog']['R'] - fr['dog']['R']) * 24
    if abs(POSE[min(767, fr['i'] + 1)]['dog']['psi'] - fr['dog']['psi']) * 24 > 0.5: return 'turning in place'
    if mv > 0.05:
        back = (POSE[min(767, fr['i'] + 1)]['dog']['R'] - fr['dog']['R']) @ fr['dog']['F'] < 0
        return ('backing away' if back else 'walking') + (', crouched' if c['crouch'] > 0.5 else '') + (', head low' if c['head'] < 0.5 else '')
    return 'standing' + (', crouched' if c['crouch'] > 0.5 else '') + (', head low' if c['head'] < 0.5 else ', head up')


frames = []
for i in range(768):
    m = M[i]; fr = POSE[i]; s = SCORE['frames'][i]
    facing = 1 if m['head_x'] < m['cx'] else -1
    frames.append(dict(i=i, t=round(i / 24, 4), state=s['dog']['state'], x_score=round(float(fr['dog']['R'][0]), 4),
                       x_screen=round(m['cx'], 2), y_screen=round(m['cy'], 2), camera=m['cam'],
                       x_world_measured=round(x_world_from_screen(CAMOBJ[m['cam']], m['cx'], m['cy']), 4), facing=facing, posture=posture(fr),
                       head_screen=[round(m['head_x'], 1), round(m['head_y'], 1)], muzzle_screen=[round(m['muzzle_x'], 1), round(m['muzzle_y'], 1)],
                       back_line_y=round(m['back_y'], 1), head_below_back_px=round(m['head_y'] - m['back_y'], 1),
                       bbox=[m['x0'], m['y0'], m['x1'], m['y1']],
                       nose_x_world=round(float((fr['dog']['Hc'] + fr['dog']['Mdir'] * 0.17)[0]), 3),
                       tail_tip_x_world=round(float(fr['dog']['tail'][-1][0]), 3)))

cx = np.array([f['x_screen'] for f in frames]); hy = np.array([f['head_screen'][1] for f in frames])
hx = np.array([f['head_screen'][0] for f in frames])
mang = np.array([math.degrees(math.atan2(f['muzzle_screen'][1] - f['head_screen'][1], f['muzzle_screen'][0] - f['head_screen'][0])) for f in frames])
top = np.array([f['bbox'][1] for f in frames]); bot = np.array([f['bbox'][3] for f in frames])
T = np.arange(768) / 24


def first(cond, t0, t1=32):
    for i in range(768):
        if t0 <= T[i] < t1 and cond(i): return round(float(T[i]), 3)
    return None


def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)


i09 = int(0.9 * 24); i30 = int(3.30 * 24); i74 = int(7.30 * 24); i146 = int(14.5 * 24); i236 = int(23.6 * 24); i262 = int(26.2 * 24)
on = [
    dict(choice='watch -> retreat', score_t=1.0, measure='dog centroid moves right (away from the door) > 1.5 px from its 0.9 s position',
         t=first(lambda i: cx[i] - cx[i09] > 1.5, 0.9)),
    dict(choice='retreat -> watch', score_t=2.333, measure='head rises on screen: head y > 2 px above its lowest point of the retreat (1.4-2.2 s)',
         t=first(lambda i: hy[i] < hy[int(1.4 * 24):int(2.2 * 24)].max() - 2, 2.0)),
    dict(choice='watch -> refuse', score_t=3.417, measure='muzzle direction on screen turns > 10 deg from its 3.3 s heading (the head leads the turn)',
         t=first(lambda i: angdiff(mang[i], mang[i30]) > 10, 3.3)),
    dict(choice='refuse: back shown', score_t=None, measure='head right of the body centroid (facing measured -1)',
         t=first(lambda i: hx[i] > cx[i], 3.3)),
    dict(choice='refuse -> watch', score_t=7.458, measure='head lifts > 2 px off the paws (from its 7.3 s rest)',
         t=first(lambda i: hy[i] < hy[i74] - 2, 7.3)),
    dict(choice='watch -> approach', score_t=14.708, measure='dog centroid moves left (toward the door) > 1.5 px from its 14.5 s hold',
         t=first(lambda i: cx[i] - cx[i146] < -1.5, 14.5)),
    dict(choice='approach -> lie_down', score_t=23.792, measure='silhouette top drops > 3 px below its 23.6 s height',
         t=first(lambda i: top[i] - top[i236] > 3, 23.6)),
    dict(choice='hears come in: looks in', score_t=26.4, measure='muzzle direction on screen turns > 8 deg or head rises > 2 px from its 26.2 s pose',
         t=first(lambda i: angdiff(mang[i], mang[i262]) > 8 or hy[i] < hy[i262] - 2, 26.2)),
    dict(choice='settles, chin on paws, stays', score_t=None, measure='head drops > 3 px below its look-in height after 27.8 s',
         t=first(lambda i: hy[i] > hy[int(27.8 * 24)] + 3, 27.8)),
]
for o in on:
    o['dt'] = None if (o['t'] is None or o['score_t'] is None) else round(o['t'] - o['score_t'], 3)
    o['within_0.25s'] = None if o['dt'] is None else abs(o['dt']) <= 0.25

app = [f for f in frames if f['state'] == 'approach']
head_low = dict(frames=len(app), head_below_back_line=sum(1 for f in app if f['head_below_back_px'] > 0),
                min_px_below=min(f['head_below_back_px'] for f in app), mean_px_below=round(float(np.mean([f['head_below_back_px'] for f in app])), 2))
end = frames[-1]
summary = dict(onsets_measured=on, approach_head_low=head_low,
               end_pose=dict(x_score=end['x_score'], nose_x_world=end['nose_x_world'], tail_tip_x_world=end['tail_tip_x_world'],
                             house_wall_outer_x=0.40, house_wall_inner_x=0.24, sill_x=0.56,
                             reading='nose inside the inner face of the wall, body centre outside the sill edge, tail on the porch' if end['nose_x_world'] < 0.24 and end['tail_tip_x_world'] > 0.56 else 'check'),
               min_x_score=min(f['x_score'] for f in frames))
json.dump(dict(about='SCION 33 trace, measured from the render: x_screen/y_screen are the dog silhouette centroid (px, in that frame's camera), facing is measured on screen (head left of centroid = +1, toward the door), x_score is the rig root in world metres (= the score x mapping, 1 m = 1 m).',
               camera='two fixed set-ups, one cut at 20.5 s (A: wide, B: closer on the sill); x_world_measured back-projects the measured centroid through the frame\'s camera onto the plane of the path', summary=summary, frames=frames), open(os.path.join(ROOT, 'trace.json'), 'w'))
print(json.dumps(summary, indent=1))
