"""SCION 53 · invariant checks, measured from ../trace.json (written by the render from the composited dog alpha)
and ../build/edl.json (the transform ledger). Writes ../build/check.json. Prints PASS/FAIL per invariant.
Numbers here are measurements of the render; whether a choice *reads* on screen is judged by looking, not here."""
import json, os
import numpy as np
from lib import load_json, ROOT, HERE, SRC

tr = load_json(ROOT, 'trace.json')['frames']
edl = load_json(HERE, 'edl.json')
score = load_json(SRC, 'threshold-score.json')
T = np.array([f['t'] for f in tr]); XM = np.array([f['x_measured_m'] for f in tr]); XS = np.array([f['x_score'] for f in tr])
HP = np.array([f['height_px'] for f in tr]); HH = np.array([f['head_height_px'] for f in tr]); FAC = [f['facing'] for f in tr]; OP = [f['op'] for f in tr]
res = {}

def first(cond, after):
    for i, t in enumerate(T):
        if t >= after and cond(i):
            return float(t)
    return None

def op_change(after):
    for i in range(1, len(T)):
        if T[i] >= after and OP[i].split(' ·')[0] != OP[i - 1].split(' ·')[0]:
            return float(T[i])
    return None

stand_h = float(np.median(HP[(T > 16) & (T < 23)]))
refuse_lie_h = float(np.median(HP[(T > 5.5) & (T < 7.3)]))
ch = {}
ch['watch>retreat (1.00)'] = {'op_change': op_change(0.9), 'motion_onset': first(lambda i: XM[i] - XM[0] > 0.03, 0.5)}
ch['retreat>watch (2.33)'] = {'op_change': op_change(2.2)}
ch['watch>refuse (3.42)'] = {'op_change': op_change(3.3), 'first_frame_not_facing_door': first(lambda i: FAC[i] != 'door', 3.0),
                            'first_frame_back_turned': first(lambda i: FAC[i] == 'away', 3.0)}
ch['refuse>watch (7.46)'] = {'head_lift_onset (head end +4px over 5.5-7.3 s)': first(lambda i: HH[i] > np.median(HH[(T > 5.5) & (T < 7.3)]) + 4, 7.3),
                            'first_frame_facing_door_again': first(lambda i: FAC[i] == 'door', 7.3)}
ch['watch>approach (14.71)'] = {'op_change': op_change(14.5), 'motion_onset': first(lambda i: XM[i] < 3.97, 14.0)}
ch['approach>lie_down (23.79)'] = {'op_change': op_change(23.5), 'height_drop_below_80pct': first(lambda i: HP[i] < 0.8 * stand_h, 23.0)}
ch['hears come in (26.4): looks in'] = {'head_lift_onset (head end +4px over 25.0-26.3 s)': first(lambda i: HH[i] > np.median(HH[(T > 25.0) & (T < 26.3)]) + 4, 26.3)}
targets = [1.0, 2.333, 3.417, 7.458, 14.708, 23.792, 26.4]
inv1 = []
for (k, v), tt in zip(ch.items(), targets):
    best = [x for x in v.values() if x is not None]
    near = min(best, key=lambda x: abs(x - tt)) if best else None
    ok = near is not None and abs(near - tt) <= 0.25
    inv1.append(ok)
    v['target'] = tt; v['nearest'] = near; v['within_0.25s'] = ok
res['invariant_1_choice_times'] = {'pass': all(inv1), 'choices': ch,
    'note': 'op_change = the frame where the archive operation switches (structural); motion/height/facing are measured from the render.'}

end = [f for f in tr if f['t'] >= 26]
sill_px = 372 + 185 * 0.46
inner_px = 372 - 185 * 0.46
inv2 = {'min_x_measured_m': float(XM.min()), 'x_measured_end_m': float(XM[-1]),
        'min_nose_left_px': int(min(f['nose_left_px'] for f in tr)), 'door_inner_edge_px (x=-0.46)': inner_px,
        'frac_inside_door_frame_end (mean t>=26)': float(np.mean([f['frac_inside_door_frame'] for f in end])),
        'posture_end': tr[-1]['posture']}
inv2['pass'] = bool(XM.min() >= 0.56 - 0.03 and inv2['min_nose_left_px'] > inner_px and 0.2 <= inv2['frac_inside_door_frame_end (mean t>=26)'] <= 0.8 and tr[-1]['posture'] == 'lying')
res['invariant_2_never_enters'] = inv2

# 3: commands push away; circumstances visible before the approach
d_after_call = float(XM[(T > 2.3) & (T < 2.4)].mean() - XM[(T > 0.9) & (T < 1.0)].mean())
turned_after_reach = first(lambda i: FAC[i] == 'away', 3.4)
door_open = next((e['t'] for e in edl if 'open' in e['door']['op'] or 'opens' in e['door']['op']), None)
seated = next((e['t'] for e in edl if e['person']['src'] == 'seated'), None)
low_hand = next((e['t'] for e in edl if 'low hand' in e.get('hand', {}).get('op', '')), None)
approach = ch['watch>approach (14.71)']['motion_onset']
inv3 = {'retreat_after_call_m': d_after_call, 'back_turned_after_reach_at': turned_after_reach,
        'seated_on_screen_from': seated, 'door_opening_on_screen_from': door_open, 'low_hand_on_screen_from': low_hand,
        'soft_voice_from (score timeline)': 7.4, 'approach_motion_onset': approach}
inv3['pass'] = bool(d_after_call > 0.5 and turned_after_reach and turned_after_reach < 4.6 and all(v is not None and v < (approach or 99) for v in (seated, door_open, low_hand)))
res['invariant_3_commands_vs_circumstances'] = inv3

err = np.abs(XM - XS)
appr = (T >= 14.708) & (T < 23.792)
ret = (T >= 1.0) & (T < 2.6)
inv4 = {'max_abs_error_m': float(err.max()), 'mean_abs_error_m': float(err.mean()),
        'approach_distance_score_m': float(XS[appr][0] - XS[appr][-1]), 'approach_distance_measured_m': float(XM[appr][0] - XM[appr][-1]),
        'approach_mean_speed_score_mps': float((XS[appr][0] - XS[appr][-1]) / (T[appr][-1] - T[appr][0])),
        'approach_mean_speed_measured_mps': float((XM[appr][0] - XM[appr][-1]) / (T[appr][-1] - T[appr][0])),
        'retreat_direction_measured': 'away from door (+x)' if XM[ret][-1] > XM[ret][0] else 'toward door',
        'mapping': 'x_screen = 372 + 185 * x (px); dog centroid placed on that line each frame'}
inv4['pass'] = bool(err.max() < 0.05 and XM[ret][-1] > XM[ret][0])
res['invariant_4_position_follows_x'] = inv4

with open(os.path.join(HERE, 'check.json'), 'w') as fh:
    json.dump(res, fh, indent=1)
for k, v in res.items():
    print(('PASS ' if v['pass'] else 'FAIL ') + k)
for k, v in ch.items():
    print('   ', k, '->', v['nearest'], 'ok' if v['within_0.25s'] else 'MISS', {a: b for a, b in v.items() if a not in ('target', 'nearest', 'within_0.25s')})
print('    inv2', {k: v for k, v in inv2.items()})
print('    inv3', inv3)
print('    inv4', inv4)
