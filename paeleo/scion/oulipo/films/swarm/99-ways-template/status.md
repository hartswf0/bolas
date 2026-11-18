# Status — 99-ways-template, r1 (editor, repair round 1)

## Current preview

| File | Notes |
|---|---|
| `assets/films/99-ways-template.mp4` | 72.5 s, 3.6 MB, 960×540 / 24 fps |
| `assets/films/99-ways-template.webp` | Poster from the S8 hold |
| `assets/pages/99-ways-template.png` | The page, 2550×3300 (tone: 47.0% L>220, 11.0% L<40) |
| Derivative pages | `-compressed.png` (40.0% / 18.8%), `-platform.png` (40.6% / 20.0%) |
| Reader cut | `films/swarm/99-ways-template/reader-cut.mp4`: the film trimmed before the S12 ledger (for the B2 fixture, amendment A-3) |
| Checkpoint | `checkpoints/r1/` (r0 kept) |

## Decisive review — what r1 changed against the r0 critic and rights review

- **Rights (blocking):** the P8 line, which was Madden's punchline word for word, is now "Now... what did I come over here for?" on the page, D1 C2 and the film (S8, S10). Amendment A-4 asks the operator to reword B1's quotation.
- **B1, P2:** the desk and chair are left empty, with only his shoulder at the right edge. The plate's head ghost, arm residue and desk smear are repaired with pixels of the same photograph (`editor/plate_repair.py`).
- **B1, P3:** rebuilt. The camera is on the closed double cupboard with no desk, inkwell or papers in frame. He stands, cut at the waist by the panel edge, pitched into the step, before the right leaf, which carries the SERVICE card clear of the lamp cord. The stray forearm is gone. In S3 he walks in from the left in 5 steps.
- **B2, P4:** nobody is behind the glass, so the asker is off-panel on the platform. His pencil hand is below the frame, so there is no wristwatch reading. His head tilts up toward the voice.
- **P5:** un-mirrored, so he faces the clock, head up.
- **B5, P8:**
  - He is un-mirrored, facing right, away from the key on the door at his left.
  - His head is tipped up 11° on the collar hinge, in 3 steps in S8.
  - The pencil tip meets the actual chin: CHIN_TOUCH (3012, 2060) in the source, where r0 aimed at the collar.
  - He stands closer to the door, so the key is just beyond his left shoulder.
- **B2, D2:**
  - "What time is it?" (V1) and "Thanks!" (V4) are now spoken in the panels where she stands, with tails to her mouth, which is open in the photograph.
  - The shop neon is covered by a handmade TICKET OFFICE card hung inside the glass.
  - The awning is covered by a handmade RANDOLPH station nameboard.
- **Protected and unchanged:** the P6 empty "Thanks!" window cut to the cupboard; the 7-pose door swing with latch and creak; the hold with the key fixed (FK offset 0); the memo card; the 4:10 clock re-set from the real clock; LoC/Commons sourcing with levels only; tone higher-key than kf-2.
- **Measured:**
  - Rest identity 0.0 for S0–S8, both in timing.json and in the editor's film-scale check.
  - FK: pivot drift 0.0, key offset Δ 0.0, jamb Δ 0.0. These come from the joint matrices, so they hold by construction.
  - Variant rest layers match their pages to ≤0.12/255.
  - Balloon land frames are asserted against timing.json.

## Remaining failure risk (to be judged by the next blind readers and critic)

- **P3:**
  - The SERVICE "door" is the right leaf of a cupboard (no room door exists in the Randolph photograph).
  - The walk reads only from his standing pose, the pitch and the new place. The page has no motion lines.
  - Readers may still say "cupboard" rather than "door".
- **The clerk's face:**
  - In all panels his eyes look down as photographed. P8's upward tilt is a hinge rotation; no second photograph exists.
  - The P8 head now sits close under the balloon.
- **D2:**
  - The two Bubley station photographs are a different station from Rothstein's office, joined by collage. The TICKET OFFICE card is large and is cropped by the panel edge in V2/V3.
  - She faces the camera, so she has her back to the window as she asks.
- **Plate repairs:** visible at 100% as a darker cabinet block left of the desk (P1/P2), and as a smoothed wall strip where the head ghost was.
- **Sound:** the footsteps are still smeared (a reverberant crowd source), and the counter bell is synthesized (declared).
- **Housekeeping:**
  - To free a 100%-full disk, the editor deleted the r0 full-rate frame dumps in readers-1-1/full, readers-1-2/full and critic-1/full. They can be regenerated from checkpoints/r0.
  - The site page (build.py) was not rebuilt in this unit: it is shared with other works.
