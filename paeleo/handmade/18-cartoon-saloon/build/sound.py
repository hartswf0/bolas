"""SCION 18 · the sound, synthesized from the same timeline the picture uses (numpy only; nothing recorded or fetched).
- voice: a formant voice (glottal pulse train through three moving resonators) speaking the syllables in cache/voice.json;
  calls are loud and lifted in pitch, the soft lines breathy and at least 6 dB quieter (measured below), above the room tone.
- dusk room tone: wind (filtered noise), crickets; the hearth's crackle inside.
- the door: a hinge creak (jittered FM) and a soft knock as it settles open at 6.2 s.
- the dog: paw taps on the boards from the gait solver's touch-downs (cache/events.json), the turn's scuffle, the thump of
  lying down, a sigh, and tail thumps on the sill while it wags lying down.
- music: a plucked (Karplus-Strong) harp in D dorian, sparse: title, the turn back to look, the arrival, the settling.
Writes cache/audio.wav (48 kHz stereo) and cache/levels.json (measured RMS levels)."""
import numpy as np, json, os, wave
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(H, 'cache')
SR = 48000; DUR = 38.0; OFF = 3.0  # scene t=0 is film t=3
N = int(SR * DUR)
rng = np.random.default_rng(18)
L = np.zeros(N); R = np.zeros(N)

def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def fft_band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))

def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR); i1 = min(N, i0 + len(sig))
    if i1 <= i0 or i0 < 0: return
    s = sig[:i1 - i0] * gain
    L[i0:i1] += s * np.sqrt(0.5 * (1 - pan)); R[i0:i1] += s * np.sqrt(0.5 * (1 + pan))

def env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

# ---------------- room tone (dusk outside + hearth inside)
wind = fft_band(rng.normal(size=N), 60, 700); wind /= np.abs(wind).max()
wmod = 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(N) / SR * 0.11 + 1) * np.sin(2 * np.pi * np.arange(N) / SR * 0.037)
room = wind * wmod * 0.030
tt = np.arange(N) / SR
crick = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.3) * (np.sin(2 * np.pi * 0.9 * tt + 0.5) > 0.2)
crick2 = np.sin(2 * np.pi * 3900 * tt + 1) * (np.sin(2 * np.pi * 31 * tt) > 0.4) * (np.sin(2 * np.pi * 0.63 * tt + 2.1) > 0.35)
room_l = room + 0.0035 * crick + 0.0025 * crick2
room_r = room * 0.95 + 0.0045 * crick + 0.0018 * crick2
fade = np.clip((tt - 1.0) / 2.0, 0, 1) * np.clip((DUR - tt) / 1.5, 0, 1)
L += room_l * fade; R += room_r * fade
for k in range(160):  # hearth crackle, panned left (the hearth is at the left of the room)
    t0 = OFF + rng.random() * 32
    n = int(SR * 0.006); c = rng.normal(size=n) * np.exp(-np.arange(n) / (SR * 0.0015))
    add(fft_band(np.pad(c, (0, 200)), 800, 6000), t0, 0.010 + 0.012 * rng.random(), -0.8)

# ---------------- voice (formant synthesis)
VOW = {'a': (700, 1220, 2600), 'ʌ': (640, 1190, 2390), 'i': (390, 1990, 2550), 'e': (480, 1750, 2500), 'o': (560, 880, 2400),
       'l': (360, 1000, 2400), 'm': (260, 1000, 2200), 'n': (280, 1600, 2500), 'ai': (660, 1100, 2500), 'ə': (500, 1500, 2500)}
def resonate(x, F, B):  # time-varying 2-pole resonator; F, B arrays per sample
    y = np.zeros_like(x); y1 = y2 = 0.0
    r = np.exp(-np.pi * B / SR); c = 2 * r * np.cos(2 * np.pi * F / SR); d = -r * r; g = 1 - r
    for i in range(len(x)): v = g[i] * x[i] + c[i] * y1 + d[i] * y2; y2 = y1; y1 = v; y[i] = v
    return y
