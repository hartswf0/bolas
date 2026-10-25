"""SCION 46 sound: everything synthesized here (numpy), timed from the same state as the picture.
- the person's voice: formant synthesis of timed syllables (voice.py, shared with the face's mouth substitution)
- paws on the porch boards: one click+thump per foot contact from the stepper (cache/contacts.json), panned by screen x
- the door's creak (from its hinge angle), the room's sound coming out once it is open (a clock, a warm hum)
- the dog's collar tag on its turns, its breath when it lies down; dusk room tone and crickets
Writes build/cache/scene.wav (32 s) and build/cache/sound_levels.json (measured levels of the voice classes)."""
import json, math, os, wave
import numpy as np
from geom import CACHE, Camera, W
import voice

SR = 48000
DUR = 32.0
N = int(SR * DUR)
rng = np.random.default_rng(46)


def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y


def onepole(x, fc):
    a = 1 - math.exp(-2 * math.pi * fc / SR)
    # vectorised approximation via cumulative filtering in blocks (exact recursion done with lfilter-like loop on short signals)
    return lp(x, a) if len(x) < 200000 else lp_fast(x, a)


def lp_fast(x, a):
    # exact one-pole recursion using numpy in chunks
    y = np.empty_like(x); acc = 0.0; B = 4096
    for s in range(0, len(x), B):
        seg = x[s:s + B]
        k = np.arange(len(seg))
        decay = (1 - a) ** (k + 1)
        # y[n] = (1-a)^(n+1) acc + a * sum_{m<=n} (1-a)^(n-m) x[m]
        w = (1 - a) ** (-(k).astype(float))
        cs = np.cumsum(seg * w)
        y[s:s + B] = decay * acc + a * cs * (1 - a) ** k
        acc = y[s + len(seg) - 1]
    return y


def biquad_bp(x, f0, q):
    w0 = 2 * math.pi * f0 / SR; al = math.sin(w0) / (2 * q)
    b0, b1, b2 = al, 0.0, -al; a0, a1, a2 = 1 + al, -2 * math.cos(w0), 1 - al
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        v = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x[i]; y2, y1 = y1, v; y[i] = v
    return y


def place(buf, sig, t, gain=1.0, pan=0.0):
    i0 = int(t * SR)
    if i0 >= N: return
    sig = sig[:N - i0]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[i0:i0 + len(sig), 0] += sig * gain * l * 1.41
    buf[i0:i0 + len(sig), 1] += sig * gain * r * 1.41


FORM = {'uh': [(640, 80), (1190, 90), (2390, 120)], 'ee': [(300, 60), (2250, 100), (2950, 140)], 'ih': [(400, 70), (1950, 100), (2550, 130)],
        'aw': [(590, 80), (880, 90), (2400, 130)], 'ai': [(720, 80), (1150, 90), (2450, 120)]}
ONSET = {('uh', 0): 'k', ('ee', 1): 'h', ('ih', 4): 's', ('aw', 5): '', ('ai', 6): 'r', ('ih', 7): 's', ('aw', 8): '', ('ai', 9): 'r',
         ('uh', 10): 'k', ('ih', 11): ''}


def syllable(k, s, e, amp, f0a, f0b, vow):
    n = int((e - s) * SR); t = np.arange(n) / SR
    f0 = f0a + (f0b - f0a) * (t / max(1e-6, t[-1])) + 3 * np.sin(2 * math.pi * 5.2 * t)
    ph = np.cumsum(f0 / SR)
    # glottal source: band-limited saw with soft shape, plus breath for the soft voice
    src = np.zeros(n)
    for h in range(1, 28):
        src += np.sin(2 * math.pi * h * ph) / h * (1.0 if h < 12 else 0.6)
    breath = rng.normal(0, 1, n) * (0.35 if amp < 0.5 else 0.08)
    src = src + breath
    out = np.zeros(n)
    F = FORM[vow]
    if vow == 'ai':
        # diphthong: two halves
        h = n // 2
        for (fa, bw), (fb, _) in zip(F, FORM['ee']):
            out[:h] += biquad_bp(src[:h], fa, fa / bw)
            out[h:] += biquad_bp(src[h:], (fa + fb) / 2, fa / bw)
    else:
        for fq, bw in F: out += biquad_bp(src, fq, fq / bw)
    env = np.minimum(1, t / 0.035) * np.minimum(1, (t[-1] - t) / 0.09)
    out *= env
    c = ONSET.get((vow, k), '')
    if c:
        cn = int((0.05 if c in 'kt' else 0.09) * SR)
        noise = rng.normal(0, 1, cn)
        fc = {'k': 2200, 'h': 1500, 's': 6000, 'r': 900, 't': 3500}[c]
        burst = biquad_bp(noise, fc, 1.5 if c != 's' else 3) * np.linspace(1, 0, cn) ** 1.5 * (0.7 if c != 'h' else 0.35)
        out = np.concatenate([burst, out])
    out /= (np.abs(out).max() + 1e-9)
    return out * amp


