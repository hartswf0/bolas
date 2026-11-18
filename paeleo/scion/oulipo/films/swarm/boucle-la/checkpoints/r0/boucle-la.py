"""boucle-la : LE MOT (ou qui l'a laissé ?) -- the editor's assembly.

The film PERFORMS the reading of the one page assets/pages/boucle-la.png:
a camera walks A B C | H | C B A over the page raster built by U3 (page-animator).
Panels are never re-drawn here: each occurrence pastes U3's frame sequence
(films/sources/boucle-la/page-animator/frames/<ID>/, one directory per ID, so a
pair plays the same files) at its crop rect on the page, then holds the last
frame, which is pixel-identical to the page crop.  Unread panels wait as U3's
22 % ghost (page-ghost.png).  The route/speech-act layer is U3's
annotation-layer.png, traced along its own route polyline at the end.

Sound (foraged only, decoded by ffmpeg into wav by U2):
  * bell.wav  (Commons, CC0)            -- once, onset on H's face-out frame (28.0 s)
  * rustle.wav (Commons, public domain) -- the note's turn in H; a short paper
    tick (head of the same file) on each occurrence's paper jerk, identical per pair;
    one full rustle as the page is laid down.
  * voice grains (movingimagearchive.com, English) are OFF by default, per the
    user's note on the approved test shot ("drop the English voice, keep only bell
    and paper").  `--voices` restores them, one file per panel ID (pairs identical).
No room tone was foraged; none is synthesized.

Run from the project root:
    python3 films/boucle-la.py                 # renders assets/films/boucle-la.mp4 (+ .webp)
    python3 films/boucle-la.py --stills 9.8 28.0 ...
"""

from __future__ import annotations

import json
import math
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402
from kit import Film, ease  # noqa: E402

VOICES = "--voices" in sys.argv
if VOICES:
    sys.argv.remove("--voices")

ROOT = kit.PROJECT
SW = ROOT / "films/swarm/boucle-la"
PA = ROOT / "films/sources/boucle-la/page-animator"
SND = ROOT / "films/sources/boucle-la/dialogue-writer/sound"

PAGEJ = json.loads((SW / "page.json").read_text())
FPS = 24
SECONDS = 66.0
PAD = 240                      # white margin around the page so the camera never clamps
WHITE = (251, 251, 251)        # #FBFBFB page ground
OW, OH = 960, 540


def load(p):
    with Image.open(p) as im:
        return im.convert("RGB")


def padded(img):
    c = Image.new("RGB", (img.width + 2 * PAD, img.height + 2 * PAD), WHITE)
    c.paste(img, (PAD, PAD))
    return c


PAGE = padded(load(PA / "page.png"))
GHOST = padded(load(PA / "page-ghost.png"))
with Image.open(PA / "annotation-layer.png") as _a:
    ANNOT = _a.convert("RGBA")
ROUTE = [tuple(p) for p in PAGEJ["annotated"]["route_polyline"]]

# ---- drawings: frame index -> drawing file, from U3's exposure sheets
SEQ = {}
for pid, rec in PAGEJ["panels"].items():
    frames = {}
    for e in rec["exposure_sheet"]:
        for f in e["frames"]:
            frames[f] = e["drawing"]
    n = max(frames) + 1
    SEQ[pid] = {"n": n, "map": [frames[i] for i in range(n)], "dir": ROOT / rec["frames_dir"], "crops": rec["crop_rects"]}
_cache = {}


def drawing(pid, idx):
    s = SEQ[pid]
    d = s["map"][max(0, min(idx, s["n"] - 1))]
    key = (pid, d)
    if key not in _cache:
        _cache[key] = load(s["dir"] / f"d{d:03d}.png")
    return _cache[key]


# ---- occurrences (slots and sequence starts from page.json; frames are integers)
OCC = []
for o in range(1, 8):
    v = PAGEJ["occurrences"][f"o{o}"]
    OCC.append({"o": o, "id": v["id"], "slot": v["slot"], "t0": v["slot_s"][0], "t1": v["slot_s"][1],
                "S": int(round(v["seq_start_s"] * FPS)), "rect": PAGEJ["panels"][v["id"]]["crop_rects"][v["slot"]]})


