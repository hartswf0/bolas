# Zazie dans le métro: assembly (montage editor, round 3)

Script: `films/zazie-dans-le-metro.py` (kit `Film`, kit.py unchanged). It imports U3's rig `sources/zazie-dans-le-metro/puppet/puppet.py` and U3's approved test shot `puppet/build/test_shot.py` (S3/S4 are its exposure sheet, hair simulation and compositing, unchanged). It reads U1's `gag-route.json` (tile geometry, syllable frames, exposure-sheet mouths for S1, shot positions) and U2's plates and cutouts in `sources/zazie-dans-le-metro/forage/`. Sound is U4's gated mix (`sound/soundbed-preview.wav`, `-B.wav`), decoded with ffmpeg and added to the kit Mix.

Outputs:
- cut A `assets/films/zazie-dans-le-metro.mp4` (22.0 s)
- cut B `assets/films/zazie-dans-le-metro-control.mp4` (22.0 s, frames 0-191 identical to A)
- negative control `films/swarm/zazie-dans-le-metro/negctl.mp4` (7.0-10.0 s of A, no puppet, no plaque)
- `frame-ledger.json` (per frame, both cuts), `compare-ref.jpg`, `films/credits/zazie-dans-le-metro.json`, `films/notes/zazie-dans-le-metro.txt`

Evidence IDs: P1-P4 = LoC Photochrom plates 2001698526, 2002707975, 2001698539, 2001698544 (U2 evidence-ledger.json). V = tram cutout from P2 (U2 cutouts.json). FG = plane-tree cutout from P1. PAPER-kraft / card / book1928 / book1929 = U3 rig.json `puppet-paper`. SND1 = Commons wind (CC BY-SA 4.0). MIA-VALLEYTOWN = Valley Town (1940) via movingimagearchive.com. SYN = kit-synthesized (U4 `synth_items`). H = handmade.

## Timecoded sequence, cut A

| tc (s) | frames | shot | on screen | evidence |
|---|---|---|---|---|
| 0.00-2.00 | 0-47 | S1 setup, MS, L1 | Z waist-up frame left (FK: head tracks V +12°, arm to point f24-30), handmade MÉTRO/GRÈVE sign, V crosses the far plane L→R from f12. Captions « Le métro ? En grève. » f10, « …le tram, alors ! » f31. Offscreen bell f8 (left). | P1 (P1W crop), V, H (puppet, sign), SYN bell, U4 bed |
| 2.00-6.00 | 48-143 | S2 chase, MLS, L1 | Full figure, 8-drawing run cycle on twos (16 f stride), hip 80→420 px; V ahead, gap 180→320 px; camera drifts 60 px: plate 0.25x, foreground crowns 1.4x (straight crop edges off frame). Bob on a 1-D spring. | P1, V, FG, H, SYN footsteps on contacts |
| 6.00-8.00 | 144-191 | S3 test shot, CU, L1 | U3 test shot unchanged: laugh 1-4-5-4-6, crescent eyes, cheeks up, head rock; gust from 6.6 s sweeps the fringe across her right eye; hold f184-191 (mouth 5). | P1, H, PAPER-*, SND1 gust; silence 7.667-8.000 |
| **8.000** | **192** | **JUMP CUT** to S4, CU, L2 | same drawing, mouth 5, hair state carried; plate P1→P2, native tram V mid-right; plaque PLACE DE CLICHY pops f196; f216 eyes open on the tram, gulp; caption « … le tram ! » f222. | P2, V (native), H plaque |
| 10.00-10.50 | 240-251 | S5 push-in | multiplane push: puppet plane 1→4.5x about the mouth, plate plane 1→1.6x; the paper mouth-tunnel set fades in under the push (f244-250). | P2, H |
| 10.50-12.40 | 252-297 | S5 bouche de métro, ECU | lips, gums, 6 tunnel rings, the Clichy plate as the far light; 14 tiles as teeth (DOUK · IPU above, gap between K and I; DONKTAN below). Jaw opens on twos per syllable DOU f254 KI 259 PU 264 DONK 269 TAN 275 and the syllable's tiles pop 6 px; TAN drops the jaw to the row floor (y 452); the N tilts f278; the 7 lower tiles come loose one per frame f281-287, hop under gravity, rotation springs settle upright by f296. Caption « Doukipudonktan ! » f258. | H, P2 (far light), MIA-VALLEYTOWN tunnel, SYN clicks/clatter |
| **12.417** | **298** | **MATCH CUT** to S6, MLS, L3 | the same 7 tiles (feet added) on the same row y 452 and spacing 64 at place du Châtelet; plaque pops f300; caption « faire la queue… » f302; V waits at frame right. Z runs in f312, hits the queue f326 (squash pose), rebounds 60 px, hair flung forward, silence f328-333; the bump runs down the queue; dominos flip f335-359 (ticks on landings f341…359) into a 3-column stair plus T14 upright on top. | P3, V, H, SYN impact/ticks |
| 15.00-18.00 | 360-431 | S7 recovery, same setup | run to the stair f360-381; climb with the near ankle pinned on each tread (f382, 391, 400, 409; IK hip, pin error 0), deck step f414, sits on the impériale f418; T14 kicked loose f418 and falls; tram starts f426. | P3, V, H |
| 18.00-20.00 | 432-479 | S8 resolution, CU, top deck | reference framing; P3 slides R→L behind her, handmade deck railing rides with her; breeze gust then steady air on a fresh U3 HairSolver run; laugh cycle; the loose N flutters past on the near plane f450-470; caption « Zazie a pris le tram. » f442. | P3, H, SND1 breeze, SYN hooves |
| 20.00-22.00 | 480-527 | tail | cut-paper title « ZAZIE / DANS LE / MÉTRO » on dark card: D, O, I, A, T and the N are the T tiles reused (the stair N lands last, f514); Z, E, S, L, M, É, R are new title tiles (declared exception to invariant 4); credit lines. | H |

