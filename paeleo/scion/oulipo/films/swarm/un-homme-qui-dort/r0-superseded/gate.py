#!/usr/bin/env python3
"""Grammar / referent gate for "Un homme qui dort" (SCION, plan-r1, unit U3).

Plain Python, standard library only. Imports nothing from downloads.

    python3 -I gate.py [clauses.json] [--report referent-audit.json]

Checks plan section 3.2 preconditions on the clause ledger:
  G1  person == 2 and the text passes the grammar gate (subject "You", or a
      declared imperative; no he/she/him/his/I/we... narrating; <= 7 words)
  G2  addressee_id == ADDR-1 and no addressee shift is declared
  G5  the text is identical string-for-string in take A and take B
  G6  the relation is computed from d = onset - event onset:
        anticipates d <= -0.5, overlaps |d| < 0.5, lags d >= +0.5;
      take A needs anticipates with d = -1.2 +/- 0.1,
      take B needs lags with d = +1.4 +/- 0.1
  G7  [onset, offset] lies inside [0, 35.0] and meets no SilenceSpan
Also: the bound event exists (part of precondition 3), the caption lasts 1.6 s,
cues in a take do not overlap, and every SRT file matches the ledger.

Then it runs the fixtures (section 3.4 / prompt section 7), FAILs the baseline,
and writes a referent audit (what image each "you" lies over, from picture.json
if present). Exit status 0 only if the film takes pass AND every fixture gives
its expected verdict (expected FAILs must fail).
"""
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EPS = 1e-6

FORBIDDEN = {
    # third person narrating
    "he", "she", "him", "his", "her", "hers", "himself", "herself",
    "they", "them", "their", "theirs", "themselves",
    # first person narrating
    "i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves",
}
SECOND = {"you", "your", "yours", "yourself"}
NOT_IMPERATIVE_START = FORBIDDEN | SECOND | {"it", "the", "a", "an", "this", "that", "there", "one", "someone"}
MAX_WORDS = 7


# ------------------------------------------------------------------ grammar --
def words(text):
    return re.findall(r"[A-Za-z']+", text)


def grammar(text, mood="indicative"):
    """Return (ok, inferred_person, reasons)."""
    w = words(text)
    low = [x.lower() for x in w]
    reasons = []
    if not w:
        return False, None, ["empty text"]
    first = [x for x in low if x in {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}]
    third = [x for x in low if x in {"he", "she", "him", "his", "her", "hers", "himself", "herself",
                                     "they", "them", "their", "theirs", "themselves"}]
    if first:
        reasons.append(f"first-person narrating word(s): {first}")
    if third:
        reasons.append(f"third-person narrating word(s): {third}")
    if mood == "imperative":
        if low[0] in NOT_IMPERATIVE_START:
            reasons.append(f"declared imperative but starts with {w[0]!r}")
        subject_ok = low[0] not in NOT_IMPERATIVE_START
    else:
        subject_ok = w[0] == "You"
        if not subject_ok:
            reasons.append(f"subject is {w[0]!r}, not 'You'")
    if len(w) > MAX_WORDS:
        reasons.append(f"{len(w)} words > {MAX_WORDS}")
    if first:
        person = 1
    elif third or not subject_ok:
        person = 3
    else:
        person = 2
    return (not reasons), person, reasons


# ----------------------------------------------------------------- relation --
def relation(d):
    if d <= -0.5 + EPS:
        return "anticipates"
    if d >= 0.5 - EPS:
        return "lags"
    return "overlaps"


REQUIRED = {"A": ("anticipates", -1.2), "B": ("lags", +1.4)}


