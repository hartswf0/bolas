"""Edition A (domestic / welcoming community) stems for La Cite Raymond Queneau, plan-r3 section 6b, column A.

Run:  python3 -I build_A.py
Writes into films/sources/la-cite-raymond-queneau/sound-A/stems/{voice,music,fx,amb}.wav (44.1 kHz, stereo,
16-bit, exactly 1,323,000 samples), sound-A/preview-A.wav, sound-A/cues-A.json, sound-A/mix-A.json.
Foraged recordings are decoded with ffmpeg only (to float PCM) and never executed.  Where a foraged file is absent
the cue is synthesized with kit.Mix primitives and marked HANDMADE in the cue map.
"""
import json, math, os, subprocess, sys
import numpy as np

FILMS = "/home/user/bolas/paeleo/scion/oulipo/films"
sys.path.insert(0, FILMS)
import kit                      # noqa: E402  (Mix)
from kit_cinema_b import lufs   # noqa: E402

RATE, FPS = 44100, 24
N = 1323000
SRC = FILMS + "/sources/la-cite-raymond-queneau/sound-A"
RAW, TS = SRC + "/raw", FILMS + "/sources/la-cite-raymond-queneau/test-shot/audio"
PREP = FILMS + "/sources/la-cite-raymond-queneau/sound-a-domestic-welcoming-community-team-voice-captions-music-fx-ambience-"
OUT = FILMS + "/swarm/la-cite-raymond-queneau/sound-A"
EDL = FILMS + "/swarm/la-cite-raymond-queneau/picture/edl.json"
os.makedirs(SRC + "/stems", exist_ok=True); os.makedirs(PREP, exist_ok=True)
M = kit.Mix(30.0, RATE, seed=1998)        # used for its synthesis primitives (noise, band, env, tone)
rs = np.random.RandomState(47)

# ------------------------------------------------------------------ ledger ids -> local files
FILES = {
    "latch_open":   (RAW + "/342706_spacejoe_lock-3-open-lock-3.wav", TS + "/latch_open.wav"),
    "latch_close":  (RAW + "/342701_spacejoe_lock-3-close-lock-1.wav",),
    "door_close":   (RAW + "/Closing_an_old_door.ogg",),
    "handle_creak": (RAW + "/Door_handle_creaking.ogg",),
    "squeaky_door": (RAW + "/Squeaky_door.ogg",),
    "cupboard":     (RAW + "/Cupboarddoorclose.ogg",),
    "faucet":       (RAW + "/Faucet_water_into_sink.ogg",),
    "sink":         (RAW + "/Tapsinkwaternoise.ogg",),
    "footstep":     (RAW + "/Footstep_on_Gravel_Gravity_Sound_.mp3",),
    "kids":         (RAW + "/Douzen_kids_on_playground.ogg",),
    "street":       (RAW + "/Karlova_0001.ogg",),
    "car_pass":     (RAW + "/Kolem_proj_d_auto_-_st_Karlova_ulice_001.ogg",),
    "kettle":       (RAW + "/WWS_Whistlingkettle.ogg", TS + "/kettle_wws.ogg"),
    "musicbox":     (RAW + "/Music_box_notes_1.ogg",),
    "radio_song":   (RAW + "/Victor-73522a-b26758.ogg.mp3",),
    "bonsoir":      (RAW + "/LL-Q150_fra_-LoquaxFR-bonsoir.wav", RAW + "/LL-Q150_fra_-Helenou66-bonsoir.wav"),
    "toi":          (RAW + "/LL-Q150_fra_-LoquaxFR-toi.wav",),
    "bonne_nuit":   (RAW + "/LL-Q150_fra_-Rodrigo5260-bonne_nuit.wav", RAW + "/LL-Q150_fra_-LoquaxFR-bonne_nuit.wav"),
}
USED = {}

def load(key):
    for p in FILES[key]:
        if os.path.exists(p) and os.path.getsize(p) > 2000:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            x = np.frombuffer(raw, np.float32).astype(np.float64)
            x = x - x.mean()
            USED[key] = p
            prep = os.path.join(PREP, key + ".wav")
            if not os.path.exists(prep):
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", prep], check=True)
            return x / (np.abs(x).max() + 1e-9)
    return None

