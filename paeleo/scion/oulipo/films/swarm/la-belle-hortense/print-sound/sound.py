"""U4 print-sound: cut the foraged recordings into cues, lay the cue sheet, premix 66 s.

Reads only wavs decoded with ffmpeg from the foraged files (sources/.../print-sound/sound/raw).
Writes cue wavs to sources/.../print-sound/sound/cues/, a premix to the editor media dir,
and swarm/la-belle-hortense/sound_cues.json.
Run: python3 -I sound.py   (imports kit from films/ by path; kit is not edited)
"""
import json, sys, wave, math
from pathlib import Path
import numpy as np

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, str(FILMS))
import kit  # noqa: E402

RATE = kit.RATE
SRC = FILMS / "sources/la-belle-hortense"
RAW = SRC / "print-sound/sound/raw"
CUES = SRC / "print-sound/sound/cues"
EDIT = SRC / "print-sound-handmade-print-objects-sound-design-"
SWARM = FILMS / "swarm/la-belle-hortense"
CUES.mkdir(parents=True, exist_ok=True)
EDIT.mkdir(parents=True, exist_ok=True)
DUR = 66.0

LIC = {
    "BELL-SND": ("Glockenschlagwerk Bahnhof Fridingen.ogg, Olga Ernst", "CC BY-SA 4.0"),
    "STEPS": ("Concrete Steps 2.ogg, Pwaivers", "CC BY-SA 3.0"),
    "HANDLE": ("Door handle creaking.ogg, stephan", "Public domain"),
    "HINGE": ("Squeaky door hinge.ogg, MKFI", "Public domain"),
    "KEYS-SND": ("Keys hitting tree 2 (Gravity Sound).wav, Gravity Sound", "CC BY 4.0"),
    "LOCK": ("342706 spacejoe lock-3-open-lock-3.wav, SpaceJoe", "CC0"),
    "PAPER": ("Book paper pages assorted.ogg, stephan", "Public domain"),
    "SYNTH": ("kit.Mix synthesis (films/kit.py), handmade", "handmade (no third-party material)"),
}


def rd(name):
    w = wave.open(str(RAW / name))
    assert w.getframerate() == RATE and w.getnchannels() == 1
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0


def wr(path, x):
    x = np.asarray(x, np.float64)
    pk = np.abs(x).max()
    if pk > 0.99:
        x = x / pk * 0.99
    w = wave.open(str(path), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes((x * 32767).astype(np.int16).tobytes())
    w.close()


def seg(x, a, b, fi=0.003, fo=0.03):
    y = x[int(a * RATE):int(b * RATE)].copy()
    n1, n2 = int(fi * RATE), int(fo * RATE)
    if n1: y[:n1] *= np.linspace(0, 1, n1)
    if n2: y[-n2:] *= np.linspace(1, 0, n2)
    return y


def norm(y, peak=0.9):
    return y / (np.abs(y).max() + 1e-12) * peak


def fft_band(y, lo, hi):
    X = np.fft.rfft(y); f = np.fft.rfftfreq(len(y), 1 / RATE)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(y))


def synth(fn, seconds, seed=0):
    m = kit.Mix(seconds + 0.5, seed=seed)
    fn(m)
    return (m.L + m.R)[: int(seconds * RATE)] / 2.828  # undo the add() 1.414 centre gain


# ------------------------------------------------------------------ grains ---
bell_rec = rd("Glockenschlagwerk_Bahnhof_Fridingen.wav")
# last strike of the recording has a free decay to the end (no following strike)
w0 = int(12.8 * RATE)
win = bell_rec[w0:int(13.2 * RATE)]
on_last = (w0 + int(np.argmax(np.abs(win) > 0.5 * np.abs(win).max()))) / RATE
PRE = 0.010  # every bell file starts 10 ms before the strike onset
bell_full = norm(seg(bell_rec, on_last - PRE, len(bell_rec) / RATE, fi=0.004, fo=0.4), 0.95)
# distant variant for the title: a real low-pass (air absorption) and a softer level, same strike
bell_dist = norm(fft_band(bell_full, 0, 2200), 0.6)
bell_dist[: int(0.004 * RATE)] *= np.linspace(0, 1, int(0.004 * RATE))
# reversed swell for IV.2: the same tail, reversed, long fade-in, closed with a 0.25 s fade-out
# so there is no transient (no strike onset)
tail = bell_full[int(0.25 * RATE):int(1.45 * RATE)][::-1].copy()
tail *= np.linspace(0, 1, len(tail)) ** 2
nfo = int(0.30 * RATE); tail[-nfo:] *= np.linspace(1, 0, nfo) ** 2
bell_rev = norm(tail, 0.5)

