"""SCION 20 · 02: the exposure sheet (xsheet), built from the score.
For each of the 768 scene frames it writes which drawing is exposed in every column (dog_body, dog_head, dog_ear,
dog_tail, person, person_mouth), the peg values (dog x and mirror, head joint, person x, door swing), the deformation
chain values (tail rotations; the neck curve is solved from the pegs) and the light. It also writes the track breakdown
(voice syllables, footfalls, tail thumps, door) that the sound script reads, so picture and sound share one timing.
Outputs: scene/xsheet.json, scene/xsheet.tsv (a readable exposure sheet, holds marked '|'), scene/track.json"""
import json, math, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(D))
SC = json.load(open(os.path.join(R, 'handmade/score/threshold-score.json')))
LIB = json.load(open(os.path.join(D, 'scene/library.json')))['elements']
F = SC['frames']; N = len(F); FPS = 24
STRIDE = 0.55; NW = 16
clamp = lambda v, a, b: max(a, min(b, v))
lerp = lambda a, b, t: a + (b - a) * t
sm = lambda t: (lambda u: u * u * (3 - 2 * u))(clamp(t, 0, 1))
fr = lambda t: int(round(t * FPS))

# ---------------- head poses (joint in BODY-local metres, rotation in radians, + = nose down for a left-facing head)
def neck(body):
    return LIB['dog_body'][body]['anchors']['neck']
def head_joint(body, pose):
    ax, ay = neck(body)
    P = {  # name: (angle deg from +x in native left-facing frame, length, rot)
        'up': (126, 0.135, -0.05), 'mid': (165, 0.14, 0.12), 'low': (200, 0.13, 0.28), 'stalk': (222, 0.17, 0.26),
    }
    if pose in P:
        a, L, r = P[pose]
        return ax + L * math.cos(math.radians(a)), ay + L * math.sin(math.radians(a)), r
    if pose == 'lie_up': return ax - 0.06, ay + 0.105, -0.02
    if pose == 'lie_mid': return ax - 0.075, ay + 0.03, 0.14
    if pose == 'lie_low': return ax - 0.06, ay - 0.10, 0.12
    if pose == 'rest': return ax - 0.065, ay - 0.19, 0.06
    if pose == 'look_in': return ax - 0.12, ay + 0.035, 0.06
    if pose == 'look_back': return ax + 0.07, ay + 0.075, 0.08   # over the shoulder (head mirrored against the body)
    if pose == 'front': return ax, ay + 0.085, 0.0
    if pose == 'q3front': return ax - 0.035, ay + 0.085, 0.0
    if pose == 'back': return ax, ay + 0.07, 0.0
    if pose == 'q3back': return ax - 0.03, ay + 0.07, 0.0
    raise KeyError(pose)

def ear_state(e):
    return 'flat' if e < 0.3 else ('half' if e < 0.75 else 'pricked')
def tail_state(t):
    return 'high' if t < 0.25 else 'mid' if t < 0.62 else 'low' if t < 1.0 else 'tucked'

# ---------------- voice (the track breakdown): syllables (t0, t1, mouth, vowel, level dB re call)
VOICE = [
    # call 1: "Come here! Come on!"
    (1.00, 1.22, 'wide', 'uh', 0, 'call'), (1.28, 1.62, 'open', 'ee', 0, 'call'), (1.80, 1.98, 'wide', 'uh', -1, 'call'), (2.03, 2.28, 'open', 'oh', -1, 'call'),
    # call 2, with the reach: "Come HERE! Come here!"
    (3.42, 3.62, 'wide', 'uh', 1, 'call'), (3.68, 4.02, 'wide', 'ee', 2, 'call'), (4.14, 4.30, 'wide', 'uh', 0, 'call'), (4.34, 4.58, 'open', 'ee', 0, 'call'),
    # soft: "It's all right."  "it's all right."
    (7.45, 7.57, 'soft', 'ih', -12, 'soft'), (7.61, 7.84, 'soft', 'aw', -12, 'soft'), (7.90, 8.24, 'soft', 'ai', -13, 'soft'),
    (8.62, 8.72, 'soft', 'ih', -14, 'soft'), (8.76, 8.96, 'soft', 'aw', -14, 'soft'), (9.01, 9.34, 'soft', 'ai', -15, 'soft'),
    (10.45, 10.56, 'soft', 'ih', -14, 'soft'), (10.60, 10.82, 'soft', 'aw', -14, 'soft'), (10.88, 11.30, 'soft', 'ai', -15, 'soft'),
    # "Come in."
    (26.45, 26.68, 'soft', 'uh', -12, 'soft'), (26.76, 27.12, 'soft', 'ih', -13, 'soft'),
]
SUBS = [(1.0, 2.45, 'Come here! Come on!'), (3.4, 4.75, 'Come here! Come here!'), (7.4, 9.5, 'It’s all right. It’s all right.'),
        (10.4, 11.6, 'It’s all right…'), (26.4, 27.6, 'Come in.')]

