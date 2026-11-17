"""Les caids de la gaudriole -- "Folded dialogue" (SCION swarm, montage editor).

A printed two-panel strip (Wilhelm Busch's 1865 Max und Moritz plates cut out as
puppets, pen-drawn balloons, lettering, key, forearm and service door, printed on
a real paper scan) lies on a table made from a real wood scan. The tabletop is a
computed stop-motion: every exposure is rendered in code (perspective-warped facets
of the scanned sheet, z-buffer, contact shadows), not photographed. Its puppets settle into the printed
pose; then the sheet folds by stop-motion (mountain A, valley M) until A lies on
B and the two half-panels read as one: "THE KEY? I HAD IT / IN MY POCKET / ALL
ALONG." -- "OH? REALLY?". It unfolds, refolds, and ends on a light box that
shows every hidden layer, mirrored or not, where the fold geometry puts it.

Sources of every frame (nothing is drawn here except the two pen-lettered cards):
  shots 1, 5, 7, 8 : exposures rendered by the tabletop unit
                      (sources/les-caids-de-la-gaudriole/tabletop/shot-N/eNNN.png)
  shots 2, 3, 4, 6 : rendered here, per exposure, with the tabletop unit's own
                      renderer (swarm/.../shots/build/render_shots.py) and the
                      puppet rig (puppets/rig.json, poses.json) -- 2 and 3 with the
                      corrected reading drift, 4 = pull-back to the open strip,
                      6 = hold + stepped push-in on the settled folded state.
All strip art comes from swarm/.../strip/strip-art.png (the page's art, sha256 in
strip/sheet.json). Stop-motion on twos: 12 exposures/s in a 24 fps container.

Sound: the tabletop unit's foraged effect stems (paper ticks per exposure, thud,
bell strike, light-box switch; declared synthetic lamp hum) laid at each shot's
start, the foraged room tone (Wreckless, 1935) under all of it, and one more bell
strike at 0:40 on "OH? REALLY?". Run from the project root:
    python3 films/les-caids-de-la-gaudriole.py [--stills t ...]
"""
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import Film, RATE  # noqa: E402

SLUG = "les-caids-de-la-gaudriole"
WS = os.path.join(HERE, "swarm", SLUG)
BUILD = os.path.join(WS, "shots", "build")
STRIP = os.path.join(WS, "strip")
SRC = os.path.join(HERE, "sources", SLUG)
TAB = os.path.join(SRC, "tabletop")
SND = os.path.join(WS, "shots", "sound")
sys.path.insert(0, BUILD)
sys.path.insert(0, STRIP)

import render_shots as RS  # noqa: E402  (tabletop unit's renderer; reads strip/strip-art.png)
from pen import pen, text_width  # noqa: E402  (handmade stroke alphabet)

W, H, XPS = 960, 540, 12      # frame size, exposures per second (on twos)

# ------------------------------------------------------------- renderer -----
_R = None


def R():
    global _R
    if _R is None:
        _R = RS.Renderer()
        _R.open_cs = RS.section(*RS.OPEN)
        _R.flat_cs = RS.section(*RS.FLAT)
        _R.rest = RS.PUP.render({}).astype(np.int16)
    return _R


def u8(img):
    return np.clip(img, 0, 255).astype(np.uint8)


def cam_shift(c, d):
    d = np.asarray(d, float)
    return (c[0] + d, c[1] + d, c[2])


def puppet_exposure(ex, jit, gain):
    r = R()
    pos, tgt, foc = ex["cam"]
    cam = RS.Cam(pos + jit, tgt + jit * 0.5, foc)
    pr = RS.PUP.render(ex["pose"]).astype(np.int16)
    sheet = np.where(np.abs(pr - r.rest) > 2, pr, RS.ART).astype(np.uint8)
    r.set_art(sheet)
    img = r.frame(cam, r.open_cs, gain)
    r.set_art(RS.ART)
    return u8(img)


# reading drift corrected (the tabletop unit's own fix, see its report)
DRIFT2 = (45, -15, 0)
DRIFT3 = (40, -10, 0)
END2 = cam_shift(RS.CAM_P1, DRIFT2)
END3 = cam_shift(RS.CAM_P2, DRIFT3)
SEQ2 = RS.seq_puppet(2, RS.CAM_WIDE, RS.CAM_P1, DRIFT2)
SEQ3 = RS.seq_puppet(3, END2, RS.CAM_P2, DRIFT3)
_rng = np.random.RandomState(40)
JIT = {s: [(_rng.normal(0, 1.0, 3), 1 + _rng.uniform(-0.02, 0.02)) if ex.get("jit") else (np.zeros(3), 1.0)
           for ex in seq] for s, seq in (("2", SEQ2), ("3", SEQ3))}