def onset(x, thr=0.2):
    i = int(np.argmax(np.abs(x) > thr)); return max(0, i - int(0.003 * RATE))

def seg(x, t0, dur, fade=0.01):
    a = int(t0 * RATE); y = x[a:a + int(dur * RATE)].copy(); f = min(int(fade * RATE), len(y) // 2)
    if f > 0:
        y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

def lp(x, hz): return M.lowpass(x, hz) if len(x) else x
def bp(x, lo, hi): return M.band(x, lo, hi) if len(x) else x
def pitch(x, r): return np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)

def loudest(x, dur):
    w = int(dur * RATE); cs = np.concatenate([[0.0], np.cumsum(x ** 2)])
    c = cs[w:] - cs[:-w]; i = int(np.argmax(c)); return x[i:i + w]

class Stem:
    def __init__(self, name):
        self.name, self.L, self.R = name, np.zeros(N), np.zeros(N)
    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * RATE))
        if i < 0: sig, i = sig[-i:], 0
        sig = np.asarray(sig[: max(0, N - i)]) * gain
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        self.L[i:i + len(sig)] += sig * lg * 1.414; self.R[i:i + len(sig)] += sig * rg * 1.414
    def add_moving(self, sig, t, gain, pan0, pan1):
        i = int(round(t * RATE)); sig = np.asarray(sig[: max(0, N - i)]) * gain
        p = np.linspace(pan0, pan1, len(sig)); lg, rg = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
        self.L[i:i + len(sig)] += sig * lg * 1.414; self.R[i:i + len(sig)] += sig * rg * 1.414
    def gate(self, t0, t1, fade=0.15):
        """digital silence in [t0, t1) with fades outside the window, so the window itself is zero."""
        g = np.ones(N); i0, i1, f = int(t0 * RATE), int(t1 * RATE), int(fade * RATE)
        g[i0:i1] = 0; g[i0 - f:i0] = np.linspace(1, 0, f) ** 2; g[i1:i1 + f] = np.linspace(0, 1, f) ** 2
        self.L *= g; self.R *= g
    def st(self): return np.stack([self.L, self.R], 1)

def limit(st, ceil=0.70, rel=0.12):
    """peak limiter: ~5 ms look-ahead (block running-min), instant attack, exponential release.
    Returns the limited stem and its max gain reduction (dB)."""
    a = np.abs(st).max(1); B = 220
    need = np.minimum(1.0, ceil / np.maximum(a, 1e-9))
    nb = -(-len(need) // B); blk = np.pad(need, (0, nb * B - len(need)), constant_values=1).reshape(nb, B).min(1)
    blk = np.minimum(blk, np.minimum(np.r_[blk[1:], 1.0], np.r_[1.0, blk[:-1]]))
    need = np.repeat(blk, B)[: len(need)]
    g = np.empty_like(need); cur = 1.0; k = math.exp(-1.0 / (rel * RATE))
    for i in range(len(need)):
        cur = need[i] if need[i] < cur else 1.0 - (1.0 - cur) * k
        g[i] = cur
    return st * g[:, None], round(float(20 * np.log10(g.min())), 2)

voice, music, fx, amb = Stem("voice"), Stem("music"), Stem("fx"), Stem("amb")
CUES, HANDMADE = [], []

def T(frame): return frame / FPS
def win_pan(w):                  # bay 0 = far left (the block recedes left), bay 23 near right
    return -0.8 + 1.5 * ((w % 24) / 23.0) ** 0.85
def win_depth(w):                # far-left bays and upper floors further away: more air absorption
    bay, floor = w % 24, w // 24
    return 1800 + 4200 * (bay / 23.0) - 250 * (3 - floor), 0.55 + 0.45 * (bay / 23.0)

def claim(stem, ev, key, sig, frame, off_ms, gain, pan, pid, text, handmade=False, depth=None):
    t = T(frame) + off_ms / 1000.0
    stem.add(sig, t, gain, pan)
    CUES.append(dict(sound_event=ev, source_ledger_id=("HANDMADE:" + key) if handmade else key, stem=stem.name,
                     t_sound=round(t, 4), picture_event_id=pid, frame=frame, offset_ms=off_ms,
                     reading="domestic", claim=text, pan=round(pan, 2), depth=depth or "near/dry"))

# ------------------------------------------------------------------ handmade sounds (kit.Mix primitives)
def spoon_cup(f0):
    t = M.t(0.8)
    x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 10), (2.32, .6, 15), (4.25, .35, 24), (6.8, .2, 32)))
    x2 = np.zeros_like(x); k = int(0.11 * RATE); x2[k:] = x[:-k] * 0.55       # a second, lighter tap
    return (x + x2) / np.abs(x + x2).max()
