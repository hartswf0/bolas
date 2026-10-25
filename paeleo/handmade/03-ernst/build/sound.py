"""SCION 03 Ernst · the sound plate: every sound synthesized here (no recordings), cut to the score and the solver.

  room tone   dusk crickets and a low wind, under everything
  the call    a formant voice ("Come here.") with a lion's growl pasted under it: the command is a hybrid noun too
  the hand    a paper rustle as the pasted hand swells
  the lion    a flutter of paper in flight, a stone knock as it settles in the keystone
  the door    a hinge creak, then a warm low chord: the light, heard
  soft voice  "It's all right." / "Come in." breathy, lower, at least 6 dB under the calls
  the dog     a claw tick and a soft pad on the boards at every touchdown of the step solver; a sigh when it lies down;
              its tail knocking the boards when it hears "come in"
Writes build/cache/scene.wav (32 s) and build/cache/audio_levels.json (measured RMS levels).
"""
import json, os, pickle, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
SR = 48000
DUR = 32.0
RNG = np.random.default_rng(20261025)


def db(x):
    return 10 ** (x / 20)


def biquad_bp(x, f, bw):
    """time-varying two-pole resonator (f, bw arrays or scalars), unity peak-ish gain."""
    n = len(x)
    f = np.broadcast_to(np.asarray(f, float), (n,)); bw = np.broadcast_to(np.asarray(bw, float), (n,))
    r = np.exp(-np.pi * bw / SR)
    th = 2 * np.pi * f / SR
    a1 = -2 * r * np.cos(th); a2 = r * r
    g = (1 - r * r) * 0.5
    y = np.zeros(n); y1 = y2 = 0.0
    xs = x.tolist(); a1l = a1.tolist(); a2l = a2.tolist(); gl = g.tolist()
    out = [0.0] * n
    for i in range(n):
        v = gl[i] * xs[i] - a1l[i] * y1 - a2l[i] * y2
        out[i] = v; y2 = y1; y1 = v
    return np.array(out)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    out = np.zeros_like(x); acc = 0.0
    xs = x.tolist(); o = [0.0] * len(xs)
    for i, v in enumerate(xs):
        acc = (1 - a) * v + a * acc; o[i] = acc
    return np.array(o)


def highpass(x, fc):
    return x - lowpass(x, fc)


def env(n, a, r, hold=None):
    e = np.ones(n)
    na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def glottal(f0, n, breath=0.1, jitter=0.01):
    """a Rosenberg-like pulse train with jitter, plus breath noise."""
    f0 = np.broadcast_to(np.asarray(f0, float), (n,)) * (1 + jitter * lowpass(RNG.standard_normal(n), 20) * 8)
    ph = np.cumsum(f0 / SR) % 1.0
    open_q = 0.6
    p = np.where(ph < open_q, 0.5 * (1 - np.cos(np.pi * ph / open_q)), np.cos(np.pi * (ph - open_q) / (2 * (1 - open_q))))
    src = np.diff(np.concatenate([[0], p]))
    src = src / (np.abs(src).max() + 1e-9)
    noise = RNG.standard_normal(n) * breath
    return src + noise


# phoneme table: (F1, F2, F3) in Hz
V = {'a': (700, 1220, 2600), 'u': (640, 1190, 2390), 'm': (280, 1100, 2300), 'h': (500, 1500, 2500),
     'i': (390, 1990, 2550), 'e': (530, 1840, 2480), 'o': (570, 840, 2410), 'l': (360, 1000, 2400),
     'ai1': (750, 1300, 2500), 'ai2': (420, 2000, 2600), 'n': (280, 1700, 2600), 'r': (460, 1300, 1700)}


