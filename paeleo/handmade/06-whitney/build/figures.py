"""SCION 06 · Whitney — the bodies, as parametric trajectories.

A body is a set of tubes; a tube is a chain of rings; a ring is a periodic function: M points at angles
theta_m = 2 pi m / M + phi_j(t), where phi_j(t) = (j mod 6 + 1) * W0 * (t - T_REUNION) is the ring's precession, a harmonic
series of rates. At t = T_REUNION + k * 8 s every ring's points line up into straight engraved stripes; between those
moments they wind into helices. Nothing is a bitmap: every dot on screen is a point on one of these curves.

dog(pose, t, osc) -> Points; person(pose, t) -> Points. A Points record is a dict of arrays:
  p (n,3) world metres; n (n,3) outward normal (for the light-pen shading); c (n,3) colour 0..1; w (n,) weight;
  part (n,) integer part id (for measurement: 0 torso, 1 neck, 2 head, 3 legs, 4 tail, 5 ears, 6 eyes/nose)
Proportions of the dog were measured from the archive dog's rig keys (kit/archive-dog/pose_agent_v8.json, frame 0):
chest->tail base 90 px for 0.80 m of torso, nose 30 px ahead of the neck, feet 55 px below the chest.
"""
import math
import numpy as np

W0 = 2 * math.pi / 8.0        # rad/s: the ring precession fundamental (an 8 s period)
T_REUNION = 24.0              # the rings align when the dog lies down on the sill

DOG_COL = np.array([0.72, 0.88, 1.00])
DOG_WARM = np.array([1.00, 0.86, 0.62])
HOT = np.array([1.00, 0.36, 0.42])
PERSON_COL = np.array([1.00, 0.70, 0.42])

RANK_CACHE = {}


def ranks(n, seed):
    """fixed visibility rank per point (the density of the compositional field selects points with rank < density)."""
    k = (n, seed)
    if k not in RANK_CACHE:
        # golden-ratio sequence: an even, deterministic thinning
        RANK_CACHE[k] = (np.arange(n) * 0.6180339887 + seed * 0.37) % 1.0
    return RANK_CACHE[k]


def norm(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def tube(centers, rx, ry, M, ref, phase, ripple=0.0, ripple_k=3, ripple_ph=0.0):
    """rings around a centre line. centers (K,3); rx, ry (K,) radii; ref (3,) direction that ry points along (projected);
    phase (K,) ring precession. Returns points (K*M,3) and normals."""
    C = np.asarray(centers, float); K = len(C)
    Tn = np.gradient(C, axis=0) if K > 1 else np.array([[1, 0, 0.]])
    Tn = norm(Tn)
    ref = np.broadcast_to(np.asarray(ref, float), C.shape)
    A1 = norm(ref - (ref * Tn).sum(1, keepdims=True) * Tn)
    A2 = np.cross(Tn, A1)
    th = 2 * math.pi * np.arange(M) / M
    TH = th[None, :] + np.asarray(phase)[:, None]
    rr = 1 + ripple * np.sin(ripple_k * TH + ripple_ph)
    ca, sa = np.cos(TH) * rr, np.sin(TH) * rr
    P = C[:, None, :] + ca[..., None] * np.asarray(rx)[:, None, None] * A2[:, None, :] \
        + sa[..., None] * np.asarray(ry)[:, None, None] * A1[:, None, :]
    Nn = norm(np.cos(TH)[..., None] * A2[:, None, :] + np.sin(TH)[..., None] * A1[:, None, :])
    return P.reshape(-1, 3), Nn.reshape(-1, 3)


def rotY(v, a):
    """rotate vectors about the world up axis (y) so that forward (-1,0,0) at a=0 goes to F(a) = (-cos a, 0, -sin a)."""
    c, s = math.cos(a), math.sin(a)
    v = np.asarray(v, float)
    x, y, z = v[..., 0], v[..., 1], v[..., 2]
    return np.stack([c * x - s * z, y, s * x + c * z], -1)


def ik2(a, target, l1, l2, bend):
    """two-bone IK in 3D: joint at distance l1 from a, ending at target; `bend` is the direction the joint points."""
    a = np.asarray(a, float); target = np.asarray(target, float)
    d = target - a; L = np.linalg.norm(d)
    L = min(max(L, 1e-4), l1 + l2 - 1e-4)
    dn = d / (np.linalg.norm(d) + 1e-9)
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0))
    b = np.asarray(bend, float); b = b - b.dot(dn) * dn; b = b / (np.linalg.norm(b) + 1e-9)
    j = a + dn * x + b * h
    end = a + dn * L
    return j, end


