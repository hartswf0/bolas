"""Independent-ish assertions: read what the render measured about its own dog layer (raw_trace.json), write
../trace.json and ../build/checks.json, and test the PAELEO invariants numerically. Perceptual judgement is not here."""
import json
import numpy as np
from common import *

raw = json.load(open(os.path.join(CACHE, 'raw_trace.json')))
R = raw['raw']; EV = raw['events']
score = load_score(); SF = score['frames']
FPS_ = 24
n = len(R)
xs_score = np.array([r['x_score'] for r in R])
xst = np.array([r['x_stage'] for r in R])
white = np.array([r['white_frac'] for r in R])
fl = np.array([r['front_light'] for r in R])
by = np.array([r['body_y_stage'] for r in R])
bbox = np.array([r['bbox_stage'] for r in R])
mlum = np.array([r['mean_lum'] for r in R])
fw = np.array([r['front_warm'] for r in R])
facing = np.where(mlum > 0.55, -1, 1)

# calibrate the constant offset between the body card's alpha centroid and its pivot, per side of the card
front = (facing == 1) & (np.arange(n) < 20)
back = (facing == -1) & (np.arange(n) > 95) & (np.arange(n) < 170)
off_f = float(np.median(xst[front] - sx(xs_score[front])))
off_b = float(np.median(xst[back] - sx(xs_score[back])))
x_est = (xst - np.where(facing == 1, off_f, off_b) - X0) / K

h0 = float(np.median(by[:20]))
drop = by - h0
posture = np.where(drop > 30, 'lying', np.where(drop > 6, 'crouched', 'standing'))

trace = []
for k, r in enumerate(R):
    trace.append({'i': r['i'], 't': r['t'], 'state': r['state'], 'x_score': r['x_score'],
                  'x_screen': r['x_screen'], 'y_screen': r['y_screen'], 'facing': int(facing[k]), 'posture': str(posture[k]),
                  'x_stage': r['x_stage'], 'x_measured_m': round(float(x_est[k]), 3), 'camera': r['camera'],
                  'body_drop_px': round(float(drop[k]), 1), 'mean_lum': r['mean_lum'], 'front_warm': r['front_warm'],
                  'bbox_stage': r['bbox_stage']})
json.dump({'about': 'Measured per scene frame from the rendered dog layer (alpha centroid of the body card, bbox, '
                    'luminance of the card: white = its blank back). x_screen/y_screen are in final film pixels (after the '
                    'rostrum cut-in at frame 610); x_stage is before the camera. x_measured_m inverts x_stage = 300 + 185 x '
                    'with a calibrated card-centroid offset (front %.1f px, back %.1f px).' % (off_f, off_b),
           'mapping': {'X0_px': X0, 'K_px_per_m': K, 'door_opening_px': [sx(-0.46), sx(0.46)], 'sill_m': 0.56},
           'frames': trace}, open(os.path.join(ROOT, 'trace.json'), 'w'))


def first(cond, start=0, end=None):
    for k in range(start, end or n):
        if cond(k):
            return k
    return None


det = {}
# 1 retreat at 1.00: crouch snaps (body drops), the head is a door (pale front), the dog starts moving away
det['retreat'] = {'crouch': first(lambda k: drop[k] > 6, 12), 'door_head': first(lambda k: fw[k] < fw[:20].mean() - 0.06, 12),
                  'moves_away': first(lambda k: x_est[k] > x_est[20] + 0.03, 12)}
# 2 retreat -> watch at 2.333: the door head is gone (dog head back)
det['watch1'] = {'head_back': first(lambda k: fw[k] > fw[:20].mean() - 0.03, (det['retreat']['door_head'] or 24) + 1),
                  'crouch_released': first(lambda k: drop[k] < 6.5, (det['retreat']['crouch'] or 24) + 1)}
# 3 refuse at 3.417: the card starts to turn (width shrinks) and shows its blank back
wid = bbox[:, 2] - bbox[:, 0]
det['refuse'] = {'turn_starts': first(lambda k: wid[k] < 0.95 * wid[k - 1], 70), 'back_shown': first(lambda k: facing[k] == -1, 70)}
# 4 refuse -> watch at 7.458: front shown again
det['watch2'] = {'front_shown': first(lambda k: facing[k] == 1, (det['refuse']['back_shown'] or 90) + 1),
                 'turn_starts': first(lambda k: wid[k] < 0.95 * wid[k - 1], 170)}
