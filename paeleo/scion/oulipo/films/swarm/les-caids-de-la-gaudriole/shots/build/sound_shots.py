"""Per-shot sound stems from shots/fold-events.json: one paper tick per moving exposure
(cut from the foraged Commons recording 'Book paper pages assorted', PD), landing rustle +
'Dull thud' (PD), the station bell = one strike of 'WWS Signalbell' (Commons, Work With
Sounds, CC BY 4.0), the light-box switch = the relay click of 'Sound of heating system
turning on' (PD), room tone = the quiet optical-track stretch of Wreckless (1935) via
movingimagearchive.com. Synthesised and declared: a faint 100 Hz lamp hum under shot 8.
Stems keep absolute levels (no auto-gain) so the editor can mix them as they are;
they are written at kit.RATE, stereo int16. Then each shot is muxed (exposures on twos)."""
import os, sys, json, wave, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
WS = os.path.dirname(SHOTS)
FILMS = os.path.normpath(os.path.join(WS, "../.."))
sys.path.insert(0, FILMS)
from kit import Mix, RATE  # noqa: E402
SRC = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole/tabletop")
EDITOR = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole/tabletop-lightbox-cinematographer-sound")
OUT = os.path.join(SHOTS, "sound")
os.makedirs(OUT, exist_ok=True); os.makedirs(EDITOR, exist_ok=True)


def rd(name):
    w = wave.open(os.path.join(SRC, name))
    assert w.getframerate() == RATE and w.getnchannels() == 1
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0


def write(path, L, R=None):
    R = L if R is None else R
    st = np.stack([L, R], 1)
    pk = np.abs(st).max()
    if pk > 0.95:
        st *= 0.95 / pk
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(RATE)
        wf.writeframes((st * 32767).astype(np.int16).tobytes())


