"""Sound unit for zazie-dans-le-metro: trims foraged recordings, builds the cue
sheet for cut A and cut B against gag-route.json, renders a soundbed preview
with kit.Mix, and checks cue timing and the declared-silence holds.

Run:  python3 -I build_sound.py
Inputs are decoded with ffmpeg only (untrusted media). Nothing from the
downloads is executed.
"""
import json, math, subprocess, sys, wave
from pathlib import Path
import numpy as np

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
sys.path.insert(0, str(FILMS))
import kit  # noqa: E402

SW = FILMS / "swarm/zazie-dans-le-metro"
SND = FILMS / "sources/zazie-dans-le-metro/sound"
RAW, TRIM = SND / "raw", SND / "trim"
TRIM.mkdir(parents=True, exist_ok=True)
SR, FPS, DUR = 44100, 24, 22.0
MIA = Path("/home/user/hartswf0/cineosis-lab/lab/clips")


def fr(f):
    return f / FPS


def load(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.4f}"]
    if t is not None:
        cmd += ["-t", f"{t:.4f}"]
    cmd += ["-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)
    return x


def save(path, x):
    x = np.asarray(x, np.float64)
    st = x if x.ndim == 2 else np.stack([x, x], 1)
    st = np.clip(st, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def db(x):
    return 20 * math.log10(max(1e-12, float(np.sqrt(np.mean(np.asarray(x) ** 2)))))


def onset(x, thresh_rel=0.25, win=64):
    """First sample where the short-time envelope passes thresh_rel * its max."""
    e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same"))
    if e.max() <= 0:
        return None
    return int(np.argmax(e >= thresh_rel * e.max()))


def fade(x, a=0.002, r=0.02):
    x = x.copy(); na, nr = int(a * SR), int(r * SR)
    if na: x[:na] *= np.linspace(0, 1, na)
    if nr: x[-nr:] *= np.linspace(1, 0, nr)
    return x


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


def resample_pitch(x, ratio):
    """Pitch by resampling (tape-speed): ratio>1 is higher and shorter."""
    n = int(len(x) / ratio)
    return np.interp(np.arange(n) * ratio, np.arange(len(x)), x)


def lowpass(x, hz):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / hz) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, hz):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (hz / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X, len(x))


def events(x, min_gap=0.08, rel=0.3, win=220):
    """Transient candidates: peaks of positive envelope flux."""
    e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same"))
    flux = np.maximum(0, np.diff(e, prepend=e[0]))
    fl = np.convolve(flux, np.ones(win) / win, "same")
    thr = rel * fl.max(); out = []; i = 0; gap = int(min_gap * SR)
    while i < len(fl):
        if fl[i] > thr:
            j = i + int(np.argmax(fl[i:i + gap])); out.append((j, float(e[j:j + gap].max()))); i = j + gap
        else:
            i += 1
    return out


def oneshot(x, at, pre=0.004, length=0.25, r=0.04):
    a = max(0, at - int(pre * SR))
    seg = x[a:a + int(length * SR)]
    o = onset(seg, 0.2) or 0
    seg = x[a + max(0, o - int(0.001 * SR)): a + max(0, o - int(0.001 * SR)) + int(length * SR)]
    return fade(seg, 0.0005, r)


# --------------------------------------------------------------- cue sheet ---
GR = json.load(open(SW / "gag-route.json"))
EXA = GR["exposure_sheet"]["A"]
EXB = GR["exposure_sheet"]["B"]
RUN_A = [r["f"] for r in EXA if r.get("contact") and r["f"] % 8 == 0]   # first frame of each contact pair
RUN_B = [r["f"] for r in EXB if r.get("contact") and r["f"] % 8 == 0]


def cue(f, name, src, gain, pan, purpose, event, **kw):
    d = dict(t=round(fr(f), 4), frame=f, cue=name, gain=gain, pan=pan, purpose=purpose, event=event)
    d.update(src); d.update(kw)
    return d


