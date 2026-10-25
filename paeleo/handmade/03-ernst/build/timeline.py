"""SCION 03 Ernst · the improbable-world builder's timeline: from the score's decisions to the pose of every part.

The score decides (state, x, acting intentions); this file is where the operation answers it in this plate's language:
the dog's yaw passes through its face at every turn, its paws are set by the step solver, the lion leaves the person's
head for the keystone, the hand is pasted on large to reach and small to offer.  Writes build/cache/timeline.pkl.
"""
import json, os, pickle
import numpy as np
import dog as D
import person as PR
import gait
import sdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
R2D = 180 / np.pi; D2R = np.pi / 180


def ss(a, b, t):
    """smoothstep from a to b (a may be > b)."""
    if a == b:
        return float(t >= a)
    x = np.clip((t - a) / (b - a), 0, 1)
    return float(x * x * (3 - 2 * x))


def lerp(a, b, t):
    return a + (b - a) * t


T_REFUSE = 3.417; T_BACK = 7.458; T_APPROACH = 14.708; T_LIE = 23.792; T_COMEIN = 26.4


def dog_yaw(t, x):
    """the body's facing (deg).  180 = to the door, 0 = back turned; every turn passes 90 (the face to the viewer)."""
    if t < T_REFUSE:
        return 180.0
    if t < T_BACK + 0.03:
        return 180.0 - 180.0 * ss(T_REFUSE, T_REFUSE + 0.5, t)
    if t < 12:
        return 180.0 * ss(T_BACK + 0.03, T_BACK + 0.5, t)
    # coming to the sill it angles into the doorway (front half in, hind half out)
    return 180.0 + 27.0 * ss(1.2, 0.62, x) if t < T_LIE + 0.6 else 207.0


def head_world_yaw(t, body):
    """at the turn back (7.46) the head comes round first, over the shoulder on the viewer's side."""
    if T_BACK <= t < T_BACK + 1.0:
        return max(body, 178.0 * ss(T_BACK, T_BACK + 0.24, t))
    return None


def dog_z(t, x):
    s = ss(1.25, 0.62, x) if t < T_LIE + 0.6 else 1.0
    return sdf.ZD - 0.49 * s


