"""boucle-la TEST SHOT film: H (film 26.0-31.0 s) then B' (film 45.5-50.5 s), 10.0 s, 960x540, 24 fps.

local 0.00-0.58  H: heads swing in (drawings on 2s)             film 26.0
local 1.00-2.00  the note turns back->face over 6 note drawings  film 27.0-28.0 (other pieces on 2s)
local 2.00       face-out drawing: ground cuts to spot black, the only bell   film 28.0
local 2.50       Gustave's balloon + voice grain                film 28.5
local 2.5-5.0    she recoils, settles; slow push toward the note
local 5.0-5.5    camera slides down to row 3, B'  (time elided: C' 39-45.5 s is skipped in this test)
local 5.5-7.0    B' plays the identical exposure sheet of B    film 45.5-47.0
local 7.0-10.0   B' holds its page drawing
Run: python3 -I film.py [--stills t ...]
"""
import json
import math
import os
import sys
import wave

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shot  # noqa: E402
from shot import SEQ, CANON, H_SHEET, B_SHEET, FACE_OUT_DRAWING, H_BALLOON_DRAWING, B_BALLOON_DRAWING  # noqa: E402

from pathlib import Path  # noqa: E402
import kit  # noqa: E402  (films/kit.py, via shot's sys.path)

FPS = 24
SECONDS = 10.0
MEDIA = shot.MEDIA
AUD = os.path.join(MEDIA, "audio")
T_H0 = 0.0     # H exposure sheet starts (film 26.0)
T_B0 = 5.5     # B' exposure sheet starts (film 45.5)
F_FACE = int(round(T_H0 * FPS)) + 2 * FACE_OUT_DRAWING      # frame of the face-out drawing
F_B0 = int(round(T_B0 * FPS))


def sheet_at(sheet, f0, k):
    d = (k - f0) // 2  # on 2s
    if d < 0:
        return None, -1
    return sheet[min(d, len(sheet) - 1)], d


def state_at(k):
    st = {}
    for i in range(7):
        key = SEQ[i]
        st[i] = (CANON[key], key == "H", i > 3, True)  # rows 1, 2 inked; row 3 waits as a ghost
    pose, d = sheet_at(H_SHEET, int(T_H0 * FPS), k)
    st[3] = (pose, d >= FACE_OUT_DRAWING, False, d >= H_BALLOON_DRAWING)
    if k >= F_B0:
        pose, d = sheet_at(B_SHEET, F_B0, k)
        st[5] = (pose, False, False, d >= B_BALLOON_DRAWING)
    return st


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


CAM_H0 = (1795.0, 905.0, 1240.0)    # centre x, centre y, window width (page px)
CAM_H1 = (1835.0, 912.0, 1210.0)    # pushed toward the note face
CAM_B = (1865.0, 1468.0, 1080.0)    # B' in row 3


def cam_at(t):
    if t < 2.5:
        return CAM_H0
    if t < 5.0:
        x = ease((t - 2.5) / 2.5)
        return tuple(a + (b - a) * x for a, b in zip(CAM_H0, CAM_H1))
    x = ease((t - 5.0) / 0.5)
    return tuple(a + (b - a) * x for a, b in zip(CAM_H1, CAM_B))


_page_cache = {}


def page_at(k):
    st = state_at(k)
    key = json.dumps({i: [st[i][0], st[i][1], st[i][2], st[i][3]] for i in st}, sort_keys=True)
    if key not in _page_cache:
        _page_cache.clear()
        _page_cache[key] = shot.compose(st)
    return _page_cache[key]


def frame_img(k):
    t = k / FPS
    page = page_at(k)
    cx, cy, w = cam_at(t)
    h = w * 9 / 16
    s = 960.0 / w
    M = np.float32([[s, 0, 480 - cx * s], [0, s, 270 - cy * s]])
    out = cv2.warpAffine(page, M, (960, 540), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC, borderValue=shot.PAGE)
    g = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([g, g, g]), "RGB")


# ---------------------------------------------------------------- sound
def read_wav(p):
    w = wave.open(p)
    n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
    x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    assert sr == 44100, p
    return x


