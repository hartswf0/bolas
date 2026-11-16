# Assembly: la-mort-en-ce-jardin, edit-r3 (montage editor, repair round 2)

Script: `films/la-mort-en-ce-jardin.py`. It imports the unit code and does not edit it:
- U1: `world-build/compose.py`
- U2: `performance/rig.py`, `puppets.py`, and the gate-checked `trace-{L,E,baseline}.json`
- U3: the drift layer and stems listed in `interruption.json` / `sound.json`

It renders through `kit.Film(boil=0, wobble=0)`. The page uses `ink.paper(color=#1b1b1b, grain=False)` with no vignette. The picture is 800×540, pillarboxed at x=80 in 960×540, and pasted from the frame cache in `sources/la-mort-en-ce-jardin/edit/frames/`, which `--prebuild` fills with 4 processes.

Per-frame audit: `ledger.json` (`film_frames`, and `worlds.L/E/baseline` holding every trace frame).

## Evidence IDs

**Foraged** (see `films/credits/la-mort-en-ce-jardin.json`). Licences: some unit records were read from metadata saved earlier on 2026-11-16, during the Commons 429s; the independent reviewer's live batch re-check confirmed all 11 Commons items on 2026-11-16. The one item added in edit-r2 (Buttress Roots 1) was read live from extmetadata by the editor; the raw answer is in `sources/la-mort-en-ce-jardin/edit/meta/`.

| ID | material | licence |
|---|---|---|
| `Ginat_Liana…` | P0 wall, P1 liana | CC BY-SA 4.0 |
| `Huge_Buttress_roots_28115225997_jpg` | P0 trunk | CC BY 2.0 |
| `Flooded_building_and_tree_trunk…` | P1 flood trunk, water plate; edit-r3: also the fluted P1 trunk behind the hand-off in L-S5 / E-S4 | CC BY-SA 4.0 |
| `Cyathea_dregei…` | fern mass, near crown | PD |
| `Fig_Tree_Buttress_Roots…` | P1 root wall, P4 diagonal, banks | CC BY-SA 2.0 |
| `Colocasia_esculenta_leaves_jpg` | P3 leaves | CC BY-SA 4.0 |
| `Lavers_Hill…bw` | P3 fronds | CC BY-SA 4.0 |
| `Buttress_roots.JPG` | ledger-insert floor | CC BY-SA 3.0 |
| `mia_3543b210` | *Shock Troops of Disaster* 1938, ripple motion | archive formula |
| `Cardboard_546867_jpg` | card fibre | CC0 |
| `FOR-SHOE-LACMA-51.47.2` | wedding shoe | PD |
| `FOR-AUD-STREAM` | stream | CC0 |
| `FOR-AUD-JUNGLE` | Jungle Sound Thailand Phuket (Amada44), jungle bed, edit-r3 | CC BY-SA 3.0 |
| `FOR-AUD-SPLASH` | Bathtub water splashes (gradha), the last-crossing splashes, edit-r3 | PD |
| `FOR-AUD-TIDE` | Water over rocks as tide recedes (earthcalling), close lap, edit-r3 | PD |

