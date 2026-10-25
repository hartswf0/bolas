"""Independent-of-the-plan measurement: read what the renderer actually drew (build/cache/measure.json: per scene frame,
pixel statistics of the ID pass: dog body, dog head, dog muzzle, the person's open mouth) and derive
  - the measured onset of each choice (first frame the drawing answers, by a detector fixed per choice),
  - the dog's measured screen position, facing and posture per frame -> trace.json,
  - sound->action latencies: cue vowel onset (synthesizer segment time) -> measured onset,
  - lip-sync assertions: no open mouth in silence; a visible closure inside every /m/.
The state label in trace.json switches at the MEASURED onsets, not at the score's times.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
XS = json.load(open(os.path.join(HERE, 'xsheet.json')))
AT = json.load(open(os.path.join(HERE, 'audio_timeline.json')))
FPS = 24
EV = {e['id']: e for e in AT['events']}


def f_of(t): return int(round(t * FPS))


def feat(i):
    m = M[i]
    return {'bx': m['body']['cx'], 'by': m['body']['cy'], 'hx': m['head'].get('cx'), 'hy': m['head'].get('cy'),
            'top': m['dog']['y0'], 'mx': m['muzzle'].get('cx'), 'mn': m['muzzle']['n']}


def first_change(t_from, t_to, keys, thr, sign=0):
    """first frame in (t_from, t_to] where any feature in keys differs from its value at t_from by >= thr px
    (sign=+1: only increases count, -1: only decreases)"""
    a = f_of(t_from); ref = feat(a)
    for i in range(a + 1, f_of(t_to) + 1):
        f = feat(i)
        for k in keys:
            if f[k] is None or ref[k] is None: continue
            d = f[k] - ref[k]
            if (sign == 0 and abs(d) >= thr) or (sign > 0 and d >= thr) or (sign < 0 and d <= -thr):
                return i, k, round(d, 2)
    return None, None, None


def head_rise(t_from, t_to, thr):
    """first frame where the head has risen thr px above its lowest point since t_from"""
    a = f_of(t_from); low = feat(a)['hy']
    for i in range(a + 1, f_of(t_to) + 1):
        hy = feat(i)['hy']; low = max(low, hy)
        if low - hy >= thr: return i, 'hy', round(hy - low, 2)
    return None, None, None


ch = SCORE['choices']
det = []
# each detector: (choice index, how, window start). Windows open 0.5 s before the score time, as the checker's do.
specs = [
    (0, 'dog drawing changes after the hold (body, head or top edge moves >= 2 px)', lambda c: first_change(c - 0.5, c + 0.5, ['bx', 'hx', 'hy', 'top'], 2)),
    (1, 'head rises >= 4 px above its lowest point while backing', lambda c: head_rise(c - 0.5, c + 0.5, 4)),
    (2, 'dog drawing changes after the hold (body, head or top edge moves >= 2 px)', lambda c: first_change(c - 0.5, c + 0.5, ['bx', 'hx', 'hy', 'top'], 2)),
    (3, 'head moves >= 3 px after the refusal hold (head only: breath moves the chest)', lambda c: first_change(c - 0.5, c + 0.5, ['hx', 'hy'], 3)),
    (4, 'body centroid moves toward the door >= 2 px (sniffing moves only the head)', lambda c: first_change(c - 0.5, c + 0.5, ['bx'], 2, -1)),
    (5, 'body centroid drops >= 3 px (lying down)', lambda c: first_change(c - 0.5, c + 0.5, ['by'], 3, +1)),
]
onsets = {}
for k, how, fn in specs:
    c = ch[k]; i, key, d = fn(c['t'])
    t = None if i is None else round(i / FPS, 4)
    onsets[k] = i
    det.append({'choice': f"{c['from']} -> {c['to']}", 'score_t': c['t'], 'measured_onset_t': t, 'measured_frame': i,
                'dt': None if t is None else round(t - c['t'], 3), 'detector': how, 'feature': key, 'delta_px': d})
# 26.4: hears "come in", looks in (head moves >= 3 px after its lowering has finished)
i, key, d = first_change(26.1, 26.9, ['hx', 'hy'], 3)
det.append({'choice': 'lie_down: hears "come in" -> looks in', 'score_t': 26.4, 'measured_onset_t': round(i / FPS, 4) if i else None,
            'measured_frame': i, 'dt': round(i / FPS - 26.4, 3) if i else None, 'detector': 'head moves >= 3 px after 26.1 s', 'feature': key, 'delta_px': d})
i_settle, _, _ = first_change(27.6, 29.0, ['hx', 'hy'], 3)
det.append({'choice': 'looks in -> settles, chin down, stays', 'score_t': 28.0, 'measured_onset_t': round(i_settle / FPS, 4) if i_settle else None,
            'measured_frame': i_settle, 'detector': 'head moves >= 3 px after 27.6 s', 'note': 'not a scored choice'})

# causes: the sound each answer follows
causes = [('retreat', 'call1', 0), ('refuse', 'call3', 2), ('watch (turns back to look)', 'soft1', 3), ('looks in', 'soft3', 6)]
lat = []
for name, lid, k in causes:
    e = EV[lid]; t_on = det[k]['measured_onset_t']
    lat.append({'answer': name, 'cause': f"{lid} \"{e['text']}\" cue vowel of '{e['cue_word']}'", 'cue_t': e['cue_t'],
                'answer_onset_t': t_on, 'latency_s': round(t_on - e['cue_t'], 3)})
voice_end = max(p['t1'] for p in EV['call4']['phones'])
lat.append({'answer': 'stops backing, lifts its head (watch)', 'cause': 'the call stops sounding (last phone of "Come on!")', 'cue_t': voice_end,
            'answer_onset_t': det[1]['measured_onset_t'], 'latency_s': round(det[1]['measured_onset_t'] - voice_end, 3)})
sn = EV['sniff']; last_sniff = sn['t0'] + (sn['n'] - 1) * sn['gap']
lat.append({'answer': 'approach (first step)', 'cause': "the dog's own third sniff, after 3.2 s of silence", 'cue_t': last_sniff,
            'answer_onset_t': det[4]['measured_onset_t'], 'latency_s': round(det[4]['measured_onset_t'] - last_sniff, 3)})
foley = json.load(open(os.path.join(HERE, 'foley.json')))
last_paw = max(f['t0'] for f in foley if f['kind'] == 'paw')
lat.append({'answer': 'lies down', 'cause': 'its last footfall at the sill', 'cue_t': last_paw, 'answer_onset_t': det[5]['measured_onset_t'],
            'latency_s': round(det[5]['measured_onset_t'] - last_paw, 3)})
# trace: state switches at measured onsets
bounds = [(onsets[k], ch[k]['to']) for k in range(6)]
fw = None; trace = []
for i in range(768):
    st = 'watch'
    for fi, s in bounds:
        if fi is not None and i >= fi: st = s
    f = feat(i)
    if f['mx'] is not None and f['hx'] is not None and f['mn'] > 40 and abs(f['mx'] - f['hx']) > 2:
        fw = 1 if f['mx'] < f['hx'] else -1
    by = f['by']; posture = 'lying' if by > 475 else ('crouched' if by > 452 else 'standing')
    trace.append({'i': i, 't': round(i / FPS, 4), 'state': st, 'x_score': SCORE['frames'][i]['dog']['x'], 'x_screen': f['bx'], 'y_screen': f['by'],
                  'facing': fw, 'posture': posture, 'head_screen': [f['hx'], f['hy']], 'sprite': XS['frames'][i]['dog']['key']})

# lip-sync assertions
voiced = set()
for e in AT['events']:
    if e['kind'] != 'voice': continue
    for p in e['phones']:
        for i in range(f_of(p['t0']) - 2, f_of(p['t1']) + 2): voiced.add(i)
open_silent = [i for i in range(768) if M[i]['mouth'] > 0 and i not in voiced]
mm = []
for e in AT['events']:
    if e['kind'] != 'voice': continue
    for p in e['phones']:
        if p['p'] == 'm':
            fr = list(range(int(p['t0'] * FPS) - 1, int(p['t1'] * FPS) + 2))
            mm.append({'line': e['id'], 't0': p['t0'], 't1': p['t1'], 'closed_frames': [i for i in fr if M[i]['mouth'] == 0],
                       'ok': any(M[i]['mouth'] == 0 for i in fr)})
open_frames = sum(1 for i in range(768) if M[i]['mouth'] > 0)
lips = {'frames_mouth_open': open_frames, 'frames_open_in_silence': open_silent, 'no_flapping_in_silence': not open_silent,
        'm_closures': mm, 'all_m_closed': all(x['ok'] for x in mm),
        'note': 'measured on the ID pass: pixels of the open-mouth interior drawn by the viseme; silence = more than 2 frames from any phone'}

meta = {'about': 'Measured from the render (ID pass pixel statistics) of PAE-02 SCION 47. x_screen/y_screen: dog body centroid (px). '
                 'facing: +1 muzzle left of skull (toward the door), -1 away, from the ID pass. state: switches at the measured onsets below. '
                 'Camera is fixed, so x_screen is the world position up to scale.', 'onsets': det, 'sound_to_action': lat, 'lipsync': lips}
json.dump({'meta': meta, 'frames': trace}, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
for d in det: print(f"{d['choice']:45s} score {d['score_t']:6.3f}  measured {d['measured_onset_t']}  dt {d.get('dt')}  ({d.get('feature')} {d.get('delta_px')})")
for l in lat: print('  ', l['answer'], '<-', l['cause'], 'latency', l['latency_s'])
print('lips: open frames', open_frames, 'open in silence', len(open_silent), 'm closed', lips['all_m_closed'])