def bag_rustle(seconds=0.22):
    n = M.noise(seconds) * M.env(int(seconds * RATE), 0.01, seconds * 0.7, 0, 0.03)
    x = bp(n, 1800, 7000) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 9, len(n)))))
    return x / (np.abs(x).max() + 1e-9)
def room_tone(seconds, lo=40, hi=420):
    x = bp(M.noise(seconds, "brown"), lo, hi); return x / (np.abs(x).max() + 1e-9)
def synth_step():
    n = M.noise(0.09) * M.env(int(0.09 * RATE), 0.002, 0.06, 0, 0.02); return lp(n, 1800) / 0.5

# ------------------------------------------------------------------ load foraged
S = {k: load(k) for k in FILES}

def get_contacts():
    if os.path.exists(EDL):
        e = json.load(open(EDL))
        ev = e.get("events", e) if isinstance(e, dict) else e
        c = [x for x in ev if isinstance(x, dict) and x.get("kind") == "walker_step"]
        if c: return [(int(x["frame"]), x.get("id", f"walker_step:{x['frame']}")) for x in c], "edl.json"
    fr = [int(round((8.33 + 0.55 * k) * FPS)) for k in range(int((15.0 - 8.33) / 0.55) + 1)]
    return [(f, f"walker_step:{f}") for f in fr], "assumed (0.55 s from 8.33 s; re-align to edl.json)"

# ================================================================== AMB
# S1-S2 exterior: Prague street ambience (far city, low-passed) + distant playground (far left) ; 17.5-26 room tone ;
# S4 exterior returns.
if S["street"] is not None:
    st = S["street"]; bed = np.tile(st, 3)[: int(16.4 * RATE)]
    amb.add(lp(bed, 1400), 0.0, 0.22, -0.25)
    amb.add(lp(np.roll(bed, RATE * 7), 1100), 0.0, 0.12, 0.35)
    amb.add(lp(np.tile(st, 2)[int(20 * RATE):int(24.4 * RATE)], 1600), 25.95, 0.18, 0.1)
else:
    wind = room_tone(16.4, 60, 900); amb.add(wind, 0, 0.16, 0); amb.add(room_tone(4.2, 60, 900), 25.95, 0.10, 0)
    HANDMADE.append("amb: exterior wind bed (brown noise band 60-900 Hz), street recording unavailable")
if S["kids"] is not None:
    k = S["kids"]; kb = np.tile(k, 2)[: int(16.2 * RATE)] * np.clip(np.linspace(0.3, 1.6, int(16.2 * RATE)), 0, 1)
    amb.add(lp(kb, 2600), 0.0, 0.085, -0.7)                    # far, left: across the estate
    amb.add(lp(k[int(3 * RATE):int(7.3 * RATE)], 2200), 25.9, 0.06, -0.55)
rt = room_tone(9.2, 35, 380)
amb.add(rt * np.clip(np.linspace(0, 6, len(rt)), 0, 1), 17.5, 0.11, -0.1)
amb.add(room_tone(9.2, 50, 300), 17.5, 0.07, 0.25)
HANDMADE.append("amb: interior room tone 17.5-26.7 s (two band-limited brown-noise layers, 35-380 Hz)")

