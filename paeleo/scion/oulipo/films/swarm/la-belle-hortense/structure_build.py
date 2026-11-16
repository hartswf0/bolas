#!/usr/bin/env python3
"""Builds the canonical structure (structure.json) and the comparison baseline
(baseline.json) for La Belle Hortense, plus two mutants used to show that
verify.py catches a sequence violation and a clue move.

structure.json is the editable canonical structure: edit it directly afterwards
if you prefer; this script only records how revision S1 was generated.
Run: python3 -I structure_build.py
"""
import json, copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = "S2"  # S2 (editor repair 1): K6, K10 retagged corroborates; R1, R2 typed reveal (non-support)
SIGMA = [6, 1, 5, 2, 4, 3]
MOTIFS = {
    "A": {"fr": "manteau", "en": "coat",
          "signature": "Coat panel GrabCut-cut from LoC 2017844115 (Delano, FSA/OWI, PD), folds kept, stencil-dyed red #e2011b (multiply, tone shows through). Same cut contour and dye in every appearance.",
          "permitted_functions": ["background", "action", "absence", "evidence"]},
    "B": {"fr": "cloche", "en": "bell",
          "signature": "Station bell cutout on a pinned yoke, clapper as child pendulum; sound = the foraged Fridingen station-bell strike (CC BY-SA 4.0). Bell strikes sound only in cloche slots (plus title 0.4 s and end card 57.2 s).",
          "permitted_functions": ["action", "evidence", "false-lead", "closure"]},
    "C": {"fr": "clé", "en": "key",
          "signature": "Skeletonkey.png (Commons, CC0), left key, dyed brass ~#c9a23a.",
          "permitted_functions": ["action", "absence", "false-lead", "evidence", "closure"]},
    "D": {"fr": "banc", "en": "bench",
          "signature": "Park-bench cutout (Highsmith, LoC, PD) on the bench plane (parallax 0.8).",
          "permitted_functions": ["action", "absence", "evidence", "background", "closure"]},
    "E": {"fr": "reçu", "en": "receipt",
          "signature": "HANDMADE typeset ticket 'REÇU N° 6 · une clé · porte de service · remise au banc', red number stamp; states: plain, struck-through, underlined, RENDU.",
          "permitted_functions": ["action", "evidence", "closure"]},
    "F": {"fr": "porte", "en": "door",
          "signature": "Shut goods-shed door of Bourré plate 50866795131 (Daniel Jolivet, CC BY 2.0), brick quoins dyed red/white; HANDMADE enamel '6' plate from IV.1 on.",
          "permitted_functions": ["background", "action", "evidence", "closure"]},
}
FUNCTIONS = ["background", "action", "absence", "false-lead", "evidence", "closure"]


def sigma(order):
    return [order[s - 1] for s in SIGMA]


def orders():
    o = list("ABCDEF")
    out = []
    for _ in range(6):
        out.append(o)
        o = sigma(o)
    return out


def slot_start(i, k):
    return round(3.0 + 9 * (i - 1) + 1.5 * (k - 1), 3)


ROMAN = ["I", "II", "III", "IV", "V", "VI"]
CLICK = {"kind": "click", "src": "kit.click (synthesised)", "gain": 0.5}

