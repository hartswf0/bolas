# SCION 29 · GrabCut: the threshold, cut out of archive film

## Thesis
Every figure on screen is a figure *extracted* from a public-domain archive frame by our own graph cut, and it keeps its cut
line. The dog is the home-movie dog of *Amateur Film New Jersey C*, cut out frame by frame; the person and the door are cut
from *Straight Talk* (NTIS, 1992); the low hand is cut from *The Door to Heaven* (1941) away from the card its fingers hold.
The defining passage is the end: a dog that this footage never shows lying down is assembled from the pieces of one of its own
frames and lies across the lit sill, front half in the door frame, then turns the back of its head into the room.
What would make it bland: a generic puppet with an archive texture laid over it. So the dog's look and its motion are the cuts
themselves: substitution of whole real cut frames (turns, walk, watching), re-timing and reversal by registered distance,
and re-posing of its own cut pieces only where the footage has nothing (lying, the head coming round).

## Swarm (one agent, roles merged; no independent critic was run by me)
- Source image restorer: `build/plate.py`, a camera-registered median clean plate of the dog shot (dog excluded).
- Segmentation operator: `build/graphcut.py` (Boykov–Kolmogorov max-flow in pure Python, numpy elsewhere), `extract.py`,
  `extract_world.py`.
- Boundary cost designer: unaries (intensity × local texture × |frame − plate| histograms, colour cube for colour footage),
  contrast pairwise term, seeds (SAM eroded = fg, SAM dilated complement = bg, rig-key scribbles, belly-gap and tail
  scribbles, box + scribbles for unmasked figures).
- Edge/matte specialist: `cleanup()` (largest component = no background islands, small-hole fill, border matte from local
  fg/bg means with a distance-ramp fallback), 2× supersampled cut averaged back to source resolution.
- QA inspector: `inspect_cuts.py` proof sheets, `trace.py`, `export_pieces.py` failure masks.
- Independent extraction critic: **not run** here; the brief assigns an independent critic after delivery.

## Native formal language, as kept in the project
Typed primitives (`graphcut.py` docstring): unary costs U_fg/U_bg, pairwise W_r/W_d, seeds {unknown, hard fg, hard bg},
the cut (bool), alpha (float). Coordinates: source-frame pixels; every piece keeps its crop origin (`pieces/manifest.json`:
piece (u,v) → source (u+ox, v+oy)); canvas transforms are affine (dog, person, hand) or projective (door panel).
Time base: score frame i, t = i/24. Mapping: X(x) = 325 + 205·x px (threshold x = 0 at 325, sill 0.56, door ±0.46 → 231..419).
Numerical invariant tested: the BK cut energy equals the max flow (synthetic test, exact), and the PAELEO trace invariants
(below). Artistic achievement judged only by viewing: whether the cut dog reads as one animal deciding.

## How the dog is built and moved
- Cut: 50 frames extracted; 16 used (f0, f9–11, f13, f15, f26, f30, f34, f36, f38, f40, f42–45). SAM masks are one input:
  they seed and softly bias the cut; our cut disagrees with SAM on 400–1900 px per frame (logged per piece).
- Watching: substitution among real cuts f9/f10/f11 (head up toward the person), boiling every ~0.45 s, anchored at the feet.
- Backing away (1.0–2.33 s): the real walk f42–45, mirrored to face the door and played **backwards**; each drawing is placed
  at its own registered source position (plate coordinates × scale), so the feet hold within a drawing and the travel is the
  dog's own stride.
- Turning its back (3.42–3.86 s): ten real cuts of the dog turning, side-left → frontal → 3/4 right (13, 15, 26, 30, 34, 36,
  38, 40, 42, 44). No mirroring or squashing inside the turn; every drawing is a filmed dog.
- Lying with its back turned (4.45–7.46 s) and lying across the sill (from 23.79 s): the *puppet*: f13 split at manual joint
  lines into head, torso, two forelegs, hind legs, tail; the forelegs are laid forward along the boards, the hind legs folded
  behind the torso, the torso lowered, the head levelled or laid on the paws (score `rest`), the tail wagged (score `wag`).
  Mirrored for the refusal. At lie = 0 the puppet is exactly the cut f13, so the switch is drawing-to-drawing.
- Head comes round (7.458 s): on the turned (mirrored) lying body the f13 head is drawn un-mirrored, over the shoulder,
  facing the door; the body rises; then turns back through mirrored 3/4 cuts (36, 38, 40) to side f13.
- Coming, head low (14.71–23.79 s): the mirrored real walk f42–45, drawing chosen by distance travelled (registered stride),
  walking into the depth of the doorway as it nears (feet y 620 → 546).
