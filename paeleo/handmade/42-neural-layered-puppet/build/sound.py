"""SCION 42 · sound, all synthesized here (numpy): dusk crickets and room tone, a formant-synthesized voice (calls at
full voice, the soft lines at least 10 dB under them), the door latch and hinge, the light's warm hum, the person's
steps and the stool, and the dog's pads and claws keyed to the score's walk phase, its body settling on the boards.
Writes build/cache/sound.wav (48 kHz stereo, 38.0 s: 3 s title + 32 s scene + 3 s end card) and data/sound_levels.json.
usage: python3 sound.py <perform.json>
"""
import json, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SR = 48000
TOTAL = 38.0
OFF = 3.0     # scene starts here
R = np.random.default_rng(42)

VOW = {'a': (700, 1220, 2600), 'A': (640, 1190, 2390), 'e': (530, 1840, 2480), 'i': (300, 2300, 3000), 'I': (400, 2000, 2550),
       'o': (500, 900, 2400), 'u': (330, 1000, 2300), '@': (500, 1500, 2500), 'O': (580, 880, 2400),
       'm': (260, 1000, 2200), 'n': (280, 1500, 2500), 'l': (350, 1100, 2600), 'r': (420, 1300, 1700)}


def resonator(x, f, bw):
    """time-varying 2-pole resonator; f, bw arrays (Hz)"""
    y = np.zeros_like(x)
    r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
    a1 = 2 * r * np.cos(th); a2 = -r * r; g = (1 - r)
    y1 = y2 = 0.0
    for n in range(len(x)):
        v = g[n] * x[n] + a1[n] * y1 + a2[n] * y2
        y[n] = v; y2 = y1; y1 = v
    return y


def voice(spec, f0, f0_end, breath=0.1, gain=1.0):
    """spec: list of (phone, seconds). voiced phones in VOW, noise phones: k t s h (silence ' ')"""
    n = int(sum(d for _, d in spec) * SR)
    F = np.zeros((n, 3)); voiced = np.zeros(n); noise = np.zeros(n); pos = 0
    for ph, d in spec:
        m = int(d * SR)
        if ph in VOW:
            F[pos:pos + m] = VOW[ph]; voiced[pos:pos + m] = 1 if ph not in 'mnlr' else 0.6
        else:
            F[pos:pos + m] = (2500, 3000, 3600) if ph in 'st' else (1800, 2400, 3200) if ph == 'k' else (700, 1300, 2500)
            noise[pos:pos + m] = {'k': 0.8, 't': 0.8, 's': 0.5, 'h': 0.35, ' ': 0}.get(ph, 0.3)
            if ph in 'kt':
                env = np.exp(-np.arange(m) / (0.012 * SR)); noise[pos:pos + m] *= env
        pos += m
    # smooth formant tracks and voicing (coarticulation)
    k = int(0.03 * SR)
    ker = np.hanning(k); ker /= ker.sum()
    for j in range(3): F[:, j] = np.convolve(np.pad(F[:, j], (k, k), mode='edge'), ker, 'same')[k:-k]
    voiced = np.convolve(voiced, ker, 'same'); noise = np.convolve(noise, np.hanning(64) / 32, 'same')
    t = np.arange(n) / SR
    f0c = f0 + (f0_end - f0) * (t / t[-1]) + 4 * np.sin(2 * np.pi * 5 * t) + R.normal(0, 1, n).cumsum() * 0.002
    ph = 2 * np.pi * np.cumsum(f0c) / SR
    src = np.zeros(n)
    for h in range(1, 30):
        amp = 1.0 / h ** 1.1 * (h * f0 < 5000)
        src += amp * np.sin(h * ph)
    src = src * voiced * (1 - breath) + R.normal(0, 1, n) * (voiced * breath * 0.8 + noise)
    out = np.zeros(n)
    for j, bw in enumerate((80, 110, 160)):
        out += resonator(src, F[:, j], np.full(n, bw)) * (1.0, 0.6, 0.35)[j]
    env = np.minimum(1, np.minimum(t / 0.02, (t[-1] - t) / 0.06))
    out *= env
    return out / (np.abs(out).max() + 1e-9) * gain


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = a * s + (1 - a) * x[i]; y[i] = s
    return y


