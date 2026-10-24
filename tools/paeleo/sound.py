"""PAELEO-00 · The threshold: the soundtrack, synthesized from the cues the render wrote (cues.json).
Every sound is made here from numbers: no samples. python3 tools/paeleo/sound.py OUTDIR  ->  OUTDIR/sound.wav

Keys and the return carry the prompt; the voice is a muted, wordless murmur with the contour of the words (the words are on screen);
paws tap the boards and get louder as the dog comes nearer; the door creaks; crickets hold the dusk; a pad sits under the titles."""
import json, sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]
cues = json.load(open(f'{out}/cues.json'))
DUR = cues['dur']
N = int(DUR * SR) + SR
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)


def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[:max(0, N - i)] * gain
    if i < 0: s = s[-i:]; i = 0
    L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2); R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2)


def env(n, a, d):
    e = np.ones(n); ai = max(1, int(a * SR)); di = max(1, int(d * SR))
    e[:ai] = np.linspace(0, 1, ai); e[-di:] *= np.linspace(1, 0, di) ** 2; return e


def reson(x, f, q):
    """two-pole resonator (a band of a formant)"""
    w = 2 * np.pi * f / SR; r = np.exp(-w / (2 * q)); a1, a2 = -2 * r * np.cos(w), r * r
    y = np.zeros_like(x); y1 = y2 = 0.0
    for i in range(len(x)):
        v = x[i] - a1 * y1 - a2 * y2; y[i] = v; y2, y1 = y1, v
    return y * (1 - r)


def lowpass(x, f):
    a = np.exp(-2 * np.pi * f / SR); y = np.zeros_like(x); p = 0.0
    for i in range(len(x)): p = (1 - a) * x[i] + a * p; y[i] = p
    return y


def noise(d): return rng.standard_normal(int(d * SR))


def key(n):   # a typewriter-ish key: a click and a short body
    d = .045; t = np.arange(int(d * SR)) / SR
    c = noise(d) * np.exp(-t * 260) * .5 + np.sin(2 * np.pi * (1700 + 160 * (n % 5)) * t) * np.exp(-t * 180) * .25
    return c


def ret():
    d = .16; t = np.arange(int(d * SR)) / SR
    return noise(d) * np.exp(-t * 90) * .35 + np.sin(2 * np.pi * 420 * t) * np.exp(-t * 40) * .3


# vowel formants (F1, F2, F3)
VOW = {'a': (730, 1090, 2440), 'u': (440, 1020, 2240), 'i': (300, 2200, 2900), 'e': (530, 1840, 2480), 'o': (570, 840, 2410), 'r': (490, 1350, 1690)}


def voice(sylls, loud):
    """sylls: [(vowel, dur, f0 start, f0 end)]. A glottal pulse train through formant resonators: a muted, wordless voice."""
    parts = []
    for v, d, f0a, f0b in sylls:
        n = int(d * SR); t = np.arange(n) / SR
        f0 = np.linspace(f0a, f0b, n) * (1 + .012 * np.sin(2 * np.pi * 5.5 * t))
        ph = np.cumsum(f0) / SR; src = (ph % 1.0) ** 3 * 2 - .5 + noise(d) * .03
        y = sum(reson(src, f, 9 + 3 * k) * g for k, (f, g) in enumerate(zip(VOW[v], (1, .6, .25))))
        parts.append(y * env(n, .03, .07)); parts.append(np.zeros(int(.03 * SR)))
    y = np.concatenate(parts); y /= (np.abs(y).max() + 1e-9)
    return lowpass(y, 2600 if loud else 1700) * (.5 if loud else .3)


CALL1 = [('u', .2, 210, 230), ('i', .42, 290, 220)]                 # "come HERE"
CALL2 = [('u', .2, 240, 260), ('r', .5, 340, 230)]                  # "come HERE!" again, harder
SOFT = [('i', .16, 165, 160), ('o', .26, 170, 150), ('a', .22, 160, 140), ('i', .34, 150, 125)]   # "it's all right"
COMEIN = [('u', .26, 175, 168), ('i', .55, 172, 132)]               # "come in"


def creak(d=1.3):
    n = int(d * SR); t = np.arange(n) / SR
    f = 180 + 120 * np.sin(np.pi * t / d) + 30 * np.sin(2 * np.pi * 7 * t)
    ph = np.cumsum(f) / SR; src = ((ph % 1) < .08).astype(float) + noise(d) * .05
    y = reson(src, 900, 6) + reson(src, 2100, 8) * .5
    return y / (np.abs(y).max() + 1e-9) * env(n, .1, .3) * .3


def thud(f=90, d=.25, g=.6):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t * (1 - .3 * t)) * np.exp(-t * 18) + noise(d) * np.exp(-t * 60) * .3) * g


