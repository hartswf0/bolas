#!/usr/bin/env python3
"""Validate a reverse tour against a process graph (direct-edge rule), and the verse cue sheet.

Usage:
  python3 -I validate_tour.py                    # fixtures + shot_ledger.json (default; --planned for plan.md shots) + verse cues
  python3 -I validate_tour.py --ledger L.json    # also validate an editor ledger: {"shots":[{shot_id, step_id, playback, t_in, t_out}, ...]}
  python3 -I validate_tour.py --json             # machine-readable result

Rule (direct edge, reversed): consecutive distinct steps (a, b) of a tour are valid iff some VERIFIED edge e
with acceptable evidence has  mat(a) <= outputs(e)  and  b <= inputs(e)  (tool members of a, e.g. the mould M,
are persistent and need not be produced by e; every member of b must be an input of e).
A step id may be compound ("M+P2"). Repeated consecutive step ids (several shots of one step) collapse.
Unverified hypotheses (regrind) are never edges. Playback (forward/backward) must be a separate field and
does not change the rule.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALLOWED = ("PD", "Public domain", "CC0", "CC BY", "CC BY-SA")
FPS = 24


def lic_ok(lic):
    lic = lic.strip()
    if any(bad in lic for bad in ("NC", "ND", "fair use")):
        return False
    return any(lic.startswith(a) for a in ALLOWED)


class Graph:
    def __init__(self, nodes, edges, evidence=None):
        self.kind = {k: v.get("kind", "material") for k, v in nodes.items()}
        ev = {e["id"]: e for e in (evidence or [])}
        self.edges = []
        for e in edges:
            if e.get("status", "verified") != "verified":
                continue
            if evidence is not None:
                items = [ev[i] for i in e.get("evidence", []) if i in ev]
                if not items or not any(lic_ok(x["license"]) for x in items):
                    continue
            self.edges.append((set(e["inputs"]), set(e["outputs"]), e["id"]))

    @classmethod
    def load(cls, path):
        g = json.loads(Path(path).read_text())
        return cls(g["nodes"], g["edges"], g.get("evidence"))

    def members(self, step):
        return set(step.split("+"))

    def back_edge(self, a, b):
        A, B = self.members(a), self.members(b)
        matA = {x for x in A if self.kind.get(x, "material") != "tool"}
        for ins, outs, eid in self.edges:
            if matA and matA <= outs and B <= ins:
                return eid
        return None

    def check(self, tour):
        seq = [s for i, s in enumerate(tour) if i == 0 or s != tour[i - 1]]
        for s in seq:
            if not self.members(s) <= set(self.kind):
                return False, f"unknown step {s}", []
        used = []
        for a, b in zip(seq, seq[1:]):
            eid = self.back_edge(a, b)
            if eid is None:
                return False, f"no direct verified edge {b} -> {a}", used
            used.append(f"{a} <-{eid}- {b}")
        return True, "ok", used


def fixture():
    nodes = {k: {"kind": "material"} for k in ("raw_stock", "casting", "finish")}
    edges = [dict(id="cast", inputs=["raw_stock"], outputs=["casting"]),
             dict(id="finish", inputs=["casting"], outputs=["finish"])]
    return Graph(nodes, edges)


# ------------------------------------------------------------------ verse ---
PULSE, GAP = 0.30, 0.45
LINES = {"L1": 2.40, "L2": 11.00, "L3": 19.60, "L4": 29.40}


def onset(line, k):
    return LINES[line] + (k - 1) * PULSE + (GAP if k > 6 else 0.0)


def caesura_mid(line):
    return LINES[line] + 6 * PULSE + GAP / 2  # end of syllable 6 + half the gap


def line_span(line):
    return LINES[line], onset(line, 12) + PULSE


def verse_checks(cuts_other):
    res = {}
    c1 = caesura_mid("L2")
    c2 = onset("L3", 5)
    res["C1_t"] = round(c1, 4)
    res["C1_ok"] = abs(c1 - 13.025) < 1e-9
    res["C1_frame_window"] = [int(c1 * FPS) - 1 + 1, int(c1 * FPS) + 1]  # frames 312..313 lie within +-1 frame
    res["C2_t"] = round(c2, 4)
    res["C2_ok"] = abs(c2 - 20.80) < 1e-9
    res["C2_before_caesura_s"] = round(caesura_mid("L3") - c2, 4)
    res["C2_lead_ok"] = caesura_mid("L3") - c2 >= 0.6
    spans = {l: tuple(round(x, 3) for x in line_span(l)) for l in LINES}
    res["line_spans"] = spans
    bad = [t for t in cuts_other if any(a < t < b for a, b in spans.values())]
    res["other_cuts"] = cuts_other
    res["other_cuts_in_gaps_ok"] = not bad
    res["ok"] = all(res[k] for k in ("C1_ok", "C2_ok", "C2_lead_ok", "other_cuts_in_gaps_ok"))
    return res


PLANNED_SHOTS = [
    dict(shot_id="Sh1", step_id="P4", playback="static", t_in=0.00, t_out=8.60),
    dict(shot_id="Sh2a", step_id="P3", playback="backward", t_in=8.60, t_out=13.02),
    dict(shot_id="Sh2b", step_id="P3", playback="backward", t_in=13.02, t_out=17.60),
    dict(shot_id="Sh3a", step_id="M+P2", playback="static", t_in=17.60, t_out=20.80),
    dict(shot_id="Sh3b", step_id="M+P2", playback="backward", t_in=20.80, t_out=27.60),
    dict(shot_id="Sh4", step_id="P1", playback="backward", t_in=27.60, t_out=35.00),
    dict(shot_id="Sh5", step_id="P1", playback="static", t_in=35.00, t_out=38.00),
]


def ledger_checks(G, shots):
    out = {}
    out["playback_field_on_every_shot"] = all("playback" in s and s["playback"] in ("forward", "backward", "static") for s in shots)
    path = [s["step_id"] for s in shots]
    ok, why, used = G.check(path)
    collapsed = [s for i, s in enumerate(path) if i == 0 or s != path[i - 1]]
    out.update(path=collapsed, ok=ok and out["playback_field_on_every_shot"] and collapsed == ["P4", "P3", "M+P2", "P1"],
               reason=why, edges_used=used)
    dur = max(s["t_out"] for s in shots) - min(s["t_in"] for s in shots)
    out["duration_s"] = round(dur, 3)
    out["duration_ok"] = 25 <= dur <= 40
    return out


def main(argv):
    as_json = "--json" in argv
    R = {}
    F = fixture()
    p = F.check(["finish", "casting", "raw_stock"])
    f = F.check(["finish", "raw_stock", "casting"])
    R["fixture_pass"] = dict(tour=["finish", "casting", "raw_stock"], ok=p[0], reason=p[1], edges=p[2])
    R["fixture_fail"] = dict(tour=["finish", "raw_stock", "casting"], ok=f[0], reason=f[1])
    G = Graph.load(HERE / "process_graph.json")
    R["film_tour"] = dict(zip(("ok", "reason", "edges"), G.check(["P4", "P3", "M+P2", "P1"])))
    # counterexamples from plan section 4
    R["counter_rings_to_pellets"] = dict(zip(("ok", "reason", "edges"), G.check(["P4", "P1", "M+P2"])))
    R["counter_skip_shot"] = dict(zip(("ok", "reason", "edges"), G.check(["P4", "M+P2", "P1"])))
    R["counter_forward_order"] = dict(zip(("ok", "reason", "edges"), G.check(["P1", "M+P2", "P3", "P4"])))
    shots = PLANNED_SHOTS
    if "--ledger" in argv:
        L = json.loads(Path(argv[argv.index("--ledger") + 1]).read_text())
        shots = L["shots"] if isinstance(L, dict) else L
        R["ledger_source"] = argv[argv.index("--ledger") + 1]
    elif "--planned" not in argv and (HERE / "shot_ledger.json").exists():
        # default (critic round 2): the editor's shot_ledger.json beside this script; --planned uses plan.md's shots
        L = json.loads((HERE / "shot_ledger.json").read_text())
        shots = L["shots"] if isinstance(L, dict) else L
        R["ledger_source"] = "shot_ledger.json (default)"
    else:
        R["ledger_source"] = "PLANNED_SHOTS (plan.md section 7)"
    R["ledger"] = ledger_checks(G, shots)
    cuts = sorted({round(s["t_in"], 3) for s in shots} - {0.0, 13.02, 20.8})
    R["verse"] = verse_checks(cuts)
    R["all_ok"] = (R["fixture_pass"]["ok"] and not R["fixture_fail"]["ok"] and R["film_tour"]["ok"]
                   and not R["counter_rings_to_pellets"]["ok"] and not R["counter_skip_shot"]["ok"]
                   and not R["counter_forward_order"]["ok"] and R["ledger"]["ok"] and R["ledger"]["duration_ok"]
                   and R["verse"]["ok"])
    if as_json:
        print(json.dumps(R, indent=1))
    else:
        for k, v in R.items():
            print(f"{k}: {v}")
    return 0 if R["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
