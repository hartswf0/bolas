"""SCION 51 · choreography: per scene frame, the dog's pose state and the person's, derived from the score.
Writes build/cache/poses.json. The dog's position is the score's x; its acting (turns, head, lying) follows the score's
act channels with our direction where the critics' lessons demand it (head leads the body at 7.46, head below the back
on the approach, looking IN at 26.4 without lifting)."""
import json, math, os
import numpy as np
from lib import SCORE, FPS, Z_OFF, smooth, lerp, OUT

N = 768
T_REFUSE, T_BACK, T_APPROACH, T_LIE, T_LOOK = 3.417, 7.458, 14.708, 23.792, 26.4
YAW_AWAY = math.radians(-142)


def ang_ease(a, b, t0, t1, t):
    return lerp(a, b, smooth(t0, t1, t))


def voice_at(t):
    v = 'none'
    for tt, ev in SCORE['timeline']:
        if t >= tt and 'voice' in ev:
            v = ev['voice']
    return v


def dog_pose(i, f, walk):
    t = i / FPS; g = f['dog']; a = g['act']
    P = {'t': t, 'z': g['x'] + Z_OFF, 'lie': a['lie'], 'crouch': a['crouch'], 'ear': a['ear'], 'tail': a['tail'],
         'wag': a['wag'], 'moving': 0.0}
    # ---- body yaw
    if t < T_REFUSE:
        yaw = 0.0
    elif t < 7.62:
        yaw = ang_ease(0, YAW_AWAY, T_REFUSE, 3.95, t)
    else:
        yaw = ang_ease(YAW_AWAY, 0, 7.62, 8.55, t)
    P['yaw'] = yaw
    # ---- lying: the score's lie channel during the refusal; the sill lie at 23.79
    if T_REFUSE <= t < 7.62:
        P['lie'] = smooth(4.2, 5.0, t)
    elif 7.62 <= t < 9:
        P['lie'] = 1 - smooth(7.62, 8.2, t)
    # ---- head (neck angle above horizontal, muzzle pitch), world head yaw
    neck, muz, hyw = 50.0, -12.0, 0.0
    if 1.0 <= t < 2.333:                      # backing away, cowering
        k = smooth(1.0, 1.3, t); neck, muz = lerp(50, 4, k), lerp(-12, -42, k)
    elif 2.333 <= t < T_REFUSE:               # watches again: head comes up
        k = smooth(2.333, 2.6, t); neck, muz = lerp(4, 50, k), lerp(-42, -12, k)
    if T_REFUSE <= t < 7.458:                 # turns its back, head droops, then lies with chin down
        k = smooth(T_REFUSE, 4.0, t); neck, muz = lerp(50, 8, k), lerp(-12, -40, k)
        k2 = smooth(4.4, 5.6, t); neck, muz = lerp(neck, -24, k2), lerp(muz, -10, k2)
        hyw = yaw
    if 7.458 <= t < 9.0:                      # the head leads: comes round to the door, muzzle level, body still down
        k = smooth(7.458, 7.72, t)
        neck, muz = lerp(-24, 28, k), lerp(-10, -4, k)
        hyw = lerp(YAW_AWAY, 0.0, k)
        k3 = smooth(8.3, 8.9, t); neck, muz = lerp(neck, 50, k3), lerp(muz, -12, k3)
    if T_APPROACH <= t < T_LIE:               # comes, head low: below the line of the back for the whole approach
        k = smooth(T_APPROACH - 0.05, T_APPROACH + 0.35, t); neck, muz = lerp(50, -30, k), lerp(-12, -38, k)
    if t >= T_LIE:                            # lies across the sill, head up a little, then chin lowers
        k = smooth(T_LIE, 24.5, t); neck, muz = lerp(-30, 6, k), lerp(-38, -10, k)
        k2 = smooth(25.4, 26.1, t); neck, muz = lerp(neck, -10, k2), lerp(muz, -8, k2)
    if t >= T_LOOK:                           # looks IN: head turns into the lit room, level, pushed forward; then settles
        k = smooth(T_LOOK, 26.9, t); k_out = smooth(28.2, 29.0, t)
        kk = k * (1 - k_out)
        neck, muz = lerp(neck, 10, kk), lerp(muz, -6, kk)
        hyw = lerp(0, math.radians(-38), kk)
        P['neck_len'] = 0.21 + 0.05 * kk
        k3 = smooth(28.2, 29.2, t); neck = lerp(neck, -16, k3 * (1 - kk))
    hy = yaw - hyw                 # lib: head world yaw = body yaw - head_yaw
    hy = max(-math.radians(128), min(math.radians(128), hy))
    P['neck'], P['muzzle'], P['head_yaw'] = neck, muz, hy
    P['walk'] = walk
    return P


