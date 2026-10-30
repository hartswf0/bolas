"""SCION 19 sound, all synthesized here with numpy (no recordings, no TTS): dusk room tone and crickets, the person's voice
from a small source-filter formant synthesizer (pulse train through three resonators per phoneme; noise for consonants),
the dog's paws on the boards placed at the gait solver's touch-downs (read from the render's measures), the body settling,
the door's creak and the room's warm hum once it is open, the dog's sigh when it settles.
Writes cache/scene.wav (32 s, 48 kHz stereo) and ../proof/levels.json (measured RMS of calls, soft voice, room tone)."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
SR = 48000; DUR = 32.0; N = int(SR * DUR)
rng = np.random.default_rng(19)


def iir2(x, b0, a1, a2):
    """y[n] = b0 x[n] - a1 y[n-1] - a2 y[n-2], python loop on short signals only"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    for n in range(len(x)):
        v = b0 * x[n] - a1 * y1 - a2 * y2; y[n] = v; y2 = y1; y1 = v
    return y

def reson(x, f, bw):
    r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
    return iir2(x, 1 - r, -2 * r * np.cos(th), r * r)

def onepole_lp(x, f):
    a = np.exp(-2 * np.pi * f / SR); y = np.zeros_like(x); s = 0.0
    for n in range(len(x)): s = (1 - a) * x[n] + a * s; y[n] = s
    return y

def fft_band(x, lo, hi):
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); X[(fr < lo) | (fr > hi)] = 0; return np.fft.irfft(X, len(x))

def env(n, a=.01, r=.05):
    e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

def rms_db(x): return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))

# formants (F1, F2, F3) for the few sounds we need
FMT = {'uh': (640, 1190, 2390), 'm': (300, 1100, 2300), 'ee': (290, 2250, 2950), 'er': (480, 1350, 1700), 'ih': (400, 1950, 2600),
       'aw': (580, 880, 2450), 'l': (380, 1050, 2500), 'ai': (700, 1220, 2500), 'n': (300, 1500, 2550), 'oh': (480, 900, 2450)}

def phrase(segs, f0a, f0b, soft=False):
    """segs: list of (sound, seconds); voiced sounds use FMT, 'k','t','h','s' are noise consonants"""
    parts = []; T = sum(d for _, d in segs); t0 = 0.0; ph = 0.0
    for k, d in segs:
        n = int(d * SR); tt = t0 + np.arange(n) / SR
        if k in ('k', 't', 'h', 's'):
            z = rng.normal(0, 1, n)
            if k == 'k': x = fft_band(z, 1500, 3800) * np.exp(-np.arange(n) / (.015 * SR)) * 1.6
            elif k == 't': x = fft_band(z, 3000, 7000) * np.exp(-np.arange(n) / (.012 * SR)) * 1.3
            elif k == 's': x = fft_band(z, 4000, 9000) * env(n, .02, .03) * .8
            else: x = fft_band(z, 400, 2600) * env(n, .02, .03) * .6
            parts.append(x * (.6 if soft else 1.)); t0 += d; continue
        f0 = f0a + (f0b - f0a) * (tt / T) + 3 * np.sin(2 * np.pi * 5.2 * tt)
        phase = ph + np.cumsum(2 * np.pi * f0 / SR); ph = phase[-1]
        src = 1 - 2 * ((phase / (2 * np.pi)) % 1.0)          # falling saw ~ glottal pulse
        src = onepole_lp(src, 1600 if soft else 3200)
        if soft: src = .5 * src + .5 * fft_band(rng.normal(0, 1, n), 300, 4500) * .35
        F = FMT[k]
        y = reson(src, F[0], 80) + .55 * reson(src, F[1], 110) + .3 * reson(src, F[2], 160)
        if k in ('m', 'n'): y *= .45
        parts.append(y * env(n, .015, .02)); t0 += d
    x = np.concatenate(parts)
    return x / (np.max(np.abs(x)) + 1e-9)

def place(buf, x, t, gain):
    i = int(t * SR); j = min(N, i + len(x)); buf[i:j] += x[:j - i] * gain

out = np.zeros(N)
# ---- room tone: low air + crickets (dusk)
air = onepole_lp(rng.normal(0, 1, N), 300) * 0.02
out += air
crick = np.zeros(N)
for k in range(110):
    t = rng.uniform(0, DUR - 0.5); n = int(0.18 * SR); tt = np.arange(n) / SR
    chirp = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 34 * tt) > 0.2) * np.hanning(n)
    place(crick, chirp, t, 0.010 * rng.uniform(.5, 1))
