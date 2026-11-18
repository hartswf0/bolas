# Les caïds de la gaudriole — director's plan

Work: `prompts/les-caids-de-la-gaudriole.md` (SCION, Folded dialogue). Lineage: Lécroart, Oubapo.
Chosen direction: **1 · Le pli sur la table** (proposals/kf-1.png). The strip folds on a table, by stop-motion. It **ends on Direction 2's light-box shot** (proposals/kf-2.png).
Story: this direction tells its own story, with the miller, the porter and the two boys. It takes from the §10 common seed the station, the **sealed envelope** (the miller: "not in my envelope"), the **bell**, the **brass key**, and the **closed service door**, which is drawn behind the porter. The seed's visitor, bench and walk-away are not used.
The bar is frozen in `plan.json`. Proposed changes go to `amendments.md`.

---

## 1 · Creative thesis

The same ink tells two stories.

- **Opened out**, the strip shows a misunderstanding over a borrowed station key. The miller swears it is not in his envelope ("all I carry is paper"). The porter, red-faced, produces the key: "Here! Silly me – I had it in the coat pocket all along." The porter is at fault.
- **Folded once** (one pleat, marked A/B), the miller's own balloon reads "THE KEY? I HAD IT IN MY POCKET ALL ALONG." His sleeve, cut at the crease, now ends in the hand that holds the key. The miller lied, and the boys' "OH? REALLY?" turns from mild surprise into an accusation.

The viewer should *feel the paper do it*. A sheet of printed paper is pushed by an unseen hand on a real table. It curls, casts a shadow, lands, and a sentence and a hand snap together at the crease. Then a light box shows the hidden layers glowing through: proof that nothing was added.

**What would make it bland:**
- A cross-fade or a sliding mask between two pictures. The "fold" would be a wipe.
- A fold that looks like rigid card: no curl at the crease, no contact shadow, no back face.
- Captions explaining the joke.
- A reveal ink-patched in the folded view, such as a key redrawn into the miller's hand.
- Ghosts in the light box that are geometrically wrong. The keyframe kf-2 shows the A..M facet's "…RRY IS PAPER" reading forwards; it must be mirrored.
- A sepia/beige look on what should be black ink on white paper.
- Puppets that only translate, never bend at a joint.

## 2 · Defining beat and comparison baseline

**Defining beat: THE FOLD, 0:26–0:38.**
1. Stop-motion at 12 exposures/s. The left part of panel 1 (P1[40..A]) rises on the mountain crease A and the gutter valley crease M.
2. The middle sheet (A..B) curls under and is hidden.
3. P1-left comes down over the table until mark ▼A sits on ▼B.
4. The paper settles. Camera and lamp hold still on the flat fold.
5. At **0:34.0** (the first flat, settled exposure), the balloon reads as one line, and the miller's cuff at A continues without a break into the hand holding the key at B.

What a viewer can point to:
- (a) The seam line, with the two halves of the balloon sentence meeting there.
- (b) The sleeve and hand joining across the seam, with the key hanging from the hand.
- (c) The fold marks ▲A/▲B coinciding in the top and bottom margins.

**Baseline to compare against.** Two things:
- Lécroart's reference (`assets/references/fold_extract-000.webp`). It is a static page: panel 1 | panel 2 → arrow → combined panel.
- The proposal keyframes kf-1 (mid-fold) and kf-2 (light box).

The film must at least match the reference's *readability* of both states, and must add what the reference cannot: the physical act of folding and the evidence of the hidden layers. kf-1 is the "card, not paper" baseline to beat (no curl band). kf-2 is the light-box baseline to beat (ghosts must be mirrored correctly; the palette must be neutral, not cream/sepia).

## 3 · Lineage Genome (compact)

