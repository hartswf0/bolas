"""SOUND: synthesized here, nothing recorded or downloaded. Events come from the decoded path (the drawings on screen):
paws touch the boards when a walking drawing puts a lifted paw down; the body thumps when a lying drawing first
appears; the tail knocks the boards when the wag drawing swings down. The person's voice is a small formant
synthesizer (harmonics shaped by vowel resonances, noise for consonants). Calls are loud; the soft voice is quiet.
python3 build/sound.py -> build/cache/sound.wav, build/cache/sound_levels.json"""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
FOLD = os.path.abspath(os.path.join(HERE, '..'))
SR = 48000
T0 = 3.0                      # the scene starts after the 3 s title card
DUR = 38.0
N = int(SR * DUR)
rng = np.random.default_rng(14)
BANK = json.load(open(os.path.join(FOLD, 'bank', 'bank.json')))
PATH = json.load(open(os.path.join(C, 'path.json')))['frames']
CUES = json.load(open(os.path.join(C, 'cues.json')))
out = np.zeros(N)
stems = {k: np.zeros(N) for k in ('room', 'voice', 'dog', 'house', 'person')}


def db(x):
    return 10 ** (x / 20)


def place(sig, t, gain_db, stem):
    i = int((t + T0) * SR)
    if i >= N: return
    j = min(N, i + len(sig))
    stems[stem][i:j] += sig[:j - i] * db(gain_db)


def shaped_noise(n, lo, hi, seed=None, tilt=0.0):
    r = np.random.default_rng(seed) if seed is not None else rng
    x = r.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    # soft edges
    m = np.convolve(m, np.hanning(31) / np.hanning(31).sum(), mode='same')
    if tilt: m *= (1 + f / 1000.0) ** (-tilt)
    y = np.fft.irfft(X * m, n)
    return y / (np.sqrt(np.mean(y ** 2)) + 1e-12)


def env(n, a, r, hold=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a - hold) / max(r, 1e-4))
    return e


# ---------------------------------------------------------------- voice
VOW = {'ʌ': (640, 1190, 2390), 'ɪ': (390, 1990, 2550), 'ə': (500, 1500, 2500), 'i': (300, 2300, 3000), 'ɔ': (570, 840, 2410),
       'a': (730, 1090, 2440), 'm': (260, 1100, 2300), 'n': (270, 1500, 2500), 'l': (360, 1000, 2500), 'r': (430, 1250, 1650)}


