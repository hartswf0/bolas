"""SCION 35 · per-frame anchor trajectories, keyed to the score.

dog_pose(i)    -> which view print is shown, the target anchors q (film px) for every named anchor, the root, notes
person_pose(i) -> same for the person
world(i)       -> door angle, light level, etc.

The dog's choices are keyed here to the score's choice times; the onsets are then MEASURED from the render.
"""
import numpy as np, json, os
from common import CACHE, X_of, GROUND_Y, S_OUT, load_score, smoothstep

SCORE = load_score()
FR = SCORE['frames']
FPS = 24
_meta = {}


def meta(name):
    if name not in _meta:
        _meta[name] = json.load(open(os.path.join(CACHE, 'prints', name + '.json')))
    return _meta[name]


def rest(name):
    """rest anchors relative to the root, in film px (print px / 2)."""
    m = meta(name)
    r = np.array(m['root'])
    return {k: (np.array(v) - r) / 2.0 for k, v in m['anchors'].items()}


# ------------------------------------------------------------------ view keys (time, print). Consecutive different
# prints = a gesture that carries the change of view. The handles follow the stick guide continuously between the keys
# (body yaw, head yaw/pitch, stand->lie, monotone cubic in time); the PRINT shown swaps at the gesture's midpoint,
# behind the swing, warped to the same handles as the print it replaces (no dissolve).
VIEW_KEYS = [
    (0.0, 'P_prof'), (3.40, 'P_prof'),
    (3.53, 'R1_r34'), (3.65, 'R2_rear'), (3.77, 'R3_r34'), (3.90, 'P_right'),     # refusal: turns its back
    (4.28, 'P_right'), (4.86, 'L_right'),                                          # lies down, back turned
    (7.34, 'L_right'), (7.54, 'LB_look'),                                          # 7.46: the head comes round first
    (7.80, 'LB_look'), (8.06, 'SB_look'),                                          # gets up, head still on the door
    (8.20, 'RT3'), (8.34, 'RT2'), (8.48, 'RT1'), (8.64, 'P_prof'),                 # the body follows the head round
    (23.80, 'P_prof'), (24.40, 'L_prof'),                                          # lies down across the sill
    (26.40, 'L_prof'), (26.64, 'L_in'),                                            # looks in, through the door
    (28.20, 'L_in'), (28.50, 'L_prof'),                                            # settles, stays
    (40.0, 'L_prof'),
]


def _pchip(ts, ys):
    ts = np.asarray(ts, float); ys = np.asarray(ys, float)
    h = np.diff(ts); dl = np.diff(ys) / h
    m = np.zeros_like(ys)
    for k in range(1, len(ys) - 1):
        if dl[k - 1] * dl[k] > 0:
            w1 = 2 * h[k] + h[k - 1]; w2 = h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / dl[k - 1] + w2 / dl[k])
    def f(t):
        k = int(np.clip(np.searchsorted(ts, t) - 1, 0, len(ts) - 2))
        s = np.clip((t - ts[k]) / h[k], 0, 1)
        h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
        return h00 * ys[k] + h10 * h[k] * m[k] + h01 * ys[k + 1] + h11 * h[k] * m[k + 1]
    return f


_curves = None


def curves():
    global _curves
    if _curves is None:
        ts = [k[0] for k in VIEW_KEYS]
        ms = [meta(k[1]) for k in VIEW_KEYS]
        _curves = dict(psi=_pchip(ts, [m['psi'] for m in ms]),
                       lie=_pchip(ts, [1.0 if m['posture'] == 'lie' else 0.0 for m in ms]),
                       hy=_pchip(ts, [m['head_yaw'] for m in ms]), hp=_pchip(ts, [m['head_pitch'] for m in ms]))
    return _curves


def view_at(t):
    for (ta, A), (tb, B) in zip(VIEW_KEYS[:-1], VIEW_KEYS[1:]):
        if ta <= t < tb:
            if A == B:
                return A, A, 0.0, ta, tb
            return A, B, float((t - ta) / (tb - ta)), ta, tb
    return VIEW_KEYS[-1][1], VIEW_KEYS[-1][1], 0.0, 0, 0


def ease(s):
    return s * s * (3 - 2 * s)