- **Source medium:** a printed humour strip in a bound album (Oubapo "pliage" constraint). The reader folds the page physically. *Uncertain:* the exact edition and year of *Les caïds de la gaudriole*; it is known to us only through the CITEBD reproduction (p. 21).
- **Target media:** (1) A printable A3 page with the strip at 1:1 print scale, folding instructions and evidence. (2) A ~62 s film that performs the fold by stop-motion on a table and proves it on a light box.
- **Preserved relation:** the visible faces after one declared pleat (A mountain, M valley, B=2M−A) recombine existing fragments into a new utterance and image. Zero added ink.
- **Changes:**
  - *Optics:* overhead/oblique tabletop camera; the light box shows transmitted light through stacked paper layers.
  - *Formalism:* the fold is computed as reflections x→2f−x, composed over two creases, with a visibility mask by layer depth.
  - *Concept:* the borrowed-key misunderstanding replaces Lécroart's "pliable strip" joke. The guilt moves across the seam.
  - *Sound:* the album is silent. The film adds paper foley per exposure, a station bell for the incident, and room tone. There is near-silence at the reveal.

| Formation epoch | Weight | Reason |
|---|---|---|
| 19th-c. picture-story (Töpffer, **Busch 1865**) | 45 | Supplies the actual ink (*Max und Moritz* plates, PD) and the two-boy chorus |
| Oulipo (1960) → **Oubapo** (1987/1992) constraint comics | 100 | The defining frame: a formal constraint, applied to the strip, makes the meaning |
| Lécroart's folded strips (*Pervenche et Victor*, *Les caïds…*) | 95 | The direct model: marked fold, two panels, a third panel created |
| MAD Fold-In (Jaffee, 1964–) | 55 | Same mechanism (two edges meet to produce a new image and line). *Uncertain* as a causal influence on Lécroart; recorded as a parallel |
| Cutout and stop-motion paper animation (Reiniger 1926, tabletop practice) | 60 | How the film moves: hinged paper puppets, one exposure at a time |
| Animator's light box and onion-skin (studio practice, 1910s–) | 45 | The closing proof shot: layered translucency as evidence |
| Constraint graphics (Sutherland, *Sketchpad* 1963) | 40 | Crease, seam and registration expressed as inspectable geometric constraints |

## 4 · Olog of the system (state, operation, tests)

**Types**

- **◻Sheet**
  - `{id: "caids-strip-r1", W: 2400 u, H: 900 u, scale: 1 u = 0.1 mm (240 × 90 mm printed), faces: front (ink) / back (blank, show-through), art_raster: strip-art.png (sha256 recorded), panels: P1 = x 40..1180, P2 = x 1220..2360, y 50..850, marks: ▼▲A, ▼▲M, ▼▲B in the top and bottom margins}`
- **◻Fold**
  - `{id, axis_x, kind: mountain|valley, order, moving_portion, mask}`
  - A: x = 620, mountain, order 1.
  - M: x = 1210, valley, order 2, in the gutter.
  - The pair is **one marked pleat**: "fold so that ▼B lies on ▼A". B = 2M − A = 1800. D = B − A = 1180.
- **◻Fragment**
  - `{id, panel, speaker, layer (balloon|figure|furniture), side (L of A / A..B / R of B), bbox (x0, y0, x1, y1), text | image-part}`
  - The 12 balloon fragments are in `proposals/fragments.txt`.
  - Image fragments: `miller.sleeve` (P1, cut at A), `porter.hand+key` (P2, from B), `boys` and their balloon (P2, right of B), `porter-P1` and `WHO TOOK IT, THEN?` (A..M).
- **◻Facet**
  - `{x-range, orientation ±1, depth layer}`
  - F0 = [0, A], F1 = [A, M], F2 = [M, B], F3 = [B, W].

**Operation [fold] : Sheet × Pleat → FoldedView**

Composing the two reflections gives:

