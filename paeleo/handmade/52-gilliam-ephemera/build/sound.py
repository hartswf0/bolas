"""The sound track, synthesized and placed from the exposure sheet (events are read from xsheet.json, the voice from
voice.py's takes). 38 s, 48 kHz stereo; the scene starts at 3.0 s. Writes cache/sound.wav and proof/sound_levels.json."""
import json, math, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xsheet import gait, LEGN, K, F

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache')
SR = 48000; DUR = 38.0; OFF = 3.0
N = int(SR * DUR)
rng = np.random.default_rng(52)
L = np.zeros(N, np.float32); Rr = np.zeros(N, np.float32)
XS = json.load(open(os.path.join(FOLDER, 'xsheet.json')))
VO = json.load(open(os.path.join(CACHE, 'voice_chart.json')))
stems = {}


def db(x): return 10 ** (x / 20)


def add(sig, t, gain_db=0, pan=0.0, stem=None):
    i0 = int((t + OFF) * SR)
    if i0 >= N: return
    s = sig[: N - i0] * db(gain_db)
    l = s * math.cos((pan + 1) * math.pi / 4); r = s * math.sin((pan + 1) * math.pi / 4)
    L[i0:i0 + len(s)] += l; Rr[i0:i0 + len(s)] += r
    if stem:
        st = stems.setdefault(stem, np.zeros(N, np.float32)); st[i0:i0 + len(s)] += s


def onepole(x, fc, hp=False):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); z = 0.0
    # vectorised enough for short sounds; long ones use fft_filter
    for i in range(len(x)):
        z = (1 - a) * x[i] + a * z; y[i] = z
    return x - y if hp else y


def fft_band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(np.float32)
    m = np.convolve(m, np.hanning(41) / np.hanning(41).sum(), 'same')
    return np.fft.irfft(X * m, len(x)).astype(np.float32)


def env(n, a, r):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[n - nr:] *= np.linspace(1, 0, nr)
    return e


# ------------------------------------------------------------------ room tone: dusk air and crickets, the whole film
air = fft_band(rng.normal(0, 1, N).astype(np.float32), 60, 700)
air *= .012 / (np.sqrt(np.mean(air ** 2)) + 1e-9)
fade = np.minimum(1, np.arange(N) / (SR * 1.5)) * np.minimum(1, (N - np.arange(N)) / (SR * 1.5))
L += air * fade; Rr += air * fade * .96
stems['room'] = air * fade
t = 0.4
while t < DUR - 4:
    n = int(.11 * SR); tt = np.arange(n) / SR
    chirp = np.sin(2 * np.pi * 4650 * tt) * (np.sin(2 * np.pi * 32 * tt) > .3) * env(n, .005, .02)
    add(chirp.astype(np.float32), t - OFF, -44 + rng.normal(0, 2), pan=rng.uniform(.3, .9), stem='room')
    t += rng.uniform(.55, 1.2)

# ------------------------------------------------------------------ the voice: two calls, three soft lines
for k, ln in enumerate(VO['lines']):
    a = np.load(os.path.join(CACHE, f'voice_{k}.npy')).astype(np.float32)
    g = -9 if ln['register'] == 'call' else -23
    add(a, ln['t'], g, pan=-.45, stem='call' if ln['register'] == 'call' else 'soft')


# ------------------------------------------------------------------ the dog: claws on boards, from the gait
def click(strength=1.0):
    n = int(.045 * SR)
    s = rng.normal(0, 1, n).astype(np.float32) * np.exp(-np.arange(n) / (SR * .004))
    s = fft_band(np.pad(s, (0, 2048)), 1800, 7000)[:n]
    body = np.sin(2 * np.pi * 180 * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * .012)) * .5
    return (s / (np.abs(s).max() + 1e-9) + body) * strength


ex = XS['exposures']
prev = None
for e in ex:
    lab = e['dog_label']
    if not lab.startswith(('approach', 'retreat', 'watch')): prev = None; continue
    x = F[e['f0']]['dog']['x']
    if lab.startswith('approach'): s = (4.0 - x) * K
    elif lab.startswith('retreat') or (lab == 'watch' and e['f0'] < 82): s = -(x - 3.0) * K
    else: prev = None; continue
    _, ph = gait(s)
    if prev:
        for k in LEGN:
            if prev[k][0] == 'swing' and ph[k][0] != 'swing':        # a foot is put down
                near = k in ('fore', 'hind')
                add(click(1.0 if near else .6), e['t'] + rng.uniform(0, .02), -27 if lab.startswith('retreat') else -30,
                    pan=.5 if e['dog']['X'] > 700 else -.05, stem='dog')
    prev = ph


