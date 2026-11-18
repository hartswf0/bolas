# Monsieur Ripois: three proposed directions

**Reference.** `assets/references/ripois1.webp` is a black-and-white studio still with a long tonal range: a hard key light, deep blacks in the suit, and bright skin and silk.
- The teller (dark hair, pinstripes) holds an open silver box toward the woman.
- She listens in profile. Her hair is up, with a drop earring and a bare shoulder.
- The décor is a cluttered salon (leopard throw, lamp), and the framing is a 4:3 medium two-shot.

**Defining beat.** The Hard proof asks for a visitor who claims he returned a borrowed object, a flashback that hides one gesture, and a clue that lets the listener decide differently. Here the object is the box from the reference, with a ring in it. The film runs about 45 s:
- **0–8 s:** present-tense encounter. Claim C1: « Je la lui ai rendue. »
- **8–24 s:** his flashback (E2, marked as his perspective). The box is opened and the ring is in it. His far hand stays out of sight.
- **24–34 s:** back on the sofa. The listener's look drops to the box.
- **34–42 s:** the clue (E3), a pawn receipt dated the day of the "return".
- **42–45 s:** her decision (she gets up, or she keeps the receipt).

**Baseline (control).** The same cut with E3 removed and her reaction held at neutral. C1 and E2 then read as consistent.

**Frames.** Every keyframe is 1280x720 with a pillarboxed 4:3 picture. Captions are the voice: 1950s release-print subtitles, white serif italic. The builders are in `proposals/src/`: `common.py`, `kf1.py`, `kf2.py`, `kf3.py`, `board.py`, plus rig JSONs. All are deterministic.

**Foraged pool.** About 2.3 MB in `films/sources/monsieur-ripois/`. Every item is from the Library of Congress FSA/OWI Black & White Photographs collection, marked **"No known restrictions on publication"** (US government work, public domain). The 1024 px service JPEGs were used.

| id | LoC item | what | used in |
|---|---|---|---|
| V0 | 2017831564, John Vachon, 1942, "Jim Tillman and his girl in the lounge of the student union", Lincoln NE (`8d04830v.jpg`) | a man talking and a woman listening on a striped sofa: the reference's staging, mirrored | KF1 plate and puppet pieces; KF2 far-plane window |
| B1 | 2017848680, Esther Bubley, 1943, Washington DC, Sea Grill: "drinking beer and exchanging life histories" (`8d27149v.jpg`) | a dark-haired woman with a drop earring, in profile, listening to a soldier | KF3 |
| B2 | 2017848664, Bubley 1943, "Girl and a soldier came into the Sea Grill separately…" (`8d27133v.jpg`) | a close face-to-face two-shot | spare: alternate reaction cut |
| V1, V3, B0, B4 | 2017831565 / 2017831567 (Vachon, wider lounge), 2017848653 (Bubley, girl alone), 2017853043 (Bubley, card room) | | spares: establishing shot, "after" shot |

**Moving Image Archive cache.** Searched (`couple|sofa|living room…`, `hand|box|receipt|jewel…`, `conversation|talking…`, `woman…profile|glance`). It holds no intimate two-shot in a salon. The nearest were *Party Magic* 1938 (a living room in colour), *Beginning to Date* 1953 (dance-floor crowds) and *All My Babies* 1953 (an embrace). It does hold two hand inserts that fit the hidden gesture:
- `af625567`, *Bookkeeping and You* (1947): a hand with a ring.
- `aaf17c56`, *Learning to Set Type* (1959): low-key hands closing over a small dark object.

These are kept as E2 or insert candidates for direction 3. Their licence must be confirmed on the MIA source page before use; I assume Prelinger and public domain, but this is not verified.

**Wikimedia Commons** rate-limited this session after two searches, so nothing was taken from it.

---

## 1 · Le canapé articulé (photo-cutout puppetry on a foraged print), animation-led

- **Beat, 0:26.** Back in the present, after the flashback. He says « Je la lui ai rendue, sa boîte. Rien n'y manquait. » The open box lies on her lap. Its velvet cushion shows an **empty ring slit**. Her head has tipped about 11° down toward it, under his clause "Rien n'y manquait". This is the listener's shift, put under the same line as the repair rule asks.
- **Material.**
  - Foraged: V0 (Vachon, PD).
  - Handmade: the silver box, drawn as its own lit layer: mirror lid, engine-turned front, velvet with a pressed ring hollow and slit, and a contact shadow.
- **Techniques.**
  - **#11 Video Puppetry Tabletop / #40 Paper Performance:** the print is cut into card pieces.
  - **#29 GrabCut:** hand-seeded mattes. A drawn outline gives probable foreground and its eroded core gives definite foreground.
  - **#32 Forward Kinematics:** pivots at her neck (340, 312) and his (585, 255), recorded in `src/kf1-rig.json`.
  - **#45 Occlusion Compositing:** the vacated plate is inpainted, and a contact shadow sits under each piece.
  - **#47 Sound-to-Action:** her head move is keyed to the syllable "man-" of "manquait".
- **How it moves.**
  - The plate is locked off.
  - His head is keyed on twos: 0° to +3° while he leans in on "rendue", then back.
  - Her head holds at 0° until the cue. It then eases to −11° over 8 frames and holds. Her eyes stay on the box through the cut to E3.
  - The box lid closes by 2 drawings (it is a separate card layer) when he notices the look.
  - The alternate reaction cut moves her head drop to the end of the line ("…manquait" plus 12 frames), to test early versus late suspicion.
