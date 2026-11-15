# SCION plan · Un homme qui dort · "Second-person voice"

Director's plan, rebuilt from scratch at revision `plan-r1` (2026-11-15).
Inputs read: prompts/un-homme-qui-dort.md (sections 1–10 and anchors), films/BRIEF-2.md,
films/kit.py (API only, not edited), catalogue/cinema.json (id 2), assets/references/sommeil.webp,
the earlier script/notes/credits and the nine LoC files already in films/sources/un-homme-qui-dort/.

The earlier version used a "rendered clip" of a figure and a synthesized murmur. Any drawn
figure is a style costume and is withdrawn. Its LoC photographs (Esther Bubley, Washington
boardinghouse, 1943) are kept only as candidates.

The reference (sommeil.webp) is a black-and-white photographic still of the actor beside a
mirror that doubles his back: the source is photographic cinema of one anonymous young man
in one small room. So this film FORAGES real photographs of real lodgers in real
boardinghouses (FSA/OWI, Library of Congress, public domain) and real recorded sound
(Commons). The only HANDMADE things are what the proof itself needs: the second-person
clause text (the voice, as captions), the two timed caption takes, the take cards, and a
small score strip. No still from the 1974 film is used. No filters, grain, vignette or
tinting go over any photograph.

---

## 1 · Creative thesis

A voice that says "you" claims whoever is in its path. The image can keep showing someone
else, from outside. Make the spectator feel addressed while an anonymous lodger stays
available to look at. The two must separate in one interval that the viewer can see and
hear: the voice says "You take the stairs" while the camera is watching an empty
stairwell from a place the lodger never stands.

The film has one 35-second picture, shown twice. A lodger wakes in a boardinghouse bunk,
lets a hall telephone ring, takes a staircase, the room is held empty with only room sound,
he takes the identical staircase again, and the house is seen from the street at night.
The same seven second-person clauses run in both passes:
- **Take A**: each clause starts 1.2 s *before* the action it names (anticipates).
- **Take B**: each clause starts 1.4 s *after* that action (lags).

Picture, words and sound are identical in both takes. Only the voice onsets move.

## 2 · Defining beat and comparison baseline

**Defining beat: STAIR-2, picture time 24.0–30.0 s (film 25.5–31.5 in Take A,
62.0–68.0 in Take B).** The staircase clip is frame-for-frame the clip already seen at
12.0–18.0. It starts on an **empty** stairwell (24.0–25.4), cuts to the lodger on the stair
(25.4–27.4) and ends on an empty stairwell (27.4–30.0).
- Take A: "You take the stairs." is on screen 24.2–25.8, almost all of it over the empty
  stairwell, *before* anyone is there.
- Take B: the same words are on screen 26.8–28.4, landing as he leaves and staying over
  the empty stairwell *after* he is gone.

In both takes "you" sits on an image with no body in it, seen from a camera position the
lodger does not occupy. The viewer is the only one "on" the stairs. It is the second time
the identical clip and the identical words have appeared, so the viewer can tell the
difference is timing, not content.

When it succeeds, the viewer can point to:
1. The caption over an empty stairwell, in each take (before him in A, after him in B).
2. The identical stair clip at 12.0 and 24.0, and the identical words.
3. A held shot just before it (18.0–24.0) with no words at all, only room sound, in both
   takes.

**Comparison baseline (`baseline.mp4`, rendered privately by the editor, not published).**
A conventional, synchronised voice-over on the same picture:
- third-person captions ("He opens his eyes", "He takes the stairs") placed exactly on each
  action (offset 0);
- an extra clause laid over the held shot ("He sits in the empty room"), so no
  voice-free passage;
- one pass only.

