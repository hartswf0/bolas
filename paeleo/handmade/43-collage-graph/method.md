# SCION 43 · Collage Graph Rewriting · *The threshold, handmade*

## The studio and the thesis

SCION-COLLAGE-GRAPH-REWRITING: a grammar for images becoming new actors, tools, buildings and environments while keeping
editorial cause. Here every actor is a **typed entity graph** whose nodes are found fragments; the score is the
**scene-event contract** that decides which **rewrite rule** fires on which frame; each rule REPLACEs, MERGEs, SPLITs,
ENTERs or EXITs a node; a node is placed only by its **visual anchors** (two named points of the fragment mapped to two
points of the world). Nothing is tweened between drawings.

Thesis for this scene: *the dog is never the same set of pieces twice, and the circumstances rewrite what it is made of, but
its choices stay its own.* The defining passage is the approach and the sill: the decision to come rewrites the dog's head
from its shaded frames to its sunlit frames; as the dog walks into the door's light, each node that enters the light is
re-cut from the sunlit frames; at the sill the torso is SPLIT, so the dog ends half in and half out *materially*: lit chest,
shaded haunch, the tail never rewritten. What would make it bland: a whole-dog cut-out slid along the floor, or a dog
whose material changed for no cause.

Swarm (merged, since one agent built it; the coupling of cut, anchor and rule made separate agents costlier than useful):
world-grammar designer + archive forager + transformation dramaturg + matte compositor + rule verifier, all here.
The **independent surprise-and-readability critic was not run by me**: I cannot approve my own work; the film goes to the
critic named by the brief.

## Native formal language, as built

- **Typed entity graph** (`build/scene.py`). Dog nodes: `dog.head`, `dog.torso` (or `dog.chest` + `dog.haunch` after a
  SPLIT), `dog.leg.fore` ×2, `dog.leg.hind` ×2, `dog.tail`, or a single `dog.whole` after a MERGE. Person nodes:
  `person.body` (or torso + thigh + shin after SPLIT), `person.sleeve`, `person.hand`, `person.head`, `person.hair`,
  `voice.arcs`. Door nodes: `door.leaf`, the room. Every placed node is logged per frame (`graph_trace.json`).
- **Rules** (`rulebook.json`, with every firing in this render): R1 REPLACE head (by intention, only to a drawing whose
  native angle is within 45° of the wanted one); R2 REPLACE head by its mirror (turning to look); R3 MERGE dog → whole found
  frame (the turns: frames f027 and f030 of the real dog turning); R4 SPLIT back to the mirrored graph; R5 REPLACE leg by
  stance/swing drawing; R6 EXIT legs / lie (four discrete drawings); R7 REPLACE material shade → sun; R8 SPLIT torso at the
  threshold; R9 ENTER head into the door light (look in); P1 ENTER voice (found sound arcs); P2 SPLIT coat (sit);
  D1 REPLACE door leaf by the found swing; D2 ENTER room light.
- **Motif tags**: `shade` (frames 0–14: the dog in shade looking up at its person), `sun` + `collar` (frames 45–48: the same
  dog seconds later in sunlight at its bowl; its head lowered to the bowl is re-used as the head lowered in trust),
  `turn`, `look-in`.
- **Visual anchors**: torso S (shoulder), H (hip), N (neck), T (tail base); head neck/nose; leg top/foot; tail base/tip;
  whole-frame ground/top; person feet/top/hip/neck/mouth; hand arm/tip. A stance foot is a world anchor: it keeps its
  world x while the body travels (measured creep below).
- **Coordinates and time**: metres along the porch (the score's x; threshold 0; my door opening −0.55…0.55 in a facade
  view), height v; screen X = 305 + 205·x; ground line 588 px mid-porch, 520 px at the sill. Dog graph in local metres ×1.25
  (a big shepherd). Time base = the score's 24 fps; the dog's graph is solved on twos (12 drawings/s), the world at 24.
- **Provenance**: `assets.json` lists every fragment with its source frame file, title, archive URL, rights, the scissors
  polygon (source px), anchors, and the operation (SAM mask ∩ scissors polygon, luminance key, mirror, tone stretch).

## How the dog is built and moved

All 17 fragments drawn as the dog come from one source: *Amateur Film New Jersey C* (Home Movies, Internet Archive, public
domain), frames 6, 12, 27, 30, 45, 48 (`trace.json → invariants.dog_sources = ["archive-dog"]`). Torso and alert head from
f006; level head, the four legs and the fur of the back of its head from f012; turning frames f027/f030; sunlit torso, chest
and legs from f045 (mirrored); low head with the white collar from f048 (mirrored). Each fragment is the SAM mask of that
frame intersected with my scissors polygon; one rim of paper is cut around the assembled dog.

