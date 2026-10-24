"""SCION 08 · Sutherland — the sound, synthesised with numpy from the solve and render passes.

A machine room (fans, mains hum, relays), the display's deflection buzz whose pitch follows the
length of the display file, teletype clicks for typed text, the light pen, the person's voice as
loudspeaker tones (hard square calls; soft sine phrases), the door, and the dog: paw contacts
from the solver's own planting events, settling, tail thumps on the boards, a breath.
"""
import json, math, os, pickle, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import world as Wd
SR = 48000
T_TITLE = Wd.TITLE_N / Wd.FPS
DUR = (Wd.TITLE_N + Wd.N_SCENE + Wd.END_N) / Wd.FPS
N = int(DUR * SR)
rng = np.random.RandomState(8)

L = np.zeros(N); R = np.zeros(N)
SEND = np.zeros(N)      # reverb send (mono)

def put(sig, t, gain=1.0, pan=0.0, send=0.0):
    i0 = int(t * SR)
    if i0 >= N or i0 + len(sig) <= 0:
        return
    s = sig * gain
    a, b = max(0, i0), min(N, i0 + len(s))
    seg = s[a - i0:b - i0]
    L[a:b] += seg * math.sqrt(0.5 * (1 - pan)); R[a:b] += seg * math.sqrt(0.5 * (1 + pan))
    SEND[a:b] += seg * send

def onepole(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x); acc = 0.0
    # vectorised via lfilter-like recursion in chunks (numpy has no IIR): use cumulative trick
    out = np.zeros_like(x)
    b = 1 - a
    # simple loop in blocks with numba-free python is slow; use FFT-domain filter instead
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = b / (1 - a * np.exp(-2j * math.pi * f / SR))
    return np.fft.irfft(X * H, len(x))

def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / (1 + ((f - math.sqrt(lo * hi)) / (0.5 * (hi - lo) + 1e-9)) ** 2)
    return np.fft.irfft(X * m, len(x))

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def tone(freqs, durs, kind='sine', vib=0.0, att=0.01, rel=0.05):
    out = []
    ph = 0.0
    for f, d in zip(freqs, durs):
        n = int(d * SR); t = np.arange(n) / SR
        fi = f * (1 + vib * np.sin(2 * math.pi * 5.5 * t))
        p = ph + 2 * math.pi * np.cumsum(fi) / SR
        ph = p[-1]
        if kind == 'square':
            s = np.sign(np.sin(p)) * 0.6 + 0.4 * np.sign(np.sin(2 * p + 0.3)) * 0.3
        elif kind == 'voice':
            s = sum(np.sin(k * p) * (0.8 ** k) / k ** 0.3 for k in range(1, 7))
            s *= 0.5
        else:
            s = np.sin(p)
        e = np.minimum(1, t / att) * np.minimum(1, (d - t) / rel)
        out.append(s * np.clip(e, 0, 1))
    return np.concatenate(out)

# ---------------------------------------------------------------------------- bed
t_all = np.arange(N) / SR
fan = onepole(rng.randn(N), 380) * 0.9 + bandpass(rng.randn(N), 900, 2400) * 0.25
fan *= 0.035 * (1 + 0.15 * np.sin(2 * math.pi * 0.13 * t_all))
hum = sum(a * np.sin(2 * math.pi * f * t_all + k) for k, (f, a) in enumerate(((60, 1), (120, 0.5), (180, 0.35), (240, 0.12), (300, 0.08))))
hum *= 0.012
L += fan + hum; R += fan * 0.96 + hum
# relays / core: sparse clicks in bursts
t = 0.0
while t < DUR:
    t += rng.exponential(0.55)
    for k in range(rng.randint(1, 4)):
        c = bandpass(rng.randn(900), 1500, 5000) * env(900, 0.0003, 0.004)
        put(c, t + k * rng.uniform(0.02, 0.06), 0.06 * rng.uniform(0.4, 1), rng.uniform(-0.7, 0.7), 0.1)

# ---------------------------------------------------------------------------- data from the passes
S = pickle.load(open(os.path.join(HERE, '_cache', 'solve.pkl'), 'rb'))
RM = json.load(open(os.path.join(HERE, '_cache', 'render_meas.json')))
counts = np.array(RM['spot_counts'], float)
scene = S['scene']

# display deflection buzz: pitch follows the display file's length (longer file, slower refresh)
fr_idx = np.minimum((t_all * Wd.FPS).astype(int), len(counts) - 1)
spots = np.maximum(counts[fr_idx], 2000)
f_buzz = 150000.0 / spots * 14.0
ph = 2 * math.pi * np.cumsum(f_buzz) / SR
buzz = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * 0.010
L += buzz; R += buzz

def sx_pan(x):
    return float(np.clip((x - 1.45) / 4.0, -0.8, 0.8))

