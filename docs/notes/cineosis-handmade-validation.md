# CINEOSIS, handmade: validation record

This record covers the handmade film: hand-authored passages for the 39 signs outside the pilot: two per sign, three for 34b (79 passages), plus the six pilot passages carried over (signs 2, 28, 29, 38, 39, 42).

## What is observed and what is generated

- **Observed:** every background is an unaltered archival clip from the cineosis-lab periodic table, trimmed to a cut-free segment. Where noted, it is slowed (frame-blended), time-remapped (frames held or skipped to sync an event to her action), or cropped (a push-in). No plate pixels are painted or regenerated, except the labelled overlays below.
- **Generated:** the figures (Bola, and Shim in 14.0 and 14.1) are a rigged 2D crash-test-dummy character. Every pose is keyed by hand in code (key poses, contacts, timing), and in-betweens are interpolated by the rig. No image or video generation model and no model training were used.
- **Generated, compositing:** shadows, contact darkening, tone and grain matching, front mattes keyed from the plate (smoke, water, crowd, hands), and the drawn props or marks listed per passage (trails, crumbs, footprints, placards, glasses, hearts, wind streaks, a shelf, a parapet). The camera roll in 27.4 and the push-in crops are also generated.
- **Sound:** the plate's own track where it has one, plus synthesized footsteps, knocks, tones and hums.

## Shared integration standard (all handmade passages)

Each passage carries:
- a contact shadow and a cast shadow along the plate's key light, with density set from the plate's contrast;
- her tones mapped into the plate's black and white points;
- grain, and softening through the plate's native resolution.

Exceptions are noted per passage (void floors, night skies, screen-lit faces).

## Reviews that took place

Each review was done by a fresh agent that had not seen the work being made. The agent inspected the actual rendered frames (contact sheets and dense crops) and described each passage before reading its intended scenario.

- **Round 2 (signs 1–8, 14 passages):** about 4 read fully and 7 partly. This led to the shared integration standard and to rewrites of 1.1, 1.2, 4.0, 5.2, 5.4, 6.0, 7.1 and 7.2.
- **Round 3 (signs 1–13, 24 passages):**
  - Blind: 8 READS, 13 PARTLY, 3 FAILS.
  - Against intent: 4 matched, 13 partly, 7 missed.
  - Fixed: props made readable (10.3 footprint, 7.2 crumbs, 3.0 copies, 12.3 figure); shadow directions (7.1, 8.1, 4.0, 8.0); support (11.0, 11.4, 5.4); cause and effect timing (10.4 stamps, 12.0 dive, 11.0 jump, 1.1 steering); 5.2 rewritten as a walk toward camera; wind made visible in 9.2.
- **Round 4 (signs 13–41, 46 passages):**
  - Blind: 17 READS, 23 PARTLY, 6 FAILS.
  - Against intent: 13 matched, 24 partly, 9 missed.
  - Fixed: push-ins where the figure was too small (23.0, 24.2, 31.5, 35.0, 35.1, 41.1, 37.2); softer, attached shadows (14.1, 32.3, 23.2); bigger signature gestures (15.3 laugh, 35.1 head dip, 31.5 stamps, 18.4 frame and turn, 16.0 side kicks); 32.3 made a continuous stroll; 26.1 orbit smoothed; 22.4 run lengthened.
- **Not reviewed:** the round-4 fixes and the signs 1–13 fixes have not been re-reviewed. Signs 34b, 43 and 44, the second passages of 34a and 40, and 17.4 and 36.4 have had no review.

The assembled film is cineosis-handmade-film.mp4: 85 passages (79 handmade and 6 pilot), 21.8 minutes, with a title card per sign.

## Passages

