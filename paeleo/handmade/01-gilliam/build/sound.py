"""Sound editor: every sound synthesized here with numpy; punctuating incongruities placed on the score's frames.
Writes build/cache/sound.wav (48 kHz stereo, 38 s) and build/cache/sound_events.json."""
import json, math, wave
import numpy as np
from common import *

SR = 48000
DUR = 38.0
OFF = 3.0  # the scene starts after the 3 s title
score = load_score(); SF = score['frames']; N = len(SF)
L = np.zeros(int(SR * DUR)); R = np.zeros(int(SR * DUR))
rng = np.random.default_rng(5)
log = []


def first(pred, start=0):
    for f in SF[start:]:
        if pred(f):
            return f['i']


EV = {}
EV['retreat'] = first(lambda f: f['dog']['state'] == 'retreat')
EV['watch1'] = first(lambda f: f['dog']['state'] == 'watch', EV['retreat'])
EV['refuse'] = first(lambda f: f['dog']['state'] == 'refuse')
EV['watch2'] = first(lambda f: f['dog']['state'] == 'watch', EV['refuse'])
EV['approach'] = first(lambda f: f['dog']['state'] == 'approach')
EV['lie'] = first(lambda f: f['dog']['state'] == 'lie_down')
EV['door_open'] = first(lambda f: f['door'] == 'open')
T = {k: v / FPS for k, v in EV.items()}


def add(sig, t, pan=0.0, gain=1.0, name=None, scene=True):
    t0 = t + (OFF if scene else 0)
    i = int(t0 * SR)
    if i >= len(L):
        return
    sig = sig[:len(L) - i]
    gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    L[i:i + len(sig)] += sig * gain * gl * 1.414
    R[i:i + len(sig)] += sig * gain * gr * 1.414
    if name:
        log.append({'t_film': round(t0, 3), 't_scene': round(t, 3) if scene else None, 'sound': name})


def env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def noise(d):
    return rng.standard_normal(int(d * SR))


def onepole(x, a):
    """simple low-pass: y += a (x - y)"""
    y = np.empty_like(x); acc = 0.0
    # vectorized via lfilter-like recursion in blocks is overkill; this is short audio
    for k in range(len(x)):
        acc += a * (x[k] - acc); y[k] = acc
    return y