# vehicle passes: far in S1 (left->right, low-passed), the 'bus' in S4 crossing with the track (left->right)
if S["car_pass"] is not None:
    cp = S["car_pass"]
    amb.add_moving(lp(cp, 900), 3.2, 0.22, -0.9, 0.4)
    CUES.append(dict(sound_event="far vehicle passing (S1)", source_ledger_id="car_pass", stem="amb", t_sound=3.2,
                     picture_event_id="shot:S1", frame=77, offset_ms=0, reading="domestic", claim="a lived-in street, not an empty set", pan="-0.9->0.4", depth="far/LP 900 Hz"))
    bus = pitch(cp, 0.82)                                       # slowed: a heavier vehicle
    amb.add_moving(lp(bus, 1500)[: int(4.0 * RATE)], 26.0, 0.24, -0.95, 0.9)
    CUES.append(dict(sound_event="bus passing left to right with the track", source_ledger_id="car_pass", stem="amb", t_sound=26.0,
                     picture_event_id="cut:S4", frame=624, offset_ms=0, reading="domestic", claim="the evening bus: the estate keeps its rhythms", pan="-0.95->0.9", depth="mid/LP 1500 Hz, pitched 0.82"))

# ================================================================== FX: window score (irregular domestic answers)
WINDOWS = [(0, 0, 146), (1, 13, 168), (2, 26, 190), (3, 39, 211), (4, 52, 233), (5, 65, 254), (6, 78, 276), (7, 91, 298),
           (8, 8, 319), (9, 21, 341), (10, 34, 362), (11, 47, 384), (12, 60, 406), (13, 73, 427), (14, 86, 449),
           (15, 3, 470), (16, 16, 492), (17, 29, 514), (18, 42, 535), (19, 55, 557), (20, 68, 578), (21, 81, 600)]

def lc():  x = S["latch_close"] if S["latch_close"] is not None else S["latch_open"]; return x[onset(x):][: int(0.6 * RATE)], ("latch_close" if S["latch_close"] is not None else "latch_open")
def lo():  x = S["latch_open"]; return x[onset(x):][: int(0.5 * RATE)], "latch_open"
def dc():  x = S["door_close"]; return x[onset(x, 0.15):][: int(1.1 * RATE)], "door_close"
def cup():
    if S["cupboard"] is not None: x = S["cupboard"]; return x[onset(x):][: int(0.4 * RATE)], "cupboard"
    return None, None
def tap(dur):
    x = S["faucet"] if S["faucet"] is not None else S["sink"]; key = "faucet" if S["faucet"] is not None else "sink"
    y = loudest(x, dur + 0.2)[: int(dur * RATE)].copy(); f = int(0.06 * RATE); y[:f] *= np.linspace(0, 1, f); y[-int(0.25 * RATE):] *= np.linspace(1, 0, int(0.25 * RATE))
    return y, key
def creak():
    x = S["handle_creak"]; return x[onset(x, 0.15):][: int(0.9 * RATE)], "handle_creak"

# plan per step: (kind, offset_ms, claim)
PLAN = {0: ("latch_close", 260, "a far window latched: someone shutting out the evening"),
        1: ("cupboard", 140, "a cupboard in another flat: someone putting the shopping away"),
        2: ("tap", 330, "a tap runs: a kitchen in use"),
        3: ("spoon", 190, "a spoon on a cup: tea being made somewhere"),
        4: ("creak", 380, "a door handle: someone stepping out onto a landing"),
        5: ("door_close", 220, "a distant door closing: a neighbour home"),
        6: ("bonsoir", 400, "a neighbour's 'bonsoir' across the street"),
        7: ("latch_open", 160, "a lock opened: a key in a door"),
        8: ("tap", 130, "a short tap: a hand rinsed"),
        9: ("spoon", 350, "a cup set down"),
        10: ("cupboard", 240, "a cupboard shut"),
        11: ("musicbox", 210, "a music box answers the cut: a child's room"),
        12: ("radio", 120, "a radio comes on through a wall, mid-tune: a family's evening"),
        13: ("creak", 310, "a door handle: someone stepping out onto a landing"),
        14: ("tap", 170, "water for the washing-up"),
        15: ("door_close", 260, "someone else coming home, far up the block"),
        16: ("latch_open", 150, "the flat door is opened for the walker who went in"),
        17: ("spoon", 380, "tea things set out next door"),
        18: ("latch_close", 120, "a soft latch: a neighbour turning in"),
        19: ("door_close", 300, "a distant door"),
        20: ("cupboard", 210, "plates put away"),
        21: ("creak", 270, "a door eased shut for the night")}

