"""SCION-27 · audio timing integrator. python3 build/sound.py
Reads build/cache/audio.json (event list compiled from the score by solve.ts: every paw plant, every spoken line, the door,
the body meeting the boards, the tail thumping) and synthesises the whole 38 s track with numpy. No samples, no recordings.
Writes build/cache/public/mix.wav (48 kHz stereo) and ../audio.json (the audio manifest, with measured levels)."""
import json, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
A = json.load(open(os.path.join(HERE, 'cache/audio.json')))
OFF, TOTAL = A['offset_s'], A['total_s']
N = int(SR * TOTAL)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(27)
db = lambda d: 10 ** (d / 20)


def put(sig, t, pan=0.0, gain=1.0):
    i = int(round(t * SR)); j = min(N, i + len(sig))
    if i >= N or j <= 0: return
    s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); R[i:j] += s * np.sqrt(0.5 * (1 + pan))


def onepole(x, a):
    y = np.empty_like(x); acc = 0.0
    for k in range(len(x)): acc += a * (x[k] - acc); y[k] = acc
    return y


def lowpass(x, fc):
    # fast one-pole via cumulative filter in blocks (vectorised with scipy-free recursion using lfilter-like trick)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    return onepole(x, a)


def reson(x, f, bw):
    """two-pole resonator with per-sample frequency/bandwidth arrays (Klatt style)"""
    f = np.broadcast_to(f, x.shape); bw = np.broadcast_to(bw, x.shape)
    r = np.exp(-np.pi * bw / SR); c = -r * r; b = 2 * r * np.cos(2 * np.pi * f / SR); a = 1 - b - c
    y = np.zeros_like(x); y1 = y2 = 0.0
    for k in range(len(x)):
        v = a[k] * x[k] + b[k] * y1 + c[k] * y2; y2 = y1; y1 = v; y[k] = v
    return y


# ---------------- voice: a source-filter formant voice ----------------
V = {'ʌ': (640, 1190, 2390), 'm': (280, 1250, 2200), 'n': (280, 1700, 2500), 'ɪ': (400, 1900, 2600), 'ə': (520, 1500, 2500),
     'ɔ': (570, 840, 2410), 'l': (360, 1300, 2700), 'r': (420, 1250, 1650), 'a': (750, 1250, 2500), 'i': (330, 2100, 2800),
     'h': (500, 1500, 2500), 's': (500, 1500, 2500), 't': (500, 1700, 2600), 'k': (450, 1600, 2400)}
UNVOICED = {'h': 0.0, 's': 0.0, 't': 0.0, 'k': 0.0}
NASAL = {'m': 0.35, 'n': 0.35, 'l': 0.6, 'r': 0.7}


def voice(plan, f0keys, dur, loud=1.0, breath=0.08):
    """plan: list of (phoneme, seconds); f0keys: [(u, Hz)] over the utterance (u in 0..1)"""
    n = int(SR * dur); t = np.arange(n) / SR
    # per-sample formant targets from the plan, smoothed (coarticulation)
    F = np.zeros((3, n)); amp = np.zeros(n); noi = np.zeros(n); pos = 0
    for ph, d in plan:
        m = int(SR * d); sl = slice(pos, min(n, pos + m))
        F[:, sl] = np.array(V[ph])[:, None]
        if ph in UNVOICED: amp[sl] = 0.0; noi[sl] = {'h': 0.35, 's': 0.6, 't': 0.9, 'k': 0.9}[ph]
        else: amp[sl] = NASAL.get(ph, 1.0); noi[sl] = breath
        if ph in ('t', 'k'):   # stop: silence then burst
            q = sl.start; noi[q:q + int(0.6 * m)] = 0; amp[q:q + int(0.6 * m)] = 0
        pos += m
    k = int(0.025 * SR)
    ker = np.hanning(2 * k + 1); ker /= ker.sum()
    F = np.array([np.convolve(np.pad(fr, k, mode='edge'), ker, 'valid') for fr in F])
    amp = np.convolve(np.pad(amp, k, mode='edge'), ker, 'valid'); noi = np.convolve(np.pad(noi, k // 2, mode='edge'), np.hanning(k + 1) / np.hanning(k + 1).sum(), 'valid')[:n]
    us = np.array([u for u, _ in f0keys]); fs = np.array([f for _, f in f0keys])
    f0 = np.interp(t / dur, us, fs) * (1 + 0.012 * np.sin(2 * np.pi * 5.3 * t))   # a little vibrato
    ph = np.cumsum(f0 / SR) % 1.0
    glott = np.where(ph < 0.6, 0.5 * (1 - np.cos(np.pi * ph / 0.6)), np.cos(np.pi * (ph - 0.6) / 0.8)) ; glott = np.diff(glott, prepend=glott[0]) * 40
    src = glott * amp + rng.standard_normal(n) * noi * 0.6
    y = reson(src, F[0], 90) * 1.0 + reson(src, F[1], 120) * 0.55 + reson(src, F[2], 170) * 0.3
    # fricative /s/ is high-passed noise
    hiss = rng.standard_normal(n) * (noi > 0.5) * (noi - 0.5) * 2
    y += (hiss - lowpass(hiss, 3500)) * 0.25
    env = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.05)).clip(0, 1)
    y *= env
    return y / (np.abs(y).max() + 1e-9) * loud


