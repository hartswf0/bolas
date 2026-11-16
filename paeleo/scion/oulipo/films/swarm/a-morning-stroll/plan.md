# A Morning Stroll: SCION swarm plan (Direction 1, "Rizzuto Stoop")

Director's plan, revision `plan-r1`. It is rebuilt from scratch. Earlier files (`films/a-morning-stroll.py` and the station-seed notes and credits) are superseded. Only the foraged sources already in `films/sources/a-morning-stroll/r2/` may be reused, and only after their licences are re-verified.

Inputs read:
- `prompts/a-morning-stroll.md`, all of it
- `films/BRIEF-2.md`
- `proposals/proposals.md`, `board.jpg` and `kf-1.png` (the chosen direction)
- `catalogue/variations.json` (id 20)
- the references `assets/references/orchard3.webp`, `orchardAK08.webp` and `orchardAK17.webp`
- swarms.json prompts #29, #32 and #45, in full
- `kit.py`: 960x540, 24 fps, 44.1 kHz

## 1 · Creative thesis

A white chicken climbs a stoop and knocks twice on a door with its beak, and the door lets it in. Someone on the sidewalk stops to watch. The same small act, *tok . tok* and then in, happens three times, in 1959, 2009 and 2059.

The bird, the two strikes and the watcher's turned head never change. What changes is the world the act lands in, and it is carried by real material:
- a 1959 silver-gelatin street photograph;
- a 2009-era colour digital photograph of a Philadelphia row house;
- a cold, glazed 2059 entrance whose door can *hear*.

The door's answer escalates:
- 1959: an unseen hand opens the door.
- 2009: the door opens only to its security chain, and the bird has to squeeze through.
- 2059: nobody opens it. The door reads the knock rhythm as an access code and slides aside by itself.

The animal is a real photographed rooster, cut out and articulated. It is animated frame by frame on real stone steps, under real hard light, with real knocking. It is not a drawing in a photographic costume.

**What would make it bland:** three slideshows of plates with a sliding sticker, in which the knock is not legible as a knock, the eras differ only by a colour grade, and the third door is just a door.

## 2 · Defining beat and comparison baseline

**Defining beat: THE KNOCK (test shot).** It is shot B of every version, local time 6.00 s.
- The rooster's head piece rotates about the neck pin, and the beak tip makes contact with the door leaf twice. The contacts are at 6.00 s and 6.32 s, 0.32 s apart, which is 8 frames at 24 fps.
- Each contact gets a 2-frame recoil and a sound onset on the contact frame.
- The door then opens (7.0–8.5 s) and the bird steps over the sill and is occluded by the jamb (8.5–10.0 s).

What the viewer should be able to point to:
- the beak touching wood, or glass;
- two sounds in the same rhythm each time;
- the door moving *because of* the knock;
- in 2059, a door that moves with no hand, its sensor dots lit in the same rhythm.

**Comparison baseline.** This is `baseline.mp4`, a diagnostic only and not part of the film. It has the same plates and the same event times, staged as one static wide shot of each plate. The rooster cut-out is a single rigid sticker translated along the treads: no joints, no head strike, no occlusion and no cast shadow. The knock is a sound only.

The film beats the baseline when a viewer with the sound off can still say when the bird knocked and how many times.

## 3 · Lineage Genome and Olog

### 3.1 Lineage Genome (compact)