# ---------------------------------------------------------------------------- typing
def click(g=0.05, pan=0.0):
    c = bandpass(rng.randn(700), 2000, 7000) * env(700, 0.0002, 0.0025)
    c2 = onepole(rng.randn(1400), 300) * env(1400, 0.0005, 0.006)
    return (c + c2 * 0.8) * g

title = 'PAE-02 · SCION 08 · IVAN SUTHERLAND'
for k in range(len(title)):
    put(click(0.05), (k / len(title)) * 26 / Wd.FPS, 1.0, -0.2)
for t0, s in Wd.PROMPTS:
    for k in range(len(s)):
        put(click(0.04), T_TITLE + t0 + k / 32.0, 1.0, -0.5)
for k in range(60):
    put(click(0.03), T_TITLE + 32.0 + 6 / 24 + k * 0.035, 1.0, 0.0)

# ---------------------------------------------------------------------------- pen
prev = None
for fr in scene:
    m = fr['mode']
    if m != prev:
        tt = T_TITLE + fr['t']
        if m == 'drag':
            put(click(0.10), tt, 1, -0.3, 0.2)
            put(tone([1760, 2349], [0.04, 0.06], 'square', att=0.002, rel=0.01), tt + 0.01, 0.025, -0.3)
        elif m == 'point':
            put(tone([2637], [0.05], 'square', att=0.002, rel=0.02), tt, 0.02, -0.3)
        elif prev == 'drag':
            put(click(0.07), tt, 1, -0.3)
            put(tone([2349, 1760], [0.04, 0.06], 'square', att=0.002, rel=0.01), tt, 0.02, -0.3)
    prev = m
# drag hiss proportional to pen speed
pen = np.array([fr['pen'] for fr in scene]); spd = np.r_[0, np.linalg.norm(np.diff(pen, axis=0), axis=1) * Wd.FPS]
drag = np.array([1.0 if fr['mode'] == 'drag' else 0.3 for fr in scene])
a = np.zeros(N)
idx = ((t_all - T_TITLE) * Wd.FPS).astype(int)
ok = (idx >= 0) & (idx < len(scene))
a[ok] = np.clip(spd[idx[ok]] / 3.0, 0, 1) * drag[idx[ok]]
a = onepole(a, 20)
hiss = bandpass(rng.randn(N), 3000, 9000) * a * 0.05
L += hiss * 0.8; R += hiss * 0.5

# ---------------------------------------------------------------------------- voice
def call_phrase():
    return tone([330, 494, 440], [0.16, 0.05, 0.30], 'square', vib=0.012, att=0.004, rel=0.04)
def soft_phrase(notes, durs):
    return tone(notes, durs, 'voice', vib=0.006, att=0.09, rel=0.18)
for tt in (1.0, 1.65, 3.4, 4.0):
    put(call_phrase(), T_TITLE + tt, 0.11, -0.35, 0.25)
put(soft_phrase([220, 208, 185, 165], [0.18, 0.2, 0.32, 0.6]), T_TITLE + 7.45, 0.16, -0.4, 0.6)     # it's all right
put(soft_phrase([220, 196, 175], [0.2, 0.3, 0.7]), T_TITLE + 10.45, 0.15, -0.4, 0.6)
put(soft_phrase([196, 175], [0.3, 0.8]), T_TITLE + 26.45, 0.15, -0.4, 0.6)                         # come in

# ---------------------------------------------------------------------------- door
dt = T_TITLE + 6.2
n = int(0.45 * SR); tt = np.arange(n) / SR
creak_f = 260 + 380 * tt / 0.45 + 40 * np.sin(2 * math.pi * 31 * tt)
p = 2 * math.pi * np.cumsum(creak_f) / SR
creak = (np.sign(np.sin(p)) * 0.5 + np.sin(3 * p) * 0.3) * (0.6 + 0.4 * rng.rand(n)) * np.sin(math.pi * tt / 0.45)
put(bandpass(creak, 300, 2500), dt, 0.05, -0.1, 0.3)
put(click(0.2), dt - 0.02, 1, -0.1, 0.3)
# the light: a warm drone that rises with the open door and stays
angles = np.array([fr['door_angle'] for fr in scene])
openk = np.clip((angles - Wd.Door.AJAR) / (Wd.Door.OPEN - Wd.Door.AJAR), 0, 1)
lk = np.zeros(N); lk[ok] = openk[idx[ok]]
lk[(t_all - T_TITLE) >= Wd.SF[-1]['t']] = openk[-1]
lk = onepole(lk, 2) * np.clip(1 - (t_all - (DUR - 1.5)) / 1.5, 0, 1)
drone = (np.sin(2 * math.pi * 110 * t_all) * 0.5 + np.sin(2 * math.pi * 165 * t_all) * 0.3 + np.sin(2 * math.pi * 220.7 * t_all) * 0.15)
drone *= lk * 0.022 * (1 + 0.2 * np.sin(2 * math.pi * 0.21 * t_all))
L += drone; R += drone

