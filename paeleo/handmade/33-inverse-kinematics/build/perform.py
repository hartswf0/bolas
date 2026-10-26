"""SCION 33 · the performance: the score's decisions become world-space targets, contacts and IK solves.

Input  : paeleo/handmade/score/threshold-score.json (768 frames, 24 fps; the dog's state, x and acting intentions)
Output : build/cache/pose.pkl   (per frame: every joint of dog and person in world metres, door angle, light)
         data/contacts.json      (contact timeline: every touch, grip, plant, release, bear-weight event)
         data/residuals.json     (per frame: reach residual of every chain, planted-foot slip, knee/elbow bend side)
The dog is a constraint rig: a spine (pelvis, chest), a neck aimed at a world look-target, and four three-segment legs
solved by analytic two-bone IK to a wrist/hock point set from the paw target and a pastern direction, with pole vectors
(elbows back, stifles forward) and joint limits. Paws are placed by a footfall planner that locks every planted paw at a
world position until the body has carried its home far enough away; a locked paw never moves.
"""
import os, json, math, pickle
import numpy as np
from geom import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache')
DATA = os.path.join(ROOT, 'data')
os.makedirs(CACHE, exist_ok=True); os.makedirs(DATA, exist_ok=True)

SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
T = np.arange(N) / FPS
UP = np.array([0, 1.0, 0])

def act(k):
    return np.array([f['dog']['act'][k] for f in FR], float)

def sm(t, a, b):
    return smooth(a, b, t)

def fwd(psi):
    return np.array([math.cos(psi), 0.0, math.sin(psi)])

def right_of(psi):
    return np.array([-math.sin(psi), 0.0, math.cos(psi)])

def interp(pts, t):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return float(np.interp(t, xs, ys))

def ease_out(u):
    u = min(1, max(0, u)); return 1 - (1 - u) ** 3

# --------------------------------------------------------------------------------------------------------------
# Dog proportions: a shepherd-type body, ratios studied from the archive dog's rig keys (kit/archive-dog/
# pose_agent_v8.json, profile frames 0-17: chest-to-tail-root / chest-to-ground = 1.75, nose-neck = 0.3 of length).
DOG = dict(
    half_back=0.28, half_front=0.25, hc=0.45, hp=0.44,
    fore=dict(l1=0.17, l2=0.25, l3=0.075, f=0.04, y=-0.06, s=0.078),
    hind=dict(l1=0.22, l2=0.25, l3=0.15, f=-0.02, y=-0.03, s=0.088),
    neck=0.21, skull=0.080,
)
LEGS = ['RF', 'LF', 'RH', 'LH']
SIDE = {'RF': 1, 'LF': -1, 'RH': 1, 'LH': -1}
HOME_F = {'RF': 0.29, 'LF': 0.29, 'RH': -0.29, 'LH': -0.29}

# --------------------------------------------------------------------------------------------------------------
# 1. The person: keyed world-space targets (pelvis, chest lean, feet, hands, gaze), IK legs and arms.
P_DIM = dict(thigh=0.44, shin=0.43, upper=0.30, fore=0.27, hand=0.085, hipw=0.10, shw=0.18, spine=0.46, neck=0.12)

# door: hinge on the near jamb, opens inward. theta in degrees. Edge point at height y:
def door_edge(theta, y=0.95):
    th = math.radians(theta)
    return HINGE + np.array([-math.sin(th), y, -math.cos(th)]) * np.array([DOOR_W, 1, DOOR_W])

def door_point(theta, s, y):
    th = math.radians(theta)
    return HINGE + np.array([-math.sin(th) * DOOR_W * s, y, -math.cos(th) * DOOR_W * s])


def keyed(keys, t):
    """keys: list of (t, value-array); smoothstep between keys (held outside)."""
    if t <= keys[0][0]: return np.array(keys[0][1], float)
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = smooth(t0, t1, t); return np.array(v0, float) * (1 - u) + np.array(v1, float) * u
    return np.array(keys[-1][1], float)


def step_keys(keys, t, lift=0.08):
    """foot keys: (t_lift, t_land, pos). Between lift and land the foot swings in an arc; otherwise it is locked."""
    pos = np.array(keys[0][2], float)
    for (ta, tb, p) in keys:
        p = np.array(p, float)
        if t >= tb: pos = p; continue
        if t > ta:
            u = smooth(ta, tb, t)
            q = pos * (1 - u) + p * u
            q[1] += lift * math.sin(math.pi * u)
            return q, False
        break
    return pos, True


# Feet (world). Facing +X: right is +Z.
P_RFOOT = [(0, 0, [0.16, 0, -0.08]),
           (3.45, 3.72, [0.52, 0.03, -0.06]),      # steps onto the sill to reach
           (4.62, 4.85, [0.20, 0, -0.10]),          # back off the sill
           (4.95, 5.18, [0.58, 0, -0.72]),          # stepping aside
           (5.40, 5.62, [1.02, 0, -0.86])]          # seated, knee up
P_LFOOT = [(0, 0, [0.10, 0, -0.34]),
           (5.08, 5.30, [0.66, 0, -1.16]),
           (5.48, 5.70, [1.08, 0, -1.16])]

