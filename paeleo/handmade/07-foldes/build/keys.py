"""SCION 07 (Foldès) · KEY CONTOUR DRAWINGS.

Every drawing here was drawn by hand as coordinates (metres, y up), by this swarm's key-image draughtsperson, with proportions
studied from the archive dog's SAM outline in kit/archive-dog frame f008 (a collie-like dog in profile, head low): body length
~1.25x withers height, long legs, deep chest, bushy low tail. Nothing is traced pixel-for-pixel; the outline was read, then
redrawn as named contour points.

A key is a set of NAMED strokes with a FIXED number of points. The index of a point is its correspondence: point i of `body`
in one key is the same anatomical place as point i of `body` in every other key (0 neck top, 1 withers, 2 back, 3 loin,
4 croup, 5 rump, 6 back of thigh, 7 groin, 8 belly, 9 brisket, 10 chest front, 11 throat). Limbs are centrelines
(top, joint, joint, paw) with widths. In-betweens are made by interpolating corresponding points (solve.py).

Dog body group keys are drawn facing LEFT (toward the door). Facing right is the mirror image WITH the dog's left and right
swapped (after a 180 degree turn the camera sees the dog's other side): mirror() negates x and swaps L/R stroke names.
Two keys are drawn left-right symmetric on purpose (rearA, frontA): at those keys the correspondence set is substituted by
its mirror (a declared discontinuity, invisible because the shape is the same point set). That is how a flat drawing turns
through 180 degrees without collapsing edge-on.

Writes ../keys/dog_keys.json and ../keys/person_keys.json (the key drawing set, canonical)."""
import json, math, os, copy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'keys')

FW = [0.085, 0.062, 0.046, 0.05]     # fore-leg widths (top..paw)
HW = [0.13, 0.08, 0.05, 0.05]        # hind-leg widths
TW = [0.06, 0.075, 0.075, 0.06, 0.02]  # bushy tail widths


def limb(pts, w, a=1.0, k=1.0, z=6):
    return {'type': 'limb', 'pts': [list(p) for p in pts], 'w': list(w), 'a': a, 'k': k, 'z': z}


def closed(pts, a=1.0, k=1.0, z=5, fill=True):
    return {'type': 'closed', 'pts': [list(p) for p in pts], 'a': a, 'k': k, 'z': z, 'fill': fill}


def opn(pts, a=1.0, k=1.0, z=9):
    return {'type': 'open', 'pts': [list(p) for p in pts], 'a': a, 'k': k, 'z': z}


def ring(cx, cy, rx, ry, n=12, start=105, wob=None):
    """symmetric ring of n points at angles start - 360k/n (so the set is its own mirror)."""
    out = []
    for k in range(n):
        th = math.radians(start - 360.0 * k / n)
        f = 1.0 if wob is None else wob(th)
        out.append((round(cx + rx * f * math.cos(th), 4), round(cy + ry * f * math.sin(th), 4)))
    return out


# ------------------------------------------------------------------------------------------------ dog BODY group (facing L)
def body_key(body, RF, LF, RH, LH, tail, neck=1.0, fwd=-1.0, tail_hi=None, tail_tuck=None, z=None):
    k = {'body': closed(body, z=5), 'RF': RF, 'LF': LF, 'RH': RH, 'LH': LH, 'tail': tail,
         '_neck_attach': neck, '_fwd': fwd}
    if tail_hi: k['_tail_hi'] = tail_hi
    if tail_tuck: k['_tail_tuck'] = tail_tuck
    return k


NEAR, FAR = dict(a=1.0, k=1.0, z=4.5), dict(a=1.0, k=0.6, z=1)

