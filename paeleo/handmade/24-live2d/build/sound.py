"""SCION-24 sound: every sound is synthesized here from numbers (numpy); nothing is recorded or sampled.
Cues come from the render: cache/events.json holds the footfalls the gait solver actually planted, the collar-tag swings, the
lie-downs and the sigh, and the speech script whose syllables also drive the person's mouth. Output: cache/sound.wav (48 kHz).
The film is 3 s title + 32 s scene + 3 s end; scene time t sits at film time t + 3."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = 38.0
OFF = 3.0
N = int(SR * DUR)
rng = np.random.default_rng(24)
ev = json.load(open(os.path.join(HERE, 'cache', 'events.json')))
mix = np.zeros(N)
stems = {}


def add(name, sig, t, gain=1.0):
    i = int((t + OFF) * SR)
    if i >= N: return
    j = min(N, i + len(sig))
    mix[i:j] += sig[:j - i] * gain
    s = stems.setdefault(name, np.zeros(N)); s[i:j] += sig[:j - i] * gain


def db(x): return 10 ** (x / 20)


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); z = 0.0
    for n in range(len(x)): z = (1 - a) * x[n] + a * z; y[n] = z
    return y


def biquad_bp(x, f0, q):
    w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b0, b2, a0, a1, a2 = al, -al, 1 + al, -2 * np.cos(w), 1 - al
    b0, b2, a1, a2 = b0 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for n in range(len(x)):
        v = b0 * x[n] + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x[n], y1, v; y[n] = v
    return y


def fft_filter(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    m = np.convolve(m, np.ones(31) / 31, mode='same')
    return np.fft.irfft(X * m, len(x))


# ---------------- the voice: a source-filter formant synthesizer ----------------
PH = {  # vowel targets: (F1, F2, F3)
    '@': (700, 1220, 2600), 'i': (400, 2100, 2850), 'e': (560, 1500, 2100), 'o': (620, 920, 2550), 'a': (760, 1300, 2500), 'I': (420, 2000, 2700),
    'u': (450, 1100, 2400), 'n': (280, 1200, 2600), 'm': (260, 1000, 2400), 'l': (380, 950, 2700), 'r': (420, 1100, 1700),
}
SYL = {  # syllable -> (onset consonant, vowel path with fractions, coda)
    'k@m': ('k', [('@', 0.0), ('@', 0.65), ('m', 1.0)], None),
    'hi@': ('h', [('i', 0.0), ('i', 0.35), ('e', 0.75), ('r', 1.0)], None),
    'on': (None, [('o', 0.0), ('o', 0.6), ('n', 1.0)], None),
    'its': (None, [('I', 0.0), ('I', 0.5)], 's'),
    'ol': (None, [('o', 0.0), ('o', 0.5), ('l', 1.0)], None),
    'rait': ('r', [('r', 0.0), ('a', 0.3), ('a', 0.55), ('i', 0.95)], 't'),
    'gud': ('g', [('u', 0.0), ('u', 0.8)], 'd'),
    'dog': ('d', [('o', 0.0), ('o', 0.8)], 'g'),
    'in': (None, [('I', 0.0), ('I', 0.55), ('n', 1.0)], None),
}


def resonator_tv(x, F, B):
    """time-varying 2-pole resonator (Klatt), F and B arrays per sample"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    C = -np.exp(-2 * np.pi * B / SR); Bc = 2 * np.exp(-np.pi * B / SR) * np.cos(2 * np.pi * F / SR); A = 1 - Bc - C
    for n in range(len(x)):
        v = A[n] * x[n] + Bc[n] * y1 + C[n] * y2
        y2, y1 = y1, v; y[n] = v
    return y


def burst(dur, lo, hi, amp=1.0):
    n = int(dur * SR); x = rng.standard_normal(n) * np.exp(-np.linspace(0, 6, n))
    return fft_filter(x, lo, hi) * amp


