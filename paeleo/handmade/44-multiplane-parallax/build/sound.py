"""Sound: synthesized here (no recordings), placed in depth.

Every source has a world position; per frame its pan comes from where the camera sees it (screen x) and its level and
brightness from its distance to the camera (depth audio): the room's hum grows as the camera leans through the door.
Voice: a small formant synthesizer (glottal pulses through vowel resonators, noise for consonants) speaks the
person's lines on the score's voice timeline; calls loud, soft lines >= 6 dB quieter (measured, proof/audio_levels.json).
Dog: nail clicks on the boards at every foot plant of the planner (dog.PLAN), thumps when it lies down, its tail
thumping the boards while it wags lying down, a sigh when it settles.
"""
import os, json, math
import numpy as np
from scipy.signal import lfilter, butter
from common import *
import dog

SR = 48000
T = N / FPS
rng = np.random.default_rng(4)


def bp(x, f, q):
    w = 2 * math.pi * f / SR
    al = math.sin(w) / (2 * q)
    b = [al, 0, -al]; a = [1 + al, -2 * math.cos(w), 1 - al]
    return lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2))
    return lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'high')
    return lfilter(b, a, x)


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


# ---------------------------------------------------------------- voice
VOW = {  # formants F1..F3 (Hz) for a female voice
    'a': (850, 1610, 2850), 'u': (600, 1200, 2700), 'i': (430, 2300, 3000), 'I': (480, 2100, 2900),
    'e': (600, 2300, 2900), 'o': (650, 1000, 2700), 'O': (700, 1100, 2700), 'm': (280, 1300, 2600), 'n': (300, 1600, 2600),
    'r': (500, 1350, 1700), 'l': (400, 1200, 2700), 'ai': (750, 1500, 2800),
}


def syllables(spec, f0, loud, breath):
    """spec: list of (phone, dur, f0 multiplier). returns signal."""
    out = []
    phase = 0.0
    for ph, dur, fm in spec:
        n = int(dur * SR)
        t = np.arange(n) / SR
        if ph in ('k', 't', 's', 'h'):
            nz = rng.standard_normal(n)
            if ph == 'k':
                sig = bp(nz, 2200, 3) * env(n, 0.002, dur * 0.8) * 0.8
            elif ph == 't':
                sig = bp(nz, 4000, 2) * env(n, 0.001, dur * 0.8) * 0.6
            elif ph == 's':
                sig = hp(nz, 4500) * env(n, 0.01, 0.02) * 0.35
            else:
                sig = bp(nz, 1500, 1) * env(n, 0.02, 0.03) * 0.5
            out.append(sig * loud); continue
        if isinstance(fm, tuple):
            f = np.linspace(f0 * fm[0], f0 * fm[1], n)
        else:
            f = np.full(n, f0 * fm)
        f = f * (1 + 0.012 * np.sin(2 * math.pi * 5.2 * t))
        ph_ = phase + np.cumsum(f) / SR
        phase = ph_[-1]
        saw = 2 * (ph_ % 1) - 1
        glott = lp(saw, 2500) + breath * rng.standard_normal(n) * 0.6
        if '-' in ph:
            a_, b_ = ph.split('-')
            F = np.array([np.linspace(VOW[a_][k], VOW[b_][k], n) for k in range(3)])
        else:
            F = np.array([np.full(n, VOW[ph][k]) for k in range(3)])
        sig = np.zeros(n)
        # time-varying formants: process in 10 ms blocks
        blk = 480
        for s0 in range(0, n, blk):
            seg = glott[s0:s0 + blk]
            acc = 0
            for k, g in zip(range(3), (1.0, 0.6, 0.3)):
                acc = acc + g * bp(seg, F[k][s0], 6 + 2 * k)
            sig[s0:s0 + blk] = acc
        sig *= env(n, 0.03, 0.06)
        if ph in ('m', 'n'):
            sig = lp(sig, 900) * 0.6
        out.append(sig * loud)
    return np.concatenate(out)


