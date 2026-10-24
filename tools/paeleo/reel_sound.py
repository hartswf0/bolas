"""PAE-01 · SCION through the dog: the reel's soundtrack from reel.json. python3 tools/paeleo/reel_sound.py OUTDIR
A paper flick on every cut; the loop's own events (calls, the door, the soft voice) wherever they fall inside a cut;
a pad that changes chord with each family of swarms; crickets under the porch."""
import json, sys, wave
import numpy as np
SR = 44100; out = sys.argv[1]; R = json.load(open(f'{out}/reel.json'))
N = int(R['dur'] * SR) + SR; L = np.zeros(N); Rr = np.zeros(N); rng = np.random.default_rng(3)
def place(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i] * g; L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2); Rr[i:i + len(s)] += s * np.sqrt((1 + pan) / 2)
def env(n, a, d):
    e = np.ones(n); ai, di = max(1, int(a * SR)), max(1, int(d * SR)); e[:ai] = np.linspace(0, 1, ai); e[-di:] *= np.linspace(1, 0, di) ** 2; return e
def noise(d): return rng.standard_normal(int(d * SR))
def lowpass(x, f):
    a = np.exp(-2 * np.pi * f / SR); y = np.zeros_like(x); p = 0.0
    for i in range(len(x)): p = (1 - a) * x[i] + a * p; y[i] = p
    return y
def flick():
    d = .12; t = np.arange(int(d * SR)) / SR; return noise(d) * (np.exp(-t * 70) * .25 + np.exp(-np.abs(t - .05) * 120) * .2)
def tone(f0, f1, d, g, harsh):
    n = int(d * SR); f = np.linspace(f0, f1, n); ph = np.cumsum(f) / SR
    y = (np.sin(2 * np.pi * ph) + (.5 * np.sign(np.sin(2 * np.pi * ph)) if harsh else .3 * np.sin(4 * np.pi * ph)))
    return lowpass(y * env(n, .03, .1), 1800 if harsh else 900) * g
def creak(d=1.0):
    n = int(d * SR); t = np.arange(n) / SR; f = 180 + 120 * np.sin(np.pi * t / d); ph = np.cumsum(f) / SR
    return lowpass(((ph % 1) < .08).astype(float) + noise(d) * .05, 2500) * env(n, .1, .3) * .5
def clip(sig, d):
    """cut a sound to d seconds, with a 12 ms fade, so it ends before the next cut"""
    n = max(1, min(len(sig), int(d * SR))); out = sig[:n].copy(); f = min(n, int(.012 * SR)); out[n - f:] *= np.linspace(1, 0, f); return out
def pad(chord, d, g):
    n = int(d * SR); t = np.arange(n) / SR; y = sum(np.sin(2 * np.pi * f * t + k) / (1 + k * .4) for k, f in enumerate(chord)); return y / len(chord) * env(n, .8, 1.0) * g
FAM = {range(1, 8): [220, 277.2, 329.6, 440], range(8, 16): [196, 246.9, 293.7, 392], range(16, 29): [174.6, 220, 261.6, 349.2], range(29, 49): [164.8, 207.7, 246.9, 329.6], range(49, 55): [146.8, 185, 220, 293.7]}
chord = lambda i: next(v for k, v in FAM.items() if i in k)
place(clip(pad([196, 246.9, 293.7, 440], R['head'], .1), R['head'] - .1), 0)
# one pad per family run
runs = []
for c in R['cuts']:
    ch = chord(c['id'])
    if not runs or runs[-1][0] != ch: runs.append([ch, c['at'], c['at'] + R['each']])
    else: runs[-1][2] = c['at'] + R['each']
for c in R['cuts']: place(clip(pad(chord(c['id']), R['each'], .09), R['each'] - .1), c['at'] + .02)   # a chord for each lens, inside its 1.6 s: nothing sustains across a cut
for c in R['cuts']:
    place(flick(), c['at'], 2.4, .1); place(flick(), c['at'] + .02, 1.2, -.1)
    for t, w in R['tl']:
        if c['from'] <= t < c['from'] + R['each']:
            at = c['at'] + t - c['from']
            end = c['at'] + R['each'] - .1   # nothing runs across a cut: every sound ends 0.1 s before the next one, so the cut is heard
            fit = lambda sig: clip(sig, end - at)
            if w.get('voice') == 'call': place(fit(tone(220, 300, .45, .35, True)), at, 1, -.4)
            if w.get('voice') == 'soft': place(fit(tone(170, 140, .6, .25, False)), at, 1, -.4)
            if w.get('door') == 'open': place(fit(creak()), at, 1)
end = R['dur'] - R['tail']; place(flick(), end, 2.4, 0); place(pad([261.6, 329.6, 392, 587.3], R['tail'], .12), end + .02)
for c in R['cuts']: tt = np.arange(int((R['each'] - .1) * SR)) / SR; place(np.sin(2 * np.pi * 4500 * tt) * (np.sin(2 * np.pi * 28 * tt) > .2) * ((tt % .9) < .2) * .008, c['at'])
m = max(np.abs(L).max(), np.abs(Rr).max()); st = np.stack([L, Rr], 1)[:int(R['dur'] * SR)] * (.89 / m)
with wave.open(f'{out}/sound.wav', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('reel sound', R['dur'])
