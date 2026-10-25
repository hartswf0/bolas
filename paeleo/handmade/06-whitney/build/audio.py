"""SCION 06 · Whitney — the audio synchronizer. Everything audible is synthesized here from the same oscillator bank.

  house tone   220 Hz harmonic tone, pulsing at the house oscillator (0.4 Hz): the 2 of the 3:2
  dog tone     330 Hz * (the dog oscillator's instantaneous rate / 0.6 Hz), pulsing at the dog's breath: the 3 of the 3:2.
               Locked, the two make a pure fifth and a 3-against-2 pulse; detuned (the calls), the fifth beats and the
               pulses slide.
  voice        additive formant synthesis (a bank of harmonics of f0 weighted by vowel formants), plus noise consonants.
               Calls loud and high; the soft voice >= 6 dB quieter, breathy, low.
  footfalls    a soft tick at each frame where a drawn foot goes from swing to stance (from trace.json)
  room tone    filtered noise and a 55 Hz hum, far below everything
Writes build/cache/audio.wav (38 s: 3 s title, 32 s scene, 3 s card) and proof/audio.json (measured levels).
"""
import json, math, os, wave
import numpy as np
import harmonic as H

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SR = 48000
PRE, SCENE, POST = 3.0, 32.0, 3.0
NT = int(SR * (PRE + SCENE + POST))
rng = np.random.default_rng(606)


def tt(n):
    return np.arange(n) / SR


def interp_frames(a):
    """per-frame array (24 fps, scene time) -> per-sample array over the whole film."""
    ts = PRE + np.arange(len(a)) / 24
    return np.interp(tt(NT), ts, a, left=a[0], right=a[-1])


def bandnoise(n, lo, hi):
    x = rng.standard_normal(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def formant_gain(f, F):
    g = np.zeros_like(f)
    for k, (Fi, Bi) in enumerate(F):
        g += (1.0 / (1 + ((f - Fi) / Bi) ** 2)) * (1.0, 0.55, 0.3)[k]
    return g


VOWEL = {'a': [(640, 90), (1190, 110), (2390, 160)], 'i': [(400, 70), (1950, 120), (2600, 170)],
         'e': [(500, 80), (1500, 110), (2500, 160)], 'o': [(570, 80), (840, 90), (2410, 160)],
         'ai': [(730, 90), (1090, 110), (2440, 160)], 'n': [(280, 60), (1300, 200), (2500, 200)]}


def syllable(dur, f0a, f0b, va, vb, breath=0.08, tilt=1.0):
    """an additive voice: harmonics of a gliding f0, weighted by formants that glide from vowel va to vb."""
    n = int(dur * SR); t = tt(n); s = t / dur
    f0 = f0a * (1 - s) + f0b * s + 4 * np.sin(2 * math.pi * 5.2 * t) * s   # a little vibrato at the end
    ph = 2 * math.pi * np.cumsum(f0) / SR
    y = np.zeros(n)
    Fa, Fb = VOWEL[va], VOWEL[vb]
    for k in range(1, 36):
        fk = k * f0
        if np.all(fk > 7000):
            break
        g = (1 - s) * formant_gain(fk, Fa) + s * formant_gain(fk, Fb)
        y += g * np.sin(k * ph) / k ** (0.6 * tilt)
    env = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.09) ** 1.2
    y = y * env
    if breath:
        y += breath * bandnoise(n, 400, 4000) * env * np.abs(y).max()
    return y / (np.abs(y).max() + 1e-9)


def consonant(kind, dur):
    n = int(dur * SR); t = tt(n)
    if kind == 'k':
        return bandnoise(n, 1500, 4000) * np.exp(-t / 0.012)
    if kind == 'h':
        return bandnoise(n, 500, 3000) * np.sin(math.pi * t / dur) * 0.5
    if kind == 's':
        return bandnoise(n, 4500, 9000) * np.sin(math.pi * t / dur) * 0.6
    if kind == 't':
        return bandnoise(n, 3000, 7000) * np.exp(-t / 0.008)
    return np.zeros(n)


def place(buf, t0, sig, gain, pan):
    i0 = int(t0 * SR); n = min(len(sig), NT - i0)
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i0:i0 + n] += sig[:n] * gain * l
    buf[1, i0:i0 + n] += sig[:n] * gain * r