# Pelvis keys (position), torso lean (forward pitch, rad), torso twist (yaw, rad), head gaze handled separately
P_PELVIS = [(0.0, [0.12, 0.95, -0.21]), (1.0, [0.12, 0.95, -0.21]), (1.25, [0.16, 0.93, -0.21]), (2.3, [0.16, 0.93, -0.21]),
            (2.6, [0.12, 0.95, -0.21]), (3.4, [0.12, 0.95, -0.21]), (3.75, [0.30, 0.91, -0.10]), (4.55, [0.31, 0.91, -0.10]),
            (4.85, [0.16, 0.95, -0.20]), (5.12, [0.42, 0.94, -0.62]), (5.32, [0.58, 0.88, -0.94]),
            (5.75, [0.64, 0.14, -1.02]), (32.0, [0.64, 0.14, -1.02])]
P_LEAN = [(0.0, 0.03), (1.0, 0.03), (1.3, 0.16), (2.3, 0.16), (2.6, 0.04), (3.4, 0.04), (3.8, 0.42), (4.5, 0.42),
          (4.8, 0.05), (5.3, 0.10), (5.75, -0.32),       # seated: back against the wall
          (5.80, -0.30), (5.96, 0.45), (6.12, 0.55), (6.45, -0.05), (7.0, 0.32), (32, 0.32)]
P_TWIST = [(0, 0.0), (5.75, 0.0), (5.80, 0.0), (5.96, 1.3), (6.12, 1.35), (6.45, 0.2), (7.0, 0.25), (32, 0.25)]


PUSH = dict(t_touch=5.96, th_end=13.5, rel=None)


def door_curve():
    """Door angle per frame (deg): held at 35 by the person's grip; released at 4.75 it settles on its own weight toward
    a 6 deg gap (overdamped). From 5.96 the seated person's hand is on the edge and shoves: static friction holds the
    heavy door until the push torque exceeds it (resist), it gives, the hand follows only while the arm can reach the
    edge (to 13.5 deg), then the door coasts on, slowed by friction, and meets its stop."""
    th = np.zeros(N); w = 0.0; theta = 35.0
    TMAX, TS, TK, CV = 2300.0, 1150.0, 60.0, 0.8
    out_force = np.zeros(N); rel = None
    for i in range(N):
        t = T[i]
        for sub in range(8):
            dt = 1 / FPS / 8; tt = t + sub * dt
            if tt < 4.75:
                theta, w = 35.0, 0.0
            elif tt < PUSH['t_touch']:
                acc = -9.0 * (theta - 6.0) - 4.5 * w
                w += acc * dt; theta += w * dt
            else:
                if w < 0: w = 0.0
                contact = rel is None and theta < PUSH['th_end']
                if not contact and rel is None: rel = tt
                tau = TMAX * smooth(PUSH['t_touch'], PUSH['t_touch'] + 0.26, tt) if contact else 0.0
                out_force[i] = max(out_force[i], tau)
                if w <= 0 and tau < TS:
                    w = 0.0; continue
                a = tau - TK - CV * w
                w = max(0.0, w + a * dt); theta += w * dt
                if theta > 100: theta, w = 100.0, 0.0
        th[i] = theta
    PUSH['rel'] = rel
    return th, out_force


