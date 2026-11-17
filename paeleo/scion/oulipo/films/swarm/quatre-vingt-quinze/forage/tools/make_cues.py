"""quatre-vingt-quinze · U3 forager-sound: one sound cue per cell (cue_A.wav .. cue_I.wav) and room.wav.

Every cue is a function of the cell id only (no route argument), so it is identical on both routes.
t = 0 in each cue file is the cell's exposure-sheet frame 0 (the instant the editor starts the cell's
sheet, puppets.layer(cell, 0)); event times are U2's puppets.EVENTS (exposure-local seconds), read
from puppets.py when it imports, else from the copy below. Each cue runs 3 s plus its own natural tail
(no truncation of a tail before it has decayed under -60 dBFS, except B's, which is capped so that it is
silent long before across E at 15 s: B ends at most 6.0 s after its start).

All foraged recordings are decoded with ffmpeg only (to forage/wav/*.wav). Every cue shares one
handmade hall impulse response (decaying band-limited noise, RT60 ~2.4 s) so the cells sound as one
stone waiting room. Levels are FIXED (no per-cue normalisation) so the editor can sum cues and room.

Usage: python3 make_cues.py <sources/quatre-vingt-quinze dir>
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1]).resolve()
WAV = ROOT / "forage" / "wav"
OUT = ROOT / "forager-sound"
FILMS = Path(__file__).resolve().parents[4]          # .../oulipo/films
sys.path.insert(0, str(FILMS))
from kit import Mix  # noqa: E402  (kit.py unedited; used for its synthesis primitives)

RATE = 44100
EVENTS_COPY = {
    "A": {"steps_s": [0.0, 0.25, 0.5, 0.75], "stop_s": 1.0},
    "B": {"pulls_s": [1.15, 2.35], "strikes_s": [1.4, 2.6]},
    "C": {"knocks_s": [0.667, 1.0, 1.333]},
    "D": {"tear_s": [1 / 3, 0.5], "key_out_s": 0.75, "surprise_s": 7 / 6},
    "E": {"lift_start_s": 1 / 12, "head_up_s": None, "key_top_click_s": 0.75, "glint_s": 0.75},
    "F": {"key_on_wood_s": 1 / 3, "steps_s": [0.75, 1.0]},
    "G": {"downstrokes_s": [0.167, 0.5, 0.833, 1.167]},
    "H": {"light_out_s": 10 / 12},
    "I": {"thread_taut_s": 0.5, "scrape_s": [2 / 3, 5 / 3]},
}
EVENTS, EVENTS_FROM = EVENTS_COPY, "copy in make_cues.py (puppets.py not importable)"
try:
    sys.path.insert(0, str(FILMS / "swarm" / "quatre-vingt-quinze" / "puppets"))
    import puppets  # our own unit's code (U2), not downloaded material
    EVENTS, EVENTS_FROM = puppets.EVENTS, "puppets.EVENTS (imported)"
except Exception as e:  # pragma: no cover
    EVENTS_FROM += f" [{type(e).__name__}]"


def rd(name):
    w = wave.open(str(WAV / name))
    assert w.getframerate() == RATE and w.getnchannels() == 1
    return np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0


def seg(x, a, b, fade=0.006):
    s = x[int(a * RATE):int(b * RATE)].copy()
    f = max(1, int(fade * RATE))
    s[:f] *= np.linspace(0, 1, f)
    s[-f:] *= np.linspace(1, 0, f)
    return s


def write(path, st):
    st = np.clip(st, -1, 1)
    w = wave.open(str(path), "wb")
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes((st * 32767).astype("<i2").tobytes())
    w.close()


# ---- the hall: one handmade impulse response shared by every cue
_rs = np.random.RandomState(95)
_m = Mix(1, seed=95)
_n = int(2.6 * RATE)
_t = np.arange(_n) / RATE
IR = _rs.normal(0, 1, _n) * np.exp(-_t * 6.91 / 2.4)           # RT60 2.4 s
IR = _m.band(IR, 140, 3600)
IR[: int(0.018 * RATE)] = 0                                    # 18 ms pre-delay: a big room
IR /= np.sqrt((IR ** 2).sum())


def hall(x, wet):
    y = np.fft.irfft(np.fft.rfft(x, len(x) + _n) * np.fft.rfft(IR, len(x) + _n), len(x) + _n)
    return np.concatenate([x, np.zeros(_n)]) + wet * y


SRC = {}
def src():
    if not SRC:
        SRC["bell"] = rd("Glockenschlagwerk_Bahnhof_Fridingen.wav")
        SRC["steps"] = rd("Concrete_Steps_2.wav")
        SRC["keys"] = rd("Keys_hitting_tree_2_(Gravity_Sound).wav")
        SRC["hinge"] = rd("Squeaky_door_hinge.wav")
        SRC["handle"] = rd("Door_handle_creaking.wav")
        for k, n in (("knock", "Knock_on_door.wav"), ("knock2", "Knocking_on_wood_or_door.wav")):
            if (WAV / n).exists():
                SRC[k] = rd(n)
    return SRC


# grains, chosen by listening/inspection of the envelopes (forage/ledger.json records each)
STEP_GRAINS = [(0.085, 0.30), (0.635, 0.786)]          # the two heel-toe steps of Concrete_Steps_2
KEY_CLINK = (0.31, 0.62)                                 # first clink of Keys hitting tree 2
KEY_SOFT = (0.73, 1.05)                                  # second, softer clink
BELL_1 = (11.815, 12.965)                                # strike 13 of the Fridingen station bell
BELL_2 = (12.965, 15.88)                                 # strike 14 (r0; it is damped within 0.3 s: unused in r1)
BELL_12 = (10.465, 11.70)                                # r1: strike 12, its ring up to strike 13
BELL_13 = (11.715, 12.33)                                # r1: strike 13, attack and first 0.6 s of its natural ring
BELL_RING = (12.03, 12.33)                               # r1: ring-only part of strike 13 (sustain source)
BELL_EXT_S, BELL_EXT_DB_PER_S = 3.2, 7.0                 # r1: ring-out extension length and decay rate


def bell_extend(x, ring, seconds, db_per_s, seed=95):
    """r1: continue a real strike's ring past the point where the recording's next strike cut it.
    Overlap-add of 90 ms Hann grains drawn at random from the recording's own ring-only segment
    (no synthesis; same partials), under an exponential envelope that continues the decay; the
    first 60 ms crossfade from the real ring into the extension."""
    rng = np.random.RandomState(seed)
    src_ = seg(x, *ring, fade=0.0)
    g = int(0.09 * RATE); hop = g // 3; win = np.hanning(g)
    n = int(seconds * RATE)
    out = np.zeros(n + g)
    for i in range(0, n, hop):
        o = rng.randint(0, len(src_) - g)
        out[i:i + g] += src_[o:o + g] * win
    out = out[:n] / 1.5                                   # Hann at 1/3 overlap sums to 1.5
    lvl = np.sqrt(np.mean(src_[-int(0.08 * RATE):] ** 2)) / (np.sqrt(np.mean(out[:int(0.3 * RATE)] ** 2)) + 1e-12)
    out *= 1.15 * lvl * 10 ** (-db_per_s * np.arange(n) / RATE / 20)
    return out
HINGE = [(2.30, 2.58), (3.05, 3.30), (3.90, 4.16), (4.70, 4.98)]   # four squeak slices (rope creak)
HANDLE = (0.08, 0.75)                                    # door-handle creak (rope taking load)


def place(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * RATE)
    if i >= len(buf):
        return
    s = sig[: len(buf) - i] * gain
    lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(s), 0] += s * lg * 1.414
    buf[i:i + len(s), 1] += s * rg * 1.414


def mono_to_hall_stereo(dry_events, seconds, wet, cap=None):
    """dry_events: list of (signal, at, gain, pan). Dry is panned; the hall is mono-wide."""
    n = int(seconds * RATE)
    dry = np.zeros((n, 2))
    mono = np.zeros(n)
    for s, at, g, p in dry_events:
        place(dry, s, at, g, p)
        i = int(at * RATE)
        mono[i:i + len(s)] += (s * g)[: max(0, n - i)]
    wetsig = hall(mono, 1.0)[: n + _n] - np.concatenate([mono, np.zeros(_n)])
    out = np.zeros((n + _n, 2))
    out[:n] += dry
    out[:, 0] += wet * wetsig * 0.95
    out[:, 1] += wet * np.roll(wetsig, int(0.011 * RATE)) * 1.0
    # trim the tail where it has decayed below -60 dBFS (natural end), or at `cap`
    env = np.abs(out).max(1)
    above = np.where(env > 10 ** (-60 / 20))[0]
    end = min(len(out), (above[-1] + int(0.05 * RATE)) if len(above) else n)
    end = max(end, int(3.0 * RATE))
    if cap:
        end = min(end, int(cap * RATE))
    out = out[:end]
    f = int(0.08 * RATE)
    out[-f:] *= np.linspace(1, 0, f)[:, None]
    return out


def handmade_tear(m, seconds=0.16, seed=0):
    """Paper tear: a dense run of tiny fibre clicks (handmade with kit noise; no recording)."""
    rs = np.random.RandomState(seed)
    n = int(seconds * RATE)
    x = np.zeros(n)
    k = 0
    while k < n - 200:
        L = rs.randint(30, 160)
        c = rs.normal(0, 1, L) * np.exp(-np.linspace(0, 5, L))
        x[k:k + L] += c * rs.uniform(0.3, 1.0)
        k += rs.randint(20, 140)
    x = m.band(x, 900, 7500)
    x *= np.sin(np.linspace(0, np.pi, n)) ** 0.6
    return x / (np.abs(x).max() + 1e-9)


def handmade_scrape(m, seconds, seed=0):
    """Key dragged over stone sill: band noise with stick-slip amplitude roughness (handmade)."""
    rs = np.random.RandomState(seed)
    n = int(seconds * RATE)
    x = m.band(rs.normal(0, 1, n), 1200, 6500)
    grit = np.repeat(rs.uniform(0.2, 1.0, n // 220 + 1), 220)[:n]
    grit = np.convolve(grit, np.ones(60) / 60, "same")
    x *= grit * np.sin(np.linspace(0, np.pi, n)) ** 0.4
    return x / (np.abs(x).max() + 1e-9)


def handmade_knock(m, seed=0):
    """Knuckle on a wooden door (fallback only if no foraged knock): a short wooden thud plus click."""
    t = np.arange(int(0.14 * RATE)) / RATE
    rs = np.random.RandomState(seed)
    body = np.sin(2 * np.pi * (190 + 60 * np.exp(-t * 60)) * t) * np.exp(-t * 38)
    clk = m.band(rs.normal(0, 1, len(t)) * np.exp(-t * 300), 600, 4500)
    x = body + 0.5 * clk
    return x / np.abs(x).max()


def cue(c):
    S = src()
    E = EVENTS[c]
    m = Mix(1, seed=ord(c))
    ev = []
    info = {}
    wet, cap = 0.16, None
    if c == "A":
        for k, at in enumerate(E["steps_s"]):
            a, b = STEP_GRAINS[k % 2]
            ev.append((seg(S["steps"], a, b), at, 0.95 * (0.9 if k % 2 else 1.0), -0.35 + 0.15 * k))
        info["sources"] = ["Concrete_Steps_2 (two grains alternated)"]
    elif c == "B":
        b1 = seg(S["bell"], *BELL_12, fade=0.004)
        b2r = seg(S["bell"], *BELL_13, fade=0.004)
        ext = bell_extend(S["bell"], BELL_RING, BELL_EXT_S, BELL_EXT_DB_PER_S)
        xf = int(0.06 * RATE)                         # crossfade the real ring into its continuation
        b2 = np.concatenate([b2r, np.zeros(len(ext) - xf)])
        b2[len(b2r) - xf:len(b2r)] *= np.linspace(1, 0, xf)
        ext[:xf] *= np.linspace(0, 1, xf)
        b2[len(b2r) - xf:] += ext
        b2[-int(0.4 * RATE):] *= np.linspace(1, 0, int(0.4 * RATE))
        off = 0.035                                   # onset offset inside the grain
        s1, s2 = E["strikes_s"]
        ev += [(b1, s1 - off, 0.42, -0.05), (b2, s2 - off, 0.42, 0.0)]
        for p in E["pulls_s"]:                        # the cord jerks: a small creak of the bracket
            ev.append((seg(S["handle"], 0.10, 0.28), p, 0.10, -0.4))
        wet, cap = 0.55, 6.0
        info["sources"] = ["Fridingen station bell strikes 12 and 13 (r1); strike 13's ring continued by overlap-add of its own ring grains", "Door handle creaking (cord jerk, low)"]
    elif c == "C":
        if "knock" in S or "knock2" in S:
            info["sources"] = ["Knocking on wood or door (stephan, PD): one three-knock group, one grain per knock"]
            k = S.get("knock2", S.get("knock"))
            ons = KNOCK_GRAINS
            for i, at in enumerate(E["knocks_s"]):
                a, b = ons[i % len(ons)]
                g = seg(k, a, b)
                g /= np.abs(g).max() + 1e-9                # each knuckle at the same strength
                ev.append((g, at, KNOCK_GAIN * (1.0, 0.92, 1.05)[i % 3], 0.3))
        else:
            info["sources"] = ["handmade knock (kit noise/tones)"]
            for i, at in enumerate(E["knocks_s"]):
                ev.append((handmade_knock(m, i), at, 0.5, 0.3))
        wet = 0.2
    elif c == "D":
        for i, at in enumerate(E["tear_s"]):
            ev.append((handmade_tear(m, 0.15 if i == 0 else 0.22, seed=i + 3), at, 0.30, -0.2))
        ev.append((seg(S["keys"], *KEY_SOFT), E["key_out_s"], 0.22, -0.15))
        info["sources"] = ["handmade paper tear", "Keys hitting tree 2 (soft clink, key out)"]
    elif c == "E":
        ev.append((seg(S["keys"], *KEY_SOFT), E["key_top_click_s"], 0.12, 0.05))    # r1: ducked, soft grain
        info["sources"] = ["Keys hitting tree 2 (soft clink at the top of the lift; r1 ducked so B's ring stays audible)"]
    elif c == "F":
        ev.append((seg(S["keys"], *KEY_SOFT), E["key_on_wood_s"], 0.45, 0.25))
        t_thud = np.arange(int(0.12 * RATE)) / RATE
        ev.append((np.sin(2 * np.pi * 230 * t_thud) * np.exp(-t_thud * 45), E["key_on_wood_s"], 0.16, 0.25))
        st = list(E["steps_s"])
        while st[-1] + 0.27 < 2.9:                    # she walks out of the left side: steps recede
            st.append(st[-1] + 0.27)
        for k, at in enumerate(st):
            a, b = STEP_GRAINS[k % 2]
            ev.append((seg(S["steps"], a, b), at, 0.80 * (0.80 ** k), -0.2 - 0.12 * k))
        info["sources"] = ["Keys hitting tree 2 (key set down) + handmade wood knock body", "Concrete_Steps_2 (receding)"]
    elif c == "G":
        for i, at in enumerate(E["downstrokes_s"]):
            a, b = HINGE[i % len(HINGE)]
            ev.append((seg(S["hinge"], a, b, 0.03), at + 0.02, 0.55, 0.2))
            ev.append((seg(S["handle"], *HANDLE, 0.03)[: int(0.25 * RATE)], at, 0.10, 0.1))
            # palm slap on the rope: handmade
            ev.append((m.band(np.random.RandomState(i).normal(0, 1, 900) * np.exp(-np.linspace(0, 9, 900)), 300, 3000),
                       at - 0.01, 0.18, 0.15))
        info["sources"] = ["Squeaky door hinge (rope creak slices)", "Door handle creaking (load)", "handmade palm slaps"]
    elif c == "H":
        info["sources"] = ["none: room tone only (the cell is silent by design); this cue is digital silence"]
    elif c == "I":
        ev.append((seg(S["keys"], *KEY_SOFT), E["scrape_s"][0] - 0.05, 0.16, 0.2))
        for i, at in enumerate(E["scrape_s"]):
            ev.append((handmade_scrape(m, 0.55 if i == 0 else 0.45, seed=i + 7), at, 0.13 * (1.0 if i == 0 else 0.7), 0.25))
        info["sources"] = ["Keys hitting tree 2 (key on sill)", "handmade scrape (key under the door)"]
    out = mono_to_hall_stereo(ev, 5.6 if c == "B" else 3.0, wet, cap) if ev else np.zeros((int(3.0 * RATE), 2))
    info.update(events=E, seconds=round(len(out) / RATE, 3), peak_dbfs=round(20 * np.log10(np.abs(out).max() + 1e-12), 1),
                wet=wet, cap_s=cap)
    return out, info


KNOCK_GRAINS = [(0.0, 0.2)]
KNOCK_GAIN = 0.5


def room(seconds=66.0):
    """Handmade room bed (kit Mix.room: pink air + faint 50 Hz mains) through the same hall."""
    mx = Mix(seconds, seed=1095)
    mx.room(0.0, seconds, gain=0.018, hum=50)
    st = np.stack([mx.L, mx.R], 1)
    f = int(1.5 * RATE)
    st[:f] *= np.linspace(0, 1, f)[:, None]
    st[-f:] *= np.linspace(1, 0, f)[:, None]
    return st


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((OUT / "knock_grains.json").read_text()) if (OUT / "knock_grains.json").exists() else None
    if cfg:
        KNOCK_GRAINS[:] = [tuple(g) for g in cfg["grains"]]
        KNOCK_GAIN = cfg.get("gain", KNOCK_GAIN)
    rec = {"events_from": EVENTS_FROM, "rate": RATE, "t0": "exposure-sheet frame 0 of the cell", "cues": {}}
    for c in "ABCDEFGHI":
        st, info = cue(c)
        write(OUT / f"cue_{c}.wav", st)
        rec["cues"][c] = info
        print(c, info["seconds"], info["peak_dbfs"], info["sources"])
    r = room()
    write(OUT / "room.wav", r)
    rec["room"] = {"seconds": round(len(r) / RATE, 2), "rms_dbfs": round(20 * np.log10(np.sqrt((r ** 2).mean())), 1),
                   "source": "handmade (kit Mix.room); no clean station room tone found in the MIA cache"}
    rec["hall_ir"] = "handmade: Gaussian noise x exp decay (RT60 2.4 s), band 140-3600 Hz, 18 ms pre-delay, seed 95"
    (OUT / "cues.json").write_text(json.dumps(rec, indent=1, default=float))
