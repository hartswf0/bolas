"""SCION 16 JibJab: the sound, synthesized here from the performance's timecoded events (no recordings are used).
Voice: a three-formant source-filter synthesizer (glottal pulses + breath noise through resonators), phoneme targets typed
below. The calls are loud and bright; the soft lines are breathy and at least 6 dB quieter. Paws from the stepping solver's
contacts, the collar tag on the dog's turns, the door, the room that opens. Writes build/cache/sound.wav (38 s, 48 kHz)
and sound-levels.json (measured)."""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERF = json.load(open(os.path.join(HERE, 'performance.json')))
SR = 48000; T = 38.0; OFF = 3.0          # the scene starts after the 3 s title
n = int(SR * T)
rng = np.random.default_rng(16)
mix = np.zeros((2, n))


def db(x): return 20 * math.log10(max(x, 1e-12))


def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int((t0) * SR)
    if i0 >= n: return
    s = sig[: max(0, n - i0)]
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    mix[0, i0:i0 + len(s)] += s * gain * l * 1.414
    mix[1, i0:i0 + len(s)] += s * gain * r * 1.414


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); z = 0.0
    for i in range(len(x)): z = (1 - a) * x[i] + a * z; y[i] = z
    return y


def lp_fast(x, fc, passes=2):
    # cheap low pass via moving average (for long beds)
    k = max(1, int(SR / fc / 2))
    y = x
    for _ in range(passes): y = np.convolve(y, np.ones(k) / k, mode='same')
    return y


def resonator(x, f, bw):
    """time-varying 2-pole resonator; f and bw arrays per sample"""
    y = np.zeros_like(x); y1 = y2 = 0.0
    for i in range(len(x)):
        r = math.exp(-math.pi * bw[i] / SR); c = 2 * r * math.cos(2 * math.pi * f[i] / SR)
        g = (1 - r) * math.sqrt(1 + r * r - 2 * r * math.cos(4 * math.pi * f[i] / SR))
        yy = g * x[i] + c * y1 - r * r * y2
        y2, y1 = y1, yy; y[i] = yy
    return y


# phoneme targets: (F1, F2, F3, voiced amp, noise amp, noise centre)
PH = {
    'k': (300, 1800, 2500, 0.0, 0.9, 2500), 'A': (640, 1190, 2390, 1.0, 0.02, 0), 'm': (260, 1150, 2200, 0.35, 0.0, 0),
    'h': (500, 1500, 2500, 0.05, 0.6, 1600), 'I': (400, 1920, 2560, 0.9, 0.02, 0), 'r': (420, 1150, 1650, 0.8, 0.02, 0),
    'e': (520, 1400, 1800, 0.95, 0.02, 0), 't': (300, 1700, 2600, 0.0, 0.8, 4000), 's': (300, 1700, 2600, 0.0, 0.7, 6500),
    'o': (570, 860, 2410, 1.0, 0.02, 0), 'l': (360, 1000, 2400, 0.7, 0.0, 0), 'a': (740, 1100, 2440, 1.0, 0.02, 0),
    'n': (280, 1500, 2500, 0.4, 0.0, 0), '_': (400, 1500, 2500, 0.0, 0.0, 0),
}
LINES = {
    'Come here.': [('k', .05), ('A', .17), ('m', .09), ('h', .07), ('I', .12), ('e', .10), ('r', .20)],
    'It’s all right.': [('I', .09), ('_', .04), ('t', .03), ('s', .09), ('o', .15), ('l', .08), ('r', .06), ('a', .14), ('I', .10), ('_', .05), ('t', .04)],
    'Come in.': [('k', .05), ('A', .16), ('m', .10), ('I', .16), ('n', .22)],
}