LINES = [
    # (t, text, spec, f0, loud, breath)
    (1.02, 'Come here.', [('k', .05, 1), ('u', .16, 1.0), ('m', .12, (1.0, .95)), ('h', .07, 1), ('i-r', .42, (1.25, .9))], 225, 1.0, 0.05),
    (1.85, 'Come!', [('k', .05, 1), ('u', .18, 1.2), ('m', .16, (1.15, 0.9))], 235, 0.9, 0.05),
    (3.42, 'Come here!', [('k', .05, 1), ('u', .14, 1.05), ('m', .10, 1.0), ('h', .06, 1), ('i-r', .40, (1.35, .95))], 240, 1.0, 0.05),
    (4.05, 'Come on, now.', [('k', .05, 1), ('u', .12, 1.1), ('m', .08, 1.05), ('O', .12, 1.0), ('n', .12, .95), ('n', .06, .95), ('a-u', .30, (1.15, .85))], 230, 0.95, 0.05),
    (7.45, "It's all right.", [('I', .10, 1.0), ('t', .04, 1), ('s', .08, 1), ('O', .22, (1.0, .95)), ('l', .10, .92), ('r', .08, .95), ('ai', .34, (1.05, .85)), ('t', .05, 1)], 185, 0.42, 0.35),
    (8.55, "it's all right", [('I', .09, .95), ('t', .04, 1), ('s', .07, 1), ('O', .2, .92), ('l', .1, .9), ('ai', .32, (1.0, .8)), ('t', .04, 1)], 178, 0.40, 0.4),
    (10.45, 'Good dog.', [('k', .04, 1), ('u', .2, (1.0, .95)), ('t', .04, 1), ('t', .03, 1), ('O', .3, (1.05, .8)), ('k', .04, 1)], 180, 0.40, 0.4),
    (10.95, "It's all right.", [('I', .09, .95), ('t', .04, 1), ('s', .07, 1), ('O', .2, .92), ('l', .1, .9), ('ai', .34, (1.0, .8)), ('t', .04, 1)], 176, 0.40, 0.4),
    (26.42, 'Come in.', [('k', .05, 1), ('u', .14, 1.0), ('m', .10, .97), ('I', .14, 1.02), ('n', .26, (1.0, .82))], 182, 0.42, 0.4),
]


def person_pos(t):
    i = min(int(t * FPS), N - 1)
    p = FR[i]['person']
    import person
    return np.array([p['x'], 1.2 if p['sit'] < 0.5 else 0.7, person.person_z(p['x'])])


def place(buf, sig, t0, pos_fn, gain=1.0, ref=3.0):
    """mix a mono signal into the stereo buffer with per-block pan/level from where the camera sees it."""
    n0 = int(t0 * SR)
    n = len(sig)
    blk = SR // 50
    for s in range(0, n, blk):
        tt = (n0 + s) / SR
        cam, _ = camera(min(tt, T - 1e-3))
        P = pos_fn(tt)
        u, v, d = project(P, cam)
        pan = float(np.clip((u - W / 2) / (W / 2), -1, 1)) * 0.8
        dist = float(np.linalg.norm(P - cam))
        g = gain * ref / max(ref, dist) ** 1.0
        seg = sig[s:s + blk]
        a = n0 + s
        if a >= buf.shape[1]:
            break
        seg = seg[:buf.shape[1] - a]
        buf[0, a:a + len(seg)] += seg * g * math.cos((pan + 1) * math.pi / 4)
        buf[1, a:a + len(seg)] += seg * g * math.sin((pan + 1) * math.pi / 4)