def mouth_at(t):
    for s in VOICE:
        if s[0] <= t < s[1]: return s[2]
    return 'closed'
def sub_at(t):
    for a, b, s in SUBS:
        if a <= t < b: return s
    return ''

# ---------------- dog: one record per frame
rows = []
foot_events, thump_events = [], []
prev_phi = None
blinks = set()
for t0 in (0.55, 3.1, 9.6, 12.2, 13.9, 19.6, 25.1, 29.0):
    for k in range(3): blinks.add(fr(t0) + k)

for i in range(N):
    f = F[i]; t = i / FPS; d = f['dog']; a = d['act']; x = d['x']
    r = dict(i=i, t=round(t, 3), x=x, mirror=1, body='stand', head='profile_open', head_pose='up', head_rel=1, head_behind=False,
             ear=ear_state(a['ear']), tail=tail_state(a['tail']), tail_front=False, wag=0.0, state=d['state'], beat='')
    # ---- A. opening: watch, the call, backing away, watching again (facing the door = native left)
    if i < 82:
        mv = a['moving'] > 0.25
        r['head_pose'] = 'up' if a['head'] > 0.75 else ('mid' if a['head'] > 0.5 else 'low')
        if mv:
            phi = (-x / STRIDE) % 1.0
            q = round(phi * NW) % NW
            dphi = ((phi - q / NW + 0.5) % 1.0) - 0.5
            r['x_peg'] = x + STRIDE * dphi
            r['body'] = ('cwalk' if a['crouch'] > 0.55 else 'walk') + '%02d' % q
            r['beat'] = 'backs away' if d['state'] == 'retreat' else 'eases back'
            if prev_phi is not None:
                for leg, off in (('nh', 0), ('nf', .25), ('fh', .5), ('ff', .75)):
                    # backing away: phase decreases; a foot touches down when (phi+off) crosses duty from above
                    a0, a1 = (prev_phi + off) % 1, (phi + off) % 1
                    if a0 > 0.62 >= a1 and a0 - a1 < 0.5: foot_events.append(dict(t=round(t, 3), leg=leg, who='dog', level=-8))
            prev_phi = phi
        else:
            r['body'] = 'crouch' if a['crouch'] > 0.5 else 'stand'
            prev_phi = None
            r['beat'] = 'watches'
        if i < 24: r['beat'] = 'watches'
        r['head'] = 'profile_closed' if i in blinks else 'profile_open'
    # ---- B. the refusal turn: through the BACK view (rump to camera), whole drawings, 3 frames each
    elif i < 91:
        k = i - 82
        r['ear'] = 'flat'; r['tail'] = 'tucked_back'; r['tail_front'] = True; r['head_behind'] = True; r['beat'] = 'turns its back'
        if k < 3: r.update(body='q3back_c', head='q3back', head_pose='q3back', mirror=1)
        elif k < 6: r.update(body='back_c', head='back', head_pose='back', mirror=1)
        else: r.update(body='q3back_c', head='q3back', head_pose='q3back', mirror=-1)
    # ---- C/D. back turned: crouched, then lies down facing away (tail toward the door), chin on paws
    elif i < 179:
        r['mirror'] = -1; r['ear'] = 'flat'; r['beat'] = 'back turned'
        if i < 104: r.update(body='crouch', head_pose='low', tail='tucked')
        elif i < 110: r.update(body='lower1', head_pose='low', tail='low')
        elif i < 116: r.update(body='lower2', head_pose='lie_low', tail='lie')
        else:
            r.update(body='lie', tail='lie')
            if i < 140: r['head_pose'] = 'lie_low'
            else: r['head_pose'] = 'rest'
        # eyes: open, then shut while it sulks, open again when the light comes
        r['head'] = 'profile_closed' if 146 <= i < 165 else 'profile_open'
        # an ear flicks at the door's creak and at the low hand (registers, does not turn)
        if 150 <= i < 154 or 170 <= i < 173: r['ear'] = 'half'
    # ---- E. head leads (7.458): the head comes round through the FACE view while the body is still down
    elif i < 186:
        k = i - 179
        r.update(mirror=-1, body='lie', tail='lie', ear='half', beat='turns back to look')
        if k < 2: r.update(head='q3front_open', head_pose='look_back', head_rel=1)
        elif k < 4: r.update(head='front_open', head_pose='look_back', head_rel=1)
        elif k < 6: r.update(head='q3front_open', head_pose='look_back', head_rel=-1)
        else: r.update(head='profile_open', head_pose='look_back', head_rel=-1, ear='pricked')
    # ---- F. the body follows: rises still facing away, head looking back, then turns through the FRONT view
    elif i < 204:
        r.update(ear='pricked', tail='mid', beat='turns back to look')
        if i < 189: r.update(mirror=-1, body='lower2', head='profile_open', head_pose='look_back', head_rel=-1, tail='lie')
        elif i < 192: r.update(mirror=-1, body='lower1', head='profile_open', head_pose='look_back', head_rel=-1, tail='low')
        elif i < 195: r.update(mirror=-1, body='stand', head='profile_open', head_pose='look_back', head_rel=-1)
        elif i < 198: r.update(mirror=-1, body='q3front', head='q3front_open', head_pose='q3front', head_rel=-1)
        elif i < 201: r.update(mirror=1, body='front', head='q3front_open', head_pose='front', head_rel=1)
        else: r.update(mirror=1, body='q3front', head='profile_open', head_pose='q3front', head_rel=1)
    # ---- G. watching, standing, facing the door: it listens, tilts, considers
    elif i < 353:
        r.update(body='stand', ear=ear_state(a['ear']), tail='mid', beat='watches')
        r['head_pose'] = 'up'
        r['head'] = 'profile_closed' if i in blinks else 'profile_open'
        if 250 <= i < 252 or 186 <= i < 188: r['ear'] = 'half'
        if 300 <= i < 330: r['head_pose'] = 'mid'
        r['wag'] = 0.25 if i > 320 else 0.0
    # ---- H. comes, head low (stalking walk, head below the line of the back)
    elif i < 571:
        mv = a['moving'] > 0.05 or i >= 355
        r.update(ear='half', tail='low', head_pose='stalk', beat='comes, head low')
        phi = (-x / STRIDE) % 1.0
        q = round(phi * NW) % NW
        dphi = ((phi - q / NW + 0.5) % 1.0) - 0.5
        r['x_peg'] = x + STRIDE * dphi
        r['body'] = 'lwalk%02d' % q
        if prev_phi is not None:
            for leg, off in (('nh', 0), ('nf', .25), ('fh', .5), ('ff', .75)):
                a0, a1 = (prev_phi + off) % 1, (phi + off) % 1
                if a1 < a0 and (a0 - a1) > 0.5: foot_events.append(dict(t=round(t, 3), leg=leg, who='dog', level=-10))
        prev_phi = phi
        r['wag'] = a['wag']
        r['head'] = 'profile_closed' if i in blinks else 'profile_open'
    # ---- I. lies down across the sill
    elif i < 634:
        prev_phi = None
        r.update(ear='half', tail='lie', beat='lies down across the sill')
        if i < 577: r.update(body='lower1', head_pose='low', tail='low')
        elif i < 583: r.update(body='lower2', head_pose='lie_up')
        else:
            r['body'] = 'lie'
            h = a['head']  # 0.7 -> 0.3 by 26.0
            r['head_pose'] = 'lie_up' if h > 0.6 else ('lie_mid' if h > 0.42 else 'lie_low')
        r['wag'] = a['wag'] * 0.6
        r['head'] = 'profile_closed' if i in blinks else 'profile_open'
    # ---- J. "come in": ears up, the head comes up and turns IN, away from us, muzzle into the lit room
    elif i < 677:
        r.update(body='lie', tail='lie', beat='looks in')
        if i < 636: r.update(head_pose='lie_low', ear='half')
        elif i < 640: r.update(head_pose='lie_mid', ear='pricked')
        elif i < 642: r.update(head_pose='lie_up', ear='pricked')
        else: r.update(head='deep', head_pose='look_in', ear='pricked')
        r['wag'] = a['wag']
    # ---- K. settles, chin on the paws, and stays
    else:
        r.update(body='lie', tail='lie', beat='settles and stays')
        r['ear'] = 'half' if i < 700 else 'flat'
        if i < 681: r['head_pose'] = 'lie_up'
        elif i < 686: r['head_pose'] = 'lie_mid'
        elif i < 690: r['head_pose'] = 'lie_low'
        else: r['head_pose'] = 'rest'
        r['head'] = 'profile_closed' if (i >= 724 or i in blinks) else 'profile_open'
        if 742 <= i < 745: r['ear'] = 'half'   # an ear flicks at the room sounds, eyes stay shut
        r['wag'] = a['wag']
    rows.append(r)

