# La belle Hortense: assembly (editor revision E2, repair round 1)

- **Film:** `assets/films/la-belle-hortense.mp4`, 66.0 s, 960×540, 24 fps, AAC stereo. Poster `assets/films/la-belle-hortense.webp` (43.3 s). Size and measures: see "Measured" below.
- **What it is:** a fiction that re-stages archive photographs. It is an hommage to the novel by Jacques Roubaud (1985) and takes nothing from the novel or its cover. The title card and end card say so on screen (fiction label: 11 px cap height on the title card, 10 px on the end card). The film is licensed CC BY-SA 4.0 because it synchronises CC BY-SA 3.0 and 4.0 recordings. This is stated on the end card, in the credits JSON and in the note.
- **Script:** `films/la-belle-hortense.py` (kit.Film; kit.py not edited). At import it asserts:
  - σ=[6,1,5,2,4,3], and the fixture ABCDEF→FAEBDC holds;
  - σ⁶=id; each module is σ of the previous one, and VI returns to I;
  - no module repeats a motif;
  - each slot's clip shows that slot's motif;
  - each slot's type overlay has `active_word == order_i[k]` at every slot midpoint.
- **Built on:**
  - structure.json **S2**: K6 and K10 retagged `corroborates`; R1 and R2 typed `reveal`. verify.py now also checks C1c (every support of S at or before 21.0 s) and C1d (reveals are not supports). Results: structure PASS, baseline FAIL with 14 checks, M1 FAIL, M2 FAIL. Log in `verify.txt`.
  - scenes.json A1 (U3), print.json and sound_cues.json (U4), ledger.json (U2, plus the `editor_E2` block).
  - Editor beats: `editor/editor_beats.py` (E1) and **`editor/repair_beats.py` (E2)**.
  - Cards: `editor/cards.py`. Credits and ledger: `editor/credits_e2.py`.
  - Clips are in `films/sources/la-belle-hortense/editor/clips/`.

## What E2 changed (answers to critic-1 and review-1)