def seg(a, b, k):
    s = np.linspace(0, 1, k)[:, None]
    return np.asarray(a)[None, :] * (1 - s) + np.asarray(b)[None, :] * s


def chain(pts, k_each):
    out = [seg(pts[i], pts[i + 1], k_each)[(1 if i else 0):] for i in range(len(pts) - 1)]
    return np.concatenate(out, 0)


class Builder:
    def __init__(self):
        self.P, self.N, self.C, self.W, self.part = [], [], [], [], []

    def add(self, P, Nn, col, w, part):
        P = np.asarray(P, float).reshape(-1, 3)
        self.P.append(P); self.N.append(np.asarray(Nn, float).reshape(-1, 3))
        self.C.append(np.broadcast_to(np.asarray(col, float), P.shape).copy())
        self.W.append(np.broadcast_to(np.asarray(w, float), (len(P),)).copy())
        self.part.append(np.full(len(P), part))

    def done(self):
        return dict(p=np.concatenate(self.P), n=np.concatenate(self.N), c=np.concatenate(self.C),
                    w=np.concatenate(self.W), part=np.concatenate(self.part))


def ring_phase(h, K, t):
    """the meridians' phase along a tube of K stations, harmonic number h: a slow common rotation plus a twist that
    winds the lines into helices and unwinds them to straight engraved lines at T_REUNION + 8 k s."""
    s = np.linspace(0, 1, K)
    rot = 0.35 * h * W0 * (t - T_REUNION)
    tw = 1.6 * math.sin(0.5 * W0 * (t - T_REUNION))
    return rot + h * tw * s


def dense(a, n):
    """resample a station array (K,...) to n stations along its length."""
    a = np.asarray(a, float); K = len(a)
    x = np.linspace(0, 1, K); xn = np.linspace(0, 1, n)
    if a.ndim == 1:
        return np.interp(xn, x, a)
    return np.stack([np.interp(xn, x, a[:, k]) for k in range(a.shape[1])], 1)