# ---- head joint, on twos in the holds (ones in turns and walks)
for r in rows:
    hx, hy, hr = head_joint(r['body'], r['head_pose'])
    r['hx'], r['hy'], r['hrot'] = round(hx, 4), round(hy, 4), round(hr, 4)
# smooth the head joint between pose changes (on twos), never across a drawing change of the body's view
for i in range(1, N):
    a_, b_ = rows[i - 1], rows[i]
    same_view = LIB['dog_body'][a_['body']]['view'] == LIB['dog_body'][b_['body']]['view'] and a_['head_rel'] == b_['head_rel'] and a_['mirror'] == b_['mirror']
    if same_view and b_['head'].split('_')[0] == a_['head'].split('_')[0] and not b_['body'].startswith(('lwalk', 'cwalk', 'walk')):
        if i % 2 == 1:   # odd frames hold the previous exposure (twos)
            b_['hx'], b_['hy'], b_['hrot'] = a_['hx'], a_['hy'], a_['hrot']
        else:            # ease 55% toward the target pose per exposure
            b_['hx'] = round(lerp(a_['hx'], b_['hx'], 0.55), 4); b_['hy'] = round(lerp(a_['hy'], b_['hy'], 0.55), 4); b_['hrot'] = round(lerp(a_['hrot'], b_['hrot'], 0.55), 4)
