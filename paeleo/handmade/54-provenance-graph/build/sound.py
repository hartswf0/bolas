"""Sound, synthesised from the score and the render's own events (no recordings are used): a formant voice for the
person, claws on boards at the dog's actual foot contacts, the found door's creak, room tone of dusk (wind, crickets) and a
low warmth that comes out with the light. Writes build/cache/sound.wav (48 kHz stereo, 38 s incl. cards) and
lineage/sound.json with the measured levels of every voice line."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import FOLDER, REPO

SR = 48000
PRE, SCENE, POST = 3.0, 32.0, 3.0
N = int(SR * (PRE + SCENE + POST))
rng = np.random.default_rng(54)
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))


def biquad_bp(x, f, q):
    """band-pass resonator, constant 0 dB peak; f may be an array (per sample) -> computed in blocks."""
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    farr = np.broadcast_to(np.asarray(f, float), x.shape)
    B = 64
    for b0 in range(0, len(x), B):
        fc = farr[b0]
        w = 2 * math.pi * fc / SR; al = math.sin(w) / (2 * q)
        a0 = 1 + al; bb0 = al / a0; bb2 = -al / a0; aa1 = -2 * math.cos(w) / a0; aa2 = (1 - al) / a0
        seg = x[b0:b0 + B]
        out = np.empty_like(seg)
        for k, v in enumerate(seg):
            o = bb0 * v + bb2 * x2 - aa1 * y1 - aa2 * y2
            x2 = x1; x1 = v; y2 = y1; y1 = o
            out[k] = o
        y[b0:b0 + B] = out
    return y


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


PH = {  # phoneme: (F1, F2, F3, voiced, noise)
    'k': (300, 1800, 2500, 0, 1), 'ah': (680, 1200, 2450, 1, 0), 'm': (260, 1250, 2300, 1, 0), 'h': (500, 1600, 2500, 0, 1),
    'ih': (400, 1950, 2600, 1, 0), 'eh': (560, 1700, 2500, 1, 0), 'er': (500, 1400, 1700, 1, 0), 't': (400, 1800, 3000, 0, 1),
    's': (400, 1800, 3500, 0, 2), 'aw': (600, 900, 2400, 1, 0), 'l': (380, 1100, 2600, 1, 0), 'r': (460, 1150, 1600, 1, 0),
    'ay': (740, 1250, 2500, 1, 0), 'iy': (320, 2200, 2900, 1, 0), 'n': (260, 1600, 2500, 1, 0), '_': (500, 1500, 2500, 0, 0)}


def voice(segs, f0_pts, loud=1.0, breath=0.08):
    """formant synthesis: glottal pulses (+breath) through three time-varying resonators."""
    dur = sum(d for _, d, _ in segs)
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = np.interp(t, [p[0] * dur for p in f0_pts], [p[1] for p in f0_pts])
    f0 *= 1 + 0.012 * np.sin(2 * math.pi * 5.2 * t)
    ph = np.cumsum(f0 / SR) % 1.0
    glott = (ph < 0.6) * np.sin(math.pi * ph / 0.6) ** 2 - 0.35
    glott = np.diff(np.concatenate([[0], glott]))
    noise = rng.standard_normal(n) * 0.25
    F = np.zeros((n, 3)); V = np.zeros(n); NZ = np.zeros(n); A = np.zeros(n)
    edges = np.cumsum([0] + [d for _, d, _ in segs])
    for (p, d, a), e0, e1 in zip(segs, edges[:-1], edges[1:]):
        i0, i1 = int(e0 * SR), int(e1 * SR)
        F[i0:i1] = PH[p][:3]; V[i0:i1] = PH[p][3]; NZ[i0:i1] = PH[p][4]; A[i0:i1] = a
    # smooth parameter tracks (coarticulation)
    def sm(v, ms):
        k = int(SR * ms / 1000); w = np.hanning(2 * k + 1); w /= w.sum()
        return np.convolve(np.pad(v, k, mode='edge'), w, 'valid')
    for c in range(3):
        F[:, c] = sm(F[:, c], 30)
    V = sm(V, 12); NZ = sm(NZ, 8); A = sm(A, 15)
    src = glott * V * 4.0 + noise * (NZ * 0.9 + breath * V)
    out = biquad_bp(src, F[:, 0], 5) * 1.0 + biquad_bp(src, F[:, 1], 9) * 0.55 + biquad_bp(src, F[:, 2], 12) * 0.3
    s_hi = biquad_bp(noise, 5200, 3) * (NZ > 1.5)
    out = (out + s_hi * 0.6) * A * loud
    return out


LINES = {
    'come_here': ([('k', .05, 1), ('ah', .16, 1), ('m', .10, .8), ('h', .07, .7), ('ih', .16, 1), ('er', .22, .9), ('_', .05, 0)],
                  [(0, 235), (0.25, 262), (0.55, 300), (0.8, 250), (1, 200)]),
    'come_here2': ([('k', .05, 1), ('ah', .15, 1), ('m', .09, .8), ('h', .06, .7), ('ih', .18, 1), ('er', .26, .95), ('_', .05, 0)],
                   [(0, 250), (0.25, 290), (0.5, 330), (0.8, 280), (1, 215)]),
    'all_right': ([('ih', .07, .8), ('t', .03, .5), ('s', .07, .6), ('aw', .16, 1), ('l', .07, .8), ('r', .07, .8), ('ay', .24, 1), ('t', .05, .4), ('_', .05, 0)],
                  [(0, 190), (0.4, 200), (0.7, 182), (1, 160)]),
    'come_in': ([('k', .05, .8), ('ah', .14, 1), ('m', .08, .8), ('ih', .14, 1), ('n', .16, .7), ('_', .05, 0)],
                [(0, 186), (0.5, 196), (1, 165)]),
}


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int((PRE + t) * SR)
    n = min(len(sig), N - i)
    if n <= 0:
        return
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i:i + n] += sig[:n] * gain * l * 1.41
    buf[1, i:i + n] += sig[:n] * gain * r * 1.41


def tick(strength=1.0):
    n = int(0.03 * SR); t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t / 0.004)
    s = biquad_bp(s, 3200, 2.5) * 1.2 + biquad_bp(s, 900, 2) * 0.5
    th = np.sin(2 * math.pi * 120 * t) * np.exp(-t / 0.012) * 0.4
    return (s + th) * strength


def creak(dur, f_lo, f_hi, rough=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * math.pi * 1.3 * t + 1)) + rng.standard_normal(n).cumsum() * 0.02
    ph = np.cumsum(f / SR) % 1
    stick = (ph < 0.08).astype(float) * (0.6 + 0.4 * rng.random(n))
    s = biquad_bp(stick, 700, 4) + biquad_bp(stick, 1650, 6) * 0.6 + biquad_bp(stick, 2900, 8) * 0.3
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    return s * env * rough


def thump(dur=0.25, f=70):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * math.pi * f * t * (1 - 0.3 * t / dur)) * np.exp(-t / 0.06) + onepole_lp(rng.standard_normal(n), 400) * np.exp(-t / 0.05) * 0.8


def breath(dur, f=900, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 1.5
    return biquad_bp(rng.standard_normal(n), f, 1.2) * env * gain


def rms_db(x):
    return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


def main():
    trace = json.load(open(os.path.join(FOLDER, 'trace.json')))['frames']
    buf = np.zeros((2, N))
    # ---- room tone: wind and crickets at dusk, through the whole film (in and out of the cards)
    t = np.arange(N) / SR
    wind = onepole_lp(rng.standard_normal(N), 260) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.07 * t + 1.3)) * 0.05
    crick = np.zeros(N)
    for rate, f, a, off in ((1.7, 4700, 0.010, 0.1), (2.3, 5100, 0.007, 0.5), (1.1, 4300, 0.005, 0.9)):
        for c0 in np.arange(off, PRE + SCENE + POST, 1 / rate):
            for k in range(3):
                i = int((c0 + k * 0.03 + rng.random() * 0.005) * SR); n = int(0.016 * SR)
                if i + n < N:
                    tt = np.arange(n) / SR
                    crick[i:i + n] += np.sin(2 * math.pi * f * tt) * np.sin(np.pi * tt / 0.016) * a * (0.7 + 0.6 * rng.random())
    fade = np.clip(t / 1.5, 0, 1) * np.clip((PRE + SCENE + POST - t) / 2.0, 0, 1)
    room = (wind + crick) * fade * 0.7
    buf[0] += room; buf[1] += room * 0.96
    room_stem = room.copy()
    # ---- the voice: calls are loud and near, the soft lines are quiet and close
    stems = {}
    plan = [('come_here', 1.0, 0.5), ('come_here2', 3.42, 0.58), ('all_right', 7.42, 0.23), ('all_right', 10.42, 0.22), ('come_in', 26.42, 0.22)]
    vlog = []
    for key, t0, g in plan:
        segs, f0 = LINES[key]
        sig = voice(segs, f0, 1.0, breath=0.05 if g > 0.3 else 0.35)
        sig = sig / (np.max(np.abs(sig)) + 1e-9)
        pan = -0.55
        place(buf, sig, t0, g, pan)
        vlog.append({'line': key, 't': t0, 'gain': g, 'rms_dbfs': round(rms_db(sig[np.abs(sig) > 0.02] * g), 2), 'peak_dbfs': round(20 * math.log10(g), 2)})
    # ---- the dog's claws on the boards, at the render's own foot contacts
    import dogrig
    contacts = 0
    prev = {}
    for f in trace:
        fs = SCORE['frames'][f['i']]['dog']
        if f['mode'] != 'rig' or fs['act']['moving'] <= 0.02 or f['posture'].startswith(('lying', 'standing, back')):
            prev = {}; continue
        s_ = (4.0 - fs['x']) * 125.0
        for leg, (pc, pv, ft, near, ph) in dogrig.LEGS.items():
            _, _, stance = dogrig.gait_foot(s_, ph, 70.0, 0.62, 70.0 * 0.62 / 2)
            if stance and prev.get(leg) is False:
                x = (f['feet_px'] or {}).get(leg, [640, 0])[0]
                pan = (x - 640) / 640 * 0.7
                g = (0.22 if near else 0.15) * (0.75 if fs['state'] == 'approach' else 1.0) * min(1.0, fs['act']['moving'] * 1.3)
                place(buf, tick(1.0), f['t'], g, pan)
                contacts += 1
            prev[leg] = stance
    # scuffles at the two turns
    for t0 in (3.42, 3.6, 7.66, 7.84):
        place(buf, tick(0.6), t0, 0.12, 0.6); place(buf, tick(0.4), t0 + 0.07, 0.10, 0.6)
    # ---- the person: steps back into the room, sits on the bench (5.4 - 6.5)
    for t0 in (5.55, 5.85, 6.15):
        place(buf, thump(0.2, 90) * 0.5, t0, 0.10, -0.6)
    place(buf, creak(0.45, 140, 210, 0.5), 6.35, 0.18, -0.7)
    # ---- the found door's swing: a creak while it opens (6.2 - 7.1), and a latch tick
    place(buf, tick(0.5), 6.2, 0.10, -0.5)
    place(buf, creak(0.9, 180, 330, 0.8), 6.22, 0.22, -0.45)
    # ---- the light comes out with a low warmth (a held chord, below the voices)
    n = N; tw = np.arange(n) / SR - PRE
    warm_env = np.clip((tw - 6.3) / 2.5, 0, 1) * (0.85 + 0.15 * np.clip((tw - 23.8) / 1.5, 0, 1)) * np.clip((SCENE + 2.5 - tw) / 2.5, 0, 1)
    warm = (np.sin(2 * math.pi * 110 * tw) * 0.5 + np.sin(2 * math.pi * 164.8 * tw) * 0.35 + np.sin(2 * math.pi * 277.2 * tw) * 0.18) * (1 + 0.15 * np.sin(2 * math.pi * 0.21 * tw))
    warm = warm * warm_env * 0.018
    buf[0] += warm; buf[1] += warm
    # ---- lying down across the sill, and the settle after it looks in
    place(buf, thump(0.3, 62), 24.25, 0.16, -0.1)
    place(buf, breath(0.9, 700, 1.0), 24.45, 0.05, -0.1)
    place(buf, breath(1.2, 600, 1.0), 28.45, 0.05, -0.1)
    # ---- title and end card: a single low tone each, under the room
    for t0 in (-2.6, SCENE + 0.4):
        nn = int(2.2 * SR); tt = np.arange(nn) / SR
        tone = np.sin(2 * math.pi * 220 * tt) * np.exp(-tt / 0.9) * 0.05
        place(buf, tone, t0, 1.0, 0)
    peak = np.max(np.abs(buf))
    if peak > 0.98:
        buf *= 0.98 / peak
    pcm = (buf.T * 32767).astype(np.int16)
    import wave
    with wave.open(os.path.join(FOLDER, 'build', 'cache', 'sound.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    mix = buf.mean(0)
    def win(t0, t1):
        return rms_db(mix[int((PRE + t0) * SR):int((PRE + t1) * SR)])
    bg = win(12.0, 14.0)
    mixlines = {f'{k}@{t0}': round(win(t0, t0 + sum(d for _, d, _ in LINES[k][0])) , 2) for k, t0, g in plan}
    room_db = rms_db(room_stem[int((PRE + 12) * SR):int((PRE + 14) * SR)])
    calls = [v['rms_dbfs'] for v in vlog if v['line'].startswith('come_here')]
    softs = [v['rms_dbfs'] for v in vlog if not v['line'].startswith('come_here')]
    rep = {'about': 'levels measured on the synthesised stems before mixing (rms over the voiced part, dBFS)', 'lines': vlog,
           'room_tone_rms_dbfs': round(room_db, 2), 'soft_minus_loudest_call_db': round(max(softs) - min(calls), 2),
           'soft_above_room_db': round(min(softs) - room_db, 2), 'claw_contacts': contacts,
           'in_mix': {'about': 'rms of the final mix over each line, and over 12-14 s (room tone + warmth, no events)', 'lines': mixlines, 'background_12_14s': round(bg, 2),
                      'soft_minus_loudest_call_db': round(max(v for k, v in mixlines.items() if not k.startswith('come_here')) - min(v for k, v in mixlines.items() if k.startswith('come_here')), 2),
                      'softest_line_above_background_db': round(min(v for k, v in mixlines.items() if not k.startswith('come_here')) - bg, 2)}}
    json.dump(rep, open(os.path.join(FOLDER, 'lineage', 'sound.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
