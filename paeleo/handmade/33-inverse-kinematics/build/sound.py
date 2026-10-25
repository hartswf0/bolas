"""SCION 33 · sound: every sound is synthesized here and placed from the contact timeline (data/contacts.json), the door
simulation and the score's voice timeline. Nothing is recorded or found.
  voices  : formant synthesis (glottal pulse train through vowel resonators, noise for consonants)
  contacts: paw clicks and pads, footfalls on boards, pats, the door's grip, stick-slip creak, swing and stop
  room    : dusk air and crickets outside; the warm room tone grows as the door opens
Writes build/cache/scene.wav (32 s) and build/cache/film.wav (38 s: 3 s title + scene + 3 s card) and data/sound_levels.json."""
import os, json, math, pickle, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache'); DATA = os.path.join(ROOT, 'data')
SR = 48000
DUR = 32.0
n = int(SR * DUR)
rng = np.random.default_rng(33)
SCORE = json.load(open(os.path.join(REPO, 'paeleo/handmade/score/threshold-score.json')))
EV = json.load(open(os.path.join(DATA, 'contacts.json')))['events']
POSE = pickle.load(open(os.path.join(CACHE, 'pose.pkl'), 'rb'))
DOOR = POSE['door']


def db(x): return 10 ** (x / 20)


def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.zeros_like(x); s = 0.0
    # vectorised via lfilter-like recursion in chunks
    out = np.empty_like(x)
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s
        out[i] = s
    return out


def biquad_bp(x, f0, q):
    w0 = 2 * math.pi * f0 / SR; al = math.sin(w0) / (2 * q)
    b0, b1, b2 = al, 0.0, -al
    a0, a1, a2 = 1 + al, -2 * math.cos(w0), 1 - al
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        v = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x[i], y1, v
        y[i] = v
    return y


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def resonator_bank(src, formants):
    """formants: list of (freq_array or float, bandwidth, gain). Time-varying via per-sample freq arrays (2-pole)."""
    out = np.zeros_like(src)
    N_ = len(src)
    for F, B, G in formants:
        F = np.broadcast_to(np.asarray(F, float), (N_,))
        r = math.exp(-math.pi * B / SR)
        y1 = y2 = 0.0; y = np.empty(N_)
        c2 = -r * r
        for i in range(N_):
            c1 = 2 * r * math.cos(2 * math.pi * F[i] / SR)
            v = (1 - r) * src[i] + c1 * y1 + c2 * y2
            y2, y1 = y1, v; y[i] = v
        out += G * y
    return out


def glottal(f0):
    """band-limited-ish glottal pulse train from an f0 contour (Hz per sample)."""
    ph = np.cumsum(f0 / SR)
    frac = ph % 1.0
    pulse = np.where(frac < 0.6, np.sin(np.pi * frac / 0.6) ** 2, 0.0)
    d = np.diff(pulse, prepend=0)
    return d * 6.0


# ---------------- voice: phoneme strings -> samples
V = {  # F1, F2, F3
    'ʌ': (640, 1190, 2390), 'm': (280, 1100, 2300), 'ɪ': (400, 1900, 2550), 'ə': (520, 1450, 2450),
    'ɔ': (560, 880, 2500), 'l': (380, 900, 2600), 'a': (760, 1250, 2500), 'r': (420, 1150, 1650), 'n': (300, 1500, 2500),
    'i': (300, 2250, 2950),
}


