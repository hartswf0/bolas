"""SCION 43 · sound: everything synthesized here in numpy (no recordings). 48 kHz stereo, 38.0 s.
Scene time 0 = film time 3.0 s. Events come from the score's timeline (voice, door) and from the rule engine
(foot plants of the gait, rewrite rules = paper snips, the lie-down, the settle).
Writes build/cache/sound.wav and build/cache/sound_levels.json (measured RMS of the calls, the soft voice, the room tone)."""
import json, math, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 48000
DUR = 38.0
OFF = 3.0
N = int(SR * DUR)
rng = np.random.RandomState(43)
L = np.zeros(N); R = np.zeros(N)
VST = np.zeros(N)  # voice stem, for measurement


def db(x): return 10 ** (x / 20)


def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int((t0) * SR)
    if i0 >= N: return
    sig = sig[:max(0, N - i0)]
    if i0 < 0: sig = sig[-i0:]; i0 = 0
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    L[i0:i0 + len(sig)] += sig * gain * l * 1.414
    R[i0:i0 + len(sig)] += sig * gain * r * 1.414


def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))


def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= np.exp(-((np.log((f + 1) / math.sqrt(lo * hi))) / (0.5 * math.log(hi / lo))) ** 4)
    return np.fft.irfft(X, len(x))


# ------------------------------------------------------------------ formant voice (source-filter, STFT envelope)
PH = {  # F1, F2, F3, voiced amp, noise amp, noise band
    'a': (640, 1190, 2390, 1, 0, None), 'm': (250, 1100, 2300, .45, 0, None), 'n': (260, 1500, 2500, .42, 0, None),
    'i': (400, 1950, 2600, 1, 0, None), 'e': (520, 1500, 2450, 1, 0, None), 'o': (570, 840, 2410, 1, 0, None),
    'l': (360, 1000, 2600, .7, 0, None), 'r': (450, 1300, 1700, .75, 0, None), 'ai': (730, 1090, 2440, 1, 0, None),
    'aiE': (420, 2000, 2600, 1, 0, None), 'h': (520, 1600, 2450, 0, .5, None), 'k': (500, 1500, 2500, 0, 1, (1500, 4000)),
    't': (500, 1700, 2600, 0, 1, (3000, 7000)), 's': (500, 1700, 2600, 0, .7, (4000, 9000)), '_': (500, 1500, 2500, 0, 0, None),
}


