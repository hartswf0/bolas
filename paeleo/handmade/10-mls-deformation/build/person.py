"""SCION-10 · the person: a figure of capsules (no face), posed from the score's person track.
Stands in the doorway and calls; reaches; steps out and aside; sits with its back to the wall beside the door; offers a hand low."""
import numpy as np

COAT = (0.34, 0.36, 0.42); TROUSERS = (0.22, 0.21, 0.24); SKIN = (0.72, 0.55, 0.45); HAIR = (0.16, 0.12, 0.10); SHOE = (0.08, 0.07, 0.07)
SLEEVE = (0.36, 0.38, 0.44)


def ss(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * k


def pose(t, fr, dog_xy):
    p = fr['person']
    reach = float(p['reach']); low = float(p['low'])
    walk = ss(4.65, 5.45, t)                  # steps out of the doorway and aside
    sit = ss(5.45, 7.1, t)
    # feet base: doorway -> a point beside the door on the porch, back to the wall
    A = np.array([-0.07, 0.0]); M = np.array([0.40, 0.50]); B = np.array([0.34, 1.12])
    if walk < 0.5:
        base = lerp(A, M, walk * 2)
    else:
        base = lerp(M, B, (walk - 0.5) * 2)
    fwd = np.array([1.0, 0.0])
    if 0 < walk < 1:
        d = (M - A) if walk < 0.5 else (B - M); d = d / np.linalg.norm(d)
        fwd = lerp(fwd, d, np.sin(np.pi * walk)); fwd /= np.linalg.norm(fwd)
    # toward the dog, a little
    to_dog = dog_xy - base; to_dog /= np.linalg.norm(to_dog) + 1e-9
    face = fwd * 0.6 + to_dog * 0.4 if walk < 0.05 or walk > 0.95 else fwd
    face = face / np.linalg.norm(face)
    l = np.array([-face[1], face[0]])
    up = np.array([0, 0, 1.0])
    def P(xy, z): return np.r_[xy, z]
    call = 1.0 if p['voice'] == 'call' else 0.0
    lean = 0.10 * reach + 0.05 * call * (1 - sit)
    hipz = lerp(0.95, 0.13, sit)
    hip_xy = base + face * (-0.05 * sit)
    hip = P(hip_xy, hipz)
    chest = hip + np.r_[face * (lean + 0.02 - 0.06 * sit + 0.12 * low * sit), 0.48 - 0.03 * sit]
    neck = chest + np.r_[face * 0.03, 0.12]
    head = neck + np.r_[face * (0.04 + 0.05 * low), 0.13 - 0.04 * low]
    parts = []
    parts.append((hip, chest, 0.165, COAT))
    parts.append((chest, neck, 0.075, COAT))
    parts.append((head, head + np.r_[0, 0, 0.001], 0.105, SKIN))
    parts.append((head + np.r_[-face * 0.025, 0.045], head + np.r_[-face * 0.05, 0.02], 0.095, HAIR))
    # legs
    step = np.sin(walk * np.pi * 4) * (0 < walk < 1)
    for sg in (1, -1):
        hp = hip + np.r_[l * sg * 0.09, -0.05]
        if sit < 0.5:
            k = sit * 2
            foot = P(base + l * sg * 0.12 + face * (0.10 * sg * step), 0.05 + 0.08 * max(0, sg * step))
            knee = lerp((hp + foot) / 2 + np.r_[face * 0.04, 0], hp + np.r_[face * 0.30, -0.15], k)
            foot = lerp(foot, hp + np.r_[face * 0.40, -0.40], k)
        else:
            k = (sit - 0.5) * 2
            knee = lerp(hp + np.r_[face * 0.30, -0.15], hp + np.r_[face * 0.38 + l * sg * 0.04, 0.20 - 0.08 * (sg > 0)], k)
            foot = lerp(hp + np.r_[face * 0.40, -0.40], P(base + face * (0.78 - 0.1 * (sg > 0)) + l * sg * 0.16, 0.05), k)
        parts.append((hp, knee, 0.075, TROUSERS)); parts.append((knee, foot, 0.06, TROUSERS))
        parts.append((foot, foot + np.r_[face * 0.13, -0.01], 0.045, SHOE))
    # arms. right arm (toward the dog's side, -l when facing +x... the dog is at y<0 of the seated person) does the reaching
    for sg in (1, -1):
        sh = chest + np.r_[l * sg * 0.19, 0.05]
        rest_hand = sh + np.r_[face * (0.10 + 0.25 * sit) + l * sg * 0.04, -0.58 + 0.25 * sit]
        hand = rest_hand
        if sg == -1:
            if reach > 0:
                tgt = sh + np.r_[to_dog * 0.62, -0.30]
                hand = lerp(rest_hand, tgt, reach)
            if call > 0 and reach < 0.1 and sit < 0.1:      # a beckoning hand at the thigh
                hand = rest_hand + np.r_[face * 0.10 * (0.5 + 0.5 * np.sin(t * 9)), 0.08]
            if low > 0:
                tgt = np.r_[np.array([0.82, 0.62]), 0.10]
                hand = lerp(hand, tgt, low)
        elbow = (sh + hand) / 2 + np.r_[-face * 0.03 + l * sg * 0.05, -0.05]
        parts.append((sh, elbow, 0.055, SLEEVE)); parts.append((elbow, hand, 0.05, SLEEVE))
        parts.append((hand, hand + np.r_[0, 0, 0.001], 0.045, SKIN))
    return parts, {'base': base, 'head': head, 'sit': sit, 'walk': walk}
