"""SCION 16 JibJab: the one performance (cast-agnostic), solved from the score.

The score's decision trace drives a body plate (a cut-out dog body with 3D anchors) and a head track (the face slot's pose:
collar point, head yaw, pitch, ears). Any cast can be dropped into the face slot afterwards without re-performing.
Outputs:
  performance.json           the cast-agnostic performance schema: per frame channels + timecoded events (kept, small)
  build/cache/skeleton.json  per frame 3D anchors for the body plate (regenerable)
World: x along the porch in metres (score x, threshold 0, sill 0.56), d depth into the screen (wall of the house at 0.55),
y up. Time base: 24 fps, scene frame i = 0..767.
"""
import json, math, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = json.load(open(os.path.join(HERE, '..', 'score', 'threshold-score.json')))
F = SC['frames']; N = len(F); FPS = 24
os.makedirs(os.path.join(HERE, 'build/cache'), exist_ok=True)


def clamp(v, a=0., b=1.): return max(a, min(b, v))
def lerp(a, b, u): return a + (b - a) * u
def sstep(u): u = clamp(u); return u * u * (3 - 2 * u)
def ss5(u): u = clamp(u); return u * u * u * (u * (u * 6 - 15) + 10)
def ramp(t, t0, t1): return ss5((t - t0) / (t1 - t0))


def interp(tab, v):
    if v <= tab[0][0]: return tab[0][1]
    for (a, fa), (b, fb) in zip(tab, tab[1:]):
        if v <= b: return lerp(fa, fb, (v - a) / (b - a))
    return tab[-1][1]


ALPHA = [(0, -62), (0.15, -58), (0.35, -52), (0.45, -50), (0.6, -8), (0.75, 26), (0.9, 46), (1.2, 56)]
PITCH = [(0, -38), (0.15, -32), (0.45, -26), (0.7, -6), (0.9, 0), (1.2, 12)]
TAIL = [(0, 48), (0.5, 8), (1.0, -45), (1.35, -78)]

SILL = SC['places']['sill']
CH = {c['to'] + '@' + str(c['t']): c['t'] for c in SC['choices']}
T_RET, T_W1, T_REF, T_W2, T_APP, T_LIE = [c['t'] for c in SC['choices']]
T_IN = 26.4


def body_yaw(t):
    y = 180.0
    # round 2: the turns go through the camera, as the archive dog's own turn did (its frames f016-f044 are the plates)
    if t >= T_REF: y = lerp(180, 360, sstep((t - T_REF - 0.02) / (3.88 - T_REF)))   # turns its back: facing away by 3.9 s
    if t >= 7.76: y = lerp(360, 180, sstep((t - 7.76) / (8.40 - 7.76)))             # body follows the head round
    return y


def path_yaw(x):
    # walking the diagonal toward the sill the body follows its path; lying, it lies across the threshold (head in)
    k = 0.36 / (2.1 - SILL)
    on = sstep((2.25 - x) / 0.3)
    return 180 - math.degrees(math.atan(k)) * on


def head_yaw(t, yb, look):
    if T_REF <= t < 4.6: return lerp(180, 360, sstep((t - T_REF) / (3.85 - T_REF)))  # the head leads the turn away slightly
    if T_W2 <= t < 8.45: return min(yb, lerp(360, 185, sstep((t - T_W2) / (7.70 - T_W2))))  # turns to look: the muzzle is at the door by 7.70
    if t >= 23.6: return lerp(yb, lerp(180, 84, look), sstep((t - 23.6) / 0.6))   # lying: toward the person; look in: the back of its head to us
    return yb


def depth(x):
    u = clamp((2.1 - x) / (2.1 - SILL))
    return 0.36 * (u if u < 0.9 else u)   # straight diagonal, then held


# ---------------------------------------------------------------- body plate geometry (dog-local: u forward, v up, w left)
LEG = {  # socket u, w, upper, lower
    'FL': (0.22, 0.075, 0.19, 0.21), 'FR': (0.22, -0.075, 0.19, 0.21),
    'HL': (-0.25, 0.08, 0.20, 0.21), 'HR': (-0.25, -0.08, 0.20, 0.21)}
