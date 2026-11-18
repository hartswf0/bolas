# SCION swarm plan: un-homme-qui-dort ("Second-person voice"), plan r1

Revision base: plan-r1, 2026-11-15. Prompt: `prompts/un-homme-qui-dort.md`, read in full. The common beat ledger is `beats.json` in this folder. It is authoritative: every unit forks from it, and every time below is copied from it. The r0 swarm files (a stills-and-captions cut) were moved, unchanged, to `r0-superseded/`. Units may read them for licence evidence only and must not build on their timeline.

The reference looked at was `assets/references/sommeil.webp` (QAGOMA / Dovidis still). It shows a young man's face against a wall beside a doubled, back-turned reflection. What it teaches: one anonymous body, seen from outside, doubled. We do not imitate its look, and no frame of the 1974 film is used.

## 0. Material decision (why these sources)

We first looked at the Moving Image Archive cache (allways-forage `forage.py`, contact sheets for `stair|steps`, `telephone|phone`, `bed|sleep|wak|alarm` and `room|apartment|hotel|lonel`). It has a man in a stairwell (14c8b94b, *Third Avenue El*, 1955, an independent short with no public-domain status established, so it is **rejected**). It has men dozing in armchairs (db4a7675, *Alcohol and the Human Body*, 1949, EB Films, renewal unknown; 7836124c and cd9add6a, *Financial Investigation – Fundamentals*, 2004, a US federal training film). It has telephones (575666be and b352abf2, *The Town and the Telephone*, 1950). No single archive film gives one body that wakes, ignores a phone and climbs a stair from a camera outside him.

The Library of Congress FSA/OWI negatives already on disk do give that. John Vachon's December 1940 set at Mrs. Pritchard's boardinghouse in Radford, Virginia, shows one house and a few rooms: a man in his bunk (seen inside the room and through the doorway) and a man going upstairs. All are "No known restrictions" and are US government work. So:

- **Picture = FORAGED LoC FSA negatives, animated** with SCION-29 (cutouts), SCION-44 (multiplane parallax) and SCION-47 (sound-driven action). The figures move because they are real cutouts, articulated and staged in depth, not slides.
- **Sound = FORAGED.** The Moving Image Archive cache's source sound comes first: wordless interior or room tone, and a telephone bell if a speech-free one exists. Wikimedia Commons recordings (PD, CC0, CC BY, CC BY-SA) fill what the cache lacks.
- **Captions and cards = HANDMADE** typography (kit `Ink.caption`, kit fonts).
- Archive branch (kept named, not default): `HELD-archive` uses cd9add6a, the man in an armchair, as S4, if U1 finds that the doorway man's gaze goes into the lens. It is used only after U1 confirms the item is a US-government work and the clip carries no speech used on the soundtrack.

## 1. Creative thesis

A voice says "you" to a man we only ever watch from outside: from the foot of his bunk, through his doorway, from the hall below his stair. The man is cut from a 1940 government photograph and made to move. The same 35-second picture is shown twice with word-identical narration. In pass I each clause comes 1.2 s before the action it names, so "you" sounds like an instruction the body then obeys. In pass II each clause comes 1.2 s after its action, so "you" sounds like a recollection. Because the second staircase is the same frames as the first, the only thing that changes is when "you" arrives. In one interval of pass II the voice is still saying "you take the same stairs" after the body has left the frame. "You" then has nobody on screen to land on but the viewer.

What would make it bland: narration that names what we already see while we see it (pure duplication), a camera that drifts into the man's eyeline, or stills that only cross-fade.

## 2. Defining beat and comparison baseline

- **Defining beat D:** pass II, shot S7 (flight 2). c5, "You take the same stairs again, one step after another.", is shown at 29.7–32.5. The figure enters at 28.5 and leaves the frame at 31.5. That gives 1.0 s of empty staircase (only wall, banister and stair) carrying a second-person clause. A viewer can point to those frames.
- **Baseline Bl:** pass II, shot S5 (flight 1). These are the same frames with the same 1.2 s lag. c4, "You take the stairs.", is shown at 21.7–23.0, entirely inside the figure-visible interval 20.5–23.5. Here "you" lands on the character.
- **Second baseline:** pass I, S7. These are the same words as D, but they start at 27.3, over the empty stair before the body enters at 28.5, and read as an order the figure carries out.
- **Success:** a fresh viewer who marks "when the voice felt addressed to me" places a mark inside D (pass II, 31.5–32.5) and not inside Bl. The repair loop (section 8 of the prompt) compares this with an onset-only shift and a camera-distance-only change.

