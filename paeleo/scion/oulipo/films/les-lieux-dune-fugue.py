"""les-lieux-dune-fugue · The Paper Facade (SCION swarm, editor assembly).

A cut-paper tabletop collage. Every visible surface is a scissor-cut paper print of a
public-domain Library of Congress photograph (Carol M. Highsmith: a Columbus courthouse
doorway, a Savannah riveted door, a Sacramento park bench) or of a CC BY-SA Commons street
photo (P02), printed on a foraged 1934 Federal Theatre Project blank sheet and lit by one
simulated tabletop lamp (paper_stage.py, unit U2: SCION 40 tabletop, 44 multiplane, 32 FK hinge).
The voice is captions (voice_score.json, unit U3); sound follows sound_cues.json (U3): one
foraged bell (Murbach, CC BY-SA 3.0), the rest kit.Mix synthesis. 0:44.0-0:57.0 is declared
digital silence: every sample is zero.

Timeline (plan.md sec. 5):
  1  0:00-0:08  P01 prise A matin       (left leaf lifts 18 deg, falls, thud 7.0)
  2  0:08-0:19  P02 carrefour           (multiplane glide; route strip laid 13-15)
  3  0:19-0:28  P03 banc (present)      (8 px truck)
  4  0:28-0:44  P01 prise B soir        (leaves open from 31.0 over ~2.5 s, memory bench behind, close 41-43.5)
  5  0:44-0:52  P03 retour, silence     (shot-3 plate, held)
  6  0:52-0:57  record card             (silence)

Run from the project root:  python3 films/les-lieux-dune-fugue.py  [--stills t ...]
"""
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from kit import Film, RATE, HERE, PROJECT

SLUG = "les-lieux-dune-fugue"
SWARM = HERE / "swarm" / SLUG
sys.path.insert(0, str(SWARM))
import paper_stage as PS  # noqa: E402  (U2 stage module; renders from its bake cache)

VOICE = json.load(open(SWARM / "voice_score.json", encoding="utf-8"))
CUES = json.load(open(SWARM / "sound_cues.json", encoding="utf-8"))
SILENCE_AT = float(CUES["silence"][0]["window"][0])   # 44.0
SECONDS = 57

SHOTS = {s["shot"]: s for s in VOICE["shots"]}
WINDOWS = [(s["shot"], s["screen_time"][0], s["screen_time"][1]) for s in VOICE["shots"]]

_fonts = {}


def ft(path, size):
    k = (path, size)
    if k not in _fonts:
        try:
            _fonts[k] = ImageFont.truetype(path, size)
        except OSError:
            _fonts[k] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    return _fonts[k]


SLATE_FONT = (str(PROJECT / "assets" / "fonts" / "ibm-plex-mono.woff2"), 13)


def shot_at(t):
    for k, a, b in WINDOWS:
        if a <= t < b:
            return k
    return 6


def fade(t, a, b, fi, fo):
    if t < a or t >= b:
        return 0.0
    return min(1.0, (t - a) / max(fi, 1e-6), (b - t) / max(fo, 1e-6))


