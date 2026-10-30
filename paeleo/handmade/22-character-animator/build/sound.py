"""SCION 22 · the sound, all synthesized here: dusk room tone (crickets, air), the dog's claws on the boards at the
footfalls the Walk behaviour reported, collar tag on the turns, lying-down thumps and a sigh, the person's steps and the
bench, the door's creak, the room's clock once the door is open, and the voice.  Stereo by world x.
Writes cache/scene_audio.wav (32 s) and cache/levels.json (measured RMS of calls, soft voice and room tone)."""
import json, os, wave
import numpy as np
from scipy.signal import butter, sosfilt
from common import CACHE, WALL_IN

FS = 44100
DUR = 32.0
n = int(FS * DUR)
rng = np.random.default_rng(9)
L = np.zeros(n); R = np.zeros(n)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=FS, output='sos'), x)


def lp(x, hi):
    return sosfilt(butter(2, hi, 'lowpass', fs=FS, output='sos'), x)


def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * FS)
    if i >= n:
        return
    sig = sig[: n - i] * gain
    a = (pan + 1) / 2
    L[i:i + len(sig)] += sig * np.cos(a * np.pi / 2)
    R[i:i + len(sig)] += sig * np.sin(a * np.pi / 2)


def pan_x(x):
    return float(np.clip((x - 1.6) / 3.2, -1, 1))


def env(N, a, d):
    e = np.ones(N)
    ka, kd = int(a * FS), int(d * FS)
    e[:ka] = np.linspace(0, 1, ka)
    e[-kd:] *= np.linspace(1, 0, kd)
    return e


# room tone: crickets (outside) + air
t = np.arange(n) / FS
air = lp(rng.standard_normal(n), 400) * 0.010
cr = np.zeros(n)
for f0, rate, ph in ((4400, 2.9, 0.0), (4700, 3.4, 1.3), (4100, 2.5, 2.1)):
    gate = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(float)
    trill = (np.sin(2 * np.pi * 28 * t) > 0).astype(float)
    cr += np.sin(2 * np.pi * f0 * t) * lp(gate * trill, 300) * 0.0035
room = air + cr
L += room * 0.9 + np.roll(cr, 3000) * 0.4
R += room * 0.9 + np.roll(cr, 7000) * 0.4

ev = json.load(open(os.path.join(CACHE, 'events.json')))
# claws and pads on the boards
for tt, leg, x in ev['feet']:
    N = int(0.05 * FS)
    click = bp(rng.standard_normal(N), 2500, 6000) * np.exp(-np.arange(N) / (0.004 * FS)) * 0.10
    pad = lp(rng.standard_normal(N), 300) * np.exp(-np.arange(N) / (0.012 * FS)) * 0.10
    place(click + pad, tt, pan_x(x), 0.9)


def jingle(tt, x):
    N = int(0.35 * FS)
    k = np.arange(N) / FS
    s = sum(np.sin(2 * np.pi * f * k + rng.uniform(0, 6)) * np.exp(-k / d) for f, d in ((3120, 0.08), (4730, 0.06), (5890, 0.04)))
    for dt in (0.0, 0.07, 0.15):
        place(s * 0.03, tt + dt, pan_x(x), 1.0)


jingle(3.62, 4.0); jingle(8.15, 4.0); jingle(14.8, 4.0); jingle(26.5, 0.6)


def thump(tt, x, g=1.0):
    N = int(0.3 * FS)
    k = np.arange(N) / FS
    s = lp(rng.standard_normal(N), 180) * np.exp(-k / 0.05) * 0.35 + np.sin(2 * np.pi * 70 * k) * np.exp(-k / 0.06) * 0.12
    place(s, tt, pan_x(x), g)


def sigh(tt, x, g=1.0):
    N = int(0.9 * FS)
    s = bp(rng.standard_normal(N), 300, 1600) * np.sin(np.linspace(0, np.pi, N)) ** 2 * 0.05
    place(s, tt, pan_x(x), g)


thump(4.75, 4.0, 0.8); sigh(5.6, 4.0, 0.8)
thump(24.25, 0.6); sigh(25.0, 0.6); sigh(28.7, 0.6, 1.1)
# person: two steps aside, the bench
for tt in (5.03, 5.30):
    thump(tt, -0.6, 0.6)
N = int(0.5 * FS)
place(bp(rng.standard_normal(N), 400, 1800) * np.exp(-np.arange(N) / (0.08 * FS)) * 0.06, 5.55, pan_x(-1.05))
thump(5.6, -1.05, 0.7)
# door creak: stick-slip friction (a jittered pulse train swept in pitch through a wooden body resonance)
a0, a1 = ev['door']
N = int((a1 - a0 + 0.15) * FS)
k = np.arange(N) / FS
f = 140 + 220 * np.sin(np.pi * k / k[-1]) + 40 * np.sin(2 * np.pi * 7 * k)
ph = np.cumsum(f / FS)
pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.6 + 0.4 * rng.random(N))
creak = bp(pulses, 300, 2400) * env(N, 0.04, 0.12) * 0.55
place(creak, a0, pan_x(0.2), 1.0)
# the room, once the door is open: a clock and a warm hum
for k2 in range(26):
    tt = 6.9 + k2 * 1.0
    N = int(0.03 * FS)
    tick = bp(rng.standard_normal(N), 1800, 5000) * np.exp(-np.arange(N) / (0.003 * FS)) * 0.035
    place(tick, tt, pan_x(-2.0), 1.0)
hum = lp(rng.standard_normal(n), 220) * 0.006
hum[: int(6.4 * FS)] = 0
fade = np.clip((t - 6.2) / 0.6, 0, 1)
L += hum * fade * 1.1; R += hum * fade * 0.6

# voice: the person is inside, left of centre
voice = np.load(os.path.join(CACHE, 'voice.npy')).astype(float)[:n]
place(voice, 0.0, -0.35, 1.0)

mix = np.stack([L, R], 1)
pk = np.abs(mix).max()
if pk > 0.97:
    mix *= 0.97 / pk
with wave.open(os.path.join(CACHE, 'scene_audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(FS)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

lines = json.load(open(os.path.join(CACHE, 'voice_lines.json')))
mono = mix.mean(1)
db = lambda a, b: round(float(20 * np.log10(np.sqrt(np.mean(mono[int(a * FS):int(b * FS)] ** 2)) + 1e-12)), 2)
lev = {'lines': [{'text': l['text'], 'start': l['start'], 'rms_dbfs_in_mix': db(l['start'], l['end'])} for l in lines],
       'room_tone_dbfs_12_14s': db(12.0, 14.0), 'room_tone_dbfs_30_32s': db(30.0, 31.9)}
calls = [x['rms_dbfs_in_mix'] for x in lev['lines'] if 'here' in x['text']]
softs = [x['rms_dbfs_in_mix'] for x in lev['lines'] if 'here' not in x['text']]
lev['soft_below_calls_db'] = round(min(calls) - max(softs), 2)
lev['soft_above_room_db'] = round(min(softs) - max(lev['room_tone_dbfs_12_14s'], lev['room_tone_dbfs_30_32s']), 2)
json.dump(lev, open(os.path.join(CACHE, 'levels.json'), 'w'), indent=1)
print(json.dumps(lev))
