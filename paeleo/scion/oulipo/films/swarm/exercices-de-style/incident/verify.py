#!/usr/bin/env python3
"""Constraint verifier for 'exercices-de-style' (U1).

python3 verify.py            -> checks anthology.json@rev, runs the counterexample fixtures,
                                writes coverage.json (feeds the S6 matrix). Exit 0 iff the anthology
                                passes AND every fixture is rejected with its expected code.
python3 verify.py FILE.json  -> verify one anthology-shaped file (exit non-zero on failure).

Codes: LEDGER_REV, BASE_REV, COVER, NEW_ENDING, NOT_CLOSED, ANCHOR, ORDER, TIMESTAMPS, TABLEAU,
EDGE_REVERSED, EDGE_MISSING, EDGE_STYLE, GRID, FREE_SENTENCE, EMPTY_GRID, FEELING, VOICE, ACCESS,
OBJECT_NAMED, CAUSE, ONE_OP, SOUND_UNDECLARED, TIMING.
"""
import copy, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FIXDIR = os.path.join(FILMS, "sources", "exercices-de-style", "incident")
FACTS = ["E1", "E2", "E3", "E4", "E5", "E6", "F7"]
EVENTS = FACTS[:6]
COLS = [("baseline", "registre"), ("rev", "rebours"), ("sense", "sens"), ("notice", "avis"), ("key", "clé")]

FIRST = re.compile(r"(?i)(?:^|[^\w])(je\b|j['’]|me\b|m['’]|moi\b)")
KEY_3RD = re.compile(r"(?i)\b(la|une|cette|sa) clé\b")
RETURN = re.compile(r"(?i)\b(revenu|revient|revint|retour|rouvr\w*|repri[st]|chercher|rentr\w*)\b")
CAUSAL = re.compile(r"(?i)\b(parce que|car|donc|alors|à cause|puisque|ainsi|si bien que|pour cela)\b")
FEEL = re.compile(r"(?i)\b(triste|inqui\w*|heureu\w*|peur|ému\w*|angoiss\w*|content\w*|regrett\w*|hésit\w*|soulag\w*|craint\w*)")
HHMM = re.compile(r"\b(\d{2}):(\d{2})\b")
GRID_HEADER = "N° | HEURE | LIEU | OBJET | ACTION | ÉTAT"
GRID_ROW = re.compile(r"^[1-6] \| \d{2}:\d{2} \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+$")
DIM_NAMES = ["order", "sound-order", "access", "format", "voice"]


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_ledger():
    with open(os.path.join(HERE, "ledger.json"), encoding="utf-8") as f:
        L = json.load(f)
    body = {k: v for k, v in L.items() if k not in ("rev", "rev_rule", "frozen")}
    return L, hashlib.sha256(canon(body)).hexdigest()


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class Report:
    def __init__(self):
        self.fails = []
        self.passes = []

    def check(self, ok, code, where, msg):
        (self.passes if ok else self.fails).append({"code": code, "where": where, "msg": msg})
        return ok


def claim_events(c):
    return list(c.get("events", []))


def typed_len(c):
    t = c["text"]
    if c.get("stamp") and " · " in t:
        t = t.split(" · ", 1)[1]
    return len(t)


def features(v, L):
    """Measured operator signature of a variant (computed from its data, not its declarations)."""
    tl = {e["id"]: minutes(e["t"]) for e in L["events"]}
    cs = sorted(v["claims"], key=lambda c: (c["t_in"], c["id"]))
    order = []
    for c in cs:
        if c["kind"] not in ("assert", "percept"):
            continue
        for e in claim_events(c):
            if e in tl and e not in order:
                order.append(e)
                break
    snd = [s["event"] for s in sorted(v.get("sound", []), key=lambda s: s["t"])]
    access = {}
    for c in v["claims"]:
        for e in claim_events(c):
            if e in FACTS:
                access.setdefault(e, set()).add(c["kind"])
    for o in v.get("omissions", []):
        access.setdefault(o["event"], set()).add("omit")
    access = {k: sorted(s) for k, s in sorted(access.items())}
    fmt = "grid" if any(c.get("role") == "row" and GRID_ROW.match(c["text"]) for c in v["claims"]) else "prose"
    voice = "first" if any(FIRST.search(c["text"]) for c in v["claims"]) else "third"
    return {"order": order, "sound": snd, "access": access, "format": fmt, "voice": voice}


