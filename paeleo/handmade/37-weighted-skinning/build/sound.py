"""SCION 37 sound, all synthesized here (no recordings): dusk room tone (crickets, air), the person's voice (a source-filter
formant synthesizer: glottal pulses through resonators, consonant noise), the door's creak and the room's clock once it is
open, the dog's claws on the boards from the gait solver's touch-downs, its body settling, its tail knocking the sill.
Writes cache/scene.wav (32 s) and cache/levels.json (measured RMS of calls, soft voice and room tone)."""
import json, os
import numpy as np
from scipy.signal import lfilter, butter
import raster

HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
SR = 48000; DUR = 32.0; N = int(SR * DUR)
rng = np.random.default_rng(37)
PF = dict(np.load(os.path.join(CACHE, 'perform.npz')))


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)

def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2)); return lfilter(b, a, x)

def hp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), 'high'); return lfilter(b, a, x)

def reson(x, f, bw):
    r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)

def env(n, a=.01, r=.05):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)

# ------------------------------------------------------------------ voice
VOW = {'ʌ': (640, 1190, 2390), 'ɪ': (400, 1920, 2550), 'ə': (500, 1500, 2500), 'ɔ': (570, 840, 2410), 'a': (730, 1090, 2440),
       'i': (300, 2250, 2900), 'm': (280, 1000, 2200), 'n': (280, 1500, 2500), 'l': (360, 1000, 2400), 'r': (420, 1300, 1700)}

def phrase(segs, f0, soft=False):
    """segs: list of (kind, dur): kind a vowel/sonorant key, or 'k','t','s','h' for noise consonants"""
    out = []
    tot = sum(d for _, d in segs); t0 = 0
    ph = 0.
    for kind, d in segs:
        n = int(d * SR); tt = (t0 + np.arange(n) / SR) / tot
        if kind in ('k', 't', 's', 'h'):
            nz = rng.normal(0, 1, n)
            if kind == 'k': x = bp(nz, 1800, 3500) * np.exp(-np.arange(n) / (.012 * SR)) * 1.4
            elif kind == 't': x = bp(nz, 3000, 6000) * np.exp(-np.arange(n) / (.010 * SR)) * 1.2
            elif kind == 's': x = bp(nz, 4500, 9000) * env(n, .02, .03) * .7
            else: x = bp(nz, 500, 2500) * env(n, .02, .03) * .5
            out.append(x * (.5 if soft else 1.)); t0 += d; continue
        f = f0(tt) * (1 + .006 * rng.normal(0, 1, n).cumsum() / np.sqrt(np.arange(1, n + 1)))
        ph_arr = ph + np.cumsum(2 * np.pi * f / SR); ph = ph_arr[-1]
        saw = ((ph_arr / (2 * np.pi)) % 1.) * 2 - 1
        src = lp(-saw, 3500 if not soft else 1800, 1)
        if soft: src = src * .55 + bp(rng.normal(0, 1, n), 300, 4000) * .45
        F = VOW[kind]
        x = sum(reson(src, fq, bw) * g for fq, bw, g in zip(F, (80, 100, 140), (1., .7, .35)))
        if kind in ('m', 'n'): x = lp(x, 900) * .7
        out.append(x * env(n, .015, .02)); t0 += d
    y = np.concatenate(out)
    return y / (np.abs(y).max() + 1e-9)

def call_f0(base):
    return lambda u: base * (1 + .25 * np.sin(np.pi * np.clip(u * 1.2, 0, 1))) * (1 - .12 * u)

def soft_f0(base):
    return lambda u: base * (1 + .08 * np.sin(np.pi * u)) * (1 - .15 * u)

COME_HERE = [('k', .05), ('ʌ', .16), ('m', .10), ('h', .07), ('ɪ', .20), ('ə', .14), ('r', .10)]
ALL_RIGHT = [('ɪ', .08), ('t', .03), ('s', .08), ('ɔ', .18), ('l', .10), ('r', .06), ('a', .20), ('ɪ', .08), ('t', .04)]
COME_IN = [('k', .05), ('ʌ', .14), ('m', .08), ('ɪ', .18), ('n', .16)]

# ------------------------------------------------------------------ world sounds
def crickets():
    t = np.arange(N) / SR; y = np.zeros(N)
    for k, (f, rate, ph) in enumerate(((4300, 1.7, 0), (4700, 2.3, .4), (3900, 1.1, .7))):
        chirp = (np.sin(2 * np.pi * rate * t + ph * 6) > .55).astype(float)
        pulses = (np.sin(2 * np.pi * 28 * t) > 0).astype(float)
        e = lp(chirp * pulses, 300, 1)
        y += np.sin(2 * np.pi * f * t) * e * (.5 + .2 * k)
    return y

def air():
    return lp(rng.normal(0, 1, N), 400, 2) + .3 * bp(rng.normal(0, 1, N), 800, 3000)

def creak(n):
    t = np.arange(n) / SR
    f = 160 + 90 * np.sin(2 * np.pi * .9 * t) + 30 * rng.normal(0, 1, n).cumsum() / SR * 20
    ph = np.cumsum(2 * np.pi * f / SR); stick = (np.sin(ph) > .7).astype(float)
    x = bp(stick + .2 * rng.normal(0, 1, n), 300, 2500)
    return x * env(n, .05, .2) * (.6 + .4 * np.sin(2 * np.pi * 2.3 * t))

