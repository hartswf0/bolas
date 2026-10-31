"""SCION 40 · sound, all synthesized here (numpy), 48 kHz.
  - the voice: a small formant synthesizer (glottal pulses through three resonators, noise for consonants) speaking
    "Come here." (1.0 s), "Come here!" (3.4 s), "It's all right." (7.4 s, 10.4 s, soft, breathy) and "Come in." (26.4 s, soft).
    Every voice starts at or before the dog's reaction (calls at 0.95 and 3.36, soft voice at 7.36).
  - the paper: every recovered event in data/events.jsonl makes the sound of paper being handled: a swap is a card
    flick, a step of the walk is a soft tap of card on the table, the door is a stiff card creak, the light is tissue.
    So the sound is driven by the recovered event stream, like the picture.
  - room tone (low noise) and dusk crickets.
Writes cache/sound.wav (title 3 s + scene 32 s + end 3 s = 38 s) and data/sound_levels.json."""
import json, math, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SR = 48000
OFF = 3.0      # scene starts 3 s into the film
rng = np.random.default_rng(40)


def reson(x, f, bw):
    """2-pole resonator (python loop, fine for short utterances)"""
    r = math.exp(-math.pi * bw / SR)
    c = 2 * r * math.cos(2 * math.pi * f / SR)
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    g = 1 - r
    for n in range(len(x)):
        v = g * x[n] + c * y1 - r * r * y2
        y[n] = v; y2 = y1; y1 = v
    return y


def reson_tv(x, F, bw):
    """time-varying resonator, F per sample"""
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    r = math.exp(-math.pi * bw / SR)
    g = 1 - r
    cs = 2 * r * np.cos(2 * np.pi * F / SR)
    rr = r * r
    for n in range(len(x)):
        v = g * x[n] + cs[n] * y1 - rr * y2
        y[n] = v; y2 = y1; y1 = v
    return y


# phoneme targets: (F1, F2, F3, voiced, noise, nasal)
PH = {
    'k': (300, 1800, 2500, 0, 1.0, 0), 't': (300, 1800, 2700, 0, 1.0, 0), 's': (300, 1800, 2700, 0, 0.8, 0),
    'h': (500, 1500, 2500, 0, 0.5, 0), 'V': (640, 1190, 2390, 1, 0.0, 0), 'm': (250, 1100, 2200, 0.6, 0, 1),
    'n': (250, 1500, 2400, 0.6, 0, 1), 'I': (390, 1990, 2550, 1, 0, 0), 'E': (480, 1700, 2500, 1, 0, 0),
    'r': (420, 1300, 1700, 1, 0, 0), 'O': (570, 840, 2410, 1, 0, 0), 'l': (360, 1000, 2700, 0.9, 0, 0),
    'a': (750, 1250, 2500, 1, 0, 0), 'i': (300, 2200, 2900, 1, 0, 0), '_': (500, 1500, 2500, 0, 0, 0),
}


def say(phones, f0s, breath=0.05, rate=1.0):
    """phones: list of (symbol, dur s). f0s: list of (t_frac, hz) pitch contour."""
    total = sum(d for _, d in phones) / rate
    n = int(total * SR)
    t = np.arange(n) / SR
    # parameter tracks with smoothing (coarticulation)
    tr = np.zeros((n, 6))
    pos = 0
    for p, d in phones:
        k = int(d / rate * SR)
        tr[pos:pos + k] = PH[p]
        pos += k
    tr[pos:] = tr[pos - 1]
    ker = np.hanning(int(0.03 * SR)); ker /= ker.sum()
    for c in range(6):
        tr[:, c] = np.convolve(np.pad(tr[:, c], (len(ker), len(ker)), mode='edge'), ker, 'same')[len(ker):-len(ker)]
    fx = np.interp(t / total, [a for a, _ in f0s], [b for _, b in f0s])
    fx *= 1 + 0.01 * np.sin(2 * np.pi * 5.2 * t)
    ph = np.cumsum(fx / SR)
    saw = (ph % 1.0)
    glott = np.where(saw < 0.6, np.sin(np.pi * saw / 0.6) ** 2, 0) - 0.4
    src_v = glott * tr[:, 3] + rng.normal(0, 1, n) * breath * tr[:, 3]
    src_n = rng.normal(0, 1, n) * tr[:, 4]
    out = np.zeros(n)
    for c, bw, gain in ((0, 90, 1.0), (1, 120, 0.7), (2, 170, 0.35)):
        out += gain * reson_tv(src_v, tr[:, c], bw)
    hiss = reson_tv(src_n, np.maximum(tr[:, 2], 2500), 1800) * 0.9
    out += hiss
    # nasal murmur: low resonance
    out += 0.6 * reson(src_v * tr[:, 5], 260, 60)
    env = np.ones(n)
    a = int(0.015 * SR)
    env[:a] = np.linspace(0, 1, a); env[-a * 3:] = np.linspace(1, 0, a * 3)
    out *= env
    return out / (np.abs(out).max() + 1e-9)


def db(x):
    return 20 * math.log10(math.sqrt((x ** 2).mean()) + 1e-12)