def paw(scale):
    n = int(0.09 * SR); t = np.arange(n) / SR
    click = rng.normal(0, 1, n) * np.exp(-t / 0.004)
    click = biquad_bp(click, 3800, 2.0)
    thump = np.sin(2 * math.pi * 140 * t) * np.exp(-t / 0.025) * 0.6
    return (click * 0.5 + thump) * scale


def tag_jingle(dur):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for k in range(int(dur * 14)):
        t0 = rng.uniform(0, dur * 0.8); f = rng.uniform(3200, 5200)
        m = t >= t0
        out[m] += np.sin(2 * math.pi * f * (t[m] - t0)) * np.exp(-(t[m] - t0) / 0.05) * rng.uniform(0.2, 0.6)
    return out


def creak(dur, f0=320):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 + 140 * np.sin(2 * math.pi * 0.7 * t) + 60 * rng.normal(0, 1, n).cumsum() / np.sqrt(np.arange(1, n + 1))
    ph = np.cumsum(f / SR)
    pulses = (np.sin(2 * math.pi * ph) > 0.92).astype(float)
    sig = biquad_bp(pulses, 900, 3) + 0.5 * biquad_bp(pulses, 2100, 5)
    env = np.minimum(1, t / 0.1) * np.minimum(1, (t[-1] - t) / 0.3)
    return sig * env