def speak(segs, f0s, gain=1.0, breath=0.08):
    """segs: list of (kind, dur, p0, p1): kind 'v' voiced with formants interpolated p0->p1, 'n' nasal, 'f' fricative
    (centre Hz), 'b' burst, 's' silence.  f0s: (start, end) pitch over the whole utterance."""
    total = sum(s[1] for s in segs)
    n = int(total * SR)
    f0 = np.linspace(f0s[0], f0s[1], n)
    src = glottal(f0, n, breath=breath)
    out = np.zeros(n); k = 0
    for kind, dur, p0, p1 in segs:
        m = int(dur * SR)
        seg = np.zeros(m)
        if kind in ('v', 'n'):
            x = src[k:k + m]
            F0 = np.array(V[p0]); F1 = np.array(V[p1])
            tt = np.linspace(0, 1, m)[:, None]
            Fs = F0 * (1 - tt) + F1 * tt
            amp = [1.0, 0.6, 0.25] if kind == 'v' else [1.0, 0.12, 0.05]
            for j in range(3):
                seg += amp[j] * biquad_bp(x, Fs[:, j], [80, 110, 150][j])
            if kind == 'n':
                seg = lowpass(seg, 600) * 0.7
            seg *= env(m, 0.02, 0.03)
        elif kind == 'f':
            x = RNG.standard_normal(m)
            seg = biquad_bp(x, p0, p0 * 0.5) * 0.5 * env(m, 0.015, 0.02)
        elif kind == 'b':
            x = RNG.standard_normal(m)
            seg = biquad_bp(x, p0, 1500) * env(m, 0.002, dur * 0.8) * 0.8
        out[k:k + m] += seg
        k += m
    out = highpass(out, 70)
    return out / (np.abs(out).max() + 1e-9) * gain


def come_here(gain):
    return speak([('b', 0.03, 1800, 0), ('v', 0.16, 'u', 'u'), ('n', 0.1, 'm', 'm'), ('s', 0.05, 0, 0),
                  ('f', 0.07, 1400, 0), ('v', 0.34, 'i', 'r')], (150, 125), gain=gain, breath=0.05)


def here(gain):
    return speak([('f', 0.07, 1400, 0), ('v', 0.36, 'i', 'r')], (175, 120), gain=gain, breath=0.05)


def its_all_right(gain):
    return speak([('v', 0.09, 'i', 'i'), ('b', 0.02, 4000, 0), ('f', 0.08, 6000, 0), ('v', 0.2, 'o', 'o'),
                  ('v', 0.08, 'l', 'l'), ('v', 0.1, 'r', 'r'), ('v', 0.26, 'ai1', 'ai2'), ('b', 0.04, 3500, 0)],
                 (128, 92), gain=gain, breath=0.35)


def come_in(gain):
    return speak([('b', 0.03, 1800, 0), ('v', 0.13, 'u', 'u'), ('n', 0.08, 'm', 'm'), ('v', 0.2, 'i', 'i'),
                  ('n', 0.2, 'n', 'n')], (125, 98), gain=gain, breath=0.35)


def growl(dur, gain):
    n = int(dur * SR)
    x = RNG.standard_normal(n)
    rate = 24 + 4 * np.clip(lowpass(RNG.standard_normal(n), 3) * 30, -1, 1)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    y = biquad_bp(x, 220, 160) + 0.5 * biquad_bp(x, 520, 250)
    y = y * am * env(n, 0.12, 0.25)
    return y / (np.abs(y).max() + 1e-9) * gain


def rustle(dur, gain, fc=3200):
    n = int(dur * SR)
    x = RNG.standard_normal(n)
    am = np.clip(lowpass(np.abs(RNG.standard_normal(n)), 30) * 3, 0, 1.5)
    y = biquad_bp(x, fc, fc * 0.8) * am * env(n, 0.05, 0.1)
    return y / (np.abs(y).max() + 1e-9) * gain


def knock(gain, f=150, dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * tt * (1 - 0.15 * tt)) * np.exp(-tt * 18)
    click = biquad_bp(RNG.standard_normal(n), 2200, 1200) * np.exp(-tt * 120)
    y = body + 0.6 * click
    return y / (np.abs(y).max() + 1e-9) * gain


