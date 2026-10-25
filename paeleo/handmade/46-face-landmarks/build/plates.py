"""SCION 46 plate library: the cast. Each plate is drawn artwork (or a cut source portrait) carrying its own landmark
vector in its own coordinates. The film never bends a plate by hand: every plate is placed by a fit from its landmarks
to the solver's projected landmarks (affine for drawn plates, similarity only for the source portrait).

Dog plates are drawn for this film, one per view (the SCION's answer to profile failure: view-specific artwork),
authored facing screen-right with alpha = camera azimuth from the nose (45 three-quarter front, 90 side, 135 three-quarter
back, 180 back). Coat and markings studied from the archive dog in 'Amateur Film New Jersey C' (tan coat, dark saddle,
white collar, chest and blaze). Coordinates: metres, x right, y up."""
import numpy as np
from geom import BODY, HEAD, canon_project, TORSO_KEYS, HEAD_KEYS

PAL = {
    'coat': (166, 118, 74), 'coat_far': (122, 86, 56), 'saddle': (70, 50, 38), 'white': (232, 224, 208),
    'ink': (30, 22, 24), 'nose': (24, 18, 20), 'ear_in': (176, 120, 104), 'iris': (84, 50, 26), 'pupil': (12, 8, 8),
    'shine': (250, 244, 230), 'mouth': (60, 26, 30), 'tongue': (190, 92, 96), 'muzzle': (214, 196, 170),
    'cheek': (150, 104, 66),
}


def catmull(pts, closed=True, n=7):
    P = np.asarray(pts, float)
    if len(P) < 3: return P
    if closed: Q = np.vstack([P[-1], P, P[0], P[1]])
    else: Q = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed: out.append(Q[-2])
    return np.array(out)


def S(pts, fill=None, stroke='ink', w=1.0, closed=True, smooth=True, tag=''):
    return dict(pts=np.asarray(pts, float), fill=fill, stroke=stroke, w=w, closed=closed, smooth=smooth, tag=tag)


def canon(keys, table, alpha):
    return {k: canon_project(table[k], alpha) for k in keys}


