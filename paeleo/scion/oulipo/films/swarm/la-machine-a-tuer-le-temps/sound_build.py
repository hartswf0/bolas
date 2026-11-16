"""U4 sound-editor: build the separately versioned stems T0-T4 for
La Machine a tuer le temps (plan section 9).

    python3 films/swarm/la-machine-a-tuer-le-temps/sound_build.py

Reads:  notebook/events.json (animator event stream, film frames, 24 fps)
        edit-recipes.json (A1 / B1 event starts, cut-relative frames)
        sound-editor/*.wav (foraged archive audio, decoded with ffmpeg)
Writes: sources/la-machine-a-tuer-le-temps/sound/*.wav  (44.1 kHz, 16-bit stereo)
        swarm/la-machine-a-tuer-le-temps/sound-cues.json (cue list; merged into sound-edit.json)

Deterministic: fixed seeds; every synthesised element is made here with numpy
through films/kit.py Mix (not edited). Foraged audio is only trimmed, looped
with crossfades, filtered and gained.
"""
import sys, json, math, wave, hashlib
from pathlib import Path
import numpy as np

FILMS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(FILMS))
import kit  # noqa: E402

SLUG = 'la-machine-a-tuer-le-temps'
SRC = FILMS / 'sources' / SLUG
OUT = SRC / 'sound'
ED = SRC / 'sound-editor'
SW = FILMS / 'swarm' / SLUG
OUT.mkdir(parents=True, exist_ok=True)
R = kit.RATE
FPS = 24
VERSION = 'v2'
import sound_crowd as C  # noqa: E402  (repair round 2: event-built concourse, gentle filters)

EVS = json.load(open(SRC / 'notebook' / 'events.json'))
TL = EVS['timeline']
EVENTS = EVS['events']
REC = json.load(open(SW / 'edit-recipes.json'))
POOL = REC['base_pool_hash']
EDITS = {e['edit_id']: e for e in REC['edits']}
A1, B1 = EDITS['A1'], EDITS['B1']
A_START = [c['start_frame'] for c in A1['cut_points']]
B_START = [c['start_frame'] for c in B1['cut_points']]
A_LEN, B_LEN = A1['total_frames'], B1['total_frames']
TAIL = 18                         # S4 / S8 pull-out: the bed falls under it
PRE = TL['S2'][1] + 1 - TL['S1'][0]   # S1 + S2 (90 f): bed fades in and rises
FILM_N = TL['total']

CUES = []


def sec(f):
    return f / FPS


def cue(track, f, what, sync_dep, **kw):
    d = dict(track=track, t_frame=int(f), t_s=round(sec(f), 4), cue=what, sync_dep=sync_dep)
    d.update(kw)
    CUES.append(d)


def load(p, rate=R):
    with wave.open(str(p)) as w:
        sr = w.getframerate(); ch = w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    if sr != rate:
        x = np.arange(int(len(a) * rate / sr)) * sr / rate
        a = np.interp(x, np.arange(len(a)), a)
    return a


def save(name, L, Rch=None, peak_db=-1.0):
    Rch = L if Rch is None else Rch
    st = np.stack([L, Rch], 1)
    st = np.clip(st, -0.98, 0.98)
    p = OUT / name
    with wave.open(str(p), 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return p


def loop_to(x, n, rs, xf=0.25):
    """Loop a foraged segment to n samples with random-offset equal-power crossfades."""
    k = int(xf * R); out = np.zeros(n); pos = 0
    while pos < n:
        s = rs.randint(0, max(1, len(x) - k * 3))
        seg = x[s:].copy()
        if len(seg) < 2 * k:
            continue
        fade = np.sin(np.linspace(0, math.pi / 2, k))
        seg[:k] *= fade; seg[-k:] *= fade[::-1]
        m = min(len(seg), n - pos)
        out[pos:pos + m] += seg[:m]
        pos += len(seg) - k
    return out


def fft_conv(x, ir):
    n = len(x) + len(ir) - 1
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]


def hall_ir(mix, rt=2.4, lp=3500, seed=0):
    """Repair round 2: two-band noise IR with smooth filters (no brick-wall shelf)."""
    return C.hall(rt, seed, bright=lp)


