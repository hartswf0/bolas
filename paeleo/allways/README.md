# ALLWAYS

**Cinema from the rest of the frame.**

ALLWAYS is a cinema practice within PAELEO: films, playable archives, and experiments in machine-assisted editing, organized around ordinary gestures, overlooked work, and the differences that survive a match.

Its question is **what else was happening?** Its name joins *always* and *all ways*: recurrence through time, and different routes through the same material.

**Live:** https://hartswf0.github.io/bolas/paeleo/allways/

## Read and use

- [Statement](STATEMENT.md): the public proposition, through Record / Work / Machine.
- [Proposed works](WORKS.md): twelve development concepts and the first proofs that could make them concrete.
- [Methods](METHOD.md): source records, editorial comparisons, reconstruction, and the SCION production cycle.
- [Between Takes](NOTEBOOK.md): working fragments and questions.
- [Naming](NAMING.md): the complete earlier name slate, with canonical uses, aliases, and studies.
- [Editorial decisions](EDITORIAL.md): what the competing drafts contributed and what changed.
- [SCION operator](operator.html): search, read, copy, and download all 59 new prompts, IDs 055–113.
- [SCION files](scion/README.md): individual prompts, registry JSON, source audit, complete book, and reviews.

## One practice, distinct roles

| Name | Role |
| --- | --- |
| **PAELEO** | Research language and environment for descriptions that become consequential actions. |
| **ALLWAYS** | The cinema practice presented here. |
| **SCION** | Reusable production operators and criticism. |
| **B-ROLL OF CIVILIZATION** | The first proposed archival series. |
| **NEARMATCH** | Editorial principle: make differences easier to notice through resemblance. |
| **BETWEEN TAKES** | The working notebook. |

## Status

The statement, development slate, and 59 prompt specifications are published here. The first batch of archive proofs, SCION 055–065 cut by hand from movingimagearchive.com footage, is in [films/](films/) with edit lists, source ledgers, forage logs and a first critic round. These are proofs in progress, not released works. The twelve named ALLWAYS films remain concepts. The proposed proof scenes in the new prompt corpus have not yet been executed. Reference films are cited as lineages, not claimed as our productions.

Earlier work remains under its established project names: [Afterlight](../../afterlight/), [The Found Odyssey](../../found-odyssey/), [CINEOSIS](../../cineosis/), [WYGWYL](../../wygwyl/), and [PAELEO's handmade threshold studies](../handmade/). The ALLWAYS page connects to these precedents without changing their credits or production status.

## Source and build

`works.json` is the structured development slate. The Markdown files above are the editorial sources. Run `python3 tools/allways/build.py` from the repository root to rebuild the landing page; the script uses the Python standard library and preserves the independent SCION reader and corpus. Styling is in `allways.css`.

Existing PAELEO and homepage build sources include links to this section. The original 54-prompt animation operator remains separate and unchanged. No new license for earlier media is implied by these pages; each work retains its source-specific terms and credits.
