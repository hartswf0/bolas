# SCION swarm plan: un-homme-qui-dort ("Second-person voice")

Revision base: plan r0 (2026-11-15). Prompt: prompts/un-homme-qui-dort.md. Earlier script/notes/credits exist (films/un-homme-qui-dort.py etc.); the plan is rebuilt from scratch. Nine Library of Congress FSA/OWI stills already in films/sources/un-homme-qui-dort/ (Bubley boardinghouse series, Mydans rooming-house stairway) may be reused after re-checking each LoC item page for "No known restrictions".

Reference looked at: assets/references/sommeil.webp (QAGOMA/Dovidis still: the young man's face against a wall, beside a doubled, back-turned reflection). What it teaches: one anonymous body seen from outside, doubled. We plan real material for that, not its look. No frame of the 1974 film is used.

## 1. Creative thesis

A voice says "you" to a man we only ever watch from across a room or down a stairwell. The 35 s picture is shown twice with word-identical narration: in pass A each clause comes 1.2 s before the action it names, in pass B 1.2 s after. Because the second staircase is the same frames as the first, the only thing that changes is when "you" arrives. At one point the voice keeps talking to "you" after the body has left the frame, and "you" then has nobody on screen to land on except the viewer.

## 2. Defining beat and comparison baseline

- **Defining beat (D):** pass B, flight 2. The clause c5 "You take the same stairs again, one step after another." starts 1.2 s after the figure enters the identical stair clip and is still being shown after the figure has left the frame (planned: it ends at least 0.8 s after the measured exit). The viewer can point to frames with an empty stairwell carrying a second-person clause.
- **Baseline (Bl):** pass B, flight 1, same frames, same lag, clause c4 "You take the stairs." It starts and ends while the figure is visibly on the stairs. Here "you" lands on the character. A second baseline is pass A flight 2: the same words as D start over the empty stair before the body enters, so they read as an instruction that the figure then obeys.
- **Success means** a viewer marking the moment the voice felt addressed to them places a mark inside D (pass B, after the exit frame) and not inside Bl.

## 3. Lineage Genome (compact)

| field | value |
|---|---|
| source | *Un homme qui dort*, Perec and Queysanne, 1974 (feature film, adapted from Perec's 1967 novel). Its narration is in "tu" and is spoken by a woman's voice (Ludmila Mikaël) over a lone, mostly silent young man (Jacques Spiesser) in Paris. The female narrator is from general film knowledge (uncertain, check against QAGOMA). Waschneck, *Screening OULIPO*, p. 9, identifies the second-person narration. |
| target | a 35 s screen study, shown twice (two voice timings). About 72 s with two pass cards. |
| preserved relation | the address ("you") and the observation (a third party's camera) are two separate channels kept apart. |
| optics change | 35 mm location cinematography becomes foraged public-domain US archive footage and FSA/OWI stills. The anonymous figure is several archive strangers, held together only by the address (a constraint we accept, and a deviation: the source has one actor). |
| formalism change | the source's long variable narration becomes a ledger of 5 clauses bound to 5 event IDs with declared relations. The repeated staircase is literal frame identity. |
| concept change | the source leaves you to infer whose "tu" it is. Here, two timings of the same words test where "you" lands. |
| sound change | a spoken voice becomes captions, since no TTS exists and no openly licensed recording of the source voice exists. Foraged room tone, a telephone bell heard through a wall, and footsteps carry the body. |

Formation epochs (weights 0–100):
- Nouveau roman / second-person fiction (Butor, *La Modification*, 1957): **70**. It supplies the grammatical device directly. That Perec drew on Butor is a common critical claim, recorded here as uncertain.
- Oulipo constraint practice (1960–): **55**. Gives fixed rules, frame identity and a word-identical retake. Perec joined the Oulipo in 1967. The film is not formally an Oulipian constraint work.
- Post-1968 Parisian essay and observational cinema: **45**. Gives the long held voice-free shots and the camera outside the subject.
- Sound-to-action timecoded score (SCION s47): **60**. The voice track becomes a performance score with onsets.
- Mid-century US documentary, industrial and FSA film/photo (the material we forage): **40**. This is a change of optics, not lineage, and is declared as such.

## 4. Olog (types, bind, central operation)

Types
- **AddressClause** {clause_id, text, addressee_id = "you:A1" (the declared addressee), grammatical_person = 2, predicate, track ∈ {A_ahead, B_behind}, spoken_interval [on, off] (caption visible)}.
- **ObservedAction** {event_id, subject_id = "figure:F", observation_interval [on, off], shot_id}.
- **Viewpoint** fields, kept distinct for every shot: camera_viewpoint (e.g. "across room, standing height", "stairwell, from above"), narrator = "N (off-screen, captions)", on_screen_performer = "figure:F (archive stranger, id per shot)", audience_position = "spectator in front of screen". Invariant: camera_viewpoint ≠ figure's eye line (no POV shot).
- **DiegeticSpeech** track: declared empty (no quoted speech in this proof).
- **Silence** {silence_id, interval, allowed_sound = "room tone only"}.

Central operation: **bind(c: AddressClause, e: ObservedAction, relation)** with relation ∈ {anticipates, overlaps, lags, leaves_silence}.
- Typed preconditions:
  1. c.grammatical_person = 2, and c.addressee_id equals the current declared addressee (no marked shift exists in this proof).
  2. e.event_id exists in the beat ledger at the current revision, and e.shot_id is a non-POV shot.
  3. If anticipates: c.on = e.on − 1.2 s ± 0.05. If lags: c.on = e.on + 1.2 s ± 0.05. Overlap is computed, not declared: overlap(c,e) = |c ∩ e| > 0.
  4. c.spoken_interval does not intersect any Silence interval (guard 0.3 s). c.on does not lie before the start of the shot that holds e when that would put voice across an edit into a different event's shot (an address boundary).
- Observable consequences:
  - anticipates: the caption is on screen before the matching action is visible (measurable by frame).
  - lags: the action is visible before the caption appears. For c5 in track B, the caption is visible on frames where the figure is absent (D).
  - leaves_silence: in the held shot H no caption is present for 7.5 s and the soundtrack contains only room tone (RMS above a floor; no ring, step or voice onset).
- Counterexample (must fail the gate): c' = "He takes the stairs." bound to E4. grammatical_person = 3, so precondition 1 fails and c' is quarantined. A second counterexample, failing precondition 4: moving c4 in track A to 18.6 s (onset 1.9 s ahead) puts voice inside H. That invalidates the sound editor's silence review and is rejected.
- Replay / alternate views. Equivalent: picture frames of passes A and B are byte-identical per shot (same source in/out points). Flights F1 and F2 are the same frames. Clause text is identical across tracks. Divergent: spoken intervals, and therefore the overlap set. Track A overlaps the body in c1–c3. Track B overlaps the body in c4 but outlasts it in c5. The same words therefore yield an anticipatory timeline (A) and a retrospective timeline (B), and both are valid (fixture section 7).
- Interactivity: none (a linear screen study). The two passes are the "alternate view".

## 5. Invariants (checked by asserts in the film script and by the referent checker)

1. Every narrative clause is 2nd person, and the addressee is "you:A1" throughout. No he/she/I narration, and no marked shift in this proof.
2. Diegetic speech track is separate and empty. Any audible archive speech is muted or excluded (source sound is used only if it is wordless).
3. Held shot H: ≥ 7.0 s (planned 7.5 s) with no caption and no voice. The only sound is room tone. Identical in both passes.
4. No shot is from the figure's viewpoint. The camera is always outside the figure (across the room, through a doorway, above the stairwell).
5. F1 and F2 are the same source clip with the same in/out points and identical frames (hash check), and appear in both passes.
6. Track A and track B carry the same clause strings in the same order (string equality). Only the onsets differ: A = event − 1.2 s, B = event + 1.2 s.
7. No clause crosses into H or straddles an edit into another event's shot.
8. Every foraged item has a credit entry with a licence acceptable under BRIEF-2, or "via movingimagearchive.com" with a best-supported PD status.

## 6. Timed sequence (Hard proof, one pass = 35.0 s)

Film layout: [card A 1.0 s] [pass A 35.0 s] [card B 1.0 s] [pass B 35.0 s] = 72.0 s at 640×480 or the kit default, ≤ 6 MB. Cards are HANDMADE, typeset with kit.font: "1 · the voice ahead" and "2 · the voice behind". Pass picture and sound are identical in both passes. Only the caption track differs. No on-screen diagnostic strip in the viewing cut. The editor may render a separate diagnostic version with a beat strip.

Pass-relative times (s):

| shot | time | on screen | heard (both passes) | element |
|---|---|---|---|---|
| S1 WAKE | 0.0–6.0 | A man in bed seen from the side or foot of the bed, stirring, then opening his eyes or sitting up. Event E1 (wake) at ≈1.8 (measured). | room tone; bedclothes rustle if the source has it | FORAGED. Moving Image Archive first: queries "bed|asleep|wak|lying awake|bedroom" (candidate db4a7675 *Alcohol and the Human Body* 1949: man lying in bed; check rights, EB Films may be renewed. 52f99990 *The Inner City* 1958 is too dark?). Fallback: Commons PD film; or LoC Bubley 2017862344 "laid up with a cold" still, held, with E1 defined as a cut to a second still. Wide or medium, never close POV. |
| S2 RING | 6.0–11.5 | A room or hall with the figure present and not moving toward the phone, or an unanswered telephone on a wall or table with nobody touching it. E2 ring-1 at 6.5, E3 ring-2 at 8.3 (the one he lets go). Ring-3 at 10.1 ends by 11.1. | telephone bell ×3, low-passed and quieter, as if through a wall (E2/E3). Room tone continues. | FORAGED. Picture: archive 575666be or b352abf2 *The Town and the Telephone* 1950 (telephone shot, no hand on receiver), or LoC Bubley 2017862346 "The telephone in a boardinghouse" if no one is on it, or a hall still 2017862354. Bell: Commons PD/CC0/CC BY recording of an electromechanical telephone ring, or the archive clip's own source sound if wordless. |
| S3 HELD (H) | 11.5–19.0 (7.5 s) | One held, static view of the figure sitting in a room, seen across the room, barely moving (breath, a hand). No voice in either pass. | room tone only: no ring, steps or voice. SILENCE id SIL-H. | FORAGED. Candidate archive 7836124c *Financial Investigation – Fundamentals* 2004 (man slumped in armchair under a lamp, static, 3 s; US federal-government training film, verify PD) looped by ping-free repetition, or cd9add6a (same film, longer take, check no speech in source sound). Alternative: Bubley 2017862333 / 2017862362 boardinghouse room still held 7.5 s. Room tone: archive clip source sound of a quiet interior, or a Commons CC0 room-tone recording. |
| S4 FLIGHT 1 (F1) | 19.0–24.5 | Stairwell seen from above or below, empty, then a man walks the flight and leaves frame. E4 entry at ≈20.5, exit ≈23.5 (measured from the clip, with 1.5 s empty pre-roll). | footsteps on stairs (clip source sound or Commons), room/stairwell tone | FORAGED. Archive 14c8b94b *Third Avenue El* (3.2 s, a man on a tenement stair seen from above; source in/out 55.322–58.525). Pad with that same clip's empty first or last frames only if they are the source's own frames; otherwise choose a longer stair take. Alternatives via "stair|stairwell|steps|landing". Must show the empty stair before entry and after exit. |
| S5 LANDING | 24.5–27.0 | an empty boarding-house hall or landing, static | steps fading, room tone | FORAGED. LoC Mydans 2017714055 "Stairway in rooming house" or Bubley 2017862356 "The upstairs of a boardinghouse" (re-verify item pages). |
| S6 FLIGHT 2 (F2) | 27.0–32.5 | **identical frames to S4** (same in/out). E5 entry ≈28.5, exit ≈31.5. | same steps, same mix (identical audio is allowed and preferred) | FORAGED (reused). |
| S7 TAIL | 32.5–35.0 | the empty stairwell: the clip's final empty frame held, or the S5 landing still again | room tone | FORAGED (reused). |

Caption tracks (HANDMADE: typeset captions via kit `Ink.caption`, serif, one band; identical strings in both tracks):

| clause | text | event | A_ahead interval | B_behind interval | relation A / B |
|---|---|---|---|---|---|
| c1 | You open your eyes. | E1 wake 1.8 | 0.6–1.8 | 3.0–4.2 | anticipates / lags |
| c2 | You hear it through the wall. | E2 ring-1 6.5 | 5.3–6.8 (over S1, before the bell) | 7.7–9.2 | anticipates / lags |
| c3 | You do not answer. | E3 ring-2 8.3 | 7.1–8.3 | 9.5–10.7 | anticipates / lags |
| (none) | | SIL-H | 11.5–19.0 silence | 11.5–19.0 silence | leaves_silence |
| c4 | You take the stairs. | E4 F1 entry 20.5 | 19.3–20.5 (empty stair) | 21.7–22.9 (body visible) | anticipates / lags+overlaps (Bl) |
| c5 | You take the same stairs again, one step after another. | E5 F2 entry 28.5 | 27.3–30.1 | 29.7–32.5 (body exits ≈31.5) | anticipates / lags past exit (D) |

Note on c2 A: its onset at 5.3 falls in S1 before the S2 edit. It belongs to E2, which starts in S2. That is the one deliberate "ahead" crossing of an edit, and it crosses into its own event's shot, not across H. The referent checker must record it as allowed under precondition 4. If the critic finds it confusing, the alternative branch "c2A-in-shot" starts S2 at 5.0. Both are kept as named branches.

All times marked "≈" are re-measured from the chosen footage by the image unit. The voice unit then recomputes onsets as event ± 1.2 s, and the checker re-verifies preconditions 3–4 and the condition D_end ≥ exit + 0.8.

Sound design rules (sound unit): the bell is low-passed (~2.5 kHz) and quiet relative to room tone, so it reads as "through the wall". Footsteps sit closer and drier. Room tone is continuous across all shots at a constant level (so H is not dead digital silence). Withheld cue: no sound effect marks E1 (the wake is silent), and in pass B the bell is heard 1.2 s before the clause that names it.

## 7. Swarm units

| unit | role (prompt sec. 5) | output |
|---|---|---|
| U1 image | camera team: quiet observational cut | films/swarm/un-homme-qui-dort/picture_ledger.json + media under films/sources/un-homme-qui-dort/image/ |
| U2 sound | sound editor: distance, breath, withheld cues | films/swarm/un-homme-qui-dort/sound_ledger.json (silence map) + media under films/sources/un-homme-qui-dort/sound/ |
| U3 voice+referent | voice writer + referent checker (coupled: same ledger; the checker pass is a distinct step run after U1's measurements land) | films/swarm/un-homme-qui-dort/clause_ledger.json + referent_audit.txt |

The montage editor (assembler of films/un-homme-qui-dort.py, credits, notes) and the independent viewer/critic are run separately by the workflow.

## 8. Acceptance bar (falsifiable)

1. The render is 70–75 s and consists of two 35.0 s passes (±0.1 s), each preceded by a ~1 s card naming the pass. Within each pass, the picture and non-voice sound are the same across passes (ledger: identical shot sources and in/out points; frame hashes match).
2. In each pass the figure wakes, a telephone audibly rings at least twice and nobody answers it, and the same stair clip appears twice with identical source in/out points (F1 = F2 by frame hash). No shot is from the figure's point of view (picture_ledger camera_viewpoint ≠ eye line on every shot, and confirmed by watching).
3. Tracks A and B contain exactly the same clause strings in the same order. Every clause is in the second person with addressee "you:A1". No he/she/I narration line appears on screen.
4. Every clause onset in track A is 1.2 ± 0.05 s before its bound event's measured onset, and every onset in track B is 1.2 ± 0.05 s after it. This is checked in clause_ledger.json against picture_ledger.json event times.
5. A held shot of ≥ 7.0 s exists in both passes with no caption on any frame and only room tone audible (no bell, step or voice onset; non-zero room-tone level). It sits at the same time in both passes.
6. Defining beat: in pass B the c5 caption is visible on at least 0.8 s of frames where the figure has left the stair (empty stairwell). In pass B, c4 is fully contained in the interval where the figure is visible. In pass A, c4 and c5 begin on empty-stair frames before the figure enters.
7. Every on-screen and audible element is foraged, with a credit entry (source_url, licence acceptable under BRIEF-2 or a best-supported movingimagearchive PD status), or handmade (cards, captions). No filters, faux grain, drawn figures or frames from the 1974 film. Audible archive speech is absent.
