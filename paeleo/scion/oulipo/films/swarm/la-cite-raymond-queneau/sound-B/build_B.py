"""Edition B (surveillance) stems for la-cite-raymond-queneau, plan-r3 section 6b, B column.

Builds voice / music / fx / amb as 44.1 kHz stereo 16-bit wav, 1,323,000 samples each,
plus preview-B.wav, cues-B.json, B.vtt and ledger.json.  Foraged sources are decoded with
ffmpeg only (to wav in sources/.../sound-B/raw/*.dec.wav), then read with the wave module.
Run:  python3 -I build_B.py
"""
import json, math, os, sys, wave, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, FILMS)
import kit                      # noqa: E402  (Mix, RATE)
from kit_cinema_b import lufs   # noqa: E402

SRC = os.path.join(FILMS, "sources", "la-cite-raymond-queneau", "sound-B")
RAW = os.path.join(SRC, "raw")
STEMS = os.path.join(SRC, "stems")
PREP = os.path.join(FILMS, "sources", "la-cite-raymond-queneau",
                    "sound-b-surveillance-uneasy-watching-team-voice-captions-music-drone-fx-ambience-")
os.makedirs(STEMS, exist_ok=True); os.makedirs(PREP, exist_ok=True)
R = 44100; N = 1323000; FPS = 24
def T(frame): return frame / FPS
def I(t): return int(round(t * R))

# ---------------------------------------------------------------- locked picture events (plan §6)
WIN = [(0, 146), (13, 168), (26, 190), (39, 211), (52, 233), (65, 254), (78, 276), (91, 298), (8, 319),
       (21, 341), (34, 362), (47, 384), (60, 406), (73, 427), (86, 449), (3, 470), (16, 492), (29, 514),
       (42, 535), (55, 557), (68, 578), (81, 600)]
EDL = os.path.join(HERE, "..", "picture", "edl.json")
CONTACTS = None
if os.path.exists(EDL):
    ev = json.load(open(EDL))["events"] if isinstance(json.load(open(EDL)), dict) else json.load(open(EDL))
    CONTACTS = [(e["id"], e["frame"]) for e in ev if e["kind"] == "walker_step" and e["id"].startswith("step")]
    wins = {e["window"]: e["frame"] for e in ev if e["kind"] == "window_on"}
    assert all(wins.get(w) == f for w, f in WIN), "edl.json window frames differ from plan §6 table"
if not CONTACTS:   # from picture/maquette.py contact_frames() (WALK_K0=200, STEP=13.2), <= 346
    CONTACTS = [(f"step{j:02d}", f) for j, f in enumerate([200, 213, 226, 240, 253, 266, 279, 292, 306, 319, 332, 345])]

# ---------------------------------------------------------------- io
def load(name):
    p = os.path.join(RAW, name)
    w = wave.open(p); c = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    assert w.getframerate() == R
    return x.reshape(-1, c).mean(1)

def have(name): return os.path.exists(os.path.join(RAW, name))

def onset(x, thr_db=18):
    """first sample whose 1 ms high-passed energy rises thr_db above the median floor."""
    hp = np.diff(x, prepend=0); n = 44
    e = np.array([np.sqrt((hp[i:i + n] ** 2).mean()) for i in range(0, len(x) - n, n)])
    db = 20 * np.log10(e + 1e-9); fl = np.median(db)
    k = int(np.argmax(db > fl + thr_db)); return k * n

def cut(x, t0, dur, pre=0.004, fade=0.01):
    a = max(0, I(t0) - I(pre)); w = x[a:a + I(0.3)]
    on = a + onset(w); y = x[max(0, on - I(pre)): on + I(dur)].copy()
    f = I(fade); y[-f:] *= np.linspace(1, 0, f); y[:8] *= np.linspace(0, 1, 8)
    return y, I(pre)            # sample, offset of the transient inside it

def band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / R)
    g = np.ones_like(f)
    if lo > 0: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** 8)
    if hi > 0: g *= 1 / np.sqrt(1 + (f / hi) ** 8)
    return np.fft.irfft(X * g, len(x))

def norm_peak(x, db): return x / (np.abs(x).max() + 1e-12) * 10 ** (db / 20)

