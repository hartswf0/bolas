"""SCION 17 // cast: BISCUIT, a porch mutt cut from construction paper (cast bible v1).

Typed pose in, pieces out. The figure frame: centimetres, y up, origin on the ground under the body centre, the dog faces
-x (screen left, toward the door). A right-facing dog is the same complete profile drawing turned over (mirror=True);
it is never squashed through edge-on: the turn is a substitution through drawn direction states.

Direction states (body):  P (profile)  Q (three-quarter front)  F (front)
Head direction states:    P  Q  F  QB (three-quarter back)  B (back of the head: looking away from camera, into the house)
Body drawings:            STAND (planted-foot leg rig, height H)   LIE (a lying drawing: belly, elbows and hocks on the floor)
Expression atlas:         eye OPEN WIDE HALF CLOSED x brow NEUTRAL WORRY DOWN UP x ear PRICK HALF FLAT
Head stops:               UP MID LOW DOWN (standing), UP MID CHIN (lying)
"""
import math
import numpy as np
from kit import PAPER as C, Piece, ellipse, rrect, capsule, poly, handcut, affine, apply, ik2

VERSION = 'biscuit-v1'

# leg geometry (cm): thigh, shin, hip offsets from the body centre (standing drawing)
LEG = {'front': dict(a=17.0, b=19.0, hip=(-22.0, -6.0), bend=+1, w0=9.0, w1=7.0),
       'hind': dict(a=18.0, b=19.0, hip=(22.0, -4.0), bend=-1, w0=12.0, w1=7.0)}
NECK = (-30.0, 16.0)          # neck pivot relative to body centre (standing profile)
H_STAND = 40.0                 # body centre height when upright


def hull(pts):
    pts = sorted(map(tuple, np.asarray(pts)))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


def P(pts, fill, z, tag, name=None, amp=0.4, outline=True):
    if name: pts = handcut(pts, 'biscuit.' + name, amp)
    return Piece(pts, fill, z, tag, outline)


EAR_SHAPE = np.array([(-5, 0), (-4.6, 6), (-2.4, 12.5), (0.2, 16), (2.8, 12.5), (4.9, 5), (5, 0)], float)


def ear_piece(base, rot, fill, z, name, scale=1.0):
    pts = EAR_SHAPE * scale
    M = affine(base[0], base[1], rot)
    return P(pts @ M[:2, :2].T + M[:2, 2], fill, z, 'ear', name, 0.3)


def eye_pieces(cx, cy, rx, ry, eye, gaze, z, name, lidcol):
    out = []
    k = 1.14 if eye == 'WIDE' else 1.0
    out.append(P(ellipse(cx, cy, rx * k, ry * k, n=16), C['eye'], z, 'eye', name + '.white', 0.15))
    pr = min(rx, ry) * (0.42 if eye == 'WIDE' else 0.52)
    gx, gy = gaze
    px = cx + gx * (rx * k - pr - 0.4); py = cy + gy * (ry * k - pr - 0.6)
    if eye != 'CLOSED':
        out.append(Piece(ellipse(px, py, pr, pr * 1.08, n=12), C['pupil'], z + 1, 'pupil', outline=False))
    if eye in ('HALF', 'CLOSED'):
        cut = cy + (ry * 0.05 if eye == 'HALF' else -ry * 1.2)
        a = np.linspace(0, np.pi, 14)
        top = np.stack([cx + rx * 1.08 * np.cos(a), cy + ry * 1.08 * np.sin(a)], 1)
        top = top[top[:, 1] >= cut] if eye == 'HALF' else np.stack([cx + rx * 1.08 * np.cos(np.linspace(0, 2 * np.pi, 18)), cy + ry * 1.08 * np.sin(np.linspace(0, 2 * np.pi, 18))], 1)
        if eye == 'HALF':
            top = np.vstack([[cx + rx * 1.08, cut], top, [cx - rx * 1.08, cut]])
        out.append(Piece(top, lidcol, z + 2, 'lid'))
        if eye == 'CLOSED':
            out.append(Piece(capsule((cx - rx * 0.9, cy - ry * 0.1), (cx + rx * 0.9, cy - ry * 0.1), 1.2), C['ink'], z + 3, 'lash', outline=False))
    return out