def sound_relation(base, snd):
    if not snd:
        return "none"
    pos = [base.index(e) for e in snd if e in base]
    if len(pos) != len(snd):
        return "other"
    if pos == sorted(pos):
        return "forward"
    if pos == sorted(pos, reverse=True):
        return "reverse"
    return "other"


def verify(A, L, rev_ok_hash, R=None):
    R = R or Report()
    rev = L["rev"]
    tl = {e["id"]: minutes(e["t"]) for e in L["events"]}
    anchors = L["anchors"]
    ledger_edges = {(e["from"], e["to"], e["type"]): e for e in L["edges"]}
    R.check(L["rev"] == rev_ok_hash, "LEDGER_REV", "ledger", f"stored rev {L['rev'][:12]} vs recomputed {rev_ok_hash[:12]}")
    R.check(A.get("rev") == rev, "BASE_REV", "anthology", "anthology rev equals ledger rev")
    V = A["variants"]
    base_f = features(V["baseline"], L)

    for vid, v in V.items():
        w = vid
        R.check(v.get("base_rev") == rev, "BASE_REV", w, "variant cites ledger@rev")
        cited = [e for c in v["claims"] for e in claim_events(c)]
        # --- ending
        unknown = [e for e in cited if e not in FACTS]
        R.check(not unknown, "NEW_ENDING", w, f"events outside the ledger: {unknown}" if unknown else "all cited events are in the ledger")
        late = [c["id"] for c in v["claims"] for m in HHMM.finditer(c["text"]) if int(m.group(1)) * 60 + int(m.group(2)) > minutes("18:07")]
        R.check(not late, "NEW_ENDING", w, f"timestamps after 18:07 in {late}" if late else "no time after 18:07")
        ret = [c["id"] for c in v["claims"] if RETURN.search(c["text"])]
        R.check(not ret, "NEW_ENDING", w, f"return/new-ending wording in {ret}: {[c['text'] for c in v['claims'] if c['id'] in ret]}" if ret else "no return or new-ending wording")
        evs = [e for e in cited if e in tl]
        last = max(evs, key=lambda e: tl[e]) if evs else None
        R.check(last == "E6", "NEW_ENDING", w, f"chronological last event = {last}")
        f7 = any("F7" in claim_events(c) and c["kind"] in ("assert", "percept") for c in v["claims"])
        R.check(f7, "NOT_CLOSED", w, "F7 (service door closed) affirmed" if f7 else "F7 not affirmed")
        if vid == "key":
            fk = features(v, L)
            R.check(fk["order"] and fk["order"][-1] == "E6", "NEW_ENDING", w, f"key's last told event = {fk['order'][-1] if fk['order'] else None}")
        # --- anchors: each claim speaks of the events it cites
        for c in v["claims"]:
            for e in claim_events(c):
                if e in anchors:
                    ok = any(a.lower() in c["text"].lower() for a in anchors[e])
                    R.check(ok, "ANCHOR", f"{w}/{c['id']}", f"text anchors {e}" if ok else f"text «{c['text']}» does not speak of {e}")
        # --- the uncertain cue is never asserted as a cause
        for c in v["claims"]:
            if set(claim_events(c)) & {"E2", "E3"} and CAUSAL.search(c["text"]):
                R.check(False, "CAUSE", f"{w}/{c['id']}", "causal connective on the uncertain E2→E3 cue")
        # --- coverage
        omitted = {o["event"]: o for o in v.get("omissions", [])}
        for o in v.get("omissions", []):
            R.check(bool(o.get("reason")), "COVER", w, f"omission of {o['event']} has reason '{o.get('reason')}'")
        prot = v["operator"]["protected"]
        for fct in FACTS:
            covered = any(fct in claim_events(c) and c["kind"] in ("assert", "percept") for c in v["claims"])
            ok = covered or fct in omitted
            R.check(ok, "COVER", w, f"{fct} {'covered' if covered else ('omitted: ' + omitted[fct]['reason'] if fct in omitted else 'MISSING')}")
        for p in prot:
            if p in FACTS:
                covered = any(p in claim_events(c) and c["kind"] in ("assert", "percept") for c in v["claims"])
                R.check(covered, "COVER", w, f"protected {p} is told (not merely omitted)")
        # --- timing
        w0, w1 = v["window"]
        for c in v["claims"]:
            inside = w0 - 1e-6 <= c["t_in"] <= c["t_out"] <= w1 + 1e-6
            R.check(inside, "TIMING", f"{w}/{c['id']}", f"{c['t_in']}-{c['t_out']} inside window {w0}-{w1}")
            if c.get("reveal") == "type":
                cps = c["cps"]
                R.check(12.0 <= cps <= 16.0, "TIMING", f"{w}/{c['id']}", f"typing {cps} chars/s (about 14)")
                exp = c["t_in"] + typed_len(c) / cps
                R.check(abs(exp - c["t_type_end"]) < 0.01, "TIMING", f"{w}/{c['id']}", f"type end {c['t_type_end']} = t_in + len/cps ({exp:.3f})")
                R.check(c["t_out"] - c["t_type_end"] >= 0.39, "TIMING", f"{w}/{c['id']}", f"hold after typing {c['t_out'] - c['t_type_end']:.2f} s")
        typed = sorted([c for c in v["claims"] if c.get("reveal") == "type"], key=lambda c: c["t_in"])
        for a, b in zip(typed, typed[1:]):
            R.check(a["t_type_end"] <= b["t_in"] + 1e-6, "TIMING", w, f"{a['id']} finishes typing before {b['id']} starts")

    # --- O_rev
    v = V["rev"]
    logs = sorted([c for c in v["claims"] if c.get("role") == "log"], key=lambda c: c["t_in"])
    order = [claim_events(c)[0] for c in logs]
    R.check(order == ["E6", "E5", "E4", "E3", "E2", "E1"], "ORDER", "rev", f"presentation order {order}")
    stamps = [minutes(HHMM.search(c["text"]).group(0)) for c in logs]
    R.check(all(a > b for a, b in zip(stamps, stamps[1:])), "TIMESTAMPS", "rev", f"displayed timestamps {[c['stamp'] for c in logs]} strictly decrease")
    for c in logs:
        e = claim_events(c)[0]
        R.check(HHMM.search(c["text"]).group(0) == next(x["t"] for x in L["events"] if x["id"] == e), "TIMESTAMPS", f"rev/{c['id']}", f"stamp matches ledger t of {e}")
    for t in v["timing"]:
        R.check(t["t_out"] > t["t_in"], "TABLEAU", "rev", f"tableau {t['event']} plays forward ({t['t_in']}→{t['t_out']})")
    ys = v["log_line_y"]
    drawn = {}
    for a in v["arrows"]:
        key = (a["from"], a["to"], a["type"])
        drawn[key] = a
        back = (a["to"], a["from"], a["type"])
        if key not in ledger_edges:
            R.check(False, "EDGE_REVERSED" if back in ledger_edges else "EDGE_MISSING", "rev",
                    f"arrow {a['from']}→{a['to']} ({a['type']}) is {'a reversed ledger edge' if back in ledger_edges else 'not a ledger edge'}")
            continue
        up = a["y_to"] < a["y_from"] and a["y_from"] == ys[a["from"]] and a["y_to"] == ys[a["to"]] and a.get("direction") == "up"
        R.check(up, "EDGE_REVERSED", "rev", f"arrow {a['from']}→{a['to']} drawn from cause line (y={a['y_from']}) {'UP' if up else 'NOT up'} to effect line (y={a['y_to']})")
        unc = not ledger_edges[key]["certain"]
        sty = (a["style"] == "dotted" and a.get("label") == "incertain") if unc else a["style"] == "solid"
        R.check(sty, "EDGE_STYLE", "rev", f"arrow {a['from']}→{a['to']} style {a['style']} label '{a.get('label')}'")
    for k in ledger_edges:
        R.check(k in drawn, "EDGE_MISSING", "rev", f"ledger edge {k[0]}→{k[1]} ({k[2]}) drawn")

    # --- O_sense
    v = V["sense"]
    named = [c["id"] for c in v["claims"] if re.search(r"(?i)\bclé", c["text"])]
    R.check(not named, "OBJECT_NAMED", "sense", f"object identity named in {named}" if named else "the key is never named (no access)")
    for c in v["claims"]:
        R.check(c["kind"] in ("percept", "omit"), "ACCESS", f"sense/{c['id']}", f"kind {c['kind']} (percept or omit only)")
        R.check(not CAUSAL.search(c["text"]), "CAUSE", f"sense/{c['id']}", "no cause asserted")
    np_ = [c for c in v["claims"] if c["text"].startswith("NON PERÇU")]
    R.check(len(np_) == 1 and set(np_[0]["events"]) >= {"E4", "E5"} and np_[0]["t_out"] - np_[0]["t_in"] >= 2.0,
            "COVER", "sense", "red NON PERÇU line cites E4+E5 and is held >= 2 s")
    for e in ("E4", "E5"):
        R.check(any(o["event"] == e and o["reason"] == "no access" for o in v["omissions"]), "COVER", "sense", f"{e} omission recorded, reason 'no access'")

    # --- O_notice
    v = V["notice"]
    allowed = {"heading", "grid_header", "row", "footnote", "stamp"}
    for c in v["claims"]:
        R.check(c.get("role") in allowed, "FREE_SENTENCE", f"notice/{c['id']}", f"role {c.get('role')} is part of the form")
        R.check(not FEEL.search(c["text"]), "FEELING", f"notice/{c['id']}", "no verb of feeling")
    hdr = [c for c in v["claims"] if c.get("role") == "grid_header"]
    R.check(len(hdr) == 1 and hdr[0]["text"] == GRID_HEADER, "GRID", "notice", "grid header N° | HEURE | LIEU | OBJET | ACTION | ÉTAT")
    rows = sorted([c for c in v["claims"] if c.get("role") == "row"], key=lambda c: c["t_in"])
    R.check(len(rows) == 6, "GRID", "notice", f"{len(rows)} rows")
    for c in rows:
        fields = [x.strip() for x in c["text"].split("|")]
        R.check(bool(GRID_ROW.match(c["text"])) and len(fields) == 6 and all(fields), "GRID", f"notice/{c['id']}", f"six-field row: {c['text']}")
    R.check(sum(c.get("role") == "stamp" for c in v["claims"]) == 1, "FREE_SENTENCE", "notice", "exactly one stamp")
    if hdr and rows:
        R.check(rows[0]["t_in"] - hdr[0]["t_in"] >= 1.0, "EMPTY_GRID", "notice", f"empty grid shown {rows[0]['t_in'] - hdr[0]['t_in']:.2f} s before the first field")

    # --- O_object (key)
    v = V["key"]
    blocks = {}
    for c in v["claims"]:
        sub = next(s["shot"] for s in A["schedule"] if s["t0"] - 1e-6 <= c["t_in"] < s["t1"])
        blocks.setdefault(sub, []).append(c)
    for sub, cs in blocks.items():
        R.check(any(FIRST.search(c["text"]) for c in cs), "VOICE", f"key/{sub}", f"block {sub} spoken in the first person: {[c['text'] for c in cs]}")
    for c in v["claims"]:
        R.check(not KEY_3RD.search(c["text"]), "VOICE", f"key/{c['id']}", "the key is not named in the third person")
    t_e3 = next(t["t_in"] for t in v["timing"] if t["event"] == "E3")
    for c in v["claims"]:
        if "seen" in (c.get("sense") or ""):
            R.check(c["t_in"] >= t_e3, "ACCESS", f"key/{c['id']}", "nothing seen before the envelope is torn")
        if set(claim_events(c)) & {"E1", "E2"}:
            R.check(c["kind"] == "percept" and "seen" not in (c.get("sense") or ""), "ACCESS", f"key/{c['id']}", "E1/E2 only as darkness and muffled sound")

    # --- one-operator signature (INV-ONE-OP)
    sig = {}
    for vid, v in V.items():
        f = features(v, L)
        rel = sound_relation(base_f["sound"], f["sound"])
        diff = set()
        if f["order"] != base_f["order"]:
            diff.add("order")
        if rel not in ("forward", "none"):
            diff.add("sound-order")
        if f["access"] != base_f["access"]:
            diff.add("access")
        if f["format"] != base_f["format"]:
            diff.add("format")
        if f["voice"] != base_f["voice"]:
            diff.add("voice")
        if len(f["sound"]) < len(base_f["sound"]):
            missing = [e for e in base_f["sound"] if e not in f["sound"]]
            R.check(bool(v.get("sound_absent")), "SOUND_UNDECLARED", vid, f"absent sounds {missing} {'declared' if v.get('sound_absent') else 'NOT declared'}")
        mut = set(v["operator"]["mutable"])
        ok = diff == mut and (vid == "baseline" or len(mut) >= 1)
        R.check(ok, "ONE_OP", vid, f"differs from baseline in {sorted(diff)}; declared mutable {sorted(mut)}")
        R.check(isinstance(v["operator"].get("id"), str), "ONE_OP", vid, "exactly one primary operator")
        sig[vid] = {"operator": v["operator"]["id"], "measured": {"order": f["order"], "sound": f["sound"], "sound_relation": rel,
                    "access": f["access"], "format": f["format"], "voice": f["voice"]},
                    "differs_in": sorted(diff), "mutable": sorted(mut)}
    # --- schedule
    sch = A["schedule"]
    R.check(all(abs(a["t1"] - b["t0"]) < 1e-6 for a, b in zip(sch, sch[1:])), "TIMING", "schedule", "shots are contiguous")
    R.check(60.0 <= sch[-1]["t1"] <= 75.0, "TIMING", "schedule", f"total {sch[-1]['t1']} s within 60-75")
    return R, sig


