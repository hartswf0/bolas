"""Sound stems for Le Chant du styrène (38.0 s, 44.1 kHz stereo int16, all aligned at film t = 0).

Handmade by modal synthesis (numpy, via kit.Mix helpers) except press_foraged.wav, which is the real
recorded sound of an Engel injection moulding machine (Commons, CC BY 3.0; see process_verse.json).

Every stem is written with ONE fixed scale (no per-stem normalisation), so the editor can sum them at the
suggested gains in cues.json. Timings come from cues.json (written here from the verse table, the cutout
unit's geometry.json timing and the proposed drain order); re-run with edited cues.json if a unit changes them:

  python3 -I stems.py              # write cues.json (if absent) and all stems + mix_preview.wav
  python3 -I stems.py --recue      # rebuild cues.json from sources first
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
import kit  # noqa: E402  (read-only use of Mix helpers)

SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/"
           "process-verse-process-researcher-verse-writer-voice-sound-performer-")
STEMS = OUT / "stems"
DUR, R = 38.0, 44100
SCALE = 0.5  # fixed output scale for every stem
PULSE, GAP = 0.30, 0.45
LINES = {"L1": 2.40, "L2": 11.00, "L3": 19.60, "L4": 29.40}


def onset(line, k):
    return LINES[line] + (k - 1) * PULSE + (GAP if k > 6 else 0.0)


def build_cues():
    g = json.loads((SW / "geometry.json").read_text())
    tm = g["timing"]
    rings = {}
    for r in g["rings"]:
        x = r["film"]["sh2b_hold"]["home_centre"][0]
        rings[str(r["ring"])] = dict(launch=tm["flights"][str(r["ring"])][0], home=tm["flights"][str(r["ring"])][1],
                                     pan=round(float(np.clip((x - 480) / 480 * 0.7, -0.7, 0.7)), 3))
    return dict(
        note="film-time seconds; ring times from geometry.json timing (cutout unit); drain times PROPOSED to the melt unit "
             "(far cavity first, 1.0 s apart, the user's fix 'larger time differences'); re-run stems.py after editing",
        verse={l: [round(onset(l, k), 3) for k in range(1, 13)] for l in LINES},
        ring_setdown_sh1=0.60,
        rings=rings,
        drain=dict(tone=[21.00, 26.30], cavity_release_far_to_near=[21.90, 22.90, 23.90, 24.90],
                   cavity_pans=[0.35, -0.40, 0.15, -0.10], sprue_glug=26.20),
        rain=dict(start=26.80, sh4_from=27.60, peak=33.60, heap_cut=35.00, stop=36.50),
        chord=33.60,
        press_foraged=dict(in_=[18.8, 19.8], out=[26.4, 27.4], source_seconds=[2.0, 12.8]),
        room=[0.0, 38.0, "fade out 36.6-37.8"],
        suggested_gains=dict(meter=1.0, ring_events=1.0, drain=0.9, rain=0.8, chord=0.8, room=1.0, press_foraged=1.0),
    )


rs = np.random.RandomState(1958)
mx = kit.Mix(DUR, seed=1958)


def T(sec):
    return np.arange(int(sec * R)) / R


def modal(f0, ratios, amps, taus, sec, strike=0.002):
    t = T(sec)
    s = sum(a * np.sin(2 * np.pi * f0 * q * t + rs.uniform(0, 6.28)) * np.exp(-t / tau) for q, a, tau in zip(ratios, amps, taus))
    s *= 1 - np.exp(-t / strike)
    return s


def plus(a, b):
    n = max(len(a), len(b))
    return np.pad(a, (0, n - len(a))) + np.pad(b, (0, n - len(b)))


def contact(sec, lo, hi, k=60.0):
    x = rs.normal(0, 1, int(sec * R)) * np.exp(-T(sec) * k)
    return mx.band(x, lo, hi)


class Bus:
    def __init__(self):
        self.L = np.zeros(int(DUR * R))
        self.Rt = np.zeros(int(DUR * R))

    def add(self, sig, at, gain=1.0, pan=0.0):
        i = int(round(at * R))
        if i >= len(self.L):
            return
        sig = sig[: len(self.L) - i] * gain
        lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:i + len(sig)] += sig * lg * 1.414
        self.Rt[i:i + len(sig)] += sig * rg * 1.414

    def st(self):
        return np.stack([self.L, self.Rt], 1)


def write(name, st):
    st = np.clip(st * SCALE, -1, 1)
    p = STEMS / name
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return p, float(np.abs(st).max())


# ---------------------------------------------------------------- pulses ---
RING_MODES = [1.0, 2.83, 5.43, 8.87]          # thin free ring, flexural n=2..5 normalised (n(n^2-1)/sqrt(n^2+1))
BEAM_MODES = [1.0, 2.757, 5.404, 8.933]        # free-free beam (runner arm)


def pulse_hollow(k, f0, modes, accent):
    tau = 0.045 if not accent else 0.09
    s = modal(f0 * (1 + 0.012 * rs.randn()), modes, [1.0, 0.55, 0.3, 0.15], [tau, tau * 0.6, tau * 0.4, tau * 0.25], 0.35)
    return plus(s, 0.5 * contact(0.03, 900, 6000, 120))


def pulse_viscous(k, accent):
    sec = 0.55 if accent else 0.27
    t = T(sec)
    f0 = (74 if k == 12 else 98) - (0 if accent else 2.5 * (k - 1) % 9)
    f = f0 * (1 + 0.35 * np.exp(-t * 22)) * (1 - 0.12 * t / sec)
    ph = 2 * np.pi * np.cumsum(f) / R
    body = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    e = (1 - np.exp(-t * 90)) * np.exp(-t * (5 if accent else 11))
    blub = mx.band(rs.normal(0, 1, len(t)), 150, 900) * np.exp(-t * 30) * 0.25
    return (body * e + blub) * 0.8


def pulse_granular(k, accent):
    sec = 0.16 if not accent else 0.24
    out = np.zeros(int(sec * R) + 2000)
    n = 22 if not accent else 40
    for j in range(n):
        at = int(abs(rs.exponential(sec / 5)) * R) if j else 0
        at = min(at, int(sec * R))
        g = modal(rs.uniform(2600, 6200), [1.0, 2.3], [1.0, 0.4], [0.006, 0.003], 0.04, strike=0.0002)
        out[at:at + len(g)] += g * rs.uniform(0.3, 1.0) * (1.0 if j == 0 else 0.55)
    return out * 0.55


def meter():
    b = Bus()
    pitch_contour = [0, 2, 3, 4, 5, 7, 3, 2, 1, 0, -1, -4]  # semitones: rising to the caesura accent, falling to the end
    for line in LINES:
        for k in range(1, 13):
            acc = k in (6, 12)
            at = onset(line, k)
            pan = -0.12 + 0.02 * k
            if line == "L1":
                s = pulse_hollow(k, 1180 * 2 ** (pitch_contour[k - 1] / 12), RING_MODES, acc)
                g = 0.55 if acc else 0.38
            elif line == "L2":
                s = pulse_hollow(k, 640 * 2 ** (pitch_contour[k - 1] / 12), BEAM_MODES, acc)
                g = 0.60 if acc else 0.42
            elif line == "L3":
                s = pulse_viscous(k, acc); g = 0.75 if acc else 0.55
            else:
                s = pulse_granular(k, acc); g = 1.40 if acc else 1.00
            b.add(s, at, g, pan)
    return b.st()


# ------------------------------------------------------------ ring events ---
def ring_hit(f0, bright=1.0):
    s = modal(f0, RING_MODES, [1.0, 0.6, 0.35, 0.2], [0.07, 0.04, 0.025, 0.015], 0.4)
    s = plus(s, modal(f0 * 0.53, BEAM_MODES, [0.6, 0.3, 0.15, 0.1], [0.05, 0.03, 0.02, 0.01], 0.3))  # the runner arm it lands on
    return plus(s, 0.8 * bright * contact(0.02, 1500, 9000, 200))


def ring_events(c):
    b = Bus()
    # Sh1: one ring set down on black at 0.6 s, a little rattle
    b.add(ring_hit(1250), c["ring_setdown_sh1"], 0.45, 0.25)
    for j, dt in enumerate([0.07, 0.115, 0.15]):
        b.add(ring_hit(1250, 0.6) * 0.5 ** (j + 1), c["ring_setdown_sh1"] + dt, 0.45, 0.25)
    for rid, r in sorted(c["rings"].items()):
        f0 = {"1": 1180, "2": 1090, "3": 1270, "4": 1010}.get(rid, 1150)
        # launch: a short lift-off tick + air whoosh along the flight
        b.add(contact(0.015, 2000, 8000, 300), r["launch"], 0.12, r["pan"])
        fl = 0.45  # a short air whoosh as the ring lifts (not over the whole flight)
        w = mx.band(rs.normal(0, 1, int(fl * R)), 400, 4500) * np.hanning(int(fl * R)) ** 1.5
        b.add(w, r["launch"], 0.045, r["pan"] * 0.6)
        # home: snap onto the gate stub, then the spring-damper settle (3.2 Hz, zeta 0.22) as a decaying rattle
        b.add(ring_hit(f0), r["home"], 0.7, r["pan"])
        if rid != "1":
            tau, k = 0.0, 0
            per = 1 / 3.2 / 2  # contacts at each half period of the settle oscillation
            amp = 1.0
            while amp > 0.06 and r["home"] + tau < 15.75:
                tau += per * (0.92 ** k); amp *= np.exp(-0.22 * np.pi / np.sqrt(1 - 0.22 ** 2)) ** 0.5; k += 1
                b.add(ring_hit(f0 * (1 + 0.01 * k), 0.4), r["home"] + tau, 0.5 * amp, r["pan"])
    return b.st()


# ------------------------------------------------------------------ drain ---
def drain(c):
    b = Bus()
    d = c["drain"]
    a0, a1 = d["tone"]
    sec = a1 - a0; t = T(sec)
    f = 190 * (55 / 190) ** (t / sec)
    ph = 2 * np.pi * np.cumsum(f) / R
    tone = np.sin(ph) * 0.6 + 0.25 * np.sin(1.5 * ph)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(7 + 5 * t / sec) / R)
    gurg = mx.band(rs.normal(0, 1, len(t)).cumsum(), 60, 500); gurg /= np.abs(gurg).max() + 1e-9
    env = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 0.7 * (0.4 + 0.6 * t / sec)
    b.add((tone * 0.5 + gurg * am * 0.8) * env, a0, 0.5)
    for i, (ti, pan) in enumerate(zip(d["cavity_release_far_to_near"], d["cavity_pans"])):
        s_sec = 0.22; tt = T(s_sec)
        s = mx.band(rs.normal(0, 1, len(tt)), 500, 2600) * np.sin(np.pi * tt / s_sec) ** 2
        s += 0.5 * np.sin(2 * np.pi * np.cumsum(300 + 900 * tt / s_sec) / R) * np.exp(-tt * 16)
        b.add(s, ti, 0.30 + 0.06 * i, pan)  # nearer cavities slightly louder
    tt = T(0.5)
    f = 58 * (1 + 1.5 * np.exp(-tt * 30))
    glug = np.sin(2 * np.pi * np.cumsum(f) / R) * np.exp(-tt * 12)
    b.add(glug, d["sprue_glug"], 0.9)
    tt = T(0.22)
    b.add(np.sin(2 * np.pi * np.cumsum(220 + 1200 * tt / 0.22) / R) * np.exp(-tt * 14), d["sprue_glug"] + 0.03, 0.25)
    return b.st()


# ------------------------------------------------------------------- rain ---
def grain(bright):
    return modal(rs.uniform(0.6, 1.0) * bright, [1.0, 2.4, 4.1], [1.0, 0.5, 0.2], [0.008, 0.004, 0.002], 0.04, strike=0.0002)


def rain(c):
    b = Bus()
    r = c["rain"]
    t = r["start"]
    # sidechain: dip the rain 0.12 s under each L4 pulse so the meter stays countable
    l4 = [onset("L4", k) for k in range(1, 13)]
    n = 0
    while t < r["stop"]:
        if t < r["sh4_from"]:                       # sound-only transition over the still mould: sparse -> 160/s
            dens = 18 + 140 * (t - r["start"]) / (r["sh4_from"] - r["start"]); bright = 6000; g = 0.10
        elif t < r["peak"]:                          # thickening through Sh4
            x = (t - r["sh4_from"]) / (r["peak"] - r["sh4_from"])
            dens = 160 + 340 * x ** 1.5; bright = 6000 - 1500 * x; g = 0.06
        elif t < r["heap_cut"]:                      # after the chord, thinning
            x = (t - r["peak"]) / (r["heap_cut"] - r["peak"])
            dens = 500 * (1 - x) + 60 * x; bright = 4500; g = 0.07
        else:                                        # the last grains land on the heap, lower and duller, stopping
            x = (t - r["heap_cut"]) / (r["stop"] - r["heap_cut"])
            dens = 40 * (1 - x) ** 2 + 1.5; bright = 2600; g = 0.12 * (1 - 0.6 * x)
        duck = 0.35 if any(0 <= t - o < 0.12 for o in l4) else 1.0
        b.add(grain(bright), t, g * duck * rs.uniform(0.4, 1.0), rs.uniform(-0.8, 0.8))
        t += rs.exponential(1 / dens); n += 1
    return b.st(), n


# ------------------------------------------------------------------ chord ---
def chord(c):
    b = Bus()
    base = 110.0
    ratios = [1, 3 / 2, 2, 5 / 2, 3, 4]  # locked rational ratios: the Whitney alignment heard
    for i, q in enumerate(ratios):
        s = modal(base * q, [1.0, 2.0, 3.01], [1.0, 0.3, 0.12], [0.45, 0.25, 0.12], 2.0, strike=0.003)
        b.add(s, c["chord"] + 0.004 * i, 0.22 / (1 + 0.3 * i), -0.5 + 0.2 * i)
    b.add(ring_hit(1180) * 0.6, c["chord"], 0.4, 0.0)  # struck plastic transient on top
    return b.st()


# ------------------------------------------------------------------- room ---
def room(c):
    b = Bus()
    for pan in (-0.3, 0.3):
        x = rs.normal(0, 1, int(DUR * R)).cumsum()
        x -= np.convolve(x, np.ones(600) / 600, "same")
        x /= np.abs(x).max() + 1e-9
        b.add(x, 0, 0.05, pan)
    hum = 0.10 * np.sin(2 * np.pi * 50 * T(DUR)) + 0.03 * np.sin(2 * np.pi * 100 * T(DUR))
    b.add(hum, 0, 0.12)
    st = b.st()
    tt = np.arange(len(st)) / R
    env = np.clip(tt / 0.8, 0, 1) * np.clip((37.8 - tt) / 1.2, 0, 1)
    return st * env[:, None]


# ---------------------------------------------------------- foraged press ---
def press_foraged(c):
    src = OUT / "gigaset_full.wav"
    if not src.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "dl" / "gigaset_engel.webm"), "-vn", "-ac", "2",
                        "-ar", str(R), "-c:a", "pcm_s16le", str(src)], check=True)
    with wave.open(str(src)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768.0
    p = c["press_foraged"]
    s0, s1 = p["source_seconds"]
    seg = x[int(s0 * R):int(s1 * R)]
    seg = np.stack([mx.band(seg[:, 0], 30, 2500), mx.band(seg[:, 1], 30, 2500)], 1)  # EQ only: tucked under the melt
    st = np.zeros((int(DUR * R), 2))
    i0 = int(p["in_"][0] * R)
    n = min(len(seg), len(st) - i0, int((p["out"][1] - p["in_"][0]) * R))
    st[i0:i0 + n] = seg[:n] * 0.11  # about -18 dB: a faint press bed, not a foreground
    tt = np.arange(len(st)) / R
    env = np.clip((tt - p["in_"][0]) / (p["in_"][1] - p["in_"][0]), 0, 1) * np.clip((p["out"][1] - tt) / (p["out"][1] - p["out"][0]), 0, 1)
    # also hand the editor the raw trimmed source (no EQ) for reference
    raw = x[int(s0 * R):int(s1 * R)]
    with wave.open(str(OUT / "gigaset_trim_2.0-12.8s_raw.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(R)
        w.writeframes((np.clip(raw, -1, 1) * 32767).astype(np.int16).tobytes())
    return st * env[:, None] / SCALE  # keep the recording's own level after the fixed SCALE


def measure_onsets(st, cues):
    """Detect each meter pulse onset (first sample above 20% of local peak) and compare to the cue sheet."""
    m = np.abs(st).max(1)
    errs = []
    for line, ons in cues["verse"].items():
        for k, o in enumerate(ons, 1):
            a, b = int((o - 0.05) * R), int((o + 0.12) * R)
            w = m[a:b]
            thr = 0.2 * w.max()
            idx = int(np.argmax(w > thr))
            errs.append(round((a + idx) / R - o, 4))
    return errs


def main():
    STEMS.mkdir(parents=True, exist_ok=True)
    cf = STEMS / "cues.json"
    if "--recue" in sys.argv or not cf.exists():
        cf.write_text(json.dumps(build_cues(), indent=1))
    c = json.loads(cf.read_text())
    stems = {}
    stems["meter"] = meter()
    stems["ring_events"] = ring_events(c)
    stems["drain"] = drain(c)
    stems["rain"], ngr = rain(c)
    stems["chord"] = chord(c)
    stems["room"] = room(c)
    stems["press_foraged"] = press_foraged(c)
    rep = {}
    for k, st in stems.items():
        p, pk = write(f"{k}.wav", st)
        rep[k] = dict(path=str(p), peak=round(pk, 3))
    g = c["suggested_gains"]
    mix = sum(stems[k] * g[k] for k in stems)
    mix *= min(1.0, 0.95 / (np.abs(mix * SCALE).max() + 1e-9))
    p, pk = write("mix_preview.wav", mix)
    rep["mix_preview"] = dict(path=str(p), peak=round(pk, 3))
    errs = measure_onsets(stems["meter"], c)
    rep["meter_onset_error_s"] = dict(max_abs=max(abs(e) for e in errs), n=len(errs), frame=1 / 24)
    rep["rain_grains"] = ngr
    # gap check: energy in each caesura gap vs pulses (meter stem)
    m = np.abs(stems["meter"]).max(1)
    gaps = {}
    for line in LINES:
        e6 = onset(line, 6) + 0.30 if line != "L3" else onset(line, 6) + 0.30
        a, b = int((onset(line, 7) - 0.12) * R), int((onset(line, 7) - 0.01) * R)
        gaps[line] = round(float(20 * np.log10((m[a:b].max() + 1e-9) / (m.max() + 1e-9))), 1)
    rep["meter_level_just_before_hemistich2_dB_re_peak"] = gaps
    (STEMS / "stems_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
