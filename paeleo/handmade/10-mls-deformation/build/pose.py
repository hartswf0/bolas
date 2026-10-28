"""SCION-10 · landmark placement: the score's acting intentions -> where the dog's handles go, frame by frame.

The score gives per frame: state, x along the porch, and act {turn, lie, crouch, ear, tail, wag, head, rest, look, moving}.
This file turns them into a pose (body centre, heading, curl of the hide's centre line, back heights, head place, ears, tail)
and walks the four paws with a foot-planting gait: a paw stays where it was put on the boards until the body has moved
too far from it, then it steps (diagonal pairs), so the hide's legs, not a slide, account for the travel.

Mapping (stated in method.md): porch x_world = x_score - 0.49 (the sill at score 0.56 puts the lying dog's chest in the door
frame and its hindquarters on the boards). y = 0 is the centre line of the doorway.
Writes cache/poses.json (per frame: pose parameters and the 3D target of every handle), cache/footfalls.json."""
import json, os, sys
import numpy as np

H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import dog

SCORE = json.load(open(os.path.join(H, '..', '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']; N = len(FR); FPS = 24
X_OFF = 0.49
Y_LINE = 0.12          # the dog's line along the porch, a little to the far side of the doorway's centre
PI = np.pi


def ss(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(arr, r):
    if r <= 0: return arr
    k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2); k /= k.sum()
    p = np.pad(arr, (3 * r, 3 * r), mode='edge')
    return np.convolve(p, k, mode='valid')


def channels():
    t = np.array([f['t'] for f in FR])
    g = lambda k: np.array([f['dog']['act'][k] for f in FR], float)
    x = np.array([f['dog']['x'] for f in FR])
    C = {'t': t, 'x': x - X_OFF}
    for k in ('lie', 'crouch', 'ear', 'tail', 'wag', 'head', 'rest', 'look', 'moving'):
        C[k] = smooth(g(k), 2)
    # heading: the refusal turn leads the score's own turn curve so the back is shown by 3.9 s (lesson of the first six);
    # turning back at 7.46 is led by the head (below), the body follows on the score's curve.
    p1 = ss(3.42, 4.10, t)                      # facing door (pi) -> facing the steps (2 pi), through facing the camera (3pi/2)
    turn = np.array([f['dog']['act']['turn'] for f in FR])
    p2 = 1 - ss(7.85, 8.85, t)                               # after 7.46: back toward the door (score's turn crosses 0 at 8.1)
    back = np.where(t < 7.4, p1, np.minimum(p1, p2))
    C['back'] = back                                        # 0 facing door, 1 back turned
    C['th'] = PI + PI * back
    C['curl'] = 1.3 * np.sin(PI * back) * np.where(t < 7.4, 1, -1)
    # head lead (rad, added to the body heading): before the turn away the head swings first; at 7.46 the head comes round
    lead1 = -0.0 + 0.9 * (ss(3.42, 3.75, t) - ss(3.9, 4.25, t))
    lead2 = -2.1 * (ss(7.46, 7.85, t) - ss(8.15, 8.95, t))
    C['lead'] = lead1 + lead2
    return C


def pose_at(i, C):
    t = C['t'][i]
    lie, cr, rest, look = C['lie'][i], C['crouch'][i], C['rest'][i], C['look'][i]
    th, curl = C['th'][i], C['curl'][i]
    # standing / crouched values
    zw_s = 0.56 - 0.17 * cr; zc_s = 0.53 - 0.21 * cr
    head = C['head'][i]
    hz_s = max(zw_s + (head - 0.75) * 0.85, 0.20)
    pitch_s = 0.22 + 0.8 * np.clip(0.75 - head, 0, 1)
    # lying (sphinx: chest up on the forelegs, hips down, flanks spread on the boards)
    zw_l, zc_l = 0.30, 0.21
    hz_l = max(0.28 + (min(head, 1.0) - 0.5) * 0.25 - 0.18 * rest, 0.10)
    pitch_l = 0.15 + 0.35 * rest - 0.2 * np.clip(head - 0.7, 0, 1)
    k = lie
    p = dict(th=th, curl=curl * (1 - 0.7 * k),
             zw=lerp(zw_s, zw_l, k), zc=lerp(zc_s, zc_l, k), depth=lerp(0.27 - 0.04 * cr, 0.29, k), spread=lerp(0.15, 0.20, k),
             head_z=lerp(hz_s, hz_l, k), head_pitch=lerp(pitch_s, pitch_l, k), ear=float(np.clip(C['ear'][i], 0, 1)),
             tail_el=lerp(0.6 - 1.5 * C['tail'][i], -0.3, k), knee=0.03 * (1 - k))
    p['tail_curl'] = lerp(-0.25 - 0.4 * np.clip(C['tail'][i] - 0.7, 0, 1), 0.1, k)

    # tail yaw: wag, and in the lie a sweep to the side
    p['tail_yaw'] = 0.55 * C['wag'][i] * np.sin(2 * PI * 2.1 * t) + 0.9 * k
    # head direction: body heading + curl at the neck + lead; lying, the head rests turned toward the person (left of the
    # dog when it faces the door, i.e. toward +y) until "come in", when it turns in through the door (look -> 0 offset)
    hy = th + curl * 0.38 + C['lead'][i]
    lying_late = ss(23.8, 24.6, t)
    toward_person = -0.0 + (-1.25) * lying_late * (1 - look) * (1 - 0.55 * ss(28.3, 29.3, t))
    # (heading pi - 1.25 points the muzzle toward +y, the person's side)
    hy = hy + toward_person
    p['head_yaw'] = hy
    p['neck_yaw'] = th + curl * 0.3 + 0.55 * (hy - th - curl * 0.3)
    p['neck_reach'] = lerp(0.30 + 0.06 * np.clip(0.7 - head, 0, 1), 0.27 + 0.08 * rest, k)
    return p


def home_paws(p, C2):
    """where the paws want to be, in the body frame (forward f, left l) of the centre C2."""
    f = np.array([np.cos(p['th']), np.sin(p['th'])]); l = np.array([-f[1], f[0]])
    k = p.get('lie_k', 0)
    out = {}
    for side, sg in (('L', 1), ('R', -1)):
        fs = lerp(np.array([0.22, 0.11]), np.array([0.50, 0.075]), k)
        hs = lerp(np.array([-0.27, 0.11]), np.array([-0.06, 0.25]), k)
        out[f'fpaw_{side}'] = C2 + f * fs[0] + l * sg * fs[1] + f * p['curl'] * 0.0
        out[f'hpaw_{side}'] = C2 + f * hs[0] + l * sg * hs[1]
    return out


def run():
    C = channels()
    poses, falls = [], []
    paws = None; swing = {}; last_step = {0: -1.0, 1: -2.0}
    names = ['fpaw_L', 'hpaw_R', 'fpaw_R', 'hpaw_L']
    pair = {'fpaw_L': 0, 'hpaw_R': 0, 'fpaw_R': 1, 'hpaw_L': 1}
    xs = C['x']
    vel = np.gradient(xs) * FPS
    for i in range(N):
        t = C['t'][i]
        p = pose_at(i, C)
        p['lie_k'] = float(C['lie'][i])
        bob = 0.012 * C['moving'][i] * np.sin(2 * (C['x'][i] * 2 * PI / 0.62))
        p['zw'] += bob; p['zc'] += bob
        cx = xs[i]
        p['cx'], p['cy'] = cx, Y_LINE
        home = home_paws(p, np.array([cx, Y_LINE]))
        if paws is None:
            paws = {n: np.r_[home[n], 0.0] for n in home}
        lead = np.array([vel[i], 0.0]) * 0.2
        th_rate = (C['th'][min(i + 1, N - 1)] - C['th'][max(i - 1, 0)]) * FPS / 2
        if p['lie_k'] > 0.25:
            # lying or getting up/down: the legs fold and unfold; the paws go with the body
            for n in home:
                paws[n] = np.r_[lerp(paws[n][:2], home[n], 0.35), 0.0]
            swing = {}
        else:
            busy = {pair[n] for n in swing}
            fast = abs(th_rate) > 1.0
            # the pair that stepped longest ago goes first, so the diagonals alternate
            order = sorted(names, key=lambda n: (last_step[pair[n]], pair[n]))
            for n in order:
                if n in swing: continue
                tgt = home[n] + lead
                err = np.linalg.norm(tgt - paws[n][:2])
                if err > (0.05 if fast else 0.075) and (fast or not busy or busy == {pair[n]}):
                    dur = 0.15 if fast else (0.30 if abs(vel[i]) < 0.5 else 0.24)
                    swing[n] = {'a': paws[n][:2].copy(), 't0': t, 't1': t + dur}
                    busy = busy | {pair[n]}
                    last_step[pair[n]] = t
            for n in list(swing):
                s = swing[n]
                u = np.clip((t - s['t0']) / (s['t1'] - s['t0']), 0, 1)
                tgt = home[n] + lead * 0.5
                e = u * u * (3 - 2 * u)
                paws[n] = np.r_[lerp(s['a'], tgt, e), 0.07 * np.sin(PI * u)]
                if u >= 1:
                    paws[n] = np.r_[tgt, 0.0]; del swing[n]
                    falls.append({'i': i, 't': round(float(t), 3), 'paw': n, 'x': round(float(tgt[0]), 3), 'y': round(float(tgt[1]), 3)})
        p['paws'] = {n: paws[n].copy() for n in paws}
        Q = dog.place(p)
        poses.append({'i': i, 't': round(float(t), 4), 'state': FR[i]['dog']['state'],
                      'pose': {k: (float(v) if not isinstance(v, dict) else {a: [round(float(c), 4) for c in b] for a, b in v.items()}) for k, v in p.items()},
                      'Q': np.round(Q, 4).tolist()})
    os.makedirs(os.path.join(H, 'cache'), exist_ok=True)
    json.dump({'names': dog.NAMES, 'src_uv': dog.P_SRC.round(4).tolist(), 'frames': poses}, open(os.path.join(H, 'cache', 'poses.json'), 'w'))
    json.dump(falls, open(os.path.join(H, 'cache', 'footfalls.json'), 'w'))
    return poses, falls


if __name__ == '__main__':
    P, F = run()
    print(len(P), 'poses', len(F), 'footfalls')