| sheet x | folded position x′ | face | depth |
|---|---|---|---|
| x ≤ A | x | up | layer 1 (top) |
| A ≤ x ≤ M | 2A − x (reflection about A) | down | layer 2 |
| M ≤ x ≤ B | 2(2A − M) − (2A − x) = x − D (reflection about A, then about the image of M) | up | layer 3 |
| x ≥ B | x − D | up | layer 3 plane, unoccluded since x′ ≥ A |

- **Visible front:** V(x′) = Sheet(x′) for x′ < A, and Sheet(x′ + D) for x′ ≥ A.
- **Folded panel width:** (A − 40) + (2360 − B) = 580 + 560 = 1140 u, the same width as a panel.
- **Light-box view:** for x′ < A, three layers stack. In order: x′ (up), mirrored 2A − x′ (down, so its ink reads reversed), and x′ + D (up).

**Typed preconditions (checked before any art is final)**

1. 0 < 2A − M (= 30). The hidden facet stays on the sheet, so no paper hangs past the left edge.
2. P1.x0 = 40 ≤ A < P1.x1 and P2.x0 < B < P2.x1, so each crease cuts through a panel.
3. Panels share a y-range, frame line y, balloon border y and floor-line y. Every ink line that crosses x = A in P1 has a partner crossing x = B in P2 at the same y within the tolerance τ (see §5).
4. Each balloon line i has an L fragment ending ≥ 12 u before A and an R fragment starting ≥ 12 u after B, with the same baseline LINE_Y[i] and the same cap height (36 u). The joined line is then spaced like a normal word gap.
5. The miller's sleeve crosses A at the same y-band and slope as the porter's forearm crosses B. Cuff width at A equals wrist width at B within τ.
6. Anything that must read in **both** states (the boys and "OH? REALLY?") lies wholly in x ≥ B + 12, or wholly in x ≤ A − 12.

**Observable consequences**
- The folded panel shows exactly
  - "THE KEY? I HAD IT / IN MY POCKET / ALL ALONG.",
  - the miller's body with a hand and a key,
  - the boys with "OH? REALLY?".
- The outer panel frame stays continuous.
- The marks ▲A and ▲B coincide.
- These disappear: "I SWEAR, NOT", "ENVELOPE!", "I CARRY IS PAPER.", "HERE! SILLY ME -", "IN THE COAT", the porter's left "ALL", "WHO TOOK IT, THEN?", and both porter figures.

**Counterexample (the operation fails if…)**
- *A single valley fold at M alone.* x → 2M − x lays P2 face-down over P1. You see blank paper backs and mirrored show-through. No new adjacency forms.
- *Moving A by +20 u while B stays.* Then B ≠ 2M − A. "THE KEY?" meets "AD IT", the balloon border steps by 20 u, and the cuff overlaps the hand.
- *Ink patching.* If the folded view needs any pixel not in V(x′), such as a key redrawn into the miller's fingers, it fails by definition (§7).

**Where replay and alternate views agree, and where they diverge**
- *They agree:*
  - the physical print folded at the marks,
  - the digital stop-motion's final flat exposure,
  - the light box with the lamp off.
  All three show the same front face V. For the digital ones it is pixel-identical; for the physical print it is within τ.
- *They diverge:*
  - Mid-fold oblique frames show parallax; the seam is unreadable until the paper is flat.
  - The light box with the lamp on adds ghosts of layers 2 and 3.
  - The back of a rising facet shows mirrored show-through.
  - A physical pleat of three paper thicknesses creeps by about 2 × 0.1 mm. That is inside τ.
  - Order of operations matters: folding M first and then A on the folded packet gives the same faces, but different layer stacking for the light box. The film uses A-first.

**Second fold on a fresh copy (§8, inquiry only).** A second pleat inside P2 at x = 1990/2100 would hide "OH? REALLY?". Record the visible faces in strip/second-fold.json. No content is added for it.

## 5 · Invariants