def voice(buf):
    """the person's words, at the times of the renderer's VOICE table (scene time + PRE)."""
    CALL, SOFT = 0.50, 0.16           # peak gains (soft is ~10 dB below the calls)
    P = -0.55                         # the person is on the left
    events = []
    # Come here! (twice): k + 'a' (come), h + i->e (here), loud, f0 high and rising-falling
    for t0 in (1.05, 3.45):
        events += [(t0, consonant('k', 0.04), CALL * 0.7), (t0 + 0.03, syllable(0.26, 250, 235, 'a', 'n', 0.04), CALL),
                   (t0 + 0.33, consonant('h', 0.07), CALL * 0.5), (t0 + 0.38, syllable(0.52, 300, 210, 'i', 'e', 0.04), CALL)]
    # It's all right. (twice) soft: low f0, breathy, slow
    for t0 in (7.50, 10.50):
        events += [(t0, syllable(0.14, 175, 170, 'i', 'i', 0.35), SOFT), (t0 + 0.13, consonant('s', 0.09), SOFT * 0.4),
                   (t0 + 0.24, syllable(0.32, 180, 165, 'o', 'o', 0.35), SOFT),
                   (t0 + 0.60, syllable(0.55, 172, 140, 'ai', 'i', 0.35), SOFT), (t0 + 1.13, consonant('t', 0.03), SOFT * 0.3)]
    # Come in. soft
    t0 = 26.45
    events += [(t0, consonant('k', 0.03), SOFT * 0.5), (t0 + 0.03, syllable(0.28, 178, 168, 'a', 'n', 0.3), SOFT),
               (t0 + 0.35, syllable(0.48, 175, 140, 'i', 'n', 0.3), SOFT)]
    v = np.zeros((2, NT))
    for t0, sig, g in events:
        place(v, PRE + t0, sig, g, P)
    buf += v
    return v


def tones(buf, B):
    t = tt(NT)
    th_h = interp_frames(np.unwrap(B['th_house'])); th_d = interp_frames(np.unwrap(B['th_dog']))
    dens = interp_frames(B['density'])
    press = interp_frames(B['press'])
    light = interp_frames(H.door(None, B)['light'])
    scene = ((t >= PRE) & (t < PRE + SCENE)).astype(float)
    fade = np.clip((t - PRE + 0.5) / 1.5, 0, 1) * np.clip((PRE + SCENE + 1.5 - t) / 2.0, 0, 1)
    # the house tone: phase = 220 Hz carrier; its pulse follows the house oscillator
    ph_h = 2 * math.pi * 220 * t
    house = sum(np.sin(k * ph_h) / k ** 1.3 for k in (1, 2, 3, 4))
    pulse_h = (0.5 + 0.5 * np.cos(th_h)) ** 2
    lvl_h = (0.020 + 0.050 * light) * fade
    # the dog tone: its carrier rate is 330 Hz scaled by the dog oscillator's instantaneous rate over 0.6 Hz
    rate = np.gradient(th_d) * SR / (2 * math.pi)
    ph_d = 2 * math.pi * np.cumsum(330 * rate / 0.6) / SR
    dog = sum(np.sin(k * ph_d) / k ** 1.5 for k in (1, 2, 3))
    pulse_d = (0.5 + 0.5 * np.cos(th_d)) ** 2
    lvl_d = (0.012 + 0.045 * dens + 0.02 * press) * fade
    mono = house * pulse_h * lvl_h + dog * pulse_d * lvl_d
    # the reunion bloom at 24 s (rings align as the dog lies down): octave and twelfth, slowly
    bl = np.exp(-((t - (PRE + 24.1)) / 1.3) ** 2)
    mono += bl * 0.035 * (np.sin(2 * math.pi * 440 * t) + 0.6 * np.sin(2 * math.pi * 660 * t))
    # release: the field thins; let the bed fall
    mono *= 1 - 0.5 * np.clip((t - (PRE + 28.6)) / 3.0, 0, 1)
    # duck the bed under the soft voice (it must sit clearly above it): -14 dB from 0.6 s before each soft line to its end
    duck = np.ones(NT)
    for on, dur in SOFT_LINES:
        a0, a1 = PRE + on - 0.6, PRE + on - 0.15
        b0, b1 = PRE + on + dur + 0.1, PRE + on + dur + 0.7
        g = np.clip((t - a0) / (a1 - a0), 0, 1) * (1 - np.clip((t - b0) / (b1 - b0), 0, 1))
        duck = np.minimum(duck, 1 - 0.8 * g)
    mono = mono * duck
    buf[0] += mono * 0.95; buf[1] += mono * 1.05
    return mono


SOFT_LINES = [(7.50, 1.25), (10.50, 1.25), (26.45, 0.85)]


def door_sound(buf):
    # a slow creak: a gliding harmonic rasp 6.2 -> 7.0 s
    n = int(0.8 * SR); t = tt(n)
    f0 = 90 + 60 * t / 0.8 + 8 * np.sin(2 * math.pi * 23 * t)
    ph = 2 * math.pi * np.cumsum(f0) / SR
    sig = sum(np.sin(k * ph) * (1 / k) for k in range(1, 12)) * np.sin(math.pi * t / 0.8) ** 0.7
    sig *= 0.6 + 0.4 * np.sign(np.sin(2 * math.pi * 31 * t))
    place(buf, PRE + 6.2, sig / np.abs(sig).max(), 0.035, -0.5)