def dog(q, t, breath, agit, warmth, density):
    """q: pose dict for one frame (u, yaw, head_rel, head_pitch, lie, rest, crouch, ear, tail, wag, d_fwd, moving, look).
    breath: the dog oscillator phase (rad). agit: 0..1 the commands' strike. warmth: 0..1 the door light on it."""
    B = Builder()
    lie, crouch = q['lie'], q['crouch'] * (1 - q['lie'])
    yaw = q['yaw']
    origin = np.array([q['u'], 0.0, 0.0])

    kap = q.get('bend', 0.0) / 0.84       # spine curvature (rad/m): a turning dog curls into a C, head leading

    def W(v):  # dog-local (forward f, up y, side l) -> world. local forward is -x at yaw 0.
        v = np.asarray(v, float)
        fl, yl, ll = v[..., 0], v[..., 1], v[..., 2]
        if abs(kap) > 1e-4:
            th = kap * fl
            fl, ll = np.sin(th) / kap - ll * np.sin(th), (1 - np.cos(th)) / kap + ll * np.cos(th)
        loc = np.stack([-fl, yl, ll], -1)
        return origin + rotY(loc, yaw)

    def Wd(v):
        v = np.asarray(v, float)
        return rotY(np.stack([-v[..., 0], v[..., 1], v[..., 2]], -1), yaw)

    col = DOG_COL * (1 - 0.55 * warmth) + DOG_WARM * 0.55 * warmth
    col = col * (1 - 0.6 * agit) + HOT * 0.6 * agit
    br = 1 + 0.035 * math.sin(breath)                         # the dog's breath: torso girth at the dog's rate
    ripple = 0.03 + 0.22 * agit                                # bristle under the call
    # --- spine (rump -> withers -> chest front), lowered by crouch and by lying
    drop_sh = 0.10 * crouch + 0.30 * lie
    drop_hp = 0.14 * crouch + 0.32 * lie
    sh_y, hp_y = 0.60 - drop_sh, 0.56 - drop_hp
    s = np.linspace(0, 1, 15)
    f = -0.40 + 0.84 * s
    spine_y = hp_y + (sh_y - hp_y) * s + 0.025 * np.sin(math.pi * s) * (1 + 1.5 * crouch)
    ry = np.interp(s, [0, .12, .4, .72, .9, 1], [.07, .105, .10, .165, .15, .09]) * br
    rx = np.interp(s, [0, .12, .4, .72, .9, 1], [.06, .095, .085, .115, .11, .07]) * br
    dy = np.interp(s, [0, .12, .4, .72, .9, 1], [.02, .06, .075, .13, .12, .10])
    cy = spine_y - dy
    floor = np.minimum(cy - ry - 0.015, 0)
    cy = cy - floor
    cent = dense(np.stack([f, cy, np.zeros_like(f)], 1), 46)
    rx, ry = dense(rx, 46), dense(ry, 46)
    P, Nn = tube(W(cent), rx, ry, 11, np.array([0, 1, 0]), ring_phase(1, 46, t), ripple, 3, breath)
    B.add(P, Nn, col, 1.0, 0)
    withers = np.array([0.34, sh_y + 0.0, 0])
    # --- neck and head: pitch from the score's head, yaw relative to the body (head leads the turns)
    hp = q['head_pitch'] * (1 - q['rest']) + math.radians(-38) * q['rest']
    yr = q['head_rel']
    nyaw, hyaw = -0.62 * yr, -yr          # local head yaw is the negative of the world yaw offset
    def dirv(pitch, yw):
        # local direction: forward rotated by pitch (up) and yaw (about up; + toward the dog's +l side)
        return np.array([math.cos(pitch) * math.cos(yw), math.sin(pitch), math.cos(pitch) * math.sin(yw)])
    nb = withers + np.array([0.02, -0.03, 0])
    npitch = 0.75 * hp + math.radians(18)
    if lie > 0:
        npitch = npitch * (1 - 0.3 * lie)
    nd = dirv(npitch, nyaw)
    ncent = seg(nb, nb + 0.24 * nd, 12)
    # head pitch for chin-on-paws: the head lies along the floor ahead of the shoulders
    P, Nn = tube(W(ncent), np.linspace(.08, .062, 12), np.linspace(.10, .072, 12), 9, Wd([0, 1, 0]), ring_phase(2, 12, t), ripple * .5, 3, breath)
    B.add(P, Nn, col, 1.0, 1)
    hd = dirv(hp - math.radians(6), hyaw)
    skull = ncent[-1] + 0.05 * hd
    # keep the head above the floor
    skull[1] = max(skull[1], 0.085)
    hcent = np.concatenate([seg(skull - 0.06 * hd, skull + 0.05 * hd, 4), seg(skull + 0.07 * hd, skull + 0.07 * hd + 0.15 * dirv(hp - math.radians(22), hyaw), 4)])
    hrx = np.array([.045, .07, .075, .06, .05, .042, .034, .024])
    hry = np.array([.05, .075, .08, .065, .045, .038, .03, .022])
    hcent, hrx, hry = dense(hcent, 22), dense(hrx, 22), dense(hry, 22)
    P, Nn = tube(W(hcent), hrx, hry, 10, Wd([0, 1, 0]), ring_phase(3, 22, t), ripple * .4, 3, breath)
    B.add(P, Nn, col, 1.05, 2)
    nose = hcent[-1] + 0.02 * hd
    side = np.array([-math.sin(hyaw), 0, math.cos(hyaw)])  # local lateral of the head
    up = np.cross(side, hd); up = up / (np.linalg.norm(up) + 1e-9)
    if up[1] < 0: up = -up
    eyes = [skull + 0.06 * hd + 0.035 * up + 0.042 * side, skull + 0.06 * hd + 0.035 * up - 0.042 * side]
    B.add(W(np.array([nose] + eyes)), np.tile(Wd(hd), (3, 1)), np.array([1, 1, 1.0]), 2.6, 6)
    # ears: triangle outlines; ear 1 pricked (tip up), 0 flat (tip back along the neck)
    ea = q['ear']
    for sg in (1, -1):
        base_f = skull + 0.01 * hd + 0.055 * up + 0.04 * sg * side
        base_b = skull - 0.04 * hd + 0.05 * up + 0.045 * sg * side
        tipdir = norm(up * (0.25 + 0.95 * ea) - hd * (1.1 - 0.6 * ea) + 0.25 * sg * side)
        tip = (base_f + base_b) / 2 + 0.10 * tipdir
        tri = np.concatenate([seg(base_f, tip, 6), seg(tip, base_b, 6)[1:], seg(base_b, base_f, 4)[1:-1]])
        B.add(W(tri), np.tile(Wd(up), (len(tri), 1)), col, 1.2, 5)
    # --- legs: gait as phase relations (lateral-sequence walk: LH 0, LF 1/4, RH 1/2, RF 3/4 of the stride cycle)
    L = 0.56; beta = 0.62
    amp = min(1.0, q['moving'] * 1.4) * (1 - lie)
    legs = [('LF', 0.30, sh_y - 0.07, 0.085, 0.25, 1), ('RF', 0.30, sh_y - 0.07, -0.085, 0.75, 1),
            ('LH', -0.31, hp_y - 0.06, 0.085, 0.0, 0), ('RH', -0.31, hp_y - 0.06, -0.085, 0.5, 0)]
    contacts = {}
    for name, jf, jy, jl, off, fore in legs:
        sph = (q['d_fwd'] / L + off) % 1.0
        if sph < beta:
            rel = L * (beta / 2 - sph)
            lift = 0.0
        else:
            v = (sph - beta) / (1 - beta)
            rel = -L * beta / 2 + L * beta * (0.5 - 0.5 * math.cos(math.pi * v))
            lift = 0.085 * math.sin(math.pi * v)
        contacts[name] = (sph < beta) or amp < 0.05
        rel *= amp; lift *= amp
        joint = np.array([jf, jy, jl])
        if fore:
            paw_st = np.array([jf + 0.03 + rel, 0.025 + lift, jl])
            wrist_st = paw_st + np.array([-0.015, 0.07, 0])
            elb_st, _ = ik2(joint, wrist_st, 0.25, 0.22, [-1, 0, 0])
            # lying: elbow on the floor under the shoulder, forearm flat ahead
            elb_ly = np.array([jf - 0.02, 0.05, jl * 1.15]); wrist_ly = np.array([jf + 0.22, 0.03, jl]); paw_ly = np.array([jf + 0.32, 0.025, jl])
            elb = elb_st * (1 - lie) + elb_ly * lie; wrist = wrist_st * (1 - lie) + wrist_ly * lie; paw = paw_st * (1 - lie) + paw_ly * lie
            pts = [joint, elb, wrist, paw]
            rads = [.05, .036, .03, .032]
        else:
            paw_st = np.array([jf - 0.03 + rel, 0.025 + lift, jl])
            hock_st = paw_st + np.array([-0.04, 0.15, 0])
            stifle_st, _ = ik2(joint, hock_st, 0.25, 0.25, [1, -0.2, 0])
            stifle_ly = np.array([jf + 0.20, 0.10, jl * 1.7]); hock_ly = np.array([jf - 0.10, 0.045, jl * 1.4]); paw_ly = np.array([jf + 0.06, 0.025, jl * 1.2])
            st = stifle_st * (1 - lie) + stifle_ly * lie; hk = hock_st * (1 - lie) + hock_ly * lie; paw = paw_st * (1 - lie) + paw_ly * lie
            pts = [joint, st, hk, paw]
            rads = [.065, .045, .03, .032]
        cen = chain(pts, 7)
        rr = np.interp(np.linspace(0, 1, len(cen)), np.linspace(0, 1, len(rads)), rads)
        P, Nn = tube(W(cen), rr, rr, 6, Wd([1, 0, 0]), ring_phase(4 + int(fore), len(cen), t), ripple * .3, 2, breath)
        B.add(P, Nn, col, 0.95, 3)
    # --- tail: pitch from the score's tail (0 high .. 1.35 tucked); wag at twice the dog's rate (a harmonic)
    tl = q['tail']
    a0 = math.radians(float(np.interp(tl, [0, .25, .5, 1.0, 1.35], [30, -14, -36, -62, -82])))
    wag = q['wag'] * 0.9 * math.sin(2 * breath)
    base = np.array([-0.42, hp_y + 0.01, 0])
    pts = [base]; ang = a0; d = 0.06
    for k in range(7):
        dvec = np.array([-math.cos(ang) * math.cos(wag), math.sin(ang), math.cos(ang) * math.sin(wag)])
        nxt = pts[-1] + d * dvec
        # lying: the tail rests on the floor, outside
        if lie > 0:
            flo = np.array([pts[-1][0] - d * 0.9, 0.03, pts[-1][2] + d * 0.35 * lie])
            nxt = nxt * (1 - lie) + flo * lie
        nxt[1] = max(nxt[1], 0.025)
        pts.append(nxt); ang += math.radians(7 if tl < .15 else -3)
    cen = dense(np.array(pts), 18)
    P, Nn = tube(W(cen), np.linspace(.038, .012, 18), np.linspace(.038, .012, 18), 6, Wd([0, 1, 0]), ring_phase(6, 18, t), ripple * .3, 2, breath)
    B.add(P, Nn, col, 1.0, 4)
    D = B.done()
    # density: thin the rings by fixed rank (eyes, nose and ears always kept)
    rk = ranks(len(D['w']), 1)
    keep = (rk < density) | (D['part'] >= 5)
    for k in D:
        D[k] = D[k][keep]
    D['contacts'] = contacts
    D['anchor'] = dict(torso=W(np.array([0.0, (sh_y + hp_y) / 2 - 0.08, 0])), withers=W(withers), rump=W(np.array([-0.40, hp_y, 0])),
                       chest=W(np.array([0.44, sh_y - 0.1, 0])), skull=W(skull), nose=W(nose))
    D['local'] = dict(sh_y=sh_y, hp_y=hp_y, skull_y=float(skull[1]), nose=nose, withers_y=float(withers[1]))
    return D


