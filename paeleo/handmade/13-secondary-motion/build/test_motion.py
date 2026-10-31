"""Numeric assertions the representation supports (the bar's measurable part), from build/cache/measure*.json.
They do not replace looking. Writes proof/assertions.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
M = json.load(open(os.path.join(C, 'measure.json')))
E = lambda key, a, b: [m['energy'][key] for m in M if a <= m['t'] <= b]
mx = lambda v: max(v) if v else 0
res = []
def check(name, ok, **kw): res.append({'name': name, 'ok': bool(ok), **kw})

# 1 follow-through settles after the body stops (lying down at 23.79; the primary pose is still from 24.55)
peak = mx(E('body', 23.8, 24.7)); after = mx(E('body', 25.0, 25.3))
check('coat settles after lying down: body-coat kinetic energy 25.0-25.3 s < 15% of its 23.8-24.7 s peak', after < 0.15 * peak, peak=round(peak, 2), after=round(after, 2))
# 2 follow-through lags onset: the fur energy peak comes after the primary onset of lying (23.79)
k = max(range(len(M)), key=lambda i: M[i]['energy']['body'] if 23.7 <= M[i]['t'] <= 24.8 else -1)
check('coat lags the body: fur energy peaks after the lying onset (23.79 s)', M[k]['t'] > 23.85, peak_t=M[k]['t'])
# 3 no endless idle oscillation: while the dog holds still in the last second and the wind is low, energy is small
end = mx(E('body', 31.5, 32.0)); check('no endless oscillation: body-coat energy 31.5-32 s < 25% of the lying peak', end < 0.25 * peak, end=round(end, 2))
# 4 the ears flick after each soft voice onset, not before (reaction 0.04-0.35 s after the onset)
for tv in (7.36, 10.36, 26.36):
    seg = [(m['t'], m['energy']['ears']) for m in M if tv - 0.3 <= m['t'] <= tv + 0.6]
    before = mx([e for t, e in seg if t < tv]); tp, ep = max([x for x in seg if x[0] <= tv + 0.35], key=lambda x: x[1])  # the flick's peak inside the reaction window (at 26.4 the ears are then lowered on purpose, a later, separate swing)
    check(f'ear flick follows the soft voice at {tv:.2f} s', tv + 0.04 <= tp <= tv + 0.35 and ep > 2 * max(before, 0.05), peak_t=tp, peak=round(ep, 2), before=round(before, 2))
# 5 the coat flattens on the refusal: fur tips sit closer to the body axis than while watching
def spread(a, b): v = [m['fur_radial'] for m in M if a <= m['t'] <= b]; return sum(v) / len(v)
sw, sr = spread(2.9, 3.35), spread(3.9, 4.2)
check('coat flattens on the refusal: mean fur-tip distance from the spine axis drops', sr < sw, watching=round(sw, 4), refusing=round(sr, 4))
# 6 the tail tucks on the refusal: tail tip lower than while watching
tw = sum(m['tail_tip'][1] for m in M if 2.9 <= m['t'] <= 3.35) / sum(1 for m in M if 2.9 <= m['t'] <= 3.35)
tr = sum(m['tail_tip'][1] for m in M if 3.9 <= m['t'] <= 4.2) / sum(1 for m in M if 3.9 <= m['t'] <= 4.2)
check('tail tucks on the refusal: tail tip lower than while watching', tr < tw - 0.05, watching=round(tw, 3), refusing=round(tr, 3))
# 7 comparison presets (if rendered): with no secondary motion the fur carries no energy of its own
for pre in ('none', 'generic'):
    p = os.path.join(C, f'measure-{pre}.json')
    if os.path.exists(p):
        N = json.load(open(p)); a = [m['fur_radial'] for m in N if 3.9 <= m['t'] <= 4.2]
        res.append({'name': f'preset {pre}: refusal fur spread (tuned {round(sr, 4)})', 'ok': True, 'value': round(sum(a) / len(a), 4)})
out = {'about': 'numeric assertions from the solver/mask measurements; perceptual judgment is the critic\'s', 'all_ok': all(r['ok'] for r in res), 'assertions': res}
os.makedirs(os.path.join(TOP, 'proof'), exist_ok=True)
json.dump(out, open(os.path.join(TOP, 'proof', 'assertions.json'), 'w'), indent=1)
for r in res: print('OK ' if r['ok'] else 'FAIL', r['name'], {k: v for k, v in r.items() if k not in ('name', 'ok')})
