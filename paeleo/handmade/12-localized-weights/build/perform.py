"""The performance: read the score per frame and turn the dog's acting state into rig poses (and the person's).
Timing is the score's; the swarm's choices are how each act becomes handle motion:
  - the turn is a yaw ripple along the handle groups: head leads, then the shoulders, then the hips;
  - at 7.458 the head comes round first, raised over the shoulder, while the body still lies facing away;
  - feet are planted: gait phase comes from distance actually travelled, not from a clock.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
X_OFFSET = -0.12          # my space: torso centre = score x - 0.12 m
STRIDE = 0.50
APPROACH_HEAD = 0.32
LOOK_YAW = 70.0
LEG_PHASE = {'hn': 0.0, 'fn': 0.25, 'hf': 0.5, 'ff': 0.75}


def smooth(e):
    e = np.clip(e, 0, 1)
    return e * e * (3 - 2 * e)


def series(key):
    return np.array([f['dog']['act'][key] for f in FR], float)


T = np.array([f['t'] for f in FR])
XS = np.array([f['dog']['x'] for f in FR])
TURN = series('turn')


def turn_at(t):
    return np.interp(t, T, TURN)


def phi_body(t):
    return (1 - turn_at(t)) / 2 * 180.0


# Yaw ripple schedule (seconds): each handle group swings through 180 degrees in 0.30 s, head first, then shoulders, then
# hips, so at no frame is the whole dog edge-on; mid-turn the dog is folded like a real U-turn seen from the side (head and
# tail on the same side). Onsets are placed on the score's choices: refuse 3.417, watch 7.458.
TURNS = [  # (direction +1 = turning away, onsets for head, front, rear)
    (+1, 3.42, 3.54, 3.54),
    (-1, 7.36, 8.00, 8.00),
]
TURN_DUR = 0.34
HEAD_TURN_DUR = 0.22    # the head comes round faster, so it is in clear profile while the body folds


def yaw_at(t):
    out = {}
    for gi, g in enumerate(('head', 'front', 'rear')):
        phi = 0.0
        dur = HEAD_TURN_DUR if (g == 'head' and t < 6) else TURN_DUR
        for d, *ons in TURNS:
            e = smooth((t - ons[gi]) / dur)
            phi = phi + 180.0 * e if d > 0 else phi - 180.0 * e
        out[g] = float(np.clip(phi, 0, 180))
    return out


VOICE = [f['person']['voice'] for f in FR]
WORDS = []          # (start, end, words, kind): the person's lines, where the score turns the voice on
for _i, _v in enumerate(VOICE):
    if _v != 'none' and (_i == 0 or VOICE[_i - 1] != _v):
        _j = _i
        while _j < len(VOICE) and VOICE[_j] == _v:
            _j += 1
        _a, _b = float(T[_i]), float(T[_j - 1] + 1 / FPS)
        if _v == 'call':
            WORDS.append((_a, _b, 'Come here.', 'call'))
        else:
            WORDS.append((_a, _b, 'Come in.' if _a > 20 else "It's all right.", 'soft'))


def dog_poses():
    poses = []
    dist = 0.0
    seg_dir = 1.0
    for i, f in enumerate(FR):
        a = f['dog']['act']; t = f['t']
        if i > 0:
            dx = XS[i] - XS[i - 1]
            dist += abs(dx)
            if abs(dx) > 1e-5:
                seg_dir = np.sign(dx)
        m = a['moving']
        paws = {}
        for leg, o in LEG_PHASE.items():
            u = (dist / STRIDE + o) % 1.0
            if u < 0.6:
                off = -seg_dir * STRIDE * (u / 0.6 - 0.5) * 0.6
                lift = 0.0
            else:
                s = (u - 0.6) / 0.4
                off = -seg_dir * STRIDE * 0.6 * (0.5 - smooth(s))
                lift = 0.07 * np.sin(np.pi * s)
            paws[leg] = (off * m, lift * m)
        yaw = yaw_at(t)
        # looking in: the head also turns a little away from the camera, into the depth of the room (ears part, muzzle
        # foreshortens), so the look reads as into the room, not up at the person
        yaw['head'] = yaw['head'] - LOOK_YAW * a['look']
        lookback = np.clip((yaw['front'] - yaw['head']) / 150.0, 0, 1)
        # the second look: after the head has come round, keep it level and raised until the body catches up
        head = a['head']; rest = a['rest']; lie = a['lie']
        crouch = a['crouch']
        look = a['look']
        if lookback > 0:
            rest = rest * (1 - lookback)
        # approach: head low (below the back) for the whole approach, as the brief asks
        cap = 1 - smooth((t - 14.70) / 0.45) * (1 - smooth((t - 23.80) / 0.5))
        head = min(head, APPROACH_HEAD + (1.5 - APPROACH_HEAD) * cap)
        # looking in: no lift toward the light; the score's head > 1 becomes reach, not rise
        if 26.2 <= t <= 28.8:      # looking in: the head stays low (no lift toward the hand); look = reach + yaw into the room
            head = min(head, 0.30)
        # breathing: calm when lying, quick when afraid
        rate = 0.32 + 0.9 * crouch
        breath = 0.006 * np.sin(2 * np.pi * rate * t) * (1 + lie)
        ear = a['ear']
        if lie > 0.5:                # lying: ears stay half up, never flattened into the skull line
            ear = max(ear, 0.68)
        poses.append({'x': XS[i] + X_OFFSET, 'yaw': yaw, 'lie': lie, 'crouch': crouch, 'head': head, 'rest': rest,
                      'look': look, 'ear': ear, 'tail': a['tail'], 'wag': a['wag'], 'wag_phase': 2 * np.pi * 2.3 * t,
                      'breath': breath, 'paws': paws, 'lookback': float(lookback), 'state': f['dog']['state'], 't': t, 'i': i})
    return poses


if __name__ == '__main__':
    P = dog_poses()
    for p in P[::24]:
        print(p['t'], p['state'], round(p['x'], 2), {k: round(v) for k, v in p['yaw'].items()}, round(p['lookback'], 2))
