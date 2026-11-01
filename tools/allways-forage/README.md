# ALLWAYS forage kit

Forage and hand-cut ALLWAYS films (`allways-sonnet/`) from the archive shots
cached in a local clone of [cineosis-lab](https://github.com/hartswf0/cineosis-lab)
(movingimagearchive.com shots: 405 clips with sound, mostly 320×240 and about 25 s;
474 silent 3 s loops; 5,272 stills).

| step | command |
|---|---|
| index | `python3 build_index.py /path/to/cineosis-lab` → `index.json`, not committed because it holds local paths. Each shot carries every archive query that returned it, CLIP subjects, colour and audio features. |
| search | `python3 forage.py "regex" --media clip --n 40 --sheet sheet.jpg` gives candidates and a contact sheet. The archive queries name *scenes*, so treat a hit as a hint and choose from the frames. |
| shape scan | `python3 circles.py still` or `python3 circles.py clip` → `circles-*.json` (Hough circles scored by rim-edge support). This is how BALL was foraged. |
| measure | `python3 measure.py <id-prefix> still\|clip [t] --out check.jpg` measures the registration circle for one image. |
| render | `python3 render.py allways-sonnet/<id>/edl.json [--control]` → `<id>.mp4` + `<id>.ledger.json` |
| case studies | `python3 build_casestudies.py` builds the Sonnet edition's index, atlas and a case-study page per film (frames from the finished films, candidate strips from the local archive cache, the critic round, copyable prompts) |
| editions | `python3 ../allways/build.py` validates every edition and rebuilds the landing page and `editions.html` |

The renderer only translates and uniformly scales sources: no mirroring, warping, rotation or retiming. `--control` renders every registered layer as a plain full-frame fit, giving the unregistered comparison cut. The ledger records, for every shot, the source film, its archive page, its time in the source film and the transform applied. The EDL schema is in the `render.py` docstring.

The archive's own search (`www.movingimagearchive.com/api/search`) was unreachable from the build session. The first batch is foraged from the cache only, and each film's NOTES.md ends with a queue of live searches for its next version.
