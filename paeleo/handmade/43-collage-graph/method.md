# SCION 43 · Collage Graph Rewriting · *The threshold, handmade*

## The studio and the thesis

SCION-COLLAGE-GRAPH-REWRITING: a grammar for images becoming new actors, tools, buildings and environments while keeping
editorial cause. Here every actor is a **typed entity graph** whose nodes are found fragments; the score is the
**scene-event contract** that decides which **rewrite rule** fires on which frame; each rule REPLACEs, MERGEs, SPLITs,
ENTERs or EXITs a node; a node is placed only by its **visual anchors** (two named points of the fragment mapped to two
points of the world). Nothing is tweened between drawings.

Thesis: *the dog is never the same set of pieces twice, and the circumstances rewrite what it is made of, but its choices
stay its own.* The defining passage is the approach and the sill: the decision to come rewrites the dog's head from its
shaded frames to its sunlit frames; as the dog walks into the door's light, each node that enters the light is re-cut from
the sunlit frames; at the sill the torso is SPLIT, so the dog ends half in and half out *materially*: lit chest inside the
door frame, shaded haunch and tail outside, joined by a graded edge. What would make it bland: a whole-dog cut-out slid
along the floor, or a dog whose material changed for no cause.

Swarm (merged into one agent; the coupling of cut, anchor and rule made separate agents costlier than useful): world-grammar
designer + archive forager + transformation dramaturg + matte compositor + rule verifier. The independent
surprise-and-readability critic is external (the brief's critic); I do not approve my own work.

## Native formal language, as built

- **Typed entity graph** (`build/scene.py`). Dog nodes: `dog.head`, `dog.torso` (or `dog.chest` + `dog.haunch` after a
  SPLIT), `dog.leg.fore` ×2, `dog.leg.hind` ×2, `dog.tail`, or a single `dog.whole` after a MERGE. Person nodes:
  `person.body` (or torso + thigh + shin after SPLIT), `person.sleeve`, `person.hand`, `person.head`, `person.hair`,
  `voice.arcs`. Door nodes: `door.leaf`, the room. Every placed node, with the fragment it is made of, is logged per change
  in `graph_trace.json`.
- **Rules** (`rulebook.json`, with every firing in this render): R1 REPLACE head (by intention; only a drawing whose native
  angle is within 45° of the wanted one); R2 REPLACE head by the looking-away head (turning to look); R3 MERGE dog → whole
  found frame (the turns: f027, f030 of the real dog turning); R4 SPLIT back to the mirrored graph; R5 REPLACE leg by
  stance/swing drawing; R6 EXIT legs / lie (four discrete drawings); R7 REPLACE material shade → sun; R8 SPLIT torso at the
  threshold; R9 ENTER head into the door light (look in); P1 ENTER voice (found sound arcs); P2 SPLIT coat (sit);
  D1 REPLACE door leaf by the found swing; D2 ENTER room light.
- **Motif tags**: `shade` (frames 0–14: the dog in shade looking up at its person), `sun` + `collar` (frames 45–48: the same
  dog seconds later in sunlight at its bowl; its head lowered to the bowl is re-used as the head lowered in trust),
  `turn`, `look-back`, `look-in`.
- **Visual anchors**: torso S (shoulder), H (hip), N (neck), T (tail base); head neck/nose (or neck/crown/muzzle); leg
  top/foot; tail base/tip; whole-frame ground/top; person feet/top/hip/neck/mouth; hand arm/tip. A stance foot is a world
  anchor: it keeps its world x while the body travels.
- **Coordinates and time**: metres along the porch (the score's x; threshold 0; my door opening −0.55…0.55 in a facade
  view), height v; screen X = 278 + 195·x; ground line 588 px mid-porch, 520 px at the sill. Dog graph in local metres
  ×1.25 (a big shepherd). Time base = the score's 24 fps; the dog's graph is solved on twos (12 drawings/s), the world at 24.
- **Provenance**: `assets.json` lists every fragment with its source frame file, title, archive URL, rights, scissors
  polygon (source px), anchors and operation (SAM mask ∩ scissors polygon, luminance key, mirror, tone, feather).

## How the dog is built and moved

Every fragment drawn as the dog comes from one source: *Amateur Film New Jersey C* (Home Movies, Internet Archive, public
domain), frames 6, 12, 27, 30, 33, 45, 48 (`trace.json → invariants.dog_sources = ["archive-dog"]`). Torso, alert head and tail
(cut tapered along the found tail) from f006; level head and the four legs from f012; turning frames f027/f030; the
profile head (`head_side_f033`, its own head turned sideways in the turning frame f033); sunlit torso, chest and legs from f045 (mirrored); low
head with the white collar from f048 (mirrored). Each piece is the SAM mask of its frame intersected with my scissors
polygon, toned by the whole dog of its frame (not stretched on its own); one paper rim is cut around the assembled dog.
**Nothing of the dog is drawn.**

- **Watching / backing away (1.0)**: the call starts at 0.70 and its arcs travel to it; it cowers (crouch drawing) and walks *backward* with
  planted feet (stance legs fixed in world x, swing legs replaced by the bent drawing).
- **Stops and looks (2.333)**: stands, head up (R1).
- **Turning away (3.417) and back (7.92–8.25)**: never a mirror flip. R3 MERGEs the graph into the real dog's own turning
  frames (f027 three-quarter, f030 front), then R4 SPLITs into the mirrored profile. The back is shown from 3.75 s.
- **Refusal**: stands with its back turned, then lies down (R6), tail toward the person, head low on its paws, whole dog in
  frame (right edge ≤ 1219 px, 61 px clear); the hind legs EXIT (fold under the haunch) from the 2/3 drawing on.
- **Turning to look (7.458)**: R2: on the still-turned lying body, on the choice's own frame, the head is replaced by
  `head_side_f033` (the dog's own profile head, mirrored), lifted clear of the back, muzzle level (3° above horizontal,
  measured) and pointing left to the door. The body stays lying (no hybrid) until the found turning frames take over at
  7.75: f030 *mirrored* (so the muzzle stays toward the door), then f027 mirrored; it stands facing the door from 8.08 and
  keeps watching it with the same level profile head (6°) until it decides to come.
- **Coming, head low (14.708)**: R1+R7: the head is replaced by f048 (head below the back line, collar showing) for the
  whole approach; the walk is the gait solver with found legs.
- **Lying across the sill (23.79)**: composed (no frame of this dog lies down). On the choice's own frame it is already half
  down (the feet stay where they stood while the body lowers over them), then down: forelegs short and forward, hind legs
  folded away. R7/R8 bring the sunlit chest and forelegs in by weight as they enter the light (over ~0.6 s of walking,
  never a one-frame swap), laid over the shaded body with a feathered rear edge; the door's light itself falls off softly
  across the body. Haunch and tail stay shaded, outside.
- **Looking in (26.4)**: R9: lying at the sill its head has rested on its paws since it lay down; on "come in" (from
  26.417, held to 28.458) the head is replaced by `head_back_f001`: the back of its own head and neck, from f001 (the dog
  seen from behind, raising its head to its person). The neck rises from the shoulders at 50° inside the lit opening, skull
  and ear toward the viewer, muzzle hidden: it looks into the room. Its left edge is at x 257 px (door leaf 235, hand tip
  211). Then it settles, head on its paws (f048, recut with a radial fade: no straight edge), and stays.

The world is other found images becoming buildings and tools: the home movie's stone pillar is the house wall, its path the
porch, its shrubs the hedge, its coat the porch timber; Straight Talk's door (closing swing, played backward) is the door; a
bulb from *Light Of Your Life B* is the lit room; the sound arcs of *We Learn About the Telephone I* are the person's voice;
a cloud time-lapse regraded is the dusk. The person is the coat of the dog's own person in the home movie (also cut as its
sleeve and hair), a face from *Anthracite: Pre-Shift Examinations*, a forearm and hand from *The Door to Heaven*.

