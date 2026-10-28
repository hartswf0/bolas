"""Sound for the 38 s film (3 s title + 32 s scene + 3 s card), 48 kHz stereo -> cache/sound.wav, cache/sound_levels.json.
Voice: flite speech synthesis (ffmpeg's libflite, voice 'slt') - calls loud, the soft voice >= 10 dB quieter and darker.
Foley synthesized: paw taps at every planted-foot onset of the gait planner, lying thumps, door latch and creak, the
person's steps. Room tone: dusk air + crickets. A faint detuned tone follows the puppet's out-of-distribution score
(measured per frame in the render): the model's uncertainty, audible."""
import json, os, subprocess, sys
import numpy as np
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controls as CT
import dogmodel as DM

HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache')
SR = 48000; T = 38.0; OFF = 3.0
N = int(SR * T)
rng = np.random.default_rng(15)
L = np.zeros(N); R = np.zeros(N)


def db(x):
    return 10 ** (x / 20)


def put(sig, t, gain=1.0, pan=0.0):
    i = int((t + OFF) * SR); j = min(N, i + len(sig))
    if i >= N or j <= i:
        return
    s = sig[:j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); R[i:j] += s * np.sqrt(0.5 * (1 + pan))


def tts(text, name):
    path = os.path.join(C, 'tts_%s.wav' % name)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', "flite=text='%s':voice=slt" % text,
                    '-ar', str(SR), '-ac', '1', path], check=True)
    import wave
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    return x / (np.abs(x).max() + 1e-9)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2)); return signal.lfilter(b, a, x)


def env(n, a=0.002, d=0.08):
    t = np.arange(n) / SR; return (1 - np.exp(-t / a)) * np.exp(-t / d)


def paw(gain=1.0):
    n = int(0.09 * SR); x = rng.normal(0, 1, n) * env(n, 0.001, 0.018)
    board = np.sin(2 * np.pi * rng.uniform(170, 230) * np.arange(n) / SR) * env(n, 0.002, 0.03)
    return (bp(x, 900, 4000) * 0.5 + board * 0.35) * gain


