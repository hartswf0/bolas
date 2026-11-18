#!/usr/bin/env python3
"""U1 incident-editor (writers merged): freeze ledger.json, write anthology.json.

Run:  python3 build_incident.py      (then python3 verify.py)
Pure data; no media. Caption timing is computed here so that every typed
caption obeys the pacing rule (about 14 chars/s, with holds).
"""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "exercices-de-style"
CPS = 14.0          # typing speed for typed captions (user review note: ~14 chars/s)
FPS = 24


def r3(x):
    return round(x, 3)


def fr(x):
    """snap to a frame boundary at 24 fps"""
    return round(round(x * 24) / 24, 3)


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------- 1. ledger
ledger = {
    "incident": "La gare, 18:00-18:07",
    "slug": SLUG,
    "clock": "local station time, minutes 18:00-18:07, one evening",
    "events": [
        {"id": "E1", "t": "18:00", "actor": "visitor", "action": "arrives",
         "object": "sealed envelope (held)", "place": "empty station",
         "outcome": "visitor present; envelope sealed"},
        {"id": "E2", "t": "18:02", "actor": "bell", "action": "rings",
         "object": "station bell", "place": "station",
         "outcome": "sound (three strokes)"},
        {"id": "E3", "t": "18:04", "actor": "visitor", "action": "opens",
         "object": "envelope", "place": "by the bench",
         "outcome": "envelope torn open"},
        {"id": "E4", "t": "18:05", "actor": "visitor", "action": "finds",
         "object": "brass key (inside the envelope)", "place": "by the bench",
         "outcome": "key in hand"},
        {"id": "E5", "t": "18:06", "actor": "visitor", "action": "leaves",
         "object": "brass key", "place": "bench, platform",
         "outcome": "key on bench"},
        {"id": "E6", "t": "18:07", "actor": "visitor", "action": "walks away",
         "object": "-", "place": "station exit",
         "outcome": "visitor absent"},
    ],
    "state_facts": [
        {"id": "F7", "subject": "service door", "state": "closed",
         "interval": ["18:00", "18:07"], "statement": "The service door is closed at every t in [18:00, 18:07]; it is never opened."}
    ],
    "edges": [
        {"from": "E1", "to": "E3", "type": "enable", "certain": True, "why": "he has the envelope"},
        {"from": "E3", "to": "E4", "type": "enable", "certain": True, "why": "access to the contents"},
        {"from": "E4", "to": "E5", "type": "enable", "certain": True, "why": "he holds the key"},
        {"from": "E5", "to": "E6", "type": "precede", "certain": True, "why": "he leaves hands-free (temporal edge, declared)"},
        {"from": "E2", "to": "E3", "type": "cue", "certain": False,
         "why": "the bell may prompt the opening; declared uncertain: no telling may assert it as a cause"},
    ],
    "roles": {
        "visitor": "actor: a man in overcoat and bowler (E1, E3-E6)",
        "bell": "actor: the station bell (E2)",
        "key": "object: brass key, inside the envelope until E4, on the bench from E5",
        "envelope": "object: sealed until E3",
        "bench": "place: the platform bench (E5)",
        "service door": "witness object: carries F7; never moves",
        "clerk": "observer added by O_sense only (behind GUICHET 3); not an actor in the incident",
    },
    # lexical anchors used by verify.py to check that a claim's text speaks of the event it cites
    "anchors": {
        "E1": ["arriv", "pas sur la pierre", "ne voyais rien", "visiteur", "enveloppe cachet"],
        "E2": ["cloche", "sonn"],
        "E3": ["ouvr", "déchir", "enveloppe"],
        "E4": ["trouv", "clé", "éclat", "m'a sortie", "dans l'enveloppe"],
        "E5": ["banc", "laiss", "posée", "déposée", "métal sur bois", "tiède"],
        "E6": ["s'en va", "départ", "s'éloign", "manteau", "il n'y eut que"],
        "F7": ["porte"],
    },
}
REV = hashlib.sha256(canon(ledger)).hexdigest()
ledger_out = dict(ledger)
ledger_out["rev"] = REV
ledger_out["rev_rule"] = ("sha256 of the canonical JSON of this object without 'rev' and 'rev_rule' "
                          "(json.dumps sort_keys=True, separators=(',',':'), ensure_ascii=False, utf-8)")
