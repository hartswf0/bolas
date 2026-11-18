# Monsieur Ripois / « Rien n'y manquait » — SCION swarm plan

Director's plan, rebuilt from scratch. Base revision: `prompts/monsieur-ripois.md` (as read on 2026-11-16); chosen direction = proposals 1 + 2 (`proposals/kf-1.png`, `proposals/kf-2.png`), receipt of direction 3 as final evidence.
Film script (editor): `films/monsieur-ripois.py` (kit `Film`, 960×540, 24 fps, picture area 4:3 = 720×540 centred, pillarboxed). Target 44.0 s.

---

## 1 · Creative thesis

A man on a sofa tells a woman how he returned her family's silver box. The telling is an action in the present: he wants to be cleared (and to be let closer); she wants to know where her ring went. His flashback is **made of a different material** from the room he is sitting in: the present is a real 1942 photograph cut into card and articulated; the past is his account, a backlit shadow play he controls. Shadow theatre can only show contour, so the one gesture he wants hidden — the far hand meeting the box while it passes behind his body — is hidden *by the medium itself*: black on black. The room, not the story, holds the evidence: the same box on her lap, with an empty ring slot, and a pawn receipt that slips from his pocket. The viewer should leave knowing that the flashback established only that the box went back; it did not establish that the ring did.

What would make it bland: a flashback that looks as authoritative as the present (neutral paper, no « selon lui »); a listener who reacts before the decisive clause; a receipt that explains everything in text with no look to set it up; pans over stills instead of articulated, timed bodies.

## 2 · Defining beat and comparison baseline

**Defining beat (the TEST SHOT, 0:16.5–0:27.0).** In the shadow play the box passes behind his silhouette for 8 frames while his lid-closing hand and the hidden far hand meet there; it comes out closed. Hard cut to the present: insert of the open box on her lap, the ring slot **empty** (same box, same slot geometry). Back to the two-shot: he says « Rien n'y manquait. » The caption completes on the word *manquait*, and on that frame her head (hat brim) starts dropping −11° toward the box, holding there. His head, mid-lean, stops.

What a viewer should be able to point to: (a) the frame range where the box is swallowed by his silhouette in S2; (b) the empty slot in S3a in the same position as the ring in S2c; (c) the first frame of her head drop coinciding with the onset of « manquait » in the caption.

**Baseline (control cut, rendered from the same script with `--baseline`).** Identical timing, but (1) S3a insert removed (two-shot held instead, lid closed), (2) her head held neutral at 0° throughout, (3) S4/S5 receipt removed (hold on the two-shot, fade). In the baseline C1 and E2 read as consistent: nothing contests him. The master must make a viewer infer "he took it"; the baseline must not. A critic watches both.

