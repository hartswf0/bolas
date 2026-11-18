# Sound for la-mort-en-ce-jardin: cue list + mixed WAV stems on the 73.0 s film timeline (plan section 6).
# python3 -I sound.py   (reads performance/trace-{L,E}.json for step, splash and grip times; foraged audio decoded
# with ffmpeg from films/sources/la-mort-en-ce-jardin/; synthesized foley with kit.Mix)
# Stems (44.1 kHz stereo 16-bit): water.wav (foraged bed + lapping), jungle.wav (foraged insects/birds, with the
# declared insect silences), foley.wav (synthesized creaks/steps/tap/rustle/pencil + foraged splash), mix.wav.
import sys, os, json, math, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, FILMS)
from kit import Mix, RATE  # noqa: E402

SRC = os.path.join(FILMS, "sources", "la-mort-en-ce-jardin")
OS = os.path.join(SRC, "object-sound")
PERF = os.path.join(HERE, "..", "performance")
T_FILM = 73.0
OFF = {"L": 2.0, "E": 39.5}           # film t = local + OFF
END = {"L": 36.0, "E": 30.0}
cues = []

def cue(film_t, kind, what, version, source, gain_db=None, dur=None):
    cues.append(dict(film_t=round(film_t, 3), dur=None if dur is None else round(dur, 3), version=version, kind=kind,
                     what=what, source=source, gain_db=gain_db))

