"""U1 dramaturg-sound: builds the sound beds and mixes for monsieur-ripois from foraged Commons recordings.
Run with python3 -I. Reads raw files (untrusted; decoded by ffmpeg only) from films/sources/monsieur-ripois/sound/raw/.
Writes WAVs (44.1 kHz, 16-bit) to films/sources/monsieur-ripois/sound/ and one-shots to .../dramaturg-sound/,
and the event list to films/swarm/monsieur-ripois/sound-events.json (read by write_manifest.py)."""
import json, subprocess, wave, sys
from pathlib import Path
import numpy as np
ROOT = Path("/home/user/bolas/paeleo/scion/oulipo/films")
RAW = ROOT / "sources/monsieur-ripois/sound/raw"
SND = ROOT / "sources/monsieur-ripois/sound"
ONE = ROOT / "sources/monsieur-ripois/dramaturg-sound"
TS = ROOT / "sources/monsieur-ripois/test-shot"
RATE, FPS, DUR = 44100, 24, 44.0
N = int(DUR * RATE)
S2_IN, S2_OUT = 216 / FPS, 468 / FPS          # flashback 9.0 .. 19.5 s
rng = np.random.default_rng(1953)

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
def save(p, x, stereo=None):
    x = np.clip(x, -0.99, 0.99)
    ch = 1 if stereo is None else 2
    data = x if stereo is None else np.stack([x, stereo], 1).reshape(-1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(RATE); w.writeframes((data * 32767).astype("<i2").tobytes())
def spec_filter(x, lo=None, hi=None, slope=1.5):
    """zero-phase FFT filter with smooth (order-ish) rolloff; lo = highpass Hz, hi = lowpass Hz"""
    n = len(x); X = np.fft.rfft(x, 2 * n); fr = np.fft.rfftfreq(2 * n, 1 / RATE)
    g = np.ones_like(fr)
    if hi: g /= np.sqrt(1 + (fr / hi) ** (4 * slope))
    if lo: g /= np.sqrt(1 + (lo / np.maximum(fr, 1e-3)) ** (4 * slope))
    return np.fft.irfft(X * g, 2 * n)[:n]
def conv(x, h):
    n = len(x) + len(h) - 1; L = 1 << int(np.ceil(np.log2(n)))
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(h, L), L)[:n]
def resample(x, ratio):   # ratio > 1 = pitch/speed up
    return np.interp(np.arange(0, len(x) - 1, ratio), np.arange(len(x)), x)
def env_db(x, hop=441):
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
def cut(x, t0, t1, fade=0.004):
    s = x[int(t0 * RATE):int(t1 * RATE)].copy(); k = max(1, int(fade * RATE))
    s[:k] *= np.linspace(0, 1, k); s[-k:] *= np.linspace(1, 0, k); return s
def norm(x, peak=0.5):
    return x / (np.abs(x).max() + 1e-12) * peak
def strongest(x, t_win=0.25, k=1, start=0.0, end=None, gap=0.3):
    """time(s) of the k strongest onsets (by 10 ms envelope) in [start, end]"""
    e = env_db(x); hop = 441
    a, b = int(start * RATE / hop), int((end or len(x) / RATE) * RATE / hop)
    order = np.argsort(e[a:b])[::-1] + a; out = []
    for i in order:
        if all(abs(i - j) * hop / RATE > gap for j in out): out.append(i)
        if len(out) == k: break
    # back off to the onset rise
    res = []
    for i in out:
        j = i
        while j > 0 and e[j - 1] > e[i] - 18: j -= 1
        res.append(j * hop / RATE)
    return sorted(res)
def quiet_windows(x, win=0.5, k=12):
    e = env_db(x); w = int(win * RATE / 441)
    m = np.convolve(e, np.ones(w) / w, "valid"); order = np.argsort(m); out = []
    for i in order:
        if all(abs(i - j) > w for j in out): out.append(i)
        if len(out) == k: break
    return [i * 441 / RATE for i in out]

# ------------------------------------------------------------------ sources
SRC = {}
def have(name): return (RAW / name).exists()
def get(name):
    if name not in SRC: SRC[name] = load(RAW / name if (RAW / name).exists() else TS / name)
    return SRC[name]
events = []   # (t, name, file, perspective, note)
def log(t, name, srcfile, persp, note=""):
    events.append(dict(t=round(t, 3), frame=int(round(t * FPS)), cue=name, source=srcfile, perspective=persp, note=note))

