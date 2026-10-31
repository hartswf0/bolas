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
on['looks in (head card turned into the doorway)'] = first(lambda i: tr[i]['head_piece'] in ('dog_backhead', 'dog_away', 'dog_backprint'), 26.0)
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
# ---- round 4 (critic round 3 conditions), measured from the placed transforms and the rendered trace
import puppets as PU
from table import PIECES as PC, T as TT, R as RR, FLIP as FF
from world import OPEN_L, OPEN_R, FLOOR
def ex_at(i): return next(e for e in ex if e['f0'] <= i < e['f0'] + e['n'])
def ang(v): return round(math.degrees(math.atan2(-v[1], v[0])), 1)   # screen angle, 0 = right, 90 = up
lbf = [f for f in tr if 7.458 - 1e-6 <= f['t'] < 8.08]
lb_e = ex_at(179)['dog']; G = PU.dog_global(lb_e); A = PU.head_low_aff(G, lb_e, 'dog_lookback')
nz = A.apply(PC['dog_lookback']['pins']['nose']); nk = A.apply(PC['dog_lookback']['pins']['neck'])
lb_card_h = PC['dog_lookback']['size'][1]; torso_h = PC['dog_torso']['size'][1]
look_back4 = {'head_card': 'dog_lookback (eye, nostril, ear retouched)', 'card_height_px': lb_card_h, 'torso_card_height_px': torso_h,
              'ratio': round(lb_card_h / torso_h, 2), 'first_frame_t': lbf[0]['t'], 'share_frames_7.458_8.08_facing_door': round(sum(f['facing'] == 1 for f in lbf) / len(lbf), 3),
              'muzzle_direction_deg_at_7.458': ang((nz[0] - nk[0], nz[1] - nk[1])), 'note': '180 = level toward the door (left)'}
# the watch: every exposure in 8.33-14.71 whose dog card placement changes, and what changed
acts = []
wex = [e for e in ex if 200 <= e['f0'] < 353]
for a_, b_ in zip(wex, wex[1:]):
    ch = sorted(k for k in set(a_['dog']) | set(b_['dog']) if a_['dog'].get(k) != b_['dog'].get(k) and k not in ('tail',))
    if ch: acts.append({'t': b_['t'], 'changed': {k: [a_['dog'].get(k), b_['dog'].get(k)] for k in ch}})
watch4 = {'acting_changes_8.33_14.71': acts, 'n': len(acts)}
# the look-in (round 4 repair): the back-of-head print, where its crown lies and how it moves
from world import OPEN_L as OL, OPEN_R as OR_
def crown(i):
    d = ex_at(i)['dog']; G_ = PU.dog_global(d); nk_ = PC['dog_torso']['pins']['neck']; b_ = PC['dog_backprint']['pins']['nape']
    bx, by = d.get('back_at', PU.BACK_AT)
    A_ = G_ @ TT(nk_[0] + bx, nk_[1] + by + d.get('hdrop', 0)) @ RR(d.get('head', 0)) @ TT(-b_[0], -b_[1])
    return A_.apply(PC['dog_backprint']['pins']['crown']), A_.apply(b_)
bp = [f for f in tr if f['head_piece'] == 'dog_backprint']
hold = [e for e in ex if 634 <= e['f0'] < 674]
c0, n0 = crown(634)
look_in4 = {'card': 'dog_backprint (Amateur Film New Jersey C f001: the dog from behind)', 'frames_with_card': len(bp),
            'first_t': bp[0]['t'], 'last_t': bp[-1]['t'], 'card_angles_during_hold_deg': sorted(set(e['dog'].get('head', 0) for e in hold)),
            'crown_xy_at_26.42': [round(c0[0], 1), round(c0[1], 1)], 'crown_inside_door_opening_x': bool(OL < c0[0] < OR_),
            'crown_above_nape_px': round(n0[1] - c0[1], 1),
            'crown_y_at_t': {str(t_): round(crown(int(t_ * 24))[0][1], 1) for t_ in (26.42, 27.2, 27.6, 28.0, 28.7, 31.9)},
            'note': 'no muzzle on this card; it is never rotated up beyond 5 deg and from 28.08 it slides 12 px down (chin toward the sill)'}
# lying: the paws on the boards (lower-card foot pins vs the floor line the dog stands on)
def paws(i):
    f = next(q for q in tr if q['i'] == i); return {k: round(v[1] - PU.FLOOR_DOG, 1) for k, v in (f['feet'] or {}).items()}
lying4 = {'paw_y_minus_floor_px_at': {str(t_): paws(int(t_ * 24)) for t_ in (6.0, 25.0, 30.0)},
          'leg_card_angles_lying': {k: v for k, v in ex_at(720)['dog'].items() if k.split('_')[0] in ('fore', 'farfore', 'hind', 'farhind')}}
out = {'about': 'measured from trace.json (the rendered dog layer) and xsheet.json', 'onsets': onsets, 'refusal_back': back,
       'approach_head_low': head_low, 'look_back': look_back, 'feet_while_walking': feet, 'end_on_sill': sill, 'camera_interval': interval,
       'round4': {'look_back': look_back4, 'watch': watch4, 'look_in': look_in4, 'lying': lying4}}
os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
json.dump(out, open(os.path.join(FOLDER, 'proof', 'measured.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