**Alternate reaction cut (`--late`).** Head drop moved to the end of the line + 12 frames (prompt §7: two placements; §8: suspicion too early/late).

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Monsieur Ripois*, René Clément, dialogue Raymond Queneau, 1954; 35 mm B&W feature; Ripois narrates his past to a woman he hopes to seduce, the flashbacks are his interested account. |
| target | 44 s 960×540 animated short, 4:3 picture, captions as voice, sound design, no music. |
| preserved relation | teller → listener in the present; the flashback is an *interested* retelling; the listener's inference can diverge from the told image. |
| optics change | live-action photography → (present) articulated photo-cutout of a 1942 documentary print; (past) backlit jointed-card shadow theatre. The difference of medium carries the difference between scene and account. |
| formalism change | voice-over narration → French subtitles timed syllable-by-word; listener gesture keyed to a speech event (SCION #47). |
| concept change | seduction narration → confession that functions as a defence; a material trace (box, receipt) outranks the told image. |
| sound change | dialogue track → no voice (captions); diegetic room tone, clock, lid click, paper; the flashback has a muffled, reverberant sonic perspective. |

Formation epochs (weight 0–100, reason; historical claims marked):
- 1920s silhouette film (Reiniger) — **80**: the flashback's whole grammar (hinged card, contour-only acting). Certain as technique lineage.
- 1940s FSA/OWI documentary photography — **70**: the present-tense plate is a real 1942 Vachon print; its soft flash light and grain set the tone. Certain.
- 1950s French studio cinema (Clément, Queneau) — **60**: subtitle typography, 4:3, soft-key B&W interior, the interested-narration structure. The claim that Clément's film uses flashback as unreliable narration is the brief's reading (source anchor: Fondation René Clément description); recorded as interpretation, not verified scene-by-scene.
- Oulipo/Queneau constraint thinking — **25**: dialogue is short, constrained to one decisive clause; uncertain as direct influence on the film's structure.
- 1970s Gilliam/Python photo-cutout — **30**: articulated photographic heads; used only for mechanics, not for comedy.

## 4 · Olog (types, relations, central operation)

Types (boxes):
- ◻ **Claim** {claim_id, speaker, target_listener, asserted_event, desired_effect, timeline_position(s)}.
- ◻ **SceneEvidence** {evidence_id, event_relation(supports|contests|ambiguous → event_id), perspective(teller|room|material), certainty(subjective|observed|material)}.
- ◻ **ListenerState** {t, hears, sees, infers, withholds}.
- ◻ **Event** (ledger, independent of tellings) {event_id, what, when, who}.
- ◻ **Cue** {cue_id, clause, onset_frame, listener_action, action_onset_frame}.

Arrows: Claim —asserts→ Event; SceneEvidence —relates_to→ Event; Claim —is_staged_by→ SceneEvidence (cutaway); Cue —anchors→ Claim clause; ListenerState(t) —is_changed_by→ Cue | SceneEvidence.

Event ledger (ground truth, never shown as such):
- EV1 14 March: R. brings the borrowed box (with ring) to the listener's aunt.
- EV2 14 March, same visit: the aunt opens the box, sees the ring; R. closes the lid; R. palms the ring with his far hand while the box is behind his body.
- EV3 14 March: R. pawns "une bague or, un brillant"; receipt issued to A. R.
- EV4 later: aunt passes the box to the listener; slot is empty.

Claims: C1 « Je l'ai rapportée chez votre tante le 14 mars, en main propre. » (asserts EV1; desired: credibility). C2 « Elle l'a ouverte devant moi. La bague y était. » (asserts EV2 first half; desired: shift doubt to the aunt/afterwards). C3 « Rien n'y manquait. » (asserts EV2 complete with nothing removed — false; desired: closure).
Evidence: E1 box on her lap (material, supports EV1 — the **corroborating** image). E2 shadow flashback (teller, subjective; supports EV1, EV2-first-half; silent on the palm) . E3a empty slot (material, **ambiguous** — contests C3 but not who). E3b receipt (material, contests C3 directly, dates EV3 = EV1's day).

**Central operation: CUT(Claim_i → SceneEvidence_j → return to ListenerState).**
- Typed preconditions: (P1) Claim_i and SceneEvidence_j are distinct ledger entries (different ids, different source files); (P2) SceneEvidence_j.perspective is *visibly encoded* in the frame (warm paper + « — selon lui — » label + muffled sound) iff perspective = teller; (P3) the object in E2 and E3a share one geometry spec (box §7) so the viewer can match the slot; (P4) the listener action of the cue fires on or after the onset of its clause, never before (`action_onset_frame ≥ onset_frame`).
- Observable consequences: (O1) at the cut back, the first present-tense image is the slot position the flashback showed full, now empty; (O2) her head starts dropping on the onset frame of « manquait » (master) and his lean stops within 6 frames after (he notices); (O3) the paper tint returns to neutral on the cut frame.
- Counterexample (must fail): the flashback rendered on neutral, untinted grey with no label, and the box insert shown full (ring present) — then E2 is presented as verified, C3 is uncontested, the cut corroborates instead of opening a gap. Fixture §7: "A cut that presents E2 as verified while E2 is a subjective reconstruction fails." A second counterexample: her head drops during C1 (before any discrepancy is shown) — suspicion too early; repair per §8 by moving the reaction under C3.
- Replay equivalence/divergence: E2 replayed (master vs baseline) is frame-identical — the telling does not change; what diverges is only the present-tense evidence and reaction. Master vs `--late`: identical except her head key (divergent leverage: early = she already suspects; late = the word lands then she checks). Optional second-teller branch (aunt's view from the doorway side light, far hand visible) is **not** in the 44 s master; if built it is a named branch `branch-aunt` and must keep E2 frame-identical up to the swallow.

ListenerState timeline (master): 0–9 s hears C1/C2, sees closed box, infers nothing, withholds judgement. 21–23 sees empty slot. 25.6 hears « manquait » → infers contradiction (look). 32–36 sees receipt → infers he pawned it the same day. 38–43 withholds reply; acts: puts receipt into the slot, closes lid, turns away from him.

## 5 · Invariants

1. Event ledger (`ledger.json`) is independent of every telling; each Claim and each SceneEvidence has its own id and file of origin; C3 and E2 both survive (§7 fixture).
2. Every frame of S2 carries the perspective mark: paper warmed ≥ 4 % (b-channel shift) relative to neutral, label « — selon lui — », reverberant/muffled sound bed. On the cut frame back, all three are gone.
3. Each pivotal line (C1, C2, C3) has a staged, inspectable listener consequence in `dialogue-cues.json` (frame numbers).
4. Box geometry spec (§7) is shared by both media; slot centre in the present insert and in the shadow play differ by < 5 % of box width (normalised).
5. Cutout rig: bone lengths constant, no detachment at pivots (≤ 1 px gap at 960×540), no visible inpaint seam at max rotation.
6. Shadow puppets: limbs never detach; joint angles within declared limits; the far hand never appears outside the torso silhouette in S2 (assert by mask: hand-piece mask ⊂ torso mask for all S2 frames).
7. Only verified PD / CC0 / CC BY / CC BY-SA material on screen and in sound; every item in `films/credits/monsieur-ripois.json`.
8. Listener action never precedes its clause (P4), in all cuts.

## 6 · Timed shot list — Hard proof (44.0 s, 24 fps)

Picture area 720×540 (4:3) centred; pillarbox black. Captions: white serif italic, 1950s release-print subtitle style, bottom of picture, no band. « » quotes.

| # | time | on screen | heard | material |
|---|---|---|---|---|
| S0 | 0.0–2.0 | Black; white serif italic title « Rien n'y manquait » fades in/out. | Silence → room tone fades in at 1.5. | HANDMADE type. |
| S1 | 2.0–9.0 | PRESENT two-shot (Vachon lounge, cropped to the couple, ~1.1× upscale). Closed silver box on her lap, her hands either side. Caption C1 « Votre boîte… je l'ai rapportée chez votre tante le 14 mars, » 2.5–5.4, then « en main propre. » 5.4–6.6. He leans in 0→+3° on « rapportée » (3.4–3.9), back by 5.0; drawings on twos. Her head holds 0° (no reaction: P4). Caption C2a « Elle l'a ouverte devant moi. » 7.2–9.0. | Room tone (foraged), clock ticking ~1 Hz (foraged), one cushion creak on his lean. | FORAGED LoC 2017831564 (PD) cut into pieces (GrabCut + FK). HANDMADE box layer. |
| S2a | 9.0–12.0 | Cut to SHADOW THEATRE (« — selon lui — » top, paper warm +5 %). Door opens (3 drawings), he walks in: 8-pose walk on twos, far arm already bent behind back. Aunt in wing chair, lamp, scalloped rail; far plane: lounge window blinds (from the same Vachon print) thresholded and softened, drifting 0.3×. | Muffled room tone with long reverb (same bed, lowpassed); door latch; 4 footsteps on parquet. | HANDMADE jointed card puppets, chair, lamp, door; FORAGED blinds layer (LoC 2017831564). |
| S2b | 12.0–14.5 | He offers the box with the near hand (6 drawings); far hand inside his torso silhouette; only his elbow juts past the jacket line. | Steps stop; small box set-down tick. | HANDMADE. |
| S2c | 14.5–16.5 | Aunt opens the lid (4 drawings); the ring shows as a punched light-ring standing in the slot. Caption C2b « La bague y était. » 14.8–16.4. Her earring swings (secondary dynamics). | Hinge creak (soft), muffled. | HANDMADE. |
| S2d | 16.5–19.5 | **The swallow**: he closes the lid with the near hand while his body turns ~10°; the box passes behind/into his torso silhouette for 8 frames (16.9–17.25), his elbow moves 6° (the only trace), box re-emerges closed and is handed to the aunt, who sets it on her lap. Caption « Je l'ai refermée, je la lui ai donnée. » 17.6–19.4. | Lid shut (muffled). No ring sound (silence is declared). | HANDMADE. |
| S3a | 19.5–21.5 | **Cut back — lands on the empty ring slot.** Present insert: the open silver box on her lap, close (box ≈ 60 % of picture width); velvet cushion with pressed ring hollow, slit **empty**. Background = Vachon skirt/sofa fabric, softened as a shallow-focus plane. Paper tint neutral. | Room tone and clock return dry (no reverb) on the cut frame. | HANDMADE box; FORAGED fabric plane (same LoC print). |
| S3b | 21.5–29.0 | Two-shot; box open on her lap. Caption C3 appears in two parts: « Rien n'y » at 23.6, « manquait. » appended at **24.4** (onset of the clause = cue CUE-3). Her head starts −11° drop at 24.4 (master), eases over 8 frames, holds; his lean stops by 24.65 and he holds still (he notices). 27.0–28.0 his far (right) hand comes forward onto his knee — the same hand the shadow hid. | Clock continues; no other sound under the look (silence animates thought); small fabric rustle as his hand moves. | FORAGED/HANDMADE as S1. |
| S4 | 29.0–36.0 | From his breast pocket a folded slip slides out and falls to the sofa cushion between them (29.4–30.2, with weight: accelerate, one small bounce, settle). Her eyes/head turn to it (30.6). 31.5–36.0 INSERT receipt, her hand unfolds it (3 drawings): « MONT-DE-PIÉTÉ · Bureau auxiliaire n° 7 · Engagé le **14 mars** 1953 · une bague or, un brillant · 9 000 F · Déposant : A. R. », ENGAGÉ stamp off-axis. Slow hold on the date line. | Paper slip whisper; fold opening; clock. | HANDMADE receipt (typeset form, stamp, paper tooth, fold), lit and grained to the print. |
| S5 | 36.0–43.0 | Two-shot. She lays the receipt in the empty slot, closes the lid (2 drawings) at 39.5, turns her head away from him (+8°, toward frame edge) at 40.5 and holds. He does not move. No caption. | Lid click (dry, close) at 39.5; clock; tone fades from 42.0. | as S1. |
| S6 | 43.0–44.0 | Black. | Silence. | — |

Baseline and `--late` variants as §2. All three cuts saved by the editor.

## 7 · Element sources (FORAGED / HANDMADE) and shared specs

FORAGED
- **V0** LoC 2017831564, John Vachon, May 1942, "Jim Tillman and his girl in the lounge of the student union. University of Nebraska, Lincoln" — "No known restrictions" (FSA/OWI, US government work). Already in `films/sources/monsieur-ripois/8d04830.jpg` (1024×781) with item JSON. Re-verify `rights_information`; try the master `8d04830u.tif` from tile.loc.gov (listed in item JSON) for a larger scan to cut softness. Used: plate, puppet pieces, fabric insert plane, blinds far plane.
- **Spares** (verified "No known restrictions" in their item JSON): V1 2017831567 (8d04831), Bubley 2017848680 (8d27149), 2017848664 (8d27133). `8d29055.jpg` / it-2017695225 has **no rights field** in its JSON — do not use unless verified.
- **Sound**: Commons (CC0/CC BY/PD only, from extmetadata): an interior room tone, a mechanical clock tick, a paper rustle, a small hinge/latch click; fallback kit synthesis (declared in notes). MIA clip sound is allowed if a quiet interior with no narration is found (credit per shared rules). MIA hand inserts `af625567`, `aaf17c56` are **not** planned for the master.

HANDMADE
- **Silver box** (both media): spec, units of box width w: width w, depth 0.62w, body height 0.30w, lid 0.08w, lid hinged at back edge; velvet insert dark (L≈30–45/255 in present) with ring hollow centred at (0.50w, 0.45 depth); slot length 0.18w, width 0.025w. Front engine-turned (guilloché) pattern computed from actual concentric/wave geometry; mirror lid interior reflects a blurred crop of the V0 plate (its own room); contact shadow and key direction matched to V0 (key high-left of camera). States: closed, lid 33/66/100 % (drawings), empty-slot open, receipt-in-slot. Same spec exported as `box-spec.json` and used for the shadow-play box silhouette (ring as punched light-ring in the slot).
- **Pawn receipt**: typeset form (Courier-like labels + clerk's italic hand), fold, off-axis ENGAGÉ stamp, paper tooth from real noise, laid into the plate with perspective, lit/grained to the print. Fictional institution number; dated 14 mars 1953.
- **Shadow theatre**: jointed card puppets (R.: quiff, lapel notch, shoulder/elbow/wrist + hip/knee/ankle, pin rivets; Aunt: chignon, drop earring with pendulum, open palm, skirt as one piece + replacement profile), wing chair with punched lace, standard lamp with light slot, door frame + door, scalloped floor rail; backlit paper screen with fibre texture from a real noise process; warm +5 %.

## 8 · Animation technique SCIONs

1. **#2 Lotte Reiniger — Articulated Shadow Theater** — carries E2: contour-only acting makes the hidden gesture a property of the medium (the box swallowed by the silhouette). Applied in S2a–S2d: pinned joints with angle limits, exposure sheet on twos, replacement profiles for the aunt's head, contact plane (floor rail), foreground/midground shadows; numeric invariant = no detachment + far-hand mask ⊂ torso mask; viewing test = action reads with colour removed (thumbs/hands distinguishable in the offer pose).
2. **#29 GrabCut — Cutout Extraction Swarm** — carries the present: the Vachon print is cut into real animation layers (her head+hat, his head, his right forearm+hand, her hands, his breast pocket flap) with box/scribble seeds, alpha cleanup, inpainted plate. Applied in S1, S3, S4, S5; deliverable RGBA pieces + masks + original-coordinate transforms. Rotation pivots per FK (#32, used inside this unit: parent/child for forearm→hand, bone lengths invariant).
3. **#47 Sound-to-Action — Viseme and Gesture Swarm** — carries the listener: every listener gesture is keyed to a speech event (caption clause onset) in a cue sheet; holds and silence are scored (no motion without a reason). Applied to S1 (no reaction under C1 — expressive hold), S3b (head drop on « manquait », his stop), S4 (look to receipt on its landing sound), S5 (lid click → turn away); master vs `--late` alternates.

Supporting methods used inside the units (not separate SCIONs): #32 FK, #45 occlusion compositing (box under her hands; receipt under his hand shadow; box swallowed in silhouette), #41 secondary dynamics (earring, receipt bounce), #44 multiplane (blinds far plane in S2).

## 9 · AESTHETIC TARGET (from `assets/references/ripois1.webp`, catalogue/cinema.json id 8)

Measured with PIL on the 1000×777 reference:
- **Medium**: black-and-white studio photograph (gelatin-silver print scan), 35 mm-era studio still.
- **Tonal range**: L percentiles p1 35, p5 37, p25 44, p50 74, p75 141, p95 220, p99 248. Low-key and dark-dominant; blacks are *print* blacks (~35, not 0), highlights reach paper white only on skin/silk/shirt.
- **Palette** (6-colour quantisation, by area): #262c28, #6b6b64, #444740, #313631, #a0a09b, #d3d3ce. Near-neutral with a very slight green-grey cast in the shadows; mean chroma (max−min) ≈ 6.
- **Light**: one sculpting key high camera-left/front, soft fill; faces modelled, background furniture falls off into mid-greys; catchlights; deep suit blacks.
- **Texture**: fine photographic grain, no halftone; pattern accents (leopard throw, pinstripe) as the only busy textures.
- **Framing/scale**: 4:3-ish (1.29) medium two-shot, figures fill ~80 % of width, heads in the upper third, the object (box) in the lower-left third held between them. Tight; no headroom to spare.
- **Typography** (for captions, by period convention, not in the still): white serif italic subtitles.
- **Pacing**: held, theatrical — few cuts, long holds, gesture on the word.

Comparison measured on the proposals: kf-1 (present) p50 95, p99 208 — too bright, highlights not reaching white, picture blacks fine; kf-2 (shadow) chroma 22 — the warm perspective tint is intentional but must stay bounded.

How the film arrives at it (real material and technique only):
- Choose a genuinely B&W documentary print (V0) and crop as close as the reference (couple fills ≥ 75 % of picture width, heads in upper third, box lower third between them); use the larger LoC master scan to keep upscale ≤ 1.3×.
- Since the figures are cut out, burn the background plate separately (a darkroom burn-in done per layer) so the walls fall to mid-grey and the figures carry the key — matching the reference's falloff. Then one global tone curve to unify: target p5 30–45, p50 65–100, p99 ≥ 235, chroma ≤ 10 in present shots.
- The handmade box is shaded from its geometry with the same key direction as V0, reflections from the plate itself, and the plate's own grain sampled and applied (measured grain std matched within 25 %), so it sits in the print rather than on it.
- Shadow theatre: silhouettes at ≈ #1c1713, paper L 180–215, chroma ≤ 25; it is deliberately warmer than the present (perspective mark) and returns to neutral at the cut.
- Captions: Liberation Serif Italic (system) or Instrument Serif italic-equivalent, white with a thin dark edge, ~26 px at 960×540.

## 10 · Swarm units (the editor/assembler and the independent critic run separately)

Workspace `films/swarm/monsieur-ripois/`; media under `films/sources/monsieur-ripois/<role>/`. All units read this plan, the prompt, BRIEF-2.md, and the SCION prompts named for them in swarms.json in full. Each unit ≤ ~45 min, downloads ≤ ~75 MB total.

**U1 · dramaturg-sound** (dramaturg + dialogue writer + listener scoring + sound; mode: both)
- Writes `ledger.json`: events EV1–EV4, claims C1–C3 (all Claim fields), evidence E1, E2, E3a, E3b (all SceneEvidence fields), ListenerState timeline, the two agendas (teller: be cleared + closeness; listener: locate the ring, decide whether to trust him), the cut → evidence → listener links, and the baseline/`--late` definitions.
- Writes `dialogue-cues.json`: final French lines (+ English gloss), each caption's split points and onset frames, every listener/teller gesture key (cue_id, clause, onset_frame, action, action_onset_frame, ease, hold) for master and `--late`, and the P4 assertion list. Follows #47.
- Forages and prepares sound from Commons (licence from extmetadata) or MIA: room tone, clock tick, hinge/latch, paper rustle, footsteps; builds a dry present bed and a muffled reverberant flashback bed; saves WAVs under `films/sources/monsieur-ripois/sound/` with a `sound-manifest.json` (file, source, licence, cue times) and appends credits entries.
- Output: `films/swarm/monsieur-ripois/ledger.json` (primary), plus `dialogue-cues.json`, `sound-manifest.json`.

**U2 · present-cutout** (editor-of-evidence for the present: plate, cutout puppets, handmade box, receipt; mode: both)
- Re-verifies V0 rights and fetches the larger master if feasible; GrabCut-extracts pieces (#29) with masks and failure masks; inpaints the plate; burns the background plate; FK rig with pivots and limits (#32).
- Builds the handmade silver box from `box-spec.json` (writes it first, by 15 min, for U3) in all states, and the handmade receipt; implements occlusion (her hands over box, receipt fall with bounce).
- Delivers an importable module `films/swarm/monsieur-ripois/present_puppets.py` with `render_twoshot(t, keys) -> PIL.Image (720×540)`, `render_box_insert(t, state)`, `render_receipt_insert(t)`, reading keys from `dialogue-cues.json`; plus keypose PNGs and a reference side-by-side `present-vs-ref.jpg`.
- Output: `films/swarm/monsieur-ripois/present-manifest.json` (pieces, pivots, limits, source coords, box states, measured tone stats), media under `films/sources/monsieur-ripois/present/`.

**U3 · shadow-theatre** (animator of the flashback E2; mode: handmake + one foraged far plane)
- Builds the jointed card puppets, chair, lamp, door, rail, backlit paper; the blinds far plane from V0; the box silhouette from `box-spec.json` (ring as punched light).
- Animates S2a–S2d straight-ahead/pose-to-pose on twos per an exposure sheet (walk 8 poses, offer 6, lid 4, swallow 8 frames, hand-off), with secondary dynamics on the earring; asserts no detachment and far-hand mask ⊂ torso mask on every frame.
- Delivers `films/swarm/monsieur-ripois/shadow_theatre.py` with `render_flashback(t) -> PIL.Image (720×540)` for t in [0, 10.5] (S2 local time), and a contact sheet `shadow-contact.jpg` + greyscale-read test sheet.
- Output: `films/swarm/monsieur-ripois/exposure-sheet.json` (poses, joint angles per frame, limits, assertion results), media under `films/sources/monsieur-ripois/shadow/`.

Dependencies: U2 writes `box-spec.json` early (U3 reads; if absent at start U3 uses §7 numbers, identical). U1's `dialogue-cues.json` drives U2 key timing; U2 starts from §6 times and re-reads cues before final keyposes. The editor imports U2/U3 modules and U1 sound into `films/monsieur-ripois.py` and renders master, `--baseline`, `--late`.

## 11 · Acceptance bar (falsifiable; critic watches at normal speed first, then reads `ledger.json`)

1. **Duration & assembly**: the master plays 30–45 s with sound; baseline and `--late` cuts exist from the same script; S2 sits between two present-tense shots and the first frame after S2 shows the open box with an empty slot. (structural)
2. **Perspective marked, E2 not verified**: every S2 frame shows « — selon lui — » and a paper tint warmer than the present (mean b* or R−B ≥ 4 units above S1), and the tint/label/reverb are gone on the cut frame back; `ledger.json` lists E2 with perspective = teller, certainty = subjective, and C3 and E2 as distinct entries. (measured + structural)
3. **The hidden gesture is hidden and traceable**: in S2d the box disappears into his silhouette for ≥ 6 consecutive frames and reappears closed; his far hand is never visible outside the torso in any S2 frame (exposure-sheet assertion), yet a viewer can name the moment the ring could have been taken. (measured + perceptually judged)
4. **Cue timing**: in the master, her head's first moving frame is within ±2 frames of the onset of « manquait »; in `--late` it is ≥ 12 frames after the line ends; under C1/C2 her head is still (0 change). (measured from frames vs `dialogue-cues.json`)
5. **Listener can decide differently**: watching master vs baseline, a fresh viewer says in the master that he likely took/pawned the ring and that she withholds/ends the encounter (receipt into slot, lid closed, turns away), and in the baseline finds no contradiction. (perceptually judged; two viewers if possible)
6. **Aesthetic, tonal (side-by-side)**: a contact sheet placing S1, S3b and S5 frames beside `ripois1.webp` at equal height shows a matched B&W tonal range: present-shot picture area p5 in 25–50, p50 in 60–105, p99 ≥ 230, mean chroma ≤ 10; the box reads as an object lit by the same key as the room (critic judges it is not "pasted on"). (measured + perceptually judged)
7. **Aesthetic, framing & medium (side-by-side)**: beside the reference, the two-shot frames the couple at ≥ 75 % of picture width with heads in the upper third and the box in the lower third between them; the shadow-theatre frames read as backlit cut card (contour-only, joints pinned, no internal shading); no filter-faked grain over drawn shapes. (perceptually judged + measured widths)
8. **Provenance**: every foraged image/sound appears in `films/credits/monsieur-ripois.json` with a PD/CC0/CC BY/CC BY-SA licence read from its source; nothing from Clément's film is used. (structural)
