"""SCION 41 sound: every sound is synthesized here from the simulation (no recordings).
python3 build/sound.py [sim.json] [out.wav]

- voice: a formant synthesizer (glottal pulse train -> three resonators), driven by the same syllable script the
  person's mouth uses (sim.voice). Calls are loud and bright; the soft voice is breathy and >= 6 dB quieter.
- foley from the solver's own events: paw touchdowns (claws + pads on boards), the collar tag hitting the chest,
  the tail on the floor, the body lying down, the door's creak (from its angular velocity) and its knock on the stop,
  the shrub's rustle (from the shrub's secondary energy). Room tone: crickets and air, under everything.
Writes the wav and a levels report (RMS of calls, soft voice, room tone) next to it."""
import json, sys, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cache/sim.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'cache/sound.wav')
SR = 44100; T0 = 3.0; DUR = 38.0; NS = int(SR * DUR)
rng = np.random.default_rng(41)
S = json.load(open(SIM))
L = np.zeros(NS); R = np.zeros(NS)
tracks = {k: np.zeros(NS) for k in ('voice_call', 'voice_soft', 'room', 'foley')}


def place(sig, t, pan=0.0, track='foley'):
    i = int((T0 + t) * SR) if track != 'card' else int(t * SR)
    if i >= NS or i + len(sig) <= 0: return
    a, b = max(0, i), min(NS, i + len(sig)); s = sig[a - i:b - i]
    gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    L[a:b] += s * gl * 1.414; R[a:b] += s * gr * 1.414
    if track in tracks: tracks[track][a:b] += s


def biquad_bp(x, f, q):  # constant-skirt band-pass, direct form, python loop (short signals only)
    w = 2 * math.pi * f / SR; al = math.sin(w) / (2 * q); b0, b2 = al, -al; a0, a1, a2 = 1 + al, -2 * math.cos(w), 1 - al
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for n in range(len(x)):
        v = (b0 * x[n] + b2 * x2 - a1 * y1 - a2 * y2) / a0; x2, x1 = x1, x[n]; y2, y1 = y1, v; y[n] = v
    return y


def fft_filter(x, lo, hi, tilt=0.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); m = ((f >= lo) & (f <= hi)).astype(float)
    if tilt: m *= (np.maximum(f, 20) / 1000.0) ** tilt
    return np.fft.irfft(X * m, len(x))


def env(n, a, d):  # attack/decay envelope in seconds
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4))


def pan_of(x):
    return float(np.clip((x - 1.8) / 3.2, -0.8, 0.8))


# ---------------- voice ----------------
VOW = {'ah': (720, 1240, 2600), 'ih': (400, 1950, 2600), 'aw': (590, 880, 2450), 'ay': (760, 1320, 2500), 'uh': (520, 1400, 2500)}
GLIDE = {('h', 'ih'): ('uh', 0.55), ('r', 'ay'): ('ih', 0.6)}


def resonate(src, F, BW):  # time-varying formant resonators; F, BW arrays per sample (n x 3)
    out = np.zeros_like(src)
    for k in range(3):
        y1 = y2 = 0.0; y = np.zeros_like(src)
        for n in range(len(src)):
            r = math.exp(-math.pi * BW[k] / SR); c = 2 * r * math.cos(2 * math.pi * F[n, k] / SR)
            v = src[n] + c * y1 - r * r * y2; y2, y1 = y1, v; y[n] = v
        out += y * (1 - r) * (1.0, 0.55, 0.3)[k]
    return out


def syllable(cons, vowel, dur, amp, level, f0a, f0b, coda=''):
    soft = level == 'soft'; n = int(dur * SR); t = np.arange(n) / SR
    f0 = f0a + (f0b - f0a) * (t / dur) ** 1.3 + 2.5 * np.sin(2 * math.pi * 5.2 * t)
    ph = np.cumsum(f0 / SR); frac = ph % 1.0
    oq = 0.75 if soft else 0.5  # open quotient: breathy soft voice, pressed loud call
    glot = np.where(frac < oq, np.sin(math.pi * frac / oq) ** 2, 0.0); glot = np.diff(glot, prepend=0) * 40
    breath = rng.standard_normal(n) * (0.45 if soft else 0.08); src = glot + fft_filter(breath, 300, 7000)
    v0 = np.array(VOW[vowel], float); g = GLIDE.get((cons, vowel)); v1 = np.array(VOW[g[0]], float) if g else v0
    u = np.clip((t / dur - (g[1] if g else 1)) / 0.35, 0, 1)[:, None]; F = v0 * (1 - u) + v1 * u
    if not soft: F[:, 0] *= 1.08  # a raised, carrying voice opens the jaw
    y = resonate(src, F, (90, 120, 180) if not soft else (130, 170, 260))
    e = np.minimum(1, t / 0.035) * np.minimum(1, (dur - t) / (0.09 if not soft else 0.14)); y *= e
    pre = np.zeros(0)
    if cons == 'k': nb = int(0.04 * SR); pre = fft_filter(rng.standard_normal(nb), 1400, 4200) * env(nb, 0.002, 0.012) * (0.9 if not soft else 0.35)
    if cons == 'h': nb = int(0.07 * SR); pre = fft_filter(rng.standard_normal(nb), 500, 4000) * np.hanning(nb) * (0.35 if not soft else 0.18)
    if cons == 'r': nb = int(0.05 * SR); pre = resonate(glot[:nb] * np.hanning(nb), np.tile([450, 1100, 1700], (nb, 1)), (90, 120, 180)) * 0.6
    post = np.zeros(0)
    if coda in ('m', 'n'): nb = int(0.09 * SR); tt = np.arange(nb) / SR; post = np.sin(2 * math.pi * np.cumsum(np.full(nb, f0b)) / SR) * np.exp(-tt / 0.05) * 0.25 * (1 if coda == 'm' else 0.8)
    if coda == 'ts': nb = int(0.07 * SR); post = fft_filter(rng.standard_normal(nb), 4000, 9000) * env(nb, 0.01, 0.03) * (0.3 if not soft else 0.16)
    if coda == 't': nb = int(0.03 * SR); post = fft_filter(rng.standard_normal(nb), 2500, 7000) * env(nb, 0.002, 0.01) * 0.25
    out = np.concatenate([pre, y / (np.abs(y).max() + 1e-9) * amp, post])
    return out


