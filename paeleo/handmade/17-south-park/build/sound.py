"""SCION 17 // sound v1: everything synthesized here, cut to the director's events. 48 kHz stereo WAV -> build/cache/sound.wav

Voice: a small cascade formant synthesizer (glottal pulse source, three time-varying resonators, a frication branch)
reading the same phoneme list as the mouth atlas (dialogue.py). Calls are loud and bright; the soft lines are breathy,
lower and at least 6 dB below the calls (measured and printed). Room: dusk wind and two crickets. Foley: paw taps at the
gait's foot contacts, the collar tag, the flop, the huff, her steps and sitting, the door's creak, the inside warmth
when the door opens, tail thumps on the boards. One comic pluck under the sulking flop.
"""
import json, math, os, sys, wave
import numpy as np
import dialogue, direct

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
SR = 48000
PRE, POST = 3.0, 3.0                       # title and end cards
SCENE = 32.0
TOTAL = PRE + SCENE + POST
rng = np.random.default_rng(1717)

V = {  # phoneme targets: F1 F2 F3, voicing, aspiration, frication (centre, bandwidth, amp)
    'AH': (640, 1190, 2390, 1.0, 0, None), 'IH': (400, 1920, 2560, 1.0, 0, None), 'ER': (490, 1350, 1690, 1.0, 0, None),
    'EY': (480, 2000, 2600, 1.0, 0, None), 'AO': (590, 880, 2540, 1.0, 0, None), 'AY': (730, 1090, 2440, 1.0, 0, None),
    'm': (280, 1100, 2300, 0.32, 0, None), 'n': (280, 1700, 2600, 0.32, 0, None), 'l': (360, 1000, 2700, 0.6, 0, None),
    'r': (420, 1300, 1600, 0.6, 0, None), 'h': (None, None, None, 0.0, 0.55, None), '_': (None, None, None, 0.0, 0, None),
    's': (None, None, None, 0.0, 0.0, (6500, 3000, 0.5)), 'k': (None, None, None, 0.0, 0.0, 'k'), 't': (None, None, None, 0.0, 0.0, 't'),
}
GLIDE = {'AY': (400, 1920, 2560), 'EY': (400, 1920, 2560)}
FSCALE = 1.12                               # an adult woman's vocal tract, roughly


def resonate(x, F, B):
    """time-varying two-pole resonator (Klatt form); F, B arrays"""
    y = np.zeros_like(x); y1 = y2 = 0.0; T = 1.0 / SR
    C = -np.exp(-2 * np.pi * B * T); Bc = 2 * np.exp(-np.pi * B * T) * np.cos(2 * np.pi * F * T); A = 1 - Bc - C
    for n in range(len(x)):
        v = A[n] * x[n] + Bc[n] * y1 + C[n] * y2
        y2 = y1; y1 = v; y[n] = v
    return y


def smooth(a, ms):
    k = max(1, int(SR * ms / 1000))
    ker = np.ones(k) / k
    return np.convolve(np.pad(a, (k, k), mode='edge'), ker, mode='same')[k:-k]