# ---------------------------------------------------------------- heads (head frame: origin at the neck pivot, facing -x)
def head(view, ear, eye, brow, gaze):
    pc = []
    if view == 'P':
        pc.append(ear_piece((-3.0, 25.0), {'PRICK': -6, 'HALF': -48, 'FLAT': -96}[ear] + 8, C['dog_ear_far'], 19, 'ear_far', 0.9))
        pc.append(P(ellipse(-8, 18, 12.5, 12), C['dog'], 20, 'skull', 'skull'))
        pc.append(P(rrect(-31, 7, -11, 18.5, 5), C['dog'], 21, 'snout', 'snout'))
        pc.append(P(rrect(-30.5, 7, -14, 12.5, 3), C['dog_cream'], 22, 'muzzle', 'muzzle', outline=False))
        pc.append(P(ellipse(-31, 15.5, 4, 3.4), C['nose'], 23, 'nose', 'nose', 0.2))
        pc.append(Piece(capsule((-28.5, 9.6), (-17, 9.2), 1.1), C['ink'], 23, 'mouth', outline=False))
        pc += eye_pieces(-12.5, 21.0, 4.3, 5.2, eye, gaze, 24, 'eyeP', C['dog'])
        b = {'NEUTRAL': ((-17, 27.6), (-9, 28.0)), 'WORRY': ((-17, 29.2), (-9, 26.9)), 'DOWN': ((-17, 25.9), (-9, 28.6)), 'UP': ((-17, 29.6), (-9, 30.2))}[brow]
        pc.append(Piece(capsule(b[0], b[1], 1.7), C['ink'], 27, 'brow', outline=False))
        pc.append(ear_piece((1.0, 25.5), {'PRICK': -8, 'HALF': -52, 'FLAT': -100}[ear], C['dog_ear'], 28, 'ear_near'))
    elif view == 'Q':
        pc.append(ear_piece((-14.0, 26.5), {'PRICK': 12, 'HALF': 42, 'FLAT': 85}[ear], C['dog_ear_far'], 19, 'ear_far', 0.85))
        pc.append(P(ellipse(-6, 16, 13, 12.5), C['dog'], 20, 'skull', 'skullQ'))
        pc.append(P(ellipse(-17, 9, 9.5, 6.8), C['dog_cream'], 21, 'muzzle', 'muzzleQ'))
        pc.append(P(ellipse(-24, 12, 3.9, 3.1), C['nose'], 23, 'nose', 'noseQ', 0.2))
        pc.append(Piece(capsule((-22, 5.6), (-15, 4.8), 1.0), C['ink'], 23, 'mouth', outline=False))
        pc += eye_pieces(-4.5, 19.5, 4.2, 5.1, eye, gaze, 24, 'eyeQn', C['dog'])
        pc += eye_pieces(-15.5, 20.0, 3.3, 4.5, eye, gaze, 24, 'eyeQf', C['dog'])
        b = {'NEUTRAL': (0, 0), 'WORRY': (1.3, -1.0), 'DOWN': (-1.2, 1.0), 'UP': (1.6, 1.6)}[brow]
        pc.append(Piece(capsule((-8.5, 25.6 + b[0]), (-1.5, 25.9 + b[1]), 1.6), C['ink'], 27, 'brow', outline=False))
        pc.append(Piece(capsule((-18.5, 25.9 + b[1]), (-13.0, 25.6 + b[0]), 1.4), C['ink'], 27, 'brow', outline=False))
        pc.append(ear_piece((2.5, 24.5), {'PRICK': -10, 'HALF': -50, 'FLAT': -95}[ear], C['dog_ear'], 28, 'ear_near'))
    elif view == 'F':
        er = {'PRICK': 14, 'HALF': 62, 'FLAT': 112}[ear]
        pc.append(ear_piece((-10.5, 24.5), er, C['dog_ear'], 19, 'earL'))
        pc.append(ear_piece((10.5, 24.5), -er, C['dog_ear'], 19, 'earR'))
        pc.append(P(ellipse(0, 16, 14, 13), C['dog'], 20, 'skull', 'skullF'))
        pc.append(P(ellipse(0, 7.5, 9, 7), C['dog_cream'], 21, 'muzzle', 'muzzleF'))
        pc.append(P(ellipse(0, 11.5, 4.2, 3.1), C['nose'], 23, 'nose', 'noseF', 0.2))
        pc.append(Piece(capsule((-4, 4.3), (4, 4.3), 1.0), C['ink'], 23, 'mouth', outline=False))
        pc += eye_pieces(-6.2, 19.5, 4.0, 5.0, eye, gaze, 24, 'eyeFL', C['dog'])
        pc += eye_pieces(6.2, 19.5, 4.0, 5.0, eye, gaze, 24, 'eyeFR', C['dog'])
        b = {'NEUTRAL': (0, 0), 'WORRY': (1.4, -0.8), 'DOWN': (-1.3, 1.0), 'UP': (1.6, 1.6)}[brow]
        pc.append(Piece(capsule((-9.5, 25.6 + b[1]), (-3, 25.6 + b[0]), 1.6), C['ink'], 27, 'brow', outline=False))
        pc.append(Piece(capsule((3, 25.6 + b[0]), (9.5, 25.6 + b[1]), 1.6), C['ink'], 27, 'brow', outline=False))
    elif view == 'QB':
        pc.append(P(ellipse(-19, 12, 7.5, 5.2), C['dog'], 19, 'snout', 'snoutQB'))
        pc.append(P(ellipse(-25.5, 13.5, 2.6, 2.3), C['nose'], 19, 'nose', 'noseQB', 0.15))
        pc.append(ear_piece((-11.0, 26.5), {'PRICK': 8, 'HALF': 38, 'FLAT': 80}[ear], C['dog_ear_far'], 21, 'ear_far', 0.9))
        pc.append(P(ellipse(-4, 17, 12.5, 12.5), C['dog'], 20, 'skull', 'skullQB'))
        pc.append(ear_piece((3.0, 26.0), {'PRICK': -8, 'HALF': -45, 'FLAT': -95}[ear], C['dog_ear'], 28, 'ear_near'))
    elif view == 'B':
        er = {'PRICK': 10, 'HALF': 55, 'FLAT': 105}[ear]
        pc.append(P(ellipse(0, 18, 12.5, 13), C['dog'], 20, 'skull', 'skullB'))
        pc.append(ear_piece((-8.0, 27.0), er, C['dog_ear'], 28, 'earBL'))
        pc.append(ear_piece((8.0, 27.0), -er, C['dog_ear'], 28, 'earBR'))
    return pc