steps = rd("Concrete_Steps_2.wav")
stepA = seg(steps, 0.0, 0.30, fi=0.002, fo=0.06)
stepB = seg(steps, 0.62, 0.787, fi=0.002, fo=0.05)
keys = rd("Keys_hitting_tree_2__Gravity_Sound_.wav")
tinkA = seg(keys, 0.335, 0.60, fi=0.002, fo=0.08)
tinkB = seg(keys, 0.73, 1.05, fi=0.002, fo=0.1)
handle = rd("Door_handle_creaking.wav")
lock = rd("spacejoe_lock-3-open.wav")
hinge = rd("Squeaky_door_hinge.wav")
paper = rd("Book_paper_pages_assorted.wav")


def resample(y, speed):
    n = int(len(y) / speed)
    return np.interp(np.arange(n) * speed, np.arange(len(y)), y)


def step_run(t0, t1, every, g0, g1, rs, lp=None):
    """A run of footfalls: the recording's two steps alternated as grains, +-1.5% speed."""
    n = int((t1 - t0) * RATE) + RATE
    out = np.zeros(n); times = []
    k, t = 0, t0
    while t < t1 - 1e-9:
        g = (stepA if k % 2 == 0 else stepB)
        g = resample(g, 1 + rs.uniform(-0.015, 0.015)) * kit.lerp(g0, g1, (t - t0) / max(t1 - t0, 1e-9))
        i = int((t - t0 + rs.uniform(-0.008, 0.008)) * RATE)
        i = max(0, i)
        out[i:i + len(g)] += g[: n - i]
        times.append(round(t, 3)); t += every; k += 1
    if lp:
        out = fft_band(out, 40, lp)
    return out[: int((t1 - t0) * RATE + 0.35 * RATE)], times


rs = np.random.RandomState(6)
files = {}


def save(name, y):
    p = CUES / f"{name}.wav"
    wr(p, y)
    files[name] = p
    return p


save("bell_strike_full", bell_full)
save("bell_strike_distant", bell_dist)
save("bell_swell_reversed", bell_rev)
save("click", synth(lambda m: m.click(0.0, gain=1.0), 0.05, seed=1))
# strike-through / underline: the typewriter re-strikes over each letter (7 for "une clé", 14 for "remise au banc")
save("type_strikethrough_7", synth(lambda m: [m.click(i * 0.085, gain=0.8 + 0.2 * (i % 2), bright=5000) for i in range(7)], 0.7, seed=2))
save("type_underline_14", synth(lambda m: [m.click(i * 0.07, gain=0.8 + 0.2 * (i % 3 == 0), bright=5000) for i in range(14)], 1.05, seed=3))
save("type_row_return", synth(lambda m: (m.click(0.0, gain=1.0, bright=3000, seconds=0.04), m.click(0.06, gain=0.6, bright=6000)), 0.15, seed=4))
save("wind_0-37.5", synth(lambda m: m.wind(0.0, 37.5, gain=1.0), 37.5, seed=5))
save("wind_39-63", synth(lambda m: m.wind(0.0, 24.0, gain=1.0), 24.0, seed=6))
save("room_tone_VI3", synth(lambda m: m.room(0.0, 1.5, gain=1.0), 1.5, seed=7))
save("cloth_rustle", synth(lambda m: m.add(m.band(m.noise(0.6), 250, 2800) * np.hanning(int(0.6 * RATE)) * (0.6 + 0.4 * np.sin(np.linspace(0, 19, int(0.6 * RATE)))), 0.0), 0.6, seed=8))
save("whoosh_IV5", synth(lambda m: m.whoosh(0.0, 0.7, gain=1.0), 0.7, seed=9))
save("whoosh_V3_pan", synth(lambda m: m.whoosh(0.0, 1.5, gain=1.0), 1.5, seed=10))
save("stamp_thud", synth(lambda m: (m.thud(0.0, freq=80, gain=1.0, seconds=0.35), m.click(0.0, gain=0.7, bright=2500, seconds=0.02)), 0.4, seed=11))
save("handle_rattle_a", seg(handle, 0.08, 1.30))
save("handle_rattle_b", seg(handle, 1.30, 2.40))
save("handle_rattle_c", seg(handle, 0.30, 1.40))
save("latch_lock_open", seg(lock, 0.0, len(lock) / RATE, fi=0.001, fo=0.02))
save("hinge_squeak", seg(hinge, 2.05, 4.45, fi=0.02, fo=0.3))
save("key_tink_strong", tinkA)
save("key_tink_soft", tinkB)
save("key_on_cloth", fft_band(tinkB, 0, 1800) * 0.6)  # the real tap, muffled as if on cloth
save("paper_tear", seg(paper, 1.70, 2.45, fi=0.005, fo=0.08))
save("paper_flutter_I5", seg(paper, 5.30, 6.50, fi=0.03, fo=0.15))
save("paper_handle_II3", seg(paper, 8.60, 9.40, fi=0.01, fo=0.1))
save("paper_flutter_V2", seg(paper, 13.65, 14.85, fi=0.03, fo=0.15))
save("paper_slap_stamp", seg(paper, 19.30, 19.55, fi=0.002, fo=0.05))