def say(segs, f0pts, breath=0.15, level=1.0):
    """segs: list of (phone, dur). Vowel-like phones are voiced through formants that glide from phone to phone;
    'k','t','h','s' are noise events."""
    total = sum(d for _, d in segs)
    N_ = int(total * SR)
    t = np.arange(N_) / SR
    f0 = np.interp(t, [p[0] * total for p in f0pts], [p[1] for p in f0pts])
    f0 = f0 * (1 + 0.012 * np.sin(2 * math.pi * 5.2 * t))
    src = glottal(f0)
    noise = rng.normal(0, 1, N_)
    F1 = np.zeros(N_); F2 = np.zeros(N_); F3 = np.zeros(N_); amp = np.zeros(N_); asp = np.zeros(N_); fric = np.zeros(N_)
    pos = 0; last = 'ə'
    for ph, d in segs:
        k = int(d * SR); sl = slice(pos, pos + k)
        if ph in V:
            a = V[last] if last in V else V[ph]; b = V[ph]
            u = np.clip(np.arange(k) / max(1, int(0.06 * SR)), 0, 1)
            F1[sl] = a[0] + (b[0] - a[0]) * u; F2[sl] = a[1] + (b[1] - a[1]) * u; F3[sl] = a[2] + (b[2] - a[2]) * u
            env = np.ones(k)
            if ph in ('m', 'n', 'l'): env *= 0.45
            amp[sl] = env; last = ph
        else:
            vv = V[last]
            F1[sl], F2[sl], F3[sl] = vv
            if ph == 'h': asp[sl] = np.hanning(k) * 0.9
            if ph in ('k', 't'):
                b_ = np.zeros(k); m = min(k, int(0.025 * SR)); b_[:m] = np.exp(-np.arange(m) / (0.006 * SR)); fric[sl] = b_ * 1.6
            if ph == 's': fric[sl] = np.hanning(k) * 0.7
            if ph == '_': pass
        pos += k
    # smooth amplitude
    ker = np.hanning(int(0.03 * SR)); ker /= ker.sum()
    amp = np.convolve(amp, ker, 'same')
    exc = src * amp * (1 - breath) + noise * (amp * breath * 0.35 + asp * 0.5)
    voiced = resonator_bank(exc, [(F1, 90, 1.0), (F2, 110, 2.2), (F3, 160, 1.6)])
    voiced = voiced + 0.6 * np.diff(voiced, prepend=0) * 8
    fr = fft_filter(noise * fric, lo=2500, hi=9000)
    y = voiced * 0.9 + fr * 0.08
    y = y / (np.max(np.abs(y)) + 1e-9)
    return y * level


def place(buf, x, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= buf.shape[1]: return
    x = x[: buf.shape[1] - i0]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i0:i0 + len(x)] += x * gain * l * 1.414
    buf[1, i0:i0 + len(x)] += x * gain * r * 1.414


def env_exp(N_, tau):
    return np.exp(-np.arange(N_) / (tau * SR))


def paw(scrape=False):
    k = int(0.05 * SR)
    click = fft_filter(rng.normal(0, 1, k), lo=1800, hi=6000) * env_exp(k, 0.004)
    pad = np.sin(2 * math.pi * (150 + 20 * rng.random()) * np.arange(k) / SR) * env_exp(k, 0.018)
    x = click * 0.5 + pad * 0.6
    if scrape:
        m = int(0.11 * SR)
        s = fft_filter(rng.normal(0, 1, m), lo=2200, hi=7000) * np.hanning(m) * 0.35
        x = np.concatenate([x, np.zeros(max(0, m - k))]); x[:m] += s
    return x


def footfall(weight=1.0):
    k = int(0.22 * SR)
    t = np.arange(k) / SR
    thump = np.sin(2 * math.pi * 85 * t) * env_exp(k, 0.05)
    body = fft_filter(rng.normal(0, 1, k), lo=120, hi=900) * env_exp(k, 0.03)
    x = (thump * 0.8 + body * 0.5) * weight
    if rng.random() < 0.6:   # board creak under weight
        m = int(0.18 * SR); tt = np.arange(m) / SR
        f = 310 - 60 * tt / 0.18
        stick = (np.sin(2 * math.pi * 38 * tt) > 0.2).astype(float)
        c = np.sin(2 * math.pi * np.cumsum(f) / SR) * stick * np.hanning(m) * 0.12
        x[:m] += fft_filter(c, lo=150, hi=2500)
    return x