for step, w, fr in WINDOWS:
    kind, off, text = PLAN[step]
    cut_lp, far = win_depth(w)
    near = (w == 16)
    pan = win_pan(w); pid = f"window_on:{w}"
    g = 1.0 if near else far
    if kind == "latch_close":
        x, key = lc(); x = x if near else lp(pitch(x, 0.9) if step == 15 else x, cut_lp)
        claim(fx, "window latch", key, x, fr, off, 0.34 * g, pan, pid, text, depth=f"LP {int(cut_lp)} Hz")
    elif kind == "latch_open":
        x, key = lo()
        if near: claim(fx, "door latch (flat door opens)", key, x, fr, off, 0.42, pan, pid, text, depth="near/dry")
        else: claim(fx, "lock opened", key, lp(x, cut_lp), fr, off, 0.3 * g, pan, pid, text, depth=f"LP {int(cut_lp)} Hz")
    elif kind == "cupboard":
        x, key = cup()
        if x is None:
            x = lp(M.noise(0.12) * M.env(int(0.12 * RATE), 0.001, 0.08, 0, 0.02), 1200); key = "cupboard_synth"
            claim(fx, "cupboard shut (synth)", key, lp(x, cut_lp), fr, off, 0.3 * g, pan, pid, text, True, f"LP {int(cut_lp)} Hz")
        else:
            claim(fx, "cupboard door", key, lp(x, cut_lp), fr, off, 0.4 * g, pan, pid, text, depth=f"LP {int(cut_lp)} Hz")
    elif kind == "tap":
        x, key = tap(1.1 if step != 8 else 0.55)
        claim(fx, "tap running", key, lp(x, min(cut_lp, 3500)), fr, off, 0.2 * g, pan, pid, text, depth=f"LP {int(min(cut_lp, 3500))} Hz")
    elif kind == "spoon":
        f0 = {3: 2150, 9: 1870, 17: 2400}[step]
        claim(fx, "spoon on a cup", "spoon_cup", lp(spoon_cup(f0), min(cut_lp, 5000)), fr, off, 0.11 * g, pan, pid, text, True, f"LP {int(min(cut_lp, 5000))} Hz")
    elif kind == "creak":
        x, key = creak(); claim(fx, "door handle creak", key, lp(x, cut_lp), fr, off, 0.28 * g, pan, pid, text, depth=f"LP {int(cut_lp)} Hz")
    elif kind == "door_close":
        x, key = dc(); claim(fx, "distant door closing", key, lp(x, min(cut_lp, 1800)), fr, off, 0.3 * g, pan, pid, text, depth=f"LP {int(min(cut_lp, 1800))} Hz")
    elif kind == "bonsoir":
        x = S["bonsoir"]
        if x is not None:
            x = x[onset(x, 0.05):][: int(0.9 * RATE)]
            claim(voice, "'bonsoir' (real speech, Lingua Libre), across the street", "bonsoir", lp(x, 3800), fr, off, 0.26, -0.35, pid, text, depth="mid/LP 3.8 kHz")
        else:
            y = sum(M.tone(f, 0.45, "tri") * a for f, a in ((220, 1), (330, .4))) * M.env(int(.45 * RATE), .04, .3, .2, .1)
            claim(voice, "hummed two-note greeting (synth)", "greeting_synth", lp(y, 2000), fr, off, 0.08, -0.35, pid, text, True)
    elif kind == "musicbox" or kind == "musicbox_note":
        pass                                                        # placed with the music block below
    elif kind == "radio":
        pass                                                        # placed with the radio below

# ------------------------------------------------------------------ music: 16.0-17.5 crossover, music box only
mb = S["musicbox"]
if mb is not None:
    i0 = onset(mb, 0.15); phrase = mb[i0:i0 + int(1.29 * RATE)].copy()
    phrase[-int(0.35 * RATE):] *= np.linspace(1, 0, int(0.35 * RATE)) ** 1.5
    music.add(phrase, 16.0 + 0.21, 0.2, 0.15)
    mb_key, mb_hand = "musicbox", False
    # the second note: the recording's next onset after 0.6 s, measured, placed at f406 + 120 ms