In the baseline the narration only duplicates what is visible and nobody is addressed. If
a fresh viewer finds the real cut no different from the baseline in who "you" lands on,
the beat has failed and section 8's repair runs.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Un homme qui dort*, Bernard Queysanne and Georges Perec, France, 1974; from Perec's 1967 novel. Black and white, about 77–82 min (**uncertain**). Spoken text in the second person singular ("tu"), read by a woman (Ludmila Mikaël, per common filmographies; **not verified here**) over a near-silent young man (Jacques Spiesser) in Paris. Waschneck (Screening OULIPO, intro p. 9) identifies the second-person narration. |
| source media | Feature film: photographed observation of one body, off-screen literary voice, a dense sound score. Exact production details (gauge, sound team): **uncertain**, not used. |
| target media | 74.0 s digital study, 960×540, 24 fps, stereo, rendered with kit.py. One 35.0 s picture timeline shown twice with two caption takes. Ledgers beside it: clause/referent ledger (JSON), two SRTs, timed silence map, picture and sound ledgers, credits. |
| preserved relation | A voice addresses "you" while the image observes a solitary, nearly mute man from outside. Address and observation are separate tracks that can drift apart. |
| optics change | No moving camera. Real 1941 FSA/OWI photographs of lodgers in boardinghouses (John Vachon, Radford, Virginia; Carl Mydans, Washington, D.C.; Bubley 1943 as reserve), cut as a sequence of stills, each framed from outside the subject's viewpoint. The lodger is anonymous and not Perec's character. |
| formalism change | Each clause is a typed record (addressee, person, predicate, interval) bound to an observed event ID with a declared relation (anticipates / overlaps / lags / silence). The same words are re-timed into two takes against a frame-identical picture. |
| concept change | The address is split into a measurable timing variable. The film shows that the same words make an anticipatory timeline and a retrospective one, and that "you" can land on an empty place. |
| sound change | No spoken voice (no TTS; the 1974 voice is not used): voice = captions. Foraged real recordings: telephone ring, footsteps on wooden stairs, room tone, night street. Ring heard "through the wall" by distance (level, low-pass), and a held room-tone-only passage. |

**Formation epochs (weight 0–100, reason):**
- **Second-person novel, 1957–1967** (Butor, *La Modification* 1957, "vous"; Perec's novel
  1967, "tu"). Weight 90. This is the grammar the whole proof tests.
- **Literary voice-over essay cinema, 1955–1970** (Resnais/Duras, Marker). Weight 55. An
  off-screen literary voice with independent timing. Direct influence on Queysanne is
  **uncertain** (inference).
- **Oulipo constraint practice, 1960–** Weight 45. Perec's membership is documented. Whether
  the film's form is itself a constraint is **uncertain**, so it is weighted below the
  grammar.
- **FSA/OWI documentary photography, 1935–1944.** Weight 35. This is the foraged optical
  layer, not the source's: anonymous observed lodgers in rented rooms. Its affinity with
  Perec's furnished room is the production's choice, not a historical claim.
- **Sound-to-action timecode scores** (SCION 47). Weight 40. The voice track is used as a
  performance score that the picture is bound to.

### 3.1 Olog (types and arrows)

Types (boxes):
- `AddressClause`: `{clause_id, text, addressee_id, person ∈ {1,2,3}, predicate, onset, offset, take ∈ {A,B}}`
- `ObservedAction`: `{event_id, subject_id, predicate, onset, obs_start, obs_end, shot_id}`
- `Shot`: `{shot_id, source_id, crop, camera_viewpoint, subject_in_frame ∈ {yes,no}, start, end}`
- `Narrator`: `{narrator_id = N1, embodied = false, on_track = captions}`
- `Performer`: `{subject_id = P1 "the lodger", source_ids[], same_person_verified ∈ {yes,no,unknown}}`
- `AudiencePosition`: `{viewer_id = V, seat = "in front of the screen"}`
- `Relation`: `{anticipates, overlaps, lags, silence}`
- `SilenceSpan`: `{span_id, start, end, heard = [room tone ids], clauses = []}`
- `DiegeticSpeech`: its own track, declared **empty** (no one speaks; the phone is not answered).

Arrows:
- `AddressClause --spoken_by--> Narrator`
- `AddressClause --addresses--> addressee_id`. Declared addressee for the whole work:
  `ADDR-1 = "you"`, ambiguous between P1 and V by design. There is no marked shift
  anywhere.
- `ObservedAction --performed_by--> Performer`
- `ObservedAction --seen_in--> Shot --seen_from--> camera_viewpoint`
- `[bind] : AddressClause × ObservedAction → Relation`
- `SilenceSpan --contains_no--> AddressClause`

