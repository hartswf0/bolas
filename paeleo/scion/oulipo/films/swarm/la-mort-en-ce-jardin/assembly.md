# Assembly: la-mort-en-ce-jardin, edit-r1 (montage editor)

Script: `films/la-mort-en-ce-jardin.py`. It imports the unit code and does not edit it:
- U1: `world-build/compose.py`
- U2: `performance/rig.py`, `puppets.py`, and the gate-checked `trace-{L,E,baseline}.json`
- U3: the drift layer and stems listed in `interruption.json` / `sound.json`

It renders through `kit.Film(boil=0, wobble=0)`. The page uses `ink.paper(color=#1b1b1b, grain=False)` with no vignette. The picture is 800×540, pillarboxed at x=80 in 960×540, and pasted from the frame cache in `sources/la-mort-en-ce-jardin/edit/frames/`, which `--prebuild` fills with 4 processes.

Per-frame audit: `ledger.json` (`film_frames`, and `worlds.L/E/baseline` holding every trace frame).

## Evidence IDs

**Foraged** (see `films/credits/la-mort-en-ce-jardin.json`; every licence was re-read live from Commons extmetadata on 2026-11-16):

| ID | material | licence |
|---|---|---|
| `Ginat_Liana…` | P0 wall, P1 liana | CC BY-SA 4.0 |
| `Huge_Buttress_roots_28115225997_jpg` | P0 trunk | CC BY 2.0 |
| `Flooded_building_and_tree_trunk…` | P1 flood trunk, water plate | CC BY-SA 4.0 |
| `Cyathea_dregei…` | fern mass, near crown | PD |
| `Fig_Tree_Buttress_Roots…` | P1 root wall, P4 diagonal, banks | CC BY-SA 2.0 |
| `Colocasia_esculenta_leaves_jpg` | P3 leaves | CC BY-SA 4.0 |
| `Lavers_Hill…bw` | P3 fronds | CC BY-SA 4.0 |
| `Buttress_roots.JPG` | ledger-insert floor | CC BY-SA 3.0 |
| `mia_3543b210` | *Shock Troops of Disaster* 1938, ripple motion | archive formula |
| `Cardboard_546867_jpg` | card fibre | CC0 |
| `FOR-SHOE-LACMA-51.47.2` | wedding shoe | PD |
| `FOR-AUD-STREAM` | stream | CC0 |

**Handmade:**
- `HM-PUPPETS` (U2): A, B, C cards and the FK rig.
- `HM-BAG` (U2).
- `HM-PLANK` and `HM-LIANA` (U1 card plank and twisted-paper cord).
- `HM-BANKS` (U1 torn polygons).
- `HM-SHOE-CUT` and `HM-DRIFT-LAYER` (U3).
- `HM-LEDGER`, `HM-CARDS` and `HM-INSERT-HAND` (editor). These are the pencil lettering traced stroke by stroke along glyph skeletons, the strike and underline strokes, the torn card, and the writer's hand card with its pencil.
- `HM-SYN-*` (U3 synthesized foley: insects, creak, wood/mud steps, tap, rustle, lap, splash, pencil, liana).

## Timecoded sequence

| film s | shot | local | camera | on screen | evidence |
|---|---|---|---|---|---|
| 0.0–2.0 | T | | card | « La planche » / « trois · un sac · une planche » written in pencil, stroke by stroke | HM-CARDS, Cardboard; FOR-AUD-STREAM fades in, HM-SYN-PENCIL |
| 2.0–5.0 | L-S1 | 0–3 | U1 glide R→L, 60 px at P2 (parallax 0.15 / 0.35 / 1 / 1.5 / 2.0), wide m 0.955 | P0–P4 jungle, water, plank, liana; A, B (bag in her L hand), C on N bank; caption « La planche n'en porte qu'un. » | all plates, mia_3543b210, HM-PUPPETS |
| 5.0–8.0 | L-S2 | 3–6 | insert | the ledger card on the forest floor; A's hand pencils « 1 A · 2 B (sac) · 3 C » | HM-LEDGER, Buttress_roots.JPG |
| 8.0–14.5 | L-S3 | 6–12.5 | wide, static | A crosses, R hand on the liana; the plank bends at the occupant (2–9 px) and springs back | trace-L |
| 14.5–20.0 | L-S4 | 12.5–18 | push-in 8 % toward (300,380) | 14.0 local: the shoe layer k 0 enters; 17.58: tap (k 86); « Laisse-la. »; 18.4: bag B→C | FOR-SHOE, HM-DRIFT-LAYER (k = (local−14)·24) |
| 20.0–22.4 | L-S5 (D) | 18–20.4 | close at the plank foot, M 2.6 centred (200,336) | B kneels and reaches; her hand card over the layer (k 115–134); 19.6 grasp, shoe parented to B.R; rises | hi layer at m/3 (downscale) |
| 22.4–23.5 | L-S6 | 20.4–21.5 | two-shot, M 2.8 centred (110,212) | C holds the bag high, B with the shoe; « Je ne peux pas tout porter. » | |
| 23.5–25.5 | L-S6i | 21.5–23.5 | insert | the old line struck in 8 frames, then « 1 A · 2 C (sac) · 3 B » written by B's free left hand | HM-LEDGER |
| 25.5–26.0 | L-S6 | 23.5–24 | two-shot | C steps toward the plank | |
| 26.0–32.0 | L-S7 | 24–30 | wide | C crosses with liana and bag held high; water rising | |
| 32.0–38.0 | L-S8 | 30–36 | wide | B crosses last with liana and shoe; clearance down to 4 px; splash; mud darkens on her; « Elle la garde. » | |
| 38.0–39.5 | card | | card | « Plus tôt » | HM-CARDS |
| 39.5–42.5 | E-S1 | 0–3 | = L-S1 | byte-identical to film frames 48–119 | |
| 42.5–45.5 | E-S2 | 3–6 | = L-S2 | byte-identical to film frames 120–191 | |
| 45.5–50.0 | E-S3 | 6–10.5 | wide | 7.0 local: the same layer frames (k = (local−7)·24); 10.58 tap | |
| 50.0–52.4 | E-S4 (D′) | 10.5–12.9 | = L-S5 framing | 11.4 bag B→A; 12.6 grasp; the same pose sequence | |
| 52.4–54.5 | E-S5 | 12.9–15 | insert | struck, then « 1 B (chaussure) · 2 A (sac) · 3 C » written by A's free left hand | |
| 54.5–69.5 | E-S6 | 15–30 | wide | B crosses first (low water), A with the bag, C last (6 px clearance, splash); « C passe le dernier. » | |
| 69.5–73.0 | cmp | | card | « sans chaussure : 1 A · 2 B (sac) · 3 C » / « 14 s : 1 A · 2 C (sac) · 3 B » / « 7 s : 1 B · 2 A (sac) · 3 C », with each last crosser underlined in turn | |

