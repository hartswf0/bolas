"""Teuf-Teuf (Direction 1, "La paroi") -- montage editor's assembly.

Picture: the animator unit's frame-by-frame render (handmade cut-card puppets, logs,
cart and the GrabCut Ljubljana wheel) composited over the layout unit's toned
Cueva de las Manos plates, decoded with ffmpeg from
sources/teuf-teuf/animator/animator_master_0-44s.mp4. The editor adds: the two
three trial resets (13.0, 25.0, 34.0 s) as real cuts through a held black frame
with a white scratch wipe, the captions (FR + EN, small serif italic, cream, lower
band, no box) and the end source line.

Repair 1: there is ONE motion ledger, the rendered frames. motion.py drives the
picture; swarm/teuf-teuf/verify_sheet.py rewrites exposure.json and the
mechanism.json asserts from the render's own per-frame records, after this script
has rendered both mp4s. Captions and sound are timed to that sheet's events. Foraged material is the
commentary-sound unit's decoded cuts (PDSounds knock, Pwaivers steps, Gravity Sound
gravel, PDSounds church room); scrape, grind, rumble and scratch are synthesized
(declared) because the licensed wagon/quern recordings could not be downloaded (429).

    python3 films/teuf-teuf.py               # film + no-caption control
    python3 films/teuf-teuf.py --stills 7 17.5 30
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from kit import Film, Mix, RATE, OUT

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources" / "teuf-teuf"
SWARM = HERE / "swarm" / "teuf-teuf"
MASTER = SRC / "animator" / "animator_master_0-44s.mp4"
SIZE = (1280, 720)
FPS = 24
SECONDS = 44.0
NOCAP = "--nocaption" in sys.argv

ANIM = json.load(open(SWARM / "animation.json"))
ED = ANIM["for_the_editor"]
XF = json.load(open(SRC / "animator" / "exposure_animator.json"))["frames"]
SCORE = json.load(open(SWARM / "score.json"))
EV = {}
for e in ED["events"]:
    EV.setdefault(e["kind"], []).append(e["t"])

# ------------------------------------------------------------- captions ---
# Text from score.json; onsets re-timed to the picture's causal frames (lag 0.2-0.6 s).
STONE_F = np.array([f["stone"]["F"] for f in XF])


CAUSE = [   # the bar's named causes (plan s10.5), read from the rendered sheet's event list
    ("the 4th stick begins: the stone holds after its 3rd lurch", EV["stick"][3]),
    ("log A stops behind the stone (tok)", EV["log-stop"][0]),
    ("the cart passes the 3 m roller ghost", EV["pass-3m"][0]),
    ("the axle pins are pulled", EV["pin-pull"][0]),
]
LAG = [0.36, 0.34, 0.36, 0.34]
HOLD = [3.3, 3.2, 3.6, 3.8]
CAPS = []
for c, (cause, ct), lag, hold in zip(SCORE["captions"], CAUSE, LAG, HOLD):
    on = round(ct + lag, 3)
    CAPS.append(dict(i=c["i"], on=on, off=round(on + hold, 3), cause=cause, cause_t=round(ct, 3),
                     lag_s=round(on - ct, 3), fr=c["fr"], en=c["en"], voice=c["voice"]))
for c in CAPS:
    assert 0.2 <= c["lag_s"] <= 0.6, c
END = SCORE["end_line"]
STAGED = "Séquence mise en scène, non chronologique · staged sequence, not a chronology"
SRC_LINE = "Sources : Cueva de las Manos (Suzko, CC BY-SA 3.0) · roue des marais de Ljubljana (P. Milošević, CC BY-SA 4.0)"
SRC_LINE2 = "sons : PDSounds (domaine public) · Gravity Sound (CC BY 4.0) · Pwaivers (CC BY-SA 3.0)"
END_ON, END_OFF = 39.8, 44.0     # written on by 40.8 s, then held 3.2 s (review repair)

FONT_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
_fc = {}


def fnt(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(FONT_IT, size)
    return _fc[size]


CREAM = (236, 229, 199)
OLIVE = (22, 24, 14)


def type_layer(lines, alpha, reveal=1.0):
    """cream italic lines centred in the lower band, over a soft charcoal rub (no box)."""
    W, H = SIZE
    txt = Image.new("L", SIZE, 0)
    d = ImageDraw.Draw(txt)
    for s, size, y in lines:
        d.text((W / 2, y), s, font=fnt(size), fill=255, anchor="mm")
    if reveal < 1.0:  # write-on: a scratch moving left to right through the line
        bb = txt.getbbox() or (0, 0, W, H)
        xr = bb[0] + (bb[2] - bb[0]) * reveal
        m = Image.new("L", SIZE, 0)
        ImageDraw.Draw(m).rectangle([0, 0, xr, H], fill=255)
        txt = Image.fromarray((np.asarray(txt).astype(np.uint16) * np.asarray(m) // 255).astype(np.uint8))
    rub = txt.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(9))
    a_txt = np.asarray(txt).astype(np.float32) / 255 * alpha
    a_rub = np.clip(np.asarray(rub).astype(np.float32) / 255 * 1.6, 0, 1) * 0.62 * alpha
    return a_rub, a_txt


def comp_type(arr, a_rub, a_txt):
    arr = arr * (1 - a_rub[..., None]) + np.array(OLIVE, np.float32) * a_rub[..., None]
    arr = arr * (1 - a_txt[..., None]) + np.array(CREAM, np.float32) * a_txt[..., None]
    return arr


def caption_at(t):
    for c in CAPS:
        if c["on"] - 0.01 <= t < c["off"]:
            a = min(1.0, (t - c["on"]) / 0.25, (c["off"] - t) / 0.35)
            return [(c["fr"], 25, 648), (c["en"], 19, 680)], max(0.0, a)
    return None, 0.0


# ------------------------------------------------------------- picture ---
class Reader:
    """sequential ffmpeg decode of the animator master; reopens on a seek."""

    def __init__(self, path):
        self.path = path
        self.p = None
        self.k = None
        self.cache = {}

    def _open(self, k):
        if self.p:
            self.p.kill()
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{k / FPS:.4f}", "-i", str(self.path),
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.k = k

    def get(self, k):
        k = max(0, min(1055, k))
        if k in self.cache:
            return self.cache[k]
        if self.p is None or k != self.k:
            self._open(k)
        n = SIZE[0] * SIZE[1] * 3
        buf = self.p.stdout.read(n)
        if len(buf) < n:
            raise SystemExit(f"short read at frame {k}")
        self.k = k + 1
        a = np.frombuffer(buf, np.uint8).reshape(SIZE[1], SIZE[0], 3)
        if k in KEEP:
            self.cache[k] = a
        return a


CUTS = [312, 600, 816]       # trial resets, real cuts through black: 13.0 (drag -> rollers), 25.0 (-> wheel), 34.0 (-> counter-check)
KEEP = set()
BLACK = np.array([15, 17, 9], np.float32)   # the reference's olive black
RD = Reader(MASTER)


def scratch_wipe(arr, u, seed):
    """white engraved line sweeping left to right, with its dark lip (handmade)."""
    W, H = SIZE
    rng = np.random.default_rng(seed)
    x = -40 + (W + 80) * u
    im = Image.new("L", SIZE, 0)
    d = ImageDraw.Draw(im)
    for j in range(3):
        pts = []
        for y in range(-20, H + 40, 36):
            pts.append((x + 18 * math.sin(y / 70 + seed + j) + rng.normal(0, 3) - j * 11, y))
        d.line(pts, fill=255 - 60 * j, width=3 - (j > 0))
    a = np.asarray(im).astype(np.float32) / 255
    lip = np.roll(np.roll(a, 2, 0), 2, 1)
    arr = arr * (1 - 0.18 * lip[..., None])
    return arr * (1 - a[..., None]) + 246 * a[..., None]


def picture_frame(k):
    t = k / FPS
    arr = None
    for c in CUTS:  # reset = a real cut: 2 frames down to black, 2 held black, 3 frames up; a scratch wipe crosses the black
        if c - 2 <= k < c + 5:
            src = RD.get(k).astype(np.float32)
            if k < c:
                u = (k - (c - 3)) / 3.0
            elif k < c + 2:
                u = 1.0
            else:
                u = 1.0 - (k - (c + 1)) / 4.0
            arr = src * (1 - u) + BLACK * u
            if c - 1 <= k < c + 3:
                arr = scratch_wipe(arr, (k - (c - 1) + 0.5) / 4.0, c)
    if arr is None:
        arr = RD.get(k).astype(np.float32)
    if not NOCAP:
        lines, a = caption_at(t)
        if lines and a > 0:
            arr = comp_type(arr, *type_layer(lines, a))
    # end source line (in both versions: it is provenance, not commentary). Staged label first, larger.
    if END_ON <= t < END_OFF:
        rev = min(1.0, (t - END_ON) / 1.0)
        a = min(1.0, (END_OFF - t) / 0.25, 1.0)
        arr = comp_type(arr, *type_layer([(STAGED, 21, 641), (SRC_LINE, 16, 672), (SRC_LINE2, 15, 694)], a, rev))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# --------------------------------------------------------------- sound ---
def wav(path):
    w = wave.open(str(path))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2)
    return x


CS = SRC / "commentary-sound"
KNOCK = [wav(CS / f"cut-knock-{i}.wav") for i in range(9)]
STEP = [wav(CS / "cut-step-stone-0.wav"), wav(CS / "cut-step-stone-1.wav")]
GRAVEL = wav(CS / "cut-step-gravel.wav")
ROOM = wav(SRC / "sound" / "stem-room.wav")  # PDSounds church, low-passed 220 Hz (commentary-sound unit)
SOUND_LOG = []


def resample(x, f):
    n = max(2, int(len(x) / f))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def per_frame_to_audio(v, n):
    tf = np.arange(len(v)) / FPS
    ta = np.arange(n) / RATE
    return np.interp(ta, tf, v)


def lowpass(x, cut):
    """FFT low-pass (no scipy here)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    X *= 1 / (1 + (f / cut) ** 4)
    return np.fft.irfft(X, len(x))