def cues_for(cut):
    C = []
    F = lambda **k: {"file": k["file"]}
    S = lambda s: {"synth": s}
    # S1 offscreen bell, before V enters at f12 (gag-route: offscreen LEFT, f8 = 0.333 s; task 0.35 s = f8.4)
    C.append(cue(8, "tram bell, offscreen left (V not yet visible; enters f12)", F(file="trim/bell_tram_1.wav"), 0.55, -0.85, "offscreen", "gag-route f8 offscreen bell"))
    # S2 footsteps on stone on run contacts
    for k, f in enumerate(f for f in RUN_A if 48 <= f < 144):
        C.append(cue(f, f"footstep on stone (run contact {k+1})", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.42 if k % 2 == 0 else 0.36, -0.3 + 0.6 * (f - 48) / 96, "impact", f"exposure_sheet A contact f{f}"))
    C.append(cue(120, "tram bell receding, off right", F(file="trim/bell_tram_2.wav"), 0.22, 0.9, "offscreen", "gag-route f120 V leaves frame right"))
    # S3 gust and declared silence
    C.append(cue(158, "wind gust (fringe sweeps the right eye)", F(file="trim/wind_gust.wav"), 0.5, 0.35, "bed", "gag-route f158 gust 6.6 s"))
    C.append(cue(184, "DECLARED SILENCE 7.667-8.000 s (picture hold f184-191)", S("none: all layers gated to zero"), 0.0, 0.0, "hold", "exposure_sheet hold f184-191", hold=[fr(184), fr(192)]))
    if cut == "A":
        C.append(cue(192, "JUMP CUT: hard change to busier Clichy square bed", F(file="trim/bed_clichy.wav"), 0.55, 0.0, "bed", "cuts.A f192 AnchoredJumpCut"))
        C.append(cue(192, "tram bell close, centre (V is right there)", F(file="trim/bell_tram_3.wav"), 0.6, 0.15, "impact", "gag-route f192 bell close centre"))
        C.append(cue(196, "PLACE DE CLICHY plaque pops in (paper snap)", F(file="trim/paper_snap_1.wav"), 0.5, 0.6, "impact", "gag-route f196 plaque pop"))
        C.append(cue(216, "gulp: small paper click (eyes open on V)", F(file="trim/paper_tick_1.wav"), 0.3, 0.05, "impact", "gag-route f216 gulp"))
        C.append(cue(240, "push-in: low tunnel resonance swells", F(file="trim/bed_tunnel.wav"), 0.45, 0.0, "bed", "gag-route f240 push-in"))
    else:
        C.append(cue(192, "continuity cut: rue Royale bed continues (no change)", F(file="trim/bed_royale.wav"), 0.5, 0.0, "bed", "B_overrides f192 ambience continuous"))
        C.append(cue(192, "tram bell far, off right", F(file="trim/bell_tram_2.wav"), 0.2, 0.85, "offscreen", "B_overrides f192 bell far"))
        for k, f in enumerate(f for f in RUN_B if 192 <= f < 240):
            C.append(cue(f, f"footstep on stone (S4b run contact {k+1})", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.38, -0.2 + 0.5 * (f - 192) / 48, "impact", f"exposure_sheet B contact f{f}"))
    # S5 syllables (same timing in B)
    sylls = GR["tiles"]["syllables"]
    ratios = [1.0, 1.19, 1.12, 0.94, 1.33]   # DOU KI PU DONK TAN: a little melody, TAN highest
    for s, r in zip(sylls, ratios):
        C.append(cue(s["f"], f"syllable tile click {s['syl']} (pitch x{r})", F(file=f"trim/tile_click_{s['syl']}.wav"), 0.55, -0.15 + 0.3 * sylls.index(s) / 4, "impact", f"tiles.syllables {s['syl']} f{s['f']}"))
    if cut == "A":
        C.append(cue(275, "jaw drop on TAN (soft card thud)", F(file="trim/card_thud.wav"), 0.5, 0.0, "impact", "gag-route f275 jaw drop"))
        for k, (tid, f) in enumerate(GR["tiles"]["release"].items()):
            C.append(cue(f, f"tile {tid} releases (clatter cascade {k+1}/7)", F(file=f"trim/clatter_{k%4+1}.wav"), 0.32, -0.6 + 1.2 * k / 6, "impact", f"tiles.release {tid} f{f}"))
        for k, (tid, f) in enumerate(GR["tiles"]["land"].items()):
            C.append(cue(f, f"tile {tid} lands on jaw floor", F(file=f"trim/clatter_{(k+2)%4+1}.wav"), 0.26, -0.6 + 1.2 * k / 6, "impact", f"tiles.land {tid} f{f}"))
        C.append(cue(298, "MATCH CUT: Chatelet bed in, clatter tail rings 1 f across", F(file="trim/bed_chatelet.wav"), 0.45, 0.0, "bed", "cuts.A f298 TileRewrite"))
        C.append(cue(300, "PLACE DU CHATELET plaque pops", F(file="trim/paper_snap_2.wav"), 0.45, 0.6, "impact", "gag-route f300 plaque"))
        for k, f in enumerate([312, 320]):
            C.append(cue(f, f"footstep on stone (S6 run-in {k+1})", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.4, -0.6 + 0.2 * k, "impact", f"exposure_sheet A run.0/run.4 f{f}"))
        C.append(cue(326, "CONTACT: card clack + thud as she hits the queue", F(file="trim/impact_contact.wav"), 0.85, -0.05, "impact", "gag-route f326 contact frame"))
        C.append(cue(328, "HOLD 0.25 s after the bounce: total silence 13.667-13.917 s", S("none: all layers gated to zero"), 0.0, 0.0, "hold", "gag-route hold f326-332", hold=[fr(328), fr(334)]))
        dom = [341, 344, 347, 350, 353, 356, 359]
        for k, f in enumerate(dom):
            C.append(cue(f, f"domino tick {k+1}/7 (rising pitch x{1.0 + 0.09 * k:.2f})", F(file=f"trim/domino_{k+1}.wav"), 0.45, -0.4 + 0.8 * k / 6, "impact", f"gag-route domino tick f{f}"))
        for k, f in enumerate([382, 391, 400, 409]):
            C.append(cue(f, f"hollow card footstep on tile tread {k+1}", F(file=f"trim/step_card_{k+1}.wav"), 0.5, -0.1 + 0.15 * k, "impact", f"gag-route foot on card tread f{f}"))
        C.append(cue(414, "step onto the tram deck (wood)", F(file="trim/step_deck.wav"), 0.5, 0.45, "impact", "gag-route f414 step on deck"))
    else:
        C.append(cue(298, "plain cut: Chatelet bed in", F(file="trim/bed_chatelet.wav"), 0.45, 0.0, "bed", "B_overrides f298 plain cut"))
        for k, f in enumerate([312, 320]):
            C.append(cue(f, f"footstep on stone (S6b run-in {k+1})", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.4, -0.6 + 0.2 * k, "impact", f"exposure_sheet B run f{f}"))
        for k, f in enumerate([341, 344, 347, 350, 353, 356, 359]):
            C.append(cue(f, f"queue shuffles: commuter footstep {k+1}", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.22, 0.1 + 0.05 * k, "impact", f"B_overrides f{f} queue shuffle"))
        for k, f in enumerate([372, 380, 388, 396, 404]):
            C.append(cue(f, f"walk to the platform {k+1}", F(file=f"trim/step_stone_{k%4+1}.wav"), 0.32, 0.0 + 0.1 * k, "impact", f"exposure_sheet B walk f{f}"))
        C.append(cue(410, "step onto the tram platform (wood)", F(file="trim/step_deck.wav"), 0.45, 0.45, "impact", "exposure_sheet B step_platform f410"))
    # departure bell twice, hooves, ride
    C.append(cue(418, "departure bell 1/2", F(file="trim/bell_tram_1.wav"), 0.5, 0.55, "impact", "gag-route f418 bell x2"))
    C.append(cue(426, "departure bell 2/2", F(file="trim/bell_tram_1.wav"), 0.5, 0.55, "impact", "gag-route f426 bell x2"))
    C.append(cue(418, "hooves start", F(file="trim/hooves_ride.wav"), 0.5, 0.3, "bed", "gag-route f418 hooves start"))
    C.append(cue(432, "ride: hooves + wheel rumble + breeze", F(file="trim/breeze_ride.wav"), 0.35, 0.4, "bed", "gag-route f432 rumble + breeze"))
    if cut == "A":
        C.append(cue(450, "N tile flutters past (paper flick)", F(file="trim/paper_flick.wav"), 0.35, 0.7, "impact", "gag-route f450 T14 flutters"))
    C.append(cue(480, "title card: ambience fades out", S("fade 0.6 s on all beds"), 0.0, 0.0, "bed", "gag-route f480"))
    C.append(cue(520, "final tile click on the tail", F(file="trim/tile_click_TAN.wav"), 0.5, 0.0, "impact", "gag-route f520 final tile click"))
    return sorted(C, key=lambda c: (c["frame"], c["purpose"]))


