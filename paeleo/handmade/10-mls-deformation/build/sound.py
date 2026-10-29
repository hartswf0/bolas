"""SCION-10 · sound, synthesized here (numpy/scipy): dusk room tone (wind, crickets), a formant voice for the person
(calls, then the soft words), the dog's paws on the boards at the footfalls the gait produced, the turn's scrabble, the body
going down, tail thumps, the door's latch and creak, the warm room behind it. 38 s: 3 s title, 32 s scene, 3 s end card.
Writes cache/sound.wav and ../proof/sound_levels.json (measured RMS of the calls, the soft words and the room tone)."""
import json, os
import numpy as np
from scipy import signal
from scipy.io import wavfile

H = os.path.dirname(os.path.abspath(__file__))
SR = 48000; PRE = 3.0; TOTAL = 38.0
rng = np.random.default_rng(1010)
N = int(TOTAL * SR)
L = np.zeros(N); Rch = np.zeros(N)


def at(t):
    return int((t + PRE) * SR)


def add(sig, t, gain=1.0, pan=0.0):
    i = at(t); j = min(N, i + len(sig))
    if j <= i: return
    s = sig[:j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); Rch[i:j] += s * np.sqrt(0.5 * (1 + pan))


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2)); return signal.lfilter(b, a, x)


def env(n, a=0.005, r=0.05):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


# ---------------- the voice: a small formant synthesizer ------------------------------------------------------------------
V = {'a': (730, 1090, 2440), 'uh': (640, 1190, 2390), 'ih': (390, 1990, 2550), 'schwa': (500, 1500, 2500), 'aw': (570, 840, 2410),
     'iy': (300, 2200, 2950), 'l': (360, 1300, 2700), 'r': (420, 1300, 1650), 'm': (260, 1100, 2300), 'n': (260, 1500, 2500)}


def phrase(units, f0a, f0b, breath=0.1, loud=1.0):
    """units: list of (kind, dur, spec). kind 'v' voiced with formants spec (name or (name1,name2) glide), 'n' nasal,
    'h' aspiration with formants of spec, 'k'/'t' burst, 's' hiss, '-' silence."""
    total = sum(u[1] for u in units); n = int(total * SR)
    t = np.arange(n) / SR
    f0 = f0a + (f0b - f0a) * (t / total) + 6 * np.sin(2 * np.pi * 5.2 * t) * 0.3
    ph = np.cumsum(f0 / SR)
    src = (ph % 1.0) * 2 - 1                                   # sawtooth glottal source
    src = lp(src, 2800, 1) + breath * rng.normal(0, 0.6, n)
    out = np.zeros(n); pos = 0
    for kind, dur, spec in units:
        m = int(dur * SR); seg = slice(pos, pos + m)
        if kind in ('v', 'n', 'h'):
            a, b = (spec, spec) if isinstance(spec, str) else spec
            Fa, Fb = np.array(V[a], float), np.array(V[b], float)
            x = src[seg] if kind != 'h' else rng.normal(0, 0.5, m)
            y = np.zeros(m)
            blk = int(0.005 * SR)
            zis = [np.zeros(2) for _ in range(3)]
            for s0 in range(0, m, blk):
                k = min(1, (s0 + blk / 2) / max(m, 1))
                F = Fa + (Fb - Fa) * k
                xx = x[s0:s0 + blk]; acc = np.zeros(len(xx))
                for fi, (f, bw, g) in enumerate(zip(F, (80, 110, 160), (1.0, 0.6, 0.3))):
                    r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
                    bb = [1 - r]; aa = [1, -2 * r * np.cos(th), r * r]
                    yy, zis[fi] = signal.lfilter(bb, aa, xx, zi=zis[fi] if zis[fi].any() else signal.lfilter_zi(bb, aa) * 0)
                    acc += g * yy
                y[s0:s0 + blk] = acc
            if kind == 'n': y *= 0.35
            if kind == 'h': y *= 0.5
            out[seg] = y * env(m, 0.012, 0.02)
        elif kind in ('k', 't'):
            bn = int(0.022 * SR); burst = bp(rng.normal(0, 1, bn), 1800 if kind == 'k' else 3500, 4500 if kind == 'k' else 8000) * np.linspace(1, 0, bn) ** 2
            out[pos + max(0, m - bn):pos + m] += burst[:min(bn, m)] * 0.5
        elif kind == 's':
            out[seg] = bp(rng.normal(0, 1, m), 4500, 9000, 2) * env(m, 0.02, 0.03) * 0.25
        pos += m
    out /= np.abs(out).max() + 1e-9
    return out * loud