def breath(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    no = rng.normal(0, 1, n)
    sig = biquad_bp(no, 700, 0.8) + 0.5 * biquad_bp(no, 1800, 1.5)
    env = np.sin(math.pi * t / dur) ** 1.5
    return sig * env


def write_wav(path, buf):
    b = np.clip(buf, -1, 1)
    pcm = (b * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def db(x): return 20 * math.log10(max(1e-12, x))


def main():
    rig = json.load(open(os.path.join(CACHE, 'rig.json')))
    pose = json.load(open(os.path.join(CACHE, 'pose.json')))
    contacts = json.load(open(os.path.join(CACHE, 'contacts.json')))
    stems = {k: np.zeros((N, 2)) for k in ('room', 'voice_call', 'voice_soft', 'paws', 'door', 'house', 'dog', 'person')}
    # room tone: low wind
    no = rng.normal(0, 1, N)
    wind = lp_fast(no, 1 - math.exp(-2 * math.pi * 300 / SR))
    wind = wind / np.abs(wind).max()
    sway = 0.6 + 0.4 * np.sin(2 * math.pi * np.arange(N) / SR / 7.0)
    stems['room'][:, 0] += wind * sway * 0.05; stems['room'][:, 1] += np.roll(wind, 999) * sway * 0.05
    # crickets: pulsed 4.6 kHz
    t = np.arange(N) / SR
    for k, (f, rate, ph, pan) in enumerate(((4600, 2.1, 0.0, 0.7), (4300, 1.7, 0.4, -0.5), (4900, 2.6, 0.2, 0.2))):
        gate = ((np.sin(2 * math.pi * rate * t + ph) > 0.4) * (np.sin(2 * math.pi * 30 * t) > 0)).astype(float)
        gate = lp_fast(gate, 0.02)
        sig = np.sin(2 * math.pi * f * t) * gate * 0.005 * (0.6 + 0.4 * np.sin(2 * math.pi * t / (9 + 4 * k) + k))
        place(stems['room'], sig, 0.0, 1.0, pan)
    # voice
    for k, (s, e, amp, fa, fb, vow) in enumerate(voice.SYL):
        sig = syllable(k, s, e, amp, fa, fb, vow)
        key = 'voice_call' if amp >= 0.9 else 'voice_soft'
        pre = 0.05 if vow in ('uh', 'ee', 'ih') and ONSET.get((vow, k)) else 0.0
        place(stems[key], sig, s - pre, 0.36, -0.45 if rig[int(s * 24)]['person']['X'] > -0.8 else -0.6)
    # paws: from the solver's foot contacts, panned by where the dog is on screen
    for (tc, leg) in contacts:
        i = min(767, int(tc * 24)); f = rig[i]; c = f['camera']; cam = Camera(c['pos'], c['target'], c['fov'])
        x = cam.project(np.array(pose[i]['legs'][leg][-1]))[0][0][0]
        pan = max(-0.9, min(0.9, (x / W) * 2 - 1))
        moving = f['moving']
        g = 0.10 + 0.08 * (f['state'] == 'retreat')
        place(stems['paws'], paw(1.0), tc, g * (0.6 + 0.4 * moving), pan)
    # dog: collar tag on the turns and on lying down; breath when it settles
    for (t0, d, g) in ((3.48, 0.45, 0.05), (7.46, 0.3, 0.035), (8.0, 0.5, 0.045), (23.85, 0.5, 0.04), (26.42, 0.35, 0.03), (28.1, 0.3, 0.02)):
        place(stems['dog'], tag_jingle(d), t0, g, 0.2)
    place(stems['dog'], breath(1.0), 24.45, 0.05, 0.0)
    place(stems['dog'], breath(1.3), 28.4, 0.035, 0.0)
    for ts in (16.2, 19.6, 22.1):     # sniffs on the way in
        for q in range(3): place(stems['dog'], breath(0.07), ts + q * 0.11, 0.03, 0.1)
    # person: steps aside (two steps) and sits (cloth and a floor creak)
    for ts in (5.42, 5.88):
        n = int(0.12 * SR); tt = np.arange(n) / SR
        place(stems['person'], np.sin(2 * math.pi * 90 * tt) * np.exp(-tt / 0.04) + 0.2 * rng.normal(0, 1, n) * np.exp(-tt / 0.01), ts, 0.13, -0.6)
    place(stems['person'], breath(0.6) * 0.6, 6.1, 0.04, -0.6)
    place(stems['person'], creak(0.35, 180), 6.35, 0.03, -0.6)
    # door creak while it swings (6.2-7.3), then the house's sound comes out with the light
    place(stems['door'], creak(1.15), 6.18, 0.07, -0.35)
    openf = np.array([min(1.0, max(0.0, (rig[min(767, int(x * 24))]['door'] - 9) / 87)) for x in np.arange(N)[::480] / SR])
    openf = np.repeat(openf, 480)[:N]
    hum = lp_fast(rng.normal(0, 1, N), 1 - math.exp(-2 * math.pi * 180 / SR)); hum /= np.abs(hum).max()
    house = hum * 0.03 * (0.25 + 0.75 * openf)
    for tk in np.arange(0.5, 32, 1.0):   # a clock in the room, heard only through the door
        n = int(0.03 * SR); tt = np.arange(n) / SR
        g = 0.25 + 0.75 * openf[min(N - 1, int(tk * SR))]
        tick = biquad_bp(rng.normal(0, 1, n) * np.exp(-tt / 0.003), 2600 if int(tk) % 2 else 2300, 4) * g * 0.03
        i0 = int(tk * SR); house[i0:i0 + n] += tick[:max(0, min(n, N - i0))]
    stems['house'][:, 0] += house * 0.9; stems['house'][:, 1] += house * 0.6
    mix = sum(stems.values())
    peak = np.abs(mix).max(); g = 0.89 / peak if peak > 0.89 else 1.0
    mix *= g
    write_wav(os.path.join(CACHE, 'scene.wav'), mix)
    # measured levels (RMS over each class's own syllables, and room tone in a quiet stretch)
    def rms_over(stem, spans):
        idx = np.concatenate([np.arange(int(a * SR), int(b * SR)) for a, b in spans])
        return math.sqrt(float((stem[idx] ** 2).mean())) * g
    calls = [(s, e) for s, e, a, *_ in voice.SYL if a >= 0.9]; softs = [(s, e) for s, e, a, *_ in voice.SYL if a < 0.9]
    lv = dict(call_rms_db=db(rms_over(stems['voice_call'], calls)), soft_rms_db=db(rms_over(stems['voice_soft'], softs)),
              room_tone_db=db(rms_over(stems['room'] + stems['house'], [(12.0, 14.0)])),
              mix_peak_db=db(np.abs(mix).max()))
    lv['soft_minus_call_db'] = lv['soft_rms_db'] - lv['call_rms_db']
    lv['soft_minus_room_db'] = lv['soft_rms_db'] - lv['room_tone_db']
    json.dump({k: round(v, 2) for k, v in lv.items()}, open(os.path.join(CACHE, 'sound_levels.json'), 'w'), indent=1)
    print(lv)


if __name__ == '__main__':
    main()