stand = body_key(
    [(-0.45, 0.76), (-0.22, 0.60), (0.0, 0.575), (0.2, 0.575), (0.34, 0.55), (0.425, 0.47), (0.405, 0.335),
     (0.27, 0.275), (0.05, 0.265), (-0.22, 0.225), (-0.42, 0.37), (-0.55, 0.65)],
    limb([(-0.26, 0.36), (-0.265, 0.22), (-0.275, 0.07), (-0.295, 0.0)], FW, **NEAR),
    limb([(-0.18, 0.36), (-0.175, 0.22), (-0.185, 0.07), (-0.205, 0.0)], FW, **FAR),
    limb([(0.28, 0.42), (0.21, 0.24), (0.33, 0.10), (0.31, 0.0)], HW, **NEAR),
    limb([(0.21, 0.42), (0.14, 0.24), (0.26, 0.10), (0.24, 0.0)], HW, **FAR),
    limb([(0.375, 0.525), (0.49, 0.48), (0.56, 0.40), (0.585, 0.31), (0.63, 0.245)], TW, z=2),
    tail_hi=[(0.375, 0.535), (0.49, 0.59), (0.59, 0.59), (0.66, 0.54), (0.70, 0.48)],
    tail_tuck=[(0.39, 0.50), (0.42, 0.40), (0.38, 0.30), (0.30, 0.24), (0.22, 0.22)])

crouch = body_key(
    [(-0.45, 0.62), (-0.22, 0.50), (0.0, 0.485), (0.2, 0.48), (0.34, 0.445), (0.415, 0.365), (0.39, 0.245),
     (0.25, 0.195), (0.05, 0.19), (-0.22, 0.16), (-0.42, 0.29), (-0.55, 0.52)],
    limb([(-0.26, 0.29), (-0.3, 0.17), (-0.275, 0.065), (-0.31, 0.0)], FW, **NEAR),
    limb([(-0.18, 0.29), (-0.22, 0.17), (-0.185, 0.065), (-0.22, 0.0)], FW, **FAR),
    limb([(0.27, 0.33), (0.16, 0.19), (0.35, 0.085), (0.32, 0.0)], HW, **NEAR),
    limb([(0.20, 0.33), (0.09, 0.19), (0.28, 0.085), (0.25, 0.0)], HW, **FAR),
    limb([(0.37, 0.43), (0.44, 0.34), (0.41, 0.25), (0.33, 0.18), (0.24, 0.16)], TW, z=2),
    tail_hi=[(0.37, 0.44), (0.49, 0.43), (0.57, 0.37), (0.6, 0.29), (0.62, 0.22)],
    tail_tuck=[(0.37, 0.42), (0.41, 0.32), (0.37, 0.23), (0.29, 0.17), (0.21, 0.15)])

lie = body_key(
    [(-0.414, 0.50), (-0.230, 0.40), (0.000, 0.365), (0.202, 0.365), (0.350, 0.335), (0.451, 0.25), (0.432, 0.10),
     (0.276, 0.035), (0.046, 0.045), (-0.230, 0.055), (-0.396, 0.18), (-0.506, 0.42)],
    limb([(-0.276, 0.19), (-0.340, 0.05), (-0.534, 0.035), (-0.635, 0.02)], [0.085, 0.06, 0.048, 0.05], **NEAR),
    limb([(-0.202, 0.19), (-0.285, 0.06), (-0.478, 0.045), (-0.580, 0.03)], [0.085, 0.06, 0.048, 0.05], **FAR),
    limb([(0.285, 0.23), (0.129, 0.12), (0.340, 0.04), (0.212, 0.02)], [0.15, 0.08, 0.05, 0.05], **NEAR),
    limb([(0.230, 0.23), (0.092, 0.12), (0.276, 0.05), (0.156, 0.03)], [0.15, 0.08, 0.05, 0.05], a=1.0, k=0.5, z=1),
    limb([(0.405, 0.22), (0.524, 0.12), (0.644, 0.055), (0.764, 0.035), (0.874, 0.04)], TW, z=2),
    tail_hi=[(0.405, 0.23), (0.534, 0.16), (0.662, 0.10), (0.782, 0.08), (0.892, 0.10)],
    tail_tuck=[(0.405, 0.21), (0.506, 0.09), (0.607, 0.04), (0.699, 0.025), (0.791, 0.025)])