- **Risk.**
  - The figures are a 1942 student couple, not 1950s Paris glamour: the hat, the glasses and the soft light are less sculpted than the reference's key.
  - The source is 1024 px, upscaled 1.8x, so it is soft.
  - The handmade box is still too clean against the photograph and needs a photographed real box or a dirtier render.
  - The inpainted neck seam shows slightly at −11°.

## 2 · Ombres du retour (articulated shadow theatre of his flashback), animation-led

- **Beat, 0:14.** E2, the return as he tells it, labelled « — selon lui — ». He holds the open box out to its owner, and the ring stands in its slit (a punched light-ring in the card). His **far arm is bent behind his back**, and in silhouette that hand is simply not there. Only the elbow jutting past the jacket line is a trace. That is the consequential gesture the telling hides. Caption: « Elle l'a ouverte devant moi. La bague y était. »
- **Material.**
  - Handmade: two jointed card puppets. She has a chignon, drop earring, open palm and wing chair with punched lace. He has a slicked quiff, a lapel notch and pin-hole rivets at the joints. Also handmade: the standard lamp with a light slot, the door frame he came in by, and the scalloped floor rail. The screen is backlit warm paper with fibre noise.
  - Foraged: the far plane is the lounge window blinds from V0, thresholded and blurred, printed faintly behind the paper.
- **Techniques.**
  - **#2 Lotte Reiniger Articulated Shadow Theater.**
  - **#32 Forward Kinematics:** shoulder, elbow and wrist chains, with angles in `src/kf2-rig.json`.
  - **#44 Multiplane Parallax:** the far window sits a stop softer and drifts 0.3x.
  - **#45 Occlusion:** what the body hides is the hidden gesture.
  - **#41 Secondary Dynamics:** the earring swings, and the lid has a small bounce.
- **How it moves.**
  - Shot on twos.
  - His walk-in from the door: 8 poses.
  - The box offered: 6 drawings.
  - The lid opened with her hand: 4 drawings.
  - The back arm: upper arm 84° then 96°, forearm 196°. It is keyed so the hand enters the torso silhouette and stays there for the whole scene.
  - The paper warms 5 % during the flashback and returns to neutral at the cut, so the recollection reads as perspective (invariant: E2 is never presented as verified).
  - The second teller's branch replays the same puppets with the back arm visible, from the doorway's side light.
- **Risk.**
  - The puppets are still crude and need a proper cut-paper drawing pass: hands, profiles, the woman's skirt.
  - Shadow theatre pulls toward fairy tale, away from the reference's photographic salon. I would intercut it only with photographic present-tense shots, which means pairing it with direction 1 or 3.

## 3 · Le reçu sur la table (archive montage plus a handmade receipt), archive-led

- **Beat, 0:36.** E3, the clue. At the Sea Grill table (B1) she listens. Dark hair up, drop earring, in profile, the reference's listener almost exactly. He says « Je la lui ai rendue le 14 mars, en main propre. » On the table, in her line of sight, lies a handmade pawn receipt: « PRÊT SUR GAGES · Bureau auxiliaire n° 7 · Engagé le 14 mars 1953 · une bague or, un brillant · 9 000 F · Déposant : A. R. » with an ENGAGÉ stamp. The dates match and contradict him.
- **Material.**
  - Foraged: B1 (Bubley, PD). B2 serves as the reaction alternate. The MIA hand-with-ring clip (*Bookkeeping and You*, 1947) is the E2 insert, with licence still to confirm.
  - Handmade: the receipt. It is a typeset form with Courier labels and the clerk's hand in italic. It has a stamp off-axis, paper tooth and a centre fold, and is laid on the photographed table by a perspective warp. Its focus, falloff and contact shadow are matched to the print's high-left key.
- **Techniques.**
  - **#27 Remotion Declarative Film Compiler:** an EDL drives cut A (no receipt) and cut B (receipt).
  - **#45 Occlusion Compositing:** the receipt sits under the hands' shadows.
  - **#50 Library of Congress Historical Print Stage.**
  - **#54 Provenance Graph:** a claim/evidence ledger with C1, E2 and E3 as distinct entries.
- **How it moves.**
  - The photographs are held as shots, cut by the EDL with no Ken Burns drift.
  - The MIA insert plays at its real speed: the hand closing.
  - The receipt is slid into frame by her own hand over 14 frames. It is a translated, re-shadowed layer. Then there is a hard insert on the date line.
  - The reaction alternates: B1 (still smiling) or B2 (leaning close) is placed under "en main propre" or after it.
- **Risk.**
  - This is mostly an edit, not animation.
  - The table occupies only the bottom of B1, so the receipt is small in the master and needs its insert.
  - There are three figures in B1, so the second soldier must be cropped out or used as the second teller.
  - The MIA clips are 320x240.

---

## Recommendation

Make **1 + 2 as one film: Le canapé articulé for the present tense, Ombres du retour for his flashback.**
- Two different animation media keep claim and evidence materially separate. The photo-cutouts are the present and the room's evidence. The shadow cards are his account, a perspective by construction, and they fail the "E2 shown as verified" fixture only if we let the paper look neutral.
- The hidden gesture becomes a real property of the medium: the hand inside the silhouette. The clue is the empty ring slit in the box on her lap, the same object in both media.
- Direction 3's receipt can join as the final E3 insert, a handmade prop, without making the film archive-led. B1 is the strongest match to the reference's listener and should be kept as the reaction alternate.
- **Before the swarm build:**
  - Replace the drawn box with a photographed or better-rendered box.
  - Redraw the puppets properly.
  - Confirm the MIA licences, or drop the MIA clips.
