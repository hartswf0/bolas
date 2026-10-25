"""The sound of the plate, synthesized here (no recordings): dusk room tone and crickets, a formant-synthesized voice
(calls; the soft voice ≥ 6 dB quieter), paper riffles when the dog's drawing is substituted, claws on boards at the
footfalls the render logged, the door, the dog lying down. Writes cache/audio.wav and ../sound.json (measured levels)."""
import os, json, math, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SR = 48000; DUR = 38.0; OFF = 3.0
n = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(n); R = np.zeros(n)
EV = json.load(open(os.path.join(HERE, 'cache', 'events.json')))
MEAS = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))

def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); s = 0.0
    # vectorised via cumulative trick is unstable; small loops are fine at these lengths
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def fft_filter(x, lo=None, hi=None, order=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** (2 * order))
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * g, len(x))

def resonator(x, f0, bw):
    """two-pole formant resonator (Klatt); f0 may be an array (moving formant)"""
    f0 = np.broadcast_to(np.asarray(f0, float), x.shape)
    y = np.zeros_like(x); y1 = y2 = 0.0
    r = math.exp(-math.pi * bw / SR)
    C = -r * r
    for i in range(len(x)):
        B = 2 * r * math.cos(2 * math.pi * f0[i] / SR); A = 1 - B - C
        yi = A * x[i] + B * y1 + C * y2; y[i] = yi; y2 = y1; y1 = yi
    return y

def place(sig, t, pan=0.0, gain=1.0):
    i0 = int((t + OFF) * SR)
    if i0 >= n: return
    sig = sig[:max(0, n - i0)] * gain
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    L[i0:i0 + len(sig)] += sig * l; R[i0:i0 + len(sig)] += sig * r

