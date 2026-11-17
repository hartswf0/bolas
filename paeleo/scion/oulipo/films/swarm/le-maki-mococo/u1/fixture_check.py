"""Fixture check for cue_timeline.json: asserts precondition P1 of admit_reading (every cited cue released
at or before the response's t_said) for every response and every branch response, confirms the plan's
counterexample is rejected, and checks cue order and voice/response non-collision. Writes fixture_check."""
import json, sys, datetime
path = sys.argv[1]
tl = json.load(open(path))
rel = {c["cue_id"]: c["t_avail"] for c in tl["cues"]}
results, ok = [], True

def p1(r, rel):
    bad = [q for q in r["cites"] if rel.get(q) is None or rel[q] > r["t_said"]]
    return not bad, bad

for r in tl["responses"]:
    good, bad = p1(r, rel)
    results.append(dict(resp_id=r["resp_id"], t_said=r["t_said"], cites=r["cites"],
                        releases={q: rel.get(q) for q in r["cites"]}, P1=good, violations=bad))
    ok &= good
    ok &= "(fictional)" in r["speaker"] and r["consent"].startswith("fictional")
for r in tl["quarantined_counterexamples"]:
    good, bad = p1(r, rel)
    results.append(dict(resp_id=r["resp_id"], counterexample=True, P1=good, expected=False,
                        rejected=not good))
    ok &= not good
br = tl["branches"]["image_first"]
brel = {c["cue_id"]: c["t_avail"] for c in br["cues"]}
for r in br["responses"]:
    good, bad = p1(r, brel)
    results.append(dict(branch="image_first", resp_id=r["resp_id"], P1=good, violations=bad))
    ok &= good
order = rel["Q_sound"] < rel["Q_text"] < rel["Q_image"]
ok &= order
# voice placements must not overrun the next response or overlap each other
pl = sorted(tl["audio"]["placements"], key=lambda p: p["at"])
resp_t = sorted(r["t_said"] for r in tl["responses"])
coll = []
for a, b in zip(pl, pl[1:]):
    if a["end"] > b["at"]:
        coll.append(f"{a['shot']} ends {a['end']} after {b['shot']} starts {b['at']}")
s1 = [p for p in pl if p["shot"] == "S1"][0]; s3 = [p for p in pl if p["shot"] == "S3"][0]
# E3 (editor): compare against the responses' staged t_said (the ledger now records the cut), not the plan's 10/24
tR = {r["resp_id"]: r["t_said"] for r in tl["responses"]}
if s1["end"] > tR["R1"]: coll.append(f"S1 voice ends {s1['end']} > Reader A at {tR['R1']}")
if s3["end"] > tR["R2"]: coll.append(f"S3 voice ends {s3['end']} > Reader B at {tR['R2']}")
# responses must be verbatim and the shift must name the image clue
r3 = [r for r in tl["responses"] if r["resp_id"] == "R3"][0]
shift_ok = "by its tail" in r3["quoted_span"] and "Q_image" in r3["cites"]
ok &= shift_ok
# collisions are staging warnings, not P1 failures: a caption may appear while the cited cue is still sounding
recs = []
for c in coll:
    shot = c.split()[0]
    p = [q for q in pl if q["shot"] == shot][0]
    recs.append(dict(warning=c, option_a="keep plan time; caption lands over the last refrain (mouth keeps "
                     "speaking, the 'hm' gesture starts after the voice ends)",
                     option_b=f"delay the response to {round(p['end'] + 0.4, 2)} s (voice end + 0.4 s); label m:ss "
                              "changes accordingly; P1 still holds"))
fc = dict(script="u1/fixture_check.py", run=str(datetime.datetime.now().isoformat(timespec="seconds")),
          passed=bool(ok), P1=results, cue_order_ok=order, staging_warnings=recs,
          reconsideration_names_image_clue=shift_ok, evidence_label="measured (script assertion)")
tl["fixture_check"] = fc
json.dump(tl, open(path, "w"), indent=1, ensure_ascii=False)
print(json.dumps(dict(passed=fc["passed"], warnings=coll, cue_order_ok=order)))
assert ok, "fixture check failed"
