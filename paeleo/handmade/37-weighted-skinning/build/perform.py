"""SCION 37 performance: the score -> skeletal motion clips (bind-relative joint rotations per frame).
Dog: root path from the score's x (X = x - 0.17 m, so the body centre sits over the sill at x = 0.59), yaw from the score's
turn (my own easing; the refusal shows the back by 3.97 s), head-led turn back at 7.46 s, a gait clock that only advances
when the hips must travel (so planted feet never slide), two-bone IK per leg, a lying clip (sphinx: forearms flat, hind legs
folded, hocks on the ground) blended in by the score's `lie`, neck/head/ears/tail from the score's acting channels.
Person, door, interior light and camera are keyed from the score's circumstances.  Writes cache/perform.npz."""
import json, os
import numpy as np
import rig
from rig import euler, rx, ry, rz

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']; N = len(FR); FPS = 24
T = np.array([f['t'] for f in FR])
DOG_X_OFFSET = -.17


def ss(a, b, t):
    u = np.clip((t - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

def act(k): return np.array([f['dog']['act'][k] for f in FR])

def smooth(a, n=3):
    k = np.hanning(2 * n + 1); k /= k.sum(); p = np.pad(a, n, mode='edge'); return np.convolve(p, k, 'valid')


# ------------------------------------------------------------------------------------------------ dog channels
X = np.array([f['dog']['x'] for f in FR]) + DOG_X_OFFSET
lie = smooth(act('lie'), 2); crouch = smooth(act('crouch'), 3); ear = smooth(act('ear'), 2); tail = smooth(act('tail'), 3)
wag = act('wag'); head = smooth(act('head'), 3); rest = smooth(act('rest'), 3); look = smooth(act('look'), 2)
state = [f['dog']['state'] for f in FR]

# yaw: pi = facing the door (-X). Refusal turns away through pi/2 (its back to the camera mid-turn);
# the turn back goes through -pi/2 (facing the camera), the head leading.
yaw = np.full(N, np.pi)
yaw = np.where(T >= 3.417, np.pi - np.pi * ss(3.417, 3.97, T), yaw)
yaw = np.where(T >= 7.80, -np.pi * ss(7.80, 8.75, T), yaw)
# lie: refusal lie is the score's; the turn-back rise starts once the head is round (7.62)
lie = np.where((T > 7.4) & (T < 8.4), 1 - ss(7.62, 8.05, T), lie)
lie = np.where((T > 23.6) & (T < 24.8), ss(23.80, 24.45, T), lie)
# head-led look back: from 7.458 the head turns to the door before the body follows
lookback = ss(7.458, 7.80, T) * (1 - ss(8.55, 8.95, T))
# lying across the sill: attends to the person's low hand (to its left), then on 'come in' turns into the room
attend = ss(24.45, 25.0, T) * (1 - ss(26.40, 26.80, T))
look_in = np.clip(look, 0, 1)

sk = rig.dog_skeleton(); J = len(sk.names)
LEGS = {'LF': ('shoulderL', 'elbowL', 'wristL', 'fpawL', 'chest'), 'RF': ('shoulderR', 'elbowR', 'wristR', 'fpawR', 'chest'),
        'LH': ('hipL', 'stifleL', 'hockL', 'hpawL', 'pelvis'), 'RH': ('hipR', 'stifleR', 'hockR', 'hpawR', 'pelvis')}
GAIT_OFF = {'LH': 0., 'LF': .25, 'RH': .5, 'RF': .75}
STANCE = .65


def root_mat(i, extra_y=0.):
    M = np.eye(4); M[:3, :3] = ry(yaw[i]); M[:3, 3] = [X[i], extra_y, 0.]
    return M


def body_y(i):
    return -.10 * crouch[i] * (1 - lie[i]) - .305 * lie[i]


def trunk_pose(i):
    p = {}
    c = crouch[i] * (1 - lie[i])
    p['pelvis'] = euler(pitch=-.10 * c)
    p['spine'] = euler(pitch=.06 * c)
    # look back: the whole front of the body bends round, the head rolls (a true twist along the neck)
    lb = lookback[i]
    need = 0.
    if lb > 0:
        need = np.clip(-np.pi - yaw[i], -2.75, 0) * lb if yaw[i] <= 0.01 else 0.
    yw = {'spine': .08, 'chest': .12, 'neck1': .22, 'neck2': .33, 'head': .25}
    att = -1.45 * attend[i]
    # head carriage
    h = head[i]
    n1 = -1.30 * (1 - h); n2 = -.45 * (1 - h); hd = .80 * (1 - h)
    if h > 1: n1 = .55 * (h - 1); n2 = .3 * (h - 1); hd = -.2 * (h - 1)
    # chin on the paws while lying
    r = rest[i] * lie[i]
    n1 = n1 * (1 - r) + (-1.05) * r; n2 = n2 * (1 - r) + (-.30) * r; hd = hd * (1 - r) + .62 * r
    # looking in: the neck stretches forward and low through the door, the muzzle past the jamb
    li = look_in[i] * lie[i]
    n1 = n1 * (1 - li) + (-.55) * li; n2 = n2 * (1 - li) + (-.05) * li; hd = hd * (1 - li) + .30 * li
    roll_lb = 1.0 * lb          # the head tilts as it comes round over the shoulder: twist along the neck
    p['spine'] = p['spine'] @ euler(yaw=yw['spine'] * need)
    p['chest'] = euler(yaw=yw['chest'] * need)
    p['neck1'] = euler(yaw=yw['neck1'] * need + .45 * att, pitch=n1, roll=.15 * roll_lb)
    p['neck2'] = euler(yaw=yw['neck2'] * need + .35 * att, pitch=n2, roll=.40 * roll_lb)
    p['head'] = euler(yaw=yw['head'] * need + .20 * att, pitch=hd, roll=.55 * roll_lb)
    e = ear[i]
    for s, sg in (('L', 1), ('R', -1)):
        p['ear' + s] = euler(pitch=-1.25 * (1 - min(e, 1.)), roll=sg * .25 * (1 - min(e, 1.)))
    tl = tail[i]
    w = wag[i] * .7 * np.sin(2 * np.pi * 2.4 * T[i])
    tl_l = tl * (1 - .6 * lie[i])
    # the tail points backward (-x): a positive pitch about z swings it DOWN, so tucking is positive
    p['tail1'] = euler(yaw=w, pitch=-.85 * (.5 - tl_l) + .25 * lie[i])
    p['tail2'] = euler(yaw=.6 * w, pitch=.35 * tl_l - .25 * lie[i])
    p['tail3'] = euler(yaw=.4 * w, pitch=.25 * tl_l - .1 * lie[i])
    return p


LIE_LEGS = {}
for s, sg in (('L', 1), ('R', -1)):
    LIE_LEGS.update({'shoulder' + s: euler(pitch=-.15), 'elbow' + s: euler(pitch=1.55), 'wrist' + s: euler(pitch=-.05),
                     'fpaw' + s: euler(pitch=-.10),
                     'hip' + s: euler(pitch=.62, roll=-.28 * sg), 'stifle' + s: euler(pitch=-1.45), 'hock' + s: euler(pitch=2.05),
                     'hpaw' + s: euler(pitch=-.45)})


def ik2(d, u0, v0, a, b):
    """two-bone IK in the leg's plane; d = target of the end joint in the upper joint's parent frame"""
    phi = np.arctan2(-d[2], -d[1])
    w = np.hypot(d[1], d[2])
    tx, ty = d[0], -w
    D = np.clip(np.hypot(tx, ty), abs(a - b) + 1e-3, (a + b) * .995)
    th_rest = np.arctan2(u0[0] * v0[1] - u0[1] * v0[0], u0[0] * v0[0] + u0[1] * v0[1])
    g = np.arccos(np.clip((a * a + b * b - D * D) / (2 * a * b), -1, 1))
    th2 = np.sign(th_rest) * (np.pi - g) - th_rest
    c2, s2 = np.cos(th2), np.sin(th2)
    c0 = a * u0[:2] + b * np.array([c2 * v0[0] - s2 * v0[1], s2 * v0[0] + c2 * v0[1]])
    th1 = np.arctan2(ty, tx) - np.arctan2(c0[1], c0[0])
    return rx(phi) @ rz(th1), rz(th2)


R = sk.rest
def leg_geom(up, lo, an, paw):
    S, E, A, P = R[sk.ix[up]], R[sk.ix[lo]], R[sk.ix[an]], R[sk.ix[paw]]
    return (E - S) / np.linalg.norm(E - S), (A - E) / np.linalg.norm(A - E), np.linalg.norm(E - S), np.linalg.norm(A - E), A - P

def neutral_foot(i, leg, Gt=None):
    """where the paw joint rests under its girdle at frame i (world), from the trunk FK"""
    up, lo, an, paw, par = LEGS[leg]
    loc = R[sk.ix[paw]].copy()
    if Gt is None:
        Gt = sk.fk(trunk_pose(i), root_mat(i, body_y(i)))
    gp = Gt[sk.ix[par]]
    p = gp[:3, :3] @ (loc - R[sk.ix[par]]) + gp[:3, 3]
    p[1] = .04
    return p


def run():
    poses = np.zeros((N, J, 3, 3)); roots = np.zeros((N, 4, 4))
    # precompute neutral foot positions for the gait planner
    trunk = [trunk_pose(i) for i in range(N)]
    Gts = [sk.fk(trunk[i], root_mat(i, body_y(i))) for i in range(N)]
    neut = {L: np.array([neutral_foot(i, L, Gts[i]) for i in range(N)]) for L in LEGS}
    # gait clock: advances with the fastest girdle's travel (translation and turning); stride 0.55 m like the score
    speed = np.max([np.r_[0, np.linalg.norm(np.diff(neut[L], axis=0), axis=1)] * FPS for L in LEGS], 0)
    trans = np.r_[0, np.abs(np.diff(X))] * FPS
    stride = np.where(trans > .05, .55, .30)
    clock = np.zeros(N); feet = {L: neut[L][0].copy() for L in LEGS}; swing = {L: None for L in LEGS}
    contact = np.zeros((N, 4), bool); footpos = np.zeros((N, 4, 3))
    def cyc(c, L): return (c + GAIT_OFF[L]) % 1.
    for i in range(N):
        settle = max(np.linalg.norm(feet[L][[0, 2]] - neut[L][i][[0, 2]]) for L in LEGS)
        rate = speed[i] / stride[i]
        if lie[i] < .3 and rate < .4 and (settle > .03 or any(swing[L] is not None for L in LEGS)):
            rate = 1.6                                           # finish the step: settle the feet under the body
        if lie[i] >= .3: rate = 0.
        if i: clock[i] = clock[i - 1] + rate / FPS
        for k, L in enumerate(LEGS):
            c = cyc(clock[i], L)
            in_swing = c >= STANCE and rate > 0
            if in_swing:
                if swing[L] is None:
                    dur = (1 - STANCE) / max(rate, .1)
                    tl = min(N - 1, i + int(round((dur + .5 * STANCE / max(rate, .1)) * FPS)))
                    swing[L] = (feet[L].copy(), neut[L][tl].copy())
                u = (c - STANCE) / (1 - STANCE); a0, a1 = swing[L]
                e = u * u * (3 - 2 * u)
                p = a0 + (a1 - a0) * e; p[1] = .04 + (.065 - .03 * crouch[i]) * np.sin(np.pi * u)
                footpos[i, k] = p
            else:
                if swing[L] is not None:
                    feet[L] = swing[L][1].copy(); swing[L] = None
                footpos[i, k] = feet[L]; contact[i, k] = True
        # IK
        pose = dict(trunk[i]); G = Gts[i]
        for k, L in enumerate(LEGS):
            up, lo, an, paw, par = LEGS[L]
            u0, v0, a, b, AP = leg_geom(up, lo, an, paw)
            tgt_paw = footpos[i, k]
            tgt_an = tgt_paw + ry(yaw[i]) @ AP
            gp = G[sk.ix[par]]
            Sw = gp[:3, :3] @ (R[sk.ix[up]] - R[sk.ix[par]]) + gp[:3, 3]
            d = gp[:3, :3].T @ (tgt_an - Sw)
            R1, R2 = ik2(d, u0, v0, a, b)
            R3 = (gp[:3, :3] @ R1 @ R2).T @ ry(yaw[i])          # pastern upright in the world
            ik = {up: R1, lo: R2, an: R3}
            if not contact[i, k]:
                ik[paw] = euler(pitch=-.5 if 'pawL' in paw or 'pawR' in paw else 0)
            lw = ss(.0, 1., lie[i])
            for jn in (up, lo, an, paw):
                A_ = ik.get(jn, np.eye(3)); B_ = LIE_LEGS.get(jn, np.eye(3))
                pose[jn] = rig.slerp_mat(A_, B_, lw) if lw > 0 else A_
        for jn, Rm in pose.items():
            poses[i, sk.ix[jn]] = Rm
        for j in range(J):
            if not poses[i, j].any(): poses[i, j] = np.eye(3)
        roots[i] = root_mat(i, body_y(i))
    return poses, roots, contact, footpos, clock


# ------------------------------------------------------------------------------------------------ person, door, light, camera
psk = rig.person_skeleton()
PJ = len(psk.names)

def person_track():
    ps = np.zeros((N, PJ, 3, 3)); pr = np.zeros((N, 4, 4)); mouth = np.zeros(N)
    voice = [f['person']['voice'] for f in FR]
    seat = np.array([.74, 0, -1.12]); door_spot = np.array([.06, 0, .10])
    for i, t in enumerate(T):
        p = {}
        walk = ss(4.60, 5.35, t); sit = ss(5.30, 5.85, t)
        reach = ss(3.40, 3.75, t) * (1 - ss(4.45, 4.80, t))
        low = ss(6.75, 7.30, t)
        pos = door_spot + (seat - door_spot) * walk
        pos[2] += .0
        yw = 0. + (-.50) * ss(4.9, 5.5, t)
        # stepping legs while walking aside
        if 4.6 < t < 5.45:
            sph = np.sin((t - 4.6) / .8 * 2 * np.pi * 1.5)
            for s, sg in (('L', 1), ('R', -1)):
                p['th' + s] = euler(pitch=.45 * sg * sph); p['kn' + s] = euler(pitch=-.5 * max(0, sg * sph))
        lean = -.30 * reach - .25 * sit - .42 * low
        p['spine'] = euler(pitch=lean * .5); p['chestp'] = euler(pitch=lean * .5)
        # sitting on the crate: thighs forward, shins down
        for s, sg in (('L', 1), ('R', -1)):
            th = p.get('th' + s, np.eye(3)); kn = p.get('kn' + s, np.eye(3))
            p['th' + s] = rig.slerp_mat(th, euler(pitch=1.50, roll=-.10 * sg), sit)
            p['kn' + s] = rig.slerp_mat(kn, euler(pitch=-1.45), sit)
            p['an' + s] = euler(pitch=-.05 * sit)
        # arms: the reach (right arm forward toward the dog), then the low offered hand (right arm, palm down, near the floor)
        armR_reach = (euler(pitch=1.35, roll=.05), euler(pitch=.15), euler(pitch=-.1))
        armR_low = (euler(pitch=.80, roll=.10), euler(pitch=.30), euler(pitch=.25))
        rest_arm = (euler(roll=-.05), euler(pitch=.1), np.eye(3))
        if sit < 1:
            A = [rig.slerp_mat(r0, r1, reach) for r0, r1 in zip(rest_arm, armR_reach)]
        else:
            A = list(rest_arm)
        A = [rig.slerp_mat(a, b, low) for a, b in zip(A, armR_low)]
        p['shR'], p['elR'], p['wrR'] = A
        p['shL'] = euler(roll=.08 + .25 * sit, pitch=.25 * sit); p['elL'] = euler(pitch=.6 * sit)
        # speaking: a small nod on each phrase; soft voice = head lowered and toward the dog
        sp = 1. if voice[i] in ('call', 'soft') else 0.
        mouth[i] = sp
        nod = .06 * sp * np.sin(2 * np.pi * 3.1 * t) * (1 if voice[i] == 'call' else .5)
        p['neck'] = euler(pitch=nod - .12 * (voice[i] == 'soft') - .15 * low)
        p['headp'] = euler(pitch=-.15 * low)
        M = np.eye(4); M[:3, :3] = ry(yw); M[:3, 3] = pos + np.array([0, -.50 * sit, 0]) + np.array([-.05 * sit, 0, 0])
        if 4.6 < t < 5.45: M[1, 3] += .02 * abs(np.sin((t - 4.6) / .8 * 2 * np.pi * 1.5))
        for jn, Rm in p.items(): ps[i, psk.ix[jn]] = Rm
        for j in range(PJ):
            if not ps[i, j].any(): ps[i, j] = np.eye(3)
        pr[i] = M
    return ps, pr, mouth


def door_light():
    door = np.radians(48) + np.radians(54) * ss(6.2, 7.0, T)        # ajar 48 deg, open to 102 deg (opens inward)
    light = .30 + .70 * ss(6.25, 7.2, T)
    return door, light


CAM_A = dict(eye=(6.05, 1.55, 3.55), target=(2.05, .52, -.30), f=1010.)     # the whole porch: door, person, dog
CAM_C = dict(eye=(3.05, 1.00, 4.10), target=(1.45, .42, -.25), f=1000.)     # the approach, side on: the head below the back
CAM_B = dict(eye=(2.85, .98, 1.32), target=(.00, .40, -.25), f=1180.)       # behind the dog at the sill: looking in, in depth

def camera():
    u1 = ss(14.9, 17.6, T); u2 = ss(21.6, 24.2, T)
    def mix(k):
        a, c, b = (np.array(C[k], float) for C in (CAM_A, CAM_C, CAM_B))
        if a.ndim == 0: a, c, b = a[None], c[None], b[None]
        v = a[None] * (1 - u1[:, None]) + c[None] * u1[:, None]
        return v * (1 - u2[:, None]) + b[None] * u2[:, None]
    return mix('eye'), mix('target'), mix('f')[:, 0]


if __name__ == '__main__':
    poses, roots, contact, footpos, clock = run()
    ps, pr, mouth = person_track()
    door, light = door_light()
    eye, tg, f = camera()
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    np.savez_compressed(os.path.join(HERE, 'cache', 'perform.npz'), dog_rot=poses, dog_root=roots, contact=contact, footpos=footpos,
                        clock=clock, person_rot=ps, person_root=pr, mouth=mouth, door=door, light=light, cam_eye=eye, cam_target=tg,
                        cam_f=f, yaw=yaw, lie=lie, lookback=lookback, look_in=look_in, attend=attend, X=X)
    # foot-slide audit: planted paws must not move
    sl = 0.
    for k in range(4):
        m = contact[1:, k] & contact[:-1, k]
        if m.any(): sl = max(sl, np.linalg.norm(np.diff(footpos[:, k], axis=0)[m], axis=1).max())
    print('frames', N, 'max planted-foot slide per frame (m):', round(float(sl), 5), 'gait cycles', round(float(clock[-1]), 2))