class Stem:
    def __init__(s, name): s.name = name; s.L = np.zeros(N); s.R = np.zeros(N)
    def add(s, sig, t_event, pan=0.0, gain_db=0.0, lead=0):
        i = I(t_event) - lead
        if i < 0: sig = sig[-i:]; i = 0
        sig = sig[: N - i] * 10 ** (gain_db / 20)
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        s.L[i:i + len(sig)] += sig * lg * 1.414; s.R[i:i + len(sig)] += sig * rg * 1.414
    def gate(s, t0, t1, fade=0.03):
        """hard silence in [t0,t1) with short fades outside it."""
        a, b, f = I(t0), I(t1), I(fade)
        for ch in (s.L, s.R):
            ch[a:b] = 0
            ch[a - f:a] *= np.linspace(1, 0, f); ch[b:b + f] *= np.linspace(0, 1, f)
    def st(s): return np.stack([s.L, s.R], 1)

voice, music, fx, amb = Stem("voice"), Stem("music"), Stem("fx"), Stem("amb")
cues = []; handmade = []
def claim(ev, sid, t_sound, pid, frame, c):
    cues.append(dict(sound_event=ev, source_ledger_id=sid, t_sound=round(t_sound, 4), picture_event_id=pid,
                     frame=frame, offset_ms=round((t_sound - T(frame)) * 1000, 1), reading="surveillance", claim=c))

# ---------------------------------------------------------------- foraged samples
click_src = load("click_heating.dec.wav")
CLICK, CL = cut(click_src, 1.12, 0.16)                 # the louder second click of the switch
CLICK = norm_peak(band(CLICK, 180, 9000), -7.5)
LATCH, LL = cut(click_src, 0.05, 0.16)                 # the first, softer click: strike re-latching
LATCH = norm_peak(band(LATCH, 120, 6000), -14)

tw = load("typewriter_wws.dec.wav")
KEY_T = [1.387, 6.690, 7.064, 7.348, 8.226]            # strongest single keystrokes (onset scan)
KEYS = []
for t in KEY_T:
    k, kl = cut(tw, t - 0.01, 0.11); KEYS.append((norm_peak(band(k, 250, 12000), -11), kl))
CARR, CRL = cut(tw, 20.45, 0.74, fade=0.06)             # carriage throw to its stop (ends before the hold)
CARR = norm_peak(band(CARR, 120, 12000), -10)
DING, DGL = cut(load("typewriter_ding.dec.wav"), 0.0, 0.9, fade=0.15)
DING = norm_peak(DING, -16)
SHUT, SHL = cut(load("shutter_holga.dec.wav"), 0.28, 1.0, pre=0.0005, fade=0.1)
SHUT = norm_peak(band(SHUT, 150, 14000), -8.5)
CHAT_KEYS = []                                         # a run of real keystrokes for S4 chatter
for t in [0.524, 0.678, 1.078, 1.282, 1.482, 1.576, 1.711, 1.886, 2.39, 2.524, 2.903, 3.083, 3.248, 3.447, 3.542, 3.682]:
    k, kl = cut(tw, t - 0.005, 0.07, fade=0.02); CHAT_KEYS.append((band(k, 900, 9000), kl))

def wind_bed():
    w = load("wind.dec.wav")[I(8):I(8) + N + I(1)]
    w = band(w, 60, 900)
    return norm_peak(w, -6)[:N]

def hum_bed():
    if have("MainsBrum50Hz.dec.wav"):
        h = load("MainsBrum50Hz.dec.wav")
        h = h[I(0.5):I(5.0)]; h = band(h, 40, 1200)
        xf = 882 * 12; seg = len(h) - xf; out = np.zeros(N + len(h))   # 4.5 s = 225 periods; seam on whole periods
        win = np.concatenate([np.linspace(0, 1, xf), np.ones(seg - xf), np.linspace(1, 0, xf)])
        for i in range(0, N, seg): out[i:i + len(h)] += h * win
        return norm_peak(out[:N], -6), "FORAGED:hum_mainsbrum"
    m = kit.Mix(N / R + 0.1, seed=5); t = np.arange(N) / R
    fl = 1 + 0.002 * np.sin(2 * np.pi * 0.07 * t)
    h = sum(a * np.sin(2 * np.pi * 50 * k * np.cumsum(fl) / R) for k, a in [(1, 1), (2, .55), (3, .35), (5, .12), (7, .05)])
    h *= 1 + 0.04 * np.sin(2 * np.pi * 0.31 * t)
    handmade.append(dict(id="HM:hum", what="50 Hz mains hum (1,2,3,5,7 harmonics, 0.2% flutter)", where="build_B.py hum_bed()"))
    return norm_peak(h, -6), "HANDMADE:hum"

