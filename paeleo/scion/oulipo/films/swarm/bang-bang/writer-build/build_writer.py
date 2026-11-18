"""Writer + timing/sound unit for bang-bang (SCION #47 cue anchoring).

Builds:
  films/swarm/bang-bang/cues.json        cue sheet (slips, gloss, gate, anchors, contrast, fx, evidence)
  films/swarm/bang-bang/cues_swap.json   BB-07 <-> BB-09 slip swap (replay experiment)
  films/swarm/bang-bang/stems.json       stems, sources, measured peak frames vs anchors
  films/sources/bang-bang/sound/*.wav    44.1 kHz stereo 16-bit, 30.0 s stems + preview mix + baseline mix

Run:  python3 -I films/swarm/bang-bang/writer-build/build_writer.py
Deterministic (seed 47). Reads foraged audio only through ffmpeg decode -> wav -> numpy.
"""
import json, math, re, subprocess, sys, wave, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SW = HERE.parent                                   # films/swarm/bang-bang
FILMS = SW.parent.parent                           # films/
sys.path.insert(0, str(FILMS))
import kit                                         # read-only use of kit.Mix synthesis

SRC = FILMS / "sources" / "bang-bang"
SND = SRC / "sound"; SND.mkdir(parents=True, exist_ok=True)
PREP = SRC / "writer-and-timing-sound-unit-nonhuman-account-cue-sheet-stems-"; PREP.mkdir(exist_ok=True)
FPS, RATE, SECONDS = 24, 44100, 30.0
N = int(SECONDS * RATE)
SPF = RATE / FPS                                   # 1837.5 samples per frame
SILENCE = (540, 554)                               # declared near-silence [f540, f554): air only
STRIKE_F, IMPACT_F = 528, 605


def ftime(f):            # centre of frame f, seconds
    return (f + 0.5) / FPS


# ======================================================================= text
# chars counted including spaces and punctuation; cps = n * 24 / (end - start)
SLIPS = [
    # id, board, attempt, paste_f, write_start, write_end, text, gloss, image_event, image_event_f, anchor(kind,frame) or None,
    # contrast, witness perception note, gate4 ('pass'/'marker'), depends_on_outcome, fx
    dict(id="S1", board="BB-01", attempt="A1", paste=28, ws=30, we=91,
         text="Il s'est fait une aile en papier.", gloss="He made himself a wing out of paper.",
         image_event="push-in completes on panel 1: the man on the wall with a ribbed paper wing strapped to his arm", image_event_f=24,
         anchor=None,
         contrast="The image shows a paper shape tied to an arm. The slip adds the bird's surprise that a wing can be made at all ('s'est fait'): a wing is something it grows.",
         perception="bird perched on the gatepost in panel 1, head toward him", gate4="pass", depends_on_outcome=False,
         fx=["paper flap f28 (paste)", "magpie chatter onset f29"]),
    dict(id="S1b", board="BB-01", attempt="A1", paste=105, ws=107, we=135,
         text="La mienne obéit.", gloss="Mine does what I tell it.",
         image_event="third flap: the paper wing tip folds back on itself", image_event_f=108,
         anchor=("write_start", 108),
         contrast="The image shows the paper tip folding by itself. The slip compares it with the bird's own wing, which folds only when the bird wants: the failure is disobedience, not weakness.",
         perception="bird's head at the 3rd held angle (f100), toward the wing", gate4="pass", depends_on_outcome=False,
         fx=["paper flap f105 (paste)", "paper crease crinkle f108"]),
    dict(id="S1c", board="BB-01", attempt="A1", paste=None, ws=154, we=161, line_of="S1b",
         text="pof.", gloss="(flump)",
         image_event="he sits down on the flowerbed", image_event_f=154, anchor=("write_start", 154),
         contrast="Sound word: the bird hears the sit as soft and harmless (a 'pof', not a fall). Carried with S1b.",
         perception="bird's head at 5th held angle (f150), on him", gate4="marker", depends_on_outcome=False,
         fx=["soft low thud 'pof' f154"]),
    dict(id="S2", board="BB-02/03", attempt="A2", paste=200, ws=203, we=250,
         text="Puis un moulin à élastique.", gloss="Then a rubber-band windmill.",
         image_event="he winds the two-rotor machine in steps (12 turns, tally in graphite)", image_event_f=192,
         anchor=None,
         contrast="The image shows a winding machine. The slip names it as the bird sees it, a 'moulin', a thing that turns where it is, not a flier.",
         perception="bird perched in panel 2 at left", gate4="pass", depends_on_outcome=False,
         fx=["paper flap f200 (paste)", "rubber creak per winding step f192-f250 (30 steps on 2s)"]),
    dict(id="S2b", board="BB-02/03", attempt="A2", paste=252, ws=255, we=306,
         text="Lui reste en bas. C'est sage.", gloss="He stays down below. Sensible.",
         image_event="release: the rotor rises out of his hands; he stays on the ground", image_event_f=254,
         anchor=("write_start", 254),
         contrast="The image shows only the machine rising and the man staying. The slip approves: staying down to watch first is what the bird calls wise.",
         perception="bird looks up (head 35 deg) from f254", gate4="pass", depends_on_outcome=False,
         fx=["paper flap f252 (paste)", "release whirr f254-f312", "magpie chatter onset f264"]),
    dict(id="S2c", board="BB-02/03", attempt="A2", paste=None, ws=312, we=321, line_of="S2b",
         text="clac.", gloss="(snap)",
         image_event="the rubber band snaps (pen squiggle whips)", image_event_f=312, anchor=("write_start", 312),
         contrast="Sound word only: the bird hears the snap. Carried with S2b (no added claim).",
         perception="bird head up 50 deg toward the rotor", gate4="marker", depends_on_outcome=False,
         fx=["band snap 'clac' f312", "small thump f331 (machine drops on turf)"]),
    dict(id="S3", board="BB-03/06", attempt="A3", paste=343, ws=346, we=389,
         text="Enfin, les grandes ailes.", gloss="At last, the big wings.",
         image_event="REQUIRES sheet-1 panel 3 to show the glider at rest (still key pose), visible in the pull-out f384-f396", image_event_f=346,
         anchor=None,
         contrast="The image shows a large frame of cloth and spars. 'grandes ailes' measures it the bird's way, by wings, and 'Enfin' says that, to a bird, this at last looks like the real thing.",
         perception="DEPENDENCY: passes only if s1p3 holds the resting glider (board artist); fallback: drop S3, nothing else moves",
         gate4="pass", depends_on_outcome=False,
         fx=["paper flap f343 (paste)"]),
    dict(id="S4", board="BB-07", attempt="A3", paste=430, ws=433, we=466,
         text="Face au vent. Bien.", gloss="Into the wind. Good.",
         image_event="the run starts down the pen hill, right to left", image_event_f=432,
         anchor=("write_start", 432),
         contrast="The image shows a man running downhill. The slip adds the bird's own take-off rule (into the wind) and approves it.",
         perception="bird on the fence post in panel s2p1", gate4="pass", depends_on_outcome=False,
         fx=["paper flap f430 (paste)", "footfalls on turf f432-f490", "wind rising f432 -> cut f528"]),
    dict(id="S5", board="BB-08", attempt="A3", paste=476, ws=480, we=525,
         text="Il lève le nez pour monter", gloss="He lifts his nose to ~~climb~~ stop.",
         image_event="lift-off f490; nose starts to come up after f504", image_event_f=490,
         anchor=None,
         contrast="Written as the man's intention ('to climb'), so the bird can correct it at the strike.",
         perception="bird on the post in panel s2p2, watching the lift-off", gate4="pass", depends_on_outcome=True,
         fx=["paper flap f476 (paste)"]),
    dict(id="S5-strike", board="BB-08", attempt="A3", paste=None, ws=528, we=530, line_of="S5",
         text="~~monter~~", gloss="(climb, struck)",
         image_event="nose crosses 15 deg above the horizon, forward advance dying (exposure: nose_15deg_frame 528)", image_event_f=528,
         anchor=("strike", 528),
         contrast="The strike is the bird changing its mind on the page: what looked like climbing is, to a flier, the start of stopping.",
         perception="bird in panel 2 (on post, takes off ~f538)", gate4="pass", depends_on_outcome=True,
         fx=["brass pin tick f528", "wind cut f528"]),
    dict(id="S5-corr", board="BB-08", attempt="A3", paste=None, ws=531, we=547, line_of="S5",
         text="s'arrêter", gloss="stop",
         image_event="pitch reaches 35 deg, x-advance zero at f540; hang f540-f554 with legs still swinging", image_event_f=540,
         anchor=None,
         contrast="The image shows nose up and forward motion ceasing. The slip gives the bird's reading: a raised nose is how you stop. It reads braking, not failure.",
         perception="bird in panel 2", gate4="pass", depends_on_outcome=True,
         fx=["declared near-silence f540-f554 (air only)"]),
    dict(id="S5b", board="BB-08", attempt="A3", paste=547, ws=549, we=592,
         text="Moi aussi, pour me poser.", gloss="Me too, to land.",
         image_event="the magpie flies level past him and flares nose-up at f560 (the same gesture, done right)", image_event_f=548,
         anchor=("write_start", 548),
         contrast="The image shows two nose-up shapes. The slip says they are the same act and that its purpose is landing: the man is doing what birds do to come down.",
         perception="the bird is the subject; flying through panel 2", gate4="pass", depends_on_outcome=True,
         fx=["paste flap SUPPRESSED (paste f547 falls in the declared silence)", "magpie wing whoosh f554-f562 (peak f557)", "flare flutter f560-f568"]),
    dict(id="S6", board="BB-09", attempt="A3", paste=589, ws=593, we=605,
         text="Krach !", gloss="Crash!",
         image_event="impact: glider shadow and glider touch the turf", image_event_f=605,
         anchor=("write_complete", 605),
         contrast="Sound word: on its own it paraphrases the image (gate 4 fails alone). It is carried by S6b/S6c, which turn the crash into a landing.",
         perception="bird perched at the panel 2/3 edge after its landing f568-f580; NEEDS head turned to the wreck at f580-f605 (or bird visible at the edge of panel 3)",
         gate4="marker", depends_on_outcome=True,
         fx=["paper flap f589 (paste)", "thump + paper crumple peak f605"]),
    dict(id="S6b", board="BB-09", attempt="A3", paste=615, ws=617, we=638,
         text="Un peu vite.", gloss="A bit fast.",
         image_event="the wreck is held; legs whip and settle by f636", image_event_f=605,
         anchor=None,
         contrast="The image shows a wreck. The slip grades it as a landing that was a bit fast, which is how a bird judges any landing.",
         perception="bird re-enters panel 3 from f620", gate4="pass", depends_on_outcome=True,
         fx=["paper flap f615 (paste)", "magpie chatter onset f614"]),
    dict(id="S6c", board="BB-09", attempt="A3", paste=636, ws=639, we=674,
         text="Mais au bon endroit.", gloss="But in the right place.",
         image_event="the magpie lands beside the wreck with a clean flare (two-hop settle, one peck)", image_event_f=638,
         anchor=("write_start", 638),
         contrast="The image shows the bird landing next to the wreck. The slip says the place was right: the man came down where a bird would choose to.",
         perception="bird in panel 3", gate4="pass", depends_on_outcome=True,
         fx=["paper flap f636 (paste)", "landing flutter f636"]),
]

