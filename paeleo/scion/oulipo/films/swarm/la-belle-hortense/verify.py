#!/usr/bin/env python3
"""verify.py: checks a La Belle Hortense structure JSON, reading only that JSON.

Usage: python3 -I verify.py structure.json [more.json ...] [--log verify.txt]
Exit status 0 if every file passes, 1 if any fails.

Checks (prompt §4, §7; plan §4-5):
  P1  module I order = start_order; sigma maps each module's order to the next;
      sigma^6 = id; fixture ABCDEF -> FAEBDC
  P2  each module has six appearances, one per motif (no motif twice), in order,
      at the slot times 3.0 + 9(i-1) + 1.5(k-1)
  P3  every function is in the allowed set and permitted for its motif
  C1  every declared support of S is before reader_stop (39.0) and at or before 21.0;
      reveal clues are not typed as supports (S2)
  C2  S is derivable from clues before reader_stop alone
  C3  the reveal (V.3/V.4) is not a necessary support of S; the reveal motif
      appeared earlier as background and was linked to the key before the reveal
  C4  computed time S becomes inferable == declared; otherwise every later
      module is FLAGGED for re-opening
  C5  each alternative explanation is refuted by clues before reader_stop
  C6  knowledge_out(i) == knowledge_in(i+1); knowledge only grows; module I starts empty;
      'S inferable' first appears in the module that contains the computed time
  C7  no caption names the background->evidence motif before its first action/evidence slot
  S1  each cloche slot has a bell cue inside the slot; no bell strike onset outside
      cloche slots except the film-level ones; a click at every slot start
"""
import json, sys, datetime
from itertools import combinations

BELL = {"bell_strike", "bell_tail"}


class Report:
    def __init__(self, name):
        self.name, self.lines, self.fails, self.flags = name, [], 0, []

    def ok(self, cid, cond, msg):
        self.lines.append(f"  [{'PASS' if cond else 'FAIL'}] {cid}: {msg}")
        if not cond:
            self.fails += 1
        return cond


def apply_sigma(sigma, order):
    return "".join(order[s - 1] for s in sigma)


def derivable(facts, rules, goal):
    facts = set(facts)
    changed = True
    while changed:
        changed = False
        for r in rules:
            if r["concludes"] not in facts and all(q in facts for q in r["requires"]):
                facts.add(r["concludes"])
                changed = True
    return goal in facts


def facts_of(clues):
    out = set()
    for c in clues:
        out.update(c["establishes"])
    return out


def kid(item):
    return item.split(":")[0].strip()


