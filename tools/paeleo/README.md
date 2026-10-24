# PAELEO tools

PAELEO-00 *The threshold* and the `paeleo/` pages were made with these. Unlike the This Side Up scripts, they run from this
folder in a fresh checkout: Node with Playwright and its Chromium, Python 3 with numpy and Pillow, and ffmpeg.

- `../../paeleo/threshold/machine.js`: the dog's state machine. The film and the Try it page both run it.
- `../../paeleo/threshold/stage.js`: the paper set and cast, drawn on a canvas in metres.
- `film.js`: the score. The prompts and what each one changes, camera keys and cuts, the opening lineage, the title, the
  three-scales card, the lockup and credits, and the sound cues they leave behind.
- `render.html` and `render.js`: render the score frame by frame in Chromium and pipe it to ffmpeg. Also writes `cues.json`
  (sound cues, the decision trace, the timeline). `node render.js OUT 0 1968 24` writes one still a second instead of a film.
- `sound.py`: the soundtrack, synthesized from `cues.json`. No samples.
- `make.sh OUT`: picture, sound and mux, loudness at -18 LUFS.
- `test_machine.js`: model-based tests for the machine (`node tools/paeleo/test_machine.js`).
- `stills.py FILM`: the stills on the pages.
- `case_data.py CUES`: writes `case.json`, the record behind PAE-00's pages. It reads the critic rounds from `reviews/`.
- `build_pages.py`: builds `paeleo/`, `paeleo/threshold/` and `paeleo/scion/`.
- `reviews/`: each critic round's report, verbatim (`roundN.txt`), and its summary for the page (`roundN.json`).
- `fonts/`: the site's three faces (Big Shoulders Display, JetBrains Mono, Literata; SIL Open Font License) as woff2,
  so the render doesn't need the network.

The SCION operator (`paeleo/scion/operator.html`) is the operator file as supplied, plus a link back and `#sNN` to open a
given swarm. `paeleo/scion/swarms.json` is its data.
