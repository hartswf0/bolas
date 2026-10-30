"""Tune the dog's machine until its OWN decisions land on the score (+-0.25 s), and its pace matches the score's x.
The score's states are never fed to the machine; they are only the target of the error.
Coordinate descent over a few physical parameters of the dog. Writes tuned.json and cache/tune_log.json.
"""
import json, os, math
import machine as M

HERE = os.path.dirname(os.path.abspath(__file__))
sc, W = M.world_frames()
SX = [f['dog']['x'] for f in sc['frames']]
KEYS = {'r_trust': (0.15, 0.8), 'v0': (0.1, 0.45), 'v1': (0.05, 0.8), 'k_brake': (0.6, 4.0), 'l_cur': (0.1, 0.8),
        'theta_look': (0.3, 0.9), 'tau_press': (0.03, 0.2), 'v_ret': (0.3, 1.4), 'acc': (0.5, 3.0),
        'room_w': (0.4, 1.6), 'hyst': (0.02, 0.12)}


def cost(P):
    fr, _ = M.run(P, W)
    on = M.onsets(fr)
    c = 0.0
    for o in on:
        c += 25.0 if o['dt'] is None else (o['dt'] / 0.1) ** 2 + (o['dt'] / 0.12) ** 6
    # pace: approach and retreat positions against the score's x
    xs = [f['x'] for f in fr]
    c += sum((a - b) ** 2 for a, b in zip(xs, SX)) / len(xs) * 40
    return c, on


def main():
    P = {}
    if os.path.exists(os.path.join(HERE, 'tuned.json')):
        P = json.load(open(os.path.join(HERE, 'tuned.json')))
    base = {k: P.get(k, M.PARAMS[k]) for k in KEYS}
    best, on = cost(base)
    log = [{'round': 0, 'cost': round(best, 3), 'params': dict(base), 'onsets': on}]
    step = 0.25
    for rnd in range(1, 9):
        improved = False
        for k, (lo, hi) in KEYS.items():
            for sgn in (+1, -1):
                trial = dict(base)
                trial[k] = min(hi, max(lo, base[k] * (1 + sgn * step)))
                c, o = cost(trial)
                if c < best - 1e-6:
                    best, base, on, improved = c, trial, o, True
        log.append({'round': rnd, 'step': step, 'cost': round(best, 3), 'params': {k: round(v, 4) for k, v in base.items()},
                    'onsets': [(o['to'], o['dt']) for o in on]})
        print(rnd, round(best, 3), [(o['to'], o['dt']) for o in on])
        if not improved:
            step *= 0.5
            if step < 0.02:
                break
    json.dump({k: round(v, 4) for k, v in base.items()}, open(os.path.join(HERE, 'tuned.json'), 'w'), indent=1)
    json.dump(log, open(os.path.join(HERE, 'cache', 'tune_log.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
