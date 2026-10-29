"""Sound, synthesized here (no recordings): a formant voice, boards, the door, the room, dusk insects.

Voice: a source-filter synthesizer. A glottal pulse train (with breath noise) at a pitch contour passes through three
time-varying formant resonators that move between phoneme targets; consonants are shaped noise bursts.
Events are timed from the score (voice: call / soft) and from the performance (paw plants, the door, the tail).
Writes build/cache/sound.wav (38.0 s, 48 kHz, title and end card included) and cache/sound_levels.json.
"""
import json, os, sys
import numpy as np
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, FPS

SR = 48000
VSR = 16000
OFF = 3.0            # the scene starts after the 3 s title
TOTAL = 38.0
rng = np.random.default_rng(34)

PH = {  # F1, F2, F3 (Hz), voiced, noise band (lo, hi) or None, relative amp
    'a': (850, 1500, 2900, 1, None, 1.0), 'V': (760, 1400, 2800, 1, None, 1.0), 'I': (430, 2250, 3000, 1, None, 0.9),
    'e': (600, 1600, 2800, 1, None, 0.85), 'O': (640, 1000, 2700, 1, None, 1.0), 'r': (460, 1300, 1700, 1, None, 0.7),
    'l': (380, 1100, 2800, 1, None, 0.6), 'm': (280, 1250, 2500, 1, None, 0.35), 'n': (280, 1700, 2600, 1, None, 0.35),
    'k': (500, 1800, 2800, 0, (1500, 3500), 0.6), 't': (500, 1800, 2800, 0, (3000, 6000), 0.45),
    's': (500, 1800, 2800, 0, (4000, 7800), 0.5), 'h': (700, 1600, 2800, 0, (500, 3500), 0.35),
    '_': (500, 1500, 2800, 0, None, 0.0),
}
PHRASES = {
    'Come here.': [('k', .06), ('V', .13), ('m', .09), ('h', .07), ('I', .16), ('e', .12), ('r', .14)],
    'Come here!': [('k', .06), ('V', .12), ('m', .08), ('h', .06), ('I', .18), ('e', .14), ('r', .16)],
    "It's all right.": [('I', .08), ('t', .04), ('s', .09), ('O', .16), ('l', .1), ('r', .07), ('a', .16), ('I', .1), ('t', .05)],
    'Come in.': [('k', .06), ('V', .12), ('m', .08), ('I', .16), ('n', .2)],
}


def resonator(x, f, bw, sr):
    """Two-pole resonator with a time-varying centre frequency f (array)."""
    y = np.zeros_like(x)
    r = np.exp(-np.pi * bw / sr)
    y1 = y2 = 0.0
    c2 = -r * r
    for i in range(len(x)):
        c1 = 2 * r * np.cos(2 * np.pi * f[i] / sr)
        v = (1 - r) * x[i] + c1 * y1 + c2 * y2
        y[i] = v; y2 = y1; y1 = v
    return y


def voice(text, f0, contour, breath=0.08, rate=1.0):
    seq = [(p, d / rate) for p, d in PHRASES[text]]
    dur = sum(d for _, d in seq) + 0.12
    n = int(dur * VSR)
    tt = np.arange(n) / VSR
    # targets per sample with smooth transitions (30 ms)
    keys = []
    t0 = 0.0
    for p, d in seq:
        keys.append((t0 + d / 2, p)); t0 += d
    F = np.zeros((3, n)); voiced = np.zeros(n); amp = np.zeros(n); nb = np.zeros((2, n)); namp = np.zeros(n)
    t0 = 0.0
    for p, d in seq:
        a = int(t0 * VSR); b = int((t0 + d) * VSR)
        f1, f2, f3, vo, band, am = PH[p]
        F[0, a:b], F[1, a:b], F[2, a:b] = f1, f2, f3
        voiced[a:b] = vo; amp[a:b] = am
        if band:
            nb[0, a:b], nb[1, a:b] = band; namp[a:b] = am
        t0 += d
    F[:, int(t0 * VSR):] = F[:, int(t0 * VSR) - 1:int(t0 * VSR)]
    k = int(0.03 * VSR)
    win = np.hanning(k) / np.hanning(k).sum()
    for j in range(3):
        F[j] = np.convolve(np.pad(F[j], (k, k), mode='edge'), win, 'same')[k:-k]
    voiced = np.convolve(voiced, win, 'same'); amp = np.convolve(amp, win, 'same'); namp = np.convolve(namp, np.ones(40) / 40, 'same')
    # pitch contour: contour(u) multiplies f0 over the phrase, plus a little jitter
    u = tt / dur
    pitch = f0 * contour(u) * (1 + 0.01 * np.sin(2 * np.pi * 5.3 * tt))
    ph = np.cumsum(pitch / VSR)
    saw = (ph % 1.0)
    glott = np.where(saw < 0.6, np.sin(np.pi * saw / 0.6) ** 2, 0.0)    # Rosenberg-like pulse
    glott = np.diff(glott, prepend=0) * 8
    src = glott * voiced + breath * rng.standard_normal(n) * voiced
    out = np.zeros(n)
    for j, bw in enumerate((90, 120, 180)):
        out += resonator(src, F[j], bw, VSR) * (1.0, 0.6, 0.35)[j]
    out *= amp
    # consonant noise
    noise = rng.standard_normal(n)
    sos_cache = {}
    nz = np.zeros(n)
    for lo, hi in {(int(a), int(b)) for a, b in zip(nb[0], nb[1]) if b > 0}:
        sos = signal.butter(4, [lo, min(hi, VSR / 2 - 100)], btype='band', fs=VSR, output='sos')
        sel = (nb[0] == lo) & (nb[1] == hi)
        nz[sel] = signal.sosfilt(sos, noise)[sel]
    out += nz * namp * 0.9
    env = np.minimum(1, np.minimum(tt / 0.015, (dur - tt) / 0.06))
    out *= np.clip(env, 0, 1)
    out = signal.resample_poly(out, SR // VSR, 1)
    return out / (np.abs(out).max() + 1e-9)


def place(buf, t, x, gain):
    a = int(t * SR)
    b = min(len(buf), a + len(x))
    if b > a:
        buf[a:b] += x[:b - a] * gain


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def bandnoise(dur, lo, hi, order=2):
    n = int(dur * SR)
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, rng.standard_normal(n))