Distinct fields that must never be merged:
- `camera_viewpoint`: always "across the room / below or above the stair / across the
  street";
- `narrator`: N1, off-screen;
- `performer`: P1;
- `audience_position`: V.

A shot is rejected if `camera_viewpoint == eyes(P1)`.

### 3.2 Central operation `[bind]`: typed preconditions

`bind(c: AddressClause, a: ObservedAction, take) -> Relation` is legal only if all of these
hold:
1. `c.person == 2`, and `c.text` matches the grammar gate: subject "You", or imperative
   2nd person, and no he / she / him / his / I / we narrating.
2. `c.addressee_id == ADDR-1` (no shift is declared).
3. `a.event_id` exists in the beat ledger; `a.subject_id == P1`, or the event is a sound
   event of the place (ring) observed while P1 is in frame or absent.
4. `a.shot_id`'s `camera_viewpoint != eyes(P1)`.
5. `c.text` is identical string-for-string in take A and take B for the same `clause_id`.
6. The relation is computed, not asserted. Let `d = c.onset − a.onset`:
   - `anticipates` if `d ≤ −0.5`;
   - `overlaps` if `|d| < 0.5`;
   - `lags` if `d ≥ +0.5`.

   Take A requires every clause to be `anticipates` (d = −1.2 ± 0.1). Take B requires every
   clause to be `lags` (d = +1.4 ± 0.1).
7. `[c.onset, c.offset]` does not intersect any SilenceSpan (held shot 18.0–24.0) and lies
   inside `[0, 35.0]`.
8. Picture frames of take A and take B are identical. The editor asserts per-frame equality
   of the rendered pictures, or the sha256 of the picture layer.

### 3.3 Observable consequences
- In Take A the viewer reads each line just before the thing happens: "You open your eyes"
  over black before the bunk appears, and "You take the stairs" over an empty stairwell
  before the lodger is there.
- In Take B each line confirms something already seen. The second "You take the stairs"
  lands as he leaves, and stays on the emptied stairwell.
- In both takes 18.0–24.0 has no caption, and only room tone can be heard (RMS of the
  ring/steps stems = 0 in that span).
- Stair-1 and stair-2 are identical clips. Identical words are bound to them.
- The ledger's `relation` column reads 7× `anticipates` for A and 7× `lags` for B, with no
  `overlaps`.

### 3.4 Counterexample (what `[bind]` must refuse)
- **Grammar.** "He hears it through the wall." (person = 3) fails gate 1. This is the
  section 7 fixture. The clause is quarantined and the take is not rendered.
- **Silence.** Moving Take A's C5 onset from 24.2 to 23.4 (so it starts over the held
  room) fails gate 7. It invalidates the sound editor's silence-map review, so both
  tracks are re-reviewed.
- **Viewpoint.** Using a photograph taken from the stair-top looking down "as if his eyes"
  (labelled POV) fails gate 4.
- **Collapse.** Placing C4 at d = 0 fails gate 6 for both takes. It yields `overlaps`, which
  is the baseline's behaviour, not the proof's.

The passing fixture is "You hear it through the wall." (person 2, ADDR-1, interval 5.2–6.8
in A / 7.8–9.4 in B), bound to E2 (ring onset 6.4). The same words validly produce an
anticipatory timeline (A) and a retrospective timeline (B).

### 3.5 Replay and alternate views: equivalent vs divergent
- **Equivalent:**
  - the picture of Take A = the picture of Take B (frame-identical);
  - STAIR-1 = STAIR-2 (frame-identical);
  - the clause texts of A = those of B;
  - the sound bed of A = that of B (same stems, same onsets);
  - replaying a take reproduces it exactly (deterministic render, fixed seed).
- **Divergent:**
  - the `relation` column (anticipates vs lags);
  - which image each word lies over (e.g. C1-A over black, C1-B over the bunk);
  - whether "You let it ring" precedes or follows the unanswered second ring;
  - C3-B crossing the 12.0 cut into the stairwell. That is a declared lag property. It is
    not an edit moved across an address boundary, because no clause boundary is edited.
