"""SCION-48 · the dog's own machine.

A hierarchical utility state machine. The world (the person, the door, the voice: the circumstances of the score) is
given as data, frame by frame. The dog is NOT given its states: it perceives the world through its own facing (it cannot
see what is behind it), keeps a world model (what it last saw), carries four drives (fear, trust, curiosity and the memory
of being pressed), scores every behaviour by a utility, and chooses one, subject to guards, priorities, hysteresis and
action windows (minimum dwell). Its locomotion and its body (heading, head, lie, crouch, tail ...) are a second layer
driven by the chosen state and the drives, so the head leads the body because the head responds faster, not because a
key says so.

Top states:   watch · retreat · refuse{turn, sulk} · approach · lie_down{settle, rest, look_in}
Candidate that is scored but has no state: cross (go inside). Its utility is logged; it never wins, by the dog's own
threshold cost (persistent world data: inside is not its place).

Time base 24 ticks/s, one tick per film frame. Units: metres along the porch (score x: sill 0.56, threshold 0).
python3 machine.py [params.json]  ->  cache/machine.json
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')
DT = 1 / 24
STATES = ['watch', 'retreat', 'refuse', 'approach', 'lie_down']

# the tuned parameters (see tune.py and ledger.jsonl); every number is a property of THIS dog
PARAMS = {
    'tau_press': 0.07,    # s, how fast a command is felt (perceptual smoothing)
    'g_fear': 2.2,        # fear gain from pressure
    'l_fear': 0.22,       # fear decay /s
    'calm_sit': 0.6,      # extra fear decay when the person is seen sitting
    'c_soft': 0.75,       # curiosity kick from a soft voice onset
    'l_cur': 0.35,        # curiosity decay /s
    'r_trust': 0.42,      # trust gain /s per unit invitation
    'l_trust': 0.6,       # trust loss per unit pressure
    'theta_T': 0.6,       # trust needed to come
    'a_app': 2.2,         # utility slope of approach in trust
    'x_edge': 4.4,        # the porch steps as the dog knows them (score metres): room to back away
    'room_w': 0.8,
    'sulk0': 0.30, 'sulk1': 0.40,
    'v_ret': 0.85,        # m/s backing speed at full pressure
    'v0': 0.25, 'v1': 0.5,   # approach pace = v0 + v1*(trust above the threshold)  (more trust, longer stride)
    'k_brake': 1.6,      # /s arrival braking toward the sill
    'acc': 1.4,           # m/s^2
    'goal': 0.59,         # the place it chooses: the sill, front half in, back half out
    'W_inside': 1.25,     # threshold cost of going in
    'theta_look': 0.55,   # curiosity that lifts the head off the paws to look in
    'hyst': 0.06,
    'arrive': 0.03,       # m: close enough to the place it chose
}
DWELL = {'watch': 0.6, 'retreat': 0.5, 'refuse': 2.0, 'approach': 0.8, 'lie_down': 2.0}
DANGER = ('retreat', 'refuse')
PERSON_X = {'doorway': -0.28, 'beside': -1.25}


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def ease(cur, tgt, tau):
    return cur + (tgt - cur) * (1 - math.exp(-DT / max(tau, 1e-6)))


def world_frames():
    sc = json.load(open(SCORE))
    W = []
    for f in sc['frames']:
        p = f['person']
        W.append({'t': f['t'], 'voice': p['voice'], 'hand': p['hand'], 'sit': p['sit'], 'reach': p['reach'], 'low': p['low'],
                  'place': p['place'], 'posture': p['posture'], 'px': p['x'], 'door': f['door'], 'mouth': p['mouth'], 'prompt': f['prompt']})
    return sc, W


def run(P=None, W=None):
    P = dict(PARAMS, **(P or {}))
    if W is None:
        _, W = world_frames()
    d = dict(state='watch', sub='', since=0.0, x=3.0, v=0.0, psi=0.0, hy=0.0, F=0.2, T=0.2, C=0.1, M=0.0, press=0.0,
             m_sit=0.0, m_door=0.0, m_low=0.0, soft=0.0, lie=0.0, rest=0.0, look=0.0, crouch=0.05, head=0.9, tail=0.5,
             ear=0.8, phase=0.0, wagph=0.0, lastvoice='none', lastdoor='ajar', lasthand='none', lying_since=None)
    frames, events = [], []
    LAT = 2                                             # ticks of perceptual latency (about 80 ms)
    for i, w0 in enumerate(W):
        t = i * DT
        w = W[max(0, i - LAT)]                          # what reaches the dog now happened two ticks ago
        # ---------- perception: hearing is all-round, seeing goes where the head points ----------
        gaze = d['psi'] + d['hy']                       # 0 = toward the door and the person, pi = away
        vis = clamp(0.5 + 0.7 * math.cos(gaze))
        call = 1.0 if w['voice'] == 'call' else 0.0
        softv = 1.0 if w['voice'] == 'soft' else 0.0
        door = 1.0 if w['door'] == 'open' else 0.0
        k = 1 - math.exp(-DT / 0.15)
        d['m_sit'] += (w['sit'] - d['m_sit']) * k * vis
        d['m_low'] += (w['low'] - d['m_low']) * k * vis
        d['m_door'] += (door - d['m_door']) * k * clamp(vis + 0.3 * door)   # the light on the boards is seen even facing away
        reach = w['reach'] * vis
        dist = d['x'] - w['px']
        prox = clamp(5.0 / (dist + 1.2), 0.5, 1.3)
        loom = (1 - w['sit']) * (1.0 if w['place'] == 'doorway' else 0.3) * vis
        press_in = (0.8 * call + 0.9 * reach) * prox      # the push: commands only
        loomf = 0.22 * loom * prox                         # a standing figure in the door: unease, not a push
        d['press'] = ease(d['press'], press_in, P['tau_press'])
        press = d['press']
        # ---------- drives ----------
        d['F'] = clamp(d['F'] + DT * (P['g_fear'] * (press + loomf) * (1 - d['F']) - P['l_fear'] * d['F'] * (1 + P['calm_sit'] * d['m_sit'])))
        d['M'] += DT * (0.5 * (call + reach) - 0.04 * d['M'])                       # remembers being pressed
        if softv and d['lastvoice'] != 'soft':
            d['C'] += P['c_soft'] * (1 - d['C']); events.append({'t': round(t, 3), 'e': 'hears', 'what': 'soft voice'})
        if call and d['lastvoice'] != 'call':
            events.append({'t': round(t, 3), 'e': 'hears', 'what': 'call'})
        if w['door'] != d['lastdoor']:
            d['C'] += 0.25 * clamp(vis + 0.3) * (1 - d['C'])
        if w['hand'] == 'low' and d['lasthand'] != 'low':
            d['C'] += 0.2 * vis * (1 - d['C'])
        d['C'] = clamp(d['C'] + DT * (0.12 * d['m_door'] * vis - P['l_cur'] * d['C']))
        d['soft'] = clamp(d['soft'] + DT * (1.5 * softv * (1 - d['soft']) - 0.08 * d['soft']))
        inv = clamp(0.25 * d['m_sit'] + 0.15 * d['m_door'] + 0.25 * d['m_low'] + 0.35 * d['soft'] - 0.6 * call)
        d['T'] = clamp(d['T'] + DT * (P['r_trust'] * inv * (1 - d['T']) * (1 - d['F']) ** 2 - P['l_trust'] * press * d['T']))
        d['lastvoice'], d['lastdoor'], d['lasthand'] = w['voice'], w['door'], w['hand']
        F, T, C, S = d['F'], d['T'], d['C'], d['state']
        # ---------- utilities ----------
        room = clamp((P['x_edge'] - d['x']) / P['room_w'])
        U = {}
        U['watch'] = 0.35 + 0.6 * C * (1 - F)
        U['retreat'] = press * (0.6 + F) * room
        U['refuse'] = press * (0.6 + F) * (1 - room) * 1.2 + 0.4 * reach * (1 - room)
        if S == 'refuse':
            U['refuse'] = max(U['refuse'], P['sulk0'] + P['sulk1'] * F)
        clear = d['m_door'] > 0.5 and d['m_sit'] > 0.5
        U['approach'] = P['a_app'] * (T - P['theta_T']) + 0.35 - 2 * F if (clear and (S == 'approach' or d['x'] > P['goal'] + 0.1)) else -1.0
        arrived = S == 'approach' and d['x'] - P['goal'] < P['arrive'] and abs(d['v']) < 0.12
        U['lie_down'] = 2.0 if arrived else (0.8 + 0.4 * T - 2 * press if S == 'lie_down' else -1.0)
        u_cross = T - P['W_inside'] if d['x'] - P['goal'] < 0.05 else None
        # ---------- choice: priorities, hysteresis, action windows ----------
        dwelt = t - d['since'] >= DWELL[S]
        best, bu = S, U[S] + P['hyst']
        for s in STATES:
            if s == S:
                continue
            if not dwelt and s not in DANGER:
                continue
            if U[s] > bu:
                best, bu = s, U[s]
        if best != S:
            why = {'retreat': f'pressure {press:.2f} x fear {F:.2f}, room behind {room:.2f}: backs away',
                   'refuse': f'pressure {press:.2f}, fear {F:.2f}, no room behind ({room:.2f}): turns its back',
                   'watch': f'curiosity {C:.2f} over fear {F:.2f}: looks',
                   'approach': f'trust {T:.2f} >= {P["theta_T"]}, fear {F:.2f}, door and sitting seen: comes, head low',
                   'lie_down': f'at the sill x={d["x"]:.3f}: lies across it'}[best]
            if S == 'retreat' and best == 'watch':
                why = f'the push stops (pressure {press:.2f}): watches'
            events.append({'t': round(t, 3), 'i': i, 'e': 'transition', 'from': S, 'to': best, 'why': why,
                           'U': {k2: round(v2, 3) for k2, v2 in U.items()}, 'x': round(d['x'], 3)})
            d['state'], d['since'], S = best, t, best
        ts = t - d['since']
        # ---------- locomotion ----------
        vt = 0.0
        if S == 'retreat':
            vt = P['v_ret'] * clamp(press * (0.6 + F)) * room
        elif S == 'approach':
            vt = -min(P['v0'] + P['v1'] * clamp((T - P['theta_T']) / (1 - P['theta_T'])), P['k_brake'] * max(0.0, d['x'] - P['goal']) + 0.02)
        d['v'] += clamp(vt - d['v'], -P['acc'] * DT, P['acc'] * DT)
        d['x'] += d['v'] * DT
        if d['x'] < P['goal']:
            d['x'], d['v'] = P['goal'], 0.0
        # ---------- the body layer (fast head, slow body) ----------
        want = math.pi if S == 'refuse' else 0.0
        # sub-states and their action windows
        sub = ''
        if S == 'refuse':
            sub = 'turn' if ts < 1.0 else 'sulk'
        if S == 'lie_down':
            sub = 'settle' if ts < 1.0 else ('look_in' if C > P['theta_look'] else 'rest')
        lie_t = 0.0
        if S == 'refuse' and ts > 1.0:
            lie_t = 1.0
        if S == 'lie_down':
            lie_t = 1.0
        if S == 'watch' and d['lie'] > 0.05 and ts < 0.22:
            lie_t = d['lie']                                  # window: head first, body stays down
        d['lie'] = ease(d['lie'], lie_t, 0.28 if lie_t > d['lie'] else 0.2)
        # head: answers within a tenth of a second, up to 150 deg over the shoulder
        hy_t = clamp(want - d['psi'], -2.6, 2.6)
        d['hy'] = ease(d['hy'], hy_t, 0.09)
        # body: turns only when up; turning toward the camera side (psi rises 0 -> pi through +z)
        upf = clamp(1 - d['lie'] * 8.0)                   # stands up first, then turns: no turning while folded
        dpsi = want - d['psi']
        rate = 4.2 * upf * DT
        step = clamp(dpsi * 0.18 + math.copysign(0.035, dpsi) if abs(dpsi) > 1e-3 else 0, -rate, rate)
        if abs(dpsi) < 0.01:
            step = dpsi
        d['psi'] += step
        d['hy'] = clamp(d['hy'] - step, -2.6, 2.6)            # the head keeps its world aim while the body turns under it
        # posture
        cr_t = clamp(0.08 + 0.8 * press * (0.5 + F) + 0.25 * F) if S in ('retreat', 'refuse', 'watch') else (0.14 if S == 'approach' else 0.05)
        d['crouch'] = ease(d['crouch'], cr_t, 0.18)
        rest_t = 0.0
        if d['lie'] > 0.8 and ((S == 'refuse' and ts > 1.8) or (S == 'lie_down' and sub == 'rest' and ts > 1.6)):
            rest_t = 1.0
        d['rest'] = ease(d['rest'], rest_t, 0.3)
        look_t = 1.0 if sub == 'look_in' else 0.0
        d['look'] = ease(d['look'], look_t, 0.22)
        head_t = {'watch': 0.9, 'retreat': 0.45, 'refuse': 0.5, 'approach': 0.22, 'lie_down': 0.6}[S] - 0.15 * F
        d['head'] = ease(d['head'], head_t, 0.2)
        tail_t = clamp(0.25 + 1.1 * F + 0.4 * press, 0, 1.35) if S != 'approach' else 0.55
        if S == 'lie_down':
            tail_t = 0.3
        d['tail'] = ease(d['tail'], tail_t, 0.25)
        wag = (0.25 * T if S in ('approach', 'lie_down') else 0.06 * T) * (1 - F)
        if S == 'lie_down' and sub == 'rest':
            wag *= 0.4
        d['wagph'] += DT * 2 * math.pi * (1.6 + 1.5 * T)
        d['ear'] = ease(d['ear'], clamp(0.45 + 0.6 * C + (0.3 if S == 'watch' else 0) - 0.7 * F), 0.15)
        d['phase'] += (abs(d['v']) * DT + abs(step) * 0.22) / 0.62
        frames.append({'i': i, 't': round(t, 4), 'state': S, 'sub': sub, 'x': round(d['x'], 4), 'v': round(d['v'], 4),
                       'drives': {'fear': round(F, 4), 'trust': round(T, 4), 'curiosity': round(C, 4), 'pressed_memory': round(d['M'], 3), 'pressure': round(press, 4), 'invitation': round(inv, 4)},
                       'percept': {'vis': round(vis, 3), 'sit_seen': round(d['m_sit'], 3), 'door_seen': round(d['m_door'], 3), 'low_seen': round(d['m_low'], 3), 'reach_seen': round(reach, 3), 'soft_heard': round(d['soft'], 3), 'call': call},
                       'U': {k2: round(v2, 3) for k2, v2 in U.items()}, 'U_cross': None if u_cross is None else round(u_cross, 3),
                       'body': {'psi': round(d['psi'], 4), 'head_yaw': round(d['hy'], 4), 'lie': round(d['lie'], 4), 'rest': round(d['rest'], 4), 'look': round(d['look'], 4),
                                'crouch': round(d['crouch'], 4), 'head': round(d['head'], 4), 'tail': round(d['tail'], 4), 'wag': round(wag * math.sin(d['wagph']), 4),
                                'ear': round(d['ear'], 4), 'phase': round(d['phase'], 4), 'moving': round(clamp(abs(d['v']) / 0.12 + abs(step) * 6), 3)},
                       'world': w0})
    return frames, events


def onsets(frames):
    """the first frame of each scored choice, as the machine decided it"""
    want = [('watch', 'retreat', 1.0), ('retreat', 'watch', 2.333), ('watch', 'refuse', 3.417), ('refuse', 'watch', 7.458),
            ('watch', 'approach', 14.708), ('approach', 'lie_down', 23.792)]
    out, k0 = [], 1
    for a, b, ts in want:
        hit = None
        for k in range(k0, len(frames)):
            if frames[k - 1]['state'] == a and frames[k]['state'] == b:
                hit, k0 = frames[k]['t'], k + 1; break
        out.append({'from': a, 'to': b, 'score': ts, 'machine': hit, 'dt': None if hit is None else round(hit - ts, 3)})
    look = next((f['t'] for f in frames if f['sub'] == 'look_in'), None)
    out.append({'from': 'lie_down.rest', 'to': 'lie_down.look_in', 'score': 26.4, 'machine': look, 'dt': None if look is None else round(look - 26.4, 3)})
    back = next((f['t'] for f in frames if look is not None and f['t'] > look and f['sub'] == 'rest'), None)
    out.append({'from': 'lie_down.look_in', 'to': 'lie_down.rest', 'score': 28.1, 'machine': back, 'dt': None if back is None else round(back - 28.1, 3)})
    return out


if __name__ == '__main__':
    pf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'tuned.json')
    P = json.load(open(pf)) if os.path.exists(pf) else {}
    fr, ev = run(P)
    on = onsets(fr)
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    json.dump({'params': dict(PARAMS, **P), 'dwell': DWELL, 'frames': fr, 'events': ev, 'onsets': on}, open(os.path.join(HERE, 'cache', 'machine.json'), 'w'))
    for o in on:
        print(o)
    print('transitions:', [(e['t'], e['from'], e['to']) for e in ev if e['e'] == 'transition'])
