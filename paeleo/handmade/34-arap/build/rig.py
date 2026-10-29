"""Control handles for the engraved dog, and the solve that bends it.

The handle artist's choice: few handles, each a small rigid patch of vertices, never a skeleton.
  body (P_body): shoulder patch, hip patch, neck tip, tail middle, tail tip, four paws, four ankles (wrist/hock)
  head (P_head): skull patch at the joint, nose, the two ear tips
Knees are placed by two-bone IK; everything between the handles (the bend of each leg, belly, neck, the barrel
of the chest, the ears' fold) is what ARAP decides.
A pose is given in the dog's own frame (mm, y up, ground 0, facing left); the renderer mirrors it for facing right.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DRAW, MESH
from arap import ARAP, rigid_targets


def rot(v, a):
    c, s = np.cos(a), np.sin(a)
    v = np.asarray(v, float)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


class Piece:
    def __init__(self, name):
        m = np.load(os.path.join(MESH, name + '.npz'))
        self.name = name
        self.V, self.T, self.uv = m['V'], m['T'], m['uv']
        self.part, self.layer, self.weight = m['part'], m['layer'], m['weight']
        self.names = list(m['names'])
        self.meta = json.load(open(os.path.join(DRAW, name + '.json')))
        self.pts = {k: np.array(v) for k, v in self.meta['points'].items()}
        vp = -np.ones(len(self.V), int)       # a part for each vertex (from its triangles; the top layer wins)
        order = np.argsort(self.layer)
        for t in order:
            vp[self.T[t]] = self.part[t]
        self.vpart = vp

    def group(self, center, r, parts=None, ymax=None):
        d = np.sqrt(((self.V - center) ** 2).sum(1))
        sel = d < r
        if parts is not None:
            ids = [self.names.index(p) for p in parts]
            sel &= np.isin(self.vpart, ids)
        if ymax is not None:
            sel &= self.V[:, 1] < ymax
        return np.where(sel)[0]


LEGS = {'FN': 'near_fore', 'FF': 'far_fore', 'HN': 'near_hind', 'HF': 'far_hind'}


class DogP:
    """The profile dog: body + head pieces."""

    def __init__(self):
        self.body = Piece('P_body')
        self.head = Piece('P_head')
        b, p = self.body, self.body.pts
        self.c_sh = np.array([-235.0, 470.0]); self.c_hip = np.array([195.0, 455.0])
        H = {}
        H['shoulder'] = b.group(self.c_sh, 52, parts=['torso', 'neck', 'near_shoulder'])
        H['hip'] = b.group(self.c_hip, 55, parts=['torso', 'near_thigh'])
        H['neck'] = b.group(p['neck_top'] + np.array([0, -15]), 42, parts=['neck'])
        H['tail_mid'] = b.group(p['tail_mid'], 28, parts=['tail'])
        H['tail_tip'] = b.group(p['tail_tip'] + np.array([0, 10]), 26, parts=['tail'])
        for L, part in LEGS.items():
            H[L + '_paw'] = b.group(p[L + '_heel'] + np.array([-25, -5]), 48, parts=[part], ymax=34)
            H[L + '_ankle'] = b.group(p[L + '_ankle'] + np.array([0, 12]), 20, parts=[part])
            H[L + '_knee'] = b.group(p[L + '_knee'], 30, parts=[part])
        self.H = {k: v for k, v in H.items() if len(v)}
        self.hcent = {k: b.V[v].mean(0) for k, v in self.H.items()}
        self.solver = ARAP(b.V, b.T, b.weight, self.H)
        hd, hp = self.head, self.head.pts
        G = {}
        G['skull'] = hd.group(np.array([5.0, 25.0]), 42, parts=['skull'])
        G['nose'] = hd.group(hp['nose'] + np.array([12, 0]), 20, parts=['skull'])
        G['ear_near'] = hd.group(hp['ear_near_tip'] + np.array([0, -12]), 18, parts=['ear_near'])
        G['ear_far'] = hd.group(hp['ear_far_tip'] + np.array([0, -12]), 16, parts=['ear_far'])
        self.G = {k: v for k, v in G.items() if len(v)}
        self.gcent = {k: hd.V[v].mean(0) for k, v in self.G.items()}
        self.hsolver = ARAP(hd.V, hd.T, hd.weight, self.G)
        self.hsolver_m = ARAP(hd.V * [-1, 1], hd.T[:, [0, 2, 1]], hd.weight, self.G)
        self._last_flip = False
        self.neck_rest = self.hcent['neck']
        # where the head joint sits relative to the neck handle's centre, in rest
        self.joint_off = p['neck_top'] - self.neck_rest
        # the lying body: its own rest mesh (nothing has to fold)
        lb = Piece('P_lie'); self.lieb = lb; q = lb.pts
        self.c_sh_l = np.array([-235.0, 222.0]); self.c_hip_l = np.array([200.0, 160.0])
        K = {'shoulder': lb.group(self.c_sh_l, 52, parts=['torso', 'neck', 'near_shoulder']),
             'hip': lb.group(self.c_hip_l, 55, parts=['torso', 'near_thigh']),
             'neck': lb.group(q['neck_top'] + np.array([0, -15]), 42, parts=['neck']),
             'tail_mid': lb.group(q['tail_mid'], 28, parts=['tail']),
             'tail_tip': lb.group(q['tail_tip'] + np.array([-12, 0]), 26, parts=['tail']),
             'FN_paw': lb.group(q['FN_paw'], 40, parts=['near_fore']), 'FF_paw': lb.group(q['FF_paw'], 36, parts=['far_fore']),
             'HN_paw': lb.group(q['HN_paw'], 40, parts=['near_hind']), 'HN_hock': lb.group(q['HN_hock'], 28, parts=['near_hind'])}
        self.K = {k: v for k, v in K.items() if len(v)}
        self.kc = {k: lb.V[v].mean(0) for k, v in self.K.items()}
        self.lsolver = ARAP(lb.V, lb.T, lb.weight, self.K)
        self.neck_rest_l = self.kc['neck']; self.joint_off_l = q['neck_top'] - self.neck_rest_l
        # the head turned into the room (three-quarter from behind)
        lh = Piece('L_head'); self.lhead = lh
        LG = {'skull': lh.group(np.array([0.0, 40.0]), 45, parts=['skull', 'ruff']),
              'nose': lh.group(lh.pts['nose'] + np.array([14, -4]), 22, parts=['muzzle']),
              'ear_near': lh.group(lh.pts['ear_near_tip'] + np.array([0, -14]), 18, parts=['ear_near']),
              'ear_far': lh.group(lh.pts['ear_far_tip'] + np.array([0, -14]), 16, parts=['ear_far'])}
        self.LG = {k: v for k, v in LG.items() if len(v)}
        self.lgc = {k: lh.V[v].mean(0) for k, v in self.LG.items()}
        self.lhsolver = ARAP(lh.V, lh.T, lh.weight, self.LG)

    # ---------------------------------------------------------------- pose -> handle targets
    def targets(self, pose):
        """pose keys (all dog-frame mm / radians):
        sh, hip: new centres of the shoulder and hip patches; neck_a: neck swing (+ = head forward/down);
        paws: {L: (x, y, angle)}; ankles: {L: (x, y)}; tail_a, tail_curl; head_a: extra head pitch; ear: 0 flat .. 1 pricked
        """
        b = self.body
        tg = {}
        sh, hip = np.asarray(pose['sh'], float), np.asarray(pose['hip'], float)
        rest_vec = self.c_hip - self.c_sh
        new_vec = hip - sh
        pitch = np.arctan2(new_vec[1], new_vec[0]) - np.arctan2(rest_vec[1], rest_vec[0])
        tg['shoulder'] = rigid_targets(b.V, self.H['shoulder'], self.c_sh, sh, pitch)
        tg['hip'] = rigid_targets(b.V, self.H['hip'], self.c_hip, hip, pitch)
        # neck: swing the neck tip about the shoulder patch
        neck_a = pose.get('neck_a', 0.0) + pitch
        nv = rot(self.neck_rest - self.c_sh, neck_a) * pose.get('neck_len', 1.0)
        neck_c = sh + nv
        tg['neck'] = rigid_targets(b.V, self.H['neck'], self.neck_rest, neck_c, neck_a)
        # tail: swing about the hip; tail_a + = down/tucked (clockwise when facing left means toward -y...)
        tail_a = pose.get('tail_a', 0.0) + pitch
        tm_rest, tt_rest = self.hcent['tail_mid'], self.hcent['tail_tip']
        root = b.pts['tail_root']
        root_new = hip + rot(root - self.c_hip, pitch)
        tm = root_new + rot(tm_rest - root, tail_a)
        tt = tm + rot(tt_rest - tm_rest, tail_a + pose.get('tail_curl', 0.0))
        tg['tail_mid'] = rigid_targets(b.V, self.H['tail_mid'], tm_rest, tm, tail_a)
        tg['tail_tip'] = rigid_targets(b.V, self.H['tail_tip'], tt_rest, tt, tail_a + pose.get('tail_curl', 0.0))
        for L in LEGS:
            k = L + '_paw'
            if k in self.H:
                x, y, a = pose['paws'][L]
                tg[k] = rigid_targets(b.V, self.H[k], self.hcent[k], np.array([x, y], float), a)
            k = L + '_ankle'
            if k in self.H:
                ax, ay = pose['ankles'][L]
                aa = pose.get('ankle_a', {}).get(L, 0.0)
                tg[k] = rigid_targets(b.V, self.H[k], self.hcent[k], np.array([ax, ay]), aa)
            k = L + '_knee'
            if k in self.H:
                kx, ky = pose['knees'][L]
                tg[k] = rigid_targets(b.V, self.H[k], self.hcent[k], np.array([kx, ky]), pose.get('knee_a', {}).get(L, 0.0))
        return tg, neck_c, neck_a

    def solve_lie(self, pose, iters=8):
        lb = self.lieb
        st = float(pose.get('settle', 0.0)); br = float(pose.get('breath', 0.0))
        sh = self.c_sh_l + [0, st + br]; hip = self.c_hip_l + [0, 1.2 * st + 0.5 * br]
        v0 = self.c_hip_l - self.c_sh_l; v1 = hip - sh
        pitch = np.arctan2(v1[1], v1[0]) - np.arctan2(v0[1], v0[0])
        tg = {'shoulder': rigid_targets(lb.V, self.K['shoulder'], self.c_sh_l, sh, pitch),
              'hip': rigid_targets(lb.V, self.K['hip'], self.c_hip_l, hip, pitch)}
        neck_a = pose.get('neck_a_lie', 0.0) + pitch
        neck_c = sh + rot(self.neck_rest_l - self.c_sh_l, neck_a) * pose.get('neck_len', 1.0)
        tg['neck'] = rigid_targets(lb.V, self.K['neck'], self.neck_rest_l, neck_c, neck_a)
        ta = pose.get('tail_a_lie', 0.0)
        root = lb.pts['tail_root']; root_new = hip + rot(root - self.c_hip_l, pitch)
        tm = root_new + rot(self.kc['tail_mid'] - root, ta)
        tt = root_new + rot(self.kc['tail_tip'] - root, ta * 1.3)
        tg['tail_mid'] = rigid_targets(lb.V, self.K['tail_mid'], self.kc['tail_mid'], tm, ta)
        tg['tail_tip'] = rigid_targets(lb.V, self.K['tail_tip'], self.kc['tail_tip'], tt, ta * 1.3)
        for k in ('FN_paw', 'FF_paw', 'HN_paw', 'HN_hock'):
            if k in self.K:
                tg[k] = rigid_targets(lb.V, self.K[k], self.kc[k], self.kc[k] + [0, 0.25 * st if k == 'HN_hock' else 0], 0.0)
        X = self.lsolver.solve_repair(tg, iters=iters)
        nc = X[self.K['neck']].mean(0)
        return X, nc + rot(self.joint_off_l, neck_a), neck_a

    def solve(self, pose, iters=8, X0=None, Xh0=None):
        if pose.get('body') == 'lie':
            X, joint, neck_a = self.solve_lie(pose, iters)
            self.cur_body = self.lieb
            ha = neck_a + pose.get('head_a_lie', pose.get('head_a', 0.0))
        else:
            tg, neck_c, neck_a = self.targets(pose)
            X = self.solver.solve_repair(tg, iters=iters, X0=X0)
            nc = X[self.H['neck']].mean(0)
            joint = nc + rot(self.joint_off, neck_a)
            self.cur_body = self.body
            ha = neck_a + pose.get('head_a', 0.0)
        ear = pose.get('ear', 1.0)
        if pose.get('head_view') == 'L':
            # the head turned into the room: the back of the skull to us, the muzzle aimed away into the lit hall
            lh = self.lhead; V = lh.V
            ha = pose.get('L_a', 0.0)
            gt = {}
            for k, idx in self.LG.items():
                c = self.lgc[k]
                fa = 0.0
                if k.startswith('ear'):
                    fa = -(1 - ear) * 0.9
                    base = c + np.array([0, -95.0]); c2 = base + rot(c - base, fa)
                else:
                    c2 = c
                gt[k] = rigid_targets(V, idx, c, joint + rot(c2, ha), ha + fa)
            c_, s_ = np.cos(ha), np.sin(ha)
            Xh0 = joint + np.stack([c_ * V[:, 0] - s_ * V[:, 1], s_ * V[:, 0] + c_ * V[:, 1]], 1)
            Xh = self.lhsolver.solve_repair(gt, iters=10, X0=Xh0)
            self.cur_head = lh; self.cur_head_nose = Xh[self.LG['nose']].mean(0); self.cur_head_joint = joint
            return X, Xh
        flip = bool(pose.get('head_flip', False))
        sg = -1.0 if flip else 1.0
        if flip:      # the head looks the other way: its rest shape reflected (a Jacobian of determinant -1)
            ha = neck_a + pose.get('head_flip_a', 0.0)
        hd = self.head
        V = hd.V * [sg, 1]
        gc = {k: v * [sg, 1] for k, v in self.gcent.items()}
        gt = {}
        gt['skull'] = rigid_targets(V, self.G['skull'], gc['skull'], joint + rot(gc['skull'], ha), ha)
        gt['nose'] = rigid_targets(V, self.G['nose'], gc['nose'], joint + rot(gc['nose'], ha), ha)
        for e, base in (('ear_near', hd.pts['ear_near_base']), ('ear_far', hd.pts['ear_near_base'] - [25, 0])):
            if e in self.G:
                base = base * [sg, 1]
                fa = -(1 - ear) * 1.25 * sg             # flatten: the tip folds back
                tip = base + rot(gc[e] - base, fa)
                gt[e] = rigid_targets(V, self.G[e], gc[e], joint + rot(tip, ha), ha + fa)
        solver = self.hsolver_m if flip else self.hsolver
        c_, s_ = np.cos(ha), np.sin(ha)     # every frame starts from the rest head placed rigidly where it goes
        Xh0 = joint + np.stack([c_ * V[:, 0] - s_ * V[:, 1], s_ * V[:, 0] + c_ * V[:, 1]], 1)
        Xh = solver.solve_repair(gt, iters=10, X0=Xh0)
        self.cur_head = hd; self.cur_head_flip = flip
        self.cur_head_nose = Xh[self.G['nose']].mean(0); self.cur_head_joint = joint
        return X, Xh


def rest_pose(d):
    p = d.body.pts
    pose = dict(sh=d.c_sh.copy(), hip=d.c_hip.copy(), neck_a=0.0, tail_a=0.0, head_a=0.0, ear=1.0, paws={}, ankles={})
    for L in LEGS:
        k = L + '_paw'
        pose['paws'][L] = (d.hcent[k][0], d.hcent[k][1], 0.0)
        pose['ankles'][L] = tuple(d.hcent[L + '_ankle'])
    pose['knees'] = {L: tuple(d.hcent.get(L + '_knee', d.body.pts[L + '_knee'])) for L in LEGS}
    return pose


def leg_top(d, L, sh, hip, pitch):
    """Where a leg's top joint (shoulder or hip joint) is, given the solved patches."""
    p = d.body.pts[L + '_top']
    c0, c1 = (d.c_sh, sh) if L[0] == 'F' else (d.c_hip, hip)
    return np.asarray(c1) + rot(p - c0, pitch)