| issue | repair | where |
|---|---|---|
| Coat on the bench read as a stepped red block | **Draped coat.** The same LoC 2017844115 coat panel and the same red dye: collar (kept in mono), shoulders and buttons hung over the bench back, the empty sleeve falling over the seat edge, the skirt folded forward on its waist hinge (foreshortened, in shade), a hem flap over the seat edge, and a contact shadow on the slats. The key lies on the folded skirt. | I.1–I.6, VI.6, and the I.4 replays IV.2 and VI.2 (`*_E2`) |
| II.2 lift unreadable | **Re-staged lift.** The conductor's own sleeve and hand (forearm piece cut from the same print; the hand is masked from the background) come down to the collar (0–0.40 s), the fingers close and the coat sags (0.40–0.50), then the coat is lifted: the skirt swings open on its hinge, with a brass glint of the key bow in the fold on frames 12–17. From 1.05 s it plays U3's swap: the conductor wears the coat behind the bench. | `II2_manteau_E2` |
| I.3 showed no key; the envelope was a flat polygon | **A foraged envelope.** The back of an 1861 stamped envelope (LoC 2010652109, no known restrictions), cut out with a threshold mask refined by GrabCut, with a contact shadow on the gravel. The CC0 key (re-sampled at 205 px) slides bow-first out of its slit top edge and is half out at 6.75 s. U4's handmade envelope is no longer on screen. | `I3_cle_E2` |
| III.1 showed a pole | The visitor's shadow-theatre turn now finishes by 0.45 s, and the brass key hangs from her hand as a damped pendulum. This is the hypothesis "Elle l'a reprise ?", shown as a shadow. | `III1_cle_E2` |
| IV.5 coat only at the frame edge | The sweep is re-timed so the coat (scale 1.5) crosses mid-frame at 36.75 s. | `IV5_manteau_E2` |
| V.1 no bench | The camera accelerates as t³ (still 0 → 4200 px/s), so the bench is in frame through 39.75 s. | `V1_banc_E2` |
| V.2 receipt edge-on | U4's receipt card (state 2, underlined), 230 px wide, flutters face-on at 41.25 s. | `V2_recu_E2` |
| V.4 key invisible, plate seam | **Two parts.** (1) Local 0–0.70 s: a labelled half-speed replay ("V·3 ralenti ×0,64", cream mat like the I·4 replays) of 43.15–43.60 s, zoomed 1.45× on the hem. Each frame is integrated in source time with its shutter scaled to the replay speed, so it is a high-speed exposure, not a blur. The key leaves the fold and falls in view. (2) From 0.70 s: one photograph of grass (a single meadow-plate crop, no strip seam). The key lies large (205 px piece), rocking to rest, with a contact shadow. The red sleeve and hand come down at 1.00 s, close on it at 1.22 s and lift it out. | `V4_cle_E2` |
| V.3 key trajectory measured only from authored positions | Measured from the rendered V.4 replay frames: each frame is rendered with and without the key, and the difference mask's centroid is fitted with a parabola. See "Measured". V.3 itself is unchanged (the protected test shot). | `editor/measures/v4_replay_key.json` |
| Clicks inaudible | Every typewriter click and strike is raised +10 dB (`CLICK_BOOST`). | film script `cue_plan` |
| No fiction label; Roubaud in the author slot; "D'après"; no film licence; fonts uncredited; note wrong about type | New title type: "La belle Hortense" in red; "exercice sur une sextine, en hommage au roman de Jacques Roubaud (1985)" in black on cream strips; the fiction label on a black band. New end-card text from 60.5 s: the fiction label, credits with typefaces, "Hommage ; rien n'est repris du roman ni de sa couverture.", and "Ce film est publié sous licence CC BY-SA 4.0". Credits JSON gains Courier 10 Pitch, DejaVu (σ), the envelope, and the film-licence record; the paper licence_url is filled. Note rewritten. | `editor/cards.py`, `editor/credits_e2.py` |
| LoC items resting on on-disk JSON | Re-verified live on www.loc.gov on 2026-11-16: 2017844115, 2017750547, 2017750548 and 2013633886 all read "No known restrictions". | `sources/.../editor/forage/live_loc_*.json`, ledger `editor_E2` |

## Timecoded sequence