def voice(phones, f0s, level_curve=None, breath=0.08, fscale=1.12):
    """phones: list of (symbol, dur). Symbols in VOW are voiced; 'k','t' plosives; 's' fricative; 'h' aspiration; '_' silence.
    f0s: list of (time fraction, Hz) breakpoints."""
    total = sum(d for _, d in phones); n = int(total * SR)
    F = np.zeros((3, n)); V = np.zeros(n); NZ = np.zeros(n); band = np.zeros((2, n))
    i = 0
    last = VOW['ə']
    for k, (ph, d) in enumerate(phones):
        m = int(d * SR); sl = slice(i, i + m)
        nxt = next((p for p, _ in phones[k + 1:] if p in VOW), 'ə')
        if ph in VOW:
            F[:, sl] = np.array(VOW[ph])[:, None] * fscale; V[sl] = .5 if ph in 'mn' else (.75 if ph in 'lr' else 1.0); last = VOW[ph]
        else:
            F[:, sl] = np.array(VOW[nxt])[:, None] * fscale
            if ph == 'h': NZ[sl] = .5; band[:, sl] = np.array([[400], [3500]])
            if ph == 's': NZ[sl] = .55; band[:, sl] = np.array([[4200], [9000]])
            if ph in 'kt':
                b = int(.028 * SR); NZ[i + m - b:i + m] = 1.0
                band[:, sl] = np.array([[1500], [4000]]) if ph == 'k' else np.array([[3000], [7000]])
        i += m
    # coarticulation: smooth the tracks over ~25 ms
    w = np.hanning(int(.025 * SR)); w /= w.sum()
    for a in (F[0], F[1], F[2]): a[:] = np.convolve(a, w, mode='same')
    V = np.convolve(V, np.hanning(int(.018 * SR)) / np.hanning(int(.018 * SR)).sum(), mode='same')
    # pitch
    tt = np.linspace(0, 1, n)
    f0 = np.interp(tt, [a for a, _ in f0s], [b for _, b in f0s]) * (1 + .012 * np.sin(2 * np.pi * 5.2 * tt * total))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    y = np.zeros(n)
    BW = (90, 120, 160)
    for h in range(1, 30):
        fh = h * f0
        amp = np.zeros(n)
        for j in range(3):
            amp += (1.0, .55, .3)[j] / (1 + ((fh - F[j]) / BW[j]) ** 2)
        amp *= (fh < 5500) * (1.0 / h ** .55)
        y += amp * np.sin(h * ph)
    y *= V
    # breath + consonant noise
    nz = rng.standard_normal(n)
    segs = []
    for lo, hi in {(int(a), int(b)) for a, b in band.T if b > 0}:
        msk = (band[0] == lo) & (band[1] == hi)
        segs.append(shaped_noise(n, lo, hi) * msk)
    cons = sum(segs) if segs else np.zeros(n)
    y = y / (np.sqrt(np.mean(y[V > .5] ** 2)) + 1e-9) if (V > .5).any() else y
    y = y + cons * NZ * .55 + shaped_noise(n, 300, 5000) * breath * V
    e = np.ones(n)
    a = int(.01 * SR); e[:a] = np.linspace(0, 1, a); e[-a * 3:] = np.linspace(1, 0, a * 3)
    if level_curve:
        e *= np.interp(tt, [p for p, _ in level_curve], [q for _, q in level_curve])
    return y * e


def call(t, loud):
    s = voice([('_', .02), ('k', .07), ('ʌ', .15), ('m', .09), ('h', .07), ('ɪ', .15), ('ə', .2)],
              [(0, 230 + loud * 20), (.45, 250 + loud * 25), (.62, 300 + loud * 35), (1, 210 + loud * 15)],
              [(0, .8), (.5, 1), (.75, 1), (1, .7)], breath=.05)
    place(s, t, -10 + loud * 2, 'voice')


def soft(t, words):
    if words == 'all':
        ph = [('ɪ', .09), ('t', .05), ('s', .1), ('ɔ', .17), ('l', .08), ('r', .07), ('a', .16), ('ɪ', .12), ('t', .06), ('_', .04)]
        f0 = [(0, 185), (.35, 175), (.6, 168), (1, 140)]
    else:  # come in
        ph = [('_', .02), ('k', .06), ('ʌ', .14), ('m', .08), ('ɪ', .16), ('n', .14)]
        f0 = [(0, 180), (.5, 172), (1, 148)]
    s = voice(ph, f0, [(0, .8), (.4, 1), (1, .6)], breath=.32)
    place(s, t, -21, 'voice')


for a, b, txt, kind in CUES['lines']:
    if kind == 'call':
        call(a + .02, 1 if a > 3 else 0)
    else:
        soft(a + .05, 'in' if txt.startswith('Come in') else 'all')
        if b - a > 1.6:      # the soft voice lasts: say it once more, quieter
            soft(a + 1.05, 'all') if not txt.startswith('Come in') else None

# ---------------------------------------------------------------- room tone, crickets, the house
room = shaped_noise(N, 40, 500, seed=1, tilt=1.0) * db(-50)
stems['room'] += room
t = 0.0
r2 = np.random.default_rng(3)
while t < DUR:
    for pitch, lvl in ((4700, -44), (5300, -48)):
        if r2.random() < .8:
            g = r2.uniform(.75, 1.3)
            for k in range(3):
                n = int(.018 * SR); tt = np.arange(n) / SR
                p = np.sin(2 * np.pi * pitch * tt) * np.sin(np.pi * tt / .018) ** 2
                i = int((t + k * .034 + (0 if pitch < 5000 else .41)) * SR)
                if i + n < N: stems['room'][i:i + n] += p * db(lvl)
    t += r2.uniform(.7, 1.15)


