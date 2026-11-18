"""Step 1 (editor): compare cues-A.json and cues-B.json against picture/edl.json for the same master revision.

Writes out/cuemap-compare.json. Never retimes the picture. Run: python3 -I editor/cuemap.py
"""
import json, os, re, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
SRC = os.path.join(FILMS, "sources", "la-cite-raymond-queneau")
RATE, N, FPS = 44100, 1323000, 24

STEMS = {"A": {k: f"{SRC}/sound-A/stems/{k}.wav" for k in ("voice", "music", "fx", "amb")},
         "B": {k: f"{SRC}/sound-B/stems/B-{k}.wav" for k in ("voice", "music", "fx", "amb")}}


def read_wav(p):
    w = wave.open(p)
    assert w.getframerate() == RATE and w.getsampwidth() == 2, p
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return x.reshape(-1, w.getnchannels())


def peak_db(x):
    p = float(np.abs(x).max()) if len(x) else 0.0
    return round(20 * np.log10(p), 1) if p > 0 else -240.0


def resolve(pid, ev_by_id, edl):
    """Map a team's picture_event_id onto an edl.json event (or shot). Returns (edl_id, frame, span) or None."""
    if pid in ev_by_id:
        e = ev_by_id[pid]
        return pid, e["frame"], None
    m = re.match(r"window_on:(\d+)$", pid)
    if m and f"win{int(m.group(1)):02d}_on" in ev_by_id:
        i = f"win{int(m.group(1)):02d}_on"; return i, ev_by_id[i]["frame"], None
    m = re.match(r"walker_step:(\d+)$", pid)
    if m:
        for e in edl["events"]:
            if e["kind"] == "walker_step" and e["frame"] == int(m.group(1)):
                return e["id"], e["frame"], None
    alias = {"door_open:C": "door_open", "door_close:C": "door_close", "silhouette_rise:16": "silhouette_rise",
             "head_turn:16": "head_turn", "cut:S4": "cut_624", "lamp_on": "lamp_on", "window_off:16": "win16_off"}
    if pid in alias:
        i = alias[pid]; return i, ev_by_id[i]["frame"], None
    m = re.match(r"shot:(S\d)$", pid)
    if m:
        for s in edl["shots"]:
            if s["id"] == m.group(1):
                return "shot:" + s["id"], s["k0"], (s["k0"], s["k1"])
    return None


# visible spans of events whose action lasts several frames (from edl.json / maquette.py, plan §6)
SPANS = {"door_open": (334, 346), "door_close": (365, 374), "silhouette_rise": (502, 518), "head_turn": (538, 552),
         "curtain_slide": (552, 566)}


