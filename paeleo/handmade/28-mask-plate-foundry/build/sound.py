"""Sound: everything synthesized here (no recordings). A source-filter voice (glottal pulses through moving formant
resonators), stone footfalls placed on the rig's own foot plants, a door creak, the room's warmth when the door opens,
dusk crickets. Writes cache/audio.wav (48 kHz stereo, 38 s) and cache/audio_levels.json (measured RMS per line)."""
import os, json, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
SR = 48000; DUR = 38.0; OFF = 3.0          # the scene starts after the 3 s title
rng = np.random.default_rng(28)
N = int(SR * DUR)
mix = np.zeros((N, 2), np.float32)


def reson(x, f, bw):
    """2-pole resonator with per-sample centre frequency f (array) and bandwidth bw (Hz)."""
    y = np.zeros_like(x); y1 = y2 = 0.0
    r = np.exp(-np.pi * bw / SR)
    c = -r * r; b = 2 * r * np.cos(2 * np.pi * f / SR); a = 1 - b - c
    for n in range(len(x)):
        v = a[n] * x[n] + b[n] * y1 + c * y2
        y2 = y1; y1 = v; y[n] = v
    return y


# phoneme table: F1 F2 F3, voiced amplitude, noise amplitude, noise centre
PH = {
    'k': (300, 1800, 2500, 0.0, 0.9, 2200), 't': (300, 1800, 2600, 0.0, 0.8, 4000), 's': (300, 1800, 2600, 0.0, 0.6, 6500),
    'h': (600, 1500, 2500, 0.0, 0.5, 1500), 'm': (260, 1100, 2300, 0.35, 0.0, 0), 'n': (260, 1600, 2500, 0.35, 0.0, 0),
    'A': (640, 1190, 2390, 1.0, 0.0, 0), 'I': (400, 2000, 2600, 1.0, 0.0, 0), 'E': (500, 1500, 2500, 0.9, 0.0, 0),
    'O': (570, 840, 2410, 1.0, 0.0, 0), 'l': (360, 1000, 2400, 0.7, 0.0, 0), 'r': (420, 1300, 1600, 0.75, 0.0, 0),
    'a': (750, 1300, 2500, 1.0, 0.0, 0), 'i': (380, 2100, 2700, 0.9, 0.0, 0), '_': (500, 1500, 2500, 0.0, 0.0, 0),
}


def voice(seq, f0, breath=0.05, gain=1.0):
    """seq: list of (phoneme, seconds); f0: list of (fraction of utterance, Hz)."""
    total = sum(d for _, d in seq); n = int(total * SR)
    tt = np.arange(n) / SR
    # per-sample targets with 25 ms smoothing between phonemes
    keys = []; acc = 0
    for p, d in seq:
        keys.append((acc + d * .5, PH[p])); acc += d
    kt = np.array([k[0] for k in keys])
    tr = lambda j: np.interp(tt, kt, [k[1][j] for k in keys])
    F1, F2, F3, AV, AN, NC = (tr(j) for j in range(6))
    # amplitude envelope per phoneme boundaries (hard-ish edges for stops)
    hz = np.interp(tt / total, [a for a, _ in f0], [b for _, b in f0])
    hz = hz * (1 + 0.01 * np.sin(2 * np.pi * 5.5 * tt)) * (1 + 0.004 * rng.standard_normal(n))
    ph = np.cumsum(hz / SR) % 1.0
    glott = np.where(ph < .6, np.sin(np.pi * ph / .6) ** 2, 0.0)        # Rosenberg-like pulse
    glott = np.diff(glott, prepend=0) * 30
    src = glott * AV + rng.standard_normal(n) * (breath * AV + 0.0)
    v = reson(src, F1, 90) + 0.7 * reson(src, F2, 120) + 0.35 * reson(src, F3, 170)
    noise = rng.standard_normal(n)
    nz = reson(noise, np.maximum(NC, 500), 1800) * AN * 0.25
    out = v + nz
    env = np.minimum(1, np.minimum(tt / .02, (total - tt) / .05))
    out = out * env
    return (out / (np.abs(out).max() + 1e-9) * gain).astype(np.float32)


def place(sig, t_scene, pan=0.0, gain=1.0):
    i = int((t_scene + OFF) * SR)
    j = min(N, i + len(sig))
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    mix[i:j, 0] += sig[:j - i] * gain * l; mix[i:j, 1] += sig[:j - i] * gain * r


def rms_db(sig):
    s = sig[np.abs(sig) > 1e-4]
    return float(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12))


# the person's lines: the calls are full voice; the soft lines are breathier, lower, and 12 dB quieter
come_here = [('k', .05), ('A', .13), ('m', .09), ('h', .07), ('I', .14), ('E', .20)]
its_all_right = [('I', .07), ('t', .03), ('s', .08), ('O', .15), ('l', .07), ('r', .06), ('a', .14), ('i', .10), ('t', .04)]
come_in = [('k', .05), ('A', .12), ('m', .08), ('I', .12), ('n', .18)]
CALL = 0.50; SOFT = CALL * 10 ** (-12 / 20)
person_pan = -0.55
lines = []
for t in (1.0, 3.42):
    s = voice(come_here, [(0, 235), (.45, 250), (.6, 300), (.85, 260), (1, 220)], breath=.03, gain=CALL)
    place(s, t, person_pan); lines.append(('call', t, s))
