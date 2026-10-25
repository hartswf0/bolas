"""SCION 17 // timing and acting director v1: the score in, a performance out (one record per scene frame).

The score says what the dog decides and when. The director decides how this cast plays it in this grammar:
which drawing is up (direction state, posture drawing, expression), held on twos; where the planted feet are; what the
person does with her body, voice and face; which door drawing is up; and which framing (stage template camera) is cut in.
It also emits the sound events (paw contacts, door, flop, tail thumps) so the sound is cut to the same picture.
"""
import json, math, os
import numpy as np
import dialogue
import dog as D

VERSION = 'director-v1'
HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = json.load(open(os.path.join(HERE, '..', '..', 'score', 'threshold-score.json')))
FPS = 24
N = len(SCORE['frames'])
STRIDE = 0.42                                       # metres per gait cycle
LEG_PHASE = {'hindn': 0.0, 'frontn': 0.25, 'hindf': 0.5, 'frontf': 0.75}
CUT_CLOSE = 606                                     # 25.25 s: cut from the porch wide to the sill close

T_RETREAT, T_WATCH1, T_REFUSE, T_LOOK, T_APPROACH, T_LIE, T_IN = 1.0, 2.333, 3.417, 7.458, 14.708, 23.792, 26.4


def lerp(a, b, u): return a + (b - a) * max(0.0, min(1.0, u))
def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def head_stop_stand(h):
    return 'UP' if h >= 0.75 else 'MID' if h >= 0.5 else 'LOW' if h >= 0.25 else 'DOWN'


def ear_of(e):
    return 'PRICK' if e >= 0.75 else 'HALF' if e >= 0.35 else 'FLAT'


# ---------------------------------------------------------------- gait: feet are placed on the porch and stay there
def gait(d, moving):
    """d: distance walked forward (m) along the facing direction. Returns local foot positions (cm, facing-left frame)
    and the set of legs in stance."""
    feet, stance = {}, set()
    for leg, off in LEG_PHASE.items():
        p = (d / STRIDE + off) % 1.0
        if p < 0.65:
            r = STRIDE * (0.325 - p); lift = 0.0; stance.add(leg)
        else:
            q = (p - 0.65) / 0.35
            r = STRIDE * (-0.325 + 0.65 * (0.5 - 0.5 * math.cos(math.pi * q)))
            lift = 4.5 * math.sin(math.pi * q) * min(1.0, moving * 1.5)
            if moving < 0.05: stance.add(leg)
        kind = 'front' if leg.startswith('front') else 'hind'
        hx = D.LEG[kind]['hip'][0] + (-1.5 if leg.endswith('f') else 0.0)
        feet[leg] = (hx - r * 100.0, 0.5 + lift)
    return feet, stance


def body_height(H, feet, stance):
    """lower the body just enough that every planted foot reaches the floor (the bob comes from the feet)"""
    Hm = H
    for leg in stance:
        kind = 'front' if leg.startswith('front') else 'hind'
        g = D.LEG[kind]; L = g['a'] + g['b'] - 0.4
        dx = feet[leg][0] - g['hip'][0]
        reach = math.sqrt(max(L * L - dx * dx, 1.0))
        Hm = min(Hm, reach + feet[leg][1] - g['hip'][1])
    return Hm