def matrix(A, L):
    V = A["variants"]
    labels = {"E1": "E1 arrive", "E2": "E2 cloche", "E3": "E3 ouvre", "E4": "E4 trouve", "E5": "E5 laisse", "E6": "E6 s'en va", "F7": "porte fermée"}
    pos = {e: i for i, e in enumerate(features(V["rev"], L)["order"])}
    rows = []
    for fct in FACTS:
        cells = {}
        for vid, col in COLS:
            v = V[vid]
            cs = [c for c in v["claims"] if fct in claim_events(c) and c["kind"] in ("assert", "percept")]
            om = [o for o in v.get("omissions", []) if o["event"] == fct]
            senses = " ".join((c.get("sense") or "") for c in cs)
            if om:
                cell = {"mark": "omis · déclaré", "circle_red": True, "reason": om[0]["reason"]}
            elif cs and all(c["kind"] == "percept" for c in cs) and "heard" in senses and not re.search(r"seen|shadow|glint|light", senses):
                cell = {"mark": "ouï, non vu", "circle_red": False}
            elif vid == "rev" and fct in pos:
                cell = {"mark": str(pos[fct] + 1), "circle_red": False, "note": "order number in the reverse log"}
            elif cs:
                cell = {"mark": "✓", "circle_red": False}
            else:
                cell = {"mark": "—", "circle_red": False}
            cell["claims"] = [c["id"] for c in cs]
            cells[col] = cell
        rows.append({"fact": fct, "label": labels[fct], "cells": cells})
    return {"columns": [c for _, c in COLS], "rows": rows}