PAIRS = {'FL': 'FR', 'FR': 'FL', 'HL': 'HR', 'HR': 'HL'}
LIE_FOOT = {'FL': (0.50, 0.08), 'FR': (0.46, -0.07), 'HL': (-0.02, 0.14), 'HR': (-0.05, -0.13)}


def to_world(X, D, yaw, u, v, w):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return [X + u * c - w * s, v, D + u * s + w * c]


def to_local(X, D, yaw, x, d):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    dx, dd = x - X, d - D
    return dx * c + dd * s, -dx * s + dd * c


def ik(a, b, P, Q, bend):
    """two-segment chain from P to Q (3D), knee pushed along unit vector 'bend'"""
    d = [Q[i] - P[i] for i in range(3)]; L = math.sqrt(sum(x * x for x in d)) or 1e-6
    Lc = min(L, a + b - 1e-4)
    x = (a * a - b * b + Lc * Lc) / (2 * Lc); h = math.sqrt(max(0, a * a - x * x))
    e = [v / L for v in d]
    dot = sum(bend[i] * e[i] for i in range(3)); n = [bend[i] - dot * e[i] for i in range(3)]
    nl = math.sqrt(sum(v * v for v in n)) or 1e-6; n = [v / nl for v in n]
    K = [P[i] + e[i] * x + n[i] * h for i in range(3)]
    if L > a + b: Q = [P[i] + e[i] * (a + b) for i in range(3)]
    return K, Q


def yaw_at(k):
    k = min(N - 1, max(0, k)); f = F[k]; t = f['t']; X = f['dog']['x']
    yb = body_yaw(t)
    if t > 14: yb = path_yaw(X)
    if t >= 23.6: yb = lerp(path_yaw(X), 148, ramp(t, 23.6, 24.4))
    return yb