# ---------------------------------------------------------------- person track (her circumstances, from the score's timeline)
def person_at(t, dog_head_world):
    """returns (world x, pose dict, posture) for Maren at scene time t"""
    pose = dict(posture='STAND', pelvis=(0, 67), lean=0.0, eye='OPEN', brow='NEUTRAL', tilt=0.0, palm_up=False)
    x = -0.28
    feet_world = {'n': -0.18, 'f': -0.36}
    # steps aside: planted feet, one at a time
    steps = [(5.40, 5.60, 'f', -0.36, -0.74), (5.60, 5.80, 'n', -0.18, -0.86), (5.80, 5.96, 'f', -0.74, -1.02)]
    lifts = {'n': 0.0, 'f': 0.0}
    for t0, t1, ft, a, b in steps:
        if t >= t1: feet_world[ft] = b
        elif t >= t0:
            u = (t - t0) / (t1 - t0); feet_world[ft] = lerp(a, b, smooth(u)); lifts[ft] = 7 * math.sin(math.pi * u)
    if t < 5.40: x = -0.28
    elif t < 5.96: x = (feet_world['n'] + feet_world['f']) / 2 - 0.01 + (0.0)
    else: x = -0.95
    pose['feet'] = {k: ((feet_world[k] - x) * 100.0, lifts[k]) for k in ('n', 'f')}
    sh = (12, 119)
    pose['hands'] = {'n': (16, 66), 'f': (-14, 66)}
    # calls and reach (commands)
    if 1.0 <= t < 1.95:
        pose['lean'] = 7; pose['brow'] = 'UP'
        beck = int((t - 1.0) / 0.25) % 2
        pose['hands']['n'] = (48, 92) if beck == 0 else (40, 104)
    if 2.6 <= t < 3.4: pose['brow'] = 'SAD'
    if 3.4 <= t < 4.75:
        u = smooth((t - 3.45) / 0.5) if t < 4.6 else 1 - smooth((t - 4.6) / 0.15)
        pose['lean'] = 16 * u; pose['brow'] = 'UP'
        pose['hands']['n'] = (lerp(16, 70, u), lerp(66, 118, u))
    if 4.75 <= t < 5.4: pose['brow'] = 'SAD'; pose['tilt'] = -4
    if 4.95 <= t < 5.25: pose['eye'] = 'HALF'
    # pushes the door wide while she lowers herself
    if 5.92 <= t < 6.34:
        u = smooth((t - 5.92) / 0.2)
        pose['lean'] = 18 * u
        pose['hands']['n'] = (lerp(16, 72, u), lerp(66, 102, u))
    posture = 'STAND'
    if 6.34 <= t < 6.54:
        posture = 'CROUCH'; x = -1.10
        pose.update(posture='CROUCH', pelvis=(0, 42), lean=18, feet={'n': (22, 0), 'f': (-6, 0)}, hands={'n': (34, 40), 'f': (-2, 30)})
    elif t >= 6.54:
        posture = 'SIT'; x = -1.25
        pose.update(posture='SIT', pelvis=(0, 13), lean=14, feet={'n': (56, 0), 'f': (48, 0)}, hands={'n': (34, 40), 'f': (34, 38)})
        if t >= 6.80:
            u = smooth((t - 6.8) / 0.45)
            pose['hands']['n'] = (lerp(34, 82, u), lerp(40, 8, u)); pose['lean'] = lerp(14, 20, u)
            pose['palm_up'] = u > 0.6
            pose['eye'] = 'HALF' if t >= 7.2 else 'OPEN'
            pose['brow'] = 'SOFT'; pose['tilt'] = 6 * u
    # mouth from the phoneme chart
    m, li = dialogue.mouth_at(t)
    if m == 'REST' and t >= 7.0: m = 'SMILE'
    if 23.4 <= t < 26.3 and m == 'SMILE': m = 'SMILE'
    pose['mouth'] = m
    # blinks (substitution, two frames on)
    for bt in (0.7, 2.9, 5.1, 9.85, 13.15, 16.0, 19.4, 22.6, 25.0, 29.45, 31.3):
        if bt <= t < bt + 0.09: pose['eye'] = 'CLOSED'
    # eyes on the dog
    return x, pose, posture


def person_gaze(px, py, hx, hy):
    dx, dy = hx - px, hy - py; n = math.hypot(dx, dy) or 1.0
    return (dx / n, max(-0.8, min(0.8, dy / n * 1.6)))