# ---- the 36 appearances, keyed by module numeral and motif ----------------
# (function, on_screen, fr, en, extra sound cues as list of (dt, kind, desc))
A = {}
A["I"] = {
    "A": ("background", "Wide, still camera, no streak: station house plate; bench downstage right with a dark red coat folded on it (3 hinged pieces of the same coat panel). Nobody looks at it; uncaptioned as an object.",
          "Une gare vide.", "An empty station.", [(0.0, "ambience", "kit.wind, low")]),
    "B": ("action", "Bell on its wall bracket swings (FK pendulum). The visitor enters left walking (articulated cutout), sealed envelope in hand.",
          "Une cloche sonne.", "A bell rings.", [(0.1, "bell_strike", "Fridingen strike at 4.6 s"), (0.3, "steps", "gravel steps (foraged)")]),
    "C": ("action", "Medium close on her hands: the envelope flap hinges open and the brass key slides out, frame by frame.",
          "Dans l'enveloppe, une clé de laiton.", "In the envelope, a brass key.", [(0.2, "paper", "paper tear")]),
    "D": ("action", "Wide again. She lays the key on the bench, ON THE RED COAT; contact shadow; she straightens. (Clue K1; frame 8.25 s is the critic's pointing frame.)",
          "Elle la laisse sur le banc.", "She leaves it on the bench.", [(0.75, "tap", "soft key-on-cloth tap")]),
    "E": ("action", "A small ticket slips from the envelope and flutters to the gravel (drift + rotation).",
          "Un reçu tombe.", "A receipt falls.", [(0.2, "paper", "paper flutter")]),
    "F": ("background", "She walks off right. Slow push on the goods-shed door: shut.",
          "La porte de service reste fermée.", "The service door stays shut.", [(0.0, "steps", "receding steps, then wind")]),
}
A["II"] = {
    "F": ("action", "Tight on the door: the conductor's cut hand tries the handle. Locked. Small pan begins (streak 0.15).",
          "Fermée.", "Locked.", [(0.2, "rattle", "door handle rattle (foraged)")]),
    "A": ("action", "At the bench the red coat is lifted out of frame; for 6 frames a brass glint shows in its fold. Holdout cut behind the bench plane to the conductor already wearing it. (Clue K2.)",
          "Il reprend son manteau.", "He takes back his coat.", [(0.2, "cloth", "cloth rustle (filtered noise)")]),
    "E": ("evidence", "He picks up the ticket. Insert: the line 'remise au banc' is legible.",
          "« remise au banc »", "'left at the bench'", [(0.2, "paper", "paper handling")]),
    "B": ("action", "The bell swings: a train is due. He hurries off left; the camera pans; first streaks (0.4).",
          "Le train est annoncé.", "The train is called.", [(0.1, "bell_strike", "Fridingen strike at 16.6 s"), (0.3, "steps", "hurried steps")]),
    "D": ("absence", "The empty bench, held. No coat, no key.",
          "Le banc est vide.", "The bench is empty.", [(0.0, "ambience", "wind only")]),
    "C": ("absence", "The key is absent: on the receipt, 'une clé' is struck through in red, typed over.",
          "Où est la clé ?", "Where is the key?", [(0.2, "typewriter", "strike-through clicks")]),
}
A["III"] = {
    "C": ("false-lead", "The visitor's cut hand, closed and turning. (Raises ALT-1.)",
          "Elle l'a reprise ?", "Did she take it back?", []),
    "F": ("evidence", "The door: still locked; a rattle. Nobody has used a key on it.",
          "Toujours fermée.", "Still locked.", [(0.2, "rattle", "door handle rattle")]),
    "D": ("evidence", "Low under the bench: gravel and nothing (gravel plane slides under the bench plane). It did not fall.",
          "Rien sous le banc.", "Nothing under the bench.", [(0.0, "ambience", "wind")]),
    "A": ("background", "Wide, far plane: a small red figure crosses the far end of the meadow (conductor in the coat, 1/5 scale). Same cut, same dye. Caption does not name the coat.",
          "Au loin, quelqu'un traverse.", "Far off, someone crosses.", [(0.0, "steps", "faint steps")]),
    "B": ("evidence", "The bell swings with no one near it: there is no bell-ringer.",
          "La cloche sonne seule.", "The bell rings by itself.", [(0.1, "bell_strike", "Fridingen strike at 27.1 s")]),
    "E": ("evidence", "The receipt again: 'remise au banc' underlined in red. She left it; she did not take it back.",
          "« remise au banc » : elle l'a laissée.", "'left at the bench': she left it.", [(0.2, "typewriter", "underline strike")]),
}
A["IV"] = {
    "E": ("evidence", "The ticket's 'N° 6' matches the handmade enamel '6' on the shed door.",
          "Reçu n° 6, porte n° 6.", "Receipt no. 6, door no. 6.", []),
    "C": ("false-lead", "Typed frame 'I·4' replays the exact pixels of I.4: the key on the red coat (equivalent view). Caption raises ALT-2.",
          "Un voleur ?", "A thief?", [(0.3, "bell_reversed", "short reversed bell swell from the same recording (no strike onset)")]),
    "B": ("false-lead", "The bell's rope; the bell swings. Caption raises ALT-3.",
          "Ou la cloche ?", "Or the bell?", [(0.1, "bell_strike", "Fridingen strike at 33.1 s")]),
    "F": ("evidence", "Close on the keyhole: dark, locked. No thief has opened it.",
          "Aucun voleur n'a ouvert.", "No thief has opened it.", [(0.2, "rattle", "door handle rattle")]),
    "A": ("action", "A red blur sweeps across the near plane (coat sleeve, streak 0.6), coming back toward us.",
          "Quelque chose revient.", "Something is coming back.", [(0.2, "whoosh", "pan whoosh (filtered noise)")]),
    "D": ("absence", "The empty bench. Caption holds. FRESH READER STOPS AT 39.0 s.",
          "Qui a la clé ?", "Who has the key?", [(0.3, "silence", "declared silence 37.8-39.0 after the click")]),
}
A["V"] = {
    "D": ("action", "The bench; the camera starts a fast pan right; streaks build to full strength.",
          "Quelqu'un court vers le banc.", "Someone is running to the bench.", [(0.0, "steps", "running steps begin far off")]),
    "E": ("action", "The ticket lifts off the gravel in the runner's wind and flutters through the streak.",
          "Le reçu s'envole.", "The receipt blows away.", [(0.2, "paper", "paper flutter")]),
    "A": ("evidence", "TEST SHOT. The conductor runs back in the red coat, cropped tight (coat >= 55% of frame height, head at/above top edge): jointed legs with knees and a real stride, forward lean, arms swinging; ground and shed smeared by sub-frame pan integration. At ~43.2 s the key slips from the coat's fold and falls, turning. Type: 'V.' black / 'le manteau revient' red / slot line with MANTEAU red. (Reveal R1.)",
          "le manteau revient", "the coat comes back", [(0.0, "steps", "steps at stride rate (Concrete Steps 2 grains)"), (0.0, "whoosh", "pan whoosh")]),
    "C": ("evidence", "The key lands brass-on-green, bounces once, lies still; his hand takes it. (Reveal R2.)",
          "La clé était dans le pli.", "The key was in the fold.", [(0.1, "tink", "key tink (foraged)")]),
    "F": ("action", "Key in the lock: the door leaf swings open on its hinge (horizontal foreshortening), dark inside.",
          "La porte s'ouvre.", "The door opens.", [(0.1, "latch", "latch (lock-3-open, CC0)"), (0.6, "hinge", "squeaky hinge (PD)")]),
    "B": ("action", "The bell rings as the door opens: a full strike.",
          "La cloche sonne : c'est ouvert.", "The bell rings: it is open.", [(0.1, "bell_strike", "Fridingen strike at 46.6 s")]),
}
A["VI"] = {
    "B": ("closure", "The bell settles: damped pendulum to rest. Streak decays to 0.",
          "La cloche se tait.", "The bell falls silent.", [(0.0, "bell_tail", "ring-out tail of the 46.6 s strike continues through the slot (no new onset)")]),
    "D": ("evidence", "Typed frame 'I·4' replays the key laid on the red coat (equivalent view of I.4).",
          "Elle l'avait posée sur le manteau.", "She had laid it on the coat.", []),
    "F": ("closure", "The door stands open.",
          "La porte reste ouverte.", "The door stays open.", [(0.0, "ambience", "room tone")]),
    "E": ("closure", "A red stamp 'RENDU' thumps onto the ticket.",
          "RENDU.", "Returned.", [(0.15, "thud", "stamp thud (kit.thud)")]),
    "C": ("closure", "The key hangs on its hook (slight pendulum).",
          "La clé à son crochet.", "The key on its hook.", [(0.2, "tink", "soft tink")]),
    "A": ("background", "The coat lies folded on the bench again: background, as in I.1.",
          "Le manteau, sur le banc.", "The coat, on the bench.", [(0.0, "ambience", "wind")]),
}

