"""Le Chant du styrène — a reverse tour of a moulded ring (38.0 s).

Four loose rings (P4, finished parts) fly back onto the runner they were cut
from (P3, the shot); the runner-with-rings becomes the melt in the hollow of a
steel mould and the melt drains backward out of it, leaving four ring-shaped
hollows (M + P2); the melt was a forest of plastic trees and the trees were
grain (P1, raw stock), which falls onto a real heap of granules.

This script is the editor's assembly only. It pastes frames rendered by the
swarm units (films/sources/le-chant-du-styrene/<unit>/), adds the 2.35
letterbox on true black, the four alexandrines as captions in the lower bar,
one shared grade (black point + highlight roll-off) and one grain strength
(kit's), and mixes the process-verse unit's stems with Mix.add.

    FORAGED: Spritzguss teile.jpg (Gmhofmann, CC BY-SA 4.0) -> rings + runner
             Injection mold - (11).jpg (Bricetofly, CC0) -> mould steel
             Granuls orange.jpg (Lobkovs, CC BY-SA 3.0) -> heap
             Gigaset ... Engel Injection Moulding Machine (Work With Sounds,
             CC BY 3.0) -> press bed under L3
    HANDMADE: puppetry, colour gel (declared), melt simulation, harmonic
              trees + pellets, blue practicals, all other sound.

REPAIR ROUND 1 (critic): Sh1, Sh3a/Sh3b, Sh4 and the Sh5 pellet layer are re-rendered by the editor's
repair scripts in swarm/le-chant-du-styrene/editor-build/ (sh1v2.py, melt3e.py, sh4v2.py), built on the
units' code without editing it, into sources/le-chant-du-styrene/editor-repair/. Sh4's trees are now MELT
(lit-through, liquid) breaking up into drops that freeze into the real heap's granule colour (melt <- pellets),
with no reunion into chains. The mix ducks transients off the meter grid; the encode uses a lower CRF.

Run from the project root:  python3 films/le-chant-du-styrene.py
Stills:                     python3 films/le-chant-du-styrene.py --stills 5 16.5 24 26.5 32
"""
import json
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import kit
from kit import Film, font, ease, clamp

SLUG = "le-chant-du-styrene"
SRC = kit.HERE / "sources" / SLUG
CUT = SRC / "cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-"
MELT = SRC / "melt-simulation-camera-unit-b-test-shot-sh3a-sh3b-defining-beat-"
HARM = SRC / "harmonic-trees-to-granule-camera-unit-c-sh4-sh5-falling-pellets-"
STEMS = SRC / "process-verse-process-researcher-verse-writer-voice-sound-performer-" / "stems"
SWARM = kit.HERE / "swarm" / SLUG
REP = SRC / "editor-repair"

SECONDS = 38.0
FPS = 24
BAND_Y0, BAND_Y1 = 66, 474          # 2.35 letterbox: 960x408 band
CREAM = (232, 226, 210)             # #E8E2D2

# --------------------------------------------------------------- shot map ---
# Global frame index k, t = k/24. Units rendered on this same index.
DISSOLVE = (415, 422)               # Sh2b hold -> melt-filled mould (8 frames)
SHOTS = [  # (first frame, last frame, id, source dir)
    (0, 206, "Sh1", REP / "sh1"),
    (207, 312, "Sh2a", CUT / "sh2a"),            # C1 between 312 and 313
    (313, 422, "Sh2b", CUT / "sh2b"),
    (423, 499, "Sh3a", REP / "sh3a"),            # C2 between 499 and 500
    (500, 662, "Sh3b", REP / "sh3b"),
    (663, 839, "Sh4", REP / "sh4"),
    (840, 911, "Sh5", None),                     # heap + pellet layer
]

_heap = None


def heap():
    global _heap
    if _heap is None:
        h = np.asarray(Image.open(CUT / "sh5" / "heap_rgba_960x408.png").convert("RGBA"), np.float32)
        _heap = h[..., :3] * (h[..., 3:] / 255.0)       # cutout onto true black
    return _heap


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), np.float32)