# ---------------------------------------------------------------- HANDMADE drone (kit.Mix)
def drone():
    m = kit.Mix(N / R + 0.1, seed=11); t = np.arange(N) / R
    sig = (m.tone(41.2, N / R)[:N] * 1.0 + m.tone(41.33, N / R)[:N] * 0.7 +
           m.tone(61.8, N / R)[:N] * 0.35)
    upper = m.tone(123.6, N / R)[:N] * 0.22 + m.tone(185.4, N / R)[:N] * 0.10
    thin = np.clip((t - 26.0) / 3.0, 0, 1)             # S4: the drone thins
    sig = sig * (1 - 0.65 * thin) + upper * (1 - thin)
    sig *= np.clip(t / 2.5, 0, 1)                      # slow rise from 0 s
    handmade.append(dict(id="HM:drone", what="held low drone: E1 41.2 Hz with a 0.13 Hz beating twin, fifth 61.8 Hz, "
                         "2nd/3rd partials that thin out from 26 s (kit.Mix.tone)", where="build_B.py drone()"))
    return norm_peak(sig, -6)

def strike_buzz(dur=0.50):
    m = kit.Mix(dur + 0.05, seed=3); t = m.t(dur)
    b = m.tone(100, dur, "square") + 0.4 * m.tone(200, dur, "saw")
    b *= 1 + 0.5 * np.sign(np.sin(2 * np.pi * 50 * t))  # coil rattle at mains rate
    b = band(b, 90, 4500) * m.env(len(t), attack=0.004, decay=0.02, sustain=0.85, release=0.03)
    handmade.append(dict(id="HM:strike_buzz", what="electric door-strike buzz, 0.50 s, 100 Hz square + rattle", where="build_B.py strike_buzz()"))
    return norm_peak(b, -12)

def radio(x):
    y = band(x, 300, 3000); y = np.tanh(3.0 * y / (np.abs(y).max() + 1e-9)) / np.tanh(3.0)
    return y

def squelch(dur, seed):
    m = kit.Mix(dur + 0.05, seed=seed); n = m.noise(dur)[: I(dur)]
    n = radio(n) * m.env(len(n), attack=0.002, decay=dur * 0.6, sustain=0.2, release=0.02)
    return n

# ================================================================= assemble
pan_of = lambda w: ((w % 24) - 11.5) / 23 * 0.6

# 1. window score: the same relay click on every window frame, except where the plan holds silence
for w, f in WIN:
    if f == 384:   continue                 # 16.0-17.5 voice only (radio speech carries this cue)
    if f == 406:   continue                 # still in the voice-only crossover (radio key-off carries it)
    if 538 <= f <= 566: continue            # expressive hold (window 55, f557): deliberately unlogged
    fx.add(CLICK, T(f), pan_of(w), lead=CL)
    claim("relay click (same sample)", "click_heating", T(f), f"win{w:02d}_on", f,
          f"the light in window {w} is registered by a switch the instant it appears: a lit window is an entry in a ledger")
cues.append(dict(sound_event="held silence (no click)", source_ledger_id=None, t_sound=round(T(557), 4), picture_event_id="win55_on",
                 frame=557, offset_ms=0.0, reading="surveillance",
                 claim="the only unlogged light falls inside the hold after the head turn: the recorder itself is listening"))

# 2. walker: a typewriter key on each foot contact, quiet at first and growing
for j, (sid, f) in enumerate(CONTACTS):
    k, kl = KEYS[j % len(KEYS)]
    g = -9 + 9 * min(1, j / 6)
    fx.add(k, T(f), -0.35 + 0.5 * j / max(1, len(CONTACTS) - 1), gain_db=g, lead=kl)
    claim("typewriter key", "typewriter_wws", T(f), sid, f,
          "each step of Madame Ferrand is typed as she takes it: her walk home is being written up")

# 3. door: electric strike buzz at f334, re-latch at f374
if have("metro.dec.wav"):
    mb = load("metro.dec.wav")[I(39.0) - I(0.3): I(39.0) + I(0.6)]
    on = onset(band(mb, 1800, 7000), 12); mb = band(mb[on:on + I(0.52)], 1800, 7000)
    mb *= np.concatenate([np.ones(len(mb) - I(0.03)), np.linspace(1, 0, I(0.03))])
    fx.add(norm_peak(mb, -13), T(334), 0.15); BUZZ_ID = "metro_buzzer"
else:
    fx.add(strike_buzz(), T(334), 0.15); BUZZ_ID = "HM:strike_buzz"
claim("electric door buzzer (0.52 s)", BUZZ_ID, T(334), "door_open", 334,
      "the door does not open, it is released: someone else holds the entrance")