def voice(seq, f0s, breath=0.0, rate=1.0):
    """seq: list of (phoneme, dur). f0s: list of (t_rel 0..1, Hz). returns mono signal"""
    tot = sum(d for _, d in seq) / rate
    n = int(tot * SR) + SR // 10
    tt = np.arange(n) / SR
    f0 = np.interp(tt / tot, [a for a, _ in f0s], [b for _, b in f0s]) * (1 + 0.012 * np.sin(2 * math.pi * 5.5 * tt))
    ph = np.cumsum(f0 / SR)
    src = (ph % 1.0) * 2 - 1
    src = src - np.convolve(src, np.ones(8) / 8, 'same')  # tilt
    src = np.convolve(src, np.ones(3) / 3, 'same')
    noise = rng.randn(n)
    # per-sample targets with short crossfades
    bounds = np.cumsum([0] + [d / rate for _, d in seq])
    def track(k):
        vals = np.array([PH[p][k] for p, _ in seq], float)
        centers = (bounds[:-1] + bounds[1:]) / 2
        return np.interp(tt, centers, vals)
    F = [track(0), track(1), track(2)]
    va = np.zeros(n); na = np.zeros(n); nb_lo = np.full(n, 300.0); nb_hi = np.full(n, 8000.0)
    for (p, d), b0, b1 in zip(seq, bounds[:-1], bounds[1:]):
        m = (tt >= b0) & (tt < b1)
        va[m] = PH[p][3]; na[m] = PH[p][4]
        if PH[p][5]: nb_lo[m], nb_hi[m] = PH[p][5]
    sm = np.ones(int(0.018 * SR)) / int(0.018 * SR)
    va = np.convolve(va, sm, 'same'); na = np.convolve(na, sm, 'same')
    ex = src * va * (1 - breath) + noise * (na * 0.35 + va * breath * 0.5)
    # STFT envelope filter
    hop, win = 256, 1024
    w = np.hanning(win)
    out = np.zeros(n + win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    for s0 in range(0, n - win, hop):
        c = s0 + win // 2
        seg = ex[s0:s0 + win] * w
        S = np.fft.rfft(seg)
        env = np.zeros_like(freqs)
        for k, bw, g in ((0, 90, 1.0), (1, 120, 0.7), (2, 180, 0.35)):
            env += g * np.exp(-0.5 * ((freqs - F[k][c]) / bw) ** 2)
        env += 0.03
        if na[c] > 0.05:
            env += na[c] * 0.6 * ((freqs > nb_lo[c]) & (freqs < nb_hi[c]))
        out[s0:s0 + win] += np.fft.irfft(S * env, win) * w
    out = out[:n]
    env = np.convolve(np.abs(out), np.ones(480) / 480, 'same')
    out /= (np.max(np.abs(out)) + 1e-9)
    return out


def utter(text):
    if text == 'come here':
        return voice([('k', .05), ('a', .16), ('m', .09), ('_', .03), ('h', .07), ('i', .10), ('e', .24)],
                     [(0, 205), (.35, 215), (.55, 250), (.8, 230), (1, 175)])
    if text == 'come here!':
        return voice([('k', .05), ('a', .15), ('m', .08), ('_', .03), ('h', .07), ('i', .11), ('e', .26)],
                     [(0, 220), (.35, 235), (.55, 280), (.8, 250), (1, 190)])
    if text == "it's all right":
        return voice([('i', .07), ('t', .03), ('s', .09), ('o', .17), ('l', .07), ('r', .08), ('ai', .14), ('aiE', .14), ('t', .03)],
                     [(0, 170), (.4, 182), (.7, 165), (1, 140)], breath=0.35, rate=0.85)
    if text == 'come in':
        return voice([('k', .05), ('a', .14), ('m', .08), ('i', .12), ('n', .2)], [(0, 172), (.5, 180), (1, 150)], breath=0.35, rate=0.85)


def env_adsr(n, a, r):
    e = np.ones(n); A = int(a * SR); Rr = int(r * SR)
    e[:A] = np.linspace(0, 1, A); e[-Rr:] *= np.linspace(1, 0, Rr); return e


# ------------------------------------------------------------------ the bed: dusk room tone + crickets
bed = lowpass(rng.randn(N), 380) * db(-44)
bed2 = lowpass(rng.randn(N), 2500) * db(-58)
add(bed, 0); add(bed2, 0, pan=0.3)
# fade the bed in/out with the cards
fade = np.ones(N); fade[:int(2.5 * SR)] = np.linspace(0, 1, int(2.5 * SR)); fade[int(36.5 * SR):] = np.linspace(1, 0, N - int(36.5 * SR))
for k in range(150):
    t0 = 2.6 + rng.rand() * 33
    n = int(SR * 0.16)
    tt = np.arange(n) / SR
    ch = np.sin(2 * math.pi * (4300 + 400 * rng.rand()) * tt) * (np.sin(2 * math.pi * 32 * tt) > 0.2) * np.hanning(n)
    add(ch * db(-47 - 6 * rng.rand()), t0, pan=rng.uniform(.2, .9))

# ------------------------------------------------------------------ the voice: calls loud, soft voice >= 6 dB quieter
VOICE_EVENTS = []
for tsc, txt, g in ((1.0, 'come here', -1.0), (3.4, 'come here!', 0.0), (7.45, "it's all right", -14.0), (10.45, "it's all right", -15.0), (26.42, 'come in', -14.5)):
    v = utter(txt)
    add(v * db(g), OFF + tsc, pan=-0.55)
    i0 = int((OFF + tsc) * SR); VST[i0:i0 + len(v)] += v * db(g)
    VOICE_EVENTS.append(dict(t=tsc, text=txt, gain_db=g, n=len(v)))

# ------------------------------------------------------------------ the door (6.2): latch, creak, then the light's warm pad
n = int(0.03 * SR); click = bandpass(rng.randn(n), 1500, 6000) * np.exp(-np.arange(n) / (0.004 * SR))
add(click * db(-20), OFF + 6.18, pan=-0.6)
n = int(0.65 * SR); tt = np.arange(n) / SR
cr = bandpass(rng.randn(n), 250, 900) * (0.6 + 0.4 * np.sin(2 * math.pi * (18 + 30 * tt) * tt)) * env_adsr(n, .05, .3)
add(cr / np.max(np.abs(cr)) * db(-27), OFF + 6.22, pan=-0.6)
n = int(28.5 * SR); tt = np.arange(n) / SR
pad = sum(np.sin(2 * math.pi * f * tt + p) for f, p in ((110, 0), (164.8, 1), (220, 2), (277.2, .5))) / 4
pad *= np.minimum(1, tt / 1.6) * (0.75 + 0.25 * np.sin(2 * math.pi * 0.11 * tt))
pad *= np.linspace(1, 0.6, n) * np.concatenate([np.ones(n - SR), np.linspace(1, 0, SR)])
add(lowpass(pad, 900) * db(-36), OFF + 6.3, pan=-0.4)

# ------------------------------------------------------------------ the dog: paws from the gait solver, the rewrites, the body
import scene
taps = []
prev = None
for i, f in enumerate(scene.FRAMES):
    d = scene.travel(i)
    if f['dog']['act']['moving'] < 0.15: prev = None; continue
    for leg, off in scene.PHASE.items():
        p = (d / scene.D_CYCLE + off) % 1.0
        if prev is not None:
            pp = prev[leg]
            if (pp > scene.STANCE and p < 0.1) or (pp < 0.1 and p > scene.STANCE):  # a foot lands
                taps.append((f['t'], leg))
    prev = {leg: (d / scene.D_CYCLE + off) % 1.0 for leg, off in scene.PHASE.items()}
for t0, leg in taps:
    n = int(0.05 * SR)
    tap = bandpass(rng.randn(n), 900, 4200) * np.exp(-np.arange(n) / (0.006 * SR))
    tap += np.sin(2 * math.pi * 140 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.01 * SR)) * 0.5
    x = scene.FRAMES[int(t0 * 24)]['dog']['x']
    add(tap * db(-33 + (2 if leg.startswith('fore') else 0)), OFF + t0, pan=float(np.clip((x - 1.5) / 3, -0.8, 0.9)))
