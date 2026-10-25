"""SCION 09 · Igarashi — the sound, synthesized here (numpy) plus speech from flite (ffmpeg's libflite, voice 'slt').
python3 build/sound.py  ->  build/cache/sound.wav (48 kHz stereo, 38 s: 3 s title, 32 s scene, 3 s end card) and
                            build/cache/sound_levels.json (measured: call vs soft voice vs room tone, in dBFS RMS)
Reads build/cache/events.json (written by build/events.js from the rig: every paw that lands on the boards, the sit,
the rise, the lie-down, tail thumps) so that what is heard is what the feet did.
"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
SR = 48000
PRE = 3.0
DUR = 38.0
N = int(SR * DUR)
rng = np.random.default_rng(9)
L = np.zeros(N); R = np.zeros(N)
X0, S = 320, 190


def pan_of(xs):  # screen x -> (gl, gr)
    p = np.clip(xs / 1280, 0, 1)
    return np.cos(p * np.pi / 2), np.sin(p * np.pi / 2)


def put(sig, t, xs=640, g=1.0):
    i0 = int((PRE + t) * SR)
    if i0 >= N: return
    sig = sig[:N - i0]
    gl, gr = pan_of(xs)
    L[i0:i0 + len(sig)] += sig * g * gl
    R[i0:i0 + len(sig)] += sig * g * gr


def env(n, a, d):
    e = np.ones(n); na = max(1, int(a * SR)); nd = max(1, int(d * SR))
    e[:na] = np.linspace(0, 1, na); e[-nd:] *= np.linspace(1, 0, nd); return e


def lp(x, fc):  # one-pole low-pass, run twice
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for _ in range(2):
        out = np.empty_like(x)
        # vectorized-ish IIR via scipy-free loop in chunks
        s = 0.0
        for i in range(len(x)):
            s = (1 - a) * x[i] + a * s; out[i] = s
        x = out
    return x


def bp_noise(n, f0, q, seed=0):
    # band noise made by FFT shaping (fast, no IIR loops)
    r = np.random.default_rng(seed)
    w = r.standard_normal(n)
    F = np.fft.rfft(w); fr = np.fft.rfftfreq(n, 1 / SR)
    F *= np.exp(-0.5 * ((fr - f0) / (f0 / q)) ** 2)
    y = np.fft.irfft(F, n); return y / (np.abs(y).max() + 1e-9)


def lowshape(x, fc):
    F = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); F /= np.sqrt(1 + (fr / fc) ** 4); return np.fft.irfft(F, len(x))


# ── room tone: dusk air, a far road, crickets that thicken as it gets dark ──
air = lowshape(rng.standard_normal(N), 380) ; air /= np.abs(air).max()
L += air * 0.010; R += np.roll(air, 2400) * 0.010
t = np.arange(N) / SR
for k, (f, rate, x) in enumerate([(4300, 13.0, 1000), (4700, 15.5, 1180), (3900, 11.0, 860)]):
    chirp = np.sin(2 * np.pi * f * t) * (np.sin(2 * np.pi * rate * t) > 0.55) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.21 + 0.05 * k) * t + k) > 0.35)
    dusk = np.clip((t - PRE) / 32, 0, 1) * 0.6 + 0.4
    c = lowshape(chirp * dusk, 6000) * 0.0045
    gl, gr = pan_of(x); L += c * gl; R += c * gr

# ── speech ──
def flite(text, voice='slt'):
    f = os.path.join(CACHE, 'tts.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"flite=text='{text}':voice={voice}", '-ar', str(SR), '-ac', '1', f], check=True)
    w = wave.open(f); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; return a


def voice(text, t0, kind):
    a = flite(text)
    a = a / (np.abs(a).max() + 1e-9)
    if kind == 'call':
        g = 0.42
        # a little porch reverb
        y = a.copy()
        for d, gg in [(0.031, .35), (0.067, .22), (0.113, .14)]:
            k = int(d * SR); y[k:] += a[:-k] * gg
        a = y / np.abs(y).max()
    else:
        g = 0.10
        a = lowshape(a, 2200)
        breath = lowshape(rng.standard_normal(len(a)), 3000) * np.convolve(np.abs(a), np.ones(400) / 400, 'same') * 0.6
        a = a + breath
        a = a / np.abs(a).max()
    put(a, t0, X0 - 1.0 * S if t0 > 5 else X0 - 0.28 * S, g)
    return a, g


levels = {'call': [], 'soft': []}
for t0, txt, kind in [(1.02, 'Come here.', 'call'), (3.42, 'Come here!', 'call'), (7.45, "It's all right.", 'soft'),
                      (10.45, "It's all right.", 'soft'), (26.42, 'Come in.', 'soft')]:
    voice(txt, t0, kind)
    levels[kind].append((t0, t0 + 1.1))

# ── the dog's paws, the sit, the rise, the lie, the tail ──
ev = json.load(open(os.path.join(CACHE, 'events.json')))


def paw(strength=1.0, seed=0):
    n = int(0.06 * SR)
    click = bp_noise(n, 3200, 3, seed) * env(n, 0.001, 0.05) * np.exp(-np.arange(n) / (0.006 * SR))
    knock = np.sin(2 * np.pi * 180 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.012 * SR))
    return (click * 0.6 + knock * 0.5) * strength


for k, e in enumerate(ev['paws']):
    put(paw(e.get('s', 1.0), k), e['t'], e['x'], 0.05)
for e in ev['thumps']:
    n = int(0.35 * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * (70 + 30 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 9)
    rustle = lowshape(rng.standard_normal(n), 1200) * np.exp(-tt * 6) * 0.4
    put((body + rustle) * e.get('s', 1.0), e['t'], e['x'], 0.16)
for e in ev['sighs']:
    n = int(1.1 * SR); tt = np.arange(n) / SR
    s = lowshape(rng.standard_normal(n), 900) * np.sin(np.pi * np.clip(tt / 1.1, 0, 1)) ** 2
    put(s / np.abs(s).max(), e['t'], e['x'], 0.05)
for e in ev['tail']:
    n = int(0.08 * SR); tt = np.arange(n) / SR
    put(np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 40) + lowshape(rng.standard_normal(n), 600) * np.exp(-tt * 30) * 0.3, e['t'], e['x'], 0.05)
for e in ev['whine']:
    n = int(0.55 * SR); tt = np.arange(n) / SR
    f = 980 - 260 * tt / 0.55 + 18 * np.sin(2 * np.pi * 7 * tt)
    w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.55) ** 1.5
    put(lowshape(w, 2500), e['t'], e['x'], 0.035)

# ── the person: steps aside, the crate takes the weight ──
for t0, x in [(5.52, X0 - 0.5 * S), (5.80, X0 - 1.0 * S)]:
    n = int(0.12 * SR); tt = np.arange(n) / SR
    put(np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 30) + lowshape(rng.standard_normal(n), 900) * np.exp(-tt * 25) * .3, t0, x, 0.12)
n = int(0.5 * SR); tt = np.arange(n) / SR
put(lowshape(np.sign(np.sin(2 * np.pi * (60 + 25 * tt) * tt)) * rng.uniform(.6, 1, n), 1400) * np.sin(np.pi * tt / 0.5), 6.06, X0 - 1.25 * S, 0.035)

# ── the door: a creak as it swings in, then the light: a warm low chord that stays ──
n = int(0.75 * SR); tt = np.arange(n) / SR
f = 150 + 120 * tt / 0.75 + 30 * np.sin(2 * np.pi * 3 * tt)
pulses = (np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.97).astype(float) * rng.uniform(.5, 1, n)
creak = lowshape(np.convolve(pulses, np.exp(-np.arange(200) / 30), 'same'), 2400) * np.sin(np.pi * tt / 0.75)
put(creak / np.abs(creak).max(), 6.2, X0 + 0.3 * S, 0.06)
pad = np.zeros(N); tg = np.arange(N) / SR - PRE
light = np.clip((tg - 6.25) / 1.4, 0, 1) ** 1.5
for fq, a in [(110.0, .5), (164.8, .35), (220.0, .25), (277.2, .16), (329.6, .10)]:
    pad += a * np.sin(2 * np.pi * fq * tg + 0.3 * np.sin(2 * np.pi * 0.11 * tg))
# the chord brightens a little when the dog turns back (7.46), when it comes (14.7) and when it settles (24)
sw = 1 + 0.25 * np.clip((tg - 14.7) / 3, 0, 1) - 0.1 * np.clip((tg - 28.5) / 3, 0, 1)
pad = pad * light * sw * 0.0105
end = np.clip((35.0 - tg) / 0.8, 0, 1); pad *= np.where(tg > 34.2, end, 1)
L += pad; R += pad * 0.95
# two soft plucks: when it turns back to look, and when it looks in
for t0, fq in [(7.47, 659.3), (26.45, 587.3)]:
    n = int(1.6 * SR); tt = np.arange(n) / SR
    pl = (np.sin(2 * np.pi * fq * tt) + .3 * np.sin(2 * np.pi * 2 * fq * tt)) * np.exp(-tt * 3.2)
    put(pl, t0, X0 + 0.5 * S, 0.035)

# fades: title card has only air; end card fades out
tg = np.arange(N) / SR
fade = np.clip(tg / 1.5, 0, 1) * np.clip((DUR - tg) / 1.5, 0, 1)
L *= fade; R *= fade
mix = np.stack([L, R], 1)
peak = np.abs(mix).max()
if peak > 0.95: mix *= 0.95 / peak


def rms_db(a, b):
    seg = mix[int((PRE + a) * SR):int((PRE + b) * SR)].mean(1)
    return float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-12))


lv = {'call_dbfs_rms': [round(rms_db(a, b), 1) for a, b in levels['call']], 'soft_dbfs_rms': [round(rms_db(a, b), 1) for a, b in levels['soft']],
      'room_tone_dbfs_rms': round(rms_db(12.2, 14.4), 1), 'room_tone_before_light_dbfs_rms': round(rms_db(0.1, 0.9), 1), 'peak_dbfs': round(float(20 * np.log10(np.abs(mix).max())), 1)}
lv['soft_minus_call_db'] = round(max(lv['soft_dbfs_rms']) - min(lv['call_dbfs_rms']), 1)
json.dump(lv, open(os.path.join(CACHE, 'sound_levels.json'), 'w'), indent=1)
print(lv)
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
w = wave.open(os.path.join(CACHE, 'sound.wav'), 'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
