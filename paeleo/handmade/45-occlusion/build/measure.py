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
                         contact_cov=d.get('contact_cov')))
    # the dog's own alpha pass in its layer space (before camera and shear), regenerated deterministically by the same
    # code that rendered it: posture height, rump height and frame-to-frame change of the dog's pixels
    loc = []
    prev = None
    for q in rows:
        r = DOG.dog_frame(q['i'])
        a = np.asarray(r['img'])[:, :, 3].astype(np.float32) / 255
        on_ = a > 0.5
        ys_, xs_ = np.nonzero(on_)
        hl = (ys_.max() - ys_.min()) / DOG.P_SRC
        x0_, x1_ = xs_.min(), xs_.max()
        q4 = (x1_ - x0_) // 4
        rear = on_[:, x1_ - q4:x1_ + 1] if not r['mirror'] else on_[:, x0_:x0_ + q4 + 1]
        if r['facing'] == -1 and not r['mirror']:
            rear = on_[:, x0_:x0_ + q4 + 1]
        ry = np.nonzero(rear.any(1))[0]
        hr = (ry.max() - ry.min()) / DOG.P_SRC if len(ry) else 0
        mo = 0.0 if prev is None else float(np.abs(a - prev).sum() / max(1.0, a.sum()))
        prev = a
        # head over the back: top of the front quarter vs top of the middle half (positive = head above the back line)
        import re as _re
        m_ = _re.match(r'cel(\d+)', r['parts'][0]) if r['parts'] else None
        if m_:
            n_ = int(m_.group(1))
            left = True if (n_ <= 19 or r['mirror']) else (None if n_ <= 35 else False)
        else:
            left = not r['mirror']
        hrel = None
        if left is not None:
            cols = np.nonzero(on_.any(0))[0]; c0, c1 = cols.min(), cols.max(); w_ = c1 - c0
            front = on_[:, c0:c0 + w_ // 4 + 1] if left else on_[:, c1 - w_ // 4:c1 + 1]
            mid = on_[:, c0 + w_ // 4:c1 - w_ // 4 + 1]
            ft = np.nonzero(front.any(1))[0].min(); mt = np.nonzero(mid.any(1))[0].min()
            hrel = (mt - ft) / DOG.P_SRC
        loc.append((hl, hr, mo, hrel))
    hl_ = np.array([v[0] for v in loc]); hr_ = np.array([v[1] for v in loc]); mo_ = np.array([v[2] for v in loc])
    hx_ = np.array([np.nan if v[3] is None else v[3] for v in loc])
    t = np.array([q['t'] for q in rows]); xw = np.array([q['xw'] for q in rows]); ht = np.array([q['h_top'] for q in rows])
    hs = np.array([q['head_side'] if q['head_side'] is not None else 0 for q in rows]); wd = np.array([q['width'] for q in rows])
    dk = np.array([q['dark_head'] for q in rows])

    def first(cond, after):
        k = np.nonzero((t >= after) & cond)[0]
        return int(k[0]) if len(k) else None
    def med(arr, a0, a1):
        return float(np.median(arr[(t > a0) & (t < a1)]))
    def sustained(cond, n=3):
        c = np.array(cond, bool); out = np.zeros_like(c)
        for k in range(len(c) - n + 1):
            out[k] = c[k:k + n].all()
        return out
    on = {}
    # 1.00 retreat: the head drops below the line of the back, or it moves back
    on['retreat'] = first((hx_ < med(hx_, 0.2, 0.9) - 0.10) | (xw > med(xw, 0.2, 0.9) + 0.05), 0.6)
    # 2.33 watch: the head comes back up above the line of the back
    tr = t[on['retreat']]
    on['watch_1'] = first(hx_ > 0.0, tr + 0.4)
    # 3.42 refuse: the dog's pixels start to change frame after frame (the real turn begins)
    on['refuse'] = first(sustained(mo_ > 0.08), 3.0)
    # 7.46 watch: after a second of stillness lying down, the first movement (the head comes up and round)
    on['watch_2'] = first(mo_ > 0.03, 7.0)
    # 14.71 approach: the head drops below the line of the back, or it moves toward the door
    on['approach'] = first((hx_ < med(hx_, 12, 14.5) - 0.10) | (xw < med(xw, 12, 14.5) - 0.05), 14.0)
    # 23.79 lie down: the dog's height starts to fall and keeps falling (three frames running)
    dec = np.zeros(len(hl_), bool)
    dec[1:-2] = (hl_[1:-2] < hl_[:-3] - 1e-4) & (hl_[2:-1] < hl_[1:-2] - 1e-4) & (hl_[3:] < hl_[2:-1] - 1e-4)
    on['lie_down'] = first(dec, 23.4)
    # 26.4 'come in': the head rises and turns into the doorway (the dog's own height rises over the lying hold)
    ref4 = med(hl_, 25.2, 26.2)
    on['look_in'] = first(hl_ > ref4 + 0.03, 26.0)
    on['settle'] = first(hl_ < ref4 - 0.015, (t[on['look_in']] + 0.5) if on['look_in'] is not None else 27)
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
    stand_h = med(hl_, 0.2, 0.9)
    trace = []
    for q, st, fa, (hl, hr, mo, hx) in zip(rows, state, facing, [(a_, b_, c_, (np.nan if d_ is None else d_)) for a_, b_, c_, d_ in loc]):
        i = q['i']
        posture = 'lying' if hl < 0.50 else ('crouched' if hl < stand_h - 0.06 else 'standing')
        x_meas = q['xw'] + DOG.CENTER_OFFSET           # back into the score's x by this film's one fixed mapping
        trace.append(dict(i=i, t=q['t'], state=st, state_score=FR[i]['dog']['state'], x_score=FR[i]['dog']['x'],
                          x_screen=round(q['cx'], 2), y_screen=round(q['cy'], 2), x_world_measured=round(x_meas, 4),
                          facing=fa, head_side_px=None if q['head_side'] is None else round(q['head_side'], 3), posture=posture, dog_height_m=round(hl, 3), head_over_back_m=None if np.isnan(hx) else round(float(hx), 3), pixel_change=round(mo, 3), visible_share=round(q['vis'], 3),
                          inside_frame_share=round(q['in_frac'], 3), hidden_by=q['hiders'],
                          facing_annotated=q['facing_annot']))
    choices = []
    for (k, st), c in zip(names, SCORE['choices']):
        tk = None if on[k] is None else float(t[on[k]])
        choices.append(dict(choice=st, score_t=c['t'], measured_onset_t=tk, dt=None if tk is None else round(tk - c['t'], 3),
                            measured_by={'retreat': 'head drops below the line of the back (dog alpha: front-quarter top vs middle top) or its measured position moves back',
                                         'watch_1': 'head back above the line of the back', 'refuse': 'the dog\'s own pixels change three frames running (the real turn starts)',
                                         'watch_2': 'first movement of the lying dog\'s pixels (the head comes up); the composited head looks to the door from 7.54', 'approach': 'head drops below the line of the back, or it moves toward the door',
                                         'lie_down': 'the dog alpha\'s height falls three frames running (it goes down, hind end first)'}[k]))
    look = None if on['look_in'] is None else float(t[on['look_in']])
    choices.append(dict(choice='looks in', score_t=26.4, measured_onset_t=look, dt=None if look is None else round(look - 26.4, 3),
                        measured_by='top of the lying dog rises as the head turns into the doorway (h_top); what turns is judged by viewing'))
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
    cc = [q['contact_cov'] for q in rows if q['contact_cov'] is not None]
    A['contact_shadow_under_dog_base_min'] = round(float(min(cc)), 3) if cc else None
    A['contact_shadow_under_dog_base_median'] = round(float(np.median(cc)), 3) if cc else None
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