def syllable(dur, f0a, f0b, path, breath, onset=None, coda=None):
    n = int(dur * SR); u = np.linspace(0, 1, n)
    f0 = f0a + (f0b - f0a) * u + 3 * np.sin(2 * np.pi * 5.5 * u * dur)
    ph = np.cumsum(f0 / SR); src = (ph % 1.0) * 2 - 1; src = np.diff(np.concatenate([[0], src])) * -1  # pulse train
    src = onepole_lp(src, 3000) * 8
    src = (1 - breath) * src + breath * rng.normal(size=n) * 0.6
    keys = np.linspace(0, 1, len(path)); out = np.zeros(n)
    for k in range(3):
        Fk = np.interp(u, keys, [VOW[p][k] for p in path])
        out += resonate(src, Fk, np.full(n, 90 + 40 * k)) * (1.0, 0.55, 0.25)[k]
    e = np.minimum(1, u / 0.12) * np.minimum(1, (1 - u) / 0.25)
    out *= e
    if onset == 'k': b = rng.normal(size=int(0.025 * SR)) * np.exp(-np.arange(int(0.025 * SR)) / (SR * 0.006)); out[:len(b)] += fft_band(b, 1500, 4000) * 0.5
    if onset == 'h': m = int(0.07 * SR); out[:m] += fft_band(rng.normal(size=m), 500, 3500) * 0.12 * np.sin(np.linspace(0, np.pi, m))
    if onset == 'r': pass
    if coda == 't': b = rng.normal(size=int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / (SR * 0.005)); out = np.concatenate([out, np.zeros(int(0.04 * SR)), fft_band(b, 2500, 6000) * 0.3])
    if coda == 'ts': m = int(0.09 * SR); out = np.concatenate([out, fft_band(rng.normal(size=m), 4000, 9000) * 0.18 * np.linspace(1, 0, m)])
    return out / (np.abs(out).max() + 1e-9)

V = json.load(open(os.path.join(C, 'voice.json')))
PHON = {'Come here.': [dict(p=['ʌ', 'ʌ', 'm'], on='k'), dict(p=['i', 'i', 'ə'], on='h')],
        'Come here!': [dict(p=['ʌ', 'ʌ', 'm'], on='k'), dict(p=['i', 'i', 'ə'], on='h')],
        "It's all right.": [dict(p=['i', 'e'], co='ts'), dict(p=['o', 'o', 'l']), dict(p=['ai', 'ai', 'i'], co='t')],
        'Come in.': [dict(p=['ʌ', 'ʌ', 'm'], on='k'), dict(p=['i', 'i', 'n'])]}
segs = {'call': [], 'soft': []}
for line in V:
    call = line['kind'] == 'call'
    for k, (a, b, loud) in enumerate(line['syl']):
        ph = PHON[line['line']][k]
        if call: f0a, f0b = (215, 250) if k == 0 else (265, 205)
        else: f0a, f0b = (185, 175) if k < len(line['syl']) - 1 else (180, 150)
        s = syllable(b - a, f0a, f0b, ph['p'], 0.08 if call else 0.45, ph.get('on'), ph.get('co'))
        g = (0.30 if call else 0.075) * loud
        add(s, OFF + a, g, -0.45)  # the person is at the left of frame
        segs['call' if call else 'soft'].append((OFF + a, OFF + b))

# ---------------- the door: creak + settle knock
n = int(0.55 * SR); u = np.linspace(0, 1, n)
fc = 380 + 260 * np.sin(np.pi * u) + 40 * rng.normal(size=n).cumsum() / np.sqrt(np.arange(1, n + 1)) * 0
ph = np.cumsum((fc + 30 * np.sin(2 * np.pi * 37 * u)) / SR)
cr = np.sign(np.sin(2 * np.pi * ph)) * (0.5 + 0.5 * (rng.random(n) > 0.4))
cr = fft_band(cr, 300, 3000) * np.sin(np.pi * u) ** 0.7
add(cr / np.abs(cr).max(), OFF + 6.2, 0.05, -0.4)
k = int(0.12 * SR); knock = np.sin(2 * np.pi * 120 * np.arange(k) / SR) * np.exp(-np.arange(k) / (SR * 0.025))
add(knock, OFF + 6.74, 0.10, -0.4)

# ---------------- the dog
EV = json.load(open(os.path.join(C, 'events.json')))
def tap(g):
    n = int(0.05 * SR); x = rng.normal(size=n) * np.exp(-np.arange(n) / (SR * 0.008))
    body = np.sin(2 * np.pi * (180 + 40 * rng.random()) * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * 0.012))
    return (fft_band(x, 1500, 7000) * 0.6 + body * 0.8) * g
def panx(x): return float(np.clip((320 + x * 180) / 640 - 1, -1, 1))
for e in EV:
    if e['type'] == 'paw': add(tap(1), OFF + e['t'], 0.035 + 0.01 * rng.random(), panx(e['x']))
