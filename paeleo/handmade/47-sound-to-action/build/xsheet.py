"""Exposure sheet (alignment engineer + body-gesture choreographer + mouth-shape designer).
Reads the typed audio timeline and the score, writes one line per scene frame naming:
  dog:    the sprite key exposed (a drawing from the dog's sprite set) and where it stands (x along the porch, metres)
  person: pose key and the viseme exposed
  door:   angle; light level
  sound marks: the voice envelope for the visible wavefronts, and the words as they are spoken
Every dog answer is scheduled from a SOUND: the cue vowel's onset + LAT (hearing latency), the end of a voice, the
dog's own sniffs, the last footfall. The score supplies where the dog is (x) and what each choice is.
Dog drawings are exposed on twos (12 drawings/s) and held; walking drawings change only when the body has travelled one
gait step, so planted feet do not slide. Visemes are exposed on ones with a 40 ms lead and a 2-frame minimum hold.
Output: build/xsheet.json, build/foley.json (sounds the dog's and person's actions make, for the mix)
"""
import json, math, os
import numpy as np, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
AT = json.load(open(os.path.join(HERE, 'audio_timeline.json')))
LAT = AT['LAT']
FPS, N = 24, 768
SF = SCORE['frames']
EV = {e['id']: e for e in AT['events']}
STRIDE, NG, DUTY = 0.55, 12, 0.62


def ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def lerp(a, b, u): return a + (b - a) * u


def sx(t):
    """score x at time t (linear between frames)"""
    f = t * FPS; i = int(min(N - 2, max(0, math.floor(f)))); u = f - i
    return lerp(SF[i]['dog']['x'], SF[i + 1]['dog']['x'], u)


# ---- times the sound gives us
t_ret = EV['call1']['cue_t'] + LAT                       # backs away at "here"
t_acc1 = EV['call4']['cue_t'] + LAT                      # flinch accent on "on"
voice_end = max(p['t1'] for p in EV['call4']['phones'])  # the call stops sounding
t_stop = voice_end + 0.36                                # one breath of silence later it stops backing, lifts its head
t_ref = EV['call3']['cue_t'] + LAT                       # turns its back at the second "here"
t_acc2 = EV['call4b']['cue_t'] + LAT                     # "come on!" -> head lower, then lies down, back turned
t_creak = EV['door']['t0'] + LAT                         # ear turns to the hinge, nothing else
t_look = EV['soft1']['cue_t'] + LAT                      # "it's all right" -> head comes round
t_soft2 = EV['soft2']['cue_t'] + LAT
sn = EV['sniff']; sniffs = [sn['t0'] + k * sn['gap'] for k in range(sn['n'])]
t_app = sniffs[-1] + 0.12 + 0.36                         # after the last sniff, one breath, the first step
t_in = EV['soft3']['cue_t'] + LAT                        # "come in" -> looks in
# where the walk ends: the score's x reaches the sill and stays
t_arrive = next(f['t'] for f in SF if f['t'] > 20 and abs(f['dog']['x'] - SF[-1]['dog']['x']) < 0.003)
t_lie = t_arrive + 1 / 12                                # one drawing after the last footfall
X_END = SF[-1]['dog']['x']