- **Named branches (non-commuting, kept, not merged):**
  - `stair-gaze`: Vachon 2017811448, where the lodger looks into the lens, used in place of
    2017811447. It may collapse the camera into the addressee. It is not in the main cut
    and is kept for the section 8 distance/gaze comparison.
  - `held-body`: the held shot showing a seated lodger (full 2017811431) instead of the
    empty-bed crop.
- **Interactive:** none (screen work). TTL 2; theory not skipped.

## 4 · Invariants (hard; a breach quarantines the candidate)
1. Every narrative clause is second person (gate 1). There is no third-person or
   first-person narration anywhere, including the cards.
2. Diegetic speech is on its own track. That track is declared empty, and no caption
   pretends to be the lodger's or a caller's speech.
3. The addressee stays ADDR-1 throughout. No marked shift.
4. Voice-free held shot: picture 18.0–24.0 (6.0 s ≥ 5.0 s) in both takes. Only room
   tone, with no ring, steps or captions. The full voice-free runs are 13.8–24.2 (A) and
   16.4–26.8 (B).
5. The camera never takes P1's viewpoint. Every shot records its `camera_viewpoint`.
6. Image and narration fork from one beat ledger (section 5 IDs). A voice onset may not
   move across 18.0 or 24.0, and an edit may not move across a clause boundary, without
   re-review of the other track.
7. All material is FORAGED (LoC/Commons, PD/CC0/CC BY/CC BY-SA, read from metadata) or
   HANDMADE (text, cards, strip). No filters, faux grain, vignette or kit `paper()` grain
   over photographs, and no drawn figures. Photographs are pillar/letter-boxed in black at
   their true aspect, and may be cropped and reframed.
8. Sources are immutable: each is identified by its LoC/Commons ID and sha256 of the
   downloaded file. Each unit records owner, base revision (`plan-r1`), read/write sets
   and changed fields.

## 5 · Fixed IDs (shared by all units so they can work in parallel)

**Picture sources** (all FSA/OWI at LoC, "No known restrictions", US government work, PD;
U1 re-verifies):

| ID | LoC item | description |
|---|---|---|
| P-BUNK | 2017811426 | John Vachon, "W.W. McDaniel, rigger at Hercules powder plant, in his bunkhouse in the rear of Mrs. Pritchard's boardinghouse. Radford, Virginia". A man lies in bed, eyes open, wooden walls. |
| P-STAIR-MAN | 2017811447 | Vachon, untitled, related to "Powder plant employee going upstairs. Mrs. Pritchard's boardinghouse". A man on the stair in profile, carrying a coat. |
| P-STAIR-GAZE | 2017811448 | Vachon. Same man, looking at the lens. Branch only. |
| P-STAIR-EMPTY-1 | 2017714056 | Carl Mydans, untitled, related to "Stairway in rooming house, Washington, D.C.". An empty stairwell. |
| P-STAIR-EMPTY-2 | 2017714055 | Mydans, "Stairway in rooming house, Washington, D.C.". An empty stairwell seen from above. |
| P-ROOM | 2017811431 | Vachon, "Powder plant's construction worker in his bedroom at Mrs. Pritchard's boardinghouse". Crop to the empty beds and chair, excluding the seated man. |
| P-HOUSE | 2017811432 | Vachon, "Crowded boardinghouse with cars parked outside. Radford, Virginia". The house at night. |
| P-TEL | TBD by U1 | A wall telephone with no one at it: LoC FSA/OWI or Commons PD/CC. Reserve: crop of Bubley 2017862346 to the wooden phone box only. |
| P-WAKE-2 | TBD by U1, optional | A second frame of the same bunk/man at another moment, if one exists. |
| reserves | 2017862344 / 2017862333 / 2017862354 / 2017862359 | Esther Bubley, Washington 1943. |

**Performer.** P1 = "the lodger": P-BUNK, P-STAIR-MAN.
`same_person_verified = unknown`. The two Vachon frames may show different men. This is
recorded as montage-constructed identity, and the voice never names him.

**Sound sources** (U2 finds them on Commons):