def check(path):
    d = json.load(open(path, encoding="utf-8"))
    R = Report(path)
    sig, mods, tm = d["sigma"], d["modules"], d["timing"]
    stop, deadline = tm["reader_stop"], tm["fair_play_deadline"]
    R.lines.append(f"== {path}  (rev {d.get('revision')}: {d.get('title')})")

    # ---- P1 permutation
    R.ok("P1a", sorted(sig) == list(range(1, 7)), f"sigma {sig} is a permutation of 1..6")
    R.ok("P1b", apply_sigma(sig, "ABCDEF") == "FAEBDC", "fixture ABCDEF -> FAEBDC")
    o = "ABCDEF"
    for _ in range(6):
        o = apply_sigma(sig, o)
    R.ok("P1c", o == "ABCDEF", f"sigma^6 = id (ABCDEF -> {o})")
    orders = [m["order"] for m in mods]
    R.ok("P1d", len(mods) == 6 and orders[0] == d["start_order"], f"six modules, I = {d['start_order']}")
    for i in range(len(mods) - 1):
        exp = apply_sigma(sig, orders[i])
        R.ok("P1e", orders[i + 1] == exp,
             f"sigma({mods[i]['module']} {orders[i]}) = {exp}; {mods[i+1]['module']} is {orders[i+1]}")
    R.ok("P1f", apply_sigma(sig, orders[-1]) == orders[0], f"sigma(VI {orders[-1]}) returns to {orders[0]}")

    # ---- P2 module contents and slot times
    slot = {}
    for i, m in enumerate(mods, start=1):
        apps = m["appearances"]
        motifs = [a["motif"] for a in apps]
        R.ok("P2a", len(apps) == 6 and len(set(motifs)) == 6 and set(motifs) == set("ABCDEF"),
             f"{m['module']}: six distinct motifs {''.join(motifs)} (no duplicate)")
        R.ok("P2b", "".join(motifs) == m["order"], f"{m['module']}: appearances follow the declared order {m['order']}")
        bad = [a["id"] for k, a in enumerate(apps, start=1)
               if abs(a["start"] - (3.0 + 9 * (i - 1) + 1.5 * (k - 1))) > 1e-6 or abs(a["end"] - a["start"] - 1.5) > 1e-6]
        R.ok("P2c", not bad, f"{m['module']}: slot times = 3.0+9(i-1)+1.5(k-1), 1.5 s long" + (f" (bad {bad})" if bad else ""))
        for a in apps:
            slot[a["id"]] = a

    # ---- P3 functions
    allowed = set(d["functions"])
    badf = [a["id"] for a in slot.values() if a["function"] not in allowed
            or a["function"] not in d["motifs"][a["motif"]]["permitted_functions"]]
    R.ok("P3", not badf, "every function allowed and permitted for its motif" + (f" (bad {badf})" if badf else ""))

    # ---- clue graph
    clues = d["clues"]
    for c in clues:
        a = slot.get(c["at"])
        R.ok("G0", a is not None and abs(a["start"] - c["t"]) < 1e-6,
             f"clue {c['id']} sits at {c['at']} t={c['t']}" + ("" if a else " (no such slot)"))
    rules = d["rules"]
    supports = [c for c in clues if c["claim"] == "S" and c["edge"] == "supports"]
    reveal_ids = {c["id"] for c in clues if c.get("reveal")}

    # C1
    late = [f"{c['id']}@{c['t']}" for c in supports if not c["t"] < stop]
    R.ok("C1a", supports and not late, f"every support of S before {stop} s"
         + (f" (late: {late})" if late else f" ({len(supports)} supports)"))
    R.ok("C1b", any(c["t"] <= deadline for c in supports),
         f"at least one support at or before {deadline} s: "
         + str([f"{c['id']}@{c['t']}" for c in supports if c["t"] <= deadline]))
    late21 = [f"{c['id']}@{c['t']}" for c in supports if c["t"] > deadline]
    R.ok("C1c", supports and not late21, f"every support of S at or before {deadline} s"
         + (f" (late: {late21})" if late21 else ""))
    bad_rv = [c["id"] for c in clues if c.get("reveal") and c["edge"] == "supports"]
    R.ok("C1d", not bad_rv, "reveal clues are typed as reveals, not supports" + (f" (bad {bad_rv})" if bad_rv else ""))

    # C2 derivable before the reader stop
    pre = [c for c in clues if c["t"] < stop]
    R.ok("C2", derivable(facts_of(pre), rules, "S"), f"S derivable from clues before {stop} s alone")

    # C3 reveal not a necessary support of itself. Clues are grouped: an equivalent
    # view (replay) joins the clue it replays, and all reveal clues form one group.
    at2id = {c["at"]: c["id"] for c in clues}
    def group(c):
        if c.get("reveal"):
            return "REVEAL"
        return at2id.get(c.get("equivalent_view_of"), c["id"])
    groups = sorted({group(c) for c in clues})
    all_ok = derivable(facts_of(clues), rules, "S")
    necessary = [g for g in groups if all_ok and not derivable(facts_of([c for c in clues if group(c) != g]), rules, "S")]
    R.ok("C3a", all_ok and "REVEAL" not in necessary,
         f"reveal group {sorted(reveal_ids)} not a necessary support; necessary groups = {necessary}")
    pre_g = [c for c in clues if c["t"] < stop]
    core = [g for g in groups if derivable(facts_of(pre_g), rules, "S")
            and not derivable(facts_of([c for c in pre_g if group(c) != g]), rules, "S")]
    R.lines.append(f"  [INFO] C3: fair-play core (groups necessary among clues before {stop} s) = {core}")
    no_reveal = [c for c in clues if c["id"] not in reveal_ids]
    R.ok("C3b", derivable(facts_of(no_reveal), rules, "S"), "S derivable with the reveal removed")
    bm = d["claim"].get("background_to_evidence_motif")
    rv_t = min((c["t"] for c in clues if c.get("reveal")), default=None)
    first_bg = min((a["start"] for a in slot.values() if a["motif"] == bm and a["function"] == "background"), default=None)
    later_ev = [a["id"] for a in slot.values() if a["motif"] == bm and a["function"] == "evidence"]
    lf = d["claim"].get("link_fact")
    link = [f"{c['id']}@{c['at']}" for c in clues if not c.get("reveal") and lf in c["establishes"]
            and rv_t is not None and c["t"] < rv_t]
    R.ok("C3c", first_bg is not None and rv_t is not None and first_bg < rv_t and later_ev and link,
         f"motif {bm}: first background at {first_bg} s, evidence at {later_ev}, reveal at {rv_t} s; "
         f"'{lf}' shown before the reveal by {link} (reveal must not rest on its own first appearance)")

    # C4 when S becomes inferable
    inf = None
    for c in sorted(clues, key=lambda c: c["t"]):
        if derivable(facts_of([x for x in clues if x["t"] <= c["t"]]), rules, "S"):
            inf = c["t"]
            break
    decl = d["claim"].get("inferable_at_declared")
    same = inf is not None and decl is not None and abs(inf - decl) < 1e-6
    R.ok("C4", same, f"S becomes inferable at {inf} s (declared {decl} s)")
    if not same:
        cut = min(x for x in (inf, decl) if x is not None) if (inf or decl) else 0
        flagged = [m["module"] for m in mods if m["end"] > cut]
        R.flags = flagged
        R.lines.append(f"  [FLAG] clue move changed when S is inferable ({decl} -> {inf}): re-open modules {flagged}")

    # C5 alternatives
    byid = {c["id"]: c for c in clues}
    for alt in d["alternatives"]:
        ref = [byid[r] for r in alt["refuted_by"] if r in byid]
        rule = [r for r in rules if r["concludes"] == f"not {alt['id']}"]
        okr = bool(ref) and all(c["t"] < stop for c in ref) and bool(rule) and \
            derivable(facts_of([c for c in clues if c["t"] < stop]), rule, f"not {alt['id']}")
        R.ok("C5", okr, f"{alt['id']} ('{alt['text']}') refuted before {stop} s by "
             + str([f"{c['id']}@{c['at']}" for c in ref]))

    # C6 knowledge
    R.ok("C6a", mods[0]["knowledge_in"] == [], "module I starts with empty knowledge")
    for i in range(len(mods) - 1):
        R.ok("C6b", mods[i]["knowledge_out"] == mods[i + 1]["knowledge_in"],
             f"knowledge_out({mods[i]['module']}) == knowledge_in({mods[i+1]['module']})")
    grows = all({kid(x) for x in m["knowledge_in"]} <= {kid(x) for x in m["knowledge_out"]} for m in mods)
    R.ok("C6c", grows, "knowledge only grows within each module")
    first_s = next((m for m in mods if "S inferable" in {kid(x) for x in m["knowledge_out"]}), None)
    home = next((m for m in mods if inf is not None and m["start"] <= inf < m["end"]), None)
    R.ok("C6d", first_s is not None and home is not None and first_s["module"] == home["module"],
         f"'S inferable' first enters knowledge in {first_s and first_s['module']}; computed time falls in {home and home['module']}")

    # C7 the coat is not named before it acts
    name = d["motifs"][bm]["fr"] if bm else None
    first_act = min((a["start"] for a in slot.values() if a["motif"] == bm and a["function"] in ("action", "evidence")), default=99)
    leak = [a["id"] for a in slot.values() if a["start"] < first_act and name and name in a["caption_fr"].lower()]
    R.ok("C7", not leak, f"no caption names '{name}' before {first_act} s" + (f" (leak {leak})" if leak else ""))

    # S1 sound
    for a in slot.values():
        if a["motif"] == "B":
            bells = [c for c in a["sound"] if c["kind"] in BELL and a["start"] <= c["t"] < a["end"]]
            R.ok("S1a", bool(bells), f"cloche slot {a['id']} ({a['start']}-{a['end']}) has bell cue {[(c['kind'], c['t']) for c in bells]}")
    stray = [(a["id"], c["t"]) for a in slot.values() if a["motif"] != "B"
             for c in a["sound"] if c["kind"] == "bell_strike"]
    R.ok("S1b", not stray, "no bell-strike onset outside cloche slots" + (f" (stray {stray})" if stray else ""))
    noclick = [a["id"] for a in slot.values() if not any(c["kind"] == "click" and abs(c["t"] - a["start"]) < 1e-6 for c in a["sound"])]
    R.ok("S1c", not noclick, "a click at every slot start" + (f" (missing {noclick})" if noclick else ""))

    verdict = "PASS" if R.fails == 0 else f"FAIL ({R.fails} failed checks)"
    R.lines.append(f"  => {verdict}" + (f"; flagged modules {R.flags}" if R.flags else ""))
    return R


def main(argv):
    log = None
    if "--log" in argv:
        j = argv.index("--log")
        log = argv[j + 1]
        argv = argv[:j] + argv[j + 2:]
    out = [f"# verify.py run {datetime.datetime.now().isoformat(timespec='seconds')}  args={argv}"]
    bad = 0
    for p in argv:
        r = check(p)
        out += r.lines
        bad += r.fails > 0
    text = "\n".join(out) + "\n"
    print(text, end="")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
