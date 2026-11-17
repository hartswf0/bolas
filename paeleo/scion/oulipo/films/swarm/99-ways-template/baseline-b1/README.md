# Baseline b1 — 99 Ways to Tell a Story · Template (Direction 2, Photo-Fumetti Cutout)

This package lets another swarm rebuild b1, or derive from it, without reading the plan. `manifest.json` lists every file below with a short sha256, so you can check the revision.

## The incident (frozen; `ledger.json`)

| Event | What happens | Panel |
|---|---|---|
| E0 | The clerk reads the memo (4:15, open the SERVICE door, key in the cupboard). | P1 |
| E1 | He leaves the desk. | P2, P3 |
| E2 | The visitor, off-panel on the platform, asks "What time is it?". | P4 |
| E3 | The clerk answers "Ten past four!". The clock reads 4:10. | P5 |
| E3b | "Thanks!" comes from outside, and the window is empty. | P6 |
| E4 | He opens the cupboard. The brass key hangs on its hook. | P7 |
| E5 | "What the hell was I looking for, anyway?" The key stays, and the SERVICE door stays closed. | P8 |

## What to read

| What | Where |
|---|---|
| Event graph (fact, cue, interpretation) | `../ledger.json` |
| Page record: bounds, speech, tails, rig rest poses, film in/out | `../panels.json` |
| Page (2550×3300, 300 dpi) | `assets/pages/99-ways-template.png`, built by `../page/build_page.py` |
| Rest layers per panel | `../page/rest/P1..P8/` (layers composite over each other, in order, to the page crop) |
| Lettering | `../page/glyphs.json` (the handmade pen alphabet); `../variants/glyphs_extra.json` adds "2" and "F"; the film script adds a "3" in the same pen |
| Pieces | `films/sources/99-ways-template/page-cartoonist/pieces/manifest.json` (used on the page), `../cutouts/manifest.json` (master-resolution pieces) |
| Rig and animation | `../anim/rig.json`, `../anim/timing.json` (pose keys on twos, balloon land frames), `../anim/fk_test.json`, `../anim/panels.py` |
| Derivatives and coverage | `../variants/` (D1 compressed, D2 from the platform), `../coverage.json` |
| Film | `assets/films/99-ways-template.mp4`, rendered by `films/99-ways-template.py` (runs `--checks`) |
| Credits | `films/credits/99-ways-template.json` |

## Rules a derivative must keep

- Change exactly one dimension.
- Mark every event as shown, implied (with its cue) or omitted in `coverage.json`.
- Keep the outcome and the speaker of every line.
