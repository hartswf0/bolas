"""Step 2 (editor): sum each edition's stems on the shared clock, level-match to -23.0 LUFS, true peak <= -1 dBTP.

Editions: A, B, X (A music+fx+amb, A voice to 16.0 s then B voice), C (branch: A+B amb only, silent 16-26 s
except one room-tone swell from f492), silent (digital zero). Loudness measured with ffmpeg ebur128=peak=true.
Writes films/sources/la-cite-raymond-queneau/editor/mix-<ed>.wav and out/mix.json.
"""
import json, os, re, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
SRC = os.path.join(FILMS, "sources", "la-cite-raymond-queneau")
ED = os.path.join(SRC, "editor")
RATE, N, FPS = 44100, 1323000, 24
TARGET, TOL, TP_MAX = -23.0, 0.5, -1.0
STEMS = {"A": {k: f"{SRC}/sound-A/stems/{k}.wav" for k in ("voice", "music", "fx", "amb")},
         "B": {k: f"{SRC}/sound-B/stems/B-{k}.wav" for k in ("voice", "music", "fx", "amb")}}


def read_wav(p):
    w = wave.open(p)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    x = x.reshape(-1, w.getnchannels())
    assert len(x) == N and x.shape[1] == 2, (p, x.shape)
    return x


def write_wav(p, st):
    pcm = np.round(np.clip(st, -1, 32767 / 32768) * 32768).astype(np.int16)
    with wave.open(p, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm.tobytes())