STREAK = {"I": 0.0, "II": 0.25, "III": 0.3, "IV": 0.4, "V": 1.0, "VI": 0.2}

KNOWLEDGE = [
    [],
    ["K-seed: a visitor left a brass key for 'porte de service' at the bench",
     "K-coat: a red coat lay on the bench and the key was laid on it (shown, not said)",
     "K-door: the service door is shut"],
    ["K-seed", "K-coat", "K-door",
     "K-took: the conductor took the coat from the bench and put it on (glint in the fold)",
     "K-missing: the bench is empty and the key is missing",
     "S inferable: K-coat + K-took"],
    ["K-seed", "K-coat", "K-door", "K-took", "K-missing", "S inferable",
     "ALT-1 refuted: raised at III.1, the receipt says she left it at the bench",
     "K-not-fallen: nothing under the bench",
     "K-no-ringer: the bell rings by itself",
     "K-far: a red figure crossed the far meadow"],
    ["K-seed", "K-coat", "K-door", "K-took", "K-missing", "S inferable",
     "ALT-1 refuted", "K-not-fallen", "K-no-ringer", "K-far",
     "K-door6: the key belongs to door no. 6",
     "K-replay: I.4 re-seen: the key lay on the coat",
     "ALT-2 refuted: raised at IV.2, door no. 6 is still locked",
     "ALT-3 refuted: raised at IV.3, nothing under the bench, no ringer",
     "READER STOP 39.0: leading explanation expected = S"],
    ["K-seed", "K-coat", "K-door", "K-took", "K-missing", "S inferable",
     "ALT-1 refuted", "K-not-fallen", "K-no-ringer", "K-far", "K-door6", "K-replay",
     "ALT-2 refuted", "ALT-3 refuted", "READER STOP 39.0",
     "S confirmed: the key falls from the coat's fold (reveal)",
     "K-open: door no. 6 opened with the key"],
    ["K-seed", "K-coat", "K-door", "K-took", "K-missing", "S inferable",
     "ALT-1 refuted", "K-not-fallen", "K-no-ringer", "K-far", "K-door6", "K-replay",
     "ALT-2 refuted", "ALT-3 refuted", "READER STOP 39.0", "S confirmed", "K-open",
     "K-closed: key returned, receipt stamped RENDU, coat back on the bench"],
]

