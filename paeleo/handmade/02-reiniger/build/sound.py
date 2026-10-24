"""Sound: a small pit band for the shadow theatre, synthesized in numpy (no samples).

The voices are instruments (silent-film convention): the person's commands are a muted horn,
her soft words a flute; the dog's theme a clarinet; its paws pizzicato plucks driven by the paw
contacts of the render's contact solver (build/out/events.json), panned to the dog's screen x;
the door is a harp glissando timed to the re-timed Straight Talk swing; dusk is crickets.
"""
import json, math, os, wave
import numpy as np
from theatre import OUT, FPS, X

SR = 48000
DUR = 38.0
OFF = 3.0                       # scene time 0 = 3 s into the film (after the title card)
N = int(SR * DUR)
buf = np.zeros((N, 2), np.float64)
rng = np.random.default_rng(1926)

def hz(name):
    names = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6,
             'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)

def env(n, a, r, sustain=1.0):
    e = np.ones(n) * sustain
    na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, sustain, na) if na < n else np.linspace(0, sustain, n)[:na]
    if nr < n: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def put(sig, t, pan=0.0, gain=1.0, scene=True):
    t0 = t + (OFF if scene else 0.0)
    i0 = int(t0 * SR)
    if i0 >= N: return
    sig = sig[:N - i0]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[i0:i0 + len(sig), 0] += sig * gain * l * 1.41
    buf[i0:i0 + len(sig), 1] += sig * gain * r * 1.41

def tt(d): return np.arange(int(d * SR)) / SR

def pluck(f, d=1.6, bright=1.0):
    t = tt(d); s = np.zeros_like(t)
    for k in range(1, 9):
        s += (1 / k ** (1.4 - 0.4 * bright)) * np.sin(2 * math.pi * f * k * t) * np.exp(-t * (2.2 + 1.6 * k))
    s *= np.minimum(1, t / 0.003)
    return s / 2.2

def organ(fs, d, a=0.6, r=1.2, vib=0.0):
    t = tt(d); s = np.zeros_like(t)
    for f in fs:
        for det in (-0.6, 0.6):
            ph = 2 * math.pi * (f + det) * t + vib * np.sin(2 * math.pi * 5.0 * t)
            for k, amp in enumerate([1, 0.45, 0.28, 0.14, 0.08, 0.04], 1):
                s += amp * np.sin(k * ph)
    s *= env(len(t), a, r) / (len(fs) * 4.0)
    return s

def horn(f, d, a=0.05, r=0.18, bright=1.0):
    t = tt(d); s = np.zeros_like(t)
    br = np.minimum(1, t / 0.08) * bright
    for k in range(1, 10):
        s += (0.9 ** k) * (br ** (k / 3)) * np.sin(2 * math.pi * f * k * t + 0.3 * k)
    s *= env(len(t), a, r) * (1 + 0.04 * np.sin(2 * math.pi * 5.5 * t))
    return s / 4.0

def flute(f, d, a=0.09, r=0.3):
    t = tt(d)
    vib = 1 + 0.006 * np.sin(2 * math.pi * 5.0 * t) * np.minimum(1, t / 0.4)
    ph = 2 * math.pi * f * np.cumsum(vib) / SR
    s = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    noise = bandnoise(len(t), f * 0.9, f * 1.4) * 0.12
    return (s + noise) * env(len(t), a, r) / 1.4

def clarinet(f, d, a=0.08, r=0.35):
    t = tt(d)
    vib = 1 + 0.004 * np.sin(2 * math.pi * 4.6 * t) * np.minimum(1, t / 0.6)
    ph = 2 * math.pi * f * np.cumsum(vib) / SR
    s = np.sin(ph) + 0.4 * np.sin(3 * ph) + 0.2 * np.sin(5 * ph) + 0.08 * np.sin(7 * ph)
    return s * env(len(t), a, r) / 1.8

def bell(f, d=2.5):
    t = tt(d); s = np.zeros_like(t)
    for ratio, amp, dec in [(1, 1, 1.2), (2.76, 0.5, 2.5), (5.4, 0.25, 4), (8.93, 0.12, 6)]:
        s += amp * np.sin(2 * math.pi * f * ratio * t) * np.exp(-t * dec)
    return s * np.minimum(1, t / 0.002) / 2.0