for t0, x in [(3.48, 4.0), (3.56, 4.0), (3.62, 4.0), (3.68, 4.0), (8.14, 4.0), (8.22, 4.0), (8.32, 4.0), (8.44, 4.0)]:  # steps of the turns
    add(tap(1), OFF + t0, 0.03, panx(x))
def thump(dur=0.25, f=70):
    n = int(dur * SR); return np.sin(2 * np.pi * f * np.arange(n) / SR * (1 - 0.3 * np.arange(n) / n)) * np.exp(-np.arange(n) / (SR * 0.06))
def breath(dur, lo, hi):
    n = int(dur * SR); return fft_band(rng.normal(size=n), lo, hi) * np.sin(np.linspace(0, np.pi, n)) ** 1.5
add(thump(), OFF + 4.80, 0.12, panx(4.0)); add(breath(0.7, 300, 1800), OFF + 5.4, 0.05, panx(4.0))
add(thump(), OFF + 24.38, 0.12, panx(0.6)); add(breath(0.9, 250, 1500), OFF + 24.6, 0.06, panx(0.6))
add(breath(1.1, 200, 1300), OFF + 29.05, 0.07, panx(0.6))  # the contented sigh as it settles
for k in range(7):  # tail thumps on the boards while it wags, looking in
    add(thump(0.12, 95), OFF + 26.75 + k * 0.476, 0.05 * (1 - k / 9), panx(1.0))
add(breath(0.25, 600, 3000), OFF + 7.47, 0.03, panx(4.0))  # a quick breath as the head comes round

# ---------------- music: plucked harp, D dorian
def pluck(freq, dur=2.6, bright=0.5):
    n = int(dur * SR); p = int(SR / freq); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        j = i % p; out[i] = buf[j]; buf[j] = 0.5 * (buf[j] + buf[(j + 1) % p]) * (0.996 + 0.003 * bright)
    return out * np.exp(-np.arange(n) / (SR * 1.2))
D = {'D3': 146.83, 'A3': 220.0, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0, 'C5': 523.25, 'D5': 587.33}
def phrase(t0, notes, gain, pan=0.3):
    for dt, nm in notes: add(pluck(D[nm]), t0 + dt, gain, pan)
phrase(0.3, [(0, 'D4'), (0.35, 'A4'), (0.7, 'G4'), (1.05, 'F4'), (1.5, 'E4'), (2.1, 'D4')], 0.10)
phrase(OFF + 7.5, [(0, 'A3'), (0.45, 'D4')], 0.07)
phrase(OFF + 14.8, [(0, 'D3'), (1.6, 'A3'), (3.4, 'C4'), (5.4, 'A3'), (7.2, 'D4')], 0.05)
phrase(OFF + 28.6, [(0, 'D4'), (0.4, 'F4'), (0.8, 'A4'), (1.3, 'C5'), (2.0, 'D5'), (3.2, 'A4')], 0.07)
phrase(35.2, [(0, 'D4'), (0.6, 'A3'), (1.3, 'D3')], 0.07)

# ---------------- master, measure, write
mx = max(np.abs(L).max(), np.abs(R).max()); g = 0.89 / mx if mx > 0.89 else 1.0
L *= g; R *= g
def rms_db(a, b):
    i0, i1 = int(a * SR), int(b * SR); s = 0.5 * (L[i0:i1] ** 2 + R[i0:i1] ** 2); return 10 * np.log10(np.mean(s) + 1e-12)
call_db = np.mean([rms_db(a, b) for a, b in segs['call']]); soft_db = np.mean([rms_db(a, b) for a, b in segs['soft']])
tone_db = rms_db(OFF + 12.0, OFF + 14.0)  # a stretch of the scene with only room tone, hearth and breath
lev = {'call_rms_dbfs': round(call_db, 2), 'soft_rms_dbfs': round(soft_db, 2), 'soft_minus_call_db': round(soft_db - call_db, 2),
       'room_tone_rms_dbfs (scene 12-14 s)': round(tone_db, 2), 'soft_above_room_db': round(soft_db - tone_db, 2), 'master_gain': round(g, 3),
       'note': 'RMS over the syllable spans of each kind (voice plus whatever room tone is under it). Measured, not listened to.'}
json.dump(lev, open(os.path.join(C, 'levels.json'), 'w'), indent=1); print(lev)
pcm = (np.stack([L, R], 1) * 32767).astype('<i2')
with wave.open(os.path.join(C, 'audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
