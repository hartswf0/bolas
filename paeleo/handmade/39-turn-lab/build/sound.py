"""SCION 39 · Turn Lab — the sound, all synthesized here (numpy). python3 build/sound.py
Room tone (dusk crickets, air), the person's voice (a small formant synthesizer: glottal pulses through three resonators,
consonants as shaped noise), the dog's footfalls (from the controller's own foot landings in build/cache/plan.json), the door,
the person sitting, the dog lying down and sighing, and a low warm tone when the door opens. Writes build/cache/sound.wav
(38 s, 48 kHz stereo) and proof/sound_levels.json (measured RMS of each spoken line and of the room tone)."""
import json, math, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
SR = 48000
TITLE, SCENE, END = 3.0, 32.0, 3.0
N = int(SR * (TITLE + SCENE + END))
rng = np.random.default_rng(39)
mix = np.zeros(N)
pan = np.zeros(N)  # not used for panning per event; we build L/R separately
L = np.zeros(N); R = np.zeros(N)


def at(t):  # scene time → sample index
    return int((TITLE + t) * SR)


def add(sig, t, gain=1.0, p=0.0):  # p: -1 left … 1 right
    i = at(t); j = min(N, i + len(sig)); s = sig[:j - i] * gain
    L[i:j] += s * math.sqrt((1 - p) / 2); R[i:j] += s * math.sqrt((1 + p) / 2)


def biquad_bp(x, f, q):
    """time-varying band-pass (RBJ, constant peak gain); f may be an array per sample"""
    y = np.zeros_like(x); f = np.broadcast_to(f, x.shape)
    x1 = x2 = y1 = y2 = 0.0
    for n in range(len(x)):
        w = 2 * math.pi * f[n] / SR; al = math.sin(w) / (2 * q); a0 = 1 + al
        b0 = al / a0; b2 = -al / a0; a1 = -2 * math.cos(w) / a0; a2 = (1 - al) / a0
        yn = b0 * x[n] + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, x[n]; y2, y1 = y1, yn; y[n] = yn
    return y


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for n in range(len(x)):
        s = (1 - a) * x[n] + a * s; y[n] = s
    return y


def hp(x, fc):
    return x - onepole_lp(x, fc)


# ---------------------------------------------------------------- the voice
# phoneme: (kind, dur s, formants start, formants end, amp)
V = {
    'uh': (640, 1190, 2390), 'ih': (400, 1900, 2550), 'ear': (480, 1550, 2450), 'aw': (570, 840, 2410), 'ai0': (730, 1090, 2440),
    'ai1': (420, 1900, 2550), 'l': (360, 1000, 2400), 'r': (420, 1300, 1650), 'm': (280, 1250, 2300), 'n': (280, 1650, 2500),
}


def voice(phones, f0s, breath=0.15, gain=1.0):
    """phones: list of (kind, dur, a, b, amp). kind 'v' voiced (formants a→b), 'f' fricative noise (band a), 'b' burst, 'h' aspiration"""
    total = sum(p[1] for p in phones); n = int(total * SR)
    t = np.arange(n) / SR
    f0 = np.interp(t, np.linspace(0, total, len(f0s)), f0s)
    ph = np.cumsum(f0 / SR)
    saw = 2 * (ph % 1.0) - 1.0
    glott = onepole_lp(saw, 900) * 3.0 + rng.normal(0, 1, n) * breath
    F = [np.zeros(n) for _ in range(3)]; voiced = np.zeros(n); noise_amp = np.zeros(n); noise_f = np.full(n, 3000.0)
    k = 0
    for kind, dur, a, b, amp in phones:
        m = int(dur * SR); sl = slice(k, k + m); u = np.linspace(0, 1, m)
        env = np.minimum(1, np.minimum(u / 0.12, (1 - u) / 0.18 + 0.15))
        if kind == 'v':
            for j in range(3): F[j][sl] = a[j] + (b[j] - a[j]) * u
            voiced[sl] = amp * env
        else:
            for j in range(3): F[j][sl] = (b or a)[j] if isinstance(a, tuple) else 1500 * (j + 1)
            if kind == 'f': noise_amp[sl] = amp * np.sin(np.pi * u); noise_f[sl] = a if not isinstance(a, tuple) else 4500
            if kind == 'b': noise_amp[sl] = amp * np.exp(-u * 6); noise_f[sl] = 2200
            if kind == 'h': noise_amp[sl] = amp * np.sin(np.pi * u) * 0.8
        k += m
    for j in range(3):  # fill silent gaps of formant tracks
        F[j][F[j] == 0] = [500, 1500, 2500][j]
    src = glott * voiced
    out = biquad_bp(src, F[0], 6) * 1.0 + biquad_bp(src, F[1], 8) * 0.55 + biquad_bp(src, F[2], 10) * 0.25
    nz = rng.normal(0, 1, n) * noise_amp
    out += biquad_bp(nz, noise_f, 2.0) * 0.6
    asp = biquad_bp(rng.normal(0, 1, n) * (noise_amp > 0) * 0.3, F[1], 4) * 0.3
    out += asp
    out = hp(out, 90)
    return out / (np.max(np.abs(out)) + 1e-9) * gain


