"""SCION 23 · sound, all synthesized here: a formant voice for the person (calls loud, the soft voice quiet and
breathy), dusk crickets and room tone, the dog's paw falls fired by the runtime's foot planner, and the clip
events (whimper, thump, jingle, sigh), the door, the room's warmth once it opens. Writes cache/film.wav (38 s)
and proof/levels.json (measured)."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SR = 44100
rng = np.random.default_rng(5)
OFF = 3.0  # the scene starts after the 3 s title


def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
    return e


V = dict(a=(750, 1250, 2500), u=(680, 1200, 2600), i=(320, 2250, 2950), I=(420, 1900, 2550), e=(500, 1550, 2500),
         o=(560, 850, 2400), m=(260, 1100, 2400), n=(260, 1500, 2500), l=(360, 1150, 2700), r=(430, 1250, 1650))


def resonate(src, F, bw):
    """time-varying 2-pole resonator, F and bw per sample"""
    y = np.zeros_like(src); y1 = y2 = 0.0
    r = np.exp(-math.pi * bw / SR); c = 2 * r * np.cos(2 * math.pi * F / SR); d = -r * r
    g = 1 - r
    for k in range(len(src)):
        v = g[k] * src[k] + c[k] * y1 + d[k] * y2
        y[k] = v; y2 = y1; y1 = v
    return y


def say(phones, f0s, breath=0.05, gain=1.0):
    """phones: list of (symbol, dur). Vowels/sonorants voiced; 'k','t' bursts; 's','h' noise; '_' silence."""
    segs = []; total = sum(d for _, d in phones); n = int(total * SR)
    F = np.zeros((3, n)); amp = np.zeros(n); noise_amp = np.zeros(n); nband = np.zeros((2, n))
    pos = 0; last = V['e']
    for ph, d in phones:
        m = int(d * SR); sl = slice(pos, pos + m)
        if ph in V:
            tgt = V[ph]
            for j in range(3):
                F[j, sl] = np.linspace(last[j], tgt[j], m) if m else 0
                F[j, sl] = tgt[j] + (np.asarray(last[j]) - tgt[j]) * np.exp(-np.arange(m) / (0.025 * SR))
            amp[sl] = 0.45 if ph in 'mnlr' else 1.0
            last = tgt
        else:
            for j in range(3): F[j, sl] = last[j]
            if ph == 's': noise_amp[sl] = 0.35; nband[0, sl] = 4500; nband[1, sl] = 9000
            if ph == 'h': noise_amp[sl] = 0.5; nband[0, sl] = 400; nband[1, sl] = 4000
            if ph in 'kt':
                b = int(0.025 * SR); noise_amp[pos + m - b:pos + m] = 0.6
                nband[0, sl] = 1800 if ph == 'k' else 3500; nband[1, sl] = 4000 if ph == 'k' else 7000
        pos += m
    t = np.arange(n) / SR
    f0 = np.interp(t, np.linspace(0, total, len(f0s)), f0s) * (1 + 0.01 * np.sin(2 * math.pi * 5.5 * t))
    ph = np.cumsum(f0 / SR)
    pulse = (ph % 1.0); src = (pulse - 0.5) * 2
    src = np.diff(np.concatenate([[0], np.cumsum(src)])) if False else src
    src = src - np.convolve(src, np.ones(4) / 4, 'same') * 0.6
    sm = np.convolve(amp, np.ones(int(0.012 * SR)) / int(0.012 * SR), 'same')
    asp = rng.normal(0, 1, n) * breath
    voiced = (src + asp) * sm
    out = np.zeros(n)
    for j, bw in enumerate((90, 110, 160)):
        out += resonate(voiced, F[j], np.full(n, bw)) * (1.0, 0.6, 0.3)[j]
    nz = rng.normal(0, 1, n) * np.convolve(noise_amp, np.ones(200) / 200, 'same')
    lo = int(np.median(nband[0][nband[0] > 0])) if (nband[0] > 0).any() else 2000
    out += band(nz, 1500, 8000) * 0.5
    out = out / (np.abs(out).max() + 1e-9) * gain
    return out * env(n, 0.01, 0.05)


def place(buf, x, t):
    i = int((t + OFF) * SR)
    if i < 0 or i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += x[:j - i]


def main():
    n = int(38 * SR); L = np.zeros(n); R = np.zeros(n)
    voice = np.zeros(n)
    # the person: calls (loud, raised pitch) and the soft voice (low, breathy, quiet)
    call1 = say([('_', .03), ('k', .06), ('u', .13), ('m', .08), ('h', .07), ('I', .13), ('e', .2)],
                [200, 225, 245, 215, 170], breath=0.04, gain=0.55)
    call2 = np.concatenate([say([('_', .02), ('k', .05), ('u', .12), ('m', .07), ('h', .06), ('I', .14), ('e', .16)],
                                [225, 250, 270, 240], breath=0.04, gain=0.62),
                            np.zeros(int(0.1 * SR)),
                            say([('k', .05), ('u', .11), ('m', .06), ('o', .16), ('n', .12)], [240, 260, 230, 190],
                                breath=0.04, gain=0.58)])
    soft1 = say([('I', .08), ('t', .05), ('s', .09), ('o', .16), ('l', .08), ('r', .06), ('a', .14), ('i', .1),
                 ('t', .06)], [150, 160, 150, 135, 120], breath=0.22, gain=0.2)
    soft2 = say([('k', .05), ('u', .12), ('m', .08), ('I', .14), ('n', .16)], [150, 155, 140, 122], breath=0.22,
                gain=0.2)
    segs = []
    for x, t, kind in ((call1, 0.88, 'call'), (call1 * 0.9, 1.65, 'call'), (call2, 3.30, 'call'), (soft1, 7.30, 'soft'),
                       (soft1 * 0.95, 10.40, 'soft'), (soft2, 26.25, 'soft')):
        place(voice, x, t); segs.append((t, t + len(x) / SR, kind))
    # ambience: room tone (outside, cooler) and crickets; the room's warmth after the door opens
    tt = np.arange(n) / SR
    tone = band(rng.normal(0, 1, n), 60, 900) * 0.006
    cr = np.zeros(n)
    for k in range(int(38 * 1.6)):
        t0 = rng.uniform(0, 38); f = rng.uniform(4200, 4700)
        for p in range(rng.integers(3, 6)):
            s = int((t0 + p * 0.045) * SR); m = int(0.025 * SR)
            if s + m < n: cr[s:s + m] += np.sin(2 * math.pi * f * np.arange(m) / SR) * np.hanning(m) * 0.006
    open_ = np.clip((tt - (OFF + 6.2)) / 0.8, 0, 1)
    warm = (band(rng.normal(0, 1, n), 90, 400) * 0.007 + np.sin(2 * math.pi * 110 * tt) * 0.0016) * open_
    amb = tone + cr + warm
    fx = np.zeros(n)
    ev = json.load(open(os.path.join(CACHE, 'events.json')))
    for e in ev:
        t = e['t']
        if e['name'] == 'step':
            m = int(0.05 * SR)
            x = band(rng.normal(0, 1, m), 150, 2200) * np.exp(-np.arange(m) / (0.008 * SR)) * rng.uniform(0.02, 0.035)
            place(fx, x, t)
        elif e['name'] == 'thump':
            m = int(0.35 * SR)
            x = (np.sin(2 * math.pi * 70 * np.arange(m) / SR) * 0.08 + band(rng.normal(0, 1, m), 80, 600) * 0.05) * \
                np.exp(-np.arange(m) / (0.07 * SR))
            place(fx, x, t)
        elif e['name'] == 'whimper':
            m = int(0.45 * SR); a = np.arange(m) / SR
            f = 950 - 300 * a / 0.45 + 25 * np.sin(2 * math.pi * 7 * a)
            x = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.hanning(m) * 0.03
            place(fx, x, t)
        elif e['name'] == 'jingle':
            for k in range(3):
                m = int(0.25 * SR); a = np.arange(m) / SR
                x = sum(np.sin(2 * math.pi * f * a) for f in (3150, 4720, 6230)) * np.exp(-a / 0.05) * 0.012
                place(fx, x, t + k * 0.06 + rng.uniform(0, 0.02))
        elif e['name'] == 'sigh':
            m = int(0.9 * SR); a = np.arange(m) / SR
            x = band(rng.normal(0, 1, m), 250, 1600) * np.hanning(m) * 0.05
            place(fx, x, t)
    # the door: a creak as it swings (6.2 s), a latch tick
    m = int(0.75 * SR); a = np.arange(m) / SR
    f0 = 140 + 60 * np.sin(2 * math.pi * 1.3 * a) + rng.normal(0, 4, m)
    cre = np.sign(np.sin(2 * math.pi * np.cumsum(f0) / SR)) * 0.5
    cre = band(cre, 300, 2500) * np.hanning(m) * 0.05
    place(fx, cre, 6.2)
    # the person: steps aside (4.8-5.4), sits (5.9)
    for k, t in enumerate(np.arange(4.85, 5.5, 0.22)):
        mm = int(0.07 * SR); place(fx, band(rng.normal(0, 1, mm), 100, 1500) * np.exp(-np.arange(mm) / (0.015 * SR)) * 0.05, t)
    mm = int(0.3 * SR); place(fx, band(rng.normal(0, 1, mm), 60, 500) * np.exp(-np.arange(mm) / (0.06 * SR)) * 0.09, 5.95)
    mix = voice + fx + amb
    # fade the ambience in under the title and out under the end card
    fade = np.clip(tt / 1.5, 0, 1) * np.clip((38 - tt) / 1.5, 0, 1)
    mix = mix * fade
    L = mix * 1.0; R = mix * 1.0
    peak = max(np.abs(L).max(), 1e-9)
    if peak > 0.95: L *= 0.95 / peak; R *= 0.95 / peak
    import wave
    st = np.stack([L, R], 1)
    w = wave.open(os.path.join(CACHE, 'film.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

    def rms_db(x): return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)
    lv = []
    for a0, a1, kind in segs:
        i0, i1 = int((a0 + OFF) * SR), int((a1 + OFF) * SR)
        v = voice[i0:i1]; v = v[np.abs(v) > 0.02 * np.abs(v).max()]
        lv.append(dict(t=a0, kind=kind, rms_db=round(rms_db(v), 2)))
    calls = [x['rms_db'] for x in lv if x['kind'] == 'call']; softs = [x['rms_db'] for x in lv if x['kind'] == 'soft']
    room = rms_db(amb[int(OFF * SR):int((OFF + 32) * SR)])
    out = dict(segments=lv, call_rms_db=round(float(np.mean(calls)), 2), soft_rms_db=round(float(np.mean(softs)), 2),
               soft_under_calls_db=round(float(np.mean(calls) - np.mean(softs)), 2),
               ambience_rms_db=round(room, 2), soft_over_ambience_db=round(float(np.mean(softs) - room), 2),
               voice_onsets=[s[0] for s in segs],
               note='measured on the synthesized voice track (active samples only) and the ambience bed, dBFS')
    json.dump(out, open(os.path.join(FOLDER, 'proof', 'levels.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
