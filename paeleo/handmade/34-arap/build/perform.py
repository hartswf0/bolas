"""The control-handle artist's timeline: score frame -> which drawing, where, and its acting.

Writes build/cache/perform.json, one entry per scene frame (768). The dog's x is the score's x (metres); its acting
comes from the score's act channels; the turns are scheduled here (substitution keys bridged by ARAP).
Stepping: an event simulation of four paws; a planted paw never moves in the world.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import score, CACHE, N_SCENE, FPS, smoothstep

S = score()
F = S['frames']
NEUTRAL = {'FN': -0.289, 'FF': -0.175, 'HN': 0.226, 'HF': 0.102}     # paw centres in the dog frame (m), facing left
PAIR = {'FN': 'F', 'FF': 'F', 'HN': 'H', 'HF': 'H'}
T_SWING = 0.22

# the turn schedule (frame indices; 24 fps)
R_ON = 82           # 3.417 refuse
W_ON = 179          # 7.458 watch (turns back to look)


def view_for(i):
    """(view, mirror, extra) for frame i."""
    if R_ON <= i <= R_ON + 2:
        return 'P', False, {}
    if R_ON + 3 <= i <= R_ON + 5:
        return 'P', False, {'head_flip': True}
    if R_ON + 6 <= i <= R_ON + 10:
        u = (i - (R_ON + 6)) / 4.0
        return 'R0', False, {'sx': 1.35 - 0.35 * u, 'head_dx': -55 + 110 * u}
    if R_ON + 11 <= i < W_ON:
        k = i - (R_ON + 11)
        return 'P', True, {'fs': min(1.0, 0.72 + 0.1 * k)}
    if W_ON <= i <= W_ON + 18:
        return 'P', True, {'head_flip': True}
    if W_ON + 19 <= i <= W_ON + 25:
        u = (i - (W_ON + 19)) / 6.0
        return 'F0', False, {'sx': 1.3 - 0.3 * u}
    if i >= W_ON + 26:
        k = i - (W_ON + 26)
        return 'P', False, {'fs': min(1.0, 0.72 + 0.1 * k)}
    return 'P', False, {}


class Gait:
    def __init__(self, x0):
        self.legs = {L: dict(p=x0 + NEUTRAL[L], swing=None) for L in NEUTRAL}

    def reset(self, xb, sign=1):
        for L in self.legs:
            self.legs[L] = dict(p=xb + sign * NEUTRAL[L], swing=None)

    def step(self, t, xb, v, sign=1):
        out, lifts = {}, {}
        # finish / advance swings
        for L, s in self.legs.items():
            if s['swing']:
                t0, p0, p1 = s['swing']
                u = (t - t0) / T_SWING
                if u >= 1:
                    s['p'] = p1; s['swing'] = None
        swinging = [L for L, s in self.legs.items() if s['swing']]
        moving = abs(v) > 0.03
        d = np.sign(v) if moving else 0.0
        cands = []
        for L, s in self.legs.items():
            if s['swing']:
                continue
            neu = xb + sign * NEUTRAL[L]
            off = s['p'] - neu
            if moving and off * d < -0.09:
                cands.append((abs(off), L, neu + d * 0.09 + v * T_SWING))
            elif not moving and abs(off) > 0.05:
                cands.append((abs(off) * 0.5, L, neu))
        cands.sort(reverse=True)
        for lag, L, target in cands:
            busy = [M for M in self.legs if self.legs[M]['swing']]
            if len(busy) >= 2 or any(PAIR[M] == PAIR[L] for M in busy):
                continue
            if not moving and busy:
                continue
            self.legs[L]['swing'] = (t, self.legs[L]['p'], target)
        for L, s in self.legs.items():
            if s['swing']:
                t0, p0, p1 = s['swing']
                u = min(max((t - t0) / T_SWING, 0), 1)
                e = u * u * (3 - 2 * u)
                out[L] = p0 + (p1 - p0) * e
                lifts[L] = u
            else:
                out[L] = s['p']
                lifts[L] = 0.0
        return out, lifts


def person_for(t, fr):
    p = fr['person']
    # where she stands, in metres from the door plane (negative = inside)
    x = -0.35 + (-1.30 + 0.35) * smoothstep(5.4, 6.35, t)
    walk = smoothstep(5.4, 6.35, t)
    step_phase = walk * 3.0                # three short back-steps
    sit = float(p['sit'])
    lean = 0.0; sh = 0.05; el = 0.10; hand_a = 0.0
    if 1.0 <= t < 2.4:                     # first call: beckons twice
        u = (t - 1.0) / 1.4
        env = np.sin(np.pi * min(u * 1.6, 1.0)) if u < 0.62 else max(0.0, 1 - (u - 0.62) / 0.38)
        lean = 0.07 * env
        sh = 0.05 + 0.95 * env
        el = 0.25 + 1.0 * env * (0.5 + 0.5 * np.sin(2 * np.pi * 1.6 * (t - 1.0) - 1.2))
    reach = float(p['reach'])
    if reach > 0.01:
        lean = max(lean, 0.20 * reach)
        sh = max(sh, 0.05 + 1.40 * reach)
        el = 0.12 * reach + el * (1 - reach)
    if 3.35 <= t < 3.45:                    # the second call starts a beat before the reach
        lean = max(lean, 0.06)
    low = float(p['low'])
    if sit > 0.3:
        sh = sh * (1 - low) + 0.70 * low
        el = el * (1 - low) + 0.25 * low
        hand_a = -0.5 * low
    head_a = -0.12 if p['voice'] == 'soft' else (0.06 if p['voice'] == 'call' else 0.0)
    return dict(x=x, walk=walk, step_phase=step_phase, sit=sit, lean=lean, sh=sh, el=el, hand_a=hand_a,
                head_a=head_a, voice=p['voice'], hand=p['hand'], reach=reach, low=low)


def main():
    plan = []
    g = Gait(F[0]['dog']['x'])
    prev_view = None
    wph = 0.0
    for i in range(N_SCENE):
        fr = F[i]; t = fr['t']; dg = fr['dog']; a = dict(dg['act'])
        x = dg['x']
        xn = F[min(i + 1, N_SCENE - 1)]['dog']['x']; xp = F[max(i - 1, 0)]['dog']['x']
        v = (xn - xp) / (2.0 / FPS)
        view, mirror, extra = view_for(i)
        key = (view, mirror)
        sign = -1 if mirror else 1
        if key != prev_view:
            g.reset(x, sign)
        paws, lifts = g.step(t, x, v, sign)
        prev_view = key
        state = dg['state']
        head = float(a['head'])
        if state == 'approach':
            head = min(head, 0.22 + 0.68 * (1 - smoothstep(14.71, 15.05, t)))
        if state == 'refuse':
            head = min(head, 0.5)
        wag = float(a['wag'])
        wph += 2 * np.pi * 2.0 / FPS
        acts = dict(crouch=float(a['crouch']), lie=float(a['lie']), head=head, ear=float(a['ear']),
                    tail=float(a['tail']), wag=wag, wph=wph, rest=float(a['rest']), look=float(a['look']),
                    breath=4.0 * np.sin(2 * np.pi * t / 2.4) * (1 - min(1, abs(v) * 4)))
        if view == 'P' and extra.get('head_flip') and i >= W_ON:
            acts['head'] = max(head, 0.75)      # looking back over the shoulder, head up
            acts['ear'] = max(acts['ear'], 0.85)
        # paw centres in the dog's own frame (mm): world offset from the body, mirrored when facing right
        pl = {L: (sign * (paws[L] - x) * 1000.0, 18.0 + 45.0 * np.sin(np.pi * lifts[L])) for L in paws}
        plan.append(dict(i=i, t=t, state=state, x=x, v=v, view=view, mirror=mirror, extra=extra, acts=acts,
                         paws=pl, lifts=lifts, paws_world=paws, person=person_for(t, fr), door=fr['door'],
                         door_open=float(smoothstep(6.2, 7.3, t)), prompt=fr['prompt']))
    json.dump(plan, open(os.path.join(CACHE, 'perform.json'), 'w'))
    print('frames', len(plan))


if __name__ == '__main__':
    main()
