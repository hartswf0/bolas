"""Measures the choices from the render (trace.json), not from the score labels. Writes ../proof/measured.json."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xsheet import gait, LEGN, STANCE, K
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
tr = json.load(open(os.path.join(FOLDER, 'trace.json')))['frames']
xs = json.load(open(os.path.join(FOLDER, 'xsheet.json')))
X = np.array([f['x_screen'] for f in tr]); t = np.array([f['t'] for f in tr])
top = np.array([f['bbox'][1] for f in tr]); hy = np.array([f['head_xy'][1] for f in tr])
asp = np.array([f['aspect_h_w'] for f in tr]); fac = np.array([f['facing'] for f in tr])
def first(cond, after):
    idx = [i for i in range(len(tr)) if t[i] >= after and cond(i)]
    return float(t[idx[0]]) if idx else None
on = {}
hxs = np.array([f['head_xy'][0] for f in tr])
on['retreat (backs away)'] = first(lambda i: abs(X[i] - X[0]) > 1.5 or math.hypot(hxs[i] - hxs[0], hy[i] - hy[0]) > 2.5, .5)
r0 = on['retreat (backs away)']
on['watch (stops backing, head comes up)'] = first(lambda i: hy[i] < hy[i - 1] - 3.0, r0 + .5)
on['refuse (back turned)'] = first(lambda i: fac[i] == -1, 3.0)
on['watch (turns back to look)'] = first(lambda i: fac[i] == 1, 7.0)
i14 = int(14 * 24)
on['approach (comes, head low)'] = first(lambda i: X[i] < X[i14] - 1.5 or abs(hy[i] - hy[i14]) > 3, 14.0)
i23 = int(23.5 * 24)
on['lie_down (lies across the sill)'] = first(lambda i: top[i] > top[i23] + 6 or asp[i] < asp[i23] - .05, 23.5)
on['looks in (head card turned into the doorway)'] = first(lambda i: tr[i]['head_piece'] == 'dog_backhead', 26.0)
score = {'retreat (backs away)': 1.0, 'watch (stops backing, head comes up)': 2.333, 'refuse (back turned)': 3.417,
         'watch (turns back to look)': 7.458, 'approach (comes, head low)': 14.708, 'lie_down (lies across the sill)': 23.792,
         'looks in (head card turned into the doorway)': 26.4}
onsets = {k: {'score_t': score[k], 'measured_t': v, 'dt': None if v is None else round(v - score[k], 3)} for k, v in on.items()}
# the back shown during the refusal
ref = [f for f in tr if f['state'] == 'refuse']
back = {'first_back_turned_t': next(f['t'] for f in ref if f['facing'] == -1), 'share_refuse_frames_back_turned': round(sum(f['facing'] == -1 for f in ref) / len(ref), 3)}
# head below the line of the back during the approach
ap = [f for f in tr if f['state'] == 'approach' and f['back_line_y'] is not None]
below = [f['head_xy'][1] - f['back_line_y'] for f in ap]
head_low = {'frames': len(ap), 'share_head_centroid_below_back_line': round(sum(b > 0 for b in below) / len(below), 3),
            'min_px_below': round(min(below), 1), 'median_px_below': round(float(np.median(below)), 1)}
# repair 1: the topmost pixel of the head card (ears included) below the withers, muzzle clearly below, whole approach
apf = [f for f in tr if 14.708 <= f['t'] < 23.792]
tops = [f['head_top_y'] - f['withers_y'] for f in apf]
muz = [f['muzzle_y'] - f['withers_y'] for f in apf]
head_low['head_card_top_below_withers'] = {'frames': len(apf), 'share_all_below': round(sum(v > 0 for v in tops) / len(tops), 3),
                                           'min_px': min(tops), 'median_px': float(np.median(tops))}
head_low['muzzle_below_withers'] = {'min_px': round(min(muz), 1), 'median_px': round(float(np.median(muz)), 1)}
# repair 2: one head card, the face, pointing at the door from the look-back
lb = [f for f in tr if 7.458 <= f['t'] < 8.1]
look_back = {'frames_7.458_to_8.1': len(lb), 'head_pieces': sorted(set(f['head_piece'] for f in lb)),
             'share_facing_door': round(sum(f['facing'] == 1 for f in lb) / len(lb), 3)}
# feet: slip of planted feet between consecutive exposures while walking (structural: from the placed transforms)
slips = []
ex = xs['exposures']
for a, b in zip(ex, ex[1:]):
    if a['dog_label'] != b['dog_label'] or not a['dog_label'].startswith(('approach', 'retreat')): continue
    fa = next(f for f in tr if f['i'] == a['f0'])['feet']; fb = next(f for f in tr if f['i'] == b['f0'])['feet']
    xa = next(f for f in tr if f['i'] == a['f0'])['x_score']; xb = next(f for f in tr if f['i'] == b['f0'])['x_score']
    sa = (4.0 - xa) * K if a['dog_label'].startswith('approach') else -(xa - 3.0) * K
    sb = (4.0 - xb) * K if b['dog_label'].startswith('approach') else -(xb - 3.0) * K
    _, pa = gait(sa); _, pb = gait(sb)
    for k, piece in LEGN.items():
        if pa[k][0] in ('stance', 'planted') and pa[k] == pb[k] and piece in fa:   # same foot-fall held on the boards
            slips.append(abs(fb[piece][0] - fa[piece][0]))
feet = {'stance_pairs': len(slips), 'max_slip_px': round(max(slips), 3) if slips else None, 'mean_slip_px': round(float(np.mean(slips)), 3) if slips else None}
end = tr[-1]
sill = {'end_bbox': end['bbox'], 'door_frame_px': [193, 387], 'part_inside_frame': end['bbox'][0] < 387,
        'part_outside_frame': end['bbox'][2] > 387, 'share_of_dog_pixels_inside_frame': end['share_inside_door_frame_px'],
        'end_posture': end['posture'], 'end_facing': end['facing']}
holds = [e['n'] for e in ex]
interval = {'exposures': len(ex), 'frames': sum(holds), 'min_frames_per_exposure': min(holds),
            'share_on_twos_or_longer': round(sum(h >= 2 for h in holds) / len(holds), 3), 'longest_hold_frames': max(holds)}
out = {'about': 'measured from trace.json (the rendered dog layer) and xsheet.json', 'onsets': onsets, 'refusal_back': back,
       'approach_head_low': head_low, 'look_back': look_back, 'feet_while_walking': feet, 'end_on_sill': sill, 'camera_interval': interval}
os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
json.dump(out, open(os.path.join(FOLDER, 'proof', 'measured.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