# the refusal closes: the body draws in to a tight curl, the tail wrapped round in front of the paws, the head tucked
curl = body_key(
    [(-0.36, 0.30), (-0.17, 0.39), (0.03, 0.43), (0.2, 0.41), (0.32, 0.34), (0.39, 0.22), (0.37, 0.08),
     (0.23, 0.03), (0.02, 0.04), (-0.19, 0.045), (-0.31, 0.13), (-0.40, 0.22)],
    limb([(-0.22, 0.15), (-0.29, 0.045), (-0.42, 0.03), (-0.5, 0.02)], [0.08, 0.058, 0.046, 0.05], **NEAR),
    limb([(-0.16, 0.15), (-0.24, 0.05), (-0.37, 0.035), (-0.45, 0.025)], [0.08, 0.058, 0.046, 0.05], **FAR),
    limb([(0.26, 0.21), (0.1, 0.12), (0.29, 0.04), (0.17, 0.02)], [0.15, 0.08, 0.05, 0.05], **NEAR),
    limb([(0.21, 0.21), (0.07, 0.12), (0.24, 0.05), (0.12, 0.03)], [0.15, 0.08, 0.05, 0.05], a=1.0, k=0.5, z=1),
    limb([(0.37, 0.2), (0.43, 0.08), (0.3, 0.025), (0.02, 0.015), (-0.3, 0.035)], [0.06, 0.075, 0.07, 0.06, 0.02], z=7),
    neck=1.0, fwd=-1.0)

# 3/4 from behind, still turned toward the left: the rump comes nearer and rounds, the head goes small and away
rear34L = body_key(
    [(-0.30, 0.70), (-0.18, 0.60), (-0.03, 0.58), (0.12, 0.57), (0.21, 0.55), (0.30, 0.48), (0.31, 0.32),
     (0.20, 0.25), (0.0, 0.27), (-0.18, 0.25), (-0.30, 0.38), (-0.38, 0.60)],
    limb([(-0.22, 0.38), (-0.23, 0.23), (-0.23, 0.075), (-0.245, 0.0)], FW, a=1.0, k=0.9, z=4.4),
    limb([(-0.13, 0.36), (-0.13, 0.23), (-0.13, 0.075), (-0.14, 0.0)], FW, a=1.0, k=0.5, z=1),
    limb([(0.19, 0.42), (0.17, 0.23), (0.235, 0.10), (0.22, 0.0)], [0.14, 0.085, 0.055, 0.055], **NEAR),
    limb([(0.04, 0.42), (0.03, 0.23), (0.07, 0.10), (0.06, 0.0)], [0.12, 0.08, 0.05, 0.05], a=1.0, k=0.8, z=4.3),
    limb([(0.24, 0.51), (0.30, 0.43), (0.30, 0.33), (0.27, 0.25), (0.235, 0.19)], TW, z=7),
    neck=0.6, fwd=-0.5)

# directly from behind: drawn symmetric (its own mirror); the head is behind the shoulders, only its back and ears show
rearA = body_key(
    ring(0.0, 0.42, 0.20, 0.20, wob=lambda th: 1.0 + 0.10 * math.sin(th) ** 2 * (1 if math.sin(th) > 0 else -0.4)),
    limb([(-0.075, 0.30), (-0.075, 0.20), (-0.075, 0.07), (-0.075, 0.0)], FW, a=1.0, k=0.5, z=1),
    limb([(0.075, 0.30), (0.075, 0.20), (0.075, 0.07), (0.075, 0.0)], FW, a=1.0, k=0.5, z=1),
    limb([(0.095, 0.36), (0.125, 0.22), (0.115, 0.09), (0.115, 0.0)], [0.10, 0.08, 0.055, 0.055], **NEAR),
    limb([(-0.095, 0.36), (-0.125, 0.22), (-0.115, 0.09), (-0.115, 0.0)], [0.10, 0.08, 0.055, 0.055], **NEAR),
    limb([(0.0, 0.53), (0.012, 0.44), (0.008, 0.34), (-0.004, 0.25), (0.0, 0.185)], TW, z=7),
    neck=0.0, fwd=0.0)

