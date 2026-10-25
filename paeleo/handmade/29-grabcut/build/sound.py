"""Sound, synthesized here (numpy), placed on the scene's events. 48 kHz mono -> build/cache/sound.wav (38 s film time).
Voice: a small formant synthesizer (glottal pulse train through vowel resonators, noise for consonants). The calls are
loud and pitched up; the soft voice is breathy, lower and at least 6 dB quieter (measured below, written to
build/cache/sound_levels.json). Dog: footfalls on the boards at the frames where the walk drawing changes (read from the
render's own measure.json), a sigh as it lies down, tail taps on the boards while it wags. Door: latch, creak, and the
room's warm hum that comes out with the light. Under it all, dusk: wind-noise floor and crickets."""
import os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
SR = 48000
T = 38.0
OFF = 3.0     # the scene starts after the 3 s title card
rng = np.random.default_rng(29)
N = int(SR * T)
out = np.zeros(N, np.float64)
voice_track = np.zeros(N); room_track = np.zeros(N)


def biquad_bp(x, f, q):
    w = 2 * math.pi * f / SR; al = math.sin(w) / (2 * q)
    b0, b1, b2 = al, 0, -al; a0, a1, a2 = 1 + al, -2 * math.cos(w), 1 - al
    return lfilter([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0], x)


def lfilter(b, a, x):
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    b0, b1, b2 = b; _, a1, a2 = a
    for n in range(len(x)):
        xn = x[n]; yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, xn; y2, y1 = y1, yn; y[n] = yn
    return y


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for n in range(len(x)):
        s = (1 - a) * x[n] + a * s; y[n] = s
    return y


def resonator_bank(src, formants):
    """formants: list of (f_array or f, bw, gain); time-varying centre allowed (piecewise-constant per 5 ms block)."""
    y = np.zeros_like(src)
    blk = int(SR * 0.005)
    for f, bw, g in formants:
        f = np.broadcast_to(np.asarray(f, float), src.shape)
        out = np.zeros_like(src); y1 = y2 = 0.0
        for s in range(0, len(src), blk):
            fc = float(f[s]); r = math.exp(-math.pi * bw / SR); th = 2 * math.pi * fc / SR
            a1, a2 = -2 * r * math.cos(th), r * r; gn = (1 - r)
            seg = src[s:s + blk]
            o = np.empty_like(seg)
            for n, xn in enumerate(seg):
                yn = gn * xn - a1 * y1 - a2 * y2
                y2, y1 = y1, yn; o[n] = yn
            out[s:s + blk] = o
        y += out * g
    return y


VOWELS = {'a': (640, 1190, 2390), 'i': (400, 2000, 2550), 'e': (480, 1800, 2500), 'o': (450, 850, 2400),
          'u': (350, 900, 2300), 'ai': (700, 1220, 2600), 'm': (280, 1300, 2300), 'n': (280, 1700, 2500)}


def syllables(spec, f0, loud, breath):
    """spec: list of (phone, dur, f0_mult). phones: vowels/nasals voiced; 'k','t','s','h' noise."""
    parts = []
    for ph, dur, fm in spec:
        n = int(dur * SR); t = np.arange(n) / SR
        if ph in ('k', 't'):
            x = rng.normal(0, 1, n) * np.exp(-t / 0.012); x = biquad_bp(x, 2800 if ph == 'k' else 4200, 1.5) * 0.9
            parts.append(('n', x, None)); continue
        if ph in ('s', 'h'):
            x = rng.normal(0, 1, n) * np.sin(np.pi * t / dur) ** 0.7
            x = biquad_bp(x, 6000 if ph == 's' else 1600, 1.2 if ph == 's' else 0.7) * (0.5 if ph == 's' else 0.35)
            parts.append(('n', x, None)); continue
        parts.append(('v', n, (ph, fm)))
    sig = []
    phase = 0.0
    for kind, a, b in parts:
        if kind == 'n':
            sig.append(a); continue
        n = a; ph, fm = b
        t = np.arange(n) / SR
        fm_arr = np.interp(t, [0, t[-1]], fm) if isinstance(fm, tuple) else np.full(n, fm)
        f = f0 * fm_arr * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * t))
        ph_acc = phase + np.cumsum(f) / SR
        phase = ph_acc[-1] % 1.0
        saw = (ph_acc % 1.0)
        glott = (1 - saw) ** 3 - 0.25                    # a rough glottal pulse shape
        src = glott * (1 - breath) + rng.normal(0, 1, n) * breath * 0.6
        F = VOWELS[ph]
        y = resonator_bank(src, [(F[0], 80, 1.0), (F[1], 110, 0.6), (F[2], 160, 0.3)])
        env = np.minimum(1, np.minimum(t / 0.03, (t[-1] - t) / 0.05 + 0.02))
        sig.append(y * env)
    x = np.concatenate(sig)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    return x * loud