TECH = {
    "I": "multiplane stage, still camera; Reiniger rigs (visitor walk, bell pendulum, envelope flap); stencil dye",
    "II": "multiplane, slow pan with sub-frame integration; coat swap as holdout behind bench plane",
    "III": "multiplane depth (far-plane red figure at 1/5 scale); gravel plane under bench",
    "IV": "replay of I.4 pixels in a typed frame; near-plane blur from real sub-frame integration",
    "V": "full pan exposure (sub-frame integration, 36-72 sub-frames); Reiniger run cycle with knees; parabolic key fall",
    "VI": "streak decays to 0; damped bell; replay of I.4; still camera",
}


def module_block(o, i, appearances):
    num = ROMAN[i - 1]
    apps = []
    for k, m in enumerate(o, start=1):
        fn, scr, fr, en, extra = appearances[num][m]
        t0 = slot_start(i, k)
        cues = [dict(CLICK, t=t0)]
        for dt, kind, desc in extra:
            cues.append({"t": round(t0 + dt, 3), "kind": kind, "desc": desc})
        apps.append({
            "id": f"{num}.{k}", "slot": k, "motif": m, "motif_fr": MOTIFS[m]["fr"],
            "start": t0, "end": round(t0 + 1.5, 3), "function": fn,
            "on_screen": scr, "caption_fr": fr, "caption_en": en,
            "slot_line": " · ".join((MOTIFS[x]["fr"].upper() if x == m else MOTIFS[x]["fr"]) for x in o),
            "sound": cues,
        })
    return apps