- **Watching / backing away**: R1 picks the head; a call makes it cower (crouch drawing) and walk *backward* with planted
  feet (stance legs fixed in world x, swing legs replaced by the bent drawing).
- **Turning away (3.417) and back (8.0)**: never a mirror flip. R3 MERGEs the graph into the real dog's own turning frames
  (f027 three-quarter, f030 front), then R4 SPLITs into the mirrored profile. The back is shown from 3.75 s.
- **Refusal**: stands with its back turned, then lies down (R6), tail toward the person.
- **Turning to look (7.458)**: R2: the head alone comes round to the door on the still-turned body; the body rises and
  turns after it.
- **Coming, head low (14.708)**: R1+R7: the head is replaced by f048 (head below the back line, collar showing) for the
  whole approach; the walk is the gait solver with found legs.
- **Lying across the sill (23.79)**: composed (no frame of this dog lies down): torso lowered, forelegs laid forward, hind
  legs gathered; R7/R8 make the chest and forelegs sunlit inside the door frame, the haunch and tail shaded outside.
- **Looking in (26.4)**: R9: the head is replaced by the back of its head (the one drawn outline in the film, cut from the
  dog's own fur), dark against the lit room: the head turned away from us, into the house. Then it settles, head on its paws.

The world is other found images becoming buildings and tools: the home movie's stone pillar is the house wall, its path
the porch, its shrubs the hedge, its coat the porch timber; Straight Talk's door (closing swing, played backward) is the
door; a bulb from *Light Of Your Life B* is the lit room; the sound arcs of *We Learn About the Telephone I* are the
person's voice; a cloud time-lapse regraded is the dusk. The person is the coat of the dog's own person in the home movie,
a face from *Anthracite: Pre-Shift Examinations*, a forearm and hand from *The Door to Heaven*.

## What is protected (and measured)

Measured from this render (`trace.json`, `invariants.json`, `build/cache/sound_levels.json`):

- **I1–I4**: `check_handmade.py` → ALL OK (see invariants.json).
- **Choice onsets measured from pixels** (`trace.json → measured_onsets`, each with its rule of measurement): see the
  report numbers in `ledger.jsonl` (last line) — they are recomputed by `build/trace.py`.
- **Feet**: max creep of a planted foot between consecutive frames (world metres) — `trace.json →
  feet_max_creep_m_between_frames` (≈1 mm; it comes from the slight depth scale change near the sill).
- **Identity**: every dog fragment from the one home-movie dog (`identity_single_source: true`).
- **Threshold end state**: end bbox vs the door opening, px inside / outside the frame (`invariants.end_part_*`).
- **Sound**: soft voice vs calls (voice stem RMS and loudest 300 ms in the mix), soft voice vs room tone.

Judged only by viewing (not by me — by the critic): whether the six choices *read* as choices; whether the dog reads as a
dog in every frame of both turns; whether the material rewrite reads as cause (the light) and not as clutter.

## What failed and what I changed (details in `ledger.jsonl`)

1. Per-piece paper rims made the assembled dog read as broken pieces → one rim around the whole dog.
2. Torso halves mapped by (M, S) anchors rotated the sunlit chest into a wedge → every torso piece mapped by its own S/H.
3. The shaded torso kept the neck stump of a raised head, so a low head looked doubled → torso cut below the neck.
4. The first back-of-head looked like a cat's face (the collar strip read as a mouth) → collar removed, darker, ears lower.
5. The floor crop held the home movie's bowl; the porch end showed raw sky → recropped; steps are off-frame right.
6. The voice arcs scaled from mouth to dog were invisible threads → luminous wavefronts drawn after the grade.
7. The dog was too small to read → local graph ×1.25, with the stride solved in world metres so feet still hold.
8. The seated person was a box → person SPLIT into torso/thigh/shin, sleeve + forearm, hair cut from the coat.
9. Two measured onsets lagged by quantisation (watch after retreat 2.583, lie down 24.0) → the choice shows on its first
   frame (stands and looks; starts to go down).

## What is still weak (my view; the critic decides)

- The home-movie dog is blurred and grey; the profile composite reads as a dog at film size but its parts are soft and
  the legs thick. The walk is a solver over four found legs, not a found walk.
- The back of the head is a drawn outline; it may read as generic animal, not *this* dog.
- The person is stiff (substitution in thirds), the face fragment is small.
- The voice is a formant synthesizer: intelligibility of "come here / it's all right / come in" is **unknown** (I cannot
  listen). Levels are measured; the timbre is not judged.
- The steps at 4.9 m are off-frame; the porch end is implied.

## What I did not do

- No independent critic was run here; no human viewing; I did not listen to the sound.
- No Quick, Draw! drawings, no other found shots beyond those listed, no 3D maquette, no import of stage.js or lenses.js.
- No git, nothing written outside this folder. The operator page (`operator.html`) is a local file, not published.