def creak(dur, gain, f0=380, f1=720):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.linspace(f0, f1, n) * (1 + 0.04 * np.sin(2 * np.pi * 7 * tt))
    ph = np.cumsum(f / SR)
    pulse = (np.sin(2 * np.pi * ph) > 0.92).astype(float)        # stick-slip pulses
    y = biquad_bp(pulse, f * 2.0, 120) + 0.5 * biquad_bp(pulse, f * 3.1, 200)
    y = y * env(n, 0.05, 0.2)
    return y / (np.abs(y).max() + 1e-9) * gain


def step_sound(gain, claw=True):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    pad = np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 60)
    y = pad
    if claw:
        y = y + 0.8 * biquad_bp(RNG.standard_normal(n), 4200 + RNG.uniform(-500, 500), 2000) * np.exp(-tt * 300)
    return y / (np.abs(y).max() + 1e-9) * gain


def sigh(dur, gain):
    n = int(dur * SR)
    x = RNG.standard_normal(n)
    y = biquad_bp(x, 700, 600) + 0.4 * biquad_bp(x, 1600, 900)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    y = y * e
    return y / (np.abs(y).max() + 1e-9) * gain


def mix_at(buf, t, sig):
    i = int(t * SR)
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def build():
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    tl = pickle.load(open(os.path.join(CACHE, 'timeline.pkl'), 'rb'))
    room = np.zeros(n)
    # dusk crickets: a few chirping voices, each a 4-5 kHz tone pulsed in triplets
    for c in range(4):
        fc = 4300 + 350 * c
        rate = 1.6 + 0.4 * c
        ph = (tt * rate + c * 0.31) % 1.0
        trip = ((ph < 0.16) & ((ph * 40) % 2 < 1.0)).astype(float)
        trip = lowpass(trip, 400)
        tone = np.sin(2 * np.pi * fc * tt) * trip
        gate = (lowpass(RNG.standard_normal(n), 0.08) * 30 > -0.2).astype(float)
        room += tone * lowpass(gate, 2) * (0.6 if c % 2 else 1.0)
    wind = lowpass(lowpass(RNG.standard_normal(n), 220), 220) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 11.0))
    room = room / (np.abs(room).max() + 1e-9) * db(-36) + wind / (np.abs(wind).max() + 1e-9) * db(-34)
    voice = np.zeros(n); fx = np.zeros(n)
    # the calls: loud, with the lion under them
    c1 = come_here(db(-8)); mix_at(voice, 1.02, c1); mix_at(fx, 1.0, growl(1.2, db(-20)))
    mix_at(voice, 1.75, here(db(-9)))
    c2 = come_here(db(-6)); mix_at(voice, 3.42, c2); mix_at(fx, 3.4, growl(1.3, db(-16)))
    mix_at(voice, 4.05, here(db(-7)))
    mix_at(fx, 3.45, rustle(0.9, db(-22)))                         # the pasted hand swelling
    # the lion leaves the head: paper flutter, then the stone knock in the keystone
    mix_at(fx, 5.45, rustle(0.6, db(-26), fc=2400))
    mix_at(fx, 6.04, knock(db(-14), f=95, dur=0.6))
    # the person's footsteps to the chair and the chair taking the weight
    for e in tl['person_events']:
        mix_at(fx, e[0] / 24.0, knock(db(-24), f=80, dur=0.25))
    mix_at(fx, 6.55, creak(0.5, db(-28), 300, 420))
    # the door: hinge creak, then the warm chord of the light (sustained, swelling at "come in")
    mix_at(fx, 6.2, creak(0.9, db(-20)))
    warm = np.zeros(n)
    for f, a in ((110, 1.0), (164.8, 0.6), (220, 0.45), (329.6, 0.2)):
        warm += a * np.sin(2 * np.pi * f * tt + RNG.uniform(0, 6)) * (1 + 0.1 * np.sin(2 * np.pi * 0.17 * tt * (1 + f / 400)))
    wenv = np.clip((tt - 6.3) / 1.2, 0, 1) * (0.8 + 0.2 * np.clip((tt - 26.4) / 1.0, 0, 1) - 0.2 * np.clip((tt - 28.4) / 2.0, 0, 1))
    warm = warm / np.abs(warm).max() * wenv * db(-30)
    # the soft voice
    s1 = its_all_right(db(-17)); mix_at(voice, 7.46, s1)
    mix_at(voice, 10.46, its_all_right(db(-18)))
    mix_at(voice, 26.42, come_in(db(-17)))
    # the dog: a claw tick and a pad on the boards at every touchdown
    for (i, k, dist) in tl['dog_events']:
        t = i / 24.0
        p = tl['dog'][i]
        if dist < 0.03:
            continue
        g = -31 if p['state'] == 'approach' else -28
        if p['lie'] > 0.3:
            g = -36
        mix_at(fx, t, step_sound(db(g), claw=p['lie'] < 0.5))
    # lying down: a soft thump and a sigh (refusal, at 4.4; at the sill, 23.9); settling after "come in"
    mix_at(fx, 4.55, knock(db(-28), f=70, dur=0.4)); mix_at(fx, 4.7, sigh(0.9, db(-32)))
    mix_at(fx, 24.05, knock(db(-28), f=70, dur=0.4)); mix_at(fx, 24.2, sigh(1.0, db(-31)))
    mix_at(fx, 28.4, sigh(1.6, db(-31)))
    # the tail knocking the boards while it looks in (wag extremes, 26.5 - 28.1)
    for k in range(int(26.55 * 2 * 2.3), int(28.1 * 2 * 2.3)):
        t = (k + 0.25) / (2 * 2.3)
        mix_at(fx, t, knock(db(-30), f=120, dur=0.12))
    mix = room + voice + fx + warm
    levels = measure(voice, room, [(1.02, c1), (3.42, c2)], [(7.46, s1)], mix)
    peak = np.abs(mix).max()
    g = 0.95 / peak if peak > 0.95 else 1.0
    mix = mix * g
    levels['mix_gain_db'] = round(float(20 * np.log10(g)), 2)
    levels['absolute_levels_note'] = 'the levels above are before the final mix gain; add mix_gain_db for the film'
    levels['mix_peak'] = round(float(np.abs(mix).max()), 3)
    return mix, levels


