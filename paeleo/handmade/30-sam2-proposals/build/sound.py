"""Sound for SCION 30: everything synthesized here (flite voice via ffmpeg, numpy for the rest).
Calls are loud and close; the soft voice is mixed at least 6 dB under them; every voice starts at or before the dog's
reaction. Paw ticks fire only on frames where the walk proposal changes (the sound is tied to the substitution)."""
import json, os, subprocess, wave
import numpy as np
from common import CACHE, SCORE, jdump
import render

SR = 48000
DUR = 38.0
OFF = 3.0            # scene starts after the 3 s title
rng = np.random.default_rng(3030)

VOICES = [  # (scene time, text, kind) -- start times precede the reactions at 1.00, 3.42, 7.46, 26.4
    (0.70, 'Come here.', 'call'),
    (3.05, 'Come here!', 'call'),
    (7.05, "It's all right.", 'soft'),
    (10.40, "It's all right.", 'soft'),
    (25.95, 'Come in.', 'soft'),
]


def flite(text, path):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', "flite=text='%s':voice=slt" % text.replace("'", "’"),
                    '-ar', str(SR), '-ac', '1', path], check=True)
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.


def lowpass(x, a):
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a * (x[i] - s); y[i] = s
    return y


def onepole(x, a):
    # vectorised enough for short signals: use cumulative filter via scipy-free recursion in chunks
    return lowpass(x, a)


def put(buf, sig, t):
    i = int(t * SR)
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def main():
    n = int(DUR * SR)
    mix = np.zeros(n, np.float32)
    # room tone at dusk: brown-ish noise + sparse crickets, scene only
    wn = rng.normal(0, 1, n).astype(np.float32)
    brown = np.cumsum(wn); brown -= np.convolve(brown, np.ones(4800) / 4800, 'same'); brown /= np.abs(brown).max()
    tone = brown * 0.010
    t = np.arange(n) / SR
    for k in range(70):
        c = rng.uniform(OFF, OFF + 32); f = rng.uniform(4300, 4900)
        L = int(.045 * SR); tt = np.arange(L) / SR
        chirp = np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / tt[-1]) ** 2 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * tt)))
        for r in range(3):
            put(tone, chirp * 0.006, c + r * .07)
    env = ((t >= OFF) & (t < OFF + 32)).astype(np.float32)
    ramp = np.clip(np.minimum(t - OFF, OFF + 32 - t) / .4, 0, 1)
    mix += tone * env * ramp
    # voices
    levels = {'call': 0.62, 'soft': 0.20}
    meas = []
    for k, (ts, text, kind) in enumerate(VOICES):
        v = flite(text, os.path.join(CACHE, 'voice_%d.wav' % k))
        v = v / (np.abs(v).max() + 1e-6) * levels[kind]
        if kind == 'soft':
            v = lowpass(v, 0.35)                       # softer, breathier
            v = v / (np.abs(v).max() + 1e-6) * levels[kind]
        put(mix, v, OFF + ts)
        rms = float(np.sqrt(np.mean(v[np.abs(v) > .01 * levels[kind]] ** 2)))
        meas.append(dict(t=ts, text=text, kind=kind, peak_db=round(float(20 * np.log10(np.abs(v).max())), 2), rms_db=round(20 * np.log10(rms), 2),
                         dur=round(len(v) / SR, 2)))
    # door: a slow creak as it opens (6.2-7.1): jittered sawtooth through a resonance, plus latch click at 6.15
    L = int(.9 * SR); tt = np.arange(L) / SR
    f0 = 210 + 60 * np.sin(2 * np.pi * 1.3 * tt) + rng.normal(0, 8, L).cumsum() * .02
    ph = np.cumsum(f0) / SR
    saw = (ph % 1.0) * 2 - 1
    creak = lowpass(saw.astype(np.float32), .2) * np.sin(np.pi * tt / tt[-1]) * 0.07
    put(mix, creak, OFF + 6.2)
    click = rng.normal(0, 1, int(.012 * SR)).astype(np.float32) * np.exp(-np.arange(int(.012 * SR)) / 90.) * .12
    put(mix, click, OFF + 6.15)
    # paw ticks on the boards: one per walk-proposal change, retreat and approach
    prev = None
    for i in range(768):
        p = render.dog_plan(i)
        if p['posture'] in ('crouch-backing', 'walk-head-low'):
            if prev is not None and p['f'] != prev:
                Lk = int(.03 * SR)
                tick = rng.normal(0, 1, Lk).astype(np.float32) * np.exp(-np.arange(Lk) / 160.)
                tick = lowpass(tick, .5) * (0.05 if p['posture'] == 'walk-head-low' else 0.07)
                put(mix, tick, OFF + i / 24.)
            prev = p['f']
        else:
            prev = None
    # lying down: a soft body settle at 24.2 and an exhale at 24.9; settling again at 28.8
    for ts, a in ((24.2, .05), (28.8, .035)):
        Lk = int(.25 * SR)
        th = lowpass(rng.normal(0, 1, Lk).astype(np.float32), .04) * np.exp(-np.arange(Lk) / (SR * .07)) * a * 6
        put(mix, th, OFF + ts)
    for ts in (24.9, 29.2):
        Lk = int(.9 * SR); tt = np.arange(Lk) / SR
        br = lowpass(rng.normal(0, 1, Lk).astype(np.float32), .12) * np.sin(np.pi * tt / tt[-1]) ** 1.5 * .035
        put(mix, br, OFF + ts)
    # end card: a low single tone fading
    Lk = int(2.6 * SR); tt = np.arange(Lk) / SR
    put(mix, (np.sin(2 * np.pi * 110 * tt) * .03 + np.sin(2 * np.pi * 165 * tt) * .015) * np.exp(-tt / 1.2) * np.clip(tt / .05, 0, 1), OFF + 32.2)
    mix = np.clip(mix, -.98, .98)
    with wave.open(os.path.join(CACHE, 'sound.wav'), 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    room = float(20 * np.log10(np.sqrt(np.mean((tone * env)[int((OFF + 15) * SR):int((OFF + 20) * SR)] ** 2)) + 1e-9))
    calls = [m['rms_db'] for m in meas if m['kind'] == 'call']; softs = [m['rms_db'] for m in meas if m['kind'] == 'soft']
    rep = dict(voices=meas, room_tone_rms_db=round(room, 2), soft_minus_call_db=round(max(softs) - min(calls), 2))
    jdump(rep, os.path.join(CACHE, 'sound_levels.json'))
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