# 3/4 from the front, turned toward the left: the chest comes nearer, both forelegs show, the rump goes behind
front34L = body_key(
    [(-0.40, 0.72), (-0.17, 0.60), (0.0, 0.57), (0.15, 0.56), (0.25, 0.54), (0.30, 0.47), (0.28, 0.35),
     (0.18, 0.29), (0.0, 0.28), (-0.20, 0.24), (-0.36, 0.36), (-0.48, 0.62)],
    limb([(-0.26, 0.38), (-0.27, 0.24), (-0.27, 0.075), (-0.29, 0.0)], FW, **NEAR),
    limb([(-0.13, 0.36), (-0.13, 0.23), (-0.13, 0.075), (-0.145, 0.0)], FW, a=1.0, k=0.85, z=4.3),
    limb([(0.22, 0.42), (0.18, 0.23), (0.27, 0.10), (0.25, 0.0)], HW, a=1.0, k=0.8, z=4.2),
    limb([(0.14, 0.40), (0.11, 0.23), (0.19, 0.10), (0.17, 0.0)], HW, a=1.0, k=0.5, z=1),
    limb([(0.28, 0.50), (0.38, 0.48), (0.45, 0.43), (0.48, 0.36), (0.51, 0.30)], TW, z=2),
    neck=0.7, fwd=-0.6)

# directly from the front: symmetric; chest and both forelegs, the hind paws just showing behind
frontA = body_key(
    ring(0.0, 0.45, 0.19, 0.175, wob=lambda th: 1.0 + 0.08 * math.sin(th) ** 2),
    limb([(-0.085, 0.36), (-0.09, 0.22), (-0.085, 0.075), (-0.09, 0.0)], FW, **NEAR),
    limb([(0.085, 0.36), (0.09, 0.22), (0.085, 0.075), (0.09, 0.0)], FW, **NEAR),
    limb([(-0.14, 0.30), (-0.15, 0.18), (-0.15, 0.07), (-0.15, 0.0)], [0.11, 0.08, 0.05, 0.05], a=1.0, k=0.5, z=1),
    limb([(0.14, 0.30), (0.15, 0.18), (0.15, 0.07), (0.15, 0.0)], [0.11, 0.08, 0.05, 0.05], a=1.0, k=0.5, z=1),
    limb([(0.12, 0.50), (0.22, 0.55), (0.29, 0.56), (0.34, 0.53), (0.37, 0.48)], TW, a=0.9, k=0.7, z=0),
    neck=0.0, fwd=0.0)

# ------------------------------------------------------------------------------------------------ dog HEAD group (head-local)
# 10-point head outline: 0 back-top of skull, 1 crown, 2 forehead/stop, 3 muzzle top, 4 nose tip, 5 under the nose,
# 6 jaw, 7 throat under the jaw, 8 cheek/back of the jaw, 9 back of the head. Ears 4 points: base front, tip, tip back, base back.
def head_key(head, earR, earL, eyeR, eyeL, nose, mouth, gaze, earRz=1, earLz=-1, eyeRa=1.0, eyeLa=0.0, mouth_a=0.8):
    return {'head': closed(head, z=8), 'earR': closed(earR, z=8 + earRz * 0.5), 'earL': closed(earL, z=8 + earLz * 0.5),
            'eyeR': opn(eyeR, a=eyeRa, k=2.4, z=9), 'eyeL': opn(eyeL, a=eyeLa, k=2.4, z=9),
            'nose': opn(nose, k=3.2, z=9), 'mouth': opn(mouth, a=mouth_a, k=0.6, z=9), '_gaze': gaze}