| t (s) | slot | motif | function | picture | evidence IDs | clue | caption |
|---|---|---|---|---|---|---|---|
| 0.0–3.0 | title | — | — | TITLE pan exposure (Bourré meadow, 420 px integrated travel) + E2 title type | SHED-MEADOW, TITLE-E2 (handmade type, Courier 10 Pitch), BELL-SND 0.4 | | La belle Hortense · hommage · fiction label |
| 3.0–4.5 | I.1 | manteau | background | I1_manteau_E2: draped coat on bench | COND (coat panel), BENCH, SHED-MEADOW | K0 | Une gare vide. |
| 4.5–6.0 | I.2 | cloche | action | I2_cloche_E2 | VISITOR-F, BELL, BENCH, COND, BELL-SND, STEPS | | Une cloche sonne. |
| 6.0–7.5 | I.3 | clé | action | I3_cle_E2: LoC envelope, key half out | ENVELOPE-LOC, KEY, SHED-MEADOW, PAPER | | Dans l'enveloppe, une clé de laiton. |
| 7.5–9.0 | I.4 | banc | action | I4_banc_E2: key laid on the folded skirt | VISITOR-F, KEY, BENCH, COND, KEYS-SND | K1 | Elle la laisse sur le banc. |
| 9.0–10.5 | I.5 | reçu | action | I5_recu_E2 | VISITOR-F, RECEIPT, BENCH, COND, PAPER | | Un reçu tombe. |
| 10.5–12.0 | I.6 | porte | background | I6_porte_E2 | VISITOR (back), BENCH, COND, STEPS | | La porte de service reste fermée. |
| 12.0–13.5 | II.1 | porte | action | II1_porte (E1) | COND (hand), SHED-DOOR, HANDLE | | Fermée. |
| 13.5–15.0 | II.2 | manteau | action | II2_manteau_E2: hand lifts the coat, glint, swap to wearer | COND (sleeve, hand, coat), BENCH, KEY glint | K2 | Il reprend son manteau. |
| 15.0–16.5 | II.3 | reçu | evidence | II3_recu (E1) | RECEIPT, PAPER | K4 | « remise au banc » |
| 16.5–18.0 | II.4 | cloche | action | bell_strike (U3) | BELL, SHED-DOOR, BELL-SND | | Le train est annoncé. |
| 18.0–19.5 | II.5 | banc | absence | bench_empty (U3) | BENCH | K3 | Le banc est vide. |
| 19.5–21.0 | II.6 | clé | absence | II6_cle (E1) | KEY, RECEIPT | | Où est la clé ? |
| 21.0–22.5 | III.1 | clé | false-lead | III1_cle_E2: shadow visitor with key | VISITOR-F/VISITOR, KEY | | Elle l'a reprise ? |
| 22.5–24.0 | III.2 | porte | evidence | III2_porte (E1) | SHED-DOOR, HANDLE | K9 | Toujours fermée. |
| 24.0–25.5 | III.3 | banc | evidence | bench_empty (U3) | BENCH | K5 | Rien sous le banc. |
| 25.5–27.0 | III.4 | manteau | background | III4_manteau (U3) | COND (far), STEPS | K6 (corroborates) | Au loin, quelqu'un traverse. |
| 27.0–28.5 | III.5 | cloche | evidence | bell_strike (U3) | BELL, BELL-SND | K7 | La cloche sonne seule. |
| 28.5–30.0 | III.6 | reçu | evidence | III6_recu (E1) | RECEIPT, PAPER | K8 | « remise au banc » : elle l'a laissée. |
| 30.0–31.5 | IV.1 | reçu | evidence | IV1_recu (E1) | RECEIPT, PLATE6 | | Reçu n° 6, porte n° 6. |
| 31.5–33.0 | IV.2 | clé | false-lead | I4_banc_E2 replay + I·4 mat | = I.4 pixels | K10 (corroborates) | Un voleur ? |
| 33.0–34.5 | IV.3 | cloche | false-lead | bell_strike (U3) | BELL, BELL-SND | | Ou la cloche ? |
| 34.5–36.0 | IV.4 | porte | evidence | IV4_porte (E1) | SHED-DOOR, PLATE6, HANDLE | K11 | Aucun voleur n'a ouvert. |
| 36.0–37.5 | IV.5 | manteau | action | IV5_manteau_E2: coat crosses mid-frame | COND, run stage | | Quelque chose revient. |
| 37.5–39.0 | IV.6 | banc | absence | bench_empty (U3) | BENCH | | Qui a la clé ? |
| 39.0–40.5 | V.1 | banc | action | V1_banc_E2: bench in frame as the pan starts | BENCH, run stage | | Quelqu'un court vers le banc. |
| 40.5–42.0 | V.2 | reçu | action | V2_recu_E2: receipt card in the wake | RECEIPT, run stage, COND | | Le reçu s'envole. |
| 42.0–43.5 | V.3 | manteau | evidence | V3_manteau_clean frames 12–47 = the accepted TEST SHOT, unchanged | COND, SHED, SHED-MEADOW, KEY, STEPS | R1 (reveal) | le manteau revient |
| 43.5–45.0 | V.4 | clé | evidence | V4_cle_E2: replay ×0.64 (labelled), then the key large on grass; hand takes it | COND, KEY, SHED-MEADOW, KEYS-SND (tinks re-timed to 44.15 and 44.33) | R2 (reveal) | La clé était dans le pli. |
| 45.0–46.5 | V.5 | porte | action | V5_porte (U3) + enamel 6 | SHED-DOOR, KEY, PLATE6, LOCK, HINGE | | La porte s'ouvre. |
| 46.5–48.0 | V.6 | cloche | action | bell_strike (U3) | BELL, BELL-SND | | La cloche sonne : c'est ouvert. |
| 48.0–49.5 | VI.1 | cloche | closure | VI1_cloche (U3) | BELL, BELL-SND tail | | La cloche se tait. |
| 49.5–51.0 | VI.2 | banc | evidence | I4_banc_E2 replay + I·4 mat | = I.4 pixels | | Elle l'avait posée sur le manteau. |
| 51.0–52.5 | VI.3 | porte | closure | VI3_porte (E1) | SHED-DOOR, PLATE6 | | La porte reste ouverte. |
| 52.5–54.0 | VI.4 | reçu | closure | VI4_recu (E1) | RECEIPT (RENDU) | | RENDU. |
| 54.0–55.5 | VI.5 | clé | closure | VI5_cle (E1) | KEY, SHED-DOOR, hook (handmade), KEYS-SND | | La clé à son crochet. |
| 55.5–57.0 | VI.6 | manteau | background | I1_manteau_E2 (identical pixels to I.1) | COND, BENCH | | Le manteau, sur le banc. |
| 57.0–66.0 | end card | — | — | U4 rows 0…6 (one per 0.5 s), σ line 60.5 s; from 60.5 s the E2 panel (fiction label, credits, typefaces, hommage line, film licence) | ENDCARD (handmade), BELL-SND 57.2 | | σ⁶ = id · ABCDEF |

