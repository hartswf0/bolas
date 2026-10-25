"""The exposure sheet (dope sheet). Reads the score and the voice chart; writes, per exposure, where every card lies.
The camera interval is the primitive: exposures are shot on twos (each held 2 frames), re-phased so that a choice
starts on its own exposure, and held as long as nothing on the table is touched. Output: ../xsheet.json"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from table import PIECES, pin
from world import xs, K

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
F = SCORE['frames']
VOICE = json.load(open(os.path.join(HERE, 'cache', 'voice_chart.json')))
N = 768

# choice frames (first frame in the new state) and other events that must start their own exposure
def first(state, after):
    return next(f['i'] for f in F if f['t'] >= after and f['dog']['state'] == state)
CH = {'retreat': first('retreat', .9), 'watch1': first('watch', 2.2), 'refuse': first('refuse', 3.3),
      'watch2': first('watch', 7.3), 'approach': first('approach', 14.6), 'lie': first('lie_down', 23.7)}
LOOK_IN = 634       # 26.42 s: hears "come in" (the soft voice starts at 26.4) -> the head card is replaced
LOOK_OUT = 674      # 28.08 s: the score's look falls back (0.88 at 28.0, 0.18 at 28.25)
DOOR = [(149, 'door_22', .35), (151, 'door_20', .6), (153, 'door_edge', 1.0)]
FORCED = sorted(set(list(CH.values()) + [LOOK_IN, LOOK_OUT, 149, 86, 194, 200]))


def exposure_starts():
    starts, f = [], 0
    while f < N:
        starts.append(f)
        nxt = f + 2
        later = [b for b in FORCED if f < b <= nxt + 1]
        if later and later[0] == nxt + 1:      # a forced boundary one frame past the twos: hold this one for three
            nxt = later[0]
        elif later and later[0] < nxt:
            nxt = later[0]
        f = nxt
    # no exposure shorter than 2 frames except where a choice forces it
    return starts


def smooth(a, b, u):
    u = min(1, max(0, u)); u = u * u * (3 - 2 * u)
    return a + (b - a) * u


# ------------------------------------------------------------------------------------------------- dog
LEGN = {'fore': 'dog_fore', 'farfore': 'dog_farfore', 'hind': 'dog_hind', 'farhind': 'dog_farhind'}
def leglen(p):
    piv = [v for k, v in PIECES[p]['pins'].items() if k != 'foot'][0]; f = pin(p, 'foot')
    return math.hypot(f[0] - piv[0], f[1] - piv[1])
LL = {k: leglen(v) for k, v in LEGN.items()}
OFF = {'hind': 0.0, 'fore': .25, 'farhind': .5, 'farfore': .75}   # lateral-sequence walk
STRIDE = .42 * K; STANCE = .62; AMP = STRIDE * STANCE / 2


def _phase(k, s):
    return (s / STRIDE + OFF[k]) % 1.0


def _d_reg(ph):
    if ph < STANCE:
        return AMP - ph / STANCE * 2 * AMP
    u = (ph - STANCE) / (1 - STANCE)
    return -AMP + 2 * AMP * (.5 - .5 * math.cos(math.pi * u))


def _start_swing(k, sgn):
    """first distance (in the direction of travel) at which leg k must leave the spot where it stood, and where that
    swing ends. Before it, the foot stays where the standing dog had it (offset -s from its pin: planted)."""
    step = STRIDE / 400
    s = 0.0
    while True:
        ph = _phase(k, s)
        if ph >= STANCE or abs(s) >= AMP * .9:   # its regular swing, or as far back as a leg will reach
            s1 = s
            break
        s += sgn * step
    s = s1
    while True:
        ph = _phase(k, s + sgn * step)
        if (sgn > 0 and ph < STANCE) or (sgn < 0 and ph < STANCE):
            return s1, s
        s += sgn * step


_SW = {}


def gait(s):
    """leg angles for distance s travelled forward from a standing start (px; negative = backing). In stance the
    foot's offset from its pin is linear in s, so on the table the foot does not move; at the start each foot stays
    where it stood until its first swing."""
    sgn = 1 if s >= 0 else -1
    out, phase = {}, {}
    for k in LEGN:
        if (k, sgn) not in _SW:
            _SW[(k, sgn)] = _start_swing(k, sgn)
        s1, s2 = _SW[(k, sgn)]
        ph = _phase(k, s)
        if abs(s) < abs(s1):
            d = -s; phase[k] = ('planted', -1)          # planted where it stood
        elif abs(s) < abs(s2):
            u = (s - s1) / (s2 - s1)
            tgt = AMP if sgn > 0 else -AMP
            d = -s1 + (tgt + s1) * (.5 - .5 * math.cos(math.pi * u)); phase[k] = ('swing', -2)   # first swing
        else:
            d = _d_reg(ph); phase[k] = ('stance' if ph < STANCE else 'swing', math.floor(s / STRIDE + OFF[k]))
        out[k] = math.degrees(math.asin(max(-1, min(1, d / LL[k]))))
    return out, phase


LIE = {'fore': 80, 'farfore': 72, 'hind': 110, 'farhind': 105}


def dog_pose(i, prev):
    f = F[i]; d = f['dog']; a = d['act']; t = f['t']; x = d['x']
    st = d['state']
    p = {'X': round(xs(x), 2), 'face': 1, 'head': -15, 'tail': 0, 'drop': 0, 'tilt': -4,   # -4: the back levelled
         'fore': 0, 'farfore': 0, 'hind': 0, 'farhind': 0}
    label = st
    cr = a['crouch']
    if i < CH['retreat']:
        p['head'] = -15 - 6 * a['crouch'] / .12
    elif i < CH['watch1']:                                   # backing away: crouched, head low, tail tucked
        g, _ = gait(-(x - 3.0) * K)
        p.update(g); p['head'] = smooth(-36, -48, (t - 1.0) / .15); p['tail'] = 45 * min(1, cr / .8)
        p['drop'] = 7 * cr; p['tilt'] = 4 * cr
        label = 'retreat: backing away'
    elif i < CH['refuse']:                                   # stops; the feet are re-set one at a time
        g, _ = gait(-(x - 3.0) * K)           # still drifting back as it stops (the score decelerates)
        order = ['hind', 'fore', 'farhind', 'farfore']
        k = max(0, int((i - 66) / 3))         # then the feet are re-set one at a time (a step each)
        for n, leg in enumerate(order):
            p[leg] = 0 if n < k else g[leg]
        p['head'] = smooth(-30, -18, (t - 2.33) / .5); p['tail'] = 45 * min(1, cr / .8) + 5
        p['drop'] = 7 * cr; p['tilt'] = 4 * cr
        label = 'watch'
    elif i < 86:                                             # the turning card (substitution)
        p = {'X': p['X'], 'card': 'front', 'face': 1}
        label = 'refuse: turning card'
    elif i < CH['watch2']:                                   # back turned; then lies down, chin on paws
        p['face'] = -1
        l = a['lie']; rest = a['rest']
        p['head'] = smooth(-40, -25, l) + (-50) * rest
        p['tail'] = smooth(70, 58, l)          # tucked down between the hind legs
        for k in LIE: p[k] = LIE[k] * l
        p['drop'] = 50 * l + 4; p['tilt'] = 2 * l + 2 * (1 - l)
        label = 'refuse: back turned' + (', lying' if l > .5 else '')
    elif i < 194:                                            # the head card turned over: looks back; then rises
        p['face'] = -1; p['headflop'] = 1; p['headpiece'] = 'dog_face'   # the face card, looking back at the door
        l = a['lie']
        p['head'] = 0
        for k in LIE: p[k] = LIE[k] * l
        p['drop'] = 50 * l; p['tilt'] = 2 * l; p['tail'] = 25 * l
        label = 'watch: looks back over the shoulder' + (', rising' if l > .1 else '')
    elif i < 200:
        p = {'X': p['X'], 'card': 'front', 'face': -1}
        label = 'watch: turning card'
    elif i < CH['approach']:                                 # watching the open door
        p['head'] = -15
        tilt = 0
        for t0 in (7.4, 10.4):
            if t0 + .3 <= t < t0 + 1.6:
                tilt = 7                                     # the listening tilt of the head card at the soft voice
        if 12.5 <= t: p['head'] = smooth(-15, -30, (t - 12.5) / 1.5)
        p['head'] += tilt
        p['tail'] = 10 - 10 * math.sin(t * 5) * a['wag'] * 3
        label = 'watch'
    elif i < CH['lie']:                                      # coming, head low, below the line of the back
        g, _ = gait((4.0 - x) * K)
        p.update(g)
        p['head'] = smooth(-30, -32, (t - 14.71) / .2)   # the head drops on the first exposure of the choice
        p['neckdrop'] = smooth(42, 46, (t - 14.71) / .2)  # and hangs from lower on the chest: wholly below the withers
        p['tail'] = 18 + 8 * math.sin(t * 4.0)
        label = 'approach: head low'
    else:                                                    # lies down across the sill
        g, _ = gait((4.0 - 0.59) * K)
        l = max(a['lie'], .3)          # the first exposure of the choice already folds the legs a third of the way
        for k in LIE: p[k] = smooth(g[k], LIE[k], l)
        p['drop'] = 50 * l; p['tilt'] = 2 * l; p['tail'] = smooth(18, 25, l)
        hd = smooth(-32, -20, (l - .3) / .7); p['neckdrop'] = 46 * (1 - min(1, max(0, l - .3) / .6))
        if t >= 25.4: hd = smooth(-20, -38, (t - 25.4) / .7)
        p['head'] = hd
        label = 'lie_down: across the sill'
        if LOOK_IN <= i < LOOK_OUT:
            p['headpiece'] = 'dog_backhead'
            # the held look moves: a tilt toward the voice inside, then back, then an ear-flick of the whole card
            p['head'] = 0 if t < 26.95 else (6 if t < 27.45 else (-3 if t < 27.8 else 1))
            label = 'lie_down: looks in through the door'
        elif i >= LOOK_OUT:
            p['head'] = smooth(-30, -75, (t - 28.08) / .55)
            label = 'lie_down: stays' if t > 28.7 else 'lie_down: settles'
    for k in list(p):   # a hand places a card to about a degree and half a pixel: drift below that is a hold
        if isinstance(p[k], float): p[k] = round(p[k] * 2) / 2 if k == 'X' else float(round(p[k]))
    return p, label


# ------------------------------------------------------------------------------------------------- person
SIT_X = 128


def person_pose(i):
    t = i / 24
    mouth = max(VOICE['mouth'][i:i + 2]) if i < N else 0
    p = {'X': 290, 'sit': 0, 'arm': 0, 'jaw': round(mouth, 2), 'nod': 4, 'lean': 0, 'crate': 142}
    if .8 <= t < 2.3: p['nod'] = -6; p['lean'] = 4
    if 3.22 <= t < 4.6:            # the reach starts with the second call, a beat before the dog turns its back
        p['nod'] = -4; p['lean'] = smooth(4, 10, (t - 3.22) / .25); p['arm'] = smooth(0, 86, (t - 3.22) / .25)
    if 4.6 <= t < 4.8: p['arm'] = smooth(86, 0, (t - 4.6) / .2); p['lean'] = 4
    if t >= 4.8: p['X'] = smooth(290, SIT_X, (t - 4.8) / .6)
    if t >= 5.4: p['sit'] = smooth(0, 1, (t - 5.4) / .4)
    if t >= 5.8: p['lean'] = 3; p['nod'] = 8
    if t >= 6.8:
        p['arm'] = smooth(0, 58, (t - 6.8) / .3); p['lean'] = smooth(3, 12, (t - 6.8) / .3); p['nod'] = 12
    if t >= 23.9: p['nod'] = 16
    for k in list(p):
        if isinstance(p[k], float): p[k] = round(p[k], 1) if k == 'jaw' else float(round(p[k]))
    return p


def moon_beat(i):
    """the absurd beat, 11.9-13.6 s, while the dog only watches: a giant hand slides in from the right edge, takes the
    moon between finger and thumb, lowers it into the cloud (the dusk deepening, by hand), and withdraws."""
    t = i / 24
    dy = 0.0; hx = None
    if 11.9 <= t < 13.7:
        if t < 12.4: hx = smooth(1420, 1150, (t - 11.9) / .5)
        elif t < 13.2: hx = 1150
        else: hx = smooth(1150, 1430, (t - 13.2) / .45)
        if hx > 1400: hx = None
    if t >= 12.6: dy = smooth(0, 56, (t - 12.6) / .45)
    return float(round(dy)), (None if hx is None else float(round(hx)))


def door_state(i):
    name, fr = 'door_24', .1
    for f0, n, o in DOOR:
        if i >= f0: name, fr = n, o
    return name, fr


def main():
    starts = exposure_starts()
    ex = []
    prev = None
    for k, s0 in enumerate(starts):
        s1 = starts[k + 1] if k + 1 < len(starts) else N
        dp, lab = dog_pose(s0, prev)
        pp = person_pose(s0)
        dn, op = door_state(s0)
        e = {'f0': s0, 'n': s1 - s0, 't': round(s0 / 24, 3), 'state': F[s0]['dog']['state'], 'dog': dp, 'dog_label': lab,
             'person': pp, 'door': dn, 'open': op, 'cloud_dx': round(-.35 * s0 / 2, 2)}
        e['moon_dy'], e['hand_x'] = moon_beat(s0)
        if prev and prev['dog'] == dp and prev['person'] == pp and prev['door'] == dn and abs(prev['cloud_dx'] - e['cloud_dx']) < 4 \
                and prev['moon_dy'] == e['moon_dy'] and prev['hand_x'] == e['hand_x'] \
                and prev['state'] == e['state']:
            prev['n'] += e['n']           # nothing touched: the previous exposure is simply held
            continue
        ex.append(e); prev = e
    for k, e in enumerate(ex):
        e['k'] = k
    out = {'about': 'exposure sheet: one row per exposure (f0 first film frame, n frames held). Dog/person poses are pin angles '
                    '(deg), slides (px) and card substitutions; see build/puppets.py.', 'choices_frames': CH,
           'look_in_frame': LOOK_IN, 'exposures': ex}
    json.dump(out, open(os.path.join(FOLDER, 'xsheet.json'), 'w'), indent=0)
    lens = [e['n'] for e in ex]
    print(len(ex), 'exposures; frames', sum(lens), '; min hold', min(lens), '; 1-frame exposures',
          [e['f0'] for e in ex if e['n'] < 2])
    print('choices', CH)


if __name__ == '__main__':
    main()