def env_lin(n, pts):
    """piecewise-linear gain from [(sample, gain)...]"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return np.interp(np.arange(n), xs, ys)


def db(x):
    return 10 ** (x / 20)


# --------------------------------------------------------------- sources
def tick_sig(mix, strong=1.0, tock=False, seed=0):
    """Wall-clock escapement: sharp pallet click + case resonance + secondary drop."""
    rs = np.random.RandomState(seed)
    n = int(0.09 * R); t = np.arange(n) / R
    c = rs.normal(0, 1, n) * np.exp(-t / 0.0018)
    c = C.gentle(c, 1800, 9000)
    f0 = 1180 if not tock else 1040
    body = (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.31 * t)) * np.exp(-t / 0.018)
    d = int(0.011 * R)
    sec2 = np.zeros(n); sec2[d:] = c[:n - d] * 0.35
    s = (c * 1.0 + body * 0.25 + sec2) * strong
    return s / (np.abs(s).max() + 1e-9) * strong


def murmur(mix, seconds, seed=11):
    """HANDMADE concourse murmur (used only if the foraged Commons station file is absent):
    40 unintelligible 'voices' = noise through two moving formant bands with syllabic
    3-6 Hz amplitude, plus a pink floor, then a 2.6 s hall."""
    rs = np.random.RandomState(seed)
    n = int(seconds * R); t = np.arange(n) / R
    out = np.zeros(n)
    for v in range(40):
        base = mix.noise(seconds)
        f1 = rs.uniform(350, 800); f2 = rs.uniform(1100, 2400)
        x = 0.7 * C.gentle(base, f1 * 0.8, f1 * 1.25) + 0.35 * C.gentle(base, f2 * 0.85, f2 * 1.2)
        syl = rs.uniform(3.0, 6.0)
        am = np.clip(np.sin(2 * np.pi * syl * t + rs.uniform(0, 6)) + 0.3 * np.sin(2 * np.pi * syl * 1.7 * t), 0, None) ** 1.5
        talk = (np.sin(2 * np.pi * rs.uniform(0.05, 0.2) * t + rs.uniform(0, 6)) > rs.uniform(-0.3, 0.4)).astype(float)
        talk = np.convolve(talk, np.ones(int(0.2 * R)) / int(0.2 * R), 'same')
        out += x * am * talk * rs.uniform(0.4, 1.0)
    out = out / (np.abs(out).max() + 1e-9)
    floor = C.gentle(mix.noise(seconds, 'pink'), None, 2500) * 0.25
    dry = out + floor
    wet = fft_conv(dry, hall_ir(mix, 2.6, 3000, seed + 1))
    y = 0.25 * dry + wet / (np.abs(wet).max() + 1e-9)
    return C.gentle(y, None, 4500) / (np.abs(y).max() + 1e-9)


def trains(mix, seconds, passes, seed=21):
    """HANDMADE distant trains: low rumble swells with rail-joint clacks, through the hall."""
    rs = np.random.RandomState(seed)
    n = int(seconds * R); out = np.zeros(n)
    for (t0, dur) in passes:
        m = int(dur * R); tt = np.arange(m) / R
        rum = C.gentle(mix.noise(dur, 'brown'), 25, 220)
        sw = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
        x = rum * sw
        k = 0.0
        while k < dur:
            for dd in (0.0, 0.11):
                i = int((k + dd) * R)
                if i + 3000 < m:
                    tk = np.arange(3000) / R
                    x[i:i + 3000] += 0.5 * sw[i] * np.sin(2 * np.pi * 90 * tk) * np.exp(-tk * 35)
            k += 0.95 + rs.uniform(-0.04, 0.04)
        i0 = int(t0 * R)
        if i0 < n:
            out[i0:i0 + m] += x[:n - i0]
    wet = fft_conv(out, hall_ir(mix, 3.0, 1200, seed + 2))
    return 0.3 * out + wet


# -------------------------------------------------------------- the stems
def build():
    mix = kit.Mix(1, seed=3)
    rs = np.random.RandomState(7)
    sources = {}

    # ---------------- T0 room (full film length, both exports)
    n_film = int(FILM_N / FPS * R)
    room_src = load(ED / 'wreckless1935_roomtone_1.00-3.45s.wav')
    room_src = C.gentle(room_src, 60, 7000)
    room = loop_to(room_src, n_film, rs)
    room = room / (np.sqrt((room ** 2).mean()) + 1e-9) * db(-46)
    air0 = C.gentle(np.random.RandomState(4).normal(0, 1, n_film), 60, 3000, 1) * 0.0012   # faint air, no mains hum
    T0L = room + air0; T0R = np.roll(room, int(0.013 * R)) + np.roll(air0, 977)
    def fr(f):
        return int(sec(f) * R)
    # Repair round 1: the room under cut B's first 480 frames is the same samples
    # as under cut A (copied, 20 ms crossfades outside the window), so the
    # shared-bed export carries sample-identical sound from each cut's frame 0.
    a0, b0, wn, xf = fr(TL['S3'][0]), fr(TL['S7'][0]), fr(A_LEN), int(0.02 * R)
    for X in (T0L, T0R):
        seg = X[a0 - xf:a0 + wn + xf].copy()
        w = np.ones(len(seg)); w[:xf] = np.linspace(0, 1, xf); w[-xf:] = np.linspace(1, 0, xf)
        X[b0 - xf:b0 + wn + xf] = X[b0 - xf:b0 + wn + xf] * (1 - w) + seg * w
    # dip the room under the full-frame cuts (the cut slots carry their own world);
    # the A dip now rises under S4 so the dip is the same over A's and B's frames 0..479
    g = env_lin(n_film, [(0, 0), (fr(12), 1), (fr(TL['S3'][0]), 1), (fr(TL['S3'][0] + 12), 0.25),
                         (fr(TL['S3'][1] + 1), 0.25), (fr(TL['S4'][0] + 8), 1),
                         (fr(TL['S7'][0]), 1), (fr(TL['S7'][0] + 12), 0.25), (fr(TL['S7'][1] - 6), 0.25),
                         (fr(TL['S8'][0]), 1), (fr(FILM_N - 24) + int(0.09 * R), 1), (fr(FILM_N - 24) + int(0.5 * R), 0),
                         (n_film, 0)])
    T0L *= g; T0R *= g
    # the room tone ends on one clock tick (S10 last held second)
    f_tick = FILM_N - 24
    tk = tick_sig(mix, 0.32, seed=99); i = fr(f_tick)
    T0L[i:i + len(tk)] += tk; T0R[i:i + len(tk)] += tk * 0.9
    cue('T0', 0, 'room tone in (foraged 1935 interior air, looped)', {'segment': 'S0', 'frames': TL['S0']})
    cue('T0', TL['S3'][0], 'room dips -12 dB under cut A', {'segment': 'S3'})
    cue('T0', TL['S7'][0], 'room dips -12 dB under cut B', {'segment': 'S7'})
    cue('T0', f_tick, 'single clock tick; room tone ends with it', {'stream': 'notebook/events.json', 'index': len(EVENTS) - 1,
        'ev': EVENTS[-1]['ev'], 'note': 'last held second of S10 (after the tape event)'})
    save(f'T0_room_{VERSION}.wav', T0L, T0R)

    # ---------------- T1 shared bed: generated on [-PRE, B_LEN+TAIL] frames
    pre_s = sec(PRE); body_s = sec(B_LEN + TAIL); tot = pre_s + body_s
    nb = int(tot * R)
    mb = kit.Mix(tot, seed=12)
    tamp = ED / 'dl' / 'tampere_tunnel.wav'
    if tamp.exists():
        st = load(tamp)
        st = C.gentle(st, 40, 9000)
        mur = loop_to(st, nb, np.random.RandomState(5), xf=0.6); murR = np.roll(mur, int(0.021 * R))
        sources['murmur'] = 'foraged: Commons WWS TheStationTunnelOfTheTampereStation.ogg'
    else:
        mur, murR, crowd_log = C.concourse(tot, seed=11)
        sources['murmur'] = ('handmade synthesis v2 (Commons file not obtained): event-built concourse -- '
                             'talkers on a crowd swell, passing walkers, 2 PA fragments, trolley, case, steam; smooth filters')
        sources['concourse_events'] = crowd_log
    g_ = np.sqrt(((mur ** 2 + murR ** 2) / 2).mean()) + 1e-9
    mur = mur / g_; murR = murR / g_
    tr = C.trains(np.random.RandomState(21), tot, [(pre_s + 1.5, 9.0), (pre_s + 13.0, 8.0)])
    tr = tr / (np.sqrt((tr ** 2).mean()) + 1e-9)
    ticks = np.zeros(nb)
    tick_times = []
    k = 0
    t = pre_s - math.floor(pre_s)   # ticks on whole seconds of cut time: t_cut = 0,1,2...
    while t < tot:
        s = tick_sig(mb, 1.0, tock=(k % 2 == 1), seed=k % 4)
        i = int(t * R)
        ticks[i:i + len(s)] += s[:nb - i]
        tick_times.append(round(t - pre_s, 3)); t += 1.0; k += 1
    tick_dry = ticks.copy()
    ticks = ticks + 0.12 * fft_conv(ticks, hall_ir(mb, 0.5, 5000, 3))
    bedL = db(-24) * mur + db(-30) * tr + db(-25) * ticks
    bedR = db(-24) * murR + db(-30) * np.roll(tr, int(0.008 * R)) + db(-26) * ticks
    i0 = int(pre_s * R)
    # preroll: faint under S1 then rising under S2
    preg = env_lin(i0, [(0, 0), (int(sec(72) * R * 0.5), db(-18)), (int(sec(72) * R), db(-14)), (i0, 1.0)])
    save(f'T1_bed_preroll_{VERSION}.wav', bedL[:i0] * preg, bedR[:i0] * preg)
    T1L, T1R = bedL[i0:], bedR[i0:]
    n1 = len(T1L)
    gfall = env_lin(n1, [(0, 1), (int(sec(B_LEN) * R), 1), (n1, db(-30))])
    save(f'T1_bed_{VERSION}.wav', T1L * gfall, T1R * gfall)
    # cut-A tail variant: identical frames 0..479, then the S4 fall over 18 f
    ga = env_lin(n1, [(0, 1), (int(sec(A_LEN) * R), 1), (int(sec(A_LEN + TAIL) * R), db(-30)), (n1, 0)])
    nA = int(sec(A_LEN + TAIL) * R)
    save(f'T1_bed_cutA-slot_{VERSION}.wav', (T1L * ga)[:nA], (T1R * ga)[:nA])
    cue('T1', 0, 'shared bed starts on cut frame 0 (same offset in A and B): murmur + distant trains + 1 Hz tick on whole seconds',
        {'edit_id': 'A1|B1', 'event': 0}, ticks_at_s=tick_times[:6] + ['...'])
    cue('T1', -PRE, 'preroll: bed fades in faint under S1, rises under the S2 push', {'segment': 'S1-S2', 'frames': [TL['S1'][0], TL['S2'][1]]})
    cue('T1', A_LEN, 'cut A slot: bed falls to room tone under S4 (18 f)', {'edit_id': 'A1', 'event': 7, 'at': 'out'})
    cue('T1', B_LEN, 'cut B slot: bed falls to room tone under S8 (18 f)', {'edit_id': 'B1', 'event': 7, 'at': 'out'})

    # common bed components for mixes (cut-relative, from frame 0)
    cutn = int(sec(B_LEN + TAIL) * R)
    MUR = mur[i0:i0 + cutn]; MURR = murR[i0:i0 + cutn]; TR = tr[i0:i0 + cutn]; TK = ticks[i0:i0 + cutn]; TKD = tick_dry[i0:i0 + cutn]
    ir_hall = hall_ir(mb, 2.8, 3200, 41)

    # ---------------- T3 mix A
    nA = int(sec(A_LEN + TAIL) * R)
    mA = kit.Mix(sec(A_LEN + TAIL), seed=31)
    warm = C.gentle(MUR[:nA], None, 2600, 1) * 1.15; warmR = C.gentle(MURR[:nA], None, 2600, 1) * 1.15
    AL = db(-23) * warm + db(-30) * TR[:nA] + db(-25) * TK[:nA]
    AR = db(-23) * warmR + db(-30) * TR[:nA] + db(-26) * TK[:nA]
    # mail-room bustle under 02 (A event 1): parcels set down, paper, a string pulled
    e0, e1 = A_START[1], A_START[2]
    bust = kit.Mix(sec(A_LEN + TAIL), seed=33)
    tt = sec(e0) + 0.15
    while tt < sec(e1) - 0.1:
        r = bust.rs.random()
        if r < 0.45:
            bust.thud(tt, freq=bust.rs.uniform(110, 180), gain=0.09, seconds=0.18, pan=bust.rs.uniform(-0.6, 0.6))
            bust.click(tt + 0.01, gain=0.08, bright=2200, seconds=0.04)
        else:
            d = bust.rs.uniform(0.15, 0.4); x = bust.band(bust.noise(d), 600, 5000)
            x *= np.sin(np.linspace(0, math.pi, len(x))) ** 0.8 * (0.6 + 0.4 * (bust.rs.random(len(x)) > 0.4))
            bust.add(x, tt, gain=0.05, pan=bust.rs.uniform(-0.6, 0.6))
        tt += bust.rs.uniform(0.18, 0.45)
    bwL = fft_conv(bust.L, ir_hall) * 0.35 + bust.L; bwR = fft_conv(bust.R, ir_hall) * 0.35 + bust.R
    gb = env_lin(nA, [(0, 0), (int(sec(e0) * R), 0), (int(sec(e0 + 4) * R), 1), (int(sec(e1 - 3) * R), 1), (int(sec(e1 + 6) * R), 0), (nA, 0)])
    AL += db(-6) * bwL[:nA] * gb; AR += db(-6) * bwR[:nA] * gb
    cue('T3', e0, 'mail-room bustle under 02 (parcels, paper), fades by 6 f into 03', {'edit_id': 'A1', 'event': 1})
    # door latch on the 04 cut (A event 3), on the cut
    lat = latch(mA, seed=5)
    i = int(sec(A_START[3]) * R)
    AL[i:i + len(lat)] += lat[:nA - i] * db(-9); AR[i:i + len(lat)] += lat[:nA - i] * db(-10)
    cue('T3', A_START[3], 'door latch on the 04 cut (on the frame)', {'edit_id': 'A1', 'event': 3}, offset_frames=0)
    # whistle under 07 (A event 6): foraged Valley Town (1940) factory whistle, distant
    wh = load(ED / 'valleytown1940_whistle_a11ba534.wav')
    wh = C.gentle(wh, 70, 2200)
    wh = wh / (np.sqrt((wh ** 2).mean()) + 1e-9)
    wh_len = min(len(wh), int(sec(A_START[7] - A_START[6] + 12) * R))
    wh = wh[:wh_len] * env_lin(wh_len, [(0, 0), (int(0.35 * R), 1), (wh_len - int(0.6 * R), 1), (wh_len, 0)])
    whw = fft_conv(np.pad(wh, (0, int(2.5 * R))), hall_ir(mA, 2.5, 1800, 51))
    whd = np.pad(wh, (0, int(2.5 * R))) * 0.25 + whw
    i = int(sec(A_START[6] + 6) * R)
    m = min(len(whd), nA - i)
    AL[i:i + m] += whd[:m] * db(-27); AR[i:i + m] += np.roll(whd, int(0.01 * R))[:m] * db(-27)
    cue('T3', A_START[6] + 6, 'distant factory/rail whistle under 07 (foraged, Valley Town 1940), hall-reverbed', {'edit_id': 'A1', 'event': 6})
    cue('T3', 0, 'bed at normal level, tick steady at 1 Hz, murmur warmed (low-pass 2.6 kHz)', {'edit_id': 'A1', 'event': 0})
    gA = env_lin(nA, [(0, 1), (int(sec(A_LEN) * R), 1), (nA, db(-30))])
    save(f'T3_mixA_{VERSION}.wav', AL * gA, AR * gA)

    # ---------------- T4 mix B (and branch B4-delayed-cue)
    for variant, latch_f in (('B1', B_START[1] - 6), ('B4-delayed-cue', B_START[1] + 12)):
        nB = int(sec(B_LEN + TAIL) * R)
        mBm = kit.Mix(sec(B_LEN + TAIL), seed=61)
        def S(f):
            return int(sec(f) * R)
        duck = db(-9)
        # bed (murmur + trains), ducked -9 dB; declared silence 60-120; gone under 01; fades under 08
        gbed = env_lin(nB, [(0, duck), (S(36), duck), (S(60), 0.0), (S(120), 0.0), (S(120) + int(0.03 * R), duck),
                            (S(B_START[5]) - int(0.02 * R), duck), (S(B_START[5]), 0.0), (S(B_START[6]) - 1, 0.0),
                            (S(B_START[6]), duck), (S(B_START[7]), duck), (S(B_LEN - 12), 0.0), (nB, 0.0)])
        BL = (db(-23) * MUR[:nB] + db(-30) * TR[:nB]) * gbed
        BR = (db(-23) * MURR[:nB] + db(-30) * TR[:nB]) * gbed
        # tick: slows over 0-60 (intervals 1.0 -> 1.9 s, weakening), silent 60-240, hard on 06, alone on 01
        tks = []
        t = 0.0; iv = 1.0
        while t < sec(60):
            tks.append((t, 0.9 - 0.5 * t / sec(60))); t += iv; iv *= 1.28
        t = sec(B_START[3])
        while t < sec(B_START[5]) - 0.3:
            strong = 1.35 if t < sec(B_START[3]) + 0.05 else 1.0
            tks.append((t, strong)); t += 1.0
        t = sec(B_START[5])          # re-phased onto the 01 cut: the clock is the only sound
        while t < sec(B_START[6]):
            tks.append((t, 1.15)); t += 1.0
        tkL = np.zeros(nB)
        for j, (t, s_) in enumerate(tks):
            s = tick_sig(mBm, 1.0, tock=(j % 2 == 1), seed=j % 4) * s_
            i = int(t * R); tkL[i:i + len(s)] += s[:nB - i]
        tkW = tkL + 0.12 * fft_conv(tkL, hall_ir(mBm, 0.5, 5000, 3))
        BL += db(-22) * tkW; BR += db(-23) * tkW
        # declared silence: only the faintest air (-60 dBFS), no tick, no bed
        air = C.gentle(mBm.noise(sec(B_LEN + TAIL), 'pink'), None, 3000)
        air = air / (np.sqrt((air ** 2).mean()) + 1e-12) * db(-62)
        BL += air; BR += np.roll(air, 977)
        # pre-lapped door latch
        lat = latch(mBm, seed=5)
        i = S(latch_f)
        BL[i:i + len(lat)] += lat[:nB - i] * db(-7); BR[i:i + len(lat)] += lat[:nB - i] * db(-8)
        # Repair round 2: a second decisive cue into 02 -- close footsteps pre-lap the 04->02 cut by
        # 14 f and arrive with her; the parcel is set down hard just before 06 and a paper slip is
        # drawn across the counter as 06 (the reservation slips) opens: parcel exchanged for paper.
        rsx = np.random.RandomState(73)
        app = C.steps_near(rsx, 5, pace=0.46, gain=1.0, rise=True)
        i = S(B_START[2] - 14); m = min(len(app), nB - i)
        appw = app + 0.35 * fft_conv(app, hall_ir(mBm, 1.6, 3000, 74))
        BL[i:i + m] += appw[:m] * db(-17); BR[i:i + m] += appw[:m] * db(-19)
        last_app = sec(B_START[2] - 14) + 4 * 0.46
        th = C.thump(rsx); i = S(B_START[3] - 5); m = min(len(th), nB - i)
        BL[i:i + m] += th[:m] * db(-15); BR[i:i + m] += th[:m] * db(-16)
        sl = C.gentle(rsx.normal(0, 1, int(0.38 * R)), 1500, 7000, 1) * np.sin(np.linspace(0, math.pi, int(0.38 * R))) ** 0.7
        sl = sl / (np.abs(sl).max() + 1e-9)
        i = S(B_START[3] - 2); m = min(len(sl), nB - i)
        BL[i:i + m] += sl[:m] * db(-21); BR[i:i + m] += sl[:m] * db(-20)
        # footsteps pre-lapping 07, walking away into the hall; reverb tail under 08 fades to nothing
        fs = kit.Mix(sec(B_LEN + TAIL), seed=71)
        t = sec(B_START[6] - 12); k = 0
        while t < sec(B_START[7] + 6):
            gk = 0.25 * (1.0 - 0.55 * (t - sec(B_START[6] - 12)) / (sec(B_START[7] + 6) - sec(B_START[6] - 12)))
            fs.step(t + fs.rs.uniform(-0.012, 0.012), gain=gk * (0.85 if k % 2 else 1.0), pan=-0.1 + 0.5 * (t - sec(B_START[6])) / 3.5, surface='stone')
            t += 0.52; k += 1
        last_step = t - 0.52
        ir_long = hall_ir(mBm, 3.6, 2800, 81)
        wL = fft_conv(fs.L, ir_long); wR = fft_conv(fs.R, np.roll(ir_long, 300))
        gt = env_lin(nB, [(0, 1), (S(B_START[7]), 1), (S(B_LEN - 6), 0.0), (nB, 0.0)])
        BL += (fs.L * 0.8 + wL * 0.9) * gt; BR += (fs.R * 0.8 + wR * 0.9) * gt
        BL[S(B_LEN - 6):] = 0.0; BR[S(B_LEN - 6):] = 0.0
        name = f'T4_mixB_{VERSION}.wav' if variant == 'B1' else f'T4_mixB_B4-delayed-cue_{VERSION}.wav'
        save(name, BL, BR)
        trk = 'T4' if variant == 'B1' else 'T4-B4'
        cue(trk, 0, 'bed ducked -9 dB (murmur + trains); tick slowing: %d ticks, intervals x1.28 each, weakening' % sum(1 for x in tks if x[0] < sec(60)),
            {'edit_id': 'B1', 'event': 0}, tick_times_s=[round(x[0], 3) for x in tks if x[0] < sec(60)])
        cue(trk, 60, 'DECLARED SILENCE 2.5 s over the 05 stare (frames 60-119): no tick, no bed, air only at -62 dBFS',
            {'edit_id': 'B1', 'event': 0}, duration_frames=60, declared_silence=True)
        cue(trk, latch_f, 'door latch ' + ('pre-lapped 6 f before the 05->04 cut' if variant == 'B1' else 'delayed 12 f into 04 (branch B4)'),
            {'edit_id': 'B1', 'event': 1}, offset_frames=latch_f - B_START[1])
        cue(trk, 120, 'bed returns ducked on 04 (no tick yet)', {'edit_id': 'B1', 'event': 1})
        cue(trk, B_START[2] - 14, 'close footsteps pre-lap the 04->02 cut by 14 f and arrive with her (5 steps, 0.46 s, rising)',
            {'edit_id': 'B1', 'event': 2}, offset_frames=-14, last_step_s=round(last_app, 3))
        cue(trk, B_START[3] - 5, 'the parcel set down hard on a counter, 5 f before 06', {'edit_id': 'B1', 'event': 3}, offset_frames=-5)
        cue(trk, B_START[3] - 2, 'a paper slip drawn across the counter, pre-lapping 06 by 2 f (parcel exchanged for paper)',
            {'edit_id': 'B1', 'event': 3}, offset_frames=-2)

        cue(trk, B_START[3], 'tick returns hard on 06 (+3 dB first tick), 1 Hz', {'edit_id': 'B1', 'event': 3})
        cue(trk, B_START[4], 'tick continues under 03 (someone is timing it)', {'edit_id': 'B1', 'event': 4})
        cue(trk, B_START[5], 'tick alone on 01: bed muted, only the tick', {'edit_id': 'B1', 'event': 5}, until_frame=B_START[6] - 1)
        cue(trk, B_START[6] - 12, 'footsteps pre-lap 07 by 12 f, receding on stone, 0.52 s pace', {'edit_id': 'B1', 'event': 6}, offset_frames=-12)
        cue(trk, B_START[6], 'tick stops; bed back ducked under 07', {'edit_id': 'B1', 'event': 6})
        cue(trk, B_START[7], 'hall reverb tail (RT 3.6 s) of the last steps under 08, fading to nothing by frame %d; bed fades out too' % (B_LEN - 6),
            {'edit_id': 'B1', 'event': 7}, last_step_s=round(last_step, 3))

    # ---------------- T2 notebook foley (full film length), cued to the animator's event stream
    mf = kit.Mix(FILM_N / FPS, seed=91)
    for idx, e in enumerate(EVENTS):
        f = e['f']; t = sec(f); kind = e['ev']; d = sec(e.get('frames', 4))
        dep = {'stream': 'notebook/events.json', 'index': idx, 'ev': kind, 'f': f}
        if kind == 'cover_flip':
            paper(mf, t, d, 300, 3500, 0.10, crackle=0.2)
            mf.thud(t + d * 0.92, freq=120, gain=0.12, seconds=0.15); mf.click(t + d * 0.92, gain=0.10, bright=2500, seconds=0.04)
            cue('T2', f, 'cover flap around the coil, board lands', dep)
        elif kind == 'turn':
            paper(mf, t, d, 700, 7000, 0.07, crackle=0.5)
            mf.click(t + d * 0.95, gain=0.04, bright=1800, seconds=0.03)
            cue('T2', f, 'page turn: rustle + soft land', dep)
        elif kind == 'lift':
            paper(mf, t, sec(3), 900, 4500, 0.035, crackle=0.1)
            cue('T2', f, 'slip lifted: peel/air', dep)
        elif kind == 'travel':
            paper(mf, t, d, 1200, 6500, 0.045, crackle=0.05, shape=1.2)
            cue('T2', f, 'slip slides over paper', dep)
        elif kind == 'setdown':
            mf.click(t, gain=0.17, bright=2600, seconds=0.04); mf.thud(t, freq=160, gain=0.045, seconds=0.08)
            cue('T2', f, 'set-down tap', dep)
        elif kind == 'settle':
            mf.click(t + sec(3), gain=0.035, bright=2000, seconds=0.02)
            cue('T2', f + 3, 'spring overshoot return: faint second contact', dep)
        elif kind in ('strike', 'write', 'line'):
            nstroke = 1 if kind != 'write' else (3 if e.get('mark') in ('4', '5', 'B') else 2)
            pencil(mf, t, d, nstroke, gain=0.06 if kind != 'line' else 0.05)
            cue('T2', f, 'red pencil %s (%d stroke%s)' % (kind, nstroke, 's' if nstroke > 1 else ''), dep)
        elif kind == 'slide':
            paper(mf, t, d, 500, 5000, 0.09, crackle=0.08, shape=0.9)
            mf.click(t + d, gain=0.05, bright=1500, seconds=0.04)
            cue('T2', f, 'loose sheet slides in over the spread, settles', dep)
        elif kind == 'tape':
            paper(mf, t, sec(4), 400, 3000, 0.04, crackle=0.6)
            mf.thud(t + sec(4), freq=200, gain=0.03, seconds=0.06)
            pencil(mf, t + sec(5), sec(5), 1, gain=0.025)  # thumb rubbing the tape down
            cue('T2', f, 'typed tape laid and pressed down', dep)
        # push / pull are camera moves: no foley (the bed rises / falls instead)
    save(f'T2_foley_{VERSION}.wav', mf.L, mf.R)
    return sources


def latch(mix, seed=0):
    """Door latch: bolt click, strike-plate clack, door wood body, small hall."""
    rs = np.random.RandomState(seed)
    n = int(0.6 * R); t = np.arange(n) / R
    x = np.zeros(n)
    for (dt, g, lo, hi, tau) in ((0.0, 0.7, 1500, 8000, 0.003), (0.045, 1.0, 900, 6000, 0.005), (0.06, 0.4, 300, 2500, 0.012)):
        i = int(dt * R); m = n - i
        c = rs.normal(0, 1, m) * np.exp(-np.arange(m) / R / tau)
        x[i:] += C.gentle(c, lo, hi) * g
    body = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.06) * 0.5
    i = int(0.05 * R); x[i:] += body[:n - i]
    x = x + 0.3 * fft_conv(x, hall_ir(mix, 1.2, 4000, seed + 7))
    return x / (np.abs(x).max() + 1e-9)


def paper(mix, at, dur, lo, hi, gain, crackle=0.2, shape=0.8):
    n = max(int(dur * mix.rate), 64)
    x = C.gentle(mix.noise(n / mix.rate + 0.02), lo, hi)[:n]
    e = np.sin(np.linspace(0, math.pi, n)) ** shape
    cr = (mix.rs.random(n) < crackle * 0.004).astype(float)
    cr = np.convolve(cr, np.exp(-np.arange(200) / 25.0), 'same')
    mix.add(x * e * (1 + 3 * cr), at, gain, pan=mix.rs.uniform(-0.2, 0.2))


def pencil(mix, at, dur, nstroke, gain=0.06):
    """Graphite on paper: granular band noise, 2-9 kHz, per stroke with lifts between."""
    per = dur / nstroke
    for s in range(nstroke):
        n = int(per * 0.8 * mix.rate)
        if n < 32:
            continue
        x = C.gentle(mix.noise(n / mix.rate + 0.02), 2000, 9000)[:n]
        grain = C.gentle(mix.rs.normal(0, 1, n), None, 180); grain = 0.5 + 0.5 * np.abs(grain) / (np.abs(grain).max() + 1e-9)
        e = mix.env(n, 0.006, 0.02, 0.85, 0.03)
        mix.add(x * e * grain, at + s * per, gain, pan=0.1)


def compose_previews():
    """Convenience full-film previews for the editor (not stems): T0 + T2 + cut slots."""
    def ld(n):
        with wave.open(str(OUT / n)) as w:
            return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
    n = int(FILM_N / FPS * R)
    base = ld(f'T0_room_{VERSION}.wav')[:n] + ld(f'T2_foley_{VERSION}.wav')[:n]
    pre = ld(f'T1_bed_preroll_{VERSION}.wav')
    rise = pre[-int(sec(18) * R):]
    def put(buf, x, f):
        i = int(sec(f) * R); m = min(len(x), n - i); buf[i:i + m] += x[:m]
    out = {}
    for name, a_slot, b_slot in (('screening1-sharedbed', f'T1_bed_cutA-slot_{VERSION}.wav', f'T1_bed_{VERSION}.wav'),
                                 ('final', f'T3_mixA_{VERSION}.wav', f'T4_mixB_{VERSION}.wav')):
        buf = base.copy()
        put(buf, pre, TL['S1'][0]); put(buf, ld(a_slot), TL['S3'][0])
        put(buf, rise, TL['S6'][0]); put(buf, ld(b_slot), TL['S7'][0])
        p = save(f'preview_{name}_{VERSION}.wav', buf[:, 0], buf[:, 1])
        out[name] = str(p)
    return out


if __name__ == '__main__':
    src = build()
    src['previews'] = compose_previews()
    files = sorted(OUT.glob('*.wav'))
    info = []
    for p in files:
        a = load(p)
        info.append(dict(file=str(p.relative_to(FILMS.parent.parent.parent.parent)) if False else str(p),
                         seconds=round(len(a) / R, 4), frames_24=round(len(a) / R * FPS, 2),
                         rms_dbfs=round(20 * math.log10(np.sqrt((a ** 2).mean()) + 1e-12), 1),
                         peak_dbfs=round(20 * math.log10(np.abs(a).max() + 1e-12), 1),
                         sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    json.dump(dict(sources=src, cues=CUES, files=info, timeline=TL, pool_hash=POOL), open(SW / 'sound-cues.json', 'w'), indent=1, ensure_ascii=False)
    for i in info:
        print(i)
    print(len(CUES), 'cues;', src)