def decode(path, ss=0.0, dur=None):
    """ffmpeg -> float stereo @ RATE (untrusted file: decoded only)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(dur)] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(RATE), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    return x

def norm_rms(x, db):
    r = np.sqrt((x ** 2).mean()) + 1e-12
    return x * (10 ** (db / 20) / r)

def loop_to(x, n, xfade=RATE // 2):
    out = np.zeros((n, 2)); i = 0; w = np.linspace(0, 1, xfade)[:, None]
    while i < n:
        seg = x.copy()
        if i > 0:
            k = min(xfade, len(seg), n - i)
            out[i:i + k] = out[i:i + k] * (1 - w[:k]) + seg[:k] * w[:k]; seg = seg[k:]; i += k
        k = min(len(seg) - xfade, n - i) if len(seg) > xfade else min(len(seg), n - i)
        out[i:i + k] = seg[:k]; i += k
        if i >= n: break
        i -= min(xfade, i)
    return out[:n]

def envelope(n, pts):
    """piecewise-linear gain in dB over film time: pts [(t, db)]."""
    ts = np.arange(n) / RATE
    tt, dd = zip(*pts)
    return 10 ** (np.interp(ts, tt, dd) / 20)

def put(stem, sig, at, gain=1.0, pan=0.0):
    i = int(round(at * RATE));
    if sig.ndim == 1:
        lg, rg = math.cos((pan + 1) * math.pi / 4) * 1.414, math.sin((pan + 1) * math.pi / 4) * 1.414
        sig = np.stack([sig * lg, sig * rg], 1)
    k = min(len(sig), len(stem) - i)
    if k > 0 and i >= 0: stem[i:i + k] += sig[:k] * gain

N = int(T_FILM * RATE)
M = Mix(T_FILM, seed=56)
rs = np.random.RandomState(1956)

# ------------------------------------------------------------------ foraged files
F = dict(stream=os.path.join(SRC, "test-shot", "audio", "stream.mp3"),
         jungle=os.path.join(OS, "raw", "jungle_phuket.flac"),
         cicadas=os.path.join(OS, "raw", "cicadas_greece.ogg"),
         tide=os.path.join(OS, "raw", "tide_rocks.ogg"),
         splash=os.path.join(OS, "raw", "splashes.ogg"))
have = {k: os.path.exists(v) and os.path.getsize(v) > 1000 for k, v in F.items()}
used = {}

# ------------------------------------------------------------------ water stem
water = np.zeros((N, 2))
st = decode(F["stream"], 12.0, 30.0)                       # the soft, unbroken part of the CC0 stream recording
st = norm_rms(st - st.mean(0), -30.0)
water += loop_to(st, N)
used["stream"] = "stream.mp3 12.0-42.0 s, looped with 0.5 s crossfades, normalised to -30 dBFS RMS"
wenv = [(0, -40), (2.0, 0), (26.0, 0), (29.0, 3.5), (38.0, 4.5), (38.2, -9), (39.5, -9), (39.7, 0),
        (64.3, 0), (66.0, 3.0), (69.5, 3.0), (73.0, -40)]
water *= envelope(N, wenv)[:, None]
cue(0.0, "ambience", "water bed fades in under the title", "T", "FOR-AUD-STREAM", dur=2.0)
cue(26.0, "ambience", "water louder as the flood rises (L-S7/S8, +3.5..4.5 dB)", "L", "FOR-AUD-STREAM", dur=12.0)
cue(38.0, "ambience", "room-quiet water under the 'Plus tot' card (-9 dB)", "card", "FOR-AUD-STREAM", dur=1.5)
cue(64.3, "ambience", "water louder for C's last crossing (+3 dB)", "E", "FOR-AUD-STREAM", dur=5.2)
cue(69.5, "ambience", "water out over the comparison card", "cmp", "FOR-AUD-STREAM", dur=3.5)
# close water lapping at the plank foot in the two close retrievals
for v, t0 in (("L", 20.0), ("E", 50.0)):
    if have["tide"]:
        lap = decode(F["tide"], 6.0, 2.6); lap = norm_rms(lap - lap.mean(0), -27.0)
        used["tide"] = "tide_rocks.ogg 6.0-8.6 s"; src = "FOR-AUD-TIDE"
    else:
        lap = np.stack([M.band(M.noise(2.6), 150, 900) * 0.04] * 2, 1); src = "HM-SYN-LAP"
    lap *= np.r_[np.linspace(0, 1, 2200), np.ones(len(lap) - 4400), np.linspace(1, 0, 2200)][:, None]
    put(water, lap, t0, 1.0)
    cue(t0, "water", "close lap at the plank foot (S5 / E-S4 close)", v, src, dur=2.4)

# ------------------------------------------------------------------ jungle stem
jungle = np.zeros((N, 2))
if have["jungle"]:
    j = decode(F["jungle"], 3.0, 40.0); j = norm_rms(j - j.mean(0), -33.0); jungle += loop_to(j, N)
    used["jungle"] = "jungle_phuket.flac 3-43 s looped, -33 dBFS RMS"; jsrc = "FOR-AUD-JUNGLE"
    if have["cicadas"]:
        c = decode(F["cicadas"], 2.0, 24.0); c = norm_rms(c - c.mean(0), -42.0); jungle += loop_to(c, N)
        used["cicadas"] = "cicadas_greece.ogg 2-26 s looped, -42 dBFS RMS"
elif have["cicadas"]:
    c = decode(F["cicadas"], 2.0, 24.0); c = norm_rms(c - c.mean(0), -36.0); jungle += loop_to(c, N)
    used["cicadas"] = "cicadas_greece.ogg 2-26 s looped"; jsrc = "FOR-AUD-CICADAS"
else:
    # FALLBACK only while no foraged jungle/insect recording could be fetched (Commons upload host rate-limited):
    # insect bed synthesized with kit Mix, three cicada/cricket voices (AM tone clusters) and sparse distant chirps.
    t = np.arange(N) / RATE; jb = np.zeros(N)
    for f0, am, depth, g0 in ((4300, 38.0, 0.9, 0.5), (5650, 52.0, 0.8, 0.35), (3100, 6.5, 0.7, 0.3)):
        car = M.band(rs.normal(0, 1, N), f0 - 260, f0 + 260)
        swell = 0.6 + 0.4 * np.sin(2 * np.pi * rs.uniform(0.05, 0.12) * t + rs.uniform(0, 6))
        jb += g0 * car * (1 - depth + depth * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * am * t)))) * swell
    for _ in range(int(T_FILM * 0.6)):
        c = rs.uniform(0, T_FILM - 0.5); f = rs.uniform(2400, 3600); tt = np.arange(int(0.18 * RATE)) / RATE
        put_i = int(c * RATE); jb[put_i:put_i + len(tt)] += 0.6 * np.sin(2 * np.pi * f * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 30 * tt))) * np.exp(-tt * 12)
    jb = jb / (np.sqrt((jb ** 2).mean()) + 1e-12) * 10 ** (-38 / 20)
    jungle += np.stack([jb, np.roll(jb, 300)], 1)
    used["insects_fallback"] = "synthesized insect bed (kit Mix noise bands, AM), -38 dBFS RMS: stand-in until a foraged jungle recording is fetched"
    jsrc = "HM-SYN-INSECTS (fallback)"
# the declared insect silences: L film 21.4-22.0 (local 19.4-20.0) and the same local window in E (51.9-52.5)
SIL = [(21.4, 22.0, "L"), (51.9, 52.5, "E")]
jpts = [(0, -40), (1.0, -40), (2.6, 0), (37.6, 0), (38.0, -30), (39.5, -30), (40.1, 0), (69.5, 0), (72.0, -40), (73.0, -40)]
for a, b, v in SIL:
    jpts += [(a - 0.06, 0), (a, -60), (b, -60), (b + 0.12, 0)]
jpts.sort()
jungle *= envelope(N, jpts)[:, None]
for a, b, v in SIL:
    cue(a, "silence", "declared insect silence: the jungle stops while she takes the shoe", v, jsrc or "none", dur=b - a)
cue(2.0, "ambience", "jungle/insect bed (absent under title and cards)", "L+E", jsrc or "MISSING", dur=67.5)

# ------------------------------------------------------------------ foley stem (synthesized with kit Mix unless noted)
foley = np.zeros((N, 2))
def creak(load=1.0, seconds=0.32):
    """stick-slip of a wet plank: impulse train gliding 38->85 Hz through three wood modes."""
    n = int(seconds * RATE); t = np.arange(n) / RATE
    rate = 38 + 47 * (t / seconds) ** 0.7
    ph = np.cumsum(rate) / RATE; imp = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    imp *= 0.6 + 0.4 * rs.rand(n)
    out = np.zeros(n)
    for f, d, a in ((182, 0.035, 1.0), (413, 0.02, 0.6), (737, 0.012, 0.35), (1210, 0.008, 0.2)):
        k = np.arange(int(0.08 * RATE)) / RATE
        out += a * np.convolve(imp, np.sin(2 * np.pi * f * k) * np.exp(-k / d))[:n]
    out *= np.sin(np.pi * t / seconds) ** 0.6
    return out / (np.abs(out).max() + 1e-9) * 0.5 * load

def wood_step(load=1.0):
    n = int(0.12 * RATE); t = np.arange(n) / RATE
    x = M.band(M.noise(0.12), 90, 1600) * np.exp(-t * 45)
    x += 0.9 * np.sin(2 * np.pi * 96 * t) * np.exp(-t * 28) + 0.4 * np.sin(2 * np.pi * 231 * t) * np.exp(-t * 50)
    return x / (np.abs(x).max() + 1e-9) * 0.5 * load

def mud_step():
    n = int(0.16 * RATE); t = np.arange(n) / RATE
    x = M.band(M.noise(0.16), 60, 700) * np.exp(-t * 30) + 0.25 * M.band(M.noise(0.16), 900, 3000) * np.exp(-((t - 0.05) / 0.02) ** 2)
    return x / (np.abs(x).max() + 1e-9) * 0.25

def shoe_tap():
    """heel of a leather shoe knocking the wet plank foot: tap + rebound, a hollow 520 Hz body, a plip."""
    n = int(0.35 * RATE); t = np.arange(n) / RATE; x = np.zeros(n)
    for t0, a in ((0.0, 1.0), (0.105, 0.38)):
        tt = np.clip(t - t0, 0, None); on = (t >= t0)
        x += on * a * (np.sin(2 * np.pi * 520 * tt) * np.exp(-tt / 0.022) + 0.5 * np.sin(2 * np.pi * 1340 * tt) * np.exp(-tt / 0.009))
        x[int(t0 * RATE):int(t0 * RATE) + 300] += a * 0.6 * M.band(M.noise(300 / RATE), 400, 5000)
    tt = np.clip(t - 0.03, 0, None); x += (t > 0.03) * 0.25 * np.sin(2 * np.pi * (900 + 3000 * tt) * tt) * np.exp(-tt * 70)
    return x / (np.abs(x).max() + 1e-9) * 0.55

def card_rustle(seconds=0.7):
    """card on card: crackle grains in a 1.2-7 kHz band, bunched, plus the bag's soft landing."""
    n = int(seconds * RATE); x = np.zeros(n); t = np.arange(n) / RATE
    for _ in range(int(seconds * 60)):
        c = int(rs.beta(2, 2.5) * (n - 900)); L = rs.randint(120, 900)
        x[c:c + L] += rs.normal(0, 1, L) * np.exp(-np.arange(L) / (L / 3)) * rs.uniform(0.2, 1)
    x = M.band(x, 1200, 7000)
    x += 0.5 * np.sin(2 * np.pi * 105 * np.clip(t - 0.42, 0, None)) * np.exp(-np.clip(t - 0.42, 0, None) * 22) * (t > 0.42)
    return x / (np.abs(x).max() + 1e-9) * 0.35