## What is protected (and measured)

Measured from this render (`trace.json`, `invariants.json`, `build/cache/sound_levels.json`); final numbers are in the last
line of `ledger.jsonl`.

- **I1–I4**: `check_handmade.py` (see invariants.json).
- **Choice onsets measured from pixels** (`trace.json → measured_onsets`, each with how it was measured).
- **Feet**: max creep of a planted foot between consecutive frames (`feet_max_creep_m_between_frames`).
- **Identity**: every dog fragment from the one home-movie dog (`identity_single_source`).
- **Threshold end state**: last-frame dog bbox vs the door opening, px inside / outside the frame.
- **Sound** (measured, not listened to): soft voice vs calls (voice stem RMS; loudest 300 ms in the mix), soft vs room tone.

Judged only by viewing (by the critic, not me): whether the six choices *read* as choices; whether every frame of both turns
reads as a dog; whether the material rewrite reads as cause (the light) and not as clutter.

## What failed and what I changed (details in `ledger.jsonl`)

1. Per-piece paper rims made the dog read as broken pieces → one rim around the whole dog.
2. Torso halves mapped by (M, S) anchors rotated the sunlit chest into a wedge → every torso piece mapped by its own S/H.
3. The shaded torso kept the neck stump of a raised head → torso cut below the neck.
4. The first back-of-head (a drawn shape) looked like a cat's face → reshaped; the critic still read it as a cat, so it was
   replaced by a found head (repair 1 below).
5. The floor crop held the home movie's bowl; the porch end showed raw sky → recropped; the steps are off-frame right.
6. The voice arcs were invisible threads → luminous wavefronts drawn after the grade.
7. The dog was too small → local graph ×1.25, stride solved in world metres so the feet still hold.
8. The seated person was a box → person SPLIT into torso/thigh/shin, sleeve + forearm, hair cut from the coat.
9. Measured onsets lagged by quantisation → the choice shows on its first frame.

### Repair round 1 (independent critic: does not pass)