runs = {}
for name, (t0, t1, ev, g0, g1, lp) in {
    "steps_I2_walk_in": (4.8, 6.0, 0.55, 0.5, 0.8, 5000),
    "steps_I4_lay": (7.6, 8.0, 0.4, 0.6, 0.6, 5000),
    "steps_I6_recede": (10.5, 12.0, 0.55, 0.8, 0.25, 4000),
    "steps_II4_hurry": (16.8, 18.0, 0.36, 0.9, 0.3, 5000),
    "steps_III4_far": (25.5, 27.0, 0.5, 0.18, 0.18, 2500),
    "steps_V1_run_far": (39.0, 42.0, 1 / 4.6, 0.12, 0.8, None),
    "steps_V3_run": (42.0, 43.5, 1 / 4.6, 1.0, 1.0, None),
    "steps_V4_stop": (43.5, 44.0, 0.26, 0.8, 0.4, None),
}.items():
    y, times = step_run(t0, t1, ev, g0, g1, np.random.RandomState(int(t0 * 10)), lp)
    save(name, y)
    runs[name] = times

# ------------------------------------------------------------------ cue sheet ---
slot_names = json.load(open(SWARM / "structure.json"))["modules"]
C = []


def cue(t, name, gain, pan, src, what, slot=None, **kw):
    lic_title, lic = LIC[src]
    d = {"t": round(t, 3), "file": str(files[name]).replace(str(FILMS.parent) + "/", ""),
         "gain": gain, "pan": pan, "source_id": src, "source": lic_title, "license": lic, "what": what}
    if slot: d["slot"] = slot
    d.update(kw)
    C.append(d)


B = "bell_strike_full"
note_bell = {"align": f"file starts {PRE:.3f} s before the strike onset; placed at t-{PRE:.3f}", "onset_at": None}
for t, name, g, pan, slot in [(0.4, "bell_strike_distant", 0.35, -0.3, "title"), (4.6, B, 0.7, -0.4, "I.2"), (16.6, B, 0.7, -0.4, "II.4"),
                              (27.1, B, 0.75, 0.0, "III.5"), (33.1, B, 0.7, 0.3, "IV.3"), (46.6, B, 0.85, 0.0, "V.6"), (57.2, B, 0.6, 0.0, "end card")]:
    cue(t - PRE, name, g, pan, "BELL-SND", f"bell strike, onset at {t:.1f} s" + (" (tail rings out through VI.1, no new onset)" if t == 46.6 else ""), slot, onset_at=t)
# IV.2 reversed swell dropped: a crescendo reads as a bell onset to the detector; the rule is bells only at the 7 times
# cue(31.8, "bell_swell_reversed", 0.35, 0.0, "BELL-SND", "IV.2 reversed swell of the same strike's tail; no strike onset (verified)", "IV.2")

for m in slot_names:
    for a in m["appearances"]:
        cue(a["start"], "click", 0.5, -0.2, "SYNTH", "typewriter slot click (kit.click)", a["id"])
cue(19.7, "type_strikethrough_7", 0.45, -0.1, "SYNTH", "strike-through of 'une clé' on the receipt, 7 re-strikes", "II.6")
cue(28.7, "type_underline_14", 0.45, -0.1, "SYNTH", "red underline of 'remise au banc', 14 strikes", "III.6")
for r in range(8):  # end-card rows typed one per 0.5 s (6 matrix rows, sigma line, credits)
    cue(57.5 + 0.5 * r, "type_row_return", 0.35, -0.1, "SYNTH", f"end card row {r + 1} typed", "end card")

