# La Mort en ce jardin: three proposed directions

**Reference.** `assets/references/bunuel.webp` is a black-and-white publicity still of the 1956 film, credited to MoMA / Photofest.
- It is a close two-shot in the jungle. A woman with wet, tangled blonde hair kneels over a man lying among the roots. He wears a patterned headband.
- Faces and cloth are filmed with mud and sweat.
- The tonal range is soft and panchromatic: mid-greys, lifted blacks, highlights that never clip.
- The frame is crammed with roots, ferns and big leaves.
- The still is 1.48:1. All three keyframes are 1280x720 with a 3:2 (1080x720) picture, pillarboxed. Kf-3 is narrower: its 4:3 archive frame is pillarboxed again inside that.

**Defining beat (Hard proof).** Three people cross a flooded passage with one dry bag and one safe plank, and the plank holds one person. An immaculate wedding shoe floats into reach, and one person retrieves it. Her hands are now full, so she can no longer carry the bag. The bag changes holder, and the crossing order changes.
- **Timeline, ~40 s proof:**
  - **0–12 s:** setup and first crossing.
  - **≈14 s:** the shoe first appears.
  - **≈18–20 s:** retrieval.
  - **≈24–28 s:** the bag is handed over and the order rewritten, from 1 A · 2 B · 3 C to 1 C · 2 A · 3 B.
  - **28–40 s:** consequence.
- **Alternate:** the same shoe, visually identical, lands at ≈7 s instead of 14 s.
- **Baseline:** the same crossing with no shoe, keeping the original order.

**Builder.** `proposals/kf.py` builds all three frames and is deterministic.
```
python3 -I kf.py films/sources/la-mort-en-ce-jardin <cache thumbs> <cache clips> <out> assets/references/bunuel.webp
```

