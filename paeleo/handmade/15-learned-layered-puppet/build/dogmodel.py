"""Generation: turn the score's acting intentions into poses of the learned layered puppet, and render them.

controls -> pose:
  view      phi (0 profile-left .. 90 facing camera .. 180 profile-right) -> psi = min(phi, 180-phi) + mirror;
            torso foreshortening from the view prior, head/tail/leg shape from the learned view regression,
            each leg's joint shifted by its lateral depth * sin(psi) (2.5D: legs separate when the dog faces you).
  head      its own view phi_h (may oppose the body: looking back over the shoulder), tilt from act.head / rest.
  legs      planted-foot gait planner by distance walked (stance feet fixed in the world), 2-link IK per leg;
            lying blends to authored folded-leg angles (CORRECTION: outside the learned range).
appearance: learned per-layer atlases at psi (head at psi_h), linearly interpolated between 15-degree view bins.
mode 'raw' = what the learned model gives on its own (rotations clamped to the learned range, head view tied to the
body view, 'away' head views folded onto 'toward'); mode 'corrected' = the film, with hand-authored overrides.
Every pose gets an out-of-distribution score (Mahalanobis over learned joint rotations, view support)."""
import json, os
import numpy as np
from scipy import ndimage
from puppet import Template, PARTS, ORDER, SKEL, POINTS, transforms, warp_layer, neutral_pose, CACHE, rot
from stage import P, KX, KZV
from controls import DOG_Z

tpl = Template()
MJ = json.load(open(os.path.join(CACHE, 'model.json')))
MZ = np.load(os.path.join(CACHE, 'model.npz'))
TEX, CONF = MZ['tex'], MZ['conf']
MU, COV = MZ['mu'], MZ['cov']
COVI = np.linalg.inv(COV)
SD = np.sqrt(np.diag(COV))
BINS = np.array(MJ['bins'])
S_SCREEN = 1.42          # screen px per template px  (template px ~ 0.0068 m)
M_PER_TPX = KX / S_SCREEN  # template px per metre -> 1/0.0068
CENTER = np.array(SKEL['torso']['pivot'], float)
LEG = {'ff': ('ff_up', 'ff_lo', 'f1', 0.75, -1, +1), 'fn': ('fn_up', 'fn_lo', 'f2', 0.25, +1, +1),
       'hf': ('hf_up', 'hf_lo', 'h1', 0.5, -1, -1), 'hn': ('hn_up', 'hn_lo', 'h2', 0.0, +1, -1)}
# (upper, lower, foot point, gait phase offset, side: +1 near/-1 far, knee bend: +1 forward / -1 back)
LAT = 8.0          # template px: half body width, lateral depth of each leg column
STRIDE, DUTY, LIFT = 0.42, 0.62, 0.045
ROTKEYS = ['head', 'tail', 'ff_up', 'ff_lo', 'fn_up', 'fn_lo', 'hf_up', 'hf_lo', 'hn_up', 'hn_lo']
# authored lying angles (the correction; the archive never shows a dog lying)
LIE = {'ff_up': 1.2, 'ff_lo': 0.32, 'fn_up': 1.28, 'fn_lo': 0.26, 'hf_up': 1.15, 'hf_lo': -2.25, 'hn_up': 1.22, 'hn_lo': -2.35}


def fx_of(psi, w):
    c = np.cos(np.radians(psi)); return float(np.sqrt(c * c + w * w * (1 - c * c)))


def shape_at(name, psi):
    v = MJ['shape'][name]; b = np.clip(psi / 15.0, 0, len(BINS) - 1 - 1e-6); b0 = int(b); t = b - b0
    return v[b0] * (1 - t) + v[b0 + 1] * t


def tex_at(j, psi):
    b = np.clip(psi / 15.0, 0, len(BINS) - 1 - 1e-6); b0 = int(b); t = b - b0
    return TEX[j, b0] * (1 - t) + TEX[j, b0 + 1] * t, CONF[j, b0] * (1 - t) + CONF[j, b0 + 1] * t


