"""U3 (voice writer + referent checker): builds u3-clause-ledger.json, takeA.srt, takeB.srt
from beats-r3 (editor repair round 2 copy of U3's builder; changes marked r3). HANDMADE text only; reads no downloaded data.

    python3 -I u3_build_ledger.py

Times are pass-relative seconds, rounded to the millisecond. Film time = pass time + 1.0 (PASS-A)
or + 37.0 (PASS-B).
"""
import json
from pathlib import Path

SWARM = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort")
BEATS = json.loads((SWARM / "beats.json").read_text())
OFFSET = 1.2
FILM_OFFSET = {"A": 1.0, "B": 37.0}
TRACK_NAME = {"A": "A_ahead", "B": "B_behind"}

r3 = lambda x: round(x + 0.0, 3)


def inter(a, b):
    return r3(max(0.0, min(a[1], b[1]) - max(a[0], b[0])))


EV = {e["id"]: e for e in BEATS["events"]}
SH = {s["id"]: s for s in BEATS["shots"]}
SIL = BEATS["silences"][0]

# ---- referent tagging (handmade) ---------------------------------------------------------
PRED = {
    "c1": {"subject": "You", "predicate": "lift(your head)", "verb": "lift", "polarity": "positive",
           "aspect": "punctual"},
    "c2": {"subject": "You", "predicate": "hear(it, through the wall)", "verb": "hear", "polarity": "positive",
           "aspect": "perception"},
    "c3": {"subject": "You", "predicate": "answer(it)", "verb": "answer", "polarity": "negative",
           "aspect": "refusal (withheld action)"},
    "c4": {"subject": "You", "predicate": "take(the stairs)", "verb": "take", "polarity": "positive",
           "aspect": "motion"},
    "c5": {"subject": "You", "predicate": "take(the same stairs, again; one step after another)", "verb": "take",
           "polarity": "positive", "aspect": "iterative motion"},
}
REFS = {
    "c1": [
        {"span": "You", "role": "agent / addressee", "referent": "you:A1",
         "depicted_by": "figure:F (Bubley sitter, LoC 2017862333) via bind E1"},
        {"span": "your head", "role": "patient (body part of addressee)", "referent": "you:A1.head",
         "depicted_by": "figure:F head piece H rising >= 30 px off the fixed hand K in E1 (r3); eyes the plate's own, down and off-lens"},
    ],
    "c2": [
        {"span": "You", "role": "experiencer / addressee", "referent": "you:A1",
         "depicted_by": "absent from S2 (nobody present); figure:F is the off-screen listener whose room fixes sonic perspective"},
        {"span": "it", "role": "stimulus (3rd-person non-human; not narration person)", "referent": "object:telephone.ring",
         "depicted_by": "E2 ring 1 (sound) over S2 telephone plate LoC 2017735081"},
        {"span": "the wall", "role": "path", "referent": "place:wall-between-room-and-hall",
         "depicted_by": "sonic perspective only (low-passed bell, U2); not shown as such"},
    ],
    "c3": [
        {"span": "You", "role": "agent of refused act / addressee", "referent": "you:A1",
         "depicted_by": "figure:F (Bubley sitter, LoC 2017862340) via bind E3"},
        {"span": "(answer) [implicit object]", "role": "elided theme", "referent": "object:telephone.call",
         "depicted_by": "ring 3 heard in S3; head turns at 9.25 and returns at 10.4, no reach"},
    ],
    "c4": [
        {"span": "You", "role": "agent / addressee", "referent": "you:A1",
         "depicted_by": "figure:F (the Bubley sitter of S3/S4, cut from LoC 2017862340, climbing the Mydans stair LoC 2017714056) via bind E4"},
        {"span": "the stairs", "role": "path", "referent": "place:stair#1",
         "depicted_by": "S5 stair plate LoC 2017714056 (Mydans)"},
    ],
    "c5": [
        {"span": "You", "role": "agent / addressee", "referent": "you:A1",
         "depicted_by": "figure:F via bind E6 while visible (28.5-31.5); after E6.exit nobody: in track B the address falls on the audience position (D)"},
        {"span": "the same stairs", "role": "path (identity claim)", "referent": "place:stair#1",
         "depicted_by": "S7 27.0-32.5 = S5 frames byte-identical (invariant 5); 'same' is true by frame identity"},
        {"span": "again", "role": "iteration anaphor", "referent": "event:E4",
         "depicted_by": "repeat of flight 1"},
        {"span": "one step after another", "role": "manner", "referent": "event:E7 footfalls",
         "depicted_by": "footfalls 28.8, 29.35, 29.9, 30.45, 31.0 (step dips + foraged steps)"},
    ],
}