def pat():
    k = int(0.06 * SR)
    return fft_filter(rng.normal(0, 1, k), lo=200, hi=2500) * env_exp(k, 0.008)


def knock(f=90, tau=0.08, k_s=0.3):
    k = int(k_s * SR); t = np.arange(k) / SR
    return np.sin(2 * math.pi * f * t) * env_exp(k, tau) + fft_filter(rng.normal(0, 1, k), lo=80, hi=700) * env_exp(k, tau * 0.4) * 0.6


def creak(dur, f0, f1, rate, amp=1.0):
    m = int(dur * SR); tt = np.arange(m) / SR
    f = np.linspace(f0, f1, m) * (1 + 0.03 * rng.normal(0, 1, m).cumsum() / np.sqrt(np.arange(1, m + 1)))
    rr = rate * (1 + 0.3 * np.sin(2 * math.pi * 1.7 * tt))
    stick = (np.sin(2 * math.pi * np.cumsum(rr) / SR) > 0.0).astype(float)
    stick = np.convolve(stick, np.ones(40) / 40, 'same')
    c = np.sign(np.sin(2 * math.pi * np.cumsum(f) / SR)) * stick
    c = fft_filter(c, lo=120, hi=3000)
    return c * np.hanning(m) ** 0.5 * amp


def sigh(dur=0.8, level=1.0):
    m = int(dur * SR); tt = np.arange(m) / SR
    e = np.sin(np.pi * tt / dur) ** 2 * np.exp(-tt / (dur * 0.8))
    return fft_filter(rng.normal(0, 1, m), lo=300, hi=1800) * e * level


