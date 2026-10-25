"""Mix editor. Synthesize the world's sounds and mix them with the voice lines on the film clock.
Film clock = 3 s title + 32 s scene + 3 s end card = 38 s, 48 kHz stereo. Scene time t lands at film time 3 + t.
Sonic perspective: the microphone is the camera. Every source is panned by its screen x and the voice keeps its two
registers apart: calls loud, close to the edge of breaking; soft words 14 dB lower in the source, breathy, low-passed.
Writes build/cache/mix.wav, build/cache/stems/*.wav and build/audio_measure.json (measured from the rendered stems).
"""
import json, os, wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache'); os.makedirs(os.path.join(CACHE, 'stems'), exist_ok=True)
SR = 48000; T0 = 3.0; DUR = 38.0; NS = int(SR * DUR)
AT = json.load(open(os.path.join(HERE, 'audio_timeline.json')))
FOLEY = json.load(open(os.path.join(HERE, 'foley.json')))
rng = np.random.default_rng(47)
K, X0 = 180, 360


def pan_of(x_m):
    return float(np.clip((X0 + x_m * K - 640) / 640, -1, 1))


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'low'); return lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'high'); return lfilter(b, a, x)


def db(v): return 10 ** (v / 20)


def mixs(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out


def smooth(x, k):
    c = np.cumsum(np.concatenate([[0], x])); y = (c[k:] - c[:-k]) / k
    return np.concatenate([np.full(k // 2, y[0]), y, np.full(len(x) - len(y) - k // 2, y[-1])])


stems = {k: np.zeros((NS, 2)) for k in ('voice_call', 'voice_soft', 'room', 'foley_person', 'door', 'dog')}


def put(stem, sig, t_scene, pan, gain_db=0.0):
    a = int((T0 + t_scene) * SR); sig = sig * db(gain_db)
    if a >= NS: return
    n = min(len(sig), NS - a)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    stems[stem][a:a + n, 0] += sig[:n] * l * 1.414; stems[stem][a:a + n, 1] += sig[:n] * r * 1.414


def load16(path):
    w = wave.open(os.path.join(ROOT, path)); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    t = np.arange(int(len(x) * SR / sr)) / SR
    return np.interp(t, np.arange(len(x)) / sr, x)


def porch_space(x, wet=0.12):
    """a few early reflections off the boards and the wall, and a short tail"""
    y = x.copy()
    for d, g in [(0.011, 0.35), (0.019, 0.25), (0.031, 0.18), (0.047, 0.12)]:
        k = int(d * SR); y[k:] += g * wet * 3 * x[:-k]
    tail = lp(rng.standard_normal(int(0.35 * SR)) * np.exp(-np.arange(int(0.35 * SR)) / (0.08 * SR)), 3000)
    return y + wet * fftconvolve(x, tail)[:len(x)] * 0.05


def env_follow(x, ms=12):
    k = int(ms / 1000 * SR); return np.sqrt(smooth(x ** 2, k))


# ---- voice
pperson = {}
for e in AT['events']:
    if e['kind'] != 'voice': continue
    x = load16(e['file'])
    t_mid = (e['t0'] + e['t1']) / 2
    px = -0.28 if t_mid < 4.85 else -1.25
    if e['style'] == 'call':
        x = x / (np.abs(x).max() + 1e-9) * 0.7
        x = np.tanh(2.2 * x) / np.tanh(2.2)                  # pushed: the edge of shouting
        x = hp(x, 140) * 0.62
        x = porch_space(x, 0.18)
        put('voice_call', x, e['t0'], pan_of(px) * 0.8, 0)
    else:
        x = x / (np.abs(x).max() + 1e-9) * 0.7
        x = lp(x, 2600, 2)
        breath = bp(rng.standard_normal(len(x)), 900, 5200) * env_follow(x, 25) * 0.55
        x = x + breath
        x = porch_space(x, 0.08)
        put('voice_soft', x, e['t0'], pan_of(px) * 0.8, -14)
    pperson[e['id']] = px

# ---- room tone: air and crickets
n = NS
air = lp(rng.standard_normal(n), 500, 2) * 0.05 + lp(rng.standard_normal(n), 120, 2) * 0.08
room = np.stack([air, np.roll(air, 1100)], 1)
for c, (f, rate, pan, lvl, ph) in enumerate([(4650, 0.62, 0.7, -46, 0.1), (4300, 0.81, 0.35, -50, 0.4), (4900, 0.55, -0.5, -52, 0.7)]):
    t = np.arange(n) / SR
    sig = np.zeros(n)
    k = ph
    while k < DUR:
        for p in range(3):
            a = int((k + p * 0.035) * SR); m = int(0.018 * SR)
            if a + m < n: sig[a:a + m] += np.sin(2 * np.pi * f * t[:m]) * np.hanning(m)
        k += rate * (0.9 + 0.2 * rng.random())
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    room[:, 0] += sig * db(lvl) * l * 1.414; room[:, 1] += sig * db(lvl) * r * 1.414
fade = np.clip((np.arange(n) / SR - 1.2) / 1.8, 0, 1) * np.clip((DUR - 0.3 - np.arange(n) / SR) / 2.2, 0, 1)
stems['room'] = room * fade[:, None] * 0.55


# ---- synthesized foley
def thump(f0=90, dur=0.18, click=0.3):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t * (1 - 0.3 * t / dur)) * np.exp(-t / (dur / 4))
    s += click * bp(rng.standard_normal(len(t)), 800, 4000) * np.exp(-t / 0.006)
    return s


def nails():
    t = np.arange(int(0.05 * SR)) / SR
    return hp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.0025) * 0.6 + np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.02) * 0.5


def noise_env(dur, lo, hi, attack=0.02, rel=None):
    m = int(dur * SR); t = np.arange(m) / SR
    e = np.minimum(1, t / attack) * np.exp(-t / (rel or dur / 3))
    return bp(rng.standard_normal(m), lo, hi) * e


def creak(dur):
    m = int(dur * SR); s = np.zeros(m); t = 0.0
    while t < dur:
        u = t / dur
        f = 180 + 420 * np.sin(np.pi * u) ** 1.5 + 60 * np.sin(17 * u)
        k = int(t * SR)
        if k < m: s[k] += (0.6 + 0.4 * rng.random()) * np.sin(np.pi * u) ** 0.5
        t += 1 / f * (0.9 + 0.2 * rng.random())
    s = bp(s, 600, 1700, 2) * 1.6 + bp(s, 2000, 3500, 2) * 0.8
    return s / (np.abs(s).max() + 1e-9) * 0.6


for e in AT['events']:
    k = e['kind']
    if k == 'step': put('foley_person', mixs(thump(85, 0.2, 0.5) * 0.5, 0.15 * creak(0.12)), e['t0'], pan_of(e['x']), -16)
    if k == 'sit':
        put('foley_person', noise_env(e['t1'] - e['t0'], 400, 3500, 0.08) * 0.5, e['t0'], pan_of(e['x']), -24)
        put('foley_person', mixs(thump(70, 0.3, 0.2) * 0.6, 0.3 * creak(0.25)), e['t1'] - 0.08, pan_of(e['x']), -18)
    if k == 'touch': put('foley_person', thump(200, 0.06, 0.6) * 0.5, e['t0'], pan_of(e['x']), -26)
    if k == 'creak':
        put('door', creak(e['t1'] - e['t0']), e['t0'], pan_of(e['x']), -16)
    if k == 'cloth': put('foley_person', noise_env(e['t1'] - e['t0'], 600, 4000, 0.05) * 0.5, e['t0'], pan_of(e['x']), -30)

for f in FOLEY:
    k = f['kind']; pan = pan_of(f['x'])
    if k == 'paw': put('dog', nails(), f['t0'], pan, -33 if not f.get('soft') else -38)
    if k == 'thump': put('dog', thump(60, 0.25, 0.15), f['t0'], pan, f.get('g', -14) - 6)
    if k == 'sniff': put('dog', noise_env(0.09, 1500, 6000, 0.01, 0.03), f['t0'], pan, -24)
    if k == 'sigh': put('dog', noise_env(f['dur'], 300, 1800, 0.12, f['dur'] / 2.5), f['t0'], pan, -27)
    if k == 'tailthump': put('dog', thump(75, 0.12, 0.1), f['t0'], pan, -24)

mix = sum(stems.values())
peak = np.abs(mix).max()
g = min(1.0, 0.89 / peak)
mix *= g
for k in stems: stems[k] *= g


def wwrite(path, x):
    with wave.open(path, 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


wwrite(os.path.join(CACHE, 'mix.wav'), mix)
for k, v in stems.items(): wwrite(os.path.join(CACHE, 'stems', k + '.wav'), v)


# ---- measurement (from the stems as written)
def rms_db(x):
    return float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12))


