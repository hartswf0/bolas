"""Review preview of Sh3a+Sh3b (film 17.60-27.60 s) through films/kit.py: letterbox, L3 caption, and the
process-verse unit's stems (drain, meter, room, rain, and the foraged CC BY 3.0 Engel press bed) sliced to this span.
The editor's real assembly replaces this; it exists so the shot can be watched with its sound."""
import sys, wave
from pathlib import Path
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
import numpy as np
from PIL import Image
import kit
MD = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/melt-simulation-camera-unit-b-test-shot-sh3a-sh3b-defining-beat-")
T0 = 17.60
CREAM = (232, 226, 210)
film = kit.Film("melt-shot-preview", seconds=10.0, boil=0, wobble=0, seed=3)
film.poster_at = 6.4
H1, H2 = "Le rouge se retire,", "et la forme est un creux."
def png(f):
    d = "sh3a" if f <= 499 else "sh3b"
    return Image.open(MD / d / f"f{f:04d}.png").convert("RGB")
@film.picture
def frame(t, ink):
    ink.paper((0, 0, 0))
    f = min(423 + ink.i, 662)
    ink.img.paste(png(f), (0, 66))
    ft = T0 + t
    a = kit.ramp(ft, 19.45, 19.6) * (1.0 - kit.ramp(ft, 24.2, 24.7))
    if a > 0:
        fnt = kit.font("serif", 23)
        w1 = ink.d.textlength(H1, font=fnt); w2 = ink.d.textlength(H2, font=fnt); gap = 26
        x0 = 480 - (w1 + gap + w2) / 2; y = 507; al = int(235 * a)
        ink.text((x0, y), H1, "serif", 23, CREAM, anchor="lm", alpha=al)
        ink.text((x0 + w1 + gap, y), H2, "serif", 23, CREAM, anchor="lm", alpha=al)
        rx = x0 + w1 + gap / 2
        ink.d.line([(rx, y - 12), (rx, y + 12)], fill=CREAM + (int(170 * a),), width=1)
def wav(p):
    with wave.open(str(p)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        return x.reshape(-1, w.getnchannels())
GAINS = {"meter": 1.0, "drain": 0.9, "rain": 0.8, "room": 1.0, "press_foraged": 0.7}
@film.sound
def sound(mix):
    for s, g in GAINS.items():
        x = wav(MD / "audio" / f"{s}_17.60-27.60.wav")
        mix.add(x[:, 0] / 1.414, 0, g, pan=-1.0)
        mix.add(x[:, 1] / 1.414, 0, g, pan=1.0)
if __name__ == "__main__":
    film.render(out_dir=MD)
