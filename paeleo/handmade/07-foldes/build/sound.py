"""SCION 07 · the sound, synthesized here (numpy). Nothing recorded, nothing sampled.
- voices: formant synthesis (glottal pulse train through three moving resonators); calls loud and raised, the soft voice
  breathy and at least 6 dB lower (measured below, written to cache/levels.json)
- the pen: band-limited scratch whose loudness follows how fast the drawing is changing (mean point speed, px/frame)
- paws on boards at every step the foot solver plants; the door's latch and creak; the light as a slow warm chord
- dusk room tone and a few crickets
Writes cache/scene.wav (32 s) and cache/film.wav (38 s: 3 s title, scene, 3 s end)."""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
rng = np.random.default_rng(11)


def reson(x, f, bw):
    """two-pole resonator with time-varying centre frequency f (array) and bandwidth bw (Hz)."""
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    for n in range(len(x)):
        r = math.exp(-math.pi * bw / SR)
        c = 2 * r * math.cos(2 * math.pi * f[n] / SR)
        v = x[n] + c * y1 - r * r * y2
        y[n] = v; y2 = y1; y1 = v
    return y * (1 - r)


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for n in range(len(x)):
        s = (1 - a) * x[n] + a * s; y[n] = s
    return y


def hp(x, fc):
    return x - onepole_lp(x, fc)


def voice(segs, f0s, breath=0.05):
    """segs: list of (dur, (F1,F2,F3), voiced, noise). f0s: list of (t_frac, Hz). Linear glides between segments."""
    total = sum(s[0] for s in segs)
    n = int(total * SR)
    F = np.zeros((3, n)); V = np.zeros(n); N = np.zeros(n)
    t = 0
    for i, (d, fm, v, nz) in enumerate(segs):
        m = int(d * SR)
        nxt = segs[i + 1] if i + 1 < len(segs) else segs[i]
        u = np.linspace(0, 1, m)
        for j in range(3):
            F[j, t:t + m] = fm[j] + (nxt[1][j] - fm[j]) * np.clip((u - 0.6) / 0.4, 0, 1)
        V[t:t + m] = v; N[t:t + m] = nz
        t += m
    F = F[:, :n]
    V = np.convolve(V, np.ones(480) / 480, 'same'); N = np.convolve(N, np.ones(240) / 240, 'same')
    tf = np.linspace(0, 1, n)
    f0 = np.interp(tf, [a for a, b in f0s], [b for a, b in f0s]) * (1 + 0.012 * np.sin(2 * math.pi * 5.2 * np.arange(n) / SR))
    ph = np.cumsum(f0 / SR)
    src = (ph % 1.0)
    pulse = np.exp(-src * 9.0) - 0.12            # a decaying glottal pulse each period
    exc = pulse * V + rng.normal(0, 1, n) * (N + breath * V) * 0.6
    out = 1.0 * reson(exc, F[0], 90) + 0.6 * reson(exc, F[1], 120) + 0.3 * reson(exc, F[2], 170)
    env = np.minimum(1, np.minimum(np.arange(n) / (0.02 * SR), (n - np.arange(n)) / (0.06 * SR)))
    return out * env


A, E, I, O, U = (650, 1150, 2400), (530, 1840, 2480), (400, 1980, 2550), (580, 880, 2500), (440, 1100, 2300)
SCHWA, M_, N_, L_, R_ = (500, 1500, 2500), (260, 1000, 2200), (280, 1500, 2500), (360, 1000, 2500), (420, 1300, 1650)
AI2 = (420, 2000, 2600)


def come_here(loud=False):
    segs = [(0.05, A, 0, 1.0), (0.2, A, 1, 0), (0.1, M_, 0.6, 0), (0.07, I, 0.1, 0.8), (0.18, I, 1, 0), (0.16, SCHWA, 1, 0)]
    f0 = [(0, 210), (0.3, 250 if not loud else 285), (0.55, 225), (0.7, 265 if not loud else 300), (1, 190)]
    return voice(segs, f0, 0.03)