def check_clause(c, take, L, partner_texts=None):
    """Run G1 G2 G5 G6 G7 (+ event, duration) for one clause in one take."""
    t = c["takes"][take]
    on, off = float(t["onset"]), float(t["offset"])
    events = {e["event_id"]: e for e in L["events"]}
    out = {"clause_id": c["clause_id"], "take": take, "text": c["text"],
           "onset": on, "offset": off, "gates": {}}
    g = out["gates"]

    ok, person, why = grammar(c["text"], c.get("mood", "indicative"))
    if c.get("person") != 2:
        why = why + [f"declared person {c.get('person')} != 2"]
    if person != c.get("person"):
        why = why + [f"inferred person {person} != declared {c.get('person')}"]
    g["G1_grammar"] = {"pass": ok and c.get("person") == 2 and person == 2,
                       "inferred_person": person, "reasons": why}

    shifts = L.get("addressee_shifts", [])
    r2 = []
    if c.get("addressee_id") != "ADDR-1":
        r2.append(f"addressee_id {c.get('addressee_id')!r} != 'ADDR-1'")
    if shifts:
        r2.append(f"addressee shift declared: {shifts}")
    g["G2_addressee"] = {"pass": not r2, "reasons": r2}

    # G5: same clause_id has the same text in A and B
    r5 = []
    texts = partner_texts if partner_texts is not None else {
        k: c["text"] for k in c["takes"]}
    if set(texts) != {"A", "B"}:
        r5.append(f"clause has takes {sorted(texts)}, needs exactly A and B")
    elif texts["A"] != texts["B"]:
        r5.append(f"text differs: A={texts['A']!r} B={texts['B']!r}")
    g["G5_identical_text"] = {"pass": not r5, "reasons": r5}

    # event existence (precondition 3, existence part only)
    ev = events.get(c.get("event_id"))
    r3 = [] if ev and ev.get("kind") != "silence" else [f"event {c.get('event_id')!r} missing or is a silence span"]
    g["event_exists"] = {"pass": not r3, "reasons": r3}

    # G6
    r6 = []
    d = rel = None
    if ev:
        d = round(on - float(ev["onset"]), 3)
        rel = relation(d)
        if take not in REQUIRED:
            r6.append(f"take {take!r} is neither A nor B; computed relation {rel}")
        else:
            need, target = REQUIRED[take]
            if rel != need:
                r6.append(f"computed {rel} (d={d:+.3f}), take {take} needs {need}")
            if abs(d - target) > 0.1 + EPS:
                r6.append(f"d={d:+.3f} outside {target:+.1f} +/- 0.1")
        dec = t.get("declared_relation")
        if dec and dec != rel:
            r6.append(f"declared {dec!r} but computed {rel!r}")
    else:
        r6.append("no event to bind")
    g["G6_relation"] = {"pass": not r6, "d": d, "computed": rel, "reasons": r6}

    # G7
    r7 = []
    T = float(L["picture_length"])
    if on < -EPS or off > T + EPS:
        r7.append(f"[{on}, {off}] not inside [0, {T}]")
    for s in L["silence_spans"]:
        if on < s["end"] - EPS and off > s["start"] + EPS:
            r7.append(f"[{on}, {off}] intersects {s['span_id']} [{s['start']}, {s['end']}]")
    g["G7_silence_bounds"] = {"pass": not r7, "reasons": r7}

    dur = round(off - on, 3)
    g["duration"] = {"pass": abs(dur - float(L["caption_duration"])) <= EPS,
                     "value": dur}
    out["pass"] = all(v["pass"] for v in g.values())
    return out


def check_take(clauses, take, L):
    rows = []
    for c in clauses:
        if take not in c["takes"]:
            continue
        texts = {k: c["text"] for k in c["takes"]}
        rows.append(check_clause(c, take, L, texts))
    # cues in one take must not overlap each other
    iv = sorted((r["onset"], r["offset"], r["clause_id"]) for r in rows)
    clashes = [f"{a[2]} [{a[0]},{a[1]}] overlaps {b[2]} [{b[0]},{b[1]}]"
               for a, b in zip(iv, iv[1:]) if b[0] < a[1] - EPS]
    rels = [r["gates"]["G6_relation"]["computed"] for r in rows]
    return {"take": take, "pass": all(r["pass"] for r in rows) and not clashes and bool(rows),
            "relations": rels, "cue_overlaps": clashes, "clauses": rows}


# ---------------------------------------------------------------------- srt --
def parse_srt(path):
    txt = Path(path).read_text(encoding="utf-8")
    cues = []
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        v = [int(x) for x in m.groups()]
        a = v[0] * 3600 + v[1] * 60 + v[2] + v[3] / 1000
        b = v[4] * 3600 + v[5] * 60 + v[6] + v[7] / 1000
        cues.append((round(a, 3), round(b, 3), " ".join(lines[2:]).strip()))
    return cues


def is_label(cue):
    return cue[2].startswith("[") and cue[2].endswith("]") and cue[1] - cue[0] <= EPS


def compare_srt(path, expected):
    if not Path(path).exists():
        return {"file": str(path), "pass": False, "reasons": ["missing"]}
    got = [c for c in parse_srt(path) if not is_label(c)]
    reasons = []
    if len(got) != len(expected):
        reasons.append(f"{len(got)} cues, ledger has {len(expected)}")
    for i, (g, e) in enumerate(zip(got, expected), 1):
        if abs(g[0] - e[0]) > 0.001 or abs(g[1] - e[1]) > 0.001 or g[2] != e[2]:
            reasons.append(f"cue {i}: srt {g} != ledger {e}")
    return {"file": Path(path).name, "pass": not reasons, "cues": len(got), "reasons": reasons}