**Streak progression:**
- I: none (static camera).
- II–IV: partial (E1 drifts of 60/120/200 px/s; III.4 160 px/s; IV.5 1500 px/s).
- V.1: from still to full speed. V.2–V.3: full (4200 px/s, 36 sub-frames).
- V.4: high-speed replay, then still.
- V.5 onward: still; VI: none.

## Claim graph (structure.json S2, as it is on screen)

- **S:** the conductor carried the key away in the fold of his coat. It becomes inferable at 13.5 s (II.2).
- **Supports, all at or before 21.0 s:**
  - K0, I.1, 3.0 s: the coat is draped on the bench.
  - K1, I.4, 7.5 s: the key is laid on the folded skirt.
  - K2, II.2, 13.5 s: a hand lifts the coat, a glint shows in the fold, and the conductor wears it.
  - K3, II.5, 18.0 s: the bench is empty.
- **Corroborations (not supports):**
  - K6, III.4, 25.5 s: a red figure far off.
  - K10, IV.2, 31.5 s: replay of the I.4 pixels.
- **Refutations before 39 s:**
  - ALT-1 (the visitor took it back) is refuted by K4 (II.3) and K8 (III.6), "remise au banc". III.1 shows that hypothesis as a shadow.
  - ALT-2 (a thief) is refuted by K9 (III.2) and K11 (IV.4): the door is still locked.
  - ALT-3 (the bell) is refuted by K5 (III.3) and K7 (III.5).
- **Reveals (typed `reveal`, not supports):**
  - R1, V.3, 42.0 s: the key leaves the hem at 43.2 s.
  - R2, V.4, 43.5 s: the key is seen leaving the hem in the half-speed replay, lands, and a hand takes it.
- **Background to evidence:** A (manteau) is background in I.1, III.4 and VI.6 and evidence in V.3. It is the same coat panel (LoC 2017844115) with the same red dye in every appearance.
- **Fresh reader:** NOT RUN. No naive human viewer was available to this unit. The protocol (`reader-protocol.md`) is ready, and the ledger records the absence. Fair play is verified structurally only.

## Measured

**The film:**
- `assets/films/la-belle-hortense.mp4` runs **66.0 s** and is **5.0 MB** (5,025,971 bytes), 960×540 at 24 fps.
- Diagnostic: `la-belle-hortense-baseline.mp4`, 15.5 s, 0.9 MB, story order. Its II.2 and V.4 now use the E2 clips.

**43.3 s (the test shot, unchanged), measured on the decoded frame:**
- coat hue −5.6° (target −6 ± 8), coat saturation 1.0;
- green 72.8 %, lower-half gy/gx 1.90;
- luma p5/p25/p50/p75/p95 = 18/50/86/101/163;
- board: `board-43.3.jpg`.