- **Only ink on the sheet.** Every pixel of every folded or light-box view derives from `strip-art.png` through [fold]. This is tested by pixel comparison.
- **Geometry first.** A, M, B, the print scale, LINE_Y and the panel bounds are frozen by the paper engineer in `strip/sheet.json` rev 1. Changing any of them invalidates every reveal and requires re-running all fixtures.
- **Print scale:** 1 u = 0.1 mm, so the strip is 240 × 90 mm. On the A3 page at 300 dpi, 1 u = 1.1811 px.
- **Seam tolerance τ = 5 u (0.5 mm printed)** for hand folding. Digital composition must be exact (0 u, by construction).
- **100× test.** Before the page is printed, seam crops of 40 × 40 u are enlarged and saved to `strip/seam-100x.png`. There are four of them: the balloon top border, the balloon bottom border, the floor line, and the sleeve/hand. Reading order is checked as well.
- **Hidden phrase recoverable.** Each hidden phrase is listed with its sheet bbox and its folded/ghost position.
- **Puppet poses end in print.** Any puppet that acts in the film settles into exactly the printed pose before the fold starts, and the pre-fold rest frame equals `strip-art.png` (measured). The film's page art equals the page's art.
- **Source IDs immutable:** Busch plates mm_001, mm_031 and mm_082 (Commons), paper.jpg and wood.jpg (re-verify licences), and the archive room-tone clip by its index id.

## 6 · Shot list (24 fps container; stop-motion and puppets on twos = 12 exposures/s)

Total ~62 s. Voice = the printed balloons; no added captions explain the joke. The only on-screen words besides the strip are a title card at the head and a credit card at the tail, both in the pen alphabet on the same paper.

| # | Time | On screen | Heard | Technique |
|---|---|---|---|---|
| 0 | 0:00–0:03 | Title, pen-lettered on the paper scan: "FOLDED DIALOGUE" / small "after Lécroart · Oubapo · figures W. Busch 1865" | room tone (archive) | handmade lettering |
| 1 | 0:03–0:07 | Oblique tabletop, dark wood. The printed strip is laid down by stop-motion: 4 exposures falling, 2 settling with a lifted corner. Contact shadow tightens as it lands. Marks ▼A ▼M ▼B are visible. | paper slap, room tone | #40, #45 |
| 2 | 0:07–0:15 | Camera moves (stepped per exposure) onto P1. The miller's articulated arm shrugs on its shoulder hinge, 3 swings, then settles to its printed angle (52°). Reading order: balloon lines 1→3, then the porter's "WHO TOOK IT, THEN?" with a head tilt on its neck joint. | station bell (foraged), once at 0:08; paper creak per joint move | #40 puppet transforms, #45 layer order (arm in front of sack) |
| 3 | 0:15–0:23 | Camera crosses the gutter to P2. The porter's hinged forearm swings the key out from the coat (key as a pendulum on the hand, damped) and settles to its printed pose. Balloon "HERE! SILLY ME – I HAD IT…" is read; the boys' "OH? REALLY?". | key jingle (foley), small laugh-beat of silence | #40, #45 |
| 4 | 0:23–0:26 | Pull back to the whole flat strip. Hold 1.5 s: the open state is the printed page, exactly. | room tone | — |
| 5 | **0:26–0:34** | **THE FOLD** (stop-motion, 96 exposures). P1-left lifts on mountain A, with the gutter valley M. Curl band ~40 u at each crease. The back face shows faint mirrored show-through. Contact shadows lengthen and then tighten. ~1 u handheld jitter and ±2 % lamp exposure flicker are stepped per exposure. P1-left lands over P2 until ▲A sits on ▲B; 3 exposures of settle. | one paper-crease tick per exposure (foraged paper foley, cut), soft landing thud | #40, #45, #8 |
| 6 | 0:34–0:42 | Hold flat (camera settles; no jitter for 1 s). Then a stepped push-in reads "THE KEY? I HAD IT / IN MY POCKET / ALL ALONG." left to right across the seam. Hold on the sleeve→hand→key join; the key still swings, then stops. Pan to "OH? REALLY?". | near silence (room tone only); one bell strike at 0:40 on "OH? REALLY?" | #8 seam held, #45 |
| 7 | 0:42–0:50 | Replay: the strip is unfolded (24 exposures) to the open reading, held 1 s, then refolded (24 exposures) to the folded reading. Same ink, two readings. | paper ticks, slap | #40 |
| 8 | 0:50–0:59 | Cut to straight-down on an animator's light box (handmade peg bar, frosted glass). The folded strip lies on it. The lamp switches on and ramps up over 3 s, and the hidden layers glow through. The **mirrored** "…RRY IS PAPER." / "ENVELOPE!" / "WHO TOOK IT, THEN?" / porter appear at 2A−x; "HERE! SILLY ME -" / "IN THE COAT" / porter-P2 appear unmirrored at x−D. Hold 3 s. The lamp ramps down; the clean folded reading remains. | switch click, lamp hum (foraged if available, else synthesized), room tone | #45 (transmission compositing), #8 (positions computed) |
| 9 | 0:59–1:02 | Credit card on the paper: sources + licences (short) | room tone out | — |

