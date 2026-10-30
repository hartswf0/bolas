"""SCION-48 · sound, all synthesized here (no recordings).

- the board: every disc that flips clicks (counts measured per rendered frame, cache/measure_*.jsonl), a low transformer hum
- the machine: a relay clack each time the dog's machine changes state (its decisions are audible, never written)
- the person: formant-synthesized phrases on the score's voice windows: two calls, three soft phrases (>= 6 dB quieter)
- the world: dusk (crickets, air), the door's hinge, the warmer room tone once it is open, the dog's pads and breath
python3 sound.py -> cache/sound.wav (38.0 s, 48 kHz stereo) and cache/sound_levels.json
"""
import json, glob, os, math
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
SR = 48000
TITLE, SCENE, END = 3.0, 32.0, 3.0
N = int(SR * (TITLE + SCENE + END))
rng = np.random.default_rng(48)


def at(t):
    return int((TITLE + t) * SR)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2))
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def add(buf, x, t0, gain=1.0, pan=0.0):
    i = at(t0) if not isinstance(t0, int) else t0
    j = min(N, i + len(x))
    if j <= i:
        return
    gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:j, 0] += x[:j - i] * gain * gl * 1.414
    buf[i:j, 1] += x[:j - i] * gain * gr * 1.414


# ------------------------------------------------------------------ formant voice
V = {'a': (730, 1090, 2440), 'u': (640, 1190, 2390), 'i': (390, 1990, 2550), 'e': (500, 1500, 2500), 'o': (570, 840, 2410),
     'l': (360, 1000, 2400), 'r': (420, 1300, 1600), 'm': (260, 1000, 2300), 'n': (260, 1700, 2500), 'ai2': (390, 1990, 2550)}


def phrase(segs, f0a, f0b, breath=0.1, f0peak=None):
    """segs: list of (dur, kind, formant-key or (key_from, key_to)); kinds: v vowel/approximant, n nasal, s fricative, k burst, h aspiration, _ silence"""
    total = sum(s[0] for s in segs)
    n = int(total * SR)
    t = np.arange(n) / SR
    f0 = f0a + (f0b - f0a) * (t / total)
    if f0peak:
        f0 += f0peak[1] * np.exp(-((t - f0peak[0]) / 0.12) ** 2)
    f0 *= 1 + 0.01 * np.sin(2 * math.pi * 5.5 * t)
    ph = np.cumsum(f0 / SR) % 1.0
    glott = np.where(ph < 0.6, 0.5 * (1 - np.cos(math.pi * ph / 0.6)), np.cos(math.pi * (ph - 0.6) / 0.8))
    glott = np.diff(glott, prepend=0) * 30
    noise = rng.standard_normal(n) * 0.5
    F = np.zeros((n, 3)); vamp = np.zeros(n); namp = np.zeros(n); nasal = np.zeros(n); fric = np.zeros(n)
    i = 0
    prevF = np.array(V['e'], float)
    for dur, kind, key in segs:
        m = int(dur * SR)
        sl = slice(i, i + m)
        if kind in ('v', 'n', 'h'):
            if isinstance(key, tuple):
                fa, fb = np.array(V[key[0]], float), np.array(V[key[1]], float)
            else:
                fa = fb = np.array(V[key], float)
            w = np.linspace(0, 1, m)[:, None]
            F[sl] = fa * (1 - w) + fb * w
            # smooth the joins
            k = min(m, int(0.03 * SR))
            F[i:i + k] = prevF * (1 - np.linspace(0, 1, k)[:, None]) + F[i:i + k] * np.linspace(0, 1, k)[:, None]
            prevF = fb
            if kind == 'v':
                vamp[sl] = 1
            elif kind == 'n':
                vamp[sl] = 0.35; nasal[sl] = 1
            else:
                namp[sl] = 0.5; vamp[sl] = 0.05
        else:
            F[sl] = prevF
            if kind == 's':
                fric[sl] = 1
            elif kind == 'k':
                fric[i:i + int(0.025 * SR)] = 1.5
        i += m
    env_s = lambda a: lp(a, 40, 1)
    vamp, namp, nasal, fric = env_s(vamp), env_s(namp), env_s(nasal), lp(fric, 120, 1)
    src = glott * vamp * (1 - breath) + noise * (namp + breath * vamp * 0.6)
    out = np.zeros(n)
    for j, bw in enumerate((80, 100, 140)):
        y = np.zeros(n)
        # time-varying two-pole resonator, updated every 64 samples
        y1 = y2 = 0.0
        for s0 in range(0, n, 64):
            f = F[s0, j]
            r = math.exp(-math.pi * bw / SR)
            c1, c2 = 2 * r * math.cos(2 * math.pi * f / SR), -r * r
            g = (1 - r)
            seg = src[s0:s0 + 64]
            ys, y1, y2 = _res(seg, c1, c2, g, y1, y2)
            y[s0:s0 + 64] = ys
        out += y * (1.0, 0.6, 0.3)[j]
    out = out * (1 - 0.7 * nasal) + lp(out, 400) * 0.7 * nasal
    out += bp(noise, 3500, 7500) * fric * 1.2
    out = hp(out, 90)
    out /= max(1e-9, np.max(np.abs(out)))
    fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.01 * SR))
    return out * fade