**44.25 s (V.4):**
- The key covers 1.72 % of the frame (target ≥ 0.5 %). It spans 201 px, 21 % of the frame width (target ≥ 8 %).
- Its median colour in the encoded frame is #8f7329 (brass, a little darker than #c9a23a).
- It sits on one grass photograph, with a contact shadow and no seam.
- Board: `board-44.25.jpg`.

**Key trajectory measured from the rendered V.4 replay frames** (`sources/.../editor/measures/v4_replay_key.json`):
- Visible and tracked in 14 consecutive replay frames, against 9 frames at real speed in V.3.
- The parabola fits with an RMS residual of 2.8 px.
- The apparent acceleration is 3.8×10³ px/s² in source pixels, against the 2.6×10³ authored. The measure is the centroid of the visible key area: the near shin occludes the key, and the key rotates at 690°/s. Both bias the centroid, so the measured value is reported as measured.

**Fiction label:**
- Cap height 11 px on the title card at 1.5 s (Courier 10 Pitch Bold 18 px).
- Cap height 10 px on the end card from 60.5 s.
- Board: `board-title.jpg`.

**Sound:**
- Every one of U4's 82 cues is placed with `mix.add`.
- Typewriter clicks and strikes are +10 dB. Mix peak before mastering is 1.15, so kit's master lowers the whole mix by 1.2 dB uniformly. Relative levels and bell times are unchanged: 0.4, 4.6, 16.6, 27.1, 33.1, 46.6 and 57.2 s.
- V.4 key tinks are re-timed to 44.15 s (landing, as seen in the replay) and 44.33 s.
- 37.6–38.95 s and 63.05–65.9 s are digital zero in the encoded film.

**Stills:** `films/stills/la-belle-hortense/{001.50,003.75,006.75,008.25,014.00,021.00,021.75,036.75,039.00,039.75,041.25,043.30,044.25,044.75,060.50}.png`. Check sheet: `editor/e2_checks.jpg`.

**Clips, with a mid-frame still for each:** `films/sources/la-belle-hortense/editor/stills/*_E2_mid.png`.

## Revisions linked

structure S2 · scenes A1 · print-sound U4 (title and end-card text superseded by editor E2 cards; the envelope superseded by LoC 2010652109) · ledger U2 + `editor_E2` · editor E2 (this file). Credits: `films/credits/la-belle-hortense.json`, 19 records, including the typefaces and the film licence. Note: `films/notes/la-belle-hortense.txt`, 108 words.

## Remaining failures and weaknesses

- **Fresh-reader run not done.** No naive human viewer was available to this unit, so the pause-at-39.0 s record does not exist. Fair play rests on verify.py S2 alone.
- **Commons.** The API answered HTTP 429 all through this round. Commons licences were not re-read live in E2; they stand as U2 and U4 read them earlier today.
- **Tonal range.** Still short of the cover: p95 163 against 228, with few hot creams.
- **Draped coat.** It reads as a coat (collar, sleeve, folded skirt), but the cut hand area of the source print shows as a bright red patch at the chest. The coat is small in the wide shot: about 60 px across.
- **II.2.** The reaching arm is assembled from the conductor's sleeve piece and forearm piece. The hand is a soft mask cut from a print that is small at source, so it is legible but soft. The brass glint of the key bow (frames 12–17) is large and shows outside the fold for 6 frames.
- **V.4 key.** The landed key is the CC0 key photograph dyed flat brass. It reads as a key but is flatter than the photographic grass.
- **Shared clips and soft sources.** Door close-ups are still soft (2–4× enlargements). II.5, III.3 and IV.6 share one empty-bench clip, and the four cloche slots share one bell clip. The visitor is a soft, upscaled source.
- **I.3 envelope.** It is an 1861 envelope, older than the 1940s photographs. Two library pencil marks on its lower edge were inpainted (declared). U4's typed-address envelope is no longer used.
