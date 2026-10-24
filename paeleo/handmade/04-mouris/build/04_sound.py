"""SCION-04 · the sound, synthesized with numpy, timed from the score and from the torrent's own statistics.
- the torrent: every replaced picture is a click (dog: woody, ground: paper ticks, words: harsh); its density is the boil
- a projector purr at 24 Hz; dusk crickets that thin out when the door light comes
- the voice: a source-filter formant voice (glottal pulses through moving formants): COME HERE loud, it's all right soft
- the door's stick-slip creak, the paws (from the score's walk phase), the dog's exhale when it lies down
- a warm chord that rises with the door light and holds at the end
Output: cache/sound.wav (38 s, 48 kHz stereo)."""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000; DUR = 38.0; OFF = 3.0; N = int(SR * DUR)
rng = np.random.default_rng(404)
SCORE = json.load(open(os.path.join(HERE, '../../score/threshold-score.json')))
FR = SCORE['frames']
stats = json.load(open(os.path.join(HERE, 'cache/stats.json')))
cards = json.load(open(os.path.join(HERE, 'cache/card_stats.json')))
trace = json.load(open(os.path.join(HERE, '..', 'trace.json')))['frames']
L = np.zeros(N); R = np.zeros(N)

def fft_filter(x, fn):
    n = len(x); X = np.fft.rfft(x, 2 * n); f = np.fft.rfftfreq(2 * n, 1 / SR)
    return np.fft.irfft(X * fn(f), 2 * n)[:n]
def band(x, lo, hi, order=2):
    return fft_filter(x, lambda f: 1 / np.sqrt(1 + ((f * f - lo * hi) / (np.maximum(f, 1) * (hi - lo))) ** (2 * order)))
def lowpass(x, fc, order=2): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order)))
def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i): N - i] if i < 0 else sig[:N - i]; i = max(i, 0)
    L[i:i + len(s)] += s * gain * math.cos((pan + 1) * math.pi / 4) * 1.41
    R[i:i + len(s)] += s * gain * math.sin((pan + 1) * math.pi / 4) * 1.41

# ---------------------------------------------------------------- the torrent: one click per replaced picture
GRAIN = {}
def grain(kind):
    if kind in GRAIN: return GRAIN[kind]
    n = int(SR * {'dog': 0.006, 'ground': 0.003, 'words': 0.009, 'person': 0.005}[kind])
    out = []
    for v in range(6):
        e = np.exp(-np.arange(n) / (n / 4)); z = rng.standard_normal(n) * e
        lo, hi = {'dog': (500, 1800), 'ground': (2500, 7000), 'words': (900, 4000), 'person': (1200, 3000)}[kind]
        g = band(np.concatenate([z, np.zeros(n)]), lo * (0.8 + 0.4 * rng.random()), hi)[:2 * n]
        out.append(g / (np.abs(g).max() + 1e-9))
    GRAIN[kind] = out; return out
GROUPS = {'dog': ['dog', 'dogeye'], 'ground': ['sky', 'yard', 'wall', 'beam', 'floor', 'trim', 'inside', 'panel', 'spill', 'moon'], 'words': ['words'], 'person': ['person', 'face', 'hand']}
LEVEL = {'dog': 0.06, 'ground': 0.022, 'words': 0.05, 'person': 0.04}
def clicks(count, t0, kind, pan_c=0.0, spread=0.6):
    if count <= 0: return
    n = min(count, 160); g = LEVEL[kind] * (count / n) ** 0.5
    G = grain(kind)
    for _ in range(n):
        put(G[rng.integers(len(G))], t0 + rng.random() / 24, g * (0.5 + rng.random()), float(np.clip(pan_c + spread * (rng.random() * 2 - 1), -1, 1)))
for k, s in enumerate(stats):
    t = OFF + s['t']; tr = trace[k]; dpan = (tr['x_screen'] / 1280) * 2 - 1
    for kind, names in GROUPS.items():
        c = sum(s.get(nm, 0) for nm in names)
        clicks(c, t, kind, dpan if kind == 'dog' else (-0.4 if kind == 'person' else 0.0), 0.25 if kind == 'dog' else 0.9)