| ID | sound |
|---|---|
| S-RING | Real electromechanical telephone ring (bell ringer), ≥ 2 bursts. |
| S-STEPS | Footsteps on wooden stairs, about 3.5 s, one direction. |
| S-ROOM | Interior room tone, ≥ 12 s, without voices (a quiet radiator or distant traffic through glass is acceptable). |
| S-STREET | Night street ambience, ≥ 5 s, no speech. |
| S-BED | Optional: bed creak or bedding movement, ≤ 1 s. |

**Events (picture timeline, seconds):**

| ID | time | event |
|---|---|---|
| E1 | 1.5 | Wakes: the bunk shot appears out of black, eyes open. |
| E2 | 6.4 | Telephone ring onset (burst R1). |
| E3 | 9.4 | Ignores the ring: second ring burst R2 while P1 lies unmoved; observed 8.5–12.0. |
| E4 | 13.4 | Takes the stairs: P1 appears on the stair in STAIR-1. |
| E5 | 18.0–24.0 | Held silence (SilenceSpan SIL-1). No event and no clause. |
| E6 | 25.4 | Takes the stairs: P1 appears on the stair in STAIR-2 (identical clip). |
| E7 | 30.0 | Outside: cut to the house from the street; P1 not visible. |
| E8 | 32.0 | Ring heard once more, faint, from inside the house (R4). |

**Clauses** (identical words in A and B; caption duration 1.6 s; A = event −1.2, B = event
+1.4):

| ID | text | event | Take A | Take B |
|---|---|---|---|---|
| C1 | You open your eyes. | E1 | 0.3–1.9 | 2.9–4.5 |
| C2 | You hear it through the wall. | E2 | 5.2–6.8 | 7.8–9.4 |
| C3 | You let it ring. | E3 | 8.2–9.8 | 10.8–12.4 |
| C4 | You take the stairs. | E4 | 12.2–13.8 | 14.8–16.4 |
| C5 | You take the stairs. | E6 | 24.2–25.8 | 26.8–28.4 |
| C6 | You are outside. | E7 | 28.8–30.4 | 31.4–33.0 |
| C7 | You do not go back. | E8 | 30.8–32.4 | 33.4–35.0 |

U3 may revise the wording (still second person, ≤ 7 words, with the same events and the same
offsets). It may not move offsets. "You hear it through the wall" is fixed: it is the
section 7 fixture.

## 6 · Timed shot list: Hard proof (35.0 s picture), film total 74.0 s

Film timeline:
- 0.0–1.5: card A (HANDMADE).
- 1.5–36.5: Pass A, the picture with Take A captions.
- 36.5–38.0: card B (HANDMADE).
- 38.0–73.0: Pass B, the identical picture with Take B captions.
- 73.0–74.0: end card (HANDMADE).

Times below are picture time `p`. The film time is 1.5 + p in Pass A and 38.0 + p in
Pass B.

**Card A, film 0.0–1.5 (HANDMADE).** Black ground, kit serif: "TAKE A · the voice comes
first". Heard: S-ROOM fades in under the last 0.5 s.

**SH1 · BLACK → BUNK, p 0.0–6.0.**
- 0.0–1.5: black, a declared darkness and not a filter. Heard: S-ROOM, low.
- 1.5–6.0: P-BUNK (FORAGED, LoC Vachon), full frame pillar-boxed, seen from the foot of
  the bed across the bunkhouse. `camera_viewpoint` = across room; P1 in frame. A very slow
  reframe (crop scale 1.00→1.04) is allowed; no effects. E1 = 1.5.
- Heard: S-ROOM; optional S-BED at 1.6.
- Captions: C1 (A 0.3–1.9 over black, before the image; B 2.9–4.5 over the bunk).

**SH2 · TELEPHONE, p 6.0–8.5.** P-TEL (FORAGED): a wall telephone in a hall with no one
at it; `camera_viewpoint` = hallway, P1 not in frame.
- Heard: S-RING burst R1 at 6.4, full level; this insert is where the ring is.
- Captions: C2 (A 5.2–6.8 starts over the bunk and crosses into the phone; B 7.8–9.4).

