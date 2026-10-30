"""Sound for PAE-02 / SCION 49: synthesized here (numpy) plus speech from ffmpeg's flite filter. Nothing is sampled.
Writes build/cache/sound.wav (48 kHz stereo, 38.0 s: 3 s title, 32 s scene, 3 s end card) and ../sound.json (levels measured).
Scene time t is film time - 3.0."""
import json, math, os, subprocess, wave
import numpy as np
from scipy.signal import lfilter

HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
SR = 48000; DUR = 38.0; OFF = 3.0
n = int(SR * DUR); L = np.zeros(n); Rt = np.zeros(n)
rng = np.random.default_rng(49)
SCORE = json.load(open(os.path.join(HERE, '..', '..', 'score', 'threshold-score.json')))
FR = SCORE['frames']


def at(t): return int((t + OFF) * SR)
def add(sig, t, pan=0.0, gain=1.0):
    i = at(t); j = min(n, i + len(sig)); s = sig[:j - i] * gain
    L[i:j] += s * math.sqrt((1 - pan) / 2); Rt[i:j] += s * math.sqrt((1 + pan) / 2)
def onepole(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); return lfilter([1 - a], [1, -a], x)
def bandpass(x, f0, q):
    # RBJ biquad
    w = 2 * math.pi * f0 / SR; al = math.sin(w) / (2 * q)
    b0, b1, b2, a0, a1, a2 = al, 0, -al, 1 + al, -2 * math.cos(w), 1 - al
    return lfilter([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0], x)
def env(m, a, r):
    e = np.ones(m); ka = max(1, min(m, int(a * SR))); kr = max(1, min(m, int(r * SR)))
    e[:ka] = np.linspace(0, 1, ka); e[-kr:] *= np.linspace(1, 0, kr); return e
def db(x): return 20 * math.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-9))


# ---- room tone (whole film) and dusk crickets outside (right of frame)
brown = np.cumsum(rng.standard_normal(n)); brown -= onepole(brown, 0.5); brown /= np.abs(brown).max()
tone = brown * 0.012
L += tone; Rt += tone
for k in range(int(DUR * 2.2)):
    t0 = rng.uniform(-3, 35); f = rng.choice([4300, 4700, 5100]); m = int(SR * 0.16)
    tt = np.arange(m) / SR
    chirp = np.sin(2 * math.pi * f * tt) * (0.5 + 0.5 * np.sin(2 * math.pi * 32 * tt)) * env(m, .01, .05)
    add(chirp, t0, pan=rng.uniform(.3, .9), gain=0.006)

# ---- the room, heard once the door opens: a clock and a small fire
def openness(t): u = min(max((t - 6.2) / 0.7, 0), 1); return 0.18 + 0.82 * u * u * (3 - 2 * u)
for s in range(0, 32):
    t = s + 0.37; m = int(SR * 0.03)
    tick = bandpass(rng.standard_normal(m), 2600 if s % 2 else 2100, 6) * env(m, .001, .025)
    add(tick, t, pan=-0.6, gain=0.05 * openness(t))
for k in range(260):
    t = rng.uniform(0, 32); m = int(SR * rng.uniform(.004, .02))
    add(bandpass(rng.standard_normal(m), rng.uniform(900, 3000), 3) * env(m, .001, .01), t, pan=-0.75, gain=0.03 * openness(t))

# ---- voices (flite, ffmpeg), calls loud, soft lines quiet and darker
def say(text, voice='rms', tempo=1.0, lp=None):
    f = os.path.join(CACHE, 'v_' + ''.join(c for c in text if c.isalnum())[:20] + f'_{tempo}.wav')
    af = [f'atempo={tempo}'] + ([f'lowpass=f={lp}'] if lp else []) + [f'aresample={SR}']
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', f"flite=text='{text}':voice={voice}",
                    '-af', ','.join(af), '-ac', '1', f], check=True)
    with wave.open(f) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    return x / (np.abs(x).max() + 1e-9)
calls = [(1.0, 'Come here!'), (3.42, 'Come here! Come on!')]
softs = [(7.42, "It's all right."), (10.42, "It's all right."), (26.42, 'Come in.')]
voice_levels = {'call': [], 'soft': []}
for t, txt in calls:
    v = say(txt, tempo=1.05) * 0.55; add(v, t, pan=-0.35); voice_levels['call'].append(db(v[np.abs(v) > 0.02]))
