"""SCION 23 · the person's atlas regions: profile facing right, painted in the same gouache as the dog.
No likeness: an ochre-skinned head with hair, a nose and an eye dot."""
import math
import numpy as np
import paint as P
import turnaround as T
import atlas as A

SKIN = np.array([0.80, 0.60, 0.46]); HAIR = np.array([0.20, 0.14, 0.12]); SWEATER = np.array([0.55, 0.27, 0.22])
TROUS = np.array([0.24, 0.25, 0.32]); SHOE = np.array([0.16, 0.12, 0.10])


def head():
    ells = [dict(c=(0.0, 0.0, 0), r=(0.095, 0.115, 0.08), id=1),
            dict(c=(0.045, -0.06, 0), r=(0.06, 0.055, 0.06), id=1),
            dict(c=(0.105, -0.005, 0), r=(0.022, 0.03, 0.018), id=1, R=A.rz(-20)),
            dict(c=(-0.018, 0.035, 0), r=(0.104, 0.098, 0.086), id=5),
            dict(c=(-0.045, -0.02, 0), r=(0.07, 0.09, 0.078), id=5),
            dict(c=(0.06, 0.03, -0.055), r=(0.011, 0.009, 0.006), id=4),
            dict(c=(-0.01, -0.005, -0.075), r=(0.022, 0.03, 0.012), id=1)]

    def alb(hl, nl, idx, ncam):
        a = np.zeros(hl.shape) + SKIN
        a = np.where((idx == 5)[..., None], HAIR, a)
        a = np.where((idx == 4)[..., None], np.array([0.1, 0.07, 0.06]), a)
        return a
    col, al, org = A.paint_plane(ells, 180, alb, (-0.2, 0.2, -0.17, 0.2), seed=700)
    return A.crop(col, al, org)


def paint_all(ppm):
    out = {}
    c, a, o = head(); out['p_head'] = (c, a, o, 'plane')
    parts = dict(p_torso=(0.52, 0.15, 0.17, SWEATER, 90), p_neck=(0.09, 0.05, 0.045, SKIN, 90),
                 p_uarm=(0.29, 0.055, 0.045, SWEATER, -90), p_farm=(0.26, 0.043, 0.034, SWEATER, -90),
                 p_hand=(0.08, 0.033, 0.03, SKIN, -90), p_thigh=(0.43, 0.085, 0.06, TROUS, -90),
                 p_shin=(0.43, 0.058, 0.046, TROUS, -90), p_shoe=(0.21, 0.045, 0.04, SHOE, 0))
    k = 0
    for nm, (L, r0, r1, base, la) in parts.items():
        for nf in (('near', 'far') if nm not in ('p_torso', 'p_neck') else ('near',)):
            col, al, org = A.paint_capsule(L, r0, r1, base, nf == 'far', la, seed=800 + k)
            out[nm + ('' if nm in ('p_torso', 'p_neck') else '_' + nf)] = (col, al, org, 'axis')
            k += 1
    return out