def person_pose(i, f, walk, prev_xz):
    t = i / FPS; p = f['person']
    Q = {'sit': p['sit'], 'reach': p['reach'], 'low': p['low'], 'lean': 0.0, 'bow': 0.0, 'beckon': 0.0, 'moving': 0.0, 'walk': walk}
    a, b, c = np.array([0.14, -0.34]), np.array([0.02, 0.16]), np.array([-0.98, 0.42])
    k = smooth(4.6, 5.45, t)
    if k < 0.5:
        xz = lerp(a, b, k * 2)
    else:
        xz = lerp(b, c, (k - 0.5) * 2)
    Q['x'], Q['z'] = float(xz[0]), float(xz[1])
    Q['moving'] = float(smooth(4.55, 4.7, t) * (1 - smooth(5.3, 5.5, t)))
    dogz = f['dog']['x'] + Z_OFF
    face_dog = math.atan2(0 - xz[0], dogz - xz[1])
    d = xz - prev_xz
    if Q['moving'] > 0.3 and np.linalg.norm(d) > 1e-4:
        Q['yaw'] = math.atan2(d[0], d[1])
    else:
        Q['yaw'] = face_dog
    if t > 5.3:
        Q['yaw'] = lerp(Q['yaw'], math.atan2(0.98, 3.0), smooth(5.3, 5.8, t))
    v = p['voice']
    if 1.0 <= t < 2.33:
        Q['beckon'] = smooth(1.0, 1.15, t) * (1 - smooth(2.1, 2.33, t)) * (0.75 + 0.25 * math.sin(t * 9))
        Q['lean'] = 0.12 * smooth(1.0, 1.2, t) * (1 - smooth(2.1, 2.4, t))
    if 3.4 <= t < 4.75:
        Q['lean'] = 0.38 * p['reach']
    if v == 'soft':
        Q['bow'] = 0.7
    elif t > 6.8:
        Q['bow'] = 0.4
    return Q, xz


def build():
    fr = SCORE['frames']; assert len(fr) == N
    poses = []; walk = 0.0; pw = 0.0; prev_xz = np.array([0.14, -0.34]); prev_yaw = 0.0; prevz = fr[0]['dog']['x'] + Z_OFF
    for i, f in enumerate(fr):
        z = f['dog']['x'] + Z_OFF
        walk += -(z - prevz); prevz = z
        P = dog_pose(i, f, walk)
        dyaw = abs(P['yaw'] - prev_yaw); prev_yaw = P['yaw']
        walk += dyaw * 0.22 * (1 - P['lie'])         # feet step round while it turns in place
        P['walk'] = walk
        # foot amplitude follows real travel (no sliding when held)
        poses.append(P)
        Q, xz = person_pose(i, f, 0, prev_xz)
        pw += float(np.linalg.norm(xz - prev_xz)); Q['walk'] = pw; prev_xz = xz
        poses[-1] = (P, Q)
    # movement amplitude from measured travel per frame (smoothed)
    w = np.array([p[0]['walk'] for p in poses]); sp = np.abs(np.diff(w, prepend=w[0])) * FPS
    sp = np.convolve(sp, np.ones(7) / 7, 'same')
    for k, (P, Q) in enumerate(poses):
        P['moving'] = float(min(1.0, sp[k] / 0.12)) * (1 - P['lie'])
        P['voice'] = voice_at(k / FPS)
    out = [{'i': k, 'dog': P, 'person': Q, 'door': fr[k]['door']} for k, (P, Q) in enumerate(poses)]
    json.dump(out, open(os.path.join(OUT, 'build/cache/poses.json'), 'w'))
    return out


if __name__ == '__main__':
    o = build(); print(len(o), 'poses')