def speak(line):
    reg = line['reg']; sp = line['speed']
    segs = [(p, ms / 1000 * sp) for p, ms in line['ph']]
    n = int(sum(d for _, d in segs) * SR) + int(0.12 * SR)
    F = np.zeros((3, n)); AV = np.zeros(n); AH = np.zeros(n); FR = np.zeros(n); FC = np.full(n, 5000.0); BURST = np.zeros(n)
    i = 0
    # carry formants of the neighbouring vowel into consonants
    vowel_targets = [V[p][:3] if V[p][0] else None for p, _ in segs]
    for k, (p, d) in enumerate(segs):
        m = int(d * SR); sl = slice(i, i + m)
        tgt = vowel_targets[k]
        if tgt is None:
            nxt = next((vt for vt in vowel_targets[k + 1:] if vt), None) or next((vt for vt in vowel_targets[:k][::-1] if vt), (500, 1500, 2500))
            tgt = nxt
        for q in range(3): F[q, sl] = tgt[q]
        if p in GLIDE:
            g = GLIDE[p]; u = np.linspace(0, 1, m) ** 1.5
            for q in range(3): F[q, sl] = tgt[q] + (g[q] - tgt[q]) * u
        AV[sl] = V[p][3]; AH[sl] = V[p][4]
        fr = V[p][5]
        if fr == 'k' or fr == 't':
            c = int(m * 0.6)
            BURST[i + c:i + m] = np.linspace(1, 0.2, m - c) ** 2
            FC[i:i + m] = 2400 if fr == 'k' else 5200
            AH[i + c:i + m] = 0.35
        elif fr:
            FR[sl] = fr[2]; FC[sl] = fr[0]
        i += m
    F = np.stack([smooth(F[q], 22) for q in range(3)]) * FSCALE
    AV = smooth(AV, 14); AH = smooth(AH, 10); FR = smooth(FR, 10)
    tt = np.arange(n) / SR; dur = i / SR
    u = tt / max(dur, 1e-3)
    if line['text'].startswith('Hey'):
        f0 = np.where(u < 0.25, 300 - 50 * u / 0.25, 250 + 80 * np.sin(np.clip((u - 0.3) / 0.7, 0, 1) * np.pi * 0.8) - 40 * np.clip((u - 0.8) / 0.2, 0, 1))
    elif reg == 'call':
        f0 = 225 + 75 * np.sin(np.clip(u, 0, 1) * np.pi * 0.85) - 30 * np.clip((u - 0.75) / 0.25, 0, 1)
    else:
        f0 = 182 + 14 * np.sin(np.clip(u, 0, 1) * np.pi) - 22 * np.clip(u, 0, 1)
    f0 = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * tt)) * (1 + 0.004 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)))
    ph = np.cumsum(f0 / SR) % 1.0
    # glottal flow derivative (Rosenberg-like): open 60 %, closing 40 %
    flow = np.where(ph < 0.6, 0.5 * (1 - np.cos(np.pi * ph / 0.6)), np.cos(0.5 * np.pi * (ph - 0.6) / 0.4))
    flow = np.where(ph < 1.0, flow, 0)
    src = np.diff(flow, prepend=flow[0]) * 40
    noise = rng.standard_normal(n)
    breath = 0.10 if reg == 'call' else 0.45
    exc = src * AV + noise * (AH * 0.5 + AV * breath * 0.25)
    bw = (70, 95, 140) if reg == 'call' else (110, 140, 190)
    y = exc
    for q in range(3):
        y = resonate(y, F[q], np.full(n, bw[q]))
    fric = resonate(noise * (FR + BURST * 1.2), FC, np.full(n, 2200.0))
    out = y / (np.abs(y).max() + 1e-9) + fric * 0.6 / (np.abs(fric).max() + 1e-9) * (0.6 if reg == 'call' else 0.35)
    env = np.minimum(1, np.minimum(tt / 0.01, (tt[-1] - tt) / 0.03))
    return out * env


def pluck(f, dur, amp):
    n = int(dur * SR); N = int(SR / f)
    buf = rng.uniform(-1, 1, N); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % N]
        buf[k % N] = 0.497 * (buf[k % N] + buf[(k + 1) % N])
    return out * amp


def tone_burst(freqs, dur, amp, decay):
    t = np.arange(int(dur * SR)) / SR
    return amp * sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in freqs) / len(freqs) * np.exp(-t / decay)


def knock(f, dur, amp, noise=0.5):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / (dur / 4))
    nz = rng.standard_normal(len(t)) * np.exp(-t / (dur / 8))
    nz = resonate(nz, np.full(len(t), f * 6.0), np.full(len(t), f * 4.0))
    nz /= np.abs(nz).max() + 1e-9
    return amp * ((1 - noise) * s + noise * nz)


def breathy(dur, F, amp):
    n = int(dur * SR); t = np.arange(n) / SR
    y = rng.standard_normal(n)
    for f, b in F: y = resonate(y, np.full(n, f), np.full(n, b))
    y /= np.abs(y).max() + 1e-9
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return y * env * amp


def db(x): return 20 * math.log10(max(x, 1e-9))