def person_pose(t, door_th):
    pel = keyed(P_PELVIS, t)
    lean = interp(P_LEAN, t); twist = interp(P_TWIST, t)
    seated = smooth(5.3, 5.75, t)
    F0 = np.array([1.0, 0, 0]); S0 = np.array([0, 0, 1.0])
    Ft = np.array([math.cos(twist), 0, math.sin(twist)]); St = np.array([-math.sin(twist), 0, math.cos(twist)])
    spine_dir = norm(UP * math.cos(lean) + Ft * math.sin(lean))
    chest = pel + spine_dir * P_DIM['spine']
    neck = chest + spine_dir * P_DIM['neck']
    hipR = pel + S0 * P_DIM['hipw']; hipL = pel - S0 * P_DIM['hipw']
    shR = chest + St * P_DIM['shw'] - spine_dir * 0.04; shL = chest - St * P_DIM['shw'] - spine_dir * 0.04
    # gaze: the dog's head, computed by the caller and passed in later; here a default
    # feet
    rf, rlock = step_keys(P_RFOOT, t); lf, llock = step_keys(P_LFOOT, t)
    def leg(hip, foot):
        ankle = foot + np.array([-0.06, 0.08, 0])
        pole = norm(F0 + UP * 0.1)
        knee, end, res, cl = two_bone(hip, ankle, P_DIM['thigh'], P_DIM['shin'], pole)
        toe = foot + np.array([0.17, 0.0, 0]); toe[1] = max(0.02, foot[1] + 0.02)
        return dict(root=hip, mid=knee, end=end, tip=toe, res=res, bend=bend_side(hip, knee, end, pole))
    legR = leg(hipR, rf); legL = leg(hipL, lf)
    # hands
    E = door_edge(door_th, 0.95)
    # left hand grips the door edge until 4.75
    lh_free = pel + np.array([0.04, -0.05, -0.20]) + seated * np.array([-0.12, -0.08, -0.15])
    if t < 4.75:
        lh = E + np.array([0.0, 0, 0.03])
    else:
        lh = lh_free
    if 5.30 <= t < 5.80:   # bears weight on the boards as it sits down
        u = smooth(5.30, 5.42, t) * (1 - smooth(5.68, 5.80, t))
        lh = lh * (1 - u) + np.array([0.42, 0.03, -1.30]) * u
    # right hand: pats the thigh (call 1), reaches for the dog (call 2), pushes the door, offers low
    thigh_pt = (hipR + legR['mid']) / 2 + np.array([0.05, 0, 0.07])
    rh_rest = pel + np.array([0.06, -0.10, 0.24]) + seated * np.array([0.2, 0.15, 0.05])
    rh = rh_rest.copy()
    pats = [1.18, 1.48, 1.78]
    if 1.0 <= t < 2.2:
        u = smooth(1.0, 1.12, t) * (1 - smooth(2.0, 2.2, t))
        k = 0.5 + 0.5 * math.cos(2 * math.pi * (t - 1.18) / 0.30)
        tgt = thigh_pt + np.array([0.04, 0, 0.02]) + np.array([0.06, 0.10, 0.03]) * (1 - k)
        rh = rh * (1 - u) + tgt * u
    reach_on = smooth(3.45, 3.85, t) * (1 - smooth(4.45, 4.75, t))
    if reach_on > 0:
        rh = rh * (1 - reach_on) + np.array([4.0, 0.62, -0.06]) * reach_on      # aimed at the dog's chest: out of reach
    rel = PUSH['rel'] or 6.12
    dp = smooth(5.80, PUSH['t_touch'], t) * (1 - smooth(rel, rel + 0.25, t))
    if dp > 0:
        rh = rh * (1 - dp) + door_point(door_th, 0.96, 0.85) * dp
    low = smooth(6.55, 7.05, t)
    LOW = np.array([0.96, 0.035, -0.64])
    if low > 0:
        breath = 0.006 * math.sin(2 * math.pi * 0.22 * t)
        rh = rh * (1 - low) + (LOW + np.array([0, breath, 0])) * low
    def arm(sh, hand_t, pole):
        wrist_t = hand_t - norm(hand_t - sh) * P_DIM['hand'] * 0.6
        elbow, wrist, res, cl = two_bone(sh, wrist_t, P_DIM['upper'], P_DIM['fore'], pole)
        hand = wrist + norm(wrist - elbow) * P_DIM['hand']
        return dict(root=sh, mid=elbow, end=wrist, tip=hand, res=float(np.linalg.norm(hand - hand_t)), bend=bend_side(sh, elbow, wrist, pole), target=hand_t)
    armR = arm(shR, rh, norm(-F0 * 0.5 - UP + S0 * 0.6))
    armL = arm(shL, lh, norm(-F0 * 0.5 - UP - S0 * 0.6))
    head = neck + spine_dir * 0.03 + UP * 0.12
    return dict(pelvis=pel, chest=chest, neck=neck, head=head, lean=lean, twist=twist, legR=legR, legL=legL,
                armR=armR, armL=armL, rlock=rlock, llock=llock, rfoot=rf, lfoot=lf, seated=seated,
                grip_door=t < 4.75, push_door=dp > 0.95, low_hand=low, gaze=np.array([1.0, 0, 0]))


# --------------------------------------------------------------------------------------------------------------
# 2. Dog controls: from the score's decisions and acting intentions to world-space targets.
X = np.array([f['dog']['x'] for f in FR], float)
STATE = [f['dog']['state'] for f in FR]
CROUCH = act('crouch'); LIE = act('lie'); HEADP = act('head'); REST = act('rest'); LOOK = act('look')
EAR = act('ear'); TAIL = act('tail'); WAG = act('wag')

T_REF, T_BACK, T_APP, T_LIE, T_IN = 3.417, 7.458, 14.708, 23.792, 26.4


def dog_yaw(t):
    """heading: pi faces the door (-X); 0 faces away (+X). Both turns pass through facing the camera (pi/2)."""
    if t < T_REF + 0.02: return math.pi
    if t < 4.15:
        u = min(1.0, max(0.0, (t - T_REF - 0.02) / 0.70)) ** 0.8
        return math.pi * (1 - u * u * (3 - 2 * u))
    if t < 8.10: return 0.0
    if t < 8.85: return math.pi * smooth(8.10, 8.85, t)
    return math.pi


def dog_arc(t):
    """the body's small lateral arc while it turns (toward the camera and back), metres in Z."""
    a = 0.0
    if T_REF < t < 4.3: a += 0.16 * math.sin(math.pi * min(1, (t - T_REF) / 0.75))
    if 8.10 < t < 8.85: a += 0.12 * math.sin(math.pi * (t - 8.10) / 0.75)
    return a


def head_rel(h):
    """head intention -> skull-centre height relative to the back line (metres)."""
    return interp([(0.0, -0.31), (0.15, -0.25), (0.35, -0.19), (0.45, -0.15), (0.6, -0.04), (0.9, 0.16), (1.25, 0.27)], h)


