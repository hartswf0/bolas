# Boucle-là !: three proposed directions

**Reference.** `assets/references/extract-001.webp` is Lécroart's page.
- Four rows of black-and-white ink panels: white grounds, some spot-black night panels.
- The figures are big-nosed caricatures, and the man wears spectacles.
- The balloons are hand-lettered in capitals.
- The panel sequence comes back reversed around a central line, and the meaning turns on it.
- The title "boucle-là !" is lettered in the left margin.

**The stage, shared by all three directions.** This is the user's note: keep the comics page grammar as the stage and animate it.
- **Grid:** one 16:9 page of seven occurrences. Row 1 is A B C, row 2 is a wide hinge panel H, and row 3 is C B A.
- **Margin furniture:** a hand-lettered title column ("LE MOT / OU QUI L'A LAISSÉ ?"), a drawn loop arrow and the path A B C H C B A. It sits outside the mirrored sequence.
- **Lettering:** handmade for this film. `kf_common.py` defines a single-stroke capital alphabet as pen polylines and inks it with a round pen. The jitter is seeded per balloon, so a repeated balloon is the same drawing, not a re-render.
- **Reading order:** the page is read in order. A panel animates only while it is being read and then holds its last drawing, the way a page holds still. Row 3 waits as a pale ghost of the same art until the loop comes back to it.

**Hard proof, the same in all three.**
- Two people dispute who left a note. Odette holds it throughout.
  - **A** (Odette, accuses): "ET ÇA ?! C'EST TOI QUI L'AS LAISSÉ, CE MOT ?"
  - **B** (Gustave, denies): "MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ?"
  - **C** (Odette, presses): "ALORS DE QUI IL EST ?!"
  - **H** (Gustave): "« À MA CHÈRE ODETTE... » TIENS. C'EST POUR TOI." The note turns its lettered face to the reader.
- **After the hinge,** the same C B A return with identical art and balloons.
  - C becomes a flustered deflection.
  - B becomes his sarcasm ("you think I'd write *you* notes?"), and now he holds the leverage.
  - A becomes her lame counter-accusation.
- **Fixture:** `kf_common.assert_fixture()` asserts that the sequence mirrors around H and that H is the single unpaired occurrence. The art cache is keyed by letter, so a pair is literally one image.
- **Baseline:** the same seven panels read as A B C H only, with no return.
- **What the viewer should point to:** the same "MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ?" balloon, now a jab instead of a defence.

**Clock (a 62 s film).**

| Beat | Time |
|---|---|
| Title | 0–4 s |
| A, B, C | 7 s each, 4–25 s |
| H | 25–35 s |
| C, B, A | 35–56 s |
| Full page held with speech-act labels | 56–62 s |

Sound: one short repeated voice murmur per occurrence (identical for each pair) and one bell at the hinge.

**Keyframe beat, all three.** **t = 31 s**, inside H: the note is turned so its face "À MA CHÈRE ODETTE" reads, and the accuser recoils. Rows 1 and 2 are inked and row 3 is still a ghost.

**Builders.**
- `kf1.py`, `kf2.py` and `kf3.py` are deterministic and share `kf_common.py`. Run each as `python3 -I kfN.py` from this folder.
- The board is the reference beside the three keyframes, 2000 px wide.
- Sources are in `films/sources/boucle-la/` (git-ignored, about 5.3 MB in total).

---

## I · Ombres de la boucle: articulated cut-paper silhouette puppets (kf-1.png)

- **Beat:** H at 31 s, pose 7 of 12.
  - Gustave leans in and points at the note.
  - Odette holds it out face-first and recoils, with her head back and her back hand going to her mouth.
- **Material: all handmade, nothing foraged.**
  - Two black cut-paper puppets made for this film, in Lécroart's types.
    - **Gustave:** stout and bald, with a hair tuft, a bulbous nose and spectacles cut as a ring.
    - **Odette:** bun, curl, upturned nose and a bell skirt.
  - Their internal details are cut-outs, Reiniger-style: eye slits, the spectacle ring, coat buttons, lace collar holes and hem scallops.
  - The props are also cut paper: table, carafe and hanging lamp.
  - Each panel is lit from behind: a backlight pool with paper fibre.
  - The note is the only white paper object in black hands, so it carries the reveal.
- **Technique SCIONs:**
  - **2** Reiniger articulated shadow theatre
  - **32** forward kinematics
  - **38** dynamic pose selection
  - **48** state machines, for the reading route
  - **47** sound-to-action, for the murmur and the bell
- **How it moves, frame by frame (12 drawings/s, on 2s):**
  - Every puppet is an FK rig: hip lean, a neck pivot for head tilt, and two-bone arms with replaceable hands (mitten, point, open).
  - Each frame is cut fresh from joint angles, so nothing is a warp.
  - Each occurrence is a 12-pose arc between two keyed poses, with a 3-drawing settle.
    - **A:** her arm rises with the note.
    - **B:** his "Moi ?!" shrug, with both hands opening.
    - **C:** her pointing lunge.
    - **H:** he leans and points; the note turns from back to face over 4 drawings; she recoils.
  - The pair occurrences replay the same exposure sheet. The art does not change; only the adjacency does.
- **Risk:**
  - The puppets are geometric polygons. Next to Lécroart's fluid pen they can read as clip-art.
  - Silhouette loses facial expression, so the leverage shift has to come from posture and the note alone.
  - Fix in the build: hand-drawn replacement heads per pose (SCION 38), and finer cut-out lacework.

## II · Daumier à la colle: articulated collage cutouts from a real 1839 lithograph (kf-2.png)

