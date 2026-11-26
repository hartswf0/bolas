"""SCION-LUCASFILM-1985 · the dope sheet. Every pose is keyed by hand, with the reason for it; in-betweens are Catmull-Rom splines
between keys. No motion capture, no procedural walk: the walk is a keyed cycle (contact, down, passing, up), laid down step by step.
Angles in degrees. Legs and arms: from straight down, forward positive. s: spine lean forward. n: neck. k*/e*: knee and elbow bend.
rot: the whole body about the hip (lying). face: the knight's visor, 0 frontal, 1 in profile toward Uncle Mesa. sw: sword out (0..1)."""
import math
Z = dict(s=0, n=0, tL=0, kL=0, tR=0, kR=0, aL=0, eL=0, aR=0, eR=0, rot=0, face=0, sw=0, crouch=0, b=54)
def P(**k): d = dict(Z); d.update(k); return d
LIB = {
 'stand':   P(s=2, tL=3, tR=-3, kL=4, kR=4, aL=-4, eL=8, aR=6, eR=12),
 'settle':  P(s=5, tL=6, tR=-4, kL=12, kR=6, aL=-2, eL=10, aR=10, eR=16),              # weight comes down after the stairs
 'aim':     P(s=-3, tL=10, tR=-12, kL=6, kR=4, aL=-14, eL=30, aR=88, eR=2),            # gun arm straight at the shoulder
 'recoil':  P(s=-7, tL=10, tR=-12, kL=8, kR=4, aL=-16, eL=34, aR=100, eR=12),
 'down':    P(s=0, rot=-88, tL=4, kL=6, tR=12, kR=14, aL=-8, eL=10, aR=16, eR=10),    # flat on his back, the hat knocked off
 'kneel':   P(s=30, tL=70, kL=100, tR=-10, kR=110, aL=20, eL=30, aR=20, eR=10),         # getting up: one knee, the hand pushes off the floor
 'sit':     P(s=20, n=14, tL=82, kL=88, tR=76, kR=84, aL=34, eL=40, aR=8, eR=14),   # forward, forearms toward the knees: done
 # a keyed walk: contact (front leg forward, heel down), down (weight on it, knee gives), passing, up
 'c1': P(s=4, tL=24, kL=4, tR=-22, kR=12, aL=16, eL=10, aR=-14, eR=16), 'd1': P(s=6, tL=18, kL=16, tR=-14, kR=30, aL=10, eL=12, aR=-8, eR=18),
 'p1': P(s=4, tL=2, kL=6, tR=12, kR=58, aL=0, eL=10, aR=2, eR=14),     'u1': P(s=3, tL=-12, kL=2, tR=24, kR=30, aL=-10, eL=10, aR=12, eR=14),
 # the knight
 'k_window': P(s=0, tL=2, tR=-2, kL=2, kR=2, aL=-4, eL=6, aR=-6, eR=8, face=0),
 'k_look':   P(s=0, n=4, tL=2, tR=-2, kL=2, kR=2, aL=-4, eL=6, aR=-6, eR=8, face=1),
 'k_crouch': P(s=26, n=6, tL=60, kL=96, tR=40, kR=100, aL=30, eL=30, aR=-30, eR=40, face=1, crouch=1),
 'k_air':    P(s=12, tL=50, kL=70, tR=-10, kR=60, aL=60, eL=20, aR=-50, eR=20, face=1),
 'k_land':   P(s=22, tL=40, kL=80, tR=-6, kR=74, aL=24, eL=40, aR=-20, eR=30, face=1, crouch=1),
 'k_stand':  P(s=4, tL=8, tR=-10, kL=8, kR=6, aL=-6, eL=20, aR=10, eR=60, face=1),
 'k_draw0':  P(s=6, tL=8, tR=-10, kL=8, kR=6, aL=-6, eL=20, aR=-30, eR=80, face=1, sw=0),   # hand at the hilt, across the body
 'k_guard':  P(s=6, tL=12, tR=-14, kL=10, kR=8, aL=-10, eL=30, aR=40, eR=50, face=1, sw=1),
 'k_raise':  P(s=-10, n=-4, tL=14, tR=-16, kL=8, kR=6, aL=-20, eL=40, aR=190, eR=30, face=1, sw=1),
 'k_strike': P(s=24, n=8, tL=30, tR=-24, kL=24, kR=8, aL=10, eL=20, aR=70, eR=0, face=1, sw=1, b=-30),
 'k_over':   P(s=10, tL=16, tR=-14, kL=14, kR=8, aL=-6, eL=24, aR=20, eR=20, face=1, sw=1, b=-20),
 'kc1': P(s=6, tL=22, kL=6, tR=-20, kR=12, aL=12, eL=20, aR=40, eR=50, face=1, sw=1), 'kd1': P(s=8, tL=16, kL=18, tR=-12, kR=26, aL=8, eL=22, aR=42, eR=50, face=1, sw=1),
 'kp1': P(s=6, tL=2, kL=6, tR=10, kR=54, aL=0, eL=20, aR=40, eR=50, face=1, sw=1),     'ku1': P(s=5, tL=-12, kL=2, tR=22, kR=28, aL=-8, eL=20, aR=38, eR=50, face=1, sw=1),
}
def mirror(p):  # the other half of a cycle: swap legs, swap arm swing (but not a held gun or sword arm)
    q = dict(p); q['tL'], q['tR'], q['kL'], q['kR'] = p['tR'], p['tL'], p['kR'], p['kL']; q['aL'] = -p['aL']
    return q