**What is foraged and what is handmade**

| Element | Status | What and where |
|---|---|---|
| Figures | FORAGED | Wilhelm Busch, *Max und Moritz* 1865: plates 082 (the miller), 031 (the farmer as porter), 001 (the boys). Wikimedia Commons, PD-old. Already in `sources/…/busch/`. Re-verify through extmetadata. |
| Paper | FORAGED | Paper scan "Vintage Paper Texture (9789792113).jpg" (Commons, reported CC BY 2.0, J. Puckett). Re-verify. Neutralise to white paper (grading to unify only). If the grain is too yellow to neutralise honestly, forage a white laid/wove paper scan from Commons or the LoC. |
| Table | FORAGED | Wood scan "Wood Texture Background.jpg" (Commons, reported CC0). Re-verify. Greyscale/darkened for the table. |
| Room tone | FORAGED | From the Moving Image Archive cache (first source for sound): an interior/station clip whose audio is room tone or a quiet waiting room, e.g. `forage.py "station\|waiting room\|railroad\|office"`. Choose by listening/looking; credit it. |
| Station bell | FORAGED | Commons audio (search "station bell", "hand bell", "railway bell"; PD/CC0/CC BY). Fall back to the archive cache. |
| Paper handling | FORAGED | Commons audio ("paper rustle", "paper fold", "crumpling paper"; CC0/CC BY). Cut into per-exposure ticks. |
| Lettering, balloons, frame, fold marks, scale ruler | HANDMADE | `pen.py`, a stroke alphabet, not a font. |
| Strip furniture and porter parts | HANDMADE | Pen-drawn: the porter's striped forearm, with a new Busch-style hatching pass; the bit-key; the floor lines; the closed service door behind the porter in P2 (seed). |
| Light box and peg bar | HANDMADE | Drawn and lit in code as an object; its glass is lit by transmission through paper. |
| Puppets | HANDMADE from FORAGED | Cutouts with joints: the miller's shoulder (cut, hinge 52°), the porter's elbow and wrist, the porter-P1 neck, and the key as a pendulum. |

## 7 · The page (A3 landscape, 4961 × 3508 px at 300 dpi, `assets/pages/les-caids-de-la-gaudriole.png` + `.pdf`)

All page lettering is pen-alphabet ink on the same paper scan. The strip art is the **same raster** the film uses (`strip/strip-art.png`), scaled 1.1811×.

