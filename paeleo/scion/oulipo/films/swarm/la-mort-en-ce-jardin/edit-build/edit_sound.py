# Montage editor (edit-r2) sound for la-mort-en-ce-jardin.  Rebuilds U3's stems on the edit-r2 timeline with the
# critic's repairs: foraged jungle / splash / lap recordings when present in sources/.../object-sound/raw/ (decoded only,
# with ffmpeg), the bag rustle onset locked to the logged holder-change frame, the splash locked to the last crosser's
# minimum-clearance frame of the gate-checked trace (the same frame the ledger reports) and >= 8 dB over the steps.
# U3's synthesized foley generators are reused unchanged: only the function definitions of object-sound/sound.py are
# executed (its module-level render is not).
import ast, json, math, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
SRC = os.path.join(FILMS, "sources", "la-mort-en-ce-jardin")
OS_ = os.path.join(SRC, "object-sound")
T_FILM = 73.0
OFF = {"L": 2.0, "E": 39.5}
FPS = 24


def _u3_generators(Mix, RATE):
    src = open(os.path.join(SW, "object-sound", "sound.py")).read()
    tree = ast.parse(src)
    mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    ns = dict(np=np, math=math, RATE=RATE, M=Mix(T_FILM, seed=56), rs=np.random.RandomState(1956), subprocess=subprocess)
    exec(compile(mod, "object-sound/sound.py (function defs only)", "exec"), ns)
    return ns


def decode(path, ss=0.0, dur=None, RATE=44100):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss)] + (["-t", str(dur)] if dur else []) + ["-i", path, "-ac", "2", "-ar", str(RATE), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-12)


def db(x):
    return 20 * math.log10(x + 1e-12)


