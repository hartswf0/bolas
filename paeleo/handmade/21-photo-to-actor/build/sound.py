"""Sound: the dusk, the calls, the soft voice, the door, and the dog's own sounds placed from its performance.

Voices are synthesised here with flite (ffmpeg's libflite filter, voice 'slt'); everything else is computed noise and
resonance. Paw clicks fall on the frames where a photographed paw touches down (from performance.json), the sigh on
the lie-down, tail thumps on the boards while it wags looking in. Writes build/cache/scene.wav (32 s) and
sound-levels.json (measured RMS of the calls vs the soft voice).
"""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
CACHE = os.path.join(FOLDER, 'build', 'cache')
SR = 48000; DUR = 32.0
N = int(SR * DUR)
rng = np.random.default_rng(2102)
perf = json.load(open(os.path.join(CACHE, 'performance.json')))


def flite(text, name, tempo=1.0):
    path = os.path.join(CACHE, name + '.wav')
    af = 'atempo=%.3f' % tempo if tempo != 1.0 else 'anull'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', "flite=text='%s':voice=slt" % text,
                    '-af', af, '-ar', str(SR), '-ac', '1', path], check=True)
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    # trim flite's leading silence so the first phoneme lands on the score frame (critic round 1: voices were 0.3-0.4 s late)
    k = int(0.005 * SR); env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, 'same'))
    on = int(np.argmax(env > 0.06 * env.max()))
    x = x[max(0, on - int(0.01 * SR)):]
    x[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    return x


def lowpass(x, fc):
    # one-pole, run twice
    a = np.exp(-2 * np.pi * fc / SR)
    for _ in range(2):
        y = np.zeros_like(x); acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc; y[i] = acc
        x = y
    return x


def lp_fast(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))


def hp_fast(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (f / fc) ** 4 / (1 + (f / fc) ** 4), len(x))


def bp_fast(x, lo, hi): return hp_fast(lp_fast(x, hi), lo)


def put(buf, x, t, gain=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    buf[i:j] += gain * x[:j - i]


def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


amb = np.zeros(N); voice_call = np.zeros(N); voice_soft = np.zeros(N); fx = np.zeros(N)

# ---- dusk ambience: wind in the field, crickets, a far dog-less quiet
wind = lp_fast(rng.normal(0, 1, N), 380) * (0.6 + 0.4 * np.sin(np.linspace(0, 7, N)))
amb += 0.012 * wind / np.std(wind)
t = np.arange(N) / SR
for k, (f0, rate, ph) in enumerate([(4300, 2.7, 0.0), (4700, 3.1, 1.3), (3900, 2.2, 2.1)]):
    gate = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(float)
    trill = (np.sin(2 * np.pi * 32 * t) > 0).astype(float)
    env = lp_fast(gate * trill, 300)
    amb += 0.0035 * env * np.sin(2 * np.pi * f0 * t) * (0.7 + 0.3 * np.sin(0.13 * t + k))

# ---- the person: two calls (commands), then the soft voice (circumstances)
c1 = flite('Come here!', 'v_call1'); c2 = flite('Come here. Come here!', 'v_call2')
for x, at in ((c1, 0.98), (c2, 3.40)):
    x = np.tanh(2.2 * x) / np.tanh(2.2)                 # pushed: a raised, hard voice
    put(voice_call, x / np.max(np.abs(x)) * 0.62, at)
s1 = flite("It's all right.", 'v_soft1', 0.82); s2 = flite("It's all right.", 'v_soft2', 0.78); s3 = flite('Come in.', 'v_soft3', 0.8)
for x, at in ((s1, 7.40), (s2, 10.40), (s3, 26.40)):
    x = lp_fast(x, 1900)
    put(voice_soft, x / np.max(np.abs(x)) * 0.17, at)

# ---- the door: latch, a slow creak as it swings, the room tone of the lit hall rising
latch = rng.normal(0, 1, int(0.03 * SR)) * np.exp(-np.linspace(0, 9, int(0.03 * SR)))
put(fx, bp_fast(np.r_[latch, np.zeros(2000)], 900, 5000) * 0.35, 6.18)
cl = int(0.9 * SR); tt = np.arange(cl) / SR
f_inst = 210 + 140 * np.sin(np.linspace(0, 2.6, cl)) + 30 * rng.normal(0, 1, cl).cumsum() / np.sqrt(cl)
creak = np.sin(2 * np.pi * np.cumsum(f_inst) / SR) * (np.sin(2 * np.pi * 23 * tt) > 0.2) * np.hanning(cl)
put(fx, bp_fast(np.r_[creak, np.zeros(4000)], 150, 2500) * 0.07, 6.22)
hum = lp_fast(rng.normal(0, 1, N), 160) * np.clip((t - 6.3) / 1.0, 0, 1)
amb += 0.006 * hum / np.std(hum)

# ---- she steps aside and sits: board creak and cloth
for at in (5.45, 5.9, 6.15):
    put(fx, bp_fast(rng.normal(0, 1, int(0.25 * SR)) * np.hanning(int(0.25 * SR)), 300, 2200) * 0.05, at)

# ---- the dog: paw clicks at each touchdown, a sigh lying down, tail thumps while it looks in
G = None
prev = {}
steps = []
for r in perf:
    for ln, (fx_, fy) in r['pose']['feet'].items():
        lifted = fy < 199.5
        if prev.get(ln) and not lifted and r['pose']['lie'] < 0.2:
            steps.append((r['t'], ln))
        prev[ln] = lifted
for ts, ln in steps:
    n = int(0.018 * SR)
    click = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 7, n))
    thud = np.sin(2 * np.pi * 120 * np.arange(n * 3) / SR) * np.exp(-np.linspace(0, 6, n * 3))
    put(fx, bp_fast(np.r_[click, np.zeros(600)], 1500, 7000) * 0.05, ts)
    put(fx, thud * 0.015, ts)