def pencil(seconds, strokes_per_s=6.0, scratch=False):
    """graphite on card: stroke-shaped band noise; a strike-through is one long, harder, rising stroke."""
    n = int(seconds * RATE); t = np.arange(n) / RATE; env = np.zeros(n)
    if scratch:
        env = np.sin(np.pi * t / seconds) ** 0.4 * (0.8 + 0.2 * np.sin(2 * np.pi * 23 * t))
        x = M.band(M.noise(seconds), 1200, 6500)
    else:
        c = 0.0
        while c < seconds:
            L = rs.uniform(0.06, 0.22); a = rs.uniform(0.5, 1.0)
            m = (t >= c) & (t < c + L); env[m] = a * np.sin(np.pi * (t[m] - c) / L) ** 0.5
            c += L + rs.uniform(0.02, 1.0 / strokes_per_s)
        x = M.band(M.noise(seconds), 2200, 8000) + 0.3 * M.band(M.noise(seconds), 600, 1800)
    x *= env
    return x / (np.abs(x).max() + 1e-9) * (0.32 if scratch else 0.2)

def liana_creak():
    n = int(0.45 * RATE); t = np.arange(n) / RATE
    x = creak(0.6, 0.45) * 0.6 + 0.2 * M.band(M.noise(0.45), 300, 1200) * np.exp(-t * 6)
    return x