# ---- room tone: the real quiet room under the door recording (between its events), looped with crossfades
door = get("Closing_an_old_door.ogg")
qs = quiet_windows(door, 0.45, 6)
tone_bits = [cut(door, t, t + 0.45, 0.05) for t in qs]
def loop_tone(n):
    out = np.zeros(n + RATE); i = 0; k = 0; step = int(0.38 * RATE)
    while i < n:
        b = tone_bits[k % len(tone_bits)] * np.hanning(len(tone_bits[k % len(tone_bits)])) ** 0.5
        if rng.random() < 0.5: b = b[::-1]
        out[i:i + len(b)] += b; i += step; k += 1
    return out[:n]
room = spec_filter(loop_tone(N), lo=40, hi=6000)
room = room / (np.sqrt((room ** 2).mean()) + 1e-12) * 10 ** (-50 / 20)      # -50 dBFS RMS room

# ---- clock: individual ticks cut from the CC0 recording (its hiss gated out), re-laid at 1 Hz
clk = get("clock-tictac.ogg")
e = env_db(clk); thr = np.percentile(e, 95)
tick_idx = [i for i in range(1, len(e) - 1) if e[i] > thr and e[i] >= e[i - 1] and e[i] >= e[i + 1]]
ticks_t = []
for i in tick_idx:
    if not ticks_t or i * 441 / RATE - ticks_t[-1] > 0.5: ticks_t.append(i * 441 / RATE)
ticks = [spec_filter(cut(clk, max(0, t - 0.012), t + 0.09, 0.003), lo=300) for t in ticks_t[1:-1]]
ticks = [norm(t, 1.0) for t in ticks]
clock_track = np.zeros(N)
tick_times = list(np.arange(1.75, DUR - 1.0, 1.0))
for k, t in enumerate(tick_times):
    s = ticks[k % len(ticks)] * (0.11 if k % 2 == 0 else 0.085)   # tic / tac
    i = int(t * RATE); clock_track[i:i + len(s)] += s[:max(0, N - i)]

# ---- one-shots
def shot(name, x, persp="dry"):
    save(ONE / f"{name}.wav", x); return x
oneshots = {}
if have("Knocking_on_wood_or_door.ogg"):
    knock = get("Knocking_on_wood_or_door.ogg")
    kt = strongest(knock, k=6, gap=0.15)
    kn = [norm(spec_filter(cut(knock, t - 0.005, t + 0.18), hi=900), 1.0) for t in kt]
    oneshots["step"] = (kn, "Knocking_on_wood_or_door.ogg", "knock transients low-passed to 900 Hz = heel on parquet")
    oneshots["setdown"] = ([norm(spec_filter(cut(knock, kt[0] - 0.005, kt[0] + 0.25), hi=1400), 1.0)], "Knocking_on_wood_or_door.ogg", "one knock, 1.4 kHz low-pass, fabric-damped = box set on a lap / into hands")
else:
    kn = None
if have("Cupboarddoorclose.ogg"):
    cup = get("Cupboarddoorclose.ogg"); ct = strongest(cup, k=1)[0]
    lid = norm(cut(cup, max(0, ct - 0.01), ct + 0.25), 1.0)
    oneshots["lidclick"] = ([norm(spec_filter(resample(lid, 1.6), lo=500), 1.0)], "Cupboarddoorclose.ogg", "wooden cupboard close, pitched up 1.6x, high-passed: small box lid click")
    oneshots["clasp"] = ([norm(spec_filter(resample(lid, 2.2), lo=1200)[:int(0.05 * RATE)], 1.0)], "Cupboarddoorclose.ogg", "first 50 ms of the close, pitched up 2.2x: clasp tick")
    oneshots["lidshut"] = ([norm(resample(lid, 1.2), 1.0)], "Cupboarddoorclose.ogg", "lid shut (muffled later)")
if have("Door_handle_creaking.ogg"):
    dh = get("Door_handle_creaking.ogg"); t0 = strongest(dh, k=1)[0]
    oneshots["latch"] = ([norm(cut(dh, max(0, t0 - 0.02), t0 + 0.6, 0.02), 1.0)], "Door_handle_creaking.ogg", "door handle turned: latch")
if have("Squeaky_door_hinge.ogg"):
    hg = get("Squeaky_door_hinge.ogg"); t0 = strongest(hg, k=1)[0]
    h = norm(cut(hg, max(0, t0 - 0.05), t0 + 0.9, 0.05), 1.0)
    oneshots["doorhinge"] = ([h], "Squeaky_door_hinge.ogg", "door swinging open")
    oneshots["lidhinge"] = ([norm(resample(h, 1.7)[:int(0.45 * RATE)], 1.0)], "Squeaky_door_hinge.ogg", "hinge pitched up 1.7x, 0.45 s: small box lid opening")
