# quatre-vingt-quinze: assembly (editor, plan r0)

Build: `films/quatre-vingt-quinze.py` (kit.Film, unedited kit). It renders the page, the 9 canonical cells, both walkthrough strips and the film from one composite, `compose(K, box)`.
- Film: 1280x720, 24 fps, 64.0 s, H.264 + AAC, 3.86 MB. Poster (webp) at 44.5 s.
- Page: 3360x2400.
- Fixture: `adjacency_test.py`, results in `adjacency-results.json`. ALL_OK = true.

## Evidence IDs
- **U1 (handmade):** `grid/grid.py` (registry.json). Covers the paper relief, painted pools, pen lettering, borders and tabs, marks, rails, title, bottom line and arrow.
  - Foraged within U1: PAPER, LoC musftpsets.200218222 p.1.
- **U2 (handmade):** `puppets/puppets.py` (exposure.json, joint-errors.json). Covers the FK rigs, the replacement heads and hands, and the props.
- **U3 (foraged):**
  - KEY: Commons File:Skeletonkey.png, CC0, delivered as `forage/key_cut.png`.
  - STENCIL_A and STENCIL_H: LoC 2017843779, Delano 1943, PD.
  - CUE_A–I: Commons sounds. The ledger is `forage/ledger.json`.
  - ROOM: handmade.
- **EDITOR (handmade, synthesized):** CLICKS, 8 kit `Mix.click` at the turn; END_LINES; E_BORDER.

## Composite (per cell, no route argument)
The layers stack in this order:
1. U1 ground(c)
2. U3 stencil_c (A, H)
3. U2 layer(c, f)
4. U1 lettering(c, tail = puppets.mouth_anchor(c); F uses U1's own tail)

Then on the page:
- paper wash (cell-local: it lifts over the occurrence's first 0.5 s, on 2s);
- U1 furniture;
- marks(u-state);
- rails(state);
- title(turn state);
- arrow(edge, k).

## Timecoded sequence
In every cell segment the cell's sheet (frames 0–71) plays, and its cue (t0 = frame 0) sounds over the inherited tail of the previous cue.

| time (s) | segment | camera / route state | evidence |
|---|---|---|---|
| 0–3 | Title | Whole page, all cells under wash. 9 flipped glyphs turn 4 drawings each (36 drawings). Marks neutral. Rails both, then rail I lit at 1.5 s. | U1 title/marks/rails, PAPER, ROOM fades in |
| 3–6 | Across A | Pull-in to A. Marks grow to across-long in 3 drawings (3.0–3.5). | U2 A, STENCIL_A, CUE_A |
| 6–9 | Across B | Travel right across the A/B gutter, arrow A>B. Bell swings. | U2 B, CUE_B (Fridingen) |
| 9–12 | Across C | Travel right. Knocks. | U2 C, CUE_C + B tail |
| 12–15 | Across D | Diagonal return C>D. Tear, key, man in the window. | U2 D, KEY, CUE_D |
| 15–18 | Across E | Travel right D>E. Lift. No bell tail (measured −240 dBFS). | U2 E, KEY, CUE_E |
| 18–21 | Across F | Travel right. Key set down, she walks off. | U2 F, KEY, CUE_F |
| 21–24 | Across G | Diagonal return F>G. Haul. | U2 G, CUE_G |
| 24–27 | Across H | Travel right. Window goes dark. | STENCIL_H, CUE_H (silence) |
| 27–30 | Across I | Travel right. Key slides under the shut door. | U2 I, KEY, CUE_I |
| 30–32 | Turn | Pull out to the page (30.0–30.5). Wash returns. Marks turn mark by mark, MARK_TURN_ORDER, 3 drawings each, with one click each. Rail II lit at 31.0. | U1 marks, CLICKS |
| 32–35 | Down A | Pull-in to A. | as above |
| 35–38 | Down D | Travel down A>D. | |
| 38–41 | Down G | Travel down D>G. | |
| 41–44 | Down B | Diagonal return G>B. Bell strikes at 42.4 and 43.6 s. | CUE_B |
| **44–47** | **Down E, the beat** | Travel down the B/E gutter (44.0–44.5), arrow B>E pointing down, vertical-long marks. **44.5 s:** settled on E, key raised, head up. The B tail under the balloon: −31 dBFS over 44–45 s, −42 dBFS over 44.5–45. | U2 E, CUE_B tail + CUE_E |
| 47–50 | Down H | Travel down. | |
| 50–53 | Down C | Diagonal return H>C. | |
| 53–56 | Down F | Travel down. | |
| 56–59 | Down I | Travel down. | |
| 59–64 | End | Pull out (59.0–59.6). Marks back to neutral (59.0–59.5). Both red route lines draw (59.5–61.5) and arrive in I. E's border thickens (61–62). Lines lift (62.0–62.25). Rails both from 59.5. The last 1.5 s is the page exactly (measured: 0 px differ). Room tone out by 61.5. | END_LINES, E_BORDER |

Beat clock asserted in the build: 32 + 3·4 = 44 ≤ 44.5 < 47.

## Measured (adjacency-results.json)
- **Routes:** both performed routes equal the declared ones (ABCDEFGHI and ADGBEHCFI). All edges are legal, each route covers all nine cells once, A is first and I is last on both. E's predecessors are D (across) and B (down); E is 5th on both.
- **Cell identity:** every frame of every cell is identical between across and down inside the ruled border (12 px inset), 72 frames × 9 cells.
  - Over the full cell box, only the gutter arrow's tip and shadow touch a few px of the ruled edge (28–92 px, at the arrow's entry drawing). That is route furniture, not cell art.
- **Rest frames:** every film rest frame equals the page PNG inside the border (0 px).
- **End hold:** every end-hold frame equals the page (0 px), and the camera frame equals the page scaled (0 px, pre-encode).
- **Sound:** one cue file per cell, on both routes.
- **FK:** joint errors are 0.0 px on every joint (U2).

## Deviations, declared
- **Sheet timing.** Sheets and cues start at the cell's frame 0 (during the 0.5 s travel), not at 0.5 s as plan §7 lists. This keeps E mid-lift at 44.5 s (defining beat) and keeps the cues synced to U2's contacts (U3 imported puppets.EVENTS). See amendments.md.
- **Readers.** readers/reader-across.md and reader-down.md (B3) are not editor products; they await the reader units.