# head tilt while listening (10.45-11.2): the tilt is a peg rotation on the held drawing
for i in range(251, 270):
    rows[i]['hrot'] = round(rows[i]['hrot'] - 0.16 * math.sin(math.pi * (i - 251) / 19), 4)
# walking head bob (walk drawings carry the body bob; the head peg follows it)
for r in rows:
    if r['body'][:-2] in ('walk', 'cwalk', 'lwalk'):
        q = int(r['body'][-2:]); r['hy'] = round(r['hy'] + 0.009 * math.cos(4 * math.pi * q / NW) - 0.006 * math.sin(2 * math.pi * q / NW), 4)
# breathing: a body peg y on twos in the holds
for r in rows:
    i = r['i']; br = 0.0
    if r['body'] in ('stand', 'lie', 'crouch'):
        br = 0.004 * math.sin(2 * math.pi * (i - i % 2) / FPS / (1.6 if r['body'] == 'lie' else 1.2))
    r['y'] = round(br, 4)
    r.setdefault('x_peg', r['x'])
    r['x_peg'] = round(r['x_peg'], 4)
# tail chain: wag rotations per joint (6 joints); thumps when a lying tail strikes the floor
prev = None
for r in rows:
    i = r['i']; t = i / FPS; w = r['wag']
    sway = 0.05 * math.sin(2 * math.pi * t / 2.7)
    if r['tail'] == 'lie':
        ph = 2 * math.pi * 2.0 * t
        rots = [0.0, 0.0, -0.42 * w * (0.5 + 0.5 * math.sin(ph)), -0.15 * w * (0.5 + 0.5 * math.sin(ph - 0.6)), 0.0, 0.0]
        lift = 0.5 + 0.5 * math.sin(ph)
        if w > 0.3 and prev is not None and prev > 0.08 and lift <= 0.08: thump_events.append(dict(t=round(t, 3), level=-14 + 6 * w))
        prev = lift if w > 0.3 else None
    else:
        ph = 2 * math.pi * 2.3 * t
        rots = [sway * 0.5 + 0.25 * w * math.sin(ph), 0.25 * w * math.sin(ph - 0.7), 0.2 * w * math.sin(ph - 1.4), 0.1 * w * math.sin(ph - 2.1), 0, 0]
        prev = None
    r['tail_rots'] = [round(v, 4) for v in rots]