def env(m, a, d):
    e = np.ones(m); ai = int(a * SR); di = int(d * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if di: e[-di:] *= np.linspace(1, 0, di) ** 1.5
    return e

# ---------------- voice: a source-filter synth (Rosenberg-like pulses + aspiration through moving formants)
VOW = {'uh': (640, 1190, 2390), 'i': (330, 2100, 2900), 'er': (500, 1500, 2500), 'ih': (400, 1900, 2600), 'o': (520, 900, 2400),
       'ai': (750, 1250, 2500), 'm': (260, 1000, 2300), 'n': (280, 1600, 2600), 'l': (360, 1100, 2600), 'r': (420, 1300, 1700), 'a': (700, 1100, 2500)}

def voice(segments, f0_curve, breath=0.12, level=1.0):
    """segments: list of (phone, duration, voiced, noise); f0_curve: function of time fraction → Hz"""
    total = sum(s[1] for s in segments); m = int(total * SR)
    t = np.arange(m) / SR
    f0 = np.array([f0_curve(x) for x in t / total])
    ph = np.cumsum(f0 / SR) % 1.0
    pulse = np.where(ph < 0.6, 0.5 - 0.5 * np.cos(np.pi * ph / 0.6), np.cos(np.pi * (ph - 0.6) / 0.8)) ; pulse = np.diff(pulse, prepend=0) * 40
    F = np.zeros((m, 3)); vo = np.zeros(m); no = np.zeros(m); i = 0
    for ph_, d, v, nz in segments:
        k = int(d * SR); F[i:i + k] = VOW[ph_]; vo[i:i + k] = v; no[i:i + k] = nz; i += k
    # smooth formant and voicing trajectories (coarticulation)
    ker = np.hanning(int(0.035 * SR)); ker /= ker.sum()
    for j in range(3): F[:, j] = np.convolve(np.pad(F[:, j], len(ker), mode='edge'), ker, 'same')[len(ker):-len(ker)]
    vo = np.convolve(np.pad(vo, len(ker), mode='edge'), ker, 'same')[len(ker):-len(ker)]
    no = np.convolve(np.pad(no, len(ker), mode='edge'), ker, 'same')[len(ker):-len(ker)]
    src = pulse * vo + rng.normal(0, 1, m) * (no + breath * vo) * 0.6
    out = resonator(src, F[:, 0], 90) * 1.0 + resonator(src, F[:, 1], 120) * 0.5 + resonator(src, F[:, 2], 180) * 0.25
    out = fft_filter(out, lo=120, hi=6000)
    out *= env(m, 0.02, 0.08)
    return out / (np.sqrt(np.mean(out ** 2)) + 1e-9) * level

def come_here(level, urgent=False):
    segs = [('uh', 0.035, 0.0, 1.0), ('uh', 0.17, 1, 0), ('m', 0.09, 0.8, 0), ('ih', 0.04, 0.0, 0.8), ('i', 0.18, 1, 0.05), ('er', 0.24 if not urgent else 0.2, 1, 0.05)]
    hi_ = 330 if urgent else 290
    return voice(segs, lambda x: 210 + (hi_ - 210) * math.sin(min(1, x * 1.6) * math.pi / 2) - (70 * max(0, x - 0.62) / 0.38), breath=0.06, level=level)

def its_all_right(level):
    segs = [('ih', 0.11, 0.7, 0.3), ('n', 0.04, 0.0, 0.9), ('o', 0.16, 1, 0.1), ('l', 0.08, 0.9, 0.05), ('r', 0.07, 0.9, 0.05), ('ai', 0.24, 1, 0.12), ('ih', 0.05, 0.0, 0.7)]
    return voice(segs, lambda x: 205 - 40 * x, breath=0.35, level=level)

def come_in(level):
    segs = [('uh', 0.035, 0.0, 0.9), ('uh', 0.15, 1, 0.1), ('m', 0.08, 0.8, 0), ('ih', 0.2, 1, 0.12), ('n', 0.14, 0.8, 0.05)]
    return voice(segs, lambda x: 210 - 35 * x, breath=0.35, level=level)

CALL = 0.20; SOFT = CALL * 10 ** (-14 / 20)     # soft voice 14 dB under the calls (RMS)
voice_track = np.zeros(n)
def vplace(sig, t, pan):
    place(sig, t, pan); i0 = int((t + OFF) * SR); voice_track[i0:i0 + len(sig)] += sig
vplace(come_here(CALL), 1.02, -0.45)
vplace(come_here(CALL * 1.05, urgent=True), 1.70, -0.45)
vplace(come_here(CALL * 1.15, urgent=True), 3.42, -0.4)
vplace(come_here(CALL * 1.15, urgent=True), 4.02, -0.4)
for t0 in (7.45, 8.4, 10.45):
    vplace(its_all_right(SOFT), t0, -0.1)
vplace(come_in(SOFT), 26.45, -0.1)

# ---------------- room tone: dusk air, crickets; warm air from the room once the door is open
air = fft_filter(rng.normal(0, 1, n), lo=60, hi=900, order=1)
air = air / np.sqrt(np.mean(air ** 2)) * 10 ** (-46 / 20)
tt = np.arange(n) / SR
fade = np.clip((tt - 0.5) / 2.0, 0, 1) * np.clip((DUR - 0.3 - tt) / 2.5, 0, 1)
L += air * fade; R += air * fade * 0.95
cr = np.zeros(n)
t = 1.2
while t < DUR - 1:
    for k in range(3):
        i0 = int((t + k * 0.032) * SR); m = int(0.016 * SR)
        cr[i0:i0 + m] += np.sin(2 * np.pi * 4700 * np.arange(m) / SR) * np.hanning(m)
    t += rng.uniform(0.55, 0.95)
cr *= 10 ** (-40 / 20) * fade
L += cr * 0.6; R += cr * 1.0
door_open = lambda x: min(1, max(0, (x - 6.2) / 0.85))
warm = fft_filter(rng.normal(0, 1, n), lo=80, hi=500, order=1)
warm = warm / np.sqrt(np.mean(warm ** 2)) * 10 ** (-44 / 20)
hum = (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 165 * tt) + 0.25 * np.sin(2 * np.pi * 220.5 * tt)) * 10 ** (-50 / 20)
lt = np.array([door_open(x - OFF) for x in tt]) * (tt < OFF + 32)
L += (warm + hum) * lt; R += (warm + hum) * lt * 0.5

# ---------------- paper: each substitution of the dog's drawing is a print slid on the stage
for e in EV:
    if e['type'] != 'paper': continue
    m = int(0.07 * SR)
    sig = fft_filter(rng.normal(0, 1, m), lo=1800, hi=7000) * np.exp(-np.arange(m) / (0.018 * SR)) * env(m, 0.004, 0.02)
    place(sig / (np.abs(sig).max() + 1e-9), e['t'], 0.4, 10 ** (-24 / 20))

# ---------------- claws and pads on the porch boards at the footfalls the render logged
xs = {i: r['msr']['cx'] for i, r in enumerate(MEAS) if r.get('msr')}
for e in EV:
    if e['type'] != 'step': continue
    i = int(round(e['t'] * 24)); pan = (xs.get(i, 900) / 640.0) - 1
    m = int(0.09 * SR)
    click = fft_filter(rng.normal(0, 1, m), lo=2500, hi=9000) * np.exp(-np.arange(m) / (0.0025 * SR))
    thud = np.sin(2 * np.pi * 140 * np.arange(m) / SR) * np.exp(-np.arange(m) / (0.02 * SR))
    g = 10 ** (-30 / 20) * (1.3 if e['t'] < 3 else 1.0)
    place((click * 0.6 + thud * 0.5) / 1.1, e['t'], pan, g)