def its_all_right():
    segs = [(0.1, I, 1, 0), (0.04, I, 0, 0.5), (0.09, (400, 1800, 2600), 0, 0.9), (0.18, O, 1, 0), (0.1, L_, 0.8, 0),
            (0.09, R_, 0.9, 0), (0.24, A, 1, 0), (0.12, AI2, 1, 0), (0.04, AI2, 0, 0.6)]
    f0 = [(0, 175), (0.3, 165), (0.6, 168), (1, 135)]
    return voice(segs, f0, 0.45)


def come_in():
    segs = [(0.05, A, 0, 0.8), (0.18, A, 1, 0), (0.08, M_, 0.6, 0), (0.2, I, 1, 0), (0.16, N_, 0.6, 0)]
    f0 = [(0, 170), (0.4, 160), (1, 132)]
    return voice(segs, f0, 0.45)


def place(buf, x, t, gain):
    i = int(t * SR)
    j = min(len(buf), i + len(x))
    buf[i:j] += x[:j - i] * gain


def db(x):
    return 20 * math.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-9))


def main():
    T = 32.0
    n = int(T * SR)
    amb = np.zeros(n); vox = np.zeros(n); fx = np.zeros(n); pen = np.zeros(n); mus = np.zeros(n)
    # dusk room tone: soft low wind + a few crickets
    w = onepole_lp(rng.normal(0, 1, n), 380)
    amb += w / (np.abs(w).max() + 1e-9) * 0.02
    for k in range(70):
        t0 = rng.uniform(0, T - 0.3)
        m = int(0.045 * SR); tt = np.arange(m) / SR
        ch = np.sin(2 * math.pi * 4400 * tt) * np.sin(math.pi * tt / 0.045) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 55 * tt)))
        for r in range(3):
            place(amb, ch, t0 + r * 0.07, 0.006 * (0.6 + 0.6 * t0 / T))
    # voices (score timeline): calls at 1.0 and 3.4, soft at 7.4, 10.4 and 26.4
    calls = [come_here(False), come_here(True)]
    softs = [its_all_right(), its_all_right(), come_in()]
    for v in calls + softs:
        v /= np.abs(v).max()
    place(vox, calls[0], 1.02, 0.62); place(vox, calls[1], 3.42, 0.72)
    place(vox, softs[0], 7.42, 0.17); place(vox, softs[1], 10.42, 0.16); place(vox, softs[2], 26.42, 0.16)
    # the door: latch click at 6.2, then a slow creak while it swings, then the light: a warm chord swelling in
    click = hp(rng.normal(0, 1, int(0.012 * SR)), 1500) * np.exp(-np.arange(int(0.012 * SR)) / (0.002 * SR))
    place(fx, click, 6.2, 0.25)
    m = int(0.75 * SR); tt = np.arange(m) / SR
    f = 28 + 30 * np.sin(math.pi * tt / 0.75) + 6 * np.sin(2 * math.pi * 3 * tt)
    pulses = (np.diff(np.floor(np.cumsum(f / SR)), prepend=0) > 0).astype(float)
    cr_ = reson(pulses, np.full(m, 900.0), 300) + 0.5 * reson(pulses, np.full(m, 1900.0), 400)
    place(fx, cr_ / (np.abs(cr_).max() + 1e-9) * np.sin(math.pi * tt / 0.75), 6.25, 0.07)
    tt = np.arange(int((T - 6.3) * SR)) / SR
    env = np.clip(tt / 2.5, 0, 1) * (0.8 + 0.2 * np.cos(2 * math.pi * tt / 9.0))
    chord = sum(a * np.sin(2 * math.pi * fq * tt) for fq, a in ((110, 1), (164.8, 0.7), (277.2, 0.45), (329.6, 0.25)))
    place(mus, chord * env / 2.4, 6.3, 0.03)
    # paws on the boards, from the foot solver; a sigh as it lies down (4.6, 24.2); tail thumps while it looks in
    ev = json.load(open(os.path.join(HERE, 'cache', 'events.json')))
    tick_n = int(0.03 * SR)
    for e in ev['paws']:
        x = onepole_lp(rng.normal(0, 1, tick_n), 1800) * np.exp(-np.arange(tick_n) / (0.006 * SR))
        x += 0.5 * np.sin(2 * math.pi * 180 * np.arange(tick_n) / SR) * np.exp(-np.arange(tick_n) / (0.01 * SR))
        place(fx, x, e['t'], 0.12 * (0.8 + 0.4 * rng.random()))
    for t0, g in ((4.62, 0.05), (24.25, 0.05), (28.4, 0.04)):
        m = int(0.7 * SR); tt = np.arange(m) / SR
        x = onepole_lp(rng.normal(0, 1, m), 900) * np.sin(math.pi * tt / 0.7) ** 2
        place(fx, x / (np.abs(x).max() + 1e-9), t0, g)
    for k in range(6):
        m = int(0.05 * SR)
        x = onepole_lp(rng.normal(0, 1, m), 300) * np.exp(-np.arange(m) / (0.012 * SR))
        place(fx, x / (np.abs(x).max() + 1e-9), 26.9 + k * 0.24, 0.05)
    # the pen: loudness follows the morph speed of the drawing (per frame), a dry scratch band
    ms = np.array(ev['morph'])
    env = np.repeat(np.clip(ms / 6.0, 0, 1) ** 0.8, SR // 24)[:n]
    env = np.convolve(env, np.ones(1200) / 1200, 'same')
    sc = hp(onepole_lp(rng.normal(0, 1, len(env)), 5200), 1800)
    grain = (rng.random(len(env)) < 0.02) * rng.normal(0, 3, len(env))
    pen[:len(env)] = (sc + onepole_lp(grain, 4000)) * env * 0.035
    scene = amb + vox + fx + pen + mus
    peak = np.abs(scene).max()
    scene = scene / peak * 0.89
    g = 0.89 / peak
    # levels, measured on the stems as mixed (dBFS RMS over each utterance)
    def seg(x, a, b): return x[int(a * SR):int(b * SR)] * g
    lv = {'call_1': db(seg(vox, 1.02, 1.02 + len(calls[0]) / SR)), 'call_2': db(seg(vox, 3.42, 3.42 + len(calls[1]) / SR)),
          'soft_1': db(seg(vox, 7.42, 7.42 + len(softs[0]) / SR)), 'soft_2': db(seg(vox, 10.42, 10.42 + len(softs[1]) / SR)),
          'soft_come_in': db(seg(vox, 26.42, 26.42 + len(softs[2]) / SR)),
          'room_tone': db(seg(amb, 12, 14)), 'scene_peak_dbfs': 20 * math.log10(0.89)}
    lv['softest_call_minus_loudest_soft_db'] = round(min(lv['call_1'], lv['call_2']) - max(lv['soft_1'], lv['soft_2'], lv['soft_come_in']), 2)
    lv['quietest_soft_minus_room_tone_db'] = round(min(lv['soft_1'], lv['soft_2'], lv['soft_come_in']) - lv['room_tone'], 2)
    lv = {k: round(v, 2) for k, v in lv.items()}
    json.dump(lv, open(os.path.join(HERE, 'cache', 'levels.json'), 'w'), indent=1)
    print(lv)
    full = np.zeros(int(38 * SR))
    tt = np.arange(int(3 * SR)) / SR
    full[:len(tt)] += 0.02 * onepole_lp(rng.normal(0, 1, len(tt)), 300) * np.clip(tt / 1.0, 0, 1)
    full[int(3 * SR):int(3 * SR) + n] = scene
    tail = scene[-int(0.5 * SR):]
    full[int(35 * SR):int(35 * SR) + len(tail)] += tail[::-1] * np.linspace(0.5, 0, len(tail)) * 0
    for name, x in (('scene.wav', scene), ('film.wav', full)):
        with wave.open(os.path.join(HERE, 'cache', name), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
            f.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    main()