out += crick
tone = out.copy()

# ---- the person's voice
calls, softs = [], []
come_here = [('k', .06), ('uh', .17), ('m', .10), ('h', .07), ('ee', .20), ('er', .22)]
x = phrase(come_here, 205, 165); place(out, x, 1.02, 0.36); calls.append((1.02, len(x)))
x = phrase(come_here, 230, 175); place(out, x, 3.42, 0.42); calls.append((3.42, len(x)))
alright = [('ih', .10), ('t', .05), ('s', .07), ('aw', .22), ('l', .08), ('r' if False else 'er', .08), ('ai', .28), ('t', .05)]
for t0 in (7.42, 10.42):
    x = phrase(alright, 150, 120, soft=True); place(out, x, t0, 0.11); softs.append((t0, len(x)))
come_in = [('k', .05), ('uh', .16), ('m', .08), ('ih', .20), ('n', .22)]
x = phrase(come_in, 145, 118, soft=True); place(out, x, 26.42, 0.11); softs.append((26.42, len(x)))

# ---- paws on the boards: touch-downs from the render's measured foot heights
meas = json.load(open(os.path.join(CACHE, 'frames', 'measures.json')))
taps = 0
for k in range(4):
    for a, b in zip(meas[:-1], meas[1:]):
        if a['rig']['legs'][k]['F'][1] > 0.004 and b['rig']['legs'][k]['F'][1] <= 0.004:
            n = int(.03 * SR); z = fft_band(rng.normal(0, 1, n), 900, 5000) * np.exp(-np.arange(n) / (.004 * SR))
            th = np.sin(2 * np.pi * 140 * np.arange(n) / SR) * np.exp(-np.arange(n) / (.012 * SR)) * .6
            place(out, (z + th), b['i'] / 24, 0.035 * rng.uniform(.7, 1)); taps += 1

# ---- body settling (lying down in refusal, and across the sill), and the sigh when it settles
def thud(t, g):
    n = int(.35 * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (70 + 40 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 12) + fft_band(rng.normal(0, 1, n), 100, 900) * np.exp(-tt * 25) * .4
    place(out, y, t, g)
thud(4.85, 0.10); thud(24.35, 0.10)
n = int(1.1 * SR); tt = np.arange(n) / SR
sigh = fft_band(rng.normal(0, 1, n), 250, 1800) * np.sin(np.pi * tt / 1.1) ** 2
place(out, sigh, 28.3, 0.045)
# ---- the door: a creak as it opens, then the room's warm hum out through the opening
n = int(.8 * SR); tt = np.arange(n) / SR
f = 260 + 180 * tt + 25 * np.sin(2 * np.pi * 7 * tt); ph = np.cumsum(2 * np.pi * f / SR)
creak = (np.sign(np.sin(ph)) * (rng.uniform(0, 1, n) > .35)) * np.hanning(n)
creak = fft_band(creak, 300, 3000)
place(out, creak, 6.2, 0.05)
hum = (np.sin(2 * np.pi * 110 * np.arange(N) / SR) + .5 * np.sin(2 * np.pi * 165 * np.arange(N) / SR)) * 0.006
hum *= np.clip((np.arange(N) / SR - 6.3) / 1.2, 0, 1)
out += hum

# ---- levels (measured on the voice alone at its placed gain, and the room tone)
def seg_rms(lst, gain_list):
    return [rms_db(phrase_buf[int(t * SR):int(t * SR) + n]) for (t, n) in lst]
phrase_buf = out - tone - hum
lv = {'calls_db': [round(v, 2) for v in seg_rms(calls, None)], 'soft_db': [round(v, 2) for v in seg_rms(softs, None)], 'room_tone_db': round(rms_db(tone), 2)}
lv['soft_under_calls_db'] = round(min(lv['calls_db']) - max(lv['soft_db']), 2)
lv['soft_over_room_db'] = round(min(lv['soft_db']) - lv['room_tone_db'], 2)
lv['paw_taps'] = taps
lv['note'] = 'RMS over each phrase (voice only, with its placed gain); paws and other effects excluded from the voice measure'
peak = np.max(np.abs(out)); out = out / peak * 0.89
json.dump(lv, open(os.path.join(HERE, '..', 'proof', 'levels.json'), 'w'), indent=1)
pcm = (np.stack([out, out], 1) * 32767).astype('<i2')
with wave.open(os.path.join(CACHE, 'scene.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(lv)