def build_sound(mix):
    rs = np.random.RandomState(7)
    n = mix.n
    # room: the foraged church air, under everything
    mix.add(ROOM[:, 0], 0.0, gain=1.0, pan=-0.2)
    mix.add(ROOM[:, 1], 0.0, gain=1.0, pan=0.2)
    SOUND_LOG.append(dict(t=0.0, what="room bed (foraged, PDSounds church walking, low-passed)", stem="room"))

    def knock(t, gain=0.5, pan=0.0, pitch=1.0, i=None, what=""):
        k = KNOCK[(i if i is not None else int(t * 7)) % 9]
        mix.add(resample(k, pitch), t, gain=gain, pan=pan)
        SOUND_LOG.append(dict(t=round(t, 3), what=what or "wood knock", src="Knocking on wood or door.ogg (PDSounds, PD)", stem="knocks"))

    def thud(t, gain=0.45, what="thud"):
        mix.thud(t, freq=62, gain=gain, seconds=0.4)
        SOUND_LOG.append(dict(t=round(t, 3), what=what, src="synthesized (kit thud)", stem="impacts"))

    # footsteps on every IK plant of the picture
    for who, ts in ED["footsteps_s"].items():
        for j, t in enumerate(ts):
            k = min(1055, int(round(t * FPS)))
            fx = np.mean(XF[k][who]["feet_x"])
            pan = float(np.clip((fx / 640 - 1) * 0.7, -0.8, 0.8))
            s = STEP[j % 2]
            mix.add(resample(s, 1 + 0.08 * math.sin(j * 2.3)), t, gain=0.32, pan=pan)
            if j % 3 == 0:
                mix.add(GRAVEL[:, 0] if GRAVEL.ndim == 2 else GRAVEL, t + 0.005, gain=0.18, pan=pan)
            SOUND_LOG.append(dict(t=round(t, 3), what=f"footstep {who}", src="Concrete Steps 2.ogg (Pwaivers, CC BY-SA 3.0)" + (" + gravel (Gravity Sound, CC BY 4.0)" if j % 3 == 0 else ""), stem="steps"))

    # drag scrape and counter-check grind: grit noise following the stone's speed
    v = np.abs(np.gradient(STONE_F)) * FPS            # px/s
    shot = [f["shot"] for f in XF]
    drag = np.array([s == "1_drag" for s in shot], float)
    grind = np.array([(s == "5_counter_no_axle" and EV["wheel-drop"][0] - 0.05 <= f["t"] <= EV["stop-counter"][0] + 0.05) for s, f in zip(shot, XF)], float)
    env = per_frame_to_audio(np.clip(v / 120, 0, 1.2) * (drag * 0.55 + grind * 0.9), n)
    grit = rs.randn(n)
    grit = mix.band(grit, 700, 3800) + 0.6 * (rs.rand(n) < 0.004) * rs.randn(n)
    sc = grit * lowpass(env, 30)
    mix.add(sc, 0.0, gain=0.55, pan=-0.2)
    SOUND_LOG.append(dict(t="5.0-11.5, 35.9-36.2", what="scrape / grind following stone speed", src="synthesized (grit noise)", stem="scrape"))

    # rumble: logs and wheels, amplitude follows angular speed
    om = np.zeros(len(XF))
    for k, f in enumerate(XF):
        if k == 0:
            continue
        p = XF[k - 1]
        if "logs" in f and "logs" in p:
            for nme, L in f["logs"].items():
                if nme in p["logs"] and L[2] in ("carried", "free"):
                    om[k] += abs(L[1] - p["logs"][nme][1]) * FPS
        if "wheel_theta" in f and "wheel_theta" in p:
            om[k] += abs(f["wheel_theta"] - p["wheel_theta"]) * FPS * 1.4
        if "wheels" in f and "wheels" in p:
            for a, b in zip(f["wheels"], p["wheels"]):
                om[k] += abs(a[1] - b[1]) * FPS
    for c in CUTS + [312, 336, 389, 451]:  # no rumble spikes across camera changes / resets
        om[max(0, c - 1):c + 1] = 0
    env = lowpass(per_frame_to_audio(np.clip(om / 6, 0, 1.3), n), 12)
    rum = lowpass(lowpass(rs.randn(n), 140), 140) * 9
    rum += 0.3 * np.sin(2 * np.pi * np.cumsum(55 + 40 * env) / RATE)
    mix.add(rum * env, 0.0, gain=0.3)
    SOUND_LOG.append(dict(t="14-23, 26-33, 34.7-36.3", what="rumble following log/wheel angular speed", src="synthesized (low noise)", stem="rumble"))

    # plank knock once per wheel turn (shot 4)
    th = [(f["t"], f["wheel_theta"]) for f in XF if "wheel_theta" in f]
    for (t0, a0), (t1, a1) in zip(th, th[1:]):
        if a1 > a0 and int(a1 // (2 * math.pi)) > int(a0 // (2 * math.pi)) and a0 > 0:
            knock(t1, gain=0.28, pitch=0.8, what="plank knock, one wheel turn")

    # contact events of the picture
    for t in EV["slip"]:
        pass  # the scrape bed carries each lurch; silence is the stick
    thud(EV["drag-stop"][0], what="drag stops at 1.2 m")
    knock(EV["lift"][0], gain=0.45, pitch=1.1, what="lever bites under the stone")
    for j, t in enumerate(EV["log-in"]):
        knock(t + 0.07 * j, gain=0.55, pan=-0.3 + 0.3 * j, i=j, what="log lands under the stone")
    thud(EV["settle"][0], gain=0.35, what="stone settles onto the logs")
    for t in EV["log-stop"]:
        knock(t, gain=0.7, pan=-0.45, pitch=0.92, i=4, what="tok: log stops behind")
        knock(t + 0.11, gain=0.2, pan=-0.45, pitch=1.05, i=5, what="tok rebound")
    for t in EV["stone-stop"] + EV["stone-stop-2"]:
        thud(t, gain=0.3, what="stone stops on its logs")
    knock(EV["log-set"][0], gain=0.6, pan=0.25, i=6, what="log D set down in front")
    knock(EV["log-under"][0], gain=0.4, pan=0.2, i=7, what="stone rides onto log D")
    thud(EV["wheel-stop"][0], gain=0.3, what="cart stops at 8 m")
    mix.click(EV["pin-pull"][0], gain=0.35, bright=3000)
    knock(EV["pin-pull"][0] + 0.06, gain=0.3, pitch=1.3, i=8, what="pins pulled, forks drop")
    knock(EV["wheel-drop"][0], gain=0.55, pan=-0.4, i=2, what="rear wheel falls out")
    thud(EV["wheel-drop"][0] + 0.02, gain=0.5, what="platform's rear hits the ground")
    thud(EV["stop-counter"][0], gain=0.35, what="platform grinds to a stop")
    knock(EV["loose-wheel-stop"][0], gain=0.4, pan=-0.5, i=3, what="loose wheel stops")
    knock(EV["callback"][0], gain=0.5, pan=-0.5, i=4, what="loose wheel rocks once (tok)")
    knock(EV["callback"][0] + 0.24, gain=0.18, pan=-0.5, pitch=1.1, i=5, what="rock back")

    # scratch strokes: title write-on, ghosts, resets, end line (synthesized)
    def scratch(t0, dur, gain=0.05):
        m = int(dur * RATE)
        x = mix.band(rs.randn(m), 2500, 9000) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, dur * 9, m))))
        x *= np.minimum(1, np.linspace(0, 1, m) * 20) * np.minimum(1, np.linspace(1, 0, m) * 10)
        mix.add(x, t0, gain=gain, pan=0.1)
        SOUND_LOG.append(dict(t=round(t0, 3), what=f"scratch {dur:.2f}s", src="synthesized", stem="scratch"))
    scratch(0.85, 1.2)
    for t_on in (11.7, 23.15, 33.35):
        scratch(t_on, 0.8, 0.035)
    for c in CUTS:
        scratch(c / FPS - 0.125, 0.25, 0.06)
    scratch(END_ON, 1.0, 0.04)


# ------------------------------------------------------------- assemble ---
def make_film(slug):
    film = Film(slug, seconds=SECONDS, size=SIZE, boil=0, wobble=0, seed=11)
    film.poster_at = 17.6

    def frame(t, ink):
        ink._grain = False  # the plates carry their own fixed print grain
        ink.img = picture_frame(int(round(t * FPS)))
    film.picture(frame)
    film.sound(build_sound)
    return film


if __name__ == "__main__":
    if "--stills" in sys.argv:
        make_film("teuf-teuf").render()
    else:
        nc = NOCAP
        make_film("teuf-teuf-nocaption" if nc else "teuf-teuf").render()
        if not nc:
            json.dump(dict(captions=CAPS, sound_events=SOUND_LOG), open(SWARM / "assembly-cues.json", "w"), indent=1, ensure_ascii=False)
            subprocess.run([sys.executable, __file__, "--nocaption"], check=True)