def plip():
    n = int(0.12 * RATE); t = np.arange(n) / RATE
    return 0.35 * np.sin(2 * np.pi * (700 + 2600 * t) * t) * np.exp(-t * 55)

def synth_splash():
    n = int(0.9 * RATE); t = np.arange(n) / RATE
    return M.band(M.noise(0.9), 200, 5000) * np.exp(-t * 6) * 0.4

PLX = (190.0, 690.0)
def pan_of(x): return float(np.clip((x - 400) / 420, -0.8, 0.8))

for v in ("L", "E"):
    tr = json.load(open(os.path.join(PERF, f"trace-{v}.json"))); fr = tr["frames"]; off = OFF[v]
    # footfalls: the walk is keyed so each ankle swings forward (+x, all crossings go N->F) and plants; a footfall is
    # a local maximum of ankle x (end of the forward swing) with >= 15 px of swing, while the root is travelling.
    for who in ("A", "B", "C"):
        for ai in (0, 1):
            xs = [f["people"][who]["ankles"][ai][0] for f in fr]
            last_i = -99
            for i in range(4, len(fr) - 4, 1):
                if i - last_i < 4: continue
                if not (xs[i] >= max(xs[i - 4:i]) and xs[i] > xs[i + 2] + 0.5 and xs[i] >= xs[i + 1]): continue
                if xs[i] - min(xs[max(0, i - 14):i]) < 15: continue
                r0 = fr[max(0, i - 6)]["people"][who]["root"][0]; r1 = fr[min(len(fr) - 1, i + 6)]["people"][who]["root"][0]
                if abs(r1 - r0) < 6: continue
                last_i = i
                t = fr[i]["t"]; x = xs[i]; bank = fr[i]["people"][who]["bank"]
                on_plank = bank == "P" and PLX[0] - 5 <= x <= PLX[1] + 5
                defl = fr[i].get("plank_deflection_px", 0.0) or 0.0
                if on_plank:
                    load = 0.6 + 0.4 * min(defl / 9.0, 1.0)
                    put(foley, wood_step(load), off + t, 0.8, pan_of(x))
                    put(foley, creak(load), off + t + 0.03, 0.55, pan_of(x))
                    cue(off + t, "foley", f"{who} step on the plank + creak (deflection {defl:.1f} px)", v, "HM-SYN-CREAK", dur=0.35)
                else:
                    put(foley, mud_step(), off + t, 0.5, pan_of(x))
                    cue(off + t, "foley", f"{who} step on the {bank} bank (mud)", v, "HM-SYN-MUD", dur=0.16)
    # liana grips: a fibre creak
    for e in tr["events"]:
        if e["event"] == "grip" and e["obj"] == "liana":
            put(foley, liana_creak(), off + e["t"], 0.5, -0.1)
            cue(off + e["t"], "foley", f"{e['who']} takes the liana: fibre creak", v, "HM-SYN-LIANA", dur=0.45)
        if e["event"] == "handoff" and e["obj"] == "bag":
            put(foley, card_rustle(), off + e["t"] - 0.15, 1.0, -0.35)
            cue(off + e["t"] - 0.15, "foley", f"bag hand-off {e['frm']}->{e['to']}: card rustle + soft landing", v, "HM-SYN-RUSTLE", dur=0.7)
        if e["event"] == "retrieve":
            put(foley, plip(), off + e["t"] + 0.02, 0.8, -0.4)
            cue(off + e["t"], "foley", "fingers close on the heel: the shoe leaves the water (plip)", v, "HM-SYN-PLIP", dur=0.12)
    # the shoe: tap on the plank foot (3.6 s after first appearance), drips after the lift (layer rings k 139/143/148)
    t0 = {"L": 14.0, "E": 7.0}[v]
    put(foley, shoe_tap(), off + t0 + 3.6, 1.0, -0.45)
    cue(off + t0 + 3.6, "foley", "the shoe's hollow tap on the plank foot (layer frame 86)", v, "HM-SYN-TAP", dur=0.35)
    for kk in (139, 143, 148):
        put(foley, plip(), off + t0 + kk / 24, 0.45, -0.4)
        cue(off + t0 + kk / 24, "foley", f"drip from the lifted shoe (layer frame {kk})", v, "HM-SYN-PLIP", dur=0.12)
    # splash: the last crosser's minimum clearance frame (the plank dips into the water)
    last = {"L": "B", "E": "C"}[v]
    best = None
    for f in fr:
        if f.get("plank_occupant") == [last]:
            c = f["water_y"] - (392 + f.get("plank_deflection_px", 0))
            if best is None or c < best[0]: best = (c, f["t"], f["people"][last]["root"][0])
    if best:
        if have["splash"]:
            sp = decode(F["splash"], 3.2, 1.2); sp = norm_rms(sp - sp.mean(0), -20.0)
            sp *= np.r_[np.ones(len(sp) - 8000), np.linspace(1, 0, 8000)][:, None]
            used["splash"] = "splashes.ogg 3.2-4.4 s"; ssrc = "FOR-AUD-SPLASH"
        else:
            sp = synth_splash(); ssrc = "HM-SYN-SPLASH"
        put(foley, sp, off + best[1] - 0.05, 1.0, pan_of(best[2]))
        cue(off + best[1] - 0.05, "foley", f"splash on {last}'s shins at the plank's lowest (clearance {best[0]:.1f} px)", v, ssrc, dur=1.1)

