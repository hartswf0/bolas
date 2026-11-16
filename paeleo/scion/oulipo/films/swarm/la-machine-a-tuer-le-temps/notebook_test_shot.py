"""TEST SHOT (notebook-animator): S5 re-shuffle + S6 push + the opening of cut B.

  local 0..215   S5  (global 660..875)  riffle back, 6 slips lifted / parked /
                 re-slotted, red pencil strikes and re-numbers, 'A' -> 'B', hold
  local 216..233 S6  (global 876..893)  push into page 1 (05) ending on asset 05 W0
  local 234..353 B1 event 1: 05, src 0..59 at 0.5x (each frame twice), 5.0 s
  local 354..401 B1 event 2: 04, src 0..47
  local 402..473 B1 event 3: 02, src 24..95 (its full 3.0 s)
Run: python3 notebook_test_shot.py  (renders with films/kit.py, unedited)
"""
import sys, json, math, hashlib, wave, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import numpy as np
import kit
import notebook_rig as R

OUT = R.SRC / 'notebook'
AUD = R.SRC / 'notebook-animator/aud'
FPS = 24
G0 = R.TL['S5'][0]
L5, L6 = R.TL['S5'][1] - G0 + 1, 18
CUTS = [('05', 0, 59, 0.5), ('04', 0, 47, 1), ('02', 24, 95, 1)]
N = L5 + L6 + sum(round((b - a + 1) / s) for _, a, b, s in CUTS)
LEDGER = {}


def which(f):
    if f < L5 + L6:
        return ('notebook', G0 + f)
    t = f - L5 - L6
    for k, a, b, s in CUTS:
        n = round((b - a + 1) / s)
        if t < n:
            return ('cut', k, a + int(t * s))
        t -= n
    raise ValueError(f)


def picture(t, ink):
    f = int(round(t * FPS))
    ink._grain = False                                    # no kit grain anywhere in this shot
    w = which(f)
    if w[0] == 'notebook':
        img, led = R.notebook_frame(w[1])
        led['local'] = f
    else:
        img = R.asset_frame(w[1], w[2])
        led = dict(local=f, segment='S7', asset_id=w[1], src_frame=w[2], md5=hashlib.md5(img.tobytes()).hexdigest())
    LEDGER[f] = led
    ink.paste(img, (0, 0))


def load_wav(p):
    with wave.open(str(p)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
        return a, w.getframerate()


def sound(mix):
    """T0 room + T2 foley cued from the rig's event stream (handmade), and the
    station bed under cut B (foraged if the Commons file could be fetched)."""
    sec = lambda gf: (gf - G0) / FPS
    T = N / FPS; r = mix.rate
    mix.room(0, T, gain=0.012)
    for e in R.events():
        if not (G0 <= e['f'] < G0 + L5 + L6):
            continue
        t = sec(e['f'])
        if e['ev'] == 'lift':
            mix.click(t, gain=0.05, bright=1800, seconds=0.03)
        elif e['ev'] == 'travel':
            d = e['frames'] / FPS
            n = int(d * r)
            x = mix.band(mix.noise(d + 0.05), 700, 5000)[:n] * np.sin(np.linspace(0, math.pi, n)) ** 0.7
            mix.add(x, t, gain=0.05)
        elif e['ev'] == 'setdown':
            mix.click(t, gain=0.22, bright=2400, seconds=0.045)
            mix.thud(t, freq=150, gain=0.06, seconds=0.1)
        elif e['ev'] in ('strike', 'write'):
            d = e['frames'] / FPS; n = int(d * r)
            x = mix.band(mix.noise(d + 0.05), 1800, 9000)[:n]
            env = np.abs(np.sin(np.linspace(0, math.pi * (1 if e['ev'] == 'strike' else 3), n))) ** 0.6
            env *= 0.6 + 0.4 * (mix.rs.random(n) > 0.3)
            mix.add(x * env, t, gain=0.07)
        elif e['ev'] == 'turn':
            d = e['frames'] / FPS; n = int(d * r)
            x = mix.lowpass(mix.noise(d + 0.05, 'pink'), 2500)[:n] * np.sin(np.linspace(0, math.pi, n)) ** 1.5
            mix.add(x, t, gain=0.16)
            mix.click(t + d * 0.9, gain=0.07, bright=1500, seconds=0.05)
    # station bed: rises on the push, ducked in B; tick slows and stops over the stare
    t_push, t_b = L5 / FPS, (L5 + L6) / FPS
    n = int(T * r); tt = np.arange(n) / r
    bed_src = AUD / 'bed.wav'
    if bed_src.exists():
        bed, _ = load_wav(bed_src); bed = np.resize(bed, n)
    else:
        sub = kit.Mix(T, seed=5)
        sub.murmur(0, T, gain=0.5, pitch=115)
        sub.add(sub.lowpass(sub.noise(T, 'brown'), 180), 0, gain=0.6)
        sub.reverb(0.35, 1.4)
        bed = (sub.L + sub.R) / 2; bed = bed / (np.abs(bed).max() + 1e-9)
    env = np.interp(tt, [0, t_push - 0.5, t_push, t_b, t_b + 0.4, T], [0.0, 0.0, 0.05, 0.30, 0.106, 0.106])
    env *= np.interp(tt, [0, t_b + 1.6, t_b + 2.0, t_b + 4.6, t_b + 5.0, T], [1, 1, 0.45, 0.45, 1, 1])
    mix.add(bed * env, 0, gain=1.0)
    for i, tk in enumerate([t_b + 0.1, t_b + 1.1, t_b + 2.25]):
        mix.click(tk, gain=0.15, bright=5200, seconds=0.025)
    tl = t_b + 120 / FPS - 6 / FPS                       # pre-lapped door latch, 6 f before 05 -> 04
    mix.click(tl, gain=0.30, bright=3500, seconds=0.03)
    mix.thud(tl + 0.06, freq=95, gain=0.22, seconds=0.3)


film = kit.Film('test-shot', seconds=N / FPS, size=(R.OW, R.OH), fps=FPS, boil=0, wobble=0)
film.picture(picture)
film.sound(sound)
film.poster_at = 150 / FPS

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    film.render(out_dir=OUT)
    json.dump(dict(shot='notebook test shot', fps=FPS, frames=N, global_offset=G0, timeline=R.TL,
                   events=[e for e in R.events() if G0 <= e['f'] < G0 + L5 + L6],
                   ledger=[LEDGER[k] for k in sorted(LEDGER)]),
              open(OUT / 'test-shot-ledger.json', 'w'), indent=1)
    print('frames', N)
