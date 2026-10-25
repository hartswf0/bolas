"""SCION 45 · The person, as a holdout matte. Drawn (by this swarm) as a dark figure; only the offered hand is a real image.

The person is the one thing in the scene that is a matte and nothing else: a cut-out of darkness against the dusk and the
doorway light, with a light pass for the rim. Joints are world metres relative to the feet (x toward the dog, h up).
Version: person-v3
"""
import math
PX_BESIDE = -1.05   # the score's 'beside the door' (-1.25) placed on this porch's bench
import numpy as np

# joint sets: hip, knee_n, ankle_n, toe_n, knee_f, ankle_f, toe_f, shoulder, elbow_n, wrist_n, elbow_f, wrist_f, neck, head
STAND = dict(hip=(0.0, 0.93), kn=(0.03, 0.49), an=(0.0, 0.07), tn=(0.15, 0.02), kf=(-0.02, 0.49), af=(-0.04, 0.07),
             tf=(0.10, 0.02), sh=(0.02, 1.40), en=(0.05, 1.11), wn=(0.07, 0.84), ef=(-0.03, 1.11), wf=(-0.04, 0.85),
             neck=(0.03, 1.47), head=(0.05, 1.58))
CALL = dict(STAND, sh=(0.05, 1.39), neck=(0.08, 1.46), head=(0.12, 1.56), en=(0.18, 1.16), wn=(0.40, 0.98))   # points at the boards: 'come here'
REACH = dict(STAND, hip=(-0.02, 0.92), sh=(0.12, 1.36), neck=(0.18, 1.42), head=(0.24, 1.51), en=(0.40, 1.27),
             wn=(0.66, 1.18), ef=(0.04, 1.09), wf=(0.04, 0.83), kn=(0.06, 0.49), tn=(0.18, 0.02))
SIT = dict(hip=(0.0, 0.47), kn=(0.40, 0.50), an=(0.42, 0.07), tn=(0.56, 0.02), kf=(0.37, 0.52), af=(0.36, 0.07),
           tf=(0.50, 0.02), sh=(-0.04, 0.98), en=(0.06, 0.72), wn=(0.30, 0.62), ef=(-0.02, 0.71), wf=(0.18, 0.55),
           neck=(-0.02, 1.05), head=(0.0, 1.16))
SIT_PUSH = dict(SIT, sh=(0.12, 0.96), neck=(0.15, 1.03), head=(0.19, 1.12), en=(0.47, 0.99), wn=(0.83, 0.95))
SIT_LOW = dict(SIT, sh=(0.04, 0.95), neck=(0.07, 1.01), head=(0.12, 1.10), en=(0.28, 0.66), wn=(0.54, 0.40))
SIT_LOW_SOFT = dict(SIT_LOW, head=(0.14, 1.08), neck=(0.08, 1.00))


def mix(a, b, u):
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * u, a[k][1] + (b[k][1] - a[k][1]) * u) for k in a}


