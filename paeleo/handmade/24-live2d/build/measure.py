"""SCION-24 measurement: read cache/raw.json (positions of the dog's drawn geometry in every rendered scene frame: the spine
points of the torso mesh, the head and nose of the head mesh, the paws, in screen pixels, with the camera of that frame) and
write ../trace.json, ../proof/onsets.json and ../proof/measures.json.

Onsets are measured, not copied from the score: each choice is the first frame where the drawn dog starts the change that
the choice names (backing away = the spine moves away from the door; stopping = the crouch lifts; refusing = the head starts
to swing away; turning to look = it rises from lying; coming = the spine moves toward the door; lying down = the withers
drop; looking in = the head starts to move after its hold). The trace's state switches at those measured frames."""
import json, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
raw = json.load(open(os.path.join(HERE, 'cache', 'raw.json')))
score = json.load(open(os.path.join(OUT, '..', 'score', 'threshold-score.json')))


def W(f, s):  # screen px -> world metres (inverse of this frame's camera; y up, in the picture plane)
    c = f['cam']
    return [c['cx'] + (s[0] - 640) / c['K'], c['cy'] - (s[1] - 360) / c['K']]


g = []
for f in raw:
    w, h = W(f, f['withers']), W(f, f['hip'])
    hd, ns = W(f, f['head']), W(f, f['nose'])
    g.append({'x': (w[0] + h[0]) / 2, 'wy': w[1], 'hx': hd[0], 'hy': hd[1], 'nx': ns[0], 'top': W(f, [0, f['headPolysTop']])[1]})
fps = 24


def first(cond, a, b):
    for i in range(max(1, a), min(len(g) - 2, b)):
        if cond(i):
            return i
    return None


def sec(t): return int(round(t * fps))


on = {}
on['retreat'] = first(lambda i: g[i]['x'] - g[i - 1]['x'] > 0.002 and g[i + 1]['x'] - g[i]['x'] > 0.002, sec(0.5), sec(1.6))
on['watch_1'] = first(lambda i: g[i]['wy'] - g[i - 1]['wy'] > 0.003 and g[i + 1]['wy'] - g[i]['wy'] > 0.003, sec(1.9), sec(2.9))
hm = lambda i: ((g[i]['hx'] - g[i - 1]['hx']) ** 2 + (g[i]['hy'] - g[i - 1]['hy']) ** 2) ** .5
on['refuse'] = first(lambda i: hm(i) > 0.004 and hm(i + 1) > 0.004, sec(3.0), sec(4.0))
on['watch_2'] = first(lambda i: g[i]['wy'] - g[i - 1]['wy'] > 0.003 and g[i + 1]['wy'] - g[i]['wy'] > 0.003, sec(7.0), sec(8.0))
on['approach'] = first(lambda i: g[i - 1]['x'] - g[i]['x'] > 0.002 and g[i]['x'] - g[i + 1]['x'] > 0.002, sec(14.2), sec(15.3))
on['lie_down'] = first(lambda i: g[i - 1]['wy'] - g[i]['wy'] > 0.003 and g[i]['wy'] - g[i + 1]['wy'] > 0.003, sec(23.3), sec(24.4))
on['look_in'] = first(lambda i: hm(i) > 0.004 and hm(i + 1) > 0.004, sec(26.0), sec(27.0))
# the turned back: first frame the drawn spine points away from the door (hip left of withers)
back = first(lambda i: raw[i]['hip'][0] - raw[i]['withers'][0] < -8, sec(3.4), sec(4.5))
# the head round to the door at 7.46: first frame the nose is left of the head centre again (facing the door)
headround = first(lambda i: raw[i]['nose'][0] < raw[i]['head'][0] - 4, sec(7.4), sec(8.5))
# looking in: first frame the near eye is hidden (head turned past profile into the room: back of the head to the viewer)
lookin_deep = first(lambda i: max(raw[i]['facing']['eyeA'], raw[i]['facing']['eyeB']) < 0.06, sec(26.0), sec(28.0))