def bandnoise(d, lo, hi):
    n = int(d * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def sweepnoise(d, f0, f1, bw=0.5):
    """noise whose band sweeps f0 -> f1 (paper whoosh): sum of short band chunks with crossfade"""
    n = int(d * SR); out = np.zeros(n); seg = int(0.02 * SR)
    for s in range(0, n, seg // 2):
        u = s / n; fc = f0 * (f1 / f0) ** u
        c = bandnoise(seg / SR, fc * (1 - bw / 2), fc * (1 + bw / 2)) * np.hanning(seg)
        out[s:s + seg] += c[:len(out[s:s + seg])]
    return out / (np.abs(out).max() + 1e-9)


def tone(d, f, kind='sine', glide=None):
    n = int(d * SR); t = np.arange(n) / SR
    ff = np.full(n, f, float) if glide is None else np.geomspace(f, glide, n)
    ph = 2 * np.pi * np.cumsum(ff) / SR
    if kind == 'sine': return np.sin(ph)
    if kind == 'saw':
        y = np.zeros(n)
        for k in range(1, 14): y += np.sin(k * ph) / k * (ff * k < 9000)
        return y * 0.6
    if kind == 'square':
        y = np.zeros(n)
        for k in range(1, 16, 2): y += np.sin(k * ph) / k * (ff * k < 9000)
        return y * 0.8


def thump(f=70, d=0.25, click=0.3):
    n = int(d * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t * (1 + 1.5 * np.exp(-t * 30))) * np.exp(-t * 18)
    y[:int(0.004 * SR)] += bandnoise(0.004, 1500, 6000) * click
    return y


def mix(*sigs):
    n = max(len(x) for x in sigs); y = np.zeros(n)
    for x in sigs: y[:len(x)] += x
    return y


def voice(sylls, f0s, loud=True):
    """additive formant voice: list of (dur, (F1,F2,F3) start, end, onset noise) per syllable."""
    out = []
    for (d, Fa, Fb, onset), (p0, p1) in zip(sylls, f0s):
        n = int(d * SR); t = np.arange(n) / SR; u = t / d
        f0 = p0 + (p1 - p0) * u + (6 if loud else 2) * np.sin(2 * np.pi * 5.5 * t)
        ph = 2 * np.pi * np.cumsum(f0) / SR
        F = [Fa[j] + (Fb[j] - Fa[j]) * u for j in range(3)]
        BW = [90, 120, 170]
        y = np.zeros(n)
        for k in range(1, 40):
            fk = k * f0
            a = sum(1.0 / (1 + ((fk - F[j]) / BW[j]) ** 2) * [1, 0.6, 0.3][j] for j in range(3))
            a *= (fk < 5000) * (1.0 / k ** 0.3)
            y += a * np.sin(k * ph)
        if not loud:
            y = y * 0.6 + bandnoise(d, 300, 4000) * 0.12 * np.abs(np.sin(np.pi * u))
        e = np.minimum(1, np.minimum(t / 0.03, (d - t) / 0.06).clip(0, 1))
        y *= e
        if onset == 'k':
            y[:int(0.03 * SR)] += bandnoise(0.03, 1500, 4500)[:int(0.03 * SR)] * 0.8
        if onset == 'h':
            h = bandnoise(0.08, 500, 3500) * 0.5 * np.linspace(0, 1, int(0.08 * SR))
            y = np.concatenate([h, y])
        if onset == 's':
            y = np.concatenate([y, bandnoise(0.07, 4000, 9000) * 0.25 * np.hanning(int(0.07 * SR))])
        out.append(y)
        out.append(np.zeros(int(0.03 * SR)))
    y = np.concatenate(out)
    return y / (np.abs(y).max() + 1e-9)


# ------------------------------------------------------------------ title: a cut-paper fanfare
fan = np.zeros(int(3.0 * SR))
for k, (tt, f, d) in enumerate([(0.15, 262, 0.18), (0.36, 330, 0.18), (0.57, 392, 0.18), (0.80, 523, 0.7)]):
    s = (tone(d, f, 'saw') + 0.5 * tone(d, f * 1.005, 'saw')) * env(int(d * SR), 0.01, 0.12)
    i = int(tt * SR); fan[i:i + len(s)] += s * 0.25
for tt in [0.3, 0.55]:  # the paper slips land
    s = thump(110, 0.12, 0.6); i = int(tt * SR); fan[i:i + len(s)] += s * 0.4
honk = tone(0.35, 140, 'square', glide=95) * env(int(0.35 * SR), 0.01, 0.15)
fan[int(1.9 * SR):int(1.9 * SR) + len(honk)] += honk * 0.25
add(fan, 0.0, 0.0, 0.9, 'title fanfare (synth brass), paper slaps, honk', scene=False)

# ------------------------------------------------------------------ dusk ambience: crickets + air (scene only)
n = int(32 * SR); t = np.arange(n) / SR
cr = np.zeros(n)
for (fc, rate, ofs, pan) in [(4300, 0.73, 0.0, 0.6), (4700, 0.91, 0.31, -0.4), (3900, 0.61, 0.57, 0.9)]:
    gate = ((t * rate + ofs) % 1.0 < 0.22).astype(float)
    pulses = (np.sin(2 * np.pi * 28 * t) > 0.2).astype(float)
    c = np.sin(2 * np.pi * fc * t) * gate * pulses
    c = np.convolve(c, np.hanning(64) / 32, 'same')
    add(c * 0.12, 0.0, pan, 1.0)
    add(c[:int(3 * SR)] * 0.05 * np.linspace(1, 0, int(3 * SR)), 32.0, pan, 1.0)
air = np.convolve(rng.standard_normal(n), np.ones(400) / 400, 'same')
air = air / np.abs(air).max()
add(air * 0.12 * (1 + 0.3 * np.sin(2 * np.pi * 0.07 * t)), 0.0, 0.0, 1.0, 'dusk: three crickets, air')

# ------------------------------------------------------------------ the first command (t = 1.0): COME HERE! + klaxon; the dog's head shuts like a door
come_here = voice([(0.26, (640, 1190, 2390), (600, 1100, 2400), 'k'), (0.42, (400, 1950, 2600), (620, 1500, 2500), 'h')],
                  [(205, 175), (225, 150)], loud=True)
for tc in [1.0, T['refuse']]:
    add(come_here, tc, -0.55, 0.55, 'voice: COME HERE! (formant synth, loud)')
    kl = mix(tone(0.5, 330, 'square', glide=220), tone(0.5, 247, 'square', glide=165)) * env(int(0.5 * SR), 0.01, 0.2)
    add(kl, tc + 0.02, -0.4, 0.14, 'klaxon under the shout')
add(mix(thump(85, 0.3, 0.8), 0.4 * thump(160, 0.12, 1.0)), T['retreat'], 0.45, 0.8, 'door SLAM: the dog head becomes a door')
for k in range(7):  # claws scrabbling backwards
    add(bandnoise(0.025, 2000, 7000) * np.hanning(int(0.025 * SR)), T['retreat'] + 0.12 + k * 0.17, 0.5, 0.18)
cre = tone(0.35, 380, 'saw', glide=520) * (0.6 + 0.4 * np.sin(np.arange(int(0.35 * SR)) / SR * 2 * np.pi * 33)) * env(int(0.35 * SR), 0.02, 0.1)
add(cre, T['watch1'] - 0.05, 0.45, 0.12, 'creak: the door-head opens back into a dog head')
add(thump(300, 0.08, 1.0), T['watch1'] + 0.28, 0.45, 0.35, 'pop')

# ------------------------------------------------------------------ the second command (3.42): telescoping arm, the card turns its back, the stamp
for k in range(12):
    add(bandnoise(0.012, 2500, 8000), T['refuse'] + 0.02 + k * 0.045, -0.2 + k * 0.06, 0.35, 'ratchet: the arm extends' if k == 0 else None)
sw = tone(0.5, 500, 'sine', glide=1500) * env(int(0.5 * SR), 0.02, 0.1)
add(sw, T['refuse'], 0.1, 0.18, 'slide whistle up')
add(sweepnoise(0.22, 600, 4000), T['refuse'], 0.5, 0.35, 'paper whoosh: the card turns over')
add(thump(140, 0.15, 1.0), T['refuse'] + 0.23, 0.5, 0.5, 'card slap')
stamp = mix(thump(60, 0.2, 1.0), 0.6 * thump(190, 0.1, 1.0))
add(stamp, T['refuse'] + 0.33, 0.5, 0.75, 'rubber stamp: NO')
retract_t = 4.625
add(tone(0.45, 1400, 'sine', glide=380) * env(int(0.45 * SR), 0.02, 0.1), retract_t, 0.0, 0.18, 'slide whistle down: the arm retracts')
add(thump(220, 0.1, 1.0), retract_t + 0.45, -0.5, 0.5, 'snap')
add(sweepnoise(0.3, 2000, 400) * 0.6, 4.55, 0.5, 0.3, 'paper flop: lies down, back turned')

# ------------------------------------------------------------------ steps aside, sits; the door opens; light
for k in range(4):
    add(thump(180 + 30 * k, 0.07, 0.6), 5.45 + k * 0.17, -0.7, 0.28, 'hop steps' if k == 0 else None)
add(mix(sweepnoise(0.25, 800, 200) * 0.5, thump(70, 0.2, 0.2)), 6.05, -0.8, 0.45, 'sits: cushion flump')
dn = int(0.6 * SR)
creak = tone(0.6, 160, 'saw', glide=110) * (0.5 + 0.5 * (np.sin(np.arange(dn) / SR * 2 * np.pi * 27) > 0)) * env(dn, 0.03, 0.15)
add(creak, T['door_open'], -0.4, 0.13, 'door creak')
add(thump(120, 0.1, 1.0), T['door_open'] + 0.2, -0.4, 0.35, 'latch')
pd = 32 - T['door_open'] - 0.2
n = int(pd * SR); tp = np.arange(n) / SR
pad = sum(np.sin(2 * np.pi * f * tp + k) for k, f in enumerate([196, 247, 294, 392, 494])) / 5
pad *= (1 - np.exp(-tp / 0.25)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.21 * tp)) * np.minimum(1, (pd - tp) / 1.0)
add(pad, T['door_open'] + 0.2, -0.3, 0.085, 'warm light: a soft G-major chord that holds to the end')
add(np.sin(2 * np.pi * 880 * np.arange(int(0.6 * SR)) / SR) * np.exp(-np.arange(int(0.6 * SR)) / SR * 7), 6.8, -0.6, 0.12, 'plink: the hand, low')

# ------------------------------------------------------------------ soft voice and the butterfly
allright = voice([(0.14, (400, 2000, 2600), (400, 2000, 2600), 's'), (0.22, (650, 1000, 2500), (500, 900, 2500), None),
                  (0.40, (600, 1200, 2500), (400, 2000, 2600), None)], [(190, 200), (205, 195), (210, 160)], loud=False)
comein = voice([(0.22, (640, 1190, 2390), (600, 1100, 2400), 'k'), (0.36, (400, 2000, 2600), (380, 2100, 2600), None)],
               [(190, 185), (200, 165)], loud=False)
for ts in [7.4, 10.4]:
    add(allright, ts, -0.6, 0.40, "voice: it's all right (soft)")
add(comein, 26.4, -0.6, 0.40, 'voice: come in (soft)')


def flutter(d):
    n = int(d * SR); tt = np.arange(n) / SR
    return bandnoise(d, 200, 2500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 11 * tt))) * env(n, 0.05, 0.2)


