"""ILLUSTRATOR: the illustration bank. Each entry is one finished drawing with the pose it represents.
Drawings are set by hand from the construction kit in dogparts.py; walking drawings are set on a gait chart so
that a planted paw stays on the same board from one drawing to the next (see GAIT). Flops (left-right mirror
copies) are separate drawings for the other facing; a turn never mirrors, it goes through drawn three-quarter
and front views.
python3 build/bank.py  -> bank/bank.json"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from geom import add, mirror, ellipse, limb, cr
from dogparts import profile_dog, part, head_front, head_q, head_back, tail_part

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'bank', 'bank.json')
D = {}
S = 190.0                      # px per metre
STRIDE_M = 2 * math.pi / 11.42  # metres per gait cycle (the score's walk phase advances 11.42 rad per metre)
STRIDE = STRIDE_M * S           # px
NWALK = 8


def put(id, parts, pose, meta, note='', group=''):
    meta = dict(meta); meta['note'] = note; meta['group'] = group
    D[id] = {'parts': parts, 'pose': pose, 'meta': meta}


def flop(src, id, pose_over, note='', group=None):
    s = D[src]
    meta = json.loads(json.dumps(s['meta']))
    for k in ('nose', 'eye', 'withers', 'croup'):
        if k in meta: meta[k] = [-meta[k][0], meta[k][1]]
    if 'feet' in meta: meta['feet'] = {k: [-v[0], v[1]] for k, v in meta['feet'].items()}
    meta['flopped_from'] = src
    pose = dict(s['pose']); pose.update(pose_over)
    put(id, mirror(s['parts']), pose, meta, note or ('flop of ' + src), group if group is not None else s['meta'].get('group', ''))


def pose(**k):
    base = dict(yaw=0, lie=0, crouch=0, head=.9, look=0, rest=0, ear=1, tail=.5, moving=0, back=0, phase=None, wag=0, over=0)
    base.update(k)
    return base


TAIL_HANG = [(54, -98), (72, -88), (82, -66), (80, -44)]
TAIL_LOW = [(54, -96), (66, -82), (70, -62), (64, -44)]
TAIL_TUCK = [(52, -80), (60, -62), (52, -44), (40, -34)]

# ---------------------------------------------------------------- standing, facing the door (left)
p, m = profile_dog(W=(-36, -104), R=(42, -101), d=58, head=dict(base=(-62, -128), pitch=.1, ears='up', s=1.1),
                   paws={'fn': (-52, 0), 'ff': (-34, 0), 'hn': (56, 0), 'hf': (42, 0)}, tail=TAIL_HANG)
put('watch', p, pose(head=.9, ear=1, tail=.5), m, 'standing, alert, faces the door', 'stand')

p, m = profile_dog(W=(-36, -104), R=(42, -101), d=58, head=dict(base=(-60, -131), pitch=.32, ears='up', s=1.1, tilt_ear='half'),
                   paws={'fn': (-52, 0), 'ff': (-34, 0), 'hn': (56, 0), 'hf': (42, 0)}, tail=[(54, -98), (74, -92), (86, -74), (88, -56)])
put('listen', p, pose(head=1.0, ear=1, tail=.4, listen=1), m, 'hears the soft voice: nose lifts, ears forward', 'stand')

p, m = profile_dog(W=(-36, -97), R=(42, -93), d=56, head=dict(base=(-64, -112), pitch=0, ears='half', s=1.1),
                   paws={'fn': (-50, 0), 'ff': (-32, 0), 'hn': (54, 0), 'hf': (40, 0)}, tail=TAIL_LOW)
put('wary', p, pose(crouch=.35, head=.7, ear=.6, tail=.8), m, 'wary, weight back, ears half', 'stand')

p, m = profile_dog(W=(-34, -88), R=(46, -80), d=52, head=dict(base=(-62, -96), pitch=-.05, ears='flat', s=1.1),
                   paws={'fn': (-50, 0), 'ff': (-32, 0), 'hn': (50, 0), 'hf': (36, 0)}, tail=TAIL_TUCK)
put('flinch', p, pose(crouch=.85, head=.4, ear=0, tail=1.3), m, 'flinches from the call: low, tail tucked', 'stand')

p, m = profile_dog(W=(-34, -92), R=(44, -88), d=54, head=dict(base=(-66, -84), pitch=-.45, ears='flat', s=1.1),
                   paws={'fn': (-50, 0), 'ff': (-32, 0), 'hn': (52, 0), 'hf': (38, 0)}, tail=TAIL_TUCK)
put('cower', p, pose(crouch=.5, head=.15, ear=0, tail=1.2), m, 'cowers from the reach, head down', 'stand')

p, m = profile_dog(W=(-36, -101), R=(42, -99), d=57, head=dict(base=(-70, -76), pitch=-.32, ears='low', s=1.1),
                   paws={'fn': (-52, 0), 'ff': (-34, 0), 'hn': (56, 0), 'hf': (42, 0)}, tail=TAIL_LOW)
put('stand_low', p, pose(head=.45, ear=.55, tail=.3), m, 'decides: head low, below the back', 'stand')


# ---------------------------------------------------------------- gait chart: walking (head low) and backing away (crouched)
def gait_feet(k, n, direction, beta=.62, lift=9.0, xc=None):
    """Paw targets for drawing k of n. direction=-1 walks toward -x (left), +1 backs toward +x.
    In the body frame a planted paw slides backward at exactly the travel speed, so in the world it stays put."""
    xc = xc or {'fn': -46, 'ff': -40, 'hn': 50, 'hf': 44}
    off = {'hn': 0.0, 'fn': .25, 'hf': .5, 'ff': .75}
    phi = k / n
    out = {}
    for leg, o in off.items():
        psi = (phi + o) % 1.0
        if psi < beta:   # stance: paw moves opposite to travel in the body frame
            x = xc[leg] + direction * (STRIDE * beta / 2 - STRIDE * psi)
            y = 0.0
        else:
            s = (psi - beta) / (1 - beta)
            x = xc[leg] + direction * (-STRIDE * beta / 2 + STRIDE * beta * s)
            y = -lift * math.sin(math.pi * s)
        out[leg] = (round(x, 2), round(y, 2))
    return out


for k in range(NWALK):
    f = gait_feet(k, NWALK, -1)
    bob = 1.5 * math.cos(4 * math.pi * k / NWALK)
    nod = 2.0 * math.cos(4 * math.pi * k / NWALK + .6)
    p, m = profile_dog(W=(-36, -100 + bob), R=(42, -98 + bob), d=57,
                       head=dict(base=(-70, -73 + nod), pitch=-.34, ears='low', s=1.1),
                       paws=f, tail=[(54, -96 + bob), (68, -86), (76, -68 + 2 * math.sin(2 * math.pi * k / NWALK)), (74 + 3 * math.sin(2 * math.pi * k / NWALK), -50)])
    m['gait'] = {'k': k, 'n': NWALK, 'dir': -1, 'stride_px': round(STRIDE, 2)}
    put('walk_%d' % k, p, pose(head=.45, ear=.55, tail=.3, moving=1, phase=2 * math.pi * k / NWALK, crouch=.1), m,
        'comes, head low: gait %d/%d' % (k, NWALK), 'walk')

for k in range(NWALK):
    f = gait_feet(k, NWALK, +1, beta=.6, lift=7.0, xc={'fn': -44, 'ff': -38, 'hn': 46, 'hf': 40})
    bob = 1.5 * math.cos(4 * math.pi * k / NWALK)
    p, m = profile_dog(W=(-34, -87 + bob), R=(46, -80 + bob), d=52,
                       head=dict(base=(-62, -95 + bob), pitch=-.05, ears='flat', s=1.1),
                       paws=f, tail=TAIL_TUCK)
    m['gait'] = {'k': k, 'n': NWALK, 'dir': 1, 'stride_px': round(STRIDE, 2)}
    put('back_%d' % k, p, pose(crouch=.9, head=.35, ear=0, tail=1.35, moving=1, back=1, phase=2 * math.pi * k / NWALK), m,
        'backs away from the call: gait %d/%d' % (k, NWALK), 'back')


# ---------------------------------------------------------------- three-quarter and front views (the turns)
def q_body(head, low=True, tail=None):
    """Three-quarter view, the dog turned toward the viewer and to the left (yaw 45)."""
    if low:
        W, R, d = (-24, -90), (30, -96), 60
        paws = {'fn': (-30, 0), 'ff': (-12, -4), 'hn': (34, -6), 'hf': (20, -8)}
    else:
        W, R, d = (-24, -104), (30, -108), 62
        paws = {'fn': (-30, 0), 'ff': (-12, -4), 'hn': (34, -6), 'hf': (20, -8)}
    bib = part([add(W, (-30, d * .2)), add(W, (-8, d * .1)), add(W, (6, d * .7)), add(W, (-4, d * 1.05)), add(W, (-24, d * .95))], 'cream', 'mark', a=.55)
    p, m = profile_dog(W=W, R=R, d=d, head=head, paws=paws, tail=tail or TAIL_TUCK, sag=1, tuck=.85, extra=[bib])
    return p, m


p, m = q_body(dict(kind='q', base=(-50, -84), ears='flat', s=1.1, pitch=-.2), low=True)
put('q45_low', p, pose(yaw=45, crouch=.5, head=.2, ear=0, tail=1.2), m, 'turning away: three-quarter, head low', 'turn')
p, m = q_body(dict(kind='q', base=(-44, -118), ears='up', s=1.1, pitch=.05), low=False, tail=TAIL_HANG)
put('q45_up', p, pose(yaw=45, crouch=.1, head=.9, ear=1, tail=.5), m, 'turning to the door: three-quarter, head up', 'turn')


def front_body(head_c, ears, low=True, look=0.0, tail='tuck', headkind='front'):
    """Front view, the dog facing the viewer: the turn passes through this drawing instead of a squashed profile."""
    parts = []
    hy = 0 if low else -10
    for sx in (-1, 1):   # hind legs, further away: higher and darker
        parts.append(part(limb([(sx * 17, -64 + hy), (sx * 19, -36), (sx * 18, -14), (sx * 18, -7)], [20, 12, 8.5, 7.5], foot=None), 'coatD', 'far'))
        parts.append(part(ellipse((sx * 18, -6.5), 7, 3.8, 0, 12), 'coatD', 'far'))
    parts.append(part([(-200, -28), (200, -28), (200, 9), (-200, 9)], 'creamD', 'farmark', smooth=False, a=.9))
    if tail == 'tuck':
        parts.append(part(limb(cr([(4, -66), (9, -48), (4, -30), (-3, -20)], False, 4), [10, 9, 8, 7, 6, 5, 4.5, 4, 4, 3.5, 3.5, 3, 3]), 'saddle', 'far'))
    else:
        parts.append(part(limb(cr([(12, -108 + hy), (30, -116 + hy), (44, -110 + hy), (50, -96 + hy)], False, 4), [11, 10, 9, 8, 7, 6, 5, 5, 4, 4, 3, 3, 3]), 'coat', 'far'))
    # the back, seen a little from above, running away behind the shoulders
    if low:
        parts.append(part([(-24, -92), (-18, -106), (0, -111), (18, -106), (24, -92)], 'coat', 'main'))
    else:
        parts.append(part([(-25, -92 + hy), (-21, -110 + hy), (0, -117 + hy), (21, -110 + hy), (25, -92 + hy)], 'coat', 'main'))
    chest = [(-34, -92 + hy), (-18, -102 + hy), (18, -102 + hy), (34, -92 + hy), (36, -70 + hy * .5), (28, -52), (12, -45), (-12, -45), (-28, -52), (-36, -70 + hy * .5)]
    parts.append(part(chest, 'coat', 'main'))
    for sx in (-1, 1):
        parts.append(part(limb([(sx * 17, -68), (sx * 18, -38), (sx * 17, -13), (sx * 18, -3)], [25, 15, 11, 10]), 'coat', 'main'))
        parts.append(part(ellipse((sx * 17.5, -3), 9, 4.8, 0, 14), 'coat', 'main'))
    if headkind == 'front':
        hp = head_front(head_c, ears=ears, s=1.1, look=look)
    elif headkind == 'qright':
        hp = head_q(head_c, ears=ears, s=1.05, pitch=-.25, flip=True)
    else:
        parts.append(part([(-24, -96 + hy), (-22, -110 + hy), (head_c[0] - 6, head_c[1] - 6), (head_c[0] + 14, head_c[1] + 2), (20, -98 + hy)], 'coat', 'main'))
        hp = head_q(head_c, ears=ears, s=1.08, pitch=0)
    parts += [q for q in hp if q['L'] == 'main']
    parts.append(part([(-200, -26), (200, -26), (200, 9), (-200, 9)], 'cream', 'mark', smooth=False, a=.85))
    parts.append(part([(-34, -122 + hy), (34, -122 + hy), (30, -100 + hy), (14, -96 + hy), (-14, -96 + hy), (-30, -100 + hy)], 'saddle', 'mark', a=.9))
    if low:
        parts.append(part([(-30, -86), (head_c[0] - 4, -74), (head_c[0] + 20, -70), (34, -78), (34, -66), (-30, -68)], 'cream', 'mark', a=.9))
    else:
        parts.append(part([(-30, -97 + hy), (30, -97 + hy), (26, -84 + hy), (-26, -84 + hy)], 'cream', 'mark', a=.95))
    parts.append(part([(-12, -84), (12, -84), (8, -52), (-8, -52)], 'cream', 'mark', a=.45))
    parts += [q for q in hp if q['L'] in ('mark',)]
    parts += [q for q in hp if q['L'] in ('line', 'dot')]
    for sx in (-1, 1):
        parts.append(part([(sx * 22, -4), (sx * 21, 0)], 'ink', 'line', w=1.0, closed=False, smooth=False))
        parts.append(part([(sx * 14, -4), (sx * 14, 0)], 'ink', 'line', w=1.0, closed=False, smooth=False))
    return parts


put('f90_low', front_body((10, -80), 'flat', low=True, headkind='qright'), pose(yaw=90, crouch=.5, head=.15, ear=0, tail=1.2),
    {'nose': [0, -70], 'eye': [0, -94]}, 'turning: faces the viewer, head low, ears flat', 'turn')
put('f90_qleft', front_body((-10, -120), 'up', low=False, tail='out', headkind='q'), pose(yaw=90, crouch=.1, head=.85, ear=1, tail=.6, over=1),
    {'nose': [-58, -118], 'eye': [-34, -125]}, 'turning back: body to the viewer, head already to the door', 'turn')
flop('q45_low', 'q135_low', dict(yaw=135), group='turn')
flop('cower', 'cower_R', dict(yaw=180), group='stand')

# ---------------------------------------------------------------- lying, and the moments lying down (facing left: across the sill)
LYF = {'fn': [(-38, -34), (-36, -10), (-70, -6), (-82, -3)], 'ff': [(-34, -36), (-30, -10), (-62, -8), (-74, -5)]}
LYH = {'hn': [(42, -30), (14, -16), (52, -7), (30, -3)], 'hf': [(38, -30), (16, -18), (46, -8), (28, -5)]}
TAIL_OUT = [(56, -40), (76, -26), (96, -12), (118, -6)]


def lying(head, tail=TAIL_OUT, W=(-30, -60), R=(44, -48), d=54):
    return profile_dog(W=W, R=R, d=d, head=head, paws={'fn': (0, 0), 'ff': (0, 0), 'hn': (0, 0), 'hf': (0, 0)}, tail=tail,
                       socks=False, tuck=.95, front_joints=LYF, hind_joints=LYH)


# sitting: hind down, front straight (the way down)
p, m = profile_dog(W=(-34, -100), R=(30, -62), d=52, head=dict(base=(-58, -116), pitch=0, ears='half', s=1.1),
                   paws={'fn': (-48, 0), 'ff': (-32, 0), 'hn': (0, 0), 'hf': (0, 0)}, tail=[(40, -42), (60, -24), (80, -10), (100, -4)],
                   hind_joints={'hn': [(30, -40), (4, -24), (36, -8), (12, -3)], 'hf': [(26, -40), (6, -26), (32, -9), (10, -5)]}, tuck=.9)
put('sit', p, pose(lie=.5, head=.7, ear=.6, tail=.3), m, 'going down: sits', 'lie')

p, m = lying(dict(base=(-56, -84), pitch=.02, ears='up', s=1.1))
put('lie_up', p, pose(lie=1, head=.75, ear=.8, tail=.25), m, 'lies across the sill, head up', 'lie')
p, m = lying(dict(base=(-60, -66), pitch=-.12, ears='half', s=1.1))
put('lie_low', p, pose(lie=1, head=.3, ear=.6, tail=.25), m, 'lies, head lowered', 'lie')
p, m = lying(dict(base=(-62, -38), pitch=-.04, ears='back', s=1.1))
put('rest', p, pose(lie=1, head=.2, rest=1, ear=.4, tail=.25), m, 'chin on the paws: stays', 'lie')
for nm, tl, wg in (('look_in', TAIL_OUT, 0), ('look_in_a', [(56, -40), (78, -34), (100, -34), (122, -40)], 1), ('look_in_b', [(56, -40), (74, -20), (92, -6), (112, 0)], -1)):
    p, m = lying(dict(kind='back', base=(-40, -80), s=1.15, turn=-.4), tail=tl)
    put(nm, p, pose(lie=1, head=1.1, look=1, ear=1, tail=.25, wag=wg), m, 'looks in through the door' + (' (tail %+d)' % wg if wg else ''), 'look')

# refusal lying, the tail curled in (facing left first, then flopped so the back is to the door)
TAIL_CURL = [(54, -40), (40, -14), (14, -8), (-12, -6)]
p, m = lying(dict(base=(-62, -64), pitch=-.2, ears='flat', s=1.1), tail=TAIL_CURL)
put('_lie_tuck', p, pose(lie=1, crouch=.5, head=.15, ear=0, tail=1.15), m, '', 'lie')
p, m = lying(dict(base=(-62, -38), pitch=-.04, ears='flat', s=1.1), tail=TAIL_CURL)
put('_rest_tuck', p, pose(lie=1, crouch=.5, head=.15, rest=1, ear=0, tail=1.15), m, '', 'lie')
p, m = profile_dog(W=(-34, -100), R=(30, -62), d=52, head=dict(base=(-64, -90), pitch=-.4, ears='flat', s=1.1),
                   paws={'fn': (-48, 0), 'ff': (-32, 0), 'hn': (0, 0), 'hf': (0, 0)}, tail=TAIL_CURL,
                   hind_joints={'hn': [(30, -40), (4, -24), (36, -8), (12, -3)], 'hf': [(26, -40), (6, -26), (32, -9), (10, -5)]}, tuck=.9)
put('_sit_tuck', p, pose(lie=.5, crouch=.5, head=.15, ear=0, tail=1.15), m, '', 'lie')
flop('_sit_tuck', 'sink_R', dict(yaw=180), 'refuses: goes down with its back to the door', 'lieR')
flop('_lie_tuck', 'lie_R', dict(yaw=180), 'refuses: lies with its back to the door', 'lieR')
flop('_rest_tuck', 'rest_R', dict(yaw=180), 'refuses: chin down, back to the door', 'lieR')

# turns back to look: lying with its back to the door, the head comes round over the shoulder
p, m = lying(dict(base=(-20, -84), pitch=.05, ears='half', s=1.1, flip=True), tail=TAIL_CURL)
put('_lookback', p, pose(), m, '', 'lie')
flop('_lookback', 'lookback_R', dict(yaw=180, lie=1, head=.5, ear=.6, tail=1.0, over=1),
     'turns back to look: head over the shoulder to the door', 'lieR')
# asked for by the curator (unexplained cluster at 7.6 s, see ledger): half up, still turned away, head to the door
p, m = profile_dog(W=(-34, -100), R=(30, -62), d=52, head=dict(base=(-14, -118), pitch=.05, ears='half', s=1.1, flip=True),
                   paws={'fn': (-48, 0), 'ff': (-32, 0), 'hn': (0, 0), 'hf': (0, 0)}, tail=[(40, -44), (54, -26), (70, -12), (90, -6)],
                   hind_joints={'hn': [(30, -40), (4, -24), (36, -8), (12, -3)], 'hf': [(26, -40), (6, -26), (32, -9), (10, -5)]}, tuck=.9)
put('_situp', p, pose(), m, '', 'lie')
flop('_situp', 'situp_R', dict(yaw=180, lie=.5, crouch=.3, head=.6, ear=.6, tail=.9, over=1), 'gets up: half up, back still to the door, looking round', 'lieR')
# rises, body still away, head to the door
p, m = profile_dog(W=(-34, -100), R=(42, -96), d=56, head=dict(base=(-16, -116), pitch=.05, ears='up', s=1.1, flip=True),
                   paws={'fn': (-50, 0), 'ff': (-32, 0), 'hn': (54, 0), 'hf': (40, 0)}, tail=TAIL_LOW)
put('_rise', p, pose(), m, '', 'stand')
flop('_rise', 'rise_R', dict(yaw=180, crouch=.2, head=.85, ear=1, tail=.7, over=1), 'gets up, still turned away, looking back', 'stand')


# ---------------------------------------------------------------- the person (same kit, same ink)
from personparts import person


def pp(**k):
    base = dict(sit=0, reach=0, low=0, mouth=0, walk=0, phase=None)
    base.update(k)
    return base


p, m = person()
put('P_stand', p, pp(), m, 'stands in the doorway', 'person')
p, m = person(lean=.08, head_pitch=-.12, mouth=1, armN=(.35, -.25), armF=(.1, .1))
put('P_call', p, pp(mouth=1), m, 'calls: come here', 'person')
p, m = person(lean=.32, head_pitch=-.2, mouth=.9, armN=(1.35, .15), armF=(.25, .1), footN=(30, 0), footF=(-16, 0))
put('P_reach', p, pp(mouth=.9, reach=1), m, 'calls again and reaches for it', 'person')
PSTRIDE = .64 * S     # px per two steps
NPW = 6
for k in range(NPW):
    feet = []
    for o in (0.0, .5):
        psi = (k / NPW + o) % 1.0
        if psi < .6:
            fx = PSTRIDE * .6 / 2 - PSTRIDE * psi; fy = 0.0
        else:
            u = (psi - .6) / .4; fx = -PSTRIDE * .6 / 2 + PSTRIDE * .6 * u; fy = -10 * math.sin(math.pi * u)
        feet.append((round(fx, 1), round(fy, 1)))
    sw = math.sin(2 * math.pi * k / NPW)
    p, m = person(lean=.06, armN=(-.3 * sw, .15), armF=(.3 * sw, .1), footN=feet[0], footF=feet[1], face=-1)
    m['gait'] = {'k': k, 'n': NPW, 'dir': -1, 'stride_px': round(PSTRIDE, 2), 'who': 'person'}
    m['feet'] = {'n': [-feet[0][0], feet[0][1]], 'f': [-feet[1][0], feet[1][1]]}
    put('P_walk_%d' % k, p, pp(walk=1, phase=2 * math.pi * k / NPW), m, 'steps aside %d/%d' % (k, NPW), 'person')
p, m = person(hip=(0, -118), lean=.25, armN=(.6, -.3), armF=(.5, -.3), footN=(30, 0), footF=(18, 0), sit=False)
put('P_sitting', p, pp(sit=.5), m, 'sits down beside the door', 'person')
p, m = person(hip=(0, -88), lean=.05, armN=(.5, -.6), armF=(.45, -.7), footN=(56, 0), footF=(46, 0), sit=True)
put('P_sit', p, pp(sit=1), m, 'sits beside the door', 'person')
p, m = person(hip=(0, -88), lean=.5, head_pitch=.05, armN=(.5, .2), armF=(.45, -.7), footN=(56, 0), footF=(46, 0), sit=True)
put('P_sit_low', p, pp(sit=1, low=1), m, 'offers a hand, low', 'person')
p, m = person(hip=(0, -88), lean=.5, head_pitch=.12, mouth=.45, armN=(.5, .2), armF=(.45, -.7), footN=(56, 0), footF=(46, 0), sit=True)
put('P_sit_soft', p, pp(sit=1, low=1, mouth=.45), m, "says softly: it's all right", 'person')

for k in [k for k in D if k.startswith('_')]:
    D[k]['meta']['hidden'] = True

if __name__ == '__main__':
    vis = {k: v for k, v in D.items() if not k.startswith('_')}
    json.dump({'about': 'Illustration bank, PAE-02 SCION 14 Pose2Pose. Film px at 190 px/m, origin on the ground under the dog.',
               'S': S, 'stride_px': STRIDE, 'nwalk': NWALK, 'drawings': vis}, open(OUT, 'w'))
    print('bank', len(vis), 'drawings ->', OUT)
