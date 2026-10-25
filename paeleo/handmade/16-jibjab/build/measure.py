"""SCION 16 JibJab: the trace, measured from the film's own render (mattes read back from the canvas every frame).
Reads build/cache/measure-<cast>.json (per scene frame: torso matte, head matte, whole-dog matte, head view, occlusion)
Writes trace.json: per frame {i, t, state, x_score, x_screen, y_screen, facing, posture, ...} and the measured choice onsets.
The state is NOT copied from the score: it is segmented at onsets detected in the measured signals, in order.
"""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cast = sys.argv[1] if len(sys.argv) > 1 else 'paper'
M = json.load(open(os.path.join(HERE, f'build/cache/measure-{cast}.json')))
SC = json.load(open(os.path.join(HERE, '..', 'score', 'threshold-score.json')))
F = {f['i']: f for f in SC['frames']}
S, CX = 205.0, 290.0
n = len(M)
assert n == 768, n


def sm(a, k=2):
    return [sum(a[max(0, i - k):i + k + 1]) / len(a[max(0, i - k):i + k + 1]) for i in range(len(a))]


tx = [m['torso']['cx'] for m in M]; ty = [m['torso']['cy'] for m in M]
ttop = [m['torso']['y0'] for m in M]
hx = [m['head']['cx'] if m['head'] else m['torso']['cx'] for m in M]
hy = [m['head']['cy'] if m['head'] else m['torso']['cy'] for m in M]
dh = [m['dog']['y1'] - m['dog']['y0'] for m in M]
vx = [0] + [tx[i] - tx[i - 1] for i in range(1, n)]
vxs = sm(vx, 2)
dxh = [hx[i] - tx[i] for i in range(n)]          # head relative to body: negative = head toward the door (left)
hh = [ttop[i] - hy[i] for i in range(n)]          # head height above the line of the back (px; negative = below)
t = [i / 24 for i in range(n)]


def first(cond, a, b=n):
    for i in range(a, b):
        if cond(i): return i
    return None


ons = {}
# 1 retreat: the body starts moving away from the door (right), measured on the torso matte
i1 = first(lambda i: vxs[i] > 0.8 and vx[i] > 0.5, 1)
ons['retreat'] = i1
# 2 watch: the head comes up out of the retreat crouch (head matte rising by > 1 px/frame)
hys = sm(hy, 1)
i2 = first(lambda i: hys[i - 1] - hys[i] > 1.0 and hh[i] > min(hh[i1:i]) + 3, i1 + 8)
ons['watch'] = i2
# 3 refuse: the head drops or swings away from the door (relative to its watch baseline)
base_dx = sum(dxh[i2 + 10:i2 + 20]) / 10; base_hy = sum(hy[i2 + 10:i2 + 20]) / 10
i3 = first(lambda i: dxh[i] - base_dx > 6 or hy[i] - base_hy > 5, i2 + 20)
ons['refuse'] = i3
# 4 watch: after the back has been turned for a while, the head comes back round / up toward the door
ref_dx = sum(dxh[i3 + 60:i3 + 70]) / 10; ref_hy = sum(hy[i3 + 60:i3 + 70]) / 10
i4 = first(lambda i: ref_dx - dxh[i] > 6 or ref_hy - hy[i] > 5, i3 + 70)
ons['watch2'] = i4
# 5 approach: the body starts moving toward the door
i5 = first(lambda i: vxs[i] < -0.8 and vx[i] < -0.5, i4 + 24)
ons['approach'] = i5
# 6 lie_down: the body plate goes down (torso matte centre drops > 4 px below its walking line)
walk_cy = sorted(ty[i5 + 24:i5 + 180])[len(ty[i5 + 24:i5 + 180]) // 2]
i6 = first(lambda i: ty[i] - max(ty[i - 12:i]) > 4 and abs(vxs[i]) < 1.5, i5 + 48)
ons['lie_down'] = i6
# 7 looks in: the head starts to come up and round into the room (head matte rises > 4 px over its last half second)
i7 = first(lambda i: max(hy[i - 12:i]) - hy[i] > 4, i6 + 36)
ons['look_in'] = i7

seq = [('watch', 0), ('retreat', i1), ('watch', i2), ('refuse', i3), ('watch', i4), ('approach', i5), ('lie_down', i6)]
state = []
for i in range(n):
    s = 'watch'
    for name, k in seq:
        if k is not None and i >= k: s = name
    state.append(s)

stand_h = sorted(dh[:20])[10]
frames = []
for i in range(n):
    m = M[i]
    d = dxh[i]
    facing = 'door' if d < -4 else ('away' if d > 4 else ('away' if m['view'] in ('B', 'BL~') else 'door'))
    lying = dh[i] < 0.72 * stand_h
    posture = 'lying' if lying else ('crouched' if hh[i] < -8 else 'standing')
    frames.append({'i': i, 't': round(t[i], 4), 'state': state[i], 'x_score': F[i]['dog']['x'],
                   'x_screen': round(tx[i], 1), 'y_screen': round(ty[i], 1),
                   'x_world_from_screen': round((tx[i] - CX) / S, 3),
                   'facing': facing, 'posture': posture, 'head_view': m['view'], 'head_behind_torso': m['headBehind'],
                   'head_above_back_px': round(hh[i], 1), 'head_x_rel_body_px': round(d, 1),
                   'dog_height_px': dh[i], 'score_state': F[i]['dog']['state']})

score_t = {'retreat': 1.0, 'watch': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
signal = {'retreat': 'torso matte starts moving right (> 0.8 px/frame)', 'watch': 'head matte rises out of the crouch',
          'refuse': 'head matte drops or swings away from the door', 'watch2': 'head matte swings back toward the door / rises',
          'approach': 'torso matte starts moving left (toward the door)', 'lie_down': 'torso matte centre drops > 4 px (the body goes down)',
          'look_in': 'head matte starts to rise and turn in (> 4 px over 0.5 s); its view becomes the back of the head'}
onsets = [{'choice': k, 'score_t': score_t[k], 'measured_t': None if v is None else round(v / 24, 3),
           'dt': None if v is None else round(v / 24 - score_t[k], 3), 'signal': signal[k]} for k, v in ons.items()]

# approach: head below the line of the back, share of frames
app = [f for f in frames if f['state'] == 'approach']
below = sum(1 for f in app if f['head_above_back_px'] < 0) / max(1, len(app))
ref = [f for f in frames if f['state'] == 'refuse']
away = sum(1 for f in ref if f['facing'] == 'away') / max(1, len(ref))
# end: the dog's matte across the door frame (screen x of the jambs: 196..384)
last = M[-1]['dog']
inside_px = max(0, min(last['x1'], 384) - max(last['x0'], 196)); outside_px = max(0, last['x1'] - 384)
summary = {'cast': cast, 'onsets': onsets,
           'approach_head_below_back_share': round(below, 3), 'refusal_facing_away_share': round(away, 3),
           'end_matte_x_range_px': [last['x0'], last['x1']], 'end_inside_door_frame_px': inside_px, 'end_outside_px': outside_px,
           'x_screen_range_px': [min(tx), max(tx)]}
json.dump({'about': 'Measured from the render of film.mp4 (cast: %s): mattes read from the canvas each frame. state is segmented at '
                    'onsets detected in these measurements, not copied from the score (score_state is kept beside it for comparison).' % cast,
           'summary': summary, 'frames': frames}, open(os.path.join(HERE, 'trace.json'), 'w'), separators=(',', ':'))
print(json.dumps(summary, indent=1))