def base_geom(t, th_n=0.0, th_h=0.0):
    from dogprint import guide, project
    A, B, s, ta, tb = view_at(t)
    c = curves()
    psi, lie, hy, hp = c['psi'](t), float(np.clip(c['lie'](t), 0, 1)), c['hy'](t), c['hp'](t)
    pr = project(guide(lie, hy, hp - th_h, th_n), psi)
    r = pr['tail0'] * 0 if False else None
    from dogprint import proj_pt
    root = proj_pt(np.zeros(3), psi)
    G = {k: (np.array(v[:2]) - np.array(root[:2])) / 2.0 for k, v in pr.items()}
    shown = A if s < 0.5 else B
    return G, psi, lie, shown, (A, B, s)


def rot(pts, keys, pivot, ang_deg):
    a = np.deg2rad(ang_deg); c, s = np.cos(a), np.sin(a)
    for k in keys:
        d = pts[k] - pivot
        pts[k] = pivot + np.array([d[0] * c - d[1] * s, d[0] * s + d[1] * c])


HEADK = ['skull', 'nose', 'jaw', 'eye_l', 'eye_r', 'ear_lb', 'ear_lt', 'ear_rb', 'ear_rt']
TAILK = ['tail1', 'tail2', 'tail3']
LEGS = {'fl': ['fl_sh', 'fl_el', 'fl_wr', 'fl_paw'], 'fr': ['fr_sh', 'fr_el', 'fr_wr', 'fr_paw'],
        'hl': ['hl_hip', 'hl_st', 'hl_hk', 'hl_paw'], 'hr': ['hr_hip', 'hr_st', 'hr_hk', 'hr_paw']}
GAIT_OFF = {'hl': 0.0, 'fl': 0.25, 'hr': 0.5, 'fr': 0.75}
K_PHASE = 11.5      # rad of walk_phase per metre (measured from the score)
STANCE = 0.62


def act(i):
    return FR[max(0, min(len(FR) - 1, i))]['dog']['act']


def smooth_act(i, key, r=2):
    vals = [act(j)[key] for j in range(i - r, i + r + 1)]
    return float(np.mean(vals))