BASELINE = [  # human reporter, typed newspaper strip, no correction, no strike, no chatter (plan sec. 2, sec. 8)
    dict(id="R7", board="BB-07", paste=430, ws=433, we=454, text="Course d'élan.", gloss="Run-up."),
    dict(id="R8", board="BB-08", paste=476, ws=480, we=514, text="L'appareil se cabre.", gloss="The machine rears up."),
    dict(id="R8b", board="BB-08", paste=None, ws=531, we=552, text="Il décroche.", gloss="It stalls."),
    dict(id="R9", board="BB-09", paste=581, ws=584, we=605, text="Il s'écrase.", gloss="It crashes."),
    dict(id="R9b", board="BB-09", paste=None, ws=617, we=627, text="Échec.", gloss="Failure."),
]

# ------------------------------------------------------------- witness gate
JARGON = ["décroch", "incidence", "portance", "vitesse", "aérodynam", "angle", "degré", "hélice", "hélicoptère", "planeur",
          "moteur", "rotor", "torsion", "caoutchouc", "pilote", "appareil", "machine", "gravité", "poussée", "traînée",
          "équilibre", "aviat", "aéro", "inventeur", "brevet", "physique", "force", "énergie", "°"]
NAMES = ["lilienthal", "pénaud", "penaud", "pique-vent", "queneau", "jabely", "otto", "alphonse", "wright", "berlin", "paris"]


def lexicon_gate(text):
    t = text.replace("~~", "")
    fails = []
    if re.search(r"\d", t): fails.append("digit/number")
    if re.search(r"\b(1[5-9]\d\d|20\d\d)\b", t): fails.append("year")
    for w in ("un", "deux", "trois", "quatre", "cinq", "douze", "cent", "mille", "premier", "second"):
        if re.search(r"\b%s\b" % w, t.lower()) and w != "un":
            fails.append("number word '%s'" % w)
    low = t.lower()
    for j in JARGON:
        if j in low: fails.append("jargon '%s'" % j)
    for n in NAMES:
        if n in low: fails.append("proper name '%s'" % n)
    # capitalised word that is not sentence-initial
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-ZÉÈÀ][a-zéèêàç]+)", t):
        if m.start() > 0 and t[:m.start()].rstrip()[-1:] not in ".!?":
            fails.append("capitalised mid-sentence '%s'" % m.group(1))
    return fails


def cps(n, ws, we):
    return round(n * FPS / max(1, we - ws), 2)