def onset(x, t0, t1, thr_db=-32):
    hop = 441
    for i in range(int(t0 * 44100), int(t1 * 44100), hop):
        if 20 * math.log10(np.sqrt((x[i:i + hop] ** 2).mean()) + 1e-9) > thr_db:
            return i
    return int(t0 * 44100)


def grain(x, a, b, fade=0.03):
    g = x[a:b].copy()
    f = int(fade * 44100)
    g[:f] *= np.linspace(0, 1, f)
    g[-f:] *= np.linspace(1, 0, f)
    return g


def band(mix, x, lo, hi):
    return mix.band(x, lo, hi)


SOUND = {}


def sound(mix):
    voice = read_wav(os.path.join(AUD, "working-together.wav"))
    # Gustave's two grains: one real man's speech (1951 industrial film), muffled to a murmur through the page
    a = onset(voice, 11.05, 11.4)
    gH = grain(voice, a, a + int(2.15 * 44100))
    b = onset(voice, 15.6, 15.95)
    gB = grain(voice, b, b + int(1.55 * 44100))
    for g, at, nm in ((gH, 2.5, "H"), (gB, T_B0 + 2 * B_BALLOON_DRAWING / FPS, "B")):
        y = band(mix, g, 160, 1700)
        y = y / (np.abs(y).max() + 1e-9) * 0.5
        mix.add(y, at, gain=1.0)
        SOUND[nm] = {"start_s": round(at, 4), "src_in_s": round((a if nm == "H" else b) / 44100, 3),
                     "dur_s": round(len(g) / 44100, 3)}
    # the turn: a paper rustle (foraged if it arrived, else nothing)
    rp = os.path.join(AUD, "paper.wav")
    if os.path.exists(rp):
        r = read_wav(rp)
        i = onset(r, SOUND.get("rustle_in", 0.0), len(r) / 44100 - 1)
        mix.add(grain(r, i, i + int(0.9 * 44100), 0.05) / (np.abs(r[i:i + 40000]).max() + 1e-9) * 0.22, 1.0)
        SOUND["rustle"] = {"start_s": 1.0, "src_in_s": round(i / 44100, 3)}
    # the only bell, on the face-out frame
    bp = os.path.join(AUD, "bell.wav")
    t_bell = F_FACE / FPS
    if os.path.exists(bp):
        bl = read_wav(bp)
        i = onset(bl, 0.0, len(bl) / 44100 - 1, thr_db=-30)
        # back up to the true attack: the first sample above 30 % of the strike's peak
        seg = bl[i:i + 8820]
        j = i + int(np.argmax(np.abs(seg) > 0.3 * np.abs(seg).max()))
        g = bl[j:j + int(4.5 * 44100)].copy()
        g[-4410:] *= np.linspace(1, 0, 4410)
        mix.add(g / (np.abs(g).max() + 1e-9) * 0.9, t_bell)
        SOUND["bell"] = {"start_s": t_bell, "src_in_s": round(j / 44100, 4), "kind": "foraged"}
    else:
        mix.bell(t_bell, freq=1320, seconds=3.5, gain=0.5)
        SOUND["bell"] = {"start_s": t_bell, "kind": "SYNTHESIZED kit.Mix.bell fallback (foraged bell not downloaded)"}


def main():
    film = kit.Film("test-shot", SECONDS)

    def pic(t, ink):
        ink._grain = False  # no added grain: the only texture is Daumier's crayon and the pen
        ink.img = frame_img(int(round(t * FPS))).convert("RGB")

    film.picture(pic)
    film.sound(sound)
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = Path(HERE) / "stills"
        out.mkdir(exist_ok=True)
        for t in [float(x) for x in sys.argv[2:]]:
            frame_img(int(round(t * FPS))).save(out / f"{t:05.2f}.png")
        return
    film.render(out_dir=Path(shot.SWARM))
    json.dump({"face_out_frame": F_FACE, "face_out_s": F_FACE / FPS, "sound": SOUND, "fps": FPS},
              open(os.path.join(HERE, "timing.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