def cello(fs, d, a=0.4, r=0.8, trem=0.0):
    t = tt(d); s = np.zeros_like(t)
    for f in fs:
        ph = 2 * math.pi * f * t + 0.002 * f * np.sin(2 * math.pi * 5.2 * t)
        for k in range(1, 12):
            s += (1 / k) * np.sin(k * ph) * (0.75 ** k)
    if trem: s *= 1 - trem * (0.5 + 0.5 * np.sin(2 * math.pi * 9 * t))
    return s * env(len(t), a, r) / (2.0 * len(fs))

def bandnoise(n, lo, hi):
    x = rng.normal(0, 1, n)
    X_ = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    X_[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X_, n)
    return y / (np.abs(y).max() + 1e-9)

def thump(d=0.09):
    n = int(d * SR); y = bandnoise(n, 60, 500) * np.exp(-np.arange(n) / SR * 45)
    return y

# ------------------------------------------------------------------ the cue sheet
ev = json.load(open(os.path.join(OUT, 'events.json')))
rig = json.load(open(os.path.join(OUT, 'rig.json')))
def dog_pan(i):
    return float(np.clip((X(rig[min(i, len(rig) - 1)]['dog']['x']) - 640) / 640, -1, 1)) * 0.8
P_PERSON = -0.55

# title: the harp sets the stage, the reed organ opens a fifth
for k, n in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4', 'D5']):
    put(pluck(hz(n), 2.2), 0.35 + k * 0.32, pan=-0.3 + 0.12 * k, gain=0.30, scene=False)
put(organ([hz('D2'), hz('A2')], 4.6, a=1.5, r=0.4), 1.6, gain=0.28, scene=False)

# 0-1 s: the organ fifth waits
# 1.0 the call: "Come here." -- a muted horn, falling, firm
put(horn(hz('A4'), 0.30), 1.00, P_PERSON, 0.42); put(horn(hz('D4'), 0.55), 1.30, P_PERSON, 0.42)
put(organ([hz('D2'), hz('A2')], 1.1, a=0.02, r=1.0), 1.0, gain=0.10)  # the organ breaks off
# retreat: the low strings tremble, paws pluck downward
put(cello([hz('C#2'), hz('D2')], 1.6, a=0.15, r=0.6, trem=0.5), 1.05, gain=0.35)
pitches_down = ['A3', 'G#3', 'G3', 'F#3', 'F3', 'E3', 'Eb3', 'D3', 'C#3', 'C3']
k = 0
for e in ev['paws']:
    if e['kind'] != 'touch': continue
    i = e['i']; t = i / FPS
    put(thump(), t, dog_pan(i), 0.10)
    if 20 <= i <= 60:
        put(pluck(hz(pitches_down[min(k, 9)]), 0.9, 0.6), t, dog_pan(i), 0.30); k += 1
# 2.33 watch: a held breath, one harmonic
put(bell(hz('A5'), 2.0), 2.35, 0.4, 0.10)
# 3.4 the second call and the reach: louder, with a clashing stab
put(horn(hz('A4'), 0.28, bright=1.3), 3.40, P_PERSON, 0.55); put(horn(hz('D4'), 0.6, bright=1.3), 3.68, P_PERSON, 0.55)
put(organ([hz('D3'), hz('Eb3'), hz('A3')], 1.0, a=0.03, r=0.5), 3.45, gain=0.32)
# 3.42 the refusal: a low sigh down a semitone; the turn of the body is a soft drum
put(cello([hz('E3')], 0.6, a=0.06, r=0.2), 3.45, 0.5, 0.35); put(cello([hz('Eb3')], 1.2, a=0.05, r=0.6), 3.95, 0.5, 0.35)
put(thump(0.25) * 1.0, 4.05, 0.6, 0.5)
# back turned, lying: D minor in the low strings
put(cello([hz('D2'), hz('F2'), hz('A2')], 3.4, a=0.8, r=1.2), 4.4, gain=0.30)
# 5.4 she kneels: the organ softens to G minor
put(organ([hz('G2'), hz('D3'), hz('Bb3')], 1.6, a=0.5, r=0.8), 5.3, gain=0.16)
# 6.2 the door opens: harp glissando on the archive swing, a warm D major swells
for k, n in enumerate(['D3', 'F#3', 'A3', 'D4', 'F#4', 'A4', 'D5', 'F#5', 'A5', 'D6']):
    put(pluck(hz(n), 2.6, 1.2), 6.2 + 0.11 * k * (1 + 0.04 * k), -0.6 + 0.12 * k, 0.24)