def band_frame(k):
    """The 960x408 picture band for global frame k, as float RGB."""
    k = min(max(k, 0), 911)
    if DISSOLVE[0] <= k <= DISSOLVE[1]:
        a = (k - DISSOLVE[0] + 1) / 8.0                   # 0.125 ... 1.0
        a = a * a * (3 - 2 * a)
        b = load(CUT / "sh2b" / f"f{k:04d}.png")
        m = load(REP / "sh3a_dissolve_target" / f"f{k:04d}.png")
        return b * (1 - a) + m * a
    for f0, f1, sid, d in SHOTS:
        if f0 <= k <= f1:
            if sid == "Sh5":
                p = np.asarray(Image.open(REP / "sh5_pellets_rgba" / f"f{k:04d}.png").convert("RGBA"), np.float32)
                a = p[..., 3:] / 255.0
                return heap() * (1 - a) + p[..., :3] * a
            return load(d / f"f{k:04d}.png")
    raise ValueError(k)


# ------------------------------------------------------------------ grade ---
BLACK_POINT = 3.0      # shared: lifts nothing, pulls compression shadows to 0
KNEE, CEIL = 196.0, 222.0   # shared highlight roll-off: no whites


EDGE = np.linspace(1.0, 0.0, 6)[1:5].astype(np.float32)
EDGE6 = np.linspace(1.0, 0.0, 8)[1:7].astype(np.float32)


def grade(x):
    x = np.clip((x - BLACK_POINT) * (255.0 / (255.0 - BLACK_POINT)), 0, None)
    over = x > KNEE
    span = CEIL - KNEE
    x[over] = KNEE + span * (1 - np.exp(-(x[over] - KNEE) / span))
    return x


# --------------------------------------------------------------- captions ---
VERSE = json.loads((SWARM / "process_verse.json").read_text())["verse"]["lines"]


