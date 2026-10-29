"""SCION 11 · the sound, synthesized here (no recordings): a formant voice, dusk room tone,
paws on boards from the gait's foot plants, the door, paper.

Writes build/cache/film.wav (38 s: 3 s title + 32 s scene + 3 s card) and data/sound_levels.json
(measured RMS of every voice line and of the room tone, so the soft-voice rule is evidence).
"""
import json, os
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
PRE, SCENE, POST = 3.0, 32.0, 3.0
TOT = PRE + SCENE + POST
rng = np.random.default_rng(11)
L = np.zeros(int(TOT * SR)); R = np.zeros(int(TOT * SR))
PERF = json.load(open(os.path.join(HERE, '..', 'data', 'performance.json')))['frames']


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def put(sig, t, pan=0.0, gain=1.0):
    i = int((t) * SR)
    n = min(len(sig), len(L) - i)
    if n <= 0:
        return
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + n] += sig[:n] * gain * l * 1.414
    R[i:i + n] += sig[:n] * gain * r * 1.414


def pan_of(sx):
    return float(np.clip((sx - 640) / 640, -1, 1)) * .8


def reson(x, f, bw):
    r = np.exp(-np.pi * bw / SR)
    th = 2 * np.pi * f / SR
    return r, th


def formant_filter(src, F, B, blk=240):
    """time-varying cascade of 2-pole resonators, coefficients updated every 5 ms (state carried)"""
    out = src.copy()
    n = len(src)
    for k in range(F.shape[1]):
        y = np.zeros(n)
        zi = np.zeros(2)
        for i in range(0, n, blk):
            j = min(n, i + blk)
            f, bw = F[i, k], B[i, k]
            r = np.exp(-np.pi * bw / SR)
            a = [1, -2 * r * np.cos(2 * np.pi * f / SR), r * r]
            y[i:j], zi = signal.lfilter([1 - r], a, out[i:j], zi=zi)
        out = y / (np.max(np.abs(y)) + 1e-9)
    return out


V = {'a': (640, 1190, 2390), 'm': (260, 1000, 2300), 'h': (500, 1600, 2500), 'i': (400, 1900, 2550),
     'er': (480, 1350, 1750), 'o': (570, 840, 2410), 'l': (360, 1000, 2400), 'r': (420, 1250, 1700),
     'ai': (750, 1250, 2450), 'ai2': (420, 2000, 2600), 'n': (280, 1600, 2500), 's': (4500, 6000, 7500), 't': (1800, 3500, 5000),
     'k': (1500, 2200, 3000)}


def say(segs, f0, breath, loud):
    """segs: list of (phone, dur, voiced, noise). f0: (start, peak, end) Hz. returns mono signal"""
    n = int(sum(s[1] for s in segs) * SR)
    F = np.zeros((n, 3)); vo = np.zeros(n); no = np.zeros(n)
    i = 0
    for ph, d, v, z in segs:
        m = int(d * SR)
        F[i:i + m] = V[ph]
        vo[i:i + m] = v; no[i:i + m] = z
        i += m
    F = F[:n]
    # glide formants between phones
    for k in range(3):
        F[:, k] = np.convolve(F[:, k], np.ones(1200) / 1200, mode='same')
    vo = np.convolve(vo, np.ones(480) / 480, mode='same'); no = np.convolve(no, np.ones(240) / 240, mode='same')
    t = np.arange(n) / SR
    u = t / t[-1]
    f = np.interp(u, [0, .45, 1], f0) * (1 + .01 * np.sin(2 * np.pi * 5.3 * t))
    ph = np.cumsum(f / SR)
    glott = (ph % 1.0)
    glott = (glott < .6) * np.sin(np.pi * glott / .6) ** 2  # rounded pulse
    glott = np.diff(glott, prepend=0) * 40
    src = glott * vo * (1 - breath) + rng.normal(0, 1, n) * (vo * breath * .6 + no)
    B = np.array([80, 110, 160])[None, :] * np.ones((n, 1)) * (1 + breath)
    y = formant_filter(src, F, B)
    env = np.minimum(1, np.minimum(t / .02, (t[-1] - t) / .06))
    y = y * env
    y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9)
    return y * loud


COME_HERE = [('k', .05, 0, .8), ('a', .15, 1, 0), ('m', .1, 1, 0), ('h', .07, 0, .5), ('i', .12, 1, 0), ('er', .26, 1, 0)]
ALL_RIGHT = [('i', .07, 1, 0), ('t', .03, 0, .6), ('s', .09, 0, .5), ('o', .17, 1, 0), ('l', .08, 1, 0), ('r', .06, 1, 0),
             ('ai', .12, 1, 0), ('ai2', .1, 1, 0), ('t', .04, 0, .4)]
COME_IN = [('k', .05, 0, .6), ('a', .13, 1, 0), ('m', .08, 1, 0), ('i', .14, 1, 0), ('n', .2, 1, 0)]

CALL, SOFT = 0.20, 0.045
lines = [(1.02, COME_HERE, (170, 235, 150), .08, CALL, 'call: come here'),
         (3.42, COME_HERE, (180, 250, 160), .08, CALL, 'call: come here (again, reaching)'),
         (7.46, ALL_RIGHT, (150, 165, 120), .5, SOFT, "soft: it's all right"),
         (10.45, ALL_RIGHT, (145, 160, 118), .5, SOFT, "soft: it's all right"),
         (26.42, COME_IN, (150, 160, 125), .5, SOFT, 'soft: come in')]
