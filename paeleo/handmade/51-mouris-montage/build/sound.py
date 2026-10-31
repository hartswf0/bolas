"""SCION 51 · sound montage, synthesized here (no recordings).
- voices: a small formant synthesizer speaks the narrated words at the same frames the cut letters appear;
  calls loud and bright, the soft voice breathy and >= 6 dB under the calls, above the room tone.
- the cutting score is audible: every cut makes a grain (cold cuts: a dry splice tick; warm cuts: a soft brush).
- dusk room tone, the dog's footfalls (from its walk), the door, the person's steps.
Writes build/cache/scene.wav (32 s) and sound-levels.json (measured)."""
import json, math, os, wave
import numpy as np
from lib import OUT, FPS

SR = 48000
N = int(32 * SR)
rng = np.random.RandomState(51)
CACHE = os.path.join(OUT, 'build/cache')


def db(x):
    return 20 * math.log10(max(x, 1e-9))


def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def resonate(x, f, bw):
    """time-varying 2-pole resonator; f, bw arrays (Hz)"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    r = np.exp(-math.pi * bw / SR); c = 2 * r * np.cos(2 * math.pi * f / SR); r2 = r * r
    g = (1 - r)
    for n in range(len(x)):
        v = g[n] * x[n] + c[n] * y1 - r2[n] * y2
        y2 = y1; y1 = v; y[n] = v
    return y


# phonemes: (F1, F2, F3, voiced amp, noise amp)
PH = {'k': (300, 1800, 2500, 0, 0.0), 'uh': (640, 1190, 2390, 1, 0), 'm': (260, 1000, 2200, 0.35, 0), 'h': (500, 1600, 2500, 0, 0.6),
      'ih': (400, 1950, 2600, 1, 0), 'eh': (580, 1700, 2500, 1, 0), 'r': (420, 1300, 1700, 0.8, 0), 'ts': (3000, 5000, 6500, 0, 0.5),
      'aw': (580, 880, 2500, 1, 0), 'l': (360, 1000, 2500, 0.7, 0), 'ai': (760, 1250, 2500, 1, 0), 'iy': (330, 2200, 2900, 1, 0),
      't': (3000, 4500, 6000, 0, 0.4), 'n': (280, 1500, 2500, 0.4, 0), 'sil': (500, 1500, 2500, 0, 0)}
WORDS = {  # (phoneme, duration s)
    'come': [('k', 0.05), ('uh', 0.16), ('m', 0.10)],
    'here': [('h', 0.07), ('ih', 0.16), ('eh', 0.08), ('r', 0.14)],
    "it's": [('ih', 0.10), ('t', 0.03), ('ts', 0.09)],
    'all': [('aw', 0.20), ('l', 0.10)],
    'right': [('r', 0.07), ('ai', 0.20), ('iy', 0.07), ('t', 0.05)],
    'in': [('ih', 0.13), ('n', 0.14)],
}


def speak(word, f0a, f0b, loud, breath, bright):
    seq = WORDS[word]; dur = sum(d for _, d in seq); n = int(dur * SR)
    tt = np.arange(n) / SR
    # piecewise phoneme targets, crossfaded 25 ms
    F = np.zeros((3, n)); va = np.zeros(n); na = np.zeros(n)
    t0 = 0
    for ph, d in seq:
        a, b = int(t0 * SR), int((t0 + d) * SR); p = PH[ph]
        F[0, a:b], F[1, a:b], F[2, a:b] = p[0], p[1], p[2]; va[a:b] = p[3]; na[a:b] = p[4]; t0 += d
    k = np.ones(int(0.025 * SR)) / int(0.025 * SR)
    F = np.stack([np.convolve(np.pad(f, (len(k), len(k)), 'edge'), k, 'same')[len(k):-len(k)] for f in F])
    va = np.convolve(va, k, 'same'); na = np.convolve(na, k, 'same')
    f0 = f0a + (f0b - f0a) * (tt / dur) + 3 * np.sin(2 * math.pi * 5.5 * tt)
    ph = np.cumsum(f0 / SR)
    src = np.zeros(n)
    for h in range(1, 30):
        src += np.sin(2 * math.pi * h * ph) / h ** (1.0 if bright else 1.35) * (f0 * h < 5000)
    noise = rng.randn(n)
    ex = src * va * (1 - breath) + noise * (0.35 * va * breath + na)
    out = np.zeros(n)
    for j, bw in enumerate((90, 120, 170)):
        out += resonate(ex, F[j], np.full(n, bw)) * (1.0, 0.6, 0.3)[j]
    if 'k' in [p for p, _ in seq]:
        out[:int(0.012 * SR)] += rng.randn(int(0.012 * SR)) * 0.3
    env = np.minimum(1, np.minimum(tt / 0.02, (dur - tt) / 0.04))
    out = out * env
    return loud * out / (np.abs(out).max() + 1e-9)


def place(buf, x, t):
    a = int(t * SR); b = min(len(buf), a + len(x))
    if b > a:
        buf[a:b] += x[:b - a]


def grain_cold():
    n = int(0.03 * SR); tt = np.arange(n) / SR
    tick = rng.randn(n) * np.exp(-tt / 0.003)
    ping = sum(np.sin(2 * math.pi * f * tt) for f in (2310, 3770, 5120)) * np.exp(-tt / 0.012) * 0.25
    return (tick + ping)


def grain_warm():
    n = int(0.12 * SR); tt = np.arange(n) / SR
    x = np.convolve(rng.randn(n), np.ones(40) / 40, 'same')
    return x * np.sin(math.pi * tt / tt[-1]) ** 2 * 3


def thud(f=90, d=0.12):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.sin(2 * math.pi * f * tt * (1 - 0.3 * tt / d)) * np.exp(-tt / 0.03) + np.convolve(rng.randn(n), np.ones(20) / 20, 'same') * np.exp(-tt / 0.01)


def build():
    voice = np.zeros(N); fx = np.zeros(N); room = np.zeros(N)
    words = json.load(open(os.path.join(OUT, 'words.json')))['words']
    marks = []
    for wd in words:
        ws = [w.lower() for w in wd['text'].split(' ')]
        for w, t in zip(ws, wd['syll']):
            if wd['voice'] == 'call':
                big = 1.0 if wd['spoken'][0] > 3 else 0.85
                x = speak(w, 175 if w == 'come' else 205, 195 if w == 'come' else 150, 0.62 * big, 0.08, True)
            else:
                x = speak(w, 128, 112, 0.6, 0.55, False) * 0.38
            place(voice, x, t); marks.append((wd['voice'], t, t + len(x) / SR))
    # the cutting score, audible
    cuts = json.load(open(os.path.join(OUT, 'cutting-score.json')))['cuts']
    for c in cuts:
        g = grain_cold() * 0.05 if c['temperature'] == 'cold' else (grain_warm() * 0.010 if c['temperature'] == 'warm' else grain_cold() * 0.02)
        place(fx, g, c['frame'] / FPS)
    # the dog's footfalls from its walk (every 0.275 m: one diagonal pair lands)
    poses = json.load(open(os.path.join(CACHE, 'poses.json')))
    w = [p['dog']['walk'] for p in poses]
    for k in range(1, len(w)):
        if math.floor(w[k] / 0.275) != math.floor(w[k - 1] / 0.275):
            place(fx, thud(180, 0.06) * 0.05, k / FPS)
    # the person's steps, the sitting rustle, the door
    for t in (4.66, 4.95, 5.22):
        place(fx, thud(80) * 0.09, t)
    n = int(0.5 * SR); tt = np.arange(n) / SR
    place(fx, np.convolve(rng.randn(n), np.ones(30) / 30, 'same') * np.sin(math.pi * tt / tt[-1]) * 0.15, 5.6)
    n = int(0.7 * SR); tt = np.arange(n) / SR
    creak = resonate(rng.randn(n) * 0.5, 600 + 500 * tt / tt[-1] + 60 * np.sin(2 * math.pi * 23 * tt), np.full(n, 30))
    place(fx, creak / (np.abs(creak).max() + 1e-9) * 0.05 * np.sin(math.pi * tt / tt[-1]), 6.2)
    # the dog: a breath out as it lies on the sill and as it settles
    for t, a in ((24.1, 0.03), (28.6, 0.025)):
        n = int(0.8 * SR); tt = np.arange(n) / SR
        b = resonate(rng.randn(n), np.full(n, 700), np.full(n, 400))
        place(fx, b / np.abs(b).max() * a * np.sin(math.pi * tt / tt[-1]) ** 2, t)
    # room tone: dusk air + far crickets; the warm light adds a low hum after the door opens
    tt = np.arange(N) / SR
    air = np.convolve(rng.randn(N), np.ones(200) / 200, 'same') * 0.05
    crick = np.sin(2 * math.pi * 4400 * tt) * (np.sin(2 * math.pi * 2.1 * tt) > 0.85) * (np.sin(2 * math.pi * 33 * tt) > 0) * 0.0009
    open_k = np.clip((tt - 6.2) / 0.8, 0, 1)
    hum = (np.sin(2 * math.pi * 110 * tt) + 0.5 * np.sin(2 * math.pi * 165 * tt)) * 0.0022 * open_k
    room = air + crick + hum
    mix = voice + fx + room
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    # measured levels (on the mix, A-weighting not applied): RMS over each spoken word window
    lv = {'call': [], 'soft': []}
    for v, a, b in marks:
        lv[v].append(db(rms(mix[int(a * SR):int(b * SR)])))
    tone = db(rms(mix[int(12.5 * SR):int(14.0 * SR)]))
    res = {'about': 'measured from build/cache/scene.wav: RMS dBFS of each spoken word window, and room tone (12.5-14.0 s, no voice)',
           'call_words_db': [round(x, 1) for x in lv['call']], 'soft_words_db': [round(x, 1) for x in lv['soft']],
           'call_mean_db': round(float(np.mean(lv['call'])), 1), 'soft_mean_db': round(float(np.mean(lv['soft'])), 1),
           'soft_under_calls_db': round(float(np.mean(lv['call']) - np.mean(lv['soft'])), 1),
           'soft_loudest_db': round(max(lv['soft']), 1), 'call_quietest_db': round(min(lv['call']), 1),
           'room_tone_db': round(tone, 1), 'voice_onsets_s': [round(a, 3) for _, a, _ in marks]}
    json.dump(res, open(os.path.join(OUT, 'sound-levels.json'), 'w'), indent=1)
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(CACHE, 'scene.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
    return res


if __name__ == '__main__':
    print(json.dumps(build(), indent=1))