def main():
    plan = json.load(open(os.path.join(CACHE, 'perform.json')))
    N = int(TOTAL * SR)
    amb = np.zeros(N); fx = np.zeros(N); vox = np.zeros(N)
    tt = np.arange(N) / SR
    # ---- dusk: wind in the trees (low band noise) and insects that thicken as it darkens
    wind = bandnoise(TOTAL, 80, 600)
    wind *= 0.6 + 0.4 * np.sin(2 * np.pi * tt / 9.0) ** 2
    amb += wind / np.abs(wind).max() * 0.010
    ins = np.zeros(N)
    for k in range(int(TOTAL * 1.6)):
        t0 = rng.uniform(OFF, TOTAL - 3.5)
        f = rng.uniform(4300, 4900)
        d = 0.05 + rng.uniform(0, 0.03)
        n = int(d * SR)
        tc = np.arange(n) / SR
        chirp = np.sin(2 * np.pi * f * tc) * (np.sin(2 * np.pi * 32 * tc) > 0) * np.hanning(n)
        place(ins, t0, chirp, 0.010 * (0.5 + (t0 - OFF) / 32))
    amb += ins
    # ---- the room: a warm hum and air that comes out with the light
    room = bandnoise(TOTAL, 90, 900) * 0.6 + 0.4 * np.sin(2 * np.pi * 120 * tt) * 0.05
    room /= np.abs(room).max()
    door_t = np.array([OFF + f['t'] for f in plan]); door_o = np.array([f['door_open'] for f in plan])
    open_amt = np.interp(tt, door_t, 0.12 + 0.88 * door_o, left=0.12, right=1.0)
    open_amt *= np.clip(np.minimum((tt - 0.5) / 1.5, (TOTAL - 0.5 - tt) / 1.5), 0, 1)
    amb += room * 0.013 * open_amt
    # ---- the door at 6.2: the latch, then a slow hinge creak
    tdo = OFF + 6.2
    click = bandnoise(0.03, 1500, 5000) * np.exp(-np.arange(int(0.03 * SR)) / (0.005 * SR))
    place(fx, tdo - 0.05, click, 0.25)
    n = int(0.9 * SR); tc = np.arange(n) / SR
    f = 240 + 140 * tc / 0.9 + 20 * np.sin(2 * np.pi * 7 * tc)
    creak = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * tc) ** 8)
    creak = signal.sosfilt(signal.butter(2, [400, 2400], btype='band', fs=SR, output='sos'), creak) * np.hanning(n)
    place(fx, tdo, creak, 0.06)
    # ---- the dog's paws on the boards: a tick when a swinging paw lands; the person's steps; the stool
    prev = {}
    for f in plan:
        for L, u in f['lifts'].items():
            if prev.get(L, 0) > 0 and u == 0:
                d = 0.025
                tk = bandnoise(d, 700, 3200) * np.exp(-np.arange(int(d * SR)) / (0.004 * SR))
                knock = np.sin(2 * np.pi * rng.uniform(170, 230) * np.arange(int(0.05 * SR)) / SR) * np.exp(-np.arange(int(0.05 * SR)) / (0.01 * SR))
                place(fx, OFF + f['t'], tk, 0.10); place(fx, OFF + f['t'], knock, 0.05)
            prev[L] = u
    for k in range(3):
        ts = OFF + 5.4 + (k + 0.6) * (0.95 / 3)
        st = bandnoise(0.08, 100, 900) * np.exp(-np.arange(int(0.08 * SR)) / (0.02 * SR))
        place(fx, ts, st, 0.14)
    stool = bandnoise(0.25, 300, 1400) * np.hanning(int(0.25 * SR))
    place(fx, OFF + 6.25, stool, 0.05)
    # the dog lies down (a breath out) at 4.7 and 24.3; its tail thumps the boards while it looks in
    for tb in (4.75, 24.35, 28.6):
        br = bandnoise(0.7, 300, 2500) * np.hanning(int(0.7 * SR)) ** 2
        place(fx, OFF + tb, br, 0.035)
    for k, f in enumerate(plan):
        if 26.7 <= f['t'] <= 28.3 and np.sin(f['acts']['wph']) > 0.95:
            th = np.sin(2 * np.pi * 95 * np.arange(int(0.07 * SR)) / SR) * np.exp(-np.arange(int(0.07 * SR)) / (0.015 * SR))
            place(fx, OFF + f['t'], th, 0.10)
    # ---- the voice
    segs = {}
    calls = [(1.0, 'Come here.', 1.0, lambda u: 1.05 + 0.25 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) - 0.25 * u),
             (3.4, 'Come here!', 1.15, lambda u: 1.15 + 0.3 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) - 0.3 * u)]
    for t0, txt, g, cont in calls:
        v = voice(txt, 215, cont, breath=0.05)
        place(vox, OFF + t0, v, 0.30 * g)
        segs.setdefault('call', []).append((OFF + t0, OFF + t0 + len(v) / SR))
    softs = [(7.4, "It's all right."), (10.4, "It's all right."), (26.4, 'Come in.')]
    for t0, txt in softs:
        v = voice(txt, 190, lambda u: 1.0 - 0.18 * u, breath=0.22, rate=0.8)
        place(vox, OFF + t0, v, 0.075)
        segs.setdefault('soft', []).append((OFF + t0, OFF + t0 + len(v) / SR))
    # small room reverb on the voice (she is indoors)
    ir = rng.standard_normal(int(0.35 * SR)) * np.exp(-np.arange(int(0.35 * SR)) / (0.07 * SR))
    vox = vox + signal.fftconvolve(vox, ir)[:N] * 0.025
    # ---- title and end: a low struck plate (the engraver's press), quiet
    for tp in (0.4, OFF + 32 + 0.4):
        n = int(2.4 * SR); tc = np.arange(n) / SR
        plate = sum(np.sin(2 * np.pi * fr * tc) * a for fr, a in ((110, 1), (164.8, .5), (277, .25), (412, .12))) * np.exp(-tc / 0.8)
        place(fx, tp, plate, 0.05)
    mix = amb + fx + vox
    # fades at the very start and end
    mix *= np.clip(np.minimum(tt / 0.3, (TOTAL - tt) / 0.8), 0, 1)
    peak = np.abs(mix).max()
    if peak > 0.89:
        mix *= 0.89 / peak
    lev = {}
    for k, ss in segs.items():
        lev[k] = [round(db(mix[int(a * SR):int(b * SR)]), 1) for a, b in ss]
        lev[k + '_voice_only'] = [round(db(vox[int(a * SR):int(b * SR)]), 1) for a, b in ss]
    quiet = mix[int((OFF + 12.5) * SR):int((OFF + 14.0) * SR)]
    lev['room_tone_12.5-14s'] = round(db(quiet), 1)
    lev['room_tone_0.2-0.9s_scene'] = round(db(mix[int((OFF + 0.2) * SR):int((OFF + 0.9) * SR)]), 1)
    lev['peak_dbfs'] = round(20 * np.log10(np.abs(mix).max()), 1)
    # measured voice onsets (first 10 ms window above -40 dBFS on the voice track)
    ons = []
    for k, ss in segs.items():
        for a, b in ss:
            seg = vox[int(a * SR) - 2400:int(b * SR)]
            win = int(0.01 * SR)
            r = [db(seg[i:i + win]) for i in range(0, len(seg) - win, win)]
            i0 = next(i for i, v in enumerate(r) if v > -40)
            ons.append(dict(kind=k, scene_t=round(a - 0.05 - OFF + i0 * 0.01, 3)))
    lev['voice_onsets'] = sorted(ons, key=lambda o: o['scene_t'])
    calls_db = np.mean(lev['call']); soft_db = np.mean(lev['soft'])
    lev['soft_below_calls_db'] = round(calls_db - soft_db, 1)
    json.dump(lev, open(os.path.join(CACHE, 'sound_levels.json'), 'w'), indent=1)
    from scipy.io import wavfile
    wavfile.write(os.path.join(CACHE, 'sound.wav'), SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))
    print(json.dumps(lev))


if __name__ == '__main__':
    main()