def cycle(t0, t1, period, names, hold_arms=None):
    """lay a keyed walk between t0 and t1: four keys per step, the second step mirrored"""
    keys, t, k = [], t0, 0
    while t < t1 - 1e-6:
        for j, nm in enumerate(names):
            tk = t + j * period / 8
            if tk >= t1: break
            p = LIB[nm] if k % 2 == 0 else mirror(LIB[nm])
            if hold_arms: p = dict(p, **{a: LIB[hold_arms][a] for a in ('aR', 'eR', 'aL', 'eL', 'sw', 'face', 'b')})
            keys.append((tk, p, f'walk {nm}{"" if k % 2 == 0 else "-mirror"}'))
        t += period / 2; k += 1
    return keys

def mesa_keys(sc):
    hits = [p['t'] for p in sc['pieces']]
    K = cycle(0.0, 2.85, 1.0, ['c1', 'd1', 'p1', 'u1'])  # down the steps and onto the floor, one step every half second
    K += [(3.0, LIB['settle'], 'arrives: the weight drops into the front knee'), (3.45, LIB['stand'], 'stands, looking up at the window'),
          (6.5, LIB['stand'], 'still: the knight has drawn'), (6.68, LIB['aim'], 'the six-shooter comes up in one move')]
    for h in hits[:1]: K += [(h, LIB['aim'], ''), (h + .06, LIB['recoil'], 'the shot'), (h + .22, LIB['aim'], '')]
    K += [(12.18, LIB['aim'], 'holds his ground'), (12.32, LIB['down'], 'the sword lands: he goes down flat'), (13.5, LIB['down'], 'lies there'),
          (13.85, LIB['kneel'], 'one knee, a hand on the floor'), (14.15, LIB['aim'], 'up, gun first')]
    K += cycle(14.1, 14.95, .9, ['c1', 'd1', 'p1', 'u1'], hold_arms='aim')   # backing away, aiming
    K += [(15.0, LIB['aim'], 'plants')]
    for h in hits[1:]: K += [(h, LIB['aim'], ''), (h + .06, LIB['recoil'], 'the shot'), (h + .22, LIB['aim'], '')]
    K += [(20.6, LIB['aim'], 'it is over'), (21.0, LIB['stand'], 'lowers the gun')]
    K += cycle(21.0, 21.85, .85, ['c1', 'd1', 'p1', 'u1'])
    K += [(21.9, LIB['stand'], 'turns at the step'), (22.12, LIB['sit'], 'sits on the lowest step'), (24.0, LIB['sit'], '')]
    return sorted(K, key=lambda k: k[0])

def knight_keys(sc):
    K = [(0.0, LIB['k_window'], 'held in the glass, frontal'), (2.98, LIB['k_window'], ''), (3.1, LIB['k_look'], 'turns its head to him'),
         (4.45, LIB['k_look'], ''), (4.5, LIB['k_crouch'], 'gathers'), (4.68, LIB['k_air'], 'out of the window'), (4.92, LIB['k_land'], 'lands, the weight goes deep'),
         (5.4, LIB['k_stand'], 'rises'), (5.95, LIB['k_draw0'], 'hand to the hilt'), (6.15, LIB['k_guard'], 'draws: the red blade comes across'), (7.95, LIB['k_guard'], '')]
    K += cycle(8.0, 11.5, .9, ['kc1', 'kd1', 'kp1', 'ku1'])
    K += [(11.55, LIB['k_guard'], 'stops in reach'), (11.95, LIB['k_raise'], 'winds up over the head'), (12.2, LIB['k_strike'], 'the cut, all its weight behind it'),
          (12.6, LIB['k_over'], 'stands over him'), (13.95, LIB['k_over'], '')]
    K += cycle(14.0, 19.45, 1.3, ['kc1', 'kd1', 'kp1', 'ku1'])   # broken: slower, it keeps walking
    K += [(19.5, LIB['k_guard'], 'gone to pieces')]
    return sorted(K, key=lambda k: k[0])

def sample(keys, t):
    """Catmull-Rom between the keys around t"""
    ts = [k[0] for k in keys]
    if t <= ts[0]: return dict(keys[0][1])
    if t >= ts[-1]: return dict(keys[-1][1])
    i = max(j for j in range(len(ts)) if ts[j] <= t); i1 = min(i + 1, len(ts) - 1)
    u = (t - ts[i]) / max(1e-6, ts[i1] - ts[i]); p0, p1, p2, p3 = keys[max(0, i - 1)][1], keys[i][1], keys[i1][1], keys[min(len(ts) - 1, i1 + 1)][1]
    out = {}
    for k in Z:
        a, b, c, d = p0[k], p1[k], p2[k], p3[k]
        out[k] = .5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
    return out