def click(n=int(.05 * SR), bright=1.):
    nz = rng.normal(0, 1, n); e = np.exp(-np.arange(n) / (.006 * SR))
    return (bp(nz, 1500, 5000) * bright + lp(nz, 400) * 1.5) * e

def thump(dur=.25, f=70):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 - .3 * t / dur)) * np.exp(-t / (dur / 4)) + .3 * lp(rng.normal(0, 1, n), 300) * np.exp(-t / .03))

def sigh(dur=1.1):
    n = int(dur * SR); x = bp(rng.normal(0, 1, n), 250, 1600)
    return x * np.sin(np.pi * np.arange(n) / n) ** 2


def place(buf, x, t, gain=1., pan=0.):
    i = int(t * SR); x = x[:max(0, min(len(x), N - i))]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(x)] += x * gain * l; buf[1, i:i + len(x)] += x * gain * r


def main():
    bus = {k: np.zeros((2, N)) for k in ('tone', 'voice', 'soft', 'fx', 'claw')}
    tone = crickets() * .010 + air() * .006
    bus['tone'] += tone
    # the dog's screen side for panning (projected root with the per-frame camera)
    def dog_pan(i):
        cam = raster.Camera(PF['cam_eye'][i], PF['cam_target'][i], PF['cam_f'][i], 1280, 720)
        xy, _ = cam.project(PF['dog_root'][i][None, :3, 3]); return float(np.clip((xy[0, 0] - 640) / 700, -1, 1))
    # voice: calls (the person in the doorway, left of frame) and the soft voice
    for t in (1.02, 3.42):
        v = phrase(COME_HERE, call_f0(185 if t < 2 else 200))
        place(bus['voice'], v, t, .32, -.45)
    for t in (7.45, 10.45):
        place(bus["soft"], phrase(ALL_RIGHT, soft_f0(150), soft=True), t, .13, -.2)
    place(bus["soft"], phrase(COME_IN, soft_f0(145), soft=True), 26.42, .13, .1)
    # the door: creak while it swings, then the room's clock is heard
    place(bus['fx'], creak(int(.85 * SR)), 6.2, .05, -.4)
    for k in range(int(6.9) + 1, 32):
        place(bus['fx'], click(int(.02 * SR), 2.) * .5, k + .03, .012 * min(1, (k - 6.5) / 2), -.5)
    # the dog's paws: every touch-down in the gait solver is a claw on the boards
    C = PF['contact']; lie = PF['lie']
    for i in range(1, len(C)):
        for k in range(4):
            if C[i, k] and not C[i - 1, k] and lie[i] < .5:
                place(bus['claw'], click(bright=.8 + .4 * rng.random()), i / 24 + rng.random() * .01, .16, dog_pan(i))
    # lying down: the body meets the boards; settling sigh; tail knocks while it looks in
    place(bus['fx'], thump(.3, 65), 4.85, .20, dog_pan(116)); place(bus['fx'], thump(.3, 60), 24.40, .22, dog_pan(586))
    place(bus['fx'], sigh(), 28.55, .05, dog_pan(686))
    place(bus['fx'], sigh(.9), 6.0, .035, dog_pan(144))
    for t in np.arange(26.75, 28.3, .42):
        place(bus['fx'], thump(.12, 120) * .6, t, .10, dog_pan(int(t * 24)))
    # the person: steps aside, the crate takes the weight
    for t in (4.68, 5.0, 5.3):
        place(bus["fx"], thump(.10, 90) * .8 + click(int(.10 * SR)) * .3, t, .07, -.3)
    place(bus['fx'], creak(int(.35 * SR)), 5.62, .035, -.1)
    mix = sum(bus.values())
    # measured levels (active windows only)
    def win(b, spans): return np.concatenate([b[0, int(a * SR):int(c * SR)] for a, c in spans])
    lv = {'call_rms_db': rms_db(win(bus['voice'], [(1.05, 1.85), (3.45, 4.25)])),
          'soft_rms_db': rms_db(win(bus['soft'], [(7.5, 8.3), (10.5, 11.3), (26.45, 27.0)])),
          'room_tone_rms_db': rms_db(bus['tone'][0])}
    lv['soft_below_call_db'] = lv['call_rms_db'] - lv['soft_rms_db']
    lv['claw_approach_rms_db'] = rms_db(win(bus['claw'], [(15.0, 23.6)]))
    lv['claw_above_tone_db'] = lv['claw_approach_rms_db'] - lv['room_tone_rms_db']
    lv['soft_above_tone_db'] = lv['soft_rms_db'] - lv['room_tone_rms_db']
    peak = np.abs(mix).max(); mix = mix / max(peak, 1e-9) * .89 if peak > .89 else mix
    import wave
    w = wave.open(os.path.join(CACHE, 'scene.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix.T, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    json.dump({k: round(v, 2) for k, v in lv.items()}, open(os.path.join(CACHE, 'levels.json'), 'w'), indent=1)
    print(json.dumps({k: round(v, 2) for k, v in lv.items()}))


if __name__ == '__main__':
    main()