def speak(text, f0a, f0b, breath, loud):
    seq = LINES[text]
    dur = sum(d for _, d in seq); N = int(dur * SR)
    tt = np.arange(N) / SR
    # per-sample targets with 25 ms glides
    keys = []; t = 0
    for p, d in seq: keys.append((t, PH[p])); t += d
    keys.append((t, PH[seq[-1][0]]))
    arr = np.zeros((N, 6))
    for j in range(6):
        xs = [k[0] for k in keys]; ys = [k[1][j] for k in keys]
        # step-wise then smoothed
        st = np.interp(tt, xs, ys)
        idx = np.searchsorted(xs, tt, side='right') - 1
        stp = np.array([ys[min(k, len(ys) - 1)] for k in idx])
        arr[:, j] = lp_fast(stp, 40, 1)
    # pitch contour: rise then fall (a call) or a gentle fall (soft)
    u = tt / dur
    f0 = f0a + (f0b - f0a) * u + (loud * 60) * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) + 3 * np.sin(2 * np.pi * 5.5 * tt)
    ph = np.cumsum(f0 / SR)
    glott = (ph % 1.0); glott = (glott < 0.6) * np.sin(np.pi * glott / 0.6) ** 2 - 0.35
    glott = np.diff(np.concatenate([[0], glott]))   # differentiated glottal flow
    noise = rng.standard_normal(N)
    src = glott * arr[:, 3] * (1 - breath) * 6 + noise * (arr[:, 3] * breath * 0.25)
    y = 0
    for j, bw in ((0, 80), (1, 110), (2, 160)):
        y = y + resonator(src, arr[:, j], np.full(N, bw * (1.6 if breath > .3 else 1))) * (1.0, 0.6, 0.35)[j]
    # fricatives / bursts
    fn = noise * arr[:, 4]
    fr = resonator(fn, np.where(arr[:, 5] > 0, arr[:, 5], 3000), np.full(N, 1500.0)) * 0.6
    y = y + fr
    env = np.minimum(1, np.minimum(tt / 0.02, (dur - tt) / 0.06))
    y = y * env
    return y / (np.max(np.abs(y)) + 1e-9)


def pluck(f, dur=1.6, bright=0.5):
    N = int(dur * SR); tt = np.arange(N) / SR
    s = sum((bright ** k) * np.sin(2 * np.pi * f * (k + 1) * tt) * np.exp(-tt * (3 + 2 * k)) for k in range(5))
    return s * np.minimum(1, tt / 0.004)


def click(dur=0.06, f=180, tone=0.6):
    N = int(dur * SR); tt = np.arange(N) / SR
    nz = rng.standard_normal(N) * np.exp(-tt / 0.004)
    nz = np.diff(np.concatenate([[0], nz]))
    k = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.018) * tone
    return nz * 0.5 + k


def jingle(dur=0.45):
    N = int(dur * SR); tt = np.arange(N) / SR; y = np.zeros(N)
    for s in sorted(rng.uniform(0, dur * 0.6, 5)):
        i = int(s * SR); m = N - i; t2 = tt[:m]
        for f in (3150, 4720, 6230, 8100):
            y[i:] += np.sin(2 * np.pi * f * (1 + rng.uniform(-.01, .01)) * t2) * np.exp(-t2 * rng.uniform(18, 30)) * rng.uniform(.2, .5)
    return y


def thump(dur=0.35):
    N = int(dur * SR); tt = np.arange(N) / SR
    return np.sin(2 * np.pi * 62 * tt * (1 - 0.3 * tt)) * np.exp(-tt / 0.07) + lp_fast(rng.standard_normal(N), 600) * np.exp(-tt / 0.05) * 2


def breath_sig(dur=1.0):
    N = int(dur * SR); tt = np.arange(N) / SR
    nz = rng.standard_normal(N); b = resonator(nz, np.full(N, 900.0), np.full(N, 700.0))
    return b * np.sin(np.pi * tt / dur) ** 1.5


def creak(dur=0.9, f0=95):
    N = int(dur * SR); tt = np.arange(N) / SR
    f = f0 + 25 * np.sin(2 * np.pi * 1.3 * tt) + 8 * rng.standard_normal(N).cumsum() / np.sqrt(np.arange(1, N + 1))
    ph = np.cumsum(f / SR); saw = (ph % 1) * 2 - 1
    y = resonator(saw, np.full(N, 1400.0), np.full(N, 300.0)) + resonator(saw, np.full(N, 2600.0), np.full(N, 500.0)) * 0.5
    return y * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.6


# ---------------------------------------------------------------- beds
tt = np.arange(n) / SR
pink = lp_fast(rng.standard_normal(n), 900, 2)
room = pink / np.std(pink) * 10 ** (-54 / 20)
fade_in = np.clip((tt - 0.5) / 2.0, 0, 1); fade_out = np.clip((T - 0.3 - tt) / 1.5, 0, 1)
bed = room * fade_in * fade_out
add(bed, 0, 1.0, -0.2); add(lp_fast(rng.standard_normal(n), 700, 2) / np.std(pink) * 10 ** (-54 / 20) * fade_in * fade_out, 0, 1.0, 0.3)
# crickets in the garden (right of frame): chirp trains, a little sparser as the evening goes on
t = 0.8
while t < T - 1.5:
    N = int(0.12 * SR); t2 = np.arange(N) / SR
    am = (np.sin(2 * np.pi * 30 * t2) > 0) * np.sin(np.pi * t2 / 0.12)
    ch = np.sin(2 * np.pi * 4600 * t2) * am
    add(ch, t, 10 ** (-41 / 20), 0.6)
    t += rng.uniform(0.45, 0.95)
