"""sound_crowd.py -- repair round 2: the handmade concourse bed, rebuilt.

The round-1 bed was static band-limited noise (kit.Mix.band is an FFT
brick-wall: hard shelves) with fixed narrow formant bands (steady lines).
This module builds the concourse from EVENTS instead of from a texture:

  * talkers: utterances arrive as a Poisson process whose rate follows a slow
    crowd swell; each utterance has its own speaker (f0 95-230 Hz with
    declination and drift), syllables of 140-320 ms each on a new vowel
    (F1/F2/F3 from a vowel table), occasional fricatives; every talker sits
    at a distance (gain 1/d, air absorption, more reverb send)
  * walkers: heel strikes on stone passing by, some close, most far
  * PA fragments: two distant announcer phrases through a horn band and
    slap echoes, unintelligible
  * a baggage trolley, a case set down, a far steam release
  * trains: brown-noise rumble swells with noise-burst rail joints (no sine)
  * hall: noise IR, two bands, the highs decaying faster (no brick wall)

All filters are smooth Butterworth-magnitude responses applied in the FFT
domain (no brick-wall edges).  Deterministic: fixed seeds.  Everything here is
synthesised (HANDMADE); nothing foraged.

  check(x) -> the critic's falsifiable test:
      short-term RMS over 250 ms windows: p90 - p10 (dB) >= 6
      no narrowband line > 20 dB above the local spectral median for > 3 s
"""
import math
import numpy as np

R = 44100


def gentle(x, lo=None, hi=None, order=2):
    """Smooth band shaping (Butterworth magnitude, zero phase) in the FFT domain."""
    n = len(x)
    N = 1 << (n - 1).bit_length()
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / R)
    H = np.ones_like(f)
    if lo:
        H *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi:
        H *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * H, N)[:n]


def conv(x, ir):
    n = len(x) + len(ir) - 1
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]


def hall(rt=2.6, seed=0, bright=4200):
    """Hall IR: noise with a slow low band and a faster-decaying high band."""
    rs = np.random.RandomState(seed)
    n = int(rt * R); t = np.arange(n) / R
    a = rs.normal(0, 1, n); b = rs.normal(0, 1, n)
    lo = gentle(a, 90, 900) * np.exp(-6.9 * t / rt)
    hi = gentle(b, 900, bright) * np.exp(-6.9 * t / (rt * 0.55))
    ir = lo + 0.7 * hi
    k = int(0.015 * R); ir[:k] *= np.linspace(0, 1, k)
    return ir / np.sqrt((ir ** 2).sum())


VOWELS = [  # F1, F2, F3 (Hz), French-ish
    (300, 2300, 3000), (400, 2000, 2650), (550, 1750, 2500), (750, 1350, 2500), (650, 1050, 2550),
    (450, 850, 2500), (320, 760, 2400), (300, 1750, 2150), (380, 1650, 2300), (500, 1450, 2450)]


def _formant_filter(seg, F, bw, gains):
    n = len(seg); N = 1 << (n - 1).bit_length()
    X = np.fft.rfft(seg, N); f = np.fft.rfftfreq(N, 1 / R)
    H = np.ones_like(f)                  # cascade of 2-pole resonators (all-pole vocal tract)
    for Fi, Bi in zip(F, bw):
        H *= Fi ** 2 / np.sqrt((Fi ** 2 - f ** 2) ** 2 + (Bi * f) ** 2)
    H *= np.sqrt(1 + (f / 450) ** 2) / np.sqrt(1 + (f / 5000) ** 4)   # radiation / sharper source edge
    return np.fft.irfft(X * H, N)[:n]


