# Contaminant jelly · SCION 093 · two cuts of one take

Built with SCION 093 *What Is Neorealism?* (counterfactual cuts from shared material) as the spine.

**Revision 2 (after the golden-river operators).** The care strand is no longer a list chosen in advance: it is defined by physical evidence, an image in which something is touched, the same rule the cinema cut's censor applies. The take's jellyfish collects by rhyme (each image shares a visible feature with the last). The take was re-rendered and both cuts rebuilt; they have not been re-watched by a critic since.

**The editorial question.** Given one take of a jellyfish gathering an archive, what does the film treat as consequential when it is cut for the delivery, and what when it is cut for the peripheral life?

**The film** (`film.mp4`, about 81 s, no text): amber leader, **A** (28 s); blue leader, **B** (28 s); white leader, the **diagnostic** (both cuts side by side on the take's clock at 3.6x, each panel dark where its version omitted that moment, bars of retained intervals, a playhead).

- **A, the censor's cut**: the delivery. The jellyfish lifting, carrying and handing fragments on; the untouched archive images briefly. No image in which something is touched is ever given the frame: those appear only as small thumbnails the jellyfish tows.
- **B, the jellyfish's cut**: the peripheral life. The archive's people held for their full length, and the moment after each goes. The jellyfish's work (lifting, carrying, handing on) is left out; it appears only drifting between them.

## Shared source pool

One continuous take, `../rushes/film.mp4` (72 s), rendered from the page in `?rushes=1` mode with seed 8: no censor, no cooling, no cut-aways; each fragment the jellyfish lifts plays full screen for 3 s. `../rushes/meta.json` records, for every source frame, whether it is a world shot or an insert, which fragment, its strand, and what the jellyfish is doing. Archive frames are public domain (`../mood/sources.json`).

## Controlled variables

- Same source take, no added footage; both versions in source order (`checks.json`).
- Equal length: both exactly 672 frames (28 s at 24 fps). This is also the deliverable's equal-duration variant.
- Same grade (the take's own), same splice treatment (25 ms audio fades at every cut).
- Sound: the take's own sound is cut with the picture; one identical newly composed cue (`build/cue.js`) runs under each at the same level. Integrated loudness is in `loudness.json` (A −17.2, B −16.8 LUFS in revision 2).
- The diagnostic is visually distinct from ordinary playback (two panels, bars, a playhead, 3.6x) and quieter.

## Files

- `edl_A.json`, `edl_B.json`: the paired edit-decision lists (source frames and seconds, what each interval shows).
- `source_map.json`: for each annotated stretch of the take, how much each version keeps.
- `checks.json`: same pool, in range, source order, equal length, splice counts, seconds given to each kind of material.
- `loudness.json`: integrated LUFS of A, B and the diagnostic.
- Build: `../build/make.sh rushes` (the take), then `node ../build/edl.js` and `python3 ../build/assemble093.py`.

## Status

Independent critic, round 1 (093 tribunal; it wrote down what it saw before reading the argument): **pass**. It found the change in what counts "clear": the same people as tiny cargo in A and full frame in B, B's steady 3-second holds against A's 1–2 s cuts, matched loudness and cue. It found two faults:
- B did not omit the jellyfish's work (about 7 s, opening on a handoff).
- The film had been encoded at 29 fps by a build bug.

Repairs, verified by measurement but not yet re-watched by a critic:
- B now holds 0 s of handoff, lift and carry, and opens on an archive image (`checks.json`).
- The film is 24 fps (1941 frames).
- A's description now says what the critic saw: the people appear in A only as towed thumbnails.

Not repaired, for a later round: the critic could not tell whether the leaping woman upside down is a handstand or a flipped image (it is a handstand, frame `yoga_f024`). The diagnostic is mainly rhythm at 3.6x.