# ------------------------------------------------------------------ torso (fit keys: W R C K B Sj Hj T N)
TORSO = {}
TORSO[90] = dict(shapes=[
    S([(0.37, 0.63), (0.27, 0.655), (0.08, 0.632), (-0.12, 0.627), (-0.29, 0.632), (-0.41, 0.595), (-0.47, 0.52), (-0.455, 0.43),
       (-0.40, 0.37), (-0.24, 0.355), (-0.13, 0.372), (0.02, 0.335), (0.16, 0.292), (0.27, 0.282), (0.35, 0.305), (0.43, 0.36),
       (0.47, 0.45), (0.445, 0.555)], fill='coat', w=1.1),
    S([(0.33, 0.648), (0.10, 0.63), (-0.12, 0.624), (-0.30, 0.628), (-0.405, 0.592), (-0.37, 0.535), (-0.16, 0.515),
       (0.05, 0.525), (0.24, 0.565)], fill='saddle', stroke=None),
    S([(-0.40, 0.40), (-0.24, 0.372), (-0.13, 0.385), (0.02, 0.348), (0.16, 0.305), (0.27, 0.296), (0.30, 0.33), (0.15, 0.345), (0.0, 0.38), (-0.15, 0.42), (-0.30, 0.42)], fill='cheek', stroke=None),
    S([(0.47, 0.465), (0.44, 0.365), (0.35, 0.305), (0.31, 0.34), (0.37, 0.46), (0.43, 0.56)], fill='white', stroke=None),
    S([(-0.16, 0.50), (-0.25, 0.44), (-0.27, 0.38)], stroke='ink', w=0.7, closed=False, tag='hatch'),
    S([(0.08, 0.40), (0.0, 0.37), (-0.08, 0.375)], stroke='ink', w=0.6, closed=False, tag='hatch'),
], keys=['W', 'R', 'C', 'K', 'B', 'N', 'T'])
TORSO[135] = dict(shapes=[
    S([(0.27, 0.62), (0.20, 0.652), (0.05, 0.645), (-0.10, 0.645), (-0.23, 0.655), (-0.33, 0.625), (-0.385, 0.55), (-0.38, 0.45),
       (-0.33, 0.37), (-0.25, 0.335), (-0.16, 0.36), (-0.06, 0.345), (0.08, 0.31), (0.19, 0.295), (0.27, 0.32), (0.32, 0.40),
       (0.33, 0.50)], fill='coat', w=1.1),
    S([(0.24, 0.648), (0.05, 0.643), (-0.10, 0.642), (-0.23, 0.652), (-0.31, 0.63), (-0.27, 0.575), (-0.10, 0.56), (0.08, 0.565),
       (0.22, 0.59)], fill='saddle', stroke=None),
    S([(-0.27, 0.60), (-0.335, 0.53), (-0.33, 0.43), (-0.28, 0.375)], stroke='ink', w=0.75, closed=False, tag='hatch'),
    S([(-0.12, 0.55), (-0.17, 0.46), (-0.16, 0.39)], stroke='ink', w=0.6, closed=False, tag='hatch'),
], keys=['W', 'R', 'C', 'K', 'B', 'N', 'T', 'HjR', 'HjL', 'SjR', 'SjL'])
TORSO[180] = dict(shapes=[
    S([(0.0, 0.672), (0.10, 0.66), (0.13, 0.62), (0.05, 0.60), (-0.05, 0.60), (-0.13, 0.62), (-0.10, 0.66)], fill='saddle', w=1.0, tag='shoulders_beyond'),
    S([(0.0, 0.635), (0.10, 0.625), (0.16, 0.575), (0.175, 0.485), (0.16, 0.40), (0.11, 0.335), (0.05, 0.315), (0.0, 0.34),
       (-0.05, 0.315), (-0.11, 0.335), (-0.16, 0.40), (-0.175, 0.485), (-0.16, 0.575), (-0.10, 0.625)], fill='coat', w=1.1),
    S([(0.0, 0.632), (0.08, 0.622), (0.12, 0.59), (0.04, 0.575), (-0.04, 0.575), (-0.12, 0.59), (-0.08, 0.622)], fill='saddle', stroke=None),
    S([(0.0, 0.53), (0.0, 0.37)], stroke='ink', w=0.8, closed=False, smooth=False, tag='hatch'),
    S([(0.10, 0.56), (0.13, 0.47), (0.11, 0.39)], stroke='ink', w=0.6, closed=False, tag='hatch'),
    S([(-0.10, 0.56), (-0.13, 0.47), (-0.11, 0.39)], stroke='ink', w=0.6, closed=False, tag='hatch'),
], keys=['W', 'R', 'T', 'HjR', 'HjL', 'SjR', 'SjL', 'FlR', 'FlL', 'K', 'B'])
for a, P in TORSO.items():
    P['alpha'] = a; P['lm'] = canon(P['keys'], BODY, a)

