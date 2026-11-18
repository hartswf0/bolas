#!/usr/bin/env python3
"""validate_voice.py -- U3 check of voice_score.json (les-lieux-dune-fugue).

Fails (exit 1) on:
  * an exact remembered date/year without an evidence id in the evidence register
    (type Exact, or an exact date/year written into text_fr / gloss_en / labels / on-screen flags);
  * an inferred place link that is not flagged INFÉRÉ on screen (inside the caption window);
  * a caption (or its on-screen flag) outside the shot that carries it, crossing a cut,
    overlapping another caption, or falling in the declared silence window;
  * pairing errors from the Olog: unknown place/obs, bad status, a dislocated beat not
    flagged, or a dislocated memory lit with a stage lamp state;
  * a caption line wider than its max width, or placed outside the frame.

Also runs the counterexamples recorded in the score (each must FAIL) so the checker is
shown to bite. Usage: python3 validate_voice.py [voice_score.json] [--json report.json]
"""
import copy, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = (960, 720)
SILENCE = (44.0, 57.0)
STATUSES = {"asserted", "inferred", "unknown"}
PLACES = {"P01", "P02", "P03"}
MONTHS = "janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre|january|february|march|april|may|june|july|august|september|october|november|december"
EXACT_PATTERNS = [
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),                       # ISO date
    re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"),                # 12/01/1952
    re.compile(r"\b\d{1,2}(er)?\s+(%s)(\s+\d{2,4})?\b" % MONTHS, re.I),  # 12 janvier (1952)
    re.compile(r"\b(%s)\s+\d{1,2},?\s+\d{4}\b" % MONTHS, re.I),      # January 12, 1952
    re.compile(r"\b(1[89]\d\d|20\d\d)\b"),                           # a bare year is an exact claim
]


def exact_hits(s):
    return [m.group(0) for p in EXACT_PATTERNS for m in p.finditer(s or "")]


def within(inner, outer, eps=1e-6):
    return inner[0] >= outer[0] - eps and inner[1] <= outer[1] + eps and inner[0] < inner[1]


def text_width(spec, s):
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(spec["font"], spec["size_px"])
        return f.getlength(s)
    except Exception:
        return None