fx.add(LATCH, T(374), 0.15, lead=LL)
claim("strike re-latch click", "click_heating", T(374), "door_close", 374, "the entrance is locked again behind her")

# 4. beat: click on 492 (already placed), ding + carriage at 518, silence 538-566, shutter at 566
fx.add(DING, T(518) - 0.32, 0.2, lead=DGL)
fx.add(CARR, T(518), 0.2, lead=CRL)
claim("typewriter carriage return (bell 0.32 s before, throw on the frame)", "typewriter_wws", T(518), "silhouette_rise", 518,
      "the silhouette's rise completes a line in the report: the watcher has been entered")
claim("single camera shutter", "shutter_holga", T(566), "curtain_slide", 566,
      "after the hold, one exposure: the head turn toward the street was a look that is now on file")

# 5. S4: teleprinter-like chatter of real keystrokes, final click at 696
rng = np.random.RandomState(7); t = 26.35; j = 0
while t < T(696) - 0.12:
    k, kl = CHAT_KEYS[j % len(CHAT_KEYS)]
    fx.add(k, t, 0.45 * math.sin(j * 0.7), gain_db=-15 + 2 * rng.rand() + 4 * min(1, (t - 26.35) / 1.5), lead=kl)
    t += 1 / 9.0 + (0.03 if j % 8 == 7 else 0); j += 1
fx.add(CLICK, T(696), pan_of(16), lead=CL)
claim("relay click (same sample)", "click_heating", T(696), "win16_off", 696,
      "window 16 goes dark on the same click that lit it: the watcher's own light is switched off from elsewhere")

# 6. voice: radio 'quarante-sept' on 384, key-off squelch on 406
qs = None
for cand in ("LL-Q150_fra-Poslovitch-quarante-sept", "LL-Q150_fra-Estrie-quarante-sept"):
    if have(cand + ".wav") and not have(cand + ".dec.wav"):     # decode the download with ffmpeg only
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", os.path.join(RAW, cand + ".wav"),
                        "-ac", "1", "-ar", str(R), "-c:a", "pcm_s16le", os.path.join(RAW, cand + ".dec.wav")], check=True)
    if have(cand + ".dec.wav"): qs = cand + ".dec.wav"; break
if qs:
    sp = load(qs); on = onset(sp, 20); sp = sp[max(0, on - I(0.01)):]; sp = sp[: I(1.3)]
    sp[-I(0.05):] *= np.linspace(1, 0, I(0.05))
    sp = norm_peak(radio(sp), -9)
    voice.add(sp, T(384), 0.0, lead=I(0.01))
    voice.add(squelch(0.05, 1) * 0.25, T(384) - 0.07)
    claim("radio voice 'quarante-sept' (300-3000 Hz, saturated)", "LL:" + qs.split("-")[2], T(384), "win47_on", 384,
          "window 47 is named aloud by number over a radio: the lit window is an address being called in")
LOC_T0 = 2.9                          # s into the 1917 record: a ~1.2 s phrase between two pauses (3.0-4.2 s)
LOC_SP = "loc_jukebox26299.dec.wav"   # repair 2 fallback: real recorded speech, Victor 1917 (US PD since 2022, MMA), via LoC
if not qs and not have(LOC_SP) and os.path.exists(os.path.join(SRC, "loc-r2", "jukebox-26299.mp3")):
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", os.path.join(SRC, "loc-r2", "jukebox-26299.mp3"),
                    "-ac", "1", "-ar", str(R), "-c:a", "pcm_s16le", os.path.join(RAW, LOC_SP)], check=True)
if not qs and have(LOC_SP):
    src = load(LOC_SP)
    seg = src[I(LOC_T0): I(LOC_T0) + I(2.0)]
    on = onset(seg, 15); sp = seg[on: on + I(1.25)].copy()
    sp[-I(0.08):] *= np.linspace(1, 0, I(0.08)); sp[:I(0.004)] *= np.linspace(0, 1, I(0.004))
    sp = norm_peak(radio(band(sp, 350, 2600)), -10)
    voice.add(norm_peak(squelch(0.05, 3), -16), T(384))          # the channel opens ON the cut frame
    voice.add(sp, T(384) + 0.05, 0.0)
    voice.add(norm_peak(squelch(0.10, 5), -17), T(384) + 0.05 + len(sp) / R)
    qs = LOC_SP
    claim("radio voice, a man speaking, words indistinct (300-3000 Hz, saturated)", "LOC:jukebox-26299", T(384) + 0.05, "win47_on", 384,
          "a voice comes over the radio on the cut frame as window 47 lights: the lit window is being reported to someone")