def come_here(loud):
    hi = 1.25 if loud else 1.0
    ph = [('b', 0.035, None, V['uh'], 0.9), ('v', 0.17, V['uh'], V['uh'], 1.0), ('v', 0.09, V['m'], V['m'], 0.45),
          ('h', 0.07, None, V['ih'], 0.8), ('v', 0.36, V['ih'], V['ear'], 1.0), ('v', 0.05, V['ear'], V['ear'], 0.0)]
    f0 = [200 * hi, 215 * hi, 205 * hi, 245 * hi, 270 * hi, 230 * hi, 185 * hi]
    return voice(ph, f0, breath=0.08, gain=1.0)


def its_all_right():
    ph = [('v', 0.08, V['ih'], V['ih'], 0.7), ('b', 0.02, None, V['ih'], 0.5), ('f', 0.10, 5200, None, 0.7),
          ('v', 0.22, V['aw'], V['aw'], 1.0), ('v', 0.08, V['l'], V['l'], 0.7), ('v', 0.07, V['r'], V['r'], 0.6),
          ('v', 0.30, V['ai0'], V['ai1'], 1.0), ('b', 0.04, None, V['ai1'], 0.3), ('v', 0.06, V['ai1'], V['ai1'], 0.0)]
    return voice(ph, [168, 172, 165, 160, 158, 150, 140], breath=0.45, gain=1.0)


def come_in():
    ph = [('b', 0.03, None, V['uh'], 0.6), ('v', 0.16, V['uh'], V['uh'], 1.0), ('v', 0.07, V['m'], V['m'], 0.5),
          ('v', 0.22, V['ih'], V['ih'], 1.0), ('v', 0.13, V['n'], V['n'], 0.5), ('v', 0.05, V['n'], V['n'], 0.0)]
    return voice(ph, [165, 168, 160, 172, 150, 140], breath=0.45, gain=1.0)


LINES = []
def speak(sig, t, db, name):
    g = 10 ** (db / 20); add(sig, t, g, -0.55); LINES.append((name, t, len(sig) / SR, g))

speak(come_here(False), 1.02, -7, 'come here (call)')
speak(come_here(True), 3.40, -4, 'come here (call again)')
speak(its_all_right(), 7.42, -20, "it's all right (soft)")
speak(its_all_right(), 10.42, -21, "it's all right (soft)")
speak(come_in(), 26.42, -21, 'come in (soft)')

# ---------------------------------------------------------------- room tone: crickets and air
def room_tone():
    n = N; t = np.arange(n) / SR
    air = onepole_lp(rng.normal(0, 1, n), 400) * 0.6
    air *= 0.8 + 0.2 * np.sin(2 * np.pi * t / 7.3)
    cr = np.zeros(n)
    for c in range(3):
        f = 4300 + 350 * c; rate = 2.1 + 0.37 * c; ph0 = rng.uniform(0, 1)
        gate = ((t * rate + ph0) % 1.0) < 0.16
        trill = (np.sin(2 * np.pi * 55 * t) > 0) * gate
        cr += np.sin(2 * np.pi * f * t) * onepole_lp(trill.astype(float), 300) * (0.5 - 0.1 * c)
    return air * 0.02 + cr * 0.010

tone = room_tone()
L += tone * 0.9; R += tone * 1.1

# ---------------------------------------------------------------- foley
def pad(gain=1.0, bright=900):
    n = int(0.06 * SR); u = np.arange(n) / SR
    s = onepole_lp(rng.normal(0, 1, n), bright) * np.exp(-u * 70) + np.sin(2 * np.pi * 140 * u) * np.exp(-u * 90) * 0.4
    return s * gain

plan = json.load(open(os.path.join(HERE, 'cache/plan.json')))
prev = None; steps = 0
for f in plan:
    d = f['dog']
    if prev is not None:
        for leg in ('hf', 'ff', 'hn', 'fn'):
            if prev['lift'][leg] > 0.08 and d['lift'][leg] <= 0.08:
                p = max(-1, min(1, (d['u'] * 225 + 290 - 640) / 640))
                add(pad(0.12 + 0.05 * rng.random()), f['t'], 1.0, p); steps += 1
    prev = d

def creak(dur, f0, f1, gain):
    n = int(dur * SR); u = np.linspace(0, 1, n)
    f = f0 + (f1 - f0) * u + 25 * np.sin(2 * np.pi * 3 * u)
    ph = np.cumsum(f / SR); s = np.sign(np.sin(2 * np.pi * ph)) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * u) ** 2)
    s = biquad_bp(s, np.full(n, 1200.0), 3) * np.sin(np.pi * u) ** 0.6
    return s * gain