door_open_t = strongest(door, k=1)[0]
oneshots["door"] = ([norm(cut(door, max(0, door_open_t - 0.05), door_open_t + 0.9, 0.03), 1.0)], "Closing_an_old_door.ogg", "old door, its strongest event")
if have("Book_paper_pages_assorted.ogg"):
    bp = get("Book_paper_pages_assorted.ogg"); pt = strongest(bp, k=8, gap=0.4)
    pp = [norm(cut(bp, max(0, t - 0.01), t + 0.35, 0.02), 1.0) for t in pt]
    oneshots["paper"] = (pp, "Book_paper_pages_assorted.ogg", "page/paper handling transients (receipt slip, fold, unfold)")
    oneshots["cloth"] = ([norm(spec_filter(cut(bp, max(0, pt[3] - 0.05), pt[3] + 0.9, 0.2), hi=1500), 1.0)], "Book_paper_pages_assorted.ogg", "slow paper movement low-passed to 1.5 kHz = cloth rustle of his sleeve")
if have("Assorted_creaking_noises_of_office_chair.ogg"):
    ch = get("Assorted_creaking_noises_of_office_chair.ogg"); cht = strongest(ch, k=3, gap=0.8)
    oneshots["creak"] = ([norm(spec_filter(cut(ch, max(0, t - 0.03), t + 0.5, 0.04), hi=2500), 1.0) for t in cht], "Assorted_creaking_noises_of_office_chair.ogg", "chair creak low-passed 2.5 kHz = sofa cushion/spring")
for k, (lst, f, note) in oneshots.items():
    for j, x in enumerate(lst): shot(f"{k}-{j}", x)
save(ONE / "roomtone-loop-10s.wav", room[:10 * RATE] * 8)
save(ONE / "clock-ticks-10s.wav", clock_track[int(2 * RATE):int(12 * RATE)])

def os_(name, j=0):
    lst = oneshots.get(name, (None,))[0]
    return None if lst is None else lst[j % len(lst)]

# ------------------------------------------------------------------ cue timeline (seconds)
fr = lambda f: f / FPS
PRESENT = [  # (t, oneshot, variant, gain, cue, master/baseline)
 (fr(82), "creak", 0, 0.10, "CUE-1 his lean: cushion", "both"),
 (fr(144), "setdown", 0, 0.16, "CUE-1b box set down on her lap", "both"),
 (fr(186), "clasp", 0, 0.07, "CUE-2a clasp tick", "master"),
 (fr(648), "cloth", 0, 0.06, "CUE-3h his hand to his knee: sleeve rustle", "both"),
 (fr(718), "paper", 0, 0.12, "CUE-4 slip lands on the cushion", "master"),
 (fr(721), "paper", 1, 0.05, "CUE-4 slip settles", "master"),
 (fr(756), "paper", 2, 0.10, "CUE-4i unfold 1", "master"),
 (fr(770), "paper", 3, 0.09, "CUE-4i unfold 2", "master"),
 (fr(784), "paper", 4, 0.09, "CUE-4i unfold 3", "master"),
 (fr(918), "paper", 5, 0.06, "CUE-5a receipt into the velvet slot", "master"),
 (fr(948), "lidclick", 0, 0.22, "CUE-5b lid click (dry, close)", "master"),
]
FLASH = [
 (fr(220), "latch", 0, 0.20, "SH-1 latch"),
 (fr(222), "doorhinge", 0, 0.14, "SH-1 door swings open"),
 (fr(240), "step", 0, 0.22, "SH-1 step 1"), (fr(252), "step", 1, 0.20, "SH-1 step 2"),
 (fr(264), "step", 2, 0.22, "SH-1 step 3"), (fr(276), "step", 3, 0.18, "SH-1 step 4"),
 (fr(341), "setdown", 0, 0.14, "SH-2 box into the aunt's hands"),
 (fr(349), "lidhinge", 0, 0.12, "SH-3 aunt opens lid (soft hinge)"),
 (fr(408), "lidshut", 0, 0.24, "SH-4 lid shut INSIDE the swallow (heard, not seen); no ring sound"),
 (fr(456), "setdown", 0, 0.16, "SH-4 box set on the aunt's lap"),
]

def place(buf, s, t, g):
    if s is None: return False
    i = int(t * RATE); j = min(N, i + len(s)); buf[i:j] += s[:j - i] * g; return True

