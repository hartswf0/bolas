# Les caïds de la gaudriole: three directions

The Hard proof: a strip with two panels and one marked fold. Opened out, it shows a misunderstanding over a borrowed key. Folded, two text fragments that are already printed join up, and the hands line up to show who held the key.

All three directions use the same fold, built in `strip.py`. The sheet is 2400 x 900 px. Panel 1 runs from x 40 to 1180 and panel 2 from 1220 to 2360. There is a mountain fold at A (x 620) and a valley fold at M (x 1210, in the gutter). Folding puts sheet point B (x 1800) on A, so everything to the right of B moves left by 1180 px. The folded panel is P1[40..A] beside P2[B..2360]. The fragments are listed in `fragments.txt`. Flat and folded proofs are in `strip-open.png` and `strip-folded.png`.

| | left of the fold | right of the fold (hidden once folded) |
|---|---|---|
| P1, the miller | THE KEY? / IN MY / ALL | I SWEAR, NOT / ENVELOPE! / I CARRY IS PAPER. |
| P2, the porter | HERE! SILLY ME - / IN THE COAT / ALL (hidden once folded) | I HAD IT / POCKET / ALONG. |

- **Open strip.** The miller says "The key? I swear, not in my envelope! All I carry is paper." He is carrying a huge sack, and his hand is empty. The porter answers "Here! Silly me, I had it in the coat pocket all along," holding out the key. So the open strip makes the porter the one at fault.
- **Folded strip.** The miller now says "The key? I had it in my pocket all along." His sleeve, cut at A, meets the hand holding the key at B. The two boys' "OH? REALLY?" sits on the part that stays visible in both states, so it works with both readings.
- **No new ink.** Nothing is added when the strip folds. The hand beyond B is the same cut-out hand as the miller's own hand beyond A, so the seam registers by construction.

**Shared material (every direction):**
- **Figures:** Wilhelm Busch, *Max und Moritz* (1865). Plates 082 (the miller), 031 (the farmer, used as the porter) and 001 (the boys), from Wikimedia Commons, **Public domain** (author died 1908). Saved in `films/sources/les-caids-de-la-gaudriole/busch/`.
- **Puppet work on the figures:** they are cut out as puppets, not traced. The miller's arm is cut at the shoulder and swung 52° forward on a hinge so that it reaches the fold. The farmer's stick and hands are cut away, and one copy is mirrored for panel 1.
- **Handmade:** I drew these myself:
  - a single-stroke pen alphabet (`pen.py`, my own stroke definitions, not a font)
  - the balloons, panel borders and fold marks
  - the floor lines
  - the porter's striped forearm
  - the bit-key

---

## 1 · LE PLI SUR LA TABLE: stop-motion of the printed strip folding (animation-led)

- **Beat:** the fold itself, at about 28–34 s of a ~60 s film. The keyframe is at about 31 s. The miller's panel is coming down over panel 2, and the miller's sleeve is about to land on the hand that holds the key.
- **Material:**
  - The strip, printed on the paper scan "Vintage Paper Texture (9789792113).jpg" by James Puckett (Wikimedia Commons, **CC BY 2.0**).
  - The table is "Wood Texture Background.jpg" (Wikimedia Commons, **CC0**), shown in greyscale.
- **Technique SCIONs:**
  - #40 *Physical Tabletop Capture*, the paper performance.
  - #8 *Constraint Sketchpad*: the crease and registration coordinates are fixed constraints.
  - #45 *Occlusion Compositing*: the facets are drawn in depth order and cast contact shadows.
  - #41 *Secondary Dynamics*: the free edge lags and settles.
- **How it moves:**
  - The film runs at 12 fps "on twos". Each frame advances two crease angles: facet 2 about M (α from 0° to 180°) and facet 1 about A (β relative to facet 2).
  - Each facet is its own perspective-warped crop of the printed sheet. When facet 2 turns away from the camera, you see its back, which shows the ink faintly through the paper.
  - A small handheld jitter (about 1 px) and slight changes in lamp exposure are stepped per frame, not smoothed, so it reads as paper moved by hand between exposures.
  - Before the fold (0–25 s), the puppets act out the open strip in the same frame-by-frame way: the porter's hinged arm swings the key out, and the miller's arm shrugs.
  - After the fold (34–60 s), the paper is lifted and laid flat again twice: open reading, folded reading, open, folded.
- **Risk:**
  - The 3D facets are flat planes, not paper that bends. A real fold curls near the crease, and a fold with no bend can look like card. The fix is a short curl band at each crease; it costs time.
  - When the strip is half-folded, the seam is hidden by parallax. The beat only lands when the paper is flat, so the camera has to settle and hold on the flat fold.
- **Physical option:** this direction is the closest to a real print. The same `strip-open.png` can be printed and folded on camera at the marks.