## 3. Lineage Genome (compact)

| field | value |
|---|---|
| source | *Un homme qui dort*, Georges Perec and Bernard Queysanne, 1974, a 35 mm b/w feature adapted from Perec's 1967 novel. The narration is in "tu" over a mostly silent young man (Jacques Spiesser) in Paris. Waschneck, *Screening OULIPO*, p. 9, identifies the second-person narration. That the voice is a woman's (Ludmila Mikaël) is from general film knowledge and is **uncertain** here (not checked against QAGOMA). |
| target | a 35 s screen study shown twice with two timings of the same words, 72.0 s with two cards, 960×540, 24 fps, ≤ 6 MB |
| preserved relation | address ("you", off-screen narrator) and observation (a camera outside the body) are two channels that never merge |
| optics change | 35 mm location cinematography becomes 1935–1940 FSA large-format negatives. The figure is a GrabCut cutout staged on multiplane layers cut from the same negatives, and the camera is a virtual glide across real planes. This is declared as a change of optics. |
| formalism change | the novel's and film's long variable narration becomes 5 clauses bound to 5 event IDs with declared relations (anticipates / lags / leaves silence). The repeated staircase is literal frame identity, and the event times are authored by the animation, so they are exact. |
| concept change | the source leaves the "tu" ambiguous. Here, two timelines of identical words test where "you" lands (character, audience, or both). |
| sound change | a spoken voice becomes captions (no TTS; no openly licensed voice of the source). Foraged room tone, a bell heard "through the wall" (sonic perspective fixed at the bunk room in every shot) and footfalls that drive the figure's step accents (SCION-47) |

