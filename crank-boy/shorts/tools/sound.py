"""Synthesised soundtrack for a short, from the cue list its page declares (window.SHORT.cues).
Every sound is made here from oscillators and filtered noise; nothing is sampled.
A cue is {"t": seconds, "k": kind, ...}. Kinds and their fields are the functions below."""
import numpy as np

SR = 48000
rng = np.random.default_rng(1910)


def env(n, a=0.005, r=0.08):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def fast_lp(x, f):
    # one-pole low-pass by blocks; a cheap stand-in for long noise beds
    a = np.exp(-2 * np.pi * f / SR)
    from itertools import accumulate
    return np.array(list(accumulate(x, lambda acc, v: (1 - a) * v + a * acc)))


def noise(n, color='white'):
    w = rng.standard_normal(n)
    if color == 'brown':
        w = np.cumsum(w)
        w -= fast_lp(w, 8)
        w /= np.max(np.abs(w)) + 1e-9
    return w


def tone(c):
    d, f = c.get('d', .3), c.get('f', 440)
    n = int(d * SR); t = np.arange(n) / SR
    f1 = c.get('f1', f)
    ph = 2 * np.pi * np.cumsum(np.linspace(f, f1, n)) / SR
    w = c.get('wave', 'sine')
    x = np.sin(ph) if w == 'sine' else np.sign(np.sin(ph)) * .5 if w == 'square' else (2 * ((ph / (2 * np.pi)) % 1) - 1) * .5
    if c.get('vib'):
        x *= 1 + .15 * np.sin(2 * np.pi * c['vib'] * t)
    return x * env(n, c.get('att', .01), c.get('rel', d * .6)) * c.get('a', .3)


def click(c):
    n = int(.02 * SR)
    x = noise(n) * np.exp(-np.arange(n) / (SR * .002))
    x = x + np.sin(2 * np.pi * c.get('f', 1800) * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * .004)) * .6
    return x * c.get('a', .4)


def ratchet(c):
    d, rate = c.get('d', 1), c.get('rate', 12)
    out = np.zeros(int(d * SR) + SR // 10)
    for i in range(int(d * rate)):
        s = int(i / rate * SR)
        k = click({'a': c.get('a', .25) * (0.8 + .4 * rng.random()), 'f': c.get('f', 1400) * (0.9 + .2 * rng.random())})
        out[s:s + len(k)] += k
    return out


def hum(c):
    d, f = c.get('d', 2), c.get('f', 55)
    n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * t) / h for h in (1, 2, 3, 5))
    x *= 1 + .2 * np.sin(2 * np.pi * c.get('wob', 3) * t)
    return x * env(n, c.get('att', .3), c.get('rel', .4)) * c.get('a', .08)


def bed(c):
    # a filtered noise bed: wind, fire, water, the projector's draught
    d = c.get('d', 2); n = int(d * SR)
    x = noise(n, c.get('color', 'white'))
    if c.get('lp'):
        x = fast_lp(x, c['lp']); x /= np.max(np.abs(x)) + 1e-9
    if c.get('pulse'):
        t = np.arange(n) / SR
        x *= .55 + .45 * np.sin(2 * np.pi * c['pulse'] * t) ** 2
    return x * env(n, c.get('att', .3), c.get('rel', .5)) * c.get('a', .1)


def crackle(c):
    d = c.get('d', 2); n = int(d * SR)
    out = bed({'d': d, 'color': 'brown', 'a': c.get('a', .12) * .6, 'att': .4, 'rel': .6})
    for _ in range(int(d * c.get('rate', 30))):
        s = rng.integers(0, n - 2000)
        k = click({'a': c.get('a', .12) * rng.random(), 'f': 600 + 2400 * rng.random()})
        out[s:s + len(k)] += k
    return out


def bonk(c):
    f = c.get('f', 160); n = int(.5 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t * (1 - .35 * t)) * np.exp(-t * 9) + np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t * 20) * .4
    k = click({'a': .5, 'f': 900}); x[:len(k)] += k
    return x * c.get('a', .5)