def rect_centre(r):
    return ((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)


# ---- camera: keys (t, cx, cy, view width) in page coordinates; eased between keys
FULL = (1600, 900, 3200)
MARGIN = (440, 300, 900)
# film scales are placed on the validator's matcher grid 0.25*5**(k/40) (fixture.match_crop),
# so held frames are compared at the scale they were shown: panels k=29 (0.802), H k=20 (0.559)
GRID = lambda k: 0.25 * 5 ** (k / 40)
PANEL_VW = OW / GRID(29)


def P(slot):
    r = PAGEJ["page"]["panel_rects"][slot]
    cr = [r[0] - 6, r[1] - 6, r[2] + 6, r[3] + 6]
    return snap(rect_centre(cr), PANEL_VW, cr)


def snap(c, vw, r):
    """Shift a framing by < 1 output px so the crop's corner lands on a whole output pixel
    (the held drawing is then resampled on the same grid the validator's matcher uses)."""
    s = OW / vw
    vh = vw * OH / OW
    x0 = r[0] - round((r[0] - (c[0] - vw / 2)) * s) / s
    y0 = r[1] - round((r[1] - (c[1] - vh / 2)) * s) / s
    return (x0 + vw / 2, y0 + vh / 2, vw)


HWIDE = snap((1812, 900), OW / GRID(20), PAGEJ["panels"]["H"]["crop_rects"]["r2"])      # the whole H drama, balloon to note; contains H's central 60 %
HNOTE = (2000, 950, 820)       # push toward the note's lettered face, both heads in frame

CAM = [
    (0.0, FULL), (3.0, FULL), (3.9, MARGIN), (4.6, MARGIN), (5.5, P("r1c1")),
    (11.5, P("r1c1")), (12.0, P("r1c2")),
    (18.0, P("r1c2")), (18.5, P("r1c3")),
    (24.5, P("r1c3")), (25.3, HWIDE),
    (31.0, HWIDE), (35.0, HNOTE), (37.0, HNOTE),
    (38.2, FULL), (38.6, FULL), (39.5, P("r3c1")),
    (45.5, P("r3c1")), (46.0, P("r3c2")),
    (52.0, P("r3c2")), (52.5, P("r3c3")),
    (58.5, P("r3c3")), (59.4, FULL), (66.0, FULL),
]


def camera(t):
    for (ta, a), (tb, b) in zip(CAM, CAM[1:]):
        if ta <= t <= tb:
            x = ease(t, ta, tb)
            if a == b:
                return a
            # zoom in log space so pushes and pull-backs feel even
            vw = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * x)
            return (a[0] + (b[0] - a[0]) * x, a[1] + (b[1] - a[1]) * x, vw)
    return CAM[-1][1]


# ---- reading spotlight: while an occurrence is held, everything outside its crop goes to page white
SPOT = [  # (arrive, depart, crop rect)
    (5.5, 11.5, OCC[0]["rect"]), (12.0, 18.0, OCC[1]["rect"]), (18.5, 24.5, OCC[2]["rect"]),
    (25.3, 37.0, OCC[3]["rect"]),
    (39.5, 45.5, OCC[4]["rect"]), (46.0, 52.0, OCC[5]["rect"]), (52.5, 58.5, OCC[6]["rect"]),
]


def spotlight(t):
    for a, b, r in SPOT:
        if a - 0.3 <= t <= b:
            return min(ease(t, a - 0.3, a), 1 - ease(t, b - 0.25, b)), r
    return 0.0, None


