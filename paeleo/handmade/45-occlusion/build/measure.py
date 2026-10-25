"""SCION 45 · Render verifier. From the per-frame render records (what was actually composited and measured on pixels)
write trace.json, the measured choice onsets, the occlusion assertions and the overlap-event intervals.

Measured on the render (screen px of the dog's own alpha pass, before holdouts): centroid, bbox, top of the dog above its
base, the head side (centroid of the top 35% of its alpha vs the whole), the dark-head pixels of the look-in, the visible
share after holdouts and the share behind the frame plane. State labels in trace.json come from those measurements
(segmenting at the measured onsets), not from the score's labels; the score's label is kept alongside as state_score.
"""
import json, os, sys, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
SCORE = json.load(open(os.path.join(HERE, '../../../../paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
import dog as DOG


def main():
    recs = {}
    for p in sorted(glob.glob(os.path.join(HERE, 'cache/records/r*.json'))):
        r = json.load(open(p)); recs[r['i']] = r
    idx = sorted(recs)
    if os.environ.get('PARTIAL') != '1':
        assert len(idx) == 768, 'need all 768 scene frames, have %d' % len(idx)
    rows = []
    for i in idx:
        r = recs[i]; d = r['dog']; c = r['cam']
        s, fx = c['s'], c['fx']
        xw = fx + (d['cx'] - 640) / s                       # measured body centroid, world metres
        h_top = (d['bot'] - d['top']) / s                   # measured height of the dog above its lowest pixel
        rows.append(dict(i=i, t=r['t'], xw=xw, h_top=h_top, width=(d['right'] - d['left']) / s, head_side=d.get('head_side'),
                         dark_head=d.get('dark_head', 0), head_dx=(d['cx'] - d['head_screen'][0]) / s if d['cx'] is not None else 0, cx=d['cx'], cy=d['cy'], vis=d['visible'] / max(1, d['area']),
                         in_frac=d['in_frac'], hiders=d['hiders'], facing_annot=d['facing'], posture_annot=d['posture'],
                         shadow_dx=(None if d['shadow_cx'] is None or d['base_cx'] is None else (d['shadow_cx'] - d['base_cx']) / s)))
    t = np.array([q['t'] for q in rows]); xw = np.array([q['xw'] for q in rows]); ht = np.array([q['h_top'] for q in rows])
    hs = np.array([q['head_side'] if q['head_side'] is not None else 0 for q in rows]); wd = np.array([q['width'] for q in rows])
    dk = np.array([q['dark_head'] for q in rows])

    def first(cond, after):
        k = np.nonzero((t >= after) & cond)[0]
        return int(k[0]) if len(k) else None
    ref_h = np.median(ht[(t > 0.2) & (t < 0.9)]); ref_x = np.median(xw[(t > 0.2) & (t < 0.9)])
    on = {}
    # 1.00 retreat: the head drops or it moves back (away from the door)
    on['retreat'] = first((ht < ref_h - 0.08) | (xw > ref_x + 0.02), 0.6)
    # 2.33 watch: the head is up again
    on['watch_1'] = first(ht > ref_h - 0.06, t[on['retreat']] + 0.4)
    # 3.42 refuse: the silhouette starts to turn (width departs from the watch hold) or the head side flips
    ref_w = np.median(wd[(t > 2.7) & (t < 3.3)])
    on['refuse'] = first((np.abs(wd - ref_w) > 0.12 * ref_w) | (hs < -0.02), 3.0)
    # 7.46 watch: the head lifts off the paws and comes round (top of the lying dog's alpha rises)
    ref_h1 = np.median(ht[(t > 6.4) & (t < 7.3)])
    on['watch_2'] = first(ht > ref_h1 + 0.05, 7.0)
    # 14.71 approach: the head drops below the line of the back, or it moves toward the door
    ref_h2 = np.median(ht[(t > 12) & (t < 14.5)]); ref_x2 = np.median(xw[(t > 12) & (t < 14.5)])
    on['approach'] = first((ht < ref_h2 - 0.08) | (xw < ref_x2 - 0.02), 14.0)
    # 23.79 lie down: the body goes down from its walking height
    ref_h3 = np.median(ht[(t > 22.6) & (t < 23.5)])
    on['lie_down'] = first(ht < ref_h3 - 0.05, 23.5)
    # 26.4 hears 'come in': the head turns into the lit doorway (the back of the head, dark against the room)
    on['look_in'] = first(dk > 40, 26.0)
    on['settle'] = first(dk < 10, (t[on['look_in']] + 0.3) if on['look_in'] is not None else 27)
    names = [('retreat', 'retreat'), ('watch_1', 'watch'), ('refuse', 'refuse'), ('watch_2', 'watch'), ('approach', 'approach'), ('lie_down', 'lie_down')]
    bounds = [(on[k], st) for k, st in names]
    state = ['watch'] * len(rows)
    for (k0, st) in bounds:
        if k0 is None:
            continue
        for j in range(k0, len(rows)):
            state[j] = st
    # facing measured: head side, with ties (end-on frames) keeping the previous value
    # facing: +1 = the composited head looks toward the door (left), -1 away. It is read from the render record (which
    # real cel or head sublayer was composited, and whether mirrored): structural, not a pixel measurement.
    facing = [q['facing_annot'] for q in rows]   # gaze of the head actually composited (structural, from the record)
    lie_h = 0.40
    trace = []
    for q, st, fa in zip(rows, state, facing):
        i = q['i']
        posture = 'lying' if q['h_top'] < lie_h else ('crouched' if q['h_top'] < ref_h - 0.08 else 'standing')
        x_meas = q['xw'] + DOG.CENTER_OFFSET           # back into the score's x by this film's one fixed mapping
        trace.append(dict(i=i, t=q['t'], state=st, state_score=FR[i]['dog']['state'], x_score=FR[i]['dog']['x'],
                          x_screen=round(q['cx'], 2), y_screen=round(q['cy'], 2), x_world_measured=round(x_meas, 4),
                          facing=fa, head_side_px=None if q['head_side'] is None else round(q['head_side'], 3), posture=posture, h_top_m=round(q['h_top'], 3), visible_share=round(q['vis'], 3),
                          inside_frame_share=round(q['in_frac'], 3), hidden_by=q['hiders'],
                          facing_annotated=q['facing_annot']))
    choices = []
    for (k, st), c in zip(names, SCORE['choices']):
        tk = None if on[k] is None else float(t[on[k]])
        choices.append(dict(choice=st, score_t=c['t'], measured_onset_t=tk, dt=None if tk is None else round(tk - c['t'], 3),
                            measured_by={'retreat': 'head drop or backward motion of the dog alpha',
                                         'watch_1': 'head back up (top of the alpha)', 'refuse': 'silhouette width leaves the hold / head side flips',
                                         'watch_2': 'head lifts off the paws (top of the alpha rises); the composited head looks to the door from 7.54', 'approach': 'head drop / motion toward the door',
                                         'lie_down': 'top of the alpha drops below its walking height'}[k]))
    look = None if on['look_in'] is None else float(t[on['look_in']])
    choices.append(dict(choice='looks in', score_t=26.4, measured_onset_t=look, dt=None if look is None else round(look - 26.4, 3),
                        measured_by='dark back-of-head pixels inside the dog alpha against the lit doorway'))
    settle = None if on['settle'] is None else float(t[on['settle']])
    choices.append(dict(choice='settles and stays', score_t=28.3, measured_onset_t=settle, dt=None if settle is None else round(settle - 28.3, 3),
                        measured_by='back-of-head pixels gone; chin back down'))
    # ------------------------------------------------------------- occlusion assertions over all frames
    A = {}
    A['dag_acyclic_every_frame'] = all(recs[i]['acyclic'] for i in idx)
    A['frames_with_depth_conflict'] = [i for i in idx if recs[i]['conflicts']]
    A['alpha_valid_every_frame'] = all(not recs[i]['bad_alpha'] and recs[i]['final_alpha_min'] > 0.999 for i in idx)
    A['frames_where_dog_needed_split'] = [i for i in idx if recs[i]['split_needed'].get('dog')]
    A['frames_where_person_needed_split'] = [i for i in idx if recs[i]['split_needed'].get('person')]
    ver = [(i, recs[i]['verify_max_diff'], recs[i]['verify_px_over_2pct']) for i in idx if 'verify_max_diff' in recs[i]]
    A['verifier_frames'] = len(ver)
    A['verifier_frames_disagreeing_over_50px'] = [(i, round(m, 3), n) for i, m, n in ver if n > 50]
    # no pop: an order edge that flips between consecutive frames must not have overlap in either frame
    pops = []
    for a, b in zip(idx[:-1], idx[1:]):
        Ea = {(x, y): c for x, y, c in recs[a]['edges']}; Eb = {(x, y): c for x, y, c in recs[b]['edges']}
        for (x, y), c in Eb.items():
            if (y, x) in Ea and min(c, Ea[(y, x)]) > 3:
                pops.append((b, x, y, c))
    A['order_flips_with_overlap'] = pops
    # never inside: the dog's measured centroid stays on the porch side of the sill mapping; the part behind the frame plane
    A['min_x_world_measured'] = round(min(q['x_world_measured'] for q in trace), 3)
    A['end_inside_frame_share'] = trace[-1]['inside_frame_share']
    A['end_visible_share'] = trace[-1]['visible_share']
    sdx = [abs(q['shadow_dx']) for q in rows if q['shadow_dx'] is not None]
    A['contact_shadow_offset_m_p95'] = round(float(np.percentile(sdx, 95)), 3) if sdx else None
    # overlap events (who hides the dog, when)
    ev = {}
    for q in rows:
        for n in q['hiders']:
            ev.setdefault(n, []).append(q['t'])
    intervals = {}
    for n, ts in ev.items():
        ts = sorted(ts); cur = [ts[0], ts[0]]; out = []
        for x in ts[1:]:
            if x - cur[1] > 1.5 / 24:
                out.append(cur); cur = [x, x]
            else:
                cur[1] = x
        out.append(cur)
        intervals[n] = [[round(a, 3), round(b, 3)] for a, b in out]
    pv = {}
    for i in idx:
        for x, y, c in recs[i]['edges']:
            if 'person' in x or 'person' in y:
                if x in ('jamb_L', 'jamb_R', 'lintel') or y in ('jamb_L', 'jamb_R', 'lintel'):
                    pv.setdefault('%s<%s' % (x, y), []).append(recs[i]['t'])
    person_intervals = {k: [round(min(v), 3), round(max(v), 3), len(v)] for k, v in pv.items()}
    json.dump({'frames': trace, 'mapping': 'x_world_measured = measured dog-alpha centroid (world m) + %.2f m (this film\'s fixed body-centre offset)' % DOG.CENTER_OFFSET,
               'camera_moves': True}, open(os.path.join(F, 'trace.json'), 'w'), indent=0)
    json.dump({'choices': choices, 'assertions': A, 'dog_hidden_by': intervals, 'person_vs_frame': person_intervals},
              open(os.path.join(F, 'measured.json'), 'w'), indent=1)
    print(json.dumps(choices, indent=0))
    print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 12 else '%d items: %s ...' % (len(v), v[:6])) for k, v in A.items()}, indent=0))
    print(json.dumps(intervals))


if __name__ == '__main__':
    main()
