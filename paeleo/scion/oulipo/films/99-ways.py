"""99 ways: the book leafed through, page by page (film editor).

Picture (960x1242, the page proportion): a dark table (handmade: painted ground, lamp falloff, in code) with
the book lying on it. For every page, in order 01..99:
  * a page turn: the previous leaf is lifted at its outer bottom corner and rolled over a paper cylinder
    toward the spine (left), its back (blank LoC 1934 sheet with the page showing faintly through) coming
    up, the next page uncovered beneath it, a contact shadow under the roll. Real curl geometry
    (cylinder projection, cv2.remap), not a dissolve;
  * a hold on the whole page (assets/pages/99-ways/NN-<id>.jpg);
  * its key beat, played from films/sources/99-ways/beats/NN/b01..bNN.png frame by frame on twos,
    the last state held a moment; the next turn lifts what is on screen.
Front: the title page (films/sources/99-ways/book/title.png, made by films/swarm/99-ways/kit/build_book.py);
back: the end leaf. Page 01 and a few highlights hold longer.

Sound: a station room tone bed (99-ways-template stem room_tone.wav: Panama by Air (Reel 4), 1914, noise floor
of the print's sound transfer) and one paper-turn per turn, cut from Commons 'Book paper pages assorted.ogg'
(stephan, public domain), decoded with ffmpeg only, onsets picked from its energy envelope.

Run:  python3 films/99-ways.py            (writes assets/films/99-ways.mp4 + .webp)
      python3 films/99-ways.py --stills t1 t2 ...
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from kit import Film  # noqa: E402

SLUG = "99-ways"
FPS = 24
FW, FH = 960, 1242
PW, PH = 880, 1140                         # the page on the table (2200x2850 scaled 0.4)
PX, PY = (FW - PW) // 2 - 6, (FH - PH) // 2 - 4
PAGES = ROOT / "films" / "swarm" / SLUG / "pages"
JPG = ROOT / "assets" / "pages" / SLUG
SRC = ROOT / "films" / "sources" / SLUG
BEATS = SRC / "beats"
BOOK = SRC / "book"
ROOM = ROOT / "films" / "swarm" / "99-ways-template" / "anim" / "sound" / "room_tone.wav"
PAPER_OGG = SRC / "sound" / "Book_paper_pages_assorted.ogg"

RECS = [json.load(open(PAGES / f"{n:02d}.json")) for n in range(1, 100)]
HIGHLIGHT = {36: 22, 46: 18, 50: 18, 72: 20, 81: 18, 99: 24}   # page -> hold frames (default HOLD)
TURN, HOLD, LAST = 10, 10, 5                                   # frames: turn, page hold, last beat state
TITLE_HOLD, P01_HOLD, P01_LAST, END_HOLD = 44, 40, 18, 40


# ------------------------------------------------------------------ the table (handmade)
def make_table():
    rs = np.random.RandomState(99)
    y, x = np.mgrid[0:FH, 0:FW].astype(np.float32)
    streak = cv2.resize(rs.normal(0, 1, (FH // 6, 6)).astype(np.float32), (FW, FH), interpolation=cv2.INTER_CUBIC)
    fine = cv2.GaussianBlur(rs.normal(0, 1, (FH, FW)).astype(np.float32), (0, 0), 1.2)
    r = np.hypot((x - FW * 0.48) / (FW * 0.75), (y - FH * 0.42) / (FH * 0.8))
    lamp = np.clip(1.15 - 0.75 * r ** 1.4, 0.35, 1.15)
    base = np.array([40, 33, 28], np.float32)
    t = base[None, None] * (lamp[..., None]) * (1 + 0.06 * streak[..., None] + 0.03 * fine[..., None])
    # the book's shadow on the table (soft, lamp above and slightly right)
    sh = np.zeros((FH, FW), np.float32)
    cv2.rectangle(sh, (PX + 4, PY + 10), (PX + PW + 14, PY + PH + 18), 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 14)
    t *= (1 - 0.6 * sh[..., None])
    return np.clip(t, 0, 255)


TABLE = make_table()
EDGE = np.array([214, 206, 190], np.float32)


def base_frame(remaining):
    """Table + the stack of leaves still to turn, seen as thin edges right and below the page."""
    f = TABLE.copy()
    depth = int(round(1 + 6 * remaining / 101))
    for k in range(depth, 0, -1):
        tone = EDGE * (0.82 + 0.03 * ((k * 7) % 4)) * (0.92 - 0.02 * k)
        f[PY + k * 1 + 1:PY + PH + k * 1 + 1, PX + k + 1:PX + PW + k + 1] = tone
        f[PY + PH + k - 1, PX + k:PX + PW + k] *= 0.8
    return f


# ------------------------------------------------------------------ leaves
_cache = {}


def leaf(key):
    """key: ('page', n) | ('beat', n, i) | ('book', name) -> float32 PH x PW x 3."""
    if key in _cache:
        return _cache[key]
    if len(_cache) > 40:
        _cache.clear()
    if key[0] == "page":
        p = RECS[key[1] - 1]
        im = Image.open(JPG / f"{key[1]:02d}-{p['id']}.jpg")
    elif key[0] == "beat":
        im = Image.open(BEATS / f"{key[1]:02d}" / f"b{key[2]:02d}.png")
    else:
        im = Image.open(BOOK / f"{key[1]}.png")
    a = np.asarray(im.convert("RGB").resize((PW, PH), Image.LANCZOS), np.float32)
    _cache[key] = a
    return a


def _verso():
    im = Image.open(BOOK / "end.png").convert("RGB")
    a = np.asarray(im, np.float32)
    # blank leaf back: the sheet ground without the end lettering (take the lower band, re-tile)
    band = a[1900:2700]
    a = np.concatenate([band, band[::-1], band, band[::-1]], 0)[:2850]
    return np.asarray(Image.fromarray(a.astype(np.uint8)).resize((PW, PH), Image.LANCZOS), np.float32)


VERSO = _verso()


def flat(img, remaining):
    f = base_frame(remaining)
    f[PY:PY + PH, PX:PX + PW] = img
    return f


# ------------------------------------------------------------------ the turn (cylinder curl)
GX, GY = np.meshgrid(np.arange(FW, dtype=np.float32) - PX, np.arange(FH, dtype=np.float32) - PY)
NV = np.array([1.0, 0.42], np.float32)
NV /= np.linalg.norm(NV)
PROJ = GX * NV[0] + GY * NV[1]                         # page-local coordinate along the lift direction
PMAX = PW * NV[0] + PH * NV[1]


def _sample(img, qx, qy):
    m = cv2.remap(img, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    inside = cv2.remap(np.ones((PH, PW), np.float32), qx, qy, cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return m, inside


def turn(top, under, u, remaining):
    """Leaf `top` (PHxPW) lifted off `under` at progress u in [0,1]."""
    f = flat(under, remaining)
    e = u * u * (3 - 2 * u)
    r = 34 + 110 * e
    A = PMAX + 8 - (PMAX + 8 + math.pi * r * 0.5 + 140) * e      # axis travels from the corner past the spine
    d = PROJ - A
    # contact shadow on what lies beneath, just ahead of the roll
    ahead = np.clip((d - r) / 70.0, 0, 1)
    shade = np.where(d > 0, 1 - 0.45 * (1 - ahead) ** 2, 1.0).astype(np.float32)
    f *= shade[..., None]
    # 1. flat unturned part of the leaf
    unt = (d < 0)
    m, ins = _sample(top, GX, GY)
    w = (ins * unt).astype(np.float32)[..., None]
    f = f * (1 - w) + m * w
    # 2. underside of the roll (recto, curving away)
    dc = np.clip(d, 0, r)
    on_cyl = (d >= 0) & (d <= r)
    th = np.arcsin(dc / r)
    s1 = r * th
    qx, qy = GX + (s1 - d) * NV[0], GY + (s1 - d) * NV[1]
    m, ins = _sample(top, qx.astype(np.float32), qy.astype(np.float32))
    light = (0.98 - 0.35 * (dc / r) ** 2)[..., None]
    w = (ins * on_cyl).astype(np.float32)[..., None]
    f = f * (1 - w) + m * light * w
    # 3. the back of the leaf coming over (verso: blank sheet, page faint through it)
    s2 = np.where(d >= 0, r * (math.pi - th), math.pi * r - d)
    qx, qy = (GX + (s2 - d) * NV[0]).astype(np.float32), (GY + (s2 - d) * NV[1]).astype(np.float32)
    back = (d <= r)
    vm, ins = _sample(VERSO, qx, qy)
    ghost, _ = _sample(top, qx, qy)
    vb = vm * 0.93 + ghost * 0.07
    vl = np.where(d >= 0, 0.72 + 0.26 * np.sin(th), 0.97 - 0.05 * np.clip(-d / 600, 0, 1))[..., None]
    w = (ins * back).astype(np.float32)[..., None]
    f = f * (1 - w) + vb * vl * w
    return f


# ------------------------------------------------------------------ the timeline
def beat_files(n):
    return sorted((BEATS / f"{n:02d}").glob("b[0-9][0-9].png"))


SEQ = []          # per frame: ("flat", key, remaining) | ("turn", top_key, under_key, u, remaining)
TURNS = []        # frame indices where a turn starts (for the foley)


def hold(key, frames, remaining):
    SEQ.extend([("flat", key, remaining)] * frames)


def do_turn(top, under, remaining):
    TURNS.append(len(SEQ))
    for i in range(TURN):
        SEQ.append(("turn", top, under, (i + 1) / (TURN + 1), remaining))


hold(("book", "title"), TITLE_HOLD, 100)
prev = ("book", "title")
PAGE_START = {}
for p in RECS:
    n = p["n"]
    rem = 99 - n
    do_turn(prev, ("page", n), rem)
    PAGE_START[n] = len(SEQ)
    hold(("page", n), P01_HOLD if n == 1 else HIGHLIGHT.get(n, HOLD), rem)
    bs = beat_files(n)
    assert 4 <= len(bs) <= 8, (n, len(bs))
    for i in range(1, len(bs) + 1):
        hold(("beat", n, i), 2, rem)
    hold(("beat", n, len(bs)), P01_LAST if n == 1 else LAST, rem)
    prev = ("beat", n, len(bs))
do_turn(prev, ("book", "end"), 0)
hold(("book", "end"), END_HOLD, 0)

SECONDS = len(SEQ) / FPS
_flat_cache = {}


def picture(t, ink):
    k = min(int(round(t * FPS)), len(SEQ) - 1)
    s = SEQ[k]
    if s[0] == "flat":
        ck = (s[1], s[2])
        if ck not in _flat_cache:
            _flat_cache.clear()
            _flat_cache[ck] = Image.fromarray(np.clip(flat(leaf(s[1]), s[2]), 0, 255).astype(np.uint8))
        img = _flat_cache[ck]
    else:
        _, top, under, u, rem = s
        img = Image.fromarray(np.clip(turn(leaf(top), leaf(under), u, rem), 0, 255).astype(np.uint8))
    ink._grain = False
    ink.img = img.copy()


# ------------------------------------------------------------------ sound
def read_wav(path):
    with wave.open(str(path)) as wf:
        x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float64) / 32768
        if wf.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x


def paper_grains():
    """Single page-turn gestures cut from the Commons recording (decoded by ffmpeg, never executed)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(PAPER_OGG), "-ac", "1", "-ar", "44100",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    hop = 441
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(e + 1e-9)
    grains, last = [], -100
    for i in range(400, 4000):                       # 4-40 s: the single, separated handlings
        if db[i] > -28 and db[i - 3:i].max() < -30 and i - last > 60:
            a = max(0, (i - 6) * hop)
            g = x[a:a + int(0.55 * 44100)].copy()
            g = g - np.convolve(g, np.ones(64) / 64, "same")          # moving-average subtracted: a gentle high-pass that takes out the handling rumble
            n = len(g)
            g[:441] *= np.linspace(0, 1, 441)
            g[-6615:] *= np.linspace(1, 0, 6615) ** 2
            g *= 0.27 / (np.abs(g).max() + 1e-9)
            grains.append(g)
            last = i
    return grains


def sound(mix):
    room = read_wav(ROOM)
    n = mix.n
    bed = np.tile(room, n // len(room) + 1)[:n]
    mix.add(bed, 0.0, 1.0)
    grains = paper_grains()
    assert len(grains) >= 4, len(grains)
    for j, k in enumerate(TURNS):
        g = grains[(j * 5) % len(grains)]
        mix.add(g, k / FPS + 0.02, 0.85 + 0.15 * ((j * 3) % 4) / 3, pan=0.12)


film = Film(SLUG, seconds=SECONDS, size=(FW, FH), boil=0, wobble=0)
film.picture(picture)
film.sound(sound)
film.poster_at = (TURNS[50] + 5) / FPS

if __name__ == "__main__":
    print(f"{len(SEQ)} frames, {SECONDS:.1f} s, {len(TURNS)} turns")
    film.render()