def main():
    frames, events = direct.perform()
    n = int(TOTAL * SR)
    L = np.zeros(n); R = np.zeros(n)
    T0 = PRE

    def add(sig, t, pan=0.0, gain=1.0):
        i = int((T0 + t) * SR)
        if i >= n: return
        sig = sig[:n - i] * gain
        l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
        L[i:i + len(sig)] += sig * l; R[i:i + len(sig)] += sig * r

    pan_of = lambda x: max(-0.8, min(0.8, (x - 1.5) / 3.5))
    # --- room: wind and crickets across the whole film (quiet under the cards)
    w = rng.standard_normal(n)
    w = np.convolve(w, np.ones(400) / 400, mode='same'); w = w / np.abs(w).max()
    wind_env = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / SR / 7.3) ** 2
    room = w * wind_env * 10 ** (-47 / 20)
    for (rate, f, pan, off) in ((0.68, 4650, 0.7, 0.1), (0.91, 4180, -0.5, 0.37)):
        t = off
        while t < TOTAL:
            for k in range(3):
                b = tone_burst([f, f * 1.01], 0.018, 10 ** (-41 / 20), 0.006)
                i = int((t + k * 0.035) * SR)
                if i + len(b) < n:
                    L[i:i + len(b)] += b * (1 - pan) / 2; R[i:i + len(b)] += b * (1 + pan) / 2
            t += rate + rng.uniform(-0.05, 0.05)
    L += room; R += room
    # --- voice
    levels = {}
    for li, line in enumerate(dialogue.LINES):
        s = speak(line)
        g = 10 ** ((-5 if line['reg'] == 'call' else -16) / 20)
        if line['text'].startswith('Hey'): g *= 1.12
        s = s / (np.abs(s).max() + 1e-9) * g
        px = frames[int(line['t'] * 24)]['person']['x']
        add(s, line['t'], pan=pan_of(px) * 0.6)
        levels[line['text'] + ' @%.1f' % line['t']] = round(db(np.sqrt(np.mean(s[np.abs(s) > 1e-4] ** 2))), 1)
    # --- foley from the director's events
    for e in events:
        t = e['t']; k = e['kind']
        if k == 'paw': add(knock(rng.uniform(900, 1300), 0.03, 10 ** (-33 / 20), 0.8), t, pan_of(e['x']))
        elif k == 'jingle':
            for q in range(3): add(tone_burst([3150, 4720, 6120], 0.16, 10 ** (-34 / 20), 0.05), t + q * 0.045, 0.5)
        elif k == 'flop': add(knock(85, 0.25, 10 ** (-22 / 20) * e['size'], 0.35), t, 0.4 if t < 10 else -0.3)
        elif k == 'huff': add(breathy(0.32, [(520, 200), (1300, 300)], 10 ** (-27 / 20)), t, 0.6)
        elif k == 'sigh': add(breathy(0.65, [(700, 180), (1150, 240), (2500, 400)], 10 ** (-31 / 20)), t, -0.6)
        elif k == 'step': add(knock(140, 0.09, 10 ** (-25 / 20), 0.5), t, -0.6)
        elif k == 'sit':
            add(knock(110, 0.16, 10 ** (-24 / 20), 0.5), t, -0.7); add(breathy(0.35, [(3000, 2500)], 10 ** (-35 / 20)), t - 0.15, -0.7)
        elif k == 'creak':
            d = 0.34; tt = np.arange(int(d * SR)) / SR
            f = 330 + 220 * (tt / d) + 40 * np.sin(2 * np.pi * 9 * tt)
            saw = 2 * ((np.cumsum(f / SR)) % 1.0) - 1
            am = 0.4 + 0.6 * (np.sin(2 * np.pi * 23 * tt) > 0.2)
            c = resonate(saw * am, np.full(len(tt), 1400.0), np.full(len(tt), 700.0))
            add(c / np.abs(c).max() * 10 ** (-26 / 20) * np.sin(np.pi * tt / d), t, -0.35)
        elif k == 'rise': add(breathy(0.2, [(400, 300)], 10 ** (-36 / 20)), t, 0.5)
        elif k == 'content': add(breathy(0.6, [(320, 120), (900, 250)], 10 ** (-31 / 20)), t, -0.2)
        elif k == 'thump': add(knock(120, 0.07, 10 ** (-27 / 20) * min(1, e['amp'] + 0.2), 0.4), t, -0.1)
    # the comic beat: a two-note pluck falling under the sulking flop
    add(pluck(392, 0.5, 10 ** (-27 / 20)), 4.78, 0.3); add(pluck(262, 0.9, 10 ** (-27 / 20)), 4.98, 0.3)
    # the inside warmth once the door is open (a low room hum through the doorway)
    tt = np.arange(int((SCENE - 6.25) * SR)) / SR
    hum = rng.standard_normal(len(tt)); hum = np.convolve(hum, np.ones(120) / 120, mode='same')
    hum = hum / np.abs(hum).max() * 0.6 + 0.4 * np.sin(2 * np.pi * 110 * tt) * 0.3
    hum *= np.clip(tt / 0.5, 0, 1) * 10 ** (-43 / 20)
    add(hum, 6.25, -0.3)
    # fades for the cards
    env = np.ones(n); a = int(1.2 * SR); env[:a] = np.linspace(0, 1, a); env[-a:] = np.linspace(1, 0, a)
    L *= env; R *= env
    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0.97: L *= 0.97 / peak; R *= 0.97 / peak
    out = os.path.join(ROOT, 'build', 'cache', 'sound.wav')
    pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
    with wave.open(out, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
    # measured levels (RMS over voiced samples) and the room tone
    rt = db(np.sqrt(np.mean(room[int((PRE + 12.5) * SR):int((PRE + 14.5) * SR)] ** 2)))
    json.dump(dict(voice_rms_dbfs=levels, room_tone_rms_dbfs=round(rt, 1), peak=round(db(peak), 1)), open(os.path.join(ROOT, 'build', 'cache', 'levels.json'), 'w'), indent=1)
    print(levels, 'room', round(rt, 1))


if __name__ == '__main__':
    main()
