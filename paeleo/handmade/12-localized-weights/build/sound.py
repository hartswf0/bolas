"""Sound, synthesized here (no recordings): a source-filter formant voice for the person, paper footfalls and rustles for the
lace dog (driven by the same gait and yaw schedule as the picture), the door, crickets and a low dusk air, and a warm pad when
the light comes out. Writes cache/scene.wav (32 s) and cache/film.wav (38 s: 3 s title + scene + 3 s end card).
Also writes cache/levels.json: measured RMS of each spoken line (dBFS), so the soft voice can be checked against the calls."""
import json, os
import numpy as np
from scipy.signal import lfilter, butter, sosfilt
import perform

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = 32.0
rng = np.random.default_rng(12)

# ---------------------------------------------------------------- formant voice
PH = {  # F1 F2 F3 (Hz), amplitude, voiced, noise
    'k': ((300, 1800, 2500), 0.0, 0, 'burst'), 't': ((300, 1800, 2700), 0.0, 0, 'burst'),
    's': ((300, 1800, 2700), 0.0, 0, 'hiss'), 'h': ((500, 1500, 2500), 0.0, 0, 'asp'),
    'ah': ((640, 1190, 2390), 1.0, 1, None), 'm': ((260, 1100, 2200), 0.35, 1, None), 'n': ((260, 1500, 2500), 0.35, 1, None),
    'ih': ((390, 1990, 2550), 0.9, 1, None), 'ea': ((520, 1500, 2450), 0.95, 1, None), 'ao': ((570, 840, 2410), 1.0, 1, None),
    'l': ((360, 1000, 2600), 0.6, 1, None), 'r': ((420, 1300, 1700), 0.7, 1, None), 'ai': ((700, 1220, 2600), 1.0, 1, None),
    'iy': ((300, 2300, 3000), 0.85, 1, None), 'sil': ((500, 1500, 2500), 0.0, 0, None),
}
LINES = {
    'Come here.': [('k', .06), ('ah', .16), ('m', .10), ('h', .07), ('ih', .16), ('ea', .26), ('sil', .05)],
    "It's all right.": [('ih', .09), ('t', .04), ('s', .10), ('ao', .20), ('l', .12), ('r', .08), ('ai', .26), ('t', .05), ('sil', .05)],
    'Come in.': [('k', .06), ('ah', .14), ('m', .10), ('ih', .16), ('n', .22), ('sil', .05)],
}


def resonator(x, f, bw, state):
    r = np.exp(-np.pi * bw / SR)
    c = -r * r; b = 2 * r * np.cos(2 * np.pi * f / SR); a = 1 - b - c
    y, state = lfilter([a], [1, -b, -c], x, zi=state)
    return y, state


