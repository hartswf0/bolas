"""editor: ledger linking each shot to the ONE sheet (exposure.json = rendered frames), animation, layout and score revisions."""
import hashlib, json, os
H = os.path.dirname(os.path.abspath(__file__)); F = os.path.dirname(os.path.dirname(H)); R = os.path.dirname(F)
def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:12] if os.path.exists(p) else None
files = ["swarm/teuf-teuf/exposure.json", "swarm/teuf-teuf/mechanism.json", "swarm/teuf-teuf/animation.json",
         "swarm/teuf-teuf/layout.json", "swarm/teuf-teuf/layout_wall.py", "swarm/teuf-teuf/score.json", "swarm/teuf-teuf/score.md", "swarm/teuf-teuf/score_from_render.py", "swarm/teuf-teuf/register.json",
         "swarm/teuf-teuf/animator-build/motion.py", "swarm/teuf-teuf/animator-build/anim.py", "swarm/teuf-teuf/verify_sheet.py",
         "sources/teuf-teuf/animator/animator_master_0-44s.mp4", "sources/teuf-teuf/animator/frames_metrics.json",
         "sources/teuf-teuf/layout/frameA_lum.npy", "sources/teuf-teuf/layout/frameB_lum.npy", "sources/teuf-teuf/sound/stem-room.wav",
         "teuf-teuf.py", "credits/teuf-teuf.json", "notes/teuf-teuf.txt", "../assets/films/teuf-teuf.mp4", "../assets/films/teuf-teuf-nocaption.mp4"]
an = json.load(open(os.path.join(H, "animation.json"))); me = json.load(open(os.path.join(H, "mechanism.json")))
cues = json.load(open(os.path.join(H, "assembly-cues.json")))
shots = []
for name, ps in an["per_shot"].items():
    a, b = ps["film_time_s"]
    shots.append({"shot": name, "film_time_s": [a, b], "frames": ps["frames"], "camera": ps["camera"],
                  "picture": f"sources/teuf-teuf/animator/shot_{name}.mp4 (via animator_master_0-44s.mp4)",
                  "sheet": "swarm/teuf-teuf/exposure.json frames %d-%d (rendered frames)" % tuple(ps["frames"]),
                  "plates": "layout frame%s_lum.npy" % ("B" if ps["camera"] == ["B"] else "A") + ("; push-in crops of master_lum_x2.2.npy (x1.28)" if name in ("3a_rollers_wide", "3c_carrier_sets_log", "3d_rollers_on", "3e_hold_3m") else ""),
                  "metrics": {w: ps[w] for w in ("pusher", "carrier")} | {k: ps[k] for k in ps if k.startswith(("roller", "loose", "max_stone", "stone_front"))},
                  "captions": [c["fr"] for c in cues["captions"] if a <= c["on"] < b],
                  "sound_events": [e["what"] for e in cues["sound_events"] if isinstance(e["t"], (int, float)) and a <= e["t"] < b]})
json.dump({"film": "teuf-teuf", "unit": "montage-editor", "date": "2026-11-16", "repair": 2,
           "single_ledger": "exposure.json is the rendered frames' sheet; mechanism.json asserts run on it (verify_sheet.py); sim.py's sheet is in superseded/",
           "revisions_md5_12": {f: md5(os.path.join(F, f)) for f in files},
           "asserts_all_pass": me["asserts"]["all_pass"], "declared_cuts_s": me["asserts"]["invariant_3_continuity"]["declared_cuts_s"],
           "caption_cues": me["caption_cues"], "shots": shots}, open(os.path.join(H, "ledger.json"), "w"), indent=1, ensure_ascii=False)
print("ledger ok", me["asserts"]["all_pass"])
