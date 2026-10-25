"""The illustrator's construction kit for the dog. Every drawing in the bank is set by hand from these parts
(withers, croup, chest depth, head carriage, paw placements, tail line); the film never interpolates between
drawings, it only selects them. Reference: the archive dog (Amateur Film New Jersey C), a shepherd mix with a
dark saddle, a pale ring of ruff at the neck, pale legs and pricked ears."""
import math
from geom import cr, add, lerp, ellipse, limb, ik2, xf, rnd


def part(pts, f, L, w=2.2, smooth=True, closed=True, n=6, **kw):
    p = cr(pts, closed, n) if smooth else [list(q) for q in pts]
    d = {'p': rnd(p), 'f': f, 'L': L, 'w': w}
    d.update(kw)
    return d


# ---------------------------------------------------------------- heads (local: origin at the skull base, facing left)
HEAD = [(8, -6), (4, -15), (-6, -20), (-17, -19), (-26, -14), (-31, -10), (-42, -8), (-51, -6), (-55, -2), (-53, 3),
        (-45, 6), (-35, 9), (-24, 12), (-10, 14), (4, 10)]
EARS = {
    'up': [(-6, -16), (-3, -30), (2, -43), (8, -33), (13, -13)],
    'half': [(-5, -16), (6, -28), (18, -34), (17, -23), (14, -12)],
    'low': [(-2, -15), (12, -21), (25, -21), (18, -12), (8, -8)],
    'back': [(-3, -16), (10, -25), (24, -27), (19, -16), (9, -9)],
    'flat': [(-1, -15), (14, -19), (27, -17), (18, -10), (8, -7)],
}


def head_profile(base, pitch=0.0, ears='up', mouth=0.0, eye='open', s=1.0, flip=False, far_ear=True, tilt_ear=None):
    """A profile head, nose to the left (flip: nose to the right). pitch>0 lifts the nose."""
    ang = pitch if not flip else -pitch
    T = lambda pts: xf(pts, at=base, ang=ang, s=s, flip=flip)
    out = []
    if far_ear:
        fe = [(x - 7, y + 1) for x, y in EARS[ears if tilt_ear is None else tilt_ear]]
        out.append(part(T(fe), 'saddleD', 'far', w=1.8))
    sk = HEAD[:]
    if mouth > 0:
        sk = [(x, y + (mouth * 6 if (x < -30 and y > 0) else 0)) for x, y in sk]
    out.append(part(T(sk), 'coat', 'main'))
    out.append(part(T(EARS[ears]), 'ear', 'main', w=2.0))
    # mask on the muzzle and a dark crown, as on the archive dog
    out.append(part(T([(-29, -22), (-62, -20), (-62, 18), (-34, 16), (-24, 6), (-26, -4)]), 'saddle', 'mark', a=.78))
    out.append(part(T([(14, -26), (-4, -24), (-14, -20), (-8, -12), (6, -8), (16, -10)]), 'saddle', 'mark', a=.7))
    if eye == 'open':
        out.append(part(T(ellipse((-24, -8), 3.4, 2.3, -0.2, 10)), 'eye', 'dot', smooth=False))
        out.append(part(T(ellipse((-25, -8.8), .9, .9, 0, 6)), 'glint', 'dot', smooth=False))
        out.append(part(T([(-19, -12.5), (-25, -13.5), (-30, -11.5)]), 'ink', 'line', w=1.3, closed=False))
    else:
        out.append(part(T([(-20, -7), (-24, -6), (-28, -7.5)]), 'ink', 'line', w=1.6, closed=False))
    out.append(part(T(ellipse((-53, -2.2), 4.2, 3.4, 0, 10)), 'nose', 'dot', smooth=False))
    out.append(part(T([(-52, 4 + mouth * 3), (-44, 6 + mouth * 4), (-36, 7 + mouth * 2)]), 'ink', 'line', w=1.3, closed=False))
    out.append(part(T([(-4, -14), (2, -6), (4, 4)]), 'saddleD', 'line', w=1.0, closed=False))
    return out, {'nose': T([(-55, -2)])[0], 'eye': T([(-24, -8)])[0], 'top': T([(0, -40)])[0]}


# ---------------------------------------------------------------- the profile body (facing left)
def torso_pts(W, R, d, sag=3.0, tuck=0.8):
    mid = lerp(W, R, .5)
    return [W, add(mid, (0, sag)), R, add(R, (13, 3)), add(R, (21, 18)), add(R, (17, d * .62)),
            add(R, (-6, d * tuck)), add(mid, (4, d * .93)), add(W, (4, d + 2)), add(W, (-14, d * .9)),
            add(W, (-25, d * .52)), add(W, (-19, d * .14))]


