# Quatre-vingt-quinze: director's plan (revision r0)

Direction: **1 · Ombres en croix** (proposals/kf-1.png), chosen by the user. The figures are black cut-paper articulated silhouette puppets: the visitor, and the man in the peaked cap. They have hand-drawn replacement heads and hands. They play on Lécroart's white and salmon 3×3 grid, with red barbed crossing marks and a title whose alternate glyphs are turned over. The direction's fold-ins from direction 2 are kept:
- the CC0 brass-key cutout;
- the FSA Union Station waiting-room plate, stencilled into two or three cells.

The test shot is also kept: the DOWN route entering the central cell E from B ("C'EST POUR MOI ?", with the bell and the key) at **44.5 s**.

**The common seed (section 10) is used.** A visitor, a sealed envelope, a bell, a brass key, a bench; the service door stays closed.

**One deliberate change to the proposal's cell table, and why.** In proposals.md the key first appears in C, but E shows the visitor holding it. The down route is A D G B E H C F I, so it would show the key in her hand (E) two cells *before* the envelope is opened (C). The down reader would lose direction exactly at the beat. Section 4 says "solve the path constraints before drawing." The key reveal must sit in a cell that comes before E in **both** orders. Only A, B and D qualify (positions 1/1, 2/4 and 4/2). So the key reveal moves to **D**, and the knock at the door moves to **C**.

This also improves the centre:
- **Across**, E follows D, and D *is* the key. "C'EST POUR MOI ?" therefore means *is this key meant for me?*
- **Down**, E follows B, the bell. The same line means *was that bell rung for me?*

The direction, the cast, the grid, the lettering of E, and the beat at 44.5 s are all unchanged.

---

## 1 · Creative thesis

**What the work proves.** One drawn panel, E, holds the same woman lifting the same key and saying the same words. It answers two different questions, depending on which neighbour the reader came from.
- **Across**, the page is a *lost-key story*. A key arrives in an envelope that is not hers, she leaves it, and it goes home under the service door.
- **Down**, the same nine cells are a *set-up*. The man behind the door watched her open the envelope and pulled the cord that rang the bell. Her question at the centre was an answer to his signal.

The second reading discloses what the first leaves latent:
- the shadow in D's window;
- the red cord;
- the fact that "IL" in G was there all along.

**What would make it bland:**
- the two routes feel synonymous (the same story told in a different order);
- E is quietly redrawn or re-lettered for one route;
- the down route is a "dossier" of threads instead of a story;
- the figures read as clip-art vector shapes;
- the film is a slideshow that pans over a still page;
- the lettering is a typeface;
- the axis change is announced by a caption instead of being *seen* in the marks and the camera.

### Defining beat and comparison baseline

- **Defining beat: 44.0–47.0 s, the down route, B → E** (the decisive frame is **44.5 s**).
  - At 41–44 s the bell in B swings and rings. The camera then travels *down* across the B/E gutter (44.0–44.5), past the red cut-paper arrow and the crossing marks, whose long arms now stand vertical.
  - It settles on E. The visitor is still lifting the key, and her replacement head is turning up toward the top of the panel, where the bell is (the bell is directly above E on the page).
  - The bell's ring is still audibly decaying under "C'EST POUR MOI ?".
- **What the viewer should be able to point to:** "It's the same woman with the same key, saying the same thing as before. But this time the bell has just rung, and she's asking whether it rang for her. At 15 s she was asking about the key."
- **Comparison baseline:** the same nine cells read **across only** (the 3–30 s half of the film on its own). There, E is merely "is this key for me?" The beat succeeds only if the down entry into E is perceptibly different in meaning while E's pixels are identical.

## 2 · Lineage Genome (compact)