def _res(x, c1, c2, g, y1, y2):
    b = [g]
    a = [1, -c1, -c2]
    zi = signal.lfiltic(b, a, [y1, y2])
    y, _ = signal.lfilter(b, a, x, zi=zi)
    if len(y) >= 2:
        return y, y[-1], y[-2]
    return y, (y[-1] if len(y) else y1), y1


def rms_db(x):
    return 20 * math.log10(max(1e-9, float(np.sqrt(np.mean(x ** 2)))))


def main():
    buf = np.zeros((N, 2))
    levels = {}
    # ---- room tone: board hum + dusk air + crickets (whole film)
    t = np.arange(N) / SR
    hum = 0.5 * np.sin(2 * math.pi * 50 * t) + 0.25 * np.sin(2 * math.pi * 100 * t) + 0.1 * np.sin(2 * math.pi * 150 * t)
    air = lp(rng.standard_normal(N), 600) * 0.6
    crick = np.zeros(N)
    for k in range(70):
        c0 = rng.uniform(0, N / SR - 1)
        f = rng.uniform(4200, 5200)
        nn = int(0.35 * SR)
        tt = np.arange(nn) / SR
        chirp = np.sin(2 * math.pi * f * tt) * (np.sin(2 * math.pi * 28 * tt) > 0.2) * np.hanning(nn)
        i0 = int(c0 * SR)
        crick[i0:i0 + nn] += chirp[:max(0, min(nn, N - i0))]
    room = hum * 0.0045 + air * 0.006 + crick * 0.0022
    buf[:, 0] += room; buf[:, 1] += room
    levels['room_tone_dbfs_rms'] = round(rms_db(room), 1)
    # ---- the board: clicks for flips (scene from measurements; cards from their own flip counts)
    flips = {}
    for fn in glob.glob(os.path.join(CACHE, 'measure_*.jsonl')):
        for line in open(fn):
            r = json.loads(line); flips[r['i']] = r.get('flips', 0)
    cards = json.load(open(os.path.join(CACHE, 'card_flips.json'))) if os.path.exists(os.path.join(CACHE, 'card_flips.json')) else {}
    clk_len = int(0.004 * SR)
    clk = rng.standard_normal(clk_len) * np.exp(-np.arange(clk_len) / (0.0007 * SR))
    clk = bp(clk, 1800, 6000)
    seq = [(TITLE + i / 24, flips.get(i, 0)) for i in range(768)]
    seq += [(k / 24, v) for k, v in enumerate(cards.get('title', []))]
    seq += [(TITLE + SCENE + k / 24, v) for k, v in enumerate(cards.get('end', []))]
    for t0, nf in seq:
        if nf <= 0:
            continue
        nclick = int(min(60, 2 + math.sqrt(nf) * 1.6))
        amp = 0.004 * min(4.0, math.sqrt(nf) / 3)
        for _ in range(nclick):
            tt = t0 + rng.uniform(0, 1 / 24)
            add(buf, clk * rng.uniform(0.5, 1.0), int(tt * SR), amp / math.sqrt(nclick) * 3, rng.uniform(-0.6, 0.6))
    # ---- the machine: a relay clack per change of state
    M = json.load(open(os.path.join(CACHE, 'machine.json')))
    rl = int(0.06 * SR)
    tt = np.arange(rl) / SR
    relay = (np.sin(2 * math.pi * 1250 * tt) * 0.6 + np.sin(2 * math.pi * 2710 * tt) * 0.4) * np.exp(-tt / 0.012)
    relay += rng.standard_normal(rl) * np.exp(-tt / 0.002) * 0.8
    prev_sub = None
    for f in M['frames']:
        key = (f['state'], f['sub'] if f['state'] == 'lie_down' else '')
        if prev_sub is not None and key != prev_sub:
            add(buf, relay, f['t'], 0.03 if key[0] != prev_sub[0] else 0.015, -0.3)
        prev_sub = key
    # ---- voices on the score's windows
    come_here = [(0.05, 'k', None), (0.15, 'v', 'u'), (0.08, 'n', 'm'), (0.07, 'h', 'i'), (0.32, 'v', ('i', 'e'))]
    come_on = [(0.05, 'k', None), (0.13, 'v', 'u'), (0.07, 'n', 'm'), (0.2, 'v', 'a'), (0.12, 'n', 'n')]
    its_all_right = [(0.09, 'v', 'i'), (0.03, 'k', None), (0.09, 's', None), (0.15, 'v', 'o'), (0.08, 'v', 'l'), (0.07, 'v', 'r'),
                     (0.3, 'v', ('a', 'ai2')), (0.04, 'k', None)]
    come_in = [(0.05, 'k', None), (0.12, 'v', 'u'), (0.07, 'n', 'm'), (0.2, 'v', 'i'), (0.16, 'n', 'n')]
    calls = []
    v1 = phrase(come_here, 175, 135, 0.06, (0.4, 45)); add(buf, v1, 1.05, 0.30, -0.35); calls.append(v1 * 0.30)
    v2 = phrase(come_here, 190, 140, 0.06, (0.4, 55)); add(buf, v2, 3.42, 0.32, -0.35); calls.append(v2 * 0.32)
    v3 = phrase(come_on, 180, 130, 0.08, (0.3, 35)); add(buf, v3, 4.05, 0.28, -0.35); calls.append(v3 * 0.28)
    softs = []
    for t0, g, f0 in ((7.45, 0.13, 128), (8.55, 0.10, 120), (10.45, 0.12, 126), (26.45, 0.12, 124)):
        segs = come_in if t0 > 20 else its_all_right
        if t0 == 8.55:
            segs = its_all_right[3:]
        v = phrase(segs, f0, f0 - 22, 0.32)
        add(buf, v, t0, g, -0.45); softs.append(v * g)
    levels['call_dbfs_rms'] = round(np.mean([rms_db(c) for c in calls]), 1)
    levels['soft_dbfs_rms'] = round(np.mean([rms_db(c) for c in softs]), 1)
    levels['soft_below_call_db'] = round(levels['call_dbfs_rms'] - levels['soft_dbfs_rms'], 1)
    levels['soft_above_room_db'] = round(levels['soft_dbfs_rms'] - levels['room_tone_dbfs_rms'], 1)
    # ---- the door: hinge creak and the room's warmth
    cl = int(0.9 * SR); tt = np.arange(cl) / SR
    creak_f = 340 + 160 * tt / 0.9
    creak = np.sin(2 * math.pi * np.cumsum(creak_f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 31 * tt))) * np.hanning(cl)
    add(buf, bp(creak, 250, 2500), 6.2, 0.03, -0.5)
    warm = lp(rng.standard_normal(N), 250) * 0.5 + np.sin(2 * math.pi * 60 * t) * 0.2
    ramp = np.clip((t - (TITLE + 6.2)) / 0.9, 0, 1) * (t < TITLE + SCENE)
    buf[:, 0] += warm * ramp * 0.006; buf[:, 1] += warm * ramp * 0.004
    # ---- the dog: pads on the boards (from the same gait the render used) and breath
    import render as Rn
    G = Rn.gait_tracks(M['frames'])
    pl = int(0.05 * SR); tt = np.arange(pl) / SR
    pad = lp(rng.standard_normal(pl), 900) * np.exp(-tt / 0.012)
    for off in (0.0, 0.25, 0.5, 0.75):
        for i in range(1, len(G)):
            p0, p1 = (G[i - 1][0] + off) % 1, (G[i][0] + off) % 1
            g = G[i][1]
            if g > 0.2 and ((p0 > 0.9 and p1 < 0.1) or (p0 >= 0.66 > p1 and abs(p1 - p0) < 0.5)):
                add(buf, pad, M['frames'][i]['t'], 0.05 * g, 0.2)
    bl = int(1.1 * SR); tt = np.arange(bl) / SR
    sigh = bp(rng.standard_normal(bl), 300, 1800) * np.sin(math.pi * tt / 1.1) ** 2
    for t0, g in ((24.3, 0.02), (28.35, 0.016), (5.0, 0.012)):
        add(buf, sigh, t0, g, 0.25)
    # ---- master
    pk = np.max(np.abs(buf))
    g = 0.85 / pk
    buf *= g
    gd = 20 * math.log10(g)
    for k in ('room_tone_dbfs_rms', 'call_dbfs_rms', 'soft_dbfs_rms'):
        levels[k] = round(float(levels[k]) + gd, 1)
    levels = {k: float(v) for k, v in levels.items()}
    levels['peak'] = round(float(np.max(np.abs(buf))), 3)
    wavfile.write(os.path.join(CACHE, 'sound.wav'), SR, (buf * 32767).astype(np.int16))
    json.dump(levels, open(os.path.join(CACHE, 'sound_levels.json'), 'w'), indent=1)
    print(levels)


if __name__ == '__main__':
    main()
