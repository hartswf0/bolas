"""SCION 20 · 05: the soundtrack, synthesized from the track breakdown (scene/track.json) that the exposure sheet wrote.
Nothing is recorded or sampled. Voice: a glottal pulse train through formant resonators (vowel by syllable), with
noise for consonants and breath; the calls are loud and pushed, the soft lines breathy and at least 6 dB quieter.
Dusk: crickets and wind. Wood: the dog's pads on the porch boards at each footfall the walk drawings make, the
person's steps and the stool, the door's latch and creak, tail thumps on the boards. A small music cue enters with the
light. Writes build/cache/sound.wav (38 s, 48 kHz stereo) and build/cache/sound_levels.json (measured)."""
import json, os
import numpy as np
from scipy.signal import lfilter, butter

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR = json.load(open(os.path.join(D, 'scene/track.json')))
SR = 48000; TOTAL = 38.0; OFF = 3.0     # the scene starts after the 3 s title
n = int(SR * TOTAL)
L = np.zeros(n); Rr = np.zeros(n)
rng = np.random.default_rng(20)
def at(t): return int(round((t + OFF) * SR))
def put(sig, t, gain=1.0, pan=0.0):
    i = at(t); j = min(n, i + len(sig))
    if j <= i: return
    s = sig[:j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); Rr[i:j] += s * np.sqrt(0.5 * (1 + pan))
def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'low'); return lfilter(b, a, x)
def hp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'high'); return lfilter(b, a, x)
def env(N, a, r):
    e = np.ones(N); A = min(N // 2, max(1, int(a * SR))); Rl = min(N // 2, max(1, int(r * SR)))
    e[:A] = np.linspace(0, 1, A); e[-Rl:] *= np.linspace(1, 0, Rl); return e
def reson(x, f, bw):
    r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)
def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)

# ---------------- ambience: dusk (crickets, wind), later a room hum through the open door
t = np.arange(n) / SR
wind = lp(rng.standard_normal(n), 400) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3) ** 2) * 0.018
crick = np.zeros(n)
for k, (f0, rate, ph) in enumerate([(4300, 3.1, 0.0), (4700, 2.6, 1.3), (3900, 3.6, 2.1)]):
    chirp = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(float) * (np.sin(2 * np.pi * 34 * t) > 0).astype(float)
    crick += np.sin(2 * np.pi * f0 * t) * lp(chirp, 300) * 0.006 * (1 + 0.3 * np.sin(2 * np.pi * t / (9 + k)))
amb = wind + crick
L += amb * 0.9 + np.roll(crick, 2000) * 0.25; Rr += amb * 0.9 + np.roll(crick, -1500) * 0.35
room = lp(rng.standard_normal(n), 180) * 0.004
door_open = np.clip((t - OFF - 6.2) / 0.7, 0, 1)
L += room * door_open; Rr += room * door_open * 0.6

# ---------------- voice
VOW = {'uh': (640, 1190, 2390), 'ee': (300, 2250, 2950), 'oh': (500, 900, 2400), 'ih': (400, 1950, 2550), 'aw': (580, 860, 2410), 'ai': (720, 1100, 2450)}
def syllable(s):
    dur = s['t1'] - s['t0']; N = int(dur * SR); tt = np.arange(N) / SR
    soft = s['kind'] == 'soft'
    f0 = (205 if soft else 235) * (1 + (0.10 if not soft else 0.04) * np.sin(np.pi * tt / dur) - 0.08 * tt / dur)
    f0 *= 1 + 0.01 * rng.standard_normal(N).cumsum() / np.sqrt(np.arange(1, N + 1))
    ph = np.cumsum(f0 / SR); src = (ph % 1.0) * 2 - 1           # sawtooth glottal source
    src = lfilter([1], [1, -0.96], np.diff(np.concatenate([[0], src])))  # tilt
    breath = rng.standard_normal(N) * (0.9 if soft else 0.25)
    x = src * (0.45 if soft else 1.0) + breath * 0.25
    F = VOW[s['vowel']]
    if s['vowel'] == 'ai':   # diphthong: glide toward ee
        a, b = np.array(VOW['ai']), np.array(VOW['ee']); y = np.zeros(N); half = N // 2
        y[:half] = sum(reson(x[:half], f, 90 + 40 * k) * g for k, (f, g) in enumerate(zip(a, (1, 0.6, 0.3))))
        y[half:] = sum(reson(x[half:], f, 90 + 40 * k) * g for k, (f, g) in enumerate(zip(b, (1, 0.6, 0.3))))
    else:
        y = sum(reson(x, f, 80 + 40 * k) * g for k, (f, g) in enumerate(zip(F, (1, 0.55, 0.28))))
    y *= env(N, 0.03 if not soft else 0.06, 0.07 if not soft else 0.12)
    # consonants: k (come), h (here), s (it's), r/t (right), n (in)
    lead = rng.standard_normal(int(0.05 * SR))
    if s['vowel'] in ('uh',) and not soft: y[:len(lead)] += bp(lead, 1800, 3500) * np.linspace(1, 0, len(lead)) * 0.5
    if s['vowel'] == 'ee' and not soft: y[:len(lead)] += hp(lead, 1200) * np.linspace(0.6, 0.1, len(lead)) * 0.4
    if s['vowel'] == 'ih' and soft: tail = hp(rng.standard_normal(int(0.06 * SR)), 4000) * 0.25; y[-len(tail):] += tail * np.linspace(0.2, 1, len(tail))
    y = y / (np.max(np.abs(y)) + 1e-9)
    return y