def speak(text, f0_start, f0_peak, f0_end, loud, breath, tempo=1.0):
    seq = [(p, d * tempo) for p, d in LINES[text]]
    total = sum(d for _, d in seq)
    n = int(total * SR)
    t = np.arange(n) / SR
    # pitch contour: rise to a peak at 55% then fall (a call) - softer lines have smaller range
    u = t / total
    f0 = np.where(u < .55, f0_start + (f0_peak - f0_start) * np.sin(u / .55 * np.pi / 2),
                  f0_peak + (f0_end - f0_peak) * np.sin((u - .55) / .45 * np.pi / 2))
    f0 *= 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t)
    ph = np.cumsum(f0 / SR)
    saw = 2 * (ph % 1.0) - 1
    src = lfilter([1], [1, -0.94], saw - np.concatenate([[0], saw[:-1]]) * 0.0)  # tilt
    src = src / (np.abs(src).max() + 1e-9)
    noise = rng.normal(0, 1, n)
    # per-sample targets with 25 ms glides
    F = np.zeros((n, 3)); amp = np.zeros(n); voiced = np.zeros(n); nz = np.zeros(n)
    pos = 0
    for p, d in seq:
        m = int(d * SR)
        fr, a, v, kind = PH[p]
        F[pos:pos + m] = fr; amp[pos:pos + m] = a; voiced[pos:pos + m] = v
        if kind == 'burst':
            env = np.exp(-np.arange(m) / (0.012 * SR)); nz[pos:pos + m] = 0.9 * env
        elif kind == 'hiss':
            nz[pos:pos + m] = 0.45
        elif kind == 'asp':
            nz[pos:pos + m] = 0.35
        pos += m
    k = int(0.025 * SR)
    ker = np.ones(k) / k
    for j in range(3):
        F[:, j] = np.convolve(np.pad(F[:, j], (k, k), mode='edge'), ker, 'same')[k:-k]
    amp = np.convolve(amp, ker, 'same'); voiced = np.convolve(voiced, ker, 'same'); nz = np.convolve(nz, ker, 'same')
    exc = src * amp * voiced * (1 - breath) + noise * (amp * voiced * breath * 0.5 + nz * 0.6)
    out = np.zeros(n)
    blk = 240
    for j, bw in ((0, 80), (1, 110), (2, 160)):
        st = np.zeros(2); y = np.zeros(n)
        for s0 in range(0, n, blk):
            fj = F[s0, j]
            yy, st = resonator(exc[s0:s0 + blk], fj, bw * (1.6 if breath > .3 else 1), st)
            y[s0:s0 + blk] = yy
        out += y * (1.0, 0.6, 0.35)[j]
    # hiss / burst high band
    sos = butter(4, 3500, 'hp', fs=SR, output='sos')
    out += sosfilt(sos, noise) * nz * 0.25
    out = out / (np.abs(out).max() + 1e-9)
    env = np.minimum(1, np.minimum(t / 0.02, (total - t) / 0.16)) ** 1.5   # a natural release, not a cut
    return out * env * loud


# ---------------------------------------------------------------- the score's sounds
def place(buf, sig, t0):
    i = int(t0 * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i]


def paper_tick(gain, bright=1.0):
    n = int(0.05 * SR)
    x = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.008 * SR))
    sos = butter(2, [900 * bright, 4200 * bright], 'bp', fs=SR, output='sos')
    thud = np.sin(2 * np.pi * 110 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.015 * SR))
    return (sosfilt(sos, x) * 0.6 + thud * 0.5) * gain