def door_open(t):
    return 0 if t < 6.2 else min(1, (t - 6.2) / .9)


# door creak: stick-slip pulses through a wooden resonance, then the room's clock comes out with the light
n = int(.95 * SR); cr = np.zeros(n); tt = 0.0
while tt < .9:
    rate = 40 + 120 * math.sin(math.pi * tt / .9) ** 1.5
    i = int(tt * SR); cr[i] += rng.uniform(.5, 1.0); tt += 1 / rate * rng.uniform(.85, 1.15)
X = np.fft.rfft(cr); f = np.fft.rfftfreq(n, 1 / SR)
res = 1 / (1 + ((f - 900) / 220) ** 2) + .6 / (1 + ((f - 2100) / 300) ** 2)
cr = np.fft.irfft(X * res, n); cr /= np.abs(cr).max(); cr *= np.hanning(n) ** .3
place(cr, 6.2, -20, 'house')
lat = shaped_noise(int(.012 * SR), 1800, 6000) * env(int(.012 * SR), .001, .003)
place(lat, 6.18, -28, 'house')
k = 6.6
while k < 32.0:
    lvl = -44 + 6 * door_open(k)
    tick = shaped_noise(int(.006 * SR), 2500, 6000) * env(int(.006 * SR), .0005, .0015)
    place(tick, k, lvl, 'house'); k += 1.0
hum = shaped_noise(int(25.5 * SR), 60, 380, seed=9, tilt=.8)
hum *= np.minimum(1, np.arange(len(hum)) / SR / .9)
place(hum, 6.3, -52, 'house')

# ---------------------------------------------------------------- the dog, from the drawings on screen
def paw(t, lvl):
    n = int(.05 * SR)
    pad = shaped_noise(n, 60, 450) * env(n, .002, .012)
    nail = np.zeros(n); m = int(.004 * SR); nail[:m] = shaped_noise(m, 2500, 6500) * np.hanning(m)
    place(pad + .5 * nail, t, lvl + rng.uniform(-2, 1.5), 'dog')


def thump(t, lvl, f0=75, dur=.3):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (f0 - 25 * tt / dur) * tt) * np.exp(-tt / (dur / 4)) + .5 * shaped_noise(n, 60, 700) * np.exp(-tt / .03)
    place(s, t, lvl, 'dog')


events = []
for a, b in zip(PATH, PATH[1:]):
    da, db_ = BANK['drawings'][a['dog']], BANK['drawings'][b['dog']]
    if da['meta'].get('gait') and db_['meta'].get('gait'):
        for leg, (x, y) in db_['meta']['feet'].items():
            ya = da['meta']['feet'][leg][1]
            if ya < -.5 and abs(y) < .5:
                back = db_['meta']['gait']['dir'] > 0
                paw(b['t'], -31 if back else -34); events.append(('paw', b['t'], leg))
    if b['dog'] != a['dog']:
        if b['dog'] in ('lie_R', 'lie_up') and a['dog'] in ('sink_R', 'sit'): thump(b['t'], -24); events.append(('lies down', b['t']))
        if b['dog'] == 'look_in_b': thump(b['t'], -33, f0=110, dur=.12); events.append(('tail knocks', b['t']))
        if b['dog'] == 'rest' and b['t'] > 27:
            n = int(.8 * SR); s = shaped_noise(n, 150, 1400) * env(n, .12, .25, .15)
            place(s, b['t'], -32, 'dog'); events.append(('sighs', b['t']))
        if b['dog'] == 'q45_low':
            pass
    pa, pb = BANK['drawings'][a['person']], BANK['drawings'][b['person']]
    if pa['meta'].get('gait') and pb['meta'].get('gait'):
        for leg, (x, y) in pb['meta']['feet'].items():
            if pa['meta']['feet'][leg][1] < -.5 and abs(y) < .5:
                n = int(.12 * SR); tt = np.arange(n) / SR
                s = shaped_noise(n, 50, 320) * np.exp(-tt / .02) + .6 * np.sin(2 * np.pi * 170 * tt) * np.exp(-tt / .05)
                place(s, b['t'], -27, 'person'); events.append(('step', b['t']))
    if pb['meta'].get('group') == 'person' and b['person'] == 'P_sit' and a['person'] != 'P_sit':
        n = int(.35 * SR); cr2 = np.zeros(n); tt = 0.0
        while tt < .32: i = int(tt * SR); cr2[i] += 1; tt += 1 / (50 + 40 * math.sin(math.pi * tt / .32))
        X = np.fft.rfft(cr2); f = np.fft.rfftfreq(n, 1 / SR); cr2 = np.fft.irfft(X / (1 + ((f - 520) / 160) ** 2), n); cr2 /= np.abs(cr2).max()
        place(cr2, b['t'], -30, 'person'); events.append(('bench', b['t']))