# pencil: ledger writing (L-S2 / E-S2: A writes local 3.0-5.6), strike + rewrite (L local 21.5-23.5, E-S5 film 52.4-54.5)
for v, a, b in (("L", 5.0, 7.6), ("E", 42.5, 45.1)):
    put(foley, pencil(b - a), a, 1.0, -0.2)
    cue(a, "foley", "pencil writing the ledger « 1 A · 2 B (sac) · 3 C »", v, "HM-SYN-PENCIL", dur=b - a)
for v, a, b in (("L", 23.5, 25.5), ("E", 52.4, 54.5)):
    put(foley, pencil(0.33, scratch=True), a, 1.0, 0.0)
    cue(a, "foley", "pencil strike-through of the old line (8 frames)", v, "HM-SYN-SCRATCH", dur=0.33)
    put(foley, pencil(b - a - 0.5), a + 0.45, 1.0, 0.0)
    cue(a + 0.45, "foley", "pencil rewriting the order", v, "HM-SYN-PENCIL", dur=b - a - 0.5)
put(foley, pencil(1.2) * 0.6, 0.4, 1.0, 0.0); cue(0.4, "foley", "pencil on the title card", "T", "HM-SYN-PENCIL", dur=1.2)
put(foley, pencil(2.4) * 0.6, 70.0, 1.0, 0.0); cue(70.0, "foley", "pencil underlining the last crossers on the comparison card", "cmp", "HM-SYN-PENCIL", dur=2.4)

# ------------------------------------------------------------------ write stems
def write(path, x):
    y = np.clip(x, -1, 1); d = (y * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(d.tobytes())

os.makedirs(os.path.join(OS, "stems"), exist_ok=True)
mix = water * 1.0 + jungle * 0.85 + foley * 0.9
peak = np.abs(mix).max(); g = min(1.0, 0.89 / peak)
for name, x in (("water", water * g), ("jungle", jungle * 0.85 * g), ("foley", foley * 0.9 * g), ("mix", mix * g)):
    write(os.path.join(OS, "stems", f"{name}.wav"), x)

def rms_db(x, a, b): s = x[int(a * RATE):int(b * RATE)]; return round(20 * math.log10(np.sqrt((s ** 2).mean()) + 1e-12), 1)
cues.sort(key=lambda c: c["film_t"])
json.dump(dict(timeline="film seconds, 0-73.0 (L local + 2.0, E local + 39.5)", rate=RATE, stem_gain=g, have=have, used=used,
               check=dict(jungle_rms_db_in_L_silence=rms_db(jungle, 21.5, 21.9), jungle_rms_db_before=rms_db(jungle, 20.5, 21.3),
                          jungle_rms_db_in_E_silence=rms_db(jungle, 52.0, 52.4), mix_peak=round(float(np.abs(mix * g).max()), 3)),
               cues=cues), open(os.path.join(OS, "stems", "cues.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(dict(have=have, n_cues=len(cues), g=g)))