Formation epochs (weight 0–100, with reason):
- Second-person fiction and the nouveau roman (Butor, *La Modification*, 1957), weight **70**: the grammatical device itself. That Perec drew on Butor directly is a common critical claim, recorded as **uncertain**.
- Oulipo constraint practice (1960 on), weight **50**: fixed rules, frame identity, a word-identical retake. Perec joined in 1967. The film is not formally an Oulipian constraint work (**uncertain** classification).
- Post-1968 French essay and observational film, weight **45**: held voice-free shots and the camera kept outside the subject.
- Cutout and multiplane animation (Reiniger 1920s; the Disney and Norstein multiplane; Gilliam's photo cutouts), weight **40**: the method by which still archive bodies are made to act. This is a change of technique, not the source's lineage.
- FSA/OWI documentary photography, 1935–1943, weight **35**: the material. Its observational, outside-the-subject stance happens to match the brief.
- Timecoded sound-to-action scoring (SCION s47), weight **60**: the voice and sound tracks are performance scores whose onsets drive and judge the picture.

## 4. Olog (types, bind, central operation)

**Types**
- `AddressClause` {clause_id, text, addressee_id = "you:A1", grammatical_person = 2, predicate, track ∈ {A_ahead, B_behind}, spoken_interval [on, off] (caption visible)}
- `ObservedAction` {event_id, subject_id ∈ {figure:F, object:telephone}, observation_interval [on, off], shot_id}
- `Viewpoint` per shot, four distinct fields:
  - camera_viewpoint (e.g. "through the open doorway")
  - narrator = "N, off-screen, captions only"
  - on_screen_performer = "figure:F, W.W. McDaniel or the unnamed powder-plant employee (FSA negatives), one role"
  - audience_position = "spectator before the screen"

  Invariant: camera_viewpoint ≠ the figure's eyeline (no POV shot).
- `DiegeticSpeech` track: declared **empty**. No archive speech is ever audible.
- `Silence` {SIL-H, [11.5, 19.0], allowed_sound = room tone only}
- `Layer` (from SCION-29/44) {layer_id, source_loc_id, mask_path, depth z, parallax ratio, invented_fill_mask or null}

**Central operation: bind(c: AddressClause, e: ObservedAction, relation)**, relation ∈ {anticipates, overlaps, lags, leaves_silence}

Typed preconditions:
1. c.grammatical_person = 2, and c.addressee_id = the current declared addressee "you:A1". No marked shift exists in this proof.
2. e.event_id exists in `beats.json` at the current revision, and e.shot_id is not a POV shot.
3. Offsets: anticipates ⇒ c.on = e.on − 1.2 ± 0.05; lags ⇒ c.on = e.on + 1.2 ± 0.05. overlaps is computed (|c ∩ e| > 0), never declared.
4. c.spoken_interval ∩ SIL-H = ∅ (guard 0.1 s). c never straddles an edit into a shot holding a *different* event. Running into its own event's shot is allowed (c2.A and c3.A are listed in beats.json).
5. The text of c is identical in tracks A and B.

Observable consequences:
- anticipates: the caption is on screen before the named action is visible, measured by frame. Example: c4.A at 19.3 over the empty stair, with the figure entering at 20.5.
- lags: the action is visible before the caption appears. For c5.B the caption remains on frames with zero figure-alpha coverage (D).
- leaves_silence: in SIL-H there is no caption for 7.5 s. The soundtrack holds room tone only (non-zero level, no transient onset). The figure is still visible and barely moves, with a breath-only branch.

Counterexamples (must fail the gate in `u3-gate.py`):
- c′ = "He hears it through the wall." bound to E2. Precondition 1 fails (grammatical_person = 3), so c′ is quarantined. This is the prompt §7 fixture.
- Moving c4.A to an onset of 18.8 (1.7 s ahead) puts voice inside SIL-H. Precondition 4 fails, the sound editor's silence review is invalidated, and the move is rejected.
- c2.B lengthened to end at 8.7 straddles S2→S3, the shot of E3. Precondition 4 fails.

Replay and alternate views:
- **Equivalent:** the picture layer of pass I and pass II is the same frame sequence (byte-identical before captions). Flight 1 (S5) and flight 2 (S7, 27.0–32.5) are the same 132 frames. The clause strings are identical across tracks. The non-voice sound is identical across passes.
- **Divergent:** the spoken intervals, and therefore the overlap set. In A, c1–c3 come before their actions and c4 sits over the empty stair. In B, c4 overlaps the body (Bl) and c5 outlasts the body (D). The same words yield an anticipatory and a retrospective timeline, and both are valid (prompt §7).

Interaction: none. This is a linear screen study, and the two passes are its alternate views.

## 5. Invariants (asserted in `u3-gate.py`; the editor's script re-asserts them)

1. Narrative address is 2nd person only, addressee "you:A1" throughout. There is no he/she/I narration and no marked shift.
2. The diegetic-speech track is separate and empty. No audible speech appears from any foraged clip.
3. SIL-H, 11.5–19.0 (7.5 s ≥ 7.0 s): no caption and only room tone. It is identical in both passes.
4. No POV shot. Every shot's camera_viewpoint is outside the figure.
5. S5 frames == S7 frames 27.0–32.5, checked by SHA-1 per frame of the pre-caption picture. Pass I picture == pass II picture.
6. Tracks A and B share strings, order and durations. Only the onsets differ (∓1.2 s).
7. Picture events land on the planned frame round(t·24) ± 1. The animation is authored, so events are exact.
8. Every foraged pixel and sample is credited with an accepted licence. Every invented pixel (fills behind cutouts, wall extension) is listed with its mask. No filters, no faux grain and no vignette: kit `Film(..., boil=0, wobble=0)`, and `ink.paper(grain=False)` called in every frame, because kit's default `paper()` adds grain. There are no drawn figures and no frames from the 1974 film.
9. (SCION-29) Cutouts have no background islands and no halos visible at normal size. The coat on the stair-man's arm stays attached as its own piece. Failure masks are exported.
10. (SCION-44) The near plane moves more than the far plane in every glide (parallax ratio near/far ≥ 1.5). Occlusion order stays coherent: the banister is always in front of the stair figure's legs, and the door edge is in front of the bunk.
11. (SCION-47) The figure has no mouth motion (no speech). Each body accent is tied to a sound event in `beats.json` (footfall → step dip, ring 3 → glance). There is no idle motion without a declared purpose, and the breath in SIL-H is a named branch.

## 6. Timed shot list (Hard proof §6: wake, ignore a ringing phone, the identical staircase twice, a held room-sound shot, two voice takes)

Film layout: [CARD-I 0–1.0] [PASS-A 1.0–36.0] [CARD-II 36.0–37.0] [PASS-B 37.0–72.0]. Cards are HANDMADE, set in kit serif with a neutral "I" and "II" on plain paper (no grain). The viewing cut has no diagnostic strip. The editor may render a separate diagnostic cut with a beat strip. Times are pass-relative.

| shot | time | on screen (FORAGED + animation) | heard (identical in both passes) | SCION method |
|---|---|---|---|---|
| S1 WAKE | 0.0–5.5 | LoC **2017811426** (Vachon 1940, McDaniel reclined in his bunk, seen from its foot). Planes: far = plank wall with coat hooks; mid = headboard and bunk; figure = GrabCut of the man, split into two pieces: legs and bedding (fixed) and head + torso (pivot at the hip); near = bedding edge and bunk frame cut from the same plate. The camera glides 28 px left to right over 5.5 s. **E1 at 2.0–2.8:** the head-torso piece rotates −5° about the hip pivot and rises 6 px (eased), so the body lifts from the pillow. The fill behind the moved piece is `cv2.inpaint` from the same plate, flagged as invented, with its mask exported. | room tone, continuous; no sound marks the wake (a withheld cue) | 29, 44, 47 (an expressive hold before E1) |
| S2 TELEPHONE | 5.5–8.5 | LoC **2017735081** (Russell Lee 1936, a crank wall telephone beside hanging coats; nobody present). Planes: far = wall, telephone and notice; near = the coats (GrabCut with an alpha-cleanup pass on the fur collar, per SCION-29 matting). Slow push: scale 1.00 to 1.04, with the coats 2× the wall's drift. Nothing touches the telephone. | **E2 ring 1 at 6.0–7.0, E2b ring 2 at 7.6–8.6:** a telephone bell, low-passed (about 2.5 kHz), quieter, with room reverb, so it is heard *from the bunk room through the wall*. The sonic perspective is the body's room, not the camera's. | 44, 47 |
| S3 REFUSE | 8.5–11.5 | LoC **2017811449** (the same man on the same bunk, seen through the open doorway). Planes: near = door leaf with padlock and the left jamb (they occlude); mid = the man (GrabCut, head piece separate); far = back wall and shelf. The glide eases to rest by 10.5. **E3 ring 3 at 9.0–10.0:** at 9.25 the head piece turns 3° toward the door (attention). It holds, he does not reach (refusal), and the head returns at 10.4 (changed state: he has let it go). | ring 3 at 9.0–10.0 (same treatment), then room tone | 29, 44, 47 |
| S4 HELD (SIL-H) | 11.5–19.0 (7.5 s) | The S3 rig, camera at rest: no glide. The body and place are seen through the doorway. Default: nothing moves. Branch `HELD-breath`: the torso piece rises at most 1.5 px per 4 s breath cycle (flagged as invented secondary motion). Branch `HELD-archive`: cd9add6a, only if U1 judges that the gaze in 2017811449 meets the lens. | **room tone only**: no bell, step or voice. Non-zero level, constant, no transient. | 44 (held), 47 (silence animates thought) |
| S5 FLIGHT 1 | 19.0–24.5 (132 frames) | LoC **2017811447** (Vachon 1940, a powder-plant employee going upstairs in profile, a plaid coat over his arm). The figure is GrabCut-extracted with the coat as an attached second piece. The wall behind him is rebuilt from the plate's own wallpaper by patch copying (an invented texture extension, mask exported). Planes: far = wallpaper wall and newel; mid = stair treads; figure; near = banister and balusters cut from the plate (they occlude the legs). Empty stair 19.0–20.5. **E4: the figure enters lower left at 20.5 and climbs along the measured stair line. Each footfall (20.8, 21.35, 21.9, 22.45, 23.0) gives a 3 px dip and recovery (audio-driven step accent). He leaves the frame upper right at 23.5.** Empty stair 23.5–24.5. A small lateral glide runs throughout; the banister moves at least 1.5× the wall. | footsteps on a wooden stair, closer and drier than the bell, each footfall sample placed at its ledger time (not time-stretched); room tone | 29, 44, 47 |
| S6 STAIRWELL | 24.5–27.0 | LoC **2017714056** (Mydans 1935, a rooming-house stairwell looking up, empty). Planes: near = the lower banister and newel; mid = the flights; far = ceiling and skylight. Slow upward tilt (the near plane moves fastest). | the steps continue above, quieter and further (two footfalls from the same recording, at −12 dB with more reverb), then room tone | 44 |
| S7 FLIGHT 2 + TAIL | 27.0–35.0 | 27.0–32.5: **S5's 132 frames reused byte-identically**. E6: entry 28.5, footfalls 28.8–31.0, exit 31.5. 32.5–35.0: S5's last frame held (the empty stair), so there is no edit after the defining beat. | the same footstep cues and mix as S5, then room tone to the end | reuse (invariant 5) |

Voice takes (HANDMADE captions, one band, kit serif; identical strings and durations in both tracks; times from `beats.json`):

| clause | text | event (t_on) | A_ahead | B_behind | relation A / B |
|---|---|---|---|---|---|
| c1 | You open your eyes. | E1 2.0 | 0.8–2.0 | 3.2–4.4 | anticipates / lags |
| c2 | You hear it through the wall. | E2 6.0 | 4.8–6.05 (S1 into S2, its own event's shot) | 7.2–8.45 | anticipates / lags |
| c3 | You do not answer. | E3 9.0 | 7.8–9.0 (S2 into S3, its own event's shot) | 10.2–11.4 | anticipates / lags |
| — | (none) | SIL-H 11.5–19.0 | silence | silence | leaves_silence |
| c4 | You take the stairs. | E4 20.5 | 19.3–20.6 (empty stair) | 21.7–23.0 (body visible) | anticipates / lags + overlaps = **Bl** |
| c5 | You take the same stairs again, one step after another. | E6 28.5 | 27.3–30.1 | 29.7–32.5 (body gone at 31.5) | anticipates / lags past exit = **D** |

Elements, FORAGED or HANDMADE:
- FORAGED, LoC (tile.loc.gov; fetch the largest available JPEG/TIFF-derived JPEG for cutting): 2017811426, 2017811449, 2017735081, 2017811447, 2017714056. Reserves: 2017811427, 2017811431, 2017714055, 2017862346. Re-verify each item's `rights_advisory` ("No known restrictions") from its `?fo=json` record.
- FORAGED sound:
  - Moving Image Archive cache first: search `room|interior|quiet|night|apartment|hotel`, `telephone|ring|bell`, `stair|steps|footstep` with `--media clip`. LISTEN, and accept only speech-free stretches from items whose pages are not marked copyrighted.
  - Commons second, with extmetadata licences. Candidates already found in r0: "Model 500 Telephone British ring" (CC BY-SA 3.0), "Wooden stairs (Gravity Sound)" (CC BY 4.0), "TU Delft Library quiet study room" (CC BY 3.0). Re-verify them, and prefer a magneto or wall-phone bell that matches the crank telephone on screen if one exists.
- HANDMADE: the two cards; the caption typography; the cutout rigs, plane splits and camera paths (built for this work from the foraged negatives). Every invented fill is listed.

## 7. Animation technique SCIONs (prompts read in full; their methods are applied for real)

1. **SCION-29, GrabCut: Cutout Extraction Swarm.** The figures exist only inside 1935–1940 negatives, and the proof needs a body that wakes, turns and climbs. `cv2.grabCut` is run with box and scribble seeds on high-resolution LoC scans, using the photograph preset (silver-gelatin grain is not body texture). Alpha cleanup is done by morphological open/close and a feathered edge of 1–2 px at most. Applied in S1 (man in two pieces, pivot at the hip), S2 (coats as the near plane, with fur-collar matting), S3/S4 (the man, with a separate head piece; the door leaf as a cut plane) and S5/S7 (the climbing man with the coat as an attached piece; banister and balusters cut out as the near plane). Its invariants hold: no background islands, fingers and coat retained, halos isolated, failure masks exported, and an RGBA piece plus an original-coordinate transform for every layer.
2. **SCION-44, Multiplane Parallax: Spatial Collage Swarm.** The camera must stay outside the man and still feel present in his room. Real depth planes cut from each negative, with a lateral glide in which near planes move more than far ones, give the observing position a body without ever taking his eyeline. Occlusion carries the "outside" stance: the door edge in front of the bunk, the banister in front of the legs. Applied in S1, S2, S3, S5/S7 (glides) and S6 (tilt); S4 is the same rig deliberately at rest. Its rules hold: parallax ratio ≥ 1.5 near/far, coherent occlusion, no foreground stretching, and invented texture extensions flagged with masks. Dramaturgical plane functions: the door is *confine*, the banister is *shield*, the empty stair is *distant witness*.
3. **SCION-47, Sound-to-Action: Viseme and Gesture Swarm** (also the prompt's own source anchor: "use the timecoded voice track as a performance score"). Its hard proof, a portrait that "hears an unseen object fall, then chooses not to answer", is this film's telephone beat. Audio events in `beats.json` drive the selective action: ring 3 → glance at +0.25 s → hold → return, which is attention → intention → refusal → changed state. Footfalls drive the step dips on the stair. The voice track (captions) is the score against which every event is placed ∓1.2 s. The viseme set is declared empty and the mouth stays closed, because the man never speaks (no flapping in silence). Silence is used to animate thought in SIL-H.

## 8. Swarm units (prompt §5; coupled tasks merged; editor and independent viewer run separately)

| unit | prompt §5 role(s) | mode | output (inspectable) | media saved under |
|---|---|---|---|---|
| **U1 picture** | camera/drawing team: the quiet observational cut (+ SCION-29 extraction, SCION-44 staging, SCION-47 body actions) | forage + handmake | `u1-picture-ledger.json`: plates with LoC IDs and verified rights, layers (mask paths, z, parallax ratios, invented-fill masks), camera paths, measured event frames, figure-alpha coverage per frame for S5/S7, and the SHA-1 list proving S5 == S7. Also `u1-contact.jpg`. | `films/sources/un-homme-qui-dort/u1-picture/` (raw/, rgba/, masks/, failure_masks/, fills/, shots/S1..S7 PNG sequences + .mkv) |
| **U2 sound** | sound editor: distance, breath, withheld cues | forage | `u2-sound-ledger.json`: sources and licences, stems with in/out points and gains, the sonic-perspective declaration, and the SIL-H measurement (RMS floor and max transient) | `films/sources/un-homme-qui-dort/u2-sound/` (wav stems at 48 kHz) |
| **U3 voice + referents** | voice writer + referent checker (coupled on one ledger; the checker step runs after reading U1's measured events) | handmake | `u3-clause-ledger.json` (clauses, referent tags, bind relations per track), `takeA.srt`, `takeB.srt`, `u3-gate.py` (pure-python gate, including the three counterexamples), `u3-referent-audit.json` (gate output against U1's measured frames) | `films/sources/un-homme-qui-dort/u3-voice/` (caption proof PNGs) |

All units use the authored times in `beats.json`, so they can run in parallel. U1 must deliver events on those frames. U3 re-audits against U1's measured values, and any mismatch is a quarantine plus a beats revision, never a silent shift.

## 9. Acceptance bar (falsifiable; checked by watching the render and reading the ledgers)

1. The film runs 72.0 ± 0.2 s: two 35.0 s passes, each after a ~1 s neutral card. The pre-caption picture and the non-voice sound of pass I equal those of pass II (frame hashes and stem list in the ledgers).
2. In each pass the viewer sees the man lift from his pillow (E1), hears a telephone ring three times while nobody answers (he glances, holds and stays), and sees the same stair flight twice. S5 and S7 (27.0–32.5) are hash-identical. No shot is from his point of view.
3. Tracks A and B contain the same five strings in the same order with the same durations, all in the second person with addressee "you:A1". `u3-gate.py` passes them and rejects "He hears it through the wall." (output recorded).
4. Every A onset = event − 1.2 ± 0.05 s and every B onset = event + 1.2 ± 0.05 s, measured against U1's measured event frames.
5. SIL-H (11.5–19.0, ≥ 7.0 s) has no caption on any frame in either pass. Its audio has a non-zero room-tone floor and no transient more than 6 dB above that floor (U2 measurement).
6. Defining beat: in pass II, c5 is on screen for ≥ 0.8 s of frames with zero figure-alpha coverage on the stair. c4 in pass II lies wholly within the figure-visible interval of S5. In pass I, c4 and c5 begin on empty-stair frames.
7. The animation is real. The figures are GrabCut cutouts from the named LoC negatives (RGBA and masks on disk) that visibly move: the wake lift, the glance, and the climb with step dips. In every glide the near plane moves ≥ 1.5× the far plane, and the banister occludes the climbing legs. Invented fills are listed with masks. There are no filters, grain or vignette (kit grain off), no drawn figures, and no frames from the 1974 film.
8. Every foraged image and sound is in `films/credits/un-homme-qui-dort.json` with an accepted licence (PD, CC0, CC BY, CC BY-SA, or a movingimagearchive best-supported PD status), and no speech is audible anywhere.