profile = head_key(
    [(0.095, 0.065), (0.02, 0.112), (-0.07, 0.092), (-0.17, 0.042), (-0.238, 0.008), (-0.228, -0.035), (-0.13, -0.066),
     (-0.02, -0.082), (0.08, -0.062), (0.118, 0.0)],
    [(-0.012, 0.095), (0.0, 0.215), (0.045, 0.2), (0.07, 0.075)],
    [(0.035, 0.1), (0.055, 0.21), (0.09, 0.19), (0.1, 0.065)],
    [(-0.058, 0.036), (-0.079, 0.031)], [(-0.04, 0.04), (-0.05, 0.04)],
    [(-0.233, 0.004), (-0.22, 0.002)], [(-0.215, -0.032), (-0.15, -0.038), (-0.1, -0.026)], gaze=-1.0)

# 3/4 front, looking toward the left and the camera: both eyes, the muzzle foreshortened
front34 = head_key(
    [(0.08, 0.07), (0.0, 0.112), (-0.075, 0.09), (-0.13, 0.035), (-0.165, -0.008), (-0.155, -0.048), (-0.085, -0.082),
     (0.0, -0.092), (0.075, -0.065), (0.1, 0.0)],
    [(-0.07, 0.08), (-0.075, 0.2), (-0.03, 0.19), (-0.005, 0.085)],
    [(0.03, 0.09), (0.06, 0.205), (0.1, 0.18), (0.095, 0.06)],
    [(-0.075, 0.03), (-0.092, 0.027)], [(0.0, 0.034), (0.018, 0.032)],
    [(-0.162, -0.004), (-0.146, -0.006)], [(-0.15, -0.045), (-0.1, -0.06), (-0.05, -0.05)], gaze=-0.75,
    earLz=1, eyeLa=1.0)

# 3/4 from behind, the head turned away into the picture and to the left: back of the skull, both ears, no eyes
rear34 = head_key(
    [(0.085, 0.075), (0.0, 0.12), (-0.07, 0.108), (-0.125, 0.075), (-0.155, 0.055), (-0.15, 0.03), (-0.1, -0.01),
     (-0.03, -0.072), (0.07, -0.068), (0.11, -0.008)],
    [(0.035, 0.1), (0.065, 0.225), (0.105, 0.205), (0.11, 0.07)],
    [(-0.065, 0.105), (-0.06, 0.225), (-0.02, 0.215), (-0.005, 0.11)],
    [(-0.135, 0.06), (-0.142, 0.058)], [(-0.05, 0.05), (-0.05, 0.05)],
    [(-0.155, 0.05), (-0.15, 0.048)], [(-0.12, 0.0), (-0.1, -0.01), (-0.08, -0.02)], gaze=-0.4,
    earRz=1, earLz=1, eyeRa=0.0, eyeLa=0.0, mouth_a=0.0)

# directly from behind: the round back of the head and two ears; symmetric (its own mirror)
def head_ring(r=0.095, cy=0.01):
    """symmetric head ring in the same winding as the profile head: 0 back-top, 1 crown ... 4 at the left (nose side)."""
    return [(round(r * math.cos(math.radians(a)), 4), round(cy + r * math.sin(math.radians(a)), 4))
            for a in (54, 90, 126, 162, 198, 234, 270, 306, 342, 18)]


rearH = head_key(
    head_ring(),
    [(0.03, 0.075), (0.06, 0.2), (0.1, 0.185), (0.1, 0.045)],
    [(-0.1, 0.045), (-0.1, 0.185), (-0.06, 0.2), (-0.03, 0.075)],
    [(-0.05, 0.0), (-0.05, 0.0)], [(0.05, 0.0), (0.05, 0.0)],
    [(0.0, -0.02), (0.0, -0.02)], [(0.0, -0.03), (0.0, -0.03), (0.0, -0.03)], gaze=0.0,
    earRz=1, earLz=1, eyeRa=0.0, eyeLa=0.0, mouth_a=0.0)
