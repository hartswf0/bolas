"""Depth audio, synthesized here (no recordings): the blue-hour air, crickets in the yard, the room's hum and clock
heard through the door (muffled while it is ajar), a formant-synthesized voice (calls; then soft), the dog's nails on
the boards at the foot solver's own footfalls, a door creak, the dog settling, and a sparse glass-tone score.
Each source is placed in the stereo field by where it is on screen and given distance (level, low-pass, reverb send);
sources behind the fog bank are muffled while the fog obscures.
Run: python3 sound.py -> build/cache/sound.wav (38 s: 3 s card + 32 s scene + 3 s card) and proof/audio_levels.json
"""
import json, math, os, wave
import numpy as np
from common import *
import dog as DOG
import person as PERSON

SR = 48000
PRE = 3.0
TOTAL = 38.0
NS = int(TOTAL * SR)
rng = np.random.default_rng(55)


def tt(sec):
    return int((sec + PRE) * SR)


def onepole_lp(x, fc):
    """one-pole low-pass; fc may be an array (time-varying)."""
    fc = np.broadcast_to(np.asarray(fc, np.float64), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    # vectorized in blocks with constant coefficient
    B = 480
    for k in range(0, len(x), B):
        ak = float(a[k])
        seg = x[k:k + B]
        out = np.empty_like(seg)
        for j in range(len(seg)):
            s = (1 - ak) * seg[j] + ak * s
            out[j] = s
        y[k:k + B] = out
    return y


def lp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X, len(x))


def bp_fft(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / np.sqrt(1 + (f / hi) ** 4))
    return np.fft.irfft(X, len(x))


def pan_gain(p):
    p = float(np.clip(p, -1, 1))
    a = (p + 1) * np.pi / 4
    return math.cos(a), math.sin(a)


def screen_pan(X, Zw, t):
    sx, _, _ = project((X, 0.5, Zw), cam(t))
    return float(np.clip((sx / W - 0.5) * 1.6, -0.95, 0.95))


class Mix:
    def __init__(self):
        self.L = np.zeros(NS)
        self.R = np.zeros(NS)
        self.send = np.zeros(NS)  # mono reverb send
        self.stems = {}

    def add(self, sig, t0, pan, gain=1.0, rev=0.2, stem=None):
        i0 = tt(t0)
        if i0 < 0:
            sig = sig[-i0:]
            i0 = 0
        n = min(len(sig), NS - i0)
        if n <= 0:
            return
        s = sig[:n] * gain
        if np.ndim(pan) == 0:
            gl, gr = pan_gain(pan)
        else:
            pa = np.clip(np.asarray(pan[:n]), -1, 1)
            gl, gr = np.cos((pa + 1) * np.pi / 4), np.sin((pa + 1) * np.pi / 4)
        self.L[i0:i0 + n] += s * gl
        self.R[i0:i0 + n] += s * gr
        self.send[i0:i0 + n] += s * rev
        if stem:
            st = self.stems.setdefault(stem, np.zeros(NS))
            st[i0:i0 + n] += s


# ------------------------------------------------------------------------------------------------ the voice
FORM = {  # F1, F2, F3 (Hz), amplitude, voiced?
    'k': (500, 1500, 2500, 0.0, 0), 'ʌ': (640, 1190, 2390, 1.0, 1), 'm': (260, 1100, 2300, 0.32, 1),
    'h': (450, 1800, 2500, 0.0, 0), 'ɪ': (400, 1950, 2560, 0.95, 1), 'ə': (520, 1500, 2450, 0.85, 1),
    't': (400, 1800, 2600, 0.0, 0), 's': (400, 1800, 2600, 0.0, 0), 'ɔ': (580, 860, 2400, 1.0, 1),
    'l': (360, 1050, 2400, 0.55, 1), 'r': (430, 1250, 1650, 0.7, 1), 'a': (760, 1300, 2450, 1.0, 1),
    'i': (330, 2150, 2700, 0.85, 1), 'n': (260, 1650, 2600, 0.35, 1), '_': (500, 1500, 2500, 0.0, 0)}
NOISE = {'k': (1800, 3200, 0.5, 0.03), 'h': (500, 3500, 0.35, 0.09), 't': (2800, 6500, 0.45, 0.025), 's': (4200, 9000, 0.42, 0.11)}