def dog_target(t):
    """continuous acting targets at time t; quantized into a sprite key below"""
    d = dict(yaw=0, hy=0, hp=9, ear=2, tl=5, wag=0, cr=1, lie=0, rs=0, sn=0, br=0, st=10, walk=False, plan='watch')
    br = 1 if (t % 2.4) > 1.2 else 0
    d['br'] = br
    if t < t_ret:
        return d
    if t < t_stop:  # backing away
        u = (t - t_ret) * 12
        d.update(plan='retreat', walk=True)
        d['cr'] = min(9, 3 + 3 * int(u)); d['hp'] = max(3, 7 - 2 * int(u)); d['ear'] = 1 if u < 1 else 0
        d['tl'] = min(13, 8 + 3 * int(u))
        if t_acc1 <= t < t_acc1 + 0.25: d['cr'] = 10; d['tl'] = 13   # accent on 'on': cowers lower, head stays
        return d
    if t < t_ref:  # stops, lifts its head, watches (finishing the score's last backing steps)
        u = ease((t - t_stop) / 0.45)
        d.update(plan='watch', walk=True)
        d['cr'] = round(lerp(9, 1, u)); d['hp'] = round(lerp(4, 9, u)); d['ear'] = 0 if u < 0.3 else (1 if u < 0.7 else 2)
        d['tl'] = round(lerp(13, 5, u))
        return d
    if t < t_look:  # refuses: head leads, body follows, round through the rear view; then lies with its back to them
        d.update(plan='refuse')
        d['hy'] = round(165 * ease((t - t_ref + 0.1) / 0.55)); d['yaw'] = round(150 * ease((t - t_ref - 0.02) / 0.6))
        d['hp'] = 6 if t - t_ref < 0.1 else (4 if t - t_ref < 0.3 else 3)
        d['ear'] = 1 if t - t_ref < 0.15 else 0; d['tl'] = 8 if t - t_ref < 0.15 else 11; d['cr'] = 2
        if t - t_ref < 0.85: d['walk'] = True; d['st'] = 3
        if t >= t_acc2: d['hp'] = 2; d['tl'] = 12
        lie0 = t_acc2 + 0.2
        if t >= lie0: d['lie'] = round(10 * ease((t - lie0) / 0.7)); d['cr'] = 0
        if t >= 5.6: d['rs'] = round(10 * ease((t - 5.6) / 1.0)); d['hp'] = 1
        if t_creak <= t < t_creak + 0.5: d['ear'] = 2       # hears the door; does not answer
        return d
    if t < t_app:  # turns back to look, rises, turns round, watches; silence animates thought
        d.update(plan='watch')
        u = (t - t_look)
        d['hy'] = round(lerp(165, 8, ease(u / 0.33))); d['hp'] = round(lerp(2, 7, ease(u / 0.3)))
        d['rs'] = 0 if u > 0.05 else 5; d['ear'] = 2; d['tl'] = 9
        rise0, turn0 = t_look + 0.17, t_look + 0.55
        d['lie'] = round(10 * (1 - ease((t - rise0) / 0.4)))
        d['yaw'] = round(150 * (1 - ease((t - turn0) / 0.65)))
        if turn0 <= t < turn0 + 0.7: d['walk'] = True; d['st'] = 3
        if t >= turn0: d['hy'] = min(d['yaw'] + 8, 8) if d['yaw'] < 8 else 8
        if t >= turn0 + 0.65:
            d['hy'] = 0; d['hp'] = 9; d['tl'] = 5
        if t >= turn0 + 0.65 and t < 9.6: d['hy'] = 0
        if 9.6 <= t < t_soft2: d['ear'] = 1                     # listening eases
        if t_soft2 <= t < t_soft2 + 1.0:                        # "it's okay": ears up, a low wag
            d['ear'] = 2; d['tl'] = 4; k = int((t - t_soft2 - 0.15) * 6)
            d['wag'] = 0 if t - t_soft2 < 0.15 else (1 if k % 2 == 0 else -1)
        if t >= t_soft2 + 1.0: d['tl'] = 4; d['ear'] = 2
        if 12.3 <= t < 12.95: d['hp'] = round(lerp(9, 6, ease((t - 12.3) / 0.25)))   # looks at the low hand
        if 12.95 <= t < 13.6: d['hp'] = 8; d['hy'] = -6                               # up at the light in the door
        if 13.6 <= t: d['hp'] = 7; d['hy'] = 0
        for s in sniffs:
            if s <= t < s + 0.09: d['sn'] = 1
        if t >= sniffs[-1] + 0.2: d['hp'] = round(lerp(7, 1, ease((t - sniffs[-1] - 0.2) / 0.3))); d['ear'] = 1; d['tl'] = 3
        return d
    if t < t_lie:  # comes, head low (below the line of the back the whole way)
        d.update(plan='approach', walk=True, hp=1, ear=1, tl=3, cr=1)
        d['wag'] = [0, 1, 0, -1][int((t - t_app) * 4) % 4]
        if t > t_arrive - 0.5: d['hp'] = 2; d['wag'] = 0
        return d
    # lies down across the sill
    d.update(plan='lie_down', hp=5, ear=1, tl=3, cr=0)
    d['lie'] = math.ceil(10 * ease((t - t_lie + 0.12) / 0.75))
    if t >= t_lie + 0.7: d['hp'] = 6
    if 25.5 <= t: d['hp'] = round(lerp(6, 3, ease((t - 25.5) / 0.5)))
    if t >= t_in:  # come in: the head turns into the lit doorway, then settles back
        u = t - t_in
        d['hy'] = round(90 * ease((u + 0.1) / 0.32)); d['hp'] = round(lerp(3, 6, ease((u + 0.1) / 0.32))); d['ear'] = 2
        if 0.35 <= u < 1.45: d['wag'] = [1, -1][int((u - 0.35) * 3) % 2]
        t_back = t_in + 1.5
        if t >= t_back:
            v = t - t_back
            d['hy'] = round(90 * (1 - ease(v / 0.3))); d['hp'] = round(lerp(6, 2, ease(v / 0.55)))
            d['rs'] = round(10 * ease((v - 0.25) / 0.5)); d['ear'] = 1 if v > 0.4 else 2; d['wag'] = 0
    return d


