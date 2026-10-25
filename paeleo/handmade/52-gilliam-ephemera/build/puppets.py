"""The two puppets as hinged cards. A pose is a dict; draw_* lays the pieces with pins (rotation about a pin),
slides (translation), flops (a mirrored print) and substitutions (another card in place of the whole)."""
import math
from table import place, pin, T, R, FLIP, Aff, PIECES

FLOOR_DOG = 602      # screen y where the dog's near feet stand (just in front of the wall)

# ---------------------------------------------------------------------------------------------- dog
LEGS = {  # piece: (pivot pin on torso, foot pin)
    'dog_fore': 'shoulder', 'dog_farfore': 'farshoulder', 'dog_hind': 'hip', 'dog_farhind': 'farhip'}
FOOT_Y = pin('dog_fore', 'foot')[1]       # puppet-space y of the near forefoot
CENTRE = pin('dog_torso', 'centre')
BELLY = pin('dog_torso', 'belly')


def leg_len(p):
    piv = [v for k, v in PIECES[p]['pins'].items() if k != 'foot'][0]
    f = pin(p, 'foot')
    return math.hypot(f[0] - piv[0], f[1] - piv[1])


def dog_global(pose):
    """puppet space -> screen. pose: X (screen x of the body centre), face (+1 facing left/door, -1 flopped),
    drop (px the body is lowered), tilt (deg)."""
    X = pose['X']; face = pose.get('face', 1)
    Y = FLOOR_DOG - (FOOT_Y - CENTRE[1]) + pose.get('drop', 0)
    G = T(X, Y)
    if face < 0:
        G = G @ FLIP()
    G = G @ R(pose.get('tilt', 0)) @ T(-CENTRE[0], -CENTRE[1])
    return G


def draw_dog(canvas, pose, rec=None, tint=None):
    if pose.get('card') == 'front':
        # substitution: the whole turning card, feet on the floor
        f = pin('dog_front', 'feet')
        G = T(pose['X'], FLOOR_DOG + pose.get('drop', 0))
        if pose.get('face', 1) < 0:
            G = G @ FLIP()
        G = G @ T(-f[0], -f[1])
        place(canvas, 'dog_front', G, tint=tint, record=rec)
        return
    G = dog_global(pose)
    def piv(p): return [v for k, v in PIECES[p]['pins'].items() if k != 'foot'][0]
    # far side first (behind the torso), as cards lie on the table
    place(canvas, 'dog_farhind', G @ R(pose.get('farhind', 0), piv('dog_farhind')), tint=tint, record=rec)
    place(canvas, 'dog_farfore', G @ R(pose.get('farfore', 0), piv('dog_farfore')), tint=tint, record=rec)
    place(canvas, 'dog_tail', G @ R(pose.get('tail', 0), pin('dog_tail', 'tailroot')), tint=tint, record=rec)
    place(canvas, 'dog_torso', G, tint=tint, record=rec)
    place(canvas, 'dog_hind', G @ R(pose.get('hind', 0), piv('dog_hind')), tint=tint, record=rec)
    place(canvas, 'dog_fore', G @ R(pose.get('fore', 0), piv('dog_fore')), tint=tint, record=rec)
    nk = pin('dog_torso', 'neck')
    hp = pose.get('headpiece', 'dog_head')
    if hp == 'dog_backhead':
        b = pin('dog_backhead', 'neck')
        A = G @ T(nk[0] - 14, nk[1] + 20) @ R(pose.get('head', 0)) @ T(-b[0], -b[1])
        place(canvas, 'dog_backhead', A, tint=tint, record=rec)
    elif hp in ('dog_head_low', 'dog_face'):
        place(canvas, hp, head_low_aff(G, pose, hp), tint=tint, record=rec)
    else:
        A = G @ T(0, pose.get('neckdrop', 0)) @ R(pose.get('head', 0), nk)
        if pose.get('headflop'):
            A = A @ T(nk[0], 0) @ FLIP() @ T(-nk[0], 0)   # the head card turned over (a mirrored print)
        place(canvas, 'dog_head', A, tint=tint, record=rec)


LOW_ATTACH = (124 * 1.31, 126 * 1.31)
FACE_ATTACH = (132 * 1.31, 118 * 1.31)   # the face card sits on the neck, over the shoulders   # the head-low card hangs from the front of the chest, below the neck pin


def head_low_aff(G, pose, hp='dog_head_low'):
    """the head-low print faces right; in puppet space (facing left) it is flopped about its neck pin, unless the
    head is turned back over the shoulder (headflop), when it is laid as printed."""
    p = pin(hp, 'neck')
    at = LOW_ATTACH if hp == 'dog_head_low' else FACE_ATTACH
    A = G @ T(*at) @ R(pose.get('head', 0))
    if not pose.get('headflop'):
        A = A @ FLIP()
    return A @ T(-p[0], -p[1])