put(organ([hz('D3'), hz('F#3'), hz('A3'), hz('D4')], 8.4, a=1.2, r=2.0, vib=0.002), 6.3, gain=0.26)
# 6.8 the hand offered low: a single bell
put(bell(hz('F#5'), 2.0), 6.85, P_PERSON, 0.12)
# 7.4 "It's all right." -- the flute, softly
for (n, a, d) in [('F#5', 7.40, 0.42), ('E5', 7.80, 0.42), ('D5', 8.20, 1.1)]:
    put(flute(hz(n), d), a, P_PERSON, 0.30)
# 7.46 the dog turns back to look: the clarinet asks
put(clarinet(hz('A3'), 0.35), 7.50, dog_pan(180), 0.30); put(clarinet(hz('E4'), 0.9), 7.82, dog_pan(180), 0.30)
put(pluck(hz('B4'), 1.0), 8.15, dog_pan(196), 0.16)
# 9.4-14.7 waiting: a slow harp ostinato and the organ pad; the second "It's all right"
pad_t = 9.4
put(organ([hz('D3'), hz('A3'), hz('F#4')], 5.6, a=1.5, r=1.5), 9.2, gain=0.17)
for k in range(9):
    n = ['D3', 'A3', 'F#4', 'A3'][k % 4]
    put(pluck(hz(n), 1.4, 0.7), 9.5 + k * 0.6, -0.1, 0.14)
for (n, a, d) in [('A5', 10.40, 0.4), ('F#5', 10.78, 0.42), ('E5', 11.18, 0.4), ('D5', 11.55, 1.2)]:
    put(flute(hz(n), d), a, P_PERSON, 0.24)
for k, t in enumerate(np.arange(12.0, 14.7, 0.9)):
    put(cello([hz('D2')], 0.35, a=0.02, r=0.3), t, 0.0, 0.18 + 0.03 * k)
# 14.7 approach: each paw a rising note; the clarinet sings the dog's theme
scale = ['D3', 'E3', 'F#3', 'A3', 'B3', 'D4', 'E4', 'F#4', 'A4', 'B4', 'D5']
appr = [e for e in ev['paws'] if e['kind'] == 'touch' and 350 <= e['i'] <= 575]
for k, e in enumerate(appr):
    i = e['i']; prog = (i - 350) / 225.0
    n = scale[min(len(scale) - 1, int(prog * 8) + (k % 3))]
    put(pluck(hz(n), 1.0, 0.8), i / FPS, dog_pan(i), 0.13 + 0.06 * prog)
theme = [('D4', 1.4), ('E4', 0.7), ('F#4', 1.4), ('A4', 1.4), ('B4', 0.7), ('A4', 1.4), ('F#4', 0.7), ('E4', 1.0)]
t = 14.75
for n, d in theme:
    put(clarinet(hz(n), d + 0.1), t, dog_pan(int(t * FPS)), 0.22); t += d
put(organ([hz('G2'), hz('D3'), hz('B3')], 4.6, a=1.5, r=1.4), 15.0, gain=0.12)
put(organ([hz('A2'), hz('E3'), hz('C#4')], 4.6, a=1.4, r=1.5), 19.2, gain=0.12)
# 23.79 lies down across the sill: the harp rolls the D major home; a sigh
for k, n in enumerate(['D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4']):
    put(pluck(hz(n), 3.0, 0.9), 23.80 + 0.07 * k, -0.2 + 0.06 * k, 0.22)