def text_with_halo(im, xy, s, f, color, alpha, anchor="ms"):
    """cream/muted text with a dark halo for legibility (no box, no band). Repair 1: a wider soft shadow
    (blur 4) under a 1-2 px halo, both passes always, so the captions hold on the pale P02 pavement."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, s, font=f, fill=(10, 8, 6, int(235 * alpha)), anchor=anchor, stroke_width=2,
                             stroke_fill=(10, 8, 6, int(235 * alpha)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4.0)))
    halo = lay.filter(ImageFilter.GaussianBlur(1.6))
    im.alpha_composite(halo)
    im.alpha_composite(halo)
    ImageDraw.Draw(im).text(xy, s, font=f, fill=tuple(color) + (int(255 * alpha),), anchor=anchor)


def overlay(img, shot, t):
    im = img.convert("RGBA")
    # present-tense slate: small muted mono, top left (never on the card). Repair 1: the P03 slates are light
    # with a halo (the park's top left is dark foliage) and the 'silence déclarée' slate is set 1.5x (20 px).
    if shot != 6:
        lab = SHOTS[shot]["label"]
        if shot == 5:
            text_with_halo(im, (16, 14), lab, ft(SLATE_FONT[0], 20), (214, 204, 182), 0.95, anchor="la")
        elif shot == 3:
            text_with_halo(im, (16, 12), lab, ft(*SLATE_FONT), (190, 180, 158), 0.9, anchor="la")
        else:
            ImageDraw.Draw(im).text((16, 12), lab, font=ft(*SLATE_FONT), fill=(168, 156, 134, 230))
        if shot == 1:               # the fiction is labelled during viewing, not only on the 0:52 card
            ImageDraw.Draw(im).text((16, 30), "récit fictif", font=ft(*SLATE_FONT), fill=(168, 156, 134, 200))
    # the voice: captions from voice_score.json (serif italic fr + muted roman en gloss + mono record lines)
    for fr in VOICE["fragments"]:
        a, b = fr["screen_time"]
        L = fr["layout"]
        al = fade(t, a, b, L["fade_in_s"], L["fade_out_s"])
        if al > 0:
            for key, s in (("fr", "« %s »" % fr["text_fr"]), ("en", fr["gloss_en"])):
                sp = L[key]
                text_with_halo(im, (sp["x"], sp["y"]), s, ft(sp["font"], sp["size_px"]), sp["color_rgb"], al * sp["alpha"],
                               sp["anchor"])
        for flag in fr.get("on_screen_flags", []):
            wa, wb = flag["window"]
            fa = fade(t, wa, wb, 0.4, L["fade_out_s"])
            if fa > 0:
                sp = L["record_line"]
                text_with_halo(im, (sp["x"], sp["y"]), flag["text"], ft(sp["font"], sp["size_px"]), sp["color_rgb"],
                               fa * sp["alpha"], sp["anchor"])
    return im.convert("RGB")


def frame_image(t):
    shot = shot_at(t)
    return overlay(PS.render_shot(shot, t, "none", log=False), shot, t)


film = Film(SLUG, SECONDS, size=(960, 720), boil=0, wobble=0)
film.poster_at = 38.5


@film.picture
def picture(t, ink):
    ink._grain = False          # I8: no kit grain, no vignette
    ink.paste(frame_image(t), (0, 0))


# ---------------------------------------------------------------- sound (sound_cues.json)
def read_wav(p):
    with wave.open(str(p)) as w:
        ch, n, r = w.getnchannels(), w.getnframes(), w.getframerate()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768
    assert r == RATE, (p, r)
    return x.reshape(-1, ch).mean(1)


def fades(x, a, b):
    n = len(x)
    e = np.ones(n)
    ia, ib = max(1, int(a * RATE)), max(1, int(b * RATE))
    e[:ia] = np.linspace(0, 1, ia)
    e[n - ib:] = np.linspace(1, 0, ib)
    return x * e


_stems = {}


def stem(cue):
    key = (cue["file"], cue.get("speed") or 1.0)
    if key not in _stems:
        x = read_wav(PROJECT / cue["file"])
        sp = cue.get("speed") or 1.0
        if sp != 1.0:
            x = np.interp(np.arange(0, len(x) - 1, sp), np.arange(len(x)), x)
        _stems[key] = x / max(np.abs(x).max(), 1e-9)
    return _stems[key]


@film.sound
def sound(mix):
    for c in CUES["cues"]:
        x = stem(c)
        n = int(round((c["until"] - c["at"]) * RATE))
        if len(x) < n and c["stem"] in ("present", "junction", "park"):
            x = np.tile(x, int(math.ceil(n / len(x))) + 1)
        x = x[:n].copy()
        fs = c.get("fade_s", [0.01, 0.05])
        x = fades(x, fs[0], fs[1])
        if c.get("duck"):
            tt = c["at"] + np.arange(len(x)) / RATE
            a, b = c["duck"]["window"]
            r = c["duck"]["ramp_s"]
            g = 10 ** (c["duck"]["db"] / 20)
            x *= 1 - (1 - g) * (np.clip((tt - a) / r, 0, 1) * np.clip((b - tt) / r, 0, 1))
        if c.get("spread"):
            for p in c["spread"]:
                mix.add(x, c["at"], c["gain"] * 0.71, p)
        else:
            mix.add(x, c["at"], c["gain"], c["pan"])
    mix.reverb(amount=0.06, size=0.8)       # one small room for the present; applied BEFORE the silence
    i = int(SILENCE_AT * RATE)
    # land every tail on zero 100 ms before the cut (ramp 43.80-43.90): the AAC encoder rings for ~16 ms past
    # the last non-zero sample, so the guard keeps the decoded audio exactly 0 from 44.0 (measured).
    g = int(0.10 * RATE)
    k = int(0.10 * RATE)
    ramp = np.linspace(1, 0, k)
    for ch in (mix.L, mix.R):
        ch[i - g - k:i - g] *= ramp
        ch[i - g:] = 0.0                    # DECLARED DIGITAL SILENCE 44.0-57.0 (master() only scales: zeros stay 0)


FPS_EXPECT = 24
STAGING = SWARM / "render-staging"


def probe_ok(mp4, label):
    """Gate before anything reaches assets/films: duration in [45, 60] s, decoded frame count == SECONDS*24,
    and every decoded audio sample from 44.0 s to the end exactly 0 for >= 6 s. Returns a dict or raises."""
    import subprocess
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_format", "-show_streams", "-of", "json",
                                    str(mp4)], capture_output=True, check=True).stdout)
    dur = float(pr["format"]["duration"])
    v = [st for st in pr["streams"] if st["codec_type"] == "video"][0]
    nfr = int(v.get("nb_read_frames", 0))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "-ar",
                          str(RATE), "-ac", "2", "-"], capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, np.int16).reshape(-1, 2)
    tail = pcm[int(SILENCE_AT * RATE):]
    res = dict(file=str(mp4), duration_s=dur, frames=nfr, frames_expected=int(round(SECONDS * FPS_EXPECT)),
               audio_s=round(len(pcm) / RATE, 3), silence_s=round(len(tail) / RATE, 3),
               silence_all_zero=bool(len(tail) and not np.any(tail)), size_mb=round(mp4.stat().st_size / 1e6, 3))
    ok = (45 <= dur <= 60 and nfr == res["frames_expected"] and res["silence_all_zero"] and res["silence_s"] >= 6.0
          and res["size_mb"] <= 6.0)
    print(f"[gate:{label}]", res, "PASS" if ok else "FAIL", flush=True)
    if not ok:
        raise SystemExit(f"gate failed ({label}); deliverable NOT replaced")
    return res


def publish(staged_dir):
    """Atomic: only a gated, complete encode is moved onto assets/films/<slug>.mp4 (os.replace on one filesystem
    via a .part file beside the target), so an interrupted render can never overwrite the deliverable."""
    import os, shutil
    from kit import OUT
    mp4 = staged_dir / f"{SLUG}.mp4"
    gate = probe_ok(mp4, "staged")
    OUT.mkdir(parents=True, exist_ok=True)
    for name in (f"{SLUG}.mp4", f"{SLUG}.webp"):
        src = staged_dir / name
        if src.exists():
            part = OUT / (name + ".part")
            shutil.copyfile(src, part)
            os.replace(part, OUT / name)
    probe_ok(OUT / f"{SLUG}.mp4", "published")
    json.dump(gate, open(SWARM / "render_gate.json", "w"), indent=1)
    print("published", OUT / f"{SLUG}.mp4")


def remux_audio():
    """--remux: rebuild only the sound bed over the PUBLISHED video (stream copy) in staging, gate it, publish."""
    import subprocess, tempfile
    from kit import Mix, OUT
    probe_ok_video = OUT / f"{SLUG}.mp4"
    mix = Mix(SECONDS, seed=film.seed)
    sound(mix)
    pcm = mix.master()
    STAGING.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        with wave.open(str(wav), "wb") as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(probe_ok_video), "-i", str(wav), "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart",
                        str(STAGING / f"{SLUG}.mp4")], check=True)
    publish(STAGING)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--remux"]:
        remux_audio()
    elif sys.argv[1:2] == ["--stills"]:
        film.render()                       # kit writes PNG stills only (films/stills/<slug>/), never the mp4
    else:
        STAGING.mkdir(parents=True, exist_ok=True)
        for f in STAGING.glob(f"{SLUG}.*"):
            f.unlink()
        film.render(out_dir=STAGING)        # encode into staging, never straight onto the deliverable
        publish(STAGING)