def main():
    buf = np.zeros((2, n))
    stems = {k: np.zeros((2, n)) for k in ('voice_call', 'voice_soft', 'contacts', 'room')}
    # ---- room tone: dusk air + crickets; warm room tone as the door opens
    air = fft_filter(rng.normal(0, 1, n), lo=60, hi=900)
    air = air / np.std(air) * db(-52)
    tt = np.arange(n) / SR
    crick = np.zeros(n)
    for c0 in np.arange(0.3, DUR, 0.9):
        if rng.random() < 0.75:
            st = c0 + rng.random() * 0.5
            i0 = int(st * SR); m = int(0.12 * SR)
            if i0 + m >= n: continue
            car = np.sin(2 * math.pi * (4300 + 200 * rng.random()) * np.arange(m) / SR)
            am = (np.sin(2 * math.pi * 30 * np.arange(m) / SR) > 0.3).astype(float) * np.hanning(m)
            crick[i0:i0 + m] += car * am
    crick = crick * db(-50)
    door_t = np.arange(len(DOOR)) / 24
    open_k = np.clip((np.interp(tt, door_t, DOOR) - 11) / 70, 0, 1)
    room = fft_filter(rng.normal(0, 1, n), lo=80, hi=400)
    room = room / np.std(room) * db(-50) * (0.25 + open_k)
    hum = np.sin(2 * math.pi * 120 * tt) * db(-62) * open_k
    for s in (air, crick, room, hum):
        stems['room'][0] += s; stems['room'][1] += s
    # ---- voices from the score's timeline
    calls = [(1.0, 'call1'), (3.4, 'call2')]
    softs = [(7.4, 'allright'), (10.4, 'allright2'), (26.4, 'comein')]
    v = {
        'call1': say([('k', 0.05), ('ʌ', 0.16), ('m', 0.10), ('h', 0.08), ('i', 0.20), ('ə', 0.26)], [(0, 230), (0.35, 250), (0.5, 300), (0.75, 270), (1, 200)], breath=0.08),
        'call2': say([('k', 0.05), ('ʌ', 0.15), ('m', 0.09), ('h', 0.07), ('i', 0.22), ('ə', 0.30)], [(0, 250), (0.35, 270), (0.5, 330), (0.75, 290), (1, 210)], breath=0.08),
        'allright': say([('ɪ', 0.10), ('t', 0.03), ('s', 0.10), ('ɔ', 0.20), ('l', 0.10), ('r', 0.07), ('a', 0.20), ('ɪ', 0.12), ('t', 0.05)], [(0, 175), (0.4, 165), (0.7, 150), (1, 125)], breath=0.45),
        'allright2': say([('ɪ', 0.10), ('t', 0.03), ('s', 0.10), ('ɔ', 0.22), ('l', 0.10), ('r', 0.07), ('a', 0.22), ('ɪ', 0.12), ('t', 0.05)], [(0, 170), (0.4, 160), (0.7, 145), (1, 120)], breath=0.5),
        'comein': say([('k', 0.05), ('ʌ', 0.14), ('m', 0.10), ('ɪ', 0.18), ('n', 0.22)], [(0, 165), (0.5, 175), (1, 130)], breath=0.5),
    }
    CALL_DB, SOFT_DB = -14.0, -30.0
    def rms_norm(x, target_db):
        r = np.sqrt(np.mean(x[np.abs(x) > 0.02 * np.max(np.abs(x))] ** 2))
        return x / r * db(target_db)
    pan_person = -0.55
    for t0, k in calls:
        place(stems['voice_call'], rms_norm(v[k], CALL_DB), t0 + 0.02, 1.0, pan_person)
    for t0, k in softs:
        place(stems['voice_soft'], rms_norm(v[k], SOFT_DB), t0 + 0.05, 1.0, pan_person + 0.1)
    # ---- contacts
    POSEF = POSE['frames']
    def dog_pan(t):
        i = min(767, int(t * 24)); x = POSEF[i]['dog']['R'][0]
        return float(np.clip((x - 2.2) / 2.6, -1, 1))
    for e in EV:
        t = e['t']; who = e['who']; kind = e['kind']; part = e['part']
        if who == 'dog' and kind == 'plant':
            i = min(767, int(t * 24))
            st = SCORE['frames'][i]['dog']['state']
            scr = st == 'retreat' or (3.4 < t < 4.3) or (8.1 < t < 8.9)
            g = db(-31 + 3 * rng.normal()) * (1.3 if scr else 1.0) * (0.7 if st == 'approach' else 1.0)
            place(stems['contacts'], paw(scrape=scr), t, g, dog_pan(t))
        elif who == 'dog' and part == 'dog.belly' and kind == 'bear_weight':
            place(stems['contacts'], knock(70, 0.09, 0.35), t, db(-26), dog_pan(t))
            place(stems['contacts'], sigh(0.9, 1.0), t + 0.35, db(-34), dog_pan(t))
        elif who == 'dog' and part == 'dog.belly' and kind == 'release':
            place(stems['contacts'], fft_filter(rng.normal(0, 1, int(0.25 * SR)), lo=300, hi=3000) * np.hanning(int(0.25 * SR)), t, db(-38), dog_pan(t))
        elif who == 'dog' and part == 'dog.chin' and kind == 'touch':
            place(stems['contacts'], knock(160, 0.02, 0.1), t, db(-40), dog_pan(t))
            if t > 25: place(stems['contacts'], sigh(1.4, 1.0), t + 0.2, db(-31), dog_pan(t))
        elif who == 'dog' and part == 'dog.tail':
            place(stems['contacts'], knock(120, 0.03, 0.12), t, db(-36), dog_pan(t))
        elif who == 'person' and kind == 'plant':
            place(stems['contacts'], footfall(1.0), t, db(-22), pan_person)
        elif who == 'person' and kind == 'touch' and 'thigh' in e.get('why', ''):
            place(stems['contacts'], pat(), t, db(-20), pan_person)
        elif who == 'person' and kind == 'bear_weight':
            place(stems['contacts'], knock(75, 0.07, 0.3), t, db(-24), pan_person)
            place(stems['contacts'], fft_filter(rng.normal(0, 1, int(0.4 * SR)), lo=400, hi=4000) * np.hanning(int(0.4 * SR)), t - 0.2, db(-38), pan_person)
        elif who == 'person' and kind == 'touch':
            place(stems['contacts'], knock(220, 0.012, 0.08), t, db(-30), pan_person)
        elif who == 'person' and kind == 'release' and 'door' in e.get('why', ''):
            pass
        elif who == 'world' and kind == 'resist_then_give':
            # the strain before it gives (stick-slip at low rate), then the swing
            place(stems['contacts'], creak(0.16, 150, 170, 18, 1.0), t - 0.14, db(-30), pan_person)
            place(stems['contacts'], creak(0.75, 200, 330, 26, 1.0), t, db(-27), pan_person)
        elif who == 'world' and kind == 'stop':
            place(stems['contacts'], knock(95, 0.06, 0.3), t, db(-25), pan_person)
    # the door drifting shut after release (a slower creak) and the latch-side settle
    place(stems['contacts'], creak(0.8, 260, 190, 14, 0.8), 4.8, db(-33), pan_person)
    for k in stems:
        buf += stems[k]
    peak = np.max(np.abs(buf))
    if peak > 0.89:
        buf *= 0.89 / peak
        for k in stems: stems[k] *= 0.89 / peak
    # ---- levels (measured on the stems as placed; the critic hears the mix)
    def seg_db(st, t0, t1):
        a = st[:, int(t0 * SR):int(t1 * SR)].mean(0)
        a = a[np.abs(a) > 1e-5]
        return round(20 * math.log10(np.sqrt(np.mean(a ** 2)) + 1e-12), 2)
    lv = dict(call_1=seg_db(stems['voice_call'], 1.0, 1.9), call_2=seg_db(stems['voice_call'], 3.4, 4.3),
              soft_1=seg_db(stems['voice_soft'], 7.45, 8.6), soft_2=seg_db(stems['voice_soft'], 10.45, 11.6),
              soft_come_in=seg_db(stems['voice_soft'], 26.45, 27.2), room_tone_8_14s=seg_db(stems['room'], 12.0, 14.0),
              room_tone_0_1s=seg_db(stems['room'], 0.0, 0.9))
    mix = buf.mean(0)
    def mix_db(t0, t1):
        a = mix[int(t0 * SR):int(t1 * SR)]
        return round(20 * math.log10(np.sqrt(np.mean(a ** 2)) + 1e-12), 2)
    lv['mix_call_1_window'] = mix_db(1.0, 1.9); lv['mix_soft_1_window'] = mix_db(7.45, 8.6); lv['mix_quiet_12_14s'] = mix_db(12.0, 14.0)
    lv['soft_minus_call_dB'] = round(max(lv['soft_1'], lv['soft_2'], lv['soft_come_in']) - min(lv['call_1'], lv['call_2']), 2)
    lv['note'] = 'RMS dBFS over voiced samples of each stem as placed in the mix (after the common peak scaling). Measured numerically; nobody has listened.'
    json.dump(lv, open(os.path.join(DATA, 'sound_levels.json'), 'w'), indent=1)
    print(lv)
    def write(path, x):
        x16 = (np.clip(x, -1, 1) * 32767).astype(np.int16).T.copy()
        with wave.open(path, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x16.tobytes())
    write(os.path.join(CACHE, 'scene.wav'), buf)
    # film: 3 s title with faint air, the scene, 3 s card with the room tone fading
    pre = np.zeros((2, 3 * SR)); post = np.zeros((2, 3 * SR))
    fade_in = np.linspace(0, 1, int(0.8 * SR))
    pre[:, -len(fade_in):] = stems['room'][:, :len(fade_in)] * fade_in
    tail = stems['room'][:, -3 * SR:] * np.linspace(1, 0, 3 * SR)
    post += tail
    film = np.concatenate([pre, buf, post], 1)
    write(os.path.join(CACHE, 'film.wav'), film)


if __name__ == '__main__':
    main()