# ---------------------------------------------------------------------------- the dog and the person's feet
def paw(g):
    th = onepole(rng.randn(2400), 260) * env(2400, 0.001, 0.018)
    ck = bandpass(rng.randn(300), 3000, 8000) * env(300, 0.0001, 0.0015)
    return th * g + ck * g * 0.5
for ev in S['events']:
    tt = T_TITLE + ev['t']
    if ev['kind'] == 'paw':
        put(paw(0.22), tt, 1, sx_pan(ev['x']), 0.08)
    elif ev['kind'] == 'step':
        th = onepole(rng.randn(5000), 180) * env(5000, 0.002, 0.04)
        put(th, tt, 0.35, sx_pan(ev['x']), 0.1)
SF = Wd.SF
lie = np.array([f['dog']['act']['lie'] for f in SF])
xs = np.array([f['dog']['x'] for f in SF])
for i in range(1, len(SF)):
    if lie[i - 1] < 0.5 <= lie[i]:                    # settling down
        n = int(0.7 * SR)
        s = onepole(rng.randn(n), 220) * np.sin(math.pi * np.arange(n) / n) ** 2
        put(s, T_TITLE + SF[i]['t'] - 0.25, 0.25, sx_pan(xs[i]), 0.15)
        put(onepole(rng.randn(6000), 120) * env(6000, 0.003, 0.05), T_TITLE + SF[i]['t'] + 0.15, 0.4, sx_pan(xs[i]))
    if lie[i - 1] > 0.5 >= lie[i]:                    # getting up
        n = int(0.4 * SR)
        s = onepole(rng.randn(n), 400) * np.sin(math.pi * np.arange(n) / n)
        put(s, T_TITLE + SF[i]['t'] - 0.1, 0.12, sx_pan(xs[i]), 0.1)
# tail thumps on the boards while lying and wagging
prevs = 0
for i, f in enumerate(SF):
    a = f['dog']['act']
    s = math.sin(2 * math.pi * 2.6 * f['t'])
    if a['lie'] > 0.8 and a['wag'] > 0.45 and prevs > -0.6 >= s:
        put(onepole(rng.randn(3000), 150) * env(3000, 0.001, 0.025), T_TITLE + f['t'], 0.35 * a['wag'], 0.3)
    prevs = s
# a breath when the chin goes down on the paws for good
for i in range(1, len(SF)):
    r0, r1 = SF[i - 1]['dog']['act']['rest'], SF[i]['dog']['act']['rest']
    if r0 < 0.6 <= r1:
        n = int(1.1 * SR); tt = np.arange(n) / SR
        br = bandpass(rng.randn(n), 400, 1800) * np.sin(math.pi * tt / 1.1) ** 1.5 * np.exp(-tt * 0.8)
        put(br, T_TITLE + SF[i]['t'], 0.09, 0.2, 0.2)

# ---------------------------------------------------------------------------- solver pips
for fr in scene:
    it = fr['pres']['iters'] + fr['dres']['iters']
    g = np.clip((it - 150) / 150, 0, 1)
    if g > 0:
        put(tone([3520], [0.012], 'square', att=0.001, rel=0.004), T_TITLE + fr['t'], 0.012 * g, 0.6)

# ---------------------------------------------------------------------------- reverb (Schroeder) on the send
def comb(x, d, g):
    y = x.copy()
    for k in range(d, len(y), d):
        y[k:k + d] += g * y[k - d:k][: len(y[k:k + d])]
    return y
def allpass(x, d, g):
    y = np.zeros_like(x)
    buf = np.zeros(len(x) + d)
    # direct form via blocks
    xb = np.concatenate([np.zeros(d), x])
    yb = np.zeros(len(x) + d)
    for k in range(d, len(xb), d):
        seg = slice(k, min(k + d, len(xb)))
        n = seg.stop - seg.start
        yb[seg] = -g * xb[seg] + xb[k - d:k - d + n] + g * yb[k - d:k - d + n]
    return yb[d:]
rv = sum(comb(SEND, d, 0.78) for d in (1557, 1617, 1491, 1422)) * 0.25
rv = allpass(allpass(rv, 225, 0.5), 556, 0.5)
rv = onepole(rv, 3500)
L += rv * 0.35; R += np.roll(rv, 240) * 0.35

# ---------------------------------------------------------------------------- master
fade = np.clip(t_all / 0.4, 0, 1) * np.clip((DUR - t_all) / 0.8, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = np.tanh(st * 1.6) / 1.6
st /= np.abs(st).max() / 0.89
wav = os.path.join(HERE, '_cache', 'sound.wav')
with wave.open(wav, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())
print('sound', wav, DUR)
