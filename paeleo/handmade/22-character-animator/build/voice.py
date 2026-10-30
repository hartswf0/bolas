"""SCION 22 · the person's voice, synthesized here (Klatt-style cascade formant synthesis: glottal pulse source,
aspiration and frication noise, four time-varying resonators).  No recording, no performer, no TTS engine.
Writes cache/voice.wav (mono 44.1 kHz float->16 bit) and cache/voice_lines.json (text, start, level)."""
import numpy as np, json, os, wave
from common import CACHE

FS = 44100
rng = np.random.default_rng(22)

# phoneme targets: (F1, F2, F3, AV voicing, AH aspiration, AF frication, fric centre Hz, fric bw Hz)
P = {
    'AH': (820, 1550, 2850, 1.0, 0.02, 0, 0, 0),     # cup
    'IH': (470, 2150, 2950, 1.0, 0.02, 0, 0, 0),     # hit / here
    'AX': (600, 1550, 2700, 0.9, 0.03, 0, 0, 0),     # schwa
    'AO': (660, 980, 2700, 1.0, 0.02, 0, 0, 0),      # all
    'AA': (880, 1300, 2800, 1.0, 0.02, 0, 0, 0),     # first half of 'right'
    'IY': (420, 2350, 3050, 0.9, 0.02, 0, 0, 0),     # second half of 'right'
    'L': (400, 1050, 2800, 0.55, 0.0, 0, 0, 0),
    'R': (430, 1250, 1750, 0.65, 0.0, 0, 0, 0),
    'M': (290, 1150, 2600, 0.38, 0.0, 0, 0, 0),
    'N': (290, 1650, 2650, 0.38, 0.0, 0, 0, 0),
    'HH': (700, 1800, 2800, 0.0, 0.45, 0, 0, 0),
    'K0': (400, 1800, 2700, 0.0, 0.0, 0, 0, 0),      # closure (silence)
    'KB': (500, 1800, 2700, 0.0, 0.30, 0.55, 2600, 1400),   # burst + aspiration
    'T0': (400, 1800, 2700, 0.0, 0.0, 0, 0, 0),
    'TB': (500, 1800, 2700, 0.0, 0.10, 0.6, 4200, 2200),
    'S': (500, 1800, 2700, 0.0, 0.0, 0.85, 6200, 3200),
    'SIL': (500, 1500, 2600, 0.0, 0.0, 0, 0, 0),
}

LINES = [
    # text, start s, phones [(name, ms)], f0 contour (Hz at 0, peak, end), gain dB, breathiness
    ('Come here!', 1.02, [('K0', 30), ('KB', 45), ('AH', 150), ('M', 110), ('HH', 85), ('IH', 150), ('AX', 300)], (225, 290, 205), 0.0, 0.0),
    ('Come here!', 3.44, [('K0', 25), ('KB', 45), ('AH', 160), ('M', 100), ('HH', 80), ('IH', 170), ('AX', 330)], (240, 315, 215), 1.0, 0.0),
    ("It's all right.", 7.46, [('IH', 85), ('T0', 45), ('TB', 20), ('S', 120), ('AO', 170), ('L', 90), ('R', 80), ('AA', 150), ('IY', 120), ('T0', 50), ('TB', 25)], (205, 215, 165), -11.0, 0.55),
    ("It's all right.", 10.46, [('IH', 90), ('T0', 45), ('TB', 20), ('S', 125), ('AO', 190), ('L', 95), ('R', 85), ('AA', 160), ('IY', 130), ('T0', 50), ('TB', 25)], (200, 210, 160), -11.5, 0.6),
    ('Come in.', 26.44, [('K0', 30), ('KB', 40), ('AH', 130), ('M', 95), ('IH', 170), ('N', 210)], (205, 220, 170), -11.0, 0.55),
]


def resonator(x, F, B):
    """time-varying 2-pole resonator, F and B per sample"""
    C = -np.exp(-2 * np.pi * B / FS)
    Bc = 2 * np.exp(-np.pi * B / FS) * np.cos(2 * np.pi * F / FS)
    A = 1 - Bc - C
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    for n in range(len(x)):
        v = A[n] * x[n] + Bc[n] * y1 + C[n] * y2
        y[n] = v; y2 = y1; y1 = v
    return y


def smooth(a, ms):
    k = max(1, int(FS * ms / 1000))
    ker = np.hanning(2 * k + 1); ker /= ker.sum()
    pad = np.pad(a, (k, k), mode='edge')
    return np.convolve(pad, ker, mode='valid')


