"""SCION 35 · the sound, synthesised here (no recordings): a source-filter formant voice for the person, the dog's
nails and body on the boards (keyed to the same walk phase that plants its paws), the door, crickets and room tone,
and the riso drum on the cards. Writes build/cache/audio.wav (38 s, 48 kHz) and build/cache/audio.json (measured levels)."""
import numpy as np, json, os, wave
from common import CACHE, load_score

SR = 48000
VSR = 16000
OFF = 3.0          # the scene starts after the 3 s title card
DUR = 38.0
rng = np.random.default_rng(35)
SCORE = load_score()
FR = SCORE['frames']


def reson(x, F, BW, sr):
    """time-varying 2-pole resonator (F, BW arrays per sample)."""
    T = 1.0 / sr
    C = -np.exp(-2 * np.pi * BW * T); B = 2 * np.exp(-np.pi * BW * T) * np.cos(2 * np.pi * F * T); A = 1 - B - C
    y = np.zeros_like(x); y1 = y2 = 0.0
    for n in range(len(x)):
        v = A[n] * x[n] + B[n] * y1 + C[n] * y2
        y[n] = v; y2 = y1; y1 = v
    return y


PH = {  # F1 F2 F3, voiced amplitude, noise amplitude, noise kind
    'A': (760, 1400, 2800, 1.0, 0.0), 'I': (430, 2200, 2950, 1.0, 0.0), 'E': (520, 1650, 2700, 0.9, 0.0),
    'R': (470, 1300, 1750, 0.8, 0.0), 'O': (640, 1000, 2700, 1.0, 0.0), 'a': (900, 1450, 2800, 1.0, 0.0),
    'M': (280, 1250, 2600, 0.32, 0.0), 'N': (280, 1700, 2700, 0.32, 0.0), 'L': (380, 1050, 2800, 0.6, 0.0),
    'H': (None, None, None, 0.0, 0.5), 'K': (None, None, None, 0.0, 0.0), 'T': (None, None, None, 0.0, 0.0),
    'S': (None, None, None, 0.0, 0.0), '_': (None, None, None, 0.0, 0.0),
}


def voice(segs, f0s, amp=1.0, breath=0.05):
    """segs: list of (phoneme, dur). f0s: list of (time frac, Hz)."""
    total = sum(d for _, d in segs)
    n = int(total * VSR)
    t = np.arange(n) / VSR
    F = np.zeros((3, n)); va = np.zeros(n); na = np.zeros(n)
    bursts = []
    pos = 0.0
    # fill targets per segment, then smooth (coarticulation)
    lastF = (500, 1500, 2600)
    for ph, d in segs:
        a, b = int(pos * VSR), int((pos + d) * VSR)
        f1, f2, f3, v, nz = PH[ph]
        if f1 is None:
            # consonant: hold the neighbour formants
            nxt = None
            idx = segs.index((ph, d))
            for p2, _ in segs[idx + 1:]:
                if PH[p2][0] is not None:
                    nxt = PH[p2][:3]; break
            ff = nxt or lastF
        else:
            ff = (f1, f2, f3); lastF = ff
        for k in range(3):
            F[k, a:b] = ff[k]
        va[a:b] = v; na[a:b] = nz
        if ph in 'KTS':
            bursts.append((ph, a, b))
        pos += d
    ker = np.hanning(int(0.035 * VSR)); ker /= ker.sum()
    for k in range(3):
        F[k] = np.convolve(np.pad(F[k], (len(ker), len(ker)), mode='edge'), ker, 'same')[len(ker):-len(ker)]
    kv = np.hanning(int(0.02 * VSR)); kv /= kv.sum()
    va = np.convolve(va, kv, 'same'); na = np.convolve(na, kv, 'same')
    # glottal source
    fr = np.array(f0s)
    f0 = np.interp(t / total, fr[:, 0], fr[:, 1]) * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * t))
    ph = np.cumsum(f0 / VSR) % 1.0
    glot = np.where(ph < 0.6, 0.5 - 0.5 * np.cos(np.pi * ph / 0.6), np.cos(np.pi * (ph - 0.6) / 0.8) ** 2 * (ph < 1.0))
    glot = np.diff(glot, prepend=0) * 20
    src = glot * va + rng.normal(0, 1, n) * (breath * va + 0.35 * na)
    y = src
    for k, bw in zip(range(3), (90, 120, 170)):
        y = reson(y, F[k], np.full(n, bw), VSR)
    # bursts and fricatives
    for ph_, a, b in bursts:
        L = b - a
        nz = rng.normal(0, 1, L)
        if ph_ == 'S':
            nz = np.diff(np.diff(nz, prepend=0), prepend=0) * 0.25
            env = np.sin(np.linspace(0, np.pi, L)) ** 0.7 * 0.5
        else:
            env = np.zeros(L); bl = min(L, int(0.03 * VSR)); env[-bl:] = np.exp(-np.linspace(0, 5, bl)) * 0.9
            fc = 2300 if ph_ == 'K' else 4200
            nz = reson(nz, np.full(L, fc), np.full(L, 900), VSR) * 3
        y[a:b] += nz * env
    y = y / (np.abs(y).max() + 1e-9) * amp
    # back to 48 kHz
    tt = np.arange(int(total * SR)) / SR
    return np.interp(tt, t, y)


