# quatre-vingt-quinze, branch B (from checkpoint r1)

The hypothesis is Explanation B. The gaze has no visible target. V_SKY's head is good enough, but r1's down camera finished the B to E travel by 44.5 s with B's bell entirely above the frame. A gaze directed up and off-screen reads as aimed at the only thing visible up there, which is the key.

Repair: change only the down-route camera, plus a larger B/E arrow. The cells, the lettering, the page, the across camera and the sound are untouched.

## What changed (branch-b/quatre-vingt-quinze.py only)

1. **The down-route camera at E (`_down_E_camera`, used only when route == down and cell == E).** Times are in E's cell-local time (film 44.0 to 47.0 s).
   - 0 to 0.5 s: an eased travel from B's centre into a **B/E two-panel framing**, entering from B's side as every cell entry does. The framing has its top at page y 590 and a view height of 1000 page px, which is 0.72 frame px per page px; r1 used 968.
   - 0.5 to 1.75 s (44.5 to 45.75 s): **hold** on the B/E framing. This covers all of V_SKY (0.50 to 1.67 s).
   - 1.75 to 2.25 s: tilt down onto E's ordinary r1 framing, then hold to 3.0 s. The E to H travel starts from the same camera state as r1.
   - The geometry was measured on BASE(), not guessed. B's bell body in its page pose is solid ink at page y 540 to 700, and the mouth rim, clapper disc and swing arcs sit at y 700 to 780. In the held frame, the lower bell body fills the top ~80 px. The mouth, clapper disc and the two motion arcs sit at frame y ~80 to 137, almost straight above her head. E is whole below, down to its bottom rule.
2. **The B to E gutter arrow is larger (`BIG_ARROW_BE`).** It uses U1's arrow polygon, RED and MAUVE shadow, scaled 1.12x in length and 2.0x in width. The length is limited by the B/E gutter: tip and tail stay inside the 12 px border inset that the adjacency test allows. It is on screen for the whole E occurrence, 44.0 to 47.0 s (laid down from 44.08 s), so it holds well over 0.5 s. The arrow is a film-only route overlay; the page has no arrows. Every other arrow is unchanged.
3. Plumbing:
   - FILMS is an absolute path.
   - Products go to branch-b: `quatre-vingt-quinze.mp4`/`.webp`, `quatre-vingt-quinze.png`, the across and down strips, `cells/`, and `readers/` (across-only and down-only cuts).
   - REVISION is "r1-branch-b".
   - Nothing is written to assets/, films/quatre-vingt-quinze.py, credits or notes.

## Verification

- **Adjacency fixture** (run on the branch script, with outputs redirected to the scratchpad): ALL_OK.
  - All nine cells are pixel-identical across against down in cell space, every frame, E included.
  - Film rest frames equal the page; the end hold equals the page.
  - Bell tail: across E is digital silence (-240 dBFS); down E is -25.1 dBFS at 44 to 45 s and -30.0 at 44.5 to 45.0 s.
- **Page:** branch-b PNG against checkpoints/r1 PNG: zero-pixel difference (3360x2400).
- **Audio:** the decoded PCM is byte-identical to r1 (sha1 1382406f...).
- **Film:** 64.0 s, 3.9 MB, sha256 prefix c93b2db72240fe08.
  - Frame difference against r1 is 0.0 at 5, 16, 17.5, 30.5, 40, 55 and 62 s, so the across route, the turn and the end are unchanged.
  - Frames differ only within 44.0 to 47.0 s (camera, and the larger arrow).
- **Frames:** branch-b/frames/f_*.png (16.0, 44.0, 44.25, 44.5, 45.0, 45.6, 46.0, 46.5 s) and frames/contact.jpg.
  - At 44.5 s, the bell's mouth, clapper and swing arcs are in the top of frame, above her head.
  - The arrow is clearly visible on the B/E gutter.
  - The marks show their vertical long arms.
  - D's window watcher is in frame at left.
- **Protected and unchanged:**
  - E's art inside the border.
  - The shared I ending (the key slides under the shut door, 'MERCI.').
  - The asymmetric bell tail.
  - The Lécroart page grammar.
  - The red cord and thread.
  - The watcher in D.

## What this branch does not claim

- V_SKY's nose still points up and to the right, along her arm. The key is still in frame, held above and in front of her face. This branch only puts the bell into the image as a rival target, directly above her head, while V_SKY is on screen. Whether readers now say "the bell rang for her" is untested; this is the test of Explanation B.
- If readers still name the key, Explanation B is refuted, and the pose or gaze direction (a cell change) is the remaining lever.
- No reader was run. B3 (a down-first reader whose account is recorded before the across route) is still outstanding. The single-route cuts for it are rendered here as branch-b/readers/quatre-vingt-quinze-down-only.mp4 and -across-only.mp4. In the down-only cut, this beat falls at 15.0 to 18.0 s.

## Possible bar conflict (for amendments.md; not written there, since this branch writes only in branch-b)

plan.json "aesthetic" says: "0.5 s eased camera travel entering from the predecessor's side". The B to E entry still travels for 0.5 s from B's side, but it lands on a B/E two-panel framing. A second 0.5 s tilt onto E follows at 45.75 s.

Proposed reading for the operator: "entering travel 0.5 s; the down B to E entry may hold a two-panel B/E framing through E's head turn before settling on E."

## Rights fixes (branch copies: branch-b/credits.json, branch-b/notes.txt)

- **notes.txt:** the soundtrack licence now has a version. It reads "concrete steps (CC BY-SA 4.0 and 3.0: the soundtrack is CC BY-SA 4.0)". The key clause was shortened to keep the note at 109 words (bar: 60 to 110).
- **credits.json**, the two BY-SA entries (Fridingen bell, 4.0; Concrete Steps 2, 3.0):
  - The "offered under the same licence (ShareAlike)" sentence now names one soundtrack licence, CC BY-SA 4.0, with its URL. For the 3.0 steps, it cites 3.0 section 4(b), which allows a later version for adaptations.
  - Both entries gain `adaptation_license` and `adaptation_license_url` fields.
  - The BELL and KEYS used_as fields already carried the r1 text. All other entries are unchanged.
- **Stale files outside branch-b, not edited** (branch rule). Corrections for the operator:
  - forage/ledger.json:
    - BELL.used_as: replace it with the credits' r1 cue_B text.
    - KEYS.used_as: replace "grain 0.31-0.62 s at 0.75 s" with "soft grain 0.73-1.05 s at 0.583 s, gain 0.12".
    - outputs.checks: replace the r0 bell-tail figures (-44/-31 dBFS) with the r1 measured values.
    - adapted_licence: make it "CC BY-SA 4.0 (3.0 steps relicensed under 4(b))".
  - exposure.json absences: the line saying that key_cut.png and the stencils "were not yet delivered" is stale. The render uses forage/key_cut.png.
  - puppets.py credit block (around lines 1688 to 1701): KEY local_path and KEYS-CLINK file_url and local_path are U2 placeholder text. They do not affect the render.
  - amendments.md: the sheet start at frame 0 and the 11th visitor drawing (v_sky) still await operator ratification.
- **No new sources.** No downloads were made in this branch, and there are no new credits.
