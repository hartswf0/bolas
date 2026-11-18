# Teuf-Teuf: swarm plan (Direction 1, "La paroi")

Revision base: `proposals/kf-1.png` and `proposals/src/{common,puppet,kf1}.py` as of 2026-11-15, plus `films/teuf-teuf.py` as the motion-law fixture (drag 1.2 m, rollers 3.0 m, wheels 8.0 m in the same 7.0 s push). The plan is rebuilt from scratch. Only the fixture's numbers and the already-foraged Cueva de las Manos and Ljubljana photographs carry over, and their licences must be re-verified first.

Chosen direction: **1 · La paroi**. The film uses articulated charcoal cut-card puppets on the real Cueva de las Manos rock, which is re-toned to the reference's cream sepia wash. Its real hand stencils become pale hands in dark blown halos, as they are in the reference. kf-1 got this wrong: it showed them as dark hands. The film stays in this direction and does not drift to direction 2 or 3. Direction 3's idea of a closing comparison survives only as scratched ghost marks on the ground band (§4, shot 6). It is not a stencil-diagram section.

---

## 1 · Creative thesis

One stone, one push, one wall. The same two charcoal figures meet the same boulder three times, and each time the thing under the stone changes: nothing (a sledge runner scraping the ground), then loose logs, then a wheel fixed to an axle. The figures' bodies show what the mechanism allows:
- **Dragging:** the pusher strains at 40° and the stone lurches by fingers' widths.
- **Rollers:** the stone rides, but the logs drift backwards under it, so one figure becomes a log-carrier. A log rolls out behind, is forgotten, and complains.
- **Wheel and axle:** the wheel stays under the load, the carrier is free, and the pusher has to walk faster to keep his hands on the stone.

The narration, given as captions, complicates each beat with a dry Queneau-like observation. It never explains the mechanism.

**What would make it bland:** pans over a static painted wall; figures that slide without their feet planting; logs that read as wheels; captions that explain instead of joke; a wheel beat that looks like the roller beat, only faster.

## 2 · Defining beat and comparison baseline

**Defining beat (the TEST SHOT), rollers, film time 16.2–19.0 s.** The boulder rides on two logs. The rear log has drifted out from under the stone's back edge at half the stone's speed. It drops 1 px, rolls about 0.3 s behind on its bark, and stops with a wooden "tok". The carrier, bent at the front, walks the third log forward, crouches (IK knees, hands pinned to the log) and sets it down ahead of the stone. The stone waits on its two remaining logs, and the pusher's hands stay pinned to it. When the log stops, the caption reads: « Et moi ? » dit le rouleau qu'on laisse derrière. ("And me?" says the roller left behind.)

**What the viewer can point to when it succeeds:**
1. The rolling logs turn: their bark knots and scratched end-ring mark rotate.
2. The logs move backwards relative to the stone, at half its speed.
3. One log falls out behind and lies still.
4. The carrier's job exists only because of (2).
5. The speaking log is the one that just stopped, and the line comes after it stops.