1. Look-in read as a cat (drawn, sharp ears) → found head and neck of f027, back-lit silhouette, neck from inside the chest.
2. Turning to look legible only at 7.92 → the found frontal head of f030, mirrored to the door, replaces the head from 7.50.
3. Refusal lying pose ran off the right edge → world rescaled to 195 px/m (X0 300), lying forelegs and head drawn in, head
   lowered onto the paws; right edge ≤ 1247 px.
4. Straight seam at the sill → feathered sunlit chest over an extended shaded haunch (graded join).
5. Flat pale tail → tail cut tapered along the found tail; all dog pieces toned per frame, not per piece.

### Repair round 2 (independent critic: does not pass, narrowly)

1. The darkened frontal silhouette read as a blob → looking in uses f009's real looking-away head with its ear and neck,
   neck faded along its base line (no straight cut), muzzle up inside the door frame.
2. The mirrored frontal head was oversized and looked at the camera → f009's head in profile, muzzle to the door, normal
   scale, from the choice's own frame (choices no longer wait for the next drawing on twos).
3. Lying away: standing-leg slabs → hind legs EXIT from the 2/3 drawing, lying forelegs short; world X0 278, right edge 1219.
4. Entering the sill read as two animals and thrust a stick paw → sun material blended in by weight over ~0.6 s, softer
   light falloff, feet stay put while the body lowers.
5. Lie onset late → on its own frame (23.792) the dog is already half down.

### Repair round 3 (after critic round 2; critic round 3: does not pass)

The f009 looking-away head was used for the look-back and the look-in. Critic round 3: the look-in head pointed steeply up
at the bulb; the look-back muzzle was thrown ~45° up; a hybrid lying/standing frame at 7.55; the person cut at the left
edge; calls near clipping and on the reaction frame.

### Repair round 4 (previous builder, not logged until ledger line 16)

Rotated the f006 head level for the look-back and the f048 head level for the look-in; kept it lying until 7.75; calls
lead by 0.30 s; mix peak −3.5 dBFS; the person seated just left of the door. On re-examination (this builder) the rotated
heads were illegible at 2× (a dark wedge; a triangular collar wedge), and the unmirrored f030 turned the muzzle back to the
right at 7.75–7.92.

### Repair round 5 (this builder, for the five conditions of critic round 3)

1. Look-in: a new found fragment, `head_side_f033` (the dog's own head in profile, SAM mask ∩ scissors, rounded back
   edge feathered into the neck), level (4°), muzzle inside the jamb at sill height, held over the whole window
   26.417–28.458 (it had started at 26.67 and ended at 28.1).
2. Turning to look: the same profile head on the lying body, lifted clear of the back, muzzle left at 3°, from 7.458;
   the found turn frame f030 is now mirrored so the muzzle never swings back to the right; the standing watch afterwards
   keeps the level profile head (the f006 head at 40° up is no longer used after 7.46).
3. No hybrid: lying + head 7.458–7.708, whole found frames 7.75–8.0, standing graph from 8.083 (checked on every frame).
4. Person and hand: inside the frame on every scene frame from 6 s (bbox x 45–211 px, measured per frame).
5. Sound: mix normalised to −5.0 dBFS (AAC headroom); measured on the AAC decoded from film.mp4: peak −5.03 dBFS; call
   onsets 0.700 and 3.100 s vs reactions measured at 1.000 and 3.417 (7.2 and 7.6 frames lead).

## What is still weak (my view; the critic decides)

- The home-movie dog is blurred and grey; the profile composite reads as a dog at film size but its parts are soft and the
  legs thick. The walk is a solver over four found legs, not a found walk.
- Looking in and turning to look use one found profile head: small (about 70 px long) and soft, as the home movie is.
  It is a profile into the room, not the back of the head; whether it reads as looking *in* is the critic's call.
- The found turn frames at 7.75–8.0 are frontal; the step from lying (7.708) to standing (7.75) is a cut, not a rise.
- The person is stiff (substitution in thirds), the found face is small.
- The voice is a formant synthesizer: intelligibility of "come here / it's all right / come in" is **unknown** (I cannot
  listen). Levels are measured; the timbre is not judged.
- The steps at 4.9 m are off-frame; the porch end is implied.

### Repair round 6 (after critic round 4: does not pass, narrowly; look-in only)

The level profile head pointed at the offered hand. Now the look-in shows the back of the head (`head_back_f001`, f001),
neck continuous with the body, muzzle hidden, centred in the lit opening; the low head f048 is recut with a radial fade
(no straight cut edge). Neck angles 30–45° put the head beside the hand; 62° climbed onto the bulb; 50° chosen. Still
weak: the f001 head is soft and small, a dark skull with one ear bump; the head is 46 px from the hand (no muzzle line).

## What I did not do

- No human viewing; I did not listen to the sound; the critic has not re-judged the repairs.
- No Quick, Draw! drawings, no other found shots beyond those listed, no 3D maquette, no import of stage.js or lenses.js.
- No git, nothing written outside this folder. `operator.html` is a local file, not published.
