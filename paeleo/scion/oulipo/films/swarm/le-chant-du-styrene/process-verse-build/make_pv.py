"""Assemble ../process_verse.json from the graph, validator run, verse table, stems report and evidence."""
import json, subprocess, sys
from pathlib import Path
SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
MED = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/process-verse-process-researcher-verse-writer-voice-sound-performer-")
G = json.loads((SW / "process_graph.json").read_text())
val = json.loads(subprocess.run([sys.executable, "-I", str(SW / "validate_tour.py"), "--json"], capture_output=True, text=True).stdout)
stems = json.loads((MED / "stems" / "stems_report.json").read_text())
cues = json.loads((MED / "stems" / "cues.json").read_text())
PULSE, GAP = 0.30, 0.45
def on(o, k): return round(o + (k - 1) * PULSE + (GAP if k > 6 else 0), 3)
V = [
 dict(id="L1", step_id="P4", onset=2.40, cue="free (no cut)",
      text="Voici les quatre anneaux | que la main a gardés.",
      syllables=["Voi", "ci", "les", "qua", "tr'an", "neaux", "que", "la", "main", "a", "gar", "dés"],
      elisions=["quatr(e) + anneaux: mute e elided before a vowel (syllable 5 'tr'an')"],
      caesura="after 'anneaux' (syllable 6, masculine); no mute e at the break",
      notes="'Voici' = 2 syllables; 'que' (syll. 7) counts before the consonant l; 'main a' is a nasal vowel before a vowel, admitted in classical prosody (not a hiatus).",
      gloss="Here are the four rings that the hand has kept."),
 dict(id="L2", step_id="P3", onset=11.00, cue="C1 ON the caesura: cut at the gap midpoint 13.025 s",
      text="Chaque anneau s'en revient | au bras qui l'a nourri.",
      syllables=["Cha", "qu'an", "neau", "s'en", "re", "vient", "au", "bras", "qui", "l'a", "nou", "rri"],
      elisions=["chaqu(e) + anneau (syllable 2 'qu'an')", "s'en, l'a: written elisions"],
      caesura="after 'revient' (syllable 6, masculine; 'vient' monosyllabic by usage); liaison t into 'au'",
      notes="CHANGED from plan draft '... au bras qui l'a coulé': the runner arm does not cast the ring, it feeds it (French 'canal d'alimentation' = runner), so 'nourri' is the process-true verb. Same count, same caesura, same cue.",
      gloss="Each ring comes back to the arm that fed it."),
 dict(id="L3", step_id="M+P2", onset=19.60, cue="C2 AGAINST the caesura: cut on the onset of syllable 5 at 20.80 s, 0.825 s before the caesura midpoint 21.625",
      text="Le rouge se retire, | et la forme est un creux.",
      syllables=["Le", "rou", "ge", "se", "re", "ti(re)", "et", "la", "for", "m'est", "un", "creux"],
      elisions=["retir(e) + et: the feminine e after syllable 6 ELIDES before the vowel of 'et' (regular caesura, not epic)", "form(e) + est (syllable 10 'm'est')"],
      caesura="after 'reti-' (syllable 6), its mute e absorbed by elision into 'et'",
      notes="'rou-ge' counts its mute e before the consonant s. CORRECTION to plan.md/test-shot labels: syllable 5 is 're' (first syllable of 'retire'), not '-ti-'; '-ti-' is syllable 6 at 21.10. The time of C2 (20.80) is unchanged: the cut lands as the word 'retire' begins.",
      gloss="The red withdraws, and the form is a hollow."),
 dict(id="L4", step_id="P1", onset=29.40, cue="free; line ends 33.45; chord at 33.60; cut to the heap at 35.00 in a line gap",
      text="L'objet était un arbre, | et l'arbre était du grain.",
      syllables=["L'ob", "jet", "é", "tait", "un", "ar(bre)", "et", "l'ar", "br'é", "tait", "du", "grain"],
      elisions=["arbr(e) + et across the caesura (regular, not epic)", "arbr(e) + était (syllable 9 'br'é')", "L'objet, l'arbre: written elisions"],
      caesura="after 'ar-' (syllable 6), mute e elided into 'et'",
      notes="Liaisons: objet_était, était_un, un_arbre. No hiatus.",
      gloss="The object was a tree, and the tree was grain."),
]
for v in V:
    assert len(v["syllables"]) == 12, v["id"]
    v["scansion"] = "-".join(v["syllables"][:6]) + " | " + "-".join(v["syllables"][6:])
    v["caesura_after"] = 6
    v["epic_caesura"] = False
    v["syllable_onsets"] = [on(v["onset"], k) for k in range(1, 13)]
    v["caesura_gap"] = [round(v["onset"] + 1.8, 3), round(v["onset"] + 2.25, 3)]
    v["caesura_mid"] = round(v["onset"] + 2.025, 3)
    v["line_end"] = round(v["onset"] + 4.05, 3)
    v["caption_hemistichs"] = [s.strip() for s in v["text"].split("|")]
    v["accents"] = [6, 12]