# ----------------------------------------------------------- referent audit --
def picture_segments(L):
    """(start, end, label, P1_in_frame) on the picture timeline."""
    pj = HERE / "picture.json"
    stair = [(0.0, 34 / 24, "empty stairwell (P-STAIR-EMPTY-1, from below)", False),
             (34 / 24, 82 / 24, "lodger on the stair (P-STAIR-MAN, profile, from beside/below)", True),
             (82 / 24, 6.0, "empty stairwell (P-STAIR-EMPTY-2, from above)", False)]
    source = "plan.md section 6 (picture.json absent)"
    if pj.exists():
        P = json.loads(pj.read_text())
        segs = P.get("stair_clip", {}).get("segments")
        fps = P.get("stair_clip", {}).get("fps", 24)
        if segs:
            e1, man, e2 = segs["P-STAIR-EMPTY-1"], segs["P-STAIR-MAN"], segs["P-STAIR-EMPTY-2"]
            stair = [(e1[0] / fps, (e1[1] + 1) / fps, stair[0][2], False),
                     (man[0] / fps, (man[1] + 1) / fps, stair[1][2], True),
                     (e2[0] / fps, (e2[1] + 1) / fps, stair[2][2], False)]
        source = "picture.json (U1) shots + stair_clip.segments"
    segs = [(0.0, 1.5, "black (declared darkness)", False),
            (1.5, 6.0, "SH1 bunk, lodger lying, eyes open (P-BUNK)", True),
            (6.0, 8.5, "SH2 wall telephone, no one at it (P-TEL)", False),
            (8.5, 12.0, "SH3 bunk, unmoved (P-BUNK)", True)]
    segs += [(12.0 + a, 12.0 + b, "SH4 " + lab, p) for a, b, lab, p in stair]
    segs += [(18.0, 24.0, "SH5 held room, empty beds and chair (P-ROOM crop)", False)]
    segs += [(24.0 + a, 24.0 + b, "SH6 " + lab, p) for a, b, lab, p in stair]
    segs += [(30.0, 35.0, "SH7 house from across the street at night (P-HOUSE)", False)]
    return [(round(a, 4), round(b, 4), lab, p) for a, b, lab, p in segs], source


def referent_audit(L):
    segs, source = picture_segments(L)
    rows = []
    for c in L["clauses"]:
        for take in ("A", "B"):
            on, off = c["takes"][take]["onset"], c["takes"][take]["offset"]
            over, p1 = [], 0.0
            for a, b, lab, p in segs:
                lo, hi = max(a, on), min(b, off)
                if hi > lo + EPS:
                    over.append({"from": round(lo, 3), "to": round(hi, 3), "image": lab, "P1_in_frame": p})
                    p1 += (hi - lo) if p else 0.0
            frac = round(p1 / (off - on), 3)
            if frac == 0:
                reading = "no body in frame: 'you' can only land on the viewer (V) or the place; P1 only by inference"
            elif frac == 1:
                reading = "P1 in frame throughout: 'you' lands on the lodger and/or the viewer"
            else:
                reading = "crosses a cut between body and no body: the referent of 'you' is split"
            rows.append({"clause_id": c["clause_id"], "take": take, "text": c["text"],
                         "interval": [on, off], "lies_over": over,
                         "P1_in_frame_fraction": frac, "reading": reading})
    stair_on = [s for s in segs if s[3] and s[0] >= 12.0]
    measured = []
    for c in L["clauses"]:
        if c["event_id"] in ("E4", "E6"):
            seen = [s[0] for s in stair_on if (s[0] < 18.0) == (c["event_id"] == "E4")][0]
            for take in ("A", "B"):
                d = round(c["takes"][take]["onset"] - seen, 4)
                measured.append({"clause_id": c["clause_id"], "take": take,
                                 "ledger_event_onset": [e["onset"] for e in L["events"] if e["event_id"] == c["event_id"]][0],
                                 "frame_onset_of_lodger": round(seen, 4), "d_against_frames": d,
                                 "within_tolerance": abs(d - REQUIRED[take][1]) <= 0.1 + EPS})
    return {"segments_source": source, "rows": rows, "stair_frame_onsets": measured,
            "flags": [
                "SH1/SH3 (P-BUNK): per picture.json the lodger looks toward the lens. 'You open your eyes' "
                "in take B lies over that gaze, which may pull 'you' onto the viewer more than onto him. "
                "Not a gate failure (camera_viewpoint is not his eyes); for the independent viewer.",
                "C5-A (defining beat) lies over the empty stairwell for 1.217 s of its 1.6 s, before the "
                "lodger appears (frame 34 of the stair clip = p 25.417); C5-B lies 0.617 s over the lodger "
                "and then 0.983 s over the emptied stairwell (after frame 82 = p 27.417).",
                "C6-A starts over the empty end of STAIR-2 and crosses the 30.0 cut to the house; C6/C7 "
                "otherwise lie over SH7 with no body in frame: 'you' there can only land on the viewer or "
                "the place.",
                "Performer identity across P-BUNK and P-STAIR-MAN is unverified (montage-constructed); "
                "no clause names him, so the voice does not assert it.",
            ]}


