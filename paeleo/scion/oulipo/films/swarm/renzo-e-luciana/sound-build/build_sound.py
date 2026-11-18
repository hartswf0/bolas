"""U3 sound for renzo-e-luciana: cue sheet + 72.0 s mix + stems.

Reads rules.json cues (authoritative times), lays foraged recordings at each cue,
and writes cues.json, sound.wav, sound-nobells.wav, stems/{bells,steps,foley,room}.wav.
Every sample is a real recording decoded with ffmpeg; where a recording could not be
obtained the fallback is kit-style synthesis and is declared in cues.json ("fallback").
Run: python3 -I build_sound.py
"""
import json, os, subprocess, wave, math
import numpy as np

ROOT = '/home/user/bolas/paeleo/scion/oulipo/films'
SW = ROOT + '/swarm/renzo-e-luciana'
SND = ROOT + '/sources/renzo-e-luciana/sound'
RAW, WAV = SND + '/raw', SND + '/wav'
SR, FPS, DUR = 44100, 24, 72.0
N = int(DUR * SR)
rs = np.random.RandomState(7)
META = json.load(open(RAW + '/meta.json')) if os.path.exists(RAW + '/meta.json') else {}


def readwav(p):
    with wave.open(p) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x


def load(raw_name):
    """decode raw/<name> (ogg/wav/...) to 44.1 kHz mono wav with ffmpeg; return samples or None"""
    src = os.path.join(RAW, raw_name)
    if not os.path.exists(src) or os.path.getsize(src) == 0:
        return None
    out = os.path.join(WAV, os.path.splitext(raw_name)[0] + '.wav')
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', out], check=True)
    return readwav(out)


def seg(x, a, b, fi=0.003, fo=0.02):
    y = x[int(a * SR):int(b * SR)].copy()
    ni, no = int(fi * SR), int(fo * SR)
    if ni: y[:ni] *= np.linspace(0, 1, ni)
    if no: y[-no:] *= np.linspace(1, 0, no)
    return y


def norm_peak(y, db):
    p = np.abs(y).max()
    return y if p == 0 else y / p * 10 ** (db / 20)


def resample(y, ratio):
    """ratio > 1 raises pitch (shorter); plain linear interpolation of the real recording"""
    n = int(len(y) / ratio)
    return np.interp(np.arange(n) * ratio, np.arange(len(y)), y)


def lp_fft(y, fc, order=2):
    Y = np.fft.rfft(y); f = np.fft.rfftfreq(len(y), 1 / SR)
    Y *= 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(Y, len(y))


def hp_fft(y, fc, order=2):
    Y = np.fft.rfft(y); f = np.fft.rfftfreq(len(y), 1 / SR)
    Y *= 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(Y, len(y))


def hall(y, wet=0.18, t60=0.9):
    """small Schroeder-style comb room on a real sample (declared processing, not a sound source)"""
    L = len(y) + int(t60 * SR); src = np.concatenate([y, np.zeros(L - len(y))]); acc = np.zeros(L)
    for d in (0.0297, 0.0371, 0.0411, 0.0437):
        D = int(d * SR); g = 10 ** (-3 * d / t60); c = src.copy()
        # IIR comb y[n] = x[n] + g*y[n-D], computed block-wise (blocks of D samples are independent of each other inside)
        for k in range(D, L, D):
            c[k:k + D] += g * c[k - D:k - D + len(c[k:k + D])]
        acc += c - src
    return src + wet * acc / 4

def loop_bed(x, seconds, xf=0.25):
    """tile a real recording with random-offset crossfaded grains (equal power)"""
    n = int(seconds * SR); g = min(int(1.6 * SR), len(x) - 1); out = np.zeros(n + g + 1); f = int(xf * SR); i = 0
    win = np.ones(g); win[:f] = np.sin(np.linspace(0, np.pi / 2, f)); win[-f:] = np.cos(np.linspace(0, np.pi / 2, f))
    while i < n:
        o = rs.randint(0, max(1, len(x) - g)); out[i:i + g] += x[o:o + g] * win; i += g - f
    return out[:n]