vol = {'call': 0.42, 'soft': 0.75}
voice_rms = {'call': [], 'soft': []}
for s in TR['voice']:
    y = syllable(s) * vol[s['kind']] * 10 ** (s['level'] / 20)
    voice_rms[s['kind']].append(db(y[int(0.03 * SR):-int(0.05 * SR)]))
    room_ = reson(np.concatenate([y, np.zeros(int(0.25 * SR))]), 300, 400) * 0.05  # a little room
    put(np.concatenate([y, np.zeros(int(0.25 * SR))]) + room_, s['t0'], 1.0, -0.55)

# ---------------- wood and the dog
def pad(level_db, bright=0.4):
    N = int(0.07 * SR); x = rng.standard_normal(N)
    th = lp(x, 350) * env(N, 0.002, 0.06) * 2.5
    click = hp(rng.standard_normal(int(0.008 * SR)), 2500) * bright * 0.35
    th[:len(click)] += click
    return th * 10 ** (level_db / 20)
X = json.load(open(os.path.join(D, 'scene/xsheet.json')))['frames']
def dog_pan(tt):
    i = min(767, max(0, int(round(tt * 24)))); return float(np.clip((X[i]['x'] - 1.5) / 3.0, -0.8, 0.8))
for e in TR['footfalls']:
    put(pad(e['level'] - 14, 0.5 if e['leg'].endswith('f') else 0.3), e['t'], 1.0, dog_pan(e['t']))
for e in TR['thumps']:
    N = int(0.12 * SR); th = lp(rng.standard_normal(N), 160) * env(N, 0.003, 0.1) * 3
    put(th * 10 ** ((e['level'] - 8) / 20), e['t'], 1.0, 0.0)
for e in TR['person_steps']:
    N = int(0.1 * SR); th = lp(rng.standard_normal(N), 260) * env(N, 0.002, 0.09) * 2.4
    put(th * 0.12, e['t'], 1.0, -0.7)
# stool creak as the person sits
N = int(0.35 * SR); tt = np.arange(N) / SR
creak = bp(rng.standard_normal(N) * (np.sin(2 * np.pi * (28 + 30 * tt) * tt) > 0.6), 500, 1400) * env(N, 0.02, 0.15)
put(creak * 0.05, TR['sit'], 1.0, -0.75)
# door: latch click, then the creak of the swing
N = int(0.03 * SR); put(hp(rng.standard_normal(N), 2000) * env(N, 0.001, 0.025) * 0.12, TR['door']['latch'], 1.0, -0.4)
d0, d1 = TR['door']['swing']; N = int((d1 - d0) * SR); tt = np.arange(N) / SR
rate = 18 + 55 * tt / (d1 - d0)
stick = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.85).astype(float)
cr = reson(reson(stick + 0.1 * rng.standard_normal(N), 820, 120), 1650, 260)
cr = cr / (np.max(np.abs(cr)) + 1e-9) * env(N, 0.08, 0.2) * 0.07
put(cr, d0, 1.0, -0.35)
# the dog's breath: a small whine as it turns back to look; a sniff on the approach; the sigh when it settles
def whine(dur, f_a, f_b):
    N = int(dur * SR); tt = np.arange(N) / SR; f = np.linspace(f_a, f_b, N) * (1 + 0.02 * np.sin(2 * np.pi * 6 * tt))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * rng.standard_normal(N) * 0.3
    return bp(y, 500, 2500) * env(N, 0.05, 0.12)