- **Band 1 (top, ~22 %):** title "FOLDED DIALOGUE — THE BORROWED KEY". Small: "after É. Lécroart / Oubapo · figures W. Busch 1865 (PD)".
- **Band 2 (~32 %): PRINT STRIP at 100 %.** 240 × 90 mm with crop marks at the four corners.
  - Fold marks in both margins: ▼A over ▲A (mountain: dash-dot line, small "Λ" glyph), ▼M ▲M (valley: dashed, "V" glyph), ▼B ▲B.
  - A millimetre scale ruler 0–240 mm under the strip, with a "print at 100 % — the ruler must measure 240 mm" note.
  - Panel 1 holds:
    - the miller balloon "THE KEY? I SWEAR, NOT / IN MY ENVELOPE! / ALL I CARRY IS PAPER.",
    - the porter-P1 "WHO TOOK IT, THEN?" (writer may improve it to name the borrowing, e.g. "WHO BORROWED IT, THEN?", if it fits within A..M).
  - Panel 2 holds:
    - "HERE! SILLY ME – I HAD IT / IN THE COAT POCKET / ALL ALONG.",
    - the boys "OH? REALLY?",
    - the porter's hand and key just right of B,
    - the closed service door.
- **Band 3 (~28 %), the reference's layout:** [open P1 | P2] (reduced 0.5×) → pen arrow → **folded panel** at 100 % scale.
  - Beside it is a side-view cross-section of the pleat (zig-zag): layers 1/2/3 labelled, with facet ranges.
  - Beside that, the four **100× seam insets**.
- **Band 4 (bottom, ~18 %): three columns.**
  - (a) **Fragment inventory:** each fragment with id, speaker, sheet bbox and folded/ghost position.
  - (b) **Fold coordinates and tolerances:** A = 620 u (62.0 mm), M = 1210 u, B = 1800 u, D = 1180 u, τ = 0.5 mm, map x→2f−x.
  - (c) **Assembly instructions, 6 steps:**
    1. print at 100 %;
    2. cut on the crop marks;
    3. mountain-fold on A;
    4. valley-fold on M;
    5. slide until ▲B covers ▲A, top and bottom;
    6. read.
- **Reading routes, listed in Band 4 (numbers in the margin beside each balloon, in the pen alphabet):**
  - Open: ① P1 balloon line 1→3, ② "WHO TOOK IT, THEN?", ③ P2 balloon line 1→3, ④ "OH? REALLY?".
  - Folded: ① folded balloon line 1→3, ② "OH? REALLY?".

## 8 · Aesthetic target

These values come from samples taken with PIL.

**The reference** (`fold_extract-000.webp`, 800 × 353):
- Pure black-and-white line-art comic.
- Paper is white: 255; 80 % of pixels ≥ 218.
- Ink is near-black, ~(9–16, 9–16, 9–16), and covers ~11 % of the area.
- One mid grey (~98) appears only as small hatching.
- Brush-pen lettering in balloons with heavy contours.
- Tight panel framing: figures fill the lower 60 % and balloons the top 40 %.
- Layout: panel, panel, arrow, panel. Fold marks are small triangles with letters in the margins.

**kf-1** (mid-fold, the chosen keyframe):
- Paper is (224, 221, 216): neutral, slightly warm.
- Table is a dark neutral wood, (33–51, ~same, ~same); its median luminance is about 55.
- One hard key lamp from the upper left, with soft contact shadows.
- Oblique view at about 25–35°; the strip fills ~70 % of the frame width.

**kf-2** (light box):
- Back-lit paper glows (255, 246, 224) against deeper layers (201, 194, 177).
- This cream cast is a *flaw to correct toward neutral*: lamp white ≤ 8 points of R−B.

**Targets**