| field | value |
|---|---|
| Source | Étienne Lécroart, crossed strip "Quatre-vingt-quinze" (Oubapo; reproduced by Paltani-Sargologos, fig. 23). The reference is a printed comic page, 4×5 panels, read across and down. Uncertain: the exact first publication venue and date (likely an Oubapo/L'Association *Oupus* volume, 1990s). Not verified here. |
| Target | (a) A printed 3×3 page, `assets/pages/quatre-vingt-quinze.png`. (b) A ~64 s film that *performs* both readings over the identical page art. |
| Preserved relation | One immutable cell per coordinate. Two traversals: row-major and column-major. Meaning comes from the predecessor, not from the cell. A shared terminal cell. |
| Optics change | On the page, the reader chooses the order. The film enforces each order with a camera that travels cell to cell, enters each cell from its predecessor's side, and shows the gutter it crosses. |
| Formalism change | 4×5 becomes 3×3. The cell registry (row, column, art, text, props, outgoing cues) is explicit, and the section 7 fixture is executable. |
| Concept change | Lécroart's comedy of misread intentions becomes the station seed: a key and a summons. The centre E sits on the transpose's diagonal, so it is a fixed point of position (5th in both routes) with different predecessors. |
| Sound change | The page is silent. In the film, each cell has *one* fixed sound cue, identical in both routes. The previous cell's tail decays into the next cell. The only per-route difference is therefore inherited context: the bell's tail reaches E only on the down route. |

Formation epochs (weights 0–100):

| epoch | weight | reason |
|---|---|---|
| Oubapo, 1992 →, crossed and multi-read strips | 100 | The work's direct constraint and page grammar. |
| Franco-Belgian gag page: white/salmon panels, hand-lettered capitals, big-nose profiles | 80 | The aesthetic target (extract-003). |
| Reiniger silhouette cinema, 1920s | 60 | The puppet medium. Lécroart already uses solid black shadow figures. |
| Oulipo combinatorics (Queneau, *Cent mille milliards de poèmes*, 1961) | 50 | The ancestor of the constraint: one vocabulary, many readings. |
| Sutherland, Sketchpad, 1963: constraint solving | 35 | The method for shared cells under two neighbour contracts (SCION 8, a source anchor). |
| FSA/OWI documentary photography, 1943 | 25 | The stencilled station plates. Material only. |
| Motion comics and animatics, 2000s | 15 | The film walks a page. Kept minimal to avoid the "motion comic" cliché. |

## 3 · Olog and the theory of the central operation

**Types (boxes):**
- ◻Cell = {id ∈ A..I, row, col, art (exposure sheet ending on the canonical page drawing), text (immutable lettering), props, cue (one sound cue), outgoing cues (edge marks, cords, looks)}
- ◻ReadingPath = an ordered list of Cell ids with allowed neighbour edges:
  - across: (r,c) → (r,c+1), and (r,2) → (r+1,0);
  - down: (r,c) → (r+1,c), and (2,c) → (0,c+1).
- ◻Occurrence = (path, index); it is *an occurrence of* exactly one Cell.
- ◻NarrativeContext = a path-local precondition and effect at each Occurrence.

**Arrows (aspects):**
- Occurrence —is of→ Cell
- Occurrence —has predecessor→ Occurrence (partial: the first occurrence has none)
- Cell —has→ Text
- Cell —shows→ Prop
- Occurrence —has→ NarrativeContext
- ReadingPath —ends at→ Cell. Both paths end at I.

**Facts (commuting paths):**
- For any two occurrences of the same Cell, Text and art are equal: o1.cell = o2.cell ⇒ text and art are equal.
- across.last = down.last = I.
- across.first = down.first = A.
- pos(E) = 5 in both paths.

### Central operation: `read(E | p)`, the meaning of E on path p

**Typed preconditions:**
- E.text = "C'EST POUR MOI ?"; E.art = the 12-drawing lift ending on the page pose. Both are the same object on both paths.
- pred_across(E) = D. D establishes Prop *key* (just out of the envelope). The context contains: key revealed, no addressee, she knocked and no one answered (C), and the bell rang earlier (B, three cells back, not adjacent).
- pred_down(E) = B. B establishes Event *bell rings*. The context contains: she arrived (A), she found the key (D), the man behind the door pulled the cord (G), and the bell rang (B, adjacent). The bell tail is still sounding.
- E's art must license both: the key is in her raised hand **and** her head is turning *up*, toward the bell's side of the panel.

**Observable consequences:**
- Across: a reader paraphrases E as "is this key meant for me?". F's "TANT PIS." then reads as giving the key up.
- Down: a reader paraphrases E as "was the bell rung for me? Am I being called?". H's "PLUS PERSONNE." then reads as "no one is at the window any more", C's knock as answering the call, and F's "TANT PIS." as giving up on the summons.
- Both readers end on I. The key is drawn under the closed door, and "MERCI." comes from behind it. Across, this is the owner taking his key back. Down, it is the man thanking her for having played her part.

**Counterexamples (the operation fails):**
1. **The proposal's original table** (key revealed in C). The down route shows the key in her hand at E before the envelope is opened at C. Down coherence breaks at the beat. This is why the reveal moved to D.
2. **A route-specific line.** If E said "QUI SONNE ?", it would resolve only the bell. Across, D→E would be a non sequitur.
3. **A per-route rewrite.** Adding a bell glow to E only on the down pass, or re-lettering it, makes both stories read fine, but the fixture fails: E is no longer one immutable panel.
4. **A key that isn't visible in E.** The across reading then collapses into the down one, and the routes go synonymous.

**Where replay is equivalent, and where it diverges:**
- **Identical in both routes:** every cell's art, exposure sheet (frame-for-frame), lettering and own sound cue; the page; and the first and last cells.
- **Different between the routes:**
  - the predecessor and the accumulated context;
  - the direction of camera entry (from the left on a row, from above on a column, and diagonal on the two "returns");
  - which arm of the crossing marks is long;
  - the active margin rail;
  - the inherited sound tail of the previous cell.
- **Fixed points of the transpose** (same position in both routes): A, E and I. The other six cells are permuted.

Not interactive: there is no invitation/action model. The reading order is performed, and the page is offered for free reading.

## 4 · Invariants (section 4) as applied

1. **One immutable panel and one text per coordinate.** Cells are rendered by a cell-local function of (cell id, local frame index) only, with no route argument.
   - *Measured:* every frame of E's occurrence in across (15–18 s) is pixel-identical to the corresponding frame of its occurrence in down (44–47 s), before the camera transform. The same holds for all nine cells.
   - *Measured:* a cell at rest in the film is identical to the page's cell.
2. **Each declared route visits legal cells in published order.**
   - across = A B C D E F G H I; down = A D G B E H C F I.
   - Each route covers all nine cells once, and every step is a legal neighbour edge.
3. **Each route has its own setup and resolution.**
   - Across sets up in A–C (arrival, bell, knock unanswered) and resolves in G–I (cord pulled, emptiness, key home).
   - Down sets up in A–D–G (arrival, the key observed from the window, the cord) and resolves in C–F–I (knock, give up, merci).
4. **Axis cues that survive grayscale and small size.** The red barbed crossing marks change their long arm: horizontal for across, vertical for down. A cut-paper arrow sits in the gutter being crossed. The margin rail names the route (I en travers / II en bas). The test is that the shape, not the hue, carries the cue.
5. **Concurrency.** The across story owner and the down story owner write requirements on each shared cell into the registry. A cell's art or text changes only after both adjacency contracts (its across in/out edges and its down in/out edges) pass. All cells are shared, so the registry is single-owner (unit U1) and the editor runs the contract check.

## 5 · The cell registry (canonical; the page and the film draw from this)

The grid is A B C / D E F / G H I. The lettering is hand-drawn capitals (U1's stroke alphabet), identical on the page and in the film. "Page pose" is the last drawing of each cell's exposure sheet; it is what the page prints and what the film holds when the cell is at rest.

| cell | row, col | art: page pose | animation (12 drawings/s, on 2s; same on both routes) | lettering | own sound cue | element sources |
|---|---|---|---|---|---|---|
| **A** | 0,0 | Waiting room (FSA plate, stencilled in salmon). The visitor (cloche hat, big nose) faces right, sealed cream envelope in her front hand. At right, the service door, shut, with a small lit window, empty. | A 2× walk cycle in from the left (6 drawings), stop, and a replacement head turns to the window. | CAP "GARE DE ST-ROCH, 6 H 10." · BAL "PERSONNE ?" | footsteps on stone, room tone | FORAGED plate; HANDMADE puppet, door, lettering |
| **B** | 0,1 | Close-up on the bell on its wall bracket, white ground with a salmon pool. A red pull-cord runs from the bell off the left edge. | An 8-drawing swing cycle; the clapper lags at ≈1.9× the swing angle; drawn motion arcs; the cord jerks. | SFX "DING ! DING !" (red, hand-lettered, tilted) | two bell strokes, tail ≈2.5 s | HANDMADE bell; FORAGED bell sound if usable |
| **C** | 0,2 | The visitor at the service door, fist raised against it. The door is shut. | 3 knocks (elbow FK, a 4-drawing knock); the door never moves. | SFX "TOC TOC." | three knocks on wood, then silence | HANDMADE |
| **D** | 1,0 | On the bench. The envelope is torn open and the brass key is out, with a red thread through its bow. Behind her, in the door window, the **capped man's profile** watches (dark on lit glass). | A 2-drawing tear of the envelope; the key slides out; the head is replaced by a "surprise" drawing; the man's silhouette slides into the window. | BAL "UNE CLÉ ?" | paper tear | FORAGED key cutout (CC0), FORAGED bench plate if used; HANDMADE rest |
| **E** | 1,1 | The visitor standing, the key raised at arm's length, the key glinting. Her **head is turned up and toward the panel top**, where B's bell hangs on the page. Salmon pool of light. | **A 12-pose lift** from rest to raised (shoulder→elbow→wrist FK; the key stays attached to the wrist). The head replacement goes level → up-turned between poses 5 and 8; the glint is at pose 10. | BAL "C'EST POUR MOI ?" | small key click at the top of the lift | FORAGED key; HANDMADE rig, heads, hands, lettering |
| **F** | 1,2 | The key lies on the bench, its red thread trailing off the right edge. The visitor walks away, out of the left side. | Set the key down (4 drawings), then a "shrug" head, then a walk cycle out. | BAL "TANT PIS." | key set down on wood; receding steps | FORAGED key; HANDMADE |
| **G** | 2,0 | Behind the service door: the capped man in a lit salmon interior hauls a red cord hand over hand. The cord rises out of the top-right of the panel. | Hauls hand over hand (4-drawing haul ×3); the cord's slack follows the wrist; the cap tilts. | CAP "IL TIRE LA CORDE." | rope creak, hand slaps | HANDMADE |
| **H** | 2,1 | The bench (FSA waiting-room plate, stencilled), empty: no key, no visitor. The door window above it is dark. | Only the window light goes out (2 drawings); the stillness is held. | CAP "PLUS PERSONNE." | room tone only | FORAGED plate; HANDMADE window |
| **I** | 2,2 | The service door, shut. The brass key lies at the sill, half drawn under the door, its red thread taut into the gap. The balloon tail comes from behind the door. | The key slides from the sill under the door in 6 drawings, stopping half under. **The door does not open.** | BAL "MERCI." | key scraping on stone | FORAGED key; HANDMADE |

**Both routes, read through the registry:**
- **Across (lost key):** she arrives, no one is there → a bell rings → she knocks at the service door, no answer → on the bench she opens the envelope: a key → *is this key for me?* → never mind, she leaves it and goes → someone pulls the cord → no one left, and the key is gone → the key slides home under the closed door: "MERCI." (Its owner has it back.)
- **Down (who set it up):** she arrives → she opens the envelope while the capped man watches from the window → he pulls the cord → the bell rings → *was that for me?* → the window is empty, no one → she knocks at his door → never mind, she leaves the key → he draws it in: "MERCI." (She played her part.)
- **The shared final cell is I.**
- **Secondary ambiguous cells:** G (bell cord or key thread?) and H (who has gone?). These are allowed, but E is the proof.
- **Red** is used only for the cords, the thread, the crossing marks, the SFX and the route arrow. The single red cord is the latent "it was one mechanism" that the down route discloses.

## 6 · Page layout (`assets/pages/quatre-vingt-quinze.png`)

**Overall:**
- The page is **3360 × 2400 px**, landscape, at print resolution. It prints at A4-landscape scale at about 290 dpi.
- The paper is warm white, around #fbf7f1, with real paper texture (scanned or handmade paper grain is allowed only if it is real; otherwise flat).

**Title band (y 0–260).** "quatre-vingt-quinze" is hand-lettered in bold lowercase ink, black #2b2021. **Every second glyph is turned over (rotated 180°).** The title is centred.

**Cell geometry:**
- Each cell is 900 × 600 px, and the cells are hand-ruled in ink with a border of about 7 px and slight wobble.
- Columns start at x = 240, 1230 and 2220 (gutter 90). Rows start at y = 260, 950 and 1640 (gutter 90).
- Each cell has a small id tab, A–I, in its bottom-right corner, in hand-lettered capitals in a ruled box.

**Grounds.** White cells are A-wall, B, H and F; salmon cells are D, E, G and I (pools of light #ffd7d4 → #ed9283 → #c25850). The art unit balances them as Lécroart does: alternating, never a checkerboard.

**Crossing marks.** Eight red barbed crosses #b14e3f are set at the four interior gutter intersections and at the four row-gutter ends against the margins.
- On the page they are drawn **neutral**: equal arms, each arm barbed.
- In the film they take their route state: long horizontal arms across, long vertical arms down.
- The page states both routes in its margins.

**Margins:**
- **Left margin (x 0–200):** rail "II · en bas" with A D G B E H C F I as a vertical list.
- **Right margin (x 3160–3360):** rail "I · en travers", A B C / D E F / G H I as a 3×3 list.
- **Bottom strip (y 2330–2400):** a single hand-lettered line, "LIRE EN TRAVERS (I) PUIS EN BAS (II) — MÊME FIN : I."

**Route walkthroughs (section 9)** are separate files:
- `assets/pages/quatre-vingt-quinze-across.png` and `assets/pages/quatre-vingt-quinze-down.png`;
- each is the nine canonical cells laid out in route order as one long strip (3 rows × 3), with the red arrow between them, and the incoming-edge pair labelled (for example, "D → E").

## 7 · Film: timed sequence list (1280 × 720, 24 fps, ≈64 s, ≤ 6 MB)

The camera is a virtual rostrum over the page art rendered at 3360 × 2400.
- When reading, it frames the current cell at about 62% of the frame height, so that the edge of the previous cell and the gutter between them stay in view during travel.
- Each cell gets 3.0 s:
  - 0.0–0.5 s: eased travel from the predecessor, entering from its side; the red cut-paper arrow steps into that gutter (2 drawings);
  - 0.5–2.6 s: the cell's exposure sheet plays;
  - 2.6–3.0 s: hold on the page pose.
- The paper wash lifts off each cell as it is read.
- Cells not being read hold their page pose; no other cell moves.
- Sound: each cell plays its own cue at its local 0.5 s, and the tail of the previous cue decays naturally into it. There is low room tone throughout. There is no music and no voice; captions and balloons are the voice.

| time (s) | on screen | heard |
|---|---|---|
| 0.0–3.0 | **Title.** The whole page under a paper wash. The title's alternate glyphs turn over one by one (4 drawings each). The marks are neutral. Rail I lights. | room tone fades in |
| 3–6 | **Across A.** The camera settles on A from a slight pull-in; the visitor walks in, stops and looks at the window. | steps, room |
| 6–9 | **Across B.** Travel right across the A/B gutter (the marks' horizontal arms grow long and barbed in 3 drawings at 3.0–3.5 s and stay long). The bell swings. | DING ! DING ! |
| 9–12 | **Across C.** Travel right; she knocks. | bell tail → TOC TOC TOC |
| 12–15 | **Across D.** A *return* travel, diagonal down-left, C → D; the envelope tears and the key slides out; the man's shadow appears in the window. | paper tear |
| 15–18 | **Across E.** Travel right D → E; the 12-pose lift. *(Baseline reading of E.)* | key click; **no bell tail** |
| 18–21 | **Across F.** Travel right; the key is set down and she walks off. | key on wood, receding steps |
| 21–24 | **Across G.** A return, diagonal F → G; he hauls the cord. | rope creak |
| 24–27 | **Across H.** Travel right; the window goes dark. | room tone alone |
| 27–30 | **Across I.** Travel right; the key slides under the door. | scrape, then silence |
| 30–32 | **The turn.** The camera pulls out to the whole page. Each of the eight marks turns its long arms from horizontal to vertical, drawn mark by mark (3 drawings each, left to right, top to bottom). The paper wash returns over every cell. Rail I greys; rail II · en bas lights. | eight small paper clicks, one per mark |
| 32–35 | **Down A.** Pull in to A. Same drawings, same steps. | steps |
| 35–38 | **Down D.** Travel *down* A → D; the tear and the key, with the man in the window. | paper tear |
| 38–41 | **Down G.** Travel down; he hauls the cord. | rope creak |
| 41–44 | **Down B.** A *return*, diagonal up-right, G → B; the bell swings. | DING ! DING ! |
| **44–47** | **Down E, the defining beat.** At 44.0–44.5 the camera travels down the B/E gutter, past the arrow and the vertical marks, with the bottom of B still in frame. Then the 12-pose lift, head up toward B. **44.5 s is the decisive frame.** | **the bell tail from B decays under the balloon**, then the key click |
| 47–50 | **Down H.** Travel down; the window goes dark. | room tone |
| 50–53 | **Down C.** A return, up-right, H → C; she knocks. | TOC TOC TOC |
| 53–56 | **Down F.** Travel down; the key is set down and she walks off. | key, steps |
| 56–59 | **Down I.** Travel down; the key slides under the door. | scrape |
| 59–64 | **End.** Pull out to the whole page with the marks back to neutral. Two thin red route lines draw themselves over the gutters, row by row (across) and column by column (down); both arrive in I. E's border thickens for 1 s. Hold on the page exactly as printed (the last 1.5 s equals the page PNG scaled). | silence after 61, as declared |

The beat clock is asserted in the build: t_cell(down, E) = 32 + 3·4 = 44 ≤ 44.5 < 47.

## 8 · Technique SCIONs (from swarms.json, read in full)

### 2 · Lotte Reiniger: Articulated Shadow Theater

**Why.** The direction is silhouette puppetry, and Lécroart's page already uses solid black shadow figures on salmon. Reiniger's theorem fits the proof: *action legible through contour and limited articulation*. E's double meaning must be carried by a contour, the up-turned head, not by interior detail.

**Native primitives used:**
- backlit shapes: solid #16100f–#2b2021 on the lit grounds;
- pinned joints with angle limits;
- replacement profiles: the head and hand drawings;
- contact planes: the floor line in each cell, and the bench seat;
- an exposure sheet per cell.

**Numeric invariant.** Pinned joints never separate. The distance between a child piece's pin and its parent's pin is ≤ 0.5 px in every frame of every cell. Planted feet stay on the contact line within ±1 px.

**Perceptual achievement.** With colour removed, the relations still read: who holds the key, where she looks, who pulls, which door. In E, the up-turned head reads at thumbnail size.

**Applied in:** every cell. Most decisively in E (the lift and the head turn), C (the knock), F (the walk-off) and G (the haul). D's window figure is the man as a pure shadow on the glass.

### 32 · Forward Kinematics: Hierarchical Body Logic

**Why.** The lift in E, the knock in C, the haul in G and the walk cycles must move with weight and propagate from shoulder to hand to key. The key and the envelope are attachments that must stay on the proper wrist.

**Native primitives used:**
- joint graph: pelvis → spine → neck → head, shoulder → elbow → wrist → hand → prop, hip → knee → ankle;
- local and parent transforms multiplied in order;
- bone lengths;
- pivot offsets;
- view-specific anchors: profile left and profile right.

**Numeric invariant.** Bone lengths are constant to within 0.5 px across all frames. The prop offset from the wrist joint is constant while it is held. Both are measured per joint and written to an errors-by-joint report.

**Perceptual achievement.** When the shoulder rises in E, the forearm, hand and key follow believably, with nothing floating or detaching. The haul in G has weight, with a down-stroke faster than the recovery.

**Applied in:** A (walk), C (knock), D (tear), E (lift), F (set down and walk), G (haul), and the bell pivot in B (a two-link pendulum: bell, then clapper).

### 38 · Dynamic Pose Selection: Drawing Library

**Why.** This is the direction's named fix for the clip-art risk. Heads and hands are a small library of hand-drawn replacement drawings, at most 10 per character. A decoder chooses them over each cell's action, so the figures read as *drawn*, Lécroart-like big-nose profiles, not geometric shapes.

**Native primitives used:**
- pose features: head pitch and yaw, hand state;
- illustrated candidate states:
  - visitor heads: level, look-back, surprise, up-turned, shrug, down;
  - man heads: watch, effort, tilt;
  - hands: relaxed, grasp, pinch-key, fist-knock, open, haul;
- a transition matrix;
- a DP decoder;
- minimum-duration holds.

**Numeric invariant.** No drawing is held for fewer than 2 frames (on 2s). Each cell's protected key pose is present in its decoded schedule, not averaged away:
- E: the up-turned head with the pinch-key hand at the top of the lift;
- G: the effort head;
- D: the surprise head.

The decoded schedule is exposed as JSON.

**Perceptual achievement.** The transitions don't flicker. E's head turn toward the bell is a distinct drawn change, the "surprise pose" that viewers can point to.

**Applied in:** the heads and hands of every figure in A, C, D, E, F, G; the window shadow in D.

**Also honoured, not adopted as a technique.** SCION 8, Constraint Sketchpad (a source anchor), supplies the method: the shared-cell registry, and the rule that a cell changes only when both neighbour contracts pass.

## 9 · Material: FORAGED or HANDMADE

**HANDMADE:**
- The page: the ruled borders, grounds, salmon light pools, id tabs, rails and crossing marks.
- The hand-lettered stroke alphabet (capitals, the lowercase for the title, and accents É È Ê), balloons and caption boxes, and the SFX lettering.
- The flipped title.
- The two silhouette puppets: cut pieces, joints, and the replacement head and hand drawings.
- The bell and clapper, the envelope (sealed and torn), the bench (if not taken from the plate), the service door with its window, the red cord and thread, and the paper arrow.
- Synthesized sounds where nothing foraged is suitable (kit.py Mix): knocks, a paper tear, a key click, rope creak, scrape and clicks.

**FORAGED:**
- **The brass key.** `File:Skeletonkey.png` by Blenheimears, Wikimedia Commons, **CC0**. A local copy is in `sources/quatre-vingt-quinze/skeletonkey.png`. The licence must be re-read from Commons extmetadata (back off on 429). It is cut by density with the bow hole kept open, recoloured as a flat brass (#b08a3e family) paper piece. It may be cast as black silhouette when it is in hand.
- **The waiting-room / bench plate.** Jack Delano, *Chicago, Illinois. The main waiting room of Union Station at 1 a.m.* (1943), FSA/OWI. Library of Congress item 2017843779, **public domain** (US government work; "No known restrictions"). Local copy: `films/sources/la-machine-a-tuer-le-temps/loc_2017843779.jpg`. It is copied into this work's sources and its licence re-verified on loc.gov. It is **stencilled**: a hand-chosen threshold and mask makes a two-level cut, printed as a flat salmon or deep-salmon ink layer behind the silhouettes, in A and H (and optionally D). This is a stencil print of a real photograph, not a filter.
- **Optional:** window-wall plate LoC 2017843789 (same series, PD) for G's interior.
- **Bell sound.** Moving Image Archive clip 381d177e, *Communications and Our Town* (1947), a belfry with bells. The index flags speech in that clip, so it is usable only if a bell stroke can be isolated clean of narration. Otherwise use kit `Mix.bell` (handmade) and say so.
- **Room tone and footsteps.** Search the MIA cache for clean station or hall ambience with source sound (`forage.py "station|hall|waiting|footsteps" --media clip`). Choose by listening.

Credit every item in `films/credits/quatre-vingt-quinze.json`. MIA shots use the movingimagearchive.com credit form.

**Not used:** any image from Lécroart's page or other Oubapo material; generated imagery; typefaces for lettering. FreeSans or DejaVu may appear only in the operator status view, never on the page.

## 10 · AESTHETIC TARGET

The reference is `assets/references/extract-003.webp` (Lécroart's crossed page, 684×1000), with `proposals/kf-1.png` as the keyframe to meet or beat. Colours were sampled with PIL.

- **Medium.** A printed comic page: ink-ruled panels on white paper, flat colour (one salmon-orange family plus a red spot colour), solid black figures, and hand-lettered capitals.
- **Tonal range.** High contrast. Paper white against solid black (ink-mask mean #2b2021). The salmon gives the only midtones, as smooth pools of light, not texture. The figures have no internal shading.
- **Palette (sampled):**
  - paper: #fffefe, #f8f2f2, #fefdf9;
  - salmon: pale #ffd7d4, mid #ed9283, deep #c25850; mean salmon pixel #d78c82;
  - shadow-mauve: #7e4b45, #ac8682 (edge and line fringes);
  - ink: #2e2223 / #2b2021;
  - red crossing marks: mean #b14e3f;
  - kf-1 samples: E pool #e19a84, E edge #be503e, B pool #df9680, red mark #c42a1c (too saturated; move toward the reference's #b14e3f), silhouette #16100f, paper #f7f1e7.
- **Light.** Each salmon panel has a soft radial pool, lighter at the action and darker at the panel edges, as in the reference's right-column panels. White panels are flat. Backlit silhouettes.
- **Texture.** Ink line with slight hand wobble and taper, and print-flat colour. Paper texture is allowed only if it is real. **No added grain or filter.** The FSA plates enter only as two-level stencil ink, never as a photographic halftone.
- **Framing and scale.**
  - Figures fill the panel height in profile, about 70–85%, and are cut at the knees or waist when close, as in Lécroart.
  - B is a close-up of the bell.
  - Each panel has one strong silhouette against a light field, plus one balloon or caption box.
  - Balloons are white ovals with an ink outline and a pointed tail. Caption boxes are rectangles in the upper-left corner.
- **Typography.**
  - Hand-lettered capitals, slightly irregular, with heavier strokes for emphasis. "DING ! DING !" is in red and tilted.
  - The title is bold lowercase ink lettering with alternate glyphs turned over.
  - French spacing before ! and ?.
- **Pacing.**
  - 3 s per cell; eased 0.5 s camera travel; 12 drawings/s on 2s; holds on every page pose.
  - One 2 s turn between the routes, and a 5 s end on the printed page.
  - Animation happens only where the eye is, the way a page holds still everywhere else.

## 11 · Swarm units (makers only; editor, path validator, readers, critic and reviewer are run separately)

All units work from revision **r0** of this plan. They read SCIONs 2, 32 and 38 in full, and kit.py (without editing it). Each records owner, base, read and write sets, artefact and acceptance condition in its ledger. The budget is about 45 min each, with new downloads ≤ 75 MB in total.

### U1 · story-grid-letterer

**Merged roles:** across story agent, down story agent, grid designer, letterer.

**Owns:**
- the cell registry: `grid/registry.json`, carrying for each cell id, row, col, text, props, cue, outgoing cues, and for each route its precondition and effect;
- the page scaffold;
- the hand-lettering stroke alphabet, balloons, captions and SFX;
- the flipped title;
- the crossing marks in all three states (neutral, across-long, down-long), plus the turn's per-mark drawings;
- the rails, id tabs, ruled borders, salmon light pools and the paper arrow.

It must solve both routes' contracts on every shared cell before the art is polished. It must keep E's line usable on both routes.

**Outputs:**
- `films/swarm/quatre-vingt-quinze/grid/registry.json`;
- `films/swarm/quatre-vingt-quinze/grid/page_scaffold.png` (3360×2400: everything except figures, props and plates);
- `films/swarm/quatre-vingt-quinze/grid/grid.py` (deterministic drawing functions the editor imports);
- media in `films/sources/quatre-vingt-quinze/grid/`.

### U2 · puppet-cutter-animator

**Merged roles:** puppet cutter, hinge engineer, pose illustrator, gesture animator.

**Owns:**
- the two FK silhouette rigs (SCIONs 2 and 32);
- the replacement head and hand library, at most 10 drawings per character, decoded by DP (SCION 38);
- the handmade props: bell and clapper pendulum, envelope, door and window, red cord and thread;
- the per-cell exposure sheets for A–I, ending on the page pose;
- the errors-by-joint report and the decoded pose schedules.

Cells are rendered as functions of (cell, local frame) only.

**Outputs:**
- `films/swarm/quatre-vingt-quinze/puppets/puppets.py`;
- `films/swarm/quatre-vingt-quinze/puppets/exposure.json`;
- `films/swarm/quatre-vingt-quinze/puppets/E-test.mp4` (cell E's 3 s cycle alone, at final size);
- `films/swarm/quatre-vingt-quinze/puppets/joint-errors.json`;
- media in `films/sources/quatre-vingt-quinze/puppets/`.

### U3 · forager-sound

**Merged roles:** source forager, stencil printer, sound designer.

**Owns:**
- re-verifying the licences of the key (Commons extmetadata) and the FSA plates (loc.gov);
- cutting the CC0 key (density cut, bow hole open) and the two-level stencil plates for A and H (optionally D and G);
- foraging MIA sound (bell, room tone, steps), auditioning it, and trimming it with ffmpeg;
- building each cell's single sound cue, plus the room bed;
- writing the credits entries.

**Outputs:**
- `films/swarm/quatre-vingt-quinze/forage/ledger.json`;
- `films/sources/quatre-vingt-quinze/forage/key_cut.png`;
- `films/sources/quatre-vingt-quinze/forage/stencil_A.png` and `stencil_H.png`;
- `films/sources/quatre-vingt-quinze/forage/cue_<cell>.wav` and `room.wav`;
- `films/credits/quatre-vingt-quinze.json`.

### Editor (run by the workflow)

The editor:
- builds `films/quatre-vingt-quinze.py` with kit.py, importing U1, U2 and U3;
- renders the page, the film, the walkthrough strips, the canonical cells, the adjacency test with its results, notes and the status view;
- checks pixel identity of each cell across routes and between page and film.

## 12 · The bar

The bar is frozen in `plan.json`. Changes go to `amendments.md`, for the operator only.