# ---------------------------------------------------------------- the dog
def dog_at(j, gait_state):
    """the performance of scene frame j (a pose frame: frames are held on twos)"""
    f = SCORE['frames'][j]; s = f['dog']; a = s['act']; t = f['t']
    state = s['state']; x = s['x']
    pose = dict(body='P', draw='STAND', mirror=False, head_view='P', head_mirror=False, head_stop=head_stop_stand(a['head']),
                ear=ear_of(a['ear']), eye='OPEN', brow='UP', tail=D.tail_angle(a['tail'], 0.0, 0.0), tilt=0.0)
    H = 40.0 - 9.0 * a['crouch']
    look = 'person'; posture = 'stand'; gaze_target = 'person'
    # ------------------------------------------------ phases
    if t < T_RETREAT:
        pass
    elif t < T_WATCH1:                                   # backs away from the call
        pose.update(eye='WIDE', brow='WORRY', ear='FLAT' if t >= 1.04 else 'HALF')
        posture = 'retreat'
    elif t < T_REFUSE:
        pose.update(brow='WORRY')
    elif t < T_LOOK:                                     # turns its back: substitution through drawn direction states
        pose.update(brow='DOWN', ear='FLAT' if t < 3.9 else 'HALF', eye='HALF')
        posture = 'turn'
        if t < 3.50: pose.update(body='Q', head_view='Q', eye='WIDE', brow='WORRY', head_stop='MID'); gaze_target = 'floor_away'
        elif t < 3.58: pose.update(body='F', head_view='F'); gaze_target = 'floor_away'
        else:
            pose.update(mirror=True, head_stop='LOW'); gaze_target = 'away'; posture = 'stand'
            if t >= 4.42:
                posture = 'lie'
                if t < 4.58: H = 25.0
                elif t < 4.75: H = 18.0
                else: pose.update(draw='LIE', head_stop='L_UP' if a['rest'] < 0.5 else 'L_CHIN')
                if t >= 6.0: pose['eye'] = 'CLOSED'
                if 6.25 <= t < 7.4: pose.update(ear='PRICK' if t < 6.6 else 'HALF', eye='HALF' if t >= 6.3 else 'CLOSED')
                if t >= 7.38: pose.update(eye='OPEN', ear='PRICK')
    elif t < T_APPROACH:                                 # turns back to look: the head first, then the body
        pose.update(brow='UP', ear='PRICK')
        if t < 7.54: pose.update(draw='LIE', mirror=True, head_view='F', head_stop='L_UP'); gaze_target = 'door'; posture = 'lie'
        elif t < 7.62: pose.update(draw='LIE', mirror=True, head_mirror=True, head_stop='L_UP'); gaze_target = 'person'; posture = 'lie'
        elif t < 7.75: pose.update(mirror=True, head_mirror=True, head_stop='UP'); H = 22.0; posture = 'rise'
        elif t < 8.0: pose.update(mirror=True, head_mirror=True, head_stop='UP'); posture = 'stand'
        elif t < 8.08: pose.update(body='Q', mirror=True, head_view='F'); posture = 'turn'
        elif t < 8.17: pose.update(body='F', head_view='F'); posture = 'turn'
        elif t < 8.25: pose.update(body='Q', head_view='Q'); posture = 'turn'
        else:
            pose['head_stop'] = 'UP'
            if 10.55 <= t < 11.9: pose['tilt'] = 11.0              # curious tilt at the second "it's all right"
            if 12.33 <= t < 12.42: pose['eye'] = 'CLOSED'
            if 13.0 <= t < 13.6: gaze_target = 'doorway'
            elif 13.6 <= t < 14.4: gaze_target = 'hand'
            if t >= 14.25: pose.update(head_stop='MID', ear='HALF', brow='NEUTRAL')
    elif t < T_LIE:                                      # comes, head low, in its own time
        pose.update(head_stop='LOW', ear='HALF', eye='HALF', brow='WORRY' if t < 18 else 'NEUTRAL',
                    tail=D.tail_angle(0.62, 0, 0)); gaze_target = 'hand'; posture = 'walk'
    else:                                                # lies down across the sill
        pose.update(eye='HALF', brow='NEUTRAL', ear='HALF'); gaze_target = 'hand'; posture = 'lie'
        if t < 23.92: H = 31.0; pose['head_stop'] = 'LOW'
        elif t < 24.08: H = 20.0; pose['head_stop'] = 'MID'
        else:
            pose.update(draw='LIE', head_stop='L_UP' if a['head'] >= 0.5 else 'L_MID')
            if t >= 26.42: pose.update(ear='PRICK', eye='OPEN', head_stop='L_UP'); gaze_target = 'doorway'
            if t >= 26.50 and t < 28.04: pose.update(head_view='QB' if (t < 26.58 or t >= 27.96) else 'B', head_stop='L_HIGH' if 26.58 <= t < 27.96 else 'L_UP'); look = 'in'
            if t >= 28.04 and t < 28.25: pose.update(head_stop='L_UP', ear='HALF', eye='OPEN'); gaze_target = 'doorway'
            if t >= 28.25: pose.update(head_stop='L_CHIN', ear='HALF', eye='HALF'); gaze_target = 'doorway'
            if 30.55 <= t < 30.72: pose['eye'] = 'CLOSED'
    # ------------------------------------------------ tail: score angle and wag (on the floor when lying)
    if pose['draw'] == 'LIE':
        w = a['wag']; ph = t * 2 * math.pi * 2.4
        pose['tail'] = -3.0 + 22.0 * w * max(0.0, math.sin(ph))
    elif t >= T_APPROACH and t < T_LIE:
        pose['tail'] = D.tail_angle(0.62, t * 2 * math.pi * 2.0, a['wag'])
    else:
        pose['tail'] = D.tail_angle(a['tail'], t * 2 * math.pi * 2.0, a['wag'])
    # ------------------------------------------------ feet and body height (profile standing drawing only)
    d = gait_state['x0'] - x                             # facing left: forward is -x
    feet, stance = gait(d, a['moving'])
    pose['feet'] = feet
    if pose['body'] == 'P' and pose['draw'] == 'STAND':
        pose['H'] = body_height(H, feet, stance) if H > 30 else H
    else:
        pose['H'] = H
    return dict(t=t, j=j, state=state, x=x, pose=pose, posture=posture, gaze_target=gaze_target, look=look, stance=sorted(stance))


