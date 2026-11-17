"""Sound for the test shot (kit.Mix) + mux of the exposures (on twos) to H.264/AAC.
Foraged: paper grains (Commons 'Book paper pages assorted.ogg', PD), landing thud
(Commons 'Dull thud.ogg', PD), switch click (Commons 'Sound of heating system
turning on.ogg', PD), room tone (Wreckless 1935, optical track, via
movingimagearchive.com). Synthesised and declared: a faint 100 Hz lamp hum."""
import os, sys, json, wave, subprocess, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
FILMS = os.path.normpath(os.path.join(WORK, "../.."))
sys.path.insert(0, FILMS)
from kit import Mix, RATE  # noqa
MEDIA = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole/test-shot")


def rd(name):
    w = wave.open(os.path.join(MEDIA, name))
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
    assert w.getframerate() == RATE
    return a


def grain(a, t0, dur=0.13, pre=0.008):
    i0 = int((t0 - pre) * RATE); n = int(dur * RATE)
    g = a[i0:i0 + n].copy()
    env = np.ones(n); fa = int(0.003 * RATE); fr = int(0.05 * RATE)
    env[:fa] = np.linspace(0, 1, fa); env[-fr:] = np.linspace(1, 0, fr) ** 2
    return g * env / (np.abs(g).max() + 1e-9)


ONSETS = [1.74, 4.41, 5.78, 6.97, 7.37, 8.63, 9.49, 10.83, 11.58, 14.2, 17.79, 19.42, 23.28, 31.14, 31.72,
          35.83, 38.06, 38.75, 39.05, 39.51, 39.72, 46.25, 47.71, 52.21, 53.61, 55.99, 56.53, 59.85, 61.94, 62.25]
LAND_ONSET = 13.84


def main():
    ev = json.load(open(os.path.join(HERE, "fold-events.json")))["events"]
    n_exp = len(ev)
    secs = n_exp / 12.0
    mix = Mix(secs, seed=3)
    paper = rd("Book_paper_pages_assorted.wav")
    room = rd("wreckless_clip.wav")
    thud = rd("Dull_thud.wav")
    click = rd("click_heating.wav")
    # room tone: the quiet stretch of the Wreckless optical track, looped with crossfades
    seg = room[int(0.9 * RATE):int(3.9 * RATE)]
    seg = seg - seg.mean()
    seg = seg / (np.sqrt((seg ** 2).mean()) + 1e-9) * 0.010
    bed = np.zeros(mix.n); L = len(seg); xf = int(0.4 * RATE); pos = 0
    win = np.ones(L); win[:xf] = np.linspace(0, 1, xf); win[-xf:] = np.linspace(1, 0, xf)
    while pos < mix.n:
        m = min(L, mix.n - pos); bed[pos:pos + m] += (seg * win)[:m]; pos += L - xf
    mix.add(bed, 0.0, 1.0)
    # one paper tick per fold exposure, loudness from how far the paper moved
    folds = [e for e in ev if e["kind"] == "fold"]
    sp = []
    for a, b in zip(folds[:-1], folds[1:]):
        sp.append(abs(b["alpha_M_deg"] - a["alpha_M_deg"]) + abs(b["beta_A_deg"] - a["beta_A_deg"]))
    sp = [sp[0]] + sp
    mx = max(sp) or 1
    ticks = []
    for i, (e, s) in enumerate(zip(folds, sp)):
        if not e.get("tick"):
            continue
        g = grain(paper, ONSETS[i % len(ONSETS)])
        gain = 0.05 + 0.20 * (s / mx)
        mix.add(g, e["t"], gain, pan=-0.2 + 0.4 * (i / len(folds)))
        ticks.append((e["exposure"], e["t"]))
    # landing: the first settled exposure
    land = next(e for e in ev if e["kind"] == "settled")
    mix.add(grain(paper, LAND_ONSET, 0.2), land["t"] - 0.02, 0.30, 0.2)
    mix.add(thud / (np.abs(thud).max() + 1e-9), land["t"], 0.22, 0.2)
    # light box: switch click on the first lamp-on exposure, then a faint lamp hum (synth, declared)
    on = next(e for e in ev if e["kind"] == "lightbox" and e["lamp"] > 0)
    c = click[int(1.10 * RATE):int(1.40 * RATE)]
    mix.add(c / (np.abs(c).max() + 1e-9), on["t"] - 0.05, 0.35)
    hs = secs - on["t"]
    t = np.arange(int(hs * RATE)) / RATE
    hum = (np.sin(2 * np.pi * 100 * t) + 0.35 * np.sin(2 * np.pi * 200 * t)) * np.minimum(1, t / 0.9)
    mix.add(hum, on["t"], 0.006)
    pcm = mix.master()
    wav = os.path.join(MEDIA, "test-shot.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(pcm.tobytes())
    out = os.path.join(WORK, "test-shot.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i",
                    os.path.join(MEDIA, "exposures", "e%03d.png"), "-i", wav,
                    "-vf", "fps=24", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
    json.dump(dict(ticks=ticks, land_t=land["t"], switch_t=on["t"]), open(os.path.join(HERE, "sound-cues.json"), "w"), indent=1)
    print("wrote", out, os.path.getsize(out) / 1e6, "MB;", len(ticks), "ticks")


if __name__ == "__main__":
    main()