def front_leg(sh, paw, toe=-1, up=36, lo=37):
    wrist = (paw[0] - toe * 4, paw[1] - 12)
    el = ik2(sh, wrist, up, lo, -1 if toe < 0 else 1)
    return [sh, el, wrist, paw]


def hind_leg(hip, paw, toe=-1, up=35, lo=33):
    hock = (paw[0] - toe * 4, paw[1] - 22)
    st = ik2(hip, hock, up, lo, 1 if toe < 0 else -1)
    return [hip, st, hock, paw]


def tail_part(ctrl, w0=12, w1=3, L='main', f='coat'):
    dense = cr(ctrl, False, 5)
    m = len(dense)
    widths = [w0 + (w1 - w0) * (i / (m - 1)) ** .8 for i in range(m)]
    return part(limb(dense, widths), f, L, smooth=False)


def profile_dog(W, R, d, head, paws, tail, socks=True, sag=3.0, tuck=0.8, extra=None, front_joints=None, hind_joints=None):
    """head: dict(base, pitch, ears, mouth, eye) ; paws: dict fn, ff, hn, hf (ground targets) ; tail: control points."""
    parts = []
    sh = add(W, (-8, d * .45)); hp = add(R, (0, d * .42))
    FJ = front_joints or {}
    HJ = hind_joints or {}
    # far legs
    ffj = FJ.get('ff') or front_leg(add(sh, (5, 0)), paws['ff'])
    hfj = HJ.get('hf') or hind_leg(add(hp, (-4, 0)), paws['hf'])
    parts.append(part(limb(ffj, [17, 11, 8, 7.5], foot=(-1, 9)), 'coatD', 'far'))
    parts.append(part(limb(hfj, [24, 13, 8.5, 7.5], foot=(-1, 9)), 'coatD', 'far'))
    if socks:
        parts.append(part([(-200, -30), (200, -30), (200, 9), (-200, 9)], 'creamD', 'farmark', smooth=False, a=.9))
    kind = head.get('kind', 'profile')
    hargs = {k: v for k, v in head.items() if k != 'kind'}
    if kind == 'profile':
        hd, hm = head_profile(**hargs)
    elif kind == 'q':
        hd = head_q(**{k: v for k, v in hargs.items() if k in ('base', 'ears', 's', 'pitch', 'flip')}); hm = {'nose': add(head['base'], (-44, 0)), 'eye': add(head['base'], (-20, -7))}
    elif kind == 'back':
        hd = head_back(head['base'], head.get('s', 1.0), head.get('turn', -.3)); hm = {'nose': add(head['base'], (-30, -2)), 'eye': add(head['base'], (-10, -10))}
    hd = hd + head.get('extra', [])
    # far ear goes behind everything
    parts += [q for q in hd if q['L'] == 'far']
    tailp = tail_part(tail)
    parts.append(tailp)
    parts.append(part(torso_pts(W, R, d, sag, tuck), 'coat', 'main'))
    # neck: from the withers and chest to the skull base
    b = head['base']; pitch = head.get('pitch', 0)
    ca, sa = math.cos(pitch), math.sin(pitch)
    tb = (b[0] + 6 * ca + 12 * sa, b[1] + 6 * sa - 12 * ca)    # top of skull base (rotated (6,-12))
    th = (b[0] + 2 * ca - 13 * sa, b[1] + 2 * sa + 13 * ca)    # throat
    chest = add(W, (-24, d * .55))
    neck = [add(W, (10, -1)), lerp(add(W, (8, -1)), tb, .5), tb, add(b, (4, 0)), th, lerp(th, chest, .5), chest, add(W, (-6, d * .4))]
    if kind == 'back':
        sc = head.get('s', 1.0)
        neck = [add(W, (12, -1)), add(b, (20 * sc, 2)), add(b, (14 * sc, 12 * sc)), add(b, (-14 * sc, 10 * sc)), add(b, (-20 * sc, 0)), chest, add(W, (-6, d * .4))]
    parts.append(part(neck, 'coat', 'main'))
    nfj = FJ.get('fn') or front_leg(sh, paws['fn'])
    hnj = HJ.get('hn') or hind_leg(hp, paws['hn'])
    parts.append(part(limb(nfj, [22, 13, 9.5, 8.5], foot=(-1, 10)), 'coat', 'main'))
    parts.append(part(limb(hnj, [32, 16, 10, 8.5], foot=(-1, 10)), 'coat', 'main'))
    parts += [q for q in hd if q['L'] == 'main']
    # markings: saddle, ring of ruff, pale chest, socks
    mid = lerp(W, R, .5)
    parts.append(part([add(W, (-10, -6)), add(mid, (0, -4)), add(R, (12, -6)), add(R, (20, 14)), add(R, (4, d * .45)),
                       add(mid, (14, d * .5)), add(mid, (-8, d * .4)), add(W, (8, d * .48)), add(W, (-4, d * .3))], 'saddle', 'mark', a=.92))
    t0 = add(W, (8, -1))
    ux, uy = tb[0] - th[0], tb[1] - th[1]
    ring = [add(lerp(t0, tb, .30), (ux * .4, uy * .4)), add(lerp(t0, tb, .66), (ux * .4, uy * .4)),
            add(lerp(chest, th, .78), (-ux * .4, -uy * .4)), add(lerp(chest, th, .40), (-ux * .4, -uy * .4))]
    if kind == 'back':
        sc = head.get('s', 1.0)
        ring = [add(b, (-30 * sc, 4 * sc)), add(b, (30 * sc, 4 * sc)), add(b, (30 * sc, 18 * sc)), add(b, (-30 * sc, 16 * sc))]
    parts.append(part(ring, 'cream', 'mark', a=.95))
    parts.append(part([add(W, (-28, d * .35)), add(W, (-14, d * .4)), add(W, (2, d * 1.05)), add(W, (-12, d * 1.05)), add(W, (-24, d * .8))], 'cream', 'mark', a=.6))
    if socks:
        parts.append(part([(-200, -28), (200, -28), (200, 9), (-200, 9)], 'cream', 'mark', smooth=False, a=.85))
    # tail top dark, a few fur ticks along the saddle edge
    parts.append(part(limb(cr(tail, False, 5)[:], [7] * len(cr(tail, False, 5))), 'saddle', 'mark', smooth=False, a=.85))
    for t in (.15, .35, .55, .75):
        p0 = lerp(add(W, (6, d * .46)), add(R, (6, d * .44)), t)
        parts.append(part([p0, add(p0, (-3, 4))], 'saddleD', 'line', w=.8, closed=False, smooth=False))
    parts += [q for q in hd if q['L'] in ('line', 'dot')]
    # elbow and stifle ink
    parts.append(part([add(nfj[1], (3, -6)), add(nfj[1], (1, 3))], 'ink', 'line', w=1.1, closed=False, smooth=False))
    parts.append(part([add(hnj[0], (-12, 2)), add(hnj[1], (-6, -2)), add(hnj[1], (-2, 6))], 'ink', 'line', w=1.0, closed=False))
    if extra:
        parts += extra
    feet = {'fn': nfj[-1], 'ff': ffj[-1], 'hn': hnj[-1], 'hf': hfj[-1]}
    meta = {'feet': feet, 'nose': hm['nose'], 'eye': hm['eye'], 'withers': W, 'croup': R}
    return parts, meta