| field | value |
|---|---|
| Source work | *A Morning Stroll*, Grant Orchard and Studio AKA, 2011. Drawn line (1959), flat-colour 2D/vector (2009), photoreal CG (2059). About 7 min. |
| Source media | Digital 2D and CG animation. The 1959 section is black ink line on white, with a heavy vignette and grain. |
| Target media | Photo-cutout puppet animation over foraged archive photographs (LoC, Commons), with foraged recordings and some handmade sound. About 68 s at 960x540, 24 fps (animated on twos for the puppet). |
| Preserved relation | A chicken knocks at a city door and is let in while a pedestrian watches. Eras 1959 → 2009 → 2059. |
| Optics change | Drawn line → photographic plates. Sidewalk-level framing is kept. Hard morning light and cast shadows replace the drawn black masses. |
| Formalism change | A hierarchical FK joint graph (#32) on GrabCut-extracted pieces (#29). An occlusion DAG with plate holdout mattes (#45) puts the bird *behind* the real railing. |
| Concept change | Era is carried by *material* (print, colour digital, glazed smart entrance), not by drawing style. The door's affordance escalates: hand, chain, listening door. |
| Sound change | The source uses scored, comic effects. The target uses real knocking recordings at a fixed rhythm and interval, real or foraged street ambience, and a handmade synthetic chime only where the 2059 door itself answers. There is no dialogue and the voice is declared silent. |

**Formation epochs, weighted 0–100:**

| weight | epoch | reason |
|---|---|---|
| 90 | Orchard / Studio AKA 2011 | The source. It fixes the event, the eras and the deadpan holds. |
| 75 | Queneau, *Exercices de style*, 1947 | The repetition engine. Orchard names it in the AWN interview. This is a reported claim, not independently verified here. |
| 80 | Mid-century street photography, 1950s (Rizzuto, Anthony Angel Collection, LoC) | It supplies the 1959 plate itself: the hard light, the granite stoop and the lace ironwork. |
| 60 | Gilliam photo-cutout animation, 1969–74 | Photographed animals cut out, pinned and made to act on found plates. |
| 45 | Reiniger cutout theatre, 1920s | Articulated rigid pieces about pins. It also gives the diagnostic render's technique. |
| 50 | Digital compositing, 1990s– | Holdout mattes and contact shadows. |
| 20 | Paul Auster, the anecdote collection | Orchard credits the chicken anecdote to a story in an Auster-edited collection. Uncertain which story; recorded as reported only. |

### 3.2 Olog: types and arrows

Types:
- **Actor**: the rooster puppet, a joint graph.
- **Watcher**: a pedestrian, seen only as a cast shadow plus its head piece.
- **Stoop**: the treads, as a list of tread-nose lines in plate coordinates.
- **Door**: leaf, jamb, sill and its opening mechanism.
- **Strike**: an event of `{t, beak_tip_xy, contact: bool}`.
- **Cue**: the sound event of a strike.
- **EraWorld**: `{year, plate_id, light_dir, materials, door_mechanism, sound_rules}`.
- **Version**: an EraWorld times the event score.

Arrows (◻ = holds in every Version):
- ◻ CoreBeat: an Actor, the *chicken* —climbs→ a Stoop —reaches→ the landing —strikes ×2→ the Door —then enters→ the Interior. Its causal predecessor is that the Watcher has stopped.
- ◻ A Strike —emits→ a Cue. The onset frame equals the contact frame, ±1 frame.
- ◻ The Watcher —attends-to→ the Actor. The head turns toward the stoop by local 3.5 s and is held until the entry.
- The Door —opens-after→ Strike₂, via `EraWorld.door_mechanism`:
  - 1959: `hand`, a hinged swing inward.
  - 2009: `chain`, a hinged swing stopped at about 25° by a chain, and the bird squeezes through.
  - 2059: `listen`, a state machine `closed → listening → open`, which slides on rails.
- ◻ EraWorld —renders→ Version through a separate plate, light, sound rule set and puppet-casting. The event times are shared and stay unchanged.

### 3.3 Central operation: KNOCK(actor, door) → OPEN(door) → ENTER(actor)

**Typed preconditions:**
1. `actor.pose.root` is on the landing tread, and the beak-tip reach is ≥ the distance to `door.leaf` along the head arc. Measured as the beak tip lying inside the door-leaf mask on contact frames.
2. `door.state == closed`, and the leaf mask is fully opaque in the holdout DAG (the door is in front of the interior).
3. `watcher.state == stopped`, with its head piece rotated toward the stoop, at t < 6.00.
4. There are exactly two strikes with Δt = 0.32 s ± 1 frame, each with `contact = true`.

**Observable consequences:**
- Two recoils, visible in frames f(6.00)+1..+2 and f(6.32)+1..+2.
- Two transients in the audio envelope at 6.00 s and 6.32 s, ±42 ms.
- The leaf starts moving no earlier than 6.32 + 0.4 s.
- The interior black mass grows.
- The bird's alpha is progressively removed by the jamb holdout until 0 px are visible at 10.0 s.

**Counterexamples (which must *not* open the door):**
- (a) The same head rotation with the beak short of the leaf, so `contact = false`. Example: a peck at the tread. It is a peck, not a knock.
- (b) Three strikes, or one, or two strikes 0.6 s apart.

In the 2059 version, (b) is staged deliberately as a counterexample beat, at local 4.6–5.2 s. The bird pecks once at the glass while climbing and arrives one tread too early. One sensor dot lights, then flashes off and the door stays shut. After that comes the real "tok . tok", which lights two dots and opens the door.

This makes the 2059 affordance falsifiable on screen: one strike → refused; two in rhythm → open.

**Replay and alternate views:**
- **Equivalent.** Shots A, B and C of one version are three views of one event score. The diagnostic render (1959 in silhouette theatre) replays the identical score, so the event frame numbers are equal by construction.
- **Divergent.** Only the door mechanism, the light and shadow, and the sound timbre differ. The 2059 counterexample peck is an *added* event and does not move any protected event.

## 4 · Invariants (protected beats and their observable signatures)

| ID | Event | Local time (s) | Signature, checkable in every version and in the diagnostic |
|---|---|---|---|
| E1 | `walkin` | 0.0–3.0 | The watcher's shadow slides along the pavement/treads. The rooster hops up the treads, one tread per 8 frames, on twos. |
| E2 | `notice` | 3.5 | The watcher's shadow stops, and its head piece rotates toward the bird (≥ 12°). It holds until 10.0. |
| E3 | `strike1` | 6.00 | Beak tip inside the leaf mask, plus the audio onset. |
| E4 | `strike2` | 6.32 | The same, 8 frames after E3. The same pitch interval as E3: strike 2 is +3 semitones above strike 1 in every era. |
| E5 | `open` | 7.0–8.5 | The leaf moves by the era's mechanism. The interior dark mass appears. |
| E6 | `enter` | 8.5–10.0 | The bird crosses the sill. The jamb holdout occludes it to 0 px visible. |
| E7 | `goes_on` | 11.0–15.0 | The wide view shows an empty stoop. The watcher's shadow resumes and exits. |

Other invariants:
- **Separate variables.** `era` (1959/2009/2059), `genre_tone` (deadpan in all three) and `render_technique` (photo-cutout FK in V1–V3, and silhouette theatre in the diagnostic D) are tracked as separate fields in each version manifest.
- **Numeric invariants:**
  - The FK bone lengths are constant: the distance between pivots of a child and its parent varies by ≤ 0.5 px across all frames.
  - The beak tip lies inside the door-leaf mask on the E3 and E4 frames.
  - The bird's alpha is 0 px outside the jamb at E6 end.
  - The audio onset is at E3/E4 ±1 frame.
  - The four manifests share the event IDs E1–E7 with identical frame numbers.
- **Change control.** Changing any E-time makes a new common revision (`score-rN`) for every unit.

## 5 · Timed sequence (Hard proof: three versions of 12–18 s, plus the diagnostic)

The total is 68.0 s at 24 fps. The global knock times (E3) are 9.0 s, 25.0 s, 41.0 s, and 57.0 s in the diagnostic.

Each version is 15.0 s:
- **Shot A, 0–5.0 (wide).** The plate shows the stoop at sidewalk level, with a 1.5 % slow push.
- **Shot B, 5.0–11.0 (close).** The door and landing, from the same plate at full resolution or a matched second plate.
- **Shot C, 11.0–15.0 (wide again).** The same framing as shot A.

| Global | Section | On screen | Heard |
|---|---|---|---|
| 0.0–2.0 | Title | A handmade title card: the black field, plain sans "A MORNING STROLL", and small type "after Grant Orchard (2011)". | Silence, then the room tone of V1 fades in. |
| 2.0–3.0 | Card "1959" | The year in white sans on black, fading. | 1959 street ambience. |
| 3.0–8.0 | V1·A | **Rizzuto stoop plate** (ppmsca.70651). The watcher's long morning shadow slides up the treads from bottom-left and stops (E2 at 6.5), and its head turns. The rooster hops up treads behind the near lace railing (occluded by the baluster holdout), with a contact shadow and a hard cast shadow. | Street ambience (a 1950s city clip), footsteps stopping at 6.5, two soft clucks. |
| 8.0–14.0 | V1·B | **Top landing and panelled door** (the ppmsca.70651 master crop, or a matched Rizzuto doorway). The bird arrives on the landing. **E3 9.00 / E4 9.32** beak strikes on wood. The door swings in (10.0–11.5) on an unseen hand, as a homography-swung leaf with a black hall behind it. The bird steps over the sill and is swallowed by the jamb (11.5–13.0). | "tok . tok", a real knock on wood. A latch click, a hinge creak, a cluck inside, the door bump. |
| 14.0–18.0 | V1·C | The wide again: an empty stoop with the door top just visible ajar. The watcher's shadow resumes and slides out. | Footsteps resume, ambience. |
| 18.0–19.0 | Card "2009" | | |
| 19.0–24.0 | V2·A | **Highsmith Philadelphia row-house plate** (highsm.56276, brick, white steps, pale blue door), in colour daylight. The watcher's shorter noon shadow. The colour rooster (a CC white chicken) hops up the white treads, behind the iron handrail holdout. | A 2000s city ambience recording: traffic and a distant siren. Footsteps stop at 22.5. |
| 24.0–30.0 | V2·B | Close on the blue door. **E3 25.00 / E4 25.32**. The door opens about 25° and stops on a chain (handmade chain piece). The bird squeezes through the gap and is occluded by the leaf and the jamb. | "tok . tok", the same rhythm and interval, a hollower door. The chain snaps taut, a cluck. |
| 30.0–34.0 | V2·C | The wide: the door left ajar on its chain. The watcher's shadow leaves. | Ambience. |
| 34.0–35.0 | Card "2059" | | |
| 35.0–40.0 | V3·A | **A glazed modern entrance** (a CC/PD Commons photo of an entrance up a few steps with an automatic sliding door), cold dusk light. A very long low-sun watcher shadow across the steps, after AK17. The same colour white chicken. At 39.6, a counterexample peck on the glass: **one** sensor dot lights, then blinks off and the door stays shut. | Low air-handling hum and wind. A single glass tap at 39.6 and a low "denied" two-tone (handmade). |
| 40.0–46.0 | V3·B | Close on the door with a handmade 7-dot sensor strip above it. **E3 41.00 / E4 41.32** taps on glass, and two dots light in rhythm. The door answers with a chime in the same two-note interval, and the leaf **slides aside by itself** (42.0–43.5). The bird walks in over the threshold rail and is occluded by the frame. The leaf slides shut behind it. | "tok . tok" on glass, then a synthetic chime echoing the interval (the 2059 door's voice), then the pneumatic slide. |
| 46.0–50.0 | V3·C | The wide: the door shut, the dots dark. The long shadow leaves. | Hum and wind. |
| 50.0–51.0 | Card "1959 · diagnostic: silhouette" | | |
| 51.0–66.0 | D | **Diagnostic.** 1959 re-rendered in Reiniger silhouette theatre. The same GrabCut masks are filled black as card pieces with grey split pins on a backlit warm-paper ground, and a black-card stoop is traced from the plate's tread lines. The FK animation curves and the event times are identical (E3 at 57.00). | The identical 1959 stems. |
| 66.0–68.0 | End card | "Foraged: Library of Congress, Wikimedia Commons, movingimagearchive.com. See credits." | Fade. |

Every version shows E1–E7 on its own plate. The 2059 version exploits the new environmental affordance, a door that listens, and it shows that affordance refusing one strike before accepting two.

**Captions.** There is no dialogue and no spoken voice. This is declared. The only text is the title, the era cards and the end card.

## 6 · Elements: FORAGED or HANDMADE

| Element | Status | Source / what to look for |
|---|---|---|
| 1959 plate | FORAGED | LoC **ppmsca.70651**, *[Detail of stoop showing staircases and decorative handrails]*, Angelo Rizzuto, July 1959, Anthony Angel Collection, item 2020636795. Status: "No known restrictions". **Re-verify on loc.gov.** Fetch the master through IIIF, `tile.loc.gov/image-services/iiif/service:pnp:ppmsca:70600:70651/full/pct:50/0/default.jpg` and a full-resolution region crop of the top landing and door. If the door is too cut off, search LoC "Rizzuto doorway / entrance / stoop" (ppmsca, no known restrictions) for a matched door plate at the same light. Spare: `70651r` (a second stoop). |
| 2009 plate | FORAGED | LoC **highsm.56276**, Carol M. Highsmith Archive. Status: PD/no known restrictions. **Record its actual photo date.** It has a stoop and a door in one frame. Get the hi-res region via IIIF. |
| 2059 plate | FORAGED | Wikimedia Commons: a CC BY / BY-SA / CC0 photo of a contemporary apartment or office entrance with **automatic sliding glass doors** reached by a few steps, ideally dusk or cold light, and frontal or 3/4 at eye level. Licence from extmetadata. |
| Rooster 1959 | FORAGED | LoC **stereo.1s08734**, *[Portrait of a rooster]*, Schreiber & Sons, 1870s. Status: PD. Use the left lens at full res through IIIF. It is a white bird with a dark tail, facing right. |
| Chicken 2009/2059 | FORAGED | Commons: a CC/PD **colour photograph of a white hen or rooster in clean side profile**, facing right, legs visible, on a plain ground. Same morphology so it fits the same joint graph. If none passes, reuse the 1870s rooster and record why. |
| Watcher shadow | FORAGED | The silhouette of a standing or walking woman cut from **LoC OWI 2017861981** (bus terminal, c.1943, FSA/OWI, PD US Gov; photographer unverified, record as such). Alternatively, a Rizzuto pedestrian. Only its *silhouette* is used, as a cast shadow, with the head as a separate piece. |
| Door leaf, jamb, railing holdouts | HANDMADE from foraged plates | Matte pieces cut from each plate (#29, #45): leaf, jamb, sill, baluster and handrail holdouts, and tread-nose lines. |
| Interior dark hall | HANDMADE | A black field with one soft slit of warmer light, built per era behind the leaf. |
| 2009 door chain | HANDMADE | A small drawn-and-shaded chain object: 6 links, catenary, then taut. |
| 2059 sensor strip | HANDMADE | A 7-dot LED strip object (brushed-metal bar plus dots) mounted above the door and lit by the state machine. |
| Cast and contact shadows | HANDMADE | Computed from the mattes: shear by light direction, a sawtooth break across the risers, opacity of 65–80 %. |
| Diagnostic stage | HANDMADE | Black card silhouettes (the same masks), a black-card stoop traced from the 1959 tread lines, and backlit paper with fibre noise. |
| Knock 1959 | FORAGED | Commons audio, CC0/BY/BY-SA: *knock on a wooden door*. Isolate one strike. Two strikes 0.32 s apart, the second pitched +3 semitones (resampled). |
| Knock 2009 | FORAGED | Commons: a knock on a hollow or painted door, at the same rhythm and interval. Fallback: the 1959 strike band-limited, recorded as a fallback. |
| Knock 2059 | FORAGED, with HANDMADE fallback | Commons: a knuckle or tap on glass. Fallback: `kit.Mix.click`. |
| Door voice 2059, denied tone | HANDMADE | A synthetic two-note chime at the same +3-semitone interval (`kit.Mix.note`/`bell`). The denied tone is the same interval descending. |
| Chicken clucks | FORAGED | Commons: chicken or hen clucking, CC0/BY/BY-SA. |
| Door sounds | FORAGED | Commons: creak and latch (1959), chain rattle (2009), sliding door (2059). Use handmade synth only where nothing passes. |
| Street ambience 1959 | FORAGED (primary: Moving Image Archive) | Run `forage.py "street|sidewalk|neighborhood|city|traffic"` and choose a 1940s–50s clip with real street sound by *listening*. Candidates are `e27fc433` (*According to Plan*, 1952) or the `3543b210` street (1938). Credit "via movingimagearchive.com". |
| Ambience 2009/2059 | FORAGED | Commons city ambience field recording. 2059: hum and wind, foraged, or `kit.Mix.room`/`wind`. |
| Title and cards | HANDMADE | Typeset with kit fonts. |

No material from Orchard's film itself is used. The reference stills are only compared against and are never copied, traced or composited.

## 7 · AESTHETIC TARGET

**Primary reference:** `orchard3.webp`, the 1959 section. It was studied with PIL, at 1000x563:

| property | measured value |
|---|---|
| Medium | Black ink line on white paper, with grey washes and big flat black masses: the stoop's shadow side, the doorway and the vignette corners. |
| Colour | Fully neutral (mean of R−B = 0.0). |
| Palette (6-colour quantise) | #141414 (largest), #bfbfbf, #e6e6e6, #484848, #f4f4f4, #7c7c7c |
| Tone | Bimodal. 21 % of pixels < 40 and 35 % > 200. Median 153. Percentiles p1/p5/p25/p50/p75/p95 = 3/7/54/153/221/246. |
| Vignette | Heavy: corner mean / centre mean = 0.18. |
| Grain | Fine film grain (small-difference std ≈ 3.8 levels). |
| Light | Graphic and frontal, with no modelling, and the black masses carry the depth. |
| Framing | Sidewalk level, low camera at about chicken height, a one-point street. The chicken is small, about 20 % of frame height, in the lower middle, seen from behind. |
| Typography | None in frame. |
| Pacing | Deadpan holds, limited animation and a static camera. |

**Gallery references (the era ladder):**
- **`orchardAK08`, 2009.** Flat saturated colour, dark (mean 71; 44 % < 40) with neon accents. Side-on elevation of a façade and stoop. The chicken is small and white on a grey sidewalk.
- **`orchardAK17`, 2059.** Photoreal and desaturated grey-green, with palette #a0a99b, #0e0b0a and #463d3a. Mean 93, and only 2 % > 200. A *very long low-sun cast shadow* of the watcher across the paving reaches the chicken.

**How we arrive at it with real material and real technique (no filter costume):**
- **1959.**
  - The Rizzuto print is real B&W, but soft (p5 = 78, with no blacks). Deep blacks must come from *real light-logic objects*: the hard cast shadow of the watcher laid over the treads, the stoop's own shadow side, the black hall behind the opening door, the undersides of the treads, and a lens vignette.
  - Unify with one global tone curve only (levels and contrast). No posterising, no edge-ink and no fake line.
  - Pick crops where the lace railing (white on dark brick) gives the reference's graphic white-on-black.
  - Grain only to match the reference's measured fine grain over the composited puppet so it sits in the print.
  - Framing: shot A low and tight on the treads, with the bird at 15–25 % of frame height, matching the reference scale.
- **2009.** The real colour photograph, graded only to unify the puppet with the plate. Side-on elevation framing echoes AK08.
- **2059.** A real cold-light photo, desaturated toward the AK17 palette by a single unify grade. The long shadow is computed from the watcher's silhouette at a low sun angle.
- **Typography.** Plain neutral sans (kit) for the cards only, white on #141414. Nothing in-frame.
- **Rhythm.** A static camera with a 1.5 % push, the bird animated on twos (12 drawings/s) with holds, and the watcher's stop held still.

**Colour sampling to verify (each unit and the editor):** quantise film frames to 6 colours with PIL and report them beside the reference palette.

## 8 · Technique SCIONs (from swarms.json, prompts read in full)

| id | title | why | applied, shot by shot |
|---|---|---|---|
| **29** | GrabCut — Cutout Extraction Swarm | Every actor and every holdout is a figure extracted from a real photograph: the rooster from an albumen stereo card, the woman from an OWI negative, and the door leaf and railings from the plates. #29's bar (no background islands, retained thin parts, no halos, failure masks exported) is exactly what makes a cut-out read as *in* the plate rather than pasted on. | All shots. Rooster and chicken: box plus scribble seeds, then `cv2.grabCut`, then a 5–7 px band refine, with legs and toes, comb and beak tip retained. Watcher: silhouette only. Plates: leaf, jamb, sill, balusters and handrail as RGBA pieces with contour masks and original-coordinate transforms. Export the failure masks. |
| **32** | Forward Kinematics — Hierarchical Body Logic | The knock is a joint act: the head rotates about the neck while the body braces on the legs. The climb is a hop cycle of hip and knee. #32's invariants (constant bone lengths, no head/neck detachment, correct multiply order, consistent root motion) are what make a single photographed pose *act* with weight. | Rooster graph: root/body → neck → head(beak); body → hip_L → shank_L → foot_L; and hip_R likewise; tail as a body child with lag. Watcher-shadow graph: body → head. V·A: hop cycle, 6 key poses (crouch, push, air, land, settle, hold), one tread per 8 frames, on twos. V·B: strike = head −22° about the neck pin over 2 frames, recoil +6° over 2 frames, twice, 8 frames apart, then step-over-sill. V3·A: the single peck. D: the same curves. Tests: bone-length report by joint. |
| **45** | Occlusion Compositing — Who Is In Front? | The proof's "enter an unlikely place" is an occlusion event: the bird must pass *behind* the near railing, *in front of* the treads, and finally *behind* the jamb into the dark. Contact shadows must match the light of the real plate. | Per shot, a layer DAG: plate, then interior/hall (B), then the leaf (when open), then the cast shadows, then the bird, then the baluster/handrail holdouts (A), then the jamb/sill holdouts (B), then the vignette and grain. Occlusion assertions per frame, with crossing intervals annotated (bird behind the railing in A; 0 px past the jamb by E6 end). Contact shadow under the feet on each tread. |

Also consulted, but not chosen as units: #44 Multiplane (only the 1.5 % push and the separation of shadow and bird planes), and #48 State Machines (the 2059 door's `closed → listening → open | refuse` is a 4-state table owned by the puppet unit).

## 9 · Swarm units (section 5 merged: 3 units, plus the editor and the reviewer, who run separately)

Every unit:
- works against revision `plan-r1` / `score-r1` (the E-table in §4);
- saves media under `films/sources/a-morning-stroll/<role>/`;
- writes credit-ready records (`title, author, license, license_url, source_url, file_url, used_as`) into its own output JSON;
- verifies every licence at the source (Commons extmetadata, or the loc.gov item page "Rights");
- downloads a combined total under ~75 MB;
- sends User-Agent `oulipo-film-research/1.0`;
- backs off on HTTP 429.

### U1 · `story-plates`: story editor, plus plates and holdout mattes (#29 for the plates, #45 DAG data)

**Freezes the encounter.** Writes `beatmap.json` with the event IDs E1–E7, their local and global frame numbers, and the separate `era`, `genre_tone` and `render_technique` fields per version (V1, V2, V3, D).

**Forages and verifies the three plates:**
- 1959: the Rizzuto master by IIIF, plus the door/landing crop or a matched Rizzuto door plate;
- 2009: Highsmith 56276 hi-res;
- 2059: a Commons sliding-glass entrance.

**Prepares per-plate assets:**
- shot A/B/C crops at 960x540, with the camera push;
- the unify tone curve, with 1959 meeting the §7 numbers;
- holdout mattes: balusters and handrail, leaf, jamb, sill;
- the door hinge or slide geometry (the 1959/2009 hinge axis; the 2059 rail);
- the tread-nose polylines and the light direction for the shadows;
- the interior hall layers;
- the 2009 chain and the 2059 sensor strip objects.

**Output.** `films/swarm/a-morning-stroll/plates.json`. It holds the manifest of plates, crops, mattes, geometry and credits. It references `beatmap.json` and `films/sources/a-morning-stroll/plates/`, and includes a contact sheet of each plate's A and B crops beside `orchard3`.

### U2 · `puppet`: cut-out and articulated animation (#29, #32, #45 compositing tests, and the #48 door table)

**Extracts** the rooster (1959) and the colour chicken (2009/2059), and the watcher silhouette, with GrabCut. Exports the RGBA pieces and the failure masks.

**Builds the FK rigs** (`rig.json`: joints, pivots in piece coordinates, bone lengths) and a pose library. It animates the frame-by-frame performance for every shot from `beatmap.json`:
- the hop cycle, the strikes, the recoil, the step-over and the counterexample peck;
- the watcher's walk, stop and head turn;
- the door leaf motion (hinge homography, chain stop, slide), and the 2059 state machine.

**Exports** per-shot pose tracks (`tracks/<shot>.json`: per-frame joint angles and root position) and a renderer function or module the editor calls. Puppet code lives in `films/sources/a-morning-stroll/puppet/` and is imported by the film script.

**Tests:** bone-length invariance, beak tip in the leaf mask on E3/E4, zero bird px past the jamb at E6 end, and no background islands.

**Renders** `knock-proof.mp4`: V1·B alone, 6 s with sound, as the test shot. It also renders the `baseline.mp4` sticker version.

**Output.** `films/swarm/a-morning-stroll/puppet.json`. It holds the rig, the tracks index, the test results labelled measured or structurally verified, the proof clip paths and the credits.

### U3 · `sound`: recurring cue and stems

- Forages knock-on-wood, hollow door and glass tap; clucks; door creak, latch, chain and slide; and the ambiences. The 1959 street sound comes from the Moving Image Archive first (listen to candidates), with Commons for the rest.
- Builds the **"tok . tok" cue**: two strikes 0.32 s apart, the second +3 semitones, for each era timbre, plus the handmade 2059 door chime and the denied tone.
- Writes per-version stems (`v1.wav`, `v2.wav`, `v3.wav`; D reuses v1) placed exactly on the beatmap times, with an onset-detection check (onsets at E3/E4 ±1 frame).

**Output.** `films/swarm/a-morning-stroll/sound.json`. It holds the cue sheet (event, time, file, gain), the source ledger and credits, and the onset test results. Stems go in `films/sources/a-morning-stroll/sound/`.

### Editor / assembler (run by the workflow)

Writes `films/a-morning-stroll.py` with `kit.Film`, composites per the U1 DAG and the U2 tracks, and mixes the U3 stems. It merges the credits into `films/credits/a-morning-stroll.json` and writes `films/notes/a-morning-stroll.txt` (60–110 words, forage vs handmade). It renders the film (≤ 75 s, ≤ ~6 MB), plus `ledger.json` (the per-version manifests sharing E1–E7) and `compare-1959.jpg`, `compare-2009.jpg` and `compare-2059.jpg` (each the film frame beside its reference).

## 10 · Acceptance bar (falsifiable; for a fresh critic watching the film and reading its ledger)

1. **The repeated act.** With the sound **muted**, a viewer can mark three knock moments at about 0:09, 0:25 and 0:41, and say "two beak strikes" for each. In the ledger, E3 and E4 are 8 frames apart in V1, V2, V3 and D, and the beak tip is inside the door-leaf mask on those frames (measured).
2. **The matched cue.** The sound has two transients at each E3/E4, ±1 frame, in all four sections, and the second is about +3 semitones above the first in each era (measured by onset and pitch estimate). It is wood, then hollow door, then glass: recognisably the same rhythm in different materials.
3. **Real animation.** In every shot B, the rooster changes pose frame to frame. At least 3 distinct joint configurations (crouch or hop, strike, recoil) are visible in 1 s around E3. The head stays attached (no neck gap) and the bone lengths vary by ≤ 0.5 px (from `puppet.json`). The bird passes *behind* the real railing in V1·A and disappears behind the jamb by E6 end, with no popping.
4. **Escalation earned.** In V3 a single peck lights one sensor dot and the door stays shut. Then two strikes light two dots and the door slides open with **no hand or person** visible. V1 and V2 doors swing on a hinge, and V2 stops on a chain.
5. **Aesthetic, 1959 side-by-side.** `compare-1959.jpg` puts film frame 9.0 s beside `orchard3.webp`. The film frame:
   - is neutral (mean |R−B| < 3);
   - has ≥ 15 % of pixels < 40 and ≥ 20 % > 200;
   - has its largest black mass ≥ 8 % of the frame, from a real shadow or doorway;
   - has a corner/centre luma ratio ≤ 0.6;
   - has the bird at 15–40 % of frame height.

   A critic judges whether it reads as the same high-contrast black-and-white graphic world without any line-art filter (perceptually judged), and confirms in the ledger that the plate is a real 1959 photograph (structurally verified).
6. **Aesthetic, era ladder side-by-side.** `compare-2009.jpg` and `compare-2059.jpg` put frames 25.0 s and 41.0 s beside `orchardAK08` and `orchardAK17`:
   - 2009 is clearly colour, with mean HSV saturation > 0.25 and side-elevation staging.
   - 2059 is cool and desaturated, with mean saturation < 0.2 and < 5 % of pixels > 200.
   - In 2059 the watcher's cast shadow spans ≥ 40 % of frame height in V3·A.
7. **Era vs technique.** The diagnostic D has identical E-frame numbers to V1 (ledger) and a visibly different technique (black-card silhouettes on backlit paper). A viewer can say the event is unchanged and only the rendering changed.
8. **Provenance.** Every on-screen and audible foraged item appears in `films/credits/a-morning-stroll.json` with a licence in {PD, CC0, CC BY, CC BY-SA}, verified at the source, and the archive shots carry movingimagearchive.com credits. The total runtime is ≤ 75 s and the file is ≤ ~6 MB.

## 11 · Risks and fallbacks

- **The 1959 door is cut off in ppmsca.70651.** U1 tries the IIIF full-resolution region first, then a matched Rizzuto doorway. If neither is usable, shot B uses the landing crop with the door leaf rebuilt from the visible panels: a handmade extension, recorded.
- **Commons rate-limits (429).** Back off exponentially. The 2059 plate can fall back to LoC (a Highsmith modern entrance with glass doors).
- **Rooster light mismatch.** Add a contact shadow, a unify grade toward the plate's black and white points, and grain match. Do not stylise.
- **The single photographed pose.** FK carries the act. Use #39 substitution only if a turn is needed; none is planned.