meas = {'peak_dbfs': round(float(20 * np.log10(np.abs(mix).max())), 2), 'lines': []}
for e in AT['events']:
    if e['kind'] != 'voice': continue
    st = stems['voice_call' if e['style'] == 'call' else 'voice_soft'].mean(1)
    seg = np.concatenate([st[int((T0 + p['t0']) * SR):int((T0 + p['t1']) * SR)] for p in e['phones']])
    meas['lines'].append({'id': e['id'], 'style': e['style'], 'text': e['text'], 'rms_dbfs_voiced': round(rms_db(seg), 2)})
room_mono = stems['room'][int(T0 * SR):int((T0 + 32) * SR)].mean(1)
meas['room_tone_rms_dbfs'] = round(rms_db(room_mono), 2)
calls = [l['rms_dbfs_voiced'] for l in meas['lines'] if l['style'] == 'call']
softs = [l['rms_dbfs_voiced'] for l in meas['lines'] if l['style'] == 'soft']
meas['quietest_call_db'] = min(calls); meas['loudest_soft_db'] = max(softs)
meas['soft_below_calls_db'] = round(min(calls) - max(softs), 2)
meas['soft_above_room_db'] = round(min(softs) - meas['room_tone_rms_dbfs'], 2)
# onsets of each line found in the voice stem itself (energy rises 20 dB above the stem's floor)
vs = (stems['voice_call'] + stems['voice_soft']).mean(1)
env = np.sqrt(smooth(vs ** 2, 480))
for l, e in zip(meas['lines'], [e for e in AT['events'] if e['kind'] == 'voice']):
    a = int((T0 + e['t0'] - 0.1) * SR); b = int((T0 + e['t1']) * SR)
    seg = env[a:b]; thr = seg.max() * db(-20)
    l['onset_measured_scene_s'] = round(a / SR - T0 + int(np.argmax(seg > thr)) / SR, 3)
    l['planned_t0'] = e['t0']
json.dump(meas, open(os.path.join(HERE, 'audio_measure.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in meas.items() if k != 'lines'}))
for l in meas['lines']: print(l)