def ik_knee(d, L, top, ankle, bend):
    """Two-bone IK: the knee between a top joint and the ankle with the rest bone lengths. bend=+1 knee forward
    (toward -x, the stifle), -1 knee back (the elbow sits back of the line when the leg folds)."""
    p = d.body.pts
    a = np.linalg.norm(p[L + '_knee'] - p[L + '_top']); b = np.linalg.norm(p[L + '_ankle'] - p[L + '_knee'])
    v = np.asarray(ankle, float) - np.asarray(top, float); c = np.linalg.norm(v)
    c = np.clip(c, abs(a - b) + 1e-3, a + b - 1e-3)
    cosA = (a * a + c * c - b * b) / (2 * a * c)
    A = np.arccos(np.clip(cosA, -1, 1))
    u = v / max(np.linalg.norm(v), 1e-6)
    # rotate u by +-A: +A is counter-clockwise; facing left, a forward (−x) knee on a downward leg is clockwise
    k = np.asarray(top) + a * rot(u, -A * bend)
    return k


# ------------------------------------------------------------------ acting -> pose (profile)
LIE = {   # lying (sphinx): paw centre, ankle, knee, in the dog frame
    'FN': ((-545, 22), (-470, 34), (-300, 40)), 'FF': ((-475, 22), (-400, 34), (-230, 40)),
    'HN': ((60, 22), (175, 40), (30, 110)), 'HF': ((-10, 22), (105, 40), (-40, 110)),
}
LIE_SH = np.array([5.0, -248.0]); LIE_HIP = np.array([15.0, -300.0])
DEEP_SH = np.array([10.0, -125.0]); DEEP_HIP = np.array([10.0, -215.0])


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def pose_P(d, a, paws=None, lifts=None):
    """a: acts dict (crouch, lie, head, ear, tail, wag, wph, rest, look, breath).
    paws: optional {L: (x, y)} paw centres from the gait (standing only); lifts {L: swing 0..1}."""
    r = rest_pose(d)
    c = float(a.get('crouch', 0)); l = float(a.get('lie', 0)); h = float(a.get('head', 0.9))
    br = float(a.get('breath', 0))
    pitch = 0.0
    # standing (with crouch): shoulder and hip patches
    sh_s = d.c_sh + np.array([10 * c, -95 * c + br]); hip_s = d.c_hip + np.array([20 * c, -125 * c + br * 0.5])
    legs_s = {}
    for L in LEGS:
        pc = np.array(paws[L], float) if paws and L in paws else d.hcent[L + '_paw']
        sw = (lifts or {}).get(L, 0.0)
        an = pc + (d.hcent[L + '_ankle'] - d.hcent[L + '_paw'])
        if sw > 0:      # a swinging foot flexes: the ankle trails, the paw tips
            an = an + np.array([25 * np.sin(np.pi * sw), 0.0])
        legs_s[L] = [pc, an]
    def knees(sh, hip, legs, pit=0.0):
        out = {}
        for L in LEGS:
            top = leg_top(d, L, sh, hip, pit)
            out[L] = ik_knee(d, L, top, legs[L][1], +1 if L[0] == 'H' else -1)
        return out
    vec0 = d.c_hip - d.c_sh
    def pit(sh, hip):
        v = hip - sh
        return np.arctan2(v[1], v[0]) - np.arctan2(vec0[1], vec0[0])
    ks = knees(sh_s, hip_s, legs_s, pit(sh_s, hip_s))
    if l <= 0:
        sh, hip = sh_s, hip_s
        legs = {L: (legs_s[L][0], legs_s[L][1], ks[L]) for L in LEGS}
    else:
        # two segments: stand -> deep crouch (paws planted, knees by IK) -> lying (explicit joints)
        u = min(l / 0.5, 1.0); v = max((l - 0.5) / 0.5, 0.0)
        sh_d = d.c_sh + DEEP_SH; hip_d = d.c_hip + DEEP_HIP
        legs_d = {L: [legs_s[L][0], legs_s[L][1]] for L in LEGS}
        for L in ('FN', 'FF'):     # forefeet reach forward on the way down
            legs_d[L] = [legs_s[L][0] + [-90, 0], legs_s[L][1] + [-110, -20]]
        kd = knees(sh_d, hip_d, legs_d, pit(sh_d, hip_d))
        if v <= 0:
            sh = lerp(sh_s, sh_d, u); hip = lerp(hip_s, hip_d, u)
            legs = {L: (lerp(legs_s[L][0], legs_d[L][0], u), lerp(legs_s[L][1], legs_d[L][1], u), lerp(ks[L], kd[L], u)) for L in LEGS}
        else:
            sh = lerp(sh_d, d.c_sh + LIE_SH, v); hip = lerp(hip_d, d.c_hip + LIE_HIP, v)
            legs = {L: (lerp(legs_d[L][0], LIE[L][0], v), lerp(legs_d[L][1], LIE[L][1], v), lerp(kd[L], LIE[L][2], v)) for L in LEGS}
        sh = sh + [0, br * 0.6]; hip = hip + [0, br * 0.4]
    r['sh'], r['hip'] = sh, hip
    for L in LEGS:
        r['paws'][L] = (legs[L][0][0], legs[L][0][1], (-0.3 if L[0] == 'F' else 0.0) * min(max((l - 0.5) / 0.5, 0), 1))
        r['ankles'][L] = tuple(legs[L][1]); r['knees'][L] = tuple(legs[L][2])
    lv = min(max((l - 0.5) / 0.5, 0), 1)
    # joint patches turn with the bones they sit between (measured from the solved joint positions)
    pit_now = pit(sh, hip)
    r['ankle_a'] = {}; r['knee_a'] = {}
    P0 = d.body.pts
    def ang(v):
        return np.arctan2(v[1], v[0])
    def wrap(a):
        return (a + np.pi) % (2 * np.pi) - np.pi
    for L in LEGS:
        top = leg_top(d, L, sh, hip, pit_now)
        kn, an, pw = np.asarray(legs[L][2]), np.asarray(legs[L][1]), np.asarray(legs[L][0])
        a_up = wrap(ang(kn - top) - ang(P0[L + '_knee'] - P0[L + '_top']))
        a_lo = wrap(ang(an - kn) - ang(P0[L + '_ankle'] - P0[L + '_knee']))
        a_ft = wrap(ang(pw - an) - ang(d.hcent[L + '_paw'] - d.hcent[L + '_ankle']))
        r['knee_a'][L] = 0.5 * (a_up + a_lo)
        r['ankle_a'][L] = 0.5 * (a_lo + a_ft)
    # head and neck
    na_s = float(np.clip((0.9 - h) * 1.55, -0.35, 1.25)); ha_s = 0.35 * (0.9 - h)
    na_l = 0.25 + (0.7 - h) * 0.9; ha_l = 0.15 + 0.2 * (0.7 - h)
    rest_ = float(a.get('rest', 0)); look = float(a.get('look', 0))
    na_l = na_l * (1 - rest_) + 1.0 * rest_; ha_l = ha_l * (1 - rest_) + 0.25 * rest_
    na_l = na_l * (1 - look) + 0.32 * look; ha_l = ha_l * (1 - look) - 0.30 * look
    wl = smooth(l)
    r['neck_a'] = na_s * (1 - wl) + na_l * wl
    r['head_a'] = ha_s * (1 - wl) + ha_l * wl
    r['neck_len'] = 1.0 + 0.14 * look
    r['ear'] = float(np.clip(a.get('ear', 1.0), 0, 1))
    t_ = float(a.get('tail', 0.5)); w = float(a.get('wag', 0)); ph = float(a.get('wph', 0))
    ta = -(t_ - 0.5) * 1.0 + w * 0.45 * np.sin(ph)
    r['tail_a'] = ta * (1 - wl) + (0.5 + w * 0.3 * np.sin(ph)) * wl
    r['tail_curl'] = -0.35 * max(t_ - 0.8, 0) * (1 - wl) + 0.35 * wl
    # the lying body (its own mesh): arrives 70 mm high and settles; head and tail in its frame
    vv = smooth(min(max((l - 0.5) / 0.5, 0), 1))
    r['settle'] = 70.0 * (1 - vv)
    r['neck_a_lie'] = na_l; r['head_a_lie'] = ha_l
    r['tail_a_lie'] = w * 0.35 * np.sin(ph)
    r['breath'] = br
    return r


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ the substitution keys: rear and front views
class DogView:
    """R0 (rear) or F0 (front three-quarter): body + head, a handful of handles each."""

    def __init__(self, kind):
        self.kind = kind
        self.body = Piece(kind + '_body')
        self.head = Piece(kind + '_head')
        b, p = self.body, self.body.pts
        H = {}
        if kind == 'R0':
            H['back'] = b.group(np.array([0.0, 575.0]), 45, parts=['back'])
            H['hip'] = b.group(np.array([0.0, 470.0]), 40, parts=['tail', 'haunch_l', 'haunch_r'])
            H['tail_tip'] = b.group(p['tail_tip'] + [0, 15], 26, parts=['tail'])
            for k, part in (('pl', 'hind_l'), ('pr', 'hind_r'), ('fl', 'fore_l'), ('fr', 'fore_r')):
                H[k] = b.group(p[k], 40, parts=[part], ymax=45)
            H['hl_knee'] = b.group(np.array([-92.0, 180.0]), 26, parts=['hind_l'])
            H['hr_knee'] = b.group(np.array([92.0, 180.0]), 26, parts=['hind_r'])
        else:
            H['chest'] = b.group(np.array([0.0, 470.0]), 55, parts=['chest'])
            H['neck'] = b.group(np.array([0.0, 610.0]), 30, parts=['chest'])
            for k, part in (('pl', 'paw_l'), ('pr', 'paw_r'), ('hl', 'hind_l'), ('hr', 'hind_r')):
                H[k] = b.group(p[k], 40, parts=[part] + (['fore_' + k[1]] if k[0] == 'p' else []), ymax=45)
            H['fl_knee'] = b.group(np.array([-76.0, 200.0]), 26, parts=['fore_l'])
            H['fr_knee'] = b.group(np.array([76.0, 200.0]), 26, parts=['fore_r'])
        self.H = {k: v for k, v in H.items() if len(v)}
        self.hc = {k: b.V[v].mean(0) for k, v in self.H.items()}
        self.solver = ARAP(b.V, b.T, b.weight, self.H)
        hd = self.head
        G = {'skull': hd.group(np.array([0.0, 20.0]), 45, parts=['skull'])}
        for e in ('ear_l', 'ear_r'):
            G[e] = hd.group(hd.pts[e + '_tip'] + [0, -14], 18, parts=[e])
        if kind == 'F0':
            G['nose'] = hd.group(hd.pts['nose'] + [10, 0], 22, parts=['muzzle'])
        self.G = {k: v for k, v in G.items() if len(v)}
        self.gc = {k: hd.V[v].mean(0) for k, v in self.G.items()}
        self.hsolver = ARAP(hd.V, hd.T, hd.weight, self.G)
        self.neck_top = p['neck_top']

    def solve(self, a, iters=8, X0=None, Xh0=None):
        """a: crouch, lie (0..1: R0 only crouches), sx (width, arrival foreshortening), tail, wag, wph, ear,
        head_dx (head swing, mm), head_dy, head_a."""
        b = self.body
        c = float(a.get('crouch', 0)); sx = float(a.get('sx', 1.0)); low = float(a.get('lie', 0))
        tg = {}
        drop = 110 * c + 230 * low
        for k, idx in self.H.items():
            cen = self.hc[k].copy()
            new = cen.copy(); new[0] *= sx
            ang = 0.0
            if k in ('back', 'chest', 'neck'):
                new[1] -= drop * (0.85 if k != 'neck' else 0.8)
            elif k == 'hip':
                new[1] -= drop
            elif k.endswith('knee'):
                new[1] -= drop * 0.55
                new[0] += np.sign(cen[0]) * 25 * (c + low)
            elif k == 'tail_tip':
                t_ = float(a.get('tail', 0.5)); w = float(a.get('wag', 0)) * np.sin(float(a.get('wph', 0)))
                new[1] = cen[1] - drop + (0.5 - t_) * 160
                new[0] = cen[0] * sx + w * 70
                ang = -w * 0.5
            tg[k] = rigid_targets(b.V, idx, cen, new, ang, scale=1.0)
            if sx != 1.0:
                tg[k][:, 0] = (tg[k][:, 0] - new[0]) * sx + new[0]
        X = self.solver.solve_repair(tg, iters=iters, X0=X0)
        hd = self.head
        joint = self.neck_top * [sx, 1] + [float(a.get('head_dx', 0)), -drop * 0.8 + float(a.get('head_dy', 0))]
        ha = float(a.get('head_a', 0.0))
        gt = {}
        ear = float(np.clip(a.get('ear', 1.0), 0, 1))
        for k, idx in self.G.items():
            cen = self.gc[k]
            ea = 0.0
            if k.startswith('ear'):
                ea = (1 - ear) * (0.9 if k == 'ear_l' else -0.9)
                base = cen + np.array([0, -90.0])
                newc = base + rot(cen - base, ea)
            else:
                newc = cen
            pos = joint + rot(newc, ha)
            gt[k] = rigid_targets(hd.V, idx, cen, pos, ha + ea)
            if sx != 1.0:
                gt[k][:, 0] = (gt[k][:, 0] - pos[0]) * (0.5 + 0.5 * sx) + pos[0]
        Xh = self.hsolver.solve_repair(gt, iters=max(4, iters // 2), X0=Xh0)
        return X, Xh
