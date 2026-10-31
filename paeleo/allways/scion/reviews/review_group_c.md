# Independent written-spec review — SCION 95–113

## Scope and verdict

Reviewed all 19 written operator cores in `group_c.json`, IDs 95–113 inclusive, together with their lineage, source-audit, correction, primitive, invariant, proof, acceptance, automated-check, repair and deliverable fields. This is a review of prompt specifications. No operator was executed, no film was generated or accepted, no interactive prototype was tested, and no learned model was run. The review therefore establishes neither runtime correctness nor artistic success.

The specifications preserve substantial differences between these lineages and have no overall architectural blocker. Four targeted changes would make the written operating contracts more reliable. The first two affect the truth of what the finished prototype could report; the third fixes an implementation ambiguity; the fourth makes the intended boundary between automated checks and human evidence review explicit.

## Material findings

### 1. ID 104 — Separate capture density from editorial selection density

**Issue:** The proof asks for 24–40 selected photographs from a 45-minute documented activity, while the primitives and checks describe capture frequency and intervals when nothing was recorded. If the selected images are only a subset of the captured images, their density represents editorial selection, not the original recording process. An omitted capture is not a recording gap.

**Required change:** Preserve a complete capture manifest separately from the displayed/selected image set. Derive any graph labeled capture frequency from that complete manifest. If the full log is unavailable, label the graph selected-sample density and withhold claims that particular intervals were unrecorded. The interface should distinguish an interval with no source capture from one whose captures were omitted from the current view.

**Verification boundary:** Software can compare bins against the supplied complete manifest and distinguish displayed from omitted image IDs. It cannot establish that an incomplete source collection contains every image originally made.

### 2. ID 106 — Specify the session clock and distinguish opened from completed

**Issue:** The proof combines a 90-second budget, twelve short clips, an always-available pause, and a requirement that several links remain unexplored. Rapid clicking could open all twelve items. A pause that freezes only the countdown while permitting progression could also defeat the budget. The written spec does not yet define which behavior applies.

**Required change:** Define the budget as active experience time, with pause freezing both the countdown and media/navigation progression while preserving exit. Record opened, meaningfully played/completed, and unopened states separately. Supply more playable material than the budget if incompleteness is necessary to the proof, but report the visitor's actual states rather than guaranteeing that links stayed unopened. Keep the post-session quiet index untimed as already specified.

**Verification boundary:** A deterministic event trace can verify active time and accurate counts. Neither the count nor time spent establishes attention, understanding, or psychological effect.

### 3. ID 108 — Make drawing slots and output frames separate time-base concepts

**Issue:** The eight-second reference action has 48 drawing positions. The spec protects duration and synchronized sound, but leaves the mapping from those positions to output frames implicit. Treating the 48 drawing positions as 48 output frames at 24 fps would accidentally shorten the action to two seconds.

**Required change:** Assign each drawing slot a source timestamp. State the drawing cadence explicitly: 48 equally spaced slots over eight seconds is six drawings per second. Choose and declare output frame rate and holding/interpolation policy; for example, at 24 fps each drawing is held for four output frames. Alternative editions substitute drawings within the same source-time slots and retain the eight-second duration. Validate the rendered time mapping as well as slot coverage.

**Verification boundary:** This is a time-base clarification, not a request to increase drawing cadence. Limited animation is compatible with the operator. It also keeps this lineage's frame contribution distinct from ID 109's whole-shot contribution.

### 4. IDs 101, 102, 107 and 112 — Restrict automated checks to inspectable records

**Issue:** A few check labels are broader than their computable evidence. ID 101 says to check slot eligibility although some slot conditions are semantic. ID 102 resolves historical claims to source fields. ID 107 says to verify asset dates. ID 112 checks that factual assertions have supporting records. These checks can validate structure and correspondence, but a source field alone does not authenticate a date or demonstrate that a document actually supports a historical claim.

