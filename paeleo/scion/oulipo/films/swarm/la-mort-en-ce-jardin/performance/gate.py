# Invariant gate (plan sections 4-5; SCION #48 state machine + #32 FK checks).
#   python3 -I gate.py trace-L.json [trace-E.json ...]       -> PASS/FAIL per trace, exit 1 on any FAIL
#   python3 -I gate.py --counterexamples                        -> builds the three plan-section-4 counterexamples from
#                                                                  trace-L.json and shows that each one FAILS
# Checks, every frame:
#   G1 plank occupancy <= 1
#   G2 every person grips <= 2 things (one per hand); the plank occupant has exactly one hand on the liana
#   G3 exactly one holder per object (bag always; shoe once it has appeared)
#   G4 a holder change happens only at a logged handoff/retrieve/hand_swap event (+-1 frame), with the giving and
#      receiving hands (or the shoe and the taking hand) within 40 px at that frame
#   G5 bone lengths invariant and pivots attached: FK recomputed from the stored root + whole-degree angles, error < 0.5 px,
#      and the stored hand points agree with FK (< 0.5 px)
#   G6 the bag's bottom stays above the water line
import sys, json, math, copy
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rig import fk, bone_error, FPS  # noqa: E402

HAND_RADIUS = 40.0


def gate(tr, name="trace", max_report=6):
    fails = {k: [] for k in ("G1_plank", "G2_hands", "G3_holders", "G4_events", "G5_bones", "G6_dry")}
    ev = tr["events"]; F = tr["frames"]
    rig_err = 0.0; per_joint = {}
    prev = None
    for st in F:
        t = st["t"]; P = st["people"]
        if len(st["plank_occupant"]) > 1:
            fails["G1_plank"].append((t, f"occupants {st['plank_occupant']}"))
        for w, p in P.items():
            held = [it for it in p["grips"].values() if it != "free"] + p.get("extra_grips", [])
            if len(held) > 2: fails["G2_hands"].append((t, f"{w} holds {held}: more than two hands"))
            if w in st["plank_occupant"] and held.count("liana") != 1:
                fails["G2_hands"].append((t, f"{w} on the plank with {held.count('liana')} hands on the liana"))
            J = fk(p["root"], p["a"])
            e = bone_error(J)
            for b, x in e.items(): per_joint[b] = max(per_joint.get(b, 0), x)
            m = max(e.values())
            for h, bone in (("L", "hand_f"), ("R", "hand_n")):
                m = max(m, math.dist(J[bone][1], p["hands"][h]) - 0.01)    # stored hand point is rounded to 0.01
            rig_err = max(rig_err, m)
            if m >= 0.5: fails["G5_bones"].append((t, f"{w} rig error {m:.3f} px"))
        hold = {}
        for obj in ("bag", "shoe"):
            hs = list(st.get(obj, []))
            hs += [f"{w}.x" for w, p in P.items() if obj in p.get("extra_grips", [])]
            hold[obj] = hs
            if obj == "bag" and len(hs) != 1: fails["G3_holders"].append((t, f"bag holders {hs}"))
            if obj == "shoe" and len(hs) > 1: fails["G3_holders"].append((t, f"shoe holders {hs}"))
            if obj == "shoe" and prev is not None and len(prev["shoe"]) == 1 and len(hs) == 0:
                fails["G3_holders"].append((t, "shoe vanished"))
        if st.get("bag_over_water") and st["bag_bottom_y"] >= st["water_y"]:
            fails["G6_dry"].append((t, f"bag bottom {st['bag_bottom_y']} at/below water {st['water_y']}"))
        if prev is not None:
            for obj in ("bag", "shoe"):
                a = [h.split(".")[0] for h in prev[obj]]; b = [h.split(".")[0] for h in hold[obj]]
                if sorted(a) == sorted(b) and prev[obj] == hold[obj]: continue
                if not a and not b: continue
                if not a and b == ["water"]: continue                      # the shoe's first appearance (logged interruption)
                same_person = sorted(a) == sorted(b)
                kinds = ("hand_swap",) if same_person else ("handoff", "retrieve")
                cand = [e for e in ev if e.get("obj") == obj and e["event"] in kinds and abs(e["t"] - t) <= 1.0 / FPS + 1e-6]
                if not cand:
                    fails["G4_events"].append((t, f"{obj} {prev[obj]} -> {hold[obj]} with no logged event"))
                    continue
                e = cand[0]
                if e["event"] == "handoff":
                    (gw, gh), (rw, rh) = [x.split(".") for x in e["hands"]]
                    d = math.dist(P[gw]["hands"][gh], P[rw]["hands"][rh])
                elif e["event"] == "retrieve":
                    rw, rh = e["hands"][0].split(".")
                    d = math.dist(prevstate["shoe_pos"], P[rw]["hands"][rh]) if "shoe_pos" in prevstate else 999
                else:
                    d = 0.0
                if d > HAND_RADIUS:
                    fails["G4_events"].append((t, f"{obj} {e['event']} with hands {d:.1f} px apart (> {HAND_RADIUS})"))
        prev = dict(bag=hold["bag"], shoe=hold["shoe"]); prevstate = st
    ok = all(not v for v in fails.values())
    rep = dict(name=name, verdict="PASS" if ok else "FAIL", frames=len(F), rig_error_max_px=round(rig_err, 4),
               errors_by_joint_px={b: round(x, 4) for b, x in per_joint.items()},
               failures={k: dict(count=len(v), first=[f"t={a:.3f}: {b}" for a, b in v[:max_report]]) for k, v in fails.items() if v})
    return rep