PHRASES = [
    # (scene time, text, kind, segments, f0 contour, amplitude)
    (0.90, 'Come here.', 'call', [('K', .07), ('A', .17), ('M', .09), ('H', .08), ('I', .14), ('R', .24)],
     [(0, 225), (.35, 240), (.55, 275), (.75, 255), (1, 190)], 1.0),
    (3.26, 'Come here!', 'call', [('K', .06), ('A', .16), ('M', .08), ('H', .07), ('I', .15), ('R', .26)],
     [(0, 245), (.35, 265), (.55, 305), (.75, 280), (1, 205)], 1.0),
    (7.30, "It's all right.", 'soft', [('I', .08), ('T', .05), ('S', .11), ('O', .17), ('L', .08), ('R', .06), ('a', .17), ('I', .1), ('T', .06)],
     [(0, 200), (.3, 205), (.6, 190), (1, 160)], 0.30),
    (10.32, "It's all right.", 'soft', [('I', .08), ('T', .05), ('S', .11), ('O', .18), ('L', .08), ('R', .06), ('a', .18), ('I', .1), ('T', .06)],
     [(0, 195), (.3, 200), (.6, 186), (1, 156)], 0.28),
    (26.26, 'Come in.', 'soft', [('K', .06), ('A', .13), ('M', .08), ('I', .14), ('N', .2)],
     [(0, 205), (.5, 215), (1, 165)], 0.30),
]


def add(buf, t0, x, gain=1.0):
    a = int(t0 * SR)
    b = min(len(buf), a + len(x))
    if b > a:
        buf[a:b] += x[:b - a] * gain


def click(kind='nail', amp=0.05):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    if kind == 'nail':
        nz = rng.normal(0, 1, n) * np.exp(-t / 0.004)
        nz = np.diff(nz, prepend=0)
        thud = np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.018) * 0.6
        return (nz * 0.6 + thud) * amp
    if kind == 'thud':
        return (np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.05) + rng.normal(0, .2, n) * np.exp(-t / 0.01)) * amp
    if kind == 'step':
        n = int(0.12 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.04) + np.convolve(rng.normal(0, .3, n), np.ones(30) / 30, 'same') * np.exp(-t / 0.03)) * amp


def lowpass(x, k=40):
    return np.convolve(x, np.ones(k) / k, 'same')


