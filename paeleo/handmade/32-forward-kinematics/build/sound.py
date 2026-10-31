"""SCION 32 · the sound, synthesized here (no recordings): build/cache/sound.wav (38 s, 48 kHz stereo) + cache/sound_levels.json
- voice: a source-filter formant synthesizer (glottal pulse train + aspiration through three resonators per phoneme).
  Calls are loud and clipped; the soft voice is breathy and low, measured >= 6 dB under the calls; each voice starts at or before
  the dog's reaction (calls 0.95 s and 3.34 s, soft 7.30 s, come in 26.30 s).
- wood: every paw tap is a short carved-wood knock placed on the rig's own touchdown events (cache/footfalls.json, from FK);
  lying down is a clatter of blocks and a felt rustle; the pins tick in the turns. The door creaks open at 6.2 s.
- the dusk: crickets and a little wind; inside, once the door is open, a warm low room hum."""
import json, math, os, random, struct, wave
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(H, 'cache')
SR = 48000; TOTAL = 38.0; OFF = 3.0  # scene starts after the 3 s title
rng = np.random.default_rng(32)
N = int(SR * TOTAL); L = np.zeros(N); R = np.zeros(N)

def reson(x, f, bw):  # time-varying two-pole resonator (f, bw arrays or scalars)
    n = len(x); f = np.broadcast_to(f, (n,)); bw = np.broadcast_to(bw, (n,))
    r = np.exp(-math.pi * bw / SR); c2 = 2 * r * np.cos(2 * math.pi * f / SR); c3 = -r * r; g = 1 - r
    y = np.zeros(n); y1 = y2 = 0.0
    for k in range(n):
        v = g[k] * x[k] + c2[k] * y1 + c3[k] * y2; y[k] = v; y2 = y1; y1 = v
    return y

def onepole(x, a):
    y = np.zeros_like(x); s = 0.0
    for k in range(len(x)): s += a * (x[k] - s); y[k] = s
    return y

# phoneme table: (F1, F2, F3, voiced amplitude, noise amplitude, noise centre Hz)
PH = {'k': (300, 1800, 2500, 0.0, 0.9, 2500), 'ʌ': (640, 1190, 2390, 1, 0.03, 0), 'm': (260, 1000, 2400, 0.35, 0, 0), 'h': (500, 1500, 2500, 0.05, 0.5, 1500),
      'ɪ': (400, 1950, 2600, 1, 0.03, 0), 'ə': (520, 1450, 1750, 0.95, 0.03, 0), 'r': (430, 1250, 1600, 0.8, 0, 0), 't': (300, 1800, 2700, 0, 0.8, 3800),
      's': (300, 1800, 2700, 0, 0.75, 6000), 'ɔ': (570, 860, 2420, 1, 0.03, 0), 'l': (360, 1250, 2700, 0.7, 0, 0), 'a': (720, 1240, 2500, 1, 0.03, 0),
      'i': (300, 2250, 2950, 1, 0.03, 0), 'n': (260, 1500, 2500, 0.35, 0, 0), '_': (500, 1500, 2500, 0, 0, 0)}

def say(phones, f0, start, gain, breath=0.06, pan=0.0):
    """phones: [(symbol, dur)], f0: [(t_rel, Hz)] contour; writes into L/R at start (film seconds)"""
    dur = sum(d for _, d in phones); n = int(dur * SR)
    t = np.arange(n) / SR
    tracks = np.zeros((n, 6)); pos = 0.0
    keys_t, keys_v = [], []
    for s, d in phones:
        keys_t += [pos + 0.25 * d, pos + 0.75 * d]; keys_v += [PH[s], PH[s]]; pos += d
    kv = np.array(keys_v, dtype=float)
    for j in range(6): tracks[:, j] = np.interp(t, keys_t, kv[:, j])
    ft, fv = zip(*f0); F0 = np.interp(t, ft, fv) * (1 + 0.012 * np.sin(2 * math.pi * 5.2 * t))
    ph = np.cumsum(F0 / SR) % 1.0
    pulse = np.where(ph < 0.6, np.sin(math.pi * ph / 0.6) ** 2, 0.0); src = np.diff(pulse, prepend=0) * 18
    src = src * tracks[:, 3] + rng.normal(0, 1, n) * breath * tracks[:, 3]
    v = reson(src, tracks[:, 0], 90) + 0.6 * reson(src, tracks[:, 1], 120) + 0.3 * reson(src, tracks[:, 2], 160)
    nz = rng.normal(0, 1, n) * tracks[:, 4]
    nzf = reson(nz, np.maximum(tracks[:, 5], 200), 1400) * 0.5
    y = v + nzf
    env = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.05)).clip(0, 1)
    y = y * env; y = y / (np.max(np.abs(y)) + 1e-9) * gain
    i0 = int(start * SR); i1 = min(N, i0 + n)
    L[i0:i1] += y[:i1 - i0] * (1 - pan) ; R[i0:i1] += y[:i1 - i0] * (1 + pan)
    return (start, start + dur)