def dog_pose(i, with_stretch=True):
    t = i / FPS
    f = FR[max(0, min(len(FR) - 1, i))]
    d = f['dog']; a = d['act']
    head = smooth_act(i, 'head'); rest_ = smooth_act(i, 'rest'); look = smooth_act(i, 'look')
    lie_t = float(np.clip(curves()['lie'](t), 0, 1))
    # neck and head carriage, as handle moves on the guide (so they hold in every view): standing = the score's head
    # (0 down .. 1 up); lying = rest (chin to the paws)
    sn = float(np.clip((0.9 - head) * 105, -15, 50)); sh_ = float(np.clip((0.9 - head) * 28, -10, 18))
    ln = rest_ * 38 + float(np.clip((0.7 - head) * 25, -12, 12)); lh = rest_ * 16
    th_n = sn * (1 - lie_t) + ln * lie_t; th_h = sh_ * (1 - lie_t) + lh * lie_t
    G, psi, lie, shown, trans = base_geom(t, th_n, th_h)
    fs = -np.cos(np.deg2rad(psi))          # +1 facing screen-left (the door), -1 facing away
    prof = abs(np.cos(np.deg2rad(psi)))   # 1 in profile, 0 in rear view
    down = -np.sign(fs) if abs(fs) > 1e-3 else 0.0   # rotation sign that lowers a point ahead of the pivot
    q = {k: v.copy() for k, v in G.items()}
    m = S_OUT  # px per metre
    crouch = smooth_act(i, 'crouch'); ear = smooth_act(i, 'ear')
    tail = smooth_act(i, 'tail'); wag = smooth_act(i, 'wag')
    moving = smooth_act(i, 'moving', 1)
    # --- crouch: the body sinks, hindquarters most (standing only)
    stand = 1 - lie
    sink = crouch * stand
    for k in ['withers', 'back', 'chest', 'throat', 'poll', 'belly'] + HEADK + ['fl_sh', 'fr_sh']:
        q[k] = q[k] + np.array([0, 0.07 * m * sink])
    for k in ['croup', 'rump', 'tail0', 'hl_hip', 'hr_hip'] + TAILK:
        q[k] = q[k] + np.array([0, 0.10 * m * sink])
    for L in ('fl', 'fr'):
        q[L + '_el'] = q[L + '_el'] + np.array([fs * -0.0 * m * sink, 0.045 * m * sink])
    for L in ('hl', 'hr'):
        q[L + '_st'] = q[L + '_st'] + np.array([-fs * -0.035 * m * sink * 0, 0.06 * m * sink])
        q[L + '_hk'] = q[L + '_hk'] + np.array([fs * -0.02 * m * sink, 0.02 * m * sink])
    # --- ears: flatten back when afraid
    for sd in ('l', 'r'):
        rot(q, ['ear_%st' % sd], q['ear_%sb' % sd], -down * np.clip(0.92 - ear, 0, 1) * 85 * prof)
    # --- tail: tucked under (1.35) or raised (0), wag on top
    tw = (tail - 0.5) * 62 + wag * 26 * np.sin(2 * np.pi * 2.6 * t)
    if lie > 0.5:
        tw = wag * 12 * np.sin(2 * np.pi * 2.2 * t)
    for j, k in enumerate(TAILK):
        rot(q, TAILK[j:], q['tail0'] if j == 0 else q[TAILK[j - 1]], -down * tw * (0.5 + 0.25 * j) * max(prof, 0.3))
    # --- breathing: the coat (affine) swells; faster when afraid
    br = np.sin(2 * np.pi * (0.35 + 0.5 * crouch) * t) * (1.2 + 1.0 * crouch)
    for k in ('chest', 'belly'):
        q[k] = q[k] + np.array([0, br * 0.7])
    q['back'] = q['back'] + np.array([0, -br * 0.4])
    # --- walk: paws planted while in stance, arc forward in swing (phase from the score: feet follow distance)
    v = d.get('v', 0.0)
    if moving > 0.02 and stand > 0.5:
        ph = a['walk_phase']
        sdir = np.sign(v) if abs(v) > 1e-4 else -np.sign(fs)   # screen direction of travel (+1 = right)
        half = np.pi * STANCE / K_PHASE                  # metres of travel per half stance
        for L, ks in LEGS.items():
            u = ((ph / (2 * np.pi) + GAIT_OFF[L]) % 1.0)
            if u < STANCE:
                off = half * (1 - 2 * u / STANCE)        # ahead of rest -> behind rest (planted in the world)
                lift = 0.0
            else:
                w = (u - STANCE) / (1 - STANCE)
                off = half * (-1 + 2 * ease(w))
                lift = 0.055 * np.sin(np.pi * w)
            dx = off * m * moving * sdir
            q[ks[3]] = q[ks[3]] + np.array([dx, -lift * m * moving])
            q[ks[2]] = q[ks[2]] + np.array([dx * 0.8, -lift * m * moving * 0.9])
            q[ks[1]] = q[ks[1]] + np.array([dx * 0.35, -lift * m * moving * 0.3])
        bob = np.sin(2 * ph) * 0.006 * m * moving
        for k in q:
            if not any(k in ks for ks in LEGS.values()) or k.endswith('_sh') or k.endswith('_hip'):
                q[k] = q[k] + np.array([0, bob])
    # --- root in the world
    root = np.array([X_of(d['x']), GROUND_Y])
    Q = {k: root + v for k, v in q.items()}
    if with_stretch and i > 0:
        # motion stretch: anchors that move faster than the root are drawn out along their motion (dots smear)
        P0, r0 = dog_pose(i - 1, with_stretch=False)[1:3]
        for k in Q:
            vel = (Q[k] - root) - (P0[k] - r0)
            sp = np.linalg.norm(vel)
            if sp > 1.5:
                off = vel * 0.55 * min(1.0, (sp - 1.5) / 6.0)
                n = np.linalg.norm(off)
                Q[k] = Q[k] + (off * min(1.0, 7.0 / n) if n > 0 else off)
    return shown, Q, root, dict(psi=psi, lie=lie, trans=trans, fs=fs)


# ------------------------------------------------------------------ the person
PERSON_X_DOOR = 262.0
PERSON_X_SIT = 34.0