def rms_db(x):
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def measure(voice, room, calls, softs, mix):
    """measured (not assumed) levels: RMS over the voiced part of each utterance, and the room tone alone."""
    def utt(t, sig):
        i = int(t * SR)
        seg = voice[i:i + len(sig)]
        a = np.abs(seg); thr = a.max() * 0.05
        return seg[a > thr] if (a > thr).any() else seg
    lc = [rms_db(utt(t, s)) for t, s in calls]
    ls = [rms_db(utt(t, s)) for t, s in softs]
    i0, i1 = int(12.0 * SR), int(14.5 * SR)
    lr = rms_db(room[i0:i1])
    return {'call_rms_db': lc, 'soft_rms_db': ls, 'room_tone_rms_db': lr,
            'soft_minus_call_db': round(max(ls) - min(lc), 2), 'soft_minus_room_db': round(min(ls) - lr, 2),
            'note': 'RMS of the voice track over samples above 5% of the utterance peak; room tone over 12.0-14.5 s.'}


def write_wav(path, x, pad_before=3.0, pad_after=3.0, fade_room=None):
    pre = np.zeros(int(pad_before * SR)); post = np.zeros(int(pad_after * SR))
    y = np.concatenate([pre, x, post])
    st = np.stack([y, y], axis=1)
    data = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == '__main__':
    mix, lv = build()
    # title card: room tone fades in over the last 1.5 s; end card: the warmth and the crickets fade out
    n = len(mix)
    write_wav(os.path.join(CACHE, 'scene.wav'), mix)
    json.dump(lv, open(os.path.join(CACHE, 'audio_levels.json'), 'w'), indent=1)
    print(json.dumps(lv, indent=1))