def knock(t0, f=1100, amp=0.06, decay=0.035, pan=0.0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    y = (np.sin(2 * math.pi * f * t) + 0.5 * np.sin(2 * math.pi * f * 2.76 * t) * np.exp(-t / 0.01)) * np.exp(-t / decay)
    y += rng.normal(0, 1, n) * np.exp(-t / 0.004) * 0.6
    i0 = int(t0 * SR); i1 = min(N, i0 + n)
    L[i0:i1] += amp * y[:i1 - i0] * (1 - pan); R[i0:i1] += amp * y[:i1 - i0] * (1 + pan)

def noise_burst(t0, dur, amp, a=0.05, pan=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = onepole(rng.normal(0, 1, n), a) * np.sin(math.pi * t / dur) ** 2
    i0 = int(t0 * SR); i1 = min(N, i0 + n)
    L[i0:i1] += amp * y[:i1 - i0] * (1 - pan); R[i0:i1] += amp * y[:i1 - i0] * (1 + pan)

# ---- the dusk: crickets, wind
t = np.arange(N) / SR
wind = onepole(rng.normal(0, 1, N), 0.004) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.07 * t + 1))
L += wind * 0.05; R += wind * 0.045
for (fc, rate, ph0, pan) in [(4300, 2.6, 0.0, -0.5), (4700, 3.1, 0.4, 0.4), (3900, 2.2, 0.8, 0.1)]:
    chirp = (np.sin(2 * math.pi * fc * t) * (np.sin(2 * math.pi * 32 * t) > 0.2)) * ((np.sin(2 * math.pi * rate * t + ph0 * 6) > 0.55) * 1.0)
    env = 0.5 + 0.5 * np.sin(2 * math.pi * 0.05 * t + ph0 * 9)
    L += chirp * env * 0.0035 * (1 - pan); R += chirp * env * 0.0035 * (1 + pan)
# warm room hum once the door is open (scene 6.2 s ->)
hum = (np.sin(2 * math.pi * 110 * t) * 0.6 + np.sin(2 * math.pi * 220 * t) * 0.25) * np.clip((t - OFF - 6.2) / 1.0, 0, 1) * np.clip((TOTAL - 3 - t) / 1.0 + 1, 0, 1)
L += hum * 0.004; R += hum * 0.005

# ---- voices (person on the right of frame in the wide: pan slightly right)
segs = {'call': [], 'soft': []}
segs['call'].append(say([('k', 0.06), ('ʌ', 0.13), ('m', 0.09), ('h', 0.08), ('ɪ', 0.16), ('ə', 0.22)], [(0, 200), (0.2, 230), (0.4, 255), (0.75, 190)], OFF + 0.95, 0.55, pan=0.2))
segs['call'].append(say([('k', 0.06), ('ʌ', 0.12), ('m', 0.08), ('ɔ', 0.18), ('n', 0.1), ('_', 0.08), ('k', 0.06), ('ʌ', 0.12), ('m', 0.08), ('h', 0.08), ('ɪ', 0.18), ('ə', 0.26)],
                        [(0, 230), (0.3, 270), (0.55, 215), (0.75, 250), (1.0, 290), (1.3, 205)], OFF + 3.34, 0.62, pan=0.2))
