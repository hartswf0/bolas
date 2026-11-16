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
  4  0:28-0:44  P01 prise B soir        (leaves open 31.0, memory bench behind, close 41-43.5)
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
    """cream/muted text with a soft 1-2 px dark halo for legibility (no box, no band)"""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, s, font=f, fill=(14, 11, 9, int(200 * alpha)), anchor=anchor, stroke_width=1,
                             stroke_fill=(14, 11, 9, int(200 * alpha)))
    halo = lay.filter(ImageFilter.GaussianBlur(1.6))
    im.alpha_composite(halo)
    if f.size < 20:                          # small gloss / record lines: a second pass of the same halo
        im.alpha_composite(halo)
    ImageDraw.Draw(im).text(xy, s, font=f, fill=tuple(color) + (int(255 * alpha),), anchor=anchor)


def overlay(img, shot, t):
    im = img.convert("RGBA")
    # present-tense slate: small muted mono, top left (never on the card)
    if shot != 6:
        lab = SHOTS[shot]["label"]
        col = (66, 58, 44, 235) if shot in (3, 5) else (168, 156, 134, 230)
        ImageDraw.Draw(im).text((16, 12), lab, font=ft(*SLATE_FONT), fill=col)
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
    # land every tail on zero 60 ms before the cut so the AAC frame straddling 44.0 carries no energy
    k = int(0.06 * RATE)
    ramp = np.linspace(1, 0, k)
    for ch in (mix.L, mix.R):
        ch[i - k:i] *= ramp
        ch[i:] = 0.0                        # DECLARED DIGITAL SILENCE 44.0-57.0 (master() only scales: zeros stay 0)


if __name__ == "__main__":
    film.render()
