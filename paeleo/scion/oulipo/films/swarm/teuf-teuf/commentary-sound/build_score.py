"""teuf-teuf COMMENTARY-SOUND unit: dual-column score and event-locked sound stems.

Reads exposure.json (sim.py's per-frame sheet and event list) and maps every
sim event to one sound. Foraged recordings are decoded with ffmpeg only (never
executed), cut at detected onsets and re-timed to the sim; anything with no
licensed recording is synthesised with kit.Mix and declared as such.

Outputs
  films/sources/teuf-teuf/sound/stem-*.wav      44.0 s stereo stems, film time 0 = sample 0,
                                                 one shared gain, so the stems sum to mix.wav
  films/sources/teuf-teuf/sound/mix.wav          the full bed
  films/sources/teuf-teuf/commentary-sound/      decoded foraged sources, cut samples,
                                                 captions (fr/en .srt + captions.json), spectrogram
  films/swarm/teuf-teuf/score.json, score.md     the dual-column score with evidence

Run: python3 build_score.py   (from anywhere)
"""
import json, math, os, subprocess, sys, wave
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SWARM = HERE.parent                                   # films/swarm/teuf-teuf
FILMS = SWARM.parent.parent                           # films/
sys.path.insert(0, str(FILMS))
import kit                                            # noqa: E402  (read-only use)

SRC = FILMS / "sources" / "teuf-teuf"
RAW = SRC / "sound" / "raw"
STEMS = SRC / "sound"
PREP = SRC / "commentary-sound"
PREP.mkdir(parents=True, exist_ok=True)
RATE = kit.RATE
DUR = 44.0
SEED = 4242

EXP = json.load(open(SWARM / "exposure.json"))
EV = EXP["events"]
FR = EXP["frames"]
FPS = EXP["constants"]["fps"]
CAMB = EXP["constants"]["close_up"]


# --------------------------------------------------------------- sources ---
# EDITOR NOTE (repair 1): the film's own sound is built in films/teuf-teuf.py from the cut-*.wav
# files and stem-room.wav only; it never reads sound/raw/. The wagon, quern, thud and Pasos entries
# below were never downloaded and are NOT in the film. If they are ever fetched, they must be added
# to films/credits/teuf-teuf.json and to the end line before any use.
FORAGED = {
    "knock": dict(
        file=SRC / "test-shot" / "knock.ogg",
        title="File:Knocking on wood or door.ogg", author="stephan (via PDSounds)",
        license="Public domain", license_url="",
        source_url="https://commons.wikimedia.org/wiki/File:Knocking_on_wood_or_door.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/1/1c/Knocking_on_wood_or_door.ogg",
        what_it_shows="three groups of three knuckle knocks on a wooden door, close-miked, quiet room (6.2 s, mono 44.1 kHz)",
        verified="Commons extmetadata read 2026-11-16 by the test-shot unit: LicenseShortName 'Public domain', Artist 'stephan', Credit pdsounds.org; reused, not re-downloaded"),
    "wagon": dict(
        file=RAW / "WWS_Woodenwagon.ogg",
        title="File:WWS Woodenwagon.ogg", author="Work With Sounds / Museum of Municipal Engineering (Kraków)",
        license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:WWS_Woodenwagon.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/a/a9/WWS_Woodenwagon.ogg",
        what_it_shows="a wooden-wheeled farm wagon rolling on pavement, recorded 2015-06-25 at the National Museum of Agriculture, Szreniawa, Poland (16.4 s)",
        verified="Commons extmetadata read 2026-11-16: LicenseShortName 'CC BY 4.0', Artist 'Work With Sounds / Museum of Municipal Engineering', DateTimeOriginal 2015-06-25, Szreniawa (Poland)"),
    "quern": dict(
        file=RAW / "WWS_Quern-stones.ogg",
        title="File:WWS Quern-stones.ogg", author="Work With Sounds / Museum of Municipal Engineering (Kraków)",
        license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:WWS_Quern-stones.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/e/ef/WWS_Quern-stones.ogg",
        what_it_shows="a hand quern: an upper stone turned on a lower stone, grinding grain; stone-on-stone grit, recorded 2015-06-25 at the National Museum of Agriculture, Szreniawa, Poland (57.5 s)",
        verified="Commons extmetadata read 2026-11-16: LicenseShortName 'CC BY 4.0', Artist 'Work With Sounds / Museum of Municipal Engineering', DateTimeOriginal 2015-06-25, Szreniawa (Poland)"),
    "thud": dict(
        file=RAW / "Dull_thud.ogg",
        title="File:Dull thud.ogg", author="gregoryweir (via PDSounds)",
        license="Public domain", license_url="",
        source_url="https://commons.wikimedia.org/wiki/File:Dull_thud.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/5/5b/Dull_thud.ogg",
        what_it_shows="one dull impact (PDSounds tags: thud, blow, footstep, hit, impact), 0.4 s",
        verified="Commons extmetadata read 2026-11-16: LicenseShortName 'Public domain', Artist 'gregoryweir', Credit pdsounds.org/audio/download/770, DateTimeOriginal 2009-07-04"),
    "gravel": dict(
        file=RAW / "Footstep_on_Gravel_(Gravity_Sound).mp3",
        title="File:Footstep on Gravel (Gravity Sound).mp3", author="Gravity Sound",
        license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Footstep_on_Gravel_(Gravity_Sound).mp3",
        file_url="https://upload.wikimedia.org/wikipedia/commons/f/f7/Footstep_on_Gravel_%28Gravity_Sound%29.mp3",
        what_it_shows="a single footstep on gravel, 0.6 s",
        verified="Commons extmetadata read 2026-11-16 (this unit): LicenseShortName 'CC BY 4.0', Artist 'Gravity Sound' (gravitysound.studio), size 12142 B; local copy taken read-only from films/sources/la-cite-raymond-queneau/sound-A/raw/ (same size as Commons; re-download blocked by upload.wikimedia.org 429)"),
    "stairs": dict(
        file=RAW / "Pasos_en_escalera_de_caracol.ogg",
        title="File:Pasos en escalera de caracol.ogg", author="Hippocampuz",
        license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
        source_url="https://commons.wikimedia.org/wiki/File:Pasos_en_escalera_de_caracol.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/0/0a/Pasos_en_escalera_de_caracol.ogg",
        what_it_shows="footsteps going up and down a spiral staircase (18.0 s), own work, 2022-08-24",
        verified="Commons extmetadata read 2026-11-16: LicenseShortName 'CC BY-SA 4.0', Artist 'Hippocampuz', Credit 'Own work', DateTimeOriginal 2022-08-24"),
    "steps": dict(
        file=RAW / "Concrete_Steps_2.ogg",
        title="File:Concrete Steps 2.ogg", author="Pwaivers",
        license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
        source_url="https://commons.wikimedia.org/wiki/File:Concrete_Steps_2.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/b/bf/Concrete_Steps_2.ogg",
        what_it_shows="real footsteps on concrete steps (short recording, a few hard-soled steps)",
        verified="Commons extmetadata CC BY-SA 3.0, Artist 'Pwaivers', read 2026-11-16 by the renzo-e-luciana review unit; local copy taken read-only from films/sources/renzo-e-luciana/sound/raw/, sha1 1631ce7f8efee24124fc48e56c597719235b7abb matches the sha1 that unit checked against Commons (re-download blocked by upload.wikimedia.org 429)"),
    "church": dict(
        file=RAW / "Church_people_walking_steps_with_reverb.ogg",
        title="File:Church people walking steps with reverb.ogg", author="stephan (via PDSounds)",
        license="Public domain", license_url="",
        source_url="https://commons.wikimedia.org/wiki/File:Church_people_walking_steps_with_reverb.ogg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/d/d5/Church_people_walking_steps_with_reverb.ogg",
        what_it_shows="people walking in a large reverberant stone church; low-passed it is the air of a big stone room",
        verified="Commons extmetadata 'Public domain', Artist 'stephan', read 2026-11-16 by the renzo-e-luciana sound unit; local copy taken read-only from films/sources/renzo-e-luciana/sound/raw/, sha1 8b2a6abb78bad2c5def0ab4496c4330472601445 matches the sha1 that unit checked against Commons"),
}


