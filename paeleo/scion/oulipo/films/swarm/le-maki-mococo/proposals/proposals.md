# Le Maki Mococo: three proposed directions

**Reference:** `assets/references/maki.webp`. It is an extreme close-up of a mouth in profile, facing right, with the lips parted and the teeth showing.
- The face fills the left third, cut off at the nose and the neck.
- The right two thirds are a blank, pure white field.
- It is high-key and soft, with warm flesh, rose lips, no type and no props.
- The whole film is one reader's mouth meeting one strange word.

**Frames.** Each keyframe is 1280x720. The builder is `proposals/kf.py`, which is deterministic (`python3 -I kf.py`). The board is `board.jpg`: the reference plus the three keyframes, labelled.

## The proof (frozen for all directions)

**Poem.** It is original, written for this study. The unfamiliar animal name is a real animal, the binturong (bearcat).

> In the dark it hangs and swings,
> binturong, binturong,
> smells of popcorn, never rings —
> binturong, binturong.

**Cue order.** Each cue is a `Cue{channel, t, line}`. The poem never changes; only the cues are added.

| t | cue | reader response (clearly fictional, captioned, no TTS) |
|---|---|---|
| 0:02–0:08 | **sound**: the poem is spoken, with no text on screen | — |
| 0:10 | | **Guess 1**, Reader A: "A gong? Something you strike — bin, tu, RONG." |
| 0:16–0:22 | **text**: the poem typesets, one letter per read syllable | — |
| 0:24 | | **Guess 2**, Reader B: "It hangs and swings… a lantern? A bell that's gone quiet?" |
| 0:38 | **image**: the binturong (Brehm 1895 engraving) | — |
| 0:44–0:52 | | **Reconsideration**, Reader A: "Oh — it hangs by its tail. 'Never rings': it was never a gong." |
| 0:52–0:60 | the poem again, unchanged, with "hangs" marked | — |

**Fixture.** No caption may cite a cue that was released after it. Guess 1 can cite only the sound, guess 2 the sound and the text. The cue strip in each frame (● released, ○ not yet released) makes the release order inspectable on every frame.

**Defining beat.** The viewer should be able to point at the word **"hangs"**: it means hanging like a gong at 0:24 and hanging by a tail at 0:44.

**Baseline.** The same poem and captions, but with the image shown at 0:02 (the image-first condition). There, guess 1 should already be "an animal".