- Looking in (26.54 s): the head is replaced by the f0 head, which the home movie shows from behind, raised: the back of
  the head toward us, drawn behind the torso so its crop edge is hidden.

The world: façade stone = the stone pillar cut from the dog's own shot, tiled; porch boards and far garden = the clean plate;
the door panel (Straight Talk f28) hinged by a homography, ajar then swinging inward at 6.2 s; light, sky, floor spill,
shadow (the dog's own rendered alpha flattened onto the boards) and grain are computed. The typed prompts appear as small
slips at the bottom; the dog's state is never printed.

## Measured (from the render's own dog layers: `build/cache/measure*.json`, `trace.json`)
Checker `tools/paeleo/check_handmade.py`: **ALL OK** (I1 choices, I2 threshold min/end x = 0.59, I3 r = 1.0 on x_screen,
I4 share turned = 1.0).
Measured onsets (score → measured): retreat 1.000 → 1.000; watch 2.333 → 2.333; refuse 3.417 → 3.542; watch 7.458 → 7.458;
approach 14.708 → 14.708; lie down 23.792 → 23.792; look in 26.4 → 26.542 (back-of-head piece first drawn).
How: facing = the drawn nose vs neck (rig keys carried by each drawing's transform); retreat/approach = x or head-top departs
from its watching level; lie = start of the final sinking of the dog's coverage centroid. These detectors were written
after a first full render and adjusted once (ledger #12–13); they measure the render, but they were tuned on it.
Because the choreography switches drawings at the score's times, the agreement is structural: honest, but not independent.
End: lying, coverage centroid x = 433 px; 43 % of the dog's pixels are left of the right jamb (inside the door frame), the
tail outside.
Sound (`build/cache/sound_levels.json`, RMS over voiced samples): calls −16.3 / −15.1 dBFS; soft voice −28.3 / −28.7 /
−28.3 dBFS (≥ 11.9 dB quieter than the calls); room tone −47.3 dBFS (soft voice 18.6 dB above it). Footfalls: 98, placed
at the frames where the walk drawing changes.
Film: 1280×720, 24 fps, H.264 + AAC, 912 frames, 38.0 s, 6.9 MB, faststart.

## Looked at (by me, the builder; not a critic's judgement)
Proof sheets of cuts, the puppet poses in isolation, every frame of both turns, the walk, the sill window, and 1 fps frames
from the encoded film. What I saw: the turn away reads frame by frame as a dog; the lying poses read as a dog lying in a
sphinx pose; the walk reads as a dog walking with its head below its back; the end reads as a dog lying on the sill in front
of the light with its head inside the frame.

## What failed and what changed
See `ledger.jsonl`. Main ones: graph cuts bridged the shadowed gap between the legs and dropped the tail (fixed with seed
constraints and 2× source resolution); the clean-plate cue helped little on dark fur over dark ground; weakening SAM's
authority made bleeding worse (branch rejected); graph-cut part splitting hugged its seeds (replaced by manual joint lines);
the first lying puppet was a tangle (exterior-only cut lines, split forelegs, corrected head rotation); shrub tiles read as
black trapezoids (removed); walk drawings f46–48 had blocky SAM-shaped cuts that read as a blob (dropped from the cycle).

## What is still weak
- Several cut edges are still SAM-shaped and boxy (f16/f19 were avoided; f44, f45 have straight runs). Edge fidelity is
  limited by the 384×288 blurred home movie; at film scale the dog is ~1.4× its source and soft.
- The dog is dim and small in the first 6 s (dusk before the door opens); the pre-door scene is sparse.
- The lying puppet's mid-transition frames (lie ≈ 0.3–0.6) are awkward; the head-over-the-shoulder at 7.46 points upward.
- The person is a back view read as a silhouette; her sitting legs are a dark folded piece; the 6.0 s frame is awkward;
  her lower legs are a stretched repair (recorded) because the archive frame cuts her off at the knee.
- One walk-cycle seam (f45 → f42) pops; walk drawings are 3/4 views, watching drawings are side views: the switch at
  14.7 s and 23.79 s is a visible substitution.
- The sound is synthesized formant speech: it is pitched and shaped like "come here", "it's all right", "come in" but I
  cannot listen to it; intelligibility is unknown. Levels above are measured, not heard.

## What I did not do
No independent critic was run; no human viewing. No mobile operator page (in the SCION deliverable contract; not in the
brief's list). No matting comparison beyond the border matte; no extraction presets by scan class. No GPU, no cv2/scipy,
no network. No Quick, Draw! drawings used. No git.
