"""SCION-02 Reiniger: articulated shadow theatre for the PAELEO threshold.

Typed primitives (native formal language):
  Piece      -- a cut silhouette polygon in its own local frame (metres), with a pivot (pin).
  Pin        -- a hinge joining two pieces; angle limits are enforced and logged.
  Replacement-- a discrete swap of a piece (profile / foreshortened / end-on) chosen per frame.
  Contact    -- the porch plane g(x) (floor 0, sill 0.045 m) on which paws are planted.
  Exposure   -- one row per frame: replacements used, joint angles, contacts (exposure-sheet.csv).

Coordinates: world metres, x along the porch (threshold at 0, inside negative, steps at 4.9),
y up from the porch floor.  Screen: X = OX + S*x, Y = FY - S*y (1280x720 at 1x).
Time base: scene frame i at 24 fps, aligned to paeleo/handmade/score/threshold-score.json.
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
KIT = os.path.join(REPO, 'paeleo', 'handmade', 'kit')
SCORE = os.path.join(REPO, 'paeleo', 'handmade', 'score', 'threshold-score.json')
OUT = os.path.join(HERE, 'out')

W, H = 1280, 720
SS = 2                      # supersampling for cut edges
OX, S, FY = 352.0, 175.0, 588.0
FPS = 24

def X(x): return OX + S * x
def Y(y): return FY - S * y

def ground(x):
    """Contact plane: porch floor 0, the sill stone across the door opening is 4.5 cm high."""
    return 0.045 if -0.52 <= x <= 0.52 else 0.0

# ---------------------------------------------------------------- geometry helpers
def catmull(pts, n=6, closed=True):
    P = np.asarray(pts, float); m = len(P); out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if (closed or i > 0) else P[i]
        p1 = P[i]; p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[(i + 1) % m]
        for s in np.linspace(0, 1, n, endpoint=False):
            s2 = s * s; s3 = s2 * s
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    if not closed: out.append(P[-1])
    return np.array(out)

def capsule(a, b, r0, r1, n=7):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a; L = math.hypot(*d) + 1e-9; u = d / L; v = np.array([-u[1], u[0]])
    pts = []
    for th in np.linspace(math.pi / 2, -math.pi / 2, n):
        pts.append(b + r1 * (math.cos(th) * u + math.sin(th) * v))
    for th in np.linspace(-math.pi / 2, -3 * math.pi / 2, n):
        pts.append(a + r0 * (math.cos(th) * u + math.sin(th) * v))
    return np.array(pts)

def ellipse(c, rx, ry, n=24, rot=0.0):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    p = np.stack([rx * np.cos(t), ry * np.sin(t)], 1)
    return rot2(p, rot) + np.asarray(c, float)

def rot2(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    p = np.asarray(p, float)
    return p @ np.array([[c, s], [-s, c]])

def place(p, origin, ang, sx=1.0):
    p = np.asarray(p, float).copy(); p[:, 0] *= sx
    return rot2(p, ang) + np.asarray(origin, float)

def ik2(a, t, l1, l2, bend):
    """Two-bone IK from a to target t; bend=+1 puts the middle joint to the left of a->t."""
    a = np.asarray(a, float); t = np.asarray(t, float)
    d = t - a; L = math.hypot(*d); clamped = False
    if L > l1 + l2 - 1e-4:
        t = a + d / L * (l1 + l2 - 1e-4); d = t - a; L = l1 + l2 - 1e-4; clamped = True
    if L < abs(l1 - l2) + 1e-4:
        L = abs(l1 - l2) + 1e-4; clamped = True
    ca = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L); ca = max(-1, min(1, ca))
    base = math.atan2(d[1], d[0]); ang = base + bend * math.acos(ca)
    mid = a + l1 * np.array([math.cos(ang), math.sin(ang)])
    end = mid + l2 * (t - mid) / (np.linalg.norm(t - mid) + 1e-9)
    return mid, end, clamped

def interp(v, xs, ys): return float(np.interp(v, xs, ys))
def smooth(s): s = min(1, max(0, s)); return s * s * (3 - 2 * s)
def lerp(a, b, s): return a + (b - a) * s
D = math.radians

# ---------------------------------------------------------------- score
def load_score():
    return json.load(open(SCORE))

# ---------------------------------------------------------------- the dog: cut pieces
# Proportions measured from the Amateur Film New Jersey C pose keys (frame 8, a clean profile):
# chest->tail-root 110 px, chest height 64 px, neck height 89 px, nose height 109 px.
# Scaled so chest->tail-root = 0.80 m.  Head-low range from frames 19-23 (nose 20-26 px above ground).
# pinned-joint cut: each body piece ends in an arc centred on the spine pin, so the back line
# stays continuous whatever the hinge angle (the round lap joint of a silhouette puppet)
FORE = catmull([(-0.088, 0.088), (0.0, 0.125), (0.12, 0.14), (0.22, 0.155), (0.29, 0.14), (0.33, 0.10),
                (0.40, 0.0), (0.395, -0.06), (0.33, -0.13), (0.24, -0.165), (0.12, -0.16), (0.0, -0.125),
                (-0.088, -0.088), (-0.125, 0.0)], 5)
HIND = catmull([(0.088, 0.088), (0.0, 0.122), (-0.14, 0.12), (-0.26, 0.11), (-0.36, 0.08), (-0.42, 0.03),
                (-0.435, -0.04), (-0.40, -0.10), (-0.33, -0.125), (-0.20, -0.09), (-0.05, -0.10),
                (0.0, -0.11), (0.088, -0.08), (0.122, 0.0)], 5)
FORE_SHOULDER = np.array([0.33, -0.02]); FORE_NECK = np.array([0.28, 0.07])
HIND_HIP = np.array([-0.31, -0.02]); HIND_TAIL = np.array([-0.41, 0.05])
NECK = catmull([(-0.07, -0.09), (-0.05, 0.08), (0.08, 0.08), (0.17, 0.066), (0.215, 0.04),
                (0.225, -0.02), (0.18, -0.06), (0.06, -0.08)], 5)
NECK_LEN = 0.18
HEAD = catmull([(-0.045, 0.03), (0.0, 0.06), (0.05, 0.075), (0.10, 0.066), (0.13, 0.047), (0.19, 0.036),
                (0.225, 0.026), (0.243, 0.008), (0.236, -0.013), (0.21, -0.026), (0.16, -0.036),
                (0.10, -0.046), (0.05, -0.062), (0.0, -0.06), (-0.045, -0.03)], 5)
MUZZLE = np.array([(0.14, 0.044), (0.19, 0.036), (0.225, 0.026), (0.243, 0.008), (0.236, -0.013),
                   (0.21, -0.026), (0.16, -0.036), (0.14, -0.04)])
CRANIUM = ellipse((0.03, 0.0), 0.055, 0.05, 16)
EYE = ellipse((0.103, 0.026), 0.012, 0.0065, 12, D(-10))
EAR = catmull([(0.0, -0.036), (0.05, -0.026), (0.102, -0.002), (0.05, 0.022), (0.0, 0.036)], 4)
EAR_PIN = np.array([0.012, 0.052])
LEG = dict(fu=0.17, fl=0.265, hu=0.19, hl=0.17)   # upper / lower bones (m)
TAIL_SEG = [0.10, 0.10, 0.09, 0.08]

def tail_shape(points, widths):
    """A brush tail cut with feathered serrations along its lower edge."""
    P = np.asarray(points); n = len(P)
    up, dn = [], []
    for i in range(n):
        a = P[max(0, i - 1)]; b = P[min(n - 1, i + 1)]
        d = b - a; d = d / (np.linalg.norm(d) + 1e-9); v = np.array([-d[1], d[0]])
        w = widths[i]
        up.append(P[i] + v * w)
        dn.append(P[i] - v * w * 1.15)
        if 0 < i < n - 1:
            dn.append(P[i] - v * w * 1.35 + d * 0.02)    # fur tuft
    tip = P[-1] + (P[-1] - P[-2]) / (np.linalg.norm(P[-1] - P[-2]) + 1e-9) * 0.05
    return catmull(np.array(up + [tip] + dn[::-1]), 3)

class DogRig:
    """Holds paw contact state across frames (the contact solver) and produces cut pieces per frame."""
    BETA = 0.64                      # stance fraction of the gait cycle
    CYCLE = 2 * math.pi / 11.425     # metres per gait cycle (walk_phase rate measured from the score)
    OFF = dict(nh=0.0, nf=0.25, fh=0.5, ff=0.75)

    def __init__(self):
        self.feet = {}
        self.prev = None
        self.events = []
        self.limit_log = []

    # ---- posture -> spine pins
    def spine(self, P):
        cr, lie = P['crouch'], P['lie']
        yM = lerp(0.47 - 0.07 * cr, 0.20, lie)
        aF = lerp(D(-7 * cr), D(2), lie)
        aH = lerp(D(5 + 13 * cr), D(5), lie)
        return yM, aF, aH

    def anchors(self, yM, aF, aH):
        M = np.array([0.0, yM])
        Sj = M + rot2(FORE_SHOULDER[None], aF)[0]
        Hj = M + rot2(HIND_HIP[None], aH)[0]
        return M, Sj, Hj

    def step(self, i, P):
        """Advance the paw contact solver one frame; returns world paw positions."""
        x0, dirW, sx = P['x'], P['dirW'], P['sx']
        yM, aF, aH = self.spine(P)
        M, Sj, Hj = self.anchors(yM, aF, aH)
        neutral = {'nf': Sj[0] - 0.09, 'ff': Sj[0] + 0.02, 'nh': Hj[0] - 0.07, 'fh': Hj[0] + 0.04}
        phi = P['phase']; moving = P['moving']; vx = P['vx']
        dphi = 0 if self.prev is None else abs(phi - self.prev)
        self.prev = phi
        walking = moving > 0.05 and dphi > 1e-4
        mdir = 0 if abs(vx) < 1e-6 else (1 if vx > 0 else -1)
        out = {}
        for leg, off in self.OFF.items():
            ax = x0 + dirW * sx * neutral[leg]
            st = self.feet.get(leg)
            if st is None:
                st = dict(x=ax, y=0.0, stance=True, lift=ax)
            u = (phi / (2 * math.pi) + off) % 1.0
            if walking:
                if u < self.BETA:
                    if not st['stance']:
                        self.events.append(dict(i=i, leg=leg, x=st['x'], kind='touch'))
                    st['stance'] = True; st['y'] = ground(st['x'])
                else:
                    if st['stance']: st['lift'] = st['x']
                    st['stance'] = False
                    s = (u - self.BETA) / (1 - self.BETA)
                    tgt = ax + mdir * self.CYCLE * self.BETA * 0.5
                    st['x'] = lerp(st['lift'], tgt, smooth(s))
                    st['y'] = ground(st['x']) + 0.065 * math.sin(math.pi * s)
            else:
                dx = ax - st['x']
                if abs(dx) > 0.004:
                    st['x'] += dx * 0.3
                    st['y'] = ground(st['x']) + min(0.035, abs(dx) * 0.6)
                else:
                    if st['y'] > ground(st['x']) + 0.001:
                        self.events.append(dict(i=i, leg=leg, x=st['x'], kind='settle'))
                    st['y'] = ground(st['x'])
                st['stance'] = True
            self.feet[leg] = st
            out[leg] = (st['x'], st['y'], st['stance'])
        return out

    def pose(self, i, P, feet):
        """Return dict: pieces (list of (poly_world, tag)), holes, measurement polys, exposure row."""
        x0, dirW, sx = P['x'], P['dirW'], P['sx']
        def W_(p):
            p = np.atleast_2d(np.asarray(p, float))
            return np.stack([x0 + dirW * sx * p[:, 0], p[:, 1]], 1)
        def L_(wx):  # world x -> local x
            return (wx - x0) / (dirW * sx)
        fills, holes, muzzle, skull = [], [], [], []
        row = dict(i=i)
        lie, cr, rest, look, hb = P['lie'], P['crouch'], P['rest'], P['look'], P['hb']
        if P['endon']:
            return self.pose_endon(P, W_, row)
        yM, aF, aH = self.spine(P)
        # contact: if the shoulders lie over the sill, the forequarters rest on it
        sh_world = x0 + dirW * sx * 0.27
        aF += math.atan2(ground(sh_world) * lie, 0.30)
        M, Sj, Hj = self.anchors(yM, aF, aH)
        fore = place(FORE, M, aF); hind = place(HIND, M, aH)
        neck0 = M + rot2(FORE_NECK[None], aF)[0]
        tail0 = M + rot2(HIND_TAIL[None], aH)[0]
        row.update(spine_y=round(yM, 3), fore_deg=round(math.degrees(aF), 1), hind_deg=round(math.degrees(aH), 1))
        # ---- legs (IK to planted paws; front elbows bend back, hind stifles bend forward)
        lie_paw = {'nf': Sj[0] + 0.30, 'ff': Sj[0] + 0.24, 'nh': Hj[0] + 0.25, 'fh': Hj[0] + 0.21}
        legs = {}
        for leg in ('ff', 'fh', 'nh', 'nf'):
            fx, fy, stance = feet[leg]
            lx = L_(fx)
            gl = ground(fx)
            lp = np.array([lerp(lx, lie_paw[leg], lie), lerp(fy, ground(x0 + dirW * sx * lie_paw[leg]) + 0.0, lie)])
            front = leg.endswith('f')
            if front:
                wrist = lp + np.array([lerp(-0.01, -0.07, lie), lerp(0.06, 0.03, lie)])
                elbow, wrist2, cl = ik2(Sj, wrist, LEG['fu'], LEG['fl'], bend=-1)
                ang = math.degrees(math.atan2(*(wrist2 - elbow)[::-1]) - math.atan2(*(elbow - Sj)[::-1]))
                ang = (ang + 180) % 360 - 180
                if not (-5 <= ang <= 150): self.limit_log.append((i, leg, 'elbow', round(ang, 1)))
                parts = [capsule(Sj, elbow, 0.058, 0.04), capsule(elbow, wrist2, 0.032, 0.025),
                         capsule(wrist2, lp + np.array([0.035, 0.012]), 0.026, 0.022),
                         ellipse(lp + np.array([0.04, 0.018]), 0.045, 0.02, 14)]
                legs[leg] = (parts, dict(elbow=round(ang, 1)))
            else:
                hock = lp + np.array([lerp(-0.05, -0.15, lie), lerp(0.14, 0.025, lie)])
                stifle, hock2, cl = ik2(Hj, hock, LEG['hu'], LEG['hl'], bend=+1)
                ang = math.degrees(math.atan2(*(hock2 - stifle)[::-1]) - math.atan2(*(stifle - Hj)[::-1]))
                ang = (ang + 180) % 360 - 180
                if not (-170 <= ang <= 5): self.limit_log.append((i, leg, 'stifle', round(ang, 1)))
                parts = [capsule(Hj, stifle, 0.085, 0.045), capsule(stifle, hock2, 0.04, 0.027),
                         capsule(hock2, lp + np.array([0.02, 0.012]), 0.028, 0.022),
                         ellipse(lp + np.array([0.035, 0.016]), 0.042, 0.019, 14)]
                legs[leg] = (parts, dict(stifle=round(ang, 1)))
            row[leg + '_paw'] = [round(fx, 3), round(fy, 3), int(stance)]
        for leg in ('ff', 'fh'):
            for p in legs[leg][0]: fills.append(W_(p))
        # ---- tail chain
        tau = P['tail']; wag = P['wag']
        back = interp(tau, [0, 0.3, 0.5, 1.0, 1.35], [20, -50, -58, -86, -104])
        back += wag * 26 * math.sin(2 * math.pi * 3.1 * P['t'])
        curl = interp(tau, [0, 0.5, 1.35], [8, 4, -18])
        back = lerp(back, -12 + 6 * math.sin(2 * math.pi * 3.1 * P['t']) * wag, lie)
        curl = lerp(curl, 3, lie)
        pts = [tail0]; ang = math.pi - D(back) - aH * 0
        a = math.pi - D(back)
        for k, l in enumerate(TAIL_SEG):
            nxt = pts[-1] + l * np.array([math.cos(a), math.sin(a)])
            if lie > 0.3: nxt[1] = max(nxt[1], 0.03)
            pts.append(nxt); a -= D(curl)
        fills.append(W_(tail_shape(pts, [0.028, 0.04, 0.046, 0.04, 0.02])))
        row['tail_deg'] = round(back, 1)
        # ---- body pieces
        fills.append(W_(hind)); fills.append(W_(fore))
        for leg in ('nh', 'nf'):
            for p in legs[leg][0]: fills.append(W_(p))
        # ---- neck & head
        h = P['head']
        aN = interp(h, [0, 0.15, 0.45, 0.9, 1.25], [-34, -20, 6, 50, 66])
        aHd = interp(h, [0, 0.15, 0.45, 1.0, 1.25], [-62, -52, -30, -12, 2])
        aN = lerp(aN, interp(rest, [0, 1], [aN, -32]), lie * rest)
        aHd = lerp(aHd, -9, lie * rest)
        # head leads the turn (my acting rule).  Refusal: the head is averted -- swapped for the end-on
        # head seen from behind, dropped low -- before the body turns.  Return: lying with its back to the
        # door, the head swings back over the withers (the profile head flipped on its pin) to look.
        headmode = 'profile'
        if hb > 0 and P.get('hbmode') == 'avert':
            aN = lerp(aN, aN - 8, smooth(hb)); aHd = lerp(aHd, aHd - 10, smooth(hb))
            if hb >= 0.45: headmode = 'endon'
        elif hb > 0:
            aNb = 150 + 22 * (1 - min(1, h)); aHb = 180 + 18
            aN = lerp(aN, aNb, smooth(hb)); aHd = lerp(aHd, aHb, smooth(hb))
            if 0.35 < hb < 0.65: headmode = 'endon'
            elif hb >= 0.65: headmode = 'mirror'
        if look > 0:
            aN = lerp(aN, 62, smooth(look))
            if look >= 0.6: headmode = 'back'
        aNr = D(aN); aHr = D(aHd)
        neck = place(NECK, neck0, aNr)
        hp = neck0 + NECK_LEN * np.array([math.cos(aNr), math.sin(aNr)])
        fills.append(W_(neck))
        ear_ang = D(interp(max(0, min(1, P['ear'])), [0, 1], [168, 98]))
        hsx = 1.0
        if headmode in ('profile', 'mirror'):
            if look > 0: hsx = 1 - min(look, 0.6) / 0.6 * 0.55
            if hb > 0 and P.get('hbmode') == 'avert': hsx = 1 - min(hb, 0.45) / 0.45 * 0.55
            if headmode == 'mirror':
                # the same head piece flipped on its pin, pointing back over the shoulder
                a_ = D(aHd)
                hd = place(HEAD * [1, -1], hp, a_); ey = place(EYE * [1, -1], hp, a_)
                mz = place(MUZZLE * [1, -1], hp, a_)
                sk = place(CRANIUM * [1, -1], hp, a_)
                epin = place(EAR_PIN[None] * [1, -1], hp, a_)[0]
                ear = place(EAR * [1, -1], epin, a_ - ear_ang)
            else:
                hd = place(HEAD, hp, aHr, hsx)
                ey = place(EYE, hp, aHr, hsx)
                mz = place(MUZZLE, hp, aHr, hsx)
                sk = place(CRANIUM, hp, aHr, hsx)
                epin = place(EAR_PIN[None], hp, aHr, hsx)[0]
                ear = place(EAR, epin, aHr + ear_ang)
            fills.append(W_(ear)); fills.append(W_(hd)); holes.append(W_(ey))
            muzzle.append(W_(mz)); skull.append(W_(sk))
            if P['ear'] > 0.5 and headmode == 'profile':
                ear2 = place(EAR, epin + rot2(np.array([[0.028, 0.0]]), aHr)[0] * [hsx, 1], aHr + ear_ang - D(12))
                fills.append(W_(ear2))
        else:
            # end-on replacement head (screen-facing; from behind for 'back', from the front for 'endon')
            front = headmode == 'endon'
            cw = W_((hp + rot2(np.array([[0.04, 0.0]]), aHr)[0])[None])[0]
            hdw = ellipse(cw, 0.066, 0.06, 22)
            ee = interp(max(0, min(1, P['ear'])), [0, 1], [0.0, 1.0])
            for s_ in (-1, 1):
                b0 = cw + np.array([s_ * 0.018, 0.045]); b1 = cw + np.array([s_ * 0.066, 0.005])
                tip = cw + np.array([s_ * (0.065 + 0.07 * (1 - ee)), 0.03 + 0.08 * ee])
                fills.append(catmull([b0, (b0 + tip) / 2 + [s_ * -0.004, 0.0], tip, (tip + b1) / 2 + [s_ * 0.01, 0], b1], 3))
            fills.append(hdw); skull.append(hdw)
            if front:
                fills.append(ellipse(cw + np.array([0, -0.05]), 0.04, 0.05, 16))
                for s_ in (-1, 1): holes.append(ellipse(cw + [s_ * 0.027, 0.01], 0.01, 0.006, 10))
            else:
                fills.append(ellipse(cw + np.array([0, -0.035]), 0.05, 0.03, 16))   # nape ruff
        row.update(neck_deg=round(aN, 1), head_deg=round(aHd, 1), head=headmode,
                   ear_deg=round(math.degrees(ear_ang), 1))
        return dict(fills=fills, holes=holes, muzzle=muzzle, skull=skull, row=row)

    def pose_endon(self, P, W_, row):
        """End-on replacement puppet: rear view while turning away, front view while turning back."""
        x0 = P['x']; cr = P['crouch']; lie = P['lie']
        yM = lerp(0.47 - 0.07 * cr, 0.20, lie)
        fills, holes, skull = [], [], []
        def at(dx, dy): return np.array([x0 + dx, dy])
        if P['endon'] == 'rear':
            fills.append(ellipse(at(0, yM + 0.07), 0.12, 0.09))                  # shoulders beyond
            fills.append(catmull([at(-0.15, yM + 0.03), at(0, yM + 0.10), at(0.15, yM + 0.03),
                                  at(0.16, yM - 0.10), at(0.10, yM - 0.17), at(-0.10, yM - 0.17),
                                  at(-0.16, yM - 0.10)], 4))                    # rump
            for s_ in (-1, 1):
                fills.append(capsule(at(s_ * 0.10, yM - 0.10), at(s_ * 0.085, 0.03), 0.06, 0.028))
                fills.append(ellipse(at(s_ * 0.09, 0.016), 0.038, 0.018))
            fills.append(tail_shape([at(0, yM + 0.0), at(0.005, yM - 0.10), at(0.0, yM - 0.19), at(-0.01, yM - 0.26)],
                                    [0.03, 0.04, 0.04, 0.025]))             # tucked tail hangs between
            row.update(head='hidden', body='endon-rear')
        else:
            fills.append(ellipse(at(0, yM - 0.03), 0.155, 0.15))
            for s_ in (-1, 1):
                fills.append(capsule(at(s_ * 0.075, yM - 0.10), at(s_ * 0.075, 0.03), 0.05, 0.035))
                fills.append(ellipse(at(s_ * 0.08, 0.016), 0.04, 0.02))
            hh = interp(P['head'], [0, 0.5, 1.0], [0.04, 0.14, 0.22])
            fills.append(capsule(at(0, yM + 0.02), at(0, yM + hh - 0.02), 0.095, 0.075))
            c = at(0, yM + hh + 0.04)
            hdw = ellipse(c, 0.068, 0.062, 22); fills.append(hdw); skull.append(hdw)
            ee = interp(max(0, min(1, P['ear'])), [0, 1], [0.0, 1.0])
            for s_ in (-1, 1):
                b0 = c + [s_ * 0.018, 0.045]; b1 = c + [s_ * 0.066, 0.005]
                tip = c + [s_ * (0.065 + 0.07 * (1 - ee)), 0.03 + 0.08 * ee]
                fills.append(catmull([b0, tip, b1], 3))
                holes.append(ellipse(c + [s_ * 0.027, 0.01], 0.01, 0.006, 10))
            fills.append(ellipse(c + [0, -0.05], 0.04, 0.05, 16))
            row.update(head='endon-front', body='endon-front')
        return dict(fills=fills, holes=holes, muzzle=[], skull=skull, row=row)


# ---------------------------------------------------------------- the person: cut pieces
BODICE = catmull([(-0.11, 0.0), (0.10, 0.0), (0.12, 0.12), (0.135, 0.25), (0.11, 0.34), (0.055, 0.42),
                  (0.02, 0.45), (-0.04, 0.45), (-0.10, 0.40), (-0.125, 0.25), (-0.125, 0.10)], 5)
COLLAR_HOLES = [ellipse((0.02 + 0.03 * k, 0.40 - 0.025 * k), 0.009, 0.009, 8) for k in range(3)]
HEAD_P = catmull([(-0.05, 0.0), (0.035, 0.0), (0.05, 0.05), (0.085, 0.07), (0.085, 0.09), (0.09, 0.105),
                  (0.085, 0.118), (0.10, 0.14), (0.108, 0.152), (0.085, 0.168), (0.088, 0.20), (0.07, 0.235),
                  (0.02, 0.262), (-0.05, 0.252), (-0.09, 0.21), (-0.098, 0.16), (-0.085, 0.09), (-0.06, 0.035)], 4)
HEAD_P_OPEN = catmull([(-0.05, 0.0), (0.035, 0.0), (0.05, 0.045), (0.08, 0.06), (0.085, 0.08), (0.075, 0.098),
                       (0.088, 0.118), (0.10, 0.14), (0.108, 0.152), (0.085, 0.168), (0.088, 0.20), (0.07, 0.235),
                       (0.02, 0.262), (-0.05, 0.252), (-0.09, 0.21), (-0.098, 0.16), (-0.085, 0.09), (-0.06, 0.035)], 4)
BUN = ellipse((-0.115, 0.205), 0.055, 0.05, 20)
BUN_CLIP = [ellipse((-0.115 + 0.03 * math.cos(a), 0.205 + 0.028 * math.sin(a)), 0.007, 0.007, 8)
            for a in np.linspace(0, 2 * math.pi, 7, endpoint=False)]
P_EYE = ellipse((0.058, 0.178), 0.013, 0.007, 10)

def hand_piece(kind):
    """Hands in the wrist frame (+x along the forearm). Thumb is always a separate cut lobe."""
    parts = []
    if kind == 'point':
        parts.append(ellipse((0.04, 0.0), 0.045, 0.033, 16))                      # fist
        parts.append(capsule((0.06, 0.012), (0.15, 0.016), 0.012, 0.009))           # index
        parts.append(capsule((0.03, 0.025), (0.07, 0.045), 0.011, 0.009))           # thumb, apart
    elif kind == 'open':
        parts.append(catmull([(0.0, -0.03), (0.08, -0.035), (0.09, 0.025), (0.0, 0.03)], 4))
        for k, (dy, l) in enumerate([(0.022, 0.085), (0.007, 0.095), (-0.009, 0.09), (-0.024, 0.07)]):
            parts.append(capsule((0.08, dy), (0.08 + l, dy * 1.9), 0.0095, 0.008))
        parts.append(capsule((0.03, 0.03), (0.075, 0.085), 0.012, 0.009))          # thumb spread up
    else:  # offer: palm up, fingers slightly curled up, thumb lifted
        parts.append(catmull([(0.0, -0.025), (0.085, -0.03), (0.095, 0.01), (0.0, 0.025)], 4))
        for k, dy in enumerate([0.004, -0.008, -0.019]):
            parts.append(capsule((0.085, dy), (0.165, dy + 0.02 + 0.006 * k), 0.009, 0.0075))
        parts.append(capsule((0.04, 0.02), (0.085, 0.07), 0.011, 0.0085))
    return parts

class PersonRig:
    def __init__(self):
        self.feet_phase = 0.0
        self.prevx = None

    def pose(self, i, P):
        x0 = P['x']; sitE = smooth(P['sit']); reach = P['reach']; low = P['low']
        call = P['call']; soft = P['soft']; mouth = P['mouth']
        if self.prevx is not None: self.feet_phase += abs(x0 - self.prevx) * 13.0
        self.prevx = x0
        def W_(p):
            p = np.atleast_2d(np.asarray(p, float)); return np.stack([x0 + p[:, 0], p[:, 1]], 1)
        fills, holes = [], []
        row = dict(i=i)
        # sitting = kneeling down onto the heels beside the door (seiza): the skirt pools on the floor
        hip = np.array([lerp(0.0, -0.06, sitE), lerp(0.95, 0.24, sitE)])
        lean = D(-(34 * reach + 24 * low * sitE + 3 * call * (1 - sitE)))
        st = self.feet_phase
        ph = [math.sin(st), math.sin(st + math.pi)]
        feet = []
        for k, s_ in enumerate((1, -1)):
            fx = 0.05 * s_ + 0.06 * ph[k] * (1 - sitE)
            fy = max(0, 0.04 * math.cos(st + k * math.pi)) * (1 - sitE) if P['walking'] else 0.0
            feet.append(np.array([fx, fy]))
        knees = []
        for k, f in enumerate(feet):
            ankle = f + np.array([-0.02, 0.075])
            kn, an, _ = ik2(hip + [0.01 * (1 - 2 * k), 0], ankle, 0.45, 0.43, bend=+1)
            kn = kn * (1 - sitE) + np.array([0.36 - 0.03 * k, 0.07]) * sitE
            knees.append((kn, an))
        if sitE < 0.5:
            for k, (kn, an) in enumerate(knees):
                fills.append(W_(capsule(an + [-0.01, -0.04], feet[k] + [0.10, 0.012], 0.028, 0.02)))
        kn = knees[0][0]
        hemY = lerp(0.055, 0.0, sitE)
        Wf = hip + rot2(np.array([[0.10, 0.0]]), lean)[0]; Wb = hip + rot2(np.array([[-0.11, 0.0]]), lean)[0]
        kf = kn + np.array([0.06, 0.05])
        hem_f = np.array([lerp(kn[0] + 0.17, kn[0] + 0.11, sitE), hemY])
        hem_b = np.array([lerp(hip[0] - 0.26, hip[0] - 0.30, sitE), hemY + 0.01 * (1 - sitE)])
        seat_b = np.array([hip[0] - lerp(0.15, 0.20, sitE), lerp(hip[1] - 0.35, 0.06, sitE)])
        skirt_outline = [Wb, Wf, kf]
        # scalloped lace hem
        n = 9
        for k in range(n + 1):
            p = hem_f + (hem_b - hem_f) * (k / n)
            skirt_outline.append(p)
            if k < n:
                q = hem_f + (hem_b - hem_f) * ((k + 0.5) / n) + np.array([0, -0.022])
                skirt_outline.append(q)
        skirt_outline += [seat_b]
        skirt = catmull(skirt_outline, 3)
        fills.append(W_(skirt))
        for k in range(1, n):
            p = hem_f + (hem_b - hem_f) * (k / n) + np.array([0, 0.05])
            holes.append(W_(ellipse(p, 0.011, 0.014, 10)))
            if k % 2 == 0: holes.append(W_(ellipse(p + [0, 0.045], 0.007, 0.007, 8)))
        # far arm (behind)
        sh = hip + rot2(np.array([[0.0, 0.385]]), lean)[0]
        ua = D(-98); fa = D(-84)
        if sitE > 0.5: ua = D(-80); fa = D(-60)
        e = sh + 0.29 * np.array([math.cos(ua), math.sin(ua)]); w = e + 0.25 * np.array([math.cos(fa), math.sin(fa)])
        fills.append(W_(capsule(sh + [-0.03, 0], e, 0.04, 0.032))); fills.append(W_(capsule(e, w, 0.03, 0.024)))
        fills.append(W_(place(hand_piece('open')[0], w, fa)))
        # bodice
        bod = place(BODICE, hip, lean); fills.append(W_(bod))
        for c in COLLAR_HOLES: holes.append(W_(place(c, hip, lean)))
        # head
        neck = hip + rot2(np.array([[0.0, 0.445]]), lean)[0]
        tilt = D(7 * call - 11 * soft - 6 * low * sitE + 4 * reach)
        hpiece = HEAD_P_OPEN if mouth > 0.35 else HEAD_P
        ha = lean * 0.5 + tilt
        fills.append(W_(place(hpiece, neck, ha))); fills.append(W_(place(BUN, neck, ha)))
        holes.append(W_(place(P_EYE, neck, ha)))
        for c in BUN_CLIP: holes.append(W_(place(c, neck, ha)))
        # near arm: rest / call (point at the floor: "here") / reach (grasp) / offer low (palm up)
        rest_u, rest_f = -96, -80
        cu, cf = -38, -58
        ru, rf = -8, -2
        lu, lf = -40, -36
        u_ = rest_u; f_ = rest_f
        u_ = lerp(u_, cu, call); f_ = lerp(f_, cf, call)
        u_ = lerp(u_, ru, reach); f_ = lerp(f_, rf, reach)
        u_ = lerp(u_, lu, low); f_ = lerp(f_, lf, low)
        ua = D(u_) ; fa = D(f_)
        e = sh + 0.29 * np.array([math.cos(ua), math.sin(ua)]); w = e + 0.26 * np.array([math.cos(fa), math.sin(fa)])
        fills.append(W_(ellipse(sh + [0.0, -0.01], 0.065, 0.055, 16)))         # puff sleeve
        fills.append(W_(capsule(sh, e, 0.042, 0.034))); fills.append(W_(capsule(e, w, 0.031, 0.025)))
        cuff = place(np.array([[-0.03, -0.035], [0.0, -0.045], [0.0, 0.045], [-0.03, 0.035]]), w, fa)
        fills.append(W_(cuff))
        hk = 'rest'
        if reach > 0.3: hk = 'open'
        elif call > 0.4: hk = 'point'
        elif low > 0.3: hk = 'offer'
        if hk == 'rest':
            for p in hand_piece('open')[:1]: fills.append(W_(place(p, w, fa)))
            fills.append(W_(place(capsule((0.05, 0.0), (0.12, -0.01), 0.022, 0.012), w, fa)))
            fills.append(W_(place(capsule((0.03, 0.025), (0.065, 0.045), 0.01, 0.008), w, fa)))
        else:
            ang = fa
            if hk == 'point': ang = fa + D(-12)
            if hk == 'offer': ang = fa + D(34)
            for p in hand_piece(hk): fills.append(W_(place(p, w, ang)))
        hand_tip = W_(w[None])[0]
        row.update(person_hip=[round(hip[0] + x0, 3), round(hip[1], 3)], lean=round(math.degrees(lean), 1),
                   arm=[round(u_, 1), round(f_, 1)], hand=hk, mouth=int(mouth > 0.35),
                   skirt='seated' if sitE > 0.5 else 'standing', hand_x=round(hand_tip[0], 3))
        return dict(fills=fills, holes=holes, row=row)