# ------------------------------------------------------------------ heads (fit keys from HEAD), eyes are separate controls
HEADS = {}
HEADS[90] = dict(shapes=[
    S([(-0.095, 0.035), (-0.06, 0.092), (0.0, 0.112), (0.06, 0.098), (0.105, 0.06), (0.135, 0.038), (0.20, 0.016), (0.245, -0.012),
       (0.262, -0.045), (0.25, -0.068), (0.20, -0.078), (0.15, -0.096), (0.07, -0.098), (-0.01, -0.09), (-0.075, -0.045)],
      fill='coat', w=1.1),
    S([(0.005, 0.105), (0.07, 0.084), (0.135, 0.04), (0.20, 0.014), (0.238, -0.012), (0.205, -0.03), (0.13, 0.012), (0.05, 0.06)],
      fill='white', stroke=None),
    S([(0.12, -0.035), (0.20, -0.05), (0.252, -0.06), (0.20, -0.079), (0.15, -0.095), (0.09, -0.085)], fill='muzzle', stroke=None),
    S([(-0.07, 0.07), (-0.02, 0.098), (0.04, 0.09), (0.03, 0.05), (-0.03, 0.03), (-0.075, 0.03)], fill='saddle', stroke=None),
    S([(0.233, -0.028), (0.262, -0.038), (0.266, -0.056), (0.245, -0.063), (0.228, -0.05)], fill='nose', stroke=None, tag='nose'),
    S([(0.248, -0.066), (0.20, -0.064), (0.14, -0.052)], stroke='ink', w=0.8, closed=False, tag='mouthline'),
    S([(-0.03, -0.01), (-0.045, -0.05), (-0.02, -0.08)], stroke='ink', w=0.5, closed=False, tag='hatch'),
], keys=['S', 'Nz', 'Stp', 'J', 'Th', 'Cr', 'O', 'ER', 'EbR'], eyes={'near': 'ER'})
HEADS[45] = dict(shapes=[
    S([(-0.085, 0.03), (-0.065, 0.088), (-0.01, 0.114), (0.05, 0.108), (0.10, 0.075), (0.125, 0.03), (0.165, -0.002), (0.192, -0.03),
       (0.19, -0.062), (0.155, -0.08), (0.11, -0.10), (0.04, -0.098), (-0.03, -0.075), (-0.07, -0.03)], fill='coat', w=1.1),
    S([(0.03, 0.112), (0.06, 0.07), (0.085, 0.03), (0.14, -0.005), (0.18, -0.025), (0.15, -0.04), (0.09, -0.01), (0.05, 0.02),
       (0.02, 0.07)], fill='white', stroke=None),
    S([(0.07, -0.045), (0.14, -0.05), (0.185, -0.06), (0.15, -0.085), (0.10, -0.10), (0.05, -0.085)], fill='muzzle', stroke=None),
    S([(-0.07, 0.06), (-0.04, 0.10), (0.0, 0.095), (0.0, 0.05), (-0.04, 0.025), (-0.07, 0.03)], fill='saddle', stroke=None),
    S([(0.105, 0.08), (0.125, 0.05), (0.13, 0.02), (0.11, 0.045)], fill='saddle', stroke=None),
    S([(0.158, -0.03), (0.19, -0.032), (0.198, -0.052), (0.178, -0.064), (0.155, -0.052)], fill='nose', stroke=None, tag='nose'),
    S([(0.178, -0.066), (0.15, -0.072), (0.11, -0.066), (0.07, -0.058)], stroke='ink', w=0.8, closed=False, tag='mouthline'),
    S([(0.178, -0.066), (0.182, -0.075)], stroke='ink', w=0.7, closed=False, smooth=False),
], keys=['S', 'Nz', 'Stp', 'J', 'Th', 'Cr', 'O', 'ER', 'EL', 'EbR', 'EbL', 'ChR', 'ChL'], eyes={'near': 'ER', 'far': 'EL'})
HEADS[135] = dict(shapes=[
    # three-quarter back: the face withdrawn. Back of the skull, ear backs, the cheek edge, the muzzle receding; no eye.
    S([(-0.075, 0.05), (-0.055, 0.102), (0.005, 0.122), (0.068, 0.106), (0.102, 0.07), (0.122, 0.032), (0.148, 0.006),
       (0.163, -0.024), (0.148, -0.05), (0.11, -0.07), (0.05, -0.09), (-0.02, -0.082), (-0.068, -0.038)], fill='coat', w=1.1),
    S([(-0.065, 0.055), (-0.045, 0.104), (0.015, 0.12), (0.066, 0.103), (0.062, 0.05), (0.028, 0.018), (-0.02, 0.0), (-0.066, 0.015)],
      fill='saddle', stroke=None),
    S([(0.122, 0.02), (0.158, -0.018), (0.15, -0.044), (0.124, -0.03)], fill='muzzle', stroke=None),
    S([(0.102, 0.07), (0.112, 0.02), (0.10, -0.03), (0.08, -0.07)], stroke='ink', w=0.6, closed=False, tag='hatch'),
    S([(-0.02, -0.005), (-0.035, -0.045), (-0.015, -0.078)], stroke='ink', w=0.55, closed=False, tag='hatch'),
], keys=['S', 'Nz', 'Stp', 'J', 'Th', 'Cr', 'O', 'ER', 'EL', 'EbR', 'EbL', 'ChR', 'ChL'], eyes={})
HEADS[180] = dict(shapes=[
    S([(0.0, 0.118), (0.062, 0.105), (0.088, 0.05), (0.085, -0.02), (0.06, -0.07), (0.0, -0.09), (-0.06, -0.07), (-0.085, -0.02),
       (-0.088, 0.05), (-0.062, 0.105)], fill='coat', w=1.1),
    S([(0.0, 0.115), (0.05, 0.10), (0.06, 0.05), (0.03, 0.02), (0.0, 0.03), (-0.03, 0.02), (-0.06, 0.05), (-0.05, 0.10)], fill='saddle', stroke=None),
    S([(0.0, 0.01), (0.0, -0.07)], stroke='ink', w=0.55, closed=False, smooth=False, tag='hatch'),
    S([(0.06, 0.0), (0.05, -0.05)], stroke='ink', w=0.5, closed=False, tag='hatch'),
    S([(-0.06, 0.0), (-0.05, -0.05)], stroke='ink', w=0.5, closed=False, tag='hatch'),
], keys=['S', 'Cr', 'O', 'EbR', 'EbL', 'ChR', 'ChL', 'Th', 'ER', 'EL'], eyes={})
for a, P in HEADS.items():
    P['alpha'] = a; P['lm'] = canon(P['keys'], HEAD, a)