YAW = [yaw_at(k) for k in range(N)]
feet = {}       # leg -> dict(p=[x,d], swing=None or (t0, dur, p0, p1))
events = []
frames = []
skel = []
prevX = None
for f in F:
    i, t = f['i'], f['t']; dg = f['dog']; a = dg['act']; pr = f['person']
    X = dg['x']; D = depth(X)
    yb = YAW[i]
    look = a['look']; yh = head_yaw(t, yb, look)
    lie, crouch, rest = a['lie'], a['crouch'], a['rest']
    # spine
    vs = lerp(0.40 - 0.05 * crouch, 0.12, sstep(lie))
    rump_drop = 0.04 * crouch * (1 - lie)
    breath = 1 + 0.018 * math.sin(2 * math.pi * t / (1.5 if lie < .5 else 2.6))
    spine = []
    for k in range(13):
        u = lerp(-0.33, 0.26, k / 12)
        r = interp([(-0.33, 0.12), (-0.24, 0.135), (-0.08, 0.118), (0.1, 0.145), (0.26, 0.15)], u)
        if u > 0: r *= breath
        v = vs - rump_drop * clamp((-u) / 0.33) + interp([(-0.33, 0.0), (0.1, -0.015), (0.26, 0.0)], u)
        if lie > 0: r *= lerp(1, interp([(-0.33, 1.05), (0, 0.95), (0.26, 1.0)], u), lie)
        spine.append(to_world(X, D, yb, u, v, 0) + [r])
    # feet: a stepping controller in the world plane; nothing moves while planted
    vx = 0 if prevX is None else (X - prevX) * FPS
    prevX = X
    legs = {}
    fk = min(N - 1, i + 4)                       # land where the body will be in 1/6 s (pose and turn ahead)
    Xf = F[fk]['dog']['x']; Df = depth(Xf); yf = YAW[fk]
    for L, (us, ws, la, lb) in LEG.items():
        tgt = to_world(Xf, Df, yf, us, 0, ws)
        tgt = [tgt[0], tgt[2]]
        st = feet.get(L)
        if st is None:
            st = feet[L] = {'p': [tgt[0], tgt[1]], 'swing': None}
        st['tgt'] = tgt
    if lie < 0.12:
        swinging = [L for L, s in feet.items() if s['swing']]
        errs = sorted(((math.hypot(s['p'][0] - s['tgt'][0], s['p'][1] - s['tgt'][1]), L) for L, s in feet.items() if not s['swing']), reverse=True)
        for e, L in errs:
            turning = abs(YAW[min(N - 1, i + 3)] - yb) > 2.0
            thr = 0.05 if turning else 0.075
            if e > thr and len(swinging) < (3 if turning else 2) and (turning or PAIRS[L] not in swinging):
                dur = 0.14 if turning else (0.17 if abs(vx) > .5 else 0.21)
                feet[L]['swing'] = (t, dur, list(feet[L]['p']), list(feet[L]['tgt']))
                swinging.append(L)
    for L, (us, ws, la, lb) in LEG.items():
        s = feet[L]; lift = 0.0
        if s['swing']:
            t0, dur, p0, p1 = s['swing']
            # retarget the landing to where the body will be
            p1 = [s['tgt'][0], s['tgt'][1]]
            u = clamp((t - t0) / dur)
            s['p'] = [lerp(p0[0], p1[0], sstep(u)), lerp(p0[1], p1[1], sstep(u))]
            lift = 0.06 * math.sin(math.pi * u)
            if u >= 1:
                s['swing'] = None; lift = 0
                events.append({'t': round(t, 3), 'i': i, 'e': 'paw', 'leg': L, 'x': round(s['p'][0], 3), 'd': round(s['p'][1], 3)})
        fx, fd = s['p']
        if lie > 0:
            lu, lw = LIE_FOOT[L]
            lw_ = to_world(X, D, yb, lu, 0, lw)
            k = sstep(lie)
            fx, fd = lerp(fx, lw_[0], k), lerp(fd, lw_[2], k)
            lift *= 1 - k
        sock = to_world(X, D, yb, us, vs - (rump_drop if us < 0 else 0) - 0.02, ws)
        foot = [fx, 0.03 + lift, fd]
        fwd = [math.cos(math.radians(yb)), 0, math.sin(math.radians(yb))]
        back = [-v for v in fwd]
        if L[0] == 'H':
            bend = [lerp(back[i], fwd[i] * 0.7 + (-0.7 if i == 1 else 0), sstep(lie)) for i in range(3)]
        else:
            bend = [back[0], -0.25 * lie, back[2]]
        knee, foot = ik(la, lb, sock, foot, bend)
        legs[L] = {'s': sock, 'k': knee, 'f': foot, 'lift': lift}
    # tail
    tang = lerp(interp(TAIL, a['tail']), -28, sstep(lie))     # lying, the tail lies down along the boards
    wag = a['wag'] * 0.75 * math.sin(2 * math.pi * 2.3 * t)
    tail = []
    base = (-0.37, vs + 0.06 - rump_drop)
    pu, pv, pw = base[0], base[1], 0.0
    for k in range(6):
        ang = math.radians(tang - k * 9 * (1 if tang > 0 else -0.5))
        seg = 0.065
        du = -math.cos(ang) * math.cos(wag * (k + 1) / 6) * seg
        dw = math.sin(wag * (k + 1) / 6) * seg
        dv = math.sin(ang) * seg
        if lie > .3:
            dv = lerp(dv, -0.03, lie); dw = lerp(dw, 0.05 * k / 5, lie); du *= lerp(1, 0.7, lie)
        pu, pv, pw = pu + du, max(0.035, pv + dv), pw + dw
        tail.append(to_world(X, D, yb, pu, pv, pw))
    tail = [to_world(X, D, yb, base[0], base[1], 0)] + tail
    # neck and head track (the face slot's pose)
    hd = a['head']
    if dg['state'] == 'approach':     # it comes head low from its first step, not only near the end
        hd = lerp(hd, min(hd, 0.42), ramp(t, T_APP - 0.02, T_APP + 0.22))
    alpha = interp(ALPHA, hd) - 10 * crouch
    pitch = interp(PITCH, min(hd, 1.2))
    nlen = 0.22
    alpha = lerp(alpha, -72, rest); pitch = lerp(pitch, -2, rest); nlen = lerp(nlen, 0.2, rest)
    # a neck pointing away from the camera is seen foreshortened: the head sits down on the shoulders (no giraffe)
    away = abs(math.sin(math.radians(yb)))
    nlen *= 1 - 0.45 * away * clamp((alpha + 10) / 50)
    nb = (0.25, vs + 0.05)
    cu = nb[0] + nlen * math.cos(math.radians(alpha)); cv = nb[1] + nlen * math.sin(math.radians(alpha))
    cv = max(cv, 0.06)
    neck_base = to_world(X, D, yb, nb[0], nb[1], 0)
    collar = to_world(X, D, yb, cu, cv, 0)
    head = {'collar': collar, 'yaw': yh, 'pitch': pitch, 'ear': a['ear'], 'look': look}
    skel.append({'i': i, 'spine': spine, 'legs': legs, 'tail': tail, 'neck': neck_base, 'head': head, 'yaw': yb, 'X': X, 'D': D})
    # person: the door, the light
    door_ang = 12 + 70 * ramp(t, 6.2, 7.1)
    push = clamp(1 - abs(t - 6.25) / 0.45) if 5.8 < t < 6.7 else 0
    frames.append({'i': i, 't': t, 'state_score': dg['state'], 'x': X, 'd': round(D, 4), 'yaw_body': round(yb, 2),
                   'yaw_head': round(yh, 2), 'neck_alpha': round(alpha, 2), 'head_pitch': round(pitch, 2),
                   'lie': lie, 'crouch': crouch, 'rest': rest, 'look': look, 'ear': a['ear'], 'tail': a['tail'], 'wag': a['wag'],
                   'person': {'x': pr['x'], 'sit': pr['sit'], 'reach': pr['reach'], 'low': pr['low'], 'mouth': pr['mouth'],
                              'voice': pr['voice'], 'push': round(push, 3)},
                   'door_angle': round(door_ang, 2)})