cues = []
for s in SLIPS:
    n = len(s["text"].replace("~~", ""))
    g = lexicon_gate(s["text"])
    a = s.get("anchor")
    anchor_ok = None
    if a:
        kind, af = a
        got = s["ws"] if kind in ("write_start", "strike") else s["we"]
        anchor_ok = abs(got - af) <= 1
    row = {
        "cue": s["id"], "kind": "slip", "board_id": s["board"],
        "frame_range": None, "attempt_id": s["attempt"],
        "image_event": s["image_event"], "image_event_frame": s["image_event_f"],
        "text": s["text"], "gloss_en_graphite": s["gloss"], "hand": "pen.hand (Hershey-derived, per-word slant/size/baseline drift, felt nib), warm ink (65,53,41) on torn cream slip, brass pin",
        "line_of": s.get("line_of"),
        "paste_frame": s["paste"], "write_start_frame": s["ws"], "write_end_frame": s["we"],
        "chars": n, "cps": cps(n, s["ws"], s["we"]) if s["id"] != "S5-strike" else None,
        "comment_anchor": ({"kind": a[0], "frame": a[1], "measured_frame": (s["ws"] if a[0] in ("write_start", "strike") else s["we"]),
                            "pass_pm1": anchor_ok} if a else None),
        "fx": s["fx"], "contrast": s["contrast"],
        "witness_gate": {"lexicon": "pass" if not g else "fail", "lexicon_failures": g,
                         "perception": s["perception"],
                         "precondition4_distinct": s["gate4"]},
        "depends_on_outcome": s["depends_on_outcome"],
    }
    cues.append(row)

BOARDS = json.load(open(SW / "exposure.json"))["boards"]
for r in cues:
    b = r["board_id"].split("/")[0] if r["board_id"] == "BB-03/06" else r["board_id"]
    r["frame_range"] = BOARDS.get(r["board_id"], BOARDS.get("BB-02/03" if r["board_id"] == "BB-03/06" else r["board_id"]))

# rate check
for r in cues:
    if r["cps"] is not None:
        r["cps_in_11_14"] = 11.0 <= r["cps"] <= 14.0

# single-hand overlap check (one pen, serial writing)
spans = sorted((r["write_start_frame"], r["write_end_frame"], r["cue"]) for r in cues)
overlaps = [(a[2], b[2]) for a, b in zip(spans, spans[1:]) if b[0] < a[1]]

baseline_rows = []
for s in BASELINE:
    n = len(s["text"])
    baseline_rows.append({"cue": s["id"], "board_id": s["board"], "text": s["text"], "gloss_en": s["gloss"],
                          "paste_frame": s["paste"], "write_start_frame": s["ws"], "write_end_frame": s["we"],
                          "chars": n, "cps": cps(n, s["ws"], s["we"]),
                          "hand": "typed newspaper strip (typewriter face on newsprint strip), no correction",
                          "witness_gate": "n/a: human reporter (jargon 'décroche', 'appareil' allowed; that is the point of the baseline)"})

# ======================================================================= sound
rs = np.random.RandomState(47)
mixer = kit.Mix(SECONDS, seed=47)          # used only for its synthesis helpers (noise, band, thud ...)


def silent():
    return np.zeros((N, 2))


def mono_sig(fn):
    """run a kit.Mix instrument into a fresh mix and return its mono signal."""
    m = kit.Mix(2.0, seed=int(rs.randint(1 << 30)))
    fn(m)
    return (m.L + m.R) / 2.0


def env_peak_offset(sig):
    e = np.convolve(np.abs(sig), np.ones(int(0.004 * RATE)) / int(0.004 * RATE), "same")
    return int(np.argmax(e))


def place(stem, sig, frame, gain=1.0, pan=0.0, align="peak"):
    """put sig so its envelope peak (or onset) lands at the centre of `frame`."""
    off = env_peak_offset(sig) if align == "peak" else 0
    i0 = int(round(ftime(frame) * RATE)) - off
    if align == "onset":
        i0 = int(round((frame + 0.15) / FPS * RATE))
    j0 = max(0, i0); s = sig[j0 - i0:]
    s = s[: N - j0]
    lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    stem[j0:j0 + len(s), 0] += s * gain * lg * 1.414
    stem[j0:j0 + len(s), 1] += s * gain * rg * 1.414


def nz(sec):
    return rs.normal(0, 1, int(sec * RATE))


def band(x, lo, hi):
    return mixer.band(x, lo, hi)


def norm(x):
    return x / (np.abs(x).max() + 1e-12)


# ---------- handmade FX (numpy synthesis) ----------
def paper_flap():
    """slip paste: a light card-on-card slap plus the strip's own flutter (handmade synthesis)."""
    n = int(0.16 * RATE); t = np.arange(n) / RATE
    flutter = band(nz(0.16), 700, 6500) * np.exp(-t * 28) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * t))
    slap = band(nz(0.16), 150, 2200) * np.exp(-np.maximum(t - 0.045, 0) * 90) * (t >= 0.045)
    pat = np.sin(2 * np.pi * 140 * t) * np.exp(-np.maximum(t - 0.045, 0) * 60) * (t >= 0.045)
    return norm(0.5 * flutter + 1.0 * slap + 0.35 * pat)


def wing_rustle(sec=0.26):
    n = int(sec * RATE); t = np.arange(n) / RATE
    body = band(nz(sec), 900, 7500) * np.sin(np.pi * t / sec) ** 2
    crk = np.zeros(n)
    for k in rs.randint(0, n - 200, 45):
        crk[k:k + 160] += rs.normal(0, 1, 160) * np.exp(-np.arange(160) / 25) * rs.uniform(0.3, 1)
    crk = band(crk, 1500, 9000) * np.sin(np.pi * t / sec)
    return norm(body + 0.8 * crk)


def crinkle(sec=0.35, density=120, lo=1200, hi=8000):
    n = int(sec * RATE); x = np.zeros(n)
    for k in np.sort(rs.randint(0, n - 300, int(density * sec))):
        L = rs.randint(60, 260)
        x[k:k + L] += rs.normal(0, 1, L) * np.exp(-np.arange(L) / (L / 4)) * rs.uniform(0.2, 1)
    t = np.arange(n) / RATE
    return norm(band(x, lo, hi) * np.exp(-t * 6))


def creak(tension):
    """rubber stick-slip: a short pulse train at a jittery 'squeak' pitch; pitch and level rise with tension."""
    sec = 0.055; n = int(sec * RATE); t = np.arange(n) / RATE
    f0 = 170 + 230 * tension + rs.normal(0, 12)
    ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.08 * np.sin(2 * np.pi * 31 * t)) ) / RATE
    pulse = np.maximum(np.sin(ph), 0) ** 6
    sig = band(pulse - pulse.mean(), 120, 3000) * np.sin(np.pi * t / sec) ** 0.7
    return norm(sig + 0.15 * band(nz(sec), 2000, 6000) * np.sin(np.pi * t / sec))


def whirr(sec, f_start, f_end):
    n = int(sec * RATE); t = np.arange(n) / RATE
    fm = f_start + (f_end - f_start) * (1 - np.exp(-t / (sec / 3)))
    am = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(fm) / RATE)
    x = band(nz(sec), 250, 3500) * am ** 2
    return norm(x * np.exp(-t / (sec * 0.55)) * np.minimum(1, t / 0.02))


