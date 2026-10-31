"""SCION 31 sound, synthesized with numpy (no samples): dusk air, crickets, a synthesized voice (additive harmonics shaped
by formants: calls, soft words), claws on porch boards placed at the walk-frame changes measured in the render trace,
the door's creak and the room's warm air when it opens, the person's rustle, the dog lying down and its sigh.
Writes build/cache/scene.wav (32 s, the scene) and build/cache/sound_levels.json (measured RMS in dBFS)."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache')
SR = 48000
DUR = 32.0
N = int(SR * DUR)
R = np.random.default_rng(31)
SCORE = json.load(open(os.path.join(HERE, '../../score/threshold-score.json')))


def bandnoise(n, lo, hi, seed=None):
    r = R if seed is None else np.random.default_rng(seed)
    X = np.fft.rfft(r.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    X *= ((f >= lo) & (f <= hi)) * 1.0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))


def add(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 >= len(buf): return
    n = min(len(sig), len(buf) - i0)
    buf[i0:i0 + n] += sig[:n] * gain


def formant_gain(f, F):
    g = np.zeros_like(f)
    for fc, bw, amp in F:
        g += amp / (1 + ((f - fc) / (bw / 2)) ** 2)
    return g


def voice(segs, f0_start, f0_end, breath=0.0):
    """segs: list of (dur, F_from, F_to, voiced_amp, noise_amp, noise_band). F = [(fc, bw, amp), ...] formants."""
    out = []
    for dur, Fa, Fb, va, na, band in segs:
        n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
        y = np.zeros(n)
        if va > 0:
            f0 = f0_start + (f0_end - f0_start) * u + 3 * np.sin(2 * np.pi * 5.5 * t)
            ph = 2 * np.pi * np.cumsum(f0) / SR
            for k in range(1, 28):
                fk = k * f0
                Fi = [(a[0] + (b[0] - a[0]) * u, a[1], a[2] + (b[2] - a[2]) * u) for a, b in zip(Fa, Fb)]
                g = np.zeros(n)
                for fc, bw, amp in Fi:
                    g += amp / (1 + ((fk - fc) / (bw / 2)) ** 2)
                g *= (fk < 5000) / k ** .6
                y += g * np.sin(k * ph)
            y *= va
        if na > 0:
            y += na * bandnoise(n, band[0], band[1]) * np.hanning(n) ** .5
        if breath > 0 and va > 0:
            y += breath * bandnoise(n, 400, 3500) * .5
        sm = np.minimum(1, np.minimum(t / .02, (dur - t) / .03))
        out.append(y * np.clip(sm, 0, 1))
    return np.concatenate(out)


A_ = [(750, 120, 1.0), (1200, 140, .55), (2600, 200, .2)]      # /ʌ/
M_ = [(250, 80, 1.0), (1100, 300, .08), (2200, 300, .05)]      # /m/ nasal
I_ = [(420, 90, 1.0), (2000, 160, .5), (2700, 200, .25)]       # /ɪ/
E_ = [(520, 110, 1.0), (1500, 150, .45), (2500, 200, .2)]      # /ə/
O_ = [(600, 100, 1.0), (900, 130, .6), (2500, 200, .12)]       # /ɔ/
AI = [(800, 120, 1.0), (1300, 140, .5), (2500, 200, .2)]       # /a/
N_ = [(260, 80, 1.0), (1500, 300, .06), (2500, 300, .05)]      # /n/


def come_here(force=1.0):
    return voice([(.05, A_, A_, 0, .9 * force, (1500, 4000)),          # k burst
                  (.16, A_, A_, 1, 0, None), (.09, A_, M_, 1, 0, None),   # cʌm
                  (.06, M_, M_, .7, 0, None),
                  (.07, E_, E_, 0, .35, (500, 3000)),                 # h
                  (.30, I_, E_, 1, 0, None)], 205 * force ** .2, 175 + 40 * (force - 1), breath=.02)


def its_all_right():
    return voice([(.08, I_, I_, .8, 0, None), (.06, I_, I_, 0, .4, (4000, 8000)),     # it-s
                  (.20, O_, O_, 1, 0, None), (.08, O_, E_, .8, 0, None),             # all
                  (.06, E_, E_, .5, 0, None), (.26, AI, I_, 1, 0, None),             # r-ight
                  (.03, I_, I_, 0, .3, (2000, 5000))], 185, 150, breath=.18)


def come_in():
    return voice([(.05, A_, A_, 0, .5, (1500, 4000)), (.15, A_, M_, 1, 0, None), (.05, M_, M_, .6, 0, None),
                  (.24, I_, N_, 1, 0, None), (.08, N_, N_, .6, 0, None)], 180, 150, breath=.2)


def claw(seed, hard=1.0):
    n = int(.05 * SR)
    s = bandnoise(n, 1800, 9000, seed) * env(n, .001, .008) * .6 + bandnoise(n, 120, 600, seed + 1) * env(n, .002, .02) * .5
    return s * hard


def creak(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 180 + 90 * np.sin(2 * np.pi * .7 * t) + 40 * R.standard_normal(n).cumsum() / np.sqrt(np.arange(n) + 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    stick = (np.sin(2 * np.pi * (14 + 6 * t) * t) > .2).astype(float)
    y = (np.sin(ph) + .5 * np.sin(2 * ph) + .3 * np.sin(3.1 * ph)) * (.4 + .6 * stick)
    return y * np.hanning(n)


def main():
    tr = json.load(open(os.path.join(C, 'render_trace.json')))
    L = np.zeros(N)
    # dusk air: low wind + distant hush, and crickets that thicken as it gets darker
    air = bandnoise(N, 40, 900, 1) * .5 + bandnoise(N, 900, 4000, 2) * .08
    air *= .9 + .1 * np.sin(2 * np.pi * np.arange(N) / SR / 7.3)
    L += air * 10 ** (-38 / 20)
    t = np.arange(N) / SR
    for k, (fc, rate) in enumerate([(4300, 13), (4700, 11.5), (3900, 15)]):
        chirp = np.sin(2 * np.pi * fc * t) * (np.sin(2 * np.pi * rate * t) > .55) * (np.sin(2 * np.pi * (.45 + .1 * k) * t + k) > 0)
        L += chirp * 10 ** (-50 / 20) * np.clip(t / 20 + .3, 0, 1) * (.6 + .4 * k / 2)
    # the voice: calls are loud; soft words at least 6 dB below (measured below)
    CALL_G, SOFT_G = 10 ** (-12 / 20), 10 ** (-24 / 20)
    marks = {}
    v = come_here(1.0); add(L, v, 0.62, CALL_G / np.abs(v).max()); marks['call_1'] = (0.62, 0.62 + len(v) / SR)
    v = come_here(1.25); add(L, v, 2.95, CALL_G * 1.12 / np.abs(v).max()); marks['call_2'] = (2.95, 2.95 + len(v) / SR)
    v = come_here(1.1); add(L, v, 1.62, CALL_G * .9 / np.abs(v).max()); marks['call_1b'] = (1.62, 1.62 + len(v) / SR)
    for t0, name in [(7.10, 'soft_1'), (10.42, 'soft_2')]:   # round 4: 'it's all right' 0.36 s before the look-back at 7.46
        v = its_all_right(); add(L, v, t0, SOFT_G / np.abs(v).max()); marks[name] = (t0, t0 + len(v) / SR)
    v = come_in(); add(L, v, 25.85, SOFT_G * 1.05 / np.abs(v).max()); marks['come_in'] = (25.85, 25.85 + len(v) / SR)
    # claws on boards: one tick per walk-frame change measured in the render
    prev = None
    for i in range(768):
        p = tr[str(i)]['pose']
        f = p.get('f'); post = p.get('posture', '')
        if p.get('kind') == 'frame' and f != prev and post in ('back away', 'walk head low'):
            hard = 1.3 if post == 'back away' else 1.2
            add(L, claw(i, hard), i / 24. + R.uniform(0, .02), 10 ** (-24 / 20))
            if post == 'walk head low':   # a second paw lands half a step later
                add(L, claw(i + 500, .9), i / 24. + .09, 10 ** (-27 / 20))
            if post == 'back away':
                add(L, claw(i + 999, .8), i / 24. + .03, 10 ** (-34 / 20))
        if p.get('kind') == 'gait' and i > 0:      # backing away: a tick each time a paw is set down again
            q = tr[str(i - 1)]['pose']
            for k in ('fore', 'hind'):
                if q.get('kind') == 'gait' and p['legs'][k]['plant'] != q['legs'][k]['plant']:
                    add(L, claw(i * 3 + (k == 'fore'), 1.3), i / 24. + .02, 10 ** (-25 / 20))
        prev = f
    # the person: steps aside and sits (boards, cloth)
    for k, t0 in enumerate(np.arange(5.4, 6.3, .3)):
        n = int(.09 * SR); add(L, bandnoise(n, 80, 500, 50 + k) * env(n, .003, .04), t0, 10 ** (-28 / 20))
    n = int(.9 * SR); add(L, bandnoise(n, 800, 6000, 60) * np.hanning(n), 5.7, 10 ** (-40 / 20))
    n = int(.25 * SR); add(L, bandnoise(n, 60, 300, 61) * env(n, .01, .08), 6.35, 10 ** (-27 / 20))   # sits
    # the door: creak as it swings, then the room's warm air (light coming out, heard)
    c = creak(.8); add(L, c, 6.2, 10 ** (-27 / 20) / np.abs(c).max())
    room = (np.sin(2 * np.pi * 110 * t) * .3 + np.sin(2 * np.pi * 165 * t) * .15 + bandnoise(N, 100, 700, 70) * .5)
    L += room * np.clip((t - 6.4) / 1.2, 0, 1) * 10 ** (-42 / 20)
    # the dog lies down (refusal, then the sill): fur on wood; settles with a sigh
    for t0 in (4.45, 24.0):
        n = int(.45 * SR); add(L, bandnoise(n, 200, 3000, int(t0 * 10)) * np.hanning(n), t0, 10 ** (-36 / 20))
        n = int(.2 * SR); add(L, bandnoise(n, 50, 250, int(t0 * 10) + 1) * env(n, .01, .06), t0 + .35, 10 ** (-30 / 20))
    n = int(.9 * SR); sig = bandnoise(n, 300, 2500, 80) * env(n, .25, .35); add(L, sig, 28.55, 10 ** (-36 / 20))
    n = int(.5 * SR); add(L, bandnoise(n, 300, 2500, 81) * env(n, .1, .2), 5.95, 10 ** (-40 / 20))  # sigh, back turned
    # rises at 7.46: claws scrabble
    for k in range(3):
        add(L, claw(900 + k, .9), 7.62 + .07 * k, 10 ** (-33 / 20))
    L = np.clip(L, -1, 1)
    # measured levels
    def rms(a, b):
        s = L[int(a * SR):int(b * SR)]; return 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)
    lv = {k: round(rms(a, b), 2) for k, (a, b) in marks.items()}
    lv['room_tone_0.05_0.55'] = round(rms(.05, .55), 2)
    lv['room_tone_12.5_14.5'] = round(rms(12.5, 14.5), 2)
    lv['peak'] = round(20 * np.log10(np.abs(L).max()), 2)
    lv['calls_minus_soft_dB'] = round(min(lv['call_1'], lv['call_2']) - max(lv['soft_1'], lv['soft_2'], lv['come_in']), 2)
    lv['soft_minus_room_dB'] = round(min(lv['soft_1'], lv['soft_2'], lv['come_in']) - max(lv['room_tone_0.05_0.55'], lv['room_tone_12.5_14.5']), 2)
    lv['marks_s'] = {k: [round(a, 2), round(b, 2)] for k, (a, b) in marks.items()}
    json.dump(lv, open(os.path.join(C, 'sound_levels.json'), 'w'), indent=1)
    st = np.stack([L, L * .97], 1)
    with wave.open(os.path.join(C, 'scene.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32000).astype(np.int16).tobytes())
    print(json.dumps(lv))


if __name__ == '__main__':
    main()
