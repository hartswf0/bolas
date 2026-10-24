"""SCION 53 · sound. Everything synthesized with numpy, no recordings.

The projector: every time the dog's archive frame changes, a tick (higher when the footage runs backward, none while the
cut-out is a composed fold). So the operation is audible: a re-timed film makes a different clatter than a held one.
The person: formant-synthesized voice tones with the contour of the words (commanding: high, fast, falling; soft: low,
breathy, slow). They are not speech and do not pretend to be. The door: a creak, a latch, then the warm room tone of inside.
The dog: paw taps on each walking frame, a settling breath when it lies down, its collar when it lifts its head.
Writes ../build/audio.wav (48 kHz stereo, 38 s).
"""
import json, os, math, wave
import numpy as np
from lib import load_json, SRC, HERE

SR = 48000
DUR = 38.0
OFF = 3.0
rng = np.random.default_rng(5353)
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)

def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i] * gain
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    L[i:i + len(s)] += s * l; R[i:i + len(s)] += s * r

def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def lp_fast(x, fc):
    # cascaded moving averages ~ low pass, vectorized
    k = max(1, int(SR / fc / 2))
    c = np.cumsum(np.concatenate([[0], x])); y = (c[k:] - c[:-k]) / k
    return np.concatenate([y, np.zeros(len(x) - len(y))])

def resonator(x, f, bw):
    """two-pole resonator with per-sample f (array) — a formant."""
    y = np.zeros_like(x); y1 = y2 = 0.0
    fs = np.broadcast_to(f, x.shape)
    r = math.exp(-math.pi * bw / SR)
    for i in range(len(x)):
        c = 2 * r * math.cos(2 * math.pi * fs[i] / SR)
        v = x[i] + c * y1 - r * r * y2
        y2 = y1; y1 = v; y[i] = v
    return y * (1 - r)

def env(n, a, d, sus=1.0):
    e = np.ones(n) * sus
    na = max(1, int(a * SR)); nd = max(1, int(d * SR))
    e[:na] = np.linspace(0, sus, na)
    e[-nd:] *= np.linspace(1, 0, nd)
    return e

def voice(segments, f0s, breath=0.1, gain=1.0):
    """segments: list of (dur, (F1,F2,F3) start, (F1,F2,F3) end, amp, noise) ; f0s: (start,end) Hz overall contour"""
    total = sum(s[0] for s in segments); n = int(total * SR)
    f0 = np.linspace(f0s[0], f0s[1], n) * (1 + 0.012 * np.sin(np.arange(n) / SR * 2 * math.pi * 5.2))
    ph = np.cumsum(f0 / SR) % 1.0
    src = (1 - 2 * ph) * 0.6 + (ph < 0.08) * 0.8              # buzzy glottal-ish pulse
    F = np.zeros((n, 3)); A = np.zeros(n); NZ = np.zeros(n); i = 0
    for dur, fa, fb, amp, nz in segments:
        m = int(dur * SR)
        for k in range(3):
            F[i:i + m, k] = np.linspace(fa[k], fb[k], m)
        A[i:i + m] = amp; NZ[i:i + m] = nz; i += m
    A = lp_fast(A, 30); NZ = lp_fast(NZ, 30)
    noise = rng.standard_normal(n)
    exc = src * A * (1 - NZ) + noise * (NZ * 0.5 + breath * A)
    out = resonator(exc, F[:, 0], 90) * 1.0 + resonator(exc, F[:, 1], 120) * 0.6 + resonator(exc, F[:, 2], 160) * 0.3
    out = out / (np.abs(out).max() + 1e-9)
    return out * env(n, 0.01, 0.06) * gain

UH = (640, 1190, 2390); IH = (390, 1990, 2550); ER = (500, 1500, 2500); M = (250, 1100, 2300); AO = (570, 840, 2410)
EL = (360, 1300, 2600); AI0 = (750, 1300, 2500); AI1 = (420, 2000, 2600); S_ = (4000, 6000, 7500); IN = (300, 1900, 2600)

def come_here(gain, f0=(215, 165)):
    return voice([(0.05, UH, UH, 0.0, 1.0), (0.13, UH, UH, 1.0, 0), (0.06, M, M, 0.5, 0),
                  (0.06, IH, IH, 0.2, 0.8), (0.24, IH, ER, 1.0, 0)], f0, breath=0.05, gain=gain)