def syllable(code, dur, f0a, f0b, loud, breath):
    onset, path, coda = SYL[code]
    pre = {'k': 0.05, 'h': 0.07, 'g': 0.04, 'd': 0.035, 'r': 0.0, None: 0.0}[onset]
    n = int(dur * SR); t = np.arange(n) / n
    # formant tracks along the vowel path
    F = np.zeros((3, n))
    for k in range(3):
        xs = [p[1] for p in path]; ys = [PH[p[0]][k] for p in path]
        F[k] = np.interp(t, xs, ys)
    f0 = f0a + (f0b - f0a) * t + 6 * np.sin(2 * np.pi * 5.2 * t * dur) * 0.3
    f0 *= 1 + 0.006 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1))
    ph = np.cumsum(f0 / SR)
    # glottal source: a rounded pulse train with spectral tilt, plus breath noise
    frac = ph % 1.0
    src = np.where(frac < 0.6, np.sin(np.pi * frac / 0.6) ** 2, 0.0)
    src = np.diff(src, prepend=0) * 40
    noise = rng.standard_normal(n) * 0.6
    src = (1 - breath) * src + breath * noise * 0.25 + 0.012 * noise
    env = np.minimum(1, np.minimum(t / 0.12, (1 - t) / 0.25)).clip(0, 1) ** 1.2
    # nasal coda dims the voice
    if path[-1][0] in 'mn': env *= np.interp(t, [0, 0.62, 1], [1, 1, 0.45])
    out = np.zeros(n)
    for k, bw in zip(range(3), (80, 110, 160)):
        out += resonator_tv(src, F[k], np.full(n, bw)) * (1.0, 0.9, 0.55)[k]
    out *= env * loud
    seg = [np.zeros(int(pre * SR))]
    if onset in ('k', 'g', 'd'): b = burst(0.03, {'k': 1600, 'g': 900, 'd': 2500}[onset], {'k': 4200, 'g': 2600, 'd': 5000}[onset], 0.35 * loud); seg = [b, np.zeros(max(0, int(pre * SR) - len(b)))]
    if onset == 'h':
        hn = rng.standard_normal(int(pre * SR)) * np.linspace(0.2, 1, int(pre * SR))
        hh = np.zeros_like(hn)
        for k in range(3): hh += resonator_tv(hn, np.full(len(hn), PH['i'][k]), np.full(len(hn), 300.0)) * (0.5, 0.3, 0.2)[k]
        seg = [hh * 0.25 * loud]
    tail = []
    if coda == 's': tail = [fft_filter(rng.standard_normal(int(0.11 * SR)) * np.hanning(int(0.11 * SR)), 4500, 9000) * 0.22 * loud]
    if coda in ('t', 'd', 'g'): tail = [np.zeros(int(0.04 * SR)), burst(0.025, 2000, 6000, 0.25 * loud)]
    return np.concatenate(seg + [out] + tail), pre


speech_levels = {}
for line in ev['speech']:
    call = line['kind'] == 'call'
    loud = db(-3) if call else db(-9)
    breath = 0.06 if call else 0.3
    nsy = len(line['syl'])
    for k, (t0, d, o, code) in enumerate(line['syl']):
        base = 235 if call else 192
        if call:
            f0a, f0b = (base + 10 + 25 * (k == 1), base + 40 * (k == 1) - 35 * (k == nsy - 1))
            if 'Come here!' in line['text']: f0a += 25; f0b += 25
        else:
            f0a, f0b = base - 4 * k, base - 6 * k - 14 * (k == nsy - 1)
        sig, pre = syllable(code, d, f0a, f0b, loud, breath)
        add('voice', sig, t0 - pre, 0.5)
    speech_levels[line['text']] = 'call' if call else 'soft'