# ---------------------------------------------------------------- heads seen from other angles
def head_front(c, ears='up', s=1.0, eyes='up', look=0.0):
    """Head facing the viewer. c = centre of the skull. look shifts muzzle and eyes sideways (-1 left .. 1 right)."""
    T = lambda pts: [(c[0] + x * s, c[1] + y * s) for x, y in pts]
    out = []
    E = {'up': ([(-14, -10), (-22, -26), (-24, -42), (-12, -30), (-5, -14)]),
         'flat': ([(-12, -9), (-26, -12), (-38, -8), (-30, -2), (-14, 0)]),
         'half': ([(-13, -10), (-26, -20), (-34, -32), (-20, -26), (-6, -13)]),
         'droop': ([(-12, -12), (-24, -14), (-32, -6), (-30, 4), (-18, 0)])}[ears]
    for sgn in (-1, 1):
        out.append(part(T([(sgn * x, y) for x, y in E]), 'ear', 'main', w=2.0))
    sk = [(-17, -12), (-8, -18), (8, -18), (17, -12), (20, 0), (16, 10), (10, 18), (0, 22), (-10, 18), (-16, 10), (-20, 0)]
    out.append(part(T(sk), 'coat', 'main'))
    m = look * 6
    out.append(part(T([(-6 + m, -4), (6 + m, -4), (11 + m, 8), (9 + m, 22), (0 + m, 27), (-9 + m, 22), (-11 + m, 8)]), 'saddle', 'mark', a=.75))
    out.append(part(T([(-10, -19), (0, -14), (10, -19), (6, -8), (-6, -8)]), 'saddle', 'mark', a=.7))
    for sgn in (-1, 1):
        ex = sgn * 9 + look * 3
        out.append(part(T(ellipse((ex, -4), 3.2, 2.6, 0, 10)), 'eye', 'dot', smooth=False))
        out.append(part(T(ellipse((ex - .8 + look, -4.8 - (1 if eyes == 'up' else 0)), .9, .9, 0, 6)), 'glint', 'dot', smooth=False))
        out.append(part(T([(ex - 4, -9), (ex, -10.5), (ex + 4, -9)]), 'ink', 'line', w=1.2, closed=False))
    out.append(part(T(ellipse((m * 1.2, 18), 5.5, 4.2, 0, 10)), 'nose', 'dot', smooth=False))
    out.append(part(T([(-6 + m, 25), (m, 27), (6 + m, 25)]), 'ink', 'line', w=1.2, closed=False))
    return out


