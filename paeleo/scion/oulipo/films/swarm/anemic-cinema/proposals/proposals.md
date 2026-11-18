# Anémic cinéma: three proposed directions

**References.**
- `assets/references/spiralTextPom.webp` (Centre Pompidou film strip): three frames of a lit, sphere-shaded grey plate on black. White sans capitals run clockwise in an inward spiral, with letter tops facing out.
- `assets/references/duchamp2.webp` (MoMA): cream nested eccentric rings with fine engraved grooves, on black card.
- Both are monochrome and silent, with a centred disc in a black field.

**Every keyframe** is 1280x720, monochrome with a slight warm cast, and has one centred disc on black. The builder is `proposals/kf.py`. It is deterministic and asserts that glyph order equals token order: the GlyphPath list is printed when it runs.

**Shared timeline** for a ~60 s film, with the Hard proof stretched about 2.5x:
- 0–4 s: title.
- 4–14 s: optical A, which **expands toward the eye**.
- **14.0 s: switch A → text 1.**
- 14–24 s: text 1.
- 24–34 s: optical B, which **recedes**.
- 34–46 s: text 2, the **reading disc at its chosen speed**.
- 46–56 s: still pass, a three-frame strip of the reading disc with no motion.
- 56–60 s: end.

**Exposure score.** It uses an integer frame clock at 24 fps. Disc types alternate strictly (O, T, O, T). The only sound is a declared pulse at each switch, otherwise silence.

**Baseline.** The control is the same discs with no switch event: optical A held for the full 20 s, and text 2 alone at the same speed.

**Downloads:** 0.8 MB in total, in `films/sources/anemic-cinema/`.
- One Commons thumbnail.
- Three frames decoded with ffmpeg from the local Moving Image Archive cache.

**Rejected.** I searched the cache (`record|turntable|wheel|spinning|potter|lathe|disc`, sheet looked at) and found three candidates:
- *Have I Told You Lately* (1958) turntable: colour, oblique, a modern deck.
- *POTTERY, ca. 1926* potter's wheel: the right year, but too soft at 320x240, and the wheel is seen edge-on.
- *What's It to You?* kaleidoscope: no licence trail.

Commons returned 429 on most searches, so the second search (bell interiors) was dropped.

---

## 1 · Cire chaude (archive-led: foraged footage, printed negative, with engraved type)

**Beat and time.** The reading disc legible at its chosen speed: text 2, ≈34–46 s, with the frame at ≈38 s.
- Shellac is poured on a recording plate in a 1942 record factory. The poured pool becomes the text disc.
- Printed as a negative, the dark pool turns into a lit grey plate on black, which is the reference's tonal arrangement.
- An original pun is engraved on it as an inward clockwise spiral, laid on the pool's own plane: an ellipse fitted to the pool, then an affine map from the flat disc.
- The pun: « ON SONNE LE BAN SUR LE BANC DE LA GARE · LA CLEF DES CHAMPS N'OUVRE QUE LE CHAMP DES CLEFS (PORTE CLOSE) ». It plays on *ban/banc* and the chiasmus *clef des champs / champ des clefs*, built on the station seed's bench, key, bell and shut door.

