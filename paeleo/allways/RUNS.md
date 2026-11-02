# Runs: how another maker adds an ALLWAYS run

A **run** is one maker (a model, a person, a team) making proofs for ALLWAYS by its own process, with the process kept. Each run is a folder at the repository root, `allways-<name>/`, beside `allways-opus/` and `allways-sol/`. The landing page (`paeleo/allways/index.html`) lists every run in `runs.json`.

There are two ways in:

- **Generated.** The run supplies data (`run.json`, one `film.json` per film, media) and `tools/allways/runs.py` builds its run page and its case-study pages. Runs that make the twelve works of the B-ROLL OF CIVILIZATION slate (`works.json`) also appear side by side, film by film, on the landing page and on each other's film pages. `allways-opus` is the first.
- **Linked.** The run keeps its own site, as `allways-sol` does for operators 055-078. Add an entry to `runs.json` with `"kind":"linked"`, a `summary` and a `note`. The landing page links to it and builds nothing for it.

## What a generated run adds

```
allways-<name>/                (at the repository root)
  run.json                     who/what made it, what it could perceive, caveats
  PROMPT.md                    the prompt or method it was given or followed
  tools/                       the code it used, if any
  films/<slug>/film.json       the case study for one film (schema below)
  films/<slug>/<slug>.mp4      the film
  films/<slug>/poster.jpg
  films/<slug>/img/…           sheets, strips, reel, critic sheets
  films/<slug>/…               edl.json, ledger.json, critic files, anything else you cite
```

Then add one entry to `paeleo/allways/runs.json` (its `path` is relative to the repository root), and from the repository root run:

```
python3 tools/allways/runs.py      # writes the run page and every film page for every generated run
python3 tools/allways/build.py     # rebuilds the ALLWAYS landing page, including the Runs section
```

Both use only the Python standard library. Film slugs are the ones in `works.json` (`nobody-home`, `almost-human`, `terra-incognita`, `split-second`, `cut-to-the-chase`, `kinetic`, `zero-memory`, `homonym`, `anybody-anywhere`, `collective-inventories`, `mnemonil`, `planimetric`). A run may make fewer than twelve. Every field below is optional: a section with nothing in it is left out.

## runs.json

```json
{"runs":[
 {"id":"allways-opus","path":"allways-opus/","name":"Opus 5.5","maker":"Claude Opus 5.5 (Anthropic)","date":"2026-10-31"},
 {"id":"allways-sol","path":"allways-sol/","kind":"linked","name":"Sol","maker":"Sol (OpenAI)","date":"2026-11-01","summary":"…","note":"23 films · 16 comparisons"}
]}
```

## run.json

```json
{
 "id":"allways-opus","name":"Opus 5.5","maker":"Claude Opus 5.5 (Anthropic)","date":"2026-10-31",
 "summary":"two or three sentences",
 "request":"what the maker was asked, in the asker's words",
 "perception":{"sees":true,"hears":false,"notes":"what the maker could and could not perceive"},
 "roles":[{"role":"critics","who":"Claude Sonnet 5.5, fresh agents, frames + transcript only"}],
 "caveats":["things a reader must know before trusting the films"],
 "findings":["things this run learned that are not about one film"]
}
```

`perception` matters: a maker that can hear the footage and one that cannot are not making the same kind of edit.

## film.json

```json
{
 "slug":"nobody-home",
 "state":"proof in progress",
 "summary":"one or two sentences",
 "video":{"src":"nobody-home.mp4","poster":"poster.jpg","duration":46.7},
 "searches":[{"q":"query text","results":24,"sheet":"img/sheet-1.jpg"}],
 "looks":[{"img":"img/strip-13.jpg","clip":13,"label":"#13 Title (year)","used":[1,11],"in_cut":true}],
 "shots":[{"at":0.0,"dur":2.0,"source":"Title","year":1944,"clip":"<archive clip id>","source_in":62.8,"source_out":64.8,
           "url":"<videoUrl>","transforms":[],"sound_from":[{"source":"Title","year":1944,"source_in":64.4,"source_out":66.4}],"why":"reason"}],
 "reel":"img/reel.jpg",
 "reviews":[{"round":1,"who":"independent critic","verdict":"inconclusive","packet":{"sheet":"img/critic-r1-sheet.jpg","transcript":"critic/transcript-r1.txt","note":"what the critic saw"},
             "text":"the critic's report, verbatim","builder_note":"where the builder disagrees"}],
 "repairs":["what changed after review"],
 "notes":{"worked":[],"failed":[],"open":[]},
 "extras":[{"title":"Removal evidence","html":"<p>…</p>","images":[{"src":"img/mask.jpg","caption":"…"}],"video":{"src":"compare.mp4","caption":"…"}}],
 "files":[{"path":"edl.json","label":"edit list"}]
}
```

`state` uses the vocabulary of `METHOD.md`: concept, proof in progress, proof reviewed, work in development, released. A critic's pass makes at most "proof reviewed". Only a person releases.

## Rules every run keeps

1. The edit is the maker's, and the case study shows every decision with its reason.
2. Each shot keeps its source, source seconds, and any transformation. Sound and captions from another source are recorded as such.
3. Anything derived (removed, generated, retimed, voiced) is marked, and what is unknown stays unknown.
4. A critic sees the film and brief, not the maker's reasons. Its report is kept verbatim, with the maker's disagreement beside it, not instead of it.
5. Say what you could not perceive. State what is below the brief. Check reasons against the frames before publishing them.
6. Source films are public-domain according to their archive. Keep titles, years and clip ids so anyone can go back.

## The screening room

[`screening.html`](screening.html) plays every film of every run back to back, in one frame at one loudness. Nothing in a run's own files is changed. The page reads [`screening.json`](screening.json), which `tools/allways/screening.py` builds from each run's own metadata:

```
python3 tools/allways/screening.py    # measures new files, writes screening.json and small posters
python3 tools/allways/build.py        # rebuilds the landing page
```

- **A generated run is included with no extra work** if it has `films.json` and `films/<slug>/<slug>.mp4` as above. Any other `.mp4` in a film's folder is listed as a copy of that film.
- **A linked run needs a small adapter** in `screening.py` (`ADAPTERS`) that returns its films. Sol, Sonnet and the Argon studio have one. A linked run without an adapter is simply left out, and the build says so.
- **One canonical copy per film.** It is the cut the run itself presents as current: the generated run's `<slug>.mp4`, Sol's `films[].film`, Argon's studio v2, Sonnet's `<id>.mp4`. Comparison cuts and older cuts are kept as copies; the player offers them per film and can queue them too.
- **Regularised at playback, not in the files.** Each film is fitted whole into a 16:9 frame (letterboxed or pillarboxed, never cropped). Each copy gets a volume gain from its measured integrated loudness (EBU R128) toward -20 LUFS, never lifting by more than 12 dB and never past -1 dBTP; silent files are left alone. Measurements are cached in `screening-measure.json`.
- If a run replaces a file, run `screening.py` again; a changed file size triggers a new measurement.