def captions(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    f = font("serif", 23)
    cy = (BAND_Y1 + 540) // 2 + 1
    for L in VERSE:
        on, end = L["onset"], L["line_end"]
        a = ease(t, on - 0.3, on) * (1 - ease(t, end + 0.6, end + 0.95))
        if a <= 0:
            continue
        h1, h2 = L["caption_hemistichs"]
        h2_on = L["syllable_onsets"][6]
        a2 = a * (0.38 + 0.62 * ease(t, h2_on - 0.25, h2_on))   # 2nd hemistich brightens at its onset
        A = int(255 * a)
        d.text((480 - 15, cy), h1, font=f, fill=CREAM + (A,), anchor="rm")
        d.text((480 + 15, cy), h2, font=f, fill=CREAM + (int(255 * a2),), anchor="lm")
        d.line([(480, cy - 10), (480, cy + 10)], fill=CREAM + (int(170 * a),), width=1)   # the caesura


# declared, in the picture (reviewer round 1): small dim tags in the upper bar
TAGS = [(0.9, 7.9, "photographie réelle, couleur substituée"), (17.9, 27.3, "coulée simulée"),
        (27.9, 34.6, "coulée simulée, granulés dessinés"), (35.3, 37.6, "tas photographié, chute dessinée")]


def tags(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    f = font("serif", 14)
    for a0, a1, s in TAGS:
        a = ease(t, a0, a0 + 0.5) * (1 - ease(t, a1 - 0.5, a1))
        if a > 0:
            d.text((944, 33), s, font=f, fill=CREAM + (int(130 * a),), anchor="rm")


# ---------------------------------------------------------------- picture ---
film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0, seed=1958)
film.poster_at = 24.0


@film.picture
def picture(t, ink):
    ink.paper((0, 0, 0), grain=False)             # kit grain is applied below, band only
    k = ink.i
    full = np.zeros((540, 960, 3), np.float32)
    full[BAND_Y0:BAND_Y1] = grade(band_frame(k))
    full[BAND_Y0:BAND_Y0 + 4] *= EDGE[::-1, None, None]      # 4 px gate feather: no encode bleed into the bars
    full[BAND_Y1 - 8:BAND_Y1 - 2] *= EDGE6[:, None, None]    # 8x8 block row 472-479 straddles the bar: keep it dark
    full[BAND_Y1 - 2:BAND_Y1] = 0
    img = kit._add_grain(Image.fromarray(full.clip(0, 255).astype(np.uint8)), k)   # one grain strength
    a = np.asarray(img).copy()
    a[:BAND_Y0] = 0
    a[BAND_Y1:] = 0                               # bars stay true black
    img = Image.fromarray(a)
    captions(img, t)
    tags(img, t)
    ink.img = img
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------------ sound ---
# U1's stems at U1's gains, except: press bed -6 dB (L3 must be countable), L2 meter +2 dB.
GAINS = {"meter": 1.0, "ring_events": 1.0, "drain": 0.9, "rain": 0.8, "chord": 0.8, "room": 1.0, "press_foraged": 0.5}
CUES = json.loads((STEMS / "cues.json").read_text())["verse"]
RATE = kit.RATE


def read_wav(path):
    with wave.open(str(path)) as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768.0
    x = x.reshape(-1, ch)
    return x[:, 0].copy(), x[:, -1].copy()


def duck(n, times, pre=0.05, post=0.11, floor=0.12, ramp=0.012):
    """gain envelope that clears a window around each meter onset (mixing, not new material)"""
    g = np.ones(n)
    for t in times:
        a, b = int((t - pre) * RATE), int((t + post) * RATE)
        r = int(ramp * RATE)
        g[max(a, 0):b] = np.minimum(g[max(a, 0):b], floor)
        if a - r > 0:
            g[a - r:a] = np.minimum(g[a - r:a], np.linspace(1, floor, r))
        g[b:b + r] = np.minimum(g[b:b + r], np.linspace(floor, 1, len(g[b:b + r])))
    return g


def gap_duck(n, line, floor=0.3):
    """lower a bed under a line's caesura gap (6th pulse + 0.15 s ... 7th pulse - 0.05 s)"""
    on = CUES[line]
    c, half = (on[5] + 0.15 + on[6] - 0.05) / 2, (on[6] - on[5] - 0.2) / 2
    return duck(n, [c], half, half, floor, 0.03)


def meter_gain(n):
    g = np.ones(n)
    a, b = int(10.9 * RATE), int(15.0 * RATE)
    g[a:b] = 1.26                                     # L2 +2 dB over the ring snaps
    return g


@film.sound
def sound(mix):
    n = mix.n
    env = {
        "ring_events": duck(n, CUES["L2"], 0.045, 0.11, 0.10),
        "drain": duck(n, CUES["L3"], 0.09, 0.13, 0.08) * gap_duck(n, "L3", 0.25),
        "press_foraged": duck(n, CUES["L3"], 0.09, 0.13, 0.18) * gap_duck(n, "L3", 0.3),
        "rain": duck(n, CUES["L4"], 0.07, 0.10, 0.12),
        "meter": meter_gain(n),
    }
    for name, g in GAINS.items():
        left, right = read_wav(STEMS / f"{name}.wav")
        m = min(len(left), n)
        e = env.get(name, np.ones(n))[:m]
        # pan -1 / +1 route a signal to one side at gain 1.414; undo that
        mix.add(left[:m] * e, 0.0, g / 1.414, pan=-1.0)
        mix.add(right[:m] * e, 0.0, g / 1.414, pan=1.0)
    # Sh1 repair: two more set-downs (1.25 s, 1.85 s), U1's own handmade set-down at 0.60 s reused
    left, right = read_wav(STEMS / "ring_events.wav")
    seg = (left[int(0.55 * RATE):int(1.15 * RATE)] + right[int(0.55 * RATE):int(1.15 * RATE)]) / 2
    mix.add(seg, 1.25 - 0.05, 0.85, pan=0.27)
    mix.add(seg, 1.85 - 0.05, 0.75, pan=0.09)
    # L3: the viscous low pulses get a short struck attack (handmade), accents on syllables 6 and 12
    for i, t in enumerate(CUES["L3"]):
        mix.click(t, gain=0.30 if i in (5, 11) else 0.22, pan=0.0, bright=1400, seconds=0.035)
        mix.thud(t, freq=150, gain=0.18 if i in (5, 11) else 0.12, seconds=0.12)


class Film2(Film):
    """kit.Film with a lower CRF (the critic could not measure the grain or the steel at CRF 28)."""
    CRF = "21"

    def render(self, out_dir=kit.OUT, preview=None):
        import subprocess as sp
        real = sp.Popen

        def popen(cmd, *a, **k):
            if isinstance(cmd, list) and "-crf" in cmd:
                cmd = list(cmd); cmd[cmd.index("-crf") + 1] = self.CRF
            return real(cmd, *a, **k)
        sp.Popen = popen
        try:
            return Film.render(self, out_dir, preview)
        finally:
            sp.Popen = real


film.__class__ = Film2


if __name__ == "__main__":
    film.render()