def quant_key(d, g):
    return 'yaw=%d,hy=%d,hp=%d,ear=%d,tl=%d,wag=%d,cr=%d,lie=%d,g=%d,br=%d,rs=%d,sn=%d,st=%d' % (
        d['yaw'], d['hy'], d['hp'], d['ear'], d['tl'], d['wag'], d['cr'], d['lie'], g, d['br'], d['rs'], d['sn'], d['st'])


def stance(u):
    return u < DUTY


def build_dog():
    frames, foley = [], []
    x0 = sx(0)
    prev = None
    turn_phase = 0
    for i in range(N):
        t = i / FPS
        d = dog_target(t)
        # on twos: hold the previous drawing, except that an answer may land on a one (the first drawing of a new plan)
        if i % 2 == 1 and not (prev and d['plan'] != prev['plan']):
            frames.append(dict(prev, i=i, t=round(t, 4))); continue
        x = sx(t)
        if d['walk'] and d['st'] == 10:
            ph = (x0 - x) / STRIDE                 # forward = toward the door (-x)
            fwd = sx(t) < sx(max(0, t - 0.25)) - 1e-4               # moving toward the door
            gi = math.floor(ph * NG + (0.9 if fwd else 0.0))   # the first drawing of a step comes as soon as the body moves
            xd = x0 - gi / NG * STRIDE              # the body sits where this drawing's planted feet are
            g = gi % NG
        elif d['walk']:                             # stepping round in place while turning
            turn_phase += 1
            g = (turn_phase * 2) % NG; xd = prev['x'] if prev else x
        else:
            g = -1; xd = prev['x'] if (prev and abs(prev['x'] - x) < 0.02 and prev['g'] == -1) else x
            if prev and prev['g'] >= 0 and abs(prev['x'] - x) < 0.03: xd = prev['x']
        if d['lie'] > 0 or d['plan'] == 'lie_down': xd = x if d['plan'] != 'lie_down' else X_END
        key = quant_key(d, g)
        # footfalls: a leg going from swing to stance between the previous drawing and this one
        if prev is not None and g >= 0 and prev['g'] >= 0 and g != prev['g']:
            for off, leg in [(0.25, 'FL'), (0.75, 'FR'), (0.0, 'HL'), (0.5, 'HR')]:
                ua = ((prev['g'] / NG + off) % 1); ub = ((g / NG + off) % 1)
                if (not stance(ua)) and stance(ub):
                    foley.append({'kind': 'paw', 'src': 'dog', 't0': round(t, 4), 'x': round(xd, 3), 'leg': leg,
                                  'soft': d['st'] != 10})
        cur = {'i': i, 't': round(t, 4), 'key': key, 'x': round(xd, 4), 'z': 0.32, 'g': g, 'plan': d['plan']}
        frames.append(cur); prev = cur
    # body sounds that follow the acting
    t_l0 = t_acc2 + 0.2
    foley += [{'kind': 'thump', 'src': 'dog', 't0': round(t_l0 + 0.35, 3), 'x': 4.0, 'g': -14},
              {'kind': 'thump', 'src': 'dog', 't0': round(t_l0 + 0.6, 3), 'x': 4.0, 'g': -12},
              {'kind': 'thump', 'src': 'dog', 't0': round(t_lie + 0.35, 3), 'x': X_END, 'g': -14},
              {'kind': 'thump', 'src': 'dog', 't0': round(t_lie + 0.62, 3), 'x': X_END, 'g': -12},
              {'kind': 'sigh', 'src': 'dog', 't0': round(t_lie + 1.15, 3), 'x': X_END, 'dur': 0.9},
              {'kind': 'sigh', 'src': 'dog', 't0': round(t_in + 2.3, 3), 'x': X_END, 'dur': 1.2}]
    for s in sniffs:
        foley.append({'kind': 'sniff', 'src': 'dog', 't0': round(s, 3), 'x': 4.0})
    # tail on the boards while it wags lying down
    wl = None
    for f in frames:
        if f['plan'] == 'lie_down':
            w = int(f['key'].split('wag=')[1].split(',')[0])
            if w != 0 and wl is not None and w != wl:
                foley.append({'kind': 'tailthump', 'src': 'dog', 't0': f['t'], 'x': X_END + 0.5})
            wl = w
    return frames, foley