def utterance(rs, dur, f0):
    """One unintelligible phrase: a drifting glottal source shaped syllable by syllable."""
    n = int(dur * R); t = np.arange(n) / R
    walk = np.cumsum(rs.normal(0, 1, n // 2000 + 2))
    walk = np.interp(np.arange(n), np.linspace(0, n, len(walk)), walk)
    contour = f0 * (1.12 - 0.22 * t / dur) * (1 + 0.05 * walk / (np.abs(walk).max() + 1e-9)) \
        * (1 + 0.05 * np.sin(2 * np.pi * rs.uniform(0.6, 1.6) * t + rs.uniform(0, 6)))
    contour *= 1 + rs.normal(0, 0.006, n)                      # jitter
    ph = np.cumsum(contour / R) % 1.0
    src = (1 - np.cos(2 * np.pi * np.clip(ph / 0.6, 0, 1))) * (ph < 0.6) - 0.6
    src = np.diff(src, prepend=src[0]) * 40                     # glottal flow derivative
    src += rs.normal(0, 0.04, n)                               # breath
    out = np.zeros(n); pos = 0
    while pos < n - 800:
        L = int(rs.uniform(0.14, 0.32) * R); L = min(L, n - pos)
        if rs.rand() < 0.5:                                     # a table vowel, or anywhere in the vowel space
            F = [fi * rs.uniform(0.92, 1.1) for fi in VOWELS[rs.randint(len(VOWELS))]]
        else:
            f1 = rs.uniform(280, 820); F = [f1, max(f1 + 260, rs.uniform(850, 2400)), rs.uniform(2300, 3100)]
        seg = _formant_filter(src[pos:pos + L], F, (90, 140, 220), None)
        e = np.ones(L); a = max(1, min(int(0.03 * R), L // 3)); d = max(1, min(int(0.06 * R), L // 2))
        e[:a] = np.linspace(0, 1, a) ** 1.5; e[-d:] *= np.linspace(1, 0, d) ** 1.2
        e *= rs.uniform(0.55, 1.0)
        out[pos:pos + L] += seg * e
        if rs.rand() < 0.28:                                    # fricative onset (s, ch, f)
            m = min(int(rs.uniform(0.04, 0.09) * R), n - pos)
            fr = gentle(rs.normal(0, 1, m), rs.uniform(2800, 4500), 8000, 2) * np.hanning(m) * 0.25
            out[pos:pos + m] += fr
        pos += L + (int(rs.uniform(0.02, 0.25) * R) if rs.rand() < 0.25 else 0)
    w = np.ones(n); k = int(0.04 * R); w[:k] = np.linspace(0, 1, k); w[-k:] = np.linspace(1, 0, k)
    return out * w / (np.sqrt((out ** 2).mean()) + 1e-9)


def swell(rs, n, depth_db=8.0):
    """Slow crowd-density envelope in dB (sum of slow random sines)."""
    t = np.arange(n) / R; s = np.zeros(n)
    for fq in (0.045, 0.09, 0.17, 0.31):
        s += np.sin(2 * np.pi * fq * rs.uniform(0.8, 1.2) * t + rs.uniform(0, 6)) / (1 + fq * 4)
    s /= np.abs(s).max() + 1e-9
    return s * depth_db / 2


def heel(rs, close):
    n = int(0.16 * R); t = np.arange(n) / R
    c = rs.normal(0, 1, n) * np.exp(-t / (0.006 if close else 0.01))
    c = gentle(c, 250 if close else 180, 5500 if close else 2600)
    th = gentle(rs.normal(0, 1, n) * np.exp(-t / 0.03), 60, 400) * 0.6
    s = c + th
    return s / (np.abs(s).max() + 1e-9)


def walker(rs, dur, close=False):
    n = int(dur * R); out = np.zeros(n)
    pace = rs.uniform(0.48, 0.62); t = rs.uniform(0, 0.3); k = 0
    peak = rs.uniform(0.3, 0.7)
    while t < dur - 0.2:
        u = t / dur
        g = math.exp(-((u - peak) / 0.28) ** 2) * (0.85 if k % 2 else 1.0) * rs.uniform(0.85, 1.1)
        h = heel(rs, close); i = int(t * R); m = min(len(h), n - i)
        out[i:i + m] += h[:m] * g
        t += pace * rs.uniform(0.96, 1.04); k += 1
    return out


def steps_near(rs, n_steps, pace=0.5, gain=1.0, rise=True):
    """A few close heel strikes, rising (approach) or falling; mono."""
    out = np.zeros(int((n_steps * pace + 0.3) * R))
    for k in range(n_steps):
        g = ((k + 1) / n_steps if rise else 1 - k / n_steps) ** 1.2 * (0.85 if k % 2 else 1.0)
        h = heel(rs, True); i = int(k * pace * rs.uniform(0.97, 1.03) * R)
        out[i:i + len(h)] += h[:len(out) - i] * g * gain
    return out


def pa_phrase(rs, dur):
    """Distant announcer: one talker through a horn band, slap echoes."""
    u = utterance(rs, dur, rs.uniform(105, 125))
    u = np.tanh(gentle(u, 420, 2900, 3) * 0.9)
    n = len(u) + int(1.3 * R); y = np.zeros(n)
    for d, g in ((0.0, 1.0), (0.29, 0.5), (0.61, 0.32), (0.97, 0.18)):
        i = int(d * R); y[i:i + len(u)] += u * g
    return y


def trolley(rs, dur):
    n = int(dur * R); t = np.arange(n) / R
    rum = gentle(np.cumsum(rs.normal(0, 1, n)), 70, 900)
    rum /= np.abs(rum).max() + 1e-9
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    x = rum * env
    tt = 0.2
    while tt < dur - 0.1:                                       # wheel over tile joints
        i = int(tt * R); m = min(int(0.05 * R), n - i)
        x[i:i + m] += gentle(rs.normal(0, 1, m), 300, 3000) * np.exp(-np.arange(m) / R / 0.008) * env[i] * 0.8
        tt += rs.uniform(0.22, 0.3)
    return x


def thump(rs):
    n = int(0.5 * R); t = np.arange(n) / R
    x = gentle(rs.normal(0, 1, n), 50, 700) * np.exp(-t / 0.05)
    x += gentle(rs.normal(0, 1, n), 600, 4000) * np.exp(-t / 0.01) * 0.3
    return x / (np.abs(x).max() + 1e-9)


def steam(rs, dur):
    n = int(dur * R); t = np.arange(n) / R
    x = gentle(rs.normal(0, 1, n), 1200, 7000, 1)
    env = np.minimum(1, t / 0.08) * np.exp(-np.maximum(0, t - 0.25) / (dur * 0.35))
    return x * env


def trains(rs, seconds, passes):
    n = int(seconds * R); out = np.zeros(n)
    for (t0, dur) in passes:
        m = int(dur * R); tt = np.arange(m) / R
        rum = gentle(np.cumsum(rs.normal(0, 1, m)), 22, 240)
        rum /= np.abs(rum).max() + 1e-9
        sw = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
        x = rum * sw
        k = rs.uniform(0, 0.5)
        while k < dur - 0.2:
            for dd in (0.0, 0.105 + rs.uniform(-0.01, 0.01)):
                i = int((k + dd) * R)
                if i + 3000 < m:
                    b = gentle(rs.normal(0, 1, 3000), 120, 1400) * np.exp(-np.arange(3000) / R * 45)
                    x[i:i + 3000] += 0.9 * sw[i] * b / (np.abs(b).max() + 1e-9)
            k += 0.95 + rs.uniform(-0.05, 0.05)
        i0 = int(t0 * R)
        if i0 < n:
            out[i0:i0 + m] += x[:n - i0]
    wet = conv(out, hall(3.2, 202, 1500))
    return 0.35 * out + wet


def concourse(seconds, seed=11, lead=3.0):
    """The handmade concourse bed: (L, R) float arrays at unit RMS, plus an event log.
    Built `lead` s longer and the head dropped, so the crowd is already there at t=0."""
    outL, outR, log = _concourse(seconds + lead, seed)
    k = int(lead * R); n = int(seconds * R)
    outL, outR = outL[k:k + n], outR[k:k + n]
    for e in log:
        if 't' in e:
            e['t'] = round(e['t'] - lead, 2)
    s = np.sqrt(((outL ** 2 + outR ** 2) / 2).mean()) + 1e-9
    return outL / s, outR / s, log


def _concourse(seconds, seed):
    rs = np.random.RandomState(seed)
    n = int(seconds * R)
    L = np.zeros(n); Rr = np.zeros(n); wet = np.zeros(n)
    log = []
    rate = 10 ** (swell(rs, n, 16.0) / 20)                         # density follows the swell
    t = 0.0; nt = 0
    while t < seconds:
        lam = 3.2 * rate[min(n - 1, int(t * R))]
        t += rs.exponential(1 / lam)
        if t >= seconds:
            break
        dur = rs.uniform(0.9, 3.6); d = rs.uniform(4, 28)       # seconds, metres
        u = gentle(utterance(rs, dur, rs.uniform(95, 230)), 120, 7000 / (1 + d / 10), 1)
        g = 1.0 / d; pan = rs.uniform(-0.8, 0.8)
        i = int(t * R); m = min(len(u), n - i)
        L[i:i + m] += u[:m] * g * (1 - pan) * 0.7; Rr[i:i + m] += u[:m] * g * (1 + pan) * 0.7
        wet[i:i + m] += u[:m] * g * (0.6 + d / 30); nt += 1
    log.append(dict(what='talker utterances', count=nt))
    for j in range(9):                                           # walkers passing
        dur = rs.uniform(4, 9); t0 = rs.uniform(-1, seconds - 2); close = j < 2
        w = walker(rs, dur, close) * (0.11 if close else 0.045)
        i = int(max(0, t0) * R); w = w[int(max(0, -t0) * R):]; m = min(len(w), n - i)
        p = rs.uniform(-0.7, 0.7)
        L[i:i + m] += w[:m] * (1 - p) * 0.7; Rr[i:i + m] += w[:m] * (1 + p) * 0.7
        wet[i:i + m] += w[:m] * 0.8
        log.append(dict(what='walker' + (' (close)' if close else ''), t=round(max(0, t0), 2), dur=round(dur, 2)))
    for (t0, dur) in ((seconds * 0.3, 2.6), (seconds * 0.7, 2.2)):
        y = pa_phrase(rs, dur) * 0.035
        i = int(t0 * R); m = min(len(y), n - i)
        L[i:i + m] += y[:m] * 0.6; Rr[i:i + m] += y[:m] * 0.6; wet[i:i + m] += y[:m] * 1.6
        log.append(dict(what='PA fragment (unintelligible)', t=round(t0, 2), dur=dur))
    for (fn, t0, gain, what) in ((lambda: trolley(rs, 3.4), seconds * 0.42, 0.06, 'baggage trolley'),
                                 (lambda: thump(rs), seconds * 0.55, 0.09, 'case set down'),
                                 (lambda: steam(rs, 2.0), seconds * 0.8, 0.02, 'steam release, far')):
        y = fn() * gain; i = int(t0 * R); m = min(len(y), n - i)
        L[i:i + m] += y[:m]; Rr[i:i + m] += y[:m] * 0.8; wet[i:i + m] += y[:m] * 1.2
        log.append(dict(what=what, t=round(t0, 2)))
    WL = conv(wet, hall(2.7, seed + 1)) * 2.2; WR = conv(wet, hall(2.7, seed + 2)) * 2.2
    air = gentle(rs.normal(0, 1, n), 80, 2500, 1) * 0.004
    outL = L + WL + air; outR = Rr + WR + np.roll(air, 977)
    s = np.sqrt(((outL ** 2 + outR ** 2) / 2).mean()) + 1e-9
    return outL / s, outR / s, log


def check(x, rate=R):
    """Critic's falsifiable test on a mono signal."""
    from numpy.lib.stride_tricks import sliding_window_view
    w = int(0.25 * rate); k = len(x) // w
    db = 20 * np.log10(np.sqrt((x[:k * w].reshape(k, w) ** 2).mean(1)) + 1e-12)
    spread = float(np.percentile(db, 90) - np.percentile(db, 10))
    nfft, hop = 8192, 2048
    win = np.hanning(nfft)
    S = np.array([np.abs(np.fft.rfft(x[i:i + nfft] * win)) for i in range(0, len(x) - nfft, hop)])
    S = 20 * np.log10(S + 1e-9)
    f = np.fft.rfftfreq(nfft, 1 / rate); keep = (f > 40) & (f < 12000)
    S = S[:, keep]; fk = f[keep]
    med = np.median(sliding_window_view(np.pad(S, ((0, 0), (40, 40)), mode='edge'), 81, axis=1), axis=-1)
    over = (S - med) > 20
    dt = hop / rate; worst = 0.0; worst_f = None
    for j in np.where(over.any(0))[0]:
        run = best = 0
        for v in over[:, j]:
            run = run + 1 if v else 0; best = max(best, run)
        if best * dt > worst:
            worst = best * dt; worst_f = float(fk[j])
    return dict(rms_p10_p90_db=round(spread, 2), longest_line_s=round(worst, 2), line_hz=worst_f,
                pass_rms=bool(spread >= 6.0), pass_lines=bool(worst <= 3.0))
