# ALLWAYS editions

An **edition** is one maker's pass at the SCION operators: the same prompts, a different hand. Editions live at the repository root as `allways-<name>/`, so they sit side by side: [allways-sonnet](../../allways-sonnet/) and [allways-sol](../../allways-sol/) exist; Gemini and Argon are expected. The landing page and the [comparison page](editions.html) list every edition in `editions.json` and line the films up by operator, so the same prompt can be read across makers.

## Adding an edition

1. Make a folder `allways-<name>/` at the repository root (lower case, hyphens).
2. Put in it an `index.html` that presents the edition however its maker likes, and either an `edition.json` (below) or a catalog the registry can read (see *Existing catalogs*).
3. Add one entry to [`editions.json`](editions.json) (paths there are relative to `paeleo/allways/`): `{"id": "allways-<name>", "label": "<Name>", "path": "../../allways-<name>/", "status": "published"}`. An entry with `"status": "expected"` shows as a placeholder until its folder exists.
4. From the repository root run `python3 tools/allways/build.py`. It checks every `edition.json`, rewrites the landing page's Editions section and `editions.html`, and reports problems.

Nothing else on the site needs to change. Each edition keeps its own page design, its own case-study format and its own credits.

## Existing catalogs

An edition that already has its own site and manifest does not need an `edition.json`. The registry entry names a reader with `"format"` and the manifest file with `"manifest"`. One reader exists: `allways-sol-catalog`, for [allways-sol/catalog.json](../../allways-sol/catalog.json) (films with `id`, `title`, `film.url`, `poster`, `status`). To support another shape, add a small function to `tools/allways/editions.py` that returns the same fields as `edition.json`. Files inside an edition with a reader are not checked by the build; the edition owns them.

## `edition.json`

```json
{
  "id": "allways-<name>",
  "label": "Name shown on cards",
  "made": "2026-11-02",
  "summary": "One or two sentences on what this edition is and how it was made.",
  "status": "published",
  "page": "./",
  "cover": "NNN-slug/poster.jpg",
  "films": [
    {
      "operator": 59,
      "title": "Ball",
      "duration": 40,
      "film": "059-ball/059-ball.mp4",
      "poster": "059-ball/poster.jpg",
      "page": "059-ball/",
      "verdict": "free text: critic result, or 'critic review pending'",
      "sources": 15
    }
  ]
}
```

- `operator` is the SCION id (055–113) from [`scion/scion-allways.json`](scion/scion-allways.json). It is how films are matched across editions.
- All paths are relative to the edition folder. `film` and `poster` are checked for existence; `page` is the film's own page inside the edition.
- `verdict` should say what actually happened. Include "pending" if no independent review has run, and do not imply an audience result an AI critic cannot give.
- `sources` is optional: the number of distinct archive shots in the cut.

## What a good edition shows

These are the commitments of the first edition, offered as a model rather than a rule:

- For each film, the SCION prompt that was run, the exact assignment given, and a way to copy them.
- The images that were looked at, and the reason for each shot in the cut.
- A source ledger: for every shot, its film, year, archive page, time in the source and any transform.
- What the footage could not supply, and every substitution made for the prompt's imagined scenes.
- Which review actually happened (and which did not): listening, screening, a second reader.
