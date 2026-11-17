# quatre-vingt-quinze: assembly (editor, revision r1, plan r0)

Build: `films/quatre-vingt-quinze.py` (kit.Film, unedited kit). It renders the page, the 9 canonical cells, both walkthrough strips and the film from one composite, `compose(K, box)`.
- Film: 1280x720, 24 fps, 64.0 s, H.264 + AAC, 3.88 MB. Poster (webp) at 44.5 s.
- Reader cuts (B3): `readers/quatre-vingt-quinze-across-only.mp4` and `-down-only.mp4`, 35 s each. They are time-mapped master frames (`QVQ_CUT`); see readers/README.md.
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
- **EDITOR (handmade, synthesized):**
  - CLICKS: 8 kit `Mix.click` at the turn.
  - END_LINES (r1): only the edges H→I and F→I, in red pen, meeting at one dot in I.
  - E_BORDER.
- **U2, r1:** V_SKY is the commissioned skyward head (puppets.HEADS["v_sky"]). E is retimed (E_LIFT, E_HEAD, E_NECK, e_breath).
- **U3, r1:** CUE_B is rebuilt from Fridingen strikes 12 and 13. Strike 13's ring is continued by overlap-add of its own grains (make_cues.bell_extend, 7 dB/s). CUE_E's clink is ducked (soft grain, gain 0.12).

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
| 15–18 | Across E | Travel right D>E. Lift from 15.25 s. Face turned up (V_SKY) 15.5–16.67 s, past the raised key. No bell tail (measured: B cue −240 dBFS here; 1.7 kHz band −90 dBFS). | U2 E, V_SKY, KEY, CUE_E |
| 18–21 | Across F | Travel right. Key set down, she walks off. | U2 F, KEY, CUE_F |
| 21–24 | Across G | Diagonal return F>G. Haul. | U2 G, CUE_G |
| 24–27 | Across H | Travel right. Window goes dark. | STENCIL_H, CUE_H (silence) |
| 27–30 | Across I | Travel right. Key slides under the shut door. | U2 I, KEY, CUE_I |
| 30–32 | Turn | Pull out to the page (30.0–30.5). Wash returns. Marks turn mark by mark, MARK_TURN_ORDER, 3 drawings each, with one click each. Rail II lit at 31.0. | U1 marks, CLICKS |
| 32–35 | Down A | Pull-in to A. | as above |
| 35–38 | Down D | Travel down A>D. | |
| 38–41 | Down G | Travel down D>G. | |
| 41–44 | Down B | Diagonal return G>B. Bell strikes at 42.4 and 43.6 s. The ring continues past the cut. | CUE_B (Fridingen strikes 12 and 13, extended ring) |
| **44–47** | **Down E, the beat** | Travel down the B/E gutter (44.0–44.5), arrow B>E pointing down, vertical-long marks. E holds at rest during the travel, dips at 44.25, and lifts to the glint at 44.58. **44.5–45.67 s:** her face is turned up to the top of the panel (V_SKY), toward the bell just heard. She then returns to the key (V_UP) and breathes. B's ring under the balloon (measured, film soundtrack, 1.6–1.85 kHz band): −32 dBFS at 44.50–44.75, −36 at 45.00–45.25, −41 at 45.50–45.75, −45 at 46.25. | U2 E, V_SKY, KEY, CUE_B tail + CUE_E (ducked) |
| 47–50 | Down H | Travel down. | |
| 50–53 | Down C | Diagonal return H>C. | |
| 53–56 | Down F | Travel down. | |
| 56–59 | Down I | Travel down. | |
| 59–64 | End | Pull out (59.0–59.6). Marks back to neutral (59.0–59.5). The two arriving route edges draw (59.5–61.5): across H→I from the left, down F→I from above, meeting at one red dot in I. In r1 these replace the full-route tangle. E's border thickens (61–62). Lines lift (62.0–62.25). Rails both from 59.5. The last 1.5 s is the page exactly (measured: 0 px differ). Room tone out by 61.5. | END_LINES, E_BORDER |

Beat clock asserted in the build: 32 + 3·4 = 44 ≤ 44.5 < 47.

## Measured (adjacency-results.json)
- **Routes:** both performed routes equal the declared ones (ABCDEFGHI and ADGBEHCFI). All edges are legal, each route covers all nine cells once, A is first and I is last on both. E's predecessors are D (across) and B (down); E is 5th on both.
- **Cell identity:** every frame of every cell is identical between across and down inside the ruled border (12 px inset), 72 frames × 9 cells.
  - Over the full cell box, only the gutter arrow's tip and shadow touch a few px of the ruled edge (28–92 px, at the arrow's entry drawing). That is route furniture, not cell art.
- **Rest frames:** every film rest frame equals the page PNG inside the border (0 px).
- **End hold:** every end-hold frame equals the page (0 px), and the camera frame equals the page scaled (0 px, pre-encode).
- **Sound:** one cue file per cell, on both routes.
- **FK:** joint errors are 0.0 px on every joint, with 0 limit clamps (U2, rebuilt in r1).
- **Sound (r1):** `adjacency-results.json` bell_tail gives −240 dBFS for across E and −25.1 dBFS for down E over 44–45 s (B cue only, full-band, pre-encode). The film figures above are measured after encoding.
- **Library:** the visitor has 11 drawings (7 heads and 4 hands); see amendments.md.

## Hashes (r1, sha256 prefix)
| File | sha256 prefix |
|---|---|
| mp4 | 679b3dfa78ffb6eb |
| page | 422521e7b4178ab4 (pixel-identical to r0) |
| strip across | baa044b88fb93241 |
| strip down | 302cb41809c9d160 |
| across-only cut | cfc9c7715a35fe2e |
| down-only cut | 4e76a156956add07 |
| registry.json | da63198504bb685e |
| exposure.json | 6e6f88f9b74ed72a |
| films/quatre-vingt-quinze.py | 82da473ad70ee2a9 |

cells/cells.json carries revision r1 and the page sha.

## Deviations, declared
- **Sheet timing.** Sheets and cues start at the cell's frame 0 (during the 0.5 s travel), not at 0.5 s as plan §7 lists. This keeps E mid-lift at 44.5 s (defining beat) and keeps the cues synced to U2's contacts (U3 imported puppets.EVENTS). See amendments.md.
- **Readers.** readers/reader-across.md and reader-down.md (B3) are not editor products. In r1 each reader gets a single-route cut (readers/README.md), so the down-first condition can be tested. The accounts are pending; nothing here claims a reading.
- **Licence of adaptations.** cue_A, cue_B and cue_F, and so the soundtrack, adapt CC BY-SA recordings and are offered under CC BY-SA (declared in the credits and the ledger).
- **Key source.** The key is cut from a 960x720 downscale of the Commons original (declared in the credits and the ledger). exposure.json key_cut_used now names forage/key_cut.png, the file the render actually uses.