def its_all_right(gain):
    return voice([(0.10, IH, IH, 0.6, 0), (0.07, S_, S_, 0.0, 1.0), (0.20, AO, EL, 0.9, 0), (0.08, EL, EL, 0.6, 0),
                  (0.32, AI0, AI1, 0.9, 0), (0.05, S_, S_, 0.0, 0.6)], (150, 118), breath=0.35, gain=gain)

def come_in(gain):
    return voice([(0.05, UH, UH, 0.0, 0.8), (0.14, UH, UH, 0.8, 0), (0.06, M, M, 0.5, 0), (0.24, IN, IN, 0.8, 0), (0.08, M, M, 0.4, 0)],
                 (150, 122), breath=0.35, gain=gain)

def click(freq=3000, dur=0.006):
    n = int(dur * SR); x = rng.standard_normal(n) * np.exp(-np.linspace(0, 8, n))
    t = np.arange(n) / SR
    return x * 0.5 + np.sin(2 * math.pi * freq * t) * np.exp(-np.linspace(0, 10, n))

def thump(dur=0.18, f=70):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * math.pi * f * t * (1 - 0.4 * t / dur)) * np.exp(-t * 22) + lp_fast(rng.standard_normal(n), 600) * np.exp(-t * 30) * 0.6

def breath(dur=0.9, lo=300, hi=1400):
    n = int(dur * SR)
    x = lp_fast(rng.standard_normal(n), hi) - lp_fast(rng.standard_normal(n), lo) * 0.3
    e = np.concatenate([np.linspace(0, 1, n // 4), np.linspace(1, 0, n - n // 4) ** 1.5])
    return x * e

def jingle(dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f, d in ((3120, 9), (4470, 11), (5230, 14), (6810, 16)):
        for k in range(3):
            o = int(rng.integers(0, int(0.12 * SR)))
            y[o:] += np.sin(2 * math.pi * f * (1 + 0.01 * k) * t[:n - o]) * np.exp(-t[:n - o] * d) * 0.25
    return y

def creak(dur=0.55):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 90 + 160 * (t / dur) ** 0.7 + 25 * np.sin(2 * math.pi * 7 * t)
    ph = np.cumsum(f / SR)
    saw = 2 * (ph % 1) - 1
    y = resonator(saw * 0.4, np.full(n, 900.0), 300) + resonator(saw * 0.3, np.full(n, 1900.0), 400)
    return y / (np.abs(y).max() + 1e-9) * env(n, 0.05, 0.15)

def rustle(dur=0.4):
    n = int(dur * SR); x = rng.standard_normal(n)
    x = x - lp_fast(x, 1500)
    return x * env(n, 0.05, 0.2) * (0.6 + 0.4 * np.sin(np.linspace(0, 18, n)))

score = load_json(SRC, 'threshold-score.json')
edl = load_json(HERE, 'edl.json')
FR = score['frames']

# --- the projector: motor hum and sprocket from the title, ticks per archive-frame change in the scene
t_all = np.arange(N) / SR
hum = (np.sin(2 * math.pi * 48 * t_all) * 0.5 + np.sin(2 * math.pi * 96 * t_all) * 0.25) * 0.010
spin = np.clip(t_all / 1.5, 0, 1) * np.clip((DUR - t_all) / 1.5, 0, 1)
L += hum * spin; R += hum * spin
for k in range(int(3.0 * 24)):                      # title: the gate runs
    add(click(2400, 0.004), k / 24, 0.012 * min(1, k / 24))
for k in range(int(3.0 * 24)):                      # end card
    add(click(2400, 0.004), DUR - 3.0 + k / 24, 0.012 * max(0, 1 - k / 72))

# --- dusk: wind and crickets, under everything in the scene
wind = lp_fast(rng.standard_normal(N), 180) * 0.6
wind *= (0.6 + 0.4 * np.sin(2 * math.pi * 0.07 * t_all + 1)) * np.clip((t_all - OFF + 0.5) / 1.5, 0, 1) * np.clip((DUR - 3 - t_all) / 1.0, 0, 1)
L += wind * 0.11; R += wind * 0.10
for k in range(140):
    tt = OFF + rng.random() * 31.5
    n = int(0.09 * SR); tc_ = np.arange(n) / SR
    chirp = np.sin(2 * math.pi * 4300 * tc_) * (np.sin(2 * math.pi * 55 * tc_) > 0.2) * env(n, 0.005, 0.02)
    add(chirp, tt, 0.006, pan=rng.random() * 1.6 - 0.8)

# --- ticks: the operation made audible
prev = None
for e in edl:
    d = e['dog']; t = OFF + e['t']
    key = (d['f'], d['mirror'])
    if prev is not None and key != prev and d['fold'] is None:
        rev = 'REVERSE' in d['op']
        add(click(5200 if rev else 2600), t, 0.020, pan=0.55)
    prev = key

# --- paws: on each walking frame change during the retreat and the approach
prev = None; side = 1
for e in edl:
    n = e['i']; t = OFF + e['t']; st = FR[n]['dog']['state']; mv = FR[n]['dog']['act']['moving'] or abs(FR[n]['dog']['v']) > 0.05
    f = e['dog']['f']
    if st in ('retreat', 'approach') and mv and prev is not None and f != prev and f % 2 == 0:
        side = -side
        x = FR[n]['dog']['x']
        add(thump(0.07, 140) * 0.6, t, 0.05, pan=float(np.clip((x - 2) / 3, -1, 1)) * 0.8)
        add(click(1800, 0.01) * 0.2, t, 0.05, pan=float(np.clip((x - 2) / 3, -1, 1)) * 0.8 + 0.05 * side)
    prev = f

def xpan(t):
    n = min(len(FR) - 1, int(t * 24)); return float(np.clip((FR[n]['dog']['x'] - 2) / 3, -1, 1) * 0.8)

# --- the person (left of frame)
add(come_here(1.0), OFF + 1.02, 0.25, pan=-0.45)
add(come_here(1.0, (235, 175)), OFF + 3.42, 0.30, pan=-0.45)
add(rustle(0.5), OFF + 3.45, 0.06, pan=-0.4)
add(rustle(0.7), OFF + 5.42, 0.05, pan=-0.6)
add(thump(0.25, 60), OFF + 5.95, 0.22, pan=-0.7)
add(its_all_right(1.0), OFF + 7.42, 0.17, pan=-0.6)
add(its_all_right(1.0), OFF + 10.42, 0.15, pan=-0.6)
add(come_in(1.0), OFF + 26.42, 0.15, pan=-0.6)

# --- the door: latch, creak, then the warm tone of inside
add(click(1200, 0.02), OFF + 6.18, 0.12, pan=-0.2)
add(creak(0.6), OFF + 6.2, 0.10, pan=-0.2)
warm = np.zeros(N)
for f, a in ((110, 1.0), (164.8, 0.6), (220.4, 0.45), (277.2, 0.25)):
    warm += np.sin(2 * math.pi * f * t_all + rng.random() * 6) * a
warm *= np.clip((t_all - OFF - 6.3) / 1.8, 0, 1) * np.clip((DUR - 3 - t_all) / 1.2, 0, 1) * (0.8 + 0.2 * np.sin(2 * math.pi * 0.11 * t_all))
L += warm * 0.012; R += warm * 0.008

# --- the dog
add(breath(0.4, 400, 2200), OFF + 1.0, 0.05, pan=xpan(1.0))               # startles at the call
add(rustle(0.3), OFF + 3.45, 0.04, pan=xpan(3.5))                          # turns its back
add(breath(0.9), OFF + 4.6, 0.10, pan=xpan(4.6)); add(thump(0.2, 55), OFF + 4.75, 0.10, pan=xpan(4.7))   # lies down, back turned
add(jingle(0.5), OFF + 7.46, 0.05, pan=xpan(7.5))                           # lifts its head: turns back to look
add(jingle(0.4), OFF + 8.2, 0.035, pan=xpan(8.2))
add(breath(0.6, 300, 1000), OFF + 14.7, 0.05, pan=xpan(14.7))
add(breath(1.1), OFF + 23.85, 0.12, pan=xpan(24)); add(thump(0.25, 50), OFF + 24.3, 0.12, pan=xpan(24.3))
add(jingle(0.5), OFF + 26.6, 0.045, pan=xpan(26.6))                         # looks in
add(breath(1.6, 250, 900), OFF + 28.4, 0.12, pan=xpan(28.4))               # settles and stays

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.6) / 1.6
peak = np.abs(mix).max()
mix = mix / peak * 0.85
out = os.path.join(HERE, 'audio.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out, 'peak', round(float(peak), 3))