soft_f0 = [(0, 165), (0.4, 175), (0.8, 150), (1.2, 140)]
segs['soft'].append(say([('ɪ', 0.08), ('t', 0.05), ('s', 0.1), ('ɔ', 0.22), ('l', 0.1), ('r', 0.08), ('a', 0.2), ('i', 0.14), ('t', 0.05)], soft_f0, OFF + 7.30, 0.13, breath=0.35, pan=0.1))
segs['soft'].append(say([('ɪ', 0.08), ('t', 0.05), ('s', 0.1), ('ɔ', 0.24), ('l', 0.1), ('r', 0.08), ('a', 0.22), ('i', 0.16), ('t', 0.05)], soft_f0, OFF + 10.40, 0.12, breath=0.35, pan=0.1))
segs['soft'].append(say([('k', 0.05), ('ʌ', 0.16), ('m', 0.1), ('ɪ', 0.18), ('n', 0.2)], [(0, 170), (0.3, 160), (0.7, 140)], OFF + 26.30, 0.13, breath=0.35, pan=-0.1))

# ---- wood: paw taps on the rig's footfalls; the lie-downs; the door; the person's steps
foot = json.load(open(os.path.join(C, 'footfalls.json')))
for s in foot:
    f = 950 if s['paw'].startswith('f') else 820
    knock(OFF + s['t'], f=f * (0.95 + 0.1 * random.Random(int(s['t'] * 100)).random()), amp=0.035)
for t0 in (4.45, 23.95):   # lying down: blocks settle, the felt rustles
    for k, dt in enumerate([0.0, 0.11, 0.19, 0.33]): knock(OFF + t0 + dt, f=700 - 60 * k, amp=0.05, decay=0.05)
    noise_burst(OFF + t0, 0.6, 0.05, a=0.08)
for t0 in (7.75, 8.0):     # getting up
    knock(OFF + t0, f=760, amp=0.04)
# the door: a creak from 6.2 to 7.0, then a soft stop
n = int(0.85 * SR); tt = np.arange(n) / SR
fr = 230 + 140 * np.sin(2 * math.pi * 0.9 * tt) + 40 * rng.normal(0, 1, n).cumsum() / np.sqrt(np.arange(1, n + 1))
cre = np.sign(np.sin(2 * math.pi * np.cumsum(fr) / SR)) * (rng.random(n) < 0.6)
cre = reson(cre.astype(float), 900, 600) * np.sin(math.pi * tt / 0.85) ** 1.5
i0 = int((OFF + 6.2) * SR); L[i0:i0 + n] += cre * 0.05; R[i0:i0 + n] += cre * 0.07
knock(OFF + 7.08, f=180, amp=0.08, decay=0.08)
for t0 in (4.7, 4.98, 5.27):  knock(OFF + t0, f=160, amp=0.09, decay=0.06, pan=0.2)   # the person's steps
knock(OFF + 5.95, f=120, amp=0.1, decay=0.1, pan=0.1)                                   # sits on the boards
for t0 in np.arange(3.5, 4.1, 0.09): knock(OFF + t0, f=2600, amp=0.006, decay=0.008)    # pins ticking in the turns
for t0 in np.arange(7.95, 8.75, 0.1): knock(OFF + t0, f=2600, amp=0.006, decay=0.008)

# fades at the card edges
fade = np.clip(t / 1.0, 0, 1) * np.clip((TOTAL - t) / 1.5, 0, 1)
L *= fade; R *= fade
peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
gain = 0.89 / peak; L *= gain; R *= gain
def rms_db(a, b):
    i0, i1 = int(a * SR), int(b * SR); x = (L[i0:i1] + R[i0:i1]) / 2; return 20 * math.log10(np.sqrt(np.mean(x * x)) + 1e-12)
call = [rms_db(a, b) for a, b in segs['call']]; soft = [rms_db(a, b) for a, b in segs['soft']]
tone = rms_db(OFF + 12.5, OFF + 14.0)
lv = {'call_rms_dbfs': [round(v, 1) for v in call], 'soft_rms_dbfs': [round(v, 1) for v in soft], 'room_tone_rms_dbfs': round(tone, 1),
      'soft_vs_call_db': round(min(call) - max(soft), 1), 'soft_over_room_db': round(min(soft) - tone, 1),
      'voice_onsets_scene_s': {'call': [round(a - OFF, 2) for a, _ in segs['call']], 'soft': [round(a - OFF, 2) for a, _ in segs['soft']]}}
json.dump(lv, open(os.path.join(C, 'sound_levels.json'), 'w'), indent=1)
with wave.open(os.path.join(C, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.stack([L, R], 1).clip(-1, 1).__mul__(32767).astype('<i2').tobytes())
print(json.dumps(lv))