# a little porch/room reverb on the voice (synthetic decaying noise impulse)
ir_n = int(0.45 * SR); ir = rng.standard_normal(ir_n) * np.exp(-np.linspace(0, 7, ir_n)); ir = fft_filter(ir, 200, 5000); ir /= np.sqrt(np.sum(ir ** 2))
v = stems['voice']; wet = np.fft.irfft(np.fft.rfft(v, N + ir_n) * np.fft.rfft(ir, N + ir_n))[:N]
mix += wet * 0.12; stems['voice'] = v + wet * 0.12


# ---------------- the dog ----------------
def paw(soft):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (110 + 40 * np.exp(-tt * 60)) * tt) * np.exp(-tt * 55)
    clicks = np.zeros(n)
    for c in range(rng.integers(1, 4)):
        p = int(rng.uniform(0.002, 0.03) * SR); m = int(0.003 * SR)
        clicks[p:p + m] += rng.standard_normal(m) * np.hanning(m)
    clicks = fft_filter(clicks, 2500, 7000)
    board = fft_filter(rng.standard_normal(n) * np.exp(-tt * 40), 300, 1500) * 0.3
    return (thud * 0.6 + clicks * (0.25 if soft else 0.7) + board) * (0.45 if soft else 1.0)


def jingle(amp):
    n = int(0.22 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt * d) * w for f, d, w in ((3150, 28, 1), (4720, 35, 0.7), (6260, 45, 0.5), (7930, 55, 0.35)))
    return s * amp


def flop():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    th = np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 18)
    ru = fft_filter(rng.standard_normal(n) * np.exp(-tt * 7), 400, 3000) * 0.35
    return th * 0.8 + ru


def sigh():
    n = int(1.3 * SR); tt = np.arange(n) / n
    x = rng.standard_normal(n) * np.sin(np.pi * tt) ** 1.5 * (1 - 0.6 * tt)
    return fft_filter(x, 350, 1600) * 0.5


for e in ev['events']:
    k = e['kind']
    if k == 'paw': add('dog', paw(e.get('soft')), e['t'], db(-31))
    elif k == 'tag': add('dog', jingle(e.get('amp', 0.5)), e['t'], db(-40))
    elif k == 'lie': add('dog', flop(), e['t'] + 0.05, db(-30))
    elif k == 'sigh': add('dog', sigh(), e['t'], db(-28))


# ---------------- the person, the door, the house ----------------
def step_wood():
    n = int(0.18 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 85 * tt) * np.exp(-tt * 35) + fft_filter(rng.standard_normal(n) * np.exp(-tt * 30), 200, 2500) * 0.4


def creak(dur, f0, f1, rough=0.4):
    n = int(dur * SR); tt = np.arange(n) / n
    f = np.linspace(f0, f1, n) * (1 + 0.04 * np.sin(2 * np.pi * 7 * tt * dur))
    ph = np.cumsum(f / SR); saw = 2 * (ph % 1) - 1
    pulses = (rng.random(n) < 60 / SR) * 1.0
    x = saw * (1 - rough) + np.convolve(pulses, np.hanning(200), 'same') * rough
    x = biquad_bp(x, 900, 3) + biquad_bp(x, 1800, 5) * 0.5
    return x * np.sin(np.pi * tt) ** 0.7


for e in ev['events']:
    if e['kind'] == 'steps':
        for k, dt in enumerate((0.0, 0.3, 0.58)): add('person', step_wood(), e['t'] + dt, db(-27 - 2 * k))
    if e['kind'] == 'sit':
        add('person', creak(0.35, 260, 210, 0.6), e['t'], db(-34))
        n = int(0.4 * SR); add('person', fft_filter(rng.standard_normal(n) * np.hanning(n), 800, 5000), e['t'] - 0.1, db(-38))
    if e['kind'] == 'door':
        n = int(0.03 * SR); add('door', fft_filter(rng.standard_normal(n) * np.exp(-np.linspace(0, 9, n)), 1500, 6000), e['t'] - 0.02, db(-24))
        add('door', creak(0.7, 520, 380, 0.35), e['t'] + 0.05, db(-29))