COME_HERE = [('-', 0.03, None), ('k', 0.05, None), ('v', 0.15, 'uh'), ('n', 0.10, 'm'), ('h', 0.08, 'ih'), ('v', 0.13, 'ih'), ('v', 0.24, ('ih', 'schwa'))]
ALL_RIGHT = [('v', 0.09, 'ih'), ('t', 0.04, None), ('s', 0.09, None), ('v', 0.17, 'aw'), ('v', 0.08, 'l'), ('v', 0.07, 'r'), ('v', 0.26, ('a', 'ih')), ('t', 0.05, None)]
COME_IN = [('-', 0.03, None), ('k', 0.05, None), ('v', 0.13, 'uh'), ('n', 0.08, 'm'), ('v', 0.16, 'ih'), ('n', 0.20, 'n')]


def main():
    T = TOTAL
    # room tone: low wind and a field of crickets, through the whole film (quiet under the cards)
    n = N
    wind = lp(rng.normal(0, 1, n), 300, 2) * (0.6 + 0.4 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.07))
    crick = np.zeros(n)
    for k in range(5):
        f = rng.uniform(3800, 5200); rate = rng.uniform(1.8, 3.2); ph = rng.uniform(0, 1)
        tt = np.arange(n) / SR
        gate = (np.sin(2 * np.pi * (rate * tt + ph)) > 0.6) * (np.sin(2 * np.pi * 28 * tt) > 0)
        crick += np.sin(2 * np.pi * f * tt) * gate * rng.uniform(0.3, 1.0)
    room = wind / np.std(wind) * 0.006 + lp(crick, 7000) * 0.0025
    fade = np.clip(np.arange(n) / SR / 2.0, 0, 1) * np.clip((T - np.arange(n) / SR) / 1.5, 0, 1)
    room *= fade
    L[:] += room; Rch[:] += room
    # the warm room behind the door: a low hum and a clock, rising when the door opens
    tt = np.arange(n) / SR - PRE
    open_k = np.clip((tt - 6.2) / 1.0, 0, 1) * 0.85 + 0.15
    hum = lp(rng.normal(0, 1, n), 180, 2); hum = hum / hum.std() * 0.004 * open_k * np.clip((T - PRE + 0.0 - tt) / 1.5, 0, 1) * (tt > -2)
    L[:] += hum * 1.2; Rch[:] += hum * 0.6
    for k in np.arange(0, 32, 1.0):
        tick = bp(rng.normal(0, 1, int(0.01 * SR)), 2500, 6000) * np.linspace(1, 0, int(0.01 * SR))
        add(tick, k + 0.37, 0.006 * (0.15 + 0.85 * min(1, max(0, (k - 6.2))) ), pan=-0.6)

    levels = {}
    # the calls (loud), the soft words (quiet, breathy, lower)
    call1 = phrase(COME_HERE, 190, 150, breath=0.05, loud=0.42)
    call2 = phrase(COME_HERE, 215, 160, breath=0.05, loud=0.47)
    soft = phrase(ALL_RIGHT, 150, 120, breath=0.35, loud=0.16)
    soft2 = phrase(ALL_RIGHT, 145, 118, breath=0.35, loud=0.15)
    comein = phrase(COME_IN, 150, 125, breath=0.35, loud=0.16)
    for sig, t0, key in ((call1, 1.0, 'call_1.0'), (call2, 3.4, 'call_3.4'), (soft, 7.45, 'soft_7.4'), (soft2, 10.45, 'soft_10.4'), (comein, 26.45, 'soft_26.4')):
        add(sig, t0, 1.0, pan=-0.35)
        levels[key] = sig
    # door: latch click at 6.2, then a creak while it swings (6.2-7.0)
    add(bp(rng.normal(0, 1, int(0.03 * SR)), 1500, 5000) * np.linspace(1, 0, int(0.03 * SR)) ** 3, 6.18, 0.25, pan=-0.6)
    m = int(0.8 * SR); tc = np.arange(m) / SR
    fcr = 180 + 140 * tc / 0.8 + 30 * np.sin(2 * np.pi * 3 * tc)
    saw = ((np.cumsum(fcr / SR)) % 1.0) * 2 - 1
    jit = (rng.random(m) > 0.97) * 1.0
    creak = bp(saw * (0.6 + 0.4 * lp(jit, 60, 1) * 20), 600, 2600) * env(m, 0.08, 0.25)
    add(creak / (np.abs(creak).max() + 1e-9), 6.25, 0.06, pan=-0.6)
    # the person's steps out and aside (4.7-5.4), sitting down (5.6-7.0): wood creak and cloth
    for k, ts in enumerate((4.75, 5.05, 5.35)):
        st = lp(rng.normal(0, 1, int(0.08 * SR)), 400) * np.linspace(1, 0, int(0.08 * SR)) ** 2
        add(st / np.abs(st).max(), ts, 0.10, pan=-0.4)
    cloth = bp(rng.normal(0, 1, int(1.0 * SR)), 800, 4000) * env(int(1.0 * SR), 0.3, 0.4)
    add(cloth / np.abs(cloth).max(), 5.8, 0.02, pan=-0.4)
    thud = lp(rng.normal(0, 1, int(0.15 * SR)), 150) * np.linspace(1, 0, int(0.15 * SR)) ** 2
    add(thud / np.abs(thud).max(), 6.75, 0.12, pan=-0.4)
    # the dog's paws: a soft tap on the boards at every footfall the gait made
    falls = json.load(open(os.path.join(H, 'cache', 'footfalls.json')))
    for f in falls:
        tap = bp(rng.normal(0, 1, int(0.025 * SR)), 900, 3800) * np.linspace(1, 0, int(0.025 * SR)) ** 4
        pan = float(np.clip((f['x'] - 2.0) / 3.0, -0.8, 0.8))
        add(tap / np.abs(tap).max(), f['t'], 0.035, pan=pan)
    # the turn away: nails scrabble; going down (4.5 and 24.0): a body on the boards and a breath out
    scr = bp(rng.normal(0, 1, int(0.5 * SR)), 2000, 7000) * (rng.random(int(0.5 * SR)) > 0.92) * env(int(0.5 * SR), 0.05, 0.2)
    add(scr, 3.6, 0.05, pan=0.5); add(scr[::-1], 7.95, 0.05, pan=0.5)
    for t0, pan in ((4.55, 0.5), (24.05, -0.5)):
        add(thud / np.abs(thud).max(), t0, 0.09, pan=pan)
        sigh = bp(rng.normal(0, 1, int(0.9 * SR)), 300, 1800) * env(int(0.9 * SR), 0.1, 0.6)
        add(sigh / np.abs(sigh).max(), t0 + 0.6, 0.025, pan=pan)
    # tail thumps on the boards while it looks in (wag while lying, 26.6-28.1)
    for k in np.arange(26.7, 28.1, 0.24):
        add(thud / np.abs(thud).max(), k, 0.035, pan=-0.5)
    # a small whine when it is called the second time and when it turns its back
    m = int(0.45 * SR); tw = np.arange(m) / SR
    wh = np.sin(2 * np.pi * np.cumsum(900 + 250 * np.sin(np.pi * tw / 0.45)) / SR) * env(m, 0.05, 0.2)
    add(wh, 3.85, 0.012, pan=0.5)

    mix = np.stack([L, Rch], 1)
    peak = np.abs(mix).max()
    if peak > 0.95: mix *= 0.95 / peak
    os.makedirs(os.path.join(H, 'cache'), exist_ok=True)
    wavfile.write(os.path.join(H, 'cache', 'sound.wav'), SR, (mix * 32767).astype(np.int16))
    # measured levels (RMS over each voice's own voiced span; room tone over 12-14 s where nothing else sounds but the room)
    def db(x): return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))
    def span_db(t0, sig):
        i = at(t0); j = i + len(sig)
        seg = mix[i:j].mean(1); a = np.abs(sig) > 0.05 * np.abs(sig).max()
        return db(seg[a]) if a.any() else None
    out = {k: round(span_db(float(k.split('_')[1]) + (0.05 if 'soft' in k else 0), s), 2) for k, s in levels.items()}
    out['room_tone_12_14s'] = round(db(mix[at(12.0):at(14.0)].mean(1)), 2)
    calls = [v for k, v in out.items() if k.startswith('call')]; softs = [v for k, v in out.items() if k.startswith('soft')]
    out['soft_minus_calls_db'] = round(max(softs) - min(calls), 2)
    out['soft_above_room_db'] = round(min(softs) - out['room_tone_12_14s'], 2)
    out['ok'] = out['soft_minus_calls_db'] <= -6 and out['soft_above_room_db'] > 6
    os.makedirs(os.path.join(H, '..', 'proof'), exist_ok=True)
    json.dump(out, open(os.path.join(H, '..', 'proof', 'sound_levels.json'), 'w'), indent=1)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