else:
    # HANDMADE music box: plucked comb tines (kit.Mix.bell partials, short decay), a falling phrase
    phrase = np.zeros(int(1.29 * RATE))
    for k, (f, t0) in enumerate(((1318.5, 0.0), (1174.7, 0.24), (987.8, 0.707 - 0.21 + 0.12), (1046.5, 0.98))):
        t = M.t(0.6); n = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.3 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 18)
        a = int(t0 * RATE); phrase[a:a + len(n)] += n[: len(phrase) - a]
    phrase /= np.abs(phrase).max(); phrase[-int(0.3 * RATE):] *= np.linspace(1, 0, int(0.3 * RATE))
    music.add(phrase, 16.21, 0.17, 0.15); mb_key, mb_hand = "musicbox_synth", True
    HANDMADE.append("music: synthesized music-box phrase 16.21-17.5 s (sine tines with inharmonic 3.9x partial)")
CUES.append(dict(sound_event="music-box phrase (crossover: music only)", source_ledger_id=("HANDMADE:" if mb_hand else "") + mb_key, stem="music",
                 t_sound=16.21, picture_event_id="window_on:47", frame=384, offset_ms=210, reading="domestic", claim=PLAN[11][2], pan=0.15, depth="mid, dry"))

# ------------------------------------------------------------------ radio: comes on at f406 (+120 ms, inside the crossover: music stem only, no click), song again in S4
rad = S["radio_song"]
if rad is not None:
    body = loudest(rad, 12.0)
    def radio(x): return bp(x, 280, 3200) * 0.9 + 0.1 * np.tanh(3 * bp(x, 280, 3200))
    on = radio(body[: int(1.6 * RATE)]); f = int(0.05 * RATE); on[:f] *= np.linspace(0, 1, f); on[-int(0.9 * RATE):] *= np.linspace(1, 0, int(0.9 * RATE))
    click = lp(M.noise(0.015) * np.exp(-np.linspace(0, 8, int(0.015 * RATE))), 2500)
    t_on = 406 / 24 + 0.12
    music.add(lp(on, 2400), t_on, 0.16, win_pan(60))          # crossover: music stem only, so no switch click
    CUES.append(dict(sound_event="radio through a wall, an orchestral 78 mid-tune", source_ledger_id="radio_song", stem="music",
                     t_sound=round(t_on, 4), picture_event_id="window_on:60", frame=406, offset_ms=120, reading="domestic",
                     claim=PLAN[12][2], pan=round(win_pan(60), 2), depth="through a wall: BP 280-3200, LP 2.4 kHz"))
    s4 = radio(body[int(4 * RATE):int(8.4 * RATE)]); s4[: int(0.8 * RATE)] *= np.linspace(0, 1, int(0.8 * RATE)); s4[-int(0.2 * RATE):] *= np.linspace(1, 0, int(0.2 * RATE))
    music.add(lp(s4, 2000), 25.7, 0.17, 0.55)
    CUES.append(dict(sound_event="distant radio from an open window, the orchestral 78 (S4)", source_ledger_id="radio_song", stem="music",
                     t_sound=25.7, picture_event_id="cut:S4", frame=624, offset_ms=-300, reading="domestic",
                     claim="the cité at night still has music in it", pan=0.55, depth="far: BP 280-3200, LP 2 kHz"))

# ------------------------------------------------------------------ walker: footsteps, bag, door
contacts, csrc = get_contacts()
fs = S["footstep"]
for k, (fr, pid) in enumerate(contacts):
    t = fr / FPS
    if t > 14.45: break                                     # walker inside the door (f346): no more pavement contact
    prog = (t - 8.33) / (14.42 - 8.33); pan = -0.75 + 1.2 * prog
    if fs is not None:
        x = fs[onset(fs, 0.1):][: int(0.3 * RATE)]; x = pitch(x, [1.0, 0.93, 1.06, 0.97][k % 4]); x = lp(x, 3000 + 1500 * prog)   # gravel -> paved: softened
        claim(fx, "footstep (contact)", "footstep", x, fr, 0, (0.22 + 0.12 * prog) * [1, .85][k % 2], pan, pid,
              "an unhurried walk home, heel then toe", depth=f"approaching: LP {int(3000 + 1500 * prog)} Hz")
    else:
        claim(fx, "footstep (synth)", "footstep_synth", synth_step(), fr, 0, 0.25, pan, pid, "a walk home", True)
    fx.add(bag_rustle(0.18 + 0.05 * (k % 3)), t + 4 / FPS, 0.05 + 0.03 * prog, pan + 0.05)   # bag swing: 4-frame lag (#41)
