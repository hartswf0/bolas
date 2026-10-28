"""The person: a drawn layered silhouette puppet (no found material, no face), posed from the score's person track.
Layers back to front: far leg, far arm, coat/torso, head, near leg, near arm. Joint angles in radians, profile facing +X."""
import numpy as np
from PIL import Image, ImageDraw
from stage import P, KY, W, H

L = {'shin': .47, 'thigh': .45, 'torso': .56, 'neck': .07, 'head': .115, 'uarm': .31, 'farm': .36}


def capsule(d, a, b, r, fill):
    a = np.array(a, float); b = np.array(b, float); v = b - a; n = np.hypot(*v) + 1e-9; nv = np.array([-v[1], v[0]]) / n * r
    d.polygon([tuple(a + nv), tuple(b + nv), tuple(b - nv), tuple(a - nv)], fill=fill)
    d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=fill); d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=fill)


def smooth(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def keyed(t, keys):
    """piecewise smooth interpolation of dict poses over (time, pose) keys."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1:
            w = smooth((t - t0) / max(t1 - t0, 1e-6))
            return {k: p0[k] + (p1[k] - p0[k]) * w for k in p0}
    return dict(keys[-1][1])


STAND = dict(X=-0.28, Z=0.0, hip=.93, lean=0.0, th1=0.03, sh1=0.0, th2=-0.03, sh2=0.0, arm=0.08, elb=0.15, arm2=-0.05, elb2=0.1, head=0.0)


def pose_at(t, score_person):
    """key poses timed to the score's person track (call 1.0-2.3, call+reach 3.4-4.6, beside/sit 5.4, hand low 6.8)."""
    S = STAND
    call = dict(S, lean=0.10, head=0.18, arm=0.35, elb=0.6)
    reach = dict(S, lean=0.42, head=0.25, arm=1.45, elb=0.05, th1=0.25, sh1=-0.05, th2=-0.18, X=-0.18)
    step = dict(S, X=0.12, Z=0.55, th1=0.35, th2=-0.3, arm=0.2, arm2=-0.2)
    stand_b = dict(S, X=0.28, Z=0.95, th1=0.05, th2=-0.05)
    sit = dict(S, X=0.24, Z=0.95, hip=0.13, lean=-0.12, th1=1.45, sh1=-1.5, th2=1.35, sh2=-1.25, arm=0.55, elb=0.6, arm2=0.3, elb2=0.8, head=0.12)
    low = dict(sit, lean=0.22, arm=0.62, elb=0.25, head=0.32)
    soft = dict(low, head=0.42, lean=0.28)
    keys = [(0.0, S), (0.9, S), (1.15, call), (2.2, call), (2.6, S), (3.3, S), (3.75, reach), (4.5, reach), (4.75, S),
            (5.05, step), (5.35, stand_b), (6.3, sit), (6.75, sit), (7.15, low), (7.5, soft), (9.6, low), (10.4, soft),
            (11.8, low), (26.3, low), (26.7, soft), (27.6, low)]
    return keyed(t, keys)


def draw(p, ss=2):
    """returns (alpha HxW float, rim HxW float) for the person; rim = edge facing -X (toward the lit room)."""
    im = Image.new('L', (W * ss, H * ss), 0); d = ImageDraw.Draw(im)
    rim = Image.new('L', (W * ss, H * ss), 0); dr = ImageDraw.Draw(rim)
    root = np.array(P(p['X'], 0, p['Z'])) * ss; k = KY * ss
    up = lambda a: np.array([np.sin(a), -np.cos(a)])
    hip = root + np.array([0, -p['hip'] * k])
    def leg(th, sh):
        knee = hip + np.array([np.sin(th), np.cos(th)]) * L['thigh'] * k
        foot = knee + np.array([np.sin(th + sh), np.cos(th + sh)]) * L['shin'] * k
        return knee, foot
    neck = hip + up(p['lean']) * L['torso'] * k
    head = neck + up(p['lean'] + p['head'] * 0.5) * (L['neck'] + L['head']) * k
    sh = hip + up(p['lean']) * (L['torso'] - 0.05) * k
    def arm(a, e):
        el = sh + np.array([np.sin(a), np.cos(a)]) * L['uarm'] * k
        ha = el + np.array([np.sin(a + e), np.cos(a + e)]) * L['farm'] * k
        return el, ha
    # far leg, far arm (slightly behind)
    kn, ft = leg(p['th2'], p['sh2'])
    capsule(d, hip, kn, .075 * k, 255); capsule(d, kn, ft, .055 * k, 255); capsule(d, ft, ft + np.array([.13 * k, 0]), .035 * k, 255)
    el, ha = arm(p['arm2'], p['elb2'])
    capsule(d, sh, el, .05 * k, 255); capsule(d, el, ha, .04 * k, 255)
    # coat: a tapered quad from shoulders to below the hip
    nrm = np.array([np.cos(p['lean']), np.sin(p['lean'])])
    hem = hip + np.array([0, .12 * k]) if p['hip'] > .5 else hip
    d.polygon([tuple(neck - nrm * .1 * k), tuple(neck + nrm * .12 * k), tuple(hem + nrm * .2 * k), tuple(hem - nrm * .17 * k)], fill=255)
    d.ellipse([neck[0] - .1 * k, neck[1] - .06 * k, neck[0] + .12 * k, neck[1] + .1 * k], fill=255)
    # head: skull + a short nose/brow profile toward +X, a hint of hair at the back
    r = L['head'] * k
    d.ellipse([head[0] - r, head[1] - r * 1.08, head[0] + r * .95, head[1] + r * 1.0], fill=255)
    fa = p['lean'] + p['head'] * 0.5
    nose = head + np.array([np.cos(fa), np.sin(fa)]) * r * 1.02 + np.array([0, .01 * k])
    d.polygon([tuple(head + np.array([r * .6, -r * .3])), tuple(nose), tuple(head + np.array([r * .7, r * .45]))], fill=255)
    d.ellipse([head[0] - r * 1.15, head[1] - r * .9, head[0] - r * .1, head[1] + r * .5], fill=255)
    # near leg, near arm, hand
    kn, ft = leg(p['th1'], p['sh1'])
    capsule(d, hip, kn, .08 * k, 255); capsule(d, kn, ft, .06 * k, 255); capsule(d, ft, ft + np.array([.14 * k, 0]), .038 * k, 255)
    am = Image.new('L', (W * ss, H * ss), 0); da = ImageDraw.Draw(am)
    el, ha = arm(p['arm'], p['elb'])
    capsule(da, sh, el, .055 * k, 255); capsule(da, el, ha, .043 * k, 255)
    hd = ha + np.array([np.sin(p['arm'] + p['elb']), np.cos(p['arm'] + p['elb'])]) * .06 * k
    da.ellipse([hd[0] - .055 * k, hd[1] - .04 * k, hd[0] + .055 * k, hd[1] + .04 * k], fill=255)
    a = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
    aa = np.asarray(am.resize((W, H), Image.LANCZOS), np.float32) / 255
    return a, aa, (hd / ss)