def whoosh(c):
    d = c.get('d', .6); n = int(d * SR); t = np.linspace(0, 1, n)
    x = noise(n)
    lo = fast_lp(x, c.get('f', 900)); hi = x - fast_lp(x, 2500)
    m = np.sin(np.pi * t) ** 2
    return (lo * 3 * m + hi * .3 * m) / 3 * c.get('a', .4)


def flap(c):
    d, rate = c.get('d', 1), c.get('rate', 3)
    out = np.zeros(int(d * SR) + SR // 4)
    for i in range(int(d * rate)):
        k = whoosh({'d': .16, 'f': 500, 'a': c.get('a', .3)})
        s = int(i / rate * SR); out[s:s + len(k)] += k
    return out


def babble(c):
    """A voice without words: syllables from a buzz through two vowel formants."""
    d = c.get('d', 2); f0 = c.get('f0', 120)
    n = int(d * SR); t = np.arange(n) / SR
    syl = c.get('rate', 4.5)
    pitch = f0 * (1 + .12 * np.sin(2 * np.pi * .7 * t) + .05 * np.sin(2 * np.pi * syl * t))
    ph = 2 * np.pi * np.cumsum(pitch) / SR
    src = sum(np.sin(ph * h) / h for h in range(1, 24))
    vowels = [(730, 1090), (270, 2290), (570, 840), (440, 1020), (300, 870), (530, 1840)]
    seq = [vowels[i % 6] for i in rng.integers(0, 6, int(d * syl) + 2)]
    f1 = np.repeat([v[0] for v in seq], int(SR / syl) + 1)[:n]
    f2 = np.repeat([v[1] for v in seq], int(SR / syl) + 1)[:n]
    f1 = fast_lp(f1, 30); f2 = fast_lp(f2, 30)
    out = np.zeros(n)
    for fc, bw, g in ((f1, 90, 1), (f2, 120, .5)):
        # a two-pole resonator swept along the formant track
        y1 = y2 = 0.0
        r = np.exp(-np.pi * bw / SR)
        coef = 2 * r * np.cos(2 * np.pi * fc / SR)
        y = np.empty(n)
        for i in range(n):
            v = src[i] + coef[i] * y1 - r * r * y2
            y2, y1 = y1, v; y[i] = v
        out += y / (np.max(np.abs(y)) + 1e-9) * g
    gate = np.clip(np.sin(np.pi * ((t * syl) % 1)) * 1.6, 0, 1) ** .7
    gate *= .6 + .4 * (np.sin(2 * np.pi * .31 * t) > -.6)
    return out * gate * env(n, .05, .2) * c.get('a', .25)


def chime(c):
    out = np.zeros(int((c.get('step', .25) * len(c['notes']) + 1.5) * SR))
    for i, m in enumerate(c['notes']):
        f = 440 * 2 ** ((m - 69) / 12); n = int(1.4 * SR); t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 6)) * np.exp(-t * 3.2)
        s = int(i * c.get('step', .25) * SR); out[s:s + n] += x * c.get('a', .18)
    return out


def projector(c):
    d = c.get('d', 2); out = ratchet({'d': d, 'rate': c.get('rate', 18), 'a': c.get('a', .1), 'f': 900})
    h = hum({'d': d, 'f': 72, 'a': c.get('a', .1) * .6, 'wob': 18})
    out[:len(h)] += h
    return out


KINDS = dict(tone=tone, click=click, ratchet=ratchet, hum=hum, bed=bed, crackle=crackle, bonk=bonk, whoosh=whoosh,
             flap=flap, babble=babble, chime=chime, projector=projector)


def render(cues, dur, path):
    import wave
    mix = np.zeros((int((dur + 2) * SR), 2))
    for c in cues:
        x = KINDS[c['k']](c)
        s = int(c['t'] * SR)
        x = x[:max(0, len(mix) - s)]
        p = c.get('pan', 0)
        mix[s:s + len(x), 0] += x * (1 - max(0, p))
        mix[s:s + len(x), 1] += x * (1 + min(0, p))
    # room: a little tape hiss under everything
    mix += (rng.standard_normal(mix.shape) * .002)
    mix = mix[:int(dur * SR)]
    peak = np.max(np.abs(mix)) + 1e-9
    mix = np.tanh(mix / peak * 1.2) * .89
    fade = int(.4 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