def utterance(phones, f0s, soft=False):
    """formant synthesis: phones [(ph, dur)], f0 contour [(u 0..1, Hz)]; additive harmonics through cascaded resonances."""
    dur = sum(d for _, d in phones)
    n = int(dur * SR)
    tgrid = np.arange(n) / SR
    # control tracks at 1 ms, with smooth transitions between phone targets
    ctl_t = np.arange(0, dur, 0.001)
    marks, vals = [], []
    t = 0
    for ph, d in phones:
        marks += [t + d * 0.3, t + d * 0.7]
        vals += [FORM[ph], FORM[ph]]
        t += d
    vals = np.array(vals, np.float64)
    tr = [np.interp(ctl_t, marks, vals[:, j]) for j in range(5)]
    win = 25
    ker = np.hanning(win) / np.hanning(win).sum()
    tr = [np.convolve(np.pad(x, (win, win), 'edge'), ker, 'same')[win:-win] for x in tr]
    F1, F2, F3, amp, voiced = tr
    f0 = np.interp(ctl_t / dur, [u for u, _ in f0s], [v for _, v in f0s])
    f0 = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * ctl_t))  # a little vibrato: the throat is not a machine
    B = (110, 130, 180) if soft else (70, 95, 140)
    K = 48
    harm = np.zeros((len(ctl_t), K))
    for k in range(1, K + 1):
        f = k * f0
        H = np.ones_like(f)
        for Fi, Bi in zip((F1, F2, F3), B):
            H *= Fi ** 2 / np.sqrt((Fi ** 2 - f ** 2) ** 2 + (Bi * f) ** 2)
        tilt = 1.0 / k ** (1.35 if soft else 0.95)
        harm[:, k - 1] = H * tilt * (f < 5500)
    # to audio rate
    f0a = np.interp(tgrid, ctl_t, f0)
    phase = 2 * np.pi * np.cumsum(f0a) / SR
    ampa = np.interp(tgrid, ctl_t, amp * voiced)
    y = np.zeros(n)
    for k in range(K):
        y += np.interp(tgrid, ctl_t, harm[:, k]) * np.sin((k + 1) * phase)
    y *= ampa
    y /= (np.abs(y).max() + 1e-9)
    # breath: soft speech carries air through the same formants (a noise source, shaped and gated)
    br = rng.normal(0, 1, n)
    br = bp_fft(br, 300, 4500) * (0.10 if not soft else 0.32)
    y = y + br * np.interp(tgrid, ctl_t, np.maximum(amp, 0.25) * (voiced > 0.3))
    # consonant noises
    t = 0
    for ph, d in phones:
        if ph in NOISE:
            lo, hi, a, dd = NOISE[ph]
            m = int(d * SR)
            nz = bp_fft(rng.normal(0, 1, m), lo, hi)
            env = np.exp(-np.arange(m) / (dd * SR)) if ph in 'kt' else np.sin(np.linspace(0, np.pi, m)) ** 0.7
            i0 = int(t * SR)
            y[i0:i0 + m] += nz[:len(y) - i0] / (np.abs(nz).max() + 1e-9) * a * env[:len(y) - i0] * (0.6 if soft else 1)
        t += d
    # overall envelope
    env = np.clip(np.minimum(tgrid / 0.02, (dur - tgrid) / 0.06), 0, 1)
    return y * env


def call_voice(insistent=False):
    ph = [('k', 0.06), ('ʌ', 0.16), ('m', 0.12), ('_', 0.05), ('h', 0.09), ('ɪ', 0.22), ('ə', 0.20)]
    if insistent:
        ph = [('k', 0.05), ('ʌ', 0.13), ('m', 0.09), ('_', 0.03), ('h', 0.07), ('ɪ', 0.26), ('ə', 0.18)]
        f0 = [(0, 175), (0.3, 190), (0.55, 245), (0.8, 220), (1, 165)]
    else:
        f0 = [(0, 160), (0.3, 170), (0.55, 215), (0.8, 195), (1, 150)]
    return utterance(ph, f0)