| | Target |
|---|---|
| **Medium** | Printed ink on real paper, handled physically. This is a black-and-white line comic; no colour except the paper's faint warmth and the wood. |
| **Tonal range** | Ink L ≤ 40. Paper (front-lit) L 215–235, with low chroma (|R−B| ≤ 15). Table L 25–70. Light-box glow L 240–252 and neutral. Ghosts at about 15–35 % ink density, never darker than the visible line art. |
| **Palette** | Ink #141414. Paper #E0DDD8. Table #2A2927 to #3D3B38. Shadow is a multiply of the table at ~0.55. Light box #F7F5F0, frame #1C1C1C. |
| **Light** | One key lamp, upper left, warm-neutral. Contact shadows are soft, offset down-right, and scale with height above the table. The light box is transmission only: the top lamp is dimmed to about 40 %. |
| **Texture** | Real paper-scan grain, with show-through on the back. The Busch engraving lines stay crisp, not blurred. No added film grain filters; the only per-frame variation is the stop-motion jitter and lamp flicker. |
| **Framing / scale** | Reading shots frame a single panel at ~90 % of frame height, as close as the reference. The fold shot shows the whole strip obliquely, as in kf-1. The light box is a straight-down shot of the folded panel at ~85 % frame height. |
| **Typography** | The pen alphabet only (`pen.py`): single stroke, uppercase, the size of comic lettering (cap 36 u). |
| **Pacing** | Stop-motion at 12 exposures/s, with holds of 1–3 s on every reading state. One defining beat, then a held flat. The proof is calm, not busy. |

## 9 · Animation technique SCIONs

1. **#40 Physical Tabletop Capture — Paper Performance Swarm.** This is a paper object performed on a table, and the whole film is that.
   - *Native primitives kept:*
     - per-piece rigid transforms: each facet is a plane with its own transform; each puppet part is a rigid cutout on a hinge;
     - a timestamped event stream: `shots/fold-events.json` lists, per exposure, α (M), β (A), camera jitter, lamp gain, and the sound tick;
     - hand exclusion: the unseen hand is implied. No hand is drawn, but the paper moves as if pushed by one: corner lead and the edge lagging behind.
   - *Numeric invariant:*
     - no wrong-ID swaps: each facet keeps its sheet region in every frame;
     - contact constraints survive replay: crease lines A and M stay on their computed 3D lines; the strip's part right of B never leaves the table (z = 0 ± 0);
     - capture/render sync: one sound tick per exposure, ±1 frame.
   - *Perceptual achievement:* it reads as real paper moved by hand between exposures. It has weight, curl, landing and settle, not a 3D card.
   - *Shots:* 1, 2, 3, 5, 7.
2. **#45 Occlusion Compositing — Who Is In Front?** The fold is entirely a question of which layer is in front.
   - *Primitives:*
     - RGBA facet layers;
     - an occlusion DAG per exposure, recomputed from facet depth: F0 in front of F1/F2 once β > 90°;
     - holdout mattes for the hinged puppet parts (arm in front of sack, key in front of coat);
     - contact shadows from facet height;
     - transmission passes for the light box (light falls off as T^n through n layers, and deeper ink blurs).
   - *Numeric invariant:* layer order is correct in every frame, with no pop at the crossing where F1 passes vertical. At the flat folded exposure, the composite equals V(x′) exactly. In the light box, the ghost positions equal 2A−x and x−D.
   - *Perceptual achievement:* the viewer always knows which part of the paper is on top, and believes the shadows.
   - *Shots:* 2, 3, 5, 6, 8.
3. **#8 Constraint Sketchpad.** The proof is geometry: creases, reflections and seam equalities are constraints, not hand placement.
   - *Primitives:*
     - a constraint graph in `strip/sheet.json`: points A, M, B; equality B = 2M − A; contact ▲A≡▲B; seam crossings: P1 line y at A = P2 line y at B;
     - a solver trace that checks each fragment's mapped position.
   - *Numeric invariant:* the residuals of all seam constraints are ≤ τ = 5 u in print and 0 u digitally; the fixture reports them.
   - *Perceptual achievement:* the fold feels inevitable. The viewer sees the sentence and the arm snap into one line with no fudge.
   - *Shots:* 5 and 6 (exact landing), 8 (ghost positions); the page's Band 3/4 shows the constraints.

Also used, without a full SCION of its own: secondary dynamics on the key pendulum and the facet edge lag, with damped settles.

## 10 · Swarm units (makers only; editor, readers, critic and reviewer are run by the workflow)