# ----------------------------------------------------------------- fixtures --
def clause(L, cid):
    return copy.deepcopy([c for c in L["clauses"] if c["clause_id"] == cid][0])


def fixtures(L):
    out = []

    def add(fid, desc, expect, result, focus=None, extra=None):
        got = "PASS" if result["pass"] else "FAIL"
        ok = got == expect
        if focus and expect == "FAIL":
            ok = ok and any(not r["gates"][focus]["pass"] for r in result.get("clauses", [result]))
        rec = {"fixture": fid, "description": desc, "expected": expect, "got": got,
               "as_expected": ok}
        if focus:
            rec["required_failing_gate"] = focus
        if extra:
            rec.update(extra)
        rec["detail"] = result
        out.append(rec)

    c2 = clause(L, "C2")
    assert c2["text"] == L["fixed_fixture"]["text"], "C2 is the fixed fixture and may not change"
    for take in ("A", "B"):
        add(f"F1-{take}", f"'You hear it through the wall.' bound to E2, take {take}",
            "PASS", check_clause(c2, take, L))

    he = clause(L, "C2")
    he["text"] = "He hears it through the wall."
    add("F2", "Narrator shift: 'He hears it through the wall.' (writer left person=2)",
        "FAIL", check_clause(he, "A", L), focus="G1_grammar")
    he3 = copy.deepcopy(he)
    he3["person"] = 3
    add("F2b", "Same, declared honestly as person=3", "FAIL", check_clause(he3, "A", L),
        focus="G1_grammar")

    a, b = check_clause(c2, "A", L), check_clause(c2, "B", L)
    both = {"pass": a["pass"] and b["pass"] and a["text"] == b["text"]
            and a["gates"]["G6_relation"]["computed"] == "anticipates"
            and b["gates"]["G6_relation"]["computed"] == "lags", "A": a, "B": b}
    add("F3", "Same words, two timelines: A computes anticipates, B computes lags", "PASS", both,
        extra={"A_relation": a["gates"]["G6_relation"]["computed"], "A_d": a["gates"]["G6_relation"]["d"],
               "B_relation": b["gates"]["G6_relation"]["computed"], "B_d": b["gates"]["G6_relation"]["d"]})

    c5 = clause(L, "C5")
    c5["takes"]["A"]["onset"], c5["takes"]["A"]["offset"] = 23.4, 25.0
    add("F4", "C5-A onset moved 24.2 -> 23.4 (starts over the held room SIL-1 18.0-24.0)",
        "FAIL", check_clause(c5, "A", L), focus="G7_silence_bounds")

    c4 = clause(L, "C4")
    for take in ("A", "B"):
        c4["takes"][take]["onset"], c4["takes"][take]["offset"] = 13.4, 15.0
        c4["takes"][take].pop("declared_relation", None)
        add(f"F5-{take}", f"Collapse: C4 placed at d = 0 in take {take} (computes overlaps)",
            "FAIL", check_clause(c4, take, L), focus="G6_relation")

    sh = clause(L, "C6")
    sh["addressee_id"] = "ADDR-2"
    add("F6", "Unmarked addressee shift on C6 (ADDR-2)", "FAIL", check_clause(sh, "A", L),
        focus="G2_addressee")

    ab = clause(L, "C3")
    ab["text"] = "You let it ring."
    ab_texts = {"A": "You let it ring.", "B": "You let the telephone ring."}
    add("F7", "C3 worded differently in B than in A", "FAIL",
        check_clause(ab, "A", L, ab_texts), focus="G5_identical_text")

    bl = L["baseline"]["clauses"]
    res = check_take(bl, "baseline", L)
    add("F8", "Baseline (third person, synchronised, clause over the held shot) from the ledger",
        "FAIL", res, focus="G1_grammar",
        extra={"failing_gates_per_clause": {r["clause_id"]: [k for k, v in r["gates"].items() if not v["pass"]]
                                            for r in res["clauses"]}})

    path = HERE / L["srt_files"]["baseline"]
    if path.exists():
        cues = [c for c in parse_srt(path) if not is_label(c)]
        g = [grammar(t) for _, _, t in cues]
        sil = [(a, b) for a, b, _ in cues for s in L["silence_spans"] if a < s["end"] and b > s["start"]]
        res2 = {"pass": all(x[0] for x in g) and not sil, "cues": len(cues),
                "grammar_fail": [t for (_, _, t), x in zip(cues, g) if not x[0]],
                "cues_in_silence": sil,
                "labelled_baseline_only": any(is_label(c) and "BASELINE" in c[2] for c in parse_srt(path))}
        add("F9", "baseline.srt read from disk", "FAIL", res2)
    return out