def shots_overlapping(iv):
    return [s["id"] for s in BEATS["shots"] if inter(iv, s["t"]) > 0]


def figure_visible_planned(t0, t1):
    """Planned figure:F visibility (from beats) inside [t0,t1] -> list of intervals."""
    vis = [(0.0, 5.5), (8.5, 19.0), (20.5, 23.5), (28.5, 31.5)]  # S1, S3+S4, S5 entry-exit, S7 entry-exit
    out = []
    for a, b in vis:
        lo, hi = max(a, t0), min(b, t1)
        if hi > lo:
            out.append([r3(lo), r3(hi)])
    return out


clauses = []
for c in BEATS["clauses"]:
    e = EV[c["bind"]]
    e_iv = [e["t_on"], e["t_off"]]
    entry = {
        "clause_id": c["id"],
        "text": c["text"],
        "addressee_id": "you:A1",
        "grammatical_person": 2,
        **PRED[c["id"]],
        "referent_tags": REFS[c["id"]],
        "bind": {"event_id": e["id"], "event_name": e["name"], "subject_id": e["subject_id"],
                 "shot_id": e["shot"], "observation_interval": e_iv,
                 "exit": e.get("exit")},
        "duration_s": c["dur"],
        "tracks": {},
    }
    for k, rel in (("A", "anticipates"), ("B", "lags")):
        on = r3(e["t_on"] - OFFSET) if k == "A" else r3(e["t_on"] + OFFSET)
        iv = [on, r3(on + c["dur"])]
        assert abs(iv[0] - c[k][0]) < 1e-6 and abs(iv[1] - c[k][1]) < 1e-6, (c["id"], k, iv, c[k])
        ov = inter(iv, e_iv)
        incidental = []
        for other in BEATS["events"]:
            if other["id"] == e["id"] or "t_on" not in other:
                continue
            o = inter(iv, [other["t_on"], other["t_off"]])
            if o > 0:
                incidental.append({"event_id": other["id"], "overlap_s": o, "bound": False})
        rec = {
            "track": TRACK_NAME[k],
            "interval": iv,
            "film_interval": [r3(iv[0] + FILM_OFFSET[k]), r3(iv[1] + FILM_OFFSET[k])],
            "declared_relation": rel,
            "onset_minus_event_s": r3(iv[0] - e["t_on"]),
            "overlaps_computed": ov > 0,
            "overlap_with_bound_event_s": ov,
            "incidental_overlaps_unbound": incidental,
            "shots_spanned": shots_overlapping(iv),
            "gap_to_SIL-H_s": r3(min(abs(iv[1] - SIL["t"][0]), abs(iv[0] - SIL["t"][1]))),
            "figure_visible_planned": figure_visible_planned(*iv),
        }
        if e.get("exit") is not None:
            rec["after_exit_s"] = r3(max(0.0, iv[1] - max(iv[0], e["exit"])))
        entry["tracks"][k] = rec
    clauses.append(entry)

silence = {
    "id": SIL["id"], "interval": SIL["t"], "shot_id": "S4",
    "film_intervals": {"A": [r3(SIL["t"][0] + 1.0), r3(SIL["t"][1] + 1.0)],
                       "B": [r3(SIL["t"][0] + 37.0), r3(SIL["t"][1] + 37.0)]},
    "tracks": {"A": {"relation": "leaves_silence", "captions": []},
               "B": {"relation": "leaves_silence", "captions": []}},
    "allowed_sound": SIL["allowed_sound"], "guard_s": BEATS["guards"]["silence_guard_s"],
    "nearest_clauses": {"before": "c3.B ends 11.4 (gap 0.1)", "after": "c4.A starts 19.3 (gap 0.3)"},
}