def counterexamples(trL):
    out = []
    # CX1: B keeps the bag, picks up the shoe, crosses with liana + bag + shoe (three hands)
    c = copy.deepcopy(trL)
    c["events"] = [e for e in c["events"] if not (e["event"] == "handoff")]
    for st in c["frames"]:
        if st["t"] >= 18.4 - 1e-9:
            st["people"]["C"]["grips"]["R"] = "free"
            st["people"]["B"].setdefault("extra_grips", []).append("bag")
            st["bag"] = []
    out.append(("CX1 three hands: B keeps the bag, takes the shoe, crosses liana+bag+shoe", c))
    # CX2: A still on the plank (has not stepped off at F) when C steps on at 24.0
    c = copy.deepcopy(trL)
    for st in c["frames"]:
        if 24.0 <= st["t"] <= 24.6:
            st["plank_occupant"] = sorted(set(st["plank_occupant"] + ["A"]))
            st["people"]["A"]["bank"] = "P"
            st["people"]["A"]["grips"]["L"] = "liana"
    out.append(("CX2 double occupancy: C steps on at 24.0 while A is still on the plank", c))
    # CX3: the bag disappears from every hand and both grounds for 12 frames, no logged event
    c = copy.deepcopy(trL)
    for st in c["frames"]:
        if 20.0 <= st["t"] < 20.5:
            st["bag"] = []
            st["people"]["C"]["grips"]["R"] = "free"
    out.append(("CX3 disappeared possession: no bag holder 20.0-20.5 s, no event", c))
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    reports = []
    if args and args[0] == "--counterexamples":
        trL = json.load(open(HERE / "trace-L.json"))
        for name, c in counterexamples(trL):
            r = gate(c, name); r["expected"] = "FAIL"; r["as_expected"] = r["verdict"] == "FAIL"; reports.append(r)
    else:
        for a in args or [str(HERE / f"trace-{v}.json") for v in ("L", "E", "baseline")]:
            reports.append(gate(json.load(open(a)), Path(a).name))
    print(json.dumps(reports, indent=1, ensure_ascii=False))
    bad = [r for r in reports if (r["verdict"] == "FAIL") != (r.get("expected") == "FAIL")]
    sys.exit(1 if bad else 0)