# --------------------------------------------------------------------- main --
def main(argv):
    ledger_path = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else HERE / "clauses.json"
    report_path = HERE / "referent-audit.json"
    if "--report" in argv:
        report_path = Path(argv[argv.index("--report") + 1])
    L = json.loads(ledger_path.read_text())

    takes = {t: check_take(L["clauses"], t, L) for t in ("A", "B")}

    exp = {"A": [], "B": [], "film": []}
    for c in L["clauses"]:
        for t in ("A", "B"):
            exp[t].append((c["takes"][t]["onset"], c["takes"][t]["offset"], c["text"]))
    for t in ("A", "B"):
        off = float(L["film_offsets"][t])
        exp["film"] += [(round(a + off, 3), round(b + off, 3), s) for a, b, s in exp[t]]
    exp["baseline"] = [(b["takes"]["baseline"]["onset"], b["takes"]["baseline"]["offset"], b["text"])
                       for b in L["baseline"]["clauses"]]
    srt = {k: compare_srt(HERE / L["srt_files"][k], exp[k]) for k in ("A", "B", "film", "baseline")}
    words_same = [x[2] for x in exp["A"]] == [x[2] for x in exp["B"]]

    diegetic = L.get("diegetic_speech", {})
    dieg_ok = diegetic.get("declared") == "empty" and not diegetic.get("cues")

    fx = fixtures(L)
    audit = referent_audit(L)

    film_pass = (takes["A"]["pass"] and takes["B"]["pass"] and words_same and dieg_ok
                 and all(srt[k]["pass"] for k in srt))
    fixtures_ok = all(f["as_expected"] for f in fx)
    report = {
        "gate": "films/swarm/un-homme-qui-dort/gate.py",
        "ledger": str(ledger_path),
        "base": L.get("base"),
        "preconditions_checked": ["G1 (3.2.1)", "G2 (3.2.2)", "G5 (3.2.5)", "G6 (3.2.6)", "G7 (3.2.7)",
                                  "event exists (part of 3.2.3)", "duration 1.6 s", "no cue overlap",
                                  "SRT files == ledger", "diegetic track empty"],
        "preconditions_not_checked_here": ["3.2.3 subject/sound-of-place typing beyond existence",
                                           "3.2.4 camera_viewpoint != eyes(P1) (picture unit / editor)",
                                           "3.2.8 frame identity of passes (editor)"],
        "verdict": "PASS" if film_pass and fixtures_ok else "FAIL",
        "film_takes_pass": film_pass,
        "fixtures_as_expected": fixtures_ok,
        "summary": {
            "take_A": {"pass": takes["A"]["pass"], "relations": takes["A"]["relations"]},
            "take_B": {"pass": takes["B"]["pass"], "relations": takes["B"]["relations"]},
            "identical_words_A_B": words_same,
            "srt": {k: v["pass"] for k, v in srt.items()},
            "diegetic_speech_empty": dieg_ok,
            "fixtures": {f["fixture"]: f"{f['got']} (expected {f['expected']})" for f in fx},
        },
        "takes": takes,
        "srt_checks": srt,
        "diegetic_speech": diegetic,
        "fixtures": fx,
        "referent_audit": audit,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"gate: {report['verdict']}   (report: {report_path})")
    for t in ("A", "B"):
        print(f"  take {t}: {'PASS' if takes[t]['pass'] else 'FAIL'}  relations={takes[t]['relations']}")
    print(f"  SRT == ledger: {report['summary']['srt']}   identical words A/B: {words_same}   diegetic empty: {dieg_ok}")
    for f in fx:
        print(f"  {f['fixture']:6s} {f['got']:4s} (expected {f['expected']}) {'ok' if f['as_expected'] else 'MISMATCH'}  {f['description']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