UTT = {
    'Come here.': ([('k', .06), ('ʌ', .17), ('m', .09), ('h', .07), ('ɪ', .16), ('ə', .2)], [(0, 205), (.35, 215), (.55, 262), (.8, 240), (1, 190)]),
    'Come here!': ([('k', .05), ('ʌ', .15), ('m', .08), ('h', .06), ('ɪ', .16), ('ə', .18)], [(0, 225), (.35, 235), (.55, 292), (.8, 262), (1, 205)]),
    'It’s all right.': ([('ɪ', .08), ('t', .04), ('s', .1), ('ɔ', .16), ('l', .09), ('r', .07), ('a', .14), ('i', .1), ('t', .05)],
                             [(0, 168), (.4, 160), (.75, 150), (1, 132)]),
    'Come in.': ([('k', .05), ('ʌ', .14), ('m', .08), ('ɪ', .16), ('n', .14)], [(0, 160), (.5, 152), (1, 132)]),
}
CALL_DB, SOFT_DB = -5.0, -19.0
voice_log = []
for e in A['events']:
    if e['kind'] in ('voice_call', 'voice_soft'):
        plan, f0 = UTT[e['text']]; dur = sum(d for _, d in plan) + 0.06
        soft = e['kind'] == 'voice_soft'
        y = voice(plan, f0, dur, loud=db(SOFT_DB if soft else CALL_DB), breath=0.22 if soft else 0.06)
        if soft: y = lowpass(y, 2600) * 1.6
        t0 = OFF + e['t'] + 0.05
        put(y, t0, pan=-0.35)
        voice_log.append({'t_film': round(t0, 3), 't_scene': round(t0 - OFF, 3), 'dur': round(dur, 3), 'text': e['text'], 'kind': e['kind']})

# ---------------- the dog and the porch ----------------
def knock(f, dec, n_ms, noise=0.3, hp=False):
    n = int(SR * n_ms / 1000); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + noise * rng.standard_normal(n) * np.exp(-t / (dec * 0.4))
    if hp: y = y - lowpass(y, 1500)
    return y


for e in A['events']:
    k = e['kind']; t = OFF + e['t']
    pan = e.get('pan', 0.2)
    if k == 'paw':
        y = knock(210 + 60 * rng.random(), 0.012, 45, 0.5) * 0.5; c = knock(3000, 0.002, 8, 1.0, hp=True); y[:len(c)] += c * 0.35
        put(y, t, pan, db(-33) * e.get('gain', 1))
    elif k == 'body_down':
        y = knock(68, 0.06, 260, 0.6); y = lowpass(y, 400); put(y / np.abs(y).max(), t, pan, db(-21))
    elif k == 'sigh':
        n = int(SR * 0.7); tt = np.arange(n) / SR; y = rng.standard_normal(n) * np.sin(np.pi * tt / 0.7) ** 2
        y = reson(y, 750, 600) + 0.4 * reson(y, 1600, 800); put(y / np.abs(y).max(), t, pan, db(-31))
    elif k == 'tail_thump':
        y = lowpass(knock(105, 0.025, 90, 0.4), 700); put(y / np.abs(y).max(), t, pan, db(-29) * (0.6 + 0.5 * e.get('gain', 1)))
    elif k == 'person_step':
        y = lowpass(knock(140, 0.03, 130, 0.5), 1200); put(y / np.abs(y).max(), t, -0.3, db(-26))
    elif k == 'person_sit':
        n = int(SR * (e['t1'] - e['t'])); tt = np.arange(n) / SR
        y = rng.standard_normal(n) * np.sin(np.pi * tt / tt[-1]) ** 2; y = y - lowpass(y, 900); y = lowpass(y, 4000)
        put(y / np.abs(y).max(), t, -0.3, db(-33))
        y2 = lowpass(knock(95, 0.05, 220, 0.5), 600); put(y2 / np.abs(y2).max(), t + 0.45, -0.3, db(-25))
    elif k == 'door_creak':
        d = e['t1'] - e['t']; n = int(SR * d); tt = np.arange(n) / SR
        f0 = 260 + 280 * (tt / d) ** 0.7 + 25 * np.sin(2 * np.pi * 7 * tt)
        ph = np.cumsum(f0 / SR); stick = (ph % 1.0) ** 6 * (1 + 0.6 * rng.random(n))
        y = reson(stick, 1150, 260) + 0.6 * reson(stick, 2300, 400) + 0.4 * reson(stick, 640, 200)
        y *= np.sin(np.pi * tt / d) ** 0.6; put(y / np.abs(y).max(), t, -0.4, db(-23))
    elif k == 'wind_gust':
        d = e['t1'] - e['t']; n = int(SR * d); tt = np.arange(n) / SR
        y = lowpass(rng.standard_normal(n), 500) * np.sin(np.pi * tt / d) ** 2; put(y / np.abs(y).max(), t, 0.2, db(-30))