| sign | passage | plate | generated |
|---|---|---|---|
| 1 | 1 So · Solid perception — plate 1.1 (Medicus World's Fair, peephole vignette) — v3, 15 s | 9.5 s slowed 0.62x. The view inside the circle is scaled 1.4x and shifted with her hips (5.5 px per cm): when she hauls left the hall swings left, when she hauls right it swings right. |  |
| 1 | 1 So · Solid perception — plate 1.2 (6 1/2 Magic Hours, through the windscreen) — v2, 15 s | 8.5 s slowed 0.55x with blending; the cabin (visor) is template-tracked and carries her. |  |
| 3 | 3 Ga · Gaseous perception — plate 3.0 (Fitting Faces, a tray of lenses) — v2, 14 s | 6.5 s slowed 0.45x. Ten lens copies, each with its own magnification (some inverted) and delay (2–30 frames), clipped to its lens; Bola herself drawn larger. |  |
| 3 | 3 Ga · Gaseous perception — plate 3.1 (the burning airship) |  |  |
| 4 | 4 Ic · Icon — plate 4.0 (a boy's face, eyes lowered and raised) — v2, 12.5 s | 5 s slowed 0.4x. Staging (v3): proscenium, Bola large between his eyes so her lids read, facing us; shadow cast onto his face by the plate's key light (from the left), present from the first frame. |  |
| 4 | 4 Ic · Icon — plate 4.2 (a boy's upturned worried face) — v2, 15 s | 8.4 s slowed 0.55x. Staging: proscenium beside the face (both faces in view), her shadow on his cheek. |  |
| 5 | 5 Dv · Dividual — plate 5.2 (a street crowd streaming toward the camera) — v2, 12.5 s | 7.1 s slowed 0.44x; static camera. Staging: Bola in the front row, full figure, shadow on the street. |  |
| 5 | 5 Dv · Dividual — plate 5.4 (an audience before one screen) — 14 s | 10 s cut-free audience shot, slowed 0.7x. Staging: Bola seated among the heads, back to us, rim-lit by the screen; the row in front keyed over her body. |  |
| 6 | 6 As · Any-space-whatever — plate 6.0 (a dust storm whites out the land) — 15.5 s | 7.7 s slowed 0.5x; white haze over a dark strip of ground, one tiny figure far off that fades out. |  |
| 6 | 6 As · Any-space-whatever — plate 6.5 (dust drifting over a field) — 15.5 s | 7.5 s of grass in drifting dust; plate time is remapped piecewise so the three puffs land on her three shields. |  |
| 7 | 7 Sy · Symptom — plate 7.1 (a man crouched on a gravel slope tearing at the ground) — 13 s | 4.9 s slowed 0.38x. Staging (v2): Bola in profile facing him, same plane; front hand digs, back hand flings; gravel spray drawn as ballistic stones; shadow and tone by the shared standard. |  |
| 7 | 7 Sy · Symptom — plate 7.2 (a man's hands taking the last crumbs from a plate) — 16 s | 7.7 s slowed 0.48x. Staging: Bola small, in profile at the left edge of the plate, the rim at her chest. |  |
| 8 | 8 Fe · Fetish — plate 8.0 (a carved figure, 'Cocoon', lit alone) — 16 s | 6.6 s slowed 0.41x. Staging: Bola in profile on the plinth, left of the statue; lit from the left like it. |  |
| 8 | 8 Fe · Fetish — plate 8.1 (polished black shoes at floor level) — 16 s | 10 s slowed 0.62x. Staging: Bola the height of the toe cap, in profile against the right shoe's toe. |  |
| 9 | 9 Or · Originary world — plate 9.2 (a dark farmhouse under a black tree, clouds racing) — 16 s | 10 s slowed 0.62x. Staging: Bola in profile in the foreground grass, walking left toward the tree; foreground grass keyed over her feet. |  |
| 9 | 9 Or · Originary world — plate 9.3 (a hillside burning under black smoke) — 15 s | 6.8 s slowed 0.45x. Staging: Bola in profile on the dark near slope, facing the fire, lit orange from it. |  |
| 10 | 10 Il · Index of lack — plate 10.3 (from above, a hand brushing sand off something buried) — 17 s | the first 7.3 s (before the tray is lifted), slowed 0.43x. Footprints drawn in the sand (impressions with a lit far rim). |  |
| 10 | 10 Il · Index of lack — plate 10.4 (night: dish antennas light up one by one) — 16 s | 9 s; plate time is remapped piecewise so each dish comes on exactly as one of her steps lands. Her own brightness follows how much of the row is lit. |  |
| 11 | 11 Ie · Index of equivocity — plate 11.0 (a box with a dark lens; a hand plugs it with a white disc) — 14 s | 11.3 s, time-remapped so the disc lands on the lens just as she leaps back. Staging: proscenium beside the lens, her shadow on the box. |  |
| 11 | 11 Ie · Index of equivocity — plate 11.4 (night, outside a box office: a woman down on the pavement, a man in the doorway) — 16 s | 9.6 s slowed 0.6x. Staging: Bola beside the man by the doorway, behind the woman's path; his height as her scale reference. |  |
| 12 | 12 Ve · Vector — plate 12.0 (a model intersection from overhead; across a cut, a pile-up) — 16.5 s | 7.4 s, remapped: before the cut slowed so the cars come at her; the cut (the crash) lands just after she dives clear. |  |
| 12 | 12.3 Vector: the rail switch | aerial over a rail yard, 7.6-13.1 s, slowed 0.23x, tracked (tr123). | Bola, her shadow, the white trail. Observed: the plate. |
| 13 | 13.1 Milieu: the town | slow pan over an industrial town (Mechanical Engineering at duPont), 7.1-22.7 s, real time (0.91x). | Bola, her shadow, and the rooftop parapet she stands on. Observed: the town plate. |
| 13 | 13.2 Milieu: the coal | coal cars filmed from a moving car (How Our Country Grew), 0.5-5.3 s, slowed 0.3x. | Bola, her shadow, the thrown lumps. Observed: the plate. |
| 14 | 14.0 Binomial: the placards | a picket line of pencil workers outside a factory (Working Together), 0.05-6.2 s, slowed 0.42x, pan tracked by phase correlation (tr140). | both figures, their shadows, the two placards (blank scrawl, no words). Observed: the picket line and its placards. |
| 14 | 14.1 Binomial: the line | a 1938 town football game (Ivan Besse collection), 4.05-6.2 s, slowed 0.16x, tracked (tr141). | both figures, their shadows. Observed: the plate (players in the distance). |
| 15 | 15.3 Imprint: the laugh | a worker in a hard hat laughing, in profile (Twenty-Four Hours of Progress, Part II), 0.05-3.0 s, slowed 0.27x. | Bola, her shadows on the image and the floor. Observed: the plate. |
| 15 | 15.4 Imprint: the nerves | a young man on a sofa talking about going steady (Going Steady?), 5.15-10.6 s, slowed 0.45x. | Bola and her shadow. Observed: the plate. |
| 16 | 16.0 Plastic figure: the chorus line | a chorus line kicking across a stage (Chevrolet Sales Convention Musical), 20.2-29.8 s, slowed 0.65x, tracked on the curtain (tr160). | Bola and her shadow. Observed: the plate. |
| 16 | 16.2 Plastic figure: the hourglass | a lecturer at a desk talking to camera beside a running hourglass (Coffee Break), 26.0-40.5 s, slowed 0.78x; camera static (checked by track). | Bola and her shadow. Observed: the plate. |
| 17 | 17.1 Theatrical figure: the figurine | a mechanical puppet stage with a turning Pegasus between two statuettes (amateur film, Medicus collection), 0.05-9.1 s, slowed 0.75x, tracked on the left arch (tr171), with a 1.7x push-in crop of the plate. | Bola, her contact shadow, the push-in. Observed: the plate. |
| 17 | 17.4 Theatrical figure: the casualty | a first-aid drill in a street during the 1934 San Francisco general strike, 3.0-5.85 s, slowed 0.25x, tracked on the pavement and folded blanket (tr174). | Bola and her shadow. Observed: the plate. |
| 18 | 18.0 Mise en abyme: the remote | a woman with a remote control watching a television that shows another scene (Television Remote Control (Tuner)), 0.05-16.3 s, real time. | Bola, her shadow, the blank of our picture. Observed: the plate (including its channel change). |
| 18 | 18.4 Mise en abyme: the frame | a photographer at a view camera on a dune crest with a model (THE PHOTOGRAPHER), 19.9-24.5 s, slowed 0.39x, tracked on the sand (tr184). | Bola, her shadow, two faint shutter blinks. Observed: the plate. |
| 19 | 19.0 Figure of the sublime: the kangaroo | a man floored in a boxing booth gets up dazed, stands, lunges and stumbles away (The Battling Kangaroo), 4.8-12.0 s, slowed 0.62x; silent. | Bola, her shadow, hop sounds. Observed: the plate. |
| 19 | 19.1 Figure of the sublime: the blast | Buster Keaton in The Balloonatic (1923) crouched in a thicket; a blast of smoke engulfs everything and he emerges blackened; 3.4-11.1 s, slowed 0.55x; silent. | Bola, her shadow, cough puffs. Observed: the plate. |
| 20 | 20.1 Figure of enfeeblement: the swimmer | surf boats crashing through breakers (Aqua Frolics), 0.05-7.9 s, slowed 0.55x. | Bola. Observed: the plate. |
| 20 | 20.2 Figure of enfeeblement: the grader | a motor grader rolling slowly down a desert road toward the camera (Oil Across Arabia), 0.15-8.4 s, slowed 0.53x. | Bola, her shadow, foot dust. Observed: the plate. |
| 21 | 21.1 Quotidian: the meal | a couple talking over a meal at a kitchen table (Inside/Outside: The Story of Food), 0.05-5.9 s, slowed 0.4x. | Bola and her shadow. Observed: the plate. |
| 21 | 21.4 Quotidian: the lawn | a boy mowing a lawn in front of a house (Health: Your Posture), 19.1-23.45 s, slowed 0.35x, tracked on the whole frame (tr214). | Bola and her shadow. Observed: the plate. |
| 22 | 22.0 Limit of the large form: the wreck | a pan along a house wrecked by a storm (Nieuwe stormramp in den Achterhoek), 5.0-10.3 s, slowed 0.29x, pan tracked (tr220); silent. | Bola and her shadow. Observed: the plate. |
| 22 | 22.4 Limit of the large form: the plane | a crop-dusting biplane flying low across a field toward the camera, which pans with it (Airport America), 4.75-9.6 s, slowed 0.36x, tracked on the field (tr224). | Bola and her shadow. Observed: the plate. |
| 23 | 23.0 Limit of the small form: the map | a close-up of a hand pressing pieces down on a map (Apollo 12: Pinpoint for Science), 0.05-5.6 s, slowed 0.36x, tracked on the map (tr230). | Bola and her shadow. Observed: the plate. |
| 23 | 23.2 Limit of the small form: the clues | tenement fronts behind a flowerbed; two women walk up the path to a door (Arteries of New York City), 3.4-10.9 s, slowed 0.6x, tracked (tr232). | Bola and her shadow. Observed: the plate. |
| 24 | 24.1 Limit of the action-image: the thinker | a philosopher in profile talking in front of a blackboard (Logic By Machine, Part II), 3.3-11.6 s (before the camera re-frames), slowed 0.54x. | Bola, her shadows on the tray and the board. Observed: the plate, including the chalk tray she stands on. |
| 24 | 24.2 Extreme limit of the action-image: the hole | the black mouth of a diversion tunnel blasted into rock, a drilling gantry at its foot (Boulder Dam), 4.65-9.15 s, slowed 0.26x. | Bola, her shadow, the pebble. Observed: the plate. |
| 25 | 25.0 Rich dream: the kaleidoscope | a kaleidoscope disc slides into a black field, turns, and slides away (What's It to You? Part I), 3.6-13.6 s, slowed 0.8x. | Bola (no shadow: the floor is black void). Observed: the plate. |
| 25 | 25.2 Rich dream: the ears | a constellation of photographed ears glowing in black around one huge ear (How the Ear Functions), 0.05-14.0 s, slowed 0.95x. | Bola, the ear's glow and the flare (added light), no shadow (void). Observed: the plate. |
| 26 | 26.1 Restrained dream: the wheel | a potter's wheel turning with a cup on it, out of focus (POTTERY, ca. 1926), 1.3-4.0 s, slowed 0.25x. | Bola, her shadow, the orbit. Observed: the plate. |
| 26 | 26.2 Restrained dream: the doze | a man reading the newspaper in an armchair while the camera drifts in (Programmer with Magic Memory), 25.2-38 s; plate time remapped: normal (0.8x), slowing toward a stop while she sleeps, then a jump forward of about 2.5 s when she wakes. Tracked on the ottoman, reduced to translation and scale. | Bola, her shadow, her little newspaper, the time remap. Observed: the plate. |
| 27 | 27.0 Movement of world: the crowd | Luna Park, Coney Island, at night; towers of light and a crowd drifting past in silhouette (Coney Island At Night), 10.4-14.7 s, slowed 0.35x. | Bola, her shadow, the drift. Observed: the plate. |
| 27 | 27.4 Movement of world: the tipping city | a street between skyscrapers in a canted low view (The Changing City), 0-4.3 s, slowed 0.35x; the camera roll and a 1.18x crop are generated in the composite. | Bola, her shadow, the roll. Observed: the plate. |
| 30 | 30.0 Forking paths: the mirror | a girl holding a hand mirror with her face in it (Going Steady?), 0.05-9.1 s, slowed 0.57x. | both figures (the double is a second instance set into the mirror and dimmed as if behind glass), her contact shadow. Observed: the plate. |
| 30 | 30.1 Forking paths: the two lines | a camera moving along a railway line toward a station where the tracks divide (Allegheny Portage Railroad), 15.5-21.3 s, slowed 0.35x, ground tracked (tr301). | both figures and their shadows. Observed: the plate. |
| 31 | 31.2 Mark: the houses | a pan along a street of identical new houses (According to Plan: The Story of Modern Suburbs), 0-4.4 s, slowed 0.25x, pan tracked (tr312). | Bola and her shadow. Observed: the plate. |
| 31 | 31.5 Mark: the ledger | a clerk at his desk making entries in a ledger (Two Pay Days, Part I), 0.05-8.1 s, slowed 0.6x. | Bola, her shadow, the stamp sounds. Observed: the plate. |
| 32 | 32.2 Demark: the chart | an animated chart of rows of identical worker figures; the top ones turn into stars and a caption appears (Finding Your Life's Work), 8.8-22.1 s of the clip, near real time. | Bola, her shadows on the chart and floor. Observed: the plate. |
| 32 | 32.3 Demark: the crossing | schoolchildren wait at the kerb; the policeman signals and they surge across the street toward the camera (Henry Ford's Mirror of America, Part II), 7.6-11.6 s, slowed 0.26x, pan tracked by phase correlation. | Bola and her shadow. Observed: the plate. |
| 33 | 33.4 Symbol: the watch | a man's fist with a wristwatch held over a machine (Bookkeeping and You), 3.2-6.1 s, slowed 0.23x. | Bola, her shadow, tick sounds. Observed: the plate. |
| 33 | 33.5 Symbol: the luggage | a pan along suitcases under a line of travel tags (6 1/2 Magic Hours), 0.05-5.9 s, slowed 0.4x, pan tracked by phase correlation. | Bola and her shadow. Observed: the plate. |
| 34a | 34a.0 Opsign: the shore | a figure in a sea-creature costume at the water's edge, a dark shape out in the surf (Alice in Wonderland, 1915), 2.8-9.8 s, slowed 0.45x. | Bola and her shadow. Observed: the plate. |
| 34a | 34a.4 Opsign: the crowd | a dense crowd in boaters behind a rope, all watching the same way for a race (Autoraces op boulevard Scheveningen), 0-3.3 s, slowed 0.28x. | Bola and her shadow. Observed: the plate. |
| 34b | 34b.2 Sonsign: the whistle | a factory whistle blowing steam on a roof (Valley Town), 0.05-3.7 s, slowed 0.3x, with a 1.6x push-in crop (generated). | Bola, her shadow, the push-in, a synthesized whistle tone under the plate's own sound. Observed: the plate. |
| 34b | 34b.4 Sonsign: the record | black lacquer poured onto a turntable plate, spreading into a disc (Command Performance), 1.3-6.6 s, slowed 0.4x. | Bola, her shadow, a short synthesized melody when she listens. Observed: the plate. |
| 34b | 34b.5 Sonsign: the alarm | an alarm clock on a lace doily; a hand comes in and presses it (Communications and Our Town), 13.1-19.6 s, time-remapped (slow until the hand, so the hand's press lands where the ringing stops). The ringing and the clock's shiver are generated. | Bola, her shadow, the ring, the shiver. Observed: the plate. |
| 35 | 35.0 Mirrors face to face: the reflection | a dance stage of refrigerators with a glossy floor that mirrors them (Frigidaire Finale 1957), 41.6-47.5 s, slowed 0.4x. | Bola and her reflection (a second instance drawn upside down under her feet, faded with distance like the plate's own reflections), her contact shadow. Observed: the plate and its real floor reflections. |
| 35 | 35.1 Mirrors face to face: the barber mirror | a barber cutting a boy's hair, pushing his head down and letting it up (Barbers), 0.05-7.0 s, slowed 0.5x. | Bola and her shadow. Observed: the plate. |
| 36 | 36.2 Limpid and opaque: into the white | a dust storm turning the horizon into a white wall (Dust Storm), 0.05-7.8 s, slowed 0.39x. | Bola, her shadow, the depth fade. Observed: the plate. |
| 36 | 36.4 Limpid and opaque: into the picture | a man standing on a stage beside a screen showing a farm, then a dust storm (Under Western Stars), 26.1-38.2 s, slowed 0.67x; the screen content changes are in the plate. | Bola on the stage and in the picture (rendered flat and grey, clipped to the screen), her shadow on the stage. Observed: the plate. |
| 37 | 37.2 Seed and environment: the box | a closed hexagonal sewing box on a table whose panels swing open onto a world of tools (Have I Told You Lately That I Love You?), 10.3-19.9 s, time-remapped so the box stays shut until her third knock; table tracked. | Bola, her shadow, the knocks. Observed: the plate. |
| 37 | 37.5 Seed and environment: the sprout | a time-lapse of a bean seedling pushing up out of the soil and lifting its seed (Unique Contribution), 0-4.65 s, slowed 0.27x. | Bola and her shadow. Observed: the plate. |
| 40 | 40.2 Powers of the false: the copies | identical model houses multiplying across a board in stop motion (How Our Country Grew), 4.5-18 s, slowed 0.9x. | Bola and her six copies (the same performance, delayed and placed in the streets of the final layout), their shadows. Observed: the plate. |
| 40 | 40.4 Powers of the false: the glasses | a cinema audience in 3-D glasses, delighted (RCA Presentation: Television), 7.65-11.9 s, slowed 0.35x. | Bola, her 3-D glasses, claps. Observed: the plate. |
| 41 | 41.0 Bodies of attitude: the slump | a man slumped back in an armchair under a lamp, worn out (Financial Investigation), 0-3.0 s, slowed 0.25x. | Bola, her shadow, the claps. Observed: the plate. |
| 41 | 41.1 Bodies of attitude: the sleeper | an old man slumped asleep against a wall, one knee up (Alcohol and the Human Body), 11.5-20 s, slowed 0.55x. | Bola and her shadow. Observed: the plate. |
| 43 | 43.0 Cinema of the brain: the floor plan | a house floor plan drawn in white lines with a pencil resting on it (Banks And Credits), 5.3-7.75 s, slowed 0.13x. | Bola and her shadow. Observed: the plate. |
| 43 | 43.4 Cinema of the brain: the map line | a hand drawing a route on a survey map in pencil (Caught Mapping), 0.46-3.9 s, slowed 0.25x, map tracked (tr434). | Bola, her shadow, her pencil line. Observed: the plate. |
| 44 | 44.1 Lectosigns: the end | a night street of neon with a BUS DEPOT sign; THE END lights up across the street (How Man Made Day), 10.4-17.1 s, slowed 0.5x, with a 1.4x push-in crop (generated). | Bola, the push-in. Observed: the plate, including THE END. |
| 44 | 44.4 Lectosigns: the ad | a newspaper want-ad, HELP WANTED, MEN (Ask Me, Don't Tell Me), 0-1.8 s used, slowed 0.15x, page tracked (tr444). | Bola and her shadow. Observed: the plate. |