for (a, b) in [(7.4, 10.2), (10.4, 11.6), (26.4, 27.6)]:
    add(flutter(b - a), a, -0.3, 0.06, 'butterfly flutter')
add(sweepnoise(0.22, 3000, 600) * 0.5, T['watch2'], 0.5, 0.25, 'paper whoosh: the card turns back to look')
add(np.sin(2 * np.pi * np.cumsum(np.geomspace(700, 1100, int(0.25 * SR))) / SR) * env(int(0.25 * SR), 0.03, 0.1), T['watch2'] + 0.35, 0.5, 0.05, 'small rising whine')

# ------------------------------------------------------------------ the approach: a pad on every footfall, from the score's distance
xs = np.array([f['dog']['x'] for f in SF])
dist = np.concatenate([[0], np.cumsum(np.abs(np.diff(xs)))])
STRIDE = 0.55
steps = np.nonzero(np.diff(np.floor(dist / (STRIDE / 2))) > 0)[0]
for k, i in enumerate(steps):
    if i < EV['approach']:
        continue
    pan = (X0 + K * xs[i]) / W * 2 - 1
    add(mix(thump(95 + 10 * (k % 2), 0.09, 0.15) * 0.7, bandnoise(0.03, 800, 3000) * 0.05), i / FPS, pan, 0.28,
        'paws on boards' if k == 0 else None)