def main():
    n = int(T * SR)
    buf = np.zeros((2, n))
    levels = {'calls': [], 'soft': []}
    vbuf = np.zeros((2, n))
    for t0, text, spec, f0, loud, br in LINES:
        sig = syllables(spec, f0, loud, br)
        sig = sig / (np.abs(sig).max() + 1e-9) * loud * 0.5
        tmp = np.zeros((2, n))
        place(tmp, sig, t0, person_pos, gain=1.0, ref=6.5)
        seg = tmp[:, int(t0 * SR):int(t0 * SR) + len(sig)]
        rms = float(np.sqrt((seg ** 2).mean()))
        (levels['calls'] if loud > 0.5 else levels['soft']).append({'t': t0, 'text': text, 'rms_dbfs': round(20 * math.log10(rms + 1e-12), 2)})
        vbuf += tmp
    buf += vbuf
    # ambience: wind (low noise) + crickets (distant, steady) + the room (grows with the door and as the camera leans in)
    nz = rng.standard_normal(n)
    wind = lp(nz, 300) * 0.05 * (1 + 0.4 * np.sin(2 * math.pi * 0.07 * np.arange(n) / SR))
    buf += wind[None, :] * np.array([[1.0], [0.9]])
    cr = np.zeros(n)
    tt = 0.3
    while tt < T:
        m = int(0.045 * SR)
        k = np.arange(m) / SR
        chirp = np.sin(2 * math.pi * 4700 * k) * (np.sin(2 * math.pi * 30 * k) > 0) * env(m, 0.005, 0.01)
        a = int(tt * SR)
        for rep in range(3):
            b = a + rep * int(0.06 * SR)
            if b + m < n:
                cr[b:b + m] += chirp * 0.012
        tt += rng.uniform(0.55, 0.9)
    buf[0] += cr * 0.8; buf[1] += np.roll(cr, int(0.3 * SR)) * 1.0
    # the room: a warm hum + a clock, placed at the lamp (inside), loudness tied to the door angle
    hum = lp(rng.standard_normal(n), 220) * 0.6 + 0.02 * np.sin(2 * math.pi * 60 * np.arange(n) / SR)
    clock = np.zeros(n)
    for k in range(int(T)):
        a = int((k + 0.5) * SR); m = int(0.012 * SR)
        clock[a:a + m] += bp(rng.standard_normal(m), 3000, 4) * env(m, 0.001, 0.01) * 0.5
    room = hum * 0.06 + clock * 0.4
    openk = np.array([0.25 + 0.75 * smooth((s / SR - 6.2) / 0.8) for s in range(0, n, SR // 50)])
    openk = np.repeat(openk, SR // 50)[:n]
    room = room * openk
    place(buf, room, 0.0, lambda t: np.array([-0.5, 1.0, 2.3]), gain=1.0, ref=4.0)
    # door: a latch and a creak as it swings wide
    m = int(0.75 * SR); k = np.arange(m) / SR
    f = 380 + 160 * np.sin(np.pi * k / 0.75) + 30 * rng.standard_normal(m).cumsum() / SR * 50
    creak = bp(np.sign(np.sin(2 * math.pi * np.cumsum(f) / SR)) * (rng.random(m) < 0.6), 900, 3) * env(m, 0.1, 0.3) * 0.10
    latch = np.zeros(m); latch[:int(.02 * SR)] = bp(rng.standard_normal(int(.02 * SR)), 2500, 3) * 0.3
    place(buf, creak + latch, 6.18, lambda t: np.array([-0.3, 1.0, 0.2]), gain=1.0, ref=4.0)
    # the person sitting down: cloth rustle and two steps
    for t0, dur, g in [(5.45, 0.18, 0.15), (5.85, 0.18, 0.15), (6.1, 0.7, 0.10)]:
        m = int(dur * SR)
        s = (bp(rng.standard_normal(m), 1800 if dur > 0.5 else 250, 1.2) * env(m, 0.01, dur * 0.6)) * g
        place(buf, s, t0, person_pos, ref=4.0)
    # dog: nail clicks at foot plants
    plan = dog.PLAN if dog.PLAN is not None else dog.plan_feet()
    clicks = 0
    for i in range(1, N):
        was, now = plan[i - 1][1], plan[i][1]
        for k in range(4):
            if was[k] and not now[k]:
                m = int(0.05 * SR)
                c = hp(rng.standard_normal(m), 3000) * env(m, 0.0005, 0.045) * 0.5
                c[:int(0.004 * SR)] *= 2.0
                knock = np.sin(2 * math.pi * 170 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / 0.02) * 0.4
                foot = plan[i][0][k]
                place(buf, (c + knock) * 0.22, i / FPS + rng.uniform(0, 0.02), lambda t, foot=foot: foot, ref=2.5)
                clicks += 1
    droot = lambda t: dog.root(min(int(t * FPS), N - 1)) + np.array([0, 0.3, 0])
    # lying down: a thump and an exhale (refusal at ~4.6 s, at the sill at ~24.1 s)
    for t0 in (4.62, 24.12):
        m = int(0.6 * SR)
        thump = np.sin(2 * math.pi * 70 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / 0.06) * 0.5
        breath = lp(bp(rng.standard_normal(m), 700, 0.8), 1500) * env(m, 0.1, 0.4) * 0.25
        place(buf, thump + breath, t0, droot, ref=2.5)
    # tail thumping the boards while it wags, lying (26.5 - 28.4)
    tt = 26.55
    while tt < 28.4:
        i = int(tt * FPS)
        w = FR[i]['dog']['act']['wag']
        if w > 0.3:
            m = int(0.08 * SR)
            th = np.sin(2 * math.pi * 95 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / 0.03) * 0.35 * w
            place(buf, th, tt, droot, ref=2.5)
        tt += 1 / 2.3 / 2
    # the sigh when it settles (28.6)
    m = int(1.1 * SR)
    sigh = lp(bp(rng.standard_normal(m), 500, 0.7), 1200) * env(m, 0.25, 0.7) * 0.35
    place(buf, sigh, 28.6, droot, ref=2.5)
    pk = np.abs(buf).max()
    buf = buf / pk * 0.89
    scale_db = 20 * math.log10(0.89 / pk)
    for k in levels:
        for e in levels[k]:
            e['rms_dbfs'] = round(e['rms_dbfs'] + scale_db, 2)
    amb = float(np.sqrt(((wind * 0.89 / pk) ** 2).mean()))
    calls = np.mean([e['rms_dbfs'] for e in levels['calls']]); soft = np.mean([e['rms_dbfs'] for e in levels['soft']])
    rep = {'measured_from': 'build/sound.py mix (stereo RMS over each line, after spatial placement and normalisation)',
           'calls': levels['calls'], 'soft': levels['soft'], 'mean_call_dbfs': round(calls, 2), 'mean_soft_dbfs': round(soft, 2),
           'soft_below_calls_db': round(calls - soft, 2), 'wind_bed_rms_dbfs': round(20 * math.log10(amb), 2), 'nail_clicks': clicks}
    os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
    json.dump(rep, open(os.path.join(FOLDER, 'proof/audio_levels.json'), 'w'), indent=1)
    from scipy.io import wavfile
    wavfile.write(os.path.join(CACHE, 'scene.wav'), SR, (buf.T * 32767).astype(np.int16))
    print(json.dumps({k: rep[k] for k in ('mean_call_dbfs', 'mean_soft_dbfs', 'soft_below_calls_db', 'wind_bed_rms_dbfs', 'nail_clicks')}))


if __name__ == '__main__':
    main()