HANDMADE.append("fx: shopping-bag rustle on every step, 4 frames after contact (band-passed noise 1.8-7 kHz, AM)")
if S["bonsoir"] is None: pass
# door: latch + creak at f334, shut on the edl door_close frame (editor re-alignment: was f370, edl says 374)
DOOR_SHUT = next((int(x["frame"]) for x in json.load(open(EDL))["events"] if x.get("kind") == "door_close"), 370) if os.path.exists(EDL) else 370
x, key = lo(); claim(fx, "street door latch", key, x, 334, 0, 0.32, 0.45, "door_open:C", "she lets herself in with her own key")
cr = S["squeaky_door"]; ck = "squeaky_door"
if cr is None: cr = S["handle_creak"]; ck = "handle_creak"
cr = cr[onset(cr, 0.1):][: int(1.0 * RATE)]; cr[-int(0.2 * RATE):] *= np.linspace(1, 0, int(0.2 * RATE))
claim(fx, "door creak (opening)", ck, cr, 334, 90, 0.3, 0.45, "door_open:C", "the old street door swings open")
x, key = dc(); x = x.copy(); x[-int(0.15 * RATE):] *= np.linspace(1, 0, int(0.15 * RATE))
claim(fx, "street door shuts", key, x, DOOR_SHUT, 0, 0.42, 0.45, "door_close:C", "home: the door closes behind her, not slammed")

# ------------------------------------------------------------------ the defining beat (window 16)
ke = S["kettle"]
cs = np.concatenate([[0.0], np.cumsum(ke ** 2)]); e = cs[RATE // 10:] - cs[:-(RATE // 10)]; i = int(np.argmax(e)) + RATE // 20
ks = ke[max(0, i - int(3.2 * RATE)): i + int(1.6 * RATE)][: int(4.4 * RATE)].copy()
ramp = np.clip(np.linspace(-0.12, 1.25, len(ks)), 0, 1) ** 1.6                     # begins with the rise f502->518 and keeps climbing
ramp[-int(1.1 * RATE):] *= np.linspace(1, 0.0, int(1.1 * RATE)) ** 1.2             # lifted off the heat
claim(fx, "kettle beginning to sing (rises with the silhouette)", "kettle", ks * ramp, 502, 0, 0.26, win_pan(16) + 0.1,
      "silhouette_rise:16", "someone inside has been waiting with the tea", depth="near, a room away: dry")
toi = S["toi"]
if toi is not None:
    y = toi[onset(toi, 0.06):][: int(0.7 * RATE)].copy(); y *= np.linspace(1, 0.7, len(y))
    claim(voice, "soft 'toi ?' (real speech, Lingua Libre), through the room", "toi", lp(y, 3400), 538, 240, 0.28, win_pan(16) + 0.05,
          "head_turn:16", "the one who waited greets the one who came home", depth="near, softened LP 3.4 kHz")
else:
    # HANDMADE hum: a warm three-note hum (triangle, vibrato), as a person humming while turning
    t = M.t(1.4); f = np.where(t < .45, 196, np.where(t < .9, 220, 247))
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.004 * np.sin(2 * np.pi * 5 * t))) / RATE
    y = (2 / np.pi * np.arcsin(np.sin(ph)) + 0.3 * np.sin(2 * ph)) * M.env(len(t), 0.12, 0.2, 0.7, 0.4)
    claim(voice, "a warm hummed tune (synth)", "hum", lp(y, 1800), 538, 240, 0.07, win_pan(16), "head_turn:16",
          "the one who waited hums as they turn", True)