def snap():
    sec = 0.5; n = int(sec * RATE); t = np.arange(n) / RATE
    crack = band(nz(sec), 1500, 12000) * np.exp(-t * 260)
    tw = np.sin(2 * np.pi * np.cumsum(260 * np.exp(-t * 7) + 90) / RATE) * np.exp(-t * 14)
    return norm(1.6 * crack + 0.5 * tw)


def thud(freq=70, sec=0.35, bright=0.2):
    return norm(mono_sig(lambda m: m.thud(0.0, freq=freq, gain=1.0, seconds=sec)) + 0 * bright)


def pin_tick():
    """brass pin pushed home: a bright tick with a short metallic ring (3.1 / 4.7 kHz)."""
    sec = 0.12; t = np.arange(int(sec * RATE)) / RATE
    tick = band(nz(sec), 2500, 14000) * np.exp(-t * 900)
    ring = (np.sin(2 * np.pi * 3150 * t) + 0.5 * np.sin(2 * np.pi * 4730 * t)) * np.exp(-t * 55)
    return norm(tick + 0.35 * ring)


def whoosh(sec):
    n = int(sec * RATE); t = np.arange(n) / RATE
    w = band(nz(sec), 300, 4500) * np.hanning(n) ** 1.5
    beats = 0.55 + 0.45 * np.abs(np.sin(np.pi * t * 12))    # wing beats on 2s (12 /s)
    return norm(w * beats)


def flutter(sec=0.3):
    n = int(sec * RATE); t = np.arange(n) / RATE
    return norm(band(nz(sec), 400, 5000) * np.abs(np.sin(np.pi * t * 14)) * np.sin(np.pi * t / sec))


def step_turf():
    sec = 0.11; t = np.arange(int(sec * RATE)) / RATE
    return norm(band(nz(sec), 90, 1600) * np.exp(-t * 45) + 0.6 * np.sin(2 * np.pi * 85 * t) * np.exp(-t * 60))


def wind_bed(sec):
    x = mixer.noise(sec, "brown")
    t = np.arange(len(x)) / RATE
    lfo = 0.65 + 0.35 * np.sin(2 * np.pi * 0.4 * t + 1.3)
    x = band(x, 60, 1800) * lfo
    return norm(x)


def page_turn():
    """card flip: swoosh of a large sheet rising to the flip edge (peak) then the settle slap."""
    sec = 0.95; n = int(sec * RATE); t = np.arange(n) / RATE
    pk = 12 / FPS                                  # peak 12 frames after start (f396 -> f408)
    sw = band(nz(sec), 250, 5000) * np.exp(-((t - pk) / 0.13) ** 2)
    edge = crinkle(sec, density=60, lo=2000, hi=9000) * np.exp(-((t - pk) / 0.08) ** 2)
    return norm(sw + 0.5 * edge)