def sm(a, b, t):
    t = min(1, max(0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def pose_at(t, f):
    """Person pose from the score's circumstances (voice, hand, place, posture) -> (root x, root depth D, joints, flags)."""
    p = f['person']
    # 0-4.8 in the doorway: calls (1.0-2.3), calls again and reaches (3.4-4.6)
    if t < 4.8:
        J = STAND
        J = mix(J, CALL, sm(0.85, 1.05, t) * (1 - sm(2.2, 2.5, t)))
        J = mix(J, REACH, sm(3.35, 3.6, t) * (1 - sm(4.5, 4.8, t)))
        J = mix(J, CALL, sm(3.3, 3.45, t) * (1 - sm(3.35, 3.6, t)) * 0.0)
        return -0.22, -0.06, J, dict(hand='reach' if 3.45 < t < 4.7 else None)
    # 4.8-5.25 steps out of the doorway (toward the camera), 5.2-5.85 to the bench, 5.55-6.0 sits
    if t < 6.0:
        u1 = sm(4.8, 5.25, t); u2 = sm(5.2, 5.85, t); u3 = sm(5.55, 6.0, t)
        x = -0.22 + (PX_BESIDE + 0.22) * u2
        D = -0.06 + (0.82 + 0.06) * u1 - (0.82 - 0.60) * u3     # out past the bench front, then back onto the seat
        J = mix(STAND, SIT, u3)
        ph = math.sin(u2 * math.pi * 3) * 0.12 * (1 - u3)      # a few steps: the legs scissor while it moves
        J = dict(J, kn=(J['kn'][0] + ph, J['kn'][1]), an=(J['an'][0] + 1.6 * ph, J['an'][1]), tn=(J['tn'][0] + 1.6 * ph, J['tn'][1]),
                 kf=(J['kf'][0] - ph, J['kf'][1]), af=(J['af'][0] - 1.6 * ph, J['af'][1]), tf=(J['tf'][0] - 1.6 * ph, J['tf'][1]))
        return x, D, J, dict(hand=None)
    # seated beside the door: reaches and pushes the door's edge (6.0-6.6), then the hand goes low (6.65-7.05) and stays
    J = SIT
    J = mix(J, SIT_PUSH, sm(6.0, 6.15, t) * (1 - sm(6.5, 6.8, t)))
    J = mix(J, SIT_LOW, sm(6.65, 7.05, t))
    if p['voice'] == 'soft':
        J = mix(J, SIT_LOW_SOFT, 0.8)
    return PX_BESIDE, 0.60, J, dict(hand='low' if t > 6.85 else ('push' if 6.02 < t < 6.62 else None))


SEGS = [('hip', 'kf', 0.14, 'far'), ('kf', 'af', 0.11, 'far'), ('af', 'tf', 0.08, 'far'),
        ('sh', 'ef', 0.09, 'far'), ('ef', 'wf', 0.075, 'far'),
        ('hip', 'kn', 0.15, 'near'), ('kn', 'an', 0.115, 'near'), ('an', 'tn', 0.085, 'near'),
        ('sh', 'en', 0.095, 'arm'), ('en', 'wn', 0.08, 'arm')]


def draw(Jw, to_screen, s, draw_far, draw_near, draw_arm):
    """Rasterise the matte with PIL drawers (supersampled by the caller). to_screen maps (x,h) world -> screen px."""
    def cap(a, b, w, dr):
        A = to_screen(*a); B = to_screen(*b); r = w * s / 2
        dr.line([A, B], fill=255, width=max(1, int(2 * r)))
        dr.ellipse([A[0] - r, A[1] - r, A[0] + r, A[1] + r], fill=255)
        dr.ellipse([B[0] - r, B[1] - r, B[0] + r, B[1] + r], fill=255)
    for a, b, w, layer in SEGS:
        dr = {'far': draw_far, 'near': draw_near, 'arm': draw_arm}[layer]
        cap(Jw[a], Jw[b], w, dr)
    # torso: a quadrilateral from shoulders to hips, plus neck and head (near layer)
    sh, hip, neck, head = Jw['sh'], Jw['hip'], Jw['neck'], Jw['head']
    ang = math.atan2(sh[1] - hip[1], sh[0] - hip[0]) - math.pi / 2
    def off(p, d):
        return (p[0] + d * math.cos(ang), p[1] + d * math.sin(ang))
    # torso: back curve, chest, waist (a rounded polygon, not a box)
    mid = ((sh[0] + hip[0]) / 2, (sh[1] + hip[1]) / 2)
    quad = [off(sh, -0.13), off((sh[0] * 0.9 + hip[0] * 0.1, sh[1] * 0.9 + hip[1] * 0.1), -0.17), off(mid, -0.15), off(hip, -0.16),
            off(hip, 0.14), off(mid, 0.12), off((sh[0] * 0.8 + hip[0] * 0.2, sh[1] * 0.8 + hip[1] * 0.2), 0.15), off(sh, 0.10)]
    draw_near.polygon([to_screen(*q) for q in quad], fill=255)
    cap(off(sh, -0.10), off(sh, 0.07), 0.10, draw_near)
    cap(sh, neck, 0.11, draw_near)
    hx, hy = to_screen(*head); r = 0.105 * s
    draw_near.ellipse([hx - r * 0.92, hy - r * 1.1, hx + r * 0.92, hy + r * 1.0], fill=255)
    bx, by = to_screen(head[0] - 0.09, head[1] + 0.04); rb = 0.055 * s
    draw_near.ellipse([bx - rb, by - rb, bx + rb, by + rb], fill=255)   # hair bun
    nx, ny = to_screen(head[0] + 0.1, head[1] - 0.02)
    draw_near.ellipse([nx - 0.03 * s, ny - 0.025 * s, nx + 0.02 * s, ny + 0.025 * s], fill=255)  # nose