## Cut B (continuity control)

| tc (s) | frames | shot | on screen |
|---|---|---|---|
| 0.00-8.00 | 0-191 | S1-S3 | identical frames to cut A (same cached images; measured diff below) |
| 8.00-10.00 | 192-239 | S4b | ordinary cut to a reverse angle down boulevard de la Madeleine (P4); Z runs in from frame left, V far ahead |
| 10.00-12.40 | 240-297 | S5b | MCU on P4: she says the word (mouth 7-4-7-5-6 on the syllable frames), then laughs; caption « Doukipudonktan ! » |
| 12.417-18.00 | 298-431 | S6b/S7b | plain cut to L3: 7 handmade paper commuters queue at the stop, Z runs in and waits at the end, the queue shuffles, they board one by one behind V's rear platform and she follows |
| 18.00-20.00 | 432-479 | S8b | CU inside the tram (handmade varnished-card window frame, P3 through the window), laughing, still air |
| 20.00-22.00 | 480-527 | tail | same title card |

## Word-to-gag table

| word | literal | gag reading | prop | setup → payoff → consequence |
|---|---|---|---|---|
| métro en grève | the underground is on strike | the goal is blocked before the film starts; the only ride left is the tram | handmade enamel MÉTRO sign + pasted GRÈVE strip (S1) | f0-47 → she points at V (goal declared) → every later operation is measured against distance(Z, V) |
| (laugh) | — | the anchor that survives the impossible cut | the CU puppet (mouth 5, orange collar, hair springs) | S3 laugh → jump cut f192 (the city moves, she does not) → V is now mid-frame: closer |
| Doukipudonktan | d'où qu'il pue donc tant | the word is her teeth: 14 cut-paper letter tiles | T1-T14 | syllables f254-275 → TAN drops the jaw, the lower 7 come loose → they leave her mouth as objects |
| bouche de métro | métro entrance ("métro mouth") | her open mouth is the métro entrance: tunnel rings, Clichy light at the end | lips, gums, tunnel rings (H) | push-in f240-251 → ECU f252-297 → the falling teeth carry the match cut |
| faire la queue | to queue | the queue is literally the word's letters, and it blocks her | T8-T14 with paper feet | match cut f298 → collision f326 (setback, bounce 60 px) → domino stair → she climbs onto the impériale |

