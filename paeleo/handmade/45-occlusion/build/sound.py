"""SCION 45 · Sound, composited like the picture: every source is a layer, and the door is a holdout for sound too.

Sources (all synthesized here; no recordings): the person's voice (flite 'slt', CMU synthesis, run locally through ffmpeg),
porch dusk (crickets + air), the room inside (lamp hum + a clock) heard THROUGH the door: while the door is ajar the room is
held out (low-passed, -14 dB); when it opens the holdout lifts. Foley from the dog's own substitutions (claws on boards at
each walk-cel change, a scuffle when it turns, the body meeting the boards when it lies), the person's steps and the bench,
the door's latch and hinge. Output: build/cache/scene_audio.wav (38 s, 48 kHz stereo) + audio_levels.json (measured).
Version: sound-v3
"""
import json, math, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 48000
PRE = 3.0                          # title card before the scene
TOTAL = 38.0
N = int(TOTAL * SR)
rng = np.random.default_rng(45)
CACHE = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(HERE, '../../../../paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']


def db(x):
    return 10 ** (x / 20)


def fft_filter(x, lo=None, hi=None, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * g, len(x))


def tv_lowpass(x, fc_curve):
    """Time-varying low-pass by crossfading two fixed filters (muffled / open)."""
    closed = fft_filter(x, hi=500, order=2)
    return closed * (1 - fc_curve) + x * fc_curve


def place(buf, sig, t, gain=1.0, pan=0.0):
    i0 = int((t + PRE) * SR)
    if i0 >= N:
        return
    sig = sig[:max(0, N - i0)]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i0:i0 + len(sig)] += sig * gain * l * 1.414
    buf[1, i0:i0 + len(sig)] += sig * gain * r * 1.414


def flite(text, rate=1.0):
    p = os.path.join(CACHE, 'vo_%s.wav' % abs(hash((text, rate))))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', "flite=text='%s':voice=slt" % text,
                    '-af', 'aresample=%d,atempo=%.3f' % (SR, rate), '-ac', '1', '-f', 'f32le', p + '.raw'], check=True)
    return np.fromfile(p + '.raw', np.float32).astype(np.float64)


def reverb(x, wet=0.2, decay=0.35):
    ir_len = int(decay * SR)
    ir = rng.standard_normal(ir_len) * np.exp(-np.linspace(0, 6, ir_len))
    ir = fft_filter(ir, lo=300, hi=4000)
    ir /= np.abs(ir).sum() / 6
    nfft = 1 << int(math.ceil(math.log2(len(x) + ir_len)))
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x) + ir_len]
    out = np.zeros(len(x) + ir_len); out[:len(x)] += x
    return out * (1 - wet) + y * wet


def click(dur=0.018, f=2600, q=8, amp=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t * 300)
    s = fft_filter(s, lo=f / 1.6, hi=f * 1.6)
    knock = np.sin(2 * math.pi * (260 + 60 * rng.random()) * t) * np.exp(-t * 90) * 0.6
    return (s * 0.8 + knock) * amp


def thump(dur=0.35, f=90, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * math.pi * f * t * (1 - 0.3 * t)) * np.exp(-t * 14)
    s += fft_filter(rng.standard_normal(n), hi=600) * np.exp(-t * 18) * 0.6
    return s * amp


def breath(dur=0.9, amp=1.0, hi=1800):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return fft_filter(rng.standard_normal(n), lo=200, hi=hi) * env * amp


def creak(dur=0.8, f0=180, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.25 * np.sin(2 * math.pi * 1.3 * t) + 0.1 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)))
    ph = 2 * math.pi * np.cumsum(f) / SR
    saw = (ph / (2 * math.pi)) % 1.0 - 0.5
    stick = (np.sin(ph * 0.5) > 0.3).astype(float)
    s = fft_filter(saw * stick, lo=300, hi=2500)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1))
    return s * env * amp


