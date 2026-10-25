"""The illustrator's kit for the person in the doorway (profile, facing the dog unless told otherwise).
Same ink and wash as the dog. Origin on the ground under the hips, film px (190 px/m)."""
import math
from geom import cr, add, lerp, ellipse, limb, ik2, xf, rnd
from dogparts import part


def rot(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def person(hip=(0, -150), lean=0.0, head_pitch=0.0, mouth=0.0, armN=(.15, .1), armF=(.1, .05), footN=(10, 0), footF=(-12, 0),
           sit=False, face=1, eyes='open'):
    """lean: torso tilt forward (rad). armN/armF: (upper-arm angle from straight down, forward positive; elbow bend).
    Built facing right, then flipped when face=-1."""
    P = []
    hx, hy = hip
    up = lambda dx, dy: rot((hx + dx, hy + dy), hip, lean)   # points on the torso, tilted about the hip
    sh = up(2, -104)
    neck = up(4, -116)
    hc = rot(up(6, -138), neck, head_pitch)

    def arm(spec, far):
        a, bend = spec
        el = (sh[0] + 56 * math.sin(a + lean * .3), sh[1] + 56 * math.cos(a + lean * .3))
        a2 = a + bend
        ha = (el[0] + 50 * math.sin(a2), el[1] + 50 * math.cos(a2))
        hand = (ha[0] + 9 * math.sin(a2), ha[1] + 9 * math.cos(a2))
        L = 'far' if far else 'main'
        P.append(part(limb([sh, el, ha], [17, 13, 10]), 'coatPD' if far else 'coatP', L))
        P.append(part(ellipse(hand, 8, 6, math.atan2(math.cos(a2), -math.sin(a2)) + math.pi / 2, 12), 'skinD' if far else 'skin', L, w=1.8))
        return hand

    # legs
    if sit:
        knee_n = (hx + 50, hy - 4); knee_f = (hx + 44, hy - 2)
        for kn, ft, far in ((knee_f, footF, True), (knee_n, footN, False)):
            P.append(part(limb([(hx, hy), kn, (ft[0], ft[1] - 8)], [34, 18, 13]), 'skirt' if not far else 'shoe', 'far' if far else 'main'))
            P.append(part([(ft[0] - 6, ft[1] - 12), (ft[0] + 16, ft[1] - 6), (ft[0] + 18, ft[1]), (ft[0] - 8, ft[1])], 'shoe', 'far' if far else 'main', w=1.6))
    else:
        for ft, far in ((footF, True), (footN, False)):
            hipj = (hx + (-3 if far else 3), hy + 4)
            kn = ik2(hipj, (ft[0], ft[1] - 8), 76, 70, -1)
            P.append(part(limb([hipj, kn, (ft[0], ft[1] - 8)], [26, 17, 12]), 'shoe' if far else 'skirt', 'far' if far else 'main'))
            P.append(part([(ft[0] - 7, ft[1] - 12), (ft[0] + 15, ft[1] - 6), (ft[0] + 17, ft[1]), (ft[0] - 9, ft[1])], 'shoe', 'far' if far else 'main', w=1.6))
    handF = arm(armF, True)
    # coat: shoulders to hem, a long coat
    hem = 52 if not sit else 6
    coat = [up(-20, -100), up(-6, -110), up(16, -106), up(24, -88), up(20, -40), up(24, 6 + (0 if sit else hem * .6)),
            up(26, hem) if not sit else (hx + 56, hy + 2), up(-4, hem + 4) if not sit else (hx + 20, hy + 8),
            up(-30, hem) if not sit else (hx - 28, hy + 4), up(-28, 0), up(-26, -50)]
    P.append(part(coat, 'coatP', 'main'))
    # neck, scarf, head
    P.append(part([up(-6, -104), up(-4, -122), up(12, -124), up(12, -104)], 'skin', 'main'))
    T = lambda pts: [rot((hc[0] + x, hc[1] + y), hc, head_pitch) for x, y in pts]
    face_pts = [(-16, -12), (-8, -21), (6, -21), (15, -12), (17, -4), (21, 2), (17, 5), (18, 10 + mouth * 3), (14, 16 + mouth * 3),
                (6, 21), (-6, 18), (-14, 8)]
    P.append(part(T(face_pts), 'skin', 'main'))
    P.append(part(T([(-19, -6), (-17, -18), (-6, -25), (8, -24), (16, -16), (14, -10), (4, -12), (-2, -6), (-6, 6), (-12, 12), (-20, 6)]), 'hair', 'main'))
    P.append(part([up(-24, -98), up(-8, -112), up(16, -110), up(22, -98), up(4, -94)], 'scarf', 'main', w=1.8))
    # interior lines
    if eyes == 'open':
        P.append(part(T(ellipse((9, -5), 1.8, 1.4, 0, 8)), 'eye', 'dot', smooth=False))
    else:
        P.append(part(T([(6, -4), (9, -3), (12, -4)]), 'ink', 'line', w=1.2, closed=False))
    P.append(part(T([(5, -10), (9, -11), (13, -9)]), 'ink', 'line', w=1.1, closed=False))
    if mouth > .2:
        P.append(part(T(ellipse((15, 11 + mouth * 1.5), 2.5, 1.2 + mouth * 2.2, 0, 10)), 'nose', 'dot', smooth=False))
    else:
        P.append(part(T([(11, 11), (16, 11)]), 'ink', 'line', w=1.1, closed=False))
    P.append(part([up(-10, -60), up(-12, 0)], 'coatPD', 'line', w=1.2, closed=False))
    handN = arm(armN, False)
    if face < 0:
        for q in P:
            q['p'] = [[2 * hx - x, y] for x, y in q['p']]
        handN = (2 * hx - handN[0], handN[1]); hc = (2 * hx - hc[0], hc[1])
    return P, {'hand': [round(handN[0], 1), round(handN[1], 1)], 'head': [round(hc[0], 1), round(hc[1], 1)]}