HEAD_STOPS = {'UP': (0, 0, 4), 'MID': (-2, -9, -10), 'LOW': (-9, -38, -22), 'DOWN': (-9, -42, -30),
              'L_UP': (0, 0, 0), 'L_MID': (-2, -7, -8), 'L_CHIN': (3, -27, -3), 'L_HIGH': (1, 4, 6)}


def tail_pieces(base, ang, z, lie=False):
    a1 = math.radians(ang); a2 = math.radians(ang + (8 if not lie else 4))
    p0 = np.array(base, float); p1 = p0 + 14 * np.array([math.cos(a1), math.sin(a1)]); p2 = p1 + 13 * np.array([math.cos(a2), math.sin(a2)])
    return [P(capsule(p0, p1, 7.5, 5.5), C['dog'], z, 'tail', 'tail1', 0.25),
            P(capsule(p1, p2, 5.5, 3.0), C['dog'], z, 'tail', 'tail2', 0.25)]


def legs_profile(H, feet, near):
    """Planted-foot legs: feet are given (they were placed on the ground by the gait and stay there); knees are solved."""
    out = []
    for kind in ('front', 'hind'):
        g = LEG[kind]; hip = np.array([g['hip'][0], H + g['hip'][1]])
        side = 'n' if near else 'f'
        foot = np.array(feet[kind + side], float)
        knee, ft = ik2(hip, foot, g['a'], g['b'], g['bend'])
        col = C['dog'] if near else C['dog_far']
        z = 14 if near else 2
        nm = kind + side
        out.append(P(capsule(hip, knee, g['w0'], 8.0), col, z, 'leg', nm + '.thigh', 0.25))
        out.append(P(capsule(knee, ft + [0, 2.5], 7.5, g['w1']), col, z, 'leg', nm + '.shin', 0.25))
        out.append(P(ellipse(ft[0] - 3.0, ft[1] + 2.6, 5.6, 3.0, n=12), col, z + 0.5, 'paw', nm + '.paw', 0.2))
    return out