def synth_line(phones, f0c, breath):
    total = sum(ms for _, ms in phones)
    n = int(FS * (total + 120) / 1000)
    tracks = np.zeros((8, n))
    pos = 0
    for name, ms in phones:
        k = int(FS * ms / 1000)
        tracks[:, pos:pos + k] = np.array(P[name])[:, None]
        pos += k
    tracks[:, pos:] = np.array(P['SIL'])[:, None]
    tracks[3, pos:] = 0
    F1, F2, F3 = smooth(tracks[0], 28), smooth(tracks[1], 32), smooth(tracks[2], 32)
    AV, AH, AF = smooth(tracks[3], 14), smooth(tracks[4], 10), smooth(tracks[5], 6)
    FC, FB = smooth(tracks[6], 5), smooth(tracks[7], 5)
    t = np.arange(n) / FS
    T = total / 1000
    u = np.clip(t / T, 0, 1)
    f0 = np.where(u < 0.35, f0c[0] + (f0c[1] - f0c[0]) * np.sin(u / 0.35 * np.pi / 2), f0c[1] + (f0c[2] - f0c[1]) * (np.clip(u - 0.35, 0, None) / 0.65) ** 1.2)
    f0 = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.3 * t)) * (1 + 0.004 * smooth(rng.standard_normal(n), 12))
    ph = np.cumsum(f0 / FS) % 1.0
    # Rosenberg glottal pulse: slow opening, fast closing (the abrupt closure gives the -12 dB/oct source of real voices)
    tp, tn = 0.40 + 0.08 * breath, 0.16 + 0.10 * breath
    flow = np.where(ph < tp, 0.5 * (1 - np.cos(np.pi * ph / tp)),
                    np.where(ph < tp + tn, np.cos(np.pi * (ph - tp) / (2 * tn)), 0.0))
    src = np.diff(flow, prepend=0.0) * 30
    src = src * (1 + 0.05 * smooth(rng.standard_normal(n), 3))       # shimmer
    noise = rng.standard_normal(n)
    asp = noise * (AH + breath * 0.18 * AV) * 0.35
    exc = src * AV + asp
    if breath > 0:   # softer glottal edge: spectral tilt
        a = 0.35 * breath
        exc = np.array(exc); exc[1:] = exc[1:] * (1 - a) + exc[:-1] * a
    y = exc
    for F, B in ((F1, 80 + 60 * breath), (F2, 110 + 40 * breath), (F3, 170), (np.full(n, 3900.0), 250), (np.full(n, 4700.0), 300)):
        y = resonator(y, F, np.broadcast_to(B, (n,)).astype(float) if np.isscalar(B) else B)
    # frication: parallel band of noise (fixed-centre resonator per phone, smoothed centre)
    fr = resonator(rng.standard_normal(n), FC.clip(500, 9000), FB.clip(300, 5000)) * AF * 0.9
    out = y + fr
    env = np.ones(n); f = int(0.006 * FS); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    return out * env, total / 1000


def main():
    dur = 32.0
    voice = np.zeros(int(FS * dur))
    info = []
    for text, start, phones, f0c, gain, breath in LINES:
        y, d = synth_line(phones, f0c, breath)
        y = y / (np.sqrt(np.mean(y[: int(d * FS)] ** 2)) + 1e-9)        # unit RMS, then gain
        y = y * 0.12 * 10 ** (gain / 20)
        i0 = int(start * FS)
        voice[i0:i0 + len(y)] += y[: len(voice) - i0]
        seg = voice[i0:i0 + int(d * FS)]
        info.append({'text': text, 'start': start, 'end': round(start + d, 3), 'rms_dbfs': round(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12), 2),
                     'phones': [p for p, _ in phones], 'f0_hz': list(f0c), 'breathiness': breath})
    pk = np.max(np.abs(voice))
    if pk > 0.95:
        voice *= 0.95 / pk
    np.save(os.path.join(CACHE, 'voice.npy'), voice.astype(np.float32))
    with wave.open(os.path.join(CACHE, 'voice.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(FS)
        w.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(info, open(os.path.join(CACHE, 'voice_lines.json'), 'w'), indent=1)
    for i in info:
        print(i['text'], i['start'], i['end'], i['rms_dbfs'])


if __name__ == '__main__':
    main()