# ---------------- the door: a slow creak, then the latch side touching the wall
m = int(0.85 * SR); x = np.arange(m) / SR
rate = 26 + 70 * (x / 0.85) ** 0.8
ph = np.cumsum(rate / SR); pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
pulses *= 1 + 0.4 * rng.normal(0, 1, m)
creak = resonator(pulses, np.full(m, 720.0), 60) + 0.5 * resonator(pulses, np.full(m, 1650.0), 120)
creak *= env(m, 0.05, 0.2); creak /= np.abs(creak).max()
place(creak, 6.22, -0.75, 10 ** (-27 / 20))
m = int(0.25 * SR); knock = np.sin(2 * np.pi * 95 * np.arange(m) / SR) * np.exp(-np.arange(m) / (0.03 * SR))
place(knock, 7.05, -0.8, 10 ** (-30 / 20))

# ---------------- lying down: a soft body on boards and an exhale; the settled sigh at the end
def liedown(t, pan, g=1.0):
    m = int(0.3 * SR); th = fft_filter(rng.normal(0, 1, m), hi=260) * np.exp(-np.arange(m) / (0.06 * SR))
    place(th / np.abs(th).max(), t, pan, 10 ** (-28 / 20) * g)
    m = int(0.9 * SR); ex = fft_filter(rng.normal(0, 1, m), lo=300, hi=1800) * np.hanning(m)
    place(ex / np.abs(ex).max(), t + 0.15, pan, 10 ** (-34 / 20) * g)
liedown(4.75, 0.6)
liedown(24.35, -0.4)
m = int(1.2 * SR); sigh = fft_filter(rng.normal(0, 1, m), lo=250, hi=1400) * np.hanning(m) ** 0.7
place(sigh / np.abs(sigh).max(), 28.6, -0.4, 10 ** (-33 / 20))

# ---------------- title and end cards: a sheet laid down
for tc in (-2.9, 32.1):
    m = int(0.35 * SR); sh = fft_filter(rng.normal(0, 1, m), lo=900, hi=6000) * env(m, 0.03, 0.25)
    place(sh / np.abs(sh).max(), tc, 0.0, 10 ** (-30 / 20))

# ---------------- master
peak = max(np.abs(L).max(), np.abs(R).max())
g = 10 ** (-1 / 20) / peak
L *= g; R *= g; voice_track *= g
def rms_db(x): return 20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
def win(t0, t1, x): return x[int((t0 + OFF) * SR):int((t1 + OFF) * SR)]
mix = (L + R) / 2
def voiced_rms(t0, t1):
    seg = win(t0, t1, voice_track); m = np.abs(seg) > 1e-4
    return rms_db(seg[m]) if m.any() else None
meas = {
    'call_1_rms_db': voiced_rms(1.0, 2.3), 'call_2_rms_db': voiced_rms(3.4, 4.6),
    'soft_1_rms_db': voiced_rms(7.4, 9.4), 'soft_2_rms_db': voiced_rms(10.4, 11.6), 'come_in_rms_db': voiced_rms(26.4, 27.4),
    'room_tone_rms_db_12_14s': rms_db(win(12.0, 14.0, mix)), 'room_tone_rms_db_0.5_0.9s': rms_db(win(0.5, 0.9, mix)),
    'peak_dbfs': 20 * math.log10(max(np.abs(L).max(), np.abs(R).max())),
    'note': 'RMS over voiced samples of the voice stem only (the same gain as the mix); room tone from the full mix in windows without voice.'}
meas['soft_below_calls_db'] = round(min(meas['call_1_rms_db'], meas['call_2_rms_db']) - max(meas['soft_1_rms_db'], meas['soft_2_rms_db'], meas['come_in_rms_db']), 2)
meas['soft_above_room_db'] = round(min(meas['soft_1_rms_db'], meas['soft_2_rms_db'], meas['come_in_rms_db']) - meas['room_tone_rms_db_12_14s'], 2)
json.dump(meas, open(os.path.join(ROOT, 'sound.json'), 'w'), indent=1)
pcm = (np.stack([L, R], -1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, 'cache', 'audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(json.dumps(meas, indent=1))