def main():
    edl = json.load(open(os.path.join(SW, "picture", "edl.json")))
    rev = edl["master"]["revision"]
    sha = json.load(open(os.path.join(SW, "out", "master.sha1.json")))
    assert sha["revision"] == rev, "edl.json and master.sha1.json name different revisions"
    ev_by_id = {e["id"]: e for e in edl["events"]}
    out = {"master_revision": rev, "edl": "picture/edl.json", "editions": {}, "checks": {}}
    ok_all = True
    for ed, path in (("A", "sound-A/cues-A.json"), ("B", "sound-B/cues-B.json")):
        cues = json.load(open(os.path.join(SW, path)))
        rows, missing = [], []
        for c in cues:
            r = resolve(c["picture_event_id"], ev_by_id, edl)
            row = {"sound_event": c["sound_event"], "source": c.get("source_ledger_id") or "", "picture_event_id": c["picture_event_id"], "t_sound": c["t_sound"],
                   "cue_frame": c["frame"], "offset_ms_declared": c["offset_ms"],
                   "offset_ms_from_cue_frame": round((c["t_sound"] - c["frame"] / FPS) * 1000, 1)}
            if r is None:
                missing.append(c["picture_event_id"]); row["edl_event"] = None
            else:
                row["edl_event"], row["edl_frame"] = r[0], r[1]
                span = r[2] or SPANS.get(r[0])
                row["cue_frame_minus_edl_frame"] = c["frame"] - r[1]
                if span:
                    row["edl_span"] = list(span)
                    row["cue_frame_in_span"] = span[0] <= c["frame"] <= span[1]
            rows.append(row)
        out["editions"][ed] = {"cues": rows, "n": len(rows), "unresolved_ids": missing}
        ok_all &= not missing
        # frames must agree with edl unless the cue sits inside the event's declared visible span
        drift = [r for r in rows if r.get("edl_event") and r["cue_frame_minus_edl_frame"] != 0 and not r.get("cue_frame_in_span")]
        out["editions"][ed]["frame_drift"] = drift
        ok_all &= not drift
    # B: window cues within +-42 ms of their frame (declared and measured onset)
    fxB = read_wav(STEMS["B"]["fx"]).mean(1)
    hp = np.diff(fxB, prepend=0)
    winB = []
    for r in out["editions"]["B"]["cues"]:
        if (r.get("edl_event") or "").startswith("win") and r["edl_event"].endswith("_on") and "click" in r["sound_event"] and "no click" not in r["sound_event"]:
            f = r["edl_frame"]; t = f / FPS
            a, b = int((t - 0.03) * RATE), int((t + 0.08) * RATE)
            seg = np.abs(hp[a:b]); thr = 0.3 * seg.max()
            on = (a + int(np.argmax(seg > thr))) / RATE if seg.max() > 0 else None
            winB.append({"event": r["edl_event"], "frame": f, "declared_ms": round((r["t_sound"] - t) * 1000, 1),
                         "measured_onset_ms": round((on - t) * 1000, 1) if on is not None else None})
    silent = [r["edl_event"] for r in out["editions"]["B"]["cues"] if "no click" in r["sound_event"]]
    out["checks"]["B_declared_silent_window_cues"] = silent
    bad = [w for w in winB if abs(w["declared_ms"]) > 42 or w["measured_onset_ms"] is None or abs(w["measured_onset_ms"]) > 42]
    out["checks"]["B_window_cues_within_42ms"] = {"n": len(winB), "fail": bad, "pass": not bad, "rows": winB,
                                                   "note": "measured onset = first sample of the stem's differenced fx signal above 30% of the local max within -30..+80 ms (the window avoids a typewriter key one frame earlier); win55_on is a declared silent cue inside the f538-566 hold"}
    ok_all &= not bad
    # A: window offsets irregular (std >= 80 ms), no two consecutive window cues on the same sound
    wa = [r for r in out["editions"]["A"]["cues"] if (r.get("edl_event") or "").startswith("win") and r["edl_event"].endswith("_on")]
    wa.sort(key=lambda r: r["edl_frame"])
    offs = np.array([(r["t_sound"] - r["edl_frame"] / FPS) * 1000 for r in wa])
    rep = [(x["edl_event"], y["edl_event"], x["source"]) for x, y in zip(wa, wa[1:]) if x["source"] == y["source"]]   # same SOUND source
    out["checks"]["A_window_offsets"] = {"n": len(wa), "std_ms": round(float(offs.std()), 1), "min_ms": round(float(offs.min()), 1),
                                         "max_ms": round(float(offs.max()), 1), "pass_std_ge_80": bool(offs.std() >= 80),
                                         "consecutive_same_sound": rep, "pass_no_consecutive_repeat": not rep,
                                         "sequence": [[r["edl_frame"], r["source"]] for r in wa],
                                         "note": "repeat test compares source_ledger_id (the recording or handmade generator), sorted by frame"}
    ok_all &= bool(offs.std() >= 80) and not rep
    # crossover 16.0-17.5 s by stem energy
    a, b = int(16.0 * RATE), int(17.5 * RATE)
    xo = {}
    for ed in ("A", "B"):
        xo[ed] = {}
        for k, p in STEMS[ed].items():
            x = read_wav(p)
            assert len(x) == N, (p, len(x))
            xo[ed][k] = peak_db(x[a:b])
    passA = bool(xo["A"]["voice"] <= -60 and xo["A"]["fx"] <= -60 and xo["A"]["amb"] <= -60 and xo["A"]["music"] > -60)
    passB = bool(xo["B"]["music"] <= -60 and xo["B"]["fx"] <= -60 and xo["B"]["amb"] <= -60 and xo["B"]["voice"] > -60)
    out["checks"]["crossover_16.0_17.5_peak_dbfs"] = {"A": xo["A"], "B": xo["B"], "A_music_only": passA, "B_voice_only": passB}
    out["checks"]["stem_samples"] = {"all_1323000": True}
    # B's key cut: is the voice on f384 REAL speech? (source must be a foraged speech recording, onset within 42 ms of 16.0 s)
    vB = read_wav(STEMS["B"]["voice"]).mean(1)
    seg = vB[int(15.9 * RATE):int(17.5 * RATE)]
    spec = np.abs(np.fft.rfft(seg)); fq = np.fft.rfftfreq(len(seg), 1 / RATE)
    band = float((spec[(fq >= 300) & (fq <= 3000)] ** 2).sum() / max((spec ** 2).sum(), 1e-12))
    env = np.abs(seg); thr = 0.1 * env.max() if env.max() > 0 else 1
    on_ms = round((int(np.argmax(env > thr)) / RATE + 15.9 - 16.0) * 1000, 1) if env.max() > 0 else None
    k384 = [c for c in json.load(open(os.path.join(SW, "sound-B", "cues-B.json"))) if c["frame"] == 384 and c.get("stem") in ("voice", None)]
    real = [c for c in k384 if str(c.get("source_ledger_id", "")).startswith(("LL:", "LOC:jukebox"))]
    out["checks"]["B_crossover_real_speech"] = {"sources_on_f384": [c.get("source_ledger_id") for c in k384], "real_speech": bool(real),
                                                "voice_onset_ms_from_16.0": on_ms, "energy_fraction_300_3000_hz": round(band, 3),
                                                "pass": bool(real) and on_ms is not None and abs(on_ms) <= 42,
                                                "note": "intelligibility itself is a listening judgement; this checks the source is a real speech recording (Lingua Libre word, or the LoC 1917 spoken-word record, captioned as indistinct), its onset and its band"}
    ok_all &= out["checks"]["B_crossover_real_speech"]["pass"]
    ok_all &= passA and passB
    out["realignment"] = [
        {"edition": "A", "what": "street door shut moved from f370 to the edl door_close frame f374 (door closes 365-374); build_A.py re-run, now reading walker_step ids and frames from edl.json",
         "picture_retimed": False},
        {"edition": "B", "what": "build_B.py re-run against edl.json (asserts the window table); no shift needed", "picture_retimed": False},
        {"edition": "A", "what": "repair 1: window cues re-assigned so no two consecutive windows share a source (f406 radio 78 replaces the second music-box note; f427 handle creak; f470 distant door)", "picture_retimed": False}]
    out["pass"] = bool(ok_all)
    json.dump(out, open(os.path.join(SW, "out", "cuemap-compare.json"), "w"), indent=1, ensure_ascii=False)
    print("cuemap pass:", ok_all, "| A std", out["checks"]["A_window_offsets"]["std_ms"], "| B worst onset",
          max(abs(w["measured_onset_ms"]) for w in winB), "| xo", xo,
          "| drift", [len(out["editions"][e]["frame_drift"]) for e in "AB"], "| unresolved", [out["editions"][e]["unresolved_ids"] for e in "AB"])


if __name__ == "__main__":
    main()