def spine_bend(t):
    """chest yaw relative to the body heading (curling round to look back while lying, 7.46-8.1)."""
    return 0.30 * smooth(T_BACK, T_BACK + 0.3, t) * (1 - smooth(8.0, 8.4, t))


def lie_amount(i):
    t = T[i]
    l = LIE[i]
    return l


def dog_controls(i, person):
    t = T[i]
    psi = dog_yaw(t)
    kap = spine_bend(t)
    c = CROUCH[i]; l = lie_amount(i)
    # the front lowers first when lying down, the rear first... rising: front pushes up first
    rising = i > 0 and LIE[i] < LIE[i - 1] - 1e-4
    if rising:
        lf = min(1.0, max(0.0, (l - 0.3) / 0.7)); lb = min(1.0, l * 1.25)
    else:
        lf = min(1.0, l * 1.35); lb = min(1.0, max(0.0, (l - 0.2) / 0.8))
    hc = lerp(DOG['hc'] - 0.09 * c, 0.165, lf)
    hp = lerp(DOG['hp'] - 0.13 * c, 0.15, lb)
    R = np.array([X[i], 0.0, PATH_Z + dog_arc(t)])
    # look targets (world)
    phead = person['chest'] * 0.5 + person['head'] * 0.5
    if t < T_REF:
        look = phead
    elif t < T_BACK:
        look = R + fwd(psi) * 3 + np.array([0, -0.1, 0.6])
    elif t < T_APP:
        look = phead * 0.6 + np.array([0.2, 0.9, -0.5]) * 0.4
    elif t < T_LIE:
        # coming: eyes on the boards ahead along the light, then on the low hand as it nears
        ahead = R + fwd(psi) * 1.0; ahead[1] = 0.0
        k = smooth(19.0, 22.5, t)
        look = ahead * (1 - k) + person['armR']['tip'] * k
    else:
        # lying across the sill: eyes on the boards inside; at 'come in' (the score's look) into the lit room
        k = LOOK[i]
        look = np.array([-0.6, 0.05, -0.15]) * (1 - k) + np.array([-2.3, 0.95, -0.55]) * k
    if 14.40 <= t < 15.2:      # the head goes down as it decides to come: low before the first step
        ctrl_head = min(HEADP[i], lerp(0.9, 0.42, smooth(14.42, 14.70, t)))
    else:
        ctrl_head = HEADP[i]
    rest = REST[i]
    if T_BACK <= t < 9.0: rest *= 1 - smooth(T_BACK, T_BACK + 0.12, t)     # the head comes up first
    if 26.25 <= t < 27.9: rest = 0.0                                        # the machine's transient: chin stays up
    return dict(t=t, psi=psi, kappa=kap, crouch=c, lie=l, lf=lf, lb=lb, hc=hc, hp=hp, R=R, look=look,
                head=ctrl_head, rest=rest, lookin=LOOK[i], ear=EAR[i], tail=TAIL[i], wag=WAG[i])


def body_frame(ctrl):
    psi, kap = ctrl['psi'], ctrl['kappa']
    Fc = fwd(psi + kap); Sc = right_of(psi + kap); Fp = fwd(psi - 0.25 * kap); Sp = right_of(psi - 0.25 * kap)
    R = ctrl['R']
    Pv = R - Fp * DOG['half_back'] + UP * ctrl['hp']
    Ch = R + Fc * DOG['half_front'] + UP * ctrl['hc']
    anchors = {}
    for L in LEGS:
        g = DOG['fore'] if L[1] == 'F' else DOG['hind']
        base, FF, SS = (Ch, Fc, Sc) if L[1] == 'F' else (Pv, Fp, Sp)
        anchors[L] = base + FF * g['f'] + UP * g['y'] + SS * (g['s'] * SIDE[L])
    return dict(Fc=Fc, Sc=Sc, Fp=Fp, Sp=Sp, Pv=Pv, Ch=Ch, anchors=anchors)


def pastern(ctrl, L, FF):
    lyw = ctrl['lf'] if L[1] == 'F' else ctrl['lb']
    if L[1] == 'F':
        D = norm(UP - FF * 0.18) * (1 - lyw) + (-FF) * lyw
    else:
        D = norm(UP - FF * 0.42) * (1 - lyw) + norm(-FF + UP * 0.05) * lyw
    return norm(D), lyw


def reach_gap(ctrl, L, paw):
    """how far the planted paw is beyond what the leg can hold (m); > 0 means the contact must release."""
    bf = body_frame(ctrl)
    g = DOG['fore'] if L[1] == 'F' else DOG['hind']
    FF = bf['Fc'] if L[1] == 'F' else bf['Fp']
    D, _ = pastern(ctrl, L, FF)
    w = paw + UP * 0.028 + D * g['l3']
    return float(np.linalg.norm(w - bf['anchors'][L]) - (g['l1'] + g['l2']) * 0.97)