NARR = "N, off-screen, captions only"
AUD = "spectator before the screen"
viewpoints = []
PERF = {
    "S1": "figure:F (Bubley sitter, LoC 2017862333)",
    "S2": "none (nobody present; telephone only)",
    "S3": "figure:F (Bubley sitter, LoC 2017862340)",
    "S4": "figure:F (Bubley sitter, LoC 2017862340)",
    "S5": "figure:F (Bubley sitter, cut from LoC 2017862340, on the Mydans stair LoC 2017714056) 20.5-23.5; none 19.0-20.5 and 23.5-24.5",
    "S6": "none (empty stairwell)",
    "S7": "figure:F (same frames as S5) 28.5-31.5; none 27.0-28.5 and 31.5-35.0",
}
EYE = {
    "S1": "down at his hand/pillow, off-lens", "S2": "n/a", "S3": "off-lens; turns 9 deg toward frame left at 9.25",
    "S4": "off-lens (as S3)", "S5": "three-quarter, ahead up the stair, off-lens", "S6": "n/a", "S7": "as S5",
}
for s in BEATS["shots"]:
    viewpoints.append({
        "shot_id": s["id"], "t": s["t"],
        "camera_viewpoint": s["camera_viewpoint"],
        "narrator": NARR,
        "on_screen_performer": PERF[s["id"]],
        "audience_position": AUD,
        "performer_eyeline": EYE[s["id"]],
        "is_pov": False,
        "gaze_meets_lens": False,
    })