# shot 6: hold on the settled fold, then a stepped push-in that reads the joined
# balloon left to right across the seam, drops to the sleeve->hand->key join, and
# pans to the boys' "OH? REALLY?" (bell at its exposure 72 = 0:40).
C_HOLD = RS.CAM_PACKET
C_L1 = RS.cam_at(1590, 205, 1180, 24, 1150)    # "THE KEY? I HAD IT" (left of the seam)
C_L2 = RS.cam_at(1930, 205, 1180, 24, 1150)    # "...IN MY POCKET / ALL ALONG." across it
C_JOIN = RS.cam_at(1800, 560, 1180, 24, 1150)  # the miller's sleeve into the porter's hand + key
C_OH = RS.cam_at(2070, 450, 1240, 24, 1150)    # the boys, "OH? REALLY?"
# repair r1: the first still hold on the settled reading is 3 (end of shot 5) + 18
# exposures = 1.75 s (was 1.25 s), so A3's >= 1.5 s holds before the push-in starts.
SHOT6 = ([C_HOLD] * 18 +
         [RS.cam_mix(C_HOLD, C_L1, RS.ease((i + 1) / 12)) for i in range(12)] +
         [C_L1] * 6 +
         [RS.cam_mix(C_L1, C_L2, RS.ease((i + 1) / 14)) for i in range(14)] +
         [C_L2] * 6 +
         [RS.cam_mix(C_L2, C_JOIN, RS.ease((i + 1) / 8)) for i in range(8)] +
         [C_JOIN] * 8 +
         [RS.cam_mix(C_JOIN, C_OH, RS.ease((i + 1) / 6)) for i in range(6)] +
         [C_OH] * 18)
assert len(SHOT6) == 96, len(SHOT6)

# shot 4: pull back, stepped, from the end of shot 3 to the whole open strip; hold.
SHOT4 = [RS.cam_mix(END3, RS.CAM_WIDE, RS.ease((i + 1) / 12)) for i in range(12)] + [RS.CAM_WIDE] * 24


def flat_or_open(cam, folded):
    r = R()
    pos, tgt, foc = cam
    return u8(r.frame(RS.Cam(pos, tgt, foc), r.flat_cs if folded else r.open_cs, 1.0))


# --------------------------------------------------------- pen cards --------
_paper = None


def card_paper():
    """The same neutralised paper scan the strip is printed on, lit by the key lamp."""
    global _paper
    if _paper is None:
        p = Image.open(os.path.join(SRC, "paper-engineer-writer", "paper-front-4800x1800.png")).convert("RGB")
        p = np.asarray(p.crop((700, 0, 3900, 1800)).resize((W * 2, H * 2), Image.LANCZOS), np.float32)
        fall = R().fall
        _paper = p * np.clip(fall, 0.86, 1.04)[..., None]
    return _paper


def card(lines, e, write_xps=None):
    """lines: (text, cap_px_at_2x, y_at_2x). Written stroke by stroke: with write_xps,
    `write_xps` letters appear per exposure (straight-ahead, on twos)."""
    m = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(m)
    shown = 10 ** 6 if write_xps is None else int(e * write_xps)
    for i, (s, size, y) in enumerate(lines):
        k = max(0, min(len(s), shown))
        shown -= len(s)
        if k == 0:
            continue
        x0 = W - text_width(s, size) / 2
        pen(d, s[:k], x0, y, size, ink=255, seed=31 + i)
    ink = np.asarray(m, np.float32)[..., None] / 255.0
    img = card_paper() * (1 - 0.93 * ink)
    return np.asarray(Image.fromarray(u8(img)).resize((W, H), Image.LANCZOS))


TITLE = [("FOLDED DIALOGUE", 92, 400),
         ("AFTER LÉCROART - OUBAPO - FIGURES W. BUSCH 1865", 30, 600)]
CREDITS = [(t, 28, 170 + 80 * i) for i, t in enumerate([
    "FIGURES: W. BUSCH, MAX UND MORITZ 1865, PD, COMMONS",
    "PAPER SCAN: JAMES PUCKETT, CC BY 2.0, GRADED",
    "TABLE SCAN: BANGO TEXTURES, CC0",
    "PAPER, THUD, SWITCH: STEPHAN, GREGORYWEIR, MKFI (PD)",
    "BELL: WORK WITH SOUNDS / KONRAD GUTKOWSKI, CC BY 4.0,",
    "WWS SIGNALBELL, ONE STRIKE CUT, FADED, RE-LEVELLED",
    "ROOM TONE: WRECKLESS (1935), JAM HANDY, PD, PRELINGER",
    "PEN-DRAWN: LETTERING, BALLOONS, KEY, FOREARM, DOOR",
    "TABLE, FOLD, LIGHT BOX: RENDERED IN CODE FROM THE SCANS,",
    "ONE EXPOSURE AT A TIME - LAMP HUM SYNTHESISED"])]


