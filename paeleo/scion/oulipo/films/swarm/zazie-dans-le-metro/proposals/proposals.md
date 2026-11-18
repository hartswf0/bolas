# Zazie dans le métro: round 2, three proposed directions

**Reference:** `assets/references/zazie1.webp`.
- A 4:3 Eastmancolor close-up of a laughing child.
- She has gap teeth, eyes squeezed shut, and an auburn bob blown across her brow.
- Her collar is orange.
- Behind her, pale city pillars are thrown far out of focus.

**Round 1** (`r1/`) was rejected. It was not close enough to that laugh, and it leaned on archive footage. This round keeps the close framing, the warm print palette, the soft Paris behind, and the joy of the laugh. Two of the three directions are animation-led.

**Frames.** Every keyframe is 1280x720, with the 4:3 picture pillarboxed. Captions are the voice, in French italic serif. The builder is `proposals/kf.py`, and it is deterministic.

**Defining beat.** Zazie wants the métro. The métro is on strike, so the city keeps changing the terms. She laughs anyway. The Hard proof is a 20 s pursuit:
- **0–4 s, setup:** the same straight chase.
- **≈8–10 s, jump cut:** impossible distance.
- **≈12.4 s, match cut:** the queue becomes an obstacle.
- **16–20 s:** recovery.

**Baseline.** The control is a clean continuity cut of the same chase, with no gag operation.

**Downloads:** about 2.6 MB in total, in `films/sources/zazie-dans-le-metro/r2/`, all licence-checked:
- **G.** *Little girl laughing with excitement in France*. Basile Morin, **CC BY-SA 4.0**. Wikimedia Commons, `File:Little_girl_laughing_with_excitement_in_France.jpg` (1920 px thumbnail).
- **P1.** *The Madeleine, and rue Royale, Paris*. Photochrom, Detroit Publishing Co., c.1890–1900. LoC 2001698526, **no known restrictions / PD**.
- **P2.** *Street scene and monument, in the Place Clichy, Paris*. Photochrom with a horse-tram, Detroit Publishing Co. LoC 2002707975, **no known restrictions / PD**.
- **P3, P4.** Boulevard de la Madeleine and Place du Châtelet photochroms (LoC 2001698544, 2001698539, PD). Spares for the third location.

**Not found.** The local Moving Image Archive cache has no colour close-up of a laughing child. The nearest were b/w (*Eyes and Their Care*, *A Place to Live*) or not laughing (the 1941 Krewe of Rex parade child). So the one foraged direction uses a still photograph. Commons rate-limited me after a few searches, so a colour *film* close-up was not searched for. That stays open (see risks).

---

## 1 · Rire, et Paris saute (foraged photograph, jump-cut pixilation)

**Beat and time.** The impossible-distance jump cut, ≈8–10 s, with the laugh as its anchor.
- The face stays fixed and laughing while Paris jumps behind her: rue Royale (P1), then Place Clichy (P2), then Châtelet (P3), one location per cut.
- Caption: « Le métro ? En grève. » The goal is legible, and the city answers it with a jump.
- Prop: her straw hat, read two more ways. First the wind takes it, and she chases the hat rather than the métro, so the goal is substituted. Then it lands on the Clichy tram's roof, and the tram becomes the hat's vehicle.

**Material.**
- G, the laughing girl. A real laugh, eyes squeezed, at good resolution.
- P1, as a defocused plate, so the Madeleine's pale columns sit where the reference's pillars are.

**Technique.**
- **#29 GrabCut:** hand-seeded matte, three passes of seed rectangles.
- **#31 Alpha Matting:** the hair and spray edge, still to do.
- **#44 Multiplane Parallax:** the plate sits 1.0 stop softer and drifts 0.3x.
- **#43 Collage Graph Rewriting:** the hat node goes hat → chased vehicle → tram roof.
- **#45 Occlusion:** the hat on the tram.
- **#27 Remotion EDL:** cut fixtures.

**How it moves, frame by frame.**
- The girl's layer is held. Only a 2–3 % breathing scale on a 6-frame cycle follows the laugh.
- Every 6 frames the plate under her is replaced (P1 → P2 → P3). This is pixilation of place, not of the figure.
- The hat is split onto its own layer and rotated 2–4° per frame by a wind curve, then released on a ballistic path.
- The negative control swaps the plates without the anchor: the face is removed, and the cut reads as a plain location change.

**Risk.**
- She is blonde, wears a red hat, and has no gap teeth. The laugh and warmth are right, but she is not the reference's auburn bob.
- It is a digital photo, not an Eastmancolor film. The print grade is applied to the foraged image, which BRIEF-2 tolerates, but the result is still a still and it moves only as a cutout.
- The matte edge around the wet hair needs alpha matting.
- CC BY-SA 4.0 means a credit to Basile Morin and share-alike on the film.
- She is an identifiable real child (Commons-licensed). Keep her use dignified and uncropped from context in the credits.

## 2 · Zazie en papier (articulated cut-paper puppet; the recommended spine)

**Beat and time.** Setup A, ≈0–4 s: who wants the vehicle, and her joy. Then it carries every beat.
- The puppet is the protagonist, so it survives every discontinuous cut. That makes it the match anchor the proof needs.
- The frame shows the laugh pose mid-gust on the rue Royale.