# ------------------------------------------------------------------ bone plates: (0,0) top joint -> (0,1) bottom joint, x in widths
EAR = dict(outer=[S([(-0.34, 0.0), (-0.33, 0.35), (-0.16, 0.78), (0.0, 1.0), (0.12, 0.78), (0.30, 0.38), (0.33, 0.0), (0.0, -0.08)], fill='saddle', w=1.0)],
           inner=[S([(-0.34, 0.0), (-0.33, 0.35), (-0.16, 0.78), (0.0, 1.0), (0.12, 0.78), (0.30, 0.38), (0.33, 0.0), (0.0, -0.08)], fill='saddle', w=1.0),
                  S([(-0.20, 0.08), (-0.16, 0.45), (-0.04, 0.80), (0.06, 0.62), (0.18, 0.25), (0.14, 0.04)], fill='ear_in', stroke=None)])
BONES = {
    'thigh': [S([(-0.55, 0.0), (-0.62, 0.35), (-0.40, 0.80), (-0.25, 1.0), (0.25, 1.0), (0.45, 0.70), (0.55, 0.25), (0.40, -0.10), (0.0, -0.18)], fill='coat')],
    'shin': [S([(-0.5, 0.0), (-0.35, 0.6), (-0.28, 1.02), (0.28, 1.02), (0.35, 0.5), (0.5, 0.0), (0.0, -0.12)], fill='coat')],
    'meta': [S([(-0.42, -0.05), (-0.38, 1.0), (0.38, 1.0), (0.42, -0.05)], fill='coat', smooth=False)],
    'upperarm': [S([(-0.55, -0.15), (-0.55, 0.45), (-0.38, 1.0), (0.38, 1.0), (0.55, 0.45), (0.50, -0.15), (0.0, -0.25)], fill='coat')],
    'forearm': [S([(-0.45, 0.0), (-0.40, 0.55), (-0.38, 1.02), (0.38, 1.02), (0.40, 0.55), (0.45, 0.0)], fill='coat', smooth=False)],
    'paw': [S([(-0.25, -0.1), (-0.45, 0.35), (-0.40, 0.85), (0.0, 1.05), (0.42, 0.85), (0.45, 0.35), (0.25, -0.1)], fill='white')],
    'neck': [S([(-0.50, -0.1), (-0.56, 0.45), (-0.45, 1.05), (0.45, 1.05), (0.56, 0.45), (0.50, -0.1)], fill='coat', smooth=True),
             S([(-0.47, 0.70), (-0.46, 0.80), (0.46, 0.80), (0.47, 0.70)], fill='white', stroke=None, smooth=False, tag='collar')],
}
BONE_W = {'thigh': 0.16, 'shin': 0.075, 'meta': 0.055, 'upperarm': 0.11, 'forearm': 0.058, 'paw': 0.07, 'neck': 0.22}

# eye control: almond in eye-local units (x along the eye, y up), lid covers from the top
EYE = dict(w=0.032, h=0.020)


def plate_for(table, alpha):
    """view-matching: the authored view nearest the needed azimuth (0..180, mirrored sides handled by the caller)"""
    keys = sorted(table)
    return table[min(keys, key=lambda a: abs(a - alpha))]