add(mix(thump(65, 0.35, 0.3), sweepnoise(0.3, 900, 200) * 0.4), T['lie'] + 0.4, -0.1, 0.6, 'flump: lies down across the sill')
add(bandnoise(0.01, 3000, 9000), 610 / FPS, 0.0, 0.2, 'tick: the camera cuts in')
add(np.sin(2 * np.pi * np.cumsum(np.geomspace(600, 950, int(0.35 * SR))) / SR) * env(int(0.35 * SR), 0.03, 0.12), 26.7, -0.1, 0.05, 'small whine: looks in')
add(sweepnoise(0.8, 1500, 250) * np.linspace(1, 0, int(0.8 * SR)) * 0.5, 28.4, -0.1, 0.25, 'sigh: chin on paws')

# ------------------------------------------------------------------ end card
add(thump(80, 0.3, 0.4), 35.05, 0.0, 0.5, 'end card lands', scene=False)
add(np.sin(2 * np.pi * np.cumsum(np.geomspace(300, 900, int(0.15 * SR))) / SR) * env(int(0.15 * SR), 0.005, 0.05), 37.3, 0.0, 0.12, 'pop', scene=False)

# duck the crickets a little under the lie-down (the held moment) — done by a gain envelope on the master
mx = max(np.abs(L).max(), np.abs(R).max())
L /= mx; R /= mx
# gentle tape-ish compression so the dusk is audible under the gags
L = np.tanh(2.6 * L) / np.tanh(2.6) * 0.89; R = np.tanh(2.6 * R) / np.tanh(2.6) * 0.89
fade = np.ones(len(L)); fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR))
L *= fade; R *= fade
st = np.stack([L, R], 1)
pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
with wave.open(os.path.join(CACHE, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
json.dump(sorted(log, key=lambda e: e['t_film']), open(os.path.join(CACHE, 'sound_events.json'), 'w'), indent=1)
print('sound ok', len(log), 'events')