ledger_out["frozen"] = "2026-11-17, U1 incident-editor; facts are never edited downstream (INV-LEDGER)"
with open(os.path.join(HERE, "ledger.json"), "w", encoding="utf-8") as f:
    json.dump(ledger_out, f, ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- timing helpers


def typed(text, t_in, hold_to=None, cps=CPS):
    te = t_in + len(text) / cps
    return {"reveal": "type", "cps": cps, "t_in": r3(t_in), "t_type_end": r3(te),
            "t_out": r3(hold_to if hold_to is not None else te)}


def setline(t_in, t_out):
    return {"reveal": "set", "cps": None, "t_in": r3(t_in), "t_type_end": r3(t_in), "t_out": r3(t_out)}


# Shot windows. S0-S4 exactly as plan.md §7. S5-S6 are lengthened (see timing_revision).
W = {
    "S0": (0.0, 3.0), "S1": (3.0, 13.0), "S2": (13.0, 24.0), "S3": (24.0, 36.0), "S4": (36.0, 46.0),
}

COMMON_PROTECTED = ["E1", "E2", "E3", "E4", "E5", "E6", "F7"]

variants = {}

# ---------------------------------------------------------------- baseline (S1)
s1_lines = [
    ("E1", "18:00 Un visiteur arrive à la gare vide, une enveloppe cachetée à la main."),
    ("E2", "18:02 La cloche de la gare sonne."),
    ("E3", "18:04 Il ouvre l'enveloppe."),
    ("E4", "18:05 Il y trouve une clé de laiton."),
    ("E5", "18:06 Le visiteur laisse la clé sur le banc."),
    ("E6", "18:07 Il s'en va."),
]
claims, timing = [], []
for i, (ev, txt) in enumerate(s1_lines):
    t0 = 3.2 + 1.6 * i
    timing.append({"event": ev, "t_in": r3(t0), "t_out": r3(t0 + 1.6), "tableau": "eye-level medium-wide puppet pose"})
    c = {"id": f"baseline.{i+1}", "text": txt, "events": [ev], "kind": "assert",
         "style": "roman, warm black #191304, top-right register; lines accumulate"}
    c.update(setline(t0, 13.0))
    claims.append(c)
# F7 closes the last register line
c = {"id": "baseline.7", "text": "La porte de service reste fermée.", "events": ["F7"], "kind": "assert",
     "style": "roman, same register line as 18:07 (continues it)"}
c.update(setline(11.2, 13.0))
claims.append(c)
variants["baseline"] = {
    "variant_id": "baseline", "shot": "S1", "window": W["S1"], "title": "Le registre", "ghost": "Gare",
    "band": {"name": "Le registre", "label": "EXERCICE 1 · SANS OPÉRATEUR", "clock": "18:00 → 18:07, steps at each beat"},
    "base_rev": REV,
    "operator": {"id": "O_none", "input_domain": f"Incident@{REV}", "protected": COMMON_PROTECTED + ["edges"],
                 "mutable": [], "accept": ["order == [E1..E6]", "every event asserted", "ends E6 + F7"]},
    "format": "prose", "voice": "third",
    "claims": claims, "omissions": [], "timing": timing,
    "sound": [{"event": "E1", "cue": "arriving steps", "t": 3.2}, {"event": "E2", "cue": "bell", "t": 4.9},
              {"event": "E3", "cue": "paper tear", "t": 6.6}, {"event": "E5", "cue": "key on wood (placed, no settle)", "t": 10.2},
              {"event": "E6", "cue": "receding steps", "t": 11.3}],
    "reveal_note": ("Register lines are SET whole (a printed register, not typing): at 1.6 s per beat a 75-char "
                    "line cannot be typed at 14 chars/s, so lines accumulate and stay until 13.0 s (line 1 is on screen 9.8 s)."),
    "beat5_pair_frame_s": 11.0,
}

# ---------------------------------------------------------------- rev (S2)
rev_lines = [("E6", "18:07", "il s'en va."), ("E5", "18:06", "laisse la clé."),
             ("E4", "18:05", "trouve une clé."), ("E3", "18:04", "ouvre l'enveloppe."),
             ("E2", "18:02", "la cloche sonne."), ("E1", "18:00", "un visiteur arrive.")]
claims, timing = [], []
c = {"id": "rev.0", "text": "porte de service : fermée, de 18:07 à 18:00", "events": ["F7"], "kind": "assert",
     "style": "rubric under the title, warm black small caps, printed (set)", "role": "rubric"}
c.update(setline(13.0, 24.0))
claims.append(c)
for i, (ev, stamp, txt) in enumerate(rev_lines):
    t0 = 13.2 + 1.4 * i
    full = f"{stamp} · {txt}"
    c = {"id": f"rev.{i+1}", "text": full, "events": [ev], "kind": "assert", "role": "log",
         "stamp": stamp, "line_index": i,
         "style": "log line: timestamp SET at t_in, text after '· ' typed; lines persist to 24.0"}
    tt = typed(txt, t0, 24.0)
    tt["note"] = "the 'HH:MM · ' stamp is printed at t_in; only the text after it is typed"
    c.update(tt)
    claims.append(c)
    timing.append({"event": ev, "t_in": r3(t0), "t_out": r3(t0 + 1.2), "tableau": "held puppet pose of this beat, plays FORWARD 1.2 s"})
# log lines top->bottom in presentation order: E6 at line 0 (top, y smallest) ... E1 at line 5 (bottom)
LINE_Y0, LINE_DY = 150, 30           # screen y of log line 0 and line spacing (px, 540-high frame)
ypos = {ev: LINE_Y0 + LINE_DY * i for i, (ev, _, _) in enumerate(rev_lines)}
arrows = []
for k, e in enumerate([("E1", "E3"), ("E3", "E4"), ("E4", "E5"), ("E5", "E6"), ("E2", "E3")]):
    edge = next(x for x in ledger["edges"] if (x["from"], x["to"]) == e)
    t0 = 21.6 + 0.13 * k              # repair 1: finished arrows held >= 1.5 s before the 24.0 wipe
    arrows.append({"from": e[0], "to": e[1], "type": edge["type"],
                   "style": "dotted" if not edge["certain"] else "solid",
                   "label": "incertain" if not edge["certain"] else "",
                   "y_from": ypos[e[0]], "y_to": ypos[e[1]], "direction": "up" if ypos[e[1]] < ypos[e[0]] else "down",
                   "t_in": r3(t0), "t_drawn": r3(t0 + 8 / FPS), "t_out": 24.0,
                   "draw": "hand-ruled red #d6280a, 8 frames, pen scratch on draw"})
variants["rev"] = {
    "variant_id": "rev", "shot": "S2", "window": W["S2"], "title": "Journal à rebours", "ghost": "Rebours",
    "band": {"name": "Journal à rebours", "label": "EXERCICE 2 · ORDRE INVERSÉ", "clock": "counts BACK 18:07 → 18:00 with the log"},
    "base_rev": REV,
    "operator": {"id": "O_rev", "input_domain": f"Incident@{REV}", "protected": COMMON_PROTECTED + ["edges"],
                 "mutable": ["order", "sound-order"],
                 "accept": ["presentation order == [E6,E5,E4,E3,E2,E1]", "displayed timestamps strictly decrease",
                            "arrows == ledger edges, each drawn from cause line UP to effect line; E2→E3 dotted 'incertain'",
                            "each tableau plays forward in time", "sound events in reverse order, each forward"]},
    "format": "prose", "voice": "third",
    "claims": claims, "omissions": [], "timing": timing, "arrows": arrows, "log_line_y": ypos,
    "sound": [{"event": "E6", "cue": "receding steps", "t": 13.2}, {"event": "E5", "cue": "key on wood", "t": 14.7},
              {"event": "E3", "cue": "paper tear", "t": 17.5}, {"event": "E2", "cue": "bell", "t": 19.0},
              {"event": "E1", "cue": "arriving steps", "t": 20.2}],
}

# ---------------------------------------------------------------- sense (S3)
sense_lines = [
    ("E1", 24.6, "pas sur la pierre · une ombre à chapeau", "percept", "heard+shadow"),
    ("E2", 26.5, "la cloche — trois coups · l'ombre lève la tête", "percept", "heard+shadow"),
    ("E3", 28.3, "papier déchiré", "percept", "heard+shadow"),
    ("E4", 29.7, "un éclat, bref", "percept", "glint"),
    ("E5", 30.9, "métal sur bois", "percept", "heard"),
    ("E6", 32.1, "les pas s'éloignent · la porte de service : aucun bruit", "percept", "heard"),
]
ev_t = {"E1": 24.2, "E2": 26.4, "E3": 28.2, "E4": 29.6, "E5": 30.8, "E6": 32.0}
claims, timing = [], []
for i, (ev, t0, txt, kind, sense) in enumerate(sense_lines):
    evs = [ev, "F7"] if ev == "E6" else [ev]
    c = {"id": f"sense.{i+1}", "text": txt, "events": evs, "kind": kind, "sense": sense, "role": "card",
         "style": "typed inventory card line, warm black mono; appears when the sense event fires; persists to 36.0"}
    c.update(setline(t0, 36.0))
    claims.append(c)
    timing.append({"event": ev, "t_in": r3(ev_t[ev]), "t_out": r3(ev_t[ev] + 1.2),
                   "tableau": "silhouette behind frosted pane; E2 head-up starts within 2 frames of bell onset" if ev == "E2" else "silhouette behind frosted pane"})
c = {"id": "sense.7", "text": "NON PERÇU : ce qu'il y avait dans l'enveloppe ; ce qu'il a laissé sur le banc.",
     "events": ["E4", "E5"], "kind": "omit", "role": "declaration",
     "style": "red #d6280a, set whole like a stamp at 33.0, held to 36.0 (>= 2 s legible)"}
c.update(setline(33.0, 36.0))
claims.append(c)
variants["sense"] = {
    "variant_id": "sense", "shot": "S3", "window": W["S3"], "title": "Inventaire des sens", "ghost": "Sens",
    "band": {"name": "Inventaire des sens", "label": "EXERCICE 3 · ACCÈS : LE GUICHET", "clock": "18:00 → 18:07"},
    "base_rev": REV, "observer": "clerk behind GUICHET 3 (added by the operator, not an actor)",
    "operator": {"id": "O_sense", "input_domain": f"Incident@{REV}",
                 "protected": ["E1", "E2", "E3", "E6", "F7"],
                 "protected_note": "E1, E2, E3, E6 and F7 as perceived; E4/E5 may be reduced to percepts",
                 "mutable": ["access"],
                 "accept": ["every event is a percept (sound, shadow, glint) or a declared omission (reason 'no access')",
                            "the object identity of E4/E5 is never named ('clé' absent); the red NON PERÇU line cites E4 and E5",
                            "no cause asserted (no causal connective)"]},
    "format": "prose", "voice": "third",
    "claims": claims,
    "omissions": [{"event": "E4", "aspect": "object identity: what was inside the envelope", "reason": "no access",
                   "detail": "frosted glass: only a brief glint is seen; the key shape is never sharp"},
                  {"event": "E5", "aspect": "object identity: what was left on the bench", "reason": "no access",
                   "detail": "only 'métal sur bois' is heard"}],
    "timing": timing,
    "sound": [{"event": "E1", "cue": "steps, through glass", "t": 24.2}, {"event": "E2", "cue": "bell, low-passed through glass", "t": 26.4},
              {"event": "E3", "cue": "paper tear, through glass", "t": 28.2}, {"event": "E5", "cue": "metal on wood, through glass", "t": 30.8},
              {"event": "E6", "cue": "receding steps", "t": 32.0}],
    "reveal_note": ("Card lines are SET whole when the sense event fires (a typewriter line in one carriage stroke): the six lines "
                    "plus NON PERÇU are 267 chars, 19 s at 14 chars/s, in a 12 s window, and each line must coincide with its event. "
                    "Lines persist to 36.0, so the shortest dwell is 3.0 s (NON PERÇU)."),
    "interpretation": ("plan.md §3.2 asks that 'clé' appear in the NON PERÇU line, but §7's exact line does not name it, and naming it "
                       "would break the clerk's access. verify.py therefore checks the stronger form: 'clé' appears nowhere in this "
                       "variant, and the NON PERÇU line is linked to E4 and E5 as an omission."),
}

# ---------------------------------------------------------------- notice (S4)
grid_header = "N° | HEURE | LIEU | OBJET | ACTION | ÉTAT"
rows = [
    ("E1", "1 | 18:00 | gare, entrée | enveloppe cachetée | arrivée | —"),
    ("E2", "2 | 18:02 | gare | cloche | non entendue | consignée"),
    ("E3", "3 | 18:04 | banc, quai | enveloppe | ouverte | déchirée"),
    ("E4", "4 | 18:05 | banc, quai | clé laiton | trouvée | en main"),
    ("E5", "5 | 18:06 | banc, quai | clé laiton | déposée | —"),
    ("E6", "6 | 18:07 | sortie | — | départ | porte de service : FERMÉE"),
]
claims, timing = [], []
c = {"id": "notice.0", "text": "AVIS — OBJET TROUVÉ", "events": [], "kind": "form", "role": "heading",
     "style": "printed notice heading"}
c.update(setline(36.2, 46.0))
claims.append(c)
c = {"id": "notice.h", "text": grid_header, "events": [], "kind": "form", "role": "grid_header",
     "style": "printed grid header; the full grid of 6 EMPTY rows is shown 36.2-37.9 before any field fills (>= 1.5 s after the 36.33 page-turn wipe ends)"}
c.update(setline(36.2, 46.0))
claims.append(c)
for i, (ev, txt) in enumerate(rows):
    t0 = 37.9 + 1.0 * i
    evs = [ev, "F7"] if ev == "E6" else [ev]
    c = {"id": f"notice.{i+1}", "text": txt, "events": evs, "kind": "assert", "role": "row",
         "style": "mono, fields fill box by box left to right, 0.15 s per field, typewriter click per field",
         "field_times": [r3(t0 + 0.15 * k) for k in range(6)]}
    c.update(setline(t0, 46.0))
    c["reveal"] = "field"
    c["t_type_end"] = r3(t0 + 0.75)
    claims.append(c)
    timing.append({"event": ev, "t_in": r3(t0), "t_out": r3(t0 + 1.0), "tableau": "row fill"})
c = {"id": "notice.n", "text": "cloche : consignée, non entendue", "events": ["E2"], "kind": "assert", "role": "footnote",
     "style": "grid footnote (inside the grid frame), mono small"}
c.update(setline(43.6, 46.0))
claims.append(c)
c = {"id": "notice.s", "text": "SUITE DONNÉE : NÉANT", "events": [], "kind": "form", "role": "stamp",
     "style": "red rubber stamp #d6280a, lands 44.0 with 2-frame squash, kit thud"}
c.update(setline(44.0, 46.0))
claims.append(c)
variants["notice"] = {
    "variant_id": "notice", "shot": "S4", "window": W["S4"], "title": "Avis", "ghost": "Avis",
    "band": {"name": "Avis", "label": "EXERCICE 4 · FORMAT FIXE", "clock": "18:00 → 18:07 row by row"},
    "base_rev": REV,
    "operator": {"id": "O_notice", "input_domain": f"Incident@{REV}", "protected": COMMON_PROTECTED,
                 "mutable": ["format"],
                 "accept": ["every row matches N° | HEURE | LIEU | OBJET | ACTION | ÉTAT (six fields)",
                            "no free sentence outside the grid except the one stamp (heading and grid footnote are part of the form)",
                            "empty grid visible >= 1 s before the first field fills", "no verbs of feeling"]},
    "format": "grid", "voice": "none",
    "claims": claims, "omissions": [], "timing": timing,
    "key_drop": {"t": 42.45, "with_row": "notice.5", "note": "foraged key cutout drops 40 px under a drawn paper clip and settles (#41)"},
    "sound": [],
    "sound_absent": {"reason": "a notice records, it does not hear: the bell is 'consignée, non entendue' (footnote). "
                               "Only non-diegetic typewriter clicks and the stamp thud are heard.",
                     "declared_by": "notice.n"},
}

# ---------------------------------------------------------------- key (S5): lengthened windows, typed at 14 chars/s


def chain(t, items):
    """items: (id, text, events, kind, sense, gap_before, style). Returns claims, end time of last typing."""
    out = []
    for cid, text, evs, kind, sense, gap, style in items:
        t += gap
        c = {"id": cid, "text": text, "events": evs, "kind": kind, "sense": sense,
             "style": style, "role": "caption"}
        c.update(typed(text, t))
        t = c["t_type_end"]
        out.append(c)
    return out, t


S5a0 = 46.0
cA, tA = chain(S5a0, [
    ("key.1", "Je ne voyais rien.", ["E1"], "percept", "dark; steps heard through paper", 0.1,
     "cream italic on envelope-interior brown"),
    ("key.2", "Une cloche, au loin.", ["E2"], "percept", "heard, muffled", 0.1,
     "cream italic"),
])
S5b0 = fr(tA + 0.4)
cB, tB = chain(S5b0, [
    ("key.3", "Déchirure, et je vois.", ["E3"], "percept", "heard + light", 0.1, "cream italic, then warm black as the light opens"),
])
# repair 2: the TEST SHOT starts at 51.5 s exactly as plan §7 / bar §10.5 (no re-anchor). S5a+S5b are compressed
# to 5.5 s (texts shortened); « Une main m'a sortie. » types over the first frames of S5c, while the hand lowers us.
S5c0 = 51.5
assert tB + 0.39 <= S5c0, (tB, S5c0)
cK, tK = chain(S5c0, [
    ("key.4", "Une main m'a sortie.", ["E4"], "assert", "felt + seen", 0.0, "warm black italic, upper right"),
])
LAND = r3(S5c0 + 30 / FPS)          # key touches the wood on frame 30 of S5c (exposure.json key_contact_frame)
assert tK <= LAND + 0.2
cC, tC = chain(LAND, [
    ("key.5", "On m'a posée sur le banc.", ["E5"], "assert", "felt + seen", 0.2, "black italic, upper right"),
    ("key.6", "Sa main était tiède,", ["E5"], "percept", "felt (new detail)", 0.2, "black italic"),
    ("key.7", "puis il n'y eut que son manteau.", ["E6"], "percept", "seen from below, receding", 0.25, "black italic"),
    ("key.8", "La porte de service n'a pas bougé.", ["F7"], "assert", "seen", 0.3, "red #d6280a italic"),
])
S5d0 = fr(tC + 0.1)
S5d1 = fr(S5d0 + 2.0)
for c in cA:
    c["t_out"] = S5b0
for c in cB:
    c["t_out"] = S5c0
cC = cK + cC
for c in cC:
    c["t_out"] = S5d1
S60, S61 = S5d1, fr(S5d1 + 6.0)
W.update({"S5a": (S5a0, S5b0), "S5b": (S5b0, S5c0), "S5c": (S5c0, S5d0), "S5d": (S5d0, S5d1), "S6": (S60, S61)})
variants["key"] = {
    "variant_id": "key", "shot": "S5a-S5d", "window": (S5a0, S5d1), "title": "Narré par la clé", "ghost": "Je",
    "band": {"name": "Narré par la clé", "label": "EXERCICE 5 · VOIX : LA CLÉ", "clock": "18:00 → 18:07"},
    "base_rev": REV,
    "operator": {"id": "O_object", "input_domain": f"Incident@{REV}", "protected": COMMON_PROTECTED,
                 "protected_note": "E3-E6 and F7 as the key perceives them; E1-E2 as darkness and muffled sound",
                 "mutable": ["voice", "access"],
                 "accept": ["spoken by the key: each sub-shot's caption block has a first-person marker (je/j'/me/m'/moi) "
                            "and no caption names the key in the third person",
                            "no claim outside the key's access: before E3 nothing is 'seen'",
                            "the last event is E6 and F7 is affirmed; no event after 18:07"]},
    "format": "prose", "voice": "first",
    "claims": cA + cB + cC, "omissions": [],
    "timing": [
        {"event": "E1", "t_in": S5a0, "t_out": r3(cA[1]["t_in"]), "tableau": "darkness inside the envelope, lamp-through-paper brown"},
        {"event": "E2", "t_in": r3(cA[1]["t_in"] - 0.1), "t_out": S5b0, "tableau": "darkness; muffled bell onset 0.1 s before key.2"},
        {"event": "E3", "t_in": S5b0, "t_out": r3(S5c0 - 0.4), "tableau": "straight-ahead tear, edge re-cut every 2 frames"},
        {"event": "E4", "t_in": r3(S5c0 - 0.4), "t_out": LAND, "tableau": "the Rol hand slides the key out and lowers it"},
        {"event": "E5", "t_in": LAND, "t_out": r3(cC[3]["t_in"]),
         "tableau": f"key lands at {LAND} s (frame 30 of S5c), 6°→0° over 10 frames, one 3 px bounce, clink on the landing frame; still before 54.0 s"},
        {"event": "E6", "t_in": r3(cC[2]["t_in"]), "t_out": S5d0,
         "tableau": "visitor walks away to frame left, >= 2 full steps on twos, scale -3 %/step, 6 px bob; EXITS frame before key.8 finishes"},
    ],
    "sound": [{"event": "E1", "cue": "steps, muffled through paper", "t": S5a0 + 0.2},
              {"event": "E2", "cue": "bell, heavily low-passed", "t": r3(cA[1]["t_in"] - 0.1)},
              {"event": "E3", "cue": "paper tear (unmuffles)", "t": S5b0},
              {"event": "E5", "cue": "clink on the landing frame", "t": LAND},
              {"event": "E6", "cue": "receding steps on foot contacts, gain and low-pass falling", "t": r3(cC[1]["t_in"])}],
    "test_shot": {"window": [S5c0, S5d0], "landing_s": LAND, "beat5_pair_frame_s": 54.0,
                  "settle_done_by_s": 54.0,
                  "bar_note": "repair 2: the bar's numbers are kept as written (S5c starts 51.5 s, key still before 54.0 s, pair 11.0 vs 54.0 s); "
                              "the earlier re-anchor to 58.667 s is withdrawn. S5c ends later than 58.0 s (the visitor's exit and key.7-key.8 typing)."},
    "interpretation": ("§3.2 asks 'every caption in the key's first person'. Lines key.6-key.8 are the key speaking but carry no "
                       "grammatical first person (« Sa main était tiède, » …). verify.py checks first person per utterance block "
                       "(S5a, S5b, S5c each contain je/me/m') plus: no third-person naming of the key, no access outside the key's."),
}

for v in variants.values():
    v["window"] = [r3(v["window"][0]), r3(v["window"][1])]

# ---------------------------------------------------------------- page texts (S0, S6) and schedule
page_text = {
    "S0": {"ghost": "Gare", "title": {"text": "Une gare, six faits", "reveal": "letter by letter", "cps": CPS,
                                       "t_in": 0.3, "t_type_end": r3(0.3 + len("Une gare, six faits") / CPS), "t_out": 3.0,
                                       "colour_by_word": ["#d6280a", "#191304", "#d6280a", "#191304"]},
           "band": "d'après Raymond Queneau · cinq manières", "strip": "six empty cells"},
    "S6": {"ghost": "Matrice", "title": "Matrice", "band": "même incident · cinq règles",
           "matrix_source": "incident/coverage.json (matrix)", "ticks": "type in cell by cell from S6+0.4 s, 0.08 s per cell",
           "bell_stroke_t": S60, "declared_silence_from": r3(S60 + 3.0)},
}

ORIG = {"S0": [0, 3], "S1": [3, 13], "S2": [13, 24], "S3": [24, 36], "S4": [36, 46],
        "S5a": [46, 49], "S5b": [49, 51.5], "S5c": [51.5, 58], "S5d": [58, 60], "S6": [60, 66]}
schedule = [{"shot": k, "t0": r3(W[k][0]), "t1": r3(W[k][1]), "plan_window": ORIG[k],
             "changed": [r3(W[k][0]), r3(W[k][1])] != [float(x) for x in ORIG[k]]} for k in ORIG]

handmade = [
    {"id": "H-ledger", "what": "the incident itself: six events, one state fact, five typed edges, roles", "where": "incident/ledger.json"},
    {"id": "H-texts", "what": "all French caption, log, card, notice and matrix texts (writers merged, U1)", "where": "incident/anthology.json"},
    {"id": "H-verify", "what": "the constraint verifier and its counterexample fixtures",
     "where": "incident/verify.py; films/sources/exercices-de-style/incident/*.json"},
]

anthology = {
    "film": SLUG, "unit": "U1 incident-editor + constraint verifier (writers merged)",
    "ledger": "incident/ledger.json", "rev": REV,
    "merge_note": ("The incident editor, the constraint verifier and the four writers (rev, sense, notice, key) are merged under one "
                   "owner (U1), as plan.md §9 records: the captions are short and coupled to the timing. Operator independence is "
                   "checked instead by verify.py's one-operator signature: each variant differs from the baseline only in its "
                   "declared mutable dimensions."),
    "timing_policy": {
        "typed_cps": CPS, "fps": FPS,
        "rule": ("Typed captions (S0 title, S2 log text, S5 key) type at 14 chars/s and are held after typing. Register lines (S1), "
                 "card lines (S3) and notice fields (S4) are set whole on their event and persist to the end of their shot, so "
                 "every line is readable; the reason is recorded per variant (reveal_note)."),
    },
    "timing_revision": {
        "what": (f"S0-S5c start keep plan §7 exactly (S5a 46.0-{S5b0}, S5b {S5b0}-{S5c0}, S5c from {S5c0}); S5c is lengthened at its END "
                 f"to {S5d0}, S5d {S5d0}-{S5d1}, S6 {S60}-{S61}. Film total {S61} s (plan 66.0; limit 75)."),
        "why": ("Repair 2: the bar's S5 numbers stand as written (key still before 54.0 s, pair 11.0 vs 54.0 s). S5a-S5b texts were "
                "shortened to fit 5.5 s at 14 chars/s with holds; « Une main m'a sortie. » types over the first second of S5c. "
                "S5c runs past 58.0 s only so the visitor actually exits and key.6-key.8 type at 14 chars/s with holds."),
        "consequences": ["beat-5 pair still: S1 at 11.0 s vs S5c at 54.0 s (as in the bar)",
                         f"key lands {LAND} s, still from {r3(S5c0 + 40 / FPS)} s, before 54.0 s",
                         f"S6 bell stroke at {S60}, declared silence from {r3(S60 + 3.0)}"],
    },
    "schedule": schedule,
    "page_text": page_text,
    "variants": variants,
    "evidence": [],
    "handmade": handmade,
    "absences": [{"searched": "none: U1 is a text/data unit and foraged nothing",
                  "note": "no media prepared under sources/exercices-de-style/incident-editor/ (none needed); "
                          "sources/exercices-de-style/incident/ holds only the counterexample fixtures"}],
}
with open(os.path.join(HERE, "anthology.json"), "w", encoding="utf-8") as f:
    json.dump(anthology, f, ensure_ascii=False, indent=1)
print("rev", REV)
print("S5a", W["S5a"], "S5b", W["S5b"], "S5c", W["S5c"], "S5d", W["S5d"], "S6", W["S6"], "land", LAND)