def build():
    dog_p = []
    per_p = []
    # -- dog: posture parameters per frame ------------------------------------------------------------------------------
    for f in FR:
        t = f['t']; d = f['dog']; a = d['act']
        x = d['x']
        phi = dog_yaw(t, x)
        st = d['state']
        head = a['head']
        if st == 'approach':
            head = head - 0.27 * min(1.0, a['moving'] * 1.5 + 0.3)
        lie = a['lie']
        rest = a['rest']
        if T_BACK <= t < T_BACK + 1.0:
            rest = rest * (1 - ss(T_BACK, T_BACK + 0.12, t))
            head = max(head, lerp(a['head'], 0.85, ss(T_BACK, T_BACK + 0.2, t)))
        p = dict(t=t, i=f['i'], state=st, x=x, z=dog_z(t, x), phi=phi * D2R, lie=lie, crouch=a['crouch'],
                 head=head, rest=rest, ear=float(np.clip(a['ear'], 0, 1)), tail=a['tail'],
                 wag_ang=a['wag'] * 0.55 * np.sin(2 * np.pi * 2.3 * t), y=0.03 * ss(1.0, 0.7, x) * lie)
        p['breath'] = 0.004 * np.sin(2 * np.pi * (0.45 if lie > 0.5 else 0.6) * t)
        # while it waits (8.3-14.7 s) it is alive but undecided: an ear flicks at each soft word
        if st == 'watch' and t > 8.3:
            for t0 in (8.9, 10.5, 12.6, 13.9):
                p['ear'] = float(np.clip(p['ear'] - 0.5 * np.exp(-((t - t0) / 0.09) ** 2), 0, 1))
        dog_p.append(p)
    # gaze (yaw of the head relative to the body), from targets
    person_head_stand = np.array([-0.28, 1.62, 0.12])
    person_head_sit = np.array([-1.2, 1.25, 0.38])
    low_hand = np.array([-0.7, 0.4, 0.62])
    inside = np.array([-0.45, 0.35, -2.4])
    for p, f in zip(dog_p, FR):
        t = p['t']; a = f['dog']['act']
        F, S = D.frame(p['phi'])
        chest, _ = D.body_points(p)
        hpos = np.array([p['x'], 0.45, p['z']]) + F * 0.35

        def yaw_to(tg):
            g = tg - hpos
            return float(np.arctan2(g @ S, g @ F)), float(np.arctan2(g[1], np.hypot(g[0], g[2])))
        if t < T_REFUSE:
            yr, gp = yaw_to(person_head_stand)
        elif t < T_BACK:
            yr, gp = 0.0, 0.0
        elif t < T_APPROACH:
            yr, gp = yaw_to(person_head_sit)
        elif t < T_LIE:
            yr, gp = yaw_to(low_hand)
            yr *= 0.6
        else:
            y1, g1 = yaw_to(person_head_sit)
            y2, g2 = yaw_to(inside)
            w = float(np.clip(a['look'], 0, 1))
            yr = lerp(y1, y2, w); gp = lerp(g1, g2 * 0.2, w) * 0.5
            p['head'] = lerp(p['head'], min(p['head'], 0.75), w)
            yr *= (1 - a['rest'])
        hw = head_world_yaw(t, p['phi'] * R2D)
        if hw is not None:
            yr = (hw - p['phi'] * R2D) * D2R
            gp = 0.1
        p['yaw_rel'] = float(np.clip(yr, -125 * D2R, 125 * D2R))
        p['gaze_pitch'] = float(np.clip(gp, -0.3, 0.4)) * 0.6
    # feet: desired positions from the body, then the step solver
    desired = {k: np.zeros((N, 3)) for k in ('LF', 'RF', 'LH', 'RH')}
    for i, p in enumerate(dog_p):
        F, S = D.frame(p['phi'])
        root = np.array([p['x'], 0.0, p['z']])
        rp = D.rest_paws(p['lie'], p['crouch'])
        for k, v in rp.items():
            desired[k][i] = root + (F * v[0] + D.Y * v[1] + S * v[2]) * D.K
            desired[k][i][1] = v[1] * D.K + p['y']
    lie_arr = np.array([p['lie'] for p in dog_p])
    dlie = np.abs(np.gradient(lie_arr))
    # the gait clock: one stride per 0.54 m travelled, and per ~1.5 rad of turning (feet must walk the body round)
    xs = np.array([p['x'] for p in dog_p]); zs = np.array([p['z'] for p in dog_p]); ph = np.unwrap([p['phi'] for p in dog_p])
    step = np.hypot(np.gradient(xs), np.gradient(zs)) / 0.54 + np.abs(np.gradient(ph)) * 0.34 / 0.54
    step = step * (1 - np.clip(lie_arr * 1.3, 0, 1))
    clock = np.cumsum(step)
    speed = np.maximum(step * FPS, 1e-3)
    period = np.clip(1.0 / speed * FPS, 8, 40)

    dphi = np.abs(np.gradient(ph))
    free = np.convolve(dphi > 0.03, np.ones(9), 'same') > 0

    def thr_fn(i):
        return 0.03 if dlie[i] > 0.002 else 0.045
    pos, contact, events = gait.solve(desired, clock=clock, offsets={'LH': 0.0, 'LF': 0.25, 'RH': 0.5, 'RF': 0.75},
                                      period=period, swing=5, lift=0.055, thr_fn=thr_fn, settle=0.04,
                                      pairs=(('LF', 'LH'), ('RF', 'RH')), free=free,
                                      turn_pairs=(('LF', 'LH'), ('RF', 'RH')))
    for i, p in enumerate(dog_p):
        p['paws'] = {k: pos[k][i].copy() for k in pos}
        p['contact'] = {k: bool(contact[k][i]) for k in contact}
        nsw = sum(1 for k in contact if not contact[k][i])
        p['y'] = p['y'] - 0.006 * nsw * (1 - p['lie'])
    # -- person -----------------------------------------------------------------------------------------------------------
    for f in FR:
        t = f['t']; ps = f['person']
        walk = ss(5.4, 6.15, t)
        x = lerp(-0.28, -1.25, walk)
        z = lerp(0.12, 0.36, walk)
        sit = ss(6.0, 6.75, t)
        # facing: toward the dog; turns to walk left, turns back to sit facing the porch
        if t < 5.4:
            psi = 18.0
        elif t < 6.05:
            psi = lerp(18.0, 168.0, ss(5.4, 5.55, t))
        else:
            psi = lerp(168.0, 12.0, ss(6.0, 6.3, t))
        reach = ps['reach']; low = ps['low']; mouth = ps['mouth'] if ps['voice'] == 'call' else 0.0
        lean = 0.5 * reach + 0.1 * mouth + 0.6 * low * sit
        q = dict(t=t, x=x, z=z, psi=psi * D2R, sit=sit, lean=lean, reach=reach, low=low, mouth=mouth,
                 voice=ps['voice'], soft=ps['mouth'] if ps['voice'] == 'soft' else 0.0)
        per_p.append(q)
    # person's feet: desired, then the same step solver (a biped: the two feet may not both be in the air)
    pdes = {k: np.zeros((N, 3)) for k in ('L', 'R')}
    for i, q in enumerate(per_p):
        F, S = PR.frame(q['psi'])
        root = np.array([q['x'], 0.0, q['z']])
        for k, side in (('L', 1), ('R', -1)):
            v = np.array([lerp(0.04, 0.4, q['sit']), 0.0, 0.12 * side])
            pdes[k][i] = root + F * v[0] + S * v[2]
    pxs = np.array([q['x'] for q in per_p])
    pclock = np.cumsum(np.abs(np.gradient(pxs)) / 0.7 + np.abs(np.gradient(np.unwrap([q['psi'] for q in per_p]))) * 0.2 / 0.7)
    ppos, pcon, pev = gait.solve(pdes, clock=pclock, offsets={'L': 0.0, 'R': 0.5}, period=np.full(N, 14.0), swing=6, lift=0.08, settle=0.06, pairs=(('L', 'R'),))
    for i, q in enumerate(per_p):
        q['feet'] = {k: ppos[k][i].copy() for k in ppos}
        F, S = PR.frame(q['psi'])
        up = np.array([np.sin(q['lean']), np.cos(q['lean']), 0.0])
        pel = np.array([q['x'], lerp(0.95, 0.53, q['sit']), q['z']])
        chest = pel + (F * up[0] + PR.Y * up[1]) * 0.5
        # right hand (toward the dog): pointing down at the floor ("come here"), reaching, or offered low
        rest_h = pel + F * (0.06 + 0.25 * q['sit']) + PR.Y * (0.02 + 0.12 * q['sit']) - S * 0.23
        point = chest + F * 0.5 - PR.Y * 0.38 - S * 0.12
        reachp = chest + F * 0.6 + PR.Y * 0.02 - S * 0.1
        lowp = np.array([-0.6, 0.5, 0.62])
        call_w = np.clip(q['mouth'] / 0.6, 0, 1) * (1 - q['reach'])
        h = rest_h + (point - rest_h) * call_w
        h = h + (reachp - h) * q['reach']
        h = h + (lowp - h) * q['low'] * q['sit']
        q['hand'] = h
        q['hand2'] = None
    return dict(dog=dog_p, person=per_p, dog_events=events, person_events=pev)