**SH3 · BUNK, UNMOVED, p 8.5–12.0.** P-BUNK in exactly the same framing as SH1's end. He
does not move, because it is the same photograph. The stillness is the observed action
"ignores". E3 = 9.4.
- Heard: S-ROOM, plus S-RING burst R2 at 9.4 heard "through the wall": about −12 dB and
  low-passed about 2.5 kHz by U2.
- Captions: C3 (A 8.2–9.8; B 10.8–12.4, running 0.4 s into SH4).

**SH4 · STAIR-1, p 12.0–18.0. The STAIR clip, 6.0 s, prepared once by U1 as a frame list
or rendered clip:**
- 0.0–1.4: P-STAIR-EMPTY-1, empty stairwell.
- 1.4–3.4: P-STAIR-MAN, the lodger on the stair, seen from below and to the side.
- 3.4–6.0: P-STAIR-EMPTY-2, empty stairwell from above.

`camera_viewpoint` = below/beside or above the stair, never his. Place = a montage of
two rooming houses, declared as `place_id PL-STAIR, continuity constructed`. E4 = 13.4.
- Heard: S-STEPS 13.2–16.6, as if from the stair. S-RING R3 at 12.4, faint (−18 dB), the
  last ring; the ring stops after 14.4.
- Captions: C4 (A 12.2–13.8 over the empty stair → lodger; B 14.8–16.4 over the lodger →
  empty stair).

**SH5 · HELD ROOM, p 18.0–24.0 (6.0 s). SIL-1, voice-free in both takes.** P-ROOM cropped
to the two empty iron beds and the chair with clothes. The seated man is excluded. If he
cannot be fully cropped out, use branch `held-body`, P1-equivalent, and record it.
Locked frame, no reframe.
- Heard: S-ROOM only, at a slightly closer level (+3 dB) so the room is heard as a place.
- No captions.

**SH6 · STAIR-2, p 24.0–30.0.** The STAIR clip again, frame-identical to SH4 (same file,
same frames). E6 = 25.4.
- Heard: S-STEPS, the identical stem at 25.2–28.6; no ring.
- Captions: C5 (A 24.2–25.8 over the empty stairwell before he appears: **defining beat**;
  B 26.8–28.4, as he leaves and then over the emptied stair).

**SH7 · HOUSE FROM THE STREET, p 30.0–35.0.** P-HOUSE (FORAGED, LoC Vachon), the
boardinghouse at night with cars, from across the street. P1 not visible. E7 = 30.0.
- Heard: S-STREET. S-RING R4 at 32.0, very faint (−24 dB, low-passed), from inside the
  house: a withheld cue that no one answers.
- Captions: C6 and C7 (A 28.8–30.4, which starts over the empty stair end of STAIR-2, and
  30.8–32.4; B 31.4–33.0 and 33.4–35.0).

**Card B, film 36.5–38.0 (HANDMADE).** "TAKE B · same picture, same words, the voice comes
after". S-ROOM continues.

**Pass B, film 38.0–73.0.** Identical picture and sound; Take B captions.

**End card, film 73.0–74.0 (HANDMADE).**
"Photographs: John Vachon, Carl Mydans (FSA/OWI, Library of Congress, public domain).
Sounds: Wikimedia Commons (see credits)."

**HANDMADE score strip.** A 14-px band in the black letterbox above the photograph, never
over it:
- event ticks (E1–E8) and clause bars for the current take, in ACCENT;
- the SilenceSpan drawn as an empty bracket labelled "room only".

It is the same in both passes except the clause bars. It makes the formal claim legible.

**Captions.** Kit serif in the bottom letterbox band, centred, with no speaker label
(narrator N1 is unembodied). A 0.15 s fade is allowed. A caption never covers the face or
the stair.

## 7 · Units (excluding the montage editor/assembler and the independent reviewer)

Every unit works from revision `plan-r1` and the fixed IDs in section 5. Every unit:
- reads BRIEF-2.md;
- downloads only from commons.wikimedia.org / upload.wikimedia.org / www.loc.gov /
  tile.loc.gov, with User-Agent `oulipo-film-research/1.0`;
- decodes media only with ffmpeg or PIL (`python3 -I`), and never executes anything from
  downloads;
- does not commit and touches no other film;
- keeps under 50 MB of downloads;
- records owner, base, read/write sets and changed fields in its output JSON.

