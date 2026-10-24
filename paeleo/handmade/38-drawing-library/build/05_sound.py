"""Sound, synthesized with numpy, placed on the score and on the decoder's own events.

- dusk: crickets and a little air, the whole time
- the person's voice: formant-synthesized syllables (no words recorded), hard and rising for
  the calls, low, breathy and falling for 'it's all right' and 'come in'
- the drawings: each substitution of a dog drawing is a soft paper flick (the medium heard);
  a substitution that is a choice (a change of posture or facing) is a louder flick with a
  low 'thup'. The set drawing itself on at the start is a pencil.
- the dog: claw ticks while it backs away, pads while it comes, a flop when it lies with its
  back turned, a sigh when it lies across the sill, tail thumps on the boards when it hears
  'come in', a last settling breath
- the door: a latch and a creak at 6.2 s; then a warm chord (the light) that stays

Writes work/sound.wav (48 kHz stereo).
"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
DUR = 38.0
OFF = 3.0   # scene starts after the 3 s title card
N = int(SR * DUR)
rng = np.random.default_rng(38)
L = np.zeros(N); R = np.zeros(N)
SCORE = json.load(open(f'{HERE}/../score/threshold-score.json'))
SCHED = json.load(open(f'{HERE}/work/schedule.json'))


def band(x, lo, hi, soft=0.15):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / (1 + np.exp(-(f - lo) / (lo * soft + 1))) * 1 / (1 + np.exp((f - hi) / (hi * soft + 1)))
    return np.fft.irfft(X * m, len(x))


def add(sig, t0, gain=1.0, pan=0.0):
    i = int((t0) * SR)
    if i < 0:
        sig = sig[-i:]; i = 0
    n = min(len(sig), N - i)
    if n <= 0:
        return
    L[i:i + n] += sig[:n] * gain * (1 - max(0, pan))
    R[i:i + n] += sig[:n] * gain * (1 + min(0, pan))


def env(n, a, d, shape=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    return e ** shape


# ---------------------------------------------------------------- dusk
for c, (fc, pan, per) in enumerate([(4400, -0.5, 0.93), (4750, 0.5, 1.21), (3900, 0.1, 1.67)]):
    t = 0.4 + rng.uniform(0, per)
    while t < DUR - 0.5:
        n = int(0.24 * SR)
        tt = np.arange(n) / SR
        pulses = sum(np.exp(-((tt - k * 0.055 - 0.02) / 0.009) ** 2) for k in range(3))
        sig = np.sin(2 * np.pi * fc * tt) * pulses
        g = 0.012 if 3 < t < 35 else 0.006
        add(sig, t, g, pan)
        t += per * rng.uniform(0.8, 1.25)
air = band(rng.normal(0, 1, N), 80, 600)
air = air / np.abs(air).max() * 0.02
slow = 0.6 + 0.4 * np.sin(np.arange(N) / SR * 2 * np.pi * 0.07)
L += air * slow; R += np.roll(air, 2400) * slow

# ---------------------------------------------------------------- voice
VOW = {  # formants (Hz) and bandwidths
    'uh': [(640, 80), (1190, 90), (2390, 120)],
    'ih': [(390, 60), (1990, 100), (2550, 120)],
    'eer': [(400, 60), (1900, 100), (2600, 120)],
    'aw': [(570, 80), (840, 90), (2410, 120)],
    'ai': [(750, 80), (1250, 90), (2500, 120)],
    'ee': [(300, 50), (2300, 100), (3000, 140)],
}


def syllable(dur, f0a, f0b, vow_a, vow_b, loud=1.0, breath=0.1, tilt=1.0, onset=None, coda=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    f0 = f0a * (1 - u) + f0b * u
    f0 = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
    ph = np.cumsum(f0) / SR
    Fa, Fb = np.array(VOW[vow_a]), np.array(VOW[vow_b])
    out = np.zeros(n)
    for k in range(1, 40):
        fk = k * f0
        F = Fa[None, :, 0] * (1 - u[:, None]) + Fb[None, :, 0] * u[:, None]
        B = Fa[None, :, 1]
        envk = np.sum(1 / (1 + ((fk[:, None] - F) / B) ** 2), 1)
        amp = envk / k ** tilt
        amp[fk > 5000] = 0
        out += amp * np.sin(2 * np.pi * k * ph)
    a = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.06)
    out *= a
    out += band(rng.normal(0, 1, n), 500, 4000) * breath * a
    if onset == 'k':
        b = band(rng.normal(0, 1, int(0.03 * SR)), 1500, 4000) * env(int(0.03 * SR), 0.002, 0.01)
        out = np.concatenate([b * 0.6, out])
    if onset == 'h':
        b = band(rng.normal(0, 1, int(0.07 * SR)), 800, 5000) * env(int(0.07 * SR), 0.03, 0.04) * 0.3
        out = np.concatenate([b, out])
    if coda == 's':
        b = band(rng.normal(0, 1, int(0.09 * SR)), 4000, 9000) * env(int(0.09 * SR), 0.02, 0.05) * 0.25
        out = np.concatenate([out, b])
    if coda == 't':
        b = band(rng.normal(0, 1, int(0.025 * SR)), 2000, 6000) * env(int(0.025 * SR), 0.002, 0.008) * 0.4
        out = np.concatenate([out, np.zeros(int(0.04 * SR)), b])
    out = out / (np.abs(out).max() + 1e-9) * loud
    return out


def say(t0, sylls, pan=-0.35):
    t = t0
    for s in sylls:
        sig = syllable(**s[1])
        add(sig, OFF + t, 1.0, pan)
        t += len(sig) / SR + s[0]


CALL = dict(breath=0.04, tilt=0.8)
SOFT = dict(breath=0.35, tilt=1.6)
# "come here" at 1.0 and, sharper, at 3.4 (with the reach), "here!" again at 4.0
say(1.00, [(0.03, dict(dur=0.20, f0a=220, f0b=235, vow_a='uh', vow_b='uh', loud=0.20, onset='k', **CALL)),
           (0.0, dict(dur=0.42, f0a=250, f0b=290, vow_a='ee', vow_b='eer', loud=0.23, onset='h', **CALL))])
say(3.42, [(0.03, dict(dur=0.18, f0a=240, f0b=255, vow_a='uh', vow_b='uh', loud=0.24, onset='k', **CALL)),
           (0.0, dict(dur=0.40, f0a=275, f0b=320, vow_a='ee', vow_b='eer', loud=0.27, onset='h', **CALL))])
say(4.02, [(0.0, dict(dur=0.36, f0a=290, f0b=330, vow_a='ee', vow_b='eer', loud=0.23, onset='h', **CALL))])
# "it's all right" softly, twice; "come in" softly at 26.4
for t0, g in ((7.45, 0.20), (10.45, 0.17)):
    say(t0, [(0.02, dict(dur=0.12, f0a=165, f0b=160, vow_a='ih', vow_b='ih', loud=g * 0.8, coda='s', **SOFT)),
             (0.02, dict(dur=0.30, f0a=170, f0b=150, vow_a='aw', vow_b='aw', loud=g, **SOFT)),
             (0.0, dict(dur=0.45, f0a=155, f0b=125, vow_a='ai', vow_b='ee', loud=g, coda='t', **SOFT))])
say(8.55, [(0.02, dict(dur=0.28, f0a=160, f0b=148, vow_a='aw', vow_b='aw', loud=0.15, **SOFT)),
           (0.0, dict(dur=0.42, f0a=150, f0b=122, vow_a='ai', vow_b='ee', loud=0.15, coda='t', **SOFT))])
say(26.42, [(0.03, dict(dur=0.22, f0a=168, f0b=160, vow_a='uh', vow_b='uh', loud=0.17, onset='k', **SOFT)),
            (0.0, dict(dur=0.45, f0a=165, f0b=140, vow_a='ih', vow_b='ee', loud=0.17, **SOFT))])

# ---------------------------------------------------------------- the drawings
def flick(strong):
    n = int(0.05 * SR)
    s = band(rng.normal(0, 1, n), 2500, 9000) * env(n, 0.002, 0.012)
    if strong:
        m = int(0.09 * SR); tt = np.arange(m) / SR
        thup = np.sin(2 * np.pi * (140 - 400 * tt) * tt) * env(m, 0.003, 0.03)
        s = np.concatenate([s, np.zeros(m - n)]) * 0.7 + thup * 0.8
    return s

fr = SCHED['frames']
for a, b in zip(fr, fr[1:]):
    if b['cand'] != a['cand']:
        strong = (a['posture'] != b['posture']) or (a['face'] != b['face'])
        add(flick(strong), OFF + b['t'], 0.10 if strong else 0.035, 0.15)
# pencil drawing the set on (0-0.7 s) and the title card being written
for t0, t1 in ((0.0, 0.7),):
    n = int((t1 - t0) * SR)
    sc = band(rng.normal(0, 1, n), 1800, 7000)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 9 * np.arange(n) / SR) ** 2
    add(sc * am * np.minimum(1, (t1 - t0 - np.arange(n) / SR) / 0.1), OFF + t0, 0.012)

# ---------------------------------------------------------------- the dog
def tap(bright):
    n = int(0.06 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * 110 * tt) * env(n, 0.002, 0.018) * 0.7
    s += band(rng.normal(0, 1, n), 300, 2500 if not bright else 7000) * env(n, 0.001, 0.01) * (0.6 if bright else 0.4)
    return s

for f, s in zip(SCORE['frames'], fr):
    if s['footfall']:
        st = f['dog']['state']
        if st == 'retreat':
            add(tap(True), OFF + f['t'], 0.10, 0.3)
            add(tap(True), OFF + f['t'] + 0.05, 0.06, 0.3)  # claws scrabble
        else:
            add(tap(False), OFF + f['t'], 0.08, 0.2)
# whine at the reach (3.6), a flop when it lies with its back turned (~4.5)
n = int(0.5 * SR); tt = np.arange(n) / SR
wh = np.sin(2 * np.pi * np.cumsum(900 + 300 * np.sin(np.pi * tt / 0.5) + 20 * np.sin(2 * np.pi * 7 * tt)) / SR) * env(n, 0.06, 0.18)
add(wh, OFF + 3.65, 0.035, 0.4)
def flop(g, t0):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (80 - 60 * tt) * tt) * env(n, 0.005, 0.07) + band(rng.normal(0, 1, n), 150, 900) * env(n, 0.005, 0.05) * 0.5
    add(s, OFF + t0, g, 0.3)
flop(0.16, 4.52)
flop(0.18, 23.85)
def sigh(t0, g, d=0.8):
    n = int(d * SR); tt = np.arange(n) / SR
    s = band(rng.normal(0, 1, n), 250, 1600) * np.sin(np.pi * tt / d) ** 1.5 * (1 - 0.5 * tt / d)
    add(s, OFF + t0, g, 0.25)
sigh(5.8, 0.05)
sigh(24.15, 0.09)
sigh(28.45, 0.10, 1.1)
# tail thumps on the boards while it hears 'come in' and looks in (wag in the score)
for f in SCORE['frames']:
    if 26.55 <= f['t'] <= 28.2 and f['dog']['act']['wag'] > 0.4 and f['i'] % 8 == 0:
        n = int(0.08 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * 95 * tt) * env(n, 0.002, 0.025), OFF + f['t'], 0.11, 0.2)

# ---------------------------------------------------------------- the door, then the light
n = int(0.06 * SR)
add(band(rng.normal(0, 1, n), 1200, 6000) * env(n, 0.001, 0.008), OFF + 6.12, 0.12, -0.4)
n = int(0.75 * SR); tt = np.arange(n) / SR
f0 = 70 + 60 * tt / 0.75 + 25 * np.sin(2 * np.pi * 3.1 * tt) + rng.normal(0, 4, n)
ph = np.cumsum(f0) / SR
src = ((ph % 1.0) < 0.12).astype(float)
cr = band(src - src.mean(), 600, 2400) * np.sin(np.pi * tt / 0.75)
add(cr / (np.abs(cr).max() + 1e-9), OFF + 6.2, 0.07, -0.4)

def pad(t0, t1, freqs, g, a=1.5, r=2.0):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt + k) * (1 + 0.003 * np.sin(2 * np.pi * 0.3 * tt)) for k, f in enumerate(freqs))
    e = np.minimum(1, tt / a) * np.minimum(1, (t1 - t0 - tt) / r)
    add(s * e / len(freqs), OFF + t0, g, -0.2)
pad(6.3, 15.0, [110.0, 164.81, 277.18], 0.07, 1.6, 4.0)
pad(14.7, 24.5, [110.0, 164.81, 246.94], 0.035, 2.5, 2.0)          # while it comes
pad(23.8, 33.5, [110.0, 164.81, 277.18, 329.63], 0.075, 0.8, 3.0)  # it lies across the sill
pad(28.4, 34.5, [138.59, 220.0, 369.99, 440.0], 0.05, 1.5, 3.0)    # and stays

# ---------------------------------------------------------------- master
mix = np.stack([L, R], 1)
fade = np.ones(N); fi = int(0.5 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
mix *= fade[:, None]
mix = np.tanh(mix / 0.9) * 0.9
mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(f'{HERE}/work/sound.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('sound ok', N / SR, 's; rms', float(np.sqrt((mix ** 2).mean())))