SC = {'retreat': 1.0, 'watch_1': 2.333, 'refuse': 3.417, 'watch_2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
onsets = {k: {'score_t': SC[k], 'measured_frame': v, 'measured_t': None if v is None else round(v / fps, 3),
              'dt': None if v is None else round(v / fps - SC[k], 3)} for k, v in on.items()}
onsets['_also'] = {'back_shown_t': None if back is None else round(back / fps, 3), 'head_round_to_door_t': None if headround is None else round(headround / fps, 3),
                   'head_into_room_past_profile_t': None if lookin_deep is None else round(lookin_deep / fps, 3)}

seq = [(0, 'watch'), (on['retreat'], 'retreat'), (on['watch_1'], 'watch'), (on['refuse'], 'refuse'), (on['watch_2'], 'watch'), (on['approach'], 'approach'), (on['lie_down'], 'lie_down')]
frames = []
for k, f in enumerate(raw):
    st = [s for i0, s in seq if i0 is not None and k >= i0][-1]
    dx = raw[k]['hip'][0] - raw[k]['withers'][0]
    facing = 1 if dx > 8 else (-1 if dx < -8 else 0)
    vx = (g[min(k + 1, len(g) - 1)]['x'] - g[max(k - 1, 0)]['x']) * fps / 2
    wy = g[k]['wy']
    posture = 'lie' if wy < 0.4 else ('crouch' if wy < 0.5 else ('walk' if abs(vx) > 0.08 else 'stand'))
    frames.append({'i': f['i'], 't': round(f['t'], 4), 'state': st, 'x_score': f['x_score'],
                   'x_screen': round((raw[k]['withers'][0] + raw[k]['hip'][0]) / 2, 2), 'y_screen': round((raw[k]['withers'][1] + raw[k]['hip'][1]) / 2, 2),
                   'x_world_measured': round(g[k]['x'], 4), 'facing': facing, 'posture': posture,
                   'withers_height_m': round(wy, 4), 'head_top_m': round(g[k]['top'], 4), 'nose_screen': [round(v, 1) for v in raw[k]['nose']],
                   'head_turned_into_room': max(raw[k]['facing']['eyeA'], raw[k]['facing']['eyeB']) < 0.06,
                   'params': {kk: round(vv, 3) if isinstance(vv, (int, float)) else vv for kk, vv in f['pose'].items()}})

# protected conditions the representation supports numerically
appr = [fr for fr in frames if fr['state'] == 'approach']
below = sum(1 for fr in appr if fr['head_top_m'] < fr['withers_height_m']) / max(1, len(appr))
tail_x = [W(raw[k], raw[k]['tail'])[0] for k in range(len(raw))]
end = frames[-1]
nose_end = W(raw[-1], raw[-1]['nose'])[0]
min_nose = min(W(raw[k], raw[k]['nose'])[0] for k in range(len(raw)))
sp_app = [(frames[k]['x_world_measured'], score['frames'][k]['dog']['x']) for k in range(len(frames)) if frames[k]['state'] == 'approach']
measures = {
    'head_skull_below_withers_share_during_approach': round(below, 3),
    'end_nose_x_m': round(nose_end, 3), 'end_tail_tip_x_m': round(tail_x[-1], 3), 'door_frame_x_m': [-0.22, 0.40], 'house_inside_x_lt': -0.22,
    'min_nose_x_m_whole_film': round(min_nose, 3),
    'end_state': end['state'], 'end_posture': end['posture'], 'end_x_score': end['x_score'],
    'approach_distance_measured_m': round(sp_app[0][0] - sp_app[-1][0], 3) if sp_app else None,
    'approach_distance_score_m': round(sp_app[0][1] - sp_app[-1][1], 3) if sp_app else None,
    'retreat_distance_measured_m': round(max(fr['x_world_measured'] for fr in frames if fr['t'] < 3.4) - frames[0]['x_world_measured'], 3),
    'refusal_frames_back_turned_share': round(sum(1 for fr in frames if fr['state'] == 'refuse' and fr['facing'] == -1) / max(1, sum(1 for fr in frames if fr['state'] == 'refuse')), 3),
}
json.dump({'about': 'per scene frame, measured from the drawn geometry of the render (spine points of the torso mesh, head and nose of the head mesh). x_world_measured inverts each frame\'s camera.', 'frames': frames},
          open(os.path.join(OUT, 'trace.json'), 'w'))
os.makedirs(os.path.join(OUT, 'proof'), exist_ok=True)
json.dump(onsets, open(os.path.join(OUT, 'proof', 'onsets.json'), 'w'), indent=1)
json.dump(measures, open(os.path.join(OUT, 'proof', 'measures.json'), 'w'), indent=1)
print(json.dumps(onsets, indent=1)); print(json.dumps(measures, indent=1))