def ebur128(path, stream="a:0"):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:" + stream, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", s).group(1))
    m = re.search(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS", s)
    tp = float(m.group(1)) if m else None
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", s).group(1))
    return I, tp, lra


def fade(n, a, b, ramp=0.03):
    """gain curve 1 outside [a,b) s, 0 inside, with short ramps (no clicks)."""
    t = np.arange(n) / RATE
    g = np.ones(n)
    g[(t >= a) & (t < b)] = 0
    r = int(ramp * RATE)
    k = np.ones(r) / r
    return np.convolve(g, k, "same")


def main():
    os.makedirs(ED, exist_ok=True)
    S = {e: {k: read_wav(p) for k, p in d.items()} for e, d in STEMS.items()}
    t = np.arange(N) / RATE
    cut = int(16.0 * RATE)
    voiceX = np.concatenate([S["A"]["voice"][:cut], S["B"]["voice"][cut:]])
    # C: amb only; silent 16-26 except a room-tone swell starting at f492 (20.5 s), peak at 21.1 s, gone by 22.6 s
    amb = S["A"]["amb"] + S["B"]["amb"]
    gate = fade(N, 16.0, 26.0)
    t0, tp_, t1 = 492 / FPS, 492 / FPS + 0.6, 492 / FPS + 2.1
    sw = np.where((t >= t0) & (t < tp_), np.sin(0.5 * np.pi * (t - t0) / 0.6) ** 2, 0) + \
         np.where((t >= tp_) & (t < t1), np.cos(0.5 * np.pi * (t - tp_) / 1.5) ** 2, 0)
    swell = S["A"]["amb"] * sw[:, None]           # A's interior room tone (handmade by sound-A) at this moment
    recipes = {
        "A": ("A voice+music+fx+amb", sum(S["A"].values())),
        "B": ("B voice+music+fx+amb", sum(S["B"].values())),
        "X": ("A music+fx+amb 0-30 s; A voice 0-16.0 s then B voice 16.0-30 s (hard switch on sample 705600)",
              S["A"]["music"] + S["A"]["fx"] + S["A"]["amb"] + voiceX),
        "C": ("branch C: A amb + B amb outside 16.0-26.0 s (30 ms ramps); inside, silence except A's room tone swelling from f492 (0.6 s up, 1.5 s down)",
              amb * gate[:, None] + swell),
    }
    TEAM_GAIN = {"A": json.load(open(os.path.join(SW, "sound-A", "mix-A.json")))["global_gain_db"],
                 "B": json.load(open(os.path.join(SW, "sound-B", "premix-B.json")))["pre_gain_db"]}
    STEM_USE = {"A": {k: ("A", k, f"sound-A {k}.wav") for k in ("voice", "music", "fx", "amb")},
                "B": {k: ("B", k, f"sound-B B-{k}.wav") for k in ("voice", "music", "fx", "amb")},
                "X": {"music": ("A", "music", "sound-A music.wav"), "fx": ("A", "fx", "sound-A fx.wav"), "amb": ("A", "amb", "sound-A amb.wav"),
                      "voice": ("B", "voice", "A voice.wav 0-16.0 s, B-voice.wav 16.0-30 s")},
                "C": {"amb(A+B)": ("A", "amb", "A amb + B amb, gated 16-26 s, A room-tone swell from f492")}}
    rep = {"target_lufs": TARGET, "tolerance_lu": TOL, "true_peak_max_dbtp": TP_MAX, "meter": "ffmpeg ebur128=peak=true",
           "team_premix_gain_db": TEAM_GAIN,
           "editions": {}}
    for ed, (recipe, st) in recipes.items():
        tmp = os.path.join(ED, f"mix-{ed}.wav")
        write_wav(tmp, st)
        I0, tp0, _ = ebur128(tmp)
        g_db = TARGET - I0
        st2 = st * 10 ** (g_db / 20)
        write_wav(tmp, st2)
        I1, tp1, lra = ebur128(tmp)
        # one trim pass if needed (int16 rounding / gating moves)
        if abs(I1 - TARGET) > 0.05:
            g2 = TARGET - I1; g_db += g2; st2 = st * 10 ** (g_db / 20); write_wav(tmp, st2); I1, tp1, lra = ebur128(tmp)
        assert tp1 <= TP_MAX, (ed, tp1)
        rep["editions"][ed] = {"recipe": recipe, "wav": os.path.relpath(tmp, FILMS), "unity_integrated_lufs": I0, "unity_true_peak_dbtp": tp0,
                               "edition_gain_db": round(g_db, 2), "integrated_lufs_wav": I1, "true_peak_dbtp_wav": tp1, "lra_lu": lra,
                               "samples": N, "pass": abs(I1 - TARGET) <= TOL and tp1 <= TP_MAX}
        # actual per-stem gains: team pre-gain (already in the stem file) + this edition's one editor gain, and each
        # stem's measured loudness as it sits in this mix (stem x editor gain, ebur128 on a temp wav)
        per = {}
        for sk, (src_ed, stem, gate_desc) in STEM_USE[ed].items():
            x = S[src_ed][stem]
            if ed == "X" and sk == "voice": x = voiceX
            if ed == "C": x = (amb * gate[:, None] + swell) if sk == "amb(A+B)" else x
            tmp2 = os.path.join(ED, "_stem.wav"); write_wav(tmp2, x * 10 ** (g_db / 20))
            Is, tps, _ = ebur128(tmp2); os.remove(tmp2)
            per[sk] = {"source": gate_desc, "team_gain_db": TEAM_GAIN[src_ed], "editor_gain_db": round(g_db, 2),
                       "total_gain_db_from_unity": round(TEAM_GAIN[src_ed] + g_db, 2),
                       "stem_lufs_in_mix": Is, "stem_true_peak_dbtp_in_mix": tps}
        rep["editions"][ed]["stems"] = per
        if ed == "C":
            rep["editions"][ed]["branch"] = "out/branches/C"
        print(ed, rep["editions"][ed])
    write_wav(os.path.join(ED, "mix-silent.wav"), np.zeros((N, 2)))
    rep["editions"]["silent"] = {"recipe": "digital zero, 1,323,000 samples", "wav": os.path.relpath(os.path.join(ED, "mix-silent.wav"), FILMS),
                                 "edition_gain_db": None, "peak": 0}
    rep["A_minus_B_lu"] = round(rep["editions"]["A"]["integrated_lufs_wav"] - rep["editions"]["B"]["integrated_lufs_wav"], 2)
    json.dump(rep, open(os.path.join(SW, "out", "mix.json"), "w"), indent=1)
    os.makedirs(os.path.join(SW, "out", "branches", "C"), exist_ok=True)
    json.dump({"branch": "C", "base_revision": json.load(open(os.path.join(SW, "out", "master.sha1.json")))["revision"],
               "what": recipes["C"][0], "plan": "plan-r3 §6c / §8 (optional third soundtrack: selective silence and room tone)",
               "edition": "out/edition-C.mp4"}, open(os.path.join(SW, "out", "branches", "C", "branch.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