# rewrite rules -> paper snips (scissors), read from the rendered measurements when present
meas = os.path.join(HERE, 'cache/meas')
snips = []
if os.path.isdir(meas):
    prev = None
    for i in range(768):
        p = os.path.join(meas, '%04d.json' % i)
        if not os.path.exists(p): continue
        m = json.load(open(p))
        key = (m['mode'], m['head'], m['head_mirror'], m['split'], tuple(sorted((k, v > 0.5) for k, v in (m.get('materials') or {}).items())))
        if prev is not None and key != prev: snips.append(m['t'])
        prev = key
for t0 in snips:
    n = int(0.06 * SR)
    s1 = bandpass(rng.randn(n), 3000, 11000) * np.exp(-np.arange(n) / (0.003 * SR))
    s2 = np.roll(s1, int(0.022 * SR)) * 0.6
    x = 2.0
    add((s1 + s2) * db(-31), OFF + t0, pan=0.4)
# lie downs (refusal 4.5, sill 23.9): fur and a soft body thump
for t0 in (4.55, 23.95):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    th = np.sin(2 * math.pi * 70 * tt) * np.exp(-tt / 0.07) * 0.8 + bandpass(rng.randn(n), 400, 3000) * np.exp(-tt / 0.18) * 0.4
    add(th * db(-26), OFF + t0, pan=0.5 if t0 < 10 else -0.15)