# timecoded events beyond paws
vprev = 'none'
for f in F:
    v = f['person']['voice']
    if v != vprev and v != 'none':
        events.append({'t': f['t'], 'i': f['i'], 'e': 'voice', 'kind': v})
    vprev = v
events += [{'t': T_REF + 0.1, 'e': 'jingle', 'why': 'turns away'}, {'t': 4.45, 'e': 'thump', 'why': 'lies down, back turned'},
           {'t': 5.0, 'e': 'sigh'}, {'t': 6.2, 'e': 'door', 'why': 'the door opens'}, {'t': 7.5, 'e': 'jingle', 'why': 'gets up, looks'},
           {'t': 8.1, 'e': 'jingle'}, {'t': 14.72, 'e': 'jingle', 'why': 'comes'}, {'t': 24.05, 'e': 'thump', 'why': 'lies across the sill'},
           {'t': 26.5, 'e': 'jingle', 'why': 'looks in'}, {'t': 28.4, 'e': 'sigh', 'why': 'stays'}, {'t': 5.6, 'e': 'creak', 'why': 'person sits'}]
events.sort(key=lambda e: e['t'])
perf = {'about': 'SCION 16 JibJab: one performance, cast-agnostic. The face slot reads collar/yaw/pitch/ear from build/cache/skeleton.json; '
                 'any cast in cast/manifest.json fills it without re-performing.',
        'fps': FPS, 'n': N, 'world': {'x': 'score metres along the porch', 'd': 'metres into the screen; house wall at 0.55', 'y': 'up'},
        'choices': SC['choices'], 'frames': frames, 'events': events}
json.dump(perf, open(os.path.join(HERE, 'performance.json'), 'w'), separators=(',', ':'))


def rnd(o):
    if isinstance(o, float): return round(o, 4)
    if isinstance(o, list): return [rnd(v) for v in o]
    if isinstance(o, dict): return {k: rnd(v) for k, v in o.items()}
    return o


json.dump(rnd({'frames': skel}), open(os.path.join(HERE, 'build/cache/skeleton.json'), 'w'), separators=(',', ':'))
print('performance ok', N, 'frames', sum(1 for e in events if e['e'] == 'paw'), 'paw contacts')
