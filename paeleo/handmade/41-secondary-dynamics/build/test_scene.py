"""Scene-level assertions for SCION 41's bar, on the solved scene and the measured render.
python3 build/test_scene.py   -> prints PASS/FAIL lines, writes proof/assertions.json (exit 1 on failure)

What is asserted (numerically, where the representation supports it):
  A1 every secondary part's energy decays when its sources stop (holds 12.5-14.2 s and 30-32 s)
  A2 momentum response begins after primary motion (tail tip and ears deviate only after the pose starts moving)
  A3 no interpenetration: tail vs floor/thighs/rump, scarf vs body/floor, dog vs the door jambs, belly vs boards
  A4 feet do not slide while planted
  A5 head below the line of the back for the whole approach
  A6 the six choices measured from the render itself (not from the score labels), within 0.25 s
  A7 the soft voice is >= 6 dB quieter than the calls and above the room tone
And a reference comparison of the damping presets (none / tuned / loose): settle time, tail overshoot, penetration.
Perceptual criticism is not replaced by any of this."""
import json, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
S = json.load(open(os.path.join(C, 'sim.json'))); TR = json.load(open(os.path.join(TOP, 'trace.json')))['frames']
LV = json.load(open(os.path.join(C, 'sound-levels.json')))
fails = 0; out = {}
def ok(key, cond, msg, val=None):
    global fails; print(('PASS ' if cond else 'FAIL ') + key + '  ' + msg); fails += 0 if cond else 1; out[key] = {'ok': bool(cond), 'msg': msg, 'value': val}
E = S['energy']; parts = ['tail', 'ears', 'tag', 'scarf', 'shrub', 'coat', 'door']
fi = lambda t: int(round(t * 24))
# A1
res = {}
for p in parts:
    peak = max(e[p] for e in E) or 1e-12
    h1 = max(e[p] for e in E[fi(12.5):fi(14.2)]); h2 = max(e[p] for e in E[fi(30.0):])
    res[p] = {'peak': peak, 'hold_12.5_14.2': h1, 'hold_30_32': h2, 'ratio': max(h1, h2) / peak}
ok('A1_energy_decays', all(r['ratio'] < 1e-3 for r in res.values()), 'max hold energy / peak per part: ' + ', '.join(f"{k} {v['ratio']:.1e}" for k, v in res.items()), res)
# A2: response after primary onset, for three primary onsets
def dev(f, a, b):
    return math.dist(f['dog'][a][-1], f['dog'][b][-1])
lags = {}
for name, t0 in (('retreat', 1.0), ('refuse turn', 3.417), ('approach', 14.708)):
    i0 = fi(t0); base = max(dev(S['frames'][i], 'tail', 'tailPose') for i in range(i0 - 12, i0))
    first = next((i for i in range(i0 - 12, i0 + 48) if dev(S['frames'][i], 'tail', 'tailPose') > base + 0.01), None)
    lags[name] = None if first is None else (first - i0)
ok('A2_response_after_primary', all(v is not None and v >= 1 for v in lags.values()), 'tail-tip deviation (>1 cm over rest) begins this many frames after the primary onset: ' + str(lags), lags)
# A3
G = S['gaps']; mins = {k: min(g[k] for g in G) for k in ('tail', 'scarf', 'jamb', 'body_floor')}
ok('A3_no_interpenetration', mins['tail'] >= -0.002 and mins['scarf'] >= -0.003 and mins['jamb'] > 0 and mins['body_floor'] >= 0, 'min signed gaps (m; collision radii included): ' + str({k: round(v, 4) for k, v in mins.items()}), mins)
# A4
ok('A4_feet_planted', S['foot_slide_max'] < 0.005, f"largest planted-foot movement between frames {S['foot_slide_max'] * 1000:.1f} mm", S['foot_slide_max'])
# A5
ap = [m for m, f in zip(S['meas'], TR) if f['state'] == 'approach']
ok('A5_head_low_on_approach', all(m['head_below_back'] for m in ap), f"head top below back top in {sum(m['head_below_back'] for m in ap)}/{len(ap)} approach frames; worst margin {min(m['back_top'] - m['head_top'] for m in ap) * 100:.1f} cm", None)
# A6: choices measured from the render
X = [f['x_world_measured'] for f in TR]; T = [f['t'] for f in TR]; FA = [f['facing'] for f in TR]; PO = [f['posture'] for f in TR]
def first(pred, start):
    return next((T[i] for i in range(fi(start), len(TR)) if pred(i)), None)
