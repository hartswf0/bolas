# This Side Up case pages

These scripts built `this-side-up/<case>/` and the This Side Up entries under `docs/`. They ran in the session that made the films, so the
paths in them point at that session's working folders; they are kept here as the record of how each page was put together.

- `data.py`: the record for each case. Versions, prompts, critic rounds, sheets with captions, what broke and what changed.
- `build_docs.py`: prompts (verbatim), every critic round's brief and report, the Trouttown notes, and the This Side Up section of `docs/index.html`.
- `build_media.py`: sheets at 1100 px and versions as 640 px web encodes with posters; versions already encoded for the reader are reused.
- `build_compare.py`: same-moment frame grids (FALL's six cuts, the six leans, the Trouttown release).
- `build_pages.py`: the case pages.
- `verify_sheets.py`, `contact.py`: contact sheets for checking every caption against its picture.
- `fall_rerender_sound.py`: sound for FALL cuts 1 to 3, which were re-rendered on Oct 20 from the scripts saved on Oct 18
  (fall_r1.py, fall_r2.py, fall.py) because their films had been overwritten.

No frame of the reference film used in Tempus Fugit v1 appears on any of these pages; sheets that contained one were removed.