### U1 · picture (FORAGE): camera team, "quiet observational cut"
**Task.**
- Re-verify every P-* item from the LoC item JSON (`?fo=json`): title, contributor,
  rights_advisory, file URL. Record sha256.
- Find P-TEL: an empty wall or hall telephone, from LoC FSA/OWI ("telephone",
  "boardinghouse telephone", "pay telephone hall") or Commons (PD/CC0/CC BY/BY-SA from
  extmetadata). If nothing is found, use the reserve crop of 2017862346 and record it.
- Search for P-WAKE-2: other Vachon Radford frames of McDaniel or the bunkhouse, or a PD
  Commons film of a man waking. Record what was tried and what is absent.
- Prepare 960×540 PNGs, black-boxed at true aspect with no filters, for SH1, SH2, SH3
  (identical to the end of SH1), SH5 and SH7.
- Prepare the 6.0 s STAIR clip as 144 PNG frames, or a lossless .mkv, with a sha256 per
  frame. Prove that the SH4 and SH6 use is the same file.
- For each shot fill in: shot_id, source_id, crop box, camera_viewpoint, subject_in_frame,
  subject_id, same_person_verified, start/end.
- Also prepare the `stair-gaze` branch clip (2017811448), labelled.

**Output.**
- `films/swarm/un-homme-qui-dort/picture.json`: sources with title, author, license,
  license_url, source_url, file_url, local_path, sha256; shots; stair clip frame hashes;
  searches and absences.
- Media in `films/sources/un-homme-qui-dort/picture/`.

**Budget:** ≤ 40 MB, ≤ 30 searches.

### U2 · sound (FORAGE): sound editor; distance, breath, withheld cues
**Task.**
- Find S-RING, S-STEPS, S-ROOM, S-STREET and optional S-BED on Commons audio (.ogg, .wav,
  .flac). Read the licence from extmetadata: PD, CC0, CC BY or CC BY-SA only.
- Decode to 44.1 kHz stereo WAV with ffmpeg, trim, and normalise the peak to −3 dBFS.
- Prepare the distance versions:
  - ring R1 full level;
  - R2 at −12 dB, low-passed about 2.5 kHz;
  - R3 at −18 dB;
  - R4 at −24 dB, low-passed (through the wall / from inside the house);
  - S-STEPS 3.4 s;
  - S-ROOM ≥ 36 s, or loopable without an audible seam;
  - S-STREET 5 s.
- Write the timed silence map for the 35.0 s picture: for every span, which stems sound.
  SIL-1 18.0–24.0 must be S-ROOM only. Measure the RMS per stem in SIL-1 (ring and steps
  must be 0).
- Write a mix cue list (stem, picture onset, gain, pan) that the editor feeds to
  `mix.add`.
- If a sound cannot be found, record the absence and propose a declared silence or kit
  synthesis, labelled as such. Never pass synthesis off as foraged.

**Output.**
- `films/swarm/un-homme-qui-dort/sounds.json`: id, title, author, license, license_url,
  source_url, file_url, local_path, sha256, duration, onset_s, use, gain, filter.
- `films/swarm/un-homme-qui-dort/silence-map.json`: spans, stems per span, measured RMS,
  cue list.
- WAVs in `films/sources/un-homme-qui-dort/sound/`.

**Budget:** ≤ 30 MB.

### U3 · voice and referents (HANDMADE): voice writer + referent checker, one owner, gate as code
**Task.**
- Finalise the seven clauses of section 5. They are original English text in the second
  person, not Perec's words. Tag each with clause_id, addressee_id ADDR-1, person 2,
  predicate, bound event_id and declared relation. Compute Take A/B onsets exactly from
  the event times (−1.2 / +1.4) and the 1.6 s duration.
- Write a grammar/referent gate script at
  `films/swarm/un-homme-qui-dort/gate.py` (plain Python, no imports from downloads). It
  takes the ledger and checks:
  - preconditions 1, 2, 5, 6 and 7 of section 3.2;
  - the fixtures: "You hear it through the wall" PASS; "He hears it through the wall"
    FAIL; the same words valid as anticipates (A) and lags (B); a C5-A onset moved to
    23.4 FAIL (silence).

  Run it and save the report.