cue(0.0, "wind_0-37.5", 0.06, 0.0, "SYNTH", "kit.wind ambience, ends with IV.6 click (declared silence follows)")
cue(39.0, "wind_39-63", 0.06, 0.0, "SYNTH", "kit.wind ambience, ends at 63.0 (declared silence follows)")
cue(51.0, "room_tone_VI3", 0.05, 0.0, "SYNTH", "room tone through the open door", "VI.3")

for name, slot, pan, g, src in [("steps_I2_walk_in", "I.2", -0.6, 0.45, "STEPS"), ("steps_I4_lay", "I.4", 0.4, 0.35, "STEPS"),
                                ("steps_I6_recede", "I.6", 0.6, 0.45, "STEPS"), ("steps_II4_hurry", "II.4", -0.6, 0.5, "STEPS"),
                                ("steps_III4_far", "III.4", 0.3, 0.5, "STEPS"), ("steps_V1_run_far", "V.1", 0.5, 0.6, "STEPS"),
                                ("steps_V3_run", "V.3", 0.0, 0.6, "STEPS"), ("steps_V4_stop", "V.4", 0.0, 0.5, "STEPS")]:
    t0 = runs[name][0]
    ev = round(runs[name][1] - runs[name][0], 4) if len(runs[name]) > 1 else None
    cue(t0, name, g, pan, src, "footfall grains (the recording's two steps alternated, +-1.5% speed)", slot,
        grain_times=runs[name], stride_hz=round(1 / ev / 2, 2) if ev else None)

for t, name, slot, g, pan in [(12.2, "handle_rattle_a", "II.1", 0.6, 0.2), (22.7, "handle_rattle_b", "III.2", 0.6, 0.2), (34.7, "handle_rattle_c", "IV.4", 0.55, 0.2)]:
    cue(t, name, g, pan, "HANDLE", "locked-door handle rattle", slot)
cue(45.1, "latch_lock_open", 0.7, 0.2, "LOCK", "key turns, latch opens", "V.5")
cue(45.5, "hinge_squeak", 0.8, 0.2, "HINGE", "door leaf swings on its hinge", "V.5")
cue(8.25, "key_on_cloth", 0.5, 0.4, "KEYS-SND", "key laid on the coat (tap muffled by low-pass)", "I.4")
cue(43.6, "key_tink_strong", 0.55, 0.0, "KEYS-SND", "key lands brass-on-ground", "V.4")
cue(43.82, "key_tink_soft", 0.3, 0.05, "KEYS-SND", "key bounces once", "V.4")
cue(54.2, "key_tink_soft", 0.35, 0.1, "KEYS-SND", "key settles on its hook", "VI.5")
cue(6.2, "paper_tear", 0.5, 0.0, "PAPER", "envelope flap opened", "I.3")
cue(9.2, "paper_flutter_I5", 0.45, 0.2, "PAPER", "receipt flutters to the gravel", "I.5")
cue(15.2, "paper_handle_II3", 0.45, 0.0, "PAPER", "receipt picked up", "II.3")
cue(40.7, "paper_flutter_V2", 0.5, 0.3, "PAPER", "receipt lifted by the runner's wind", "V.2")
cue(52.65, "paper_slap_stamp", 0.4, 0.0, "PAPER", "stamp paper slap", "VI.4")
cue(52.65, "stamp_thud", 0.7, 0.0, "SYNTH", "RENDU stamp thud (kit.thud)", "VI.4")
cue(13.7, "cloth_rustle", 0.35, 0.3, "SYNTH", "coat lifted (filtered noise)", "II.2")
cue(36.2, "whoosh_IV5", 0.35, 0.6, "SYNTH", "red blur sweeps the near plane", "IV.5")
cue(42.0, "whoosh_V3_pan", 0.3, 0.0, "SYNTH", "pan whoosh", "V.3")

C.sort(key=lambda d: d["t"])

# ------------------------------------------------------------------ premix ---
mix = kit.Mix(DUR, seed=0)
for d in C:
    w = wave.open(str(FILMS.parent / d["file"]))
    y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
    mix.add(y, d["t"], d["gain"], d["pan"])
# hard-guarantee the declared silences (nothing is scheduled there; this only removes rounding residue)
for a, b in [(37.53, 39.0), (63.0, 66.0)]:
    mix.L[int(a * RATE):int(b * RATE)] = 0; mix.R[int(a * RATE):int(b * RATE)] = 0