# straight at the camera: symmetric, both eyes, the nose in the middle (the substitution point of the head's return turn)
frontH = head_key(
    [(0.06, 0.08), (0.0, 0.1), (-0.06, 0.08), (-0.09, 0.03), (-0.08, -0.03), (-0.05, -0.075), (0.0, -0.09),
     (0.05, -0.075), (0.08, -0.03), (0.09, 0.03)],
    [(-0.1, 0.05), (-0.1, 0.19), (-0.06, 0.2), (-0.03, 0.08)],
    [(0.03, 0.08), (0.06, 0.2), (0.1, 0.19), (0.1, 0.05)],
    [(-0.038, 0.022), (-0.03, 0.02)], [(0.03, 0.02), (0.038, 0.022)],
    [(-0.008, -0.04), (0.008, -0.04)], [(-0.025, -0.07), (0.0, -0.075), (0.025, -0.07)], gaze=0.0,
    earRz=1, earLz=1, eyeRa=1.0, eyeLa=1.0, mouth_a=0.6)
rearH['nose']['a'] = 0.0
for _n in ('head', 'earR', 'earL', 'eyeR', 'eyeL', 'nose', 'mouth'):
    rearH[_n]['z'] -= 5.0   # from behind, the head is behind the shoulders


# ------------------------------------------------------------------------------------------------ person (facing right)
# head 8 pts, coat 10 pts closed, limbs: armN armF legN legF (shoulder/hip, elbow/knee, wrist/ankle, hand/toe)
def person_key(head, coat, armN, armF, legN, legF, mouth, eye, hair):
    AW, LW = [0.09, 0.075, 0.06, 0.07], [0.15, 0.11, 0.08, 0.09]
    return {'hair': closed(hair, z=3.5, k=0.9), 'head': closed(head, z=4), 'coat': closed(coat, z=3),
            'armF': limb(armF, AW, a=0.9, k=0.7, z=1), 'legF': limb(legF, LW, a=0.9, k=0.7, z=0.5),
            'legN': limb(legN, LW, z=2), 'armN': limb(armN, AW, z=5),
            'mouth': opn(mouth, k=1.2, z=6), 'eye': opn(eye, k=2.2, z=6)}


def P_head(cx, cy, tilt=0.0, mouth_open=0.0):
    c, s = math.cos(tilt), math.sin(tilt)
    def T(x, y): return (round(cx + c * x - s * y, 4), round(cy + s * x + c * y, 4))
    head = [T(*p) for p in [(-0.08, 0.09), (0.02, 0.125), (0.1, 0.07), (0.115, 0.0), (0.105, -0.06), (0.06, -0.115),
                            (-0.03, -0.11), (-0.09, -0.02)]]
    hair = [T(*p) for p in [(-0.11, 0.06), (-0.02, 0.15), (0.09, 0.12), (0.12, 0.05), (0.05, 0.08), (-0.04, 0.06),
                            (-0.1, -0.06), (-0.12, -0.0)]]
    mo = mouth_open
    mouth = [T(0.08, -0.06 + 0.01 * mo), T(0.1, -0.065 - 0.02 * mo), T(0.075, -0.07 - 0.03 * mo)]
    eye = [T(0.07, 0.015), T(0.085, 0.012)]
    return head, hair, mouth, eye


def P(cx, cy, tilt, mo, coat, armN, armF, legN, legF):
    h, hair, m, e = P_head(cx, cy, tilt, mo)
    return person_key(h, coat, armN, armF, legN, legF, m, e, hair)


COAT_STAND = [(-0.06, 1.47), (0.07, 1.47), (0.17, 1.38), (0.18, 1.0), (0.2, 0.55), (0.02, 0.5), (-0.2, 0.55),
              (-0.17, 1.0), (-0.16, 1.38), (-0.12, 1.45)]
LEGS_STAND = ([(0.05, 0.55), (0.06, 0.3), (0.06, 0.06), (0.16, 0.0)], [(-0.06, 0.55), (-0.07, 0.3), (-0.07, 0.06), (0.03, 0.0)])

