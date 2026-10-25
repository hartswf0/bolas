"""SCION 06 · Whitney — the motion mathematician and the choreographic composer.

Everything that moves in the film is read from this module: a small bank of oscillators (typed phases, in radians, on one
time base t = i / 24 s), event envelopes keyed to the score's circumstances, and the dog's choreography (its pose state per
frame), all derived from paeleo/handmade/score/threshold-score.json. Nothing here draws.

Primitives (the native formal language, kept as named objects, not pixels):
  Osc            a phase accumulator theta(t) with a time-varying frequency f(t) (Hz) and optional coupling
  envelope       attack/hold/release functions of t, attached to score events
  bank()         the film's oscillator bank: house (2), dog (3), the 3:2 phase relation psi = 2*theta_dog - 3*theta_house,
                 gait, ring precession rates (harmonic series), field oscillators
  choreography() per-frame pose state of the dog and the person (world metres, radians)

Numerical invariant (tested in proof/phase.json): while the dog approaches and lies on the sill, the 3:2 relation is locked:
|d psi / dt| < 0.05 rad/s; while the commands press (1.0–7.4 s) it drifts (|d psi/dt| > 1 rad/s on average).
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
SCORE_PATH = os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')
FPS = 24
N = 768
T = np.arange(N) / FPS

U_OFFSET = 0.45      # my space: u = x_score - 0.45 (metres); the facade's outer face is u = 0, the inner face u = -0.30


def load_score():
    return json.load(open(SCORE_PATH))


def smooth(a, b, t):
    """smoothstep from a to b (scalar or array t)."""
    s = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return s * s * (3 - 2 * s)


def env(t, on, off, att=0.15, rel=0.4):
    """event envelope: rises at `on`, holds, falls after `off`."""
    return smooth(on, on + att, t) * (1 - smooth(off, off + rel, t))


def series(score, path):
    out = []
    for f in score['frames']:
        v = f
        for k in path.split('.'):
            v = v[k]
        out.append(v)
    return out


def circumstance(score):
    """per-frame typed circumstances from the score: call, reach, sit, beside, door_open, low, soft (0/1 arrays)."""
    v = series(score, 'person.voice'); h = series(score, 'person.hand')
    c = dict(
        call=np.array([x == 'call' for x in v], float),
        soft=np.array([x == 'soft' for x in v], float),
        reach=np.array([x == 'reach' for x in h], float),
        low=np.array([x == 'low' for x in h], float),
        sit=np.array([x == 'sit' for x in series(score, 'person.posture')], float),
        beside=np.array([x == 'beside' for x in series(score, 'person.place')], float),
        door_open=np.array([x == 'open' for x in series(score, 'door')], float),
    )
    return c


class Osc:
    """phase accumulator: theta[i+1] = theta[i] + 2 pi f[i] dt (+ coupling term, applied by bank())."""
    def __init__(self, name, f, phase0=0.0):
        self.name, self.f, self.theta = name, np.asarray(f, float), np.zeros(N)
        self.theta[0] = phase0


DETUNE = 0.03      # the residual detune that coupling must overcome (A/B: K = 0 leaves it drifting)


def bank(score, coupled=True):
    """the oscillator bank. Returns dict of arrays (length N) and the coupling record."""
    t = T
    c = circumstance(score)
    trust = np.array(series(score, 'dog.trust'))
    # pressure: the commands (call, reach) as an event envelope with a slow release
    press = np.clip(np.maximum(env(t, 1.0, 2.3, .08, .9), env(t, 3.4, 4.6, .08, 1.4)) * 1.0, 0, 1)
    # invitation: the changed circumstances accumulate (sit, door, low hand, soft voice)
    invite = np.clip(0.30 * smooth(5.4, 6.0, t) + 0.25 * smooth(6.2, 7.0, t) + 0.20 * smooth(6.8, 7.2, t)
                     + 0.25 * smooth(7.4, 8.4, t), 0, 1)
    F_HOUSE = 0.40                                   # Hz; the house (2 in the 3:2)
    f_house = np.full(N, F_HOUSE)
    # the dog's natural rate: panting under pressure, then a calm breath tuned slightly sharp of 3:2 (drift),
    # entrained by coupling K once circumstances change; the detune is the A/B variable (rational lock vs drift)
    f_nat = 1.5 * F_HOUSE * (1 + 0.55 * press + 0.12 * (1 - invite) + DETUNE)
    K = (0.05 + 2.2 * smooth(7.4, 14.0, t)) * (1.0 if coupled else 0.0)   # coupling strength (rad/s)
    th_h = np.zeros(N); th_d = np.zeros(N); dt = 1 / FPS
    th_d[0] = 0.7
    for i in range(N - 1):
        th_h[i + 1] = th_h[i] + 2 * math.pi * f_house[i] * dt
        psi = 2 * th_d[i] - 3 * th_h[i]
        # coupling pulls psi toward 0 (the reunion phase); 2*dth_d - 3*dth_h = 2*2pi*(f_nat - 1.5 f_h) - 2K sin psi
        th_d[i + 1] = th_d[i] + (2 * math.pi * f_nat[i] - K[i] * math.sin(psi)) * dt
    psi = np.unwrap(2 * th_d - 3 * th_h)
    dpsi = np.gradient(psi) * FPS
    # density: sparse -> dense -> release (the progression the bar asks for)
    density = np.clip(0.38 + 0.12 * smooth(6.2, 8.0, t) + 0.25 * smooth(9.0, 15.0, t) + 0.25 * smooth(15.0, 23.8, t)
                      - 0.45 * smooth(28.6, 31.8, t), 0.25, 1.0)
    # agitation: how hard the commands strike the body's rings (bristle amplitude)
    return dict(t=t, th_house=th_h, th_dog=th_d, psi=psi, dpsi=dpsi, f_house=f_house, f_nat=f_nat, K=K,
                press=press, invite=invite, density=density, trust=trust, **{'c_' + k: v for k, v in c.items()})


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def choreography(score, B):
    """per-frame pose state of the dog (world metres / radians) from the score + my envelopes."""
    t = T
    act = {k: np.array(series(score, 'dog.act.' + k), float) for k in score['frames'][0]['dog']['act']}
    x = np.array(series(score, 'dog.x'), float)
    state = series(score, 'dog.state')
    u = x - U_OFFSET
    # body yaw: 0 faces the door (-u); one full revolution across the film's two turns:
    #   refusal 3.417 -> 3.90 turns away from the camera to pi (its back to the door),
    #   turning back: body 7.72 -> 8.55 from pi through facing the camera (3pi/2) to 2pi.
    yaw = math.pi * smooth(3.43, 3.90, t) + math.pi * smooth(7.72, 8.55, t)
    # head world yaw leads the body (attention -> intention -> gesture)
    head_w = math.pi * smooth(3.40, 3.80, t)
    head_w = head_w + (2 * math.pi - math.radians(18) - math.pi) * smooth(7.46, 7.70, t) \
        + math.radians(18) * smooth(8.1, 8.6, t)
    # on the sill: first a glance toward the low hand (the person, camera side), then at 26.4 into the lit doorway
    glance = -math.radians(42) * smooth(24.4, 25.2, t) * (1 - smooth(26.45, 26.85, t))
    look_in = math.radians(16) * smooth(26.45, 26.85, t) * (1 - smooth(28.2, 28.9, t))
    head_w = head_w + glance + look_in
    # approach glances (small, toward the hand) keep the head alive without lifting it
    head_rel = np.array([wrap(a) for a in head_w - yaw])
    head_rel = np.clip(head_rel, -math.radians(165), math.radians(165))
    # pitch drives: head (0 down .. 1 up), my mapping keeps the approach head below the back line
    head = act['head'].copy()
    head_pitch = np.interp(head, [0, 0.2, 0.45, 0.7, 0.9, 1.25], [-50, -38, -28, 8, 30, 44])
    appr = np.array([s == 'approach' for s in state], float)
    head_pitch = np.where(appr > 0, np.minimum(head_pitch, -30), head_pitch)
    # looking back over the shoulder at 7.46: head lifts as it comes round (before the body rises)
    head_pitch = head_pitch + 12 * smooth(7.46, 7.70, t) * (1 - smooth(8.0, 8.6, t))
    rest = act['rest'].copy()
    # the lie: the score's lie, but at 7.46 the rise waits for the head (it rises 7.70 -> 8.10)
    lie = act['lie'].copy()
    m = (t >= 7.40) & (t < 8.4)
    lie[m] = 1 - smooth(7.70, 8.10, t[m])
    rest[m] = np.minimum(rest[m], 1 - smooth(7.46, 7.62, t[m]))
    # refusal lie: score's timing (4.3 -> 5.0) kept
    crouch = act['crouch']; ear = act['ear']; tail = act['tail']; wag = act['wag']; look = act['look']
    # retreat and approach move along u; forward distance for the gait (signed along the body's forward axis)
    fwd = -np.cos(yaw)             # forward unit along u is -cos(yaw)... (forward vector F = (-cos y, 0, -sin y))
    du = np.gradient(u)
    d_fwd = np.cumsum(du * fwd)    # metres travelled forward (backing away decreases it)
    moving = act['moving']
    return dict(t=t, x=x, u=u, state=state, yaw=yaw, head_rel=head_rel, head_pitch=np.radians(head_pitch),
                lie=lie, rest=rest, crouch=crouch, ear=ear, tail=tail, wag=wag, look=look, d_fwd=d_fwd, moving=moving)


def person(score, B):
    """the person's pose state: position (u, z), sit, reach, low hand, voice."""
    t = T
    # doorway: standing in the door frame (u -0.55); 4.75 -> 5.45 steps aside (inside, toward the camera) and sits
    step = smooth(4.75, 5.45, t)
    pu = -0.58 + (-0.92 - -0.58) * step
    pz = 0.0 + 0.78 * step
    sit = smooth(5.35, 6.05, t)
    reach = np.clip(env(t, 3.40, 4.55, .30, .45), 0, 1)
    low = smooth(6.8, 7.25, t)
    lean = 0.25 * reach + 0.1 * B['press']
    return dict(u=pu, z=pz, sit=sit, reach=reach, low=low, lean=lean, call=B['c_call'], soft=B['c_soft'])


def door(score, B):
    """door leaf angle (radians, swinging inward) and light level."""
    t = T
    ang = math.radians(14) + math.radians(84) * smooth(6.2, 7.0, t)
    light = 0.12 + 0.88 * smooth(6.25, 7.2, t)
    return dict(angle=ang, light=light)


if __name__ == '__main__':
    S = load_score(); B = bank(S)
    lock = (B['t'] > 15) & (B['t'] < 31.9)
    press = (B['t'] > 1) & (B['t'] < 7.4)
    print('psi drift locked', np.abs(B['dpsi'][lock]).max(), 'pressed mean', np.abs(B['dpsi'][press]).mean())