def breath(dur, f0, f1, gain):
    n = int(dur * SR)
    s = fft_band(rng.normal(0, 1, n + 4096).astype(np.float32), 300, 2400)[:n]
    sweep = np.exp(np.linspace(math.log(f0), math.log(f1), n))
    s *= (.6 + .4 * np.sin(np.cumsum(2 * np.pi * sweep / SR)))
    return s / (np.abs(s).max() + 1e-9) * env(n, .15, .5) * gain


def whimper(dur=.45, f0=980, f1=720):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.linspace(f0, f1, n) * (1 + .02 * np.sin(2 * np.pi * 7 * tt))
    s = np.sin(np.cumsum(2 * np.pi * f / SR)) + .3 * np.sin(2 * np.cumsum(2 * np.pi * f / SR))
    return (s * env(n, .04, .2)).astype(np.float32)


add(whimper(), 3.55, -33, pan=.6, stem='dog')                    # as it turns its back
add(breath(1.1, 900, 400, 1), 5.0, -32, pan=.6, stem='dog')        # lies down, away
add(breath(1.0, 900, 380, 1), 24.25, -31, pan=-.1, stem='dog')     # lies down across the sill
add(breath(1.4, 700, 300, 1), 28.6, -32, pan=-.1, stem='dog')      # settles, chin on paws


# ------------------------------------------------------------------ the table: a card swapped is heard
def tap(gain=1.0):
    n = int(.06 * SR)
    s = rng.normal(0, 1, n).astype(np.float32) * np.exp(-np.arange(n) / (SR * .009))
    s = fft_band(np.pad(s, (0, 2048)), 900, 5000)[:n]
    return s / (np.abs(s).max() + 1e-9) * gain


for f0 in [82, 86, 194, 200, 634, 674]:
    add(tap(), f0 / 24, -36, pan=0, stem='table')

# ------------------------------------------------------------------ the door: a creak, then the lamp's warm chord
n = int(.75 * SR); tt = np.arange(n) / SR
f = 95 + 60 * np.sin(2 * np.pi * 1.3 * tt) + rng.normal(0, 6, n).cumsum() * .02
saw = ((np.cumsum(f / SR)) % 1.0) * 2 - 1
creak = fft_band(np.pad(saw.astype(np.float32), (0, 2048)), 400, 3200)[:n] * env(n, .05, .2) * (1 + .5 * (np.sin(2 * np.pi * 17 * tt) > 0))
add(creak / (np.abs(creak).max() + 1e-9), 6.2, -29, pan=-.5, stem='door')


def chord(dur, notes, attack, release):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for k, fr in enumerate(notes):
        for h, amp in [(1, 1), (2, .35), (3, .15), (4, .06)]:
            s += amp * np.sin(2 * np.pi * fr * h * tt + k) * (1 + .003 * np.sin(2 * np.pi * (.3 + .1 * k) * tt))
    s *= (1 + .08 * np.sin(2 * np.pi * 4.8 * tt))           # a reed organ's beat
    return s / (np.abs(s).max() + 1e-9) * env(n, attack, release)


add(chord(6.5, [196.0, 246.9, 293.7], 1.4, 3.0), 6.25, -33, pan=-.3, stem='music')          # G major, the lamp
add(chord(14.0, [174.6, 220.0, 261.6, 329.6], 2.0, 5.0), 23.9, -34, pan=-.2, stem='music')  # F maj7, lying across the sill

# ------------------------------------------------------------------ master
mix = np.stack([L, Rr], 1)
pk = np.abs(mix).max()
if pk > .95: mix *= .95 / pk
with wave.open(os.path.join(CACHE, 'sound.wav'), 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())


def rms_db(x, t0, t1):
    seg = x[int((t0 + OFF) * SR): int((t1 + OFF) * SR)]
    return round(20 * math.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12), 2)


def active_rms(stem):
    x = stems[stem]; a = np.abs(x)
    win = int(.05 * SR); e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, 'same'))
    on = e > e.max() * .1
    return round(20 * math.log10(np.sqrt(np.mean(x[on] ** 2)) + 1e-12), 2)


lev = {'note': 'levels measured on the synthesized stems before the master (no master gain applied: peak ' + str(round(float(pk), 3)) + ')',
       'call_voice_active_rms_dbfs': active_rms('call'), 'soft_voice_active_rms_dbfs': active_rms('soft'),
       'room_tone_rms_dbfs': round(20 * math.log10(np.sqrt(np.mean(stems['room'][SR * 4:SR * 34] ** 2))), 2)}
lev['soft_minus_call_db'] = round(lev['soft_voice_active_rms_dbfs'] - lev['call_voice_active_rms_dbfs'], 2)
lev['soft_minus_room_db'] = round(lev['soft_voice_active_rms_dbfs'] - lev['room_tone_rms_dbfs'], 2)
json.dump(lev, open(os.path.join(FOLDER, 'proof', 'sound_levels.json'), 'w'), indent=1)
print(lev)