def door_at(t):
    return 'AJAR' if t < 6.2 else 'WIDE' if t < 6.33 else 'OPEN'


def caption_at(t):
    for li, L in enumerate(dialogue.LINES):
        t0, t1 = dialogue.line_span(li)
        if t0 - 0.04 <= t < t1 + 0.35:
            return dict(text=L['text'], reg=L['reg'], line=li)
    return None


def perform():
    frames = []
    gs = {'x0': SCORE['frames'][0]['dog']['x']}
    prev_stance = None
    events = []
    for i in range(N):
        j = i - (i % 2)                                   # held on twos
        rec = dog_at(j, gs)
        t = i / FPS
        tj = j / FPS
        dh = (rec['x'] - 0.35, 0.75)
        px, ppose, posture = person_at(tj, dh)
        frames.append(dict(i=i, t=round(t, 4), j=j, cam='WIDE' if i < CUT_CLOSE else 'CLOSE', dog=rec,
                           person=dict(x=px, pose=ppose, posture=posture), door=door_at(t), caption=caption_at(t)))
        # paw contacts -> sound events (only on the profile standing drawing while walking)
        st = set(rec['stance']) if rec['posture'] in ('walk', 'retreat') else None
        if st is not None and prev_stance is not None and i % 2 == 0:
            for leg in st - prev_stance:
                events.append(dict(t=t, kind='paw', leg=leg, x=rec['x']))
        if i % 2 == 0: prev_stance = st
    # one-off events cut to the picture
    events += [dict(t=3.42, kind='jingle'), dict(t=3.58, kind='jingle'), dict(t=4.75, kind='flop', size=1.0),
               dict(t=4.85, kind='huff'), dict(t=4.80, kind='sigh'), dict(t=5.42, kind='step'), dict(t=5.62, kind='step'),
               dict(t=5.82, kind='step'), dict(t=6.2, kind='creak'), dict(t=6.54, kind='sit'), dict(t=7.62, kind='rise'),
               dict(t=8.0, kind='jingle'), dict(t=8.17, kind='jingle'), dict(t=14.75, kind='jingle'),
               dict(t=24.08, kind='flop', size=0.7), dict(t=24.3, kind='content'), dict(t=26.45, kind='jingle')]
    # tail thumps: the lying tail coming back down to the boards
    for fr in frames:
        if fr['dog']['pose']['draw'] == 'LIE' and fr['t'] > 24:
            w = SCORE['frames'][fr['j']]['dog']['act']['wag']
            ph = (fr['t'] * 2.4) % 1.0
            if w > 0.3 and fr['i'] % 2 == 0:
                prev = ((fr['t'] - 2 / FPS) * 2.4) % 1.0
                if prev < 0.5 <= ph or (prev > ph and ph >= 0.5):
                    events.append(dict(t=fr['t'], kind='thump', amp=w))
    return frames, sorted(events, key=lambda e: e['t'])


if __name__ == '__main__':
    fr, ev = perform()
    print(len(fr), 'frames', len(ev), 'events')
    from collections import Counter
    print(Counter(e['kind'] for e in ev))