## Claim graph (prompt section 9 deliverable)

The causal chain, one row per version:

| version | shoe enters (layer k 0) | bag hand-off | shoe grasp (k 135) | last crosser | clearance |
|---|---|---|---|---|---|
| L | 14.0 | B→C at 18.4, hands 18.4 px apart | 19.6 → B.R | B | 4 px |
| E | 7.0 | B→A at 11.4 | 12.6 → B.R | C | 6 px |
| baseline (no shoe) | none | none | none | C, with order A, B (sac), C | 9 px |

In both versions the bag leaves B before she touches the shoe, so the shoe costs a hand. B then holds the liana and the shoe, so she has no hand for the bag; every later frame shows B.R = shoe and someone else holding the bag.

**What is equivalent between L and E:**
- The 150 shoe-layer PNGs (hash list in `ledger.json` `shoe_layer.png_sha256`; the same files are pasted at a +168-frame offset).
- The retrieval pose keys.
- E-S1/S2 = L-S1/S2, checked by `sha1_rgb` on every pair in `write_ledger()`.

**What diverges:** bag carrier (C vs A), crossing order (A C B vs B A C), last crosser (B vs C), clearance (4 vs 6 px), ledger text.

**Invariants asserted on every rendered frame and on every trace frame** (`check_invariants`):
- plank occupancy ≤ 1;
- ≤ 2 grips per person, and exactly one liana hand for the occupant;
- one bag holder, and at most one shoe holder;
- holder changes only within 1 frame of a logged handoff/retrieve;
- bag bottom above the water;
- bone error < 0.5 px, both in world and in screen space;
- plate scale ≤ 1.6.

## Declared editorial decisions
- **E-S1/E-S2 come from L.** These segments show L's frames, as the plan requires byte identity. U2's E trace differs there: C sits 10 px further left and the water 2 px lower. The E world takes over at the cut into E-S3 (45.5 s), which follows the ledger insert, so C and A shift by up to 10 px across that cut.
- **Cameras.**
  - The wide framing is m 0.955 so that both banks and all three puppets fit.
  - The L-S5/E-S4 close is re-centred from U1's (205,330) M 3.0 to (200,336) M 2.6, so that B's head and the shoe at the waterline are both in frame.
  - The L-S6 two-shot is (110,212) M 2.8, and its near dressing is re-laid (the same U1 pieces) so that no frond crosses a face.
- **Who writes the ledger.** Only the hand appears in the inserts: A writes the first line, B's free hand makes the L rewrite (A has crossed), and A's free hand makes the E rewrite.
- **Sound** uses U3's stems as they stand. When this edit ran, Commons downloads were still rate-limited (HTTP 429), so the foraged jungle, cicadas, tide and splash recordings never arrived. The insect bed, lap and splash are synthesized stand-ins, declared in the notes.

## Render and acceptance measurements (edit-r1)

Output: `assets/films/la-mort-en-ce-jardin.mp4`, 73.0 s, 5.24 MB, with audio (mean −24.7 dB, max −2.7 dB). The side-by-side sheet is `edit-compare.jpg`.

Measured over the 800×540 picture area:

| frame | p5/p50/p95 | \|R−B\| | gradient | below L60 | above L200 |
|---|---|---|---|---|---|
| reference (native) | 38/105/206 | 0 | 14.4 | 25.1 % | 6.3 % |
| 3.5 s, L-S1 wide | 42/103/199 | 0.0 | 16.4 | 17.1 % | 4.4 % |
| 21.2 s, L-S5 close | 43/98/200 | 0.0 | 13.3 | 16.9 % | 4.9 % |

Acceptance condition 4 holds: p5 is within 30–45, p50 within 90–125, p95 ≥ 185, and |R−B| ≤ 2. Condition 5's gradient (≥ 10) also holds. The dark share is still below the reference.

`ledger.json` summary:
- **Bone error:** `rig_error_max` is 0.0001 px.
- **Byte identity:** 144 E→L frame pairs are byte-identical (sha1 of the RGB frame).
- **Shoe layer:** 130 shoe-layer frames appear in both versions at the same resolution, with equal file hashes.
- **Per-version outcomes:**

| version | crossing order | last crosser | bag carrier | min. clearance |
|---|---|---|---|---|
| L | A, C, B | B | C | 4.0 px |
| E | B, A, C | C | A | 6.0 px |
| baseline | A, B, C | C | B | 9.2 px |

- **Plank:** maximum occupancy is 1 in all three versions.