def lp_fast(x, fc, passes=2):
    # cheap low-pass: repeated moving average
    k = max(1, int(SR / fc / 2))
    for _ in range(passes): x = np.convolve(x, np.ones(k) / k, 'same')
    return x


def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def main(perf_path):
    P = json.load(open(perf_path))
    fr = P['frames']
    n = int(TOTAL * SR)
    L = np.zeros(n); Rr = np.zeros(n)
    def add(sig, t0, pan=0.0, g=1.0):
        i = int((t0) * SR)
        if i >= n: return
        s = sig[:n - i] * g
        L[i:i + len(s)] += s * np.sqrt(0.5 * (1 - pan)); Rr[i:i + len(s)] += s * np.sqrt(0.5 * (1 + pan))
    levels = {}
    # room tone + dusk air, whole film; crickets in the scene
    tone = lp_fast(R.normal(0, 1, n), 300) * 0.02
    L += tone; Rr += lp_fast(R.normal(0, 1, n), 300) * 0.02
    t = np.arange(n) / SR
    cr = np.zeros(n)
    tt = 0.3
    while tt < TOTAL - 0.5:
        m = int(0.18 * SR); u = np.arange(m) / SR
        chirp = np.sin(2 * np.pi * (4300 + R.normal(0, 60)) * u) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * u)) * np.hanning(m)
        i = int(tt * SR); cr[i:i + m] += chirp[:max(0, min(m, n - i))] * R.uniform(0.4, 1)
        tt += R.uniform(0.35, 0.9)
    fade = np.clip(np.minimum(t / 2.0, (TOTAL - t) / 1.5), 0, 1)
    L += cr * 0.010 * fade; Rr += np.roll(cr, 900) * 0.012 * fade
    # voice
    calls = []
    v1 = voice([('k', .06), ('A', .16), ('m', .10), (' ', .05), ('h', .07), ('I', .16), ('@', .2)], 175, 150, 0.08, 0.32)
    v2 = voice([('k', .05), ('A', .14), ('m', .09), (' ', .04), ('h', .06), ('i', .22), ('@', .18)], 205, 160, 0.06, 0.40)
    calls += [(v1, OFF + 1.0), (v2, OFF + 3.42)]
    soft1 = voice([('I', .07), ('t', .04), ('s', .08), ('O', .18), ('l', .08), (' ', .02), ('r', .08), ('a', .2), ('I', .14), ('t', .05)], 150, 125, 0.45, 0.075)
    soft2 = voice([('O', .2), ('l', .08), ('r', .1), ('a', .22), ('I', .14), ('t', .05)], 145, 120, 0.5, 0.07)
    soft3 = voice([('k', .05), ('A', .16), ('m', .1), (' ', .05), ('I', .2), ('n', .16)], 150, 128, 0.45, 0.075)
    softs = [(soft1, OFF + 7.45), (soft2, OFF + 10.45), (soft3, OFF + 26.4)]
    for s, t0 in calls: add(s, t0, -0.35)
    for s, t0 in softs: add(s, t0, -0.45)
    levels['call_rms_dbfs'] = [round(db(s[np.abs(s) > 0.02 * np.abs(s).max()]), 1) for s, _ in calls]
    levels['soft_rms_dbfs'] = [round(db(s[np.abs(s) > 0.02 * np.abs(s).max()]), 1) for s, _ in softs]
    levels['room_tone_rms_dbfs'] = round(db(tone), 1)
    # door: latch click + hinge creak at 6.2, then the warm hum of the light
    m = int(0.9 * SR); u = np.arange(m) / SR
    creak = np.sin(2 * np.pi * (330 + 140 * np.sin(2 * np.pi * 1.3 * u)) * u + 3 * np.sin(2 * np.pi * 23 * u)) * np.exp(-u / 0.5) * 0.05
    creak *= (1 + 0.6 * np.sign(np.sin(2 * np.pi * 37 * u)))
    click = R.normal(0, 1, 1200) * np.exp(-np.arange(1200) / 150.) * 0.12
    add(click, OFF + 6.15, -0.2); add(creak, OFF + 6.2, -0.2)
    hum_t = np.arange(int(26 * SR)) / SR
    hum = (np.sin(2 * np.pi * 110 * hum_t) + 0.5 * np.sin(2 * np.pi * 220 * hum_t) + 0.25 * np.sin(2 * np.pi * 330.5 * hum_t))
    hum *= np.clip(hum_t / 1.5, 0, 1) * 0.0045
    add(hum, OFF + 6.3, -0.3)
    # person: steps aside 5.4-6.2, stool creak at sit
    for k, t0 in enumerate(np.arange(5.4, 6.3, 0.3)):
        st = lp_fast(R.normal(0, 1, 3000), 400) * np.exp(-np.arange(3000) / 500.) * 0.25
        add(st, OFF + t0, -0.4)
    m = int(0.35 * SR); u = np.arange(m) / SR
    add(np.sin(2 * np.pi * 180 * u + 4 * np.sin(2 * np.pi * 9 * u)) * np.exp(-u / 0.12) * 0.03, OFF + 6.3, -0.4)
    # dog: pads and claws at each half-cycle of the walk phase (4 feet => 4 contacts per cycle)
    prev = None
    for f in fr:
        if f['moving'] < 0.3: prev = None; continue
        ph = f['walk_phase'] * 2 / np.pi
        if prev is not None and np.floor(ph) != np.floor(prev):
            m = 2400
            pad = lp_fast(R.normal(0, 1, m), 600) * np.exp(-np.arange(m) / 300.) * 0.22
            claw = R.normal(0, 1, 400) * np.exp(-np.arange(400) / 40.) * 0.025
            pan = float(np.clip((f['x_screen'] - 640) / 640, -1, 1))
            add(pad, OFF + f['t'], pan); add(claw, OFF + f['t'] + 0.004, pan)
        prev = ph
    # dog body settles on the boards (both lie-downs), and exhales when it puts its chin down
    for t0 in P.get('events', {}).get('settle', []):
        m = int(0.4 * SR); u = np.arange(m) / SR
        th = lp_fast(R.normal(0, 1, m), 150) * np.exp(-u / 0.09) * 0.5
        add(th, OFF + t0, 0.2)
    for t0 in P.get('events', {}).get('sigh', []):
        m = int(0.9 * SR); u = np.arange(m) / SR
        s = lp_fast(R.normal(0, 1, m), 900) * np.sin(np.pi * u / u[-1]) ** 2 * 0.05
        add(s, OFF + t0, 0.2)
    # title / end: a single low tone under the cards
    for t0 in (0.3, 35.3):
        m = int(2.4 * SR); u = np.arange(m) / SR
        add((np.sin(2 * np.pi * 98 * u) + 0.3 * np.sin(2 * np.pi * 147 * u)) * np.sin(np.pi * u / u[-1]) * 0.03, t0)
    mix = np.stack([L, Rr], 1)
    peak = np.abs(mix).max(); mix = mix / max(peak, 1e-9) * 0.89
    levels['note'] = 'rms over the voiced part of each phrase, before the final mix normalisation (same gain for all)'
    levels['soft_minus_call_db'] = round(max(levels['soft_rms_dbfs']) - min(levels['call_rms_dbfs']), 1)
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    with wave.open(os.path.join(HERE, 'cache', 'sound.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype('<i2').tobytes())
    json.dump(levels, open(os.path.join(ROOT, 'data', 'sound_levels.json'), 'w'), indent=1)
    print(levels)


if __name__ == '__main__':
    main(sys.argv[1])