# ---------------- the dusk: wind bed, crickets, and the room once the door opens ----------------
tt = np.arange(N) / SR
bed = lowpass(rng.standard_normal(N), 260) * (0.7 + 0.3 * np.sin(2 * np.pi * tt / 11.0))
bed = bed / np.abs(bed).max() * db(-40)
fade = np.clip((tt - 0.3) / 2.0, 0, 1) * np.clip((TOTAL - tt) / 1.6, 0, 1)
L += bed * fade; R += bed * fade
for c, (fc, period, pan, lev) in enumerate([(4500, 0.83, -0.7, -41), (4820, 1.07, 0.75, -43), (4300, 1.31, 0.1, -45)]):
    t = 0.8 + rng.random() * 0.5
    while t < TOTAL - 1.0:
        n = int(SR * 0.12); x = np.arange(n) / SR
        pulses = (np.sin(2 * np.pi * 30 * x) > 0.2) * np.sin(np.pi * x / 0.12)
        y = np.sin(2 * np.pi * fc * x) * pulses
        put(y, t, pan, db(lev) * fade[int(t * SR)])
        t += period * (0.85 + 0.3 * rng.random())
# the room: a clock ticking and a low warm hum, opening up with the door (scene 6.2–6.85 s)
door = np.clip((tt - (OFF + 6.2)) / 0.65, 0, 1) * 0.75 + 0.25
door[tt < OFF] = 0
door[tt > OFF + 32] *= np.clip((OFF + 32 + 1.5 - tt[tt > OFF + 32]) / 1.5, 0, 1)
hum = (np.sin(2 * np.pi * 60 * tt) * 0.5 + np.sin(2 * np.pi * 120 * tt) * 0.2) * db(-50) * door
L += hum * 0.8; R += hum * 0.6
for s in np.arange(OFF + 0.5, OFF + 32.5, 1.0):
    y = knock(2400, 0.003, 12, 0.6, hp=True); put(y, s, -0.45, db(-42) * door[int(s * SR)])

mix = np.stack([L, R], 1)
peak = np.abs(mix).max()
if peak > db(-1): mix *= db(-1) / peak
out = os.path.join(HERE, 'cache/public/mix.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())

# measured levels of the spoken lines in the mix (RMS over each line, dBFS) and of the room tone alone
mono = mix.mean(1)
def rms_db(a, b): seg = mono[int(a * SR):int(b * SR)]; return round(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-12), 2)
for v in voice_log: v['rms_dbfs'] = rms_db(v['t_film'], v['t_film'] + v['dur'])
room = rms_db(OFF + 12.5, OFF + 14.5)
calls = [v['rms_dbfs'] for v in voice_log if v['kind'] == 'voice_call']; softs = [v['rms_dbfs'] for v in voice_log if v['kind'] == 'voice_soft']
man = {'schema': 'scion27.audio/1', 'sr': SR, 'file': 'build/cache/public/mix.wav (muxed into film.mp4 as AAC)', 'offset_s': OFF,
       'synthesis': 'numpy only: formant voice (glottal pulse + 3 resonators), knocks, filtered noise; no samples, no recordings',
       'lines': voice_log, 'room_tone_rms_dbfs_scene_12.5_14.5': room,
       'soft_minus_call_db': round(max(softs) - min(calls), 2), 'soft_minus_room_db': round(min(softs) - room, 2),
       'events': [{**e, 't_film': round(OFF + e['t'], 4)} for e in A['events']]}
json.dump(man, open(os.path.join(HERE, '..', 'audio.json'), 'w'), indent=1, ensure_ascii=False)
print('mix', out, 'calls', calls, 'soft', softs, 'room', room, 'soft-call', man['soft_minus_call_db'])