**Comparison baseline.** Within the film, the baseline is the drag beat: the same stone, the same pusher pose, the same hand height, the same 7.0 s push clock and the same fixed frame. Rollers and wheel are read against the drag beat's 1.2 m ghost mark. Outside the film, the baseline is kf-1 (a still). The rollers shot has to meet or beat it in rock wash (paler and smoother), log read (bark and irregular outline, not discs) and figure character (charcoal dry-brush, tapered, Jabely-like).

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Teuf-Teuf* (Jean Jabely, 1956; commentary by Raymond Queneau). Animated history of the means of transport, staged on a cave-painting mural (still: Cité Films; the dossier describing Queneau's commentary: Gazette Drouot lot 186). The film itself was not inspected beyond the one still, so its exact sequence is **unknown**. |
| source medium | 35 mm animation, drawn/painted mural ground, French spoken commentary |
| target medium | 1280×720 / 24 fps digital animation (kit.py `Film`) about 44 s long, with French captions and English subtitles, foraged and synthesized sound |
| preserved relation | a mechanism's improvement is shown as what bodies can now do, on a prehistoric wall, with a witty commentary set against the action |
| optics | flat, frontal mural, no camera perspective. One oblique close-up is the exception (§8 repair, used once). |
| formalism | the same challenge repeated three times in a fixed before/after frame; a physics fixture drives the motion; [substitute] swaps the mechanism under an unchanged load |
| concept | a demonstration of mechanisms, not a dated history. Chronology appears only where a source dates an object (Ljubljana wheel). |
| sound | Queneau's voice is replaced by captions, because no TTS is allowed. Contact sounds are the "voice" of each mechanism: scrape, tok, rumble. |

**Formation epochs** (weight 0–100, with the reason):
- **Upper Palaeolithic / Holocene rock art, 90.** The ground, the stencils and the animal silhouettes are the medium. The Cueva de las Manos stencils are dated about 9,000–13,000 BP in the literature; this is an *uncertain claim*, and it is not shown on screen.
- **Neolithic and Chalcolithic transport, 60.** This is the subject. Sledges, rollers and the plank wheel with axle are the mechanisms. Only the Ljubljana Marshes wheel carries a sourced date (Commons description: about 5,150 years old). Rollers preceding wheels is a *contested causal claim* (the roller-to-wheel theory is disputed), so the film presents a sequence of mechanisms, not a lineage. Staged compression is marked in the source register.
- **1950s French animated pedagogy and Oulipo-era wit, 75.** Jabely and Queneau give the tone: a demonstration undercut by deadpan remarks.
- **Reiniger shadow theatre (1920s), 55.** The method for the articulated silhouette.
- **Computational puppetry (IK and spring secondary motion), 50.** The method for contact and weight.

### Olog (from §3 of the prompt)

- ◻**Mechanism** has: `period: SourcedClaim|Unsourced`, `input_force: Push(N=const, height=hand_y, window=7.0s)`, `moving_parts: [Part]`, `contact_points: [Contact(part_a, part_b, kind∈{slide, roll, axle, grip, plant})]`, `supported_action: Displacement(m in 7 s)`, `failure_mode: Event`.
  - Drag: parts {stone, runner}; contacts {runner–ground: slide, hands–stone: grip, feet–ground: plant}; action 1.2 m; failure: stick-slip lurches, and the pusher's feet re-plant at every slip.
  - Rollers: parts {stone, log×3}; contacts {stone–log: roll, log–ground: roll}; action 3.0 m; failure: the logs travel at v/2, fall out behind, and the load must wait while a log is carried forward (load stationary for τ ∈ [2.2, 4.8] s).
  - Wheel and axle: parts {stone, platform, axle, wheel×2}; contacts {platform–axle: axle bearing, wheel–ground: roll}; action 8.0 m; failure: none in the window, but the pusher's walking speed becomes the limit (his stride rate rises).
- ◻**ExplanatoryBeat** = (one visible movement, one caption, one sound event), each with its own timestamp. The caption's onset falls 0.2–0.6 s after the movement's causal frame.
- **[substitute]**: Mechanism × Load → Mechanism' × Load, which swaps `moving_parts` and `contacts` while keeping Load (same stone mask and mass), `input_force`, frame and push window.
  - **Typed preconditions:** (a) the load mask is pixel-identical across trials; (b) the push height and the 7.0 s window are identical; (c) the frame, ground line and px/m (100 px/m) are identical; (d) the new mechanism has at least one contact of a kind the old one lacked (slide→roll→axle).
  - **Observable consequences:** (a) the final load displacement changes monotonically, 1.2 → 3.0 → 8.0 m, read off the scratched marks on the ground band; (b) the figures' work changes kind: strain, then carrying, then walking to keep up; (c) the contact sound changes: scrape, then tok, then rumble.
  - **Counterexample (central operation):** keep the wheels but remove the axle coupling (shot 5). The wheels become loose discs. The platform rides on them at v/2 relative, they drift back, the rear wheel falls out, the platform drops and grinds, and the load stops after about 0.9 m. So a "wheel" substituted without its *contact kind* (axle) does not produce the wheel outcome. The shape of a part is not the mechanism; its contact is.
  - **Replay and alternate views:** *equivalent*: the oblique close-up (shot 3b) and the wide (shot 3a) show the same instants of the same sim (same τ, same log positions), and the counter-check reuses the wheel trial's input exactly. *Divergent*: the counter-check differs only in the axle contact, and its outcome diverges, which is the point. The close-up deliberately shows the log's length and bark, which the frontal view cannot.
- **TTL** = 2. No interactive component.

## 4 · Invariants

1. **Same challenge:** the load mask, push height (hand_y), 7.0 s push window, fixed frame, ground line and 100 px/m are identical in all three trials and in the counter-check. They are asserted in `sim.py`.
2. **Contact carried through motion.** Planted feet do not slide while planted (residual ≤ 1 px). Hands stay on the stone face (≤ 2 px) during push phases. Rollers have no slip: log rotation Δθ = Δx_log/R. Wheel rotation = Δx_cart/R. Nothing interpenetrates the ground (logs and wheels are tangent to it ±1 px).
3. **Continuity:** the load's x is continuous frame to frame (no jump > its sim velocity·dt + 1 px). It is identical between the wide and close-up views at the same τ.
4. **Historical attribution:** every dated or sourced claim is tied to a register entry. Staged compression (three mechanisms on one wall) is declared in the notes and in the end-credit line.
5. **Joke timed to cause:** each caption's onset falls 0.2–0.6 s after its causal frame (the stick, the log stop, the cart passing the 3 m mark, the axle pin pulled).
6. **Silhouette readability (Reiniger):** limbs never detach; hands and head read with the colour removed; the stone, logs and figures do not merge into one blob (each keeps a ≥ 3 px pale gap, or a halo edge that separates it).
7. **Secondary motion:** begins after primary impulses and decays to rest within 0.6 s. There is no idle wiggle.
8. **Licence:** only PD, CC0, CC BY or CC BY-SA, read from Commons extmetadata. No frames from Jabely's film.

## 5 · Shot list: the Hard proof (30 s, from 4.0 to 34.0 s) inside a 44 s film

There is one fixed frame (layout A), 1280×720 at 24 fps, used for shots 1, 2, 3a, 4, 5 and 6. Ground line y = 566. Load front edge at x0 = 330 px for 0 m. Scale 100 px/m, so 8 m reaches x = 1130. The ground band carries faint scratched tick marks at 0, 1.2, 3 and 8 m. They are uncaptioned scratches, the way the reference has scratches, not labelled rulers.

| # | time (s) | on screen | heard | elements |
|---|---|---|---|---|
| 0 | 0.0–4.0 | The wall wakes. The toned Cueva rock fades up from black under the charcoal bands, and the real stencils and guanaco silhouettes come up as the light comes up. Title *Teuf-teuf* is scratched in white (it writes on with a stroke-order reveal, 1.2 s). The boulder is already at x0. The two figures walk in from the left (IK walk cycle, 4 steps). | room tone (a foraged cave or room ambience if one is found, otherwise kit `room`), footsteps on stone synced to foot plants | wall FORAGED (Commons, Suzko, CC BY-SA 3.0); title, figures and boulder HANDMADE |
| 1 | 4.0–13.0 | **Drag.** The stone sits on a short sledge runner. Push window 4.5–11.5 s (τ 0–7). Pusher leans 40°, hands pinned, feet planted. Nine stick-slip lurches move the stone 1.2 m. At each slip: a head nod (spring), a stone rock of ±1.5° (spring), and the rear foot re-plants. The helper hauls a rope tied to the runner's nose (two-bone IK arms, rope as a polyline under tension). At 11.5 s the stone stops. A white scratched ghost outline of the stone stays at the 1.2 m position for the rest of the film. Caption at 7.3 s, on the 4th stick: « La pierre avance d'un pas, puis elle réfléchit. » / *The stone takes a step, then thinks it over.* | a scrape (stone on grit, foraged if possible) on each slip; breath is not used (no voice); footstep on each re-plant; one low thud at the stop | runner, rope and ghost HANDMADE |
| 2 | 13.0–14.0 | **Substitute I.** The carrier lays three logs in front of the stone: the stone is levered up in 3 frames, tilts on a spring and settles onto the logs. | wooden knocks as each log lands (3) | logs HANDMADE (bark-textured cut card) |
| 3a | 14.0–16.2 | **Rollers (wide).** τ 0–2.2: the stone rolls forward to 1.5 m. The logs visibly turn and drift back under it at v/2. | low wooden rumble whose amplitude follows the log angular speed | |
| 3b | 16.2–18.8 | **TEST SHOT. Close-up, oblique (§8 repair).** The camera moves in on the rear of the stone. It is the same wall, scaled ×2.2 and cropped, with the same τ. In this view the log is drawn as a 3/4 cylinder (end ellipse plus bark length), so it cannot read as a wheel. The rear log slips out at the stone's back edge, drops, rolls 0.3 s and stops. Its end-ring mark settles with a spring overshoot. At 16.9 s it stops ("tok"), and from 17.2 s the caption reads: « Et moi ? » dit le rouleau qu'on laisse derrière. / *"And me?" says the roller left behind.* This is the film's ONE nonhuman line. In the background, out of focus by scale only (no blur filter), the carrier's legs walk the third log forward. | tok (wood on stone), small dry roll | |
| 3c | 18.8–21.0 | Back to the wide frame, at the same instants. The carrier crouches and sets the log down in front (hands pinned to the log, knees IK). The stone waits throughout (τ 2.2–4.8); the pusher's hands stay pinned and his feet are planted. | wood set down, step, step | |
| 3d | 21.0–23.0 | τ 4.8–7.0: the stone rolls on to 3.0 m. One log has been left lying behind in the frame (it stays). | rumble; a soft thud at the stop | |
| 3e | 23.0–25.0 | Hold. A scratched ghost mark appears at 3.0 m. The left-behind log is still on screen. | room | ghost HANDMADE |
| 4 | 25.0–34.0 | **Substitute II, wheel and axle.** 25.0–26.0: the stone is now on a plank platform over one axle with two solid tripartite plank wheels. The wheel piece is cut with cv2.grabCut from the Ljubljana Marshes wheel photograph (FORAGED, Commons, Petar Milošević, CC BY-SA 4.0) and toned to charcoal. Its real square axle hole is kept, which shows the axle lock. 26.0–33.0 (τ 0–7): the load goes 8.0 m, x ease-in. The wheel turns Δx/R. The pusher must walk: his stride rate rises from 1 to 2.2 steps per second. The carrier has nothing to carry; he walks alongside with empty hands, looks at his hands, and drops back. At 28.4 s the cart passes the 3 m roller ghost. At 28.8 s the caption reads: « La roue tourne sur place ; c'est tout le reste qui voyage. » / *The wheel turns on the spot; everything else travels.* The cart reaches 8 m near the right edge at 33.0 s. | rumble of an axle and wheel (foraged cart or wheel recording if licensed, otherwise synthesized low rumble with periodic plank knock once per wheel turn, so the knock rate tracks rotation); footsteps accelerate | wheel FORAGED cutout; platform, axle and pin HANDMADE |
| 5 | 34.0–38.0 | **Counter-check, axle removed.** The cart is back at x0 (a 6-frame dissolve marked by a white scratch wipe, so the reset is a declared cut, not a jump). The pusher pulls the axle pin, and the axle beam lifts away. The same push (τ 0–1.6 at the same hand height) is applied. The wheels now roll free under the platform at v/2, drift back, and the rear wheel falls out. The platform drops onto the ground and grinds to a stop at about 0.9 m. Caption at 36.6 s: « Sans essieu, la roue n'est qu'un rouleau qui se croit quelqu'un. » / *Without an axle, a wheel is just a roller with ideas.* | the pin's click; rumble; a grinding scrape; a thud | |
| 6 | 38.0–44.0 | **Comparison held.** The same frame. Three ghosts of the stone (1.2, 3.0 and 8.0 m) stand scratched in white on the wall, with the left-behind log and the wheel-less platform still lying where they fell. The figures sit down against the wall (IK settle). There is no caption. At 42.0 s the end line scratches in, small: "Sources : Cueva de las Manos (Suzko, CC BY-SA 3.0) · roue des marais de Ljubljana (P. Milošević, CC BY-SA 4.0) · séquence mise en scène, non chronologique". | room; one final wooden tok from the forgotten log, rocking once (a secondary-motion callback) | |

The Hard proof is the 30 s window from 4.0 to 34.0 s: dragging, rolling on loose cylinders and riding a simple wheeled platform, each under the same 7.0 s push. **Sound off:** the ghosts, the ground ticks, the figures' changing labour, and the left-behind log make the improvement readable without sound. **Sound:** every contact event in `sim.py`'s event list gets one sound event. Captions are the only voice, and there is one nonhuman line (the log). The narrator lines are commentary, not speech by objects.

**Commentary-off comparison (§7):** the editor also renders `teuf-teuf-nocaption.mp4` (same picture, no captions) so the critic can compare the staging with and without commentary.

## 6 · FORAGED vs HANDMADE

- **FORAGED**
  - Rock wall: "Cueva de las manos - detalle.jpg", Suzko, CC BY-SA 3.0, Commons. It is already in `sources/teuf-teuf/hands_cueva.jpg`; re-verify extmetadata. Its real negative hand stencils, guanaco silhouettes and ochre are kept.
  - Wheel: "Ljubljana Marshes Wheel with axle…jpg", Petar Milošević, CC BY-SA 4.0, Commons. It is already present; re-verify. The film uses a GrabCut cutout of the wheel only (the axle is drawn new, because the photographed axle is a separate fragment).
  - Sound (try first, then fall back to synthesis):
    - Commons audio for stone scraping, wood knocks, logs rolling or a wooden cart: search `filetype:audio` for "wood knock", "stone scrape", "cart wheel", "footsteps gravel".
    - The movingimagearchive cache for clips with source sound: try "quarry|stone|wood|cart|wagon|lumber" and look and listen; for example 1914 "Panama by Air (Reel 4)" has driftwood rolling in surf. It could serve as a rotoscope timing reference for a log's tumble, but only with a credit, and only if it is used at all.
    - LoC audio is unlikely.
    - Every sound used is credited. Synthesized sounds (kit Mix) are declared in the notes.
- **HANDMADE**
  - Cut-card puppets ×2: tapered limb pieces with pinned joints, charcoal dry-brush fill, blown-pigment halo.
  - The boulder, an irregular cut shape.
  - Three logs with bark (a bark-stripe texture along the length, knots, and an irregular 9–14-point outline whose radius varies ±12 %, plus a broken-off branch stub on one log so its rotation is visible).
  - The sledge runner, rope, plank platform, axle beam and pin.
  - The charcoal bands, scratched ghosts and ticks.
  - The title and caption type.
  - The physics fixture.

## 7 · AESTHETIC TARGET (reference: `assets/references/teuf.webp`, Cité Films still)

Sampled with PIL (1000×617):
- luminance p1/5/10/25/50/75/90/95/99 = 13/21/39/84/169/212/225/229/236
- darkest ink ≈ rgb(15,17,9); dark charcoal ≈ (43,44,31); mid grey-brown ≈ (89,90,73); mid wash ≈ (179,176,152); pale cream ≈ (239,232,202); highlight ≈ (251,243,213)
- pale-wall pixels (blurred luminance > 150, 54 % of frame): median rgb ≈ (223,217,188), median luminance 209
- top band mean ≈ (99,100,82); bottom band ≈ (120,120,100)
- 17 % of pixels below luminance 60

The palette is a near-monochrome *greenish* sepia: R ≈ G > B, and the blacks lean olive, not brown.

kf-1 by comparison: pale-wall median luminance 166, rgb (176,170,153), so it is too dark and too grey. Only 9.6 % of its pixels are below 60.

- **Medium:** a photographed painted mural, matte gouache or wash ground. Charcoal or dry brush in the bands and inside the silhouettes. White scratched (engraved) lines. Blown-pigment halos round the stencils. Our medium matches this by keeping the real photographed rock and painting the rest as cut-card and charcoal, then printing the result as one toned photographic image.
- **Tonal range:** full, from near-black silhouettes to cream, with a wide smooth pale field. Silhouettes are solid black with grey dry-brush texture inside.
- **Light:** soft, even, frontal (copy-stand light). No cast shadows, no directional rim light.
- **Texture:** a smooth wash with broad soft gradients (*not* busy rock grain); rubbed horizontal charcoal streaks in the bands; dot clusters; a fine print grain. The rock must therefore be low-passed: keep its large forms and stencils, keep the high-pass at 0.25–0.35 (it was 0.85 in kf-1), lift its median to about 210, and warm it to the (223,217,188) cream.
- **Framing and scale:** a wide frieze, flat and frontal. Figures fill about 30–40 % of the frame height (the reference's bulls are about 35 %). Wavy dark bands of 8–15 % at the top and bottom. Figures are profile silhouettes.
- **Typography:** the reference has none. On-picture type is limited to the white-scratched title, captions in a small serif italic in the lower band (cream on charcoal, no box), and the end source line.
- **Pacing:** calm. Long holds between actions (the reference is a tableau). Action is concentrated in short efforts, and the camera stays fixed except for the one close-up.

**Figures with Jabely's charcoal character:**
- the limb ends are brush-tapered with ragged dry-brush edges (the outline is broken with stroke noise, not a smooth polygon);
- the interior carries grey dry-brush hatching that runs along the limb direction (like the strokes inside the reference's bulls);
- the heads are animal-like and have a small profile nose or brow;
- the silhouettes are black with sparse pale streaks, plus a few white scratched contour accents.

## 8 · Technique SCIONs (from swarms.json)

1. **#2 Lotte Reiniger, articulated shadow theatre.** Why: the figures are cut-card silhouettes with pinned joints and joint-angle limits on a flat backlit-like plane, and the action must read in silhouette, exactly as the reference's black animals read. How, per shot:
   - All shots use replacement profiles: hands open or gripping, a head turned or bowed.
   - Joint limits apply everywhere (knee 0–150°, elbow 0–160°).
   - An exposure sheet (`exposure.json`) is kept for every frame.
   - In shot 3b a *replacement* profile is used for the log (a 3/4 cylinder instead of a disc).
   - The silhouette-read test (frames converted to greyscale and thresholded) runs on shots 1, 3a, 3c and 4.
2. **#33 Inverse kinematics, contact and reach.** Why: the proof is contact and force. Feet grip the ground, hands bear on the stone, and contact changes the next pose. How, per shot:
   - two-bone analytic IK with pole (knee or elbow bend) signs;
   - planted-foot locks driven by a contact timeline (plant, lift, plant);
   - hands locked to the stone face during push and to the log during the carry (3b, 3c);
   - the rope hauler in shot 1;
   - the walking-speed limit in shot 4 (stride length capped at 0.75 m, so the cadence must rise);
   - per-frame residual metrics written to `animation.json`.
3. **#41 Secondary dynamics, inertia and restraint.** Why: momentum and material have to read: stick-slip, a log settling, a wheel-less platform falling. How, per shot:
   - spring-damper (semi-implicit Euler, dt = 1/240) for the head nod and stone rock at each slip (shot 1), the stone settling onto the logs (shot 2), the log's end-mark overshoot and its final rock (3b and shot 6), the platform drop (shot 5), and the rope sag (shot 1);
   - impulses come only from sim events, with ζ ≈ 0.35–0.6, and energy decays to below 1 % within 0.6 s;
   - the test is that there is no secondary motion before the first impulse.

Supporting method (not a declared SCION): cv2.grabCut (the #29 method) cuts the Ljubljana wheel out of its photograph. Its mask is saved, and its interior keeps the real wood grain, toned to charcoal grey.

## 9 · Swarm units (the montage editor and the independent reviewer run separately)

1. **mechanic-historian** (historian + mechanic modeler, merged because the joint and contact definitions are shared).
   - Builds `films/swarm/teuf-teuf/sim.py`: the motion laws from the fixture (drag stick-slip, roller sim with v/2 logs and carry, wheel ease, counter-check without axle) at 24 fps with 1/240 substeps.
   - Writes `exposure.json`: the per-frame load x and angle, each log's x and angle, carried/free state, wheel angle, foot and hand contact targets, and an event list with times (slip, log-land, log-stop, pass-3m, pin-pull, wheel-drop, stops).
   - Writes the parts and contact schema in `mechanism.json`, with asserts for invariants 1–3.
   - Writes the historical source register `register.json`: every claim, its source URL, and its status (sourced, uncertain, staged compression).
   - Re-verifies the licences for the Cueva and Ljubljana files from Commons extmetadata and rewrites `films/credits/teuf-teuf.json` with only the items used.
   - Output: `films/swarm/teuf-teuf/mechanism.json`; media goes to `sources/teuf-teuf/mechanic/`.
2. **layout-wall** (layout artist).
   - Builds the fixed frame A: the toned Cueva wall (low-passed, warmed to the target cream, with the real stencils shown as pale hands in dark halos, and the guanacos kept), the charcoal bands, the ground line, the scratched ticks at 0, 1.2, 3 and 8 m, and the ghost-outline generator.
   - Builds the close-up frame B (×2.2, the same wall, the same τ mapping).
   - Writes `layout.json`: px/m, x0, ground y, band geometry, close-up transform, and the measured pale-wall median rgb and luminance against the reference targets.
   - Writes a side-by-side `layout-vs-ref.jpg`.
   - Output: `films/swarm/teuf-teuf/layout.json`; plates go to `sources/teuf-teuf/layout/`.
3. **animator** (puppets, contact and force).
   - Builds the Reiniger cut-card puppets with Jabely charcoal character, the FK spine, the two-bone IK with foot locks, the secondary springs, the bark logs (frontal and 3/4 replacement), the boulder, the runner and rope, and the cart with the GrabCut Ljubljana wheel.
   - Renders every shot from `exposure.json` over the layout plates, as PNG sequences or clips, in `sources/teuf-teuf/animator/`.
   - Writes `animation.json`: per-shot frame ranges, IK residuals, max foot slide while planted, hand-to-stone residual, roller-slip residual, and secondary-energy decay times.
   - Writes a contact sheet `test-shot-sheet.jpg` of shot 3b.
   - Output: `films/swarm/teuf-teuf/animation.json`.
4. **commentary-sound** (aligns the punchlines with the mechanical cues).
   - Writes the dual-column score `score.json` (and `score.md`): for every beat, the picture event and time from `exposure.json`'s event list, the caption FR/EN with onset and offset, and the sound event and its source.
   - Forages sound: Commons audio first (licence from extmetadata), then movingimagearchive clips with source sound, then kit `Mix` synthesis, which is declared.
   - Prepares the WAV stems and the caption timing.
   - Output: `films/swarm/teuf-teuf/score.json`; audio goes to `sources/teuf-teuf/sound/`.

Dependencies: the animator and commentary-sound units read `exposure.json` and `layout.json`. The time and position constants in §5 are fixed now, so all four units can start against the same revision.

## 10 · Acceptance bar (falsifiable, for a fresh critic watching `assets/films/teuf-teuf.mp4` and reading the ledger)

1. **Same challenge, monotone outcome:** in the drag, rollers and wheel trials, the load's front edge ends at 1.2 ± 0.05, 3.0 ± 0.05 and 8.0 ± 0.1 m (measured from frames at 11.5, 23.0 and 33.0 s against the scratched ticks, and in `exposure.json`). The stone mask, hand height and push window are identical (`mechanism.json` asserts pass).
2. **Roller read (TEST SHOT):** in 16.2–18.8 s a viewer with the sound off can point to a log that (a) visibly rotates (bark or knot marks turn), (b) moves backwards relative to the stone, (c) falls out behind and stays still afterwards, while (d) the carrier sets a log down in front during 18.8–21.0 s. No log reads as a perfect disc: it has a bark outline and, in 3b, a visible length. A critic shown frames from 3a and 4 side by side must be able to say which shows logs and which shows wheels.
3. **Axle counter-check:** in 34.0–38.0 s, with the axle removed and the same push, the wheels move backwards relative to the platform and one falls out, and the load stops at ≤ 1.2 m. This movement is visibly different from shot 4, where the wheels stay under the platform for all 8 m.
4. **Contact and continuity:** `animation.json` reports planted-foot slide ≤ 1 px, hand-to-stone residual ≤ 2 px during push phases, and roller slip (Δθ·R − Δx) ≤ 0.5 px per frame. No frame-to-frame jump in load x exceeds sim velocity·dt + 1 px, except at the declared cuts (14.0 s, 16.2 s, 18.8 s, 34.0 s), where wide and close-up positions agree at the same τ.
5. **Joke timed to cause, one nonhuman line:** each caption's onset falls 0.2–0.6 s after its causal event in `exposure.json` (the 4th stick, the log stop, passing 3 m, the pin pull). Exactly one line is spoken by a nonhuman object (the log). Each caption adds an idea the picture alone does not state (the critic compares against `teuf-teuf-nocaption.mp4`).
6. **Aesthetic, tone (side by side):** frames at 7.0, 17.5 and 30.0 s placed beside `teuf.webp` show:
   - pale-wall median luminance 195–220 and median rgb within ±12 per channel of (223,217,188), with R ≥ G > B;
   - ≥ 12 % of pixels below luminance 60 (black silhouettes and bands);
   - dark wavy charcoal bands at the top and bottom;
   - real hand stencils that read as pale hands inside dark blown halos, as in the reference.

   Measured with PIL; perceptually, the critic judges the rock "a smooth wash, not busy stone".
7. **Aesthetic, figures (side by side):** a crop of the pusher at 7.0 s beside a crop of the reference's black bull shows the same family of marks: solid black mass, grey dry-brush streaks inside, ragged brush-tapered edges and a blown-pigment halo. No smooth vector polygons, no shaded stick figures, no photographic filter.
8. **Provenance:** every foraged item on screen or audible appears in `films/credits/teuf-teuf.json` with a licence read from Commons extmetadata (PD, CC0, CC BY or CC BY-SA only). `register.json` marks the staged compression and every dated claim. The film shows no date except one that is sourced.