# a small whine after the reach, a sniff when it decides to come
def whine(t, dur=.55, lvl=-31):
    n = int(dur * SR); tt = np.arange(n) / SR
    f0 = 980 - 380 * tt / dur
    ph = 2 * np.pi * np.cumsum(f0) / SR
    s = sum((1 / h) * np.sin(h * ph) / (1 + ((h * f0 - 1600) / 600) ** 2) for h in range(1, 6))
    s = s / np.abs(s).max() * np.sin(np.pi * tt / dur) ** 1.5
    place(s + .15 * shaped_noise(n, 800, 3000) * np.sin(np.pi * tt / dur), t, lvl, 'dog')


whine(4.66); events.append(('whines', 4.66))
for k in (14.45, 14.6):
    n = int(.07 * SR); place(shaped_noise(n, 900, 4500) * env(n, .01, .02), k, -34, 'dog')
events.append(('sniffs', 14.45))

mix = sum(stems.values())
# fade the room in under the title and out under the end card
tt = np.arange(N) / SR
fade = np.clip(tt / 2.5, 0, 1) * np.clip((DUR - tt) / 2.5, 0, 1)
mix *= np.where((tt > T0) & (tt < T0 + 32), 1, .55 + .45 * fade)
peak = np.abs(mix).max()
if peak > db(-1): mix *= db(-1) / peak


def rms_db(x):
    return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


lv = {}
v = stems['voice']
calls = [(a, b) for a, b, _, k in CUES['lines'] if k == 'call']; softs = [(a, b) for a, b, _, k in CUES['lines'] if k == 'soft']


def active_rms(sig, wins):
    seg = np.concatenate([sig[int((a + T0) * SR):int((a + T0 + 1.2) * SR)] for a, b in wins])
    frames = seg[:len(seg) // 960 * 960].reshape(-1, 960)
    e = np.sqrt((frames ** 2).mean(1))
    act = e[e > e.max() * .1]
    return 20 * math.log10(np.sqrt((act ** 2).mean()))


lv['call_rms_dbfs'] = round(active_rms(v, calls), 2)
lv['soft_rms_dbfs'] = round(active_rms(v, softs), 2)
lv['soft_below_call_db'] = round(lv['call_rms_dbfs'] - lv['soft_rms_dbfs'], 2)
quiet = slice(int((T0 + 12.0) * SR), int((T0 + 14.0) * SR))
lv['room_tone_rms_dbfs_12_14s'] = round(rms_db((stems['room'] + stems['house'])[quiet]), 2)
lv['soft_above_room_db'] = round(lv['soft_rms_dbfs'] - lv['room_tone_rms_dbfs_12_14s'], 2)
lv['peak_dbfs'] = round(20 * math.log10(np.abs(mix).max()), 2)
lv['events'] = [e for e in events if e[0] != 'paw'] + [('paws', len([e for e in events if e[0] == 'paw']))]
lv['note'] = 'measured on the synthesized stems before mixing to AAC; nobody has listened to this sound'
y = (mix * 32767).astype(np.int16)
with wave.open(os.path.join(C, 'sound.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
json.dump(lv, open(os.path.join(C, 'sound_levels.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in lv.items() if k != 'events'}, indent=1)); print(lv['events'][:30])