def build(variant):
    sfx_p = np.zeros(N); sfx_f = np.zeros(N)
    for t, nm, j, g, cue, who in PRESENT:
        if variant == "baseline" and who == "master": continue
        if place(sfx_p, os_(nm, j), t, g) and variant == "master": log(t, cue, oneshots[nm][1], "present dry")
    for t, nm, j, g, cue in FLASH:
        if place(sfx_f, os_(nm, j), t, g) and variant == "master": log(t, cue, oneshots[nm][1], "flashback muffled")
    a, b = int(S2_IN * RATE), int(S2_OUT * RATE)
    # present bed: dry room + dry clock, outside S2 (fade in from 1.5 s, out 42.0 -> 43.0)
    pres = room + clock_track + sfx_p
    gate = np.ones(N); gate[a:b] = 0
    fi = np.clip((np.arange(N) / RATE - 1.5) / 0.5, 0, 1); fo = np.clip((43.0 - np.arange(N) / RATE) / 1.0, 0, 1)
    pres = pres * gate * fi * fo
    # flashback bed: the same room and clock heard through his telling: low-passed 650 Hz, far, reverberant (1.6 s IR)
    fl_dry = (room * 1.4 + clock_track + sfx_f)
    fl_dry = spec_filter(fl_dry[a - RATE:b + 2 * RATE], hi=650, slope=1.2)
    L = int(1.6 * RATE); ir = rng.normal(0, 1, L) * np.exp(-np.arange(L) / (0.36 * RATE)); ir = spec_filter(ir, hi=1800); ir /= np.sqrt((ir ** 2).sum())
    wet = conv(fl_dry, ir)[:len(fl_dry)]
    fl = 0.35 * fl_dry + 0.95 * wet
    flash = np.zeros(N); seg = fl[RATE:RATE + (b - a)].copy()
    k = int(0.006 * RATE); seg[:k] *= np.linspace(0, 1, k)    # hard cut in; the cut out is hard (dry on frame 468)
    flash[a:b] = seg
    # sonic perspective: the telling sits 4 dB under the dry present room (far, muffled), measured on the beds
    r_p = np.sqrt((pres[int(2.5 * RATE):int(8.5 * RATE)] ** 2).mean()); r_f = np.sqrt((flash[a:b] ** 2).mean())
    flash *= r_p / r_f * 10 ** (-4 / 20)
    mix = pres + flash
    return mix, pres, flash, sfx_p, sfx_f

out = {}
for v in ("master", "baseline"):
    mix, pres, flash, sp, sf = build(v)
    peak = np.abs(mix).max(); gn = 0.5 / peak if v == "master" else out["gain"]
    out["gain"] = gn
    # slight stereo: clock a touch left, room decorrelated
    left = mix * gn; right = (mix + spec_filter(np.roll(room, 977), hi=6000) * 0.0) * gn
    save(SND / f"mix-{v}.wav", left, right)
    if v == "master":
        save(SND / "mix-late.wav", left, right)          # --late changes picture only; sound identical
        save(SND / "bed-present-dry.wav", pres * gn); save(SND / "bed-flashback-muffled.wav", flash * gn)
        save(SND / "sfx-present-dry.wav", sp * gn); save(SND / "sfx-flashback-raw.wav", sf * gn)
        save(SND / "room-tone-dry.wav", room * gn); save(SND / "clock-dry.wav", clock_track * gn)
        st = dict(peak_dbfs=round(20 * np.log10(np.abs(mix * gn).max()), 1),
                  present_rms_dbfs=round(20 * np.log10(np.sqrt(((mix * gn)[int(2 * RATE):int(9 * RATE)] ** 2).mean())), 1),
                  flashback_rms_dbfs=round(20 * np.log10(np.sqrt(((mix * gn)[int(9.2 * RATE):int(19.4 * RATE)] ** 2).mean())), 1))
        # spectral check: share of energy above 1 kHz just before/after the cut
        def hf(x):
            X = np.abs(np.fft.rfft(x)) ** 2; f_ = np.fft.rfftfreq(len(x), 1 / RATE); return float(X[f_ > 1000].sum() / X.sum())
        st["hf_share_last_0.5s_flashback"] = round(hf(mix[int(19.0 * RATE):int(19.5 * RATE)]), 3)
        st["hf_share_first_0.5s_present_after_cut"] = round(hf(mix[int(19.5 * RATE):int(20.0 * RATE)]), 3)
        out["stats"] = st
json.dump(dict(events=events, tick_times=[round(t, 3) for t in tick_times], room_tone_windows_s=[round(q, 3) for q in qs],
               clock_ticks_used_from_source_s=[round(t, 3) for t in ticks_t[1:-1]],
               oneshots={k: dict(source=v[1], how=v[2], n=len(v[0])) for k, v in oneshots.items()},
               missing=[k for k in ("step", "lidclick", "latch", "doorhinge", "paper", "creak") if k not in oneshots],
               stats=out["stats"]), open(ROOT / "swarm/monsieur-ripois/dramaturg-sound-build/sound-events.json", "w"), indent=1)
print(json.dumps(out["stats"]), "missing:", [k for k in ("step", "lidclick", "latch", "doorhinge", "paper", "creak") if k not in oneshots])
