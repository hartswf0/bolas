"""SCION-25 RIVE · sound, synthesized from the event trace (no recordings).
python3 build/sound.py RENDER_TRACE_JSON OUT_WAV OUT_LEVELS_JSON

Every dog sound is fired by an event the puppet's state machine or its stepping solver emitted while the film was rendered
(footfalls, turns, going down, chin down, looking in); every world sound by the score's timeline (calls, soft voice, the door).
Voices are formant-synthesized syllables, not words a recognizer would accept: a firm two-beat call and a soft, breathy phrase."""
import sys, json, os
import numpy as np

SR = 48000; T0 = 3.0; DUR = 38.0; N = int(SR * DUR)
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
score = json.load(open(os.path.join(R, 'paeleo/handmade/score/threshold-score.json')))
tr = json.load(open(sys.argv[1])); events = tr['events']; trace = {f['i']: f for f in tr['trace']}
rng = np.random.default_rng(25)
L = np.zeros(N); Rr = np.zeros(N)
stems = {k: np.zeros(N) for k in ('voice_call', 'voice_soft', 'room', 'dog', 'world')}


def pan_of_x(sx):  # screen x -> pan -1..1
    return float(np.clip((sx - 640) / 640, -1, 1))


def put(sig, t, pan=0.0, gain=1.0, stem='world'):
    i = int((T0 + t) * SR if stem != 'card' else t * SR)
    if i < 0 or i >= N: return
    sig = sig[: N - i] * gain
    a = np.sqrt((1 - pan) / 2); b = np.sqrt((1 + pan) / 2)
    L[i:i + len(sig)] += sig * a; Rr[i:i + len(sig)] += sig * b
    if stem in stems: stems[stem][i:i + len(sig)] += sig


def reson(x, f, bw):
    """two-pole resonator with time-varying centre f (array) and bandwidth bw (Hz)."""
    y = np.zeros_like(x); y1 = y2 = 0.0
    f = np.broadcast_to(f, x.shape); r = np.exp(-np.pi * bw / SR)
    for n in range(len(x)):
        c = 2 * r * np.cos(2 * np.pi * f[n] / SR)
        yn = x[n] + c * y1 - r * r * y2; y[n] = yn; y2 = y1; y1 = yn
    return y * (1 - r)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for n in range(len(x)): s = (1 - a) * x[n] + a * s; y[n] = s
    return y


def env(n, att, rel):
    e = np.ones(n); a = max(1, int(att * SR)); r = max(1, int(rel * SR))
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r); return e


VOW = {'a': (700, 1220, 2600), 'uh': (640, 1190, 2390), 'i': (300, 2200, 2900), 'ih': (420, 1950, 2600), 'eer': (440, 1700, 2500),
       'aw': (560, 880, 2500), 'ai': (720, 1500, 2550), 'ee': (330, 2250, 2950), 'oo': (380, 950, 2300)}