def head_q(base, ears='up', s=1.0, pitch=0.0, flip=False):
    """Three-quarter head, nose to the left and toward the viewer."""
    T = lambda pts: xf(pts, at=base, ang=(pitch if not flip else -pitch), s=s, flip=flip)
    out = []
    E1 = {'up': [(-14, -15), (-14, -30), (-12, -44), (-4, -32), (0, -17)], 'flat': [(-8, -14), (2, -22), (14, -24), (10, -14), (2, -10)],
          'half': [(-12, -15), (-8, -30), (-2, -38), (2, -28), (2, -16)]}[ears]
    E2 = {'up': [(4, -14), (8, -30), (14, -42), (18, -30), (16, -10)], 'flat': [(6, -12), (18, -18), (30, -16), (22, -8), (12, -6)],
          'half': [(5, -14), (14, -28), (22, -34), (22, -22), (16, -10)]}[ears]
    out.append(part(T(E2), 'ear', 'main', w=2.0))
    sk = [(12, -6), (8, -16), (-4, -21), (-16, -18), (-24, -10), (-34, -6), (-41, -1), (-40, 6), (-32, 11), (-20, 15), (-4, 15), (8, 9)]
    out.append(part(T(sk), 'coat', 'main'))
    out.append(part(T(E1), 'ear', 'main', w=2.0))
    out.append(part(T([(-22, -20), (-50, -16), (-48, 18), (-24, 16), (-16, 4), (-18, -6)]), 'saddle', 'mark', a=.75))
    out.append(part(T([(-12, -28), (8, -28), (12, -16), (-2, -15), (-14, -16)]), 'saddle', 'mark', a=.6))
    for ex, ey, r in ((-20, -7, 3.2), (-4, -8, 2.8)):
        out.append(part(T(ellipse((ex, ey), r, r * .75, 0, 10)), 'eye', 'dot', smooth=False))
        out.append(part(T(ellipse((ex - .8, ey - .8), .85, .85, 0, 6)), 'glint', 'dot', smooth=False))
        out.append(part(T([(ex - 4, ey - 5), (ex, ey - 6.5), (ex + 4, ey - 5)]), 'ink', 'line', w=1.2, closed=False))
    out.append(part(T(ellipse((-40, 0), 4.6, 3.8, 0, 10)), 'nose', 'dot', smooth=False))
    out.append(part(T([(-40, 6), (-33, 9), (-25, 9)]), 'ink', 'line', w=1.2, closed=False))
    return out


def head_back(base, s=1.0, turn=-0.3):
    """The head seen from behind: the dog looks away from the viewer, into the doorway. The back of the skull and
    both ears face us; only a sliver of cheek shows on the side it is turned toward (turn<0: a little left).
    Local origin at the top of the neck."""
    T = lambda pts: [(base[0] + x * s, base[1] + y * s) for x, y in pts]
    out = []
    o = turn * 8
    out.append(part(T([(-17 + o, -12), (-25 + o, -12), (-27 + o, -5), (-17 + o, -2)]), 'coatD', 'far', w=1.8))   # cheek beyond
    for sx in (-1, 1):
        out.append(part(T([(sx * 7 + o, -22), (sx * 13 + o, -38), (sx * 18 + o, -52), (sx * 21 + o, -36), (sx * 21 + o, -18)]), 'saddleD', 'main', w=2.0))
    sk = [(-18 + o, -2), (-20 + o, -15), (-13 + o, -25), (0 + o, -28), (13 + o, -25), (19 + o, -15), (17 + o, -2), (10, 7), (0, 10), (-10, 7)]
    out.append(part(T(sk), 'coat', 'main'))
    out.append(part(T([(-24 + o, -34), (24 + o, -34), (22 + o, -10), (10 + o, -6), (-10 + o, -6), (-22 + o, -10)]), 'saddle', 'mark', a=.85))
    out.append(part(T([(o, -26), (o * .7, -14), (0, -2)]), 'saddleD', 'line', w=1.1, closed=False))
    return out