**Handmade:**
- `HM-PUPPETS` (U2): A, B, C cards and the FK rig.
- `HM-BAG` (U2).
- `HM-PLANK` and `HM-LIANA` (U1 card plank and twisted-paper cord).
- `HM-BANKS` (U1 torn polygons).
- `HM-SHOE-CUT` and `HM-DRIFT-LAYER` (U3).
- `HM-LEDGER`, `HM-CARDS` and `HM-INSERT-HAND` (editor). These are the pencil lettering traced stroke by stroke along glyph skeletons, the strike and underline strokes, the torn card, and the writer's hand card with its pencil.
- `HM-WET` (editor, edit-r2): charcoal mud and sweat glints laid on faces and mittens.
- `HM-SPLASH` (editor, edit-r2/r3): a water sheet (cut to a torn crest, its body the channel's own foraged plate rows) rising to the knees, with card droplets, on twos.
- `HM-PLANK-SAG` (editor, edit-r3): the plank bent along an elastic point-load curve, drawn at 2.5x the trace's extra deflection, with the water's plate rows laid over the submerged card.
- `HM-SYN-*`: synthesized foley from U3's generators, re-placed by `edit-build/edit_sound.py`. Covers creak, wood/mud steps, tap, rustle, plip, pencil and liana. In edit-r3 the insect bed, lap and splash are foraged recordings, no longer synthesized.

## Timecoded sequence

| film s | shot | local | camera | on screen | evidence |
|---|---|---|---|---|---|
| 0.0–2.0 | T | | card | « La planche » / « trois · un sac · une planche » written in pencil, stroke by stroke | HM-CARDS, Cardboard; FOR-AUD-STREAM fades in, HM-SYN-PENCIL |
| 2.0–5.0 | L-S1 | 0–3 | U1 glide R→L, 60 px at P2 (parallax 0.15 / 0.35 / 1 / 1.5 / 2.0), wide m 0.955 | P0–P4 jungle, water, plank, liana; A, B (bag in her L hand), C on N bank; caption « La planche n'en porte qu'un. » | all plates, mia_3543b210, HM-PUPPETS |
| 5.0–8.0 | L-S2 | 3–6 | insert | the ledger card on the forest floor; A's hand pencils « 1 A · 2 B (sac) · 3 C » | HM-LEDGER, Buttress_roots.JPG |
| 8.0–14.5 | L-S3 | 6–12.5 | wide, static | A crosses, R hand on the liana; the plank bends at the occupant (2–9 px) and springs back | trace-L |
| 14.5–20.0 | L-S4 | 12.5–18 | push-in 8 % toward (300,380) | 14.0 local: the shoe layer k 0 enters; 17.58: tap (k 86); « Laisse-la. »; 18.4: bag B→C | FOR-SHOE, HM-DRIFT-LAYER (k = (local−14)·24) |
| 20.0–22.4 | L-S5 (D) | 18–20.4 | close: opens at M 2.4 on (128,296), with both heads in frame for the hand-off, then tilts down over 18.5–19.05 to M 2.6 on (200,352) (edit-r3: 16 px lower, the floating shoe and its heel in full against the darkened water) | 18.4 bag B→C, with C's headband in frame against the buttress flange; B kneels and reaches; her hand card over the layer (k 115–134); 19.6 grasp, shoe parented to B.R; rises | hi layer at m/3 (downscale), Flooded_building…trunk (P1), HM-WET; 21.65–22.4: the shoe alone in B's mitten, upright in profile (heel, bar strap, rosette), 18 frames |
| 22.4–23.5 | L-S6 | 20.4–21.5 | two-shot, M 2.2 centred (150,244) (edit-r3), both heads and the shoe in frame; the bag layered behind C's head; B's free arm re-keyed to an open palm | C holds the bag high, B with the shoe; « Je ne peux pas tout porter. » | |
| 23.5–25.5 | L-S6i | 21.5–23.5 | insert | the old line struck in 8 frames, then « 1 A · 2 C (sac) · 3 B » written by B's free left hand | HM-LEDGER |
| 25.5–26.0 | L-S6 | 23.5–24 | two-shot | C steps toward the plank | |
| 26.0–32.0 | L-S7 | 24–30 | wide | C crosses with liana and bag held high; water rising | |
| 32.0–38.0 | L-S8 | 30–36 | edit-r3: push-in at P2, m 0.955 → 1.38 over local 30.0–31.2, then held | B crosses last with liana and shoe; clearance down to 4.0 px at local 32.04 (film 34.04), where the paper splash rises up her shins (film frames 816–843); the plank bends under her and goes under the water at her foot (drawn sag 2+2.5×(9.0−2) ≈ 18.5 world px ≈ 25 screen px), then springs back; mud darkens on her; B walks out of frame right at 36.75; « Elle la garde. » | HM-SPLASH, HM-PLANK-SAG, FOR-AUD-SPLASH |
| 38.0–39.5 | card | | card | « Plus tôt » | HM-CARDS |
| 39.5–42.5 | E-S1 | 0–3 | = L-S1 | byte-identical to film frames 48–119 | |
| 42.5–45.5 | E-S2 | 3–6 | = L-S2 | byte-identical to film frames 120–191 | |
| 45.5–50.5 | E-S3 | 6–11.0 | wide | 7.0 local: the same layer frames (k = (local−7)·24); 10.58 tap | |
| 50.5–52.9 | E-S4 (D′) | 11.0–13.4 | = L-S5 camera as a function of time since the cut | 11.4 bag B→A, with A (hat) in frame; 12.6 grasp; the same pose sequence; shoe-layer k 96–149 hi, raster-identical to L-S5 | Buttress_Roots_1, HM-WET |
| 52.9–54.5 | E-S5 | 13.4–15 | insert | struck, then « 1 B (chaussure) · 2 A (sac) · 3 C » written by A's free left hand | |
| 54.5–69.5 | E-S6 | 15–30 | wide; edit-r3: from local 24.0 the same push-in to m 1.38 for C's crossing (B, across first, is then out of frame right) | B crosses first (low water), A with the bag, C last: 6.0 px clearance at local 26.75 (film 66.25), water sheet on C's shins (film frames 1589–1616), plank bent under the water at his foot; « C passe le dernier. » | HM-SPLASH, HM-PLANK-SAG, FOR-AUD-SPLASH |
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
- All 150 shoe-layer frames appear in both versions (`ledger.json` `shoe_layer.per_k`). Each is shown from the same file (sha256) at the same resolution, at world times exactly 7.0 s (168 frames) apart; `write_ledger()` asserts all three.
  - k 0–95 are the wide layer. L shows them in the L-S4 push-in and E in the static E-S3 wide, so the screen rasters differ by that camera move only.
  - k 96–149 are the hi layer in the identical close camera. The screen raster is byte-identical (`raster_sha256`) before a whole-pixel vertical translation `dy_screen = round(m·dy_world)`, which rides each version's own water level (about 5 px lower in E).
  - In all, 57 of the 150 screen rasters are byte-identical (k 0–2 and 96–149).
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
- **E retiming (edit-r2, a deviation from plan section 6).** The E-S3/E-S4 cut moves from 50.0 to 50.5 and the E-S4/E-S5 cut from 52.4 to 52.9. E-S5 becomes 1.6 s, with the rewrite written faster.
  - Why: E-S4 now starts at the same shoe-layer frame (k 96) and the same 0.4 s before the hand-off as L-S5. That is the only way all 150 layer frames can appear in both versions at the same resolution.
  - What stays: the film-to-local offset of E (39.5 s) and every other cut.
- **Close re-dressing (edit-r2).**
  - The heart leaf that hid the receiver is removed from the L-S5/E-S4 near dressing; a small dark fern frond sits in the top-left corner instead.
  - A buttress flange (Buttress Roots 1) is inserted as a P1 plane, in close renders only.
- **Sound (edit-r2).** `edit-build/edit_sound.py` rebuilds the stems. It executes only the function definitions of U3's `sound.py`, so the generators are unchanged. `sound.json` is the editor's record; U3's original is kept as `sound-u3.json`.
  - **Rustle:** starts 1 frame before the logged holder change (L film frame 490, E film frame 1222), about 11 dB over the bed.
  - **Splash:** on the trace's minimum-clearance frame, the same 4.0 / 6.0 px the ledger reports. It is soft-saturated and about 8 dB over the median plank step in the final mix.
  - **Tap:** at layer frame 86.
  - **Foraged since edit-r3:** the jungle bed, lap and splash now decode the Commons mp3 transcodes of the verified recordings (the original-file URLs still answered HTTP 429). `sound.json`: `jungle_source: FOR-AUD-JUNGLE`, `have` all true. Still synthesized and declared: steps, creaks, tap, rustle, plip/drips, liana and pencil.
- **Not in the final film** (spares; credit them before any use): Buttress_Roots_1 (removed in edit-r3, credits row removed), Flooded banks…raft, the Oxford shoe, *[Reno Flood]* 1927 and *Indisch allerlei* 1920.

## Repair round 2 (edit-r3): what changed and why

All changes are in the film script and `edit-build/`; U1/U2/U3 code is not edited (U1's `water()` and `plank()` are replaced at run time, declared in `ledger.json` `declared`).

| critic repair | what was done | check |
|---|---|---|
| Shoe legible | L-S5/E-S4 close ends at (200,352) so the floating shoe (hi layer, about 120 px long at M 2.6) sits whole above the frame edge against water darkened by a uniform 0.72 lighting gain on the water plate in closes. After the grasp the shoe hangs from B's mitten by its heel counter, upright in profile within 0.3 s, layered over the mitten with the thumb card re-laid over the heel; it is shown alone in the mitten for 18 frames (21.65–22.4 / 52.15–52.9) and stays in frame through L-S6 | decoded frames at 21.5 and 52.0: heel, bar strap and rosette visible (`edit-compare.jpg`, stills) |
| 22.4–23.5 rise | L-S6 reframed (150,244) M 2.2; B's free far arm re-keyed (open palm at chest height, local 20.4–21.75; no grip involved); a bag held at head height is layered behind the holder's head | C's and B's heads and the shoe in frame; shoe bottom margin > 40 px |
| Water bottom streaks | the water plate is reflect-tiled downward from the real texture instead of repeating its last row | rows 520–539 of decoded wide frames: mean vertical difference 6.5–16 (a column-repeat streak would be ~0) |
| Visible deflection and danger | elastic point-load curve; drawn extra sag 2.5× the trace's (occupant lowered with it, the same FK pose); the plate rows laid over the card where it bends below the water line; L-S8 and E-S6's last crossing pushed in to m 1.38; splash sheet rises to the knees (72 world px) with the channel's own texture, a bright crest and card droplets, about 14 frames | 2 fps sheets: the plank visibly bows into the water under the foot and straightens after |
| Foraged ambience, limiter | upload.wikimedia.org still answered 429 for the originals, but the Commons mp3 transcodes of the same files came through: Jungle Sound Thailand Phuket (CC BY-SA 3.0), Bathtub water splashes (PD), Water over rocks as tide recedes (PD), licences re-read live from extmetadata on 2026-11-16 (`sources/.../edit/meta/r3_*.json`). Mix normalised to 0.70 before kit's master | decoded peak 0.652 (max_volume −3.7 dB), zero samples ≥ 0.999; `sound.json` have.jungle = true, jungle_source FOR-AUD-JUNGLE |
| Sweat glint, face | damp darkened patch with an L 246–248 specular on brow, cheekbone and nose tip; a pencilled ear and jaw line on every head | visible at 1x in the close |
| Placard | the grey-bar ledger placard on the near bank is removed | |
| Close texture | P1 plane behind the hand-off is now the fluted Mekong trunk cut (dense bark); close depth-blur sigmas reduced (P0 0.8, P1 0.35, near 0.6, near_fg 1.1); the top-left near dressing is a shaded tree-fern crown instead of the flat dark fern | decoded hypot gradient at 21.2 s: 12.25 |
| Reviewer | shoe title = exact Commons filename; Rabich's credit leads its row in his requested order; the note names the CC0 cardboard fibre | `films/credits/la-mort-en-ce-jardin.json` |

## Render and acceptance measurements (edit-r3)

Output: `assets/films/la-mort-en-ce-jardin.mp4`, 73.0 s, 5,959,227 bytes, AAC audio: mean −28.4 dB, max −3.7 dB, decoded peak 0.652, no clipped samples.

Measured on the decoded mp4 over the 800×540 picture area.

| frame | p5/p50/p95 | \|R−B\| | gradient (abs / hypot) | below L60 | above L200 |
|---|---|---|---|---|---|
| reference (native) | 38/105/206 | 0 | 14.36 / 11.42 | 25.1 % | 6.3 % |
| 3.5 s, L-S1 wide | 43/102/199 | 0.0 | 15.53 / 12.52 | 17.2 % | 4.4 % |
| 21.2 s, L-S5 close | 43/97/199 | 0.0 | 15.32 / 12.25 | 19.0 % | 4.5 % |

Sound checks (`sound.json` checks): splash −17.2 dB RMS vs median plank step −28.9 dB (+11.7 dB); rustle −25.4 dB vs bed −33.8 dB (+8.4 dB), onset 1 frame before the logged holder change; tap at layer frame 86.

`ledger.json` (edit-r3): rig_error_max 0.0002 px; 144 byte-identical E→L frame pairs; 150/150 shoe-layer frames in both versions at +7.0 s from identical files, 57 identical screen rasters; max plank occupancy 1; orders L A,C,B (B last, 4.0 px), E B,A,C (C last, 6.0 px), baseline A,B,C (C last, 9.19 px). The shoe is on screen in 315/345 L and 239/379 E frames where B holds it: the rest are B walking out of frame right after her crossing in the pushed-in last crossings (L 36.75–38.0; E 63.7–69.5, while C crosses).

## Earlier measurements (edit-r2, superseded)


Output: `assets/films/la-mort-en-ce-jardin.mp4`, 73.0 s, 5,417,015 bytes, with audio (mean −24.2 dB, max 0.0 dB after AAC). The side-by-side sheet is `edit-compare.jpg`.

Measured over the 800×540 picture area. Gradient is given two ways: |dx|+|dy| and hypot(dx, dy).

| frame | p5/p50/p95 | \|R−B\| | gradient (abs / hypot) | below L60 | above L200 |
|---|---|---|---|---|---|
| reference (native) | 38/105/206 | 0 | 14.36 / 11.42 | 25.1 % | 6.3 % |
| 3.5 s, L-S1 wide | 42/102/199 | 0.0 | 16.40 / 13.19 | 17.1 % | 4.4 % |
| 21.2 s, L-S5 close | 41/104/200 | 0.0 | 14.07 / 11.22 | 18.4 % | 4.8 % |

`ledger.json` (edit-r2):
- **Rig:** `rig_error_max` is 0.0002 px.
- **Byte identity:** 144 E→L frame pairs are byte-identical.
- **Shoe layer:** 150/150 frames appear in both versions with identical file hashes and resolution at +7.0 s; 57 screen rasters are byte-identical.
- **Shoe in hand:** after the retrieval, the shoe is on screen in every frame where B holds it (L 345/345, E 379/379).
- **Splash:** frames are logged.
- **Plank:** maximum occupancy is 1.
- **Orders:** L A, C, B (last B, 4.0 px); E B, A, C (last C, 6.0 px); baseline A, B, C (last C, 9.2 px).