def build():
    n = int(DUR * SR)
    out = np.zeros(n)
    t = np.arange(n) / SR
    # room tone + far wind
    rt = lowpass(rng.normal(0, 1, n), 60)
    out += rt * 0.004
    # crickets: two, chirping in short trains
    for f, per, ph0, amp in ((4300, 0.83, 0.1, 0.006), (3900, 1.07, 0.5, 0.004)):
        k = 0
        while True:
            t0 = OFF - 1.0 + ph0 + k * per + 0.05 * np.sin(k)
            if t0 > DUR - 3.5:
                break
            for j in range(3):
                m = int(0.014 * SR); tt = np.arange(m) / SR
                add(out, t0 + j * 0.03, np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / tt[-1]) * amp)
            k += 1
    # riso drum on the cards: a turning drum, a sheet every half second
    for t0, t1 in ((0.15, 2.8), (35.2, 37.6)):
        k = 0
        while t0 + k * 0.5 < t1:
            s = t0 + k * 0.5
            m = int(0.25 * SR); tt = np.arange(m) / SR
            sw = lowpass(rng.normal(0, 1, m), 12) * np.sin(np.pi * tt / tt[-1]) * 0.03
            add(out, s, sw); add(out, s + 0.21, click('nail', 0.05))
            k += 1
    # ---- the dog: nails on boards at each planted paw, from the same walk phase that plants the drawn paws
    GAIT_OFF = {'hl': 0.0, 'fl': 0.25, 'hr': 0.5, 'fr': 0.75}
    prev = None
    for i, f in enumerate(FR):
        a = f['dog']['act']
        if a['moving'] < 0.05 or a['lie'] > 0.3:
            prev = None; continue
        ph = a['walk_phase'] / (2 * np.pi)
        if prev is not None:
            for L, o in GAIT_OFF.items():
                u0 = (prev + o) % 1.0; u1 = (ph + o) % 1.0
                if u1 < u0 and (prev != ph):           # wrapped: this paw touches down
                    amp = 0.05 + 0.04 * a['crouch']
                    add(out, OFF + i / 24 + rng.uniform(0, 0.02), click('nail', amp * a['moving']))
        prev = ph
    # the turn (scrabble), lying down (thumps + exhale), getting up, settling sigh, tail on the boards
    for s in np.arange(3.46, 3.92, 0.075):
        add(out, OFF + s, click('nail', 0.05))
    for t0 in (4.62, 24.12):
        add(out, OFF + t0, click('thud', 0.12)); add(out, OFF + t0 + 0.18, click('thud', 0.07))
        m = int(0.6 * SR); tt = np.arange(m) / SR
        add(out, OFF + t0 + 0.25, lowpass(rng.normal(0, 1, m), 25) * np.sin(np.pi * tt / tt[-1]) ** 2 * 0.03)
    for s in (7.80, 7.93, 8.05, 8.22, 8.36, 8.50, 8.62):
        add(out, OFF + s, click('nail', 0.045))
    m = int(0.9 * SR); tt = np.arange(m) / SR
    add(out, OFF + 28.45, lowpass(rng.normal(0, 1, m), 30) * np.sin(np.pi * tt / tt[-1]) ** 1.5 * 0.035)   # the sigh
    # a short breath as the head comes round at 7.46
    m = int(0.22 * SR); tt = np.arange(m) / SR
    add(out, OFF + 7.40, lowpass(rng.normal(0, 1, m), 18) * np.sin(np.pi * tt / tt[-1]) * 0.03)
    for s in np.arange(26.7, 28.2, 1 / 2.2):
        add(out, OFF + s, click('thud', 0.05))                                                      # tail on the boards
    # ---- the person: steps aside, sits (bench creak)
    for s in (4.75, 5.0, 5.25):
        add(out, OFF + s, click('step', 0.06))
    m = int(0.35 * SR); tt = np.arange(m) / SR
    creak = np.sin(2 * np.pi * np.cumsum(np.interp(tt, [0, tt[-1]], [420, 300])) / SR) * np.sin(np.pi * tt / tt[-1]) * 0.012
    add(out, OFF + 5.85, creak * (1 + np.sign(np.sin(2 * np.pi * 37 * tt))) * 0.5)
    # ---- the door: latch, slow creak, then the room (a little warmer air: low hum) once it stands open
    add(out, OFF + 6.18, click('nail', 0.06))
    m = int(0.75 * SR); tt = np.arange(m) / SR
    fz = np.interp(tt, [0, 0.3, 0.75], [260, 190, 150]) * (1 + 0.04 * rng.normal(0, 1, m).cumsum() / np.sqrt(m))
    saw = (np.cumsum(fz / SR) % 1.0) * 2 - 1
    cr = reson(saw, np.full(m, 900.0), np.full(m, 300.0), SR) * np.sin(np.pi * tt / tt[-1]) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 23 * tt))) * 0.03
    add(out, OFF + 6.22, cr)
    hum = (np.sin(2 * np.pi * 110 * t) * 0.5 + np.sin(2 * np.pi * 220 * t) * 0.2) * 0.0025
    door = np.clip((t - OFF - 6.3) / 0.7, 0, 1) * (t < OFF + 32)
    out += hum * door + lowpass(rng.normal(0, 1, n), 120) * 0.004 * door
    # ---- voices
    log = []
    for t0, text, kind, segs, f0s, amp in PHRASES:
        v = voice(segs, f0s, 1.0, breath=0.05 if kind == 'call' else 0.4)
        g = 0.62 if kind == 'call' else 0.62 * amp
        add(out, OFF + t0, v * g)
        log.append(dict(t_scene=t0, text=text, kind=kind, dur=round(len(v) / SR, 3), rms_db=None))
    # fades
    out *= np.clip(t / 0.3, 0, 1) * np.clip((DUR - t) / 0.6, 0, 1)
    # measure each voice's level from the mix (RMS over its own span, dBFS) and the room tone between
    for L in log:
        a = int((OFF + L['t_scene']) * SR); b = a + int(L['dur'] * SR)
        L['rms_db'] = round(20 * np.log10(np.sqrt(np.mean(out[a:b] ** 2)) + 1e-12), 2)
        L['peak_db'] = round(20 * np.log10(np.abs(out[a:b]).max() + 1e-12), 2)
    a = int((OFF + 13.0) * SR); b = int((OFF + 14.0) * SR)
    room = round(20 * np.log10(np.sqrt(np.mean(out[a:b] ** 2)) + 1e-12), 2)
    pk = np.abs(out).max()
    if pk > 0.95:
        out *= 0.95 / pk
    st = np.stack([out, out], 1)
    with wave.open(os.path.join(CACHE, 'audio.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    calls = [L['rms_db'] for L in log if L['kind'] == 'call']; softs = [L['rms_db'] for L in log if L['kind'] == 'soft']
    res = dict(voices=log, room_tone_rms_db_13_14s=room, soft_under_calls_db=round(min(calls) - max(softs), 2))
    json.dump(res, open(os.path.join(CACHE, 'audio.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    build()