def thump(gain, f=70):
    n = int(0.25 * SR); u = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * u) * np.exp(-u * 18) + onepole_lp(rng.normal(0, 1, n), 300) * np.exp(-u * 25) * 0.6) * gain

def breath_sigh(dur, gain):
    n = int(dur * SR); u = np.linspace(0, 1, n)
    s = biquad_bp(rng.normal(0, 1, n), np.linspace(900, 600, n), 1.5) * np.sin(np.pi * u) ** 1.5 * (1 - 0.5 * u)
    return s * gain

def rustle(dur, gain):
    n = int(dur * SR); u = np.linspace(0, 1, n)
    s = biquad_bp(rng.normal(0, 1, n), np.full(n, 2500.0), 0.8) * (0.4 + 0.6 * np.abs(np.sin(np.pi * 5 * u))) * np.sin(np.pi * u)
    return s * gain

add(rustle(0.4, 0.05), 3.38, 1.0, -0.6)                # the reach
add(rustle(0.5, 0.05), 5.0, 1.0, -0.8)                 # stepping aside
for k, t0 in enumerate([5.08, 5.30]): add(pad(0.25, 600), t0, 1.0, -0.8)
add(creak(0.5, 160, 120, 0.06), 5.62, 1.0, -0.8)       # porch board as the person sits
add(thump(0.10, 60), 5.98, 1.0, -0.8)
add(pad(0.25, 3000) * 0.6, 6.14, 1.0, -0.5)            # the latch
add(creak(0.65, 380, 260, 0.08), 6.18, 1.0, -0.45)     # the door swinging in
add(thump(0.10), 4.75, 1.0, 0.7); add(breath_sigh(0.9, 0.05), 6.05, 1.0, 0.7)     # refusal: lies down, sighs
add(thump(0.09), 24.30, 1.0, -0.25); add(breath_sigh(1.1, 0.06), 29.25, 1.0, -0.25)  # at the sill: lies down, sighs
add(rustle(0.3, 0.025), 7.5, 1.0, 0.7)                 # the dog lifts its head, collar
# the open door has a sound: a low warm room tone that comes out with the light
t = np.arange(N) / SR
warm = (np.sin(2 * np.pi * 110 * t) * 0.5 + np.sin(2 * np.pi * 164.8 * t) * 0.3 + np.sin(2 * np.pi * 220 * t) * 0.15)
warm = onepole_lp(warm, 600)
env = np.clip((t - (TITLE + 6.2)) / 1.5, 0, 1) * (1 - np.clip((t - (TITLE + SCENE + 1.0)) / 2.0, 0, 1))
env *= 1 + 0.25 * np.clip((t - (TITLE + 23.8)) / 2, 0, 1)
L += warm * env * 0.012; R += warm * env * 0.010
# a single soft note under the title and under the end card
for t0, f in ((0.3, 220.0), (TITLE + SCENE + 0.2, 164.8)):
    n = int(2.4 * SR); u = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * u) + 0.3 * np.sin(2 * np.pi * 2 * f * u)) * np.exp(-u * 1.4) * 0.05
    i = int(t0 * SR); L[i:i + n] += s; R[i:i + n] += s
# fade the room in/out at the cards
fade = np.clip((t - 2.0) / 1.0, 0, 1) * (1 - np.clip((t - (TITLE + SCENE + 1.5)) / 1.5, 0, 1)) * 0.85 + 0.15
L *= fade; R *= fade

st = np.stack([L, R], 1)
peak = np.max(np.abs(st))
if peak > 0.97: st *= 0.97 / peak
pcm = (st * 32767).astype('<i2')
with wave.open(os.path.join(HERE, 'cache/sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# measured levels: RMS of each line (voice only, over its own duration), and of the room tone in the scene
def dbfs(x): return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)
lev = {'room_tone_dbfs': round(dbfs(tone[at(0):at(32)] * fade[at(0):at(32)]), 1), 'lines': [], 'footfalls': steps}
for name, t0, dur, g in LINES:
    sig = {'come here (call)': come_here, 'come here (call again)': come_here}.get(name)
    lev['lines'].append({'line': name, 't': t0, 'dur': round(dur, 2), 'gain_db': round(20 * math.log10(g), 1)})
mixmono = st.mean(1)
for e in lev['lines']:
    i, j = at(e['t']), at(e['t'] + e['dur'])
    e['mix_rms_dbfs'] = round(dbfs(mixmono[i:j]), 1)
calls = [e['mix_rms_dbfs'] for e in lev['lines'] if 'call' in e['line']]
soft = [e['mix_rms_dbfs'] for e in lev['lines'] if 'soft' in e['line']]
lev['soft_below_calls_db'] = round(min(calls) - max(soft), 1)
lev['soft_above_room_db'] = round(min(soft) - lev['room_tone_dbfs'], 1)
os.makedirs(os.path.join(FOLDER, 'proof'), exist_ok=True)
json.dump(lev, open(os.path.join(FOLDER, 'proof/sound_levels.json'), 'w'), indent=1)
print(json.dumps(lev, indent=1))