person = {
    'stand': P(0.02, 1.6, 0.0, 0.0, COAT_STAND,
               [(0.1, 1.38), (0.14, 1.12), (0.13, 0.9), (0.14, 0.8)], [(-0.1, 1.38), (-0.14, 1.12), (-0.13, 0.9), (-0.13, 0.8)],
               *LEGS_STAND),
    'call': P(0.06, 1.59, -0.12, 1.0,
              [(-0.04, 1.47), (0.1, 1.46), (0.2, 1.37), (0.2, 1.0), (0.21, 0.55), (0.03, 0.5), (-0.19, 0.55), (-0.16, 1.0),
               (-0.14, 1.38), (-0.1, 1.45)],
              [(0.12, 1.38), (0.24, 1.22), (0.22, 1.42), (0.18, 1.52)], [(-0.1, 1.38), (-0.15, 1.12), (-0.14, 0.9), (-0.14, 0.8)],
              *LEGS_STAND),
    # the reach: the torso bends and the near arm is drawn LONG (1.6x): the command distorts the figure toward the dog
    'reach': P(0.3, 1.42, -0.3, 1.0,
               [(0.13, 1.33), (0.27, 1.28), (0.34, 1.16), (0.27, 0.85), (0.22, 0.5), (0.04, 0.48), (-0.16, 0.55),
                (-0.1, 0.95), (0.0, 1.25), (0.06, 1.31)],
               [(0.3, 1.25), (0.68, 1.12), (1.06, 0.98), (1.2, 0.93)], [(0.05, 1.25), (-0.06, 1.02), (-0.1, 0.84), (-0.11, 0.76)],
               [(0.08, 0.52), (0.14, 0.3), (0.12, 0.06), (0.22, 0.0)], [(-0.07, 0.53), (-0.1, 0.3), (-0.1, 0.06), (0.0, 0.0)]),
    'side': P(0.0, 1.6, 0.05, 0.0, COAT_STAND,
              [(0.1, 1.38), (0.15, 1.12), (0.14, 0.9), (0.15, 0.8)], [(-0.1, 1.38), (-0.15, 1.12), (-0.15, 0.9), (-0.15, 0.8)],
              [(0.05, 0.55), (0.1, 0.3), (0.17, 0.08), (0.27, 0.03)], [(-0.06, 0.55), (-0.14, 0.3), (-0.19, 0.06), (-0.1, 0.0)]),
    'lower': P(0.05, 1.18, 0.1, 0.0,
               [(-0.08, 1.06), (0.05, 1.07), (0.15, 0.98), (0.17, 0.7), (0.3, 0.5), (0.1, 0.36), (-0.2, 0.36), (-0.18, 0.7),
                (-0.17, 0.97), (-0.13, 1.04)],
               [(0.08, 0.98), (0.2, 0.8), (0.3, 0.66), (0.35, 0.6)], [(-0.1, 0.98), (-0.12, 0.75), (-0.05, 0.58), (0.0, 0.55)],
               [(0.05, 0.45), (0.34, 0.42), (0.3, 0.06), (0.4, 0.0)], [(-0.08, 0.42), (0.22, 0.38), (0.18, 0.06), (0.28, 0.0)]),
    # seated on the porch floor against the wall beside the door, knees up, facing the dog
    'sit': P(-0.04, 0.98, 0.12, 0.0,
             [(-0.16, 0.86), (-0.03, 0.88), (0.06, 0.8), (0.08, 0.5), (0.1, 0.18), (-0.06, 0.03), (-0.26, 0.05), (-0.26, 0.4),
              (-0.24, 0.75), (-0.2, 0.84)],
             [(0.0, 0.8), (0.13, 0.6), (0.27, 0.5), (0.33, 0.47)], [(-0.18, 0.8), (-0.16, 0.6), (0.0, 0.5), (0.05, 0.48)],
             [(0.0, 0.12), (0.28, 0.44), (0.47, 0.08), (0.57, 0.02)], [(-0.12, 0.1), (0.18, 0.42), (0.38, 0.07), (0.48, 0.01)]),
    # the low hand: the near arm goes down and out along the boards, palm up
    'low': P(0.0, 0.95, 0.28, 0.0,
             [(-0.14, 0.85), (-0.01, 0.87), (0.08, 0.79), (0.1, 0.5), (0.1, 0.18), (-0.06, 0.03), (-0.26, 0.05), (-0.26, 0.4),
              (-0.23, 0.74), (-0.19, 0.83)],
             [(0.04, 0.78), (0.3, 0.42), (0.6, 0.12), (0.72, 0.09)], [(-0.16, 0.78), (-0.14, 0.58), (0.0, 0.5), (0.05, 0.48)],
             [(0.0, 0.12), (0.3, 0.42), (0.48, 0.08), (0.58, 0.02)], [(-0.12, 0.1), (0.2, 0.4), (0.39, 0.07), (0.49, 0.01)]),
}
person['soft'] = copy.deepcopy(person['low'])
_h, _hair, _m, _e = P_head(0.02, 0.94, 0.36, 0.45)
person['soft']['mouth']['pts'] = [list(p) for p in _m]
person['soft']['head']['pts'] = [list(p) for p in _h]
person['soft']['hair']['pts'] = [list(p) for p in _hair]
person['soft']['eye']['pts'] = [list(p) for p in _e]