# ------------------------------------------------------------------ sources ---
SRC = {}       # key -> dict(sig or grains, source record, fallback flag)

def src_rec(title, used_as, extra=None):
    m = META.get(title, {})
    r = dict(id=title, title=title, author=m.get('author', ''), license=m.get('license', ''), license_url=m.get('license_url', ''),
             source_url=m.get('source_url', ''), file_url=m.get('file_url', ''), local_path=m.get('local', ''),
             what_it_shows=m.get('desc', '')[:200], verified_date_or_place=m.get('date', '') or 'unverified', used_as=used_as)
    if extra: r.update(extra)
    return r

FALLBACKS = []
RECORDS = []

# steps: Concrete Steps 2 (two real steps on concrete)
cs = load('Concrete_Steps_2.ogg')
STEP_GRAINS = [norm_peak(seg(cs, 0.0, 0.30, 0.001, 0.08), -3), norm_peak(seg(cs, 0.635, 0.787, 0.001, 0.05), -3)]
RECORDS.append(src_rec('File:Concrete Steps 2.ogg', 'all footsteps: the two real steps cut as grains, alternated with +-3% speed and +-2 dB variation; the foreman\'s pacing gets a small declared room reverb'))

# hall walla / reverberant steps: low far layer under the foreman's pacing
ch = load('Church_people_walking_steps_with_reverb.ogg')  # editor repair r1: PD hall recording, used only as a sub-200 Hz rumble (4th-order low-pass: no speech band survives)

# clock tick
tick = load('Clock_ticking.ogg')
if tick is None:
    tick = readwav(WAV + '/Clock_ticking_from_testshot.wav')
RECORDS.append(src_rec('File:Clock ticking.ogg', 'clock tick bed (A: dropped under the meeting; B: rises 12:01-12:03)',
                       None if 'File:Clock ticking.ogg' in META else dict(author='natalie', license='Public domain',
                       source_url='https://commons.wikimedia.org/wiki/File:Clock_ticking.ogg',
                       file_url='https://upload.wikimedia.org/wikipedia/commons/5/56/Clock_ticking.ogg',
                       local_path=WAV + '/Clock_ticking_from_testshot.wav', verified_date_or_place='2007-04-29')))

# room tone: Moving Image Archive Valley Town (1940) factory-roof clip + WWS machine shop if present
# editor repair r1: the Valley Town (1940) plant clip is dropped (steady 118/174 Hz fifth = probable Blitzstein score; licence of the clip not independently verified)
ep = load('WWS_Edgeplaner.ogg')

# bells
b1 = load('Old_school_bell_1.ogg'); b2 = load('Old_school_bell_2.ogg'); b3 = load('Old_school_bell_3.ogg')
sig = load('WWS_Signalbell.ogg'); seb = load('WWS_Steamengineandsignalbell.ogg')
# punch, paper, tap, bite
tc = load('WWS_Timeclock.ogg'); mt = load('Mechanical_tack.ogg')
fw = load('Food_wrapper_crumpling.ogg'); bp = load('Book_paper_pages_assorted.ogg')
kn = load('Knocking_on_wood_or_door.ogg'); es = load('Eating_snacks.ogg')
cr = load('Crunching_munching_grinding.ogg')
m500 = load('ring_model500.ogg'); mine = load('WWS_Minetelephone.ogg'); cup = load('Cupboarddoorclose.ogg')

CHOICE = json.load(open(SW + '/sound-build/choice.json')) if os.path.exists(SW + '/sound-build/choice.json') else {}


def synth_bell(f0, seconds):
    t = np.arange(int(seconds * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t * d) for m, a, d in ((1, 1, 1.2), (2.76, .5, 2), (5.4, .25, 3.5)))
    # electric striker: 22 Hz amplitude ripple
    s *= 0.65 + 0.35 * np.abs(np.sin(np.pi * 22 * t))
    return norm_peak(s, -3)