def cut(a, t0, dur, pre=0.006, fade=0.05):
    i0 = max(0, int((t0 - pre) * RATE)); n = int(dur * RATE)
    g = a[i0:i0 + n].copy()
    e = np.ones(len(g)); fa = int(0.003 * RATE); fr = min(len(g) // 2, int(fade * RATE))
    e[:fa] = np.linspace(0, 1, fa); e[-fr:] = np.linspace(1, 0, fr) ** 2
    return g * e


def onsets(a, thr_db=-38, gap=0.18):
    """Transient onsets in the paper recording: a hand moving real paper."""
    h = int(0.01 * RATE)
    env = np.sqrt(np.convolve(a ** 2, np.ones(h) / h, "same"))
    db = 20 * np.log10(env + 1e-9)
    out, last = [], -1
    for i in range(1, len(db), h):
        if db[i] > thr_db and db[i - h] <= thr_db and (i - last) / RATE > gap:
            out.append(i / RATE); last = i
    return out


paper = rd("Book_paper_pages_assorted.wav"); paper -= paper.mean()
room = rd("wreckless_ef7bfc89.wav")
thud = rd("Dull_thud.wav")
click = rd("click_heating.wav")
bell = rd("WWS_Signalbell.wav")
ONS = [t for t in onsets(paper) if 0.5 < t < paper.size / RATE - 0.5]
GR = []
for t in ONS:
    g = cut(paper, t, 0.12)
    pk = np.abs(g).max()
    if pk > 0.02:
        GR.append((t, g / pk))
print(len(GR), "paper grains from", len(ONS), "onsets")

# room tone: Wreckless optical track, 1.0-3.9 s (clip time; source film ~324.0-326.9 s), looped with crossfades
seg = room[int(1.0 * RATE):int(3.9 * RATE)]; seg = seg - seg.mean()
seg = seg / (np.sqrt((seg ** 2).mean()) + 1e-9) * 0.010


def room_bed(secs):
    n = int(secs * RATE); bed = np.zeros(n); L = len(seg); xf = int(0.4 * RATE); pos = 0
    win = np.ones(L); win[:xf] = np.linspace(0, 1, xf); win[-xf:] = np.linspace(1, 0, xf)
    while pos < n:
        m = min(L, n - pos); bed[pos:pos + m] += (seg * win)[:m]; pos += L - xf
    return bed


# bell: the strike at 2.0 s of the signal bell recording, 1.6 s of ring (the next strike faded out)
bpk = int(np.argmax(np.abs(bell[int(1.9 * RATE):int(2.2 * RATE)]))) / RATE + 1.9
BELL = cut(bell, bpk, 0.66, pre=0.01, fade=0.25); BELL /= np.abs(BELL).max()
write(os.path.join(OUT, "bell-strike.wav"), BELL * 0.5)
write(os.path.join(OUT, "roomtone-10s.wav"), room_bed(10.0))

ev = json.load(open(os.path.join(SHOTS, "fold-events.json")))
cues = {}
rng = np.random.RandomState(8)
for sk, sh in ev["shots"].items():
    secs = sh["n"] / 12.0 + 0.5
    mix = Mix(secs, seed=int(sk))
    fx = Mix(secs, seed=int(sk))           # effects only (no room tone), for the editor
    E = sh["events"]
    c = []
    # loudness of each tick from how far the paper moved since the last exposure
    prev = None
    for e in E:
        mv = 0.0
        if prev is not None and "alpha_M_deg" in e:
            mv = abs(e["alpha_M_deg"] - prev["alpha_M_deg"]) + abs(e["beta_A_deg"] - prev["beta_A_deg"])
            mv += 0.4 * sum(abs(e.get("joints", {}).get(k, 0) - prev.get("joints", {}).get(k, 0)) for k in e.get("joints", {}))
            if e.get("sheet_rigid_dx_dy_dz_rotz") or e.get("corner_lift_u"):
                mv += 6.0
        prev = e
        tk = e.get("tick")
        if not tk:
            continue
        t = e["t"]
        if tk == "paper":
            g = GR[rng.randint(len(GR))][1]
            gain = 0.04 + 0.16 * min(1.0, mv / 6.0)
            for m in (mix, fx):
                m.add(g, t, gain, pan=rng.uniform(-0.3, 0.3))
        elif tk == "land":
            g = cut(paper, GR[3][0], 0.22); g /= np.abs(g).max() + 1e-9
            for m in (mix, fx):
                m.add(g, t - 0.02, 0.22, 0.15); m.add(thud / (np.abs(thud).max() + 1e-9), t, 0.20, 0.15)
        elif tk == "switch":
            k = click[int(1.10 * RATE):int(1.40 * RATE)]
            for m in (mix, fx):
                m.add(k / (np.abs(k).max() + 1e-9), t - 0.04, 0.32)
        c.append(dict(exposure=e["exposure"], t=t, cue=tk))
    if sk == "2":                                  # the station bell, once, 1 s in (= 0:08 in the film)
        for m in (mix, fx):
            m.add(BELL, 1.0, 0.30, -0.25)
        c.append(dict(t=1.0, cue="bell"))
    if sk == "8":
        on = next(e["t"] for e in E if e["kind"] == "lb-ramp")
        off = next(e["t"] for e in E if e["kind"] == "lb-clean")
        tt = np.arange(int((off - on) * RATE)) / RATE
        hum = (np.sin(2 * np.pi * 100 * tt) + 0.35 * np.sin(2 * np.pi * 200 * tt)) * np.minimum(1, tt / 0.9) * np.minimum(1, (off - on - tt) / 0.8)
        for m in (mix, fx):
            m.add(hum, on, 0.005)
        k = click[int(1.10 * RATE):int(1.40 * RATE)]
        dn = next(e["t"] for e in E if e["kind"] == "lb-down")
        for m in (mix, fx):
            m.add(k / (np.abs(k).max() + 1e-9), dn - 0.04, 0.22)
        c.append(dict(t=dn, cue="switch-off"))
    mix.add(room_bed(secs), 0.0, 1.0)
    write(os.path.join(OUT, f"shot-{sk}.wav"), mix.L, mix.R)
    write(os.path.join(OUT, f"shot-{sk}-fx.wav"), fx.L, fx.R)
    cues[sk] = c
    # mux the shot: exposures at 12/s held two frames each (24 fps container)
    src = os.path.join(FILMS, f"sources/les-caids-de-la-gaudriole/tabletop/shot-{sk}/e%03d.png")
    out = os.path.join(SHOTS, f"shot-{sk}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", src, "-i", os.path.join(OUT, f"shot-{sk}.wav"),
                    "-vf", "fps=24", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("shot", sk, len(c), "cues ->", out, round(os.path.getsize(out) / 1e6, 2), "MB")
json.dump(dict(rate=RATE, cues=cues, grains=[round(t, 3) for t, _ in GR]), open(os.path.join(OUT, "cues.json"), "w"), indent=1)