# ---- person
VIS = {}
for p in 'aa ah ay aw ae'.split(): VIS[p] = 'AA'
for p in 'ao ow oy uw uh w'.split(): VIS[p] = 'OO'
for p in 'iy ih ey eh y'.split(): VIS[p] = 'EE'
for p in 'r er'.split(): VIS[p] = 'R'
for p in 'm b p'.split(): VIS[p] = 'MBP'
for p in 'f v'.split(): VIS[p] = 'FV'
for p in 'l'.split(): VIS[p] = 'L'
for p in 't d s z n th dh sh ch jh zh'.split(): VIS[p] = 'TS'
for p in 'k g hh ng'.split(): VIS[p] = 'KG'


def build_visemes():
    """per frame viseme + emphasis. Linguistic shape from the phone; emphasis (jaw scale) from the line's style."""
    vis = ['X'] * N; emph = [0.0] * N
    lines = [e for e in AT['events'] if e['kind'] == 'voice']
    for i in range(N):
        t = i / FPS + 0.04  # mouth leads the sound by 40 ms
        for L in lines:
            for p in L['phones']:
                if p['t0'] <= t < p['t1']:
                    vis[i] = VIS.get(p['p'], 'KG'); emph[i] = 1.0 if L['style'] == 'call' else 0.45
    # minimum hold 2 frames: a single-frame shape takes the previous shape's place
    for i in range(1, N - 1):
        if vis[i] != vis[i - 1] and vis[i] != vis[i + 1] and vis[i - 1] == vis[i + 1]:
            vis[i] = vis[i - 1]
    # closures must show: an MBP that the hold rule would remove is kept
    return vis, emph


def person_track():
    vis, emph = build_visemes()
    out = []
    for i in range(N):
        t = i / FPS
        p = dict(x=-0.28, z=0.10, dir=1, rch=0, bk=0, lean=0, sit=0, push=0, low=0, w=-1, ht=0, rest=0)
        # beckon accents on the stressed vowels of the first calls
        for e in ('call1', 'call4'):
            c = EV[e]['cue_t']
            if c - 0.05 <= t < c + 0.3: p['bk'] = 10 if t < c + 0.15 else 5
        if EV['call1']['t0'] <= t < EV['call4']['t1']: p['lean'] = 1
        # reach with the second call
        if t >= 2.95: p['rch'] = round(10 * ease((t - 2.95) / 0.55)); p['lean'] = round(3 * ease((t - 2.95) / 0.55))
        if t >= 4.55: p['rch'] = round(10 * (1 - ease((t - 4.55) / 0.3))); p['lean'] = round(3 * (1 - ease((t - 4.55) / 0.3)))
        # steps aside: turn, three steps, turn, sit
        if t >= 4.85:
            p['dir'] = 0 if t < 4.93 else -1
            u = ease((t - 4.93) / 0.62)
            p['x'] = lerp(-0.28, -1.25, u); p['z'] = lerp(0.10, 0.16, u)
            if 4.93 <= t < 5.55: p['w'] = int((t - 4.93) / 0.62 * 8) % 8
        if t >= 5.6:
            p['dir'] = 0 if t < 5.68 else 1; p['w'] = -1; p['x'] = -1.25
        if t >= 5.75: p['sit'] = round(10 * ease((t - 5.75) / 0.55))
        if 6.0 <= t < 6.6: p['push'] = round(10 * ease((t - 6.0) / 0.2)) if t < 6.25 else round(10 * (1 - ease((t - 6.25) / 0.3)))
        if t >= 6.8: p['low'] = round(10 * ease((t - 6.8) / 0.35))
        if t >= 7.0: p['ht'] = 1
        if t >= 29.6: p['low'] = round(10 * (1 - ease((t - 29.6) / 0.35))); p['rest'] = round(10 * ease((t - 29.6) / 0.35))
        p['vis'] = vis[i]; p['em'] = emph[i]
        out.append(p)
    return out


