"""SCION-36 · the soundtrack, synthesized here from numbers (no samples), on the score's timeline and the onsets
measured from the render. 38 s: 3 s title, 32 s scene, 3 s end card.  python3 sound.py OUT.wav

The voice is a wordless formant murmur with the shape of the words (two syllables for "come here", three for
"it's all right", two for "come in"); calls are loud and pressed, the soft voice breathy and at least 6 dB lower.
Dusk: room tone, crickets, a projector's whir under the archive footage. Paws on boards follow the walk phase;
the lower leaf of the door creaks and its latch clicks; the dog settles with a soft thump."""
import json, os, sys, wave
import numpy as np
from scipy.signal import lfilter, butter

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
SR = 44100; T0 = 3.0; DUR = 38.0
N = int(DUR * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(36)
LEVELS = {}


def place(sig, t, gain=1.0, pan=0.0, tag=None):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i] * gain
    L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2) * 1.414; R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2) * 1.414
    if tag:
        LEVELS.setdefault(tag, []).append(float(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12)))


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2)); return lfilter(b, a, x)


def reson(x, f, bw):
    r = np.exp(-np.pi * bw / SR); w = 2 * np.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(w), r * r], x)


def env(n, a, d):
    e = np.ones(n); ai = max(1, int(a * SR)); di = max(1, int(d * SR))
    e[:ai] = np.linspace(0, 1, ai); e[-di:] *= np.linspace(1, 0, di) ** 1.5; return e