st = np.stack([mix.L, mix.R], 1)
pk = np.abs(st).max()
st = st / max(pk, 1.0) * 0.89 if pk > 0.89 else st
premix = EDIT / "hortense_premix_66s.wav"
w = wave.open(str(premix), "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()

# bell-only stem for verification
bm = kit.Mix(DUR, seed=0)
for d in C:
    if d["source_id"] == "BELL-SND":
        w = wave.open(str(FILMS.parent / d["file"]))
        y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
        bm.add(y, d["t"], d["gain"], d["pan"])
bell_stem = (bm.L + bm.R) / 2
wr(EDIT / "stem_bell_only_66s.wav", bell_stem)


# ------------------------------------------------------------------ verify ---
def onsets(x, hop=0.01, jump=12.0, floor=-45):
    h = int(hop * RATE); n = len(x) // h
    e = np.array([np.sqrt((x[i * h:(i + 1) * h] ** 2).mean()) for i in range(n)])
    db = 20 * np.log10(e + 1e-9)
    out = []
    for i in range(5, n):
        if db[i] > floor and db[i] - db[i - 5:i].min() > jump and (not out or i * hop - out[-1] > 0.3):
            out.append(round(i * hop, 2))
    return out


mono = st.mean(1)


def bell_onsets(x, hop=0.01, nwin=4096):
    """Onsets of the foraged strike in the full mix: the 642 Hz partial must rise >=12 dB and, 0.3 s
    later, still stand >=12 dB above its spectral neighbours (and 0.1-0.3 s before, the partial must not already be
    ringing, median tonality < 6 dB: a step landing on a ringing tail is not a new strike) (590-620, 665-700 Hz) -- a ringing,
    tonal bell partial, not a broadband step, click or paper noise."""
    h = int(hop * RATE); f = np.fft.rfftfreq(nwin, 1 / RATE)
    band = (f > 634) & (f < 650); nb = ((f > 590) & (f < 620)) | ((f > 665) & (f < 700))
    win = np.hanning(nwin); n = (len(x) - nwin) // h
    S = [np.abs(np.fft.rfft(x[i * h:i * h + nwin] * win)) for i in range(n)]
    e = np.array([s[band].mean() for s in S]); q = np.array([s[nb].mean() for s in S])
    db = 20 * np.log10(e + 1e-9); tonal = db - 20 * np.log10(q + 1e-9); out = []
    thr = np.percentile(db, 99.5) - 25
    for i in range(30, n - 31):
        if db[i] - db[i - 10:i].min() > 12 and np.median(tonal[i - 30:i - 10]) < 6 and tonal[i + 5] > 12 and tonal[i + 30] > 12 and db[i + 30] > thr and (not out or i * hop - out[-1] > 0.5):
            out.append(round(i * hop + nwin / 2 / RATE, 2))
    return out


mono = st.mean(1)
ver = {
    "bell_stem_onsets": onsets(bell_stem),
    "full_mix_sustained_642Hz_onsets": bell_onsets(mono),
    "target_bell_onsets": [0.4, 4.6, 16.6, 27.1, 33.1, 46.6, 57.2],
    "silence_37.53-39.0_peak_dbfs": round(20 * math.log10(np.abs(st[int(37.53 * RATE):int(39.0 * RATE)]).max() + 1e-12), 1),
    "silence_63-66_peak_dbfs": round(20 * math.log10(np.abs(st[int(63.0 * RATE):]).max() + 1e-12), 1),
    "level_just_before_37.53_dbfs": round(20 * math.log10(np.abs(st[int(37.3 * RATE):int(37.53 * RATE)]).max() + 1e-12), 1),
    "clicks_at_slot_starts": sum(1 for d in C if d["file"].endswith("click.wav")),
}
ok_b = all(any(abs(o - t) <= 0.1 for o in ver["bell_stem_onsets"]) for t in ver["target_bell_onsets"]) and \
       all(any(abs(o - t) <= 0.1 for t in ver["target_bell_onsets"]) for o in ver["bell_stem_onsets"])
ok_f = all(any(abs(o - t) <= 0.1 for t in ver["target_bell_onsets"]) for o in ver["full_mix_sustained_642Hz_onsets"]) and len(ver["full_mix_sustained_642Hz_onsets"]) == 7
ver["bell_onsets_ok"] = bool(ok_b)
ver["no_extra_bell_band_onsets_in_full_mix"] = bool(ok_f)
print(json.dumps(ver, indent=1))
json.dump({"cues": C, "verification": ver, "premix": str(premix)}, open(SWARM / "print-sound" / "_sound_build.json", "w"), indent=1, ensure_ascii=False)