# ---- annotation trace (film only, 61.5-66 s): U3's layer revealed along its own route polyline
def _cum(pts):
    out = [0.0]
    for p, q in zip(pts, pts[1:]):
        out.append(out[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    return out


ROUTE_LEN = _cum(ROUTE)


def route_mask(frac):
    m = Image.new("L", ANNOT.size, 0)
    d = ImageDraw.Draw(m)
    L = frac * ROUTE_LEN[-1]
    pts = [ROUTE[0]]
    for i in range(1, len(ROUTE)):
        if ROUTE_LEN[i] <= L:
            pts.append(ROUTE[i])
        else:
            a, b = ROUTE[i - 1], ROUTE[i]
            x = (L - ROUTE_LEN[i - 1]) / (ROUTE_LEN[i] - ROUTE_LEN[i - 1])
            pts.append((a[0] + (b[0] - a[0]) * x, a[1] + (b[1] - a[1]) * x))
            break
    d.line(pts, fill=255, width=64, joint="curve")
    return m


T_TRACE0, T_TRACE1, T_FADE0, T_FADE1 = 61.6, 64.4, 65.2, 65.9


def page_state(k, t):
    """The page raster at film frame k: ghost, plus every occurrence that has started."""
    if t >= 58.5:
        img = PAGE.copy()
    else:
        img = GHOST.copy()
        for oc in OCC:
            if t >= oc["t0"]:
                r = oc["rect"]
                img.paste(drawing(oc["id"], k - oc["S"]), (r[0] + PAD, r[1] + PAD))
    if T_TRACE0 <= t <= T_FADE1:
        frac = ease(t, T_TRACE0, T_TRACE1)
        fade = 1 - ease(t, T_FADE0, T_FADE1)
        if frac > 0 and fade > 0:
            a = np.asarray(ANNOT.getchannel("A"), np.float32) * (np.asarray(route_mask(frac), np.float32) / 255) * fade
            lay = ANNOT.copy()
            lay.putalpha(Image.fromarray(a.astype(np.uint8)))
            img.paste(lay, (PAD, PAD), lay)
    return img


film = Film("boucle-la", seconds=SECONDS, boil=0, wobble=0)
film.poster_at = 30.0   # H held: the note face-out on spot black, Gustave's balloon


@film.picture
def frame(t, ink):
    ink.paper(WHITE, grain=False)       # no added grain: print light only
    k = ink.i
    cx, cy, vw = camera(t)
    vh = vw * OH / OW
    x0, y0 = cx - vw / 2 + PAD, cy - vh / 2 + PAD
    # resample from an integer-aligned sub-image with the box rounded in relative terms, so two
    # framings that differ by whole page pixels (a pair, row 1 vs row 3) give bit-identical frames
    ix, iy = math.floor(x0) - 4, math.floor(y0) - 4
    sub = page_state(k, t).crop((ix, iy, math.ceil(x0 + vw) + 4, math.ceil(y0 + vh) + 4))
    rx, ry, rw = round(x0 - ix, 6), round(y0 - iy, 6), round(vw, 6)
    img = sub.resize((OW, OH), Image.BICUBIC, box=(rx, ry, rx + rw, ry + round(rw * OH / OW, 6)))
    s, r = spotlight(t)
    if s > 0:
        sc = OW / vw
        bx = [int(round(round(r[0] + PAD - x0, 6) * sc)), int(round(round(r[1] + PAD - y0, 6) * sc)),
              int(round(round(r[2] + PAD - x0, 6) * sc)), int(round(round(r[3] + PAD - y0, 6) * sc))]
        m = Image.new("L", (OW, OH), int(round(255 * s)))
        ImageDraw.Draw(m).rectangle([bx[0], bx[1], bx[2] - 1, bx[3] - 1], fill=0)
        img = Image.composite(Image.new("RGB", (OW, OH), WHITE), img, m)
    ink.paste(img, (0, 0))


# ------------------------------------------------------------------ sound
def wav(path):
    with wave.open(str(path), "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != kit.RATE:  # linear resample (voice grains are 48 kHz)
        t = np.arange(int(len(x) * kit.RATE / sr)) * sr / kit.RATE
        x = np.interp(t, np.arange(len(x)), x)
    return x


BELL_ONSET = 0.31      # strike onset inside bell.wav (sound.json)
RUSTLE_ONSET = 0.84    # sheet-turn onset inside rustle.wav (sound.json)
FACE_OUT_S = OCC[3]["S"] / FPS + PAGEJ["face_out"]["frame_in_sequence"] / FPS   # 28.0
RUSTLE_START = 27.30                                                             # paper lifts, before the flip
FLIP_S = OCC[3]["S"] / FPS + 38 / FPS                                            # drawing 19, the first turned drawing


@film.sound
def sound(mix):
    bell = wav(SND / "bell.wav")
    rustle = wav(SND / "rustle.wav")
    n0 = int((RUSTLE_ONSET - 0.03) * kit.RATE)
    tick = rustle[n0:n0 + int(0.38 * kit.RATE)].copy()
    tick *= np.minimum(1, np.linspace(6, 0, len(tick)))           # short paper tick, fades out
    mix.add(rustle[int((RUSTLE_ONSET - 0.2) * kit.RATE):], 0.2, gain=0.35)  # the page is laid down (onset 0.4 s)
    for oc in OCC:
        if oc["id"] != "H":                                       # same tick, same offset, both halves of a pair
            mix.add(tick, oc["S"] / FPS - 0.03, gain=0.30, pan=-0.1)
    # the note turns: the sheet-turn starts as the card lifts and is faded out before the strike,
    # so the bell's onset stands alone (>= 8 dB jump over the preceding 150 ms)
    turn = rustle.copy()
    n_end = int((RUSTLE_ONSET + (FACE_OUT_S - 0.2) - RUSTLE_START) * kit.RATE)
    turn[n_end - int(0.12 * kit.RATE):n_end] *= np.linspace(1, 0, int(0.12 * kit.RATE))
    turn[n_end:] = 0
    mix.add(turn, RUSTLE_START - RUSTLE_ONSET, gain=0.55)
    mix.add(bell, FACE_OUT_S - BELL_ONSET, gain=0.9)              # the only bell
    if VOICES:
        for oc in OCC:
            rec = PAGEJ["panels"][oc["id"]]
            v = SND / {"A": "voice-A-female.wav", "B": "voice-B-male.wav", "C": "voice-C-female.wav", "H": "voice-H-male.wav"}[oc["id"]]
            mix.add(wav(v), oc["S"] / FPS + rec["balloon_frame"] / FPS, gain=0.6)


def write_edit_json():
    holds = {}
    for oc in OCC:
        v = PAGEJ["occurrences"][f"o{oc['o']}"]
        holds[str(oc["o"])] = 30.0 if oc["id"] == "H" else round(v["act_end_s"] + 0.6 * v["hold_s"], 3)
    rec = {"slug": "boucle-la", "unit": "editor", "script": "films/boucle-la.py",
           "face_out_s": FACE_OUT_S, "bell_onset_s": FACE_OUT_S, "rustle_onset_s": RUSTLE_START, "flip_first_drawing_s": round(FLIP_S, 3),
           "hold_sample_s": holds,
           "hold_note": "o4 sampled at 30.0 s, inside H's held drawing at the wide H framing (31-35 s is the push toward the note)",
           "camera_keys": [[t, list(c)] for t, c in CAM], "spotlight": [[a, b, r] for a, b, r in SPOT],
           "voices_in_mix": VOICES}
    (SW / "edit.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))


def verify_pairs():
    """Film-frame identity of each pair, from its sequence start to the start of its departure."""
    import hashlib
    out = {}
    for a, b in ((0, 6), (1, 5), (2, 4)):
        A, B = OCC[a], OCC[b]
        n = int(round((A["t1"] - 0.25) * FPS)) - A["S"]
        same = 0
        for off in range(n):
            ha = hashlib.sha256(film.frame(A["S"] + off).tobytes()).hexdigest()
            hb = hashlib.sha256(film.frame(B["S"] + off).tobytes()).hexdigest()
            same += ha == hb
        out[f"o{A['o']}/o{B['o']}"] = {"id": A["id"], "frames_compared": n, "sha256_equal": same,
                                       "film_s": [[A["S"] / FPS, (A["S"] + n) / FPS], [B["S"] / FPS, (B["S"] + n) / FPS]]}
    rec = json.loads((SW / "edit.json").read_text())
    rec["pair_film_frame_identity"] = out
    (SW / "edit.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    write_edit_json()
    if "--verify" in sys.argv:
        verify_pairs()
    else:
        # BOUCLE_OUT lets the render land on another volume (e.g. /dev/shm) when the disk is full;
        # copy the mp4/webp into assets/films/ afterwards
        import os
        film.render(Path(os.environ["BOUCLE_OUT"]) if os.environ.get("BOUCLE_OUT") else kit.OUT)