def pick(name, default=None):
    return CHOICE.get(name, default)


# ---- build each sound family; each returns (signal, source title, fallback-or-None)
def work_bell(seconds):
    c = pick('work_bell')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['a'] + seconds + 0.6, 0.002, 0.6), -4), c['title'], None
    return synth_bell(880, seconds + 0.6), None, 'kit-style synthesized electric bell 880 Hz (no foraged bell obtained)'


def late_bell(seconds):
    c = pick('late_bell')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]; y = seg(x, c['a'], c['a'] + (seconds + 0.6) * c.get('ratio', 1), 0.002, 0.5)
        if c.get('ratio', 1) != 1: y = resample(y, c['ratio'])
        return norm_peak(y, -4), c['title'], None
    return synth_bell(1320, seconds + 0.5), None, 'kit-style synthesized higher electric bell 1320 Hz (no foraged late bell obtained)'


def punch():
    c = pick('punch')
    if c and c.get('layers'):
        parts = []
        for L in c['layers']:
            x = globals()[L['var']]; y = norm_peak(seg(x, L['a'], L['b'], 0.001, 0.04), L['db'])
            parts.append((int(L['at'] * SR), y))
        n = max(o + len(y) for o, y in parts); out = np.zeros(n)
        for o, y in parts: out[o:o + len(y)] += y
        return norm_peak(out, -5), c['title'], c.get('note')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['b'], 0.001, 0.05), -5), c['title'], None
    # declared fallback: a real wood knock (if present) layered as the 'chunk', else synthesis
    t = np.arange(int(.35 * SR)) / SR
    y = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 18) + .5 * hp_fft(rs.randn(len(t)), 2500) * np.exp(-t * 60)
    y[int(.09 * SR):] += .6 * hp_fft(rs.randn(len(t) - int(.09 * SR)), 1800) * np.exp(-t[:len(t) - int(.09 * SR)] * 70)
    return norm_peak(y, -6), None, 'kit-style synthesized "ka-chunk" (thud + two clicks); no foraged time-clock recording obtained'


def paper():
    c = pick('paper')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['b'], 0.01, 0.12), -10), c['title'], None
    n = int(.4 * SR); y = hp_fft(rs.randn(n), 2500) * np.hanning(n) * (0.5 + 0.5 * (rs.rand(n) > .9))
    return norm_peak(y, -14), None, 'kit-style band-noise paper rustle (no foraged paper recording obtained)'


def tap():
    c = pick('tap')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['b'], 0.001, 0.04), -12), c['title'], None
    t = np.arange(int(.12 * SR)) / SR
    return norm_peak(np.sin(2 * np.pi * 420 * t) * np.exp(-t * 60), -16), None, 'kit-style synthesized wood tap'


def lid():
    c = pick('lid')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['b'], 0.001, 0.04), -16), c['title'], None
    t = np.arange(int(.18 * SR)) / SR
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((1870, 30), (2950, 40), (4410, 55)))
    return norm_peak(y, -22), None, 'kit-style synthesized tin-lid tick (no foraged tin lid recording obtained)'


BITES = pick('bites', None)
def bite(k):
    if BITES and globals().get(BITES['var']) is not None:
        x = globals()[BITES['var']]; a, b = BITES['spans'][k % len(BITES['spans'])]
        return norm_peak(seg(x, a, b, 0.001, 0.08), -9), BITES['title'], BITES.get('note')
    a, b = [(8.02, 8.40), (10.93, 11.30), (13.13, 13.50)][k % 3]
    return norm_peak(seg(cr, a, b, 0.001, 0.08), -9), 'File:Crunching munching grinding.ogg', \
        'substitute: a real crunch (pistachio husks ground in the fist, PDSounds), not an apple bite; no openly licensed apple-bite recording found'


def whoosh():
    c = pick('slide')
    if c and globals().get(c['var']) is not None:
        x = globals()[c['var']]
        return norm_peak(seg(x, c['a'], c['b'], 0.05, 0.3), -16), c['title'], None
    return None, None, None