def body_stand_P(H, hd=(0.0, 0.0)):
    """the standing profile; the neck runs from the chest to wherever the head stop puts the head, collar across it"""
    body = hull(np.vstack([ellipse(2, H, 30, 13.5, n=30), ellipse(-22, H - 1, 13.5, 14.5, n=24)]))
    n0 = np.array([-23.0, H + 3.0]); n1 = np.array([NECK[0] + hd[0], H + NECK[1] + hd[1]])
    if hd[1] < -5: n1 = n1 + [2.0, 12.0]
    u = (n1 - n0) / (np.hypot(*(n1 - n0)) or 1); v = np.array([-u[1], u[0]])
    if v[0] > 0: v = -v
    cc = n0 + (n1 - n0) * 0.45
    pc = [P(body, C['dog'], 10, 'body', 'bodyP', 0.5),
          P(ellipse(6, H + 8, 20, 5), C['dog_saddle'], 11, 'saddle', 'saddleP', outline=False),
          P(ellipse(-30, H - 5, 6, 8), C['dog_cream'], 12, 'blaze', 'blazeP', outline=False),
          P(capsule(n0, n1, 16, 15), C['dog'], 15, 'neck', 'neckP', 0.3),
          P(capsule(cc + v * 7.8, cc - v * 7.8, 4.2), C['collar'], 16, 'collar', 'collarP', 0.15),
          P(ellipse(*(cc + v * 7.0 - u * 3.5), 2.6, 2.8, n=10), C['tag'], 17, 'tag', 'tagP', 0.1)]
    return pc, (NECK[0], H + NECK[1])


def body_stand_Q(H):
    pc = [P(ellipse(10, H + 1, 21, 13), C['dog'], 6, 'body', 'bodyQ', 0.5),
          P(ellipse(10, H + 9, 13, 4.2), C['dog_saddle'], 7, 'saddle', 'saddleQ', outline=False),
          P(capsule((16, H - 6), (17, 3), 9, 6.5), C['dog_far'], 5, 'leg', 'qhf'),
          P(ellipse(16, 2.6, 5.2, 3.0), C['dog_far'], 5.5, 'paw', 'qhfp'),
          P(capsule((25, H - 5), (26, 3), 11, 7), C['dog'], 8, 'leg', 'qhn'),
          P(ellipse(25, 2.6, 5.5, 3.0), C['dog'], 8.5, 'paw', 'qhnp'),
          P(capsule((-3, H - 8), (-2, 3), 8, 6.5), C['dog_far'], 9, 'leg', 'qff'),
          P(ellipse(-3, 2.6, 5.0, 3.1), C['dog_far'], 9.5, 'paw', 'qffp'),
          P(ellipse(-10, H - 1, 15, 16), C['dog'], 10, 'body', 'chestQ', 0.5),
          P(ellipse(-13, H - 4, 7, 10), C['dog_cream'], 11, 'blaze', 'blazeQ', outline=False),
          P(capsule((-17, H - 8), (-18, 3), 8.5, 7), C['dog'], 14, 'leg', 'qfn'),
          P(ellipse(-19, 2.7, 5.4, 3.2), C['dog'], 14.5, 'paw', 'qfnp'),
          P(capsule((-22, H + 9), (-2, H + 11), 4.4), C['collar'], 16, 'collar', 'collarQ', 0.15),
          P(ellipse(-12, H + 6.2, 2.6, 2.8, n=10), C['tag'], 17, 'tag', 'tagQ', 0.1)]
    return pc, (-12.0, H + 10.0)


def body_stand_F(H):
    pc = [P(ellipse(0, H + 2, 21, 12), C['dog_far'], 5, 'body', 'haunchF', 0.5),
          P(ellipse(-15, 2.6, 5, 3), C['dog_far'], 5.5, 'paw', 'fhl'),
          P(ellipse(15, 2.6, 5, 3), C['dog_far'], 5.5, 'paw', 'fhr'),
          P(ellipse(0, H - 2, 15, 17), C['dog'], 10, 'body', 'chestF', 0.5),
          P(ellipse(0, H - 5, 7, 11), C['dog_cream'], 11, 'blaze', 'blazeF', outline=False),
          P(capsule((-8, H - 12), (-9, 3), 8.5, 7), C['dog'], 14, 'leg', 'ffl'),
          P(capsule((8, H - 12), (9, 3), 8.5, 7), C['dog'], 14, 'leg', 'ffr'),
          P(ellipse(-9.5, 2.8, 5.2, 3.2), C['dog'], 14.5, 'paw', 'fflp'),
          P(ellipse(9.5, 2.8, 5.2, 3.2), C['dog'], 14.5, 'paw', 'ffrp'),
          P(capsule((-11, H + 9), (11, H + 9), 4.4), C['collar'], 16, 'collar', 'collarF', 0.15),
          P(ellipse(0, H + 5.6, 2.6, 2.8, n=10), C['tag'], 17, 'tag', 'tagF', 0.1)]
    return pc, (0.0, H + 10.0)