for k, c in enumerate(cards['title']): clicks(int(c * 0.5), k / 24, 'ground')
for k, c in enumerate(cards['end']): clicks(c, 35.0 + k / 24, 'ground')

# ---------------------------------------------------------------- projector purr and dusk
t_all = np.arange(N) / SR
purr = lowpass(rng.standard_normal(N), 180) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t_all) ** 8)
purr *= 0.035 / (np.abs(purr).max() + 1e-9) * 3
door_t = next(f['t'] for f in FR if f['door'] == 'open')
light = np.clip((t_all - OFF - door_t) / 1.2, 0, 1)
L += purr; R += purr
for k in range(int(DUR / 0.37)):
    t = 0.2 + k * 0.37 + rng.random() * 0.2
    if 3 <= t < 35:
        amp = 0.010 * (1 - 0.7 * float(np.interp(t, t_all[::480], light[::480])))
        for j in range(3):
            n = int(0.018 * SR); tt = np.arange(n) / SR
            put(np.sin(2 * np.pi * (4300 + 200 * (k % 3)) * tt) * np.sin(np.pi * tt / tt[-1]), t + j * 0.032, amp, 0.7 if k % 2 else -0.6)

# ---------------------------------------------------------------- the voice (formant synthesis)
VOW = {'a': (700, 1220, 2600), 'u': (640, 1190, 2390), 'i': (300, 2300, 3000), 'I': (400, 1950, 2600), 'e': (450, 1800, 2550),
       'o': (570, 840, 2410), 'O': (500, 800, 2500), 'ai': (700, 1200, 2600), 'm': (250, 1100, 2400), 'n': (260, 1700, 2600)}