def build_structure():
    os_ = orders()
    modules = []
    for i, o in enumerate(os_, start=1):
        num = ROMAN[i - 1]
        modules.append({
            "module": num, "index": i, "order": "".join(o),
            "start": slot_start(i, 1), "end": round(slot_start(i, 1) + 9.0, 3),
            "streak": STREAK[num], "technique": TECH[num],
            "knowledge_in": KNOWLEDGE[i - 1], "knowledge_out": KNOWLEDGE[i],
            "appearances": module_block(o, i, A),
        })
    clues = [
        {"id": "K0", "at": "I.1", "t": 3.0, "establishes": ["coat_on_bench"], "edge": "supports", "claim": "S",
         "note": "the coat is present on the bench as background, uncaptioned"},
        {"id": "K1", "at": "I.4", "t": 7.5, "establishes": ["key_on_coat"], "edge": "supports", "claim": "S",
         "note": "the visitor lays the key on the red coat"},
        {"id": "K2", "at": "II.2", "t": 13.5, "establishes": ["coat_taken_by_conductor", "glint_in_fold"], "edge": "supports", "claim": "S",
         "note": "the coat is lifted with a brass glint in its fold; the conductor wears it"},
        {"id": "K3", "at": "II.5", "t": 18.0, "establishes": ["bench_empty"], "edge": "supports", "claim": "S",
         "note": "the bench is empty right after the coat left"},
        {"id": "K4", "at": "II.3", "t": 15.0, "establishes": ["visitor_left_key"], "edge": "refutes", "claim": "ALT-1"},
        {"id": "K5", "at": "III.3", "t": 24.0, "establishes": ["not_fallen"], "edge": "refutes", "claim": "ALT-3"},
        {"id": "K6", "at": "III.4", "t": 25.5, "establishes": ["conductor_in_coat_far"], "edge": "corroborates", "claim": "S",
         "note": "quiet colour-only clue: the red coat is moving with someone"},
        {"id": "K7", "at": "III.5", "t": 27.0, "establishes": ["no_ringer"], "edge": "refutes", "claim": "ALT-3"},
        {"id": "K8", "at": "III.6", "t": 28.5, "establishes": ["visitor_left_key"], "edge": "refutes", "claim": "ALT-1"},
        {"id": "K9", "at": "III.2", "t": 22.5, "establishes": ["door_still_locked"], "edge": "refutes", "claim": "ALT-2"},
        {"id": "K10", "at": "IV.2", "t": 31.5, "establishes": ["key_on_coat"], "edge": "corroborates", "claim": "S",
         "equivalent_view_of": "I.4", "note": "replay of the I.4 pixels"},
        {"id": "K11", "at": "IV.4", "t": 34.5, "establishes": ["door_still_locked"], "edge": "refutes", "claim": "ALT-2"},
        {"id": "R1", "at": "V.3", "t": 42.0, "establishes": ["key_falls_from_coat"], "edge": "reveal", "claim": "S", "reveal": True},
        {"id": "R2", "at": "V.4", "t": 43.5, "establishes": ["key_falls_from_coat"], "edge": "reveal", "claim": "S", "reveal": True},
    ]
    return {
        "title": "La belle Hortense: canonical structure",
        "revision": REV, "base": "plan.md P1", "owner": "U1 structure (combinatorial editor + mystery designer + verifier)",
        "sigma": SIGMA, "start_order": "ABCDEF",
        "timing": {"title": [0.0, 3.0], "module_len": 9.0, "slot_len": 1.5,
                   "slot_start_formula": "3.0 + 9(i-1) + 1.5(k-1)", "end_card": [57.0, 66.0], "duration": 66.0,
                   "reader_stop": 39.0, "fair_play_deadline": 21.0, "reveal_time": 43.2},
        "motifs": MOTIFS, "functions": FUNCTIONS,
        "film_level_sound": [
            {"t": 0.4, "kind": "bell_strike", "desc": "title: one distant strike"},
            {"t": 57.2, "kind": "bell_strike", "desc": "end card: final strike"},
            {"t": 63.0, "kind": "silence", "desc": "declared silence 63-66"}],
        "modules": modules,
        "claim": {"id": "S", "text": "The conductor carried the key away in the fold of his coat.",
                  "inferable_at_declared": 13.5,
                  "background_to_evidence_motif": "A",
                  "link_fact": "key_on_coat"},
        "rules": [
            {"id": "R-fair", "concludes": "S", "requires": ["key_on_coat", "coat_taken_by_conductor"],
             "gloss": "the key lay on the coat; the conductor took the coat; so the key went with him"},
            {"id": "R-reveal", "concludes": "S", "requires": ["key_falls_from_coat"],
             "gloss": "seeing the key fall from the worn coat"},
            {"id": "R-alt1-out", "concludes": "not ALT-1", "requires": ["visitor_left_key"]},
            {"id": "R-alt2-out", "concludes": "not ALT-2", "requires": ["door_still_locked", "coat_taken_by_conductor"]},
            {"id": "R-alt3-out", "concludes": "not ALT-3", "requires": ["not_fallen", "no_ringer"]},
        ],
        "clues": clues,
        "alternatives": [
            {"id": "ALT-1", "text": "The visitor took the key back.", "raised_at": "III.1", "raised_t": 21.0,
             "refuted_by": ["K4", "K8"], "why": "the receipt reads 'remise au banc' (left at the bench): II.3 shows it, III.6 underlines it"},
            {"id": "ALT-2", "text": "A thief took the key.", "raised_at": "IV.2", "raised_t": 31.5,
             "refuted_by": ["K9", "K11", "K2"], "why": "a thief takes a key to open a door, and door no. 6 is still locked (III.2, IV.4); the key had already left with the coat (II.2)"},
            {"id": "ALT-3", "text": "The bell: its ringing shook the key off the bench, or a bell-ringer took it.", "raised_at": "IV.3", "raised_t": 33.0,
             "refuted_by": ["K5", "K7"], "why": "nothing lies under the bench (III.3) and the bell rings with nobody near it (III.5)"},
        ],
        "pointing_frames": {"coat_on_bench": 3.75, "key_on_coat": 8.25, "reveal": 43.3},
        "slot_sample_times": "t = 3.75 + 9(i-1) + 1.5(k-1): the red-caps word in the slot line must equal order_i[k]",
        "type_conventions": {
            "face": "Courier 10 Pitch Bold (/usr/share/fonts/X11/Type1/c0583bt_.pfb)",
            "numeral": "module numeral, black #010201, 44 px, lower left",
            "caption_fr": "red slab #a50917 / #e2011b, 30 px",
            "caption_en": "English gloss at 60% size; per test-shot review it must be legible: set it in cream #e1e5b2 on a black #010201 band (or black on a cream band), never black directly on dark streak",
            "slot_line": "18 px black; active motif in CAPS and red; the exact string is in each appearance's slot_line"},
        "notes_for_units": [
            "Coat identity (signature A): if U3 replaces the walking conductor with another PD figure for a real run (test-shot review), the bench coat in I.1, II.2, VI.6 and the far/near coat in III.4, IV.5 must be cut from the SAME coat panel with the same dye, or the C3 identity of background and evidence breaks. Record the new source id in rig.json and update motifs.A.signature here.",
            "Coat folds must survive the dye (multiply over the monochrome print) so the I.1 folded coat and the V.3 worn coat read as the same cloth.",
            "VI.1 bell cue is the ring-out tail of the 46.6 s strike (no new onset), consistent with acceptance bar 7 (onsets only at 0.4, 4.6, 16.6, 27.1, 33.1, 46.6, 57.2). If U4 prefers a fresh strike at 48.1, add it to acceptance 7 too.",
            "IV.2 uses a reversed bell swell from the same recording: it must have no strike onset (verify S1b only checks declared cue kinds; U4 should confirm by onset detection).",
            "Captions are now set for all 36 slots; plan §6 left some blank. The editor may drop a caption (set caption_fr to an empty string) but must not add the word 'manteau' before 13.5 s (verify C7).",
            "Any edit that moves a clue (clues[].at / t) or changes a caption that carries a clue: re-run verify.py; a C4 FLAG lists every module to re-open."],
        "evidence": {
            "foraged": [],
            "foraged_note": "This unit downloaded nothing. Motif signatures name items foraged and licence-checked by U2 (LoC 2017844115 PD; Bourré 50866795131/50866798791/50866891867 CC BY 2.0 Daniel Jolivet; Skeletonkey.png CC0; Fridingen bell CC BY-SA 4.0; Highsmith bench PD); their records live in ledger.json / test-shot-ledger.json.",
            "absences": [],
            "handmade": [
                {"id": "STRUCT", "what": "canonical structure: six orders, 36 appearances, captions, cues, clue graph, alternatives", "where": "films/swarm/la-belle-hortense/structure.json (generated by structure_build.py)"},
                {"id": "VERIFY", "what": "verifier reading only the JSON", "where": "films/swarm/la-belle-hortense/verify.py, log verify.txt"},
                {"id": "BASELINE", "what": "story-order counter-cut, rejected by verify.py", "where": "films/swarm/la-belle-hortense/baseline.json"},
                {"id": "MUTANTS", "what": "M1 module V order swap; M2 clue move (I.4 key-on-coat removed)", "where": "films/swarm/la-belle-hortense/mutants/"},
                {"id": "BOARD", "what": "motif x module matrix with braid strands and clue timeline, Courier 10 Pitch, for the editor and end card reference", "where": "films/sources/la-belle-hortense/structure-combinatorial-editor-mystery-designer-verifier-/structure-board.png"},
                {"id": "SAMPLES", "what": "36-row slot table (id, start, end, sample t, motif, slot line, captions, function)", "where": "films/sources/la-belle-hortense/structure-combinatorial-editor-mystery-designer-verifier-/slots.csv"}]},
    }