def soft_voice(words):
    if words == 'allright':
        ph = [('ɪ', 0.07), ('t', 0.04), ('s', 0.12), ('ɔ', 0.20), ('l', 0.12), ('r', 0.08), ('a', 0.20), ('i', 0.12), ('t', 0.08)]
        f0 = [(0, 128), (0.3, 132), (0.6, 122), (1, 104)]
    else:  # come in
        ph = [('k', 0.06), ('ʌ', 0.15), ('m', 0.12), ('_', 0.06), ('ɪ', 0.18), ('n', 0.2)]
        f0 = [(0, 124), (0.4, 128), (1, 106)]
    return utterance(ph, f0, soft=True)


# ------------------------------------------------------------------------------------------------ other sources
def click(dur=0.05, lo=1800, hi=5000, knock=170, kamp=0.6):
    n = int(dur * SR)
    x = np.arange(n) / SR
    nz = bp_fft(rng.normal(0, 1, n), lo, hi) * np.exp(-x / 0.004)
    nz /= np.abs(nz).max() + 1e-9
    k = np.sin(2 * np.pi * knock * x) * np.exp(-x / 0.03) * kamp
    return nz * 0.7 + k


def thump(dur=0.35, f=85, decay=0.09):
    x = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * f * x * (1 - 0.2 * x)) * np.exp(-x / decay) + lp_fft(rng.normal(0, 1, len(x)), 400) * np.exp(-x / 0.03) * 0.4


def exhale(dur=0.8, fc=1100):
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    nz = bp_fft(rng.normal(0, 1, n), 200, fc)
    nz /= np.abs(nz).max() + 1e-9
    return nz * (np.sin(np.pi * x) ** 1.5) * (1 - 0.5 * x)


def creak(dur=0.75):
    n = int(dur * SR)
    x = np.arange(n) / SR
    # stick-slip: a train of tiny impulses whose rate glides and jitters, through a wooden resonance
    rate = 95 + 70 * np.sin(np.pi * x / dur) + 18 * rng.normal(0, 1, n).cumsum() / np.sqrt(np.arange(1, n + 1)) * 0
    ph = np.cumsum(rate * (1 + 0.15 * np.sin(2 * np.pi * 7 * x))) / SR
    imp = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.6 + 0.4 * rng.random(n))
    y = bp_fft(imp, 450, 2600) + 0.3 * bp_fft(imp, 120, 400)
    y /= np.abs(y).max() + 1e-9
    return y * np.sin(np.pi * x / dur) ** 0.6


def glass_tone(freqs, dur, attack=1.2, amp=1.0):
    n = int(dur * SR)
    x = np.arange(n) / SR
    y = np.zeros(n)
    for k, f in enumerate(freqs):
        y += np.sin(2 * np.pi * f * x + k) * (1 + 0.3 * np.sin(2 * np.pi * 0.23 * x + k)) / (k + 1) ** 0.3
        y += 0.15 * np.sin(2 * np.pi * 2 * f * x) / (k + 1)
    env = np.minimum(1, x / attack) * np.minimum(1, (dur - x) / 1.5)
    return y / len(freqs) * np.clip(env, 0, 1) * amp


