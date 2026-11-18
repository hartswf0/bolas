"""E3 editor: make cue_timeline.json a true record of the cut (critic + reviewer, repair round 1).
Writes the staged response times (option b, frame-aligned), the on-screen labels exactly as drawn, the R1
caption rewrite (no syllable spelling before Q_text), and keeps the plan times as plan_t_said. Then re-run
u1/fixture_check.py on the file."""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parent / "cue_timeline.json"
tl = json.loads(P.read_text())
ft = tl["audio"]["film_time"]
FPS = 24
def frame_after(t):
    import math
    return math.ceil(round(t * FPS, 6)) / FPS
staged = {"R1": frame_after(ft["S1"]["end"] + 0.4), "R2": frame_after(ft["S3"]["end"] + 0.4), "R3": 44.0, "R4": 48.5}
rel = {c["cue_id"]: c["t_avail"] for c in tl["cues"]}
NAME = {"Q_sound": "sound", "Q_text": "text", "Q_image": "image"}
def mss(t): return f"{int(t) // 60}:{int(t) % 60:02d}"
for r in tl["responses"]:
    rid = r["resp_id"]
    r.setdefault("plan_t_said", r["t_said"])
    r["t_said"] = round(staged[rid], 4)
    r["label_time"] = mss(r["t_said"])
    if rid == "R1" and "bin, tu" in r["quoted_span"]:
        r["quoted_span_plan"] = r["quoted_span"]
        r["quoted_span"] = "A gong? Something you strike."
        r["quoted_span_source"] = ("plan.md §6, revised by the editor in repair round 1 (reviewer): the plan's "
                                   "'— bin, tu, RONG.' spelled the word before Q_text; the guess is unchanged")
    cites = [NAME[q] + (f" ({mss(rel[q])})" if q == "Q_image" else "") for q in ("Q_sound", "Q_text", "Q_image") if q in r["cites"]]
    r["on_screen_label"] = f"{r['speaker'].upper().replace('(FICTIONAL)', '(fictional)')} · {r['label_time']} · cites: {', '.join(cites)}"
    r["first_frame_shown"] = round(r["t_said"], 4)
    if rid in ("R1", "R2"):
        r["staging"] = ("option (b): said 0.4 s after the measured voice it answers ends, rounded up to the next frame; "
                        f"plan time {r['plan_t_said']} kept as plan_t_said (the measured voice runs past it)")
tl.setdefault("editor_staging", {})["E3"] = dict(
    note="responses' t_said / label / first frame on screen are the cut's; ledger time, label and first frame agree",
    staged=staged)
P.write_text(json.dumps(tl, indent=1, ensure_ascii=False))
print(json.dumps({r["resp_id"]: (r["t_said"], r["on_screen_label"]) for r in tl["responses"]}, ensure_ascii=False, indent=0))