def paper(kind, n_ms, amp):
    n = int(n_ms / 1000 * SR)
    x = rng.normal(0, 1, n)
    if kind == 'flick':
        env = np.exp(-np.arange(n) / (0.012 * SR))
        y = reson(x, 3200, 2500) * env
    elif kind == 'tap':
        env = np.exp(-np.arange(n) / (0.02 * SR))
        y = reson(x, 900, 600) * env + 0.5 * reson(x, 220, 80) * env
    elif kind == 'creak':
        t = np.arange(n) / SR
        f = 120 + 40 * np.sin(2 * np.pi * 3 * t)
        y = reson_tv(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + rng.normal(0, .3, n), 700 + 300 * np.sin(2 * np.pi * 1.5 * t), 300)
        y *= np.hanning(n)
    else:  # rustle / tissue
        env = np.hanning(n) * (0.6 + 0.4 * np.abs(rng.normal(0, 1, n)).clip(0, 2.5) / 2.5)
        y = reson(x, 4500, 4000) * env
    return amp * y / (np.abs(y).max() + 1e-9)


def main():
    total = 38.0
    mix = np.zeros(int(total * SR))
    # room tone and crickets for the scene
    s0, s1 = int(OFF * SR), int((OFF + 32) * SR)
    tone = np.cumsum(rng.normal(0, 1, s1 - s0)); tone -= np.convolve(tone, np.ones(4800) / 4800, 'same')
    tone = tone / np.abs(tone).max() * 0.006
    mix[s0:s1] += tone
    for k in range(70):
        tc = rng.uniform(0.2, 31.5)
        f = rng.uniform(4200, 4800)
        n = int(0.05 * SR)
        tt = np.arange(n) / SR
        chirp = np.sin(2 * np.pi * f * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.hanning(n) * 0.006
        a = s0 + int(tc * SR)
        mix[a:a + n] += chirp[:len(mix[a:a + n])]
    # the voice
    come_here = [('k', .05), ('V', .13), ('m', .09), ('h', .07), ('I', .16), ('E', .08), ('r', .14)]
    come_in = [('k', .05), ('V', .12), ('m', .08), ('I', .2), ('n', .16)]
    all_right = [('I', .07), ('t', .04), ('s', .1), ('O', .16), ('l', .08), ('r', .08), ('a', .14), ('i', .09), ('t', .05)]
    voices = [
        ('call', 0.95, say(come_here, [(0, 190), (.3, 235), (.6, 220), (1, 160)], breath=0.02), 0.50),
        ('call', 3.36, say(come_here, [(0, 210), (.3, 265), (.6, 245), (1, 175)], breath=0.02), 0.62),
        ('soft', 7.36, say(all_right, [(0, 165), (.4, 150), (1, 115)], breath=0.35, rate=0.82), 0.14),
        ('soft', 10.36, say(all_right, [(0, 160), (.4, 148), (1, 112)], breath=0.35, rate=0.8), 0.13),
        ('soft', 26.36, say(come_in, [(0, 160), (.5, 150), (1, 120)], breath=0.35, rate=0.85), 0.14),
    ]
    levels = []
    for kind, t, v, amp in voices:
        a = int((OFF + t) * SR)
        seg = v * amp
        mix[a:a + len(seg)] += seg
        levels.append(dict(kind=kind, t_start=t, dur=round(len(seg) / SR, 3), rms_db=round(db(seg), 2)))
    # paper sounds from the recovered event stream
    ev = [json.loads(l) for l in open(os.path.join(DATA, 'events.jsonl'))]
    for e in ev:
        a = int((OFF + e['t']) * SR)
        if e['ev'] == 'swap':
            if e['piece'] == 'dog.body' and e['to'].startswith(('b_walk', 'b_back', 'b_step')):
                s = paper('tap', 60, 0.05)
            elif e['piece'] == 'door':
                s = paper('creak', 380, 0.05)
            else:
                s = paper('flick', 70, 0.035)
        elif e['ev'] == 'move':
            s = paper('rustle', 240 if e['piece'] != 'light' else 600, 0.02 if e['piece'] != 'light' else 0.03)
        elif e['ev'] in ('hand_on', 'hand_off'):
            s = paper('rustle', 120, 0.012)
        else:
            continue
        mix[a:a + len(s)] += s[:len(mix[a:a + len(s)])]
    room = db(mix[s0 + int(13 * SR):s0 + int(14 * SR)])
    calls = [l['rms_db'] for l in levels if l['kind'] == 'call']
    softs = [l['rms_db'] for l in levels if l['kind'] == 'soft']
    info = dict(voices=levels, room_tone_rms_db=round(room, 2), quietest_call_minus_loudest_soft_db=round(min(calls) - max(softs), 2),
                softest_voice_minus_room_db=round(min(softs) - room, 2), note='rms of each utterance alone; room = 13-14 s of the scene mix without voice')
    json.dump(info, open(os.path.join(DATA, 'sound_levels.json'), 'w'), indent=1)
    print(json.dumps(info))
    mix = np.clip(mix, -1, 1)
    st = np.stack([mix, mix], 1)
    with wave.open(os.path.join(CACHE, 'sound.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    main()
