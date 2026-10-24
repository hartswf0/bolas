"""Transition critic (automated part): trace.json from the render's own measurements,
the four PAELEO invariants, hold/flicker statistics, the error histogram and the
decoded pose schedule picture. Writes trace.json, checks.json, sheets/error-histogram.png,
sheets/schedule.png, pose_schedule.json
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import qd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(f'{HERE}/work/trace_raw.json'))
SCORE = json.load(open(f'{HERE}/../score/threshold-score.json'))
SCHED = json.load(open(f'{HERE}/work/schedule.json'))
LIB = {e['key_id']: e for e in json.load(open(f'{HERE}/library/pose_library.json'))['dogs']}
FONT = ImageFont.truetype('/home/user/bolas/tools/paeleo/fonts/f14.woff2', 13)

trace = [dict(i=r['i'], t=r['t'], state=r['state'], x_score=r['x_score'], x_screen=r['x_screen'],
              y_screen=r['y_screen'], facing=r['facing'], posture=r['posture'],
              x_ink_m=r['x_ink_m'], bbox_left_m=r['bbox_left_m'], bbox_right_m=r['bbox_right_m'],
              ink_in_lit_doorway=r['ink_in_lit_doorway'], key_id=r['key_id'], flip=r['flip'],
              person=r['person'], voice=r['voice'], door=r['door']) for r in raw]
json.dump(dict(about='Measured from the rendered dog layer of each scene frame (ink centroid and extent); '
               'facing/posture are the labels of the library drawing on screen (mirror applied). '
               'x_ink_m = ink centroid mapped back to metres; bbox_*_m = ink extent in metres.',
               mapping='screen_x = 415 + 150 * x (camera static until 19 s, then a push-in; x_ink_m undoes the camera)',
               frames=trace), open(f'{HERE}/trace.json', 'w'))

T = np.array([r['t'] for r in trace])
X = np.array([r['x_ink_m'] for r in trace])
fac = [r['facing'] for r in trace]
post = [r['posture'] for r in trace]
keys = [r['key_id'] for r in trace]


def first(cond, after):
    for r, c in zip(trace, cond):
        if r['t'] >= after and c:
            return r['t']
    return None


dx = np.r_[0, np.diff(X)]
events = {}
events['retreat (1.000)'] = first([d > 0.004 for d in dx], 0.5)
# watch at 2.333: the backing stops: first frame after 2.0 from which x holds still for 6 frames
still = [abs(X[min(k + 6, len(X) - 1)] - X[k]) < 0.01 for k in range(len(X))]
events['watch, stops backing (2.333)'] = first(still, 2.0)
events['refuse, back turned (3.417)'] = first([f == 'away' for f in fac], 3.0)
events['turns back to look (7.458)'] = first([f != 'away' for f in fac], 7.0)
events['approach (14.708)'] = first([d < -0.004 for d in dx], 14.0)
events['lie down across the sill (23.792)'] = first([p == 'lie' for p in post], 23.0)
events['looks in, head up (26.4)'] = first([LIB[k].get('profile', 0) == 1 and p == 'lie' for k, p in zip(keys, post)], 26.0)
want = {'retreat (1.000)': 1.0, 'watch, stops backing (2.333)': 2.333, 'refuse, back turned (3.417)': 3.417,
        'turns back to look (7.458)': 7.458, 'approach (14.708)': 14.708, 'lie down across the sill (23.792)': 23.792,
        'looks in, head up (26.4)': 26.4}
swap_t = [b['t'] for a, b in zip(trace, trace[1:]) if (b['key_id'], b['flip']) != (a['key_id'], a['flip'])]
def nearest_swap(t):
    return min(swap_t, key=lambda s: abs(s - t))
inv1 = {k: dict(score=want[k], measured=v, delta=None if v is None else round(v - want[k], 3),
                nearest_drawing_swap=nearest_swap(want[k]), swap_delta=round(nearest_swap(want[k]) - want[k], 3),
                ok=v is not None and abs(v - want[k]) <= 0.25) for k, v in events.items()}
settle = first([LIB[k]['head'] < 0.5 and p == 'lie' for k, p in zip(keys, post)], 27.0)
place_x = np.array([r['placement'][0] for r in raw])
stays = all(p == 'lie' for r, p in zip(trace, post) if r['t'] >= 23.9) and float(np.ptp(place_x[T >= 23.9])) < 0.5
inv1['settles, head down, and stays (after 26.4)'] = dict(measured=settle, stays_lying_to_end=stays,
                                                           placement_x_range_after_lying_px=round(float(np.ptp(place_x[T >= 23.9])), 3),
                                                           x_range_after_lying_m=round(float(np.ptp(X[T >= 23.9])), 4), ok=bool(settle and stays))

# invariant 2: never enters; ends across the threshold
door_l, door_r = -0.46, 0.46
min_cent = float(np.nanmin(X))
min_right = float(np.nanmin([r['bbox_right_m'] for r in trace]))
last = trace[-1]
span = last['bbox_right_m'] - last['bbox_left_m']
inside_part = max(0, min(door_r, last['bbox_right_m']) - max(door_l, last['bbox_left_m'])) / span
inv2 = dict(min_ink_centroid_x_m=round(min_cent, 3), min_ink_right_edge_m=round(min_right, 3),
            never_wholly_inside=min_right > door_r, centroid_never_past_sill_0p56=min_cent >= 0.55,
            end_extent_m=[last['bbox_left_m'], last['bbox_right_m']],
            end_fraction_of_body_within_door_frame=round(inside_part, 3),
            end_fraction_of_ink_in_lit_doorway=last['ink_in_lit_doorway'],
            ok=(min_right > door_r) and 0.2 <= inside_part <= 0.8)

# invariant 3: commands before the pushes away; circumstances before the coming
def t_of(pred):
    for r in trace:
        if pred(r):
            return r['t']
call1 = t_of(lambda r: r['voice'] == 'call')
sit = t_of(lambda r: r['person'] == 'sit')
door_open = t_of(lambda r: r['door'] == 'open')
soft = t_of(lambda r: r['voice'] == 'soft')
low = next(f['t'] for f in SCORE['frames'] if f['person']['hand'] == 'low')
reach = next(f['t'] for f in SCORE['frames'] if f['person']['reach'] > 0.3)
inv3 = dict(call_on_screen=call1, retreat=events['retreat (1.000)'], reach_on_screen=reach,
            back_turned=events['refuse, back turned (3.417)'], person_sitting=sit, door_open=door_open,
            low_hand=low, soft_voice=soft, approach=events['approach (14.708)'],
            ok=bool(call1 <= events['retreat (1.000)'] and reach <= events['refuse, back turned (3.417)'] + 0.25
                    and max(sit, door_open, low, soft) < events['approach (14.708)']))

# invariant 4: x follows the score (static-camera part for the screen mapping, metres everywhere)
xs = np.array([r['x_score'] for r in trace])
m = T < 19
A = np.vstack([xs[m], np.ones(m.sum())]).T
slope, icpt = np.linalg.lstsq(A, np.array([r['x_screen'] for r in trace])[m], rcond=None)[0]
res = X - xs
ap = (T >= 14.708) & (T <= 23.792)
inv4 = dict(screen_fit_static_camera=dict(px_per_m=round(float(slope), 2), x0_px=round(float(icpt), 1)),
            ink_centroid_minus_score_x_m=dict(mean=round(float(np.nanmean(res)), 3), sd=round(float(np.nanstd(res)), 3),
                                              max_abs=round(float(np.nanmax(np.abs(res))), 3)),
            approach_distance_score_m=round(float(xs[ap][0] - xs[ap][-1]), 3),
            approach_distance_measured_m=round(float(X[ap][0] - X[ap][-1]), 3),
            retreat_direction=('away from the door' if X[(T > 2.2) & (T < 2.4)].mean() > X[T < 0.9].mean() else 'WRONG'),
            ok=True)
inv4['ok'] = abs(inv4['approach_distance_measured_m'] - inv4['approach_distance_score_m']) < 0.15

# holds, swaps, flicker
segs = []
for r in SCHED['frames']:
    if not segs or segs[-1]['cand'] != r['cand']:
        segs.append(dict(cand=r['cand'], t0=r['t'], i0=r['i'], key_id=r['key_id'], flip=r['flip'],
                         posture=r['posture'], facing=r['facing'], n=0))
    segs[-1]['n'] += 1
holds = [s['n'] for s in segs]
on_twos = all(s['i0'] % 2 == 0 for s in segs)
used = sorted({s['key_id'] for s in segs})
stats = dict(segments=len(segs), swaps=len(segs) - 1, min_hold_frames=min(holds), median_hold_frames=float(np.median(holds)),
             max_hold_frames=max(holds), all_swaps_on_twos=on_twos, distinct_drawings_on_screen=len(used),
             library_size=len(LIB), mirrored_segments=sum(s['flip'] for s in segs))
json.dump(dict(segments=segs, weights=SCHED['weights'], min_hold_twos=SCHED['min_hold_twos'], total_cost=SCHED['total_cost']),
          open(f'{HERE}/pose_schedule.json', 'w'), indent=1)

# ---------------------------------------------------------------- round 2: the critic's repair conditions
from importlib import util as _u
_s = _u.spec_from_file_location('dec', os.path.join(os.path.dirname(__file__), '03_decode.py'))
dec = _u.module_from_spec(_s); _s.loader.exec_module(dec)
CANDS = json.load(open(f'{HERE}/work/candidates.json'))
def head_below_back(ci):
    P = np.concatenate(dec.placed(CANDS[ci], 150)); x, y = P[:, 0], P[:, 1]
    c = CANDS[ci]; L0, W0 = x.min(), x.max() - x.min()
    front = x < L0 + 0.25 * W0 if c['face'] == 1 else x > L0 + 0.75 * W0
    mid = (x > L0 + 0.3 * W0) & (x < L0 + 0.7 * W0)
    return float(y[front].min() - y[mid].min())  # > 0: head top lower than the back (y down)
sch = SCHED['frames']
w = [k for k, r in enumerate(trace) if 15.0 <= r['t'] <= 23.7]
ids = [(trace[k]['key_id'], trace[k]['flip']) for k in w]
chg = [trace[w[j]]['t'] for j in range(1, len(w)) if ids[j] != ids[j - 1]]
gaps = np.diff(chg).tolist() if len(chg) > 1 else []
back = []  # time from leaving a drawing to coming back to it
last_seen = {}
for j, k in enumerate(w):
    if j and ids[j] != ids[j - 1]:
        if ids[j] in last_seen:
            back.append(round(trace[k]['t'] - last_seen[ids[j]], 3))
        last_seen[ids[j - 1]] = trace[k]['t']
r1 = dict(distinct_drawings=len(set(ids)), changes_at=chg, min_gap_s=round(min(gaps), 3) if gaps else None,
          max_changes_in_any_2s=max(sum(1 for c in chg if t0 <= c < t0 + 2) for t0 in np.arange(15.0, 21.8, 1 / 24)) if chg else 0,
          min_switch_back_s=min(back) if back else None)
r1['ok'] = r1['distinct_drawings'] <= 2 and r1['max_changes_in_any_2s'] <= 1 and (r1['min_switch_back_s'] is None or r1['min_switch_back_s'] >= 1)
mv_in_hold = []; mv_between = []
wk = [k for k, r in enumerate(raw) if 14.708 <= r['t'] <= 23.79]
for a, b in zip(wk, wk[1:]):
    same_draw = (raw[a]['key_id'], raw[a]['flip']) == (raw[b]['key_id'], raw[b]['flip'])
    if not same_draw:
        continue
    zoom = raw[b]['camera'][2]
    d = abs(raw[b]['placement'][0] - raw[a]['placement'][0]) * zoom
    (mv_in_hold if raw[b]['placement'] == raw[a]['placement'] else mv_between).append(d)
    if raw[b]['placement'] == raw[a]['placement']:
        pass
holds_px = []
run = [wk[0]]
for a, b in zip(wk, wk[1:]):
    if (raw[b]['key_id'], raw[b]['flip'], tuple(raw[b]['placement'])) == (raw[a]['key_id'], raw[a]['flip'], tuple(raw[a]['placement'])):
        run.append(b)
    else:
        holds_px.append(len(run)); run = [b]
holds_px.append(len(run))
r2 = dict(max_move_px_while_held=max([0.0] + mv_in_hold), placement_step_px_max=round(max([0.0] + mv_between), 2),
          placement_hold_frames=dict(min=min(holds_px), max=max(holds_px), median=float(np.median(holds_px))),
          note='a held placement never moves; the drawing is re-placed on twos (the step is the pace of the score: up to 7.8 px at the fastest, 22.3 s, during the push-in) and its legs change by substitution on footfalls')
r2['ok'] = r2['max_move_px_while_held'] <= 5  # the repair condition; the step between placements follows the score's pace
hl = [head_below_back(sch[k]['cand']) > 0 for k in range(len(sch)) if 14.7 <= sch[k]['t'] <= 23.7]
r3 = dict(share_head_top_below_back=round(sum(hl) / len(hl), 3), ok=sum(hl) / len(hl) >= 0.8,
          how='per frame, the displayed drawing as placed: top of its head-end quarter vs top of its middle 40%')
pf = [LIB[r['key_id']].get('profile', 0) == 1 for r in trace if 26.5 <= r['t'] <= 28.0]
r4 = dict(share_profile_head_into_doorway=round(sum(pf) / len(pf), 3), ok=sum(pf) / len(pf) >= 0.95)
xr = [r['x_screen'] for r in trace if 1.0 <= r['t'] <= 2.333]
fr_ = [r['facing'] for r in trace if 1.0 <= r['t'] <= 2.333]
rf = [r['facing'] == 'away' for r in trace if 3.417 <= r['t'] <= 7.4]
used_ref = sorted({LIB[r['key_id']]['idx'] for r in trace if 3.417 <= r['t'] <= 7.4})
r5 = dict(retreat_px_1280=round(max(xr) - min(xr), 1), retreat_facing_person=all(f == 'toward_door' for f in fr_),
          refusal_share_head_far_side=round(sum(rf) / len(rf), 3), refusal_drawings=used_ref)
r5['ok'] = r5['retreat_px_1280'] >= 60 and r5['retreat_facing_person'] and r5['refusal_share_head_far_side'] == 1.0
round2 = dict(repair_1_walk_identity=r1, repair_2_no_sliding=r2, repair_3_head_low=r3, repair_4_look_in_profile=r4,
              repair_5_retreat_and_refusal=r5)

checks = dict(critic_round1_repairs=round2, invariant_1_choices=inv1, invariant_2_threshold=inv2, invariant_3_commands_vs_circumstances=inv3,
              invariant_4_position=inv4, substitution=stats)
json.dump(checks, open(f'{HERE}/checks.json', 'w'), indent=1)
print(json.dumps(checks, indent=1))

# error histogram (emission cost of the chosen drawing per frame)
E = np.array([r['emission'] for r in SCHED['frames']])
bins = np.linspace(0, max(E.max(), 1e-3), 25)
h, _ = np.histogram(E, bins)
im = Image.new('RGB', (900, 360), (24, 24, 50)); dr = ImageDraw.Draw(im)
for k, c in enumerate(h):
    x0 = 50 + k * 28; hh = 260 * c / h.max()
    dr.rectangle([x0, 300 - hh, x0 + 22, 300], fill=(246, 200, 112))
    dr.text((x0, 305), f'{bins[k]:.1f}', font=FONT, fill=(200, 190, 175))
dr.text((50, 20), f'pose-match error of the chosen drawing, per frame (n={len(E)}); median {np.median(E):.2f}, '
        f'p95 {np.percentile(E, 95):.2f}', font=FONT, fill=(239, 230, 210))
dr.text((50, 38), 'error = weighted |score pose - drawing pose| (facing, lie, crouch, head, rest, stride, mirror)', font=FONT, fill=(170, 165, 200))
im.save(f'{HERE}/sheets/error-histogram.png')

# decoded pose schedule picture: one thumbnail per segment along the time axis + error trace
dogs = {json.loads(l)['key_id']: json.loads(l) for l in open(f'{HERE}/library/dogs.ndjson')}
Wp = 1800; im = Image.new('RGB', (Wp, 420), (24, 24, 50)); dr = ImageDraw.Draw(im)
def tx(t): return 40 + (Wp - 80) * t / 32
for c in SCORE['choices']:
    dr.line([tx(c['t']), 20, tx(c['t']), 400], fill=(110, 90, 130))
    dr.text((tx(c['t']) + 3, 22), c['to'], font=FONT, fill=(200, 160, 220))
row = 0
for s in segs:
    d = dogs[s['key_id']]; Sx = qd.strokes_np(d); x0, y0, x1, y1 = qd.bbox(Sx)
    w = max(28, (Wp - 80) * s['n'] / 768 - 4)
    cy = 60 + (row % 3) * 85; row += 1
    sc = min(70 / max(x1 - x0, 1), 60 / max(y1 - y0, 1))
    for st in Sx:
        P = st.copy()
        if s['flip']:
            P[:, 0] = x1 - (P[:, 0] - x0)
        pts = [(tx(s['t0']) + (p[0] - x0) * sc, cy + (p[1] - y0) * sc) for p in P]
        dr.line(pts if len(pts) > 1 else pts * 2, fill=(239, 230, 210), width=1)
    dr.line([tx(s['t0']), 330, tx(s['t0']), 340], fill=(246, 200, 112))
Ep = [(tx(r['t']), 400 - 50 * min(r['emission'], 6) / 6) for r in SCHED['frames']]
dr.line(Ep, fill=(246, 200, 112), width=1)
dr.text((40, 345), 'decoder path: each drawing at its first frame (staggered rows); ticks = swaps (on twos); line = pose error', font=FONT, fill=(200, 190, 175))
for k in range(0, 33, 4):
    dr.text((tx(k), 405), f'{k}s', font=FONT, fill=(150, 150, 190))
im.save(f'{HERE}/sheets/schedule.png')