**Material.**
- **Handmade:** a cut-paper puppet built for this work, not traced from the reference.
  - Ten separate fringe strands, each pinned at the crown, plus four flying slivers.
  - Back-hair bob, face sheet, and tissue cheeks.
  - Closed laughing eye arcs and raised brows.
  - A folded nose tab.
  - Jaw/mouth replacement piece #4 of a 6-mouth laugh cycle, with gap teeth.
  - Orange collar and jumper.
  - Brass split pins at the crown, jaw corners and neck.
  - Each piece has a scissor-wobble edge, a fibre texture and its own drop shadow.
- **Foraged:** P1 (PD) as the soft Paris plate.

**Technique.**
- **#2 Reiniger articulated theatre** (in colour) and **#32 Forward Kinematics:** neck → head → crown → strands.
- **#13 / #41 Secondary Dynamics:** each strand is a damped spring driven by a wind curve.
- **#38 Dynamic Pose Selection:** replacement mouths for the laugh: closed, grin, open ×3, gasp.
- **#44 Multiplane:** P1 drifts 0.25x, the puppet 1x, the flying slivers 1.4x.
- **#40 Physical Tabletop** is optional: print, cut and shoot the real pieces on glass.

**How it moves, frame by frame, on twos (12 fps), like real cutout.**
- The head rocks ±4° about the neck pin on the laugh beat.
- The jaw pin swaps mouths 1-4-5-4-6-4.
- The strands lag the head by 2–3 frames and overshoot in gusts. The slivers detach and leave frame.
- For the chase, the same rig is posed run-cycle-style in front of P1, P2 and P3. The jump cut keeps the puppet's silhouette and collar as the anchor.

**Risk.**
- It can read as naïve or clip-art if the pieces stay this flat. It needs more hair tones, an ear and lip pieces, and real tabletop light, ideally a print-and-shoot pass.
- The face is rounder and simpler than the reference.
- Lip-flap timing must sell the laugh with sound off.

## 3 · Bouche de métro (kinetic typography; the defining verbal gag)

**Beat and time.** The match cut at ≈12.4 s, and the opening title.
- The pun is literal: a métro entrance is a *bouche de métro*.
- In extreme close-up, Zazie's laughing mouth *is* the métro entrance.
- Its teeth are cream letter tiles: upper row DOUK·IPU, with her gap; lower row DONKTAN.
- Down the throat is a tiled tunnel and the Place Clichy tram (P2) coming out. The strike has closed the métro, so the tram takes its place.

**Material.**
- **Handmade:** the cut-paper mouth, lips, nose tab, tunnel rings and typeset letter tiles. The tiles are set in DejaVu Serif Bold, a free licence.
- **Foraged:** P2's tram, cut out with a hand polygon, and P2 again as the soft Paris seen through the tunnel.
- The auburn strands at the corner carry over from direction 2's wind.

**Technique.**
- **Kinetic typography,** with **#47 Sound-to-Action:** the syllables drive the jaw, DOU · KI · PU · DONK · TAN.
- **#43 Collage Graph Rewriting:** the letter tiles go teeth → queue.
- **#45 Occlusion:** the tram inside the mouth matte.
- **#44 Multiplane:** the tunnel rings, then the tram, then Paris.
- **#27 EDL:** the match cut fixture.

**How it moves, frame by frame.**
- Each syllable is a 4-frame jaw open/close, and each tile pops 6 px on its own syllable.
- On "TAN" the jaw drops fully, and the tram slides forward and scales up 1.0 → 1.6 over 10 frames, as if driving out.
- The loose N tooth (already tilted in the frame) falls. The other lower tiles follow, one per 3 frames.
- On the match cut they land in a row at the tram stop as the queue, a line of letters at the same height as the lower teeth. The queue now blocks her: *faire la queue*.
- The negative control lands the tiles at a different height, so the anchor is lost.

**Risk.**
- It is a graphic, not a face: no eyes. It must be intercut with 1 or 2 to keep the laugh human.
- The tram plate is only ≈150 px wide in the source photochrom, so it is soft at this size. That is fine in a tunnel, but a sharper PD tram would help.
- The joke depends on the viewer knowing *bouche de métro*, so caption it once.

---

## Recommendation

Build **2 · Zazie en papier** as the spine. It is the animation-led direction that can hold the reference closest:
- the auburn wind-blown bob, the squeezed-shut eyes and the gap-tooth laugh;
- the orange collar against pale, soft Paris columns;
- and an articulated rig that survives every jump cut as the match anchor.

Use **3 · Bouche de métro** as the title gag and as the 12.4 s queue match cut. It is the one image that turns Queneau's word play straight into an obstacle on screen. Its letter tiles also give the film a prop line: teeth → queue → confetti in the recovery.

Keep **1 · Rire, et Paris saute** as a short live-photo insert, one beat, if the user wants a real child's laugh. Its jump-cut-behind-a-fixed-laugh mechanism can be done with the puppet as well.

**Before the swarm build:**
- Do a print-and-shoot tabletop pass of the puppet pieces, or add more tonal pieces.
- Forage a sharper PD tram or bus.
- Retry Commons later for a colour *film* close-up of a laughing child (PD or CC).
- Write `films/credits/zazie-dans-le-metro.json` with G (CC BY-SA 4.0, Basile Morin) and P1–P3 (LoC, no known restrictions).