def place(track, x, t0):
    i0 = int((t0 + OFF) * SR)
    i1 = min(len(track), i0 + len(x))
    track[i0:i1] += x[: i1 - i0]


def db(x):
    return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


# ---- voice
CALL = 10 ** (-13 / 20); SOFT = 10 ** (-25 / 20)
come_here = [('k', .05, 1), ('a', .16, (1.05, 1.15)), ('m', .09, 1.1), ('h', .07, 1), ('i', .14, (1.25, 1.2)), ('e', .2, (1.2, 0.85))]
place(voice_track, syllables(come_here, 205, CALL, 0.05), 1.02)
come_here2 = [('k', .05, 1), ('a', .14, (1.1, 1.25)), ('m', .08, 1.2), ('h', .06, 1), ('i', .16, (1.4, 1.3)), ('e', .22, (1.3, 0.9))]
place(voice_track, syllables(come_here2, 215, CALL * 1.12, 0.05), 3.42)
place(voice_track, syllables(come_here2, 215, CALL * 1.05, 0.05), 4.0)
its_all_right = [('i', .07, 1.0), ('t', .03, 1), ('s', .08, 1), ('o', .18, (1.0, .95)), ('ai', .2, (1.0, .9)), ('t', .04, 1)]
place(voice_track, syllables(its_all_right, 170, SOFT, 0.45), 7.45)
place(voice_track, syllables(its_all_right, 165, SOFT * 0.95, 0.5), 10.45)
come_in = [('k', .04, 1), ('a', .14, (1.0, .98)), ('m', .08, .96), ('i', .12, (1.0, .92)), ('n', .14, .9)]
place(voice_track, syllables(come_in, 170, SOFT, 0.45), 26.42)

# ---- room tone: dusk (soft wind noise floor + crickets)
noise = rng.normal(0, 1, N)
wind = onepole_lp(noise, 300) * 0.9
room_track += wind / (np.sqrt(np.mean(wind ** 2)) + 1e-9) * 10 ** (-46 / 20)
tt = np.arange(N) / SR
for k, (fc, rate, ph) in enumerate(((4300, 2.7, 0.0), (4700, 3.1, 0.4), (3900, 2.2, 0.7))):
    gate = (np.sin(2 * np.pi * rate * tt + ph * 6) > 0.6).astype(float)
    trill = (np.sin(2 * np.pi * 38 * tt) > 0).astype(float)
    c = np.sin(2 * np.pi * fc * tt) * gate * trill
    c = onepole_lp(c, 6000)
    room_track += c * 10 ** ((-50 - 3 * k) / 20) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * tt + k))

# ---- door: latch, creak, then the room's warm hum with the light
lt = np.arange(int(.05 * SR)) / SR
latch = rng.normal(0, 1, len(lt)) * np.exp(-lt / .006)
place(out, biquad_bp(latch, 2200, 2) * 0.35, 6.2)
place(out, biquad_bp(rng.normal(0, 1, len(lt)) * np.exp(-lt / .004), 3000, 3) * 0.25, 6.26)
cn = int(0.85 * SR); ct = np.arange(cn) / SR
cf = 520 + 260 * np.sin(np.pi * ct / 0.85) + 40 * np.sin(2 * np.pi * 7 * ct)
creak = np.sin(2 * np.pi * np.cumsum(cf) / SR) * (np.sin(2 * np.pi * 31 * ct) > -0.2)
creak = biquad_bp(creak, 900, 1.4) * np.sin(np.pi * ct / 0.85) ** 1.5
place(out, creak * 0.05, 6.28)
open_env = np.clip((tt - (6.2 + OFF)) / 0.9, 0, 1) * (tt < 35 + 0)
hum = (np.sin(2 * np.pi * 110 * tt) * 0.5 + np.sin(2 * np.pi * 220 * tt) * 0.2 + onepole_lp(rng.normal(0, 1, N), 500) * 4)
room_track += hum * open_env * 10 ** (-47 / 20)