def syllable(dur, f0a, f0b, F1, F2, breath=0.0, press=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    f0 = np.linspace(f0a, f0b, n) * (1 + .012 * np.sin(2 * np.pi * 5.5 * tt))
    ph = np.cumsum(2 * np.pi * f0 / SR)
    src = np.zeros(n)
    for h in range(1, 18):
        src += np.sin(h * ph) / h ** (1.2 if press > .5 else 1.7)
    src = src * (1 - breath) + rng.standard_normal(n) * breath * .6
    F1v = np.linspace(F1[0], F1[1], n); F2v = np.linspace(F2[0], F2[1], n)
    # piecewise formant sweep in 8 blocks
    out = np.zeros(n); blk = n // 8 + 1
    for k in range(8):
        a, b = k * blk, min(n, (k + 1) * blk)
        if a >= n: break
        seg = src[a:b]
        out[a:b] = reson(seg, F1v[a], 90) * 1.0 + reson(seg, F2v[a], 120) * .6 + reson(seg, 2800, 200) * .25
    return out * env(n, .03, .09)


def phrase(sylls, t, gain, pan, tag):
    tt = t
    for s in sylls:
        sig = syllable(*s[:5], **(s[5] if len(s) > 5 else {}))
        sig /= np.abs(sig).max() + 1e-9
        place(sig, tt, gain, pan, tag); tt += s[0] + .04


def paw(t, gain, pan):
    n = int(.05 * SR); x = rng.standard_normal(n) * np.exp(-np.arange(n) / (.008 * SR))
    place(bp(x, 300, 1800), t, gain, pan, None)


def creak(t, dur, gain, pan):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 180 + 90 * np.sin(2 * np.pi * .7 * tt) + 40 * rng.standard_normal(n).cumsum() / np.sqrt(n)
    pulses = (np.sin(np.cumsum(2 * np.pi * f / SR)) > .97).astype(float)
    x = reson(pulses, 900, 300) + reson(pulses, 1900, 400) * .5
    place(x / (np.abs(x).max() + 1e-9) * env(n, .1, .2), t, gain, pan, None)


def click(t, gain, pan):
    n = int(.03 * SR); x = rng.standard_normal(n) * np.exp(-np.arange(n) / (.002 * SR))
    place(bp(x, 1500, 6000), t, gain, pan, None)


def main(out):
    tl = np.arange(N) / SR
    # dusk room tone and wind (whole film, quieter under the cards)
    tone = lp(rng.standard_normal(N), 300) * .05 + bp(rng.standard_normal(N), 400, 1200) * .006
    scene = ((tl > T0 - .5) & (tl < T0 + 32.5)).astype(float); scene = lp(scene, 3)
    L[:] += tone * (.35 + .65 * scene); R[:] += lp(rng.standard_normal(N), 300) * .05 * (.35 + .65 * scene)
    # crickets
    for k in range(3):
        f = 4300 + 350 * k; rate = 15 + 3 * k
        gate = (np.sin(2 * np.pi * rate * tl + k) > .3) * (np.sin(2 * np.pi * (.45 + .1 * k) * tl + 2 * k) > -.1)
        c = np.sin(2 * np.pi * f * tl) * lp(gate.astype(float), 200) * .010
        place(c * scene, 0, 1.0, -.6 + .6 * k)
    # projector whir (the archive under everything, louder on the cards)
    whir = bp(rng.standard_normal(N), 90, 500) * (1 + .5 * np.sin(2 * np.pi * 24 * tl)) * .012
    L[:] += whir * (1.6 - scene); R[:] += whir * (1.6 - scene)
    # voices: on the score's timeline; every voice starts at or before the dog's reaction
    on = json.load(open(os.path.join(HERE, 'cache', 'onsets.json')))['onsets'] if os.path.exists(os.path.join(HERE, 'cache', 'onsets.json')) else {}
    CALL = dict(press=1.0)
    come_here = [(.30, 235, 250, (640, 700), (1190, 1250), CALL), (.48, 290, 220, (330, 450), (2250, 1700), CALL)]
    call_t1 = min(SCORE['timeline'][0][0], on.get('retreat', {}).get('t', 9)) - .08
    phrase(come_here, T0 + call_t1, .32, -.45, 'call')
    phrase(come_here, T0 + call_t1 + .95, .30, -.45, 'call')
    call_t2 = min(3.4, on.get('refuse', {}).get('t', 9)) - .08
    phrase(come_here, T0 + call_t2, .36, -.45, 'call')
    phrase(come_here, T0 + call_t2 + .9, .34, -.45, 'call')
    SOFT = dict(press=0.0)
    allright = [(.18, 190, 185, (400, 420), (2000, 1900), SOFT), (.30, 185, 170, (700, 600), (1100, 900), SOFT),
                (.42, 175, 150, (700, 400), (1200, 2000), SOFT)]
    for st in (7.40, 10.40):
        st = min(st, on.get('watch_2', {}).get('t', 99) - .06) if st < 8 else st
        sig_t = T0 + st
        tt = sig_t
        for s in allright:
            x = syllable(*s[:5], breath=.55, press=0.0); x /= np.abs(x).max() + 1e-9
            place(x, tt, .085, -.35, 'soft'); tt += s[0] + .05
    come_in = [(.28, 195, 190, (640, 680), (1190, 1200), SOFT), (.40, 200, 160, (350, 300), (2200, 2100), SOFT)]
    st = min(26.30, on.get('look_in', {}).get('t', 99) - .05)
    tt = T0 + st
    for s in come_in:
        x = syllable(*s[:5], breath=.55, press=0.0); x /= np.abs(x).max() + 1e-9
        place(x, tt, .085, -.35, 'soft'); tt += s[0] + .05
    # paws: one tap each time a foot's walk phase passes a footfall
    fr = SCORE['frames']
    prev = None
    for f in fr:
        a = f['dog']['act']; ph = a['walk_phase']
        if prev is not None and a['moving'] > .2:
            for k in range(4):
                o = k * np.pi / 2
                if np.floor((prev + o) / (2 * np.pi)) != np.floor((ph + o) / (2 * np.pi)):
                    x = f['dog']['x']; pan = -.6 + .3 * x
                    paw(T0 + f['t'] + .01 * k, .05 + .03 * (1 - x / 5), pan)
        prev = ph
    # the person steps aside and sits (4.8 - 5.6)
    for k, tt in enumerate((4.85, 5.1, 5.32)):
        n = int(.06 * SR); x = rng.standard_normal(n) * np.exp(-np.arange(n) / (.012 * SR))
        place(lp(x, 900), T0 + tt, .12, -.55)
    rustle = bp(rng.standard_normal(int(.6 * SR)), 1500, 6000) * env(int(.6 * SR), .1, .3) * .03
    place(rustle, T0 + 5.4, 1.0, -.55)
    # door: latch at 6.2, creak while the lower leaf swings in, warm hum as the light comes out
    click(T0 + 6.18, .25, -.5); creak(T0 + 6.22, .75, .12, -.5)
    n = int(26 * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 110 * tt) + .4 * np.sin(2 * np.pi * 220 * tt)) * .006 * np.clip(tt / 1.0, 0, 1)
    place(hum * env(n, .5, 1.5), T0 + 6.3, 1.0, -.4)
    # the dog: a scuff as it turns away, a settle when it lies (4.4, 24.0), the tail on the boards at 27
    for tt, g in ((3.6, .06), (3.85, .05), (4.45, .07), (7.55, .04), (8.0, .05), (24.0, .10)):
        nn = int(.25 * SR); x = lp(rng.standard_normal(nn), 400) * env(nn, .01, .2)
        place(x / (np.abs(x).max() + 1e-9), T0 + tt, g, .3)
    for k in range(4):
        paw(T0 + 27.0 + k * .28, .025, -.2)
    mix = np.stack([L, R], 1)
    mix = mix / (np.abs(mix).max() + 1e-9) * .89
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    lv = {k: round(float(np.mean(v)), 2) for k, v in LEVELS.items()}
    json.dump({'voice_rms_db_before_master': lv, 'soft_minus_call_db': round(lv.get('soft', 0) - lv.get('call', 0), 2)},
              open(os.path.join(HERE, 'cache', 'sound_levels.json'), 'w'), indent=1)
    print('sound', lv)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cache', 'sound.wav'))