# the room that opens: a warm low hum rising with the door
door_t = OFF + 6.2
N = n; hum = (np.sin(2 * np.pi * 110 * tt) * 0.5 + np.sin(2 * np.pi * 165 * tt) * 0.25 + lp_fast(rng.standard_normal(n), 300, 2) * 6)
env = np.clip((tt - door_t) / 1.2, 0, 1) * fade_out * 0.25 + np.clip((tt - OFF) / 1, 0, 1) * (tt < door_t) * 0.03
add(hum * env * 10 ** (-47 / 20), 0, 1.0, -0.5)

# ---------------------------------------------------------------- voices (the person, left of frame)
levels = {'calls': [], 'soft': []}
VO = []
for e in PERF['events']:
    if e['e'] != 'voice': continue
    ts = e['t']
    if e['kind'] == 'call':
        sig = speak('Come here.', 205, 175, 0.05, 1.0); g = 10 ** (-2 / 20); key = 'calls'
    else:
        txt = 'Come in.' if ts > 25 else 'It’s all right.'
        sig = speak(txt, 178, 140, 0.42, 0.25); g = 10 ** (-14 / 20); key = 'soft'
    add(sig, OFF + ts + 0.05, g, -0.45)
    levels[key].append({'t': ts, 'rms_db': round(db(np.sqrt(np.mean((sig * g) ** 2))), 2), 'peak_db': round(db(np.max(np.abs(sig * g))), 2)})
# ---------------------------------------------------------------- the dog
for e in PERF['events']:
    ts = OFF + e['t']; x = e.get('x', 3)
    pan = float(np.clip((x - 2) / 3, -0.8, 0.8))
    if e['e'] == 'paw': add(click(), ts, 10 ** (-33 / 20) * rng.uniform(0.7, 1.0), pan)
    elif e['e'] == 'jingle': add(jingle(), ts, 10 ** (-36 / 20), 0.4 if e['t'] < 20 else -0.2)
    elif e['e'] == 'thump': add(thump(), ts, 10 ** (-24 / 20), 0.4 if e['t'] < 20 else -0.2)
    elif e['e'] == 'sigh': add(breath_sig(0.9), ts, 10 ** (-34 / 20), 0.4 if e['t'] < 20 else -0.2)
    elif e['e'] == 'door':
        add(click(0.05, 900, 0.3), ts - 0.08, 10 ** (-26 / 20), -0.3); add(creak(0.95, 92), ts, 10 ** (-30 / 20), -0.3)
    elif e['e'] == 'creak': add(creak(0.4, 70), ts, 10 ** (-38 / 20), -0.6)
# ---------------------------------------------------------------- a few plucked notes for the earned moments
for ts, f, g in ((OFF + 14.72, 392, -30), (OFF + 15.1, 523.3, -32), (OFF + 24.05, 329.6, -30), (OFF + 24.25, 392, -31),
                 (OFF + 24.45, 493.9, -32), (OFF + 28.45, 261.6, -31), (OFF + 28.6, 329.6, -33)):
    add(pluck(f, 2.2, 0.35), ts, 10 ** (g / 20), 0.0)
# title sting and end card
add(pluck(196, 2.5, 0.4), 0.3, 10 ** (-30 / 20), 0); add(pluck(293.7, 2.5, 0.4), 0.6, 10 ** (-32 / 20), 0)

peak = np.max(np.abs(mix))
if peak > 0.89: mix *= 0.89 / peak
pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2').T.copy()
os.makedirs(os.path.join(HERE, 'build/cache'), exist_ok=True)
w = wave.open(os.path.join(HERE, 'build/cache/sound.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(pcm.tobytes()); w.close()


# measured from the mix itself: speech windows vs the bed
def win_rms(t0, t1):
    a, b = int(t0 * SR), int(t1 * SR); seg = mix[:, a:b]
    return db(np.sqrt(np.mean(seg ** 2)))


meas = {'calls_window_rms_db': [], 'soft_window_rms_db': [], 'bed_window_rms_db': None}
for e in PERF['events']:
    if e['e'] != 'voice': continue
    k = 'calls_window_rms_db' if e['kind'] == 'call' else 'soft_window_rms_db'
    meas[k].append(round(win_rms(OFF + e['t'] + 0.1, OFF + e['t'] + 0.7), 2))
meas['bed_window_rms_db'] = round(win_rms(OFF + 12.0, OFF + 14.0), 2)
meas['call_minus_soft_db'] = round(min(meas['calls_window_rms_db']) - max(meas['soft_window_rms_db']), 2)
meas['soft_minus_bed_db'] = round(min(meas['soft_window_rms_db']) - meas['bed_window_rms_db'], 2)
meas['per_line_signal'] = levels
json.dump(meas, open(os.path.join(HERE, 'sound-levels.json'), 'w'), indent=1)
print('sound ok', meas['call_minus_soft_db'], meas['soft_minus_bed_db'])