def smooth(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def gait_offset(D, off):
    """foot position along the dog's forward axis (metres, relative to its home under the body) for distance D walked.
    stance: the foot is fixed in the world; swing: it travels one stride. returns (offset, lift)."""
    c = D / STRIDE + off
    n = np.floor(c); u = c - n
    if u < DUTY:
        foot = STRIDE * (n + DUTY / 2 - off); lift = 0.0
    else:
        s = smooth((u - DUTY) / (1 - DUTY))
        foot = STRIDE * (n + DUTY / 2 - off + s); lift = LIFT * np.sin(np.pi * s)
    return foot - D, lift


def ik(J, q, b1, b2, fy1, fy2, bend, base):
    """2-link IK in the dog frame. returns (theta_up, theta_lo) relative rotations, reach error."""
    v1 = np.array([b1[0], b1[1] * fy1]); v2 = np.array([b2[0], b2[1] * fy2])
    l1, l2 = np.hypot(*v1), np.hypot(*v2)
    be1, be2 = np.arctan2(v1[1], v1[0]), np.arctan2(v2[1], v2[0])
    d = q - J; dist = np.hypot(*d)
    dc = np.clip(dist, abs(l1 - l2) + 1e-3, (l1 + l2) * 0.999)
    al = np.arctan2(d[1], d[0])
    cosk = np.clip((l1 * l1 + dc * dc - l2 * l2) / (2 * l1 * dc), -1, 1)
    g1 = al + bend * np.arccos(cosk)
    knee = J + l1 * np.array([np.cos(g1), np.sin(g1)])
    g2 = np.arctan2(q[1] - knee[1], q[0] - knee[0])
    t1 = g1 - be1 - base; t2 = g2 - be2 - g1 + be1
    t1 = (t1 + np.pi) % (2 * np.pi) - np.pi; t2 = (t2 + np.pi) % (2 * np.pi) - np.pi
    return t1, t2, dist - dc


def build_pose(c, mode='corrected'):
    """c: controls dict. returns pose, info."""
    raw = mode == 'raw'
    phi = c['phi']; psi = min(phi, 180 - phi); mirror = 1 if phi < 90 else -1
    phi_h = c['phi_h']
    if raw:
        phi_h = phi                             # the learned model ties head view to body view
    away = c.get('away', 0.0)                   # 0..1 head turned away from camera (into the room)
    psi_h = min(phi_h, 180 - phi_h)
    head_rel = 1 if (phi_h < 90) == (phi < 90) else -1
    p = neutral_pose()
    g = p['g']; g['mirror'] = mirror; g['s'] = S_SCREEN; g['rot'] = c.get('pitch', 0.0) * mirror
    p['torso']['fx'] = fx_of(psi, MJ['W_BODY'])
    # raw: a head turned away from the camera is foreshortened exactly like one turned toward it (the 2.5D model
    # cannot tell front from back): it shows the 3/4 FACE. corrected: profile texture, shortened, face in shadow.
    hpsi = (35.0 * away) if raw else psi_h
    if raw:
        psi_h = hpsi
    p['head']['fx'] = head_rel * fx_of(hpsi, MJ['W_HEAD']) * (1 - 0.3 * away * (not raw))
    p['head']['fy'] = shape_at('head_fy', psi_h)
    # learned: in front views the archive dog's head layer sits tilted down (view regression of head rot)
    p['head']['rot'] = c['head_rot'] + (shape_at('head_rot', psi_h) - shape_at('head_rot', 0))
    if not raw:
        # CORRECTION: a head foreshortened toward the camera stands its neck upright ('giraffe'); tip it toward us
        p['head']['rot'] -= 0.85 * smooth((psi_h - 30) / 50)
    if head_rel < 0:
        p['head']['rot'] = -p['head']['rot']   # a head reflected about its pivot carries its tilt reflected too
    # head carried low (approach, retreat): the neck joint itself drops, so the skull sits below the withers
    if not raw:
        p['head']['dy'] = 30.0 * float(np.clip((0.85 - c.get('head', 0.9)) / 0.4, 0, 1)) * (1 - c['lie'])
    p['tail']['fx'] = shape_at('tail_fx', psi) * c.get('tail_len', 1.0)
    p['tail']['rot'] = c['tail_rot']
    fl, hl = shape_at('fore_len', psi), shape_at('hind_len', psi)
    sinp = np.sin(np.radians(psi))
    for l, (up, lo, foot, off, side, bend) in LEG.items():
        p[up]['fy'] = fl if l[0] == 'f' else hl; p[lo]['fy'] = p[up]['fy']
        p[up]['dx'] = side * LAT * sinp * 0.9
    # body height: standing torso centre above the floor, lowered by crouch and lying
    stand_h = 64.0 * (0.5 * (fl + hl))
    lie = c['lie']
    h = stand_h * (1 - 0.16 * c['crouch']) * (1 - lie) + 26.0 * lie
    Xc = c['X']
    u, v = P(Xc, 0, DOG_Z)
    bob = c.get('bob', 0.0)
    g['tx'] = u; g['ty'] = v - (h + bob) * S_SCREEN
    # legs: IK to planted feet, blended with the lying fold
    M = transforms(p)
    Gi = np.linalg.inv(M['torso'] @ np.linalg.inv(_dogframe_torso(p)))  # screen -> dog frame
    D = c['D']
    info = {'reach_err': 0.0}
    fwd = -1 if mirror > 0 else 1        # world +X per unit forward
    for l, (up, lo, foot, off, side, bend) in LEG.items():
        Dt = _dogframe_torso(p)
        J = (Dt @ np.r_[SKEL[up]['pivot'], 1])[:2] + np.array([p[up]['dx'], 0])
        ft = np.array(POINTS[foot][1], float)
        home = (ft[0] - CENTER[0]) * p['torso']['fx'] + p[up]['dx']      # dog-frame x of the foot under the body
        go, lift = gait_offset(D, off) if c.get('walk', True) else (0.0, 0.0)
        go += c.get('foot_slip', {}).get(l, 0.0)
        # target in screen: along the porch by home + gait, on the floor (near legs a little nearer the camera)
        Xf = Xc + mirror * home * S_SCREEN / KX + fwd * go
        zf = -0.07 * side * np.cos(np.radians(psi))
        tu, tv = P(Xf, lift, zf + DOG_Z)
        q = (Gi @ np.r_[tu, tv, 1])[:2]
        knee_t = np.array(SKEL[lo]['pivot'], float)
        b1 = knee_t - np.array(SKEL[up]['pivot'], float); b2 = ft - knee_t
        t1, t2, err = ik(J, q, b1, b2, p[up]['fy'], p[lo]['fy'], bend, p['torso']['rot'])
        info['reach_err'] = max(info['reach_err'], abs(err))
        if raw:
            lo1, hi1 = MU[ROTKEYS.index(up)] - 2.5 * SD[ROTKEYS.index(up)], MU[ROTKEYS.index(up)] + 2.5 * SD[ROTKEYS.index(up)]
            lo2, hi2 = MU[ROTKEYS.index(lo)] - 2.5 * SD[ROTKEYS.index(lo)], MU[ROTKEYS.index(lo)] + 2.5 * SD[ROTKEYS.index(lo)]
            t1 = float(np.clip(t1, lo1, hi1)); t2 = float(np.clip(t2, lo2, hi2))
            p[up]['rot'], p[lo]['rot'] = t1, t2
        else:
            p[up]['rot'] = t1 * (1 - lie) + LIE[up] * lie
            p[lo]['rot'] = t2 * (1 - lie) + LIE[lo] * lie
    r = np.array([p[k]['rot'] for k in ROTKEYS])
    dm = float(np.sqrt((r - MU) @ COVI @ (r - MU)))
    vs = float(np.exp(-0.5 * ((np.array(MJ['psi']) - psi) / 10.0) ** 2) @ np.array(MJ['quality']))
    info.update({'psi': psi, 'psi_h': psi_h, 'mirror': mirror, 'mahal': dm, 'view_support': vs, 'head_rel': head_rel,
                 'ood': float(1 - np.exp(-max(0, dm - 3.0) / 4.0) * (1 - np.exp(-vs / 1.5)))})
    return p, info


def _dogframe_torso(p):
    q = p['torso']; piv = CENTER
    from puppet import affine, T
    return affine(rot(q['rot']) @ np.diag([q['fx'], q['fy']]), (0, 0)) @ T(-piv)


def render_dog(p, info, H, W, c=None, mode='corrected'):
    """returns gray HxW, alpha HxW, conf HxW (per-pixel learned confidence of what is shown), layer alphas."""
    M = transforms(p)
    out = np.zeros((H, W), np.float32); A = np.zeros((H, W), np.float32); C = np.zeros((H, W), np.float32)
    layers = {}
    away = (c or {}).get('away', 0.0) if mode != 'raw' else 0.0
    for k in ORDER:
        j = PARTS.index(k)
        psi = info['psi_h'] if k == 'head' else info['psi']
        t, cf = tex_at(j, psi)
        if k == 'head' and away > 0:
            # CORRECTION for the head turned away (no such view in the archive): the face side falls into
            # shadow, the back of the skull and ear read as a dark mass against the lit room.
            yy, xx = np.mgrid[0:t.shape[0], 0:t.shape[1]]
            dn = np.hypot(xx - 92, yy - 86); face = np.clip(1 - dn / 34.0, 0, 1)
            t = t * (1 - away * (0.25 + 0.55 * face))
            cf = cf * (1 - 0.7 * away)
        g, a, bb = warp_layer(t, tpl.alpha[j], M[k], H, W, (0, 0), tpl.bbox[j], 1.0)
        if k[:2] in ('ff', 'hf'):
            # visibility layer: toward the front view the far legs pass behind the near legs and chest
            a = a * (0.0 if info['psi'] > 62 else 1.0)   # hard visibility switch, never translucent
        if bb is None:
            continue
        cfw, _, _ = warp_layer(cf, tpl.alpha[j], M[k], H, W, (0, 0), tpl.bbox[j], 1.0)
        out = out * (1 - a) + g * a
        C = C * (1 - a) + cfw * a
        A = A + a * (1 - A)
        layers[k] = a
    return out, A, C, layers, M
