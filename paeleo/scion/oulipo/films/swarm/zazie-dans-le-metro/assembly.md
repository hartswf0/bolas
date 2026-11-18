# Zazie dans le métro: assembly (montage editor, round 3, repair round 2)

## Repair round 2: what changed

- **V recut (evidence V2).** The Clichy tram is recut from the full-size LoC master of P2 (2002707975, 3650 px) along its real outline: the canopy, the body, the front platform, and the undercarriage with its wheels down to the road. Road pixels between the wheels are removed. This is `editor-build/tram_recut.py`: hand polygons seed `cv2.grabCut`, and the output is `sources/.../editor/V2_tram_graded.png` plus `V2_tram.json`. The bowler-hatted man and the gas lamp standing in front of the tram in the photograph stay whole on the card; nothing is retouched. The card carries P2's own grade.
- **A3, Clichy close-up f192-239.** A nearer V2 card sits in the gap at screen right, outside the bob, from the cut frame on. It shows the tram's side: windows, the "…ST DENIS" route board, the lamp and the undercarriage. It moves 1.3x the plate drift and has a soft drop shadow. The visible area outside the puppet alpha is asserted at ≥ 8 % of the picture (measured: see ledger table). The front platform itself falls behind her head. Showing the front and still reaching 8 % would have meant blowing the card up about 2.9x, and at that size it no longer read as a tram.
- **A6, Châtelet queue f300-334.** After the match cut (f298-299 are unchanged, so the 297/298 match is untouched), each of the 14 tiles grows on twos (f300-304) into a sandwich-board person:
  - Two paper legs of staggered length (12-28 px) with shoes pointing at the tram.
  - A paper head with a nose and eye facing right, and a bowler, boater or cap.
  - Each figure leans 4-7.9° toward the tram's front platform, which stands at the head of the line (x ≈ 495). They breathe on twos while they wait.
  - At the collision (f326) the hats hop on a decaying spring (SCION #41).
  - In the 5 frames before each tile tips into the stair, its head ducks behind its board and its legs fold, so the stair is still made of the same 14 boards.
- **A6, Châtelet tram.** V2 is now at x 425 (54 % of its body in frame), scale 1.0, canopy top y 195. Its wheels stand on the road plane (y ≈ 458) over a soft contact shadow, and there are no crop edges left. It stays put; the ride is carried by S8. She climbs the tile stair onto its canopy roof.
- **Plaque.** PLACE DU CHÂTELET moved to the top left (96, 52). A check in code confirms that her body never overlaps it from f300 to f431. The arrondissement lines ("17e ARRt", "1er ARRt") are dropped from both plaques.
- **Material honesty.** Every full-figure puppet and every tile now throws a 1.5-2 px lifted-paper shadow (`lift()`).
- **Cut B.** The commuters now queue to the same front platform (x 130-442) and board there. She follows them.
- **Licence (SND1).** The credits entry for the wind now has `modified` (trimmed 0.2-1.3 s and 1.6-4.4 s, high-pass 120 Hz / band 90-1800 Hz, normalised, faded, mixed) and `film_license` "CC BY-SA 4.0". The on-screen tail (from f494) reads: « vent : « Strong winds before the Rain », SAgbley, CC BY-SA 4.0 (modifié) · film sous CC BY-SA 4.0 ». The papers line reads « domaine public / CC0 / sans restriction connue ». The note carries the same statement.
- **Housekeeping.** The stale `sound-build/_last_run.json` (which listed MIA-VALLEYTOWN) is deleted. The shipped mix is the one built at 05:25, with the tunnel synthesized.

## Repair round 1: what changed

- **A6, all 14 tiles reinterpreted twice.** The upper teeth T1-T7 (DOUK IPU) now fall out too (f282-288, gravity and rotation spring, upright by f296) onto a back row (base y 402, half a tile over). From the match cut both rows stand at Châtelet: DOUKIPU behind DONKTAN, a two-row queue. The collision bump runs down both rows, and the domino flips build a stair two tiles deep. Each back tile lands one frame after its front partner, one slot deeper (+20, -16 px). `tile_count` in frame-ledger.json is now `len(tiles)` of the drawn list. It is 14 in every frame f240-431. It is null in S8 and in the tail, where the prop is out of frame; nothing is asserted off screen.
- **A4, laugh across the whole 6.0-8.0 s window.** S3/S4 use a new exposure sheet (`s3_sheet_row`). Crescent eyes and mouth 5 begin on f144. The laugh cycle is 5-4-6-4-5-4-6-7, 4 frames per mouth, with a 4-frame shake in phase. The held pose f184-193 is removed: drawings change on twos straight through the cut. A single HairSolver is stepped through the cut, so the hair state is carried with no reset. The sound's declared silence f184-191 stays, so she laughs in silence before the cut.
- **A7, a lock across the right eye.** Fringe strands 6 and 7 are re-rested (`make_fringe_lock`) so they lie across the viewer's right eye. They remain spring strands with the same solver and the same k and zeta, at a lower wind gain.
- **A3, the tram is readable at the cut.** U2's V cutout of the Clichy tram sits at its native place in P2, on a nearer card with less defocus (blur ≤ 3.5 px at 720 against the plate's 12). The P2 position comes from a template match, ccoeff 0.70. It is in frame right from f192, not only after the rack focus.
- **Polish:** a contact shadow under the composited tram in S1/S2.
- **Match-cut honesty:** the tiles keep the ECU drawings (no feet) on f298-299, and the paper feet sprout at f300. The image measurement of the front-row tile bodies (band y 420-470) gives a baseline of 451-452 at f297 and 450-452 at f298, max Δ 1 px, spacing Δ ≤ 1 px. The back row moves 0 px.
- **Provenance.** Valley Town (1940) is no longer used. archive.org metadata lists the Prelinger item ValleyTo1940 as public domain, but the movingimagearchive clip could not be confirmed as that source (its page returns 403). The tunnel bed `trim/bed_tunnel.wav` is now synthesized: brown and pink noise through the same 40-380 Hz band and 98 Hz comb (sound-build/build_sound.py, re-run; all cue and hold checks pass, and cut B's mix is unchanged). Further fixes:
  - Credits: both Official proceedings scans now name the Railway Club of Pittsburgh as author; Kraft has a licence URL.
  - Note: "about two kilometres", and the plates dated c.1890-1900.
  - The on-screen tail credit reads « photochromes de Paris v. 1890-1900 ».
  - The note says the strike sign is a handmade prop staged on period photographs (the métro opened in 1900).


Script: `films/zazie-dans-le-metro.py` (kit `Film`, kit.py unchanged). It imports U3's rig `sources/zazie-dans-le-metro/puppet/puppet.py` and U3's approved test shot `puppet/build/test_shot.py` (S3/S4 are its exposure sheet, hair simulation and compositing, unchanged). It reads U1's `gag-route.json` (tile geometry, syllable frames, exposure-sheet mouths for S1, shot positions) and U2's plates and cutouts in `sources/zazie-dans-le-metro/forage/`. Sound is U4's gated mix (`sound/soundbed-preview.wav`, `-B.wav`), decoded with ffmpeg and added to the kit Mix.

Outputs:
- cut A `assets/films/zazie-dans-le-metro.mp4` (22.0 s)
- cut B `assets/films/zazie-dans-le-metro-control.mp4` (22.0 s, frames 0-191 identical to A)
- negative control `films/swarm/zazie-dans-le-metro/negctl.mp4` (7.0-10.0 s of A, no puppet, no plaque)
- `frame-ledger.json` (per frame, both cuts), `compare-ref.jpg`, `films/credits/zazie-dans-le-metro.json`, `films/notes/zazie-dans-le-metro.txt`

Evidence IDs: P1-P4 = LoC Photochrom plates 2001698526, 2002707975, 2001698539, 2001698544 (U2 evidence-ledger.json). V = tram cutout from P2 (U2 cutouts.json). FG = plane-tree cutout from P1. PAPER-kraft / card / book1928 / book1929 = U3 rig.json `puppet-paper`. SND1 = Commons wind (CC BY-SA 4.0). MIA-VALLEYTOWN was dropped in repair round 1. SYN = kit-synthesized (U4 `synth_items`). H = handmade.

## Timecoded sequence, cut A

| tc (s) | frames | shot | on screen | evidence |
|---|---|---|---|---|
| 0.00-2.00 | 0-47 | S1 setup, MS, L1 | Z waist-up frame left (FK: head tracks V +12°, arm to point f24-30), handmade MÉTRO/GRÈVE sign, V crosses the far plane L→R from f12. Captions « Le métro ? En grève. » f10, « …le tram, alors ! » f31. Offscreen bell f8 (left). | P1 (P1W crop), V, H (puppet, sign), SYN bell, U4 bed |
| 2.00-6.00 | 48-143 | S2 chase, MLS, L1 | Full figure, 8-drawing run cycle on twos (16 f stride), hip 80→420 px; V ahead, gap 180→320 px; camera drifts 60 px: plate 0.25x, foreground crowns 1.4x (straight crop edges off frame). Bob on a 1-D spring. | P1, V, FG, H, SYN footsteps on contacts |
| 6.00-8.00 | 144-191 | S3 laugh CU, L1 | U3 test-shot rig and compositing on the repair exposure sheet: the laugh begins on f144 (crescent eyes, mouths 5-4-6-4-5-4-6-7, shake every 4 f, cheeks up 11 px, head rock ±3.5°). The lock lies across her right eye. A gust from 6.6 s; drawings keep changing on twos up to the cut. | P1, H, PAPER-*, SND1 gust; silence 7.667-8.000 |
| **8.000** | **192** | **JUMP CUT** to S4, CU, L2 | next drawing on twos (mouth 5 → 5, one solver, centroid Δ 1.3 px); plate P1→P2; the near V2 card (tram side, windows, ST-DENIS board, wheels) fills the gap at screen right from this frame (≥ 8 % of the picture); plaque PLACE DE CLICHY pops f196; f216 eyes open on the tram, gulp; caption « … le tram ! » f222. | P2, V2, H plaque |
| 10.00-10.50 | 240-251 | S5 push-in | multiplane push: puppet plane 1→4.5x about the mouth, plate plane 1→1.6x; the paper mouth-tunnel set fades in under the push (f240-246), so the 14 teeth are in frame from 10.0 s. | P2, H |
| 10.50-12.40 | 252-297 | S5 bouche de métro, ECU | lips, gums, 6 tunnel rings, the Clichy plate as the far light; 14 tiles as teeth (DOUK · IPU above, gap between K and I; DONKTAN below). Jaw opens on twos per syllable DOU f254 KI 259 PU 264 DONK 269 TAN 275 and the syllable's tiles pop 6 px; TAN drops the jaw to the row floor (y 452); the N tilts f278; the 7 lower tiles come loose one per frame f281-287 and hop under gravity. The 7 upper tiles rattle and fall f282-288 to a back row. Rotation springs set all 14 upright by f296. Caption « Doukipudonktan ! » f258. | H, P2 (far light), SYN tunnel/clicks/clatter |
| **12.417** | **298** | **MATCH CUT** to S6, MLS, L3 | the same 14 tiles (DONKTAN front row y 452, DOUKIPU back row y 402) at place du Châtelet; the tiles stand up as sandwich-board people (legs, heads, hats, leaning at the tram's front platform) f300-304; plaque pops f300 (top left); caption « faire la queue… » f302; the V2 tram stands at frame right on its wheels, 54 % in frame. Hats hop at the collision. Z runs in f312, hits the queue f326 (squash pose), rebounds 60 px, hair flung forward, silence f328-333; the bump runs down both rows; dominos flip f335-360 (ticks on the front landings f341…359, back partners 1 f later) into a 3-column stair two tiles deep, with T14 and T7 upright on top. | P3, V2, H, SYN impact/ticks |
| 15.00-18.00 | 360-431 | S7 recovery, same setup | run to the stair f360-381; climb with the near ankle pinned on each tread (f382, 391, 400, 409; IK hip, pin error 0), deck step f414, sits on the tram's canopy roof f418; T14 kicked loose f418 and falls; bells f418/426 (the ride itself is S8). | P3, V2, H |
| 18.00-20.00 | 432-479 | S8 resolution, CU, top deck | reference framing; P3 slides R→L behind her, handmade deck railing rides with her; breeze gust then steady air on a fresh U3 HairSolver run; laugh cycle; the loose N flutters past on the near plane f450-470; caption « Zazie a pris le tram. » f442. | P3, H, SND1 breeze, SYN hooves |
| 20.00-22.00 | 480-527 | tail | cut-paper title « ZAZIE / DANS LE / MÉTRO » on dark card: D, O, I, A, T and the N are the T tiles reused (the stair N lands last, f514); Z, E, S, L, M, É, R are new title tiles (declared exception to invariant 4); credit lines. | H |

## Cut B (continuity control)

| tc (s) | frames | shot | on screen |
|---|---|---|---|
| 0.00-8.00 | 0-191 | S1-S3 | identical frames to cut A (same cached images; measured diff below) |
| 8.00-10.00 | 192-239 | S4b | ordinary cut to a reverse angle down boulevard de la Madeleine (P4); Z runs in from frame left, V far ahead |
| 10.00-12.40 | 240-297 | S5b | MCU on P4: she says the word (mouth 7-4-7-5-6 on the syllable frames), then laughs; caption « Doukipudonktan ! » |
| 12.417-18.00 | 298-431 | S6b/S7b | plain cut to L3: 7 handmade paper commuters queue at the stop, Z runs in and waits at the end, the queue shuffles, they board one by one at V2's front platform (x ≈ 495) and she follows |
| 18.00-20.00 | 432-479 | S8b | CU inside the tram (handmade varnished-card window frame, P3 through the window), laughing, still air |
| 20.00-22.00 | 480-527 | tail | same title card |

## Word-to-gag table

| word | literal | gag reading | prop | setup → payoff → consequence |
|---|---|---|---|---|
| métro en grève | the underground is on strike | the goal is blocked before the film starts; the only ride left is the tram | handmade enamel MÉTRO sign + pasted GRÈVE strip (S1) | f0-47 → she points at V (goal declared) → every later operation is measured against distance(Z, V) |
| (laugh) | — | the anchor that survives the impossible cut | the CU puppet (mouth 5, orange collar, hair springs) | S3 laugh → jump cut f192 (the city moves, she does not) → V is now mid-frame: closer |
| Doukipudonktan | d'où qu'il pue donc tant | the word is her teeth: 14 cut-paper letter tiles | T1-T14 | syllables f254-275 → TAN drops the jaw; all 14 come loose (lower f281-287, upper f282-288) → they leave her mouth as objects |
| bouche de métro | métro entrance ("métro mouth") | her open mouth is the métro entrance: tunnel rings, Clichy light at the end | lips, gums, tunnel rings (H) | push-in f240-251 → ECU f252-297 → the falling teeth carry the match cut |
| faire la queue | to queue | the queue is literally the word's letters, standing as people in line at the tram door, and it blocks her | T1-T14 in two rows, legs + heads + hats f300-334 | match cut f298 → collision f326 (setback, bounce 60 px) → domino stair → she climbs onto the impériale |

## Route and continuity exceptions

- Toward the tram is left → right in every shot (invariant 1). L1: Z enters frame left, V leaves frame right (S2). L2: same CU anchor, V native mid-right. L3: Z enters left, queue/stair centre, V2 at frame right (x 425, front platform = head of the queue); deck on its canopy at (606, 208).
- **Exception E1, AnchoredJumpCut f192** (apparent place): the city moves, the girl does not. Preconditions asserted in code (see Ledger).
- **Exception E2, TileRewrite teeth → queue f297/298** (object identity, match cut): the same 14 tiles in two rows; row y and spacing held (model and image).
- **Exception E5 (repair round 1)**: there is no held pose before the jump. The plan's 1/3 s hold before the cut survives only as sound silence (f184-191), while the picture keeps laughing on twos. The S3/S4 exposure sheet differs from gag-route frames 144-191: the laugh starts at f144, not after the breathing f144-155.
- **Exception E3, queue → steps f335-359** (route): cause is Z's collision; the flips are cartoon physics (tiles leap into stacked columns), declared.
- **Exception E4, tail title**: new title tiles for letters not in T; T itself stays 14 objects.
- Deviation from the plan: the stair is three stacked columns (1, 2, 3 lying tiles) plus T14 standing on top, not seven tiles leaning at 40°: seven tiles on one ground line cannot make a rising stair, stacking can. The V2 card in L3 is placed at x 425 at scale 1.0, so more than half the tram is in frame. Captions are 25 px Instrument Serif cream on a faint dark band.

## Timecoded gag cues (cut A)

| f | tc | cue |
|---|---|---|
| 8 | 00:00:00:08 | tram bell offscreen left (before V is seen) |
| 10 / 31 | 00:00:00:10 / 01:07 | captions: strike, then the tram |
| 12 | 00:00:00:12 | V enters the far plane, head tracks it |
| 30 | 00:00:01:06 | she points at V: goal declared |
| 48-143 | 00:00:02:00 | the chase, footsteps on contacts every 8 f, V pulls away |
| 158 | 00:00:06:14 | gust: fringe sweeps across her right eye |
| 184-191 | 00:00:07:16 | silence at full laugh (picture keeps moving on twos) |
| **192** | **00:00:08:00** | **jump cut to place de Clichy**, close bell |
| 196 | 00:00:08:04 | plaque snap |
| 216 | 00:00:09:00 | eyes open on the tram, gulp |
| 240-251 | 00:00:10:00 | push-in into the mouth, tunnel resonance |
| 254 259 264 269 275 | 00:00:10:14 … 11:11 | DOU KI PU DONK TAN: jaw + tile pops + pitched clicks |
| 278 | 00:00:11:14 | the loose N tilts |
| 281-296 | 00:00:11:17 | all 14 tiles come loose (lower f281-287, upper f282-288), clatter, land in two rows |
| **298** | **00:00:12:10** | **match cut: the teeth are the queue at Châtelet** |
| 300-304 | 00:00:12:12 | the tiles stand up as people in line (legs, heads, hats) |
| 300 / 302 | 00:00:12:12 | plaque snap / « faire la queue… » |
| 326 | 00:00:13:14 | **impact**: she hits the queue (squash), then silence f328-333 |
| 335-359 | 00:00:13:23 | domino flips, ticks rising every 3 f on the landings |
| 382 391 400 409 414 | 00:00:15:22 … 17:06 | card steps on each tread, deck step |
| 418 / 426 | 00:00:17:10 / 17:18 | bell twice, she sits on the roof, the N is kicked loose |
| 442 | 00:00:18:10 | « Zazie a pris le tram. » |
| 450-470 | 00:00:18:18 | the N flutters past |
| 480-527 | 00:00:20:00 | title card, last tile (the N) f514, final click f520 |

## Strongest checkpoint

Frames 191 → 192 (7.958 → 8.000 s): the same paper puppet in the middle of her laugh, on the next drawing on twos (mouth 5 → 5, one hair solver carried through, alpha-centroid Δ 1.3 px, collar hue Δ 0.01°). The plate swaps from the Madeleine to the place de Clichy, and her tram is now right beside her, its side filling the gap at frame right. With the negative control (`negctl.mp4`) the same swap without her is a plain location change. Second strongest: f297 → f298, where the fourteen loose teeth in two rows become the queue in the same two rows (measured image baseline Δ ≤ 1 px).

## Ledger / claim graph (measured; from frame-ledger.json)

Asserted in `films/zazie-dans-le-metro.py` (`preconditions()`), all pass; values stored under `preconditions` in `frame-ledger.json`:

| claim | evidence | measured | bar |
|---|---|---|---|
| pre1 goal shown before the jump | V on screen in S1/S2 + GRÈVE sign + captions f10-47 | V visible 132 frames before f192 | ≥ 36 |
| pre2 place changes | plate_id f191 → f192 | P1 → P2 (Madeleine → Clichy, ~2 km, map estimate, uncertain) | differ |
| pre3 anchor 191 → 192 | puppet alpha centroid, root transform, mouth, hair solver, collar hue | centroid Δ 1.32 px; scale Δ 0; mouth 5 → 5 (drawings 46 → 48); one solver, no reset; fringe tips move 40.9 px at 720 against a 34.0 px median between other drawings (≤ 1.5×); collar hue 21.24° → 21.25° | ≤ 8 px, ≤ 3 %, no reset, ≤ 4° |
| pre4 screen direction | wind vector, gaze | fringe wind 64° down-right both sides of the cut | unchanged |
| pre5 V within 24 f | ledger V.visible | native tram visible from f192 | ≤ f216 |
| match 297 → 298 | tile model row + image | model: base y 452 → 452 (all 7), spacing 64 → 64, glyphs DONKTAN → DONKTAN; back row DOUKIPU moves 0 px. Image, cream bodies in band y 420-470: baseline 451-452 → 450-452 (max Δ 1 px), spacing Δ ≤ 1 px. The feet sprout at f300, after the cut | ±6 px |
| tile count from 10 s | len(drawn tile list) per frame, f240-431 (every shot with the prop in frame) | 14 every frame; S8 and the tail are null (out of frame), except T14, which flutters past in S8 | 14 |
| A4 laugh 6.0-8.0 s | exposure sheet + frame diffs f144-191 | mouths 4, 5, 6, 7; eyes 'squeeze' on every frame; no drawing held longer than 2 frames; cheek apples rise 11.0 px (rig piece centroid, laugh 0 → 1) | ≥ 4 mouths, crescent eyes, changes ≤ 2 f, ≥ 5 px |
| A3 tram at the cut (r2) | V2 card alpha minus puppet alpha, every frame f192-239 | 10.4 % at f192, 10.4-13.5 % over the shot; side, windows, ST-DENIS board, undercarriage | ≥ 8 % from f192 |
| A6 Châtelet tram (r2) | static V2 card | 53.8 % of its width in frame; wheel line y 458 on the road (ground 460), contact shadow | ≥ 50 %, grounded |
| A6 queue reading (r2) | drawn tile list | 7/7 front-row tiles are people (legs, head, hat) on every frame f304-325; lean 4.0-6.4° toward the door at x ≈ 495 | all 7 |
| plaque clear (r2) | Z body bbox vs plaque rect (14-187, 8-96), f300-431 | 0 overlapping frames | 0 |
| A/B shared frames | pre-encode frames f0-191 | max mean abs diff 0.0; after x264 encoding 0.0 for f0-143 and up to 1.48 for f144-191 (encoder references across the different B continuation) | < 1.0 on f0-143 |
| A4 hair (S3/S4 repair solver) | frame-ledger hair_tests.S3_S4_repair1 | energy 1 s after the gust 2.5 % of peak (486 → 12.4); U3's strand lag of 3 f is unchanged (same solver and parameters) | 2-3 f, < 10 % |
| S8 hair | fresh HairSolver, gust then steady breeze | energy at end 11 % of peak (steady breeze keeps a held deflection, no gust energy left) | settles |
| S7 contact plane (#2) | IK climb, near ankle pinned on each tread | pin error ≤ 0.035 body units (≈ 0.01 px) | stable |
| A7 framing (compare-ref.jpg) | puppet alpha | head width 0.525 / 0.526 / 0.522 at 7.6 / 8.1 / 19.0 s; crown y 0.224 / 0.213 / 0.226; the fringe lock lies across the right eye in all three | 0.45-0.55; 0.18-0.30 |
| A8 tone/palette | picture region | p50 78 / 90 / 85, p95 132 / 137 / 142, > 235: 0 %; plate HSV-S 39 / 29 / 34; hair #4e3220 ΔE 5.2-5.4, skin #b56d4b-#b77756 ΔE 5.3-6.9; 12-13 hair tones | p50 75-105, p95 ≤ 175, ΔE ≤ 18, S ≤ 110, ≥ 5 tones |

Claim graph (SCION #43 entity rewrites as shown on screen):
- Z —wants→ Goal —names→ V (S1 point, f30) → AnchoredJumpCut f192 (Z anchor held; L1 → L2) → distance(Z, V) drops (V mid-frame in P2).
- T1-T14 reading=teeth (f252-280) —[cause: TAN jaw drop f275]→ T1-T14 falling (f281-295) → row (T8-T14) / row2 (T1-T7) (f296-297) —[match cut f298, row y/spacing held]→ two-row queue —[cause: Z contact f326, impact + hold]→ obstacle (Z bounces back 60 px) —[cause: bump wave, domino flips f335-359]→ steps —supports→ Z (f382-414) —boards→ V (f418); T14 —kicked loose f418→ flutters (S8) → reused in the title (f514).
- Cut B forks at f192 with no rewrite: L1 → L1b continuity, real commuter queue, normal boarding.