def syllable(dur, f0a, f0b, v1, v2=None, onset=None, breath=0.05, coda=None):
    n = int(dur * SR); t = np.arange(n) / SR
    f0 = np.linspace(f0a, f0b, n) * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * t))
    ph = np.cumsum(2 * np.pi * f0 / SR); src = np.zeros(n)
    for h in range(1, 28):
        src += np.sin(h * ph) / h ** 1.25 * (h * f0 < 5000)
    src = src * (1 - breath) + rng.normal(0, 1, n) * breath * 0.9
    F = [np.linspace(VOW[v1][k], VOW[v2 or v1][k], n) for k in range(3)]
    out = reson(src, F[0], 90) * 1.0 + reson(src, F[1], 110) * 0.55 + reson(src, F[2], 160) * 0.25
    out *= env(n, 0.025, 0.06)
    pre = np.zeros(0)
    if onset == 'k':
        b = rng.normal(0, 1, int(0.03 * SR)); pre = np.concatenate([np.zeros(int(0.04 * SR)), reson(b, np.full(len(b), 2400.0), 600) * env(len(b), 0.002, 0.02) * 2.5])
    if onset == 'h':
        b = rng.normal(0, 1, int(0.09 * SR)); pre = reson(b, np.full(len(b), 1600.0), 900) * env(len(b), 0.03, 0.03) * 0.9
    if onset == 'r':
        out[: int(0.05 * SR)] *= np.linspace(0.3, 1, int(0.05 * SR))
    post = np.zeros(0)
    if coda == 'm' or coda == 'n':
        m = int(0.12 * SR); tt = np.arange(m) / SR; ph2 = ph[-1] + np.cumsum(2 * np.pi * np.full(m, f0b) / SR)
        post = (np.sin(ph2) + 0.3 * np.sin(2 * ph2)) * np.linspace(1, 0, m) * 0.012 * (1 if coda == 'm' else 0.8)
        post = reson(post, np.full(m, 250.0), 100) * 6
    if coda == 'ts' or coda == 't':
        m = int(0.07 * SR); b = rng.normal(0, 1, m); post = reson(b, np.full(m, 5200.0), 1800) * env(m, 0.005, 0.03) * (0.5 if coda == 'ts' else 0.25)
    if coda == 'l':
        m = int(0.08 * SR); ph2 = ph[-1] + np.cumsum(2 * np.pi * np.full(m, f0b) / SR); post = reson(np.sin(ph2), np.full(m, 350.0), 120) * np.linspace(1, 0, m) * 0.6
    return np.concatenate([pre, out, post])


def phrase(syls, gap=0.03):
    parts = []
    for s in syls: parts += [syllable(**s), np.zeros(int(gap * SR))]
    x = np.concatenate(parts); return x / (np.max(np.abs(x)) + 1e-9)


def come_here(f0=215):
    return phrase([dict(dur=0.24, f0a=f0 + 15, f0b=f0, v1='uh', onset='k', coda='m', breath=0.03),
                   dict(dur=0.42, f0a=f0 + 30, f0b=f0 - 45, v1='ih', v2='eer', onset='h', breath=0.04)])


def come_on(f0=220):
    return phrase([dict(dur=0.2, f0a=f0 + 10, f0b=f0, v1='uh', onset='k', coda='m', breath=0.03),
                   dict(dur=0.36, f0a=f0 + 25, f0b=f0 - 30, v1='aw', coda='n', breath=0.04)])


def its_all_right(f0=185):
    return phrase([dict(dur=0.12, f0a=f0, f0b=f0, v1='ih', coda='ts', breath=0.45),
                   dict(dur=0.26, f0a=f0 + 5, f0b=f0 - 5, v1='aw', coda='l', breath=0.45),
                   dict(dur=0.5, f0a=f0, f0b=f0 - 35, v1='a', v2='ee', onset='r', coda='t', breath=0.5)], gap=0.04)


def come_in(f0=180):
    return phrase([dict(dur=0.2, f0a=f0, f0b=f0 - 5, v1='uh', onset='k', coda='m', breath=0.45),
                   dict(dur=0.42, f0a=f0 + 5, f0b=f0 - 30, v1='ih', coda='n', breath=0.5)], gap=0.05)


# ---------- voices from the score's timeline (the person stands left of the door: pan left) ----------
CALL = 10 ** (-7 / 20); SOFT = 10 ** (-21 / 20)
voice_at = [(1.05, come_here(), CALL, 'voice_call'), (1.85, come_here(225), CALL * 0.9, 'voice_call'),
            (3.45, come_here(225), CALL, 'voice_call'), (4.1, come_on(230), CALL * 0.95, 'voice_call'),
            (7.5, its_all_right(), SOFT, 'voice_soft'), (10.5, its_all_right(180), SOFT, 'voice_soft'), (26.45, come_in(), SOFT, 'voice_soft')]
for t, x, g, st in voice_at:
    put(lowpass(x, 5500), t, pan=-0.62 if t < 5 else -0.78, gain=g, stem=st)

