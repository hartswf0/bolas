"""Score -> puppet controls, per scene frame (768 at 24 fps). The score's act values drive the puppet; where the brief's
lessons demand it, timing is re-shaped (the refusal turn completes by 3.82 s; the head comes round at 7.46 s ahead of
the body). Everything here is deterministic from paeleo/handmade/score/threshold-score.json."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = json.load(open(os.path.normpath(os.path.join(HERE, '../../score/threshold-score.json'))))
FR = SCORE['frames']
X_OFF = 0.25          # torso centre (world X) = score x - X_OFF: lying at x=0.59 puts the head inside the frame
DOG_Z = -0.25         # the dog's path runs 0.25 m nearer the camera than the door's centre line (in front of the seated person)


def sm(t):
    t = np.clip(t, 0, 1); return float(t * t * (3 - 2 * t))


def ramp(t, t0, t1, a, b):
    return a + (b - a) * sm((t - t0) / (t1 - t0))


def head_rot(head):
    # the template (f006) holds its head high; act.head 0.9 (alert) sits a little below it
    if head >= 0.9:
        return -0.55 + 0.9 * (head - 0.9)
    return -0.55 - 0.8 * ((0.9 - head) / 0.75) ** 0.6


def whip_mid(p):
    """turn back (round 4): 0->55 deg, then three solid 3/4 intermediates through the front, then ->180 (no dissolve)"""
    p = float(np.clip(p, 0, 1))
    if p < 0.35:
        return 55.0 * sm(p / 0.35) ** 0.8
    if p < 0.65:
        return 55.0 + 70.0 * (p - 0.35) / 0.3
    return 125.0 + 55.0 * sm((p - 0.65) / 0.35) ** 1.25


def whip(p):
    """a turn as a whip-around: 0->55 deg, then one cut to 125, then ->180. No frame between 55 and 125 deg:
    the learned front view knots the legs (critic, round 1), so the dog is never shown edge-on."""
    p = float(np.clip(p, 0, 1))
    if p < 0.5:
        return 55.0 * sm(p / 0.5) ** 0.8
    return 125.0 + 55.0 * sm((p - 0.5) / 0.5) ** 1.25


def phi_body(t):
    if t < 3.42:
        return 0.0
    if t < 8.0:
        return whip((t - 3.42) / 0.4)
    return 180.0 - whip_mid((t - 8.0) / 0.5)


def controls():
    out = []
    D = 0.0; prev_x = FR[0]['dog']['x']; Dturn = 0.0; prev_phi = 0.0
    for f in FR:
        t = f['t']; a = f['dog']['act']; x = f['dog']['x']
        phi = phi_body(t)
        facing_left = phi < 90
        D += -(x - prev_x) * (1 if facing_left else -1); prev_x = x
        # turning in place: the feet step through the turn (a virtual walk of 0.5 m per half-turn)
        Dturn += abs(phi - prev_phi) / 180 * 0.21; prev_phi = phi
        # head view: leads the refusal turn a little; at 7.46 comes round over the shoulder before the body
        phi_h = phi_body(t + 0.07) if t < 7.46 else phi
        if 7.46 <= t < 8.6:
            look_back = max(14.0, 180.0 - whip((t - 7.46) / 0.26))
            phi_h = min(look_back, max(phi, 14)) if t >= 8.0 else look_back
        rest = a['rest']
        hr = head_rot(a['head'])
        lie = a['lie']
        # the refusal: lying with its back to the door, face turned a little toward us while it rests
        if 4.3 < t < 7.46:
            phi_h = 180 - 18 * sm((t - 5.2) / 0.8)
        if t >= 7.46 and t < 8.6:
            hr = ramp(t, 7.46, 7.7, head_rot(0.15), -0.45) if t < 8.1 else ramp(t, 8.1, 8.6, -0.45, head_rot(a['head']))   # head lifts as it turns back to look
        # lying at the sill: head resting turned a little toward the camera; at 26.4 it turns in, away from us
        away = 0.0
        if t >= 24.0:
            look = a['look']
            phi_h = 18 * (1 - min(1, look * 1.6)) * (1 - 0.0)
            if 27.0 <= t <= 28.2:
                look = 1.0          # held: the look into the room lasts to 28.2 s
            away = look
            phi_h = 18 * (1 - min(1, look * 1.6))
            # looking in: the head lifts off the paws and the muzzle goes up into the lit doorway, back of the head to us
            hr = hr * (1 - look) + (-0.12) * look   # level: the back-of-head layer is drawn upright
            if rest > 0.05 and not (27.0 <= t <= 28.2):
                hr = hr * (1 - rest) + (-1.05) * rest
        tail = a['tail']; wag = a['wag']
        tail_rot = (tail - 0.5) * 1.15 + wag * 0.4 * np.sin(2 * np.pi * 2.4 * t) + 0.5 * lie
        tail_rot = tail_rot * (1 - lie) + 0.4 * lie   # lying: the tail rests along the boards, not under the body
        crouch = a['crouch']
        pitch = 0.11 * crouch * (1 - lie)
        moving = a['moving']
        bob = 1.5 * abs(np.sin(D / 0.42 * 2 * np.pi)) * (1 - lie) if moving else 0.0
        out.append({'i': f['i'], 't': t, 'state': f['dog']['state'], 'x_score': x, 'X': x - X_OFF, 'phi': phi,
                    'phi_h': float(np.clip(phi_h, 0, 180)), 'head_rot': hr, 'tail_rot': tail_rot, 'crouch': crouch,
                    'lie': lie, 'rest': rest, 'pitch': pitch, 'D': D + Dturn, 'away': away, 'bob': bob,
                    'look': a['look'], 'head': a['head']})
    return out


def world(t):
    """the person, door and voice from the score."""
    f = FR[min(len(FR) - 1, int(round(t * 24)))]
    door_open = sm((t - 6.2) / 0.9)
    light = 0.45 + 0.55 * door_open
    return {'door': door_open, 'light': light, 'voice': f['person']['voice'], 'person': f['person']}