# ------------------------------------------------------------------ beds ---
# (trim file, start s, end s, gain, pan, fade-in s, fade-out s). Hard edges at the cuts.
def beds_for(cut):
    B = [("trim/bed_royale.wav", 0.0, fr(184), 0.50, 0.0, 0.05, 0.0)]          # rue Royale, gated at the hold
    if cut == "A":
        B += [("trim/bed_clichy.wav", fr(192), fr(252), 0.60, 0.0, 0.0, 0.5),   # HARD in at the jump cut
              ("trim/bed_tunnel.wav", fr(240), fr(298), 0.55, 0.0, 0.6, 0.0),    # push-in: inside the mouth
              ("trim/bed_chatelet.wav", fr(298), fr(480), 0.45, 0.0, 0.0, 0.6)]
    else:
        B += [("trim/bed_royale_cont.wav", fr(192), fr(298), 0.50, 0.0, 0.0, 0.0),  # continuity: same street
              ("trim/bed_chatelet.wav", fr(298), fr(480), 0.45, 0.0, 0.0, 0.6)]
    B += [("trim/hooves_ride.wav", fr(418), fr(480), 0.55, 0.3, 0.25, 0.6),
          ("trim/breeze_ride.wav", fr(432), fr(480), 0.40, 0.4, 0.4, 0.6),
          ("trim/wind_gust.wav", fr(158), fr(184), 0.55, 0.35, 0.15, 0.0)]
    return B


HOLDS = {"A": [(fr(184), fr(192)), (fr(328), fr(334))], "B": [(fr(184), fr(192))]}
# S3 'ambience thins' 6.0 -> 7.667: duck the street bed to -12 dB
THIN = (fr(144), fr(184), 0.25)


def wav_in(rel):
    p = SND / rel
    return load(p)