# ------------------------------------------------------------------------------------------------ mirror
SWAP = {'RF': 'LF', 'LF': 'RF', 'RH': 'LH', 'LH': 'RH', 'earR': 'earL', 'earL': 'earR', 'eyeR': 'eyeL', 'eyeL': 'eyeR'}


def mirror(key):
    out = {}
    for name, s in key.items():
        nn = SWAP.get(name, name)
        if name.startswith('_'):
            if isinstance(s, list):
                out[nn] = [[-p[0], p[1]] for p in s]
            elif name in ('_fwd', '_gaze'):
                out[nn] = -s
            else:
                out[nn] = s
            continue
        s2 = copy.deepcopy(s)
        s2['pts'] = [[-p[0], p[1]] for p in s['pts']]
        out[nn] = s2
    # the near/far drawing weights and draw order belong to the camera side, not to the leg: after mirroring the dog's
    # other side is nearer, so the stroke now named RF carries what LF carried (that swap is what SWAP did). Nothing else.
    return out


DOG_BODY = {'stand': stand, 'crouch': crouch, 'lie': lie, 'curl': curl, 'rear34L': rear34L, 'rearA': rearA, 'front34L': front34L,
            'frontA': frontA}
DOG_HEAD = {'profile': profile, 'front34': front34, 'rear34': rear34, 'rearH': rearH, 'frontH': frontH}
for n in list(DOG_BODY):
    DOG_BODY[n + '_R' if not n.endswith('L') else n[:-1] + 'R'] = mirror(DOG_BODY[n])
for n in list(DOG_HEAD):
    DOG_HEAD[n + '_R'] = mirror(DOG_HEAD[n])
# rearA_R / frontA_R are the substitution partners: the same symmetric point set, mirrored correspondences
DOG_BODY['rearB'] = DOG_BODY.pop('rearA_R')
DOG_BODY['frontB'] = DOG_BODY.pop('frontA_R')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    json.dump({'about': __doc__, 'units': 'metres, y up, body-local (origin: floor under the torso centre); head keys are '
               'head-local (origin: skull centre) and are placed by (cx, cy, angle, scale) in the schedule',
               'body': DOG_BODY, 'head': DOG_HEAD}, open(os.path.join(OUT, 'dog_keys.json'), 'w'), indent=0)
    json.dump({'about': 'person key contours, facing right, metres, origin floor under the person', 'keys': person},
              open(os.path.join(OUT, 'person_keys.json'), 'w'), indent=0)
    print('keys:', len(DOG_BODY), 'body,', len(DOG_HEAD), 'head,', len(person), 'person')