ledger = {
    "film": "un-homme-qui-dort",
    "unit": "U3 voice writer + referent checker (one owner, one ledger)",
    "mode": "handmake",
    "forks_from": BEATS["revision"],
    "date": "2026-11-16 (r3, editor)",
    "time_base": "pass-relative seconds, 24 fps; film time = pass + 1.0 (A) or + 37.0 (B)",
    "declared_addressee": {"id": "you:A1", "grammatical_person": 2,
                           "note": "one addressee throughout; no marked shift exists in this proof"},
    "diegetic_speech_track": {"declared": "empty", "note": "invariant 2; U2 states no speech audible"},
    "viseme_set": {"declared": "empty", "note": "SCION-47: the performer never speaks and no mouth motion is authored anywhere. Mouths are the plates' own and stay still: closed in S1 (2017862333); pursed/slightly open as photographed in S3/S4 and on the S5/S7 climber (2017862340). r2 wrongly said 'mouth stays closed' (the r2 S1 plate 2017862347 had an open mouth)."},
    "offset_rule": BEATS["offset_rule"],
    "clauses": clauses,
    "silences": [silence],
    "viewpoints": viewpoints,
    "roles_kept_distinct": "camera_viewpoint, narrator, on_screen_performer and audience_position are four separate "
                           "fields per shot and never merge: no POV, the narrator never appears, the performer never "
                           "looks into the lens, the audience is addressed only through the empty frames of D.",
    "defining_beat": BEATS["defining_beat"],
    "baseline": BEATS["baseline"],
    "allowed_edit_crossings": BEATS["allowed_edit_crossings"],
    "caption_setting": {
        "font": "Instrument Serif (assets/fonts/instrument-serif.woff2, OFL), 26 px",
        "color": "#efefef", "band": "#1e1e1e at 60% opacity (alpha 153), padding 14 px x, 10/12 px y",
        "y_center": "frame height - 46 px", "align": "centred", "case": "sentence case, full stop kept",
        "not": "kit Ink.caption()'s cream PAGE band; the editor draws this band itself",
        "proof": "u3-caption-proof.png",
    },
    "outputs": {
        "takeA.srt": str(SWARM / "takeA.srt"), "takeB.srt": str(SWARM / "takeB.srt"),
        "gate": str(SWARM / "u3-gate.py"), "audit": str(SWARM / "u3-referent-audit.json"),
        "caption_proof": str(SWARM / "u3-caption-proof.png"),
        "builder": str(Path(__file__).resolve()),
    },
    "evidence": [
        {"id": "loc-2017862340", "title": "Washington, D.C. A boardinghouse philosopher", "author": "Esther Bubley (photographer), U.S. Office of War Information",
         "license": "No known restrictions (LoC rights_advisory; FSA/OWI, US government work)",
         "license_url": "https://www.loc.gov/rr/print/res/071_fsab.html", "source_url": "https://www.loc.gov/item/2017862340/",
         "file_url": "https://tile.loc.gov/storage-services/master/pnp/fsa/8d33000/8d33500/8d33583u.tif",
         "local_path": "/home/user/bolas/paeleo/scion/oulipo/films/sources/un-homme-qui-dort/u1-picture-camera-drawing-team-quiet-observational-cut-scion-29-extraction-scion-44-multiplane-staging-scion-47-body-actions-aesthetic-grade-/raw/8d33583u.tif",
         "what_it_shows": "a man in a dark pinstripe suit slumped against a pale wall, flash-lit, his cast shadow on the wall at right",
         "verified_date_or_place": "1943 Jan., Washington, D.C. (LoC record /home/user/bolas/paeleo/scion/oulipo/films/sources/un-homme-qui-dort/u1-picture-camera-drawing-team-quiet-observational-cut-scion-29-extraction-scion-44-multiplane-staging-scion-47-body-actions-aesthetic-grade-/raw/2017862340.json, read 2026-11-15)",
         "used_as": "U3 caption proof only: provisional S4 stand-in frame (U1's recorded S4 crop and curve); not a film element supplied by U3"},
        {"id": "loc-2017811447", "title": "[Untitled photo, possibly related to: Powder plant employee going upstairs. Mrs. Pritchard's boardinghouse. Radford, Virginia]",
         "author": "John Vachon (photographer), U.S. Farm Security Administration",
         "license": "No known restrictions (LoC rights_advisory; FSA/OWI, US government work)",
         "license_url": "https://www.loc.gov/rr/print/res/071_fsab.html", "source_url": "https://www.loc.gov/item/2017811447/",
         "file_url": "https://tile.loc.gov/storage-services/service/pnp/fsa/8c18000/8c18400/8c18457v.jpg",
         "local_path": "/home/user/bolas/paeleo/scion/oulipo/films/sources/un-homme-qui-dort/u1-picture/raw/loc_2017811447_v.jpg",
         "what_it_shows": "a man in a cap climbing a boardinghouse stair in profile, plaid coat over his arm, banister at left, patterned wallpaper",
         "verified_date_or_place": "1940 Dec., Radford, Virginia (LoC record /home/user/bolas/paeleo/scion/oulipo/films/sources/un-homme-qui-dort/u1-picture-camera-drawing-team-quiet-observational-cut-scion-29-extraction-scion-44-multiplane-staging-scion-47-body-actions-aesthetic-grade-/raw/2017811447.json, read 2026-11-15)",
         "used_as": "U3 caption proof only: provisional S5 stand-in frame (plate, rebate cropped, one monotone curve); not a film element supplied by U3"},
        {"id": "font-instrument-serif", "title": "Instrument Serif", "author": "The Instrument Serif Project Authors", "license": "SIL Open Font License 1.1",
         "license_url": "https://openfontlicense.org", "source_url": "https://github.com/Instrument/instrument-serif", "file_url": "",
         "local_path": "/home/user/bolas/paeleo/scion/oulipo/assets/fonts/instrument-serif.woff2",
         "what_it_shows": "caption typeface", "verified_date_or_place": "OFL text shipped beside the font", "used_as": "caption and card typography"}
    ],
    "handmade": [
        {"item": "five second-person clauses (original English; not Perec's text)", "where": "this ledger, takeA.srt, takeB.srt"},
        {"item": "referent tags, bind relations, viewpoint role table", "where": "this ledger"},
        {"item": "pure-Python gate", "where": str(SWARM / "u3-gate.py")},
        {"item": "caption typography proof (Instrument Serif, OFL font shipped in assets/fonts)",
         "where": str(SWARM / "u3-caption-proof.png")},
    ],
    "absences": [
        {"searched": "an openly licensed recording of a real voice speaking these lines",
         "result": "not sought further: the clauses are original text written for this film, so no existing recording of them can exist; no TTS is available. Voice is captions only (plan §3)."}
    ],
}


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(k):
    lines = []
    for i, c in enumerate(clauses, 1):
        a, b = c["tracks"][k]["interval"]
        lines += [str(i), f"{srt_time(a)} --> {srt_time(b)}", c["text"], ""]
    (SWARM / f"take{k}.srt").write_text("\n".join(lines))


if __name__ == "__main__":
    write_srt("A")
    write_srt("B")
    (SWARM / "u3-clause-ledger.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")
    print("wrote ledger + srts")
