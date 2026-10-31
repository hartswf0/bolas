# 062-colors — Colors: Chromatic Chapters (found-footage draft)

Files: `edl.json` → `062-colors.mp4` (50.2 s, 5.2 MB, sound-led: source tracks of clips at −3 dB, loops silent) + ledger;
comparison `edl-alt.json` → `062-colors-alt-silent.mp4` (identical picture, all source sound removed) + ledger; `contact.jpg`; `mk.py`.
Revision r1 (2026-10-31). Builder: forms.

**How it was checked.** I inspected contact sheets, frame strips and full-size single frames, and a 1 fps strip of the render. I did not watch the film at speed. I could not listen, so the sound-led cut uses each clip's own track **unauditioned**: it may contain narration fragments. **Independent critic review: PENDING.** No recolouring, grading or crop-to-colour was applied. Every shot is `fit: cover` at its native colour.

## 1 · Theorem, adapted
Colour carries attention across unrelated films. Each chapter goes through different kinds of work: yellow is protective gear and heavy machinery, blue is the sea and the work table where suits are mended, red is packing and unloading. The same hue organises different actions. Two mixed frames act as hinges: yellow machines over blue water, then a crate over blue water swinging toward a red hull. The film ends at a table where red, yellow-orange and blue share one ordinary setting.

## 2 · Forage log
- **Index colour as a filter only.** I wrote `colorscan.py` (scratchpad), which measures the per-half-second area of saturated red/yellow/blue pixels (OpenCV HSV, S>110, V>70) across all 662 colour clips and loops. Top numeric hits were often **wrong for the concept**: tinted silent film (*The Battling Kangaroo* reads 95 % "yellow"), blue-tinted Dutch newsreels, skies, sunsets, title cards. The CLIP/`hue` fields from the thumbnail missed most shots that worked. Final picks were made by looking at frames.
- **Three-hue search:** only 5 shots have red, yellow and blue together above threshold in the same frame. The best is a 1983 dinner table (*Inside/Outside*), which became the ending.
- **Surprising finds:** *Oil Across Arabia* (1950) has, in one 27 s clip, yellow Caterpillar machines slung over a blue sea, a ship waiting at anchor, and a crate swung toward a red hull. That gave both chapter hinges from one source. *Moonwalk One* (c.1970) has hands mending a space-suit boot and glove on a blue table, which is the nearest match to the prompt's "glove being repaired".
- **Not in the archive:** a yellow work glove entering a neutral frame. A yellow object being repaired. A quiet red action that is clearly a single gesture. The red material is thin: loops are 3 s, and most strong reds are stage costumes, title cards, sunsets or tinting.

## 3 · The cut
| t | shot | source (year), interval | why |
|---|---|---|---|
| 0:00–0:01.9 | looking out through the mesh of a yellow cab; yellow-shirted man behind | *Structure Protection Strategies…* (2003) 0.85–2.75 | yellow enters as a frame/structure |
| 0:01.9–0:04.0 | yellow-clad crew hosing a burnt slope | same 12.3–14.4 | yellow at work in ash |
| 0:04.0–0:07.4 | firefighter's yellow shirt crossed by harness, radio, gloves; red helmet | same 3.3–6.7 | yellow partly covered by use; the red helmet anticipates chapter 3 |
| 0:07.4–0:10.2 | yellow bulldozers slung over blue sea | *Oil Across Arabia* (1950) 21.3–24.1 | **hinge Y→B**, discovered inside one frame |
| 0:10.2–0:15.5 | derrick lowering cargo on deck against blue water | same 15.9–21.2 | blue, work at the edge of frame |
| 0:15.5–0:18.8 | ship lying at anchor | same 12.1–15.4 | change of pace: the ship waits |
| 0:18.8–0:23.1 | hands working on a suit boot on a blue table | *Moonwalk One* (c.1970) 0.05–4.35 | repair under blue |
| 0:23.1–0:26.4 | woman stitches suit layers, pressure glove waits | same 9.1–12.4 | the glove motif |
| 0:26.4–0:29.4 | silhouettes before a blue-lit window | *The Eagle Has Landed* (1969) loop | waiting |
| 0:29.4–0:32.2 | crate swung over blue water toward a red hull | *Oil Across Arabia* 24.15–26.95 | **hinge B→R** |
| 0:32.2–0:35.2 | man packs a box against red canvas | *Antarctica 1939–41* loop | quiet practical red |
| 0:35.2–0:38.2 | men in red shirts unload sacks from a van | *Inside the Fed* (1994) 0–3 | red at work |
| 0:38.2–0:41.2 | red machinery hoisted by a corrugated wall | *Moonwalk One* loop | red, and a rhyme with the derrick |
| 0:41.2–0:47.1 | dinner table: red curtains, orange/yellow fruit, blue blouse, pale-blue cloth | *Inside/Outside* (1983) 0–5.9 | shared setting |
| 0:47.1–0:50.1 | source card | | |

## 4 · Departures
- The prompt's glove arc (yellow glove → repair → hidden yellow → glove placed among the other objects at the end) **could not be found**. The glove appears in the blue chapter (*Moonwalk One*), not as the opening object, and the ending is a different setting, not the opening object returned.
- Duration is 50 s instead of 60. The red chapter is short because the archive's usable reds are 3 s loops.
- "Sound-led cut first, score only after": no score was composed. The sound-led version uses unauditioned source tracks; the silent version is the comparison. A critic needs to listen to both, because I could not.
- Colour-region records exist per shot as half-second area fractions (`scratchpad/forms/colorscan.json`) but were not copied into the film folder. Numbers for chosen shots are summarised in the event labels only.

## 5 · Self-review against §5
- *Colour continuity visible without destroying tonal range:* no grading was applied, so tonal range is the source's. Continuity across a 1950 Kodachrome print, a 1970 print and 2003 video is uneven. The blue of *Oil Across Arabia* is teal-green next to the *Eagle* blue.
- *A chapter contains differing actions or stakes:* yellow = protection, firefighting and heavy lift. Blue = cargo, waiting, mending. Red = packing, unloading, hoisting. Plausibly yes.
- *Mixed-colour transition makes the change legible:* both hinges are single frames that contain both hues (checked on stills).
- *Ending gives colours a shared situation:* yes, the dinner table. But it is a staged instructional scene (1983) whose speech may surface in the sound-led cut.
- *Avoids universal emotional meanings for hues:* red is packing and unloading, not danger. The firefighting yellow is protective gear, not a mood.
- *Structural:* the ledger shows `fit: cover` with uniform scale only (1.0, 2.0 or 2.67 depending on source size) and no colour transforms. No selective hue replacement exists to flag.
- **Largest unresolved limitation:** the red chapter is three 3-s fragments, and the sound is unauditioned, so the sound-led cut may carry stray narration.
- Critic verdict: **PENDING**.