def voice(segs, f0a, f0b, breath, amp):
    """segs: list of (dur, formant-key-from, formant-key-to, voiced, noise) ; returns signal"""
    total = sum(s[0] for s in segs); n = int(total * SR)
    tt = np.arange(n) / SR
    f0 = np.interp(tt, [0, total * 0.35, total], [f0a, f0a * 1.06, f0b]) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * tt))
    ph = np.cumsum(f0 / SR); pulses = np.zeros(n)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]; pulses[idx] = 1
    glott = lowpass(pulses, 900, 1) * 30
    noise = rng.standard_normal(n)
    voiced = np.zeros(n); noisy = np.zeros(n); F = np.zeros((n, 3)); pos = 0
    for (d, a, b, v, z) in segs:
        m = int(d * SR); r = np.linspace(0, 1, m)[:, None]
        F[pos:pos + m] = np.array(VOW[a]) * (1 - r) + np.array(VOW[b]) * r
        voiced[pos:pos + m] = v; noisy[pos:pos + m] = z; pos += m
    k = np.ones(400) / 400; voiced = np.convolve(voiced, k, 'same'); noisy = np.convolve(noisy, k, 'same')
    src = glott * voiced * (1 - breath) + noise * (breath * voiced * 0.6 + noisy)
    # short-time source-filter
    hop = 256; win = 1024; out = np.zeros(n + win); w = np.hanning(win)
    f = np.fft.rfftfreq(win, 1 / SR)
    for st in range(0, n - win, hop):
        fr = src[st:st + win] * w; Fm = F[st + win // 2]
        env = sum(g / (1 + ((f - fc) / (bw)) ** 2) for fc, bw, g in zip(Fm, (80, 110, 160), (1.0, 0.6, 0.3)))
        out[st:st + win] += np.fft.irfft(np.fft.rfft(fr) * env, win) * w
    out = out[:n]
    e = np.minimum(1, np.minimum(tt / 0.03, (total - tt) / 0.08))
    out *= e
    return out / (np.abs(out).max() + 1e-9) * amp
COME_HERE = [(0.05, 'u', 'u', 0, 1.0), (0.16, 'u', 'u', 1, 0), (0.08, 'm', 'm', 1, 0), (0.06, 'e', 'e', 0, 0.8), (0.30, 'I', 'e', 1, 0)]
ALL_RIGHT = [(0.08, 'I', 'I', 1, 0), (0.07, 'I', 'I', 0, 0.5), (0.20, 'O', 'o', 1, 0), (0.08, 'e', 'e', 1, 0.05), (0.30, 'ai', 'i', 1, 0), (0.05, 'i', 'i', 0, 0.4)]
COME_IN = [(0.05, 'u', 'u', 0, 0.8), (0.15, 'u', 'u', 1, 0), (0.07, 'm', 'm', 1, 0), (0.22, 'I', 'I', 1, 0), (0.12, 'n', 'n', 1, 0)]
voice_events = []
prev = 'none'
for f in FR:
    v = f['person']['voice']
    if v != prev and v != 'none': voice_events.append((f['t'], v))
    prev = v
for (t, v) in voice_events:
    if v == 'call':
        sig = voice(COME_HERE, 205, 175, 0.08, 0.30)
        put(sig, OFF + t + 0.03, 1.0, -0.45)
    else:
        segs = COME_IN if t > 20 else ALL_RIGHT
        sig = voice(segs, 150, 118, 0.45, 0.13)
        put(sig, OFF + t + 0.05, 1.0, -0.5)

# ---------------------------------------------------------------- door creak (stick-slip) and the light chord
n = int(1.1 * SR); tt = np.arange(n) / SR
rate = 35 + 70 * np.sin(np.pi * tt / tt[-1]) ** 1.5
ph = np.cumsum(rate / SR); imp = np.zeros(n); imp[np.nonzero(np.diff(np.floor(ph)) > 0)[0]] = 1
creak = band(imp * (0.6 + 0.4 * rng.random(n)), 450, 1600) + 0.5 * band(imp, 1800, 2600)
creak *= np.sin(np.pi * tt / tt[-1]) ** 0.5
put(creak / (np.abs(creak).max() + 1e-9), OFF + door_t, 0.16, -0.3)
chord = np.zeros(N)
for fq, g in ((110, 1), (164.8, 0.7), (220, 0.6), (277.2, 0.45), (329.6, 0.3)):
    chord += g * np.sin(2 * np.pi * fq * t_all * (1 + 0.002 * np.sin(2 * np.pi * 0.21 * t_all + fq)))
lie_t = OFF + next(c['t'] for c in SCORE['choices'] if c['to'] == 'lie_down')
ch_env = 0.018 * light * (0.6 + 0.4 * np.clip((t_all - lie_t) / 3, 0, 1)) * np.clip((DUR - 0.2 - t_all) / 2.5, 0, 1)
chord = lowpass(chord, 900) * ch_env
L += chord * 0.95; R += chord

# ---------------------------------------------------------------- the dog's body: paws, huffs, exhale
def thump(gain, pan, t):
    n = int(0.06 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt / 0.018) + 0.3 * band(rng.standard_normal(n), 800, 2500) * np.exp(-tt / 0.006)
    put(s, t, gain, pan)
prev_ph = None
for k, f in enumerate(FR):
    a = f['dog']['act']; ph = a['walk_phase']
    if prev_ph is not None and a['moving'] > 0.3:
        if math.floor(ph / math.pi) != math.floor(prev_ph / math.pi):
            pan = (trace[k]['x_screen'] / 1280) * 2 - 1
            thump(0.10 if f['dog']['state'] == 'retreat' else 0.06, pan, OFF + f['t'])
    prev_ph = ph
def breath(t, dur, gain, pan, lo=300, hi=1400):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = band(rng.standard_normal(n), lo, hi) * np.sin(np.pi * tt / tt[-1]) ** 2 * np.exp(-tt / dur)
    put(s / (np.abs(s).max() + 1e-9), t, gain, pan)
for c in SCORE['choices']:
    pan = (trace[int(c['t'] * 24)]['x_screen'] / 1280) * 2 - 1
    if c['to'] == 'refuse': breath(OFF + c['t'] + 0.3, 0.35, 0.10, pan, 500, 2200)
    if c['to'] == 'lie_down': breath(OFF + c['t'] + 0.5, 1.1, 0.11, pan)
breath(OFF + 28.9, 1.6, 0.10, 0.1)    # chin on the paws: the long exhale that starts the last hold

# ---------------------------------------------------------------- master
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.4) / 1.4
mix *= 0.89 / np.abs(mix).max()
fade = np.minimum(1, np.minimum(t_all / 0.05, (DUR - t_all) / 0.6))[:, None]
mix *= fade
with wave.open(os.path.join(HERE, 'cache/sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('sound ok', mix.shape)