# ---------------- person, door, light
P = []
for i in range(N):
    f = F[i]; t = i / FPS; p = f['person']
    if 24 <= i < 56: d = 'call'
    elif 82 <= i < 86: d = 'reach1'
    elif 86 <= i < 111: d = 'reach2'
    elif 111 <= i < 115: d = 'reach1'
    elif 130 <= i < 150: d = 'step1' if ((i - 130) // 4) % 2 == 0 else 'step2'
    elif 150 <= i < 158: d = 'sitdown'
    elif 158 <= i < 163: d = 'sit'
    elif 163 <= i < 172: d = 'sit_low1'
    elif i >= 172: d = 'sit_low'
    else: d = 'stand'
    # door swing (degrees): ajar 22, swings open 6.2-6.9 with a small settle
    if t < 6.2: ang = 22
    else: u = clamp((t - 6.2) / 0.7, 0, 1); ang = 22 + 80 * sm(u) + 5 * math.sin(math.pi * clamp((t - 6.75) / 0.5, 0, 1)) * (t > 6.75)
    spill = sm((ang - 22) / 76)
    # camera: wide until 23.0 s, then a slow push-in on the doorway (ease 23.0-25.2), held to the end
    u = sm((t - 23.0) / 2.2)
    cz, ccx, ccy = lerp(1.0, 1.55, u), lerp(640, 430, u), lerp(360, 466, u)
    v = sm((t - 26.2) / 0.8) * (1 - sm((t - 28.7) / 1.2))   # a closer push while it looks in, then back
    cz, ccx, ccy = lerp(cz, 1.9, v), lerp(ccx, 445, v), lerp(ccy, 520, v)
    P.append(dict(cam_z=round(cz, 4), cam_cx=round(ccx, 2), cam_cy=round(ccy, 2), px=round(p['x'], 4), person=d, mouth=mouth_at(t), door=round(ang, 2), spill=round(spill, 4), sub=sub_at(t)))

# ---------------- write
frames = []
for r, p in zip(rows, P):
    frames.append(dict(i=r['i'], t=r['t'], score_state=r['state'], x=r['x'], x_peg=r['x_peg'], y=r['y'], mirror=r['mirror'],
                       body=r['body'], head=r['head'], ear='%s_%s' % (LIB['dog_head'][r['head']]['view'], r['ear']), tail=r['tail'],
                       hx=r['hx'], hy=r['hy'], hrot=r['hrot'], head_rel=r['head_rel'], head_behind=r['head_behind'], tail_front=r['tail_front'],
                       tail_rots=r['tail_rots'], beat=r['beat'], **p))
track = dict(voice=[dict(t0=a, t1=b, mouth=m, vowel=v, level=l, kind=k) for a, b, m, v, l, k in VOICE], subtitles=SUBS,
             footfalls=foot_events, thumps=thump_events,
             person_steps=[dict(t=round(i / FPS, 3)) for i in range(130, 150, 4)], sit=6.3, door=dict(latch=6.15, swing=[6.2, 6.95]))
json.dump(dict(about='SCION 20 exposure sheet: one row per scene frame (24 fps, 768 frames). Columns name the drawing exposed in each element; pegs in metres.',
               mapping=dict(X0=315, K=198, FLOOR=620, dog_scale=1.12, note='base screen: bx = X0 + K * x, by = FLOOR - K * y ; camera: screen = (b - (cam_cx, cam_cy)) * cam_z + (640, 360)'),
               columns=['body', 'head', 'ear', 'tail', 'person', 'mouth'], frames=frames), open(os.path.join(D, 'scene/xsheet.json'), 'w'))
json.dump(track, open(os.path.join(D, 'scene/track.json'), 'w'), indent=1)
# readable exposure sheet
with open(os.path.join(D, 'scene/xsheet.tsv'), 'w') as fo:
    cols = ['body', 'head', 'ear', 'tail', 'person', 'mouth']
    fo.write('frame\ttime\t' + '\t'.join(['dog_' + c if c in ('body', 'head', 'ear', 'tail') else c for c in cols]) + '\tdog_x\tmirror\tdoor\taction\n')
    prevv = {}
    for fm in frames:
        cells = []
        for c in cols:
            v = fm[c] + ('' if c != 'body' and c != 'head' else ('' if fm['mirror'] == 1 else ''))
            if c in ('body',): v = fm['body'] + ('·R' if fm['mirror'] == -1 else '')
            if c == 'head': v = fm['head'] + ('·R' if fm['mirror'] * fm['head_rel'] == -1 else '')
            cells.append('|' if prevv.get(c) == v else v); prevv[c] = v
        fo.write('%d\t%.3f\t%s\t%.3f\t%d\t%.0f\t%s\n' % (fm['i'] + 1, fm['t'], '\t'.join(cells), fm['x_peg'], fm['mirror'], fm['door'], fm['beat']))
print('xsheet', len(frames), 'frames; footfalls', len(foot_events), 'thumps', len(thump_events))
