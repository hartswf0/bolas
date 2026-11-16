# SCION swarm plan: un-homme-qui-dort ("Second-person voice"), plan r2

Revision: plan-r2, 2026-11-15. Director. The prompt `prompts/un-homme-qui-dort.md` was read in full.

The authoritative timing is `beats.json` (beats-r2) in this folder. The measured reference target is `aesthetic.json` (aesthetic-r2). Every unit forks from these two files at these revisions.

Earlier swarm material is kept but is not built on:
- `r0-superseded/` holds a stills-and-captions cut.
- `r1-superseded/` holds the r1 plan, beats-r1 and the partial `u1-build/` rigs. r1 was planned without an aesthetic target.

Units may read both folders for licence evidence and code ideas. They must not inherit r1's plates or framings.

Why r2 exists: the user asked that the film now *animate towards the aesthetic reference*. r1 staged wide Vachon bunkhouse plates in flat mid-grey. The reference is a hard-lit, close, bimodal black-and-white head against a pale wall, with a dark double beside it. r2 changes the material and the framing to arrive there honestly.

---

## 0. AESTHETIC TARGET (reference: `assets/references/sommeil.webp`)

The catalogue entry (`catalogue/cinema.json`, slug `un-homme-qui-dort`) names one image: *"A black-and-white close-up of Jacques Spiesser beside a doubled reflection"*, credit QAGOMA / Dovidis. It has no gallery. The image is studied and measured only. It is never copied, traced, pasted or composited, and no frame of the 1974 film is used.

What it shows: a young man's head and open-collared shirt, slumped against a pale wall and a door or mirror-frame edge. He looks at the lens from under his fringe. Right of the frame edge is a mirror holding *two* back-turned heads in dark suits, a doubling like Magritte's *La reproduction interdite* (that association is a perceptual reading and is **uncertain**).

Measured with PIL/numpy (full numbers in `aesthetic.json`):

