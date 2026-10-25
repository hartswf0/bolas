"""SCION 17 // cast: MAREN, the person at the door, cut from construction paper (cast bible v1).

Figure frame: centimetres, y up, origin on the ground at the figure, facing +x (screen right, toward the dog) in a
three-quarter view. She never turns away from the dog in this scene, so one direction state suffices; her change of
circumstance is carried by posture drawings (STAND, CROUCH, SIT), arm pivots solved to a hand target, and her face atlas.

Mouth atlas (phoneme chart in dialogue.py): REST MBP AA EE OH OO CONS S L SMILE
Eyes: OPEN HALF CLOSED; brows: NEUTRAL UP SAD SOFT; head tilt in degrees.
"""
import math
import numpy as np
from kit import PAPER as C, Piece, ellipse, rrect, capsule, handcut, affine, apply, ik2

VERSION = 'maren-v1'
ARM = (29.0, 27.0)       # upper arm, forearm
LEGL = (35.0, 34.0)      # thigh, shin


def P(pts, fill, z, tag, name=None, amp=0.4, outline=True):
    if name: pts = handcut(pts, 'maren.' + name, amp)
    return Piece(pts, fill, z, tag, outline)


def mouth(shape, mx, my, z):
    ink = C['mouth']
    if shape == 'REST':
        return [Piece(capsule((mx - 3.2, my), (mx + 3.2, my + 0.3), 1.3), C['ink'], z, 'mouth', outline=False)]
    if shape == 'SMILE':
        a = np.linspace(math.radians(200), math.radians(340), 9)
        pts = [(mx + 4 * math.cos(t), my + 2.2 + 3 * math.sin(t)) for t in a]
        return [Piece(capsule(pts[i], pts[i + 1], 1.3), C['ink'], z, 'mouth', outline=False) for i in range(len(pts) - 1)]
    if shape == 'MBP':
        return [Piece(capsule((mx - 2.8, my), (mx + 2.8, my), 2.0), C['ink'], z, 'mouth', outline=False)]
    if shape == 'AA':
        return [Piece(ellipse(mx, my - 1.2, 4.0, 3.8, n=14), ink, z, 'mouth'),
                Piece(rrect(mx - 3.0, my + 0.8, mx + 3.0, my + 2.2, 0.6), C['teeth'], z + 0.1, 'teeth', outline=False),
                Piece(ellipse(mx, my - 3.2, 2.4, 1.2, n=10), C['tongue'], z + 0.1, 'tongue', outline=False)]
    if shape == 'EE':
        return [Piece(rrect(mx - 4.6, my - 1.8, mx + 4.6, my + 1.6, 1.5), ink, z, 'mouth'),
                Piece(rrect(mx - 3.8, my + 0.1, mx + 3.8, my + 1.3, 0.4), C['teeth'], z + 0.1, 'teeth', outline=False)]
    if shape == 'OH':
        return [Piece(ellipse(mx, my - 0.6, 2.9, 3.3, n=12), ink, z, 'mouth')]
    if shape == 'OO':
        return [Piece(ellipse(mx, my - 0.2, 2.0, 2.3, n=10), ink, z, 'mouth')]
    if shape == 'CONS':
        return [Piece(rrect(mx - 3.0, my - 1.2, mx + 3.0, my + 1.0, 0.8), ink, z, 'mouth'),
                Piece(rrect(mx - 2.6, my - 0.1, mx + 2.6, my + 0.8, 0.3), C['teeth'], z + 0.1, 'teeth', outline=False)]
    if shape == 'S':
        return [Piece(rrect(mx - 3.4, my - 0.9, mx + 3.4, my + 0.9, 0.8), ink, z, 'mouth'),
                Piece(rrect(mx - 3.0, my - 0.6, mx + 3.0, my + 0.6, 0.3), C['teeth'], z + 0.1, 'teeth', outline=False)]
    if shape == 'L':
        return [Piece(ellipse(mx, my - 0.8, 3.4, 2.8, n=12), ink, z, 'mouth'),
                Piece(ellipse(mx, my + 0.6, 1.8, 1.0, n=8), C['tongue'], z + 0.1, 'tongue', outline=False)]
    return []