put(whine(0.42, 820, 1050) * 0.035, 7.55, 1.0, 0.6)
for ts in (13.1, 13.35, 21.6, 21.8):
    N = int(0.09 * SR); put(bp(rng.standard_normal(N), 900, 4000) * env(N, 0.01, 0.06) * 0.03, ts, 1.0, dog_pan(ts))
N = int(1.1 * SR); tt = np.arange(N) / SR
sigh = bp(rng.standard_normal(N), 300, 1800) * env(N, 0.15, 0.7) * (1 - 0.5 * tt / tt[-1])
put(sigh * 0.05, 28.55, 1.0, 0.0)

# ---------------- music: enters with the light (a warm pad), a few plucked notes as it comes, a chord at the sill
def note(f, dur, amp, kind='pad'):
    N = int(dur * SR); tt = np.arange(N) / SR
    if kind == 'pad':
        y = sum(np.sin(2 * np.pi * f * h * tt + h) / h ** 1.6 for h in (1, 2, 3)) * env(N, dur * 0.35, dur * 0.45)
        y *= 1 + 0.03 * np.sin(2 * np.pi * 4.5 * tt)
    else:
        y = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * np.sin(2 * np.pi * 3.01 * f * tt)) * np.exp(-tt * 3.2)
        y[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return y * amp
mid = lambda m: 440 * 2 ** ((m - 69) / 12)
for m in (53, 57, 60, 64):   # F major 7, under the door opening
    put(note(mid(m), 7.0, 0.012), 6.3, 1.0, 0.0)
for k, m in enumerate((72, 69, 67, 64, 65, 67, 69, 72, 71, 69)):   # plucks as it comes (14.7 - 23.4)
    put(note(mid(m), 1.6, 0.03, 'pluck'), 14.9 + k * 0.92, 1.0, 0.2)
for m in (48, 55, 60, 64, 67):   # at the sill
    put(note(mid(m), 6.0, 0.011), 24.0, 1.0, 0.0)
for m in (53, 60, 64, 69):   # settles; carries into the end card
    put(note(mid(m), 9.0, 0.011), 28.7, 1.0, 0.0)
# title sting
put(note(mid(76), 2.0, 0.025, 'pluck'), -2.4, 1.0, -0.2); put(note(mid(72), 2.0, 0.022, 'pluck'), -1.9, 1.0, 0.2)
# fades at the very ends
fade = np.ones(n); fi = int(0.4 * SR); fade[:fi] = np.linspace(0, 1, fi); fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
L *= fade; Rr *= fade
peak = max(np.max(np.abs(L)), np.max(np.abs(Rr)))
g = 0.89 / peak; L *= g; Rr *= g
out = np.stack([L, Rr], 1)
os.makedirs(os.path.join(D, 'build/cache'), exist_ok=True)
import wave
with wave.open(os.path.join(D, 'build/cache/sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype('<i2').tobytes())
# measured levels (in the final mix, mono sum, voice windows vs a room-tone window)
mono = (L + Rr) / 2
def win(a, b): return mono[at(a):at(b)]
calls = np.concatenate([win(s['t0'] + 0.03, s['t1'] - 0.05) for s in TR['voice'] if s['kind'] == 'call'])
softs = np.concatenate([win(s['t0'] + 0.03, s['t1'] - 0.05) for s in TR['voice'] if s['kind'] == 'soft'])
quiet = np.concatenate([win(12.0, 14.5), win(29.5, 31.5)])
lev = dict(call_rms_db=round(db(calls), 2), soft_rms_db=round(db(softs), 2), room_tone_rms_db=round(db(quiet), 2))
lev['soft_under_call_db'] = round(lev['call_rms_db'] - lev['soft_rms_db'], 2)
lev['soft_over_room_db'] = round(lev['soft_rms_db'] - lev['room_tone_rms_db'], 2)
json.dump(lev, open(os.path.join(D, 'build/cache/sound_levels.json'), 'w'), indent=1)
print('sound', lev)
