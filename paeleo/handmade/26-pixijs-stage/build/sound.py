"""SCION-26 · the sound, synthesized (numpy only): a formant voice, dusk room tone, paws on boards timed to the rendered
foot contacts, the door, the person's steps and the crate, the dog lying down and sighing, and the warm room that spills
out when the door opens.  Reads build/cache/measure.json (foot positions per scene frame, measured from the stage).
Writes build/cache/sound.wav (38.0 s, 48 kHz stereo) and build/cache/sound.json (levels: calls vs soft voice vs room tone)."""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
SR = 48000
DUR = 38.0
OFF = 3.0                      # scene starts after the 3 s title card
N = int(SR * DUR)
rng = np.random.default_rng(2626)
L = np.zeros(N); Rch = np.zeros(N)
layers = {}

def place(sig, t, gain=1.0, pan=0.0, name=None):
    i = int(t * SR)
    if i >= N: return
    s = sig[: N - i] * gain
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    L[i:i + len(s)] += s * l * 1.414; Rch[i:i + len(s)] += s * r * 1.414
    if name:
        a = layers.setdefault(name, np.zeros(N)); a[i:i + len(s)] += s

def resonator(x, f, bw):
    """two-pole resonator with per-sample frequency/bandwidth arrays"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    T = 1.0 / SR
    C = -np.exp(-2 * np.pi * bw * T); B = 2 * np.exp(-np.pi * bw * T) * np.cos(2 * np.pi * f * T); A = 1 - B - C
    for n in range(len(x)):
        v = A[n] * x[n] + B[n] * y1 + C[n] * y2
        y2 = y1; y1 = v; y[n] = v
    return y

def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); p = 0.0
    for n in range(len(x)): p = (1 - a) * x[n] + a * p; y[n] = p
    return y

def lp_fast(x, fc, passes=2):
    a = math.exp(-2 * math.pi * fc / SR)
    # vectorised one-pole via scipy-free trick: use cumulative filtering in blocks (approximate with FFT)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / (1 + (f / fc) ** (2 * passes))
    return np.fft.irfft(X * H, len(x))

def bandpass_fft(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    H = np.exp(-0.5 * (np.log(np.maximum(f, 1) / math.sqrt(lo * hi)) / (math.log(hi / lo) / 2)) ** 2)
    return np.fft.irfft(X * H, len(x))

# ------------------------------------------------------------------ formant voice
PH = {  # F1 F2 F3, voiced?, noise kind
    'a': (730, 1090, 2440), 'ʌ': (640, 1190, 2390), 'ɪ': (400, 1920, 2560), 'ə': (500, 1500, 2500), 'ɔ': (570, 840, 2410),
    'i': (300, 2250, 2950), 'm': (280, 1000, 2200), 'n': (280, 1650, 2600), 'l': (360, 1100, 2650), 'r': (420, 1250, 1650),
    'ɛ': (550, 1770, 2490), 'h': (500, 1500, 2500), 'k': (500, 1700, 2500), 't': (400, 1800, 2600), 's': (400, 1800, 2600),
}
def voice(seq, f0, gain_curve=None, breath=0.05, tilt=1.0):
    """seq: list of (phoneme, dur_s, amp). f0: (start, peak, end) Hz contour."""
    total = sum(d for _, d, _ in seq); n = int(total * SR)
    tt = np.arange(n) / SR
    # f0 contour: rise to peak at 35 %, fall to end
    f0c = np.interp(tt, [0, total * 0.35, total], [f0[0], f0[1], f0[2]]) * (1 + 0.006 * np.sin(2 * np.pi * 5.3 * tt))
    ph = np.cumsum(f0c / SR) % 1.0
    glott = np.where(ph < 0.6, np.sin(np.pi * ph / 0.6) ** 2, 0.0)          # Rosenberg-like pulse
    glott = np.diff(glott, prepend=0) * 12
    noise = rng.standard_normal(n)
    F = np.zeros((3, n)); amp = np.zeros(n); voiced = np.zeros(n); fric = np.zeros(n); burst = np.zeros(n)
    t0 = 0; prevF = None
    for p, d, a in seq:
        i0, i1 = int(t0 * SR), int((t0 + d) * SR)
        f = PH[p]
        for k in range(3):
            start = prevF[k] if prevF else f[k]
            ramp = min(i1 - i0, int(0.05 * SR))
            F[k, i0:i1] = f[k]; F[k, i0:i0 + ramp] = np.linspace(start, f[k], ramp)
        env = np.ones(i1 - i0)
        amp[i0:i1] = a * env
        if p in 'kt':
            voiced[i0:i1] = 0; burst[i0 + int((i1 - i0) * 0.6): i1] = 1.0
        elif p == 's':
            voiced[i0:i1] = 0; fric[i0:i1] = 1.0
        elif p == 'h':
            voiced[i0:i1] = 0.15; fric[i0:i1] = 0.0; burst[i0:i1] = 0.5
        else:
            voiced[i0:i1] = 1.0
        prevF = f; t0 += d
    # smooth envelopes (20 ms)
    k = int(0.02 * SR); ker = np.ones(k) / k
    amp = np.convolve(amp, ker, 'same'); voiced = np.convolve(voiced, ker, 'same'); burst = np.convolve(burst, ker / 2, 'same')
    src = glott * voiced * (1 - breath) + noise * (breath * voiced * 0.35 + burst * 0.6)
    y = src
    for kk, bw in zip(range(3), (90, 110, 170)):
        y = resonator(y, F[kk], np.full(n, bw))
    hiss = bandpass_fft(noise, 4500, 8500) * fric * 0.5
    y = y / (np.max(np.abs(y)) + 1e-9) + hiss
    y = y * amp
    if tilt != 1.0: y = lp_fast(y, 2600 * tilt)
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.01 * SR), (n - np.arange(n)) / (0.03 * SR)))
    return y * fade

def norm_rms(x, db):
    r = np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2)) if np.any(np.abs(x) > 1e-4) else 1
    return x * (10 ** (db / 20) / r)

VOICE_PAN = -0.45
call1 = norm_rms(voice([('k', .07, 1), ('ʌ', .17, 1), ('m', .11, .8), ('h', .07, .6), ('ɪ', .2, 1), ('ə', .2, .8)], (150, 210, 150), breath=0.04), -13)
call2 = norm_rms(voice([('k', .06, 1), ('ʌ', .15, 1), ('m', .1, .8), ('h', .06, .6), ('i', .24, 1), ('ə', .18, .8)], (170, 240, 160), breath=0.03), -11.5)
call1b = norm_rms(voice([('k', .06, 1), ('ʌ', .14, 1), ('m', .1, .8), ('ɔ', .2, 1), ('n', .14, .7)], (160, 200, 150), breath=0.04), -14)
soft1 = norm_rms(voice([('ɪ', .1, .8), ('t', .05, .6), ('s', .1, .5), ('ɔ', .2, 1), ('l', .12, .8), ('r', .08, .8), ('a', .18, 1), ('ɪ', .1, .8), ('t', .08, .5)], (125, 140, 105), breath=0.35, tilt=0.8), -27)
soft2 = norm_rms(voice([('ɔ', .2, 1), ('l', .12, .8), ('r', .08, .8), ('a', .2, 1), ('ɪ', .1, .8), ('t', .08, .5)], (120, 135, 100), breath=0.38, tilt=0.8), -28)
soft3 = norm_rms(voice([('k', .06, .8), ('ʌ', .16, 1), ('m', .1, .8), ('ɪ', .18, 1), ('n', .2, .8)], (120, 132, 105), breath=0.36, tilt=0.8), -27)
for sig, t, name in [(call1, 1.04, 'call'), (call1b, 1.75, 'call'), (call2, 3.45, 'call'), (call1b, 4.05, 'call'),
                     (soft1, 7.45, 'soft'), (soft2, 10.45, 'soft'), (soft3, 26.45, 'soft')]:
    place(sig, OFF + t, 1.0, VOICE_PAN, name)

# ------------------------------------------------------------------ room tone: wind + crickets, through the whole film
t_all = np.arange(N) / SR
wind = lp_fast(rng.standard_normal(N), 380) * (0.6 + 0.4 * np.sin(2 * np.pi * t_all / 9.0 + 1))
wind = norm_rms(wind, -46)
crick = np.zeros(N)
for c in range(3):
    f = 4300 + 350 * c; rate = 3.1 + 0.7 * c
    gate = (np.sin(2 * np.pi * rate * t_all + c) > 0.55).astype(float) * (np.sin(2 * np.pi * 0.11 * t_all + c * 2) > -0.2)
    gate = np.convolve(gate, np.ones(200) / 200, 'same')
    crick += np.sin(2 * np.pi * f * t_all) * gate * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t_all))
crick = norm_rms(crick, -50)
fadeio = np.clip(np.minimum(t_all / 1.5, (DUR - t_all) / 2.0), 0, 1)
place(wind * fadeio, 0, 1.0, 0.2, 'room'); place(crick * fadeio, 0, 1.0, 0.6, 'room')

# ------------------------------------------------------------------ the room inside (after the door opens): a warm low chord
def pad(dur, freqs, att, rel):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * tt + k) * (0.6 ** k) for k, f in enumerate(freqs))
    env = np.minimum(1, tt / att) * np.minimum(1, (dur - tt) / rel)
    return y * env * (1 + 0.15 * np.sin(2 * np.pi * 0.3 * tt))
room = norm_rms(lp_fast(pad(28.5, [110, 164.8, 220, 277.2], 2.5, 3.0), 900), -36)
place(room, OFF + 6.3, 1.0, -0.6, 'pad')

# ------------------------------------------------------------------ door: latch + creak 6.2-7.0
def creak(dur, f0a, f0b):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.interp(tt, [0, dur * 0.4, dur], [f0a, f0b * 1.2, f0b]) * (1 + 0.04 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)))
    ph = np.cumsum(f / SR); saw = 2 * (ph % 1) - 1
    y = bandpass_fft(saw, 600, 2600) + 0.3 * bandpass_fft(rng.standard_normal(n), 900, 3000)
    env = np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.15) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * tt) ** 2)
    return y * env
latch = bandpass_fft(rng.standard_normal(int(0.04 * SR)), 1500, 6000) * np.exp(-np.arange(int(0.04 * SR)) / (0.006 * SR))
place(norm_rms(latch, -24), OFF + 6.17, 1.0, -0.55, 'door')
place(norm_rms(creak(0.85, 70, 45), -30), OFF + 6.22, 1.0, -0.55, 'door')

# ------------------------------------------------------------------ knocks: paws, person steps, crate, lying down
def knock(f, dec, n_ms=80, noise=0.4):
    n = int(n_ms / 1000 * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt) * np.exp(-tt / dec) + noise * bandpass_fft(rng.standard_normal(n), 1500, 5000) * np.exp(-tt / 0.004)
    return y
meas = json.load(open(os.path.join(CACHE, 'measure.json')))
sc = meas['scene']
paws = 0
for leg in range(4):
    for i in range(1, len(sc)):
        y0, y1 = sc[i - 1]['feet'][leg][1], sc[i]['feet'][leg][1]
        if y0 > 0.012 and y1 <= 0.012:
            x = sc[i]['feet'][leg][0]
            pan = max(-1, min(1, (330 + 200 * x) / 640 - 1))
            g = 10 ** ((-34 + rng.uniform(-3, 2)) / 20)
            place(knock(rng.uniform(170, 230), 0.012, 60, 0.9) / 2, OFF + i / 24, g, pan, 'paws'); paws += 1
for ts in (5.5, 5.8, 6.1):
    place(knock(95, 0.03, 120, 0.3) / 2, OFF + ts, 10 ** (-27 / 20), -0.8, 'steps')
place(norm_rms(creak(0.4, 90, 60), -33), OFF + 6.55, 1.0, -0.8, 'crate')
place(knock(70, 0.06, 200, 0.2) / 2, OFF + 24.35, 10 ** (-28 / 20), -0.45, 'dog')
place(knock(70, 0.05, 160, 0.2) / 2, OFF + 4.75, 10 ** (-31 / 20), 0.75, 'dog')
# a sigh as it settles (exhale through the nose): filtered noise, falling
def sigh(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = bandpass_fft(rng.standard_normal(n), 300, 1800) * np.exp(-tt / (dur * 0.45)) * np.minimum(1, tt / 0.08)
    return y
place(norm_rms(sigh(1.1), -34), OFF + 28.9, 1.0, -0.45, 'dog')
place(norm_rms(sigh(0.9), -36), OFF + 6.0, 1.0, 0.75, 'dog')

# ------------------------------------------------------------------ write
mix = np.stack([L, Rch], 1)
peak = np.max(np.abs(mix));
if peak > 0.95: mix *= 0.95 / peak
pcm = (mix * 32767).astype(np.int16)
with wave.open(os.path.join(CACHE, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
def rms_db(name):
    a = layers.get(name)
    if a is None: return None
    v = a[np.abs(a) > 1e-4]
    return round(20 * math.log10(np.sqrt(np.mean(v ** 2)) + 1e-12), 2)
lv = {k: rms_db(k) for k in layers}
lv['soft_minus_call_dB'] = round(lv['soft'] - lv['call'], 2)
lv['soft_minus_room_dB'] = round(lv['soft'] - lv['room'], 2)
lv['paw_contacts'] = paws
json.dump(lv, open(os.path.join(CACHE, 'sound.json'), 'w'), indent=1)
print(json.dumps(lv))