# room tone: dusk wind and crickets outside; inside, a clock and a fire whose sound comes out when the door opens
t = np.arange(N) / SR
wind = fft_filter(rng.standard_normal(N), 60, 500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t + 1))
crick = np.zeros(N)
for rate, f, ph, amp in ((0.9, 4300, 0.0, 1.0), (1.17, 4650, 0.4, 0.6), (0.73, 3950, 0.2, 0.45)):
    tt = 0.0 + ph
    while tt < DUR:
        for p in range(4):
            i = int((tt + p * 0.018) * SR); m = int(0.012 * SR)
            if i + m < N: crick[i:i + m] += np.sin(2 * np.pi * f * np.arange(m) / SR) * np.hanning(m) * amp
        tt += 1 / rate + rng.uniform(-0.05, 0.05)
door_open = np.clip((t - OFF - 6.2) / 0.8, 0, 1)
ajar = 0.3 + 0.7 * door_open
clock = np.zeros(N)
for k in range(int(DUR)):
    i = int((k + 0.37) * SR); m = int(0.012 * SR)
    clock[i:i + m] += fft_filter(rng.standard_normal(m) * np.exp(-np.linspace(0, 8, m)), 1500, 5000)[:m] * (1 if k % 2 else 0.7)
fire = fft_filter(rng.standard_normal(N), 80, 600) * 0.5
cr = (rng.random(N) < 9 / SR) * rng.uniform(0.3, 1.0, N)
fire += fft_filter(np.convolve(cr, np.hanning(60), 'same'), 800, 6000) * 2.0
fade = np.clip((t - 2.4) / 1.2, 0, 1) * np.clip((DUR - 0.2 - t) / 2.6, 0, 1)
room_out = wind * db(-44) / (np.sqrt(np.mean(wind ** 2)) + 1e-9) + crick * db(-47) / (np.sqrt(np.mean(crick ** 2)) + 1e-9)
room_in = (clock * db(-44) / (np.sqrt(np.mean(clock ** 2)) + 1e-9) + fire * db(-46) / (np.sqrt(np.mean(fire ** 2)) + 1e-9)) * ajar
room = (room_out + room_in) * fade
mix += room; stems['room'] = room

# master: gentle limiter
peak = np.max(np.abs(mix)); g = min(1.0, db(-1) / peak) if peak > 0 else 1
mix *= g
for k in stems: stems[k] *= g
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, 'cache', 'sound.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


# measured levels (the brief: the soft voice at least 6 dB below the calls and above the room tone)
def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
lv = {}
for line in ev['speech']:
    a = line['syl'][0][0] - 0.1 + OFF; b = line['syl'][-1][0] + line['syl'][-1][1] + 0.15 + OFF
    seg = stems['voice'][int(a * SR):int(b * SR)]
    act = seg[np.abs(seg) > 0]
    frame = 1024; fr = [rms_db(seg[i:i + frame]) for i in range(0, len(seg) - frame, frame)]
    lv[line['text']] = {'kind': line['kind'], 'film_t': round(a, 2), 'active_rms_dbfs': round(float(np.percentile(fr, 90)), 1), 'peak_dbfs': round(20 * np.log10(np.max(np.abs(seg)) + 1e-12), 1)}
room_db = rms_db(stems['room'][int(4 * SR):int(37 * SR)])
calls = [v['active_rms_dbfs'] for v in lv.values() if v['kind'] == 'call']; softs = [v['active_rms_dbfs'] for v in lv.values() if v['kind'] == 'soft']
out = {'lines': lv, 'room_tone_rms_dbfs': round(room_db, 1), 'quietest_call_minus_loudest_soft_db': round(min(calls) - max(softs), 1), 'quietest_soft_minus_room_db': round(min(softs) - room_db, 1),
       'note': 'measured on the synthesized stems (90th percentile of 21 ms RMS frames while the line plays); nobody has listened to this sound'}
os.makedirs(os.path.join(os.path.dirname(HERE), 'proof'), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(HERE), 'proof', 'sound_levels.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