def build(TR, SPLASH, Mix, RATE, SEG_E_REWRITE=(52.9, 54.5)):
    G = _u3_generators(Mix, RATE)
    M = G["M"]; rs = G["rs"]
    N = int(T_FILM * RATE)
    cues = []

    def cue(t, kind, what, v, source, dur=None, **kw):
        cues.append(dict(film_t=round(t, 3), dur=None if dur is None else round(dur, 3), version=v, kind=kind, what=what, source=source, **kw))

    def put(stem, sig, at, gain=1.0, pan=0.0):
        i = int(round(at * RATE))
        if sig.ndim == 1:
            lg, rg = math.cos((pan + 1) * math.pi / 4) * 1.414, math.sin((pan + 1) * math.pi / 4) * 1.414
            sig = np.stack([sig * lg, sig * rg], 1)
        k = min(len(sig), len(stem) - i)
        if k > 0 and i >= 0: stem[i:i + k] += sig[:k] * gain

    F = dict(stream=os.path.join(SRC, "test-shot", "audio", "stream.mp3"),
             jungle=os.path.join(OS_, "raw", "jungle_phuket.flac"),
             tide=os.path.join(OS_, "raw", "tide_rocks.ogg"),
             splash=os.path.join(OS_, "raw", "splashes.ogg"))
    have = {}
    for k, p in F.items():
        ok = os.path.exists(p) and os.path.getsize(p) > 20000
        if ok:
            try: decode(p, 0, 0.5, RATE)
            except Exception: ok = False
        have[k] = ok
    used = {}

    # ---------------- water
    water = np.zeros((N, 2))
    st = decode(F["stream"], 12.0, 30.0, RATE); st = st - st.mean(0); st *= 10 ** (-30 / 20) / rms(st)
    water += G["loop_to"](st, N)
    used["stream"] = "stream.mp3 12.0-42.0 s looped (0.5 s crossfades), -30 dBFS RMS"
    wenv = [(0, -40), (2.0, 0), (26.0, 0), (29.0, 3.5), (38.0, 4.5), (38.2, -9), (39.5, -9), (39.7, 0), (64.3, 0), (66.0, 3.0), (69.5, 3.0), (73.0, -40)]
    water *= G["envelope"](N, wenv)[:, None]
    cue(0.0, "ambience", "water bed (stream) fades in under the title", "T", "FOR-AUD-STREAM", 2.0)
    cue(26.0, "ambience", "water louder as the flood rises", "L", "FOR-AUD-STREAM", 12.0)
    cue(64.3, "ambience", "water louder for C's last crossing", "E", "FOR-AUD-STREAM", 5.2)
    for v, t0 in (("L", 20.0), ("E", 50.5)):
        if have["tide"]:
            lap = decode(F["tide"], 6.0, 2.4, RATE); lap = lap - lap.mean(0); lap *= 10 ** (-28 / 20) / rms(lap)
            used["tide"] = "tide_rocks.ogg 6.0-8.4 s, -28 dBFS RMS"; src = "FOR-AUD-TIDE"
        else:
            lap = np.stack([M.band(M.noise(2.4), 150, 900) * 0.04] * 2, 1); src = "HM-SYN-LAP"
        lap *= np.r_[np.linspace(0, 1, 2200), np.ones(len(lap) - 4400), np.linspace(1, 0, 2200)][:, None]
        put(water, lap, t0)
        cue(t0, "water", "close lap at the plank foot (L-S5 / E-S4)", v, src, 2.4)

    # ---------------- jungle
    jungle = np.zeros((N, 2))
    if have["jungle"]:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", F["jungle"]],
                                   capture_output=True, text=True).stdout.strip() or 40)
        j = decode(F["jungle"], 1.0, min(60.0, dur - 1.5), RATE); j = j - j.mean(0); j *= 10 ** (-31 / 20) / rms(j)
        jungle += G["loop_to"](j, N)
        used["jungle"] = f"Jungle Sound Thailand Phuket.flac 1.0-{1.0 + min(60.0, dur - 1.5):.1f} s looped, -31 dBFS RMS"
        jsrc = "FOR-AUD-JUNGLE"
    else:
        t = np.arange(N) / RATE; jb = np.zeros(N)
        for f0, am, depth, g0 in ((4300, 38.0, 0.9, 0.5), (5650, 52.0, 0.8, 0.35), (3100, 6.5, 0.7, 0.3)):
            car = M.band(rs.normal(0, 1, N), f0 - 260, f0 + 260)
            swell = 0.6 + 0.4 * np.sin(2 * np.pi * rs.uniform(0.05, 0.12) * t + rs.uniform(0, 6))
            jb += g0 * car * (1 - depth + depth * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * am * t)))) * swell
        jb = jb / (np.sqrt((jb ** 2).mean()) + 1e-12) * 10 ** (-38 / 20)
        jungle += np.stack([jb, np.roll(jb, 300)], 1)
        used["insects_synth"] = "synthesized insect bed (U3 generator, kit Mix noise bands, AM), declared stand-in"
        jsrc = "HM-SYN-INSECTS"
    SIL = [(21.4, 22.0, "L"), (51.9, 52.5, "E")]
    jpts = [(0, -40), (1.0, -40), (2.6, 0), (37.6, 0), (38.0, -30), (39.5, -30), (40.1, 0), (69.5, 0), (72.0, -40), (73.0, -40)]
    for a, b, v in SIL: jpts += [(a - 0.06, 0), (a, -60), (b, -60), (b + 0.12, 0)]
    jpts.sort()
    jungle *= G["envelope"](N, jpts)[:, None]
    cue(2.0, "ambience", "jungle bed (absent under title and cards)", "L+E", jsrc, 67.5)
    for a, b, v in SIL: cue(a, "silence", "declared silence of the jungle while she takes the shoe", v, jsrc, b - a)

    # ---------------- foley
    foley = np.zeros((N, 2))
    steps_rms = []
    PLX = (190.0, 690.0)
    pan_of = lambda x: float(np.clip((x - 400) / 420, -0.8, 0.8))
    for v in ("L", "E"):
        fr = TR[v]["frames"]; off = OFF[v]
        for who in ("A", "B", "C"):
            for ai in (0, 1):
                xs = [f["people"][who]["ankles"][ai][0] for f in fr]
                last_i = -99
                for i in range(4, len(fr) - 4):
                    if i - last_i < 4: continue
                    if not (xs[i] >= max(xs[i - 4:i]) and xs[i] > xs[i + 2] + 0.5 and xs[i] >= xs[i + 1]): continue
                    if xs[i] - min(xs[max(0, i - 14):i]) < 15: continue
                    r0 = fr[max(0, i - 6)]["people"][who]["root"][0]; r1 = fr[min(len(fr) - 1, i + 6)]["people"][who]["root"][0]
                    if abs(r1 - r0) < 6: continue
                    last_i = i
                    t = fr[i]["t"]; x = xs[i]; bank = fr[i]["people"][who]["bank"]
                    if bank == "P" and PLX[0] - 5 <= x <= PLX[1] + 5:
                        defl = fr[i].get("plank_deflection_px", 0.0) or 0.0
                        load = 0.6 + 0.4 * min(defl / 9.0, 1.0)
                        s1 = G["wood_step"](load) * 0.8; s2 = G["creak"](load) * 0.55
                        put(foley, s1, off + t, 1.0, pan_of(x)); put(foley, s2, off + t + 0.03, 1.0, pan_of(x))
                        steps_rms.append(rms(np.r_[s1, s2]))
                        cue(off + t, "foley", f"{who} step on the plank + creak (deflection {defl:.1f} px), trace frame {i}", v, "HM-SYN-CREAK", 0.35, frame=i)
                    else:
                        put(foley, G["mud_step"](), off + t, 0.5, pan_of(x))
                        cue(off + t, "foley", f"{who} step on the {bank} bank (mud), trace frame {i}", v, "HM-SYN-MUD", 0.16, frame=i)
        for e in TR[v]["events"]:
            if e["event"] == "grip" and e["obj"] == "liana":
                put(foley, G["liana_creak"](), off + e["t"], 0.5, -0.1)
                cue(off + e["t"], "foley", f"{e['who']} takes the liana: fibre creak", v, "HM-SYN-LIANA", 0.45)
            if e["event"] == "retrieve":
                put(foley, G["plip"](), off + e["t"] + 0.02, 0.8, -0.4)
                cue(off + e["t"], "foley", "the shoe leaves the water (plip)", v, "HM-SYN-PLIP", 0.12)
        # bag rustle: onset on the first trace frame where the logged holder has changed (the ledger's holder change)
        bags = [f["bag"][0] for f in fr]
        ich = next(i for i in range(1, len(fr)) if bags[i] != bags[i - 1])
        t_ch = fr[ich]["t"]
        ru = G["card_rustle"](0.6)
        ru[:int(0.012 * RATE)] *= np.linspace(0, 1, int(0.012 * RATE))
        # the grains of U3's rustle are bunched mid-way; give it a struck onset (the bag's card body hitting the palm)
        n0 = int(0.05 * RATE); tt = np.arange(n0) / RATE
        ru[:n0] += 0.35 * M.band(M.noise(n0 / RATE), 900, 6000) * np.exp(-tt * 60)
        t_on = t_ch - 1.0 / FPS
        put(foley, ru, off + t_on, 1.9, -0.35)
        cue(off + t_on, "foley", f"bag hand-off {bags[ich - 1]} -> {bags[ich]}: card rustle (onset 1 frame before the holder change at trace frame {ich})", v, "HM-SYN-RUSTLE", 0.6, holder_change_film_frame=int(round((off + t_ch) * FPS)))
        # the shoe: tap at layer frame 86, drips at 139/143/148
        t0 = {"L": 14.0, "E": 7.0}[v]
        put(foley, G["shoe_tap"](), off + t0 + 86 / FPS, 1.0, -0.45)
        cue(off + t0 + 86 / FPS, "foley", "the shoe's hollow tap on the plank foot (layer frame 86)", v, "HM-SYN-TAP", 0.35)
        for kk in (139, 143, 148):
            put(foley, G["plip"](), off + t0 + kk / FPS, 0.45, -0.4)
            cue(off + t0 + kk / FPS, "foley", f"drip from the lifted shoe (layer frame {kk})", v, "HM-SYN-PLIP", 0.12)
    # splash: at the last crosser's minimum clearance (trace clearance_px, as in the ledger), >= 8 dB over the steps
    step_ref = float(np.median(steps_rms))
    for v in ("L", "E"):
        sp_t = SPLASH[v]["t"]; off = OFF[v]
        last = {"L": "B", "E": "C"}[v]
        x = TR[v]["frames"][int(round(sp_t * FPS))]["people"][last]["root"][0]
        if have["splash"]:
            sp = decode(F["splash"], 3.2, 1.1, RATE); sp = sp - sp.mean(0)
            used["splash"] = "Bathtub water splashes.ogg 3.2-4.3 s"; ssrc = "FOR-AUD-SPLASH"
        else:
            n = int(1.0 * RATE); tt = np.arange(n) / RATE
            body = M.band(M.noise(1.0), 180, 5200) * (np.exp(-tt * 5.5) * (1 - np.exp(-tt * 300)))
            slap = M.band(M.noise(1.0), 400, 3000) * np.exp(-tt * 40)
            drops = np.zeros(n)
            for _ in range(14):
                c = int(rs.uniform(0.12, 0.75) * RATE); L = int(0.03 * RATE); q = np.arange(L) / RATE
                drops[c:c + L] += rs.uniform(0.3, 0.8) * np.sin(2 * np.pi * rs.uniform(900, 2400) * q * (1 + 6 * q)) * np.exp(-q * 90)
            sp1 = body + 1.4 * slap + 0.5 * drops
            sp = np.stack([sp1, np.roll(sp1, 220)], 1); ssrc = "HM-SYN-SPLASH"
        sp *= np.r_[np.ones(len(sp) - 6000), np.linspace(1, 0, 6000)][:, None]
        pk = np.abs(sp).max() + 1e-9
        sp = np.tanh(4.0 * sp / pk) / np.tanh(4.0) * pk          # soft saturation: a dense wash, not a single spike
        seg = sp[:int(0.35 * RATE)]
        g = step_ref * 10 ** (14.0 / 20) / rms(seg)            # 14 dB over the median isolated plank step (>= 8 dB over the steps in the mix)
        put(foley, sp * g, off + sp_t - 0.08, 1.0, pan_of(x))
        cue(off + sp_t - 0.08, "foley", f"splash on {last}'s shins at the plank's lowest (trace clearance {SPLASH[v]['clearance_px']:.1f} px, local {sp_t:.3f} s)",
            v, ssrc, 1.0, clearance_px=SPLASH[v]["clearance_px"], over_step_db_isolated=14.0)
    # pencil
    for v, a, b in (("L", 5.0, 7.6), ("E", 42.5, 45.1)):
        put(foley, G["pencil"](b - a), a, 1.0, -0.2); cue(a, "foley", "pencil writing the ledger", v, "HM-SYN-PENCIL", b - a)
    for v, a, dur in (("L", 23.5, 1.45), ("E", SEG_E_REWRITE[0], 1.05)):
        put(foley, G["pencil"](0.33, scratch=True), a, 1.0, 0.0); cue(a, "foley", "pencil strike-through (8 frames)", v, "HM-SYN-SCRATCH", 0.33)
        put(foley, G["pencil"](dur), a + 0.45, 1.0, 0.0); cue(a + 0.45, "foley", "pencil rewriting the order", v, "HM-SYN-PENCIL", dur)
    put(foley, G["pencil"](1.2) * 0.6, 0.4); cue(0.4, "foley", "pencil on the title card", "T", "HM-SYN-PENCIL", 1.2)
    put(foley, G["pencil"](2.4) * 0.6, 70.0); cue(70.0, "foley", "pencil underlining on the comparison card", "cmp", "HM-SYN-PENCIL", 2.4)

    mix = water + jungle * 0.85 + foley * 0.9
    gg = min(1.0, 0.89 / np.abs(mix).max())
    stems = dict(water=water * gg, jungle=jungle * 0.85 * gg, foley=foley * 0.9 * gg)
    mixg = mix * gg

    def win(x, a, b): return x[int(a * RATE):int(b * RATE)]
    checks = {}
    for v in ("L", "E"):
        c_sp = [c for c in cues if c["version"] == v and "splash" in c["what"]][0]
        c_ru = [c for c in cues if c["version"] == v and "rustle" in c["what"]][0]
        a = c_sp["film_t"]
        checks[f"{v}_splash_rms_db"] = round(db(rms(win(stems["foley"], a + 0.0, a + 0.35))), 1)
        checks[f"{v}_step_median_rms_db"] = round(db(step_ref * 0.9 * gg), 1)
        r = c_ru["film_t"]
        checks[f"{v}_rustle_rms_db"] = round(db(rms(win(mixg, r, r + 0.35))), 1)
        checks[f"{v}_bed_before_rustle_rms_db"] = round(db(rms(win(mixg, r - 0.6, r - 0.05))), 1)
        checks[f"{v}_rustle_onset_vs_holder_change_frames"] = round(r * FPS - c_ru["holder_change_film_frame"], 2)
    checks["mix_peak"] = round(float(np.abs(mixg).max()), 3)
    cues.sort(key=lambda c: c["film_t"])
    return stems, mixg, dict(have=have, used=used, cues=cues, checks=checks, jungle_source=jsrc)