| property | measurement | what it asks of the film |
|---|---|---|
| Medium | silver-gelatin black-and-white still (35 mm production photograph) | genuinely black-and-white photographic material, nothing tinted or colourised |
| Neutrality | mean RGB 128.0/128.0/128.0; mean chroma 0.005, max 1 | pure neutral grey, no sepia, no cream. The kit's cream PAPER/PAGE colours are excluded from picture and captions. |
| Tonal range | L p1 = 27, p5 = 30, p25 = 41, p50 = 94, p75 = 238, p95 = 246, p99 = 246 | blacks are lifted (never 0), whites soft-clip about 245, and very little sits in the midtones |
| Bimodality | 41.6 % of pixels below L 60, 32.6 % above L 220, 25.7 % between | hard light, deep shadow and a pale wall, which needs flash-lit or window-lit interiors |
| Palette (8-colour quantise, share) | #2c2c2c .171 · #efefef .161 · #f5f5f5 .152 · #252525 .124 · #1e1e1e .111 · #444444 .104 · #828282 .104 · #d6d6d6 .074 | anchor black **#1e1e1e**, anchor white **#f5f5f5**, mid **#828282** rare |
| Light / space | column means by tenths L→R: 226 218 191 177 118 87 62 67 57 70 | a pale lit wall fills the left ~40 % and a shadow mass fills the right ~50 %, with the head on the boundary. A single hard key from frame left/front casts the head's shadow on the wall. |
| Texture | high-pass σ: white wall 0.86, shadow 1.78, midtone 3.47 | fine grain, visible only in midtones, comes from the negative itself. None is added. |
| Framing / scale | head height ≈ 0.48 of frame height; one body; shallow space; 1.42:1 | close-ups. The anonymous body is close enough to be *observed* (skin, hair, collar). |
| The double | two identical back-turned heads in the mirror | the film's doubling is the identical staircase taken twice, plus the man's own cast shadow on the wall in S3/S4 |
| Typography | none in the still | captions follow 1970s French subtitle practice: white serif (kit `serif`, Instrument Serif, 26 px, #efefef) on a neutral #1e1e1e band at 60 % opacity, never kit's cream band. Cards: numerals "I" / "II" in #efefef on #1e1e1e. |
| Pacing (from the source film's practice and the still's stasis) | n/a | few cuts (7 per pass), long holds, glides of 30 px or less per shot, and one 7.5 s held shot |

**How the film arrives there with real material and real technique**

1. **Material chosen for its light.** The core plates come from Esther Bubley's January 1943 FSA/OWI set of a Washington, D.C. boardinghouse. She shot it with on-camera flash: white walls, black jambs, hard cast shadows on the wall. That is the reference's lighting regime, met in real negatives.
   - S1 uses LoC **2017862333**, a man in bed, head on his hand.
   - S3 and S4 use LoC **2017862340**, "A boardinghouse philosopher": his head leans against a pale wall, his flash shadow is cast beside him, and a black door jamb runs at frame right.
   - The two frames appear to show **the same man** (curly dark hair, same face). This is perceptually judged and probable; U1 must confirm by side-by-side and record the result.
   - Both are "No known restrictions" (US government work). LoC item JSON was checked for 2017862340, and the credits file covers 2017862333.
2. **Real resolution for real close-ups.** The 1024 px service JPEGs cannot carry a close-up, because the head is only about 70 px wide. LoC's master TIFFs for this set are about 26–30 MB each (`8d33583u.tif` = 28.6 MB, `8d33576u.tif` = 30.3 MB, HEAD-checked). U1 downloads those two TIFFs and crops the close-ups from them, so close framing comes from real silver detail, not upscaling.
   - The Vachon and Russell Lee TIFFs are about 146 MB each, which is over budget. S2, S5 and S6 therefore use the 1024 px JPEGs at medium framing, with upscale ≤ 1.6×.
   - Budget: the sources folder already holds 153 MB, much of it regenerable derived PNG sequences from r0/r1. U1 may delete only *derived* PNG/MKV folders produced by earlier runs of this film, never raw downloads. It records in its ledger what was deleted and the final folder size, keeping new downloads ≤ 75 MB.
3. **Framing.** S1, S3 and S4 are close-ups, with head height ≥ 0.35, ≥ 0.35 and ≥ 0.42 of frame height. S4 is composed on the reference's measured layout: pale wall in the left 40 %, head on the boundary, cast shadow and jamb dark on the right. It is composed by cropping and placing the real plate, not by drawing anything.
4. **Grade only to unify.** One monotone, neutral tone curve per plate maps the plate's own p2 and p98 to L 30 and L 244, with a gentle toe and shoulder.
   - The 1936–1940 plates are flatter (p50 98–144) and get a steeper midtone, as a printer would print a flat negative on a harder paper grade.
   - Output is desaturated to exact neutral.
   - No blur, sharpening, vignette, faux grain, halation, scratches or flicker. Kit `Film(..., boil=0, wobble=0)` is used, `ink.paper(grain=False)` is called in every frame, and `ink.vignette` is never called.
   - Negative rebates and edge numbers ("OWI 38319-E") are cropped out, never shown.
5. **Doubling, made by the operation itself.** The identical staircase (S5 = S7, byte-identical) is the film's double. In S3/S4 the man's real flash shadow is cut as its own plane and follows his head turn, so the body has a dark twin on the wall, as in the reference, but from the plate's own light.

---

## 1. Creative thesis

A voice says "you" to a man we only ever watch from outside: close beside his pillow, across the room against a pale wall, from the hall below a stair. He is cut from 1940s government photographs, made to move, and lit by their own hard flash.

The same 35-second picture is shown twice with word-identical narration:
- In pass I each clause comes **1.2 s before** the action it names, so "you" is an instruction the body then obeys.
- In pass II each clause comes **1.2 s after**, so "you" is a recollection.

The second staircase is the same frames as the first, so the only thing that changes is *when* "you" arrives. In one interval of pass II the voice is still saying *"You take the same stairs again, one step after another."* after the body has left the frame. With nobody on screen for it to land on, "you" lands on the viewer.

What would make it bland:
- narration that names what we see while we see it (pure duplication);
- a camera that drifts into the man's eyeline (POV);
- stills that only cross-fade;
- a grey, mid-toned image that ignores the reference's hard light.

## 2. Defining beat and comparison baseline

- **Defining beat D.** Pass II, S7 (flight 2). c5 is on screen 29.7–32.5. The figure enters at 28.5 and exits at 31.5, leaving **1.0 s of empty stair** (wall, banister, treads) carrying a second-person clause. A viewer can point to those frames: film time 68.5–69.5.
- **Baseline Bl.** Pass II, S5 (flight 1). These are the same frames with the same 1.2 s lag. c4 "You take the stairs." at 21.7–23.0 lies wholly inside the figure-visible interval 20.5–23.5, so "you" lands on the character.
- **Second baseline.** Pass I, S7. The same words as D start at 27.3, over the empty stair before entry at 28.5, and read as an order the figure carries out.
- **Success.** A fresh viewer who marks "when the voice felt addressed to me" places a mark inside D (pass II, 31.5–32.5) and not inside Bl. Repair (prompt §8) compares an onset-only shift with frozen delivery, then held onsets with a camera-distance change. S5 is re-framed from medium to close, as a named branch `R-close`.

## 3. Lineage Genome (compact)

| field | value |
|---|---|
| source | *Un homme qui dort*, Georges Perec and Bernard Queysanne, 1974. A 35 mm b/w feature after Perec's 1967 novel, with second-person ("tu") narration over a mostly silent young man (Jacques Spiesser) in Paris. Waschneck, *Screening OULIPO*, p. 9, identifies the second-person narration. That the narrator is Ludmila Mikaël comes from general film knowledge and is **uncertain**. |
| target | a 35 s screen study shown twice with two timings of identical words: 72.0 s total with two 1 s cards, 960×540, 24 fps, ≤ 6 MB |
| preserved relation | address (off-screen "you") and observation (camera outside the body) stay two channels that never merge. Also preserved: the reference's hard b/w close observation of one anonymous body with a double. |
| optics change | 35 mm location cinematography becomes 1935–1943 FSA/OWI negatives (flash-lit Bubley interiors as the core). The figure is a GrabCut cutout on multiplane layers cut from the same plate, with a virtual glide across real planes. This is a declared change of optics. |
| formalism change | the long variable narration becomes 5 clauses bound to 5 event IDs with declared relations. The repeated stair is literal frame identity, and the event times are authored, so they are exact. |
| concept change | the source's "tu" is left ambiguous. Here, two timelines of identical words test where "you" lands. |
| sound change | the spoken voice becomes captions (no TTS, no openly licensed voice). Foraged room tone and a telephone bell heard "through the wall" (sonic perspective fixed at the man's room). Foraged footfalls drive the step accents (SCION-47). |

Formation epochs (weight 0–100, reason):
- **Second-person fiction / nouveau roman** (Butor, *La Modification*, 1957), weight **70**: the grammatical device itself. Perec's direct debt to Butor is a common critical claim and is **uncertain**.
- **Timecoded sound-to-action scoring** (SCION s47, a source anchor), weight **60**: voice and sound tracks are performance scores that drive and judge the picture.
- **Oulipo constraint practice** (1960 on), weight **50**: fixed rules, frame identity, a word-identical retake. Perec joined in 1967. Classifying the film as Oulipian is **uncertain**.
- **Post-1968 French observational and essay film**, weight **45**: held voice-free shots, the camera kept outside the subject.
- **FSA/OWI documentary photography** (1935–1943), weight **45**: the material. Bubley's flash interiors match the reference's hard light; the outside-the-subject stance suits the brief.
- **Cutout and multiplane animation** (Reiniger; Disney/Norstein multiplane; Gilliam photo-cutouts), weight **40**: how still archive bodies are made to act. This is a technique change, not the source's lineage.

## 4. Olog (types, bind, central operation)

**Types**
- `AddressClause` {clause_id, text, addressee_id = "you:A1", grammatical_person = 2, predicate, track ∈ {A_ahead, B_behind}, spoken_interval [on, off] (caption visible)}
- `ObservedAction` {event_id, subject_id ∈ {figure:F, object:telephone}, observation_interval [on, off], shot_id}
- `Viewpoint` per shot, with four distinct fields:
  - camera_viewpoint (from `beats.json`)
  - narrator = "N, off-screen, captions only"
  - on_screen_performer = "figure:F". This is one role played by the Bubley sitter in S1/S3/S4 and by the Vachon powder-plant employee in S5/S7, a declared casting substitution.
  - audience_position = "spectator before the screen"

  Constraint: camera_viewpoint ≠ the performer's eyeline. There is no POV shot, and no shot where his gaze meets the lens.
- `DiegeticSpeech` track: declared **empty**.
- `Silence` {SIL-H, [11.5, 19.0], allowed = room tone}
- `Layer` (SCION-29/44) {layer_id, source_loc_id, crop box in source coords, mask_path, z, parallax ratio, grade curve id, invented_fill_mask | null}

**Central operation: `bind(c: AddressClause, e: ObservedAction, relation)`**, relation ∈ {anticipates, overlaps, lags, leaves_silence}

Typed preconditions:
1. c.grammatical_person = 2, and c.addressee_id equals the declared addressee "you:A1". No marked shift exists in this proof.
2. e.event_id exists in beats-r2, and e.shot_id is not a POV shot.
3. anticipates ⇒ c.on = e.on − 1.2 ± 0.05; lags ⇒ c.on = e.on + 1.2 ± 0.05. overlaps is computed (|c ∩ e| > 0), never declared.
4. c ∩ SIL-H = ∅ with a 0.1 s guard. c never straddles an edit into a shot holding a *different* event. The listed crossings of c2.A and c3.A into their own event's shot are allowed.
5. c.text is identical in tracks A and B.

Observable consequences:
- anticipates: the caption is on screen before the named action is visible. Example: c4.A at 19.3 over the empty stair; the figure enters at 20.5.
- lags: the action is visible before the caption appears. c5.B stays on frames with zero figure-alpha coverage, which is D.
- leaves_silence: SIL-H carries no caption for 7.5 s. Audio is room tone only (non-zero floor, no transient). The close-up body stays visible and barely moves.

Counterexamples (must fail `u3-gate.py`):
- c′ = "He hears it through the wall." bound to E2 fails precondition 1 (person = 3) and is quarantined. This is the prompt's §7 fixture.
- Moving c4.A's onset to 18.8 puts voice inside SIL-H. It fails precondition 4, invalidates U2's silence review, and is rejected.
- Extending c2.B to end at 8.7 straddles S2→S3 into E3's shot. It fails precondition 4.

Replay and alternate views:
- **Equivalent:**
  - the pass I and pass II picture (identical pre-caption frames);
  - S5 and S7 27.0–32.5 (the same 132 frames);
  - the clause strings and durations;
  - the non-voice sound.
- **Divergent:** the spoken intervals, and with them the overlap set.
  - In A, c1–c3 precede their actions and c4 sits over the empty stair.
  - In B, c4 overlaps the body (Bl) and c5 outlasts it (D).

  The same words yield an anticipatory and a retrospective timeline, and both are valid (§7).

Interaction: none. This is a linear screen study, and the two passes are its alternate views.

## 5. Invariants (asserted by `u3-gate.py` and re-asserted by the editor)

1. Narrative address is second person only, addressee "you:A1" throughout. There is no he/she/I narration and no marked shift.
2. The diegetic-speech track is separate and empty. No speech is audible from any foraged clip.
3. SIL-H, 11.5–19.0 (7.5 s), has no caption and room tone only, identically in both passes.
4. No POV shot, and the performer's gaze never meets the lens.
5. S5 frames equal S7 frames 27.0–32.5 (SHA-1 per pre-caption frame), and the pass I picture equals the pass II picture.
6. Tracks A and B share strings, order and durations. Only the onsets differ (−1.2 / +1.2 s).
7. Picture events land on frame round(t·24) ± 1.
8. Every foraged pixel and sample is credited with an accepted licence, and every invented pixel (fill behind a moved piece, wall extension) is listed with its mask. No filters, faux grain or vignette; kit grain is off. No drawn figures and no 1974-film frames.
9. **Aesthetic** (from `aesthetic.json`):
   - Every film frame is neutral (mean chroma ≤ 1.5).
   - Each plate's grade is a single monotone neutral curve, recorded.
   - No negative rebate or edge numbers are visible.
10. (SCION-29) Cutouts have no background islands, fingers retained (S1 hand), no halos visible at normal size, and failure masks exported.
11. (SCION-44) The near plane moves at least 1.5× the far plane in every glide. Occlusion stays coherent: the banister is in front of the climbing legs, the door jamb in front of the man in S3/S4, and the cast-shadow plane behind the head and on the wall.
12. (SCION-47) There is no mouth motion. Each body accent is tied to a ledger sound event (footfall → step dip; ring 3 → head turn at +0.25 s). There is no idle motion without a declared purpose; the S4 breath is a named branch.

## 6. Timed shot list (Hard proof §6: wake, ignore a ringing telephone, take an identical staircase twice, a held room-sound shot, two voice takes)

Film layout:

| segment | film time |
|---|---|
| CARD-I | 0–1.0 |
| PASS-A | 1.0–36.0 |
| CARD-II | 36.0–37.0 |
| PASS-B | 37.0–72.0 |

Cards are HANDMADE: the numerals "I" and "II" in kit serif, #efefef on #1e1e1e. The viewing cut has no diagnostic strip; the editor may render a separate diagnostic cut. Times below are pass-relative.

| shot | time | on screen (FORAGED plate + animation) | heard (identical both passes) | SCION |
|---|---|---|---|---|
| **S1 WAKE** | 0.0–5.5 | **LoC 2017862333** (Bubley 1943), cropped from master TIFF `8d33576u.tif` to a close-up of head-on-hand, pillow and wallpaper. Book and rebate are cropped out; head height ≥ 0.35 of frame. Planes: far = wallpaper and curtain; mid = pillow and jacket; figure = GrabCut head (piece H) and hand/forearm (piece K, fingers retained); near = the jacket shoulder edge cut from the same plate. Glide 18 px L→R. **E1 2.0–2.8:** H lifts 8 px off K and rotates 4° upright about the neck pivot (eased in/out). K stays, so contact is released: the body rouses. Fill behind H is `cv2.inpaint` from the plate, flagged invented, mask exported. His eyes are down, off-lens, throughout. | room tone, continuous; no sound marks the wake (a withheld cue) | 29, 44, 47 |
| **S2 TELEPHONE** | 5.5–8.5 | **LoC 2017735081** (Russell Lee 1936), a crank wall telephone beside hanging coats, nobody present. Close crop: the phone box ≥ 0.45 of frame height, upscale ≤ 1.6× from the 1024 px JPEG. Graded on the harder curve to the reference anchors. Planes: far = wall, phone, notice; near = coats (GrabCut plus alpha cleanup on the fur collar). Push 1.00→1.04, coats drifting 2× the wall. Nothing touches the phone. | **E2 ring 1 6.0–7.0, E2b ring 2 7.6–8.6**: a foraged telephone bell, low-passed (~2.5 kHz), −8 dB, room reverb, heard *from his room through the wall* | 29, 44, 47 |
| **S3 REFUSE** | 8.5–11.5 | **LoC 2017862340** (Bubley 1943), cropped from master TIFF `8d33583u.tif`: head and shoulders against the pale wall, the black jamb at right, his flash shadow on the wall. Planes: far = wall; shadow plane (his cast shadow, cut as its own piece and graded with the wall); figure = GrabCut head piece and torso piece; near = jamb (occludes). The glide settles to rest by 10.5. **E3 ring 3 9.0–10.0:** at 9.25 the head piece turns 3° toward frame left (the sound) and the shadow plane follows with the parallax-correct offset. It holds; he does not reach (refusal). It returns at 10.4 (changed state). The woman at the plate's left edge is cropped out. | ring 3 9.0–10.0 (same treatment), then room tone | 29, 44, 47 |
| **S4 HELD (SIL-H)** | 11.5–19.0 (7.5 s) | The same plate and rig, cut closer (head ≥ 0.42 of frame height), composed to the reference's layout: pale wall in the left 40 %, head on the boundary, shadow and jamb dark at right. No camera move. Default: nothing moves. Branch `HELD-breath`: the torso piece rises ≤ 1.5 px per 4 s cycle (flagged invented secondary motion). | **room tone only**: non-zero, steady, no transient | 44 (held), 47 (silence animates thought) |
| **S5 FLIGHT 1** | 19.0–24.5 (132 frames) | **LoC 2017811447** (Vachon 1940), a man going upstairs in profile, plaid coat over his arm. GrabCut figure with the coat as an attached piece. The wall behind him is rebuilt by patch-copying the plate's own wallpaper (invented extension, mask exported). Planes: far = wallpaper and newel; mid = treads; figure; near = banister and balusters (occlude the legs). Medium framing, head ≥ 0.18 of frame. Empty stair 19.0–20.5. **E4: enters lower left at 20.5 and climbs along the measured stair line. Footfalls at 20.8, 21.35, 21.9, 22.45 and 23.0 each give a 3 px dip and recovery. He exits upper right at 23.5.** Empty 23.5–24.5. Small lateral glide; banister ≥ 1.5× wall. Graded on the harder curve. | foraged footsteps on a wooden stair, each footfall placed at its ledger time (not stretched), closer and drier than the bell; room tone | 29, 44, 47 |
| **S6 STAIRWELL** | 24.5–27.0 | **LoC 2017714056** (Mydans 1935), a rooming-house stairwell looking up, empty; already bimodal (p50 27). Rebate cropped. Planes: near = lower banister and newel; mid = flights; far = ceiling. Slow upward tilt, near fastest. | two footfalls from the same recording, −12 dB with more reverb (above, further), then room tone | 44 |
| **S7 FLIGHT 2 + TAIL** | 27.0–35.0 | 27.0–32.5: **S5's 132 frames reused byte-identically**. E6 enters 28.5, footfalls 28.8–31.0, exits 31.5. 32.5–35.0: S5's last frame held (empty stair), with no edit after D. | the same footstep cues and mix as S5, then room tone to the end | reuse (invariant 5) |

**Voice takes.** HANDMADE captions in one band, set per §0. Strings and durations are identical in both tracks; times come from beats-r2.

| clause | text | event (t_on) | A_ahead | B_behind | relation A / B |
|---|---|---|---|---|---|
| c1 | You open your eyes. | E1 2.0 | 0.8–2.0 | 3.2–4.4 | anticipates / lags |
| c2 | You hear it through the wall. | E2 6.0 | 4.8–6.05 | 7.2–8.45 | anticipates / lags |
| c3 | You do not answer. | E3 9.0 | 7.8–9.0 | 10.2–11.4 | anticipates / lags |
| — | (none) | SIL-H 11.5–19.0 | — | — | leaves_silence |
| c4 | You take the stairs. | E4 20.5 | 19.3–20.6 (empty stair) | 21.7–23.0 (body visible) = **Bl** | anticipates / lags + overlaps |
| c5 | You take the same stairs again, one step after another. | E6 28.5 | 27.3–30.1 | 29.7–32.5 (body gone at 31.5) = **D** | anticipates / lags past exit |

**Elements, FORAGED or HANDMADE**

- **FORAGED, Library of Congress** (tile.loc.gov; re-verify `rights_advisory` = "No known restrictions" from each `?fo=json` record):
  - 2017862333 (master TIFF), 2017862340 (master TIFF), 2017735081, 2017811447 and 2017714056, as 1024 px JPEGs except the two TIFFs.
  - Reserves: 2017811448 (the same stair, alternative pose), 2017862354 (a man in a dark hall by a wall lamp, also Bubley; a chiaroscuro alternative for S3/S4), 2017735082, 2017714055.
- **FORAGED sound:**
  - The Moving Image Archive cache comes first (`forage.py` with `--media clip`). Queries: `room|interior|quiet|night|apartment|hotel|bedroom`, `telephone|ring|bell`, `stair|steps|footstep`. LISTEN to every candidate and accept only speech-free, music-free stretches from items whose page or title is not marked copyrighted. Credit with the movingimagearchive best-supported status. Candidate leads for interior hush: 491529e4 *Door to Heaven* (1941) and db4a7675 *Alcohol and the Human Body* (1949). Listen first.
  - Commons comes second (extmetadata licence). Leads re-usable from r0, to re-verify: "Model 500 Telephone British ring" (CC BY-SA 3.0), "Wooden stairs (Gravity Sound)" (CC BY 4.0), "TU Delft Library quiet study room" (CC BY 3.0). Prefer a magneto or wall-phone bell matching the crank phone if Commons has one.
- **HANDMADE:** the two cards; caption typography; cutout rigs, plane splits, grade curves and camera paths built from the foraged negatives. Every invented fill is listed.

## 7. Animation technique SCIONs (prompts read in full in `paeleo/scion/swarms.json`)

| id | title | why this film | applied in |
|---|---|---|---|
| **29** | GrabCut — Cutout Extraction Swarm | The bodies exist only inside 1936–1943 negatives, and the proof needs a body that rouses, turns its head and climbs. Uses the photograph preset by scan class: silver grain is not body texture. | S1 (head H and hand K, fingers retained), S2 (coats, fur-collar matte), S3/S4 (head, torso, **cast-shadow plane**, jamb), S5/S7 (climber plus attached coat; banister and balusters as the near piece) |
| **44** | Multiplane Parallax — Spatial Collage Swarm | The camera must stay outside the man yet feel bodily present. Real planes cut from each negative, with near moving more than far, give the observer a position that never takes his eyeline. Occlusion carries the "outside" stance. | glides in S1, S2, S3, S5/S7; the tilt in S6; S4 is the same rig deliberately at rest. Dramaturgical planes: jamb = *confine*, banister = *shield*, empty stair = *distant witness*, cast shadow = *double* |
| **47** | Sound-to-Action — Viseme and Gesture Swarm | This is the prompt's own source anchor ("use the timecoded voice track as a performance score"). Its hard proof, a portrait that "hears an unseen object fall, then chooses not to answer", *is* this film's telephone beat. | ring 3 → head turn at +0.25 s → hold → return (attention → intention → refusal → changed state); footfalls → step dips; the viseme set is declared empty (mouth closed, no flapping in silence); SIL-H as silence that animates thought; sonic perspective fixed in his room |

Rules kept from those prompts:
- **29:** no background islands, fingers retained, halos isolated, transparent output truly separated, failure masks exported. Each piece is an RGBA file with an original-coordinate transform and a manifest entry.
- **44:** near ≥ 1.5× far, coherent occlusion, no foreground stretching, invented extensions flagged with masks.
- **47:** mouth closures (none, since he never speaks), gesture relates to thought, cue and reaction appropriately spaced.

Fallback, kept as a named branch and not a chosen SCION: if the rigid head-piece rotation in S1/S3 shows a seam at normal size, U1 may replace it with a small ARAP warp (SCION-34 method) under the same handles. It records the branch.

## 8. Swarm units (prompt §5; coupled tasks merged; the editor and the independent viewer run separately)

| unit | prompt §5 role(s) | mode | inspectable output | media saved under |
|---|---|---|---|---|
| **U1 picture** | camera/drawing team, the quiet observational cut (SCION-29 extraction, 44 staging, 47 body actions, §0 aesthetic grade) | forage + handmake | `u1-picture-ledger.json`: plates (LoC IDs, verified rights, TIFF/JPEG used, crop boxes), grade curves, layers (mask paths, z, parallax ratios, invented-fill masks), camera paths, measured event frames, figure-alpha coverage per frame for S5/S7, SHA-1 list proving S5 == S7, the same-sitter check (2017862333 vs 2017862340), budget record. Also `u1-contact.jpg` and `u1-aesthetic-compare.jpg` (one frame per shot beside the reference, with measured p1/p99/bimodality/chroma printed under each). | `films/sources/un-homme-qui-dort/u1-picture/` (raw/, rgba/, masks/, failure_masks/, fills/, shots/S1..S7 PNG sequences) |
| **U2 sound** | sound editor: distance, breath, withheld cues | forage | `u2-sound-ledger.json`: sources and licences (MIA first, then Commons), stems with in/out and gains, sonic-perspective declaration, SIL-H measurement (RMS floor, max transient), and a statement that no speech or music is audible | `films/sources/un-homme-qui-dort/u2-sound/` (48 kHz wav stems; one pass mix) |
| **U3 voice + referents** | voice writer and referent checker, coupled on one ledger; the checker step runs after reading U1's measured events | handmake | `u3-clause-ledger.json` (clauses, referent tags, bind relations per track), `takeA.srt`, `takeB.srt`, `u3-gate.py` (pure-Python gate with the three counterexamples), `u3-referent-audit.json` (gate output against U1's measured frames), `u3-caption-proof.png` (caption setting over S4 and S5 frames) | `films/sources/un-homme-qui-dort/u3-voice/` |

All units use beats-r2 times, so they run in parallel. U1 must deliver events on those frames. U3 re-audits against U1's measured values; a mismatch means quarantine and a beats revision, never a silent shift.

## 9. Acceptance bar (falsifiable: watch the render and read the ledgers)

1. **Structure.** The film runs 72.0 ± 0.2 s: two 35.0 s passes, each after a ~1 s card. The pre-caption picture and non-voice sound of pass I equal those of pass II (frame hashes and stem list). S5 equals S7 27.0–32.5 (SHA-1).
2. **Proof actions, seen.** In each pass the viewer sees the man's head lift off his hand (E1), and hears three rings while nobody answers: his head turns toward the sound, holds, and returns, with his wall shadow following. The viewer sees the same stair flight twice. No shot is from his POV, and his gaze never meets the lens.
3. **Grammar.** Tracks A and B have the same five strings in the same order with the same durations, all second person with addressee "you:A1". `u3-gate.py` passes them and rejects "He hears it through the wall." (output recorded).
4. **Timing.** Every A onset = event − 1.2 ± 0.05 s and every B onset = event + 1.2 ± 0.05 s, measured against U1's measured event frames.
5. **Silence and the defining beat.**
   - SIL-H (11.5–19.0) has no caption on any frame in either pass. Its audio has a non-zero floor and no transient more than 6 dB above it.
   - In pass II, c5 is visible on ≥ 0.8 s of zero-figure-alpha stair frames. c4 lies wholly within the figure-visible interval.
   - In pass I, c4 and c5 begin on empty-stair frames.
6. **Aesthetic, side by side (measured).** `u1-aesthetic-compare.jpg` and the editor's re-run on final frames place the S4 frame at pass time 15.0, and one frame of every other shot, beside `sommeil.webp`. Every frame has mean chroma ≤ 1.5 and L p1 in 20–40 and p99 in 236–250. The S3/S4 frames have (fraction below 60) + (fraction above 220) ≥ 0.55, with each part within ± 0.12 of the reference (0.42 / 0.33). No frame shows kit grain, a vignette, a negative rebate or a cream tone.
7. **Aesthetic, side by side (perceptual + framing).** A fresh critic shown the S1, S3 and S4 frames beside the reference judges them the same photographic family:
   - hard flash or window key;
   - a pale wall against a deep dark mass;
   - one anonymous head close enough to read skin and hair;
   - a dark double (cast shadow) beside it.

   Measured head height is ≥ 0.35 of frame height in S1 and S3, and ≥ 0.42 in S4 (reference 0.48), cropped from the LoC master TIFFs (crop boxes in the ledger). The critic also confirms that the close-ups are not upscaled from 1024 px JPEGs.
8. **The animation is real, and the material is credited.**
   - The figures are GrabCut cutouts from the named LoC negatives (RGBA and masks on disk) that visibly move: the lift, the head turn with the shadow following, and the climb with step dips.
   - In every glide near ≥ 1.5× far, and the banister occludes the climbing legs. Invented fills are listed with masks.
   - Every foraged image and sound appears in `films/credits/un-homme-qui-dort.json` with an accepted licence. No speech or music is audible anywhere.
