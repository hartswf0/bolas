# Zazie dans le métro: three proposed directions

Reference: `assets/references/zazie1.webp`. It is a 4:3 Eastmancolor close-up of a laughing child, with a warm skin and auburn palette, an orange collar, and a soft, grey-olive city blurred behind. Each keyframe is 1280x720, with the 4:3 picture (960x720) pillarboxed in black so it keeps the Academy framing. Captions are the voice, in French, set in italic serif.

**Defining beat.** A child wants the promised vehicle, and the city keeps changing the terms. The Hard proof is a 20 s pursuit with:
- a setup, 0–4 s: the same plain chase for the tram;
- an impossible-distance jump cut, about 8–10 s;
- a match cut that turns the queue into an obstacle, about 12.4 s;
- a recovery, 16–20 s.

There are three locations: the parade street, the cable-car turntable, and the plaza with its kiosk. The prop is a métro ticket, read three ways: first a ticket, then a spyglass, then confetti.

**Baseline.** The control is a clean continuity cut of the same chase with no gag operation.

**Material.** Everything foraged comes from the local Moving Image Archive cache (`tools/allways-forage`). There were no new downloads, so 0 MB of the budget is used. One Commons search for a period Paris bus came back empty or rate-limited and was not pursued. The script that builds the keyframes is `proposals/kf.py`.

Foraged clips:
- **A.** *[Amateur film: Parade of Krewe of Rex, New Orleans, February 25, 1941]*, colour, clip ed8a925a. https://www.movingimagearchive.com/sources/amateur-film-parade-of-krewe-of-rex-new-orleans-february-25-1941-34c2030c?clip=ed8a925a-af57-5c05-8a6d-514c9ac2a7aa
- **B.** *Golden Gate City*, b/w, clip 86343393, a cable car on its turntable seen from above with a boarding queue. https://www.movingimagearchive.com/sources/golden-gate-city-f9fc6af6?clip=86343393-db93-55a0-a811-b887e7724abf
- **C.** *Uruguay* (1949), b/w, clip 1ae81a8c, a plaza with a kiosk and a standing crowd. https://www.movingimagearchive.com/sources/uruguay-183e9f58?clip=1ae81a8c-ad65-5f91-ba2e-a04bbb3d58de

**Licence status, all three: not verified.** The archive cache does not carry licence fields. A is a 1941 amateur film and is probably unpublished, so its status is unclear. B and C look like government or sponsored travelogues, probably public domain, but that is unconfirmed. Each needs a PD check, or a Commons or LoC substitute, before the swarm build. Under BRIEF-2 none of them can go into `films/credits/` until that check is done.

---

## 1 · Prendre le tram (cutout collage)
- **Beat / time:** the impossible-distance jump cut, about 8–10 s. In the setup the tram is far away across the turntable. On the cut it sits in the girl's lap like a toy. The verbal play is *prendre le tram*, "to take the tram", taken literally. The anchor kept across the cut is the tram's silhouette and its roof lettering. Here it is the vehicle itself that gets reread, from vehicle to toy. The ticket prop is kept for directions 2–3.
- **Material:** girl in the orange costume from A, t≈4.4 s. The background is A, t≈0.4 s: the parade street with palm and façades, defocused. The cable car comes from B, t≈1.2 s, foraged with nothing redrawn.
- **Technique:**
  - **#1 Comic Cutout Metamorphosis (Gilliam).** The tram is a scissor cut: a hand-placed polygon with a straight cut edge on the left, where the source frame cuts it off.
  - **#29 GrabCut.** The girl's outline is a hand polygon refined by GrabCut in a 5 px band.
  - **#44 Multiplane parallax.** In the film the background drifts 0.3x and the girl 1x, and the tram has its own small bounce.
  - **#45 Occlusion.** The tram is in front of the girl, with a real drop shadow.
  - **#41 Secondary dynamics.** The tram rocks on her knees after the cut.
  - Motion: 4 s of the straight chase on B, a hard cut to this plate, then a 1 s hold for the laugh. The b/w tram against the colour plate is the declared exception.