def dog_points(pose):
    """screen positions of named points of a puppet pose (for the trace)."""
    if pose.get('card') == 'front':
        return {'head': (pose['X'] + 14 * pose.get('face', 1) * -1, FLOOR_DOG - 100), 'tail': (pose['X'], FLOOR_DOG - 60)}
    G = dog_global(pose)
    nk = pin('dog_torso', 'neck')
    H = G @ T(0, pose.get('neckdrop', 0)) @ R(pose.get('head', 0), nk)
    if pose.get('headflop'):
        H = H @ T(nk[0], 0) @ FLIP() @ T(-nk[0], 0)
    hp = pose.get('headpiece', 'dog_head')
    if hp in ('dog_head_low', 'dog_face'):
        hd = head_low_aff(G, pose, hp).apply(pin(hp, 'nose'))
    elif hp == 'dog_head':
        hd = H.apply(pin('dog_head', 'nose'))
    else:
        hd = G.apply((nk[0] - 6, nk[1] - 20))
    out = {'head': hd, 'shoulder': G.apply(pin('dog_torso', 'shoulder')),
           'neck': G.apply(nk), 'centre': G.apply(CENTRE),
           'tail': (G @ R(pose.get('tail', 0), pin('dog_tail', 'tailroot'))).apply(pin('dog_tail', 'tip'))}
    for p in LEGS:
        out[p] = (G @ R(pose.get(p.split('_')[1], 0), [v for k, v in PIECES[p]['pins'].items() if k != 'foot'][0])).apply(pin(p, 'foot'))
    return out


# ---------------------------------------------------------------------------------------------- person
FLOOR_P = 596


def draw_person(canvas, pose, rec=None, tint=None):
    """pose: X (screen x of the hip), sit (0 standing .. 1 seated on the crate), arm (deg; 0 hanging, 90 level toward
    the dog), jaw (0..1 open), nod (deg, + toward the dog/down), lean (deg, + forward), crateX (where the crate stands)."""
    X = pose['X']; s = pose.get('sit', 0)
    hip = pin('person_thigh', 'hip'); knee = pin('person_thigh', 'knee'); ank = pin('person_shin', 'ankle')
    thigh_len = knee[1] - hip[1]; shin_len = ank[1] - knee[1]
    th = -90 * s                     # thighs swivel at the hip pin from hanging to level (toward +x)
    shoe_h = 12
    hip_y = FLOOR_P - shoe_h - shin_len - thigh_len * math.cos(math.radians(th))
    G = T(X, hip_y)
    Gt = G @ R(th) @ T(-hip[0], -hip[1])
    kn = Gt.apply(knee)
    Gs = T(kn[0], kn[1]) @ T(-knee[0], -knee[1])
    an = Gs.apply(ank)
    bh = pin('person_body', 'hip'); bn = pin('person_body', 'neck'); bs = pin('person_body', 'shoulder')
    Gb = G @ R(pose.get('lean', 0)) @ T(-bh[0], -bh[1])
    neck = Gb.apply(bn); sh = Gb.apply(bs)
    ash = pin('person_arm', 'shoulder')
    arm = pose.get('arm', 0)
    Ga = T(sh[0] - 10, sh[1] + 8) @ R(90 - arm) @ FLIP() @ T(-ash[0], -ash[1])
    hn = pin('person_head', 'neck'); jp = pin('person_head', 'jaw')
    Gh = T(neck[0] + 4, neck[1] + 14) @ R(pose.get('nod', 0)) @ FLIP() @ T(-hn[0], -hn[1])   # flopped print
    Gj = Gh @ R(-24 * pose.get('jaw', 0), jp)
    mp = Gh.apply(pin('person_head', 'mouth')); mc = pin('mouth', 'c')
    Gm = T(mp[0], mp[1]) @ R(pose.get('nod', 0)) @ T(-mc[0], -mc[1])
    if pose.get('crate'):
        c = pin('crate', 'top'); place(canvas, 'crate', T(pose['crate'], FLOOR_P - 70 + 4) @ T(-c[0], 0), tint=tint)
    ap = pin('shoes', 'ankle')
    place(canvas, 'shoes', T(an[0], an[1]) @ T(-ap[0], -ap[1] + 2), tint=tint, record=rec)
    place(canvas, 'person_shin', Gs, tint=tint, record=rec)
    place(canvas, 'person_thigh', Gt, tint=tint, record=rec)
    place(canvas, 'person_body', Gb, tint=tint, record=rec)
    place(canvas, 'mouth', Gm, tint=tint, shadow=None)
    place(canvas, 'person_jaw', Gj, tint=tint, record=rec)
    place(canvas, 'person_head', Gh, tint=tint, record=rec)
    place(canvas, 'person_arm', Ga, tint=tint, record=rec)
    return {'hand': Ga.apply(pin('person_arm', 'hand')), 'neck': neck, 'hip_y': hip_y}