All units read `prompts/les-caids-de-la-gaudriole.md`, this plan, `plan.json` (frozen), the SCION prompts #40, #45 and #8 in `swarms.json`, `films/BRIEF-2.md` and `films/kit.py`. They start from `proposals/strip.py` and `pen.py`.

**U1 · Paper engineer + writer.** The geometry and the words are coupled, so they have one owner.
- Freeze `strip/sheet.json` rev 1: sheet, scale, A/M/B/D, panel bounds, LINE_Y, τ, the constraint list, and the fragment inventory with folded and ghost positions.
- Revise the lines only within those bounds. The borrowed key must be explicit in the open state, and both readings must stay coherent.
- Build `strip/fold.py`: a pure geometry module giving, for α and β, the 3D facet poses, layer order and visibility masks, the folded view, and the light-box layer stack.
- Build `strip/fixture.py`, which writes `strip/fixture.json`:
  - pixel equality of the folded view with V(x′);
  - seam residuals;
  - a no-orphan-ink check;
  - ghost positions;
  - 100× seam crops.
- Build the page: `assets/pages/…png` and `.pdf`, `strip/strip-flat.png`, `strip/strip-folded.png`, `strip/assembly.md`, `strip/second-fold.json`.
- Media goes in `sources/…/paper-engineer/`.
- Hands the art layer off from U2, and owns the final `strip/strip-art.png` (sha256 in sheet.json).

**U2 · Panel artist + puppet fabricator.**
- Re-cut the Busch figures as articulated cutouts with joint pivots: the miller's shoulder, the porter's elbow and wrist, the porter-P1 neck, and the key pendulum.
- Do the hatching pass on the porter's forearm, the service door, and any furniture.
- Align the meaningful image edges at A and B: the cuff and wrist must meet within τ; the frame, balloon borders and floor lines are shared.
- Output `puppets/rig.json` (parts, pivots, printed rest angle, source plate and crop), the part PNGs, and `puppets/poses.json` (per-exposure joint angles for shots 2–3, ending exactly at the rest pose).
- Output `puppets/art-layers.png`: the composed strip art, which U1 adopts as strip-art.
- Media goes in `sources/…/panel-artist/`.

**U3 · Tabletop and light-box cinematographer + sound forager.**
- Render shots 1–3, 5, 7 and 8 from strip-art, fold.py and the rig. Work frame by frame on twos.
- Facets get perspective warps, curl bands, back-face show-through, contact shadows, jitter and lamp flicker.
- The light box gets transmission compositing.
- Forage and cut the sound (room tone from the archive cache, bell, paper foley) and record credits in `shots/credits-draft.json`.
- Output `shots/shot-*.mp4` (or PNG sequences), `shots/fold-events.json`, `shots/contact-fold.jpg` (every 4th exposure), `shots/lightbox-still.png`, and `shots/sound/*.wav`.
- Media goes in `sources/…/tabletop/`.

**Dependency order:**
1. U1 freezes `sheet.json` first, within about 10 minutes.
2. U2 composes the art inside those bounds.
3. U1 verifies the art with the fixture.
4. U3 renders. It may block out the shots with the current proposals strip while waiting.

**The editor** (run by the workflow) assembles `films/les-caids-de-la-gaudriole.py` with kit.py, and writes `assets/films/…mp4`, the notes and the credits.

## 11 · Known risks

- **Curl band cost.** Fallback: a 3-strip cylindrical approximation per crease, 6 sub-facets.
- **Busch hatching vs. the pen forearm style.** Mitigation: hatch with Busch-sampled stroke widths.
- **Ghost legibility vs. the punchline.** Mitigation: tune the transmission so that, at full lamp, the visible balloon text still has ≥ 3:1 contrast over any ghost.
- **The "one marked fold" wording.** It is read as one marked pleat (A to B, with M in the gutter), like Lécroart's a/b marks. If the operator disagrees, see amendments.md.