def decode(key):
    """ffmpeg-decode a foraged file to mono 44.1 kHz wav in PREP; return float array or None."""
    src = FORAGED[key]["file"]
    if not src.exists():
        return None
    out = PREP / f"src-{key}.wav"
    if not out.exists():
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src), "-ac", "1",
                        "-ar", str(RATE), "-sample_fmt", "s16", str(out)], check=True)
    w = wave.open(str(out))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    FORAGED[key]["local_path"] = str(src.relative_to(FILMS.parent))
    FORAGED[key]["decoded"] = str(out.relative_to(FILMS.parent))
    FORAGED[key]["used"] = True
    return x


def onsets(x, thr_db=-32, jump=8, hop_s=0.005, min_gap=0.08):
    hop = int(RATE * hop_s)
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(e + 1e-9)
    out = []
    for i in range(2, len(db)):
        if db[i] > thr_db and db[i] - db[i - 2] > jump:
            if not out or (i * hop_s - out[-1]) > min_gap:
                out.append(i * hop_s)
    return out


def cut(x, t, dur, pre=0.004):
    a = max(0, int((t - pre) * RATE)); b = min(len(x), a + int(dur * RATE))
    s = x[a:b].copy()
    n = len(s); f = min(n // 4, int(0.012 * RATE))
    if f > 0:
        s[-f:] *= np.linspace(1, 0, f)
    s[: int(pre * RATE)] *= np.linspace(0, 1, int(pre * RATE))
    return s / (np.abs(s).max() + 1e-9)


def resample(s, rate):
    """Play back at `rate` (0.7 = slower and lower)."""
    n = int(len(s) / rate)
    return np.interp(np.arange(n) * rate, np.arange(len(s)), s)


def varispeed(s, r, n):
    """Read through loop `s` with a time-varying speed r[k] (per output sample)."""
    pos = np.cumsum(r) % (len(s) - 1)
    return np.interp(pos, np.arange(len(s)), s)


# ------------------------------------------------------------ sim curves ---
def frame_series(fn):
    return np.array([fn(f) for f in FR], np.float64)


TF = np.array([f["t"] for f in FR])


def omega_logs(states=("carried", "free")):
    th = {k: frame_series(lambda f, k=k: f["logs"][k].get("theta", np.nan) if f["logs"][k].get("state") in states else np.nan)
          for k in "ABCD"}
    tot = np.zeros(len(FR))
    for k, a in th.items():
        d = np.abs(np.diff(a, prepend=a[0])) * FPS
        tot += np.nan_to_num(d)
    return tot


def omega_log(k):
    a = frame_series(lambda f: f["logs"][k].get("theta", np.nan) if f["logs"][k].get("state") in ("free",) else np.nan)
    return np.nan_to_num(np.abs(np.diff(a, prepend=a[0])) * FPS)


def omega_wheels(states=("axle", "loose", "free")):
    tot = np.zeros(len(FR))
    for w in ("rear", "front"):
        a = frame_series(lambda f, w=w: f["cart"]["wheels"][w]["theta"] if f["cart"] and f["cart"]["wheels"][w]["state"] in states else np.nan)
        tot += np.nan_to_num(np.abs(np.diff(a, prepend=a[0])) * FPS)
    return tot


def load_speed():
    return frame_series(lambda f: abs(f["load"]["v_px_s"]))


def to_audio(series, t0=0.0, t1=DUR):
    ta = np.arange(int(t0 * RATE), int(t1 * RATE)) / RATE
    return np.interp(ta, TF, series, left=0, right=0)


def mask(series, t0, t1):
    s = series.copy(); s[(TF < t0) | (TF > t1)] = 0; return s


def pan_x(x, t):
    """World x -> stereo pan; the close-up scales about its centre."""
    if CAMB["t"][0] <= t < CAMB["t"][1]:
        x = 640 + (x - 300) * CAMB["scale"]
    return float(np.clip((x - 640) / 700, -0.85, 0.85))


def frame_at(t):
    return FR[min(len(FR) - 1, max(0, int(round(t * FPS))))]


# ------------------------------------------------------------- the score ---
def build():
    rng = np.random.RandomState(SEED)
    stems = {k: kit.Mix(DUR, seed=SEED + i) for i, k in enumerate(
        ["room", "steps", "scrape", "knocks", "rumble", "impacts", "scratch"])}
    cues = []                       # one record per sound event

    def cue(t, event, sound, source, stem, kind="sim"):
        cues.append(dict(t=round(t, 3), event=event, sound=sound, source=source, stem=stem, kind=kind))

    knock_x = decode("knock"); wagon = decode("wagon"); quern = decode("quern")
    thud = decode("thud"); gravel = decode("gravel"); stairs = decode("stairs")
    concrete = decode("steps"); church = decode("church")

    # single knocks cut from the PD recording
    knocks = []
    if knock_x is not None:
        for t in onsets(knock_x)[:12]:
            knocks.append(cut(knock_x, t, 0.20))
    for i, k in enumerate(knocks):
        _wav(PREP / f"cut-knock-{i}.wav", k)

    def wood(at, rate=0.72, gain=0.5, pan=0.0, i=0, decay=10.0):
        if knocks:
            s = resample(knocks[i % len(knocks)], rate)
            s = s * np.exp(-np.arange(len(s)) / RATE * decay)
            stems["knocks"].add(s, at, gain, pan)
            return "FORAGED knock (PD) x%.2f" % rate
        stems["knocks"].step(at, gain, pan, "wood"); return "SYNTH kit step(wood)"

    def impact(at, gain=0.5, pan=0.0, rate=0.8, low=True):
        if thud is not None:
            s = resample(thud / (np.abs(thud).max() + 1e-9), rate)
            if low:
                s = stems["impacts"].lowpass(s, 900)
            stems["impacts"].add(s, at, gain, pan)
            return "FORAGED dull thud (PD) x%.2f" % rate
        m = stems["impacts"]; sec = 0.45 * (1 / rate)
        tt = m.t(sec); fq = 70 * rate * (1 + 1.2 * np.exp(-tt * 30))
        sig = np.sin(2 * np.pi * np.cumsum(fq) / RATE) * np.exp(-tt * 11)
        sig += 0.35 * m.lowpass(m.rs.normal(0, 1, len(tt)), 600 * rate) * np.exp(-tt * 35)
        sig[: int(0.003 * RATE)] *= np.linspace(0, 1, int(0.003 * RATE))
        m.add(sig / (np.abs(sig).max() + 1e-9), at, gain, pan)
        return "SYNTH low thud (sine drop + low-passed noise, no click)"

    # footstep bank: stone stair steps (CC BY-SA) and the gravel step (CC BY)
    steps = []
    if concrete is not None:
        for t in onsets(concrete, thr_db=-40, jump=7, min_gap=0.18)[:12]:
            steps.append(cut(concrete, t, 0.16))
    if stairs is not None:
        for t in onsets(stairs, thr_db=-38, jump=7, min_gap=0.18)[:24]:
            s = cut(stairs, t, 0.16)
            steps.append(s)
    gravel_s = cut(gravel, onsets(gravel, thr_db=-45, jump=6)[0] if gravel is not None and onsets(gravel, thr_db=-45, jump=6) else 0, 0.30) if gravel is not None else None
    for i, s in enumerate(steps[:8]):
        _wav(PREP / f"cut-step-stone-{i}.wav", s)
    if gravel_s is not None:
        _wav(PREP / "cut-step-gravel.wav", gravel_s)

    def footstep(at, who, x, k):
        g = 0.20 if who == "P" else 0.15
        p = pan_x(x, at)
        if steps:
            s = steps[k % len(steps)]
            s = resample(s, 0.92 + 0.08 * rng.rand())
            src = "FORAGED hard-soled step on concrete/stone (CC BY-SA)"
            if gravel_s is not None and k % 3 == 2:          # a little grit under every third step
                stems["steps"].add(stems["steps"].band(resample(gravel_s, 0.9), 200, 6000), at, g * 0.35, p)
                src += " + gravel grit (CC BY 4.0)"
            stems["steps"].add(s, at + rng.uniform(-0.006, 0.006), g, p)
            return src
        if gravel_s is not None:
            stems["steps"].add(resample(gravel_s, 0.85 + 0.1 * rng.rand()), at, g, p)
            return "FORAGED gravel step (CC BY 4.0)"
        stems["steps"].step(at, g, p, "stone"); return "SYNTH kit step(stone)"

    # ---------- room: no licensed cave ambience found -> kit room, no mains hum
    if church is not None:
        m = stems["room"]
        bed = m.lowpass(church - church.mean(), 220)
        reps = int(math.ceil(DUR * RATE / len(bed))) + 1
        bed = np.tile(bed, reps)[: int(DUR * RATE)]
        bed = bed / (np.percentile(np.abs(bed), 99) + 1e-9)
        m.add(bed * m.env(len(bed), 1.2, 0.01, 1.0, 1.0), 0.0, 0.05, 0.0)
        m.room(0.0, DUR, gain=0.012, hum=0)
        cue(0.0, "room tone 0-44 s", "air of a big stone room (no cave ambience under an allowed licence was found)",
            "FORAGED church walking-with-reverb (PD), low-passed 220 Hz so no steps or voices survive, + SYNTH kit room(hum=0) air", "room", "bed")
    else:
        stems["room"].room(0.0, DUR, gain=0.028, hum=0)
        cue(0.0, "room tone 0-44 s", "pink air, no hum (cave ambience searched, none licensed)", "SYNTH kit Mix.room(hum=0)", "room", "bed")

    # ---------- title write-on scratch (0.4-1.6 s) and the scratches of ghosts, cuts, end line
    def scratch(at, dur, gain=0.05, pan=0.0):
        m = stems["scratch"]
        n = m.noise(dur)
        strokes = np.abs(np.sin(np.linspace(0, math.pi * max(2, dur * 7), len(n)))) ** 4   # separate strokes with gaps
        grit = (m.rs.rand(len(n)) < 0.08) * m.rs.normal(0, 1, len(n))                      # sparse grains, not a hiss
        s = (m.band(grit, 1800, 7000) + 0.25 * m.band(n, 3000, 6000)) * strokes * m.env(len(n), 0.01, dur * 0.6, 0.4, dur * 0.3)
        m.add(s / (np.abs(s).max() + 1e-9), at, gain * 0.5, pan)
    scratch(0.4, 1.2, 0.04)
    cue(0.4, "title 'Teuf-teuf' scratches on (stroke order, 1.2 s)", "chalk-like scratch strokes", "SYNTH band-passed noise", "scratch", "picture")

    # ---------- footsteps: one per IK foot plant
    for k, ff in enumerate(EXP["footfalls"]):
        src = footstep(ff["t"], ff["who"], ff["x"], k)
        cue(ff["t"], f"foot plant {ff['who']} foot {ff['foot']} at x={ff['x']}", "footstep", src, "steps", "footfall")

    # ---------- the sim's event list, one sound each
    v = load_speed()
    for e in EV:
        t, kind = e["t"], e["kind"]
        f = frame_at(t); xs = f["load"]["xb"] + 125
        p = pan_x(xs, t)
        if kind == "push-start":
            s = impact(t, 0.10, p, 1.4)
            cue(t, e["event"], "palms meet the stone (soft, high)", s, "impacts")
        elif kind == "slip":
            # scrape: quern grit read at a speed that follows the stone's real speed in the slip
            a, b = t - 0.01, e["end"] + 0.06
            sp = to_audio(mask(v, a, b), a, b)
            sp = sp / (np.abs(v[(TF > 4.5) & (TF < 11.5)]).max() + 1e-9)
            n = len(sp)
            if quern is not None:
                loop = stems["scrape"].band(quern[int(5 * RATE):int(45 * RATE)], 120, 6500)
                start = rng.randint(0, len(loop) - n * 2 - 1)
                s = varispeed(loop[start:], 0.55 + 0.6 * sp, n) * np.sqrt(sp)
                src = "FORAGED quern stone-on-stone grind (CC BY 4.0), varispeed = stone speed"
            else:
                s = stems["scrape"].band(stems["scrape"].rs.normal(0, 1, n), 200, 5000) * sp
                src = "SYNTH grit noise x stone speed"
            stems["scrape"].add(s / (np.abs(s).max() + 1e-9), a, 0.32, p)
            cue(t, e["event"], f"scrape {b - a:.2f} s, level and grain rate follow v(t)", src, "scrape")
        elif kind == "stick":
            cue(t, e["event"], "the scrape cuts off (silence holds the stick)", "absence of the slip scrape", "scrape")
        elif kind == "stop" and "drag" in e["event"]:
            s = impact(t, 0.45, p, 0.7)
            cue(t, e["event"], "low thud, the stone sits", s, "impacts")
        elif kind == "ghost":
            scratch(t, 0.7, 0.045, p)
            cue(t, e["event"], "faint scratch as the ghost outline is drawn", "SYNTH band-passed noise", "scratch")
        elif kind == "cut":
            scratch(t - 0.05, 0.3, 0.05, 0.0)
            cue(t, e["event"], "one quick scratch stroke under the white wipe", "SYNTH band-passed noise", "scratch")
        elif kind == "lever":
            s = wood(t, 0.55, 0.30, p, i=0, decay=14)
            cue(t, e["event"], "low wood creak-knock as the lever bites", s, "knocks")
        elif kind == "log-land":
            lx = frame_at(t + 0.1)["logs"][e["log"]].get("x", xs)
            s = wood(t, 0.74 + 0.04 * "ABC".index(e["log"]), 0.55, pan_x(lx, t), i="ABC".index(e["log"]))
            cue(t, e["event"], "wooden knock (log lands)", s, "knocks")
        elif kind == "settle":
            s = impact(t, 0.30, p, 0.9)
            cue(t, e["event"], "soft settle thud", s, "impacts")
        elif kind == "release":
            cue(t, e["event"], "small dry roll of log A, level follows its own angular speed (in the rumble stem)", "see rumble", "rumble")
        elif kind == "foot-lift":
            cue(t, e["event"], "the lead foot's re-plant step (in the footstep list)", "see steps", "steps")
        elif kind == "log-stop":
            lx = e["x"]
            s = wood(t, 0.66, 0.70, pan_x(lx, t), i=3, decay=8)
            wood(t + 0.085, 0.70, 0.18, pan_x(lx, t), i=4, decay=16)      # rebound on the facet
            cue(t, e["event"], "TOK: wood on stone, one small rebound", s, "knocks")
        elif kind == "pickup":
            s = wood(t, 0.95, 0.15, pan_x(f["logs"]["D"].get("x", 700), t), i=5, decay=20)
            cue(t, e["event"], "light wood knock, hands take the log", s, "knocks")
        elif kind == "stop" and "1.5 m" in e["event"]:
            cue(t, e["event"], "the rumble falls to zero with the logs' angular speed", "see rumble", "rumble")
        elif kind in ("carry-start", "carry-end"):
            cue(t, e["event"], "window mark only: heard through pickup / set-down / push", "none", "-")
        elif kind == "log-set":
            s = wood(t, 0.62, 0.55, pan_x(e["x"], t), i=6, decay=9)
            cue(t, e["event"], "wood set down on stone", s, "knocks")
        elif kind == "capture":
            s = wood(t, 0.80, 0.30, p + 0.15, i=7, decay=14)
            cue(t, e["event"], "short knock as the nose rides onto log D", s, "knocks")
        elif kind == "stop" and "3.0 m" in e["event"]:
            s = impact(t, 0.30, p, 0.85)
            cue(t, e["event"], "soft thud; the rumble falls away", s, "impacts")
        elif kind == "pass-3m":
            cue(t, e["event"], "no contact: the caption is the event's voice", "none (caption cue)", "-")
        elif kind == "stop" and "8.0 m" in e["event"]:
            s = impact(t, 0.25, p, 0.75)
            cue(t, e["event"], "the wagon rumble decays; small low thud as the cart halts", s, "impacts")
        elif kind == "pin-pull":
            if knocks:
                s = stems["knocks"].band(resample(knocks[8 % len(knocks)], 1.35), 1200, 9000)[: int(0.06 * RATE)]
                stems["knocks"].add(s / (np.abs(s).max() + 1e-9), t, 0.35, p)
                src = "FORAGED knock (PD) x1.35, high-passed, 60 ms"
            else:
                stems["knocks"].click(t, 0.3, p); src = "SYNTH kit click"
            wood(t + 0.32, 0.85, 0.18, p, i=2, decay=18)                   # the beam lifting off its seat
            cue(t, e["event"], "the pin's click (and a light knock as the beam lifts)", src, "knocks")
        elif kind == "wheel-drop":
            wx = f["cart"]["wheels"]["rear"]["x"]
            s = wood(t, 0.58, 0.50, pan_x(wx, t), i=1, decay=9)
            cue(t, e["event"], "the wheel runs off the platform end: heavy wood knock", s, "knocks")
        elif kind == "wheel-stop":
            wx = f["cart"]["wheels"]["rear"]["x"]
            s = wood(t, 0.70, 0.22, pan_x(wx, t), i=4, decay=14)
            cue(t, e["event"], "small tok as the fallen wheel stops", s, "knocks")
        elif kind == "platform-drop":
            s = impact(t, 0.60, p, 0.65)
            a, b = t, 36.825 + 0.05
            sp = to_audio(mask(v, a, b), a, b); sp = sp / (sp.max() + 1e-9)
            n = len(sp)
            if quern is not None:
                loop = stems["scrape"].band(quern[int(20 * RATE):int(50 * RATE)], 80, 5000)
                g = varispeed(loop, 0.45 + 0.5 * sp, n) * sp
                src2 = "FORAGED quern grind (CC BY 4.0), varispeed = platform speed"
            else:
                g = stems["scrape"].band(stems["scrape"].rs.normal(0, 1, n), 100, 3000) * sp; src2 = "SYNTH"
            stems["scrape"].add(g / (np.abs(g).max() + 1e-9), a, 0.42, p)
            cue(t, e["event"], "THUD, then a grinding scrape until the stop", s + " ; " + src2, "impacts+scrape")
        elif kind == "stop" and "wheel-less" in e["event"]:
            s = impact(t, 0.35, p, 0.6)
            cue(t, e["event"], "the grind ends in a short low thud", s, "impacts")
        elif kind == "sit":
            lx = f["logs"]["A"]["x"]
            s = wood(t, 0.66, 0.55, pan_x(lx, t), i=3, decay=8)
            wood(t + 0.23, 0.70, 0.16, pan_x(lx, t), i=4, decay=16)      # rocks back once (logA_rock spring)
            cue(t, e["event"], "final TOK of the forgotten log, and its one rock back", s, "knocks")
        elif kind == "end-line":
            scratch(t, 1.4, 0.035, 0.3)
            cue(t, e["event"], "faint scratch as the source line writes on", "SYNTH band-passed noise", "scratch")
        else:
            cue(t, e["event"], "UNMAPPED", "-", "-")

    # ---------- rumble stem: logs (rollers) and wheels, level and grain rate follow angular speed
    wl = omega_logs(("carried",))
    wa = omega_log("A")
    ww = omega_wheels()
    m = stems["rumble"]
    n = int(DUR * RATE)
    w_roll = to_audio(wl); w_a = to_audio(wa); w_wh = to_audio(ww)
    def norm(a):
        return a / (a.max() + 1e-9)
    if wagon is not None:
        bed = m.band(wagon, 40, 2500)
        roll_tex = varispeed(m.lowpass(bed, 700), 0.45 + 0.55 * norm(w_roll), n)
        roll_src = "FORAGED wooden wagon on pavement (CC BY 4.0), low-passed 700 Hz, varispeed = log angular speed"
        a_tex = varispeed(m.band(bed, 150, 2500), 0.6 + 0.6 * norm(w_a), n)
        wh_tex = varispeed(bed, 0.35 + 0.75 * norm(w_wh), n)
        wh_src = "FORAGED wooden wagon on pavement (CC BY 4.0), varispeed = wheel angular speed"
    else:
        roll_tex = m.lowpass(m.noise(DUR, "brown"), 160); a_tex = m.band(m.noise(DUR), 300, 2500)
        wh_tex = m.lowpass(m.noise(DUR, "brown"), 220)
        roll_src = wh_src = "SYNTH low rumble"
    def nz(a):
        return a / (np.percentile(np.abs(a), 99.5) + 1e-9)
    m.add(nz(roll_tex) * np.sqrt(norm(w_roll)), 0.0, 0.30, -0.1)
    m.add(nz(a_tex) * np.sqrt(norm(w_a)), 0.0, 0.20, pan_x(60, 16.5))
    m.add(nz(wh_tex) * np.sqrt(norm(w_wh)), 0.0, 0.34, 0.1)
    for a, b, what in [(14.0, 16.95, "rollers rumble (logs A, B, C carried)"), (21.0, 23.0, "rollers rumble (B, C, D)")]:
        cue(a, f"{what} {a}-{b} s", "low wooden rumble, level and grain rate follow the carried logs' |dθ/dt|", roll_src, "rumble", "continuous")
    cue(16.254, "log A free roll 16.25-16.84 s", "small dry roll following log A's own |dθ/dt|", roll_src.replace("low-passed 700 Hz", "band 150-2500 Hz"), "rumble", "continuous")
    cue(26.0, "wheel trial rumble 26.0-33.0 s", "axle-and-wheel rumble, level and grain rate follow the wheels' |dθ/dt|", wh_src, "rumble", "continuous")
    cue(35.3, "counter-check loose wheels 35.3-36.8 s", "loose wheels rolling free at v/2", wh_src, "rumble", "continuous")

    # plank knock once per wheel turn: theta crosses 2πk (both wheels share theta; seam at 0 rad)
    th = frame_series(lambda f: f["cart"]["wheels"]["rear"]["theta"] if f["cart"] and f["cart"]["wheels"]["rear"]["state"] == "axle" else np.nan)
    turns = []
    for i in range(1, len(th)):
        a, b = th[i - 1], th[i]
        if np.isnan(a) or np.isnan(b) or b <= a:
            continue
        ka, kb = math.floor(a / (2 * math.pi)), math.floor(b / (2 * math.pi))
        if kb > ka:
            tc = TF[i - 1] + (TF[i] - TF[i - 1]) * ((kb * 2 * math.pi - a) / (b - a))
            turns.append(tc)
    for j, tc in enumerate(turns):
        f = frame_at(tc)
        for wname, g in (("rear", 0.36), ("front", 0.30)):
            wx = f["cart"]["wheels"][wname]["x"]
            s = wood(tc + (0.0 if wname == "rear" else 0.012), 0.52, g, pan_x(wx, tc), i=j + (0 if wname == "rear" else 4), decay=11)
        cue(tc, f"wheel turn {j + 1} completes (θ = {2 * (j + 1)}π)", "plank knock, rear and front wheel (seam at 0 rad)", s, "knocks", "derived")

    return stems, cues, turns


def _wav(path, x, stereo=None):
    path = Path(path)
    if stereo is None:
        y = np.clip(x / (np.abs(x).max() + 1e-9) * 0.9, -1, 1)
        data = (y * 32767).astype(np.int16).tobytes(); ch = 1
    else:
        data = stereo.tobytes(); ch = 2
    w = wave.open(str(path), "wb"); w.setnchannels(ch); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(data); w.close()


# --------------------------------------------------------------- captions ---
CAPTIONS = [
    dict(i=1, cause="drag stick 4 begins (stone holds)", on=7.3, off=10.6,
         fr="« La pierre avance d'un pas, puis elle réfléchit. »",
         en="The stone takes a step, then thinks it over.", voice="narrator"),
    dict(i=2, cause="log A stops on its bark, flat facet down (tok)", on=17.2, off=20.4,
         fr="« Et moi ? » dit le rouleau qu'on laisse derrière.",
         en="\"And me?\" says the roller left behind.", voice="the log (the film's only nonhuman line)"),
    dict(i=3, cause="the cart passes the 3 m roller ghost", on=28.8, off=32.4,
         fr="« La roue tourne sur place ; c'est tout le reste qui voyage. »",
         en="The wheel turns on the spot; everything else travels.", voice="narrator"),
    dict(i=4, cause="the platform's rear end hits the ground (thud), grind begins", on=36.6, off=40.4,
         fr="« Sans essieu, la roue n'est qu'un rouleau qui se croit quelqu'un. »",
         en="Without an axle, a wheel is just a roller with ideas.", voice="narrator"),
]
END_LINE = dict(on=42.0, off=44.0,
    fr="Sources : Cueva de las Manos (Suzko, CC BY-SA 3.0) · roue des marais de Ljubljana (P. Milošević, CC BY-SA 4.0) · "
       "sons : Work With Sounds (CC BY 4.0), Hippocampuz (CC BY-SA 4.0), Gravity Sound (CC BY 4.0), PDSounds (domaine public) · "
       "séquence mise en scène, non chronologique",
    en="Sources: Cueva de las Manos (Suzko, CC BY-SA 3.0) · Ljubljana Marshes wheel (P. Milošević, CC BY-SA 4.0) · "
       "sounds: Work With Sounds (CC BY 4.0), Hippocampuz (CC BY-SA 4.0), Gravity Sound (CC BY 4.0), PDSounds (public domain) · "
       "staged sequence, not chronological")


def srt(path, items, key):
    def ts(t):
        ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as fh:
        for k, c in enumerate(items, 1):
            fh.write(f"{k}\n{ts(c['on'])} --> {ts(c['off'])}\n{c[key]}\n\n")


def main():
    stems, cues, turns = build()
    # caption checks against the sim's causes
    evt = {e["event"]: e["t"] for e in EV}
    for c in CAPTIONS:
        c["cause_t"] = evt[c["cause"]]
        c["lag_s"] = round(c["on"] - c["cause_t"], 3)
        assert 0.2 <= c["lag_s"] <= 0.6, c
    # the end line credits only the recordings actually used in this build
    names = {"knock": "PDSounds", "thud": "PDSounds", "church": "PDSounds", "wagon": "Work With Sounds", "quern": "Work With Sounds",
             "gravel": "Gravity Sound", "steps": "Pwaivers", "stairs": "Hippocampuz"}
    lic = {}
    for k, v in FORAGED.items():
        if v.get("used"):
            lic.setdefault(names[k], v["license"])
    def lst(pd):
        return ", ".join(f"{n} ({pd if l == 'Public domain' else l})" for n, l in lic.items())
    END_LINE["fr"] = ("Sources : Cueva de las Manos (Suzko, CC BY-SA 3.0) · roue des marais de Ljubljana (P. Milošević, CC BY-SA 4.0) · "
                      f"sons : {lst('domaine public')} · séquence mise en scène, non chronologique")
    END_LINE["en"] = ("Sources: Cueva de las Manos (Suzko, CC BY-SA 3.0) · Ljubljana Marshes wheel (P. Milošević, CC BY-SA 4.0) · "
                      f"sounds: {lst('public domain')} · staged sequence, not chronological")
    srt(PREP / "captions.fr.srt", CAPTIONS + [END_LINE], "fr")
    srt(PREP / "captions.en.srt", CAPTIONS + [END_LINE], "en")

    # stems share one gain so they sum to the mix
    L = sum(m.L for m in stems.values()); R = sum(m.R for m in stems.values())
    peak = max(np.abs(L).max(), np.abs(R).max())
    g = 0.89 / peak
    fade = int(0.05 * RATE)
    def pcm(Lx, Rx):
        st = np.stack([Lx, Rx], 1) * g
        st[:fade] *= np.linspace(0, 1, fade)[:, None]; st[-fade:] *= np.linspace(1, 0, fade)[:, None]
        return (np.clip(st, -1, 1) * 32767).astype(np.int16)
    for k, m in stems.items():
        _wav(STEMS / f"stem-{k}.wav", None, pcm(m.L, m.R))
    _wav(STEMS / "mix.wav", None, pcm(L, R))
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(STEMS / "mix.wav"), "-lavfi",
                    "showspectrumpic=s=1400x360:legend=1:scale=log", str(PREP / "mix-spectrogram.png")], check=True)

    # per-second level map (for the editor and the critic)
    mono = (L + R) * g / 2
    lev = [round(20 * math.log10(np.sqrt((mono[int(s * RATE):int((s + 0.25) * RATE)] ** 2).mean()) + 1e-9), 1)
           for s in np.arange(0, DUR, 0.25)]

    cues.sort(key=lambda c: c["t"])
    unmapped = [c for c in cues if c["sound"] == "UNMAPPED"]
    assert not unmapped, unmapped
    used = {k: v for k, v in FORAGED.items() if v.get("used")}
    absent = [k for k, v in FORAGED.items() if not v.get("used")]
    json.dump(dict(cues=cues, turns=[float(t) for t in turns], levels_db_quarter_s=lev, used=list(used), absent=absent,
                   gain=g), open(PREP / "build-result.json", "w"), indent=1, ensure_ascii=False)
    print(f"cues {len(cues)}  wheel turns {len(turns)} at {[round(float(t), 2) for t in turns]}  used {list(used)}  absent {absent}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------ score docs ---
SHOTS = [
    ("0", 0.0, 4.0, "The wall wakes: toned Cueva rock fades up under the charcoal bands; real stencils and guanacos come up with the light. Title 'Teuf-teuf' scratches on in white (1.2 s). The boulder sits at x0; the two cut-card figures walk in (IK walk, foot plants).",
     "—", "stone-room air; footsteps on each foot plant; scratch of the title"),
    ("1", 4.0, 13.0, "DRAG. Pusher leans 40°, hands pinned, feet planted; helper hauls the rope. Nine stick-slip lurches carry the stone 1.2 m; a nod, a ±1.5° rock and a rear-foot re-plant at each slip. Stop at 11.5 s; white ghost at 1.2 m from 11.7 s. Declared reset cut at 12.75 s.",
     "7.3 s (4th stick) « La pierre avance d'un pas, puis elle réfléchit. » / The stone takes a step, then thinks it over.",
     "palms on stone at 4.5; a stone-on-stone scrape per slip whose level and grain follow the stone's speed; silence on every stick; step per re-plant; low thud at the stop; faint scratch for the ghost; scratch stroke under the reset wipe"),
    ("2", 13.0, 14.0, "SUBSTITUTE I. The stone is levered up in 3 frames; three bark logs are shoved in; it settles on a tilt spring.",
     "—", "lever knock; three wooden knocks (13.15 / 13.35 / 13.55); soft settle thud"),
    ("3a", 14.0, 16.2, "ROLLERS (wide). The stone rolls toward 1.5 m; logs turn and drift back at v/2.", "—",
     "low wooden rumble whose level and grain rate follow the carried logs' angular speed"),
    ("3b", 16.2, 18.8, "TEST SHOT, close-up x2.2 oblique. Log A squeezes out behind the rear lip, rolls under the pusher's lead foot (he lifts it), and stops on its flat facet well behind the stone (16.84 s). The carrier lifts log D in the background.",
     "17.2 s « Et moi ? » dit le rouleau qu'on laisse derrière. / \"And me?\" says the roller left behind. (the only nonhuman line)",
     "small dry roll following log A's own angular speed; the foot re-plant; TOK and one rebound at 16.84; rumble falls to zero at 16.95; light knock as hands take log D"),
    ("3c", 18.8, 21.0, "Wide again. The carrier crouches and sets log D down in front (19.7 s). The stone waits on two logs; the pusher holds.", "(caption 2 continues to 20.4)",
     "carrier's steps; wood set down on stone at 19.7"),
    ("3d", 21.0, 23.0, "The stone rolls on to 3.0 m, riding onto log D at 21.67 s; log A lies behind.", "—",
     "rumble returns with the logs' angular speed; short knock as the nose rides onto D; soft thud at 23.0"),
    ("3e", 23.0, 25.0, "Hold. Ghost at 3.0 m (23.3 s). Declared reset cut at 25.0.", "—", "ghost scratch; air; wipe scratch"),
    ("4", 25.0, 34.0, "WHEEL AND AXLE. Plank platform on one axle and two GrabCut Ljubljana wheels; 8.0 m in the same 7 s push (26.0–33.0). The pusher's stride rate rises; the carrier walks alongside empty-handed and drops back. Passes the 3 m ghost at 28.38 s; ghost at 8.0 m at 33.3 s. Reset cut at 34.0.",
     "28.8 s « La roue tourne sur place ; c'est tout le reste qui voyage. » / The wheel turns on the spot; everything else travels.",
     "axle-and-wheel rumble following the wheels' angular speed; a plank knock on both wheels at each full turn (27.91, 29.33, 30.79 s); quickening footsteps; low thud as the cart halts; ghost scratch"),
    ("5", 34.0, 38.0, "COUNTER-CHECK. Pin pulled (34.6), beam lifts away; the same push (35.3). Loose wheels roll at v/2, the rear wheel runs out (36.07) and stops (36.22); the platform drops (36.30) and grinds to a stop at 0.95 m (36.83).",
     "36.6 s « Sans essieu, la roue n'est qu'un rouleau qui se croit quelqu'un. » / Without an axle, a wheel is just a roller with ideas.",
     "pin click and a light beam knock; loose-wheel rumble; heavy wood knock as the wheel falls; small tok as it stops; THUD and a stone grind that follows the platform's speed; short thud at the stop"),
    ("6", 38.0, 44.0, "COMPARISON HELD. Three ghosts (1.2 / 3.0 / 8.0 m), log A and the wheel-less platform where they fell. The figures sit; the pusher sits on log A (39.6) and it rocks once. End line scratches in at 42.0.",
     "42.0 s end source line (French, English subtitle)",
     "air; footsteps of the sit-down; final TOK of the forgotten log and its one rock back; faint scratch of the end line"),
]


def write_docs():
    res = json.load(open(PREP / "build-result.json"))
    rel = lambda p: str(Path(p).relative_to(FILMS.parent)) if str(p).startswith(str(FILMS.parent)) else str(p)
    evidence = []
    for k, v in FORAGED.items():
        if not v.get("used"):
            continue
        evidence.append(dict(id=f"snd-{k}", title=v["title"], author=v["author"], license=v["license"],
                             license_url=v["license_url"], source_url=v["source_url"], file_url=v["file_url"],
                             local_path=v["local_path"], decoded_path=v["decoded"], what_it_shows=v["what_it_shows"],
                             verified_date_or_place=v["verified"],
                             used_as=sorted({c["sound"] + " @ " + str(c["t"]) for c in res["cues"] if k_label(k) in c["source"]})[:60]))
    absences = [
        dict(searched="Commons filetype:audio 'cave ambience'", result="no hits"),
        dict(searched="Commons filetype:audio 'stone scrape grinding' / 'stone scrape'", result="no stone-on-stone drag; hits were pronunciation clips (slicker, sleek); used the WWS quern grind if downloaded, else synthesis"),
        dict(searched="Commons filetype:audio 'log rolling', 'stone dragging', 'wooden cart'", result="not reached or nothing apt before the Commons API rate limit (429, retry-after up to 600 s)"),
        dict(searched="movingimagearchive.com cache, forage.py 'quarry|stone|wood|cart|wagon|lumber|log|wheel|saw' --media clip and the index's audio features",
             result="no clip with an isolated contact sound: the 'sound' clips are narration, music or surf noise under unrelated scenes (e.g. d3c1f500 Panama by Air 1914, -48 dB surf; 77a0080e, 7102b861 music/voice); none used"),
    ]
    for k in res["absent"]:
        v = FORAGED[k]
        absences.append(dict(searched=f"{v['title']} ({v['license']}) found and licence-checked", result="download blocked by upload.wikimedia.org 429 (retry-after 600 s) within the time budget; its role is synthesised (declared in cues)"))
    handmade = [
        dict(what="event map and sound placement", where=rel(HERE / "build_score.py"), how="reads exposure.json events, footfalls and per-frame log/wheel angles; one sound per event; continuous beds follow |dθ/dt| and |v|"),
        dict(what="scratch strokes (title, ghosts, wipes, end line)", where="stem-scratch.wav", how="kit.Mix noise: sparse band-passed grains in gapped strokes"),
        dict(what="air", where="stem-room.wav", how="kit.Mix.room(hum=0) under the low-passed PD church bed"),
        dict(what="any role whose recording was not reachable", where="see cues with source 'SYNTH'", how="kit.Mix thud/step/noise"),
        dict(what="captions FR + EN", where=rel(PREP / "captions.fr.srt") + ", " + rel(PREP / "captions.en.srt"), how="text written for this film; timing from exposure.json causes"),
    ]
    stems = {k: rel(STEMS / f"stem-{k}.wav") for k in ["room", "steps", "scrape", "knocks", "rumble", "impacts", "scratch"]}
    score = dict(
        film="teuf-teuf", unit="COMMENTARY-SOUND", direction="1 'La paroi'", fps=FPS, duration_s=DUR,
        about="Dual-column score: picture | commentary | sound, from plan.md §5 and exposure.json. All stems start at film time 0, 44.1 kHz stereo, share one gain and sum to mix.wav.",
        columns=[dict(shot=s, t0=a, t1=b, picture=p, commentary=c, sound=snd) for s, a, b, p, c, snd in SHOTS],
        captions=[dict(i=c["i"], on=c["on"], off=c["off"], cause=c["cause"], cause_t=c["cause_t"], lag_s=c["lag_s"],
                       fr=c["fr"], en=c["en"], voice=c["voice"]) for c in CAPTIONS],
        caption_style="small serif italic (Liberation Serif Italic) in the lower charcoal band; FR line above, EN subtitle below in a smaller size; white-scratched ghost of the type, no box",
        end_line=END_LINE,
        sound_events=res["cues"], wheel_turn_knocks_t=res["turns"],
        stems=stems, mix=rel(STEMS / "mix.wav"), prepared_media=rel(PREP),
        levels_db_quarter_s=res["levels_db_quarter_s"],
        evidence=evidence, handmade=handmade, absences=absences,
        notes=[
            "Caption 4 cause: the computed task names the pin pull (34.6 s); plan §5 and exposure.json's caption_cues tie it to the platform drop (36.30 s) with onset 36.6 s (lag 0.30 s). Kept 36.6 s: the line comments on the wheel becoming a roller, which is only visible once the axle-less wheel runs out. If the editor wants the pin-pull cause, onset 34.9 s (lag 0.30 s) also fits the 0.2-0.6 s rule; the line would then hold to 38.4 s.",
            "pass-3m and the carry window marks have no contact; they are given no sound on purpose (the caption is the pass's voice).",
            "No voice recordings: the narrator and the log speak only in captions.",
            "No sound or text from Jabely's Teuf-Teuf was used.",
        ])
    json.dump(score, open(SWARM / "score.json", "w"), indent=1, ensure_ascii=False)

    L = ["# Teuf-teuf — dual-column score (COMMENTARY-SOUND unit)", "",
         f"44.0 s, 24 fps. Stems in `{rel(STEMS)}/stem-*.wav` (start at film 0, one shared gain, sum = `mix.wav`). Captions: `{rel(PREP)}/captions.fr.srt`, `captions.en.srt`.", "",
         "| shot | time (s) | picture | commentary (FR / EN) | sound |", "|---|---|---|---|---|"]
    for s, a, b, p, c, snd in SHOTS:
        L.append(f"| {s} | {a:.1f}–{b:.1f} | {p} | {c} | {snd} |")
    L += ["", "## Captions (onset 0.2–0.6 s after the causal sim event)", "", "| # | on–off | cause (t) | lag | FR | EN |", "|---|---|---|---|---|---|"]
    for c in CAPTIONS:
        L.append(f"| {c['i']} | {c['on']}–{c['off']} | {c['cause']} ({c['cause_t']}) | {c['lag_s']} | {c['fr']} | {c['en']} |")
    L += [f"| end | {END_LINE['on']}–{END_LINE['off']} | end-line | — | {END_LINE['fr']} | {END_LINE['en']} |", "",
          "## Sound events (one per sim event; footsteps one per IK plant)", "", "| t | event | sound | source | stem |", "|---|---|---|---|---|"]
    for c in res["cues"]:
        if c["kind"] == "footfall":
            continue
        L.append(f"| {c['t']} | {c['event']} | {c['sound']} | {c['source']} | {c['stem']} |")
    nf = sum(1 for c in res["cues"] if c["kind"] == "footfall")
    L += ["", f"Footsteps: {nf} plants from exposure.json `footfalls` (P and C), panned by world x (the close-up scales pan x2.2); full list in score.json.", "",
          "## Foraged sounds (evidence)", ""]
    for e in evidence:
        L.append(f"- **{e['title']}**, {e['author']}, {e['license']} — {e['source_url']} — local `{e['local_path']}` — {e['what_it_shows']}. Verified: {e['verified_date_or_place']}")
    L += ["", "## Absences", ""] + [f"- {a['searched']}: {a['result']}" for a in absences]
    L += ["", "## Notes", ""] + [f"- {n}" for n in score["notes"]]
    open(SWARM / "score.md", "w").write("\n".join(L) + "\n")

    # credits: add foraged sound entries, no duplicates
    cp = FILMS / "credits" / "teuf-teuf.json"
    cr = json.load(open(cp)) if cp.exists() else []
    have = {c["source_url"] for c in cr}
    for e in evidence:
        rec = dict(title=e["title"], author=e["author"], license=e["license"], license_url=e["license_url"],
                   source_url=e["source_url"], file_url=e["file_url"],
                   used_as="sound: " + SOUND_ROLE.get(e["id"][4:], "contact sound"))
        if e["source_url"] in have:
            for c in cr:
                if c["source_url"] == e["source_url"]:
                    c.update(rec)
        else:
            cr.append(rec)
    json.dump(cr, open(cp, "w"), indent=1, ensure_ascii=False)


SOUND_ROLE = {
    "knock": "every wooden contact: log landings, the 'tok' of the left-behind log, set-down, plank knock per wheel turn, the pin click, the fallen wheel, the final tok (single knocks cut, slowed 0.52-0.95x, shortened)",
    "wagon": "the rollers' and the wheels' rumble, read at a speed that follows the logs' / wheels' angular speed",
    "quern": "the drag scrape at each stick-slip lurch and the grind of the axle-less platform, read at a speed that follows the stone's speed",
    "thud": "the stone's and the platform's thuds (slowed, low-passed)",
    "gravel": "grit under every third footstep",
    "stairs": "footsteps (cut as single steps)",
    "steps": "footsteps on each IK foot plant (single steps cut, +-8% speed variation)",
    "church": "the room: low-passed at 220 Hz into the air of a big stone room",
}


def k_label(k):
    return {"knock": "knock (PD)", "wagon": "wooden wagon", "quern": "quern", "thud": "dull thud", "gravel": "gravel",
            "stairs": "stone-stair", "steps": "concrete/stone", "church": "church"}[k]


if __name__ == "__main__":
    write_docs()