CODA = {"Come here!": ['m', ''], "come on!": ['m', 'n'], "Come HERE!": ['m', ''], "it's all right": ['ts', '', 't'], "come in": ['m', 'n']}
voice_spans = {'call': [], 'soft': []}
for v in S['voice']:
    t = v['t']; level = v['level']; start = t; n_s = len(v['syl'])
    for k, (c, vw, d, amp) in enumerate(v['syl']):
        last = k == n_s - 1
        if level == 'call': f0a, f0b = (215, 205) if not last else (250, 300 if 'HERE' in v['text'] else 270)
        else: f0a, f0b = (190, 182) if not last else (185, 160)
        sig = syllable(c, vw, d, amp * (0.92 if level == 'call' else 0.30), level, f0a, f0b, CODA.get(v['text'], [''] * 3)[k])
        place(sig, t + 0.03, -0.55, 'voice_call' if level == 'call' else 'voice_soft'); t += d + 0.04
    voice_spans[level].append((start, t + 0.1))

# ---------------- foley from the solver's events ----------------
last = {}
def debounce(tag, t, gap):
    if t - last.get(tag, -9) < gap: return False
    last[tag] = t; return True


def mx(*sigs):
    n = max(len(x) for x in sigs); o = np.zeros(n)
    for x in sigs: o[:len(x)] += x
    return o


def click(amp, bright=1.0):
    n = int(0.012 * SR); return fft_filter(rng.standard_normal(n), 2500 * bright, 8000) * env(n, 0.0005, 0.003) * amp


def thump(f, amp, d=0.05):
    n = int(d * 4 * SR); t = np.arange(n) / SR; return np.sin(2 * math.pi * f * t * (1 - 0.3 * t / (d * 4))) * np.exp(-t / d) * amp


def jingle(amp):
    n = int(0.35 * SR); t = np.arange(n) / SR; parts = [(2380, 0.12), (3890, 0.09), (5710, 0.06), (7330, 0.04)]
    return sum(np.sin(2 * math.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) for f, d in parts) * amp * 0.35


for e in S['events']:
    t, tag, sp = e['t'], e['tag'], e.get('speed', 0.3); x = e.get('x', 1.0)
    if tag == 'paw':
        a = min(1.0, 0.25 + 0.5 * sp); place(mx(click(0.05 * a), thump(140, 0.035 * a, 0.02)), t, pan_of(x))
    elif tag == 'tag' and sp > 0.25 and debounce('tag', t, 0.07):
        place(jingle(min(0.05, 0.02 + 0.03 * sp)), t, pan_of(x))
    elif tag == 'tail-floor' and debounce('tail', t, 0.12):
        place(mx(thump(95, min(0.05, 0.02 + 0.05 * sp), 0.03), fft_filter(rng.standard_normal(int(0.06 * SR)), 300, 2500) * np.hanning(int(0.06 * SR)) * 0.01), t, 0.1)
    elif tag == 'lie':
        n = int(0.9 * SR); tt = np.arange(n) / SR
        sigh = fft_filter(rng.standard_normal(n), 250, 2200) * np.sin(math.pi * np.clip(tt / 0.85, 0, 1)) ** 2 * 0.03
        place(thump(80, 0.06, 0.06), t - 0.05, pan_of(x)); place(sigh, t + 0.25, pan_of(x))
    elif tag == 'rise':
        for k in range(4): place(click(0.035, 0.8), t + k * 0.06 + rng.uniform(0, 0.02), pan_of(4.0))
    elif tag == 'door-stop':
        place(mx(thump(170, 0.10, 0.05), thump(410, 0.05, 0.03), click(0.05, 0.6)), t, -0.65)