n = int(1.3 * SR)
sigh = lp_fast(rng.normal(0, 1, n), 900) * np.sin(np.linspace(0, np.pi, n)) ** 2
put(fx, sigh / np.max(np.abs(sigh)) * 0.08, 24.35)
for k in range(5):                                       # three-ish thumps of a tail on the boards
    nn = int(0.12 * SR)
    th = np.sin(2 * np.pi * 70 * np.arange(nn) / SR) * np.exp(-np.linspace(0, 8, nn))
    put(fx, th * 0.05, 26.75 + k * 0.36)
n = int(0.6 * SR)
whine = np.sin(2 * np.pi * np.cumsum(np.linspace(880, 700, n)) / SR) * np.sin(np.linspace(0, np.pi, n)) ** 2
put(fx, lp_fast(whine, 2500) * 0.025, 1.35)            # a thin whine as it backs away from the call

mix = amb + voice_call + voice_soft + fx
peak = np.max(np.abs(mix))
mix = mix / max(1.0, peak / 0.95)
# measured levels (active speech only)
def active(x):
    env = np.abs(x); k = int(0.02 * SR)
    e = np.convolve(env, np.ones(k) / k, 'same'); return x[e > 0.1 * e.max()]
lv = {'call_rms_dbfs': round(rms_db(active(voice_call)), 2), 'soft_rms_dbfs': round(rms_db(active(voice_soft)), 2),
      'room_tone_rms_dbfs': round(rms_db(amb), 2)}
lv['soft_under_call_db'] = round(lv['call_rms_dbfs'] - lv['soft_rms_dbfs'], 2)
lv['soft_over_room_db'] = round(lv['soft_rms_dbfs'] - lv['room_tone_rms_dbfs'], 2)
lv['paw_touchdowns'] = len(steps)
def onsets(x, t0s):
    k = int(0.005 * SR); env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, 'same')); out = []
    for t0 in t0s:
        seg = env[int((t0 - 0.3) * SR):int((t0 + 1.0) * SR)]
        out.append(round(t0 - 0.3 + int(np.argmax(seg > 0.06 * env.max())) / SR, 3))
    return out
lv['voice_onsets_s'] = {'calls': onsets(voice_call, [1.0, 3.42]), 'soft': onsets(voice_soft, [7.42, 10.42, 26.42])}
json.dump(lv, open(os.path.join(FOLDER, 'sound-levels.json'), 'w'), indent=1)
with wave.open(os.path.join(CACHE, 'scene.wav'), 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print(lv)