- **Risk:** the source is 320x240, scaled up 3.9x, so the girl is soft. That softness suits the reference's defocus, but the face lacks detail. The mask edges still step slightly. The tram is b/w in a colour frame. That works as collage, but it is not the reference palette. The girl is smiling, not laughing.

## 2 · La queue fait mur (straight archive match cut)
- **Beat / time:** the queue-to-obstacle match cut at 12.40 / 12.44 s. The verbal play is *faire la queue*: the queue is what you join to reach the vehicle, and after the cut it is what blocks you. The keyframe shows both sides of the hinge. On the left (OUT) is the boarding queue at the cable car (B, t≈4.3 s). On the right (IN) is the standing crowd at the kiosk (C). The match anchor is the line of feet at the same height, marked by the orange ticks at the frame edges. In the film this is a hard cut in time, not a split.
- **Material:** B and C, cut but untouched: no grade and no cutouts.
- **Technique:**
  - **#27 Declarative compiler (Remotion-style EDL).** The cut time is a fixture and the anchor height is asserted.
  - **#43 Collage graph rewriting.** The node "queue" keeps its identity while its role changes from access to obstacle.
  - The negative control removes the anchor by shifting C 120 px. With that, the cut should read as an ordinary location change.
  - Motion: only real footage, cut on frames. Sound is a single bell held over the cut.
- **Risk:** this frame is the furthest from the reference. It is black and white, wide, and has no protagonist in it. The joke depends on timing, and a still frame reads as a split screen. The labels and ticks are proposal annotation and do not appear in the film. Both clips need licence checks.

## 3 · Le ticket troué (handmade prop over a foraged plate)
- **Beat / time:** the prop's second reading, about 14–16 s, after the queue blocks her. The métro ticket has been useless since the strike ("Grève : se présenter à l'autobus"). Its punch hole becomes a spyglass, and through it the escaping tram is sighted. The third reading, in the recovery at 18–20 s, is the ticket torn into confetti thrown on the parade, which links to plate A.
- **Material:** the ticket is **handmade**. Its card stock, typeset face, invented serial "N° 06001960", the strike notice, Queneau's *Doukipudonktan ?*, and a real punched hole in its alpha were all made for this work. It has no real operator's branding. The background is A, t≈2.6 s, heavily defocused, with the warm orange of the costumes coming through. Through the hole is B, the tram, sharp and small.
- **Technique:**
  - **#45 Occlusion compositing.** The hole is an actual matte, and the vehicle layer is clipped to it.
  - **#44 Multiplane.** In the film, the ticket is held still (1x), the street behind slides, and the tram drifts inside the hole until it leaves the circle.
  - **#43 Identity change.** The same ticket node is read as ticket, then lens, then confetti.
  - **#40 Physical tabletop** is optional: print and shoot the real ticket if a camera pass is available.
- **Risk:** the ticket can look like flat graphics. It needs paper bend, an edge highlight and a hand holding it to feel physical. The hole is small at 4:3, so the tram must stay readable inside it. It shows no child's face, which is the reference's main subject.

---

## Recommendation
Build **1 · Prendre le tram** as the film's spine and its defining image. It is the only direction that has a child protagonist and the reference's warm Eastmancolor palette and soft city, and it makes the impossible-distance jump cut readable in one frame.

Use **3 · Le ticket troué** as the prop line that runs through all three locations. It gives the gag its consequence after the queue blocks her, and its third reading, confetti, lands on the same parade plate as direction 1.

Use **2 · La queue fait mur** as a cut, not as a look: it is the 12.4 s match cut in the assembly, with its anchor and negative-control fixtures.

**Before the swarm build:** verify PD status for clips A, B and C, or replace them. Forage a colour vehicle if one exists. Make a cleaner, higher-resolution girl plate.
