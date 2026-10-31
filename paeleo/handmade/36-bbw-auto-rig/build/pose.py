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
    return dict(cx=float(xs.mean()), ground=ground, back=float(np.median(tops)), body_h=ground - float(np.median(tops)),
                anchor=np.array([float(feet[:, 0].mean()), ground]), x0=float(x0), x1=float(x1))


def leg_len(H, k):
    a, b = np.array(H[k].get('p', H[k]['a'])), np.array(H[k]['b'])
    return float(np.linalg.norm(b - a)), a, b


DEFAULT = dict(drop=0.0, crouch=0.0, neck=0.0, head=0.0, push=0.0, tail=0.0, wag=0.0, swing=None, fold=0.0,
               fold_front=None, frontal=False, chin=0.0, tuck=False)


def mats(rig, **kw):
    p = dict(DEFAULT); p.update(kw)
    H = rig['H']; f = rig['facing']; names = rig['names']
    legs = [k for k in names if k.startswith('leg')]
    L = [float(np.linalg.norm(np.array(H[k]['b']) - np.array(H[k]['a']))) for k in legs] or [rig['body']['body_h'] * .6]
    Lh = float(np.mean(L))
    fold = p['fold']; ffold = fold if p['fold_front'] is None else p['fold_front']
    # the body sinks by the fold (lying) and the crouch; feet stay on the ground (legs compress or fold)
    drop = (.62 * max(fold, ffold * .6) + .16 * p['crouch']) * Lh + p['drop']
    # lying: the hindquarters settle lower than the shoulders (the body tilts about the shoulder)
    tilt = .12 * fold
    root = compose(trans((0, drop)), rot(-f * tilt, np.array(H['neck']['a'])))
    if p['frontal']:
        root = trans((0, drop + .3 * fold * Lh))
    out = {}
    sh = np.array(H['neck']['a'])
    neck_ang = f * (p['neck'] + p['chin'])
    Mn = compose(root, trans((f * p['push'], 0)), rot(neck_ang, sh))
    out['neck'] = Mn
    hd = np.array(H['head']['at'])
    out['head'] = compose(Mn, rot(f * p['head'], hd))
    out['back'] = root
    ta = np.array(H['tail']['a'])
    tb = np.array(H['tail']['b'])
    # lying: the tail lies out behind on the boards, a little longer than the found stub so its tip shows
    Mt = compose(root, rot(-f * (p['tail'] * (1 - fold) + (0 if p['frontal'] else .1) * fold), ta), scale_along(ta, tb - ta, 1.0))
    out['tail'] = Mt
    tdir = np.array([-f * .85, .5])                     # out behind and down onto the boards
    ext = (0 if p['frontal'] else 34.0) * fold          # lying: the tail tip lies out a few px further on the boards
    out['tailtip'] = compose(Mt, trans(tdir * ext), rot(-f * p['tail'] * .6 + p['wag'], tb))
    for i, k in enumerate(legs):
        l, a, b = leg_len(H, k)
        front = H[k].get('kind') == 'front'
        fo = ffold if front else fold
        front0 = H[k].get('kind') == 'front'
        sw = 0.0 if p['swing'] is None else (p['swing'][0] if front0 else p['swing'][-1])
        comp = 1 - .16 * p['crouch'] / max(l / Lh, .5)
        if p['frontal']:
            M = compose(root, scale_along(a, b - a, comp * (1 - .9 * fo), 1 + .15 * fo))
        elif front and p['tuck']:
            # forepaws drawn in under the chest (no pale paw reaching out ahead of the head)
            M = compose(root, rot(-f * .5 * fo, a), scale_along(a, b - a, .3))
        elif front:
            # forelegs reach forward and lie flat (sphinx), a little shortened
            M = compose(root, rot(-f * (sw + .95 * fo), a), scale_along(a, b - a, comp * (1 - .45 * fo)))
        else:
            # hind legs fold under the hip: rotate forward and compress
            M = compose(root, rot(-f * (sw + 1.65 * fo), a), scale_along(a, b - a, comp * (1 - .45 * fo), 1 + .1 * fo))
        out[k] = M
    return np.stack([out[k] for k in names])


def depth(rig, fold=0.0):
    d = {'head': -.2, 'neck': -.1, 'back': 0.0, 'tail': .4, 'tailtip': .5}
    def leg(k):
        if rig['H'][k].get('kind') == 'front': return .8                              # lying: tucked behind the chest
        return .8
    return rig['W'] @ np.array([d[k] if k in d else leg(k) for k in rig['names']])