def person_pose(i):
    t = i / FPS
    p = FR[max(0, min(len(FR) - 1, i))]['person']
    # standing -> stepping aside (4.7-5.4) -> sitting (5.45-6.05)
    walk = smoothstep(4.65, 5.45, t)
    x = PERSON_X_DOOR + (PERSON_X_SIT - PERSON_X_DOOR) * walk
    sit_s = smoothstep(5.45, 6.05, t)
    rs, rt = rest('PERSON_stand'), rest('PERSON_sit')
    G = {k: rs[k] * (1 - sit_s) + rt[k] * sit_s for k in rs}
    shown = 'PERSON_stand' if sit_s < 0.5 else 'PERSON_sit'
    m = S_OUT
    q = {k: v.copy() for k, v in G.items()}
    # calls: the head and shoulders push forward on each call
    call = 0.0
    for t0, t1 in ((0.92, 2.25), (3.28, 4.55)):
        call = max(call, smoothstep(t0, t0 + 0.15, t) * (1 - smoothstep(t1 - 0.2, t1, t)))
    lean = 6 * call
    reach = smoothstep(3.42, 3.95, t) * (1 - smoothstep(4.4, 4.85, t))
    lean += 14 * reach
    up = ['head', 'head_f', 'head_t', 'neck', 'sh', 'chest', 'back', 'el_n', 'ha_n', 'el_f', 'ha_f']
    rot(q, up, q['pelvis'], lean)
    # reach: the near arm goes out toward the dog, hand open, at the dog's head height
    if reach > 0:
        sh = q['sh']
        tgt_e = sh + np.array([0.26 * m, 0.14 * m]); tgt_h = sh + np.array([0.56 * m, 0.40 * m])
        q['el_n'] = q['el_n'] * (1 - reach) + tgt_e * reach
        q['ha_n'] = q['ha_n'] * (1 - reach) + tgt_h * reach
    # stepping aside: legs scissor a little while moving
    if 0 < walk < 1:
        sw = np.sin(np.pi * 4 * walk) * 0.12 * m * np.sin(np.pi * walk)
        q['ft_n'] = q['ft_n'] + np.array([sw, -abs(sw) * 0.3]); q['an_n'] = q['an_n'] + np.array([sw * 0.9, -abs(sw) * 0.3])
        q['kn_n'] = q['kn_n'] + np.array([sw * 0.5, 0])
        q['ft_f'] = q['ft_f'] - np.array([sw, abs(sw) * 0.3]); q['an_f'] = q['an_f'] - np.array([sw * 0.9, abs(sw) * 0.3])
        q['kn_f'] = q['kn_f'] - np.array([sw * 0.5, 0])
    # hand offered low (6.8 ->): near hand forward and down, near the floor, toward the sill
    low = smoothstep(6.75, 7.35, t)
    if low > 0:
        sh = q['sh']
        tgt_e = sh + np.array([0.30 * m, 0.24 * m]); tgt_h = np.array([0.72 * m, -0.27 * m])
        q['el_n'] = q['el_n'] * (1 - low) + tgt_e * low
        q['ha_n'] = q['ha_n'] * (1 - low) + tgt_h * low
        rot(q, ['head', 'head_f', 'head_t', 'neck', 'sh', 'chest', 'back', 'el_f', 'ha_f'], q['pelvis'], 10 * low)
    # soft voice: a small nod
    soft = 0.0
    for t0, t1 in ((7.32, 8.6), (10.32, 11.5), (26.28, 27.3)):
        soft = max(soft, smoothstep(t0, t0 + 0.2, t) * (1 - smoothstep(t1 - 0.25, t1, t)))
    rot(q, ['head', 'head_f', 'head_t'], q['neck'], 6 * soft * np.sin(np.pi * 2 * 0.8 * t) + 4 * soft)
    breath = np.sin(2 * np.pi * 0.25 * t) * 1.0
    q['chest'] = q['chest'] + np.array([breath * 0.5, 0])
    sc = 1.0 - 0.2 * walk                        # stepping aside = stepping back, away from the viewer
    root = np.array([x, GROUND_Y - 4.0 - 22.0 * walk])
    return shown, {k: root + v * sc for k, v in q.items()}, root


def world(i):
    t = i / FPS
    door = 34.0 + (100.0 - 34.0) * smoothstep(6.2, 6.9, t)      # degrees the door stands open
    light = 0.12 + 0.88 * smoothstep(6.25, 6.95, t)               # the room light reaching the porch
    return dict(door=door, light=light, t=t)