def main():
    buf = np.zeros((2, N))
    T = np.arange(N) / SR - PRE      # scene time
    # ---------------------------------------------------------------- porch dusk bed (crickets + air), the room tone
    air = fft_filter(rng.standard_normal(N), lo=60, hi=700) * 0.010
    cr = np.zeros(N)
    for k in range(3):
        f = 4300 + 350 * k
        rate = 2.6 + 0.7 * k
        gate = (np.sin(2 * math.pi * rate * (T + 0.37 * k)) > 0.55).astype(float)
        trill = (np.sin(2 * math.pi * 38 * T) > 0).astype(float)
        cr += np.sin(2 * math.pi * f * T) * gate * trill * (0.0035 / (k + 1))
    cr = fft_filter(cr, lo=2000, hi=8000)
    fade_in = np.clip((T + PRE - 1.2) / 2.0, 0, 1); fade_out = np.clip((35.6 - T) / 2.2, 0, 1)
    bed = (air + cr) * fade_in * fade_out
    buf[0] += bed; buf[1] += bed * 0.92 + np.roll(cr, 211) * 0.3 * fade_in * fade_out
    # ---------------------------------------------------------------- the room, through the door (holdout for sound)
    hum = (np.sin(2 * math.pi * 120 * T) * 0.5 + np.sin(2 * math.pi * 240 * T) * 0.25 + np.sin(2 * math.pi * 360 * T) * 0.1) * 0.006
    clock = np.zeros(N)
    for k in range(int(TOTAL)):
        tt = k * 1.0 - PRE + 0.13
        if tt > -PRE:
            place_mono = click(0.012, 3400, amp=0.012 if k % 2 else 0.009)
            i0 = int((tt + PRE) * SR); clock[i0:i0 + len(place_mono)] += place_mono[:max(0, N - i0)]
    room = hum + clock
    door_open = np.clip((T - 6.12) / 0.88, 0, 1); door_open = door_open * door_open * (3 - 2 * door_open)
    room = tv_lowpass(room, door_open) * (db(-14) + (1 - db(-14)) * door_open) * fade_in * fade_out
    buf[0] += room * 0.8; buf[1] += room * 0.6
    # ---------------------------------------------------------------- the voice (synthesized), calls vs soft
    calls = []
    v1 = reverb(flite('Come here!', 0.95), 0.18) ; place(buf, v1, 0.98, db(-6), -0.35); calls.append((0.98, len(v1), db(-6)))
    v2 = reverb(flite('Come here! Come on!', 1.0), 0.18); place(buf, v2, 3.38, db(-4.5), -0.35); calls.append((3.38, len(v2), db(-4.5)))
    softs = []
    for (t0, txt) in [(7.42, "It's all right."), (10.42, "It's all right. It's all right.")]:
        s = fft_filter(flite(txt, 0.82), hi=2600) ; s = reverb(s, 0.08)
        place(buf, s, t0, db(-17), -0.55); softs.append((t0, len(s), db(-17)))
    s = fft_filter(flite('Come in.', 0.8), hi=2600); s = reverb(s, 0.08)
    place(buf, s, 26.42, db(-17), -0.5); softs.append((26.42, len(s), db(-17)))
    # ---------------------------------------------------------------- the dog: foley from its own cel substitutions
    import dog as DOG
    events = []
    prev_k = None
    for f in FR:
        t = f['t']; d = f['dog']; x = d['x']
        pan = max(-1, min(1, (x - 1.5) / 3.0))
        if 1.0 <= t < 2.333:
            k = int((x - 3.0) / (DOG.STRIDE / 6))
        elif 14.708 <= t < 23.792:
            k = int((4.0 - x) / (DOG.STRIDE / 6))
        else:
            k = None
        if k is not None and prev_k is not None and k != prev_k:
            amp = db(-26) if t < 3 else db(-30)
            place(buf, click(0.02, 2400 + 500 * rng.random(), amp=1.0), t + 0.01 * rng.random(), amp, pan); events.append(('claw', round(t, 3)))
        prev_k = k
    # the turn away (3.42-3.96): a scuffle of claws
    for k in range(7):
        tt = 3.42 + k * 0.075 + 0.02 * rng.random()
        place(buf, click(0.025, 2000 + 800 * rng.random()), tt, db(-27), 0.75); events.append(('scuffle', round(tt, 3)))
    # lies down, back turned (4.4-5.0): hind end then chest on the boards, and a sigh
    place(buf, thump(0.3, 85), 4.52, db(-22), 0.8); place(buf, thump(0.35, 75), 4.86, db(-20), 0.8)
    place(buf, breath(1.1, hi=1400), 5.1, db(-30), 0.8); events += [('lie', 4.52), ('lie', 4.86), ('sigh', 5.1)]
    # turns back to look and gets up (7.46-8.0): a quick shake of the collar fur, claws
    place(buf, breath(0.25, hi=3000), 7.47, db(-32), 0.8)
    for k in range(5):
        tt = 7.62 + k * 0.09; place(buf, click(0.02, 2300), tt, db(-28), 0.8); events.append(('rise', round(tt, 3)))
    for k in range(5):
        tt = 8.0 + k * 0.2; place(buf, click(0.02, 2500), tt, db(-30), 0.75); events.append(('turn', round(tt, 3)))
    # lies down across the sill (23.8-24.6), exhale
    place(buf, thump(0.3, 80), 24.05, db(-22), 0.1); place(buf, thump(0.4, 70), 24.42, db(-20), 0.05)
    place(buf, breath(1.4, hi=1200), 24.8, db(-29), 0.05); events += [('lie', 24.05), ('lie', 24.42), ('exhale', 24.8)]
    # looks in (26.6-28.3): tail sweeps the boards (score wag 0.8)
    for k in range(6):
        tt = 26.75 + k * 0.27
        place(buf, breath(0.16, hi=5000) * 0.8, tt, db(-31), 0.2); events.append(('tail', round(tt, 3)))
    # settles (28.4): a long breath out
    place(buf, breath(1.6, hi=1000), 28.6, db(-28), 0.05); events.append(('settle', 28.6))
    # ---------------------------------------------------------------- the person: steps, bench, the door
    for k, tt in enumerate([4.85, 5.2, 5.5, 5.8]):
        place(buf, thump(0.18, 110 + 10 * k), tt, db(-27), -0.5 - 0.1 * k)
    place(buf, creak(0.45, 260), 5.95, db(-30), -0.8)
    place(buf, click(0.03, 1800), 6.12, db(-24), -0.2)                     # latch
    place(buf, creak(0.9, 170), 6.18, db(-25), -0.1)                       # hinge
    # ---------------------------------------------------------------- master
    peak = np.abs(buf).max()
    buf *= db(-1.5) / peak
    # measured levels (scene time) for the record
    def rms_at(t0, n, ch=0):
        i0 = int((t0 + PRE) * SR); seg = buf[:, i0:i0 + n].mean(0)
        return 20 * math.log10(max(1e-9, np.sqrt((seg ** 2).mean())))
    lev = {'calls_dbfs': [round(rms_at(t, int(n * 0.8)), 2) for t, n, g in calls],
           'soft_dbfs': [round(rms_at(t, int(n * 0.8)), 2) for t, n, g in softs]}
    quiet = buf[:, int((12.5 + PRE) * SR):int((14.0 + PRE) * SR)].mean(0)
    lev['room_tone_dbfs_12.5_14.0'] = round(20 * math.log10(np.sqrt((quiet ** 2).mean())), 2)
    lev['soft_minus_calls_db'] = round(max(lev['soft_dbfs']) - min(lev['calls_dbfs']), 2)
    lev['soft_minus_room_db'] = round(min(lev['soft_dbfs']) - lev['room_tone_dbfs_12.5_14.0'], 2)
    lev['peak_dbfs'] = round(20 * math.log10(np.abs(buf).max()), 2)
    lev['note'] = 'RMS over 80% of each line (includes the bed under it). Measured, not listened to.'
    json.dump({'levels': lev, 'events': events}, open(os.path.join(CACHE, 'audio_levels.json'), 'w'), indent=1)
    pcm = (np.clip(buf.T, -1, 1) * 32767).astype('<i2')
    import wave
    with wave.open(os.path.join(CACHE, 'scene_audio.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(json.dumps(lev))


if __name__ == '__main__':
    main()