def footfalls(buf, trace):
    fr = trace['frames']; prev = None; n = 0
    for f in fr:
        cur = set(f['feet_planted'])
        if prev is not None:
            for leg in cur - prev:
                if f['state'] in ('retreat', 'approach', 'watch'):
                    tl = tt(int(0.09 * SR))
                    tick = bandnoise(len(tl), 300, 2500) * np.exp(-tl / 0.012) * 0.6 + np.sin(2 * math.pi * 660 * tl) * np.exp(-tl / 0.03) * 0.4
                    pan = float(np.clip((f['x_screen'] - 640) / 640, -1, 1))
                    place(buf, PRE + f['t'], tick, 0.05 if leg.endswith('F') else 0.04, pan); n += 1
        prev = cur
    return n


def body_sounds(buf):
    # lying down on the sill: a soft thump and a sigh; and the settle at 28.6 s
    for t0, g in ((24.25, 0.06), (4.75, 0.035)):
        tl = tt(int(0.25 * SR))
        thump = np.sin(2 * math.pi * 70 * tl) * np.exp(-tl / 0.06)
        place(buf, PRE + t0, thump, g, -0.1)
    for t0, g in ((25.0, 0.03), (28.7, 0.035)):
        tl = tt(int(1.1 * SR))
        sig = bandnoise(len(tl), 300, 1800) * np.sin(math.pi * tl / 1.1) ** 1.5
        place(buf, PRE + t0, sig, g, -0.1)


def room(buf):
    n = NT
    x = bandnoise(n, 40, 900)
    t = tt(n)
    hum = 0.3 * np.sin(2 * math.pi * 55 * t)
    r = (x + hum) * 0.0045
    buf[0] += r; buf[1] += r
    return r


def rms_db(x):
    return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


def main():
    S = H.load_score(); B = H.bank(S)
    trace = json.load(open(os.path.join(OUT, 'trace.json')))
    buf = np.zeros((2, NT))
    r = room(buf)
    m = tones(buf, B)
    door_sound(buf)
    nf = footfalls(buf, trace)
    body_sounds(buf)
    v = voice(buf)
    peak = np.abs(buf).max()
    if peak > 0.95:
        buf *= 0.95 / peak
        v *= 0.95 / peak; r *= 0.95 / peak
    # measurements: active-voice RMS per utterance (samples where the voice envelope is > -30 dB of its peak)
    meas = {}
    vm = v.mean(0)
    for name, a, b in (('call_1', 1.0, 2.0), ('call_2', 3.4, 4.4), ('soft_1', 7.5, 8.8), ('soft_2', 10.5, 11.7), ('soft_come_in', 26.45, 27.3)):
        seg = vm[int((PRE + a) * SR):int((PRE + b) * SR)]
        env = np.abs(seg)
        act = seg[env > env.max() * 0.03]
        meas[name] = round(rms_db(act), 2)
    meas['room_tone_alone'] = round(rms_db(r), 2)
    full = buf.mean(0)
    meas['mix_quiet_window_13.0-14.5s'] = round(rms_db(full[int((PRE + 13) * SR):int((PRE + 14.5) * SR)]), 2)
    meas['soft_minus_loudest_call_dB'] = round(max(meas['soft_1'], meas['soft_2'], meas['soft_come_in']) - min(meas['call_1'], meas['call_2']), 2)
    meas['footfall_ticks'] = nf
    # 1-3 kHz band: each soft line against the mix in the 0.5 s before it
    def band_db(x):
        X = np.fft.rfft(x * np.hanning(len(x))); f = np.fft.rfftfreq(len(x), 1 / SR)
        m = (f >= 1000) & (f <= 3000)
        return 10 * math.log10(np.sum(np.abs(X[m]) ** 2) / len(x) + 1e-20)
    for k, (on, dur) in enumerate(SOFT_LINES):
        seg = full[int((PRE + on) * SR):int((PRE + on + dur) * SR)]
        pre = full[int((PRE + on - 0.5) * SR):int((PRE + on) * SR)]
        meas['soft%d_band1-3k_over_bed_before_dB' % (k + 1)] = round(band_db(seg) - band_db(pre), 2)
    meas['note'] = 'RMS in dBFS of the voice stem alone over its active samples; the soft voice must be >= 6 dB below the calls and above the room tone.'
    json.dump(meas, open(os.path.join(OUT, 'proof', 'audio.json'), 'w'), indent=1)
    print(meas)
    pcm = (np.clip(buf, -1, 1) * 32767).astype('<i2').T.copy()
    with wave.open(os.path.join(HERE, 'cache', 'audio.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    main()