**Required change:** State that automation checks file/duration/orientation constraints, existing approval and review records, valid pointers, date formats and agreement with the supplied manifest. Assign semantic eligibility and source-to-claim support to an attributed curatorial/research review whose decision is recorded. Keep unknown dates unknown; do not promote metadata consistency to historical verification. ID 101 already prohibits fake match scores, so this clarification reinforces its existing invariant.

**Verification boundary:** No automated test should certify an image's emotional effect, a participant's mental state, historical truth, or therapeutic success. The other cores already avoid making those claims.

## Coverage and strengths

| ID | Reference | Written-spec assessment beyond the findings above |
|---|---|---|
| 95 | Bear 71 | Event time, visitor navigation and gaps in observation remain distinct; no invented continuous animal route. |
| 96 | BLA BLA | Gesture ownership, meaningful waiting and recovery to quiet states make the interaction plausible. |
| 97 | Welcome to Pine Point | Optional artifacts supplement a finite authored route; differing memories retain attribution. |
| 98 | One Millionth Tower | Proposed spatial changes retain authorship, constraints and reversibility; modeled clearance is not treated as community approval. |
| 99 | Out My Window | Voice context, one foreground speaker, orientation and return position are explicit. |
| 100 | A Short History of the Highrise | A complete linear argument survives optional expansion; saved playback and drawer return are coherent. |
| 101 | Motto | The contribution unit is a short semantic image slot with local preview, skip and removal states. |
| 102 | The Unknown Photographer | Evidence view, original photographs and authored fiction remain separable and reversible. |
| 103 | We Feel Fine | Authored expressions are not treated as validated emotions; categories, denominators and ambiguous cases remain visible. |
| 104 | The Whale Hunt | Filtering retains timestamps and distinguishes playback policy from source timing, subject to finding 1. |
| 105 | Cowbird | The protected contribution unit is a complete authored personal story, with relational links that do not dissolve authorship. |
| 106 | Network Effect | A finite corpus, actual route trace and untimed post-session index avoid invented global significance, subject to finding 2. |
| 107 | In Fragments | First-person material action and observed aftermath remain distinct from claims of healing or success. |
| 108 | The Johnny Cash Project | Contribution is a drawing in a fixed performance slot; honest single-maker studies and reproducible editions are specified. |
| 109 | Man with a Movie Camera: The Global Remake | Contribution is a whole shot occupying a declared score position; successful submissions are not automatically a successful film. |
| 110 | Sandy Storyline | Community accounts, later updates, disagreements and missing updates retain their own time and authorship. |
| 111 | 18DaysEgypt | The unit is an ordered participant evidence stream; capture, upload and recollection times are separated without false precision. |
| 112 | Prison Valley | Return hub, saved scene position and a notebook separating observation, quotation and inference are coherent. |
| 113 | Learning to See | Requires an actual documented trained model, paired input/output and measured delay; a scripted filter is explicitly insufficient. |

The participation units are therefore materially different: ID 101's semantic clip, ID 105's complete personal story, ID 108's drawing slot, ID 109's complete shot, ID 110's community account/update and ID 111's evidence stream should retain their distinct schemas. They should not be normalized into an undifferentiated contribution object during compilation.

ID 113 correctly permits clearly labeled playback of actual computed outputs when live inference is unavailable. It also limits a one-model proof to a single-prior study and marks the cross-prior comparison unavailable. The written spec does not silently replace the learned mechanism with visual resemblance or claim that a missing comparison was performed.

## Source and evidence limits of this review

Reviewed the source descriptions and correction boundaries supplied in all 19 records; this was not a fresh verification of every external source or every credited role. The independent spot-check of [Memo Akten's Learning to See page](https://memo.tv/projects/2017/learning-to-see/) confirms the 2017 series, actual neural-network reconstruction of live camera input, and availability of source/example pretrained models. That supports the mechanism required by ID 113, but does not prove any future implementation uses it.

A fresh request to the NFB catalogue page for The Unknown Photographer returned a server error during this review. That access failure is not evidence against the credited source record and does not establish a new metadata correction. Existing uncertainty notes, historical-version distinctions and legacy-access limits should remain in the compiled pack.

No Group C source file was edited by this review.