# door creak: stick-slip pulses at a rate set by the hinge's angular velocity
door = np.array([f['door'] for f in S['frames']]); w = np.gradient(door) * 24; n = len(door)
tt = np.arange(int(n / 24 * SR)) / SR; wv = np.interp(tt, np.arange(n) / 24, np.abs(w)); rate = 60 + 260 * wv
ph = np.cumsum(rate / SR); pulse = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * np.clip(wv / 0.5, 0, 1)
cre = biquad_bp(pulse[: int(7.0 * SR)], 760, 6) + 0.6 * biquad_bp(pulse[: int(7.0 * SR)], 1480, 8)
place(cre * 0.16, 0.0, -0.65)
# shrub rustle: band noise whose level follows the shrub's secondary energy
E = np.array([e['shrub'] for e in S['energy']]); lev = np.sqrt(np.clip(E, 0, None)); lev = np.clip(lev / 0.25, 0, 1)
lv = np.interp(tt, np.arange(n) / 24, lev); rus = fft_filter(rng.standard_normal(len(tt)), 1800, 9000, tilt=-0.5) * lv * 0.06
place(rus, 0.0, 0.75)
# the person: steps on the floor when stepping aside, the settle when sitting
for ts in (4.9, 5.16, 5.42, 5.62): place(mx(thump(110, 0.03, 0.03), click(0.012, 0.5)), ts, -0.6)
place(fft_filter(rng.standard_normal(int(0.5 * SR)), 200, 3000) * np.hanning(int(0.5 * SR)) * 0.02, 6.0, -0.6)

# ---------------- room tone: dusk air + crickets; the open door adds the room's warmth ----------------
air = fft_filter(rng.standard_normal(NS), 40, 1800, tilt=-0.8); air = air / np.std(air) * 0.0035
place(air, -T0, 0.0, 'room')
cr = np.zeros(NS); tt2 = np.arange(NS) / SR
for (f, rate, ph0, amp, pan) in [(4600, 1.9, 0.1, 0.0035, 0.6), (5200, 1.45, 0.7, 0.0025, -0.3), (4300, 2.3, 0.3, 0.0018, 0.9)]:
    sig = np.zeros(NS); t = ph0
    while t < DUR:
        for k in range(3):
            a = int((t + k * 0.045) * SR); m = int(0.025 * SR)
            if a + m < NS: sig[a:a + m] += np.sin(2 * math.pi * f * np.arange(m) / SR) * np.hanning(m) * amp
        t += 1 / rate * rng.uniform(0.85, 1.15)
    place(sig, -T0, pan, 'room')
roomwarm = fft_filter(rng.standard_normal(NS), 60, 500); roomwarm = roomwarm / np.std(roomwarm) * 0.0025
op = np.clip((tt2 - T0 - 5.0) / 1.5, 0, 1) * (tt2 < T0 + 32.0)
place(roomwarm * op, -T0, -0.5, 'room')
# cards: a quiet tone under the title, nothing under the end card but the room fading
fade = np.ones(NS); fade[: int(1.0 * SR)] = np.linspace(0, 1, int(1.0 * SR)); fade[int(35.0 * SR):] = np.linspace(1, 0, NS - int(35.0 * SR))
L *= fade; R *= fade

# ---------------- levels report and write ----------------
def rms_db(x):
    x = x[np.abs(x) > 1e-6] if np.any(np.abs(x) > 1e-6) else x; return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


def span_rms(track, spans):
    segs = [track[int((T0 + a) * SR):int((T0 + b) * SR)] for a, b in spans]; x = np.concatenate(segs); return 20 * math.log10(math.sqrt(np.mean(x ** 2)) + 1e-12)


peak = max(np.abs(L).max(), np.abs(R).max()); g = min(1.0, 0.89 / peak); L *= g; R *= g
for k in tracks: tracks[k] *= g
mix = (L + R) / 2
rep = {'calls_rms_dbfs': round(span_rms(mix, voice_spans['call']), 1), 'soft_rms_dbfs': round(span_rms(mix, voice_spans['soft']), 1),
       'calls_voice_only_dbfs': round(span_rms(tracks['voice_call'], voice_spans['call']), 1), 'soft_voice_only_dbfs': round(span_rms(tracks['voice_soft'], voice_spans['soft']), 1),
       'room_tone_rms_dbfs': round(20 * math.log10(math.sqrt(np.mean(tracks['room'][int(3.5 * SR):int(35 * SR)] ** 2)) + 1e-12), 1), 'peak_dbfs': round(20 * math.log10(max(np.abs(L).max(), np.abs(R).max())), 1)}
rep['soft_below_calls_db'] = round(rep['calls_voice_only_dbfs'] - rep['soft_voice_only_dbfs'], 1)
rep['soft_above_room_db'] = round(rep['soft_voice_only_dbfs'] - rep['room_tone_rms_dbfs'], 1)
st = np.stack([L, R], 1); pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
import wave
with wave.open(OUT, 'wb') as wf: wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
json.dump(rep, open(os.path.splitext(OUT)[0] + '-levels.json', 'w'), indent=1)
print('wrote', OUT, rep)