# ---------- room tone: dusk air and crickets; a warm room once the door opens ----------
n = N; air = lowpass(rng.normal(0, 1, n), 380) * 0.035
cr = np.zeros(n); t = np.arange(n) / SR
for k in range(4):
    f = 4300 + 350 * k; rate = 2.1 + 0.4 * k; ph0 = rng.uniform(0, 6)
    gate = (np.sin(2 * np.pi * rate * t + ph0) > 0.55).astype(float) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + k))
    cr += np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t)) * lowpass(gate, 60) * 0.006
room = (air + cr) * np.clip(np.minimum(t - 2.6, 38 - t - 0.4) / 0.6, 0, 1)
L += room * 0.9; Rr += room * 1.1; stems['room'] += room
open_t = next(f['t'] for f in score['frames'] if f['door'] == 'open')
hum_n = int((32 - open_t + 0.3) * SR); tt = np.arange(hum_n) / SR
hum = (np.sin(2 * np.pi * 110 * tt) * 0.3 + np.sin(2 * np.pi * 165 * tt) * 0.15) * 0.004 + lowpass(rng.normal(0, 1, hum_n), 900) * 0.01
crackle = np.zeros(hum_n); idx = rng.choice(hum_n, 220, replace=False); crackle[idx] = rng.uniform(-1, 1, 220) * 0.08
hum = (hum + lowpass(crackle, 2500)) * np.clip(tt / 0.9, 0, 1)
put(hum, open_t - 0.2, pan=-0.85, gain=1.0, stem='room')

# ---------- the door and the person ----------
def creak(dur):
    m = int(dur * SR); tt = np.arange(m) / SR; rate = 55 + 70 * np.sin(np.pi * tt / dur) ** 2
    pulses = (np.sin(np.cumsum(2 * np.pi * rate / SR)) > 0.97).astype(float)
    return (reson(pulses, 480 + 250 * tt / dur, 60) + reson(pulses, 1150, 120) * 0.5) * env(m, 0.05, 0.15) * 0.9
put(creak(0.75), open_t - 0.12, pan=-0.6, gain=0.5, stem='world')
put(lowpass(rng.normal(0, 1, int(0.25 * SR)), 700) * env(int(0.25 * SR), 0.02, 0.15), 5.85, pan=-0.85, gain=0.12, stem='world')   # stool
put(creak(0.3) * 0.5, 6.0, pan=-0.85, gain=0.25, stem='world')

# ---------- dog sounds, from the event trace ----------
def sx_at(t):
    f = trace.get(min(767, max(0, int(round(t * 24)))));
    return f['x_screen'] if f and f.get('x_screen') else 900


def pad(loud):
    m = int(0.06 * SR); tt = np.arange(m) / SR
    th = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 60) * 0.5 + lowpass(rng.normal(0, 1, m), 600) * np.exp(-tt * 80) * 0.6
    tick = np.zeros(m); k = int(0.004 * SR); tick[k:k + 90] = reson(rng.normal(0, 1, 90), np.full(90, 3400.0), 900) * 3
    return (th + tick * 0.35) * loud


def jingle():
    m = int(0.18 * SR); tt = np.arange(m) / SR
    return sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt * d) for f, d in ((3120, 30), (4710, 40), (6260, 55))) * 0.02


def thump(m=0.35, f=70):
    k = int(m * SR); tt = np.arange(k) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 14) * 0.6 + lowpass(rng.normal(0, 1, k), 400) * np.exp(-tt * 18) * 0.4


def breath(dur, fc=900):
    k = int(dur * SR); b = rng.normal(0, 1, k); return (reson(b, np.full(k, fc), 700) + reson(b, np.full(k, 1800.0), 900) * 0.4) * np.sin(np.pi * np.arange(k) / k) ** 2 * 0.25