def make_fixtures(A):
    os.makedirs(FIXDIR, exist_ok=True)
    fx = []
    # 1. NEW_ENDING, honest form: the key adds an event the ledger does not have
    a = copy.deepcopy(A)
    k = a["variants"]["key"]
    last = k["claims"][-1]
    k["claims"].append({"id": "key.9", "text": "Il est revenu me chercher.", "events": ["E7"], "kind": "assert", "sense": "seen",
                        "role": "caption", "reveal": "type", "cps": 14.0, "t_in": last["t_in"], "t_type_end": round(last["t_in"] + 26 / 14, 3),
                        "t_out": last["t_out"], "style": "counterexample"})
    fx.append(("new_ending.json", a, "NEW_ENDING", "key narrator ends « Il est revenu me chercher. » (cites E7)"))
    # 2. NEW_ENDING, disguised: the same line replaces the door line and pretends to cite E6
    a = copy.deepcopy(A)
    k = a["variants"]["key"]
    k["claims"][-1]["text"] = "Il est revenu me chercher."
    k["claims"][-1]["events"] = ["E6"]
    fx.append(("new_ending_disguised.json", a, "NEW_ENDING", "« Il est revenu me chercher. » replaces the door line and claims to be E6"))
    # 3. EDGE_REVERSED: arrows drawn in reading order, downward, effect → cause
    a = copy.deepcopy(A)
    r = a["variants"]["rev"]
    ys = r["log_line_y"]
    for ar in r["arrows"]:
        ar["from"], ar["to"] = ar["to"], ar["from"]
        ar["y_from"], ar["y_to"] = ys[ar["from"]], ys[ar["to"]]
        ar["direction"] = "down"
    fx.append(("edge_reversed.json", a, "EDGE_REVERSED", "reverse log draws its arrows downward in reading order (E6→E5 …)"))
    # 3b. EDGE_REVERSED, subtler: correct endpoints, but drawn downward on screen
    a = copy.deepcopy(A)
    r = a["variants"]["rev"]
    for ar in r["arrows"]:
        ar["y_from"], ar["y_to"] = ar["y_to"], ar["y_from"]
        ar["direction"] = "down"
    fx.append(("edge_reversed_downward.json", a, "EDGE_REVERSED", "right endpoints, arrowheads pointing down the page"))
    out = []
    for name, data, code, what in fx:
        data["fixture"] = {"expect_reject": code, "what": what}
        with open(os.path.join(FIXDIR, name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        out.append((name, code, what))
    return out


def main():
    L, h = load_ledger()
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            A = json.load(f)
        R, _ = verify(A, L, h)
        for x in R.fails:
            print("FAIL", x["code"], x["where"], x["msg"])
        print("OK" if not R.fails else f"REJECTED ({len(R.fails)} failures)")
        sys.exit(0 if not R.fails else 1)
    with open(os.path.join(HERE, "anthology.json"), encoding="utf-8") as f:
        A = json.load(f)
    R, sig = verify(A, L, h)
    fixtures = []
    for name, code, what in make_fixtures(A):
        with open(os.path.join(FIXDIR, name), encoding="utf-8") as f:
            FA = json.load(f)
        FR, _ = verify(FA, L, h)
        codes = sorted({x["code"] for x in FR.fails})
        fixtures.append({"file": os.path.relpath(os.path.join(FIXDIR, name), FILMS), "what": what, "expected": code,
                         "rejected": bool(FR.fails) and code in codes, "codes": codes,
                         "failures": [f"{x['code']} {x['where']}: {x['msg']}" for x in FR.fails]})
    fixtures_ok = all(f["rejected"] for f in fixtures)
    ok = not R.fails and fixtures_ok
    cov = {"film": "exercices-de-style", "rev": L["rev"], "ok": ok,
           "anthology_ok": not R.fails, "fixtures_ok": fixtures_ok,
           "n_checks": len(R.passes) + len(R.fails), "n_failed": len(R.fails),
           "failures": R.fails, "fixtures": fixtures, "signatures": sig, "matrix": matrix(A, L),
           "s6_note": "The S6 printed table must equal 'matrix' cell for cell (rows E1-E6 + porte fermée; columns registre/rebours/sens/avis/clé)."}
    with open(os.path.join(HERE, "coverage.json"), "w", encoding="utf-8") as f:
        json.dump(cov, f, ensure_ascii=False, indent=1)
    for x in R.fails:
        print("FAIL", x["code"], x["where"], x["msg"])
    for fxr in fixtures:
        print("fixture", fxr["file"], "expected", fxr["expected"], "->", "REJECTED" if fxr["rejected"] else "NOT REJECTED", fxr["codes"])
    print(f"anthology: {len(R.passes)} passed, {len(R.fails)} failed; fixtures {'all rejected' if fixtures_ok else 'NOT all rejected'}")
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