put(clarinet(hz('D4'), 2.2, r=1.4), 23.75, dog_pan(570), 0.20)
sigh = bandnoise(int(0.8 * SR), 300, 1600) * np.sin(np.linspace(0, math.pi, int(0.8 * SR))) ** 2
put(sigh, 24.25, dog_pan(580), 0.07)
put(organ([hz('D3'), hz('A3'), hz('D4'), hz('F#4')], 3.0, a=1.0, r=1.0), 24.0, gain=0.16)
# 26.4 "Come in." -- the flute rises, an invitation
put(flute(hz('E5'), 0.4), 26.40, P_PERSON, 0.28); put(flute(hz('A5'), 1.0), 26.78, P_PERSON, 0.28)
# 26.5-28 it looks in: a suspended shimmer; the tail wag brushes the floor
for k, n in enumerate(['D5', 'G5', 'A5', 'D6']):
    put(bell(hz(n), 3.0), 26.55 + 0.18 * k, -0.05 + 0.05 * k, 0.08)
put(organ([hz('D3'), hz('G3'), hz('A3')], 1.8, a=0.4, r=0.8), 26.5, gain=0.13)
for i in range(630, 700):
    w = rig[i]['dog']['wag']
    if w > 0.3 and i % 8 == 0:
        put(bandnoise(int(0.07 * SR), 800, 4000) * np.exp(-np.arange(int(0.07 * SR)) / SR * 50), i / FPS, dog_pan(i), 0.025 * w)
# 28.0 it settles and stays: the chord resolves open (D, A, E, F#) and stays
put(organ([hz('D3'), hz('A3'), hz('E4'), hz('F#4')], 7.6, a=1.2, r=3.5), 28.1, gain=0.20)
put(pluck(hz('D2'), 4.0, 0.6), 28.2, 0.0, 0.25)
put(pluck(hz('A4'), 3.0, 0.6), 29.6, 0.1, 0.10)
put(pluck(hz('F#4'), 3.0, 0.6), 30.5, 0.1, 0.09)
# end card: one last harp D, the crickets carry out
put(pluck(hz('D4'), 3.0, 0.5), 35.3, 0.0, 0.12, scene=False)

# ------------------------------------------------------------------ dusk: crickets and air
t = np.arange(N) / SR
for (f0, rate, pan, ph, g) in [(4700, 1.7, -0.7, 0.0, 0.020), (5200, 2.3, 0.6, 0.4, 0.016), (4300, 1.3, 0.2, 0.8, 0.012)]:
    car = np.sin(2 * math.pi * f0 * t)
    chirp = (np.sin(2 * math.pi * 30 * t) > 0.2).astype(float)
    gate = ((t * rate + ph) % 1.0) < 0.12
    am = chirp * gate
    am = np.convolve(am, np.ones(48) / 48, mode='same')
    ramp = np.clip((t - 1.0) / 4.0, 0, 1) * np.clip((DUR - t) / 2.0, 0, 1)
    s = car * am * ramp * g
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[:, 0] += s * l; buf[:, 1] += s * r
air = bandnoise(N, 80, 700) * 0.012 * np.clip(t / 2.0, 0, 1) * np.clip((DUR - t) / 2.0, 0, 1)
buf[:, 0] += air; buf[:, 1] += np.roll(air, 900)

# a small room: two early reflections
for d, g in [(0.031, 0.18), (0.057, 0.12)]:
    k = int(d * SR)
    buf[k:, 0] += buf[:-k, 1] * g; buf[k:, 1] += buf[:-k, 0] * g
# fade in and out, normalize
fade = np.clip(t / 0.3, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1)
buf *= fade[:, None]
rms = np.sqrt((buf ** 2).mean()); buf *= 0.13 / rms
buf = np.tanh(buf * 1.4) / 1.4                     # gentle limiter so the stab does not set the level
peak = np.abs(buf).max(); buf *= min(1.0, 0.92 / peak)
pcm = (buf * 32767).astype(np.int16)
with wave.open(os.path.join(OUT, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('sound.wav', DUR, 's, peak normalized from', round(peak, 3))
