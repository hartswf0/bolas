#!/usr/bin/env python3
"""u3-gate.py: the bind gate for un-homme-qui-dort (U3, beats-r2). Pure Python, stdlib only.

Asserts plan §4 preconditions P1-P5 and §5 invariants I1, I3, I4, I6 on the clause ledger and
the two SRT takes; optionally re-runs the timing preconditions against U1's MEASURED event frames
(--picture u1-picture-ledger.json), checks D and Bl on U1's per-frame figure-alpha coverage, and
reads U2's SIL-H measurement (--sound u2-sound-ledger.json).

    python3 -I u3-gate.py                    # gate the shipped ledger + takes (exit 0 = pass)
    python3 -I u3-gate.py --selftest         # also prove the three counterexamples are rejected
    python3 -I u3-gate.py --picture P --sound S --json out.json

Exit status: 0 pass, 1 fail. A failure is a QUARANTINE of the named clause(s); the remedy is a new
beats revision, never a silent shift of a voice onset.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS = 24
OFFSET = 1.2
TOL = 0.05
EPS = 1e-6
ADDRESSEE = "you:A1"

# Personal pronouns that would make the NARRATION non-second-person. "it" is allowed as a
# non-human referent (the ring), not a narration person. "one" is a numeral here, not a pronoun.
FIRST = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
THIRD = {"he", "him", "his", "himself", "she", "her", "hers", "herself", "they", "them", "their",
         "theirs", "themselves"}
SECOND = {"you", "your", "yours", "yourself"}


# ------------------------------------------------------------------------------------ io ---
def load_json(p):
    return json.loads(Path(p).read_text())


def parse_srt(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            raise ValueError("bad SRT timing line: %r" % lines[1])
        g = [int(x) for x in m.groups()]
        on = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        off = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        out.append({"index": int(lines[0]), "on": on, "off": off, "text": " ".join(lines[2:])})
    return out


def inter(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


# ---------------------------------------------------------------------------- grammar ---
def lexical_person(text):
    toks = re.findall(r"[A-Za-z']+", text.lower())
    toks = [t.split("'")[0] for t in toks]
    has2 = any(t in SECOND for t in toks)
    has1 = sorted(set(t for t in toks if t in FIRST))
    has3 = sorted(set(t for t in toks if t in THIRD))
    subj = toks[0] if toks else ""
    return {"second": has2, "first": has1, "third": has3, "subject": subj}


# ------------------------------------------------------------------------------- gate ---
class Gate:
    def __init__(self, beats, ledger, srt_a, srt_b, picture=None, sound=None):
        self.beats, self.ledger = beats, ledger
        self.srt = {"A": srt_a, "B": srt_b}
        self.picture, self.sound = picture, sound
        self.results = []
        self.ev = {e["id"]: e for e in beats["events"]}
        self.shots = beats["shots"]
        self.sil = beats["silences"][0]
        self.guard = beats["guards"]["silence_guard_s"]
        self.vp = {v["shot_id"]: v for v in ledger.get("viewpoints", [])}

    def check(self, code, ok, subject, detail):
        self.results.append({"check": code, "subject": subject, "pass": bool(ok), "detail": detail})
        return ok

    # measured event times (U1) override planned times when present
    def event_time(self, eid):
        e = dict(self.ev[eid])
        m = (self.picture or {}).get("_events", {}).get(eid)
        if m:
            e.update({k: v for k, v in m.items() if v is not None})
            e["_measured"] = True
        return e

    def shot_at(self, t):
        for s in self.shots:
            if s["t"][0] - EPS <= t < s["t"][1] - EPS:
                return s
        return None

    def events_in_shot(self, sid):
        return [e["id"] for e in self.beats["events"] if e.get("shot") == sid]

    def clause_intervals(self, c):
        """Intervals per track: from the ledger, cross-checked against the SRTs below."""
        return {k: c["tracks"][k]["interval"] for k in ("A", "B")}

    def run(self):
        clauses = self.ledger["clauses"]
        # ---- P1 / I1: second person, declared addressee, lexical check on the text itself
        for c in clauses:
            for k in ("A", "B"):
                texts = [c["text"]] + [s["text"] for s in self.srt[k] if s["index"] == clauses.index(c) + 1]
                for txt in texts:
                    lp = lexical_person(txt)
                    ok = (c.get("grammatical_person") == 2 and c.get("addressee_id") == ADDRESSEE
                          and lp["second"] and not lp["first"] and not lp["third"] and lp["subject"] == "you")
                    self.check("P1/I1 second person, addressee you:A1", ok, f"{c['clause_id']}.{k}",
                               f"text={txt!r} declared_person={c.get('grammatical_person')} "
                               f"addressee={c.get('addressee_id')} lexical={lp}")
        # ---- P2: bind event exists; its shot is not POV and gaze does not meet the lens
        for c in clauses:
            eid = c["bind"]["event_id"]
            ok = eid in self.ev
            sid = self.ev[eid]["shot"] if ok else None
            v = self.vp.get(sid, {})
            ok = ok and v.get("is_pov") is False and v.get("gaze_meets_lens") is False
            self.check("P2 bound event exists, shot not POV", ok, c["clause_id"], f"event={eid} shot={sid}")
        # ---- P3: offsets; relation declared; overlaps computed only
        for c in clauses:
            e = self.event_time(c["bind"]["event_id"])
            iv = self.clause_intervals(c)
            for k, rel, sign in (("A", "anticipates", -1), ("B", "lags", +1)):
                tr = c["tracks"][k]
                want = e["t_on"] + sign * OFFSET
                ok = abs(iv[k][0] - want) <= TOL + EPS and tr.get("declared_relation") == rel
                self.check("P3 onset = event %s 1.2 +/- 0.05" % ("-" if sign < 0 else "+"), ok,
                           f"{c['clause_id']}.{k}",
                           f"onset={iv[k][0]:.3f} want={want:.3f} event_t_on={e['t_on']:.3f}"
                           f"{' (U1 measured)' if e.get('_measured') else ' (beats planned)'} relation={tr.get('declared_relation')}")
                ov = inter(iv[k], [e["t_on"], e["t_off"]]) > EPS
                ok2 = tr.get("declared_relation") != "overlaps" and bool(tr.get("overlaps_computed")) == ov
                self.check("P3 overlaps is computed, never declared", ok2, f"{c['clause_id']}.{k}",
                           f"computed={ov} ledger={tr.get('overlaps_computed')}")
        # ---- P4: SIL-H guard and edit crossings
        s0, s1 = self.sil["t"]
        for c in clauses:
            iv = self.clause_intervals(c)
            for k in ("A", "B"):
                a, b = iv[k]
                ok = inter([a, b], [s0 - self.guard, s1 + self.guard]) <= EPS
                self.check("P4 clear of SIL-H with 0.1 s guard", ok, f"{c['clause_id']}.{k}",
                           f"[{a:.3f},{b:.3f}] vs SIL-H [{s0},{s1}] guard {self.guard}")
                bad = []
                for s in self.shots:
                    edge = s["t"][0]
                    if a + EPS < edge < b - EPS:  # straddles the edit INTO shot s
                        evs = self.events_in_shot(s["id"])
                        if evs and c["bind"]["event_id"] not in evs:
                            bad.append(f"edit {edge} into {s['id']} holding {evs}")
                self.check("P4 no straddle into a shot holding a different event", not bad,
                           f"{c['clause_id']}.{k}", "; ".join(bad) or "ok")
        # ---- P5 / I6: identical strings, order, durations across tracks; only onsets differ
        A, B = self.srt["A"], self.srt["B"]
        ok = len(A) == len(B) == len(clauses)
        self.check("I6 same clause count A/B/ledger", ok, "takes", f"A={len(A)} B={len(B)} ledger={len(clauses)}")
        for i, c in enumerate(clauses):
            a = A[i] if i < len(A) else None
            b = B[i] if i < len(B) else None
            if a is None or b is None:
                continue
            self.check("P5 text identical in tracks A and B", a["text"] == b["text"] == c["text"], c["clause_id"],
                       f"A={a['text']!r} B={b['text']!r}")
            da, db = a["off"] - a["on"], b["off"] - b["on"]
            self.check("I6 durations identical", abs(da - db) <= 0.001 and abs(da - c["duration_s"]) <= 0.001,
                       c["clause_id"], f"A={da:.3f} B={db:.3f} ledger={c['duration_s']}")
            self.check("I6 only onsets differ, by 2.4 s", abs((b["on"] - a["on"]) - 2 * OFFSET) <= 0.001,
                       c["clause_id"], f"B.on-A.on={b['on'] - a['on']:.3f}")
            for k, s in (("A", a), ("B", b)):
                li = c["tracks"][k]["interval"]
                self.check("I6 SRT matches ledger", abs(s["on"] - li[0]) <= 0.001 and abs(s["off"] - li[1]) <= 0.001,
                           f"{c['clause_id']}.{k}", f"srt=[{s['on']:.3f},{s['off']:.3f}] ledger={li}")
        # ---- I3: SIL-H: no caption in either take; sound floor from U2
        for k in ("A", "B"):
            hits = [s["text"] for s in self.srt[k] if inter([s["on"], s["off"]], [s0, s1]) > EPS]
            self.check("I3 SIL-H has no caption", not hits, f"take{k}", f"captions in SIL-H: {hits}")
        if self.sound:
            m = self.sound.get("SIL-H", {})
            ok = (m.get("nonzero") is True and m.get("max_transient_over_floor_db_50ms", 99) <= 6.0
                  and m.get("max_transient_over_floor_db_10ms", 99) <= 6.0
                  and m.get("non_room_stems_peak_in_SILH", 1) == 0)
            self.check("I3 SIL-H room tone only (U2 measured)", ok, "SIL-H", json.dumps(m))
        # ---- I4: no POV; four distinct role fields per shot
        for s in self.shots:
            v = self.vp.get(s["id"])
            if not v:
                self.check("I4 viewpoint record present", False, s["id"], "missing")
                continue
            roles = [v.get("camera_viewpoint"), v.get("narrator"), v.get("on_screen_performer"), v.get("audience_position")]
            ok = all(roles) and len(set(roles)) == 4 and v.get("is_pov") is False and v.get("gaze_meets_lens") is False
            ok = ok and not re.search(r"\bpov\b|through his eyes|from his eyeline|(?<!not )looks? into (the )?lens", v["camera_viewpoint"], re.I)
            self.check("I4 no POV, gaze off-lens, roles distinct", ok, s["id"], f"roles={roles}")
        pg = (self.picture or {}).get("_gaze", {})
        for sid, g in pg.items():
            self.check("I4 gaze off-lens (U1 measured)", g.get("gaze_meets_lens") is False and not g.get("is_pov"),
                       sid, json.dumps(g))
        # ---- D and Bl (need U1 per-frame figure-alpha coverage)
        cov = (self.picture or {}).get("_coverage")
        c5 = next(c for c in clauses if c["clause_id"] == "c5")
        c4 = next(c for c in clauses if c["clause_id"] == "c4")
        if cov:
            on, off = self.srt["B"][4]["on"], self.srt["B"][4]["off"]
            frames = [f for f in range(int(round(on * FPS)), int(round(off * FPS)))]
            zero = [f for f in frames if f in cov and cov[f] <= 0.0]
            missing = [f for f in frames if f not in cov]
            ok = len(zero) / FPS >= 0.8 - EPS and not missing
            self.check("D c5.B on >= 0.8 s of zero figure-alpha frames", ok, "c5.B",
                       f"zero-alpha frames {len(zero)} ({len(zero) / FPS:.3f} s) of {len(frames)}; "
                       f"first zero {min(zero) if zero else None}; missing {len(missing)}")
            on, off = self.srt["B"][3]["on"], self.srt["B"][3]["off"]
            frames = list(range(int(round(on * FPS)), int(round(off * FPS))))
            nonvis = [f for f in frames if cov.get(f, 0.0) <= 0.0]
            self.check("Bl c4.B wholly inside figure-visible frames", not nonvis, "c4.B",
                       f"{len(frames)} frames, {len(nonvis)} without figure alpha: {nonvis[:10]}")
            on = self.srt["A"][3]["on"]
            self.check("A-baseline c4.A begins on an empty-stair frame", cov.get(int(round(on * FPS)), 1) <= 0.0,
                       "c4.A", f"frame {int(round(on * FPS))} coverage {cov.get(int(round(on * FPS)))}")
            on = self.srt["A"][4]["on"]
            self.check("A-baseline c5.A begins on an empty-stair frame", cov.get(int(round(on * FPS)), 1) <= 0.0,
                       "c5.A", f"frame {int(round(on * FPS))} coverage {cov.get(int(round(on * FPS)))}")
        else:
            iv = c5["tracks"]["B"]["interval"]
            ex = self.ev["E6"]["exit"]
            self.check("D (planned) c5.B after E6.exit >= 0.8 s", iv[1] - max(iv[0], ex) >= 0.8 - EPS, "c5.B",
                       f"{iv} exit {ex}; PLANNED ONLY, needs U1 coverage")
            iv = c4["tracks"]["B"]["interval"]
            e = self.ev["E4"]
            self.check("Bl (planned) c4.B inside [E4.on, E4.exit]", e["t_on"] <= iv[0] and iv[1] <= e["exit"], "c4.B",
                       f"{iv} in [{e['t_on']},{e['exit']}]; PLANNED ONLY")
        return self

    @property
    def passed(self):
        return all(r["pass"] for r in self.results)

    def failures(self):
        return [r for r in self.results if not r["pass"]]


# ------------------------------------------------------------- U1 ledger normalisation ---
def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normalise_picture(p):
    """Accepts U1's ledger and extracts {_events:{id:{t_on,t_off,exit}}, _coverage:{frame:cov}, _gaze}.

    Recognised shapes (any of): events as list or dict, with t_on/t_off/exit seconds or
    frame_on/frame_off/frame_exit (24 fps), or 'measured' sub-dicts; figure-alpha coverage as
    {"S5"/"S7": [cov per frame from shot start]} or {frame_index: cov} in pass frames, under a
    key containing 'alpha' and 'cov'.
    """
    out = {"_events": {}, "_coverage": {}, "_gaze": {}}
    ev = p.get("measured_events") or p.get("events") or {}
    items = ev.items() if isinstance(ev, dict) else [(e.get("id") or e.get("event_id"), e) for e in ev]
    for eid, e in items:
        if not eid or not isinstance(e, dict):
            continue
        e = e.get("measured", e)
        rec = {}
        for k in ("t_on", "t_off", "exit"):
            fk = {"t_on": "frame_on", "t_off": "frame_off", "exit": "frame_exit"}[k]
            if _num(e.get(fk)) is not None:
                rec[k] = _num(e[fk]) / FPS
            elif _num(e.get(k)) is not None:
                rec[k] = _num(e[k])
        if rec:
            out["_events"][eid] = rec
    cov_key = next((k for k in p if "alpha" in k.lower() and "cov" in k.lower()), None)
    cov = p.get(cov_key) if cov_key else None
    starts = {"S5": 19.0, "S7": 27.0}
    if isinstance(cov, dict):
        for k, v in cov.items():
            if isinstance(v, dict) and "per_frame" in v:
                v = v["per_frame"]
            if k in starts and isinstance(v, list):
                f0 = int(round(starts[k] * FPS))
                for i, x in enumerate(v):
                    x = x if not isinstance(x, dict) else x.get("coverage", x.get("cov"))
                    out["_coverage"].setdefault(f0 + i, float(x))
            elif re.fullmatch(r"\d+", str(k)) and _num(v) is not None:
                out["_coverage"][int(k)] = float(v)
    # S7 tail (32.5-35.0) is S5's last frame held; if not listed, it inherits S5's last value
    for sid, g in (p.get("gaze") or {}).items():
        out["_gaze"][sid] = g
    return out


# ---------------------------------------------------------------------- selftest ---
def counterexamples(ledger, srt_a, srt_b):
    """Yield (name, ledger', srtA', srtB', expected check prefix)."""
    def mut(fn_l, fn_srt):
        L, a, b = copy.deepcopy(ledger), copy.deepcopy(srt_a), copy.deepcopy(srt_b)
        fn_l(L)
        fn_srt(a, b)
        return L, a, b

    def he_l(L):
        c = L["clauses"][1]
        c["text"] = "He hears it through the wall."
        c["grammatical_person"] = 3
        c["addressee_id"] = "figure:F"

    def he_s(a, b):
        a[1]["text"] = b[1]["text"] = "He hears it through the wall."

    # forged variant: someone keeps the declared fields at 2/you:A1 but writes a 3rd-person text
    def he_forged_l(L):
        L["clauses"][1]["text"] = "He hears it through the wall."

    def c4a_l(L):
        L["clauses"][3]["tracks"]["A"]["interval"] = [18.8, 20.1]

    def c4a_s(a, b):
        a[3]["on"], a[3]["off"] = 18.8, 20.1

    def c2b_l(L):
        L["clauses"][1]["tracks"]["B"]["interval"] = [7.2, 8.7]

    def c2b_s(a, b):
        b[1]["off"] = 8.7

    yield ("X1 'He hears it through the wall.' (person 3)", *mut(he_l, he_s), "P1")
    yield ("X1' same text with forged person=2/addressee=you:A1", *mut(he_forged_l, he_s), "P1")
    yield ("X2 c4.A onset moved to 18.8", *mut(c4a_l, c4a_s), "P4 clear of SIL-H")
    yield ("X3 c2.B extended to end 8.7", *mut(c2b_l, c2b_s), "P4 no straddle")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", default=str(HERE / "beats.json"))
    ap.add_argument("--ledger", default=str(HERE / "u3-clause-ledger.json"))
    ap.add_argument("--srt-a", default=str(HERE / "takeA.srt"))
    ap.add_argument("--srt-b", default=str(HERE / "takeB.srt"))
    ap.add_argument("--picture", default=None, help="u1-picture-ledger.json (measured events, figure-alpha coverage)")
    ap.add_argument("--sound", default=None, help="u2-sound-ledger.json (SIL-H measurement)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    beats, ledger = load_json(a.beats), load_json(a.ledger)
    sa, sb = parse_srt(Path(a.srt_a).read_text()), parse_srt(Path(a.srt_b).read_text())
    pic = normalise_picture(load_json(a.picture)) if a.picture else None
    snd = load_json(a.sound) if a.sound else None

    g = Gate(beats, ledger, sa, sb, pic, snd).run()
    report = {"gate": "u3-gate.py", "beats": beats.get("revision"), "pass": g.passed,
              "n_checks": len(g.results), "failures": g.failures(), "checks": g.results,
              "picture_source": a.picture, "sound_source": a.sound,
              "measured_events_used": sorted((pic or {}).get("_events", {}).keys()),
              "coverage_frames": len((pic or {}).get("_coverage", {}))}
    print(f"[gate] {len(g.results)} checks, {len(g.failures())} failed -> {'PASS' if g.passed else 'FAIL / QUARANTINE'}")
    for f in g.failures():
        print(f"  FAIL {f['check']} [{f['subject']}] {f['detail']}")

    if a.selftest:
        report["counterexamples"] = []
        all_rejected = True
        for name, L, xa, xb, expect in counterexamples(ledger, sa, sb):
            gx = Gate(beats, L, xa, xb, pic, snd).run()
            hit = [f["check"] for f in gx.failures()]
            rejected = (not gx.passed) and any(h.startswith(expect) for h in hit)
            all_rejected &= rejected
            report["counterexamples"].append({"name": name, "rejected": rejected, "expected_failure": expect,
                                              "failed_checks": sorted(set(hit)),
                                              "quarantined": sorted(set(f["subject"] for f in gx.failures()))})
            print(f"[selftest] {name}: {'REJECTED' if rejected else 'NOT REJECTED (gate bug)'} "
                  f"by {sorted(set(hit))}")
        report["selftest_pass"] = all_rejected
        if not all_rejected:
            g.results.append({"check": "selftest", "pass": False, "subject": "gate", "detail": "a counterexample passed"})
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + "\n")
    ok = g.passed and report.get("selftest_pass", True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
