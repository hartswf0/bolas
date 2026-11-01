# ALLWAYS page builder

Run `python3 tools/allways/build.py` from the repository root. Python's standard library is sufficient.

The script reads `paeleo/allways/STATEMENT.md`, `works.json`, and `scion/scion-allways.json`, then writes `paeleo/allways/index.html`. The statement renderer intentionally supports the controlled heading, paragraph, emphasis, and strong-emphasis format used by its source. Companion Markdown links open their rendered GitHub documents.

Edit the Markdown statement or structured slate before rebuilding. `WORKS.md` is the readable development catalogue and should remain consistent with `works.json`. `allways.css` controls presentation. The page reuses local fonts and existing project preview images, and introduces no tracking or external runtime dependency.

The standalone `operator.html` contains its 59-entry registry so it also works as a downloaded file. Its prompt content matches the registry and individual Markdown files in `scion/`. If prompt content changes, update all three representations and verify exact copy/download content. The reader's browser behavior and the original prompt reviews are documented in the ALLWAYS section.

The existing homepage and PAELEO builders retain links to ALLWAYS. No media-dependent site-wide rebuild is required to update this section.

`runs.py` builds the run pages and film case-study pages for every generated run in `paeleo/allways/runs.json` (see `paeleo/allways/RUNS.md` for the data a run supplies), and writes each run's `films.json`. Run it before `build.py`: the landing page's Runs section reads those files. Linked runs (their own site) are listed but not generated.