**Material.**
- *Command Performance* (1942), Wm. J. Ganz Co. for RCA Victor, a Prelinger Archives film. archive.org item `0534_Command_Performance_E00150_23_01_06_08`.
- Moving Image Archive clip `b3ef2f32`, 320x240, at 7.6–8.0 s of the clip ([page](https://www.movingimagearchive.com/sources/command-performance-66691535?clip=b3ef2f32-ea89-5744-8940-c804848c95e0)).
- **Licence unverified.** It is a Prelinger 1942 sponsored film, and probably PD-US through non-renewal. The archive.org metadata (read 2026-11-16) has **no `licenseurl` and no `rights` field**.
- The fallback is `gov.dod.dimoc.26387`, *Modern Manufacturing: Command Performance* (1963), a record-making film listed **CC0** on archive.org. archive.org downloads are blocked here, so it needs a Commons copy or a confirmed cache clip.

**Technique.**
- **#53 Atlanta Moving Image / #54 Provenance Graph:** archive plate with a per-frame ledger.
- **#28 After Effects mask-and-plate:** pool matte by threshold and largest component, then `fitEllipse`.
- **#6 Whitney Harmonic Motion:** text angle θ(t) = θ0 + ω·t, with ω the declared reading speed of 0.09 rev/s. Fixture: θ(t + 1/ω) ≡ θ(t) mod 2π.
- Kinetic typography: GlyphPath on an Archimedean spiral.

**How it moves, frame by frame.**
- The footage runs 1:1 at its native rate: the pour settles and the spindle glints.
- On each frame, the type plate is rotated by ω/24 rev in the disc's flat coordinates, then re-projected through that frame's ellipse fit, so the words stay on the pool as it spreads.
- The still pass shows three negative frames on a strip.

**Risk.**
- The source is 320x240, so 3x upscaling leaves soft, blocky matte edges (visible at the pool's right lobe).
- The pool is not round, and reflections print as black blobs.
- The negative is an operation on the footage, but it can read as a filter.
- The licence is unconfirmed.
- This is the one archive-led direction. Animation only lives in the type.

---

## 2 · Le cerne se délie (animation-led: procedural disc, drawing substitution at the switch)

**Beat and time.** **The switch itself, the principal event in the thesis:** optical A → text 1 at **14.0 s**. The frame is the sixth of a 12-frame substitution.
- A cream disc of seven nested eccentric rings, each with engraved grooves, is turning.
- The outer three rings have already become the spiral sentence. The fourth is breaking into letter-length dashes. The inner three are still rings.
- The eye that was pulled into depth is handed a line to follow, outermost turn first.
- The pun: « LA PORTE DE SERVICE NE REND PAS SERVICE · LE SERVICE DE LA PORTE NE REND PAS LA PORTE » (the service door that stays closed, from the seed).

**Material.** Handmade: the disc artwork is fully procedural and original.
- Ring centres walk along a diagonal at 0.32 px per px of radius. Widths alternate at 15 and 20 px, with a groove pitch of 3.1 px.
- The plate is sphere-lit, and the letters are cut from the same groove stock.
- No foraged pixels and no reference pixels.

**Technique.**
- **#6 Whitney Harmonic Motion:** constant ω across the switch, so speed is held and only kind changes.
- **#7 Foldès Drawn Metamorphosis** and **#39 Drawing Substitution:** each ring is replaced by its glyph run.
- **#8 Sutherland constraints:** the glyph spiral's turn k must lie on ring k's radius band.
- Kinetic typography.

**How it moves, frame by frame.**
- At frame 336 (14.0 s) the substitution begins. Every 2 frames, ring k (from the outside in) is cut into dashes, and on the next frame each dash is swapped for the glyph whose arc it occupies.
- Over frames 336–347 all seven rings become the sentence, and the disc never stops turning.
- After the switch, text 1 runs at its reading speed. Optical B later runs the substitution in reverse, from letters back to rings.
- The ExposureSequence counts the transitional frames as belonging to the incoming disc, which keeps the strict-alternation fixture.

**Risk.**
- In this frame, two spiral turns crowd each other (pitch 44 px at 30 px type). Turn spacing needs to open by about 15 %.
- The hybrid frame may read as a design object rather than as an event, and only motion tests can tell.
- Apparent depth from eccentric rings depends on rotation speed and on the offset, which is not tuned yet.

---

## 3 · Anneaux de clefs (animation-led: collage cutout optical disc)

**Beat and time.** Optical A **expanding toward the eye**, ≈4–14 s, with the frame at ≈8 s.
- The optical disc is built from cutouts of a single real iron key, the station seed's key left on the bench.
- Five eccentric rings of keys sit on a black card plate. Each ring is a chain of keys laid tangentially, bow to bit, and the rings get smaller and more offset toward the centre.
- As the plate turns, the off-centre chains wobble against each other the way Duchamp's eccentric rings do, so the tunnel seems to push out.
- Optical B uses the reverse offset order, so it recedes.

**Material.**
- *Skeleton key (Yale & Towne).png*, Wikimedia Commons, by User:Noy-nac, **CC BY-SA 4.0**. 1280 px thumbnail of `File:Skeleton_key_(Yale_&_Towne).png`. It needs an author credit and share-alike.
- The plate, the layout and the light are handmade.

**Technique.**
- **#29 GrabCut:** a real `cv2.grabCut` matte, seeded by luminance, with the border marked as background, keeping the largest component.
- **#3 Ernst collage grammar / #43 Collage Graph Rewriting:** a key becomes a ring member.
- **#44 Multiplane:** each ring can sit on its own plane for a later variant. In the proof all rings stay on one flat plane, as the invariant requires.
- **#6 Harmonic Motion:** one ω for the plate, with ring centres rotating with it.

**How it moves, frame by frame.**
- Each frame rotates the whole card about the screen centre by ω/24 rev, at 0.5 rev/s. The keys are rigid cutouts, re-pasted at their rotated pose, with no warping.
- The eccentric centres orbit with the plate, so the rings slide against each other and the stack appears to bulge toward the viewer.
- An optional paper-shadow layer (1 px offset) gives the cutouts physical presence. It is still to be added.

**Risk.**
- The keys still overlap slightly at bow and bit, and the orientation reads a little loose. The chains need tighter spacing so each ring reads as a ring and not as scattered keys.
- The depth illusion is weaker with broken outlines than with Duchamp's continuous rings, so it may need a faint guide ring under each chain.
- It has only an optical disc; its text discs would have to borrow from 1 or 2.

---

## Recommendation

**Build 2, Le cerne se délie, as the spine, with direction 3's key-chain disc as optical B.**
- Direction 2 is the only one that shows the thesis's principal event, the switch, as a frame-by-frame act. It also keeps speed constant across the switch, as section 8 requires, so the test is clean.
- It is fully handmade and licence-free, and its tonal range is the closest to both references: cream grooved stock and a lit grey plate on black.
- Adding the key rings as the receding disc B brings real foraged matter (CC BY-SA, credited) into the optical half. It also ties the discs to the seed's key without costume.
- Keep direction 1 as a declared archive variant only if the *Command Performance* licence is confirmed. Its 320x240 source is the weakest material on the board.
- Before the swarm build, open the spiral pitch in 2, tighten the chains in 3, and tune the ring offset at 0.5 rev/s, measured at 100x for aliasing.