# --------------------------------------------------------- timeline ---------
def tab(shot):
    return lambda e: np.asarray(Image.open(os.path.join(TAB, f"shot-{shot}", f"e{e:03d}.png")).convert("RGB"))


SEGMENTS = [  # (name, exposures, exposure -> HxWx3 uint8)
    ("title", 36, lambda e: card(TITLE, e, write_xps=3)),
    ("shot1", 48, tab(1)),
    ("shot2", 96, lambda e: puppet_exposure(SEQ2[e], *JIT["2"][e])),
    ("shot3", 96, lambda e: puppet_exposure(SEQ3[e], *JIT["3"][e])),
    ("shot4", 36, lambda e: flat_or_open(SHOT4[e], False)),
    ("shot5", 96, tab(5)),
    ("shot6", 96, lambda e: flat_or_open(SHOT6[e], True)),
    ("shot7", 96, tab(7)),
    ("shot8", 108, tab(8)),
    ("credits", 48, lambda e: card(CREDITS, e)),
]
STARTS, _t = {}, 0.0
for name, n, _ in SEGMENTS:
    STARTS[name] = _t
    _t += n / XPS
SECONDS = _t

_last = {}


def exposure_at(t):
    for name, n, fn in SEGMENTS:
        t0 = STARTS[name]
        if t0 <= t < t0 + n / XPS or name == SEGMENTS[-1][0]:
            e = min(n - 1, int((t - t0) * XPS + 1e-6))
            key = (name, e)
            if _last.get("key") != key:
                _last["key"], _last["img"] = key, fn(e)
            return _last["img"]


film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0)
film.poster_at = STARTS["shot6"] + 3.0


@film.picture
def frame(t, ink):
    ink.paper(grain=False)        # no added grain: the texture is the paper scan itself
    ink.paste(Image.fromarray(exposure_at(t)), (0, 0))


# --------------------------------------------------------------- sound ------
def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == RATE
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
        return a.reshape(-1, w.getnchannels())


@film.sound
def sound(mix):
    n = mix.n
    # foraged room tone (Wreckless, 1935), looped with 0.4 s crossfades, whole film
    room = read_wav(os.path.join(SND, "roomtone-10s.wav"))[:, 0]
    room = room[int(0.4 * RATE):int(9.6 * RATE)]
    xf = int(0.4 * RATE)
    win = np.ones(len(room))
    win[:xf] = np.linspace(0, 1, xf)
    win[-xf:] = np.linspace(1, 0, xf)
    bed = np.zeros(n + len(room))
    pos = 0
    while pos < n:
        bed[pos:pos + len(room)] += room * win
        pos += len(room) - xf
    bed = bed[:n]
    tt = np.arange(n) / RATE
    duck = 1 - 0.45 * np.clip(np.minimum((tt - 34.0) / 0.6, (40.0 - tt) / 0.6), 0, 1)  # near silence on the reveal
    fade = np.clip(np.minimum(tt / 1.0, (SECONDS - tt) / 2.0), 0, 1)
    bed = bed * duck * fade
    mix.L[:n] += bed
    mix.R[:n] += bed
    # per-shot foraged effects stems (paper tick per moving exposure, thud, bell at 0:08, switch)
    for name, shot in (("shot1", 1), ("shot2", 2), ("shot3", 3), ("shot5", 5), ("shot7", 7), ("shot8", 8)):
        st = read_wav(os.path.join(SND, f"shot-{shot}-fx.wav"))
        i = int(STARTS[name] * RATE)
        m = min(len(st), n - i)
        mix.L[i:i + m] += st[:m, 0]
        mix.R[i:i + m] += st[:m, 1]
    # the second station-bell strike, on "OH? REALLY?" (shot 6 exposure 72 = 0:40)
    bell = read_wav(os.path.join(SND, "bell-strike.wav"))[:, 0]
    mix.add(bell, STARTS["shot6"] + 72 / XPS, 0.6, pan=0.25)
    # keep the stems' relative levels: scale the whole bed so kit's master leaves it as is
    pk = max(np.abs(mix.L).max(), np.abs(mix.R).max())
    mix.L *= 0.8 / pk
    mix.R *= 0.8 / pk


if __name__ == "__main__":
    film.render()