def rustle(dur, gain):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    sos = butter(2, [1500, 7000], 'bp', fs=SR, output='sos')
    env = np.sin(np.pi * np.arange(n) / n) ** 2 * (0.6 + 0.4 * np.abs(rng.normal(0, 1, n // 400 + 1)).repeat(400)[:n])
    return sosfilt(sos, x) * env * gain


def creak(dur, gain):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 240 + 120 * np.sin(2 * np.pi * 0.7 * t) + 30 * rng.normal(0, 1, n).cumsum() / np.sqrt(n)
    ph = np.cumsum(f / SR)
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.5 + 0.5 * rng.random(n))
    y = np.zeros(n); st = np.zeros(2)
    for fr in (900, 1700, 2600):
        r, st = resonator(pulses, fr, 60, np.zeros(2)); y += r
    env = np.sin(np.pi * t / dur) ** 0.6
    return y / (np.abs(y).max() + 1e-9) * env * gain


def build_scene():
    n = int(DUR * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    # dusk air: low filtered noise, and crickets
    sos = butter(2, [60, 500], 'bp', fs=SR, output='sos')
    out += sosfilt(sos, rng.normal(0, 1, n)) * 0.010
    for c0, fc in ((0.0, 4300), (0.37, 4700)):
        chirp = np.sin(2 * np.pi * fc * t) * (np.sin(2 * np.pi * 28 * t) > 0.2)
        gate = ((t + c0) % 0.9) < 0.22
        out += chirp * gate * 0.0035
    levels = {}
    vbus = np.zeros(n)
    # voices, placed where the score turns the voice on (onset 40 ms early, so the voice is at or before the dog's reaction)
    for a, b, text, kind in perform.WORDS:
        if kind == 'call':
            sig = speak(text, 190, 290, 180, 0.50, 0.08, tempo=1.0)
        else:
            sig = speak(text, 175, 200, 150, 0.115, 0.45, tempo=1.25)
        place(vbus, sig, a - 0.04)
        levels.setdefault(text + ' @%.2f' % a, 20 * np.log10(np.sqrt(np.mean(sig[np.abs(sig) > 1e-4] ** 2)) + 1e-12))
    # the voices sound in the room: a short decaying reverb tail (porch and doorway), so no line stops dead
    from scipy.signal import fftconvolve
    m = int(0.7 * SR); ti = np.arange(m) / SR
    ir = rng.normal(0, 1, m) * np.exp(-ti / 0.16)
    ir = sosfilt(butter(2, [300, 3500], 'bp', fs=SR, output='sos'), ir)
    ir = ir / np.sqrt((ir ** 2).sum())
    out += vbus + 0.22 * fftconvolve(vbus, ir)[:n]
    # dog: a paper tick at each paw plant (same gait as the picture), rustles on each yaw ripple
    P = perform.dog_poses()
    prev = None
    for p in P:
        cur = {k: v[1] for k, v in p['paws'].items()}
        if prev is not None:
            for k in cur:
                if prev[k] > 0.004 and cur[k] <= 0.004:
                    place(out, paper_tick(0.10 + 0.05 * rng.random()), p['t'])
        prev = cur
    for d, *ons in perform.TURNS:
        for o in ons:
            place(out, rustle(0.32, 0.05), o)
    # lying down: a long paper slide; at 4.4 and 23.9
    for t0 in (4.35, 23.85):
        place(out, rustle(0.8, 0.045), t0)
    # retreat scuffle
    place(out, rustle(1.2, 0.03), 1.05)
    # door: creak as it opens, latch click before
    open_t = next(f['t'] for f in perform.FR if f['door'] == 'open')
    place(out, paper_tick(0.22, 1.6), open_t - 0.08)
    place(out, creak(0.75, 0.06), open_t - 0.02)
    # person: soft steps aside (4.7 - 5.4), stool creak when sitting
    for t0 in np.arange(4.75, 5.5, 0.32):
        place(out, paper_tick(0.08, 0.5), t0)
    place(out, creak(0.35, 0.025), 5.55)
    # warm pad when the light comes out, and again, softer, when the dog lies across the sill
    for t0, dur, g in ((open_t, 9.0, 0.020), (23.8, 8.2, 0.016)):
        m = int(dur * SR); tt = np.arange(m) / SR
        env = np.minimum(1, tt / 1.5) * np.minimum(1, (dur - tt) / 2.5)
        pad = sum(np.sin(2 * np.pi * f * tt + k) / (k + 1) for k, f in enumerate((130.8, 196.0, 261.6, 329.6)))
        place(out, pad * env * g, t0)
    return out, levels


def card_audio(dur, f):
    n = int(dur * SR); tt = np.arange(n) / SR
    env = np.minimum(1, tt / 0.4) * np.minimum(1, (dur - tt) / 0.8)
    return (np.sin(2 * np.pi * f * tt) * 0.012 + rustle(dur, 0.012)) * env


if __name__ == '__main__':
    import wave
    scene, levels = build_scene()
    film = np.concatenate([card_audio(3.0, 196.0), scene, card_audio(3.0, 130.8)])
    peak = np.abs(film).max()
    film = film / max(peak, 1e-9) * 0.89 if peak > 0.89 else film
    for name, sig in (('film.wav', film),):
        with wave.open(os.path.join(HERE, 'cache', name), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())
    calls = [v for k, v in levels.items() if k.startswith('Come here')]
    softs = [v for k, v in levels.items() if not k.startswith('Come here')]
    levels['calls_minus_softest_db'] = round(min(calls) - max(softs), 2)
    json.dump({k: round(float(v), 2) for k, v in levels.items()}, open(os.path.join(HERE, 'cache', 'levels.json'), 'w'), indent=1)
    print(levels, 'peak', peak)