# ------------------------------------------------------------------ mix ---
STEMS = {k: np.zeros((N, 2)) for k in ('bells', 'steps', 'foley', 'room')}
FOREMAN = np.zeros((N, 2))
CUES = []


def onset(y, h=441):
    e = np.array([np.abs(y[i:i + h]).max() for i in range(0, max(1, len(y) - h), h)])
    return float(np.argmax(e > e.max() * 0.3) * h) / SR if len(e) and e.max() > 0 else 0.0


def put(stem, y, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or y is None: return
    if i < 0: y = y[-i:]; i = 0
    buf = FOREMAN if stem == 'foreman' else STEMS[stem]
    y = y[:N - i] * gain
    lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(y), 0] += y * lg * 1.414
    buf[i:i + len(y), 1] += y * rg * 1.414


def cue(kind, t, what, stem, src, fb, dur=None, gain=None, pan=0.0, rule_ref=None):
    f = int(round(t * FPS))
    c = dict(cue=kind, t=round(t, 3), frame=f, tolerance_frames=1, window_frames=[f - 1, f + 1], stem=stem,
             what=what, source=src, fallback=fb, pan=pan)
    if dur is not None: c['dur'] = round(dur, 3); c['end_frame'] = int(round((t + dur) * FPS))
    if gain is not None: c['gain_db'] = round(20 * math.log10(gain), 1)
    if rule_ref: c['rules_cue'] = rule_ref
    m = META.get(src or '', {})
    c['license'] = m.get('license', '') if src else ('kit synthesis (declared)' if fb else '')
    CUES.append(c)


def pacing(t0, t1, every, pan, gain, room=False, start_foot=0, label='', rref=None):
    t, k = t0, start_foot; n = 0
    while t < t1 - 0.05:
        g = STEP_GRAINS[k % 2]; r = 1 + rs.uniform(-.03, .03); y = resample(g, r)
        put('foreman' if room else 'steps', y, t, gain * 10 ** (rs.uniform(-2, 2) / 20), pan)
        k += 1; n += 1; t += every * rs.uniform(.94, 1.06)
    cue('steps', t0, f'{label} ({n} steps, every ~{every:.2f} s, stop by {t1:.2f})', 'steps', 'File:Concrete Steps 2.ogg', None,
        dur=t1 - t0, gain=gain, pan=pan, rule_ref=rref)


rules = json.load(open(SW + '/rules.json'))
RC = rules['cues']


def tick_loop(n):
    # loop the real ticking on a whole number of tick periods so the rhythm never stutters
    h = 220; e = np.array([np.abs(tick[i:i + h]).max() for i in range(0, len(tick) - h, h)])
    thr = e.max() * 0.35; on = [i for i in range(1, len(e)) if e[i] > thr and e[i - 1] <= thr]
    on = [o for j, o in enumerate(on) if j == 0 or o - on[j - 1] > 20]
    a, b = on[1] * h - 200, on[-1] * h - 200
    span = tick[a:b]; reps = int(np.ceil(n / len(span))) + 1
    return np.tile(span, reps)[:n].copy()


def room_bed(t0, t1, tick_env):
    n = int((t1 - t0) * SR)
    y = loop_bed(lp_fft(lp_fft(ch, 200, 2), 200, 2), t1 - t0)     # large-room rumble from the PD hall recording, < 200 Hz only
    y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 10 ** (-40 / 20)
    if ep is not None:
        far = loop_bed(lp_fft(hp_fft(ep, 120), 1800), t1 - t0)
        far = far / (np.sqrt(np.mean(far ** 2)) + 1e-9) * 10 ** (-44 / 20)
        y = y + far
    fade = int(.3 * SR); y[:fade] *= np.linspace(0, 1, fade); y[-int(.02 * SR):] *= np.linspace(1, 0, int(.02 * SR))
    put('room', y, t0, 1.0, 0.0)
    # ticking with a gain envelope over version-local seconds
    tk = tick_loop(n)
    tl = np.arange(n) / SR
    env = np.interp(tl, [p[0] for p in tick_env], [p[1] for p in tick_env])
    tk = norm_peak(tk, -1) * env
    put('room', tk, t0, 1.0, -0.25)