def build_baseline(s):
    """Story-order counter-cut: no permutation, coat absent from I.1, key laid on the
    bare bench, coat taken from a hook in II with no glint, key simply found at the end."""
    b = copy.deepcopy(s)
    b["title"] = "La belle Hortense: BASELINE story-order counter-cut (expected to FAIL)"
    b["revision"] = "B1"
    story = ["BCDEFA", "FAEDCB", "CFDEBA", "ECBFDA", "DEACFB", "BDFECA"]
    newA = copy.deepcopy(A)
    newA["I"]["A"] = ("absence", "An empty coat hook by the station door. No coat on the bench.",
                      "Une gare vide.", "An empty station.", [])
    newA["I"]["D"] = ("action", "She lays the key on the bare bench.", "Elle la laisse sur le banc.", "She leaves it on the bench.", [])
    newA["II"]["A"] = ("action", "The conductor takes his coat from the hook inside (no glint).",
                       "Il prend son manteau.", "He takes his coat.", [])
    newA["IV"]["C"] = ("false-lead", "A hand in shadow (no replay of I.4).", "Un voleur ?", "A thief?", [])
    newA["VI"]["D"] = ("closure", "The empty bench.", "Le banc.", "The bench.", [])
    mods = []
    for i, o in enumerate(story, start=1):
        m = copy.deepcopy(s["modules"][i - 1])
        m["order"] = o
        m["appearances"] = module_block(list(o), i, newA)
        mods.append(m)
    for m in mods:  # in the cut, S is only inferable at the reveal (module V)
        for f in ("knowledge_in", "knowledge_out"):
            m[f] = [x for x in m[f] if not x.startswith(("S inferable", "K-coat", "K-replay"))]
            if (f == "knowledge_out" and m["index"] >= 5) or (f == "knowledge_in" and m["index"] == 6):
                m[f] = m[f] + ["S inferable: only from the reveal"]
    b["modules"] = mods
    b["claim"]["inferable_at_declared"] = 42.0
    b["clues"] = [
        {"id": "K1b", "at": "I.3", "t": 6.0, "establishes": ["key_on_bench"], "edge": "context", "claim": "S"},
        {"id": "K2b", "at": "II.2", "t": 13.5, "establishes": ["coat_taken_by_conductor"], "edge": "context", "claim": "S"},
        {"id": "R1", "at": "V.3", "t": 42.0, "establishes": ["key_falls_from_coat"], "edge": "supports", "claim": "S", "reveal": True},
        {"id": "R2", "at": "V.4", "t": 43.5, "establishes": ["key_falls_from_coat"], "edge": "supports", "claim": "S", "reveal": True},
        {"id": "K9", "at": "III.2", "t": 22.5, "establishes": ["door_still_locked"], "edge": "refutes", "claim": "ALT-2"},
        {"id": "K8", "at": "III.6", "t": 28.5, "establishes": ["visitor_left_key"], "edge": "refutes", "claim": "ALT-1"},
        {"id": "K5", "at": "III.3", "t": 24.0, "establishes": ["not_fallen"], "edge": "refutes", "claim": "ALT-3"},
        {"id": "K7", "at": "III.5", "t": 27.0, "establishes": ["no_ringer"], "edge": "refutes", "claim": "ALT-3"},
    ]
    b["alternatives"][0]["refuted_by"] = ["K8"]
    b["alternatives"][1]["refuted_by"] = ["K9"]
    return b


