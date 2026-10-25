"""SCION 07 · metamorphosis dramaturg + interpolation engineer.

Turns the score into a REGISTERED MORPH SEQUENCE: for every scene frame, which key drawings are blended and by how much
(transformation pacing), where the head key sits, the acting fields from the score (ear, tail, wag), the planted paws
(foot interventions), the person's key blend, the door angle and the door-to-light metamorphosis.

Outputs (build/cache/): seq.pkl (per-frame screen strokes for render.py), and in the folder: trace.json (measured from the
geometry that is drawn), proof/topology.json (discontinuity markers), build/schedule.json (the registered sequence),
build/cache/events.json (sound events)."""
import json, math, os, pickle, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dog import compose, to_screen, BODY, HEAD, LEGS
import stage as ST

ROOT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
PK = json.load(open(os.path.join(ROOT, 'keys', 'person_keys.json')))['keys']
FPS = 24


def smooth(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- the dog's registered key sequence (hand-timed to the score)
# body: (t, {key: weight}). '|' marks a declared substitution (same point set, mirrored correspondences).
# Round 2: a declared substitution is INSTANTANEOUS: two waypoints at the same time (a zero-length segment is never
# interpolated). In round 1 they were 0.01 s tweens, and a frame that landed inside one blended a key with its own mirror,
# which collapsed the body (the sliver at 3.833 s and the broken body at 8.375 s).
BODY_SEQ = [
    (0.00, {'stand': 1}),
    (0.98, {'stand': 1}),
    (1.30, {'crouch': .85, 'stand': .15}),          # retreat: the call presses it down and back
    (2.36, {'crouch': .85, 'stand': .15}),
    (2.85, {'stand': 1}),                           # watch again, upright
    (3.42, {'stand': 1}),                           # call again + reach: it turns its back
    (3.60, {'rear34L': 1}),
    (3.80, {'rearA': 1}),
    (3.86, {'rearA': 1}), ('|', 3.86, 'rearA', 'rearB'),
    (3.86, {'rearB': 1}),
    (4.04, {'rear34R': 1}),
    (4.26, {'stand_R': .5, 'crouch_R': .5}),
    (4.55, {'crouch_R': .5, 'lie_R': .5}),
    (5.00, {'lie_R': 1}),                           # lies down with its back to the door
    (6.00, {'curl_R': .6, 'lie_R': .4}),           # and closes: the contour draws in (the refusal, drawn)
    (7.42, {'curl_R': .6, 'lie_R': .4}),
    (7.62, {'lie_R': 1}),                           # opens as the head comes round (head sequence leads from 7.46)
    (7.88, {'front34R': .55, 'crouch_R': .45}),     # rises turning toward us, behind its face
    (8.02, {'frontB': 1}),
    (8.06, {'frontB': 1}), ('|', 8.06, 'frontB', 'frontA'),
    (8.06, {'frontA': 1}),
    (8.22, {'front34L': 1}),
    (8.42, {'stand': 1}),
    (14.71, {'stand': 1}),
    (15.00, {'stand': .88, 'crouch': .12}),        # comes, low
    (23.79, {'stand': .88, 'crouch': .12}),
    (24.05, {'crouch': .45, 'lie': .55}),
    (24.50, {'lie': 1}),
    (32.0, {'lie': 1}),
]

PA = (-0.55, 0.73, 0.0, 1.0)
HL = 1.1   # the head drawn a little larger when the dog lies (round 2: the small head read as a rodent's)
HEAD_SEQ = [  # (t, {headkey: w}, placement)
    (0.00, {'profile': 1}, PA),
    (0.98, {'profile': 1}, PA),
    (1.30, {'profile': 1}, (-0.57, 0.55, 0.14, 1.0)),
    (2.36, {'profile': 1}, (-0.57, 0.55, 0.14, 1.0)),
    (2.85, {'profile': 1}, PA),
    (3.42, {'profile': 1}, PA),
    (3.56, {'rear34': 1}, (-0.33, 0.68, 0.0, 0.95)),   # the head leads the turn away
    (3.76, {'rearH': 1}, (0.0, 0.70, 0.0, 0.95)),
    (3.84, {'rearH': 1}, (0.0, 0.70, 0.0, 0.95)), ('|', 3.84, 'rearH', 'rearH_R'),
    (3.84, {'rearH_R': 1}, (0.0, 0.70, 0.0, 0.95)),
    (4.00, {'rear34_R': 1}, (0.33, 0.64, 0.0, 0.95)),
    (4.24, {'profile_R': 1}, (0.56, 0.52, -0.28, 1.0)),
    (4.55, {'profile_R': 1}, (0.57, 0.36, -0.3, 1.05)),
    (5.00, {'profile_R': 1}, (0.56, 0.30, -0.3, HL)),
    (5.70, {'profile_R': 1}, (0.55, 0.16, -0.2, HL)),
    (6.00, {'profile_R': 1}, (0.47, 0.15, -0.22, HL)),   # head down on its paws in the curl, back turned
    (7.40, {'profile_R': 1}, (0.47, 0.15, -0.22, HL)),
    (7.46, {'front34_R': 1}, (0.52, 0.24, -0.05, HL)),   # 7.46: the head lifts and comes round, past the camera,
    (7.50, {'frontH_R': 1}, (0.52, 0.31, 0.0, HL)),      #       through the drawn front view (not a mirror flip),
    (7.51, {'frontH_R': 1}, (0.52, 0.32, 0.0, HL)), ('|', 7.51, 'frontH_R', 'frontH'),
    (7.51, {'frontH': 1}, (0.52, 0.32, 0.0, HL)),
    (7.56, {'front34': 1}, (0.48, 0.38, 0.0, HL)),       #       and faces the door, muzzle to the left, from 7.56
    (7.72, {'front34': .45, 'profile': .55}, (0.40, 0.50, 0.0, 1.05)),  # muzzle at the door while it rises
    (7.88, {'front34': .6, 'profile': .4}, (0.30, 0.60, 0.0, 1.03)),     # rises facing the door
    (8.04, {'front34': 1}, (-0.03, 0.72, 0.0, 1.0)),     # the body comes round under it
    (8.22, {'front34': .4, 'profile': .6}, (-0.40, 0.71, 0.0, 1.0)),
    (8.42, {'profile': 1}, PA),
    (10.0, {'profile': 1}, PA),
    (14.6, {'profile': 1}, (-0.57, 0.69, 0.08, 1.0)),   # trust: the watching head drifts down and forward
    (14.71, {'profile': 1}, (-0.57, 0.69, 0.08, 1.0)),
    (15.00, {'profile': 1}, (-0.60, 0.40, 0.30, 1.0)),  # head low, below the line of the back, for the whole approach
    (23.79, {'profile': 1}, (-0.60, 0.40, 0.30, 1.0)),
    (24.45, {'profile': 1}, (-0.52, 0.47, 0.0, HL)),
    (25.40, {'profile': 1}, (-0.52, 0.47, 0.0, HL)),
    (26.10, {'profile': 1}, (-0.57, 0.32, 0.16, HL)),
    (26.40, {'profile': 1}, (-0.57, 0.32, 0.16, HL)),   # come in (soft): it turns its head in, through the door
    (26.72, {'rear34': 1}, (-0.60, 0.42, 0.12, HL)),    # back of the head to us, muzzle pointing level into the lit room
    (28.05, {'rear34': 1}, (-0.60, 0.42, 0.12, HL)),
    (28.65, {'profile': 1}, (-0.62, 0.20, 0.08, 1.14)),  # and settles, head down on its paws, and stays
    (32.0, {'profile': 1}, (-0.62, 0.20, 0.08, 1.14)),
]

STATE_AT = [(0, 'watch')] + [(c['t'], c['to']) for c in SCORE['choices']]


def seq_eval(seq, t, with_place=False):
    pts = [s for s in seq if s[0] != '|']
    subs = [s for s in seq if s[0] == '|']
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if a[0] <= t < b[0] or i == len(pts) - 2:
            u = smooth((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 1.0
            w = {}
            for k, v in a[1].items(): w[k] = w.get(k, 0) + v * (1 - u)
            for k, v in b[1].items(): w[k] = w.get(k, 0) + v * u
            if with_place:
                pl = tuple(lerp(x, y, u) for x, y in zip(a[2], b[2]))
                return w, pl, (i, u)
            return w, None, (i, u)
    raise ValueError(t)


def state_at(t):
    st = 'watch'
    for tt, s in STATE_AT:
        if t >= tt - 1e-6: st = s
    return st


# ---------------------------------------------------------------- the person's key sequence
def person_pose(f):
    p = f['person']; t = f['t']
    mouth = p['mouth']
    w = {}
    if t < 5.0:
        reach = p['reach']
        call = min(mouth / 0.9, 1.0) * (1 - reach)
        w = {'stand': max(1 - call - reach, 0), 'call': call, 'reach': reach}
        if 4.6 <= t:
            w = {'stand': 1}
            if p['reach'] > 0.02: w = {'stand': 1 - p['reach'], 'reach': p['reach']}
    elif t < 5.55:
        u = (t - 5.0) / 0.55
        ph = 0.5 - 0.5 * math.cos(u * 2 * math.pi * 1.5)
        w = {'stand': 1 - ph, 'side': ph}
    else:
        sit = p['sit']; low = p['low']
        if sit < 0.5:
            w = {'stand': max(0, 1 - sit * 2), 'lower': min(1, sit * 2)}
        else:
            s2 = (sit - 0.5) * 2
            w = {'lower': 1 - s2, 'sit': s2 * (1 - low), 'low': s2 * low * (1 - min(mouth / 0.35, 1)), 'soft': s2 * low * min(mouth / 0.35, 1)}
    tot = sum(w.values())
    w = {k: v / tot for k, v in w.items() if v > 1e-6}
    out = []
    loom = 1.0 + 0.09 * min(mouth / 0.9, 1.0) * (1.0 if p['voice'] == 'call' else 0.0) + 0.05 * p['reach']
    for n in PK['stand']:
        s0 = PK['stand'][n]
        pts = [[0, 0] for _ in s0['pts']]
        for kn, kw in w.items():
            for i, q in enumerate(PK[kn][n]['pts']):
                pts[i][0] += q[0] * kw; pts[i][1] += q[1] * kw
        if loom > 1.0:   # the call distorts the caller: the figure swells and leans toward the dog
            pts = [[q[0] * loom + (loom - 1) * 0.8 * q[1], q[1] * loom] for q in pts]
        s = dict(s0); s['pts'] = pts; s['name'] = n
        out.append(s)
    return out, w


def person_x(f):
    return f['person']['x']


# ---------------------------------------------------------------- paws: planted unless stepping (the foot intervention)
class Feet:
    def __init__(self):
        self.planted = {}; self.swing = {}; self.events = []

    def update(self, t, xd, desired, fold, dt=1 / FPS, free=0.0):
        """desired: {leg: [x,y] body-local}; returns body-local paws and lifts."""
        world = {L: [xd + desired[L][0], desired[L][1]] for L in LEGS}
        if not self.planted:
            self.planted = {L: list(world[L]) for L in LEGS}
        paws, lifts = {}, {}
        if fold > 0.02:
            f = smooth(fold * 2.2)
            for L in LEGS:
                p = [lerp(self.planted[L][0], world[L][0], f), lerp(self.planted[L][1], world[L][1], f)]
                if f >= 0.999: self.planted[L] = list(world[L])
                paws[L] = [p[0] - xd, p[1]]; lifts[L] = 0.0
            self.swing = {}
            return paws, lifts
        if free > 0.04:
            # turning on the spot: the paws follow the drawn view, lifted in proportion to how fast they move (steps)
            prev = getattr(self, 'prev_world', world)
            for L in LEGS:
                sp = abs(world[L][0] - prev[L][0])
                h = min(0.07, sp * 1.6)
                paws[L] = [world[L][0] - xd, h]; lifts[L] = h / 0.075
                self.planted[L] = list(world[L])
                if h > 0.02 and getattr(self, 'last_ev', {}).get(L, -9) < t - 0.15:
                    self.events.append({'t': round(t, 3), 'leg': L, 'x': round(world[L][0], 3)}); self.last_ev = dict(getattr(self, 'last_ev', {}), **{L: t})
            self.prev_world = world; self.swing = {}
            return paws, lifts
        self.prev_world = world
        # finish swings
        for L in list(self.swing):
            s = self.swing[L]
            u = (t - s['t0']) / s['dur']
            if u >= 1:
                self.planted[L] = [s['to'][0], 0.0]
                self.events.append({'t': round(t, 3), 'leg': L, 'x': round(s['to'][0], 3)})
                del self.swing[L]
        # start swings for the legs left furthest behind
        err = {L: world[L][0] - self.planted[L][0] for L in LEGS if L not in self.swing}
        vel = getattr(self, 'v', 0.0)
        thr = 0.075 if abs(vel) > 0.05 else 0.09
        for L in sorted(err, key=lambda L: -abs(err[L])):
            if abs(err[L]) < thr or len(self.swing) >= 2:
                continue
            pair = [M for M in self.swing if M[1] == L[1]]
            if pair:
                continue
            recent = [s for s in self.swing.values() if t - s['t0'] < 0.07]
            if recent:
                continue
            to = world[L][0] + vel * 0.16
            self.swing[L] = {'t0': t, 'dur': 0.19 if abs(vel) > 0.05 else 0.16, 'from': list(self.planted[L]), 'to': [to, 0.0]}
        for L in LEGS:
            if L in self.swing:
                s = self.swing[L]
                u = smooth((t - s['t0']) / s['dur'])
                x = lerp(s['from'][0], s['to'][0], u)
                h = 0.075 * math.sin(math.pi * min(1, (t - s['t0']) / s['dur']))
                paws[L] = [x - xd, h]; lifts[L] = h / 0.075
            else:
                paws[L] = [self.planted[L][0] - xd, 0.0]; lifts[L] = 0.0
        return paws, lifts


def centroid(P):
    a = cx = cy = 0.0
    for i in range(len(P)):
        x0, y0 = P[i]; x1, y1 = P[(i + 1) % len(P)]
        c = x0 * y1 - x1 * y0
        a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    if abs(a) < 1e-9:
        return sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)
    return cx / (3 * a), cy / (3 * a)


def main():
    from draw import cr
    feet = Feet()
    frames, trace, topo = [], [], []
    prev_P = None
    prev_order = None
    for f in FR:
        i, t = f['i'], f['t']
        d = f['dog']; act = d['act']
        bw, _, bseg = seq_eval(BODY_SEQ, t)
        hw, place, hseg = seq_eval(HEAD_SEQ, t, True)
        xd = d['x']
        # desired paws from the blended key (no foot intervention), then the feet decide
        st0, _ = compose(bw, hw, place, ear=act['ear'], tv=act['tail'])
        desired = {s['name']: s['pts'][-1] for s in st0 if s['name'] in LEGS}
        lie_w = sum(v for k, v in bw.items() if k.startswith('lie'))
        feet.v = d['v']
        turn_w = sum(v for k, v in bw.items() if k[:4] in ('rear', 'fron'))
        paws, lifts = feet.update(t, xd, desired, lie_w, free=turn_w)
        breath = 0.6 * math.sin(2 * math.pi * t / (3.4 if lie_w < 0.5 else 4.2))
        strokes, meta = compose(bw, hw, place, ear=act['ear'], tv=act['tail'], wag=act['wag'], t=t, breath=breath,
                                paws=paws, lifts=lifts)
        scr = to_screen(strokes, ST.X0, ST.YDOG, ST.S, xd)
        # ---- person
        pst, pw = person_pose(f)
        pscr = to_screen(pst, ST.X0, ST.YDOG - 2, ST.S, person_x(f))
        # ---- door: ajar until 6.2, then it swings; the leaf's outline is carried out onto the boards as light
        tdo = 6.2
        open_u = smooth((t - tdo) / 0.75)
        theta = math.radians(lerp(24, 84, open_u))
        lit = smooth((t - tdo - 0.1) / 0.9)
        meta_u = smooth((t - tdo - 0.05) / 0.95)          # door -> light metamorphosis progress
        frames.append({'i': i, 't': t, 'dog': scr, 'fwd': meta['fwd'], 'person': pscr, 'theta': theta, 'lit': lit,
                       'meta_u': meta_u, 'late': t / 32.0, 'prompt': f.get('prompt', '')})
        # ---- measure what is drawn
        body = next(s for s in scr if s['name'] == 'body')
        poly = cr(body['P'][1:11], True, 7)      # the torso: withers .. chest, without the neck points bound to the head
        cxs, cys = centroid(poly)
        head = next(s for s in scr if s['name'] == 'head')
        hpoly = cr(head['P'], True, 7)
        head_top = min(p[1] for p in hpoly)
        withers = body['P'][1][1]
        gaze = meta['gaze']
        # measured from the drawn head: where the nose point sits relative to the head outline (-1 far left .. +1 far right)
        nose = next(s for s in scr if s['name'] == 'nose')
        hxs = [p[0] for p in hpoly]
        hcx = sum(hxs) / len(hxs); hwid = (max(hxs) - min(hxs)) / 2 or 1.0
        muzzle = (nose['P'][0][0] - hcx) / hwid if nose['a'] > 0.3 else 0.0
        eyes_shown = max(s['a'] for s in scr if s['name'] in ('eyeR', 'eyeL'))
        facing = 1 if muzzle < -0.15 else -1
        turnw = sum(v for k, v in bw.items() if k[:4] in ('rear', 'fron'))
        crw = sum(v for k, v in bw.items() if k.startswith('crouch'))
        posture = 'lie' if lie_w > 0.5 else 'turning' if turnw > 0.3 else 'crouch' if crw > 0.5 else 'stand'
        sill_line = ST.DOOR[1]
        xs = [p[0] for s in scr for p in s['P'] if s['a'] > 0.3]
        trace.append({'i': i, 't': t, 'state': state_at(t), 'x_score': round((cxs - ST.X0) / ST.S, 4), 'x_screen': round(cxs, 2),
                      'y_screen': round(cys, 2), 'facing': facing, 'posture': posture,
                      'head_top_y': round(head_top, 1), 'withers_y': round(withers, 1),
                      'head_below_back_px': round(head_top - withers, 1),
                      'front_px_inside_frame': round(max(0.0, sill_line - min(xs)), 1),
                      'rear_px_outside_frame': round(max(0.0, max(xs) - sill_line), 1),
                      'muzzle_dir': round(muzzle, 3), 'eyes_shown': round(eyes_shown, 3),
                      'withers_m': round((ST.YDOG - withers) / ST.S, 4), 'head_cx_px': round(hcx, 1),
                      'x_anchor_score': xd, 'body_keys': {k: round(v, 3) for k, v in bw.items()},
                      'head_keys': {k: round(v, 3) for k, v in hw.items()}})
        # topology: draw-order flips and declared substitutions
        order = [s['name'] for s in sorted(scr, key=lambda s: s['z']) if s['a'] > 0.05]
        if prev_order and order != prev_order:
            topo.append({'i': i, 't': t, 'kind': 'draw-order change', 'from': prev_order, 'to': order})
        prev_order = order
        # morph speed (px/frame, mean over corresponding points) for the sound of the drawing changing
        P = [p for s in scr for p in s['P']]
        sp = 0.0 if prev_P is None else sum(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(P, prev_P)) / len(P)
        frames[-1]['morph_speed'] = sp; trace[-1]['morph_px_per_frame'] = round(sp, 3)
        prev_P = P
    # ---- measured onsets of each choice, from the drawn geometry (not from the schedule's state labels)
    def first(pred, after):
        for k, f in enumerate(trace):
            if f['t'] >= after and pred(k, f):
                return f['t']
        return None
    vel = lambda k: (trace[min(k + 1, len(trace) - 1)]['x_screen'] - trace[max(k - 1, 0)]['x_screen']) / ST.S * FPS / 2
    dwh = lambda k: (trace[min(k + 1, len(trace) - 1)]['withers_m'] - trace[max(k - 1, 0)]['withers_m']) * FPS / 2
    mz0 = trace[int(3.0 * FPS)]['muzzle_dir']
    stand_w = trace[int(22.0 * FPS)]['withers_m']
    onsets = [
        ('retreat', 1.0, 'torso moves away from the door faster than 0.05 m/s', first(lambda k, f: vel(k) > 0.05, 0.5)),
        ('watch', 2.333, 'body starts to rise out of the crouch (withers rising > 0.05 m/s)', first(lambda k, f: dwh(k) > 0.05, 1.6)),
        ('refuse', 3.417, 'the drawn muzzle starts to swing away (muzzle_dir moves > 0.15 from its 3.0 s value)',
         first(lambda k, f: abs(f['muzzle_dir'] - mz0) > 0.15, 3.0)),
        ('watch', 7.458, 'the drawn muzzle points toward the door again (muzzle_dir < -0.15)',
         first(lambda k, f: f['muzzle_dir'] < -0.15, 6.0)),
        ('approach', 14.708, 'torso moves toward the door faster than 0.05 m/s', first(lambda k, f: vel(k) < -0.05, 9.0)),
        ('lie_down', 23.792, 'withers drop more than 0.03 m below standing height', first(lambda k, f: f['withers_m'] < stand_w - 0.03, 20.0)),
        ('look in', 26.4, 'the head turns away from us into the doorway (eyes hidden) while inside the door frame',
         first(lambda k, f: f['eyes_shown'] < 0.5 and f['head_cx_px'] < ST.DOOR[1], 25.0)),
    ]
    measured = [{'choice': c, 'score_t': st_, 'measure': m, 'onset_t': o, 'dt': None if o is None else round(o - st_, 3)}
                for c, st_, m, o in onsets]
    for s in BODY_SEQ + HEAD_SEQ:
        if s[0] == '|':
            topo.append({'t': s[1], 'kind': 'declared substitution (mirrored correspondence, same point set)', 'from': s[2], 'to': s[3]})
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    pickle.dump(frames, open(os.path.join(HERE, 'cache', 'seq.pkl'), 'wb'))
    json.dump({'about': 'SCION 07 trace: measured from the geometry drawn in each scene frame (centroid of the torso contour, body points 1-10, withers to chest; the neck points are bound to the head and left out; head '
               'and withers heights, extents against the door frame). state is the dog\'s choice as scheduled from the score; '
               'facing is measured from the drawn head (1 when the drawn nose point is on the door side of the head outline, -1 when it points away or is hidden). measured_onsets gives the onset of each choice, detected from the drawn geometry.',
               'mapping': {'x_screen': 'X0 + S * x', 'X0': ST.X0, 'S': ST.S, 'door_frame_px': ST.DOOR[:2]},
               'measured_onsets': measured, 'frames': trace}, open(os.path.join(ROOT, 'trace.json'), 'w'))
    for m in measured:
        print('onset', m['choice'], m['score_t'], '->', m['onset_t'], m['dt'])
    os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)
    json.dump(topo, open(os.path.join(ROOT, 'proof', 'topology.json'), 'w'), indent=0)
    json.dump({'body': [list(s) if s[0] == '|' else [s[0], s[1]] for s in BODY_SEQ],
               'head': [list(s) if s[0] == '|' else [s[0], s[1], list(s[2])] for s in HEAD_SEQ]},
              open(os.path.join(HERE, 'schedule.json'), 'w'), indent=0)
    ev = {'paws': feet.events, 'morph': [round(fr['morph_speed'], 3) for fr in frames]}
    json.dump(ev, open(os.path.join(HERE, 'cache', 'events.json'), 'w'))
    print('frames', len(frames), 'steps', len(feet.events), 'topology events', len(topo))


if __name__ == '__main__':
    main()