levels = []
for t0, segs, f0, br, loud, label in lines:
    y = say(segs, f0, br, loud)
    pcx = PERF[int(t0 * 24)]['person']['cx']
    put(y, PRE + t0, pan_of(pcx))
    levels.append(dict(t=t0, line=label, rms_dbfs=round(db(y), 2)))

# room tone: wind (brown noise, low-passed) and crickets
n = len(L)
wind = np.cumsum(rng.normal(0, 1, n))
bh, ah = signal.butter(1, 20 / (SR / 2), 'high'); wind = signal.lfilter(bh, ah, wind)
b, a = signal.butter(2, 400 / (SR / 2)); wind = signal.lfilter(b, a, wind)
wind = wind / np.sqrt(np.mean(wind ** 2)) * 10 ** (-50 / 20)
tt = np.arange(n) / SR
crick = np.zeros(n)
for c, (fc, rate, ph) in enumerate([(4300, 2.1, 0), (4650, 1.7, .3), (3950, 2.6, .7)]):
    gate = (np.sin(2 * np.pi * rate * tt + ph * 6) > .55).astype(float)
    pulses = (np.sin(2 * np.pi * 28 * tt) > 0).astype(float)
    crick += np.sin(2 * np.pi * fc * tt) * gate * pulses * (0.6 + .4 * np.sin(2 * np.pi * .05 * tt + c))
crick = np.convolve(crick, np.ones(48) / 48, mode='same')
crick = crick / np.sqrt(np.mean(crick ** 2)) * 10 ** (-52 / 20)
fade = np.clip(np.minimum(tt / 2.0, (TOT - tt) / 2.0), 0, 1)
room = (wind + crick) * fade
L += room * .9 + np.roll(crick, 300) * fade * .25; R += room * .9


def tap(gain, f=1400):
    m = int(.035 * SR)
    x = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (SR * .006))
    b, a = signal.butter(2, [f * .6 / (SR / 2), f * 1.6 / (SR / 2)], 'band')
    return signal.lfilter(b, a, x) * gain


# paws: a tap whenever a foot comes down (its lift returns to 0 while the dog walks)
prev = {}
for fr in PERF:
    feet = fr['dog']['pose']['feet']
    for k, (dx, lift) in feet.items():
        if prev.get(k, 0) > .3 and lift <= .3:
            put(tap(.05 if fr['t'] < 3 else .035, 1200 + 300 * (k[0] == 'f')), PRE + fr['t'], pan_of(fr['dog']['sx']))
        prev[k] = lift


def rustle(dur, gain):
    m = int(dur * SR)
    x = rng.normal(0, 1, m) * (rng.random(m) < .08)
    b, a = signal.butter(2, [1500 / (SR / 2), 7000 / (SR / 2)], 'band')
    x = signal.lfilter(b, a, x)
    return x * np.hanning(m) * gain


# paper: the cut-outs are turned over / laid down on the table
for t0, d, g in [(3.42, .45, .05), (4.5, .5, .035), (7.46, .5, .05), (23.8, .6, .035), (28.2, .5, .025)]:
    put(rustle(d, g), PRE + t0, pan_of(PERF[int(t0 * 24)]['dog']['sx']))
# door: latch, then a slow creak as it swings in; then the room's warmth (a low hum) comes up
put(tap(.12, 2600), PRE + 6.15, -.45)
m = int(.95 * SR); tc = np.arange(m) / SR
cr = signal.sawtooth(2 * np.pi * np.cumsum(90 + 40 * np.sin(2 * np.pi * 1.3 * tc) + 25 * rng.normal(0, .3, m)) / SR)
b, a = signal.butter(2, [600 / (SR / 2), 2400 / (SR / 2)], 'band')
cr = signal.lfilter(b, a, cr) * np.hanning(m) * .045
put(cr, PRE + 6.2, -.45)
hum_t = np.arange(int((SCENE - 6.3) * SR)) / SR
hum = (np.sin(2 * np.pi * 110 * hum_t) + .5 * np.sin(2 * np.pi * 165 * hum_t)) * np.clip(hum_t / 1.5, 0, 1) * .006
put(hum, PRE + 6.3, -.4)
# a breath out when it settles its chin (28.3)
m = int(.8 * SR)
br = rng.normal(0, 1, m); b, a = signal.butter(2, [300 / (SR / 2), 1800 / (SR / 2)], 'band')
br = signal.lfilter(b, a, br) * np.hanning(m) ** 2 * .03
put(br, PRE + 28.3, -.2)

mx = max(np.abs(L).max(), np.abs(R).max())
if mx > .95:
    L *= .95 / mx; R *= .95 / mx
out = np.stack([L, R], 1)
wavfile.write(os.path.join(HERE, 'cache', 'film.wav'), SR, (out * 32767).astype(np.int16))
calls = [l['rms_dbfs'] for l in levels if l['line'].startswith('call')]
softs = [l['rms_dbfs'] for l in levels if l['line'].startswith('soft')]
seg = room[int((PRE + 12) * SR):int((PRE + 14) * SR)]
rep = dict(lines=levels, room_tone_rms_dbfs=round(db(seg), 2),
           soft_minus_call_db=round(max(softs) - min(calls), 2),
           soft_above_room_db=round(min(softs) - db(seg), 2),
           note='levels measured on the synthesized signals before the final mix normalisation (applied equally to all)')
json.dump(rep, open(os.path.join(HERE, '..', 'data', 'sound_levels.json'), 'w'), indent=1)
print(json.dumps(rep))