def paw():
    d = .06; t = np.arange(int(d * SR)) / SR
    return (noise(d) * np.exp(-t * 200) * .4 + np.sin(2 * np.pi * (520 + rng.integers(-60, 60)) * t) * np.exp(-t * 120) * .5)


def flick():   # a paper tag turning over
    d = .12; t = np.arange(int(d * SR)) / SR
    return noise(d) * (np.exp(-t * 70) * .25 + np.exp(-np.abs(t - .05) * 120) * .2)


def huff(d=.6):  # a dog's exhale through the nose
    n = int(d * SR); t = np.arange(n) / SR
    return lowpass(noise(d), 900) * np.exp(-t * 5) * env(n, .04, .3) * 1.4


def whine(d=.9):
    n = int(d * SR); t = np.arange(n) / SR; f = 900 - 250 * t / d + 25 * np.sin(2 * np.pi * 6 * t)
    return np.sin(np.cumsum(f) * 2 * np.pi / SR) * env(n, .12, .4) * .06


def pad(chord, d, g=.12):
    n = int(d * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for k, f in enumerate(chord):
        for det in (-.6, .6): y += np.sin(2 * np.pi * (f + det) * t + k) * (1 / (1 + k * .4))
    return y / len(chord) * env(n, 1.2, 1.8) * g


def chime(f, g=.25, d=2.5):
    t = np.arange(int(d * SR)) / SR
    return sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (2 + h)) / h for h in (1, 2.76, 5.4)) * g


def cricket_bed(t0, t1):
    n = int((t1 - t0) * SR); y = np.zeros(n)
    for c in range(3):
        f = 4300 + 350 * c; period = .9 + .23 * c; t = np.arange(n) / SR
        chirp = (np.sin(2 * np.pi * 28 * t) > .2) * ((t + c * .31) % period < .22)
        y += np.sin(2 * np.pi * f * t) * chirp * (.010 + .004 * c)
    y += lowpass(noise(t1 - t0), 300) * .02   # the evening's air
    fade = np.ones(n); k = int(1.5 * SR); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
    return y * fade


# ---------------------------------------------------------------- beds and music
place(cricket_bed(4.6, 63.5), 4.6, 1.0, .2)
place(pad([220, 277.2, 329.6, 493.9], 6.0, .09), 0.0)                    # the page
place(pad([196, 246.9, 293.7, 440], 4.6, .10), 14.3)                      # the title
place(chime(587.3, .18), 14.6, 1, -.2)
place(pad([174.6, 220, 261.6, 392], 8.5, .11), 63.2)                       # three scales
place(pad([261.6, 329.6, 392, 587.3], 11.0, .12), 71.2)                    # the lockup and credits
place(chime(523.3, .2), 71.6, 1, .1); place(chime(784, .12), 73.0, 1, -.1)

T0 = cues['T0']
for c in cues['sfx']:
    t, k = c['t'], c['k']
    if k == 'key': place(key(c['n']), t, .55, -.35)
    elif k == 'return': place(ret(), t, .6, -.35)
    elif k == 'call': place(voice(CALL2 if 'HERE' in c['text'] else CALL1, True), t, .9, -.45)
    elif k == 'soft': place(voice(COMEIN if 'come' in c['text'] else SOFT, False), t, .9, -.5)
    elif k == 'creak': place(creak(), t, 1, -.05)
    elif k == 'sit': place(thud(70, .3, .5), t, 1, -.5)
    elif k == 'step': place(thud(110, .14, .22), t, 1, -.4)
    elif k == 'flick': place(flick(), t, 1, .0)
    elif k == 'paw':
        near = 1 - min(1, max(0, (c.get('x', 3) - .3) / 4.5)); place(paw(), t, .12 + .2 * near, .2 + .4 * (1 - near))
    elif k == 'thump': place(thud(85, .2, .32), t, 1, .05)
    elif k == 'rise': place(huff(.4), t, .6, .5)
    elif k == 'state':
        if c['to'] == 'refuse': place(huff(.7), t + .5, .9, .5); place(whine(), t + 1.1, 1, .5)
        elif c['to'] == 'retreat': place(thud(140, .1, .15), t + .05, 1, .5)
        elif c['to'] == 'lie_down': place(thud(60, .35, .35), t + .45, 1, .2); place(huff(.9), t + 1.3, .7, .2)
        elif c['to'] == 'watch' and c['from'] == 'refuse': place(flick(), t + .1, 1.4, .5)
    elif k == 'pulse': place(chime(880, .15, 1.2), t, 1, .4)
    elif k == 'unfold': place(flick(), t, 2.0, 0); place(flick(), t + .6, 1.5, 0)
    elif k == 'reply': place(chime(659.3, .14, 1.8), t, 1, 0)

m = max(np.abs(L).max(), np.abs(R).max()); g = .89 / m
st = np.stack([L, R], 1)[:int(DUR * SR)] * g
with wave.open(f'{out}/sound.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('sound', DUR, 's, peak gain', round(g, 3))