# --------------------------------------------------------------------------------------------------------------
# 3. Footfall planner: planted-foot locks.
class Planner:
    def __init__(self):
        self.lock = {}; self.swing = {}; self.events = []; self.mode = {}

    def home(self, ctrl, leg):
        F = fwd(ctrl['psi']); S = right_of(ctrl['psi'])
        p = ctrl['R'] + F * HOME_F[leg] + S * (0.085 * SIDE[leg])
        p[1] = 0.0
        return p

    def lying_target(self, ctrl, leg):
        F = fwd(ctrl['psi'] + ctrl['kappa'] * 0.8); S = right_of(ctrl['psi'] + ctrl['kappa'] * 0.8)
        if leg in ('RF', 'LF'):
            p = ctrl['R'] + F * 0.58 + S * (0.06 * SIDE[leg])
        else:
            p = ctrl['R'] + F * (-0.20) + S * (0.15 * SIDE[leg])
        p[1] = 0.0
        return p

    def step(self, i, ctrl, ctrl_next):
        t = ctrl['t']
        out = {}
        if not self.lock:
            for L in LEGS: self.lock[L] = self.home(ctrl, L); self.mode[L] = 'stand'
        lying = ctrl['lf'] > 0.12 or ctrl['lie'] > 0.12
        speed = np.linalg.norm(ctrl_next['R'] - ctrl['R']) * FPS
        turn = abs(ctrl_next['psi'] - ctrl['psi']) * FPS
        swinging = [L for L in LEGS if L in self.swing]
        # forelegs walk out to the lying place / back under the shoulders
        for L in ('RF', 'LF'):
            want_mode = 'lie' if lying else 'stand'
            if self.mode[L] != want_mode and L not in self.swing:
                if len([s for s in self.swing]) < 1 + (L == 'LF'):
                    tgt = self.lying_target(ctrl, L) if want_mode == 'lie' else self.home(ctrl, L)
                    dur = 0.30
                    self.swing[L] = dict(t0=t, t1=t + dur, a=self.lock[L].copy(), b=tgt, fixed=True, lift=0.05)
                    self.mode[L] = want_mode
                    self.events.append(dict(t=round(t, 3), who='dog', part=L, kind='release', why='forepaw re-placed to ' + want_mode))
        if lying:
            for L in ('RF', 'LF'):
                if L not in self.swing and self.mode[L] == 'lie' and reach_gap(ctrl_next, L, self.lock[L]) > -0.02:
                    self.swing[L] = dict(t0=t, t1=t + 0.22, a=self.lock[L].copy(), b=self.lying_target(ctrl_next, L), fixed=True, lift=0.03)
                    self.events.append(dict(t=round(t, 3), who='dog', part=L, kind='release', why='forepaw re-placed: out of reach'))
        if not lying:
            for L in ('RH', 'LH'): self.mode[L] = 'stand'
            # gait: a leg steps when its home (predicted a little ahead) has left its lock
            lead = 0.12
            fast = speed > 0.5 or turn > 1.0
            thresh = 0.10 if not fast else 0.12
            if turn > 1.0: thresh = 0.07
            dur = 0.30 if speed < 0.5 else 0.22
            if turn > 1.0: dur = 0.14
            pred = {L: self.home(ctrl_next, L) + (self.home(ctrl_next, L) - self.home(ctrl, L)) * (lead * FPS) for L in LEGS}
            err = {L: np.linalg.norm(pred[L] - self.lock[L]) for L in LEGS if L not in self.swing}
            # a planted paw the leg can no longer hold must release, whatever the gait rules say
            urgent = {L for L in err if reach_gap(ctrl_next, L, self.lock[L]) > -0.05}
            for L in sorted(err, key=lambda k: (k not in urgent, -err[k])):
                if err[L] < thresh and L not in urgent: continue
                sw = list(self.swing.keys())
                if len(sw) >= 2 and L not in urgent: break
                if len(sw) >= 3: break
                # support rule: never lift both legs of one side, nor both fores or both hinds together
                bad = False
                for s_ in sw:
                    if SIDE[s_] == SIDE[L] or s_[1] == L[1]: bad = True
                if bad and L not in urgent: continue
                # land where the home will be at touchdown, a little beyond (overshoot along the travel)
                h0 = self.home(ctrl, L); h1 = self.home(ctrl_next, L)
                vel = (h1 - h0) * FPS
                tgt = h0 + vel * (dur + 0.10)
                self.swing[L] = dict(t0=t, t1=t + dur, a=self.lock[L].copy(), b=tgt, fixed=False, lift=0.065 if not ctrl['crouch'] > .5 else 0.045, vel=vel)
                self.events.append(dict(t=round(t, 3), who='dog', part=L, kind='lift'))
        # advance swings
        for L in list(self.swing):
            s = self.swing[L]
            if not s['fixed'] and t < s['t0'] + 0.7 * (s['t1'] - s['t0']):
                h0 = self.home(ctrl, L); h1 = self.home(ctrl_next, L)
                vel = (h1 - h0) * FPS
                s['b'] = h0 + vel * max(0.0, s['t1'] - t + 0.10)
            u = smooth(s['t0'], s['t1'], t)
            p = s['a'] * (1 - u) + s['b'] * u
            p[1] = s['lift'] * math.sin(math.pi * u)
            out[L] = (p, False)
            if t >= s['t1'] - 1e-6:
                self.lock[L] = s['b'].copy(); self.lock[L][1] = 0.0
                del self.swing[L]
                self.events.append(dict(t=round(t, 3), who='dog', part=L, kind='plant', pos=[round(float(v), 3) for v in self.lock[L]],
                                        load=round(0.35 if L[1] == 'F' else 0.25, 2)))
                out[L] = (self.lock[L].copy(), True)
        for L in LEGS:
            if L not in out: out[L] = (self.lock[L].copy(), True)
        return out