def door_state(t):
    # round 2: the door is struck open by the lion landing in the keystone (6.05 s): it starts to swing on the knock
    x = float(np.clip((t - 6.07) / 0.9, 0, 1))
    o = 1 - (1 - x) ** 2.4                     # struck: fast at first, then slowing
    ang = lerp(0.06, 1.28, o)
    light = lerp(0.3, 1.0, ss(6.1, 6.8, t))
    return ang, light


def dusk(t):
    return 0.12 + 0.4 * t / 32.0


def lion_state(t, head_px, mouth):
    """the lion: on the person's head (pasted, cut margin shown) until 5.45, flies to the keystone, settles there
    (margin concealed).  Returns (fragment name, centre px, scale, rotation deg, margin alpha)."""
    key = (sdf.X0, sdf.project(np.array([0.0, 2.36, 0.06]))[1])
    if t < 5.45:
        name = 'lion_head'
        if mouth > 0.3 and int(t * 8) % 2 == 1:
            name = 'lion_head_b'
        c = (head_px[0] + 4 + 5 * mouth, head_px[1] - 6)
        return name, c, 0.42 * (1 + 0.07 * mouth), -6 * mouth, 1.0
    if t < 6.05:
        s = ss(5.45, 6.05, t)
        p0 = np.array([head_px[0] + 4, head_px[1] - 6]); p2 = np.array(key)
        p1 = (p0 + p2) / 2 + np.array([0, -90])
        c = (1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s * s * p2
        name = 'lion_head' if s < 0.5 else 'lion_mask'
        sc = lerp(0.42, 0.5, s) if name == 'lion_head' else 0.46
        return name, tuple(c), sc, 0.0, 1.0
    # it lands with a knock: a small drop and rebound
    bounce = 7.0 * np.exp(-(t - 6.05) * 14) * np.cos((t - 6.05) * 40) if t < 6.5 else 0.0
    return 'lion_mask', (key[0], key[1] + bounce), 0.46, 0.0, 1.0 - ss(6.05, 6.5, t)


if __name__ == '__main__':
    tl = build()
    pickle.dump(tl, open(os.path.join(HERE, 'cache', 'timeline.pkl'), 'wb'))
    print('dog steps', len(tl['dog_events']), 'person steps', len(tl['person_events']))


def mane_state(t):
    """the lion's mane on the dog: (scale, margin alpha, opacity) or None."""
    if t < 1.0:
        return None
    sc = 0.36 * (0.7 + 0.3 * ss(1.0, 1.12, t))                     # hackles up with the first call
    sc *= 1 - 0.1 * ss(7.6, 12.0, t) - 0.08 * ss(14.7, 23.0, t)     # they lie down as trust grows
    margin = 1.0 - ss(23.9, 24.9, t)                                 # the seam closes on the sill
    alpha = 1.0 - 0.18 * ss(23.9, 24.9, t)
    return sc, margin, alpha


def _voice_spans():
    spans = []
    cur = None
    for f in FR:
        v = f['person']['voice']
        if v != 'none' and cur is None:
            cur = [f['t'], f['t']]
        if v != 'none':
            cur[1] = f['t']
        if v == 'none' and cur is not None:
            spans.append(tuple(cur)); cur = None
    if cur:
        spans.append(tuple(cur))
    return spans


VOICE = _voice_spans()
PROMPT_T = {}
for _f in FR:
    if _f['prompt'] and _f['prompt'] not in PROMPT_T:
        PROMPT_T[_f['prompt']] = _f['t']


def caption_on(i):
    f = FR[i]; p = f['prompt']
    if not p:
        return False
    t = f['t']
    if t - PROMPT_T[p] < 2.4:
        return True
    return any(a - 0.8 <= t <= b + 0.5 for a, b in VOICE) and t >= PROMPT_T[p]


def caption(i):
    """round 2: a caption is shown when its circumstance is set, and again while its words are spoken; never in silence."""
    for k in range(i, max(-1, i - 8), -1):
        if caption_on(k):
            return FR[k]['prompt']
    return ''


def caption_alpha(i):
    on = [caption_on(k) for k in range(max(0, i - 7), i + 1)]
    # fade in over 8 frames when it begins, fade out over 8 after it ends
    if caption_on(i):
        n = 0
        for v in reversed(on):
            if not v:
                break
            n += 1
        return min(1.0, n / 8.0)
    n = 0
    for v in reversed(on):
        if v:
            break
        n += 1
    return max(0.0, 1.0 - n / 8.0)