# ---- the person sits: cloth, then a soft settle
rn = int(0.7 * SR); rt = np.arange(rn) / SR
rust = biquad_bp(rng.normal(0, 1, rn), 2500, 0.8) * np.sin(np.pi * rt / 0.7) * 0.03
place(out, rust, 5.45)
tn = int(.12 * SR); tk = np.arange(tn) / SR
thump = np.sin(2 * np.pi * 70 * tk) * np.exp(-tk / .03)
place(out, thump * 0.08, 6.15)

# ---- the dog: footfalls where its drawing changes (from the render's measurement)
import glob
meas = {}
for p in sorted(glob.glob(os.path.join(C, 'measure*.json'))):
    meas.update(json.load(open(p)))
prev = None
pad_n = int(.035 * SR); pt = np.arange(pad_n) / SR
foot_times = []
for k in sorted(meas, key=int):
    m = meas[k]; d = m.get('drawing')
    if d and d[0] == 'frame' and prev and prev[0] == 'frame' and d[1] != prev[1]:
        foot_times.append(m['t'])
    prev = d
for ft in foot_times:
    if (1.0 <= ft < 2.4) or (14.7 <= ft < 23.8):
        pad = biquad_bp(rng.normal(0, 1, pad_n), 1500 + rng.normal(0, 200), 1.5) * np.exp(-pt / .008)
        tick = biquad_bp(rng.normal(0, 1, pad_n), 4200, 4) * np.exp(-pt / .003)
        g = 0.07 if ft < 3 else 0.05
        place(out, (pad + tick * 0.6) * g, ft + rng.normal(0, .004))
# the turns: a scuffle of claws on boards
for t0, dur in ((3.45, .4), (8.05, .4)):
    sn = int(dur * SR); st = np.arange(sn) / SR
    sc = biquad_bp(rng.normal(0, 1, sn), 3500, 2) * (np.sin(2 * np.pi * 14 * st) > .3) * np.sin(np.pi * st / dur) * .025
    place(out, sc, t0)
# lying down: a body settling and a long exhale; and the final settle
for t0, g in ((4.75, 1.0), (24.15, 1.0), (28.3, 0.8)):
    en = int(1.1 * SR); et = np.arange(en) / SR
    sigh = onepole_lp(rng.normal(0, 1, en), 900) * np.exp(-et / .45) * np.minimum(1, et / .08)
    place(out, sigh / (np.abs(sigh).max() + 1e-9) * 0.05 * g, t0 + 0.15)
    place(out, thump * 0.06 * g, t0)
# tail taps on the boards while it wags (score wag, 26.5-28)
for k in range(9):
    place(out, thump * 0.035 + biquad_bp(rng.normal(0, 1, tn), 800, 1) * np.exp(-tk / .01) * .02, 26.55 + k * 0.205)

mix = out + voice_track + room_track
peak = np.abs(mix).max()
if peak > 0.95:
    mix *= 0.95 / peak; voice_track *= 0.95 / peak; room_track *= 0.95 / peak
# ---- measure: calls vs soft voice vs room tone (RMS over the voiced spans, dBFS)
def span(track, a, b):
    return track[int((a + OFF) * SR): int((b + OFF) * SR)]
def voiced_db(a, b):
    x = span(voice_track, a, b); x = x[np.abs(x) > 1e-4]; return db(x)
levels = {'call_1_dBFS': round(voiced_db(1.0, 1.9), 2), 'call_2_dBFS': round(voiced_db(3.4, 4.7), 2),
          'soft_1_dBFS': round(voiced_db(7.4, 8.4), 2), 'soft_2_dBFS': round(voiced_db(10.4, 11.4), 2),
          'soft_come_in_dBFS': round(voiced_db(26.4, 27.2), 2), 'room_tone_dBFS': round(db(span(room_track, 7.4, 8.4)), 2),
          'room_tone_early_dBFS': round(db(span(room_track, 0, 0.9)), 2), 'footfalls': len(foot_times)}
levels['soft_minus_call_dB'] = round(max(levels['soft_1_dBFS'], levels['soft_2_dBFS'], levels['soft_come_in_dBFS']) -
                                     min(levels['call_1_dBFS'], levels['call_2_dBFS']), 2)
levels['soft_minus_room_dB'] = round(min(levels['soft_1_dBFS'], levels['soft_2_dBFS'], levels['soft_come_in_dBFS']) - levels['room_tone_dBFS'], 2)
json.dump(levels, open(os.path.join(C, 'sound_levels.json'), 'w'), indent=1)
print(levels)
import wave
w = wave.open(os.path.join(C, 'sound.wav'), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