ev = G["evidence"]
out = dict(
 unit="U1 process-verse (process researcher + verse writer + voice/sound performer)",
 revision="r1 against plan.md r3 (round 3 build)", date="2026-11-16",
 process_graph=dict(path=str(SW / "process_graph.json"), builder=str(SW / "process-verse-build/make_graph.py"),
                    steps=list(G["nodes"]), edges=[dict(id=e["id"], inputs=e["inputs"], outputs=e["outputs"], confidence=e["confidence"], licence=e["licence"], evidence=e["evidence"]) for e in G["edges"]],
                    hypotheses_unverified=[h["id"] for h in G["hypotheses_unverified"]]),
 validator=dict(path=str(SW / "validate_tour.py"), run="python3 -I validate_tour.py [--ledger <editor ledger json>] [--json]", result=val,
                ledger_format='{"shots":[{"shot_id","step_id","playback","t_in","t_out"}, ...]} or a bare list; exit status 0 = all checks pass'),
 verse=dict(meter="classical alexandrine 6+6, pulse 0.30 s, caesura gap 0.45 s; onset(k) = on + (k-1)*0.30 + (k>6)*0.45; caesura midpoint = on + 2.025",
            lines=V,
            cue_check=dict(C1=val["verse"]["C1_t"], C1_ok=val["verse"]["C1_ok"], C1_frames="13.025 s = frame 312.6; frames 312 (13.000) and 313 (13.042) are both within +-1 frame; the cutout unit lands ring 1 home on frame 312 and cuts between 312 and 313",
                           C2=val["verse"]["C2_t"], C2_ok=val["verse"]["C2_ok"], C2_frames="20.80 s = frame 499.2 -> cut at frame 499 (20.792)", C2_lead_before_caesura_s=val["verse"]["C2_before_caesura_s"],
                           other_cuts=val["verse"]["other_cuts"], other_cuts_in_line_gaps=val["verse"]["other_cuts_in_gaps_ok"], line_spans=val["verse"]["line_spans"]),
            changes_vs_plan=["L2 'coulé' -> 'nourri' (process-true; cue contract kept)", "L3 cue syllable label corrected: syllable 5 = 're', not '-ti-' (time unchanged)"]),
 sound=dict(
   format="WAV 44.1 kHz stereo 16-bit, each 38.000 s, aligned at film t=0, one fixed scale for all stems (sum at suggested gains)",
   dir=str(MED / "stems"), builder=str(SW / "process-verse-build/stems.py"), cues=str(MED / "stems/cues.json"), overview=str(MED / "stems/stems_overview.png"),
   suggested_gains=cues["suggested_gains"],
   stems={
    "meter.wav": "HANDMADE performed meter: 48 struck-plastic pulses (12 per line) with the 0.45 s caesura gap and accents on syllables 6 and 12 (louder, longer). L1 hollow ring clicks (modal synthesis, free-ring flexural ratios 1:2.83:5.43:8.87, f0 ~1180 Hz with a rising-then-falling pitch contour); L2 lower hollow runner-arm clicks (free-free beam ratios, f0 ~640 Hz); L3 viscous low tones (~98 Hz drooping, with a wet blub; final syllable 74 Hz); L4 granular bursts of 22-40 micro-grains. Measured onset error vs cue sheet: max %.3f s over 48 pulses (< 1 frame); the gap before each 2nd hemistich is silent in this stem." % stems["meter_onset_error_s"]["max_abs"],
    "ring_events.wav": "HANDMADE: Sh1 ring set down at 0.60 with a 3-bounce rattle; Sh2 per ring a lift-off tick + 0.45 s air whoosh at launch (10.30, 11.10, 11.80, 12.50) and a snap home on the gate (13.000 = ring 1 on frame 312 just before C1; 14.000, 14.700, 15.300), rings 2-4 followed by a settle rattle derived from the cutout unit's spring-damper (3.2 Hz, zeta 0.22), all ended before 15.75; silence (room only) 15.9-17.6. Times read from geometry.json timing.",
    "drain.wav": "HANDMADE: Sh3b drain tone 21.00-26.30, falling 190->55 Hz with gurgle; four cavity-release suctions FAR TO NEAR at 21.90, 22.90, 23.90, 24.90 (1.0 s apart, nearer ones louder) - PROPOSED times for the melt unit's larger drain-order spacing; sprue glug at 26.20.",
    "rain.wav": "HANDMADE: granular pellet rain, sound-only transition 26.80-27.60 over the still empty mould (18 -> 160 grains/s), thickening through Sh4 to ~500/s at 33.60, ducked 0.12 s under each L4 pulse so the meter stays countable, thinning after the chord, then the last duller grains landing on the heap 35.0-36.5; 0.8 s ahead of the Sh4 picture.",
    "chord.wav": "HANDMADE: struck chord at 33.60 on locked rational ratios 1:3/2:2:5/2:3:4 over 110 Hz (the Whitney alignment heard) with a plastic transient; decays mostly before 35.0.",
    "room.wav": "HANDMADE room tone 0-38 s: low pink air + faint 50/100 Hz hum, fades out 36.6-37.8 to silence at 38.0.",
    "press_foraged.wav": "FORAGED: the real Engel injection moulding machine recording (source 2.0-12.8 s), band-limited 30-2500 Hz and set about 18 dB down as a faint press bed under L3: fades in 18.8-19.8, out 26.4-27.4 so the pellet rain enters over near-silence.",
    "mix_preview.wav": "sum of all stems at suggested gains (reference for the editor, not a master)",
   },
   foraged_raw=[str(MED / "gigaset_full.wav"), str(MED / "gigaset_trim_2.0-12.8s_raw.wav")],
   report=stems),
 red_amber_runner_search=dict(
   for_unit="U2 cutout", result="NOT FOUND - keep the declared thickness-to-colour gel ramp on the teal Spritzguss teile runner",
   time_spent_min=10,
   searched=["Commons file search: 'sprue red plastic', 'Gussast', 'Spritzling', 'runner injection red', 'transparent red plastic sprue', 'sprue plastic model', 'clear red plastic parts runner', 'Angießkanal', 'Spritzgussteil rot', 'translucent amber plastic molded', 'Gunpla clear parts'",
             "Commons categories: Sprue (4 files: Casting gating system.svg, Mold cavity.jpg [cream], Spritzguss teile.jpg [teal], Sprue.JPG [grey]), Injection moulding (first 60 members), Plastic pellets",
             "Library of Congress photos: 'injection molding plastic', 'polystyrene' (no relevant items; one query failed mid-transfer)",
             "Previously foraged local candidates re-viewed: gp_* Gunpla sprues (green/blue/grey, opaque), sprue_dm (grey), flash (grey), sprue_array/sprue_multi (green/blue)"],
   closest=["Mold cavity.jpg (CC BY-SA 3.0): cream, opaque, a 4-cavity shot with sprue/runner/gates labelled - good process evidence, wrong colour and not translucent"]),
 notes_for_other_units=dict(
   melt_unit="Drain order proposal matching drain.wav: far cavity empty at 21.90, then 22.90, 23.90, 24.90 (near), sprue last at 26.20. If you choose other times, edit cues.json drain.cavity_release_far_to_near and re-run stems.py (1.6 s).",
   editor="Captions: use the four lines exactly as in verse.lines[].caption_hemistichs (L2 now ends 'nourri'). Mix stems at suggested_gains; they share one scale. Run validate_tour.py --ledger on the final ledger. Credits: add the Gigaset recording (CC BY 3.0, below) - it is the film's one foraged sound."),
 evidence=ev,
 handmade=[
   dict(id="H-graph", what="process_graph.json + validate_tour.py (direct-edge reverse-tour validator with fixture and counterexamples)", where=str(SW)),
   dict(id="H-verse", what="four original French alexandrines with scansion, elisions, onset tables and glosses", where=str(SW / "process_verse.json")),
   dict(id="H-stems", what="meter, ring_events, drain, rain, chord, room stems by modal/noise synthesis in numpy (kit.Mix band filter used read-only)", where=str(MED / "stems"))],
 credits_entries=[
   dict(title="Gigaset Cordless Telephone Production II - Engel Injection Moulding Machine (2009)", author="Sound recordist Kathinka Engels; photographer and video recordist Inke Pickhardt (Work With Sounds), via Wikimedia Commons",
        license="CC BY 3.0", license_url="https://creativecommons.org/licenses/by/3.0",
        source_url="https://commons.wikimedia.org/wiki/File:Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm",
        file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/9/9f/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm.480p.vp9.webm",
        used_as="sound: the press bed under Sh3a/Sh3b (audio 2.0-12.8 s, band-limited, about -18 dB)")],
 absences=[
   "No genuine red or amber translucent runner/sprue photograph under an allowed licence (see red_amber_runner_search).",
   "No open photograph or recording of polystyrene melt itself (it is enclosed in the barrel/mould); the melt stays a declared handmade simulation.",
   "No open evidence foraged for regrind (runner scrap returned to the hopper): kept as unverified hypothesis H-regrind, not an edge.",
   "No open evidence that the 1958 reference's trees are injection-moulded polystyrene: hypothesis H-reference-construction.",
   "No openly licensed real speech usable as voice: voice stays captions + the wordless performed meter.",
   "No struck-plastic or pellet recordings found under an allowed licence in this run's budget (not searched exhaustively); those sounds are handmade.",
   "Moving Image Archive cache: query 'machine|press|factory|stamping|industr' returned general factory shots (Valley Town 1940, Master Hands 1936, etc.) and no plastics; not used, since a licensed recording of an actual injection moulding machine was found on Commons.",
   "Library of Congress: no relevant injection-moulding or polystyrene printed matter in two queries."],
 downloads_MB=round(sum(f.stat().st_size for f in (MED / "dl").iterdir()) / 1e6, 2),
)
(SW / "process_verse.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("ok", val["all_ok"], out["downloads_MB"])