if not qs:   # gap: no Lingua Libre download got through (HTTP 429); the radio channel still opens on the cut
    voice.add(norm_peak(squelch(0.22, 4), -15), T(384), 0.0)
    claim("radio squelch opening (fallback: 'quarante-sept' recording not obtained)", "HM:squelch", T(384), "win47_on", 384,
          "the radio channel opens on the cut frame as window 47 lights: the lights are being reported to someone")
voice.add(norm_peak(squelch(0.18, 2), -18), T(406), 0.0)
claim("radio key-off squelch", "HM:squelch", T(406), "win60_on", 406,
      "the next light coincides with the transmission closing: the radio is answering the windows")
handmade.append(dict(id="HM:squelch", what="radio squelch bursts (band-passed noise 300-3000 Hz)", where="build_B.py squelch()"))

# 7. beds: hum (music stem bed), drone (music), wind (amb)
hum, hum_id = hum_bed()
music.add(drone(), 0.0, 0.0, gain_db=-14)
music.add(hum, 0.0, 0.1, gain_db=-19)
amb.add(wind_bed(), 0.0, -0.1, gain_db=-14)
# hum re-enters at 17.5 slightly louder (plan: 'the hum returns')
for s in (music, amb, fx):
    s.gate(16.0, 17.5)           # crossover: voice only
    s.gate(T(538), T(566))       # held silence through 538-566 (shutter at 566 is re-added below)
voice.gate(T(538), T(566))
# the shutter is placed after gating so the gate's fade-in cannot soften its transient
fx.add(SHUT, T(566), 0.1, lead=SHL)

stems = {s.name: s.st() for s in (voice, music, fx, amb)}

# ---------------------------------------------------------------- pre-mix to -23 LUFS
def tpk(st):
    up = np.stack([np.interp(np.arange(len(st) * 4) / 4, np.arange(len(st)), st[:, c]) for c in range(2)], 1)
    return 20 * math.log10(np.abs(up).max() + 1e-12)
mix = sum(stems.values())
L0 = lufs(mix); g = 10 ** ((-23.0 - L0) / 20)
for k in stems: stems[k] = stems[k] * g
mix = mix * g
report = dict(pre_gain_db=round(20 * math.log10(g), 2), integrated_lufs=round(lufs(mix), 2), true_peak_dbtp_approx=round(tpk(mix), 2),
              per_stem_gain_db=dict(voice=round(20 * math.log10(g), 2), music=round(20 * math.log10(g), 2),
                                    fx=round(20 * math.log10(g), 2), amb=round(20 * math.log10(g), 2)),
              per_stem_internal_db=dict(voice="radio speech peak -9 dBFS, squelch -18", music="drone -14, hum -19 (" + hum_id + ")",
                                        fx="click -6 peak, keys -11 peak (-9..0 dB ramp), carriage -10, ding -16, shutter -7, chatter -15..-9, buzz -12",
                                        amb="wind -14 (peak-normalised -6 then -14)"),
              stem_lufs={k: round(lufs(v), 2) for k, v in stems.items()})

def wwav(p, st):
    a = np.clip(np.round(st * 32767), -32768, 32767).astype("<i2")
    assert a.shape == (N, 2)
    w = wave.open(p, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(R); w.writeframes(a.tobytes()); w.close()
for k, v in stems.items(): wwav(os.path.join(STEMS, f"B-{k}.wav"), v)
wwav(os.path.join(HERE, "preview-B.wav"), mix)

# ---------------------------------------------------------------- checks
def dbfs(st, t0, t1):
    a = st[I(t0):I(t1)]; return 20 * math.log10(np.abs(a).max() + 1e-12)
checks = dict(crossover_16_17_5={k: round(dbfs(v, 16.0, 17.5), 1) for k, v in stems.items()},
              hold_538_566={k: round(dbfs(v, T(538), T(566) - 0.001), 1) for k, v in stems.items()},
              samples={k: len(v) for k, v in stems.items()})
report["checks"] = checks
json.dump(report, open(os.path.join(HERE, "premix-B.json"), "w"), indent=1)
json.dump(cues, open(os.path.join(HERE, "cues-B.json"), "w"), indent=1, ensure_ascii=False)
json.dump(handmade, open(os.path.join(HERE, "handmade-B.json"), "w"), indent=1)
print(json.dumps(report, indent=1))
