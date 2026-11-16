"""teuf-teuf: regenerate the dual-column score (score.json, score.md) from the RENDER (editor repair 2).

The review found score.md/score.json still carrying the commentary-sound unit's pre-repair
numbers (sim.py's sheet). This script rewrites both from the ledgers the film is actually
built from, so every time in the score is a time in the picture:

  * exposure.json      (verify_sheet.py: events measured on the rendered frames' fixture)
  * assembly-cues.json (films/teuf-teuf.py: caption onsets/causes and every sound placed)
  * mechanism.json     (asserts and end points)

    python3 films/swarm/teuf-teuf/score_from_render.py      (after verify_sheet.py)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = json.load(open(os.path.join(HERE, "exposure.json")))
CUE = json.load(open(os.path.join(HERE, "assembly-cues.json")))
MECH = json.load(open(os.path.join(HERE, "mechanism.json")))
OLD = json.load(open(os.path.join(HERE, "score.json")))

EV = {}
for e in EXP["events"]:
    EV.setdefault(e["kind"], []).append(e["t"])


def E(kind, i=0):
    return round(EV[kind][i], 2)


CAPS = CUE["captions"]
C = {c["i"]: c for c in CAPS}
HOM = CUE.get("homage_line", {})
END = CUE.get("end_line", {})
stop_counter_m = round((CUE.get("counter_stop_F", 0) - 330.0) / 100.0, 2) if CUE.get("counter_stop_F") else None
ends = MECH["asserts"]["invariant_1_same_challenge"].get("end_points_m", {})


def snd(lo, hi):
    """the sound column: every placed sound between lo and hi (from the film's own log)"""
    out = []
    for s in CUE["sound_events"]:
        t = s["t"]
        if isinstance(t, (int, float)) and lo <= t < hi and not s["what"].startswith("footstep"):
            out.append(f"{t:.2f} {s['what']}")
    nf = sum(1 for s in CUE["sound_events"] if isinstance(s["t"], (int, float)) and lo <= s["t"] < hi and s["what"].startswith("footstep"))
    if nf:
        out.append(f"{nf} footsteps on the IK plants")
    return out


SHOTS = [
    ("0", 0.0, 4.0, "The toned wall fades up; the title is scratched in white (0.85-2.05 s); the pusher walks in; the carrier stands at the rope.",
     f"{HOM.get('on', 1.6)}-{HOM.get('off', 3.9)} s lineage line: after Jean Jabely's Teuf-Teuf (1956), original captions"),
    ("1", 4.0, 13.0, f"DRAG. 9 stick-slip lurches (first slip {E('slip', 0)} s); the 4th stick begins {E('stick', 3)} s; push ends {E('drag-stop')} s at 1.20 m; 1.2 m ghost scratched in at 11.7 s. Reset cut at 13.0 s (held black, scratch wipe).",
     f"caption 1 at {C[1]['on']} s"),
    ("2", 13.0, 14.0, f"SUBSTITUTE I. Stone levered up in 3 frames (lift {E('lift')} s); three bark logs rolled in ({', '.join(str(round(t, 2)) for t in EV['log-in'])} s); settles {E('settle')} s.", "-"),
    ("3a", 14.0, 16.2, "ROLLERS, wide; the camera pushes in to x1.28 over 14.0-14.5 s so the logs read as logs; logs turn at v/2 and drift back; the carrier walks to log D and picks it up.", "-"),
    ("3b", 16.2, 18.8, f"TEST SHOT, close-up x2.2 at the same tau. Log A squeezed out behind ({E('release', 0)} s) and stops ({E('log-stop', 0)} s, tok); the stone waits from {E('stone-stop')} s.",
     f"caption 2 at {C[2]['on']} s (the only nonhuman line)"),
    ("3c", 18.8, 21.0, f"Wide (push-in framing). The carrier sets log D down in front ({E('log-set')} s); push resumes 19.6 s; the stone rides onto D ({E('log-under')} s).", "-"),
    ("3d/3e", 21.0, 25.0, f"Rolls on; log B also left behind ({E('log-stop', 1)} s); stops at 3.00 m ({E('stone-stop-2')} s); the camera pulls back to the full wall 23.0-23.6 s; 3 m ghost at 23.15 s. Reset cut 25.0 s.", "-"),
    ("4", 25.0, 34.0, f"WHEEL AND AXLE. Plank cart on two Ljubljana-wheel cutouts; the carrier walks ahead of the load, clear of it; passes 3 m at {E('pass-3m')} s; 8.00 m at {E('wheel-stop')} s; 8 m ghost at 33.35 s. Reset cut 34.0 s.",
     f"caption 3 at {C[3]['on']} s"),
    ("5", 34.0, 38.0, f"COUNTER-CHECK. Pins pulled {E('pin-pull')} s; same push from 35.0 s; the loose wheels drift back under the platform; the rear wheel rolls out at {E('wheel-drop')} s, kicked out behind the pusher in front of his legs, and settles behind him ({E('loose-wheel-stop')} s, tok); the platform's rear falls for 0.30 s and lands {E('platform-lands')} s; grinds to a stop at {E('stop-counter')} s, {ends.get('counter', '0.82')} m.",
     f"caption 4 at {C[4]['on']} s"),
    ("6", 38.0, 44.0, f"COMPARISON HELD. Three ghosts (1.2 / 3.0 / 8.0 m); the figures sit; the loose wheel lying behind rocks once ({E('callback')} s, tok).",
     f"{END.get('on', 39.8)}-{END.get('off', 44.0)} s end line written on, staged-sequence label first, then sources"),
]


def main():
    shots = [dict(shot=i, t0=a, t1=b, picture=p, commentary=c, sound=snd(a, b)) for i, a, b, p, c in SHOTS]
    score = dict(
        film="teuf-teuf", unit="montage editor (repair 2: regenerated from the render)", direction=OLD.get("direction"),
        fps=24, duration_s=44.0,
        about="Dual-column score: picture | commentary | sound, regenerated by score_from_render.py from exposure.json (rendered-frame events), "
              "assembly-cues.json (caption onsets and every sound the film places) and mechanism.json. Supersedes the commentary-sound unit's sim-based score.",
        sources=dict(exposure="exposure.json", cues="assembly-cues.json", mechanism="mechanism.json"),
        columns=["picture", "commentary", "sound"],
        shots=shots,
        captions=[dict(i=c["i"], on=c["on"], off=c["off"], cause=c["cause"], cause_t=c["cause_t"], lag_s=c["lag_s"],
                       fr=c["fr"], en=c["en"], voice=c["voice"]) for c in CAPS],
        caption_style=OLD.get("caption_style"),
        homage_line=HOM,
        end_line=END,
        events=EXP["events"],
        sound_events=CUE["sound_events"],
        sound_build="films/teuf-teuf.py build_sound(): foraged knocks/steps/gravel cut by the commentary-sound unit (sources/teuf-teuf/commentary-sound/cut-*.wav) and its room stem (stem-room.wav) placed on the render's events; scrape, grind, rumble, scratch and thuds synthesized",
        evidence=OLD.get("evidence"), handmade=OLD.get("handmade"), absences=OLD.get("absences"),
        notes=["Caption 4's cause is the pin pull (bar 10.5), measured on the render.",
               "The pass at 3 m has no contact sound on purpose: the caption is its voice."],
    )
    json.dump(score, open(os.path.join(HERE, "score.json"), "w"), indent=1, ensure_ascii=False)
    L = ["# teuf-teuf: dual-column score (regenerated from the render, repair 2)", "",
         "44.0 s, 24 fps. Every time below is read from `exposure.json` (events of the rendered frames) or `assembly-cues.json` (what `films/teuf-teuf.py` placed). Built by `score_from_render.py`.", "",
         "| shot | time (s) | picture | commentary | sound |", "|---|---|---|---|---|"]
    for s in shots:
        L.append(f"| {s['shot']} | {s['t0']}–{s['t1']} | {s['picture']} | {s['commentary']} | {'; '.join(s['sound']) or '-'} |")
    L += ["", "## Captions (onset 0.2–0.6 s after the measured cause)", "", "| # | on–off | cause (t) | lag | FR | EN |", "|---|---|---|---|---|---|"]
    for c in CAPS:
        L.append(f"| {c['i']} | {c['on']}–{c['off']} | {c['cause']} ({c['cause_t']}) | {c['lag_s']} | {c['fr']} | {c['en']} |")
    L += ["", f"Lineage line {HOM.get('on')}–{HOM.get('off')} s: {HOM.get('fr', '')} / {HOM.get('en', '')}",
          f"End line {END.get('on')}–{END.get('off')} s: {' / '.join(END.get('lines', []))}", ""]
    open(os.path.join(HERE, "score.md"), "w").write("\n".join(L) + "\n")
    print("score regenerated:", len(shots), "shots,", len(CAPS), "captions,", len(CUE["sound_events"]), "sounds")


if __name__ == "__main__":
    main()