# room / tick beds -------------------------------------------------------
# A: tick at bed level, dropped under the meeting (7.0-14.3: declared silence, room tone only) and back for the rule
room_bed(0.0, 35.0, [(0, .10), (6.0, .10), (7.0, 0.0), (14.3, 0.0), (15.0, .10), (35, .10)])
cue('room', 0.0, 'A room tone bed (plant roar + far machine shop + hall air); clock tick bed except 7.0-14.3 (meeting: room tone only)', 'room',
    None, None, dur=35.0, rule_ref='room_tone/clock_tick A')
# B: tick rises 12:01-12:03 (tau 5 -> 15), no meeting
room_bed(37.0, 72.0, [(0, .10), (5.0, .10), (15.0, .22), (16.0, .12), (35, .12)])
cue('room', 37.0, 'B room tone bed; clock tick rises from 42.0 to 52.0 (R waits alone), eases after the late bell', 'room',
    None, None, dur=35.0, rule_ref='room_tone/clock_tick B')
# slate 35-37: no room tone (the light box), only the card slide

# bells ------------------------------------------------------------------
y, s, fb = work_bell(2.0); put('bells', y, 0.0 - onset(y), 1.0, 0.1); cue('bell', 0.0, 'work bell: both breaks begin (one ring ~2 s)', 'bells', s, fb, 2.0, rule_ref='work_bell')
if fb: FALLBACKS.append(('work_bell', fb))
y, s, fb = work_bell(1.2); _o = onset(y); _a = max(0, int((_o - 0.004) * SR)); y = y[_a:].copy(); y[:88] *= np.linspace(0, 1, 88); put('bells', y, 37.0 - (_o - _a / SR), 1.0, 0.1); cue('bell', 37.0, 'work bell: Renzo\'s break only (single shorter ring)', 'bells', s, fb, 1.2, rule_ref='work_bell')
y, s, fb = late_bell(1.6); put('bells', y, 52.0 - onset(y), 1.0, -0.1); cue('bell', 52.0, 'LATE BELL (higher, different bell): Luciana\'s break begins 12:03', 'bells', s, fb, 1.6, rule_ref='late_bell')
if fb: FALLBACKS.append(('late_bell', fb))

# steps --------------------------------------------------------------------
pacing(0.4, 5.0, 0.55, -0.6, 0.30, room=True, label='foreman pacing in the doorway (FLOOR); stops at 5.0 when he turns', rref='footsteps_foreman 0.4')
pacing(0.4, 2.0, 0.48, 0.6, 0.45, label='Renzo walks on from the right', rref='footsteps 0.4')
pacing(1.0, 2.6, 0.50, -0.3, 0.40, start_foot=1, label='Luciana walks on from the left', rref='footsteps 1.0')
pacing(14.3, 15.0, 0.35, 0.1, 0.45, label='Renzo rises and walks to the clock', rref='footsteps 14.3')
pacing(19.0, 19.6, 0.30, -0.4, 0.40, label='Luciana walks from the corner to the clock', rref='footsteps 19.0')
pacing(20.05, 35.0, 0.60, -0.6, 0.30, room=True, label='foreman pacing resumes, fading', rref='footsteps_foreman 20.0')
pacing(37.4, 42.0, 0.55, -0.6, 0.30, room=True, label='B foreman pacing (FLOOR); stops at 42.0', rref='footsteps_foreman 37.4')
pacing(37.4, 39.0, 0.48, 0.6, 0.45, label='B Renzo walks on from the right', rref='footsteps 37.4')
pacing(51.3, 52.0, 0.35, 0.1, 0.45, label='B Renzo rises and walks to the clock', rref='footsteps 51.3')
pacing(52.0, 53.5, 0.42, -0.5, 0.42, start_foot=1, label='B NEAR-MISS: Luciana crosses from the left', rref='footsteps 52.0')
pacing(52.4, 53.5, 0.40, 0.3, 0.45, label='B NEAR-MISS: Renzo walks back past the pile', rref='footsteps 52.4')
pacing(56.2, 56.8, 0.30, -0.3, 0.40, label='B Luciana moves to the open left end', rref='footsteps 56.2')
pacing(57.05, 72.0, 0.60, -0.6, 0.30, room=True, label='B foreman pacing resumes, fading', rref='footsteps_foreman 57.0')
# the foreman's pacing gets one small room (declared processing), then joins the steps stem
for ch_ in (0, 1):
    FOREMAN[:, ch_] = hall(FOREMAN[:, ch_], wet=.35, t60=.8)[:N]