def head(eye, brow, mouth_shape, gaze, z0=40):
    pc = []
    pc.append(P(ellipse(-11, 15, 7, 7.5), C['hair'], z0 - 1, 'hair', 'bun', 0.3))              # the bun
    pc.append(P(ellipse(2, 0, 14.5, 17.5, n=26), C['skin'], z0, 'skull', 'face', 0.35))
    pc.append(P(ellipse(-8.5, -1, 3, 4.5), C['skin_far'], z0 + 0.5, 'ear', 'ear', 0.2))
    hair = np.array([(-13, -2), (-14, 8), (-9, 16), (0, 19), (10, 17.5), (16, 10), (15.5, 5), (9, 8), (2, 9), (-4, 6), (-8, 2)], float)
    pc.append(P(hair, C['hair'], z0 + 1, 'hair', 'hair', 0.35))
    pc.append(P(ellipse(16.2, -2.5, 2.2, 3.2), C['skin'], z0 + 2, 'nose', 'nose', 0.15))
    for k, (ex, rx, ry) in enumerate([(3.5, 3.6, 4.6), (12.2, 3.2, 4.4)]):
        ey = 3.0
        pc.append(Piece(ellipse(ex, ey, rx, ry, n=14), C['eye'], z0 + 3, 'eye'))
        if eye != 'CLOSED':
            pr = 1.7
            px = ex + gaze[0] * (rx - pr - 0.3); py = ey + gaze[1] * (ry - pr - 0.5)
            pc.append(Piece(ellipse(px, py, pr, pr * 1.1, n=10), C['pupil'], z0 + 4, 'pupil', outline=False))
        if eye in ('HALF', 'CLOSED'):
            if eye == 'HALF':
                a = np.linspace(0, np.pi, 14)
                top = np.stack([ex + rx * 1.1 * np.cos(a), ey + ry * 1.1 * np.sin(a)], 1)
                cut = ey + 0.4
                top = top[top[:, 1] >= cut]
                lid = np.vstack([[ex + rx * 1.1, cut], top, [ex - rx * 1.1, cut]])
            else:
                a = np.linspace(0, 2 * np.pi, 18, endpoint=False)
                lid = np.stack([ex + rx * 1.1 * np.cos(a), ey + ry * 1.1 * np.sin(a)], 1)
            pc.append(Piece(lid, C['lid_person'], z0 + 5, 'lid'))
            if eye == 'CLOSED':
                pc.append(Piece(capsule((ex - rx * 0.9, ey), (ex + rx * 0.9, ey), 1.0), C['ink'], z0 + 6, 'lash', outline=False))
        b = {'NEUTRAL': (0, 0), 'UP': (1.8, 1.8), 'SAD': (2.0, -0.6), 'SOFT': (0.8, 0.2)}[brow]
        inner, outer = (b[0], b[1]) if k == 0 else (b[0], b[1])
        if k == 0:
            pc.append(Piece(capsule((ex - 3.2, ey + 6.4 + outer), (ex + 3.0, ey + 6.4 + inner), 1.5), C['hair'], z0 + 7, 'brow', outline=False))
        else:
            pc.append(Piece(capsule((ex - 2.8, ey + 6.2 + inner), (ex + 3.0, ey + 6.2 + outer), 1.5), C['hair'], z0 + 7, 'brow', outline=False))
    pc += mouth(mouth_shape, 9.5, -9.5, z0 + 8)
    return pc


def limb(p0, target, lens, bend, w, fill, z, name, tip=None):
    knee, end = ik2(p0, target, lens[0], lens[1], bend)
    out = [P(capsule(p0, knee, w[0], w[1]), fill, z, 'limb', name + '.a', 0.25),
           P(capsule(knee, end, w[1], w[2]), fill, z + 0.1, 'limb', name + '.b', 0.25)]
    return out, end