- Write `takeA.srt` and `takeB.srt` on the **picture** timeline (0–35.0). Write a
  film-timeline SRT (`captions-film.srt`) with offsets 1.5 and 38.0.
- Write the baseline's third-person synchronised captions (`baseline.srt`). This file is
  labelled as baseline only, and the gate must FAIL it.
- Typeset the clause/referent ledger as a readable sheet (PNG, kit fonts) for the end
  card, if the editor wants it.

**Output.**
- `films/swarm/un-homme-qui-dort/clauses.json`: clauses, events, binds and relations per
  take, silence spans, the declared diegetic track (empty).
- `takeA.srt`, `takeB.srt`, `captions-film.srt`, `baseline.srt`.
- `gate.py` and `referent-audit.json`: the gate report with pass/fail per clause and
  fixture.
- The sheet in `films/sources/un-homme-qui-dort/voice/`.

**Budget:** text and code only.

### Run separately by the workflow (not assigned here)
- **Montage editor/assembler.**
  - Writes films/un-homme-qui-dort.py with kit.py from picture.json, sounds.json,
    silence-map.json and clauses.json.
  - Asserts section 3.2's preconditions in code, re-running gate.py's checks, plus
    picture-frame identity of the passes and of STAIR-1/2.
  - Renders the 74.0 s film and the private baseline.mp4.
  - Rewrites films/credits/un-homme-qui-dort.json (every foraged item, used_as) and
    films/notes/un-homme-qui-dort.txt (60–110 words, foraged vs handmade).
- **Independent viewer/reviewer.**
  - Watches once at normal speed. Marks when "you" lands on the lodger, the audience or
    both, what the body does while the voice is silent, and where narration only
    duplicates.
  - Then checks the acceptance bar and labels evidence measured / structurally verified /
    perceptually judged / unknown.

## 8 · Acceptance bar (falsifiable; checked by watching the render and reading the ledgers)
1. **Structure (measured).** The film is ≤ 75 s (target 74.0) and contains two 35.0 s
   passes. Their picture frames are identical, apart from the caption band and the
   clause bars of the score strip (pixel difference outside those bands = 0). The
   stair clip at p 12.0–18.0 and p 24.0–30.0 is frame-identical and shows a real
   photograph of a man on a staircase.
2. **Grammar (structurally verified).** Both SRTs contain the same seven clause texts,
   word for word. Every clause is second person, and gate.py passes them. There are no
   he/she/I narration lines anywhere in the film or cards. gate.py FAILS "He hears it
   through the wall" and the baseline SRT.
3. **Timing (measured).**
   - In Take A every caption onset precedes its event by 1.2 ± 0.1 s; in Take B every
     onset follows its event by 1.4 ± 0.1 s, per clauses.json and the rendered captions.
   - Visibly, Take A's "You open your eyes" appears over black before the bunk photograph,
     and Take A's second "You take the stairs" appears over an empty stairwell before the
     lodger does.
4. **Silence (measured).** Picture 18.0–24.0 has no caption in either pass, and its audio
   is S-ROOM only: ring and step stems are silent there per the silence map, and the
   ring is audibly absent.
5. **The ring is ignored, from outside (perceptually judged + structural).**
   - A real recorded telephone ring is heard at least twice, once at reduced level "through
     the wall".
   - The lodger's photograph does not change while it rings.
   - No shot is labelled or reads as his point of view: picture.json `camera_viewpoint`
     is never his eyes, and no frame is taken from where he lies or stands.
6. **Material (structurally verified).** Every image and sound appears in
   films/credits/un-homme-qui-dort.json with a PD/CC0/CC BY/CC BY-SA licence, author and
   source URL. No still or sound from the 1974 film is used. No drawn figure, filter,
   faux grain or vignette is applied over any photograph.
7. **Defining beat (perceptually judged).** A fresh viewer, after one viewing, can point
   to the moment where "you" sits on a stairwell with no one in it, seen from a place the
   lodger does not stand, and can say whether it landed on the lodger, on them or on
   both. If they cannot name any difference from baseline.mp4 in who is addressed, the
   bar fails.