- **Beat:** H at 31 s. The couple's heads tilt toward each other over the note, which is turned face-out between them. The hinge panel goes to spot black, as Lécroart's night panels do.
- **Material:**
  - **Foraged:** Honoré Daumier, *Mœurs conjugales* no. 3, "Et les cinq francs de ce matin ?…"
    - Rijksmuseum RP-P-OB-41.183, via Wikimedia Commons, licence **CC0**.
    - Source: https://commons.wikimedia.org/wiki/File:Echtpaar_bespreekt_huishoudelijke_financi%C3%ABn_in_de_slaapkamer_Et_les_cinq_francs_de_ce_matin_(..)_(titel_op_object)_Gezinssituaties_(serietitel)_Moeurs_conjugales_(serietitel_op_object),_RP-P-OB-41.183.jpg
    - The 960 px standard thumbnail is used.
    - It is a real married couple quarrelling face to face, and the man has a big nose: the caricature lineage Lécroart descends from.
  - **Handmade:** the note, the lettering, and the few inked set lines (floor, wall rail).
- **Technique SCIONs:**
  - **1** Gilliam cutout metamorphosis
  - **29** cutout extraction
    - Tonal matte against the crayon vignette, inside a hand-set scissor envelope, then re-cut as straight snips.
    - This is not GrabCut: GrabCut was tried, and it failed on this print.
  - **32** FK joint pins
  - **45** occlusion compositing, with contact shadows and paper-on-paper underlaps at the joints
  - **43** collage rewriting: the towel in the print is removed and the note takes its place
- **How it moves, frame by frame (on 2s, with Gilliam's paper jerk):**
  - Each figure is three pieces: body, head pinned at the neck, and forearm pinned at the elbow.
  - Every frame re-composites the pieces with rigid rotations only: head nods on every stressed syllable of the murmur, forearm lifts, a whole-body lean about the feet.
  - **A:** her forearm lifts the note.
  - **B:** his forearm flips up and his head jerks back on "MOI".
  - **C:** her lean forward.
  - **H:** both heads swing in over 6 drawings. The panel cuts to black on the bell, and the note turns face-out.
- **Risk:**
  - Daumier's grey crayon is softer and greyer than Lécroart's crisp pen. At page scale the panels read pale, and the man's forearm cut still carries fragments of her fingers.
  - Fixes in the build: a second print for replacement poses (the Commons search found more CC0 *Mœurs conjugales* plates, still to download under rate limits), and a hand-cleaned forearm cut.
  - The tone curve already pushes the crayon toward ink.

## III · Rotoscope au lavoir: a real 1915 quarrel rotoscoped into pen and ink (kf-3.png)

- **Beat:** H at 31 s.
  - Fatty reaches at her chest. She gasps, holding the note.
  - An iris insert, in period silent-film grammar, shows the note's face "À MA CHÈRE ODETTE".
- **Material:**
  - **Foraged:** *Mabel and Fatty's Wash Day* (Keystone, 1915), Library of Congress, item mp73105700, resource ntscrm.00013268.
    - The LoC says "not aware of any U.S. copyright or other restrictions". The film is a 1915 US release, so it is **public domain**.
    - Segment: 156–172 s, read by HTTP range-seek through the proxy (no full 610 MB download), as 192 frames at 12 fps.
    - Source frames: A = f169 (she raises the note), B = f113 (his open-mouthed "Moi ?!"), C = f129 (she points at his face), H = f89 (he reaches, she recoils).
  - **Handmade:** the note composited into her hand, the iris insert, and the lettering.
- **Technique SCIONs:**
  - **28** matte and performance-plate foundry
  - **30**-style figure masks
  - **38** dynamic pose selection: choosing which real frames carry each speech act
  - **47** sound-to-action
- **How it moves, frame by frame:**
  - Each occurrence plays its own run of real frames, about 1.5 s of performance, re-inked every frame at 12 fps.
  - The inking:
    - spot blacks for the dark kitchen
    - a pen contour from the tonal matte
    - XDoG and fine-edge pen lines for faces and folds
    - 45° hatching for the mid-tones, so the line boils the way hand rotoscope does
  - Each run then holds its last drawing.
  - The return C B A replays the *identical* inked frames.
- **Risk:**
  - **Fails "no filter over material"?** The automatic inking still reads partly as a filter, and faces lose detail.
  - **Cost of a real build:** keyed contour splines per drawing, tracked between keys and hand-corrected, before the pen pass.
  - **Note continuity:** her note is composited into real hands that never held it.
  - **Archive limit:** this is the archive-led direction. It is animation by technique, but its acting is borrowed.

---

## Recommendation

**Build I, Ombres de la boucle, and fold in II's hinge black.**
- **Why I fits the formal claim best.** The palindrome needs the *same drawing* to change meaning, and an FK puppet makes that literal: one exposure sheet, replayed. The defining beat (the white note turning face-out between two black figures) reads instantly in grayscale and at thumbnail size.
- **Why it is the most animation-led.** Every frame is cut from joint angles, and nothing is borrowed acting.
- **What to protect:**
  - the handmade lettering, with identical seeds for each pair
  - the ghost of row 3 waiting
  - the note as the only white object
- **Largest gap:** the puppets' geometric stiffness. Spend the build on hand-drawn replacement heads and hands (SCION 38), and on a spot-black H panel borrowed from II.
- **If the user prefers foraged texture,** II is the stronger second: it is real caricature lineage under a real CC0 licence.
- **III is the riskiest:** it needs per-frame hand correction before it stops reading as a filter.

*Note on new SCION prompts:* `paeleo/scion/swarms.json` still holds the same 54 animation SCIONs, and nothing in `paeleo/scion` is newer than Nov 15. No new prompts were found; the directions above draw on 1, 2, 28, 29, 30, 32, 38, 43, 45, 47 and 48.
