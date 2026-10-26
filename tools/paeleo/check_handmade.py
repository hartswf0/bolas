"""The PAELEO invariant test for a handmade threshold: did the description survive the operation?
python3 tools/paeleo/check_handmade.py paeleo/handmade/<nn>-<slug>   (or several folders; writes invariants.json into each)

Reads the swarm's trace.json (what its dog did, measured from its own render) against score/threshold-score.json:
  I1 choices    each of the six choices appears within ±0.25 s of the score's time (first frame in the new state)
  I2 threshold  the dog never goes inside the house (x_score ≥ the sill) and ends at the sill
  I3 direction  the dog's motion follows the score: correlation of its measured position with the score's x at least 0.9 in
                magnitude. The position is x_world_measured when the trace has it (a film whose camera moves), else x_screen
  I4 refusal    while the score refuses, the trace has the dog's back turned (facing opposite its facing while watching)
These are structural checks of the trace the builder reports; they do not judge whether the choices read on screen.
That is the critic's job."""
import json, os, sys

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCORE = json.load(open(os.path.join(R, 'paeleo/handmade/score/threshold-score.json')))
SILL = SCORE['places']['sill']


def corr(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    sa = sum((x - ma) ** 2 for x in a) ** .5; sb = sum((y - mb) ** 2 for y in b) ** .5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else 0.0


def check(folder):
    tr = json.load(open(os.path.join(folder, 'trace.json')))
    fr = tr['frames'] if isinstance(tr, dict) and 'frames' in tr else tr
    res = {}
    # I1: choices
    got = []
    for c in SCORE['choices']:
        hit = next((f for f in fr if f['t'] >= c['t'] - .5 and f.get('state') == c['to']), None)
        dt = None if hit is None else round(hit['t'] - c['t'], 3)
        got.append({'t': c['t'], 'to': c['to'], 'found_at': None if hit is None else hit['t'], 'dt': dt, 'ok': dt is not None and abs(dt) <= .25})
    res['I1_choices'] = {'ok': all(g['ok'] for g in got), 'choices': got}
    # I2: threshold
    xs = [f['x_score'] for f in fr if f.get('x_score') is not None]
    res['I2_threshold'] = {'ok': bool(xs) and min(xs) >= SILL - 1e-3 and abs(xs[-1] - SILL) < .1, 'min_x': min(xs) if xs else None, 'end_x': xs[-1] if xs else None}
    # I3: direction
    sc = {f['i']: f['dog']['x'] for f in SCORE['frames']}
    key = 'x_world_measured' if any(f.get('x_world_measured') is not None for f in fr) else 'x_screen'
    pairs = [(f[key], sc[f['i']]) for f in fr if f.get(key) is not None and f['i'] in sc]
    r = corr([p[0] for p in pairs], [p[1] for p in pairs]) if len(pairs) > 10 else 0
    res['I3_direction'] = {'ok': abs(r) >= .9, 'r': round(r, 3), 'n': len(pairs), 'measure': key}
    # I4: refusal shows the back
    watch = [f.get('facing') for f in fr if f.get('state') == 'watch' and f.get('facing') is not None]
    ref = [f.get('facing') for f in fr if f.get('state') == 'refuse' and f.get('facing') is not None]
    fw = max(set(watch), key=watch.count) if watch else None
    turned = sum(1 for v in ref if v != fw) / len(ref) if ref else 0
    res['I4_refusal'] = {'ok': turned >= .8, 'share_turned': round(turned, 3), 'facing_when_watching': fw}
    res['all_ok'] = all(v['ok'] for k, v in res.items() if k.startswith('I'))
    json.dump(res, open(os.path.join(folder, 'invariants.json'), 'w'), indent=1)
    return res


if __name__ == '__main__':
    for f in sys.argv[1:]:
        r = check(f)
        print(os.path.basename(f.rstrip('/')), 'ALL OK' if r['all_ok'] else 'FAILS', {k: v['ok'] for k, v in r.items() if k.startswith('I')})
