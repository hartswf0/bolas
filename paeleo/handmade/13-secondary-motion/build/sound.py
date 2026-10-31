"""SCION 13 sound: everything synthesized here (numpy), nothing recorded or downloaded.
- voices: a source-filter formant synthesizer (glottal pulse train + aspiration through time-varying cascade resonators),
  phoneme by phoneme: "Come here." (call), "Come here!" (call, reaching), "It's all right." (soft, twice), "Come in." (soft).
  Each voice starts 40 ms before the dog's reaction it causes.
- paper foley from the solver: the dog's crepe rustle follows the kinetic energy of its fringe nodes; reeds, curtain,
  the person's coat and scarf likewise; paw taps at measured paw touchdowns; the door's creak follows the hinge speed.
- dusk wind follows the same gust function that drives the wind force in the solver; the room's warm hum rises as the door opens.
Writes build/cache/sound.wav (38.0 s, 48 kHz stereo) and build/cache/voice_levels.json."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache')
SR = 48000; TITLE = 3.0; SCENE = 32.0; END = 3.0; N = int(SR * (TITLE + SCENE + END))
rng = np.random.default_rng(13)
M = json.load(open(os.path.join(C, 'measure.json')))
FPS = 24

def env_from(series, t0=TITLE):
    """per-frame series -> per-sample envelope (linear interpolation), placed at scene time"""
    x = np.zeros(N); ts = np.arange(len(series)) / FPS + t0
    idx = np.arange(N) / SR
    x[:] = np.interp(idx, ts, series, left=0, right=series[-1] if len(series) else 0)
    return x

def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    # vectorised enough via lfilter-like loop in chunks
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def biquad_bp(x, fc, q):
    w = 2 * np.pi * fc / SR; al = np.sin(w) / (2 * q)
    b0, b1, b2 = al, 0, -al; a0, a1, a2 = 1 + al, -2 * np.cos(w), 1 - al
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        v = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2; x2, x1, y2, y1 = x1, x[i], y1, v; y[i] = v
    return y

def fft_band(x, lo, hi):
    """zero-phase band-pass by FFT (fast for long noise beds)"""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4); return np.fft.irfft(X * g, len(x))

# ---------------- formant voice ----------------
V = {  # F1 F2 F3 (female-ish), voicing 1/0, noise type
    'k': (400, 1800, 2600, 0, 'burst_k'), 'ʌ': (720, 1300, 2700, 1, None), 'm': (280, 1250, 2500, 1, 'nasal'),
    'h': (450, 1950, 2700, 0, 'asp'), 'ɪ': (440, 2150, 2900, 1, None), 'ə': (560, 1650, 2700, 1, None),
    't': (400, 1800, 2700, 0, 'burst_t'), 's': (400, 1800, 2700, 0, 'sss'), 'ɔ': (680, 1000, 2700, 1, None),
    'l': (380, 1150, 2800, 1, None), 'r': (460, 1250, 1750, 1, None), 'a': (880, 1450, 2750, 1, None),
    'n': (300, 1650, 2650, 1, 'nasal'), '_': (500, 1500, 2500, 0, 'sil'),
}
def say(ph, f0, amp, breath):
    """ph: [(phoneme, seconds)], f0: (start, peak, end) Hz -> mono float array"""
    segs = []; t = 0
    for p, d in ph: segs.append((t, t + d, p)); t += d
    n = int(t * SR); tt = np.arange(n) / SR
    # formant tracks with 30 ms glides
    def track(k):
        pts_t, pts_v = [], []
        for a, b, p in segs: pts_t += [a + 0.015, b - 0.015]; pts_v += [V[p][k], V[p][k]]
        return np.interp(tt, pts_t, pts_v)
    F = [track(0), track(1), track(2)]
    voiced = np.zeros(n); noise_amp = np.zeros(n); nasal = np.zeros(n); kinds = [None] * n
    for a, b, p in segs:
        i0, i1 = int(a * SR), int(b * SR); fn = V[p][4]
        voiced[i0:i1] = V[p][3] * (0.55 if fn == 'nasal' else 1)
        if fn == 'nasal': nasal[i0:i1] = 1
        if fn == 'asp': noise_amp[i0:i1] = 0.5
        if fn == 'sss': noise_amp[i0:i1] = 0.0
    voiced = np.convolve(voiced, np.ones(480) / 480, 'same')
    # pitch contour: rise to the stressed vowel, fall at the end
    pk = t * 0.55; f0c = np.where(tt < pk, np.interp(tt, [0, pk], [f0[0], f0[1]]), np.interp(tt, [pk, t], [f0[1], f0[2]]))
    f0c *= 1 + 0.012 * np.sin(2 * np.pi * 5.2 * tt) + 0.004 * rng.standard_normal(n)
    ph_acc = np.cumsum(f0c / SR); src = np.zeros(n)
    edges = np.nonzero(np.diff(np.floor(ph_acc)) > 0)[0]; src[edges] = 1.0
    src = onepole_lp(onepole_lp(src, 700), 1400) * 30            # glottal spectrum tilt
    src = src * voiced + rng.standard_normal(n) * (0.06 * voiced * breath + noise_amp * 0.35)
    # cascade resonators, per sample (formants move)
    y = src.copy()
    for k, bw in zip(range(3), (90, 110, 170)):
        out = np.zeros(n); y1 = y2 = 0.0; f = F[k]
        r = np.exp(-np.pi * bw / SR); c2 = -r * r
        for i in range(n):
            c1 = 2 * r * np.cos(2 * np.pi * f[i] / SR); v = (1 - c1 - c2) * y[i] + c1 * y1 + c2 * y2; y2, y1 = y1, v; out[i] = v
        y = out
    y = y - 0.7 * nasal * fft_band(y, 900, 4000)                 # nasal murmur: damp the upper formants
    # consonant noises
    for a, b, p in segs:
        i0, i1 = int(a * SR), int(b * SR); fn = V[p][4]
        if fn in ('burst_k', 'burst_t'):
            m = i1 - i0; burst = np.zeros(m); bl = int(0.025 * SR); s0 = int(m * 0.55)
            nz = fft_band(rng.standard_normal(bl), 1500, 3500) if fn == 'burst_k' else fft_band(rng.standard_normal(bl), 3500, 7000)
            burst[s0:s0 + bl] = nz[:max(0, min(bl, m - s0))] * np.exp(-np.arange(min(bl, m - s0)) / (0.008 * SR)) * 2.2
            y[i0:i1] += burst
        if fn == 'sss':
            m = i1 - i0; y[i0:i1] += fft_band(rng.standard_normal(m), 4500, 9000) * np.hanning(m) * 0.5
    y *= np.minimum(1, np.minimum(tt / 0.02, (t - tt) / 0.05))
    y = y / (np.abs(y).max() + 1e-9) * amp
    return y

PHR = {
    'come_here': [('k', 0.07), ('ʌ', 0.13), ('m', 0.09), ('h', 0.08), ('ɪ', 0.16), ('ə', 0.2)],
    'its_all_right': [('ɪ', 0.08), ('t', 0.06), ('s', 0.1), ('ɔ', 0.17), ('l', 0.08), ('r', 0.07), ('a', 0.14), ('ɪ', 0.1), ('t', 0.08)],
    'come_in': [('k', 0.07), ('ʌ', 0.12), ('m', 0.07), ('ɪ', 0.16), ('n', 0.18)],
}
CALL, SOFT = 0.50, 0.13          # peak amplitudes: soft is 11.7 dB below the calls
VOICES = [  # (scene t of the score event, phrase, f0, amp, breath)  — onset 40 ms before the event
    (1.00, 'come_here', (250, 330, 210), CALL, 0.4),
    (3.40, 'come_here', (270, 360, 220), CALL * 1.08, 0.3),
    (7.40, 'its_all_right', (205, 235, 175), SOFT, 1.0),
    (10.40, 'its_all_right', (200, 228, 172), SOFT, 1.0),
    (26.40, 'come_in', (210, 240, 180), SOFT, 1.0),
]
L = np.zeros(N); R = np.zeros(N)
def place(sig, t, pan, gain=1.0):
    i = int(t * SR); sig = sig[:max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l * gain; R[i:i + len(sig)] += sig * r * gain
def screen_pan(x): return float(np.clip((x - 640) / 640, -1, 1)) * 0.7

levels = []
for t, ph, f0, amp, br in VOICES:
    sig = say(PHR[ph], f0, amp, br)
    k = int(t * FPS); px = M[min(k, len(M) - 1)]
    pan = -0.35 if t < 5 else -0.5
    place(sig, TITLE + t - 0.04, pan)
    rms = float(np.sqrt(np.mean(sig[np.abs(sig) > amp * 0.05] ** 2)))
    levels.append({'t_score': t, 'onset_scene_s': round(t - 0.04, 3), 'phrase': ph, 'peak_dbfs': round(20 * np.log10(amp), 1), 'rms_dbfs': round(20 * np.log10(rms), 1)})

# ---------------- foley from the solver ----------------
nfr = len(M); tt = np.arange(N) / SR
def series(key, sub=None): return np.array([(m[key][sub] if sub else m[key]) for m in M], float)
dog_pan = np.interp(tt, np.arange(nfr) / FPS + TITLE, [screen_pan(m['x_screen']) for m in M])
# dusk wind: low noise shaped by the solver's gust function
wind = env_from(series('wind')); wbed = fft_band(rng.standard_normal(N), 60, 700) ; wbed /= np.abs(wbed).max()
wair = fft_band(rng.standard_normal(N), 900, 3500); wair /= np.abs(wair).max()
amb = wbed * (0.018 + 0.03 * np.clip(wind - 0.2, 0, 3)) + wair * 0.006 * np.clip(wind - 0.3, 0, 3)
amb[: int(TITLE * SR)] *= np.linspace(0, 1, int(TITLE * SR)) ** 2
amb[int((TITLE + SCENE) * SR):] *= np.linspace(1, 0, N - int((TITLE + SCENE) * SR))
L += amb; R += amb * 0.95
# crepe rustle of the dog: crinkle (sparse clicks through a paper band) scaled by fringe kinetic energy
fur = env_from(np.sqrt(series('energy', 'fur')))
fur = np.clip(fur / 14.0, 0, 1.2)
clicks = (rng.random(N) < 0.02).astype(float) * rng.standard_normal(N)
crin = fft_band(clicks, 1800, 7500) + 0.35 * fft_band(rng.standard_normal(N), 2500, 6000)
crin /= np.abs(crin).max(); rust = crin * fur * 0.09
L += rust * (1 - dog_pan) / 2 * 1.4; R += rust * (1 + dog_pan) / 2 * 1.4
# reeds and curtain and person (paper/cloth rustle bands)
for key, lo, hi, scale, gain, pan in [('reeds', 1500, 6000, 6.0, 0.03, 0.8), ('curtain', 1000, 5000, 5.0, 0.05, -0.3), ('person', 400, 3000, 5.0, 0.04, -0.6)]:
    e = np.clip(env_from(np.sqrt(series('energy', key))) / scale, 0, 1)
    nz = fft_band(rng.standard_normal(N), lo, hi); nz /= np.abs(nz).max()
    s = nz * e * gain; place(s, 0, pan)
# ear flicks: short paper flap where ear energy jumps
ear = series('energy', 'ears')
for k in range(1, nfr):
    if ear[k] > 2.5 and ear[k - 1] < 2.5 and ear[k] > 1.8 * ear[k - 1]:
        m = int(0.06 * SR); f = fft_band(rng.standard_normal(m), 900, 5000) * np.exp(-np.arange(m) / (0.012 * SR)) * 0.08
        place(f, TITLE + k / FPS, screen_pan(M[k]['x_screen']))
# paw taps at measured touchdowns (paw height falls back to the floor)
paws = np.array([m['paws'] for m in M])
for j in range(4):
    for k in range(1, nfr):
        if paws[k - 1, j] > 0.05 and paws[k, j] <= 0.05:
            m = int(0.05 * SR); tap = fft_band(rng.standard_normal(m), 120, 900) * np.exp(-np.arange(m) / (0.007 * SR)) * 0.05
            tap += fft_band(rng.standard_normal(m), 2500, 6000) * np.exp(-np.arange(m) / (0.003 * SR)) * 0.012
            place(tap, TITLE + k / FPS, screen_pan(M[k]['x_screen']))
# lying down: a soft settling of paper on boards
for t0 in (4.3, 23.85):
    m = int(0.7 * SR); s = fft_band(rng.standard_normal(m), 200, 2500) * np.hanning(m) * 0.035; place(s, TITLE + t0, screen_pan(M[int(t0 * FPS)]['x_screen']))
# person steps aside and sits
for t0 in (4.75, 5.05, 5.35): m = int(0.08 * SR); place(fft_band(rng.standard_normal(m), 80, 600) * np.exp(-np.arange(m) / (0.015 * SR)) * 0.08, TITLE + t0, -0.6)
m = int(0.25 * SR); place(fft_band(rng.standard_normal(m), 60, 500) * np.exp(-np.arange(m) / (0.05 * SR)) * 0.09, TITLE + 6.3, -0.6)
# door: creak follows the hinge angular speed
dw = env_from(series('energy', 'door')); dw = np.clip(dw / 3.0, 0, 1)
ph = np.cumsum((170 + 90 * dw) / SR); creak = np.sign(np.sin(2 * np.pi * ph)) * (rng.random(N) < 0.5) ; creak = fft_band(creak, 300, 2500)
creak /= np.abs(creak).max() + 1e-9; place(creak * dw * 0.05, 0, -0.4)
# warm room hum, louder with the door open
op = env_from(series('door_open'))
hum = (np.sin(2 * np.pi * 110 * tt) * 0.5 + np.sin(2 * np.pi * 165 * tt) * 0.3 + np.sin(2 * np.pi * 220.5 * tt) * 0.2) * (1 + 0.1 * np.sin(2 * np.pi * 0.3 * tt))
place(hum * (0.003 + 0.01 * op) * (tt > TITLE) * (tt < TITLE + SCENE + 1.5), 0, -0.5)
# title and end: a single torn-paper sound each
for t0 in (0.4, TITLE + SCENE + 0.3):
    m = int(0.5 * SR); s = fft_band(rng.standard_normal(m), 1200, 7000) * (np.linspace(1, 0, m) ** 2) * (rng.random(m) < 0.3) * 0.08; place(s, t0, 0)

peak = max(np.abs(L).max(), np.abs(R).max()); g = min(1.0, 0.89 / peak)
L *= g; R *= g
st = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(C, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
amb_rms = float(np.sqrt(np.mean((amb[int(TITLE * SR):int((TITLE + SCENE) * SR)] * g) ** 2)))
for v in levels: v['peak_dbfs'] = round(v['peak_dbfs'] + 20 * np.log10(g), 1); v['rms_dbfs'] = round(v['rms_dbfs'] + 20 * np.log10(g), 1)
calls = [v['rms_dbfs'] for v in levels if v['phrase'] == 'come_here']; softs = [v['rms_dbfs'] for v in levels if v['phrase'] != 'come_here']
rep = {'voices': levels, 'room_tone_rms_dbfs': round(20 * np.log10(amb_rms), 1), 'soft_minus_call_db': round(max(softs) - min(calls), 1), 'master_gain': round(g, 3)}
json.dump(rep, open(os.path.join(C, 'voice_levels.json'), 'w'), indent=1)
print(json.dumps(rep))