for t, txt in softs:
    v = say(txt, tempo=0.86, lp=2600) * 0.12; add(v, t, pan=-0.45); voice_levels['soft'].append(db(v[np.abs(v) > 0.006]))

# ---- the door: latch, then the creak as it swings (6.2 - 6.9 s)
m = int(SR * 0.04); add(bandpass(rng.standard_normal(m), 1800, 4) * env(m, .001, .03), 6.12, pan=-0.1, gain=0.25)
m = int(SR * 0.75); tt = np.arange(m) / SR
f0 = 140 + 160 * np.sin(np.pi * tt / 0.75) + 25 * np.sin(2 * np.pi * 7 * tt)
saw = 2 * ((np.cumsum(f0) / SR) % 1) - 1
add(bandpass(saw, 900, 3) * env(m, .05, .2), 6.2, pan=0.05, gain=0.12)

# ---- the person: three steps back to the bench, the bench takes the weight
for t in (5.46, 5.76, 6.06):
    m = int(SR * .09); add(bandpass(rng.standard_normal(m), 260, 2) * env(m, .002, .08), t, pan=-0.5, gain=0.3)
m = int(SR * .35); tt = np.arange(m) / SR
add(bandpass(2 * ((np.cumsum(90 + 40 * tt) / SR) % 1) - 1, 600, 4) * env(m, .03, .2), 6.28, pan=-0.6, gain=0.06)

# ---- the dog: paw clicks at every foot plant of the render's gait (same formula as render.py), thumps, tail, sigh
xs = np.array([f['dog']['x'] for f in FR]); dist = np.concatenate([[0], np.cumsum(-(xs[1:] - xs[:-1]))])
speed = np.abs(np.gradient(xs)) * 24
clicks = 0
for off in (0.0, 0.25, 0.5, 0.75):
    ph = dist / 0.28 + off
    for i in range(1, len(FR)):
        if speed[i] < 0.08: continue
        if math.floor(ph[i]) != math.floor(ph[i - 1]):     # a foot enters stance (forward) or leaves it (backing)
            t = i / 24; m = int(SR * .012)
            pan = max(-1, min(1, (xs[i] - 2.0) / 3))
            add(bandpass(rng.standard_normal(m), 3200, 5) * env(m, .0005, .01), t, pan=pan, gain=0.09); clicks += 1
for t, g in ((4.62, .5), (24.25, .45)):
    m = int(SR * .25); tt = np.arange(m) / SR
    add(np.sin(2 * math.pi * 70 * tt) * np.exp(-tt * 18) + onepole(rng.standard_normal(m), 300) * .5 * np.exp(-tt * 25), t, pan=.2, gain=g * .5)
for k, t in enumerate(np.arange(26.95, 28.3, 0.33)):
    m = int(SR * .08); tt = np.arange(m) / SR
    add(np.sin(2 * math.pi * 95 * tt) * np.exp(-tt * 40), t, pan=0.15, gain=0.12)
m = int(SR * 1.3); tt = np.arange(m) / SR
sigh = onepole(rng.standard_normal(m), 900) * np.sin(np.pi * tt / 1.3) ** 2
add(sigh / np.abs(sigh).max(), 28.6, pan=0.05, gain=0.05)

# ---- master: fades at the ends, peak -2 dBFS
st = np.stack([L, Rt], 1)
fade = np.ones(n); k = int(SR * .6); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
st *= fade[:, None]; st *= 10 ** (-2 / 20) / np.abs(st).max()
with wave.open(os.path.join(CACHE, 'sound.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
# measured levels of the mixed program in the voice windows vs room tone alone
mono = st.mean(1)
def win(t0, t1): return db(mono[at(t0):at(t1)])
lv = {'call_windows_db': [round(win(t, t + 1.0), 1) for t, _ in calls], 'soft_windows_db': [round(win(t, t + 1.0), 1) for t, _ in softs],
      'room_tone_window_db': round(win(12.5, 14.0), 1), 'paw_clicks': clicks}
lv['soft_minus_call_db'] = round(max(lv['soft_windows_db']) - min(lv['call_windows_db']), 1)
lv['soft_minus_room_db'] = round(min(lv['soft_windows_db']) - lv['room_tone_window_db'], 1)
json.dump({'about': 'RMS levels (dBFS) of the final mix in 1 s windows starting at each line; measured by sound.py',
           **lv}, open(os.path.join(HERE, '..', 'sound.json'), 'w'), indent=1)
print(lv)