# ---------- foraged audio ----------
def decode(src, out, ss=None, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if ss is not None: cmd += ["-ss", str(ss)]
    if dur is not None: cmd += ["-t", str(dur)]
    cmd += ["-i", str(src), "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(out)]
    subprocess.run(cmd, check=True)
    w = wave.open(str(out)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
    return x


CACHE = Path("/home/user/hartswf0/cineosis-lab/lab/clips")
airA = decode(CACHE / "9be990a5-12e4-54d0-803a-46ee2566f9c3.mp4", PREP / "air_A_9be990a5_0.10-2.50.wav", 0.10, 2.40)
airB = decode(CACHE / "3b4530d3-83e3-56e7-a9d7-fd17e8eaf94c.mp4", PREP / "air_B_3b4530d3_6.05-7.65.wav", 6.05, 1.60)
pica = decode(SRC / "sound" / "raw" / "Pica_pica.ogg", PREP / "pica_pica_pd.wav")


def air_bed():
    """30 s bed from the two verified speech-free spans, slices alternated (some reversed), 0.35 s equal-power xfades."""
    a = airA / (np.sqrt((airA ** 2).mean()) + 1e-9); b = airB / (np.sqrt((airB ** 2).mean()) + 1e-9)
    a = band(a, 80, 9000); b = band(b, 80, 9000)
    pieces = [a, b[::-1], a[::-1], b, a, b[::-1], a[::-1], b, a, b, a[::-1], b[::-1], a, b, a[::-1], b, a, b[::-1]]
    xf = int(0.35 * RATE); out = pieces[0].copy()
    for p in pieces[1:]:
        r = np.linspace(0, np.pi / 2, xf)
        out = np.concatenate([out[:-xf], out[-xf:] * np.cos(r) + p[:xf] * np.sin(r), p[xf:]])
    out = out[:N]
    assert len(out) == N, len(out)
    t = np.arange(N) / RATE
    g = np.clip(t / 1.0, 0, 1) * np.clip((SECONDS - t) / 2.5, 0, 1) ** 0.7     # fade in over BB-00, out over BB-10
    return out * g


# chatter bursts in the PD recording (energy-detected rattles)
def bursts(x):
    h = RATE // 100
    e = np.array([np.sqrt((x[i:i + h] ** 2).mean()) for i in range(0, len(x) - h, h)])
    db = 20 * np.log10(e + 1e-9)
    on = db > (np.median(db) + 18)
    out = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or (j + 8 < len(on) and on[j:j + 8].any())): j += 1
            if j - i >= 30: out.append((i * h, j * h))
            i = j
        i += 1
    return out


B = bursts(pica)
CHAT = []
for (a0, a1) in B:
    seg = pica[max(0, a0 - int(0.03 * RATE)): a1 + int(0.08 * RATE)].copy()
    seg = band(seg, 900, 12000)                     # drop low hum / traffic; the rattle sits 1-10 kHz
    L = len(seg); f = int(0.02 * RATE)
    seg[:f] *= np.linspace(0, 1, f); seg[-int(0.06 * RATE):] *= np.linspace(1, 0, int(0.06 * RATE))
    CHAT.append((a0 / RATE, a1 / RATE, seg))


def onset_offset(sig):
    e = np.convolve(np.abs(sig), np.ones(220) / 220, "same")
    return int(np.argmax(e > 0.25 * e.max()))


def place_onset(stem, sig, frame, gain, pan=0.0):
    off = onset_offset(sig)
    i0 = int(round((frame + 0.2) / FPS * RATE)) - off
    s = sig[max(0, -i0):]; i0 = max(0, i0); s = s[: N - i0]
    lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    stem[i0:i0 + len(s), 0] += s * gain * lg * 1.414; stem[i0:i0 + len(s), 1] += s * gain * rg * 1.414


# ---------- footfalls from the exposure sheet (BB-07 legs on panel s2p1) ----------
EXP = json.load(open(SW / "exposure.json"))
legs = {}
for d in EXP["drawings"]:
    if 432 <= d["f"] <= 492:
        for p in d["pieces"]:
            if p["panel"] == "s2p1" and p["piece"] == "legs": legs[d["f"]] = p["angle"]
fr = sorted(legs)
FOOT = [f for a, f, c in zip(fr, fr[1:], fr[2:]) if (legs[f] - legs[a]) * (legs[c] - legs[f]) < 0 and f < 490]
if not FOOT:
    FOOT = list(range(436, 490, 6))

# ======================================================== build the stems
stems = {k: silent() for k in ("air", "magpie", "paper", "action", "pin")}
events = []   # (stem, name, anchor_frame, align)

stems["air"] += air_bed()[:, None] * np.array([0.9, 1.0]) * 10 ** (-36 / 20) * 1.0

# magpie chatter (foraged, PD): onsets f29, f264, f614, f682
chat_plan = [(29, 0, -0.5, -10), (264, 2, -0.4, -12), (614, 4, 0.3, -9), (682, 5, 0.2, -15)]
for f, k, pan, db in chat_plan:
    seg = CHAT[k % len(CHAT)][2]
    seg = norm(seg)
    place_onset(stems["magpie"], seg, f, 10 ** (db / 20), pan)
    events.append(("magpie", "chatter onset (burst %d of Pica_pica.ogg, %.2f-%.2f s)" % (k, CHAT[k % len(CHAT)][0], CHAT[k % len(CHAT)][1]), f, "onset"))

# paper: slip paste flaps (S5b's suppressed: declared silence), paper settle, page turn
pastes = [(s["paste"], s["id"]) for s in SLIPS if s["paste"] is not None and s["id"] != "S5b"]
for f, sid in pastes:
    place(stems["paper"], paper_flap(), f, 10 ** (-17 / 20), 0.35)
    events.append(("paper", "slip paste flap %s" % sid, f, "peak"))
place(stems["paper"], paper_flap() * 0.5, 6, 10 ** (-24 / 20), 0.0); events.append(("paper", "sheet settle (BB-00)", 6, "peak"))
place(stems["paper"], page_turn(), 408, 10 ** (-14 / 20), 0.1); events.append(("paper", "page turn: flip edge (exposure page turn f396-f418, sheet swap f408)", 408, "peak"))
place(stems["paper"], paper_flap(), 418, 10 ** (-18 / 20), 0.0); events.append(("paper", "page turn: sheet lands", 418, "peak"))

# action: A1
for f in (55, 85, 115):
    place(stems["action"], wing_rustle(), f, 10 ** (-19 / 20), -0.2); events.append(("action", "paper-wing rustle (flap downstroke)", f, "peak"))
place(stems["action"], crinkle(0.3), 108, 10 ** (-20 / 20), -0.2); events.append(("action", "paper wing tip creases back", 108, "peak"))
place(stems["action"], step_turf() * 0.6, 134, 10 ** (-24 / 20), -0.2); events.append(("action", "hop off the wall (scuff)", 134, "peak"))
place(stems["action"], thud(60, 0.4), 154, 10 ** (-12 / 20), -0.1); events.append(("action", "'pof': sits on the flowerbed", 154, "peak"))
# A2
for k, f in enumerate(range(192, 252, 2)):
    place(stems["action"], creak(k / 29.0), f, 10 ** ((-28 + 8 * k / 29.0) / 20), 0.1)
    events.append(("action", "rubber creak, winding step %d" % (k + 1), f, "peak"))
place(stems["action"], whirr(2.3, 70, 9), 255, 10 ** (-20 / 20), 0.1); events.append(("action", "release whirr starts", 255, "peak"))
place(stems["action"], snap(), 312, 10 ** (-9 / 20), 0.15); events.append(("action", "band snap 'clac'", 312, "peak"))
place(stems["action"], thud(110, 0.25), 331, 10 ** (-17 / 20), 0.15); events.append(("action", "machine drops on the turf (small thump)", 331, "peak"))
# A3
for f in FOOT:
    place(stems["action"], step_turf(), f, 10 ** (-23 / 20), 0.0); events.append(("action", "footfall on turf (leg extreme in exposure)", f, "peak"))
w = wind_bed((528 - 432) / FPS + 0.2)
t = np.arange(len(w)) / RATE
w = w * np.clip(t / ((528 - 432) / FPS), 0, 1) ** 1.6
i0 = int(432 / FPS * RATE); i1 = int(528 / FPS * RATE)        # hard cut at the start of f528 (5 ms ramp)
seg = w[: i1 - i0]; ramp = int(0.005 * RATE); seg[-ramp:] *= np.linspace(1, 0, ramp)
stems["action"][i0:i1] += seg[:, None] * 10 ** (-20 / 20)
events.append(("action", "wind cut", 528, "cut"))
place(stems["pin"], pin_tick(), STRIKE_F, 10 ** (-10 / 20), 0.4); events.append(("pin", "brass pin tick: strike through 'monter'", STRIKE_F, "peak"))
place(stems["action"], whoosh(8 / FPS), 557, 10 ** (-16 / 20), -0.3); events.append(("action", "magpie wing whoosh (enters at silence end f554, peak f557)", 557, "peak"))
place(stems["action"], flutter(0.33), 564, 10 ** (-22 / 20), -0.4); events.append(("action", "magpie flare flutter", 564, "peak"))
place(stems["action"], thud(65, 0.45), IMPACT_F, 10 ** (-5 / 20), 0.0)
cr = crinkle(0.45, density=260, lo=900, hi=9000)
place(stems["action"], cr, IMPACT_F, 10 ** (-12 / 20), 0.05)
events.append(("action", "impact: thump + paper crumple", IMPACT_F, "peak"))
place(stems["action"], flutter(0.25), 636, 10 ** (-24 / 20), 0.3); events.append(("action", "magpie landing flutter beside the wreck", 636, "peak"))

# enforce the declared near-silence: everything but air is zero in [f540, f554)
s0, s1 = int(SILENCE[0] * SPF), int(SILENCE[1] * SPF)
for k in ("magpie", "paper", "action", "pin"):
    stems[k][s0:s1] = 0.0


# ======================================================== write + measure
def write_wav(path, st):
    st = np.clip(st, -1, 1)
    w = wave.open(str(path), "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes((st * 32767).astype("<i2").tobytes()); w.close()


mix = sum(stems.values())
peak = np.abs(mix).max()
G = min(1.0, 0.89 / peak)                     # one shared gain so stems sum to the preview mix exactly
paths = {}
for k, st in stems.items():
    p = SND / ("bang-bang_stem_%s.wav" % k); write_wav(p, st * G); paths[k] = p
write_wav(SND / "bang-bang_mix_preview.wav", mix * G)
# baseline (f432-f660, 9.5 s): air + action, NO pin tick, NO chatter; typed-strip pastes at R* paste frames
bl_paper = silent()
for s in BASELINE:
    if s["paste"]: place(bl_paper, paper_flap(), s["paste"], 10 ** (-17 / 20), 0.35)
bl = (stems["air"] + stems["action"] + bl_paper) * G
a, b = int(432 * SPF), int(660 * SPF)
write_wav(SND / "baseline_bb07-09_mix.wav", bl[a:b])


def mono(st):
    return np.abs(st).max(axis=1)


def measure(stem, frame, align, win=4):
    x = mono(stems[stem] * G)
    lo, hi = int((frame - win) * SPF), int((frame + win + 1) * SPF)
    lo = max(lo, 0)
    seg = x[lo:hi]
    if align == "peak":
        # transient envelope: 4 ms envelope minus an 80 ms running mean, so a bed (wind) under the event does not pull the peak
        a0 = max(0, lo - 4000); full = x[a0:hi + 4000]
        e = np.convolve(full, np.ones(176) / 176, "same") - np.convolve(full, np.ones(3528) / 3528, "same")
        e = e[lo - a0: lo - a0 + len(seg)]
        i = lo + int(np.argmax(e))
    elif align == "onset":
        e = np.convolve(seg, np.ones(220) / 220, "same")
        i = lo + int(np.argmax(e > 0.25 * e.max()))
    else:  # cut: last frame with wind energy
        x2 = mono(stems[stem] * G)
        pre = x2[int((frame - 3) * SPF): int(frame * SPF)]; post = x2[int(frame * SPF) + int(0.006 * RATE): int((frame + 2) * SPF)]
        return frame, {"pre_rms": float(np.sqrt((pre ** 2).mean())), "post_rms": float(np.sqrt((post ** 2).mean()))}
    return int(i // SPF), {"level_dbfs": round(20 * math.log10(x[i] + 1e-12), 1)}


meas = []
for stem, name, f, align in events:
    others = [g for st2, _, g, _ in events if st2 == stem and g != f]
    gap = min([abs(g - f) for g in others] + [9])
    win = max(1, min(4, gap // 2))          # window never reaches the neighbouring event's centre
    mf, extra = measure(stem, f, align, win)
    extra["window_pm_frames"] = win
    meas.append({"stem": stem, "event": name, "anchor_frame": f, "align": align, "measured_frame": mf,
                 "delta": mf - f, "pass_pm1": abs(mf - f) <= 1, **extra})

sil = {}
for k in stems:
    seg = stems[k][s0:s1] * G
    r = math.sqrt((seg ** 2).mean()) if seg.size else 0
    sil[k] = round(20 * math.log10(r + 1e-12), 1)
mixseg = mix[s0:s1] * G
around = mix[int(500 * SPF):int(528 * SPF)] * G

# per-frame RMS of the preview mix (for the editor)
mm = (mix * G).mean(axis=1)
frame_rms = [round(20 * math.log10(math.sqrt((mm[int(f * SPF):int((f + 1) * SPF)] ** 2).mean()) + 1e-12), 1) for f in range(720)]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


EVID = [
    {"id": "SND-PICA-PD", "title": "File:Pica pica.ogg", "author": "Oona Räisänen (Mysid)",
     "license": "Public domain (Commons extmetadata LicenseShortName 'Public domain', read 2026-11-16)", "license_url": "",
     "source_url": "https://commons.wikimedia.org/wiki/File:Pica_pica.ogg",
     "file_url": "https://upload.wikimedia.org/wikipedia/commons/b/b6/Pica_pica.ogg",
     "local_path": "films/sources/bang-bang/sound/raw/Pica_pica.ogg (sha256 %s); decoded: films/sources/bang-bang/writer-and-timing-sound-unit-nonhuman-account-cue-sheet-stems-/pica_pica_pd.wav" % sha(SRC / "sound/raw/Pica_pica.ogg"),
     "what_it_shows": "Sound, 26.5 s: a Eurasian magpie (Pica pica) in a backyard in southern Finland, two kinds of call (the rattling chatter and single 'chack' calls); a house sparrow faint in the background. Spectrogram checked: 6 chatter bursts at about 30 dB above the floor.",
     "verified_date_or_place": "2008-05-25, southern Finland (Commons description)",
     "used_as": "the magpie's chatter: bursts %s placed at f29, f264, f614, f682 (stem_magpie); high-passed at 900 Hz, edges faded" % [(round(a, 2), round(b, 2)) for a, b, _ in CHAT]},
    {"id": "MIA-AIR-A", "title": "Blackwater National Wildlife Refuge (2005)", "author": "via movingimagearchive.com (U.S. Fish and Wildlife Service)",
     "license": "Public domain (US government work, U.S. Fish and Wildlife Service); rights as listed by movingimagearchive.com, not independently verified",
     "license_url": "", "source_url": "https://www.movingimagearchive.com/sources/blackwater-national-wildlife-refuge-1677118f?clip=9be990a5-12e4-54d0-803a-46ee2566f9c3",
     "file_url": "", "local_path": "films/sources/bang-bang/writer-and-timing-sound-unit-nonhuman-account-cue-sheet-stems-/air_A_9be990a5_0.10-2.50.wav (decoded from the local cache clip)",
     "what_it_shows": "Sound: marsh air with faint small birds, clip 0.10-2.50 s (source film about 547.0-549.4 s), before the narration (same span as the researcher's MIA-AIR-A and the approved test shot).",
     "verified_date_or_place": "2005 (archive title); place: Blackwater NWR, Maryland (title)", "used_as": "air bed (stem_air), alternated with MIA-AIR-B"},
    {"id": "MIA-AIR-B", "title": "Bosque del Apache National Wildlife Refuge (2005)", "author": "via movingimagearchive.com (U.S. Fish and Wildlife Service)",
     "license": "Public domain (US government work, U.S. Fish and Wildlife Service); rights as listed by movingimagearchive.com, not independently verified",
     "license_url": "", "source_url": "https://www.movingimagearchive.com/sources/bosque-del-apache-national-wildlife-refuge-2c75717f?clip=3b4530d3-83e3-56e7-a9d7-fd17e8eaf94c",
     "file_url": "", "local_path": "films/sources/bang-bang/writer-and-timing-sound-unit-nonhuman-account-cue-sheet-stems-/air_B_3b4530d3_6.05-7.65.wav",
     "what_it_shows": "Sound: a 1.6 s pause in the narration (clip 6.05-7.65 s, source film about 281.3-282.9 s): open air, faint birds. Spectrogram checked: no speech.",
     "verified_date_or_place": "2005 (archive title); Bosque del Apache NWR, New Mexico (title)", "used_as": "air bed (stem_air)"},
]
ABSENCES = [
    "File:Pica pica - Eurasian Magpie XC537413.mp3 (CC BY-SA 4.0, Benoît Van Hecke, France 2020; the researcher's pick): metadata read, but upload.wikimedia.org answered HTTP 429 with retry-after 600 s repeatedly; not downloaded. The PD recording above replaced it, so no CC BY-SA attribution is needed for sound.",
    "Other Commons magpie calls seen in search (XC432921, XC475651, XC478076, XC551758, all CC BY-SA 4.0; W1CDR0001537 BD28, CC BY-SA 4.0): not needed; not downloaded.",
    "Moving Image Archive cache: no magpie or corvid call; the refuge films are narrated and the bird clips are scored. Speech-free outdoor air exists only in 1.6-2.4 s spans (the researcher scanned every clip with sound).",
    "No foraged paper, rubber, pin or impact recordings under an allowed licence were looked for beyond the cache. All FX are handmade synthesis, which the brief allows and the plan specifies.",
]
HANDMADE = [
    {"item": "slip paste flap", "made": "numpy: band-passed noise flutter + a card slap + a 140 Hz pat", "where": "stem_paper"},
    {"item": "page turn", "made": "numpy: a sheet swoosh peaking at the flip edge f408, crinkled edge, then the settle flap at f418", "where": "stem_paper"},
    {"item": "paper-wing rustle, crease crinkle", "made": "numpy: band noise with sparse crackle impulses", "where": "stem_action"},
    {"item": "rubber creak per winding step", "made": "numpy: stick-slip pulse train, pitch and level rising with tension over 30 steps on 2s", "where": "stem_action"},
    {"item": "release whirr, band snap 'clac', small thump, 'pof'", "made": "numpy AM noise; noise crack + falling twang; kit.Mix.thud", "where": "stem_action"},
    {"item": "footfalls on turf", "made": "numpy low noise + 85 Hz body, at leg-angle extremes read from exposure.json", "where": "stem_action"},
    {"item": "wind on the wing", "made": "kit.Mix brown noise, band-limited, rising f432-f528, hard cut at f528", "where": "stem_action"},
    {"item": "brass pin tick (strike)", "made": "numpy: a bright tick + 3.15/4.73 kHz ring decaying in 60 ms", "where": "stem_pin"},
    {"item": "magpie wing whoosh, flare and landing flutters", "made": "numpy: band noise in a Hann window, amplitude-beaten at 12 beats/s (wings on 2s)", "where": "stem_action"},
    {"item": "impact thump + paper crumple at f605", "made": "kit.Mix.thud 65 Hz + dense crackle burst, both peaks aligned on f605", "where": "stem_action"},
    {"item": "air bed", "made": "assembled from MIA-AIR-A/B slices (alternated, some reversed), 0.35 s equal-power crossfades, fade in f0-f24, fade out over the last 2.5 s", "where": "stem_air"},
]

cue_doc = {
    "film": "bang-bang", "unit": "writer and timing/sound (nonhuman account, cue sheet, stems)", "date": "2026-11-16",
    "fps": FPS, "frames": 720, "conventions": {
        "frames": "0-based film frames at 24 fps; frame f covers [f/24, (f+1)/24) s",
        "write_start_frame": "first ink of the first letter", "write_end_frame": "last letter complete",
        "cps": "characters incl. spaces and punctuation * 24 / (write_end - write_start); target 11-14",
        "one_hand": "a single pen writes serially; no two write-ons overlap (checked)",
        "anchors": "write_start anchors: ink begins within +/-1 frame of the image event; S6 'Krach !' anchors on write completion (f605); the strike anchors on f528",
    },
    "witness": {"id": "PIE", "kind": "magpie", "perceptual_limits": "only what is in the panel or its own field; no names, dates, numbers, physics terms; cannot read",
                "attitude": "calm, approving, literal-minded", "voice": "first person, one hand, one paper stock"},
    "struck_word": {"word": "monter", "slip": "S5", "strike_frame": STRIKE_F, "correction": "s'arrêter", "correction_frames": [531, 547],
                    "placement": "s'arrêter is written above the struck word"},
    "changes_from_plan_lines": [
        "S1b 'Le papier plie quand il veut. Le mien, quand je veux.' (52 chars) -> 'La mienne obéit.' (16): the original needs 3.7 s at 14 cps and would run through the 'pof' at f154. The comparison with the bird's own wing is kept.",
        "S2 'Ensuite, un moulin à élastique.' -> 'Puis un moulin à élastique.' so it ends before the release at f254.",
        "S2b 'Il le lâche, et le moulin monte tout seul. Lui reste en bas. C'est sage : il faut bien quelqu'un pour regarder.' (110 chars, about 8 s) -> 'Lui reste en bas. C'est sage.' (fits the release-to-snap window f254-f312).",
        "S3 moved from the page turn (16.6 s) to f346-f389, beside sheet 1's third panel: after the turn there is no room to write S3, S4 and 'monter' by f527 at 14 cps or less. DEPENDENCY: s1p3 must show the glider at rest so the bird can see 'les grandes ailes'.",
        "S4 'Il court face au vent. Bien.' -> 'Face au vent. Bien.' (the image already shows the running).",
        "S5b 'Moi aussi, quand je veux me poser.' (34 chars, 2.4 s) -> 'Moi aussi, pour me poser.' (25): it must finish by f592 so 'Krach !' can complete at f605 with one hand.",
        "S6 'Donc il se pose.' dropped before the impact: no room between S5b and 'Krach !'. Its inference ('he is landing') is carried by S5b ('pour me poser') and S6b/S6c.",
        "S6b/S6c 'Un peu vite. Mais au bon endroit.' split in two slips so 'au bon endroit' is anchored on the magpie's own landing beside the wreck (f638).",
    ],
    "cues": cues,
    "single_hand_overlaps": overlaps,
    "sound_only_cues": [
        {"cue": "C00", "board_id": "BB-00", "frame_range": BOARDS["BB-00"], "fx": ["air fade-in f0-f24", "sheet settle f6"]},
        {"cue": "C06", "board_id": "BB-06", "frame_range": BOARDS["BB-06"], "fx": ["page turn swoosh, flip edge peak f408 (exposure: turn f396-f418)", "sheet lands f418"],
         "note": "The task text puts the page turn at 16 s (f384). The exposure sheet has the pull-out f384-f394 and the turn f396-f418, so the sound follows the exposure."},
        {"cue": "C08-silence", "board_id": "BB-08", "frame_range": [540, 554], "fx": ["declared near-silence: air only"],
         "note": "The magpie whoosh (task: f548-f560) is moved to start at f554 (peak f557) so the declared silence holds. The bird is seen approaching in silence and heard only as it passes. S5b's paste flap (f547) is suppressed for the same reason."},
        {"cue": "C10", "board_id": "BB-10", "frame_range": BOARDS["BB-10"], "fx": ["last chatter onset f682", "air fades out over the last 2.5 s"],
         "note": "S6c's write-on ends at f674, 14 frames into BB-10's pull-out; the full-sheet hold from about f684 shows every slip complete."},
    ],
    "baseline_human_reporter": {"render": "baseline_bb07-09.mp4 (editor), f432-f660, same picture, typed strip, no strike, no chatter",
                                "sound": "films/sources/bang-bang/sound/baseline_bb07-09_mix.wav (air + action FX, no pin tick, no chatter)",
                                "slips": baseline_rows,
                                "note": "'Course d'élan.' was added for BB-07 so every board has one strip; the three plan lines are kept verbatim."},
    "dependencies_for_board_and_editor": [
        "S5 paste f476 / write f480-f525 (board.py currently pastes S5 at f474 with cps 14; same strike f528).",
        "S5b paste f547 / write f549-f592 (board.py has f552, cps 12.5, with the longer text: replace it with 'Moi aussi, pour me poser.').",
        "S3 needs the resting glider drawn in sheet-1 panel 3 (s1p3).",
        "At f580-f605 the perched magpie must be visible at the panel 2/3 edge, or its head turned toward the wreck, so the 'Krach !' passes witness precondition 2.",
    ],
    "evidence": EVID, "absences": ABSENCES, "handmade": HANDMADE,
}
json.dump(cue_doc, open(SW / "cues.json", "w"), ensure_ascii=False, indent=1)

# ---------------- swap variant: BB-07 slip <-> BB-09 slips (same slots, same hand, same rate)
def resched(texts, start, rate=13.8):
    out = []; f = start
    for sid, txt, gl in texts:
        n = len(txt); d = int(math.ceil(n * FPS / rate)); out.append((sid, txt, gl, f, f + d)); f = f + d + 3
    return out

bb09 = [(s["id"], s["text"], s["gloss"]) for s in SLIPS if s["board"] == "BB-09"]
bb07 = [(s["id"], s["text"], s["gloss"]) for s in SLIPS if s["board"] == "BB-07"]
swap_rows = []
for r in cues:
    if r["board_id"] not in ("BB-07", "BB-09"):
        swap_rows.append(dict(r, swap="unchanged"))
for sid, txt, gl, ws, we in resched(bb09, 433):
    swap_rows.append({"cue": sid + "@BB-07", "kind": "slip", "board_id": "BB-07", "frame_range": BOARDS["BB-07"], "attempt_id": "A3",
                      "image_event": "the run starts (unchanged image)", "image_event_frame": 432, "text": txt, "gloss_en_graphite": gl,
                      "paste_frame": ws - 3, "write_start_frame": ws, "write_end_frame": we, "chars": len(txt), "cps": cps(len(txt), ws, we),
                      "comment_anchor": None, "swap": "moved from BB-09",
                      "fx": ["paper flap f%d (paste)" % (ws - 3)], "depends_on_outcome": True,
                      "contrast": "Now precedes its referent: the slip anticipates a crash and a landing that have not happened. The image-only read is unchanged."})
for sid, txt, gl, ws, we in resched(bb07, 593):
    swap_rows.append({"cue": sid + "@BB-09", "kind": "slip", "board_id": "BB-09", "frame_range": BOARDS["BB-09"], "attempt_id": "A3",
                      "image_event": "impact f605 (unchanged image)", "image_event_frame": 605, "text": txt, "gloss_en_graphite": gl,
                      "paste_frame": ws - 3, "write_start_frame": ws, "write_end_frame": we, "chars": len(txt), "cps": cps(len(txt), ws, we),
                      "comment_anchor": None, "swap": "moved from BB-07",
                      "fx": ["paper flap f%d (paste)" % (ws - 3)], "depends_on_outcome": False,
                      "contrast": "Approves facing the wind while the wreck lies there: it reads as calm misplaced praise."})
sp = sorted((r["write_start_frame"], r["write_end_frame"], r["cue"]) for r in swap_rows)
swap_doc = {"film": "bang-bang", "variant": "BB-07/BB-09 slip swap (replay experiment, plan sec. 4)",
            "rule": "Image and exposure unchanged. The BB-09 slips are rewritten serially from f433 and the BB-07 slip from f593, at the same hand and 13.8 cps. 'Krach !' no longer completes at f605. The three BB-09 slips (39 chars) do not fit BB-07's window before S5 at 14 cps, so the last one (S6c) overlaps S5's write-on: declared, part of the experiment (or the editor drops S6c from the swap render).",
            "expected": {"image_only": "equivalent: it failed", "voice_only": "equivalent set of claims, different order",
                         "combined": "diverges: the 'Krach !' before the run makes the bird prophetic, and 'Face au vent. Bien.' over the wreck reads as misplaced praise; the anchor tests (Krach at f605 +/-1, au bon endroit at f638 +/-1) fail by design"},
            "anchor_tests": {"krach_completion_f605": False, "bon_endroit_on_landing_f638": False, "strike_f528": True},
            "single_hand_overlaps": [(a[2], b[2]) for a, b in zip(sp, sp[1:]) if b[0] < a[1]],
            "cues": swap_rows}
json.dump(swap_doc, open(SW / "cues_swap.json", "w"), ensure_ascii=False, indent=1)

stems_doc = {
    "film": "bang-bang", "rate": RATE, "channels": 2, "bits": 16, "seconds": SECONDS, "frames": 720,
    "shared_gain_applied": round(G, 4), "sum_rule": "the five stems sum exactly to bang-bang_mix_preview.wav (one shared gain, no limiter); the editor may rebalance",
    "stems": {
        "air": {"path": str(paths["air"].relative_to(FILMS.parent)), "sources": ["MIA-AIR-A", "MIA-AIR-B"], "kind": "foraged (assembled bed)"},
        "magpie": {"path": str(paths["magpie"].relative_to(FILMS.parent)), "sources": ["SND-PICA-PD"], "kind": "foraged"},
        "paper": {"path": str(paths["paper"].relative_to(FILMS.parent)), "sources": ["handmade"], "kind": "handmade"},
        "action": {"path": str(paths["action"].relative_to(FILMS.parent)), "sources": ["handmade"], "kind": "handmade"},
        "pin": {"path": str(paths["pin"].relative_to(FILMS.parent)), "sources": ["handmade"], "kind": "handmade (strike tick only, so the baseline can omit it)"},
    },
    "preview_mix": "films/sources/bang-bang/sound/bang-bang_mix_preview.wav",
    "baseline_mix": "films/sources/bang-bang/sound/baseline_bb07-09_mix.wav (f432-f660, 9.5 s)",
    "measured_events": meas,
    "all_events_pass_pm1": all(m["pass_pm1"] for m in meas),
    "failures": [m for m in meas if not m["pass_pm1"]],
    "declared_silence": {"frames": list(SILENCE), "rms_dbfs_by_stem": sil,
                         "mix_rms_dbfs": round(20 * math.log10(math.sqrt((mixseg ** 2).mean()) + 1e-12), 1),
                         "mix_rms_dbfs_f500_f528": round(20 * math.log10(math.sqrt((around ** 2).mean()) + 1e-12), 1),
                         "pass": all(v < -90 for k, v in sil.items() if k != "air")},
    "key_anchors": {m["event"]: {"anchor": m["anchor_frame"], "measured": m["measured_frame"]} for m in meas
                    if m["anchor_frame"] in (154, 312, 331, 528, 557, 605, 408)},
    "frame_rms_dbfs_mix": frame_rms,
    "sha256": {k: sha(p) for k, p in paths.items()},
}
json.dump(stems_doc, open(SW / "stems.json", "w"), ensure_ascii=False, indent=1)

print("bursts", [(round(a, 2), round(b, 2)) for a, b, _ in CHAT])
print("footfalls", FOOT)
print("overlaps", overlaps, "swap overlaps", swap_doc["single_hand_overlaps"])
print("gate fails", [(r["cue"], r["witness_gate"]["lexicon_failures"]) for r in cues if r["witness_gate"]["lexicon_failures"]])
print("cps out of range", [(r["cue"], r["cps"]) for r in cues if r["cps"] is not None and not r["cps_in_11_14"]])
print("anchors", [(r["cue"], r["comment_anchor"]) for r in cues if r["comment_anchor"]])
print("events fail", stems_doc["failures"])
print("silence", stems_doc["declared_silence"])
print("gain", G)