def build():
    M = Mix()
    P = DOG.controller()
    T = np.arange(NS) / SR - PRE

    # --- the blue-hour air: soft wind, muffled more while the fog obscures
    wind = rng.normal(0, 1, NS)
    wind = lp_fft(wind, 520, 2)
    wind = wind / np.abs(wind).max()
    mod = 0.65 + 0.35 * np.sin(2 * np.pi * T / 9.0) * np.sin(2 * np.pi * T / 3.7 + 1)
    fade = np.clip((T + PRE) / 2.0, 0, 1) * np.clip((TOTAL - PRE - T) / 2.0, 0, 1)
    M.add(wind * mod * fade * 0.05, -PRE, -0.2, rev=0.0, stem='room')
    wind2 = lp_fft(rng.normal(0, 1, NS), 380, 2)
    M.add(wind2 / np.abs(wind2).max() * mod[::-1] * fade * 0.045, -PRE, 0.4, rev=0.0, stem='room')
    # crickets far in the yard (right), damped by the fog
    for k in range(int(38 / 0.9)):
        t0 = -PRE + k * 0.9 + rng.uniform(-0.1, 0.1)
        n = int(0.16 * SR)
        x = np.arange(n) / SR
        ch = np.sin(2 * np.pi * 4300 * x) * (np.sin(2 * np.pi * 22 * x) > 0.2) * np.sin(np.pi * x / 0.16)
        g = 0.006 * (0.6 + 0.4 * rng.random()) * (1 - 0.5 * smooth(1.0, 2.5, t0 + 0) * (1 - smooth(6, 9, t0)))
        M.add(lp_fft(ch, 3000 + 2000 * smooth(6, 9, t0)) if False else ch, t0, 0.75, gain=g, rev=0.3, stem='room')

    # --- the room: a warm hum and a clock, heard through the door: muffled ajar, open after 6.2, nearer as we come in
    hum_t = np.arange(NS) / SR
    hum = (np.sin(2 * np.pi * 110 * hum_t) * 0.4 + np.sin(2 * np.pi * 165 * hum_t) * 0.25 + 0.6 * lp_fft(rng.normal(0, 1, NS), 300)) * 0.5
    clock = np.zeros(NS)
    for k in range(int(TOTAL)):
        tk = k * 1.0 + 0.37
        c = click(0.04, 2500, 6000, 900, 0.3) * 0.5
        i0 = int(tk * SR)
        clock[i0:i0 + len(c)] += c[:NS - i0]
    room = hum + clock * 0.9
    door_open = np.array([door_gap(max(0, min(32, t))) for t in T[::480]])
    door_open = np.repeat(door_open, 480)[:NS] / door_gap(30)
    near = np.array([1 + 1.2 * smooth(14.7, 32, t) for t in T[::480]])
    near = np.repeat(near, 480)[:NS]
    muff = lp_fft(room, 700)
    room_out = (muff * (1 - door_open) * 0.6 + room * door_open) * near * fade
    pan_door = np.repeat(np.array([screen_pan(0.0, 5.3, max(0, min(32, t))) for t in T[::480]]), 480)[:NS]
    M.add(room_out * 0.021, -PRE, pan_door, rev=0.25, stem='room')

    # --- the voice (from where the person is; reverb from the porch)
    def voice_at(sig, t0, gain):
        q = PERSON.pose(t0)
        pn = screen_pan(q['X'], q['Z'], t0)
        M.add(sig, t0, pn, gain=gain, rev=0.22, stem='voice_call' if gain > 0.2 else 'voice_soft')
    voice_at(call_voice(False), 1.0, 0.42)
    voice_at(call_voice(True), 3.42, 0.5)
    voice_at(soft_voice('allright'), 7.42, 0.11)
    voice_at(soft_voice('allright'), 10.42, 0.105)
    voice_at(soft_voice('comein'), 26.42, 0.105)

    # --- the dog: nails and pads on the boards at its own footfalls (from the foot-plant solver)
    for k, p in enumerate(P):
        for leg, (pos, lift, landed) in p['feet'].items():
            if landed:
                t0 = p['t'] + rng.uniform(0, 0.01)
                pn = screen_pan(pos[0], pos[2], p['t'])
                obscured = 1 - 0.45 * smooth(1.0, 2.5, p['t']) * (1 - smooth(6.4, 9, p['t']))
                g = (0.05 if p['state'] == 'retreat' else 0.032) * (0.7 + 0.5 * rng.random()) * obscured
                M.add(lp_fft(click(), 2500 + 4000 * obscured), t0, pn, gain=g, rev=0.15, stem='dog')
    # lying down (twice): body to the boards, a breath out
    for t0, g in ((4.55, 0.10), (24.05, 0.14)):
        p = P[int(t0 * FPS)]
        pn = screen_pan(p['x'], p['z'], t0)
        M.add(thump(), t0, pn, gain=g, rev=0.15, stem='dog')
        M.add(exhale(0.7, 900), t0 + 0.12, pn, gain=g * 0.35, rev=0.1, stem='dog')
    # getting up at 7.6, a shake of the collar? no collar: a scrape of nails
    p = P[int(7.7 * FPS)]
    M.add(click(0.08, 1500, 4000, 140, 0.4), 7.72, screen_pan(p['x'], p['z'], 7.7), gain=0.04, stem='dog')
    # tail on the boards while it looks in (wag)
    for k, p in enumerate(P):
        if k and p['t'] > 26.6 and p['wag'] > 0.4 and p['lie'] > 0.9:
            if math.sin(p['wag_phase']) < 0 <= math.sin(P[k - 1]['wag_phase']):
                M.add(thump(0.12, 120, 0.025), p['t'], screen_pan(p['x'] + 0.6, p['z'], p['t']), gain=0.05, rev=0.1, stem='dog')
    # the long sigh as it settles to stay
    p = P[int(28.7 * FPS)]
    M.add(exhale(1.3, 800), 28.65, screen_pan(p['x'], p['z'], 28.6), gain=0.05, rev=0.15, stem='dog')

    # --- the door: latch, then the slow creak as it swings in and the light comes out
    M.add(click(0.03, 2000, 7000, 600, 0.4), 6.12, screen_pan(-0.2, 5.0, 6.1), gain=0.05, rev=0.3, stem='door')
    M.add(creak(0.72), 6.2, screen_pan(-0.1, 5.2, 6.4), gain=0.07, rev=0.35, stem='door')

    # --- the score: sparse glass tones (A, E, B, C#: open, unresolved), entering with the light, resolving at the sill
    M.add(glass_tone([220.0, 329.6, 493.9], 7.0, 1.8, 0.022), 6.4, 0.0, rev=0.6, stem='music')
    M.add(glass_tone([207.7, 311.1, 466.2], 6.0, 2.0, 0.018), 12.5, 0.0, rev=0.6, stem='music')
    for k, (f, t0) in enumerate(((659.3, 15.0), (587.3, 17.6), (554.4, 20.2), (493.9, 22.6))):
        M.add(glass_tone([f], 3.2, 0.05, 0.016), t0, -0.1 + 0.07 * k, rev=0.7, stem='music')
    M.add(glass_tone([220.0, 277.2, 329.6, 440.0], 5.5, 1.5, 0.024), 24.0, 0.0, rev=0.6, stem='music')
    M.add(glass_tone([220.0, 329.6, 554.4], 6.0, 2.0, 0.016), 28.9, 0.0, rev=0.7, stem='music')

    # --- reverb (porch and fog: short, dark)
    ir_n = int(1.1 * SR)
    ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR / 0.32)
    ir = lp_fft(ir, 2800)
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.fft.irfft(np.fft.rfft(M.send, NS + ir_n) * np.fft.rfft(ir, NS + ir_n), NS + ir_n)[:NS]
    L = M.L + wet * 0.5
    R = M.R + np.concatenate([np.zeros(240), wet[:-240]]) * 0.5
    peak = max(np.abs(L).max(), np.abs(R).max())
    g = 0.75 / peak  # about -2.5 dBFS sample peak, leaving room for the encoder's overshoot
    L *= g
    R *= g
    pcm = (np.stack([L, R], 1) * 32767).astype('<i2')
    with wave.open(os.path.join(CACHE, 'sound.wav'), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    # --- measured levels (dBFS RMS of each stem in its window, after the master gain)
    def rms_db(x):
        return round(20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-12), 2)

    def window(stem, a, b):
        s = M.stems[stem][tt(a):tt(b)] * g
        act = np.abs(s) > 1e-4
        return rms_db(s[act]) if act.any() else None
    lv = dict(call_1=window('voice_call', 1.0, 2.0), call_2=window('voice_call', 3.42, 4.3),
              soft_1=window('voice_soft', 7.42, 8.6), soft_2=window('voice_soft', 10.42, 11.6), soft_come_in=window('voice_soft', 26.42, 27.4),
              room_tone_during_soft_1=rms_db(M.stems['room'][tt(7.42):tt(8.6)] * g),
              room_tone_during_come_in=rms_db(M.stems['room'][tt(26.42):tt(27.4)] * g))
    lv['soft_minus_call_dB'] = round(max(lv['soft_1'], lv['soft_2'], lv['soft_come_in']) - min(lv['call_1'], lv['call_2']), 2)
    lv['soft_minus_room_dB'] = round(min(lv['soft_1'] - lv['room_tone_during_soft_1'], lv['soft_come_in'] - lv['room_tone_during_come_in']), 2)
    lv['note'] = 'RMS over the active samples of each stem, after the master gain. Measured, not listened to.'
    os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
    json.dump(lv, open(os.path.join(FOLDER, 'proof/audio_levels.json'), 'w'), indent=1)
    print(lv)


if __name__ == '__main__':
    build()