# 'bonne nuit' as window 16 goes dark
bn = S["bonne_nuit"]
if bn is not None:
    y = bn[onset(bn, 0.05):][: int(0.95 * RATE)]
    claim(voice, "'bonne nuit' (real speech, Lingua Libre)", "bonne_nuit", lp(y, 3600), 696, 180, 0.3, win_pan(16) * 0.6,
          "window_off:16", "good night: the waiting is over, the flat goes to bed", depth="mid, softened LP 3.6 kHz")

# ------------------------------------------------------------------ crossover gate: only music 16.0-17.5
for s in (voice, fx, amb):
    s.gate(16.0, 17.5, 0.18)

# ------------------------------------------------------------------ loudness: one global gain to -23 LUFS integrated
stems = {s.name: s.st() for s in (voice, music, fx, amb)}
total = sum(stems.values())
L0 = lufs(total)
g_db = -23.0 - L0; g = 10 ** (g_db / 20)
LIM = {}
for _ in range(2):                                   # limit each scaled stem, re-trim the global gain
    for k in stems:
        stems[k], LIM[k] = limit(stems[k] * g, 0.55 if k == "fx" else 0.7); stems[k] /= g
    total = sum(stems.values()); g_db = -23.0 - lufs(total); g = 10 ** (g_db / 20)
peak = np.abs(total * g).max()
print("DIAG", L0, g_db, peak, {k: (round(lufs(v),1), round(float(np.abs(v).max()),3), round(int(np.argmax(np.abs(v).max(1)))/RATE,2)) for k, v in stems.items()})
if os.environ.get("DIAG"): sys.exit()
assert peak < 0.89, f"sample peak {peak} too hot"
mixrep = {"integrated_before": round(L0, 2), "global_gain_db": round(g_db, 2), "stems": {}}
def write(path, st):
    pcm = np.clip(np.round(st * 32767), -32768, 32767).astype("<i2")
    assert pcm.shape == (N, 2)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "2", "-i", "-", "-c:a", "pcm_s16le", path],
                   input=pcm.tobytes(), check=True)
for k, st in stems.items():
    st = st * g; write(f"{SRC}/stems/{k}.wav", st)
    seg_x = st[int(16.0 * RATE):int(17.5 * RATE)]
    mixrep["stems"][k] = dict(gain_db=round(g_db, 2), limiter_max_reduction_db=LIM[k], stem_lufs=round(lufs(st), 2), sample_peak_dbfs=round(20 * np.log10(np.abs(st).max() + 1e-12), 2),
                              crossover_16_17_5_peak_dbfs=round(20 * np.log10(np.abs(seg_x).max() + 1e-12), 1))
write(f"{OUT}/preview-A.wav", total * g)
mixrep["preview_lufs_internal"] = round(lufs(total * g), 2)
mixrep["contacts_source"] = csrc
json.dump(mixrep, open(f"{OUT}/mix-A.json", "w"), indent=1)

CUES.sort(key=lambda c: c["t_sound"])
win = [c for c in CUES if c["picture_event_id"].startswith("window_on:")]
offs = [c["offset_ms"] for c in win]
seq = [c["source_ledger_id"] for c in sorted(win, key=lambda c: c["frame"])]   # the SOUND (source), not its label
summary = dict(window_cues=len(win), offset_std_ms=round(float(np.std(offs)), 1), offset_range_ms=[min(offs), max(offs)],
               consecutive_repeat=any(a == b for a, b in zip(seq, seq[1:])), repeat_check_on="source_ledger_id, window cues sorted by frame",
               window_sequence=[[c["frame"], c["source_ledger_id"]] for c in sorted(win, key=lambda c: c["frame"])], contacts_source=csrc, handmade=HANDMADE,
               foraged_used={k: os.path.relpath(v, FILMS) for k, v in USED.items()})
json.dump(CUES, open(f"{OUT}/cues-A.json", "w"), indent=1, ensure_ascii=False)
json.dump(summary, open(f"{OUT}/cues-A.summary.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(mixrep, indent=1)); print(json.dumps(summary, indent=1, ensure_ascii=False))