## 2 · LA TABLE LUMINEUSE: the fold filmed from above on an animator's light box (animation-led)

- **Beat:** the reveal and its proof, at about 34–44 s. The keyframe is at about 38 s: the strip is folded and reads "THE KEY? I HAD IT IN MY POCKET ALL ALONG." The miller's hand holds the key across the seam.
- **Material:**
  - The same Busch and pen strip, on the same CC BY 2.0 paper scan.
  - A light box and peg bar, drawn by me.
- **Technique SCIONs:**
  - #8 *Constraint Sketchpad*: the mapping x → 2f−x is computed and shown.
  - #45 *Occlusion Compositing*: layers are composited by the light they let through.
  - #40 *Physical Tabletop Capture*, used as an overhead stand.
  - #41 *Secondary Dynamics*: the key keeps swinging from a finger across the fold.
- **How it moves:**
  - The camera looks straight down. Each frame computes the real stack of layers: in the folded panel, every point left of A has three layers of paper (sheet x, 2A−x mirrored, x+D).
  - Box light falls off as T to the power of the number of layers. The paper above a deeper layer blurs its ink, so the hidden ink shows up as soft onion-skin ghosts: the mirrored "...RRY IS PAPER" and the porter's shoulder. The keyframe shows this.
  - The ghosts are traceable to existing ink, so they prove the reveal was already printed. That is the Hard proof's "recoverable from explicit visible fragments", made visible.
  - Animation runs at 12 fps. From above, the fold looks like facet widths narrowing, |cos α|·(M−A) per frame. The light-box lamp is ramped up for the proof and down for the reading.
  - The key is a hinged cut-out pendulum. It swings the whole time: first from the porter's hand, then from the miller's.
- **Risk:**
  - Ghosts that are too strong spoil the punchline. In this frame they are tuned (top/back light mix 62/38) and the balloon stays clean, but the balance has to hold in every frame.
  - It is a cooler, more diagrammatic look than the reference's white page.

## 3 · PHOTO-ROMAN PLIÉ: archive hands as a two-panel photo strip (archive-led)

- **Beat:** the reference's own layout (open panel 1, open panel 2, arrow, folded panel), at about 40–50 s. In the folded third panel, the fingers on the lock knob (from panel 1) now belong to the wristwatch hand (from panel 2).
- **Material:** Moving Image Archive cache (cineosis-lab):
  - Shot 7102b861 from *Key to Our Horizons* (1952), at 9.3 s.
  - Shot af625567 from *Bookkeeping and You* (1947), at 4.0 s.
  - Both are Prelinger-derived. **Licence to verify:** the archive cache does not state one, so check each film's PD status on movingimagearchive.com before any build.
  - Balloons and lettering are by me with `pen.py`.
- **Technique SCIONs:**
  - #51 / #54 *Montage Research* and *Provenance Graph*: shot, timecode and transform are recorded.
  - #8 *Constraint Sketchpad*: the fold column is fixed at 50% of the panel width.
  - Kinetic typography for the balloon fragments.
- **How it moves:**
  - Frames are only translated and scaled uniformly for registration. Here panel 2 is shifted (−8, −14) px so that the wrist lines meet.
  - The film plays both 25 fps shots as photo-roman panels. At the fold, the right half of panel 1 and the left half of panel 2 slide under frame by frame. The letter fragments ride with their halves until the two halves meet.
- **Risk:**
  - The 320×240 sources are soft when enlarged.
  - The tone jumps visibly at the seam: the watch-hand shot is brighter.
  - There is no key in the archive hands, only a lock knob.
  - It sits furthest from the reference's ink medium.

---

## Recommendation

**Direction 1, finished with Direction 2's proof.** The folded paper object, moved frame by frame on the table, is the stage the user asked for. It keeps the comics page grammar (two panels that fold into a third) as a physical event, and the beat happens at a real crease.

The film should end on Direction 2's overhead light-box shot. It shows that the reveal was already printed: the ghosts are the hidden fragments, recoverable and mirrored. That answers the verification fixture without a caption.

Drop Direction 3, or keep two seconds of it as a coda. Its sources are low-resolution and its licences still need checking.

**Before building:**
- Add a crease curl band to KF1.
- Give the porter's pen-drawn forearm a proper Busch-style hatching pass.
- Test the seam at 100× on the printed proof.

## Gaps in SCION coverage

- **Paper engineering / fold kinematics.** `swarms.json` has no SCION for this: crease graphs, facet order, visible faces after N folds, curl at creases. #8 Sketchpad and #40 Tabletop come closest. A new SCION would serve this film, Pervenche et Victor (Lécroart's related folded strip, the second source) and any Oubapo strip that folds.
- **Light-box / onion-skin optics.** This is the traditional animator's tool used as the subject. A small SCION for translucency layering would also serve this film.
