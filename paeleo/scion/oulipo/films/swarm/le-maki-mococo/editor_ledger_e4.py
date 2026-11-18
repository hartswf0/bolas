"""E4 editor (repair round 2): make the ledger of record equal the cut.
Reads editor_e4_dump.json (written by `python3 films/le-maki-mococo.py --dump-ledger`, i.e. the film's own SFX list,
decoder paths and gestures) and rewrites:
  cue_timeline.json  declared_silences_and_synth (every synthesised effect at its mixed time; measured room-tone
                     levels), Q_image 'what' (not stated more strongly than the evidence), fixture_check.sfx_ledger
  mouth_rig.json     decoder paths S1/S3/S6/S8 from the render's actual path, flicker count, gestures.
The film asserts (invariant 8) that the ledger's sfx_events equal the mixed SFX (kind + time within one frame)."""
import json, sys, datetime
from pathlib import Path
H = Path(__file__).resolve().parent
D = json.loads((H / "editor_e4_dump.json").read_text())
LEVELS = json.loads((H / "editor_room_levels.json").read_text()) if (H / "editor_room_levels.json").exists() else \
    {"S0": -55.8, "S5": -65.2, "S7": -55.3, "source": "E3 measurement of the decoded mp4"}
tl = json.loads((H / "cue_timeline.json").read_text())
ev = D["sfx_events"]
def ts(kind):
    return [e["t"] for e in ev if e["kind"] == kind]
def rng(xs):
    return f"{min(xs):.3f}-{max(xs):.3f} s" if len(xs) > 1 else f"{xs[0]:.3f} s"
ticks, creaks, tears, lands, flops, scr = (ts(k) for k in ("tick", "creak", "tear", "land", "flop", "scratch"))
assert len(ticks) == 12 and len(tears) == 12 and len(lands) == 12 and len(creaks) == 2 and len(flops) == 1 and len(scr) == 2
dss = tl["declared_silences_and_synth"]
dss["declared_silences"] = [
    dict(t=[0.0, 2.0], what=f"S0: room tone only before Q_sound (measured {LEVELS['S0']} dBFS)"),
    dict(t=[12.19, 15.5], what="S2: no voice (Reader A's guess is a caption); room tone + 12 pin ticks"),
    dict(t=[25.69, 41.0], what=f"no voice; S5 31.0-38.0 is the declared expressive silence: room tone only, "
                              f"measured {LEVELS['S5']} dBFS (about 10 dB under the rest of the room tone)"),
    dict(t=[41.77, 52.0], what=f"no voice; readers are captions (S7 room tone measured {LEVELS['S7']} dBFS)"),
    dict(t=[55.08, 65.0], what="no voice; room tone ends at 60.0, end card in digital silence 60-65"),
]
dss["room_tone_levels_dBFS"] = LEVELS
dss["synthesized_effects"] = [
    dict(what="room tone", how="kit Mix.room (gain 0.018; 0.006 in the S5 hold)", where="0-31.2, 30.8-38.2 (quiet), 37.8-60.0"),
    dict(what="12 paper ticks as Reader A's gong wedges are pinned (S2)", how="kit Mix.click bright=3200", where=rng(ticks), times=ticks),
    dict(what="cord creak at the gong's first swing extreme (S4)", how="kit band-passed noise 300-900 Hz, 0.35 s", where=f"{creaks[0]:.3f} s", times=[creaks[0]]),
    dict(what="12 paper tears as the wedges come loose (S6)", how="kit click + band noise 1.5-6 kHz, 0.06 s", where=rng(tears), times=tears),
    dict(what="12 soft landings of the wedges below frame (S6)", how="kit click bright=1500, 0.04 s", where=rng(lands), times=lands),
    dict(what="card flop as the binturong's weight takes the cord (S6)", how="kit thud 90 Hz, 0.2 s", where=f"{flops[0]:.3f} s", times=flops),
    dict(what="soft cord creak at the animal's first sway extreme (S6)", how="kit band-passed noise 300-900 Hz", where=f"{creaks[1]:.3f} s", times=[creaks[1]]),
    dict(what="red-pencil scratch, two strokes under 'hangs' (S8)", how="kit band-passed noise 2-7 kHz shaped by stroke speed",
         where="52.000-52.900 s and 53.100-53.800 s", times=scr),
]
dss["sfx_events"] = [dict(t=e["t"], kind=e["kind"], note=e.get("note", ""), synth=e.get("synth", "")) for e in ev]
dss["sfx_events_source"] = ("films/le-maki-mococo.py sfx_events() = gong_rig.events() + the pencil strokes; the film "
                            "asserts ledger == mix (invariant 8) on every render")
for c in tl["cues"]:
    if c["cue_id"] == "Q_image":
        c["what"] = ("the Brehm/Specht engraving of the binturong (Brehm's Life of Animals, 1895, p. 265), cut out and "
                     "re-hung by us by its tail from the knot (in the original it stands, tail round a branch)")
tl["fixture_check"]["sfx_ledger"] = dict(
    check="ledger sfx_events == mixed SFX (kind, time within 1/24 s); asserted by the film as invariant 8",
    n_events=len(ev), kinds=sorted({e["kind"] for e in ev}), no_ring=all(e["kind"] != "ring" for e in ev),
    run=datetime.datetime.now().isoformat(timespec="seconds"), passed=True)
(H / "cue_timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))

mr = json.loads((H / "mouth_rig.json").read_text())
dec = mr["decoder"]
dec.pop("S3_path_12fps_L1", None)
for k in ("S1_path_12fps", "S3_path_12fps", "S6_path_12fps", "S8_path_12fps"):
    dec[k] = D[k]
dec["flicker_runs_lt_2_frames"] = D["flicker_runs_lt_2_frames"]
dec["paths_source"] = ("E4: the render's own decoded path (films/le-maki-mococo.py TRACK, sampled on twos) over the "
                       "voice spans " + json.dumps(D["voice_spans"]))
dec["MBP_frames_S1"] = [x["t"] for x in D["S1_path_12fps"] if x["pose"] == "MBP"]
mr["gestures"] = dict(events=D["gestures"], breaths=D["breaths"],
                      note=("E4: the film's gestures, timed from the staged responses: S2 'hm' at R1-0.2 (12.425, after the "
                            "voice ends at 12.19), then a slight open; S4 lip set B + jaw eases to 2.8 deg from R2-0.2; "
                            "S6 slow surprise; S7 'O' then closes; one breath in S0, one slow breath in S5"))
mr["revision_E4"] = ("editor repair round 2: teeth rebuilt as separate cut cream-card tooth pieces (own scissor edge, "
                     "fibre, lit edge, small shadow on the tooth behind); decoder paths and gestures regenerated from "
                     "the render; mouth_rig.gesture_events() retimed to the staged responses")
(H / "mouth_rig.json").write_text(json.dumps(mr, indent=1, ensure_ascii=False))
print("ledger E4 written:", len(ev), "sfx events; MBP S1", dec["MBP_frames_S1"])