def body_lie_P():
    body = hull(np.vstack([ellipse(4, 13, 32, 11.5, n=30), ellipse(-22, 15, 13, 13, n=24)]))
    pc = [P(capsule((-18, 7.5), (-50, 4.0), 7.0, 6.5), C['dog_far'], 2, 'leg', 'lff'),
          P(ellipse(-53, 4.0, 5.6, 3.0), C['dog_far'], 2.5, 'paw', 'lffp'),
          P(body, C['dog'], 10, 'body', 'bodyL', 0.5),
          P(ellipse(8, 20.5, 20, 4.2), C['dog_saddle'], 11, 'saddle', 'saddleL', outline=False),
          P(ellipse(-30, 12, 5, 7), C['dog_cream'], 12, 'blaze', 'blazeL', outline=False),
          P(ellipse(20, 12, 13, 9.5), C['dog'], 13, 'haunch', 'haunchL', 0.3),
          P(capsule((18, 5.5), (4, 3.6), 6.5, 6), C['dog'], 13.5, 'leg', 'lhock'),
          P(ellipse(2, 3.4, 6, 3.2), C['dog'], 13.8, 'paw', 'lhp'),
          P(capsule((-22, 8.5), (-46, 3.8), 7.5, 6.8), C['dog'], 14, 'leg', 'lfn'),
          P(ellipse(-49, 3.6, 5.8, 3.2), C['dog'], 14.5, 'paw', 'lfnp'),
          P(capsule((-20, 17), (-28, 27), 15, 14), C['dog'], 15, 'neck', 'neckL', 0.3),
          P(capsule((-33.0, 20.5), (-19.5, 26.5), 4.2), C['collar'], 16, 'collar', 'collarL', 0.15),
          P(ellipse(-30, 17.5, 2.6, 2.8, n=10), C['tag'], 17, 'tag', 'tagL', 0.1)]
    return pc, (-29.0, 27.0)


def build(pose):
    """pose: dict(body P|Q|F, draw STAND|LIE, mirror, H, feet, head_view, head_mirror, head_stop, ear, eye, brow, gaze, tail)
    returns (pieces in the figure frame, facing left unless mirror), sorted by z."""
    draw = pose.get('draw', 'STAND'); view = pose.get('body', 'P'); H = pose.get('H', H_STAND)
    if draw == 'LIE':
        pcs, neck = body_lie_P()
        pcs += tail_pieces((34, 13), pose.get('tail', -4), 9, lie=True)
    elif view == 'P':
        hs = HEAD_STOPS[pose.get('head_stop', 'UP')] if pose.get('head_view', 'P') == 'P' and not pose.get('head_mirror') else (0, 0, 0)
        pcs, neck = body_stand_P(H, hs[:2])
        pcs += legs_profile(H, pose['feet'], True) + legs_profile(H, pose['feet'], False)
        pcs += tail_pieces((30, H + 6), pose.get('tail', 30), 9)
    elif view == 'Q':
        pcs, neck = body_stand_Q(H)
        pcs += tail_pieces((22, H + 8), pose.get('tail', 30) + 25, 4)
    else:
        pcs, neck = body_stand_F(H)
        pcs += tail_pieces((14, H + 6), pose.get('tail', 30) * 0.5 + 8, 4)
    hv = pose.get('head_view', 'P')
    hp = head(hv, pose.get('ear', 'PRICK'), pose.get('eye', 'OPEN'), pose.get('brow', 'NEUTRAL'), pose.get('gaze', (-1, 0)))
    stop = pose.get('head_stop', 'UP')
    dx, dy, rot = HEAD_STOPS[stop]
    if hv != 'P': rot = rot * 0.3
    rot += pose.get('tilt', 0.0)
    sx = -1.0 if pose.get('head_mirror') else 1.0
    M = affine(neck[0] + dx * sx, neck[1] + dy, rot * sx) @ np.diag([sx, 1.0, 1.0])
    pcs += apply(hp, M)
    if pose.get('mirror'):
        pcs = apply(pcs, np.diag([-1.0, 1.0, 1.0]))
    pcs.sort(key=lambda p: p.z)
    for p in pcs:
        if p.tag in ('body', 'neck', 'tail') and p.fill == C['dog']: p.grp = 'body'
        elif p.tag in ('skull', 'snout'): p.grp = 'head'
    return pcs


def tail_angle(tail, wag_phase=0.0, wag=0.0):
    """score tail (0 high, 0.5 level, 1.35 tucked) -> profile tail angle in degrees from the tail direction, y up"""
    pts = [(0.0, 62.0), (0.5, 28.0), (1.0, -60.0), (1.35, -118.0)]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if tail <= b:
            u = max(0.0, (tail - a) / (b - a)); ang = va + (vb - va) * u; break
    else:
        ang = pts[-1][1]
    return ang + wag * 28.0 * math.sin(wag_phase)