def mutants(s):
    out = {}
    # M1: sequence violation - module V swapped to DEACBF (coat still in slot 3)
    m1 = copy.deepcopy(s)
    m1["title"] = "MUTANT M1: module V order DEACBF (sequence violation)"
    mv = m1["modules"][4]
    mv["order"] = "DEACBF"
    a5, a6 = mv["appearances"][4], mv["appearances"][5]
    a5["motif"], a6["motif"] = a6["motif"], a5["motif"]
    out["mutant-M1-order.json"] = m1
    # M2: clue move - the coat is no longer on the bench in I.1/I.4 (key laid on bare bench);
    # the key-on-coat fact is first available from the IV.2 replay -> S inferable moves 13.5 -> 31.5
    m2 = copy.deepcopy(s)
    m2["title"] = "MUTANT M2: clue K1 moved out of I.4 (key-on-coat first seen at IV.2)"
    m2["clues"] = [c for c in m2["clues"] if c["id"] not in ("K1",)]
    out["mutant-M2-cluemove.json"] = m2
    return out


if __name__ == "__main__":
    s = build_structure()
    (HERE / "structure.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))
    (HERE / "baseline.json").write_text(json.dumps(build_baseline(s), ensure_ascii=False, indent=1))
    md = HERE / "mutants"
    md.mkdir(exist_ok=True)
    for name, d in mutants(s).items():
        (md / name).write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print("orders:", [m["order"] for m in s["modules"]])
