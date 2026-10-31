"""Five soundtracks for PINK EYE, through her eyes. Same picture, sound swapped; all synthesized, no samples.

Each is cued to the picture's changes: the desk at 7 s, her face at 13 s, the butterfly at 23 s, the swan at 27.5 s, her
second look at 31 s, the projector glow at 42 s, white at 47 s, the title at 50.5 s.

  1 lullaby      Ode to Joy on a celesta, very slow, close and intimate, in a soft room
  2 voices       a wordless three-part "ah" choir sings the tune, breathy and legato
  3 bloom        no tune: warm chords that change with each image, glass bells on every dissolve, a long shimmer
  4 dream-pop    a soft 84 bpm beat, warm bass, a pumping pad, the tune as a gentle synth lead from the butterfly on
  5 harp-cello   a plucked harp arpeggio, then a bowed cello carries the tune from the moment she appears

    python3 tools/pink_eye/her_eyes_sound.py PICTURE.mp4 OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np

SR, END = 48000, 56.0
N = int(END * SR); T = np.arange(N) / SR
EVENTS = [7.0, 13.0, 23.0, 27.5, 31.0, 42.0, 47.0, 50.5]
TUNE = [66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 66, 64, 64, 66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 64, 62, 62]
LENS = [1] * 12 + [1.5, 0.5, 2] + [1] * 12 + [1.5, 0.5, 2]
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def put(out, sig, at, g=1.0):
    a = int(at * SR); b = min(N, a + len(sig))
    if 0 <= a < N:
        out[a:b] += g * sig[:b - a]


def lowpass(x, cut):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / (1 + (f / cut) ** 4), len(x))


def reverb(x, secs, decay, wet, seed=1):
    L = int(secs * SR); ir = np.random.default_rng(seed).normal(0, 1, L) * np.exp(-np.arange(L) / SR * decay)
    ir = lowpass(ir, 5000); m = 1 << int(np.ceil(np.log2(len(x) + L)))
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
    return (1 - wet) * x + wet * y / max(1e-9, np.abs(y).max()) * np.abs(x).max()


def notes(beat, start):
    out, t = [], start
    for m, l in zip(TUNE, LENS):
        out.append((m, t, l * beat)); t += l * beat
    return out


def finish(x):
    x = x * np.minimum(1, T / 2.0) * np.clip((END - T) / 3.0, 0, 1)
    return x / max(1e-9, np.abs(x).max()) * 0.8


def tone(f, dur, partials, decay, attack=0.004):
    k = int(dur * SR); x = np.arange(k) / SR
    return sum(a * np.sin(2 * np.pi * f * r * x) for r, a in partials) * np.exp(-x * decay) * np.minimum(1, x / attack)


# 1 ---------------------------------------------------------------------------
def lullaby():
    out = np.zeros(N)
    for m, at, d in notes(1.0, 5.0):
        put(out, tone(hz(m + 12), 3.0, ((1, 1), (4.0, 0.18), (8.0, 0.05)), 2.0), at, 0.5)
    for i, (m, at, d) in enumerate(notes(1.0, 5.0)[:8]):           # an answering echo, an octave higher, near the end
        put(out, tone(hz(m + 24), 3.0, ((1, 1), (4.0, 0.12)), 2.4), 42.0 + i * 1.0, 0.18)
    out += 0.02 * lowpass(np.random.default_rng(1).normal(0, 1, N), 400)          # the room
    return finish(reverb(out, 3.5, 1.6, 0.45))


# 2 ---------------------------------------------------------------------------
def sing(f0, dur, gain, vowel=((800, 120), (1150, 140), (2900, 220))):
    k = int(dur * SR); x = np.arange(k) / SR
    f = f0 * (1 + 0.006 * np.sin(2 * np.pi * 5.4 * x) * np.minimum(1, x / 0.6))
    ph = 2 * np.pi * np.cumsum(f) / SR; s = np.zeros(k)
    for h in range(1, int(4000 / f0)):
        amp = sum(np.exp(-((h * f0 - F) / B) ** 2) for F, B in vowel) + 0.04
        s += amp / h ** 0.6 * np.sin(h * ph)
    breath = lowpass(np.random.default_rng(int(f0)).normal(0, 1, k), 2500) * 0.08
    env = np.minimum(1, x / 0.18) * np.minimum(1, (dur - x) / 0.4).clip(0)
    return gain * (s + breath) * env


def voices():
    out = np.zeros(N)
    deg = [62, 64, 66, 67, 69, 71, 73, 74]                               # D major, so a third below stays in key
    third = lambda m: deg[max(0, deg.index(m) - 2)] if m in deg else m - 4
    for m, at, d in notes(1.05, 6.0):
        put(out, sing(hz(m), d + 0.35, 0.5), at)
        put(out, sing(hz(third(m)), d + 0.35, 0.28, ((600, 120), (1000, 140), (2700, 200))), at)
    for at, root in ((6.0, 50), (23.0, 45), (31.0, 50), (42.0, 43)):         # a low hum under each section
        put(out, sing(hz(root), 9.5, 0.25, ((400, 100), (800, 120), (2600, 200))), at)
    return finish(reverb(out, 3.0, 1.8, 0.5))


# 3 ---------------------------------------------------------------------------
def bloom():
    out = np.zeros(N); rng = np.random.default_rng(7)
    chords = [[50, 57, 64, 66, 69], [47, 54, 61, 62, 66], [43, 50, 59, 62, 66], [45, 52, 59, 61, 64],
              [50, 57, 64, 66, 69], [47, 54, 62, 64, 66], [43, 55, 62, 66, 71], [50, 57, 66, 69, 76]]
    cues = [0.0] + EVENTS
    for i, ch in enumerate(chords):
        a, b = cues[i], cues[i + 1] if i + 1 < len(cues) else END
        w = np.clip(np.minimum((T - a + 2.5) / 2.5, (b + 2.5 - T) / 2.5), 0, 1)
        for m in ch:
            f = hz(m)
            out += 0.05 * w * np.sin(2 * np.pi * f * T + m)
            out += 0.012 * w * np.sin(2 * np.pi * 2 * f * T) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.05, 0.2) * T + m))  # shimmer
    for e in EVENTS:
        put(out, tone(hz(81), 4.0, ((1, 1), (2.76, 0.4), (5.4, 0.15)), 1.1), e, 0.25)
    for i, m in enumerate((78, 79, 81, 81)):                                 # one quiet fragment of the tune, at the glow
        put(out, tone(hz(m), 2.5, ((1, 1), (2.0, 0.2)), 1.6), 42.5 + i * 1.1, 0.18)
    return finish(reverb(out, 5.0, 1.0, 0.6))


# 4 ---------------------------------------------------------------------------
def dreampop():
    out = np.zeros(N); beat = 60 / 84; rng = np.random.default_rng(4)
    prog = [50, 45, 47, 43]                                                  # D A Bm G
    bars = np.arange(0, END, 4 * beat)
    pump = np.ones(N)
    for i, b in enumerate(bars):
        root = prog[i % 4]; third = 4 if i % 4 in (0, 1, 3) else 3
        for m in (root + 12, root + 12 + third, root + 19, root + 24):       # the pad, a soft saw
            k = int(4 * beat * SR); x = np.arange(k) / SR
            saw = sum(np.sin(2 * np.pi * hz(m) * h * x) / h for h in range(1, 7))
            put(out, lowpass(saw, 1800) * np.minimum(1, x / 0.3) * np.minimum(1, (4 * beat - x) / 0.3), b, 0.05)
        if 7.0 <= b < 47.0:
            k = int(4 * beat * SR); x = np.arange(k) / SR
            put(out, (np.sin(2 * np.pi * hz(root - 12) * x) + 0.3 * np.sin(4 * np.pi * hz(root - 12) * x)) * np.minimum(1, x / 0.02), b, 0.14)   # bass
    for i in range(int(END / beat)):
        at = i * beat
        if 7.0 <= at < 47.0 and i % 2 == 0:                                   # kick on 1 and 3, with the pad pumping under it
            k = int(0.3 * SR); x = np.arange(k) / SR
            put(out, np.sin(2 * np.pi * (45 + 60 * np.exp(-x * 25)) * x) * np.exp(-x * 9), at, 0.45)
            a = int(at * SR); pump[a:a + k] *= 1 - 0.45 * np.exp(-x * 8)
        if 13.0 <= at < 47.0 and i % 2 == 1:                                  # a soft clap on 2 and 4
            k = int(0.18 * SR); put(out, lowpass(rng.normal(0, 1, k), 3000) * np.exp(-np.arange(k) / SR * 28), at, 0.12)
        if 13.0 <= at < 47.0:                                                 # quiet hats on the eighths
            for h in (0, 0.5):
                k = int(0.05 * SR); put(out, (rng.normal(0, 1, k) - lowpass(rng.normal(0, 1, k), 6000)) * np.exp(-np.arange(k) / SR * 80), at + h * beat, 0.04)
    out *= pump
    for m, at, d in notes(beat, 23.0):                                       # the lead: the tune, gently
        if at > 46:
            break
        k = int((d + 0.1) * SR); x = np.arange(k) / SR
        sq = sum(np.sin(2 * np.pi * hz(m + 12) * h * x) / h for h in (1, 3, 5, 7))
        put(out, lowpass(sq, 2400) * np.minimum(1, x / 0.02) * np.minimum(1, (d + 0.1 - x) / 0.08), at, 0.12)
    return finish(reverb(out, 2.2, 2.5, 0.3))


# 5 ---------------------------------------------------------------------------
def pluck(f, dur, seed):
    """Karplus-Strong, processed a period at a time"""
    P = int(SR / f); k = int(dur * SR); y = np.zeros(k + P)
    y[:P] = np.random.default_rng(seed).uniform(-1, 1, P)
    for s in range(P, k + P, P):
        prev = y[s - P:s]; nxt = 0.5 * (prev + np.roll(prev, -1)) * 0.996
        y[s:s + P] = nxt[:len(y[s:s + P])]
    return y[P:] * np.minimum(1, np.arange(k) / 40)


def bow(f, dur):
    k = int(dur * SR); x = np.arange(k) / SR
    fr = f * (1 + 0.007 * np.sin(2 * np.pi * 5.0 * x) * np.minimum(1, x / 0.5))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    s = sum(np.sin(h * ph) / h ** 1.2 for h in range(1, 14))
    s += 0.05 * lowpass(np.random.default_rng(int(f)).normal(0, 1, k), 1500)     # bow noise
    return lowpass(s, 2200) * np.minimum(1, x / 0.25) * np.clip(np.minimum(1, (dur - x) / 0.3), 0, 1)


def harpcello():
    out = np.zeros(N); beat = 0.9
    chords = [[50, 57, 62, 66], [45, 57, 61, 64], [50, 57, 62, 66], [43, 55, 59, 62]]
    i = 0; at = 0.5
    while at < 52.0:                                                          # the harp: rolling arpeggios, all film long
        ch = chords[(i // 8) % 4]; m = ch[i % 4] + (12 if (i // 4) % 2 else 0)
        put(out, pluck(hz(m + 12), 2.5, i), at, 0.22); at += beat / 2; i += 1
    for m, a0, d in notes(beat, 7.5):                                        # the cello, from the moment she appears
        if a0 > 42.5:
            break
        put(out, bow(hz(m - 12), d + 0.2), a0, 0.35)
    for m in (38, 50, 57, 62, 66):                                            # a last chord under the title
        put(out, pluck(hz(m + 12), 5.0, m), 50.5, 0.25)
    return finish(reverb(out, 2.8, 1.9, 0.4))


def main(picture, od):
    os.makedirs(od, exist_ok=True)
    silent = os.path.join(od, "picture-only.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-an", "-c:v", "copy", silent], check=True)
    for name, fn in (("1-lullaby", lullaby), ("2-voices", voices), ("3-bloom", bloom), ("4-dream-pop", dreampop), ("5-harp-cello", harpcello)):
        wav = os.path.join(od, f"{name}.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((fn() * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", "-shortest", os.path.join(od, f"pink-eye-sound-{name}.mp4")], check=True)
        print(name)


if __name__ == "__main__":
    main(*sys.argv[1:3])