def door_track():
    out = []
    t0, t1 = EV['door']['t0'], EV['door']['t1']
    for i in range(N):
        t = i / FPS
        u = 0 if t < t0 else min(1, (t - t0) / (t1 - t0))
        k = 1 - (1 - u) ** 2.2
        ang = 18 + (102 - 18) * k + (4 * math.sin((t - t1) * 9) * math.exp(-(t - t1) * 4) if t > t1 else 0)
        light = 0.10 + 0.90 * ease((t - t0 - 0.05) / 0.7)
        out.append({'ang': round(ang, 2), 'light': round(light, 3)})
    return out


def voice_env():
    """RMS envelope (dBFS of the source line, before the mix) per frame, for the visible wavefronts"""
    env = [None] * N
    for e in AT['events']:
        if e['kind'] != 'voice': continue
        w = wave.open(os.path.join(ROOT, e['file']))
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; sr = w.getframerate()
        for i in range(N):
            t = i / FPS - e['t0']
            if 0 <= t < len(x) / sr:
                a = int(t * sr); seg = x[a:a + sr // FPS]
                if len(seg): env[i] = {'db': round(float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-6)), 1), 'style': e['style'], 'id': e['id']}
    return env


def main():
    dog, foley = build_dog()
    per = person_track(); door = door_track(); env = voice_env()
    words = [{'w': w['w'], 't0': w['t0'], 't1': w['t1'], 'style': e['style'], 'line': e['id']}
             for e in AT['events'] if e['kind'] == 'voice' for w in e['words']]
    lines = [{'id': e['id'], 'text': e['text'], 't0': e['t0'], 't1': e['t1'], 'style': e['style']} for e in AT['events'] if e['kind'] == 'voice']
    frames = [{'i': i, 't': dog[i]['t'], 'dog': {k: dog[i][k] for k in ('key', 'x', 'z', 'plan')}, 'person': per[i], 'door': door[i], 'voice': env[i]}
              for i in range(N)]
    sched = {'t_ret': t_ret, 't_stop': t_stop, 't_ref': t_ref, 't_look': t_look, 't_app': t_app, 't_lie': t_lie, 't_in': t_in,
             't_acc1': t_acc1, 't_acc2': t_acc2, 't_creak': t_creak, 't_soft2': t_soft2, 'sniffs': sniffs, 't_arrive': t_arrive}
    json.dump({'fps': FPS, 'N': N, 'LAT': LAT, 'schedule': {k: (round(v, 3) if isinstance(v, float) else v) for k, v in sched.items()},
               'lines': lines, 'words': words, 'frames': frames}, open(os.path.join(HERE, 'xsheet.json'), 'w'))
    json.dump(foley, open(os.path.join(HERE, 'foley.json'), 'w'), indent=0)
    keys = sorted(set(f['dog']['key'] for f in frames))
    print('dog drawings exposed:', len(keys), ' footfalls:', sum(1 for f in foley if f['kind'] == 'paw'))
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in sched.items()})


if __name__ == '__main__':
    main()