# a short whine as it turns back to look (7.46), a sniff as it decides to come (14.7), a sigh as it settles (28.5)
n = int(0.42 * SR); tt = np.arange(n) / SR
f = 760 + 160 * np.sin(math.pi * tt / 0.42) + 12 * np.sin(2 * math.pi * 7 * tt)
wh = np.sin(2 * math.pi * np.cumsum(f) / SR) * env_adsr(n, .06, .2)
add(lowpass(wh, 2500) * db(-36), OFF + 8.3, pan=0.6)
for k in range(2):
    n = int(0.09 * SR); sn = bandpass(rng.randn(n), 1500, 6000) * env_adsr(n, .02, .05)
    add(sn * db(-31), OFF + 14.72 + k * 0.16, pan=0.6)
n = int(0.9 * SR); tt = np.arange(n) / SR
sg = bandpass(rng.randn(n), 300, 1800) * env_adsr(n, .15, .6)
add(sg / np.max(np.abs(sg)) * db(-30), OFF + 28.55, pan=-0.15)
# title / end card: one paper sound each (a sheet laid down)
for t0 in (0.2, 35.1):
    n = int(0.35 * SR); pp = bandpass(rng.randn(n), 600, 7000) * env_adsr(n, .01, .3)
    add(pp / np.max(np.abs(pp)) * db(-30), t0)

L *= fade; R *= fade
mx = max(np.max(np.abs(L)), np.max(np.abs(R)))
if mx > 0.98: L *= 0.98 / mx; R *= 0.98 / mx; VST *= 0.98 / mx


def rms_db(a, b):
    i0, i1 = int(a * SR), int(b * SR); x = (L[i0:i1] + R[i0:i1]) / 2
    return 20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def peak_rms_db(a, b, w=0.3):
    best = -200
    for s in np.arange(a, b - w, 0.05): best = max(best, rms_db(s, s + w))
    return best


lv = {}
for e in VOICE_EVENTS:
    a = OFF + e['t']; b = a + e['n'] / SR
    i0, i1 = int(a * SR), int(b * SR)
    vs = VST[i0:i1]; vr = 20 * math.log10(np.sqrt(np.mean(vs ** 2)) + 1e-12)
    lv['%s@%.2f' % (e['text'], e['t'])] = dict(mix_rms_db=round(rms_db(a, b), 2), mix_loudest_300ms_db=round(peak_rms_db(a, b), 2), voice_stem_rms_db=round(vr, 2))
lv['room_tone_quiet_window_db'] = round(rms_db(OFF + 12.2, OFF + 14.2), 2)
calls = [v['mix_loudest_300ms_db'] for k, v in lv.items() if k.startswith('come here')]
soft = [v['mix_loudest_300ms_db'] for k, v in lv.items() if k.startswith(("it's", 'come in'))]
lv['soft_minus_calls_db_mix_loudest_300ms'] = round(max(soft) - min(calls), 2)
cs = [v['voice_stem_rms_db'] for k, v in lv.items() if k.startswith('come here')]
ss = [v['voice_stem_rms_db'] for k, v in lv.items() if k.startswith(("it's", 'come in'))]
lv['soft_minus_calls_db_voice_stem_rms'] = round(max(ss) - min(cs), 2)
lv['soft_minus_room_db'] = round(min(soft) - lv['room_tone_quiet_window_db'], 2)
lv['paw_taps'] = len(taps); lv['rewrite_snips'] = len(snips)
json.dump(lv, open(os.path.join(HERE, 'cache/sound_levels.json'), 'w'), indent=1)
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, 'cache/sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(json.dumps(lv, indent=1))