# --------------------------------------------------------------------------------------------------------------
# 4. Solve the dog's body for one frame.
def dog_solve(ctrl, feet):
    psi, kap = ctrl['psi'], ctrl['kappa']
    F = fwd(psi); S = right_of(psi)
    Fc = fwd(psi + kap); Sc = right_of(psi + kap)
    Fp = fwd(psi - 0.25 * kap)
    R = ctrl['R']
    Pv = R - Fp * DOG['half_back'] + UP * ctrl['hp']
    Ch = R + Fc * DOG['half_front'] + UP * ctrl['hc']
    body_ax = norm(Ch - Pv)
    t = ctrl['t']; l = ctrl['lie']
    breath = (0.006 + 0.006 * l) * math.sin(2 * math.pi * (0.32 if l > .5 else 0.5) * t)
    withers = Ch + UP * 0.10 - Fc * 0.04
    back_line = withers[1] + 0.035
    NB = Ch + Fc * 0.12 + UP * 0.07
    # head: a world look target, a height intention, joint limits on yaw and pitch, and the chin-on-paws contact
    look = ctrl['look']
    d = look - NB
    want_yaw = math.atan2(d[2], d[0])
    rel = (want_yaw - (psi + kap) + math.pi) % (2 * math.pi) - math.pi
    lim = 1.25 if l < 0.5 else 2.35
    if T_BACK <= t < 8.9: lim = 2.35          # looking back over the shoulder: neck and spine bend together
    phi = max(-lim, min(lim, rel))
    if t >= T_BACK and t < 8.1:          # turning back to look: over the right shoulder, toward the camera
        tgt = math.pi - (psi + kap)
        phi = min(lim, tgt) * smooth(T_BACK, T_BACK + 0.32, t)
    if T_REF <= t < 4.3:                 # turning away: the head leads the body round
        phi = -0.55 * math.sin(math.pi * min(1, (t - T_REF) / 0.7))
    if 8.10 <= t < 8.85:
        phi = (math.pi - (psi + kap)) * 0.9 * (1 - smooth(8.5, 8.9, t)) + phi * smooth(8.5, 8.9, t)
        phi = max(-lim - 0.6, min(lim + 0.6, phi))
    hyaw = psi + kap + phi
    Fh = fwd(hyaw)
    hy = back_line + head_rel(ctrl['head'])
    if l > 0.5:
        hy = max(hy, 0.20)
    neck_yaw = psi + kap + phi * 0.7
    Fn = fwd(neck_yaw)
    sp = max(-0.80, min(0.74 + 0.2 * l, (hy - NB[1]) / DOG['neck']))
    Hc = NB + DOG['neck'] * (Fn * math.sqrt(1 - sp * sp) + UP * sp)
    chin_res = None
    paw_mid = (feet['RF'][0] + feet['LF'][0]) / 2
    if ctrl['rest'] > 0.01:
        chin_t = paw_mid + UP * (DOG['skull'] + 0.035) - Fc * 0.03
        dd = chin_t - NB
        dn = norm(dd)
        Hc_rest = NB + DOG['neck'] * dn
        chin_res = float(np.linalg.norm(Hc_rest - chin_t))
        k = ctrl['rest']
        Hc = Hc * (1 - k) + Hc_rest * k
        Fh = norm(Fh * (1 - k) + Fc * k)
    # muzzle pitch: toward the look target, limited; level when resting
    dl = look - Hc
    pitch = math.atan2(dl[1], math.hypot(dl[0], dl[2]))
    pitch = max(-1.0, min(0.22, pitch)) * (1 - ctrl['rest']) + (-0.12) * ctrl['rest']
    if T_APP <= t < T_LIE:
        pitch = min(pitch, -0.35)
    Mdir = norm(Fh * math.cos(pitch) + UP * math.sin(pitch))
    Sh = right_of(hyaw)
    # legs
    legs = {}
    for L in LEGS:
        g = DOG['fore'] if L[1] == 'F' else DOG['hind']
        base = Ch if L[1] == 'F' else Pv
        FF = Fc if L[1] == 'F' else Fp
        SS = Sc if L[1] == 'F' else right_of(psi - 0.25 * kap)
        anchor = base + FF * g['f'] + UP * g['y'] + SS * (g['s'] * SIDE[L])
        paw, planted = feet[L]
        paw = paw.copy(); paw[1] = max(paw[1], 0.0) + 0.028
        lyw = ctrl['lf'] if L[1] == 'F' else ctrl['lb']
        if L[1] == 'F':
            D = norm(UP - FF * 0.18) * (1 - lyw) + (-FF) * lyw
            pole = norm(-FF * (1 - 0.3 * lyw) + UP * 0.25 * lyw)
        else:
            D = norm(UP - FF * 0.42) * (1 - lyw) + norm(-FF + UP * 0.05) * lyw
            pole = norm(FF + SS * SIDE[L] * 0.9 * lyw)
        D = norm(D)
        W_t = paw + D * g['l3']
        if lyw > 0.5:
            W_t[1] = max(W_t[1], 0.03)
        mid, wrist, res, cl = two_bone(anchor, W_t, g['l1'], g['l2'], pole)
        if not planted and res > 1e-4:
            # a swinging paw is carried by its leg: when the swing target is out of reach the paw stays on the leg's end
            paw = wrist - D * g['l3']
        legs[L] = dict(anchor=anchor, mid=mid, wrist=wrist, paw=paw, planted=planted, res=res, clamped=cl,
                       bend=bend_side(anchor, mid, wrist, pole), pole=pole, wrist_target=W_t)
    # tail: root behind the pelvis; carriage from the score's tail (0 high .. 1.35 tucked), wag sweep
    tr = Pv - Fp * 0.11 + UP * 0.05
    ang = interp([(0, 0.35), (0.25, -0.45), (0.5, -0.95), (0.8, -1.25), (1.35, -1.6)], ctrl['tail'])
    if l > 0.5: ang = max(ang, -0.35) * 0.4 - 0.12
    tail = [tr]
    SP = right_of(psi - 0.25 * kap)
    wagph = 2 * math.pi * 2.6 * t
    for k in range(7):
        a = ang - 0.12 * k * (1 if ctrl['tail'] < 0.6 else -0.6)
        sw = ctrl['wag'] * 0.55 * math.sin(wagph - 0.5 * k) * (k + 1) / 7
        dirv = norm(-Fp * math.cos(a) * math.cos(sw) + UP * math.sin(a) + SP * math.sin(sw) * math.cos(a))
        nxt = tail[-1] + dirv * 0.056
        nxt[1] = max(nxt[1], 0.03)
        tail.append(nxt)
    return dict(R=R, F=F, S=S, Fc=Fc, Sc=Sc, Pv=Pv, Ch=Ch, withers=withers, NB=NB, Hc=Hc, Fh=Fh, Mdir=Mdir, Sh=Sh,
                legs=legs, tail=tail, ear=ctrl['ear'], breath=breath, lie=l, chin_res=chin_res, phi=phi, hyaw=hyaw,
                back_line=back_line, psi=psi)