for t in (7.4, 10.4):
    s = voice(its_all_right, [(0, 200), (.5, 185), (1, 150)], breath=.18, gain=SOFT)
    place(s, t, person_pan); lines.append(('soft', t, s))
s = voice(come_in, [(0, 190), (.6, 180), (1, 160)], breath=.18, gain=SOFT)
place(s, 26.4, person_pan); lines.append(('soft', 26.4, s))

# dusk room tone: low wind + crickets (always under the soft voice)
n = N
wind = np.cumsum(rng.standard_normal(n)).astype(np.float32); wind -= np.convolve(wind, np.ones(4801) / 4801, 'same'); wind /= np.abs(wind).max()
tt = np.arange(n) / SR
crick = np.zeros(n, np.float32)
for c0, fr, rate in ((0.3, 4300, 2.6), (0.9, 4700, 3.1), (1.7, 3900, 2.2)):
    gate = (np.sin(2 * np.pi * rate * tt + c0) > .7) * (np.sin(2 * np.pi * 28 * tt) > 0)
    crick += (np.sin(2 * np.pi * fr * tt) * gate).astype(np.float32)
tone = 0.010 * wind + 0.0035 * crick
mix[:, 0] += tone; mix[:, 1] += tone * .9

# door: latch click + creak at 6.2, then the room's warmth (low hum + muffled murmur) while it is open
cr = np.arange(int(.6 * SR)) / SR
creak = np.sin(2 * np.pi * (180 + 90 * np.sin(2 * np.pi * 3 * cr)) * cr + 4 * np.sin(2 * np.pi * 37 * cr)) * np.exp(-cr * 3) * (cr > .05)
click = rng.standard_normal(int(.02 * SR)) * np.exp(-np.arange(int(.02 * SR)) / 150)
place(click.astype(np.float32), 6.15, -.4, .25); place(creak.astype(np.float32), 6.2, -.4, .08)
i0 = int((6.2 + OFF) * SR)
warm = (np.sin(2 * np.pi * 60 * tt) * .5 + np.sin(2 * np.pi * 120 * tt) * .25) * np.clip((tt - 6.2 - OFF) / .6, 0, 1)
mix[:, 0] += (0.004 * warm).astype(np.float32); mix[:, 1] += (0.003 * warm).astype(np.float32)

# the dog's feet: one soft click on stone per foot plant, from the rig's own gait (same phase, same stride)
import sys
sys.path.insert(0, HERE)
import rig
g = rig.Gait()
steps = []
for k, off in (('hind', 0.0), ('fore_near', 0.25), ('hind_far', 0.5), ('fore_far', 0.75)):
    prev = None
    for i in range(768):
        if abs(g.dx[i]) < 1e-4: prev = None; continue
        u = (g.dist[i] / rig.STRIDE + off) % 1.0
        if prev is not None and u < prev: steps.append(i / 24)
        prev = u
pad = np.arange(int(.05 * SR)) / SR
for ts in steps:
    tap = (rng.standard_normal(len(pad)) * np.exp(-pad * 90) + 0.6 * np.sin(2 * np.pi * 140 * pad) * np.exp(-pad * 60)).astype(np.float32)
    x = rig.FR[int(ts * 24)]['dog']['x']
    place(tap, ts, pan=float(np.interp(x, [0, 4.5], [-.5, .7])), gain=.05)
# lying down: two soft body thumps (refusal 4.6 s, the sill 24.1 s) and a breath out at 29 s
for ts, gn in ((4.62, .12), (24.15, .14)):
    d = np.arange(int(.25 * SR)) / SR
    th = (np.sin(2 * np.pi * 70 * d) * np.exp(-d * 18) + .2 * rng.standard_normal(len(d)) * np.exp(-d * 40)).astype(np.float32)
    place(th, ts, .4 if ts < 10 else -.2, gn)
d = np.arange(int(1.1 * SR)) / SR
sigh = (rng.standard_normal(len(d)) * np.sin(np.pi * d / 1.1) ** 2).astype(np.float32)
sigh = np.convolve(sigh, np.ones(30) / 30, 'same')
place(sigh, 29.0, -.2, .05)

mix = np.clip(mix, -1, 1)
os.makedirs(CACHE, exist_ok=True)
with wave.open(os.path.join(CACHE, 'audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
lv = dict(lines=[dict(kind=k, t=t, rms_dbfs=round(rms_db(s * (1)), 2)) for k, t, s in lines],
          room_tone_rms_dbfs=round(float(20 * np.log10(np.sqrt(np.mean(tone ** 2)))), 2), footfalls=len(steps))
calls = [l['rms_dbfs'] for l in lv['lines'] if l['kind'] == 'call']; soft = [l['rms_dbfs'] for l in lv['lines'] if l['kind'] == 'soft']
lv['soft_under_calls_db'] = round(float(np.mean(calls) - np.mean(soft)), 2)
lv['soft_over_room_tone_db'] = round(float(min(soft) - lv['room_tone_rms_dbfs']), 2)
json.dump(lv, open(os.path.join(CACHE, 'audio_levels.json'), 'w'), indent=1)
print(json.dumps(lv))
