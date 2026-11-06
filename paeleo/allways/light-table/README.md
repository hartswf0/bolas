# ALLWAYS light table

A buildless, additive viewing surface for the four existing ALLWAYS runs. The studio remains intact and links here from its navigation and introductory links.

## Viewing behavior

- **Contact sheet:** filter the 132 published entries by maker, collection, operator, title, source or description. An unfinished SOL source study retains its preparatory status.
- **Watch & inspect:** switch between makers without losing the proposition; click a proportional output interval or a shot card to seek. Source title, reason, source interval where available, and the original source link follow the selected interval. Unannotated gaps remain visible.
- **Compare:** choose two films, play/pause both, seek by elapsed seconds or relative progress, and audition one soundtrack. Shared seeking does not claim action synchronization. Playback preserves original speed. Reset restores the selected proposition.

The six design principles map to visible behavior: review scope and timing gaps expose hidden state; proposition groups reduce memory burden; contact sheet, watch and compare provide multiple modes; seeking and soundtrack audition support direct manipulation; selection persists across overview, film and shot detail; comparison is reversible and changes no source media.

## Data and limits

`catalog.json` is a 2 November 2026 snapshot of the published records, not a new critic evaluation. It imports 85 Argon entries, 24 Sol entries, 11 Sonnet films and 12 Opus films. There are 980 imported output intervals across 109 entries. The remaining entries link to their original records without invented cut timings. Review results are not converted into a common rating or full audiovisual acceptance.

The seven SOL 055 thumbnails in `frames/` are midpoint frames decoded from its published V04 MP4. Argon images and Sonnet cut frames retain their published URLs. No source recordings are copied into this addition. External media availability remains a dependency.

Local comparison state is transient. The selected film and mode are shareable in the URL fragment. Filtering and comparison never write to the catalog or source media. No packages, accounts, API keys or build step are required.

## Refresh the catalog

From the repository root, with Python 3:

```sh
python tools/allways-light-table/fetch_records.py /tmp/allways-published-records
python tools/allways-light-table/build_catalog.py /tmp/allways-published-records
node --check paeleo/allways/light-table/light-table.js
```

The importer intentionally asserts the expected 132-entry snapshot. Update that assertion and the snapshot labels when the published collection changes. SOL 055 thumbnails must be regenerated if its imported revision changes. Add adapters for further SOL timing schemas before claiming their cut records are normalized.

Serve the repository with any static server and open `/paeleo/allways/light-table/`.