def build(pose):
    """pose: dict(posture STAND|CROUCH|SIT, pelvis (x,y) cm, lean deg, feet {'n':(x,y),'f':(x,y)},
    hands {'n':(x,y),'f':(x,y)} in the figure frame, tilt deg, eye, brow, mouth, gaze, palm_up)"""
    pc = []
    pel = np.array(pose.get('pelvis', (0, 67)), float); lean = pose.get('lean', 0.0)
    posture = pose.get('posture', 'STAND')
    # torso hangs from the pelvis and leans about it
    T = affine(pel[0], pel[1], -lean)
    torso = np.array([(-21, -4), (21, -4), (21, 40), (17, 56), (4, 60), (-12, 59), (-19, 52), (-21, 40)], float)
    pc.append(P(apply([Piece(torso, C['sweater'], 20, 'torso')], T)[0].pts, C['sweater'], 20, 'torso', 'torso', 0.5))
    hem = np.array([(-21, -4), (21, -4), (21, 3), (-21, 3)], float)
    pc.append(Piece(apply([Piece(hem, C['sweater_far'], 21, 'hem')], T)[0].pts, C['sweater_far'], 21, 'hem', outline=False))
    sh_n = (T @ [12, 52, 1])[:2]; sh_f = (T @ [-13, 52, 1])[:2]; neck = (T @ [2, 60, 1])[:2]
    # legs (figure frame); hips at the pelvis
    hip_n = (T @ [8, 0, 1])[:2]; hip_f = (T @ [-7, 0, 1])[:2]
    feet = pose.get('feet', {'n': (10, 0), 'f': (-8, 0)})
    kb = (1.0, 0.25) if posture != 'SIT' else (0.2, 1.0)
    for side, hip, col, z in (('f', hip_f, C['trousers_far'], 8), ('n', hip_n, C['trousers'], 24)):
        legs, foot = limb(hip, feet[side], LEGL, kb, (15, 12, 10), col, z, 'leg' + side)
        pc += legs
        pc.append(P(ellipse(foot[0] + 5, foot[1] + 3.6, 10.5, 4.6), C['shoe'], z + 0.5, 'shoe', 'shoe' + side, 0.3))
    # arms: shoulders on the torso, hands at targets
    hands = pose.get('hands', {'n': (sh_n[0] + 4, sh_n[1] - 54), 'f': (sh_f[0] - 2, sh_f[1] - 54)})
    for side, sh, col, skin, z in (('f', sh_f, C['sweater_far'], C['skin_far'], 6), ('n', sh_n, C['sweater'], C['skin'], 30)):
        arm, hand = limb(sh, hands[side], ARM, (-0.3, -1.0), (11, 9, 8), col, z, 'arm' + side)
        pc += arm
        if pose.get('palm_up') and side == 'n':
            pc.append(P(ellipse(hand[0] + 4, hand[1] + 0.5, 7.0, 3.6), skin, z + 0.5, 'hand', 'palm', 0.25))
            pc.append(P(ellipse(hand[0] + 1, hand[1] + 3.6, 2.2, 1.8), skin, z + 0.6, 'thumb', 'thumb', 0.1))
        else:
            pc.append(P(ellipse(hand[0], hand[1] - 1.5, 4.8, 6.0), skin, z + 0.5, 'hand', 'mitt' + side, 0.25))
    pc.append(P(capsule((neck[0] - 1, neck[1] - 4), (neck[0] + 1, neck[1] + 8), 10, 9), C['skin'], 19, 'neck', 'neck', 0.2))
    # head on the neck, tilted
    hd = head(pose.get('eye', 'OPEN'), pose.get('brow', 'NEUTRAL'), pose.get('mouth', 'REST'), pose.get('gaze', (1, 0)))
    HS = 1.4                                   # cut-out proportion: a big readable face on an adult body
    H = affine(neck[0] + 1, neck[1] + 16 * HS, -lean * 0.6 + pose.get('tilt', 0.0), sx=HS, sy=HS)
    pc += apply(hd, H)
    pc.sort(key=lambda p: p.z)
    for p in pc:
        if p.tag == 'skull': p.grp = 'face'
    return pc, dict(head=(H @ [2, 0, 1])[:2], hand_n=hands['n'])