**Foraged material.** About 1.3 MB of new downloads (budget ~40 MB), in `films/sources/la-mort-en-ce-jardin/`:
- **SHOE.** *Pair of Woman's Bar Shoes (Wedding)*, LACMA 51.47.2a-b. Wikimedia Commons, `File:Pair_of_Woman's_Bar_Shoes_(Wedding)_LACMA_51.47.2a-b.jpg`, 1280 px thumbnail. Licence: **Public domain**, read from extmetadata. I cut out the right-hand shoe with GrabCut and pushed its ivory satin to white.
- **SHOE-2.** *Pair of Woman's Oxford Shoes (Wedding)*, LACMA M.83.156.1a-b. Commons, **Public domain**. A spare, kept for the "second object" branch.
- **MANGROVE A/B.** *Mangroves (53575741485 / 53575741785)*. Commons, **Public domain** (Flickr, US government). Downloaded but **not used**: they are colour and sunlit, the wrong light for this film.
- **Moving Image Archive local cache.** No download needed. All three films are pre-1931 and so public domain in the US by date, but the cache records no licence field. Confirm each on its archive page before the build.
  - **RC-B.** *Robinson Crusoe B* (1927), clip `62fd3c56`, 10.5 s, 320x240. A lone walker in jungle beside bright water.
  - **RC-C.** *Robinson Crusoe C* (1927), stills `c74f645d` (jungle trunks) and `f7f9d32a` (palm fronds), 320x240.
  - **IA.** *Indisch allerlei* (1920), still `fdb47ec9`, 1440x1080. Only the water half of the frame is used, as a texture. The washerwomen in it are cropped out and not used as performers.
- **Searched and not found.** The cache has no footage of three people wading or crossing a plank. Hits for "wading", "plank" and "raft" were ducks, barns and boats. The only flood footage was *Shock Troops of Disaster* (1938) and the 1936 Pittsburgh flood, and I rejected both because their licences are uncertain.
  - Commons rate-limited me (HTTP 429) after about 4 searches. Hennell's *Troops crossing a Jungle Stream* (IWM, PD) could not be fetched, and a Commons/LoC search for old engravings did not happen.
  - The LoC JSON API timed out once.

---

## 1 · Trois sur la planche (articulated cut-paper puppets, multiplane): **recommended**

**Beat and time.** Retrieval, ≈19 s.
- B, the woman, kneels at the foot of the plank, her fingers on the heel of the shoe.
- A is mid-plank with the dry bag and has turned back. The plank holds one person, so he cannot come back past her.
- C waits on the near bank, his hand out.
- The caption names the consequence: « Elle la prend. Il faut refaire l'ordre. »

**Material.**
- **Handmade:**
  - Three grey card puppets, built for this film and not traced from the reference:
    - 13–15 pieces each (torso, shirt card, neck, head, nose tab, ear, and two-part arms and legs with hands and feet).
    - Brass-grey split pins at every joint.
    - Pencilled eye, brow, mouth and shirt seams.
    - Charcoal mud smudged into the head, hands, shins and shirt.
    - B's wet, loose strands and C's patterned headband nod to the reference without copying it.
  - The plank: a pale card piece scored with grain.
  - Torn-card banks with root fingers, and the dry bag.
- **Foraged:**
  - RC-C jungle as the far plane.
  - IA water as the flood surface.
  - RC-C palm fronds, luminance-keyed into a defocused dark near plane.
  - The SHOE photograph, as the one photographic object in a world of paper.

**Technique.**
- **#32 Forward Kinematics:** the rig is a bone chain from hip to torso to neck to head, with arms and legs below it, one card per bone. `fk()` and `puppet_parts()` in kf.py.
- **#44 Multiplane Parallax:** four planes: jungle, water and banks, plank and puppets, palm fronds.
- **#29 GrabCut:** the shoe matte.
- **#45 Occlusion Compositing:** her hand card is laid over the shoe, the shoe over its reflection.
- **#43 Collage Graph Rewriting:** the shoe → occupied hands → bag → order chain.
- **#48 State Machines:** the plank holds one occupant, and its state is checked on every frame.
- **#41 Secondary Dynamics:** bobbing of the shoe and the plank.

**How it moves, frame by frame.**
- The film runs at 12 fps "on twos", like a cut-out bench.
- Each puppet pose is a keyed set of joint angles, eased between keys and then quantised to whole degrees. The quantising gives the stepped cut-out feel.
- The far plane drifts at 0.2x the camera move, the water at 0.5x, the puppets at 1.0x and the fronds at 1.6x. The fronds are blurred at 6 px.
- The shoe arrives on a drift spline across the IA water:
  - It bobs ±3 px with a 0.9 s period.
  - Its reflection is re-rippled with a sine displacement each frame.
  - Broken ripple arcs spread from it.
- At contact the shoe's holder changes from water to B, and from that point it is parented to her hand bone.
- Then the 24–28 s handover runs:
  - B cannot hold both the shoe and the bag, so A retreats off the plank and the bag passes to C.
  - C crosses first.
  - Every frame logs plank occupancy and the holders of the bag and the shoe.
- In the 7 s alternate, A has not yet stepped onto the plank, so the rewrite costs no retreat. That is the comparison the proof asks for.

**Risk.**
- The puppets are still stiff and mannequin-like at keyframe stage. B's kneeling torso reads as boxy, and the faces are simple.
- The cards need a second modelling pass: cloth folds, a sleeve break at the elbow, and a fuller wet-hair silhouette for B.
- The foraged plates are 320x240 film, softened. The paper reads sharper than its world.
- The water is a 1920 canal texture, not a flood. It needs a darker, rougher grade, and possibly a second water plane.

## 2 · Ombres de la crue (silhouette shadow theatre after Reiniger)

**Beat and time.** The rewrite, ≈26 s.
- B stands on the near bank with the shoe raised in one hand.
- C has the bag and has stepped onto the plank first.
- A waits on the far bank with empty, open hands.
- A ledger is scratched into the black bank: « ORDRE 1 A · 2 B · 3 C », struck through, and « 1 C · 2 A · 3 B » below it.
- Caption: « Les mains prises : le sac passe à l'autre. »

**Material.**
- **Handmade:**
  - Every silhouette is black card, built procedurally and edge-roughened like a knife cut:
    - The buttress roots and great trunks.
    - The lianas.
    - Pinnate ferns, built leaflet by leaflet.
    - Big leaves.
    - Four strips of wave-cut card, with light slits between them for glitter.
    - The plank and the banks.
  - The three figures carry filigree: B's lace cut as holes of light, her strand-by-strand hair and torn hem, C's shirt fringe and hat, A's flying headband ends.
  - Behind the black sits a pale far plane of cut tracing paper.
  - The backlight is an oiled-paper falloff in neutral grey.
- **Foraged:** only the SHOE. It is the single lit object on the screen, lit by a soft halo.

**Technique.**
- **#2 Lotte Reiniger, Articulated Shadow Theater:** the same FK rig as direction 1, rendered as one black card per figure. Hinges are hidden in the silhouette.
- **#44 Multiplane:** three planes: backlight, tracing paper and black card.
- **#45 Occlusion:** her fingers over the heel of the shoe.
- **#48 State Machines:** the plank's occupancy.

**How it moves, frame by frame.**
- The film runs at 12 fps. Joints step between keyed poses, as in Reiniger's under-camera substitution.
- The four wave strips slide sideways at 4, 7, 11 and 16 px per frame and swell with phase-shifted sines. The light slits between them flicker as the water.
- The far tracing plane breathes ±1 px.
- The shoe is the only element with tone. It drifts in from the right on the lowest slit of light, so it shines through the water strips.
- B lifts it frame by frame: elbow, wrist, then the shoe re-parented to her hand.
- The ledger line is scratched across in 8 frames, at the moment C takes the bag.

**Risk.**
- This is the furthest of the three from the reference's mid-grey, mud-on-skin photographic look. It keeps the jungle, the black and white and the crowding, but loses the faces entirely.
- The figures need more Reiniger finesse: thinner limbs, more cut detail, and clearer profiles against the light.
- The bottom third is heavy black. The water strips may need to rise.

## 3 · Le jardin trouvé (archive-led: 1927 footage + foraged shoe)

**Beat and time.** First appearance, ≈14 s, and the same frame at ≈7 s for the alternate.
- A real 1927 shot: a walker on the jungle shore.
- The foraged wedding shoe floats on the bright water beyond the trees, partly hidden behind a trunk.
- Caption: « Sur l'eau, une chaussure de mariée. Personne ne bouge. »

**Material.**
- **Foraged:** the RC-B clip, a real 10.5 s shot, and the SHOE.

**Technique.**
- **#29 GrabCut:** the shoe matte.
- **#45 Occlusion Compositing:** a luminance key on the plate makes the dark trunks a holdout, so the shoe passes behind them.
- **#41 Secondary Dynamics:** bob, ripple and reflection.
- **#27 Remotion EDL:** cut fixtures.

**How it moves, frame by frame.**
- The footage plays as it is.
- The shoe is composited on a drift path, with its holdout matte recomputed from each source frame so that the trunks occlude it correctly.
- The reflection is re-rippled each frame, with a slight bob.
- The other people and the crossing would have to be cut together from other Crusoe reels (RC-A, B, C: the shore, the hut, the ladder).

**Risk.**
- **This is the weakest direction.** The archive holds no three-person flood crossing, no plank and no bag. The Hard proof's physical law cannot be staged with real footage; it could only be implied by montage.
- The 320x240 source upscales to visible blocks.
- The walker is a single costumed Crusoe, not a group.
- It is the one archive-led slot. I would keep it only as a texture source for direction 1.

---

## Recommendation

**Direction 1, *Trois sur la planche*.** It is the only one that keeps:
- the reference's mid-grey, mud-and-sweat photographic tonality, with a crowded jungle on the far and near planes;
- legible faces and hands;
- the physical law of the Hard proof as a visible mechanism: one occupant on the plank, a holder for the shoe, a holder for the bag. Every frame can log it, the 7 s alternate can be compared against it, and the foraged shoe stays the one alien photographic object among cut paper.

Borrow from direction 2 its scratched ORDRE ledger and its sliding water strips, which could serve as a second water plane in front of the IA texture.

Before any build:
- give the puppets a second modelling pass;
- confirm the archive pages for the 1927 and 1920 films;
- retry Commons, once the rate limit lifts, for a sharper public-domain black-and-white jungle plate to replace the 320x240 Crusoe stills.