# --------------------------------------------------------------------------------------------------------------
def main():
    door_th, push_force = door_curve()
    persons = [person_pose(T[i], door_th[i]) for i in range(N)]
    ctrls = [dog_controls(i, persons[i]) for i in range(N)]
    pl = Planner()
    frames = []; resid = []
    prev_planted = {}
    for i in range(N):
        feet = pl.step(i, ctrls[i], ctrls[min(N - 1, i + 1)])
        dog = dog_solve(ctrls[i], feet)
        # the person watches the dog (the door while pushing it)
        pp = persons[i]
        tgt = dog['Hc'] if not (5.85 < T[i] < 6.4) else door_edge(door_th[i], 0.9)
        gz = norm(tgt - pp['head'])
        pp['gaze'] = gz
        # planted-foot slip: a locked paw must not move between consecutive frames
        slip = {}
        for L in LEGS:
            p, planted = feet[L]
            if planted and L in prev_planted and prev_planted[L] is not None:
                slip[L] = float(np.linalg.norm(p - prev_planted[L]))
            prev_planted[L] = p.copy() if planted else None
        frames.append(dict(i=i, t=T[i], dog=dog, person=persons[i], door=float(door_th[i]), push=float(push_force[i]), ctrl=ctrls[i]))
        resid.append(dict(i=i, t=round(T[i], 4),
                          dog_reach={L: round(dog['legs'][L]['res'], 5) for L in LEGS},
                          dog_bend={L: dog['legs'][L]['bend'] for L in LEGS},
                          dog_planted={L: bool(feet[L][1]) for L in LEGS},
                          dog_slip={L: round(v, 6) for L, v in slip.items()},
                          chin_res=None if dog['chin_res'] is None else round(dog['chin_res'], 4),
                          person_reach={'armR': round(persons[i]['armR']['res'], 4), 'armL': round(persons[i]['armL']['res'], 4),
                                        'legR': round(persons[i]['legR']['res'], 4), 'legL': round(persons[i]['legL']['res'], 4)},
                          person_bend={'legR': persons[i]['legR']['bend'], 'legL': persons[i]['legL']['bend']},
                          door_deg=round(float(door_th[i]), 3)))
    # person + world contact events (from the keyed contacts and the door simulation)
    ev = list(pl.events)
    for keys, part in ((P_RFOOT, 'person.Rfoot'), (P_LFOOT, 'person.Lfoot')):
        for ta, tb, p in keys[1:]:
            ev.append(dict(t=ta, who='person', part=part, kind='lift'))
            ev.append(dict(t=tb, who='person', part=part, kind='plant', pos=p, load=0.8))
    for tp in [1.18, 1.48, 1.78]:
        ev.append(dict(t=tp, who='person', part='person.Rhand', kind='touch', why='pats the thigh as it calls'))
    ev.append(dict(t=0.0, who='person', part='person.Lhand', kind='grip', why='holds the door edge'))
    ev.append(dict(t=3.85, who='person', part='person.Rhand', kind='reach', why='reaches for the dog: target 3.4 m beyond the arm, residual stays large'))
    ev.append(dict(t=4.75, who='person', part='person.Lhand', kind='release', why='lets go of the door; it drifts shut on its own weight'))
    ev.append(dict(t=5.42, who='person', part='person.Lhand', kind='bear_weight', why='hand on the boards while sitting down'))
    ev.append(dict(t=5.75, who='person', part='person.pelvis', kind='bear_weight', why='sits on the boards, back to the wall'))
    i_touch = int(PUSH['t_touch'] * FPS)
    ev.append(dict(t=PUSH['t_touch'], who='person', part='person.Rhand', kind='touch', why='hand meets the door edge and shoves'))
    moved = next(i for i in range(i_touch, N) if door_th[i] > door_th[i_touch] + 0.3)
    ev.append(dict(t=round(T[moved], 3), who='world', part='door', kind='resist_then_give', why='static friction exceeded; the door starts to swing'))
    ev.append(dict(t=round(PUSH['rel'], 3), who='person', part='person.Rhand', kind='release', why='the edge runs out of reach; the door coasts on'))
    stop_i = next(i for i in range(moved, N) if door_th[i] >= 95.9 or (i > moved + 5 and abs(door_th[i] - door_th[i - 1]) < 1e-4))
    ev.append(dict(t=round(T[stop_i], 3), who='world', part='door', kind='stop', why='door at rest, open %.0f deg' % door_th[stop_i]))
    ev.append(dict(t=7.0, who='person', part='person.Rhand', kind='touch', why='the low hand reaches the boards, palm up'))
    # dog body contacts
    lie = LIE
    for i in range(1, N):
        if lie[i - 1] < 0.9 <= lie[i]:
            ev.append(dict(t=round(T[i], 3), who='dog', part='dog.belly', kind='bear_weight', why='lies down'))
        if lie[i - 1] > 0.5 >= lie[i]:
            ev.append(dict(t=round(T[i], 3), who='dog', part='dog.belly', kind='release', why='gets up'))
        if REST[i - 1] < 0.9 <= REST[i]:
            ev.append(dict(t=round(T[i], 3), who='dog', part='dog.chin', kind='touch', why='chin on the paws'))
        if REST[i - 1] > 0.3 >= REST[i]:
            ev.append(dict(t=round(T[i], 3), who='dog', part='dog.chin', kind='release', why='lifts the head'))
    # tail thumps: lying tail tip touching the boards at the ends of each wag sweep
    tip_prev = None
    for fr in frames:
        if fr['dog']['lie'] > 0.9 and fr['ctrl']['wag'] > 0.3:
            tip = fr['dog']['tail'][-1]
            side = tip @ fr['dog']['S']
            if tip_prev is not None and np.sign(side - tip_prev[0]) != np.sign(tip_prev[1]) and abs(side) > 0.05:
                ev.append(dict(t=round(fr['t'], 3), who='dog', part='dog.tail', kind='touch', why='tail sweeps the boards', load=0.15))
            tip_prev = (side, side - (tip_prev[0] if tip_prev else side))
        else:
            tip_prev = None
    ev.sort(key=lambda e: e['t'])
    json.dump(dict(about='SCION 33 contact timeline: every touch, grip, plant, release and bear-weight event, from the rig and the door simulation.', units='seconds (scene clock = score clock)', events=ev),
              open(os.path.join(DATA, 'contacts.json'), 'w'), indent=0)
    json.dump(dict(about='per-frame residuals: dog leg reach residual (m, |wrist - wrist target|), bend side (+1 = toward the pole: elbows back, stifles forward), planted flag and planted-paw slip (m/frame), chin-on-paws residual, person chains, door angle', frames=resid),
              open(os.path.join(DATA, 'residuals.json'), 'w'))
    pickle.dump(dict(frames=frames, door=door_th), open(os.path.join(CACHE, 'pose.pkl'), 'wb'))
    # summary
    dr = [max(r['dog_reach'].values()) for r in resid]
    slips = [v for r in resid for v in r['dog_slip'].values()]
    inv = sum(1 for r in resid for v in r['dog_bend'].values() if v < 0)
    print('dog reach residual max %.4f m, mean %.5f; planted slip max %.6f m; inverted bends %d; plants %d' % (
        max(dr), float(np.mean(dr)), max(slips) if slips else 0, inv, sum(1 for e in ev if e['who'] == 'dog' and e['kind'] == 'plant')))
    bad = [(r['t'], L, v) for r in resid for L, v in r['dog_reach'].items() if v > 0.01]
    if bad: print('frames with dog residual > 1 cm:', len(bad), bad[:12])


if __name__ == '__main__':
    main()