def person(q, t, phase):
    """the person, a figure of rings like the dog, in warm light: standing in the door, reaching, then sitting beside it.
    q: dict(u, z, sit, reach, low, lean). Faces +u (toward the porch and the dog)."""
    B = Builder()
    sit, reach, low, lean = q['sit'], q['reach'], q['low'], q['lean']
    o = np.array([q['u'], 0, q['z']])
    F = np.array([1.0, 0, 0]); S = np.array([0, 0, 1.0]); U = np.array([0, 1.0, 0])
    hip_y = 0.92 * (1 - sit) + 0.14 * sit
    hip = o + U * hip_y - F * 0.05 * sit
    lean_v = F * math.sin(lean) + U * math.cos(lean)
    chest = hip + 0.52 * lean_v * (1 - 0.1 * sit) + F * 0.05 * sit
    neck = chest + 0.10 * lean_v
    head = neck + 0.13 * lean_v + F * 0.02
    ph = phase
    # torso
    cen = seg(hip, chest + 0.06 * lean_v, 18)
    sp = np.linspace(0, 1, 18)
    P, Nn = tube(cen, np.interp(sp, [0, .35, .8, 1], [.16, .14, .19, .12]), np.interp(sp, [0, .35, .8, 1], [.11, .10, .12, .07]),
                 10, F, ring_phase(3, 18, t), 0.03, 2, ph)
    B.add(P, Nn, PERSON_COL, 0.85, 10)
    cen = seg(neck, head + 0.1 * lean_v, 13)
    hr = np.sin(np.linspace(0.25, math.pi - 0.25, 13)) * 0.09
    P, Nn = tube(cen, hr * 0.95, hr, 10, F, ring_phase(4, 13, t), 0.02, 2, ph)
    B.add(P, Nn, PERSON_COL, 0.95, 11)
    mouth = head + F * 0.10 + U * -0.02
    # legs: standing straight; sitting: thighs forward, shins down (knees up)
    for sg in (1, -1):
        h = hip + S * 0.09 * sg
        knee_st = h + U * -0.45; foot_st = h + U * -0.88 + F * 0.05
        knee_si = h + F * 0.42 + U * 0.22; foot_si = h + F * 0.60 + U * -0.12
        k = knee_st * (1 - sit) + knee_si * sit; fo = foot_st * (1 - sit) + foot_si * sit
        cen = chain([h, k, fo, fo + F * 0.12], 8)
        rr = np.linspace(.075, .045, len(cen))
        P, Nn = tube(cen, rr, rr, 6, F, ring_phase(1, len(cen), t), 0.02, 2, ph)
        B.add(P, Nn, PERSON_COL, 0.8, 12)
    # arms: the near arm (toward the camera, +z) reaches for the dog, then later is offered low
    hand_pts = {}
    for sg in (1, -1):
        sh = chest + S * 0.19 * sg - lean_v * 0.03
        rest_hand = sh + U * -0.55 + F * 0.05
        if sg == 1:
            reach_hand = sh + F * 0.62 + U * -0.22
            low_hand = o + F * 0.62 + U * 0.30 + S * -0.30
            hand = rest_hand * (1 - max(reach, low)) + reach_hand * reach + low_hand * low * (1 - reach)
        else:
            knee = hip + F * 0.42 + U * 0.22 + S * -0.09
            hand = rest_hand * (1 - sit) + (knee + U * 0.05) * sit
        elb, _ = ik2(sh, hand, 0.30, 0.30, -U * 0.6 + -F * 0.5 + S * 0.3 * sg)
        cen = chain([sh, elb, hand], 9)
        rr = np.linspace(.05, .035, len(cen))
        P, Nn = tube(cen, rr, rr, 6, F, ring_phase(1, len(cen), t), 0.02, 2, ph)
        B.add(P, Nn, PERSON_COL, 0.85, 13)
        # the hand: a small open fan of five finger rays
        fd = norm(hand - elb)
        for k in range(5):
            a = (k - 2) * 0.28
            dv = norm(fd * math.cos(a) + S * math.sin(a) * 0.8 + U * 0.1)
            B.add(seg(hand, hand + 0.09 * dv, 4), np.tile(dv, (4, 1)), PERSON_COL, 1.0, 14)
        hand_pts[sg] = hand
    D = B.done()
    D['mouth'] = mouth; D['hand'] = hand_pts[1]; D['head'] = head
    return D