**Downloads:** about 1.9 MB in total, in `films/sources/le-maki-mococo/r1/`.
- **`brehm265.jpg`**: *Brehm's Life of Animals*, vol. 1 *Mammalia*, p. 265, "The Binturong". The engraving is signed Specht and dates from the 1890s English edition. Wikimedia Commons, `File:Brehm's Life of animals (Page 265) (6220164475).jpg` (BHL/Flickr scan), **Public domain** (read from `extmetadata.LicenseShortName`).
- **`bertuch.jpg`** is a spare that is not used yet: F. J. Bertuch, *Vierf. Thiere XLII* (c.1800), a hand-coloured civet plate. Commons, Public domain.
- **Logic By Machine (Part II)** comes from the local Moving Image Archive cache, clip `6b7a3bcf`, source 224.9–263.3 s, so it was not a new download. It is archive.org `logic_by_machine_2`, `licenseurl` creativecommons.org/licenses/publicdomain, which makes it **Public domain** (Prelinger). Its page: https://www.movingimagearchive.com/sources/logic-by-machine-part-ii-a22d2554?clip=6b7a3bcf-f109-5944-a0c6-43ba31fa5ff6

**Not found.**
- The cache has no clean speaking mouth in profile on white. Its other face hits are a child watching (1941/1948) and an old man staring, all frontal and with their mouths closed.
- Commons returned no public-domain gong or bell engraving on a first search (a 429 and Wellcome portraits came back), so the gong is handmade.
- The Farquhar *Bentoorong* watercolour (1819–23, PD) is on Commons, but its file download returned an error page, so I did not use it.

---

## 1 · Lecture Profile (foraged film + scissor cutout + sound trace; the one archive-led direction)

**Beat and time.** Guess 1, at **0:10**. Only the sound has been released. The man's mouth is open after "RONG", and the trace of what he heard runs out of his lips into the white field. No word of the poem is visible yet.

**Material.**
- The frame is *Logic By Machine (Part II)* at 1.17 s into the clip: a man in profile in front of a blackboard (PD, Prelinger).
- I cut him from the grey board by hand along his profile, with points placed on a 3x view, then refined the cut with GrabCut in a 5 px band.
- I laid him onto the reference's white field and tone-lifted him to high-key. He is not mirrored: he faces left, into the white.
- In the keyframe, the trace is the clip's own audio from 0.6 to 2.8 s, standing in for the poem recording.

**Techniques.**
- **#47 Sound-to-Action:** the syllables drive the mouth.
- **#38 Dynamic Pose Selection** is drawing substitution from a library. The clip's 38 s of his speech give about 900 frames, and each is scored for mouth opening (the dark-pixel area between the lips inside the cut). On each beat of the poem, the frame whose opening matches the target viseme is substituted. In practice that is 12 fps on twos, with closed lips for "b", mid-open for "in/tu" and wide-open for "RONG".
- **#29 GrabCut** cuts every substituted frame in the same band.
- **#28 Mask plates:** the trace grows leftward from the lips in sync.

**Risk.**
- The man is a real, identifiable person, and he would be given invented "lines" (captions) and a poem he never read. That conflicts with "clearly fictional performers".
  - The mitigation is to caption him as "Reader A (fictional), image: archive lecturer, 1950s" and never use his voice for the poem.
  - A cleaner fix is to rotoscope him to an anonymous ink line in the build (#7), which pushes this direction toward animation.
- The source is only 320x240. At 3.4x it is soft, though the reference is soft too.
- Frame substitution from a lecture gives only an approximate lip-sync.
- The poem's sound needs a real recorded voice: from the operator, a consenting adult, or a declared silence with a drawn trace.

## 2 · Paper Mouth (handmade articulated cut-paper puppet + kinetic typography)

**Beat and time.** Guess 2, at **0:24**. The sound and the text have been released. The poem is typesetting itself letter by letter, and the cursor has reached "smells of pop". Reader B tries "a lantern? a bell gone quiet?".

**Material.**
- All of it is handmade: an extreme profile close-up of a mouth built from nine pieces of cut paper laid on a white card.
  - Skin: upper face with the nose base, and a lower jaw.
  - A nostril, an upper lip, a lower lip with a highlight, a teeth strip, the mouth cavity and a chin shade.
- Each piece has its own fibre and mottle texture, a scissor-wobble edge, a lit paper edge, and a soft cast shadow on what lies below it.
- The geometry is my own and was not traced from the reference. It matches the reference's framing: mouth on the left, nose cut off at the top, white field on the right.
- The type is Caladea for the poem and Inter for the reader captions.

**Techniques.**
- **#2 Reiniger / #32 Forward Kinematics:** the lower jaw, lower lip and chin are one rig that rotates about an off-screen hinge at (40, 200), 0–9°. The keyframe is at 6°.
- **#38 Drawing substitution:** six cut upper-lip and lower-lip shapes are swapped per viseme. The pins are visible in the frame.
- **#47 Sound-to-Action:** the jaw angle follows the RMS envelope of the poem's sound.
- **#40 Tabletop paper:** pieces lift and drop their shadows a pixel or two when they move.
- **Kinetic type:** each letter lands on the syllable the mouth is saying, so text and sound stay locked to the same segment IDs. At the image cue, the mouth closes and holds, and the text stays fixed.
- The image cue (0:38) is the Brehm engraving cut out and slid in from the right as a paper piece, so it shares direction 3's material.

**Risk.**
- The paper mouth can look like a diagram rather than a speaking person. It needs the cut edges and the jaw motion to carry it, and it must be judged in motion.
- Its lip shapes are simpler than the reference's fleshy close-up.
- The two "readers" are one puppet, so the speakers must be told apart by caption and a paper colour change (Reader B's lip paper is cooler).

## 3 · Gong to Animal (collage metamorphosis: handmade gong becomes the foraged engraving)

**Beat and time.** The reconsideration, at **0:44**. The image was released at 0:38. Guess 1's gong is breaking apart on its cord, and behind it the binturong hangs from the same cord by its tail. The poem's first line has not changed, but **"hangs"** now carries a red-pencil underline.

**Material.**
- The gong is handmade: a bronze card disc with hammered rings, cut into 12 wedges and hung on a cord.
- The animal is the 1895 Brehm/Specht engraving (PD). I cut it out with scissor points along the body and the bushy tail, refined the cut with GrabCut, and left a white paper margin, as with a cutout.
- I then rotated the cutout 52° so that it hangs head-down from the knot on its prehensile tail. That is the fact the engraving's own caption gives: "it has a prehensile tail".

**Techniques.**
- **#43 Collage Graph Rewriting / #3 Ernst:** the identity of the hanging thing changes while the cord, the knot and the word stay fixed.
- **#1 Gilliam cutout metamorphosis:** frame by frame from 0:38, the 12 wedges come loose one per 3 frames. Each falls on a ballistic path with spin, which is **#41 Secondary Dynamics**.
- The gong also swings on the cord as a pendulum, and the swing carries over to the animal: "hangs and swings" becomes literal.
- **#45 Occlusion compositing:** the wedges that are still hanging occlude the animal, and the wedges that fall pass in front of it.
- **#44 Multiplane:** the cord and the animal sit on plane 2, the falling wedges on plane 1, and the type on plane 0.
- At 0:52 the red-pencil underline draws itself under "hangs" stroke by stroke.

**Risk.**
- The gong-to-animal transformation is a strong visual pun. It could tell the viewer the answer instead of showing a reader find it, which is the repair note's "readers jump to one answer".
  - Keep the image cue small and late, and keep the gong whole until the caption at 0:44 exists.
- The palette (cream paper, bronze, b/w engraving) moves away from the reference's flesh and white. It needs the mouth from direction 2 as a bookend to stay in the reference's world.
- The engraving's cut edge is busy grass and fur, so the GrabCut matte needs hand clean-up at film scale.

---

## Recommendation

**Build 2 (Paper Mouth) as the spine and 3 (Gong to Animal) as its image cue. Keep 1 as the comparison branch.**
- Direction 2 is closest to the reference: the same framing, the same white field, flesh and rose, and the mouth as the whole subject.
- It is wholly handmade and fictional, so the consent ledger is trivial.
- Its kinetic type locks text release to syllables, which makes the cue-order fixture visible in every frame.
- Direction 3 then supplies the foraged image (Brehm, PD) at 0:38, and with it the one move the proof needs the viewer to point at: "hangs" reread.
- Direction 1 is the strongest *archive* match (a real profile, a real mouth on white). Its identifiable lecturer is a consent problem for invented lines, though. Use it only rotoscoped, or as the image-first baseline, where he speaks no poem.
