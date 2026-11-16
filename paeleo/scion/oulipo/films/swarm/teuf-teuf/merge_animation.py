"""editor repair 1: fold the re-render's measured metrics (animation_metrics_tmp.json, report.py)
into animation.json, keeping the animator's evidence / handmade / absences records."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
a = json.load(open(os.path.join(H, "animation.json")))
m = json.load(open(os.path.join(H, "animation_metrics_tmp.json")))
for k in ("inputs", "outputs", "for_the_editor", "per_shot", "wide_closeup_agreement", "secondary_dynamics",
          "silhouette_read_test", "tone_composited_frames", "summary"):
    a[k] = m[k]
a["revision"] = "editor repair 1 (2026-11-16): re-rendered after the critic's review"
a["repair_1_changes"] = [
    "Contact solve in Puppet.build (#33): the root is moved so every foot target and every pinned/holding hand target lies inside limb reach, so IK end-effectors land on their targets (drag hands, shot-2 heave, log-D pick-up, fast walks).",
    "Sit-down feet are labelled planted only once the sit pose has settled.",
    "Rollers retimed to 7.0 s of push (14.0-17.6 + 19.6-23.0); log D set down 18.4-19.3; same stone-local hand height (-80/-60) in all trials.",
    "Figures 1.06x (was 0.95x), hips raised 9 px; the pale hairline joint seams removed; silhouette edges are a dry-brush fringe (static bristle field) and the halo is a blown-pigment spray (haze + specks), both fixed in the frame (no shimmer).",
    "Ghost outlines are not drawn in the x2.2 close-up (their broken edge read as a stray scratch across the figures).",
    "Wall plates (layout_wall.py): stencils as pale hands in dark blown halos, small guanacos faded, rock high-pass 0.25, bands pressed darker, the close-up keeps the top band.",
]
a["deviations_from_plan"] = [d for d in a.get("deviations_from_plan", []) if not d.startswith("Rollers:")] + [
    "Rollers: 7.0 s of push in two strokes, 14.0-17.6 and 19.6-23.0, with the stone waiting on two logs while log D is set down."]
a["known_gaps"] = ["See summary for the measured residuals of this render; mechanism.json asserts (verify_sheet.py) are run on these same frames."]
json.dump(a, open(os.path.join(H, "animation.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(a["summary"], indent=1))