def place(m, x, t0, t1, gain, pan, fi, fo):
    n = int((t1 - t0) * SR)
    if len(x) < n:  # loop with a crossfade if a bed is short
        reps = int(np.ceil(n / len(x))) + 1
        x = np.concatenate([x] * reps)
    x = x[:n].copy()
    if fi > 0: x[:int(fi * SR)] *= np.linspace(0, 1, int(fi * SR))
    else: x[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    if fo > 0: x[-int(fo * SR):] *= np.linspace(1, 0, int(fo * SR))
    else: x[-int(0.002 * SR):] *= np.linspace(1, 0, int(0.002 * SR))
    m.add(x, t0, gain, pan)


GATE = {}


def render(cut, out=None, stems=False):
    m_bed, m_hit = kit.Mix(DUR, seed=1), kit.Mix(DUR, seed=2)
    for rel, t0, t1, g, p, fi, fo in beds_for(cut):
        x = wav_in(rel)
        if rel == "trim/bed_royale.wav":
            # thin the street from 6.0 s
            env = np.ones(int((t1 - t0) * SR))
            a, b = int((THIN[0] - t0) * SR), int((THIN[1] - t0) * SR)
            env[a:b] = np.linspace(1, THIN[2], b - a)
            xx = np.concatenate([x] * (int(np.ceil(len(env) / len(x))) + 1))[:len(env)] * env
            place(m_bed, xx, t0, t1, g, p, fi, fo)
        else:
            place(m_bed, x, t0, t1, g, p, fi, fo)
    C = cues_for(cut)
    for c in C:
        if "file" not in c or c["purpose"] == "bed":
            continue
        x = wav_in(c["file"])
        m_hit.add(x, c["t"], c["gain"], c["pan"])
    L = m_bed.L + m_hit.L; R = m_bed.R + m_hit.R
    # tail fade on the title card
    a, b = int(fr(480) * SR), int((fr(480) + 0.6) * SR)
    # (beds already fade; nothing else rings there except the final click)
    gate = np.ones(len(L))
    for h0, h1 in HOLDS[cut]:
        i0, i1 = int(round(h0 * SR)), int(round(h1 * SR))
        r = int(0.004 * SR)
        gate[i0 - r:i0] = np.minimum(gate[i0 - r:i0], np.linspace(1, 0, r))
        gate[i0:i1] = 0
        if not (cut == "A" and abs(h1 - fr(192)) < 1e-6):
            gate[i1:i1 + r] = np.minimum(gate[i1:i1 + r], np.linspace(0, 1, r))
    GATE[cut] = gate
    mix = kit.Mix(DUR); mix.L = L * gate; mix.R = R * gate
    st = mix.master()
    if out:
        with wave.open(str(out), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.astype("<i2").tobytes())
    hit = (m_hit.L + m_hit.R) * gate
    return st, hit, C


def check(cut, st, hit, C):
    x = st.astype(np.float64) / 32768.0
    mono = x.mean(1)
    res = {"holds": [], "cues": []}
    for h0, h1 in HOLDS[cut]:
        seg = x[int(round(h0 * SR)):int(round(h1 * SR))]
        res["holds"].append({"t0": round(h0, 4), "t1": round(h1, 4), "rms_dbfs": round(db(seg), 1) if np.any(seg) else -999.0,
                             "peak_dbfs": round(20 * math.log10(max(1e-12, np.abs(seg).max())), 1) if np.any(seg) else -999.0,
                             "pass": bool((not np.any(seg)) or db(seg) < -50)})
    for c in C:
        if "file" not in c or c["purpose"] == "bed":
            continue
        x1 = wav_in(c["file"]) * c["gain"]
        i0 = int(c["t"] * SR)
        stem = np.zeros(int(DUR * SR)); n = min(len(x1), len(stem) - i0); stem[i0:i0 + n] = x1[:n]
        stem *= GATE[cut]
        # onset of this cue alone, as it sits in the mix (after the hold gates)
        o = onset(stem[max(0, i0 - int(SR / FPS)):i0 + int(0.5 * SR)], 0.25, 32)
        if o is not None and np.abs(stem).max() > 0:
            t_on = (max(0, i0 - int(SR / FPS)) + o) / SR; err = (t_on - c["t"]) * FPS
        else:
            t_on, err = None, None
        # and in the full mix: the frame of the largest positive flux within +-1 frame
        w0, w1 = int((c["t"] - 1 / FPS) * SR), int((c["t"] + 1 / FPS) * SR)
        e = np.sqrt(np.convolve(mono[w0:w1] ** 2, np.ones(64) / 64, "same"))
        fl = np.diff(e, prepend=e[0])
        mix_peak = (w0 + int(np.argmax(fl))) / SR
        res["cues"].append({"frame": c["frame"], "cue": c["cue"], "onset_s": None if t_on is None else round(t_on, 4),
                            "error_frames": None if err is None else round(err, 3), "mix_flux_peak_s": round(mix_peak, 4),
                            "mix_flux_error_frames": round((mix_peak - c["t"]) * FPS, 2), "pass": bool(err is not None and abs(err) <= 1.0)})
    # hard ambience change at 8.0 s: level and spectral centroid before (6.9-7.6) vs after (8.0-8.7)
    def cen(seg):
        X = np.abs(np.fft.rfft(seg)); f = np.fft.rfftfreq(len(seg), 1 / SR); return float((X * f).sum() / max(X.sum(), 1e-9))
    pre, post = mono[int(6.9 * SR):int(7.6 * SR)], mono[int(8.0 * SR):int(8.7 * SR)]
    first = mono[int(8.0 * SR):int((8.0 + 1 / FPS) * SR)]
    res["jump_cut_8s"] = {"pre_rms_dbfs": round(db(pre), 1), "post_rms_dbfs": round(db(post), 1), "first_frame_after_rms_dbfs": round(db(first), 1),
                          "pre_centroid_hz": round(cen(pre)), "post_centroid_hz": round(cen(post)),
                          "hard": bool(db(first) > -40 and db(mono[int(7.95 * SR):int(8.0 * SR)]) < -90)}
    return res


# --------------------------------------------------------------- ledger ---
def C_(page):
    return "https://commons.wikimedia.org/wiki/" + page


LEDGER = [
    dict(id="SND-SOUFFLOT", title="La rue Soufflot (Paris).ogg", author="Jean-Pierre Bazard (Jpbazard)", license="CC BY-SA 3.0",
         license_url="https://creativecommons.org/licenses/by-sa/3.0", source_url=C_("File:La_rue_Soufflot_(Paris).ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/2/29/La_rue_Soufflot_%28Paris%29.ogg", local="raw/La_rue_Soufflot_(Paris).ogg",
         what_it_shows="Street sounds of rue Soufflot recorded on a Sunday morning, November 2009, from the steps of the Pantheon, Paris (71.6 s).",
         verified_date_or_place="2009-11-22, rue Soufflot / Pantheon steps, Paris (Commons description)"),
    dict(id="SND-HOOVES", title="WWS Horseshoesonstonepavedstreet.ogg", author="Work With Sounds / Torsten Nilsson", license="CC BY 4.0",
         license_url="https://creativecommons.org/licenses/by/4.0", source_url=C_("File:WWS_Horseshoesonstonepavedstreet.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/5/50/WWS_Horseshoesonstonepavedstreet.ogg", local="raw/WWS_Horseshoesonstonepavedstreet.ogg",
         what_it_shows="Fiaker (horse cab) horseshoes on the stone-paved street at the Stephansplatz cab stand, Vienna (129 s).",
         verified_date_or_place="2014-09-08, Stephansplatz, Vienna (Commons description)"),
    dict(id="SND-TRAMBELL", title="Sydney tram 18 - 2016-02-14-2.ogg", author="Andy Mabbett", license="CC BY-SA 4.0",
         license_url="https://creativecommons.org/licenses/by-sa/4.0", source_url=C_("File:Sydney_tram_18_-_2016-02-14-2.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/6/62/Sydney_tram_18_-_2016-02-14-2.ogg", local="raw/Sydney_tram_18_-_2016-02-14-2.ogg",
         what_it_shows="Tram 18 at Central Station, Sydney: the driver sounds the warning bell several times before the doors close (2.1 s).",
         verified_date_or_place="2016-02-14, Central Station, Sydney (Commons description)"),
    dict(id="SND-FIREBELL", title="WWS Firedepartmentbell.ogg", author="Work With Sounds / Konrad Gutkowski", license="CC BY 4.0",
         license_url="https://creativecommons.org/licenses/by/4.0", source_url=C_("File:WWS_Firedepartmentbell.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/8/8a/WWS_Firedepartmentbell.ogg", local="raw/WWS_Firedepartmentbell.ogg",
         what_it_shows="Hand-rung warning bell of a late-19th-century two-axle horse-drawn fire engine, fire department museum, Hattingen (20 s).",
         verified_date_or_place="2015-05-26, Feuerwehrmuseum Hattingen (Commons description)"),
    dict(id="SND-CUTPAPER", title="Rejection letter cut into pieces.ogg", author="hugh (pdsounds.org)", license="Public domain",
         license_url="", source_url=C_("File:Rejection_letter_cut_into_pieces.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/a/a6/Rejection_letter_cut_into_pieces.ogg", local="raw/Rejection_letter_cut_into_pieces.ogg",
         what_it_shows="A paper letter being cut into pieces with scissors, with rustling (21.8 s).", verified_date_or_place="2008-05-06 (pdsounds.org #550)"),
    dict(id="SND-HCDROP", title="Hardcover books dropped.ogg", author="stilgar (pdsounds.org)", license="Public domain", license_url="",
         source_url=C_("File:Hardcover_books_dropped.ogg"), file_url="https://upload.wikimedia.org/wikipedia/commons/5/55/Hardcover_books_dropped.ogg",
         local="raw/Hardcover_books_dropped.ogg", what_it_shows="A couple of hardcover books dropped onto a wood floor (7.6 s).",
         verified_date_or_place="2008-08-28 (pdsounds.org #629)"),
    dict(id="SND-SCDROP", title="Softcover books dropped.ogg", author="stilgar (pdsounds.org)", license="Public domain", license_url="",
         source_url=C_("File:Softcover_books_dropped.ogg"), file_url="https://upload.wikimedia.org/wikipedia/commons/4/4b/Softcover_books_dropped.ogg",
         local="raw/Softcover_books_dropped.ogg", what_it_shows="Some softcover books dropped on a wood floor (5.3 s).",
         verified_date_or_place="2008-08-28 (pdsounds.org #630)"),
    dict(id="SND-PAGE", title="Turning a page.ogg", author="planish (pdsounds.org)", license="Public domain", license_url="",
         source_url=C_("File:Turning_a_page.ogg"), file_url="https://upload.wikimedia.org/wikipedia/commons/6/6b/Turning_a_page.ogg",
         local="raw/Turning_a_page.ogg", what_it_shows="Turning a page in a hard-cover book (3.4 s).", verified_date_or_place="2007-07-05 (pdsounds.org #304)"),
    dict(id="SND-OLDBOOK", title="Old book.ogg", author="cori (pdsounds.org)", license="Public domain", license_url="",
         source_url=C_("File:Old_book.ogg"), file_url="https://upload.wikimedia.org/wikipedia/commons/b/bf/Old_book.ogg",
         local="raw/Old_book.ogg", what_it_shows="Leafing through pages, flicking pages, shutting a book (73.6 s).", verified_date_or_place="2008-07-21 (pdsounds.org #603)"),
    dict(id="SND-STAIRS", title="Pasos en escalera de caracol.ogg", author="Hippocampuz", license="CC BY-SA 4.0",
         license_url="https://creativecommons.org/licenses/by-sa/4.0", source_url=C_("File:Pasos_en_escalera_de_caracol.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/0/0a/Pasos_en_escalera_de_caracol.ogg", local="raw/Pasos_en_escalera_de_caracol.ogg",
         what_it_shows="Footsteps going up and down a spiral staircase (18.0 s).", verified_date_or_place="2022-08-24 (Commons, own work)"),
    dict(id="SND1", title="Strong winds before the Rain.ogg", author="SAgbley", license="CC BY-SA 4.0",
         license_url="https://creativecommons.org/licenses/by-sa/4.0", source_url=C_("File:Strong_winds_before_the_Rain.ogg"),
         file_url="https://upload.wikimedia.org/wikipedia/commons/1/1d/Strong_winds_before_the_Rain.ogg",
         local="../test-shot/sound/wind.ogg", what_it_shows="Strong wind before rain (audio track of a 5.6 s video); broadband wind, no voices (spectrogram checked).",
         verified_date_or_place="2023-04-04 (Commons); reused from the approved test shot, licence re-read from the test-shot ledger"),
    dict(id="MIA-VALLEYTOWN", title="Valley Town (1940)", author="via movingimagearchive.com",
         license="Rights as listed by movingimagearchive.com (largely public domain); not independently verified", license_url="",
         source_url="https://www.movingimagearchive.com/sources/valley-town-9978c98d?clip=a11ba534-ceca-5859-a69f-9d622f30c4e7", file_url="",
         local="mia/valley_town_1940_a11ba534.wav",
         status_note="NOT USED (repair round 1): clip identity vs the PD Prelinger item archive.org/details/ValleyTo1940 not confirmable (movingimagearchive page 403); replaced by synthesis",
         what_it_shows="Source sound of a factory roof shot (steam vent/whistle stack), source time 1130.30-1133.97 s: a steady broadband industrial roar, no speech or music (spectrogram checked).",
         verified_date_or_place="1940 per archive index; unverified place"),
]


# ---------------------------------------------------------------- trims ---
PROV = {}   # trim name -> provenance dict


def have(rel):
    p = SND / rel
    return p.exists() and p.stat().st_size > 5000


def put(name, x, prov):
    save(TRIM / name, x)
    PROV["trim/" + name] = prov


def synth_mix(seconds, fn, seed=0):
    m = kit.Mix(seconds, seed=seed); fn(m)
    return (m.L + m.R) / 2


def trim_with(src_id, rel, ss, t, note):
    return {"source": src_id, "from": rel, "ss": ss, "t": t, "processing": note}


def build_trims():
    W = "../test-shot/sound/wind.ogg"
    # -- wind gust (S3) and ride breeze (S8): SND1 -----------------------
    w = load(SND / W)
    g = fade(norm(highpass(w[int(0.2 * SR):int(1.3 * SR)], 120), 0.8), 0.12, 0.05)
    put("wind_gust.wav", g, trim_with("SND1", W, 0.2, 1.1, "highpass 120 Hz, peak -2 dB, 0.12 s rise"))
    b = norm(lowpass(highpass(w[int(1.6 * SR):int(4.4 * SR)], 90), 1800), 0.6)
    put("breeze_ride.wav", fade(b, 0.3, 0.3), trim_with("SND1", W, 1.6, 2.8, "band 90-1800 Hz (softer breeze)"))
    # -- tunnel resonance (repair round 1): SYNTH. The MIA Valley Town roar was dropped because the identity of the
    #    movingimagearchive clip with the PD Prelinger item could not be confirmed; brown noise through the same
    #    40-380 Hz band and 98 Hz comb (paper throat) replaces it.
    v = kit.Mix(3.67, seed=98).noise(3.67, "brown")
    v = v + 0.35 * kit.Mix(3.67, seed=99).noise(3.67, "pink")
    v = lowpass(highpass(v, 40), 380)
    d = int(SR / 98)  # throat resonance ~98 Hz
    y = v.copy()
    for k in range(1, 6):
        y[k * d:] += (0.55 ** k) * v[:-k * d]
    put("bed_tunnel.wav", fade(norm(y, 0.7), 0.05, 0.05),
        {"synth": "kit Mix brown+pink noise, band 40-380 Hz, 5-tap comb at 98 Hz (tunnel throat); replaces MIA-VALLEYTOWN (repair round 1)"})
    build_street()
    build_bells()
    build_paper()
    build_steps()


def build_street():
    S = "raw/La_rue_Soufflot_(Paris).ogg"
    H = "raw/WWS_Horseshoesonstonepavedstreet.ogg"
    if have(S):
        x = load(SND / S)
        put("bed_royale.wav", fade(norm(x[int(2 * SR):int(10 * SR)], 0.5), 0.05, 0.05), trim_with("SND-SOUFFLOT", S, 2.0, 8.0, "peak -6 dB"))
        put("bed_royale_cont.wav", fade(norm(x[int(10 * SR):int(15 * SR)], 0.5), 0.0, 0.05), trim_with("SND-SOUFFLOT", S, 10.0, 5.0, "continues the S1-S3 bed"))
        put("bed_chatelet.wav", fade(norm(x[int(40 * SR):int(48 * SR)], 0.45), 0.0, 0.3), trim_with("SND-SOUFFLOT", S, 40.0, 8.0, "peak -7 dB"))
    else:
        mk = lambda m: (m.room(0, 8, gain=0.5), m.murmur(0, 8, gain=0.0))
        x = synth_mix(8, lambda m: m.room(0, 8, gain=0.6), 3)
        put("bed_royale.wav", norm(x, 0.25), {"synth": "kit Mix.room (no street recording downloaded)"})
        put("bed_royale_cont.wav", norm(x, 0.4), {"synth": "kit Mix.room"})
        put("bed_chatelet.wav", norm(synth_mix(8, lambda m: m.room(0, 8, gain=0.6, hum=60), 4), 0.35), {"synth": "kit Mix.room"})
    if have(H):
        h = load(SND / H)
        put("hooves_ride.wav", fade(norm(h[int(20 * SR):int(24 * SR)], 0.6), 0.2, 0.3), trim_with("SND-HOOVES", H, 20.0, 4.0, "peak -4 dB"))
        busy = h[int(60 * SR):int(63 * SR)]
        base = load(SND / S)[int(25 * SR):int(28 * SR)] if have(S) else np.zeros_like(busy)
        n = min(len(busy), len(base))
        put("bed_clichy.wav", fade(norm(0.7 * norm(busy[:n]) + 0.6 * norm(base[:n]), 0.75), 0.0, 0.1),
            {"source": "SND-HOOVES + SND-SOUFFLOT", "from": [H, S], "ss": [60.0, 25.0], "t": 3.0, "processing": "two real recordings summed: square with horse cabs over Paris street; hard start, louder and brighter than the Royale bed"})
    else:
        def clop(m):
            for k in range(12):
                m.step(0.25 * k + 0.02 * (k % 2), gain=0.5, surface="stone")
        put("hooves_ride.wav", norm(synth_mix(3, clop, 5), 0.5), {"synth": "kit Mix.step on stone, trot rhythm"})
        put("bed_clichy.wav", norm(synth_mix(3, lambda m: (m.room(0, 3, gain=0.6), m.steps(0.05, 3, every=0.25, gain=0.25)), 6), 0.6), {"synth": "kit Mix.room + steps"})


def pick_event(x, k=0, length=0.25, rel=0.3, min_gap=0.08, strongest=False):
    ev = events(x, min_gap=min_gap, rel=rel)
    if not ev:
        return None, None
    if strongest:
        ev = sorted(ev, key=lambda e: -e[1])
    i = ev[min(k, len(ev) - 1)][0]
    return oneshot(x, i, length=length), i / SR


def distance(x, hz=2200, amt=0.35):
    """Far-off version: low-pass and a little early reflection."""
    y = lowpass(x, hz); d = int(0.031 * SR)
    y[d:] += amt * y[:-d]
    return y


BELL_PICK = {"k": 0}


def build_bells():
    T = "raw/Sydney_tram_18_-_2016-02-14-2.ogg"
    Fb = "raw/WWS_Firedepartmentbell.ogg"
    src = T if have(T) else (Fb if have(Fb) else None)
    if src:
        x = highpass(load(SND / src), 150)
        one, at = pick_event(x, BELL_PICK["k"], length=1.1, rel=0.35, min_gap=0.15)
        sid = "SND-TRAMBELL" if src == T else "SND-FIREBELL"
        one = norm(one, 0.85)
        put("bell_tram_1.wav", fade(one, 0.0005, 0.25), trim_with(sid, src, round(at, 3), 1.1, "single strike, onset-aligned to sample 0"))
        put("bell_tram_2.wav", fade(norm(distance(one, 1800, 0.45), 0.5), 0.0005, 0.3), trim_with(sid, src, round(at, 3), 1.1, "same strike, low-passed 1.8 kHz + 31 ms reflection (distance)"))
        two, at2 = pick_event(x, BELL_PICK["k"], length=0.9, rel=0.35, min_gap=0.15)
        put("bell_tram_3.wav", fade(norm(one[:int(0.9 * SR)], 0.95), 0.0005, 0.25), trim_with(sid, src, round(at, 3), 0.9, "close strike, full band"))
    else:
        for n, (g, far) in {"bell_tram_1.wav": (0.9, False), "bell_tram_2.wav": (0.5, True), "bell_tram_3.wav": (0.95, False)}.items():
            s = synth_mix(1.2, lambda m: m.bell(0, freq=1250, seconds=1.2, gain=0.9), 7)
            put(n, norm(distance(s) if far else s, g), {"synth": "kit Mix.bell 1250 Hz (no bell recording downloaded)"})


PAPER = {}


def build_paper():
    CP = "raw/Rejection_letter_cut_into_pieces.ogg"
    PG = "raw/Turning_a_page.ogg"
    OB = "raw/Old_book.ogg"
    HC = "raw/Hardcover_books_dropped.ogg"
    SC = "raw/Softcover_books_dropped.ogg"
    # crisp tick: a scissor snip / page edge -> tile clicks, dominoes
    tick = None
    for rel, sid, k in ((CP, "SND-CUTPAPER", PAPER.get("cp_k", 0)), (OB, "SND-OLDBOOK", PAPER.get("ob_k", 0))):
        if have(rel):
            x = highpass(load(SND / rel), 400)
            tick, at = pick_event(x, k, length=0.12, rel=0.35, strongest=True)
            tick = norm(tick, 0.9); tprov = trim_with(sid, rel, round(at, 3), 0.12, "one transient, highpass 400 Hz")
            break
    if tick is None:
        tick = norm(synth_mix(0.08, lambda m: m.click(0, gain=0.9, bright=6000, seconds=0.06), 8), 0.9)
        tprov = {"synth": "kit Mix.click"}
    ratios = {"DOU": 1.0, "KI": 1.19, "PU": 1.12, "DONK": 0.94, "TAN": 1.33}
    for syl, r in ratios.items():
        p = dict(tprov); p["processing"] = (p.get("processing", "") + f"; tape-speed pitch x{r}").strip("; ")
        put(f"tile_click_{syl}.wav", fade(resample_pitch(tick, r), 0.0003, 0.02), p)
    for k in range(7):
        r = 1.0 + 0.09 * k
        p = dict(tprov); p["processing"] = (p.get("processing", "") + f"; pitch x{r:.2f} (rising domino)").strip("; ")
        put(f"domino_{k+1}.wav", fade(resample_pitch(tick, r) * (0.8 + 0.03 * k), 0.0003, 0.02), p)
    put("paper_tick_1.wav", fade(resample_pitch(tick, 1.5) * 0.6, 0.0003, 0.02), dict(tprov, processing="gulp: tick at x1.5, -4 dB"))
    # snaps and flicks: a page turn
    if have(PG):
        x = highpass(load(SND / PG), 200)
        snap, at = pick_event(x, 0, length=0.18, rel=0.3, strongest=True)
        put("paper_snap_1.wav", fade(norm(snap, 0.9), 0.0005, 0.04), trim_with("SND-PAGE", PG, round(at, 3), 0.18, "strongest page-snap transient"))
        put("paper_snap_2.wav", fade(norm(resample_pitch(snap, 0.9), 0.85), 0.0005, 0.04), trim_with("SND-PAGE", PG, round(at, 3), 0.2, "same snap, pitch x0.9"))
        o = onset(x, 0.1) or 0
        put("paper_flick.wav", fade(norm(x[o:o + int(0.7 * SR)], 0.7), 0.002, 0.15), trim_with("SND-PAGE", PG, round(o / SR, 3), 0.7, "whole page turn"))
    else:
        for n in ("paper_snap_1.wav", "paper_snap_2.wav"):
            put(n, norm(synth_mix(0.1, lambda m: m.click(0, gain=0.9, bright=8000, seconds=0.08), 9), 0.85), {"synth": "kit Mix.click"})
        put("paper_flick.wav", norm(synth_mix(0.6, lambda m: (m.click(0, gain=0.9, bright=7000, seconds=0.05), m.whoosh(0.0, 0.5, gain=0.35)), 10), 0.6), {"synth": "kit Mix.click + whoosh"})
    # clatter and thuds: book drops on a wood floor
    drops = [(rel, sid) for rel, sid in ((SC, "SND-SCDROP"), (HC, "SND-HCDROP")) if have(rel)]
    if drops:
        evs = []
        for rel, sid in drops:
            x = load(SND / rel)
            for i, e in events(x, min_gap=0.05, rel=0.12):
                evs.append((e, rel, sid, i, x))
        evs.sort(key=lambda e: -e[0])
        for k in range(4):
            e, rel, sid, i, x = evs[min(k + 1, len(evs) - 1)]
            put(f"clatter_{k+1}.wav", fade(norm(highpass(oneshot(x, i, length=0.12), 300), 0.8), 0.0003, 0.03),
                trim_with(sid, rel, round(i / SR, 3), 0.12, "one hit of the book drop, highpass 300 Hz"))
        e, rel, sid, i, x = evs[0]
        hit = oneshot(x, i, length=0.35)
        put("card_thud.wav", fade(norm(lowpass(hit, 900), 0.7), 0.0005, 0.08), trim_with(sid, rel, round(i / SR, 3), 0.35, "strongest drop hit, low-passed 900 Hz (jaw drop)"))
        # contact: clack + thud, gated to < 2 frames so the 0.25 s hold is clean
        L = int(0.075 * SR)
        clack = np.zeros(L); clack[:min(L, len(tick))] += tick[:L] * 0.8
        h = hit[:L]; clack[:len(h)] += norm(h, 0.9)
        put("impact_contact.wav", fade(norm(clack, 0.95), 0.0003, 0.02),
            {"source": f"{sid} + {tprov.get('source', 'synth')}", "from": [rel, tprov.get("from")], "ss": [round(i / SR, 3), tprov.get("ss")], "t": 0.075,
             "processing": "book-drop hit summed with the paper tick, gated to 75 ms (ends before the hold at f328)"})
        put("step_deck.wav", fade(norm(lowpass(hit, 2500), 0.7), 0.0005, 0.06), trim_with(sid, rel, round(i / SR, 3), 0.35, "drop hit on wood floor, low-passed 2.5 kHz (step on the deck)"))
    else:
        for k in range(4):
            put(f"clatter_{k+1}.wav", norm(synth_mix(0.06, lambda m: m.click(0, gain=0.9, bright=3000 + 700 * k, seconds=0.05), 11 + k), 0.8), {"synth": "kit Mix.click"})
        put("card_thud.wav", norm(synth_mix(0.3, lambda m: m.thud(0, freq=110, gain=0.9, seconds=0.3), 15), 0.7), {"synth": "kit Mix.thud"})
        def ct(m):
            m.thud(0, freq=90, gain=0.9, seconds=0.075); m.click(0, gain=0.8, bright=5000, seconds=0.04)
        put("impact_contact.wav", norm(synth_mix(0.075, ct, 16), 0.95), {"synth": "kit Mix.thud + click, 75 ms"})
        put("step_deck.wav", norm(synth_mix(0.12, lambda m: m.step(0, gain=0.9, surface="wood"), 17), 0.7), {"synth": "kit Mix.step wood"})


def build_steps():
    ST = "raw/Pasos_en_escalera_de_caracol.ogg"
    if have(ST):
        x = highpass(load(SND / ST), 80)
        ev = sorted(events(x, min_gap=0.2, rel=0.25), key=lambda e: -e[1])[:12]
        ev = sorted(ev)
        for k in range(4):
            i = ev[k][0]
            s = oneshot(x, i, length=0.16)
            put(f"step_stone_{k+1}.wav", fade(norm(lowpass(s, 3500), 0.8), 0.0005, 0.03), trim_with("SND-STAIRS", ST, round(i / SR, 3), 0.16, "one footstep, low-passed 3.5 kHz"))
        for k in range(4):
            i = ev[4 + k][0]
            s = oneshot(x, i, length=0.22)
            # hollow card: band it and add a short box resonance
            y = highpass(s, 250); d = int(SR / 420)
            for j in range(1, 5):
                y[j * d:] += (0.5 ** j) * y[:-j * d]
            put(f"step_card_{k+1}.wav", fade(norm(y, 0.8), 0.0005, 0.05), trim_with("SND-STAIRS", ST, round(i / SR, 3), 0.22, "one footstep, highpass 250 Hz + 4-tap comb at 420 Hz (hollow card box)"))
    else:
        for k in range(4):
            put(f"step_stone_{k+1}.wav", norm(synth_mix(0.1, lambda m: m.step(0, gain=0.9, surface="stone"), 20 + k), 0.8), {"synth": "kit Mix.step stone"})
            put(f"step_card_{k+1}.wav", norm(synth_mix(0.12, lambda m: m.step(0, gain=0.9, surface="wood"), 30 + k), 0.8), {"synth": "kit Mix.step wood (hollow card)"})


ABSENCES = [
    {"searched": "Moving Image Archive cache: clips with source sound whose title/queries match street|traffic|city|horse|tram|trolley|bell|crowd|paris|bus|carriage|paper|market|square|town (47 hits), plus every pre-1964 'sound'-kind clip ranked by spectral flatness (40)",
     "result": "spectrograms checked: nearly all carry narration, music or crowd speech (Formations 1936, Coney Island, Uruguay 1949, Golden Gate City, This Is My Railroad 1940, Day at the Fair 1947, Boulder Dam, Look to Lockheed 1940...). Only Valley Town (1940) a11ba534 is a clean non-vocal roar; it was used for the tunnel in round 3 but dropped in repair round 1 (clip identity vs the PD Prelinger item not confirmable) and replaced by synthesis. Third Avenue El (14c8b94b) is a clean train rumble but its year/rights are not in the index and the film (1955) is not known to be PD: rejected."},
    {"searched": "Commons audio: 'Paris street ambience', 'place Paris ambiance', 'city square soundscape', 'street ambience'", "result": "only La rue Soufflot (Paris) fits (CC BY-SA 3.0); no pre-1964 Paris street recording under an allowed licence was found. Clichy's 'busier square' is built from two real recordings (Soufflot + Vienna fiaker stand)."},
    {"searched": "Commons audio: 'tram bell', 'streetcar bell', 'hand bell', 'tram Glocke'", "result": "no horse-tram or Paris tram bell; used a modern Sydney tram warning bell (CC BY-SA 4.0) and kept the 19th-c. horse-drawn fire-engine hand bell (CC BY 4.0) as alternate. De-Handglocke.ogg rejected: it is a spoken pronunciation (voice)."},
    {"searched": "Commons audio: 'domino', 'wooden blocks', 'playing cards', 'cardboard', 'paper tearing'", "result": "no domino/card-tile clack recording under an allowed licence; domino ticks and tile clicks are pitched copies of one real paper transient (scissor snip / page edge)."},
    {"searched": "Commons audio: 'footsteps', 'walking on cobblestones'", "result": "no clean footsteps on cobbles; used real footsteps on a spiral staircase (CC BY-SA 4.0). Praha cobble ambience (PD, 341 s, 6.6 MB) skipped for size."},
    {"searched": "voice", "result": "no voice of any kind is used (no TTS, no child's voice, crowd-walla clips rejected)."},
]


def write_output(out):
    rec = []
    used = set()
    for p in PROV.values():
        s = p.get("source", "")
        for part in str(s).split(" + "):
            used.add(part.strip())
    for L in LEDGER:
        if L["id"] not in used:
            continue
        lp = str((SND / L["local"]).resolve())
        rec.append({"id": L["id"], "title": L["title"], "author": L["author"], "license": L["license"], "license_url": L["license_url"],
                    "source_url": L["source_url"], "file_url": L["file_url"], "local_path": lp, "what_it_shows": L["what_it_shows"],
                    "verified_date_or_place": L["verified_date_or_place"],
                    "used_as": "; ".join(sorted(k for k, v in PROV.items() if L["id"] in str(v.get("source", ""))))})
    synth = sorted(k for k, v in PROV.items() if "synth" in v)
    doc = {
        "slug": "zazie-dans-le-metro", "unit": "SOUND (impacts and holds)", "fps": FPS, "rate": SR, "duration_s": DUR,
        "timing_source": "gag-route.json (U1) timecoded_gag_cues + exposure_sheet; t = frame/24",
        "deviations": [
            "Offscreen tram bell at f8 (0.333 s), as gag-route places it; the brief's 0.35 s is f8.4, within 1 frame. Panned LEFT per U1 (V enters L->R from behind her).",
            "Syllable clicks follow U1's compressed timing DOU f254 (10.583 s) ... TAN f275 (11.458 s), not the brief's 10.6-11.9 s.",
            "The 0.25 s hold after the contact is f328-333 (13.667-13.917 s): the 75 ms contact clack (f326-327) finishes first, then total silence.",
            "Cut B has no 13.6 s impact or hold (she joins the queue; no collision); it keeps the 7.667-8.000 s silence because frames 0-191 are identical to A.",
        ],
        "how_to_mix": "Beds are placed as windows (beds); one-shots as cues. All layers are multiplied by a gate that is exactly 0 inside each hold (4 ms ramp before; the 8.0 s jump-cut bed starts hard with a 2 ms ramp). build_sound.py renders it with kit.Mix (add + master). Gains are linear, pan -1 left..+1 right as kit.Mix.add.",
        "build_script": str(SW / "sound-build/build_sound.py"),
        "media_dir": str(SND),
        "preview": {"A": str(SND / "soundbed-preview.wav"), "B": str(SND / "soundbed-preview-B.wav")},
        "holds": {k: [[round(a, 4), round(b, 4)] for a, b in v] for k, v in HOLDS.items()},
        "beds": {cut: [dict(file=b[0], t0=round(b[1], 4), t1=round(b[2], 4), gain=b[3], pan=b[4], fade_in=b[5], fade_out=b[6]) for b in beds_for(cut)] for cut in ("A", "B")},
        "cues": {cut: out[cut][0] for cut in out},
        "checks": {cut: out[cut][1] for cut in out},
        "trims": PROV,
        "synth_items": synth,
        "evidence": rec,
        "handmade": [
            {"what": "pitched tile-click set (DOU KI PU DONK TAN) and 7 rising domino ticks", "how": "one real paper transient re-pitched by tape-speed resampling", "where": str(TRIM)},
            {"what": "hollow card-step set", "how": "real footsteps band-passed with a 420 Hz 4-tap comb (card box)", "where": str(TRIM)},
            {"what": "tunnel throat resonance", "how": "synthesized brown/pink noise low-passed 380 Hz with a 98 Hz comb (kit Mix)", "where": str(TRIM / "bed_tunnel.wav")},
            {"what": "the mix and its gates", "how": "kit.Mix, build_sound.py", "where": str(SND / "soundbed-preview.wav")},
        ],
        "absences": ABSENCES,
        "licence_ledger": [dict({k: v for k, v in L.items() if k != "local"}, local_path=str((SND / L["local"]).resolve()),
                                status=("in use" if L["id"] in used else ("downloaded, not used" if have(L["local"]) else "licence read from Commons extmetadata 2026-11-16; download blocked by upload.wikimedia.org HTTP 429 (retry-after 600 s), rerun build_sound.py after fetching"))) for L in LEDGER],
        "pending_downloads": [L["file_url"] for L in LEDGER if L["local"].startswith("raw/") and not have(L["local"])],
    }
    for cut in ("A", "B"):
        for c in doc["cues"][cut]:
            if "file" in c:
                c["file"] = "sound/" + c["file"]
            c["source"] = PROV.get(c["file"].replace("sound/", ""), {}).get("source", "synth" if "synth" in PROV.get(c.get("file", "").replace("sound/", ""), {}) else None) if "file" in c else None
    json.dump(doc, open(SW / "sound-cues.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    build_trims()
    out = {}
    for cut in ("A", "B"):
        st, hit, C = render(cut, SND / ("soundbed-preview.wav" if cut == "A" else "soundbed-preview-B.wav"))
        out[cut] = (C, check(cut, st, hit, C))
        print(cut, "holds", out[cut][1]["holds"])
        bad = [c for c in out[cut][1]["cues"] if not c["pass"]]
        print(cut, "cues", len(out[cut][1]["cues"]), "fail", bad)
    write_output(out)