## Route and continuity exceptions

- Toward the tram is left → right in every shot (invariant 1). L1: Z enters frame left, V leaves frame right (S2). L2: same CU anchor, V native mid-right. L3: Z enters left, queue/stair centre, V at frame right; deck at (606, 208).
- **Exception E1, AnchoredJumpCut f192** (apparent place): the city moves, the girl does not. Preconditions asserted in code (see Ledger).
- **Exception E2, TileRewrite teeth → queue f297/298** (object identity, match cut): same 7 tiles, row y and spacing held.
- **Exception E3, queue → steps f335-359** (route): cause is Z's collision; the flips are cartoon physics (tiles leap into stacked columns), declared.
- **Exception E4, tail title**: new title tiles for letters not in T; T itself stays 14 objects.
- Deviation from the plan: the stair is three stacked columns (1, 2, 3 lying tiles) plus T14 standing on top, not seven tiles leaning at 40°: seven tiles on one ground line cannot make a rising stair, stacking can. The V card in L3 is placed at x 560 at scale 1.0 (plan bbox x 598, larger) so more of the tram reads. Captions are 25 px Instrument Serif cream on a faint dark band.

## Timecoded gag cues (cut A)

| f | tc | cue |
|---|---|---|
| 8 | 00:00:00:08 | tram bell offscreen left (before V is seen) |
| 10 / 31 | 00:00:00:10 / 01:07 | captions: strike, then the tram |
| 12 | 00:00:00:12 | V enters the far plane, head tracks it |
| 30 | 00:00:01:06 | she points at V: goal declared |
| 48-143 | 00:00:02:00 | the chase, footsteps on contacts every 8 f, V pulls away |
| 158 | 00:00:06:14 | gust: fringe sweeps across her right eye |
| 184-191 | 00:00:07:16 | declared hold + silence at full laugh |
| **192** | **00:00:08:00** | **jump cut to place de Clichy**, close bell |
| 196 | 00:00:08:04 | plaque snap |
| 216 | 00:00:09:00 | eyes open on the tram, gulp |
| 240-251 | 00:00:10:00 | push-in into the mouth, tunnel resonance |
| 254 259 264 269 275 | 00:00:10:14 … 11:11 | DOU KI PU DONK TAN: jaw + tile pops + pitched clicks |
| 278 | 00:00:11:14 | the loose N tilts |
| 281-293 | 00:00:11:17 | lower tiles come loose, clatter, land on the row |
| **298** | **00:00:12:10** | **match cut: the teeth are the queue at Châtelet** |
| 300 / 302 | 00:00:12:12 | plaque snap / « faire la queue… » |
| 326 | 00:00:13:14 | **impact**: she hits the queue (squash), then silence f328-333 |
| 335-359 | 00:00:13:23 | domino flips, ticks rising every 3 f on the landings |
| 382 391 400 409 414 | 00:00:15:22 … 17:06 | card steps on each tread, deck step |
| 418 / 426 | 00:00:17:10 / 17:18 | bell twice, she sits, the N is kicked loose; tram moves |
| 442 | 00:00:18:10 | « Zazie a pris le tram. » |
| 450-470 | 00:00:18:18 | the N flutters past |
| 480-527 | 00:00:20:00 | title card, last tile (the N) f514, final click f520 |

## Strongest checkpoint

Frames 191 → 192 (7.958 → 8.000 s): same paper puppet, same drawing (mouth 5, hair state carried, crown centroid Δ 0 px, collar hue unchanged), plate swaps from the Madeleine to the place de Clichy with her tram now mid-frame. With the negative control (`negctl.mp4`) the same swap without her is a plain location change. Second strongest: f297 → f298, the seven loose teeth on row y 452 become the queue on the same row.

## Ledger / claim graph (measured; from frame-ledger.json)

MEASURED_BLOCK