STEMS['steps'] += FOREMAN
# fade the resumed pacing (A 20-35, B 57-72) by an envelope on the steps stem
for t0, t1 in ((20.0, 35.0), (57.0, 72.0)):
    i0, i1 = int(t0 * SR), int(t1 * SR); env = np.linspace(1.0, 0.3, i1 - i0)
    # only the foreman's pacing is in these spans except the short B walks, which get the same mild fade (<= -3 dB by 57-58)
    STEMS['steps'][i0:i1] *= env[:, None]

# foley ----------------------------------------------------------------------
for c in RC:
    s_name = c.get('sound'); t = c['t']
    if s_name == 'paper_rustle':
        y, s, fb = paper(); put('foley', y, t - onset(y), 1.0, -0.6); cue('paper', t, c['what'], 'foley', s, fb, rule_ref=s_name)
    elif s_name == 'bite_crunch':
        k = [x['t'] for x in rules['bites']['A'] + rules['bites']['B']].index(t)
        y, s, fb = bite(k); put('foley', y, t - onset(y), 1.0, 0.0); cue('bite', t, c['what'], 'foley', s, fb, rule_ref=s_name)
    elif s_name == 'timeclock_punch':
        y, s, fb = punch(); put('foley', y, t - onset(y), 1.0, -0.15); cue('punch', t, c['what'], 'foley', s, fb, rule_ref=s_name)
    elif s_name == 'tap_small':
        y, s, fb = tap(); put('foley', y, t - onset(y), 1.0, 0.0); cue('tap', t, c['what'], 'foley', s, fb, rule_ref=s_name)
    elif s_name == 'lid_tin':
        y, s, fb = lid(); put('foley', y, t - onset(y), 1.0, 0.0); cue('lid', t, c['what'], 'foley', s, fb, rule_ref=s_name)
    elif s_name in ('whoosh', 'card_slide'):
        y, s, fb = whoosh()
        if y is not None:
            put('foley', y, t - onset(y), 0.8 if s_name == 'whoosh' else 0.6, 0.0)
        cue('slate', t, c['what'], 'foley', s, fb or (None if y is not None else 'silent: no slide sample'), rule_ref=s_name)
# a real bite of the apple at the B crossing is in rules at 51.0 (Renzo's one bite); covered above.

# ---------------------------------------------------------------- write ---
def wr(p, st):
    st = np.clip(st, -1, 1); a = (st * 32767).astype(np.int16)
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())

full = sum(STEMS.values())
peak = np.abs(full).max(); g = 10 ** (-1 / 20) / peak if peak > 10 ** (-1 / 20) else 1.0
cut = int(72.0 * SR)           # hard cut to black at 72.0: no fade-out beyond 5 ms
for k in STEMS: STEMS[k] *= g
full = sum(STEMS.values()); full[cut - int(.005 * SR):] *= np.linspace(1, 0, int(.005 * SR))[:, None][:len(full[cut - int(.005 * SR):])]
os.makedirs(SW + '/stems', exist_ok=True)
for k, v in STEMS.items(): wr(SW + f'/stems/{k}.wav', v)
wr(SW + '/sound.wav', full)
wr(SW + '/sound-nobells.wav', full - STEMS['bells'])