# 5 approach at 14.708: moves toward the door
det['approach'] = {'moves_in': first(lambda k: x_est[k] < x_est[300] - 0.03, 300)}
# 6 lie down at 23.792: body drops to the boards
det['lie'] = {'body_down': first(lambda k: drop[k] > 6, 540), 'lying': first(lambda k: drop[k] > 30, 540)}
# 7 come in at 26.4: looks in (the head goes further into the door frame), then settles
hx = np.array([b[0] for b in bbox])
det['look_in'] = {'head_moves_in': first(lambda k: hx[k] < hx[615] - 8, 615),
                  'settled': first(lambda k: hx[k] >= hx[615] - 3, (first(lambda k: hx[k] < hx[615] - 8, 615) or 615) + 1)}

expected = {'retreat': 1.0, 'watch1': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie': 23.792, 'look_in': 26.4}
checks = {'choices': {}}
for k, v in det.items():
    onset = min([f for f in v.values() if f is not None and not (k == 'look_in' and f == v.get('settled'))] or [None])
    t = onset / FPS_ if onset is not None else None
    checks['choices'][k] = {'expected_t': expected[k], 'measured_onset_t': t, 'signals_frames': v,
                            'signals_t': {s: (f / FPS_ if f is not None else None) for s, f in v.items()},
                            'pass_0.25s': (t is not None and abs(t - expected[k]) <= 0.25)}
# invariant 2: never enters; ends across the threshold
min_x = float(x_est.min())
last = bbox[-1]
open_l, open_r = sx(-0.46), sx(0.46)
checks['never_enters'] = {'min_x_measured_m': round(min_x, 3), 'min_x_score_m': float(xs_score.min()),
                          'pass': bool(min_x >= 0.56 - 0.06)}
checks['ends_across_threshold'] = {'final_bbox_stage': last.tolist(), 'door_opening_px': [open_l, open_r],
                                   'px_inside_frame': float(max(0, open_r - last[0])), 'px_outside': float(max(0, last[2] - open_r)),
                                   'final_posture': str(posture[-1]),
                                   'pass': bool(last[0] < open_r < last[2] and posture[-1] == 'lying')}
# invariant 4: x follows the score
err = np.abs(x_est - xs_score)
a0, a1 = EV['approach'], EV['lie']
checks['x_follows_score'] = {'max_abs_err_m': round(float(err.max()), 3), 'mean_abs_err_m': round(float(err.mean()), 3),
                             'retreat_measured_m': round(float(x_est[EV['refuse']] - x_est[EV['retreat']]), 3),
                             'retreat_score_m': round(float(xs_score[EV['refuse']] - xs_score[EV['retreat']]), 3),
                             'approach_measured_m': round(float(x_est[a0] - x_est[a1]), 3),
                             'approach_score_m': round(float(xs_score[a0] - xs_score[a1]), 3),
                             'approach_seconds': round((a1 - a0) / FPS_, 3),
                             'pass': bool(err.max() < 0.15)}
# invariant 3 (structural, from the score and the render's events): commands push away; circumstances change before it comes
checks['commands_push_away'] = {'x_at_first_call': round(float(x_est[24]), 3), 'x_after_calls': round(float(x_est[EV['watch2']]), 3),
                                'pass': bool(x_est[EV['watch2']] > x_est[24] + 0.5)}
ci = {'sits_t': EV['sit'] / FPS_, 'door_open_t': EV['door_open'] / FPS_, 'hand_low_t': EV['hand_low'] / FPS_,
      'soft_voice_t': 7.4, 'approach_t': EV['approach'] / FPS_}
ci['pass'] = all(v < ci['approach_t'] for k, v in ci.items() if k != 'approach_t')
checks['circumstances_before_approach'] = ci
json.dump(checks, open(os.path.join(HERE, 'checks.json'), 'w'), indent=1)
for k, v in checks['choices'].items():
    print('%-9s expected %6.3f  measured %s  %s  %s' % (k, v['expected_t'], v['measured_onset_t'], 'PASS' if v['pass_0.25s'] else 'FAIL', v['signals_t']))
for k in ['never_enters', 'ends_across_threshold', 'x_follows_score', 'commands_push_away', 'circumstances_before_approach']:
    print(k, json.dumps(checks[k]))