def thump(gain=1.0, dur=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    return (lp(rng.normal(0, 1, n), 300) * env(n, 0.01, dur / 3) * 3 + np.sin(2 * np.pi * 70 * t) * env(n, 0.01, 0.1)) * gain


def breath(dur=0.9, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.sin(np.pi * t / dur) ** 2
    return bp(rng.normal(0, 1, n), 300, 1800) * e * gain


def voice(x, soft=False):
    if soft:
        x = lp(x, 2600) * 0.9 + bp(rng.normal(0, 1, len(x)), 1500, 5000) * 0.03 * (np.abs(lp(np.abs(x), 30)) > 0.02)
    return x


if __name__ == '__main__':
    ctrl = CT.controls()
    # room tone: dusk air (low noise) + crickets
    air = lp(rng.normal(0, 1, N), 500) * db(-50) * 4
    L += air; R += lp(rng.normal(0, 1, N), 500) * db(-50) * 4
    t = np.arange(N) / SR
    for k, (f0, rate, pan) in enumerate([(4300, 13.0, -0.6), (4700, 11.2, 0.5), (3900, 15.5, 0.1)]):
        chirp = np.sin(2 * np.pi * f0 * t) * (np.sin(2 * np.pi * rate * t) > 0.55) * (np.sin(2 * np.pi * 0.37 * t + k * 2) > -0.3)
        chirp = lp(chirp, 7000) * db(-46)
        L += chirp * (1 - pan) / 2; R += chirp * (1 + pan) / 2
    # interior warmth when the door opens: a soft low band of room sound
    door = np.array([CT.world(tt)['door'] for tt in np.clip(t - OFF, 0, 31.99)])
    warm = lp(rng.normal(0, 1, N), 220) * db(-46) * 4 * door
    L += warm * 1.2; R += warm * 0.8
    # voices (times from the score timeline)
    call = tts('Come here.', 'call'); call2 = tts('Come here!', 'call2')
    soft1 = tts("It's all right.", 'soft1'); soft2 = tts("It's all right.", 'soft2'); comein = tts('Come in.', 'comein')
    G_CALL, G_SOFT = db(-9), db(-21)
    put(voice(call), 1.0, G_CALL, -0.55); put(voice(call2), 3.4, G_CALL, -0.55)
    put(voice(soft1, True), 7.45, G_SOFT, -0.35); put(voice(soft2, True), 10.45, G_SOFT, -0.35)
    put(voice(comein, True), 26.4, G_SOFT, -0.45)
    levels = {}
    for name, x, g in [('call', call, G_CALL), ('call2', call2, G_CALL), ('soft', voice(soft1, True), G_SOFT), ('come_in', voice(comein, True), G_SOFT)]:
        v = x[np.abs(lp(np.abs(x), 30)) > 0.05] * g
        levels[name + '_rms_dbfs'] = round(float(20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-12)), 1)
    # door: latch at 6.2, creak 6.25-7.0
    put(bp(rng.normal(0, 1, 2400), 1500, 6000) * env(2400, 0.0005, 0.01), 6.2, db(-24), -0.7)
    n = int(0.8 * SR); tt = np.arange(n) / SR
    f = 380 + 120 * np.sin(2 * np.pi * 1.3 * tt) + 40 * rng.normal(0, 1, n).cumsum() / np.sqrt(n)
    creak = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (np.sin(np.pi * tt / 0.8) ** 1.5)
    put(bp(creak, 500, 2500) * (np.sin(2 * np.pi * 23 * tt) > 0), 6.25, db(-30), -0.7)
    # person: steps aside 4.7-5.4, sits 5.6-6.3 (rustle + soft bump)
    for ts in [4.75, 5.05, 5.32]:
        put(thump(1.0, 0.25), ts, db(-27), -0.5)
    put(bp(rng.normal(0, 1, int(0.7 * SR)), 600, 3000) * np.hanning(int(0.7 * SR)), 5.6, db(-36), -0.4)
    put(thump(1.0, 0.4), 6.2, db(-26), -0.3)
    # dog paws: stance onsets of every leg from the gait planner (the same function that plants the feet)
    prev = {}
    taps = 0
    for c in ctrl:
        for l, (up, lo, foot, off, side, bend) in DM.LEG.items():
            cc = c['D'] / DM.STRIDE + off; u = cc - np.floor(cc)
            st = u < DM.DUTY
            if l in prev and st and not prev[l] and c['lie'] < 0.3:
                pan = np.clip((c['X'] - 2.4) / 3, -1, 1)
                put(paw(), c['t'], db(-31 + 3 * (side > 0)), pan); taps += 1
            prev[l] = st
    levels['paw_taps'] = taps
    # lying: refusal 4.5-5.0 and the sill 23.9-24.5, with a breath out; the look-in 26.5 a small sniff
    put(thump(1.0, 0.5), 4.75, db(-26), 0.5); put(breath(1.1), 5.2, db(-36), 0.5)
    put(thump(1.0, 0.5), 24.25, db(-25), -0.6); put(breath(1.4), 24.6, db(-33), -0.6)
    for k in range(3):
        put(bp(rng.normal(0, 1, int(0.07 * SR)), 2000, 7000) * np.hanning(int(0.07 * SR)), 26.75 + 0.11 * k, db(-38), -0.6)
    # uncertainty tone: follows the measured OOD score of the render, if a trace exists
    trp = os.path.join(HERE, '..', 'trace.json')
    if os.path.exists(trp):
        tr = json.load(open(trp))['frames']
        ood = np.array([f.get('ood', 0) or 0 for f in tr])
        o = np.interp(t - OFF, [f['t'] for f in tr], ood, left=0, right=0)
        o = lp(o, 3)
        tone = (np.sin(2 * np.pi * 196 * t) + np.sin(2 * np.pi * 199.5 * t) + 0.5 * np.sin(2 * np.pi * 293 * t)) * o * db(-44)
        L += tone; R += tone
        levels['ood_tone_peak_dbfs'] = round(float(20 * np.log10(np.abs(tone).max() + 1e-12)), 1)
    # title/end card: a single low tone fading
    for t0 in [0.2, 35.2]:
        n = int(2.4 * SR); tt = np.arange(n) / SR
        put(np.sin(2 * np.pi * 110 * tt) * np.sin(np.pi * tt / 2.4) ** 2 * 0.5 + np.sin(2 * np.pi * 165 * tt) * np.sin(np.pi * tt / 2.4) ** 2 * 0.25, t0 - OFF, db(-30))
    room = np.concatenate([L[int(3.2 * SR):int(3.9 * SR)]])
    levels['room_tone_rms_dbfs'] = round(float(20 * np.log10(np.sqrt((room ** 2).mean()))), 1)
    levels['soft_below_call_db'] = round(levels['call_rms_dbfs'] - levels['soft_rms_dbfs'], 1)
    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0.95:
        L *= 0.95 / peak; R *= 0.95 / peak
    st = (np.stack([L, R], 1) * 32767).astype(np.int16)
    import wave
    w = wave.open(os.path.join(C, 'sound.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
    json.dump(levels, open(os.path.join(C, 'sound_levels.json'), 'w'), indent=1)
    print(levels)