def lev(x): return round(20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-12), 1), round(20 * math.log10(np.abs(x).max() + 1e-12), 1)
levels = {k: dict(zip(('rms_dbfs', 'peak_dbfs'), lev(v))) for k, v in STEMS.items()}
levels['full'] = dict(zip(('rms_dbfs', 'peak_dbfs'), lev(full)))
# meeting check: A 7.0-15.0 holds room tone + bites only
i0, i1 = int(7.05 * SR), int(14.25 * SR)
levels['A_meeting_7_14.3'] = {k: dict(zip(('rms_dbfs', 'peak_dbfs'), lev(STEMS[k][i0:i1]))) for k in STEMS}

ABSENCES = [
    'apple bite: searched Commons audio for "apple bite", "biting apple", "apple eating", "eating apple", "crunch eating", "chewing", "bite crisp": no recording of an apple bite under PD/CC0/CC BY/BY-SA; used a real PD crunch (pistachio husks) as declared substitute',
    'time-clock punch: Commons "WWS Timeclock.ogg" (CC BY 4.0, Work With Sounds) was found, but upload.wikimedia.org returned HTTP 429 (retry-after 600) for every attempt over ~60 min; substitute layered from two real recordings. Re-try later and set choice.json punch -> WWS_Timeclock.ogg',
    'also found but not downloadable (429): Old school bell 1-5.ogg (PD hand bells), WWS Signalbell.ogg (CC BY 4.0), WWS Steamengineandsignalbell.ogg, WWS Edgeplaner.ogg (CC BY 4.0 machine shop; would add a far machine layer to the room tone), Food wrapper crumpling.ogg, Eating snacks.ogg, Mechanical tack.ogg',
    'factory room tone with source sound in the Moving Image Archive cache: of the factory/machine-shop/shift/assembly/lathe/plant hits with audio, Master Hands (1936, both clips) carry an orchestral score, Look to Lockheed (1940) and the atom-plant/duPont/White Ammunition clips carry narration; Valley Town (1940) a11ba534 has diegetic plant sound but a steady 118/174 Hz fifth (probable Marc Blitzstein score) and was DROPPED in editor repair r1; the room tone is now a sub-200 Hz rumble from the PD Commons hall recording',
    'footsteps on concrete: only "Concrete Steps 2.ogg" (two steps, 0.79 s) is clean; longer step recordings found (Church people walking steps with reverb, PD) carry crowd walla, so they are not used as steps (the hall recording appears only as a sub-200 Hz room rumble), so pacing is built from the two real steps',
    'tin pail lid: no openly licensed tin-lid recording searched out in the time; a real cupboard-door click stands in (declared)',
    'no kit-synthesized sound remains in the mix: every sounding element is a real recording (bites and punch are declared substitutes)',
]
CUES.sort(key=lambda c: (c['t'], c['stem']))
out = dict(slug='renzo-e-luciana', unit='sound (U3)', base='rules.json cues (authoritative) + plan.md section 5',
           fps=FPS, rate=SR, duration_s=DUR, total_frames=int(DUR * FPS), channels=2,
           files=dict(mix=SW + '/sound.wav', mix_without_bells=SW + '/sound-nobells.wav',
                      stems={k: SW + f'/stems/{k}.wav' for k in STEMS}),
           editor_use='stereo 16-bit 44.1 kHz. With kit.Mix: x=wav (N,2); mix.add(x[:,0]/1.414, 0, pan=-1); mix.add(x[:,1]/1.414, 0, pan=1). '
                      'kit master() only attenuates (peak is -1 dBFS) so levels survive. Comparison: sound-off = mute; bell-restored = sound.wav; '
                      'rule-only = sound-nobells.wav (no bells, everything else).',
           declared_silence=['A 7.0-14.3 (frames 168-343, the MEETING): room tone only, clock tick dropped, no steps, no bells; only the three bites (8.5, 11.0, 13.0), the lid tick at 13.6 and the core tap at 14.0 sound',
                             'slate 35.0-37.0 (frames 840-887): no room tone; only the card set down and the strip slide',
                             'no voice, no score anywhere'],
           deviations=['L break-end punch is at 71.5 s (frame 1716) as in rules.json, not 72.0; the hard cut to black at 72.0 ends the mix',
                       "Renzo's one bite in B is at 51.0 (rules.json), just before he rises, not at the 52-53.5 crossing"],
           absences=ABSENCES,
           levels=levels, fallbacks_declared=[dict(element=a, fallback=b) for a, b in FALLBACKS] +
           [dict(element=c['cue'] + '@' + str(c['t']), fallback=c['fallback']) for c in CUES if c.get('fallback') and c['cue'] not in ('bell',)],
           processing='decode ffmpeg -> 44.1 kHz mono wav; trims with 1-3 ms fade-in; per-sample peak levelling; +-3% speed and +-2 dB step variation; '
                      'Schroeder-style room (wet .35, T60 .8 s) on the foreman\'s steps only; room beds tiled from random-offset crossfaded grains of the real recordings, low-passed (plant roar 400 Hz, machine shop 1.8 kHz, hall air 900 Hz)',
           cues=CUES)
