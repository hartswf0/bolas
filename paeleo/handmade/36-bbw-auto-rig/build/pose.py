"""SCION-36 · pose the auto-rig: a pose is a handful of numbers per handle (angles, a drop, a fold), turned into one
2x3 affine per handle and blended per vertex by the precomputed bounded biharmonic weights (skin.lbs)."""
import numpy as np
from skin import rot, scale_along, trans, compose, apply


def body_metrics(rig):
    m = rig['mask']; ys, xs = np.nonzero(m)
    x0, x1 = xs.min(), xs.max(); w = x1 - x0
    tops = []
    for x in range(int(x0 + .3 * w), int(x0 + .7 * w) + 1):
        col = np.nonzero(m[:, x])[0]
        if len(col): tops.append(col.min())
    H = rig['H']
    feet = np.array(H['feet']) if H['feet'] else np.array([[xs.mean(), ys.max()]])
    ground = float(ys.max())
    return dict(ground=ground, back=float(np.median(tops)), body_h=ground - float(np.median(tops)),
                anchor=np.array([float(feet[:, 0].mean()), ground]), x0=float(x0), x1=float(x1))


def leg_len(H, k):
    a, b = np.array(H[k]['a']), np.array(H[k]['b'])
    return float(np.linalg.norm(b - a)), a, b


DEFAULT = dict(drop=0.0, crouch=0.0, neck=0.0, head=0.0, push=0.0, tail=0.0, wag=0.0, swing=None, fold=0.0,
               fold_front=None, frontal=False, chin=0.0)


def mats(rig, **kw):
    p = dict(DEFAULT); p.update(kw)
    H = rig['H']; f = rig['facing']; names = rig['names']
    legs = [k for k in names if k.startswith('leg')]
    L = [leg_len(H, k)[0] for k in legs] or [rig['body']['body_h'] * .6]
    Lh = float(np.mean(L))
    fold = p['fold']; ffold = fold if p['fold_front'] is None else p['fold_front']
    # the body sinks by the fold (lying) and the crouch; feet stay on the ground (legs compress or fold)
    drop = (.62 * max(fold, ffold * .6) + .16 * p['crouch']) * Lh + p['drop']
    root = trans((0, drop))
    out = {}
    sh = np.array(H['neck']['a'])
    neck_ang = f * (p['neck'] + p['chin'])
    Mn = compose(root, trans((f * p['push'], 0)), rot(neck_ang, sh))
    out['neck'] = Mn
    hd = np.array(H['head']['at'])
    out['head'] = compose(Mn, rot(f * p['head'], hd))
    out['back'] = root
    ta = np.array(H['tail']['a'])
    Mt = compose(root, rot(-f * p['tail'], ta))
    out['tail'] = Mt
    out['tailtip'] = compose(Mt, rot(-f * p['tail'] * .6 + p['wag'], np.array(H['tail']['b'])))
    for i, k in enumerate(legs):
        l, a, b = leg_len(H, k)
        front = H[k].get('kind') == 'front'
        fo = ffold if front else fold
        sw = 0.0 if p['swing'] is None else p['swing'][i % len(p['swing'])]
        comp = 1 - .16 * p['crouch'] / max(l / Lh, .5)
        if p['frontal']:
            M = compose(root, scale_along(a, b - a, comp * (1 - .7 * fo), 1 + .15 * fo))
        elif front:
            # forelegs reach forward and lie flat (sphinx), a little shortened
            M = compose(root, rot(-f * (sw + 1.25 * fo), a), scale_along(a, b - a, comp * (1 - .3 * fo)))
        else:
            # hind legs fold under the hip: rotate forward and compress
            M = compose(root, rot(-f * (sw + 1.45 * fo), a), scale_along(a, b - a, comp * (1 - .62 * fo), 1 + .2 * fo))
        out[k] = M
    return np.stack([out[k] for k in names])


def depth(rig, fold=0.0):
    d = {'head': -.2, 'neck': -.1, 'back': 0.0, 'tail': .4, 'tailtip': .5}
    def leg(k):
        if rig['H'][k].get('kind') == 'front': return .8 * (1 - fold) + .05 * fold   # lying: just behind the chest
        return .8
    return rig['W'] @ np.array([d[k] if k in d else leg(k) for k in rig['names']])
