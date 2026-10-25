"""SEQUENCE OPTIMIZER: choose one drawing per frame by dynamic programming (Viterbi).
cost = sum_t  pose_distance(frame pose_t, drawing pose)  +  sum_t transition(drawing_{t-1} -> drawing_t)
transition(j -> k) = 0 if j == k else  SWITCH + KAPPA * pose_distance(drawing j, drawing k)
so the path holds drawings (no flicker) and turns pass through the drawn in-between views instead of jumping.
Then placement: walking drawings are pinned to the board their planted paws stand on (gait phase -> distance),
other drawings hold their spot while held.
python3 build/solve.py -> build/cache/path.json, proof/path.json"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLD = os.path.abspath(os.path.join(HERE, '..'))
BANK = json.load(open(os.path.join(FOLD, 'bank', 'bank.json')))
POSES = json.load(open(os.path.join(HERE, 'cache', 'poses.json')))
RATE = POSES['rate_rad_per_m']
NW = BANK['nwalk']

W_DOG = dict(yaw=2.0, lie=6.0, crouch=2.0, head=3.0, look=6.0, rest=3.0, ear=.5, tail=.35, moving=5.0, back=4.0, phase=3.0, wag=2.0, over=8.0, listen=2.5)
W_PER = dict(sit=6.0, reach=5.0, low=4.0, mouth=3.0, walk=6.0, phase=2.0)
SWITCH = dict(dog=.7, person=.9)
KAPPA = dict(dog=.15, person=.1)
DEF_DOG = dict(yaw=0, lie=0, crouch=0, head=.9, look=0, rest=0, ear=1, tail=.5, moving=0, back=0, phase=None, wag=0, over=0, listen=0)
DEF_PER = dict(sit=0, reach=0, low=0, mouth=0, walk=0, phase=None)


def dist_dog(f, q, parts=False):
    q = {**DEF_DOG, **q}
    c = {}
    dy = abs(((f['yaw'] - q['yaw']) + 180) % 360 - 180) / 45.0
    c['yaw'] = W_DOG['yaw'] * dy * dy
    for k in ('lie', 'crouch', 'head', 'look', 'rest', 'ear', 'moving', 'over', 'listen'):
        c[k] = W_DOG[k] * (f.get(k, DEF_DOG[k]) - q[k]) ** 2
    c['tail'] = W_DOG['tail'] * ((f['tail'] - q['tail']) / 1.35) ** 2
    mv = max(f['moving'], q['moving'])
    c['back'] = W_DOG['back'] * (f['back'] - q['back']) ** 2 * mv
    c['phase'] = 0.0
    if q['phase'] is not None and f.get('phase') is not None:
        c['phase'] = W_DOG['phase'] * (1 - math.cos(f['phase'] - q['phase'])) * min(1, f['moving'] * 1.5)
    c['wag'] = W_DOG['wag'] * (f.get('wag', 0) - q['wag']) ** 2 * (1 if q['look'] > .5 else 0)
    return c if parts else sum(c.values())


def dist_per(f, q):
    q = {**DEF_PER, **q}
    c = sum(W_PER[k] * (f.get(k, 0) - q[k]) ** 2 for k in ('sit', 'reach', 'low', 'mouth', 'walk'))
    if q['phase'] is not None and f.get('phase') is not None:
        c += W_PER['phase'] * (1 - math.cos(f['phase'] - q['phase'])) * f.get('walk', 0)
    return c


def viterbi(U, T):
    """U: frames x states data cost; T: states x states transition cost."""
    n, K = U.shape
    acc = U[0].copy(); bp = np.zeros((n, K), dtype=int)
    for t in range(1, n):
        m = acc[:, None] + T
        bp[t] = np.argmin(m, axis=0)
        acc = m[bp[t], np.arange(K)] + U[t]
    path = [int(np.argmin(acc))]
    for t in range(n - 1, 0, -1):
        path.append(int(bp[t][path[-1]]))
    return path[::-1], float(acc.min())


def solve():
    F = POSES['frames']
    dog_ids = [k for k, v in BANK['drawings'].items() if v['meta'].get('group') != 'person']
    per_ids = [k for k, v in BANK['drawings'].items() if v['meta'].get('group') == 'person']
    # person walk phase from its own distance
    sp = 0.0
    for i, f in enumerate(F):
        if i: sp += abs(f['person']['x'] - F[i - 1]['person']['x'])
        f['person']['s'] = sp
        f['person']['phase'] = (sp / .64) * 2 * math.pi % (2 * math.pi)   # two steps per 0.64 m
    U = np.array([[dist_dog(f['dog'], BANK['drawings'][k]['pose']) for k in dog_ids] for f in F])
    Tm = np.array([[0 if a == b else SWITCH['dog'] + KAPPA['dog'] * dist_dog({**DEF_DOG, **{kk: vv for kk, vv in BANK['drawings'][a]['pose'].items() if vv is not None}, 'moving': BANK['drawings'][a]['pose'].get('moving', 0)}, BANK['drawings'][b]['pose'])
                    for b in dog_ids] for a in dog_ids])
    grp = [BANK['drawings'][k]['meta'].get('group') for k in dog_ids]
    for a in range(len(dog_ids)):
        for b in range(len(dog_ids)):
            if {grp[a], grp[b]} == {'walk', 'back'}:
                Tm[a, b] += 100.0          # never step from backing away straight into walking forward
    dpath, dcost = viterbi(U, Tm)
    Up = np.array([[dist_per(f['person'], BANK['drawings'][k]['pose']) for k in per_ids] for f in F])
    Tp = np.array([[0 if a == b else SWITCH['person'] + KAPPA['person'] * dist_per({**DEF_PER, **BANK['drawings'][a]['pose'], 'phase': BANK['drawings'][a]['pose'].get('phase')}, BANK['drawings'][b]['pose'])
                    for b in per_ids] for a in per_ids])
    ppath, pcost = viterbi(Up, Tp)

    # placement
    S_ = [f['s'] for f in F]; X_ = [f['x'] for f in F]

    def x_at_s(s, i0):
        # x as a function of travelled distance, searched near frame i0 (s is monotone)
        j = i0
        while j > 0 and S_[j] > s: j -= 1
        while j < len(S_) - 1 and S_[j + 1] < s: j += 1
        if j >= len(S_) - 1: return X_[-1]
        s0, s1 = S_[j], S_[j + 1]
        if s1 - s0 < 1e-9: return X_[j]
        u = max(0, min(1, (s - s0) / (s1 - s0)))
        return X_[j] + (X_[j + 1] - X_[j]) * u

    frames = []
    prev = None
    S = BANK['S']
    FOOTED = ('stand', 'walk', 'back')

    def planted(k):
        m = BANK['drawings'][k]['meta']
        if m.get('group') not in FOOTED or 'feet' not in m: return {}
        return {leg: v[0] for leg, v in m['feet'].items() if abs(v[1]) < .5}

    def match(prev_k, prev_x, k):
        a, b = planted(prev_k), planted(k)
        legs = [l for l in a if l in b]
        if not legs: return None
        return sum((prev_x * S + a[l]) - b[l] for l in legs) / len(legs) / S

    seg_off = 0.0
    for i, f in enumerate(F):
        k = dog_ids[dpath[i]]; d = BANK['drawings'][k]
        g = d['meta'].get('gait')
        pg_prev = prev and BANK['drawings'][prev['dog']]['meta'].get('gait')
        if g:
            phk = 2 * math.pi * g['k'] / g['n']
            phf = f['s'] * RATE
            dphi = ((phk - phf) + math.pi) % (2 * math.pi) - math.pi
            xp0 = x_at_s(f['s'] + dphi / RATE, i)
            if prev and not pg_prev:
                mo = match(prev['dog'], prev['x_place'], k)
                seg_off = 0.0   # a walk starts where the score is: its first drawing takes the first step
            xp = xp0 + seg_off
        elif prev and prev['dog'] == k:
            xp = prev['x_place']           # a held drawing keeps its spot: nothing slides
        else:
            mo = match(prev['dog'], prev['x_place'], k) if prev else None
            if mo is not None and abs(mo - f['x']) < .12:
                xp = mo                    # the new drawing stands where the last one's paws were
            elif prev and abs(prev['x_place'] - f['x']) < .15:
                xp = prev['x_place']
            else:
                xp = f['x']
        pk = per_ids[ppath[i]]
        pg = BANK['drawings'][pk]['meta'].get('gait')
        if pg:
            sp_ = f['person']['s']; rate_p = 2 * math.pi / .64
            dphi = ((2 * math.pi * pg['k'] / pg['n'] - sp_ * rate_p) + math.pi) % (2 * math.pi) - math.pi
            ss = sp_ + dphi / rate_p
            # person x is monotone in its own distance: x = x0 - s
            pxp = F[0]['person']['x'] - ss
        else:
            pxp = f['person']['x']
        rec = {'i': f['i'], 't': f['t'], 'state': f['state'], 'x_score': f['x'], 'dog': k, 'x_place': round(xp, 5),
               'cost': round(float(U[i, dpath[i]]), 4), 'terms': {a: round(b, 3) for a, b in dist_dog(f['dog'], d['pose'], True).items() if b > .01},
               'person': pk, 'person_x': round(pxp, 5), 'pcost': round(float(Up[i, ppath[i]]), 4)}
        frames.append(rec); prev = rec
    # numeric invariant: a planted paw never slides on the boards, while a drawing is held or the gait cycle advances;
    # a paw may move only by being redrawn in a different place when the action changes (a step), reported separately
    slip = 0.0; slip_at = None; pop = 0.0; pop_at = None
    for a, b in zip(frames, frames[1:]):
        fa, fb = planted(a['dog']), planted(b['dog'])
        ga = BANK['drawings'][a['dog']]['meta'].get('gait'); gb = BANK['drawings'][b['dog']]['meta'].get('gait')
        for leg in fa:
            if leg in fb:
                dd = abs((b['x_place'] * S + fb[leg]) - (a['x_place'] * S + fa[leg]))
                if a['dog'] == b['dog'] or (ga and gb):
                    if dd > slip: slip, slip_at = dd, b['t']
                elif dd > pop: pop, pop_at = dd, b['t']
    switches = sum(1 for a, b in zip(frames, frames[1:]) if a['dog'] != b['dog'])
    holds = []
    run = 1
    for a, b in zip(frames, frames[1:]):
        if a['dog'] == b['dog']: run += 1
        else: holds.append(run); run = 1
    holds.append(run)
    summary = {'dog_cost': round(dcost, 3), 'person_cost': round(pcost, 3), 'switches': switches,
               'single_frame_holds': sum(1 for h in holds if h == 1), 'max_planted_slip_px': round(slip, 3), 'slip_at': slip_at, 'max_step_pop_px': round(pop, 3), 'pop_at': pop_at,
               'drawings_used': sorted(set(r['dog'] for r in frames)), 'unused': sorted(set(dog_ids) - set(r['dog'] for r in frames)),
               'weights': {'dog': W_DOG, 'person': W_PER, 'switch': SWITCH, 'kappa': KAPPA}}
    out = {'about': 'Decoded path: one drawing per scene frame, chosen by Viterbi over pose distance + transition penalty.',
           'summary': summary, 'frames': frames}
    json.dump(out, open(os.path.join(HERE, 'cache', 'path.json'), 'w'))
    json.dump(out, open(os.path.join(FOLD, 'proof', 'path.json'), 'w'), indent=0)
    print(json.dumps(summary, indent=1)[:1500])


if __name__ == '__main__':
    solve()