def validate(doc, measure=True):
    errs = []
    evidence = {e["id"] for e in doc.get("evidence", [])}
    shots = {s["obs_id"]: s for s in doc["shots"]}
    lamps = doc.get("lamp_states", {})
    stage_states = {s["lamp_state"] for s in doc["shots"]}
    windows = []
    for f in doc["fragments"]:
        fid = f["frag_id"]
        # --- required fields
        for k in ("speaker", "text_fr", "gloss_en", "remembered_time", "place_link", "confidence",
                  "provenance", "screen_time", "dislocated", "layout"):
            if k not in f:
                errs.append(f"{fid}: missing field {k}")
        rt = f.get("remembered_time", {})
        # --- I2: remembered time typed, no exact without evidence
        t = rt.get("type")
        if t not in ("Interval", "Unknown", "Exact"):
            errs.append(f"{fid}: remembered_time.type must be Interval/Unknown/Exact, got {t!r}")
        if t == "Exact" and rt.get("evidence_id") not in evidence:
            errs.append(f"{fid}: exact remembered_time {rt.get('value')!r} without evidence")
        if t == "Interval" and ("lo" not in rt or "hi" not in rt or rt.get("lo") == rt.get("hi")):
            errs.append(f"{fid}: Interval needs distinct lo and hi")
        texts = [f.get("text_fr"), f.get("gloss_en"), rt.get("label"), str(rt.get("value", "")),
                 str(rt.get("lo", "")), str(rt.get("hi", ""))] + [x.get("text") for x in f.get("on_screen_flags", [])]
        if t != "Exact" or rt.get("evidence_id") not in evidence:
            for s in texts:
                for h in exact_hits(s):
                    errs.append(f"{fid}: exact date/year {h!r} in {s!r} without evidence")
        if "provenance" in f and not f["provenance"]:
            errs.append(f"{fid}: empty provenance")
        # --- link status
        pl = f.get("place_link", {})
        st = pl.get("status")
        if st not in STATUSES:
            errs.append(f"{fid}: place_link.status {st!r} not in {sorted(STATUSES)}")
        if pl.get("place_id") is not None and pl["place_id"] not in PLACES:
            errs.append(f"{fid}: unknown place {pl['place_id']}")
        if st == "asserted" and pl.get("place_id") is None:
            errs.append(f"{fid}: asserted link with no place")
        # --- shot containment (pair precondition 4)
        obs = shots.get(f.get("obs_id"))
        if obs is None:
            errs.append(f"{fid}: obs_id {f.get('obs_id')!r} not in shot register")
            continue
        st_win = f.get("screen_time", [0, 0])
        if not within(st_win, obs["screen_time"]):
            errs.append(f"{fid}: caption {st_win} outside its shot {obs['obs_id']} {obs['screen_time']}")
        if st_win[0] < SILENCE[1] and st_win[1] > SILENCE[0]:
            errs.append(f"{fid}: caption {st_win} falls in declared silence {list(SILENCE)}")
        windows.append((st_win, fid))
        flags = f.get("on_screen_flags", [])
        for fl in flags:
            if not within(fl.get("window", [0, 0]), st_win):
                errs.append(f"{fid}: on-screen flag window {fl.get('window')} outside caption {st_win}")
        # --- inferred links flagged on screen
        if st == "inferred":
            if not any("INFÉRÉ" in (fl.get("text") or "") and within(fl.get("window", [0, 0]), st_win) for fl in flags):
                errs.append(f"{fid}: inferred link to {pl.get('place_id')} not flagged INFÉRÉ on screen")
        # --- dislocation (pair preconditions 5 and 6)
        linked = pl.get("place_id")
        should = linked is not None and linked != obs["place_id"]
        if should and not f.get("dislocated"):
            errs.append(f"{fid}: links {linked} over {obs['place_id']} but dislocated is not true")
        if f.get("dislocated") and not should:
            errs.append(f"{fid}: dislocated=true but link {linked} is the observed place {obs['place_id']}")
        if f.get("dislocated"):
            ml = (f.get("dislocation") or {}).get("memory_light", "")
            key = ml.split()[0] if ml else ""
            if not ml or key in stage_states or key in ("A", "B"):
                errs.append(f"{fid}: dislocated memory lit with stage state {key!r} (must be its own light)")
            if st == "asserted" and not pl.get("evidence_id"):
                errs.append(f"{fid}: dislocated link asserted without evidence")
        # --- layout: inside frame, fits width, typography distinct from slates
        lay = f.get("layout", {})
        for part in ("fr", "en", "record_line"):
            spec = lay.get(part)
            if not spec:
                if part != "record_line":
                    errs.append(f"{fid}: layout.{part} missing")
                continue
            y = spec.get("y", -1)
            if not (0 < y - spec["size_px"] and y + 0.3 * spec["size_px"] < FRAME[1]):
                errs.append(f"{fid}: layout.{part} y={y} outside frame")
            if measure:
                s = {"fr": f.get("text_fr"), "en": f.get("gloss_en")}.get(part)
                if part == "record_line":
                    s = max((fl["text"] for fl in flags), key=len, default="")
                w = text_width(spec, s)
                if w is not None and w > lay.get("max_width_px", FRAME[0]):
                    errs.append(f"{fid}: layout.{part} {w:.0f}px wider than {lay.get('max_width_px')}")
        if "Italic" not in lay.get("fr", {}).get("font", ""):
            errs.append(f"{fid}: French voice must be serif italic")
        if "Mono" in lay.get("fr", {}).get("font", ""):
            errs.append(f"{fid}: voice set in mono (slate face)")
    windows.sort()
    for (a, fa), (b, fb) in zip(windows, windows[1:]):
        if b[0] < a[1]:
            errs.append(f"{fa}/{fb}: captions overlap {a} {b}")
    return errs


def apply_mutation(doc, mutation):
    d = copy.deepcopy(doc)
    for path, val in mutation.items():
        fid, *keys = path.split(".")
        node = next(f for f in d["fragments"] if f["frag_id"] == fid)
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = val
    return d


def main():
    argv = sys.argv[1:]
    if "--json" in argv:
        i = argv.index("--json"); argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    path = args[0] if args else os.path.join(HERE, "voice_score.json")
    doc = json.load(open(path, encoding="utf-8"))
    errs = validate(doc)
    report = {"score": path, "errors": errs, "counterexamples": []}
    print(f"voice_score: {len(doc['fragments'])} fragments, {len(errs)} error(s)")
    for e in errs:
        print("  FAIL", e)
    cx_ok = True
    for cx in doc.get("counterexamples", []):
        ce = validate(apply_mutation(doc, cx["mutation"]), measure=False)
        bit = bool(ce)
        cx_ok &= bit
        report["counterexamples"].append({"id": cx["id"], "rejected": bit, "first_error": ce[0] if ce else None})
        print(f"  counterexample {cx['id']}: {'rejected (good)' if bit else 'ACCEPTED (checker too weak)'}" + (f" -- {ce[0]}" if ce else ""))
    report["pass"] = not errs and cx_ok
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump(report, open(out, "w"), indent=1, ensure_ascii=False)
    print("PASS" if report["pass"] else "FAIL")
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