# visible onset of each choice, measured on the drawn/solved body: travel choices = 2 cm of measured travel; posture and
# head choices = 25 % of the way from the value before the choice to the value after it
hx = [f['dog']['fwd'][0] for f in S['frames']]  # head direction along X: -1 points at the door, +1 away
hyH = [f['dog']['head'][1] for f in S['frames']]
def onset(series, t0, before, after, frac=0.25, lo=-0.6):
    v0, v1 = series[fi(t0 + before)], series[fi(t0 + after)]; thr = v0 + (v1 - v0) * frac
    return next((T[i] for i in range(fi(t0 + lo), len(series)) if (series[i] - thr) * (1 if v1 > v0 else -1) >= 0), None)
x10 = X[fi(0.8)]
m_retreat = first(lambda i: X[i] - x10 > 0.02, 0.5)
m_watch = onset(hyH, 2.333, -0.25, 0.8)             # the head comes up out of the cower to watch
m_refuse = onset(hx, 3.417, -0.3, 0.7)              # the head and body turn away from the door
m_turnback = onset(hx, 7.458, -0.3, 0.5)            # the head comes round toward the door
x14 = X[fi(14.3)]
m_approach = first(lambda i: x14 - X[i] > 0.02, 14.0)
m_lie = first(lambda i: PO[i].startswith('lying'), 22.0)
m_lookin = onset(hx, 26.4, -0.2, 0.9)               # the head turns in through the doorway
meas = {'retreat': (m_retreat, 1.0), 'watch': (m_watch, 2.333), 'refuse': (m_refuse, 3.417), 'turns back to look': (m_turnback, 7.458), 'approach': (m_approach, 14.708), 'lie down': (m_lie, 23.792), 'looks in': (m_lookin, 26.4)}
# the first frame of each new state shows the start of the act; a choice is "on time" if its visible onset is within 0.25 s
ok('A6_choices_measured_from_render', all(a is not None and abs(a - b) <= 0.25 for a, b in meas.values()), 'render-measured onset - score time (s): ' + ', '.join(f'{k} {a - b:+.2f}' if a is not None else f'{k} none' for k, (a, b) in meas.items()), {k: {'measured': a, 'score': b} for k, (a, b) in meas.items()})
# A7
ok('A7_voice_levels', LV['soft_below_calls_db'] >= 6 and LV['soft_above_room_db'] > 6, f"soft voice {LV['soft_below_calls_db']} dB below the calls, {LV['soft_above_room_db']} dB above the room tone", LV)
# reference comparison of presets
cmp = {}
for p in ('none', 'tuned', 'loose'):
    fn = os.path.join(C, 'sim.json' if p == 'tuned' else f'sim-{p}.json')
    if not os.path.exists(fn): continue
    s = json.load(open(fn)); g = s['gaps']
    # settle: time after a source stops until the part's secondary energy stays below 1e-4 (m^2/s^2 per kg);
    # swings: local maxima of that energy (each is one visible swing or rebound)
    En = s['energy']
    def settle(part, t0, t1):
        i0, i1 = fi(t0), fi(t1); last = max((i for i in range(i0, i1) if En[i][part] > 1e-4), default=i0 - 1); return round((last + 1 - i0) / 24, 2)
    def swings(part, t0, t1):
        e = [En[i][part] for i in range(fi(t0), fi(t1))]; return sum(1 for k in range(1, len(e) - 1) if e[k] > e[k - 1] and e[k] >= e[k + 1] and e[k] > 1e-3)
    cmp[p] = {'tail_settle_after_wag_s (28.5)': settle('tail', 28.5, 31.9), 'tail_swings_after_wag': swings('tail', 28.5, 31.9),
              'ears_settle_after_rise_s (8.7)': settle('ears', 8.7, 10.4), 'ears_swings_after_rise': swings('ears', 8.7, 10.4),
              'scarf_settle_after_sit_s (6.6)': settle('scarf', 6.6, 14.0), 'shrub_settle_after_leave_s (8.9)': settle('shrub', 8.9, 14.0), 'shrub_swings_after_leave': swings('shrub', 8.9, 14.0),
              'min_gap_tail_m': round(min(x['tail'] for x in g), 4), 'min_gap_scarf_m': round(min(x['scarf'] for x in g), 4),
              'tag_contacts': sum(1 for e in s['events'] if e['tag'] == 'tag' and e['speed'] > 0.25)}
print('preset comparison:', json.dumps(cmp, indent=1)); out['preset_comparison'] = cmp
json.dump(out, open(os.path.join(TOP, 'proof', 'assertions.json'), 'w'), indent=1)
print('FAILED', fails) if fails else print('all scene assertions pass'); sys.exit(1 if fails else 0)
