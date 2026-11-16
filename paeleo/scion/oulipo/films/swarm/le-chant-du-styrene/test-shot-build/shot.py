"""Test shot Sh3b (film time 20.80-27.60) rendered through films/kit.py.

Run: python3 -I shot.py            -> ../test-shot.mp4
     python3 -I shot.py --stills t ...
Shot-relative time t = film time - 20.80.
"""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image
import kit
import melt

T0 = 20.80
CREAM = (232, 226, 210)
film = kit.Film("test-shot", seconds=melt.DUR, boil=0, wobble=0, seed=3)
film.poster_at = 3.0

H1 = "Le rouge se retire,"
H2 = "et la forme est un creux."

@film.picture
def frame(t, ink):
    ink.paper((0, 0, 0))
    ink.img.paste(Image.fromarray(melt.band(t, ink.i)), (0, 66))
    # caption: line L3 (onset 19.60 film time), held until 24.20 then fades
    a = 1.0 - kit.ramp(t, 3.4, 3.9)
    if a > 0:
        f = kit.font("serif", 23)
        w1 = ink.d.textlength(H1, font=f); w2 = ink.d.textlength(H2, font=f)
        gap = 26
        x0 = 480 - (w1 + gap + w2) / 2
        y = 507
        al = int(235 * a)
        ink.text((x0, y), H1, "serif", 23, CREAM, anchor="lm", alpha=al)
        ink.text((x0 + w1 + gap, y), H2, "serif", 23, CREAM, anchor="lm", alpha=al)
        rx = x0 + w1 + gap / 2
        ink.d.line([(rx, y - 12), (rx, y + 12)], fill=CREAM + (int(170 * a),), width=1)

def syl_onsets():
    on = 19.60
    return {k: on + (k - 1) * 0.30 + (0.45 if k > 6 else 0) - T0 for k in range(5, 13)}

@film.sound
def sound(mix):
    r = mix.rate
    # room + faint press hum (handmade)
    mix.room(0, melt.DUR, gain=0.018, hum=50)
    mix.drone(0, melt.DUR, freqs=(50, 100, 150.6, 201), gain=0.022, attack=0.2, release=0.6)
    # the meter: viscous low pulses, syllables 5..12 of L3 ("-ti-(re) | et la for-m'est un creux")
    for k, at in syl_onsets().items():
        last = k == 12
        sec = 0.55 if last else 0.26
        t = mix.t(sec)
        f0 = (72 if last else 96 - 3 * (k - 5))
        f = f0 * (1 + 0.35 * np.exp(-t * 22)) * (1 - 0.12 * t / sec)
        body = np.sin(2 * np.pi * np.cumsum(f) / r) + 0.35 * np.sin(4 * np.pi * np.cumsum(f) / r)
        e = (1 - np.exp(-t * 120)) * np.exp(-t * (5 if last else 11))
        blub = mix.band(mix.noise(sec), 150, 900) * np.exp(-t * 30) * 0.25
        mix.add((body * e + blub) * 0.5, max(at, 0), 0.55 if not last else 0.7, pan=-0.15 + 0.04 * (k - 5))
    # each cavity lets go (a small wet suction) when its melt has left: times from the simulation
    for ci in melt.cav_info:
        ti = float(np.interp(melt.gate_T[ci["id"]], np.sort(melt.tau_tab), melt.tt_[np.argsort(melt.tau_tab)]))
        sec = 0.18; t = mix.t(sec)
        s = mix.band(mix.noise(sec), 500, 2600) * np.sin(np.pi * t / sec) ** 2
        s += 0.4 * np.sin(2 * np.pi * np.cumsum(300 + 900 * t / sec) / r) * np.exp(-t * 18)
        pan = (ci["c"][0] - melt.hub[0]) / 500
        mix.add(s, ti, 0.10, pan=float(np.clip(pan, -0.8, 0.8)))
    # drain: falling tone with gurgle, the melt pulled up the runner into the sprue
    a0, a1 = 1.2, 5.45
    sec = a1 - a0; t = mix.t(sec)
    f = 190 * (55 / 190) ** (t / sec)
    tone = np.sin(2 * np.pi * np.cumsum(f) / r) * 0.6 + 0.25 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / r)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(7 + 5 * t / sec) / r)
    gurg = mix.band(mix.noise(sec, "brown"), 60, 500) * am
    env = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 0.7 * (0.4 + 0.6 * t / sec)
    mix.add((tone * 0.5 + gurg * 0.8) * env, a0, 0.18)
    # the last of it goes down the sprue at 5.40 (26.20): a glug
    mix.thud(5.40, freq=58, gain=0.35, seconds=0.5)
    t = mix.t(0.22)
    bub = np.sin(2 * np.pi * np.cumsum(220 + 1200 * t / 0.22) / r) * np.exp(-t * 14)
    mix.add(bub, 5.43, 0.08)
    # sound-only transition (26.80-27.60): granular pellet rain predicting the next material
    rs = np.random.RandomState(7)
    n = 0
    tt = 6.0
    while tt < melt.DUR:
        dens = 18 + 140 * (tt - 6.0) / 0.8
        mix.click(tt, gain=0.05 + 0.05 * rs.rand(), pan=rs.uniform(-0.8, 0.8), bright=int(rs.uniform(3500, 9000)), seconds=0.012)
        tt += rs.exponential(1 / dens); n += 1
    mix.reverb(0.18, 1.1)

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent
    film.render(out_dir=out)