fired = []
for e in events:
    t = e['t']; p = pan_of_x(sx_at(t))
    if e['kind'] == 'footfall':
        fr = trace.get(int(round(t * 24)), {}); post = fr.get('posture', '')
        loud = 0.16 if post == 'backing' else 0.1
        put(pad(loud), t, p, 1.0, 'dog'); fired.append(('footfall', t))
        if rng.uniform() < (0.75 if post == 'backing' else 0.45): put(jingle(), t + 0.01, p, 1.0, 'dog')
    elif e['kind'] == 'transition':
        ev = e.get('event')
        if ev == 'turn_away': put(lowpass(rng.normal(0, 1, int(0.4 * SR)), 1800) * env(int(0.4 * SR), 0.05, 0.2) * 0.05, t, p, 1, 'dog'); put(jingle() * 1.5, t + 0.1, p, 1, 'dog'); fired.append((ev, t))
        if ev == 'going_down': put(thump(), t + 0.55, p, 0.5, 'dog'); put(jingle(), t + 0.5, p, 1, 'dog'); fired.append((ev, t + 0.55))
        if ev == 'chin_down': put(breath(0.9, 800), t + 0.15, p, 0.32, 'dog'); fired.append((ev, t))
        if ev == 'settles': put(breath(1.1, 700), t + 0.1, p, 0.4, 'dog'); fired.append((ev, t))
        if ev == 'head_leads': put(jingle() * 1.2, t + 0.08, p, 1, 'dog'); fired.append((ev, t))
        if ev == 'turn_back': put(lowpass(rng.normal(0, 1, int(0.35 * SR)), 1500) * env(int(0.35 * SR), 0.05, 0.2) * 0.04, t, p, 1, 'dog')
        if ev == 'looks_in':
            fired.append((ev, t)); put(jingle() * 1.3, t + 0.05, p, 1, 'dog')
            for k in range(5): put(thump(0.12, 120) * 0.5, t + 0.25 + k * 0.42, pan_of_x(sx_at(t) + 80), 0.35, 'dog')   # the tail beats the boards
    elif e['kind'] == 'world':
        pass

# ---------- cards: a quiet low chord under the title and the end ----------
def pad_chord(dur, fs):
    k = int(dur * SR); tt = np.arange(k) / SR; return sum(np.sin(2 * np.pi * f * tt) for f in fs) * np.sin(np.pi * tt / dur) ** 2 * 0.012
c1 = pad_chord(3.0, (110, 164.8, 220)); i0 = 0; L[:len(c1)] += c1; Rr[:len(c1)] += c1
c2 = pad_chord(3.0, (98, 146.8, 196, 246.9)); i1 = int(35 * SR); L[i1:i1 + len(c2)] += c2; Rr[i1:i1 + len(c2)] += c2

mx = max(np.max(np.abs(L)), np.max(np.abs(Rr)))
if mx > 0.95: L *= 0.95 / mx; Rr *= 0.95 / mx; scale = 0.95 / mx
else: scale = 1.0
pcm = (np.stack([L, Rr], 1) * 32767).astype(np.int16)
import wave
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def rms_db(x, mask=None):
    x = x * scale; x = x[np.abs(x) > 1e-5] if mask is None else x[mask]
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def active_db(x):   # RMS over the 50 ms windows where the stem is actually sounding (top 60 % of its window energy)
    w = int(0.05 * SR); k = len(x) // w; e = np.sqrt(np.mean((x[:k * w] * scale).reshape(k, w) ** 2, 1)); e = e[e > 1e-6]
    e = np.sort(e)[int(len(e) * 0.4):]; return float(20 * np.log10(np.sqrt(np.mean(e ** 2)) + 1e-12))


lv = {'call_active_rms_db': active_db(stems['voice_call']), 'soft_active_rms_db': active_db(stems['voice_soft']),
      'room_rms_db': rms_db(stems['room'][int(3.5 * SR):int(34.5 * SR)], np.ones(int(31 * SR), bool)),
      'peak_scale': scale, 'dog_sound_events': len(fired), 'dog_events_by_kind': {k: sum(1 for f in fired if f[0] == k) for k in set(f[0] for f in fired)}}
lv['soft_below_call_db'] = lv['call_active_rms_db'] - lv['soft_active_rms_db']; lv['soft_above_room_db'] = lv['soft_active_rms_db'] - lv['room_rms_db']
json.dump(lv, open(sys.argv[3], 'w'), indent=1); print(json.dumps(lv))