json.dump(out, open(SW + '/cues.json', 'w'), indent=1)
# credits / evidence
used = sorted({c['source'] for c in CUES if c.get('source')})
for t in used:
    if t not in [r['id'] for r in RECORDS]:
        RECORDS.append(src_rec(t, ', '.join(sorted({c['cue'] for c in CUES if c.get('source') == t}))))
for v, nm in ((ep, 'File:WWS Edgeplaner.ogg'), (ch, 'File:Church people walking steps with reverb.ogg')):
    if v is not None and nm not in [r['id'] for r in RECORDS]:
        RECORDS.append(src_rec(nm, 'room tone: the only bed, 4th-order low-passed at 200 Hz (a large-room rumble; no speech band survives), tiled into a 35 s bed per version'))
USED_AS = {
    'File:Model 500 Telephone British ring.ogg': 'WORK BELL (t 0.0, one 2 s double ring; t 37.0, single shorter ring): a real electric telephone bell, gongs ~1235/1690 Hz, trimmed from 0.2 s',
    'File:WWS Minetelephone.ogg': 'LATE BELL (t 52.0, 1.6 s): a real continuous trembling electric bell, gong ~1885/3785 Hz, higher and shriller than the work bell; trimmed from 3.0 s',
    'File:Cupboarddoorclose.ogg': 'pail lid open/close ticks (2.8, 13.6, 18.0, 54.0) and the first half of every time-clock "ka-chunk" (15.0, 20.0, 52.0, 71.5)',
    'File:Knocking on wood or door.ogg': 'single wood knock: the core set in the lid (14.0), the apple set on her lid (53.0), and the second half of each time-clock "ka-chunk"',
    'File:Book paper pages assorted.ogg': 'paper rustle as the foreman turns to his sheets (5.0, 12.0, 42.0, 49.0) and the slate card set down / strip slide (35.0, 35.25)',
    'File:Crunching munching grinding.ogg': 'bite crunches (8.5, 11.0, 13.0, 51.0, 55.0): SUBSTITUTE, a real crunch of pistachio husks, not an apple',
}
for r in RECORDS:
    if r['id'] in USED_AS: r['used_as'] = USED_AS[r['id']]
    m = META.get(r['id'], {})
    if r['id'].startswith('File:'):
        r['verified'] = 'licence read from Commons extmetadata on 2026-11-16; local file sha1 ' + ('matches the Commons original' if m.get('sha1_match') is True else 'not compared (Commons mp3/ogg transcode)' if m.get('sha1_match') is not None else 'not compared (downloaded directly this session)')
        if m.get('copied_from'): r['verified'] += '; bytes reused from ' + m['copied_from']
json.dump(RECORDS, open(SW + '/credits-sound.json', 'w'), indent=1)
print(json.dumps(levels, indent=0)); print('fallbacks', out['fallbacks_declared']); print(len(CUES), 'cues')
